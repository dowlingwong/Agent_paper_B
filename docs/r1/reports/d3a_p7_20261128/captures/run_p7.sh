#!/bin/bash
set -uo pipefail
ROOT=/home/dowling/r1_tracks/work/d3p7_20261128
cd "$ROOT/repo"
export PYTHONPATH="$ROOT/pydeps_audit"
export AR_HARNESS_ROOT=/home/dowling/r1_tracks/work/harness_9bb_20261127
export PATH="/home/dowling/r1_tracks/venv/bin:$PATH"
( while true; do
    ts=$(date -u +%FT%TZ)
    g=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free,power.draw,temperature.gpu --format=csv,noheader,nounits | tr -d " ")
    a=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr "\n" ";")
    echo "$ts,$g,$a" >> "$ROOT/gpu_samples.csv"
    sleep 2
  done ) & SAM=$!
for s in 6301 6302; do
  if [ "$s" = 6301 ]; then rid=d3a-p7-20261128-a; else rid=d3a-p7-20261128-b; fi
  /home/dowling/r1_tracks/venv/bin/python -m r1.scripts.d3_smoke_engineering run \
    --manifest "$ROOT/manifest.json" --observed "$ROOT/observed.json" \
    --out "$ROOT/run-s$s" --harness-root /home/dowling/r1_tracks/work/harness_9bb_20261127 \
    --repo-root . --node openml_climate --seed "$s" \
    --arms A0 A0R A1 A2 FIXR3 EGATE LADDER --run-id "$rid" \
    > "$ROOT/run-s$s.log" 2>&1
  echo "seed $s rc $?" >> "$ROOT/run_p7.status"
done
kill $SAM 2>/dev/null || true
wait $SAM 2>/dev/null || true
echo DONE >> "$ROOT/run_p7.status"
