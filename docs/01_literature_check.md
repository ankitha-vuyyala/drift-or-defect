# 01 — Literature check and proposed claim

Status: draft for approval · 5 Oct 2026
Working title: *Is It Model Drift or a Broken Pipeline? Intervention-Based Diagnosis of Production ML Degradation*

---

## 1. The question in one paragraph

A production model's accuracy drops. Two families of explanation produce that symptom. **World change**: the prediction problem itself moved (covariate shift, label shift, concept drift); the fix is to retrain. **Pipeline defect**: the data-processing system changed (a faulty join, a unit change, a stale lookup table, a schema change upstream, training/serving skew, a library upgrade that silently changes values); the fix is to repair the pipeline, and retraining on corrupted features makes things worse or hides the bug. Monitoring stacks see only the *output* of the pipeline: features, predictions and (late) labels. This paper asks when those observations can tell the two apart, shows that for an important class of defects they provably cannot, and gives a cost-aware method that resolves those cases by re-executing a few pipeline components, then recommends **fix the pipeline, retrain, both, or do nothing**.

## 2. Closest prior work

Flags: **(a)** treats pipeline defects and genuine shift as competing explanations · **(b)** uses interventions / re-execution · **(c)** chooses interventions under a cost budget · **(d)** formal identifiability result · **(e)** evaluates on real, documented defects. Y = yes, ~ = partial, N = no.

### 2.1 Interventional debugging of pipelines and programs (the closest *method* threats)

| Work | What it does | a | b | c | d | e |
|---|---|---|---|---|---|---|
| **BugDoc** — Lourenço, Freire, Shasha, SIGMOD 2020 / VLDB J. 2023 [arXiv 2004.06530] | Re-runs pipeline instances to find the minimal parameter/component settings that cause a failure; "Shortcut" swaps known-good values into the failing run one at a time. | N | **Y** | ~ (instance count) | N | ~ (3 real pipelines, not ML-degradation incidents) |
| **AID** (Causality-Guided Adaptive Interventional Debugging) — Fariha, Nath, Meliou, SIGMOD 2020 | Forces suspect predicates to their passing-run values and re-executes; approximate causal graph + group testing to minimise interventions. | N | **Y** | **Y** (count) | N | Y, but concurrency bugs, not data |
| **DataPrism** — Galhotra, Fariha, Lourenço, Freire, Meliou, Srivastava, SIGMOD 2022 | Finds data profiles that differ between passing/failing inputs, transforms the failing data to match, re-runs to confirm cause; greedy selection uses far fewer interventions than BugDoc. | N (a label-encoding mismatch and a natural shift are treated alike) | **Y** | ~ (count) | N | ~ (7 case studies) |
| **mlwhatif** — Grafberger, Guha, Groth, Schelter, PVLDB 16(12) 2023 | Extracts a pipeline's dataflow plan, patches it into what-if variants, executes them with shared computation. | N | Y | N (runs all variants cheaper, does not select) | N | N |
| **SAVAGE** (Stress-Testing ML Pipelines with Adversarial Data Corruption) — Zhu et al., PVLDB 18(11) 2025 | Searches for high-impact structured corruptions of a black-box pipeline. | ~ | Y | N | N | N |

### 2.2 Causal / observational diagnosis of shifts and pipeline faults (the closest *framing* threats)

