"""Text of the paper, section by section (used by build_paper_v3.py). Numbers are never typed here: every number
comes from the context object C (saved records) through C.E / P.ev, which records it in the evidence index."""
from __future__ import annotations

import numpy as np

CONS = "Cases with a consequential defect (primary endpoint)"


def lname(names: dict, m: str) -> str:
    """Method name inside a sentence (lower-case first letter, except for LLM)."""
    n = names[m]
    return n if n.startswith("LLM") else n[0].lower() + n[1:]
EVT = "Cases spanning a published source change"
SIL = "Silent consequential defects"


# ======================================================================================== related work and setting
def related(P, C):
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
        "**Invariants.** Daikon [@ernst2007] infers likely program invariants from execution traces, and data "
        "validation systems learn constraints from data history [@schelter2018; @tu2023]. We use mined invariants "
        "differently: as evidence that is robust to arbitrary shifts of the world (Lemma 1), and we characterise "
        "the defects they cannot see (Theorem 5c). The rank argument behind our history rule is the one that "
        "underlies conformal prediction [@vovk2005].")
    P.para(
        "**Causal diagnosis of ML systems.** Paleyes and Lawrence [@paleyes2023] attribute anomalies on the "
        "dataflow graph observationally to input shift or faulty components; Leest et al. [@leest2025] propose "
        "causal system maps to separate software faults, data-quality issues and natural change, without an "
        "evaluation. Causal root-cause analysis for microservices [@ikram2022], including interventional approaches "
        "[@jha2024], and root-cause discovery and identifiability results [@li2025; @orchard2025] are the closest "
        "formal relatives; our results are their counterpart for data pipelines, where the confounder is the "
        "world itself. Observability for ML pipelines [@shankar2022] and studies of data-pipeline issues "
        "[@foidl2024; @sambasivan2021] motivate the problem.")


def problem(P, C):
    P.heading("Problem formulation", 1, label="sec:problem")
    P.para(
        "World records W ∈ Ω_W with labels Y ∈ Ω_Y follow a distribution D from a family ℱ of distributions we are willing "
        "to entertain (covariate, label and concept shift). A *source encoding* σ turns world records into "
        "published raw records R = σ(W) (layout, units, code lists). A pipeline is a directed acyclic graph of "
        "deterministic components; with versions θ (code, configuration, reference artifacts, library environment) "
        "it computes features X = P_θ(R). θ⁰ is the version deployed when the model h was trained; θ∗ is the "
        "*specification* for the current period — the pipeline a careful engineer would run on the current "
        "sources. A component c is *changed* if θ_c ≠ θ⁰_c, *forced* if the specification itself differs from the "
        "reference (θ∗_c ≠ θ⁰_c, e.g. an adapter rewritten for a new layout), and an *effective defect* if "
        "replacing θ_c by θ∗_c changes the pipeline output on the current records. A raw-reading component (an "
        "*adapter*) maps published records to semantic records S = A(R); the correct adapter for period t "
        "satisfies A∗_t ∘ σ_t = s, where s : Ω_W → Ω_S is the semantic content the provider publishes.")
    P.para(
        "A *monitoring-only* diagnostic sees samples of the joint law of (P_θ(σ(W)), Y), reference statistics, the "
        "lineage graph and the change log (which components changed and in which aspect). An *interventional* "
        "diagnostic may in addition re-execute components on archived inputs. The actions are fix(S) for a set of "
        "components S, retrain, fix(S)+retrain and nothing. We call a defect *consequential* if fixing it changes "
        "the held-out accuracy of the nothing or the retrain action by at least 0.002; the correct action fixes the "
        "consequential defects and retrains iff retraining after the fix gains more than 0.01 accuracy. A "
        "diagnosis is *correct* if the set of components it would fix contains every consequential defect and "
        "only effective defects.")


# ======================================================================================================= theory
def theory(P, C):
    P.heading("Identifiability", 1, label="sec:theory")
    P.para("We state the results here and give proofs in Appendix A. Theorems 1–3 and Proposition 4 were the basis "
           "of round 1; Lemma 1, Theorem 5 and Proposition 7 were added after round 1, and Propositions 8–10 after "
           "round 2, each from development data only ({sec:setup}).")
    P.heading("What monitoring and re-execution can identify", 2)
    P.para(
        "**Theorem 1 (observational equivalence of silent defects).** Let (D, σ, θ) be defective. If some D′ ∈ ℱ "
        "and some non-defective θ′ with the same change-log signature give the same joint law of features and "
        "labels, then every monitoring-only diagnostic outputs \"defect\" with the same probability under both "
        "configurations; its type-I plus type-II error on the pair is at least 1.")
    P.para(
        "**Corollary 1 (image characterisation).** If ℱ contains all distributions on world records and labels, "
        "a defect is monitoring-equivalent to a world change if and only if its corrupted features lie almost "
        "surely in the image Img = P_θ∗(σ(Ω_W)) of the correct pipeline. A defect that puts mass ε > 0 outside Img is "
        "detected by a support check against Img with probability 1 − (1 − ε)ⁿ from n records.")
    P.para(
        "Data validation therefore catches exactly the *loud* defects; *silent* ones — inside the image — are "
        "invisible to drift tests, validation, label monitoring and any learned combination of them, unless ℱ is "
        "restricted, for example by a prior over which components tend to change.")
    P.para(
        "**Theorem 2 (interventional identification of unforced changes).** Let components be deterministic, the "
        "intermediate outputs of the production run be archived, and the reference version of a changed component "
        "c be reproducible. If c was not forced (θ∗_c = θ⁰_c), the rollback test — run θ⁰_c on c's current inputs "
        "and compare with c's current output — returns *differ* iff c is an effective defect on the current data. "
        "Rolling back all components that differ yields the correct pipeline's output, so the remaining "
        "performance gap is attributable to the world; this needs at most |Δ| single-component executions for a "
        "change set Δ.")
    P.para(
        "**Theorem 3 (the limit: source-forced changes).** Let the source encoding change from σ⁰ to σ¹. If some "
        "D″ ∈ ℱ satisfies σ¹#D = σ⁰#D″, no diagnostic using monitoring and any re-execution of pipeline "
        "components separates (D, σ¹) from (D″, σ⁰). The same holds for the correctness of an adapter written for "
        "σ¹: it is a property of σ¹, which no re-execution observes.")
    P.para(
        "**Proposition 4 (test ordering).** Under a single-fault prior p_c with test costs k_c, testing candidates "
        "in decreasing p_c/k_c minimises the expected cost of finding the faulty component (sequential fault search "
        "with test costs goes back to [@gluss1959]).")
    P.heading("Side information for forced changes", 2)
    P.para(
        "Theorem 3 means that a forced change can only be judged with side information. Round 1 used one "
        "assumption, *world smoothness at published changes*: a component's output should not jump at a change "
        "much more than it moves between ordinary periods. Its weak point is that providers change layouts *when "
        "the world changes* (a new fee needs a new column). Two further kinds of evidence do not depend on the "
        "world staying still.")
    P.para(
        "**Assumption (I), invariant stability.** An *invariant* of the semantic schema is a measurable "
        "g : Ω_S → {0, 1} (1 = violated) whose violation rate under the correct adapter, v_t = P_{D_t}[g(s(W)) = 1], "
        "is small and does not increase at the change by more than its largest increase over the m preceding "
        "transitions. (I) is a statement about the provider's *process* (accounting identities, business rules, "
        "timestamp order), not about the distribution of the world.")
    P.para(
        "**Lemma 1 (region invariance).** Let g = 1[s ∉ A] for a region A ⊂ Ω_S that contains the support of s(W) "
        "under every world distribution the provider can produce in both periods. Then (I) holds for every world "
        "shift D_{e−1} → D_e, however large, that keeps s(W) inside A.")
    P.para(
        "**Theorem 5 (invariant evidence for forced changes).** Let A_e be the deployed adapter at the change e, "
        "Δ = {w : A_e(σ_e(w)) ≠ A∗_e(σ_e(w))} the records it gets wrong, and V ⊂ Δ the wrong records it moves out "
        "of the invariant region. (a) *Detection:* the violation rate of the deployed output satisfies "
        "v̂_e ≥ v_e − P(Δ \\ V) + P(V); if P(V) exceeds the provider-side change allowed by (I), the deployed "
        "adapter is distinguishable from the correct one by the violation rate alone, for every world "
        "distribution satisfying (I). (b) *World-robustness:* under (I) and a correct adapter, the rule \"flag if "
        "the violation-rate increase at the change exceeds the largest increase over the m preceding transitions\" "
        "errs with probability at most 1/(m+1) if the increases are exchangeable, and never under Lemma 1. (c) "
        "*Blind defects:* if P(V) = 0 — the defect maps every record it corrupts into the invariant region — the "
        "invariant carries no evidence and Theorem 3 applies again.")
    P.para(
        "**Corollary 2 (excusing a jump).** If an invariant determines a jumping column k given other columns z "
        "(support, sum and difference identities), the invariant is intact at the change, and the z columns do "
        "not jump themselves, the jump of k is consistent with a correct adapter, whatever its size.")
    P.para(
        "**Proposition 7 (history rule).** Let the world-induced change statistics J_1, …, J_m of the m ordinary "
        "transitions before a change and J_e of the change transition be exchangeable for a correct pipeline. The "
        "rule \"flag if J_e > max(J_1, …, J_m)\" has false-flag probability at most 1/(m+1) per column; with L "
        "columns at most L/(m+1). Round 1 compared J_e with a single transition, for which no bound below 1/2 "
        "holds.")
    P.heading("What round 2 taught: three conditions the tests silently assumed", 2)
    P.para(
        "**Proposition 8 (superseded layouts carry no evidence).** Let the source publish layouts σ_1, …, σ_k at "
        "changes e_1 < … < e_k ≤ p. The correct adapter for period p need only satisfy A∗_p ∘ σ_k = s: for any "
        "adapter A that is correct on σ_k there is an adapter A′, equal to A on the support of σ_k and failing on "
        "σ_j (j < k), that is also correct. Hence no test whose outcome depends on how the adapter treats an "
        "earlier layout is a consistent test of its correctness at p; a forced component may only be judged at "
        "the latest published change that touches its columns.")
    P.para(
        "**Proposition 9 (validity of a rollback counterfactual).** Theorem 2 and the effect test use the "
        "reference version θ⁰_c as a known-good counterfactual. If θ⁰_c maps semantic values that the current "
        "version reads to *missing* (it cannot parse the new layout), its output lies outside the image of the "
        "correct pipeline whenever the field is always defined, and the effect test compares the current version "
        "with a broken counterfactual; a non-improvement is then no evidence that the current version is "
        "harmless. Such a rollback must be treated like one that fails.")
    P.para(
        "**Proposition 10 (introduced missingness is world-robust evidence).** Let a semantic field k be always "
        "defined by the provider (a trip has a start time). This is a support invariant in the sense of Lemma 1. "
        "If a component's output has k missing on a fraction ρ > 0 of records while the inputs it reads k from are "
        "defined there, the component maps those records out of the invariant region; under (I) this happens with "
        "probability 0 for a correct component, whatever the world does. An increase of the missing rate of a "
        "component's output relative to the reference period that is not present in its inputs is therefore "
        "evidence of a defect that needs neither history nor smoothness.")
    P.para(
        "Propositions 8–10 do not weaken Theorem 3: they remove three ways in which a correct adapter was "
        "*mistaken* for a defect (judged on layouts it no longer needs to read; judged against a rollback that "
        "cannot read the current layout; judged without history that the deployed versions could read), and add "
        "one form of evidence for defects that destroy values.")


