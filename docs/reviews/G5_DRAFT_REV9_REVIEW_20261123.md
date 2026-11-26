Reviewed base: `30e2d51a`, merged forward to `2582c898` (READY 91's code); accepted at `91d78f3a`, confirmed at `e2423fa96ecf7102ede13d26657da358ecadfaf5`

# Independent review record — G.5 authorization draft revision 9 (text only, approved: false), against main 89899f76 and the G.5 code of READY 91

**Unit.** On `mac-g5-draft-rev9-20261123`: `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md` revised to revision 9 (approved: false) and the change report `docs/r1/reports/g5_code_20261123/G5_DRAFT_REV9_20261123.md`. Docs only; no code or spec change. Folded in: the TASL-2 AR-pin host-check binding record PASS (`cce9b8fb…`, after R1-G1B-AR-PY) and the signed third G.1b note; R1-G1B-JOIN; the published TASL launch chain; the re-issued G.4 note `g4_t1_tasl_20261123.md`; R1-ARMS-DECISIONS, R1-G5-DECISIONS-2 (§11 items 1–8 signed, A each; items 9–19 open, fixed at the note's signature) and R1-G5-MEM-E4; §5 equal to `g5_tasl.py key-lines` for the spec (53 lines, spec sha256 `3627cc16…`; the five 3b-1 readings shown as signed text, not code-checked); §6's gate binding through the preregistration's block; §9 the code built (3a, 3b-1, 3b-2) and the harness unit separate; the G5-MEM A row check as `g5_tasl.decision_row_checks` (READY 91); the ARMS-T1FEAT dependency (READY 92) with its decisions and deadlines (D1–D4, D6-σ, D8, D9 before the launch; D6 before the gate-run noise, or before the launch under D6-σ B, with an author row amending REL-T1-G1B under D6 A; D7 before the arms-frozen record; D5 decided). Authority: the user's queue of 23 Nov 2026 (14:02), item 3.

**Process.** One independent reviewer, read-only. Round 1 found the E4 row check described as a blocker after the code fix `baf6be5d` had removed it (M1) and four minors; round 2 found the ARMS-T1FEAT dependency not carried into §3, §5, §11 and P5, so that signing `t1_table_readings` would silently settle D6-σ (M1), and one minor; round 3 accepted with one minor ("record pending" out of date), fixed and confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `b5ab1b1b` | NOT ACCEPTED (M1; minors m1–m4) |
| 2 | `16da3acc` | NOT ACCEPTED (M1 round 2; m1) |
| 3 | `91d78f3a` | ACCEPTED (m1 round 3) |
| 4 | `e2423fa9` | ACCEPTED (confirmation) |

**Open items.** (1) The draft stays approved: false; §11 items 9–19 (the values the signature fixes and the new note lines) and every `<…>` field after the pilot are the author's at signature. (2) The ARMS-T1FEAT decisions (D1–D4, D6-σ, D8, D9) before the launch; under D6-σ B the spec and the `t1_table_readings` line are re-issued before signature; D6 A needs an author row amending REL-T1-G1B's copy list. (3) The harness unit (`trackg/audit_g5.py`) must be reviewed and its two commits published before P5 can cite it. (4) Follow-up for the code unit (READY 91), not this draft: the `decision_row_checks` docstring, the 3A report amendment and the G.5-on-main review's open item (2) say a single row serving as both the decisions and the E4 row "is refused"; `plan_row` strips only the id cell, so a row whose text names its own id with "E4" and "memory modes" would pass.

## Round 1 (`b5ab1b1b`)

> Reviewed base: 30e2d51a6 (code branch at the draft's base), unit tip b5ab1b1be591e9f2521e53db523568b85ac42a0c, against origin/main 89899f765fc4134c05897bf079ced3ecb95314f2 and the G.5 code fix baf6be5de1a87fb84233a9fe1a3a4339dd438bdb
>
> ## Summary
>
> The revision is careful and nearly all of it checks out against main and the code. One point is now wrong, and it is the one the coordinator asked about. The draft and the change report still say the switch's E4 row check refuses R1-G5-MEM-E4, calling it "a blocker for every G.5 job under G5-MEM A". The code branch fixed that check at `baf6be5d`. The unit is text-only, but it was written on `30e2d51a`, before that fix, and it repeats the stale claim in about nine places. So it should not ship as it is.
>
> **What I checked and found correct:**
> - **AR host-check record.** On main, sha256 `cce9b8fb…`. It records `host_check_items: 1-7 PASS` and `host_check_verdict: PASS` at `2d09f9a9`, and is the rerun after R1-G1B-AR-PY (`52f4e3e5`). It was merged by `e9c12a4a`, and its R4 review exists. Item 7 (CUDA IPC) is untested, as the draft says.
> - **Third note.** `g1b_ar_t1_tasl_20261122.md` is on main: `approved: true`, sha256 `ac5ee6c5…`, `paper_commit` `570ae410`, `spec_sha256` `65da95db…`, harness `2d09f9a9`. It was committed in `9f23fea8` together with R1-G1B-JOIN.
> - **Rows.** R1-G1B-JOIN and R1-G1B-AR-PY are paraphrased faithfully. R1-G5-DECISIONS-2 is quoted word for word (I compared it by script). R1-G5-MEM-E4 and the parts of R1-ARMS-DECISIONS that bear on G.5 are paraphrased faithfully.
> - **Launch chain.** All of these are on main and match `launch_table.json`:
>   - merges `38ae4a05` and `5d5ca7b4`;
>   - launch commits (a) `34a5b1d6`, (b) `b5824240`, (c) `6ad899e0`, (d) `d52c9d9d`;
>   - spec sha256s `7ff3c95b…`, `a9e6b463…`, `fd9c6e9d…`, `65da95db…`;
>   - erratum `4b7452b6`, sha256 `9b40944b…`;
>   - the publication record, the launch table and the chain review.
> - **Re-issued G.4 note.** `g4_t1_tasl_20261123.md`: sha256 `89e50a9c…`, `paper_commit` `b5824240`, spec `fd9c6e9d…`. It was signed by the coordinating chat under R1-T1-DATA-MANIFEST, supersedes the 22 Nov note, and nothing ran under the old one. The spec's `pilot_basis` names it.
> - **Other citations.** The T0 release merges `dc9ad88a` and `a454d6db`, the P1 record `681011b2…`, and the `arms_freeze.py` record format (`r1_c3_arms_frozen/v1`, one fenced JSON block, `t1`, `g1b_summaries`, and `label_tables.g5` when T1 nodes are present) all match.
> - **Decisions recorded only from rows.** §11 items 1–8 are marked signed by R1-G5-DECISIONS-2. Items 9–16 keep revision 8's numbering, which is the numbering the row refers to. Items 17–19 are open, as "the new note lines". Nothing is recorded as decided by chat, and `approved: false` is kept.
> - **§5.** I re-ran `g5_tasl.py key-lines sweep2/t1_tasl/g5_tasl_spec.json` from the rev9 worktree (rc 0, 53 lines, spec sha256 `3627cc16…`). Compared by script, the draft's block is identical except the first line, `approved: false`. With `--k 6 --k-row …` only `audit_K` and the two seed lines change. The output at `baf6be5d` is byte-identical: same spec, and the fix touches only `launch()`. The change report's 17 unchanged / 25 changed / 10 new lines is correct.
>   - The first three 3b-1 readings and `reuse_parent_runs_false` are verbatim from the 3b-1 report §7.
>   - The updated `gpuh_b_meter` follows 3b-2 §1.4 (see m1).
>   - None of the five readings appears in `note_lines`, as the report says.
> - **§6.** `release.row_pattern("T1","traindev")` has no gate field. `release_row` → `prereg_frozen` checks the preregistration block's `gate_sha256` and `gate_input_builder_sha256` against the committed files, so the correction is right.
> - **§9.** The code is built: the three review files on the branch each say `Verdict: ACCEPTED`. The harness unit is described as separate, correctly.
> - **Scientific content.** None changed. The edits are status updates, citations, and descriptions of the built and reviewed code. Only the two docs files changed.
> - **Change report.** Its 19 stale statements are real and each is fixed in the draft. It is incomplete only where M1 makes it out of date.
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
>
> **M1. The E4 row check is described as it stood before `baf6be5d`.**
>
> *Where (draft):*
> - Status, lines 7–8 (code at `30e2d51a`, merged with `000ac3b1`) and lines 46–50 ("as the code stands the switch refuses every job under G5-MEM A").
> - §1, the R1-G5-MEM-E4 row's parenthesis.
> - §2.3, lines 151–156.
> - §5 intro, line 581, and the PENDING table rows `decisions` and `e4_amendment_row` (lines 670–671).
> - P6, lines 867–868.
> - §9 "Remains, before any G.5 job", lines 946–948.
> - §11, lines 1008–1013, item 3 (lines 1019–1020), and line 1059.
>
> *Where (change report):* §1 (the §2.3 row), §4 items 3–4, §5 second bullet, §6 last bullet.
>
> *Problem:* At `baf6be5d` (the tip of `mac-g5-code-main-20261123`, after merging main `89899f76` in `ecfd86a5`) the switch checks:
> - the decisions row with the eight `<decision> A` terms **plus the E4 row's id**, `R1-G5-MEM-E4`, under G5-MEM A;
> - the E4 row with the terms "E4" and "memory modes".
>
> I ran `g5_tasl.plan_row` on main `89899f76`'s PLAN:
> - R1-G5-DECISIONS-2 with the new terms: PASS.
> - R1-G5-MEM-E4 with ("E4", "memory modes"): PASS.
> - R1-G5-MEM-E4 with the old ("E4", "G5-MEM"): STOP, as the draft says, but that check no longer exists.
>
> So the draft's "blocker", "two ways out, neither taken" and "Until the check or the row changes, the switch refuses every G.5 job" are now false. Its description of the decisions-row check is also incomplete: that check now requires the E4 row id as well. I found no review record for `baf6be5d` on the branch.
>
> *Fix:* Base the draft on `baf6be5d`, or cite it. §5 and the spec sha256 stay as they are. In each place listed, say that:
> - the switch checks the decisions row for the eight options and the E4 row's id;
> - it checks the E4 row for "E4" and "memory modes";
> - both rows pass against main `89899f76`'s PLAN.
>
> Remove the E4 item from §9 "Remains", or move it to "built on the branch, review pending" if the fix is not yet reviewed. Update the change report to match.
>
> ### m (minor)
>
> **m1. §5, `gpuh_b_meter` line (line 686), and §11 item 19.** The line says "a gap in the server numbers, counts as open until now". 3b-2 §1.4 says a gap counts as open "from the previous registered server's stop (or the earliest known start) until now". This line is offered as signed text, so it should say exactly that: add the start point.
>
> **m2. §5 block versus §11 items 9–16.** The block now prints the spec's proposed values without the *(proposed)* marks revision 8 had, for example `liveness_floor: 0.25 (proposed)`. Affected values include `liveness_floor 0.25`, `freeze_wait 2026-12-18`, `cap_gpu_hours 425` and the acceptance branch of `cuda_ipc`. The rest of the draft keeps them open. Add one sentence to the §5 intro: the values governed by §11 items 9–19 are the spec's proposals and are fixed at signature.
>
> **m3. §4 STOP 9, last sentence.** "A missed audit-chunk deadline is a node STOP (the author decides)" is new text with no source. The other built readings in the revision cite theirs. Cite it as the built behaviour (part 3b-1 review m5) so it reads as a description of the code, not a new rule.
>
> **m4. §1, R1-ARMS-DECISIONS row.**
> - The cell's parenthesis "(READY 87; the arms-frozen record's code `r1/c3/arms_freeze.py`, merge `630398c6`)" reads as row content. The row itself names `mac-t0-arms-readiness-20261123` @ `4e4d6d1a` and the readiness report.
> - The cell also says the record format "is what R1-T1-LABELS-TEST-RELEASE cites". That row does not exist yet; `release.row_pattern` says it will cite the record by path and sha256.
>
> Mark both as context, not row text.
>
> VERDICT: NOT ACCEPTED (M1: the draft and change report describe the E4 row check from before baf6be5d; with the coordinator's fix both rows pass against main 89899f76, so the "blocker" statements in the status, §2.3, §5, P6, §9 and §11 must be updated)

## Round 2 (`16da3acc`)

> Reviewed base: 16da3acc5b8b35a94267feefb7d542899a9f45c4 (merge b0cd020d of mac-g5-code-main-20261123 @ baf6be5de1a87fb84233a9fe1a3a4339dd438bdb; origin/main 89899f765fc4134c05897bf079ced3ecb95314f2)
>
> ## Summary (round 2)
>
> Every round-1 finding is fixed correctly. The unasked addition about the T1 features unit is accurate as far as it goes, but it stops short. It introduces a dependency on the ARMS-T1FEAT unit and that unit's open author decisions. One of those decisions, D6-σ, governs a line the G.5 note itself signs. The dependency is not carried into §3, §5 or §11, so I can't accept it yet. The fix is a few sentences.
>
> **What I checked and found correct:**
> - **The merge.** `b0cd020d` is clean. Against `baf6be5d`, the tip differs only in the two docs files. The spec is unchanged (sha256 `3627cc16…`). Round 1 showed `key-lines` prints byte-identical output at `30e2d51a` and `baf6be5d`, so the §5 block still stands.
> - **M1 (the E4 row check).** The check is now described as of `baf6be5d`: the decisions row is checked for the eight options plus the E4 row id, and the E4 row for "E4" and "memory modes". Both rows pass against main `89899f76`, which I confirmed with `plan_row` in round 1. The fix is marked "built on the G.5 branch, review pending"; no review record for it exists yet, at `baf6be5d` or at `ebe7fb8c`. It is fixed in the status, the revision log, §1, §2.3, the §5 intro and rows, P6, §9 and §11. In the report it is fixed in the header and in §1, §4, §5 and §6. No stale "G5-MEM", "blocker" or "fails" wording is left. The report's history note in §4 item 4 is accurate.
> - **m1.** The gap wording now matches 3b-2 §1.4.
> - **m2.** The §5 intro sentence is there and lists the right items.
> - **m3.** STOP 9 cites the 3b-1 report §6, review m5 row ("Both deadline STOPs are node class"). That citation is correct.
> - **m4.** The R1-ARMS-DECISIONS cell now carries the row's own reference (`4e4d6d1a`, the readiness report §3). The context is marked as context, and the test row is described as "not yet a row, will cite the record by path and sha256".
> - **Report §7.** It maps every finding to its fix.
> - **The features addition, checked against `mac-t1-features-20261123` @ `a5715142` (on `baf6be5d`):**
>   - The unit adds `g5_features.py` and `g5_noise.py`, changes `g5_assemble.py`, and adds two `IMPORT_SOURCES` entries in `g5_tasl.py`. The spec is unchanged.
>   - The features become table bytes. They sit under `G5_PATHS`, so they are frozen from launch to the test release.
>   - At `baf6be5d` the table carries `features: {}`, and `arms_freeze` refuses a row without the features.
>   - No review record exists yet, which matches "under review".
>   - The unit report §5 says its decisions D1–D4, D6-σ, D8 and D9, and the code for them, must be on main before the G.5 launch. The draft's "before the G.5 launch" matches that.
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
>
> **M1 (round 2). The ARMS-T1FEAT dependency stops at §6 step 2 and §9. The open decisions in it that change G.5's own signed content are not named.**
>
> *Where:*
> - §3 (lines 482–485, "σ̂_node is the G.1b `joint` σ …").
> - §5, the `t1_table_readings` line ("sigma_cmp = sigma_node (the node's G.1b joint sigma)") and the PENDING table.
> - §6 step 2 (lines 783–787).
> - §9, last paragraph.
> - §11, "Rows and records needed before the signature" (line 1067 onwards) and "After the table" (lines 1079–1082).
>
> *Problem:*
> - **D6-σ (the T1 σ_node definition) is open, with no recommendation.** `T1_FEATURES_20261123.md` §3 and §5 on `a5715142` define it. Option B (T0's definition) needs a change to `g5_assemble.noise_by_node` and a new spec field, on main before the launch. That would change the spec sha256 and possibly the `t1_table_readings` line. σ_node scales `recorded_gain_z`, the soft-label width and g. As written, signing the G.5 note's `t1_table_readings` line would quietly decide D6-σ A. If the author chooses B instead, §5 and the spec sha256 change.
> - **D6 (the source of T1 δ_n), recommended option A,** needs an author row amending REL-T1-G1B's copy list (`ASSEMBLY.json` and `runs.jsonl` beside the summary copy). That changes the REL-T1-G1B step described in §3 and §6 step 1.
> - **D7:** without a T1 input for A5, `TEST_SERIES` keeps T1 out of the read, and PRE-T1 A would freeze an empty T1 set. This has to be settled before the arms-frozen record.
> - **§11 does not match the new §6/§9 text.**
>   - "Before the signature" does not list the features unit on main or its decisions row.
>   - "After the table" still presents the features only as something the arms-frozen record needs.
>   - P5 reads "G.5 job code … reviewed at the launch commit", but the launch commit will carry the features unit's code in `sweep2/t1_tasl`. So that unit's review belongs among P5's reviews, or beside them.
>
> *Fix:*
> - In §6 step 2 and §9, name D6-σ, D6 and D7 and their deadlines: D6-σ and D6 before the launch, D7 before the arms-frozen record.
> - In §3 and §5, say that the σ_node definition and the `t1_table_readings` text are open under D6-σ. Under B, the spec and the line are re-issued before signature.
> - In §11, add the ARMS-T1FEAT unit on main (reviewed) and its decisions row to "Rows and records needed before the signature", and update "After the table".
> - In P5, cover the features unit's review.
>
> ### m (minor)
>
> **m1 (round 2). §6 step 2, line 784.** "R1-ARMS-DECISIONS (ARMS-T1FEAT A) gives them [the features and δ_n] to a reviewed CPU unit" says more than the row does. The row says "a reviewed CPU unit gives G.5 rows the features"; δ_n is not in it. The unit took on δ_n (`g5_noise.py`) itself. Reword along these lines: "gives the features to a reviewed CPU unit; that unit also builds the T1 δ_n input and the suite mapping".
>
> (Housekeeping: round-2 scratch is in `/tmp/rev9rev/_to_delete/`. The round-1 scratch I had moved there earlier was no longer present when I looked; I did not remove it. The worktree is untouched.)
>
> VERDICT: NOT ACCEPTED (M1 round 2: the T1-features dependency is not carried into §3, §5 and §11; D6-σ, which the `t1_table_readings` line would silently settle, and D6, which amends the REL-T1-G1B copy list, are open author decisions due before the launch and must be named)

## Round 3 (`91d78f3a`)

> Reviewed base: 91d78f3aed9e2449a3bf3eb92483fd42c068687c (merge 92b64980 of mac-g5-code-main-20261123 @ 2582c8980; origin/main 89899f765fc4134c05897bf079ced3ecb95314f2)
>
> ## Summary (round 3, diff 16da3acc..91d78f3a)
>
> Both round-2 findings are fixed. One minor remains: the "record pending" wording is now out of date. It does not block shipping, and you can apply the wording yourself as you offered.
>
> **Code at `2582c898`:**
> - The refactor into `g5_tasl.decision_row_checks` keeps the same terms as `baf6be5d`: the decisions row is checked for the eight `<decision> A` options plus `R1-G5-MEM-E4` under G5-MEM A, and the E4 row for ("E4", "memory modes"). `launch()` calls it.
> - I ran it against main `89899f76`'s PLAN: R1-G5-DECISIONS-2 PASS, R1-G5-MEM-E4 PASS.
> - `key-lines` at `2582c898` and in the worktree is byte-identical to the draft's §5 block, apart from `approved: false`. The spec sha256 is still `3627cc16…`.
> - The merge `92b64980` brings in only code-branch files: the refactor, a test, the 3A report amendment, the merge report and two failure lists. The unit's own commit changes only the draft and its change report.
>
> **M1 (round 2) is fixed.** I checked it against `T1_FEATURES_20261123.md` §3 and §5:
> - **§3** says the σ_node definition is open under D6-σ. Under B it needs D6, a `noise_by_node` change and a spec field on main before the launch, so the spec and the `t1_table_readings` line would be re-issued before the signature. §3 also says D6 A needs a row amending REL-T1-G1B's copy list (`ASSEMBLY.json`, `runs.jsonl`).
> - **§5** has a new table row and a sentence: signing `t1_table_readings` does not decide D6-σ.
> - **§6 step 2 and §9** give the deadlines as the unit report does:
>   - D1–D4, D6-σ, D8 and D9 before the launch, with code on main;
>   - D6 before the gate-run noise, or before the launch under D6-σ B;
>   - D7 before the arms-frozen record, with the `TEST_SERIES` / empty-T1 consequence;
>   - D5 decided by R1-ARMS-DECISIONS.
> - **P5** cites the features unit's review, because its code sits in `sweep2/t1_tasl`.
> - **§11:** "before the signature" adds the unit on main and its decisions row, plus the re-issue under D6-σ B. "After the table" adds D6 and D7. Item 17 notes D6-σ.
> - The citation "part 3b-2 report §5 items 3–5" is correct: δ_n, features, suite names.
>
> **m1 (round 2) is fixed.** The sentence now says R1-ARMS-DECISIONS gives the features to the unit, and that the unit also builds the δ_n input and the suite mapping. That matches the row.
>
> **Change report §8** maps both findings to their fixes accurately. No scientific content changed in this round: the decisions recorded are the same, the §5 block is the same, and the options are the same.
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
> None.
>
> ### m (minor)
>
> **m1 (round 3). The review status is out of date.**
>
> *Where (draft):*
> - Status, line 8.
> - §2.3, §5 rows, P6, §9 (line 974), §11: "accepted by the G.5-on-main review, record pending".
> - §3, §6 step 2 (line 793), §9 (line 992): "ARMS-T1FEAT unit @ `a5715142`, accepted, review record pending".
> - P5, line 878: "accepted at `a5715142`".
> - Change report header, §4 item 4 and §5.
>
> *Problem:* Both review records exist now:
> - the G.5-on-main record, `docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md` on `mac-g5-code-main-20261123` @ `deb888cc`, accepted at `ebe7fb8c` and confirmed at `2582c898`;
> - the features record, `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md` on `mac-t1-features-20261123` @ `030b80a0`, accepted at `a5715142` and confirmed at `b033050e`.
>
> The features unit's code also changed after `a5715142`. `b033050e` replaces `g5_noise._refuse_sealed` with a copy of `analysis_guard.refuse_sealed` and adds two tests. So `a5715142` is not the confirmed unit commit.
>
> *Fix:* Replace "record pending" with the record paths and commits above. Cite the features unit as "accepted at `a5715142`, confirmed at `b033050e` (record `030b80a0`)". Note that both records still have to reach main with their units, as P5 requires.
>
> **Note (not a finding on this unit).** The 3A report amendment that came in with `2582c898`, and the `decision_row_checks` docstring, say a single row serving as both the decisions row and the E4 row "would have to cite its own id and is refused". `plan_row` only strips the id cell. A row whose text mentions its own id together with "E4" and "memory modes" would still pass, so "is refused" is not guaranteed by the code. The code unit can reword it; it does not affect this draft.
>
> Round-3 scratch is in `/tmp/rev9rev/_to_delete/`. The worktree is untouched.
>
> VERDICT: ACCEPTED

## Round 4 (`e2423fa9`)

> Reviewed base: e2423fa96ecf7102ede13d26657da358ecadfaf5 (one docs commit on 91d78f3a; code base mac-g5-code-main-20261123 @ 2582c8980; origin/main 89899f765fc4134c05897bf079ced3ecb95314f2)
>
> ## Summary (confirmation round, diff 91d78f3a..e2423fa9)
>
> The round-3 minor is fixed, the commit touches only the two docs files, and nothing else changed.
>
> **Checks:**
> - **Scope of the commit.** It changes only the draft and its change report (19 lines added, 20 removed). There is no code or spec change, so the §5 block, the spec sha256 `3627cc16…` and the row-check results from round 3 still stand.
> - **No "record pending" left.** A `git grep` at `e2423fa9` finds none in either file. Each place that said it now cites the record.
> - **G.5-on-main record.** `docs/r1/reviews/G5_CODE_MAIN_MERGE_REVIEW_20261123.md` exists at `deb888cc`. It shows round 1 ACCEPTED at `ebe7fb8c` and round 2 ACCEPTED (confirmation) at `2582c898`, which is an ancestor of `deb888cc`. The draft's citation, "READY 91 @ `deb888cc`", matches.
> - **Features record.** `docs/r1/reviews/T1_FEATURES_REVIEW_20261123.md` exists at `030b80a0`. It shows round 2 ACCEPTED at `a5715142` and round 3 ACCEPTED (confirmation) at `b033050e`, which is an ancestor of `030b80a0`. The draft's wording, "@ `030b80a0` (READY 92: accepted at `a5715142`, confirmed at `b033050e`)", matches. So does P5's "accepted at `a5715142`, confirmed at `b033050e`, review record on `030b80a0`".
> - **Open decisions and deadlines.** The features record lists D1–D4, D6-σ, D8 and D9 before the launch, D6 before the gate-run noise (before the launch under D6-σ B), D7 before the arms-frozen record, and D5 decided. That is the same as the draft's §3, §6 step 2, §9 and §11.
> - **Change report.** It is updated the same way, and the historical round mappings in §7 and §8 are kept.
>
> ## Findings
>
> ### B (blocking)
> None.
>
> ### M (major)
> None.
>
> ### m (minor)
> None.
>
> **Note (code unit).** The G.5-on-main review record's open item (2) repeats the "would be refused" wording about a single PLAN row serving as both rows. As you said, that is a follow-up for READY 91, not for this draft.
>
> Scratch: no new scratch was needed this round; earlier rounds' scratch is in `/tmp/rev9rev/_to_delete/`. The worktree is untouched.
>
> VERDICT: ACCEPTED

---

Code-Commit: e2423fa96ecf7102ede13d26657da358ecadfaf5
Verdict: ACCEPTED

Accepted at `91d78f3a`, confirmed at `e2423fa9`; the draft stays approved: false.
