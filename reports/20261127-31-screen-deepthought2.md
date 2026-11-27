# local/20261127-31 — deepthought2 screening re-issue

for: coordinator

- Published base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`. Delivery branch
  `mac-screen-deepthought2-20261127` @ `123d8bbeb1e8a57a906e59be4d82e98fda73300e`.
  Reviewed launch code `a7c2f8fb7b90b3237e61672c6b48112365dcdb24` and tested candidate
  `3f373665a2f593024f2e615155b96cc483fa28b5`.
- Independent tier-E re-check **ACCEPTED**. Review
  `docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md`, SHA-256
  `dc7b0d63bdda07377f2bf41fdc15b1f88cfe3b8d3aa5d19739a037722f1eaadb`.
  The final note restored author disposition for each STOP, including deepthought2 co-tenancy.
- Draft `docs/r1/authorizations/screen_measure_20261127_reissue_3.md` @ `93892f19`,
  SHA-256 `84381da7a74f9406b60383c4b07682a4baee6c549cd1551ca8090a0bdc8cebc0`.
  Runner SHA-256 `ae2d1688824ddbeb2b2c5a2e346822000aa3245730b531b0372d6c288ccabf11`.
  Shared audit environment helper SHA-256 `31feb07a8fdc737ddf1bda354647744450c5c6844594749f510352fca9ee73ac`.
- The new note uses 64 affinity-bound logical CPUs on deepthought2 under
  R1-SCREEN-DEEPTHOUGHT2. The runner verifies placement, online capacity, 10-core admission
  headroom and the in-run 60-second guard. The harness, numerical runtime, design, seeds
  3301–3420, analysis and original reference files retain their bindings.
- Key inputs are companion SHA-256 `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`,
  cache tree `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07`,
  design `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8` and harness
  `6adf3859de66c4814fcf376eed59880fbd8eeaf7`.

## Verification

- 115 focused screening and audit-guard tests passed. `bash -n` and `git diff --check` passed.
  The private Git fixture refused unpublished and unsigned authorization. Its simulated
  publication passed strict preflight using real Git, PLAN, code pins, design, companion and seed
  checks with simulated host resources, runtime and harness equivalence. Compute verifies the
  real host, its scheduler entitlement, replay environment and cache before launch.
- Serial full suite with Python 3.12.8, pytest 9.2.0, torch 2.15.0, harness
  `9bb416805175149eb87b71f28d77530572aa4bce`, no LightGBM and fresh `TMPDIR` for each run.
  Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
  Base `15fe05b0` had **5,055 passes**. Candidate `3f373665` had **5,059 passes**.
  Both had 120 failures, 3 errors, 163 skips and 71 passing subtests. Zero new failures or errors.
  The exact [123 nonpass IDs](20261127-27-28-fullsuite-failure-ids.txt) match,
  SHA-256 `bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`.

## Compute handoff after publication

The coordinator publishes the reviewed branch and approved note under R1-SCREEN-DEEPTHOUGHT2,
then dispatches the new run. Compute first checks `compute/20261127-38`, the active jobs and the
attempt ledger. The last recorded deepthought stamp `SMEAS_EVIDENCE_20261127T2125Z` stopped at
444 of 10,164 with zero failed rows. Use a fresh stamp after the prior retries end, and capture
the three thread-limit settings and actual CPU entitlement.

```bash
(
  set -eu
  test "$(hostname -s)" = deepthought2
  CODE=a7c2f8fb7b90b3237e61672c6b48112365dcdb24
  DEPLOY=/work/dwong/screen_measure_20261127/paper_c12136d6
  CACHE=/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z
  BATCH=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw
  STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  CHECKOUT="/work/dwong/screen_measure_20261127/paper_dt2_$STAMP"
  OUT="results/r1/screen_measure/SMEAS_EVIDENCE_$STAMP"
  SCRATCH="/tmp/r1_smeas_EVIDENCE_$STAMP"
  test ! -e "$CHECKOUT"
  test ! -e "$SCRATCH"
  test -f "$CACHE/MANIFEST.json"
  git -C "$DEPLOY" fetch origin refs/heads/main:refs/remotes/origin/main
  git -C "$DEPLOY" merge-base --is-ancestor "$CODE" origin/main
  git -C "$DEPLOY" worktree add --detach "$CHECKOUT" "$CODE"
  cd "$CHECKOUT"
  test ! -e "$OUT"
  STATUS=$(git status --porcelain)
  test -z "$STATUS"
  export AR_HARNESS_ROOT="$BATCH/autoresearch_harness"
  export PATH="$AR_HARNESS_ROOT/.venv/bin:$PATH"
  export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
  export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
  unset PYTHONPATH
  test "$(command -v python3)" = "$AR_HARNESS_ROOT/.venv/bin/python3"
  CPUSET=$(python3 -B -c 'import os; print(",".join(map(str, sorted(os.sched_getaffinity(0))[:64])))')
  taskset --cpu-list "$CPUSET" python3 -B -m r1.noise.screen_measure run --evidence \
    --out "$OUT" --workers 64 --tmp "$SCRATCH" --paper-root "$CHECKOUT" \
    --note docs/r1/authorizations/screen_measure_20261127_reissue_3.md \
    --code-commit "$CODE" --code-review docs/r1/reviews/SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md \
    --data-cache "$CACHE"
)
```

The full command is the reviewed draft's launch block. Compute runs analysis only after a complete
run without STOP and reports the manifest, runs and analysis hashes. D.3 step (8) stays behind
the screening result and any required SHARED disposition.

Decided alone to use the signed 64-CPU ceiling, bind the process tree with `taskset`, reuse the
shared batch/cache paths and reserve the 10-core headroom at admission. Live path visibility and
hardware scheduling are still operator checks. Used nested worktrees with writable Git metadata
because the assigned linked checkout's Git metadata refused writes.
