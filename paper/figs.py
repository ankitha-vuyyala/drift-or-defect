"""Paper figures from saved records (test split unless stated). Writes paper/figures/*.png|pdf.

Fig. correctness_by_domain  primary endpoint per method, news vs taxi test cases (consequential defects)
Fig. silent_loud            monitoring-only vs interventional methods on silent vs loud consequential defects
Fig. cost                   measured diagnosis compute vs primary endpoint (pooled test)
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
from summarize import load, per_case  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#a3a29c"
NAMES = {"retrain_on_alarm": "Retrain on alarm", "validation_first": "Validation first",
         "observational_attribution": "Observational attribution", "full_rollback": "Full rollback",
         "bisect": "Bisection", "bugdoc_shortcut": "Pipeline-instance debugging",
         "llm_report@luna": "LLM agent, report (luna)", "llm_tools@luna": "LLM agent, tools (luna)",
         "llm_report@terra": "LLM agent, report (terra)", "llm_tools@terra": "LLM agent, tools (terra)",
         "dod_no_boundary": "DoD without boundary test", "dod": "DoD"}
ORDER = list(NAMES)
# label offsets (points) for the cost scatter, to keep labels of nearby points apart
OFFSETS = {"bugdoc_shortcut": (6, 6), "llm_tools@luna": (-6, 8), "llm_tools@terra": (-6, -12),
           "dod_no_boundary": (6, -9), "bisect": (-6, -10), "full_rollback": (5, 4), "dod": (6, 3),
           "llm_report@terra": (5, -10)}


def style(ax, grid="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis=grid, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def save(fig, name):
    out = ROOT / "paper" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def main(run: Path) -> None:
    pcs = [per_case(r) for r in load(run)]
    test = [p for p in pcs if next(iter(p.values()))["split"] == "test"]
    methods = [m for m in ORDER if any(m in p for p in test)]

    def mean(m, pred, metric="diag_correct"):
        rr = [p[m] for p in test if m in p and pred(p[m])]
        return (np.mean([float(r[metric]) for r in rr]) if rr else np.nan), len(rr)

    # Fig 1: grouped bars by domain
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    y = np.arange(len(methods))[::-1]
    h = 0.36
    for k, (dom, col) in enumerate((("news", BLUE), ("tlc", ORANGE))):
        vals = [mean(m, lambda r, d=dom: r["has_cons"] and r["domain"] == d)[0] for m in methods]
        ax.barh(y + (h / 2 if k == 0 else -h / 2), vals, height=h - 0.04, color=col,
                label={"news": "News sections", "tlc": "NYC taxi"}[dom])
        for yi, v in zip(y, vals):
            if v == v:
                ax.text(v + 0.01, yi + (h / 2 if k == 0 else -h / 2), f"{v:.2f}", va="center", fontsize=6.5,
                        color=INK)
    ax.set_yticks(y, [NAMES[m] for m in methods], fontsize=7.5)
    ax.set_xlim(0, 1.1)
    ax.set_xlabel("Correct diagnosis on test cases with a consequential defect", fontsize=8, color=INK2)
    ax.legend(fontsize=7.5, frameon=False, loc="upper right")
    style(ax)
    save(fig, "correctness_by_domain")

    # Fig 2: silent vs loud
    sel = [m for m in ("retrain_on_alarm", "validation_first", "observational_attribution", "llm_report@luna",
                       "llm_report@terra", "bugdoc_shortcut", "llm_tools@luna", "llm_tools@terra", "dod_no_boundary",
                       "dod")
           if m in methods]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    x = np.arange(len(sel))
    w = 0.38
    s_vals = [mean(m, lambda r: r["has_cons"] and not r["loud"])[0] for m in sel]
    l_vals = [mean(m, lambda r: r["has_cons"] and r["loud"])[0] for m in sel]
    ax.bar(x - w / 2, s_vals, width=w - 0.03, color=BLUE, label="Silent (passes all validation checks)")
    ax.bar(x + w / 2, l_vals, width=w - 0.03, color=GREY, label="Loud (fails a validation check)")
    ax.set_xticks(x, [NAMES[m] for m in sel], rotation=35, ha="right", fontsize=7)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Correct diagnosis", fontsize=8, color=INK2)
    n_mon = sum(1 for m in sel if m in ("retrain_on_alarm", "validation_first", "observational_attribution")
                or m.startswith("llm_report"))
    ax.axvline(n_mon - 0.5, color=INK2, lw=0.6, ls=":")
    ax.text(0.02, 1.0, "monitoring only", transform=ax.transAxes, fontsize=7, color=INK2, va="top")
    ax.text(0.98, 1.0, "with re-execution", transform=ax.transAxes, fontsize=7, color=INK2, va="top", ha="right")
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.42), ncol=2)
    style(ax, "y")
    save(fig, "silent_loud")

    # Fig 3: cost vs correctness
    fig, ax = plt.subplots(figsize=(5.4, 3.4))
    for m in methods:
        c, _ = mean(m, lambda r: True, "cost_s")
        v, _ = mean(m, lambda r: r["has_cons"])
        col = BLUE if m.startswith("dod") else GREY
        ax.scatter([max(c, 0.03)], [v], s=34, color=col, edgecolor="white", linewidth=1.2, zorder=3)
        off = OFFSETS.get(m, (5, 3))
        ax.annotate(NAMES[m], (max(c, 0.03), v), textcoords="offset points", xytext=off, fontsize=6.5,
                    color=INK, ha="right" if off[0] < 0 else "left")
    ax.set_xscale("log")
    ax.set_xlabel("Mean measured diagnosis compute per case (s, log scale; 0 shown at 0.03)", fontsize=7.5,
                  color=INK2)
    ax.set_ylabel("Correct diagnosis (consequential)", fontsize=8, color=INK2)
    ax.set_ylim(-0.03, 1.03)
    style(ax, "both")
    save(fig, "cost")
    print("figures written")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
