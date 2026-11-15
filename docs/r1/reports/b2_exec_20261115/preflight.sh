#!/bin/bash
# Host preflight after the watcher pause and lease release (hand-off §5.6).
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
CAP=/home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_a
OUT=/home/dowling/exam-x/work/b2_host_preflight_8709_20261115_a
CACHE=/home/dowling/r1_b1_engineering/b2_final_gate_pycache_8709_20261115_a
[ "$HOME" = /home/dowling ] || exit 1
[ ! -e "$OUT" ] && [ ! -L "$OUT" ] || { echo "STOP: preflight --out exists"; exit 1; }
[ -s "$CAP/gate.log" ] && [ "$(cat "$CAP/gate.exit")" = 0 ] || { echo "STOP: gate not passed"; exit 1; }
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || { echo "STOP: marker absent"; exit 1; }
export AR_HARNESS_ROOT="$HARNESS" PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX="$CACHE" GIT_OPTIONAL_LOCKS=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
cd "$PAPER" || exit 1
if "$PY" -B -m r1.scripts.b1_host_preflight --head "$HEAD" --out "$OUT" > "$CAP/preflight.log" 2>&1; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$CAP/preflight.exit"
echo "preflight_rc=$rc"; tail -20 "$CAP/preflight.log"
