"""List the model ids available to the configured OpenAI key (free endpoint; no tokens are used). Prints ids only."""
import json
import os
from pathlib import Path

import requests

ROOT = Path(os.environ.get("DOD_PROJECT_ROOT", Path(__file__).resolve().parents[2]))
r = requests.get("https://api.openai.com/v1/models",
                 headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}, timeout=60)
print("status", r.status_code)
ids = sorted(m["id"] for m in r.json().get("data", [])) if r.status_code == 200 else []
keep = [i for i in ids if i.startswith(("gpt-5", "gpt-4.1", "gpt-4o", "o3", "o4"))]
out = ROOT / "runs" / "inventory" / "openai_models.json"
out.write_text(json.dumps(ids, indent=1))
print(len(ids), "models;", "chat-capable candidates:")
print("\n".join(keep))
