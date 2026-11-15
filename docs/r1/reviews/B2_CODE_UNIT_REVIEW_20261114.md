Reviewed base: 37282ec37a715feaaea48dd621ae08678424accc

# Track X B2 code unit — independent review record (14–15 November 2026)

Branch `mac-b2-code-20261114`, from the B1 `_d` run HEAD `7912b7ff`. Item 3 of `B2_HANDOFF_DRAFT_20261114.md` §0: B2 authority (x5_rule_v2, dated author PLAN rows, committed frozen B1 analysis), B2 through the reviewed B1 collector and observer, every B1 production protection for phase `b2`, the B2 grid verifier with the verified GPU-h tie-break, B2 ranking only on a verified grid, the marker phase; tests that the hand-off §6 STOPs fire in phase `b2`; B1 behaviour unchanged. Not armed. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`e0bda328`): changes requested (one B1 message in `exam_runner.evidence` changed and its base assertion rewritten; the GPU-h tie-break was neither verified nor disclosed).
- Round 2 (`37282ec3`): **accepted**. The B1 message and base assertion are restored; GPU-h is recomputed from the server intervals and the ranking uses only verified values; the verifier gains the B1 Stage A provenance, D28 and anchor checks; the author cap of 10 is enforced; tamper tests assert messages. 39 mutations tried, 32 killed; the 7 survivors are redundant or minor (recorded in round 2).

Accepted commit (round 2, last): 37282ec37a715feaaea48dd621ae08678424accc

Correction to the report at the accepted commit: report §5 still gives the round-1 full-suite figures. The round-2 figures are: base `7912b7ff` 30 failed / 1295 passed / 11 skipped; accepted commit 30 failed / 1449 passed / 11 skipped (+154 = the B2 tests), the same 30 failing test ids. Notes, not blocking: the b2 GPU-lease acquisition in `start()` and the CLI anchor check are not exercised by a test (server start refuses without the lease; the verifier checks the anchor); the production final-Y branch runs in no test (by reading it stops on a failed or non-finite seed); the invalid-trials row is checked for its ID, dated heading and the two rule IDs only.

The round texts are reproduced unchanged below.

---

# Independent review — B2 code unit, round 1

Reviewed commit: e0bda32800fadc72c424ffad3041df83bb3837f7
Base: 7912b7ff (the `_d` run HEAD, `ops-b1-restart-d-20261113`)
Branch: `mac-b2-code-20261114`
Verdict: changes requested

AI-assisted independent review (Claude). Not an author decision. I worked in a scratch `git archive` export at
`/tmp/rev_b2code` (since removed). I did not modify the worktree, commit or push. I did not read secrets or key files.

Sources I read: the report `docs/r1/reports/B2_CODE_UNIT_20261114.md`; `git diff 7912b7ff e0bda328`; the hand-off draft
`2120956c:docs/r1/proposals/B2_HANDOFF_DRAFT_20261114.md` (§0 item 3 and §6); the design
`origin/mac-b1-20261107:docs/r1/proposals/B2_GRID_VERIFIER_DESIGN_20261104.md`; the PLAN-row drafts on
`mac-b2-plan-20261114` @ `3533b545`; and `fcf52c09:docs/r1/reports/b1_d_20261113_evidence/complete_batch_verifier.json`.

## Summary

Most of the unit is sound:
- The B1 code paths are unchanged in every check, order, call and side effect except one message, which a base B1 test catches (BLOCKING 1).
- B2 goes through the same reviewed collector, worker-input check, observer context, runner protections and author gate as B1.
- The PLAN-row drafts pass the new gate.
- The full-suite claim matches the logs.

There are two blocking items:
1. A B1-path message changed, and a base B1 test assertion was edited to hide it. The report says no B1 behaviour changed.
2. The "not implemented" disclosure leaves out the design's GPU-hours verification. The B2 ranking tie-break uses the GPU-h value each manifest reports about itself, with no check.

## BLOCKING

### 1. A B1-path message changed in `exam_runner.evidence`, and a base B1 assertion was rewritten

