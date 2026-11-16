# Review: ops-20261104 integration and R1-EXAM-STAGEA-ACCEPT (`cabbe400..74c5da10`)

## Author-value wording re-check — 4 November 2026: accepted for draft scope

The same Codex reviewer re-checked the revised working-tree draft at `/private/tmp/paper-b-mac-20261104/docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261104.md`, SHA256 `c3db0396dc8f9b9161986584852c02267aff07f2b4f841af1e50a119279847c3`. MINOR 2 is resolved: the selected node, cap, and worker values are distinguished from the historical options, and the Stage A review status is updated with the limitation on historical measurement revalidation. `approved` remains false, the acceptance SHA remains TODO, and the hard STOPs and separate review/authorization requirements remain. **Accepted for the draft wording and value update only**; no code is accepted, no STOP is cleared, and B1 is not launch-ready.

---

## Author-value update re-check — 4 November 2026: not accepted pending wording fix

The same Codex reviewer checked the uncommitted B1 draft at `/private/tmp/paper-b-mac-20261104/docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261104.md`, SHA256 `48bb9629b604261467c256e5ac3b92220cbcd2539444d3fb4101712af32eee1a`, against the relayed 19:03 author decision and the previous review. The block has the selected `digits_mlp` variant, integer call cap 80 and workers 20, but keeps `approved: false` and `stage_a_amendment_acceptance_sha256` as a TODO. Precondition 5 retains the hard STOPs and independent review; no launch is authorized. The CPU headroom remains unmeasured.

**MINOR 2 — stale wording contradicts the recorded selections:** the heading `llm_call_cap — options (none is a decision)` now contradicts the selected value 80; the worker heading still calls the section a proposal; and the nodes row labels the selected variant *(proposed)*. The Stage A precondition says the row is under review at drafting time; update its status only if the reviewed record has in fact been integrated. Present the choices as a historical rationale and clearly distinguish selected values from the still-unapproved final authorization. Re-check after edits; this review does not accept any code or establish launch readiness.

---

## Round 2 re-check — 4 November 2026: accepted for draft scope

The same Codex reviewer re-checked the revised draft at `/private/tmp/paper-b-b1-draft-20261104/docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261104.md`, SHA256 `5b29910f08f476a9a1b82e2030b4e221485bdee72f4f12ea56ce9dde2befa268` (working-tree bytes, not a commit). **MAJOR 1 resolved for the draft:** precondition 5 explicitly records the existing hard STOPs, the need for implementation and independent review, and prohibits removing the guards without satisfying their conditions. **MINOR 1 resolved:** `workers` is described as the post-collection audit process pool, with resource headroom unmeasured and the author's choice open. `75134796:r1/exam/runtime.py` supplies the three BLAS/OpenMP environment limits to the worker job; actual performance is not established here.

**Accepted for the Stage A row correction, host row and draft review only.** This does not accept M2 or any B1 code, clear any hard STOP, approve the draft, fix the remaining author choices, or establish launch readiness. The final note and code pin still require re-check after the STOP is resolved. The original round-1 Claude reviewer was unavailable; the present independent reviewer handled this round and its re-check.

---

## Round 2 — 4 November 2026: not accepted

Independent re-review by Codex (AI-assisted; a fresh reviewer, not the author of the changes). The prior Claude reviewer was stopped at handover and is not available in this session; this is a new independent reviewer, not a claim that the same reviewer re-checked. Reviewed `f5f29801`, `5c1d3f80`, `a52aa7b1`, and `c87a277a` at `8bbdafd4`; cross-checked the unfinished M2 code at `751347969d1a0de0239c6beedbc8136541685f2f`. No server, model or GPU was used. Verdict concerns the draft and handoff readiness; it does not reopen the author's Stage A decision or authorize B1.

**MAJOR 1 — B1 remains blocked in code, but the authorization draft does not state the prerequisite.** At M2 `75134796`, `r1/scripts/exam_runner.py` refuses B1/B2 in both `main` and `evidence`; `r1/exam/runtime.py` refuses them in `ExamRunner.start`; and `r1/exam/campaign.py` refuses `collect` with `STOP: B1/B2 reviewed harness pin and observer cache evidence not implemented`. The preserved evidence body is explicitly unreviewed and unreachable. Draft precondition 1 requires M2 acceptance but does not identify this separate, existing hard STOP or the work and independent review needed before a B1 launch. The prior A1 requirements review also identified the unreachable path. Add the prerequisite to the draft and handoff, and route the underlying STOP to the owning task for diagnosis, implementation and independent review under the existing authorization and STOP rules. Do not simply remove the fail-closed checks. Re-check the final code pin and authorization draft before presenting a launch-ready note.

