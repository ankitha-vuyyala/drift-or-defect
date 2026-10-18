"""Text of the paper, section by section (used by build_paper_v3.py). Numbers are never typed here: every number
comes from the context object C (saved records) through C.E / P.ev, which records it in the evidence index."""
from __future__ import annotations

import re

import numpy as np

CONS = "Cases with a consequential defect (primary endpoint)"


def n_eval(C) -> int:
    """Cases evaluated: every generated case, except the storm cases outside the fixed 1-in-3 subsample."""
    gen = sum(C.bench["cases"]["storm"].values()) if "storm" in C.bench["cases"] else 0
    ev = C.tab(4, "Domain storm", "dod4")[1] if getattr(C, "r4", None) else 0
    return C.total_cases - (gen - ev if ev else 0)


def lname(names: dict, m: str) -> str:
    """Method name inside a sentence (lower-case first letter, except for LLM)."""
    n = names[m]
    return n if n.startswith(("LLM", "DoD")) else n[0].lower() + n[1:]
EVT = "Cases spanning a published source change"
SIL = "Silent consequential defects"
VERDICTS: dict = {}          # hypothesis -> verdict, filled by the round sections, listed in Appendix F


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
    P.para(
        "**Abstention.** Our three-verdict rule is a diagnostic counterpart of the reject option in "
        "classification [@chow1970] and of selective classification, which trades coverage for risk "
        "[@elyaniv2010]. The difference is the source of the abstention: not a confidence score but an "
        "identifiability result: every component that Proposition 11(d) shows no test of the pipeline can resolve "
        "is among those left unverified.")


def problem(P, C):
    P.heading("Problem formulation", 1, label="sec:problem")
    P.para(
        "World records W ∈ Ω_W with labels Y ∈ Ω_Y follow a distribution D from a family ℱ of distributions we are "
        "willing to entertain (covariate, label and concept shift). A *source encoding* σ, from a family ℰ of "
        "encodings the provider might use, turns world records into published raw records R = σ(W) (layout, "
        "units, code lists); σ#D denotes the resulting law of raw records and labels. A pipeline is a directed "
        "acyclic graph of deterministic components; with versions θ (code, configuration, reference artifacts, "
        "library environment) it computes features X = P_θ(R), and f_c^θ denotes the function component c "
        "computes at version θ. θ⁰ is the version deployed when the model h was trained; θ∗ is the "
        "*specification* for the current period — the pipeline a careful engineer would run on the current "
        "sources. A component c is *changed* if θ_c ≠ θ⁰_c and *forced* if its specification differs from the "
        "reference (θ∗_c ≠ θ⁰_c, e.g. an adapter rewritten for a new layout). It is a *defect* if f_c^{θ_c} differs "
        "from f_c^{θ∗_c} on some input the specification pipeline can feed it, and *benign* if it is changed but "
        "not a defect (a refactor, a harmless upgrade, a correct adapter written differently from θ∗_c).")
    P.para(
        "A defect c is *locally effective* if replacing θ_c by θ∗_c, with every other component at its current "
        "version, changes c's own output on its current inputs, and *effective* if this replacement changes the "
        "final pipeline output on the current records. Effectiveness is the end-to-end notion and defines the "
        "ground truth; a component is *healthy* in a case if it is not an effective defect. Because "
        "effectiveness is judged with the other components at their current versions, two defects can mask each "
        "other (a downstream defect that drops a column hides an upstream defect in that column), and fixing one "
        "can make the other effective. A raw-reading component (an *adapter*) maps published records to semantic "
        "records S = A(R); the correct adapter for period t satisfies A∗_t ∘ σ_t = s, where s : Ω_W → Ω_S is the "
        "semantic content the provider publishes. A published change lies *in the period range* of a case with "
        "reference period p₀ and current period p₁ if it was published in a period p with p₀ < p ≤ p₁; the case "
        "then *spans* the change.")
    P.para(
        "We distinguish three kinds of diagnostic by what they observe. A *monitoring-only* diagnostic sees "
        "samples of the joint law of model inputs and labels, (P_θ(σ(W)), Y), reference statistics, the lineage "
        "graph and the change log (which components changed and in which aspect). A *lineage-observational* "
        "diagnostic also sees the archived outputs of every component in both periods, and an *interventional* "
        "diagnostic may in addition re-execute components, at any version, on archived inputs. The actions are "
        "fix(S) (replace θ_c by θ∗_c for every c ∈ S), retrain, fix(S)+retrain and nothing; the benchmark scores a "
        "fix by executing the specification version, which for a forced component assumes that the engineer "
        "who acts on the diagnosis writes a correct adapter. We call an effective defect *consequential* if "
        "fixing it alone changes the held-out accuracy under the 'nothing' or under the 'retrain' action by at "
        "least 0.002 (held-out and retraining records are current records, and training is deterministic given "
        "its inputs); the correct action fixes the consequential defects and retrains iff retraining after the "
        "fix gains more than 0.01 accuracy. A diagnosis is *correct* if the set of components it would fix "
        "contains every consequential defect and only effective defects.")
    P.para(
        "A *three-verdict* diagnosis in addition lists a set U of components it declares *unverified* — neither "
        "fixed nor cleared — for a human to review; it takes the same actions as a two-verdict diagnosis and "
        "leaves the components in U at their current versions until they are reviewed. It commits a *false "
        "blame* if it fixes a component that is not an effective defect, and a *silent miss* if a consequential "
        "defect is neither fixed nor in U. It *decides* a case if U is empty; it is *correct where decided* if it "
        "decides the case and is correct. Correctness as defined above counts the fix set only, so a three-verdict "
        "diagnosis that leaves a consequential defect in U is not correct. A two-verdict diagnosis is the special "
        "case U = ∅, for which correctness means no false blame and no silent miss.")


# ======================================================================================================= theory
def theory(P, C):
    P.heading("Identifiability", 1, label="sec:theory")
    P.para("We state the main results here and give proofs in Appendix A; results on side information for forced "
           "changes are in Appendix B. Theorems 1–3 (Theorem 2 without the "
           "propagation test) and Proposition 4 were stated before round 1, Lemma 1, Theorem 5 and Propositions 6–7 "
           "before round 2, Propositions 8–10 before round 3, and Theorem 2(b–c) and Proposition 11 before round 4 "
           "({sec:setup}).")
    P.heading("What monitoring and re-execution can identify", 2)
    P.para(
        "**Theorem 1 (observational equivalence of silent defects).** Let (D, σ, θ) contain a defect. If some "
        "D′ ∈ ℱ and some θ′ without defects with the same change-log signature (the same components changed in the "
        "same aspects) give the same joint law of model inputs and labels, then every monitoring-only diagnostic "
        "outputs \"defect\" with the same probability under both configurations; its type-I plus type-II error on "
        "the pair is at least 1.")
    P.para(
        "**Corollary 1 (image characterisation).** If ℱ contains all distributions on world records and labels, "
        "a defect is monitoring-equivalent to a world change if and only if its corrupted features lie almost "
        "surely in the image Img = P_θ∗(σ(Ω_W)) of the correct pipeline. A defect that puts mass ε > 0 outside Img "
        "is detected by a support check against Img with probability 1 − (1 − ε)ⁿ from n records.")
    P.para(
        "Validation of the model inputs can therefore catch at most the *loud* defects, and a support check "
        "against Img catches all of them; *silent* ones — inside the image — are invisible to drift tests, "
        "validation and label monitoring of the model inputs and to any learned combination of them, unless ℱ is "
        "restricted or the diagnostic uses information beyond the joint law. Intermediate outputs are such "
        "information: the argument of Corollary 1 carries over to a lineage-observational diagnostic with the "
        "map from world records to the outputs of all components in place of P_θ∗ ∘ σ, so a defect is invisible "
        "to it only if the joint law of all archived outputs is one the correct pipeline produces under some "
        "world distribution. Because a component's output is then seen together with its inputs, many silent "
        "defects fail this condition, which is why observational attribution finds some of them ({sec:r2}).")
    P.para(
        "**Theorem 2 (interventional identification of unforced changes).** Let components be deterministic, the "
        "intermediate outputs of the production run be archived, the reference version of a changed component c and "
        "the current versions of the components downstream of it be re-executable, and let c not be forced "
        "(θ∗_c = θ⁰_c). (a) The *rollback test* — run θ⁰_c on c's current inputs and compare with c's current "
        "output — returns *differ* iff c is a locally effective defect. (b) Local effectiveness is necessary for "
        "effectiveness. (c) c is effective iff the *propagation test* — re-execute the components downstream of c, "
        "at their current versions, on the rolled-back output and compare the final output with the current one "
        "— returns *differ*; by (b) this can happen only when the rollback test differs. The tests need one "
        "execution of c and, if its rollback differs, one execution of its downstream subgraph. (d) If no "
        "component is forced (θ∗ = θ⁰), testing the changed components Δ in topological order, each on the inputs "
        "produced after the replacements upstream of it, and replacing those whose rollback differs yields the "
        "correct pipeline's output, so the remaining performance gap is attributable to the world (these "
        "sequential tests reconstruct P_θ∗(R); unlike (a)–(c), they do not classify components one by one).")
    P.para(
        "**Theorem 3 (the limit: source-forced changes).** Let the encoding change from σ⁰ to σ¹ at a published "
        "change, with the reference period fixed. (a) If some D″ ∈ ℱ satisfies σ¹#D = σ⁰#D″, no diagnostic using "
        "monitoring, archived outputs and any re-execution of pipeline components separates (D, σ¹) from "
        "(D″, σ⁰). (b) More generally, if some σ¹′ ∈ ℰ and D′ ∈ ℱ satisfy σ¹′#D′ = σ¹#D, no such diagnostic "
        "separates (D, σ¹) from (D′, σ¹′); an adapter that is correct under one of them and not under the other "
        "is certified or rejected wrongly in one of the two. Part (a) covers changes whose new records the old "
        "encoding could have produced (a reinterpreted unit or code); part (b) also covers visible changes such as "
        "a renamed or new column or a new layout, whose meaning is a property of σ¹ that no re-execution "
        "observes unless ℰ is restricted — for example by the provider's documentation of the change.")
    P.para(
        "**Side information.** Theorem 3 leaves two options for a component that a published change touched: decide "
        "it with assumptions that restrict ℱ or ℰ, or leave it undecided. Appendix B states the assumptions we "
        "studied — world smoothness at published changes, invariants of the provider's process that hold under any "
        "world shift (Lemma 1, Theorem 5, Proposition 6), a rank-based history rule (Proposition 7) and validity "
        "conditions for re-execution evidence (Propositions 8–10) — together with a test-ordering result "
        "(Proposition 4); Appendix C describes the three versions of DoD that decide every case with them, and "
        "{sec:r123} reports how they fared. The next subsection gives the rule that decides only where the data "
        "allow it.")
    P.heading("A sound three-verdict rule", 2)
    P.para(
        "Theorems 2 and 3 split the changed components of a case along a line that the change record and the "
        "column lineage can draw. Call a component *touched* if it reads — directly or through upstream "
        "components, by column-level lineage — a column that a published change in the case's period range "
        "names; a change of the set of published records (coverage, population) names the table's key column and "
        "so touches every component that reads the key. Whether a touched component is forced is itself a "
        "property of the new encoding (Theorem 3), so no rule may trust its rollback; an untouched component is "
        "unforced as long as the change record is accurate, so its rollback reproduces its specification.")
    P.para(
        "**Proposition 11 (a three-verdict rule).** Assume deterministic components, archived intermediate "
        "outputs, a complete change log (every component with θ_c ≠ θ⁰_c is listed), accurate column-level "
        "lineage and an *accurate change record*: every forced component is touched. Let T be the touched "
        "components and let the rule (i) list every component of T as unverified, (ii) fix a changed component "
        "outside T iff its rollback and propagation tests both return *differ*, and (iii) clear every other "
        "component; components whose reference version or propagation test cannot be run are listed as "
        "unverified, which overrides (ii) and (iii). Then (a) every fixed component is an effective defect — the "
        "rule is *sound*: it never commits a false blame; (b) every consequential defect is fixed or unverified "
        "— it is *complete*: it never commits a silent miss; (c) if T is empty and every test runs, U is empty and "
        "the rule fixes exactly the effective defects: it decides the case and its diagnosis is correct; and (d) "
        "let c ∈ T be changed, let rolling it back change the held-out accuracy under the 'nothing' or under the "
        "'retrain' action by at least 0.002, and let its deployed output be attainable by a correct adapter under "
        "some world distribution in ℱ (Corollary 1). If ℱ contains a world distribution that the new encoding "
        "maps onto the old (Theorem 3a), there are two configurations that agree on the raw-record law, the "
        "reference period, the change log and the change record, in one of which c is a correct adaptation and "
        "in the other a consequential defect; a rule using only monitoring, archived outputs and re-execution that "
        "fixes c commits a false blame in the first, and one that clears it a silent miss in the second.")
    P.para(
        "Soundness alone is trivial — fixing nothing achieves it — and so is completeness — listing every "
        "component achieves it. The content of Proposition 11 is that one rule has both, is exact where nothing "
        "is touched (c), and cannot shorten its review list for changed, consequential touched components "
        "without side information (d). The assumption on T is one-sided: any T that contains every forced "
        "component will do, so a component known to be unforced — such as the step that applies the model's "
        "fitted encoder, whose specification is its reference version — may be left out of T. For the components "
        "covered by (d), the unverified verdict is the price of soundness, not a weakness of a particular test: "
        "without assumptions that restrict ℱ or ℰ, evidence about such a component can only rank it for review, "
        "and assumptions such as (I) can establish that it is a defect (Theorem 5a, Proposition 10) but never "
        "clear it (Theorem 5c).")


