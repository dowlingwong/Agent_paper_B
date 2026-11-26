#!/bin/bash
# One delegated-scope invocation for the ENGINEERING-ONLY TASL-2 G.5 smoke.
# usage: smoke_wrapper.sh probe
#        smoke_wrapper.sh job <campaigns|audits> <node> <scenario>
#        smoke_wrapper.sh job-kill <campaigns|audits> <node> <scenario>   (deliberate engine kill)
# The systemd-run line is byte-for-byte the argv of t1_tasl_node.sh's kinds
# (no -p OOMPolicy=; systemd 249 on TASL-2).
set -u
S=/home/dowling/r1_engineering/tasl2_g5_smoke_20261123
PAPER=/home/dowling/r1_tracks/t1_tasl/paper_g5smoke
PY=/usr/bin/python3
CPUS=16-31
LOGS=$S/logs
MODE=${1:?}; shift
case "$MODE" in
  probe)    ARGS=(probe); KILL=0 ;;
  job)      ARGS=(job "$@"); KILL=0 ;;
  orphan)   ARGS=(orphan); KILL=0 ;;
  job-kill) ARGS=(job "$@"); KILL=1 ;;
  *) echo "usage: $0 probe|job|job-kill ..." >&2; exit 2 ;;
esac
mkdir -p "$LOGS" "$S/work"
LOG="$LOGS/$MODE-$(echo "$ARGS" | tr ' /' '__')-$(date -u +%Y%m%dT%H%M%SZ)-$$.log"
: > "$LOG"
rm -f "$S/work/engine.pid"
RUN=(systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 --
     env T1_PY="$PY" T1_LOG="$LOG" T1_CPUS="$CPUS" T1_ROOT="$S" T1_PAPER="$PAPER" \
     bash "$S/bin/inner.sh" "${ARGS[@]}")
{
  echo "# smoke_wrapper mode=$MODE args=${ARGS[*]} start=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) mode=$MODE"
  if [ "$KILL" = 1 ]; then
    "${RUN[@]}" >> "$LOG" 2>&1 &
    SPID=$!
    for _ in $(seq 1 240); do [ -s "$S/work/engine.pid" ] && break; sleep 0.25; done
    if [ -s "$S/work/engine.pid" ]; then
      EPID=$(cat "$S/work/engine.pid")
      echo "deliberate_engine_kill pid=$EPID utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
      kill -9 "$EPID" 2>>"$LOG" && echo "kill_signal_ok=1" >> "$LOG"
    else
      echo "engine_pidfile_absent=1" >> "$LOG"
    fi
    wait "$SPID"; SRC=$?
  else
    "${RUN[@]}" >> "$LOG" 2>&1; SRC=$?
  fi
  echo "systemd_run_rc=$SRC"
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG" 2>&1
exit "$SRC"
