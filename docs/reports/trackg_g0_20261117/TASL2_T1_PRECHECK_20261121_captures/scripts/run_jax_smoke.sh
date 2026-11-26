#!/bin/bash
# R1-T1-HOST-TASL TASL-2 pre-launch: jax312 GPU smoke inside the worker sandbox at the harness pin (the
# Breakout node's environment; G.1b/G.4 plan §6.5), in a delegated scope with the exclusive GPU lease
# (flock only, no lease-log write). Same refusals as run_gpu_smoke.sh.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_engineering/tasl2_t1_precheck_20261121
T1=/home/dowling/r1_tracks/t1_tasl
REPO=$T1/harness
JAXPY=$T1/envs/jax312/bin/python
CAP="$BASE/captures"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2

APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/gpu_compute_apps_pre_jax_smoke.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/jax_smoke_refused.txt"
  exit 3
fi
if [ -e "$HOME/r1_locks/trackx_evidence.active" ]; then
  echo "REFUSED: Track X evidence marker present" | tee "$CAP/jax_smoke_refused.txt"
  exit 3
fi

exec 9>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open $HOME/r1_locks/gpu0.lock"; exit 4; }
if ! flock -w 180 9; then
  echo "REFUSED: ~/r1_locks/gpu0.lock is held by another process (180 s wait exhausted)" | tee "$CAP/jax_lease_status.txt"
  exit 4
fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/jax_lease_status.txt"

systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup)
  export AR_TEST_CGROUP_PARENT="/sys/fs/cgroup$CG"
  exec "'"$JAXPY"'" "'"$BASE"'/scripts/probe_jax.py" \
    --repo "'"$REPO"'" --base "'"$BASE"'" --interpreter "'"$JAXPY"'" \
    --out "'"$BASE"'/captures/c6b_jax_gpu_smoke.json" --tag jax_gpu_smoke
'
rc=$?

nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/gpu_compute_apps_post_jax_smoke.txt" 2>&1
echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc" | tee -a "$CAP/jax_lease_status.txt"
flock -u 9
exit $rc
