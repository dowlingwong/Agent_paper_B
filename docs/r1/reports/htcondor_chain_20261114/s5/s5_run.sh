#!/bin/bash
# S5: NEMO2 GPU job using the ghcr.io GPU image (container universe -> Singularity pull).
# I4 = CUDA / torch / llama-server --version; records the image pull evidence the author asked for
# (image reference from the job ad, pull time split from submit->execute wait, image size, EP-side
# sandbox evidence), plus /dev/nvidia* and the driver version. Reviewed unit (S5 review M1-M3).
# Remote NEMO2 has no /work, so every artefact is written to the job directory and transferred back.
set -uo pipefail
JOB="${1:-local.0}"
PRE="s5_identity.txt s5_env.txt s5_nvidia.txt s5_torch.txt s5_llama.txt s5_pull.txt s5_PASSFAIL.txt"
for f in $PRE; do printf 'not written\n' > "$f"; done
FAIL=0
{
  echo "job=$JOB host=$(hostname -f) date_utc=$(date -u +%FT%TZ) iwd=$(pwd)"
  echo "== /opt/r1/VERSIONS.txt =="; cat /opt/r1/VERSIONS.txt 2>&1
  echo "== job ad container fields =="
  if [ -r "${_CONDOR_JOB_AD:-}" ]; then
    grep -aiE "^(ContainerImage|ContainerImageSource|WantContainer|ImageSize|DiskUsage|RequestDisk|Cmd|TransferInput)" "$_CONDOR_JOB_AD" 2>/dev/null | head -20
  else
    echo "job ad not readable"
  fi
  echo "== container runtime env =="
  env | grep -aiE "APPTAINER|SINGULARITY|CONTAINER" | sort
  echo "== scratch dirs =="
  echo "_CONDOR_SCRATCH_DIR=${_CONDOR_SCRATCH_DIR:-unset}"
} > s5_identity.txt 2>&1
{ echo "== nvidia-smi -L =="; nvidia-smi -L 2>&1; echo "rc=$?"
  echo "== nvidia-smi query =="; nvidia-smi --query-gpu=name,uuid,memory.total,driver_version,compute_cap --format=csv,noheader 2>&1; echo "rc=$?"
  echo "== /proc/driver/nvidia/version =="; cat /proc/driver/nvidia/version 2>&1 | head -3
  echo "== /dev/nvidia devices =="; ls -l /dev/nvidia* 2>&1
  echo "== libcuda =="; ls -l /usr/lib64/libcuda.so* /usr/local/cuda/lib64/libcuda.so* 2>&1 | head -5; } > s5_nvidia.txt 2>&1
{ echo "== trackp torch =="; /opt/r1/envs/trackp/bin/python -c "
import torch
print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'torch_cuda', torch.version.cuda)
print('device_count', torch.cuda.device_count())
if torch.cuda.is_available():
    print('device0', torch.cuda.get_device_name(0))
    x = torch.rand(512, 512, device='cuda'); y = x @ x; torch.cuda.synchronize()
    print('matmul_ok', float(y[0, 0]))
else:
    print('no_cuda')
"
  echo "rc=$?"; } > s5_torch.txt 2>&1
{ echo "== llama-server =="; command -v llama-server; llama-server --version 2>&1 | head -4; echo "rc=$?"
  echo "== llama binary sha =="; sha256sum /opt/r1/llama/bin/llama-server 2>&1; } > s5_llama.txt 2>&1
{ echo "== EP-side image/sandbox evidence (what the pull left in the job dir) =="
  pwd; df -h . 2>&1 | tail -1; du -sh . 2>&1 | tail -1
  ls -la . 2>&1 | head -10
  echo "== any image/sif artefacts visible =="
  find / -xdev -maxdepth 3 \( -name '*.sif' -o -name 'r1-htc*' \) -printf '%p %s\n' 2>/dev/null | head -10
  echo "== root filesystem (image) top level =="; ls -la / 2>&1 | head -20
  echo "== image identity markers =="; ls -la /.singularity.d 2>/dev/null | head -5; cat /opt/r1/VERSIONS.txt 2>/dev/null | head -3
} > s5_pull.txt 2>&1
grep -qi "GPU" s5_nvidia.txt && grep -q "matmul_ok" s5_torch.txt && grep -q "llama-server" s5_llama.txt || FAIL=1
echo "S5_$([ "$FAIL" -eq 0 ] && echo PASS || echo FAIL)" > s5_PASSFAIL.txt
cat s5_PASSFAIL.txt; echo "S5_DONE fail=$FAIL"
exit "$FAIL"
