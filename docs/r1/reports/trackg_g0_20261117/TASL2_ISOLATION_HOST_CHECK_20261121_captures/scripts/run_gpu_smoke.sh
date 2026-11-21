#!/bin/bash
# R1-TRACKG-AR-U2-TASL2 condition 6: GPU smoke under the worker sandbox, in a delegated scope, with the
# host's documented exclusive GPU lease (~/r1_locks/gpu0.lock, flock-only: the lease log is not written).
# No deletion, no push.  Preflight refuses to touch a busy card or a host with a Track X evidence marker.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_engineering/tasl2_hostcheck_20261121
REPO=/home/dowling/r1_trackp/harness_cond7a_20261121
VENV=/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
CAP="$BASE/captures"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2

# ---- preflight: exclusive GPU, no Track X marker ---------------------------------------------------
APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/gpu_compute_apps_pre_gpu_smoke.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/gpu_smoke_refused.txt"
  exit 3
fi
if [ -e "$HOME/r1_locks/trackx_evidence.active" ]; then
  echo "REFUSED: Track X evidence marker present" | tee "$CAP/gpu_smoke_refused.txt"
  exit 3
fi

# ---- documented exclusive lease (flock only; no write to the lease log, no attempt-1 archive access) --
exec 9>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open $HOME/r1_locks/gpu0.lock"; exit 4; }
if ! flock -w 180 9; then
  echo "REFUSED: ~/r1_locks/gpu0.lock is held by another process (180 s wait exhausted)" | tee "$CAP/gpu_lease_status.txt"
  exit 4
fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/gpu_lease_status.txt"

# ---- the GPU smoke in a delegated scope ------------------------------------------------------------
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup)
  export AR_TEST_CGROUP_PARENT="/sys/fs/cgroup$CG"
  exec "'"$VENV"'" "'"$BASE"'/scripts/probe_gpu.py" \
    --repo "'"$REPO"'" --base "'"$BASE"'" \
    --out "'"$BASE"'/captures/c6_gpu_smoke.json" --tag gpu_smoke
'
rc=$?

nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_post_gpu_smoke.txt" 2>&1
echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc" | tee -a "$CAP/gpu_lease_status.txt"
flock -u 9
exit $rc
