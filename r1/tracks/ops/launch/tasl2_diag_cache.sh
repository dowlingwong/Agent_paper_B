#!/usr/bin/env bash
# STOP-1 diagnostic on TASL-2 (digits_mlp): cache_prompt false (test) then true (control), one serial
# client, the pinned probe's prompts/seeds/body/schedule. ENGINEERING_ONLY / DIAGNOSTIC. Sets no k.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; WORK=$R/scratch/digits_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH

mkdir -p "$OUT/s01_diag"
BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"

$R/bin/trks-diag --url http://127.0.0.1:18101/v1 --node digits_mlp --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --mode both --host-label TASL-2 \
  --gguf "$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --llama-build 620d2225cc436ab0b001e3200e590e3b286ef9ab \
  --llama-server-bin "$R/opt/llama.cpp/build/bin/llama-server" \
  --server-args "$BASE" --out "$OUT/s01_diag/cache_prompt.json"
echo "DIAG DONE"
