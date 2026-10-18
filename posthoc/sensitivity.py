"""Sensitivity analyses (not pre-registered): leave-one-domain-out and leave-one-event-out for the main comparisons
of each round.

  domain : for every round and every held-out domain left out, the primary endpoint (correct diagnosis on
           consequential cases) of the round's DoD version, of DoD, and of the best other method run on all cases
           of the remaining domains, and the false-blame rate on cases spanning a published change.
  event  : for every published change (domain, period), the same quantities on the cases whose period range does
           not contain that change.

usage: python posthoc/sensitivity.py   -> runs/posthoc_sensitivity.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import summarize as S1  # noqa: E402

sys.path.insert(0, str(ROOT / "v4" / "analysis"))
import metrics_v4 as M4  # noqa: E402

RUNS = {"round1": ("final", "test", "dod"), "round2": ("v2main", None, "dod2"), "round3": ("v3main", None, "dod3"),
        "round4": ("v4main", None, "dod4")}
BASE = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
        "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna"]


def stats(rows: list) -> dict:
    """rows: (per_case dict, record)"""
    cons = [p for p, r in rows if r["gt"]["consequential"]]
    ev = [p for p, r in rows if r["obs"].get("source_events")]
    out = {"n_cases": len(rows), "n_cons": len(cons)}
    for m in {m for p, _ in rows for m in p}:
        c = [float(p[m]["diag_correct"]) for p in cons if m in p]
        f = [float(p[m]["false_blame"]) for p in ev if m in p]
        out[m] = {"n": len(c), "correct": float(np.mean(c)) if c else None,
                  "false_blame_events": float(np.mean(f)) if f else None}
        if m.startswith("dod4"):        # three-verdict metrics (round 4)
            tv = [M4.case_metrics(r, m) for p, r in rows if m in p]
            tc = [x for x in tv if x["has_cons"]]
            out[m].update({"false_blame_all": float(np.mean([x["false_blame"] for x in tv])) if tv else None,
                           "silent_miss_cons": float(np.mean([x["silent_miss"] for x in tc])) if tc else None,
                           "coverage": float(np.mean([x["decided"] for x in tv])) if tv else None})
    full = [m for m in BASE if m in out and out[m]["n"] == len(cons)]
    best = max(full, key=lambda m: out[m]["correct"] if out[m]["correct"] is not None else -1) if full else None
    out["best_full_baseline"] = best
    return out


def main() -> None:
    res = {}
    for rnd, (run, split, mine) in RUNS.items():
        recs = [r for r in S1.load(ROOT / "runs" / run) if not split or r["split"] == split]
        rows = [(S1.per_case(r), r) for r in recs]
        doms = sorted({r["case"]["domain"] for r in recs})
        res[rnd] = {"method": mine, "all": stats(rows), "leave_domain_out": {}, "leave_event_out": {}}
        for d in doms:
            res[rnd]["leave_domain_out"][d] = stats([(p, r) for p, r in rows if r["case"]["domain"] != d])
        events = sorted({(r["case"]["domain"], str(e.get("period", e.get("year"))))
                         for r in recs for e in r["obs"].get("source_events") or []})
        for d, per in events:
            keep = [(p, r) for p, r in rows if not (r["case"]["domain"] == d and any(
                str(e.get("period", e.get("year"))) == per for e in r["obs"].get("source_events") or []))]
            res[rnd]["leave_event_out"][f"{d} {per}"] = stats(keep)
    dst = ROOT / "runs" / "posthoc_sensitivity.json"
    dst.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for rnd, v in res.items():
        m = v["method"]
        lo = [(k, round(x[m]["correct"], 3), x["best_full_baseline"],
               round(x[x["best_full_baseline"]]["correct"], 3) if x["best_full_baseline"] else None)
              for k, x in v["leave_domain_out"].items() if m in x]
        ev = [x[m]["correct"] for x in v["leave_event_out"].values() if x[m]["correct"] is not None]
        print(rnd, m, "all", round(v["all"][m]["correct"], 3), "LODO", lo, "LOEO range",
              (round(min(ev), 3), round(max(ev), 3)) if ev else None)


if __name__ == "__main__":
    main()
