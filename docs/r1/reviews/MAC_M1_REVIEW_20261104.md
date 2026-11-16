# MAC M1 review — `mac-int-20261104` (4 Nov 2026)

**Verdict: not accepted** (0 BLOCKING, 3 MAJOR, 11 MINOR).

Independent reviewer (Claude, fresh subagent; AI-assisted). Range reviewed: `10742f85..74fdebca` (commits `7da89e8c`, `02231384`, `5e96fa56`, `d5d59a67`, `1b7e7cdc`, `76625bb5`, `a43e1b47`, `74fdebca`). Governing task: `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md` rev 3.2, §0, §1, M1. All checks below were run against git objects. No summary written by the executing agent was taken on trust; its test report `reports/MAC_M1_TESTS_20261104.md` was re-derived independently (§B.2).

The integration is sound: every PLAN row and every STATUS line of all six sources is present, merges were per-file three-way, no Track S code was taken, the five held files are untouched and every pin hash recomputes. The findings concern the **decision packet** (two options and one draft row are not faithful to their sources), a PLAN contradiction that remains open until the author's ruling row is committed, and smaller gaps in the checker and the commit records.

---

## A. Findings

### MAJOR

**M-1. Packet (a) misstates the source review and the effect of the held changes.**
- The packet (lines 41, 45, 49) says the five held files "were reviewed with the branch (`reviews/C3_EVIDENCE_GUARDS_REVIEW_20261028.md`)". It also says they "only refuse inputs; they do not change any result on rows without EVIDENCE markers". The draft row says "as reviewed in …".
- Evidence on the review: all five files were changed by a single commit (`git log 30303d87..f98e315e -- r1/c3/env.py r1/c3/control.py r1/c3/prior_model.py r1/c3/train/run.py r1/c3/train/trainer.py` → `9bab3d6f` only). The review's line 3 reads "Code-Commit: `9bab3d6f…`. Verdict: **BLOCK / NOT ACCEPTED FOR B.2 LAUNCH**". Its line 13 reads "They must not be represented as a proof of global isolation or as acceptance of subsequent training."
- Evidence on the effect: `git diff 30303d87 f98e315e -- r1/c3/train/run.py` widens `EVAL_COLUMNS` to `delta_true|delta_audit_all|se_audit|candidate_metrics|incumbent_metrics`. `guard_rows` then refuses those keys for every purpose except `p4_final_eval`, **whether or not the row carries an EVIDENCE marker**. `_keys` now also walks lists. So the change can refuse Track P inputs that are not evidence rows. For example, `offline_eval.assemble` outputs carry `delta_true` (`r1/c3/offline_eval.py:280`).
- **Fix:** state the review verdict as it stands (BLOCK for B.2 launch; guards are not acceptance of training). Describe the `EVAL_COLUMNS` widening as a behaviour change for non-evidence rows. Drop "as reviewed" from the draft row, or replace it with "reviewed (verdict BLOCK for B.2; guards not accepted as an isolation proof)". Re-derive the recommendation from those facts.

**M-2. Packet (d), its draft row and §0's consequence turn the ruling's "B1 candidate set" into v2 eligibility. That drops conditions held by other rows.**
- The 15:44 ruling defines the **B1 candidate set** (`B1 候选集`): t7h8's 8 PASS + anchors + the `t7j10` passes after the operator's acceptance.
- Packet line 94 says that set "settles" v2 eligibility. The draft row R1-EXAM-RULE-X5V2 (line 98) says "eligibility = the 8 PASS of `t7h8` + anchors + the operator-accepted `t7j10` passes".
- R1-MAIN-PROPOSER (a) sets v2 eligibility as "Stage A pass, D28 pass, **and able to run with thinking off**". R1-EXAM-ALWAYS-ON-SKIP keeps always-thinking models out of B1. Read literally, the draft row would admit always-thinking Stage A passes and skip the D28 condition. It also lists anchors as "eligible", which no row says.
- This adds something beyond the ruling. The coordinator asked that the packet "adds nothing beyond them".
- **Fix:** have the (d) row say that the Stage A pass set used by v2 is t7h8's PASS ∪ the operator-accepted `t7j10` PASS (R1-TRACKX-HANDOVER-RULING), that anchors enter as anchors, and that the D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) and R1-EXAM-ALWAYS-ON-SKIP still apply. Apply the same wording to the RUNBOOK §5 cell (`docs/r1/RUNBOOK.md`, Track X B1/B2 row).

