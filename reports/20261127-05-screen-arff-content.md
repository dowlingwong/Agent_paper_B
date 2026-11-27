# local/20261127-05 — Screening cache ARFF identification (DONE)

for: compute

- Base `5c901d19e682dbd50556054b2ebfb9e8f2c50ea1`. Published task branch `mac-screen-arff-content-20261127` @ `cb684870f939eec3a32b499a11a6bcce44d4dd57`, code `e5227c0c`.
- Independent tier-E re-check **ACCEPTED**, addendum 3 of `docs/r1/reviews/SCREEN_MEASURE_DATACACHE_REVIEW_20261126.md`. Focused suite 82 passed.
- Content inspection recognizes the sklearn 1.8 cache filename `52350.gz` using its decompressed ARFF header. Each node still needs exactly one ARFF, and pilot nodes still need the pinned content. Cache manifests bind the whole tree.
- Full `r1/tests`, one run per checkout with fresh short TMPDIR, `COPYFILE_DISABLE=1`, LightGBM off the path and harness `897d83c8efa364ec2fdd37288241cc42e01d7274`. Command `python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`. Base 134 failed / 4471 passed / 161 skipped / 3 errors. Tip 134 / 4475 / 161 / 3. **Zero new failures**. The 137 failing test IDs match exactly, sorted list SHA-256 `563e4c8cbf4c6b593724da80494269ef98d3d8bac89210d074c725da384b5419`.
- Draft pins: `screen_measure.py` `5c04aeeef13afebc6dd2839737691b16b76e4485f546e9789380d6d4a575bd38`; `test_screen_measure.py` `7f359aceb3c759d159d33067c412909a6ee8597389d85d8d04facc4bf8eb7be3`. The decompressed breast-w ARFF matches `cb44e7f62f4a962881147264e5f985eacc13256712e7a4b9d1731ced05f3ee9b` in the prior STOP report.

## Compute handoff

After the coordinator merges the task, repeat `compute/20261127-07` on deepthought. Check the existing smoke run and host commitments first. Use the pinned Python 3.13.15 / sklearn 1.8.0 environment and clean `AR_HARNESS_ROOT` at `6adf3859`. Run in the Paper B checkout.

```bash
set -e
git fetch origin
git switch --detach origin/main
git merge-base --is-ancestor cb684870f939eec3a32b499a11a6bcce44d4dd57 HEAD
test -z "$(git status --porcelain)"
python -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
CACHE=/work/dwong/screen_prep_20261126/data_cache_ENG_$STAMP
SMOKE=/work/dwong/screen_prep_20261126/smoke_ENG_$STAMP
python -B -m r1.noise.screen_measure data-cache --out "$CACHE" --tmp "/tmp/r1_smeas_cache_$STAMP"
sha256sum "$CACHE/MANIFEST.json"
python -B -m r1.noise.screen_measure run --engineering-smoke --out "$SMOKE" --workers 16 --tmp "/tmp/r1_smeas_ENG_$STAMP" --data-cache "$CACHE"
```

Report the cache tree and manifest hashes, 168/168 planned/written runs, identity flags, the `failed_runs.jsonl` status and any STOP. Preserve the old STOP directory and this attempt separately. The evidence run awaits the signed screening note.

Decided alone: resume the independently accepted task tip and validate the exact published branch against its actual parent checkout. The assigned checkout stays clean.
