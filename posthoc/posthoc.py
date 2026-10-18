"""Post-hoc analyses (NOT pre-registered; written after the test results were seen). Reported separately and
labelled post hoc in the paper. Reads saved records only; runs no pipeline or model.

  P1  per-domain primary endpoint on the test split (the protocol pooled domains)
  P2  TLC test cases whose period range does not contain the 2023-04 schema event (where the published airport
      fee changed from $1.25 to $1.75 in the same quarter the column was renamed)
  P3  a trivial "blame every changed component" heuristic, to show what the change log alone gives
  P4  attribution of DoD's false blame on TLC test cases to boundary-test events
  P5  source-coupled vs internal defects: DoD vs rollback-only per domain

usage: python posthoc/posthoc.py runs/final  -> runs/final/posthoc.json, posthoc.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from summarize import boot_ci, load, paired_diff, per_case  # noqa: E402

METHODS = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
           "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
           "dod", "dod_no_boundary", "dod_b1", "dod_b1_uniform"]


def mean_ci(rows, metric):
    if not rows:
        return None
    x = np.array([float(r[metric]) for r in rows])
    cl = np.array([f"{r['domain']}|{r['sig']}" for r in rows])
    lo, hi = boot_ci(x, cl)
    return {"mean": float(x.mean()), "ci": [lo, hi], "n": len(rows)}


def main() -> None:
    run = Path(sys.argv[1])
    recs = load(run)
    by_id = {r["case"]["case_id"]: r for r in recs}
    # P3: blame-all-changes heuristic, added to the per-case records
    for r in recs:
        changed = sorted({c["component"] for c in r["obs"]["change_log"]})
        r["methods"]["blame_all_changes"] = {"fix": changed, "retrain": False, "cost_s": 0.0,
                                             "outcome": {"score": None}, "notes": {}}
    pcs = [per_case(r) for r in recs]
    test = [p for p in pcs if next(iter(p.values()))["split"] == "test"]
    out, L = {}, ["# Post-hoc analyses (not pre-registered)", ""]
    methods = [m for m in METHODS + ["blame_all_changes"] if any(m in p for p in test)]

    # P1 per domain
    out["P1"] = {}
    L += ["## P1 Primary endpoint by domain (test split, cases with a consequential defect)", "",
          "| method | " + " | ".join(["news", "tlc"]) + " |", "|---|---|---|"]
    for m in methods:
        row = []
        for d in ("news", "tlc"):
            rows = [p[m] for p in test if m in p and p[m]["domain"] == d and p[m]["has_cons"]]
            s = mean_ci(rows, "diag_correct")
            out["P1"].setdefault(m, {})[d] = s
            row.append(f"{s['mean']:.3f} [{s['ci'][0]:.2f}, {s['ci'][1]:.2f}] (n={s['n']})" if s else "")
        L.append(f"| {m} | " + " | ".join(row) + " |")
    out["P1_diff"] = {}
    for d in ("news", "tlc"):
        for other in ("bugdoc_shortcut", "llm_tools@luna", "dod_no_boundary"):
            S = [p for p in test if next(iter(p.values()))["domain"] == d]
            out["P1_diff"][f"{d}: dod - {other}"] = paired_diff(S, "dod", other, "diag_correct",
                                                                lambda r: r["has_cons"])
    L += [""] + [f"- {k}: {v}" for k, v in out["P1_diff"].items()] + [""]

    # P2 TLC excluding the 2023-04 event
    def spans(r, ev="2023-04"):
        return r["case"]["p0"] < ev <= r["case"]["p1"]
    S2 = [p for p in test if next(iter(p.values()))["domain"] == "tlc"
          and not spans(by_id[next(iter(p.values()))["case_id"]])]
    S2n = [p for p in test if next(iter(p.values()))["domain"] == "news"]
    out["P2"] = {"n_tlc_cases": len(S2)}
    L += ["## P2 TLC test cases not spanning the 2023-04 airport-fee event", "",
          f"{len(S2)} TLC test cases ({sum(1 for p in S2 if next(iter(p.values()))['has_cons'])} with a "
          "consequential defect)", ""]
    for m in methods:
        rows = [p[m] for p in S2 if m in p and p[m]["has_cons"]]
        allr = [p[m] for p in S2 if m in p]
        if rows:
            out["P2"][m] = {"cons": mean_ci(rows, "diag_correct"), "false_blame_all": mean_ci(allr, "false_blame")}
            L.append(f"- {m}: consequential {out['P2'][m]['cons']['mean']:.3f} (n={len(rows)}), false blame "
                     f"{out['P2'][m]['false_blame_all']['mean']:.3f}")
    base = [m for m in methods if not m.startswith("dod") and m != "blame_all_changes"]
    pool = S2 + S2n

    def pm(m):
        rr = [p[m] for p in pool if m in p and p[m]["has_cons"]]
        return float(np.mean([r["diag_correct"] for r in rr])) if rr else -1
    best = max(base, key=pm)
    out["P2_best_baseline"] = {"method": best, "mean": pm(best), "dod": pm("dod")}
    out["P2_pooled_with_news"] = {o: paired_diff(pool, "dod", o, "diag_correct", lambda r: r["has_cons"])
                                  for o in dict.fromkeys([best, "bugdoc_shortcut", "llm_tools@luna",
                                                          "dod_no_boundary"])}
    L += [""] + [f"- pooled news + TLC (no 2023-04): dod - {k}: {v}" for k, v in out["P2_pooled_with_news"].items()]
    L.append("")

    # P4 false-blame attribution
    ev = Counter()
    n_fb = 0
    for p in test:
        r0 = next(iter(p.values()))
        if r0["domain"] != "tlc":
            continue
        rec = by_id[r0["case_id"]]
        d = rec["methods"]["dod"]
        extra = set(d["fix"]) - set(rec["gt"]["defective"])
        if extra:
            n_fb += 1
            flagged = False
            for c in extra:
                for f in (d["notes"].get("boundary") or {}).get(c, []):
                    ev[f"{f.get('event')}:{f.get('column', 'retention')}"] += 1
                    flagged = True
                if c in (d["notes"].get("harmful") or []):
                    ev[f"effect test:{c}"] += 1
            if not flagged:
                ev["cases without a boundary flag"] += 1
            ev["cases spanning 2023-04"] += spans(rec)
    out["P4"] = {"tlc_test_cases_with_false_blame": n_fb, "boundary_flags": dict(ev)}
    L += ["## P4 Sources of DoD false blame on TLC test cases", "",
          f"{n_fb} cases; boundary flags behind them: {dict(ev)}", ""]

    # P5 source-coupled (T1) vs internal (T2/T3) consequential defects
    out["P5"] = {}
    L += ["## P5 Source-coupled (T1) vs internal (T2/T3) consequential defects, test split", ""]
    for d in ("news", "tlc"):
        for kind, pred in (("T1", lambda r: "T1" in r["tier"]), ("internal", lambda r: "T1" not in r["tier"])):
            for m in ("dod", "dod_no_boundary", "bugdoc_shortcut", "llm_tools@luna"):
                rows = [p[m] for p in test if m in p and p[m]["domain"] == d and p[m]["has_cons"] and pred(p[m])]
                if rows:
                    s = mean_ci(rows, "diag_correct")
                    out["P5"][f"{d}|{kind}|{m}"] = s
                    L.append(f"- {d} {kind} {m}: {s['mean']:.3f} (n={s['n']})")
    L.append("")
    (run / "posthoc.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    (run / "posthoc.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