# ====================================================================================================== methods
def methods(P, C):
    P.heading("Methods", 1, label="sec:method")
    P.para(
        "All three versions receive the monitoring report of the reference and current periods, archived "
        "intermediate outputs of both production runs and of the deployment history, the lineage graph with "
        "column-level lineage to raw columns, the change log and the dated published changes of each source. "
        "Each version was frozen before it was evaluated; later versions change only how forced and source-coupled "
        "components are judged.")
    P.heading("DoD (round 1)", 2)
    P.bullets([
        "**Candidates.** Every changed component, and every unchanged component that depends — through "
        "column-level lineage — on a column touched by a published change and either reads the source or "
        "introduces drift at its node (a possible stale or latent defect). A changed component is *forced* if it "
        "depends on such a column.",
        "**Ordering.** Candidates are tested in decreasing ratio of prior to measured execution time "
        "(Proposition 4). The prior combines the drift *introduced* at the component's node (drift of its output "
        "columns beyond that of the same columns at its inputs, from archived outputs at no cost), drift and "
        "validation evidence on the model inputs it feeds, and source coupling.",
        "**Tests.** *Rollback* re-executes the reference version on the component's current inputs and compares "
        "outputs exactly; for an unforced component a difference is an effective defect (Theorem 2). For a forced "
        "component, an *effect* test propagates the rolled-back output to the deployed model; an improvement above "
        "τ = 0.003 marks it harmful; otherwise — and whenever the reference version cannot run on the new inputs, "
        "or the change alters the label or the set of records — a *boundary* test compares the component's output "
        "just before the published change with its output at the change, relative to the ordinary change between "
        "the two preceding periods. A jump above 3 times the ordinary change and above 0.05 PSI, new missing "
        "values, or lost records flag the component.",
        "**Action.** Fix every harmful or flagged component; retrain if the accuracy drop that remains after the "
        "fix is at least 0.01.",
    ])
    P.heading("DoD-2 (round 2)", 2)
    P.para(
        "DoD-2 changes only the boundary test. (i) *History rule:* the introduced change at a published change "
        "must exceed every one of the four preceding ordinary transitions of the deployment history (and 3 times "
        "their median, and 0.05 PSI) — Proposition 7 with m = 4, bound 1/5 per column. (ii) *Invariant evidence:* "
        "invariants of four templates — support (k ≠ 0 ⇔ z ∈ Z), order (a ≤ b), sum (t = a + b (+ c)) and "
        "difference (d = (b − a)/u) — are mined from the component's archived outputs in the history periods; one "
        "is kept if it holds on at least 98% of records in every history period and is violated at least five "
        "times as often after a random permutation of its first column. A violation increase of at least 0.01 at "
        "the change flags the component (Theorem 5a); a jump explained by an intact invariant is excused "
        "(Corollary 2).")
    P.heading("DoD-3 (round 3)", 2)
    P.para("DoD-3 implements Propositions 8–10 on top of DoD-2:")
    P.bullets([
        "**Latest-change rule (Proposition 8).** A source column is judged only at the latest published change, "
        "up to the current period, that touches it; a downstream component only at the latest change relevant to "
        "it. Failures to read earlier layouts are not evidence.",
        "**Valid counterfactuals (Proposition 9).** If the reference version leaves more than 1% more values "
        "missing than the current version on the columns where they differ, the rollback is treated as failed "
        "and the effect test is not used; conversely, a current version that leaves more than 10% of values "
        "missing that the reference version reads is harmful.",
        "**Readable history only.** The smoothness test uses up to four historical transitions and needs three "
        "(bound 1/4 by Proposition 7) where the archive has them; where the archive itself is shorter it uses what "
        "there is, down to one transition, as DoD did. If periods exist but the deployed versions cannot read them, "
        "the method abstains from the smoothness test instead of treating the failure as a flag. Transitions into "
        "periods with another published change relevant to the component are not ordinary and are left out of "
        "the history (the exchangeability assumption of Proposition 7). Free-text columns (more than 50 distinct "
        "values) are not compared.",
        "**Introduced missingness (Proposition 10).** Where no change could be judged otherwise, a component is "
        "flagged if it introduces at least 10 percentage points of missing values beyond its reference period "
        "while its inputs stay complete.",
    ])
    P.para(
        "Ablations: *DoD-3 without latest-change rule* keeps only the history and text-column changes; *DoD-3 "
        "without invariants* drops invariant evidence. All thresholds were fixed on development data and frozen.")


# ===================================================================================================== benchmark
def benchmark(P, C, NAMES):
    B = C.bench
    P.heading("Benchmark", 1, label="sec:bench")
    P.para(
        "The benchmark consists of nine executable pipelines over public data, added in three rounds; each round's "
        "domains were built before any method was run on them ({tab:domains}). The pipelines have four to seven "
        "components: a source adapter, feature and cleaning steps (some deployed in a pandas 1.5 environment), "
        "reference-data joins, and categorical encoding with a fitted artifact. Every domain has real, dated "
        "changes of the published files — found by profiling the raw files of every period, not from "
        "documentation alone — except the airline domain, whose history is republished in the current layout and "
        "which serves as a control.")
    srcs = {"acs": "US Census ACS 1-year PUMS [@acspums]", "tlc": "NYC TLC yellow-taxi trips [@nyctlc]",
            "news": "HuffPost News Category [@misra2022]", "divvy": "Divvy trip data [@divvy]",
            "hmda": "HMDA loan records [@hmda]", "bts": "BTS on-time performance [@bts]",
            "cabi": "Capital Bikeshare trip data [@cabi]", "fars": "NHTSA FARS crash file [@fars]",
            "landreg": "HM Land Registry Price Paid [@landreg]"}
    tasks = {"acs": "income > $50k", "tlc": "tip ≥ 20% of fare", "news": "27 sections",
             "divvy": "member vs casual", "hmda": "denied vs originated", "bts": "arrival delay ≥ 15 min",
             "cabi": "member vs casual", "fars": "two or more vehicles", "landreg": "new build"}
    rows, total_rows, total_cases = [], 0, 0
    for d, D in B["domains"].items():
        n_cases = sum(B["cases"][d].values())
        n_ev = len({(e.get("period") or e.get("year")) for e in B["events"][d]})
        total_rows += D["bronze_rows"]
        total_cases += n_cases
        rows.append([str(D["round"]), P._cites(srcs[d]), f"{D['first']}–{D['last']} ({D['periods']})",
                     P.ev(D["bronze_rows"], ",d", "runs/benchmark/tables_v3.json", f"{d} bronze rows"),
                     str(len(D["components"])), tasks[d], P.ev(n_ev, "d", "runs/benchmark/tables_v3.json",
                                                              f"{d} dated changes"),
                     P.ev(n_cases, "d", "runs/benchmark/tables_v3.json", f"{d} cases")])
    C.total_cases = total_cases
    P.table(["Round", "Source", "Periods", "Records", "Steps", "Task", "Changes", "Cases"], rows,
            "Benchmark domains. Records: sampled raw rows used by the pipelines (e.g. 100,000 trips per quarter "
            "for bike share, 150,000 records per period for taxi, mortgages, airlines and house sales; all records "
            "for news and crashes). Changes: periods with a dated published change from the first reference "
            f"period on. In total {total_rows:,} records and {total_cases:,} cases.", "domains",
            col_widths_cm=[1.1, 4.2, 2.9, 1.9, 1.1, 2.4, 1.3, 1.2], font_pt=7.2)
    P.ev(total_rows, ",d", "runs/benchmark/tables_v3.json", "total bronze rows")
    P.ev(total_cases, ",d", "runs/benchmark/tables_v3.json", "total cases")
    P.para(
        "**Real source changes.** Appendix B lists every change. They include renamed and reordered columns, "
        "new layouts after an operator's system change (both bike-share systems in 2020, in the quarter the "
        "pandemic began), recoded categories (member/casual; loan purpose and occupancy under amended Regulation C "
        "in 2018), changed units (mortgage amounts in dollars instead of thousands), removed fields (crash weather "
        "fields in 2020), a byte-order mark that appeared in a header for two years, timestamp formats with and "
        "without seconds or fractions, and coverage changes (non-standard house sales published from 2013). "
        "Several coincide with genuine world changes: COVID-19 (2020), an airport-fee rise in the quarter the "
        "taxi fee column was renamed (April 2023) and congestion pricing with its new column (January 2025).")
    P.para(
        "**Library behaviours.** We created pandas 1.5.3, 2.2.3 and 3.0.6 environments and probed idioms common "
        "in pipeline code; several behave differently, including chained assignment that becomes a no-op under "
        "copy-on-write [@pandas3] (pandas warns [@pandascow]; pipelines that suppress warnings fail silently) and "
        "timestamps whose integer representation changes resolution [@pandas3; @pandas65308]. Components declare their environment and "
        "run in it as subprocesses, so a library upgrade is a real execution, not a simulation.")
    P.para(
        "**Defects and decoys.** Each domain has a catalog of changes in five tiers (Appendix B): T1 defects tied "
        "to a published change (a stale mapping, a format not updated, a positional column mapping; cf. a renamed "
        "census field that broke a public benchmark library [@folktables22]); T2 real "
        "library-upgrade behaviours; T3 documented incident classes (unit errors, stale reference data, "
        "copy-paste join keys, swapped day and month, encoders re-fitted at serving time); T3r replays of public "
        "incidents [@folktables39; @nyctaxi3; @sklearn34549]; and benign changes — refactors, "
        "harmless upgrades, correct adapters. A case pairs a reference period with a current period and applies "
        "nothing, benign changes only, one defect with up to two benign decoys, or two defects, on top of the "
        "correct pipeline of the current period, so that the change log alone never reveals the answer.")
    P.para(
        "**Ground truth by execution.** Records are split by hashed id into training (40%), serving (30%, what "
        "diagnosers see) and held-out (30%, grader only, with labels from the correct pipeline). For every case we "
        "execute every canonical action and every action a method recommends, and score it on the held-out "
        "records.")


