# Track S STOP 4 consequences — operator record (15 November 2026)

**Status.** These two units are **prepared for independent review; not executed**. `stop_trks_watch.sh` is
executed only after (a) its review is ACCEPTED and (b) B2 has ended normally and its post-run
collection + marker retirement have completed. `tasl2_readonly_inventory.sh` is executed only after its
review is ACCEPTED and TASL-2 is reachable again. Neither unit deletes anything.

**Author decisions** (branch `author-stop4-20261115` @ `1f5f24e3`, PLAN §10; those rows are external to
this execution branch):
- `R1-TRACKS-STOP4-END`: Track S ends at STOP 4; no EVIDENCE; TASL-7 is no longer allocated to Track S; all
  Track S directories/processes/branches/data stay exactly as they are (no move/modify/delete); cleanup
  only by a later author decision.
- `R1-TRACKS-STOP4-CONSEQUENCES` item (7): `trks_watch` on TASL-7 keeps running until B2 ends; after B2
  ends and its marker is retired, the experiment agent stops it with an independently reviewed unit,
  **without deleting any file**.
- Item (4): TASL-2 is released from Track S, but after its network is restored the experiment agent
  performs a **read-only inventory** (Track S servers, GPU lease, processes); the inventory goes to
  review before any other use; nothing is resumed, no lock is released; the scene stays untouched pending
  the author's decision.

## `stop_trks_watch.sh`

**Ordering.** Normal-completion only: requires `b2.exit` = 0, the normal `postrun/POSTRUN_COLLECT_OK`
(with `analysis_rc=0`), `marker-retirement.json`, marker absent, and refuses when the stopped-run
retirement receipt is present. It also refuses while the B2 runner, any Track S collector, any Track S
`llama-server` (ports 18101/18102) or any `trks_llm` process is alive.

**Identity gates.** The pinned watcher is the tmux session `trks_watch` with pane `pane_pid=1388760`,
`cmd=bash`, and the watcher script `/home/dowling/r1_tracks/bin/trks-watch` with SHA-256
`cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`. The unit records the actual
`tmux list-panes` line and the actual script SHA and stops on any mismatch (the pane has been stable since
30 Oct 2026). The process check uses the exact command line `bash /home/dowling/r1_tracks/bin/trks-watch`
so it does not match this script itself, the `tmux new` launcher, or the tmux server.

**Action.** `tmux kill-session -t trks_watch` only (no pkill/rm; no signal to any other session or user's
process). It then verifies the session is gone and the watcher bash process is gone.

**Scene preservation.** Before/after process tables; `~/r1_locks` listing; and the `manifest.json`/`STOP`
inventory compared against the post-watch baseline (`$RUN_DIR/postwatch/manifest_inventory_after_watch.txt`
and `stop_inventory_after_watch.txt`) **with both sides sorted** (the baseline is in filesystem order).
An exclusive `stop_receipt.txt` (artifact SHA-256s), `TRKS_WATCH_STOPPED.ok`, and the before/after/diff files
are written under `$RUN_DIR/trks_stop/`. No Track S scene file is written or removed by this unit; the
watcher itself may have already appended its own `marker gone` line to `runs/logs/watch.log` after the
marker retirement — that is the watcher's write, not this unit's.

**No-retry / recovery.** A `trks_stop` directory means an earlier attempt started: move it aside with
`mv` (never delete) and re-run. Never delete the scene, the marker receipts or the unit's own capture files.

## `tasl2_readonly_inventory.sh`

Strictly read-only on TASL-2: no start/stop/signal, no lock released, no writes on TASL-2. It writes only
to a **new local output directory** and records per-command rc, host/user, tmux sessions, GPU + compute
apps, `~/r1_locks` listing (and a non-destructive `flock -n` lease probe), Track S/exam/llama processes,
listeners, `~/r1_tracks/out` trees, run logs, disk/memory. TASL-2's ssh alias is `portal_zhixu` (Track S
runbook §0.1, user dowling; the bare `tasl2` alias does not exist). A failed/unreachable ssh is a STOP
(exit 2, `UNREACHABLE.txt`, no inventory), and a second run is refused unless the output dir is moved
aside. Only after the inventory is reviewed may the deferred TASL-2 bare-repo push be considered; nothing
else is done on TASL-2.

