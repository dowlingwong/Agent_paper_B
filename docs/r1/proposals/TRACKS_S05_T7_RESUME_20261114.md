# Track S `digits_mlp` S0.5 resume on TASL-7 — candidate for review (14 November 2026, rev 5)

**Candidate for independent review; not an execution.** Resumes the paused S0.5 run after B1 `_d` ends normally and its
Track X marker is retired by the reviewed post-run unit. Authority: `reports/TRACKS_DIGITS_HOSTMOVE_20261112.md`
(rev 4), the accepted TASL-7 S0.1 result (k=2, `reports/TRACKS_S01_TASL7_RESULT_20261113.md`), the reviewed k=2 S0.5
unit, the Track S operator runbook rev 3.3 Phase 4, and the author's no-deletion rule (the paused STOP is **renamed**
into the run `_to_delete`, not removed as the runbook's illustrative `find -delete` would do). ENGINEERING_ONLY.

## 0. Preconditions (all fail-closed; any failure = STOP, preserve, report)
1. B1 `_d` ended normally and the reviewed `_d` post-run unit was accepted and executed: `~/r1_locks/trackx_evidence.active`
   absent; retirement receipt recorded; no B1/track process; `gpu0.lock` free; only `trks_watch` in default tmux; Track P
   marker absent; drill marker absent.
2. The paused scene is intact, checked against a **pause baseline**: `$RUN=out/digits_mlp/s05_t7_20261113` (manifest,
   ledgers, STOP; `done` holds the counts 22 roots / 6 forks / 0 leaves / 0 failed / 0 exhausted and `done.status` is
   asserted `paused`; `len(manifest['sessions']) == 1`) and `$WORK=scratch/digits_mlp/s05_t7_20261113`
   (`roots/<id>/root_trials.jsonl` and `roots/<id>/snapshots`; the leaves/S0.5b inputs live under `$WORK`, not
   `$RUN`). A pause
   capture exists (taken at pause time or reconstructed as: files under `$RUN`/`$WORK` have mtime <= the pause
   `2026-11-13T13:03:00Z`; `$RUN/STOP` inode 57048847, 0 bytes, sha `e3b0c442…`); no new/removed paths; no truncated
   last line of any JSONL. `b1_proposals.jsonl` is a B1 artifact and is not part of the Track S scene.
3. Paper pin `8237fd02…` detached/clean in `/home/dowling/r1_tracks/work/Agent_paper_B`; harness `a3fedbb…` clean;
   `trks` wrapper pins unchanged; prior `$OUT/digits_mlp/a2u_prior_r2_20261111.json` sha `5c849d15…`.
4. k = 2 (Phase-1 decision; the launcher's `K` is the server count 2, distinct from the manifest's audit `K`=5, which is
   `--k-audit` seeds and is not changed by the resume; `obs-inflation 1.0` and the λ₂ decision rule are fixed by the reviewed launcher/Phase 4
   analysis and are not changed by the resume). Deployed reviewed scripts: `tasl7_digits_s05_20261113.sh` sha `f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3` (takes `K`,
   starts `trks-servers $K` itself if `trks_llm` is absent), `tasl7_digits_s05b_20261113.sh` sha `3685dfe6…`; `bash -n`.
5. **No separate server start**: the launcher starts the k=2 servers after its own guards; starting servers first would
   orphan them if the launcher refuses (exit 2). First-resume note: an earlier attempt with the previous script revision
   `3e957464…` aborted rc=1 before starting anything because its `LIVE=$(pgrep … | wc -l)` guard tripped
   `set -euo pipefail` with zero servers; the STOP had already been renamed into `_to_delete` (verified, no deletion) and
   no server/collector started. The fixed revision is `f823b86a…` (see §0.5; the new unit script sha). Any launcher refusal is a STOP: if it did start `trks_llm` before
   failing, kill only that session (`tmux kill-session -t trks_llm`), verify no own `llama-server` remains and the
   lease is free, and report.

## 1. Resume steps (TASL-7 via `ssh tasl7 'bash -s'`; each block self-contained; Mac-local capture dir)
1. **Capture** (read-only): tmux; manifest `done`; `$RUN` and `$WORK` listings with sizes/mtimes/ino; STOP stat/sha
   (0 B, inode 57048847, sha `e3b0c442…`); GPU/lease; the **current** `$R/logs/trks_s05_t7.cmd` and its sha256 (trks-run
   overwrites `.cmd` on the next run, so it must be captured here); `trks_s05_t7.exit` and launch rc history; paper/harness
   HEADs; marker absence. Store the capture under `/private/tmp/...` **on the Mac** with `SHA256SUMS`; host-side copies
   are read-only listings only.