def protocol(P, C):
    P.heading("Evaluation protocol: three pre-registered rounds", 1, label="sec:setup")
    fr = C.freeze
    P.para(
        "We evaluated in three rounds. In each, hypotheses, endpoints, thresholds and a SHA-256 digest of all code "
        "and configuration were frozen before any test case was run, and the case runner refused test cases if "
        "the digest differed. After each round, the next version of the method was designed on data already "
        "seen — the earlier rounds' domains, from then on development data — and tested on fresh domains.")
    rows = []
    for k, dom, meth, hyp in ((1, "Census (development), taxi, news", "DoD", "H1–H5"),
                              (2, "Chicago bike share, mortgages, airlines", "DoD-2", "H6–H10"),
                              (3, "Washington bike share, crashes, house sales", "DoD-3", "H11–H14")):
        f = fr.get(k)
        rows.append([str(k), dom, meth, hyp,
                     (P.ev(f["sha256"][:12], "s", f"runs/{['freeze', 'freeze_v2', 'freeze_v3'][k - 1]}.json",
                           f"round {k} freeze digest") + "…") if f else "–",
                     P.ev(f["n_files"], "d", "runs/freeze*.json", f"round {k} frozen files") if f else "–"])
    P.table(["Round", "Test domains", "New method", "Hypotheses", "Digest", "Files"], rows,
            "The three pre-registered rounds. Every method of earlier rounds is run unchanged in later rounds.",
            "rounds", col_widths_cm=[1.2, 5.6, 2.2, 2.0, 2.6, 1.2], font_pt=7.5)
    P.para(
        "**Baselines.** *Retrain on alarm* retrains if accuracy on labelled serving data dropped by at least 0.01. "
        "*Validation first* learns missing-value and range checks on reference data, routes a failure through "
        "lineage to the changed or source-reading component closest to the failing input, and otherwise retrains "
        "on alarm. *Observational attribution* blames the changed or source-coupled component that introduces the "
        "most drift on the dataflow graph, using archived outputs of both production runs (in the spirit of "
        "[@paleyes2023]). *Full rollback*, *bisection* and *pipeline-instance debugging* (BugDoc's shortcut "
        "[@lourenco2020]) re-run whole pipelines with known-good versions swapped in. The *LLM agent* receives the "
        "same report, lineage, change log and published changes as all methods; in the *tools* variant it may also "
        "call the rollback, replay, effect and boundary tests, up to eight calls within a compute budget of three "
        "full pipeline runs. We used gpt-5.6-luna on all cases and gpt-5.6-terra on the test cases with a consequential "
        "defect (round 1: all of them; rounds 2 and 3: every third, within each round's API allowance; reasoning "
        "effort low, seed 0, responses cached for replay). All methods share one "
        "retrain rule.")
    P.para(
        "**Metrics.** The primary endpoint is diagnosis correctness on cases with a consequential defect. "
        "Secondary metrics are false blame (an effective defect is not required for a blamed component) and missed "
        "defects on all cases; fragility, the accuracy a retrained model loses once the pipeline is repaired; "
        "and measured diagnosis compute. Confidence intervals are 95% cluster-bootstrap intervals (2,000 "
        "resamples; clusters are domain × defect signature); tests within a round are Holm-corrected. Rounds are "
        "reported side by side and never pooled for a test.")


# ======================================================================================================= round 1
def round1(P, C, NAMES):
    test, dev, H, post = C.r1_test, C.r1_dev, C.r1_H, C.r1_post
    src = "runs/final (test split)"
    E = lambda v, w, fmt=".2f", s=src: P.ev(v, fmt, s, "R1 " + w)
    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    mean = C.r1_mean
    P.heading("Round 1: census, taxi and news (DoD)", 1, label="sec:r1")
    order = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
             "dod_no_boundary", "dod"]
    ms = [m for m in order if any(m in p for p in test)]
    rows, bold = [], set()
    for i, m in enumerate(ms):
        c_all = mean(test, m, cons)[0]
        c_news = mean(test, m, lambda r: cons(r) and r["domain"] == "news")[0]
        c_tlc = mean(test, m, lambda r: cons(r) and r["domain"] == "tlc")[0]
        c_sil = mean(test, m, silent)[0]
        fb = mean(test, m, lambda r: True, "false_blame")[0]
        if m.endswith("@terra"):
            fb = float("nan")
        rows.append([NAMES[m]] + [E(v, f"{m} {w}") if v == v else "–" for v, w in
                                  ((c_all, "pooled"), (c_news, "news"), (c_tlc, "tlc"), (c_sil, "silent"),
                                   (fb, "false blame"))])
        if m == "dod":
            bold.add(i)
    n_news = mean(test, "dod", lambda r: cons(r) and r["domain"] == "news")[1]
    n_tlc = mean(test, "dod", lambda r: cons(r) and r["domain"] == "tlc")[1]
    n_sil = mean(test, "dod", silent)[1]
    n_test = len(test)
    P.table(["Method", f"Correct, all (n={n_news + n_tlc})", f"News (n={n_news})", f"Taxi (n={n_tlc})",
             f"Silent (n={n_sil})", "False blame (all cases)"], rows,
            f"Round 1, test split ({n_test} cases). Correct diagnosis on cases with a consequential defect; false "
            "blame over all test cases. The terra agents were run only on cases with a consequential defect.",
            "r1", col_widths_cm=[5.0, 2.3, 1.8, 1.8, 1.8, 2.4], font_pt=7.5, bold_rows=bold)
    t2 = H["test"]["tests"]["primary: dod - best"]
    best = H["test"]["best_baseline"]
    h1 = H["test"]["H1"]
    h5 = H["test"]["H5"]
    tt = H["test"]["tests"]
    C.r1 = {"dod": mean(test, "dod", cons)[0], "best": mean(test, best, cons)[0], "best_m": best, "diff": t2,
            "n_sil": n_sil, "n_test": n_test}
    P.para(
        f"**H1 (monitoring cannot see silent defects): supported for monitoring signals.** Of the "
        f"{E(n_news + n_tlc, 'consequential test cases', 'd')} test cases with a consequential defect, "
        f"{E(n_sil, 'silent consequential cases', 'd')} passed every validation check on the model inputs. "
        f"Retrain-on-alarm and validation-first diagnosed {E(h1['retrain_on_alarm']['silent'][0], 'H1 retrain silent')} "
        f"and {E(h1['validation_first']['silent'][0], 'H1 validation silent')} of them, observational attribution "
        f"{E(h1['observational_attribution']['silent'][0], 'H1 obs silent')}. The LLM agent reading the same "
        f"report reached {E(h1['llm_report@luna']['silent'][0], 'H1 llm silent')} — above the bound of 0.35, below "
        "the disproof threshold of 0.60 — mostly by blaming changed components, which the change log rather than "
        "monitoring offers.")
    h2_met = t2["diff"] >= 0.15 and t2["ci"][0] > 0
    P.para(
        f"**H2 (interventions resolve them): narrowly not met.** DoD diagnosed "
        f"{E(C.r1['dod'], 'dod primary')} of consequential test defects against {E(C.r1['best'], 'best baseline')} for "
        f"the best baseline ({lname(NAMES, best)}); the difference {E(t2['diff'], 'H2 diff', '+.2f')} (95% CI "
        f"[{E(t2['ci'][0], 'H2 lo', '+.2f')}, {E(t2['ci'][1], 'H2 hi', '+.2f')}], Holm p = "
        f"{E(t2['p_holm'], 'H2 p', '.3f')}) "
        + ("met" if h2_met else "fell short of") + " the pre-registered minimum effect of 0.15. DoD was correct "
        f"on {E(mean(test, 'dod', lambda r: cons(r) and r['domain'] == 'news')[0], 'news dod')} of news cases and "
        f"{E(mean(test, 'dod', lambda r: cons(r) and r['domain'] == 'tlc')[0], 'tlc dod')} of taxi cases.")
    P.para(
        f"**H3–H4.** Ordering tests by evidence per cost under a one-run budget reached "
        f"{E(H['test']['H3']['dod_b1'][0], 'dod_b1')} against {E(H['test']['H3']['dod_b1_uniform'][0], 'dod_b1_uniform')} "
        "for pipeline order (weak evidence for H3); DoD used "
        f"{E(H['test']['H3']['cost_dod'][0], 'dod compute', '.1f')} s of compute per case, more than pipeline-instance "
        f"debugging ({E(H['test']['H3']['cost_bugdoc'][0], 'bugdoc compute', '.1f')} s). DoD missed fewer defects than "
        f"retrain-on-alarm ({E(tt['missed_defect: dod - retrain_on_alarm']['diff'], 'H4 miss vs retrain', '+.2f')}) "
        f"and its retrained models were less fragile: those chosen by retrain-on-alarm lost "
        f"{E(-tt['fragility: dod - retrain_on_alarm']['diff'], 'H4 fragility gap')} more accuracy once the pipeline "
        "was repaired.")
    P.para(
        f"**H5 (the predicted limit).** On forced (T1) consequential defects DoD was correct in "
        f"{E(h5['dod'][0], 'H5 dod')} of cases and its rollback-only ablation in "
        f"{E(h5['dod_no_boundary'][0], 'H5 no boundary')} (n = {E(h5['dod'][1], 'H5 n', 'd')}). The smoothness "
        "assumption failed on taxi data at one event: all "
        f"{E(post['P4']['tlc_test_cases_with_false_blame'], 'P4 cases', 'd', 'runs/final/posthoc.json')} taxi "
        "test cases with a false blame straddle April 2023, and "
        f"{E(post['P4']['boundary_flags']['2023-04:airport_fee'], 'P4 airport flags', 'd', 'runs/final/posthoc.json')} "
        "of them come from one boundary flag on the airport-fee column, which was renamed in the quarter the fee "
        "rose from $1.25 to $1.75. The world jumped exactly at the published change.")
    P.figure(C.FIG / "correctness_by_domain.png", "Round 1: correct diagnosis on test cases with a consequential "
             "defect, by domain.", "r1dom", width_cm=13.5)