`r1/scripts/exam_runner.py:329-330`: for phase `b1` with a rule other than v2, the message changes:
- base: `STOP: only x5_rule/v2 B1 evidence is implemented`
- tip: `STOP: only x5_rule/v2 B1/B2 evidence is implemented`

The base test `test_evidence_entry_refuses_b2_and_unreviewed_b1_rule` (7912b7ff `r1/tests/test_exam_core.py:376-382`) fails against the tip code at its first loop iteration, which is `phase='b1'`. I ran the base file against tip: 4 failures, and this is the only one that asserts B1 behaviour. The tip rewrites the test as `test_exam_core.py:376` (`match='only x5_rule/v2 B1/B2 evidence'`).

The STOP itself is unchanged, and from `main` the path is unreachable for B1 (`ExamRunner.start` refuses a non-v2 B1 rule first). It is still a B1 behaviour change. It contradicts two statements in the report:
- §0/§1: "No B1 behaviour is changed".
- §5: the four rewritten tests are described as the ones that "asserted the deliberate B2 STOPs". The b1 iteration of this test asserted B1.

**Fix.** Keep the base text when `phase=='b1'`, for example `'STOP: only x5_rule/v2 B1 evidence is implemented' if phase=='b1' else 'STOP: only x5_rule/v2 B1/B2 evidence is implemented'`. Restore the base test's b1 assertion unchanged and add the b2/stage-a cases separately.

### 2. GPU-h tie-break is unverified, and the "Not implemented" disclosure omits it

The design names the tie-break explicitly ("GPU-hours and tie-break"). It says the verifier must recompute each primary candidate's GPU-h from the server-interval records, must reject `None` or upper-bound values, and that "No tie ranking may use a merely self-reported or unknown cost".

The implementation does none of this:
- `b2_batch.verify_b2_batch` never checks `m['gpu_hours']`, `gpu_hours_status`, or `state['server_intervals']`.
- `analyze._b2_summary_v2` ranks on the manifest value (`r1/exam/analyze.py:346`) and sorts `None` last as `math.inf` instead of stopping.

Report §3 "Not implemented (as for B1)" lists only the authority anchor and the receiving commitment. B1 has no GPU-h tie-break, so "as for B1" does not cover this gap.

With the current single finalist (`gemma4_31b`) the tie-break never applies. The code is still the general ranking path, and the omission is not disclosed.

**Fix (minimum).** Add the GPU-h verification to the disclosure. Make the verified path STOP whenever the GPU-h would decide the order, that is, two primary rows with equal `final_y` and any `gpu_hours` that is unverified or `None`. Preferred: recompute from `batch_state.json` `server_intervals` (candidate, phase `b2`, mode `off`, closed intervals, `cost_is_upper_bound` false), as the design describes.

## NON-BLOCKING

### N1. Every other difference on or near the B1 path (reported as asked; none changes a phase-`b1` run)

- `PROTECTED_PHASES` / `('b1','b2')` substitutions in `runtime.py` (`save`, `start`, `_server`, `run_job`, `root`, `stop_service`, `close`) and in `exam_runner.py` (`evidence`, `_evidence_unreviewed`, `main`). For `b1`, every condition evaluates exactly as before. Messages built with `phase.upper()` or `label` give the base text for b1. Check order for b1 is unchanged: the removed b2 STOP at base `runtime.py:594-595` came before the b1 checks, and the new b2-v2 check sits after the b1-v2 check.
- `require_committed_b1_config(..., rel=B1_CONFIG_REL)` (`runtime.py:230-261`). With the default, the path, git calls and message texts are identical to the base (`label='B1'`).
- `author_gate` (`runtime.py:551-579`). The b1 branch, checks, order and messages are identical; `f'STOP: {phase.upper()} host or GPU UUID…'` gives the base text. Only the unknown-phase message changed (`runtime.py:556`).
- `campaign._verify_b1_worker_input` (`campaign.py:179-217`):
  - New leading guard `phase not in PHASE_CONFIG_REL` (`campaign.py:187-189`). It is unreachable for a phase-`b1` job. Before, a direct call with no `phase` was verified as B1; now it STOPs earlier.
  - For b1, the seed and audit comparisons are exactly the base ones (`cfg.get('instance_seeds',[])`, `cfg.get('audit_seeds')`, not `phase_seeds`). It calls `require_committed_b1_config` without `rel` and `author_gate(cfg,'b1',…)`, as `test_b1_worker_input_still_calls_the_b1_config_without_rel` confirms.
