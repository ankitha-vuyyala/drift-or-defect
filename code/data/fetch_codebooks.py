"""Fetch official ACS PUMS variable definitions (value labels) from the Census API for every year, as the
provenance for adapter specifications and the occupation crosswalk. Saves data/raw/acs_codebook/{year}/{VAR}.json.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
OUT = ROOT / "data" / "raw" / "acs_codebook"
VARS = ["RELP", "RELSHIPP", "JWTR", "JWTRNS", "WKW", "WKWN", "OCCP", "SCHL", "MAR", "COW", "SEX", "RAC1P",
        "TEN", "TYPE", "TYPEHUGQ", "ST", "STATE", "ADJINC", "PINCP", "WKHP", "AGEP", "POBP", "ESR", "CIT", "DIS"]
UA = {"User-Agent": "drift-or-defect-research/1.0"}


def main() -> None:
    summary = {}
    for y in range(2014, 2025):
        d = OUT / str(y)
        d.mkdir(parents=True, exist_ok=True)
        for v in VARS:
            p = d / f"{v}.json"
            if p.exists():
                summary[f"{y}/{v}"] = "skip"
                continue
            url = f"https://api.census.gov/data/{y}/acs/acs1/pums/variables/{v}.json"
            try:
                r = requests.get(url, headers=UA, timeout=30)
                if r.status_code == 200:
                    p.write_text(r.text, encoding="utf-8")
                    summary[f"{y}/{v}"] = "ok"
                else:
                    summary[f"{y}/{v}"] = f"http {r.status_code}"
            except Exception as e:
                summary[f"{y}/{v}"] = repr(e)[:100]
            time.sleep(0.2)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for y in range(2014, 2025):
        print(y, {v: summary.get(f"{y}/{v}") for v in VARS if summary.get(f"{y}/{v}") not in ("ok", "skip")})


if __name__ == "__main__":
    main()
