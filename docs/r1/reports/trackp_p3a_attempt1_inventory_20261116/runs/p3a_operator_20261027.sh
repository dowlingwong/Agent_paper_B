#!/usr/bin/env bash
set -u
cd /home/dowling/r1_trackp/Agent_paper_B || exit 1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1
/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python -m r1.scripts.trackp_p3a_guarded --root /home/dowling/r1_trackp/runs/p3a_operator_20261027
rc=$?
printf "P3A_SUPERVISOR_EXIT=%s\n" "$rc"
exit "$rc"
