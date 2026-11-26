#!/bin/bash
# R1-T1-HOST-TASL: jax312 GPU on TASL-7 with the standard XLA CUDA-data-directory flag.
#
# The census jax312 environment does not ship ptxas and TASL-7 has its CUDA toolkit versioned at
# /usr/local/cuda-12.2 (no /usr/local/cuda symlink), so JAX's GPU backend cannot JIT out of the box
# (see c6b_jax_gpu.json: NOT_FOUND "Couldn't find a suitable version of ptxas").  The node's own
# ar_worker.py *appends* to XLA_FLAGS, and the worker sandbox passes XLA_ variables through, so the standard
# `--xla_gpu_cuda_data_dir` host adaptation is the surgical fix.  This script records the same probe with that
# flag; run_jax_gpu.sh recorded the unadapted result.  Same delegated scope, full-UUID GPU, exclusive lease,
# no lease-log write, before/after lease-log fingerprint.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
JAXVENV="$BASE/envs/jax312/bin/python"
CAP="$BASE/captures"
GPU_UUID=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
CUDA_DATA_DIR=/usr/local/cuda-12.2
LEASELOGS=(/home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl)
XLA="--xla_gpu_cuda_data_dir=$CUDA_DATA_DIR --xla_gpu_deterministic_ops=true"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
cd "$BASE" || exit 2
mkdir -p "$CAP/logs"

APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/jax_gpu_fixed_compute_apps_pre.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/jax_gpu_fixed_refused.txt"; exit 3
fi
[ -e "$HOME/r1_locks/trackx_evidence.active" ] && { echo "REFUSED: Track X marker" > "$CAP/jax_gpu_fixed_refused.txt"; exit 3; }
[ -x "$CUDA_DATA_DIR/bin/ptxas" ] || { echo "REFUSED: $CUDA_DATA_DIR/bin/ptxas missing" > "$CAP/jax_gpu_fixed_refused.txt"; exit 3; }

{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  [ -e "$HOME/r1_locks/gpu0.lock" ] && stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"
} > "$CAP/jax_gpu_fixed_leaselogs_before.txt" 2>&1

exec 9>>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open gpu0.lock"; exit 4; }
if ! flock -n 9; then echo "REFUSED: ~/r1_locks/gpu0.lock busy" | tee "$CAP/jax_gpu_fixed_lease_status.txt"; exit 4; fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "xla_flags=$XLA"
} | tee "$CAP/jax_gpu_fixed_lease_status.txt"
flock -n "$HOME/r1_locks/gpu0.lock" -c true >/dev/null 2>&1
echo "second_flock_rc=$? (0 means the lease is NOT exclusive)" | tee -a "$CAP/jax_gpu_fixed_lease_status.txt"

systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 -E "CUDA_VISIBLE_DEVICES=$GPU_UUID" \
  -E "XLA_FLAGS=$XLA" \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  "$JAXVENV" "$BASE/scripts/probe_jax_gpu.py" \
    --gpu-uuid "$GPU_UUID" --out "$CAP/c6b_jax_gpu_xla_cuda_dir.json" --tag jax_gpu_smoke_xla \
  > "$CAP/logs/c6b_jax_gpu_xla_cuda_dir.log" 2>&1
rc=$?
cat "$CAP/logs/c6b_jax_gpu_xla_cuda_dir.log"

nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/jax_gpu_fixed_compute_apps_post.txt" 2>&1
echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) rc=$rc" | tee -a "$CAP/jax_gpu_fixed_lease_status.txt"
flock -u 9

{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  [ -e "$HOME/r1_locks/gpu0.lock" ] && stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"
} > "$CAP/jax_gpu_fixed_leaselogs_after.txt" 2>&1
diff -u "$CAP/jax_gpu_fixed_leaselogs_before.txt" "$CAP/jax_gpu_fixed_leaselogs_after.txt" \
  > "$CAP/jax_gpu_fixed_leaselogs_diff.txt" 2>&1
echo "lease_logs_unchanged=$([ -s "$CAP/jax_gpu_fixed_leaselogs_diff.txt" ] && echo NO || echo YES)" \
  | tee -a "$CAP/jax_gpu_fixed_lease_status.txt"
exit $rc