# ======================================================================================================= round 2
def round2(P, C, NAMES):
    ph = C.r2_post
    P.heading("Round 2: three held-out domains (DoD-2)", 1, label="sec:r2")
    src = "runs/v2main/summary_v2.json"
    E = lambda v, w, fmt=".2f": P.ev(v, fmt, src, "R2 " + w)
    T = lambda t, m, k="diag_correct": C.tab(2, t, m, k)
    H = C.r2["hypotheses"]
    order = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
             "dod_no_boundary", "dod", "dod2"]
    rows, bold = [], set()
    for i, m in enumerate(order):
        vals = [T(CONS, m)[0]] + [T(f"Domain {d}, consequential defect", m)[0] for d in ("divvy", "hmda", "bts")]
        vals += [T(SIL, m)[0], T(EVT, m, "false_blame")[0] if "@terra" not in m else float("nan")]
        rows.append([NAMES[m]] + [E(v, f"{m} {w}") if v == v else "–" for v, w in
                                  zip(vals, ("pooled", "divvy", "hmda", "bts", "silent", "false blame events"))])
        if m in ("dod", "dod2"):
            bold.add(i)
    n = {d: T(f"Domain {d}, consequential defect", "dod")[1] for d in ("divvy", "hmda", "bts")}
    P.table(["Method", f"Correct, all (n={sum(n.values())})", f"Bike CHI (n={n['divvy']})",
             f"Mortgages (n={n['hmda']})", f"Airlines (n={n['bts']})", f"Silent (n={T(SIL, 'dod')[1]})",
             f"False blame at changes (n={T(EVT, 'dod')[1]})"], rows,
            "Round 2 (all cases are test cases). Correct diagnosis on cases with a consequential defect; false blame "
            "on all cases whose periods span a published change. The terra agents were run on the planned every-third "
            "sample of cases with a consequential defect until the per-job cost caps were reached: "
            f"{T(CONS, 'llm_tools@terra')[1]} of "
            f"{sum(-(-T(f'Domain {d}, consequential defect', 'dod')[1] // 3) for d in ('divvy', 'hmda', 'bts'))} "
            "cases, the first ones of the sample in run order.", "r2",
            col_widths_cm=[4.6, 1.9, 1.7, 1.8, 1.8, 1.7, 2.3], font_pt=7.2, bold_rows=bold)
    t = H["tests"]
    h6, h7 = t["H6 primary: dod2 - dod"], t["H7 false blame (cases spanning a source change): dod2 - dod"]
    h8 = [v for k, v in t.items() if k.startswith("H8 primary: dod2")][0]
    C.r2s = {"dod2": T(CONS, "dod2")[0], "dod": T(CONS, "dod")[0], "fb_dod": T(EVT, "dod", "false_blame")[0],
             "fb_dod2": T(EVT, "dod2", "false_blame")[0]}
    P.para(
        f"**H6–H8: not supported.** DoD-2 diagnosed {E(T(CONS, 'dod2')[0], 'dod2 primary')} of consequential "
        f"defects against {E(T(CONS, 'dod')[0], 'dod primary')} for DoD (H6: {E(h6['diff'], 'H6 diff', '+.2f')}, "
        f"Holm p = {E(h6['p_holm'], 'H6 p', '.2f')}); its false-blame rate on cases spanning a published change was "
        f"{E(T(EVT, 'dod2', 'false_blame')[0], 'dod2 fb events')} against {E(T(EVT, 'dod', 'false_blame')[0], 'dod fb events')} "
        f"(H7: {E(h7['diff'], 'H7 diff', '+.2f')}, Holm p = {E(h7['p_holm'], 'H7 p', '.2f')}); and it fell short "
        f"of the best baseline, the tool-using terra agent, by {E(-h8['diff'], 'H8 gap')} on the cases both were "
        f"run on (H8, n = {E(h8['n'], 'H8 n', 'd')}). Both DoD versions were perfect on the airline control "
        f"domain ({E(T('Domain bts, consequential defect', 'dod2')[0], 'bts dod2')}) and failed where the source "
        f"changed repeatedly: DoD-2 reached {E(T('Domain divvy, consequential defect', 'dod2')[0], 'divvy dod2')} "
        f"(DoD: {E(T('Domain divvy, consequential defect', 'dod')[0], 'divvy dod')}) on Chicago bike "
        f"share and {E(T('Domain hmda, consequential defect', 'dod2')[0], 'hmda dod2')} on mortgages, with DoD-2 false "
        f"blame of {E(T('Domain divvy', 'dod2', 'false_blame')[0], 'divvy dod2 fb')} and "
        f"{E(T('Domain hmda', 'dod2', 'false_blame')[0], 'hmda dod2 fb')} on all cases of those domains.")
    h9 = H["H9"]
    P.para(
        f"**H9 (replication of H1): disproved.** Retrain-on-alarm and validation-first again diagnosed "
        f"{E(h9['retrain_on_alarm']['silent'][0], 'H9 retrain silent')} and "
        f"{E(h9['validation_first']['silent'][0], 'H9 validation silent')} of the "
        f"{E(h9['retrain_on_alarm']['silent'][1], 'H9 n silent', 'd')} silent consequential defects, but "
        f"observational attribution reached {E(h9['observational_attribution']['silent'][0], 'H9 obs silent')}, "
        "above the disproof threshold of 0.60. This does not contradict Theorem 1, which concerns diagnostics "
        "that see only the joint law of features and labels: observational attribution also reads the change log "
        "and the archived outputs of every component, and blames the changed component that introduces drift. "
        "When the defect is the only change that moves its node's output, that suffices; H1's operationalisation "
        "lumped this method with pure monitoring, and round 2 showed the distinction matters.")
    h10 = H["H10"]
    P.para(
        f"**H10 (invariant evidence, descriptive).** No mined invariant flagged a component in any consequential "
        f"T1 case ({E(h10['dod2']['T1_inv_flag'][1], 'H10 n inv flagged', 'd')} of "
        f"{E(h10['dod2']['T1'][1], 'H10 n T1', 'd')}); DoD-2 without invariants made identical decisions. The "
        "history rule accounted for DoD-2's whole gain over DoD on T1 defects "
        f"({E(h10['dod2']['T1'][0], 'H10 dod2 T1')} vs {E(h10['dod']['T1'][0], 'H10 dod T1')}).")
    P.figure(C.FIG / "v2_correctness_by_domain.png", "Round 2: correct diagnosis on held-out cases with a "
             "consequential defect, by domain.", "r2dom", width_cm=13.5)
    P.para(
        "**Why it failed (analysis on round-2 data, which is development data from round 3 on).** We read the "
        "decisions behind every false blame. Three causes accounted for most of them, each a violation of a "
        "condition the tests had assumed without stating it: correct adapters were flagged for failing to read "
        "layouts the source had already replaced (the Chicago bike-share files changed at "
        f"{P.ev(len(C.bench['events']['divvy']), 'd', 'runs/benchmark/tables_v3.json', 'divvy dated changes from 2016-Q3')} "
        "dated points between 2016 and 2024; Proposition 8); the effect test compared a correct new adapter against a reference version that could "
        "not parse the new layout and therefore produced missing values (Proposition 9); and the boundary test "
        "treated the deployed versions' inability to read periods before a change as a flag (\"history that "
        "cannot be read\"). Keeping only the boundary flags raised at the latest published change that touches each "
        "flagged column (Proposition 8) lowers DoD's false-blame rate in the saved round-2 decisions from "
        f"{P.ev(ph['hmda']['false_blame'], '.2f', 'runs/v2main/posthoc_r2.json', 'R2 posthoc hmda fb')} to "
        f"{P.ev(ph['hmda']['false_blame_latest_only'], '.2f', 'runs/v2main/posthoc_r2.json', 'R2 posthoc hmda fb latest')} "
        f"on mortgages and from {P.ev(ph['divvy']['false_blame'], '.2f', 'runs/v2main/posthoc_r2.json', 'R2 posthoc divvy fb')} "
        f"to {P.ev(ph['divvy']['false_blame_latest_only'], '.2f', 'runs/v2main/posthoc_r2.json', 'R2 posthoc divvy fb latest')} "
        "on Chicago bike share — a post-hoc computation that motivated, but is not evidence for, DoD-3.")