2. **Retire the pause STOP without deleting it** (if `$RUN/STOP` is already absent and a single
   `$RUN/_to_delete/STOP.retired.*` exists with 0 B, inode 57048847 and sha `e3b0c442…`, skip the rename and record
   that verification; do not create a second one): verify `$RUN/_to_delete` absent→create mode 700; verify
   `$RUN/STOP` exists, 0 B, sha `e3b0c442…`, inode 57048847; verify target
   `$RUN/_to_delete/STOP.retired.<UTC>` absent; `mv -n "$RUN/STOP" <target>`; then **verify the move happened**
   (source absent, target present, 0 B, same sha/inode); if `mv -n` no-ops or the target exists: STOP, preserve.
3. **Resume with the reviewed launcher** (it starts `trks-servers 2`, waits for both endpoints and starts the collector
   in an **outer launcher** tmux session named `trks_s05t7resume` (not prefixed by the collector name `trks_s05_t7`,
   which the launcher hardcodes for the collector):
   `K=2 bash $R/launch/tasl7_digits_s05_20261113.sh` run inside tmux. It reuses `$RUN` (manifest present → resume path),
   reuses `trks_llm` if present, refuses a server count != K, and writes `$R/logs/trks_s05_t7.cmd` again.
4. **Command identity**: after the collector starts, compare the **new** `$R/logs/trks_s05_t7.cmd` with the step-1 copy
   (trks-run's `.cmd` is deterministic: require **byte-identical**; any difference is a STOP). Keep both files;
   any launcher nonzero/refusal (exit 2 guards, exit 3 server timeout, or any other): STOP; if our `trks_llm` was
   started, `tmux kill-session -t trks_llm`, pkill only own `llama-server .*--port 1810[12]`, verify lease free and no
   own process, and report.
5. Monitor read-only to completion (30-min polling; no early stop): collector log/exit, manifest done counts
   (roots/forks/leaves/failed/exhausted), `failed_units`, STOP presence, GPU/lease. A `status=deadline` end is reported
   as a deadline stop and resumed only with the same command under a renewed decision (not silently).
6. If rc=0 but `done.status` is not `complete` (e.g. `paused` or `deadline`): report and wait for the author; do not
   run S0.5b and do not silently restart.
7. On rc=0 and `done.status=complete`: stop the servers (`tmux kill-session -t trks_llm`; pkill only own
   `llama-server .*--port 1810[12]`; verify lease free, no own process) → run `tasl7_digits_s05b_20261113.sh` (CPU;
   requires manifest complete and no servers) → wait for `s05b_truncated.jsonl` / `s05_calibration.jsonl`.

## 2. Copy-back / report / review / pause
Copy the S0.5 outputs `$RUN/s05_calibration.jsonl` and `$RUN/s05b_truncated.jsonl` (both must exist; the old
`sp05*` glob matched nothing), the other run `*.jsonl` ledgers (`roots`/`forks`/`leaves`/`failed_units`/`audit_runs` as
present), the manifest, **the run's logs** (collector `.log`/`.cmd`/`.exit`; S0.5b `s05b_t7_20261113_launch.log` and
`trks_s05b_t7.{log,cmd,exit}` as present; the launcher stdout/rc under `$R/logs/`) and `SHA256SUMS` to
`results/r1/tracks/digits_mlp/s05_t7_20261113/` (never the TASL-2 scene); assert each named file exists before copy; write
the report + STATUS on `trackS-ops-20261030`; independent review; then pause and report per L1 (S0.5 summary/STOP 4
still wait for `tabular_mlp`). No B2/X.7/sweep 2. If TASL-2 returns meanwhile, it is censused read-only and preserved,
not resumed or switched to.

## 3. STOP conditions
Any precondition failure; STOP rename failure/leftover; launcher refusal; command difference; marker/lease/GPU anomaly;
a priority marker appearing (watcher pauses; resume later, not a failure); collector exit 3 twice **in a row** (the
known forced-pause exception is recorded, not auto-retried); >2 % failed units; calibration gate failure twice; A/A or
fork-rebuild mismatch; 5-day GPU cap; verifier/report inconsistency; any difference from reviewed bytes — preserve the
scene and report; no retry/delete/pin change.
