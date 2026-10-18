"""Round-4 source probe (no keys, no paid calls): file listings and headers of candidate fresh domains.
Writes runs/v4_probe/probe.json."""
from __future__ import annotations
import gzip, io, json, re, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "v4_probe"; OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"}
def get(u, t=120, n=None):
    req = urllib.request.Request(u, headers=UA)
    with urllib.request.urlopen(req, timeout=t) as r:
        return r.read(n) if n else r.read()
res = {}
# NOAA Storm Events
try:
    base = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    html = get(base).decode("latin-1")
    files = sorted(set(re.findall(r'href="(StormEvents_[^"]+\.csv\.gz)"', html)))
    res["storm_files"] = files
    heads = {}
    for f in files:
        m = re.match(r"StormEvents_(details|fatalities|locations)-ftp_v1\.0_d(\d{4})_c(\d{8})", f)
        if m and m.group(2) in ("1996", "2000", "2006", "2007", "2010", "2016", "2024", "2025"):
            b = get(base + f)
            txt = gzip.decompress(b).decode("latin-1").splitlines()
            heads[f] = {"bytes": len(b), "rows": len(txt) - 1, "head": txt[:3]}
    res["storm_heads"] = heads
except Exception as e:
    res["storm_error"] = repr(e)
# DfT STATS19
try:
    base = "https://data.dft.gov.uk/road-accidents-safety-data/"
    out = {}
    for y in (2005, 2010, 2015, 2016, 2019, 2020, 2021, 2023, 2024):
        for t in ("collision", "vehicle", "casualty"):
            u = f"{base}dft-road-casualty-statistics-{t}-{y}.csv"
            try:
                b = get(u, n=3000)
                out[f"{t}-{y}"] = b.decode("latin-1").splitlines()[:2]
            except Exception as e:
                out[f"{t}-{y}"] = repr(e)[:120]
    res["stats19"] = out
except Exception as e:
    res["stats19_error"] = repr(e)
(OUT / "probe.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: (v if k != "storm_files" else v[-12:]) for k, v in res.items()}, indent=1)[:20000])