def theory_appx(P, C):
    P.heading("Appendix B: Side information for forced changes", 1, numbered=False, label="sec:sideinfo",
              anchor="Appendix B")
    P.para(
        "**Proposition 4 (test ordering).** Under a single-fault prior p_c with test costs k_c, testing candidates "
        "in decreasing p_c/k_c minimises the expected cost of finding the faulty component (sequential fault search "
        "with test costs goes back to [@gluss1959]).")
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
        "transitions. (I′) is the weaker assumption that the m + 1 increases are exchangeable. Both are statements "
        "about the provider's *process* (accounting identities, business rules, timestamp order), not about the "
        "distribution of the world.")
    P.para(
        "**Lemma 1 (region invariance).** Let g = 1[s ∉ Q] for a region Q ⊂ Ω_S that contains the support of s(W) "
        "under every world distribution the provider can produce in both periods. Then (I) holds for every world "
        "shift D_{e−1} → D_e, however large, that keeps s(W) inside Q.")
    P.para(
        "**Theorem 5 (invariant evidence for forced changes).** Let A_e be the deployed adapter at the change e, "
        "and among the records it gets wrong let V be those it moves out of the invariant region (the correct "
        "output satisfies g, the deployed one violates it) and V⁻ those it moves into it. (a) *Detection:* the "
        "violation rate of the deployed output is v̂_e = v_e + P(V) − P(V⁻) ≥ P(V). If the pipeline was correct "
        "in period e − 1 and P(V) exceeds v_{e−1} plus the largest increase over the m preceding transitions, the "
        "rule of (b) flags the deployed adapter for every world distribution satisfying (I). (b) "
        "*World-robustness:* for a correct adapter, the rule \"flag if the violation-rate increase at the change "
        "exceeds the largest increase over the m preceding transitions\" never flags under (I), in particular "
        "under Lemma 1, and flags with probability at most 1/(m+1) under (I′). (c) *Blind defects:* if P(V) = 0 "
        "and the deployed output is attainable by a correct adapter under some world distribution in ℱ "
        "(Corollary 1), the invariant carries no evidence and Theorem 3 applies again.")
    P.para(
        "**Proposition 6 (excusing a jump).** If an invariant determines a jumping column k from other columns z "
        "(support, sum and difference identities), the invariant is intact at the change, and the z columns are "
        "produced correctly, then the jump of k, whatever its size, is no evidence against the adapter. The "
        "proposition removes evidence; it does not certify the adapter.")
    P.para(
        "**Proposition 7 (history rule).** Let the world-induced change statistics J_1, …, J_m of the m ordinary "
        "transitions before a change and J_e of the change transition be exchangeable for a correct pipeline. The "
        "rule \"flag if J_e > max(J_1, …, J_m)\" has false-flag probability at most 1/(m+1) per column; with L "
        "columns at most L/(m+1). Round 1 compared J_e with a single transition, for which no bound below 1/2 "
        "holds.")
    P.heading("B.1 Validity conditions for re-execution evidence", 2, numbered=False)
    P.para(
        "**Proposition 8 (superseded layouts carry no evidence of correctness).** Let the source publish layouts "
        "σ_1, …, σ_k at changes e_1 < … < e_k ≤ p. The correct adapter for period p need only satisfy "
        "A∗_p ∘ σ_k = s: for any adapter A that is correct on σ_k there is an adapter A′ that equals A on the "
        "support of σ_k, fails on the support of σ_j outside that of σ_k (j < k), and is also correct. Hence no "
        "test whose outcome depends on how the adapter treats an earlier layout is a consistent test of its "
        "correctness at p; a forced component may only be judged at the latest published change that touches its "
        "columns.")
    P.para(
        "**Proposition 9 (validity of a rollback counterfactual).** Theorem 2 and the effect test of DoD "
        "({sec:deciding}) use the reference version θ⁰_c as a known-good counterfactual. If θ⁰_c maps semantic values "
        "that the current version reads to *missing* (it cannot parse the new layout), its output lies outside the "
        "image of the correct pipeline whenever the field is always defined, and the effect test compares the "
        "current version with a broken counterfactual; a non-improvement is then no evidence that the current "
        "version is harmless. Such a rollback must be treated like one that fails.")
    P.para(
        "**Proposition 10 (introduced missingness is world-robust evidence).** Let a semantic field k be always "
        "defined by the provider (a trip has a start time). This is a support invariant in the sense of Lemma 1. "
        "If a component's output has k missing on a fraction ρ > 0 of records while the inputs it reads k from are "
        "defined there, the component maps those records out of the invariant region; under (I) this happens with "
        "probability 0 for a correct component, whatever the world does. An increase of the missing rate of a "
        "component's output relative to the reference period that is not present in its inputs is therefore "
        "evidence of a defect that needs neither history nor smoothness.")
    P.para(
        "Propositions 8–10 do not weaken Theorem 3: they remove ways in which a correct adapter can be *mistaken* "
        "for a defect (judged on layouts it no longer needs to read; judged against a rollback that cannot read "
        "the current layout), and add one form of evidence for defects that destroy values. A third condition "
        "needs no proposition: a history test may only use periods that the deployed versions can read.")


# ====================================================================================================== methods
def methods(P, C):
    P.heading("DoD-4: the three-verdict diagnoser", 1, label="sec:method")
    P.para(
        "DoD (*Drift or Defect*) receives the monitoring report of the reference and current periods, archived "
        "intermediate outputs of both production runs and of the deployment history, the lineage graph with "
        "column-level lineage to raw columns, the change log and the dated published changes of each source. "
        "We built it in four versions, each frozen before it was evaluated. The first three (DoD, DoD-2, DoD-3; "
        "Appendix C) decide every case and differ only in how they judge components that a published change "
        "touched, using the side information of Appendix B. DoD-4, described here, does not judge them.")
    P.para("DoD-4 implements Proposition 11; its fix, clear and review verdicts use no thresholds:")
    P.bullets([
        "**Touched components.** A component is touched if, by column-level lineage, it reads directly or through "
        "upstream components a column that a published change in the case's period range names. The pipeline's "
        "output step, which applies the model's fitted encoder, is never touched: the encoder is versioned with the "
        "model and changes only by retraining, so its specification is its reference version and Proposition 11 "
        "allows leaving it out of T. A change of a table's record set names the table's key column.",
        "**Verified defects.** Every changed component that is not touched gets the rollback test; if it differs, "
        "the pipeline is re-executed with that component rolled back and every other at its current version, and "
        "the final outputs are compared (propagation test, Theorem 2c). Components for which both differ are "
        "fixed; the others are cleared as healthy.",
        "**Unverified components.** Every touched component, changed or not, and every component whose reference "
        "version or propagation test cannot be run, is listed for review and never fixed. DoD-4 labels "
        "each with DoD-3's evidence — *suspect* if DoD-3 would fix it, *no evidence* otherwise — as a ranking "
        "for the reviewer; *DoD-4 lite* omits the labels and has the same fix and review sets.",
        "**Action.** Fix the verified defects and leave the unverified components at their current versions; "
        "retrain by DoD-3's rule (DoD-4 lite, which does not run DoD-3: if the accuracy drop is at least 0.01).",
    ])


