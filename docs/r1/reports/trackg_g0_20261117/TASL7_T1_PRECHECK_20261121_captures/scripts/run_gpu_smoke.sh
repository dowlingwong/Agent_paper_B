#!/bin/bash
# R1-T1-HOST-TASL condition 6: GPU smoke under the worker sandbox, in a delegated scope, with the
# host's documented exclusive GPU lease (~/r1_locks/gpu0.lock, flock-only: the lease log is not written).
# No deletion, no push.  Preflight refuses to touch a busy card or a host with a Track X evidence marker.
# Records the lease's exclusivity from a second process (a non-blocking flock must fail = LOCK_BUSY) and a
# before/after sha256+stat fingerprint of gpu0.lock and the two Track P attempt-1 lease-log candidates.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
REPO=/home/dowling/r1_tracks/t1_tasl/harness
VENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python
CAP="$BASE/captures"
GPU_UUID=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
LEASELOGS=(/home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl)

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2
mkdir -p "$CAP"

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

# ---- lease-log fingerprint before (read-only) ------------------------------------------------------
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  if [ -e "$HOME/r1_locks/gpu0.lock" ]; then stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"; fi
} > "$CAP/gpu_leaselogs_before.txt" 2>&1

# ---- documented exclusive lease (flock only; no write to the lease log, no attempt-1 archive access) --
exec 9>>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open $HOME/r1_locks/gpu0.lock"; exit 4; }
if ! flock -w 180 9; then
  echo "REFUSED: ~/r1_locks/gpu0.lock is held by another process (180 s wait exhausted)" | tee "$CAP/gpu_lease_status.txt"
  exit 4
fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/gpu_lease_status.txt"
# exclusive from another process? a second non-blocking flock must FAIL (the G.1b rule is STOP-if-busy)
flock -n "$HOME/r1_locks/gpu0.lock" -c true >/dev/null 2>&1
echo "second_flock_rc=$? (0 means the lease is NOT exclusive)" | tee -a "$CAP/gpu_lease_status.txt"

# ---- the GPU smoke in a delegated scope ------------------------------------------------------------
systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 -E "CUDA_VISIBLE_DEVICES=$GPU_UUID" \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '
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

# ---- lease-log fingerprint after (read-only; must be identical = no write) -------------------------
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  if [ -e "$HOME/r1_locks/gpu0.lock" ]; then stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"; fi
} > "$CAP/gpu_leaselogs_after.txt" 2>&1
diff -u "$CAP/gpu_leaselogs_before.txt" "$CAP/gpu_leaselogs_after.txt" > "$CAP/gpu_leaselogs_diff.txt" 2>&1
echo "lease_logs_unchanged=$([ -s "$CAP/gpu_leaselogs_diff.txt" ] && echo NO || echo YES)" \
  | tee -a "$CAP/gpu_lease_status.txt"
exit $rc
