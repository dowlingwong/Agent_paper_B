#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p handback
trap 'rc=$?; printf "%s\n" "$rc" > handback/exit_status.txt; exit "$rc"' EXIT
exec > >(tee handback/preflight.log) 2>&1
export GIT_TERMINAL_PROMPT=0 PYTHONDONTWRITEBYTECODE=1
EXPECTED_NAME="${2:-NVIDIA_L40S}"
EXPECTED_NAME="${EXPECTED_NAME/_/ }"
EXPECTED_CAP="${3:-8.9}"
echo "D.3 HTCondor preflight start $(date -u +%FT%TZ) host=$(hostname -f) user=$(id -un) expected_gpu=$EXPECTED_NAME cap=$EXPECTED_CAP"
echo "=== os ==="
cat /etc/os-release
echo "=== image identity ==="
sha256sum /opt/r1/VERSIONS.txt | tee handback/VERSIONS.sha256
cat /opt/r1/VERSIONS.txt | tee handback/VERSIONS.txt
echo "=== job ad request/identity ==="
grep -Ei '^(RequestGPUs|RequestCpus|RequestMemory|RequestDisk|RequestWalltime|Machine|ContainerImage|AssignedGPUs|CUDA_VISIBLE_DEVICES|NVIDIA_VISIBLE_DEVICES) *=' "$_CONDOR_JOB_AD" || true
echo "=== gpu ==="
nvidia-smi -L | tee handback/nvidia-smi-L.txt
nvidia-smi --query-gpu=index,uuid,name,compute_cap,driver_version,memory.total,memory.free --format=csv,noheader | tee handback/gpu.csv
gpu_count=$(nvidia-smi --query-gpu=uuid --format=csv,noheader | wc -l | tr -d ' ')
echo "gpu_count=$gpu_count"
[ "$gpu_count" -eq 1 ] || { echo "STOP: expected exactly one visible GPU, got $gpu_count"; exit 2; }
gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -1 | xargs)
gpu_cap=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader | head -1 | xargs)
[ "$gpu_name" = "$EXPECTED_NAME" ] || { echo "STOP: GPU is $gpu_name, not $EXPECTED_NAME"; exit 2; }
[ "$gpu_cap" = "$EXPECTED_CAP" ] || { echo "STOP: compute capability $gpu_cap != $EXPECTED_CAP"; exit 2; }
echo "=== inputs (transferred; hashes checked in-container) ==="
sha256sum -c PREFLIGHT_INPUTS.sha256 | tee handback/input-hashes.txt
echo "=== env3 torch / CUDA ==="
PY=/opt/r1/envs/trackp/bin/python
export EXPECTED_NAME EXPECTED_CAP
"$PY" - <<'PY' | tee handback/torch.txt
import json, torch
out = {
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count(),
    "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
    "cudnn": torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else None,
}
print(json.dumps(out, indent=1, sort_keys=True))
assert out["cuda_available"] and out["device_count"] == 1
assert out["device_name"] == __import__("os").environ["EXPECTED_NAME"], out["device_name"]
assert ".".join(str(x) for x in out["capability"]) == __import__("os").environ["EXPECTED_CAP"], out["capability"]
PY
echo "D.3 HTCondor preflight end $(date -u +%FT%TZ)"
