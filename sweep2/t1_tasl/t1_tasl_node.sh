#!/bin/bash
# T1 on the TASL pair: run one G.1b or G.4 node job inside a delegated user scope, as the census smokes did
# (systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0), with AR_TEST_CGROUP_PARENT set to
# that scope and the node's CPU affinity (taskset). ENGINEERING_ONLY; AI-assisted.
#   t1_tasl_node.sh g1b <spec.json> <node> <note.md> [--enable]
#   t1_tasl_node.sh g4  <spec.json> <node> <note.md> <server_record.json> [--enable]
#   t1_tasl_node.sh xc  <crosscheck_spec.json> <node> <xc_note.md> <TASL-7|TASL-2> [--enable]
#   t1_tasl_node.sh g5  <g5_spec.json> <node> <c3_t1_labels note.md> <job> <server_record.json|-> [--enable]
#   t1_tasl_node.sh g5t7 <g5_spec.json> <node> <c3_t1_labels note.md> <audits-wave1|audits-wave2> <chunk> [--enable]
#     (on TASL-7: one claimed G.5 audit chunk, R1-G5-AUDIT-TWO-CARDS; the claim and the wave's plan copied from TASL-2)
# The keys: --enable and G1B_TASL_ENABLE_REAL=1 (g1b, xc), G4_TASL_ENABLE_REAL=1 (g4) or G5_TASL_ENABLE_REAL=1 (g5;
# job is campaigns-wave1|audits-wave1|campaigns-wave2|audits-wave2, and campaign jobs need the server record). Each call writes a new log
# <runs_root>/<run_id>/_logs/<node>-<utc>-<pid>.node.log (never overwritten), passed to the job, which records it;
# the seal binds it. Exit codes: 0 job complete; 2 usage or spec; 3 log; 4 job STOP or refusal; 5 scope failure.
# Every kind, g5 included, uses the same scope properties. No -p OOMPolicy= is passed: scope units accept it only
# from systemd v253, and TASL-2 runs systemd 249 (249.11-0ubuntu3.23; docs/r1/reports/trackg_g0_20261117/
# TASL2_T1_PRECHECK_20261121_captures/host_facts.txt), where a scope has no OOMPolicy and systemd does not act on an
# OOM kill inside it (G5 follow-ups review M1). The smoke checks memory.oom.group = 0 and that systemd-oomd leaves the
# scope alone.
set -u
set -o noclobber
KIND=${1:-}; SPEC=${2:-}; NODE=${3:-}; NOTE=${4:-}
case "$KIND" in
  g1b) SCRIPT=g1b_tasl.py; SERVER=""; ENABLE=${5:-} ;;
  xc)  SCRIPT=g1b_crosscheck.py; SERVER=""; XHOST=${5:-}; ENABLE=${6:-}
       case "$XHOST" in TASL-7|TASL-2) ;; *) echo "STOP: xc needs the host TASL-7 or TASL-2" >&2; exit 2 ;; esac ;;
  g4)  SCRIPT=g4_tasl.py; SERVER=${5:-}; ENABLE=${6:-}
       [ -n "$SERVER" ] || { echo "STOP: g4 needs the server record" >&2; exit 2; } ;;
  g5)  SCRIPT=g5_tasl.py; JOB=${5:-}; SERVER=${6:-}; ENABLE=${7:-}
       case "$JOB" in campaigns-wave1|audits-wave1|campaigns-wave2|audits-wave2) ;;
         *) echo "STOP: g5 needs the job (campaigns-wave1|audits-wave1|campaigns-wave2|audits-wave2)" >&2; exit 2 ;; esac
       [ -n "$SERVER" ] || { echo "STOP: g5 needs the server record or -" >&2; exit 2; } ;;
  g5t7) SCRIPT=g5_tasl.py; JOB=${5:-}; CHUNK=${6:-}; ENABLE=${7:-}; SERVER="-"
       case "$JOB" in audits-wave1|audits-wave2) ;;
         *) echo "STOP: g5t7 runs audit chunks only (audits-wave1|audits-wave2)" >&2; exit 2 ;; esac
       case "$CHUNK" in ''|*[!0-9]*) echo "STOP: g5t7 needs the claimed chunk number" >&2; exit 2 ;; esac ;;
  *)   echo "usage: t1_tasl_node.sh g1b|g4|xc|g5|g5t7 <spec> <node> <note> [<server_record>|<host>|<job> <server_record|->] [--enable]" >&2; exit 2 ;;
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
[ "$KIND" = g5 ] && ARGS=(run "$SPEC" --node "$NODE" --note "$NOTE" --job "$JOB")
[ "$KIND" = g5 ] && [ "$SERVER" != "-" ] && ARGS+=(--server-record "$SERVER")
[ "$KIND" = g5t7 ] && ARGS=(run "$SPEC" --node "$NODE" --note "$NOTE" --job "$JOB" --host TASL-7 --chunk "$CHUNK")
[ "$KIND" = g4 ] && ARGS+=(--server-record "$SERVER")
[ "$KIND" = xc ] && ARGS+=(--host "$XHOST")
[ -n "$ENABLE" ] && ARGS+=(--enable)
{
  echo "# t1_tasl $KIND node=$NODE spec=$SPEC start=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) cpus=$CPUS"
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
    env T1_CPUS="$CPUS" T1_PY="$PY" T1_LOG="$LOG" bash -c '
      CG=$(sed -n "s/^0:://p" /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
      echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
      export PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" G1B_TASL_NODE_LOG="$T1_LOG" G4_TASL_NODE_LOG="$T1_LOG" G5_TASL_NODE_LOG="$T1_LOG"
      unset NVIDIA_VISIBLE_DEVICES _CONDOR_AssignedGPUs
      taskset -c "$T1_CPUS" "$T1_PY" "$@"
      RC=$?; echo "NODE_EXIT=$RC"; exit $RC' t1_tasl "$HERE/$SCRIPT" "${ARGS[@]}"
  echo "systemd_run_rc=$?"
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG" 2>&1
if grep -q "^NODE_EXIT=0$" "$LOG"; then exit 0; fi
if grep -q "^NODE_EXIT=" "$LOG"; then exit 4; fi
exit 5
