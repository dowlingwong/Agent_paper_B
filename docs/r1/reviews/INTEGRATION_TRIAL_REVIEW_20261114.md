Reviewed base: 7c9c9cff83650df1601811d1eba245d68a3dd2d2

# Integration trial (14 November 2026) — independent review record

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 7. Branch `mac-int-trial-20261114` from `mac-int-20261107` @ `a15300ca`; a trial, not the integration. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (four blocking: the `offline_eval` resolution read `build.json` before the guard; the cause of the new failure was wrong; the causes of the remaining failures were wrong; the five held `9bab3d6f` diffs were not disclosed).
- Round 2: changes requested (one blocking: the held diffs need an independent review, not only the author's acknowledgement).
- Round 3: **accepted** at `7c9c9cff`.

Accepted commit (round 3, last): 7c9c9cff83650df1601811d1eba245d68a3dd2d2

Round-3 notes, not blocking: in §6 the colon makes "it carries the guard fixes…" read as the reason to split M3 rather than the reason M3 goes first; question TP-1 credits nested-field detection to `EVAL_COLUMNS`, while it comes from the `_keys` change in the same held `run.py` diff.

The round texts are reproduced unchanged below.

---

Reviewed commit: 8a078229fb6bd531ae174e56358de421e8af9cbc

# Independent review: Unit 7 integration trial (`mac-int-trial-20261114`), round 1, 14 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not do the unit). Inputs: MAC_OVERNIGHT_RUNBOOK_20261113 §7 (from `69b3576b`), the accepted runbook review (S13, N4, N8, interpretation 11), branch tip `8a078229` on base `a15300ca`, `/tmp/pb/inttrial/*`, and `docs/r1/reports/INTEGRATION_TRIAL_20261114.md` with `docs/r1/reports/integration_trial_20261114/`. I worked read-only. Scratch: a detached worktree under `/tmp/rev_u7` plus a separate git object directory for `git merge-tree` (no objects written into the repository). Both were removed at the end.

## What I checked and what holds

1. **Merges.** The nine merge commits on the first-parent line (`d317c7db`, `29556cf0`, `cf155f4a`, `1807e4c7`, `f66d1cd7`, `b418ed07`, `d46625e1`, `9d6a79f1`, `a25075df`) are all true two-parent merges. Each second parent is the stated commit, and each stated commit is the current tip of the named branch. No squash or rebase was used, so N4 holds (for example, gate commit `421a1c38` and the 9 Nov D8 `83a12b44` are ancestors of the tip). Merges 2–9 have exactly the tree that `git merge-tree` gives for their parents, so no hand edits were made there. Merge 1 differs from the automatic merge only in the six conflicted files.
2. **Review records.** Each merged commit is a single review-record commit on top of the accepted commit. The diff touches only the review file and, for M3, M4 and M10, one status line in a hand-off or answers file. In every case the last round says accepted, and the accepted commit matches:
   - M3: `MAC_M3_REVIEW_20261109.md`, round 2, accepted at `4df14fd6`, record commit `ec6e30a9`.
   - M4: round 3, `00e6cb20`, record `5cd32efc`.
   - D8 v2: round 2, `80d70832`, record `e3c0921e`. The 9 Nov `M11_D8_GATE_REVIEW` is also accepted (round 3).
   - W2 stop rule: round 2, `92c92656`, record `87f67467`. It contains `W2_BUDGET_FIELDS_REVIEW` (round 3, accepted) and `mac-w2-budget-20261109` @ `0b62fb03`.
   - M10 kit: round 3, `f4e09f87`, record `f56f7f35`.
   - M10 v2: round 2, `f77dbe32`, record `52a40d57`.
   - Track P RL: round 3, `2f36614a`, record `c9d29ba9`.
   - HTCondor: round 3, `ee6567a0`, record `68057612`.
   - DTQ: round 2, `0aa4bc00`, record `f20e7ccb`.
3. **No B1-line merge.** For all 67 local and `gh/` refs that match `mac-b1-*`, `ops-b1-*`, `mac-b2-handoff*`, `mac-appendix*` and `exam-x*`, none of their commits after the base is reachable from the tip.
4. **Test numbers.** The ten `.fail` and `.summary` files under `docs/r1/reports/integration_trial_20261114/` are byte-identical to `/tmp/pb/inttrial/`. The counts in the §1 table match the summaries: 40/749/54 → 25/951/81 → … → 25/1434/83. Steps 2–9 have the same failure set as step 1. Against the base there is 1 new failure, 16 fixed and 24 remaining, as the report says.
   **My rerun at the tip** (scratch worktree of `8a078229`, same command, harness `a3fedbb`, `/tmp/trackg_venv`) gave `25 failed, 1434 passed, 83 skipped, 43 subtests passed`. The failure set is identical to `09_dtq.fail`. The main worktree `/tmp/pb/wt/inttrial` stayed clean at `8a078229`.
5. `test_c3_audit_dryrun.py` passes on M3 alone (`ec6e30a9`: 7 passed).
6. **Step-1 resolutions that are right:**
   - `docs/r1/PLAN.md`: the merged file equals mac-int's. M3's own PLAN additions (R1-SWEEP1-CLASSIFY and its clarification) were already on mac-int, and nothing from M3 is lost.
   - `r1/c3/dataset.py`: the merged file is byte-identical to the base. M3's dataset changes were already on mac-int, and every `refuse_sealed` is present.
   - `r1/c3/audit.py`: M3's `partition_population` and `evidence_plan` refactor is intact, and every mac-int guard is present (`_digest`, `_verify_replay`, `evidence_plan`, `evidence_cache`, `validate_worker_records`, `main`; `RunCache` and `resolve_seeds` were auto-merged). `partition_population` takes in-memory rows and opens no files.
   - `test_c3_evidence_guards.py`: taking M3's version drops only the dotted-string `monkeypatch` lines, which are replaced by an equivalent object patch plus module hiding. No mac-int assertion is lost.
   - `test_c3_evidence_seed_isolation.py`: the mac-int stubs are kept and M3's stricter expectations are added.
   - The `offline_eval.py` resolution keeps M3's logic. The problem is the guard ordering (B1 below).
7. **Report scope.** The report discloses that steps 8 and 9 go beyond the runbook list, and that the W2 branch merged is the stop-rule branch, which contains the `mac-w2-budget-20261109` named in N8. The report sits in `docs/r1/reports/`, which follows the runbook's docs/r1-relative path convention.

## Findings

### B1 — BLOCKING: the `offline_eval.assemble` resolution opens a sealed table's `build.json` before the sealed-path guard

On mac-int (`a15300ca`), `assemble` calls `guard_table(table_dir, audits_path, proposals.jsonl)` first. `guard_table` runs `refuse_sealed(table, …)` before anything is opened, and the M11 inventory relies on that ("`guard_table` checks sealed inputs first, reads `build.json` as metadata").

The trial resolution keeps M3's order instead (`r1/c3/offline_eval.py:145–154` at the tip):
- it reads and parses `table_dir/build.json`;
- it acts on its contents (the classification/EVIDENCE and seed-split `ValueError`s);
- only then does it call `guard_table`.

The guard call is still there, but its protection at this point is lost. I probed this with a table under `/tmp/rev_u7/probe/r1_sealed/table` whose `build.json` holds `{"label":"X","classification":{…}}`:

| Commit | Result |
|---|---|
| `a15300ca` | `RuntimeError: STOP: r1_sealed paths are not analysis inputs` |
| `d317c7db` and `8a078229` | `ValueError: classified table must carry an EVIDENCE label` (the sealed file was opened and decided the error) |

No test catches this because the guard still fires before any label file is read. The report's statement that the resolution "keeps both: M3's code plus every mac-int guard call" therefore overstates it.

**Fix:**
- In the trial resolution (and the proposed resolution for the real integration), move `audits_path = audits_path or Path(table_dir) / "audits.jsonl"` and the `guard_table(...)` call above the `meta_path` read, as mac-int had it. M3's code does not depend on the late assignment.
- Add a regression test: a sealed table with a non-EVIDENCE classified `build.json` must STOP on the sealed check.
- Rerun the suite and correct §2's `offline_eval.py` row.

### B2 — BLOCKING: §3 misidentifies the cause of the one new failure, and so its options are incomplete or unsafe

The failure is real and correctly located: the guarded `dataset.load_table` is called from `r1/scripts/c3_audit_dryrun.py:153`. But the root cause is not "no D8 confirmation row; the test predates the guard".

- `guard_table` deliberately exempts tables built from the frozen sweep-1 index (`_index_is_frozen_sweep1`). It does so only if `build.json` records `sweep_index.path` resolving to `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` together with the pinned SHA.
- mac-int's `dataset.build_from_sweep` writes that path.
- M3's `build_table` writes only `'sweep_index': {'sha256': …}` (`c3_audit_dryrun.py:94`). The guard therefore cannot recognise the table as sweep-1 and treats it as unknown provenance, which requires D8.

I checked this directly with `guard_table` at the tip:
- `build.json` with `{"label":"DRYRUN","sweep_index":{"sha256":SWEEP1}}` → STOP;
- the same file plus `"path": <frozen index>` → passes.

Consequences the report misses:
- **It is not only the test.** M3's dry-run tool itself STOPs on the integrated code.
- **The simplest fix needs no guard change and no author row.** `build_table` can record the index path, as `build_from_sweep` does.
- **The listed option "exempt DRYRUN tables from the D8 guard" weakens a guard by label.** A caller-supplied label is exactly what the M11 inventory says must not be trusted.
- **"Keep it failing until R1-BX-D8-CONFIRM is committed" would make a sweep-1 tool depend on the sweep-2 authority row,** which is not the guard's design.
- **Two small errors:**
  - The failure persists through steps 2–**9**, not 2–8.
  - The STOP message changes at step 3, when D8 v2 brings in gate code. Steps 1–2 give "R1-BX-D8-CONFIRM or gate code absent"; steps 3–9 give "exact affirmative R1-BX-D8-CONFIRM with current gate SHA required".

**Fix:**
- Rewrite §3 with the root cause above.
- Make "record `sweep_index.path` in M3's `build_table`" the recommended IT-1 option.
- Mark the DRYRUN-exemption option as weakening the guard, or drop it.
- Correct "2–8" and note the message change.

### B3 — BLOCKING: §5's explanation of the 24 remaining base failures is wrong for most of them

§5 attributes them to "no network to OpenML, no committed sweep data here, a Python 3.13 venv". The logs (`00_base.log`, `09_dtq.log`, and my tip rerun) show otherwise:

| Count | Tests | Actual cause |
|---|---|---|
| 13 | `test_c3_sweep_table.py` (9), `test_d28_noise_binding.py` (3), `test_c3_evidence_guards.py::test_evidence_plan_covers_all_and_rejects_stale_table` | mac-int's own D8 guard STOP, the same mechanism as the "new" failure |
| 1 | `test_replay_detects_deleted_rows_despite_self_signed_table` | the D8 STOP plus a resulting missing `build.json` |
| 6 | `test_c3_sweep_dryrun.py` | `STOP: only 1 nodes passed D28 liveness (< 2)` inside the dry run |
| 1 | `test_trackp_soft_label_v2` | `ModuleNotFoundError: lightgbm` |
| 1 | `test_rerun2_batch4c` | `git commit` of the dry-run source fixture fails |
| 1 | `test_trackp_exam_synthetic` | gzip bytes differ |
| 1 | `test_c3_control_dryrun` | runner exits rc 1 before the interruption (cause not shown) |

None of the tracebacks show an OpenML network error. This matters for the author's decision: IT-1 is not a one-test question, because the D8 guard already breaks 14 mac-int tests on the base. §5 also says the failures were "not investigated" while still stating causes.

**Fix:** replace §5's cause sentence with this breakdown, or with "causes not investigated" and no attribution. Cross-reference IT-1 for the D8-guard group.

### B4 — BLOCKING: the report does not disclose that step 1 brings in the five author-held `9bab3d6f` diffs, and most of the "16 fixed" depend on them

Merging `mac-m3-20261109` changes these five files, all from commit `9bab3d6f`:
- `r1/c3/train/run.py`
- `r1/c3/train/trainer.py`
- `r1/c3/env.py`
- `r1/c3/control.py`
- `r1/c3/prior_model.py`

`docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` row R1-B2-REPAIR-SCOPE-ACK says these are taken into M3's scope and "the author acknowledges them, or not, with M3's accepted commit. **Until then they are not merged.**" Question Q24 (`MAC_OVERNIGHT_QUESTIONS_20261105.md`) is still deferred, the M11 inventory calls them "author-held", and I found no acknowledgement row on any branch.

Merging them into a trial branch is acceptable. But §4 and §6 recommend "M3 should go first: it carries the guard fixes the Track P leak-guard tests need" without saying that:
- 10 of the 16 fixes (`test_c3_evidence_other_boundaries.py`) come from exactly these held diffs: `EVAL_COLUMNS` and `guard_rows` in `run.py`, and `refuse_unverified_sweep_rows` in `control.py`, `env.py` and `prior_model.py`;
- the real merge needs the author's Q24 / R1-B2-REPAIR-SCOPE-ACK decision.

**Fix:**
- Add to §2 or §4 that step 1 includes the five held diffs, citing R1-B2-REPAIR-SCOPE-ACK and Q24.
- Say which fixed tests depend on them.
- Add to §6 "Before the real merge" that the author must acknowledge (or reject) those diffs. If rejected, M3 would have to be integrated without them and the 10 tests would stay failing.
- Put a pointer in the question list.

### N1 — NON-BLOCKING: §4's attribution of the 16 fixes is too broad

"M3 carries the guard and provenance work that 16 failing mac-int tests expect" is accurate only for the 10 `other_boundaries` tests (code in the held files, B4). The other six are fixed largely by test-side changes:
- **2 in `test_c3_evidence_guards.py`:** M3's version of the test hides already-imported `autoresearch` modules, which fixes test-order pollution. This is the conflict resolution itself.
- **3 in `test_c3_launch_provenance.py`:** M3 updates stale fixtures (`runner.label`, and the `engineering_liveness` keyword in the `check_launch_manifest` stub).
- **1 in `test_c3_evidence_seed_isolation.py`:** M3 updates its expectations.

**Fix:** say so in §4.

### N2 — NON-BLOCKING: new M3 readers outside the conflict set have no sealed-path checks

Two M3 scripts arrive unguarded:
- **`r1/scripts/c3_audit_dryrun.py`** reads the sweep index, the sidecar and the manifests (`:80–81`, `_sha`). It also reads `configs.json` right after the guarded `load_table` (`:154`). mac-int's pattern in `dataset.plan` adds `refuse_sealed(table/'configs.json')` at exactly that point (`dataset.py:534`).
- **`r1/scripts/c3_env_replay.py`** reads the index, the sidecar, manifests, root ledgers and a tar (`:140–141, 189, 203, 239`).

The base's own C3 scripts are also unguarded, and the M11 inventory scoped out external scripts, so this is not a regression of an existing guard. Still, these are new readers of the frozen corpus that mac-int's library pattern would guard.

**Fix:** list both scripts in §2 as "new M3 readers not covered by mac-int's guard pattern", so that the code review of the real integration decides whether to add `refuse_sealed` (for `--paper`, the index, the sidecar, manifests and `configs.json`).

### N3 — NON-BLOCKING: undisclosed duplicate and overlapping suite runs

The scratch files show the suite started more than once for steps 7–9:
- `07_trackp.log` and `08_htc.log` each end with two `rc=` lines;
- `08_htc.merge` and `09_dtq.merge` say "Already up to date" (the merge script was re-invoked);
- the first step-9 run was `Terminated` (`09.out`);
- `08.out` reports a 569.74 s run while the committed `08_htc.summary` is 562.19 s.

The recorded step-8 run ended at 02:24:21, after the step-9 merge commit at 02:23:58, so it overlapped that merge in the same worktree for about 23 s. The results are not affected: the sets are identical across steps 1–9, and my independent tip rerun reproduces step 9 exactly.

**Fix:** add one line to §1 noting the repeated invocations and that the recorded files are from the last complete run, or rerun step 8 alone. In future, serialise suite runs, for example with `flock`.

### N4 — NON-BLOCKING: IT-1 is referenced but does not exist yet

§3 points to "the question list (IT-1)". `mac-overnight-report-20261114` is still at `a15300ca` and has no `MAC_OVERNIGHT_QUESTIONS_20261114.md`.

**Fix:** make sure IT-1, with the corrected options from B2, and the Q24 pointer from B4 land in the question list on the report branch (S13).

### N5 — NON-BLOCKING: small wording points in §2

- "`git diff ec6e30a9 <merge> -- r1/c3/audit.py` shows only added `refuse_sealed`/`guard_table` lines": it also moves one line in `resolve_seeds` (auto-merged). This is harmless, but "only" is not literal.
- Say that the merged `dataset.py` and `PLAN.md` are byte-identical to mac-int's, because M3's changes to them were already on mac-int. That is the strongest evidence that nothing from M3 is lost there.

## Summary

The mechanics are sound: correct `--no-ff` merges of the stated, review-accepted commits, no B1-line commits, exact test bookkeeping, and an identical tip rerun. Three gaps remain:
- **One resolution regresses a mac-int guard:** sealed `build.json` is read before `guard_table` in `offline_eval.assemble` (B1).
- **Two explanations are wrong:** the cause of the new failure and the causes of most remaining failures (B2, B3).
- **An open author decision that the real integration depends on is not disclosed:** the five held `9bab3d6f` diffs, Q24 (B4).

Verdict: changes requested

---

Reviewed commit: 95ddcefab8956568ead9c297678a27594302556d

# Independent review: Unit 7 integration trial (`mac-int-trial-20261114`), round 2, 14 Nov 2026

Same reviewer as round 1 (Claude subagent; did not do the unit). Commits reviewed since round 1: `d3ce0d52` and `95ddcefa`, on top of `8a078229`. I worked read-only. Scratch was a detached worktree under `/tmp/rev_u7`, removed at the end. The main worktree `/tmp/pb/wt/inttrial` stayed clean at `95ddcefa`.

## Verification of the round-1 findings

**B1 (guard order in `offline_eval.assemble`): fixed.**
- `r1/c3/offline_eval.py` at the tip is byte-identical to mac-int's (`git diff a15300ca 95ddcefa -- r1/c3/offline_eval.py` is empty). `guard_table` runs before `build.json` is read. No M3 logic is lost: relative to mac-int, M3's only change in this file was the reorder.
- The new test `r1/tests/test_c3_offline_eval_guard_order.py` passes at the tip.
- I copied it onto the round-1 code (`8a078229`), where it fails with the content-driven `ValueError` at `offline_eval.py:149`. So it bites.
- **Full suite at the tip** (scratch worktree, same command and environment as round 1): `25 failed, 1435 passed, 83 skipped, 43 subtests passed`. The failure set is identical to `09_dtq.fail`. The extra pass is the new test, and there is no regression.

**B2 (§3, cause of the new failure): fixed.**
- §3 gives the right cause (`build_table` records no `sweep_index.path`).
- It covers steps 1–9 and the message change at step 3.
- It says the tool itself STOPs.
- It recommends (a), recording the path, and drops the DRYRUN exemption.

**B3 (§5, causes of the remaining failures): fixed in substance, with one swap.**
- The counts 14 / 6 / 4 match the step-9 log and my rerun.
- Two causes are attached to the wrong files (see N1 below).

**B4 (held `9bab3d6f` diffs): disclosed, but the disclosure leaves out their review status (see R2-1).**

**N1–N4 from round 1:**
- N1: §4 is reworded and accurate.
- N2: added as §5a, and adequate.
- N3: added as §5b, and adequate.
- N4: IT-1 (and IT-2) are written in `/tmp/pb/wt/report14/docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261114.md`. At review time the file is **untracked** on `mac-overnight-report-20261114`, which is still at `a15300ca`. IT-1 matches §3.

**N5 from round 1:** not addressed (see N3 below).

## Findings

### R2-1 — BLOCKING: §2 and §6 present the held diffs as needing only the author's acknowledgement, but no accepted review covers them

R1-B2-REPAIR-SCOPE-ACK says the five diffs "are taken into M3's scope and **reviewed with it**". The record shows they were not:
- **`MAC_M3_REVIEW_20261109.md`** (the accepted M3 review, rounds 1–2) does not mention `run.py`, `trainer.py`, `env.py`, `control.py`, `prior_model.py`, `9bab3d6f` or `EVAL_COLUMNS`. Neither do the answers file or the hand-off.
- **`MAC_M3_REVIEW_20261104.md`** checked only that the diff of the five files from `9bab3d6f` to `ec4af062` is empty. It states: "This observation is not acceptance of those changes or their later integration."
- **`C3_EVIDENCE_GUARDS_REVIEW_20261028.md`** is the only substantive review of `9bab3d6f`. Its verdict is "BLOCK / NOT ACCEPTED FOR B.2 LAUNCH".

So §6's precondition ("after the author has acknowledged (or not) the five held diffs") is incomplete. The row's own precondition, a review of the diffs with M3, is not met.

The question-file entry IT-2 makes this worse. It recommends "(A) acknowledge the exact diffs at `ec6e30a9` … (A) if you accept M3's review", which implies that M3's review covered them.

**Fix:**
- In §2 (and §6), state that no accepted review covers the five diffs, citing the three reviews above.
- Make the precondition "an independent review of the five diffs (in M3's scope), then the author's acknowledgement".
- Correct IT-2 the same way before the question file is committed. Option (A) should not rest on "M3's review", and a review of the five diffs should be the recommended next step.

### N1 — NON-BLOCKING: §5's "4 single causes" swaps two causes

The step-9 log and my rerun show:
- `test_trackp_soft_label_v2.py::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical` fails with `ModuleNotFoundError: lightgbm`;
- `test_trackp_exam_synthetic.py::test_committed_set_matches_its_hash_and_regenerates_byte_identically` fails on gzip bytes.

The report has them the other way round.

**Fix:** swap the two causes.

### N2 — NON-BLOCKING: the report has no test result for the corrected tip

The §1 table ends at step 9 (25 / 1434 / 83). Since then the branch has changed code (`d3ce0d52`): the reorder and a new test.

**Fix:** add a row or sentence: "after the review-round fix (`d3ce0d52`): 25 / 1435 / 83, same failure set as step 9 (+1 pass: the new guard-order test)". This agrees with my rerun at `95ddcefa`. Also say that the merge commit `d317c7db` itself still contains the first resolution, which §2 already implies.

### N3 — NON-BLOCKING: §2's opening still overstates (round-1 N5)

Two statements are still too strong:
- "`git diff ec6e30a9 <merge> -- r1/c3/audit.py` shows only added `refuse_sealed` / `guard_table` lines." It also moves one line in `resolve_seeds`.
- "keeps both: M3's code plus every mac-int guard call". This was not true of the first `offline_eval` resolution, which the table row now explains.

**Fix:** soften to "essentially only (one moved line)", and add "(after the round-1 fix)" to the "keeps both" sentence.

## Summary

The code fix for B1 is correct, matches mac-int exactly, is covered by a test that bites, and the full suite at the tip shows no regression (25 / 1435 / 83, same failure set). The B2 and B3 rewrites are correct apart from one swapped pair. One blocking gap remains: the held-diffs disclosure (and IT-2) treat the five `9bab3d6f` diffs as reviewed with M3 when no accepted review covers them.

Verdict: changes requested

---

Reviewed commit: 7c9c9cff83650df1601811d1eba245d68a3dd2d2

# Independent review: Unit 7 integration trial (`mac-int-trial-20261114`), round 3, 14 Nov 2026

Same reviewer as rounds 1–2 (Claude subagent; did not do the unit). I reviewed:
- trial commit `7c9c9cff`, on top of `95ddcefa`;
- IT-1, IT-2 and TP-1 in `docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261114.md` on `mac-overnight-report-20261114` @ `ea1fcfcc`.

I worked read-only and used no scratch worktree this round. Both worktrees are clean: `/tmp/pb/wt/inttrial` at `7c9c9cff` and `/tmp/pb/wt/report14` at `ea1fcfcc`.

## Scope of the change

`git diff 95ddcefa 7c9c9cff` touches only `docs/r1/reports/INTEGRATION_TRIAL_20261114.md`. No code or test changed since round 2. My round-2 full-suite rerun at `95ddcefa` (25 / 1435 / 83, same failure set as step 9) therefore still applies to the tip, and I did not rerun.

## Verification of round-2 findings

**R2-1 (held diffs): fixed.**
- §2 now says that no accepted review covers the five diffs, citing:
  - the 9 Nov M3 review, which does not mention them;
  - the 4 Nov M3 review, which says it is "not acceptance" of them;
  - the 28 Oct `C3_EVIDENCE_GUARDS_REVIEW` of `9bab3d6f`, which says BLOCK.
- §2 and §6 make the precondition "an independent review of the five exact diffs, then the author's acknowledgement", or else M3 is split.
- I confirmed that the five files are byte-identical at `9bab3d6f`, `ec6e30a9` and the tip. So a review "of the five diffs at `ec6e30a9`" reviews exactly what the tip carries.

**N1: fixed.** lightgbm is now attributed to `test_trackp_soft_label_v2.py` and the gzip byte mismatch to `test_trackp_exam_synthetic.py`, which matches the logs.

**N2: fixed.** The tip row (25 / 1435 / 83, same 1 new failure, 16 fixed) matches my rerun.

**N3: fixed.**
- The `audit.py` sentence is now exact. `git diff ec6e30a9 d317c7db -- r1/c3/audit.py` has 19 insertions and 1 deletion: 18 guard lines plus the moved `f = Path(out) / SEEDS_FILE`.
- The "keeps both" sentence now carries the qualification for `offline_eval.py`.

## Question file (`ea1fcfcc`)

The question file is committed on top of `a15300ca`.
- **IT-1** matches report §3: the cause, options (a) and (b), and recommendation (a). It no longer offers the DRYRUN exemption, and the paste-ready line asks for option (a).
- **IT-2** states the row's "reviewed with it" condition and that no accepted review exists (with the three reviews). Its options are (A) commission an independent review of the five exact diffs at `ec6e30a9`, (B) split M3, and (C) keep deferring. It recommends (A), and the paste-ready line asks for the review before a decision. This is accurate.
- **TP-1** is accurate in substance. On mac-int, `EVAL_COLUMNS` is at `r1/c3/train/run.py` line 37 and lacks the aliases. The 8 TrackPStop tests fail on the base and pass after step 1, and TP-1 makes "integrate M3" conditional on IT-2.

## Findings

### N1 — NON-BLOCKING: one garbled sentence in §6

"…if they are not acknowledged, M3 has to be split: it carries the guard fixes the Track P leak-guard tests need, and its six conflicts are the only ones." After the edit, the colon makes the guard-fix clause read as the reason for splitting. It is really the reason M3 should go first.

**Fix (optional):** reorder as follows: "M3 should go first (it carries the guard fixes … and its six conflicts are the only ones), after an independent review … and the author's acknowledgement; if they are not acknowledged, M3 has to be split."

### N2 — NON-BLOCKING: TP-1 attributes "nested" to `EVAL_COLUMNS`

Nested-sequence detection comes from the `_keys` change, which now traverses lists and tuples. That change is in the same held `run.py` diff, not in the regex.

**Fix (optional):** write "`EVAL_COLUMNS` and `_keys` in `run.py` do not catch …", and optionally say that the fixing change is one of the five held diffs.

## Summary

All blocking findings from rounds 1 and 2 are resolved.
- The trial branch has correct `--no-ff` merges of review-accepted commits and no B1-line commits.
- The step-1 resolutions keep every mac-int guard (including the corrected `offline_eval` order, with a regression test that bites) and all of M3's logic.
- The test bookkeeping is exact and was reproduced at the tip.
- The report's causes and its disclosure of the held diffs are accurate, and the related questions IT-1, IT-2 and TP-1 are consistent with it.
- The remaining notes are wording only.

Verdict: accepted
Accepted commit: 7c9c9cff83650df1601811d1eba245d68a3dd2d2
