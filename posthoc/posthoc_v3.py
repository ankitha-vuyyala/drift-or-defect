"""Post-hoc analysis of the round-3 records (not pre-registered; written after the round-3 results were seen).
For every component a DoD version blamed although it was not an effective defect, records the evidence behind the
blame (effect test, a current version that leaves values missing, a boundary flag of a given kind) and the published
change and column it was raised at. Also reports the false-blame rate of each DoD version per domain.

usage: python posthoc/posthoc_v3.py runs/v3main   -> runs/v3main/posthoc_v3.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

METHODS = ("dod", "dod2", "dod3")


def kind(flag: dict) -> str:
    if "invariant" in flag:
        return "invariant"
    if "retention" in flag:
        return "lost records"
    if "why" in flag:
        return "missing values" if "missing" in flag["why"] else "version fails"
    if flag.get("introduced", 0) <= flag.get("threshold", 0) and flag.get("missing_jump", 0) > 0:
        return "missing values"
    return "distribution jump"


def main(run: Path) -> None:
    res = {}
    for d in ("cabi", "fars", "landreg"):
        recs = [json.loads(x) for x in (run / f"{d}.jsonl").read_text(encoding="utf-8").splitlines()]
        res[d] = {"n_cases": len(recs)}
        for m in METHODS:
            why, where, comp = Counter(), Counter(), Counter()
            n_fb = 0
            for r in recs:
                dd = r["methods"][m]
                notes = dd.get("notes") or {}
                wrong = set(dd["fix"]) - set(r["gt"]["defective"])
                n_fb += bool(wrong)
                for c in wrong:
                    comp[c] += 1
                    if c in (notes.get("current_loses_values") or []):
                        why["current version leaves values missing"] += 1
                    elif c in (notes.get("harmful") or []):
                        why["effect test"] += 1
                    else:
                        flags = (notes.get("boundary") or {}).get(c) or []
                        ks = sorted({kind(f) for f in flags}) or ["other"]
                        why["boundary: " + " + ".join(ks)] += 1
                        for f in flags:
                            where[f"{c} @ {f.get('event')} : {f.get('column') or kind(f)}"] += 1
            res[d][m] = {"false_blame": n_fb / len(recs), "wrong_components": dict(comp.most_common()),
                         "evidence": dict(why.most_common()), "flag_sites": dict(where.most_common(10))}
    # consequential cases with and without a published change in their period range (all three domains)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
    import summarize as S1
    split = {"no_change": {}, "change": {}}
    for d in ("cabi", "fars", "landreg"):
        for x in (run / f"{d}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(x)
            if not r["gt"]["consequential"]:
                continue
            key = "change" if r["obs"].get("source_events") else "no_change"
            for m, v in S1.per_case(r).items():
                split[key].setdefault(m, []).append(float(v["diag_correct"]))
    res["consequential_by_change"] = {k: {m: {"n": len(v), "diag_correct": sum(v) / len(v)} for m, v in d.items()}
                                      for k, d in split.items()}
    out = run / "posthoc_v3.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
