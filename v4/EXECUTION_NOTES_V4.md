# Round 4: execution notes (written during the run; not part of the frozen protocol)

The protocol and code were frozen at 2026-10-07T23:50:58Z (`runs/freeze_v4.json`, digest 9543f4c5…). Nothing
under `v4/code/`, `v4/analysis/` or `v4/PROTOCOL_V4.md` changed afterwards. What changed was how the frozen code was
executed:

1. **Worker count and threads.** The chicago run started with 8 worker processes. Its throughput fell to about
   0.15 cases per minute (each case 25-40 minutes, against 2-4 minutes when run alone in the smoke test), which
   points to contention between workers (memory and the multithreaded gradient-boosting library). To change the
   worker count of a running job, its inputs were withdrawn twice (the chicago bronze files and cache folders were
   renamed; `jobs/STOP` paused the runner), so that the remaining cases failed at once. Every record written after
   the inputs were withdrawn was discarded (first stop: records 70-218 of the file kept only up to 69; second stop:
   records 88-95 discarded, 87 kept); the discarded files are kept in `_to_delete/chicago_outage/`. The cache was
   checked for error entries written during the outages: none in the restored cache; two entries in folders
   created during the outage were moved to `_to_delete/chicago_outage/cache_new/`.
   The remaining cases ran with `v4/launch_single_thread.py` (one OpenMP/BLAS thread per process), 3 workers and
   40 cases per job (`--limit`), which restarts the worker processes between jobs. Throughput rose to about
   1.2 cases per minute.
2. **One transient I/O error.** In `chicago-2018-2022-defect-7bdf5562`, DoD-2 failed with `OSError: [Errno 22]`
   while reading a cached parquet file (a run in progress during the first outage may have been writing it). The
   record was removed and the case was run again (`089d_v4main_chicago_rerun1`, one worker).
3. **Storm: subsample (a deviation from the protocol).** Storm cases are about five times as expensive as Chicago
   cases (a 12-component, three-table pipeline whose history tests re-run up to 30 years of data). With one, two,
   three or four workers and one to eight threads per worker, throughput stayed between 0.1 and 0.4 cases per
   minute: about 40 hours for the 640 cases, before the storm LLM baselines and the development runs. After 52
   storm cases had been run in the protocol's order, the remaining storm cases were restricted to a fixed 1-in-3
   subsample, defined by a hash of the case id before any further result was seen:
   keep iff int(sha256("v4-storm-subsample:" + case_id), 16) % 3 == 0 (`v4/run_cases_subsample.py`, which filters
   the case list and runs the frozen `v4/code/run_cases.py` unchanged). The subsample has 219 of the 640 storm
   cases. All storm analyses use exactly these 219 cases; the storm cases run before the switch that are not in
   the subsample are kept in `runs/v4main_extra/storm.jsonl` and are not analysed. Chicago is complete (231 cases).
   Storm runs were stopped three times with the same input-withdrawal procedure (counts in
   `_to_delete/storm_stop*/count.txt`); no record was written while inputs were withdrawn, and no error entry was
   left in the cache. Ten queued jobs were interrupted at 2026-10-08T18:08Z by a console Ctrl+C on the laptop
   (exit code 0xC000013A) before doing any work.
4. **Reference models** were built once, before the first stop, and reused (`data/models/v3/chicago/`).

Results are computed by deterministic code from the same inputs; worker count, thread count and job boundaries do
not enter any computation except the floating-point order inside the gradient-boosting library, which is the same
for every method in a case.
