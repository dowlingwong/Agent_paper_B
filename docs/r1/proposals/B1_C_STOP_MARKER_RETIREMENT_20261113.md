# B1 `_c` STOP-case Track X marker retirement — candidate for review (13 November 2026)

**Candidate for independent review; not an execution and not an authorization.** This is a **new** unit authorized by
the author's chat message of 13 Nov 2026 (relayed by the operator, decision recorded in
`proposals/PLAN_ROW_R1-TRACKS-DIGITS-HOSTMOVE_REV_20261113.md` draft): B1 `_c` ending in a STOP still allows the Track S
`digits_mlp` host move to TASL-7, and **first** the `_c` Track X marker may be retired in the STOP state, renaming it
(`_to_delete/`), keeping the creation receipt and a retirement receipt, **without touching the `_c` STOP scene at all**.
It does not retry B1, does not start Track S by itself, and does not change any pin.

## 0. Bindings

- Host TASL-7; run `4b31_20261112_c` (HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`), STOPPED at
  2026-11-13T03:01:55Z in `olmo31_32b/b1/off/openml_credit_approval__s9002` trial-020 (proposal-integrity guard).
- `RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c`;
  `CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper`;
  `PY=/home/dowling/exam-x/work/venv/bin/python`.
- Marker creation receipt `$RUN_DIR/marker-receipt.json` (file sha256
  `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`; dev 66306, ino 56261618, marker sha256
  `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, run `4b31_20261112_c`, head `4b312844…`).
- The `_c` handover dir already contains the `_b`→`_c` transition files `marker-retirement.json`/`.note`; this unit
  writes **different** names (`marker-retirement_stop.json`, `marker-retirement_stop.note`) so nothing is overwritten.

## 1. Preconditions (fail-closed; any failure = STOP, preserve, report, no retirement)

1. The run is in the verified STOP state: `$RUN_DIR/b1.exit` = `1`; `batch_state.json` `status` = `STOPPED`;
   the `interruptions` entry is the proposal-guard unit; no `exam_runner`/`llama-server` process; no GPU compute app;
   `gpu0.lock` free; no tmux B1 session.
2. The live marker still matches the creation receipt exactly (dev 66306, ino 56261618, sha256 `f8c8624f…`,
   content run_id `4b31_20261112_c`/head `4b312844…`); `b1_o2_marker.py retire` will check this again.
3. Track P marker is absent and P.3a is stopped/absent; no other priority marker or unrelated Track S collector is
   running; the Track S watcher `trks_watch` is alive.
4. A read-only capture of the STOP state exists (the accepted STOP report's capture
   `docs/r1/reports/b1_stop_4b31_20261112/` plus a fresh `capture-stop-retirement-*.txt` with the current marker stat,
   `b1.exit`, batch state, `_to_delete` listing and watcher log line count). Nothing in the STOP scene is modified.

## 2. Steps (exact; TASL-7, via `ssh tasl7 'bash -s'`; `set -euo pipefail`, `umask 077`, `set -C`)

1. **Capture** (read-only): `b1.exit`; batch `status/completed/interruptions`; marker stat/sha256/content; `_to_delete`
   listing; `tmux ls`; `pgrep -af 'exam_runner|llama-server'`; `nvidia-smi --query-compute-apps`; `flock -n
   "$HOME/r1_locks/gpu0.lock" true`; `wc -l < watch.log` (pre-retire line count). Save `ssh.log`, `ssh.exit`,
   `SHA256SUMS`; record the capture path.
2. **Retire the marker with its creation receipt** (renames; deletes nothing; the STOP scene is not touched):
   ```
   set -euo pipefail; umask 077; set -C
   RUN_DIR=/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c
   CHECKOUT=/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514/paper
   PY=/home/dowling/exam-x/work/venv/bin/python
   TMP="$RUN_DIR/marker-retirement_stop.json.tmp"
   test ! -e "$TMP" || { echo "STOP: leftover $TMP"; exit 1; }
   if "$PY" "$CHECKOUT/r1/scripts/b1_o2_marker.py" retire \
        --lock-dir "$HOME/r1_locks" --receipt "$RUN_DIR/marker-receipt.json" > "$TMP" 2> "$TMP.err"; then
     rc=0
   else
     rc=$?
   fi
   printf '%s\n' "$rc" > "$RUN_DIR/marker-retirement_stop.rc"
   if [ "$rc" -ne 0 ] || [ ! -s "$TMP" ]; then
     echo "STOP: retire failed rc=$rc; partial output kept as $TMP"; exit 1
   fi
   mv "$TMP" "$RUN_DIR/marker-retirement_stop.json"
   mv "$TMP.err" "$RUN_DIR/marker-retirement_stop.err"   # retained (no deletion)
   printf 'source_receipt=%s\nsource_receipt_sha256=%s\n' \
     "$RUN_DIR/marker-receipt.json" "$(sha256sum "$RUN_DIR/marker-receipt.json" | cut -d' ' -f1)" \
     > "$RUN_DIR/marker-retirement_stop.note"
   test ! -e "$HOME/r1_locks/trackx_evidence.active" || { echo 'STOP: marker still present'; exit 1; }
   ```
   A receipt mismatch or retirement failure is a STOP: preserve everything (including any partial `.tmp`), report;
   no force, no delete, no retry. The author's 13 Nov correction to this unit: a leftover `$TMP` at the start is
   a STOP (never removed), and the success-path `$TMP.err` is **renamed** to
   `$RUN_DIR/marker-retirement_stop.err` and retained (never removed).
3. **Verify and observe**: the retired name appears in `~/r1_locks/_to_delete/`; the marker is absent; read the
   watcher transition using only lines after the pre-retire line count (a new `marker gone: resume by hand` line, or
   the documented already-paused state; a new `FORCED` line is a STOP); record any STOP file the watcher touched
   (expected: beside its manifests; pre-existing STOP files are preserved).
4. **Post-state check (read-only)**: marker absent; retirement `.json`/`.rc`/`.note` present and the retained
   `.err` file present; creation receipt still
   present unchanged; `_to_delete` contains the retired name; the entire `_c` STOP scene (batch dir, unit logs,
   `root_events/trials`, `node/`, `b1.log`, `b1.exit`, `_c` handover, staging checkout) is byte-untouched (compare the
   capture's file list/hashes; no writes into the batch or unit dirs); no processes; lease free.
5. **Record**: append a short section to the `_c` STOP report or a new `reports/B1_C_STOP_MARKER_RETIREMENT_20261113.md`
   with the capture path, retirement receipt/note hashes, watcher observation, post-state verification and the
   explicit statement that the `_c` STOP scene was not modified; publish a STATUS entry; submit for a fresh
   independent review. **Track S does not start in this unit**; the host move follows its own reviewed record.

## 3. STOP conditions

Any precondition failure, receipt mismatch, retire failure, `FORCED` watcher line, unexpected touched path, modified
STOP-scene file, or ambiguity about the capture: stop, preserve (marker if retirement did not succeed; receipts; logs;
partial files), report; no retry, no force, no delete, no restore.
