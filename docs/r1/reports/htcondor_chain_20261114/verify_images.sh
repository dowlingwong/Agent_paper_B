#!/bin/bash
# Read-only verification of the ghcr images by digest (author 14 Nov), incl. the Docker-route
# review D1 condition: the gpu image must run `llama-server --version` with rc=0.
# apptainer inspect does not accept docker:// URIs, so each image is pulled to a SIF first.
# Writes only under /work.
set -uo pipefail
V=/work/dwong/htcondor_prep_20261114/chain_20261114/verify
mkdir -p "$V"
export APPTAINER_CACHEDIR=/work/dwong/paperb/.apptainer/cache
export APPTAINER_TMPDIR=/work/dwong/paperb/.apptainer/tmp
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
CPU=ghcr.io/dowlingwong/r1-htc-cpu@sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa
GPU=ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296
TS=$(date -u +%Y%m%dT%H%M%SZ)
: > "$V/verify.log"
echo "start_utc=$(date -u +%FT%TZ) apptainer=$(apptainer --version 2>&1)" >> "$V/verify.log"
# tag -> digest (registry)
for pair in "cpu r1-htc-cpu" "gpu r1-htc-gpu"; do
  set -- $pair; name=$1; repo=$2
  tok=$(curl -s --max-time 20 "https://ghcr.io/token?scope=repository:dowlingwong/$repo:pull" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("token",""))')
  d=$(curl -sI --max-time 30 -H "Authorization: Bearer $tok" -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json" "https://ghcr.io/v2/dowlingwong/$repo/manifests/20261114-74820315" | grep -i '^docker-content-digest:' | tr -d '\r' | awk '{print $2}')
  echo "tag_${name}_digest=$d" | tee -a "$V/verify.log"
done
pull_case() {
  name=$1; uri=$2
  SIF="$V/${name}_${TS}.sif"
  echo "== pull $name ==" >> "$V/verify.log"
  t0=$(date +%s)
  apptainer pull --disable-cache --force "$SIF" "docker://$uri" > "$V/$name.pull.log" 2>&1
  prc=$?; t1=$(date +%s)
  echo "pull_${name}_rc=$prc pull_${name}_s=$((t1-t0))" >> "$V/verify.log"
  if [ "$prc" -ne 0 ] || [ ! -s "$SIF" ]; then echo "pull_${name}=FAILED" >> "$V/verify.log"; return 1; fi
  ls -l "$SIF" | awk '{print "sif_'$name'_bytes="$5}' >> "$V/verify.log"
  sha256sum "$SIF" | awk '{print "sif_'$name'_sha256="$1}' >> "$V/verify.log"
  apptainer inspect "$SIF" > "$V/$name.inspect.txt" 2>&1; echo "inspect_${name}_rc=$?" >> "$V/verify.log"
  apptainer exec "$SIF" cat /opt/r1/VERSIONS.txt > "$V/$name.VERSIONS.txt" 2>&1; echo "versions_${name}_rc=$?" >> "$V/verify.log"
  return 0
}
pull_case cpu "$CPU" && {
  apptainer exec "$V"/cpu_${TS}.sif bash -c 'set -u
    for env in harness tracks trackp; do
      if [ -x /opt/r1/envs/$env/bin/python ]; then
        echo "== $env =="; /opt/r1/envs/$env/bin/python -VV 2>&1
        /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas, pytest; print(\"numpy\", numpy.__version__, \"sklearn\", sklearn.__version__, \"pandas\", pandas.__version__, \"pytest\", pytest.__version__)" 2>&1 | tail -2
      else echo "== $env ABSENT (by design) =="; fi
    done
    echo "== llama =="; command -v llama-server || echo "absent (expected for cpu)"
    echo "== uv =="; uv --version' > "$V/cpu.checks.txt" 2>&1
  echo "checks_cpu_rc=$?" >> "$V/verify.log"
}
pull_case gpu "$GPU" && {
  apptainer exec "$V"/gpu_${TS}.sif bash -c 'set -u
    for env in harness tracks trackp; do
      echo "== $env =="; /opt/r1/envs/$env/bin/python -VV 2>&1
      /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas, pytest; print(\"numpy\", numpy.__version__, \"sklearn\", sklearn.__version__, \"pandas\", pandas.__version__, \"pytest\", pytest.__version__)" 2>&1 | tail -2
    done
    echo "== trackp torch =="; /opt/r1/envs/trackp/bin/python -c "import torch; print(\"torch\", torch.__version__, \"cuda_available\", torch.cuda.is_available(), \"torch_cuda\", torch.version.cuda)" 2>&1
    echo "== D1 llama-server --version =="
    /opt/r1/llama/bin/llama-server --version 2>&1 | head -8; echo "llama_version_rc=$?"
    echo "== ldd llama-server (libgomp/libcuda/not found) =="; ldd /opt/r1/llama/bin/llama-server 2>&1 | grep -iE "libgomp|libcuda|not found" | head -8
    echo "== VERSIONS llama lines =="; grep -i llama /opt/r1/VERSIONS.txt 2>/dev/null; echo "== VERSIONS full =="; cat /opt/r1/VERSIONS.txt' > "$V/gpu.checks.txt" 2>&1
  echo "checks_gpu_rc=$?" >> "$V/verify.log"
}
echo "end_utc=$(date -u +%FT%TZ)" >> "$V/verify.log"
echo "VERIFY_DONE"
