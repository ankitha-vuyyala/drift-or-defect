# Protocol (DRAFT — becomes PROTOCOL.md, with code fingerprints, at the freeze)

## Data and cases
- Domains: ACS income (development domain), NYC taxi tipping, HuffPost news sections. Bronze layer and case
  generator as in code/dod (cases.generate, seed 7).
- Splits: all ACS cases are development (see docs/04_dev_log.md, item 6). TLC and news cases are split by defect
  type (DEV_DEFECTS) and, for clean/benign cases, by period index. **Test = TLC and news test cases.**
- Ground truth by execution (bench.ground_truth): effective and consequential defects (EPS 0.002), outcome of
  every canonical action on the holdout split with spec labels, correct action = fix consequential defects and
  retrain iff retraining after the fix gains > 0.01 accuracy.

## Methods (frozen configurations)
retrain_on_alarm, validation_first, observational_attribution, full_rollback, bisect, bugdoc_shortcut,
dod, dod_no_boundary, dod_b1, dod_b1_no_prior, dod_b1_uniform; LLM agent (report, tools) with the local model and
with gpt-5.6-luna under the approved cap. Thresholds: DELTA_RETRAIN 0.01, TAU_EFFECT, BOUNDARY_K, BOUNDARY_MIN
as set on development data (values recorded at the freeze).

## Primary endpoint
Action correctness ("correct": consequential ⊆ fix ⊆ effective and retrain decision equal to the oracle's) on
test cases.

## Hypotheses and tests (test split; development results reported separately)
- H1 (monitoring cannot see silent defects): among test cases with a consequential defect that passes all
  validation checks, every monitoring-only method (retrain_on_alarm, validation_first,
  observational_attribution, llm_report) has correctness ≤ 0.35; on loud consequential defects validation_first
  is ≥ 0.15 higher than on silent ones. Disproved if any monitoring-only method reaches ≥ 0.6 on silent ones.
- H2 (interventions resolve them): dod − best baseline on test cases with a consequential defect ≥ 0.15
  (paired cluster bootstrap, 95% CI excluding 0; clusters = domain × defect-type set).
- H3 (selection): under a budget of one full pipeline run, ratio ordering (dod_b1) ≥ topological ordering
  (dod_b1_uniform) in correctness on cases with a consequential defect; report mean compute of dod relative to
  bugdoc_shortcut and to one full pipeline run.
- H4 (outcomes): dod has lower unnecessary-retrain and missed-defect rates than retrain_on_alarm and
  validation_first, and lower fragility (accuracy loss of the chosen model after a later repair).
- H5 (limit): on source-coupled (T1) defects, rollback-only (dod_no_boundary) cannot certify the defect; the
  boundary test resolves cases where world smoothness holds; report failures (e.g. 2025 congestion pricing).
- Multiple comparisons: Holm over the H2 and H4 pairwise tests.

## Reporting
All numbers generated from saved records by analysis/summarize.py and analysis/figures.py; evidence index maps
each reported number to its records; negative results reported as found.
