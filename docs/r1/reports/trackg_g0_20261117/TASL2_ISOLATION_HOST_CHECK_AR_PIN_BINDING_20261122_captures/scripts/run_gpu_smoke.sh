#!/bin/bash
# TASL-2 AR-pin host check: C6 GPU smoke under the worker sandbox at harness pin 2d09f9a9, in a delegated
# scope, with the host's documented exclusive GPU lease (~/r1_locks/gpu0.lock; flock only -- the lease log is
# not written).  The card is never shared and no foreign compute is run: the small CUDA tensor is allocated by
# the ar-cond7a interpreter inside the sandboxed worker.  No deletion, no push.
#
# usage: run_gpu_smoke.sh BASE REPO VENV CAP SCRIPTS
set -uo pipefail
umask 077

BASE="$1"; REPO="$2"; VENV="$3"; CAP="$4"; SCRIPTS="$5"
TAG=ar_pin_gpu_smoke
CUDA_UUID_EXPECTED="GPU-4d623e76-7587-ee15-a633-46f60d220d94"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2

APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/gpu_compute_apps_pre_c6.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/c6_refused.txt"
  exit 3
fi
if [ -e "$HOME/r1_locks/trackx_evidence.active" ]; then
  echo "REFUSED: Track X evidence marker present" | tee "$CAP/c6_refused.txt"
  exit 3
fi
GPU_LINE="$(nvidia-smi --query-gpu=uuid --format=csv,noheader 2>&1 | head -1 | tr -d '[:space:]')"
if [ "$GPU_LINE" != "$CUDA_UUID_EXPECTED" ]; then
  echo "REFUSED: the only GPU is $GPU_LINE, expected $CUDA_UUID_EXPECTED" | tee "$CAP/c6_refused.txt"
  exit 3
fi

exec 9>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open $HOME/r1_locks/gpu0.lock"; exit 4; }
if ! flock -w 180 9; then
  echo "REFUSED: ~/r1_locks/gpu0.lock is held by another process (180 s wait exhausted)" \
    | tee "$CAP/c6_gpu_lease_status.txt"
  exit 4
fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "gpu_uuid=$GPU_LINE"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/c6_gpu_lease_status.txt"

systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup)
  export AR_TEST_CGROUP_PARENT="/sys/fs/cgroup$CG"
  exec "'"$VENV"'" "'"$SCRIPTS"'/probe_gpu.py" \
    --repo "'"$REPO"'" --base "'"$BASE"'" --interpreter "'"$VENV"'" \
    --out "'"$CAP"'/c6_gpu_smoke.json" --tag "'"$TAG"'"
'
rc=$?

nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_post_c6.txt" 2>&1
echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc" | tee -a "$CAP/c6_gpu_lease_status.txt"
flock -u 9
exit $rc
