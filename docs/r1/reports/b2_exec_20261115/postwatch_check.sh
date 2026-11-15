#!/bin/bash
# Post-watcher handover check (hand-off §5.5): expected pause, no FORCED, fresh inventory after the
# pause, STOP touches only beside known manifests, GPU/lease free, no collectors/servers/P.3a.
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
PD="$RUN_DIR/prechecks"; PM="$RUN_DIR/postmarker"; PW="$RUN_DIR/postwatch"
stop() { printf 'STOP: %s\n' "$*" >> "$PW/postwatch.log"; echo "STOP: $*" >&2; exit 2; }
[ -d "$PW" ] && [ ! -L "$PW" ] || { echo "missing postwatch dir" >&2; exit 1; }
[ -e "$PW/postwatch.log" ] && { echo "postwatch.log exists (no retry)" >&2; exit 1; }
[ -e "$PW/postwatch.ok" ] && { echo "postwatch.ok exists" >&2; exit 1; }
set -C
exec 8> "$PW/postwatch.log" || exit 1
BEFORE=$(sed -n 's/^WATCH_LOG_LINES_BEFORE=//p' "$PD/prechecks.log" | tail -1)
[ -n "${BEFORE:-}" ] || stop "prechecks watch.log position missing"
WLOG=/home/dowling/r1_tracks/logs/watch.log
[ -r "$WLOG" ] || stop "watch.log unreadable"
grep -Fq "priority marker seen" <(tail -n +"$((BEFORE+1))" "$WLOG") || stop "no 'priority marker seen' line"
grep -Fq "FORCED" <(tail -n +"$((BEFORE+1))" "$WLOG") && stop "FORCED in watcher log"
tail -n +"$((BEFORE+1))" "$WLOG" > "$PW/watch_new_lines.txt" 2>/dev/null || stop "cannot read new watch.log lines"
cat "$PW/watch_new_lines.txt" >&8 2>&1
grep -Fq "servers stopped; lease released" "$PW/watch_new_lines.txt" || pgrep -f "trks_llm" >/dev/null 2>&1 && stop "no 'servers stopped; lease released' and trks_llm running"
# fresh inventory AFTER the pause
: > "$PW/find.err" || exit 1
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PW/find.err" > "$PW/manifest_inventory_after_watch.txt" || stop "manifest find failed"
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>> "$PW/find.err" > "$PW/stop_inventory_after_watch.txt" || stop "STOP find failed"
[ -s "$PW/find.err" ] && stop "find traversal error after watch"
# manifests must not have changed at all
diff "$PD/manifest_inventory_before.txt" "$PW/manifest_inventory_after_watch.txt" >/dev/null 2>&1 || stop "manifest inventory changed during the pause"
# STOP files: any new/changed entry must be a sibling of a known manifest
awk '{print $1" "$2" "$3" "$4" "$5" "$6" "$8}' "$PD/stop_inventory_before.txt" | sort > "$PW/stop_keys_before.txt"
awk '{print $1" "$2" "$3" "$4" "$5" "$6" "$8}' "$PW/stop_inventory_after_watch.txt" | sort > "$PW/stop_keys_after.txt"
comm -13 "$PW/stop_keys_before.txt" "$PW/stop_keys_after.txt" > "$PW/stop_touched_new_or_changed.txt"
while read -r line; do
  [ -n "$line" ] || continue
  p=${line##* }
  case "$p" in /home/dowling/r1_tracks/out/*/STOP) : ;; *) stop "unexpected STOP path $p";; esac
  d=$(dirname "$p")
  grep -Fq " $d/manifest.json" "$PD/manifest_inventory_before.txt" || stop "STOP touched outside a known manifest parent: $p"
done < "$PW/stop_touched_new_or_changed.txt"
# none other path may change: comm -23 (removed) must be empty
comm -23 "$PW/stop_keys_before.txt" "$PW/stop_keys_after.txt" > "$PW/stop_disappeared.txt"
[ -s "$PW/stop_disappeared.txt" ] && stop "a STOP file disappeared (no-deletion rule)"
# GPU/lease/P.3a after the pause
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader > "$PW/gpu_apps_after.txt" 2>&1
[ -s "$PW/gpu_apps_after.txt" ] && stop "GPU compute app present after pause"
flock -n /home/dowling/r1_locks/gpu0.lock true || stop "gpu0.lock still busy"
pgrep -a -f "P\.3a|p3a" > "$PW/p3a_after.txt" 2>&1 && stop "P.3a running"
pgrep -a -f "python -m r1\.tracks\.collect .*--stop-file" >/dev/null 2>&1 && stop "collector still running"
[ -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker disappeared"
echo "POSTWATCH_PASS" >> "$PW/postwatch.log"
set -C; : > "$PW/postwatch.ok" || { echo "cannot write postwatch.ok exclusively" >&2; exit 1; }
echo "POSTWATCH_PASS"