# ======================================================================================================== stubs
def key_numbers(C) -> dict:
    """Headline numbers used before the results sections (computed from the same records)."""
    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    K = {}
    t = C.r1_H["test"]["tests"]["primary: dod - best"]
    K["r1_dod"] = C.r1_mean(C.r1_test, "dod", cons)[0]
    K["r1_best_m"] = C.r1_H["test"]["best_baseline"]
    K["r1_best"] = C.r1_mean(C.r1_test, K["r1_best_m"], cons)[0]
    K["r1_diff"], K["r1_lo"], K["r1_hi"] = t["diff"], t["ci"][0], t["ci"][1]
    K["r1_sil_n"] = C.r1_mean(C.r1_test, "dod", silent)[1]
    K["r2_dod2"] = C.tab(2, CONS, "dod2")[0]
    K["r2_best_m"] = C.r2["hypotheses"]["best_baseline"]
    K["r2_best"] = C.tab(2, CONS, K["r2_best_m"])[0]
    K["r3_dod3"] = C.tab(3, CONS, "dod3")[0]
    K["r3_best_m"] = C.r3["hypotheses"]["best_baseline"]
    K["r3_best"] = C.tab(3, CONS, K["r3_best_m"])[0]
    h = C.r3["hypotheses"]["tests"]
    K["r3_h11"] = [v for k, v in h.items() if k.startswith("H11")][0]
    K["r3_h13"] = h["H13 false blame (cases spanning a source change): dod3 - dod"]
    sil = [C.r1_H["test"]["H1"]["retrain_on_alarm"]["silent"], C.r2["hypotheses"]["H9"]["retrain_on_alarm"]["silent"],
           C.r3["hypotheses"]["H9"]["retrain_on_alarm"]["silent"]]
    K["sil_n_all"] = sum(n for _, n in sil)
    K["sil_retrain_max"] = max(v for v, _ in sil)
    val = [C.r1_H["test"]["H1"]["validation_first"]["silent"], C.r2["hypotheses"]["H9"]["validation_first"]["silent"],
           C.r3["hypotheses"]["H9"]["validation_first"]["silent"]]
    K["sil_val_max"] = max(v for v, _ in val)
    bc = C.by_change
    K["nochange_n"] = sum(bc[f"round{r}"]["no_change"]["dod"]["n"] for r in (1, 2, 3))
    K["nochange_dod_correct"] = sum(bc[f"round{r}"]["no_change"]["dod"]["diag_correct"] *
                                    bc[f"round{r}"]["no_change"]["dod"]["n"] for r in (1, 2, 3))
    base = [m for m in ("retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback",
                        "bisect", "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra",
                        "llm_tools@terra")]
    K["nochange_best_base"] = max(bc[f"round{r}"]["no_change"][m]["diag_correct"] for r in (1, 2, 3) for m in base
                                  if m in bc[f"round{r}"]["no_change"])
    K["change_dod"] = {r: max(bc[f"round{r}"]["change"][m]["diag_correct"] for m in ("dod", "dod2", "dod3")
                              if m in bc[f"round{r}"]["change"]) for r in (1, 2, 3)}
    K["r3_miss_dod3"] = C.tab(3, CONS, "dod3", "missed_defect")[0]
    K["r3_miss_obs"] = C.tab(3, CONS, "observational_attribution", "missed_defect")[0]
    K["spent"] = C.ledger["total_usd"]
    return K


def front(P, C):
    K = key_numbers(C)
    E = lambda v, w, fmt=".2f", s="runs/final; runs/v2main/summary_v2.json; runs/v3main/summary_v3.json": P.ev(v, fmt, s, "Abstract: " + w)
    P.title("Is It Model Drift or a Broken Pipeline? Intervention-Based Diagnosis of Production ML Degradation",
            "[Author names and affiliations withheld]",
            "Preprint. Code, benchmark, raw records and replay scripts: [repository link to be added]")
    P.heading("Abstract", 1, numbered=False)
    P.para(
        "When a production model degrades, teams usually retrain it, although the model sees the output of a data "
        "pipeline that changes all the time. We ask from what evidence a genuine change of the prediction problem "
        "can be told apart from a pipeline defect. We prove that a defect whose corrupted features stay in the "
        "image of the correct pipeline is invisible to every monitoring-only diagnostic; that re-executing a "
        "changed component at its known-good version identifies it exactly when the change was not forced by the "
        "data source; and that source-forced changes are identifiable by no re-execution at all. For forced "
        "changes we derive evidence that survives arbitrary world shifts (invariants, a rank-based history rule) "
        "and three conditions that such tests silently require. We release a benchmark of nine executable "
        "pipelines over public data from 2008 to 2026 with "
        f"{E(C.total_cases, 'total cases', ',d', 'runs/benchmark/tables_v3.json')} cases built on dated changes of "
        "the published files, real library-upgrade behaviours and replays of public incidents, with ground truth "
        "from executing every action, and evaluate three successive versions of an interventional diagnoser (DoD) "
        "in three pre-registered rounds, each on fresh domains. Retrain-on-alarm and validation-first diagnosed "
        f"none of the {E(K['sil_n_all'], 'silent consequential cases, all rounds', 'd')} silent consequential "
        "defects. On every consequential case without a published source change in its period range "
        f"({E(K['nochange_n'], 'consequential cases without a change', 'd', 'runs/posthoc_by_change.json')}), "
        "DoD's diagnosis was correct, against at most "
        f"{E(K['nochange_best_base'], 'best baseline without a change', '.2f', 'runs/posthoc_by_change.json')} for "
        "any baseline — as Theorem 2 predicts. Where the source had changed, every method struggled, DoD more "
        "than some baselines, and two rounds of method revisions did not change that: the pre-registered comparison with the best baseline was "
        f"narrowly missed in round 1 ({E(K['r1_dod'], 'r1 dod', '.2f', 'runs/final')} vs "
        f"{E(K['r1_best'], 'r1 best', '.2f', 'runs/final')}) and not supported in rounds 2 and 3 (round 3: "
        f"{E(K['r3_dod3'], 'r3 dod3', '.2f', 'runs/v3main/summary_v3.json')} vs "
        f"{E(K['r3_best'], 'r3 best', '.2f', 'runs/v3main/summary_v3.json')} for an LLM agent on the "
        f"{E(K['r3_h11']['n'], 'r3 terra n', 'd', 'runs/v3main/summary_v3.json')} cases it was run on, where "
        f"DoD-3's paired difference was {E(K['r3_h11']['diff'], 'r3 H11 diff', '+.2f', 'runs/v3main/summary_v3.json')}), "
        "although the revised method blamed "
        "healthy components at source changes less often. The remaining failures are forced changes whose "
        "correctness depends on what the new encoding means — a world change in the same quarter as a new layout, "
        "an intended change of population, values missing by design — the cases our third result says no "
        "re-execution can resolve. All LLM calls in the study cost "
        f"{E(K['spent'], 'total API spend', '.2f', 'runs/cost_ledger.json')} USD.")


def introduction(P, C):
    K = key_numbers(C)
    E = lambda v, w, fmt=".2f", s="runs/final; runs/v2main/summary_v2.json; runs/v3main/summary_v3.json": P.ev(v, fmt, s, "Intro: " + w)
    P.heading("Introduction", 1, label="sec:intro")
    P.para(
        "A production model's accuracy drops and an alarm fires. The default response is to retrain on recent "
        "data, and monitoring tools are built around it: they compare input and output distributions with a "
        "reference window and trigger the retraining pipeline. But a model's inputs are not the world; they are "
        "the output of a data pipeline that changes all the time. Studies of production ML report that most "
        "outages of a large ML pipeline were not ML-centric [@papasian2020], data and pipeline problems are common "
        "[@breck2019; @shankar2024], and individual incidents show how costly silent pipeline faults are: a logging "
        "change at Uber removed a fare component for 10% of sessions in key US cities and went undetected for 45 "
        "days [@uberd3]. Retraining on the output of a broken pipeline hides such a fault: the model is fitted to "
        "corrupted features, and breaks again when someone repairs the pipeline.")
    P.para(
        "This paper asks a precise question: **from what evidence can a genuine change of the prediction problem "
        "be told apart from a defect of the data pipeline, and which action follows — fix the pipeline, retrain, "
        "both, or nothing?** Our answer has a clean half and a hard half. The clean half: a changed component that "
        "the data source did not force can be tested exactly by re-executing its known-good version, and "
        "monitoring cannot replace that test. The hard half: when the source itself changed — a new layout, a "
        "recoded field, a new population — no re-execution can certify the new adapter, and every method needs "
        "an assumption about the world that real data can violate. We make four contributions.")
    P.bullets([
        "**Identifiability ({sec:theory}).** Silent defects are indistinguishable from world changes for "
        "every monitoring-only diagnostic (Theorem 1); re-executing a changed component identifies it exactly when "
        "its change was not forced (Theorem 2); forced changes are identifiable by no re-execution (Theorem 3). "
        "For forced changes we give world-robust invariant evidence (Lemma 1, Theorem 5), a rank-based history "
        "rule (Proposition 7) and three validity conditions (Propositions 8–10).",
        "**A benchmark ({sec:bench})** of nine executable pipelines over public data with real, dated "
        "changes of the published files, real library-upgrade behaviours and replays of public incidents, in "
        f"{E(C.total_cases, 'total cases', ',d', 'runs/benchmark/tables_v3.json')} cases whose ground truth comes "
        "from executing every action.",
        "**DoD ({sec:method}),** an interventional diagnoser in three versions, each frozen before it "
        "was tested, which recommends fixing, retraining, both or nothing.",
        "**Three pre-registered rounds ({sec:r1} to {sec:r3})** against the responses practitioners use, "
        "observational root-cause attribution, pipeline-instance debugging, bisection and LLM agents with and "
        "without the same re-execution tools — with negative results reported as found.",
    ])
    P.para(
        "The evidence supports the clean half without exception and shows how hard the hard half is. "
        "Retrain-on-alarm and validation-first never diagnosed a silent defect "
        f"({E(K['sil_n_all'], 'silent cases all rounds', 'd')} cases over three rounds). On all "
        f"{E(K['nochange_n'], 'consequential cases without change', 'd', 'runs/posthoc_by_change.json')} "
        "consequential cases without a published source change, DoD was correct; with a change in the period "
        "range, its best version reached "
        f"{E(K['change_dod'][1], 'r1 change dod', '.2f', 'runs/posthoc_by_change.json')}, "
        f"{E(K['change_dod'][2], 'r2 change dod', '.2f', 'runs/posthoc_by_change.json')} and "
        f"{E(K['change_dod'][3], 'r3 change dod', '.2f', 'runs/posthoc_by_change.json')} in the three rounds. Its "
        "pre-registered advantage over the best baseline was narrowly missed in round 1 and not supported in "
        "rounds 2 and 3, and the two revisions of the method — each a response to an analysed failure, each "
        "tested on fresh domains — reduced false blame where their assumptions held but did not raise the "
        "pooled diagnosis rate. We report the rounds in the order they happened, with their protocols, and "
        "analyse why each assumption failed where it did.")


def _verdict(t, minimum=None, sign=1):
    ok = t.get("n") and t["p_holm"] is not None and t["p_holm"] < 0.05 and sign * t["diff"] > 0
    if not ok:
        return "not supported"
    if minimum is not None and sign * t["diff"] < minimum:
        return "significant but below the pre-registered minimum effect"
    return "supported"


