#!/bin/bash
# usage: run_chain.sh <chainname> <kit> <gpu_uuid> <cpus> <attempt> <node1> [node2 ...]
# Runs the kit's per-node port_smoke_gpu.py queue on one idle GPU, one at a time, each in its own
# delegated 8 GiB-capped scope (smoke_one.sh). Run roots and logs live outside the repository.
# Stops the queue on the first failed node (a failed node is investigated, not silently skipped).
set -u
CHAIN=$1; KIT=$2; GPU=$3; CPUS=$4; ATTEMPT=$5; shift 5
E=/home/dowling/r1_engineering/iso_kit_update_20261119
LOG=$E/smoke/chain_${CHAIN}_${ATTEMPT}.log
{
  echo "# chain=$CHAIN attempt=$ATTEMPT kit=$KIT gpu=$GPU cpus=$CPUS nodes=$* start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  nvidia-smi --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv,noheader 2>&1
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>&1
} > "$LOG" 2>&1
FAILED=0
for NODE in "$@"; do
  {
    echo "=== node=$NODE start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >> "$LOG" 2>&1
  "$E/scripts/smoke_one.sh" "$KIT" "$NODE" "$GPU" "$CPUS" "$E/smoke/${ATTEMPT}/runs/$NODE" "$E/smoke/${ATTEMPT}/${NODE}.log"
  RC=$?
  {
    echo "=== node=$NODE smoke_one rc=$RC end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  } >> "$LOG" 2>&1
  if [ "$RC" -ne 0 ]; then FAILED=1; break; fi
done
{
  echo "# chain=$CHAIN attempt=$ATTEMPT end=$(date -u +%Y-%m-%dT%H:%M:%SZ) failed=$FAILED"
  nvidia-smi --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv,noheader 2>&1
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader 2>&1
} >> "$LOG" 2>&1
touch "$E/smoke/chain_${CHAIN}_${ATTEMPT}_DONE"
exit "$FAILED"
