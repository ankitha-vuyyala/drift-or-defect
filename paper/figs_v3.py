"""Round-2 and round-3 figures from saved records. Writes paper/figures/v2_*.png|pdf and v3_*.png|pdf.

v2_correctness_by_domain   primary endpoint per method on the round-2 held-out domains
v3_correctness_by_domain   primary endpoint per method on the round-3 held-out domains
v3_false_blame_events      false blame of DoD, DoD-2 and DoD-3 on round-3 cases spanning a published change
usage: python paper/figs_v3.py runs/v2main runs/v3main
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "paper"))
from summarize import load, per_case  # noqa: E402
from figs import INK, INK2, NAMES, save, style  # noqa: E402

NAMES3 = {**NAMES, "dod_no_boundary": "DoD without boundary test", "dod2": "DoD-2", "dod3": "DoD-3", "dod3_no_latest": "DoD-3 without latest-change rule",
          "dod3_no_inv": "DoD-3 without invariants"}
BASE = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
        "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
        "dod_no_boundary", "dod", "dod2"]
ROUNDS = {2: ([("divvy", "Chicago bike share", "#2a78d6"), ("hmda", "Mortgages", "#eb6834"),
               ("bts", "Airlines", "#1baf7a")], BASE),
          3: ([("cabi", "Washington bike share", "#2a78d6"), ("fars", "Fatal crashes", "#eb6834"),
               ("landreg", "House sales", "#1baf7a")], BASE + ["dod3"])}


def correctness(run: Path, rnd: int) -> list:
    doms, order = ROUNDS[rnd]
    recs = [r for r in load(run) if r["case"]["domain"] in {d for d, _, _ in doms}]
    pcs = [per_case(r) for r in recs]
    methods = [m for m in order if any(m in p for p in pcs)]

    def mean(m, pred, metric="diag_correct"):
        rr = [p[m] for p in pcs if m in p and pred(p[m])]
        return (np.mean([float(r[metric]) for r in rr]) if rr else np.nan), len(rr)

    fig, ax = plt.subplots(figsize=(6.6, 0.36 * len(methods) + 1.0))
    y = np.arange(len(methods))[::-1]
    h = 0.26
    for k, (dom, label, col) in enumerate(doms):
        off = (1 - k) * h
        vals = [mean(m, lambda r, d=dom: r["has_cons"] and r["domain"] == d)[0] for m in methods]
        ax.barh(y + off, vals, height=h - 0.03, color=col, label=label)
        for yi, v in zip(y, vals):
            if v == v:
                ax.text(v + 0.01, yi + off, f"{v:.2f}", va="center", fontsize=6, color=INK)
    ax.set_yticks(y, [NAMES3[m] for m in methods], fontsize=7.5)
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Correct diagnosis on held-out cases with a consequential defect", fontsize=8, color=INK2)
    ax.legend(fontsize=7.5, frameon=False, loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=3)
    style(ax)
    save(fig, f"v{rnd}_correctness_by_domain")
    return recs


def false_blame(recs: list) -> None:
    doms, _ = ROUNDS[3]
    pcs = [per_case(r) for r in recs]
    ev = {r["case"]["case_id"]: bool(r["obs"].get("source_events")) for r in recs}
    ms = [m for m in ("dod", "dod2", "dod3") if any(m in p for p in pcs)]
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    x = np.arange(len(doms))
    w = 0.8 / max(1, len(ms))
    cols = ["#a3a29c", "#6f9fd8", "#2a78d6"]
    for k, m in enumerate(ms):
        vals = []
        for dom, _, _ in doms:
            rr = [p[m] for p in pcs if m in p and p[m]["domain"] == dom and ev[p[m]["case_id"]]]
            vals.append(np.mean([float(r["false_blame"]) for r in rr]) if rr else np.nan)
        pos = x + (k - (len(ms) - 1) / 2) * w
        ax.bar(pos, vals, width=w - 0.04, color=cols[k], label=NAMES3[m])
        for xi, v in zip(pos, vals):
            if v == v:
                ax.text(xi, v + 0.01, f"{v:.2f}", ha="center", fontsize=6.5, color=INK)
    ax.set_xticks(x, [label for _, label, _ in doms], fontsize=8)
    ax.set_ylabel("False-blame rate (cases spanning\na published change)", fontsize=8, color=INK2)
    ax.legend(fontsize=7.5, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    style(ax, "y")
    save(fig, "v3_false_blame_events")


if __name__ == "__main__":
    correctness(Path(sys.argv[1]), 2)
    if len(sys.argv) > 2:
        false_blame(correctness(Path(sys.argv[2]), 3))
    print("figures written")


def by_change(path: Path) -> None:
    """Correct diagnosis on consequential cases with and without a published change in their period range, per round."""
    import json
    res = json.loads(path.read_text())
    ms = [("bugdoc_shortcut", "Pipeline-instance debugging", "#a3a29c"),
          ("observational_attribution", "Observational attribution", "#d9a441"),
          ("llm_tools@luna", "LLM agent, tools (luna)", "#7a5cc4"),
          ("dod", "DoD", "#a9c4ea"), ("dod2", "DoD-2", "#6f9fd8"), ("dod3", "DoD-3", "#2a78d6")]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, key, title in zip(axes, ("no_change", "change"),
                              ("No published change in the period range", "Published change in the period range")):
        x = np.arange(3)
        present = [m for m in ms if any(m[0] in res[f"round{r}"][key] for r in (1, 2, 3))]
        w = 0.8 / len(present)
        for k, (m, label, col) in enumerate(present):
            vals = [res[f"round{r}"][key].get(m, {}).get("diag_correct", np.nan) for r in (1, 2, 3)]
            pos = x + (k - (len(present) - 1) / 2) * w
            ax.bar(pos, vals, width=w - 0.02, color=col, label=label)
        ns = [res[f"round{r}"][key]["dod"]["n"] for r in (1, 2, 3)]
        ax.set_xticks(x, [f"Round {r}\n(n={n})" for r, n in zip((1, 2, 3), ns)], fontsize=7.5)
        ax.set_title(title, fontsize=8, color=INK)
        ax.set_ylim(0, 1.05)
        style(ax, "y")
    axes[0].set_ylabel("Correct diagnosis\n(consequential cases)", fontsize=8, color=INK2)
    axes[0].legend(fontsize=6.8, frameon=False, loc="lower center", bbox_to_anchor=(1.05, 1.08), ncol=6)
    save(fig, "by_change")


if __name__ == "__main__" and len(sys.argv) > 3:
    by_change(Path(sys.argv[3]))
