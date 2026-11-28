#!/bin/bash
set -euo pipefail
B=/data1/zli538/paperb_p4_20261127/p5_e0_fresh_20261128_ada
cd /data1/zli538/paperb_p4_20261127/p5_20261127_b/paper_c80f83bc
export AR_HARNESS_ROOT=/data1/zli538/paperb_p4_20261127/p5_20261127_b/harness
export HF_HOME=/data1/zli538/paperb_p4_20261127/p5_20261127_b/hf
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
for n in 1 2; do
  echo "run $n start $(date -u +%FT%TZ)" >> $B/run.status
  /data1/zli538/paperb_p4_20261127/venv/bin/python -B r1/scripts/trackp.py \
    --config $B/config/e0_config_ref.json \
    e0 --stage final --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0 \
    --gpu GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154 \
    --run-dir $B/e0e$n > $B/e0e$n.log 2>&1
  echo "run $n rc $? $(date -u +%FT%TZ)" >> $B/run.status
done
echo DONE $(date -u +%FT%TZ) >> $B/run.status
