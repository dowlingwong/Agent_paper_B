#!/bin/bash
# G1b note-2 driver on TASL-7: the three TASL-7 nodes one after another under the GPU lease, sealed on success.
# ENGINEERING_ONLY; AI-assisted. Launch checkout paper_note2 HEAD 34a5b1d6 (the G.1b spec re-issue commit), signed
# note copied byte-identically from origin/main. A node/timing STOP ends that node and the chain goes on to the next
# authorized node; an infrastructure STOP may be retried once; a launch refusal or missing attempt aborts the chain.
set -u
B=/home/dowling/r1_tracks/t1_tasl
P=$B/paper_note2
SPEC=$P/sweep2/t1_tasl/g1b_tasl_spec.json
NOTE=$P/docs/r1/authorizations/g1b_t1_tasl_20261123.md
PY=$B/envs/torch312/bin/python
CAP=$B/logs/note2_capture.py
RUNID=g1b-tasl-20261121-b
TAG=note2
LOG=$B/logs/g1b_${TAG}_tasl7_20261124.log
STATUS=$B/logs/g1b_${TAG}_tasl7_20261124.status
C=$B/captures/${TAG}_20261124/TASL-7
NODES="mlab_cifar10 mlgym_cifar10 mlgym_breakout_minatar"
mkdir -p "$C" "$B/logs"
if [ -e "$STATUS" ] || [ -e "$LOG" ]; then echo "CHAIN_ABORT status/log exists" >&2; exit 9; fi
export G1B_TASL_ENABLE_REAL=1
export T1_TASL_ORCHESTRATOR_PYTHON="$PY"
export PYTHONDONTWRITEBYTECODE=1

say() { echo "$*" >> "$STATUS"; echo "$*" >> "$LOG"; }

say "START $(date -u +%Y-%m-%dT%H:%M:%SZ) host=$(hostname) pid=$$ driver=$0"

{
  echo "# G1b note 2 TASL-7 preflight $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# hostname=$(hostname) user=$(whoami) uid=$(id -u)"
  echo "# checkout=$P"
  echo "# HEAD=$(git -C "$P" rev-parse HEAD)"
  echo "# origin_url=$(git -C "$P" remote get-url origin)"
  echo "# origin_main=$(git -C "$P" rev-parse origin/main)"
  echo "# lsremote_main=$(git -C "$P" ls-remote origin refs/heads/main | cut -f1)"
  echo "# spec_sha256=$(sha256sum "$SPEC" | cut -d' ' -f1)"
  echo "# note_sha256=$(sha256sum "$NOTE" | cut -d' ' -f1)"
  echo "# note_on_main_sha256=$(git -C "$P" show origin/main:docs/r1/authorizations/g1b_t1_tasl_20261123.md | sha256sum | cut -d' ' -f1)"
  echo "# harness=$(git -C "$B/harness" rev-parse HEAD)"
  echo "# harness_status=[$(git -C "$B/harness" status --porcelain | tr '\n' ';')]"
  echo "# runs_dir_before=[$(ls -d "$B"/runs/"$RUNID" 2>/dev/null || echo none)]"
  echo "# sealed_dir_before=[$(ls -d "$B"/sealed_g1b/"$RUNID" 2>/dev/null || echo none)]"
  echo "# orchestrator_python=$PY ($("$PY" -V 2>&1))"
  echo "# gpu_nodes=$NODES"
  nvidia-smi -L
  nvidia-smi --query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu --format=csv
  echo "# compute_apps_csv:"
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
  if flock -n "$HOME/r1_locks/gpu0.lock" -c true 2>/dev/null; then echo "lease_free=yes"; else echo "lease_free=NO"; fi
  echo "# ptrace_scope=$(cat /proc/sys/kernel/yama/ptrace_scope)"
  echo "# cuda122=$(test -d /usr/local/cuda-12.2 && echo yes || echo no)"
  free -g | head -2
  df -h "$B" | tail -1
  echo "# loadavg=$(cat /proc/loadavg)"
  ls -l "$HOME/r1_locks/gpu0.lock"
} > "$C/preflight.txt" 2>&1 || true
say "PREFLIGHT $(tr '\n' ' ' < "$C/preflight.txt" | cut -c1-600)"

