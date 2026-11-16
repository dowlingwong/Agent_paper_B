# B1 `_c` post-run marker retirement and completion record — candidate for review (12 November 2026, rev 4)

**Candidate for independent review; not an execution and not an authorization.** This is the post-run unit for run
`4b31_20261112_c` only, to be executed **after** a verified normal completion of that run on **TASL-7** and **before**
the Track S `digits_mlp` host-move run. It follows `proposals/B1_OPERATOR_MESSAGE_V3_20261107.md` "Normal completion",
`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` §"Normal completion versus STOP", and
`proposals/B1_RESTART_HANDOFF_C_20261111.md` §3/§4. The author agreed on 12 Nov that the Track X marker is a
cooperative lock, not evidence, and can be renamed (not deleted) with its receipt (PLAN row
`R1-EXAM-B1-TRUNCATION-INVALID` rationale). Rev 2 fixes the round-1 review: the verifier/usage interpreter must be
the frozen venv used by the runner (bare `python3` on TASL-7 is 3.10.12 and cannot import the chain), and the import
preflight must precede the marker retirement; it also fixes the missing `set -eu`/rc gates, `$CHECKOUT` definition,
watcher-line scoping, the report extras and the flock probe. **Rev 3** makes the retire rc gate reachable under
`set -e` with a tmp-then-mv and no zero-length final receipt, records the pre-retire watch.log line count, defines
the step-6 paths, checks the three artifacts and fixes the report citations. **Rev 4** is title/changelog and the
leftover wording only, plus `umask 077` and removal of the success-path `.tmp.err`.

## 0. Bindings and scope

- Host **TASL-7**; run `4b31_20261112_c`; HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`.
  - `CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`
  - `HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness`
  - `RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`
  - `BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c`
  - `PY=/home/dowling/exam-x/work/venv/bin/python` (the runner/worker venv; bare `python3` on TASL-7 is 3.10.12 and
    fails `import r1.exam.runtime` with `ModuleNotFoundError: strenum` — never use it here)
- Marker creation receipt `$RUN_DIR/marker-receipt.json` (file SHA-256
  `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`; dev 66306, ino 56261618, marker SHA-256
  `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, run_id `4b31_20261112_c`, head
  `4b312844…`). The `_b`→`_c` transition files already in `$RUN_DIR` (`marker-retirement.json`, `.note`) are **not**
  touched; this unit writes new `*_after_run.*` names.
- **Not in scope:** no deletion; no retirement of pre-existing STOP files; no Track P restart; no Track S start (its
  separately reviewed host-move plan); no B2/X.7/sweep 2; no retry of B1; no change to pins or code.
- **Recorded deviation:** the operator message's order is verify → release lease → retire marker → restore prior
  Track S/P state → verifier/publish. This unit performs **no S/P restoration** (there is no prior Track S run on
  TASL-7 to restore and Track P stays paused), so the verifier runs after the retirement with no restoration step;
  the deviation is stated in the post-run report.

## 1. Preconditions (fail-closed; any failure = STOP, preserve scene, report)

1. `$RUN_DIR/b1.exit` exists and contains `0`; the own tmux session `b1_4b31_20261112_c` is gone (or the runner
   process has exited) and `$BATCH/batch_state.json` reads `status` = `COMPLETE` (normal completion). If the run
   ended in a STOP (non-zero exit, `STOPPED` state, interruptions, or a `b1.log` STOP line), **this unit does not
   apply** — use the B1 STOP procedure (preserve, report, no retirement).
2. No `llama-server`, no `exam_runner`, no B1 worker process of this run; `nvidia-smi` lists no compute apps; the
   cooperative lease is free: `flock -n "$HOME/r1_locks/gpu0.lock" true` succeeds.
3. The live marker matches its creation receipt exactly (dev/ino/sha256/content), checked in Python and again by
   `b1_o2_marker.py retire`; the Track P marker is absent and P.3a is stopped/absent (read-only check).
4. No unrelated priority marker or Track S collector is active on TASL-7; the watcher `trks_watch` is alive.
5. **Interpreter/import preflight (before any retirement):** with `AR_HARNESS_ROOT=$HARNESS PYTHONDONTWRITEBYTECODE=1
   PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 GIT_CONFIG_NOSYSTEM=1
   GIT_CONFIG_GLOBAL=/dev/null`, from `$CHECKOUT`:
   `$PY -B -c 'import r1.exam.runtime, r1.exam.analyze, r1.scripts.b1_completion_usage; print("IMPORT_OK")'`.
   A failure here is a STOP **before** the marker is retired (no half-done state).
6. The completion evidence is captured read-only first into a new `/private/tmp` capture with `SHA256SUMS`.

## 2. Steps (exact; all on TASL-7)

1. **Completion capture (read-only).** `ssh tasl7 'bash -s'` with a script printing: `b1.exit`; `status/completed/
   interruptions` from `$BATCH/batch_state.json`; `$RUN_DIR/b1.log` (size/content); `tmux ls`; `pgrep -af
   'exam_runner|llama-server|r1\.tracks\.collect'`; `nvidia-smi --query-compute-apps=pid,process_name,used_memory
   --format=csv,noheader`; `flock -n "$HOME/r1_locks/gpu0.lock" true && echo LEASE-FREE || echo LEASE-HELD`;
   `git -C "$CHECKOUT" rev-parse HEAD` and `status --porcelain`; marker `stat`/`sha256sum`/`cat`; Track P marker;
   `wc -l < "$HOME/r1_tracks/logs/watch.log"` and its last line (recorded as the pre-retire line count for
   step 4). Save `ssh.log`/`ssh.exit`/`SHA256SUMS`; record the capture path.
