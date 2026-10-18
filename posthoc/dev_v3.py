"""DoD-3 on the development domains (rounds 1-2; in-sample for DoD-3, which was designed on them). Reads the final
development records (runs/v3dev/<domain>.llm_v3dev5.jsonl, DoD-3 decisions on a systematic sample of cases) joined
to the round-1/2 case records with ground truth and the DoD (and DoD-2) decisions on the same cases.

usage: python posthoc/dev_v3.py runs/v3dev   -> runs/v3dev/dev_v3.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DOMAINS = ("acs", "tlc", "news", "divvy", "hmda", "bts")


def main(run: Path, tag: str = "v3dev5") -> None:
    res = {}
    for d in DOMAINS:
        base = {}
        for line in (run / f"{d}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            base[r["case"]["case_id"]] = r
        rows = {m: {"cons": [], "fb": []} for m in ("dod", "dod2", "dod3")}
        n = 0
        for line in (run / f"{d}.llm_{tag}.jsonl").read_text(encoding="utf-8").splitlines():
            r3 = json.loads(line)
            b = base[r3["case_id"]]
            n += 1
            eff, cons = set(b["gt"]["defective"]), set(b["gt"]["consequential"])
            for m, dd in (("dod", b["methods"].get("dod")), ("dod2", b["methods"].get("dod2")),
                          ("dod3", r3["methods"]["dod3"])):
                if not dd:
                    continue
                fix = set(dd["fix"])
                rows[m]["fb"].append(bool(fix - eff))
                if cons:
                    rows[m]["cons"].append(cons <= fix <= eff)
        res[d] = {"n_cases": n, "n_consequential": len(rows["dod"]["cons"])}
        for m, v in rows.items():
            if v["fb"]:
                res[d][m] = {"diag_correct_cons": sum(v["cons"]) / len(v["cons"]) if v["cons"] else None,
                             "false_blame": sum(v["fb"]) / len(v["fb"])}
    out = run / "dev_v3.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