def methods_appx(P, C):
    P.heading("Appendix C: The deciding versions DoD, DoD-2 and DoD-3", 1, numbered=False, label="sec:deciding",
              anchor="Appendix C")
    P.heading("C.1 DoD (round 1)", 2, numbered=False)
    P.bullets([
        "**Candidates.** Every changed component, and every unchanged component that depends — through "
        "column-level lineage — on a column touched by a published change and either reads the source or "
        "introduces drift at its node (a possible stale or latent defect). A changed component that depends on such a "
        "column is *treated as forced* (a proxy for forced in the sense of {sec:problem}).",
        "**Ordering.** Candidates are tested in decreasing ratio of prior to measured execution time "
        "(Proposition 4). The prior combines the drift *introduced* at the component's node (drift of its output "
        "columns beyond that of the same columns at its inputs, from archived outputs at no cost), drift and "
        "validation evidence on the model inputs it feeds, and source coupling.",
        "**Tests.** *Rollback* re-executes the reference version on the component's current inputs and compares "
        "outputs exactly; for an unforced component a difference shows a locally effective defect (Theorem 2a), "
        "which in our cases was almost always also effective ({sec:across}). For a component "
        "treated as forced, an *effect* test propagates the rolled-back output to the deployed model; an improvement above "
        "τ = 0.003 marks it harmful; otherwise — and whenever the reference version cannot run on the new inputs, "
        "or the change alters the label or the set of records — a *boundary* test compares the component's output "
        "just before the published change with its output at the change, relative to the ordinary change between "
        "the two preceding periods. A jump above 3 times the ordinary change and above 0.05 in population "
        "stability index (PSI), new missing "
        "values, or lost records flag the component.",
        "**Action.** Fix every harmful or flagged component; retrain if the accuracy drop that remains after the "
        "fix is at least 0.01.",
    ])
    P.heading("C.2 DoD-2 (round 2)", 2, numbered=False)
    P.para(
        "DoD-2 changes only the boundary test. (i) *History rule:* the introduced change at a published change "
        "must exceed every one of the four preceding ordinary transitions of the deployment history (and 3 times "
        "their median, and 0.05 PSI) — Proposition 7 with m = 4, bound 1/5 per column. (ii) *Invariant evidence:* "
        "invariants of four templates — support (k ≠ 0 ⇔ z ∈ Z), order (a ≤ b), sum (t = a + b (+ c)) and "
        "difference (d = (b − a)/u) — are mined from the component's archived outputs in the history periods; one "
        "is kept if it holds on at least 98% of records in every history period and is violated at least five "
        "times as often after a random permutation of its first column. A violation increase of at least 0.01 at "
        "the change flags the component (Theorem 5a); a jump explained by an intact invariant is excused "
        "(Proposition 6).")
    P.heading("C.3 DoD-3 (round 3)", 2, numbered=False)
    P.para("DoD-3 implements Propositions 8–10 on top of DoD-2:")
    P.bullets([
        "**Latest-change rule (Proposition 8).** A source column is judged only at the latest published change, "
        "up to the current period, that touches it; a downstream component only at the latest change relevant to "
        "it. Failures to read earlier layouts are not evidence.",
        "**Valid counterfactuals (Proposition 9).** If the reference version leaves more than 1% more values "
        "missing than the current version on the columns where they differ, the rollback is treated as failed "
        "and the effect test is not used; conversely — a heuristic in the spirit of Proposition 10, which assumes "
        "the field is always defined — a current version that leaves more than 10% of values missing that the "
        "reference version reads is harmful.",
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
        "The benchmark consists of eleven executable pipelines over public data, added in four rounds; each "
        "round's domains were built before any method was run on them ({tab:domains}). The pipelines of rounds "
        "1–3 have four to seven components: a source adapter, feature and cleaning steps (some deployed in a "
        "pandas 1.5 environment), reference-data joins, and categorical encoding with a fitted artifact. The two "
        "round-4 pipelines read three source tables each — storm events with their fatality and location records, "
        "traffic crashes with the people and vehicles involved — and have twelve and eleven components: three "
        "adapters, a branch of time and code-mapping steps (time-zone table, tornado-scale map and source "
        "crosswalk; notification delay and trafficway crosswalk), per-record aggregates of the two child tables "
        "with their own code crosswalks, a three-input join, a spatial grid, cleaning and encoding. Every domain "
        "has real, dated "
        "changes of the published files — found by profiling the raw files of every period, not from "
        "documentation alone — except the airline domain, whose history is republished in the current layout and "
        "which serves as a control.")
    srcs = {"acs": "US Census ACS 1-year PUMS [@acspums]", "tlc": "NYC TLC yellow-taxi trips [@nyctlc]",
            "news": "HuffPost News Category [@misra2022]", "divvy": "Divvy trip data [@divvy]",
            "hmda": "HMDA loan records [@hmda]", "bts": "BTS on-time performance [@bts]",
            "cabi": "Capital Bikeshare trip data [@cabi]", "fars": "NHTSA FARS crash file [@fars]",
            "landreg": "HM Land Registry Price Paid [@landreg]",
            "storm": "NOAA Storm Events Database [@stormevents]", "chicago": "Chicago Traffic Crashes [@chicagocrashes]"}
    tasks = {"acs": "income > $50k", "tlc": "tip ≥ 20% of fare", "news": "27 sections",
             "divvy": "member vs casual", "hmda": "denied vs originated", "bts": "arrival delay ≥ 15 min",
             "cabi": "member vs casual", "fars": "two or more vehicles", "landreg": "new build",
             "storm": "property damage", "chicago": "injury or tow"}
    rows, total_rows, total_cases = [], 0, 0
    for d, D in B["domains"].items():
        n_cases = sum(B["cases"][d].values())
        n_ev = len({(e.get("period") or e.get("year")) for e in B["events"][d]})
        total_rows += D["bronze_rows"]
        total_cases += n_cases
        rows.append([str(D["round"]), P._cites(srcs[d]), f"{D['first']}–{D['last']} ({D['periods']})",
                     P.ev(D["bronze_rows"], ",d", "runs/benchmark/tables_v4.json", f"{d} bronze rows"),
                     str(len(D["components"])), tasks[d], P.ev(n_ev, "d", "runs/benchmark/tables_v4.json",
                                                              f"{d} dated changes"),
                     P.ev(n_cases, "d", "runs/benchmark/tables_v4.json", f"{d} cases")])
    C.total_cases = total_cases
    n_st_eval = C.tab(4, "Domain storm", "dod4")[1] if getattr(C, "r4", None) else 0
    n_st_gen = sum(B["cases"]["storm"].values()) if "storm" in B["cases"] else 0
    C.total_eval = total_cases - (n_st_gen - n_st_eval if n_st_eval else 0)
    P.table(["Round", "Source", "Periods", "Records", "Steps", "Task", "Changes", "Cases"], rows,
            "Benchmark domains. Records: sampled raw rows used by the pipelines (e.g. 100,000 trips per quarter "
            "for bike share, 150,000 records per period for taxi, mortgages, airlines and house sales, 60,000 "
            "crashes per year with their person and vehicle records in Chicago; all records for news, fatal "
            "crashes and storms, over all source tables). Changes: periods with a dated published change from the first reference "
            f"period on. In total {total_rows:,} records and {total_cases:,} cases"
            + (f", of which {C.total_eval:,} were evaluated (storm: a fixed subsample, {{sec:setup}})."
               if C.total_eval != total_cases else "."), "domains",
            col_widths_cm=[1.1, 4.2, 2.9, 1.9, 1.1, 2.4, 1.3, 1.2], font_pt=7.2)
    P.ev(total_rows, ",d", "runs/benchmark/tables_v4.json", "total bronze rows")
    P.ev(total_cases, ",d", "runs/benchmark/tables_v4.json", "total cases")
    P.para(
        "**Real source changes.** Appendix E lists every change. They include renamed and reordered columns, "
        "new layouts after an operator's system change (both bike-share systems in the first half of 2020, as "
        "the pandemic began), recoded categories (member/casual; loan purpose and occupancy under amended Regulation C "
        "in 2018), changed units (mortgage amounts in dollars instead of thousands), removed fields (crash weather "
        "fields in 2020), a byte-order mark that appeared in a header for two years, timestamp formats with and "
        "without seconds or fractions, coverage changes (non-standard house sales published from 2013; storm "
        "locations only for events with coordinates from 2006; citywide crash reporting in Chicago from 2017), "
        "code lists that were extended, renamed or recased (storm time zones with the UTC offset appended in "
        "2006, reporting sources republished in title case, tornado ratings on the Enhanced Fujita scale from "
        "2007; crash restraint and vehicle contact-point codes in 2019 and 2020). "
        "Several coincide with genuine world changes: COVID-19 (2020), an airport-fee rise in the quarter the "
        "taxi fee column was renamed (April 2023) and congestion pricing with its new column (January 2025).")
    P.para(
        "**Library behaviours.** We created pandas 1.5.3, 2.2.3 and 3.0.6 environments and probed idioms common "
        "in pipeline code; several behave differently, including chained assignment that becomes a no-op under "
        "copy-on-write [@pandas3] (pandas warns [@pandascow]; pipelines that suppress warnings fail silently) and "
        "timestamps whose integer representation changes resolution [@pandas3; @pandas65308]. Components declare their environment and "
        "run in it as subprocesses, so a library upgrade is a real execution, not a simulation.")
    P.para(
        "**Defects and decoys.** Each domain has a catalog of changes in five tiers (Appendix E): T1 defects tied "
        "to a published change (a stale mapping, a format not updated, a positional column mapping; cf. a renamed "
        "census field that broke a public benchmark library [@folktables22]); T2 real "
        "library-upgrade behaviours; T3 documented incident classes (unit errors, stale reference data, "
        "copy-paste join keys, swapped day and month, encoders re-fitted at serving time); T3r replays of public "
        "incidents [@folktables39; @nyctaxi3; @sklearn34549]; and benign changes — refactors, "
        "harmless upgrades, correct adapters. A case pairs a reference period with a current period and applies "
        "nothing, benign changes only, one defect with up to two benign decoys, or two defects, on top of the "
        "correct pipeline of the current period. A changed component is therefore not by itself a defect: every "
        "domain has cases with benign changes only, and most defect cases also contain a decoy.")
    P.para(
        "**Ground truth by execution.** Records are split by hashed id into training (40%), serving (30%, what "
        "diagnosers see) and held-out (30%, grader only, with labels from the correct pipeline). For every case we "
        "execute every canonical action and every action a method recommends, and score it on the held-out "
        "records.")


def protocol(P, C):
    P.heading("Evaluation protocol: four pre-registered rounds", 1, label="sec:setup")
    fr = C.freeze
    P.para(
        "We evaluated in four rounds. In each, hypotheses, endpoints, thresholds and a SHA-256 digest of all code "
        "and configuration were frozen before any test case was run, and the case runner refused test cases if "
        "the digest differed; the digests and frozen files are part of the released repository (Appendix G). "
        "After each round, the next version of the method was designed on data already "
        "seen — the earlier rounds' domains, from then on development data — and tested on fresh domains. In "
        "round 1, the census domain was used to design the method, and the taxi and news cases were split into "
        "development and test cases by defect type (cases without a defect by period: every third current period "
        "is development); only test cases count. From round 2 on, every case of a new domain is a test case.")
    rows = []
    for k, dom, meth, hyp in ((1, "Census (development), taxi, news", "DoD", "H1–H5"),
                              (2, "Chicago bike share, mortgages, airlines", "DoD-2", "H6–H10"),
                              (3, "Washington bike share, fatal crashes (FARS), house sales", "DoD-3", "H11–H14"),
                              (4, "Storm events, Chicago crashes", "DoD-4", "H15–H19")):
        f = fr.get(k)
        rows.append([str(k), dom, meth, hyp,
                     (P.ev(f["sha256"][:12], "s", f"runs/{['freeze', 'freeze_v2', 'freeze_v3', 'freeze_v4'][k - 1]}.json",
                           f"round {k} freeze digest") + "…") if f else "–",
                     P.ev(f["n_files"], "d", "runs/freeze*.json", f"round {k} frozen files") if f else "–"])
    P.table(["Round", "Test domains", "New method", "Hypotheses", "Digest", "Files"], rows,
            "The four pre-registered rounds. Every method of earlier rounds is run unchanged in later rounds.",
            "rounds", col_widths_cm=[1.2, 5.6, 2.2, 2.0, 2.6, 1.2], font_pt=7.5)
    if getattr(C, "r4", None):
        n_st = C.tab(4, "Domain storm", "dod4")[1]
        n_gen = sum(C.bench["cases"]["storm"].values()) if "storm" in C.bench["cases"] else 0
        if n_st and n_gen and n_st < n_gen:
            P.para(f"For compute reasons, the storm domain was evaluated on a fixed random subsample of "
                   f"{P.ev(n_st, 'd', 'runs/v4main/summary_v4.json', 'storm cases evaluated')} of its "
                   f"{P.ev(n_gen, 'd', 'runs/benchmark/tables_v4.json', 'storm cases generated')} cases (one in "
                   "three, selected by a hash of the case identifier); all other domains were evaluated in full.")
    P.para(
        "**Baselines.** *Retrain on alarm* retrains if accuracy on labelled serving data dropped by at least 0.01. "
        "*Validation first* learns missing-value and range checks on reference data, routes a failure through "
        "lineage to the changed or source-reading component closest to the failing input, and otherwise retrains "
        "on alarm. *Observational attribution* blames the changed or source-coupled component that introduces the "
        "most drift on the dataflow graph, using archived outputs of both production runs (in the spirit of "
        "[@paleyes2023]). *Full rollback*, *bisection* and *pipeline-instance debugging* (BugDoc's shortcut "
        "[@lourenco2020]) re-run whole pipelines with known-good versions swapped in. The *LLM agent* receives the "
        "same report, lineage, change log and published changes as all methods; in the *tools* variant it may also "
        "call the rollback, replay (a whole-pipeline run at chosen versions), effect and boundary tests, up to eight calls within a compute budget of three "
        "full pipeline runs. LLM agents are supporting baselines: they show what a general-purpose model makes of the "
        "same evidence, not an upper bound. We used OpenAI's gpt-5.6-luna on all cases (round 4: every chicago case and "
        "every second storm case) and gpt-5.6-terra on test cases with a consequential defect (round 1: all of "
        "them; rounds 2 and 3: every third, round 4: every fourth, within each round's API allowance; reasoning "
        "effort low, seed 0, responses cached for replay).")
    P.para(
        "**Metrics.** In rounds 1–3 the primary endpoint is diagnosis correctness on cases with a consequential "
        "defect; secondary metrics are false blame (a blamed component is not an effective defect), missed "
        "defects, regret (held-out accuracy of the best action minus that of the recommended one), fragility (the "
        "accuracy a retrained model loses once the pipeline is repaired) "
        "and measured diagnosis compute. Round 4 makes the two errors of a diagnosis primary: false blame over "
        "all cases and silent misses over cases with a consequential defect, together with coverage, correctness "
        "where the method decides, and review load ({sec:problem}). Confidence intervals are 95% cluster-bootstrap "
        "intervals (2,000 resamples; clusters are domain × defect signature); tests within a round are "
        "Holm-corrected. Rounds are reported side by side and never pooled for a test.")


# ======================================================================================================= round 1
def round1(P, C, NAMES):
    test, dev, H, post = C.r1_test, C.r1_dev, C.r1_H, C.r1_post
    src = "runs/final (test split)"
    E = lambda v, w, fmt=".2f", s=src: P.ev(v, fmt, s, "R1 " + w)
    cons = lambda r: r["has_cons"]
    silent = lambda r: r["has_cons"] and not r["loud"]
    mean = C.r1_mean
    P.heading("D.1 Round 1: census, taxi and news (DoD)", 2, numbered=False, label="sec:r1", anchor="Appendix D.1")
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
        f"**H1 (monitoring cannot see silent defects): "
        + VERDICTS.setdefault("H1", "supported" if max(v["silent"][0] for v in h1.values()) <= 0.35 else
                              "disproved" if max(v["silent"][0] for v in h1.values()) >= 0.60
                              else "not supported, not disproved")
        + f".** Of the {E(n_news + n_tlc, 'consequential test cases', 'd')} test cases with a consequential "
        f"defect, {E(n_sil, 'silent consequential cases', 'd')} were *validation-silent*: they passed every "
        "validation check on the model inputs, an observable stand-in for the image condition of Corollary 1. "
        f"Retrain-on-alarm and validation-first diagnosed {E(h1['retrain_on_alarm']['silent'][0], 'H1 retrain silent')} "
        f"and {E(h1['validation_first']['silent'][0], 'H1 validation silent')} of them, observational attribution "
        f"{E(h1['observational_attribution']['silent'][0], 'H1 obs silent')}. The LLM agent reading the same "
        f"report reached {E(h1['llm_report@luna']['silent'][0], 'H1 llm silent')} — above the bound of 0.35, below "
        "the disproof threshold of 0.60 — mostly by blaming changed components, which the change log rather than "
        "monitoring offers.")
    h2_met = t2["diff"] >= 0.15 and t2["ci"][0] > 0
    P.para(
        f"**H2 (interventions resolve them): " + VERDICTS.setdefault("H2", "supported" if h2_met else "not supported")
        + ".** DoD diagnosed "
        f"{E(C.r1['dod'], 'dod primary')} of consequential test defects against {E(C.r1['best'], 'best baseline')} for "
        f"the best baseline ({lname(NAMES, best)}); the difference {E(t2['diff'], 'H2 diff', '+.2f')} (95% CI "
        f"[{E(t2['ci'][0], 'H2 lo', '+.2f')}, {E(t2['ci'][1], 'H2 hi', '+.2f')}], Holm p = "
        f"{E(t2['p_holm'], 'H2 p', '.3f')}) "
        + ("met the pre-registered criterion (at least 0.15, interval excluding 0)" if h2_met else
           ("reached the pre-registered minimum effect of 0.15, but its interval included 0"
            if t2["diff"] >= 0.15 else "fell short of the pre-registered minimum effect of 0.15")) + ". DoD was correct "
        f"on {E(mean(test, 'dod', lambda r: cons(r) and r['domain'] == 'news')[0], 'news dod')} of news cases and "
        f"{E(mean(test, 'dod', lambda r: cons(r) and r['domain'] == 'tlc')[0], 'tlc dod')} of taxi cases.")
    h3 = H["test"]["H3"]
    P.para(
        f"**H3 (ordering): " + VERDICTS.setdefault("H3", "supported" if h3["dod_b1"][0] >= h3["dod_b1_uniform"][0]
                                                   else "not supported")
        + f".** Ordering tests by evidence per cost under a one-run budget reached "
        f"{E(h3['dod_b1'][0], 'dod_b1')} against {E(h3['dod_b1_uniform'][0], 'dod_b1_uniform')} "
        f"for pipeline order (difference {E(h3['b1_diff']['diff'], 'H3 diff', '+.2f')}, 95% CI "
        f"[{E(h3['b1_diff']['ci'][0], 'H3 lo', '+.2f')}, {E(h3['b1_diff']['ci'][1], 'H3 hi', '+.2f')}]); DoD used "
        f"{E(H['test']['H3']['cost_dod'][0], 'dod compute', '.1f')} s of compute per case, more than pipeline-instance "
        f"debugging ({E(H['test']['H3']['cost_bugdoc'][0], 'bugdoc compute', '.1f')} s). "
        "**H4 (fewer errors than the default responses): " + VERDICTS.setdefault("H4", "partly supported") + ".** DoD missed fewer defects than "
        f"retrain-on-alarm ({E(tt['missed_defect: dod - retrain_on_alarm']['diff'], 'H4 miss vs retrain', '+.2f')}) "
        f"and validation-first ({E(tt['missed_defect: dod - validation_first']['diff'], 'H4 miss vs validation', '+.2f')}), "
        f"blamed fewer healthy components than validation-first "
        f"({E(tt['false_blame: dod - validation_first']['diff'], 'H4 fb vs validation', '+.2f')}), and its retrained "
        f"models were less fragile: those chosen by retrain-on-alarm lost "
        f"{E(-tt['fragility: dod - retrain_on_alarm']['diff'], 'H4 fragility gap')} more accuracy once the pipeline "
        "was repaired (all Holm p < 0.01). Against retrain-on-alarm, which never blames a component, its "
        f"false-blame rate was higher ({E(tt['false_blame: dod - retrain_on_alarm']['diff'], 'H4 fb vs retrain', '+.2f')}).")
    P.para(
        f"**H5 (the predicted limit): "
        + VERDICTS.setdefault("H5", "supported" if h5["dod_no_boundary"][0] < h5["dod"][0] else "not supported")
        + f".** On forced (T1) consequential defects DoD was correct in "
        f"{E(h5['dod'][0], 'H5 dod')} of cases and its rollback-only ablation (DoD without boundary test) in "
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
    P.heading("D.2 Round 2: three held-out domains (DoD-2)", 2, numbered=False, label="sec:r2", anchor="Appendix D.2")
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
            "on all cases whose periods span a published change. Within the round's API allowance, the terra agents "
            "covered "
            f"{T(CONS, 'llm_tools@terra')[1]} of "
            f"{sum(-(-T(f'Domain {d}, consequential defect', 'dod')[1] // 3) for d in ('divvy', 'hmda', 'bts'))} "
            "cases of the planned every-third sample of cases with a consequential defect (the first in run order).", "r2",
            col_widths_cm=[4.6, 1.9, 1.7, 1.8, 1.8, 1.7, 2.3], font_pt=7.2, bold_rows=bold)
    t = H["tests"]
    h6, h7 = t["H6 primary: dod2 - dod"], t["H7 false blame (cases spanning a source change): dod2 - dod"]
    h8 = [v for k, v in t.items() if k.startswith("H8 primary: dod2")][0]
    C.r2s = {"dod2": T(CONS, "dod2")[0], "dod": T(CONS, "dod")[0], "fb_dod": T(EVT, "dod", "false_blame")[0],
             "fb_dod2": T(EVT, "dod2", "false_blame")[0]}
    P.para(
        f"**H6–H8: " + "; ".join(f"{k} " + VERDICTS.setdefault(k, _verdict(v, mn, sg))
                                for k, v, mn, sg in (("H6", h6, None, 1), ("H7", h7, None, -1), ("H8", h8, 0.15, 1)))
        + f".** DoD-2 diagnosed {E(T(CONS, 'dod2')[0], 'dod2 primary')} of consequential "
        f"defects against {E(T(CONS, 'dod')[0], 'dod primary')} for DoD (H6: {E(h6['diff'], 'H6 diff', '+.2f')}, "
        f"Holm p = {E(h6['p_holm'], 'H6 p', '.2f')}); its false-blame rate on cases spanning a published change was "
        f"{E(T(EVT, 'dod2', 'false_blame')[0], 'dod2 fb events')} against {E(T(EVT, 'dod', 'false_blame')[0], 'dod fb events')} "
        f"(H7: {E(h7['diff'], 'H7 diff', '+.2f')}, Holm p = {E(h7['p_holm'], 'H7 p', '.2f')}); and it fell short "
        f"of the best baseline, the tool-using terra agent, by {E(-h8['diff'], 'H8 gap')} on the cases both were "
        f"run on (H8, n = {E(h8['n'], 'H8 n', 'd')}, 95% CI [{E(h8['ci'][0], 'H8 lo', '+.2f')}, "
        f"{E(h8['ci'][1], 'H8 hi', '+.2f')}], Holm p = {E(h8['p_holm'], 'H8 p', '.2f')}). Both DoD versions were perfect on the airline control "
        f"domain ({E(T('Domain bts, consequential defect', 'dod2')[0], 'bts dod2')}) and failed where the source "
        f"changed repeatedly: DoD-2 reached {E(T('Domain divvy, consequential defect', 'dod2')[0], 'divvy dod2')} "
        f"(DoD: {E(T('Domain divvy, consequential defect', 'dod')[0], 'divvy dod')}) on Chicago bike "
        f"share and {E(T('Domain hmda, consequential defect', 'dod2')[0], 'hmda dod2')} on mortgages, with DoD-2 false "
        f"blame of {E(T('Domain divvy', 'dod2', 'false_blame')[0], 'divvy dod2 fb')} and "
        f"{E(T('Domain hmda', 'dod2', 'false_blame')[0], 'hmda dod2 fb')} on all cases of those domains.")
    h9 = H["H9"]
    P.para(
        f"**H9 (replication of H1): "
        + VERDICTS.setdefault("H9", "disproved" if max(v["silent"][0] for v in h9.values() if isinstance(v, dict)
                                                       and "silent" in v) >= 0.60 else
                              "supported" if max(v["silent"][0] for v in h9.values() if isinstance(v, dict)
                                                 and "silent" in v) <= 0.35 else "not supported, not disproved")
        + f".** Retrain-on-alarm and validation-first again diagnosed "
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
        "**Analysis of the false blames (round-2 data, which is development data from round 3 on).** We read the "
        "decisions behind every false blame. Three causes accounted for most of them, each a violation of a "
        "condition the tests had assumed without stating it: correct adapters were flagged for failing to read "
        "layouts the source had already replaced (the Chicago bike-share files changed at "
        f"{P.ev(len(C.bench['events']['divvy']), 'd', 'runs/benchmark/tables_v3.json', 'divvy dated changes from 2016-Q3')} "
        "dated points between 2017 and 2024; Proposition 8); the effect test compared a correct new adapter against a reference version that could "
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
    rounds = [r for r in (1, 2, 3, 4) if f"round{r}" in bc]
    best_dod = {1: "dod", 2: "dod2", 3: "dod3", 4: "dod4"}
    K["nc_n4"] = sum(bc[f"round{r}"]["no_change"]["dod"]["n"] for r in rounds)
    K["nc_ok4"] = sum(round(bc[f"round{r}"]["no_change"][best_dod[r]]["diag_correct"]
                            * bc[f"round{r}"]["no_change"][best_dod[r]]["n"]) for r in rounds)
    K["fb_max_change"] = max(C.tab(r, "Cases spanning a published source change", m, "false_blame")[0]
                             for r in (2, 3) for m in ("dod", "dod2", "dod3", "observational_attribution",
                                                       "validation_first") if C.tab(r, "Cases spanning a published source change", m, "false_blame")[1])
    if getattr(C, "r4", None):
        H4 = C.r4["hypotheses"]
        K["r4_fb"] = H4["H15"]["dod4_false_blame"][0]
        K["r4_n"] = H4["H15"]["dod4_false_blame"][1]
        K["r4_sm"] = H4["H16"]["dod4_silent_miss"][0]
        K["r4_ncons"] = H4["H16"]["dod4_silent_miss"][1]
        K["r4_cov"] = H4["H17"]["dod4_coverage"][0]
        K["r4_cd"] = H4["H17"]["dod4_correct_decided_all"][0]
        K["r4_load"] = H4["review"]["dod4"]["load"][0]
        K["r4_share"] = H4["review"]["dod4"]["share"][0]
        K["r4_dod3_fb"] = C.tab(4, "All cases (three-verdict metrics)", "dod3", "false_blame")[0]
    return K


TITLE = "Is It Model Drift or a Broken Pipeline? What Re-Execution Can and Cannot Identify in Production ML"


def front(P, C):
    K = key_numbers(C)
    E = lambda v, w, fmt=".2f", s="runs/v4main/summary_v4.json": P.ev(v, fmt, s, "Abstract: " + w)
    P.title(TITLE, "Ankitha Vuyyala\nIndependent Researcher, Louisville, Kentucky, USA\n"
            "ankithavuyyala08@gmail.com · ORCID: https://orcid.org/0009-0004-1916-8070",
            "October 2026. Code, benchmark, raw records and replay scripts: "
            "https://github.com/ankitha-vuyyala/drift-or-defect")
    P.heading("Abstract", 1, numbered=False)
    P.para(
        "When a production model degrades, teams usually retrain it, although the model sees the output of a data "
        "pipeline that changes all the time. We ask when a pipeline defect can be told apart from a genuine change "
        "of the prediction problem at all. We prove three results. A defect whose corrupted model inputs stay in "
        "the image of the correct pipeline is invisible to every diagnostic that monitors model inputs and labels. "
        "Re-executing a changed component at its known-good version — a rollback test followed by a propagation "
        "test — decides exactly whether it is an effective defect whenever the data source did not force the "
        "change. When the source did force it, no re-execution can certify the rewritten component without "
        "evidence about the new encoding. These results draw an identifiability boundary. They yield a "
        "three-verdict rule that, under an accurate record of the source's changes, is both sound — it fixes only "
        "verified defects — and complete — it lists every component a published change touched for review, so "
        "no consequential defect is missed silently — and decides exactly where no change touched the pipeline. "
        "We tested these claims in four pre-registered rounds on a benchmark of eleven executable pipelines over "
        f"public data with {E(n_eval(C), 'evaluated cases', ',d', 'runs/benchmark/tables_v4.json; runs/v4main/summary_v4.json')} evaluated cases built "
        "on dated changes of the published files, real library-upgrade behaviours and replays of public "
        "incidents, with ground truth from executing every action. Interventional diagnosis was correct on "
        f"{E(K['nc_ok4'], 'no-change correct', 'd', 'runs/posthoc_by_change.json')} of the "
        f"{E(K['nc_n4'], 'no-change n', 'd', 'runs/posthoc_by_change.json')} consequential cases without a "
        "published change in their period range. Where the source had changed, every method that commits to a "
        "diagnosis erred often, by blaming healthy components or by missing defects"
        + (f". In the fourth round, on two three-table pipelines of eleven and twelve components, our "
           f"three-verdict diagnoser DoD-4 had a false-blame rate of {E(K['r4_fb'], 'r4 false blame', '.3f')} over "
           f"{E(K['r4_n'], 'r4 n', ',d')} cases and a silent-miss rate of {E(K['r4_sm'], 'r4 silent miss', '.3f')} "
           f"over {E(K['r4_ncons'], 'r4 cons n', ',d')} consequential ones; it decided "
           f"{E(K['r4_cov'], 'r4 coverage')} of the cases (correct on {E(K['r4_cd'], 'r4 correct decided')} of "
           f"those) and listed {E(K['r4_load'], 'r4 review load', '.1f')} components per case for review"
           if "r4_fb" in K else "")
        + ". What remains open is not detection but certifying source-forced adaptations, which needs evidence "
        "from the data provider rather than from the pipeline.")
    P.para("**Keywords:** machine learning in production; data pipelines; distribution shift; root-cause "
           "diagnosis; identifiability; interventional debugging; selective prediction; benchmark")


def introduction(P, C):
    K = key_numbers(C)
    E = lambda v, w, fmt=".2f", s="runs/posthoc_by_change.json": P.ev(v, fmt, s, "Intro: " + w)
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
        "This paper asks an identifiability question: **from what evidence can a genuine change of the prediction "
        "problem be told apart from a defect of the data pipeline — and where is that impossible?** The answer "
        "has a clean half and a hard half, and the line between them is drawn by the data source. A changed "
        "component that the source did not force can be tested exactly by re-executing its known-good version, "
        "and monitoring cannot replace that test. When the source itself changed — a new layout, a recoded field, "
        "a new population — no re-execution can certify the new adapter, and any method that decides anyway "
        "needs an assumption about the world that real data can violate. A diagnoser should therefore say which "
        "half a component is in, decide where the data allow it, and hand the rest to a reviewer with the "
        "evidence it has. We make four contributions.")
    P.bullets([
        "**An identifiability theory ({sec:theory}).** Silent defects are indistinguishable from world changes for "
        "every diagnostic that monitors model inputs and labels (Theorem 1). Re-execution decides unforced changes "
        "exactly — a rollback test detects local effectiveness and a propagation test end-to-end effectiveness "
        "(Theorem 2) — and cannot certify source-forced changes (Theorem 3). From these we derive a three-verdict "
        "rule that never blames a healthy component and never misses a consequential defect silently, and show "
        "that a changed, consequential component it leaves unverified cannot in general be resolved without side "
        "information: any rule that resolves it risks one of the two errors (Proposition 11).",
        "**DoD-4 ({sec:method}),** a three-verdict diagnoser (DoD: *Drift or Defect*) that implements the rule. "
        "Three earlier versions, DoD to DoD-3, decide every case and use increasingly careful side information "
        "for forced changes — world smoothness, world-robust invariant evidence (Theorem 5), a rank-based history "
        "rule and validity conditions for re-execution evidence (Propositions 7–10); they test whether side "
        "information can close the gap that Theorem 3 opens.",
        "**A benchmark ({sec:bench})** of eleven executable pipelines over public data — including two three-table "
        "pipelines with joins of eleven and twelve components — with real, dated changes of the published files, "
        "real library-upgrade behaviours and replays of public incidents, in "
        f"{E(n_eval(C), 'evaluated cases', ',d', 'runs/benchmark/tables_v4.json; runs/v4main/summary_v4.json')} evaluated cases whose ground truth comes "
        "from executing every action.",
        "**Four pre-registered rounds ({sec:r4}, {sec:r123})** against the responses practitioners use, "
        "observational root-cause attribution, pipeline-instance debugging, bisection and, as supporting "
        "baselines, LLM agents with and without the same re-execution tools — with negative results reported as "
        "found.",
    ])
    P.para(
        "The evidence follows the boundary. Retrain-on-alarm and validation-first act only on alarms and failed "
        "checks, and accordingly diagnosed " + ("none" if K["sil_retrain_max"] == 0 == K["sil_val_max"] else "few")
        + " of the "
        f"{E(K['sil_n_all'], 'silent cases rounds 1-3', 'd', 'runs/final; runs/v2main/summary_v2.json; runs/v3main/summary_v3.json')} "
        "validation-silent consequential cases of rounds 1–3. On "
        f"{E(K['nc_ok4'], 'no-change correct', 'd')} of {E(K['nc_n4'], 'no-change n', 'd')} consequential cases "
        "without a published source change in their period range, interventional diagnosis was correct — as "
        "Theorem 2 predicts when its assumptions hold, so these cases mainly confirm that they held in real "
        "pipelines (deterministic execution, faithful archives), while the baselines erred there as well. Where a "
        "change lay in the range, no method that commits to a diagnosis was reliable: the three deciding versions "
        "of DoD did not meet their pre-registered comparisons with the best baseline, and their revisions "
        "reduced false blame where their assumptions held but not the number of errors, as Theorem 3 predicts. "
        "The fourth round tested the alternative the theory implies"
        + (f": on two larger pipelines, DoD-4's false-blame rate was "
           f"{E(K['r4_fb'], 'r4 false blame', '.3f', 'runs/v4main/summary_v4.json')} and its silent-miss rate "
           f"{E(K['r4_sm'], 'r4 silent miss', '.3f', 'runs/v4main/summary_v4.json')}, and it decided "
           f"{E(K['r4_cov'], 'r4 coverage', '.2f', 'runs/v4main/summary_v4.json')} of the cases; the price of that "
           "soundness is a review list of the components a published change touched"
           if "r4_fb" in K else "")
        + ". We report round 4 first and rounds 1–3 in summary; Appendix D gives their full reports.")


