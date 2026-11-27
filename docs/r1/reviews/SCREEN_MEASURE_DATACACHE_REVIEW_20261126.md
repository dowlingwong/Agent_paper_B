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

## Addendum 2: re-check of the deadline withdrawal (611b34c0)

- **Range:** `git diff 2907b684 611b34c0`. The first commit id given for this re-check, 50cd7ae7, does not exist in the repository; the corrected id 611b34c0 was used.
- **Ancestry:** 8821b70c, then 2907b684 (review record only), then 611b34c0.
- **Worktree:** a fresh detached worktree, removed afterwards and clean when removed. No file was modified.
- **Reviewer:** the same independent tier-E reviewer (AI-assisted, Claude subagent, 27 Nov 2026).

### What changed, checked

- **Authority:** PLAN row `R1-NO-TIMEOUT` is on published `origin/main`. Part (1) names "the deadline option of the screening measurement" as withdrawn. Part (2) keeps the T0 per-run budget of 600 s.
- **Code (`r1/noise/screen_measure.py`):**
  - Removed: `DEFAULT_DEADLINE`, the `--deadline` option, its finiteness check, and the manifest's `deadline_seconds`.
  - `main` passes `None` to `execute`.
  - `execute` takes `deadline: float | None`. Both deadline checks, in-process and in the pool, are guarded by `deadline is not None`, so with `None` neither can fire; the existing deadline tests pass a number.
  - The per-run budget `LocalWorker(timeout_seconds=600)` is unchanged in `run_one_lineage` and `build_data_cache`, as R1-NO-TIMEOUT (2) requires.
  - Nothing else reads `args.deadline`. `math` is still used elsewhere in the file.
- **Evidence binding:**
  - `expected_note` no longer contains `deadline_seconds`, and neither does the authorization draft's key block (still a template, `approved: false`). The preflight compares only `expected_note`'s keys, so draft and code agree.
  - The launch line has no `--deadline`. The STOP list reads "no deadline: R1-NO-TIMEOUT (1)".
- **Pre-declaration:**
  - §8.1 says there is no deadline, a run without progress is ended by the operator as an infrastructure failure, and the 600 s budget stays.
  - §9 item 7 is marked withdrawn, which keeps item 8's number.
- **Pins:**
  - `screen_measure.py` `9907689f…751edf`, the same in both drafts.
  - `test_screen_measure.py` `67d7a05e…f850e7`.
  - The other five pinned files are unchanged.
- **Run table and analysis:** unaffected. `ROW_KEYS` is unchanged, and `screen_analysis` never read the deadline.
- **Tests:** `PreflightTest` drops `deadline` from its args and from its mismatched fields. The new `NoDeadlineTest` checks three things: the constant is gone, argparse rejects `--deadline`, and `expected_note` has no `deadline_seconds`.

### Nits (non-blocking)

- `r1/noise/screen_power.py:22, 258-259` still computes and prints an informational `deadline_seconds`. That file is pinned and unchanged, and nothing reads the value. A later change could drop it or relabel it as a projection.
- Pre-declaration line 664 (the historical M7 row) lists "deadline" among the tested STOP paths. That is accurate as history, since the test remains for `execute` with a numeric deadline.

### What the reviewer ran

`python -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py` gave 78 passed.

### What runs next

The steps of addendum 1, except that the smoke takes no `--deadline`. argparse now rejects the option, so the 26 Nov command line must not be reused:

`python -B -m r1.noise.screen_measure run --engineering-smoke --out <new dir> --workers 16 --tmp /tmp/r1_smeas_ENG_<stamp> --data-cache <dir>`

The smoke follows the one-off `data-cache` build.

Verdict: ACCEPTED

## Addendum 3: re-check of ARFF identification by content (e5227c0c; local/20261127-05)

- **Range:** `git diff 5c901d19 e5227c0c`. The screening files at the base are byte-identical to `611b34c0`, the tip accepted in addendum 2.
- **Worktree:** a fresh detached worktree, removed afterwards.
- **Reviewer:** the same independent tier-E reviewer (AI-assisted, Claude subagent, 27 Nov 2026).

### Correction to round 1

In round 1 the reviewer said `check_pilot`'s name test would work under scikit-learn 1.8. It did not. Compute's STOP report (`reports/20261127-06-screening-smoke-stop.md`) shows that the 1.8.0 build stored breast-w as `…/data/v1/download/52350.gz`. The likely reason is that OpenML's current description `url` carries no file name, whereas the 9 October pilot's did. If so, the description JSON in the new cache also differs from the pilot's. That is acceptable: the pilot cross-check covers the ARFF only, and the tree sha256 binds every file. The STOP failed closed, as intended.

### Checks

- **`is_arff`:**
  - It reads the first 64 KiB of the decompressed content, skips blank lines and `%` lines, and accepts the file only if the next line starts with `@relation` (in any case).
  - The JSON files start with `{`, so they never count.
  - A real ARFF with leading `%` comments is recognised, including CRLF line endings and leading spaces.
  - A BOM, a comment block over 64 KiB, or a header cut at 64 KiB gives "0 ARFF files", a STOP. All three cases fail closed.
- **`cache_tree`:**
  - It records `{"sha256", "content_sha256", "arff"}` for each file.
  - The same function builds the manifest, verifies it, and checks each run's cache, so the format is the same at all three points.
  - No manifest in the old format exists: compute's build STOPped before writing one.
- **`check_pilot`:** counts the files with `arff` True in the recomputed tree, requires exactly one, and still applies the pilot pin. Per compute's report, `52350.gz` matches the breast-w pin.
- **Tests:** the earlier fixtures now carry ARFF headers. The new `ArffByContentTest` covers the 1.8 `<id>.gz` layout with the JSON files: one ARFF counted, the pin applied (both mismatch and match), 0 and 2 ARFF files refused, and `read_data_cache` accepting the layout.
- **Pins:**
  - `screen_measure.py`: `5c04aeee…75bd38`, in both drafts.
  - `test_screen_measure.py`: `7f359ace…eb7be3`.
  - The other five pins are unchanged.
  - §8.4's wording matches the code.
- **Scope:** nothing affects the run table, the analysis, the evidence binding, or any signed file.

### Nits

- `@relationship…` would also count, because the test is a prefix match. This cannot arise in practice.
- One docstring line is longer than the file's usual line width.

### What the reviewer ran

`python -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py`: 82 passed.

Verdict: ACCEPTED