**M-3. PLAN on the branch is still self-contradictory, and the hand-off text does not gate on the ruling row.**
- R1-HANDOVER-04NOV (11:29; PLAN line 771) makes the operator "the only agent acting on the servers" and the Mac agent the single editor of `r1/exam/`.
- The coordinator rows that follow it are dated by commit 14:09–15:29 (`git log --format='%h %ci' 3a853917..10742f85`): R1-EXAM-STAGEA-COMPLETE … R1-EXAM-STOP9-JOURNAL (PLAN lines 713–718). They record the Track X agent editing `r1/exam/` and running on TASL-7.
- M1 step 2 says "If two rows contradict each other, STOP and ask". Flagging this in packet §0 and putting it to the author was the right action (adequate as a STOP).
- The author's ruling, however, exists only in the packet and a commit body. No PLAN row records it. A decision exists only as a dated PLAN §10 row (runbook preamble). The packet's operator message (line 169) would send the operator to read a PLAN that still contradicts itself.
- **Fix:** make step 6 conditional. The operator message is sent only after R1-TRACKX-HANDOVER-RULING (revised per M-2 and m-9) is committed to PLAN §10, by the author or on his chat instruction with his words quoted. Say so explicitly in the packet's hand-off section.

### MINOR

**m-1. `plan_row_check.py` does not check STATUS text outside `## `/`- ` entries.**
- `status_entries` starts entries only at `## ` or `- `, and drops lines that are neither (r1/scripts/plan_row_check.py:80–96).
- On `74fdebca`, 195 of 1,196 non-blank STATUS lines belong to no entry: the title, free paragraphs, and tables under `## ` headings (e.g. the Track S D6 identity table).
- Mutation test: 40 alterations of such lines → **40 undetected**. The PLAN side is robust: 375 single-line deletions and 375 single-line edits of §10 lines → 0 undetected.
- The result is nonetheless clean. My raw non-blank line-multiset check over PLAN.md and STATUS.md finds **0 lost STATUS lines** for all six sources. The only lost PLAN lines are the three intended re-edits: the Historical index note, plus "1. **LLM self-control.**" and "5. **Generalisation.**", which runbooks-04nov edited outside §10 and which were merged three-way.
- The EDITED-BY / SUPERSEDED-IN tags fire only for the Historical index line. Its versions are pure insertions coordinator ⊂ main-proposer ⊂ runbooks (difflib: insert-only). The tag cannot mask a deleted row unless another source holds a different line with the same key that the result keeps. The one theoretical hole is `key()` = first 60 characters for non-table lines; it is harmless here.
- **Fix:** treat every non-blank STATUS line not inside an entry as its own item (or add a whole-file line-multiset pass). Correct the claim in `d5d59a67` / the report ("every STATUS entry").

**m-2. Done-when "failure set equal apart from new tests" is not literally met.**
- My JUnit comparison (`coord.xml` 736 cases / 11 failures; `macint.xml` 837 / 28): all 11 coordinator failures recur, and 17 fail only on mac-int.
- Classified independently. I ran the four affected files on snapshots of `f98e315e` and `a43e1b47` with the same venv and harness: `f98e315e` gives 6 failed / 67 passed; mac-int gives 17 failed / 56 passed.
  - 11 failures are in `test_c3_evidence_other_boundaries.py` (new file). They pass on `f98e315e` and fail only because the five files were held. Expected.
  - 3 failures are in new files `test_c3_evidence_guards.py` (2) and `test_c3_evidence_seed_isolation.py` (1). They fail on `f98e315e` too.
  - 3 failures are in the **existing** `test_c3_launch_provenance.py` (unchanged since `ccb47128`; same blob on base, source and result). They fail because merged b2-repair code (`check_launch_manifest(..., engineering_liveness=)`, `SweepRunner.label`) is not matched by this test's `object.__new__` / lambda fixtures. They fail on `f98e315e` too.
- None of the 17 is caused by the integration. The executing agent's report `MAC_M1_TESTS_20261104.md` is accurate. Only `1b7e7cdc` was tested; `git diff --name-only 1b7e7cdc 74fdebca` touches docs only.
- **Fix:** the author should acknowledge the 3 inherited `test_c3_launch_provenance` failures as an exception to the Done-when, with the fixture fix assigned to M3. A note in STATUS suffices.

