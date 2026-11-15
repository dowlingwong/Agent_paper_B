#!/bin/bash
# Read-only B2 site inventory before the marker. Writes only to $RUN_DIR.
set -u
set -o pipefail
umask 077
HEAD=8709dce792d45bbb5c05d9f7d239e19454efbb15
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
OUT="$RUN_DIR/prechecks.log"
[ -d "$RUN_DIR" ] || { echo "STOP: run dir missing" >&2; exit 1; }
[ -f "$OUT" ] && { echo "STOP: prechecks.log exists" >&2; exit 1; }
exec 9> "$OUT" || exit 1
echo "=== handover prechecks $(date -u +%FT%TZ) host-local $(date +%FT%T%z) ===" >&9
echo "HEAD=$HEAD RUN_ID=$RUN_ID" >&9
echo "GPU: $(nvidia-smi --query-gpu=uuid,memory.total --format=csv,noheader | head -1)" >&9
echo "GPU compute apps: $(nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader | tr '\n' ';')" >&9
if flock -n /home/dowling/r1_locks/gpu0.lock true; then echo "LEASE-FREE"; else echo "LEASE-BUSY(STOP)"; fi >&9
echo "DISK_AVAIL_BYTES=$(df -B1 --output=avail /home/dowling | tail -1 | tr -d ' ')" >&9
echo "=== locks ===" >&9; ls -la /home/dowling/r1_locks >&9 2>&1
[ -e /home/dowling/r1_locks/trackx_evidence.active ] && echo "TRACKX_MARKER_PRESENT(STOP)" >&9 || echo "TRACKX_MARKER_ABSENT" >&9
[ -e /home/dowling/r1_locks/.*trackp* ] && echo "TRACKP_MARKER_POSSIBLE" >&9 || echo "TRACKP_MARKER_ABSENT" >&9
echo "=== watcher ===" >&9; pgrep -a -f "trks_watch|trks-watch" >&9 2>&1 || echo "NO_WATCHER" >&9
echo "WATCH_LOG_LINES_BEFORE=$(wc -l < /home/dowling/r1_tracks/logs/watch.log 2>/dev/null || echo 0)" >&9
echo "=== collectors ===" >&9; pgrep -a -f "python -m r1\.tracks\.collect .*--stop-file" >&9 2>&1 || echo "NO_COLLECTORS" >&9
echo "=== trks_llm ===" >&9; pgrep -a -f "trks_llm" >&9 2>&1 || echo "NO_TRKS_LLM" >&9
echo "=== P.3a ===" >&9; pgrep -a -f "P\.3a|p3a" >&9 2>&1 || echo "NO_P3A" >&9
echo "=== manifest inventory before (device inode size owner group type mtime path) ===" >&9
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort >&9
echo "=== STOP inventory before ===" >&9
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort >&9
echo "=== STOP content hashes ===" >&9
find /home/dowling/r1_tracks/out -name STOP -print0 2>/dev/null | xargs -0 -r sha256sum >&9 2>&1
echo "=== predecessor _d retirement ===" >&9
cat /home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d/marker-retirement_after_run.json >&9 2>&1 || echo "PREDECESSOR_RETIREMENT_MISSING" >&9
ls -la /home/dowling/r1_locks/_to_delete 2>&1 >&9
echo "=== done $(date -u +%FT%TZ) ===" >&9
cat "$OUT"
