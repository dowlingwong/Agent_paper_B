# Track S `digits_mlp` S0.5 resume on TASL-7 — candidate for review (13/14 November 2026)

**Candidate for independent review; not an execution.** Resumes the paused S0.5 run
`out/digits_mlp/s05_t7_20261113` after B1 `_d` ends normally and its Track X marker has been retired by the reviewed
post-run unit. Follows `reports/TRACKS_DIGITS_HOSTMOVE_20261112.md` (host move), the review of the S0.5 k=2 unit, and
the Track S operator runbook rev 3.3. ENGINEERING_ONLY.

## 0. Preconditions (all fail-closed; any failure = STOP, preserve, report)
1. B1 `_d` ended normally and the reviewed `_d` post-run unit was accepted and executed: `~/r1_locks/trackx_evidence.active`
   is **absent**; its retirement receipt is recorded; no B1/track process is running; `gpu0.lock` free; only
   `trks_watch` in default tmux; Track P marker absent; drill marker absent.
2. The paused S0.5 scene is intact: `$RUN=/home/dowling/r1_tracks/out/digits_mlp/s05_t7_20261113` has `manifest.json`
   with `sessions[-1].done = {"roots":22,"forks":6,"leaves":0,"failed":0,"exhausted":0,"deadline_hit":false,
   "status":"paused"}` (or the same values with a later count if a short resume already ran), `$RUN/STOP` exists
   (0 bytes), and `root_trials`/`audit_runs`/`b1_proposals` (if any) are unchanged since the pause.
3. Paper pin `8237fd02b09ef2d28016a1c9f6acac3c35bb768b` checked out detached and clean in
   `/home/dowling/r1_tracks/work/Agent_paper_B`; harness `a3fedbb…` clean; `trks` wrapper pins unchanged
   (TASL-7 HOST_LABEL, GGUF `509287f7…`, llama `620d2225…`); prior
   `$OUT/digits_mlp/a2u_prior_r2_20261111.json` sha256 `5c849d15…` present.
4. k = 2 remains the Phase-1 decision (TASL-7 S0.1 accepted): both endpoints 18101/18102, servers started with
   `trks-servers 2`.
5. The reviewed CACHE/launch scripts are the deployed bytes (`tasl7_digits_s05_20261113.sh` sha
   `3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151`, `tasl7_digits_s05b_20261113.sh`
   sha `3685dfe6874f3dbbd7cdf07fd1d2ec45913f4e41b60c54c82ba3d79594fe920a`), `bash -n` OK.

## 1. Resume steps (TASL-7; `set -euo pipefail`, `umask 077`, `set -C`)
1. **Capture** a read-only pre-resume state (tmux, `$RUN/manifest.json` done, `$RUN/STOP` stat/sha (empty), listings,
   GPU/lease, `trks_s05_t7.exit` and launch rc history, paper/harness HEADs, marker absence). Save in a new
   `/private/tmp` capture with `SHA256SUMS`.
2. **Retire the pause STOP without deleting it**: `mv -n "$RUN/STOP" "$RUN/_to_delete/STOP.retired.<UTC>"` (create
   `$RUN/_to_delete` with mode 700 if absent; `-n` refuses overwrite; verify target absent first; record the source and
   target sha256 (both `e3b0c442…`) and the inode). If the target exists or the rename fails: STOP, preserve.
3. **Start k=2 servers**: if `trks_llm` is absent and no foreign GPU job and `gpu0.lock` free:
   `tmux new -d -s trks_llm "$R/bin/trks-servers 2"`, then bounded wait for `http://127.0.0.1:18101/v1/models` and
   `18102`; a timeout is a STOP.
4. **Resume the collector with the same command** (no parameter changes) by re-running the reviewed launch script
   `K=2 bash $R/launch/tasl7_digits_s05_20261113.sh` in tmux (session name not prefixed by `trks_s05_t7`, e.g.
   `trks_s05t7resume`). The script's resume path accepts the existing `$RUN` with a manifest and reuses `trks_llm`; it
   starts `trks-run trks_s05_t7 18101 collect --phase S0.5 --node digits_mlp --prior … --prior-sha256 5c849d15…
   --obs-inflation 1.0 --W 40 --instances 20 --policy static:0.00198,0 --rep 0 --rep 1 --rep-instances 10 --forks 1.5
   --aa-fraction 0.1 --label ENGINEERING_ONLY --deadline 28800 --stop-file $RUN/STOP --out $RUN --work $WORK/...`.
   Verify the new `trks_s05_t7.cmd` is byte-identical to the paused run's command except no changes; any difference is
   a STOP.
5. Monitor read-only to completion (30-min polling; no early stop): collector log/exit, manifest done counts,
   `failed_units.jsonl`, STOP presence, GPU/lease.
6. On rc=0 and `done.status=complete`: stop servers (kill `trks_llm`, pkill own `llama-server .*--port 1810[12]`,
   verify lease free) → run `tasl7_digits_s05b_20261113.sh` (CPU-only; requires manifest complete and no servers) →
   wait for `s05b_truncated.jsonl`/`s05_calibration.jsonl` → report + copy back.

## 2. Copy-back / report / review / pause
Copy `$RUN` (calibration/truncation JSONL, manifest, SHA256SUMS; never the TASL-2 scene) to
`results/r1/tracks/digits_mlp/s05_t7_20261113/`; write the report + STATUS on `trackS-ops`; independent review; then pause
and report per L1 (S0.5 summary/STOP 4 still wait for `tabular_mlp`). No B2/X.7/sweep 2.

## 3. STOP conditions
Any precondition failure; STOP rename failure/leftover; marker/lease/GPU anomaly; a priority marker appearing (watcher
pauses; resume later, not a failure); collector exit 3 twice; >2 % failed units; calibration gate failure twice; A/A or
fork-rebuild mismatch; verifier/report inconsistency; any difference from the reviewed bytes — preserve the scene and
report, no retry/delete/pin change.
