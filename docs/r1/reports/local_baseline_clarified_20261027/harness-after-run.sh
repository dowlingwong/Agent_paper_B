#!/bin/sh
set -u
export PATH="/private/tmp/paper-b-local-20261026-venv/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export CUDA_VISIBLE_DEVICES=''
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export HF_HOME=/private/tmp/paper-b-after-harness-20261027/hf-empty
export TMPDIR=/private/tmp/paper-b-after-harness-20261027/tmp
export PYTORCH_ENABLE_MPS_FALLBACK=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PIP_NO_INDEX=1
cd /private/tmp/paper-b-after-harness-20261027/clone
python -m pytest -p pytest_timeout --continue-on-collection-errors --timeout=590 --timeout-method=signal --durations=0 -ra -v --junitxml=/private/tmp/paper-b-after-harness-20261027/junit.xml tests > /private/tmp/paper-b-after-harness-20261027/pytest.log 2>&1
rc=$?
printf '%s\n' "$rc" > /private/tmp/paper-b-after-harness-20261027/exit-code.txt
exit "$rc"
