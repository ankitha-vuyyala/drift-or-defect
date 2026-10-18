"""Bronze layer for the round-4 domains: published records of each period kept as published text (no parsing),
one parquet file per table and period, plus per-period profiles (column names, value shapes, and the value counts of
every column with at most 40 distinct values). The profiles are how dated source changes are found.

  storm   : NOAA Storm Events; years 1996-2025; tables details, fatalities, locations; every record.
  chicago : Chicago Traffic Crashes; years 2016-2025; a seeded sample of 60,000 crashes per year (all crashes when
            fewer) and every person and vehicle record of the sampled crashes.

usage: python v4/data/build_bronze_v4.py storm|chicago
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw_v4"
BRONZE = ROOT / "data" / "bronze"
SEED = 20261007
N_CHI = 60_000


def shape(v: str) -> str:
    s = re.sub(r"[0-9]+", "9", str(v))
    return re.sub(r"[A-Za-z]+", "a", s)[:40]


def profile(df: pd.DataFrame) -> dict:
    out = {"columns": list(df.columns), "rows": int(len(df)), "shapes": {}, "codes": {}}
    for c in df.columns:
        vc = df[c].map(shape).value_counts(normalize=True).head(4)
        out["shapes"][c] = {k: round(float(v), 4) for k, v in vc.items()}
        codes = df[c].value_counts()
        if len(codes) <= 40:
            out["codes"][c] = {str(k): int(v) for k, v in codes.items()}
    return out


def read_str(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False, encoding="latin-1",
                       low_memory=False)


def storm() -> None:
    prof = {}
    for tab in ("details", "fatalities", "locations"):
        (BRONZE / "storm" / tab).mkdir(parents=True, exist_ok=True)
        for y in range(1996, 2026):
            src = RAW / "storm" / f"{tab}_{y}.csv.gz"
            if not src.exists():
                print("missing", src, flush=True)
                continue
            with gzip.open(src, "rb") as f:
                df = read_str(f)
            df.to_parquet(BRONZE / "storm" / tab / f"{y}.parquet", index=False)
            prof.setdefault(tab, {})[str(y)] = profile(df)
            print("storm", tab, y, len(df), flush=True)
    (BRONZE / "storm" / "_profile.json").write_text(json.dumps(prof, indent=1), encoding="utf-8")


def chicago() -> None:
    prof = {}
    for tab in ("crashes", "people", "vehicles"):
        (BRONZE / "chicago" / tab).mkdir(parents=True, exist_ok=True)
    for y in range(2016, 2026):
        cr = read_str(RAW / "chicago" / f"crashes_{y}.csv")
        key = int(hashlib.sha256(f"chicago-{y}".encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng([SEED, key])
        if len(cr) > N_CHI:
            cr = cr.iloc[np.sort(rng.choice(len(cr), N_CHI, replace=False))].reset_index(drop=True)
        ids = set(cr["crash_record_id"])
        cr.to_parquet(BRONZE / "chicago" / "crashes" / f"{y}.parquet", index=False)
        prof.setdefault("crashes", {})[str(y)] = profile(cr)
        for tab in ("people", "vehicles"):
            df = read_str(RAW / "chicago" / f"{tab}_{y}.csv")
            df = df[df["crash_record_id"].isin(ids)].reset_index(drop=True)
            df.to_parquet(BRONZE / "chicago" / tab / f"{y}.parquet", index=False)
            prof.setdefault(tab, {})[str(y)] = profile(df)
        print("chicago", y, len(cr), flush=True)
    (BRONZE / "chicago" / "_profile.json").write_text(json.dumps(prof, indent=1), encoding="utf-8")


if __name__ == "__main__":
    for d in sys.argv[1:]:
        {"storm": storm, "chicago": chicago}[d]()
