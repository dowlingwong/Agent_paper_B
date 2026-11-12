# B1 `_c` post-run marker retirement and completion record — candidate for review (12 November 2026)

**Candidate for independent review; not an execution and not an authorization.** This is the post-run unit for run
`4b31_20261112_c` only, to be executed **after** a verified normal completion of that run and **before** the Track S
`digits_mlp` host-move run. It follows `proposals/B1_OPERATOR_MESSAGE_V3_20261107.md` "Normal completion" and
`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` §"Normal completion versus STOP", and `proposals/
B1_RESTART_HANDOFF_C_20261111.md` §3/§4. The author agreed on 12 Nov that the Track X marker is a cooperative lock,
not evidence, and can be renamed (not deleted) with its receipt (PLAN row `R1-EXAM-B1-TRUNCATION-INVALID` rationale).

## 0. Scope and exclusions

- Run: `4b31_20261112_c`; HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`; checkout
  `/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`; harness
  `/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness` @ `a3fedbb…`.
- Handover dir `$RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`; batch
  `$BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`.
- Marker creation receipt `$RUN_DIR/marker-receipt.json` (file SHA-256
  `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`; content dev 66306, ino 56261618,
  marker SHA-256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, run_id `4b31_20261112_c`,
  head `4b312844…`). The `_b`→`_c` retirement files already in `$RUN_DIR` (`marker-retirement.json`,
  `marker-retirement.note`) are **not** touched; this unit writes new filenames (`*_after_run.*`).
- **Not in scope:** no deletion; no deletion or retirement of pre-existing STOP files; no Track P restart; no Track S
  start (that is the separate host-move plan); no B2/X.7/sweep 2; no retry of B1; no change to pins or code.

## 1. Preconditions (fail-closed; any failure = STOP, preserve scene, report)

1. `$RUN_DIR/b1.exit` exists and contains `0`; the own tmux session `b1_4b31_20261112_c` is gone (or the runner
   process has exited) and `$BATCH/batch_state.json` reads `status` = `COMPLETE` (normal completion). If the run
   ended in a STOP (non-zero exit, `STOPPED` state, interruptions, or a `b1.log` STOP line), **this unit does not
   apply** — use the B1 STOP procedure (preserve, report, no retirement).
2. No `llama-server`, no `exam_runner`, no B1 worker process of this run; `nvidia-smi` lists no compute apps; the
   cooperative lease `~/r1_locks/gpu0.lock` is free (the runner releases it before exit).
3. The live marker still matches its creation receipt exactly (dev/ino/sha256/content), checked in Python and by
   `b1_o2_marker.py retire`; the Track P marker is absent and P.3a is stopped/absent (confirm read-only).
4. No unrelated priority marker or Track S collector is active on TASL-7; the watcher `trks_watch` is alive and the
   last `watch.log` line is the expected paused state.
5. The completion evidence is captured read-only first (`b1.exit`, `batch_state.json`, `b1.log`, server records,
   liveness of the batch tree) into a new capture directory under `/private/tmp` with `SHA256SUMS`.

## 2. Steps (exact)

1. **Completion capture (read-only).** From the Mac: `ssh tasl7 'bash -s'` with a script that prints: `b1.exit`;
   `status/completed/interruptions` from `$BATCH/batch_state.json`; `$RUN_DIR/b1.log` (size/content); `tmux ls`;
   `pgrep` for `exam_runner|llama-server|r1.tracks.collect`; `nvidia-smi` compute apps; `flock -n
   ~/r1_locks/gpu0.lock`; `git -C "$CHECKOUT" rev-parse HEAD` and `status --porcelain`; marker stat/sha256/content;
   Track P marker; `tail -2 ~/r1_tracks/logs/watch.log`. Save `ssh.log`/`ssh.exit` and `SHA256SUMS` in the capture
   directory; record the capture path.
2. **Retire the marker with its creation receipt** (only this run's marker; renames, deletes nothing):
   ```
   set -C
   python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire \
     --lock-dir "$HOME/r1_locks" --receipt "$RUN_DIR/marker-receipt.json" \
     > "$RUN_DIR/marker-retirement_after_run.json"
   printf 'source_receipt=%s\nsource_receipt_sha256=%s\n' \
     "$RUN_DIR/marker-receipt.json" "$(sha256sum "$RUN_DIR/marker-receipt.json" | cut -d' ' -f1)" \
     > "$RUN_DIR/marker-retirement_after_run.note"
   test ! -e "$HOME/r1_locks/trackx_evidence.active" || { echo 'STOP: marker still present'; exit 1; }
   ```
   If the receipt does not match, or the retire fails, STOP: preserve the scene and report; do not force, do not
   delete.
3. **Observe the watcher transition**: within ~90 s, the watcher either logs `priority marker seen …` from a race or
   logs `marker gone: resume by hand …`; require a documented marker-gone observation or the documented paused state;
   a `FORCED` line is a STOP. Record the before/after `watch.log` lines and any STOP files it touched (expected: the
   Track S watcher may touch `STOP` beside its manifests; no other path). Preserve all pre-existing STOP files.
4. **Post-state read-only check**: no compute apps/llm processes, lease free, marker absent, marker-retirement files
   present, batch tree intact, `_to_delete/` contains the retired marker name, every other scene (6835, `_b`) intact.
5. **Complete-batch verifier + completion usage** (read-only, after normal completion; per the operator message v3 and
   handoff C §3):
   ```
   export AR_HARNESS_ROOT=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
   export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1
   export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
   cd "$CHECKOUT"
   python3 -B -m r1.exam.analyze b1 --batch "$BATCH" \
     --config "$CHECKOUT/r1/scripts/configs/exam_b1_v2.json" \
     --rule r1/exam/rules/x5_rule_v2.yaml \
     --rule-sha256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad \
     > "$RUN_DIR/complete_batch_verifier.json" 2> "$RUN_DIR/complete_batch_verifier.err"
   echo "rc=$?" > "$RUN_DIR/complete_batch_verifier.rc"
   python3 -B -m r1.scripts.b1_completion_usage --roots "$BATCH" --cap 16384 \
     > "$RUN_DIR/completion_usage.txt" 2>&1; echo "rc=$?" >> "$RUN_DIR/completion_usage.txt"
   ```
   A verifier failure is a STOP (preserve/report; no retry, no pin change). For `b1_completion_usage`, **exit 1
   (cap check FAIL) is expected in the new run by design** (truncated calls end at the cap) and is not a STOP; exit 2
   (inconsistent input) is reported.
6. **Report + STATUS + review**: write `docs/r1/reports/B1_C_RUN_20261112.md` (completion, verifier result, completion
   usage tables, marker retirement receipt, evidence paths/hashes, the anchor and candidate summary as instructed by
   handoff C §3, and any limits), a STATUS entry on `mac-b1-20261107`, and submit the record for a fresh independent
   review; only then are the B1 manifests/verifier result published. B2, X.7 and sweep 2 remain separately gated.
7. **Post-run restoration**: none is performed by this unit for Track S/P; Track P remains paused, Track S on TASL-7
   follows the separately reviewed host-move plan, and the TASL-2 scene stays preserved. Any restoration claimed by
   the operator later requires its own reviewed no-deletion procedure.

## 3. STOP conditions

Any precondition failure (including an abnormal run end, a marker/receipt mismatch, a `FORCED` watcher line, an
unexpected touched path, or a verifier failure), a dropped SSH whose completion cannot be established, or any
inconsistency: stop, preserve marker (if retirement has not succeeded), receipts, logs and partial files, report, and
do not retry, force, delete or restore.
