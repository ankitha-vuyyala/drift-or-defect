"""Run methods (LLM-agent baselines, or any method in methods.ALL_METHODS) on cases already processed by
run_cases.py, reusing their observations, ground truth and cached pipeline outputs. Provider/model for the LLM
agents come from DOD_LLM_PROVIDER / DOD_LLM_MODEL or --provider/--model.

usage: python code/run_llm.py --run dev_v2 --domain acs [--modes report,tools] [--provider ollama --model qwen2.5:3b]
       [--limit N] [--tag local]          (LLM agents: methods llm_<mode>)
       python code/run_llm.py --run dev_v2 --domain acs --methods dod,dod_b1 --tag rerun
Writes runs/<run>/<domain>.llm_<tag>.jsonl (resumable). Paid providers obey the job's cost cap (dod/llm.py).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "4")
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.simplefilter("ignore")

from dod import bench, diag, methods  # noqa: E402
from dod.core import ROOT, Executor, state_from_json  # noqa: E402
from dod.domains import get_domain  # noqa: E402
from dod.llm import BudgetExceeded  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--domain", required=True)
    ap.add_argument("--modes", default="report,tools")
    ap.add_argument("--methods", default=None, help="comma list of methods.ALL_METHODS (overrides --modes)")
    ap.add_argument("--provider", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--split", default="all")
    ap.add_argument("--tag", default="local")
    ap.add_argument("--every", type=int, default=1, help="take every k-th case (spread a pilot over the file)")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--only-consequential", action="store_true",
                    help="restrict to cases whose ground truth has a consequential defect")
    a = ap.parse_args()
    if a.provider:
        os.environ["DOD_LLM_PROVIDER"] = a.provider
    if a.model:
        os.environ["DOD_LLM_MODEL"] = a.model
    run = ROOT / "runs" / a.run
    src = run / f"{a.domain}.jsonl"
    out_p = run / f"{a.domain}.llm_{a.tag}.jsonl"
    done = set()
    if out_p.exists():
        done = {json.loads(l)["case_id"] for l in out_p.read_text(encoding="utf-8").splitlines() if l.strip()}
    recs = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    recs = [r for r in recs if (a.split == "all" or r["split"] == a.split) and r["case"]["case_id"] not in done]
    if any(r["split"] == "test" for r in recs):
        import freeze
        print("protocol freeze verified:", freeze.check()[:16], flush=True)
    if a.only_consequential:
        recs = [r for r in recs if r["gt"]["consequential"]]
    recs = recs[:: max(1, a.every)]
    if a.limit:
        recs = recs[: a.limit]
    names = a.methods.split(",") if a.methods else [f"llm_{m}" for m in a.modes.split(",")]
    print(f"{a.domain}: {len(recs)} cases, methods {names}, provider {os.environ.get('DOD_LLM_PROVIDER')} "
          f"{os.environ.get('DOD_LLM_MODEL')}, workers {a.workers}", flush=True)
    t0 = time.time()
    n = 0
    jobs = [(a.domain, r, names) for r in recs]
    if a.workers <= 1:
        it = (one(*j) for j in jobs)
        for res in it:
            n += 1
            if write(out_p, res, n, len(jobs), t0):
                break
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            futs = [pool.submit(one, *j) for j in jobs]
            for fu in as_completed(futs):
                n += 1
                if write(out_p, fu.result(), n, len(jobs), t0):
                    for f in futs:
                        f.cancel()
                    break


def write(out_p, res, n, total, t0) -> bool:
    """Append one result; returns True when the budget stop was hit."""
    if res.get("budget_stop"):
        print(f"budget stop: {res['budget_stop']}", flush=True)
        return True
    with out_p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(res, default=str) + "\n")
    m = res["methods"]
    print(f"[{n}/{total}] {res['case_id']} oracle={res.get('oracle')} " +
          " ".join(f"{k}={v.get('fix')}/{v.get('retrain')} ${(v.get('notes') or {}).get('llm_usd', 0):.4f}"
                   for k, v in m.items()) + f" {time.time() - t0:.0f}s", flush=True)
    return False


def one(domain: str, r: dict, names: list[str]) -> dict:
    warnings.simplefilter("ignore")
    dom = get_domain(domain)
    ex = Executor(dom.PIPELINE)
    cj = r["case"]
    case = bench.Case(cj["case_id"], domain, cj["p0"], cj["p1"], state_from_json(cj["state"]),
                      state_from_json(cj["spec"]), cj["injected"], cj["tier"], cj["meta"])
    ref = bench.build_reference(domain, case.p0, ex)
    o = dict(r["obs"])
    o["lineage"] = dom.LINEAGE
    o["components"] = [{"name": c, "inputs": dom.PIPELINE.components[c].inputs} for c in dom.PIPELINE.order()]
    obs = diag.Observation(**o)
    res = {"case_id": case.case_id, "split": r["split"], "oracle": r["oracle"], "methods": {}}
    for mname in names:
        tb = diag.Toolbox(case, ref, ex)
        tm = time.time()
        try:
            d = methods.ALL_METHODS[mname](obs, tb, dom)
            d.cost_s = tb.cost_s
            dj = d.to_json()
        except BudgetExceeded as e:
            return {"budget_stop": str(e)}
        except Exception as e:
            dj = {"method": mname, "error": f"{type(e).__name__}: {e}", "fix": [], "retrain": False,
                  "cost_s": tb.cost_s, "trace": traceback.format_exc()[-1200:], "notes": {}}
        dj["wall_s"] = round(time.time() - tm, 2)
        outc = bench.action_outcomes(case, ref, ex, fix_sets=[dj["fix"]])
        dj["outcome"] = outc[bench.action_key(dj["fix"], dj["retrain"])]
        res["methods"][mname] = dj
    return res


if __name__ == "__main__":
    main()
