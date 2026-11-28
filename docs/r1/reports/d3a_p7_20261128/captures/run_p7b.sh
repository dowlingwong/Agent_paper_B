#!/bin/bash
set -uo pipefail
B=/home/dowling/r1_tracks/work/d3p7b_20261128
cd /home/dowling/r1_tracks/work/d3p7_20261128/repo
export PYTHONPATH=/home/dowling/r1_tracks/work/d3p7_20261128/pydeps_audit
export AR_HARNESS_ROOT=/home/dowling/r1_tracks/work/harness_9bb_20261127
export PATH="/home/dowling/r1_tracks/venv/bin:$PATH"
( while true; do
    ts=$(date -u +%FT%TZ)
    g=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free,power.draw,temperature.gpu --format=csv,noheader,nounits | tr -d " ")
    a=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr "\n" ";")
    echo "$ts,$g,$a" >> "$B/gpu_samples.csv"
    sleep 2
  done ) & SAM=$!
( for i in $(seq 1 300); do
    pid=$(pgrep -f "train.py --config config.yaml" | head -1 || true)
    if [ -n "$pid" ]; then
      echo "$(date -u +%FT%TZ) pid=$pid Cpus_allowed_list=$(awk "/Cpus_allowed_list/{print \$2}" /proc/$pid/status)" >> "$B/affinity_probe.txt"
      break
    fi
    sleep 1
  done ) &
for s in 6301 6302; do
  if [ "$s" = 6301 ]; then rid=d3a-p7-20261128-c; else rid=d3a-p7-20261128-d; fi
  /home/dowling/r1_tracks/venv/bin/python -m r1.scripts.d3_smoke_engineering run \
    --manifest "$B/manifest.json" --observed "$B/observed.json" \
    --out "$B/run-s$s" --harness-root /home/dowling/r1_tracks/work/harness_9bb_20261127 \
    --repo-root . --node openml_climate --seed "$s" \
    --arms A0 A0R A1 A2 FIXR3 EGATE LADDER --run-id "$rid" \
    > "$B/run-s$s.log" 2>&1
  echo "seed $s rc $?" >> "$B/run_p7b.status"
done
kill $SAM 2>/dev/null || true
wait $SAM 2>/dev/null || true
echo DONE >> "$B/run_p7b.status"
