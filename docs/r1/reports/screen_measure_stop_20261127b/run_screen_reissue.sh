#!/bin/bash
set -euo pipefail
cd /work/dwong/screen_measure_20261127/paper
export PATH=/ceph/dwong/r1_prepare_20261025/venv/bin:$PATH
export AR_HARNESS_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B -m r1.noise.screen_measure run --evidence --out results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1155Z --workers 16 --tmp /tmp/r1_smeas_EVIDENCE_20261127T1155Z --paper-root "$PWD" --note docs/r1/authorizations/screen_measure_20261127_reissue.md --code-commit e153df24ee3435bbe0b2fa994297b15250550c30 --code-review docs/r1/reviews/SCREEN_MEASURE_SIGNATURE_REVIEW_20261127.md --data-cache /work/dwong/screen_prep_20261126/data_cache_ENG_20261127T0417Z