**m-3. One b2-repair file was not merged, contrary to the commit message.**
- `docs/r1/recovery/c3-fixtures-20261031/cache/fixture.log` exists on `f98e315e` and is absent on the result. It is gitignored by `*.log` (`.gitignore:3`).
- The branch README (merged) cites "Its retained `cache/fixture.log` records `1 passed in 15.68s`".
- Commit `02231384` says force-added files were taken "to stay faithful to the branch" and "New files added (32)". The source adds 35; the other 2 were already identical on base (`C3_SWEEP1_CLASSIFICATION_REVIEW_20261028.md`, `results/r1/evidence/C3_sweep_classification_20261028.json`).
- **Fix:** `git add -f` the log from `f98e315e`, or note its omission.

**m-4. Code beyond §1's description of b2-repair was merged without a mention.**
- §1 names `r1/c3/audit.py` and `r1/scripts/c3_label_sweep*` as b2-repair's code. `02231384` also merged `r1/c3/dataset.py`, `r1/c3/offline_eval.py`, the new `r1/c3/evidence_boundary.py` and `r1/scripts/c3_mount_inode_candidate.py`.
- None of these is on the shared list of §0 or on R1-HANDOVER-04NOV's list of out-of-scope files, so merging them is permitted. The commit message nonetheless labels `dataset.py` / `offline_eval.py` "in-scope" without saying on what basis.
- **Fix:** one line in the STATUS entry listing every code file taken from b2-repair and why each is in scope.

**m-5. A Track S change to the shared `prior_model.py` overlaps a held b2-repair change; the packet does not mention it.**
- `trackS-ops-20261030` changes `r1/c3/prior_model.py` (+26/−4, explicit `cache_prompt` for the A4 client; R1-CACHEPROMPT-FALSE). `codex/b2-repair-20261031` changes the same file (+3).
- Both are correctly not merged, and the file is unchanged against base. When packet (a) is acknowledged, the merge must be three-way, and the Track S change stays pinned rather than merged.
- **Fix:** note this in packet (a).

**m-6. The pin table cites a ruling that is not yet a PLAN row.**
- The RUNBOOK §5 Track X B1/B2 cell cites "author ruling 4 Nov 15:44, `proposals/AUTHOR_DECISIONS_20261104.md` §0". RUNBOOK ranks above the packet, and a proposal file is not a decision.
- **Fix:** cite R1-TRACKX-HANDOVER-RULING once committed. Until then, mark the cell "pending R1-TRACKX-HANDOVER-RULING".

**m-7. Packet §0 rewrote the option list "put to the author".**
- In `76625bb5` the options were: 1 (exception); 2 "`t7j10` continues under the operator, who takes over the guardian and lease"; 3 "pause `t7j10`".
- `a43e1b47` restates them as "1 … 2 The handover wins … 3 Something else", labelled as the options put in chat at ~15:30.
- The ruling ("选 2" while the Track X agent lets `t7j10` finish) is a hybrid of the original 1 and 2. A reader therefore needs the exact options the author chose from.
- **Fix:** keep the committed option text, or quote the chat options verbatim, and do not paraphrase.

**m-8. The two quotes of the 15:44 ruling differ.**
- The commit body has "选 2，交接行优先…`t7j10`…". The packet line 22 has "选 2，交接行优先（作者 15:33 "按原定计划走"）。`t7j10`…".
- A parenthetical "(作者 15:33 …)" inside the author's own message is unusual. It may be a relayed paraphrase.
- **Fix:** confirm the exact text with the author and make both quotes identical. If the 15:44 text was composed by the chat session and approved by the author, say so.

**m-9. The draft row R1-TRACKX-HANDOVER-RULING adds two small things beyond the ruling's words.**
- (i) "`r1/exam/` **and `r1/scripts/exam_*`**". The ruling names only `r1/exam/`. The addition is consistent with R1-HANDOVER-04NOV, but it should cite that row rather than read as the ruling.
- (ii) "then stops **and makes no further change**". The ruling says only "随后停止".
- **Fix:** keep the ruling's scope and attribute the rest to R1-HANDOVER-04NOV.

