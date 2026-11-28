#!/bin/bash
set -euo pipefail
cd /home/dowling/r1_trackp/e0_samecode_20261128
export AR_HARNESS_ROOT=/home/dowling/r1_trackp/autoresearch_harness
export HF_HOME=/home/dowling/r1_trackp/hf_cache
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
exec /home/dowling/r1_trackp/venvs/trackp-gpu/bin/python -B r1/scripts/trackp.py \
  --config /home/dowling/r1_trackp/runs/p5_e0_rep_20261128_tasl7/config/e0_config_ref_tasl7.json \
  e0 --stage final --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0 --gpu 0 \
  --run-dir /home/dowling/r1_trackp/runs/p5_e0_rep_20261128_tasl7/e0e
