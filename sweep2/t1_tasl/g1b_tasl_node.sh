#!/bin/bash
# G.1b on the TASL pair: run one node inside a delegated user scope, as the census smokes did
# (systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0), with AR_TEST_CGROUP_PARENT set to
# that scope and the node's CPU affinity. ENGINEERING_ONLY; AI-assisted.
# usage: g1b_tasl_node.sh <spec.json> <node> <note.md> [--enable]
# The two keys: --enable and G1B_TASL_ENABLE_REAL=1. The log <runs_root>/<run_id>/<node>.node.log sits next to the job
# directory and is bound by the seal receipt.
set -u
SPEC=$1; NODE=$2; NOTE=$3; ENABLE=${4:-}
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${G1B_TASL_ORCHESTRATOR_PYTHON:-python3}
CPUS=$("$PY" "$HERE/g1b_tasl.py" cpus "$SPEC" --node "$NODE") || { echo "STOP: cannot read the node's cpus" >&2; exit 2; }
LOGDIR=$("$PY" "$HERE/g1b_tasl.py" logdir "$SPEC" --node "$NODE") || { echo "STOP: cannot read the runs root" >&2; exit 2; }
mkdir -p "$LOGDIR" || exit 3
LOG="$LOGDIR/$NODE.node.log"
[ -e "$LOG" ] && { echo "STOP: $LOG exists (no overwrite)" >&2; exit 3; }
{
  echo "# g1b_tasl node=$NODE spec=$SPEC start=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) cpus=$CPUS"
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
    CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
    export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=""
    unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
    taskset -c "'"$CPUS"'" "'"$PY"'" "'"$HERE"'/g1b_tasl.py" run-node "'"$SPEC"'" --node "'"$NODE"'" --note "'"$NOTE"'" '"$ENABLE"'
    RC=$?; echo "NODE_EXIT=$RC"; exit $RC'
  echo "systemd_run_rc=$?"
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
grep -q "NODE_EXIT=0" "$LOG"
