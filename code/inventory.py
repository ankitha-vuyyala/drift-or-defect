"""Free inventory (no model calls, no paid APIs). Standard library only, so it runs in a fresh venv.

Writes runs/inventory/inventory.json and runs/inventory/inventory.md. Never prints .env values (key NAMES only).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parent.parent))
OUT = ROOT / "runs" / "inventory"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "drift-or-defect-inventory/1.0 (research; contact via repo)"}


def sh(cmd: list[str], timeout: int = 60) -> dict:
    exe = shutil.which(cmd[0])
    if not exe:
        return {"available": False}
    try:
        p = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return {"available": True, "rc": p.returncode, "out": (p.stdout or p.stderr).strip()[:3000]}
    except Exception as e:
        return {"available": True, "error": repr(e)}


def http(url: str, method: str = "HEAD", timeout: int = 20, read: int = 0) -> dict:
    req = urllib.request.Request(url, method=method, headers=UA)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(read).decode("utf-8", "replace") if read else ""
            return {"ok": True, "status": r.status, "ms": int(1000 * (time.time() - t0)),
                    "content_length": r.headers.get("Content-Length"), "body": body}
    except urllib.error.HTTPError as e:   # reachable, but refused (e.g. 401 without a key)
        return {"ok": True, "status": e.code, "ms": int(1000 * (time.time() - t0))}
    except Exception as e:
        return {"ok": False, "error": repr(e)[:300]}


def system() -> dict:
    info = {"os": platform.platform(), "machine": platform.machine(), "cpus": os.cpu_count(),
            "python": sys.version.split()[0], "python_exe": sys.executable}
    du = shutil.disk_usage(ROOT)
    info["disk_free_gb"] = round(du.free / 1e9, 1)
    try:
        import ctypes  # Windows RAM

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong), ("c", ctypes.c_ulonglong),
                        ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        info["ram_gb"] = round(m.ullTotalPhys / 1e9, 1)
        info["ram_free_gb"] = round(m.ullAvailPhys / 1e9, 1)
    except Exception:
        pass
    return info


def tools() -> dict:
    return {
        "git": sh(["git", "--version"]),
        "uv": sh(["uv", "--version"]),
        "docker": sh(["docker", "version", "--format", "{{.Server.Version}}"]),
        "nvidia_smi": sh(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
        "ollama_cli": sh(["ollama", "--version"]),
        "conda": sh(["conda", "--version"]),
        "pip_pandas_versions": sh([sys.executable, "-m", "pip", "index", "versions", "pandas"], timeout=90),
        "pip_sklearn_versions": sh([sys.executable, "-m", "pip", "index", "versions", "scikit-learn"], timeout=90),
        "py_launcher": sh(["py", "--list"]),
    }


def ollama() -> dict:
    r = http("http://localhost:11434/api/tags", method="GET", read=200000, timeout=10)
    if r.get("ok") and r.get("status") == 200:
        try:
            models = json.loads(r["body"]).get("models", [])
            return {"running": True, "models": [{"name": m.get("name"),
                                                 "size_gb": round(m.get("size", 0) / 1e9, 1),
                                                 "params": (m.get("details") or {}).get("parameter_size"),
                                                 "quant": (m.get("details") or {}).get("quantization_level")}
                                                for m in models]}
        except Exception as e:
            return {"running": True, "parse_error": repr(e)}
    return {"running": False, "detail": {k: v for k, v in r.items() if k != "body"}}


def env_keys() -> dict:
    p = ROOT / ".env"
    if not p.exists():
        return {"env_file": False}
    names = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            names.append({"name": k.strip(), "has_value": bool(v.strip().strip('"').strip("'"))})
    return {"env_file": True, "keys": names}


NET = {
    # data sources
    "census_pums_2019_index": "https://www2.census.gov/programs-surveys/acs/data/pums/2019/1-Year/",
    "census_api_relshipp": "https://api.census.gov/data/2019/acs/acs1/pums/variables/RELSHIPP.json",
    "census_api_relp_2018": "https://api.census.gov/data/2018/acs/acs1/pums/variables/RELP.json",
    "tlc_yellow_2024_01": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet",
    "tlc_yellow_2016_06": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2016-06.parquet",
    "tlc_yellow_2025_03": "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-03.parquet",
    "tlc_zone_lookup": "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
    "citibike_index": "https://s3.amazonaws.com/tripdata/index.html",
    "huggingface": "https://huggingface.co/api/datasets?search=news%20category&limit=20",
    "kaggle": "https://www.kaggle.com/",
    "github_folktables": "https://github.com/socialfoundations/folktables",
    "pypi": "https://pypi.org/simple/pandas/",
    "pythonhosted": "https://files.pythonhosted.org/",
    "noaa_ghcn": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/",
    "bls_cpi": "https://download.bls.gov/pub/time.series/cu/",
    # model endpoints (reachability only; no key sent, 401 = reachable)
    "openai_api": "https://api.openai.com/v1/models",
    "groq_api": "https://api.groq.com/openai/v1/models",
    "gemini_api": "https://generativelanguage.googleapis.com/v1beta/models",
}


def network() -> dict:
    res = {}
    for name, url in NET.items():
        method = "GET" if name in ("huggingface", "census_api_relshipp", "census_api_relp_2018") else "HEAD"
        r = http(url, method=method, read=20000 if method == "GET" else 0)
        if name == "huggingface" and r.get("status") == 200:
            try:
                r["datasets"] = [d.get("id") for d in json.loads(r["body"])]
            except Exception:
                pass
        r.pop("body", None)
        res[name] = {"url": url, **r}
    return res


def main() -> None:
    t0 = time.time()
    inv = {"generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "project_root": str(ROOT), "system": system(), "tools": tools(), "ollama": ollama(),
           "env": env_keys(), "network": network()}
    inv["elapsed_s"] = round(time.time() - t0, 1)
    (OUT / "inventory.json").write_text(json.dumps(inv, indent=2), encoding="utf-8")
    lines = ["# Inventory", "", f"Generated {inv['generated']} in {inv['elapsed_s']} s", "", "## System"]
    lines += [f"- {k}: {v}" for k, v in inv["system"].items()]
    lines += ["", "## Tools"]
    for k, v in inv["tools"].items():
        lines.append(f"- {k}: " + (v.get("out", "").splitlines()[0][:150] if v.get("out") else
                                   ("not found" if not v.get("available") else str(v)[:150])))
    lines += ["", "## Local models (Ollama)"]
    o = inv["ollama"]
    lines += [f"- {m}" for m in o.get("models", [])] if o.get("running") else ["- Ollama not running"]
    lines += ["", "## .env key names"]
    lines += [f"- {k['name']}: {'set' if k['has_value'] else 'empty'}" for k in inv["env"].get("keys", [])] or \
             ["- no .env file"]
    lines += ["", "## Network", "", "| target | ok | status | MB | ms |", "|---|---|---|---|---|"]
    for k, v in inv["network"].items():
        mb = round(int(v["content_length"]) / 1e6, 1) if v.get("content_length") else ""
        lines.append(f"| {k} | {v.get('ok')} | {v.get('status', v.get('error', ''))} | {mb} | {v.get('ms', '')} |")
    (OUT / "inventory.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
