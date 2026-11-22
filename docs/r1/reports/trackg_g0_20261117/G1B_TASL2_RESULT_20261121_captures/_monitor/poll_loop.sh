#!/bin/bash
# READ-ONLY monitor poll loop v3 for the authorized G.1b TASL-2 run (run_id g1b-tasl-20261121-b).
# Runs on the Mac; every ~5 min takes ONE read-only snapshot over SSH (`ssh portal_zhixu`) and appends it to
# polls.log. It never starts, retries, stops or modifies any remote job: only cat/tail/grep/ls/fuser/nvidia-smi
# queries. Terminal conditions handled:
#   * DONE / DONE_AFTER_FMNIST in logs/g1b_tasl2.status                       -> exit TERMINAL
#   * a STOP count above the 2 pre-existing fmnist STOP lines                 -> exit TERMINAL
#   * STOP_FETCH / STOP_SEAL in the status file                               -> exit TERMINAL
#   * 16 h after run start (2026-11-22T13:45:28Z)                             -> exit DEADLINE_16H
#   * runner process gone for 3 consecutive polls with no terminal status     -> exit ANOMALY_RUNNER_GONE
set -u
CAP="/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116/docs/r1/reports/trackg_g0_20261117/G1B_TASL2_RESULT_20261121_captures"
MON="$CAP/_monitor"
mkdir -p "$MON"
LOG="$MON/polls.log"
VERDICT="$MON/verdict"
: > "$VERDICT"
[ -s "$MON/timeline.tsv" ] || printf 'ts_utc\tstatus\tnode\tattempt\tpart_rows\tlease_holders\n' > "$MON/timeline.tsv"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=25 portal_zhixu"
DEADLINE=1795355128   # run start 2026-11-21T21:45:28Z + 16 h = 2026-11-22T13:45:28Z
BASELINE_STOPS=2      # "STOP mlgym_fmnist try=1 class=missing" + "...try=2 class=infrastructure" predate this loop
GONE=0
echo "MONITOR_V3_START $(date -u +%FT%TZ) deadline_utc=2026-11-22T13:45:28Z baseline_stops=$BASELINE_STOPS" >> "$LOG"
while :; do
  NOW=$(date -u +%s)
  TS=$(date -u +%FT%TZ)
  if [ "$NOW" -ge "$DEADLINE" ]; then
    echo "VERDICT=DEADLINE_16H $TS" >> "$LOG"
    echo "DEADLINE_16H" > "$VERDICT"
    break
  fi
  SNAP=$($SSH 'bash -s' 2>&1 <<'REMOTE'
set -u
B=/home/dowling/r1_tracks/t1_tasl
S=$B/logs/g1b_tasl2.status
L=$B/logs/g1b_tasl2_20261121.log
R=$B/runs/g1b-tasl-20261121-b
echo "SERVER_UTC=$(date -u +%FT%TZ)"
echo "RUNNER=$(pgrep -f 'run_g1b' | head -1)"
if [ -f "$S" ]; then
  echo "STATUSSTATE=present"
  echo "STATUS_LINES_BEGIN"
  cat "$S"
  echo "STATUS_LINES_END"
else
  echo "STATUSSTATE=missing"
fi
echo "RUNLOG_TAIL_BEGIN"
tail -n 18 "$L"
echo "RUNLOG_TAIL_END"
echo "NODEEVENTS_BEGIN"
grep -E '^(NODE_START|NODE_RC|SEAL_RC|STOP_CLASS|RETRY_INFRA|RESTART|AFTER_FMNIST_START) ' "$L" | tail -n 25
echo "NODEEVENTS_END"
echo "ATTEMPTS_BEGIN"
ls -d "$R"/*/attempt-* 2>/dev/null
echo "ATTEMPTS_END"
N=$(grep -E '^NODE_START ' "$L" | tail -1 | awk '{print $2}')
A=$(ls -dt "$R/$N"/attempt-* 2>/dev/null | head -1)
echo "CURRENT_NODE=${N:-none}"
echo "CURRENT_ATTEMPT=${A:-none}"
if [ -n "$A" ] && [ -f "$A/attempt.json" ]; then echo "ATTEMPT_JSON=$(tr -d '\n' < "$A/attempt.json")"; fi
if [ -n "$A" ] && [ -f "$A/job_record.json" ]; then echo "ATTEMPT_JOB_RECORD=present"; fi
if [ -n "$A" ]; then
  echo "PART_ROWS_BEGIN"
  for part in default train split joint; do
    f="$A/out/$part/runs.jsonl"
    if [ -f "$f" ]; then echo "PART $part $(wc -l < "$f")"; fi
  done
  echo "PART_ROWS_END"
fi
LG=$(ls -t "$R"/_logs/*.node.log 2>/dev/null | head -1)
echo "NODELOG=${LG:-none}"
echo "NODELOG_TAIL_BEGIN"
tail -n 8 "$LG" 2>/dev/null
echo "NODELOG_TAIL_END"
echo "GPU_APPS_BEGIN"
nvidia-smi --query-compute-apps=pid,process_name,used_memory,gpu_uuid --format=csv,noheader 2>&1
echo "GPU_APPS_END"
echo "GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>&1 | head -1)"
LP=/home/dowling/r1_locks/gpu0.lock
LPIDS=$(fuser "$LP" 2>/dev/null | tr -s ' ')
echo "LEASE_FILE=$LP"
echo "LEASE_HOLDERS=${LPIDS:-FREE}"
echo "DISK_FREE=$(df -h "$B" 2>/dev/null | tail -1 | awk '{print $4}')"
REMOTE
)
  {
    echo "=== POLL $TS (epoch $NOW) ==="
    echo "$SNAP"
    echo
  } >> "$LOG"
  RUNNER=$(printf '%s\n' "$SNAP" | sed -n 's/^RUNNER=//p' | tail -1)
  CUR_NODE=$(printf '%s\n' "$SNAP" | sed -n 's/^CURRENT_NODE=//p' | tail -1)
  CUR_ATT=$(printf '%s\n' "$SNAP" | sed -n 's/^CURRENT_ATTEMPT=//p' | tail -1)
  PARTS=$(printf '%s\n' "$SNAP" | sed -n '/^PART_ROWS_BEGIN$/,/^PART_ROWS_END$/p' | sed -n 's/^PART \([a-z]*\) \([0-9]*\)$/\1=\2/p' | paste -sd, -)
  LEASE=$(printf '%s\n' "$SNAP" | sed -n 's/^LEASE_HOLDERS=//p' | tail -1)
  STATUS_TEXT=$(printf '%s\n' "$SNAP" | sed -n '/^STATUS_LINES_BEGIN$/,/^STATUS_LINES_END$/p' | grep -v '^STATUS_LINES_')
  STOPCNT=$(printf '%s\n' "$STATUS_TEXT" | grep -c '^STOP ') || true
  STOPCNT=${STOPCNT:-0}
  HASDONE=$(printf '%s\n' "$STATUS_TEXT" | grep -cE 'DONE') || true
  HASDONE=${HASDONE:-0}
  HASFETCH=$(printf '%s\n' "$STATUS_TEXT" | grep -cE 'STOP_FETCH|STOP_SEAL') || true
  HASFETCH=${HASFETCH:-0}
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$TS" "run=$([ "$HASDONE" -gt 0 ] && echo done || echo running)" "$CUR_NODE" "$(basename "${CUR_ATT:-none}")" "$PARTS" "$LEASE" >> "$MON/timeline.tsv"
  echo "POLL $TS runner=$RUNNER node=$CUR_NODE attempt=$(basename "${CUR_ATT:-none}") rows[$PARTS] lease=${LEASE:-?} stops=$STOPCNT done=$HASDONE"
  if [ "$HASDONE" -gt 0 ] || [ "$STOPCNT" -gt "$BASELINE_STOPS" ] || [ "$HASFETCH" -gt 0 ]; then
    { echo "VERDICT=TERMINAL $TS"; echo "STATUS:"; printf '%s\n' "$STATUS_TEXT"; } >> "$VERDICT"
    echo "VERDICT_TERMINAL $TS stops=$STOPCNT done=$HASDONE" >> "$LOG"
    break
  fi
  if [ -z "$RUNNER" ]; then
    GONE=$((GONE+1))
    echo "NOTE runner-process not found (consecutive=$GONE) $TS" >> "$LOG"
    if [ "$GONE" -ge 3 ]; then
      echo "VERDICT=ANOMALY_RUNNER_GONE $TS" >> "$LOG"
      echo "ANOMALY_RUNNER_GONE" > "$VERDICT"
      break
    fi
  else
    GONE=0
  fi
  if [ -z "$SNAP" ]; then echo "NOTE empty snapshot (ssh failure) $TS" >> "$LOG"; fi
  sleep 300
done
echo "MONITOR_LOOP_EXIT $(date -u +%FT%TZ)" >> "$LOG"
