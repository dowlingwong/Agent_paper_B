# B1 `_d` post-run marker retirement and completion record — candidate for review (13 November 2026)

**Candidate for independent review; not an execution and not an authorization.** Post-run unit for run
`7912_20261113_d` only, to be executed **after** a verified normal completion of that run, before the Track S S0.5
resume. Adapted from the accepted `_c` unit (`proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`, `78c6fd7d`) to this run
and to hand-off D (`proposals/B1_RESTART_HANDOFF_D_20261113.md` §3, including the model-output rejection table).

## 0. Bindings
- Host TASL-7; run `7912_20261113_d`; HEAD `7912b7fffb4c1adeb39688bdb3852a919bdc71c8`.
  - `CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_7912b7fffb4c1adeb39688bdb3852a919bdc71c8/paper`
  - `HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness`
  - `RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d`
  - `BATCH=/home/dowling/exam-x/work/b1_7912_20261113_d`
  - `PY=/home/dowling/exam-x/work/venv/bin/python` (bare `python3` on TASL-7 is 3.10.12 and cannot import the chain)
- Marker creation receipt `$RUN_DIR/marker-receipt.json`; at execution assert its fields (dev 66306, ino 56261619,
  marker sha256 `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`, run_id `7912_20261113_d`, head
  `7912b7ff…`) and record the file's sha256. New files written by this unit: `marker-retirement_after_run.{json,rc,note,err}`.
- The `_d` handover predecessor record (`marker-retirement.json`/`.note` in `$RUN_DIR`) is not touched.
- **Not in scope:** no deletion; no retirement of pre-existing STOP files; no Track P restart; no Track S start (its own
  reviewed resume unit); no B2/X.7/sweep 2; no retry of B1; no pin/code change.
- Order deviation (as in the `_c` unit): verify → release lease (runner does) → retire marker → no S/P restoration →
  verifier/publish; recorded in the report.

## 1. Preconditions (fail-closed; any failure = STOP, preserve, report)
1. `$RUN_DIR/b1.exit` = `0`; the own tmux session `b1_7912_20261113_d` is gone (or runner exited); `$BATCH/batch_state.json`
   `status` = `COMPLETE`. Any STOP end → this unit does not apply (STOP procedure).
2. No `llama-server`, `exam_runner`, B1 worker of this run; no GPU compute app; `flock -n "$HOME/r1_locks/gpu0.lock" true`.
3. The live marker matches its creation receipt exactly (dev/ino/sha/content), and the receipt fields above.
4. Track P marker absent; P.3a absent; only `trks_watch` in default tmux (the watcher may be in its paused state with
   this marker present); no other priority marker.
5. **Import preflight before retirement**: from `$CHECKOUT` with `AR_HARNESS_ROOT=$HARNESS PYTHONDONTWRITEBYTECODE=1
   PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 GIT_CONFIG_NOSYSTEM=1
   GIT_CONFIG_GLOBAL=/dev/null`, `$PY -B -c 'import r1.exam.runtime, r1.exam.analyze, r1.scripts.b1_completion_usage; print("IMPORT_OK")'`.
6. Read-only capture first: `$RUN_DIR/b1.exit`; batch status/completed/interruptions; `b1.log`; tmux; pgrep;
   nvidia-smi; flock; checkout HEAD/clean; marker stat/sha/content; Track P marker; tail watch.log; a **baseline** of
   `$RUN_DIR` (all files) and of `$BATCH` excluding `_to_delete`, plus STOP content shas (absolute paths). Save
   `ssh.log`/`ssh.exit`/`SHA256SUMS` in a new `/private/tmp` capture; record the path.

