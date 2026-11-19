cd /home/dowling/r1_trackg_20261117/harness_iso_mlgym || exit 3
CG=$(cut -d: -f3 /proc/self/cgroup)
export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
BEFORE=$(command -v python || true)
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
export PATH=/home/dowling/r1_trackg_20261117/envs/jax312/bin:/home/dowling/.local/bin:$PATH
export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/jax312
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
  echo "CUDA_VISIBLE_DEVICES_before_smoke=$(printenv CUDA_VISIBLE_DEVICES || echo "<unset>")"
  echo "taskset_cpus=8-15"
  echo "utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/cgroup_probe.txt
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.max")" != "8589934592" ]; then echo "STOP memory.max mismatch" >&2; exit 90; fi
if [ "$(cat "$AR_TEST_CGROUP_PARENT/memory.swap.max")" != "0" ]; then echo "STOP memory.swap.max mismatch" >&2; exit 91; fi
# fresh prechecks inside the scope, BEFORE the CUDA mask
{
  echo "# JAX/device/freeze/smoke-entry prechecks captured $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "which_python=$(command -v python)"
  echo "python_version=$(python -V 2>&1)"
  echo "jax=$(python -c 'import jax; print(jax.__version__)' 2>&1)"
  echo "jaxlib=$(python -c 'import jaxlib; print(jaxlib.__version__)' 2>&1)"
  echo "jax_cuda12_plugin=$(python -c 'import importlib.metadata as m; print(m.version("jax-cuda12-plugin"))' 2>&1)"
  echo "jax_cuda12_pjrt=$(python -c 'import importlib.metadata as m; print(m.version("jax-cuda12-pjrt"))' 2>&1)"
  echo "nvidia_cuda_nvcc_cu12=$(python -c 'import importlib.metadata as m; print("present" if "nvidia-cuda-nvcc-cu12" in [d.metadata["Name"] for d in m.distributions()] else "absent")' 2>&1)"
  echo "pytest=$(python -c 'import pytest; print(pytest.__version__)' 2>&1)"
  echo "jax_devices (no CUDA mask):"
  env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'import jax; ds=jax.devices(); print("n_devices", len(ds)); print("platform", ds[0].platform if ds else None); print(ds)' 2>&1
  PATH=/home/dowling/.local/bin:$PATH uv pip freeze --python "$(command -v python)" > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live.txt 2> /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live.stderr.txt
  sort /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live.txt > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live_sorted.txt
  echo "live_freeze_lines=$(wc -l < /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live.txt)"
  echo "live_freeze_sha256_raw=$(sha256sum /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live.txt | cut -d' ' -f1)"
  echo "live_freeze_sha256_sorted=$(sha256sum /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live_sorted.txt | cut -d' ' -f1)"
  echo "expected_launch_freeze_sha256_sorted=80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1"
  echo "fix_record_freeze_sha256_sorted=d33c96120c0be3cf20fcb2b9d783ac5366d6b0d3313e6cfe4c90583f89940217"
  echo "smoke_entry (no CUDA mask):"
  env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'from tests.trackg import port_smoke_gpu as p; print("ENTRY", p.smoke_entry("mlgym_breakout_minatar"))' 2>&1
  echo "import_test_port_mlgym:"
  env -u CUDA_VISIBLE_DEVICES python -c 'import tests.trackg.test_port_mlgym; print("import OK")' 2>&1
} > /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/prechecks_jax.txt
NDEV=$(env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'import jax; print(len(jax.devices()))' 2>/dev/null)
[ "$NDEV" = "8" ] || { echo "STOP jax.devices() count is $NDEV, expected 8" >&2; exit 92; }
LFS=$(sha256sum /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/precheck_freeze_live_sorted.txt | cut -d' ' -f1)
[ "$LFS" = "80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1" ] || { echo "STOP launch env freeze sha $LFS != expected 80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1" >&2; exit 93; }
ENTRY=$(env -u CUDA_VISIBLE_DEVICES XLA_PYTHON_CLIENT_PREALLOCATE=false python -c 'from tests.trackg import port_smoke_gpu as p; print("FOUND", p.smoke_entry("mlgym_breakout_minatar") is not None)' 2>/dev/null)
case "$ENTRY" in *"FOUND True"*) : ;; *) echo "STOP smoke_entry dry-run failed: $ENTRY" >&2; exit 94 ;; esac
export CUDA_VISIBLE_DEVICES=""
taskset -c 8-15 /usr/bin/time -v -o /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/time_v.txt python -m tests.trackg.port_smoke_gpu --node mlgym_breakout_minatar --gpu-uuid GPU-3b36edea-1a09-a37e-aa42-8277c7319e77 --cpus 8-15 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root /home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/runs --provisional-timeout 1800
RC=$?
echo "SMOKE_EXIT=$RC"
exit $RC