- `observer.authorized_b1_observer` (`observer.py:44-88`). For b1: identical comparisons, the sensitivity-node restriction kept (`observer.py:79`), and `author_gate(cfg,'b1',…)`. Only the non-B1/B2 message changed (`observer.py:48`).
- `campaign.collect` (`campaign.py:174-175`) and `_collect_b1_review` (`campaign.py:221`): only the messages for other phases changed.
- Marker (`b1_o2_marker.py:30-56,115-119`):
  - `create(..., phase='b1')` writes the identical heading by default.
  - The new invalid-phase `ValueError` runs before run-id validation. It is unreachable with the default.
  - The new CLI `--phase` defaults to `b1`.
- `analyze.main`: the new b2 branch comes before the b1 one; b1 is unaffected.
- I ran the B1 test files (`test_exam_b1_*`, `test_b1_*`, `test_exam_core`, `test_exam_x5_rule_v2`, `test_exam_cache_d3_guard`) at tip: 485 passed, 1 skipped. The base versions of the two modified files against tip: 4 failed, all expected; see BLOCKING 1 for the one that asserts B1.

### N2. Checks that `b2_batch.py` drops from `b1_batch.py` without a stated reason

I compared the two line by line. Everything else is carried over, or replaced by a B2 equivalent: phase, seeds 9201–9210, forced `off` primary, grid in place of the eligible set, and final-Y in place of the anchor gate.

Dropped:
- `stage_a_pass is True` and `stage_a_pass_source` provenance (`b1_batch.py:107-108`). B2 only checks `cid in eligible` (`b2_batch.py:74`).
- Candidate `d28_pass` and `thinking_on_d28` against the verified roots (`b1_batch.py:228-239`).
- `verify_anchor_reference(cfg)` (`b1_batch.py:243`), and `refuse_sealed` of `anchor_duplicate_reference.source` (`b1_batch.py:53`). The B2 author gate binds the anchor digest, and `main` verifies it at launch (`exam_runner.py:561`), but analysis does not.

The runner writes these fields into every B2 manifest (`exam_runner.py:451-469`), so they would be unverified if the B2 report quoted them. Either add the checks or state why they are omitted.

### N3. Verifier tests are not precise; many copied checks have no B2 test

Mutations in the scratch copy, run against `test_exam_b2_code_unit.py` and `test_exam_b2_batch_verify.py` (and, for the survivors, also `test_exam_b2_collect.py`, `test_exam_cache_d3_guard.py` and `test_exam_core.py`):

- **Killed:**
  - `_b2_author_rows` accepting two literals;
  - one-rule invalid row;
  - missing `batch_verification`;
  - B2 three-node check;
  - b2 workers binding;
  - existing-root preservation;
  - worker and observer B2 seeds;
  - job audit seeds;
  - rerun-finals cross-check;
  - extra roots;
  - cache evidence;
  - authorized HEAD;
  - rerun label;
  - root grid;
  - ranking finalist and cell cross-checks;
  - free-sensitivity refusal in `evidence`;
  - the CLI B2 config binding.
