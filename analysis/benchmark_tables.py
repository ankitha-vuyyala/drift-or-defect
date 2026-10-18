"""Benchmark description tables for the paper, generated from the code and data (no hand-typed numbers).

Outputs runs/benchmark/tables.json and tables.md:
  domains      periods, sampled rows per period (bronze), pipeline components and edges
  events       raw-schema events with dates and affected columns (from each domain's source_events)
  catalog      every change type: id, component, kind, tier, description, periods where applicable
  t2           pandas idioms whose behaviour differs between environments (runs/t2_probe)
  cases        number of cases per domain x split x scenario x tier
usage: python analysis/benchmark_tables.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from dod import cases  # noqa: E402
from dod.domains import get_domain  # noqa: E402

OUT = ROOT / "runs" / "benchmark"
OUT.mkdir(parents=True, exist_ok=True)
REF = {"acs": "2014", "tlc": "2015-01", "news": "2012"}
LAST = {"acs": "2024", "tlc": "2026-07", "news": "2022"}


def main() -> None:
    res = {"domains": {}, "events": {}, "catalog": {}, "cases": {}}
    bronze = json.loads((ROOT / "data" / "bronze" / "BRONZE_MANIFEST.json").read_text())
    for d in ("acs", "tlc", "news"):
        dom = get_domain(d)
        pipe = dom.PIPELINE
        rows = {k.split("/", 1)[1]: v.get("rows") for k, v in bronze.items() if k.startswith(d + "/")}
        res["domains"][d] = {
            "periods": len(dom.PERIODS), "first": dom.PERIODS[0], "last": dom.PERIODS[-1],
            "bronze_rows": rows, "task": dom.TASK, "features": len(dom.FEATURES),
            "components": [{"name": c, "inputs": pipe.components[c].inputs, "doc": pipe.components[c].doc,
                            "variants": sorted(pipe.components[c].variants)} for c in pipe.order()]}
        res["events"][d] = dom.source_events(REF[d], LAST[d])
        seen = {}
        for p in dom.PERIODS:
            for it in dom.catalog(p, f"p0_{REF[d]}"):
                e = seen.setdefault(it["id"], {k: it[k] for k in ("component", "kind", "tier", "note")})
                e.setdefault("periods", []).append(p)
        for v in seen.values():
            v["first_period"], v["n_periods"] = v["periods"][0], len(v["periods"])
            del v["periods"]
        res["catalog"][d] = seen
        cnt = Counter()
        for split, c in cases.generate(d):
            cnt[(split, c.meta.get("scenario"), c.tier)] += 1
        res["cases"][d] = {"|".join(k): v for k, v in sorted(cnt.items())}
    t2p = ROOT / "runs" / "t2_probe"
    if (t2p / "main.json").exists():
        envs = {e: json.loads((t2p / f"{e}.json").read_text()) for e in ("p15", "main", "p30")}
        res["t2"] = {"versions": {e: envs[e]["pandas"] for e in envs},
                     "differing": {k: {e: envs[e][k] for e in envs} for k in envs["main"]
                                   if k not in ("pandas", "numpy") and len({envs[e].get(k) for e in envs}) > 1}}
    (OUT / "tables.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    lines = ["# Benchmark tables", ""]
    for d in res["domains"]:
        D = res["domains"][d]
        lines += [f"## {d}", f"- periods: {D['periods']} ({D['first']}..{D['last']}); task {D['task']}; "
                  f"{D['features']} model inputs; {len(D['components'])} components",
                  "- events: " + "; ".join(f"{e.get('period')} {e['change']}" for e in res["events"][d]),
                  "- catalog:"]
        for k, v in res["catalog"][d].items():
            lines.append(f"  - {k} [{v['tier']}/{v['kind']}] {v['component']}: {v['note']} (from {v['first_period']})")
        lines.append(f"- cases: {res['cases'][d]}")
        lines.append("")
    (OUT / "tables.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
