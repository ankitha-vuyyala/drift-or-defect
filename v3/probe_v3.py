"""Round-3 source probe (no keys, no paid calls): headers and sizes of candidate fresh domains.
Writes runs/v3_probe/probe.json; saves small samples under data/raw_v3/probe/."""
from __future__ import annotations
import io, json, re, time, urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "v3_probe"; OUT.mkdir(parents=True, exist_ok=True)
RAW = ROOT / "data" / "raw_v3" / "probe"; RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}
def get(u, t=300):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()
def heads(b):
    out = []
    try:
        z = zipfile.ZipFile(io.BytesIO(b))
        for n in z.namelist():
            if n.startswith("__MACOSX") or n.endswith("/"): continue
            with z.open(n) as f:
                out.append({"member": n, "size": z.getinfo(n).file_size, "lines": f.read(2500).decode("latin-1").splitlines()[:2]})
    except zipfile.BadZipFile:
        out.append({"lines": b[:2500].decode("latin-1").splitlines()[:3]})
    return out
res = {}
T = {}
for n in ["2016-capitalbikeshare-tripdata", "2017-capitalbikeshare-tripdata", "201801-capitalbikeshare-tripdata",
          "201912-capitalbikeshare-tripdata", "202003-capitalbikeshare-tripdata", "202004-capitalbikeshare-tripdata",
          "202005-capitalbikeshare-tripdata", "202012-capitalbikeshare-tripdata", "202301-capitalbikeshare-tripdata",
          "202406-capitalbikeshare-tripdata", "202609-capitalbikeshare-tripdata"]:
    T["cabi_" + n[:6]] = f"https://s3.amazonaws.com/capitalbikeshare-data/{n}.zip"
for y in (2009, 2010, 2015, 2019, 2020, 2022, 2023, 2024):
    T[f"fars_{y}"] = f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/National/FARS{y}NationalCSV.zip"
for ds in ("wrvz-psew", "ajtu-isnz", "m6dm-c72p", "n26f-ihde"):
    T[f"chi_{ds}"] = f"https://data.cityofchicago.org/resource/{ds}.csv?$limit=3"
    T[f"chi_{ds}_count"] = f"https://data.cityofchicago.org/resource/{ds}.json?$select=count(*)"
for y in (1995, 2005, 2013, 2014, 2020, 2025):
    T[f"landreg_{y}_head"] = f"http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{y}.csv"
for n in ("JC-201509", "JC-201701", "JC-201801", "JC-202012", "JC-202102", "JC-202406"):
    T["citi_" + n] = f"https://s3.amazonaws.com/tripdata/{n}-citibike-tripdata.csv.zip"
for k, u in T.items():
    t = time.time()
    try:
        if k.startswith("landreg"):
            r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120)
            b = r.read(3000)
            res[k] = {"len": r.headers.get("Content-Length"), "head": [{"lines": b.decode("latin-1").splitlines()[:3]}]}
            print(k, res[k]["len"], flush=True)
            continue
        b = get(u)
        if k.startswith("cabi") or k.startswith("fars") or k.startswith("citi"):
            (RAW / (k + ".zip")).write_bytes(b)
        res[k] = {"bytes": len(b), "secs": round(time.time() - t, 1), "head": heads(b)}
    except Exception as e:
        res[k] = {"error": repr(e)[:300]}
    print(k, {a: v for a, v in res[k].items() if a != "head"}, flush=True)
(OUT / "probe.json").write_text(json.dumps(res, indent=1))
print("done")
