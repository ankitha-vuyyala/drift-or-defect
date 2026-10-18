"""Summarise case records: per-method decision quality, outcomes and cost, overall and by subgroup.

usage: python analysis/summarize.py runs/<name> [--out runs/<name>/summary.md]

Definitions (per case, from the grader's ground truth):
  consequential  defects whose fix changes some action's holdout accuracy by >= 0.002 (bench.EPS_CONSEQUENTIAL)
  effective      defects whose fix changes the pipeline output at all
  diag_correct   consequential ⊆ fix ⊆ effective (the diagnosis: which components to fix, if any)
  correct        diag_correct, and the retrain decision equals the oracle's
  type_correct   the action type (nothing / retrain / fix / fix+retrain) equals the oracle's
  regret         best holdout accuracy over the evaluated actions minus the accuracy after the method's action
  unnecessary_retrain   method retrains while the oracle does not
  missed_defect  a consequential defect is not in the fix set
  false_blame    the fix set contains a component that is not an effective defect
  silent         the case's consequential defects pass all support-level validation checks on the model inputs
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np


def load(run: Path) -> list[dict]:
    """Case records of a run, with LLM-baseline results (<domain>.llm_<tag>.jsonl) merged in as '<method>@<tag>'."""
    recs, by_id = [], {}
    for p in sorted(run.glob("*.jsonl")):
        if p.name.endswith(".errors.jsonl") or ".llm_" in p.name:
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                recs.append(r)
                by_id[r["case"]["case_id"]] = r
    for p in sorted(run.glob("*.llm_*.jsonl")):
        tag = p.name.split(".llm_")[1].replace(".jsonl", "")
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                x = json.loads(line)
                if x["case_id"] in by_id:
                    for m, d in x["methods"].items():
                        by_id[x["case_id"]]["methods"][f"{m}@{tag}"] = d
    return recs


def atype(fix, retrain) -> str:
    return ("fix" if fix else "") + ("+retrain" if fix and retrain else ("retrain" if retrain else "")) or "nothing"


def per_case(rec: dict) -> dict:
    g = rec["gt"]
    cons, eff = set(g["consequential"]), set(g["defective"])
    orc = rec["oracle"]
    best = g.get("best_score")
    failing = [f for f, r in rec["obs"]["features"].items() if not f.startswith("_") and r.get("validation_fail")]
    rows = rec["obs"]["features"].get("_rows", {})
    loud = bool(failing) or (rows.get("ref") and rows.get("cur", 0) / rows["ref"] < 0.5) or rec["obs"]["cur_crash"]
    drop = None if rec["obs"]["cur_perf"] is None else rec["obs"]["ref_perf"] - rec["obs"]["cur_perf"]
    sig = ",".join(sorted(i["id"] for i in rec["case"]["injected"] if i.get("kind") == "defect")) or "none"
    base = {"case_id": rec["case"]["case_id"], "domain": rec["case"]["domain"], "tier": rec["case"]["tier"],
            "sig": sig,
            "scenario": rec["case"]["meta"].get("scenario"), "split": rec["split"],
            "has_cons": bool(cons), "oracle_type": atype(orc["fix"], orc["retrain"]),
            "loud": bool(loud), "alarm": drop is None or drop >= 0.01,
            "pipeline_cost_s": rec["obs"]["pipeline_cost_s"]}
    out = {}
    for m, d in rec["methods"].items():
        fix = set(d.get("fix") or [])
        sc = d["outcome"].get("score")
        sc = float("nan") if sc is None else sc
        regret = (best - sc) if (best is not None and sc == sc) else (best if best is not None else float("nan"))
        out[m] = {**base,
                  "correct": cons <= fix <= eff and bool(d["retrain"]) == orc["retrain"],
                  "diag_correct": cons <= fix <= eff,
                  "type_correct": atype(fix, d["retrain"]) == base["oracle_type"],
                  "regret": regret, "unnecessary_retrain": bool(d["retrain"]) and not orc["retrain"],
                  "missed_retrain": (not d["retrain"]) and orc["retrain"],
                  "missed_defect": bool(cons - fix), "false_blame": bool(fix - eff),
                  "detect_defect": bool(fix) == bool(cons),
                  "fragility": (max(0.0, sc - d["outcome"]["score_after_repair"])
                                if d["outcome"].get("score_after_repair") is not None and sc == sc else 0.0),
                  "cost_s": d.get("cost_s", 0.0), "error": bool(d.get("error")),
                  "llm_usd": (d.get("notes") or {}).get("llm_usd", 0.0)}
    return out


def boot_ci(x: np.ndarray, clusters: np.ndarray, n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    uc = np.unique(clusters)
    idx = {c: np.nonzero(clusters == c)[0] for c in uc}
    stats = []
    for _ in range(n):
        pick = rng.choice(uc, len(uc), replace=True)
        sel = np.concatenate([idx[c] for c in pick])
        stats.append(np.nanmean(x[sel]))
    return float(np.nanpercentile(stats, 2.5)), float(np.nanpercentile(stats, 97.5))


TABLES: dict = {}          # machine-readable copy of every table (written to summary.json for the paper build)


def table(rows_by_method: dict, title: str, cols=("diag_correct", "correct", "regret", "fragility",
                                                  "unnecessary_retrain", "missed_defect", "false_blame",
                                                  "cost_s")) -> list[str]:
    lines = [f"### {title}", "", "| method | n | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    TABLES[title] = {}
    for m, rows in rows_by_method.items():
        if not rows:
            continue
        vals, rec = [], {"n": len(rows), "cases": [r["case_id"] for r in rows]}
        for c in cols:
            x = np.array([float(r[c]) for r in rows], dtype=float)
            v = float(np.nanmean(x))
            rec[c] = v
            vals.append(f"{v:.3f}" if c != "cost_s" else f"{v:.2f}")
        TABLES[title][m] = rec
        lines.append(f"| {m} | {len(rows)} | " + " | ".join(vals) + " |")
    return lines + [""]


def paired_diff(pcs: list, m1: str, m2: str, metric: str, pred, n: int = 2000, seed: int = 0) -> dict:
    """Mean of metric(m1) - metric(m2) over cases satisfying pred, with a paired cluster-bootstrap 95% CI."""
    rows = [(p[m1], p[m2]) for p in pcs if m1 in p and m2 in p and pred(p[m1])]
    if not rows:
        return {"n": 0}
    d = np.round(np.array([float(a[metric]) - float(b[metric]) for a, b in rows]), 12)
    cl = np.array([f"{a['domain']}|{a['sig']}" for a, _ in rows])     # clusters: domain x defect signature
    lo, hi = boot_ci(d, cl, n, seed)
    # two-sided bootstrap p-value for mean difference = 0
    rng = np.random.default_rng(seed + 1)
    uc = np.unique(cl)
    idx = {c: np.nonzero(cl == c)[0] for c in uc}
    means = []
    for _ in range(n):
        pick = rng.choice(uc, len(uc), replace=True)
        means.append(d[np.concatenate([idx[c] for c in pick])].mean())
    means = np.array(means)
    means = np.round(means, 12)
    pval = float(min(1.0, 2 * min((means <= 0).mean(), (means >= 0).mean())))
    pval = max(pval, 1.0 / n)          # resolution of the bootstrap
    return {"n": len(rows), "diff": float(d.mean()), "ci": [lo, hi], "p": pval}


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    out, m, running = {}, len(items), 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


HYP: dict = {}


def hypotheses(pcs: list, split: str = "test") -> list[str]:
    S = [p for p in pcs if next(iter(p.values()))["split"] == split]
    H = HYP.setdefault(split, {})
    if not S:
        return []
    L = [f"## Hypotheses on the {split} split ({len(S)} cases)", ""]
    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    loud = lambda r: r["has_cons"] and r["loud"]

    def mean(m, pred, metric="diag_correct"):
        rr = [p[m] for p in S if m in p and pred(p[m])]
        return (float(np.mean([float(r[metric]) for r in rr])), len(rr)) if rr else (float("nan"), 0)
    mon = ["retrain_on_alarm", "validation_first", "observational_attribution"] + \
          sorted({m for p in S for m in p if m.startswith("llm_report")})
    L.append("**H1** diagnosis correctness on silent / loud consequential defects (monitoring-only methods):")
    for m in mon:
        a, na = mean(m, silent)
        b, nb = mean(m, loud)
        L.append(f"- {m}: silent {a:.3f} (n={na}), loud {b:.3f} (n={nb})")
    base = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
            "bugdoc_shortcut"] + sorted({m for p in S for m in p if m.startswith("llm_")})
    best = max(base, key=lambda m: mean(m, cons)[0] if mean(m, cons)[1] else -1)
    L.append("")
    L.append(f"**H2** primary endpoint (consequential): dod {mean('dod', cons)[0]:.3f} vs best baseline {best} "
             f"{mean(best, cons)[0]:.3f}; paired difference {paired_diff(S, 'dod', best, 'diag_correct', cons)}")
    L.append("")
    L.append(f"**H3** budget one run: dod_b1 {mean('dod_b1', cons)[0]:.3f} vs dod_b1_uniform "
             f"{mean('dod_b1_uniform', cons)[0]:.3f}; "
             f"diff {paired_diff(S, 'dod_b1', 'dod_b1_uniform', 'diag_correct', cons)}; mean compute dod "
             f"{mean('dod', lambda r: True, 'cost_s')[0]:.2f}s vs bugdoc_shortcut "
             f"{mean('bugdoc_shortcut', lambda r: True, 'cost_s')[0]:.2f}s")
    L.append("")
    tests = {}
    for other in ("retrain_on_alarm", "validation_first"):
        for metric in ("missed_defect", "false_blame"):
            tests[f"{metric}: dod - {other}"] = paired_diff(S, "dod", other, metric, lambda r: True)
    tests["fragility: dod - retrain_on_alarm"] = paired_diff(S, "dod", "retrain_on_alarm", "fragility", cons)
    tests["primary: dod - best"] = paired_diff(S, "dod", best, "diag_correct", cons)
    adj = holm({k: v["p"] for k, v in tests.items() if v.get("n")})
    H["best_baseline"] = best
    H["tests"] = {k: {**v, "p_holm": adj.get(k)} for k, v in tests.items()}
    H["H1"] = {m: {"silent": mean(m, silent), "loud": mean(m, loud)} for m in mon}
    H["H3"] = {"dod_b1": mean("dod_b1", cons), "dod_b1_uniform": mean("dod_b1_uniform", cons),
               "b1_diff": paired_diff(S, "dod_b1", "dod_b1_uniform", "diag_correct", cons),
               "cost_dod": mean("dod", lambda r: True, "cost_s"),
               "cost_bugdoc": mean("bugdoc_shortcut", lambda r: True, "cost_s")}
    t1c = lambda r: r["has_cons"] and "T1" in r["tier"]
    H["H5"] = {"dod": mean("dod", t1c), "dod_no_boundary": mean("dod_no_boundary", t1c),
               "diff": paired_diff(S, "dod", "dod_no_boundary", "diag_correct", t1c)}
    L.append("**H4** (and H2) paired differences with Holm-adjusted p-values:")
    for k, v in tests.items():
        if v.get("n"):
            L.append(f"- {k}: {v['diff']:+.3f} [{v['ci'][0]:+.3f}, {v['ci'][1]:+.3f}] n={v['n']} "
                     f"p={v['p']:.4f} p_holm={adj.get(k, float('nan')):.4f}")
    t1 = lambda r: r["has_cons"] and "T1" in r["tier"]
    L.append("")
    L.append(f"**H5** T1 consequential: dod {mean('dod', t1)[0]:.3f} vs dod_no_boundary "
             f"{mean('dod_no_boundary', t1)[0]:.3f} (n={mean('dod', t1)[1]}); "
             f"diff {paired_diff(S, 'dod', 'dod_no_boundary', 'diag_correct', t1)}")
    return L + [""]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    run = Path(a.run)
    recs = load(run)
    pcs = [per_case(r) for r in recs]
    methods = sorted({m for p in pcs for m in p}, key=lambda m: (m.startswith("dod"), "@" in m, m))
    lines = [f"# Summary of {run.name}", "", f"{len(recs)} cases"]
    by_dom = defaultdict(int)
    for r in recs:
        by_dom[r["case"]["domain"]] += 1
    lines += [f"by domain: {dict(by_dom)}", ""]

    def select(pred):
        return {m: [p[m] for p in pcs if m in p and pred(p[m])] for m in methods}
    for sp in ("dev", "test"):
        lines += table(select(lambda r, sp=sp: r["split"] == sp), f"Split: {sp}")
    lines += table(select(lambda r: True), "All cases")
    lines += table(select(lambda r: r["has_cons"]), "Cases with a consequential defect")
    lines += table(select(lambda r: r["has_cons"] and not r["loud"]), "Silent consequential defects (pass validation)")
    lines += table(select(lambda r: r["has_cons"] and r["loud"]), "Loud consequential defects (fail validation)")
    lines += table(select(lambda r: not r["has_cons"]), "No consequential defect (drift, benign changes, nothing)")
    lines += table(select(lambda r: r["alarm"]), "Cases where the performance alarm fires (drop >= 0.01)")
    first = lambda p: next(iter(p.values()))
    for t in sorted({first(p)["tier"] for p in pcs}):
        lines += table(select(lambda r, t=t: r["tier"] == t), f"Tier {t}")
    for d in sorted(by_dom):
        lines += table(select(lambda r, d=d: r["domain"] == d), f"Domain {d}")
    # cluster bootstrap CI for 'correct' (clusters: domain x tier x scenario)
    lines += ["### 95% cluster-bootstrap CI of 'correct' (clusters = domain x defect signature)", ""]
    for m in methods:
        rows = [p[m] for p in pcs if m in p]
        if not rows:
            continue
        x = np.array([float(r["correct"]) for r in rows])
        cl = np.array([f"{r['domain']}|{r['sig']}" for r in rows])
        lo, hi = boot_ci(x, cl)
        lines.append(f"- {m}: {np.mean(x):.3f} [{lo:.3f}, {hi:.3f}]")
    lines.append("")
    # oracle action distribution and silent/loud counts
    lines += ["### Case composition", ""]
    comp = defaultdict(int)
    for p in pcs:
        r = first(p)
        comp[(r["domain"], r["oracle_type"], "silent" if (r["has_cons"] and not r["loud"]) else
              ("loud" if r["has_cons"] else "-"))] += 1
    for k, v in sorted(comp.items()):
        lines.append(f"- {k}: {v}")
    lines += hypotheses(pcs, "test") + hypotheses(pcs, "dev")
    out = Path(a.out) if a.out else run / "summary.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps({"tables": TABLES, "hypotheses": HYP}, indent=1, default=str),
                                        encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
