"""Post-hoc split of every round's consequential cases by whether their period range contains a published source
change (not pre-registered; computed after round 3, extended to round 4). Theorem 2 predicts that re-execution identifies defects
exactly when no change was forced by the source; Theorem 3 that forced changes are not identifiable by re-execution.

usage: python posthoc/by_change.py   -> runs/posthoc_by_change.json
       (round 1: runs/final, test split; round 2: runs/v2main; round 3: runs/v3main; all LLM records included)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import summarize as S1  # noqa: E402

RUNS = {"round1": ("final", "test"), "round2": ("v2main", None), "round3": ("v3main", None),
        "round4": ("v4main", None)}


def main() -> None:
    res = {}
    for rnd, (run, split) in RUNS.items():
        recs = S1.load(ROOT / "runs" / run)
        out = {"change": {}, "no_change": {}}
        unt = [0, 0, 0, 0]       # round 4, change in range: cases; all consequential untouched; dod4 correct; C in F or U
        for r in recs:
            if split and r["split"] != split:
                continue
            if not r["gt"]["consequential"]:
                continue
            key = "change" if r["obs"].get("source_events") else "no_change"
            d4 = r["methods"].get("dod4")
            if key == "change" and d4:
                cons, cp = set(r["gt"]["consequential"]), set(d4["notes"].get("coupled", []))
                unt[0] += 1
                unt[1] += not (cons & cp)
                unt[2] += cons <= set(d4["fix"]) <= set(r["gt"]["defective"])
                unt[3] += cons <= set(d4["fix"]) | set(d4["notes"].get("unverified", {}))
            for m, v in S1.per_case(r).items():
                out[key].setdefault(m, []).append(float(v["diag_correct"]))
        res[rnd] = {k: {m: {"n": len(v), "diag_correct": sum(v) / len(v)} for m, v in d.items()}
                    for k, d in out.items()}
        if unt[0]:
            res[rnd]["change_untouched"] = {"n": unt[0], "all_consequential_untouched": unt[1], "dod4_correct": unt[2],
                                           "dod4_fixed_or_listed": unt[3]}
    dst = ROOT / "runs" / "posthoc_by_change.json"
    dst.write_text(json.dumps(res, indent=1), encoding="utf-8")
    for rnd, d in res.items():
        for k, v in d.items():
            if k == "change_untouched":
                print(rnd, k, v)
                continue
            print(rnd, k, {m: (x["n"], round(x["diag_correct"], 3)) for m, x in v.items()})


if __name__ == "__main__":
    main()