def _verdict(t, minimum=None, sign=1):
    ok = t.get("n") and t["p_holm"] is not None and t["p_holm"] < 0.05 and sign * t["diff"] > 0
    if not ok:
        return "not supported"
    if minimum is not None and sign * t["diff"] < minimum:
        return "significant but below the pre-registered minimum effect"
    return "supported"


def round3(P, C, NAMES):
    P.heading("D.3 Round 3: three fresh held-out domains (DoD-3)", 2, numbered=False, label="sec:r3", anchor="Appendix D.3")
    src = "runs/v3main/summary_v3.json"
    E = lambda v, w, fmt=".2f": P.ev(v, fmt, src, "R3 " + w)
    T = lambda t, m, k="diag_correct": C.tab(3, t, m, k)
    H = C.r3["hypotheses"]
    doms = ("cabi", "fars", "landreg")
    order = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
             "dod_no_boundary", "dod", "dod2", "dod3_no_latest", "dod3_no_inv", "dod3"]
    order = [m for m in order if T(CONS, m)[1]]
    C.r3_order = order
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
        f"**H11 (DoD-3 vs the best baseline): {VERDICTS.setdefault('H11', R['v11'])}.** DoD-3 diagnosed {E(R['dod3'], 'dod3 primary')} of "
        f"consequential defects. The best baseline was {lname(NAMES, best)} ({E(R['best_v'], 'best baseline primary')} "
        f"on the cases it was run on); the paired difference was {E(h11['diff'], 'H11 diff', '+.2f')} (95% CI "
        f"[{E(h11['ci'][0], 'H11 lo', '+.2f')}, {E(h11['ci'][1], 'H11 hi', '+.2f')}], n = {E(h11['n'], 'H11 n', 'd')}, "
        f"Holm p = {E(h11['p_holm'], 'H11 p', '.3f')}). The terra agents covered only "
        f"{E(T(CONS, 'llm_tools@terra')[1], 'terra n', 'd')} of the "
        f"{E(sum(-(-T(f'Domain {d}, consequential defect', 'dod3')[1] // 3) for d in doms), 'planned terra n', 'd')} "
        "cases of the planned every-third sample of consequential cases (the first in run order, within the "
        "round's API allowance), so their numbers rest on few cases. Among the other methods run "
        f"on all cases, the best were {lname(NAMES, full_best[0])} ({E(T(CONS, full_best[0])[0], 'best full 1')}) "
        f"and {lname(NAMES, full_best[1])} ({E(T(CONS, full_best[1])[0], 'best full 2')}), on a par with DoD-3.")
    P.para(
        f"**H12 (DoD-3 vs DoD): {VERDICTS.setdefault('H12', R['v12'])}.** DoD reached {E(R['dod'], 'dod primary')} and DoD-2 "
        f"{E(R['dod2'], 'dod2 primary')}; the paired difference DoD-3 − DoD was {E(h12['diff'], 'H12 diff', '+.2f')} "
        f"([{E(h12['ci'][0], 'H12 lo', '+.2f')}, {E(h12['ci'][1], 'H12 hi', '+.2f')}], Holm p = "
        f"{E(h12['p_holm'], 'H12 p', '.3f')}).")
    P.para(
        f"**H13 (false blame at published changes): {VERDICTS.setdefault('H13', R['v13'])}.** On the {E(h13['n'], 'H13 n', 'd')} cases whose "
        f"periods span a published change, DoD-3 blamed a healthy component in {E(R['fb3'], 'dod3 fb events')} of "
        f"cases and DoD in {E(R['fb1'], 'dod fb events')} (difference {E(h13['diff'], 'H13 diff', '+.2f')}, "
        f"[{E(h13['ci'][0], 'H13 lo', '+.2f')}, {E(h13['ci'][1], 'H13 hi', '+.2f')}], Holm p = "
        f"{E(h13['p_holm'], 'H13 p', '.3f')}).")
    h14 = R["h14"]
    P.para(
        f"**H14 (no change without published changes): "
        f"{VERDICTS.setdefault('H14', 'supported' if h14['same_diagnosis'] >= 0.95 else 'not supported')}.** On the "
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
        "those of any non-DoD method run on all cases (regret on consequential cases "
        f"{E(T(CONS, 'dod3', 'regret')[0], 'dod3 regret cons', '.3f')} against "
        f"{E(min(T(CONS, m, 'regret')[0] for m in mono), 'best non-DoD regret cons', '.3f')}). Regret scores an "
        "action under which the pipeline cannot run — typically one that leaves a crashing defect unfixed — as "
        "losing all accuracy; for every method most regret comes from such missed defects. The price is false blame: on all cases DoD-3 blamed a healthy component in "
        f"{E(T('All cases', 'dod3', 'false_blame')[0], 'dod3 fb all')} of cases.")
    h9 = H["H9"]
    P.para(
        f"**Replication of the H1/H9 analysis (descriptive, not pre-registered for round 3).** On the {E(h9['retrain_on_alarm']['silent'][1], 'R3 n silent', 'd')} "
        "silent consequential cases, retrain-on-alarm and validation-first again diagnosed "
        f"{E(h9['retrain_on_alarm']['silent'][0], 'R3 retrain silent')} and "
        f"{E(h9['validation_first']['silent'][0], 'R3 validation silent')}; observational attribution, which also "
        f"reads the change log and every component's archived output, reached "
        f"{E(h9['observational_attribution']['silent'][0], 'R3 obs silent')}, confirming the round-2 finding.")
    h10 = H["H10"]["dod3"]
    P.para(
        f"**Invariants (the H10 analysis, descriptive).** Mined invariants flagged a component in "
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
        f"({E(T(CONS, 'dod3_no_latest', 'missed_defect')[0], 'dod3_no_latest missed')}) and had the lowest regret on consequential cases of "
        f"all methods ({E(T(CONS, 'dod3_no_latest', 'regret')[0], 'dod3_no_latest regret', '.3f')}): judging a "
        "component only at the latest change that touches it removes false blame on superseded layouts, but also "
        "removes flags that, in our catalogs, coincided with stale adapters at earlier changes.")
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
        "defect. On Washington bike share no method in {tab:r3} that was run on all cases exceeded "
        f"{E(max(T('Domain cabi, consequential defect', m)[0] for m in C.r3_order if T('Domain cabi, consequential defect', m)[1] == T('Domain cabi, consequential defect', 'dod3')[1]), 'cabi best full method')} "
        "(the terra agents reached higher values on the "
        f"{E(T('Domain cabi, consequential defect', 'llm_tools@terra')[1], 'cabi terra n', 'd')} early cases they were "
        "run on). "
        f"{ev(site('cabi', 'trip_adapter @ 2020-Q2 : duration'), 'cabi trip_adapter duration flags')} false blames "
        "came from trip durations jumping at the 2020-Q2 layout change — early in the pandemic, when "
        "trips became longer and casual riders' share of trips rose sharply — and "
        f"{ev(cab['evidence'].get('current version leaves values missing', 0), 'cabi current loses values')} from "
        "the heuristic of DoD-3 (after Proposition 10) that a current version leaving values missing is harmful: in the new layout, "
        "dockless trips legitimately have no station, so the correct station join leaves their round-trip "
        "indicator undefined, where the old version compared two blank station ids and called the trip a round "
        "trip. Each failure is a forced change whose correctness depends on what the "
        "new encoding means — a coincident world change, an intended change of population, and values that are "
        "missing by design — situations in which, by Theorem 3, no re-execution can certify the adapter, and in which the extra "
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
    P.heading("Discussion and threats to validity", 1, label="sec:disc")
    P.para(
        "**What the results say.** Monitoring alone cannot separate silent defects from drift; re-executing "
        "components at their known-good versions can, exactly and with one execution per changed component (and "
        "one of its downstream subgraph per difference), for every change the data source did not force — "
        "provided the change record says correctly which changes those are. That half of the problem is solved by Theorem 2 and by the engineering it requires: archived "
        "intermediate outputs, reproducible component versions including library environments, and column-level "
        "lineage. The other half — whether a component rewritten for a new source encoding is correct — is not, "
        "and three rounds of a method designed for it show why. Each piece of side information we used was a "
        "statement about the world or the provider that real data violated somewhere: the world does not jump at "
        "a published change (taxi fees in 2023, the pandemic quarter of the bike-share layout change); records are "
        "not removed at a change (house sales, where the correct pipeline must drop a newly published "
        "population); a field the provider defines is always defined (dockless trips, which have no station). "
        "Invariants that hold for every world shift (Lemma 1) are the principled alternative, but the four "
        "templates we mined almost never covered the defects of our catalogs (Theorem 5c). Proposition 11 turns "
        "this negative result into a design rule: decide exactly where the data allow it, and say so where they "
        "do not.")
    P.para(
        "**The two errors.** Both are costly, in different ways. A diagnoser that blames a healthy component sends an engineer to "
        "rewrite code that works and, if the fix is applied, can break a correct adaptation; one that misses a "
        "defect leaves the pipeline broken and invites a retraining that hides it. Methods that always commit "
        "trade one error for the other ({fig:r4fig}): retrain-on-alarm never blames a component and misses "
        "every defect, observational attribution and the first three DoD versions blamed healthy components at "
        "most published changes in some domains. A three-verdict diagnosis avoids both at the cost of a review "
        "list, and its value depends on how short and how well ranked that list is.")
    P.para(
        "**What a deployment should do.** (1) Archive the intermediate outputs of production runs and keep the "
        "reference version of every component runnable, including its library environment; without them neither "
        "test of Theorem 2 can be run. (2) Keep a machine-readable record of the source's published changes — "
        "we found ours by profiling the raw files of every period — and column-level lineage; together they "
        "define which components a change touched, and Proposition 11's guarantees are only as good as that "
        "record. (3) Fix only components whose rollback and propagation tests both differ. (4) Treat a component "
        "that a published change touched as unverified, rank such components by the available evidence, and "
        "obtain the missing evidence from the provider — an overlap period in which both encodings are published, "
        "a change note that says which quantities changed — or from a review of the new adapter. (5) Consider "
        "deferring retraining while an adapter that feeds the model is unverified, since retraining fits the "
        "model to a possible defect; DoD-4 as evaluated retrains by DoD-3's rule, and our metrics do not score "
        "this choice.")
    P.para(
        "**Threats to validity.** (i) The source changes and library behaviours are real, but most faulty "
        "versions are ours, built from documented incident classes. (ii) The pipelines have four to twelve "
        "components; the review load of Proposition 11 grows with the number of components a change touches. "
        "(iii) We wrote the change records and the column lineage from profiles of the published files; "
        "Proposition 11's guarantees hold only if they are accurate. (iv) Each version was designed on the earlier "
        "rounds' data, so development results are in-sample. (v) The consequential threshold, the retrain rule and "
        "the held-out split, fixed before round 1, shape the ground truth. (vi) The LLM agents used one prompt and "
        "low reasoning effort, and the larger model ran on samples. (vii) The split by published changes "
        "({sec:across}) is post hoc, and round-level results are sensitive to single domains.")
    P.heading("Conclusion", 1)
    P.para(
        "Telling drift from a broken pipeline is not a matter of better drift statistics. For silent defects it is "
        "impossible from monitoring data; for every change the data source did not force, re-executing the "
        "known-good version settles it exactly; and for changes the source forced, no re-execution can. In four "
        "pre-registered rounds the evidence followed this boundary: interventional diagnosis was exact where no "
        "published change intervened, and no method that commits to a diagnosis was reliable where one did. A "
        "diagnoser that respects the boundary — fixing only what it has verified and listing what it cannot "
        "verify — " + ("avoided both false blame and silent misses" if K.get("r4_fb") == 0 == K.get("r4_sm") else
                 "rarely committed false blame or silent misses") + " on two larger pipelines. Better methods for the "
        "remaining half will need evidence from the provider rather than from the pipeline. We release the "
        "benchmark, code and records so that they can be compared on exactly these cases.")


