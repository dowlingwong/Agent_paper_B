Reviewed base: origin/main `3024db3f8` (READY 98 at `0ace90c22` merged with 44c3d80e and 3024db3f); accepted at `ad163909f`, confirmed at `162c1c6c6`

# Independent review record — READY 98 (D7: the T1 prompt form for A5) on current main: merges with READY 97 and the post-freeze reads, raw-code flags as T1 values under D2 A, the tightened D7 record check

**Unit.** On `mac-a5-t1-prompt-20261123`, on top of READY 98's accepted tip `0ace90c22`: merge `8fc56c2a9` of origin/main 44c3d80e (READY 97: D6 A, D6-σ B, D9 B; rows R1-T1-FEAT-DECISIONS, R1-T1-A5-DECISIONS); `e832c170a` (`serialize_t1.yes_no` renders the four D2 A code-state flags as "yes"/"no" from the row's own features and refuses NaN or non-0/1 values instead of printing n/a; `check_build` requires build.json's D9 counts `{raw_state_missing: 0, flag_mismatch: 0}`; the gate-coverage test adapted to READY 97's `g1b_run(world, NODE)`; `arms_freeze.check_record` with a non-empty T1 set requires ARMS-T1FEAT to cite R1-T1-FEAT-DECISIONS or R1-T1-A5-DECISIONS, and R1-T1-A5-DECISIONS to contain `D7-FORM A`); merge `947ac286b` of origin/main 3024db3f (post-freeze reads; one conflict in test_c3_arms_freeze.py's fake PLAN, all three rows kept); `7d634bbdd` (T0-only D7 test uses main's `_t0_only`); report §12 and full-suite lists; `162c1c6c6` (docs: §3 note, two runbook clauses in `DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md`, §12 wording). The two tests that failed on top of 97 in the coordinating chat's full suite (`test_na_rendering_and_no_t0_values`: the n/a expectation dated from 98's ledgers without raw states; `test_gate_coverage_is_met_for_a_t1_node_through_the_frozen_builder`: 97's helper signature) pass. `serialize.py`, `gate.py`, `gate_input_builder.py`, `release.py`, everything under `sweep2/` and the preregistration are unchanged; T0 prompts and data directories byte-identical (independently checked). Authority: the user's message of 24 Nov 2026 (00:20), item 1.

**Full `r1/tests` suite** (`pytest -q -p no:cacheprovider -rfE r1/tests`, LightGBM off the path, fresh TMPDIR, sequential): base 44c3d80e 58 failed / 3 errors / 3800 passed; base 3024db3f 58 / 3 / 3823; tip `7d634bbd` (later commits docs only) 58 / 3 / 3841 / 197 skipped; failure lists `FULLSUITE_BASE_44c3d80e.txt`, `FULLSUITE_BASE_3024db3f.txt`, `FULLSUITE_A5_TIP.txt` byte-identical (61 entries, `df956efa…`): zero new failures.

