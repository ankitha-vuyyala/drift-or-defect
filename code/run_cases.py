"""Run cases: ground truth, observations, every diagnosis method, and the outcome of each recommended action.

usage: python code/run_cases.py --domain acs --split dev [--methods a,b] [--limit N] [--workers 4] [--out NAME]
Writes runs/<out>/<domain>.jsonl (one record per case, resumable) and runs/<out>/<domain>.errors.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os

os.environ.setdefault("OMP_NUM_THREADS", "4")      # several workers share the machine; avoid oversubscription
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
import sys
import time
import traceback
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.simplefilter("ignore")

from dod import bench, cases, diag, methods  # noqa: E402
from dod.core import ROOT, Executor  # noqa: E402
from dod.domains import get_domain  # noqa: E402


def run_one(domain: str, case_json: dict, split: str, method_names: list[str]) -> dict:
    warnings.simplefilter("ignore")
    from dod.core import state_from_json
    dom = get_domain(domain)
    case = bench.Case(case_json["case_id"], domain, case_json["p0"], case_json["p1"],
                      state_from_json(case_json["state"]), state_from_json(case_json["spec"]),
                      case_json["injected"], case_json["tier"], case_json["meta"])
    ex = Executor(dom.PIPELINE)
    t0 = time.time()
    ref = bench.build_reference(domain, case.p0, ex)
    gt = bench.ground_truth(case, ref, ex, methods.DELTA_RETRAIN)
    obs = diag.observe(case, ref, ex)
    rec = {"case": case.to_json(), "split": split, "gt": gt,
           "obs": {k: v for k, v in obs.__dict__.items() if k not in ("lineage", "components")}}
    rec["methods"] = {}
    for m in method_names:
        tb = diag.Toolbox(case, ref, ex)
        tm = time.time()
        try:
            d = methods.ALL_METHODS[m](obs, tb, dom)
            d.cost_s = tb.cost_s
            dj = d.to_json()
        except Exception as e:
            dj = {"method": m, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:],
                  "fix": [], "retrain": False, "cost_s": tb.cost_s}
        dj["wall_s"] = round(time.time() - tm, 2)
        out = bench.action_outcomes(case, ref, ex, fix_sets=[dj["fix"]])
        dj["outcome"] = out[bench.action_key(dj["fix"], dj["retrain"])]
        rec["methods"][m] = dj
    rec["oracle"] = gt["correct_action"]
    rec["wall_s"] = round(time.time() - t0, 1)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True)
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--methods", default=",".join(m for m in methods.METHODS))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="dev_runs")
    a = ap.parse_args()
    out_dir = ROOT / "runs" / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_p, err_p = out_dir / f"{a.domain}.jsonl", out_dir / f"{a.domain}.errors.jsonl"
    done = set()
    if out_p.exists():
        for line in out_p.read_text(encoding="utf-8").splitlines():
            done.add(json.loads(line)["case"]["case_id"])
    if a.split in ("test", "all"):
        import freeze
        print("protocol freeze verified:", freeze.check()[:16], flush=True)
    all_cases = [(s, c) for s, c in cases.generate(a.domain) if a.split == "all" or s == a.split]
    todo = [(s, c) for s, c in all_cases if c.case_id not in done]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{a.domain} {a.split}: {len(all_cases)} cases, {len(done)} done, running {len(todo)}", flush=True)
    # build reference models first (once, sequentially) so workers do not race on them
    ex = Executor(get_domain(a.domain).PIPELINE)
    for p0 in sorted({c.p0 for _, c in todo}):
        r = bench.build_reference(a.domain, p0, ex)
        print(f"reference {a.domain} {p0}: holdout acc {r.perf_hold:.4f}", flush=True)
    names = a.methods.split(",")
    t0 = time.time()
    n_ok = n_err = 0
    jobs = [(a.domain, c.to_json(), s, names) for s, c in todo]
    # group by (p0, p1) so that a worker reuses cached pipeline outputs
    jobs.sort(key=lambda j: (j[1]["p0"], j[1]["p1"]))

    def write(rec=None, err=None):
        nonlocal n_ok, n_err
        if rec is not None:
            with out_p.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, default=str) + "\n")
            n_ok += 1
            m = rec["methods"].get("dod", {})
            print(f"[{n_ok + n_err}/{len(jobs)}] {rec['case']['case_id']} gt={rec['oracle']} "
                  f"dod={m.get('fix')}/{m.get('retrain')} {rec['wall_s']}s", flush=True)
        else:
            with err_p.open("a", encoding="utf-8") as f:
                f.write(json.dumps(err) + "\n")
            n_err += 1
            print(f"[{n_ok + n_err}/{len(jobs)}] ERROR {err['case_id']}: {err['error'][:300]}", flush=True)
    if a.workers <= 1:
        for j in jobs:
            try:
                write(rec=run_one(*j))
            except Exception as e:
                write(err={"case_id": j[1]["case_id"], "error": f"{type(e).__name__}: {e}",
                           "trace": traceback.format_exc()[-2000:]})
    else:
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            futs = {pool.submit(run_one, *j): j for j in jobs}
            for fu in as_completed(futs):
                j = futs[fu]
                try:
                    write(rec=fu.result())
                except Exception as e:
                    write(err={"case_id": j[1]["case_id"], "error": f"{type(e).__name__}: {e}",
                               "trace": traceback.format_exc()[-2000:]})
    print(f"done: {n_ok} ok, {n_err} errors, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
