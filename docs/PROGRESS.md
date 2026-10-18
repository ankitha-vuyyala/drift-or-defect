# Progress

Last updated: 2026-10-18 UTC

| Stage | Status |
|---|---|
| Round 1 (protocol `PROTOCOL.md`, freeze 8eab1e0e…) | Done: 702 cases (census dev, taxi, news), 0 errors; LLM agents luna (all) and terra (consequential test cases) |
| Round 2 (`v2/PROTOCOL_V2.md`, freeze e50ee051…) | Done: 1,000 cases (Chicago bike share, mortgages, airlines), 0 errors |
| Round 3 (`v3/PROTOCOL_V3.md`, freeze fb3229bd…) | Done: 809 cases (Washington bike share, fatal crashes, house sales), 0 errors |
| Round 4 (`v4/PROTOCOL_V4.md`, freeze 9543f4c5…) | Done: 450 cases (storm: fixed 1-in-3 subsample of 219 of 640; Chicago crashes: all 231), 0 errors; LLM agents within the round's $3.00 allowance (luna 330 of 341 planned cases, terra 18). Execution details: `v4/EXECUTION_NOTES_V4.md` |
| DoD-4 on the nine development domains (`runs/v4dev/*.llm_v4dev3.jsonl`) | Done: 2,511 cases, 0 errors (development data, in-sample): false-blame and silent-miss rates 0.000, decided 0.30 (all correct), 2.31 components per case for review; summary `runs/v4dev/summary_v4_dev.md` |
| Paper | Draft: `paper/drift_or_defect.docx` + `.pdf`; numbers recomputed from the raw records by an independent agent; references checked; evidence index in `paper/evidence_index.md` |
| Public repo | Prepared for GitHub: README, LICENSE, CITATION.cff, requirements.txt, .gitignore (raw data, environments, runner state and local notes excluded) |

Spend: $12.49 of the $18 cap (`runs/cost_ledger.json`).

## Headline results
- Silent consequential defects (200 over rounds 1–3): retrain-on-alarm and validation-first diagnosed none.
- Consequential cases without a published source change in their period range (267 over four rounds, post-hoc
  split): the round's DoD version was correct on all of them.
- Round 4 (pre-registered H15–H18 all supported): DoD-4 false-blame rate 0.000 (450 cases), lower than DoD-3 on
  cases spanning a published change (−0.05, Holm p < 0.001); silent-miss rate 0.000 (256 consequential cases);
  correct on all 51 cases it decided and on all 30 consequential cases without a published change. Price: it
  decided 0.11 of the cases and listed 5.3 components per case for review; counting fixes only, it was correct on
  0.61 of consequential cases against 0.68 for the best method that always commits.
- Rounds 1–3: primary comparisons not supported (round 1 +0.14 below the 0.15 minimum effect; rounds 2–3 not
  significant); H13 (less false blame at published changes) and H14 supported.
