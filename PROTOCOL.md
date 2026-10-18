# Protocol (frozen before any test-split case is run)

The SHA-256 digest of this file together with all code under `code/` and `analysis/` and the configuration
under `config/` (except the budget file) is recorded in `runs/freeze.json` by `code/freeze.py`. `run_cases.py`
and `run_llm.py` refuse to process test cases if the digest differs.

## 1. Data, pipelines and cases
- Domains and pipelines as implemented in `code/dod/domains/{acs,tlc,news}.py`; bronze layer built by
  `code/data/build_bronze.py` (seed 20261005) from the raw files listed in `data/raw/MANIFEST.json`.
- Cases from `code/dod/cases.py` (`generate`, seed 7). **Splits.** All ACS cases are development cases (ACS was
  used to design the method; see `docs/04_dev_log.md` item 6). TLC and news cases are split by defect type
  (`DEV_DEFECTS`); clean and benign cases by period index (every third current period is development).
  **Test set = all TLC and news cases with split "test".**
- Records split by hashed id: 40% train, 30% serve (what diagnosers see, with labels as the deployed pipeline
  produces them), 30% holdout (grader only, labels from the correct pipeline).

## 2. Ground truth (by execution; `bench.ground_truth`)
- A changed component is an *effective defect* if replacing its version by the specification's changes the
  pipeline output; *consequential* if that replacement moves the holdout accuracy of "do nothing" or of
  "retrain" by ≥ 0.002.
- Correct action: fix the consequential defects; retrain iff retraining after the fix gains > 0.01 holdout
  accuracy.
- Every action a method recommends is executed and scored on the holdout split ("outcome"); for actions that
  retrain, the retrained model is also scored on features from the repaired pipeline ("score after repair").

## 3. Methods (configurations frozen)
`retrain_on_alarm`, `validation_first`, `observational_attribution`, `full_rollback`, `bisect`,
`bugdoc_shortcut`, `dod`, `dod_no_boundary`, `dod_b1`, `dod_b1_no_prior`, `dod_b1_uniform` (budget = one full
pipeline run of measured compute). Constants: DELTA_RETRAIN = 0.01, TAU_EFFECT = 0.003, BOUNDARY_K = 3.0,
BOUNDARY_MIN = 0.05 (none was changed after looking at development results). All methods share the same retrain
rule (retrain if the residual accuracy drop on labelled serve data is ≥ 0.01), so the retrain decision is
reported separately from the diagnosis.

LLM agents (`dod/llm_agent.py`): `llm_report` (monitoring report, lineage, change log, schema events; one answer)
and `llm_tools` (same, plus rollback / replay / effect / boundary tools under a budget of three full pipeline
runs, at most 8 tool turns). Model `gpt-5.6-luna` (reasoning effort low) on all test cases; `gpt-5.6-terra` on
test cases with a consequential defect, within the approved spend cap; responses cached for replay.

## 4. Endpoints
- **Primary:** diagnosis correctness on test cases with a consequential defect:
  consequential ⊆ fix set ⊆ effective defects.
- Secondary: diagnosis correctness on all test cases and on cases without a consequential defect (no false
  blame); full action correctness (diagnosis and retrain decision); regret against the best executed action;
  fragility (accuracy lost by a retrained model once the pipeline is repaired); unnecessary-retrain, missed-defect
  and false-blame rates; measured diagnosis compute; LLM spend.

## 5. Hypotheses (test split)
- **H1** Monitoring-only methods (`retrain_on_alarm`, `validation_first`, `observational_attribution`,
  `llm_report`) achieve diagnosis correctness ≤ 0.35 on *silent* consequential defects (cases whose model inputs
  pass every validation check), and `validation_first` is at least 0.15 higher on loud than on silent ones.
  Disproved if any of them reaches ≥ 0.60 on silent consequential defects.
- **H2** `dod` exceeds the best non-oracle baseline in primary-endpoint correctness by ≥ 0.15, with the 95%
  paired cluster-bootstrap interval excluding 0 (clusters = domain × defect signature; 2000 resamples).
- **H3** Under the one-run budget, ratio ordering (`dod_b1`) is at least as correct as topological ordering
  (`dod_b1_uniform`) on the primary endpoint; report mean compute of `dod` relative to `bugdoc_shortcut`.
- **H4** `dod` has lower missed-defect and false-blame rates than `retrain_on_alarm` and `validation_first`, and
  lower fragility than `retrain_on_alarm`.
- **H5** On source-coupled (T1) defects, `dod_no_boundary` (rollback only) is less correct than `dod`; failures of
  the boundary test where the world itself jumps at a schema event (e.g. 2025 congestion pricing) are reported.
- Pairwise tests for H2 and H4 are Holm-corrected. Development-split results are reported separately and labelled
  as such.

## 6. Reporting
Numbers in the paper are generated from saved records by `analysis/summarize.py`, `analysis/figures.py` and the
paper build; an evidence index maps each number to its records. Negative results are reported as found.
