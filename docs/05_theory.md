# 05 — Formal core (draft for the paper)

## Setting

- World records `W ∈ 𝒲` with labels `Y ∈ 𝒴` drawn from a distribution `D` on `𝒲 × 𝒴`; `𝔇` is the family of
  world distributions we are willing to entertain (covariate, label and concept shift).
- A *source encoding* `σ : 𝒲 → ℛ` turns world records into published raw records (schema, units, code lists).
- A pipeline is a DAG of deterministic components; with versions `θ` it computes features `X = P_θ(R)`.
  `θ*` is the *specification* for the current period (what a correct pipeline computes); `θ⁰` is the reference
  version (what was deployed when the model was trained).
- The deployed configuration is `(D, σ, θ)`. It is *defective* if `P_θ ≠ P_θ*` on the support of `σ(W)`.
- A *monitoring-only* diagnostic sees samples of the law `L(D,σ,θ) = law of (P_θ(σ(W)), Y)` under `D`, reference
  statistics, the lineage graph, and the change log `M(θ)` (which components changed, and which aspect).

## Theorem 1 (observational equivalence of silent defects)

Let `(D, σ, θ)` be defective. If there is `D′ ∈ 𝔇` and a non-defective `θ′` with `M(θ′) = M(θ)` such that
`L(D,σ,θ) = L(D′,σ,θ′)`, then every monitoring-only diagnostic `φ` satisfies
`P_{D,σ,θ}[φ = defect] = P_{D′,σ,θ′}[φ = defect]`, so its type-I plus type-II error on this pair is at least 1.

*Proof.* `φ` is a (possibly randomised) measurable function of observations whose joint law is identical under
the two configurations; its output law is therefore identical. ∎

**Corollary 1 (image characterisation).** Let `𝔇` contain all distributions on `𝒲 × 𝒴` and let a benign change
with the same change-log signature exist (e.g. a refactor of the same component). A defect is monitoring-equivalent
to a world change iff the corrupted features lie, almost surely, in the image `ℐ = P_θ*(σ(𝒲))` of the correct
pipeline. If instead the corrupted law puts mass `ε > 0` outside `ℐ`, a support check ("validation rule") against
`ℐ` detects it with probability `1 − (1−ε)^n` from `n` records, whatever the world does.

*Proof sketch.* (⇐) For each corrupted feature vector `x ∈ ℐ` choose a pre-image `w(x)` (measurable selection);
push the corrupted joint law of `(X,Y)` back through `w` to obtain `D′`; then `L(D′, σ, θ*) = L(D, σ, θ)`.
(⇒) Mass outside `ℐ` is impossible under every non-defective configuration, so a support test separates. ∎

So data-validation rules catch exactly the *loud* defects; *silent* defects (inside the image) are invisible to
drift tests, validation, label monitoring and any learned combination of them, unless one restricts `𝔇`
(e.g. assumes the world cannot change in particular ways).

## Theorem 2 (interventional identification of internal defects)

Assume components are deterministic, intermediate outputs of the production run are archived, and the reference
version `θ⁰_c` of every changed component is reproducible (code, config, artifacts and library environment).
For a changed component `c` whose change was not required by a source change (`θ*_c = θ⁰_c`):

(a) the rollback test — run `θ⁰_c` on `c`'s current inputs and compare with `c`'s current output — returns
*differ* iff `c` is an effective defect on the current data (exact equality, no statistical error);
(b) applying the rollbacks of all components that differ yields `P_θ*(σ(W))` on the current records, so the
remaining performance gap to the reference is attributable to the world (or source) alone;
(c) at most `|Δ|` single-component executions are needed, where `Δ` is the change set, versus `|Δ|` full
pipeline runs for pipeline-instance debugging and `⌈log₂|Δ|⌉` full runs per defect for bisection.

*Proof.* (a) With `θ*_c = θ⁰_c` and deterministic components, `c` is defective on the current inputs iff
`f_c^{θ_c}(I_c) ≠ f_c^{θ⁰_c}(I_c)`, which is exactly what the test compares. (b) follows by applying (a)
component-wise in topological order. (c) counts executions. ∎

For a change that *was* required by a source change (`θ*_c ≠ θ⁰_c`, e.g. an adapter for a new schema), the
reference version is not a valid known-good version: it may fail on the new inputs or legitimately differ.
Rollback cannot certify such components; this is where Theorem 3 applies.

## Theorem 3 (the limit: source-coupled changes)

Let the source encoding change from `σ⁰` to `σ¹`. If there is `D″ ∈ 𝔇` with `σ¹#D = σ⁰#D″` (the new raw records
are distributed as possible old-encoding records), then no diagnostic that uses monitoring *and any re-execution
of pipeline components on raw records* separates `(D, σ¹)` from `(D″, σ⁰)`: every such test is a function of raw
records whose law is the same in both configurations. The same holds for an adapter written for `σ¹` (correct or
not): its correctness is a property of `σ¹`, which no pipeline re-execution observes.

Side information breaks the tie. Our method uses one explicit, testable assumption: **world smoothness at
schema boundaries** — between adjacent periods, the world moves a feature's distribution by at most what it moves
it between ordinary adjacent periods. Under this assumption, a jump at a published schema event that exceeds the
ordinary period-to-period change is attributable to the encoding/adapter. When the world genuinely jumps at the
same time (e.g. congestion pricing starting with the new fee column), the assumption fails, and we report it.

## Proposition 4 (test ordering)

Under a single-fault prior with probabilities `p_c` and test costs `k_c`, testing candidates in decreasing
`p_c / k_c` minimises the expected cost of finding the faulty component (classical optimal-search result for
sequential testing, cf. Gluss 1959). With a compute budget, the same ratio order maximises the expected prior mass
resolved. Our method uses monitoring evidence (drift introduced at each node of the dataflow graph, validation
failures, source coupling) for `p_c` and the measured execution time of `c` for `k_c`.

## What this predicts for the experiments

- H1: monitoring-only methods (drift tests, validation-first, observational attribution on the dataflow graph,
  an LLM reading the monitoring report) separate drift from defects well only for loud defects.
- H2: rollback tests resolve internal defects (T2 library upgrades, T3 incidents) exactly.
- H5: source-coupled defects (T1) are not identifiable by re-execution; the boundary test resolves them only
  where world smoothness holds.

## References to verify for the paper

- B. Gluss, "An optimum policy for detecting a fault in a complex system," Operations Research 7(4):468–477, 1959
  (verified via IDEAS/RePEc).