**MINOR 1 — The proposed worker rationale describes the wrong phase.** At `75134796`, `campaign.py` uses `workers` as the `ProcessPoolExecutor` size for audit configurations after the sequential campaign collection, not as the number of simultaneous campaign execution workers. The proposal's CPU reservation and thread-limit language is hypothetical; it must describe audit processes and retain the author's choice as open, pending M2's concrete report and verified thread controls. This does not change the recorded host decision.

**Checks passed.** `f5f29801` replaces the original review's MINOR 1 with its suggested finalist-eligibility wording, without changing the author decision cell; the B1 draft uses the same distinction. The host row's decision cell is an exact substring of the author quotation above it, and its consequences preserve the TASL-7 and P.3a conditions. Both table digests agree with the accepted Stage A recorder's note; the proposed acceptance-record SHA256 equals the merged O1 report bytes, and `75134796`'s draft config uses that same report. The rule file at `75134796` hashes to `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`. The JSON block remains `approved: false`, with unresolved author choices; `author_gate` at `75134796` binds author, phase, rule, nodes, tables, acceptance record and call cap, but does not bind `host` or `workers`, as the draft states. Node, cap and worker selections remain proposals, not decisions. These checks do not establish production readiness.

---

Independent reviewer (AI agent, Claude; fresh context, did not write the work). Verified from git objects only on branch `mac-int-20261104`; no server, LLM or GPU used; nothing staged, committed or pushed. Range reviewed: `96bca12b` (integrate `ops-20261104` @ `f52db28e`) and `74c5da10` (PLAN §10 R1-EXAM-STAGEA-ACCEPT). The branch tip has since moved on (`33988105`, HoreKa rows); commits after `74c5da10` are outside this review.

## Verdict: **accepted**

0 BLOCKING, 0 MAJOR, 2 MINOR. Neither minor affects the decision cell, the merge content or the 7-PASS count. One is a wording fix in the labelled recorder's note; the other is cosmetic and needs no action.

## Check 1: `96bca12b` (integration of `ops-20261104` @ `f52db28e`)

- **Source range.** `009d859a..f52db28e` is linear, with four commits: `2e49bd22` (16:44:55, O0 census), `51a9bc52` (16:54:06, STOP 0 reply), `ca068fca` (17:40:30, O1 audit + STOP) and `f52db28e` (17:45:55, author ruling + accepted re-check). `009d859a` is an ancestor of `cabbe400`. `origin/ops-20261104` = `f52db28e`.
- **Paths.** `git diff --name-status 009d859a f52db28e` lists 11 added files under `docs/r1/reports/` and `docs/r1/reviews/` plus `M docs/r1/STATUS.md`. `git diff --stat cabbe400 96bca12b` touches exactly the same 12 paths and nothing else.
- **Byte-identity.** For each of the 11 added files, the blob at `96bca12b` equals the blob at `f52db28e`. Examples: `OPS_O1_20261104.md` `4695c372…`, `OPS_O1_REVIEW_20261104.md` `212714cb…`, `OPS_O1_AUDIT_20261104.txt` `645c1c1c…`, `OPS_O1_TEMPLATE_AUDIT_20261104.{py,txt}` `480d1ef2…`/`6c3da25f…`. Nothing from the operator branch is omitted.
- **STATUS.md.**
  - A three-way `git merge-file` (mac `cabbe400`, base `009d859a`, ops `f52db28e`) conflicts only at the top insertion point.
  - The merged file's line multiset equals mac + ops − base.
  - Base, mac and ops line orders are each preserved as subsequences.
  - `git diff cabbe400 96bca12b -- docs/r1/STATUS.md` has only `+` lines, so no existing STATUS line is altered.
  - The three ops entries (O1, STOP 0, O0) are byte-identical to `f52db28e`. O1 is in its post-`f52db28e` form ("ACCEPTED the `t7j10` receiving review").
- **Placement (newest first, by commit time):**

  | Entry | Commit time |
  |---|---|
  | O1 (ops) | 17:40, amended 17:45 |
  | "Author rulings 17:30" (mac) | `00f10282` 17:31, edited `899edbb7` 17:37 |
  | "Reviews and merges" (mac) | `cfa74cd4` 17:05 |
  | STOP 0 (ops) | 16:54 |
  | O0 (ops) | 16:44 |
  | "A1/`t7j10` requirements" (mac) | `fe193b3b` 16:40 |

  The order is consistent and matches the commit message's description.
- **Form.** `96bca12b` is a single-parent integration commit (not a git merge), as were the earlier `210aa99e` and `316ba2a5`. `f52db28e` is therefore not an ancestor of `74c5da10`, but it stays reachable as `origin/ops-20261104`, and the PLAN row cites it by SHA. This is an observation, not a finding.

