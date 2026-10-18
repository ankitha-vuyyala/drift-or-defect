# 03 — Study design (working draft)

Status: working draft, 5 Oct 2026. Frozen into PROTOCOL.md before the test split is touched.

## 1. Formal model

**Data flow.** A batch of raw records `R_t` arrives from external sources at period `t`. A pipeline is a DAG of
components `c ∈ C`; each component has a *version* `θ_c = (code variant, config, reference artifacts, library
environment)`. Features are `X_t = P_θ(R_t)`; a model `h` trained on `(X_0, Y_0)` predicts on `X_t`. Labels `Y_t`
arrive (possibly late). Raw records are produced from the world by a source encoding `σ_s` per source
(units, code lists, schema); `R_t = σ(W_t)`, with `W_t ~ D_t`.

**Explanations of a performance drop between the reference period 0 and period t.**
- *World change*: `D_t ≠ D_0` (covariate, label or concept shift), `θ` and `σ` unchanged in effect.
- *Pipeline change*: the set of changed components `Δθ = {c : θ_c,t ≠ θ_c,0}`. In real systems this set is
  rarely empty and mostly benign: refactors, dependency upgrades, legitimate reference-table refreshes, adapters
  updated for a new source schema. A *defect* is a change that is harmful; a *stale* component (a reference that
  should have been refreshed and was not) is a change relative to its specification `θ*_c,t`.
- *Source change*: `σ_t ≠ σ_0` (a schema, unit or code-list change at the provider).
Several can hold at once (compound cases).

**Actions.** `fix(c)` (restore or repair component c), `retrain`, `fix(c)+retrain`, `nothing`. The correct action
is defined by outcomes, not by labels we assign: for every case the oracle executes every action and scores it on
held-out labelled data from period t; the correct action is the cheapest one within δ of the best outcome.

**Observations available to a monitoring-only diagnostic.** The law of `(X_t, h(X_t), Y_t)`, reference
statistics of `(X_0, Y_0)`, the pipeline's lineage graph and change log (which components changed, but not
whether a change matters).

## 2. Results to prove (sketch)

**T1 (monitoring indistinguishability).** Let the world family 𝒟 allow arbitrary joint shifts of `(W, Y)`
(or any family closed under the shifts considered). A pipeline change `θ'` applied under world `D_t` is
indistinguishable from a pure world change for every monitoring-only diagnostic (with or without labels) iff
there is `D' ∈ 𝒟` with `(P_θ' ∘ σ)#D_t = (P_θ0 ∘ σ)#D'` jointly with `Y`, i.e. iff the corrupted feature law lies
in the *image* of the healthy pipeline. Any test then has type-I + type-II error ≥ 1. Corollary: support-level
validation catches exactly the defects whose feature law leaves the support of the healthy image ("loud"); no
monitoring signal separates "silent" defects (inside the image) from drift without assumptions on 𝒟.

**T2 (interventional identifiability).** If components are deterministic and their reference versions are
reproducible, then (a) a *rollback test* — re-execute c with `θ_c,0` (or `θ*_c,t`) on the current inputs to c
— reveals whether the change at c is *effective on the current data*; (b) a *replay test* — run the current
`θ_c,t` on archived reference inputs to c and compare with archived reference outputs — reveals whether the
function at c changed on the reference support; (c) an *effect test* — propagate the rolled-back output to the
model and score — reveals whether the change at c is responsible for (part of) the drop. Rolling back all
harmful effective changes yields `X̃_t = P_θ0(R_t)`; the residual drop is attributable to world or source change.
Hence every pipeline-change explanation is identified with at most `|Δθ|` rollback + effect tests.

**T3 (the limit).** A source change `σ_t` that maps into the image of `σ_0` (e.g. a unit change within plausible
range at the provider, with no schema signal) is indistinguishable from a world change by every combination of
monitoring and pipeline interventions; only side information (a contract, an overlap period, a second source)
separates them. The method must abstain there (H5).

**T4 (selection).** Tests are deterministic and have measured costs. Choosing tests to identify the *action*
(not the full hypothesis) is an equivalence-class determination problem; a greedy cost-weighted rule on the
EC² objective is within a logarithmic factor of the optimal expected cost (Golovin, Krause & Ray, 2010 — to
verify). Monitoring supplies the prior over hypotheses (components upstream of shifted features are more likely).

## 3. Method (DoD — "Drift or Defect" diagnoser)

