"""Download raw files for the round-4 held-out domains (public, no login). Idempotent; writes
data/raw_v4/MANIFEST.json with URL, size, SHA-256 and retrieval time.

  storm    : NOAA NCEI Storm Events Database, yearly CSV files of event details, fatalities and locations,
             1996-2025 (latest published version of each file)
  chicago  : City of Chicago Traffic Crashes (crashes, people, vehicles), yearly CSV exports 2016-2025 from the
             Socrata API (data.cityofchicago.org)

usage: python v4/data/download_v4.py [storm|chicago ...]
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw_v4"
MAN = RAW / "MANIFEST.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36", "Accept": "*/*"}
STORM = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
CHI = {"crashes": "85ca-t3if", "people": "u6pd-qa9d", "vehicles": "68nd-jvt3"}


def get(url: str, timeout: int = 900) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def targets(which):
    t = []
    if "storm" in which:
        html = get(STORM, 120).decode("latin-1")
        latest = {}
        for f in set(re.findall(r'href="(StormEvents_[^"]+\.csv\.gz)"', html)):
            m = re.match(r"StormEvents_(details|fatalities|locations)-ftp_v1\.0_d(\d{4})_c(\d{8})\.csv\.gz", f)
            if m and 1996 <= int(m.group(2)) <= 2025:
                k = (m.group(1), m.group(2))
                if k not in latest or f > latest[k]:
                    latest[k] = f
        for (tab, y), f in sorted(latest.items()):
            t.append(("storm", f"{tab}_{y}.csv.gz", STORM + f))
    if "chicago" in which:
        for tab, ds in CHI.items():
            for y in range(2016, 2026):
                q = urllib.parse.urlencode({
                    "$where": f"crash_date between '{y}-01-01T00:00:00' and '{y}-12-31T23:59:59'",
                    "$limit": 5_000_000, "$order": ":id"})
                t.append(("chicago", f"{tab}_{y}.csv", f"https://data.cityofchicago.org/resource/{ds}.csv?{q}"))
    return t


def main():
    which = sys.argv[1:] or ["storm", "chicago"]
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
                h = hashlib.sha256()
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=1800) as r, \
                        open(str(dst) + ".part", "wb") as f:
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        h.update(b)
                        f.write(b)
                Path(str(dst) + ".part").replace(dst)
                man[key] = {"url": url, "bytes": dst.stat().st_size, "sha256": h.hexdigest(),
                            "retrieved": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                MAN.write_text(json.dumps(man, indent=1, sort_keys=True), encoding="utf-8")
                print(f"{key}: {man[key]['bytes']:,} bytes in {time.time() - t0:.0f}s", flush=True)
                break
            except Exception as e:  # noqa: BLE001
                print(f"{key}: attempt {attempt + 1} failed: {e!r}", flush=True)
                time.sleep(10 * (attempt + 1))


if __name__ == "__main__":
    main()
