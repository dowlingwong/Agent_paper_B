# Pre-execution review — B1 `_d` post-run marker retirement / completion unit

**Scope and independence.** I did not write the unit and took no part in its preparation. Reviewed candidate
`docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md` at repo `https://github.com/dowlingwong/Agent_paper_B.git`,
branch `trackS-ops-20261030`, commit `2c60b300f10b5243155534448b4f8bd660ca5a55` (tip; 84 lines; blob sha256
`7d1cde65778075f3a361cb842a2d6ab02bf7173932f2d7220e0bb558e496f7b9`). Nothing was executed. No TASL-7 access was
attempted (hosts unreachable in the author VPN window, per the brief); host-state claims below are checked against the
launch/precheck records, not live, and normal completion is still an execution precondition. I modified nothing under
`/Users/wongdowling/Documents/agent_paper_B`; I wrote only under `/Users/wongdowling/Documents/agent_sys_paper/` and
`/tmp`.

**Compared artifacts (exact).**

| artifact | commit / value | sha256 |
|---|---|---|
| this unit | `2c60b300` | `7d1cde65…96f7b9` |
| accepted `_c` unit | `78c6fd7d9286fa64840650baa7cb5ee0e6844cc6` | `b86d2386af67cd5096adb33da2b221d78002386ae29082b8c64e99efa99d08a9` |
| O2 draft | `999759b7fec7158e930950544db6aac4988569bb` | `6492f071bfbee35f24501da12743f8f6749bb10e8382c638ffd3e6d0670d8d9e` |
| hand-off D | `999759b7` | `7313603999ae9fa71c4a018b1d05adbf15aafa028814a32604f2d9662d11fffe` |
| run HEAD | `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` | — |
| STATUS launch entry | `6d6e8bba9336a161b8ddf5c5a22eadbd825669d2` | — |
| `r1/scripts/b1_o2_marker.py` @ run HEAD | `7912b7ff` | `8beedc2a0394f6153eb141f0e0854974887d4c9153f27a9f1fa5cc52532fc599` |
| `r1/exam/rules/x5_rule_v2.yaml` @ run HEAD | `7912b7ff` | `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad` |
| `r1/scripts/configs/exam_b1_v2.json` @ run HEAD | `7912b7ff` | `af57a42334198b2a0885c086d831ecee8c00ace274eea5705914793ac6288669` |

Launch record used for the `_d` bindings: `_xfer/b1_handover_d_review_20261113/B1_O2_HANDOVER_D_LAUNCH_PRECHECK_FINAL_20261113.md`
(marker dev `66306`, ino `56261619`, 82 B, sha `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`;
receipt `$RUN_DIR/marker-receipt.json` `a28f0f78…`; `$CHECKOUT`, `$HARNESS`, `$RUN_DIR`, `$BATCH`, STATUS `6d6e8bb…`).

## Check 1 — authority and exclusions: PASS (minor finding 8)

The unit is explicitly non-executing and non-authorizing (lines 3–4); it is scoped to run `7912_20261113_d`, only after a
verified normal completion and before the Track S S0.5 resume. It excludes STOP ends (line 26), deletion, pre-existing
STOP files, Track P restart, Track S start, B2/X.7/sweep 2, B1 retry and pin/code changes (lines 19–20), and states the
order deviation (no S/P restoration) honestly (lines 21–22, 84). The O2 draft's normal-completion order is "release the
lease, retire only this run's marker with its receipt, observe, restore prior S/P (under its own reviewed procedure),
then verify/publish"; this unit substitutes "no restoration, verifier after retirement" and records it, the same
deviation accepted for `_c`. Minor: the header does not cite the O2 draft's "Normal completion versus STOP" or
operator message v3 "Normal completion" directly, only the accepted `_c` and hand-off D §3.

## Check 2 — bindings, paths and names: PASS

HEAD `7912b7ff…`, run id `7912_20261113_d`, `$CHECKOUT` `…/b1_paper_final_7912b7ff…/paper`, `$HARNESS`
`…/b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`), `$RUN_DIR` `…/b1_handover_7912_20261113_d`, `$BATCH`
`/home/dowling/exam-x/work/b1_7912_20261113_d`, `$PY` the exam-x venv — all match the launch/precheck record and the
`_d` handover. The creation-receipt fields are correct: dev `66306`, ino `56261619`, marker sha `60cd40fb…`, run
`7912_20261113_d`, head `7912b7ff…`. The new names `marker-retirement_after_run.{json,rc,note,err}` do not collide with
the `_d` predecessor record already in `$RUN_DIR` (`marker-retirement.json`/`.note`, the `_c`→`_d` transition), which the
unit leaves alone; they also do not collide with the `_c` directory's `*_stop.*` files. Residual: the unit records but
does not pin the creation-receipt file sha (`a28f0f78…`); the helper itself checks dev/ino/marker sha, so this is
defence-in-depth only.

