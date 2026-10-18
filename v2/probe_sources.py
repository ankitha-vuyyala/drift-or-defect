"""v2 source probe: reachability, sizes and headers of candidate new-domain sources. No keys, no paid calls.
Writes runs/v2_probe/probe.json and saves small sample files under data/raw_v2/probe/."""
from __future__ import annotations
import io, json, re, sys, time, urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "v2_probe"; OUT.mkdir(parents=True, exist_ok=True)
RAW = ROOT / "data" / "raw_v2" / "probe"; RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research data probe)"}
HEAD_ONLY = [
 "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2015_1.zip",
 "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_6.zip",
 "https://transtats.bts.gov/PREZIP/On_Time_Marketing_Carrier_On_Time_Performance_Beginning_January_2018_2019_1.zip",
 "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2017_nationwide_first-lien-owner-occupied-1-4-family-records_labels.zip",
 "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2017_nationwide_all-records_codes.zip",
 "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2017_vt_all-records_labels.zip",
 "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2017_vt_all-records_codes.zip",
 "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2015_vt_all-records_labels.zip",
]
FETCH = {  # small samples, saved to disk
 "bts_2017_12.zip": "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2017_12.zip",
 "bts_2018_1.zip": "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2018_1.zip",
 "divvy_2019_q4.zip": "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2019_Q4.zip",
 "divvy_2020_q1.zip": "https://divvy-tripdata.s3.amazonaws.com/Divvy_Trips_2020_Q1.zip",
 "divvy_202012.zip": "https://divvy-tripdata.s3.amazonaws.com/202012-divvy-tripdata.zip",
 "hmda_vt_2018.csv": "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?states=VT&years=2018&actions_taken=1,3",
 "hmda_vt_2022.csv": "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?states=VT&years=2022&actions_taken=1,3",
 "jc_citibike_202101.zip": "https://s3.amazonaws.com/tripdata/JC-202101-citibike-tripdata.csv.zip",
 "jc_citibike_202102.zip": "https://s3.amazonaws.com/tripdata/JC-202102-citibike-tripdata.csv.zip",
}
LISTINGS = {"divvy": "https://divvy-tripdata.s3.amazonaws.com/", "citibike": "https://s3.amazonaws.com/tripdata/",
            "cabi": "https://s3.amazonaws.com/capitalbikeshare-data/"}

def req(url, method="GET", timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA, method=method), timeout=timeout)

def head(b: bytes, name: str):
    if name.endswith(".zip"):
        z = zipfile.ZipFile(io.BytesIO(b))
        info = []
        for n in z.namelist()[:6]:
            with z.open(n) as f:
                lines = f.read(4000).decode("latin-1").splitlines()[:3]
            info.append({"member": n, "size": z.getinfo(n).file_size, "lines": lines})
        return info
    return [{"lines": b[:4000].decode("latin-1").splitlines()[:3]}]

res = {"head": {}, "fetch": {}, "listing": {}}
for u in HEAD_ONLY:
    try:
        r = req(u, "HEAD", 60); res["head"][u] = {"status": r.status, "len": r.headers.get("Content-Length")}
    except Exception as e:
        res["head"][u] = {"error": repr(e)[:200]}
    print("HEAD", u.rsplit("/", 1)[-1], res["head"][u], flush=True)
for name, u in FETCH.items():
    t = time.time()
    try:
        b = req(u, timeout=600).read(); (RAW / name).write_bytes(b)
        res["fetch"][name] = {"bytes": len(b), "secs": round(time.time() - t, 1), "head": head(b, name)}
    except Exception as e:
        res["fetch"][name] = {"error": repr(e)[:300]}
    print("GET", name, {k: v for k, v in res["fetch"][name].items() if k != "head"}, flush=True)
for k, u in LISTINGS.items():
    try:
        x = req(u, timeout=120).read().decode()
        keys = re.findall(r"<Key>([^<]+)</Key><LastModified>([^<]+)</LastModified>.*?<Size>(\d+)</Size>", x)
        res["listing"][k] = [{"key": a, "modified": b, "size": int(c)} for a, b, c in keys]
        print("LIST", k, len(keys), "truncated" if "<IsTruncated>true" in x else "", flush=True)
    except Exception as e:
        res["listing"][k] = {"error": repr(e)[:200]}; print("LIST", k, "error", e)
(OUT / "probe.json").write_text(json.dumps(res, indent=1))
print("done")
