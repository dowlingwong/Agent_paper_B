#!/bin/bash
# Stop ONLY the TASL-7 trks_watch process, after B2 ends normally and its marker is retired.
# Authority: R1-TRACKS-STOP4-CONSEQUENCES item (7) — "B2 结束后由实验 agent 按独立审查过的单元停止，
# 不删除任何文件". Prepared for independent review: execute only after (a) this unit is accepted and
# (b) B2 normal completion + normal postrun collection + marker retirement are all done.
# No file is written to or removed from the Track S scene by this unit; logs/STOPs/locks stay.
# (The watcher itself may append its own `marker gone` line to $R/logs/watch.log after the marker
# retirement; that is the watcher's write, not this unit's.)
set -u
set -o pipefail
umask 077
RUN_ID=8709_20261115_b2
RUN_DIR="/home/dowling/r1_b1_engineering/b2_handover_${RUN_ID}"
OUT="$RUN_DIR/trks_stop"
EXPECT_PANE_PID=1388760
WATCH_SCRIPT=/home/dowling/r1_tracks/bin/trks-watch
EXPECT_SCRIPT_SHA=cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112
POSTWATCH_MAN="$RUN_DIR/postwatch/manifest_inventory_after_watch.txt"
POSTWATCH_STOP="$RUN_DIR/postwatch/stop_inventory_after_watch.txt"
stop() { echo "STOP: $*" >&2; exit 2; }
# no-retry: a trks_stop dir means an earlier attempt started. Move it aside (never delete) and re-run.
[ ! -e "$OUT" ] || stop "trks_stop dir exists (no retry; move it aside first, never delete: mv '$OUT' '$OUT.attempt-<utc>')"
# gates: B2 normal completion + normal postrun collection + normal marker retirement
[ "$(cat "$RUN_DIR/b2.exit" 2>/dev/null)" = 0 ] || stop "b2.exit is not 0"
[ -s "$RUN_DIR/postrun/POSTRUN_COLLECT_OK" ] || stop "postrun collection missing"
grep -q '^analysis_rc=0$' "$RUN_DIR/postrun/POSTRUN_COLLECT_OK" || stop "postrun analysis rc is not 0"
[ -s "$RUN_DIR/marker-retirement.json" ] || stop "B2 marker not retired"
[ ! -e "$RUN_DIR/marker-retirement-stopped.json" ] || stop "stopped-run retirement present; this unit is normal-completion only"
[ ! -e /home/dowling/r1_locks/trackx_evidence.active ] || stop "marker still present"
# no B2 runner / no Track S collector / no Track S servers (exact patterns; does not match this script)
pgrep -f 'python.*-B -m r1\.scripts\.exam_runner b2 ' >/dev/null 2>&1 && stop "B2 runner still running"
pgrep -f 'python -m r1\.tracks\.collect .*--stop-file' >/dev/null 2>&1 && stop "a Track S collector is running"
pgrep -f 'llama-server .*--port 1810[12]' >/dev/null 2>&1 && stop "a Track S llama-server is running"
[ -s "$POSTWATCH_MAN" ] && [ -s "$POSTWATCH_STOP" ] || stop "postwatch inventory baseline missing"
mkdir -m 700 "$OUT" || stop "cannot create trks_stop dir"
{
  echo "stop_requested_utc=$(date -u +%FT%TZ)"
  echo "run_id=$RUN_ID"
  echo "b2_exit=$(cat "$RUN_DIR/b2.exit")"
  echo "marker_retirement_sha256=$(sha256sum "$RUN_DIR/marker-retirement.json" | awk '{print $1}')"
  echo "watcher_script_sha256=$(sha256sum "$WATCH_SCRIPT" | awk '{print $1}')"
  echo "== watcher before =="
  pgrep -a -f '^bash /home/dowling/r1_tracks/bin/trks-watch$' || true
  tmux list-panes -a -F '#{session_name} pane=#{pane_id} pane_pid=#{pane_pid} cmd=#{pane_current_command}' 2>/dev/null || true
  echo "== track S collector/server/llama before =="
  pgrep -a -f 'python -m r1\.tracks\.collect .*--stop-file' || echo "NO_TRACKS_COLLECTORS"
  pgrep -a -f 'llama-server .*--port 1810[12]' || echo "NO_TRACKS_LLAMA"
  echo "== gpu compute before =="
  nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader 2>&1 || true
} > "$OUT/before.txt" 2>&1 || stop "cannot write before.txt"
# identity gates: pinned watcher pane line and pinned watcher script SHA (never a bare pgrep match)
grep -Eq "^trks_watch pane=[^ ]+ pane_pid=${EXPECT_PANE_PID} cmd=bash$" "$OUT/before.txt" || stop "pinned watcher pane ${EXPECT_PANE_PID} not found (identity changed)"
grep -Eq "^watcher_script_sha256=${EXPECT_SCRIPT_SHA}$" "$OUT/before.txt" || stop "watcher script SHA changed"
# stop only that tmux session (no file changes; the session's bash is the watcher)
tmux kill-session -t trks_watch 2>"$OUT/kill.err" || stop "tmux kill-session failed"
sleep 3
{
  echo "== watcher after =="
  pgrep -a -f '^bash /home/dowling/r1_tracks/bin/trks-watch$' || echo "WATCHER_GONE"
  tmux list-panes -a -F '#{session_name} #{pane_pid} #{pane_current_command}' 2>/dev/null || true
} > "$OUT/after.txt" 2>&1 || stop "cannot write after.txt"
pgrep -f '^bash /home/dowling/r1_tracks/bin/trks-watch$' >/dev/null 2>&1 && stop "watcher process still present"
tmux has-session -t trks_watch 2>/dev/null && stop "trks_watch tmux session still present"
# scene must be untouched: r1_locks listing + manifest/STOP inventory identical to the postwatch baseline
# (both sides sorted: the postwatch raw list is in filesystem order, not a canonical order)
ls -la /home/dowling/r1_locks > "$OUT/locks_after.txt" 2>&1 || stop "cannot list r1_locks"
find /home/dowling/r1_tracks/out -name manifest.json -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort > "$OUT/manifests_after.txt" || stop "manifest inventory failed"
find /home/dowling/r1_tracks/out -name STOP -printf '%D %i %s %u %g %y %T@ %p\n' 2>/dev/null | sort > "$OUT/stops_after.txt" || stop "STOP inventory failed"
diff <(sort "$POSTWATCH_MAN") "$OUT/manifests_after.txt" > "$OUT/manifests.diff" 2>&1 || stop "manifest scene changed during the watcher stop"
diff <(sort "$POSTWATCH_STOP") "$OUT/stops_after.txt" > "$OUT/stops.diff" 2>&1 || stop "STOP scene changed during the watcher stop"
# exclusive success receipt with artifact SHA-256s
{
  echo "trks_watch_stopped_utc=$(date -u +%FT%TZ)"
  echo "watcher_pane_pid=${EXPECT_PANE_PID}"
  echo "watcher_script_sha256=${EXPECT_SCRIPT_SHA}"
  ( cd "$OUT" && sha256sum before.txt after.txt manifests.diff stops.diff ) | sed 's# .*/# #'
} > "$OUT/stop_receipt.txt" || stop "cannot write stop_receipt.txt"
[ "$(grep -c '^[0-9a-f]\{64\}  ' "$OUT/stop_receipt.txt")" -eq 4 ] || stop "stop_receipt.txt artifact hash lines incomplete"
set -C; printf 'TRKS_WATCH_STOPPED\n' > "$OUT/TRKS_WATCH_STOPPED.ok" || stop "cannot write ok marker"
echo "TRKS_WATCH_STOPPED (scene unchanged; no Track S scene file writes/deletions by this unit)"