| Work | What it does | a | b | c | d | e |
|---|---|---|---|---|---|---|
| **Causal Fault Localisation in Dataflow Systems** — Paleyes & Lawrence, EuroMLSys 2023 [arXiv 2304.11987] | Treats the dataflow graph as a causal graph and attributes an anomaly to input-data shift or a buggy component (DoWhy-GCM, Shapley). | **Y** | N (observational) | N | N | N |
| **Tracing Distribution Shifts with Causal System Maps** — Leest, Gerostathopoulos, Raibulet, Lago, arXiv 2510.23528 (2025); survey *From Tea Leaves to System Maps*, arXiv 2506.10770 | Vision: layered causal maps of an ML system to decide whether a shift is a software fault, a data-quality issue or natural change. No method, theorem or evaluation. | **Y** (conceptual) | N | N | N | N |
| Zhang et al., *"Why did the model fail?"*, ICML 2023; Budhathoki et al., *Why did the distribution change?*, AISTATS 2021 | Shapley attribution of a performance/distribution change to causal mechanisms; known graph. | ~ | N | N | ~ | N |
| Cai, Namkoong, Yadlowsky, *DISDE*, 2023; Singh et al., hierarchical decomposition, NeurIPS 2024; *SHIFT*, ICML 2025; Liu et al., *WhyShift*, NeurIPS 2023 D&B | Decompose a performance drop into X-shift, Y|X-shift and unseen-support parts. All assume features are recorded correctly. | N | N | N | ~ | N |
| Rabanser et al., *Failing Loudly*, NeurIPS 2019; Lipton et al., BBSE, ICML 2018 | Shift detection; label-shift identifiability via the confusion matrix. | N | N | N | ~ | N |
| Microservice RCA: Ikram et al. (RCD), NeurIPS 2022; Jha et al., interventional fault localisation, DSN 2024 | Causal RCA for services; Jha et al. inject faults as interventions. | N | ~/Y | N | ~ | ~ |
| Root-cause identifiability: Li et al., JRSSB 2025 [arXiv 2410.12151]; Orchard/Okati et al., NeurIPS 2025 | When is the root cause identifiable from one interventional/anomalous sample (linear SEMs, polytrees)? | N | N | N | **Y** | N |

### 2.3 Data validation and monitoring (what practitioners run)

| Work / tool | What it does | a | b | c | d | e |
|---|---|---|---|---|---|---|
| Breck et al., *Data Validation for ML* (TFDV), SysML 2019 | Schema checks, training/serving skew and drift comparators at Google; reports per-anomaly alert and fix rates over 700+ pipelines. | ~ (flags, does not attribute) | N | N | N | production anecdotes |
| Deequ (Schelter et al., PVLDB 2018); Great Expectations; Auto-Validate (Song & He, SIGMOD 2021); **Auto-Validate-by-History** (Tu et al., KDD 2023) | Declarative or learned data-quality constraints; AVH learns constraints from past runs with false-positive guarantees (benign drift is just a false positive). | N | N | N | N | AVH: 3 known incidents |
| **PrismaDV** — Chen, Phani, Schelter, arXiv 2604.21765 (2026) | LLM reads downstream task code to generate task-aware data unit tests; separates harmful from benign data changes. | ~ | ~ (runs downstream tasks for feedback) | N | N | N (synthetic injection) |
| Shankar et al., *GATE / Moving Fast With Broken Data* (Meta, 2023); *Towards Observability for Production ML Pipelines* (PVLDB 2022) | Partition-level validation; vision of detect → diagnose → react with mltrace. | Y (vision) | N | ~ | N | N |
| Evidently, NannyML, Alibi Detect, WhyLabs/whylogs | Drift tests, label-free performance estimation (NannyML CBPE assumes no concept drift), data-quality presets. Evidently's own guide says "run quality checks first, then drift", a workflow, not a diagnosis. | N | N | N | N | N |

### 2.4 Provenance, inspection and data debugging (development-time)

mlinspect (VLDB J. 2022), ArgusEyes (SIGMOD 2023 demo), Datascope (ICLR 2024), Rain (SIGMOD 2020), Gopher (SIGMOD 2022), Data X-Ray (SIGMOD 2015), Maro (MAPS 2022), notebook slicing (PVLDB 2022), and the ICDE'24/SIGMOD'25 tutorial *Navigating Data Errors in ML Pipelines*. They instrument pipelines or attribute errors to training tuples. None separates defects from world change in production. mlinspect/mlwhatif are reusable infrastructure for lineage extraction.

### 2.5 Evidence that the problem is real

- Papasian & Underwood (Google), *How ML Breaks: A Decade of Outages for One Large ML Pipeline*, OpML 2020: most outages are not ML-centric.
- Uber D3 blog: an app experiment dropped a fare component for 10% of sessions in key cities; undetected for 45 days at a cost of "millions of dollars"; partial-data incidents took 5× longer to detect than ETL failures.
- Breck et al. 2019: a serving RPC failure pinned a feature to −1 for a slice; features missing only at serving in Google Play (fixing it raised installs 2%).
- Foidl et al., JSS 2024: 100 GitHub issues + 400 Stack Overflow posts; incorrect data types cause 33% of data-pipeline issues.
- Shankar et al. interview study (CSCW 2024) and Sambasivan et al. *Data Cascades* (CHI 2021).

