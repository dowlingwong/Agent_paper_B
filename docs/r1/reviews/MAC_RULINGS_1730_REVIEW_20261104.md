# Independent review: the author's 17:30 rulings and their records (4 Nov 2026)

**Reviewer:** a fresh independent reviewer (AI agent, Claude). I did not write the reviewed commits. I worked read-only except for this file, and I staged, committed and pushed nothing. I used no servers, LLMs or GPUs.

**Scope:** `cfa74cd4..00f10282` on `mac-int-20261104`:
- `fed20ea2`: the PLAN §10 subsection "4 November 2026 (17:30) — anchor criterion for `t7j10` and the M5 review of `ab74203`", with rows R1-EXAM-A1-ANCHOR-CRITERION and R1-EXAM-AB74203-M5-REVIEW;
- `00f10282`: the operator message and gate paragraph in `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` ("Hand-off to the operator — gated"), and a new STATUS entry.

I checked everything against git objects (`git show`, `git diff` and `git grep` at named commits). Local `mac-int-20261104` is at `00f10282`, two commits ahead of `origin/mac-int-20261104` (`cfa74cd4`), so neither reviewed commit has been pushed.

The author's reply, as given to me (17:30): "1. `qwen25_coder_7b` 的三项完全相等，软件锚点只比结果状态 / 2. 按 M5 流程另开新 reviewer 重新审。" The message that prompted it (17:26) was "啥进展了".

## Verdict

**accepted**: 0 BLOCKING, 0 MAJOR, 4 MINOR. No MINOR finding changes what the author decided. Finding 1 should be fixed before the push, while the PLAN lines are still result-only and unpushed. Finding 3 should be fixed before the operator message is sent.

## 1. `fed20ea2`: PLAN §10

**Scope of change.** `git show --stat fed20ea2` gives `docs/r1/PLAN.md | 13 +++++++++++++`, with insertions only. The hunk is `@@ -884,0 +885,13 @@`. It sits after the last recorder's note of the 16:39 subsection and immediately before `## 11. Relation to Paper A`, so it is inside §10. No existing line changed. **OK.**

**Decision cells are verbatim.** At `00f10282:docs/r1/PLAN.md`:
- `"`qwen25_coder_7b` 的三项完全相等，软件锚点只比结果状态" |` occurs exactly once (line 891). It is item 1 of the reply, byte for byte, without the list marker "1. ".
- `"按 M5 流程另开新 reviewer 重新审。" |` occurs exactly once (line 892). It is item 2 of the reply, byte for byte, including the full stop, without "2. ".

Each string occurs once more, inside the full quotation in the lead paragraph (line 887). That quotation joins the two items with a space where the original had a line break. Markdown renders a paragraph-internal line break as a space anyway, so this is not a finding.

**Options match the ones offered.** The lead paragraph records the first question's options as A ("`qwen25_coder_7b`'s three numbers exactly equal, software anchors compared on result status only"), B (a tolerance) and C (other). It records the second question's options as A (treat as reviewed) and B (a fresh review by the M5 procedure). This matches the options as given to me. The author's answers match A for question 1 and B for question 2. The paragraph also attributes the questions correctly: the agent's reply to the 17:26 message "啥进展了". **OK.**

**The lead paragraph's claim about the anchors is accurate.** At `3b3283f:r1/scripts/exam_runner.py:114–116` (the code `t7h8` ran), the `random_valid`/`scripted` Stage A row is `{'passed':True,'software_anchor':True,'prompts':0,'failure_classes':[],'mechanical_model_checks':'not_applicable'}`. It holds no parse-rate, reproducibility or template value. **OK.**

**Consequences, bullet 1 (anchor criterion).** I checked each element:
- "`qwen25_coder_7b`'s parse rate, reproducibility and template result … must be exactly equal to `t7h8`'s" comes from "三项完全相等". The three items come from R1-EXAM-A1-M1-REQUIREMENTS (2) ("解析率、可复现性、模板结果"). **Grounded.**
- "`random_valid` and `scripted` are compared on their result status only" comes from "软件锚点只比结果状态". **Grounded.** The term "result status" is not defined further. That is correct, because a definition would be an addition. See finding 4.
- "Otherwise `t7j10` is not accepted and the operator reports to the author first" comes from R1-EXAM-A1-M1-REQUIREMENTS (2) ("不一致就不算验收通过，先报告我"). **Grounded.** The phrase "reports to the author first" is the same rendering the 16:39 consequences use.

