#!/bin/bash
set -euo pipefail
cd /data1/zli538/paperb_p4_20261127/p5_20261127_b/paper_c80f83bc
export AR_HARNESS_ROOT=/data1/zli538/paperb_p4_20261127/p5_20261127_b/harness
export HF_HOME=/data1/zli538/paperb_p4_20261127/p5_20261127_b/hf
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
exec /data1/zli538/paperb_p4_20261127/venv/bin/python -B r1/scripts/trackp.py \
  --config /data1/zli538/paperb_p4_20261127/p5_e0_rep_20261128_ada/config/e0_config_ref.json \
  e0 --stage final --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0 \
  --gpu GPU-9be33fd1-8eeb-497d-772a-87362d6720be \
  --run-dir /data1/zli538/paperb_p4_20261127/p5_e0_rep_20261128_ada/e0e
