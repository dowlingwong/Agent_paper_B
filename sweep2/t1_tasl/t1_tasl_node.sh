#!/bin/bash
# T1 on the TASL pair: run one G.1b or G.4 node job inside a delegated user scope, as the census smokes did
# (systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0), with AR_TEST_CGROUP_PARENT set to
# that scope and the node's CPU affinity (taskset). ENGINEERING_ONLY; AI-assisted.
#   t1_tasl_node.sh g1b <spec.json> <node> <note.md> [--enable]
#   t1_tasl_node.sh g4  <spec.json> <node> <note.md> <server_record.json> [--enable]
#   t1_tasl_node.sh xc  <crosscheck_spec.json> <node> <xc_note.md> <TASL-7|TASL-2> [--enable]
# The keys: --enable and G1B_TASL_ENABLE_REAL=1 (g1b, xc) or G4_TASL_ENABLE_REAL=1 (g4). Each call writes a new log
# <runs_root>/<run_id>/_logs/<node>-<utc>-<pid>.node.log (never overwritten), passed to the job, which records it;
# the seal binds it. Exit codes: 0 job complete; 2 usage or spec; 3 log; 4 job STOP or refusal; 5 scope failure.
set -u
set -o noclobber
KIND=${1:-}; SPEC=${2:-}; NODE=${3:-}; NOTE=${4:-}
case "$KIND" in
  g1b) SCRIPT=g1b_tasl.py; SERVER=""; ENABLE=${5:-} ;;
  xc)  SCRIPT=g1b_crosscheck.py; SERVER=""; XHOST=${5:-}; ENABLE=${6:-}
       case "$XHOST" in TASL-7|TASL-2) ;; *) echo "STOP: xc needs the host TASL-7 or TASL-2" >&2; exit 2 ;; esac ;;
  g4)  SCRIPT=g4_tasl.py; SERVER=${5:-}; ENABLE=${6:-}
       [ -n "$SERVER" ] || { echo "STOP: g4 needs the server record" >&2; exit 2; } ;;
  *)   echo "usage: t1_tasl_node.sh g1b|g4|xc <spec> <node> <note> [<server_record>|<host>] [--enable]" >&2; exit 2 ;;
esac
[ -n "$SPEC" ] && [ -n "$NODE" ] && [ -n "$NOTE" ] || { echo "STOP: missing arguments" >&2; exit 2; }
[ -z "$ENABLE" ] || [ "$ENABLE" = "--enable" ] || { echo "STOP: unknown flag $ENABLE" >&2; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
PY=${T1_TASL_ORCHESTRATOR_PYTHON:-python3}
QUERY=(--node "$NODE")
[ "$KIND" = xc ] && QUERY+=(--host "$XHOST")
CPUS=$("$PY" "$HERE/$SCRIPT" cpus "$SPEC" "${QUERY[@]}") || { echo "STOP: cannot read the node's cpus" >&2; exit 2; }
LOGDIR=$("$PY" "$HERE/$SCRIPT" logdir "$SPEC" "${QUERY[@]}") || { echo "STOP: cannot read the log directory" >&2; exit 2; }
mkdir -p "$LOGDIR" || exit 3
LOG="$LOGDIR/$NODE-$(date -u +%Y%m%dT%H%M%SZ)-$$.node.log"
: > "$LOG" || { echo "STOP: $LOG exists (no overwrite)" >&2; exit 3; }
ARGS=(run-node "$SPEC" --node "$NODE" --note "$NOTE")
[ "$KIND" = g4 ] && ARGS+=(--server-record "$SERVER")
[ "$KIND" = xc ] && ARGS+=(--host "$XHOST")
[ -n "$ENABLE" ] && ARGS+=(--enable)
{
  echo "# t1_tasl $KIND node=$NODE spec=$SPEC start=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) cpus=$CPUS"
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
    env T1_CPUS="$CPUS" T1_PY="$PY" T1_LOG="$LOG" bash -c '
      CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
      echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
      export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG" G4_TASL_NODE_LOG="$T1_LOG"
      unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
      taskset -c "$T1_CPUS" "$T1_PY" "$@"
      RC=$?; echo "NODE_EXIT=$RC"; exit $RC' t1_tasl "$HERE/$SCRIPT" "${ARGS[@]}"
  echo "systemd_run_rc=$?"
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG" 2>&1
if grep -q "^NODE_EXIT=0$" "$LOG"; then exit 0; fi
if grep -q "^NODE_EXIT=" "$LOG"; then exit 4; fi
exit 5
