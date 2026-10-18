# Protocol v2 (frozen before any method is run on a v2 domain)

The SHA-256 digest of this file, all code under `v2/code/` and `v2/analysis/`, the configuration under
`v2/config/`, and the v1 analysis module it imports (`analysis/summarize.py`) is recorded in
`runs/freeze_v2.json` by `v2/code/freeze.py`. `v2/code/run_cases.py` and `v2/code/run_llm.py` refuse to process
cases of a v2 domain if the digest differs. The v1 protocol (`PROTOCOL.md`, `runs/freeze.json`) and its results
are unchanged and are reported as pre-registered.

## 0. What happened before this freeze
- After the v1 test results were seen, a second method version (DoD-2, `v2/code/dod/methods_v2.py`,
  `v2/code/dod/diag_v2.py`) and its theory (`docs/07_theory_v2.md`) were developed using only data already seen in
  v1 (ACS, NYC taxi, news). Its results on those domains are development results and are labelled as such.
- Three new domains were chosen and built (data, pipelines, defect catalogs) before any diagnosis method was run
  on them. The benchmark construction checks (`v2/code/check_domains.py`) run only the correct pipelines and the
  reference models; they run no diagnosis method.
- During construction, each catalog entry was executed on a few periods to verify that defects change the
  pipeline output (and by how much the reference model's accuracy moves); this is ground-truth construction, not
  a diagnosis result. Catalog entries found to have no effect anywhere were replaced by an effective variant of
  the same idiom (Divvy and BTS chained-assignment steps).
- A crash-only smoke test ran every non-LLM method on two or three cases per v2 domain and printed only whether a
  method raised an exception (none did); no diagnosis, ground truth or outcome was displayed.
- DoD-2 development results on the v1 domains (`runs/v2dev`) were inspected before this freeze, to find bugs
  (not to tune on v2 data, which no method had touched).
- v1 method code (`methods.py`, `diag.py`, `bench.py`) is byte-identical in the v2 code tree.

## 1. Data, pipelines and cases
- Domains: `divvy` (Chicago bike-share trips, quarters 2014-Q1..2026-Q3), `hmda` (mortgage applications in CO,
  OR, TN, 2012-2025), `bts` (US airline on-time records, months 1/4/7/10 of 2015-2026). Pipelines in
  `v2/code/dod/domains/{divvy,hmda,bts}.py`; raw files in `data/raw_v2/MANIFEST.json` (URL, size, SHA-256);
  bronze layer by `v2/data/build_bronze_v2.py` (seed 20261005).
- Cases from `v2/code/dod/cases.py` (`generate`, seed 7). **Every case of a v2 domain is a test case.**
- Splits of records, ground truth, outcomes: identical to v1 (`bench.py` unchanged; BENCH_VERSION v3).
- Defect tiers: T1 source-coupled (forced or latent adapter defects at dated published changes), T2 library
  upgrade, T3 incident class, T3r replay of a documented real incident (source cited in the catalog entry);
  benign changes: B (refactors) and T2b (library upgrades without effect).

## 2. Methods
- All v1 methods with v1 constants, unchanged: `retrain_on_alarm`, `validation_first`,
  `observational_attribution`, `full_rollback`, `bisect`, `bugdoc_shortcut`, `dod`, `dod_no_boundary`, `dod_b1`,
  `dod_b1_no_prior`, `dod_b1_uniform`.
- DoD-2: `dod2` (history rule with M_HIST = 4 preceding transitions + mined invariants), ablations
  `dod2_no_inv` (history rule only) and `dod2_no_hist` (invariants with a one-transition history). Constants:
  those of DoD plus INV_HOLD = 0.98, INV_MIN = 0.01, permutation-informativeness factor 5 and margin 0.05.
- LLM agents as in v1 (`llm_report`, `llm_tools`; tools now also on the v2 domains). `gpt-5.6-luna` on all v2
  cases; `gpt-5.6-terra` on v2 cases with a consequential defect, every third such case in file order, until the v2 LLM
  allowance is used. **v2 LLM allowance: US$5.00** (within the approved total cap of US$18; v1 spent US$3.94).
  The coverage of each LLM run is reported.

## 3. Endpoints (as v1)
Primary: diagnosis correctness on cases with a consequential defect (consequential ⊆ fix set ⊆ effective
defects), pooled over the three v2 domains. Secondary: false blame, missed defects, full action correctness,
regret, fragility, compute, LLM spend; per domain and per tier.

## 4. Hypotheses (v2 domains; all cases are test cases)
- **H6 (DoD-2 vs DoD)** `dod2` is more correct than `dod` on the primary endpoint: paired difference > 0 with
  Holm-adjusted p < 0.05.
- **H7 (false blame at source changes)** On cases whose period range contains at least one published source
  change, `dod2` has a lower false-blame rate than `dod` (paired difference < 0, Holm-adjusted p < 0.05).
- **H8 (replication of H2)** `dod2` exceeds the best non-DoD baseline (best of the v1 baselines and LLM agents on
  the primary endpoint) by ≥ 0.15 with the 95% paired cluster-bootstrap interval excluding 0. The same comparison
  for `dod` (v1) is reported as the direct replication of H2.
- **H9 (replication of H1)** Monitoring-only methods achieve ≤ 0.35 on silent consequential defects; disproved if
  any reaches ≥ 0.60.
- **H10 (Theorem 5, descriptive)** Among consequential T1 defects, report `dod2` correctness separately for
  defects where a mined invariant flagged the component and where none did (invariant-blind defects), and the
  ablations `dod2_no_inv` and `dod2_no_hist`.
- Holm correction over the family {H6, H7, H8 (dod2), H8 (dod)}. Clusters: domain × defect signature;
  2000 resamples; seeds as in v1.

## 5. Reporting
Numbers are generated from saved records by `v2/analysis/summarize_v2.py` and the paper build. v1 and v2 results
are reported side by side and never pooled for a hypothesis test. Development results of DoD-2 on v1 domains are
labelled as development results. Negative results are reported as found.
