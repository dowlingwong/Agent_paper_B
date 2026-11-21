#!/bin/bash
# R1-T1-HOST-TASL: jax312 GPU check on TASL-7 (the G.1b mlgym_breakout_minatar node's environment).
# Delegated per-command cgroup (Delegate=yes, MemoryMax=8G, MemorySwapMax=0), the host's documented exclusive GPU
# lease (~/r1_locks/gpu0.lock, flock-only: NO lease-log write), GPU named by full UUID.  No deletion, no push.
#
# Also records the lease's exclusivity from a second process (a non-blocking flock by another shell must fail =
# LOCK_BUSY) and fingerprints the two Track P attempt-1 lease-log candidates and gpu0.lock before/after.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
JAXVENV="$BASE/envs/jax312/bin/python"
CAP="$BASE/captures"
GPU_UUID=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
LEASELOGS=(/home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl)

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2
mkdir -p "$CAP"

APPARGS=(--gpu-uuid "$GPU_UUID" --out "$CAP/c6b_jax_gpu.json" --tag jax_gpu_smoke)

# ---- preflight: no compute app, no Track X marker ---------------------------------------------------
APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/jax_gpu_compute_apps_pre.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/jax_gpu_refused.txt"; exit 3
fi
if [ -e "$HOME/r1_locks/trackx_evidence.active" ]; then
  echo "REFUSED: Track X evidence marker present" | tee "$CAP/jax_gpu_refused.txt"; exit 3
fi

# ---- lease-log fingerprint before (read-only) ------------------------------------------------------
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  if [ -e "$HOME/r1_locks/gpu0.lock" ]; then stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"; fi
} > "$CAP/jax_gpu_leaselogs_before.txt" 2>&1

# ---- documented exclusive lease (flock only; no lease-log write) ------------------------------------
exec 9>>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open $HOME/r1_locks/gpu0.lock"; exit 4; }
if ! flock -n 9; then
  echo "REFUSED: ~/r1_locks/gpu0.lock is held by another process" | tee "$CAP/jax_gpu_lease_status.txt"
  exit 4
fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/jax_gpu_lease_status.txt"
# exclusive from another process? a second non-blocking flock must FAIL (this is the G.1b STOP-if-busy rule)
flock -n "$HOME/r1_locks/gpu0.lock" -c true >/dev/null 2>&1
echo "second_flock_rc=$? (0 means the lease is NOT exclusive)" | tee -a "$CAP/jax_gpu_lease_status.txt"

# ---- jax312 GPU in a delegated scope ---------------------------------------------------------------
systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 -E "CUDA_VISIBLE_DEVICES=$GPU_UUID" \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  "$JAXVENV" "$BASE/scripts/probe_jax_gpu.py" "${APPARGS[@]}" > "$CAP/logs/c6b_jax_gpu.log" 2>&1
rc=$?
cat "$CAP/logs/c6b_jax_gpu.log"

nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/jax_gpu_compute_apps_post.txt" 2>&1
{ echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc"; } | tee -a "$CAP/jax_gpu_lease_status.txt"
flock -u 9

# ---- lease-log fingerprint after -------------------------------------------------------------------
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  if [ -e "$HOME/r1_locks/gpu0.lock" ]; then stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"; fi
} > "$CAP/jax_gpu_leaselogs_after.txt" 2>&1
diff -u "$CAP/jax_gpu_leaselogs_before.txt" "$CAP/jax_gpu_leaselogs_after.txt" \
  > "$CAP/jax_gpu_leaselogs_diff.txt" 2>&1
echo "lease_logs_unchanged=$([ -s "$CAP/jax_gpu_leaselogs_diff.txt" ] && echo NO || echo YES)" \
  | tee "$CAP/jax_gpu_lease_status.txt"
exit $rc
