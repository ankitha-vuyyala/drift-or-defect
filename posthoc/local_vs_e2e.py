"""Post-hoc check of Theorem 2's two notions of effectiveness (not pre-registered). For every rollback test that a
DoD version ran in rounds 1-4, compare the local verdict (the component's own output differs from the reference
version's on the same inputs) with end-to-end effectiveness (replacing the component by its specification changes
the final pipeline output; ground truth 'defective'). Round 4 (DoD-4) is included from its records. Components are classified as unforced when the specification of
the current period equals the specification of the reference period for that component.

usage: python posthoc/local_vs_e2e.py   -> runs/posthoc_local_vs_e2e.json
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DOD_PROJECT_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "v4" / "code"))
from dod.domains import get_domain  # noqa: E402

RUNS = {"round1": "final", "round2": "v2main", "round3": "v3main", "round4": "v4main"}
METHODS = ("dod", "dod2", "dod3", "dod4")


def main() -> None:
    res = {}
    examples = []
    for rnd, run in RUNS.items():
        cnt, prop = Counter(), Counter()
        for f in sorted((ROOT / "runs" / run).glob("*.jsonl")):
            if ".llm_" in f.name or f.name.endswith("errors.jsonl"):
                continue
            for line in f.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                c = r["case"]
                if rnd == "round1" and r.get("split") != "test":
                    continue
                dom = get_domain(c["domain"])
                enc = f"p0_{c['p0']}"
                s0 = {k: v.to_json() for k, v in dom.spec_state(c["p0"], enc).items()}
                s1 = {k: v.to_json() for k, v in dom.spec_state(c["p1"], enc).items()}
                eff = set(r["gt"]["defective"])
                seen = set()
                for m in METHODS:
                    d = r["methods"].get(m)
                    if not d:
                        continue
                    if m == "dod4":            # propagation tests (Theorem 2c), counted for every DoD-4 call
                        for call in d.get("calls", []):
                            if call.get("tool") != "propagate" or not isinstance(call.get("arg"), str):
                                continue
                            comp, pv = call["arg"], (call.get("result") or {}).get("result")
                            if pv in ("equal", "differ"):
                                forced = json.dumps(s0.get(comp), sort_keys=True) != json.dumps(s1.get(comp),
                                                                                                sort_keys=True)
                                prop[("forced" if forced else "unforced", "propagate " + pv,
                                      "effective" if comp in eff else "not effective")] += 1
                    for call in d.get("calls", []):
                        if call.get("tool") != "rollback" or not isinstance(call.get("arg"), str):
                            continue
                        comp = call["arg"]
                        if comp in seen:
                            continue
                        seen.add(comp)
                        verdict = (call.get("result") or {}).get("result")
                        if verdict not in ("equal", "differ"):
                            continue
                        forced = json.dumps(s0.get(comp), sort_keys=True) != json.dumps(s1.get(comp), sort_keys=True)
                        key = ("forced" if forced else "unforced", verdict, "effective" if comp in eff else "not effective")
                        cnt[key] += 1
                        if not forced and verdict == "differ" and comp not in eff:
                            examples.append({"round": rnd, "case": c["case_id"], "component": comp})
                        if not forced and verdict == "equal" and comp in eff:
                            examples.append({"round": rnd, "case": c["case_id"], "component": comp,
                                             "note": "equal but effective"})
        res[rnd] = {" / ".join(k): v for k, v in sorted(cnt.items())}
        if prop:
            res[rnd + "_propagation"] = {" / ".join(k): v for k, v in sorted(prop.items())}
    res["exceptions"] = examples
    out = ROOT / "runs" / "posthoc_local_vs_e2e.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
