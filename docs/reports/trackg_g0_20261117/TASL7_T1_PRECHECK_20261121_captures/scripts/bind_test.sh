#!/bin/bash
# R1-T1-HOST-TASL: one short server start/stop on TASL-7 to prove the proposer binds ONLY the Tailscale
# address (the G.4 plan §6 item 7 question), not 0.0.0.0 and not the shared-node alias .50.
#
# This is NOT a G.4 run: no worker, no calls, no outputs beyond the bind/identity captures.  It uses the exact
# exam binary and GGUF and the exam flags of the spec (context 32768, -ngl 999, -np 1); it takes the host's
# documented exclusive GPU lease (flock-only, NO lease-log write) and stops the server with SIGTERM after
# /health and /props answer.  TASL-2 is not touched; its reachability of .50 is cited, not re-run.
set -uo pipefail
umask 077

BASE=/home/dowling/r1_tracks/t1_tasl
CAP="$BASE/captures"
BIN=/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server
GGUF=/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf
TS_IP=100.106.74.51
PORT=8096
GPU_UUID=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
LEASELOGS=(/home/dowling/r1_locks/trackp_evidence.log /home/dowling/r1_trackp/runs/gpu_lease_log.jsonl)
mkdir -p "$CAP/logs" "$CAP/bind_test"
cd "$BASE" || exit 2
RUNDIR="$BASE/work/bind_test_$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RUNDIR"

# ---- preflight: no compute app, no Track X marker ---------------------------------------------------
APPS_PRE="$(nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader 2>&1)"
printf '%s\n' "$APPS_PRE" > "$CAP/bind_test/compute_apps_pre.txt"
if [ -n "$(printf '%s' "$APPS_PRE" | tr -d '[:space:]')" ]; then
  echo "REFUSED: GPU has compute apps: $APPS_PRE" | tee "$CAP/bind_test/refused.txt"; exit 3
fi
if [ -e "$HOME/r1_locks/trackx_evidence.active" ]; then
  echo "REFUSED: Track X evidence marker present" | tee "$CAP/bind_test/refused.txt"; exit 3
fi
ss -ltn | grep -E ":$PORT\b" && { echo "REFUSED: port $PORT already in use" | tee "$CAP/bind_test/refused.txt"; exit 3; }
ss -ltn > "$CAP/bind_test/ss_listen_before.txt" 2>&1

# ---- lease-log fingerprint before -------------------------------------------------------------------
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  [ -e "$HOME/r1_locks/gpu0.lock" ] && stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"
} > "$CAP/bind_test/leaselogs_before.txt" 2>&1

