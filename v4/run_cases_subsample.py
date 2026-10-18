"""Run the frozen round-4 case runner (v4/code/run_cases.py, unchanged) on a fixed 1-in-3 subsample of the storm
cases. The subsample is defined before any further storm results were seen: a case is kept iff
int(sha256("v4-storm-subsample:" + case_id), 16) % 3 == 0. Chicago cases are not affected.

This file is not part of the frozen code; it only filters the list of cases the runner is given (a disclosed
deviation from v4/PROTOCOL_V4.md, made for compute reasons; see v4/EXECUTION_NOTES_V4.md).

usage: python v4/run_cases_subsample.py <run_cases.py arguments>
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "code"))
import run_cases  # noqa: E402  (frozen)
from dod import cases  # noqa: E402

_generate = cases.generate


def keep(case_id: str) -> bool:
    return int(hashlib.sha256(f"v4-storm-subsample:{case_id}".encode()).hexdigest(), 16) % 3 == 0


def generate(domain: str, seed: int = 7):
    out = _generate(domain, seed)
    return [(s, c) for s, c in out if domain != "storm" or keep(c.case_id)]


cases.generate = generate

if __name__ == "__main__":
    run_cases.main()
