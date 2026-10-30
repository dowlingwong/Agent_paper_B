#!/usr/bin/env bash
set -uo pipefail
R=/home/dowling/r1_tracks
. $R/venv/bin/activate
export AR_HARNESS_ROOT=$R/work/autoresearch_harness OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd $R/work/Agent_paper_B
echo "=== PAPER TESTS (python -m pytest) ==="
python -m pytest -q -p no:cacheprovider r1/tests/test_tracks_*.py; echo "PAPER_RC=$?"
echo "=== HARNESS TESTS ==="
cd $R/work/autoresearch_harness
python -m pytest -q -p no:cacheprovider tests/stage2/test_r1_track_s_arms.py; echo "HARNESS_RC=$?"
echo "=== TESTS DONE ==="
