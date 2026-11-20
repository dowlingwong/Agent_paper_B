#!/bin/bash
# B.2 EVIDENCE audit — authorized second (fresh) attempt. Exactly one launch; no retry/resume.
set -uo pipefail
A=/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z
H=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness
cd "$A/paper" || exit 90
export PATH="$H/.venv/bin:$PATH"
export AR_HARNESS_ROOT="$H"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export CUDA_VISIBLE_DEVICES=
echo "START_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "HOST=$(hostname) USER=$(id -un) CWD=$(pwd)"
echo "CMD=python -B -m r1.c3.audit evidence-run --table $A/table --paper-root $A/paper --index results/r1/pilot/C3_sweep_index_20261028T033315Z.json --classification results/r1/evidence/C3_sweep_classification_20261028.json --out results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z --workers 16 --deadline 10800 --code-commit ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74 --code-review docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md --addendum docs/r1/authorizations/c3_b2_addendum_20261117.md --scratch-root /tmp/r1_c3_audit_EVIDENCE_20261119T002306Z --required-scratch-bytes 17179869184 --ceph-reserve-files 2000"
python -B -m r1.c3.audit evidence-run \
  --table "$A/table" --paper-root "$A/paper" \
  --index results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
  --classification results/r1/evidence/C3_sweep_classification_20261028.json \
  --out results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z \
  --workers 16 --deadline 10800 \
  --code-commit ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74 \
  --code-review docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md \
  --addendum docs/r1/authorizations/c3_b2_addendum_20261117.md \
  --scratch-root /tmp/r1_c3_audit_EVIDENCE_20261119T002306Z \
  --required-scratch-bytes 17179869184 \
  --ceph-reserve-files 2000
rc=$?
echo "END_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "EXITCODE=$rc"
exit "$rc"