**m-10. Packet (j) puts numbers in recommendations without a source and without the estimate label.**
- Item 3 (20 % per node) and item 6 (excess kurtosis > 3 on ≥ 2 edits, ν = 5) are unsourced.
- Items 2–15 also lack the paste-ready confirmation line that M1 step 5 (j) asks for, "one per item".
- **Fix:** mark these numbers as the agent's proposal with no source basis, or offer options. Add a one-line paste-ready row per item, or state that none is needed (items 7, 8, 13, 15).

**m-11. Records and procedure.**
- No STATUS entry for M1 exists yet (STATUS result-only lines = 0), and the runbook requires one at the STOP.
- The tests ran in the cloud workspace, not on the Mac. This is disclosed in the report and needs the author's acknowledgement under R1-LOCAL-TEST-SCOPE.
- **Fix:** add the STATUS entry with the handoff hash once accepted.

---

## B. Verification record

### B.1 `plan_row_check.py` and PLAN/STATUS (Done-when 1)

- Re-run: `python3 r1/scripts/plan_row_check.py --result mac-int-20261104 --source origin/codex/coordinator-20261031 --source origin/docs/main-proposer-03nov --source origin/docs/runbooks-04nov --source origin/codex/b2-repair-20261031 --source 13badb0 --source origin/trackS-ops-20261030` → exit 0, MISSING 0, RESULT-ONLY 0. The counts are identical to `reports/MAC_PLAN_ROW_CHECK_20261104.md`.
- The PLAN extraction is sound under mutation (see m-1). STATUS has the gap described in m-1, with the result independently clean.
- **The two named rows are present.** R1-HANDOVER-04NOV is at PLAN line 771. R1-SERVER-AGENTS-TWO is at 835, under `### 4 November 2026 (14:58)` at 829. Both are byte-identical to `c15b1102`.
- **R1-CACHEPROMPT-FALSE** sits inside §10 (§10 = lines 325–846). It has its own heading `### R1-CACHEPROMPT-FALSE (31 Oct 2026, author) — accepted` (line 720) and is byte-identical to `f5d5c6b0`. It is placed after the 31 Oct coordinator block and before the 3 Nov block, so it is in date order.
- **Block placement.** The 28 Oct clarification (b2-repair) follows R1-SWEEP1-CLASSIFY. The 29 Oct and 30 Oct Track S blocks follow, then the D1–D23 topic table, as in `13badb0`'s own order. Then come 31 Oct coordinator, R1-CACHEPROMPT-FALSE, 3 Nov, and 4 Nov (unlabelled, 11:29, 11:55/12:45, 13:45, 14:58). Dates are in order.
- **STATUS** is newest-first. The 4 Nov bullets are ordered by stated or commit time. The Track S `## 31 October` / `## 30 October` / `## 29 October` sections sit after the coordinator's 31 Oct section and before 28 Oct.

### B.2 Merges

- Each modified file was re-merged with `git merge-file -p <parent> <merge-base> <source>` and compared with the commit:
  - `7da89e8c`: README, C3_DESIGN, PLAN, RUNBOOK, TECH_ROUTE, TRACK_P_POST_TRAINING and TRACK_G_RUNBOOK are byte-identical to merge-file (rc 0). STATUS (rc 1) differs only by hand-ordered insertion of source bullets.
  - `02231384`: audit.py, dataset.py, offline_eval.py, c3_label_sweep.py and c3_label_sweep_launch.sh are identical (rc 0). PLAN (rc 2) differs only by the position of the clarification paragraph.
  - `5e96fa56`: C3_DESIGN is identical to the `13badb0` merge. TRACK_P §6.5 step 4 combines the R1-BX-D11 clause and the R1-WORDING-30OCT clause in one line, which is a consistency edit.
- New files are blob-identical to their sources.
- No checkout-overwrite was found. Main-proposer's deletions of the two STOP 8 files are superseded correctly: both files exist on the coordinator and are kept.
- **Track S code not taken.** `r1/tracks/**`, `r1/tests/test_tracks_*`, `test_cache_prompt.py` and `results/r1/tracks/**` are absent. `r1/c3/prior_model.py` and `r1/exam/observer.py` are unchanged against base.
- **The five held files** (env.py, control.py, prior_model.py, train/run.py, train/trainer.py) have the same blobs as `10742f85`.
- **Pushes:** `git branch -r --contains a43e1b47` is empty, so nothing is pushed. `main` / `r1` are untouched.
- **Commits:** author `Dowling Wong <wangdowling@gmail.com>`; "AI-assisted" and the attribution lines are present in all 8. Inaccuracies are listed in m-1, m-3 and m-4.

