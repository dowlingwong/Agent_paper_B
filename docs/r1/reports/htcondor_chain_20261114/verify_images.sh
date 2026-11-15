#!/bin/bash
# Read-only verification of the ghcr images by digest (author 14 Nov: inspect + exec VERSIONS,
# plus D1 llama-server smoke for the gpu image). Writes only under /work.
set -uo pipefail
V=/work/dwong/htcondor_prep_20261114/chain_20261114/verify
mkdir -p "$V"
export APPTAINER_CACHEDIR=/work/dwong/paperb/.apptainer/cache
export APPTAINER_TMPDIR=/work/dwong/paperb/.apptainer/tmp
mkdir -p "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR"
CPU=ghcr.io/dowlingwong/r1-htc-cpu@sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa
GPU=ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296
echo "start_utc=$(date -u +%FT%TZ)" > "$V/verify.log"

for pair in "cpu r1-htc-cpu" "gpu r1-htc-gpu"; do
  set -- $pair; name=$1; repo=$2
  tok=$(curl -s --max-time 20 "https://ghcr.io/token?scope=repository:dowlingwong/$repo:pull" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("token",""))')
  d=$(curl -sI --max-time 30 -H "Authorization: Bearer $tok" -H "Accept: application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json" "https://ghcr.io/v2/dowlingwong/$repo/manifests/20261114-74820315" | grep -i '^docker-content-digest:' | tr -d '\r' | awk '{print $2}')
  echo "tag_${name}_digest=$d" >> "$V/verify.log"
done

python3 - "$V" <<'PY'
import json, sys, urllib.request
V = sys.argv[1]
repos = {"cpu": ("dowlingwong/r1-htc-cpu", "sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa"),
         "gpu": ("dowlingwong/r1-htc-gpu", "sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296")}
for name, (repo, digest) in repos.items():
    t = json.load(urllib.request.urlopen("https://ghcr.io/token?scope=repository:" + repo + ":pull"))["token"]
    req = urllib.request.Request("https://ghcr.io/v2/" + repo + "/manifests/" + digest,
        headers={"Authorization": "Bearer " + t, "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json"})
    doc = json.load(urllib.request.urlopen(req))
    if "manifests" in doc:
        m = [x for x in doc["manifests"] if x.get("platform", {}).get("architecture") == "amd64"][0]
        req2 = urllib.request.Request("https://ghcr.io/v2/" + repo + "/manifests/" + m["digest"],
            headers={"Authorization": "Bearer " + t, "Accept": "application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"})
        doc = json.load(urllib.request.urlopen(req2))
    total = sum(int(l["size"]) for l in doc.get("layers", []))
    with open(V + "/sizes.txt", "a") as f:
        f.write(f"{name}_manifest_digest={digest}\n{name}_layers_bytes={total}\n{name}_layers_gib={total/2**30:.2f}\n")
    print(name, total)
PY

run_case() {
  name=$1; img=$2; shift 2
  echo "== $name inspect rc ==" >> "$V/verify.log"
  apptainer inspect "$img" > "$V/$name.inspect.txt" 2>&1; echo "inspect_rc=$?" >> "$V/verify.log"
  echo "== $name exec VERSIONS rc ==" >> "$V/verify.log"
  apptainer exec "$img" cat /opt/r1/VERSIONS.txt > "$V/$name.VERSIONS.txt" 2>&1; echo "versions_rc=$?" >> "$V/verify.log"
  "$@" > "$V/$name.checks.txt" 2>&1
  echo "checks_rc=$?" >> "$V/verify.log"
}
run_case cpu "$CPU" bash -c 'set -u
for env in harness tracks trackp; do
  if [ -x /opt/r1/envs/$env/bin/python ]; then
    echo "== $env =="; /opt/r1/envs/$env/bin/python -VV 2>&1
    /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas, pytest; print(\"numpy\", numpy.__version__, \"sklearn\", sklearn.__version__, \"pandas\", pandas.__version__, \"pytest\", pytest.__version__)" 2>&1 | tail -2
  else echo "== $env ABSENT =="; fi
done
echo "== llama =="; command -v llama-server || echo "absent (expected for cpu)"
echo "== uv =="; uv --version'
run_case gpu "$GPU" bash -c 'set -u
for env in harness tracks trackp; do
  echo "== $env =="; /opt/r1/envs/$env/bin/python -VV 2>&1
  /opt/r1/envs/$env/bin/python -c "import numpy, sklearn, pandas, pytest; print(\"numpy\", numpy.__version__, \"sklearn\", sklearn.__version__, \"pandas\", pandas.__version__, \"pytest\", pytest.__version__)" 2>&1 | tail -2
done
echo "== trackp torch =="; /opt/r1/envs/trackp/bin/python -c "import torch; print(\"torch\", torch.__version__, \"cuda_available\", torch.cuda.is_available(), \"torch_cuda\", torch.version.cuda)" 2>&1
echo "== llama-server --version (D1 smoke) =="; /opt/r1/llama/bin/llama-server --version 2>&1 | head -8; echo "llama_version_rc=$?"
echo "== ldd llama-server =="; ldd /opt/r1/llama/bin/llama-server 2>&1 | grep -iE "libgomp|libcuda|not found" | head -8
echo "== VERSIONS llama lines =="; grep -i llama /opt/r1/VERSIONS.txt 2>/dev/null || cat /opt/r1/VERSIONS.txt'
echo "end_utc=$(date -u +%FT%TZ)" >> "$V/verify.log"
echo "VERIFY_DONE"