def round3(P, C, NAMES):
    P.heading("Round 3: three fresh held-out domains (DoD-3)", 1, label="sec:r3")
    src = "runs/v3main/summary_v3.json"
    E = lambda v, w, fmt=".2f": P.ev(v, fmt, src, "R3 " + w)
    T = lambda t, m, k="diag_correct": C.tab(3, t, m, k)
    H = C.r3["hypotheses"]
    doms = ("cabi", "fars", "landreg")
    order = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
             "dod_no_boundary", "dod", "dod2", "dod3_no_latest", "dod3_no_inv", "dod3"]
    order = [m for m in order if T(CONS, m)[1]]
    rows, bold = [], set()
    for i, m in enumerate(order):
        vals = [T(CONS, m)[0]] + [T(f"Domain {d}, consequential defect", m)[0] for d in doms]
        vals += [T(SIL, m)[0], T(EVT, m, "false_blame")[0] if "@terra" not in m else float("nan"),
                 T("All cases", m, "cost_s")[0] if "@terra" not in m else float("nan")]
        cells = [E(v, f"{m} {w}") if v == v else "–" for v, w in
                 zip(vals[:-1], ("pooled", "cabi", "fars", "landreg", "silent", "false blame events"))]
        cells.append(E(vals[-1], f"{m} compute", ".1f") if vals[-1] == vals[-1] else "–")
        rows.append([NAMES[m]] + cells)
        if m in ("dod", "dod2", "dod3"):
            bold.add(i)
    n = {d: T(f"Domain {d}, consequential defect", "dod3")[1] for d in doms}
    C.r3n = n
    P.table(["Method", f"Correct, all (n={sum(n.values())})", f"Bike DC (n={n['cabi']})",
             f"Crashes (n={n['fars']})", f"Houses (n={n['landreg']})", f"Silent (n={T(SIL, 'dod3')[1]})",
             f"False blame at changes (n={T(EVT, 'dod3')[1]})", "Compute (s)"], rows,
            "Round 3 (all cases are test cases). Columns as in {tab:r2}; compute is the measured re-execution time "
            "per case. The terra agents were run on the first "
            f"{T(CONS, 'llm_tools@terra')[1]} cases of the planned every-third sample of consequential cases "
            "(see text).", "r3",
            col_widths_cm=[4.4, 1.8, 1.5, 1.6, 1.6, 1.5, 2.1, 1.5], font_pt=7.0, bold_rows=bold)
    t = H["tests"]
    k11 = [k for k in t if k.startswith("H11")][0]
    h11, h12 = t[k11], t["H12 primary: dod3 - dod"]
    h13 = t["H13 false blame (cases spanning a source change): dod3 - dod"]
    best = H["best_baseline"]
    C.r3s = {"dod3": T(CONS, "dod3")[0], "dod": T(CONS, "dod")[0], "dod2": T(CONS, "dod2")[0],
             "best": best, "best_v": T(CONS, best)[0], "h11": h11, "h12": h12, "h13": h13,
             "v11": _verdict(h11, 0.10), "v12": _verdict(h12), "v13": _verdict(h13, sign=-1),
             "fb3": T(EVT, "dod3", "false_blame")[0], "fb1": T(EVT, "dod", "false_blame")[0],
             "h14": H["H14"]}
    R = C.r3s
    full_best = sorted([m for m in order if not m.startswith("dod") and T(CONS, m)[1] == T(CONS, "dod3")[1]],
                       key=lambda m: -T(CONS, m)[0])[:2]
    P.para(
        f"**H11 (DoD-3 vs the best baseline): {R['v11']}.** DoD-3 diagnosed {E(R['dod3'], 'dod3 primary')} of "
        f"consequential defects. The best baseline was {lname(NAMES, best)} ({E(R['best_v'], 'best baseline primary')} "
        f"on the cases it was run on); the paired difference was {E(h11['diff'], 'H11 diff', '+.2f')} (95% CI "
        f"[{E(h11['ci'][0], 'H11 lo', '+.2f')}, {E(h11['ci'][1], 'H11 hi', '+.2f')}], n = {E(h11['n'], 'H11 n', 'd')}, "
        f"Holm p = {E(h11['p_holm'], 'H11 p', '.3f')}). The terra agents covered only "
        f"{E(T(CONS, 'llm_tools@terra')[1], 'terra n', 'd')} of the "
        f"{E(sum(-(-T(f'Domain {d}, consequential defect', 'dod3')[1] // 3) for d in doms), 'planned terra n', 'd')} "
        "cases of the planned every-third sample of consequential cases: they reached the per-job cost caps we had set to keep the round within its allowance (US$"
        f"{P.ev(C.r3_spent, '.2f', 'runs/cost_ledger.json', 'R3 round-3 LLM spend')} of US$4.00 spent) after the first cases "
        "of the sample in run order, so their numbers rest on few, mostly early, cases. Among the other methods run "
        f"on all cases, the best were {lname(NAMES, full_best[0])} ({E(T(CONS, full_best[0])[0], 'best full 1')}) "
        f"and {lname(NAMES, full_best[1])} ({E(T(CONS, full_best[1])[0], 'best full 2')}), on a par with DoD-3.")
    P.para(
        f"**H12 (DoD-3 vs DoD): {R['v12']}.** DoD reached {E(R['dod'], 'dod primary')} and DoD-2 "
        f"{E(R['dod2'], 'dod2 primary')}; the paired difference DoD-3 − DoD was {E(h12['diff'], 'H12 diff', '+.2f')} "
        f"([{E(h12['ci'][0], 'H12 lo', '+.2f')}, {E(h12['ci'][1], 'H12 hi', '+.2f')}], Holm p = "
        f"{E(h12['p_holm'], 'H12 p', '.3f')}).")
    P.para(
        f"**H13 (false blame at published changes): {R['v13']}.** On the {E(h13['n'], 'H13 n', 'd')} cases whose "
        f"periods span a published change, DoD-3 blamed a healthy component in {E(R['fb3'], 'dod3 fb events')} of "
        f"cases and DoD in {E(R['fb1'], 'dod fb events')} (difference {E(h13['diff'], 'H13 diff', '+.2f')}, "
        f"[{E(h13['ci'][0], 'H13 lo', '+.2f')}, {E(h13['ci'][1], 'H13 hi', '+.2f')}], Holm p = "
        f"{E(h13['p_holm'], 'H13 p', '.3f')}).")
    h14 = R["h14"]
    P.para(
        f"**H14 (no change without published changes): "
        f"{'supported' if h14['same_diagnosis'] >= 0.95 else 'not supported'}.** On the "
        f"{E(h14['n'], 'H14 n', 'd')} cases without a published change in their period range, DoD-3 and DoD made "
        f"the same diagnosis in {E(h14['same_diagnosis'], 'H14 same')} of cases.")
    TXT_R3_EXTRA(P, C, NAMES, E, T)
    P.figure(C.FIG / "v3_correctness_by_domain.png", "Round 3: correct diagnosis on held-out cases with a "
             "consequential defect, by domain.", "r3dom", width_cm=13.5)
    P.figure(C.FIG / "v3_false_blame_events.png", "Round 3: false-blame rate on cases whose periods span a "
             "published change.", "r3fb", width_cm=11.0)


