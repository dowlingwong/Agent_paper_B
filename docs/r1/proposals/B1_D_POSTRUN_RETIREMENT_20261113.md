# B1 `_d` post-run marker retirement and completion record — candidate for review (13 November 2026, rev 2)

**Candidate for independent review; not an execution and not an authorization.** Post-run unit for run
`7912_20261113_d` only, to be executed **after** a verified normal completion of that run and before the Track S S0.5
resume. Authority: `proposals/B1_OPERATOR_MESSAGE_V3_20261107.md` "Normal completion",
`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` §"Normal completion versus STOP", and
`proposals/B1_RESTART_HANDOFF_D_20261113.md` §3 (including the model-output rejection table). Adapted from the accepted
`_c` unit (`proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`, `78c6fd7d`); rev 2 fixes the round-1 review.

## 0. Bindings
- Host TASL-7; run `7912_20261113_d`; HEAD `7912b7fffb4c1adeb39688bdb3852a919bdc71c8`.
  - `CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_7912b7fffb4c1adeb39688bdb3852a919bdc71c8/paper`
  - `HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness`
  - `RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d`
  - `BATCH=/home/dowling/exam-x/work/b1_7912_20261113_d`
  - `PY=/home/dowling/exam-x/work/venv/bin/python` (bare `python3` on TASL-7 is 3.10.12 and cannot import the chain)
- Marker creation receipt `$RUN_DIR/marker-receipt.json`; at execution assert its fields (dev 66306, ino 56261619,
  marker sha256 `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`, run_id `7912_20261113_d`, head
  `7912b7ff…`), record the file's sha256, and pin the expected dev/ino/sha in the retirement assertion.
  New files: `marker-retirement_after_run.{json,rc,note,err}`.
- The `_d` handover predecessor files (`marker-retirement.json`/`.note` in `$RUN_DIR`) are not touched.
- **Not in scope:** no deletion; no retirement of pre-existing STOP files; no Track P restart; no Track S start (its own
  reviewed resume unit); no B2/X.7/sweep 2; no retry of B1; no pin/code change. Order deviation: verify → release lease
  (runner does) → retire marker → **no S/P restoration** → verifier/publish (recorded in the report).

## 1. Preconditions (fail-closed; any failure = STOP, preserve, report)
1. `$RUN_DIR/b1.exit` = `0`; the own tmux session `b1_7912_20261113_d` is gone (or runner exited);
   `$BATCH/batch_state.json` `status` = `COMPLETE`; `interruptions` is empty; `$RUN_DIR/b1.log` has no `STOP:` line and
   no `B1_EXIT=1`. Any STOP end → this unit does not apply (STOP procedure).
2. No `llama-server`, `exam_runner`, B1 worker of this run; no GPU compute app; `flock -n "$HOME/r1_locks/gpu0.lock" true`.
3. The live marker matches its creation receipt exactly (dev 66306, ino 56261619, sha256 `60cd40fb…`,
   content run_id/head) and the receipt fields above.
4. Track P marker absent; P.3a absent; only `trks_watch` in default tmux (the watcher is in its paused state with this
   marker present); no other priority marker.
5. **Import preflight before retirement**: from `$CHECKOUT` with `AR_HARNESS_ROOT=$HARNESS PYTHONDONTWRITEBYTECODE=1
   PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 GIT_CONFIG_NOSYSTEM=1
   GIT_CONFIG_GLOBAL=/dev/null`, `$PY -B -c 'import r1.exam.runtime, r1.exam.analyze, r1.scripts.b1_completion_usage; print("IMPORT_OK")'`.
6. Read-only capture first: `b1.exit`; batch status/completed/interruptions; `b1.log`; tmux; pgrep; nvidia-smi; flock;
   checkout HEAD/clean; marker stat/sha/content; Track P marker; tail watch.log; **baseline** of every `$RUN_DIR` file,
   every `$BATCH` file except `_to_delete` (stated exclusion), and STOP content shas with absolute paths; `to_delete`
   listing. Save `ssh.log`/`ssh.exit`/`SHA256SUMS` in a new `/private/tmp` capture; record the path.

## 2. Steps (TASL-7 via `ssh tasl7 'bash -s'`; each block self-contained)
1. **Capture** (precondition 6; `set -u` only).
2. **Import preflight** (precondition 5; `set -u`); failure = STOP, marker untouched.
3. **Retire the marker with its creation receipt** (renames; deletes nothing):
   ```
   set -euo pipefail; umask 077; set -C
   RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d
   CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_7912b7fffb4c1adeb39688bdb3852a919bdc71c8/paper
   PY=/home/dowling/exam-x/work/venv/bin/python
   TMP="$RUN_DIR/marker-retirement_after_run.json.tmp"
   ERRF="$RUN_DIR/marker-retirement_after_run.err"
   test ! -e "$TMP" || { echo "STOP: leftover $TMP"; exit 1; }
   test ! -e "$ERRF" || { echo "STOP: leftover $ERRF"; exit 1; }
   test ! -e "$RUN_DIR/marker-retirement_after_run.json" || { echo "STOP: final already exists"; exit 1; }
   if "$PY" "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire --lock-dir "$HOME/r1_locks" \
        --receipt "$RUN_DIR/marker-receipt.json" > "$TMP" 2> "$ERRF"; then rc=0; else rc=$?; fi
   printf '%s\n' "$rc" > "$RUN_DIR/marker-retirement_after_run.rc"
   [ "$rc" -eq 0 ] && [ -s "$TMP" ] || { echo "STOP: retire failed rc=$rc; partial kept as $TMP"; exit 1; }
   mv "$TMP" "$RUN_DIR/marker-retirement_after_run.json"
   printf 'source_receipt=%s\nsource_receipt_sha256=%s\n' "$RUN_DIR/marker-receipt.json" \
     "$(sha256sum "$RUN_DIR/marker-receipt.json" | cut -d' ' -f1)" > "$RUN_DIR/marker-retirement_after_run.note"
   test ! -e "$HOME/r1_locks/trackx_evidence.active" || { echo 'STOP: marker still present'; exit 1; }
   ```
