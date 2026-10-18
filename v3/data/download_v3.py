"""Download raw files for the round-3 held-out domains (public, no login). Idempotent; writes
data/raw_v3/MANIFEST.json with URL, size, SHA-256 and retrieval time.

  cabi     : Capital Bikeshare (Washington DC) trip files: yearly 2014-2017, monthly 2018-01 .. 2026-09
  fars     : NHTSA FARS national CSV files, 2010-2024
  landreg  : HM Land Registry Price Paid Data, yearly files 2008-2025

usage: python v3/data/download_v3.py [cabi|fars|landreg ...]
"""
from __future__ import annotations
import hashlib, json, sys, time, urllib.error, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw_v3"
MAN = RAW / "MANIFEST.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36", "Accept": "*/*"}


def targets(which):
    t = []
    if "cabi" in which:
        b = "https://s3.amazonaws.com/capitalbikeshare-data/"
        for y in range(2014, 2018):
            t.append(("cabi", f"{y}-capitalbikeshare-tripdata.zip", b + f"{y}-capitalbikeshare-tripdata.zip"))
        for y in range(2018, 2027):
            for m in range(1, 13):
                if (y, m) > (2026, 9):
                    continue
                n = f"{y}{m:02d}-capitalbikeshare-tripdata.zip"
                t.append(("cabi", n, b + n))
    if "fars" in which:
        for y in range(2010, 2025):
            t.append(("fars", f"FARS{y}NationalCSV.zip",
                      f"https://static.nhtsa.gov/nhtsa/downloads/FARS/{y}/National/FARS{y}NationalCSV.zip"))
    if "landreg" in which:
        for y in range(2008, 2026):
            t.append(("landreg", f"pp-{y}.csv",
                      f"http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{y}.csv"))
    return t


def main():
    which = sys.argv[1:] or ["cabi", "fars", "landreg"]
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
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=900) as r, \
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
    print(f"manifest: {sum(1 for v in man.values() if 'sha256' in v)} files, "
          f"{sum(v.get('bytes', 0) for v in man.values())/1e9:.2f} GB")


if __name__ == "__main__":
    main()