def TXT_R3_EXTRA(P, C, NAMES, E, T):
    """Descriptive round-3 results (outcomes, H9/H10 replications, ablations, failure analysis, development)."""
    H = C.r3["hypotheses"]
    R = C.r3s
    best = R["best"]
    mono = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
            "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna"]
    P.para(
        f"**Outcomes.** The DoD versions rarely missed a consequential defect: DoD-3 missed one in "
        f"{E(T(CONS, 'dod3', 'missed_defect')[0], 'dod3 missed cons')} of consequential cases, against "
        f"{E(T(CONS, 'observational_attribution', 'missed_defect')[0], 'obs missed cons')} for observational "
        f"attribution, {E(T(CONS, 'bugdoc_shortcut', 'missed_defect')[0], 'bugdoc missed cons')} for "
        f"pipeline-instance debugging and {E(T(CONS, 'retrain_on_alarm', 'missed_defect')[0], 'retrain missed cons')} "
        "for retrain-on-alarm, and its recommended actions lost less accuracy relative to the best action than "
        "those of any non-DoD method run on all cases (regret "
        f"{E(T(CONS, 'dod3', 'regret')[0], 'dod3 regret cons', '.3f')} against "
        f"{E(min(T(CONS, m, 'regret')[0] for m in mono), 'best non-DoD regret cons', '.3f')}). Regret scores an "
        "action under which the pipeline cannot run — typically one that leaves a crashing defect unfixed — as "
        "losing all accuracy; for every method most regret comes from such missed defects. The price is false blame: on all cases DoD-3 blamed a healthy component in "
        f"{E(T('All cases', 'dod3', 'false_blame')[0], 'dod3 fb all')} of cases.")
    h9 = H["H9"]
    P.para(
        f"**Replication of H1/H9 (descriptive).** On the {E(h9['retrain_on_alarm']['silent'][1], 'R3 n silent', 'd')} "
        "silent consequential cases, retrain-on-alarm and validation-first again diagnosed "
        f"{E(h9['retrain_on_alarm']['silent'][0], 'R3 retrain silent')} and "
        f"{E(h9['validation_first']['silent'][0], 'R3 validation silent')}; observational attribution, which also "
        f"reads the change log and every component's archived output, reached "
        f"{E(h9['observational_attribution']['silent'][0], 'R3 obs silent')}, confirming the round-2 finding.")
    h10 = H["H10"]["dod3"]
    P.para(
        f"**Invariants (H10, descriptive).** Mined invariants flagged a component in "
        f"{E(h10['T1_inv_flag'][1], 'R3 T1 with inv flag', 'd')} of {E(h10['T1'][1], 'R3 T1 cons n', 'd')} consequential "
        "T1 cases, and DoD-3 without invariants made identical decisions on every case. Across rounds 2 and 3 the "
        "invariant evidence of Theorem 5 almost never applied: the defects of our catalogs rarely move records out "
        "of a region that the four templates describe (Theorem 5c).")
    ab = H["ablations"]
    nl = ab.get("dod3_no_latest - dod3", {})
    P.para(
        f"**Ablations.** Without the latest-change rule, DoD-3 was correct on "
        f"{E(T(CONS, 'dod3_no_latest')[0], 'dod3_no_latest primary')} of consequential cases (paired difference "
        f"{E(nl.get('diff', float('nan')), 'ablation no_latest diff', '+.2f')}) but missed fewer defects "
        f"({E(T(CONS, 'dod3_no_latest', 'missed_defect')[0], 'dod3_no_latest missed')}) and had the lowest regret of "
        f"all methods ({E(T(CONS, 'dod3_no_latest', 'regret')[0], 'dod3_no_latest regret', '.3f')}): judging a "
        "component only at the latest change that touches it removes false blame on superseded layouts, but also "
        "removes some true evidence of stale adapters at earlier changes.")
    po = C.r3_post
    src = "runs/v3main/posthoc_v3.json"
    ev = lambda v, w, fmt="d": P.ev(v, fmt, src, "R3 posthoc " + w)
    cab = po["cabi"]["dod3"]
    lr = po["landreg"]["dod3"]
    fa_dod, fa_d3 = po["fars"]["dod"]["false_blame"], po["fars"]["dod3"]["false_blame"]
    site = lambda d, k: po[d]["dod3"]["flag_sites"].get(k, 0)
    P.para(
        "**Where DoD-3 still failed (post hoc).** The domains differ sharply ({fig:r3dom}). On fatal crashes, "
        f"DoD-3 was correct on {E(T('Domain fars, consequential defect', 'dod3')[0], 'fars dod3')} of consequential "
        f"cases (DoD: {E(T('Domain fars, consequential defect', 'dod')[0], 'fars dod')}), and its false-blame rate "
        f"fell from {ev(fa_dod, 'fars dod fb', '.2f')} to {ev(fa_d3, 'fars dod3 fb', '.2f')}: DoD had blamed the "
        "adapter for failing to read the byte-order-marked header of 2021–2022, a layout the source had already "
        "replaced — exactly the case of Proposition 8. On house sales every DoD version reached about two thirds, "
        f"and all {ev(site('landreg', 'clean @ 2013 : lost records'), 'landreg clean 2013 lost records')} of "
        "DoD-3's false blames of the cleaning step came from one flag: at the 2013 coverage change, the correct "
        "pipeline *intends* to drop the newly published non-standard sales, and the lost records look like a "
        "defect. On Washington bike share no method run on all cases exceeded "
        f"{E(max(T('Domain cabi, consequential defect', m)[0] for m in C.r3['tables'][CONS] if T('Domain cabi, consequential defect', m)[1] == T('Domain cabi, consequential defect', 'dod3')[1]), 'cabi best full method')} "
        "(the terra agents reached higher values on the 15 early cases they were run on). "
        f"{ev(site('cabi', 'trip_adapter @ 2020-Q2 : duration'), 'cabi trip_adapter duration flags')} false blames "
        "came from trip durations jumping at the 2020-Q2 layout change — the quarter the pandemic began, when "
        "trips became longer and casual riders' share of trips rose sharply — and "
        f"{ev(cab['evidence'].get('current version leaves values missing', 0), 'cabi current loses values')} from "
        "the rule of Proposition 9/10 that a current version leaving values missing is harmful: in the new layout, "
        "dockless trips legitimately have no station, so the correct station join leaves their round-trip "
        "indicator undefined, where the old version compared two blank station ids and called the trip a round "
        "trip. Each failure is a forced change whose correctness depends on what the "
        "new encoding means — a coincident world change, an intended change of population, and values that are "
        "missing by design — the situations Theorem 3 says no re-execution can resolve, and in which the extra "
        "assumptions we added (smoothness, retention, Proposition 10's 'always defined') were false.")
    dv = C.r3dev
    rows = []
    for d in ("acs", "tlc", "news", "divvy", "hmda", "bts"):
        v = dv[d]
        rows.append([C.SHORT[d], P.ev(v["n_consequential"], "d", "runs/v3dev/dev_v3.json", f"dev {d} n cons")]
                    + [P.ev(v[m]["diag_correct_cons"], ".2f", "runs/v3dev/dev_v3.json", f"dev {d} {m} correct")
                       if m in v and v[m]["diag_correct_cons"] is not None else "–" for m in ("dod", "dod2", "dod3")]
                    + [P.ev(v[m]["false_blame"], ".2f", "runs/v3dev/dev_v3.json", f"dev {d} {m} fb")
                       if m in v else "–" for m in ("dod", "dod3")])
    P.para("**Development domains (in-sample).** {tab:dev} reports DoD-3 on systematic samples of the round-1 and "
           "round-2 cases, which were used to design it; these numbers show what the changes fixed on the data "
           "they were designed on and are not evidence of generalisation.")
    P.table(["Domain", "Consequential cases", "DoD", "DoD-2", "DoD-3", "False blame DoD", "False blame DoD-3"],
            rows, "DoD-3 on the development domains (rounds 1–2 data; in-sample): correct diagnosis on consequential "
            "cases and false blame on all sampled cases. DoD-2 was run only on the round-2 domains.", "dev",
            col_widths_cm=[2.4, 2.6, 1.6, 1.6, 1.6, 2.4, 2.6], font_pt=7.5)


def discussion(P, C):
    K = key_numbers(C)
    bc = C.by_change
    src = "runs/posthoc_by_change.json"
    P.heading("Across the three rounds", 1, label="sec:across")
    rows = []
    for r in (1, 2, 3):
        for key, label in (("no_change", "no published change"), ("change", "published change")):
            d = bc[f"round{r}"][key]
            full = [m for m in d if not m.startswith("dod") and d[m]["n"] == d["dod"]["n"]]
            best = max(full, key=lambda m: d[m]["diag_correct"])
            tt = d.get("llm_tools@terra")
            rows.append([str(r), label, P.ev(d["dod"]["n"], "d", src, f"R{r} {key} n")]
                        + [P.ev(d[m]["diag_correct"], ".2f", src, f"R{r} {key} {m}") if m in d else "–"
                           for m in ("dod", "dod2", "dod3")]
                        + [f"{P.ev(d[best]['diag_correct'], '.2f', src, f'R{r} {key} best full baseline')} "
                           f"({lname(C.NAMES, best)})",
                           (f"{P.ev(tt['diag_correct'], '.2f', src, f'R{r} {key} terra tools')} (n={tt['n']})"
                            if tt else "–")])
    P.para(
        "The pre-registered endpoints pool cases with and without a source change in their period range. Splitting "
        "them — a post-hoc analysis, but the split Theorems 2 and 3 draw — shows the pattern behind all three "
        "rounds ({tab:split}, {fig:split}). Without a published change, every DoD version diagnosed every "
        f"consequential case correctly ({P.ev(K['nochange_n'], 'd', src, 'all rounds no-change n')} of "
        f"{P.ev(K['nochange_n'], 'd', src, 'all rounds no-change n (again)')} over three rounds), as Theorem 2 "
        "promises for unforced changes; no baseline exceeded "
        f"{P.ev(K['nochange_best_base'], '.2f', src, 'best baseline no-change max')}. With a published change, the "
        "best DoD version's correctness ranged from "
        f"{P.ev(min(K['change_dod'].values()), '.2f', src, 'min change dod')} to "
        f"{P.ev(max(K['change_dod'].values()), '.2f', src, 'max change dod')}, and in rounds 2 and 3 several other "
        "methods did better there ({tab:split}). The advantage of re-execution is confined to the changes the "
        "source did not force.")
    P.table(["Round", "Cases", "n", "DoD", "DoD-2", "DoD-3", "Best other method run on all cases",
             "LLM agent, tools (terra)"], rows,
            "Correct diagnosis on consequential cases, split by whether the case's period range contains a "
            "published change of the source (post hoc). Round 1: test split. The terra agent was run on all "
            "consequential test cases in round 1 and on subsets in rounds 2 and 3.", "split",
            col_widths_cm=[1.1, 2.9, 1.0, 1.1, 1.1, 1.1, 5.0, 3.0], font_pt=7.2)
    P.figure(C.FIG / "by_change.png", "Correct diagnosis on consequential cases without (left) and with (right) "
             "a published source change in the case's period range, by round (post hoc).", "split", width_cm=15.5)
    P.heading("Discussion and threats to validity", 1, label="sec:disc")
    P.para(
        "**What the results say.** Monitoring alone cannot separate silent defects from drift; re-executing "
        "components at their known-good versions can, exactly and cheaply, for every change the data source did "
        "not force. That half of the problem is solved by Theorem 2 and by the engineering it requires: archived "
        "intermediate outputs, reproducible component versions including library environments, and column-level "
        "lineage. The other half — whether a component rewritten for a new source layout is correct — is not, and "
        "three rounds of a method designed for it show why. Each piece of side information we used was a "
        "statement about the world or the provider that real data violated somewhere: the world does not jump at "
        "a published change (taxi fees in 2023, the pandemic quarter of the bike-share layout change); records are "
        "not removed at a change (house sales, where the correct pipeline must drop a newly published "
        "population); a field the provider defines is always defined (dockless trips, which have no station). "
        "Invariants that hold for every world shift (Lemma 1) are the principled alternative, but the four "
        "templates we mined almost never covered the defects of our catalogs (Theorem 5c).")
    P.para(
        "**What a deployment should do.** Run the rollback test on every changed component; by Theorem 2 it is "
        "exact for unforced changes, and on cases without a published change it never led DoD astray. (Where a "
        "case spans a published change, DoD treats unforced components that read changed columns as "
        "source-coupled and judges them by the boundary test, which can call a defective component benign; the "
        "exact rollback verdict should take precedence for them.) Treat a component that a published source "
        "change forced as unverified rather than as healthy or broken, and obtain the missing evidence from the "
        "provider — an overlap period in which both encodings are published, a change note that says which "
        "quantities changed — or from a human review of the new adapter. Do not retrain on the output of an "
        "unverified adapter. In rounds 2 and 3 the actions recommended by the DoD versions had lower regret "
        "than those of every baseline run on all cases, mostly because they rarely missed a consequential defect; "
        "in round 1 they did not.")
    P.para(
        "**Threats to validity.** (i) Most defects are constructed from documented incident classes; the source "
        "changes and library behaviours are real, but the particular faulty versions are ours. (ii) Nine "
        "pipelines of four to seven components are small next to industrial ones. (iii) Each round's method was "
        "designed on the earlier rounds' data; the development numbers are in-sample, and the decisions to "
        "revise were ours. (iv) The consequential threshold, the retrain rule and the 30% held-out split shape the "
        "ground truth; they were fixed before round 1. (v) The LLM agents used one prompt, low reasoning effort and "
        "at most eight tool calls, and the larger model was run on all consequential test cases in round 1 but, "
        "because of cost caps, on only about a ninth of them in rounds 2 and 3, mostly early ones. (vi) The "
        "split by published changes in {sec:across} is post hoc, although it is the split our theorems draw.")
    P.heading("Conclusion", 1)
    P.para(
        "Telling drift from a broken pipeline is not a matter of better drift statistics. For silent defects it is "
        "impossible from monitoring data, and for every change the data source did not force, re-executing the "
        "known-good version settles it exactly — in our three pre-registered rounds, every DoD version diagnosed "
        "every consequential case without a published source change correctly. Changes "
        "forced by the source are where the problem actually lies: no re-execution can certify them, the "
        "assumptions that replace re-execution fail on real data in identifiable ways, and better methods for them "
        "will need evidence from the provider rather than from the pipeline. We release the benchmark, code and "
        "records so that such methods can be compared on exactly these cases.")


