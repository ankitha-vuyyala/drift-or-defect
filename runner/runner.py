"""Job runner for the drift-or-defect project.

Started by Windows Task Scheduler (at logon and every 5 minutes; a second copy exits at once if one is alive).
Watches jobs/queue/ for *.json job files and runs them one at a time, oldest first.

Job file format (jobs/queue/<NNN>_<name>.json):
    {
      "id": "003_pilot",                       # optional; defaults to the file stem
      "script": "code/pilot.py",               # a .py file INSIDE the project folder (required)
      "args": ["--split", "dev"],              # optional list of strings
      "timeout_min": 120,                      # optional, default 240
      "paid": false,                           # true if the job may call a paid model API
      "max_cost_usd": 0                        # paid jobs: spend allowed for this job (<= remaining approved cap)
    }

Safety rules enforced here:
  * only .py scripts that resolve inside the project folder are run, with the project venv's python, cwd = project;
    no shell is ever used;
  * .env is loaded into the child's environment only; values are never printed, and any value that appears in
    the job's output is replaced by *** before it is written to disk;
  * paid jobs are refused unless config/budget.json approves enough remaining spend (ledger: runs/cost_ledger.json);
    the job gets DOD_JOB_COST_CAP_USD and must stop itself at that cap (the LLM client enforces it per call);
  * a file named STOP in jobs/ pauses the runner (finishes nothing new until removed).

Outputs: jobs/status.json (state, current job, heartbeat, queue), jobs/heartbeat.txt, jobs/runner.log,
runs/jobs/<id>/output.log, and jobs/done|failed/<id>.json with the result.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0"
ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs"
QUEUE, DONE, FAILED = JOBS / "queue", JOBS / "done", JOBS / "failed"
STATUS, HEARTBEAT, LOG, LOCK = JOBS / "status.json", JOBS / "heartbeat.txt", JOBS / "runner.log", JOBS / "runner.lock"
BUDGET, LEDGER = ROOT / "config" / "budget.json", ROOT / "runs" / "cost_ledger.json"
HEARTBEAT_S = 60
STALE_LOCK_S = 300
IDLE_POLL_S = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    for i in range(20):  # Windows: an indexer or scanner may hold the target briefly
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05 * (i + 1))
    os.replace(tmp, path)


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def load_env() -> dict[str, str]:
    """Parse .env (KEY=VALUE lines). Values are returned for the child only and never logged."""
    env: dict[str, str] = {}
    p = ROOT / ".env"
    if not p.exists():
        return env
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v:
            env[k.strip()] = v
    return env


def redact(text: str, secrets: list[str]) -> str:
    for s in secrets:
        if len(s) >= 6:
            text = text.replace(s, "***")
    return text


def venv_python() -> str:
    for cand in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if cand.exists():
            return str(cand)
    return sys.executable


# ---------------------------------------------------------------- lock (single instance)
def acquire_lock() -> bool:
    info = read_json(LOCK, None)
    if info:
        age = time.time() - float(info.get("beat", 0))
        if age < STALE_LOCK_S:
            return False
        log(f"stale lock (age {age:.0f}s, pid {info.get('pid')}); taking over")
    write_json(LOCK, {"pid": os.getpid(), "beat": time.time(), "started": now()})
    return True


def touch_lock() -> None:
    write_json(LOCK, {"pid": os.getpid(), "beat": time.time()})


# ---------------------------------------------------------------- status
_state = {"state": "starting", "job": None, "job_started": None}


def queue_files() -> list[Path]:
    return sorted(QUEUE.glob("*.json"), key=lambda p: (p.stat().st_mtime, p.name))


def write_status() -> None:
    touch_lock()
    HEARTBEAT.write_text(now(), encoding="utf-8")
    write_json(STATUS, {
        "runner_version": VERSION, "pid": os.getpid(), "heartbeat": now(),
        "state": _state["state"], "job": _state["job"], "job_started": _state["job_started"],
        "queue": [p.name for p in queue_files()],
        "paused": (JOBS / "STOP").exists(),
        "spent_usd": round(spent_usd(), 4), "approved_cap_usd": approved_cap(),
    })


def heartbeat_loop(stop: threading.Event) -> None:
    while not stop.wait(HEARTBEAT_S):
        try:
            write_status()
        except Exception as e:  # never let the heartbeat kill the runner
            log(f"heartbeat error: {e!r}")


# ---------------------------------------------------------------- budget
def approved_cap() -> float:
    return float(read_json(BUDGET, {}).get("approved_cap_usd", 0.0))


def spent_usd() -> float:
    return float(read_json(LEDGER, {}).get("total_usd", 0.0))


# ---------------------------------------------------------------- run one job
def finish(job_path: Path, ok: bool, result: dict) -> None:
    dest = (DONE if ok else FAILED) / f"{job_path.stem}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    write_json(dest, result)
    try:
        job_path.unlink()
    except FileNotFoundError:
        pass


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def run_job(job_path: Path) -> None:
    spec = read_json(job_path, None)
    jid = (spec or {}).get("id") or job_path.stem
    result = {"id": jid, "job_file": job_path.name, "spec": spec, "queued_at_mtime": job_path.stat().st_mtime}
    if not isinstance(spec, dict) or "script" not in spec:
        result.update(status="rejected", reason="invalid job file (needs a 'script' field)", finished=now())
        finish(job_path, False, result)
        log(f"{jid}: rejected (invalid)")
        return
    script = (ROOT / spec["script"]).resolve()
    if ROOT not in script.parents or script.suffix != ".py" or not script.exists():
        result.update(status="rejected", reason="script must be an existing .py file inside the project",
                      finished=now())
        finish(job_path, False, result)
        log(f"{jid}: rejected (script outside project or missing)")
        return
    args = [str(a) for a in spec.get("args", [])]
    env = dict(os.environ)
    secrets = load_env()
    env.update(secrets)
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["DOD_PROJECT_ROOT"] = str(ROOT)
    env["DOD_JOB_ID"] = jid
    if spec.get("paid"):
        remaining = approved_cap() - spent_usd()
        want = float(spec.get("max_cost_usd", 0))
        if want <= 0 or want > remaining + 1e-9:
            result.update(status="rejected", finished=now(),
                          reason=f"paid job needs max_cost_usd within remaining approved budget ({remaining:.2f} USD)")
            finish(job_path, False, result)
            log(f"{jid}: rejected (budget)")
            return
        env["DOD_JOB_COST_CAP_USD"] = str(want)
    else:
        env["DOD_JOB_COST_CAP_USD"] = "0"     # free jobs may not spend anything

    out_dir = ROOT / "runs" / "jobs" / jid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_log = out_dir / "output.log"
    timeout_s = 60 * float(spec.get("timeout_min", 240))
    _state.update(state="running", job=jid, job_started=now())
    write_status()
    log(f"{jid}: start {spec['script']} {' '.join(args)}")
    t0 = time.time()
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with out_log.open("w", encoding="utf-8") as f:
        proc = subprocess.Popen([venv_python(), str(script), *args], cwd=str(ROOT), env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace", creationflags=flags)
        fired = threading.Event()

        def on_timeout():
            fired.set()
            kill_tree(proc)
            log(f"{jid}: timeout after {timeout_s / 60:.0f} min, killed")

        killer = threading.Timer(timeout_s, on_timeout)
        killer.daemon = True
        killer.start()
        secret_vals = list(secrets.values())
        for line in proc.stdout:
            f.write(redact(line, secret_vals))
            f.flush()
        proc.wait()
        killer.cancel()
        timed_out = fired.is_set()
    dur = time.time() - t0
    rc = proc.returncode
    tail = out_log.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
    ok = rc == 0 and not timed_out
    result.update(status="ok" if ok else ("timeout" if timed_out else "error"), returncode=rc,
                  started=_state["job_started"], finished=now(), duration_s=round(dur, 1),
                  log=str(out_log.relative_to(ROOT)), log_tail=tail)
    finish(job_path, ok, result)
    log(f"{jid}: {result['status']} rc={rc} in {dur:.0f}s")
    _state.update(state="idle", job=None, job_started=None)
    write_status()


# ---------------------------------------------------------------- main
def main() -> None:
    for d in (QUEUE, DONE, FAILED):
        d.mkdir(parents=True, exist_ok=True)
    if not acquire_lock():
        return  # another runner is alive
    log(f"runner {VERSION} started (pid {os.getpid()}, python {venv_python()})")
    stop = threading.Event()
    threading.Thread(target=heartbeat_loop, args=(stop,), daemon=True).start()
    once = "--once" in sys.argv
    try:
        while True:
            _state.update(state="paused" if (JOBS / "STOP").exists() else "idle")
            write_status()
            if not (JOBS / "STOP").exists():
                q = queue_files()
                if q:
                    try:
                        run_job(q[0])
                    except Exception as e:
                        log(f"runner error on {q[0].name}: {e!r}")
                        finish(q[0], False, {"id": q[0].stem, "status": "runner_error", "error": repr(e),
                                             "finished": now()})
                        _state.update(state="idle", job=None, job_started=None)
                    continue
            if once:
                break
            time.sleep(IDLE_POLL_S)
    finally:
        stop.set()
        _state.update(state="stopped")
        write_status()
        try:
            LOCK.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
