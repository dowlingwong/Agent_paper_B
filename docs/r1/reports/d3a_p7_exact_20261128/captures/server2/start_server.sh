#!/bin/bash
set -euo pipefail
B=/home/dowling/r1_tracks/work/d3p7c_20261128
mkdir -p "$B/server2"
exec 8>"$B/gpu0.lock"
flock -n 8 || { echo "gpu0.lock busy" >&2; exit 75; }
exec 9>"$B/cpus-16-31.lock"
flock -n 9 || { echo "cpus-16-31.lock busy" >&2; exit 76; }
{
  echo "started_utc=$(date -u +%FT%TZ)"
  nvidia-smi --query-gpu=uuid,index,name,memory.total,memory.used,memory.free,driver_version --format=csv,noheader
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
  echo "--- free ---"; free -b
  echo "--- df ---"; df -P "$B"
} > "$B/server2/gpu_at_start.txt"
printf "%q " /home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server \
  -m /home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8095 -ngl 999 -c 32768 -np 1 --jinja \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui > "$B/server2/server_argv.txt"
echo >> "$B/server2/server_argv.txt"
exec taskset -c 16-31 /home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server \
  -m /home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8095 -ngl 999 -c 32768 -np 1 --jinja \
  --chat-template-kwargs "{\"enable_thinking\":false}" \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui
