#!/bin/bash
# D.3a production driver for the TASL-2 direct SSH route (ENGINEERING; no campaign by default).
#
# The reviewed chunk and probe modules are used unchanged.  This wrapper supplies what the
# reviewed `launch_ssh.launch` helper does not supply on this host: the venv/audit-shim
# environment, the canonical CPU lease beside the GPU lease, the server lifetime, and the
# 20 GB chunk scope.  It starts no campaign unless RUN_CHUNK=1.
#
# ENDPOINT GUARD (compute/20261128-23).  A readiness answer on /props is not proof that the
# endpoint belongs to the server this wrapper started: if llama-server fails to bind, another
# responder on the port can answer and the chunk would call the wrong process.  Before the
# chunk, `r1.c3.d3.endpoint_guard` therefore proves listener PID, /props model/context/slots,
# the compute-app GPU UUID and the canonical lease inode.  A mismatch writes STOP.json, seals
# the capture directory with SHA256SUMS and exits 90 before the chunk module is imported.
#
# TEMPLATE: the executed endpoint proof is endpoint_run.sh; the chunk branch below was not run.
set -uo pipefail

B="${D3A_B:-/home/dowling/r1_tracks/work/d3a_prod_20261128}"
R="$B/record"
REPO="$B/repo"
V="${DRIVER_CAPTURE_DIR:-$B/driver_20261128}"
CHUNK_LAUNCH="${CHUNK_LAUNCH:-$R/launch_A0_digits_mlp_r0.json}"
CHUNK_OUT="${CHUNK_OUT:-$B/runs/A0__digits_mlp__r0}"
CHUNK_ROWS="${CHUNK_ROWS:-}"
GPU_LEASE="${D3A_GPU_LEASE:-/home/dowling/r1_locks/gpu0.lock}"
CPU_LEASE="${D3A_CPU_LEASE:-/home/dowling/r1_locks/cpus-16-31.lock}"
PYTHON="${D3A_PYTHON:-/home/dowling/r1_tracks/venv/bin/python}"
AUDIT_SHIM="${D3A_AUDIT_SHIM:-/home/dowling/r1_tracks/work/d3p7_20261128/pydeps_audit}"
HARNESS="${D3A_HARNESS:-/home/dowling/r1_tracks/work/harness_9bb_20261127}"
DATA_CACHE="${D3A_DATA_CACHE:-$B/data_cache}"
PORT="${D3A_PORT:-8095}"
SCOPE="systemd-run --user --scope -p Delegate=yes -p MemoryMax=20G -p MemorySwapMax=0"
STOP_RC=90

cleanup() { [ -n "${SPID:-}" ] && kill -TERM "$SPID" 2>/dev/null || true; }trap cleanup EXIT

mkdir -p "$V"
status() { echo "$(date -u +%FT%TZ) $*" | tee -a "$V/status.log"; }

# Seal the scene on an endpoint identity STOP.  Nothing is deleted; the capture directory and
# STOP.json stay for the infrastructure attempt record.
seal_scene() {
  local tag="$1" rc="$2" detail="$3"
  status "STOP endpoint_identity check=$tag rc=$rc scene=$V"
  # Quiesce the started server before hashing: its log must not change after the seal.
  kill -TERM "${SPID:-0}" 2>/dev/null || true
  wait "${SPID:-0}" 2>/dev/null || true
  sleep 1
  {
    echo "{"
    echo "  \"schema\": \"r1_d3_endpoint_stop/v1\","
    echo "  \"utc\": \"$(date -u +%FT%TZ)\","
    echo "  \"stage\": \"endpoint_identity\","
    echo "  \"check\": \"$tag\","
    echo "  \"rc\": $rc,"
    echo "  \"server_pid\": ${SPID:-0},"
    echo "  \"host\": \"127.0.0.1\","
    echo "  \"port\": $PORT,"
    echo "  \"manifest\": \"$R/manifest.json\","
    echo "  \"observed\": \"$R/observed.json\","
    echo "  \"check_record\": \"$V/endpoint_check_${tag}.json\","
    echo "  \"detail\": \"$detail\""
    echo "}"
  } > "$V/STOP.json"
  ( cd "$V" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ) 2>/dev/null \
    || ( cd "$V" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS )
  exit "$STOP_RC"
}

# The one pre-chunk identity check.  It is called after readiness (so a foreign responder is
# caught before the probe result is trusted) and again immediately before every chunk.
verify_endpoint() {
  local tag="$1" out rc
  out="$V/endpoint_check_${tag}.json"
  status "endpoint_check_start tag=$tag pid=${SPID:-0} port=$PORT"
  "$PYTHON" -B -m r1.c3.d3.endpoint_guard \
    --manifest "$R/manifest.json" --observed "$R/observed.json" \
    --server-pid "${SPID:-0}" --host 127.0.0.1 --port "$PORT" \
    --lease-path "$GPU_LEASE" --lease-fd 9 \
    --out "$out" >> "$V/guard.log" 2>&1
  rc=$?
  if [ "$rc" != "0" ]; then
    seal_scene "$tag" "$rc" "endpoint identity check failed; see endpoint_check_${tag}.json and guard.log"
  fi
  status "endpoint_check_pass tag=$tag"
}

cd "$REPO"

# The reviewed screening cache must be staged for every OpenML node before a campaign.
for n in openml_breast_w openml_climate openml_credit_approval openml_ionosphere openml_sonar; do
  [ -d "$DATA_CACHE/$n/data_cache" ] || { status "data_cache missing for $n"; exit 81; }
done

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
  if curl -sf --max-time 1 http://127.0.0.1:"$PORT"/props > "$V/props.json" 2>/dev/null; then
    READY=1; break
  fi
  sleep 0.5
done
status "server_ready=$READY pid=$SPID"
[ "$READY" = "1" ] || seal_scene "server_ready" 77 "the started server did not answer /props"

# Readiness is not identity: a foreign responder can answer after a failed bind.
verify_endpoint "ready"

# 3. The reviewed chunk runner, same argv as both reviewed launchers.  Gated: default no campaign.
run_chunk_checked() {
  local launch="$1" out="$2" tag="$3" chunk_rc
  verify_endpoint "chunk_${tag}"
  status "chunk_start tag=$tag launch=$launch out=$out"
  $SCOPE "$PYTHON" -B -m r1.c3.d3.campaign_chunk \
    --launch "$launch" --out "$out" \
    --manifest "$R/manifest.json" --observed "$R/observed.json" \
    > "$V/chunk_${tag}_stdout.txt" 2> "$V/chunk_${tag}_stderr.txt"
  chunk_rc=$?
  status "chunk_rc=$chunk_rc tag=$tag"
  [ "$chunk_rc" = "0" ] || exit 79
}

if [ "${RUN_CHUNK:-0}" = "1" ]; then
  if [ -n "$CHUNK_ROWS" ]; then
    [ -f "$CHUNK_ROWS" ] || { status "CHUNK_ROWS missing: $CHUNK_ROWS"; exit 82; }
    CHUNK_N=0
    while IFS=$'\t' read -r launch out; do
      [ -n "$launch" ] || continue
      CHUNK_N=$((CHUNK_N + 1))
      run_chunk_checked "$launch" "$out" "$(printf '%02d' "$CHUNK_N")"
    done < "$CHUNK_ROWS"
  else
    run_chunk_checked "$CHUNK_LAUNCH" "$CHUNK_OUT" "01"
  fi
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
