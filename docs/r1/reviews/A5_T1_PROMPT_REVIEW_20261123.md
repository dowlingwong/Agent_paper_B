Reviewed base: origin/main `14f19a09`; accepted at `c0bcf923c`, confirmed at `0f776404c`

# Independent review record — D7: a T1 prompt form for A5 (`trackp_prompt_t1/1`), the Track P data path for G.5 rows, and the `arms_freeze` label-row fix (F1)

**Unit.** On `mac-a5-t1-prompt-20261123` (on origin/main `14f19a09`): `r1/c3/arms_freeze.py` (F1: `check_label_rows` admits `divergent_seeds` on G.5 `audit`/`divergent` label rows only, as integers within the row's own label seeds, without which every audited G.5 label was refused and neither A3 nor A5 could train on T1; `check_record` refuses a record with a non-empty T1 set unless the cited ARMS-T1FEAT row names D7); new `r1/c3/train/serialize_t1.py` (`trackp_prompt_t1/1`: a G.5 table row in T0's sections and order, T1-less fields `n/a`, history from earlier rows of the same campaign, an optional bounded diff excerpt (default off: the G.5 table carries no diff text), T0's 896-token length rule under every pool tokenizer, fail-closed `PromptTooLong`, a whole-table row-count check against `build.json`, `missing_for_gate`); `r1/c3/train/sft_data.py` (`G5LabelSource` over released train/dev labels with a required `table_sha256`, `CompositeLabelSource` for the joint T0+T1 build (PRE-JOINT A), lazy import of the T1 form, per-tier `label_seeds` and a `t1` manifest record only when T1 rows are present); `r1/c3/train/types.py` (`T1_PROMPT_VERSION`); `sft_test_eval.py` (the `t1` record check); tests `r1/tests/test_trackp_t1_prompt.py` (17) and in `test_c3_arms_freeze.py`; report `docs/r1/reports/arms_t1feat_20261123/A5_T1_PROMPT_20261123.md` with author decisions D7-FORM, D7-DIFF, D7-HIST, D7-WORDING, D7-LEN and flags FL1–FL6. `serialize.py`, everything under `sweep2/`, the preregistration, `gate.py`, `gate_input_builder.py` and `release.py` are unchanged; T0 prompts and data directories are byte-identical (checked independently by the reviewer in both rounds). Authority: the user's message of 23 Nov 2026 (17:02), item 2 (D7 of R1-T1-FEAT-DECISIONS, to be published on main).

**Process.** One independent reviewer, read-only, own detached worktrees at the tip and at `14f19a09`, synthetic data only, targeted tests one file at a time. Round 1 accepted with eight minors (no major); applied in `0f776404c` and confirmed with two residual minors.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `c0bcf923c` | ACCEPTED (minors m1–m8) |
| 2 | `0f776404c` | ACCEPTED (confirmation; residual n1, n2) |

**Open items.** Author decisions before use (report §6–§7): F1 option A (as built) or B (remove or rename `divergent_seeds` on G.5 label rows in `g5_assemble`, before the G.5 launch); D7-FORM (a second template version, amending TRACK_P §2.2 "one text template"; an author row needed before evidence use); D7-DIFF (A no diff, as built, meets "diff provenance" in the repo's sense through the code-state flags, with FL1 disclosed; B a bounded diff excerpt, needing a reviewed `g5_assemble` change on main before the G.5 launch, with FL2 disclosed); D7-HIST, D7-WORDING, D7-LEN; flags FL1–FL6 (including R1-W2-3-STOP declared T0-only, and R1-CONTEXT-BASELINE parts (1) and (2) on T1). Residual: n1 the whole-word `D7` check is met by unrelated PLAN rows (tighten, or pin R1-T1-FEAT-DECISIONS once on main); n2 the row-count check uses an unbound `build.json` (record its sha256 in the manifest's `t1` record in the evidence-phase runner). Missing checks listed in the report: no record check that A5 data manifests carry the `t1` record, that the signed D7-DIFF option matches `t1.diff_shown`, or of A5 prediction coverage. The exam-synthetic test failure pre-exists on `14f19a09`. For the cluster: `table_prompts` with the real pool tokenizers on the released G.5 table (`PromptTooLong` is a STOP); `missing_for_gate` empty; joint data directories; predictions on every gate-source proposal.

## Round 1 (`c0bcf923c`)

> Reviewed base: c0bcf923c (mac-a5-t1-prompt-20261123; base 14f19a09)
>
> ## Summary
> I found no blocking defect. The code does what the report says. T0 output is byte-identical to base, which I checked independently. I found no leakage path, and F1 is correct and minimal. Every non-inert T1 test proposal gets a prompt. All the findings below are minor; most are about how complete the report is, plus two small robustness gaps.
>
> ## How I checked
> Own worktrees at `c0bcf923c` and `14f19a09`; no seeds 7001–7010, sealed or label data, or server.
>
> **1. T0 byte identity: confirmed independently.** My own script: node `tabular_mlp`, mode `append_only_summary`, campaigns of 14–23 trials; a whitespace tokenizer and a 2-characters-per-token one (462 and 650 history lines dropped); split configs default, `drop_from_train`, a custom salt/counts and the signed P3 split file; two synthetic label sources. Base and tip give identical sha256 for every prompt's text and meta and for `rows.jsonl`, `splits.json` and `sft_data.json` in all 8 data directories. In a joint T0+T1 build on the signed split the T0 lines of `rows.jsonl` match a T0-only build byte for byte and in order (65 rows).
>
> **2. Leakage: none found.** From the proposal's own row `t1_prompt` keeps only `ROW_FIELDS` (serialize_t1.py:225); from earlier rows only `decision` and `delta_hat`, for steps before the current one (:241–244). An earlier row's `delta_hat` is that step's campaign outcome at the instance seed 5101–5112 (`g5_assemble.py:409`), seen by the proposer before the current step; T0's history line uses the same quantity (`delta_vs_best`, serialize.py:192–194). No label, evaluation value or test-seed value in history. `recorded_gain_z` and code-state flags come from the ledger prefix plus the step's pre-execution hashes. No sealed content read by default.
>
> **3. F1: correct and minimal.** `g5_assemble.group_label` writes `divergent_seeds` on audit rows (sorted(cand_div + par_only), :313) and divergent rows (cand_div, :304), subsets of the label seeds; `rule_noop` rows have none; T0 D4B rows have none (audit_d4b.py:45). The exemption applies only when that key is the only evaluation key, the kind is audit or divergent, and the list holds integers from the row's own seeds; the seeds are still checked against the evaluation seeds and `_label_ok` still requires the exact label seeds. No evaluation field or test-seed value can pass. Without F1 every T1 training run would be refused.
>
> **4. Coverage: OK.** `table_prompts` renders every table row (no-ops, duplicates, divergent under `neg_inf`); rows not in the table are never asked for. The builder needs A5 for every non-noop test-split row (`gate_input_builder.py:328`, :412); `missing_for_gate` is a superset (probe: 72 needed, 144 listed).
>
> **5. Length rule: OK.** Same `fit_history`, same 896-token budget under every tokenizer; diff lines cut by bisection, deterministic; fails closed with `PromptTooLong` aborting the table.
>
> **6. Data path: OK.** `G5LabelSource` reads only through `load_traindev` and `training_rows`; test labels refused; soft label computed as A3's; divergent rows give no record, as in A3.
>
> **7. "Diff provenance".** Not deciding D7-DIFF. In this repo "diff provenance" means the pre-execution code-state hash record (`g5_features.py:20–21`, 37; `g5_assemble.py:422`), which the default uses through the four code-state flags, so the default plausibly meets the task as worded. The report presents D7-DIFF fairly; see m4.
>
> **8. Template pins.** No PRE-* row mentions A5's prompt. `trackp_prompt/v2` is named in R1-TRACKP-SFT-DEV, R1-W2-3-STOP, the unsigned P.4 draft's `table_pin`, and TRACK_P_POST_TRAINING.md:88 ("one text template"). A second template version needs an author row (D7-FORM) before evidence use; the report says so. R1-TRACKP-A6-DEFER not triggered.
>
> **9. Tests on the tip.** test_trackp_t1_prompt 14; test_c3_arms_freeze 43; test_t1_features 19; test_gate_input_builder 41; test_trackp_sft 35; test_trackp_sft_test_eval 48; test_trackp_p3 23; test_w2_budget_fields 19; test_trackp_serialize 13 skipped; test_trackp_sidecar_loader 1 passed, 3 skipped; test_trackp_cli 9 skipped; test_trackp_exam_synthetic 1 failed, 9 passed, 2 skipped (`test_committed_set_matches_its_hash_and_regenerates_byte_identically`, same failure on `14f19a09`: gzip bytes differ at index 13; environmental).
>
> ## Findings (no major)
> - **m1** serialize_t1.py:305–347: `table_prompts` does not check the whole table was passed; a caller filtering out no-ops silently changes 72 of 144 prompts. Fix: compare row count per node with `build.json` `nodes[n].counts.rows`.
> - **m2** sft_data.py:715 with serialize_t1.py:72: every build, T0 included, imports `serialize_t1`, which loads `g5_features.py` by fixed `parents[3]`; a sandbox shipping only `r1/` fails at import. Fix: `r1.harness.REPO` or skip when no T1 row.
> - **m3** sft_data.py manifest: in a joint build top-level `label_seeds` still says T0's [7001…7005] while T1 rows under R1-BX-D3 use 7001–7003.
> - **m4** Report §6: g5_assemble is not yet frozen (launch not happened; §7 plans a change for D7-DIFF B); the extra key is undocumented (G5_CODE_3B2 declares none; T0 B.2 rows have none), so B is not clearly worse. §7 should state "diff provenance" in the repo's vocabulary is met by A.
> - **m5** Report §7: FL4 cited but undefined, no FL2; R1-W2-3-STOP (W = 20 worker runs) scope for G.5 sources not stated; FL6 omits R1-CONTEXT-BASELINE part (1), the A1-ctx rung.
> - **m6** serialize_t1.py:351 docstring and report §2/§8: the builder asks only for the test split; wording imprecise.
> - **m7** No enforcement that D7 is signed before use: `check_record`'s `ARMS-T1FEAT` entry can cite R1-ARMS-DECISIONS; the manifest's `t1` record is not checked; under D7-DIFF B, `diffs` enter with no hash.
> - **m8** sft_data.py `G5LabelSource`: `table_sha256` optional; make it required.
>
> ## Cleanup
> Both worktrees removed; scratch in `/tmp/a5rev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

## Round 2 (`0f776404c`)

> Reviewed base: 0f776404c (on c0bcf923c)
>
> ## Summary
> All eight round-1 minors are fixed as described. No blocking issue; two small residual gaps (n1, n2), neither blocking. Own detached worktrees at `0f776404c` and `14f19a09`; no labels, sealed data, seeds 7001–7010 or server.
>
> ## T0 byte identity (own script, base vs tip)
> Same script as round 1 (node `tabular_mlp`, `append_only_summary`, campaigns of 14–23 trials; whitespace and 2-characters-per-token tokenizers; 8 data directories including the signed P3 split). Every prompt hash and every `rows.jsonl`, `splits.json` and `sft_data.json` hash identical, and identical to my round-1 run. A joint T0+T1 build on the signed split writes the same T0 lines in the same order as a T0-only build; its `label_seeds` is `{"T0": [7001…7005], "T1": […]}`.
>
> ## m7: can `check_record` refuse a record it should accept?
> T0-only records unaffected (the check runs only when `t1["suites"]` is non-empty; the new test confirms a T0-only record citing `R1-ARMS-DECISIONS` passes). Main's `test_c3_arms_freeze.py` against the tip's `arms_freeze.py`: 6 record tests fail with "must name D7" because main's fixture has a non-empty T1 set citing `R1-ARMS-DECISIONS`; this is the intended tightening, the same commit updates the fixture (44 pass on the branch), and no arms-frozen record exists on main. The new check runs before the disclosures, fold-arms and arms checks.
>
> **n1 (minor).** `\bD7\b` is satisfied by unrelated rows on main's PLAN: `R1-BX-PROPOSED-CONFIRM` ("D7 (F1): fixed-r…"), `R1-EXAM-B1-ANCHOR-R4` and `-R4-H2` ("D7 PASS"), `R1-D3-MIN` (via "R1-BX-D7"). Low to moderate risk: it catches keeping `R1-ARMS-DECISIONS`, not a wrong row cited; the report does not mention this. Suggested: also require `ARMS-T1FEAT` and a D7 token not preceded by `-`, or `D7-FORM`/`D7-DIFF`, or pin the row id once R1-T1-FEAT-DECISIONS is on main.
>
> ## Drift of `T1_PROMPT_VERSION` and `T1_NODES`
> `T1_PROMPT_VERSION` defined once in `types.py`; cannot drift. `sft_data` uses `p3_split.T1_NODES`, `serialize_t1` derives from `g5_features.T1_NODE_INFO`; `_t1_forms` refuses if they differ (probe: adding or removing a node refuses with "differ"); a drift inside `p3_split` is caught by its own generator check; a T1 row missing from the split list fails the form check (fail closed); `test_the_split_files_t1_nodes_are_the_forms_t1_nodes` checks equality always.
>
> **n2 (minor).** m1's row-count check compares against an unbound `build.json`: `check_build` does not bind `build.json` to the table by hash; the release receipt binds `proposals.jsonl` only; `build_sha256` exists only in the G.5 evidence completion record (`g5_assemble.py:532`). Probe: an edited `counts.rows` matching a filtered table is accepted. The fix stops the accidental filter with the real `build.json`, not an edited one. Suggested: record the `build.json` sha256 in the manifest's `t1` record, or check it against a pinned value, in the evidence-phase runner.
>
> ## Other changes
> m1 (filtered table, one row dropped, missing count all refused); m2 (lazy import; golden T0 build passes with `serialize_t1` unimportable); m3 (per-tier `label_seeds`; `check_t1_manifest` accepts `T1: null`, harmless for synthetic sources); m6 accurate; m7 diff sha256 in `meta.diff`; m8 `table_sha256` required, 64 lower-case hex. Report: F1 options fair, "diff provenance" met by A, FL1–FL6 without gaps, FL5 R1-W2-3-STOP, FL6 extended to A1-ctx, three missing checks listed; matches the code.
>
> ## Tests on the tip
> test_trackp_t1_prompt 17; test_c3_arms_freeze 44; test_t1_features 19; test_gate_input_builder 41; test_trackp_sft 35; test_trackp_sft_test_eval 48 (1 warning); test_trackp_p3 23; test_w2_budget_fields 19; test_trackp_sidecar_loader 1 passed, 3 skipped.
>
> ## Cleanup
> Worktrees removed (the tip's `arms_freeze.py` temporarily copied into the base worktree for the main-tests check and restored before removal); scratch in `/tmp/a5rev/_to_delete/`. Nothing committed or pushed.
>
> VERDICT: ACCEPTED

---

Code-Commit: 0f776404c
Verdict: ACCEPTED

Accepted at `c0bcf923c`, confirmed at `0f776404c`.
