"""Build the paper (.docx; PDF via LibreOffice) from saved results of all four pre-registered rounds. Every number
in the text and tables is computed here from the records and recorded in the evidence index
(paper/evidence_index.json).

usage: python paper/build_paper_v4.py
expects: runs/final (round 1, with posthoc.json), runs/v2main/summary_v2.json and posthoc_r2.json (round 2),
         runs/v3main/summary_v3.json and posthoc_v3.json (round 3), runs/v3dev/dev_v3.json (DoD-3 on the
         development domains), runs/v4main/summary_v4.json (round 4), runs/v4dev/summary_v4_dev.json (DoD-4 on the
         development domains), runs/posthoc_*.json, runs/benchmark/tables_v4.json, runs/freeze*.json,
         runs/cost_ledger.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "paper"))
import summarize as S  # noqa: E402
from build_lib import Paper  # noqa: E402
import paper_text_v4 as TXT  # noqa: E402

FIG = ROOT / "paper" / "figures"
NAMES = {"retrain_on_alarm": "Retrain on alarm", "validation_first": "Validation first",
         "observational_attribution": "Observational attribution", "full_rollback": "Full rollback",
         "bisect": "Bisection", "bugdoc_shortcut": "Pipeline-instance debugging",
         "llm_report@luna": "LLM agent, report (luna)", "llm_tools@luna": "LLM agent, tools (luna)",
         "llm_report@terra": "LLM agent, report (terra)", "llm_tools@terra": "LLM agent, tools (terra)",
         "dod_no_boundary": "DoD without boundary test", "dod_b1": "DoD, budget 1 run (ratio order)",
         "dod_b1_no_prior": "DoD, budget 1 run (no prior)",
         "dod_b1_uniform": "DoD, budget 1 run (pipeline order)", "dod": "DoD",
         "dod2": "DoD-2", "dod2_no_inv": "DoD-2 without invariants", "dod2_no_hist": "DoD-2, one-transition history",
         "dod3": "DoD-3", "dod3_no_latest": "DoD-3 without latest-change rule", "dod3_no_inv": "DoD-3 without invariants",
         "dod4": "DoD-4", "dod4_lite": "DoD-4 lite"}
DOMAIN_NAMES = {"acs": "Census income", "tlc": "NYC taxi", "news": "News sections", "divvy": "Chicago bike share",
                "hmda": "Mortgage applications", "bts": "Airline delays", "cabi": "Washington bike share",
                "fars": "Fatal crashes (FARS)", "landreg": "House sales",
                "storm": "Storm events", "chicago": "Chicago crashes"}
SHORT = {"acs": "Census", "tlc": "Taxi", "news": "News", "divvy": "Bike (CHI)", "hmda": "Mortgages",
         "bts": "Airlines", "cabi": "Bike (DC)", "fars": "FARS", "landreg": "Houses",
         "storm": "Storms", "chicago": "Crashes (CHI)"}
ROUND_DOMAINS = {1: ["acs", "tlc", "news"], 2: ["divvy", "hmda", "bts"], 3: ["cabi", "fars", "landreg"],
                 4: ["storm", "chicago"]}
CONS = "Cases with a consequential defect (primary endpoint)"


def f2(x):
    return "–" if x is None or x != x else f"{x:.2f}"


class Ctx:
    """Everything the text needs, computed once from the saved records."""

    def __init__(self, P: Paper):
        self.P = P
        self.FIG = FIG
        self.SHORT = SHORT
        self.NAMES = NAMES
        self.S = S
        self.DOMAIN_NAMES = DOMAIN_NAMES
        # round 1: recompute from case records with the v1 analysis module
        self.r1_recs = S.load(ROOT / "runs" / "final")
        self.r1_pcs = [S.per_case(r) for r in self.r1_recs]
        self.r1_test = [p for p in self.r1_pcs if next(iter(p.values()))["split"] == "test"]
        self.r1_dev = [p for p in self.r1_pcs if next(iter(p.values()))["split"] == "dev"]
        S.HYP.clear()
        S.hypotheses(self.r1_pcs, "test")
        S.hypotheses(self.r1_pcs, "dev")
        self.r1_H = S.HYP
        self.r1_post = json.loads((ROOT / "runs" / "final" / "posthoc.json").read_text())
        self.r2 = json.loads((ROOT / "runs" / "v2main" / "summary_v2.json").read_text())
        self.r2_post = json.loads((ROOT / "runs" / "v2main" / "posthoc_r2.json").read_text())
        p3 = ROOT / "runs" / "v3main" / "summary_v3.json"
        self.r3 = json.loads(p3.read_text()) if p3.exists() else None
        self.r3dev = json.loads((ROOT / "runs" / "v3dev" / "dev_v3.json").read_text())
        self.r3_post = json.loads((ROOT / "runs" / "v3main" / "posthoc_v3.json").read_text())
        self.by_change = json.loads((ROOT / "runs" / "posthoc_by_change.json").read_text())
        self.bench = json.loads((ROOT / "runs" / "benchmark" / "tables_v4.json").read_text())
        p4 = ROOT / "runs" / "v4main" / "summary_v4.json"
        self.r4 = json.loads(p4.read_text()) if p4.exists() else None
        p4d = ROOT / "runs" / "v4dev" / "summary_v4_dev.json"
        self.r4dev = json.loads(p4d.read_text()) if p4d.exists() else None
        self.lve = json.loads((ROOT / "runs" / "posthoc_local_vs_e2e.json").read_text())
        self.sens = json.loads((ROOT / "runs" / "posthoc_sensitivity.json").read_text())
        self.total_cases = sum(sum(v.values()) for v in self.bench["cases"].values())
        self.freeze = {k: json.loads((ROOT / "runs" / f).read_text())
                       for k, f in ((1, "freeze.json"), (2, "freeze_v2.json"), (3, "freeze_v3.json"),
                                    (4, "freeze_v4.json"))
                       if (ROOT / "runs" / f).exists()}
        self.ledger = json.loads((ROOT / "runs" / "cost_ledger.json").read_text())
        self.r3_spent = sum(v for k, v in self.ledger["by_job"].items() if k.startswith(("072_", "073_")))
        self.r4_spent = sum(v for k, v in self.ledger["by_job"].items() if k.startswith(("09",)))

    # -- round 1 helpers
    def r1_mean(self, P_, m, pred, metric="diag_correct"):
        rr = [p[m] for p in P_ if m in p and pred(p[m])]
        return (float(np.mean([float(r[metric]) for r in rr])) if rr else float("nan")), len(rr)

    # -- rounds 2 and 3: summary tables
    def tab(self, rnd: int, table: str, m: str, metric: str = "diag_correct"):
        s = {2: self.r2, 3: self.r3, 4: self.r4}[rnd]
        t = (s or {}).get("tables", {}).get(table, {}).get(m)
        return (float(t[metric]) if t and t.get(metric) is not None else float("nan")), (t["n"] if t else 0)

    def E(self, v, what, fmt=".2f", source="runs/final (test split)"):
        return self.P.ev(v, fmt, source, what)


def main(labels: dict | None = None) -> dict:
    P = Paper()
    if labels:
        P.labels.update(labels)
    P.load_refs(ROOT / "paper" / "references.json")
    C = Ctx(P)
    TXT.front(P, C)
    TXT.introduction(P, C)
    TXT.related(P, C)
    TXT.problem(P, C)
    TXT.theory(P, C)
    TXT.methods(P, C)
    TXT.benchmark(P, C, NAMES)
    TXT.protocol(P, C)
    if C.r4:
        TXT.round4(P, C, NAMES)
    TXT.r123(P, C, NAMES)
    TXT.across(P, C, NAMES)
    TXT.discussion(P, C)
    TXT.back(P, C, NAMES)               # declarations, references, Appendix A (proofs)
    TXT.theory_appx(P, C)               # Appendix B
    TXT.methods_appx(P, C)              # Appendix C
    TXT.appx_rounds_intro(P, C, NAMES)  # Appendix D
    TXT.round1(P, C, NAMES)
    TXT.round2(P, C, NAMES)
    TXT.round3(P, C, NAMES)
    TXT.appx_catalog(P, C, NAMES)       # Appendix E
    TXT.appx_hyps(P, C, NAMES)          # Appendix F
    TXT.appx_repro(P, C, NAMES)         # Appendix G
    out = ROOT / "paper" / "drift_or_defect.docx"
    cp = P.doc.core_properties
    cp.author, cp.last_modified_by, cp.comments = "[Authors]", "[Authors]", ""
    cp.title = TXT.TITLE
    P.save(out)
    (ROOT / "paper" / "evidence_index.json").write_text(json.dumps(P.evidence, indent=1), encoding="utf-8")
    md = ["# Evidence index", "", "Every number reported in the paper, with the file it was computed from "
          "(generated by paper/build_paper_v4.py).", "", "| # | Value | Quantity | Source |", "|---|---|---|---|"]
    md += [f"| {i + 1} | {e['value']} | {e['what']} | {e['source']} |" for i, e in enumerate(P.evidence)]
    (ROOT / "paper" / "evidence_index.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("written", out, len(P.evidence), "evidence entries")
    return dict(P.labels)


if __name__ == "__main__":
    first = main()            # pass 1 collects figure/table/section numbers for forward references
    main(first)
