#!/bin/bash
# Round-4 R1-TRACKG-AR-COND7A infrastructure-retry watcher.
# Waits for a card with 0 live compute apps and >=40 GiB free, re-checks the Paper A gate, then launches exactly
# one run_ar_cond7a_retry.sh smoke per attempt (fresh run root/evidence dir under the session dir), monitors the
# used card for co-tenant apps during the run, and retries ONLY on external co-tenant OOM/contention. Max 2 fresh
# attempts, 3 h window. Every attempt is preserved; no deletion; no shared-card launch.
set -u
B=/home/dowling/r1_trackg_20261117
NL=$B/bin/nvidia-smi-live
PY=$B/envs/torch312/bin/python
E=/home/dowling/r1_engineering/u2_iso_20261119
S=$(date -u +%Y%m%dT%H%M%SZ)
R=$E/ar_cond7a_retry_$S
mkdir -p "$R"
printf '%s\n' "$R" > "$E/last_retry_session.txt"
STATUS=$R/session_status.txt
LOG=$R/watcher.log
START=$(date +%s)
DEADLINE=$((START + 10800))   # 3 h window
MAX_ATTEMPTS=2
MIN_FREE_MIB=40960            # 40 GiB
ATTEMPTS=0
: > "$LOG"

say() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

# echo "<uuid> <free_mib>" for the first card with 0 live compute apps and free >= MIN_FREE_MIB
find_card() {
  local apps
  apps=$("$NL" --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>/dev/null | awk -F', ' '$3+0>0')
  "$NL" --query-gpu=index,uuid,memory.free,utilization.gpu --format=csv,noheader 2>/dev/null | while IFS=, read -r idx uuid free util; do
    uuid=$(echo "$uuid" | tr -d ' '); free=$(echo "$free" | tr -dc '0-9')
    n=$(printf '%s\n' "$apps" | awk -F', ' -v g="$uuid" '$1==g' | wc -l | tr -dc '0-9')
    if [ "$n" = "0" ] && [ "${free:-0}" -ge "$MIN_FREE_MIB" ]; then
      echo "$uuid $free"
      break
    fi
  done | head -1
}

card_census() {
  local out=$1
  {
    echo "# card census $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$NL" --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader
    echo "# compute apps with users"
    "$NL" --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>/dev/null | while IFS=, read -r u p m; do
      p=$(echo "$p" | tr -d ' ')
      echo "$u pid=$p user=$(ps -o user= -p "$p" 2>/dev/null | tr -d ' ') etime=$(ps -o etime= -p "$p" 2>/dev/null | tr -d ' ') mem=$m"
    done | sort
  } > "$out" 2>&1
}

gate_check() {
  local out=$1
  (cd "$B/Agent_paper_B_main_16185b0b" && "$PY" r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json > "$out" 2>/dev/null)
  python3 - "$out" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    ok = (d.get("verdict") == "clear_finished" and d.get("paper_a_live_waiting_for_card") is False
          and ((d.get("evidence") or {}).get("gpu") or {}).get("paper_a_processes") == []
          and ((d.get("evidence") or {}).get("gpu") or {}).get("unidentified_apps") == 0)
except Exception:
    ok = False
print("yes" if ok else "no")
PY
}

foreign_apps_on_gpu() {
  # prints one line per live compute app on the given GPU whose user is not dowling
  local gpu=$1
  "$NL" --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>/dev/null | awk -F', ' -v g="$gpu" '$1==g && $3+0>0' | while IFS=, read -r u p m; do
    p=$(echo "$p" | tr -d ' ')
    user=$(ps -o user= -p "$p" 2>/dev/null | tr -d ' ')
    [ -n "$user" ] && [ "$user" != "dowling" ] && echo "pid=$p user=$user mem=$m"
  done
}

