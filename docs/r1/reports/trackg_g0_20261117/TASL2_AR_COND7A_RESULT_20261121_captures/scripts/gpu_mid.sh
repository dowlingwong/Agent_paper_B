#!/bin/bash
# GPU mid-run state snapshot for the one R1-TRACKG-AR-U2-TASL2 smoke (TASL-2).
# usage: gpu_mid.sh <evidence_dir> <gpu_uuid> <baseline_used_mib>
set -u
E=${1:?}; GPU=${2:?}; BASE=${3:?}
i=0
while [ ! -f "$E/monitor_stop" ]; do
  i=$((i + 1)); sleep 2
  used=$(nvidia-smi --query-gpu=uuid,memory.used --format=csv,noheader 2>/dev/null \
         | awk -F', ' -v g="$GPU" '$1==g {print $2}' | tr -dc '0-9')
  if [ "${used:-0}" -gt "$((BASE + 500))" ] || [ $((i * 2)) -ge 120 ]; then
    {
      echo "# gpu mid (used=${used} MiB) $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      nvidia-smi --query-gpu=index,uuid,memory.total,memory.used,memory.free,utilization.gpu --format=csv
      echo "# compute apps"; nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
    } > "$E/gpu/gpu_mid.txt" 2>&1
    break
  fi
done
