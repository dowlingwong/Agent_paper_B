#!/bin/bash
# Stop ONLY the TASL-7 trks_watch process, after B2 ends normally and its marker is retired.
# Authority: R1-TRACKS-STOP4-CONSEQUENCES item (7) — "B2 结束后由实验 agent 按独立审查过的单元停止，
# 不删除任何文件". No file is written to or removed from the Track S scene; logs/STOPs/locks stay.
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
OUT="$RUN_DIR/trks_stop"
EXPECT_PANE_PID=1388760
stop() { echo "STOP: $*" >&2; exit 2; }
[ -e "$OUT" ] && stop "trks_stop dir exists (no retry)"
# gates: B2 normal completion + marker retired
[ "$(cat "$RUN_DIR/b2.exit" 2>/dev/null)" = 0 ] || stop "b2.exit is not 0"
[ -s "$RUN_DIR/postrun/POSTRUN_COLLECT_OK" ] || stop "postrun collection missing"
[ -s "$RUN_DIR/marker-retirement.json" ] || stop "B2 marker not retired"
[ ! -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker still present"
mkdir -m 700 "$OUT" || stop "cannot create trks_stop dir"
set -C
{
  echo "stop_requested_utc=$(date -u +%FT%TZ)"
  echo "== watcher before =="
  pgrep -a -f "trks_watch|trks-watch" || true
  tmux list-panes -a -F '#{session_name} pane=#{pane_id} pane_pid=#{pane_pid} cmd=#{pane_current_command}' 2>/dev/null || true
} > "$OUT/before.txt" 2>&1
# identity gate: the pinned watcher pane must be present and running the watcher script
grep -Eq "^[^ ]+ [^ ]+ ${EXPECT_PANE_PID} bash$" "$OUT/before.txt" || stop "pinned watcher pane ${EXPECT_PANE_PID} not found (identity changed)"
# stop only that tmux session (no file changes; the session's bash is the watcher)
tmux kill-session -t trks_watch 2>"$OUT/kill.err" || stop "tmux kill-session failed"
sleep 3
{
  echo "== watcher after =="
  pgrep -a -f "trks_watch|trks-watch" || echo "WATCHER_GONE"
  tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' 2>/dev/null || true
} > "$OUT/after.txt" 2>&1
pgrep -f "trks_watch|trks-watch" >/dev/null 2>&1 && stop "watcher process still present"
# scene must be untouched: locks dir listing + manifest/STOP inventory identical to the postwatch one
ls -la /home/dowling/r1_locks > "$OUT/locks_after.txt" 2>&1
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort > "$OUT/manifests_after.txt"
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort > "$OUT/stops_after.txt"
diff "$RUN_DIR/postwatch/manifest_inventory_after_watch.txt" "$OUT/manifests_after.txt" > "$OUT/manifests.diff" 2>&1 || stop "manifest scene changed during the watcher stop"
diff "$RUN_DIR/postwatch/stop_inventory_after_watch.txt" "$OUT/stops_after.txt" > "$OUT/stops.diff" 2>&1 || stop "STOP scene changed during the watcher stop"
echo "TRKS_WATCH_STOPPED (scene unchanged; no files touched)"
