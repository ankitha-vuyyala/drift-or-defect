"""Create the library environments used by T2 (real library-upgrade) defects, inside the project folder, and run
the behaviour probe in each: p15 (pandas 1.5.3) and p30 (pandas 3.0.6). "main" is the project venv, pinned to pandas
2.2.3. All share scikit-learn and pyarrow where the pins allow.

usage: python code/t2/setup_envs.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
ENVS = ROOT / "envs"
OUT = ROOT / "runs" / "t2_probe"
SPECS = {
    "p15": ["pandas==1.5.3", "numpy==1.26.4", "pyarrow==17.0.0", "scikit-learn==1.5.2", "scipy<1.15"],
    "p30": ["pandas==3.0.6", "numpy==2.4.6", "pyarrow==25.0.1", "scikit-learn==1.9.1"],
}
# The project venv ("main") is pinned to pandas 2.2.3: most benchmark runs execute in-process there, and the
# pandas-3 upgrade is the change under study (components moved to env p30 run in a subprocess).
MAIN_PINS = ["pandas==2.2.3", "numpy==2.2.6", "pyarrow==25.0.1", "scikit-learn==1.9.1", "scipy", "duckdb",
             "requests", "psutil", "matplotlib", "python-docx"]


def py(env: str) -> Path:
    return ENVS / env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(cmd: list, **kw) -> subprocess.CompletedProcess:
    print(">", " ".join(map(str, cmd)), flush=True)
    r = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, **kw)
    print((r.stdout or "")[-2000:], (r.stderr or "")[-2000:], flush=True)
    return r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = getattr(sys, "_base_executable", sys.executable)
    for env, pins in SPECS.items():
        if not py(env).exists():
            r = run([base, "-m", "venv", ENVS / env])
            if r.returncode:
                raise SystemExit(f"venv {env} failed")
        r = run([py(env), "-m", "pip", "install", "--disable-pip-version-check", "-q", *pins])
        if r.returncode:
            raise SystemExit(f"pip install for {env} failed")
    r = run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", *MAIN_PINS])
    if r.returncode:
        raise SystemExit("pip install for main failed")
    results = {}
    for env in ["p15", "main", "p30"]:
        exe = sys.executable if env == "main" else py(env)
        out = OUT / f"{env}.json"
        r = run([exe, ROOT / "code" / "t2" / "probe_snippets.py", out])
        results[env] = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"error": r.stderr[-500:]}
    keys = [k for k in results["main"] if k not in ("pandas", "numpy")]
    lines = ["# T2 probe: pandas behaviour by environment", "",
             "| idiom | " + " | ".join(f"{e} (pandas {results[e].get('pandas')})" for e in results) + " |",
             "|---|" + "---|" * len(results)]
    diffs = []
    for k in keys:
        vals = [results[e].get(k, "") for e in results]
        if len(set(vals)) > 1:
            diffs.append(k)
        cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")[:120]
        lines.append(f"| {'**' + k + '**' if k in diffs else k} | " + " | ".join(cell(v) for v in vals) + " |")
    lines += ["", f"Differing idioms: {len(diffs)} of {len(keys)}: {', '.join(diffs)}"]
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
