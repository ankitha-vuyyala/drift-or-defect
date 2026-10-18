"""v2 source probe, round 2: HMDA with browser-like headers, FARS, BTS headers across years, Divvy quarterly
headers. Writes runs/v2_probe/probe2.json; saves files under data/raw_v2/probe/."""
from __future__ import annotations
import io, json, time, urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "v2_probe"; RAW = ROOT / "data" / "raw_v2" / "probe"; RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9"}
def get(u, t=300):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t)
def heads(b, name):
    out = []
    try:
        z = zipfile.ZipFile(io.BytesIO(b))
        for n in z.namelist():
            if n.startswith("__MACOSX") or n.endswith("/"):
                continue
            with z.open(n) as f:
                out.append({"member": n, "size": z.getinfo(n).file_size,
                            "lines": f.read(3000).decode("latin-1").splitlines()[:2]})
    except zipfile.BadZipFile:
        out.append({"lines": b[:3000].decode("latin-1").splitlines()[:2]})
    return out
res = {}
T = {
 "hmda_hist_2017_labels": "https://files.consumerfinance.gov/hmda-historic-loan-data/hmda_2017_nationwide_first-lien-owner-occupied-1-4-family-records_labels.zip",
 "hmda_api_vt_2018": "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?states=VT&years=2018&actions_taken=1,3",
 "hmda_api_vt_2018_nofilter": "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?states=VT&years=2018",
 "hmda_hist_page": "https://www.consumerfinance.gov/data-research/hmda/historic-data/",
 "fars_2019": "https://static.nhtsa.gov/nhtsa/downloads/FARS/2019/National/FARS2019NationalCSV.zip",
 "landreg_2019": "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-2019.csv",
}
for k in ["2015_1", "2020_4", "2024_6"]:
    T[f"bts_{k}"] = f"https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{k}.zip"
for q in ["Divvy_Stations_Trips_2013", "Divvy_Stations_Trips_2014_Q1Q2", "Divvy_Trips_2015-Q1Q2", "Divvy_Trips_2016_Q1Q2",
          "Divvy_Trips_2017_Q1Q2", "Divvy_Trips_2018_Q1", "Divvy_Trips_2018_Q2", "Divvy_Trips_2019_Q1", "Divvy_Trips_2019_Q2",
          "Divvy_Trips_2019_Q3"]:
    T[q] = f"https://divvy-tripdata.s3.amazonaws.com/{q}.zip"
for k, u in T.items():
    t = time.time()
    try:
        r = get(u)
        if k.startswith("hmda_hist_2017") or k.startswith("landreg"):
            b = r.read(200000); res[k] = {"status": r.status, "len": r.headers.get("Content-Length"),
                                          "type": r.headers.get("Content-Type"), "partial_head": b[:600].decode("latin-1")}
        else:
            b = r.read()
            (RAW / (k + (".zip" if b[:2] == b"PK" else ".bin"))).write_bytes(b)
            res[k] = {"status": r.status, "bytes": len(b), "secs": round(time.time() - t, 1), "head": heads(b, k)}
    except Exception as e:
        res[k] = {"error": repr(e)[:300]}
    print(k, {a: v for a, v in res[k].items() if a not in ("head", "partial_head")}, flush=True)
(OUT / "probe2.json").write_text(json.dumps(res, indent=1))
print("done")
