#!/usr/bin/env bash
# STOP-1 diagnostic on TASL-7 (tabular_mlp): cache_prompt false (test) then true (control), one serial
# client, the pinned probe's prompts/seeds/body/schedule. ENGINEERING_ONLY / DIAGNOSTIC. Sets no k.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH
: "${SERVER_PID:?set SERVER_PID to the already-running server pid}"
: "${SCRIPT_START_EPOCH:?set SCRIPT_START_EPOCH to this launch start, epoch seconds}"

mkdir -p "$OUT/s01_diag"
if [ -e "$OUT/s01_diag/cache_prompt.json" ] && [ "${FORCE:-0}" != 1 ]; then
  echo "STOP: $OUT/s01_diag/cache_prompt.json exists (30 Oct evidence); set FORCE=1 to overwrite" >&2
  exit 2
fi
BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"

$R/bin/trks-diag --url http://127.0.0.1:18101/v1 --node tabular_mlp --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --mode both --server-pid "$SERVER_PID" --script-start-epoch "$SCRIPT_START_EPOCH" --phase-label 30oct --host-label TASL-7 \
  --gguf "$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --llama-build 620d2225cc436ab0b001e3200e590e3b286ef9ab \
  --llama-server-bin "$R/opt/llama.cpp/build/bin/llama-server" \
  --server-args "$BASE" --out "$OUT/s01_diag/cache_prompt.json"
echo "DIAG DONE"