def back(P, C, NAMES):
    P.heading("Declarations", 1, numbered=False)
    led = C.ledger
    n_calls = sum(v.get("calls", 0) for v in led.get("by_model", {}).values())
    P.para("**Funding.** This research was self-funded by the author and received no external funding. The author "
           f"paid all model API costs (US$ {P.ev(led['total_usd'], '.2f', 'runs/cost_ledger.json', 'total API spend')} "
           "in total).")
    P.para("**Competing interests.** The author declares no competing interests.")
    P.para("**Author contributions.** Ankitha Vuyyala: conceptualization, methodology, software, investigation, "
           "validation, formal analysis, visualization, and writing (original draft, review and editing). The author "
           "reviewed and approved the final manuscript and accepts responsibility for its content.")
    P.para("**Use of AI tools.** [To be completed by the author.]")
    P.para("**Data and code availability.** The DoD implementation (all four versions), the baselines, the eleven "
           "executable pipelines with their defect catalogs and records of published source changes, the frozen "
           "study protocols and analysis plans, the raw case records of all four rounds and of the development runs, "
           "and the analysis and paper-build scripts are publicly available at "
           "https://github.com/ankitha-vuyyala/drift-or-defect. The artifacts corresponding to this manuscript are "
           "archived in release v1.0 at https://github.com/ankitha-vuyyala/drift-or-defect/releases/tag/v1.0. The "
           "repository includes the response cache of the "
           f"{P.ev(n_calls, ',d', 'runs/cost_ledger.json', 'paid model calls')} paid model calls, whose token usage "
           "and cost are recorded per model in runs/cost_ledger.json. The case records regenerate every reported "
           "number, table and figure (paper/evidence_index.md maps each number to the file it was computed from), and "
           "the response cache replays every model decision without an API key. The source data are public and are "
           "not redistributed; the download scripts fetch them from their providers and check them against SHA-256 "
           "manifests: ACS PUMS (U.S. Census Bureau), NYC TLC trip records, the HuffPost News Category dataset, "
           "Divvy and Capital Bikeshare trip data, HMDA records (CFPB and FFIEC), BTS on-time performance data, "
           "NHTSA FARS, NOAA NCEI Storm Events, City of Chicago Traffic Crashes, and HM Land Registry Price Paid Data "
           "(contains HM Land Registry data © Crown copyright and database right, licensed under the Open Government "
           "Licence v3.0). Third-party data remain subject to their providers' licenses and attribution "
           "requirements.")
    P.para("**Corresponding author.** Ankitha Vuyyala. Email: ankithavuyyala08@gmail.com")
    P.references()

    P.doc.add_page_break()
    P.heading("Appendix A: Proofs", 1, numbered=False, label="sec:proofs", anchor="Appendix A")
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
        ("Theorem 2", "(a) With deterministic components and θ∗_c = θ⁰_c, c is locally effective on its current "
         "inputs I_c iff f_c^{θ_c}(I_c) ≠ f_c^{θ⁰_c}(I_c), which is exactly the comparison the rollback test "
         "makes on archived inputs. (b) If f_c^{θ_c}(I_c) = f_c^{θ⁰_c}(I_c), every downstream component receives "
         "identical inputs under both versions and, being deterministic, produces identical outputs; the final "
         "output is unchanged. (c) Replacing θ_c by θ∗_c = θ⁰_c changes only c's output, from f_c^{θ_c}(I_c) to "
         "f_c^{θ⁰_c}(I_c); the final output under the replacement is the downstream subgraph D_c, at its current "
         "versions, applied to the rolled-back output (with all other inputs as archived), which is what the "
         "propagation test computes. c is effective iff that output differs from the current one. The converse of "
         "(b) fails exactly when D_c maps the two outputs to the same final output, e.g. when a downstream step "
         "drops or filters the records that differ. (d) If no component is forced, θ∗ = θ⁰, which agrees with the "
         "current versions outside Δ. Induction over the topological order of all components (an untested "
         "component outside Δ equals its specification and receives specification inputs): when c is tested, "
         "every upstream output already equals its specification's; if c's current version agrees with θ⁰_c on "
         "these inputs its output equals the specification's, and otherwise replacing it makes it so. The final "
         "output is therefore P_θ∗(R). Each rollback executes one component once and each propagation test one "
         "downstream subgraph. ∎"),
        ("Theorem 3", "Every re-execution of pipeline components takes raw records (of the current or of the "
         "reference period) as input, and archived outputs are such executions. The reference period is the same "
         "in both configurations, and in the current period the raw records and labels have the same law by "
         "assumption — σ¹#D = σ⁰#D″ in (a), σ¹#D = σ¹′#D′ in (b) — so every statistic of any re-execution, and "
         "every monitoring statistic, has the same law in both configurations, and the argument of Theorem 1 "
         "applies. In (b), a certificate is a function of these statistics, so it takes the same value in law in "
         "both configurations and is wrong in the one where the adapter's correctness differs from its "
         "verdict. (a) is the special case σ¹′ = σ⁰. ∎"),
        ("Proposition 4", "Let candidates i and j be adjacent in an order, with i first. Swapping them changes only "
         "the expected cost of the two tests: testing i first costs k_i + (1 − p_i) k_j relative to the common "
         "remainder, testing j first k_j + (1 − p_j) k_i, and the first is no larger iff p_i k_j ≥ p_j k_i, i.e. "
         "p_i/k_i ≥ p_j/k_j. Any order that is not sorted by decreasing p/k therefore contains an adjacent pair whose "
         "swap does not increase the expected cost, and repeated swaps reach the sorted order. ∎"),
        ("Proposition 11", "Consequential defects are effective by definition. (a) A fixed c lies outside T, so it "
         "is not forced (accurate change record and lineage) and θ∗_c = θ⁰_c. Its propagation test re-executes the downstream subgraph on f_c^{θ⁰_c}(I_c) = f_c^{θ∗_c}(I_c) with every "
         "other component at its current version, which is the final output under the replacement of θ_c by "
         "θ∗_c; it differs from the current output, so c is an effective defect (Theorem 2c). (b) Let c be a "
         "consequential defect. If c ∈ T it is unverified. Otherwise c is not forced, and being a defect it is "
         "changed (f_c^{θ_c} ≠ f_c^{θ∗_c} = f_c^{θ⁰_c}, so θ_c ≠ θ⁰_c), hence listed in the complete change log. It is effective, hence locally effective "
         "(Theorem 2b), so its rollback differs (Theorem 2a) and its propagation test differs (Theorem 2c), unless "
         "a test cannot run, in which case c is unverified. (c) If T = ∅, no component is forced; an unchanged "
         "component then equals its specification and is not a defect; if every test runs, U = ∅, and by (a) and "
         "the argument of (b) a changed component is fixed iff it is an effective defect. The fix set is the set "
         "of effective defects, which contains the consequential ones. (d) Configuration 1 is (D, σ¹), where σ¹ is "
         "an encoding consistent with the published change under which the deployed version of c is a correct "
         "adaptation (it exists because c's deployed output is attainable by a correct adapter) and σ¹#D is the "
         "observed raw law. Configuration 2 is (D″, σ⁰) with σ⁰#D″ = σ¹#D, in which the published change leaves "
         "the encoding of c's columns unchanged. There θ∗_c = θ⁰_c ≠ θ_c, so c is a defect, consequential by the "
         "observed effect of its rollback. Both configurations share the raw-record law, the reference period, "
         "the change log and the change record (hence T), and by Theorem 3 every statistic available to the rule "
         "has the same law in both. Fixing c is a false blame in the first; clearing it is a silent miss in the "
         "second. ∎"),
        ("Lemma 1", "v_e = P_{D_e}[s(W) ∉ Q] = 0 = v_{e−1}, since Q contains the support of s(W) under both "
         "distributions; the increase is 0, which never exceeds the largest earlier increase. ∎"),
        ("Theorem 5", "(a) On records the deployed adapter gets right, the deployed and the correct outputs agree; "
         "on V the deployed output violates g and the correct one does not; on V⁻ the reverse; on the remaining "
         "wrong records both or neither violate it. Taking expectations gives v̂_e = v_e + P(V) − P(V⁻), and "
         "P(V⁻) ≤ v_e because the correct output violates g on V⁻, so v̂_e ≥ P(V). With the pipeline correct in "
         "period e − 1, the deployed increase at the change is v̂_e − v_{e−1} ≥ P(V) − v_{e−1}, which exceeds the "
         "largest earlier increase by assumption, so the rule flags, whatever the world distribution. (b) Under a correct adapter the violation-rate "
         "increases of the m + 1 transitions are exchangeable by assumption, so the event increase is the strict "
         "maximum with probability at most 1/(m+1) (Proposition 7) under (I′); under (I) the increase at the "
         "change never exceeds the largest earlier one, so the rule never flags, and Lemma 1 gives (I). (c) If the "
         "deployed output is attainable by a correct adapter under some D′ ∈ ℱ (Corollary 1), the correct pipeline "
         "under D′ produces the deployed output law, including the law of its violation indicators, so no "
         "function of the indicators separates the two configurations; P(V) = 0 is necessary for this, since "
         "records in V violate g with correct inputs. ∎"),
        ("Proposition 6", "On records satisfying g, k = h(z) for a fixed function h. If the z columns are produced "
         "correctly, the deployed k on those records is h of correct semantic values and hence attainable by a "
         "correct adapter under some world distribution (Corollary 1); a jump of k alone therefore carries no "
         "evidence against the adapter. It carries none for it either: a defect elsewhere in the adapter is not "
         "excluded. Order constraints do not determine k and cannot be used in this way. ∎"),
        ("Proposition 7", "Under exchangeability the rank of J_e among J_1, …, J_m, J_e is uniform over the "
         "m + 1 positions (ties only lower the probability of a strict maximum), so P[J_e > max_i J_i] ≤ 1/(m+1). "
         "The union bound gives L/(m+1) for L columns. Additional thresholds can only remove flags. ∎"),
        ("Proposition 8", "Correctness at p is the property A ∘ σ_k = s on the support of σ_k(W). Given A correct "
         "at p, define A′ = A on the support of σ_k and arbitrary (e.g. failing) on the support of σ_j \\ "
         "supp σ_k. A′ is also correct at p, but a test that depends on behaviour on σ_j distinguishes A from A′. "
         "Hence such a test rejects a correct adapter (A or A′), so its outcome is not a function of correctness "
         "at p. ∎"),
        ("Proposition 9", "If the field k is defined under every world distribution, the image of the correct "
         "pipeline contains only records with k defined. A rolled-back output with k missing on a positive "
         "fraction of records lies outside that image (Corollary 1) and is not the output of the correct pipeline "
         "for any world. An effect test that finds no improvement from the rollback therefore compares the current "
         "version with an output that is wrong for every world; the current version may be wrong as well (for "
         "example, wrong on other fields), so the test result does not bear on its correctness. ∎"),
        ("Proposition 10", "Let Q = {k defined}. By assumption the correct semantic output lies in Q for every "
         "world, so a correct component whose inputs carry k defined on a record outputs k defined on it. If the "
         "component's output has k missing on a fraction ρ > 0 of records whose inputs carry it, those records "
         "are mapped out of Q, which a correct component does with probability 0 under every world distribution "
         "(Lemma 1). An increase of the output's missing rate relative to the reference period that is absent in "
         "the inputs is therefore evidence against the component that does not depend on the world. ∎"),
    ]
    for name, text in proofs:
        P.para(f"**{name}.** {text}")



