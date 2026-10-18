"""Protocol freeze for round 3 (the v1 and v2 freezes are untouched). Covers v3/code, v3/analysis, v3/config,
v3/PROTOCOL_V3.md and analysis/summarize.py; writes runs/freeze_v3.json. Original v1 docstring follows.

Protocol freeze: SHA-256 over the experiment code, analysis code, configuration (except the budget file) and
PROTOCOL.md. `python code/freeze.py` writes runs/freeze.json; `check()` is called by run_cases.py and run_llm.py,
which refuse to process test-split cases unless the current digest equals the frozen one."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "v3"
FREEZE = ROOT / "runs" / "freeze_v3.json"


def files() -> list[Path]:
    out = sorted(p for d in ("code", "analysis") for p in (V2 / d).rglob("*.py") if "__pycache__" not in p.parts)
    out += sorted(p for p in (V2 / "config").glob("*.json"))
    out.append(V2 / "PROTOCOL_V3.md")
    out.append(ROOT / "analysis" / "summarize.py")        # v1 statistics imported by v3/analysis
    return out


def digest() -> tuple[str, dict]:
    h, per = hashlib.sha256(), {}
    for p in files():
        b = p.read_bytes().replace(b"\r\n", b"\n")
        rel = p.relative_to(ROOT).as_posix()
        per[rel] = hashlib.sha256(b).hexdigest()
        h.update(rel.encode() + b"\0" + b + b"\0")
    return h.hexdigest(), per


def check() -> str:
    if not FREEZE.exists():
        raise SystemExit("protocol not frozen: run v3/code/freeze.py before touching the test split")
    frozen = json.loads(FREEZE.read_text())
    cur, per = digest()
    if cur != frozen["sha256"]:
        changed = [k for k in set(per) | set(frozen["files"]) if per.get(k) != frozen["files"].get(k)]
        raise SystemExit(f"code changed since the freeze: {sorted(changed)}")
    return cur


if __name__ == "__main__":
    d, per = digest()
    FREEZE.parent.mkdir(parents=True, exist_ok=True)
    FREEZE.write_text(json.dumps({"sha256": d, "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                  "n_files": len(per), "files": per}, indent=1))
    print("frozen", d, len(per), "files")
    sys.exit(0)