## Round-1 review findings answered (commit on top of `5c3ff87a`)

- **B-1**: the identity regex now matches the real `tmux list-panes` line
  (`trks_watch pane=%0 pane_pid=1388760 cmd=bash`), and the script SHA is gated too.
- **B-2**: the manifest/STOP comparison sorts both sides (the postwatch baseline is unsorted raw `find`
  output; current content was verified identical when sorted).
- **B-3**: TASL-2 is addressed as `portal_zhixu` (runbook §0.1), not the nonexistent `tasl2` alias.
- **B-4**: ssh rc is gated; an unreachable TASL-2 writes `UNREACHABLE.txt`, exits 2 and produces no
  inventory.
- **M-1/M-2/M-3**: watcher script-SHA gate; B2-runner/Track S collector/llama/`trks_llm`/lease gates;
  exclusive receipt with artifact SHA-256s and `TRKS_WATCH_STOPPED.ok`; before/after process tables.
- **M-4/M-5/M-6**: no-retry recovery documented; TASL-2 census extended (tmux, lock presence and a
  non-destructive lease probe, processes, listeners, output trees, logs, disk/mem, per-command rc); NOTE
  wording corrected (prepared-for-review, normal-completion-only scope, invocation, the watcher's own log
  write, no file deletion).
- **M-7 (commit content)**: `5c3ff87a` also carried an updated B2 occupancy review that is not part of
  these Track S units; this follow-up commit is the record for the units themselves.

## Watcher marker-gone behaviour (author requirement, read-only)

Before retiring the B2 marker the author asked to show, read-only, what `trks_watch` does when the marker
disappears. `watcher_marker_gone_analysis.md` records the full script (SHA `cf6884…`) and the finding: on
marker-gone it **only appends the log line** `marker gone: resume by hand (delete STOP files, start servers,
re-run launch scripts)` and returns to polling; it does not delete STOP files, does not start collectors or
servers, and does not touch locks or evidence. The author's risky case therefore does not apply, and the
normal order `postrun → retire B2 marker → stop_trks_watch` is safe; `stop_trks_watch.sh` is the unit that
stops the watcher, with the scene inventory compared against the post-watch baseline.

## TASL-2 read-only census and deferred bare-repo push (executed)

- **Census (21:11Z, accepted review).** The accepted `tasl2_readonly_inventory.sh` (sha `0f7149c5…`) was run
  from the Mac after a read-only pre-check confirmed `~/r1_locks/gpu0.lock` exists (the m-10 guard). Capture:
  `tasl2_census_20261115/` (inventory `b5c737c5…`, SHA256SUMS 4/4, reachability/inventory rc 0). TASL-2 had
  rebooted shortly before (uptime 19 min): no tmux server/session, GPU idle with no compute apps,
  `gpu0.lock` 0 B and lease FREE, no Track S/exam/llama processes, no 18101/18102 listeners, `out/` =
  `digits_mlp` + `smoke` preserved, disk/memory recorded. Independent review
  `docs/r1/reviews/TASL2_READONLY_CENSUS_REVIEW_20261115.md` (sha `a00cf7a2…`, accepted; 11 MINOR, no
  BLOCKING/MAJOR). Ruling (4) gate satisfied: census reviewed before any other use; scene untouched, no
  resume, no lock release.
- **Read-only caveat (reviewer m-4).** The census SSH login itself triggered the host's systemd user
  session/wireplumber, which wrote `~/.local/state/wireplumber/restore-stream` (205 B) outside the Track S
  scene; no command of the census wrote to the host and no process/lock/ref was touched.
- **Deferred push (21:19:18Z).** After the accepted census review, `refs/heads/trackS-ops-20261030` was
  fast-forwarded **`25907343 → fab88fce`** (52 commits, no force) on the TASL-2 bare repo; live ref verified.
  Receipt: `tasl2_bare_push_receipt.txt`. The Mac's remote-tracking ref (`78a1b65e`) and the resources doc's
  "54 behind" were stale; the live delta was 52. Nothing else was done on TASL-2.
