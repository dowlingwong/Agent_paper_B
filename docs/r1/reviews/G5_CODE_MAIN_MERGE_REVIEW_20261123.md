Reviewed base: READY 90 (`459b2161`) merged with origin/main `000ac3b1` (`30e2d51a`) and `89899f76` (`ecfd86a5`); accepted at `ebe7fb8c`, confirmed at `2582c898047d98333687b76422953665f2b1227b`

# Independent review record — the G.5 code (parts 3a, 3b-1, 3b-2) on top of main without READY 86, with the G5-MEM A row-check fix

**Unit.** On `mac-g5-code-main-20261123`, starting from READY 90 (`mac-g5-code-3b2-20261123` @ `459b2161`): the merge `30e2d51a` of origin/main `000ac3b1` drops READY 86 (superseded by the cluster's R1-SWEEP1-RELEASE-COMPAT implementation, `r1/c3/sweep1_compat.py` and the `replay_builder` hook, on main `3522e59b`): `r1/c3/release_checks.py` is main's file plus the G.5 block (`g5_integrity` and its publication check), its registration, `import subprocess` and one docstring sentence; READY 86's test, report and review are removed; the G.5 code is kept unchanged. The merge `ecfd86a5` brings origin/main `89899f76` (READY 87 merged as `630398c6`; R1-ARMS-DECISIONS, R1-G5-DECISIONS-2, R1-G5-MEM-E4). `baf6be5d` fixes the switch's G5-MEM A row check, which required the E4 amendment row itself to name "G5-MEM" and so would have refused every G.5 job against main's R1-G5-MEM-E4: the decisions row must name every decision's option and, under G5-MEM A, cite the E4 row id; the E4 row must name "E4" and "memory modes" (`g5_tasl.decision_row_checks`, `2582c898`). The report `docs/r1/reports/g5_code_20261123/G5_CODE_MAIN_MERGE_20261123.md` records the resolution and the full-suite evidence. Authority: the user's queue of 23 Nov 2026 (14:02), item 1.

**Full r1/tests suite.** Run on the Mac desk, one run after another, same interpreter and `AR_HARNESS_ROOT`: baseline origin/main `000ac3b1` 55 failed / 3530 passed / 196 skipped vs `30e2d51a` 55 / 3705 / 196; baseline origin/main `89899f76` 58 failed / 3567 passed / 196 skipped / 3 errors vs `baf6be5d` 58 / 3743 / 196 / 3. The failure lists are identical in both pairs (committed beside the report): zero new failures. The six entries new on main between the baselines are `test_c3_arms_freeze.py`, which needs LightGBM (absent from this interpreter; 43 passed with it).

**Process.** One independent reviewer, read-only, on clean detached checkouts of its own; no secrets, sealed data, labels or evaluation values. It verified blob identity of every sweep-1 release file with main, the removal of every READY 86 symbol and file, that the G.5 code is unchanged apart from `baf6be5d`, the full-suite lists and collect-only totals (3781/3956/3824/4000), the merge shapes, and the row-check change against main's real PLAN rows. It accepted at `ebe7fb8c` with three minors and one note; m1 (the 3A report still described the old check) and m2 (the real-PLAN test copied the check) were fixed in `2582c898` and confirmed without a full re-run (a behaviour-preserving refactor; every test file reaching the code passes; the collected count unchanged).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ebe7fb8c` | ACCEPTED (minors m1–m3; m4 note) |
| 2 | `2582c898` | ACCEPTED (confirmation) |

**Open items.** (1) READY 86's commits remain in this branch's history (through `b7b6e9cf`), as a consequence of starting from READY 90 and merging; their content is removed by `30e2d51a`, so no tree is affected (reviewer m4: acceptable). Publish by merge commit; never squash or rebase. (2) A single PLAN row serving as both the decisions row and the E4 row would be refused (it would have to cite its own id); main uses two rows. (3) Everything open from READY 88–90 stands: the harness unit (`trackg/audit_g5.py`, under review separately), the T1 features unit (ARMS-T1FEAT A), the two T1 release rows, the G.5 draft revision 9, §11 items 9–16 and the new note lines at signature, and the freeze of the G.5 files under `sweep2/` and the spec on main from launch to the T1 test release.

## Round 1 (`ebe7fb8c`)

> Reviewed base: ebe7fb8c5ef0b258daa3e6a6148a89d03a8fd9ad (first assigned as 355dfc22be9d5444c6149d5d1c2a03d31a684d61, then widened at the coordinator's request to 355dfc22..ebe7fb8c, which takes in ecfd86a5, baf6be5d and ebe7fb8c)
>
> ## Summary
> The unit does what the user asked, and the evidence for it holds up.
>
> **1. Sweep-1 release paths match main exactly.**
> - These files have the same git blob on the branch, on origin/main 89899f76 and on 000ac3b1: `audit.py`, `sweep1_compat.py`, `release.py`, `sweep2_batch.py`, `analysis_guard.py`, `test_c3_release.py` and `test_sweep1_release_compat.py`.
> - `git diff origin/main ebe7fb8c -- r1/c3` shows only `release_checks.py`. Its only changes are:
>   - one docstring sentence;
>   - `import subprocess` at module level;
>   - the G.5 block (`G5_PATHS`, `G5_SPEC`, `_g5_git`, `_g5_unpublished`, `_g5_published`, `g5_integrity`);
>   - `"g5": g5_integrity` added to `INTEGRITY_CHECKS`.
> - `_sweep1_compat_published`, `sweep1_integrity`, `_sweep2_batch_published` and `sweep2_integrity` are byte-identical to main's.
> - The module-level `import subprocess` changes no sweep behaviour. Main's `_sweep1_compat_published` already imports subprocess locally, which binds the same module object. No test patches `release_checks.subprocess`; the tests that patch `subprocess.run` patch the shared module, so they see the same thing either way.
> - `docs/r1/PLAN.md` is the same as main's.
>
> **2. READY 86 is fully removed.**
> - READY 86's net change (the merge `b7b6e9cf` against its first parent) touched four files. Its test, report and review are gone from the branch. Its code in `release_checks.py` has been replaced by main's version.
> - None of the listed symbols appears in any code file, nor do `_builder_checkout`, `_run_builder` or `SWEEP1_FEATURIZER`.
> - The remaining mentions are historical, in the G.5 3B2 report and review and in the merge report.
> - No kept G.5 file depends on READY 86. The G.5 code uses only `release.integrity_context`, `release.test_released`, `release._INTEGRITY` and `release_checks.INTEGRITY_CHECKS`/`g5_integrity`, all of which main's `release.py` provides unchanged.
> - `release()` calls `check(table_dir, audit_dir, **integrity_args)`. For the g5 source the CLI passes no extra arguments, which matches `g5_integrity(table_dir, audit_dir)`. `SOURCES` maps g5 to T1.
>
> **3. G.5 code is kept.**
> - From 459b2161 to 355dfc22 there is no change under `sweep2/`, `r1/tests/test_t1_*` or the G.5 docs.
> - From 459b2161 to ebe7fb8c, the only G.5 changes are baf6be5d's: `g5_tasl.py` (+14/−6 lines) and `test_t1_g5_tasl.py` (+19).
>
> **4. Full-suite evidence checks out (no full re-run, as instructed).**
> - The committed failure lists match in each pair. 000ac3b1 against the branch: 55 = 55. 89899f76 against baf6be5d: 61 = 61, made up of 58 failures and 3 errors.
> - The 89899f76 baseline differs from the 000ac3b1 baseline only by the six `test_c3_arms_freeze.py` entries.
> - Those six fail here because the module `lightgbm` is missing (I saw the `ModuleNotFoundError` myself). They fail the same way on 89899f76. With `PYTHONPATH=/tmp/armsdev/pylib`, `test_c3_arms_freeze.py` gives 43 passed on the branch.
> - Collect-only totals agree with the reported numbers:
>   - 000ac3b1: 3781 = 3530 + 55 + 196.
>   - 355dfc22: 3956 = 3705 + 55 + 196.
>   - 89899f76: 3824 = 3567 + 58 + 196 + 3.
>   - baf6be5d: 4000 = 3743 + 58 + 196 + 3.
> - The extra passes are accounted for by the new G.5 test files:
>   - 175 = g5_job 23 + g5_seal 30 + g5_tasl 107 + g5_ar_projection 6 + g5_pin_check 7 + tasl_g4 2 (30 on the branch against 28 on main).
>   - 176 = those 175 plus the new row-check test (g5_tasl goes to 108).
> - Targeted runs, one file at a time, on clean detached checkouts in my own worktree:
>
> | Commit | test_c3_release | test_sweep1_release_compat | g5_seal | g5_job | g5_tasl | tasl_g4 | ar_projection | pin_check |
> |---|---|---|---|---|---|---|---|---|
> | 355dfc22 | 43 passed | 7 passed | 30 passed | 23 passed | 107 passed | 30 passed | 6 passed | 7 passed |
> | baf6be5d | 43 passed | 7 passed | 30 passed | 23 passed | 108 passed | 30 passed | 6 passed | 7 passed |
> | 000ac3b1 | 43 passed | 7 passed | – | – | – | – | – | – |
> | 89899f76 | 43 passed | 7 passed | – | – | – | – | – | – |
>
> **5. Merge shape is correct.**
> - 30e2d51a is a true merge. Its parents are 459b2161 and 000ac3b1.
> - ecfd86a5 is a true merge. Its parents are 355dfc22 and 89899f76. Its tree (d62b5285) is exactly what `git merge-tree` gives for a clean merge of origin/main into 355dfc22.
> - 355dfc22 and ebe7fb8c add only report docs and failure lists.
> - I checked the report's claims (receipt `f06e37a9`, 3522e59b on main, the resolution table, the counts) and found them accurate, apart from m1 below.
>
> **6. The baf6be5d row-check change is sound.**
> - `plan_row` matches the row's text cell only (not the id cell), with a no-letter-or-digit-follows boundary.
> - The new rule ties the two rows by id: under G5-MEM A, the decisions row must name every `G5-x <option>` plus the E4 row id, and the E4 row must name "E4" and "memory modes".
> - This is the link main actually has: R1-G5-DECISIONS-2 says "G5-MEM A (…; with R1-G5-MEM-E4)", and R1-G5-MEM-E4 says "Amends … E4's \"both memory modes\"".
> - The old rule (the E4 row must name "G5-MEM") would have stopped every G.5 job on main's real PLAN, so the fix is needed.
> - The new test checks the real PLAN rows, and the negative tests cover both new stop messages.
> - What the author signs (the authorization draft §11: "with the row amending E4's 'both memory modes'") is still satisfied.
>
> ## Findings
>
> **B (blocking):** none.
>
> **M (major):** none.
>
> **m1. The 3A report still describes the old check.**
> - **Where:** `docs/r1/reports/g5_code_20261123/G5_CODE_3A_20261123.md` lines 79–80, and the quoted review statement in `docs/r1/reviews/G5_CODE_3A_REVIEW_20261123.md` line 42.
> - **Problem:** both say the E4 row "names E4 and G5-MEM". Since baf6be5d, the switch instead requires the decisions row to cite the E4 row id, and the E4 row to name "E4" and "memory modes". The merge report's Update section describes the new rule, but the 3A report that declares the switch's checks was not amended.
> - **Failure scenario:** someone checks the PLAN rows or a future note against the 3A report, expects "G5-MEM" in the E4 row, and is confused or "fixes" the wrong row.
> - **Fix:** add a dated one-line amendment to the 3A report pointing to baf6be5d and the new rule. The review record should stay as it was written.
>
> **m2. The new real-PLAN test copies the check instead of calling it.**
> - **Where:** `r1/tests/test_t1_g5_tasl.py`, `test_main_decision_rows_pass_the_switch_row_checks`.
> - **Problem:** the test calls `T.plan_row` with its own copy of the term lists, not through `launch()`'s code.
> - **Failure scenario:** if `launch()`'s terms change later, this test still passes while the real check could stop on main's PLAN.
> - **Fix (optional):** move the terms into a small helper in `g5_tasl.py` that both `launch()` and the test use. A related stale but harmless spot is `test_m5_plan_row_duplicate_and_id`, which still uses the old terms `("E4", "G5-MEM")` against its fixture row.
>
> **m3. A single combined decisions-and-E4 row would now be refused.**
> - **Where:** `g5_tasl.launch`, the G5-MEM A branch.
> - **Problem:** under the new rule, if a spec set `decisions_row == e4_amendment_row`, the row would have to name its own id in its text cell, so the check would stop. The old rule accepted such a combined row.
> - **Why it doesn't matter now:** main uses two separate rows (R1-G5-DECISIONS-2 and R1-G5-MEM-E4), so nothing is affected.
> - **Fix:** no action needed beyond noting it in the m1 amendment.
>
> **m4. READY 86's commits stay in the history.**
> - **Where:** history through `b7b6e9cf` (fbbac887's commits).
> - **Problem:** fbbac887 is not on origin/main, so publishing this branch brings READY 86's commits into main's history, even though their content is removed by 30e2d51a.
> - **Assessment:** this follows directly from the user's instruction to start from READY 90 and use a merge commit. It has no effect on any tree and is disclosed in the merge report. Acceptable as is.
>
> ## Process note
> - While I was reviewing, the shared worktree /tmp/pb/wt/g5m moved (ecfd86a5) and briefly held uncommitted G.5 edits, which later became baf6be5d.
> - I therefore ran every test against clean detached checkouts in my own /tmp/mainrev worktree, not in the shared one.
> - I made no commits and no pushes.
> - I removed /tmp/mainrev with `git worktree remove`.
> - All scratch files are in /tmp/mrev/_to_delete/.
>
> VERDICT: ACCEPTED

## Round 2 (`2582c898`)

> Reviewed base: 2582c898047d98333687b76422953665f2b1227b (one commit on ebe7fb8c; confirmation round)
>
> ## Summary
> The new commit fixes m1 and m2 and records m3 as asked. I found no new problems, and a full-suite re-run is not needed.
>
> **What changed since ebe7fb8c.** Only three files:
> - `sweep2/t1_tasl/g5_tasl.py`: the row checks moved into a new function, `decision_row_checks(spec, o)`, and `launch()` now calls it.
> - `r1/tests/test_t1_g5_tasl.py`: the real-PLAN test now uses that same function, and the old fixture terms are updated.
> - `docs/r1/reports/g5_code_20261123/G5_CODE_3A_20261123.md`: a dated amendment section was added.
>
> **m2 (the check is now shared): resolved, and behaviour is unchanged.**
> - `decision_row_checks` produces the same pairs in the same order as baf6be5d's inline code:
>   - the decisions row, with every `G5-x <option>` and, under G5-MEM A, the E4 row's id;
>   - then, under G5-MEM A only, the E4 row with ("E4", "memory modes").
> - `launch()` still runs `plan_row` on each row and then adds it to `rows`, in the original order, so nothing changes at launch.
> - The real-PLAN test now builds the spec with R1-G5-DECISIONS-2 and R1-G5-MEM-E4 and the spec's default options. It runs it through `decision_row_checks` and asserts which rows come back. It then checks each row against this checkout's `docs/r1/PLAN.md`. So the test now runs the code `launch()` runs instead of a copy of it.
> - The stale fixture terms in `test_m5_plan_row_duplicate_and_id` are now ("E4", "memory modes").
>
> **m1 and m3 (the 3A report): resolved.**
> - The amendment names `baf6be5d`, states the new rule, and records that a single row serving as both would be refused.
> - The 3A review record is unchanged.
>
> **Targeted runs.** I ran these one file at a time on a clean detached checkout of 2582c898 in my own worktree, /tmp/mainrev, which I have since removed. Every file that imports the t1_tasl/G.5 code passed:
>
> | Test file | Result |
> |---|---|
> | test_t1_g5_tasl | 108 passed |
> | test_t1_g5_job | 23 passed |
> | test_t1_g5_seal | 30 passed |
> | test_t1_tasl_g4 | 30 passed |
> | test_t1_tasl_g5_ar_projection | 6 passed |
> | test_t1_tasl_g5_pin_check | 7 passed |
> | test_t1_tasl_chain | 16 passed |
> | test_t1_tasl_crosscheck | 30 passed |
> | test_t1_tasl_g1b | 45 passed |
> | test_t1_tasl_g1b_ar | 69 passed |
> | test_p3_split | 11 passed |
> | test_c3_release | 43 passed |
> | test_sweep1_release_compat | 7 passed |
>
> - Collecting the whole of `r1/tests` gives 4000 tests, the same as baf6be5d, so no test was added or lost.
> - None of these files appears in the committed failure lists.
>
> **Is skipping the full re-run enough? Yes.**
> - The change is a behaviour-preserving refactor inside `g5_tasl.py`, plus test and doc edits.
> - Every test file that could reach that code passes on the new commit.
> - The collected count is unchanged.
> - Nothing under `r1/c3`, the sweep-1 release files or `PLAN.md` changed.
> - So the baf6be5d full-suite evidence (identical failure lists against 89899f76) still holds for 2582c898.
>
> ## Findings
> - **B:** none.
> - **M:** none.
> - **m:** none new.
> - m4 (READY 86's commits remain in history through `b7b6e9cf`) stands as acceptable, as before.
>
> ## Process note
> - I made no commits or pushes.
> - My worktree /tmp/mainrev is removed.
> - The earlier /tmp/mrev/_to_delete folder had already disappeared before this round, so someone else deleted it. This round's scratch is in /tmp/mrev/_to_delete/t3.
>
> VERDICT: ACCEPTED

---

Code-Commit: 2582c898047d98333687b76422953665f2b1227b
Verdict: ACCEPTED

Accepted at `ebe7fb8c`, confirmed at `2582c898`.
