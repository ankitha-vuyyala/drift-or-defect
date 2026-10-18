"""Move the storm records that are not in the round-4 storm subsample (see v4/run_cases_subsample.py and
v4/EXECUTION_NOTES_V4.md) from runs/v4main/storm.jsonl to runs/v4main_extra/storm.jsonl. Run once, after the
storm subsample is complete and before the storm LLM baselines. Prints the counts.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_cases_subsample import keep  # noqa: E402

src = ROOT / "runs" / "v4main" / "storm.jsonl"
extra = ROOT / "runs" / "v4main_extra" / "storm.jsonl"
lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
ins = [l for l in lines if keep(json.loads(l)["case"]["case_id"])]
out = [l for l in lines if not keep(json.loads(l)["case"]["case_id"])]
extra.parent.mkdir(parents=True, exist_ok=True)
if out:
    with extra.open("a", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
src.write_text("\n".join(ins) + "\n", encoding="utf-8")
print(f"kept {len(ins)} subsample records, moved {len(out)} to {extra}")
