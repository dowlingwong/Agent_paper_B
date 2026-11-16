# B1 `_d` post-run unit — independent review round 2 (13 November 2026)

**Unit.** `docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md` rev 2, repo
`https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, tip
`491e12416622f2d84580995cf96c90ec3a922471` (file sha256
`f2be3f0fbe36daa68dd4d28e18f9f9c065c49c77f97a6dbde26ddf28143cc5b5`, 116 lines). Round 1 reviewed
`2c60b300f10b5243155534448b4f8bd660ca5a55`. Text-only review in a `/tmp` clone; TASL-7 not contacted (no host
command was run or attempted). The unit was treated as a document: nothing in it was executed.

## Round-1 findings

| # | Round-1 item | Status |
|---|---|---|
| 1 | MAJOR step 6 must not run under `set -e` | **FIXED.** `:75–97` is a self-contained `set -uo pipefail` block (`:78`) with per-command rc capture: `VRC=$?` (`:90`), `URC=$?` (`:92`), `HRC=$?` (`:94`) and a `VERIFIER_RC=… USAGE_RC=… HALVES_RC=…` line (`:96`). `:98–100`: verifier `VRC!=0` (or invalid JSON) = STOP; `URC=1` expected (cap FAIL) and not a STOP; `URC=2` reported; `HRC!=0` reported. No `set -e`, no bare `$?` under errexit. |
| 2 | MAJOR step 6 must export `AR_HARNESS_ROOT=$HARNESS` (plus git/bytecode/thread env) before `cd "$CHECKOUT"` | **FIXED.** `:79–85` define `CHECKOUT/HARNESS/RUN_DIR/BATCH/PY` and `export AR_HARNESS_ROOT="$HARNESS" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1` plus `OMP/OPENBLAS/MKL_NUM_THREADS=1`; `cd "$CHECKOUT"` is `:86`, after the exports. Matches the accepted `_c` step. |
| 3 | Minors | **FIXED.** Preconditions add empty `interruptions` and the `b1.log` "no `STOP:` line and no `B1_EXIT=1`" test (`:28–29`); the retirement block (`:48–64`) is self-contained and guards leftover `$TMP`, `$ERRF` and the final `.json` (`:54–56`) with no deletion anywhere; the watcher rule (`:66–70`) requires a new `marker gone: resume by hand` line naming no new marker or the already-paused state, requires any new `priority marker seen` to name `trackx_evidence.active`, makes any `FORCED` a STOP, and re-checks marker absence and the receipt; `:71–72` check the creation receipt (dev/ino/sha) and the `~/r1_locks/_to_delete/` archived name with content sha `60cd40fb…`; `:102–106` require per candidate/mode rejection columns and `scripted_minus_random` from `batch_state.json` `anchor_gate.scripted_minus_random`; `:5–7` cite operator-v3 "Normal completion", the O2 draft §"Normal completion versus STOP" and hand-off D §3; §3 STOP conditions exist (`:111–116`, incl. the retirement-succeeded-then-failure rule). |
| 4 | Diff scope / consistency | **PASS.** `git diff --name-status 2c60b300..491e124` lists only `docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md` (79+/47−); no code, pin, config or STATUS change. Both fenced blocks (`:48–64`, `:78–96`) pass `bash -n`. No secret material. The unit is prose; it executes nothing. |

## Checks run against the pinned checkout (read-only, in the clone)

- Run/HEAD bindings are self-consistent with hand-off D's staging convention; at the pinned run HEAD
  `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` the paths used by steps 3 and 6 exist: `r1/scripts/b1_o2_marker.py`,
  `r1/exam/analyze.py`, `r1/exam/runtime.py`, `r1/scripts/b1_candidate_halves.py`, `r1/scripts/b1_completion_usage.py`,
  `r1/scripts/configs/exam_b1_v2.json`, `r1/exam/rules/x5_rule_v2.yaml`.
- The pinned rule sha is correct: sha256 of `r1/exam/rules/x5_rule_v2.yaml` at `7912b7ff` is
  `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`, matching `:89`.
- The marker sha is correct: sha256 of `{"head": "7912b7fffb4c1adeb39688bdb3852a919bdc71c8", "run_id":
  "7912_20261113_d"}` + `\n` is `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`, matching `:18`,
  `:31` and `:72`. `b1_o2_marker.py retire` re-checks dev/ino/sha and renames (never deletes) into
  `_to_delete/trackx_evidence.active.<uuid>` via `renameat2(RENAME_NOREPLACE)`, so the post-state assertions are
  satisfiable.
- `r1.exam.analyze` accepts `b1 --batch … --config … --rule … --rule-sha256 …` and routes to `b1_summary_verified`
  (which only refuses sealed paths); running it after retirement is sound, as in the accepted `_c` unit.

## Residual notes (non-blocking)

1. **Report table column names (`:102–104`) should be reconciled at report time.** At the pinned checkout the
   rejection checks are the nine codes of `r1/exam/b1_proposal_precheck.CHECKS` and the manifest carries
   `proposal_journal.rejected_by_check`; the eight names listed include `unencodable_summary` (the field is
   `unencodable_reply`), mix journal outcomes (`harness_precondition`, `d25_inactive_key`, `not_applicable`) with
   rejection checks, and omit `directive_missing`, `directive_symbol_not_editable`, `directive_old_differs`,
   `replacement_escape`, `python_value_too_long`, `python_value_not_literal`, `python_value_not_finite_number`.
   The source named in the same sentence is correct, so the operator can tabulate `rejected_by_check` verbatim;
   this does not affect execution.
2. Step 3 guards `$TMP`, `.err` and the final `.json` but not leftover `.rc`/`.note`; `set -C` then makes such a
   leftover fail nonzero without a `STOP:` line. Fails closed (no overwrite), acceptable.
3. `:20` lists only the four `marker-retirement_after_run.*` files as new; step 6 adds five more
   (`complete_batch_verifier.json/.err/.rc`, `completion_usage.txt`, `candidate_halves.txt`). Step 5's baseline
   comparison precedes them, so there is no contradiction, but the operator should treat them as expected new files.

No remaining defect was found that would fail at runtime after a verified normal completion, and no round-1 finding
remains open.

VERDICT: accepted
