#!/bin/bash
# SIGTERM the smoke server, wait for exit, verify the GPU is idle and the flock is free.
set -uo pipefail
ROOT=/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121
CAP="$ROOT/captures"
PID="$1"
OUT="$CAP/stop.txt"
{
  echo "STOP_REQUEST_UTC=$(date -u +%FT%TZ) $(date -Is) pid=$PID"
  echo "cmdline: $(tr '\0' ' ' < /proc/$PID/cmdline 2>&1)"
  echo "cgroup: $(cat /proc/$PID/cgroup 2>&1)"
  kill -TERM "$PID" 2>&1 && echo "SIGTERM_SENT=1"
  for i in $(seq 1 120); do
    if ! kill -0 "$PID" 2>/dev/null; then echo "EXITED_AFTER_SECONDS=$(echo "scale=2; $i*0.5" | bc)"; break; fi
    sleep 0.5
  done
  if kill -0 "$PID" 2>/dev/null; then echo "STILL_ALIVE_AFTER_60S=1"; fi
  echo "STOP_VERIFY_UTC=$(date -u +%FT%TZ) $(date -Is)"
  echo "== pgrep llama-server =="; pgrep -af "llama-server" | grep -v pgrep || echo NONE
  echo "== port 8095 =="; ss -ltn 2>/dev/null | grep -E ":8095 " || echo FREE
  echo "== flock probe gpu0.lock =="; flock -n /home/dowling/r1_locks/gpu0.lock -c "echo LOCK_FREE" 2>&1 || echo LOCK_BUSY
  echo "== nvidia-smi compute apps =="; nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
  echo "== nvidia-smi gpu =="; nvidia-smi --query-gpu=index,uuid,memory.used,utilization.gpu --format=csv
  echo "== scopes =="; systemctl --user list-units --type=scope --all --no-pager 2>&1 | grep -E "smoke|run-" || echo NONE
} > "$OUT" 2>&1
cat "$OUT"
