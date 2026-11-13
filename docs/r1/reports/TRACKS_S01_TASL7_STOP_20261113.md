# Track S `digits_mlp` S0.1 on TASL-7 — operator-stopped before completion (13 November 2026, rev 2)

**This is NOT an S0.1 gate result and NOT a STOP of the scientific unit.** The S0.1 probe was stopped by the
operator 73 s after it started, because the operator misread the *previous* (Oct-31, `tabular_mlp`) probe log lines as
this run's results. No S0.1 identity measurement exists for TASL-7; the run is incomplete. The record below corrects
rev 1 of this file, which wrongly reported `identity_rate 0.87`.

## 1. What actually happened

- 2026-11-13T10:50:12Z: `tasl7_digits_s01_20261113.sh` started (tmux `trks_s01_launch`); the launch log has exactly
  two lines: `S0.1 start (node digits_mlp, host TASL-7, k=2 probe period)` and `both endpoints ready`; the serial probe
  started in `trks_s01_serial` (pid 4123514).
- 2026-11-13T10:51:25Z: the operator stopped `trks_s01_launch`, `trks_s01_serial` and `trks_llm`, and killed the two
  own llama-server processes — **73 s into a run whose full 600-call probe needs ~395 s at the measured ~0.658 s/call
  (the first 200-call pass ≈132 s)**.
  The probe therefore wrote no `serial.json`, no result JSON and no today-dated rc line.
- The lines `identity_rate 0.87` and `errors: 600` quoted in rev 1 belong to
  `$R/logs/trks_s01_serial.log` **mtime/ctime 2026-10-31 04:20:50 -0700** (the Oct-30/31 `tabular_mlp` S0.1 runs);
  `trks_s01_serial.exit` likewise ends at `2026-10-31T11:20:51Z rc=0`. They are not evidence about TASL-7
  `digits_mlp`.
- Today's activity is visible in the launch log (mtime 2026-11-13 02:50:12 -0800) and the llama logs' mtime
  (2026-11-13 02:50:12/02:51:20 -0800); the result dir `$OUT/digits_mlp/s01_t7_20261113/` exists but is empty.

## 2. Preserved evidence (nothing deleted or overwritten)

- `$R/logs/s01_t7_20261113_launch.log` (2 lines, today); `$R/logs/trks_s01_serial.{cmd,log,exit}` (cmd is the new
  today command; log/exit are the old Oct-31 append-only files — **do not treat their old lines as this run's
  evidence**); `$R/out/digits_mlp/s01_t7_20261113/` (empty; preserved); today's tails of
  `$R/logs/llama_18101.log` / `llama_18102.log`; captures `/private/tmp/trks-s01-t7-stop-*` and
  `/private/tmp/b1-c-stop-retirement-capture-*`.
- The `_c` STOP-case retirement (executed 10:49:31Z under the accepted unit `a4e01d2`) is unaffected: marker absent,
  retired name in `_to_delete/…040ffbe1…`, creation/retirement receipts kept, `_c` STOP scene byte-equal to the
  accepted capture; the first review later confirmed the execution is safe and must not be unwound.
- TASL-7 paper checkout remains at pin `8237fd02` detached/clean; harness `a3fedbb`; prior file present with sha
  `5c849d15…`; servers/collectors stopped; only `trks_watch`; `gpu0.lock` free.

## 3. State and next step

- **No S0.1 result exists.** The gate was not exercised. This is an operator recording error, not a host-move
  failure; no conclusion about TASL-7 determinism can be drawn from it.
- The empty `$OUT/digits_mlp/s01_t7_20261113/` directory is preserved. A re-run needs a reviewed unit that uses a
  **new output directory** (the reviewed script refuses an existing one) — prepared as the revised S0.1 script with
  `S01_SUFFIX` support (`s01_t7_20261113b`), to be independently reviewed before use; no unreviewed delete/move.
- Nothing is started until that reviewed re-run unit is accepted and the author is informed (the author's 13 Nov
  instruction already authorises the S0.1 step; the correction is an operator-error re-execution, and the report of
  the error is this file).