## Check 3 — safety: PASS with the minor gaps in findings 3–6, 9

The import preflight is before retirement (precondition 5 and step 2; failure = STOP, marker untouched). Capture and
baselines (all `$RUN_DIR` files, `$BATCH` excluding `_to_delete`, STOP content shas, a `/private/tmp` capture with
`SHA256SUMS`) precede mutation (precondition 6 / step 1). Only this run's marker is retired, with its creation receipt,
via `b1_o2_marker.py retire` — `renameat2(RENAME_NOREPLACE)` into `~/r1_locks/_to_delete/`, no deletion. The leftover-`$TMP`
check is a STOP, not an `rm`; `.err` is renamed/retained; the watcher is observed on new lines with `FORCED` as STOP and
mtime-only STOP touches allowed; post-state covers marker absence, the four new files, receipt/batch/STOP invariance, no
processes and the free lease. Gaps: the step-3 block is not self-contained and does not guard all leftover names;
the watcher check lacks the `_c` "new `priority marker seen` must name this marker" rule; the `_to_delete` archive is not
independently checked; and there is no consolidated STOP-conditions section (dropped SSH, post-retirement failure).

## Check 4 — commands: FAIL (major findings 1–2; minor findings 7)

CLI shapes are correct at the run HEAD: `r1/exam/analyze.py:334–346` takes `b1 --batch --config --rule --rule-sha256`
and calls read-only `b1_summary_verified`; the rule sha `53018aa7…` is the committed `x5_rule_v2.yaml`; the config is the
committed `exam_b1_v2.json`; `b1_completion_usage` takes `--roots/--cap` and returns 0/1/2 (1 = cap check FAIL);
`b1_candidate_halves` takes `--work`. The unit uses `$PY` (the exam-x venv), not bare `python3`, and correctly reads
completion-usage exit 1 as expected/not a STOP and exit 2 as reported. But the step preamble's `set -e` contradicts that
expectation, and the verifier is run without `AR_HARNESS_ROOT`; both are execution failures (findings 1–2). The
model-output rejection table points at the right sources (`b1_proposals.jsonl`, manifest
`proposal_journal.rejected_by_check`) but does not name the hand-off D §3 per-candidate/mode columns.

## Check 5 — consistency: PASS

The unit is a candidate only; it makes no claim of host verification or execution, and its host statements are the
launch-record bindings. The run status is the `6d6e8bb…` "Track X B1 running" entry for `7912_20261113_d` /
`7912b7ff…`. The order deviation is stated in the unit and assigned to the report. It accurately reflects what was
prepared; the only defects that would fail on TASL-7 after a normal completion are findings 1–2.

## Findings

1. **MAJOR — §2 step 6, lines 62–75, against the step preamble line 39: `set -e` aborts on the expected
   completion-usage exit 1.** The preamble says the steps run under `set -euo pipefail`, but
   `b1_completion_usage` returns 1 when the cap check fails, which lines 76–77 correctly call expected and not a STOP.
   Under `set -e` the shell exits right after line 71, so `echo "rc=$?"` (line 72), the candidate-halves run (73–74),
   and the report (78–83) never happen; the same applies to a verifier nonzero (the rc line 70 is skipped) and to
   `b1_candidate_halves` exit 2. The accepted `_c` step 6 deliberately used `set -uo pipefail` (no `-e`)
   (`78c6fd7d` lines 105 and 119–121). **Minimal fix:** run step 6 with `set -uo pipefail` (explicitly `set +e`), or
   wrap each command as `if …; then rc=0; else rc=$?; fi` / `… || rc=$?`, keeping the verifier rc gate and the
   expected-exit-1 reading.
2. **MAJOR — §2 step 6, lines 63–69: the verifier is run without `AR_HARNESS_ROOT=$HARNESS`.** `r1.exam.analyze b1`
   → `b1_summary_verified` → `b1_batch.verify_batch` imports `r1.exam.runtime` (`r1/exam/b1_batch.py:41`), whose
   module-level `from r1.exam.campaign import read_rows, write_json` (`r1/exam/runtime.py:19`) executes
   `HARNESS=import_harness()` (`r1/exam/campaign.py:12–13`). `harness_root()` falls back to
   `REPO.parent/autoresearch_harness` when `AR_HARNESS_ROOT` is unset (`r1/harness.py:12–17`), but the staged harness is
   `…/b1_harness_offline_stage_20261107_a/harness`; `import_harness()` raises "harness src not found"
   (`r1/harness.py:23–25`). Because retirement (step 3) precedes the verifier, this deterministically fails the
   verifier (`complete_batch_verifier.json` empty, rc non-zero) and produces a false STOP with the marker already
   retired. The import preflight (line 31) sets the variable only as a command prefix, so it does not persist into
   step 6. **Minimal fix:** insert the `_c` export block before `cd "$CHECKOUT"` (at minimum
   `export AR_HARNESS_ROOT=$HARNESS`, preferably also `GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
   PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`); keep
   `-B`.
