"""Download the raw data for the benchmark (free, public sources) and record provenance.

Every file goes to data/raw/<source>/..., with URL, size, SHA-256 and download time recorded in
data/raw/MANIFEST.json. Existing complete files are skipped, so the job can be re-run safely.
A schema probe of every file is written to runs/data_probe/probe.json and probe.md.

usage: python code/data/download.py [--only acs|tlc|news|all] [--probe-only]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.json"
PROBE = ROOT / "runs" / "data_probe"
UA = {"User-Agent": "drift-or-defect-research/1.0 (academic benchmark construction)"}

ACS_STATES = ["ca", "tx", "ny"]
ACS_YEARS = list(range(2014, 2025))          # 2020 1-year exists only as experimental estimates
TLC_MONTHS = [f"{y}-{m:02d}" for y in range(2015, 2027) for m in (1, 4, 7, 10)] + ["2016-06", "2024-12", "2025-02"]
HF_NEWS = "heegyu/news-category-dataset"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"files": {}}


def save_manifest(m: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(m, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, MANIFEST)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path, man: dict, retries: int = 3) -> str:
    """Returns 'ok', 'skip', or 'missing:<status>'/'error:<msg>'."""
    rel = str(dest.relative_to(ROOT)).replace("\\", "/")
    if dest.exists() and rel in man["files"] and man["files"][rel].get("bytes") == dest.stat().st_size:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(retries):
        try:
            with requests.get(url, headers=UA, stream=True, timeout=60) as r:
                if r.status_code in (403, 404):
                    return f"missing:{r.status_code}"
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with tmp.open("wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                os.replace(tmp, dest)
            man["files"][rel] = {"url": url, "bytes": dest.stat().st_size, "sha256": sha256(dest),
                                 "downloaded": now()}
            save_manifest(man)
            return "ok"
        except Exception as e:
            err = repr(e)[:200]
            time.sleep(5 * (attempt + 1))
    return f"error:{err}"


def acs(man: dict) -> list:
    out = []
    for y in ACS_YEARS:
        base = (f"https://www2.census.gov/programs-surveys/acs/experimental/2020/data/pums/1-Year"
                if y == 2020 else f"https://www2.census.gov/programs-surveys/acs/data/pums/{y}/1-Year")
        for st in ACS_STATES:
            for kind in ("p", "h"):
                name = f"csv_{kind}{st}.zip"
                res = fetch(f"{base}/{name}", RAW / "acs" / str(y) / name, man)
                out.append(("acs", y, name, res))
                print("acs", y, name, res, flush=True)
    return out


def tlc(man: dict) -> list:
    out = []
    res = fetch("https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv",
                RAW / "tlc" / "taxi_zone_lookup.csv", man)
    out.append(("tlc", "lookup", res))
    for ym in sorted(set(TLC_MONTHS)):
        name = f"yellow_tripdata_{ym}.parquet"
        res = fetch(f"https://d37ci6vzurychx.cloudfront.net/trip-data/{name}", RAW / "tlc" / "yellow" / name, man)
        out.append(("tlc", ym, res))
        print("tlc", ym, res, flush=True)
    return out


def news(man: dict) -> list:
    out = []
    r = requests.get(f"https://huggingface.co/api/datasets/{HF_NEWS}", headers=UA, timeout=60)
    r.raise_for_status()
    info = r.json()
    (RAW / "news").mkdir(parents=True, exist_ok=True)
    (RAW / "news" / "hf_dataset_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    for s in info.get("siblings", []):
        fn = s["rfilename"]
        if fn.startswith(".") or fn.lower().endswith((".md", ".gitattributes")):
            continue
        res = fetch(f"https://huggingface.co/datasets/{HF_NEWS}/resolve/main/{fn}", RAW / "news" / fn, man)
        out.append(("news", fn, res))
        print("news", fn, res, flush=True)
    return out


def probe() -> None:
    import pyarrow.parquet as pq
    PROBE.mkdir(parents=True, exist_ok=True)
    res = {}
    for p in sorted(RAW.rglob("*")):
        if not p.is_file() or p.suffix in (".part", ".tmp") or p.name == "MANIFEST.json":
            continue
        rel = str(p.relative_to(RAW)).replace("\\", "/")
        try:
            if p.suffix == ".parquet":
                f = pq.ParquetFile(p)
                res[rel] = {"rows": f.metadata.num_rows,
                            "columns": {fld.name: str(fld.type) for fld in f.schema_arrow}}
            elif p.suffix == ".zip":
                with zipfile.ZipFile(p) as z:
                    csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
                    with z.open(csvs[0]) as fh:
                        header = io.TextIOWrapper(fh, encoding="latin-1").readline().strip()
                        first = io.TextIOWrapper(z.open(csvs[0]), encoding="latin-1")
                        first.readline()
                        row = first.readline().strip()
                    cols = header.split(",")
                    res[rel] = {"csv": csvs, "n_columns": len(cols), "columns": cols,
                                "first_row_head": dict(list(zip(cols, row.split(",")))[:6])}
            elif p.suffix in (".json", ".jsonl", ".csv"):
                with p.open(encoding="utf-8", errors="replace") as fh:
                    head = [fh.readline().strip()[:400] for _ in range(2)]
                res[rel] = {"bytes": p.stat().st_size, "head": head}
            else:
                res[rel] = {"bytes": p.stat().st_size}
        except Exception as e:
            res[rel] = {"error": repr(e)[:300]}
    (PROBE / "probe.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    # compact markdown: schema changes over time
    lines = ["# Data probe", "", f"{now()}", "", "## TLC yellow schemas by month", ""]
    prev = None
    for k in sorted(x for x in res if x.startswith("tlc/yellow/")):
        cols = res[k].get("columns", {})
        sig = json.dumps(cols, sort_keys=False)
        if sig != prev:
            lines.append(f"- **{k.split('_')[-1][:7]}** ({res[k].get('rows')} rows): "
                         + ", ".join(f"{c}:{t}" for c, t in cols.items()))
            prev = sig
        else:
            lines.append(f"- {k.split('_')[-1][:7]}: same schema ({res[k].get('rows')} rows)")
    lines += ["", "## ACS person-file columns by year (ca): added / removed vs previous year", ""]
    prevc = None
    for y in ACS_YEARS:
        k = f"acs/{y}/csv_pca.zip"
        if k not in res or "columns" not in res[k]:
            lines.append(f"- {y}: not available ({res.get(k, {}).get('error', 'missing')})")
            continue
        c = res[k]["columns"]
        if prevc is None:
            lines.append(f"- {y}: {len(c)} columns; SERIALNO example {res[k]['first_row_head'].get('SERIALNO')}")
        else:
            add, rem = sorted(set(c) - set(prevc)), sorted(set(prevc) - set(c))
            lines.append(f"- {y}: {len(c)} columns; SERIALNO example {res[k]['first_row_head'].get('SERIALNO')}; "
                         f"added {add[:40]}{'…' if len(add) > 40 else ''}; removed {rem[:40]}{'…' if len(rem) > 40 else ''}")
        prevc = c
    lines += ["", "## Other files", ""]
    lines += [f"- {k}: {json.dumps(v)[:300]}" for k, v in res.items() if not k.startswith(("tlc/yellow", "acs/"))]
    (PROBE / "probe.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all", choices=["acs", "tlc", "news", "all"])
    ap.add_argument("--probe-only", action="store_true")
    a = ap.parse_args()
    if not a.probe_only:
        man = load_manifest()
        results = []
        if a.only in ("news", "all"):
            results += news(man)
        if a.only in ("tlc", "all"):
            results += tlc(man)
        if a.only in ("acs", "all"):
            results += acs(man)
        bad = [r for r in results if not str(r[-1]).startswith(("ok", "skip"))]
        print(f"\n{len(results)} files: {len(results) - len(bad)} ok/skip, {len(bad)} missing/error")
        for b in bad:
            print("  ", b)
        total = sum(v["bytes"] for v in load_manifest()["files"].values())
        print(f"raw data on disk: {total / 1e9:.2f} GB")
    probe()


if __name__ == "__main__":
    sys.exit(main())