2. **Import preflight (precondition 5).** If it fails: STOP, marker untouched.
3. **Retire the marker with its creation receipt** (only this run's marker; renames, deletes nothing):
   ```
   set -euo pipefail
   umask 077
   CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper
   RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c
   PY=/home/dowling/exam-x/work/venv/bin/python
   TMP="$RUN_DIR/marker-retirement_after_run.json.tmp"
   rm -f "$TMP"   # TASL-7 only; no pre-existing tmp is expected
   if "$PY" "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire \
        --lock-dir "$HOME/r1_locks" --receipt "$RUN_DIR/marker-receipt.json" > "$TMP" 2> "$TMP.err"; then
     rc=0
   else
     rc=$?
   fi
   printf '%s\n' "$rc" > "$RUN_DIR/marker-retirement_after_run.rc"
   if [ "$rc" -ne 0 ] || [ ! -s "$TMP" ]; then
     echo "STOP: retire failed rc=$rc; partial output kept as $TMP"; exit 1
   fi
   mv "$TMP" "$RUN_DIR/marker-retirement_after_run.json"
   rm -f "$TMP.err"   # success path only; nothing else removed
   printf 'source_receipt=%s\nsource_receipt_sha256=%s\n' \
     "$RUN_DIR/marker-receipt.json" "$(sha256sum "$RUN_DIR/marker-receipt.json" | cut -d' ' -f1)" \
     > "$RUN_DIR/marker-retirement_after_run.note"
   test ! -e "$HOME/r1_locks/trackx_evidence.active" || { echo 'STOP: marker still present'; exit 1; }
   ```
   Run this block on TASL-7 via `ssh tasl7 'bash -s'` (the `$...` paths are host paths). If the receipt does not
   match or the retire fails, STOP: preserve the scene, report; no force, no delete.
4. **Observe the watcher transition (scoped to new lines).** Record the line count of `watch.log` before the retire
   and read only lines after it. Require: no `FORCED` among the new lines; if a new `priority marker seen` line
   appears, it must name `trackx_evidence.active`; if a new `marker gone: resume by hand` line appears, record it; if
   no new line appears, re-establish the known paused state (watcher PID alive, marker absent, last line is the
   pre-existing paused line) and say so. Record any STOP file the watcher touched (expected: beside its manifests;
   pre-existing STOP files are preserved).
5. **Post-state read-only check**: no compute apps/llm processes, lease free, marker absent, the three `marker-retirement_after_run.json` / `.rc` / `.note` artifacts present, `_to_delete/` contains the retired
   name, `$BATCH` tree intact, all
   other scenes (6835, `_b`, `_c` handover) intact.
6. **Complete-batch verifier + completion usage** (read-only; after completion and marker retirement, no restoration):
   ```
   set -uo pipefail
   CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper
   RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c
   BATCH=/home/dowling/exam-x/work/b1_4b31_20261112_c
   PY=/home/dowling/exam-x/work/venv/bin/python
   export AR_HARNESS_ROOT=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
   export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
   export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
   cd "$CHECKOUT"
   "$PY" -B -m r1.exam.analyze b1 --batch "$BATCH" \
     --config "$CHECKOUT/r1/scripts/configs/exam_b1_v2.json" \
     --rule r1/exam/rules/x5_rule_v2.yaml \
     --rule-sha256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad \
     > "$RUN_DIR/complete_batch_verifier.json" 2> "$RUN_DIR/complete_batch_verifier.err"
   echo "rc=$?" > "$RUN_DIR/complete_batch_verifier.rc"
   "$PY" -B -m r1.scripts.b1_completion_usage --roots "$BATCH" --cap 16384 \
     > "$RUN_DIR/completion_usage.txt" 2>&1; echo "rc=$?" >> "$RUN_DIR/completion_usage.txt"
   ```
   A verifier failure (non-zero rc, or invalid JSON) is a STOP (preserve/report; no retry, no pin change). For
   `b1_completion_usage`, **exit 1 (cap check FAIL) is expected in the new run by design** (truncated calls end at
   the cap) and is not a STOP; exit 2 (inconsistent input) is reported.
7. **Report + STATUS + review**: write `docs/r1/reports/B1_C_RUN_20261112.md` on `mac-b1-20261107` with: completion
   and normal-end evidence; the complete-batch verifier result; the completion-usage tables; `scripted_minus_random`
   read from `batch_state.json` `anchor_gate.scripted_minus_random` (descriptive); the first-vs-second-half table from
   `"$PY" -B -m r1.scripts.b1_candidate_halves --work "$BATCH"` (read-only; not used by x5_rule_v2/finalists/STOPs);
   the marker retirement receipt/note and capture paths+SHA256; the order deviation (no S/P restoration); limits. Add
   a STATUS entry, cite this procedure commit, commit with author+committer Dowling Wong, push to `mac-b1-20261107`,
   verify the remote tip, and
   submit the record for a fresh independent review; only then publish the B1 manifests/verifier result.
8. **Post-run restoration**: none is performed by this unit for Track S/P; Track P remains paused; the TASL-7 Track S
   digits run follows its separately reviewed host-move plan; the TASL-2 scene stays preserved. Any later restoration
   requires its own reviewed no-deletion procedure.

## 3. STOP conditions

Any precondition failure (including an abnormal run end, an import-preflight failure, a marker/receipt mismatch, a
`FORCED` watcher line, an unexpected touched path, or a verifier failure), a dropped SSH whose completion cannot be
established, or any inconsistency: stop, preserve marker (if retirement has not succeeded), receipts, logs and
partial files, report, and do not retry, force, delete or restore.
