#!/bin/bash
# I3: GPU image + pinned GGUF from HuggingFace. Downloads the model into the job scratch, verifies
# the pinned sha256, starts llama-server, checks it serves, records timings, then stops it.
# Author 14 Nov (option e): HF fixed revision 13fb94bfda8c8cf22497dc57b78f391a9acb426a,
# file qwen2.5-coder-7b-instruct-q4_k_m.gguf, expected sha256 509287f7...4d3c.
set -uo pipefail
JOB="${1:-local.0}"
FAIL=0
START_UTC=$(date -u +%FT%TZ)
URL="https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/13fb94bfda8c8cf22497dc57b78f391a9acb426a/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
EXPECT_SHA=509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c
EXPECT_BYTES=4683073536
pre="i3_identity.txt i3_download.txt i3_download.log i3_sha.txt i3_cudalibs.txt i3_server.txt i3_PASSFAIL.txt"
for f in $pre; do printf 'not written\n' > "$f"; done
{
  echo "job=$JOB host=$(hostname -f) start_utc=$START_UTC iwd=$(pwd)"
  echo "== image VERSIONS =="; cat /opt/r1/VERSIONS.txt 2>&1
  echo "== driver =="; cat /proc/driver/nvidia/version 2>&1 | head -2
  echo "== nvidia devices =="; ls -l /dev/nvidia* 2>&1 | head -6
  echo "== job ad container/gpu =="
  [ -r "${_CONDOR_JOB_AD:-}" ] && grep -aiE "^(ContainerImage|ContainerImageSource|WantContainer|DockerImage|RequestGPUs|RemoteJob|ImageSize|DiskUsage|RequestDisk)" "$_CONDOR_JOB_AD" 2>/dev/null | head -12
  echo "== torch =="; /opt/r1/envs/trackp/bin/python -c "import torch; print('torch',torch.__version__,'cuda',torch.cuda.is_available(),torch.version.cuda,torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')" 2>&1
  echo "== disk/env =="; df -h . | tail -1; df -k . | awk 'NR==2{print "avail_kb="$4}'; env | grep -aiE "APPTAINER_CONTAINER|APPTAINER_CACHEDIR|CUDA_VISIBLE|NVIDIA_VISIBLE" | sort
} > i3_identity.txt 2>&1
# ---- download (timed) ---------------------------------------------------------
AVAIL_KB=$(df -k . | awk 'NR==2{print $4}')
[ "${AVAIL_KB:-0}" -ge 12000000 ] || { echo "PREFLIGHT_FAIL avail_kb=$AVAIL_KB < 12,000,000"; FAIL=1; }
DL_START=$(date +%s)
curl -L --fail --retry 3 --retry-delay 5 --max-time 1200 -o model.gguf "$URL" > i3_download.log 2>&1
DL_RC=$?
DL_END=$(date +%s)
BYTES=$(stat -c %s model.gguf 2>/dev/null || echo 0)
{
  echo "url=$URL"
  echo "download_rc=$DL_RC download_s=$((DL_END-DL_START)) bytes=$BYTES expected_bytes=$EXPECT_BYTES"
  tail -3 i3_download.log 2>/dev/null
} > i3_download.txt 2>&1
[ "$DL_RC" -eq 0 ] && [ "$BYTES" -eq "$EXPECT_BYTES" ] || FAIL=1
# ---- sha256 verify -----------------------------------------------------------
GOT_SHA=$(sha256sum model.gguf 2>/dev/null | awk '{print $1}')
{ echo "sha256=$GOT_SHA"; echo "expected=$EXPECT_SHA"; echo "match=$([ "$GOT_SHA" = "$EXPECT_SHA" ] && echo yes || echo no)"; } > i3_sha.txt 2>&1
[ "$GOT_SHA" = "$EXPECT_SHA" ] || FAIL=1
# ---- llama-server: start, health, stop --------------------------------------
{
  echo "== driver libs (llama needs libcuda.so.1; torch finds it) =="
  echo "LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-unset}"
  ldconfig -p 2>/dev/null | grep -iE "libcuda\.so|libcudart" | head -6
  find / -xdev -maxdepth 4 \( -name 'libcuda.so*' -o -name 'libnvidia*' \) -printf '%p %s\n' 2>/dev/null | head -10
  ls -la /usr/local/nvidia/lib64 2>/dev/null | head -6
  echo "== llama backend libs =="; ls /opt/r1/llama/bin/libggml-cuda.so* 2>/dev/null
  echo "== llama-server ldd (cuda/not found) =="; ldd /opt/r1/llama/bin/llama-server 2>&1 | grep -iE "cuda|not found" | head -8
  ldd /opt/r1/llama/bin/libggml-cuda.so 2>&1 | grep -iE "cuda|not found" | head -6
} > i3_cudalibs.txt 2>&1
if [ "$FAIL" -eq 0 ]; then
  SRV_START=$(date +%s)
  /opt/r1/llama/bin/llama-server -m model.gguf --host 127.0.0.1 --port 8091 -ngl 99 -c 2048 -lv 4 > llama-server.log 2>&1 &
  SRV_PID=$!
  READY=0
  for _ in $(seq 1 120); do
    if curl -fsS --max-time 2 http://127.0.0.1:8091/health >/dev/null 2>&1; then READY=1; break; fi
    kill -0 "$SRV_PID" 2>/dev/null || break
    sleep 2
  done
  SRV_READY_S=$(( $(date +%s) - SRV_START ))
  HEALTH=$(curl -fsS --max-time 5 http://127.0.0.1:8091/v1/models 2>&1 | head -c 400)
  kill "$SRV_PID" 2>/dev/null; sleep 2; kill -0 "$SRV_PID" 2>/dev/null && kill -9 "$SRV_PID" 2>/dev/null; wait "$SRV_PID" 2>/dev/null
  {
    echo "server_ready=$READY ready_s=$SRV_READY_S"
    echo "health_models=$HEALTH"
    echo "== llama-server.log (first 40) =="; head -40 llama-server.log 2>/dev/null
    echo "== server.log tail =="; tail -20 llama-server.log 2>/dev/null
    echo "== CUDA lines =="; grep -aiE "cuda|gpu|device|offload|load time" llama-server.log 2>/dev/null | head -12
  } > i3_server.txt 2>&1
  [ "$READY" -eq 1 ] || FAIL=1
  CUDA_LINES=$(grep -aicE "cuda|offload|ggml_cuda|device" llama-server.log 2>/dev/null || true)
CUDA_LINES=${CUDA_LINES:-0}
  GPU_USED=$(grep -aiE "offloading|ggml_cuda_init|CUDA0" llama-server.log 2>/dev/null | head -3)
  { echo "llama_cuda_log_lines=$CUDA_LINES"; echo "llama_gpu_evidence=${GPU_USED:-none}"; } >> i3_server.txt
else
  echo "skipped (download/sha failed)" > i3_server.txt
fi
echo "script_end_utc=$(date -u +%FT%TZ)" >> i3_identity.txt
echo "gpu_offload=$([ -n "${GPU_USED:-}" ] && echo yes || echo no)" >> i3_server.txt
echo "I3_$([ "$FAIL" -eq 0 ] && echo PASS || echo FAIL)" > i3_PASSFAIL.txt
cat i3_PASSFAIL.txt; cat i3_download.txt; cat i3_sha.txt
echo "I3_DONE fail=$FAIL"
exit "$FAIL"