### B.3 Pin table (Done-when 3)

SHA-256 recomputed from blobs, all matching:
- Track S operator runbook @`13badb0` `a93fb84bd04f650d`; design @`13badb0` `4e863cc059f779a2`;
- `c3_sweep1_20261027.md` @`55ab283c` `563374f6b0a8369c`; DEEPTHOUGHT_SWEEP1_RUNBOOK @`c5ea0374` `525191093126be55`; `c3_sweep_deepthought.json` @`ccb47128` `2fa891f43bf26e6e`;
- PORTAL_EXAM_RUNBOOK @`c5ea0374` `93513cf772b378ba`; registry @`19b8f33f` `068fcae40b70cecd`; @`74a07907` = @`96f11463` `2c6ef6b329694536`; `x5_rule_v1` `0665903b276f34ec`;
- Track P registry @`b9ad6f8f` `e60cdb28580785ab`; `p3_rule_v2` `8c0ef9089589eafc`; `e0_v1.jsonl.gz` `4f4db29b6a4c0ca0`; PORTAL_TRACK_P_RUNBOOK @`46af4b9e` `49dcef690556a9ed`; P.3a authorization @`607e85ea` `414e7144e265b0a5`.

Commit values traced to their cited sources:
- Sweep-1 manifest harness `6adf3859de66…` and paper `ccb47128aad8…`;
- `exam_portal.json` @`19b8f33f` `harness_commit 897d83c8…`;
- HOST_FACTS `v0.7.0 = 620d2225…` and `13fb94bf`;
- `d10b05b7` is an ancestor of `f5d5c6b0`.
- Harness ancestry `6adf385 ⊂ 115df37 ⊂ a3fedbb` was verified in the local harness clone.

The two *TODO_VERIFY* cells are justified: no committed file records Track P's launch commit or B1's paper commit. The remaining issue is m-6.

### B.4 Packet (Done-when 4)

- The packet exists and states it decides nothing.
- Already-ruled items are not reopened: (d′), (e), (f), the bulk of (g), and the D3/D4/D6-class/D7/D8/D13/E5/E1-E2/E4 confirmations.
- Every bullet of the 11:29 "Still open" list is covered: (a), (b), (c), (h), (j)2–10.
- All seven fenced draft rows have three pipes (two cells), so they are well-formed. The inline D8-CONFIRM draft is also well-formed.
- (g) claims the ruling file `docs/prompts/TRACKS_CACHEPROMPT_FIX_PROMPT_20261031.md` is on no branch. I checked every local and remote ref and found it on none.
- Faithfulness problems: M-1, M-2, m-7 to m-10.

### B.5 Commit `a43e1b47` (the coordinator's added scope)

- It records the ruling quoted and translated. The translation is accurate.
- It goes beyond the ruling in M-2 (eligibility) and m-9 (scope, "no further change").
- Its quote and option record are discussed in m-7 and m-8.
- Packet (b) follows the ruling and remains a proposal for an open item, which is acceptable.

---

## C. To reach "accepted"

Fix M-1, M-2 and M-3 (packet text and hand-off gate). Fix or answer m-1 to m-11. The same reviewer then re-checks.

---

## Re-check — `a9eb5952` (fixes `177047fa`, `2cc32728`, `a9eb5952`)

**Verdict: accepted.**

Same reviewer. Every claim below was checked against git objects at `a9eb5952`. `git diff --stat 74fdebca a9eb5952` touches 7 files: the packet, the RUNBOOK pin cell, one STATUS line, `fixture.log`, the checker, its tests and the regenerated report. No other code changed. Nothing is pushed (`git branch -r --contains a9eb5952` is empty).