def appx_catalog(P, C, NAMES):
    B = C.bench
    P.heading("Appendix E: Published changes and defect catalog", 1, numbered=False, label="sec:catalog",
              anchor="Appendix E")
    ev_rows = []
    for d in B["domains"]:
        by_p = {}
        for e in B["events"][d]:
            by_p.setdefault(str(e.get("period") or e.get("year")), []).append(e["change"])
        for key, chs in by_p.items():
            chs = list(dict.fromkeys(chs))
            chs = [c for c in chs if not any(c != o and c in o for o in chs)]     # person/housing duplicates
            for ch in chs:
                ev_rows.append([C.SHORT[d], key, ch])
    P.table(["Domain", "Period", "Published change"], ev_rows, "Dated changes of the published files, found by "
            "profiling the raw files of every period (from each domain's first reference period on).", "events",
            col_widths_cm=[1.8, 1.6, 13.3], font_pt=7.0)
    cat_rows = []
    for d in B["domains"]:
        for k, v in B["catalog"][d].items():
            if v["kind"] == "defect":
                src = v.get("source") or ""
                m_ = re.match(r"^(.*?)\s*\(([^()]*)\)$", src)
                if m_ and m_.group(2) in v["note"]:          # parenthetical already stated in the note
                    src = m_.group(1)
                cat_rows.append([C.SHORT[d], v["tier"], v["component"], v["note"], src or "–"])
    P.table(["Domain", "Tier", "Component", "Defect", "Documented source"], cat_rows, "Defect types (benign decoys "
            "omitted). T1: tied to a published change; T2: real library-upgrade behaviour; T3: documented incident "
            "class; T3r: replay of a public incident. The last column names the documented behaviour or incident a "
            "defect replays or is modelled on.", "catalog", col_widths_cm=[1.6, 0.9, 2.4, 7.4, 4.4], font_pt=6.8)



def appx_hyps(P, C, NAMES):
    P.heading("Appendix F: Pre-registered hypotheses", 1, numbered=False, label="sec:hyps", anchor="Appendix F")
    hyp = [
        ("H1", 1, "Monitoring-only methods (retrain on alarm, validation first, observational attribution, LLM "
                  "report) reach at most 0.35 correctness on validation-silent consequential defects; disproved if "
                  "any reaches 0.60."),
        ("H2", 1, "DoD exceeds the best non-oracle baseline on the primary endpoint by at least 0.15, with the 95% "
                  "paired cluster-bootstrap interval excluding 0."),
        ("H3", 1, "Under a one-run budget, ratio ordering is at least as correct as topological ordering."),
        ("H4", 1, "DoD has lower missed-defect and false-blame rates than retrain on alarm and validation first, "
                  "and lower fragility than retrain on alarm."),
        ("H5", 1, "On source-coupled (T1) defects, DoD without boundary test is less correct than DoD."),
        ("H6", 2, "DoD-2 is more correct than DoD (paired difference > 0, Holm p < 0.05)."),
        ("H7", 2, "On cases spanning a published change, DoD-2 has a lower false-blame rate than DoD (Holm p < 0.05)."),
        ("H8", 2, "DoD-2 exceeds the best non-DoD baseline by at least 0.15, interval excluding 0 (replication of H2)."),
        ("H9", 2, "Replication of H1 on the round-2 domains."),
        ("H10", 2, "Descriptive: DoD-2 correctness on T1 defects with and without a flagging invariant."),
        ("H11", 3, "DoD-3 exceeds the best non-DoD baseline (Holm p < 0.05; minimum effect of interest 0.10)."),
        ("H12", 3, "DoD-3 exceeds DoD on the primary endpoint (Holm p < 0.05)."),
        ("H13", 3, "On cases spanning a published change, DoD-3 has a lower false-blame rate than DoD (Holm p < 0.05)."),
        ("H14", 3, "Without a published change, DoD-3 and DoD make the same diagnosis in at least 95% of cases."),
        ("H15", 4, "DoD-4's false-blame rate is at most 0.02, and on cases spanning a published change lower than "
                   "DoD-3's (Holm p < 0.05)."),
        ("H16", 4, "DoD-4's silent-miss rate on cases with a consequential defect is at most 0.02."),
        ("H17", 4, "Where DoD-4 decides, its diagnosis is correct in at least 95% (all decided cases and decided "
                   "cases with a consequential defect)."),
        ("H18", 4, "On consequential cases without a published change, DoD-4 is correct in at least 95%."),
        ("H19", 4, "Descriptive: how well DoD-3's evidence labels rank DoD-4's unverified components."),
    ]
    P.table(["", "Round", "Pre-registered hypothesis (abridged from the frozen protocol)", "Verdict"],
            [[h, str(r), t, VERDICTS.get(h, "descriptive" if h in ("H10", "H19") else "–")] for h, r, t in hyp],
            "Hypotheses of the four rounds and their verdicts, as reported in {sec:r4} and {sec:r123} (details: "
            "Appendix D). Primary endpoint: "
            "diagnosis correctness on cases with a consequential defect.", "hyps",
            col_widths_cm=[1.0, 1.2, 11.2, 3.3], font_pt=7.0)


def appx_repro(P, C, NAMES):
    P.heading("Appendix G: Reproducibility and cost", 1, numbered=False, label="sec:repro", anchor="Appendix G")
    by_model = C.ledger.get("by_model", {})
    cost_rows = [[m, str(v["calls"]), f"{v['in'] + v.get('cached_in', 0):,}", f"{v['out']:,}",
                  P.ev(v["usd"], ".2f", "runs/cost_ledger.json", f"spend {m}")] for m, v in by_model.items()]
    P.table(["Model", "Calls", "Input tokens", "Output tokens", "USD"], cost_rows, "API usage of all LLM calls in "
            "the four rounds, from the cost ledger. All responses are cached; the study replays without API keys.",
            "costtab", col_widths_cm=[3.5, 2.0, 3.0, 3.0, 2.0])
    for k, f in sorted(C.freeze.items()):
        P.para(f"Round {k} protocol digest: {f['sha256']} over {f['n_files']} files, frozen at {f['frozen_at']}.",
               size=8.5)
    P.para("Pipelines ran on a 16-core laptop CPU; no GPU was used.", size=8.5)
    P.para("Every number in the text and tables is computed by the build script from the saved records; the "
           "released repository contains an index that maps each reported number to the file it was computed from.",
           size=8.5)


def appx_rounds_intro(P, C, NAMES):
    P.heading("Appendix D: Rounds 1–3 in detail", 1, numbered=False, label="sec:rounds", anchor="Appendix D")
    P.para("This appendix reports rounds 1–3 as pre-registered: every hypothesis with its verdict, the results "
           "per domain, and the analyses of the failures that motivated the next version.")


def r123(P, C, NAMES):
    """Main-text summary of rounds 1-3 (full reports: Appendix D)."""
    P.heading("Rounds 1–3: can side information decide forced changes?", 1, label="sec:r123")
    K = key_numbers(C)
    cons = lambda r: r["has_cons"]
    s1, s2, s3 = "runs/final (test split)", "runs/v2main/summary_v2.json", "runs/v3main/summary_v3.json"
    E = lambda v, w, s, fmt=".2f": P.ev(v, fmt, s, "R1-3 summary: " + w)
    rows = []
    t1 = C.r1_H["test"]["tests"]["primary: dod - best"]
    b1 = C.r1_H["test"]["best_baseline"]
    rows.append(["1", "Census (dev.), taxi, news", "DoD",
                 E(C.r1_mean(C.r1_test, "dod", cons)[1], "r1 n cons", s1, "d"),
                 E(C.r1_mean(C.r1_test, "dod", cons)[0], "r1 dod", s1),
                 f"{NAMES[b1]} {E(C.r1_mean(C.r1_test, b1, cons)[0], 'r1 best', s1)}",
                 f"{E(t1['diff'], 'r1 diff', s1, '+.2f')} [{E(t1['ci'][0], 'r1 lo', s1, '+.2f')}, "
                 f"{E(t1['ci'][1], 'r1 hi', s1, '+.2f')}], p = {E(t1['p_holm'], 'r1 p', s1, '.3f')}",
                 VERDICTS.get("H2", "–")])
    for rnd, R_, m, hk, doms, src in ((2, C.r2, "dod2", "H8 primary: dod2", "Chicago bike share, mortgages, airlines",
                                        s2),
                                       (3, C.r3, "dod3", "H11", "Washington bike share, FARS, house sales", s3)):
        t = [v for k, v in R_["hypotheses"]["tests"].items() if k.startswith(hk)][0]
        b = R_["hypotheses"]["best_baseline"]
        rows.append([str(rnd), doms, NAMES[m], E(C.tab(rnd, CONS, m)[1], f"r{rnd} n cons", src, "d"),
                     E(C.tab(rnd, CONS, m)[0], f"r{rnd} {m}", src),
                     f"{NAMES[b]} {E(C.tab(rnd, CONS, b)[0], f'r{rnd} best', src)}",
                     f"{E(t['diff'], f'r{rnd} diff', src, '+.2f')} [{E(t['ci'][0], f'r{rnd} lo', src, '+.2f')}, "
                     f"{E(t['ci'][1], f'r{rnd} hi', src, '+.2f')}] (n = {E(t['n'], f'r{rnd} test n', src, 'd')}), "
                     f"p = {E(t['p_holm'], f'r{rnd} p', src, '.3f')}",
                     VERDICTS.get("H8" if rnd == 2 else "H11", "–")])
    P.para(
        "Rounds 1–3 tested the three deciding versions of DoD, each on three domains it had not seen, against the "
        "same baselines; {tab:r123} summarises their pre-registered primary comparisons, and Appendix D reports "
        "every hypothesis, the results per domain and the analysis of each round's failures.")
    P.table(["Round", "Test domains", "Method", "Cons. cases", "Correct", "Best baseline", "Paired difference "
             "[95% CI], Holm p", "Verdict"], rows,
            "Pre-registered primary comparisons of rounds 1–3: correct diagnosis on cases with a consequential "
            "defect for the round's DoD version and for the best baseline (round 1: test split). Each rate is over "
            "the cases the method was run on; the paired difference is over the cases both were run on (for the "
            "sampled terra agents in rounds 2 and 3, the n given), so it need not equal the difference of the two "
            "rates. The verdicts apply the pre-registered criteria (Appendix F): in rounds 1 and 2 a difference of at "
            "least 0.15 with the 95% interval excluding 0 — round 1's "
            f"{E(t1['diff'], 'r1 diff (caption)', s1, '+.2f')} is significant but below that minimum — and in round 3 "
            "a Holm-adjusted p < 0.05 (minimum effect of interest 0.10).", "r123",
            col_widths_cm=[1.3, 3.3, 1.3, 1.3, 1.3, 3.3, 3.5, 1.6], font_pt=7.0)
    t3 = C.r3["hypotheses"]["tests"]
    h12, h13 = t3["H12 primary: dod3 - dod"], t3["H13 false blame (cases spanning a source change): dod3 - dod"]
    h14 = C.r3["hypotheses"]["H14"]
    bc = C.by_change
    hi_dod = max(bc[f"round{r}"]["change"][m]["diag_correct"] for r in (1, 2, 3) for m in ("dod", "dod2", "dod3")
                 if m in bc[f"round{r}"]["change"])
    P.para(
        "None of the deciding versions met its comparison with the best baseline, and the side information "
        "helped only where its assumptions held. DoD-3 blamed fewer healthy components than DoD on cases spanning "
        f"a published change (difference {E(h13['diff'], 'H13 diff', s3, '+.2f')}, Holm p = "
        f"{E(h13['p_holm'], 'H13 p', s3, '.3f')}) and made the same diagnosis as DoD on "
        f"{E(h14['same_diagnosis'], 'H14 same', s3)} of the cases without one, but it did not diagnose more "
        f"consequential defects correctly (difference {E(h12['diff'], 'H12 diff', s3, '+.2f')}, Holm p = "
        f"{E(h12['p_holm'], 'H12 p', s3, '.3f')}). The split that Theorems 2 and 3 predict was sharp: without a "
        "published change in the period range, every version was correct on every consequential case "
        "({sec:across}); with one, no version exceeded "
        f"{E(hi_dod, 'best DoD change rounds 1-3', 'runs/posthoc_by_change.json')}. Monitoring alone behaved as "
        "Theorem 1 predicts: retrain-on-alarm and validation-first diagnosed none of the "
        f"{E(K['sil_n_all'], 'silent cases rounds 1-3', 'runs/final; ' + s2 + '; ' + s3, 'd')} validation-silent "
        "consequential cases, while observational attribution, which also reads intermediate outputs, found some.")
    P.para(
        "Every remaining failure was a forced change whose correctness depends on what the new encoding means — "
        "the situation of Theorem 3. The world jumped in the same quarter as a published change (the taxi airport "
        "fee rose when its column was renamed in April 2023; bike-share trip durations jumped at the 2020 layout "
        "changes), a change of the published population was intended (newly published non-standard house sales "
        "from 2013, which the correct pipeline drops), and values were missing by design (dockless bike-share "
        "trips have no station). Each assumption the deciding versions added — that the world does not jump at a "
        "change, that records are not removed, that a provider-defined field is always defined — was false "
        "somewhere. DoD-4 therefore decides only where Theorem 2 applies.")