4. **Observe the watcher** (lines after the pre-retire count; up to 90 s): require a new `marker gone: resume by hand`
   line **naming no new marker**, or the documented already-paused state after that wait; any new
   `priority marker seen` must name `trackx_evidence.active`; any `FORCED` is a STOP. Record touched paths: pre-existing
   STOP mtime-only allowed (content/identity unchanged; no new/deleted paths); everything else is a STOP. Re-check the
   marker absence and creation receipt after the observation.
5. **Post-state**: marker absent; the four `marker-retirement_after_run.*` present; creation receipt unchanged (dev/ino/sha);
   the retired name appears in `~/r1_locks/_to_delete/` with content sha `60cd40fb…`; batch tree intact; baseline compare:
   `$RUN_DIR` unchanged except the four new files, `$BATCH` unchanged, STOP content/identity unchanged; no processes;
   lease free.
6. **Complete-batch verifier + completion usage + candidate halves** — run as a **self-contained block without `set -e`**
   (`set -uo pipefail`), with the harness env exported; every rc captured and interpreted:
   ```
   set -uo pipefail
   CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_7912b7fffb4c1adeb39688bdb3852a919bdc71c8/paper
   HARNESS=/home/dowling/r1_b1_engineering/b1_harness_offline_stage_20261107_a/harness
   RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_7912_20261113_d
   BATCH=/home/dowling/exam-x/work/b1_7912_20261113_d
   PY=/home/dowling/exam-x/work/venv/bin/python
   export AR_HARNESS_ROOT="$HARNESS" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
   export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
   cd "$CHECKOUT"
   "$PY" -B -m r1.exam.analyze b1 --batch "$BATCH" \
     --config "$CHECKOUT/r1/scripts/configs/exam_b1_v2.json" --rule r1/exam/rules/x5_rule_v2.yaml \
     --rule-sha256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad \
     > "$RUN_DIR/complete_batch_verifier.json" 2> "$RUN_DIR/complete_batch_verifier.err"; VRC=$?
   printf '%s\n' "$VRC" > "$RUN_DIR/complete_batch_verifier.rc"
   "$PY" -B -m r1.scripts.b1_completion_usage --roots "$BATCH" --cap 16384 > "$RUN_DIR/completion_usage.txt" 2>&1; URC=$?
   echo "rc=$URC" >> "$RUN_DIR/completion_usage.txt"
   "$PY" -B -m r1.scripts.b1_candidate_halves --work "$BATCH" > "$RUN_DIR/candidate_halves.txt" 2>&1; HRC=$?
   echo "rc=$HRC" >> "$RUN_DIR/candidate_halves.txt"
   printf 'VERIFIER_RC=%s USAGE_RC=%s HALVES_RC=%s\n' "$VRC" "$URC" "$HRC"
   ```
   A verifier `VRC != 0` (or invalid JSON) is a STOP: preserve/report; do not retry or change the pin. `URC = 1`
   (cap check FAIL) is **expected by design** and not a STOP; `URC = 2` (inconsistent input) is reported. `HRC != 0`
   is reported (descriptive).
7. **Report + STATUS + review**: write `docs/r1/reports/B1_D_RUN_20261113.md` on `mac-b1-20261107`: completion evidence;
   verifier; completion-usage tables; candidate halves; **model-output rejections by candidate and mode** with columns
   `directive_symbol_differs`, `directive_new_differs`, `truncated`, `context_overflow`, `unencodable_summary`,
   `harness_precondition`, `d25_inactive_key`, `not_applicable` (from each root's `b1_proposals.jsonl` / manifest
   `proposal_journal`; same counts feed `reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md`); `scripted_minus_random`
   from `batch_state.json` `anchor_gate.scripted_minus_random`; marker retirement receipts; capture paths+hashes; order
   deviation; limits. Add a STATUS entry, commit with author+committer Dowling Wong, push to `mac-b1-20261107`, verify
   the remote tip, submit for a fresh independent review; only then publish the B1 manifests/verifier.
8. No Track S/P restoration here; Track S resumes under its separately reviewed unit.

## 3. STOP conditions
Any precondition failure (abnormal end, marker/receipt mismatch, a new `FORCED` watcher line, an unexpected touched
path, a verifier failure, a baseline difference), a dropped SSH whose completion cannot be established, or any
inconsistency: stop, preserve marker (if retirement did not succeed), receipts, logs and partial files, report; no
retry, force, delete or restore. If retirement succeeded but a later step fails, keep the marker retirement receipt and
report; do not attempt to recreate the marker.