### 2.6 LLM agents

No 2025–2026 paper was found that uses an LLM agent to diagnose drift-versus-defect in ML pipelines. LLM RCA work is on cloud microservices (e.g. MetaRCA, FSE 2026) and is observational. PrismaDV uses an LLM to write data tests, not to diagnose degradation. A generic LLM diagnostic agent is therefore a fair, novel baseline rather than a prior method.

## 3. What this paper adds — and an honest incremental check

**The gap.** Every attribution method assumes features are recorded correctly. Every validation tool raises alarms but does not say *why*. The two papers that do pose the drift-versus-defect question (Paleyes & Lawrence; Leest et al.) are observational, and Leest et al. is a vision paper without evaluation. The interventional debuggers (BugDoc, AID, DataPrism) re-execute, but treat any difference between a good and bad run as "the bug": they have no notion that the world may have legitimately changed, no fix-vs-retrain decision, and they minimise a count of runs rather than the compute cost of re-executing parts of a lineage graph.

**What we would contribute.**
1. **An identifiability result.** We model degradation as a change in the raw-data distribution (the world), in pipeline components (code, config, reference data, library versions), or in an external source's semantics. We show that a defect is *invisible to any monitoring-only test*—including ones with labels—exactly when its output distribution lies inside the image of the reference pipeline (a "silent" defect). Validation rules can only catch defects outside that image. We then show which re-executions separate the explanations: component rollback on current inputs and replay of archived known-good inputs through current components resolve every defect whose known-good version is reproducible; a silent semantic change in an *external* source stays indistinguishable from world drift without side information (a stated, tested limit).
2. **A cost-aware diagnosis method.** Interventions are deterministic tests over a hypothesis space (world drift, defect at component *c*, source change at *s*, compound). Because the decision we need is the *action* (fix where / retrain / both / nothing), not the full hypothesis, we select re-executions with an equivalence-class objective weighted by each step's measured compute cost on the lineage graph, using monitoring signals only as a prior over which components to test. This targets a provable logarithmic approximation to the optimal expected cost (adaptive-submodularity / EC² line of work — to be verified and cited precisely). For compound cases the method repairs first, then measures the residual drop on repaired features to decide whether retraining is also needed.
3. **A released benchmark** of executable pipelines in three domains with genuine temporal drift and *real, dated* defects (source recodes, schema changes, real library upgrades executed with the real library versions), plus documented-incident-class injections, and compound drift+defect cases.
4. **Evidence about practice**: how often practitioner stacks (drift monitors, validation-first workflows, retrain-on-alarm) retrain when they should fix, miss silent defects, or fix when nothing is wrong.

**Honest verdict on novelty.** Moderate-to-strong if the formal result and the benchmark land; weak if we ship only the method.
- The main reviewer objection will be *"rolling back a component and re-running is obviously informative; this is BugDoc / git-bisect for production."* Our defence must be (i) the theorem that says *precisely* which degradations need intervention and which cannot be resolved even with it, (ii) the joint world-plus-pipeline hypothesis space and the action-level objective (BugDoc/DataPrism have neither), (iii) cost on real lineage graphs, where naive full re-runs or topological bisection are much more expensive, and (iv) realistic complications that make it non-trivial: non-deterministic steps, as-of-now joins, partially versioned pipelines, compound cases.
- The second risk is that simple schema/range validation already catches most *real* defects. If the benchmark shows that, the contribution shrinks to silent and compound cases. We will measure this honestly (H1 below) and report it either way; it is itself a useful finding.
- The third is that Leest et al. or a 2026 follow-up (an ACM paper "Explaining Shifts in ML Systems with Causal Maps", not accessible to verify) operationalises the same question. We will re-check right before writing.

**Venue fit.** VLDB/SIGMOD (BugDoc, DataPrism, mlwhatif, AVH and TFDV all live there) or MLSys; NeurIPS Datasets & Benchmarks if the benchmark becomes the lead contribution.

## 4. Proposed claim

