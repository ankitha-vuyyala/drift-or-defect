"""Download raw files for the v2 held-out domains (public, no login). Idempotent; writes data/raw_v2/MANIFEST.json
with URL, size, SHA-256 and retrieval time for every file.

  divvy : Divvy (Chicago bike share) trip files, 2014 Q1 .. 2026-09 (quarterly/half-year archives, then monthly)
  hmda  : HMDA loan/application records. 2012-2017 legacy national 'all records, codes' files (CFPB historic data);
          2018-2025 per-state CSV from the FFIEC Data Browser API (states CO, OR, TN; actions 1 and 3)
  bts   : BTS Reporting Carrier On-Time Performance, months 1/4/7/10 of 2015-2026

usage: python v2/data/download_v2.py [divvy|hmda|bts ...]
"""
from __future__ import annotations
import hashlib, json, sys, time, urllib.error, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw_v2"
MAN = RAW / "MANIFEST.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
STATES = {"CO": "08", "OR": "41", "TN": "47"}

def targets(which):
    t = []
    if "divvy" in which:
        b = "https://divvy-tripdata.s3.amazonaws.com/"
        for n in ["Divvy_Stations_Trips_2014_Q1Q2", "Divvy_Stations_Trips_2014_Q3Q4", "Divvy_Trips_2015-Q1Q2",
                  "Divvy_Trips_2015_Q3Q4", "Divvy_Trips_2016_Q1Q2", "Divvy_Trips_2016_Q3Q4", "Divvy_Trips_2017_Q1Q2",
                  "Divvy_Trips_2017_Q3Q4", "Divvy_Trips_2018_Q1", "Divvy_Trips_2018_Q2", "Divvy_Trips_2018_Q3",
                  "Divvy_Trips_2018_Q4", "Divvy_Trips_2019_Q1", "Divvy_Trips_2019_Q2", "Divvy_Trips_2019_Q3",
                  "Divvy_Trips_2019_Q4", "Divvy_Trips_2020_Q1"]:
            t.append(("divvy", f"{n}.zip", b + f"{n}.zip"))
        for y in range(2020, 2027):
            for m in range(1, 13):
                if (y, m) < (2020, 4) or (y, m) > (2026, 9):
                    continue
                t.append(("divvy", f"{y}{m:02d}-divvy-tripdata.zip", b + f"{y}{m:02d}-divvy-tripdata.zip"))
    if "hmda" in which:
        for y in range(2012, 2018):
            n = f"hmda_{y}_nationwide_all-records_codes.zip"
            t.append(("hmda", n, "https://files.consumerfinance.gov/hmda-historic-loan-data/" + n))
        for y in range(2018, 2026):
            for s in STATES:
                t.append(("hmda", f"hmda_{y}_{s}_a13.csv",
                          f"https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?states={s}&years={y}&actions_taken=1,3"))
    if "bts" in which:
        for y in range(2015, 2027):
            for m in (1, 4, 7, 10):
                n = f"On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip"
                t.append(("bts", f"bts_{y}_{m:02d}.zip", "https://transtats.bts.gov/PREZIP/" + n))
    return t

def main():
    which = sys.argv[1:] or ["divvy", "hmda", "bts"]
    man = json.loads(MAN.read_text()) if MAN.exists() else {}
    for dom, name, url in targets(which):
        dst = RAW / dom / name
        key = f"{dom}/{name}"
        if dst.exists() and key in man and man[key].get("bytes") == dst.stat().st_size:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        for attempt in range(3):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, \
                        open(str(dst) + ".part", "wb") as f:
                    h = hashlib.sha256()
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b); h.update(b)
                Path(str(dst) + ".part").replace(dst)
                man[key] = {"url": url, "bytes": dst.stat().st_size, "sha256": h.hexdigest(),
                            "retrieved": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                print(f"{key} ok {dst.stat().st_size/1e6:.1f} MB {time.time()-t0:.0f}s", flush=True)
                break
            except urllib.error.HTTPError as e:
                print(f"{key} HTTP {e.code}", flush=True)
                if e.code in (403, 404):
                    man[key] = {"url": url, "error": f"HTTP {e.code}"}
                    break
                time.sleep(10)
            except Exception as e:
                print(f"{key} error {e!r} (attempt {attempt+1})", flush=True)
                time.sleep(10)
        MAN.write_text(json.dumps(man, indent=1, sort_keys=True))
    ok = sum(1 for v in man.values() if "sha256" in v)
    print(f"manifest: {ok} files, {sum(v.get('bytes', 0) for v in man.values())/1e9:.2f} GB")

if __name__ == "__main__":
    main()
