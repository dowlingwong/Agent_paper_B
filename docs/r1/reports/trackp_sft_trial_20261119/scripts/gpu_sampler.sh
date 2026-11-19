#!/bin/bash
# GPU sampler for the TASL-2 SFT trial (ENGINEERING). Runs until <stop-file> exists or 3600 s elapse.
DB=/home/dowling/r1_engineering/sft_trial_20261119
OUT="$DB/captures/gpu_samples.csv"
STOP="$DB/captures/sampler.stop"
i=0
while [ ! -f "$STOP" ] && [ "$i" -lt 3600 ]; do
  nvidia-smi --query-gpu=timestamp,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader >> "$OUT" 2>&1
  i=$((i+1))
  sleep 1
done