# ---- exclusive GPU lease (flock only; no lease-log write) -------------------------------------------
exec 9>>"$HOME/r1_locks/gpu0.lock" || { echo "REFUSED: cannot open gpu0.lock"; exit 4; }
if ! flock -n 9; then echo "REFUSED: ~/r1_locks/gpu0.lock busy" | tee "$CAP/bind_test/lease_status.txt"; exit 4; fi
{
  echo "lease_file=$HOME/r1_locks/gpu0.lock"
  echo "lease_mode=flock-exclusive, fd 9, no lease-log write"
  echo "acquired_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} | tee "$CAP/bind_test/lease_status.txt"
flock -n "$HOME/r1_locks/gpu0.lock" -c true >/dev/null 2>&1
echo "second_flock_rc=$? (0 means the lease is NOT exclusive)" | tee -a "$CAP/bind_test/lease_status.txt"

# ---- start exactly once, bound to the Tailscale address only ----------------------------------------
export CUDA_VISIBLE_DEVICES="$GPU_UUID"
env -u LD_LIBRARY_PATH -u LD_PRELOAD "$BIN" \
  -m "$GGUF" -a gemma4_31b -c 32768 -ngl 999 -np 1 --jinja \
  --chat-template-kwargs '{"enable_thinking":false}' \
  --cache-type-k q8_0 --cache-type-v q8_0 \
  --host "$TS_IP" --port "$PORT" --no-webui -lv 3 \
  > "$RUNDIR/llama-server.log" 2>&1 &
SERVER_PID=$!
echo "server_pid=$SERVER_PID launched_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) host=$TS_IP port=$PORT" \
  | tee "$CAP/bind_test/start.txt"
echo "$SERVER_PID" > "$RUNDIR/pid.txt"
echo "$RUNDIR" > "$CAP/bind_test/rundir.txt"

# ---- wait for /health (max 180 s) -------------------------------------------------------------------
HEALTH=""
for i in $(seq 1 180); do
  HEALTH="$(curl -s --max-time 2 -w '\n%{http_code}' "http://$TS_IP:$PORT/health" 2>/dev/null)"
  code="$(printf '%s' "$HEALTH" | tail -1)"
  if [ "$code" = "200" ]; then break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then echo "server exited before /health"; break; fi
  sleep 1
done
echo "health_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) body=$(printf '%s' "$HEALTH" | head -1) code=$(printf '%s' "$HEALTH" | tail -1)" \
  | tee "$CAP/bind_test/health.txt"

# ---- bind evidence: the only listener on the port is the Tailscale address ---------------------------
ss -ltnp > "$CAP/bind_test/ss_listen_after.txt" 2>&1
ss -ltn | grep -E ":$PORT\b" > "$CAP/bind_test/ss_listener_8096.txt" 2>&1
curl -s --max-time 5 "http://$TS_IP:$PORT/health" > "$CAP/bind_test/curl_health_from_51.txt" 2>&1
# not bound on 0.0.0.0: the exact same port must not answer on a non-Tailscale local address
LAN_IP="$(ip -4 -o addr show | awk '$2!="lo" && $2!="tailscale0" {print $4}' | cut -d/ -f1 | head -1)"
if [ -n "$LAN_IP" ]; then
  curl -s --max-time 3 -o /dev/null -w '%{http_code}' "http://$LAN_IP:$PORT/health" \
    > "$CAP/bind_test/curl_health_lan_ip_http_code.txt" 2>&1
  echo "lan_ip=$LAN_IP" >> "$CAP/bind_test/curl_health_lan_ip_http_code.txt"
fi
# /props as the worker reads it (bonus evidence; the G.4 worker checks /health and /props)
curl -s --max-time 5 "http://$TS_IP:$PORT/props" > "$CAP/bind_test/props.json" 2>&1

# ---- stop with SIGTERM, verify gone -----------------------------------------------------------------
echo "sigterm_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$CAP/bind_test/start.txt"
kill -TERM "$SERVER_PID" 2>/dev/null
STOPPED=NO
for i in $(seq 1 60); do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then STOPPED=YES; break; fi
  sleep 1
done
wait "$SERVER_PID" 2>/dev/null; RC=$?
echo "stopped=$STOPPED wait_rc=$RC stopped_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "$CAP/bind_test/start.txt"
flock -u 9

# ---- after-state ------------------------------------------------------------------------------------
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv,noheader \
  > "$CAP/bind_test/compute_apps_post.txt" 2>&1
ss -ltn > "$CAP/bind_test/ss_listen_post.txt" 2>&1
{ for p in "${LEASELOGS[@]}"; do
    if [ -e "$p" ]; then sha256sum "$p"; stat -c '%n|%s|%Y|%Z|%a|%i' "$p"; else echo "absent|$p"; fi
  done
  [ -e "$HOME/r1_locks/gpu0.lock" ] && stat -c 'gpu0.lock|%s|%Y|%Z|%a|%i' "$HOME/r1_locks/gpu0.lock"
} > "$CAP/bind_test/leaselogs_after.txt" 2>&1
diff -u "$CAP/bind_test/leaselogs_before.txt" "$CAP/bind_test/leaselogs_after.txt" \
  > "$CAP/bind_test/leaselogs_diff.txt" 2>&1
{ echo "released_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } >> "$CAP/bind_test/lease_status.txt"
cp "$RUNDIR/llama-server.log" "$CAP/bind_test/llama-server.log"
du -sh "$RUNDIR" > "$CAP/bind_test/rundir_size.txt" 2>&1

# ---- result JSON ------------------------------------------------------------------------------------
/usr/bin/python3 - "$CAP/bind_test" "$PORT" "$TS_IP" > "$CAP/bind_test/bind_test_result.json" 2>&1 <<'PYEOF'
import json, re, sys
from pathlib import Path
cap, port, ts_ip = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
def read(name):
    try: return (cap / name).read_text(errors="replace").strip()
    except OSError: return ""
start = read("start.txt")
health = read("health.txt")
listener = read("ss_listener_8096.txt")
lan = read("curl_health_lan_ip_http_code.txt")
health200 = "code=200" in health and '"status":"ok"' in health.replace(" ", "")
# ss -ltn columns: State Recv-Q Send-Q Local-Address:Port Peer-Address:Port  (peer 0.0.0.0:* is normal)
def local_addrs(text):
    out = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "LISTEN":
            out.append(parts[3])
    return out
locals_ = local_addrs(listener)
listener_51_only = locals_ == [f"{ts_ip}:{port}"]
props = json.loads(read("props.json")) if read("props.json").startswith("{") else None
build_info = None
n_ctx = None
if isinstance(props, dict):
    build_info = props.get("build_info")
    def find(o):
        if isinstance(o, dict):
            if "n_ctx" in o: return o.get("n_ctx")
            for v in o.values():
                r = find(v)
                if r is not None: return r
        elif isinstance(o, list):
            for v in o:
                r = find(v)
                if r is not None: return r
        return None
    n_ctx = find(props.get("default_generation_settings") or props.get("settings") or {}) or find(props)
checks = {
    "health_200": health200,
    "listener_only_tailscale_51": listener_51_only,
    "not_0000": not any(a in ("0.0.0.0:" + port, "*:" + port, "[::]:" + port) for a in locals_),
    "lan_ip_does_not_answer": lan.startswith("000") or "status_code=0" in lan or lan.startswith("000") or lan.splitlines()[0].strip() in ("000", ""),
    "stopped": "stopped=YES" in start,
    "no_compute_app_after": read("compute_apps_post.txt") == "",
    "lease_exclusive": ("second_flock_rc=" in read("lease_status.txt") and "second_flock_rc=1" in read("lease_status.txt")),
    "lease_logs_unchanged": not read("leaselogs_diff.txt"),
    "props_build_info_present": bool(build_info),
}
result = {"utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
          "server": {"host": ts_ip, "port": int(port), "binary": "/home/dowling/exam-x/work/llama.cpp/build-exam/bin/llama-server",
                     "gguf": "/home/dowling/exam-x/models/gemma4_31b/google_gemma-4-31B-it-Q4_K_M.gguf",
                     "gpu_uuid": "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1"},
          "start": start, "health": health, "listener_8096": listener,
          "lan_probe": lan, "props_build_info": build_info, "props_n_ctx": n_ctx,
          "checks": checks, "condition_bind_test_pass": all(checks.values())}
print(json.dumps(result, indent=2, sort_keys=True))
PYEOF

cat "$CAP/bind_test/bind_test_result.json"
exit 0
