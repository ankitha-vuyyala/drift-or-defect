"""Smoke test of the local model through dod.llm (free): one short JSON answer per local model."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dod import llm  # noqa: E402

for model in ("qwen2.5:3b", "llama3.1:8b"):
    t = time.time()
    try:
        r = llm.chat("ollama", model, [{"role": "user", "content":
                     'Reply with JSON {"ok": true, "model": "<your name>"} and nothing else.'}], max_tokens=50)
        print(model, round(time.time() - t, 1), "s", r["usage"], r["text"][:200])
    except Exception as e:
        print(model, "ERROR", repr(e)[:300])
