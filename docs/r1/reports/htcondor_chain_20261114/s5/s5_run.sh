#!/bin/bash
# S5: NEMO2 GPU job using our SIF, transferred by HTCondor (container universe default transfer).
# I4 = CUDA availability, torch CUDA build, llama-server --version; plus the transfer/runtime record
# the author asked for (SIF transfer method, size, time as evidence for the adapter design).
# Remote NEMO2 has no /work, so every artefact is written to the job directory and transferred back.
set -uo pipefail
JOB="${_CONDOR_ClusterId:-local}.${_CONDOR_ProcId:-0}"
{ echo "job=$JOB host=$(hostname -f) date_utc=$(date -u +%FT%TZ)"; echo "iwd=$(pwd)"; } > s5_identity.txt
{ echo "== /opt/r1/VERSIONS.txt =="; cat /opt/r1/VERSIONS.txt 2>&1; } >> s5_identity.txt
{ echo "== container-job ad fields =="; grep -iE "ContainerImage|ContainerImageSource|WantContainer|Command|TransferInput|ImageSize|DiskUsage" "$_CONDOR_JOB_AD" 2>/dev/null | head -20; } >> s5_identity.txt
{ echo "== env (NVIDIA/CUDA/container) =="; env | grep -iE "NVIDIA|CUDA|APPTAINER|SINGULARITY|CONTAINER" | sort; } > s5_env.txt
{ echo "== nvidia-smi -L =="; nvidia-smi -L 2>&1; echo "rc=$?"
  echo "== nvidia-smi query =="; nvidia-smi --query-gpu=name,uuid,memory.total,driver_version,compute_cap --format=csv,noheader 2>&1; echo "rc=$?"; } > s5_nvidia.txt
{ echo "== trackp torch =="; /opt/r1/envs/trackp/bin/python - <<'PY'
import torch
print("torch", torch.__version__, "cuda_available", torch.cuda.is_available(), "torch_cuda", torch.version.cuda)
print("device_count", torch.cuda.device_count())
if torch.cuda.is_available():
    print("device0", torch.cuda.get_device_name(0))
    x = torch.rand(512, 512, device="cuda"); y = x @ x; torch.cuda.synchronize()
    print("matmul_ok", float(y[0, 0]))
else:
    print("no_cuda")
PY
  echo "rc=$?"; } > s5_torch.txt
{ echo "== llama-server =="; command -v llama-server; llama-server --version 2>&1 | head -4; echo "rc=$?"
  echo "== llama binary sha =="; sha256sum /opt/r1/llama.cpp/build/bin/llama-server 2>&1; } > s5_llama.txt
echo "S5_DONE"; exit 0
