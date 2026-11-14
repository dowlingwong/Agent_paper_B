# Integration trial — 14 November 2026

**Status.** A **trial**, not the integration. AI-assisted (Claude, Mac-local agent), MAC_OVERNIGHT_RUNBOOK_20261113
Unit 7. Branch `mac-int-trial-20261114` from `mac-int-20261107` @ `a15300ca` (the runbook's `origin/mac-int-20261107`;
the local `gh/` and `origin/` refs are the same commit). Only branches with an **accepted** independent review were
merged, each with `git merge --no-ff` (no squash, no rebase), so every accepted commit stays an ancestor (runbook
review N4). The B1 exam branches (`mac-b1-*`, `ops-b1-*`) and the branches built on them (`mac-b2-handoff-20261114`,
`mac-appendix-20261114`, `mac-b1-obs180-20261113`) were not merged. Harness branches are not part of a paper merge
(runbook review N8). The author decides the real integration.

## 1. Order, merges and test results

Full paper suite (`r1/tests`) after each merge: `AR_HARNESS_ROOT` = harness `a3fedbb`, venv `/tmp/trackg_venv`
(Python 3.13, NumPy 2.5.3, no torch, no network). The failure set is compared by test id with the base.

| # | Merged branch @ commit (review record) | Conflicts | Suite: failed / passed / skipped | New failures vs base | Base failures fixed |
|---|---|---|---|---|---|
| 0 | base `a15300ca` | — | 40 / 749 / 54 | — | — |
| 1 | `mac-m3-20261109` @ `ec6e30a9` (2 rounds) | 6 files (§2) | 25 / 951 / 81 | 1 (§3) | 16 |
| 2 | `mac-m4-20261109` @ `5cd32efc` (3 rounds) | none | 25 / 1003 / 81 | same 1 | 16 |
| 3 | `mac-m11-d8-v2-20261114` @ `e3c0921e` (contains the 9 Nov `83a12b44`) | none | 25 / 1306 / 81 | same 1 | 16 |
| 4 | `mac-w2-stoprule-20261114` @ `87f67467` (contains `mac-w2-budget-20261109` @ `0b62fb03`) | none | 25 / 1325 / 81 | same 1 | 16 |
| 5 | `mac-trackg-20261109` @ `f56f7f35` (M10 kit, docs) | none | 25 / 1325 / 81 | same 1 | 16 |
| 6 | `mac-trackg-v2-20261114` @ `52a40d57` (M10 v2 paper side) | none | 25 / 1325 / 81 | same 1 | 16 |
| 7 | `mac-trackp-rl-20261114` @ `c9d29ba9` (Track P RL) | none (auto-merged `r1/c3/train/model.py`) | 25 / 1348 / 83 | same 1 | 16 |
| 8 | `mac-htcondor-20261114` @ `68057612` (HTCondor adapter, not in the runbook list) | none | 25 / 1416 / 83 | same 1 | 16 |
| 9 | `mac-m4-dtq-20261114` @ `f20e7ccb` (DTQ tool, not in the runbook list) | none | 25 / 1434 / 83 | same 1 | 16 |

Steps 8 and 9 go beyond the runbook's list; they were accepted tonight and are on top so that the list's own
order (steps 1–7) can be taken without them. Track P's torch tests skip in this venv (no torch); they were run on
the branch itself in a torch venv (its review record).

## 2. Conflicts of step 1 (M3 into mac-int) and their trial resolutions

M3 (`mac-m3-20261109`) grew on a different line (from `30303d87`, with 71 commits not on mac-int), and mac-int
meanwhile added sealed-path and D8-authority guards to the same C3 readers. Every conflict is one of two kinds: mac-int
added a guard call where M3 changed nothing, or M3 refactored code mac-int had guarded. The trial resolution keeps
**both**: M3's code plus every mac-int guard call. `git diff ec6e30a9 <merge> -- r1/c3/audit.py` shows only added
`refuse_sealed` / `guard_table` lines.

| File | Hunks | Resolution |
|---|---|---|
| `docs/r1/PLAN.md` | 2 | mac-int's 28–30 Oct author-decision blocks (R1-C3-POOL … R1-T4-DI-FIX; R1-TRACKS-HOST … R1-REPO-ACCESS) are absent on the M3 line; kept |
| `r1/c3/dataset.py` | 4 | mac-int's `refuse_sealed` calls kept |
| `r1/c3/audit.py` | 7 | M3's `partition_population` + `evidence_plan` refactor, with mac-int's `refuse_sealed` and `guard_table` at the top of the new `evidence_plan` and at the five other guarded readers |
| `r1/c3/offline_eval.py` | 1 | M3's order, with mac-int's `guard_table` call after `audits_path` is set |
| `r1/tests/test_c3_evidence_guards.py` | 3 | M3's version (it hides already-imported harness modules; mac-int's version is the older form of the same test) |
| `r1/tests/test_c3_evidence_seed_isolation.py` | 3 | mac-int's `guard_table` stub kept, plus M3's new expectations (task-native runtime attestation, split label block, completion record) |

These resolutions are the trial's; the real integration should have them reviewed as code.

## 3. The one new failure

`test_c3_audit_dryrun.py::test_dryrun_on_the_frozen_corpus_partitions_the_whole_population` (an M3 test) passes on
M3 alone and fails after the merge with `RuntimeError: STOP: R1-BX-D8-CONFIRM or gate code absent`: M3's dry run on the
frozen corpus now passes through mac-int's D8 authority guard, which STOPs because no D8 confirmation row is committed.
The guard behaves as designed; the test predates it. It persists unchanged through steps 2–8. Options are in the
question list (IT-1): stub the guard in that test as the seed-isolation test does, keep it failing until R1-BX-D8-CONFIRM
is committed, or exempt DRYRUN tables from the D8 guard.

## 4. The 16 base failures that M3 fixes

M3 carries the guard and provenance work that 16 failing mac-int tests expect: 10 in
`test_c3_evidence_other_boundaries.py` (including the 8 Track P leak-guard tests that the Track P RL review traced to
`EVAL_COLUMNS` in `r1/c3/train/run.py`), 2 in `test_c3_evidence_guards.py`, 1 in `test_c3_evidence_seed_isolation.py`
and 3 in `test_c3_launch_provenance.py`.

## 5. Base failures that remain

24 of the base's 40 failures remain through every step, unchanged: `test_c3_sweep_table.py` (9),
`test_c3_sweep_dryrun.py` (6), `test_d28_noise_binding.py` (3), `test_c3_evidence_guards.py` (2: the evidence-plan
and replay-deletion tests), and `test_c3_control_dryrun.py`, `test_rerun2_batch4c.py`, `test_trackp_exam_synthetic.py`,
`test_trackp_soft_label_v2.py` (1 each). They fail on the base in this environment
(no network to OpenML, no committed sweep data here, a Python 3.13 venv rather than the pinned hosts); they were not
investigated tonight.

## 6. Proposed order for the real integration

The runbook's order works without further conflicts after step 1: M3 → M4 → M11 D8 v2 → W2 (stop-rule branch, which
contains the 9 Nov W2 budget branch) → M10 kit → M10 v2 → Track P RL; HTCondor and DTQ can follow in any order.
M3 should go first: it carries the guard fixes the Track P leak-guard tests need, and its six conflicts are the only
ones. Before the real merge: review the step-1 resolutions as code and settle IT-1.
