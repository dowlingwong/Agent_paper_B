#!/bin/bash
# TASL-2 read-only inventory after its network is restored (R1-TRACKS-STOP4-CONSEQUENCES item (4)).
# Strictly read-only on TASL-2: no start/stop/signal, no lock released, no file writes on TASL-2.
# The output dir is created locally (must be absent). TASL-2's ssh alias is `portal_zhixu`
# (Track S runbook §0.1, user dowling); override with TASL2_HOST only if the alias genuinely changes.
# Invocation: bash tasl2_readonly_inventory.sh <local_out_dir>
set -u
set -o pipefail
umask 077
OUT_DIR="${1:?usage: tasl2_readonly_inventory.sh <local_out_dir>}"
TASL2_HOST="${TASL2_HOST:-portal_zhixu}"
SSH="ssh -o BatchMode=yes -o ConnectTimeout=15"
[ ! -e "$OUT_DIR" ] || { echo "STOP: out dir exists (no retry; move it aside, never delete)" >&2; exit 2; }
mkdir -m 700 "$OUT_DIR" || { echo "STOP: cannot create local out dir" >&2; exit 2; }
printf 'inventory_requested_utc=%s\nhost_alias=%s\n' "$(date -u +%FT%TZ)" "$TASL2_HOST" > "$OUT_DIR/request.txt" || exit 2
# reachability gate FIRST: a failed ssh must STOP and must not leave a "collected" inventory behind
$SSH "$TASL2_HOST" 'true' >/dev/null 2>&1; CONN=$?
printf 'ssh_rc=%s\n' "$CONN" > "$OUT_DIR/reachability.rc"
if [ "$CONN" -ne 0 ]; then
  printf 'TASL2_UNREACHABLE ssh_rc=%s\n' "$CONN" > "$OUT_DIR/UNREACHABLE.txt"
  echo "STOP: TASL-2 ($TASL2_HOST) unreachable (ssh rc=$CONN); no inventory collected" >&2
  exit 2
fi
# remote read-only inventory; every command records its own rc; nothing is written on TASL-2
$SSH "$TASL2_HOST" 'bash -s' > "$OUT_DIR/inventory.txt" 2>&1 <<'EOF'
set -u
echo "host=$(hostname) utc=$(date -u +%FT%TZ)"
r(){ echo "\$ $*"; "$@" 2>&1; rc=$?; echo "rc=$rc"; return 0; }
echo "== user/host =="; r id; r uptime
echo "== tmux =="; r tmux ls
echo "== gpu =="; r nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv,noheader
echo "== gpu compute apps =="; r nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader
echo "== r1_locks (presence only) =="; r ls -la /home/dowling/r1_locks
echo "== lease probe (opens the existing lock file read-only; no file content change) =="; echo "\$ flock -n ~/r1_locks/gpu0.lock true"; flock -n /home/dowling/r1_locks/gpu0.lock true && echo "LEASE_FREE" || echo "LEASE_HELD"; echo "rc=$?"
echo "== track S processes =="; r pgrep -a -f 'r1\.tracks|trks_llm|trks-watch|trks_watch'
echo "== exam/llama processes =="; r pgrep -a -f 'exam_runner|llama-server'
echo "== listeners 18101/18102 =="; r ss -ltnp
echo "== track S output trees =="; r ls -la /home/dowling/r1_tracks/out
r find /home/dowling/r1_tracks/out -maxdepth 2 -type d
echo "== run logs/exits =="; r ls -la /home/dowling/r1_tracks/logs
echo "== disk/mem =="; r df -h /home/dowling; r free -g
echo "== inventory done =="
EOF
INV=$?
printf 'inventory_ssh_rc=%s\n' "$INV" > "$OUT_DIR/inventory.rc"
if [ "$INV" -ne 0 ]; then
  echo "STOP: remote inventory ssh failed (rc=$INV); partial output preserved, nothing written on TASL-2" >&2
  exit 2
fi
( cd "$OUT_DIR" && sha256sum request.txt reachability.rc inventory.rc inventory.txt > SHA256SUMS ) || { echo "STOP: cannot write local SHA256SUMS" >&2; exit 2; }
( cd "$OUT_DIR" && sha256sum -c SHA256SUMS >/dev/null ) || { echo "STOP: local SHA256SUMS verification failed" >&2; exit 2; }
printf 'TASL2_INVENTORY_WRITTEN %s/inventory.txt\n' "$OUT_DIR"
