# local/20261126-02 — screening smoke STOP: cause found, fix reviewed (DONE)

for: compute (the repeat of the engineering smoke, below)

- **Task:** `local/20261126-02`
- **Branch:** `mac-screen-measure-fix-20261126` @ **`611b34c0`**
  - The branch is `mac-screen-measure-20261123` with `main` `166db0eb` merged (`35217050`).
  - On top: the fix `d854e7ac`, the review minors `8821b70c`, the review record `2907b684`, and the deadline withdrawal `611b34c0`.
  - It supersedes `mac-screen-measure-20261123` as the unit's branch; that branch stays as it is.
- **Review:** `docs/r1/reviews/SCREEN_MEASURE_DATACACHE_REVIEW_20261126.md`. Round 1 accepted with minors; re-check of `8821b70c` ACCEPTED.
  - A second re-check of `611b34c0` (deadline withdrawal) was also ACCEPTED. Its addendum is not yet appended to the file; the coordinator can take it from this report.

## Result in five lines

1. **Cause.**
   - The six OpenML nodes read their data with `fetch_openml(data_home=<node>/data_cache)`.
   - The harness commits no cache, and `_prepare_node`'s pilot fallback lies under the harness's ignored `experiments/`, which a fresh worktree lacks.
   - So on 26 Nov every smoke run downloaded its dataset from openml.org, 16 at a time, and the data were pinned by nothing.
   - The failed run's log was deleted with its scratch copy. Its `class_weight: balanced` is the harness restoring the file after a failed run.
   - Most likely a transient download failure; this is unprovable from the record. Confirmed independently by the reviewer.
2. **Fix.**
   - `screen_measure data-cache` builds the caches once, one node at a time, through the harness worker. The four pilot nodes' ARFF data must equal the E1 pilot's. A manifest records the tree sha256 at file, node and total level.
   - Harness runs require `--data-cache`. Each run copies its node's cache, checked against the tree verified at launch, and must leave it unchanged (STOP `data_cache`).
   - The evidence note binds `data_cache_sha256`.
   - A failed run's log tail goes to `failed_runs.jsonl`.
3. **Deadline withdrawn** under R1-NO-TIMEOUT (1), as card `local/20261126-07` item 3 asks. The worker's 600 s per-run budget stays (R1-NO-TIMEOUT (2)).
4. **Docs.** The pre-declaration (§8.1, §8.3, §8.4, §9, pins) and the authorization draft (key block, P4, launch) are updated. Both remain unsigned drafts.
5. **Tests and suite.**
   - `r1/tests/test_screen_measure.py`: 78 passed (63 before this unit).
   - Full suite, same run settings as before (`AR_HARNESS_ROOT` set, `--continue-on-collection-errors`, anaconda python without torch):
     - base `166db0eb`: 178 failed / 26 errors / 3923 passed;
     - tip `d854e7ac`: 178 / 26 / 3996;
     - final tip `611b34c0`: 178 / 26 / 4001.
   - **Zero new failures.** The failing-id lists are identical (sha256 of the list `52906560…`).

## Hashes (pins in both drafts)

- `screen_measure.py`: `9907689f…751edf`
- `test_screen_measure.py`: `67d7a05e…f850e7`
- The other five code pins are unchanged.

## What compute runs next (deepthought, after the coordinator merges or from the branch)

The scene of 26 Nov stays kept. Do not reuse the 26 Nov command line: it passes `--deadline`, which argparse now rejects.

```
# evidence environment: Python 3.13.15, scikit-learn 1.8.0; AR_HARNESS_ROOT = a clean worktree at harness 6adf3859
cd <paper checkout containing 611b34c0 (or its merge)>; git status --porcelain   # must print nothing
python -m pytest -q r1/tests/test_screen_measure.py                                # 78 passed
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
python -B -m r1.noise.screen_measure data-cache --out /work/dwong/screen_prep_20261126/data_cache_ENG_$STAMP --tmp /tmp/r1_smeas_cache_$STAMP
#   record the printed tree_sha256 and sha256sum of <dir>/MANIFEST.json; the directory must stay (durable, outside both checkouts)
python -B -m r1.noise.screen_measure run --engineering-smoke --out /work/dwong/screen_prep_20261126/smoke_ENG_$STAMP --workers 16 --tmp /tmp/r1_smeas_ENG_$STAMP --data-cache /work/dwong/screen_prep_20261126/data_cache_ENG_$STAMP
```

**P4 needs:**
- 168/168 written runs and no STOP;
- `failed_runs.jsonl` absent or empty;
- the identity flags read by the reviewer;
- the cache directory's `tree_sha256` in the note's `data_cache_sha256`;
- the same directory kept for the evidence run.

A cache build that STOPs (download or pilot mismatch) leaves a partial directory without a manifest. Move it aside, report it, and do not edit it.

## Decided alone

- Hashed caches built once, rather than a network-off switch.
- The deadline withdrawal folded into this revision (R1-NO-TIMEOUT (1) names it).

## Needs from the author

Nothing new. The evidence run still waits for the signed note.