- **Survived** (no test fails when the check is removed), all in `b2_batch.py`:
  - the call `check_final_audit(root,node,seed)` (`:287`);
  - the manifest `final_audits` check (`:292`);
  - the primary-pairs coverage (`:297`);
  - the manifest `b1_analysis_sha256` (`:176`);
  - `all_false` cache (`:251`);
  - diagnostics (`:232`);
  - replay (`:266`);
  - the B1-analysis screen (`:149`);
  - budget (`:243`);
  - audits (`:286`);
  - D28 (`:261`);
  - observer journal (`:252`);
  - proposal journal (`:254`);
  - post-check (`:256`);
  - candidate audits and diagnostics (`:289`, `:302`);
  - harness pin (`:132`);
  - registry snapshot (`:140`);
  - binding (`:145`);
  - and changing `rel_tol=0.0` to `1e-3` (`:103`).

  `b2_batch` is a copy, not a shared object, so the B1 verifier tests do not cover it.

Why the final-Y tampers do not test what they claim:
- `test_partial_or_tampered_b2_batch_stops` uses `pytest.raises((ValueError, RuntimeError, KeyError))` without `match`.
- The `final_y` / `final_seed` / `final_instance` tampers are caught by the manifest cross-check, not by `check_final_audit`.
- The final-Y validation itself is covered only by the unit test `test_final_audit_checks`.
- The absolute-only tolerance is never tested near its boundary.

Recommend:
- add `match=` to each tamper;
- add a coherent root-plus-manifest tamper that only `check_final_audit` can catch;
- add the copied B1 tamper cases.

### N4. Runner-level B2 STOPs without tests

No test fails if any of these is removed:
- `exam_runner.py:362-364` (verified B1 analysis);
- `:365-367` (finalist list);
- `:374-377` (finalist missing from the registry or the Stage A set);
- `:561` (b2 `verify_anchor_reference`);
- the b2 GPU-lease acquisition in `ExamRunner.start` (`runtime.py:781-783`).

`test_b2_runner_lock_is_preserved` calls `claim_runner_lock(..., preserve_existing=True)` directly, so it does not exercise the b2 argument in `start` (`runtime.py:784`).

Removing lease acquisition still fails closed, because `_server` refuses without the lease (tested). The report §5 lists "runner lock, GPU lease" as runner protections tested in b2; that overstates what the tests exercise.

### N5. Limits of `_b2_author_rows`

- The invalid-trials row is accepted if the decision cell contains both IDs anywhere (`runtime.py:497`). A negated sentence would pass. This is the same class of limit as the B1 X5 row, and the process boundary is the author's review.
- The `undated` test case does not isolate the power row's date check. Removing `not power[0][0]` (`runtime.py:493`) survives, because the invalid row in that fixture is undated as well.
- The copy of the `_x5_author_row` structure rules in `_dated_author_decisions` is faithful.
- The drafts on `mac-b2-plan-20261114` are accepted, inserted into real PLAN §10 at 7912b7ff:
  - each of the four Chinese/English combinations;
  - the shared-table form;
  - with the X5 row still found.
- The drafts are refused for n = 5, and refused if both power blocks are pasted.

### N6. "Verified" B1 analysis is a structural check only

`runtime.py:517-520` and `exam_runner.py:362-364` only require `batch_verification` to be a dict. The author binds the exact file by sha (note plus config), so this is defence in depth.

Suggest also checking that the finalists are a subset of `batch_verification['eligible_candidates']` (present in the real `fcf52c09` file). Otherwise reword "verified complete-batch" in report §1/§2.

The real file (sha `07cb62de…`) passes every structural check: phase b1, EVIDENCE, rule sha `53018aa7…`, finalists `['gemma4_31b']`, row `b2_thinking_mode: off`.

### N7. The cap of 10 per node is not enforced in code

Author-signed line (a) caps the instance count at 10 per node. The code allows 1–89 (`runtime.py:40`, `:569`; `b2_batch.py:63`). Because the author row binds the exact n, any n above 10 needs the author's signature anyway. A `≤ 10` STOP would mirror the signed line.

### N8. `_b2_summary_v2` trusts a caller-supplied grid dict

`analyze.py:338-344` accepts any dict with `verified: True`. The function is private. The CLI and `b2_summary` cannot reach it without the verifier (individual-manifest v2 still STOPs), so this is acceptable. A proof object would be stronger.

### N9. Report wording

