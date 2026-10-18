"""Code-list profile of the round-3 bronze data (no method is run): for every period and every published column
with at most 40 distinct values, the value counts. Used to find dated code-list changes.
usage: python v3/data/codes_v3.py cabi fars landreg   -> runs/v3_checks/codes_<domain>.json"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main(d: str) -> None:
    out = {}
    for p in sorted((ROOT / "data" / "bronze" / d).glob("[0-9]*.parquet")):
        df = pd.read_parquet(p)
        cols = {}
        for c in df.columns:
            vc = df[c].astype(str).value_counts()
            if len(vc) <= 40:
                cols[c] = {str(k): int(v) for k, v in vc.items()}
        out[p.stem] = cols
        print(d, p.stem, flush=True)
    dst = ROOT / "runs" / "v3_checks" / f"codes_{d}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        main(d)
