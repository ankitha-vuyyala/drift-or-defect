"""Round-4 figures from saved records. Writes paper/figures/r4_safety.png|pdf and by_change4.png|pdf.

r4_safety     false blame (all cases) vs silent misses (consequential cases) per method, round 4
by_change4    correct diagnosis on consequential cases with / without a published change, rounds 1-4
usage: python paper/figs_v4.py runs/v4main runs/posthoc_by_change.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "paper"))
sys.path.insert(0, str(ROOT / "v4" / "analysis"))
from summarize import load  # noqa: E402
import metrics_v4 as M  # noqa: E402
from figs import INK, INK2, save, style  # noqa: E402

LAB = {"retrain_on_alarm": "Retrain on alarm", "validation_first": "Validation first",
       "observational_attribution": "Observational attr.", "full_rollback": "Full rollback", "bisect": "Bisection",
       "bugdoc_shortcut": "Pipeline-instance debugging", "llm_report@luna": "LLM report (luna)",
       "llm_tools@luna": "LLM tools (luna)", "dod": "DoD", "dod2": "DoD-2", "dod3": "DoD-3",
       "dod4_lite": "DoD-4 lite", "dod4": "DoD-4"}


def safety(run: Path) -> None:
    recs = [r for r in load(run) if r["case"]["domain"] in ("storm", "chicago")]
    fig, ax = plt.subplots(figsize=(5.8, 3.9))
    offs = {"dod": (7, -10), "dod2": (7, -10), "dod3": (7, 3), "bisect": (7, 3)}
    placed, pts = [], {}
    for m, lab in LAB.items():
        if m == "dod4_lite":          # same fix and review sets as DoD-4 by construction; labelled with it
            continue
        rows = [M.case_metrics(r, m) for r in recs if m in r["methods"]]
        if not rows or len(rows) < 0.4 * len(recs):
            continue
        fb = np.mean([x["false_blame"] for x in rows])
        cons = [x for x in rows if x["has_cons"]]
        sm = np.mean([x["silent_miss"] for x in cons]) if cons else np.nan
        cov = np.mean([x["decided"] for x in rows])
        dod4 = m.startswith("dod4")
        ax.scatter([fb], [sm], s=30 + 120 * cov, color="#2a78d6" if dod4 else ("#6f9fd8" if m.startswith("dod")
                                                                              else "#a3a29c"),
                   edgecolor=INK, linewidth=0.5, zorder=3)
        dx, dy = offs.get(m, (6, 3))
        for (px, py) in placed:          # nudge a label that would sit on an earlier one
            if abs(px - fb) < 0.04 and abs(py - sm) < 0.03 and m not in offs:
                dy -= 10
        placed.append((fb, sm))
        if m == "dod2" and pts.get("dod") and abs(pts["dod"][0] - fb) < 0.02 and abs(pts["dod"][1] - sm) < 0.02:
            lab = "DoD, DoD-2"            # the two points coincide; one label
        pts[m] = (fb, sm)
        if m == "dod" and "dod2" in LAB:
            r2 = [M.case_metrics(r, "dod2") for r in recs if "dod2" in r["methods"]]
            if r2 and abs(np.mean([x["false_blame"] for x in r2]) - fb) < 0.02 and abs(
                    np.mean([x["silent_miss"] for x in r2 if x["has_cons"]]) - sm) < 0.02:
                continue                   # labelled together with DoD-2
        ax.annotate((lab + " and DoD-4 lite" if m == "dod4" else lab) + (f" (decides {cov:.2f})" if dod4 else ""),
                    (fb, sm), textcoords="offset points", xytext=(dx, dy), fontsize=6.5, color=INK)
    ax.set_xlabel("False blame (fixes a component that is not a defect), all cases", fontsize=8, color=INK2)
    ax.set_ylabel("Silent miss (consequential defect neither\nfixed nor listed for review)", fontsize=8,
                  color=INK2)
    ax.set_xlim(-0.03, 1.0)
    ax.set_ylim(-0.03, 1.0)
    style(ax)
    save(fig, "r4_safety")


def by_change(path: Path) -> None:
    res = json.loads(path.read_text())
    rounds = [r for r in (1, 2, 3, 4) if f"round{r}" in res]
    ms = [("bugdoc_shortcut", "Pipeline-instance debugging", "#a3a29c"),
          ("observational_attribution", "Observational attribution", "#d9a441"),
          ("llm_tools@luna", "LLM agent, tools (luna)", "#7a5cc4"),
          ("dod", "DoD", "#c9d9f2"), ("dod2", "DoD-2", "#a9c4ea"), ("dod3", "DoD-3", "#6f9fd8"),
          ("dod4", "DoD-4", "#2a78d6")]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, key, title in zip(axes, ("no_change", "change"),
                              ("No published change in the period range", "Published change in the period range")):
        x = np.arange(len(rounds))
        present = [m for m in ms if any(m[0] in res[f"round{r}"][key] for r in rounds)]
        w = 0.84 / len(present)
        for k, (m, label, col) in enumerate(present):
            vals = [res[f"round{r}"][key].get(m, {}).get("diag_correct", np.nan) for r in rounds]
            pos = x + (k - (len(present) - 1) / 2) * w
            ax.bar(pos, vals, width=w - 0.02, color=col, label=label)
        ns = [res[f"round{r}"][key]["dod"]["n"] for r in rounds]
        ax.set_xticks(x, [f"Round {r}\n(n={n})" for r, n in zip(rounds, ns)], fontsize=7.5)
        ax.set_title(title, fontsize=8, color=INK)
        ax.set_ylim(0, 1.05)
        style(ax, "y")
    axes[0].set_ylabel("Correct diagnosis\n(consequential cases)", fontsize=8, color=INK2)
    axes[0].legend(fontsize=6.6, frameon=False, loc="lower center", bbox_to_anchor=(1.05, 1.08), ncol=4)
    save(fig, "by_change4")


if __name__ == "__main__":
    safety(Path(sys.argv[1]))
    if len(sys.argv) > 2:
        by_change(Path(sys.argv[2]))
    print("figures written")