3. **MINOR — §1 precondition 1, lines 25–26: the normal-completion test is thinner than `_c`.** It checks
   `b1.exit` = 0, session gone and `batch_state.json` `status` = `COMPLETE`, but not `interruptions` empty or the absence
   of a `b1.log` STOP line; the capture at line 34 records them, but there is no pass/fail. **Minimal fix:** add
   "`interruptions` empty and no `b1.log` STOP line" to precondition 1 (or make step 1 assert them).
4. **MINOR — §2 step 3, lines 39 and 44–54: the retirement block is not self-contained and its leftover guard is
   incomplete.** `set -euo pipefail`, `umask 077` and `set -C` are only in the preamble; the guard covers `$TMP` but
   not `$TMP.err`, `.rc`, `.note` or the four final names. Under `set -C` a leftover can abort after the marker is
   retired (e.g., at the `.rc` write, line 48), and `mv` can overwrite an existing final `.json`/`.err`. **Minimal
   fix:** put the shell settings in the block; test `$TMP.err` and the final names absent before starting (or use
   `mv -n`); keep STOP.
5. **MINOR — §2 step 4, lines 56–58: watcher scoping is weaker than `_c`.** It lacks the rule that a new
   `priority marker seen` line must name `trackx_evidence.active`, and the explicit "re-establish the paused state"
   test; a new priority marker (e.g., Track P) could be logged without a STOP. **Minimal fix:** add both, scanning only
   lines after the pre-retire count; keep `FORCED` as STOP.
6. **MINOR — §2 step 5, lines 59–61: the archive is not independently checked.** The `retired` name in the JSON is
   not confirmed on disk; `_c` checked `_to_delete/` contains it (`78c6fd7d` line 100). **Minimal fix:** read
   `retired` from `marker-retirement_after_run.json` and verify the `_to_delete/<name>` entry exists with the expected
   sha/identity (read-only).
7. **MINOR — §2 step 7, lines 78–83: the report spec is under-specified against hand-off D §3 and the appendix
   draft.** It does not require the rejection table per candidate and mode, with columns candidate / mode / proposer
   calls / rejected / by check, nor the descriptive anchor `scripted_minus_random` from `batch_state.json` ("as in
   hand-off `_c` §3: the anchors are descriptive"). **Minimal fix:** name the columns, the per-candidate/mode grouping,
   and the anchor read.
8. **MINOR — header, lines 3–6: the authority chain is incomplete.** It cites the accepted `_c` and hand-off D §3 but
   not the O2 draft's "Normal completion versus STOP" or operator message v3 "Normal completion", which the `_c` unit
   cited for the retirement itself. **Minimal fix:** cite them explicitly (with the `_c` commit or the O2/hand-off
   paths).
9. **MINOR — no §3 STOP conditions (the unit ends at step 8, line 84).** There is no consolidated rule for a dropped
   SSH whose completion cannot be established, or for a failure after retirement; `_c` §3 has one. **Minimal fix:**
   add the paragraph: stop, preserve the marker if retirement has not succeeded, retain receipts/logs/partial files,
   report, and do not retry, force, delete or restore.

## Residual notes

- No TASL-7 access was attempted; the launch record (final precheck) is the evidence for the marker/receipt, checkout,
  harness and STATUS bindings. Runtime preconditions remain execution checks and are not certified here.
- The run's normal completion (`b1.exit` 0, `COMPLETE`, no STOP end) is not established by this review; the unit is
  correctly gated on it and must not be executed on any STOP.
- The marker helper at `7912b7ff` is the same accepted helper (`8beedc2a…`); retirement is a no-replace rename into
  `_to_delete`, with no deletion, and the `_d` predecessor record in `$RUN_DIR` is left untouched.
- The accepted `_c` unit is at `78c6fd7d`; its step 6 exports `AR_HARNESS_ROOT` and uses `set -uo pipefail` (no `-e`),
  which are the two regression fixes needed in this unit.
- Placement: this unit is on `trackS-ops-20261030` while the report/STATUS go to `mac-b1-20261107` (the same split the
  `_c` review accepted as non-blocking); the report should cite this procedure commit.

VERDICT: changes required
