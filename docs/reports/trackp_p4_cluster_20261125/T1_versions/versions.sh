#!/bin/bash
set -uo pipefail
sha256sum /opt/r1/VERSIONS.txt && cat /opt/r1/VERSIONS.txt || exit 2
{
  echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES-unset}"
  echo "NVIDIA_VISIBLE_DEVICES=${NVIDIA_VISIBLE_DEVICES-unset}"
  echo "== p4_lib.gpu_identity query =="
  nvidia-smi --query-gpu=name,uuid,driver_version,memory.total,compute_cap --format=csv,noheader; echo "rc=$?"
  echo "== run.foreign_compute_processes query =="
  nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader; echo "rc=$?"
} > gpu_visibility.txt 2>&1
exit 0
