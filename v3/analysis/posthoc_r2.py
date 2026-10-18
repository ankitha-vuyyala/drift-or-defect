"""Post-hoc analysis of round-2 DoD decisions (not pre-registered; round-2 data are development data from round 3
on). For every component DoD blamed although it was not an effective defect, keep only the boundary flags raised at
the latest published change in the case's period range that touches the flagged column's raw source columns
(Proposition 8: earlier layouts are superseded; column sources from the domain's COLUMN_SOURCES) and recompute the
false-blame rate. Components blamed by the effect test are kept.

usage: python v3/analysis/posthoc_r2.py runs/v2main   -> runs/v2main/posthoc_r2.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DOD_PROJECT_ROOT", str(ROOT))
sys.path.insert(0, str(ROOT / "v3" / "code"))
from dod.domains import get_domain  # noqa: E402


def latest_for(events: list, cols: list | None) -> str | None:
    evs = [e for e in events if cols is None or set(cols) & set(e.get("columns", []))]
    return max((str(e["period"]) for e in evs), default=None)


def main(run: Path) -> None:
    res = {}
    for d in ("divvy", "hmda", "bts"):
        srcmap = getattr(get_domain(d), "COLUMN_SOURCES", {})
        n = fb = fb_latest = 0
        n_ev = fb_ev = fb_latest_ev = 0
        for line in (run / f"{d}.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            dd = r["methods"]["dod"]
            notes = dd.get("notes") or {}
            fix, eff = set(dd["fix"]), set(r["gt"]["defective"])
            evs = [e["period"] for e in r["obs"].get("source_events") or []]
            latest = max(evs) if evs else None
            wrong = fix - eff
            kept = set()
            for c in wrong:
                if c in (notes.get("harmful") or []):
                    kept.add(c)
                    continue
                flags = (notes.get("boundary") or {}).get(c) or []
                def current(f):
                    col = f.get("column")
                    if col is None:
                        return f.get("event") == latest
                    lt = latest_for(r["obs"]["source_events"], srcmap.get(c, {}).get(col, [col]))
                    return lt is None or f.get("event") == lt
                if not flags or any(current(f) for f in flags):
                    kept.add(c)
            n += 1
            fb += bool(wrong)
            fb_latest += bool(kept)
            if evs:
                n_ev += 1
                fb_ev += bool(wrong)
                fb_latest_ev += bool(kept)
        res[d] = {"n": n, "false_blame": fb / n, "false_blame_latest_only": fb_latest / n,
                  "n_spanning": n_ev, "false_blame_spanning": fb_ev / n_ev if n_ev else None,
                  "false_blame_latest_only_spanning": fb_latest_ev / n_ev if n_ev else None}
    out = run / "posthoc_r2.json"
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
