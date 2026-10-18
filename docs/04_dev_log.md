# 04 — Development log (decisions made before the protocol freeze)

This log records every design decision taken while looking at development data, so the test results can be
judged against it.

## 2026-10-05

1. **Benchmark source facts discovered in the published data** (runs/data_probe):
   - TLC re-published the 2015–2016 yellow files with zone ids; the July-2016 coordinate removal is therefore not
     replayable and was dropped from the plan.
   - ACS: SERIALNO format changes (2017, 2018), RELP→RELSHIPP / WKW→WKWN / JWTR→JWTRNS (2019), ST→STATE (2023),
     MLPI/MLPK→MLPIK (2021), VPS→VPSP (2024); TLC: dtype changes (2018-07), Airport_fee rename (2023-04),
     cbd_congestion_fee (2025-01), request_source (2026-07); news: section renames/merges (2014–2018), and many
     empty descriptions in 2014–2015 (a real source data-quality change, kept as a natural confounder).
2. **Library environments** (runs/t2_probe): pandas 2.2.3 with pyarrow 25 already keeps parquet timestamps in
   microseconds (pandas 1.5.3 + pyarrow 17 gives nanoseconds). The 2015-era TLC time step therefore runs in the
   p15 environment in the reference pipeline, and the upgrade to the main environment is a real T2 defect.
   The news pandas-3 upgrade turned out to be harmless on this source (no missing descriptions) and is a
   benign decoy.
3. **Ground truth**: defects are *effective* if fixing them changes the pipeline output, *consequential* if fixing
   them moves the holdout accuracy of 'nothing' or 'retrain' by ≥ 0.002. The correct action fixes the
   consequential defects and retrains iff retraining after the fix gains > 0.01 accuracy. Primary metric is
   accuracy at the deployed threshold (AUROC recorded as secondary), because retraining decisions are driven by
   label/threshold shift that AUROC ignores. Added after the first runs: the accuracy of a retrained model once
   the pipeline is repaired later ("fragility"), since retraining on corrupted features can recover accuracy
   while baking the corruption into the model.
4. **Encoders** assign category codes in order of first appearance (as pandas.factorize does), so re-fitting an
   encoder at serving time permutes codes (the realistic skew); with sorted codes the refit was a no-op.
5. **Method changes during development** (all made while looking at ACS cases, including ACS defect types that
   were originally assigned to the test split — see 6):
   - observational baseline strengthened to use drift *introduced* at each node of the dataflow graph from the
     archived intermediate outputs (fairer to Paleyes & Lawrence-style attribution);
   - boundary test redesigned: uses the deployment history (reference versions before the schema event, current
     versions at it), only columns the component creates or modifies, only events whose raw columns the
     component depends on (column-level lineage), and treats jumps already present at the component's inputs as
     inherited;
   - forced changes: a changed component downstream of a relevant schema event whose rollback *hurts* is not
     treated as beneficial without a boundary test (its reference version is not a valid known-good version).
6. **Split change (contamination disclosure).** While debugging the boundary test I ran ACS cases locally at
   p1 = 2019 and 2023 that included ACS defect types originally assigned to the test split. ACS is therefore
   re-designated a *development domain*: all ACS cases are reported as in-sample/development results. The
   held-out test set consists of the TLC and news test defect types (TLC: airport_case_stale, cbd_stale,
   clean_env_p30, do_key_bug, distance_km, encoder_refit; news: harmonise_stale, headline_only, vocab_refit) and
   the clean/benign cases of test periods. None of these has been run or inspected.
7. **Further method changes made on development cases** (ACS and the TLC/news development defect types):
   - a rollback that changes the label or the set of records is not graded by an accuracy comparison (accuracy
     over different labels/records is meaningless); unforced such changes are defects, forced ones go to the
     boundary test;
   - an unforced change (no relevant schema event upstream) whose rollback differs is an effective defect
     (Theorem 2) — the effect test is used only for forced changes and for the residual;
   - effect tests compare the deployed model on the records both versions keep;
   - the boundary test uses within-component column lineage (COLUMN_SOURCES) both to decide which output
     columns an event can affect and to recognise jumps inherited from source columns; losing records is a
     flag, regaining them is not; timestamps are excluded from drift statistics;
   - residual drop after a fix masks model inputs produced by source-coupled suspects (which cannot be rolled
     back) in both periods;
   - budgeted variants stop before any test once the budget is reached; order ablations without a budget were
     dropped because ordering cannot change an unbudgeted result.
8. **Engineering** (no effect on results by design): vectorised categorical encoding (verified identical keys),
   faster equality and drift statistics, an in-memory frame cache, retrying atomic cache writes (Windows),
   code- and artifact-content fingerprints in cache keys, and a cross-process spend ledger.
9. **Endpoint.** All methods share one retrain rule (residual drop ≥ 0.01). Development runs showed that this
   rule, not the diagnosis, drives most disagreements with the oracle's retrain decision (the oracle retrains
   when retraining *gains* > 0.01, which a drop-based rule cannot see). The primary endpoint is therefore the
   diagnosis (consequential ⊆ fix ⊆ effective); full action correctness is secondary. Decided before the freeze
   and before any test case was run.
10. **Constants** DELTA_RETRAIN 0.01, TAU_EFFECT 0.003, BOUNDARY_K 3, BOUNDARY_MIN 0.05 were set at design time and
    not tuned.
