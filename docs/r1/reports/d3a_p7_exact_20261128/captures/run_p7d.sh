#!/bin/bash
set -uo pipefail
B=/home/dowling/r1_tracks/work/d3p7c_20261128
cd "$B/repo"
export PYTHONPATH=/home/dowling/r1_tracks/work/d3p7_20261128/pydeps_audit
export AR_HARNESS_ROOT=/home/dowling/r1_tracks/work/harness_9bb_20261127
export PATH="/home/dowling/r1_tracks/venv/bin:$PATH"
echo "run_start_utc=$(date -u +%FT%TZ)" > "$B/run.status"
( while true; do
    ts=$(date -u +%FT%TZ)
    g=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free,power.draw,temperature.gpu --format=csv,noheader,nounits | tr -d " ")
    a=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader | tr "\n" ";")
    echo "$ts,$g,$a" >> "$B/gpu_samples.csv"
    sleep 2
  done ) & SAM=$!
( while true; do
    ts=$(date -u +%FT%TZ)
    m=$(free -b | awk "/^Mem:/{print \$2\",\"\$3\",\"\$4\",\"\$6\",\"\$7}")
    echo "$ts,$m" >> "$B/host_mem_samples.csv"
    sleep 2
  done ) & MEMMON=$!
( while true; do
    ts=$(date -u +%FT%TZ)
    r1=$(du -sb "$B/run-s6301" 2>/dev/null | cut -f1); r2=$(du -sb "$B/run-s6302" 2>/dev/null | cut -f1)
    dc=$(du -sb "$B/data_cache" 2>/dev/null | cut -f1)
    echo "$ts,${r1:-0},${r2:-0},${dc:-0}" >> "$B/scratch_samples.csv"
    sleep 10
  done ) & DISKMON=$!
( for i in $(seq 1 2400); do
    pid=$(pgrep -f "train.py --config config.yaml" | head -1 || true)
    if [ -n "$pid" ]; then
      echo "$(date -u +%FT%TZ) pid=$pid Cpus_allowed_list=$(awk "/Cpus_allowed_list/{print \$2}" /proc/$pid/status)" >> "$B/affinity_probe.txt"
      break
    fi
    sleep 1
  done ) &
for s in 6301 6302; do
  if [ "$s" = 6301 ]; then rid=d3a-p7-exact-20261128-c; else rid=d3a-p7-exact-20261128-d; fi
  /home/dowling/r1_tracks/venv/bin/python -m r1.scripts.d3_smoke_engineering run \
    --manifest "$B/manifest.json" --observed "$B/observed.json" \
    --out "$B/run-s$s" --harness-root /home/dowling/r1_tracks/work/harness_9bb_20261127 \
    --repo-root . --node openml_climate --seed "$s" \
    --arms A0 A0R A1 A2 FIXR3 EGATE LADDER --run-id "$rid" \
    > "$B/run-s$s.log" 2>&1
  echo "seed $s rc $? $(date -u +%FT%TZ)" >> "$B/run.status"
done
kill $SAM $MEMMON $DISKMON 2>/dev/null || true
wait $SAM $MEMMON $DISKMON 2>/dev/null || true
echo "DONE $(date -u +%FT%TZ)" >> "$B/run.status"
