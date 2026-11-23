Reviewed base: `30e2d51a`, merged forward to `2582c898` (READY 91's code); accepted at `f4be4cb4`, confirmed at `17bdf8cd7b3e6241a6465f73c76a3e373d015f81`

# Independent review record — drafts of the two T1 release rows R1-T1-LABELS-UNSEAL and R1-T1-LABELS-TEST-RELEASE (approved: false)

**Unit.** On `mac-t1-release-rows-20261123`: `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md` (approved: false) and the report `docs/r1/reports/g5_code_20261123/T1_RELEASE_ROWS_DRAFT_20261123.md`. Docs only. The row texts equal `release.row_text("T1", stage, …)` and fullmatch `release.row_pattern`, the preregistration (`aa1a961b…`) and split (`b5967dd7…`) sha256s filled, the release commit `a9d8ff5e` (`release.py` byte-identical through main and the G.5 branch), placeholders for the G.1b copies and the arms-frozen record; the ids match `g5_seal`'s locks. Around them: what each row unlocks (the `g5_seal` purposes, the two `g5_assemble` stages, the `g5` release step), preconditions (0: the ARMS-T1FEAT unit on main with its decisions by their deadlines; D7 a gate on the test row; the arms-frozen record checked with `--release-root g5=…` and `--artefact-root …`, possibly split across hosts; the G.5 files unchanged since the launch commit by `git diff --quiet`; the signed note unchanged between stages), the cluster commands and STOPs, and the open points (the δ_n binding: direct for σ_node only under D6-σ A, transitive for δ_n under D6 A or B, no T1 noise slot in the arms-frozen record; the gate bound through the preregistration's block, a difference from G.5 draft §6). Authority: the user's queue of 23 Nov 2026 (14:02), item 5.

**Process.** One independent reviewer, read-only, re-running the machine checks itself (row_text, row_pattern, author_rows, refusal of eight altered texts). Round 1 found the row texts correct but four majors in the surrounding text (the features/release order, the δ_n binding, the arms-record check command, the freeze statement); round 2 found precondition 0 and point 3a not matching the features unit's decisions and deadlines; round 3 accepted with one minor ("record pending" out of date), fixed and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `e41b414a` | NOT ACCEPTED (M1–M4; minors m1–m4) |
| 2 | `c78f6a1d` | NOT ACCEPTED (M1–M2; minors m1–m2) |
| 3 | `f4be4cb4` | ACCEPTED (m1) |
| 4 | `17bdf8cd` | ACCEPTED (confirmation) |

