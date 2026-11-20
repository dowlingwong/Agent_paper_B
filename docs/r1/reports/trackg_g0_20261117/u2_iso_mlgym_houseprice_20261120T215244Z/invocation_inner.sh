cd /home/dowling/r1_trackg_20261117/harness_iso_mlgym || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312
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
  echo "taskset_cpus=79,78,77,76,59,42,34,28"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
{
  echo "# launch env/import/versions prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "numpy=$(python -c 'import numpy;print(numpy.__version__)' 2>&1)"
  echo "pandas=$(python -c 'import pandas;print(pandas.__version__)' 2>&1)"
  echo "scikit_learn=$(python -c 'import sklearn;print(sklearn.__version__)' 2>&1)"
  echo "pytest=$(python -c 'import pytest;print(pytest.__version__)' 2>&1)"
  echo "torch=$(python -c 'import torch;print(torch.__version__)' 2>&1)"
  echo "cuda_available_under_mask=$(python -c 'import torch;print(torch.cuda.is_available())' 2>&1)"
  echo "env_freeze_live_sha256=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)"
  echo "env_freeze_expected=d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"
  echo "data_manifest_sha256=$(sha256sum /home/dowling/r1_trackg_20261117/data/mlgym_houseprice/data_manifest.json 2>&1)"
  echo "data_link=$(readlink /home/dowling/r1_trackg_20261117/harness_iso_mlgym/third_party/mlgym/nodes/mlgym_houseprice/data 2>&1)"
  echo "import_port_smoke_gpu:"; python -c 'import tests.trackg.port_smoke_gpu; print("import OK")' 2>&1
  echo "smoke_entry:"; python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("mlgym_houseprice")["budget"])' 2>&1
} > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/prechecks.txt
FS=$(PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" 2>/dev/null | sha256sum | cut -d' ' -f1)
[ "$FS" = "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42" ] || { echo "STOP env freeze sha $FS != d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42" >&2; exit 92; }
DM=$(sha256sum /home/dowling/r1_trackg_20261117/data/mlgym_houseprice/data_manifest.json 2>/dev/null | cut -d' ' -f1)
[ "$DM" = "73ee55972381fd36ee5b3244467d7f05333adfc292ed48089786b366d5c686ff" ] || { echo "STOP data manifest sha $DM != 73ee55972381fd36ee5b3244467d7f05333adfc292ed48089786b366d5c686ff" >&2; exit 93; }
ENTRY=$(python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("mlgym_houseprice") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 94 ;; esac
taskset -c 79,78,77,76,59,42,34,28 /usr/bin/time -v -o /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/time_v.txt python -m tests.trackg.port_smoke_gpu --node mlgym_houseprice --cpus 79,78,77,76,59,42,34,28 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
exit $RC
