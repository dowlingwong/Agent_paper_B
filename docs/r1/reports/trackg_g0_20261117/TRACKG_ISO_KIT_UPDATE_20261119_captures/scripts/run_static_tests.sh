#!/bin/bash
# usage: run_static_tests.sh <kit: ar|mlab|mlgym> <logfile>
# Static Tier-1 tests of a Track G port kit, CPU-masked (taskset 0-15) and GPU-masked
# (CUDA_VISIBLE_DEVICES empty), under a delegated user cgroup; nothing is written into the repo
# (no bytecode, no pytest cache).
set -u
KIT=$1; LOG=$2
BASE=/home/dowling/r1_trackg_20261117
PY=$BASE/envs/torch312/bin/python
case "$KIT" in
  ar) WT=$BASE/harness_iso_ar ;;
  mlab) WT=$BASE/harness_iso_mlab ;;
  mlgym) WT=$BASE/harness_iso_mlgym ;;
  *) echo "bad kit" >&2; exit 2 ;;
esac
cd "$WT" || exit 3
{
  echo "# kit=$KIT worktree=$WT tip=$(git rev-parse HEAD) start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  systemd-run --user --scope -p Delegate=yes -- bash -c '
    CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    cd "'"$WT"'" || exit 3
    export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=
    taskset -c 0-15 "'"$PY"'" -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke" 2>&1
    echo "PYTEST_EXIT=$?"'
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
