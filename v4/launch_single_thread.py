"""Run a project script with a fixed number of OpenMP/BLAS threads per process (default 1).

run_cases.py runs cases in a process pool; scikit-learn's histogram gradient boosting otherwise starts one OpenMP
thread per core in every worker, and the workers then slow each other down. This launcher only sets the thread
environment variables and runs the script unchanged in a child process (it is not part of the frozen code).

usage: python v4/launch_single_thread.py [--threads=N] <script.py inside the project> [args ...]
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
argv = sys.argv[1:]
threads = "1"
if argv and argv[0].startswith("--threads="):
    threads = str(int(argv.pop(0).split("=", 1)[1]))
script = (ROOT / argv[0]).resolve()
if ROOT not in script.parents or script.suffix != ".py":
    raise SystemExit(f"refusing to run {script}")
env = dict(os.environ, OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS=threads, MKL_NUM_THREADS=threads)
sys.exit(subprocess.run([sys.executable, str(script), *argv[1:]], env=env, cwd=str(ROOT)).returncode)
