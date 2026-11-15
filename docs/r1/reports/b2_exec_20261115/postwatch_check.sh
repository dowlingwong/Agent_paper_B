#!/bin/bash
# Post-watcher handover check (hand-off §5.5): expected pause, no FORCED, STOP touches match the
# pre-marker inventory pattern, GPU/lease free, no collectors/servers/P.3a. Read-only.
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
PD="$RUN_DIR/prechecks"; PM="$RUN_DIR/postmarker"; PW="$RUN_DIR/postwatch"
EXPECT_GPU=GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
stop() { printf 'STOP: %s\n' "$*" >> "$PW/postwatch.log"; echo "STOP: $*" >&2; exit 2; }
[ -d "$PW" ] && [ ! -L "$PW" ] || { echo "missing postwatch dir" >&2; exit 1; }
[ -e "$PW/postwatch.ok" ] && { echo "postwatch.ok exists" >&2; exit 1; }
set -C
exec 8> "$PW/postwatch.log" || exit 1
BEFORE=$(sed -n 's/^WATCH_LOG_LINES_BEFORE=//p' "$PD/prechecks.log" | tail -1)
[ -n "${BEFORE:-}" ] || stop "prechecks watch.log position missing"
WLOG=/home/dowling/r1_tracks/logs/watch.log
[ -r "$WLOG" ] || stop "watch.log unreadable"
diff <(head -n "$BEFORE" "$WLOG") "$WLOG" >/dev/null 2>&1 && stop "watch.log did not grow (watcher did not react)"
NEW="$PW/watch_new_lines.txt"
tail -n +"$((BEFORE+1))" "$WLOG" > "$NEW" 2>/dev/null || stop "cannot read new watch.log lines"
grep -F "priority marker seen" "$NEW" >/dev/null || stop "no 'priority marker seen' line"
grep -F "FORCED" "$NEW" >/dev/null && stop "FORCED in watcher log"
grep -F "servers stopped; lease released" "$NEW" >/dev/null && stop_ok=1 || stop_ok=0
if [ "$stop_ok" -eq 0 ]; then
  pgrep -f "trks_llm" >/dev/null 2>&1 && stop "no 'servers stopped; lease released' and trks_llm still running"
fi
cat "$NEW" >&8 2>&1
# touched STOP inventory: every path in the after inventory must be a sibling of a manifest
while read -r line; do
  [ -n "$line" ] || continue
  p=$(echo "$line" | awk '{print $8}')
  case "$p" in /home/dowling/r1_tracks/out/*/STOP) : ;; *) stop "unexpected STOP path $p";; esac
  base=$(dirname "$p")
  grep -F " $base/manifest.json" "$PD/manifest_inventory_before.txt" >/dev/null || stop "STOP touched outside a known manifest parent: $p"
done < "$PM/stop_inventory_after.txt"
# GPU/lease/P.3a after the pause
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader > "$PW/gpu_apps_after.txt" 2>&1
[ -s "$PW/gpu_apps_after.txt" ] && stop "GPU compute app present after pause"
flock -n /home/dowling/r1_locks/gpu0.lock true || stop "gpu0.lock still busy"
pgrep -a -f "P\.3a|p3a" > "$PW/p3a_after.txt" 2>&1 && stop "P.3a running"
pgrep -a -f "python -m r1\.tracks\.collect .*--stop-file" >/dev/null 2>&1 && stop "collector still running"
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker disappeared"
echo "POSTWATCH_PASS" >> "$PW/postwatch.log"
: > "$PW/postwatch.ok"
echo "POSTWATCH_PASS"