## Check 2: `74c5da10` (PLAN §10 R1-EXAM-STAGEA-ACCEPT)

- **Scope.**
  - `git diff --stat 96bca12b 74c5da10` touches only `docs/r1/PLAN.md` (+19 lines). It is one hunk, `@@ -899,0 +900,19 @@`: a new `### 4 November 2026 (17:54) — Stage A accepted …` subsection placed after the 17:30 subsection and immediately before `## 11. Relation to Paper A`.
  - `96bca12b:docs/r1/PLAN.md` equals `cabbe400:docs/r1/PLAN.md` (`b7ce2c5b…`), so the integration commit did not touch PLAN.
- **Intro.** It quotes item 9 in full and verbatim, from "Stage A 验收：" through "…转发 operator。" (checked by exact substring match).
- **Decision cell.** The cell is exactly `"我接受 Stage A：…B1 候选 = t7h8 的 8 个 PASS + t7j10 的 7 个 PASS + 3 个对照。"`, a byte-exact substring of item 9 (offset 11).
  - Reading "这段话" this way is correct. "Stage A 验收：" is the item's topic label, which the row id already carries. "请写成 PLAN 行…转发 operator。" is a process instruction to the recorder, not part of the decision.
  - This matches his standing practice: the cell holds the decision paragraph, and the full text is preserved in the intro.
- **Consequences** (not part of the cell):
  1. "accepted on the two attempts named: `t7h8` and the A1 amendment measurement `t7j10`". This restates the decision. "A1 amendment measurement" = M1, per R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED.
  2. "B1 candidate set is the 8 PASS of `t7h8`, the 7 PASS of `t7j10` and the 3 anchors". This restates the decision. The 3 anchors are R1-EXAM-A1-M1-REQUIREMENTS (2)'s "三个对照基准". The bullet's quotation of R1-TRACKX-HANDOVER-RULING's consequence ("the `t7j10` passes … after the operator's acceptance") is a fair elision of "the `t7j10` passes, the latter counting only after the operator's acceptance".
  3. "B1 starts only under its own authorization note and R1-EXAM-RULE-X5V2". This follows directly from R1-MAIN-PROPOSER (a) (v2 committed in R1-EXAM-RULE-X5V2 before the B1 authorization) and (g) step 1.
- **Recorder's note.** It is labelled ("not the author's words; from the merged O1 report and earlier rows"). Fact by fact:
  - **Table shas.** `t7h8` `00ab143d…975c` matches O1 §"Author's anchor comparison" and `reviews/TRACKX_STAGEA_RECEIVING_T7H8_20261104.md`. `t7j10` `71525124…2103` matches O1 §"Identity and custody". Code `ab74203` and manifest `64a2712c…` match O1 ("`code_commit=ab74203e…`, manifest `64a2712c16…`").
  - **`t7h8` 8 PASS list.** It is identical, in the same order, to R1-EXAM-STAGEA-COMPLETE ("8 candidates PASS (`glm47_flash`, … `qwen3_coder_30b_a3b`)").
  - **The seven `t7j10` amendment candidates**: `gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`, `laguna_xs21`, `olmo31_32b`, `devstral_small2_24b`, `ministral3_14b`.
    - All seven appear in O1's row-by-row table, alongside `qwen25_coder_7b`. Every one has 50/50 parse and active key, 100/100 repeats, 5 + 50 A1 checks, and min free VRAM ≥ 1,024 MiB (≥ 2,257 MiB). Each switchable model also has its grammar probe.
    - The BOS-artifact / repaired split matches R1-EXAM-TEMPLATE-FAILURE-MAP and R1-EXAM-TEMPLATE-AMENDMENT-PROPOSAL.
    - The three repair-template shas match O1.
    - "SHA-pinned templates carry into B1, B2 and later sweeps" is R1-EXAM-A1-M1-REQUIREMENTS (1).
  - **Anchors.** `random_valid`, `scripted` and `qwen25_coder_7b` are correct.
  - **Anchor comparison.** The note's summary ("N/A applicability and PASS identical for the two software anchors; numerical equality only for `qwen25_coder_7b`") faithfully paraphrases the verbatim ruling quoted in O1 §"Author ruling on software-anchor applicability" ("每项指标的适用状态（N/A）相同，且 Stage A 结果（PASS）相同 … 数值一致的要求只适用于模型对照 `qwen25_coder_7b`"). It is also consistent with R1-EXAM-A1-ANCHOR-CRITERION. The note correctly says this ruling is quoted in the O1 report; the ruling has no PLAN row of its own.
  - **Last bullet (B1 eligibility).** See MINOR 1.
