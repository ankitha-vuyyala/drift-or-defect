"""Chicago traffic-crash pipeline (round-4 held-out domain): City of Chicago Traffic Crashes (crashes, people,
vehicles; three source tables), crash years 2016-2025, a seeded sample of 60,000 crashes per year with all their
person and vehicle records.

Task: did the crash involve an injury or a tow? (The city's crash_type field; from the crash circumstances, the
road, the people and the vehicles involved, without any injury, damage or tow field.)

The tables are exported in one column layout for all years, so the dated changes are changes of codes and of
coverage (found from data/bronze/chicago/_profile.json):
  2017  citywide electronic crash reporting from September 2017 (earlier years cover some police districts): more
        reports per year, far more on-scene reports
  2019  revised crash report codes: intersection types added to trafficway_type ('FOUR WAY', 'T-INTERSECTION', ...),
        codes added to traffic_control_device, first_crash_type, weather_condition and the contributory causes;
        detailed restraint codes in safety_equipment ('CHILD RESTRAINT - FORWARD FACING', 'BOOSTER SEAT',
        'BICYCLE HELMET (PEDACYCLIST INVOLVED ONLY)', 'DOT COMPLIANT MOTORCYCLE HELMET', ...); vehicle codes added;
        the distribution of first_contact_point codes shifts for one year
  2020  first_contact_point corner and side codes ('FRONT-LEFT-CORNER', 'SIDE-LEFT-REAR', 'TOP', ...) replace
        'FRONT-LEFT', 'FRONT-RIGHT', 'REAR-LEFT', 'REAR-RIGHT', 'ROOF'; speeding cause codes retired
  2023  'CHILD RESTRAINT USED' and 'HELMET USED' retired
The 2020 pandemic changed traffic in the same year as the contact-point codes.
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
BRONZE = ROOT / "data" / "bronze" / "chicago"
ART = ROOT / "data" / "artifacts" / "chicago"

PERIODS = sorted(p.stem for p in (BRONZE / "crashes").glob("[0-9]*.parquet")) if BRONZE.exists() else []
CAT_FEATURES = ["tcd", "weather", "lighting", "first_crash_type", "road_group", "surface", "cell"]
NUM_FEATURES = ["hour", "dow", "month", "speed", "num_units", "report_delay_h", "hit_and_run", "intersection",
                "work_zone", "n_persons", "n_ped", "n_bike", "driver_age", "share_restrained", "n_vehicles",
                "share_front", "share_side", "share_rear", "n_heavy"]
FEATURES = NUM_FEATURES + CAT_FEATURES
LABEL = "y"
ID_COLS = ["crash_id"]
TASK = "binary"
INJURY_TOW = "INJURY AND / OR TOW DUE TO CRASH"

C = {}


def comp(name, inputs, doc=""):
    C[name] = Component(name, inputs, doc=doc)
    return C[name]


def _s(r: pd.DataFrame, c: str) -> pd.Series:
    return r[c].astype(str).str.strip()


def _num(r: pd.DataFrame, c: str) -> pd.Series:
    return pd.to_numeric(_s(r, c), errors="coerce")


# ----------------------------------------------------------------------------------------------- source adapters
crash_adapter = comp("crash_adapter", ["raw:crashes"], "published crash fields -> canonical schema")


@crash_adapter.variant("v2016")
def _ca(inp, p, a):
    r = inp["raw:crashes"]
    return pd.DataFrame({
        "crash_id": _s(r, "crash_record_id"),
        "crash_date": _s(r, "crash_date"), "notified": _s(r, "date_police_notified"),
        "speed": _num(r, "posted_speed_limit"),
        "tcd": _s(r, "traffic_control_device"), "weather": _s(r, "weather_condition"),
        "lighting": _s(r, "lighting_condition"), "first_crash_type": _s(r, "first_crash_type"),
        "trafficway": _s(r, "trafficway_type"), "surface": _s(r, "roadway_surface_cond"),
        "hit_and_run_i": _s(r, "hit_and_run_i"), "intersection_i": _s(r, "intersection_related_i"),
        "work_zone_i": _s(r, "work_zone_i"),
        "num_units": _num(r, "num_units"),
        "hour": _num(r, "crash_hour"), "dow": _num(r, "crash_day_of_week"), "month": _num(r, "crash_month"),
        "lat": _num(r, "latitude"), "lon": _num(r, "longitude"),
        "crash_type": _s(r, "crash_type"),
    })


person_adapter = comp("person_adapter", ["raw:people"], "published person records -> canonical schema")


@person_adapter.variant("v2016")
def _pa(inp, p, a):
    r = inp["raw:people"]
    return pd.DataFrame({"crash_id": _s(r, "crash_record_id"), "person_type": _s(r, "person_type"),
                         "age": _num(r, "age"), "safety": _s(r, "safety_equipment")})


vehicle_adapter = comp("vehicle_adapter", ["raw:vehicles"], "published vehicle records -> canonical schema")


@vehicle_adapter.variant("v2016")
def _va(inp, p, a):
    r = inp["raw:vehicles"]
    return pd.DataFrame({"crash_id": _s(r, "crash_record_id"), "vehicle_type": _s(r, "vehicle_type"),
                         "contact": _s(r, "first_contact_point")})


# ----------------------------------------------------------------------------------------------- crash branch
times = comp("times", ["crash_adapter"], "delay between the crash and the police notification")


@times.variant("v2016")
def _tm(inp, p, a):
    df = inp["crash_adapter"].copy()
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    c = pd.to_datetime(df["crash_date"], format=fmt, errors="coerce")
    n = pd.to_datetime(df["notified"], format=fmt, errors="coerce")
    ok = c.notna() & n.notna()
    # original idiom: delay from epoch nanoseconds (resolution-dependent across pandas versions)
    d = pd.Series(np.nan, index=df.index)
    d[ok] = ((n[ok].astype("int64") - c[ok].astype("int64")) / 3_600_000_000_000).astype("float64")
    if p.get("delay_minutes", False):           # incident class: delay reported in minutes, not hours
        d = d * 60.0
    df["report_delay_h"] = d
    return df.drop(columns=["crash_date", "notified"])


road = comp("road", ["times"], "trafficway type -> road group via the trafficway crosswalk")


@road.variant("v2016")
def _rd(inp, p, a):
    df = inp["times"].copy()
    g = df["trafficway"].map(a["trafficway_xwalk"])
    g = g.fillna("other" if p.get("unmapped_as_other", False) else "unknown")   # faulty fix: unmapped -> 'other'
    df["road_group"] = g
    return df.drop(columns=["trafficway"])


# ----------------------------------------------------------------------------------------------- side branches
person_agg = comp("person_agg", ["person_adapter"], "people per crash, driver age, restraint use")


@person_agg.variant("v2016")
def _pg(inp, p, a):
    pe = inp["person_adapter"].copy()
    grp = pe["safety"].map(a["restraint_xwalk"])
    known = grp.isin(["used", "not_used", "improper"])
    pe["_used"] = (grp == "used").astype("float64").where(known)
    age = pe["age"].where(pe["person_type"] == "DRIVER")
    if p.get("age_fill_zero", False):           # incident class: missing driver ages filled with 0 before averaging
        age = age.where(age.notna() | (pe["person_type"] != "DRIVER"), 0.0)
    pe["_age"] = age
    peds = ["PEDESTRIAN", "BICYCLE"] if p.get("ped_includes_bike", False) else ["PEDESTRIAN"]   # incident class
    pe["_ped"] = pe["person_type"].isin(peds).astype("float64")
    pe["_bike"] = (pe["person_type"] == "BICYCLE").astype("float64")
    g = pe.groupby("crash_id", as_index=False).agg(n_persons=("_ped", "size"), n_ped=("_ped", "sum"),
                                                   n_bike=("_bike", "sum"), driver_age=("_age", "mean"),
                                                   share_restrained=("_used", "mean"))
    g["n_persons"] = g["n_persons"].astype("float64")
    return g


vehicle_agg = comp("vehicle_agg", ["vehicle_adapter"], "vehicles per crash, first-contact points, heavy vehicles")

HEAVY = ("TRUCK", "BUS", "TRACTOR")


@vehicle_agg.variant("v2016")
def _vg(inp, p, a):
    ve = inp["vehicle_adapter"].copy()
    code = ve["contact"]
    if p.get("strip_corner", False):            # faulty fix: drop the '-CORNER' suffix, look up in the old list
        code = code.str.replace("-CORNER", "", regex=False)
    grp = code.map(a["impact_xwalk"]).fillna("unknown")
    for k in ("front", "side", "rear"):
        ve[f"_{k}"] = (grp == k).astype("float64")
    ve["_heavy"] = ve["vehicle_type"].str.contains("|".join(HEAVY), regex=True).astype("float64")
    g = ve.groupby("crash_id", as_index=False).agg(n_vehicles=("_heavy", "size"), share_front=("_front", "mean"),
                                                   share_side=("_side", "mean"), share_rear=("_rear", "mean"),
                                                   n_heavy=("_heavy", "sum"))
    g["n_vehicles"] = g["n_vehicles"].astype("float64")
    return g


join = comp("join", ["road", "person_agg", "vehicle_agg"], "left join of the crash branch and the aggregates")


@join.variant("v2016")
def _jn(inp, p, a):
    cr, pe, ve = inp["road"], inp["person_agg"], inp["vehicle_agg"]
    if p.get("dedupe_right", True):
        pe = pe.drop_duplicates("crash_id")
        ve = ve.drop_duplicates("crash_id")
    out = cr.merge(pe, on="crash_id", how="left").merge(ve, on="crash_id", how="left")
    for c in ("n_persons", "n_ped", "n_bike", "n_vehicles", "n_heavy"):
        out[c] = out[c].fillna(0.0)
    return out.reset_index(drop=True)


geo = comp("geo", ["join"], "0.05-degree grid cell of the crash location")


@geo.variant("v2016")
def _geo(inp, p, a):
    df = inp["join"].copy()
    lat, lon = df["lat"], df["lon"]
    if p.get("swap_lat_lon", False):             # incident class: latitude and longitude swapped
        lat, lon = lon, lat
    ok = lat.between(41.0, 43.0) & lon.between(-89.0, -87.0)
    cell = pd.Series("NA", index=df.index, dtype=object)
    cell[ok] = (np.floor(lat[ok] / 0.05).astype(int).astype(str) + "_"
                + np.floor(lon[ok] / 0.05).astype(int).astype(str))
    df["cell"] = cell
    return df.drop(columns=["lat", "lon"])


clean = comp("clean", ["geo"], "indicator flags, speed limit, label")


@clean.variant("v2016")
def _cl(inp, p, a):
    df = inp["geo"].copy()
    # pandas-1.x idiom: indicator flags filled in place (chained assignment; a no-op under copy-on-write)
    for src, dst in (("hit_and_run_i", "hit_and_run"), ("intersection_i", "intersection"),
                     ("work_zone_i", "work_zone")):
        df[dst] = 0.0
        df[dst][df[src] == "Y"] = 1.0
    df["speed"] = df["speed"].where(df["speed"].between(1, 70))
    df["y"] = (df["crash_type"] == INJURY_TOW).astype("int8")
    return df.drop(columns=["hit_and_run_i", "intersection_i", "work_zone_i", "crash_type"]).reset_index(drop=True)


@clean.variant("v2024_loc")
def _cl_loc(inp, p, a):
    df = inp["geo"].copy()
    for src, dst in (("hit_and_run_i", "hit_and_run"), ("intersection_i", "intersection"),
                     ("work_zone_i", "work_zone")):
        df[dst] = (df[src] == "Y").astype("float64")
    df["speed"] = df["speed"].where(df["speed"].between(1, 70))
    df["y"] = (df["crash_type"] == INJURY_TOW).astype("int8")
    return df.drop(columns=["hit_and_run_i", "intersection_i", "work_zone_i", "crash_type"]).reset_index(drop=True)


encode = comp("encode", ["clean"], "model matrix with categorical codes from the encoder artifact")


def fit_encoder(df: pd.DataFrame) -> dict:
    return {c: {k: i for i, k in enumerate(dict.fromkeys(df[c].astype(str).tolist()))} for c in CAT_FEATURES}


@encode.variant("v2016")
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


def _trafficway_group(code: str) -> str:
    u = code.upper()
    if u == "NOT DIVIDED":
        return "undivided"
    if u.startswith("DIVIDED"):
        return "divided"
    if u == "ONE-WAY":
        return "oneway"
    if "INTERSECTION" in u and "UNKNOWN" not in u or u in ("FOUR WAY", "FIVE POINT, OR MORE", "ROUNDABOUT"):
        return "intersection"
    if u in ("PARKING LOT", "DRIVEWAY", "ALLEY"):
        return "offroad"
    if u in ("RAMP", "TRAFFIC ROUTE", "CENTER TURN LANE"):
        return "special"
    return "other"


def _restraint_group(code: str) -> str:
    u = code.upper()
    if u in ("", "USAGE UNKNOWN"):
        return "unknown"
    if "IMPROPERLY" in u:
        return "improper"
    if "NOT USED" in u or u == "NONE PRESENT":
        return "not_used"
    if u in ("WHEELCHAIR", "STRETCHER"):
        return "other"
    return "used"


def _impact_group(code: str) -> str:
    u = code.upper()
    for k in ("FRONT", "SIDE", "REAR"):
        if u.startswith(k):
            return k.lower()
    if u in ("", "UNKNOWN", "NONE"):
        return "unknown"
    return "other"


def build_artifacts() -> dict:
    """Crosswalks from published codes to groups, one per code list (codes read from the bronze profiles):
      trafficway_xwalk '2016' (codes published 2016-2018), '2019' (+ codes published from 2019);
      restraint_xwalk  '2016' (codes published 2016-2018), '2019' (+ codes published from 2019);
      impact_xwalk     '2016' (codes published 2016-2017), '2020' (+ codes published from 2020)."""
    prof = json.loads((BRONZE / "_profile.json").read_text(encoding="utf-8"))

    def codes(tab, col, y0, y1):
        out = set()
        for y, pr in prof[tab].items():
            if y0 <= int(y) <= y1:
                out |= set(pr["codes"].get(col, {}))
        return out
    res = {}
    for name, tab, col, rule, vints in (
            ("trafficway_xwalk", "crashes", "trafficway_type", _trafficway_group, (("2016", 2016, 2018),
                                                                                   ("2019", 2016, 2025))),
            ("restraint_xwalk", "people", "safety_equipment", _restraint_group, (("2016", 2016, 2018),
                                                                                 ("2019", 2016, 2025))),
            ("impact_xwalk", "vehicles", "first_contact_point", _impact_group, (("2016", 2016, 2017),
                                                                                ("2020", 2016, 2025)))):
        for v, y0, y1 in vints:
            xw = {c: rule(c) for c in sorted(codes(tab, col, y0, y1))}
            save_artifact(name, v, xw)
            res[f"{name}/{v}"] = len(xw)
    return res


PIPELINE = Pipeline(domain="chicago", components=C, output="encode", raw_tables=["crashes", "people", "vehicles"],
                    load_raw=load_raw, load_artifact=load_artifact)
V = Version.make


# ----------------------------------------------------------------------------------------------- reference and spec
def reference_state(encoder_id: str, p0: str = "2018") -> dict:
    """The pipeline as deployed when the reference model was trained (times and clean in a pandas-1.5
    environment), adapted to every published change up to p0."""
    y = int(p0)
    return {
        "crash_adapter": V("v2016"),
        "person_adapter": V("v2016"),
        "vehicle_adapter": V("v2016"),
        "times": V("v2016", env="p15"),
        "road": V("v2016", artifacts={"trafficway_xwalk": "2019" if y >= 2019 else "2016"}),
        "person_agg": V("v2016", artifacts={"restraint_xwalk": "2019" if y >= 2019 else "2016"}),
        "vehicle_agg": V("v2016", artifacts={"impact_xwalk": "2020" if y >= 2020 else "2016"}),
        "join": V("v2016"),
        "geo": V("v2016"),
        "clean": V("v2016", env="p15"),
        "encode": V("v2016", artifacts={"encoder": encoder_id}),
    }


def spec_state(period: str, encoder_id: str) -> dict:
    return reference_state(encoder_id, period)


EVENTS = [
    ("2017", "crashes", "citywide electronic crash reporting from September 2017 (more reports, more on-scene "
     "reports)", ["crash_record_id", "report_type"]),
    ("2019", "crashes", "revised report codes: intersection types in trafficway_type; codes added to "
     "traffic_control_device, first_crash_type, weather_condition and contributory causes",
     ["trafficway_type", "traffic_control_device", "first_crash_type", "weather_condition",
      "prim_contributory_cause", "sec_contributory_cause"]),
    ("2019", "people", "detailed restraint codes in safety_equipment; pedestrian location and physical condition "
     "codes added", ["safety_equipment", "pedpedal_location", "physical_condition"]),
    ("2019", "vehicles", "first_contact_point code distribution shifts; vehicle type, maneuver and unit type codes "
     "added", ["first_contact_point", "vehicle_type", "maneuver", "unit_type"]),
    ("2020", "vehicles", "first_contact_point corner and side codes replace FRONT-LEFT, FRONT-RIGHT, REAR-LEFT, "
     "REAR-RIGHT and ROOF", ["first_contact_point"]),
    ("2020", "crashes", "speeding cause codes retired", ["prim_contributory_cause", "sec_contributory_cause"]),
    ("2023", "people", "'CHILD RESTRAINT USED' and 'HELMET USED' retired", ["safety_equipment"]),
]


def source_events(period_from: str, period_to: str) -> list[dict]:
    return [{"period": w, "table": t, "change": what, "columns": cols}
            for w, t, what, cols in EVENTS if period_from < w <= period_to]


# ----------------------------------------------------------------------------------------------- lineage and catalog
LINEAGE = {
    "hour": ["crash_adapter"], "dow": ["crash_adapter"], "month": ["crash_adapter"],
    "speed": ["crash_adapter", "clean"], "num_units": ["crash_adapter"],
    "report_delay_h": ["crash_adapter", "times"],
    "hit_and_run": ["crash_adapter", "clean"], "intersection": ["crash_adapter", "clean"],
    "work_zone": ["crash_adapter", "clean"],
    "n_persons": ["person_adapter", "person_agg", "join"], "n_ped": ["person_adapter", "person_agg", "join"],
    "n_bike": ["person_adapter", "person_agg", "join"], "driver_age": ["person_adapter", "person_agg", "join"],
    "share_restrained": ["person_adapter", "person_agg", "join"],
    "n_vehicles": ["vehicle_adapter", "vehicle_agg", "join"], "share_front": ["vehicle_adapter", "vehicle_agg", "join"],
    "share_side": ["vehicle_adapter", "vehicle_agg", "join"], "share_rear": ["vehicle_adapter", "vehicle_agg", "join"],
    "n_heavy": ["vehicle_adapter", "vehicle_agg", "join"],
    "tcd": ["crash_adapter", "encode"], "weather": ["crash_adapter", "encode"],
    "lighting": ["crash_adapter", "encode"], "first_crash_type": ["crash_adapter", "encode"],
    "road_group": ["crash_adapter", "road", "encode"], "surface": ["crash_adapter", "encode"],
    "cell": ["crash_adapter", "geo", "encode"], "y": ["crash_adapter", "clean"],
}
SOURCE_READERS = {"crashes": ["crash_adapter"], "people": ["person_adapter"], "vehicles": ["vehicle_adapter"]}
_C_ALL = ["crash_record_id", "crash_date", "date_police_notified", "posted_speed_limit", "traffic_control_device",
          "weather_condition", "lighting_condition", "first_crash_type", "trafficway_type", "roadway_surface_cond",
          "hit_and_run_i", "intersection_related_i", "work_zone_i", "num_units", "crash_hour", "crash_day_of_week",
          "crash_month", "latitude", "longitude", "crash_type"]
_P_ALL = ["crash_record_id", "person_type", "age", "safety_equipment"]
_V_ALL = ["crash_record_id", "vehicle_type", "first_contact_point"]
RAW_COLUMNS = {
    "crash_adapter": {"crashes": _C_ALL},
    "person_adapter": {"people": _P_ALL},
    "vehicle_adapter": {"vehicles": _V_ALL},
    "times": {"crashes": ["crash_date", "date_police_notified"]},
    "road": {"crashes": ["trafficway_type"]},
    "person_agg": {"people": _P_ALL},
    "vehicle_agg": {"vehicles": _V_ALL},
    "join": {"crashes": ["crash_record_id"], "people": ["crash_record_id"], "vehicles": ["crash_record_id"]},
    "geo": {"crashes": ["latitude", "longitude"]},
    "clean": {"crashes": ["hit_and_run_i", "intersection_related_i", "work_zone_i", "posted_speed_limit",
                          "crash_type"]},
    "encode": {"crashes": _C_ALL, "people": _P_ALL, "vehicles": _V_ALL},
}
COLUMN_SOURCES = {
    "crash_adapter": {"crash_id": ["crash_record_id"], "crash_date": ["crash_date"],
                      "notified": ["date_police_notified"], "speed": ["posted_speed_limit"],
                      "tcd": ["traffic_control_device"], "weather": ["weather_condition"],
                      "lighting": ["lighting_condition"], "first_crash_type": ["first_crash_type"],
                      "trafficway": ["trafficway_type"], "surface": ["roadway_surface_cond"],
                      "hit_and_run_i": ["hit_and_run_i"], "intersection_i": ["intersection_related_i"],
                      "work_zone_i": ["work_zone_i"], "num_units": ["num_units"], "hour": ["crash_hour"],
                      "dow": ["crash_day_of_week"], "month": ["crash_month"], "lat": ["latitude"],
                      "lon": ["longitude"], "crash_type": ["crash_type"]},
    "times": {"report_delay_h": ["crash_date", "notified"]},
    "road": {"road_group": ["trafficway"]},
    "person_agg": {"n_persons": ["person_type"], "n_ped": ["person_type"], "n_bike": ["person_type"],
                   "driver_age": ["age", "person_type"], "share_restrained": ["safety"]},
    "vehicle_agg": {"n_vehicles": ["contact"], "share_front": ["contact"], "share_side": ["contact"],
                    "share_rear": ["contact"], "n_heavy": ["vehicle_type"]},
    "geo": {"cell": ["lat", "lon"]},
    "clean": {"hit_and_run": ["hit_and_run_i"], "intersection": ["intersection_i"], "work_zone": ["work_zone_i"],
              "y": ["crash_type"]},
}


def catalog(period: str, encoder_id: str) -> list[dict]:
    y = int(period)
    sp = spec_state(period, encoder_id)
    out = []

    def add(cid, comp_, version, kind, tier, silent_hint, note, source=""):
        out.append({"id": cid, "component": comp_, "version": version, "kind": kind, "tier": tier,
                    "silent_hint": silent_hint, "note": note, "source": source})
    # T1: source-coupled defects (stale or faulty adaptations to the published code changes)
    if y >= 2019:
        add("chicago.trafficway_xwalk_stale", "road", V("v2016", artifacts={"trafficway_xwalk": "2016"}), "defect",
            "T1", True, "trafficway crosswalk not refreshed for the intersection codes")
        add("chicago.trafficway_unmapped_other", "road",
            V("v2016", {"unmapped_as_other": True}, {"trafficway_xwalk": "2016"}), "defect", "T1", True,
            "new trafficway codes sent to the 'other' group instead of being mapped")
        add("chicago.restraint_xwalk_stale", "person_agg", V("v2016", artifacts={"restraint_xwalk": "2016"}),
            "defect", "T1", True, "restraint crosswalk not refreshed for the detailed restraint codes")
    if y >= 2020:
        add("chicago.impact_xwalk_stale", "vehicle_agg", V("v2016", artifacts={"impact_xwalk": "2016"}), "defect",
            "T1", True, "contact-point crosswalk not refreshed for the corner and side codes")
        add("chicago.impact_strip_corner", "vehicle_agg",
            V("v2016", {"strip_corner": True}, {"impact_xwalk": "2016"}), "defect", "T1", True,
            "'-CORNER' suffix stripped and the old crosswalk used (side-front/rear and top codes lost)")
    pa, va, rd = sp["person_agg"], sp["vehicle_agg"], sp["road"]
    # T2: library upgrades
    add("chicago.adapter_env_p30", "crash_adapter", V("v2016", env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the crash adapter")
    add("chicago.times_env_main", "times", V("v2016"), "benign", "T2b", True,
        "pandas 2.2 upgrade of the time step (string dates still parse to nanoseconds)")
    add("chicago.times_env_p30", "times", V("v2016", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: delay via astype(int64) changes resolution", "pandas issue #65308")
    add("chicago.clean_env_main", "clean", V("v2016"), "benign", "T2b", True, "pandas 2.2 upgrade of the cleaning step")
    add("chicago.clean_env_p30", "clean", V("v2016", env="p30"), "defect", "T2", True,
        "pandas 3 upgrade: chained-assignment indicator flags become no-ops", "pandas 3.0 release notes (copy-on-write)")
    add("chicago.clean_modernised", "clean", V("v2024_loc"), "benign", "B", True, "chained assignment -> vectorised")
    add("chicago.person_env_p30", "person_agg", V("v2016", pa.p(), pa.a(), env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the person aggregation")
    add("chicago.vehicle_env_p30", "vehicle_agg", V("v2016", va.p(), va.a(), env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the vehicle aggregation")
    add("chicago.road_env_p30", "road", V("v2016", rd.p(), rd.a(), env="p30"), "benign", "T2b", True,
        "pandas 3 upgrade of the road step")
    add("chicago.geo_env_p30", "geo", V("v2016", env="p30"), "benign", "T2b", True, "pandas 3 upgrade of the geo step")
    add("chicago.join_nodedupe", "join", V("v2016", {"dedupe_right": False}), "benign", "B", True,
        "dedupe of the aggregate side removed (keys are unique)")
    # T3: incident classes
    add("chicago.delay_minutes", "times", V("v2016", {"delay_minutes": True}, env="p15"), "defect", "T3", True,
        "notification delay reported in minutes where hours are expected")
    add("chicago.age_fill_zero", "person_agg", V("v2016", {"age_fill_zero": True}, pa.a()), "defect", "T3", True,
        "missing driver ages filled with 0 before averaging")
    add("chicago.ped_includes_bike", "person_agg", V("v2016", {"ped_includes_bike": True}, pa.a()), "defect", "T3",
        True, "cyclists counted as pedestrians")
    add("chicago.swap_lat_lon", "geo", V("v2016", {"swap_lat_lon": True}), "defect", "T3", True,
        "latitude and longitude swapped in the grid cell")
    add("chicago.encoder_refit", "encode", V("v2016", {"refit": True}, sp["encode"].a()), "defect", "T3", True,
        "categorical codes re-fitted at serving time (training/serving skew)")
    add("chicago.unknown_as_reference", "encode", V("v2016", {"unknown_as_reference": True}, sp["encode"].a()),
        "defect", "T3r", True, "unseen categories encoded as the reference category", "scikit-learn issue #34549")
    return out
