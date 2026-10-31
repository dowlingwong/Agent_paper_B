#!/usr/bin/env bash
# D6 follow-up on TASL-2 (digits_mlp). ENGINEERING_ONLY / DIAGNOSTIC.
#   f1 = cold control: cache_prompt=true, one freshly started server, no prior call on it.
#   f2 = plain S0.1 serial repeat: NO cache_prompt field, one resident server.
# The server is started by the operator before this script (freshly, one only); this script asserts the
# resident-server state and records it, then runs the committed diagnostic.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/digits_mlp; PATH=$R/bin:$PATH
phase=${1:?usage: tasl2_d6.sh f1|f2}
case "$phase" in f1|f2) ;; *) echo "phase must be f1 or f2" >&2; exit 2 ;; esac

BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1 --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"

# Resident-server state (must be exactly one server, and it must be the only GPU compute process).
mapfile -t pids < <(pgrep -u "$(id -u)" -f "bin/llama-server" || true)
if [ "${#pids[@]}" -ne 1 ]; then echo "STOP: expected exactly 1 resident llama-server, found ${#pids[@]}" >&2; exit 1; fi
pid=${pids[0]}
echo "resident_server_count=1 server_pid=$pid server_start=$(ps -o lstart= -p "$pid" | sed 's/^ *//') utc=$(date -u +%FT%TZ)"
apps=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l)
echo "gpu_compute_apps=$apps"
[ "$apps" = 1 ] || { echo "STOP: expected exactly 1 GPU compute process, found $apps" >&2; exit 1; }

case "$phase" in
  f1) out=$OUT/s01_diag_f1/cache_prompt_true_cold.json; mode=true ;;
  f2) out=$OUT/s01_diag_f2/plain_single_absent.json; mode=absent ;;
esac
mkdir -p "$(dirname "$out")"

trks-diag --url http://127.0.0.1:18101/v1 --node digits_mlp --n 200 --repeats 3 --order-seed 1 \
  --proposal-schema manager_proposal/v1 --mode "$mode" --resident-server-count 1 --host-label TASL-2 \
  --gguf "$R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --llama-build 620d2225cc436ab0b001e3200e590e3b286ef9ab \
  --llama-server-bin "$R/opt/llama.cpp/build/bin/llama-server" \
  --server-args "$BASE" --out "$out"
echo "D6 $phase DONE"
