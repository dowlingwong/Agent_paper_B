#!/bin/bash
# Hold the documented GPU lease (flock, NO lease-log write) and exec the proposer
# llama-server with the exact exam flags.  The lock fd survives exec, so the flock
# is held for the whole server lifetime.
set -uo pipefail
ROOT=/home/dowling/r1_engineering/tasl7_proposer_smoke_20261121
BIN=/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server
MODEL=/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf
LOCK=/home/dowling/r1_locks/gpu0.lock
LOG="$ROOT/captures/server.log"
LEASE="$ROOT/captures/lease.txt"
exec 9>>"$LOCK" || { echo "LOCK_OPEN_FAILED_UTC $(date -u +%FT%TZ)" >> "$LEASE"; exit 91; }
if ! flock -n -x 9; then echo "LEASE_BUSY_UTC $(date -u +%FT%TZ)" >> "$LEASE"; exit 90; fi
echo "LEASE_ACQUIRED_UTC=$(date -u +%FT%TZ) $(date -Is) pid=$$" >> "$LEASE"
echo "CGROUP_AT_LEASE=$(cat /proc/self/cgroup)" >> "$LEASE"
export CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES" >> "$LEASE"
echo "SERVE_EXEC_UTC=$(date -u +%FT%TZ)" >> "$LEASE"
exec "$BIN" -m "$MODEL" -a gemma4_31b \
  -c 32768 -ngl 999 -np 1 --jinja \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --host 100.106.74.51 --port 8095 --no-webui -lv 4 \
  >> "$LOG" 2>&1