**Consequences, bullet 2 (M5 review).**
- "The cited but uncommitted reviews … are not relied on" and "A fresh independent reviewer reviews … by the M5 procedure" come from "按 M5 流程另开新 reviewer 重新审". The word "independent" comes from R1-TRACKX-HANDOVER-RULING (15:44: "如果 `ab74203` 还缺独立 review，就按 M5 流程补") and from the M5 procedure's step 3 (`MAC_LOCAL_RUNBOOK_20261104.md` §M5: "an independent review"). **Grounded.**
- The premise "uncommitted" is accurate. The review document for `ab74203` cited in `reports/EXAM_TRACKX_STAGEA_STOP9_20261104.md:31`, `reviews/TRACKX_STAGEA_STOP9_NONGEN_REVIEW_20261104.md`, is not in `00f10282`, not in `origin/codex/coordinator-20261031` and not in `74a07907`. `git log --all -- '*STOP9_NONGEN_REVIEW*'` returns nothing. The A1 reviews cited only by hash (`251f18a7…`, `90609c9b…`) have no review file in the tree either. This matches the M2 hand-off finding (`mac-x5v2-20261104:docs/r1/reports/MAC_M2_HANDOFF_20261104.md:21`).
- "The running `t7j10` is not touched" is grounded in R1-EXAM-A1-M1-REQUIREMENTS ("不要动正在跑的 `t7j10`。") and in R1-TRACKX-HANDOVER-RULING. It is a restatement, not a new rule. **OK.**
- The range `19b8f33f..74a07907` is real. Both endpoints resolve, `19b8f33f` is an ancestor of `74a07907`, and the range holds exactly four commits: `e996af88`, `96f11463`, `ab74203e`, `74a07907`. `19b8f33f` is the Track X Stage A code pin in `MAC_LOCAL_RUNBOOK_20261104.md:95` and the parent of `e996af88`. The range is technically sound. However, see finding 1.

### Findings on `fed20ea2`

**1 MINOR: the agent's implementation details in consequence bullet 2 read as the author's decision.** The bullet puts the following under the same unlabelled "**Consequences** (not part of the decision cells)" heading as the author's ruling:
- (a) the extension to `e996af8` ("reviews of `e996af8` and `ab74203` are not relied on"; "covering `e996af8`");
- (b) the range `19b8f33f..74a07907`;
- (c) the output path `reviews/MAC_M5_AB74203_REVIEW_20261104.md`.

None of these is in the author's words. (a) also goes beyond the question as the same subsection records it: the lead paragraph says the question was whether "the cited but uncommitted reviews of `ab74203` count". Covering `e996af8` is a sensible choice. `ab74203`'s code contains the A1 change, and the M2 hand-off flagged both reviews. But the choice is the agent's. The author's standing practice, as the 15:44 and 16:39 subsections apply it, is that agent wording carries a label: "*Recorder's note (not the author's words):*". The 17:30 subsection has no such label. A later reader would take the range, the file path and the `e996af8` scope as ruled by the author.

**Fix (before push; these lines are result-only and unpushed):** keep in the consequences only what the author ruled: the cited but uncommitted review of `ab74203` is not relied on, a new reviewer reviews it by the M5 procedure, and `t7j10` is not touched. Move (a)–(c) to a labelled "*Recorder's note (not the author's words):*", for example: "the Mac agent scopes the review as `19b8f33f..74a07907` (focus `ab74203`, also covering `e996af8`, whose cited reviews are likewise uncommitted); output `reviews/MAC_M5_AB74203_REVIEW_20261104.md`."

**2 MINOR: "three numbers" renders "三项" (three items) and recurs in `00f10282`.** The author wrote "三项", not "三个数字". One of the three items, the template result, is a pass/fail result with per-check evidence, not a number. `seed_reproducible` is not necessarily a number either. The PLAN consequence avoids the problem by listing the three items, but the lead paragraph's option text and, more importantly, the operator message and the STATUS entry (see §3) say "three numbers". The option text quotes what the agent offered, so it can stay. **Fix:** in the operator message and the STATUS entry, write "three items" or "three values (parse rate, reproducibility, template result)".

**Cosmetic, no fix needed:** the commit body of `fed20ea2` says the questions were "put at 17:26". The agent put them in reply to the 17:26 message, and the PLAN text states this correctly. Rewriting a commit for this is not worth it.

## 2. `plan_row_check`

