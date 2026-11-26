#!/usr/bin/env bash
# TASL-7 host-equivalence run (docs/r1/reports/tasl7_equivalence_20261026/PREDECLARATION.md). AI-assisted (Claude).
set -euo pipefail
cd /home/dowling/r1_trackp/equiv_8e13e77
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True HF_HUB_OFFLINE=1 AR_HARNESS_ROOT=/home/dowling/r1_trackp/autoresearch_harness
date -u +%FT%TZ
/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --run-dir /home/dowling/r1_trackp/runs/tasl7_equiv_20261026/kev-0.8b/fresh_soft_lr0.0001
date -u +%FT%TZ
