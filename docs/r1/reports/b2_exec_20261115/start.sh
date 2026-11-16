#!/bin/bash
# B2 runner launch (B1 _d pattern). Only after every launch condition holds.
set -u
set -o pipefail
umask 077
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONNOUSERSITE=1
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RULE_SHA=53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad
RUN_ID=8709_20261115_b2
PAPER="/home/dowling/r1_b1_engineering/b2_paper_final_${HEAD}/paper"
HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
PY=/home/dowling/exam-x/work/venv/bin/python
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
CAP=/home/dowling/r1_b1_engineering/b2_final_gate_preflight_8709_20261115_b
BATCH="/home/dowling/exam-x/work/b2_${RUN_ID}"
die() { printf 'STOP: %s\n' "$*" >&2; exit 1; }
[ "$HOME" = /home/dowling ] || die 'HOME mismatch'
[ ! -L "$BATCH" ] && [ ! -e "$BATCH" ] || die 'batch path exists'
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || die 'paper checkout missing or symlink'
[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ] || die 'harness missing or symlink'
[ -d "$RUN_DIR" ] && [ ! -L "$RUN_DIR" ] || die 'run directory missing or symlink'
[ -x "$PY" ] || die 'Python unavailable'
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || die 'marker absent'
[ -s "$RUN_DIR/prechecks/prechecks.ok" ] || die 'prechecks not passed'
[ -s "$RUN_DIR/postmarker/manifest_inventory_after.txt" ] || die 'post-marker inventory missing'
[ -s "$RUN_DIR/postwatch/postwatch.ok" ] || die 'postwatch not passed'
[ -s "$RUN_DIR/preflight.ok" ] || die 'preflight.ok missing'
[ "$(cat "$CAP/preflight.exit" 2>/dev/null)" = 0 ] || die 'preflight exit not 0'
grep -Fq "PREFLIGHT_PASS" "$CAP/preflight.log" || die 'PREFLIGHT_PASS missing'
grep -Fq "GATE_PASS $HEAD $RULE_SHA" "$CAP/gate.log" || die 'GATE_PASS line missing'
python3 - "$RUN_DIR/marker-receipt.json" "$RUN_ID" "$HEAD" <<'PY' || die 'marker receipt mismatch'
import json, sys
r = json.load(open(sys.argv[1])); assert r['run_id'] == sys.argv[2] and r['head'] == sys.argv[3]
print('MARKER_RECEIPT_OK')
PY
pgrep -a -f "P\.3a|p3a" >/dev/null 2>&1 && die 'P.3a running'
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader | grep -q . && die 'GPU compute app present'
cd "$PAPER" || die 'cannot enter checkout'
export AR_HARNESS_ROOT="$HARNESS" PYTHONDONTWRITEBYTECODE=1
unset LLAMACPP_CACHE_PROMPT
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
[ "$(git --no-optional-locks rev-parse HEAD)" = "$HEAD" ] || die 'HEAD mismatch'
[ -z "$(git --no-optional-locks status --porcelain --untracked-files=all)" ] || die 'checkout is dirty'
[ "$(git -C "$HARNESS" rev-parse HEAD)" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 ] || die 'harness pin mismatch'
exec "$PY" -B -m r1.scripts.exam_runner b2 --config "$PAPER/r1/scripts/configs/exam_b2_v2.json" --out "$BATCH"
