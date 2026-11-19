#!/bin/bash
# usage: smoke_one.sh <kit> <node> <gpu_uuid> <cpus> <runs_root> <logfile>
# One per-node isolated port_smoke_gpu.py run (checklist E, real data) in its own delegated user scope
# with an enforced 8 GiB memory cap. CPU affinity <cpus>; the GPU UUID is handed to the runner (which sets
# CUDA_VISIBLE_DEVICES inside the run), not to this process. Run root is outside the repository.
# The node's Python environment is put FIRST on PATH: the node spec's run_command is `python3 ...`, and the
# smoke's own interpreter (envs/torch312/bin/python) is what fix B binds into the sandbox; without this the
# baseline's `python3` resolves to /usr/bin/python3 (3.10, no torch) inside the sandbox and the run fails.
set -u
KIT=$1; NODE=$2; GPU=$3; CPUS=$4; RUNS=$5; LOG=$6
BASE=/home/dowling/r1_trackg_20261117
PY=$BASE/envs/torch312/bin/python
export AR_TRACKG_DATA_ROOT=$BASE/data
case "$KIT" in
  ar)   HOME_DIR=$BASE/harness_iso_ar ;;
  mlab) HOME_DIR=$BASE/harness_iso_mlab ;;
  mlgym) HOME_DIR=$BASE/harness_iso_mlgym ;;
  *) echo "bad kit" >&2; exit 2 ;;
esac
mkdir -p "$RUNS" || exit 3
{
  echo "# smoke kit=$KIT node=$NODE gpu=$GPU cpus=$CPUS runs_root=$RUNS start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# worktree tip: $(git -C "$HOME_DIR" rev-parse HEAD)"
  nvidia-smi --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv,noheader > "${RUNS%/}/gpu_before.txt" 2>&1
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader >> "${RUNS%/}/gpu_before.txt" 2>&1
  systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
    CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
    echo "scope_cgroup=$AR_TEST_CGROUP_PARENT"
    cd "'"$HOME_DIR"'" || exit 3
    export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
    export PATH="'"$BASE"'/envs/torch312/bin:$PATH"
    export AR_TRACKG_DATA_ROOT="'"$AR_TRACKG_DATA_ROOT"'" CUDA_VISIBLE_DEVICES=""
    taskset -c "'"$CPUS"'" "'"$PY"'" -m tests.trackg.port_smoke_gpu \
      --node "'"$NODE"'" --gpu-uuid "'"$GPU"'" --cpus "'"$CPUS"'" \
      --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
      --runs-root "'"$RUNS"'" --provisional-timeout 1800 2>&1
    RC=$?
    echo "SMOKE_EXIT=$RC"
    exit $RC'
  SRC=$?
  echo "systemd_run_rc=$SRC"
  nvidia-smi --query-gpu=index,uuid,memory.used,memory.free,utilization.gpu --format=csv,noheader > "${RUNS%/}/gpu_after.txt" 2>&1
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader >> "${RUNS%/}/gpu_after.txt" 2>&1
  echo "# end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
exit "$SRC"
