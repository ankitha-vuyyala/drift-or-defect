# Protocol v4 (frozen before any method is run on a round-4 domain)

The SHA-256 digest of this file, all code under `v4/code/` and `v4/analysis/`, the configuration under
`v4/config/`, and the v1 analysis module it imports (`analysis/summarize.py`) is recorded in
`runs/freeze_v4.json` by `v4/code/freeze.py`. `v4/code/run_cases.py` and `v4/code/run_llm.py` refuse to process
cases of a round-4 domain if the digest differs. Rounds 1-3 (`PROTOCOL.md`, `v2/PROTOCOL_V2.md`,
`v3/PROTOCOL_V3.md`) and their results are unchanged and are reported as pre-registered.

## 0. What happened before this freeze
- Round 3 (frozen fb3229bd…) was run in full on three held-out domains (runs/v3main/summary_v3.md). Its main
  finding, together with rounds 1-2: interventional diagnosis was correct on every consequential case without a
  published source change in the period range (237 of 237 over rounds 1-3), and every method struggled where a
  published change forced a new component version (by-change analysis, runs/posthoc_by_change.json; not
  pre-registered).
- Following an external review, the theory was revised (Theorem 2: rollback detects local effectiveness;
  end-to-end effectiveness needs a propagation test) and the method was redesigned around the identifiability
  boundary of Theorem 3: DoD-4 (`v4/code/dod/methods_v4.py`) returns three verdicts (verified defect, healthy,
  unverified) and never fixes a component that a published change touches. Its design used the round-1/2/3
  domains only (all nine are development data from round 4 on).
- Development results on those nine domains, inspected before this freeze:
  - `runs/v4dev/*.llm_v4dev.jsonl` (`dod4_lite`, first version: unverified = changed components touched by a
    published change, plus unchanged touched components that read the source or introduce drift >= 0.05): no
    false blame, correct on every decided case, but 10 consequential defects in neither the fix set nor the review
    list (stale time-format parsers in the bike-share domains after the 2024-Q2 timestamp change; the parser is
    neither a source reader nor a drift source).
  - The rule was changed to the one Proposition 11 implies: every component touched by a published change,
    changed or not, is unverified; the pipeline's output step is excluded because it applies the model's fitted
    encoder, which is versioned with the model and changed only by retraining (in all eleven domains no published
    change forces a new version of it; checked from the specification states, not from results). Before the
    change, the `v4dev` records were recomputed offline with all touched components listed (`notes.coupled`):
    no consequential defect would have been left silent, at a mean review load of 0 to 5.2 components per
    case by domain. A development run of the first rule with DoD-3 evidence (`v4dev2`) was
    queued and withdrawn before it started (`jobs/held/086_*`). No development result of the final rule was
    inspected before this freeze: its development run on the nine domains (`runs/v4dev/*.llm_v4dev3.jsonl`,
    summary `runs/v4dev/summary_v4_dev.md`) is run after the freeze and reported as development data.
- The two round-4 domains (below) were chosen, downloaded and built after DoD-4 was designed. Their dated source
  changes were found from the published files (`data/bronze/<domain>/_profile.json`) before any method was run on
  them. Construction checks (`v4/code/check_domains.py` -> `runs/v4_checks/<domain>.json`) and a crash-only smoke
  test (`v4/code/smoke_v4.py` -> `runs/v4_checks/<domain>.smoke.txt`) were run before this freeze. While the
  domains were being built (before the checks): the storm grid cell was coarsened from 2 to 3 degrees (the
  categorical model input exceeded 255 levels), the codes 'AKST' and 'GST' were removed from the 1996-2005 time-zone
  table (they were not published before 2006), 'METEOROLOGIST(NON NWS)' was grouped as 'other', and a Chicago
  incident class that changed nothing on the data (an inner join; every crash has a vehicle record) was replaced
  by one that does (cyclists counted as pedestrians).

## 1. Data, pipelines and cases
Two public sources not used in rounds 1-3, each a three-table DAG with joins, about twice the size of the
round-1/2/3 pipelines (12 and 11 components):

