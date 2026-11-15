#!/bin/bash
# TASL-2 read-only inventory after its network is restored (R1-TRACKS-STOP4-CONSEQUENCES item (4)).
# Read-only: no start/stop/signal, no lock released, no writes on TASL-2; collects what the reviewer
# needs (Track S servers, GPU lease, processes) and writes only on the local operator host.
set -u
set -o pipefail
umask 077
OUT_DIR="${1:?usage: tasl2_readonly_inventory.sh <local_out_dir>}"
[ -d "$OUT_DIR" ] && [ ! -e "$OUT_DIR/inventory.txt" ] || { echo "STOP: out dir missing or already used" >&2; exit 1; }
ssh -o BatchMode=yes -o ConnectTimeout=15 tasl2 'bash -s' > "$OUT_DIR/inventory.txt" 2>&1 <<'EOF'
set -u
echo "host=$(hostname) utc=$(date -u +%FT%TZ)"
echo "== user/host =="; id; uptime
echo "== gpu =="; nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>&1
echo "== gpu compute apps =="; nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader 2>&1
echo "== lock files =="; ls -la ~/r1_locks 2>&1
echo "== track S processes =="; pgrep -a -f "r1\.tracks|trks_llm|trks-watch|trks_watch" 2>&1 || echo "none"
echo "== exam/llama processes =="; pgrep -a -f "exam_runner|llama-server" 2>&1 || echo "none"
echo "== track S output trees (read-only listing) =="; ls -la ~/r1_tracks/out 2>&1 | head -20
EOF
echo "TASL2_INVENTORY_WRITTEN $OUT_DIR/inventory.txt"
