"""Benchmark description tables for all eleven domains (rounds 1-4), generated from the code and data.

Outputs runs/benchmark/tables_v4.json and tables_v4.md:
  domains      periods, rows per period (bronze parquet metadata), task, model inputs, pipeline components
  events       dated published source changes (each domain's source_events from its first reference period)
  catalog      every change type: id, component, kind, tier, description, first period, number of periods
  cases        number of cases per domain x split x scenario x tier
usage: python v4/analysis/benchmark_tables_v4.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DOD_PROJECT_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "v4" / "code"))
import pyarrow.parquet as pq  # noqa: E402

from dod import cases  # noqa: E402
from dod.domains import get_domain  # noqa: E402

OUT = ROOT / "runs" / "benchmark"
DOMAINS = {"acs": 1, "tlc": 1, "news": 1, "divvy": 2, "hmda": 2, "bts": 2, "cabi": 3, "fars": 3, "landreg": 3,
           "storm": 4, "chicago": 4}


def bronze_rows(d: str) -> dict:
    base = ROOT / "data" / "bronze" / d
    out = {}
    for p in sorted(base.rglob("*.parquet")):
        try:
            out[str(p.relative_to(base)).replace("\\", "/")] = pq.read_metadata(p).num_rows
        except Exception as e:  # noqa: BLE001
            out[str(p.relative_to(base))] = f"unreadable: {type(e).__name__}"
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"domains": {}, "events": {}, "catalog": {}, "cases": {}}
    for d, rnd in DOMAINS.items():
        dom = get_domain(d)
        pipe = dom.PIPELINE
        p0 = next(iter(cases.PAIRS[d]))
        rows = bronze_rows(d)
        res["domains"][d] = {
            "round": rnd, "periods": len(dom.PERIODS), "first": dom.PERIODS[0], "last": dom.PERIODS[-1],
            "bronze_files": len(rows), "bronze_rows": sum(v for v in rows.values() if isinstance(v, int)),
            "rows_by_file": rows, "task": dom.TASK, "features": len(dom.FEATURES), "label": dom.LABEL,
            "references": list(cases.PAIRS[d]),
            "components": [{"name": c, "inputs": pipe.components[c].inputs, "doc": pipe.components[c].doc,
                            "variants": sorted(pipe.components[c].variants)} for c in pipe.order()]}
        res["events"][d] = dom.source_events(p0, dom.PERIODS[-1])
        seen = {}
        for p in dom.PERIODS:
            for it in dom.catalog(p, f"p0_{p0}"):
                e = seen.setdefault(it["id"], {k: it.get(k, "") for k in ("component", "kind", "tier", "note",
                                                                         "source")})
                e.setdefault("periods", []).append(p)
        for v in seen.values():
            v["first_period"], v["n_periods"] = v["periods"][0], len(v["periods"])
            del v["periods"]
        res["catalog"][d] = seen
        cnt = Counter()
        for split, c in cases.generate(d):
            cnt[(split, c.meta.get("scenario"), c.tier)] += 1
        res["cases"][d] = {"|".join(k): v for k, v in sorted(cnt.items())}
        print(d, "done", flush=True)
    (OUT / "tables_v4.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    lines = ["# Benchmark tables (eleven domains)", ""]
    for d, D in res["domains"].items():
        lines += [f"## {d} (round {D['round']})",
                  f"- periods: {D['periods']} ({D['first']}..{D['last']}); task {D['task']}; {D['features']} model "
                  f"inputs; {len(D['components'])} components; {D['bronze_rows']:,} bronze rows in "
                  f"{D['bronze_files']} files",
                  "- events: " + "; ".join(f"{e.get('period')} {e['change']}" for e in res["events"][d]),
                  "- catalog:"]
        for k, v in res["catalog"][d].items():
            lines.append(f"  - {k} [{v['tier']}/{v['kind']}] {v['component']}: {v['note']} (from {v['first_period']})")
        lines.append(f"- cases: {sum(res['cases'][d].values())} {res['cases'][d]}")
        lines.append("")
    (OUT / "tables_v4.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
