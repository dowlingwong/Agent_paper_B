cd /home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120 || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data
export CUDA_VISIBLE_DEVICES=""
{
  echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
  echo "memory.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.max")"
  echo "memory.swap.max=$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")"
  echo "expected_memory.max=8589934592"
  echo "expected_memory.swap.max=0"
  echo "which_python_before_PATH=$BEFORE"
  echo "which_python_after_PATH=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "PYTHONPATH=$PYTHONPATH"
  echo "VIRTUAL_ENV=$VIRTUAL_ENV"
  echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
  echo "taskset_cpus=94,93,85,61,59,58,42,41"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt1_GPU_234004Z/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
{
  echo "# launch prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "torch=$(python -c 'import torch;print(torch.__version__, torch.version.cuda)' 2>&1)"
  echo "env_freeze_live_sha256=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "env_freeze_expected=d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"
  echo "data_manifest_sha256=$(sha256sum /home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens/data_manifest.json 2>&1)"
  echo "data_manifest_expected=ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51"
  echo "node_data_link=$(readlink /home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120/nodes/autoresearch_fixedtokens/data 2>&1)"
  echo "spec_raw_sha256=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("/home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120/configs/trackg/nodes/autoresearch_fixedtokens.yaml").raw_sha256)' 2>&1)"
  echo "spec_raw_sha256_expected=5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192"
  echo "committed_file_pin=147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc"
  echo "deployed_pin_expected=069e987ac71a8ff30db7a28b7410778a4a8211aa3ecff00e23437498f2e9d2ed"
  echo "no_cuda_ipc_in_result_path:"
  python - <<'PY'
import ast
from pathlib import Path
base = Path("nodes/autoresearch_fixedtokens")
for f in ("run_fixed_budget.py", "ar_worker.py"):
    t = ast.parse((base / f).read_text())
    hits = [n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)
            and n.attr in {"cuda_share", "cuda_open", "_share_cuda_", "_new_shared_cuda", "bind_cuda"}]
    print(f, "CUDA_IPC_API_HITS=", sorted(set(hits)) or "NONE")
PY
  echo "import_port_smoke_gpu:"; python -c 'import tests.trackg.port_smoke_gpu; print("import OK")' 2>&1
  echo "smoke_entry:"; python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("autoresearch_fixedtokens") is not None)' 2>&1
} > /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt1_GPU_234004Z/prechecks.txt
FS=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)
[ "$FS" = "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42" ] || { echo "STOP env freeze sha $FS != expected" >&2; exit 92; }
DM=$(sha256sum /home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens/data_manifest.json 2>/dev/null | cut -d' ' -f1)
[ "$DM" = "ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51" ] || { echo "STOP data manifest sha $DM != expected" >&2; exit 93; }
SS=$(PYTHONPATH=src python -c 'from autoresearch.trackg.node_template import load_trackg_node_spec as L; print(L("/home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120/configs/trackg/nodes/autoresearch_fixedtokens.yaml").raw_sha256)' 2>/dev/null)
[ "$SS" = "5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192" ] || { echo "STOP spec raw sha $SS != expected" >&2; exit 94; }
ENTRY=$(python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("autoresearch_fixedtokens") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 95 ;; esac
taskset -c 94,93,85,61,59,58,42,41 /usr/bin/time -v -o /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt1_GPU_234004Z/time_v.txt python -m tests.trackg.port_smoke_gpu --node autoresearch_fixedtokens --gpu-uuid GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d --cpus 94,93,85,61,59,58,42,41 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt1_GPU_234004Z/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
{
  echo "# cgroup memory after the smoke $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  for f in memory.peak memory.current memory.events memory.max memory.swap.max memory.swap.current; do
    if [ -f "$AR_TEST_CGROUP_PARENT/$f" ]; then echo "$f=$(cat "$AR_TEST_CGROUP_PARENT/$f")"; else echo "$f=NOT_EXPOSED"; fi
  done
} > /home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_retry_20261120T232847Z/attempt1_GPU_234004Z/memory_cgroup.txt
exit $RC
