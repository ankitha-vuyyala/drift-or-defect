"""Build the paper (.docx; PDF via LibreOffice) from saved results. Every number in the text and tables is
computed here from the records and recorded in the evidence index (paper/evidence_index.json).

usage: python paper/build_paper.py   (expects runs/final, runs/benchmark/tables.json, runs/freeze.json,
                                      runs/cost_ledger.json, runs/t2_probe, data/bronze/BRONZE_MANIFEST.json)
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

RUN = ROOT / "runs" / "final"
FIG = ROOT / "paper" / "figures"
NAMES = {"retrain_on_alarm": "Retrain on alarm", "validation_first": "Validation first",
         "observational_attribution": "Observational attribution", "full_rollback": "Full rollback",
         "bisect": "Bisection", "bugdoc_shortcut": "Pipeline-instance debugging",
         "llm_report@luna": "LLM agent, report (gpt-5.6-luna)", "llm_tools@luna": "LLM agent, tools (gpt-5.6-luna)",
         "llm_report@terra": "LLM agent, report (gpt-5.6-terra)",
         "llm_tools@terra": "LLM agent, tools (gpt-5.6-terra)",
         "dod_no_boundary": "DoD without boundary test", "dod_b1": "DoD, budget 1 run (ratio order)",
         "dod_b1_uniform": "DoD, budget 1 run (pipeline order)", "dod": "DoD (full)"}
MAIN = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
        "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
        "dod_no_boundary", "dod_b1", "dod_b1_uniform", "dod"]


def f3(x):
    return "–" if x is None or x != x else f"{x:.2f}"


def main(labels: dict | None = None) -> dict:
    recs = S.load(RUN)
    pcs = [S.per_case(r) for r in recs]
    test = [p for p in pcs if next(iter(p.values()))["split"] == "test"]
    dev = [p for p in pcs if next(iter(p.values()))["split"] == "dev"]
    methods = [m for m in MAIN if any(m in p for p in test)]
    post = json.loads((RUN / "posthoc.json").read_text())
    bench = json.loads((ROOT / "runs" / "benchmark" / "tables.json").read_text())
    freeze = json.loads((ROOT / "runs" / "freeze.json").read_text())
    ledger = json.loads((ROOT / "runs" / "cost_ledger.json").read_text())
    bronze = json.loads((ROOT / "data" / "bronze" / "BRONZE_MANIFEST.json").read_text())

    def mean(P, m, pred, metric="diag_correct"):
        rr = [p[m] for p in P if m in p and pred(p[m])]
        return (float(np.mean([float(r[metric]) for r in rr])) if rr else float("nan")), len(rr)

    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    loud = lambda r: r["has_cons"] and r["loud"]
    P = Paper()
    if labels:
        P.labels.update(labels)
    S.HYP.clear()
    S.hypotheses(pcs, "test")
    S.hypotheses(pcs, "dev")
    H = S.HYP
    P.load_refs(ROOT / "paper" / "references.json")
    src = "runs/final (test split)"

    def E(v, what, fmt=".2f", source=src):
        return P.ev(v, fmt, source, what)

    n_test = len(test)
    n_cons, _ = len([p for p in test if next(iter(p.values()))["has_cons"]]), 0
    n_sil = len([p for p in test if silent(next(iter(p.values())))])
    dod_c = mean(test, "dod", cons)[0]
    best = H["test"]["best_baseline"]
    best_c = mean(test, best, cons)[0]
    t2 = H["test"]["tests"]["primary: dod - best"]
    news_d = post["P1"]["dod"]["news"]["mean"]
    news_b = post["P1"]["bugdoc_shortcut"]["news"]["mean"]
    news_l = post["P1"]["llm_tools@luna"]["news"]["mean"]
    tlc_d = post["P1"]["dod"]["tlc"]["mean"]
    tlc_nb = post["P1"]["dod_no_boundary"]["tlc"]["mean"]
    tlc_b = post["P1"]["bugdoc_shortcut"]["tlc"]["mean"]
    base_ms = [m for m in methods if not m.startswith("dod")]
    news_best_m = max(base_ms, key=lambda m: mean(test, m, lambda r: cons(r) and r["domain"] == "news")[0])
    news_best = mean(test, news_best_m, lambda r: cons(r) and r["domain"] == "news")[0]
    tlc_best_m = max(base_ms, key=lambda m: mean(test, m, lambda r: cons(r) and r["domain"] == "tlc")[0])
    tlc_best = mean(test, tlc_best_m, lambda r: cons(r) and r["domain"] == "tlc")[0]
    h2_met = t2["diff"] >= 0.15 and t2["ci"][0] > 0
    h2_sig = t2["ci"][0] > 0 and t2["p_holm"] < 0.05
    p2_d = post["P2"]["dod"]["cons"]["mean"]
    p2_b = post["P2"]["bugdoc_shortcut"]["cons"]["mean"]
    spent = ledger["total_usd"]
    n_cases = len(pcs)

    # ------------------------------------------------------------------ front matter
    P.title("Is It Model Drift or a Broken Pipeline? Intervention-Based Diagnosis of Production ML Degradation",
            "[Author names and affiliations withheld]",
            "Preprint. Code, benchmark, raw records and replay scripts: [repository link to be added]")
    P.heading("Abstract", 1, numbered=False)
    P.para(
        "When a production model degrades, teams usually retrain it. But the model sees the output of a data "
        "pipeline, not the world, and pipelines change constantly: adapters are rewritten for new source schemas, "
        "libraries are upgraded, reference tables go stale. We ask when a genuine change in the prediction problem "
        "can be told apart from a defect in the pipeline, and what to do about it. We prove that a defect whose "
        "corrupted features stay inside the image of the correct pipeline is indistinguishable from a change of the "
        "world for every monitoring-only diagnostic, with or without labels; that re-executing a changed component "
        "at its known-good version identifies it exactly when the change was not forced by a source; and that "
        "source-forced changes are identifiable by no re-execution at all without an extra assumption. Building on "
        "these results, DoD diagnoses a degradation by single-component rollback, effect and schema-boundary tests "
        "and recommends fixing, retraining, both or nothing. We release a benchmark of three executable pipelines "
        f"over real data from 2012–2026 (census income, New York taxi trips, news headlines) with {E(n_cases, 'total cases', 'd', 'runs/final')} "
        "cases whose defects include dated source-schema changes taken from the published files and real "
        "behaviour changes across pandas 1.5, 2.2 and 3.0, and whose ground truth comes from executing every action. "
        f"On {E(n_test, 'test cases', 'd')} pre-registered test cases, retrain-on-alarm and validation-first "
        f"diagnosed none of the {E(n_sil, 'silent consequential test cases', 'd')} silent defects (observational "
        f"attribution: {E(mean(test, 'observational_attribution', silent)[0], 'obs silent')}; an LLM agent reading "
        f"the same report: {E(mean(test, 'llm_report@luna', silent)[0], 'llm_report luna silent')}). DoD diagnosed "
        f"{E(dod_c, 'dod primary')} of consequential defects against {E(best_c, 'best baseline primary')} for the "
        f"best baseline, an LLM agent with re-execution tools; the difference ({E(t2['diff'], 'H2 diff', '+.2f')}) "
        + ("was significant but fell just short of the pre-registered effect size of 0.15. "
           if (h2_sig and not h2_met) else ("met the pre-registered criterion. " if h2_met else
                                             "was not significant. ")) + "It was "
        f"decisive on news ({E(news_d, 'news dod')} vs at most {E(news_best, 'news best baseline')} for any "
        "baseline) and hurt on taxi data, "
        "where the city changed the airport fee in the same quarter that the column was renamed — exactly the "
        "failure our third result predicts. On cases with a consequential defect, models chosen by "
        f"retrain-on-alarm lost {E(H['test']['tests']['fragility: dod - retrain_on_alarm']['diff'] * -1, 'fragility gap')} "
        "more accuracy than DoD's once the pipeline was repaired. The study cost "
        f"{E(spent, 'total API spend', '.2f', 'runs/cost_ledger.json')} USD in API calls.")

    # ------------------------------------------------------------------ 1 introduction
    P.heading("Introduction", 1, label="sec:intro")
    P.para(
        "A production model's accuracy drops and an alarm fires. The default response is to retrain on recent "
        "data, and monitoring tools are built around it: they compare input and output distributions with a "
        "reference window and trigger the retraining pipeline. But a model's inputs are not the world; they are "
        "the output of a data pipeline that changes all the time. Studies of production ML report that most "
        "outages of a large ML pipeline were not ML-centric [@papasian2020], data and pipeline problems are common "
        "[@breck2019; @shankar2024], and individual incidents "
        "show how costly silent pipeline faults are: a logging change at Uber removed a fare component for 10% of "
        "sessions in key US cities and went undetected for 45 days [@uberd3]. Retraining on the output of a broken pipeline can hide "
        "such a fault: the model is fitted to corrupted features, and breaks again when someone finally repairs the "
        "pipeline.")
    P.para(
        "This paper asks a precise question: **from what evidence can a genuine change of the prediction problem "
        "be told apart from a defect of the data pipeline, and which action follows — fix the pipeline, retrain, "
        "both, or nothing?** We make four contributions.")
    P.bullets([
        "**Identifiability (Section 4).** A defect is indistinguishable from a world change for every "
        "monitoring-only diagnostic exactly when its corrupted features stay inside the image of the correct "
        "pipeline (Theorem 1); validation rules catch exactly the rest. Re-executing a changed component at its "
        "reference version decides, without statistical error, whether it is an effective defect — if its change "
        "was not forced by a change of the data source (Theorem 2). Source-forced changes are identifiable by no "
        "re-execution (Theorem 3) unless one assumes, for example, that the world does not jump exactly at a "
        "published schema change.",
        "**DoD (Section 5),** a diagnoser that turns these results into single-component rollback, effect and "
        "boundary tests ordered by monitoring evidence per measured cost, and returns an action with its evidence.",
        "**A benchmark (Section 6)** of three executable pipelines over real data with genuine temporal drift and "
        "real, dated source-schema changes, real library-upgrade behaviours and documented incident classes, in "
        f"{E(n_cases, 'total cases', 'd', 'runs/final')} cases whose ground truth is obtained by executing every action.",
        "**A pre-registered evaluation (Sections 7–8)** against the responses practitioners use, observational "
        "root-cause attribution, pipeline-instance debugging, bisection and LLM agents with and without the same "
        "re-execution tools, with negative results reported as found.",
    ])
    P.para(
        f"The results support the first contribution clearly: on {E(n_sil, 'silent consequential test cases', 'd')} "
        "test cases with a silent consequential defect, retrain-on-alarm and validation-first diagnosed none. They "
        "support DoD in a qualified way: it was correct on "
        f"{E(news_d, 'news dod')} of consequential news defects but only {E(tlc_d, 'tlc dod')} of taxi defects, "
        "because one real-world change coincided with a schema change; its pooled advantage over the best baseline "
        f"({E(t2['diff'], 'H2 diff', '+.2f')}, 95% CI [{E(t2['ci'][0], 'H2 ci lo', '+.2f')}, "
        f"{E(t2['ci'][1], 'H2 ci hi', '+.2f')}]) "
        + ("is significant but falls just short of the pre-registered effect size of 0.15."
           if (h2_sig and not h2_met) else ("meets the pre-registered criterion." if h2_met else
                                             "is not significant.")))

    # ------------------------------------------------------------------ 2 related work
    P.heading("Related work", 1, label="sec:related")
    P.para(
        "**Data validation and monitoring.** TFDV [@breck2019], Deequ [@schelter2018], Auto-Validate [@song2021] "
        "and Auto-Validate-by-History [@tu2023] check schemas, ranges and learned constraints; PrismaDV [@chen2026] "
        "generates task-aware data tests with a language model. Drift detection [@rabanser2019; @lipton2018] and "
        "monitoring tools add distribution tests. These raise alarms but do not attribute them. Theorem 1 states "
        "precisely which defects any such check can see.")
    P.para(
        "**Attributing performance changes.** DISDE [@cai2023], WhyShift [@liu2023] and hierarchical "
        "decompositions [@singh2024] attribute a performance drop to covariate and concept shift, assuming that "
        "features are computed correctly; a pipeline defect appears to them as one of these shifts. Budhathoki et "
        "al. [@budhathoki2021] and Zhang et al. [@zhang2023] attribute distribution or performance changes to "
        "changes in causal mechanisms; a pipeline step modelled as a mechanism could in principle be blamed, but "
        "from observational data alone, so Theorem 1 applies to them as well.")
    P.para(
        "**Debugging pipelines by re-execution.** BugDoc [@lourenco2020] re-runs pipeline instances with known-good "
        "parameter values to find minimal failure causes; AID [@fariha2020] and DataPrism [@galhotra2022] use "
        "causally guided interventions and minimise their number; mlinspect and mlwhatif "
        "[@grafberger2022; @grafberger2023] instrument and patch pipelines; SAVAGE [@zhu2025] searches for harmful "
        "corruptions. None models a world that may legitimately have changed, decides between fixing and "
        "retraining, or treats changes forced by a data source differently from free ones — the distinction our "
        "results show to be decisive.")
    P.para(
        "**Causal diagnosis of ML systems.** Paleyes and Lawrence [@paleyes2023] attribute anomalies on the "
        "dataflow graph observationally to input shift or faulty components; Leest et al. [@leest2025] propose "
        "causal system maps to separate software faults, data-quality issues and natural change, without an "
        "evaluation. Causal root-cause analysis for microservices [@ikram2022], including interventional approaches "
        "[@jha2024], and root-cause discovery and identifiability results [@li2025; @orchard2025] are the closest "
        "formal relatives; our results are their "
        "counterpart for data pipelines, where the confounder is the world itself. Observability for ML pipelines "
        "[@shankar2022] and studies of data-pipeline issues [@foidl2024; @sambasivan2021] motivate the problem.")

    # ------------------------------------------------------------------ 3 formulation
    P.heading("Problem formulation", 1, label="sec:problem")
    P.para(
        "World records W with labels Y follow a distribution D from a family 𝔇 of distributions we are willing "
        "to entertain (covariate, label and concept shift). A *source encoding* σ turns world records into "
        "published raw records R = σ(W) (schema, units, code lists). A pipeline is a directed acyclic graph of "
        "deterministic components; with versions θ (code, configuration, reference artifacts, library environment) "
        "it computes features X = P_θ(R). θ⁰ is the version deployed when the model h was trained; θ* is the "
        "*specification* for the current period — the pipeline a careful engineer would run on the current "
        "sources. A component c is *changed* if θ_c ≠ θ⁰_c, *forced* if the specification itself differs from the "
        "reference (θ*_c ≠ θ⁰_c, e.g. an adapter rewritten for a new schema), and an *effective defect* if "
        "replacing θ_c by θ*_c changes the pipeline output on the current records.")
    P.para(
        "A *monitoring-only* diagnostic sees samples of the joint law of (P_θ(σ(W)), Y), reference statistics, the "
        "lineage graph and the change log (which components changed and in which aspect). An *interventional* "
        "diagnostic may in addition re-execute components on archived inputs. The actions are fix(S) for a set of "
        "components S, retrain, fix(S)+retrain and nothing. We call a defect *consequential* if fixing it changes "
        "the held-out accuracy of the nothing or the retrain action by at least 0.002; the correct action fixes the "
        "consequential defects and retrains iff retraining after the fix gains more than 0.01 accuracy.")

    # ------------------------------------------------------------------ 4 identifiability
    P.heading("Identifiability", 1, label="sec:theory")
    P.para("Proofs are in Appendix A.")
    P.para(
        "**Theorem 1 (observational equivalence of silent defects).** Let (D, σ, θ) be defective. If some D′ ∈ 𝔇 "
        "and some non-defective θ′ with the same change-log signature give the same joint law of features and "
        "labels, then every monitoring-only diagnostic outputs \"defect\" with the same probability under both "
        "configurations; its type-I plus type-II error on the pair is at least 1.")
    P.para(
        "**Corollary 1 (image characterisation).** If 𝔇 contains all distributions on world records and labels, "
        "a defect is monitoring-equivalent to a world change if and only if its corrupted features lie almost "
        "surely in the image ℐ = P_θ*(σ(𝒲)) of the correct pipeline. A defect that puts mass ε > 0 outside ℐ is "
        "detected by a support check against ℐ with probability 1 − (1 − ε)ⁿ from n records.")
    P.para(
        "Data-validation rules therefore catch exactly the *loud* defects; *silent* ones — inside the image — are "
        "invisible to drift tests, validation, label monitoring and any learned combination of them, unless 𝔇 is "
        "restricted.")
    P.para(
        "**Theorem 2 (interventional identification of unforced changes).** Let components be deterministic, the "
        "intermediate outputs of the production run be archived, and the reference version of a changed component "
        "c be reproducible. If c was not forced (θ*_c = θ⁰_c), the rollback test — run θ⁰_c on c's current inputs "
        "and compare with c's current output — returns *differ* iff c is an effective defect on the current data. "
        "Rolling back all components that differ yields the correct pipeline's output, so the remaining "
        "performance gap is attributable to the world; this needs at most |Δ| single-component executions for a "
        "change set Δ.")
    P.para(
        "**Theorem 3 (the limit: source-forced changes).** Let the source encoding change from σ⁰ to σ¹. If some "
        "D″ ∈ 𝔇 satisfies σ¹#D = σ⁰#D″, no diagnostic using monitoring and any re-execution of pipeline "
        "components separates (D, σ¹) from (D″, σ⁰). The same holds for the correctness of an adapter written for "
        "σ¹: it is a property of σ¹, which no re-execution observes.")
    P.para(
        "Side information breaks the tie. DoD uses one explicit assumption, *world smoothness at schema "
        "boundaries*: between adjacent periods the world moves a quantity by no more than it does between ordinary "
        "adjacent periods. A jump of a component's output at a published schema change that clearly exceeds the "
        "ordinary period-to-period change is then attributed to the encoding or the adapter. When the world itself "
        "jumps at the schema change, the assumption fails; Section 8 shows such a case in real data.")
    P.para(
        "**Proposition 4 (test ordering).** Under a single-fault prior p_c with test costs k_c, testing candidates "
        "in decreasing p_c/k_c minimises the expected cost of finding the faulty component [@gluss1959].")

    # ------------------------------------------------------------------ 5 method
    P.heading("Method: DoD", 1, label="sec:method")
    P.para(
        "DoD receives the monitoring report of the reference and current periods, archived intermediate outputs of "
        "both production runs, the lineage graph with column-level lineage to raw columns, the change log and the "
        "published schema events of each source. It proceeds in four steps.")
    P.bullets([
        "**Candidates.** Every changed component, and every unchanged component that depends — through "
        "column-level lineage — on a column touched by a schema event and either reads the source or introduces "
        "drift at its node (a possible stale or latent defect). A changed component is *forced* if it depends on "
        "such a column.",
        "**Ordering.** Candidates are tested in decreasing ratio of prior to measured execution time "
        "(Proposition 4). The prior combines the drift *introduced* at the component's node (drift of its output "
        "columns beyond that of the same columns at its inputs, computed from archived outputs at no cost), drift "
        "and validation evidence on the model inputs it feeds, and source coupling.",
        "**Tests.** *Rollback* re-executes the reference version on the component's current inputs and compares "
        "outputs exactly. For an unforced component a difference is an effective defect (Theorem 2). For a forced "
        "component, an *effect* test propagates the rolled-back output to the deployed model; an improvement above "
        "τ = 0.003 marks it harmful, otherwise — and whenever the reference version cannot run on the new inputs, "
        "or the change alters the label or the set of records — a *boundary* test compares the component's output "
        "just before the schema event (produced by the then-deployed version, from archived history) with its "
        "output at the event, relative to the ordinary change between the two preceding periods. Only columns the "
        "component creates or modifies from the event's columns count; jumps already present at its inputs are "
        "inherited. A jump above 3 times the ordinary change and above 0.05 PSI, new missing values, or lost "
        "records flag the component.",
        "**Action.** Fix every harmful or flagged component; retrain if the accuracy drop that remains after the "
        "fix — estimated on the counterfactual with harmful components rolled back and with model inputs produced "
        "by flagged components masked in both periods — is at least 0.01.",
    ])
    P.para(
        "With a compute budget, testing stops when the measured cost reaches it, and untested candidates are "
        "treated as benign. All thresholds were fixed at design time and frozen before the test split was run.")

    # ------------------------------------------------------------------ 6 benchmark
    P.heading("Benchmark", 1, label="sec:bench")
    dm = bench["domains"]
    rows = []
    for d, label, data, task in (("acs", "Census income", "US Census ACS 1-year PUMS persons and households, "
                                  "CA/TX/NY [@acspums]", "income > $50k"),
                                 ("tlc", "NYC taxi", "TLC yellow-taxi trips, 50 months [@nyctlc]",
                                  "tip ≥ 20% of fare"),
                                 ("news", "News sections", "HuffPost News Category [@misra2022]",
                                  "27 sections")):
        D = dm[d]
        nrows = sum(D["bronze_rows"].values())
        rows.append([label, P._cites(data), f"{D['first']}–{D['last']} ({D['periods']} periods)",
                     f"{nrows:,}", str(len(D["components"])), task,
                     str(sum(bench["cases"][d].values()))])
        P.ev(nrows, "d", "data/bronze/BRONZE_MANIFEST.json", f"{d} bronze rows")
    P.table(["Domain", "Source", "Periods", "Records", "Steps", "Task", "Cases"], rows,
            "Benchmark domains. Records are the sampled raw ('bronze') rows used by the pipelines (ACS: 30% of "
            "households; taxi: 150,000 trips per month from January, April, July and October of each year plus "
            "three months around schema changes; news: all records). Steps: pipeline components.", "domains",
            col_widths_cm=[2.1, 4.4, 2.8, 1.8, 1.4, 2.1, 1.2])
    ev_rows, seen_ev = [], set()
    for d, label in (("acs", "Census"), ("tlc", "Taxi"), ("news", "News")):
        for e in bench["events"][d]:
            ch = e["change"] if len(e["change"]) < 95 else e["change"][:92] + "…"
            key = (label, str(e.get("period") or e.get("year")))
            if key in seen_ev:        # person and housing files changed together
                continue
            seen_ev.add(key)
            ev_rows.append([label, key[1], ch])
    P.para(
        "**Real source changes.** {tab:events} lists the published schema changes we verified in the raw files. "
        "Several coincide with genuine world changes: COVID-19 (2020), New York's congestion pricing (January "
        "2025, together with the new fee column) and an airport-fee increase from $1.25 to $1.75 in April 2023, "
        "the same quarter in which the column was renamed from airport_fee to Airport_fee.")
    P.table(["Domain", "Period", "Published change"], ev_rows, "Source-schema events verified in the published "
            "files (period of first appearance).", "events", col_widths_cm=[1.6, 1.6, 12.5], font_pt=7.5)
    t2n = len(bench.get("t2", {}).get("differing", {}))
    P.para(
        f"**Library behaviours.** We created pandas 1.5.3, 2.2.3 and 3.0.6 environments and probed 28 idioms common "
        f"in pipeline code; {E(t2n, 'differing idioms', 'd', 'runs/t2_probe')} behave differently between them, "
        "including chained assignment that becomes a no-op under copy-on-write [@pandas3] (pandas warns; pipelines "
        "that suppress warnings, as ours do, fail silently) and timestamps "
        "whose integer representation changes resolution. Components declare their environment and run in it as "
        "subprocesses, so a library upgrade is a real execution, not a simulation.")
    cat_rows = []
    for d, label in (("acs", "Census"), ("tlc", "Taxi"), ("news", "News")):
        for k, v in bench["catalog"][d].items():
            if v["kind"] == "defect":
                cat_rows.append([label, v["tier"], v["component"], v["note"]])
    P.para(
        "**Defects and decoys.** Each domain has a catalog of changes (Appendix B): defects tied to a source change "
        "(T1: e.g. an adapter that maps the 2019 ACS relationship codes by subtracting 20 instead of using the "
        "official crosswalk), real library-upgrade defects (T2) and documented incident classes (T3: unit changes, "
        "stale reference data, copy-paste join keys, timezone mistakes, stuck defaults, encoders or vocabularies "
        "re-fitted at serving time), plus benign changes — refactors, harmless upgrades, adapters deployed early. "
        "A case pairs a reference period with a current period and applies nothing, benign changes only, one defect "
        "with up to two benign decoys, or two defects, on top of the correct pipeline of the current period, so "
        "that the change log alone never reveals the answer.")
    P.para(
        "**Ground truth by execution.** Records are split by hashed id into training (40%), serving (30%, what "
        "diagnosers see, with labels as the deployed pipeline produces them) and held-out (30%, grader only, with "
        "labels from the correct pipeline). For every case we execute every canonical action and every action a "
        "method recommends, and score it on the held-out records.")

    # ------------------------------------------------------------------ 7 setup
    P.heading("Experimental setup", 1, label="sec:setup")
    P.para(
        "**Baselines.** *Retrain on alarm* retrains if accuracy on labelled serving data dropped by at least 0.01. "
        "*Validation first* learns missing-value and range checks on reference data, routes a failure through "
        "lineage to the changed or source-reading component closest to the failing input, and otherwise retrains "
        "on alarm. *Observational attribution* blames the changed or source-coupled component that introduces the "
        "most drift on the dataflow graph, using archived outputs of both production runs (in the spirit of "
        "[@paleyes2023]). *Full rollback*, *bisection* and *pipeline-instance debugging* (BugDoc's shortcut "
        "[@lourenco2020]) re-run whole pipelines with known-good versions swapped in. The *LLM agent* receives "
        "the same monitoring report, lineage, change log and schema events as all methods; in the *tools* variant "
        "it may also call the rollback, replay, effect and boundary tests, up to eight calls, while its "
        "measured compute is below three full pipeline runs (checked before each call, so the last call may exceed "
        "it). We used gpt-5.6-luna on all cases and gpt-5.6-terra on test cases "
        "with a consequential defect (reasoning effort low, seed 0, responses cached for replay). All methods "
        "share one retrain rule.")
    P.para(
        "**Splits and protocol.** The census domain was used to develop the method and is reported as development "
        "data; the test set consists of the taxi and news cases whose defect types and periods were held out "
        f"({E(n_test, 'test cases', 'd')} cases). Hypotheses, endpoints, thresholds and a SHA-256 digest of all "
        f"code and configuration ({E(freeze['sha256'][:16], 'freeze digest', 's', 'runs/freeze.json')}…, "
        f"{E(freeze['n_files'], 'frozen files', 'd', 'runs/freeze.json')} files) were frozen before any test case "
        "was run, and the case runner refuses test cases if the digest differs. Changes made while developing the "
        "method are logged in the repository.")
    P.para(
        "**Metrics.** The primary endpoint is diagnosis correctness on cases with a consequential defect: the set "
        "of components to fix contains every consequential defect and only effective defects. Secondary metrics "
        "are false blame and missed defects on all cases; fragility, the accuracy a retrained model loses once the "
        "pipeline is repaired; and measured diagnosis compute. Confidence intervals are 95% cluster-bootstrap "
        "intervals (2,000 resamples; clusters are domain × defect signature); pairwise tests are Holm-corrected.")

    # ------------------------------------------------------------------ 8 results
    P.heading("Results", 1, label="sec:results")
    P.heading("Main results", 2)
    rows, bold = [], set()
    for i, m in enumerate(methods):
        c_all, n1 = mean(test, m, cons)
        c_news, _ = mean(test, m, lambda r: cons(r) and r["domain"] == "news")
        c_tlc, _ = mean(test, m, lambda r: cons(r) and r["domain"] == "tlc")
        c_sil, _ = mean(test, m, silent)
        fb, _ = mean(test, m, lambda r: True, "false_blame")
        ms, _ = mean(test, m, lambda r: True, "missed_defect")
        fr, _ = mean(test, m, cons, "fragility")
        cs, _ = mean(test, m, lambda r: True, "cost_s")
        for v, w in ((c_all, "pooled"), (c_news, "news"), (c_tlc, "tlc"), (c_sil, "silent"), (fb, "false blame"),
                     (ms, "missed"), (fr, "fragility"), (cs, "compute")):
            P.ev(v, ".3f", src, f"Table main: {m} {w}")
        if m.endswith("@terra"):          # run only on test cases with a consequential defect
            fb = ms = cs = float("nan")
        rows.append([NAMES[m], f3(c_all), f3(c_news), f3(c_tlc), f3(c_sil), f3(fb), f3(ms), f3(fr),
                     "–" if cs != cs else f"{cs:.1f}"])
        if m == "dod":
            bold.add(i)
    n_news_c = mean(test, "dod", lambda r: cons(r) and r["domain"] == "news")[1]
    n_tlc_c = mean(test, "dod", lambda r: cons(r) and r["domain"] == "tlc")[1]
    P.table(["Method", f"Diagnosis, all (n={n_news_c + n_tlc_c})", f"News (n={n_news_c})",
             f"Taxi (n={n_tlc_c})", f"Silent (n={n_sil})", "False blame", "Missed", "Fragility", "Compute (s)"],
            rows, f"Test-split results ({n_test} cases). The diagnosis columns give the share of cases with a "
            "consequential defect in which the method's fix set was correct; false blame and missed defects are "
            "over all test cases; fragility (over cases with a consequential defect) is the accuracy lost by the "
            "chosen model after a later pipeline repair; "
            "compute is the measured re-execution time per case. The gpt-5.6-terra agents were run only on cases "
            "with a consequential defect, so their all-case columns are empty.", "main",
            col_widths_cm=[4.4, 1.7, 1.3, 1.3, 1.3, 1.3, 1.2, 1.4, 1.4], font_pt=7.2, bold_rows=bold)
    P.figure(FIG / "correctness_by_domain.png", "Correct diagnosis on test cases with a consequential defect, by "
             "domain. Rolling components back (DoD without boundary test, pipeline-instance debugging) suffices on "
             "taxi data, where most defects are unforced; on news data every later period contains a forced change "
             "(a refreshed section table), which rollback-based methods mistake for the defect.",
             "domain", width_cm=14.5)

    P.heading("H1: monitoring cannot see silent defects", 2)
    h1 = H["test"]["H1"]
    P.para(
        f"Of the {E(n_news_c + n_tlc_c, 'consequential test cases', 'd')} test cases "
        f"with a consequential defect, {E(n_sil, 'silent consequential test cases', 'd')} passed every validation "
        f"check on the model inputs. Retrain-on-alarm and validation-first diagnosed "
        f"{E(h1['retrain_on_alarm']['silent'][0], 'H1 retrain silent')} and "
        f"{E(h1['validation_first']['silent'][0], 'H1 validation silent')} of them, and observational attribution "
        f"{E(h1['observational_attribution']['silent'][0], 'H1 obs silent')}, as Theorem 1 predicts "
        "({fig:silent}). Validation-first did better on loud defects "
        f"({E(h1['validation_first']['loud'][0], 'H1 validation loud')}), a gap of "
        f"{E(h1['validation_first']['loud'][0] - h1['validation_first']['silent'][0], 'H1 validation loud-silent')}"
        + (" that meets" if h1['validation_first']['loud'][0] - h1['validation_first']['silent'][0] >= 0.15
           else " that falls short of") + " the pre-registered 0.15. "
        "The LLM agent that reads the monitoring report scored "
        f"{E(h1['llm_report@luna']['silent'][0], 'H1 llm silent')} on silent defects — above the pre-registered "
        "bound of 0.35 for H1, below its disproof threshold of 0.60 — but at a false-blame rate of "
        f"{E(mean(test, 'llm_report@luna', lambda r: True, 'false_blame')[0], 'llm report false blame')} on all "
        "test cases: it mostly blames changed components, which is what the change log, not monitoring, offers "
        f"(gpt-5.6-terra with the same report: {E(mean(test, 'llm_report@terra', silent)[0], 'H1 terra silent')}). "
        "H1 is therefore supported for monitoring signals and partly contradicted for an agent that reasons over "
        "the change log.")
    P.figure(FIG / "silent_loud.png", "Correct diagnosis on silent (pass all validation checks) and loud "
             "consequential test defects. Methods left of the dotted line see monitoring data only.", "silent",
             width_cm=14.0)

    P.heading("H2: interventions resolve them", 2)
    P.para(
        f"DoD diagnosed {E(dod_c, 'dod primary')} of consequential test defects, against "
        f"{E(best_c, 'best baseline primary')} for the best baseline ({NAMES[best].lower()}). The paired difference "
        f"of {E(t2['diff'], 'H2 diff', '+.2f')} (95% CI [{E(t2['ci'][0], 'H2 ci lo', '+.2f')}, "
        f"{E(t2['ci'][1], 'H2 ci hi', '+.2f')}], Holm-adjusted p = {E(t2['p_holm'], 'H2 p holm', '.3f')}) "
        + ("is significant but below the pre-registered minimum effect of 0.15, so **H2 is narrowly not met on the "
           "pooled test set**." if (h2_sig and not h2_met) else
           ("meets the pre-registered criterion (**H2 supported**)." if h2_met else
            "is not significant (**H2 not supported**).")) + " The domains disagree sharply. On news, DoD was correct in every consequential case "
        f"({E(news_d, 'news dod')}; best baseline: {NAMES[news_best_m].lower()}, {E(news_best, 'news best baseline')}; "
        f"pipeline-instance debugging {E(news_b, 'news bugdoc')}). On taxi data it reached {E(tlc_d, 'tlc dod')}, "
        f"below its own rollback-only ablation ({E(tlc_nb, 'tlc dod no boundary')}) and the best baselines "
        f"(pipeline-instance debugging and bisection, both {E(tlc_best, 'tlc best baseline')}). Section 8.6 traces the taxi result to a "
        "single event.")

    P.heading("H3: cost and test selection", 2)
    h3 = H["test"]["H3"]
    P.para(
        f"DoD used {E(h3['cost_dod'][0], 'dod compute', '.1f')} s of measured compute per case, more than "
        f"pipeline-instance debugging ({E(h3['cost_bugdoc'][0], 'bugdoc compute', '.1f')} s), because its boundary "
        "tests re-execute components on neighbouring periods ({fig:cost}). Under a budget of one full pipeline "
        f"run, ordering tests by evidence per cost reached {E(h3['dod_b1'][0], 'dod_b1')} against "
        f"{E(h3['dod_b1_uniform'][0], 'dod_b1_uniform')} for pipeline order (difference "
        f"{E(h3['b1_diff']['diff'], 'H3 diff', '+.2f')}, 95% CI [{E(h3['b1_diff']['ci'][0], 'H3 lo', '+.2f')}, "
        f"{E(h3['b1_diff']['ci'][1], 'H3 hi', '+.2f')}]): H3's ordering claim holds in direction, but the evidence "
        "is weak, and DoD is not cheaper than pipeline-instance debugging.")
    P.figure(FIG / "cost.png", "Measured diagnosis compute against correct diagnosis (pooled test split).", "cost",
             width_cm=11.5)

    P.heading("H4: outcomes", 2)
    tt = H["test"]["tests"]
    P.para(
        "DoD missed fewer consequential defects than retrain-on-alarm "
        f"({E(tt['missed_defect: dod - retrain_on_alarm']['diff'], 'H4 miss vs retrain', '+.2f')}) and "
        f"validation-first ({E(tt['missed_defect: dod - validation_first']['diff'], 'H4 miss vs val', '+.2f')}), "
        "and blamed fewer healthy components than validation-first "
        f"({E(tt['false_blame: dod - validation_first']['diff'], 'H4 blame vs val', '+.2f')}), all significant "
        "after Holm correction. It blamed more than retrain-on-alarm, which never blames anything "
        f"({E(tt['false_blame: dod - retrain_on_alarm']['diff'], 'H4 blame vs retrain', '+.2f')}). Retraining "
        "on corrupted features often recovers accuracy for the moment: the models chosen by retrain-on-alarm lost "
        f"{E(-tt['fragility: dod - retrain_on_alarm']['diff'], 'H4 fragility gap')} more accuracy than DoD's once "
        "the pipeline was repaired. H4 is supported except for false blame against retrain-on-alarm.")

    P.heading("H5: the predicted limit, and where it bites", 2)
    h5 = H["test"]["H5"]
    P.para(
        f"On source-forced (T1) consequential defects DoD was correct in {E(h5['dod'][0], 'H5 dod')} of cases and "
        f"its rollback-only ablation in {E(h5['dod_no_boundary'][0], 'H5 no boundary')} "
        f"(n = {E(h5['dod'][1], 'H5 n', 'd')}): without the boundary test, rollback cannot certify a forced change, "
        "as Theorem 3 states. The same assumption failed on taxi data. All of DoD's taxi test false blames "
        f"({E(post['P4']['tlc_test_cases_with_false_blame'], 'P4 cases', 'd', 'runs/final/posthoc.json')} cases) "
        "fall on cases whose periods straddle April 2023, and "
        f"{E(post['P4']['boundary_flags']['2023-04:airport_fee'], 'P4 airport flags', 'd', 'runs/final/posthoc.json')} "
        "of them come from a single boundary flag: the airport-fee column at the April-2023 schema event, where "
        "the fee itself rose from $1.25 to $1.75 in the same quarter the column was renamed (the remaining "
        f"{E(post['P4']['boundary_flags'].get('effect test:trip_adapter', 0), 'P4 effect-test blames', 'd', 'runs/final/posthoc.json')} "
        "come from effect tests on the same adapter). The world jumped exactly at the schema change; the boundary "
        "test, as designed, attributed the jump to the adapter.")

    P.heading("LLM agents", 2)
    lt = mean(test, "llm_tools@luna", cons)[0]
    lr = mean(test, "llm_report@luna", cons)[0]
    txt = (f"With only the monitoring report, the agent (gpt-5.6-luna) diagnosed {E(lr, 'llm report cons')} of "
           f"consequential defects; with the re-execution tools, {E(lt, 'llm tools cons')}.")
    if any("llm_tools@terra" in p for p in test):
        lt2 = mean(test, "llm_tools@terra", cons)[0]
        lr2 = mean(test, "llm_report@terra", cons)[0]
        txt += (f" The larger gpt-5.6-terra reached {E(lr2, 'terra report cons')} and {E(lt2, 'terra tools cons')} "
                "on the same cases.")
    fails, lm = 0, 0
    for r in recs:
        if r["split"] != "test" or r["case"]["domain"] != "news" or not r["gt"]["consequential"]:
            continue
        for tag in ("llm_tools@luna", "llm_tools@terra"):
            d = r["methods"].get(tag)
            if not d:
                continue
            fix, eff, cs = set(d["fix"]), set(r["gt"]["defective"]), set(r["gt"]["consequential"])
            if not (cs <= fix <= eff):
                fails += 1
                lm += "label_map" in ((fix - eff) | (cs - fix))
    txt += (" Tools help, and the larger model uses them better. Where the agents failed on news, it was mostly "
            f"over the section table: {E(lm, 'llm news failures involving label_map', 'd')} of "
            f"{E(fails, 'llm news failures', 'd')} failures of the two tool-using agents either missed a stale table or blamed a "
            "correctly refreshed one — the forced change that Theorem 3 singles out. Including the pilot, all LLM "
            f"calls in this study cost {E(spent, 'total API spend', '.2f', 'runs/cost_ledger.json')} USD.")
    P.para(txt)

    P.heading("Post-hoc analyses (not pre-registered)", 2)
    P.para(
        f"Restricting the taxi test set to the {E(post['P2']['n_tlc_cases'], 'P2 n', 'd', 'runs/final/posthoc.json')} "
        "cases whose periods do not straddle April 2023, DoD diagnosed "
        f"{E(p2_d, 'P2 dod', '.2f', 'runs/final/posthoc.json')} of consequential defects with no false blame, "
        f"against {E(p2_b, 'P2 bugdoc', '.2f', 'runs/final/posthoc.json')} for pipeline-instance debugging; pooled "
        "with news, the difference to the best baseline on that subset "
        f"({NAMES[post['P2_best_baseline']['method']].lower()}) would be "
        f"{E(post['P2_pooled_with_news'][post['P2_best_baseline']['method']]['diff'], 'P2 pooled diff vs best', '+.2f', 'runs/final/posthoc.json')}. "
        "We report this only to locate the failure: excluding an inconvenient event after seeing the results is "
        "not evidence for the method. A heuristic that blames every changed component was correct in "
        f"{E(post['P1']['blame_all_changes']['news']['mean'], 'blame all news', '.2f', 'runs/final/posthoc.json')} "
        f"(news) and {E(post['P1']['blame_all_changes']['tlc']['mean'], 'blame all tlc', '.2f', 'runs/final/posthoc.json')} "
        "(taxi) of consequential cases, confirming that the change log alone does not reveal the answer.")

    P.heading("Development domain (census)", 2)
    acs = [p for p in dev if next(iter(p.values()))["domain"] == "acs"]
    a_d = mean(acs, "dod", cons)
    a_rows = []
    for m in ("retrain_on_alarm", "validation_first", "observational_attribution", "bugdoc_shortcut",
              "llm_tools@luna", "dod_no_boundary", "dod"):
        v, n = mean(acs, m, cons)
        P.ev(v, ".3f", "runs/final (dev split, acs)", f"acs dev {m}")
        a_rows.append([NAMES[m], f3(v)])
    P.para(
        f"On the {E(len(acs), 'acs cases', 'd', 'runs/final')} census cases, which were used to develop the method "
        f"and are therefore in-sample, DoD diagnosed {E(a_d[0], 'acs dod', '.2f', 'runs/final (dev split, acs)')} "
        f"of the {E(a_d[1], 'acs cons n', 'd', 'runs/final (dev split, acs)')} consequential defects "
        "({tab:acs}).")
    P.table(["Method", "Diagnosis (consequential)"], a_rows, "Census (development domain): correct diagnosis on "
            "cases with a consequential defect. In-sample; not evidence of generalisation.", "acs",
            col_widths_cm=[6.0, 4.0])

    # ------------------------------------------------------------------ 9 discussion
    P.heading("Discussion and threats to validity", 1, label="sec:disc")
    P.para(
        "**What the results say.** Monitoring alone cannot separate silent defects from drift, and re-execution "
        "can, but only for changes that are not forced by a data source. Forced changes are common — every source "
        "schema change forces one — and they are where both pipeline-instance debugging and the LLM agents went "
        "wrong on news data. Our boundary test is one way to handle them; its smoothness assumption held on news "
        "data, held in all but one census case, and failed on taxi data at one real event. A deployment would combine the boundary test "
        "with a second line of evidence for forced components, such as an overlap period in which the provider "
        "publishes both encodings, or a contract stating which quantities changed.")
    P.para(
        "**Requirements.** DoD needs archived intermediate outputs, reproducible component versions (including "
        "library environments) and column-level lineage. Lakehouse layers and pipeline versioning provide the "
        "first two in many organisations; the third is supported by lineage tools but is not universal.")
    P.para(
        "**Threats to validity.** (i) Many defects are injected from documented incident classes rather than "
        "replayed incidents; the T1 and T2 defects are real source and library behaviours, but their particular "
        "faulty adapters are our constructions. (ii) Three pipelines of 4–7 components are small next to "
        "industrial ones; cost results may not transfer. (iii) The census domain informed the method's design and "
        "is reported as development data only. (iv) The consequential threshold and the retrain rule shape the "
        "ground truth; we fixed them before the test run. (v) The LLM agents were run with one prompt, low "
        "reasoning effort and at most eight tool calls; stronger prompting may change their results. (vi) The "
        "pooled primary hypothesis was not met as pre-registered; the per-domain and post-hoc results are "
        "descriptive.")

    P.heading("Conclusion", 1)
    P.para(
        "Telling drift from a broken pipeline is not a matter of better drift statistics: for silent defects it is "
        "impossible from monitoring data, provably and in practice. Re-executing components at their known-good "
        "versions resolves unforced changes exactly, and changes forced by data sources need an explicit extra "
        "assumption that can and does fail. We release the benchmark, code and records so that diagnosers can be "
        "compared on these distinctions.")

    P.heading("Declarations", 1, numbered=False)
    P.para("**Funding.** [To be completed by the authors.]")
    P.para("**Competing interests.** [To be completed by the authors.]")
    P.para("**Use of AI tools.** [To be completed by the authors.]")
    P.para("**Data and code availability.** All data are public: ACS PUMS (U.S. Census Bureau), NYC TLC trip "
           "records, and the HuffPost News Category dataset. Code, benchmark definitions, raw case records and a "
           "replay script that needs no API keys will be released at [repository link].")
    P.references()

    # ------------------------------------------------------------------ appendices
    P.doc.add_page_break()
    P.heading("Appendix A: Proofs", 1, numbered=False)
    P.para("**Theorem 1.** A monitoring-only diagnostic φ is a (possibly randomised) measurable function of "
           "observations whose joint law is identical under (D, σ, θ) and (D′, σ, θ′), and the change logs are "
           "identical by assumption; hence the output law of φ is identical, and P[φ = defect] is the same under "
           "both. Its type-I error on the non-defective configuration plus its type-II error on the defective one "
           "is therefore 1 − P[φ = defect] + P[φ = defect] = 1 at best. ∎")
    P.para("**Corollary 1.** (⇐) Let the corrupted law of (X, Y) be supported in ℐ × 𝒴. Choose a measurable "
           "selection w(x) ∈ P_θ*^{-1}(x) ∘ σ^{-1} for x ∈ ℐ and push the corrupted law forward through "
           "(x, y) ↦ (w(x), y) to obtain D′; then the correct pipeline applied under D′ produces the corrupted law. "
           "(⇒) Mass outside ℐ is impossible under every non-defective configuration; a support test that flags any "
           "record outside ℐ has no false alarms and detects the defect unless all n records fall in ℐ, which has "
           "probability (1 − ε)ⁿ. ∎")
    P.para("**Theorem 2.** With deterministic components and θ*_c = θ⁰_c, c is an effective defect on the current "
           "inputs I_c iff f_c^{θ_c}(I_c) ≠ f_c^{θ⁰_c}(I_c), which is exactly the comparison the rollback test makes "
           "on archived inputs. Applying the test to every changed component in topological order and replacing the "
           "differing ones yields P_θ*(R) on the current records, after which the remaining gap involves only the "
           "world distribution. Each test executes one component once. ∎")
    P.para("**Theorem 3.** Every re-execution of pipeline components takes raw records as input; under "
           "(D, σ¹) and (D″, σ⁰) the raw records have the same law by assumption, so every statistic of any "
           "re-execution, and every monitoring statistic, has the same law in both configurations. The argument of "
           "Theorem 1 applies. ∎")
    P.para("**Proposition 4.** This is the classical result for sequential search with a single fault and "
           "independent test costs [@gluss1959]: an adjacent interchange argument shows that any order in which a "
           "candidate with a smaller p/k ratio precedes one with a larger ratio can be improved by swapping them.")
    P.heading("Appendix B: Defect catalog", 1, numbered=False)
    P.table(["Domain", "Tier", "Component", "Defect"], cat_rows, "Defect types (benign decoys omitted). T1: tied "
            "to a source change; T2: real library-upgrade behaviour; T3: documented incident class.", "catalog",
            col_widths_cm=[1.5, 1.0, 3.0, 10.2], font_pt=7.2)
    P.heading("Appendix C: Reproducibility and cost", 1, numbered=False)
    by_model = ledger.get("by_model", {})
    cost_rows = [[m, str(v["calls"]), f"{v['in'] + v.get('cached_in', 0):,}", f"{v['out']:,}", f"{v['usd']:.2f}"]
                 for m, v in by_model.items()]
    for m, v in by_model.items():
        P.ev(v["usd"], ".2f", "runs/cost_ledger.json", f"spend {m}")
    P.table(["Model", "Calls", "Input tokens", "Output tokens", "USD"], cost_rows, "API usage of all LLM calls, "
            "from the cost ledger. All responses are cached; the study replays without API keys.", "cost",
            col_widths_cm=[3.5, 2.0, 3.0, 3.0, 2.0])
    P.para(f"Protocol digest: {freeze['sha256']} over {freeze['n_files']} files, frozen at {freeze['frozen_at']}. "
           "Raw data: 118 published files with SHA-256 checksums in data/raw/MANIFEST.json. Pipelines ran on a "
           "16-core laptop CPU; no GPU was used.")
    P.heading("Appendix D: Evidence index", 1, numbered=False)
    P.para("Every number reported in the paper, with the file it was computed from (generated by the build).",
           size=8.5)
    ev_rows = [[str(i + 1), e["value"], e["what"], e["source"]] for i, e in enumerate(P.evidence)]
    P.table(["#", "Value", "Quantity", "Source"], ev_rows, "Evidence index.", "evidence",
            col_widths_cm=[0.8, 1.8, 7.5, 5.6], font_pt=6.5)
    out = ROOT / "paper" / "drift_or_defect.docx"
    P.save(out)
    (ROOT / "paper" / "evidence_index.json").write_text(json.dumps(P.evidence, indent=1), encoding="utf-8")
    print("written", out, len(P.evidence), "evidence entries")
    return dict(P.labels)


if __name__ == "__main__":
    first = main()            # pass 1 collects figure/table/section numbers for forward references
    main(first)
