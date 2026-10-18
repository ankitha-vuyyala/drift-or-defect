"""Round-4 source probe 2: Chicago traffic crashes (Socrata) row counts by year and columns. -> runs/v4_probe/probe_b.json"""
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs" / "v4_probe"; OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"}
def get(u, t=120):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t) as r:
        return r.read()
res = {}
for name, ds, dcol in (("crashes", "85ca-t3if", "crash_date"), ("people", "u6pd-qa9d", "crash_date"),
                       ("vehicles", "68nd-jvt3", "crash_date")):
    try:
        q = urllib.parse.urlencode({"$select": f"date_extract_y({dcol}) as y, count(*) as n", "$group": "y", "$order": "y"})
        res[name + "_counts"] = json.loads(get(f"https://data.cityofchicago.org/resource/{ds}.json?{q}"))
        res[name + "_sample"] = json.loads(get(f"https://data.cityofchicago.org/resource/{ds}.json?$limit=2"))
    except Exception as e:
        res[name + "_error"] = repr(e)[:300]
(OUT / "probe_b.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1)[:6000])
