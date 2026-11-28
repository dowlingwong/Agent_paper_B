#!/bin/bash
# D.3a production driver for the TASL-2 direct SSH route (ENGINEERING; no campaign by default).
#
# The reviewed chunk and probe modules are used unchanged.  This wrapper supplies what the
# reviewed `launch_ssh.launch` helper does not supply on this host: the venv/audit-shim
# environment, the canonical CPU lease beside the GPU lease, the server lifetime, and the
# 20 GB chunk scope.  It starts no campaign unless RUN_CHUNK=1.
#
# TEMPLATE: this file was not executed.  The executed endpoint proof is endpoint_run.sh
# (same probe/server sequence); the chunk branch below was not run.
set -uo pipefail

cleanup() { [ -n "${SPID:-}" ] && kill -TERM "$SPID" 2>/dev/null || true; }
trap cleanup EXIT

B=/home/dowling/r1_tracks/work/d3a_prod_20261128
R="$B/record"
REPO="$B/repo"
V="${DRIVER_CAPTURE_DIR:-$B/driver_20261128}"
CHUNK_LAUNCH="${CHUNK_LAUNCH:-$R/launch_A0_digits_mlp_r0.json}"
CHUNK_OUT="${CHUNK_OUT:-$B/runs/A0__digits_mlp__r0}"
GPU_LEASE=/home/dowling/r1_locks/gpu0.lock
CPU_LEASE=/home/dowling/r1_locks/cpus-16-31.lock
PYTHON=/home/dowling/r1_tracks/venv/bin/python
AUDIT_SHIM=/home/dowling/r1_tracks/work/d3p7_20261128/pydeps_audit
HARNESS=/home/dowling/r1_tracks/work/harness_9bb_20261127
DATA_CACHE="$B/data_cache"
SCOPE="systemd-run --user --scope -p Delegate=yes -p MemoryMax=20G -p MemorySwapMax=0"

mkdir -p "$V"
cd "$REPO"

# The reviewed screening cache must be staged for every OpenML node before a campaign.
for n in openml_breast_w openml_climate openml_credit_approval openml_ionosphere openml_sonar; do
  [ -d "$DATA_CACHE/$n/data_cache" ] || { status "data_cache missing for $n"; exit 81; }
done
status() { echo "$(date -u +%FT%TZ) $*" | tee -a "$V/status.log"; }

# Canonical leases: fd 8 = CPUs 16-31, fd 9 = the GPU card the probe checks by inheritance.
exec 8>"$CPU_LEASE"
flock -n 8 || { echo "STOP: cpu lease busy" >&2; exit 75; }
exec 9>"$GPU_LEASE"
flock -n 9 || { echo "STOP: gpu lease busy" >&2; exit 76; }

export PATH="/home/dowling/r1_tracks/venv/bin:$PATH"
export PYTHONPATH="$AUDIT_SHIM"
export AR_HARNESS_ROOT="$HARNESS"

status "leases_taken gpu=$GPU_LEASE cpu=$CPU_LEASE wrapper=$$"
{
  echo "started_utc=$(date -u +%FT%TZ)"
  hostname
  nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
} > "$V/lease_start.txt" 2>&1

# 1. Chunk-side probe, before the server is loaded.  fd 9 carries the GPU lease.
status "probe_start"
taskset -c 16-31 "$PYTHON" -B -m r1.c3.d3.probe \
  --launch "$CHUNK_LAUNCH" --manifest "$R/manifest.json" \
  --out "$R/observed.json" --lease-path "$GPU_LEASE" \
  > "$V/probe_stdout.txt" 2> "$V/probe_stderr.txt"
PROBE_RC=$?
status "probe_rc=$PROBE_RC"
[ "$PROBE_RC" = "0" ] || exit 78

# 2. Frozen rev 5 server under the same leases and CPU set.
mapfile -t SERVER_ARGV < <("$PYTHON" -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1]))["route"]["server_argv"]))' "$R/manifest.json")
[ "${#SERVER_ARGV[@]}" -gt 0 ] || { status "server_argv missing"; exit 80; }
printf "%q " "${SERVER_ARGV[@]}" > "$V/server_argv.txt"
echo >> "$V/server_argv.txt"
taskset -c 16-31 "${SERVER_ARGV[@]}" > "$V/server.log" 2>&1 &
SPID=$!
echo "$SPID" > "$V/server.pid"

READY=0
for _ in $(seq 1 240); do
  if curl -sf --max-time 1 http://127.0.0.1:8095/props > "$V/props.json" 2>/dev/null; then
    READY=1; break
  fi
  sleep 0.5
done
status "server_ready=$READY pid=$SPID"
[ "$READY" = "1" ] || { kill -TERM "$SPID" 2>/dev/null; wait "$SPID" 2>/dev/null; exit 77; }

# 3. The reviewed chunk runner, same argv as both reviewed launchers.  Gated: default no campaign.
if [ "${RUN_CHUNK:-0}" = "1" ]; then
  status "chunk_start launch=$CHUNK_LAUNCH out=$CHUNK_OUT"
  $SCOPE "$PYTHON" -B -m r1.c3.d3.campaign_chunk \
    --launch "$CHUNK_LAUNCH" --out "$CHUNK_OUT" \
    --manifest "$R/manifest.json" --observed "$R/observed.json" \
    > "$V/chunk_stdout.txt" 2> "$V/chunk_stderr.txt"
  CHUNK_RC=$?
  status "chunk_rc=$CHUNK_RC"
  [ "$CHUNK_RC" = "0" ] || exit 79
else
  status "chunk_skipped RUN_CHUNK=$RUN_CHUNK"
fi

# 4. Close the server and release the canonical leases.
kill -TERM "$SPID" 2>/dev/null || true
wait "$SPID" 2>/dev/null || true
sleep 2
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader > "$V/compute_apps_after_stop.txt" 2>&1
nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader > "$V/gpu_after_stop.txt" 2>&1
echo "ended_utc=$(date -u +%FT%TZ)" > "$V/lease_end.txt"
status "leases_released"
