"""England and Wales house-sales pipeline (round-3 held-out domain): HM Land Registry Price Paid Data, years
2008-2025 (150,000 transactions per year).

Task: is the sale a newly built property? (From price, date, property type, tenure and location.)

The files are republished in one 16-column layout (no header) for every year, so there is no layout change. The
dated published change is one of coverage: from October 2013 the register publishes "category B" transactions
(repossessions, buy-to-let and other non-standard sales; property type "O") next to standard "category A" sales;
their share grows from 0.1% (2012) to 2.4% (2013), 6.6% (2014) and about 16% from 2020 (data/bronze/landreg). A
correct pipeline restricts itself to category A from 2013 on to keep the population comparable. Real-world changes
include the 2016 stamp-duty surcharge, the 2020-21 stamp-duty holiday and the 2022-23 interest-rate rise.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from dod.core import Component, Pipeline, Version

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[4]))
BRONZE = ROOT / "data" / "bronze" / "landreg"
ART = ROOT / "data" / "artifacts" / "landreg"

PERIODS = sorted(p.stem for p in BRONZE.glob("[0-9]*.parquet")) if BRONZE.exists() else []
CAT_FEATURES = ["ptype", "tenure", "county", "area"]
NUM_FEATURES = ["log_price", "month", "dow", "day_of_year"]
FEATURES = NUM_FEATURES + CAT_FEATURES
LABEL = "y"
ID_COLS = ["sale_id"]
TASK = "binary"

C = {}


def comp(name, inputs, doc=""):
    C[name] = Component(name, inputs, doc=doc)
    return C[name]


sale_adapter = comp("sale_adapter", ["raw:pp"], "published price-paid columns (by position) -> canonical schema")


@sale_adapter.variant("v2008")
def _sa(inp, p, a):
    r = inp["raw:pp"]
    return pd.DataFrame({
        "sale_id": r["_row"].astype("int64"),
        "price": pd.to_numeric(r["c1"].str.strip(), errors="coerce"),
        "date": r["c2"].astype(str),
        "postcode": r["c3"].astype(str).str.strip().str.upper(),
        "ptype": r["c4"].astype(str).str.strip(),
        "new": r["c5"].astype(str).str.strip(),
        "tenure": r["c6"].astype(str).str.strip(),
        "county": r["c13"].astype(str).str.strip(),
        "category": r["c14"].astype(str).str.strip(),
    })


time_features = comp("time_features", ["sale_adapter"], "month, day of week, day of year")


@time_features.variant("v2008")
def _tf(inp, p, a):
    df = inp["sale_adapter"].copy()
    d = pd.to_datetime(df["date"], format=p.get("fmt", "%Y-%m-%d %H:%M"), errors="coerce")
    df["month"] = d.dt.month.astype("float64")
    df["dow"] = (d.dt.dayofweek.astype("float64") + (1.0 if p.get("dow_one_based", False) else 0.0))
    # original idiom: day of year from epoch nanoseconds (resolution-dependent across pandas versions)
    jan1 = pd.to_datetime(d.dt.year.astype("Int64").astype(str) + "-01-01", format="%Y-%m-%d", errors="coerce")
    ok = d.notna() & jan1.notna()
    doy = pd.Series(np.nan, index=df.index)
    doy[ok] = ((d[ok].astype("int64") - jan1[ok].astype("int64")) // 86_400_000_000_000).astype("float64")
    df["day_of_year"] = doy
    return df.drop(columns=["date"])


clean = comp("clean", ["time_features"], "scope, log price, label")


@clean.variant("v2008")
def _cl(inp, p, a):
    df = inp["time_features"]
    keep = df["price"] > 0
    if p.get("category_a_only", False):          # from the 2013 coverage change: standard sales only
        keep &= df["category"] == "A"
    df = df[keep].copy()
    df["log_price"] = np.nan
    # pandas-1.x idiom: fill the log price in place (chained assignment; a no-op under copy-on-write)
    df["log_price"][df["price"] > 0] = np.log(df["price"][df["price"] > 0])
    df["y"] = (df["new"] == "Y").astype("int8")
    return df.drop(columns=["new", "price", "category"]).reset_index(drop=True)


@clean.variant("v2024_loc")
def _cl_loc(inp, p, a):
    df = inp["time_features"]
    keep = df["price"] > 0
    if p.get("category_a_only", False):
        keep &= df["category"] == "A"
    df = df[keep].copy()
    df["log_price"] = np.log(df["price"].where(df["price"] > 0))
    df["y"] = (df["new"] == "Y").astype("int8")
    return df.drop(columns=["new", "price", "category"]).reset_index(drop=True)


geo = comp("geo", ["clean"], "postcode area")


@geo.variant("v2008")
def _geo(inp, p, a):
    df = inp["clean"].copy()
    outward = df["postcode"].str.split(" ").str[0].fillna("")
    if p.get("area_is_outward", False):          # incident class: district (outward code) used as the area key
        df["area"] = outward.replace({"": "NA"})
    else:
        df["area"] = outward.str.extract(r"^([A-Z]{1,2})", expand=False).fillna("NA")
    return df.drop(columns=["postcode"])


encode = comp("encode", ["geo"], "model matrix with categorical codes from the encoder artifact")


def fit_encoder(df: pd.DataFrame) -> dict:
    return {c: {k: i for i, k in enumerate(dict.fromkeys(df[c].astype(str).tolist()))} for c in CAT_FEATURES}


@encode.variant("v2008")
def _enc(inp, p, a):
    df = inp["geo"]
    out = df[ID_COLS + NUM_FEATURES].copy()
    maps = fit_encoder(df) if p.get("refit", False) else a["encoder"]
    for c in CAT_FEATURES:
        codes = df[c].astype(str).map(maps[c])
        if p.get("unknown_as_reference", False):    # incident replay (scikit-learn issue #34549)
            codes = codes.fillna(0)
        out[c] = codes.astype("float64")
    out[LABEL] = df[LABEL].values
    return out[ID_COLS + FEATURES + [LABEL]]


# ----------------------------------------------------------------------------------------------- data and artifacts
def load_raw(period: str, table: str) -> pd.DataFrame:
    df = pd.read_parquet(BRONZE / f"{period}.parquet")
    df.insert(0, "_row", np.arange(len(df), dtype="int64"))
    return df


@lru_cache(maxsize=64)
def _load_art(name: str, version: str) -> str:
    return (ART / name / f"{version}.json").read_text(encoding="utf-8")


def load_artifact(name: str, version: str):
    return json.loads(_load_art(name, version))


def save_artifact(name: str, version: str, obj) -> None:
    (ART / name).mkdir(parents=True, exist_ok=True)
    (ART / name / f"{version}.json").write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
    _load_art.cache_clear()


PIPELINE = Pipeline(domain="landreg", components=C, output="encode", raw_tables=["pp"],
                    load_raw=load_raw, load_artifact=load_artifact)
V = Version.make


def reference_state(encoder_id: str, p0: str = "2010") -> dict:
    return {
        "sale_adapter": V("v2008"),
        "time_features": V("v2008", env="p15"),     # deployed in a pandas-1.5 environment
        "clean": V("v2008", {"category_a_only": True} if p0 >= "2013" else {}, env="p15"),
        "geo": V("v2008"),
        "encode": V("v2008", artifacts={"encoder": encoder_id}),
    }


def spec_state(period: str, encoder_id: str) -> dict:
    return reference_state(encoder_id, period)


EVENTS = [
    ("2013", "category B transactions (non-standard sales) and property type 'Other' published", ["c4", "c14"]),
]


def source_events(period_from: str, period_to: str) -> list[dict]:
    return [{"period": w, "table": "pp", "change": what, "columns": cols}
            for w, what, cols in EVENTS if period_from < w <= period_to]


LINEAGE = {
    "log_price": ["sale_adapter", "clean"], "month": ["sale_adapter", "time_features"],
    "dow": ["sale_adapter", "time_features"], "day_of_year": ["sale_adapter", "time_features"],
    "ptype": ["sale_adapter", "encode"], "tenure": ["sale_adapter", "encode"], "county": ["sale_adapter", "encode"],
    "area": ["sale_adapter", "geo", "encode"], "y": ["sale_adapter", "clean"],
}
SOURCE_READERS = {"pp": ["sale_adapter"]}
_ALL = ["c1", "c2", "c3", "c4", "c5", "c6", "c13", "c14"]
RAW_COLUMNS = {
    "sale_adapter": {"pp": _ALL},
    "time_features": {"pp": ["c2"]},
    "clean": {"pp": ["c1", "c5", "c14"]},
    "geo": {"pp": ["c3"]},
    "encode": {"pp": _ALL},
}
COLUMN_SOURCES = {
    "sale_adapter": {"price": ["c1"], "date": ["c2"], "postcode": ["c3"], "ptype": ["c4"], "new": ["c5"],
                     "tenure": ["c6"], "county": ["c13"], "category": ["c14"], "sale_id": ["_row"]},
    "time_features": {"month": ["date"], "dow": ["date"], "day_of_year": ["date"]},
    "clean": {"log_price": ["price"], "y": ["new"]},
    "geo": {"area": ["postcode"]},
}


def catalog(period: str, encoder_id: str) -> list[dict]:
    sp = spec_state(period, encoder_id)
    cl = sp["clean"]
    out = []

    def add(cid, comp_, version, kind, tier, silent_hint, note, source=""):
        out.append({"id": cid, "component": comp_, "version": version, "kind": kind, "tier": tier,
                    "silent_hint": silent_hint, "note": note, "source": source})
    if period >= "2013":
        add("landreg.category_scope_stale", "clean", V("v2008", {}, env="p15"), "defect", "T1", True,
            "category B (non-standard) sales not excluded after the 2013 coverage change")
    add("landreg.adapter_env_p30", "sale_adapter", V("v2008", env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the adapter")
    add("landreg.time_env_main", "time_features", V("v2008"), "benign", "T2b", True,
        "pandas 2.2 upgrade of the time step (string dates still parse to nanoseconds)")
    add("landreg.time_env_p30", "time_features", V("v2008", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: day of year via astype(int64) changes resolution", "pandas issue #65308")
    add("landreg.dow_one_based", "time_features", V("v2008", {"dow_one_based": True}, env="p15"), "defect", "T3",
        True, "day of week shifted to a 1-based convention")
    add("landreg.clean_env_main", "clean", V("v2008", cl.p()), "benign", "T2b", True,
        "pandas 2.2 upgrade of the cleaning step")
    add("landreg.clean_env_p30", "clean", V("v2008", cl.p(), env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: chained-assignment log price becomes a no-op", "pandas 3.0 release notes (copy-on-write)")
    add("landreg.clean_modernised", "clean", V("v2024_loc", cl.p()), "benign", "B", True,
        "chained assignment -> vectorised .where")
    add("landreg.area_is_outward", "geo", V("v2008", {"area_is_outward": True}), "defect", "T3", True,
        "postcode district used where the postcode area is expected")
    add("landreg.geo_env_p30", "geo", V("v2008", env="p30"), "benign", "T2b", True, "pandas 3 upgrade of the geo step")
    add("landreg.encoder_refit", "encode", V("v2008", {"refit": True}, sp["encode"].a()), "defect", "T3", True,
        "categorical codes re-fitted at serving time (training/serving skew)")
    add("landreg.unknown_as_reference", "encode", V("v2008", {"unknown_as_reference": True}, sp["encode"].a()),
        "defect", "T3r", True, "unseen categories encoded as the reference category", "scikit-learn issue #34549")
    return out
