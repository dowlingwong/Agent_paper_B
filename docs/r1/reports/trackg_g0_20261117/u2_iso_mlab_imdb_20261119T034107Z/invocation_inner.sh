cd /home/dowling/r1_trackg_20261117/harness_iso_mlab || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312
export CUDA_VISIBLE_DEVICES=""
export AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data
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
  echo "AR_TRACKG_DATA_ROOT=$AR_TRACKG_DATA_ROOT"
  echo "taskset_cpus=0-7"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_imdb_20261119T034107Z/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
taskset -c 0-7 /usr/bin/time -v -o /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_imdb_20261119T034107Z/time_v.txt python -m tests.trackg.port_smoke_gpu --node mlab_imdb --gpu-uuid GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154 --cpus 0-7 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_imdb_20261119T034107Z/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
exit $RC