- **Rerun rule.** "Descriptive thinking-on rerun of the top three switchable finalists": the code reruns the switchable finalists among the first three (`rank<3 and switchable`, `b2_batch.py:79`, `exam_runner.py:412`). That is not the same as the top three switchable finalists.
- **"Real" collect test.** §5 calls `test_exam_b2_collect` "A real B2-phase root". It is DRYRUN:
  - `FixtureWorker` and fixture audits;
  - no `_verify_b1_worker_input`, editable preservation or `run_b1_audits`.

  The test docstring says so; the report table should too.
- **Where M17 is shown.** M17 in b2 is shown on the DRYRUN audit branch (`campaign.py:300`). The production final-Y line (`campaign.py:321`, `run_config(..., stop_on_invalid=True)`) runs in no test. By inspection it STOPs on a failed or non-finite seed (`r1/c3/audit.py:150-154`).
- **Track G.** The design's authorized-Track-G positive case is not implemented. The code refuses any non-protocol node, which is stricter. It could be disclosed.

### N10. Cosmetic

- B2 STOP messages in the observer still read "B1 observer …" (`observer.py:51-86`).
- `shutdown_writes` and `report_b1_stop_and_save` texts say "B1-owned" for b2.

### N11. Where the B2 thinking-on scope is enforced

The worker and the observer accept `mode: on` on any B2 node for any registry candidate (`observer.py:79`). The top-3 restriction is enforced only by the runner and by the verifier's exact grid, which refuses extra roots. This is acceptable.

## §6 coverage (phase b2)

| §6 class | Shown by |
|---|---|
| M2 truncation, M5–M9, M19 after trial 1, M20 as invalid trials (charged, journalled) | `test_exam_b2_collect::test_b2_invalid_trial_classes…` (b2, DRYRUN worker) |
| `max_completion_tokens` 16384, cache-false, journal before execution | `test_b2_root_completes…` (b2) |
| M19 at trial 1 | `test_b2_stop_classes_stop_the_root[m19_trial1]` |
| M18 transport | `[m18_transport]` |
| M15 observer | `[observer]` (HTTP 503) in b2. The 60 s timeout is phase-agnostic (`observer.py:156`); B1 test only |
| M17 audit failure | `[m17_audit]`, DRYRUN branch only (N9). Production `run_b1_audits` and `run_config` are phase-agnostic |
| Incomplete final-Y audit / M17 on 9201–9210 | `[final_y]` (DRYRUN). Production line correct by inspection only (N9) |
| Worker guard failure, M10 | Phase-agnostic `B1IntegrityWorker` and the proposal guard; no phase reads (statement accurate) |
| M16 replay | Phase-agnostic `replay_campaign`; B1 tests |
| M21 deadline | Phase-agnostic `run_job` (`runtime.py:992`); B1 tests |
| Missing `cache_prompt` evidence | Phase-agnostic `cache_prompt_evidence`; b2 verifier tamper `cache_event`. Not named in report §6 |
| Pin, sha, authority, host mismatch | `test_exam_b2_code_unit` author-gate, worker, observer and start tests (b2) |
| Existing production root on restart | `test_b2_existing_production_root_is_preserved`, `test_b2_start_refuses_an_existing_batch…` (b2) |

No §6 class is left without coverage. The gaps are the DRYRUN-only demonstrations and the untested runner checks (N4).

## Tests run (scratch export of e0bda328, harness pin a3fedbb, `/tmp/trackg_venv`)

- `test_exam_b2_code_unit.py`, `test_exam_b2_batch_verify.py`, `test_exam_b2_collect.py`: 123 passed.
- The B1 files plus the four modified tests (40 files: `test_exam_b1_*`, `test_b1_*`, `test_exam_core`, `test_exam_x5_rule_v2`, `test_exam_cache_d3_guard`): 485 passed, 1 skipped.
- Full-suite logs, not rerun:
  - `/tmp/pb/full_run7912.fail` and `/tmp/pb/full_b2code.fail` hold the same 30 ids.
  - Base: 1295 passed; tip: 1418 passed. The difference, 123, is the new B2 tests.
  - The failures are 16 namespace-fixture, 9 C3, 3 lease and 2 others, as the report states.