# ======================================================================================================= round 4
ALL4 = "All cases (three-verdict metrics)"
CONS4 = "Cases with a consequential defect (three-verdict metrics)"
EVT4 = "Cases spanning a published source change"
NOEV4 = "Cases without a published source change"


def _thr(v, thr, le=True):
    return "met" if (v == v and ((v <= thr) if le else (v >= thr))) else "not met"


def round4(P, C, NAMES):
    P.heading("Round 4: two multi-table pipelines (DoD-4)", 1, label="sec:r4")
    src = "runs/v4main/summary_v4.json"
    E = lambda v, w, fmt=".2f": P.ev(v, fmt, src, "R4 " + w)
    T = lambda t, m, k="diag_correct": C.tab(4, t, m, k)
    H = C.r4["hypotheses"]
    order = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
             "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra",
             "dod", "dod2", "dod3", "dod4_lite", "dod4"]
    order = [m for m in order if T(ALL4, m)[1] or T(CONS4, m)[1]]
    rows, bold = [], set()
    for i, m in enumerate(order):
        terra = "@terra" in m
        vals = [(T(ALL4, m, "false_blame")[0] if not terra else float("nan"), "false blame all"),
                (T(CONS4, m, "silent_miss")[0], "silent miss cons"),
                (T(ALL4, m, "decided")[0] if not terra else float("nan"), "coverage"),
                (T(ALL4, m, "correct_decided")[0] / T(ALL4, m, "decided")[0]
                 if not terra and T(ALL4, m, "decided")[0] else float("nan"), "correct where decided"),
                (T(CONS4, m, "diag_correct")[0], "correct cons"),
                (T(ALL4, m, "review_load")[0] if not terra else float("nan"), "review load")]
        rows.append([NAMES[m]] + [E(v, f"{m} {w}") if v == v else "–" for v, w in vals])
        if m in ("dod4", "dod4_lite"):
            bold.add(i)
    n_all, n_cons = T(ALL4, "dod4")[1], T(CONS4, "dod4")[1]
    P.table(["Method", f"False blame (n={n_all})", f"Silent miss (n={n_cons})", "Coverage",
             "Correct where decided", f"Correct (n={n_cons})", "Review load"], rows,
            "Round 4 (all cases are test cases). False blame over all cases; silent misses and two-verdict "
            "correctness over cases with a consequential defect; coverage is the share of cases a method decides "
            "(lists no component for review); review load is the mean number of components listed for review. "
            "Methods other than DoD-4 and DoD-4 lite always decide. LLM agents ran within the round's pre-registered "
            f"API allowance: luna on {T(ALL4, 'llm_tools@luna')[1]} of the "
            f"{T('Domain chicago', 'dod4')[1] + -(-T('Domain storm', 'dod4')[1] // 2)} planned cases (every Chicago case, "
            f"every second storm case), terra on {T(CONS4, 'llm_tools@terra')[1]} cases of its sample of every fourth "
            "consequential case; their rates are over the cases they ran on.", "r4", col_widths_cm=[4.4, 2.0, 2.0, 1.6, 2.0, 1.9, 1.6], font_pt=7.2,
            bold_rows=bold)
    h15, h16, h17, h18, h19 = H["H15"], H["H16"], H["H17"], H["H18"], H["H19"]
    tk = [k for k in H["tests"] if k.startswith("H15")]
    t15 = H["tests"][tk[0]] if tk else {"n": 0}
    fb4, sm4 = h15["dod4_false_blame"][0], h16["dod4_silent_miss"][0]
    cd_c, cd_a, cov = h17["dod4_correct_decided_cons"], h17["dod4_correct_decided_all"], h17["dod4_coverage"]
    v15 = "supported" if (fb4 <= 0.02 and t15.get("n") and t15.get("p_holm") is not None
                          and t15["p_holm"] < 0.05 and t15["diff"] < 0) else "not supported"
    C.r4s = {"fb4": fb4, "sm4": sm4, "cov": cov[0], "cd_c": cd_c[0], "cd_a": cd_a[0], "v15": v15, "t15": t15}
    P.para(
        f"**H15 (soundness): {VERDICTS.setdefault('H15', v15)}.** DoD-4's false-blame rate — the share of cases in "
        f"which it fixed a component that was not an effective defect — was {E(fb4, 'H15 dod4 false blame', '.3f')} "
        f"over the {E(h15['dod4_false_blame'][1], 'H15 n', 'd')} cases "
        f"(threshold 0.02: {_thr(fb4, 0.02)}); on the cases spanning a published change, its false-blame rate was "
        + (f"{('lower' if t15['p_holm'] < 0.05 else 'not significantly lower') if t15['diff'] < 0 else 'not lower'}"
           " than DoD-3's (paired difference "
           f"{E(t15['diff'], 'H15 diff vs dod3', '+.2f')}, 95% CI [{E(t15['ci'][0], 'H15 lo', '+.2f')}, "
           f"{E(t15['ci'][1], 'H15 hi', '+.2f')}], Holm p "
           + (f"< 0.001{'' if E(t15['p_holm'], 'H15 p', '.4f') else ''})" if t15["p_holm"] < 0.001
              else f"= {E(t15['p_holm'], 'H15 p', '.3f')})")
           + (f"; DoD-3 itself blamed a component that was not an effective defect in only "
              f"{E(T(EVT4, 'dod3', 'false_blame')[0], 'dod3 false blame spanning')} of these cases. "
              if T(EVT4, "dod3", "false_blame")[0] < 0.05 else ". ")
           if t15.get("n") else "not compared. ")
        + "DoD-4's fixes are verified by two exact re-executions, so a false blame could only come from a failure of "
        "Proposition 11's assumptions — a component that a published change forced but whose columns the change "
        "record does not name, or non-deterministic execution.")
    P.para(
        f"**H16 (completeness): {VERDICTS.setdefault('H16', 'supported' if sm4 <= 0.02 else 'not supported')}.** A consequential defect was "
        f"neither fixed nor listed for review in a share of {E(sm4, 'H16 dod4 silent miss', '.3f')} of the "
        f"{E(h16['dod4_silent_miss'][1], 'H16 n', 'd')} cases with one (threshold 0.02). "
        f"**H17 (exact where decided): "
        f"{VERDICTS.setdefault('H17', 'supported' if min(cd_c[0], cd_a[0]) >= 0.95 else 'not supported')}.** "
        f"DoD-4 decided {E(cov[0], 'H17 coverage')} of all cases; its diagnosis was correct on "
        f"{E(cd_a[0], 'H17 correct decided all')} of the decided cases (n = {E(cd_a[1], 'H17 n all', 'd')}) and on "
        f"{E(cd_c[0], 'H17 correct decided cons')} of the decided cases with a consequential defect "
        f"(n = {E(cd_c[1], 'H17 n cons', 'd')}).")
    d18 = h18.get("dod4", [float("nan"), 0])
    others18 = sorted([(v[0], m) for m, v in h18.items() if not m.startswith("dod") and v[1] == d18[1]],
                      reverse=True)
    P.para(
        f"**H18 (identifiable regime): "
        f"{VERDICTS.setdefault('H18', 'supported' if d18[0] >= 0.95 else 'not supported')}.** On the "
        f"{E(d18[1], 'H18 n', 'd')} consequential cases without a published change in the period range, DoD-4 was "
        f"correct in {E(d18[0], 'H18 dod4')}"
        + (("; the best non-DoD method run on all of them, " if sum(1 for v, _ in others18 if v == others18[0][0]) == 1
            else "; the best non-DoD methods run on all of them, ")
           + " and ".join(lname(NAMES, mm) for v, mm in others18 if v == others18[0][0])
           + f", in {E(others18[0][0], 'H18 best other')}" if others18 else "")
        + ".")
    bl = h19["by_label"]
    sus, noe = bl.get("suspect", {"n": 0, "effective": 0}), bl.get("no evidence", {"n": 0, "effective": 0})
    P.para(
        f"**H19 (evidence for review, descriptive).** DoD-4 listed {E(H['review']['dod4']['load'][0], 'review load')} "
        f"components per case for review ({E(H['review']['dod4']['share'][0], 'review share')} of a pipeline's "
        f"components). Of the {E(sus['n'], 'suspect n', 'd')} labelled *suspect* by DoD-3's evidence, "
        f"{E(sus['effective'], 'suspect effective', 'd')} were effective defects; of the "
        f"{E(noe['n'], 'no evidence n', 'd')} labelled *no evidence*, {E(noe['effective'], 'no evidence effective', 'd')} "
        f"were (AUC of the label for effective defects {E(h19['auc_suspect_label'], 'H19 AUC')}).")
    dd = [d for d in ("storm", "chicago") if T(f"Domain {d}", "dod4")[1]]
    P.para(
        "By domain: " + "; ".join(
            f"{C.DOMAIN_NAMES[d] if d == 'chicago' else C.DOMAIN_NAMES[d].lower()} — coverage {E(T(f'Domain {d}', 'dod4', 'decided')[0], d + ' coverage')}, "
            f"review load {E(T(f'Domain {d}', 'dod4', 'review_load')[0], d + ' review load')}, false blame "
            f"{E(T(f'Domain {d}', 'dod4', 'false_blame')[0], d + ' dod4 false blame', '.3f')} (DoD-3 "
            f"{E(T(f'Domain {d}', 'dod3', 'false_blame')[0], d + ' dod3 false blame')})" for d in dd) + ".")
    nc4 = T(CONS4, "dod4")[1]
    commit = [m for m in order if not m.startswith("dod4") and "@terra" not in m and T(CONS4, m)[1] == nc4]
    bm = max(commit, key=lambda m: T(CONS4, m)[0]) if commit else None
    if bm:
        P.para(
            "Soundness and completeness have a price, which the two-verdict endpoint shows. Counting only what a "
            f"method fixes, DoD-4 was correct on {E(T(CONS4, 'dod4')[0], 'two-verdict correct dod4')} of the "
            f"consequential cases, against {E(T(CONS4, bm)[0], 'two-verdict correct best committing')} for "
            f"{lname(NAMES, bm)}, the best method that always commits: where a consequential defect sat in a "
            "component a published change touched, DoD-4 listed it for review instead of fixing it, and a method "
            "that commits fixed it whenever its side information happened to point the right way — at the cost of "
            f"false blames ({E(T(ALL4, bm, 'false_blame')[0], 'false blame best committing', '.3f')} of all cases) and "
            f"silent misses ({E(T(CONS4, bm, 'silent_miss')[0], 'silent miss best committing', '.3f')} of consequential "
            "cases) that DoD-4 did not make. The review list is long — "
            f"{E(H['review']['dod4']['share'][0], 'review share 2')} of a pipeline's components — and DoD-3's evidence "
            f"ranks it only partly: the *suspect* label is precise but covers "
            f"{E(sus['effective'] / h19['n_effective'] if h19['n_effective'] else float('nan'), 'suspect recall')} of "
            "the effective defects on the list.")
    P.figure(C.FIG / "r4_safety.png", "Round 4: false blame (all cases) against silent misses (cases with a "
             "consequential defect) for every method run on most cases (LLM agents: the cases within the API allowance, "
             "{tab:r4}). Methods that always commit to a diagnosis "
             "trade one error for the other; DoD-4 avoids both by listing the components a published change "
             "touched for review (marker size: share of cases decided).", "r4fig", width_cm=12.0)


