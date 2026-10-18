"""Paper figures from saved case records (static, print-ready PNG + PDF).

usage: python analysis/figures.py runs/<name> [--split test] [--out paper/figures]
Fig. 1  action correctness by method, in three panels: silent consequential defects, loud consequential defects,
        no consequential defect (drift, benign changes, nothing).
Fig. 2  compute cost vs correctness on cases with a consequential defect (one point per method).
Fig. 3  what retraining hides: post-action accuracy now vs after a later repair, for cases with a consequential
        defect (retrain-on-alarm vs the method).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize import load, per_case  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
HIGHLIGHT, OTHER = "#2a78d6", "#a3a29c"
LABELS = {"retrain_on_alarm": "Retrain on alarm", "validation_first": "Validation first",
          "observational_attribution": "Observational attribution", "full_rollback": "Full rollback",
          "bisect": "Bisection", "bugdoc_shortcut": "Pipeline-instance debugging", "dod": "DoD (ours)",
          "dod_no_boundary": "DoD w/o boundary test", "dod_b1": "DoD, budget 1 run",
          "dod_b1_no_prior": "DoD, budget 1 run, no prior", "dod_b1_uniform": "DoD, budget 1 run, topo order",
          "llm_report@local": "LLM agent (report, local)", "llm_tools@local": "LLM agent (tools, local)"}
MAIN = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
        "bugdoc_shortcut", "dod"]


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def save(fig, out: Path, name: str):
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--split", default="all")
    ap.add_argument("--out", default="paper/figures")
    a = ap.parse_args()
    recs = [r for r in load(Path(a.run)) if a.split == "all" or r["split"] == a.split]
    pcs = [per_case(r) for r in recs]
    methods = [m for m in MAIN + sorted({m for p in pcs for m in p if "@" in m}) if any(m in p for p in pcs)]
    out = Path(a.out)

    groups = [("Silent consequential defects", lambda r: r["has_cons"] and not r["loud"]),
              ("Loud consequential defects", lambda r: r["has_cons"] and r["loud"]),
              ("No consequential defect", lambda r: not r["has_cons"])]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
    for ax, (title, pred) in zip(axes, groups):
        vals, ns = [], []
        for m in methods:
            rows = [p[m] for p in pcs if m in p and pred(p[m])]
            vals.append(np.mean([r["diag_correct"] for r in rows]) if rows else np.nan)
            ns.append(len(rows))
        y = np.arange(len(methods))[::-1]
        ax.barh(y, vals, height=0.6, color=[HIGHLIGHT if m == "dod" else OTHER for m in methods])
        for yi, v in zip(y, vals):
            if v == v:
                ax.text(v + 0.02, yi, f"{v:.2f}", va="center", fontsize=7.5, color=INK)
        ax.set_xlim(0, 1.12)
        ax.set_title(f"{title} (n={max(ns)})", fontsize=9, color=INK, loc="left")
        ax.set_yticks(y, [LABELS.get(m, m) for m in methods])
        style(ax)
    axes[0].set_xlabel("Correct diagnosis (share of cases)", fontsize=8, color=INK2)
    save(fig, out, "fig_correctness")

    rows_c = [p for p in pcs if next(iter(p.values()))["has_cons"]]
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    for m in methods:
        rr = [p[m] for p in rows_c if m in p]
        if not rr:
            continue
        x, yv = np.mean([r["cost_s"] for r in rr]), np.mean([r["diag_correct"] for r in rr])
        ax.scatter([max(x, 0.05)], [yv], s=36, color=HIGHLIGHT if m == "dod" else OTHER, zorder=3,
                   edgecolor="white", linewidth=1.5)
        ax.annotate(LABELS.get(m, m), (max(x, 0.05), yv), textcoords="offset points", xytext=(6, 3),
                    fontsize=7.5, color=INK)
    ax.set_xscale("log")
    ax.set_xlabel("Mean diagnosis compute (s, measured; log scale)", fontsize=8, color=INK2)
    ax.set_ylabel("Correct diagnosis", fontsize=8, color=INK2)
    ax.set_ylim(-0.02, 1.02)
    style(ax)
    ax.grid(axis="y", color=GRID, lw=0.6)
    save(fig, out, "fig_cost")

    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    for i, m in enumerate(["retrain_on_alarm", "dod"]):
        rr = [p[m] for p in rows_c if m in p]
        if not rr:
            continue
        reg = np.mean([r["regret"] for r in rr])
        frag = np.mean([r["fragility"] for r in rr])
        ax.barh([i + 0.18], [reg], height=0.34, color=OTHER if m != "dod" else HIGHLIGHT)
        ax.barh([i - 0.18], [reg + frag], height=0.34, color="none", edgecolor=INK2, hatch="///", lw=0.8)
        ax.text(reg + frag + 0.001, i - 0.18, f"after later repair: {reg + frag:.3f}", va="center", fontsize=7.5)
        ax.text(reg + 0.001, i + 0.18, f"now: {reg:.3f}", va="center", fontsize=7.5)
    ax.set_yticks([0, 1], [LABELS["retrain_on_alarm"], LABELS["dod"]])
    ax.set_xlabel("Accuracy regret vs best action (cases with a consequential defect)", fontsize=8, color=INK2)
    style(ax)
    save(fig, out, "fig_fragility")
    print("figures written to", out)


if __name__ == "__main__":
    main()