**Process.** One independent reviewer, read-only, own detached worktrees at the tip and at 3024db3f, synthetic data only. Round 1 accepted with four minors (no major); the docs-only fixes were confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ad163909f` | ACCEPTED (minors m1–m4) |
| 2 | `162c1c6c6` | ACCEPTED (confirmation) |

**Open items.** Residual m3: the `D7-FORM A` check is a token match in R1-T1-A5-DECISIONS (cannot tell adopting from rejecting; a later superseding row needs a human reader). Until D7-DIFF B (next unit) is on main, A5's T1 input is form A (no diff text) with FL1 disclosed, per R1-T1-A5-DECISIONS. Operators: with T1 in the read, the arms-frozen record's ARMS-T1FEAT entry cites R1-T1-FEAT-DECISIONS or R1-T1-A5-DECISIONS (runbook updated). The report's §4 example keeps pre-97 numbers with a note.

## Round 1 (`ad163909f`)

> Reviewed base: ad163909f (mac-a5-t1-prompt-20261123; base main 3024db3f)
>
> ## Summary
> No major findings, four minor ones.
>
> **1. Merges: faithful.** `git diff 3024db3f ad163909f` touches exactly the 12 D7 paths (98's 9 files plus three FULLSUITE lists); every other path, including `PLAN.md`, `gate*.py`, `release.py`, `serialize.py`, `features.py`, `labels.py`, `dataset.py`, `sweep2/`, `test_t1_*` and `authorizations/`, is byte-identical to main. Nothing of 98 lost (`sft_data.py`, `sft_test_eval.py`, `types.py` and the review record identical to 98's diff; `serialize_t1.py`, `arms_freeze.py` and the two test files differ only by e832c170a/7d634bbd; F1 intact). Merge `8fc56c2a` equals `git merge-tree 0ace90c2 44c3d80e` (no hand edit). Merge `947ac286`: the only conflict is in `test_c3_arms_freeze.py`; all three fake-PLAN rows kept; `from pathlib import Path` moved into the D7 test (main imports it at line 911); `PLAN_WITHOUT_ROW` still removes its row by exact text.
>
> **2. Raw-code flag decision: correct.** `g5_features.featurize_ledger` counts `raw_state_missing` over every step with a candidate state; `node_rows` takes each row's features from that dict and STOPs if a tabled step has none; `derive` STOPs on a non-zero count in both stages; the active pair is `float(bool)`. No assembled table can carry a NaN flag. `t1_prompt` renders both lines from the row's own features (`serialize_t1.py:257-263`). The four D2 fields are not in `NO_T1_SOURCE`; `n/a` only for those fields and non-feature items. The flag-line wording is unchanged from `0ace90c2`. For every table `g5_assemble` can write, refusing NaN gives byte-identical output to 98 as built.
>
> **3. `check_build` D9 check: tied correctly** to `build.json` `nodes.<node>.features = {raw_state_missing, flag_mismatch}`; the test asserts `S1.D9_COUNTS == g5_assemble.D9_COUNTS`; no legitimate refusal (empty node 0/0; test stage same `build.json`; T0-only builds never call it).
>
> **4. Tightened D7 record check: sound.** With T1, ARMS-T1FEAT must cite one of two exact row ids; a T0-only record (`_t0_only`) passes without the options row; the real PLAN has both rows and adopts `D7-FORM A`.
>
> **5. T0 byte identity: confirmed** with my own script (12 instances × 18 steps via `test_trackp_sft._ledger`; three tokenizer sets; `PYTHONHASHSEED=0`; 2 `SyntheticLabelSource` variants × 2 split configs, `load_sft_data`, a `LabelBlockSource` build): prompts (204 per set), `rows.jsonl`, `splits.json`, `sft_data.json` identical on `3024db3f` and the tip, except the `LabelBlockSource` `sft_data.json` differing only by the scratch path. `serialize.py` identical (`abc36d9f…`). Limitation: no prompt long enough to drop history lines (that path is in the byte-identical `serialize.py`).
>
> **6. σ_node: consistent** (`t1_prompt` requires row σ = `build.json` σ; `soft_target` refuses a differing σ, `sft_data.py:496`; the gate test asserts noise record, `build.json` and rows agree).
>
> **7. Full suite: identical and plausible (not rerun).** Six lists byte-identical (`df956efa…`, 61 lines: 58 FAILED, 3 ERROR); the 6 `test_c3_arms_freeze` entries are the LightGBM-missing failures (reproduced 3 failed, 3 errors without LightGBM); 3841 − 3823 = 18 = 17 new + 1 arms_freeze test.
>
> **8. Report §12: accurate** apart from m1 and m4.
>
> **9. Targeted tests on the tip:** test_trackp_t1_prompt 17; test_c3_arms_freeze (LightGBM) 56; test_c3_arms_constants 11; test_trackp_sft 35; test_trackp_sft_test_eval 48; test_t1_features 30 + 1 skipped without LightGBM, 31 with; test_gate_input_builder 41; test_trackp_p3 23.
>
> ## Minor findings
> - **m1** `A5_T1_PROMPT_20261123.md:135`: the §3 template table still gives the raw-code line as `y/n/n/a`; only §12's blanket note covers it. Add a one-line note at line 135.
> - **m2** `docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md:91`, `:278` vs `arms_freeze.py:1053-1057`: the runbook says to cite the row deciding each decision id; ARMS-T1FEAT A is decided in R1-ARMS-DECISIONS (`PLAN.md:1443`), which `check_record` refuses with a non-empty T1 set (costs a retry; 98's accepted check refused it too). The runbook should say that with T1 the ARMS-T1FEAT entry cites R1-T1-FEAT-DECISIONS or R1-T1-A5-DECISIONS.
> - **m3** `arms_freeze.py:1058`: the `D7-FORM A` check is a token match (cannot tell adopting from rejecting; reads only that row id). Low risk today.
> - **m4** §12 "Tests" (~line 625): "On 3024db3f: …" lists this branch's results, not the clean base's; the 31-passed figure for `test_t1_features` needs LightGBM. Wording only.
>
> ## Cleanup
> Both worktrees removed; scratch in `/tmp/a5mrev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

## Round 2 (`162c1c6c6`)

> Reviewed base: 162c1c6c6 (on ad163909f)
>
> ## Summary
> All three checks pass; no new findings. Detached worktree, removed; no tests rerun; nothing committed or pushed.
>
> 1. **Only the two docs change.** `git diff --stat ad163909f 162c1c6c6`: `docs/r1/reports/arms_t1feat_20261123/A5_T1_PROMPT_20261123.md` (+11/−2) and `docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md` (+2/−2); no code or test files.
>
> 2. **The wording matches `arms_freeze.check_record` (lines 1053–1060).** Runbook and §12 (m2): with a non-empty T1 set, ARMS-T1FEAT must cite R1-T1-FEAT-DECISIONS or R1-T1-A5-DECISIONS; citing R1-ARMS-DECISIONS is refused — exactly the checker (`t1["suites"]` non-empty and `dec["ARMS-T1FEAT"] not in D7_ROWS` raises). The runbook omits the PLAN-side `D7-FORM A` condition, acceptable (it depends on the PLAN, which already meets it). §12 residual (m3) correctly describes the token match. §3 note (m1) matches `yes_no` and `t1_prompt` at `ad163909f`. §12 test labels (m4) read "This branch on top of 3024db3f / 44c3d80e (not the clean base)"; the LightGBM note matches round 1.
>
> 3. **The runbook edits touch nothing else.** Same line count; only lines 91 (I-P8) and 278 (`decisions` row) changed, both pure appends before the closing `|`.
>
> VERDICT: ACCEPTED

---

Code-Commit: 162c1c6c6
Verdict: ACCEPTED

Accepted at `ad163909f`, confirmed at `162c1c6c6`.