cd "$P" || { say "CHAIN_ABORT cd_failed $P"; exit 9; }

for N in $NODES; do
  if ! git -C "$P" fetch -q origin main; then say "CHAIN_ABORT fetch_failed before $N"; exit 1; fi
  OM=$(git -C "$P" rev-parse origin/main)
  LM=$(git -C "$P" ls-remote origin refs/heads/main | cut -f1)
  say "NODE_START $N $(date -u +%Y-%m-%dT%H:%M:%SZ) origin_main=$OM lsremote=$LM"
  if [ "$OM" != "$LM" ]; then say "CHAIN_ABORT origin_main_differs $OM != $LM before $N"; exit 1; fi
  TRY=1
  while :; do
    T0=$(date +%s)
    bash "$P/sweep2/t1_tasl/t1_tasl_node.sh" g1b "$SPEC" "$N" "$NOTE" --enable >> "$LOG" 2>&1
    rc=$?
    T1=$(date +%s)
    WALL=$((T1 - T0))
    A=$(ls -dt "$B"/runs/"$RUNID"/"$N"/attempt-* 2>/dev/null | head -1)
    say "NODE_RC $N try=$TRY rc=$rc wall_s=$WALL end=$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt=${A:-none}"
    if [ "$rc" -eq 0 ] && [ -n "$A" ] && [ -f "$A/job_record.json" ]; then
      "$PY" "$P/sweep2/t1_tasl/g1b_tasl.py" seal "$A" "$SPEC" --node "$N" >> "$LOG" 2>&1
      src=$?
      say "SEAL_RC $N try=$TRY rc=$src"
      if [ "$src" -ne 0 ]; then say "CHAIN_ABORT seal_failed $N rc=$src attempt=$A"; exit 2; fi
      SD=$(ls -d "$B"/sealed_g1b/"$RUNID"/"$N"/attempt-* 2>/dev/null | head -1)
      say "SEALED $N $SD"
      "$PY" "$CAP" "$A" "$SD" "$SPEC" "$N" "$WALL" "$C" "$OM" >> "$LOG" 2>&1
      cap=$?
      if [ "$cap" -ne 0 ]; then say "CAPTURE_WARN $N rc=$cap"; else say "CAPTURED $N"; fi
      break
    fi
    if [ -z "$A" ]; then
      if [ -d "$B/runs/$RUNID/_refusals" ]; then cp -r "$B/runs/$RUNID/_refusals" "$C/$N.refusals" 2>/dev/null || true; fi
      say "CHAIN_ABORT launch_or_scope $N rc=$rc (no attempt created; a launch refusal is not worked around)"
      exit 3
    fi
    SC=""
    if [ -f "$A/job_record.json" ]; then
      SC=$("$PY" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("stop_class") or "none")' "$A/job_record.json" 2>/dev/null)
    else
      "$PY" "$P/sweep2/t1_tasl/g1b_tasl.py" close-attempt "$SPEC" "$A" --node "$N" \
          --reason "driver: attempt left no job record (scope killed or wrapper aborted); closed as infrastructure" >> "$LOG" 2>&1
      if [ $? -eq 0 ]; then SC=infrastructure; else SC=missing; fi
    fi
    if [ -f "$A/job_record.json" ]; then cp "$A/job_record.json" "$C/$N.try$TRY.stop.job_record.json" 2>/dev/null || true; fi
    say "NODE_STOP $N try=$TRY stop_class=${SC:-unknown} attempt=$A"
    if [ "$SC" = "infrastructure" ] && [ "$TRY" -lt 2 ]; then
      TRY=$((TRY + 1))
      say "RETRY $N try=$TRY reason=infrastructure"
      continue
    fi
    if [ "$SC" = "infrastructure" ]; then say "CHAIN_ABORT infrastructure_twice $N attempt=$A"; exit 4; fi
    say "NODE_ENDED $N stop_class=$SC (author STOP; no new attempt of this node)"
    break
  done
done
say "CHAIN_DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit 0
