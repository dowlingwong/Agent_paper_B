# B2 post-run unit (normal completion and stopped-run paths)

**Scope.** Everything after the B2 runner exits, per `proposals/B2_HANDOFF_EXEC_20261115.md` §5.9/§6:
collect the §6 hand-back artifacts, run the **verified** B2 analysis (grid verifier first), aggregate the
authoritative invalid-trial counts, retire the run's marker, publish `B2 done`/`B2 stopped`, and hand the
report to independent review (STOP 6). The batch tree is read-only throughout; nothing is deleted.

## Normal completion (`b2.exit` = 0)

| step | script | gate |
|---|---|---|
| 1. collect + verify | `postrun/postrun_collect.sh` | `b2.exit` 0; creates `$RUN_DIR/postrun` itself (fresh, 0700, recorded in `CREATED.txt`); copies `batch_state.json`; runs `python -B -m r1.exam.analyze b2 --batch <tree> --config …/exam_b2_v2.json --rule r1/exam/rules/x5_rule_v2.yaml --rule-sha256 53018aa7…` (stdout `analysis.json`, stderr `analysis.err`, rc `analysis.rc`; the verified path runs `b2_batch.verify_b2_batch` and a non-zero rc is a STOP); copies the runner's `b2_manifests.json`; aggregates **each root manifest's `proposal_journal.rejected_by_check`** by the manifest's `candidate`/`mode` into `invalid_trials.json` (records roots, journals, journal rows); writes `SHA256SUMS` (verified) and finally `POSTRUN_COLLECT_OK`, built in a temp file and renamed atomically only after the hash-line checks (with the four artifact SHA-256s and `analysis_rc=0`); a partial receipt never becomes the final `POSTRUN_COLLECT_OK`. |
| 2. retire marker | `postrun/retire_marker.sh` | `b2.exit` 0; `POSTRUN_COLLECT_OK` with `analysis_rc=0`; marker present; no existing retirement receipt; no running `python … -B -m r1.scripts.exam_runner b2`; `b1_o2_marker.py retire` with the create receipt; the marker receipt's `run_id`/`head` must match; `SHA256SUMS` and the four-hash `POSTRUN_COLLECT_OK` are re-verified; verifies the marker is gone. |
| 3. publish done | `postrun/publish_status_done.sh <status-checkout> 8709_20261115_b2 <HEAD>` (**run on the Mac**; reads host gates over `ssh tasl7`) | clean `mac-b1-20261107` checkout whose HEAD equals origin; `b2.exit` 0; marker retirement receipt; `run_id`/`head` bound to the marker receipt; complete `POSTRUN_COLLECT_OK` artifact set (`analysis.json`, `invalid_trials.json`, `b2_manifests.json`, `batch_state.json`) with `analysis_rc=0`; appends `## 2026-11-15 — Track X B2 done` + Run/HEAD; author identity `Dowling Wong <wangdowling@gmail.com>`; no-force push; remote verification; no-clobber receipt. |

**Machine contexts.** `postrun_collect.sh` and both `retire_marker*.sh` run on TASL-7 (they need the host's run tree, marker and venv). `publish_status_done.sh` and `stopped/publish_status_stopped.sh` run **on the Mac**: the status checkout is local, and every host gate (`b2.exit`, marker retirement, the postrun receipts/`SHA256SUMS`, the marker-receipt `run_id`/`head`) is read over `ssh tasl7`. Both publish scripts fail closed if the host is unreachable; neither writes anything on the host.

**Hand-back to the author (§6):** run ID and run HEAD; the HEAD review; the author-gate receipt; the
preflight and handover receipts; the marker receipt and watcher log lines; the first monitor capture (all
in `B2_START_RECEIPT.md` and `$RUN_DIR`), plus the end artifacts `b2_manifests.json`, `batch_state.json`,
the verified `analysis.json`, and `invalid_trials.json`. The B2 report and its independent review (STOP 6)
are a **separate unit** after this collection.

## Stopped run (`b2.exit` ≠ 0, preserved, never retried)

| step | script |
|---|---|
| 1. collect evidence | `postrun/stopped/stopped_run_collect.sh` — creates `$RUN_DIR/postrun_stopped` (fresh); preserves `b2.log`, `batch_state.json`, the manifest/journal path lists, and `STOPPED_STATE.json`; writes a verified `SHA256SUMS` and `STOPPED_COLLECT_OK`, built in a temp file and renamed atomically. No analysis is required for a stopped run. |
| 2. retire marker | `postrun/stopped/retire_marker_stopped.sh` — only after the stopped collection, with no runner alive; writes `marker-retirement-stopped.json`. |
| 3. publish stopped | `postrun/stopped/publish_status_stopped.sh <checkout> 8709_20261115_b2 <HEAD>` — appends `## 2026-11-15 — Track X B2 stopped`; same identity/push/remote-verification guards. |

## Recovery (no deletion, no automatic retry)

- **Analysis or collection STOP:** the `postrun` dir keeps the partial evidence. Move it aside
  (`mv "$RUN_DIR/postrun" "$RUN_DIR/postrun.attempt-$(date -u +%Y%m%dT%H%M%SZ)"` — a move, not a delete),
  then re-run the same reviewed script; it creates a fresh `postrun` itself (if the operator pre-creates
  the dir, `CREATED.txt` still records the initialisation) and records the reason in the new attempt. A
  missing `b2_manifests.json` is not a pass: the collect and the verified analysis fail closed (there is
  no `absent.txt` record any more).
- **Stopped run:** use the stopped unit; do not run the normal-completion scripts (they require exit 0).
- **Marker retirement mismatch:** STOP; the marker and receipts are preserved; no retry and no manual
  cleanup.
- **Publication recovery (P-46):** if the STATUS commit/push/remote-verification fails, the STATUS change is
  local to the status checkout only; inspect it with normal git, revert it as a normal (non-force) change if
  needed, keep the local receipt, and re-run the publication step once the cause is fixed. Never force-push,
  never rewrite the status branch, and never delete the run receipts.
