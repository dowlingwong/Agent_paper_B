#!/bin/bash
# One authorised clean-retry launch of the reviewed MLGym MetaMaze U2 census smoke (TASL-2, no GPU).
# Runs the preserved driver inside a delegated user systemd scope (8G, swap0), CPUs 8-11 P-cores.
set -u
MM=/home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125_RETRY
VC=/home/dowling/r1_trackg_20261125/venv_jax
UNIT="u2-metamaze-census-retry-$(date -u +%Y%m%dT%H%MZ)"
LOG=$MM/raw/smoke_launch_console.log
: > "$LOG"
{
  echo "launch_wrapper_start_utc=$(date -u +%FT%TZ)"
  echo "unit=$UNIT"
  echo "unit_memory_max=8G unit_memory_swap_max=0 delegate=yes cpus=8-11"
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-<unset>}"
  echo "PATH=$VC/bin:$PATH"
  echo "VIRTUAL_ENV=$VC"
  echo "PYTHONDONTWRITEBYTECODE=${PYTHONDONTWRITEBYTECODE-<unset>}"
  echo "python=$(command -v python3 2>/dev/null) absolute=$VC/bin/python"
  echo "runs_root=$MM/runs"
} >> "$LOG"
systemd-run --user --scope --unit="$UNIT" --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 U2_BASE="$MM" \
      PATH="$VC/bin:$PATH" VIRTUAL_ENV="$VC" \
  taskset -c 8-11 "$VC/bin/python" "$MM/run_u2_smoke.py" >> "$LOG" 2>&1
RC=$?
echo "$RC" > "$MM/raw/smoke_launch.rc"
echo "launch_wrapper_end_utc=$(date -u +%FT%TZ) launch_rc=$RC" >> "$LOG"
exit "$RC"
