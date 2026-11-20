#!/bin/bash
# Wait for an idle Ada GPU (free>=8 GiB, no other compute app), then run the one cond7a isolated smoke.
# Logs a per-round GPU census; auto-launches run_ar_cond7a.sh once when a card frees; waits for the smoke DONE.
set -u
B=/home/dowling/r1_trackg_20261117
NL=$B/bin/nvidia-smi-live
E=/home/dowling/r1_engineering/u2_iso_20261119
LOG=$E/cond7a_gpu_wait.log
STATUS=$E/cond7a_watcher_status.txt
: > "$LOG"
attempts=0
for i in $(seq 1 120); do
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  pick=""
  pick_free=""
  # per-card free memory and count of live compute apps (used_memory > 0) via nvidia-smi-live
  applist=$("$NL" --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>/dev/null)
  while IFS=, read -r idx uuid free util; do
    idx=$(echo "$idx" | tr -d ' '); uuid=$(echo "$uuid" | tr -d ' '); free=$(echo "$free" | tr -dc '0-9')
    apps=$(printf '%s\n' "$applist" | awk -F', ' -v g="$uuid" '$1==g && $3+0>0' | wc -l)
    echo "$ts card=$idx free=${free}MiB apps=$apps util=$(echo "$util" | tr -d ' ')" >> "$LOG"
    if [ -z "$pick" ] && [ "$apps" = "0" ] && [ "${free:-0}" -ge 8192 ]; then
      pick=$uuid; pick_free=$free
    fi
  done < <("$NL" --query-gpu=index,uuid,memory.free,utilization.gpu --format=csv,noheader 2>/dev/null)
  if [ -n "$pick" ]; then
    echo "$ts candidate_gpu=$pick free=${pick_free}MiB (idle)" >> "$LOG"
    # gate pre-check before launch (runner re-checks immediately before launch)
    (cd "$B/Agent_paper_B_main_16185b0b" && "$B/envs/torch312/bin/python" r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json > /tmp/cond7a_gate.json 2>/dev/null)
    gate_ok=$(python3 - /tmp/cond7a_gate.json <<'PY'
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
)
    if [ "$gate_ok" != "yes" ]; then echo "$ts gate_not_clear; waiting" >> "$LOG"; sleep 30; continue; fi
    CPUS=$(mpstat -P ALL 1 2 2>/dev/null | awk '$2 ~ /^[0-9]+$/ {c=$2; i=$NF; if (!(c in mn) || i<mn[c]) mn[c]=i} END {for (c in mn) printf "%s %.1f\n", c, mn[c]}' | sort -k2 -nr -k1 -n | head -8 | awk 'BEGIN{s=""}{printf "%s%s", s, $1; s=","}')
    echo "$ts launching run_ar_cond7a.sh gpu=$pick cpus=$CPUS" >> "$LOG"
    attempts=$((attempts + 1))
    cd "$E" && setsid nohup bash scripts/run_ar_cond7a.sh "$pick" "$CPUS" > "$E/launch_ar_cond7a_attempt${attempts}.log" 2>&1 < /dev/null &
    # wait for the smoke (up to 90 min)
    for j in $(seq 1 180); do
      sleep 30
      EV=$(cat "$E/last_ev_ar_cond7a.txt" 2>/dev/null || true)
      if [ -n "${EV:-}" ] && [ -f "$EV/DONE" ]; then
        nrec=$(find "$EV/runs" -name run_record.json 2>/dev/null | wc -l)
        echo "$ts EV=$EV DONE=$(cat "$EV/DONE") run_records=$nrec" >> "$LOG"
        if [ "$nrec" -gt 0 ] || grep -q "DONE_PASS" "$EV/DONE" 2>/dev/null; then
          {
            echo "watcher=finished"
            echo "attempts=$attempts"
            echo "gpu=$pick"
            echo "cpus=$CPUS"
            echo "EV=$EV"
            echo "DONE=$(cat "$EV/DONE")"
            echo "run_records=$nrec"
            echo "status_file=$(cat "$EV/RESULT_STATUS.txt" 2>/dev/null | tr '\n' '|')"
          } > "$STATUS"
          exit 0
        fi
        echo "$ts pre-launch STOP (no run records); continuing to wait" >> "$LOG"
        break
      fi
    done
    [ -f "$STATUS" ] && exit 0
    sleep 30
    continue
  fi
  sleep 30
done
{
  echo "watcher=no_idle_gpu_within_60_min"
  echo "attempts=$attempts"
  echo "stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$STATUS"
exit 0