# ================================================================================================ across rounds
def across(P, C, NAMES):
    P.heading("Across the four rounds", 1, label="sec:across")
    bc = C.by_change
    rounds = [r for r in (1, 2, 3, 4) if f"round{r}" in bc]
    E = lambda v, w, fmt=".2f", s="runs/posthoc_by_change.json": P.ev(v, fmt, s, "Across: " + w)
    P.para("This section collects analyses that were not pre-registered; they use the frozen records of all four "
           "rounds and are reported per round.")
    P.heading("The identifiability boundary in the data", 2)
    rows = []
    best_dod = {1: "dod", 2: "dod2", 3: "dod3", 4: "dod4"}
    base = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
            "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "llm_report@terra", "llm_tools@terra"]
    for r in rounds:
        R = bc[f"round{r}"]
        for key, lab in (("no_change", "no"), ("change", "yes")):
            d = R[key]
            m = best_dod[r]
            full = [b for b in base if b in d and d[b]["n"] == d.get(m, {}).get("n")]
            bb = max(full, key=lambda b: d[b]["diag_correct"]) if full else None
            ties = [b for b in full if bb and abs(d[b]["diag_correct"] - d[bb]["diag_correct"]) < 1e-12]
            rows.append([str(r), lab, E(d[m]["n"], f"r{r} {key} n", "d"), NAMES[m],
                         E(d[m]["diag_correct"], f"r{r} {key} {m}"),
                         E(d["dod"]["diag_correct"], f"r{r} {key} dod"),
                         " / ".join(NAMES[b] for b in ties) if bb else "–",
                         E(d[bb]["diag_correct"], f"r{r} {key} best other") if bb else "–"])
    P.table(["Round", "Change in range", "n", "Round's DoD version", "Correct", "DoD (round 1)",
             "Best other method", "Correct"], rows,
            "Correct diagnosis on consequential cases, split by whether a published source change lies in the "
            "case's period range (a case-level proxy for the boundary of Proposition 11, which separates components). "
            "Best other "
            "method: the non-DoD method with the highest rate among those run on all of the cases. Round 1: test "
            "split.", "bychange", col_widths_cm=[1.1, 1.6, 1.0, 3.0, 1.4, 1.6, 4.4, 1.4], font_pt=7.0)
    nc_n = sum(bc[f"round{r}"]["no_change"]["dod"]["n"] for r in rounds)
    nc_ok = sum(round(bc[f"round{r}"]["no_change"][best_dod[r]]["diag_correct"]
                      * bc[f"round{r}"]["no_change"][best_dod[r]]["n"]) for r in rounds)
    C.across = {"nc_n": nc_n, "nc_ok": nc_ok}
    ch_best = {}
    for r in rounds:
        d = bc[f"round{r}"]["change"]
        n_all = d["dod"]["n"]
        cands = [m for m in base + ["dod", "dod2", "dod3"] if m in d and d[m]["n"] == n_all]
        ch_best[r] = max(cands, key=lambda m: d[m]["diag_correct"])
    early = [r for r in rounds if r < 4]
    hi = max(bc[f"round{r}"]["change"][ch_best[r]]["diag_correct"] for r in early)
    txt = (f"Without a published change, the round's DoD version was correct on "
           f"{E(nc_ok, 'no-change correct all rounds', 'd')} of {E(nc_n, 'no-change n all rounds', 'd')} "
           "consequential cases over the four rounds — the regime in which Proposition 11(c) makes re-execution "
           "exact. With a change in the period range, no method run on all cases exceeded "
           f"{E(hi, 'best change rounds 1-3')} in rounds 1–3, and no version of the side information we tried "
           "(smoothness, invariants, history rules, introduced missingness) closed the gap ({fig:bychange4}).")
    if 4 in rounds:
        d4 = bc["round4"]["change"]
        txt += (f" In round 4 the best method that commits to a diagnosis reached "
                f"{E(d4[ch_best[4]]['diag_correct'], 'r4 change best committing')} ({lname(NAMES, ch_best[4])}) on "
                f"the {E(d4['dod']['n'], 'r4 change n', 'd')} consequential cases with a change in range, and DoD-4 "
                f"{E(d4['dod4']['diag_correct'], 'r4 change dod4')} with its fix set alone — it fixed nothing it had not "
                "verified.")
        cu = bc["round4"].get("change_untouched")
        if cu:
            txt += (f" In {E(cu['all_consequential_untouched'], 'r4 change untouched', 'd')} of these "
                    f"{E(cu['n'], 'r4 change untouched n', 'd')} cases no consequential defect was in a component "
                    "the change touched, and DoD-4 was correct on "
                    f"{E(cu['dod4_correct'], 'r4 change untouched dod4 correct', 'd')}"
                    + ("; on the rest it listed the consequential defects for review."
                       if cu.get("dod4_fixed_or_listed") == cu["n"] else
                       f"; it fixed or listed the consequential defects in "
                       f"{E(cu['dod4_fixed_or_listed'], 'r4 change fixed or listed', 'd')}."))
    P.para(txt)
    P.figure(C.FIG / "by_change4.png", "Correct diagnosis on consequential cases without (left) and with (right) a "
             "published change in the period range, per round. DoD-4 (round 4) lists the components a change "
             "touched for review instead of fixing them, so on the right it is correct only where the "
             "consequential defects were untouched.", "bychange4", width_cm=15.0)
    P.heading("The two errors of a diagnosis", 2)
    ms = ["retrain_on_alarm", "validation_first", "observational_attribution", "full_rollback", "bisect",
          "bugdoc_shortcut", "llm_report@luna", "llm_tools@luna", "dod", "dod2", "dod3", "dod4"]
    Ef = lambda v, w, r: P.ev(v, ".2f", ["runs/final (test split)", "runs/v2main/summary_v2.json",
                                         "runs/v3main/summary_v3.json", "runs/v4main/summary_v4.json"][r - 1],
                              f"Errors R{r}: " + w)

    def errs(r, m):
        if r == 1:
            fb, n1 = C.r1_mean(C.r1_test, m, lambda x: True, "false_blame")
            sm, n2 = C.r1_mean(C.r1_test, m, lambda x: x["has_cons"], "missed_defect")
        elif r in (2, 3):
            fb, n1 = C.tab(r, "All cases", m, "false_blame")
            sm, n2 = C.tab(r, CONS, m, "missed_defect")
        else:
            fb, n1 = C.tab(4, ALL4, m, "false_blame")
            sm, n2 = C.tab(4, CONS4, m, "silent_miss")
        return fb, sm, n1
    rows = []
    for m in ms:
        cells = []
        for r in rounds:
            fb, sm, n1 = errs(r, m) if (r < 4 or C.r4) else (float("nan"), float("nan"), 0)
            cells.append(f"{Ef(fb, m + ' false blame', r)} / {Ef(sm, m + ' missed', r)}" if n1 else "–")
        if any(c != "–" for c in cells):
            rows.append([NAMES[m]] + cells)
    P.table(["Method"] + [f"Round {r}" for r in rounds], rows,
            "False blame (share of all cases in which a fixed component is not an effective defect) / missed "
            "consequential defects (share of consequential cases in which one is neither fixed nor, for DoD-4, "
            "listed for review), per round. Round 1: test split. Methods are listed where they were run on all "
            "cases of a round; in round 4 the luna agents ran on the cases within the round's API allowance "
            "({tab:r4}).", "errors", col_widths_cm=[4.6] + [2.6] * len(rounds), font_pt=7.2)
    # share of the DoD versions' false blames that fall in cases spanning a published change
    fb_tot = fb_ev = 0.0
    for r in (2, 3):
        for m in ("dod", "dod2", "dod3"):
            a, na = C.tab(r, "All cases", m, "false_blame")
            e, ne = C.tab(r, "Cases spanning a published source change", m, "false_blame")
            if na and ne:
                fb_tot += a * na
                fb_ev += e * ne
    for rec in C.r1_recs:
        if rec["split"] == "test" and "dod" in rec["methods"]:
            pc = C.S.per_case(rec)["dod"]
            fb_tot += pc["false_blame"]
            fb_ev += pc["false_blame"] and bool(rec["obs"].get("source_events"))
    share = fb_ev / fb_tot if fb_tot else float("nan")
    dfb = [errs(r, m)[0] for r in (1, 2, 3) for m in ("dod", "dod2", "dod3") if errs(r, m)[2]]
    bm_miss = [errs(r, m)[1] for r in rounds for m in ("bisect", "bugdoc_shortcut")
               if (r < 4 or C.r4) and errs(r, m)[2]]
    src3 = "runs/final; runs/v2main/summary_v2.json; runs/v3main/summary_v3.json"
    P.para(
        "Every method that commits to a diagnosis traded one error for the other or made both ({tab:errors}). "
        "Retrain on alarm never blamed a component and missed every consequential defect; bisection and "
        "pipeline-instance debugging rarely blamed a healthy component but missed "
        f"{P.ev(min(bm_miss), '.2f', src3, 'min bisect/bugdoc missed')} to "
        f"{P.ev(max(bm_miss), '.2f', src3, 'max bisect/bugdoc missed')} of the consequential defects, depending on "
        "the round. In rounds 1–3 the DoD versions missed fewer but blamed a healthy "
        f"component in {P.ev(min(dfb), '.2f', src3, 'min DoD false blame rounds 1-3')} to "
        f"{P.ev(max(dfb), '.2f', src3, 'max DoD false blame rounds 1-3')} of all cases, and "
        f"{P.ev(share, '.2f', src3, 'share of DoD false blames at published changes')} "
        "of those false blames (rounds 1–3, all versions) fell in cases spanning a published change, where "
        "Theorem 3 limits what re-execution can decide; observational attribution, validation first and the LLM agent "
        "reading the report did badly on both."
        + (" DoD-4 is the only method in the study with both rates near zero; its cost is the review list."
           if C.r4 else ""))
    P.heading("Local versus end-to-end effectiveness", 2)
    L = C.lve
    src = "runs/posthoc_local_vs_e2e.json"
    tot = lambda r, pat: sum(v for k, v in L.get(f"round{r}", {}).items() if k.startswith(pat))
    ud_e = sum(L.get(f"round{r}", {}).get("unforced / differ / effective", 0) for r in rounds)
    ud_n = sum(L.get(f"round{r}", {}).get("unforced / differ / not effective", 0) for r in rounds)
    ue_e = sum(L.get(f"round{r}", {}).get("unforced / equal / effective", 0) for r in rounds)
    ue_n = sum(L.get(f"round{r}", {}).get("unforced / equal / not effective", 0) for r in rounds)
    fd_e = sum(L.get(f"round{r}", {}).get("forced / differ / effective", 0) for r in rounds)
    fd_n = sum(L.get(f"round{r}", {}).get("forced / differ / not effective", 0) for r in rounds)
    fe_e = sum(L.get(f"round{r}", {}).get("forced / equal / effective", 0) for r in rounds)
    Ev = lambda v, w, fmt=",d": P.ev(v, fmt, src, "LvE: " + w)
    P.para(
        f"Theorem 2 separates the two notions. Over the {Ev(ud_e + ud_n + ue_e + ue_n, 'unforced rollbacks')} "
        "rollback tests that the DoD versions ran on components that were not forced (θ∗_c = θ⁰_c; each case and "
        "component counted once), a *differ* verdict marked an effective "
        f"defect in {Ev(ud_e, 'unforced differ effective')} tests and a locally effective but not effective one in "
        f"{Ev(ud_n, 'unforced differ not effective')}"
        + (" (a timestamp-resolution defect from a library upgrade, in a case with a second, consequential "
           "defect upstream; its difference did not reach the final output)" if ud_n == 1 else "") + ", and an *equal* "
        f"verdict was never followed by an effective defect ({Ev(ue_e, 'unforced equal effective')} of "
        f"{Ev(ue_e + ue_n, 'unforced equal')}), as Theorem 2(b) requires. On forced components the same test "
        f"was uninformative: of {Ev(fd_e + fd_n, 'forced differ')} *differ* verdicts only "
        f"{Ev(fd_e, 'forced differ effective')} concerned an effective defect — the reference version usually "
        "cannot read the new encoding at all — and "
        f"{Ev(fe_e, 'forced equal effective')} *equal* verdicts hid one.")
    pr = L.get("round4_propagation", {})
    if pr:
        pd_e = pr.get("unforced / propagate differ / effective", 0)
        pd_n = pr.get("unforced / propagate differ / not effective", 0)
        pe_e = pr.get("unforced / propagate equal / effective", 0)
        pe_n = pr.get("unforced / propagate equal / not effective", 0)
        P.para(
            (f"In round 4, DoD-4 ran {Ev(pd_e, 'r4 propagation tests')} propagation tests, on unforced components "
             "whose rollback differed; every one returned *differ*, and every one concerned an effective defect, so "
             "none of the tested components was masked downstream."
             if pd_n == pe_e == pe_n == 0 else
             f"In round 4, DoD-4 ran {Ev(pd_e + pd_n + pe_e + pe_n, 'r4 propagation tests')} propagation tests on "
             f"unforced components: {Ev(pd_e, 'r4 propagate differ effective')} returned *differ* on an effective "
             f"defect, {Ev(pd_n, 'r4 propagate differ not effective')} on a non-effective one, and "
             f"{Ev(pe_n, 'r4 propagate equal not effective')} returned *equal* on a locally effective component "
             f"that was not effective ({Ev(pe_e, 'r4 propagate equal effective')} on an effective one)."))
    if getattr(C, "r4dev", None) and "dod4" in C.r4dev["tables"].get(ALL4, {}):
        D = C.r4dev
        Td = lambda t, m, k: (D["tables"].get(t, {}).get(m) or {}).get(k, float("nan"))
        Ed = lambda v, w, fmt=".2f": P.ev(v, fmt, "runs/v4dev/summary_v4_dev.json", "DoD-4 dev: " + w)
        P.heading("DoD-4 on the development domains", 2)
        P.para(
            "After the freeze, DoD-4 was run on all cases of the nine round-1/2/3 domains (development data from "
            f"round 4 on; {Ed(D['tables'][ALL4]['dod4']['n'], 'dev n', ',d')} cases; its rule was designed on these "
            "domains, so the results are in-sample). Its false-blame rate was "
            f"{Ed(Td(ALL4, 'dod4', 'false_blame'), 'dev false blame', '.3f')} and its silent-miss rate "
            f"{Ed(Td(CONS4, 'dod4', 'silent_miss'), 'dev silent miss', '.3f')}; it decided "
            f"{Ed(Td(ALL4, 'dod4', 'decided'), 'dev coverage')} of the cases, was correct on "
            f"{Ed(Td(ALL4, 'dod4', 'correct_decided') / Td(ALL4, 'dod4', 'decided') if Td(ALL4, 'dod4', 'decided') else float('nan'), 'dev correct where decided')} "
            f"of those, and listed {Ed(Td(ALL4, 'dod4', 'review_load'), 'dev review load')} components per case for "
            f"review ({Ed(D['hypotheses']['review']['dod4']['share'][0], 'dev review share')} of a pipeline's "
            "components, about the same share as in round 4). DoD-3 blamed a "
            f"healthy component in {Ed(Td(ALL4, 'dod3', 'false_blame'), 'dev dod3 false blame')} of the "
            f"{Ed((D['tables'][ALL4].get('dod3') or {}).get('n', 0), 'dev dod3 n', ',d')} development cases on which "
            "it had been run.")
    S = C.sens
    Es = lambda v, w, fmt=".2f": P.ev(v, fmt, "runs/posthoc_sensitivity.json", "Sensitivity: " + w)
    P.heading("Sensitivity to single domains and single changes", 2)
    parts = []
    for r in rounds:
        R = S.get(f"round{r}")
        if not R:
            continue
        m = R["method"]
        lodo = [x[m]["correct"] for x in R["leave_domain_out"].values() if m in x and x[m]["correct"] is not None]
        loeo = [x[m]["correct"] for x in R["leave_event_out"].values() if m in x and x[m]["correct"] is not None]
        if lodo and loeo:
            parts.append(f"round {r} ({NAMES[m]}: all {Es(R['all'][m]['correct'], f'r{r} all')}, leaving out one "
                         f"domain {Es(min(lodo), f'r{r} lodo min')}–{Es(max(lodo), f'r{r} lodo max')}, one published "
                         f"change {Es(min(loeo), f'r{r} loeo min')}–{Es(max(loeo), f'r{r} loeo max')})")
    P.para(
        "Leaving out one domain or all cases that span one published change moves each round's primary endpoint "
        "considerably — " + "; ".join(parts) + ". Round-level conclusions about which method diagnoses more "
        "consequential defects therefore rest on few domains and a handful of changes, which is why we keep "
        "rounds separate and never pool them for a test.")
    r4s = S.get("round4", {})
    if r4s:
        fbs = [x["dod4"].get("false_blame_all") for x in list(r4s["leave_domain_out"].values())
               + list(r4s["leave_event_out"].values()) if "dod4" in x and x["dod4"].get("false_blame_all") is not None]
        sms = [x["dod4"].get("silent_miss_cons") for x in list(r4s["leave_domain_out"].values())
               + list(r4s["leave_event_out"].values()) if "dod4" in x and x["dod4"].get("silent_miss_cons") is not None]
        if fbs and sms:
            P.para("DoD-4's error rates, unlike its correctness, do not depend on the composition: under every "
                   "leave-one-out set its false-blame rate was " + ("" if max(fbs) == 0 else "at most ")
                   + f"{Es(max(fbs), 'r4 max fb leave-out', '.3f')} and its silent-miss rate "
                   + ("" if max(sms) == 0 else "at most ") + f"{Es(max(sms), 'r4 max sm leave-out', '.3f')}.")