| domain | source | periods | task | dated published changes |
|---|---|---|---|---|
| `storm` | NOAA NCEI Storm Events Database: event details, fatalities, locations; every record | 1996 .. 2025 | event with reported property damage | 2006 time-zone codes with UTC offset, source codes recased and renamed, indirect fatalities published, fatality-location codes extended, location file restricted to events with coordinates; 2007 old codes retired, Enhanced Fujita ratings, '0.00K' for no damage, 'Volcanic Ashfall', zone type 'M' retired; 2008, 2012, 2014, 2015 source codes added; 2016 'EFU' rating; 2021 daylight-time zone codes |
| `chicago` | City of Chicago Traffic Crashes: crashes, people, vehicles; 60,000 crashes per year (seeded sample) with all their person and vehicle records | 2016 .. 2025 | crash with an injury or a tow | 2017 citywide electronic reporting; 2019 revised report codes (trafficway intersection types, restraint detail, and others), first-contact-point distribution shift; 2020 contact-point corner and side codes; 2023 restraint codes retired |

Pipelines (`v4/code/dod/domains/{storm,chicago}.py`): three source adapters, an event or crash branch with time
and code-mapping steps (time-zone table, tornado scale, source crosswalk; delay, trafficway crosswalk), per-record
aggregates of the two child tables (fatalities and locations; people and vehicles), a three-input join, a grid
cell, cleaning in a pandas-1.5 environment, and categorical encoding with a fitted artifact. Crosswalk artifacts
are built from the published code lists (`build_artifacts`). Defect catalogs use the round-2/3 tiers (T1 stale or
faulty adaptations to the published changes, T2 environment upgrades, T3 incident classes, T3r public-incident
replays, benign B/T2b). Cases (`v4/code/dod/cases.py`, seed 7): reference periods storm 2003 and 2012, chicago
2018 and 2019; current periods: every year from the reference on. 871 cases (storm 640, chicago 231); all are
test cases. Ground truth, actions and consequentiality (EPS 0.002) as in rounds 1-3.

## 2. Methods
All round-1/2/3 methods with their constants (unchanged): `retrain_on_alarm`, `validation_first`,
`observational_attribution`, `full_rollback`, `bisect`, `bugdoc_shortcut`, `dod`, `dod2`, `dod3`; and DoD-4
(`dod4`) with `dod4_lite` (same verdicts, no DoD-3 evidence labels). LLM agents are supporting baselines:
`gpt-5.6-luna` (report and tool modes) on every chicago case and every second storm case; `gpt-5.6-terra` on every
fourth case with a consequential defect. **Round-4 LLM allowance: US$3.00** (total approved cap US$18; US$10.42
spent before this round), enforced per job: luna storm 1.00, luna chicago 0.80, terra storm 0.60, terra chicago
0.40 (worst case 2.80). A job that reaches its cap stops; the cases it did not reach are reported as not run.

## 3. Endpoints
Per case and method: F the fix set (for DoD-4 the verified defects), U the components listed for review (DoD-4's
unverified set; empty for every other method), C the consequential and E the effective defects
(`v4/analysis/metrics_v4.py`).
- false blame: F contains a component that is not an effective defect;
- silent miss: a consequential defect is in neither F nor U;
- decided: U is empty; coverage: share of decided cases;
- correct where decided: decided and C <= F <= E;
- review load: |U| (and |U| over the number of components).
The round-1 metrics (diagnosis correctness C <= F <= E, regret, retrain) are reported for every method as before.
Under DoD-4, a case with an unverified consequential defect is not diagnosis-correct.

## 4. Hypotheses (round-4 domains; all cases are test cases)
- **H15 (soundness)** DoD-4's false-blame rate over all cases is at most 0.02, and on cases spanning a published
  change it is lower than DoD-3's (paired difference < 0, Holm-adjusted p < 0.05).
- **H16 (completeness)** DoD-4's silent-miss rate on cases with a consequential defect is at most 0.02.
- **H17 (exact where decided)** On cases DoD-4 decides, its diagnosis is correct in at least 95% (all decided cases,
  and decided cases with a consequential defect, each).
- **H18 (identifiable regime)** On cases with a consequential defect and no published change in the period range,
  DoD-4's diagnosis is correct in at least 95%.
- **H19 (evidence, descriptive)** Among DoD-4's unverified components, the share of effective defects labelled
  'suspect' versus 'no evidence', and the AUC of the label for effective defects.
- Descriptive: coverage and review load per domain; false blame, silent misses and correctness of every method.
- Holm correction over the paired test(s) of H15. Clusters: domain × defect signature; 2000 resamples. H15-H18
  thresholds are one-sided criteria on the observed rates (no test).

## 5. Reporting
As in rounds 1-3; all four rounds are reported side by side and never pooled for a test.
