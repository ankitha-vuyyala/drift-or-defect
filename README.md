# Drift or Defect

**Is It Model Drift or a Broken Pipeline? What Re-Execution Can and Cannot Identify in Production ML**

Ankitha Vuyyala · Independent Researcher · [ORCID 0009-0004-1916-8070](https://orcid.org/0009-0004-1916-8070)

When a production model's accuracy drops, the usual response is to retrain it. But the model sees the output of a
data pipeline, and that pipeline changes too: code is updated, libraries are upgraded, and data providers change
their published files. This repository contains the code, benchmark and raw results for a study of when a
pipeline defect can be told apart from a genuine change of the prediction problem.

- **Theory.** Defects whose corrupted features stay inside the image of the correct pipeline are invisible to any
  monitoring of model inputs and labels. Re-executing a changed component at its known-good version (a rollback
  test followed by a propagation test) decides exactly whether it is an effective defect when the data source did
  not force the change. When the source did force it, no re-execution can certify the rewritten component. From
  this follows a three-verdict rule — fix what is verified, clear what is healthy, list the rest for review — that
  is sound and complete under an accurate record of the source's changes.
- **Method.** DoD-4 (*Drift or Defect*, version 4) implements that rule. Three earlier versions (DoD, DoD-2,
  DoD-3) decide every case using side information and serve as comparisons.
- **Benchmark.** Eleven executable pipelines over public data (census, taxi, news, bike share ×2, mortgages,
  airlines, fatal crashes, house sales, storm events, Chicago traffic crashes) with real, dated changes of the
  published files, real library-upgrade behaviours and replays of public incidents; 2,961 evaluated cases with
  ground truth obtained by executing every action.
- **Evaluation.** Four pre-registered rounds. Each round's protocol, code and SHA-256 digest were frozen before
  any test case was run.

The paper is in [`paper/drift_or_defect.pdf`](paper/drift_or_defect.pdf) (also `.docx`).

## Key results

| | Result |
|---|---|
| Round 4 (two three-table pipelines, 450 cases) | DoD-4: false-blame rate 0.000, silent-miss rate 0.000 (256 consequential cases), correct on all 51 cases it decided; it decided 11% of the cases and listed 5.3 components per case for review |
| Cases without a published source change (all rounds) | Interventional diagnosis correct on 267 of 267 consequential cases |
| Silent defects (rounds 1–3) | Retrain-on-alarm and validation-first diagnosed none of 200 |
| Rounds 1–3 | The three deciding versions did not beat the best baseline; their failures were all source-forced changes, as the theory predicts |

Every number in the paper is listed with the file it was computed from in
[`paper/evidence_index.md`](paper/evidence_index.md).

## Repository layout

| Path | Contents |
|---|---|
| `PROTOCOL.md`, `v2/PROTOCOL_V2.md`, `v3/PROTOCOL_V3.md`, `v4/PROTOCOL_V4.md` | Frozen protocols of rounds 1–4 (hypotheses, endpoints, thresholds) |
| `code/` | Round-1 code: pipelines, executor, case generator, ground truth, methods, LLM baseline, data download (`code/data/`), pandas environments (`code/t2/`) |
| `v2/`, `v3/`, `v4/` | Code, data scripts and analysis of rounds 2–4; `v4/code/` contains all eleven domains and DoD-4 (`v4/code/dod/methods_v4.py`) |
| `analysis/`, `v*/analysis/` | Summaries and hypothesis tests, frozen with each round |
| `posthoc/` | Analyses that were not pre-registered (split by published changes, local vs end-to-end effectiveness, leave-one-out sensitivity) |
| `runs/` | Raw case records (`*.jsonl`, one case per line), summaries, freeze digests (`freeze*.json`), LLM response cache (`llm_cache/`), API cost ledger |
| `paper/` | Scripted paper build (`build_paper_v4.py`, `paper_text_v4.py`, `figs*.py`), figures, references, evidence index |
| `docs/` | Design notes, theory notes per round, development log, progress |
| `runner/` | The job runner used to execute everything on one machine (cost cap enforced in code) |

Raw records by round: `runs/final` (round 1; use the `test` split), `runs/v2main`, `runs/v3main`, `runs/v4main`;
development runs: `runs/v3dev`, `runs/v4dev`.

## Quick start: recompute the results from the saved records

No data download and no API keys are needed for this.

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python v4/analysis/summarize_v4.py runs/v4main          # round 4 -> runs/v4main/summary_v4.md
python posthoc/by_change.py                             # split by published changes
python posthoc/sensitivity.py                           # leave-one-domain/-change-out
python paper/figs_v4.py runs/v4main runs/posthoc_by_change.json
python paper/build_paper_v4.py                          # rebuilds paper/drift_or_defect.docx
```

Rounds 1–3: `python analysis/summarize.py runs/final`, `python v2/analysis/summarize_v2.py runs/v2main`,
`python v3/analysis/summarize_v3.py runs/v3main`.

## Full reproduction

Full reproduction re-executes every pipeline and takes several days on a laptop (over 20 GB of raw downloads).

1. **Data.** Download the public raw files and build the sampled "bronze" layer: `code/data/download.py` and
   `code/data/build_bronze.py` (round 1); `v2/data/download_v2.py`, `v2/data/build_bronze_v2.py`;
   `v3/data/download_v3.py`, `v3/data/build_bronze_v3.py <domain>`; `v4/data/download_v4.py [storm|chicago]`,
   `v4/data/build_bronze_v4.py <storm|chicago>`. Downloads are checked against SHA-256 manifests.
2. **Environments and artifacts.** `python code/t2/setup_envs.py` (pandas 1.5 / 3.0 environments used to replay
   library upgrades) and `python code/build_artifacts.py`.
3. **Cases.** For example `python v4/code/run_cases.py --domain chicago --split all --out v4main --methods <list
   in v4/PROTOCOL_V4.md>`. The storm domain used the fixed 1-in-3 subsample in `v4/run_cases_subsample.py`
   (see `v4/EXECUTION_NOTES_V4.md`). The runners refuse to process test cases if the frozen digest does not match.
4. **LLM baselines (optional).** Copy `.env.example` to `.env` and add an API key, or replay the cached responses
   without any key: `DOD_REPLAY_ONLY=1 python v4/code/run_llm.py --run v4main --domain chicago --modes
   report,tools --provider openai --model gpt-5.6-luna --tag luna`.

Python 3.11; package versions in `requirements.txt`.

## Data sources and licences

The raw data are not redistributed here; the download scripts fetch them from their providers:
U.S. Census Bureau (ACS PUMS), NYC Taxi & Limousine Commission trip records, HuffPost News Category dataset,
Divvy and Capital Bikeshare trip data, CFPB/FFIEC HMDA records, BTS on-time performance, NHTSA FARS,
NOAA NCEI Storm Events Database, City of Chicago Traffic Crashes (Chicago Data Portal), and HM Land Registry
Price Paid Data (contains HM Land Registry data © Crown copyright and database right, Open Government Licence
v3.0). Each dataset remains under its provider's terms.

## Citation

If you use the code, benchmark or records, please cite the paper (GitHub's "Cite this repository" button uses
[`CITATION.cff`](CITATION.cff)):

```bibtex
@misc{vuyyala2026drift,
  author       = {Vuyyala, Ankitha},
  title        = {Is It Model Drift or a Broken Pipeline? What Re-Execution Can and Cannot Identify in Production ML},
  year         = {2026},
  howpublished = {\url{https://github.com/ankitha-vuyyala/drift-or-defect}},
  note         = {Preprint}
}
```

## License

Code: [MIT](LICENSE) © 2026 Ankitha Vuyyala. The source data are not part of this repository and remain under
their providers' terms (see above).
