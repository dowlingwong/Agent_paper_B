#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p handback
trap 'rc=$?; printf "%s\n" "$rc" > handback/exit_status.txt; exit "$rc"' EXIT
exec > >(tee handback/job.log) 2>&1
export GIT_TERMINAL_PROMPT=0 PYTHONDONTWRITEBYTECODE=1
export HF_HOME="$PWD/hf_cache" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
printf '%s %s %s\n' "$1" "$(hostname -f)" "$(date -u +%FT%TZ)"
cat /opt/r1/VERSIONS.txt
/sbin/ldconfig -p | grep -i libcuda || true
PY=/opt/r1/envs/trackp/bin/python
GPU_UUID=$("$PY" - <<'PY'
import torch
assert torch.__version__ == "2.6.0+cu124"
assert torch.cuda.device_count() == 1
assert torch.cuda.get_device_name(0) == "NVIDIA H200"
assert torch.cuda.get_device_capability(0) == (9, 0)
raw_uuid = str(torch.cuda.get_device_properties(0).uuid)
print(raw_uuid if raw_uuid.startswith("GPU-") else "GPU-" + raw_uuid)
PY
)
if [[ ! "$GPU_UUID" =~ ^GPU-[0-9a-fA-F-]{36}$ ]]; then
  printf 'STOP: invalid allocated GPU UUID %s\n' "$GPU_UUID"
  exit 2
fi
export TRACKP_PROBE_GPU_UUID="$GPU_UUID"
test -r "${_CONDOR_JOB_AD:?must run as an HTCondor job}"
grep -Ei '^(RequestGPUs|AssignedGPUs|MachineAttrCloudSite0) *= *' "$_CONDOR_JOB_AD" || true
/usr/bin/nvidia-smi --id="$GPU_UUID" --query-gpu=name,uuid,driver_version --format=csv,noheader
mkdir -p scoped_bin
install -m 0755 nvidia-smi-scoped scoped_bin/nvidia-smi
export PATH="$PWD/scoped_bin:$PATH"
out=$(nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader)
if [[ -n "$out" ]]; then printf 'STOP: assigned GPU has an existing compute process\n'; exit 2; fi
clone_pin() {
  local url="$1" commit="$2" path="$3"
  git init -q "$path"
  git -C "$path" remote add origin "$url"
  git -C "$path" fetch -q --depth=1 origin "$commit"
  git -C "$path" checkout -q --detach "$commit"
  test "$(git -C "$path" rev-parse HEAD)" = "$commit"
  test -z "$(git -C "$path" status --porcelain)"
}
MODE=$(cat probe_mode.txt)
PAPER=https://github.com/dowlingwong/Agent_paper_B.git
case "$MODE" in
  smoke)
    clone_pin "$PAPER" 8662e35991659f7a661fb7ed6be4980791d302f3 paper
    cmp registry.yaml paper/r1/c3/train/registry.yaml
    "$PY" -B stage_models.py qwen3.5-0.8b-base | tee handback/model_sha256.txt
    "$PY" -B paper/r1/scripts/trackp_gpu_smoke.py \
      --model "$PWD/models/qwen3.5-0.8b-base" --out "$PWD/handback/gpu_smoke.json" \
      --lock "$PWD/h200_probe.lock" --lease-log "$PWD/handback/lease.jsonl"
    "$PY" -B - <<'CHECK'
import json
from pathlib import Path

report = json.loads(Path("handback/gpu_smoke.json").read_text())
ref = json.loads(Path("tasl7_smoke_reference.json").read_text())
assert report.get("pass") is True and report.get("device") == "NVIDIA H200"
assert "kernel_import_error" not in report
assert report.get("kernels_bound") == ref["kernels_bound"], "STOP: kernel bindings differ from TASL-7"
assert set(report["checks"]) == set(ref["checks"])
assert all(result.get("pass") is True for result in report["checks"].values())
CHECK
    ;;
  e0)
    clone_pin "$PAPER" 8e13e77cd49532c7ac2e78ad8e5c1ee45401b286 paper
    clone_pin https://github.com/dowlingwong/autoresearch_harness.git \
      897d83c8efa364ec2fdd37288241cc42e01d7274 harness
    cmp registry.yaml paper/r1/c3/train/registry.yaml
    "$PY" -B stage_models.py qwen3.5-0.8b-base kev-0.8b | tee handback/model_sha256.txt
    "$PY" -B configure_e0.py
    export AR_HARNESS_ROOT="$PWD/harness" PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    STAGE="$PWD"
    (cd paper && "$PY" -B r1/scripts/trackp.py --config "$STAGE/handback/e0_config.json" \
      e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001 --seed 0 \
      --run-dir "$STAGE/e0")
    mkdir -p handback/head_fit handback/lora
    cp e0/report.json e0/manifest.json e0/pred_test_head_fit.npy e0/pred_test_lora.npy handback/
    cp e0/head_fit/curve.jsonl handback/head_fit/
    cp e0/lora/{metrics.jsonl,best.json} handback/lora/
    "$PY" -B - <<'PY'
import json
with open("reference_manifest.json") as fh:
    reference = json.load(fh)
with open("handback/manifest.json") as fh:
    run = json.load(fh)
assert run["data_manifest_sha256"] == reference["data_manifest_sha256"], "STOP: E0 dataset differs"
PY
    printf '%s\n' 'comparator portal = TASL-7 reference' 'comparator tasl7 = H200 candidate' > handback/comparison_identity.txt
    "$PY" -B compare.py reference.json handback/report.json > handback/comparison.json
    ;;
  *) printf 'STOP: unknown Track P probe mode %s\n' "$MODE" >&2; exit 2 ;;
esac