# wait for the smoke in one attempt; abort if foreign apps appear on the used card for 2 consecutive ticks
monitor_attempt() {
  local ev=$1 gpu=$2 attempt=$3
  local bad=0 ticks=0
  : > "$R/attempt${attempt}_monitor.log"
  while :; do
    if [ -f "$ev/DONE" ]; then return 0; fi
    sleep 25
    if [ -f "$ev/DONE" ]; then return 0; fi
    local now; now=$(date +%s)
    if [ "$now" -ge "$DEADLINE" ]; then
      say "attempt $attempt: 3 h window reached while running; aborting the smoke to leave no orphan"
      local scope; scope=$(grep -o "scope_cgroup=.*" "$ev/logs/run_node.log" 2>/dev/null | head -1 | cut -d= -f2)
      [ -n "${scope:-}" ] && [ -f "$scope/cgroup.kill" ] && echo 1 > "$scope/cgroup.kill" 2>/dev/null
      say "window_abort=yes" >> "$R/attempt${attempt}_monitor.log"
      return 2
    fi
    local foreign free
    foreign=$(foreign_apps_on_gpu "$gpu" | wc -l | tr -dc '0-9')
    free=$("$NL" --query-gpu=uuid,memory.free --format=csv,noheader 2>/dev/null | awk -F', ' -v g="$gpu" '$1==g {print $2}' | tr -dc '0-9')
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt=$attempt foreign_apps=$foreign free_mib=${free:-?}" >> "$R/attempt${attempt}_monitor.log"
    if [ "${foreign:-0}" -gt 0 ]; then bad=$((bad + 1)); else bad=0; fi
    if [ "$bad" -ge 2 ]; then
      say "attempt $attempt: co-tenant apps appeared on the used card (2 consecutive ticks); aborting attempt"
      card_census "$ev/contention_abort_census.txt"
      {
        echo "contention_abort=yes"
        echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        echo "foreign_apps_at_abort=$(foreign_apps_on_gpu "$gpu" | tr '\n' '|')"
        echo "free_mib_at_abort=${free:-?}"
      } > "$ev/CONTENTION_ABORT.txt"
      local scope; scope=$(grep -o "scope_cgroup=.*" "$ev/logs/run_node.log" 2>/dev/null | head -1 | cut -d= -f2)
      if [ -n "${scope:-}" ] && [ -f "$scope/cgroup.kill" ]; then echo 1 > "$scope/cgroup.kill" 2>/dev/null; fi
      return 1
    fi
  done
}

