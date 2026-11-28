#!/bin/bash
# D.3a production-route endpoint-to-lease proof (ENGINEERING ONLY; no campaign).
#
# One wrapper holds the canonical GPU and CPU leases, takes the chunk-side hardware
# probe before the server is loaded, starts the frozen rev 5 server under the same
# leases, and captures the endpoint -> listening PID -> GPU UUID -> lease descriptor
# chain.  It never starts a campaign, never reads a label and never writes an outcome.
set -uo pipefail

B=/home/dowling/r1_tracks/work/d3a_prod_20261128
R="$B/record"
V="$B/endpoint_20261128"
REPO="$B/repo"
LLAMA=/home/dowling/r1_tracks/opt/llama.cpp/build/bin/llama-server
MODEL=/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf
GPU_LEASE=/home/dowling/r1_locks/gpu0.lock
CPU_LEASE=/home/dowling/r1_locks/cpus-16-31.lock
AUDIT_SHIM=/home/dowling/r1_tracks/work/d3p7_20261128/pydeps_audit
HARNESS=/home/dowling/r1_tracks/work/harness_9bb_20261127

mkdir -p "$V"
cd "$REPO" || exit 1

status() { echo "$(date -u +%FT%TZ) $*" | tee -a "$V/status.log"; }

# Canonical leases: fd 8 = CPUs 16-31, fd 9 = the GPU card the probe checks by inheritance.
exec 8>"$CPU_LEASE" || exit 75
flock -n 8 || { echo "STOP: cpu lease busy" >&2; exit 75; }
exec 9>"$GPU_LEASE" || exit 76
flock -n 9 || { echo "STOP: gpu lease busy" >&2; exit 76; }

status "leases_taken gpu=$GPU_LEASE cpu=$CPU_LEASE wrapper=$$"
{
  echo "started_utc=$(date -u +%FT%TZ)"
  hostname
  nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader
  echo "--- free ---"; free -b
  echo "--- df ---"; df -P "$B"
} > "$V/lease_start.txt" 2>&1
ls -l /proc/$$/fd > "$V/wrapper_fds.txt" 2>&1
stat -c '%n %d %i' "$GPU_LEASE" "$CPU_LEASE" > "$V/lease_inodes.txt" 2>&1

# 1. Chunk-side probe, before the server is loaded.  fd 9 carries the GPU lease.
status "probe_start"
PYTHONPATH="$AUDIT_SHIM" AR_HARNESS_ROOT="$HARNESS" \
  taskset -c 16-31 /home/dowling/r1_tracks/venv/bin/python -B -m r1.c3.d3.probe \
  --launch "$R/launch_A0_digits_mlp_r0.json" --manifest "$R/manifest.json" \
  --out "$R/observed.json" --lease-path "$GPU_LEASE" \
  > "$V/probe_stdout.txt" 2> "$V/probe_stderr.txt"
PROBE_RC=$?
status "probe_rc=$PROBE_RC"

# 2. Frozen rev 5 server under the same leases and CPU set.
printf "%q " "$LLAMA" -m "$MODEL" --host 127.0.0.1 --port 8095 -ngl 999 -c 32768 \
  -np 1 --jinja --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui > "$V/server_argv.txt"
echo >> "$V/server_argv.txt"
status "server_start"
taskset -c 16-31 "$LLAMA" -m "$MODEL" --host 127.0.0.1 --port 8095 -ngl 999 -c 32768 \
  -np 1 --jinja --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui \
  > "$V/server.log" 2>&1 &
SPID=$!
echo "$SPID" > "$V/server.pid"
status "server_pid=$SPID"

READY=0
for _ in $(seq 1 240); do
  if curl -sf --max-time 1 http://127.0.0.1:8095/props > "$V/props.json" 2>/dev/null; then
    READY=1; break
  fi
  sleep 0.5
done
status "server_ready=$READY"

# 3. The chain: endpoint port -> PID -> GPU UUID -> inherited lease descriptors.
curl -s --max-time 5 http://127.0.0.1:8095/v1/models > "$V/models.json" 2>&1
ss -ltnp 'sport = :8095' > "$V/ss_listen.txt" 2>&1
ls -l /proc/"$SPID"/fd > "$V/server_fds.txt" 2>&1
grep -E '^(Name|Pid|PPid|Cpus_allowed_list):' /proc/"$SPID"/status > "$V/server_status.txt" 2>&1
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader > "$V/compute_apps_at_endpoint.txt" 2>&1
nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader > "$V/gpu_at_endpoint.txt" 2>&1

# 4. Close the server, then show the card and the leases are released.
status "server_stop"
kill -TERM "$SPID" 2>/dev/null
wait "$SPID" 2>/dev/null
SERVER_RC=$?
status "server_rc=$SERVER_RC"
sleep 2
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv,noheader > "$V/compute_apps_after_stop.txt" 2>&1
nvidia-smi --query-gpu=index,uuid,name,driver_version,memory.total,memory.used,memory.free --format=csv,noheader > "$V/gpu_after_stop.txt" 2>&1
{
  echo "ended_utc=$(date -u +%FT%TZ)"
} > "$V/lease_end.txt"
exec 9>&-
exec 8>&-
status "leases_released"
