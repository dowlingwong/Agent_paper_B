#!/bin/bash
# B2 runner launch (B1 _d pattern). Only after every launch condition holds.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
BATCH="/home/dowling/exam-x/work/b2_${RUN_ID}"
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[ ! -L "$BATCH" ] && [ ! -e "$BATCH" ] || die 'batch path exists'
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || die 'paper checkout missing or symlink'
[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ] || die 'harness missing or symlink'
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || die 'run directory missing or symlink'
[ -x "$PY" ] || die 'Python unavailable'
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || die 'marker absent'
[ "$(cat /home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_b/preflight.exit 2>/dev/null)" = 0 ] || die 'preflight not passed'
cd "$PAPER" || die 'cannot enter checkout'
export GIT_OPTIONAL_LOCKS=0 GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
export AR_HARNESS_ROOT="$HARNESS" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
unset LLAMACPP_CACHE_PROMPT
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
[ "$(git --no-optional-locks rev-parse HEAD)" = "$HEAD" ] || die 'HEAD mismatch'
[ -z "$(git --no-optional-locks status --porcelain --untracked-files=all)" ] || die 'checkout is dirty'
exec "$PY" -B -m r1.scripts.exam_runner b2 --config "$PAPER/r1/scripts/configs/exam_b2_v2.json" --out "$BATCH"