say "round-4 cond7a retry session dir=$R window=${DEADLINE}s max_attempts=$MAX_ATTEMPTS min_free=${MIN_FREE_MIB}MiB"
while :; do
  now=$(date +%s)
  if [ "$now" -ge "$DEADLINE" ]; then
    say "3 h window reached; no clean attempt remains"
    { echo "session=STOP_WINDOW_EXHAUSTED"; echo "attempts=$ATTEMPTS"; echo "stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$STATUS"
    exit 0
  fi
  if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
    say "max $MAX_ATTEMPTS fresh attempts used; stopping"
    { echo "session=STOP_ATTEMPTS_EXHAUSTED"; echo "attempts=$ATTEMPTS"; echo "stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$STATUS"
    exit 0
  fi
  read -r cand_uuid cand_free <<< "$(find_card)"
  if [ -z "${cand_uuid:-}" ]; then
    card_census "$R/wait_census_latest.txt"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) no card with 0 apps and >=${MIN_FREE_MIB}MiB free; waiting" >> "$LOG"
    sleep 30
    continue
  fi
  say "candidate card $cand_uuid free=${cand_free}MiB (0 apps)"
  gate_json=$R/gate_precheck_$(date -u +%H%M%SZ).json
  if [ "$(gate_check "$gate_json")" != "yes" ]; then
    say "Paper A gate pre-check not clear ($gate_json); waiting"
    sleep 30
    continue
  fi
  # re-check the card immediately before launch
  read -r re_uuid re_free <<< "$(find_card)"
  if [ "${re_uuid:-}" != "$cand_uuid" ]; then
    say "card changed between selection and launch (now '${re_uuid:-none}'); waiting"
    sleep 20
    continue
  fi
  ATTEMPTS=$((ATTEMPTS + 1))
  CPUS=$(mpstat -P ALL 1 2 2>/dev/null | awk '$2 ~ /^[0-9]+$/ {c=$2; i=$NF; if (!(c in mn) || i<mn[c]) mn[c]=i} END {for (c in mn) printf "%s %.1f\n", c, mn[c]}' | sort -k2 -nr -k1 -n | head -8 | awk 'BEGIN{s=""}{printf "%s%s", s, $1; s=","}')
  EV=$R/attempt${ATTEMPTS}_${cand_uuid%%-*}_$(date -u +%H%M%SZ)
  say "LAUNCH attempt=$ATTEMPTS gpu=$cand_uuid free=${re_free}MiB cpus=$CPUS ev=$EV"
  cd "$E" && RETRY_MIN_FREE_MIB=$MIN_FREE_MIB setsid nohup bash scripts/run_ar_cond7a_retry.sh "$cand_uuid" "$CPUS" "$EV" > "$R/launch_attempt${ATTEMPTS}.log" 2>&1 < /dev/null &
  mon_rc=0
  monitor_attempt "$EV" "$cand_uuid" "$ATTEMPTS" || mon_rc=$?
  # ensure the runner finalized (it writes DONE in all cases)
  for _ in $(seq 1 60); do [ -f "$EV/DONE" ] && break; sleep 10; done
  done_txt=$(cat "$EV/DONE" 2>/dev/null || echo NO_DONE)
  nrec=$(find "$EV/runs" -name run_record.json 2>/dev/null | wc -l | tr -dc '0-9')
  statusline=$(grep -E "^status=" "$EV/RESULT_STATUS.txt" 2>/dev/null | tail -1)
  # classification: external contention only if a co-tenant was observed (monitor abort) or a CUDA OOM/GPU error
  # happened while foreign apps were present on the used card
  external=no
  if [ "$mon_rc" -ne 0 ] || [ -f "$EV/CONTENTION_ABORT.txt" ]; then external=yes; fi
  if [ "$external" = "no" ] && grep -qE "CUDA out of memory|invalid resource handle|CUDA error" "$EV"/runs/*/run.log 2>/dev/null; then
    if [ -n "$(foreign_apps_on_gpu "$cand_uuid")" ]; then external=yes; card_census "$EV/contention_failure_census.txt"; fi
    # even if the co-tenant has already exited, the CUDA OOM message names the other processes on the card
    for fpid in $(grep -hoE "Process [0-9]+" "$EV"/runs/*/run.log 2>/dev/null | awk '{print $2}' | sort -u); do
      fuser=$(ps -o user= -p "$fpid" 2>/dev/null | tr -d ' ')
      if [ -n "${fuser:-}" ] && [ "$fuser" != "dowling" ]; then external=yes; card_census "$EV/contention_failure_census.txt"; fi
    done
  fi
  {
    echo "attempt=$ATTEMPTS"
    echo "gpu=$cand_uuid"
    echo "free_at_launch_mib=$re_free"
    echo "cpus=$CPUS"
    echo "ev=$EV"
    echo "done=$done_txt"
    echo "run_records=$nrec"
    echo "status_line=$statusline"
    echo "monitor_rc=$mon_rc"
    echo "external_contention=$external"
    echo "attempt_finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } > "$R/attempt${ATTEMPTS}_summary.txt"
  say "attempt=$ATTEMPTS finished: $done_txt run_records=$nrec external=$external (summary $R/attempt${ATTEMPTS}_summary.txt)"
  if echo "$done_txt" | grep -q "DONE_PASS"; then
    say "SUCCESS attempt=$ATTEMPTS ev=$EV"
    { echo "session=PASS"; echo "attempts=$ATTEMPTS"; echo "ev=$EV"; echo "finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$STATUS"
    exit 0
  fi
  if [ "$external" = "yes" ]; then
    if [ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ] && [ "$(date +%s)" -lt "$DEADLINE" ]; then
      say "attempt $ATTEMPTS failed with external co-tenant contention; recording STOP and waiting for another idle card"
      continue
    fi
    say "attempt $ATTEMPTS failed with external co-tenant contention and no fresh attempt/window remains"
    { echo "session=STOP_EXTERNAL_CONTENTION"; echo "attempts=$ATTEMPTS"; echo "last_ev=$EV"; echo "stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$STATUS"
    exit 0
  fi
  say "attempt $ATTEMPTS failed and is NOT external contention (code/unit failure); no retry per round-4 rule"
  { echo "session=STOP_NON_EXTERNAL_FAILURE"; echo "attempts=$ATTEMPTS"; echo "last_ev=$EV"; echo "stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } > "$STATUS"
  exit 0
done