- **"7 个 PASS" against the evidence.** There is no mismatch. The O1 report supports all seven amendment candidates as PASS:
  - It states "batch status is COMPLETE with ten completed entries, zero interruptions, and no failure classes in the table".
  - Its row-by-row section checks all seven by name.
  - `OPS_O1_AUDIT_20261104.py` asserts `r['passed'] and not r['failure_classes']` for every one of the ten `t7j10` rows, and `OPS_O1_AUDIT_20261104.txt` ends `RESULT 0 issues`, with `issues []` on each of the eight model rows.
  - The independent review re-check is **ACCEPTED**.

  `t7j10` has 10 PASS rows in total. The author's "7" counts the seven amendment candidates, and the three anchors (which PASS in both tables) are counted once as "3 个对照". The 8 `t7h8` and 7 `t7j10` names are disjoint, so the set has 8 + 7 + 3 = 18 distinct entries. The recorder's note removes any ambiguity by naming the seven. None of the 18 has `thinking_policy.mode: always_on` in `74c5da10:r1/exam/registry.yaml`; the always-on models are `muse_glimmer_30b`, `lfm25_24b_a2b` and `gpt_oss_20b`, none of which passed.

## Check 3: row check

`python3 r1/scripts/plan_row_check.py --result 74c5da10 --source origin/codex/coordinator-20261031 --source origin/docs/main-proposer-03nov --source origin/docs/runbooks-04nov --source origin/codex/b2-repair-20261031 --source 13badb0 --source origin/trackS-ops-20261030 --source f52db28e` (script unchanged from `74c5da10`) gives **exit 0, `MISSING total: 0`**.

- `f52db28e`: §10 rows 283/283, other §10 lines 104/104 and STATUS 946/946, all present byte-identical.
- RESULT-ONLY items are only mac-int's own 16:39, 17:30 and 17:54 subsections and its three STATUS entries since `009d859a`.
- The only EDITED-BY / SUPERSEDED-IN entries are the known "Historical index" line, which is kept from `docs/runbooks-04nov`.

## Findings

**MINOR 1: The recorder's note's last bullet mislabels finalist eligibility as "B1 eligibility".** The bullet reads: "B1 eligibility under `x5_rule_v2` still applies its other conditions (D28 pass, able to run thinking-off; always-thinking models skip B1)."

- Under R1-MAIN-PROPOSER (a), v2's "eligibility" (Stage A pass, D28 pass, able to run thinking off) is the pool from which **finalists** are ranked. It is not a precondition for entering B1. X.5 in RUNBOOK agrees: "Eligibility = Stage A pass + D28 criteria. **Finalists:** …".
- In code, D28 for exam models is computed from the B1 runs themselves (`74c5da10:r1/scripts/exam_runner.py:133`, `d28=all(...root_results...)`) and applied at finalist selection (`r1/exam/analyze.py:29`, `choose_finalists`).
- `x5_rule_v2` is still a draft (`proposals/X5_RULE_V2_DRAFT_20261104.md`; R1-EXAM-RULE-X5V2 not yet committed).
- Only the skip clause concerns B1 entry, and it rests on R1-EXAM-ALWAYS-ON-SKIP. It is moot for these 18, since none is always-on.

Because this row goes to the operator, the wording could be read as gating B1 runs on a prior D28 pass. Suggested rewording: "Finalist eligibility under `x5_rule_v2` (draft; R1-EXAM-RULE-X5V2 not yet committed) adds D28 pass, measured in B1, and the ability to run thinking off. Always-thinking models skip B1 (R1-EXAM-ALWAYS-ON-SKIP); none of these 18 is always-on." The bullet is labelled as the recorder's and does not touch the decision cell, so this is not blocking.

**MINOR 2 (cosmetic; no action needed): blank-line style in STATUS.md.** The three ops entries carry a trailing blank line, while mac-int's entries are contiguous. The merged STATUS therefore mixes the two styles in its top six entries. Changing it would alter the operator branch's lines, so keeping them byte-identical is the right call. This is recorded only for awareness.

## Observations (not findings)

- The O1 entry in STATUS ("O1's separate author acceptance row remains to be committed") becomes stale once this row lands. Following the practice of earlier rows, a separate "Records following R1-EXAM-STAGEA-ACCEPT" STATUS entry is expected after `74c5da10`. It is outside this range, and its absence here is correct ("Only PLAN §10 changes").
- The intro sentence "The operator's O1 receiving audit and its independent review … are merged into `mac-int-20261104`" is the recorder's framing. It is accurate (`96bca12b`) and follows the convention of earlier subsections, whose intro context is also unlabelled.
