"""Summarise round-3 case records (protocol v3, v3/PROTOCOL_V3.md); derived from summarize_v2.py. Reuses the v1 definitions and statistics
(analysis/summarize.py: per_case, paired_diff, holm, boot_ci, table).

usage: python v3/analysis/summarize_v3.py runs/<v3 run>      -> summary_v3.md, summary_v3.json in that folder
       python v3/analysis/summarize_v3.py runs/v3dev --dev   -> development results on the round-1/2 domains
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis"))
import summarize as S1  # noqa: E402

V3_DOMAINS: tuple = ("cabi", "fars", "landreg")
BASELINES = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut"]
MONITORING = ["retrain_on_alarm", "validation_first", "observational_attribution"]


def spans_event(rec: dict) -> bool:
    return bool(rec["obs"].get("source_events"))


def invariant_flagged(rec: dict, method: str = "dod3") -> bool:
    d = rec["methods"].get(method) or {}
    for flags in ((d.get("notes") or {}).get("boundary") or {}).values():
        if any("invariant" in f for f in flags):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--dev", action="store_true", help="development run on the v1 domains")
    a = ap.parse_args()
    run = ROOT / a.run if not Path(a.run).is_absolute() else Path(a.run)
    recs = S1.load(run)
    if not a.dev:
        recs = [r for r in recs if r["case"]["domain"] in V3_DOMAINS]
    by_id = {r["case"]["case_id"]: r for r in recs}
    pcs = [S1.per_case(r) for r in recs]
    for p in pcs:            # case-level flags used by the v2 hypotheses
        r = by_id[next(iter(p.values()))["case_id"]]
        ev, inv = spans_event(r), invariant_flagged(r)
        for m in p:
            p[m]["spans_event"] = ev
            p[m]["inv_flag"] = inv
    methods = sorted({m for p in pcs for m in p}, key=lambda m: (m.startswith("dod"), "@" in m, m))
    title = "development (round-1/2 domains)" if a.dev else "round-3 held-out domains"
    L = [f"# Summary v3: {title}", "", f"{len(recs)} cases"]
    nd = defaultdict(int)
    for r in recs:
        nd[r["case"]["domain"]] += 1
    L += [f"by domain: {dict(nd)}", ""]

    def select(pred):
        return {m: [p[m] for p in pcs if m in p and pred(p[m])] for m in methods}
    L += S1.table(select(lambda r: True), "All cases")
    L += S1.table(select(lambda r: r["has_cons"]), "Cases with a consequential defect (primary endpoint)")
    L += S1.table(select(lambda r: r["spans_event"]), "Cases spanning a published source change")
    L += S1.table(select(lambda r: r["has_cons"] and not r["loud"]), "Silent consequential defects")
    L += S1.table(select(lambda r: r["has_cons"] and r["loud"]), "Loud consequential defects")
    L += S1.table(select(lambda r: not r["has_cons"]), "No consequential defect")
    first = lambda p: next(iter(p.values()))
    for t in sorted({first(p)["tier"] for p in pcs}):
        L += S1.table(select(lambda r, t=t: r["tier"] == t), f"Tier {t}")
    for d in sorted(nd):
        L += S1.table(select(lambda r, d=d: r["domain"] == d), f"Domain {d}")
        L += S1.table(select(lambda r, d=d: r["domain"] == d and r["has_cons"]),
                      f"Domain {d}, consequential defect")
    # composition
    L += ["### Case composition", ""]
    comp = defaultdict(int)
    for p in pcs:
        r = first(p)
        comp[(r["domain"], r["oracle_type"], "silent" if (r["has_cons"] and not r["loud"]) else
              ("loud" if r["has_cons"] else "-"))] += 1
    L += [f"- {k}: {v}" for k, v in sorted(comp.items())] + [""]

    # hypotheses
    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    loud = lambda r: r["has_cons"] and r["loud"]

    def mean(m, pred, metric="diag_correct"):
        rr = [p[m] for p in pcs if m in p and pred(p[m])]
        return (float(np.mean([float(x[metric]) for x in rr])), len(rr)) if rr else (float("nan"), 0)
    llm = sorted({m for p in pcs for m in p if m.startswith("llm_")})
    base = [m for m in BASELINES + llm if mean(m, cons)[1]]
    best = max(base, key=lambda m: mean(m, cons)[0]) if base else None
    H = {"best_baseline": best}
    tests = {}
    if best and mean("dod3", cons)[1]:
        tests[f"H11 primary: dod3 - best baseline ({best})"] = S1.paired_diff(pcs, "dod3", best, "diag_correct", cons)
    if mean("dod3", cons)[1] and mean("dod", cons)[1]:
        tests["H12 primary: dod3 - dod"] = S1.paired_diff(pcs, "dod3", "dod", "diag_correct", cons)
        tests["H13 false blame (cases spanning a source change): dod3 - dod"] = S1.paired_diff(
            pcs, "dod3", "dod", "false_blame", lambda r: r["spans_event"])
    adj = S1.holm({k: v["p"] for k, v in tests.items() if v.get("n")})
    H["tests"] = {k: {**v, "p_holm": adj.get(k)} for k, v in tests.items()}
    same = [p["dod3"]["diag_correct"] == p["dod"]["diag_correct"] and
            set(by_id[p["dod3"]["case_id"]]["methods"]["dod3"]["fix"]) ==
            set(by_id[p["dod3"]["case_id"]]["methods"]["dod"]["fix"])
            for p in pcs if "dod3" in p and "dod" in p and not p["dod3"]["spans_event"]]
    H["H14"] = {"n": len(same), "same_diagnosis": float(np.mean(same)) if same else float("nan")}
    L += [f"## Hypotheses ({title})", ""]
    for k, v in H["tests"].items():
        if v.get("n"):
            L.append(f"- {k}: {v['diff']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}] n={v['n']} p={v['p']:.4f} "
                     f"p_holm={v['p_holm']:.4f}")
    L.append("")
    L.append(f"**H14** cases without a published change: dod3 and dod make the same diagnosis in "
             f"{H['H14']['same_diagnosis']:.3f} of {H['H14']['n']} cases")
    L.append("")
    mon = [m for m in MONITORING + [x for x in llm if x.startswith("llm_report")] if mean(m, cons)[1]]
    H["H9"] = {m: {"silent": mean(m, silent), "loud": mean(m, loud)} for m in mon}
    L.append("**H9** monitoring-only methods, silent / loud consequential defects:")
    L += [f"- {m}: silent {v['silent'][0]:.3f} (n={v['silent'][1]}), loud {v['loud'][0]:.3f} (n={v['loud'][1]})"
          for m, v in H["H9"].items()]
    L.append("")
    t1 = lambda r: r["has_cons"] and "T1" in r["tier"]
    H["H10"] = {}
    for m in ("dod3", "dod3_no_latest", "dod3_no_inv", "dod2", "dod", "dod_no_boundary"):
        H["H10"][m] = {"T1": mean(m, t1), "T1_inv_flag": mean(m, lambda r: t1(r) and r["inv_flag"]),
                       "T1_no_inv_flag": mean(m, lambda r: t1(r) and not r["inv_flag"])}
    L.append("**H10** consequential T1 defects (invariant flag = some mined invariant flagged a component in dod3):")
    for m, v in H["H10"].items():
        L.append(f"- {m}: all {v['T1'][0]:.3f} (n={v['T1'][1]}); with invariant flag {v['T1_inv_flag'][0]:.3f} "
                 f"(n={v['T1_inv_flag'][1]}); without {v['T1_no_inv_flag'][0]:.3f} (n={v['T1_no_inv_flag'][1]})")
    H["ablations"] = {f"{x} - dod3": S1.paired_diff(pcs, x, "dod3", "diag_correct", cons)
                      for x in ("dod3_no_latest", "dod3_no_inv", "dod2") if mean(x, cons)[1]}
    L += [""] + [f"- ablation {k}: {v}" for k, v in H["ablations"].items()] + [""]
    out = run / ("summary_v3_dev.md" if a.dev else "summary_v3.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"tables": S1.TABLES, "hypotheses": H}, indent=1, default=str),
                                        encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
