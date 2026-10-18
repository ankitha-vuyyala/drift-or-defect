"""US severe-weather damage pipeline (round-4 held-out domain): NOAA NCEI Storm Events Database, years 1996-2025,
every published event, with its fatality and location records (three source tables).

Task: did the event cause reported property damage? (From the event type, place, time, magnitude, tornado rating,
casualties, reporting source and spatial extent.)

The three yearly files keep one column layout for all years, so every dated change is a change of codes or of
coverage. Changes found from the per-year profiles (data/bronze/storm/_profile.json):
  2006  time-zone codes with the UTC offset appended ('CST-6', 'AKST-9', 'GST10') published next to the old codes
        ('CST'); reporting-source codes republished in title case with new names ('Public' for 'GENERAL PUBLIC',
        'Official NWS Observations' for 'OFFICIAL NWS OBS.', ...); damage amounts partly written with two decimals;
        indirect fatalities ('I') published in the fatality file; fatality-location codes extended; the location file
        lists only events with coordinates, several points per event
  2007  old time-zone and source codes retired; tornado ratings on the Enhanced Fujita scale ('EF0'-'EF5' instead of
        'F0'-'F5'); 'no damage' written '0.00K' instead of blank; event type 'Volcanic Ash' renamed 'Volcanic
        Ashfall'; zone type 'M' (marine) retired
  2008, 2012, 2014, 2015  reporting-source codes added (title-case list)
  2016  tornado rating 'EFU' (unrated) added
  2021  daylight-time zone codes ('CDT-5', 'EDT-4', 'PDT-7') added
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from dod.core import Component, Pipeline, Version

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[4]))
BRONZE = ROOT / "data" / "bronze" / "storm"
ART = ROOT / "data" / "artifacts" / "storm"

PERIODS = sorted(p.stem for p in (BRONZE / "details").glob("[0-9]*.parquet")) if BRONZE.exists() else []
CAT_FEATURES = ["state", "event_type", "cz_type", "source_group", "cell"]
NUM_FEATURES = ["hour", "month", "duration_h", "utc_offset", "tor_f", "tor_length", "tor_width", "wind_kt",
                "hail_in", "injuries", "deaths", "n_fatal", "fatal_home", "n_points", "extent"]
FEATURES = NUM_FEATURES + CAT_FEATURES
LABEL = "y"
ID_COLS = ["event_id"]
TASK = "binary"

C = {}


def comp(name, inputs, doc=""):
    C[name] = Component(name, inputs, doc=doc)
    return C[name]


def _s(r: pd.DataFrame, c: str) -> pd.Series:
    return r[c].astype(str).str.strip()


def _num(r: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(_s(r, c), errors="coerce")


# ----------------------------------------------------------------------------------------------- source adapters
event_adapter = comp("event_adapter", ["raw:details"], "published event fields -> canonical schema")


@event_adapter.variant("v1996")
def _ea(inp, p, a):
    r = inp["raw:details"]
    return pd.DataFrame({
        "event_id": _num(r, "EVENT_ID").astype("int64"),
        "episode_id": _num(r, "EPISODE_ID"),
        "state": _s(r, "STATE"),
        "event_type": _s(r, "EVENT_TYPE"),
        "cz_type": _s(r, "CZ_TYPE"),
        "tz": _s(r, "CZ_TIMEZONE"),
        "begin_ym": _s(r, "BEGIN_YEARMONTH"), "begin_day": _s(r, "BEGIN_DAY"), "begin_time": _s(r, "BEGIN_TIME"),
        "end_ym": _s(r, "END_YEARMONTH"), "end_day": _s(r, "END_DAY"), "end_time": _s(r, "END_TIME"),
        "injuries": _num(r, "INJURIES_DIRECT").fillna(0) + _num(r, "INJURIES_INDIRECT").fillna(0),
        "deaths": _num(r, "DEATHS_DIRECT").fillna(0),
        "damage": _s(r, "DAMAGE_PROPERTY"),
        "source": _s(r, "SOURCE"),
        "magnitude": _num(r, "MAGNITUDE"),
        "tor_scale": _s(r, "TOR_F_SCALE"),
        "tor_length": _num(r, "TOR_LENGTH"),
        "tor_width": _num(r, "TOR_WIDTH"),
        "lat": _num(r, "BEGIN_LAT"),
        "lon": _num(r, "BEGIN_LON"),
    })


fatality_adapter = comp("fatality_adapter", ["raw:fatalities"], "published fatality records -> canonical schema")


@fatality_adapter.variant("v1996")
def _fa(inp, p, a):
    r = inp["raw:fatalities"]
    out = pd.DataFrame({"event_id": _num(r, "EVENT_ID"), "ftype": _s(r, "FATALITY_TYPE"),
                        "floc": _s(r, "FATALITY_LOCATION")})
    out = out[out["event_id"].notna()]
    return out.assign(event_id=out["event_id"].astype("int64")).reset_index(drop=True)


location_adapter = comp("location_adapter", ["raw:locations"], "published location points -> canonical schema")


@location_adapter.variant("v1996")
def _la(inp, p, a):
    r = inp["raw:locations"]
    out = pd.DataFrame({"event_id": _num(r, "EVENT_ID"), "episode_id": _num(r, "EPISODE_ID"),
                        "lat": _num(r, "LATITUDE"), "lon": _num(r, "LONGITUDE")})
    out = out[out["event_id"].notna()]
    return out.assign(event_id=out["event_id"].astype("int64")).reset_index(drop=True)


# ----------------------------------------------------------------------------------------------- event branch
times = comp("times", ["event_adapter"], "hour, month, duration, UTC offset from the time-zone table")


def _stamp(ym: pd.Series, day: pd.Series, hhmm: pd.Series) -> pd.Series:
    return pd.to_datetime(ym + day.str.zfill(2) + hhmm.str.zfill(4), format="%Y%m%d%H%M", errors="coerce")


@times.variant("v1996")
def _tm(inp, p, a):
    df = inp["event_adapter"].copy()
    b = _stamp(df["begin_ym"], df["begin_day"], df["begin_time"])
    e = _stamp(df["end_ym"], df["end_day"], df["end_time"])
    df["hour"] = (pd.to_numeric(df["begin_time"], errors="coerce") // 100).astype("float64")
    df["month"] = (pd.to_numeric(df["begin_ym"], errors="coerce") % 100).astype("float64")
    # original idiom: duration from epoch nanoseconds (resolution-dependent across pandas versions)
    ok = b.notna() & e.notna()
    dur = pd.Series(np.nan, index=df.index)
    dur[ok] = ((e[ok].astype("int64") - b[ok].astype("int64")) / 3_600_000_000_000).astype("float64")
    if p.get("duration_minutes", False):        # incident class: duration reported in minutes, not hours
        dur = dur * 60.0
    df["duration_h"] = dur
    tzc = df["tz"]
    if p.get("tz_prefix_only", False):          # faulty fix: drop the appended offset, look up the old code
        tzc = tzc.str.extract(r"^([A-Z]+)", expand=False).fillna("")
    df["utc_offset"] = tzc.map(a["tz_offsets"]).astype("float64")
    return df.drop(columns=["begin_ym", "begin_day", "begin_time", "end_ym", "end_day", "end_time", "tz"])


scale = comp("scale", ["times"], "tornado rating -> number")

F_SCALE = {f"F{i}": i for i in range(6)}
EF_SCALE = {f"EF{i}": i for i in range(6)}


@scale.variant("v1996")
def _sc(inp, p, a):
    df = inp["times"].copy()
    table = dict(F_SCALE)
    if p.get("scheme", "F") == "EF":             # from 2007: Enhanced Fujita ratings
        table.update(EF_SCALE)
    tor = df["tor_scale"].map(table).astype("float64")
    if p.get("efu_as_zero", False):              # faulty fix: unrated tornadoes ('EFU') coded as the lowest rating
        tor = tor.where(df["tor_scale"] != "EFU", 0.0)
    df["tor_f"] = tor
    return df.drop(columns=["tor_scale"])


sources = comp("sources", ["scale"], "reporting source -> source group via the source crosswalk")


@sources.variant("v1996")
def _so(inp, p, a):
    df = inp["scale"].copy()
    src = df["source"]
    if p.get("casefold", False):                 # faulty fix: upper-case new codes and look them up in the old list
        src = src.str.upper()
    df["source_group"] = src.map(a["source_xwalk"]).fillna("unknown")
    return df.drop(columns=["source"])


# ----------------------------------------------------------------------------------------------- side branches
fatal_agg = comp("fatal_agg", ["fatality_adapter"], "fatalities per event and share at home")

HOME = {"Permanent Home", "Mobile/Trailer Home"}


@fatal_agg.variant("v1996")
def _fg(inp, p, a):
    f = inp["fatality_adapter"]
    if p.get("direct_only", False):              # from 2006: indirect fatalities are published as well
        f = f[f["ftype"] == "D"]
    f = f.assign(home=f["floc"].isin(HOME).astype("float64"))
    g = f.groupby("event_id", as_index=False).agg(n_fatal=("home", "size"), fatal_home=("home", "mean"))
    g["n_fatal"] = g["n_fatal"].astype("float64")
    return g


loc_agg = comp("loc_agg", ["location_adapter"], "location points per event and spatial extent")


@loc_agg.variant("v1996")
def _lg(inp, p, a):
    l_ = inp["location_adapter"]
    l_ = l_[l_["lat"].notna() & l_["lon"].notna()]
    key = "episode_id" if p.get("by_episode", False) else "event_id"   # incident class: wrong grouping key
    g = l_.groupby(key, as_index=False).agg(n_points=("lat", "size"), lat_min=("lat", "min"), lat_max=("lat", "max"),
                                            lon_min=("lon", "min"), lon_max=("lon", "max"))
    g["n_points"] = g["n_points"].astype("float64")
    g["extent"] = (g["lat_max"] - g["lat_min"]) + (g["lon_max"] - g["lon_min"])
    return g[[key, "n_points", "extent"]]


join = comp("join", ["sources", "fatal_agg", "loc_agg"], "left join of the event branch and the per-event aggregates")


@join.variant("v1996")
def _jn(inp, p, a):
    ev, fa, lo = inp["sources"], inp["fatal_agg"], inp["loc_agg"]
    if p.get("dedupe_right", True):
        fa = fa.drop_duplicates("event_id")
        lo = lo.drop_duplicates(lo.columns[0])
    out = ev.merge(fa, on="event_id", how="left")
    key = lo.columns[0]
    out = out.merge(lo, on=key, how="left")
    for c in ("n_fatal", "fatal_home", "n_points", "extent"):
        out[c] = out[c].fillna(0.0)
    return out.reset_index(drop=True)


geo = comp("geo", ["join"], "3-degree grid cell of the begin point")


@geo.variant("v1996")
def _geo(inp, p, a):
    df = inp["join"].copy()
    lat, lon = df["lat"], df["lon"]
    if p.get("swap_lat_lon", False):             # incident class: latitude and longitude swapped
        lat, lon = lon, lat
    ok = lat.notna() & lon.notna()
    cell = pd.Series("NA", index=df.index, dtype=object)
    cell[ok] = (np.floor(lat[ok] / 3).astype(int).astype(str) + "_" + np.floor(lon[ok] / 3).astype(int).astype(str))
    df["cell"] = cell
    return df.drop(columns=["lat", "lon"])


clean = comp("clean", ["geo"], "wind speed and hail size by event type, label from the damage amount")

WIND = {"Thunderstorm Wind", "High Wind", "Strong Wind", "Marine Thunderstorm Wind", "Marine High Wind",
        "Marine Strong Wind"}
HAIL = {"Hail", "Marine Hail"}
_MULT = {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "H": 1e2}


def damage_usd(s: pd.Series) -> pd.Series:
    m = s.str.upper().str.extract(r"^\s*([0-9.]*)\s*([KMBH]?)\s*$")
    v = pd.to_numeric(m[0], errors="coerce")
    return (v * m[1].map(_MULT)).fillna(0.0)


@clean.variant("v1996")
def _cl(inp, p, a):
    df = inp["geo"].copy()
    wind, hail = df["event_type"].isin(WIND), df["event_type"].isin(HAIL)
    # pandas-1.x idiom: fill wind speed and hail size in place (chained assignment; a no-op under copy-on-write)
    df["wind_kt"] = np.nan
    df["hail_in"] = np.nan
    df["wind_kt"][wind] = df["magnitude"][wind]
    df["hail_in"][hail] = df["magnitude"][hail]
    if p.get("wind_kt_as_mph", False):           # incident class: knots converted to mph
        df["wind_kt"] = df["wind_kt"] * 1.15078
    df["y"] = (damage_usd(df["damage"]) > 0).astype("int8")
    return df.drop(columns=["magnitude", "damage", "episode_id"]).reset_index(drop=True)


@clean.variant("v2024_loc")
def _cl_loc(inp, p, a):
    df = inp["geo"].copy()
    wind, hail = df["event_type"].isin(WIND), df["event_type"].isin(HAIL)
    df["wind_kt"] = df["magnitude"].where(wind)
    df["hail_in"] = df["magnitude"].where(hail)
    if p.get("wind_kt_as_mph", False):
        df["wind_kt"] = df["wind_kt"] * 1.15078
    df["y"] = (damage_usd(df["damage"]) > 0).astype("int8")
    return df.drop(columns=["magnitude", "damage", "episode_id"]).reset_index(drop=True)


encode = comp("encode", ["clean"], "model matrix with categorical codes from the encoder artifact")


def fit_encoder(df: pd.DataFrame) -> dict:
    return {c: {k: i for i, k in enumerate(dict.fromkeys(df[c].astype(str).tolist()))} for c in CAT_FEATURES}


@encode.variant("v1996")
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
    return pd.read_parquet(BRONZE / table / f"{period}.parquet")


@lru_cache(maxsize=64)
def _load_art(name: str, version: str) -> str:
    return (ART / name / f"{version}.json").read_text(encoding="utf-8")


def load_artifact(name: str, version: str):
    return json.loads(_load_art(name, version))


def save_artifact(name: str, version: str, obj) -> None:
    (ART / name).mkdir(parents=True, exist_ok=True)
    (ART / name / f"{version}.json").write_text(json.dumps(obj, sort_keys=True), encoding="utf-8")
    _load_art.cache_clear()


# Standard UTC offsets (hours) of the time-zone codes published 1996-2005.
TZ_1996 = {"AST": -4, "EST": -5, "CST": -6, "MST": -7, "PST": -8, "HST": -10, "SST": -11}


def _tz_suffixed(codes) -> dict:
    out = {}
    for c in codes:
        m = re.match(r"^([A-Z]+)(-?\d+)$", c)
        if m:
            out[c] = int(m.group(2))
    return out


def _source_group(code: str) -> str:
    """Grouping rule for reporting sources (applied to every code of a code list when its crosswalk is built)."""
    u = code.upper()
    if "NON NWS" in u:
        return "other"
    if "SURVEY" in u:
        return "nws_survey"
    if "NWS" in u or u == "WFO":
        return "nws"
    if any(k in u for k in ("SPOTTER", "CHASER", "AMATEUR", "COCORAHS", "SHAVE")):
        return "spotter"
    if any(k in u for k in ("PUBLIC", "SOCIAL", "911")):
        return "public"
    if any(k in u for k in ("NEWSPAPER", "MEDIA")):
        return "media"
    if "INSURANCE" in u:
        return "insurance"
    if any(k in u for k in ("ASOS", "AWOS", "MESONET", "COOP", "BUOY", "C-MAN", "COASTAL OBSERVING", "GAGE",
                            "SNOTEL", "RAWS", "AWSS", "WLON", "NPOP", "DROUGHT")):
        return "network"
    if any(k in u for k in ("LAW", "EMERGENCY", "FIRE", "HIGHWAY", "OFFICIAL", "GOVT", "FEDERAL", "PARK",
                            "POST OFFICE", "UTILITY", "COAST GUARD", "LIFEGUARD")):
        return "official"
    return "other"


def build_artifacts() -> dict:
    """Time-zone tables and source crosswalks, one per published code list:
      tz_offsets '1996' (codes without offset), '2006' (+ codes with the offset appended), '2021' (+ daylight codes);
      source_xwalk '1996' (every source code published 1996-2005), '2006' (every code published from 2006 on).
    Code lists are read from the bronze profiles; offsets of suffixed codes are the published suffix."""
    prof = json.loads((BRONZE / "_profile.json").read_text(encoding="utf-8"))["details"]

    def codes(col, y0, y1):
        out = set()
        for y, pr in prof.items():
            if y0 <= int(y) <= y1:
                out |= set(pr["codes"].get(col, {}))
        return out
    tz_old = codes("CZ_TIMEZONE", 1996, 2025)
    std = {c for c in tz_old if re.match(r"^[A-Z]{2,4}S?T-?\d+$", c) and "DT" not in c}
    day = {c for c in tz_old if re.match(r"^[A-Z]DT-?\d+$", c)}
    t96 = dict(TZ_1996)
    t06 = {**t96, **_tz_suffixed(std)}
    t21 = {**t06, **_tz_suffixed(day)}
    save_artifact("tz_offsets", "1996", t96)
    save_artifact("tz_offsets", "2006", t06)
    save_artifact("tz_offsets", "2021", t21)
    src = {}
    for vint, y0, y1 in (("1996", 1996, 2005), ("2006", 2006, 2025)):
        sc = _source_codes(y0, y1)
        src[vint] = {c: _source_group(c) for c in sorted(sc) if c}
        save_artifact("source_xwalk", vint, src[vint])
    return {"tz": [len(t96), len(t06), len(t21)], "sources": {k: len(v) for k, v in src.items()}}


def _source_codes(y0: int, y1: int) -> set:
    out = set()
    for y in range(y0, y1 + 1):
        f = BRONZE / "details" / f"{y}.parquet"
        if f.exists():
            out |= set(pd.read_parquet(f, columns=["SOURCE"])["SOURCE"].astype(str).str.strip())
    return out


PIPELINE = Pipeline(domain="storm", components=C, output="encode", raw_tables=["details", "fatalities", "locations"],
                    load_raw=load_raw, load_artifact=load_artifact)
V = Version.make


# ----------------------------------------------------------------------------------------------- reference and spec
def reference_state(encoder_id: str, p0: str = "2003") -> dict:
    """The pipeline as deployed when the reference model was trained (times and clean in a pandas-1.5
    environment), adapted to every published change up to p0."""
    y = int(p0)
    return {
        "event_adapter": V("v1996"),
        "fatality_adapter": V("v1996"),
        "location_adapter": V("v1996"),
        "times": V("v1996", artifacts={"tz_offsets": "2021" if y >= 2021 else ("2006" if y >= 2006 else "1996")},
                   env="p15"),
        "scale": V("v1996", {"scheme": "EF"} if y >= 2007 else {}),
        "sources": V("v1996", artifacts={"source_xwalk": "2006" if y >= 2006 else "1996"}),
        "fatal_agg": V("v1996", {"direct_only": True} if y >= 2006 else {}),
        "loc_agg": V("v1996"),
        "join": V("v1996"),
        "geo": V("v1996"),
        "clean": V("v1996", env="p15"),
        "encode": V("v1996", artifacts={"encoder": encoder_id}),
    }


def spec_state(period: str, encoder_id: str) -> dict:
    return reference_state(encoder_id, period)


EVENTS = [
    ("2006", "details", "time-zone codes with UTC offset appended; source codes republished in title case with new "
     "names; damage amounts partly with two decimals", ["CZ_TIMEZONE", "SOURCE", "DAMAGE_PROPERTY"]),
    ("2006", "fatalities", "indirect fatalities published; fatality-location codes extended",
     ["FATALITY_TYPE", "FATALITY_LOCATION"]),
    ("2006", "locations", "only events with coordinates listed; several points per event",
     ["EVENT_ID", "LATITUDE", "LONGITUDE"]),
    ("2007", "details", "old time-zone and source codes retired; tornado ratings on the Enhanced Fujita scale; "
     "'0.00K' for no damage; 'Volcanic Ash' renamed 'Volcanic Ashfall'; zone type 'M' retired",
     ["CZ_TIMEZONE", "SOURCE", "TOR_F_SCALE", "DAMAGE_PROPERTY", "EVENT_TYPE", "CZ_TYPE"]),
    ("2008", "details", "reporting-source codes added", ["SOURCE"]),
    ("2012", "details", "reporting-source codes added", ["SOURCE"]),
    ("2014", "details", "reporting-source codes added", ["SOURCE"]),
    ("2015", "details", "reporting-source code added", ["SOURCE"]),
    ("2016", "details", "tornado rating 'EFU' (unrated) added", ["TOR_F_SCALE"]),
    ("2021", "details", "daylight-time zone codes added", ["CZ_TIMEZONE"]),
]


def source_events(period_from: str, period_to: str) -> list[dict]:
    return [{"period": w, "table": t, "change": what, "columns": cols}
            for w, t, what, cols in EVENTS if period_from < w <= period_to]


# ----------------------------------------------------------------------------------------------- lineage and catalog
LINEAGE = {
    "hour": ["event_adapter", "times"], "month": ["event_adapter", "times"], "duration_h": ["event_adapter", "times"],
    "utc_offset": ["event_adapter", "times"], "tor_f": ["event_adapter", "scale"],
    "tor_length": ["event_adapter"], "tor_width": ["event_adapter"],
    "wind_kt": ["event_adapter", "clean"], "hail_in": ["event_adapter", "clean"],
    "injuries": ["event_adapter"], "deaths": ["event_adapter"],
    "n_fatal": ["fatality_adapter", "fatal_agg", "join"], "fatal_home": ["fatality_adapter", "fatal_agg", "join"],
    "n_points": ["location_adapter", "loc_agg", "join"], "extent": ["location_adapter", "loc_agg", "join"],
    "state": ["event_adapter", "encode"], "event_type": ["event_adapter", "encode"],
    "cz_type": ["event_adapter", "encode"], "source_group": ["event_adapter", "sources", "encode"],
    "cell": ["event_adapter", "geo", "encode"], "y": ["event_adapter", "clean"],
}
SOURCE_READERS = {"details": ["event_adapter"], "fatalities": ["fatality_adapter"], "locations": ["location_adapter"]}
_D_ALL = ["EVENT_ID", "EPISODE_ID", "STATE", "EVENT_TYPE", "CZ_TYPE", "CZ_TIMEZONE", "BEGIN_YEARMONTH", "BEGIN_DAY",
          "BEGIN_TIME", "END_YEARMONTH", "END_DAY", "END_TIME", "INJURIES_DIRECT", "INJURIES_INDIRECT",
          "DEATHS_DIRECT", "DAMAGE_PROPERTY", "SOURCE", "MAGNITUDE", "TOR_F_SCALE", "TOR_LENGTH", "TOR_WIDTH",
          "BEGIN_LAT", "BEGIN_LON"]
_F_ALL = ["EVENT_ID", "FATALITY_TYPE", "FATALITY_LOCATION"]
_L_ALL = ["EVENT_ID", "EPISODE_ID", "LATITUDE", "LONGITUDE"]
_TIME = ["BEGIN_YEARMONTH", "BEGIN_DAY", "BEGIN_TIME", "END_YEARMONTH", "END_DAY", "END_TIME", "CZ_TIMEZONE"]
RAW_COLUMNS = {
    "event_adapter": {"details": _D_ALL},
    "fatality_adapter": {"fatalities": _F_ALL},
    "location_adapter": {"locations": _L_ALL},
    "times": {"details": _TIME},
    "scale": {"details": ["TOR_F_SCALE"]},
    "sources": {"details": ["SOURCE"]},
    "fatal_agg": {"fatalities": _F_ALL},
    "loc_agg": {"locations": _L_ALL},
    "join": {"details": ["EVENT_ID"], "fatalities": ["EVENT_ID"], "locations": ["EVENT_ID", "EPISODE_ID"]},
    "geo": {"details": ["BEGIN_LAT", "BEGIN_LON"]},
    "clean": {"details": ["EVENT_TYPE", "MAGNITUDE", "DAMAGE_PROPERTY"]},
    "encode": {"details": _D_ALL, "fatalities": _F_ALL, "locations": _L_ALL},
}
COLUMN_SOURCES = {
    "event_adapter": {"event_id": ["EVENT_ID"], "episode_id": ["EPISODE_ID"], "state": ["STATE"],
                      "event_type": ["EVENT_TYPE"], "cz_type": ["CZ_TYPE"], "tz": ["CZ_TIMEZONE"],
                      "injuries": ["INJURIES_DIRECT", "INJURIES_INDIRECT"], "deaths": ["DEATHS_DIRECT"],
                      "damage": ["DAMAGE_PROPERTY"], "source": ["SOURCE"], "magnitude": ["MAGNITUDE"],
                      "tor_scale": ["TOR_F_SCALE"], "tor_length": ["TOR_LENGTH"], "tor_width": ["TOR_WIDTH"],
                      "lat": ["BEGIN_LAT"], "lon": ["BEGIN_LON"]},
    "times": {"hour": ["begin_time"], "month": ["begin_ym"],
              "duration_h": ["begin_ym", "begin_day", "begin_time", "end_ym", "end_day", "end_time"],
              "utc_offset": ["tz"]},
    "scale": {"tor_f": ["tor_scale"]},
    "sources": {"source_group": ["source"]},
    "fatal_agg": {"n_fatal": ["ftype"], "fatal_home": ["ftype", "floc"]},
    "loc_agg": {"n_points": ["lat", "lon"], "extent": ["lat", "lon"]},
    "geo": {"cell": ["lat", "lon"]},
    "clean": {"wind_kt": ["magnitude", "event_type"], "hail_in": ["magnitude", "event_type"], "y": ["damage"]},
}


def catalog(period: str, encoder_id: str) -> list[dict]:
    y = int(period)
    sp = spec_state(period, encoder_id)
    out = []

    def add(cid, comp_, version, kind, tier, silent_hint, note, source=""):
        out.append({"id": cid, "component": comp_, "version": version, "kind": kind, "tier": tier,
                    "silent_hint": silent_hint, "note": note, "source": source})
    tm, sc, so = sp["times"], sp["scale"], sp["sources"]
    # T1: source-coupled defects (stale or faulty adaptations to the published changes)
    if y >= 2006:
        add("storm.tz_table_stale", "times", V("v1996", artifacts={"tz_offsets": "1996"}, env="p15"), "defect", "T1",
            True, "time-zone table not refreshed for codes with the UTC offset appended")
        add("storm.tz_prefix_only", "times", V("v1996", {"tz_prefix_only": True}, {"tz_offsets": "1996"}, env="p15"),
            "defect", "T1", True, "appended offset stripped and the old table used (Alaska and Guam codes lost)")
        add("storm.source_xwalk_stale", "sources", V("v1996", artifacts={"source_xwalk": "1996"}), "defect", "T1",
            True, "source crosswalk not refreshed for the title-case code list")
        add("storm.source_casefold", "sources", V("v1996", {"casefold": True}, {"source_xwalk": "1996"}), "defect",
            "T1", True, "new source codes upper-cased and looked up in the old list (renamed codes lost)")
        add("storm.fatal_type_unfiltered", "fatal_agg", V("v1996"), "defect", "T1", True,
            "indirect fatalities counted after they were added to the fatality file")
    if y >= 2007:
        add("storm.tor_scale_stale", "scale", V("v1996"), "defect", "T1", True,
            "tornado ratings still read on the Fujita scale (EF ratings unmapped)")
    if y >= 2016:
        add("storm.efu_as_zero", "scale", V("v1996", {**sc.p(), "efu_as_zero": True}), "defect", "T1", True,
            "unrated tornadoes ('EFU') coded as the lowest rating")
    if y >= 2021:
        add("storm.tz_daylight_stale", "times", V("v1996", artifacts={"tz_offsets": "2006"}, env="p15"), "defect",
            "T1", True, "time-zone table not refreshed for the daylight-time codes")
    # T2: library upgrades
    add("storm.adapter_env_p30", "event_adapter", V("v1996", env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the event adapter")
    add("storm.times_env_main", "times", V("v1996", tm.p(), tm.a()), "benign", "T2b", True,
        "pandas 2.2 upgrade of the time step (string dates still parse to nanoseconds)")
    add("storm.times_env_p30", "times", V("v1996", tm.p(), tm.a(), env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: duration via astype(int64) changes resolution", "pandas issue #65308")
    add("storm.clean_env_main", "clean", V("v1996"), "benign", "T2b", True, "pandas 2.2 upgrade of the cleaning step")
    add("storm.clean_env_p30", "clean", V("v1996", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: chained-assignment wind speed and hail size become no-ops",
        "pandas 3.0 release notes (copy-on-write)")
    add("storm.clean_modernised", "clean", V("v2024_loc"), "benign", "B", True, "chained assignment -> .where")
    add("storm.fatal_env_p30", "fatal_agg", V("v1996", sp["fatal_agg"].p(), env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the fatality aggregation")
    add("storm.loc_env_p30", "loc_agg", V("v1996", env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the location aggregation")
    add("storm.geo_env_p30", "geo", V("v1996", env="p30"), "benign", "T2b", True, "pandas 3 upgrade of the geo step")
    add("storm.join_nodedupe", "join", V("v1996", {"dedupe_right": False}), "benign", "B", True,
        "dedupe of the aggregate side removed (keys are unique)")
    add("storm.sources_env_p30", "sources", V("v1996", so.p(), so.a(), env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the source step")
    # T3: incident classes
    add("storm.duration_minutes", "times", V("v1996", {**tm.p(), "duration_minutes": True}, tm.a(), env="p15"),
        "defect", "T3", True, "event duration reported in minutes where hours are expected")
    add("storm.loc_by_episode", "loc_agg", V("v1996", {"by_episode": True}), "defect", "T3", True,
        "location points aggregated by episode instead of by event")
    add("storm.swap_lat_lon", "geo", V("v1996", {"swap_lat_lon": True}), "defect", "T3", True,
        "latitude and longitude swapped in the grid cell")
    add("storm.wind_kt_as_mph", "clean", V("v1996", {"wind_kt_as_mph": True}, env="p15"), "defect", "T3", True,
        "wind speed converted from knots to mph where knots are expected")
    add("storm.encoder_refit", "encode", V("v1996", {"refit": True}, sp["encode"].a()), "defect", "T3", True,
        "categorical codes re-fitted at serving time (training/serving skew)")
    add("storm.unknown_as_reference", "encode", V("v1996", {"unknown_as_reference": True}, sp["encode"].a()),
        "defect", "T3r", True, "unseen categories encoded as the reference category", "scikit-learn issue #34549")
    return out
