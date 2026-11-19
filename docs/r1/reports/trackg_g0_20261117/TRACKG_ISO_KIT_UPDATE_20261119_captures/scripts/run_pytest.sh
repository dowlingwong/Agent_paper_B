#!/bin/bash
# usage: run_pytest.sh <kit: ar|mlab|mlgym> <logfile> <mode: kit|iso|full>
#   kit  = tests/trackg -k "not smoke", minus the core isolation file (pre-update baseline of the port-kit
#          tests; the old core's isolation file fails/hangs on Ada and is captured separately by mode=iso)
#   iso  = tests/trackg/test_trackg_isolation.py only, under `timeout` (old core hangs on Ada)
#   full = tests/trackg -k "not smoke" as the task specifies (post-update run)
# CPU-masked (taskset 0-15), GPU-masked (CUDA_VISIBLE_DEVICES empty), delegated cgroup, no repo writes.
set -u
KIT=$1; LOG=$2; MODE=$3
BASE=/home/dowling/r1_trackg_20261117
PY=$BASE/envs/torch312/bin/python
case "$KIT" in
  ar) WT=$BASE/harness_iso_ar ;;
  mlab) WT=$BASE/harness_iso_mlab ;;
  mlgym) WT=$BASE/harness_iso_mlgym ;;
  *) echo "bad kit" >&2; exit 2 ;;
esac
cd "$WT" || exit 3
case "$MODE" in
  kit)  CMD="cd '$WT' && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= && taskset -c 0-15 '$PY' -m pytest tests/trackg -q -p no:cacheprovider -k 'not smoke' --ignore=tests/trackg/test_trackg_isolation.py" ;;
  iso)  CMD="cd '$WT' && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= && timeout 300 taskset -c 0-15 '$PY' -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider" ;;
  full) CMD="cd '$WT' && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= && taskset -c 0-15 '$PY' -m pytest tests/trackg -q -p no:cacheprovider -k 'not smoke'" ;;
  *) echo "bad mode" >&2; exit 2 ;;
esac
{
  echo "# kit=$KIT mode=$MODE worktree=$WT tip=$(git rev-parse HEAD) start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  systemd-run --user --scope -p Delegate=yes -- bash -c "CG=\$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup\$CG; $CMD; echo PYTEST_EXIT=\$?" 2>&1
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
