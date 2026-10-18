"""Bronze layer for the round-3 domains (derived from v2/data/build_bronze_v2.py): a seeded random sample of the *published* records of each period, every column
kept as the published text (no parsing), plus a per-period profile of the published schema (column names, value
shapes). The profile is how dated source changes are found; the pipelines, not this script, parse the values.

  cabi    : Capital Bikeshare; calendar quarters 2014-Q1 .. 2026-Q3; 100,000 trips per quarter (archive files are
            split by the trip's start month, parsed here for partitioning only).
  fars    : NHTSA FARS crash ('accident') file; years 2010-2024; every record.
  landreg : HM Land Registry Price Paid Data; years 2008-2025; 150,000 transactions per year. The files have no
            header row; columns are kept by position (c0 .. c15).

usage: python v3/data/build_bronze_v3.py [cabi|fars|landreg ...]
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw_v3"
BRONZE = ROOT / "data" / "bronze"
SEED = 20261005
N = {"cabi": 100_000, "fars": 10 ** 9, "landreg": 150_000}
STATES_FIPS = {"08": "CO", "41": "OR", "47": "TN"}
BTS_COLS = ["Year", "Quarter", "Month", "DayofMonth", "DayOfWeek", "FlightDate", "Reporting_Airline",
            "DOT_ID_Reporting_Airline", "IATA_CODE_Reporting_Airline", "Tail_Number",
            "Flight_Number_Reporting_Airline", "OriginAirportID", "Origin", "OriginCityName", "OriginState",
            "DestAirportID", "Dest", "DestCityName", "DestState", "CRSDepTime", "DepTime", "DepDelay",
            "DepDelayMinutes", "DepDel15", "DepTimeBlk", "TaxiOut", "WheelsOff", "WheelsOn", "TaxiIn", "CRSArrTime",
            "ArrTime", "ArrDelay", "ArrDelayMinutes", "ArrDel15", "ArrTimeBlk", "Cancelled", "CancellationCode",
            "Diverted", "CRSElapsedTime", "ActualElapsedTime", "AirTime", "Flights", "Distance", "DistanceGroup",
            "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay", "LateAircraftDelay"]


def shape(v: str) -> str:
    """Value shape: digits -> 9, letters -> a (runs collapsed), punctuation kept."""
    s = re.sub(r"[0-9]+", "9", str(v))
    return re.sub(r"[A-Za-z]+", "a", s)[:40]


def profile(df: pd.DataFrame) -> dict:
    out = {"columns": list(df.columns), "rows": int(len(df)), "shapes": {}}
    for c in df.columns:
        vc = df[c].map(shape).value_counts(normalize=True).head(4)
        out["shapes"][c] = {k: round(float(v), 4) for k, v in vc.items()}
    return out


def read_csv_str(f, usecols=None, chunks=False):
    kw = dict(dtype=str, keep_default_na=False, na_filter=False, encoding="latin-1", low_memory=False)
    if usecols is not None:
        kw["usecols"] = lambda c: c in usecols
    if chunks:
        return pd.read_csv(f, chunksize=250_000, **kw)
    return pd.read_csv(f, **kw)


def stable_seed(key: str) -> int:
    import hashlib
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


class Reservoir:
    """Uniform sample of n rows from a stream of chunks (bounded memory): every row gets a seeded uniform key and
    the n smallest keys are kept. Rows keep their order of arrival."""

    def __init__(self, n: int, key: str):
        self.n, self.rng, self.df, self.seen, self.src = n, np.random.default_rng([SEED, stable_seed(key)]), None, 0, []

    def add(self, ch: pd.DataFrame, src: str | None = None) -> None:
        if len(ch) == 0:
            return
        ch = ch.copy()
        ch["_k"] = self.rng.random(len(ch))
        ch["_o"] = np.arange(self.seen, self.seen + len(ch))
        self.seen += len(ch)
        if src and src not in self.src:
            self.src.append(src)
        df = ch if self.df is None else pd.concat([self.df, ch], ignore_index=True)
        if len(df) > self.n:
            df = df.nsmallest(self.n, "_k")
        self.df = df

    def result(self) -> pd.DataFrame:
        if self.df is None:
            return pd.DataFrame()
        return self.df.sort_values("_o").drop(columns=["_k", "_o"]).fillna("").reset_index(drop=True)


def save(dom: str, period: str, df: pd.DataFrame, profiles: dict, src: list[str]) -> None:
    d = BRONZE / dom
    d.mkdir(parents=True, exist_ok=True)
    df.to_parquet(d / f"{period}.parquet", index=False)
    profiles[period] = {**profile(df), "source_files": src}
    print(dom, period, len(df), "rows from", src, flush=True)


# ----------------------------------------------------------------------------------------------- cabi
def _start(df: pd.DataFrame) -> pd.Series:
    col = next(c for c in df.columns if c.strip().lower() in ("start date", "starttime", "start_time", "started_at"))
    return pd.to_datetime(df[col], format="mixed", errors="coerce")


def cabi() -> None:
    files = sorted((RAW / "cabi").glob("*.zip"))
    res: dict[str, Reservoir] = {}
    for f in files:
        z = zipfile.ZipFile(f)
        for n in z.namelist():
            base = n.rsplit("/", 1)[-1]
            if n.startswith("__MACOSX") or not base.lower().endswith(".csv"):
                continue
            with z.open(n) as fh:
                for ch in read_csv_str(io.TextIOWrapper(fh, encoding="latin-1"), chunks=True):
                    st = _start(ch)
                    q = (st.dt.year.astype("Int64").astype(str) + "-Q"
                         + ((st.dt.month - 1) // 3 + 1).astype("Int64").astype(str))
                    for qq, part in ch.groupby(q.values):
                        if qq.startswith("<NA>") or not ("2014-Q1" <= qq <= "2026-Q3"):
                            continue
                        res.setdefault(qq, Reservoir(N["cabi"], f"cabi{qq}")).add(part, f"{f.name}:{base}")
            print("read", f.name, base, flush=True)
    profiles = {}
    for q in sorted(res):
        save("cabi", q, res[q].result(), profiles, res[q].src)
    (BRONZE / "cabi" / "_profile.json").write_text(json.dumps(profiles, indent=1))


# ----------------------------------------------------------------------------------------------- fars
def fars() -> None:
    profiles = {}
    for f in sorted((RAW / "fars").glob("FARS*NationalCSV.zip")):
        y = f.name[4:8]
        z = zipfile.ZipFile(f)
        n = next(x for x in z.namelist() if x.rsplit("/", 1)[-1].lower() == "accident.csv")
        with z.open(n) as fh:
            df = read_csv_str(io.TextIOWrapper(fh, encoding="latin-1"))
        save("fars", y, df.fillna(""), profiles, [f"{f.name}:{n}"])
    (BRONZE / "fars" / "_profile.json").write_text(json.dumps(profiles, indent=1))


# ----------------------------------------------------------------------------------------------- landreg
def landreg() -> None:
    profiles = {}
    for f in sorted((RAW / "landreg").glob("pp-*.csv")):
        y = f.stem[3:]
        r = Reservoir(N["landreg"], f"landreg{y}")
        for ch in pd.read_csv(f, header=None, dtype=str, keep_default_na=False, na_filter=False, encoding="latin-1",
                              chunksize=250_000):
            ch.columns = [f"c{i}" for i in range(ch.shape[1])]
            r.add(ch, f.name)
        save("landreg", y, r.result(), profiles, r.src)
    (BRONZE / "landreg" / "_profile.json").write_text(json.dumps(profiles, indent=1))


if __name__ == "__main__":
    which = sys.argv[1:] or ["cabi", "fars", "landreg"]
    for w in which:
        {"cabi": cabi, "fars": fars, "landreg": landreg}[w]()