**Open items.** (1) Both rows are drafts for the author (approved: false); their placeholders (the G.1b copies, the arms-frozen record's path and sha256) are filled when those records exist. (2) Order: the T1 train/dev release must happen before the test row is on PLAN (`g5_integrity` takes its stage from `test_released("T1")`). (3) No Python environment on TASL-2 is recorded yet for the assembly and release step; the cluster agent records it in the release report. (4) PRE-DELTA's "recorded in the row" for δ_n is met only transitively (D6 A or B); an author note is proposed; a T1 noise slot in the arms-frozen record would need an `arms_freeze` change. (5) A PLAN row or coordinator rule freezing the G.5 files under `sweep2/` and the spec on main from launch to the T1 test release is still to be written.

## Round 1 (`e41b414a`)

> Reviewed base: e41b414a9cc8e309de6ee1f3219f3ba2c2b183ec (branch mac-t1-release-rows-20261123, on 30e2d51a6f74c9562943c23a5e4c35a1bbd92a1b; authority checked against origin/main 89899f765fc4134c05897bf079ced3ecb95314f2)
>
> ## Summary
>
> The two row texts themselves are correct.
> - Both match `release.row_text`/`row_pattern` exactly.
> - The filled values are right.
> - The release commit is valid.
> - The ids match the G.5 locks character for character.
> - They follow the signed template and the T0 precedent.
>
> The surrounding preconditions, ordering advice and gap analysis are another matter. They contain one statement that is wrong against the T1 features unit, one claim about the freeze that is wrong, and they leave out the T1 δ_n route. Because the unit tells the author and the cluster agent in what order to act, these errors matter. All fixes are docs edits. The row texts need no change.
>
> **What I re-ran myself** (my own script, Python 3.12, worktree `r1.c3.release`, synthetic values):
> - Both fenced texts are one line each and contain no `|`.
> - With stand-in values, both texts equal `row_text("T1", stage, …)` and fullmatch `row_pattern`. The prereg, split and commit groups parse to the expected values.
> - `aa1a961b…` equals the sha256 of the committed preregistration file, and `b5967dd7…` equals `p3_split.P3_SPLIT_SHA256`.
> - The G.1b group parses to 8 items, which are exactly `p3_split.T1_NODES`. Deleting the autoresearch item gives the seven-node `row_text` and still matches.
> - `author_rows` finds both rows, with exact text, in a synthetic `### 24 November 2026 — … (author)` / `| ID | Decision |` table, and finds nothing under an undated heading.
> - Eight altered texts are refused: the author's four, plus `,` for `;` between items, a trailing space, an arms path outside `docs/r1/`, and an upper-case commit.
> - The T0 row on main equals `row_text("T0","traindev", …)` with the same values, so the template is consistent.
> - `g5_seal.UNSEAL_ROW, TEST_ROW` equal `release.ROWS[("T1",…)]`. The PURPOSES names in the draft are exact.
> - `r1/c3/release.py` is byte-identical at a9d8ff5e, 000ac3b1, 89899f76, 30e2d51a and e41b414a (sha256 prefix 02b94721…). a9d8ff5e is an ancestor of origin/main and of the branch. So citing it is valid while release.py is unchanged (`release_row(writing=True)` plus `_published_clean`).
> - The ordering claim holds. `g5_integrity` takes `test=test_released("T1")`, so with the test row on PLAN the train/dev release runs the test-stage re-derivation. That needs `evaluation_block.jsonl` and `evidence_completion_test.json`.
> - The CLI matches: `assemble` has `--stage/--table/--evidence/--note`; release has `--source g5` with no sweep options; the note name is `c3_t1_labels_<YYYYMMDD>.md`.
> - The report's §3 item 7 is confirmed: the R1-G5-MEM-E4 text on main lacks "G5-MEM", so `launch` would refuse.
> - `test_c3_release.py`: 43 passed.
>
> ## Findings
>
> ### B
> None.
>
> ### M
>
> **M1. The T1 features and the release order contradict the features unit.**
> - Where: draft §5 item 3, report §3 item 3, report §1 ("`features: {}`"), and the §2 preconditions.
> - Problem: the draft says T1 "can be released (this row) but cannot be used to train arms, so it would not be in the arms-frozen record". That is wrong on four counts:
>   - Under the features unit (mac-t1-features-20261123 @ 2530d8e6), the features are computed inside `g5_assemble.node_rows` and written into `proposals.jsonl`/`build.json`. They are table bytes.
>   - `arms_freeze.check_record` requires `feature_tables.g5.proposals_sha256 == label_tables.g5.proposals_sha256` (the released table), and `training_rows` refuses rows without every FEATURES key. So a T1 release built without features cannot feed the arms. It would force a second assembly and release under the same row.
>   - The features report §5 says D1–D6 must be settled before the G.5 train/dev assembly. Its §6 item 4 says `g5_features.py` and `g5_noise.py` must be on main before the G.5 launch, under the freeze.
>   - Leaving T1 out of the record contradicts STOP 14: only an author row may freeze the arms without a node, and under PRE-T1 A an empty T1 set forecloses the T1 test row for good.
> - Related: the T0 runbook on main (I-P10) goes "T0-only" when T1 labels are absent and does not run freeze-wait.
> - Fix:
>   - Add precondition 0 to R1-T1-LABELS-UNSEAL: the ARMS-T1FEAT unit is merged on main before the G.5 launch, and its author decisions (D1–D6) are signed before the train/dev assembly.
>   - Rewrite open point 3 to match.
>   - State that the arms-frozen record is not committed while freeze-wait fails or STOPs, and that A3 is retrained with `--table/--release-root g5` once T1 is released. The coordinator holds the record that the deepthought runbook delivers.
>
> **M2. The T1 noise derivation (δ_n) is not addressed.**
> - Where: draft §1/§2/§5, report §3.
> - Problem:
>   - PRE-DELTA A requires both T1 σ_node and δ_n from the G.1b summary, with "path and sha256 recorded in the T1 train/dev release row". `g5_noise.py` derives D18's δ_n from each G.1b run's `runs.jsonl` (decision D6), bound only through the summary's `assembly_sha256` → `ASSEMBLY.json` → `runs_sha256`.
>   - The row cannot cite those copies. `_G1B_ITEM` allows one item per node, `release_row` refuses a repeated node, and `noise_by_node` requires the cited pair to equal the spec's `noise_floor.seven` or the AR record's copy.
> - Fix: add an open point. Whichever D6 option is chosen must bind through the summary's hash chain or through the arms-frozen record and a reviewed noise record, not through this row. Citing extra files would need a `release.py` change, which means a new release commit (REL-CODE A limit). Say whether PRE-DELTA's "recorded in the row" is met transitively, or needs an author note.
>
> **M3. The test-row precondition on `label_tables.g5` is not checked by the command given.**
> - Where: draft §3, precondition 2 and the Commands block (`python -m r1.c3.arms_freeze check --record <PATH>`).
> - Problem: `check_record` re-hashes a source's train/dev receipt and partition only for the sources passed in `--release-root`. No code ties the record's `label_tables.g5` to the g5 receipt that the test release step later opens.
> - Fix: use `<PY> -B -m r1.c3.arms_freeze check --record <PATH> --release-root g5=<T1_RELEASE_ROOT>` on TASL-2, plus `--artefact-root` where the arms artefacts live. Add explicit procedural STOPs for:
>   - `t1.suites` not equal to the node set R1-T1-LABELS-UNSEAL released;
>   - `g1b_summaries` not equal to the row's (path, sha256) pairs.
>   No code checks either.
>
> **M4. The freeze is described wrongly and precondition 5 has no executable check.**
> - Where: draft §5 item 4, report §3 item 4, §2 precondition 5.
> - Problem: the draft says a change to the G.5 files on main "makes `g5_integrity` refuse (fail-closed)". In fact `_g5_unpublished` compares HEAD with `origin/main`, and the procedure makes them equal. The assembly and the train/dev release run the same current code, so a change on main before the train/dev assembly is never detected. A later change refuses only if it alters derived bytes, and then only at the test stage. Only the spec is truly bound, through every sealed record's `spec_sha256`.
> - Fix: correct the statement. Make precondition 5 checkable, for example: `git diff --quiet <note paper_commit or the launch commit> origin/main -- sweep2/t1_tasl sweep2/g1b sweep2/g4 sweep2/s2_c2_lib.py` (the spec bound by the note's `spec_sha256`), run before each stage. Keep asking for the PLAN row or coordinator rule.
>
> ### m
>
> **m1. The signed note must not change between the two stages.**
> - Where: §3 precondition 4, and the freeze-wait bullet ("if an author row has moved the date in the note").
> - Problem: `build.json` records `readings.note_sha256` and `train_dev_row.decision_sha256`. Any amendment of the note after the train/dev assembly makes the test-stage assembly and `g5_integrity` refuse.
> - Fix: add "the note unchanged since the train/dev assembly" to the test-row preconditions and to the freeze.
>
> **m2. The cluster commands are underspecified.**
> - Problem: the relative paths `sweep2/t1_tasl/g5_tasl.py` and `-m r1.c3.release` assume the working directory is `<PAPER>`, but the commands use `git -C`. "HEAD = origin/main" is only a comment. `<PY>` on TASL-2 must be able to import `r1.c3` (numpy via `dataset`), and no such interpreter has been established on TASL-2.
> - Fix:
>   - Add `cd <PAPER>` and `test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"`.
>   - Name the interpreter and environment, as the sweep precedents did (`PYTHONDONTWRITEBYTECODE=1`, thread variables).
>   - Say how `check_seven_copy` is run, since it has no CLI.
>
> **m3. The gate sha256 citation departs from the G.5 draft.**
> - Problem: G.5 draft §6 item 1 says the train/dev row cites the gate v3.1 sha256. The code template does not; the gate is bound through the preregistration's `gate_sha256`.
> - Fix: draft §1 explains this, but list it in §5 as an explicit difference from G.5 draft §6 for the author.
>
> **m4. The machine-check script cannot be reproduced.**
> - Problem: it lives only in `/tmp/docdev/b/check_rows.py`.
> - Fix: include it, or its essential lines, in the report so later reviewers can reproduce it.
>
> Housekeeping (not the author's fault): the worktree had ignored `r1/__pycache__` and `r1/c3/__pycache__` (cpython-313, from before this review). I did not touch them. My scratch is in `/tmp/t1rowsrev/_to_delete/`.
>
> VERDICT: NOT ACCEPTED (M1–M4: the row texts are correct, but the features/release ordering, the δ_n binding, the arms-record check command and the freeze statement must be corrected before the drafts go to the author)

## Round 2 (`c78f6a1d`)

> Reviewed base: c78f6a1d7fd05f59f4c1e4d91f91cadebbeb26bb (round 2; mac-t1-release-rows-20261123, merge 4eff72a4 of baf6be5d; features unit compared at a5715142f)
>
> ## Summary
>
> The row texts and the M3, M4 and m1–m4 fixes are now right. Two places still do not match the features unit at a5715142, which you asked me to check: precondition 0 and open point 3a. Both feed what the author signs, so this is not accepted yet. The fixes are docs edits only.
>
> **Re-checked this round:**
> - **Row texts:** no fenced line changed between e41b414a and c78f6a1d. My fresh script (the old scratch had already been cleared) gives:
>   - both texts equal `row_text`;
>   - both fullmatch `row_pattern`;
>   - `author_rows` finds both, with exact text.
> - **`release.py`:** still 02b94721… at the tip, so citing a9d8ff5e stays valid. `arms_freeze.py` at the tip equals origin/main.
> - **M3:** `arms_freeze check --release-root g5=… --artefact-root …` plus the two procedural STOPs (`t1.suites`, `g1b_summaries`). Correct.
> - **M4:** the freeze statement is now accurate. Precondition 5 runs `git diff --quiet <G5_LAUNCH_COMMIT> origin/main -- …` before each stage, with the spec bound by `spec_sha256`. Correct.
> - **m1:** the note must stay unchanged from the train/dev assembly on, because `build.json` records its sha256. Correct.
> - **m2:** `cd`, the clean-checkout and HEAD tests, the environment and the `check-ar-record` line are fine. I ran the `check_seven_copy` one-liner from the worktree with `-B`. It imports and reaches `check_g1b_copy`, then STOPs as expected on today's unfilled spec. On success it prints the `qualifies_D21` map; it reads only the summary and the gate copy.
> - **m3, m4:** correct.
> - **M1 order and the coordinator hold:** correct (A3 retrained with g5; the record held while freeze-wait fails or STOPs).
>
> ## Findings
>
> ### B
> None.
>
> ### M
>
> **M1. Precondition 0 does not match the features unit's decisions and deadlines.**
> - Where: draft §2 precondition 0, §5 item 3, and report §3 item 3 and §4 (all say "D1–D6 signed before the launch").
> - What the unit says at a5715142 (report §5, §6 item 4):
>   - D1–D4, **D6-σ, D8 and D9** must be final, with the code that implements them on main, before the launch.
>   - D5 is already decided by R1-ARMS-DECISIONS.
>   - D6 (the copy step) is due before the gate run's noise is built.
>   - D6-σ B needs D6 A or B, so in that case D6 is also due before the launch.
>   - **D7 is due before the arms-frozen record.** Without a T1 input for A5, `gate_input_builder.TEST_SERIES` (A2, oracle, A3, A5) cannot supply T1, and PRE-T1 A then freezes an empty T1 set. That closes off the T1 test row for good.
> - Problem: as written, the draft drops D6-σ, D8 and D9 (all table bytes), and misdates D6. It also never names D7 as a gate on the T1 test row.
> - Fix:
>   - Restate precondition 0 with the unit's §5 deadlines.
>   - Add D7 to the §3 Order and preconditions: a T1 input for A5, signed and built, before the arms-frozen record; otherwise a STOP to the author.
>   - Update §5 item 3 and report §3/§4 to match.
>
> **M2. Open point 3a needs three corrections against the features unit and `arms_freeze`.**
> - Where: draft §5 item 3a, report §3 item 3a.
> - (a) **σ_node.** "For σ_node it is met directly" holds only under D6-σ A, where σ_node is the summary's `sigma_joint`. Under D6-σ B, σ_node comes from the bound `runs.jsonl` through the same hash chain as δ_n. It is then met only transitively, and it needs D6 A or B plus a `noise_by_node` change and a spec field on main before the launch.
> - (b) **D6 A.** Under the unit's D6 A, the copy needs an author row that amends REL-T1-G1B's copy list. The review ruling makes A acceptable only with that row. 3a describes D6 A as just "a reviewed copy" and does not mention the row.
> - (c) **The second binding route does not exist in code.** 3a offers "the arms-frozen record and a reviewed noise record (`g5_t1_noise/1`, its sha256 in the record's noise-source entries)". In fact `arms_freeze.check_record` pins `noise_source` to the T0 file (`_pin(..., NOISE_PATH, NOISE_SHA256)`). The record has no T1 noise slot, and an extra key would go unchecked.
> - Fix:
>   - State the D6-σ dependence.
>   - Name the REL-T1-G1B amendment row under D6 A.
>   - For (c), either say a T1 noise field needs an `arms_freeze` change, or say that binding is procedural only, where the gate input takes the record by sha256 through `g5_noise.builder_noise(sha256=…, raw=…)`.
>
> ### m
>
> **m1. The arms check may need to run on two hosts.**
> - Where: §3 Commands, `arms_freeze check … --release-root g5=… --artefact-root …` "on TASL-2".
> - Problem: the arms artefacts are written by the deepthought arms run, and the g5 release root is on TASL-2. They may not be on one host.
> - Fix: allow the check to be split, re-hashing the artefacts where they live and the g5 receipt on TASL-2. The checker handles each independently.
>
> **m2. The one-liner should use `-B`.**
> - Where: §2 Commands, the `check_seven_copy` one-liner.
> - Problem: `-I` ignores `PYTHONDONTWRITEBYTECODE`, so the one-liner writes `__pycache__` into the checkout. The files are ignored, so this is harmless.
> - Fix: add `-B`.
>
> Process note: the worktree already held ignored cpython-313 `__pycache__` directories (r1/, r1/c3/, and sweep2/… from 14:48) from runs that were not mine; my interpreter is 3.12. My scratch is in /tmp/t1rowsrev/_to_delete/.
>
> VERDICT: NOT ACCEPTED (M1: precondition 0 must follow the features unit's decision deadlines — D6-σ, D8, D9 before launch, D7 before the arms-frozen record; M2: point 3a must cover D6-σ, the REL-T1-G1B amendment row under D6 A, and the missing T1 noise slot in the arms-frozen record)

## Round 3 (`f4be4cb4`)

> Reviewed base: f4be4cb43ae6f8c1212926913656616b3739bf4c (round 3; diff c78f6a1d..f4be4cb4, including merge 55716fa3 of 2582c898; features unit compared at a5715142 and at the delivered 030b80a0)
>
> ## Summary
>
> Every round-2 finding is fixed correctly. Nothing that ships changed except the docs.
> - **Row texts:** no fenced line changed.
> - **Release code:** `r1/c3/` is unchanged between c78f6a1d and f4be4cb4, and `release.py` is still sha256 02b94721…, so citing a9d8ff5e stays valid.
> - **The merged code:** the `g5_tasl.decision_row_checks` refactor touches no part of the code the rows depend on.
>
> **M1 (precondition 0) is fixed.** It now follows the features unit's report §5 deadlines. I checked them against a5715142; that section is the same at 030b80a0.
> - D1–D4, D6-σ, D8 and D9 must be final, with their code on main, before the launch.
> - D5 is already decided.
> - D6 is due before the gate-run noise, or before the launch under D6-σ B.
> - D7 is due before the arms-frozen record.
> - The note that D6-σ B would change the spec sha256 and possibly the `t1_table_readings` line is correct. TABLE_READINGS' `sigma_cmp` text names `sigma_joint`.
> - D7 is now §3 Order step 2 and test-row precondition 3, with a STOP to the author if unsettled. This matches `gate_input_builder.TEST_SERIES` (A2, oracle, A3, A5).
>
> **M2 (point 3a) is fixed.**
> - (a) σ_node is met directly only under D6-σ A.
> - (b) The author row that amends REL-T1-G1B's copy list is named under D6 A, as the unit's review ruled.
> - (c) The draft now says correctly that `check_record` pins `noise_source` to the T0 file and has no T1 slot. The procedural route it offers is accurate: `g5_noise.builder_noise(record, sha256=…, raw=…)` at 030b80a0 refuses bytes that do not hash to the given sha256, and the record argument is ignored once raw bytes are passed.
>
> **m1 and m2 are fixed.** The arms check may be split across hosts with both runs required to pass, and the one-liner now runs with `-I -B`.
>
> ## Findings
>
> ### B
> None.
>
> ### M
> None.
>
> ### m
>
> **m1. Stale "record pending" wording and the cited features tip.**
> - Where: draft §2 precondition 0 and §5 item 3; report header, §3 items 3 and 8.
> - Problem:
>   - Both review records now exist: features `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md` on mac-t1-features-20261123 @ 030b80a0, and the G.5-on-main record on mac-g5-code-main-20261123 @ deb888cc.
>   - The features unit was delivered as READY 92 at 030b80a0, not a5715142.
>   - Between those two commits `g5_noise.py` changed only its `refuse_sealed` mechanism. Nothing the drafts cite is affected.
> - Fix: when the drafts next go out, replace "review record pending" with the record paths, and cite the delivered tip (READY 92 @ 030b80a0, accepted a5715142, confirmed b033050e). This does not block shipping.
>
> I created no scratch this round (/tmp/t1rowsrev holds only `_to_delete`), and the worktree is clean.
>
> VERDICT: ACCEPTED

## Round 4 (`17bdf8cd`)

> Reviewed base: 17bdf8cd7b3e6241a6465f73c76a3e373d015f81 (confirmation round; diff f4be4cb4..17bdf8cd, one docs commit)
>
> ## Summary
>
> This round fixes the one remaining minor from round 3: the drafts now cite the delivered review records. The commit changes 5 lines in the two draft files and nothing else, so the row texts and the code are untouched.
>
> **What I checked:**
> - **Features unit:** the drafts now cite `mac-t1-features-20261123` @ `030b80a0` (READY 92). The review record there, `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md`, has the rounds table "1 `2530d8e6` NOT ACCEPTED; 2 `a5715142` ACCEPTED; 3 `b033050e` ACCEPTED (confirmation)". So "accepted at a5715142, confirmed at b033050e" is accurate.
> - **G.5-on-main row check:** the drafts now cite `docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md` on `mac-g5-code-main-20261123` @ `deb888cc` (READY 91). That commit is the review record, "accepted ebe7fb8c, confirmed 2582c898", and the file ends "VERDICT: ACCEPTED". So "accepted … and is `g5_tasl.decision_row_checks` since `2582c898`" is accurate.
> - **Leftover wording:** no "record pending" remains in either file (grep).
>
> ## Findings
>
> None (B: none, M: none, m: none).
>
> Read-only throughout; I created no scratch this round.
>
> VERDICT: ACCEPTED

---

Code-Commit: 17bdf8cd7b3e6241a6465f73c76a3e373d015f81
Verdict: ACCEPTED

Accepted at `f4be4cb4`, confirmed at `17bdf8cd`; both rows stay approved: false.