1. Trigger: a performance alarm (labelled) or a drift alarm (unlabelled).
2. Hypotheses: `world`, `defect(c)` for each changed or stale component, `source(s)` for each source whose raw
   schema/profile changed, and pairwise compounds; prior from lineage-aware drift signals.
3. Repeat: pick the test (rollback / replay / effect / raw-contract check) with the best expected reduction of
   EC² weight per unit measured cost; run it; drop inconsistent hypotheses; stop when all remaining hypotheses
   agree on the action, or the budget is spent.
4. Compound: after `fix(c)`, compare the repaired model's performance to the reference; recommend `retrain` too
   if the residual drop exceeds δ.
5. Output: action, component(s), evidence trail, cost.

## 4. Benchmark

Three domains, each a real executable pipeline of ~8–12 components with versioned components, archived raw
inputs and archived intermediate outputs for the reference period.

- **ACS income (tabular)**: person + housing PUMS files, 2014–2024, CA/TX/NY. Components: person/housing source
  adapters, cleaning, household join on SERIALNO, inflation adjustment (ADJINC table), occupation crosswalk,
  feature derivation, label. Real dated changes: RELP → RELSHIPP (2019), OCCP to 2018 SOC (2018), 2020
  experimental release, SERIALNO format (to verify in the probe).
- **NYC taxi (spatio-temporal)**: yellow trip parquet files 2015–2026 (quarterly months). Components: schema
  adapter, timestamp parsing, cleaning, zone lookup join, fare decomposition, features, label (tip ≥ 20%).
  Real dated changes: 2016 coordinates → zone IDs, 2022 parquet migration, 2025 `cbd_congestion_fee` and
  payment type 0, column-case and dtype changes (to verify in the probe); real drift: COVID-2020, 2025 congestion
  pricing.
- **News headlines (text)**: HuffPost News Category 2012–2022. Components: ingest, text normalisation, category
  harmonisation table, vectoriser (fitted vocabulary artifact), features, label. Real changes: category taxonomy
  renames/merges over time (to verify).

**Change sets per case** mix harmful and benign changes so that "what changed" is not the answer:
benign refactors (identical outputs), dependency upgrades that do not matter, legitimate reference refreshes,
correct adapters for new schemas — alongside the defect.

**Defect tiers** (reported separately): T1 real dated source changes with a realistic adapter defect or staleness;
T2 real library behaviour changes executed in real environments (pandas 1.5 / 2.x / 3.0: `to_datetime`
inference, `datetime64[us]` epoch scaling, copy-on-write chained assignment); T3 documented incident classes
injected (stale reference table, join fan-out, unit change, stuck/default feature, missing component for a
slice, category-code reordering skew, timezone shift, feature lag).

**Case grid.** For each domain: world condition {no change (fresh sample of the reference period), real drift
at increasing temporal distance} × pipeline condition {no change, benign-only change set, change set containing
one defect (each defect), two defects} × trigger {performance alarm, drift alarm}. Every case is executed for
real; ground truth comes from the oracle action evaluation.

**Splits.** Defect *types* and periods are split into dev and test so the method cannot be tuned on test
defects: dev uses ~40% of defect types and earlier periods; test holds the rest.

## 5. Baselines (matched cost where they have a budget)

1. Retrain-on-alarm.
2. Drift-attribution heuristic: per-feature drift tests (KS/chi² as in Evidently/NannyML) + "retrain".
3. Validation-first workflow: schema/range/category checks learned on reference data (TFDV/Great Expectations
   style); validation failure → fix(component producing the failing feature, via lineage), else retrain.
4. Learned constraints by history (AVH-style) — if time permits.
5. Observational causal attribution over the dataflow graph (Paleyes & Lawrence style, anomaly attribution).
6. BugDoc-style Shortcut: swap known-good versions one at a time and re-run the whole pipeline, unweighted cost.
7. Bisection over the change set with full re-runs (git-bisect style).
8. Full rollback re-run (everything to reference versions): accurate on "is any defect present", no localisation.
9. LLM diagnostic agent: (a) monitoring report + lineage + change log, no tools; (b) same plus the re-execution
   tools under the same cost budget. Local model for development; one paid model under a hard cap later.
10. Oracle.

## 6. Metrics

Action accuracy; drift-vs-defect balanced accuracy; component localisation accuracy; unnecessary-retrain rate;
missed-defect rate; post-action model quality (AUROC / log loss on held-out period-t data) relative to the oracle
action; diagnosis cost (number of re-executions, compute seconds, dollars). Uncertainty by case-cluster bootstrap
(clusters = defect type × domain); paired comparisons with Holm correction.