## What would make round 2 acceptable

1. Restore the B1 `evidence` message and the base B1 test assertion (BLOCKING 1). Reword the report's §5 description of the four rewritten tests.
2. Disclose the missing GPU-h verification, and STOP on a tie that an unverified or `None` GPU-h would decide, or implement the recomputation (BLOCKING 2).
3. Recommended, not required: N2, N3 (`match=` and a coherent final-Y tamper), N4, and the wording fixes in N6 and N9.

---

# Independent review: B2 code unit, round 2

Reviewed commit: 37282ec37a715feaaea48dd621ae08678424accc
Previous round: e0bda32800fadc72c424ffad3041df83bb3837f7 (`REVIEW_B2CODE_round1.md`, changes requested)
Base: 7912b7ff (`_d` run HEAD)
Verdict: accepted

This is an AI-assisted independent review (Claude), not an author decision. I worked in a scratch `git archive` export
at `/tmp/rev_b2code`, which I have removed. I did not modify the worktree, commit, or push, and I did not read secrets
or key files. I read `git diff e0bda328 37282ec3`: code, tests and report.

## Round-1 blocking findings

### 1. B1 `evidence` message: resolved

- `r1/scripts/exam_runner.py:329-331`: phase `b1` gets the base text, "STOP: only x5_rule/v2 B1 evidence is
  implemented". Other phases get "…B1/B2 evidence…".
- `test_exam_core.py:376-386` has the base test name back, and its b1 assertion is the base one unchanged. The b2 and
  stage-a cases follow it.
- Running the base 7912b7ff `test_exam_core.py` against this tip, the only failure is the base test's `phase='b2'`
  iteration (expected, since b2 is no longer refused outright). The b1 iteration passes.
- Mutating the b1 text back to "B1/B2" makes the restored assertion fail.

With this fixed, I find no remaining difference in any phase-`b1` path. The round-1 N1 list still describes the only
other changes: messages or guards that a b1 job cannot reach. The new author cap (`runtime.py:571-572`) is guarded by
`phase=='b2'`.

### 2. GPU-h tie-break: resolved

- **Recompute.** `b2_batch.verified_gpu_hours` (`b2_batch.py:114-128`) recomputes each primary candidate's GPU-h from
  `batch_state.server_intervals`, filtered on (candidate, `b2`, `off`). The interval schema it reads is the one the
  runner writes: `runtime.py:896` (`start`, `end`, `candidate`, `phase`, `mode`).
- **Refusals.** It STOPs on:
  - any upper-bound or recovered interval of the candidate in b2;
  - no closed interval, or an open or inverted one;
  - a manifest status other than `recorded_dedicated_intervals`;
  - a mismatch with the manifest beyond an absolute 1e-9.
- **Agreement with the runner.** This matches how the runner computes `gpu_hours` (`exam_runner.py:458-466`).
- **Ranking.** `verify_b2_batch` calls it for every candidate (`:331`) and publishes the values in `proof.grid.gpu_hours`.
  `_b2_summary_v2` (`analyze.py:346-351`) STOPs unless every primary row's GPU-h is finite, non-bool, and within 1e-9
  of the verified value. A `None` GPU-h can therefore no longer reach the sort.
- **Report.** §3 describes this.
- **Tests.** Mutations that bypass the call, the upper-bound check, the open-interval check, the status check, the
  value check, or the ranking check are each killed by a named test.

## Round-1 non-blocking findings

