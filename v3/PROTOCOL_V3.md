# Protocol v3 (frozen before any method is run on a round-3 domain)

The SHA-256 digest of this file, all code under `v3/code/` and `v3/analysis/`, the configuration under
`v3/config/`, and the v1 analysis module it imports (`analysis/summarize.py`) is recorded in
`runs/freeze_v3.json` by `v3/code/freeze.py`. `v3/code/run_cases.py` and `v3/code/run_llm.py` refuse to process
cases of a round-3 domain if the digest differs. Rounds 1 and 2 (`PROTOCOL.md`, `v2/PROTOCOL_V2.md`) and their
results are unchanged and are reported as pre-registered.

## 0. What happened before this freeze
- Round 2 (frozen e50ee051…) was run in full on three held-out domains; its pre-registered hypotheses H6–H8 were
  not supported and H9 was disproved (v2/PROTOCOL_V2.md; runs/v2main/summary_v2.md).
- The round-2 failure analysis and the design of DoD-3 (`v3/code/dod/methods_v3.py`, `diag_v3.py`;
  `docs/10_theory_v3.md`) used the round-1 and round-2 domains only (now development data). Development results of
  DoD-3 on those six domains (`runs/v3dev`) were inspected before this freeze.
- The three round-3 domains (below) were chosen, downloaded and built after DoD-3 was designed. Their dated
  source changes were found from the published files (`data/bronze/<domain>/_profile.json`) before any method was
  run on them. Construction checks (`v3/code/check_domains.py` -> `runs/v3_checks/<domain>.json`: rows, label
  rates, missing rates of the model inputs under the correct pipeline, reference holdout accuracies) and a
  crash-only smoke test (`v3/code/smoke_v3.py` -> `runs/v3_checks/<domain>.smoke.txt`: whether each method raises,
  no diagnosis or score shown) were run before this freeze. Any change made after them is listed here:
  - after the construction checks, the code-list profile (`v3/data/codes_v3.py`) showed that FARS revised the
    ROUTE code list in 2023 and added codes to REL_ROAD (2018) and TYP_INT (2020); these were added to the
    domain's published changes, the correct pipeline maps 2023 route codes to the earlier list (new codes without
    a counterpart to 'Other'), and a T1 defect `fars.route_codes_stale` was added; the FARS construction check was
    rerun. The same profile showed bike-type code changes in the Washington bike-share files (2020-Q4, 2023-Q4),
    which were added to that domain's published changes (all adapter versions read them correctly); the house-sales
    code lists did not change (category B and type 'Other' records exist in every year in small numbers and grow
    from 2013).
  - the crash-only smoke test (8 cases per domain, every method) raised no exception; it was rerun on the final
    code after the changes below (`runs/v3_checks/*.smoke.txt`).
  - DoD-3 development results on the round-1/2 domains (`runs/v3dev/*.llm_v3dev2.jsonl`) showed a regression on
    news (latent stale section tables no longer flagged): the history rule abstained when the archive itself had
    fewer than three transitions before a change (news starts in 2012). The rule was changed before this freeze: it
    abstains only when history that exists cannot be read by the deployed versions, and otherwise uses the archived
    transitions down to one, as DoD did (`diag_v3.boundary_hist`). Development results after the change
    (`runs/v3dev/*.llm_v3dev3.jsonl`) recovered part of the news cases; the rest failed because a history
    transition into the previous published change (2013 to 2014, where the deployed table was itself stale) was
    counted as ordinary. Transitions into periods with another published change relevant to the component are now
    left out of the history statistics, as the exchangeability assumption of Proposition 7 requires
    (`skip` in `diag_v3.boundary_hist`, computed from all of the domain's published changes in `methods_v3`).
    Final development results: `runs/v3dev/*.llm_v3dev5.jsonl` (the `v3dev4` files were produced by the previous
    code because of a file-synchronisation error and are identical to `v3dev3`). Against `v3dev2`, DoD-3's
    development diagnosis rate on consequential cases rose on news (0.69 to 0.97) and fell slightly on mortgages
    (full domain: 0.55 in `v3dev3` to 0.50) and Chicago bike share (0.21 to 0.19); taxi, census and airlines were
    unchanged. No further change was made after `v3dev5`.

## 1. Data, pipelines and cases
Three public sources not used in rounds 1-2, each with a five-component pipeline in the style of rounds 1-2
(source adapter, feature steps, cleaning in a pandas-1.5 environment, categorical encoding with a fitted artifact):

| domain | source | periods | task | dated published changes |
|---|---|---|---|---|
| `cabi` | Capital Bikeshare trip files (Washington DC), 100,000 trips per quarter | 2014-Q1 .. 2026-Q3 | member vs casual rider | 2020-Q2 new layout (field names, member/casual codes, coordinates; duration and bike number removed; fractional-second times), 2020-Q3 blank station ids, 2020-Q4 and 2023-Q4 bike-type codes added and retired, 2024-Q2 fractional-second times |
| `fars` | NHTSA Fatality Analysis Reporting System, crash file, all records | 2010 .. 2024 | crash with two or more vehicles | 2011 person counts added, 2015 road-function code list replaced, 2016 name columns added, 2018 relation-to-road code added, 2020 weather fields removed and intersection-type code added, 2021 byte-order mark in the header, 2023 mark removed and route-signing code list revised |
| `landreg` | HM Land Registry Price Paid Data (England and Wales), 150,000 sales per year | 2008 .. 2025 | newly built property | 2013 category-B (non-standard) sales and property type 'Other' published |

Defect catalogs (`v3/code/dod/domains/*.py`, `catalog()`) use the round-2 tiers: T1 forced changes not made (stale
mapping for a published change), T2 environment upgrades with silent behaviour changes (pandas 3 copy-on-write,
datetime resolution), T3 internal defects of documented incident classes, T3r replays of public incidents, and
benign changes (B/T2b). Cases (`v3/code/dod/cases.py`, seed 7): reference periods cabi 2016-Q3 and 2019-Q2, fars
2011 and 2016, landreg 2010 and 2016; current periods: the reference season each year plus every period with a
dated change. 809 cases (cabi 312, fars 240, landreg 257); all are test cases. Ground truth, actions and
consequentiality (EPS 0.002) are computed by the executor as in rounds 1-2.

## 2. Methods
All round-1 methods with their constants (unchanged: `retrain_on_alarm`, `validation_first`,
`observational_attribution`, `full_rollback`, `bisect`, `bugdoc_shortcut`, `dod`, `dod_no_boundary`, `dod_b1`,
`dod_b1_no_prior`, `dod_b1_uniform`), DoD-2 (`dod2`, round 2, unchanged; its round-2 ablations are not rerun), and
DoD-3 (`dod3`) with ablations `dod3_no_latest` (round-3 changes off except the history and text-column changes in
diag_v3) and `dod3_no_inv`. The best baseline for H11 is the non-DoD method (round-1 baselines and LLM agents)
with the highest primary-endpoint mean on the cases it was run on, as in round 2; the paired test uses the cases
both methods were run on.
LLM agents as in rounds 1-2: `gpt-5.6-luna` on all round-3 cases; `gpt-5.6-terra` on every third case with a
consequential defect until the round-3 allowance is used. **Round-3 LLM allowance: US$4.00** (total approved cap
US$18; US$7.45 spent before this round).

## 3. Endpoints
As in rounds 1-2. Primary: diagnosis correctness on cases with a consequential defect, pooled over the round-3
domains.

## 4. Hypotheses (round-3 domains; all cases are test cases)
- **H11 (DoD-3 vs the best baseline)** `dod3` exceeds the best non-DoD baseline on the primary endpoint
  (paired difference > 0, Holm-adjusted p < 0.05); the minimum effect of interest is 0.10.
- **H12 (DoD-3 vs DoD)** `dod3` exceeds `dod` on the primary endpoint (Holm-adjusted p < 0.05).
- **H13 (false blame)** On cases whose period range contains a published source change, `dod3` has a lower
  false-blame rate than `dod` (Holm-adjusted p < 0.05).
- **H14 (no regression without source changes)** On cases without a published change, `dod3` and `dod` make the
  same diagnosis in at least 95% of cases.
- Holm correction over {H11, H12, H13}. Clusters: domain × defect signature; 2000 resamples.

## 5. Reporting
As in rounds 1-2; all three rounds are reported side by side and never pooled for a test.
