#!/bin/bash
set -euo pipefail
exec 8>/home/dowling/r1_locks/gpu0.lock
flock -n 8
exec 9>/home/dowling/r1_locks/cpus-16-31.lock
flock -n 9
exec taskset -c 16-31 /home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server \
  -m /home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8095 -ngl 999 -c 8192 -np 1 --jinja \
  --chat-template-kwargs "{\"enable_thinking\":false}" --no-webui