| Finding | State | Evidence |
|---|---|---|
| M-1 packet (a) | **FIXED** | Packet lines 37–65 name commit `9bab3d6f`, quote its review's "BLOCK / NOT ACCEPTED FOR B.2 LAUNCH" and the "NOT CHECKABLE" isolation caveat, and say that no later review covers the five files. "Effect" describes `EVAL_COLUMNS` and `_keys` as refusing unmarked rows. The Track S overlap in `prior_model.py` is noted. The recommendation is re-derived (option 3, defer to M3's review). The draft row no longer says "as reviewed" and states that the earlier review "is not an acceptance". |
| M-2 packet (d) / pin cell | **FIXED** | Packet line 110 and the draft row at line 114: the ruling's set is the Stage A pass set v2 reads (t7h8 PASS ∪ operator-accepted t7j10 PASS); anchors run as anchors; the D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) and R1-EXAM-ALWAYS-ON-SKIP apply unchanged. The RUNBOOK §5 Track X B1/B2 cell is reworded the same way and also cites R1-MAIN-PROPOSER (a). |
| M-3 contradiction / hand-off | **ANSWERED** | Packet "Hand-off to the operator — gated" (lines 203–209): the operator message is sent only after R1-TRACKX-HANDOVER-RULING is in PLAN §10. The STATUS M1 entry says the same. The contradiction stays in PLAN until the author acts. Putting it to the author and gating the hand-off is the STOP that M1 requires, and the agent does not commit the row without his instruction. |
| m-1 checker | **FIXED** | `status_entries` now emits every non-blank line outside an entry. 5/5 parser tests pass. Re-run with all six refs: exit 0, MISSING 0, STATUS RESULT-ONLY 1 (the new M1 entry, expected). The output matches `reports/MAC_PLAN_ROW_CHECK_20261104.md` line for line. Mutation test with the `a9eb5952` script: 120 sampled source STATUS lines, each deleted and each edited → 0 undetected (previously 40/40 undetected for lines outside entries). |
| m-2 test exceptions | **ANSWERED** | Packet (k) item 2 and the paste-ready row R1-M1-TEST-EXCEPTIONS. Correct reading: the 3 failures are inherited from `f98e315e`. The author must commit the row (or rule otherwise). |
| m-3 `fixture.log` | **FIXED** | It is added on the branch with blob `a45a4aa0…`, identical to `f98e315e`. |
| m-4 code files in scope | **FIXED** | The STATUS M1 entry lists all seven code files taken from b2-repair with the reason for each, plus the held five. |
| m-5 `prior_model.py` overlap | **FIXED** | Packet (a) "Overlap" paragraph. |
| m-6 pin cell citing the packet | **FIXED** | The cell now reads "*pending R1-TRACKX-HANDOVER-RULING*". |
| m-7 option list | **FIXED** | §0 now quotes the chat options verbatim with a gloss, and says how the ruling departs from option 2 (`t7j10` allowed to finish; hand-over point `74a0790`/`ab74203` rather than `96f1146`). |
| m-8 ruling quote | **ANSWERED** | §0 states that the quote is the 15:44 message as received, parenthetical included, and that the `a43e1b47` body is the same message with marked elisions. Nothing more can be verified from git. |
| m-9 draft ruling row | **FIXED** | It no longer has "makes no further change". `r1/scripts/exam_*` is attributed to R1-HANDOVER-04NOV. The rest keeps the ruling's scope. |
| m-10 packet (j) | **FIXED** | "†" marks the unsourced numbers (20 %, kurtosis > 3, ν = 5). Every item has a paste-ready line or "No row now". Item 6 now recommends a per-node author call. |
| m-11 STATUS / cloud tests | **FIXED / ANSWERED** | A STATUS M1 entry is added. Cloud-workspace testing is put to the author in (k) item 1 under R1-M1-TEST-EXCEPTIONS. |

All 9 fenced draft rows and the 8 inline paste-ready rows have two cells (three pipes), so they are well-formed. No draft row is committed to PLAN. The packet still takes no decision.

**Residual notes (not findings).**
- Packet (a)'s "Effect" paragraph names `run.py` as the change that affects unmarked rows. `control.py` also widens the refused `value_key` set for `fit_awr_direct` to `delta_audit_all`, `se_audit`, `candidate_metrics` and `incumbent_metrics`. The table row ("refuses … the evaluation-side value keys") covers it, and M3's review will see it.
- The STATUS entry's phrase "Code taken only from b2-repair" means *merged* code. M1's own new `plan_row_check.py` is separate and listed in its own commit.

**On the hand-off order.** I have no objection to one follow-up commit that writes the accepted commit's hash (`a9eb5952`) into the M1 STATUS entry and adds this review file, then a push, provided that commit touches only `docs/r1/STATUS.md` and this file. The operator message stays gated as the packet says. The commit it names will be a later one carrying R1-TRACKX-HANDOVER-RULING. That commit should change only PLAN §10, adding that row (and any other rows the author commits), with the author's words quoted. Anything beyond that needs a fresh check.