> **Monitoring cannot separate model drift from silent pipeline defects, but a few targeted re-executions can.** Any defect whose outputs lie within what the healthy pipeline could have produced is observationally equivalent to a world change, for every monitoring-only diagnostic, with or without labels. A lineage-guided, cost-aware sequence of component re-executions resolves exactly those cases that have a reproducible known-good version. On real pipelines with real drift and real defects, it chooses the right action (fix, retrain, both, or nothing) far more often than practitioner monitoring and validation stacks, avoids most unnecessary retrains, and costs a small fraction of a full pipeline re-run.

## 5. Falsifiable hypotheses and what would disprove them

Preregistered thresholds will be finalised in the protocol freeze after the pilot; the values below are the starting proposal.

| # | Hypothesis | Disproved if |
|---|---|---|
| **H1** — silent defects defeat monitoring | On silent defects, the best monitoring-only baseline (drift tests, validation-first workflow, observational causal attribution, LLM agent without re-execution) has drift-vs-defect balanced accuracy near chance (≤ 0.65), while on loud defects (outside the pipeline's image) validation does well (≥ 0.85). | A monitoring-only baseline reaches ≥ 0.80 balanced accuracy on silent defects. |
| **H2** — interventions resolve them | The method's action accuracy on silent and compound cases is ≥ 0.90 and beats the best baseline by ≥ 0.15 at matched cost (cluster bootstrap CI excludes 0). | Gap < 0.15 or CI includes 0. |
| **H3** — cost-aware selection matters | Mean diagnosis cost ≤ 25% of a full pipeline re-run, and the cost-aware action-level selector beats unweighted / topological / random orderings and BugDoc-style Shortcut at equal accuracy. | Simple orderings are within 10% of its cost. |
| **H4** — better outcomes | Fewer unnecessary retrains and missed defects than retrain-on-alarm and validation-first, and post-action model quality within a small margin of the oracle action. | Post-action quality not better than retrain-on-alarm. |
| **H5** — the predicted limit | For silent semantic changes in external sources (no reproducible known-good version), the method cannot separate them from drift and should abstain ("source change or drift"), as the theory predicts. | It "succeeds" there, which would mean the benchmark leaks information, or it fails on cases the theory says are resolvable. |

## 6. Study design sketch (to be refined after the inventory)

**Domains and data (all free, raw inputs available, laptop-sized subsets).**
- *Tabular*: US Census ACS PUMS via folktables, 2014–2023, a few states. Real drift (incl. COVID-2020). Real recodes: `RELP` → `RELSHIPP` (2019), `OCCP` moved to 2018 SOC codes, 2020 1-year release only as experimental estimates. Reference-data step: inflation adjustment table (stale-table defects).
- *Spatio-temporal / time series*: NYC TLC yellow taxi trips (tip or zone-hour demand). Real drift: seasonality, COVID, 2025 congestion pricing. Real changes: 2016 lat/lon → zone IDs, 2022 CSV → Parquet, 2025 `cbd_congestion_fee` column and payment code 0 "Flex Fare". Citi Bike (Feb 2021 schema change, local-time DST quirks) as a backup.
- *Text*: HuffPost News Category 2012–2018 (CC0). Real drift in topics; real label-taxonomy changes at the source (to verify in the inventory); tokenizer/vocabulary as a stale-artifact component.

**Defect tiers, reported separately.** T1 real dated source changes replayed at their real dates; T2 real library behaviour changes executed with the real library versions (pandas 2.0 `to_datetime` format inference, pandas 3.0 `datetime64[us]` default and copy-on-write chained assignment, scikit-learn 1.2 defaults); T3 documented incident classes injected (Uber missing component for a slice, Google stuck feature, km vs miles, join fan-out, stale reference table, training/serving skew). Each also appears in a compound version with genuine drift, plus no-defect/no-drift false alarms.

**Pipelines.** Real executable DAGs (DuckDB/pandas + scikit-learn) with versioned components and archived raw inputs, so re-execution is exact and its cost is measured in seconds, not assumed.

**Baselines at matched cost.** Retrain-on-alarm (Evidently / NannyML signals); validation-first workflow (Great Expectations / TFDV-style schema + range, then drift); learned constraints (AVH-style); observational causal attribution on the dataflow graph (Paleyes & Lawrence via DoWhy-GCM); BugDoc-style Shortcut re-execution; full pipeline re-run diff (expensive accuracy reference); a generic LLM diagnostic agent with monitoring reports, lineage and logs, in two variants (no tools; with the same re-execution tools and budget); oracle action.

**Ablations.** No lineage prior; uniform costs; hypothesis-level vs action-level objective; component rollback only (no input replay); no compound handling; partial versioning (some components not reproducible).

**Grading is all code.** Ground-truth cause and correct action are known by construction for every case; recovery is measured by applying the recommended action and re-scoring on held-out labelled data.

**Budget.** The method uses no LLM. Paid calls are only for the LLM baseline; development on a free local model, then one paid model under a hard cap agreed after the pilot.

## 7. Sources checked

Interventional debugging: BugDoc https://arxiv.org/abs/2004.06530 · AID https://par.nsf.gov/servlets/purl/10172474 · DataPrism https://afariha.github.io/papers/DataPrsim_SIGMOD_2022.pdf · mlwhatif https://www.vldb.org/pvldb/vol16/p4002-grafberger.pdf · SAVAGE https://arxiv.org/abs/2506.01230

Framing threats: Paleyes & Lawrence https://arxiv.org/abs/2304.11987 · Leest et al. https://arxiv.org/abs/2510.23528 and https://arxiv.org/abs/2506.10770

Shift attribution: Zhang et al. https://proceedings.mlr.press/v202/zhang23ai.html · Budhathoki et al. https://arxiv.org/abs/2102.13384 · DISDE https://arxiv.org/abs/2303.02011 · Singh et al. NeurIPS 2024 https://neurips.cc/virtual/2024/poster/93686 · SHIFT https://arxiv.org/abs/2506.00756 · WhyShift https://proceedings.neurips.cc/paper_files/paper/2023/hash/a134eaebd55b7406ff29cd75d5f1a622-Abstract-Datasets_and_Benchmarks.html · Kulinski & Inouye https://proceedings.mlr.press/v202/kulinski23a.html · Failing Loudly https://arxiv.org/abs/1810.11953 · BBSE https://proceedings.mlr.press/v80/lipton18a.html · TableShift https://arxiv.org/abs/2312.07577

RCA and identifiability: RCD https://neurips.cc/virtual/2022/poster/52853 · Jha et al. DSN 2024 https://saurabhjha.one/pubs/DSN2024c/paper.pdf · Li et al. https://arxiv.org/abs/2410.12151 · Orchard/Okati et al. https://arxiv.org/abs/2406.05014

Validation and monitoring: Breck et al. https://mlsys.org/Conferences/2019/doc/2019/167.pdf · AVH https://arxiv.org/abs/2306.02421 · PrismaDV https://arxiv.org/abs/2604.21765 · GATE https://arxiv.org/abs/2303.06094 · Observability https://www.vldb.org/pvldb/vol15/p4015-shankar.pdf · NannyML https://nannyml.readthedocs.io/en/stable/how_it_works/performance_estimation.html · Evidently https://www.evidentlyai.com/ml-in-production/data-drift

Evidence and data: How ML Breaks https://www.usenix.org/conference/opml20/presentation/papasian · Uber D3 https://www.uber.com/blog/d3-an-automated-system-to-detect-data-drifts/ · Foidl et al. https://arxiv.org/abs/2309.07067 · Shankar et al. interview https://arxiv.org/abs/2209.09125 · folktables https://github.com/socialfoundations/folktables · ACS RELSHIPP https://api.census.gov/data/2019/acs/acs1/pums/variables/RELSHIPP.json · ACS user note https://www.census.gov/programs-surveys/acs/technical-documentation/user-notes/2020-02.html · NYC TLC https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page · TLC data dictionary https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf · pandas 2.0 https://pandas.pydata.org/pandas-docs/stable/whatsnew/v2.0.0.html · pandas 3.0 https://pandas.pydata.org/docs/whatsnew/v3.0.0.html · Citi Bike https://citibikenyc.com/system-data · Wild-Time https://github.com/huaxiuyao/Wild-Time

Not yet verified (pages blocked): "Explaining Shifts in Machine Learning Systems with Causal Maps" (ACM, doi 10.1145/3793653.3793782); "Towards the Localization of Multi-Root-Cause Failures in Microservice Systems: An Active Intervention Framework" (ACM, doi 10.1145/3808180). Both get re-checked before writing. Every reference is verified again at the paper stage.