`r1/scripts/plan_row_check.py` in the worktree is byte-identical to `00f10282:r1/scripts/plan_row_check.py`. I ran:

```
python3 r1/scripts/plan_row_check.py --result 00f10282 --source origin/codex/coordinator-20261031 --source origin/docs/main-proposer-03nov --source origin/docs/runbooks-04nov --source origin/codex/b2-repair-20261031 --source 13badb0 --source origin/trackS-ops-20261030
```

Results:
- **`MISSING total: 0`**.
- PLAN §10 rows: every source has all items present byte-identical (coordinator 235/235, main-proposer 230/230, runbooks 264/264, b2-repair 193/193, `13badb0` 207/207, trackS-ops 200/200).
- STATUS: every source is fully present.
- The only non-identical "other line" is the "Historical index" blockquote. It is EDITED-BY/SUPERSEDED-IN `origin/docs/runbooks-04nov` and kept in the result. This is pre-existing and outside this range, because `fed20ea2` adds lines only.
- The new subsection lines and the new STATUS entry appear as RESULT-ONLY, as expected.

**OK.**

## 3. `00f10282`: operator message, gate, STATUS

**Scope of change.** The commit changes two files: `AUTHOR_DECISIONS_20261104.md` (2 lines changed: the gate paragraph and the message) and `STATUS.md` (1 line added at the top of the newest-first log). Nothing else changes. **OK.**

**The operator message carries the criterion faithfully.** The only change is one inserted clause after "must agree with `t7h8`": "— per R1-EXAM-A1-ANCHOR-CRITERION (17:30): `qwen25_coder_7b`'s three numbers exactly equal, `random_valid` and `scripted` compared on result status only". The rest of the message is unchanged ("if they do not, `t7j10` is not accepted and you report to the author before anything else. Do not touch the running `t7j10`. No other new server step is unlocked by M1."). The message correctly does not mention the M5 review, which concerns the Mac agent and not the operator. **Faithful, and it adds nothing**, apart from the "three numbers" wording (finding 2).

**The gate paragraph is consistent.** It now requires R1-TRACKX-HANDOVER-RULING, R1-EXAM-A1-M1-REQUIREMENTS **and R1-EXAM-A1-ANCHOR-CRITERION** to be in PLAN §10, independently reviewed and pushed before the operator is pointed at `mac-int-20261104`. This is correct, because the message now cites the new row. The gate does not wait on R1-EXAM-AB74203-M5-REVIEW, which is consistent with the author's ruling (it does not tie the operator message to the M5 review).

**3 MINOR: the gate's list of review files names only the two earlier reviews.** The gate requires the anchor-criterion row to be independently reviewed, but the parenthesis lists only `reviews/MAC_RULING_ROW_REVIEW_20261104.md` and `reviews/MAC_A1_REQUIREMENTS_REVIEW_20261104.md`, both present at `00f10282`. **Fix (before the message is sent):** add `reviews/MAC_RULINGS_1730_REVIEW_20261104.md` (this file) once it is committed, so that `<commit>` is a pushed head containing the review that clears the gate.

**The STATUS entry is accurate as far as git can show.**
- The rows, the criterion summary and "added to the operator message" are correct (but see finding 2 for "three numbers").
- "fresh M5 review of `19b8f33f..74a07907`": the range is correct (§1). STATUS is an AI-assisted log, not a PLAN row, so naming the agent's range there is fine.
- "M2 (`mac-x5v2-20261104`, x5_rule_v2 sha `79d8c5cb…`) delivered" is correct. The branch exists at `8eae4f84` (two commits on `74a07907`), and `MAC_M2_HANDOFF_20261104.md:7` and `r1/exam/rules/x5_rule_v2.yaml.sha256` give `79d8c5cb315d…`.
- "M11 started (`mac-gate-20261104` from `cfa74cd4`)" is correct. The branch exists at `cfa74cd4` with no commits yet.
- "running" (the M5 review) and "under independent review" (M2) are process states that git cannot show. No `MAC_M5_AB74203_REVIEW_20261104.md` exists yet, tracked or untracked. These are not findings.

**4 MINOR: "result status" is the author's term and is left undefined. That is correct, but the operator may need a pointer.** In `t7h8`'s code, the software-anchor row's status fields are `passed: true`, `software_anchor: true`, `failure_classes: []` and `mechanical_model_checks: not_applicable` (`3b3283f:r1/scripts/exam_runner.py:115–116`). The records rightly do not define "result status", because a definition would be an addition. If the operator meets a case where these fields disagree, the established route applies: report to the author. **Optional:** a labelled recorder's note naming where the anchor row is written. No change to the message is needed.