def back(P, C, NAMES):
    P.heading("Declarations", 1, numbered=False)
    P.para("**Funding.** [To be completed by the authors.]")
    P.para("**Competing interests.** [To be completed by the authors.]")
    P.para("**Use of AI tools.** [To be completed by the authors.]")
    P.para("**Data and code availability.** All data are public: ACS PUMS (U.S. Census Bureau), NYC TLC trip "
           "records, the HuffPost News Category dataset, Divvy and Capital Bikeshare trip data, HMDA records "
           "(CFPB and FFIEC), BTS on-time performance data, NHTSA FARS, and HM Land Registry Price Paid Data "
           "(contains HM Land Registry data © Crown copyright and database right, licensed under the Open "
           "Government Licence v3.0). Code, benchmark definitions, raw case records and a replay script that needs "
           "no API keys will be released at [repository link].")
    P.references()

    P.doc.add_page_break()
    P.heading("Appendix A: Proofs", 1, numbered=False)
    proofs = [
        ("Theorem 1", "A monitoring-only diagnostic φ is a (possibly randomised) measurable function of "
         "observations whose joint law is identical under (D, σ, θ) and (D′, σ, θ′), and the change logs are "
         "identical by assumption; hence the output law of φ is identical, and P[φ = defect] is the same under "
         "both. Its type-I error on the non-defective configuration plus its type-II error on the defective one "
         "is therefore 1 − P[φ = defect] + P[φ = defect] = 1. ∎"),
        ("Corollary 1", "(⇐) Let the corrupted law of (X, Y) be supported in Img × Ω_Y. Choose a measurable "
         "selection w(x) ∈ (P_θ∗ ∘ σ)^{−1}(x) for x ∈ Img and push the corrupted law forward through "
         "(x, y) ↦ (w(x), y) to obtain D′; the correct pipeline applied under D′ produces the corrupted law. "
         "(⇒) Mass outside Img is impossible under every non-defective configuration; a support test that flags any "
         "record outside Img has no false alarms and misses the defect only if all n records fall in Img, which has "
         "probability (1 − ε)ⁿ. ∎"),
        ("Theorem 2", "With deterministic components and θ∗_c = θ⁰_c, c is an effective defect on the current "
         "inputs I_c iff f_c^{θ_c}(I_c) ≠ f_c^{θ⁰_c}(I_c), which is exactly the comparison the rollback test makes "
         "on archived inputs. Applying the test to every changed component in topological order and replacing the "
         "differing ones yields P_θ∗(R) on the current records, after which the remaining gap involves only the "
         "world distribution. Each test executes one component once. ∎"),
        ("Theorem 3", "Every re-execution of pipeline components takes raw records as input; under (D, σ¹) and "
         "(D″, σ⁰) the raw records have the same law by assumption, so every statistic of any re-execution, and "
         "every monitoring statistic, has the same law in both configurations. The argument of Theorem 1 "
         "applies. ∎"),
        ("Proposition 4", "Let candidates i and j be adjacent in an order, with i first. Swapping them changes only "
         "the expected cost of the two tests: testing i first costs k_i + (1 − p_i) k_j relative to the common "
         "remainder, testing j first k_j + (1 − p_j) k_i, and the first is no larger iff p_i k_j ≥ p_j k_i, i.e. "
         "p_i/k_i ≥ p_j/k_j. Any order that is not sorted by decreasing p/k therefore contains an adjacent pair whose "
         "swap does not increase the expected cost, and repeated swaps reach the sorted order. ∎"),
        ("Lemma 1", "v_e = P_{D_e}[s(W) ∉ A] = 0 = v_{e−1}, since A contains the support of s(W) under both "
         "distributions; the increase is 0, which never exceeds the largest earlier increase. ∎"),
        ("Theorem 5", "(a) On w ∉ Δ the deployed and the correct outputs agree; on V the deployed output violates "
         "g while the correct one does not; on Δ \\ V the deployed output may or may not violate it. Taking "
         "expectations gives v̂_e ≥ v_e − P(Δ \\ V) + P(V). (b) Under a correct adapter the violation-rate "
         "increases of the m + 1 transitions are exchangeable by assumption, so the event increase is the strict "
         "maximum with probability at most 1/(m+1) (Proposition 7); under Lemma 1 every increase is 0 and the rule "
         "never flags. (c) If P(V) = 0, the violation indicators of the deployed and the correct adapter coincide "
         "on Δ \\ V in law whenever the corrupted records are attainable by some world distribution (Corollary 1), "
         "so no function of the indicators separates them. ∎"),
        ("Corollary 2", "On records satisfying g, k = h(z) for a fixed function h. If the z columns are produced "
         "correctly, the deployed k on those records is h of correct semantic values and hence attainable by a "
         "correct adapter under some world distribution (Corollary 1); a jump of k alone therefore carries no "
         "evidence against the adapter. Order constraints do not determine k and cannot be used in this way. ∎"),
        ("Proposition 7", "Under exchangeability the rank of J_e among J_1, …, J_m, J_e is uniform over the "
         "m + 1 positions (ties only lower the probability of a strict maximum), so P[J_e > max_i J_i] ≤ 1/(m+1). "
         "The union bound gives L/(m+1) for L columns. Additional thresholds can only remove flags. ∎"),
        ("Proposition 8", "Correctness at p is the property A ∘ σ_k = s on the support of σ_k(W). Given A correct "
         "at p, define A′ = A on the support of σ_k and arbitrary (e.g. failing) on the support of σ_j \\ "
         "supp σ_k. A′ is also correct at p, but a test that depends on behaviour on σ_j distinguishes A from A′; "
         "it therefore rejects some correct adapter or accepts some adapter with a different behaviour on σ_k "
         "only if it also depends on σ_k, so its outcome is not a function of correctness at p. ∎"),
        ("Proposition 9", "If the field k is defined under every world distribution, the image of the correct "
         "pipeline contains only records with k defined. A rolled-back output with k missing on a positive "
         "fraction of records lies outside that image (Corollary 1) and is not the output of the correct pipeline "
         "for any world. An effect test that finds no improvement from the rollback therefore compares the current "
         "version with an output that is wrong for every world; the current version may be wrong as well (for "
         "example, wrong on other fields), so the test result does not bear on its correctness. ∎"),
        ("Proposition 10", "Let A = {k defined}. By assumption the correct semantic output lies in A for every "
         "world, so a correct component whose inputs carry k defined on a record outputs k defined on it. If the "
         "component's output has k missing on a fraction ρ > 0 of records whose inputs carry it, those records "
         "are mapped out of A, which a correct component does with probability 0 under every world distribution "
         "(Lemma 1). An increase of the output's missing rate relative to the reference period that is absent in "
         "the inputs is therefore evidence against the component that does not depend on the world. ∎"),
    ]
    for name, text in proofs:
        P.para(f"**{name}.** {text}")

    B = C.bench
    P.heading("Appendix B: Published changes and defect catalog", 1, numbered=False)
    ev_rows = []
    for d in B["domains"]:
        by_p = {}
        for e in B["events"][d]:
            by_p.setdefault(str(e.get("period") or e.get("year")), []).append(e["change"])
        for key, chs in by_p.items():
            chs = list(dict.fromkeys(chs))
            chs = [c for c in chs if not any(c != o and c in o for o in chs)]     # person/housing duplicates
            for ch in chs:
                ev_rows.append([C.SHORT[d], key, ch if len(ch) < 120 else ch[:117] + "…"])
    P.table(["Domain", "Period", "Published change"], ev_rows, "Dated changes of the published files, found by "
            "profiling the raw files of every period (from each domain's first reference period on).", "events",
            col_widths_cm=[1.8, 1.6, 13.3], font_pt=7.0)
    cat_rows = []
    for d in B["domains"]:
        for k, v in B["catalog"][d].items():
            if v["kind"] == "defect":
                note = v["note"] + (f" ({v['source']})" if v.get("source") else "")
                cat_rows.append([C.SHORT[d], v["tier"], v["component"], note])
    P.table(["Domain", "Tier", "Component", "Defect"], cat_rows, "Defect types (benign decoys omitted). T1: tied to "
            "a published change; T2: real library-upgrade behaviour; T3: documented incident class; T3r: replay of "
            "a public incident. Parentheses name the documented behaviour or incident each defect replays or is "
            "modelled on.", "catalog", col_widths_cm=[1.8, 1.0, 2.9, 11.0], font_pt=6.8)

    P.heading("Appendix C: Reproducibility and cost", 1, numbered=False)
    by_model = C.ledger.get("by_model", {})
    cost_rows = [[m, str(v["calls"]), f"{v['in'] + v.get('cached_in', 0):,}", f"{v['out']:,}",
                  P.ev(v["usd"], ".2f", "runs/cost_ledger.json", f"spend {m}")] for m, v in by_model.items()]
    P.table(["Model", "Calls", "Input tokens", "Output tokens", "USD"], cost_rows, "API usage of all LLM calls in "
            "the three rounds, from the cost ledger. All responses are cached; the study replays without API keys.",
            "costtab", col_widths_cm=[3.5, 2.0, 3.0, 3.0, 2.0])
    for k, f in sorted(C.freeze.items()):
        P.para(f"Round {k} protocol digest: {f['sha256']} over {f['n_files']} files, frozen at {f['frozen_at']}.",
               size=8.5)
    P.para("Pipelines ran on a 16-core laptop CPU; no GPU was used.", size=8.5)
    P.heading("Appendix D: Evidence index", 1, numbered=False)
    P.para("Every number reported in the paper, with the file it was computed from (generated by the build).",
           size=8.5)
    ev = [[str(i + 1), e["value"], e["what"], e["source"]] for i, e in enumerate(P.evidence)]
    P.table(["#", "Value", "Quantity", "Source"], ev, "Evidence index.", "evidence",
            col_widths_cm=[0.9, 1.8, 7.6, 6.4], font_pt=6.3)
