"""US fatal-crash pipeline (round-3 held-out domain): NHTSA Fatality Analysis Reporting System (FARS) crash
('accident') records, years 2010-2024, every record.

Task: did the fatal crash involve two or more vehicles? (Features known about the place and time of the crash.)

Real, dated changes in the published crash file (found from data/bronze/fars/_profile.json):
  2011  person-count fields added (PVH_INVL, PERMVIT, PERNOTMVIT)
  2015  road function class ROAD_FNC (rural/urban x class, one code) replaced by RUR_URB and FUNC_SYS (new code
        list); text label columns (...NAME) added next to most coded fields
  2016  county and city name columns added
  2020  WEATHER1 and WEATHER2 (and contributing factors CF1-CF3) removed; only WEATHER remains
  2021  the first column header is published with a UTF-8 byte-order mark ("\\ufeffSTATE", read as "ï»¿STATE")
  2023  the byte-order mark is gone again; the ROUTE (route signing) code list is revised (0 not signed, 10-13
        marker types, 95 other, 96 not in state inventory, 99 unknown; the frontage-road code and the old 'other' and
        'unknown' codes are retired)
  (also code-list additions without a change of meaning: REL_ROAD code 12 in 2018, TYP_INT code 11 in 2020)
The 2020 pandemic changed crash patterns in the same year as the weather fields were removed.
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
BRONZE = ROOT / "data" / "bronze" / "fars"
ART = ROOT / "data" / "artifacts" / "fars"

PERIODS = sorted(p.stem for p in BRONZE.glob("[0-9]*.parquet")) if BRONZE.exists() else []
CAT_FEATURES = ["state", "rural", "func", "light", "weather", "typ_int", "rel_road", "route"]
NUM_FEATURES = ["hour", "day_week", "month", "night", "weekend", "work_zone", "nhs"]
FEATURES = NUM_FEATURES + CAT_FEATURES
LABEL = "y"
ID_COLS = ["crash_id"]
TASK = "binary"
BOM_STATE = "ï»¿STATE"

C = {}


def comp(name, inputs, doc=""):
    C[name] = Component(name, inputs, doc=doc)
    return C[name]


def _code(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def _col(r: pd.DataFrame, name: str) -> pd.Series:
    """Original helper: a missing column reads as blank (no exception)."""
    return r[name] if name in r.columns else pd.Series("", index=r.index)


OLD_FUNC = {"1": "interstate", "11": "interstate", "2": "arterial", "3": "arterial", "12": "arterial",
            "13": "arterial", "14": "arterial", "4": "collector", "5": "collector", "15": "collector",
            "6": "local", "16": "local"}
NEW_FUNC = {"1": "interstate", "2": "arterial", "3": "arterial", "4": "arterial", "5": "collector",
            "6": "collector", "7": "local"}

# 2023 route-signing codes -> the earlier code list (same meaning where one exists; no counterpart -> 8 'Other')
ROUTE_2023 = {"0": "8", "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "10": "8", "11": "8", "12": "8",
              "13": "8", "95": "8", "96": "8", "99": "9"}

crash_adapter = comp("crash_adapter", ["raw:accident"], "published crash fields -> canonical schema")


@crash_adapter.variant("v2010")
def _ca(inp, p, a):
    r = inp["raw:accident"]
    if p.get("strip_bom", False):
        r = r.rename(columns={BOM_STATE: "STATE"})
    out = pd.DataFrame({"crash_id": r["_row"].astype("int64")})
    out["state"] = _code(_col(r, "STATE"))
    out["hour"] = pd.to_numeric(_code(r["HOUR"]), errors="coerce")
    out["day_week"] = pd.to_numeric(_code(r["DAY_WEEK"]), errors="coerce")
    out["month"] = pd.to_numeric(_code(r["MONTH"]), errors="coerce")
    layout = p.get("func_layout", "road_fnc")
    if layout == "func_sys":           # 2015 layout: separate rural/urban flag and functional system
        ru = _code(_col(r, "RUR_URB"))
        out["rural"] = ru.map({"1": "rural", "2": "urban"}).fillna("unknown")
        fs = _code(_col(r, "FUNC_SYS"))
        table = OLD_FUNC if p.get("func_alias", False) else NEW_FUNC
        out["func"] = fs.map(table).fillna("unknown")
    else:                              # original layout: one rural/urban x class code
        rf = _code(_col(r, "ROAD_FNC"))
        num = pd.to_numeric(rf, errors="coerce")
        out["rural"] = np.where(num.between(1, 9), "rural", np.where(num.between(11, 19), "urban", "unknown"))
        out["func"] = rf.map(OLD_FUNC).fillna("unknown")
    wcol = p.get("weather_col", "WEATHER1")
    out["weather"] = _code(_col(r, wcol)).replace({"": "unknown"})
    out["light"] = _code(r["LGT_COND"])
    out["typ_int"] = _code(r["TYP_INT"])
    out["rel_road"] = _code(r["REL_ROAD"])
    out["route"] = _code(r["ROUTE"])
    if p.get("route_xwalk", False):    # 2023 code list -> earlier code list
        out["route"] = out["route"].map(ROUTE_2023).fillna(out["route"])
    out["work_zone"] = (pd.to_numeric(_code(r["WRK_ZONE"]), errors="coerce") > 0).astype("float64")
    out["nhs"] = pd.to_numeric(_code(r["NHS"]), errors="coerce")
    out["vehicles"] = pd.to_numeric(_code(r["VE_TOTAL"]), errors="coerce")
    return out


clean = comp("clean", ["crash_adapter"], "unknown codes, label")


@clean.variant("v2010")
def _cl(inp, p, a):
    df = inp["crash_adapter"].copy()
    # pandas-1.x idiom: hour 99 (unknown) -> missing (chained assignment; a no-op under copy-on-write)
    df["hour"][df["hour"] > 23] = np.nan
    df["nhs"][df["nhs"] > 1] = np.nan
    df["y"] = (df["vehicles"] >= 2).astype("int8")
    return df.drop(columns=["vehicles"]).reset_index(drop=True)


@clean.variant("v2024_loc")
def _cl_loc(inp, p, a):
    df = inp["crash_adapter"].copy()
    df.loc[df["hour"] > 23, "hour"] = np.nan
    df.loc[df["nhs"] > 1, "nhs"] = np.nan
    df["y"] = (df["vehicles"] >= 2).astype("int8")
    return df.drop(columns=["vehicles"]).reset_index(drop=True)


features = comp("features", ["clean"], "night and weekend indicators")


@features.variant("v2010")
def _ft(inp, p, a):
    df = inp["clean"].copy()
    h = df["hour"]
    df["night"] = ((h >= 20) | (h < 6)).astype("float64").where(h.notna())
    wk = df["day_week"]
    if p.get("weekend_off_by_one", False):     # incident class: 0-based weekday assumed (FARS: 1 = Sunday)
        df["weekend"] = wk.isin([5, 6]).astype("float64")
    else:
        df["weekend"] = wk.isin([1, 7]).astype("float64")
    return df


encode = comp("encode", ["features"], "model matrix with categorical codes from the encoder artifact")


def fit_encoder(df: pd.DataFrame) -> dict:
    return {c: {k: i for i, k in enumerate(dict.fromkeys(df[c].astype(str).tolist()))} for c in CAT_FEATURES}


@encode.variant("v2010")
def _enc(inp, p, a):
    df = inp["features"]
    out = df[ID_COLS + NUM_FEATURES].copy()
    maps = fit_encoder(df) if p.get("refit", False) else a["encoder"]
    for c in CAT_FEATURES:
        keys = df[c].astype(str)
        if p.get("zero_pad_state", False) and c == "state":    # incident class: key format differs from artifact
            keys = keys.str.zfill(2)
        codes = keys.map(maps[c])
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


PIPELINE = Pipeline(domain="fars", components=C, output="encode", raw_tables=["accident"],
                    load_raw=load_raw, load_artifact=load_artifact)
V = Version.make


def _adapter_params(period: str) -> dict:
    p = {}
    if period >= "2015":
        p["func_layout"] = "func_sys"
    if period >= "2020":
        p["weather_col"] = "WEATHER"
    if "2021" <= period < "2023":
        p["strip_bom"] = True
    if period >= "2023":
        p["route_xwalk"] = True
    return p


def reference_state(encoder_id: str, p0: str = "2011") -> dict:
    return {
        "crash_adapter": V("v2010", _adapter_params(p0)),
        "clean": V("v2010", env="p15"),          # deployed in a pandas-1.5 environment
        "features": V("v2010"),
        "encode": V("v2010", artifacts={"encoder": encoder_id}),
    }


def spec_state(period: str, encoder_id: str) -> dict:
    s = reference_state(encoder_id, period)
    return s


EVENTS = [
    ("2011", "person-count fields added", ["PVH_INVL", "PERMVIT", "PERNOTMVIT"]),
    ("2015", "ROAD_FNC replaced by RUR_URB and FUNC_SYS (new code list); label columns added",
     ["ROAD_FNC", "RUR_URB", "FUNC_SYS"]),
    ("2016", "county and city name columns added", ["COUNTYNAME", "CITYNAME"]),
    ("2018", "REL_ROAD code 12 (pedestrian refuge or traffic island) added", ["REL_ROAD"]),
    ("2020", "WEATHER1, WEATHER2 and CF1-CF3 removed", ["WEATHER1", "WEATHER2", "CF1", "CF2", "CF3"]),
    ("2020", "TYP_INT code 11 (other intersection type) added", ["TYP_INT"]),
    ("2021", "first header published with a byte-order mark (STATE)", ["STATE", BOM_STATE]),
    ("2023", "byte-order mark removed", ["STATE", BOM_STATE]),
    ("2023", "ROUTE (route signing) code list revised: new codes 0, 10-13, 95, 96, 99; frontage-road, 'other' and "
             "'unknown' codes retired", ["ROUTE"]),
]


def source_events(period_from: str, period_to: str) -> list[dict]:
    return [{"period": w, "table": "accident", "change": what, "columns": cols}
            for w, what, cols in EVENTS if period_from < w <= period_to]


LINEAGE = {
    "hour": ["crash_adapter", "clean"], "day_week": ["crash_adapter"], "month": ["crash_adapter"],
    "night": ["crash_adapter", "clean", "features"], "weekend": ["crash_adapter", "features"],
    "work_zone": ["crash_adapter"], "nhs": ["crash_adapter", "clean"],
    **{c: ["crash_adapter", "encode"] for c in CAT_FEATURES},
    "y": ["crash_adapter", "clean"],
}
SOURCE_READERS = {"accident": ["crash_adapter"]}
_ALL = ["STATE", BOM_STATE, "HOUR", "DAY_WEEK", "MONTH", "ROAD_FNC", "RUR_URB", "FUNC_SYS", "WEATHER1", "WEATHER",
        "LGT_COND", "TYP_INT", "REL_ROAD", "ROUTE", "WRK_ZONE", "NHS", "VE_TOTAL"]
RAW_COLUMNS = {
    "crash_adapter": {"accident": _ALL},
    "clean": {"accident": ["HOUR", "NHS", "VE_TOTAL"]},
    "features": {"accident": ["HOUR", "DAY_WEEK"]},
    "encode": {"accident": _ALL},
}
COLUMN_SOURCES = {
    "crash_adapter": {"state": ["STATE", BOM_STATE], "hour": ["HOUR"], "day_week": ["DAY_WEEK"], "month": ["MONTH"],
                      "rural": ["ROAD_FNC", "RUR_URB"], "func": ["ROAD_FNC", "FUNC_SYS"],
                      "weather": ["WEATHER1", "WEATHER"], "light": ["LGT_COND"], "typ_int": ["TYP_INT"],
                      "rel_road": ["REL_ROAD"], "route": ["ROUTE"], "work_zone": ["WRK_ZONE"], "nhs": ["NHS"],
                      "vehicles": ["VE_TOTAL"], "crash_id": ["_row"]},
    "clean": {"y": ["vehicles"], "hour": ["hour"], "nhs": ["nhs"]},
    "features": {"night": ["hour"], "weekend": ["day_week"]},
}


def catalog(period: str, encoder_id: str) -> list[dict]:
    sp = spec_state(period, encoder_id)
    ca = sp["crash_adapter"].p()
    out = []

    def add(cid, comp_, version, kind, tier, silent_hint, note, source=""):
        out.append({"id": cid, "component": comp_, "version": version, "kind": kind, "tier": tier,
                    "silent_hint": silent_hint, "note": note, "source": source})
    if period >= "2015":
        add("fars.func_layout_stale", "crash_adapter", V("v2010", {k: v for k, v in ca.items() if k != "func_layout"}),
            "defect", "T1", True, "rural/urban and road class still read from the removed ROAD_FNC field")
        add("fars.func_alias", "crash_adapter", V("v2010", {**ca, "func_alias": True}), "defect", "T1", True,
            "FUNC_SYS codes mapped with the old ROAD_FNC table (rename without recode)",
            "folktables issue #22 (rename without recode)")
    if period >= "2020":
        add("fars.weather_stale", "crash_adapter", V("v2010", {k: v for k, v in ca.items() if k != "weather_col"}),
            "defect", "T1", True, "weather still read from the removed WEATHER1 field")
    if "2021" <= period < "2023":
        add("fars.bom_stale", "crash_adapter", V("v2010", {k: v for k, v in ca.items() if k != "strip_bom"}),
            "defect", "T1", True, "state read from 'STATE' while the header carries a byte-order mark")
    if period >= "2023":
        add("fars.route_codes_stale", "crash_adapter", V("v2010", {k: v for k, v in ca.items() if k != "route_xwalk"}),
            "defect", "T1", True, "route-signing codes read with the pre-2023 code list (no crosswalk)")
    add("fars.adapter_env_p30", "crash_adapter", V("v2010", ca, env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the adapter")
    add("fars.clean_env_main", "clean", V("v2010"), "benign", "T2b", True, "pandas 2.2 upgrade of the cleaning step")
    add("fars.clean_env_p30", "clean", V("v2010", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: chained-assignment unknown-code handling becomes a no-op",
        "pandas 3.0 release notes (copy-on-write)")
    add("fars.clean_modernised", "clean", V("v2024_loc"), "benign", "B", True, "chained assignment -> .loc")
    add("fars.weekend_off_by_one", "features", V("v2010", {"weekend_off_by_one": True}), "defect", "T3", True,
        "weekend from a 0-based weekday convention (FARS uses 1 = Sunday)")
    add("fars.features_env_p30", "features", V("v2010", env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the feature step")
    add("fars.encoder_refit", "encode", V("v2010", {"refit": True}, sp["encode"].a()), "defect", "T3", True,
        "categorical codes re-fitted at serving time (training/serving skew)")
    add("fars.zero_pad_state", "encode", V("v2010", {"zero_pad_state": True}, sp["encode"].a()), "defect", "T3", True,
        "state key zero-padded while the encoder artifact holds unpadded codes")
    add("fars.unknown_as_reference", "encode", V("v2010", {"unknown_as_reference": True}, sp["encode"].a()),
        "defect", "T3r", True, "unseen categories encoded as the reference category", "scikit-learn issue #34549")
    return out