| Item | Status |
|---|---|
| N2: dropped B1 verifier checks | Added: Stage A pass and provenance (`b2_batch.py:206-207`); `d28_pass` with `d28_scope`, and `thinking_on_d28` recomputed (`:326-330`); `verify_anchor_reference` (`:336`); `refuse_sealed` of the anchor source (`:146`). Each is killed by a named tamper |
| N3: imprecise verifier tests | `TAMPER` now has 42 cases, each with `match=`. Final-Y tampers are carried through root and aggregate together, so removing `check_final_audit` or relaxing to `rel_tol=1e-3` is now killed. Remaining survivors are listed below |
| N4: runner-level B2 STOPs | `test_b2_runner_level_stops` (5 cases) and `test_b2_production_manifest_records_the_authorized_head` kill the B1-analysis, finalist-list and missing-finalist mutants. The b2 lease acquisition in `start()` and the CLI `verify_anchor_reference` for b2 are still untested. Both are acceptable: lease acquisition fails closed at `_server`, and the verifier now checks the anchor |
| N6, N9: wording | Fixed: "switchable finalists among the top three"; the collect test is called DRYRUN; the production final-Y line is recorded as untested by any run; the invalid-row check limit is stated (§2) |
| N7: author cap 10 | Enforced in `author_gate` for b2 (`runtime.py:571-572`) and in `expected_grid` (`b2_batch.py:69-70`). Both are tested |
| N5, N8, N10, N11 | Unchanged. They remain acceptable as described in round 1 |

## Remaining notes (non-blocking)

1. **Full-suite numbers in the report are stale.** Report §5 still gives the round-1 figures: 1418 passed and "+123".
   For this commit:
   - `/tmp/pb/full_b2code_r2.fail` and the base `/tmp/pb/full_run7912.fail` hold the same 30 test ids;
   - the run shows 30 failed / 1449 passed / 11 skipped, which is +154 over the base;
   - 154 is exactly the B2 test count (101 + 46 + 7, also given correctly in §5's table).

   I record the correct figures here. A later report-only correction would need its own review record, under the
   hand-off rule that later commits may only add review records.
2. **Remaining mutation survivors in `b2_batch.py`.** None of these is a missing protection:
   - `:251` (`all_false`) is implied by `cache_prompt_evidence` equality, which raises unless every call is false.
   - `:322` (pairs coverage) is implied by the exact root grid, the per-root `check_final_audit`, and the manifest
     cross-check.
   - `:268` (`worker_runs` vs ledger) is untested; the separate budget-vs-completion check is tested.
   - `:311` (root `audited_proposals` vs reconstruction) is untested. A root-only tamper is still caught by the
     candidate-audits check.
   - `:155` (harness pin) is untested.
3. **Round-1 survivors still present:**
   - the `undated` author-row case still does not isolate the power row's date (`runtime.py:494`);
   - the b2 lease acquisition (`runtime.py:782-784`) and the CLI anchor check (`exam_runner.py:562`) are untested;
   - see the N4 row above for why these are acceptable.
4. **Ranking sorts on the manifest value.** `_b2_summary_v2` sorts on the manifest `gpu_hours`, which has just been
   checked to equal the verified value within 1e-9. This is immaterial.

## Tests run (scratch export of 37282ec3, harness pin a3fedbb, `/tmp/trackg_venv`)

- `test_exam_b2_code_unit.py`, `test_exam_b2_batch_verify.py`, `test_exam_b2_collect.py`, `test_exam_core.py` and
  `test_exam_cache_d3_guard.py`: 200 passed.
- B1 files (`test_exam_b1_*`, `test_b1_*`, `test_exam_x5_rule_v2`) plus `test_exam_core` and
  `test_exam_cache_d3_guard`: 485 passed, 1 skipped.
- Mutations: 39 tried; 32 were killed and 7 survived. The survivors are listed above.
- Full suite: diffed from the logs, not rerun. Same 30 failures as the base; 1449 passed.

## For the hand-off

- The B2 config's `paper_commit` must be the accepted commit below, and the protected-path diff against the run HEAD
  must be empty.
- The run HEAD must carry:
  - the frozen B1 analysis (`fcf52c09` `complete_batch_verifier.json`, sha `07cb62de…`, which passes the structural
    checks);
  - the two author §10 rows (the drafts on `mac-b2-plan-20261114` pass the gate);
  - the B2 authorization note.

Accepted commit: 37282ec37a715feaaea48dd621ae08678424accc
