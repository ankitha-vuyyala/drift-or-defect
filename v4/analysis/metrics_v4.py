"""Round-4 metrics (three-verdict diagnosis). Per case and method:
  F  fix set (for DoD-4: verified defects), U  components flagged 'unverified' for review (empty for other methods)
  C  consequential defects, E  effective defects (ground truth)
  false_blame      F contains a component that is not an effective defect
  decided          U is empty (the method commits to a diagnosis)
  correct_decided  decided and C <= F <= E
  safe             F <= E and C <= F | U   (nothing wrongly fixed, nothing consequential left silent)
  silent_miss      some consequential defect is in neither F nor U
  review_load      |U|;  review_hits  |U & E|;  review_cons  |U & C|
"""
from __future__ import annotations


def unverified(d: dict) -> dict:
    return dict((d.get("notes") or {}).get("unverified") or {})


def case_metrics(rec: dict, m: str) -> dict | None:
    d = rec["methods"].get(m)
    if d is None:
        return None
    g = rec["gt"]
    C, E = set(g["consequential"]), set(g["defective"])
    F = set(d.get("fix") or [])
    U = set(unverified(d))
    return {
        "false_blame": not F <= E,
        "decided": not U,
        "diag_correct": C <= F <= E,
        "correct_decided": (not U) and C <= F <= E,
        "safe": F <= E and C <= (F | U),
        "silent_miss": bool(C - F - U),
        "missed": bool(C - F),
        "review_load": len(U), "review_hits": len(U & E), "review_cons": len(U & C),
        "has_cons": bool(C), "n_fix": len(F),
    }
