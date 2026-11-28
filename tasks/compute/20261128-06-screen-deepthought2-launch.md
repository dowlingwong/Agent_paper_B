# compute/20261128-06 — screening evidence run on deepthought2 (third re-issue, R1-SCREEN-DEEPTHOUGHT2)

Published on `main` `a98d2eff`: `docs/r1/authorizations/screen_measure_20261127_reissue_3.md` (`approved: true`, sha256 `55779a6c…`), code `a7c2f8fb`, review
`SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md`. Before launch:
1. `compute/20261127-38`: confirm no deepthought attempt is still running (`ps`, the attempt ledger); the last stamp `SMEAS_EVIDENCE_20261127T2125Z`
   stopped at 444/10,164, 0 failed. Old scenes stay untouched; none of their rows enter the analysis.
2. On deepthought2: capture `nproc`, `nproc --all`, the process affinity, any cgroup / scheduler CPU limit, `uptime` (free cores ≥ 64 + 10 headroom
   needed by the guard), GPU visibility, and that `/work/dwong/...` and `/ceph/dwong/...` paths in the command exist there.
3. Launch with **exactly** the command below (fresh UTC stamp; detach it with `nohup … &` / `setsid`, write its log next to `$OUT`). The strict
   preflight in the runner must pass; if it refuses, record the exact refusal, do not work around it, and report.
Report: launch time (UTC and CET), the stamp/run directory, the preflight output, the first progress line, and the capacity captures. Then check every
round: rows done / 10,164, failures, guard status. On completion: the analysis outputs and hashes on a branch with a fresh review. A STOP (statistical or
co-tenancy) goes to the coordinator with the scene sealed; under the note each STOP's disposition is the author's. D.3 step (8) waits for the result
(R1-D3-STEP8-HOLD). Priority: first, before the TASL-7 E0 (both can run at once: deepthought2 is CPU, TASL-7 is GPU).

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
