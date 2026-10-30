#!/usr/bin/env bash
# Phase 1 — S0.1 LLM determinism, latency and CPU census on TASL-7 (node tabular_mlp).
# Runbook rev 3.2 Phase 1. ENGINEERING_ONLY. Probes are the command of their own tmux
# session via trks-run, so an ssh drop does not kill them; serial must exit before concurrent.
set -euo pipefail; R=/home/dowling/r1_tracks; OUT=$R/out/tabular_mlp; WORK=$R/scratch/tabular_mlp; IN=$OUT/inputs; PATH=$R/bin:$PATH

mkdir -p "$OUT/s01" "$IN"
BASE="$R/opt/llama.cpp/build/bin/llama-server -m $R/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf --alias r1-manager --host 127.0.0.1"
S1="$BASE --port 18101 -ngl 999 -c 8192 --parallel 1 --verbose"
S2="$BASE --port 18102 -ngl 999 -c 8192 --parallel 1 --verbose"

rc_of() { sed -n 's/.*rc=//p' "$R/logs/$1.exit" 2>/dev/null | tail -1; }
wait_session() { while tmux has-session -t "$1" 2>/dev/null; do sleep 15; done; }

trks-run trks_s01_serial - probe --url http://127.0.0.1:18101/v1 --mode serial --n 200 --repeats 3 \
  --order-seed 1 --proposal-schema manager_proposal/v1 --node tabular_mlp --server-args "$S1" \
  --out "$OUT/s01/serial.json"
wait_session trks_s01_serial
echo "serial rc=$(rc_of trks_s01_serial)"
[ "$(rc_of trks_s01_serial)" = 0 ] || { echo "serial probe failed"; exit 1; }

trks-run trks_s01_conc - probe --url http://127.0.0.1:18101/v1 --url http://127.0.0.1:18102/v1 --mode concurrent \
  --clients-per-url 2 --n 200 --repeats 3 --order-seed 2 --proposal-schema manager_proposal/v1 --node tabular_mlp \
  --server-args "$S1 | $S2" --out "$OUT/s01/concurrent.json"
wait_session trks_s01_conc
echo "concurrent rc=$(rc_of trks_s01_conc)"
[ "$(rc_of trks_s01_conc)" = 0 ] || { echo "concurrent probe failed"; exit 1; }
echo "S01 DONE"
