"""Benchmark construction checks for the v2 domains (no diagnosis method is run): builds the reference artifacts,
runs the correct (spec) pipeline on every period, and reports rows, label rate and missing rates of the model
inputs; then builds the reference models and reports their holdout accuracy on each current period of the case
pairs under the correct pipeline (how much the world alone moves performance).

usage: python v2/code/check_domains.py divvy [hmda bts]   -> runs/v2_checks/<domain>.json
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DOD_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
warnings.simplefilter("ignore")

import numpy as np  # noqa: E402

from dod import bench, cases  # noqa: E402
from dod.core import ROOT, Executor  # noqa: E402
from dod.domains import get_domain  # noqa: E402


def main(domain: str) -> None:
    dom = get_domain(domain)
    out_p = ROOT / "runs" / "v2_checks" / f"{domain}.json"
    out_p.parent.mkdir(parents=True, exist_ok=True)
    if domain == "divvy":
        dom.build_station_artifact()
    if domain == "bts":
        dom.build_airport_artifact("2015-01")
    ex = Executor(dom.PIPELINE)
    res = {"periods": {}, "references": {}}
    p0s = list(cases.PAIRS[domain])
    for p0 in p0s:
        t = time.time()
        ref = bench.build_reference(domain, p0, ex)
        res["references"][p0] = {"holdout_acc": ref.perf_hold, "secs": round(time.time() - t, 1), "by_period": {}}
        print(f"reference {p0}: holdout acc {ref.perf_hold:.4f}", flush=True)
    for period in dom.PERIODS:
        t = time.time()
        row = {}
        try:
            spec = dom.spec_state(period, f"p0_{p0s[0]}")
            out = bench.with_split(dom, ex.run(period, spec))
            row = {"rows": int(len(out)), "label_rate": round(float(out[dom.LABEL].mean()), 4),
                   "missing": {c: round(float(np.isnan(out[c].to_numpy(dtype="float64")).mean()), 4)
                               for c in dom.FEATURES}}
            for p0 in p0s:
                if period in cases.PAIRS[domain][p0]:
                    ref = bench.build_reference(domain, p0, ex)
                    sp0 = dom.spec_state(period, ref.encoder_id)
                    o = bench.with_split(dom, ex.run(period, sp0))
                    acc = bench.score(dom, ref.model, o[o["_split"] == "hold"])
                    res["references"][p0]["by_period"][period] = round(acc, 4)
                    row[f"acc_ref_{p0}"] = round(acc, 4)
        except Exception as e:
            row = {"error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}
        row["secs"] = round(time.time() - t, 1)
        res["periods"][period] = row
        print(period, {k: v for k, v in row.items() if k not in ("missing", "trace")}, flush=True)
        if "missing" in row:
            hi = {k: v for k, v in row["missing"].items() if v > 0.02}
            if hi:
                print("   missing > 2%:", hi, flush=True)
        out_p.write_text(json.dumps(res, indent=1))
    print("written", out_p)


if __name__ == "__main__":
    for d in sys.argv[1:]:
        main(d)
