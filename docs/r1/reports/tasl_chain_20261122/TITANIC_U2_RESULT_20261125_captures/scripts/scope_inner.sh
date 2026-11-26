#!/bin/bash
# U2 census CPU smoke — inner script, executed INSIDE the delegated systemd scope
#   systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0
# It exports the scope cgroup as AR_TEST_CGROUP_PARENT, pins the reviewed torch312 environment's
# bin first on PATH (the reviewed campaign engine starts its runs as `python3` from PATH, in
# addition to the absolute pinned interpreter used here), and runs the kit's own
# `python -m tests.trackg.port_smoke_gpu --node mlgym_titanic` ONCE at the full 150,000-step budget.
set -u
BASE=${U2_BASE:-/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125}
CPUS=${U2_CPUS:-16-31}
RAW=$BASE/raw
PY=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python
H=/home/dowling/r1_trackp/wt/titanic-20261125
LOG=$RAW/scope_inner.log
: > "$LOG"

{
  echo "scope_inner_start_utc=$(date -u +%FT%TZ)"
  echo "host=$(hostname)"
  echo "euid=$(id -u)"
  echo "pid=$$"
  echo "cgroup_proc_self=$(cat /proc/self/cgroup)"
  echo "AXIS_cpus_allowed=$(grep Cpus_allowed_list /proc/self/status)"
  echo "CPUS_arg=${U2_CPUS:-<unset>}"
} >> "$LOG"

C=$(cut -d: -f3 /proc/self/cgroup)
S=/sys/fs/cgroup$C
export AR_TEST_CGROUP_PARENT=$S
echo "SCOPE=$S" >> "$LOG"
cat "$S/memory.max" > "$RAW/scope_memory_max.txt" 2>/dev/null
cat "$S/memory.swap.max" > "$RAW/scope_memory_swap_max.txt" 2>/dev/null
cat "$S/cgroup.controllers" > "$RAW/scope_cgroup_controllers.txt" 2>/dev/null
cat "$S/cgroup.subtree_control" > "$RAW/scope_subtree_control_before.txt" 2>/dev/null

# Put the driver into a sub-cgroup so the memory controller can be enabled for the run cgroups
# (cgroup v2 forbids enabling a controller in a cgroup that has its own processes).  Best effort and
# recorded: without it the per-run cgroup peaks are absent and the scope peak is the resource number.
mkdir -p "$S/driver" 2>/dev/null
if echo "$$" > "$S/driver/cgroup.procs" 2>/dev/null; then
  echo "driver_moved_to=$S/driver" >> "$LOG"
else
  echo "driver_moved_to=FAILED" >> "$LOG"
fi
if echo "+memory" > "$S/cgroup.subtree_control" 2> "$RAW/subtree_control_memory.err"; then
  echo "subtree_memory=enabled" >> "$LOG"
else
  echo "subtree_memory=not_enabled ($(cat "$RAW/subtree_control_memory.err" 2>/dev/null))" >> "$LOG"
fi
cat "$S/cgroup.subtree_control" > "$RAW/scope_subtree_control_after.txt" 2>/dev/null

{
  echo "PATH=$PATH"
  echo "VIRTUAL_ENV=${VIRTUAL_ENV-<unset>}"
  echo "PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE-<unset>}"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-<unset>}"
  echo "AR_TRACKG_DATA_ROOT=${AR_TRACKG_DATA_ROOT-<unset>}"
  echo "AR_TEST_CGROUP_PARENT=$AR_TEST_CGROUP_PARENT"
  echo "python3=$(command -v python3)"
  echo "python=$(command -v python)"
  echo "python3_resolved=$(readlink -f "$(command -v python3)" 2>/dev/null)"
} >> "$LOG"

# Interpreter sanity BEFORE any smoke run: the PATH `python3` must be the pinned env interpreter and
# it must import torch (this is the attempt-A failure class: the campaign falls through to /usr/bin).
"$PY" - >> "$LOG" 2>&1 <<'PYEOF'
import os
import sys
import torch
import numpy
import pandas
PINNED = "/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python"
print("sanity_sys_executable", sys.executable)
print("sanity_realpath", os.path.realpath(sys.executable))
print("sanity_prefix", sys.prefix)
print("sanity_torch", torch.__version__, "cuda_device_count", torch.cuda.device_count())
print("sanity_numpy", numpy.__version__, "sanity_pandas", pandas.__version__)
assert os.path.realpath(sys.executable) == os.path.realpath(PINNED), sys.executable
assert torch.cuda.device_count() == 0, torch.cuda.device_count()
assert torch.__version__.startswith("2.6.0"), torch.__version__
PYEOF
SANITY=$?
if [ "$SANITY" -ne 0 ]; then
  echo "STOP_INTERPRETER_SANITY rc=$SANITY" >> "$LOG"
  echo 9 > "$BASE/launch.rc"
  exit 9
fi

cd "$H" || { echo 10 > "$BASE/launch.rc"; exit 10; }
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1

"$PY" "$BASE/scripts/monitor.py" "$S" "$RAW/monitor.json" 2400 &
MPID=$!

echo "smoke_start_utc=$(date -u +%FT%TZ)" >> "$LOG"
taskset -c "$CPUS" "$PY" -m tests.trackg.port_smoke_gpu \
  --node mlgym_titanic \
  --cpus "$CPUS" \
  --memory-limit "external: systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
  --runs-root "$BASE/runs" \
  --provisional-timeout 1800 2>&1 | tee "$RAW/smoke_stdout.txt"
RC=${PIPESTATUS[0]}
echo "SMOKE_MAIN_RC=$RC" >> "$LOG"
echo "smoke_end_utc=$(date -u +%FT%TZ)" >> "$LOG"

kill -TERM "$MPID" 2>/dev/null
wait "$MPID" 2>/dev/null

for prop in memory.peak memory.events memory.stat memory.current; do
  cat "$S/$prop" > "$RAW/scope_${prop//./_}.txt" 2>/dev/null
done
echo "scope_memory_peak_bytes=$(cat "$RAW/scope_memory_peak.txt" 2>/dev/null)" >> "$LOG"
echo "launch_done_utc=$(date -u +%FT%TZ)" >> "$LOG"
echo "$RC" > "$BASE/launch.rc"
exit "$RC"
