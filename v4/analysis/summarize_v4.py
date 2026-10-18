"""Summarise round-4 case records (protocol v4, v4/PROTOCOL_V4.md). Reuses the v1 definitions and statistics
(analysis/summarize.py: load, per_case, paired_diff, holm, table) and adds the three-verdict metrics of
v4/analysis/metrics_v4.py.

usage: python v4/analysis/summarize_v4.py runs/<v4 run>      -> summary_v4.md, summary_v4.json in that folder
       python v4/analysis/summarize_v4.py runs/v4dev --dev   -> development results on the round-1/2/3 domains
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics_v4 as M  # noqa: E402
import summarize as S1  # noqa: E402

V4_DOMAINS: tuple = ("storm", "chicago")
BASELINES = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut"]
THREE_COLS = ("false_blame", "silent_miss", "decided", "correct_decided", "safe", "diag_correct", "review_load",
              "cost_s")
SUSPECT = "suspect"


def auc(pos: list, neg: list) -> float:
    """Probability that a random effective defect ranks above a random non-defect (ties count one half)."""
    if not pos or not neg:
        return float("nan")
    p, n = np.array(pos, float), np.array(neg, float)
    return float(((p[:, None] > n[None, :]).mean() + 0.5 * (p[:, None] == n[None, :]).mean()))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--dev", action="store_true", help="development run on the round-1/2/3 domains")
    ap.add_argument("--tag", default=None, help="read methods '<m>@<tag>' (a run_llm.py tag) as '<m>'")
    a = ap.parse_args()
    run = ROOT / a.run if not Path(a.run).is_absolute() else Path(a.run)
    recs = S1.load(run)
    if a.tag:
        for r in recs:
            for k in [k for k in r["methods"] if k.endswith("@" + a.tag)]:
                r["methods"][k[: -len(a.tag) - 1]] = r["methods"].pop(k)
    if not a.dev:
        recs = [r for r in recs if r["case"]["domain"] in V4_DOMAINS]
    by_id = {r["case"]["case_id"]: r for r in recs}
    pcs = [S1.per_case(r) for r in recs]
    for p in pcs:            # add the three-verdict metrics and case-level flags to every method row
        r = by_id[next(iter(p.values()))["case_id"]]
        ev = bool(r["obs"].get("source_events"))
        ncomp = len(r["case"]["state"])
        for m in p:
            p[m].update(M.case_metrics(r, m))
            p[m]["spans_event"] = ev
            p[m]["review_share"] = p[m]["review_load"] / ncomp
    methods = sorted({m for p in pcs for m in p}, key=lambda m: (m.startswith("dod"), "@" in m, m))
    title = "development (round-1/2/3 domains)" if a.dev else "round-4 held-out domains"
    L = [f"# Summary v4: {title}", "", f"{len(recs)} cases"]
    nd = defaultdict(int)
    for r in recs:
        nd[r["case"]["domain"]] += 1
    L += [f"by domain: {dict(nd)}", ""]

    def select(pred):
        return {m: [p[m] for p in pcs if m in p and pred(p[m])] for m in methods}
    L += S1.table(select(lambda r: True), "All cases (three-verdict metrics)", THREE_COLS)
    L += S1.table(select(lambda r: r["has_cons"]), "Cases with a consequential defect (three-verdict metrics)",
                  THREE_COLS)
    L += S1.table(select(lambda r: r["spans_event"]), "Cases spanning a published source change", THREE_COLS)
    L += S1.table(select(lambda r: not r["spans_event"]), "Cases without a published source change", THREE_COLS)
    L += S1.table(select(lambda r: r["has_cons"]), "Cases with a consequential defect (v1 metrics)")
    L += S1.table(select(lambda r: r["has_cons"] and not r["spans_event"]),
                  "Consequential, no published change in the period range")
    L += S1.table(select(lambda r: r["has_cons"] and r["spans_event"]),
                  "Consequential, published change in the period range")
    first = lambda p: next(iter(p.values()))
    for t in sorted({first(p)["tier"] for p in pcs}):
        L += S1.table(select(lambda r, t=t: r["tier"] == t), f"Tier {t}", THREE_COLS)
    for d in sorted(nd):
        L += S1.table(select(lambda r, d=d: r["domain"] == d), f"Domain {d}", THREE_COLS)
        L += S1.table(select(lambda r, d=d: r["domain"] == d and r["has_cons"]),
                      f"Domain {d}, consequential defect", THREE_COLS)

    def mean(m, pred, metric):
        rr = [p[m] for p in pcs if m in p and pred(p[m])]
        return (float(np.mean([float(x[metric]) for x in rr])), len(rr)) if rr else (float("nan"), 0)
    cons = lambda r: r["has_cons"]
    allc = lambda r: True
    H = {}
    # H15 soundness
    H["H15"] = {"dod4_false_blame": mean("dod4", allc, "false_blame"),
                "dod4_lite_false_blame": mean("dod4_lite", allc, "false_blame")}
    tests = {}
    if mean("dod4", allc, "false_blame")[1] and mean("dod3", allc, "false_blame")[1]:
        tests["H15 false blame (cases spanning a source change): dod4 - dod3"] = S1.paired_diff(
            pcs, "dod4", "dod3", "false_blame", lambda r: r["spans_event"])
    # H16 completeness
    H["H16"] = {"dod4_silent_miss": mean("dod4", cons, "silent_miss"),
                "dod4_lite_silent_miss": mean("dod4_lite", cons, "silent_miss")}
    # H17 exactness where decided
    H["H17"] = {"dod4_correct_decided_cons": mean("dod4", lambda r: r["has_cons"] and r["decided"], "diag_correct"),
                "dod4_correct_decided_all": mean("dod4", lambda r: r["decided"], "diag_correct"),
                "dod4_coverage": mean("dod4", allc, "decided")}
    # H18 no published change: the identifiable regime
    H["H18"] = {m: mean(m, lambda r: r["has_cons"] and not r["spans_event"], "diag_correct")
                for m in methods if mean(m, lambda r: r["has_cons"] and not r["spans_event"], "diag_correct")[1]}
    # H19 evidence labels of unverified components (descriptive)
    pos, neg = [], []
    lab_counts = defaultdict(lambda: [0, 0, 0])      # label -> [n, effective, consequential]
    for r in recs:
        d = r["methods"].get("dod4")
        if not d:
            continue
        E, C = set(r["gt"]["defective"]), set(r["gt"]["consequential"])
        for c, lab in M.unverified(d).items():
            s = 1.0 if lab == SUSPECT else 0.0
            (pos if c in E else neg).append(s)
            lab_counts[lab][0] += 1
            lab_counts[lab][1] += c in E
            lab_counts[lab][2] += c in C
    H["H19"] = {"auc_suspect_label": auc(pos, neg), "n_effective": len(pos), "n_not_effective": len(neg),
                "by_label": {k: {"n": v[0], "effective": v[1], "consequential": v[2],
                                 "precision_effective": v[1] / v[0] if v[0] else float("nan")}
                             for k, v in lab_counts.items()}}
    # descriptive: review load relative to pipeline size, verdict composition
    H["review"] = {m: {"load": mean(m, allc, "review_load"), "share": mean(m, allc, "review_share"),
                       "load_cons": mean(m, cons, "review_load")} for m in ("dod4", "dod4_lite") if mean(m, allc, "review_load")[1]}
    base = [m for m in BASELINES + sorted({m for p in pcs for m in p if m.startswith("llm_")})
            if mean(m, allc, "false_blame")[1]]
    H["false_blame_all"] = {m: mean(m, allc, "false_blame") for m in base + ["dod", "dod2", "dod3", "dod4", "dod4_lite"]
                            if mean(m, allc, "false_blame")[1]}
    adj = S1.holm({k: v["p"] for k, v in tests.items() if v.get("n")})
    H["tests"] = {k: {**v, "p_holm": adj.get(k)} for k, v in tests.items()}
    L += [f"## Hypotheses ({title})", ""]
    f = lambda x: f"{x[0]:.3f} (n={x[1]})"
    L.append(f"**H15** false blame of verified fixes, all cases: dod4 {f(H['H15']['dod4_false_blame'])}; "
             f"dod4_lite {f(H['H15']['dod4_lite_false_blame'])} (threshold 0.02)")
    for k, v in H["tests"].items():
        if v.get("n"):
            L.append(f"- {k}: {v['diff']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}] n={v['n']} p={v['p']:.4f} "
                     f"p_holm={v['p_holm']:.4f}")
    L.append(f"**H16** silent misses on consequential cases: dod4 {f(H['H16']['dod4_silent_miss'])}; dod4_lite "
             f"{f(H['H16']['dod4_lite_silent_miss'])} (threshold 0.02)")
    L.append(f"**H17** diagnosis correct where dod4 decides: consequential {f(H['H17']['dod4_correct_decided_cons'])}; "
             f"all {f(H['H17']['dod4_correct_decided_all'])} (threshold 0.95); coverage {f(H['H17']['dod4_coverage'])}")
    L.append("**H18** consequential cases without a published change (threshold 0.95 for dod4):")
    L += [f"- {m}: {f(v)}" for m, v in H["H18"].items()]
    L.append(f"**H19** 'suspect' label of unverified components: AUC for effective defects "
             f"{H['H19']['auc_suspect_label']:.3f} ({H['H19']['n_effective']} effective, "
             f"{H['H19']['n_not_effective']} not); by label {json.dumps(H['H19']['by_label'])}")
    L.append("Review load (unverified components per case; share of the pipeline): " + json.dumps(H["review"]))
    L.append("False blame, all cases: " + json.dumps(H["false_blame_all"]))
    L.append("")
    out = run / ("summary_v4_dev.md" if a.dev else "summary_v4.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"tables": S1.TABLES, "hypotheses": H}, indent=1, default=str),
                                        encoding="utf-8")
    print("\n".join(L[-14:]))


if __name__ == "__main__":
    main()
