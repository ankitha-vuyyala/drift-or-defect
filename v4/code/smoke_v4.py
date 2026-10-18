"""Crash-only smoke test for a round-4 domain, run before the freeze. For a small set of cases it runs every method
and prints only whether each method raised an exception; no diagnosis, ground truth or score is printed or saved.

usage: python v4/code/smoke_v4.py storm [chicago]   -> runs/v4_checks/<domain>.smoke.txt
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
import traceback
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("DOD_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
warnings.simplefilter("ignore")

from dod import bench, cases, diag, methods, methods_v2, methods_v3, methods_v4  # noqa: E402
from dod.core import ROOT, Executor  # noqa: E402
from dod.domains import get_domain  # noqa: E402

methods.ALL_METHODS.update(methods_v2.METHODS_V2)
methods.ALL_METHODS.update(methods_v3.METHODS_V3)
methods.ALL_METHODS.update(methods_v4.METHODS_V4)
MAX_CASES = 8


def pick(domain: str) -> list:
    """One case per tier, preferring periods that are dated source changes (where the new code paths run)."""
    dom = get_domain(domain)
    ev = {e[0] for e in getattr(dom, "EVENTS", [])}
    cs = [c for _, c in cases.generate(domain)]
    cs.sort(key=lambda c: (c.p1 not in ev, c.p1, c.case_id))
    out, seen = [], set()
    for c in cs:
        if c.tier not in seen:
            seen.add(c.tier)
            out.append(c)
    return out[:MAX_CASES]


def main(domain: str) -> None:
    dom = get_domain(domain)
    if hasattr(dom, "build_station_artifact"):
        dom.build_station_artifact()
    if hasattr(dom, "build_artifacts"):
        print("artifacts", dom.build_artifacts(), flush=True)
    lines = []
    for c in pick(domain):
        ex = Executor(dom.PIPELINE)
        errs = []
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ref = bench.build_reference(domain, c.p0, ex)
                bench.ground_truth(c, ref, ex, methods.DELTA_RETRAIN)
                obs = diag.observe(c, ref, ex)
        except Exception as e:
            errs.append(f"setup: {type(e).__name__}: {str(e)[:200]}")
            obs = None
        if obs is not None:
            for m, f in methods.ALL_METHODS.items():
                if m.startswith("llm_"):      # LLM agents are not run here (no paid calls before the freeze)
                    continue
                tb = diag.Toolbox(c, ref, ex)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        d = f(obs, tb, dom)
                        bench.action_outcomes(c, ref, ex, fix_sets=[d.fix])
                except Exception as e:
                    tr = traceback.format_exc().splitlines()
                    errs.append(f"{m}: {type(e).__name__}: {str(e)[:200]} | {tr[-3][:160] if len(tr) > 2 else ''}")
        line = f"{c.p0}>{c.p1} tier={c.tier} methods={sum(not m.startswith('llm_') for m in methods.ALL_METHODS)} errors={errs if errs else 'none'}"
        print(line, flush=True)
        lines.append(line)
    out = ROOT / "runs" / "v4_checks" / f"{domain}.smoke.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        main(d)
