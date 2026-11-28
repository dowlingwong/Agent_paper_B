#!/bin/bash
set -euo pipefail
B=/home/dowling/r1_trackp/runs/p5_e0_fresh_20261128_tasl7
cd /home/dowling/r1_trackp/e0_samecode_20261128
export AR_HARNESS_ROOT=/home/dowling/r1_trackp/autoresearch_harness
export HF_HOME=/home/dowling/r1_trackp/hf_cache
export TRANSFORMERS_OFFLINE=1
export PYTHONDONTWRITEBYTECODE=1
for n in 1 2; do
  echo "run $n start $(date -u +%FT%TZ)" >> $B/run.status
  /home/dowling/r1_trackp/venvs/trackp-gpu/bin/python -B r1/scripts/trackp.py \
    --config $B/config/e0_config_ref_tasl7.json \
    e0 --stage final --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0 --gpu 0 \
    --run-dir $B/e0e$n > $B/e0e$n.log 2>&1
  echo "run $n rc $? $(date -u +%FT%TZ)" >> $B/run.status
done
echo DONE $(date -u +%FT%TZ) >> $B/run.status
