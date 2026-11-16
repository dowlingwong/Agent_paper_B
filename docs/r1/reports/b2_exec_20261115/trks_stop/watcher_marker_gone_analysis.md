# Read-only analysis: what `trks_watch` does when the B2 marker disappears

**Question (author, 15 Nov):** before retiring the B2 marker, show read-only what the watcher does when the marker
disappears; if it can remove the STOP files or let any Track S collector resume, the `stop_trks_watch` step must come
**before** marker retirement, with the scene inventory unchanged.

**Evidence.** The running watcher is `/home/dowling/r1_tracks/bin/trks-watch`, SHA-256
`cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112` (matches `watcher_expected.txt`), read-only, full
script (21 lines):

```bash
#!/usr/bin/env bash
R=/home/dowling/r1_tracks
log() { echo "$(date -u +%FT%TZ) $*" >> "$R/logs/watch.log"; }
MARKERS="$HOME/r1_locks/trackx_evidence.active $HOME/r1_locks/trackp_evidence.active $R/trks_drill.active"
marker() { for f in $MARKERS; do if [ -e "$f" ]; then seen=$f; return 0; fi; done; return 1; }
ours() { pgrep -u "$(id -u)" -f 'python -m r1\.tracks\.collect .*--stop-file' >/dev/null; }
log "watch started"
while sleep 60; do
  marker || continue
  log "priority marker seen ($seen): pausing"
  find "$R/out" -name manifest.json -print0 2>/dev/null | while IFS= read -r -d '' m; do touch "$(dirname "$m")/STOP"; done
  t=0
  while ours; do
    sleep 30; t=$((t + 30))
    if [ "$t" -ge 3600 ]; then log "FORCED: collectors still running after 1 h; stopping servers anyway"; break; fi
  done
  tmux kill-session -t trks_llm 2>/dev/null && log "servers stopped; lease released"
  while marker; do sleep 60; done
  log "marker gone: resume by hand (delete STOP files, start servers, re-run launch scripts)"
done
```

**Conclusion (read-only).** On the marker-gone transition the watcher executes **only** the `log` line
`marker gone: resume by hand (delete STOP files, start servers, re-run launch scripts)` and returns to the polling
loop. It does **not** delete any STOP file, does not start any server or collector, does not release or take a lock, and
does not touch Track S evidence. The "delete STOP files, start servers, re-run launch scripts" text is an instruction
to a human, not an action in the script. Therefore the author's risky case does not apply: the normal order
`postrun → retire B2 marker → stop trks_watch (scene unchanged)` is safe, and the `stop_trks_watch` unit remains the
unit that stops the watcher. Observed corroboration in `watch.log`: after the earlier `_d` marker retirement
(2026-11-14T10:16:36Z) and the drill session (2026-11-14T22:23:37Z), the log shows only the marker-gone line, no
STOP removals or server starts; the STOP files from that session remained in place (the pre-B2 census listed them).

**Note (review nit):** the quoted script above trims two comment lines for brevity; the exact bytes are pinned by SHA-256 `cf68843e…` (and the reviewed `tasl7_census_20261107/watcher.txt`), which is the authoritative record.
