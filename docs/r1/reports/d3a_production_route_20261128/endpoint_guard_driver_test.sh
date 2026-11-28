#!/bin/bash
# Engineering stub test for the D.3a production driver's endpoint identity guard.
#
#   endpoint_guard_driver_test.sh success   -> the started server answers /props; the guard
#                                              passes and the chunk stub is called
#   endpoint_guard_driver_test.sh foreign   -> the started PID is alive but a different
#                                              process owns the port; STOP before the chunk
#   endpoint_guard_driver_test.sh bindfail  -> the started server exits; a foreign responder
#                                              answers /props; STOP before the chunk
#
# No real GPU, server, campaign or label is used.  Host commands are stubs except the guard
# module, which is imported from REPO_ROOT and reads /proc plus the real HTTP response.
set -uo pipefail

MODE="${1:?usage: endpoint_guard_driver_test.sh success|foreign|bindfail}"
HERE=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT="${REPO_ROOT:-$(cd "$HERE/../../../.." && pwd)}"
REAL_PYTHON="${REAL_PYTHON:-python3}"
ROOT=$(mktemp -d "${TMPDIR:-/tmp}/d3a_guard_test.XXXXXX")
BIN="$ROOT/bin"
UUID="GPU-4d623e76-7587-ee15-a633-46f60d220d94"
MODEL="$ROOT/model.gguf"
PORT=$((18000 + RANDOM % 1000))
GPU_LEASE="$ROOT/gpu0.lock"
CPU_LEASE="$ROOT/cpus-16-31.lock"
export TEST_ROOT="$ROOT" REAL_PYTHON FAKE_MODE="$MODE" UUID MODEL PORT

mkdir -p "$BIN" "$ROOT/repo" "$ROOT/record" "$ROOT/driver" "$ROOT/runs" "$ROOT/harness"
: > "$MODEL"
: > "$GPU_LEASE"
: > "$CPU_LEASE"
for n in openml_breast_w openml_climate openml_credit_approval openml_ionosphere openml_sonar; do
  mkdir -p "$ROOT/data_cache/$n/data_cache"
done

cleanup() {
  [ -n "${FOREIGN_PID:-}" ] && kill -TERM "$FOREIGN_PID" 2>/dev/null || true
  [ -f "$ROOT/driver/server.pid" ] && kill -TERM "$(cat "$ROOT/driver/server.pid")" 2>/dev/null || true
  [ -f "$ROOT/ss_pid" ] && kill -TERM "$(cat "$ROOT/ss_pid")" 2>/dev/null || true
  wait 2>/dev/null || true
  true
}
trap cleanup EXIT

cat > "$ROOT/record/manifest.json" <<EOF
{"schema": "r1_d3_campaign_manifest/v1",
 "route": {"host": "TASL-2", "gpu_uuid": "$UUID", "gpu_lease_path": "$GPU_LEASE",
           "server_argv": ["$BIN/llama-server", "-m", "$MODEL", "--host", "127.0.0.1",
                           "--port", "$PORT", "-c", "32768", "-np", "1"]}}
EOF
cat > "$ROOT/record/observed_template.json" <<EOF
{"schema": "r1_d3_observed/v1", "host": "TASL-2", "model": "NVIDIA GeForce RTX 4090",
 "gpu_uuid": "$UUID", "lease": true, "lease_path": "$GPU_LEASE", "memory_check": "pass"}
EOF
cat > "$ROOT/record/launch.json" <<EOF
{"schema": "r1_d3_launch/v1", "stage": "a", "arm": "A0", "node": "digits_mlp",
 "repetition": 0, "instance_seeds": [6201], "W": 20, "llm_cap": 80, "launcher": "ssh",
 "host": "TASL-2", "campaign_model_source": {"path": "x", "sha256": "a"},
 "manifest": {"path": "manifest.json", "sha256": "a"}, "observed": {"path": "observed.json", "probe": true}}
EOF

# --- stub host commands -------------------------------------------------------------
cat > "$BIN/taskset" <<'EOF'
#!/bin/bash
[ "${1:-}" = "-c" ] && shift 2
exec "$@"
EOF
cat > "$BIN/systemd-run" <<'EOF'
#!/bin/bash
while [ "$#" -gt 0 ]; do
  case "$1" in
    -p) shift 2 ;;
    -*) shift ;;
    *) break ;;
  esac
done
exec "$@"
EOF
cat > "$BIN/ss" <<'EOF'
#!/bin/bash
if [ -f "$TEST_ROOT/ss_pid" ]; then pid=$(cat "$TEST_ROOT/ss_pid")
else pid=$(cat "$TEST_ROOT/driver/server.pid" 2>/dev/null || echo 0); fi
echo "LISTEN 0 512 127.0.0.1:$PORT 0.0.0.0:* users:((\"llama-server\",pid=$pid,fd=12))"
EOF
cat > "$BIN/nvidia-smi" <<'EOF'
#!/bin/bash
case "$*" in
  *--query-compute-apps*)
    pid=$(cat "$TEST_ROOT/driver/server.pid" 2>/dev/null || echo 0)
    echo "$UUID, $pid, 21618" ;;
  *"-i 0"*--query-gpu=uuid*) echo "$UUID" ;;
  *--query-gpu=index*) echo "0, $UUID, NVIDIA GeForce RTX 4090, 535.309.01, 24564, 353, 24211" ;;
  *) echo "" ;;
