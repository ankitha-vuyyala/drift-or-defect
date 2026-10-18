"""Build the "bronze" layer: raw records exactly as published, sampled to laptop size, one file per period.

No harmonisation happens here: column names, codes and dtypes stay as the provider published them in that
period, so the benchmark pipelines must cope with the real source changes themselves.

  ACS   data/bronze/acs/{year}_person.parquet, {year}_housing.parquet   (households sampled by hashed SERIALNO;
        all columns kept as strings, as in the CSV)
  TLC   data/bronze/tlc/{yyyy-mm}.parquet   (uniform row sample per month; published Arrow schema kept)
  News  data/bronze/news/{year}.parquet     (all records of that year; raw fields)

usage: python code/data/build_bronze.py [--only acs|tlc|news|all] [--acs-frac 0.3] [--tlc-rows 150000]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
RAW, BRONZE = ROOT / "data" / "raw", ROOT / "data" / "bronze"
SEED = 20261005

# Superset of raw columns any adapter version may need (names differ across vintages; absent ones are skipped).
ACS_P = ["SERIALNO", "SPORDER", "PUMA", "ST", "STATE", "ADJINC", "PWGTP", "AGEP", "CIT", "COW", "DIS", "ENG",
         "HISP", "JWMNP", "JWTR", "JWTRNS", "MAR", "MIG", "MIL", "NATIVITY", "OCCP", "POBP", "RAC1P", "RELP",
         "RELSHIPP", "SCHL", "SEX", "WKHP", "WKW", "WKWN", "ESR", "PINCP", "WAGP"]
ACS_H = ["SERIALNO", "ST", "STATE", "ADJINC", "ADJHSG", "TYPE", "TYPEHUGQ", "NP", "TEN", "VEH", "BDSP", "RMSP",
         "HINCP", "FINCP", "HHL", "HHLANP", "NOC", "WIF", "FES", "WGTP"]


def keep(serial: str, frac: float) -> bool:
    h = hashlib.blake2b(f"{SEED}:{serial}".encode(), digest_size=8).digest()
    return int.from_bytes(h, "little") / 2 ** 64 < frac


def read_zip_csv(path: Path, wanted: list[str]) -> pd.DataFrame:
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        with z.open(name) as fh:
            header = io.TextIOWrapper(fh, encoding="latin-1").readline().strip().split(",")
        cols = [c for c in header if c in wanted]
        parts = []
        with z.open(name) as fh:
            for chunk in pd.read_csv(fh, usecols=cols, dtype=str, keep_default_na=False, chunksize=200_000,
                                     encoding="latin-1"):
                parts.append(chunk)
    return pd.concat(parts, ignore_index=True)[cols]


def acs(frac: float) -> dict:
    out = {}
    (BRONZE / "acs").mkdir(parents=True, exist_ok=True)
    for ydir in sorted((RAW / "acs").iterdir()):
        y = ydir.name
        for kind, wanted, tag in (("p", ACS_P, "person"), ("h", ACS_H, "housing")):
            dest = BRONZE / "acs" / f"{y}_{tag}.parquet"
            frames = []
            for z in sorted(ydir.glob(f"csv_{kind}*.zip")):
                df = read_zip_csv(z, wanted)
                df = df[df["SERIALNO"].map(lambda s: keep(s, frac))]
                df.insert(0, "_source_file", z.name)
                frames.append(df)
            if not frames:
                continue
            df = pd.concat(frames, ignore_index=True)
            df.to_parquet(dest, index=False)
            out[f"acs/{y}_{tag}"] = {"rows": len(df), "columns": [c for c in df.columns]}
            print(f"acs {y} {tag}: {len(df)} rows, {len(df.columns)} cols", flush=True)
    return out


def tlc(n_rows: int) -> dict:
    out = {}
    (BRONZE / "tlc").mkdir(parents=True, exist_ok=True)
    for f in sorted((RAW / "tlc" / "yellow").glob("yellow_tripdata_*.parquet")):
        ym = f.stem.split("_")[-1]
        dest = BRONZE / "tlc" / f"{ym}.parquet"
        pf = pq.ParquetFile(f)
        frac = min(1.0, n_rows / max(1, pf.metadata.num_rows))
        rng = np.random.default_rng(SEED + int(ym.replace("-", "")))
        parts = []
        for i in range(pf.num_row_groups):
            t = pf.read_row_group(i)
            take = np.nonzero(rng.random(t.num_rows) < frac)[0]
            parts.append(t.take(pa.array(take)))
        t = pa.concat_tables(parts)
        pq.write_table(t, dest)
        out[f"tlc/{ym}"] = {"rows": t.num_rows, "source_rows": pf.metadata.num_rows,
                            "schema": {fld.name: str(fld.type) for fld in t.schema}}
        print(f"tlc {ym}: {t.num_rows} of {pf.metadata.num_rows}", flush=True)
    return out


def news() -> dict:
    out = {}
    (BRONZE / "news").mkdir(parents=True, exist_ok=True)
    d = pd.read_json(RAW / "news" / "data.json", lines=True, dtype=False)
    d["date"] = d["date"].astype(str)
    years = d["date"].str[:4]
    for y, g in d.groupby(years):
        g.reset_index(drop=True).to_parquet(BRONZE / "news" / f"{y}.parquet", index=False)
        out[f"news/{y}"] = {"rows": len(g)}
        print(f"news {y}: {len(g)}", flush=True)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all", choices=["acs", "tlc", "news", "all"])
    ap.add_argument("--acs-frac", type=float, default=0.3)
    ap.add_argument("--tlc-rows", type=int, default=150_000)
    a = ap.parse_args()
    manifest_path = BRONZE / "BRONZE_MANIFEST.json"
    man = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if a.only in ("news", "all"):
        man.update(news())
    if a.only in ("tlc", "all"):
        man.update(tlc(a.tlc_rows))
    if a.only in ("acs", "all"):
        man.update(acs(a.acs_frac))
    man["_params"] = {"seed": SEED, "acs_frac": a.acs_frac, "tlc_rows": a.tlc_rows}
    BRONZE.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(man, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
