"""Washington DC bike-share pipeline (round-3 held-out domain): Capital Bikeshare trip records, calendar quarters
2014-Q1 .. 2026-Q3.

Task: was the trip taken by a member rather than a casual rider?

Real, dated changes in the published trip files (found from data/bronze/cabi/_profile.json and the code-list
profile runs/v3_checks/codes_cabi.json):
  2020-Q2  new layout (operator's system change): ride_id, rideable_type, started_at/ended_at, member_casual
           (member/casual instead of Member/Casual), station coordinates; trip duration and bike number removed;
           timestamps partly with fractional seconds. Same quarter as the start of the pandemic.
  2020-Q3  blank station ids (dockless electric-bike trips); whole-second timestamps again
  2020-Q4  rideable_type code 'classic_bike' introduced next to 'docked_bike' (code list; read correctly by all
           adapter versions)
  2023-Q4  rideable_type code 'docked_bike' retired
  2024-Q2  timestamps with fractional seconds
(2020-Q1 also contains 18 records already in the 2020 layout, read as blanks by the old-layout adapter.)
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
BRONZE = ROOT / "data" / "bronze" / "cabi"
ART = ROOT / "data" / "artifacts" / "cabi"

PERIODS = sorted(p.stem for p in BRONZE.glob("[0-9]*.parquet")) if BRONZE.exists() else []
CAT_FEATURES = ["start_area", "end_area", "bike"]
NUM_FEATURES = ["hour", "dow", "month", "duration_min", "distance_km", "round_trip", "start_lat", "start_lng",
                "end_lat", "end_lng"]
FEATURES = NUM_FEATURES + CAT_FEATURES
LABEL = "y"
ID_COLS = ["trip_id"]
TASK = "binary"

# published layouts (column names in file order)
HOLD = ["Duration", "Start date", "End date", "Start station number", "Start station", "End station number",
        "End station", "Bike number", "Member type"]
H2020 = ["ride_id", "rideable_type", "started_at", "ended_at", "start_station_name", "start_station_id",
         "end_station_name", "end_station_id", "start_lat", "start_lng", "end_lat", "end_lng", "member_casual"]
CANON = ["duration", "start", "end", "start_station", "start_name", "end_station", "end_name", "bike_id", "user"]

C = {}


def comp(name, inputs, doc=""):
    C[name] = Component(name, inputs, doc=doc)
    return C[name]


trip_adapter = comp("trip_adapter", ["raw:trips"], "published trip columns -> canonical schema")


@trip_adapter.variant("v2014")
def _ta(inp, p, a):
    """Rename by layout (param `layout`, maintained per published layout). With `positional`, columns are taken by
    position in the original order (the original code)."""
    r = inp["raw:trips"]
    layout = p.get("layout", "old")
    out = pd.DataFrame({"trip_id": r["_row"].astype("int64")})
    if p.get("positional", False):
        cols = [c for c in r.columns if c != "_row"][:9]
        for k, c in zip(CANON, cols):
            out[k] = r[c].astype(str).values
        out["start_lat"] = out["start_lng"] = out["end_lat"] = out["end_lng"] = np.nan
        out["bike"] = "classic"
    elif layout == "h2020":
        m = dict(zip(["start", "end", "start_station", "end_station"],
                     ["started_at", "ended_at", "start_station_id", "end_station_id"]))
        for k, c in m.items():
            out[k] = r[c].astype(str).values
        out["duration"] = ""
        out["user"] = r["member_casual"].astype(str).values
        for k in ("start_lat", "start_lng", "end_lat", "end_lng"):
            out[k] = pd.to_numeric(r[k], errors="coerce").values
        out["bike"] = np.where(r["rideable_type"].astype(str) == "electric_bike", "electric", "classic")
    else:
        for k, c in zip(CANON, HOLD):
            out[k] = (r[c].astype(str) if c in r.columns else pd.Series("", index=r.index)).values
        out["start_lat"] = out["start_lng"] = out["end_lat"] = out["end_lng"] = np.nan
        out["bike"] = "classic"
    # user type: published as Member/Casual until 2020-Q1, member/casual from 2020-Q2
    u = out["user"].str.strip()
    if p.get("user_recode", True):
        u = u.str.lower()
    else:      # original code: exactly "Member" is a member, anything else casual
        u = pd.Series(np.where(u == "Member", "member", "casual"), index=u.index)
    out["user"] = u
    return out[["trip_id", "start", "end", "duration", "start_station", "end_station", "user", "start_lat",
                "start_lng", "end_lat", "end_lng", "bike"]]


time_features = comp("time_features", ["trip_adapter"], "hour, day of week, month, duration")


@time_features.variant("v2014")
def _tf(inp, p, a):
    df = inp["trip_adapter"].copy()
    if p.get("dayfirst", False):
        # incident replay (nyc-taxi-data issue #3): day-first parsing of the published timestamps
        st = pd.to_datetime(df["start"], dayfirst=True, errors="coerce")
        en = pd.to_datetime(df["end"], dayfirst=True, errors="coerce")
    else:
        fmt = p.get("fmt", "%Y-%m-%d %H:%M:%S")
        st = pd.to_datetime(df["start"], format=fmt, errors="coerce")
        en = pd.to_datetime(df["end"], format=fmt, errors="coerce")
    df["hour"] = st.dt.hour.astype("float64")
    df["dow"] = st.dt.dayofweek.astype("float64")
    df["month"] = st.dt.month.astype("float64")
    dur = df["duration"].astype(str)
    if p.get("strip_commas", False):
        dur = dur.str.replace(",", "", regex=False)
    dur_s = pd.to_numeric(dur, errors="coerce")
    # original idiom where the published duration is absent: epoch nanoseconds via astype(int64)
    # (resolution-dependent across pandas versions)
    ok = st.notna() & en.notna()
    epoch = pd.Series(np.nan, index=df.index)
    epoch[ok] = (en[ok].astype("int64") - st[ok].astype("int64")) / 1e9
    df["duration_min"] = np.where(df["duration"].astype(str).str.len() > 0, dur_s, epoch) / 60.0
    return df.drop(columns=["start", "end", "duration"])


station_join = comp("station_join", ["time_features"], "station coordinates, distance, round trip")


def _haversine(a1, o1, a2, o2):
    a1, o1, a2, o2 = map(np.radians, (a1, o1, a2, o2))
    h = np.sin((a2 - a1) / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin((o2 - o1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


@station_join.variant("v2014")
def _sj(inp, p, a):
    df = inp["time_features"].copy()
    st = a["stations"]
    lat, lng = st["lat"], st["lng"]
    use_rec = p.get("record_coords", False) and df["start_lat"].notna().any()
    end_key = "start_station" if p.get("end_key_bug", False) else "end_station"
    if not use_rec:
        df["start_lat"] = df["start_station"].map(lat)
        df["start_lng"] = df["start_station"].map(lng)
        df["end_lat"] = df[end_key].map(lat)
        df["end_lng"] = df[end_key].map(lng)
    for k in ("start_lat", "start_lng", "end_lat", "end_lng"):
        df[k] = pd.to_numeric(df[k], errors="coerce").astype("float64")
    df["distance_km"] = _haversine(df["start_lat"], df["start_lng"], df["end_lat"], df["end_lng"])
    rt = (df["start_station"] == df["end_station"]).astype("float64")
    if p.get("blank_as_missing", False):     # dockless trips (blank station ids) are not round trips
        rt = rt.where((df["start_station"].str.strip() != "") & (df["end_station"].str.strip() != ""))
    df["round_trip"] = rt
    return df.drop(columns=["start_station", "end_station"])


clean = comp("clean", ["station_join"], "plausible trips, area cells, label")


def _cell(lat: pd.Series, lng: pd.Series) -> pd.Series:
    la, lo = np.floor(lat / 0.05) * 0.05, np.floor(lng / 0.05) * 0.05
    s = la.round(2).astype(str) + "_" + lo.round(2).astype(str)
    return s.where(lat.notna() & lng.notna(), "NA")


@clean.variant("v2014")
def _cl(inp, p, a):
    df = inp["station_join"]
    df = df[(df["duration_min"] >= 1) & (df["duration_min"] <= 360)].copy()
    # pandas-1.x idiom: the distance of a round trip is meaningless -> missing (chained assignment; a no-op under
    # copy-on-write)
    df["distance_km"][df["round_trip"] == 1] = np.nan
    df["start_area"] = _cell(df["start_lat"], df["start_lng"])
    df["end_area"] = _cell(df["end_lat"], df["end_lng"])
    df["y"] = (df["user"] == "member").astype("int8")
    return df.drop(columns=["user"]).reset_index(drop=True)


@clean.variant("v2024_loc")
def _cl_loc(inp, p, a):
    df = inp["station_join"]
    df = df[(df["duration_min"] >= 1) & (df["duration_min"] <= 360)].copy()
    df.loc[df["round_trip"] == 1, "distance_km"] = np.nan
    df["start_area"] = _cell(df["start_lat"], df["start_lng"])
    df["end_area"] = _cell(df["end_lat"], df["end_lng"])
    df["y"] = (df["user"] == "member").astype("int8")
    return df.drop(columns=["user"]).reset_index(drop=True)


encode = comp("encode", ["clean"], "model matrix with categorical codes from the encoder artifact")


def fit_encoder(df: pd.DataFrame) -> dict:
    return {c: {k: i for i, k in enumerate(dict.fromkeys(df[c].astype(str).tolist()))} for c in CAT_FEATURES}


@encode.variant("v2014")
def _enc(inp, p, a):
    df = inp["clean"]
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


def build_station_artifact() -> None:
    """Station id -> coordinates. The operator published no station table with the old layout; the table is built
    from the station coordinates published in the 2020-Q3 trip records (median per station id); version 'official'."""
    r = pd.read_parquet(BRONZE / "2020-Q3.parquet")
    rows = []
    for idc, la, lo in (("start_station_id", "start_lat", "start_lng"), ("end_station_id", "end_lat", "end_lng")):
        d = pd.DataFrame({"id": r[idc].astype(str).str.strip(), "lat": pd.to_numeric(r[la], errors="coerce"),
                          "lng": pd.to_numeric(r[lo], errors="coerce")})
        rows.append(d[d["id"] != ""])
    d = pd.concat(rows).dropna().groupby("id").median()
    save_artifact("stations", "official", {"lat": d["lat"].round(6).to_dict(), "lng": d["lng"].round(6).to_dict()})


PIPELINE = Pipeline(domain="cabi", components=C, output="encode", raw_tables=["trips"],
                    load_raw=load_raw, load_artifact=load_artifact)
V = Version.make


def _layout(period: str) -> str:
    return "h2020" if period >= "2020-Q2" else "old"


def _fmt(period: str) -> str:
    if period >= "2024-Q2" or period == "2020-Q2":
        return "ISO8601"
    return "%Y-%m-%d %H:%M:%S"


def _prev_fmt(period: str) -> str:
    """The format of the most recent earlier published change (what a stale parser still expects)."""
    return "%Y-%m-%d %H:%M:%S"


def reference_state(encoder_id: str, p0: str = "2016-Q3") -> dict:
    return {
        "trip_adapter": V("v2014", {"layout": _layout(p0)}),
        "time_features": V("v2014", {"fmt": _fmt(p0)}),
        "station_join": V("v2014", artifacts={"stations": "official"}),
        "clean": V("v2014", env="p15"),          # deployed in a pandas-1.5 environment
        "encode": V("v2014", artifacts={"encoder": encoder_id}),
    }


def spec_state(period: str, encoder_id: str) -> dict:
    """Correct pipeline for a period: every published layout and format is read with its own mapping."""
    s = reference_state(encoder_id, period)
    tf = {"fmt": _fmt(period)}
    s["time_features"] = V("v2014", tf)
    sj = {}
    if period >= "2020-Q2":
        sj["record_coords"] = True
    if period >= "2020-Q3":
        sj["blank_as_missing"] = True
    if sj:
        s["station_join"] = V("v2014", sj, {"stations": "official"})
    return s


EVENTS = [
    ("2020-Q2", "new layout: ride_id, rideable_type, started_at/ended_at, member_casual, coordinates; duration and "
                "bike number removed; timestamps partly with fractional seconds", HOLD + H2020),
    ("2020-Q3", "blank station ids (dockless trips); whole-second timestamps", ["start_station_id", "end_station_id",
                                                                             "started_at", "ended_at"]),
    ("2020-Q4", "rideable_type code 'classic_bike' introduced next to 'docked_bike'", ["rideable_type"]),
    ("2023-Q4", "rideable_type code 'docked_bike' retired", ["rideable_type"]),
    ("2024-Q2", "timestamps with fractional seconds", ["started_at", "ended_at"]),
]


def source_events(period_from: str, period_to: str) -> list[dict]:
    return [{"period": w, "table": "trips", "change": what, "columns": cols}
            for w, what, cols in EVENTS if period_from < w <= period_to]


LINEAGE = {
    "hour": ["trip_adapter", "time_features"], "dow": ["trip_adapter", "time_features"],
    "month": ["trip_adapter", "time_features"], "duration_min": ["trip_adapter", "time_features", "clean"],
    "distance_km": ["trip_adapter", "station_join", "clean"], "round_trip": ["trip_adapter", "station_join"],
    "start_lat": ["trip_adapter", "station_join"], "start_lng": ["trip_adapter", "station_join"],
    "end_lat": ["trip_adapter", "station_join"], "end_lng": ["trip_adapter", "station_join"],
    "start_area": ["trip_adapter", "station_join", "clean", "encode"],
    "end_area": ["trip_adapter", "station_join", "clean", "encode"],
    "bike": ["trip_adapter", "encode"],
    "y": ["trip_adapter", "clean"],
}
SOURCE_READERS = {"trips": ["trip_adapter"]}
_ALL = sorted(set(HOLD + H2020))
_TIME = ["Start date", "End date", "started_at", "ended_at", "Duration"]
_STATION = ["Start station number", "End station number", "start_station_id", "end_station_id", "start_lat",
            "start_lng", "end_lat", "end_lng"]
RAW_COLUMNS = {
    "trip_adapter": {"trips": _ALL},
    "time_features": {"trips": _TIME},
    "station_join": {"trips": _STATION},
    "clean": {"trips": _TIME + _STATION + ["Member type", "member_casual"]},
    "encode": {"trips": _ALL},
}
COLUMN_SOURCES = {
    "trip_adapter": {"start": ["Start date", "started_at"], "end": ["End date", "ended_at"],
                     "duration": ["Duration"], "start_station": ["Start station number", "start_station_id"],
                     "end_station": ["End station number", "end_station_id"],
                     "user": ["Member type", "member_casual"], "bike": ["rideable_type"], "trip_id": ["_row"],
                     "start_lat": ["start_lat"], "start_lng": ["start_lng"], "end_lat": ["end_lat"],
                     "end_lng": ["end_lng"]},
    "time_features": {"hour": ["start"], "dow": ["start"], "month": ["start"],
                      "duration_min": ["start", "end", "duration"]},
    "station_join": {"start_lat": ["start_station", "start_lat"], "start_lng": ["start_station", "start_lng"],
                     "end_lat": ["end_station", "end_lat"], "end_lng": ["end_station", "end_lng"],
                     "distance_km": ["start_station", "end_station", "start_lat", "start_lng", "end_lat", "end_lng"],
                     "round_trip": ["start_station", "end_station"]},
    "clean": {"start_area": ["start_lat", "start_lng"], "end_area": ["end_lat", "end_lng"], "y": ["user"],
              "distance_km": ["distance_km", "round_trip"]},
}


def catalog(period: str, encoder_id: str) -> list[dict]:
    sp = spec_state(period, encoder_id)
    ta, tf, sj = sp["trip_adapter"].p(), sp["time_features"].p(), sp["station_join"]
    out = []

    def add(cid, comp_, version, kind, tier, silent_hint, note, source=""):
        out.append({"id": cid, "component": comp_, "version": version, "kind": kind, "tier": tier,
                    "silent_hint": silent_hint, "note": note, "source": source})
    new = period >= "2020-Q2"
    add("cabi.positional", "trip_adapter", V("v2014", {**ta, "positional": True}), "defect" if new else "benign",
        "T1" if new else "B", True, "columns taken by position in the original order",
        "nyc-taxi-data issue #8 (positional schema)")
    if new:
        add("cabi.user_recode_stale", "trip_adapter", V("v2014", {**ta, "user_recode": False}), "defect", "T1", True,
            "user type mapped with the Member/Casual rule: every lowercase member becomes casual")
        add("cabi.coords_lookup_stale", "station_join",
            V("v2014", {k: v for k, v in sj.p().items() if k != "record_coords"}, {"stations": "official"}),
            "defect", "T1", True, "station coordinates still taken from the station table instead of the records")
    if period >= "2020-Q3":
        add("cabi.blank_ids_stale", "station_join",
            V("v2014", {k: v for k, v in sj.p().items() if k != "blank_as_missing"}, {"stations": "official"}),
            "defect", "T1", True, "blank station ids of dockless trips compared as equal: counted as round trips")
    if tf.get("fmt") == "ISO8601":
        add("cabi.fmt_stale", "time_features", V("v2014", {**tf, "fmt": _prev_fmt(period)}), "defect", "T1", True,
            "timestamps parsed with the previous published format (fractional seconds unparsed)")
    if not new:
        add("cabi.dayfirst", "time_features", V("v2014", {**tf, "dayfirst": True}, env="p15"), "defect", "T3r",
            True, "day-first timestamp parsing", "nyc-taxi-data issue #3")
    add("cabi.time_env_p30", "time_features", V("v2014", tf, env="p30"),
        "defect" if new else "benign", "T2" if new else "T2b", True,
        "pandas 3 upgrade: duration from epoch nanoseconds via astype(int64) changes resolution", "pandas issue #65308")
    add("cabi.adapter_env_p30", "trip_adapter", V("v2014", ta, env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the adapter")
    add("cabi.end_key_bug", "station_join", V("v2014", {**sj.p(), "end_key_bug": True}, sj.a()), "defect", "T3",
        True, "end coordinates looked up with the start station id (copy-paste key bug)")
    add("cabi.clean_env_main", "clean", V("v2014"), "benign", "T2b", True, "pandas 2.2 upgrade of the cleaning step")
    add("cabi.clean_env_p30", "clean", V("v2014", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: chained assignment blanking round-trip distances becomes a no-op",
        "pandas 3.0 release notes (copy-on-write)")
    add("cabi.clean_modernised", "clean", V("v2024_loc"), "benign", "B", True, "chained assignment -> .loc")
    add("cabi.encoder_refit", "encode", V("v2014", {"refit": True}, sp["encode"].a()), "defect", "T3", True,
        "categorical codes re-fitted at serving time (training/serving skew)")
    add("cabi.unknown_as_reference", "encode", V("v2014", {"unknown_as_reference": True}, sp["encode"].a()),
        "defect", "T3r", True, "unseen categories encoded as the reference category", "scikit-learn issue #34549")
    return out