esac
EOF
cat > "$BIN/python" <<'EOF'
#!/bin/bash
if [ "${1:-}" = "-B" ] && [ "${2:-}" = "-m" ]; then
  mod="$3"; shift 3
  case "$mod" in
    r1.c3.d3.probe)
      out=""
      while [ "$#" -gt 0 ]; do
        case "$1" in --out) out="$2"; shift 2 ;; *) shift ;; esac
      done
      cp "$TEST_ROOT/record/observed_template.json" "$out"; exit 0 ;;
    r1.c3.d3.campaign_chunk) : > "$TEST_ROOT/chunk_called"; exit 0 ;;
    r1.c3.d3.endpoint_guard) exec "$REAL_PYTHON" -B -m r1.c3.d3.endpoint_guard "$@" ;;
  esac
fi
exec "$REAL_PYTHON" "$@"
EOF
cat > "$BIN/llama-server" <<'EOF'
#!/bin/bash
exec "$REAL_PYTHON" "$TEST_ROOT/fake_llama.py"
EOF
cat > "$ROOT/fake_llama.py" <<'PY'
import http.server, json, os, sys, time

ROOT = os.environ["TEST_ROOT"]
MODE = os.environ["FAKE_MODE"]
PORT = int(os.environ["PORT"])
MODEL = os.environ["MODEL"]

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"model_path": MODEL,
                           "default_generation_settings": {"n_ctx": 32768},
                           "total_slots": 1}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        return

class Server(http.server.HTTPServer):
    allow_reuse_address = True

def serve():
    with open(os.path.join(ROOT, "ss_pid"), "w") as fh:
        fh.write(str(os.getpid()))
    Server(("127.0.0.1", PORT), Handler).serve_forever()

if MODE == "bindfail":
    sys.exit(3)
if MODE == "foreign":
    child = os.fork()
    if child == 0:
        serve()
    with open(os.path.join(ROOT, "ss_pid"), "w") as fh:
        fh.write(str(child))
    time.sleep(120)
    sys.exit(0)
serve()
PY
chmod +x "$BIN"/* "$ROOT/fake_llama.py"

# --- run ----------------------------------------------------------------------------
if [ "$MODE" = "bindfail" ]; then
  "$REAL_PYTHON" - "$ROOT" "$PORT" "$MODEL" <<'PY' &
import http.server, json, os, sys
root, port, model = sys.argv[1], int(sys.argv[2]), sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"model_path": model,
                           "default_generation_settings": {"n_ctx": 32768},
                           "total_slots": 1}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): return
class S(http.server.HTTPServer): allow_reuse_address = True
with open(os.path.join(root, "ss_pid"), "w") as fh: fh.write(str(os.getpid()))
S(("127.0.0.1", port), H).serve_forever()
PY
  FOREIGN_PID=$!
  for _ in $(seq 1 50); do [ -s "$ROOT/ss_pid" ] && break; sleep 0.1; done
fi

set +e
D3A_B="$ROOT" D3A_PYTHON="$BIN/python" D3A_AUDIT_SHIM="$REPO_ROOT" \
D3A_HARNESS="$ROOT/harness" D3A_DATA_CACHE="$ROOT/data_cache" \
D3A_GPU_LEASE="$GPU_LEASE" D3A_CPU_LEASE="$CPU_LEASE" D3A_PORT="$PORT" \
DRIVER_CAPTURE_DIR="$ROOT/driver" CHUNK_LAUNCH="$ROOT/record/launch.json" \
CHUNK_OUT="$ROOT/runs/out" RUN_CHUNK=1 \
D3_GUARD_SS_BIN="$BIN/ss" D3_GUARD_NVIDIA_SMI_BIN="$BIN/nvidia-smi" \
REAL_PYTHON="$REAL_PYTHON" TEST_ROOT="$ROOT" FAKE_MODE="$MODE" \
  bash "$HERE/production_driver.sh" > "$ROOT/driver_run.out" 2>&1
RC=$?
set -e

echo "mode=$MODE rc=$RC root=$ROOT"
echo "chunk_called=$([ -f "$ROOT/chunk_called" ] && echo yes || echo no)"
echo "stop_json=$([ -f "$ROOT/driver/STOP.json" ] && echo yes || echo no)"
if [ -f "$ROOT/driver/STOP.json" ]; then
  "$REAL_PYTHON" - "$ROOT/driver" <<'PY'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
stop = json.loads((root / "STOP.json").read_text())
print(f"stop_check={stop['check']} rc={stop['rc']}")
for name in sorted(root.glob("endpoint_check_*.json")):
    payload = json.loads(name.read_text())
    print(f"{name.name}: ok={payload['ok']} failed={payload['failed']} reason={payload['reason']}")
PY
  ( cd "$ROOT/driver" && sha256sum -c SHA256SUMS >/dev/null ) && echo "seal=OK" || echo "seal=FAIL"
fi

case "$MODE" in
  success) [ "$RC" = 0 ] && [ -f "$ROOT/chunk_called" ] && echo "result=PASS" || { echo "result=FAIL"; exit 1; } ;;
  foreign) [ "$RC" = 90 ] && [ ! -f "$ROOT/chunk_called" ] && echo "result=PASS" || { echo "result=FAIL"; exit 1; } ;;
  bindfail) [ "$RC" = 90 ] && [ ! -f "$ROOT/chunk_called" ] && echo "result=PASS" || { echo "result=FAIL"; exit 1; } ;;
esac
