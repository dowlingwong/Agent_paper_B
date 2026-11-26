# Review: screening measurement data caches and failed-run logs (local/20261126-02)

- **Unit:** card local/20261126-02, the fix after the 26 Nov engineering-smoke STOP `determinism_unverifiable openml_breast_w c5 seed 999`.
- **Tips:** reviewed `d854e7ac`; re-checked `8821b70c`.
- **Base:** `35217050` (`origin/mac-screen-measure-20261123` with `origin/main` `166db0eb` merged in; the merge itself was not under review).
- **Files:** `r1/noise/screen_measure.py`, `r1/tests/test_screen_measure.py`, `docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md`, `docs/r1/authorizations/SCREEN_MEASURE_AUTHORIZATION_DRAFT_20261123.md`.
- **Reviewer:** an independent tier-E reviewer (AI-assisted, Claude subagent, 26–27 Nov 2026) who did not write the unit. It modified no files, read no credential, label, test-partition or evaluation file, decompressed no dataset file, and made no network access. The author of the unit transcribed this record from the reviewer's two hand-backs.

## The diagnosis, verified independently

- **(a) Confirmed.** Harness `6adf3859`, `src/autoresearch/worker/local_worker.py:204-206`, restores the edited file after a failed run. So `values_after.class_weight = balanced` is a symptom, not an edit that failed to apply. Exit code 1 is a Python exception: not a timeout, not an OOM kill. The same configuration and seed succeeded on the repeat, so the failure was not reproducible.
- **(b) Confirmed.**
  - At `6adf3859`, `nodes/openml_{breast_w,credit_approval,ionosphere,wdbc}` have no `data_cache/`. `nodes/openml_{climate,sonar}/data_cache` hold only `.gitignore` and `.gitkeep`.
  - All six `benchmark.py` files call `fetch_openml(data_home=<node>/data_cache)`.
  - The pilot fallback of `e1_noise_floor._prepare_node` lies under `experiments/`, which the harness gitignores.
  - The smoke used a fresh harness worktree, so every OpenML run downloaded its dataset.
  - For climate and sonar, the committed `.gitkeep` means the fallback is never used even where `experiments/` exists. Those two always downloaded, in earlier harness runs too. This is outside the unit and worth recording.
- **Cause:** a transient download failure is most plausible. scikit-learn 1.8 retries 3 times and then raises; it also raises on a bad MD5. With no log, the cause is unprovable, and the author states it that way.

## Round 1 (d854e7ac): accepted with minors

**Blocking findings:** none.

### Minor findings

- **M1:** the per-run cache check was anchored to the live shared directory, not to the tree verified at launch.
- **M2:** a `data_cache` STOP lost the run's log tail.
- **M3:** the pre-declaration's §8.3 outputs and §9 STOP lists were not updated, and the `data_cache` reason was not tested through `execute`.
- **M4:** the drafts did not say where the cache must live (durable, outside both checkouts) or that it is built in the evidence environment.
- **M5:** the new tests sat after the `__main__` guard.

### Nits

- **N1:** a malformed manifest raised `AttributeError` or `TypeError` instead of a STOP.
- **N2:** a failed build leaves a partial directory. This fails closed; document it.
- **N3:** `--data-cache` was silently ignored with `--stub`.
- **N4:** a missing node cache fell through to a download.
- **N5:** the pilot pin covers only the ARFF.

### Found correct

- `cache_tree` and `read_data_cache` fail closed: symlinks, non-gzip `.gz`, schema, exact node set, stray entries, recomputed trees, one ARFF per node, the pilot pins.
- `build_data_cache`:
  - It runs one node at a time, empties the cache first, and makes one no-edit trial at seed 999.
  - Its output is limited to the path, the node list and the tree sha256; no metric is kept.
  - It is acceptable as ENGINEERING_ONLY.
  - Under scikit-learn 1.8 the layout is `…/data/v1/download/<id>/<name>.arff.gz`, matching the pilot.
- The run table is unaffected: private keys are popped before writing, and `ROW_KEYS` holds.
- Stub mode and `plan` are unchanged.
- The evidence binding (`data_cache_sha256`) is consistent with the template.
- The process pool is safe: the partial binds a module-level function and picklable keyword arguments.
- The pins matched the files.

**Verdict, round 1:** accepted with minors.

## Re-check (8821b70c): accepted

- **M1:** resolved. `data_trees` holds the launch-verified per-node tree sha256, and each run's source and post-run copy are checked against it.
- **M2:** resolved. `DataCacheStop(message, log_tail)` survives pickling, and `execute` writes the tail to `failed_runs.jsonl`.
- **M3:** resolved. §8.3 and §9 are updated, and `DataCacheStopExecuteTest` runs in-process and through the pool.
- **M4:** resolved.
- **M5:** resolved.
- **N1, N3, N4, N5:** resolved. N1 has no unit test (hand-checked).
- The pins match the files: `screen_measure.py` `fdfbbdf8…3353c5`, `test_screen_measure.py` `d3807a35…ba46a9`; the other code files are unchanged.
- The note is still a template.

**What the reviewer ran:** `python -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py` gave 73 passed at `d854e7ac` and 77 passed at `8821b70c`.

**What runs next, on deepthought:**

1. In the evidence environment, run `data-cache` once into a new durable directory outside both checkouts.
2. Run `run --engineering-smoke --data-cache <that dir>`. It needs 168/168 runs with no STOP.
3. Keep the same directory for the evidence run, with its `tree_sha256` in the note's `data_cache_sha256`.

Verdict: ACCEPTED