## Summary of fixes

| # | Severity | Where | Fix | When |
|---|---|---|---|---|
| 1 | MINOR | PLAN §10 17:30 consequence bullet 2 | Move the `e996af8` extension, the range and the output path into a labelled "*Recorder's note (not the author's words):*" | Before push |
| 2 | MINOR | Operator message, STATUS | "three numbers" → "three items/values" (author: "三项") | Before the message is sent |
| 3 | MINOR | Gate paragraph | Add this review file to the listed reviews | Before the message is sent |
| 4 | MINOR | (optional) PLAN recorder's note | Point to the software-anchor row fields; no definition | Optional |

## Re-check: `899edbb7` (on `00f10282`)

**Scope.** `899edbb7` has a single parent, `00f10282`. `git diff --numstat 00f10282 899edbb7` shows changes to three files only: `PLAN.md` (+4 −2), `STATUS.md` (+1 −1) and `AUTHOR_DECISIONS_20261104.md` (+2 −2). All the hunks are in the places the findings name: the 17:30 consequences in PLAN, the top STATUS entry, and the packet's gate paragraph and operator message. Nothing else changed. Local `mac-int-20261104` is at `899edbb7`, three commits ahead of origin, so nothing has been pushed yet.

**Decision cells are unchanged.** PLAN lines 889–892 (table header and both rows) have the same md5 at `00f10282` and `899edbb7` (`02146d05…`). The lead paragraph (line 887) is also unchanged.

**Finding 1: FIXED.** The consequences now hold only what the author decided:
- Bullet 1 is the criterion: the three items, exactly equal; software anchors compared on result status only; otherwise not accepted, and the author is told first.
- Bullet 2 reads "The cited but uncommitted review of `ab74203` is not relied on; a fresh independent reviewer reviews it by the M5 procedure. The running `t7j10` is not touched." Each part is grounded in "按 M5 流程另开新 reviewer 重新审", the M5 procedure's step 3, and R1-EXAM-A1-M1-REQUIREMENTS / R1-TRACKX-HANDOVER-RULING. Scoping the review to `ab74203` matches the recorded question.

The range, the extension to `e996af8` and the output path have moved to a note headed "*Recorder's note (not the author's words):*". This is the same label the 15:44 and 16:39 subsections use. The note is accurate:
- `19b8f33f..74a07907` contains `e996af88`, `96f11463`, `ab74203e` and `74a07907`.
- `e996af88` is an ancestor of `ab74203e` ("on which `ab74203` builds").
- The reviews cited for `e996af8` (`251f18a7…`, `90609c9b…`) have no file in the tree ("likewise not committed").

**Finding 2: FIXED.** "Three items" is now used in the PLAN consequence, the operator message and the STATUS entry. `git grep 'three numbers' 899edbb7 -- docs/r1` finds it in docs/r1 only at PLAN line 887, which is the option text the agent offered and was quoted as offered (acceptable, as noted in finding 2). The other hits are unrelated files. The phrase "Stage A numbers" in the operator message and the 16:39 STATUS entry is older text that renders the author's own "Stage A 数字", so it is correct.

**Finding 3: FIXED.** The gate paragraph now lists `reviews/MAC_RULINGS_1730_REVIEW_20261104.md` after the two earlier reviews. The rest of the paragraph is unchanged. This review file is still untracked, so it must be committed in the pushed `<commit>` before the message is sent.

**Finding 4: FIXED (optional item taken).** The recorder's note points "result status" to `passed`, `software_anchor`, `failure_classes` and `mechanical_model_checks` at `3b3283f:r1/scripts/exam_runner.py`. All four keys appear in the software-anchor row at lines 115–116: `'passed':True,'software_anchor':True,…,'failure_classes':[],'mechanical_model_checks':'not_applicable'`. The note leaves out `prompts`, `candidate`, `label` and `phase`, which is reasonable because those are not status fields. It labels the pointer as the recorder's and gives no definition, so it adds nothing to the author's ruling.

**`plan_row_check` on `899edbb7`** (same six sources): `MISSING total: 0`. The source counts are the same as for `00f10282`.

**Re-check verdict: accepted.** 0 BLOCKING, 0 MAJOR, 0 MINOR open. Before the operator message is sent, this file must be committed and pushed so that the gate's reference resolves.
