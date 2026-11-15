#!/bin/bash
# Host preflight after the watcher pause and lease release (hand-off §5.6). Fail-closed, no clobber.
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
OUT=/home/dowling/exam-x/work/b2_host_preflight_8709_20261115_a
CACHE=/home/dowling/r1_b1_engineering/b2_final_gate_pycache_8709_20261115_b
stop() { echo "STOP: $*" >&2; exit 2; }
[ "$HOME" = /home/dowling ] || stop "HOME mismatch"
[ -d "$CAP" ] && [ ! -L "$CAP" ] || stop "gate capture dir missing"
for p in "$OUT" "$CACHE"; do [ ! -L "$p" ] && [ ! -e "$p" ] || stop "path exists or is a symlink: $p"; done
[ -d "$PAPER" ] && [ ! -L "$PAPER" ] || stop "paper checkout missing/symlink"
[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ] || stop "harness missing/symlink"
[ -x "$PY" ] || stop "python unavailable"
[ -s "$RUN_DIR/prechecks/prechecks.ok" ] || stop "prechecks not passed"
[ -s "$RUN_DIR/postwatch/postwatch.ok" ] || stop "postwatch not passed"
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker absent"
[ -s "$CAP/gate.exit" ] && [ "$(cat "$CAP/gate.exit")" = 0 ] || stop "gate exit not 0"
grep -Fq "GATE_PASS $HEAD $RULE_SHA" "$CAP/gate.log" || stop "exact GATE_PASS line missing"
[ "$(git -C "$HARNESS" rev-parse HEAD)" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 ] || stop "harness pin mismatch"
[ -z "$(git -C "$HARNESS" status --porcelain --untracked-files=no)" ] || stop "harness dirty"
"$PY" - "$RUN_DIR" <<'PYCHK' || stop "venv pins mismatch"
import importlib.metadata as md, sys
run_dir = sys.argv[1]
pins = {}
for line in open(run_dir + '/venv_pins.txt'):
    line = line.strip()
    if not line or line.startswith('#'): continue
    k, v = line.split('=', 1); pins[k] = v
import platform
assert platform.python_version() == pins['python'], 'python version'
assert sys.prefix == pins['prefix'], 'prefix'
for k in ('openai','langchain_openai','langchain_core','langgraph','pydantic','pydantic_core','httpx','pytest','numpy','scikit-learn'):
    got = md.version(k)
    assert got == pins[k], f'{k} {got} != {pins[k]}'
print('VENV_PINS_OK')
PYCHK
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader | grep -q . && stop "GPU compute app present before preflight"
flock -n /home/dowling/r1_locks/gpu0.lock true || stop "gpu0.lock busy before preflight"
export AR_HARNESS_ROOT="$HARNESS" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$CACHE" GIT_OPTIONAL_LOCKS=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=/home/dowling/exam-x/work/venv/bin:/usr/local/bin:/usr/bin:/bin
cd "$PAPER" || stop "cannot enter checkout"
set -C
: > "$CAP/preflight.log" || stop "cannot create preflight.log exclusively"
: > "$CAP/preflight.exit" || { echo "cannot create preflight.exit" >&2; exit 1; }
if "$PY" -B -m r1.scripts.b1_host_preflight --head "$HEAD" --out "$OUT" > "$CAP/preflight.log" 2>&1; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" > "$CAP/preflight.exit"
grep -Fq "PREFLIGHT_PASS" "$CAP/preflight.log" || stop "PREFLIGHT_PASS line missing"
[ "$rc" -eq 0 ] || { echo "STOP: preflight rc=$rc" >&2; exit "$rc"; }
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader | grep -q . && stop "GPU compute app present after preflight"
flock -n /home/dowling/r1_locks/gpu0.lock true || stop "gpu0.lock busy after preflight"
[ ! -e "$RUN_DIR/preflight.ok" ] || stop "preflight.ok exists"
set -C; : > "$RUN_DIR/preflight.ok" || stop "cannot write preflight.ok exclusively"
echo "PREFLIGHT_OK rc=0"; tail -5 "$CAP/preflight.log"
exit 0
