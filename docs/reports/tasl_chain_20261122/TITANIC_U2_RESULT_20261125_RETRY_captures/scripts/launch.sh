#!/bin/bash
# U2 census CPU smoke launcher for the reviewed MLGym Titanic kit (TASL-2, no GPU, no GPU lease).
# Creates the delegated user systemd scope and runs scope_inner.sh inside it.  One smoke only:
# it refuses when the runs root already exists.  The pinned env's bin is put first on PATH (the
# reviewed campaign engine starts its runs as `python3` from PATH) and the absolute pinned
# interpreter is used for the driver.
set -u
BASE=${U2_BASE:-/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125}
CPUS=${U2_CPUS:-16-31}
RAW=$BASE/raw
UNIT="u2-titanic-census-20261125T${1:-0000Z}"
ENVROOT=/home/dowling/r1_tracks/t1_tasl/envs/torch312
export PATH="$ENVROOT/bin:$PATH"
export VIRTUAL_ENV="$ENVROOT"
export PYTHONDONTWRITEBYTECODE=1
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/titanic_20261125/data

{
  echo "launch_start_utc=$(date -u +%FT%TZ)"
  echo "unit=$UNIT"
  echo "cwd=$(pwd)"
  echo "PATH=$PATH"
  echo "VIRTUAL_ENV=$VIRTUAL_ENV"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-<unset>}"
  echo "PYTHONDONTWRITEBYTECODE=$PYTHONDONTWRITEBYTECODE"
  echo "AR_TRACKG_DATA_ROOT=$AR_TRACKG_DATA_ROOT"
  echo "python3=$(command -v python3)"
  echo "python3_resolved=$(readlink -f "$(command -v python3)" 2>/dev/null)"
} > "$RAW/launch_env.txt"

if [ -e "$BASE/runs" ]; then
  echo "REFUSE_ONE_SMOKE runs root already exists: $BASE/runs" >> "$RAW/launch_env.txt"
  echo 3 > "$BASE/launch.rc"
  exit 3
fi

echo "=== systemd-run --user --scope --unit=$UNIT -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 ===" \
  >> "$RAW/launch_env.txt"
systemd-run --user --scope --unit="$UNIT" --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env PATH="$PATH" VIRTUAL_ENV="$VIRTUAL_ENV" CUDA_VISIBLE_DEVICES= \
      PYTHONDONTWRITEBYTECODE=1 AR_TRACKG_DATA_ROOT="$AR_TRACKG_DATA_ROOT" \
      U2_BASE="$BASE" U2_CPUS="$CPUS" \
  taskset -c "$CPUS" bash "$BASE/scripts/scope_inner.sh" >> "$RAW/launch.out" 2>&1
RC=$?
echo "$RC" > "$BASE/launch.rc"
{
  echo "launch_rc=$RC"
  echo "launch_end_utc=$(date -u +%FT%TZ)"
} >> "$RAW/launch_env.txt"
exit "$RC"