## 2. Steps (TASL-7 via `ssh tasl7 'bash -s'`; `set -euo pipefail`, `umask 077`, `set -C`)
1. Capture (precondition 6).
2. Import preflight (precondition 5); failure = STOP, marker untouched.
3. **Retire the marker with its creation receipt** (renames; deletes nothing):
   ```
   TMP="$RUN_DIR/marker-retirement_after_run.json.tmp"
   test ! -e "$TMP" || { echo "STOP: leftover $TMP"; exit 1; }
   if "$PY" "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire --lock-dir "$HOME/r1_locks" \
        --receipt "$RUN_DIR/marker-receipt.json" > "$TMP" 2> "$TMP.err"; then rc=0; else rc=$?; fi
   printf '%s\n' "$rc" > "$RUN_DIR/marker-retirement_after_run.rc"
   [ "$rc" -eq 0 ] && [ -s "$TMP" ] || { echo "STOP: retire failed rc=$rc; partial kept as $TMP"; exit 1; }
   mv "$TMP" "$RUN_DIR/marker-retirement_after_run.json"
   mv "$TMP.err" "$RUN_DIR/marker-retirement_after_run.err"   # retained (no deletion)
   printf 'source_receipt=%s\nsource_receipt_sha256=%s\n' "$RUN_DIR/marker-receipt.json" \
     "$(sha256sum "$RUN_DIR/marker-receipt.json" | cut -d' ' -f1)" > "$RUN_DIR/marker-retirement_after_run.note"
   test ! -e "$HOME/r1_locks/trackx_evidence.active" || { echo 'STOP: marker still present'; exit 1; }
   ```
4. Observe the watcher (lines after the pre-retire count; up to 90 s): a new `marker gone: resume by hand` line, or the
   documented already-paused state; a new `FORCED` is a STOP. Record any touched path (pre-existing STOP mtime-only is
   allowed; content/identity must be unchanged; no new/deleted paths).
5. Post-state: marker absent; the four `marker-retirement_after_run.*` files present; creation receipt unchanged; batch
   tree intact; baseline comparison: `$RUN_DIR` unchanged except the four new files, `$BATCH` unchanged, STOP
   content/identity unchanged; no processes; lease free.
6. **Complete-batch verifier + completion usage + candidate halves** (read-only):
   ```
   cd "$CHECKOUT"
   "$PY" -B -m r1.exam.analyze b1 --batch "$BATCH" \
     --config "$CHECKOUT/r1/scripts/configs/exam_b1_v2.json" \
     --rule r1/exam/rules/x5_rule_v2.yaml \
     --rule-sha256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad \
     > "$RUN_DIR/complete_batch_verifier.json" 2> "$RUN_DIR/complete_batch_verifier.err"
   echo "rc=$?" > "$RUN_DIR/complete_batch_verifier.rc"
   "$PY" -B -m r1.scripts.b1_completion_usage --roots "$BATCH" --cap 16384 > "$RUN_DIR/completion_usage.txt" 2>&1
   echo "rc=$?" >> "$RUN_DIR/completion_usage.txt"
   "$PY" -B -m r1.scripts.b1_candidate_halves --work "$BATCH" > "$RUN_DIR/candidate_halves.txt" 2>&1
   echo "rc=$?" >> "$RUN_DIR/candidate_halves.txt"
   ```
   Verifier failure = STOP (preserve/report; no retry/pin change). Completion-usage exit 1 (cap check FAIL) is expected
   by design and not a STOP; exit 2 (inconsistent input) is reported. Candidate halves is descriptive.
7. **Report + STATUS + review**: write `docs/r1/reports/B1_D_RUN_20261113.md` on `mac-b1-20261107`: completion evidence,
   verifier result, completion-usage tables, candidate halves, **model-output rejections by check** (from each root's
   `b1_proposals.jsonl` / manifest `proposal_journal`; the same counts feed the appendix draft
   `reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md`), marker retirement receipts, capture paths+hashes, order
   deviation, limits. Add a STATUS entry, commit with author+committer Dowling Wong, push to `mac-b1-20261107`, verify
   the remote tip, and submit the record for a fresh independent review; only then publish the B1 manifests/verifier.
8. No Track S/P restoration here; Track S resumes under its separately reviewed unit; Track P remains paused.
