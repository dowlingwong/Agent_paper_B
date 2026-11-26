# Review — mac-int-20261104, commits 98e433e0..0b7084a0 (R1-TRACKX-HANDOVER-RULING and follow-ups)

**Reviewer:** independent reviewer subagent (Claude), 4 Nov 2026. AI-assisted. I did not write the work under review. Every statement below was checked against git objects; nothing was run on a server, no LLM, no GPU. Nothing was staged, committed or pushed except that this file exists in the working tree.

**Scope:** `4ca40393` (integration of `docs/runbooks-04nov` c15b1102→0abfaf2b), `f89e13d4` (PLAN §10 row R1-TRACKX-HANDOVER-RULING), `0b7084a0` (RUNBOOK §5 cell, packet notes, STATUS entry). Reference texts: the author's 16:13 message (instructions 1–4), his 15:33 and 15:44 messages as given to the reviewer, and packet §0 (`docs/r1/proposals/AUTHOR_DECISIONS_20261104.md`) at `98e433e0` and at `0b7084a0`.

## Verdict: **accepted**

0 BLOCKING, 0 MAJOR, 11 MINOR. None of the MINOR findings changes a decision or blocks the push. Finding 3.4 (the operator message names the old source SHA) **must be fixed in the message text before it is sent** to the operator. Finding 2.1 (modality of "runs to completion") is recommended before the push, because the PLAN row cannot be edited afterwards without a new row.

---

## Check 1 — `4ca40393` (docs/runbooks-04nov c15b1102→0abfaf2b)

Verified:
- `origin/docs/runbooks-04nov` = `0abfaf2b`; `c15b1102` is an ancestor of `0abfaf2b`. The range c15b1102..0abfaf2b has three commits and no merges: `8fa64885` (HoreKa scan prompt rev 5.3), `959eeac0` (Mac runbook rev 3.3), `0abfaf2b` (HoreKa scan prompt rev 5.4). `git log --name-only` and `git diff --name-only c15b1102 0abfaf2b`: they touch only `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md` and `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md`.
- `git diff --stat 98e433e0 4ca40393`: the same two files and nothing else (69 insertions, 31 deletions; identical to `git diff --stat c15b1102 0abfaf2b`).
- For both files the blob at `98e433e0` equals the blob at `c15b1102` (`243fce87…`, `ca3da211…`): neither changed on mac-int since 7da89e8c integrated c15b1102. A per-file `git merge-file` (ours = 98e433e0, base = c15b1102, theirs = 0abfaf2b) is clean (exit 0) and byte-identical to the blob in `4ca40393` (`b5915aa6…`, `b0a5d2dc…`), which also equals the 0abfaf2b blob.
- No PLAN, STATUS or code change on the source range, as the commit body says.

Findings:

**1.1 MINOR — the commit body's quote drops the author's backticks.** The body has "把 docs/runbooks-04nov @ 0abfaf2b 单独合进 mac-int，只审这段 diff。"; the author wrote "把 `docs/runbooks-04nov` @ `0abfaf2b` 单独合进 mac-int，只审这段 diff。". Markup only; meaning unchanged. *Fix:* none needed now; keep backticks in future quotes.

*Note (no finding):* `4ca40393` is a single-parent commit, not a git merge (0abfaf2b is not a parent). This follows the M1 convention (`7da89e8c` is single-parent too) and the commit body names the range; the provenance is in the message, not in the DAG.

---

## Check 2 — `f89e13d4` (PLAN §10 row)

Verified:
- `git show f89e13d4 --stat`: only `docs/r1/PLAN.md`, 16 insertions, 0 deletions. The hunk inserts one new subsection after the 14:58 subsection and before `## 11. Relation to Paper A`. No existing line is altered.
- Decision cell: `| R1-TRACKX-HANDOVER-RULING | "按原定计划走" |` — the author's words only, as instruction 1 requires. Table header `| Decision | Author decision (4 Nov 2026, 15:44) |` and subsection heading `### 4 November 2026 (15:44) — … (author; recorded by an AI agent, Claude, Mac-local agent)` follow the 13:45 and 14:58 subsections' pattern. The "(15:44)" attribution follows the author's own "（15:44）" in instruction 1; the intro paragraph correctly records that he first wrote the words at 15:33.
- Quotes in the intro paragraph are verbatim: "按原定计划走", "交接行优先", and "决策格只写我的原话"按原定计划走"（15:44），其余细节……写进 consequences" (elision marked).
- Consequences against the author's 15:44 message and instruction 1, item by item:

| Author (15:44 / 16:13) | Consequence bullet | Result |
|---|---|---|
| 选 2，交接行优先 | 1: R1-HANDOVER-04NOV takes precedence over the Track X agent's post-handover work | present; wording partly the recorder's (2.2) |
| `t7j10` 已在 TASL-7 上运行，允许它跑完，Track X agent 随后停止 / t7j10 跑完后 Track X agent 停 | 2 | present; modality changed (2.1); code/binding added (2.2) |
| `t7j10` 的核验和接收审查、Stage A 验收归 operator 的 O1 | 3 | exact |
| 你从 `74a0790`（代码 `ab74203`）起接手 `r1/exam/`，M2 以它为基 | 4 | exact |
| 如果 `ab74203` 还缺独立 review，就按 M5 流程补 | 4 | exact |
| B1 候选集 = `t7h8` 的 8 个 PASS + anchors + `t7j10` 的通过者，经 operator 验收后才算数 | 5 | exact |
| 整合以 `10742f85` 为底 / 以 `10742f85` 为底 | 6 | exact |
| 这条裁定写进决策包第一项 | — | procedural, done in packet §0 at `a43e1b47`; correctly not in PLAN |

  Nothing the author said is missing. The SHAs `74a0790`, `ab74203`, `10742f85` resolve; `t7j10`'s code/binding pair matches R1-EXAM-STOP9-JOURNAL.
- Commit body quotes the first two sentences of instruction 1 (see 2.4).
- `plan_row_check.py` (command as given; result `mac-int-20261104` = `0b7084a0`): exit 0, **MISSING total: 0**. PLAN §10 rows: every source fully present byte-identical; RESULT-ONLY = the new table header and the new row. PLAN §10 other lines: the only non-identical items are the known `> **Historical index.** …` line tagged EDITED-BY / SUPERSEDED-IN `origin/docs/runbooks-04nov` (the kept line is the runbooks version); RESULT-ONLY = the 9 lines of the new subsection. STATUS: every source fully present; RESULT-ONLY = the new 16:13 entry and the earlier M1 integration entry (both mac-int's own). All as expected.

Findings:

**2.1 MINOR — "runs to completion" turns the author's permission into a statement.** 15:44: "允许它跑完" (it is *allowed* to run to completion). Bullet 2 says "… already running on TASL-7, runs to completion; the Track X agent then stops." The packet's draft row had "may run to completion". If `t7j10` STOPs or fails, the PLAN text reads as if completion were required or assured. Instruction 1's "t7j10 跑完后 Track X agent 停" does not change the 15:44 modality. *Fix (before push):* "… already running on TASL-7, may run to completion; the Track X agent then stops."

**2.2 MINOR — recorder's glosses inside a block labelled as the author's details.** The Consequences heading says "the author's details from 15:44 and 16:13". Three pieces are the recorder's, not the author's: (i) bullet 1 "over the Track X agent's post-handover work" (the author said only "交接行优先", option 2); (ii) bullet 2 "(code `ab74203`, binding `74a0790`)" and "declared measurement" (from R1-EXAM-STOP9-JOURNAL); (iii) bullet 4's parenthetical on `r1/scripts/exam_*` (correctly attributed to R1-HANDOVER-04NOV). All are accurate and none adds a decision, but (i) can be read as voiding the coordinator's post-handover rows wholesale (e.g. the A1 amendment itself), which option 2 did not do — option 2 froze the A1 code and changed who executes. *Fix (optional, before push):* bullet 1 → "R1-HANDOVER-04NOV takes precedence (option 2 of packet §0)."; mark (ii) as "(per R1-EXAM-STOP9-JOURNAL)".

**2.3 MINOR — no note of which earlier rows this amends.** R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED records "B1 eligible set = t7h8 8 PASS + anchors + M1-passing rows (author's decision)"; the new ruling adds operator acceptance of `t7j10`. The neighbouring 4 Nov subsections name the rows they amend. The author did not say this, so it must not go into his Consequences block. *Fix (optional):* leave the row as is; if wanted, a separately labelled line "Recording agent's note (not the author's): this narrows R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED's B1 eligible set." — or leave it to the R1-EXAM-RULE-X5V2 row, which already restates the set.

**2.4 MINOR — commit-body quote: line wraps and an unmarked cut.** The quote is byte-identical to instruction 1 apart from hard wraps inside CJK text (rendered as spaces in many viewers, e.g. "原话 "按原定计划走"") and ends at "写进 consequences。" without marking that the instruction continues ("提交前由新 reviewer … 连同 SHA 给我。"). *Fix:* none required for this commit; in future, add "…" for a cut quote.

**2.5 MINOR (process) — commit before review.** Instruction 1 says "提交前由新 reviewer 对照决策包 §0 核对，过了再推". The row was committed locally before this review. The branch is 3 commits ahead of `origin/mac-int-20261104` and unpushed, so the order the author cares about (review before push) holds, and any fix can still be amended in. If "提交" was meant literally as "commit", tell the author it was a local, unpushed commit.

**2.6 MINOR (pre-existing, packet §0 at 98e433e0 and 0b7084a0) — the "as received" quote of 15:44 is incomplete.** Packet §0 says "The quotation is the author's 15:44 message as received", but it stops after "…才算数。"; the 15:44 text given to this reviewer continues "这条裁定写进决策包第一项。整合以 `10742f85` 为底。" Both omitted points are covered elsewhere (§0 itself; Consequences bullet 6), so no meaning is lost. *Fix:* append the two sentences, or add "…" and drop "as received".

---

## Check 3 — `0b7084a0` (RUNBOOK §5, packet notes, STATUS)

Verified:
- RUNBOOK §5, Track X B1/B2 row: "*pending R1-TRACKX-HANDOVER-RULING* (drafted in … §0: …)" → "per R1-TRACKX-HANDOVER-RULING (consequences): `t7h8` 8 PASS + anchors + operator-accepted `t7j10` passes; D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) unchanged", and the row is added to the sources column. Accurate; the D28/thinking-off part is correctly attributed to R1-MAIN-PROPOSER (a), not to the ruling. One cell changed, nothing else.
- Packet §0 note: accurate (decision cell = his words only; details under Consequences; draft row kept as history, superseded).
- Packet (a) note: "(a) 同意：5 个范围外文件并入 M3 一起审，审完我再决定。" — byte-identical to instruction 2. Gloss "(option 3: reviewed within M3; he decides after that review)" is faithful; "Not yet a PLAN row."
- Packet (k) note: "(k) 同意：测试在云端跑可以；那 3 个 `test_c3_launch_provenance` 失败只有在 M3 修好的前提下才算已知例外。" — byte-identical to instruction 3; gloss faithful; "Not yet a PLAN row."
- STATUS: new top entry. Points (1)–(4) match instructions 1–4; "Points (2) and (3) are not PLAN rows." Worker bases verified: `mac-x5v2-20261104` = `74a07907` (no commits on it yet), `mac-b2-20261104` = `f98e315e`, `mac-trackg-20261104` = `98e433e0`. Neither (a) nor (k) is marked as a PLAN row anywhere. No decision is added.

Findings:

**3.1 MINOR — STATUS paraphrases the 16:13 replies instead of quoting them.** Points (2) and (3) are faithful paraphrases; only "按原定计划走" is quoted. The verbatim text is in the packet notes, so the record is complete. *Fix (optional):* add "(verbatim in packet (a), (k))".

**3.2 MINOR — STATUS entry mixes the author's replies with the agent's own actions under one attribution.** It is headed "Author's replies to the M1 packet (4 Nov 16:13 …)", but (5) "M10 started …" and (6) "M11 and M13 follow in the Mac agent's order", and the worker list, are the agent's actions, not the author's replies. *Fix (optional):* begin (5) with "Mac agent:" or move (5), (6) and the worker list after a separator such as "Agent activity:".

**3.3 MINOR — packet (k)'s draft row now contradicts the author's condition.** The author made the exception conditional: the three failures count as a known exception *only once M3 has fixed them*. The unchanged draft row R1-M1-TEST-EXCEPTIONS still says they "are accepted as an exception to M1's Done-when; M3 fixes the fixtures", i.e. unconditional. The note sits above it, but the paste-ready row would record more than he granted. (Also, the note is placed under item 1 while it answers items 1 and 2.) *Fix:* mark the draft row "superseded by the author's 16:13 condition; to be redrafted", or redraft: "… are a known exception to M1's Done-when only once M3 has fixed them; until then M1's test criterion is not met for these three."

**3.4 MINOR, fix before sending — the paste-ready operator message names the old source SHA.** Packet "Hand-off to the operator", line 215 at `0b7084a0`: "It integrates coordinator `10742f85`, `docs/runbooks-04nov` @ `c15b1102`, …". After `4ca40393` the branch integrates `docs/runbooks-04nov` @ `0abfaf2b`. The packet header (line 5) has the same stale SHA. The operator runbook itself is unchanged by c15b1102→0abfaf2b, so no operator step changes, but the message the author asked to receive "连同 SHA" would be factually wrong. *Fix:* in the message sent (and preferably in the packet), write "`docs/runbooks-04nov` @ `0abfaf2b` (c15b1102 in M1, 0abfaf2b added in `4ca40393`)", and fill `<commit with R1-TRACKX-HANDOVER-RULING>` with the pushed head that contains it (currently `0b7084a0`, or the amended head if 2.1/2.2 are applied).

---

## Summary table

| # | Check | Grade | Short |
|---|---|---|---|
| 1.1 | 1 | MINOR | 4ca40393 body quote drops backticks |
| 2.1 | 2 | MINOR | "runs to completion" vs 允许它跑完 ("may") — fix before push recommended |
| 2.2 | 2 | MINOR | recorder's glosses inside the author-details block (bullet 1 wording, code/binding) |
| 2.3 | 2 | MINOR | no note that the B1 set narrows R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED (not to be put in the author's block) |
| 2.4 | 2 | MINOR | commit-body quote wraps, unmarked cut |
| 2.5 | 2 | MINOR | committed locally before review (unpushed; recoverable) |
| 2.6 | 2 | MINOR | packet §0 "as received" 15:44 quote lacks its last two sentences (pre-existing) |
| 3.1 | 3 | MINOR | STATUS paraphrases rather than quotes (verbatim is in packet) |
| 3.2 | 3 | MINOR | STATUS attributes agent actions (5), (6) to "author's replies" |
| 3.3 | 3 | MINOR | packet (k) draft row unconditional, author made it conditional |
| 3.4 | 3 | MINOR | operator message cites `c15b1102`, now `0abfaf2b` — fix before sending |

(11 findings, all MINOR; 1.1, 2.4 and 2.5 are cosmetic or process only.)

---

## Re-check — commit `8b1fda5e` (on `0b7084a0`)

**Verdict: accepted.** 0 BLOCKING, 0 MAJOR, 1 MINOR (residual of 3.2; it does not block the push).

Scope verified from git objects: `8b1fda5e` has a single parent, `0b7084a0`, and is HEAD of `mac-int-20261104`, which has not been pushed (`origin/mac-int-20261104` = `98e433e0`). It changes only `docs/r1/PLAN.md` (+4/−2, all inside the new 15:44 subsection of §10), `docs/r1/STATUS.md` (the 16:13 entry only) and `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md`. Nothing else changed.

**Decision cell.** At `8b1fda5e`, PLAN line 853 is still `| R1-TRACKX-HANDOVER-RULING | "按原定计划走" |`. It occurs once in §10.

**plan_row_check** (same sources, `--result 8b1fda5e`): MISSING total 0. The only RESULT-ONLY items are the new subsection's lines (now 10, including the recorder's note) and mac-int's own two STATUS entries.

| Finding | Status | Evidence |
|---|---|---|
| 2.1 | **FIXED** | "`t7j10`, already running on TASL-7, may run to completion; the Track X agent then stops." Matches 15:44 "允许它跑完". |
| 2.2 | **FIXED** | Bullet 1 is now "R1-HANDOVER-04NOV takes precedence (15:44: "交接行优先")", which quotes the author's words exactly. The code/binding pair is now a parenthetical attributed to R1-EXAM-STOP9-JOURNAL. "declared measurement" is removed. |
| 2.3 | **FIXED** | A separate paragraph after the Consequences, labelled "*Recorder's note (not the author's words):*". It quotes R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED exactly ("B1 eligible set = t7h8 8 PASS + anchors + M1-passing rows") and states the narrowing correctly. It adds no decision. |
| 2.6 | **FIXED** | Packet §0's 15:44 quote is now byte-identical to the full message ("…这条裁定写进决策包第一项。整合以 `10742f85` 为底。"). The English gloss is extended to match, so "as received" now holds. |
| 3.2 | **PARTLY FIXED** (see R-1) | The entry header now names both the author and the Mac agent, and the worker list sits under "Mac agent:". |
| 3.3 | **FIXED** | The old draft row is marked "Superseded by the author's 16:13 reply (above); kept as history". A redrafted row states the condition ("only once M3 has fixed them") and quotes "只有在 M3 修好的前提下才算已知例外" exactly. It is offered "if he wants a row" and is not presented as a PLAN row. |
| 3.4 | **FIXED** | The packet header now has "later `0abfaf2b` (merged separately, `4ca40393`)". The operator message template has `docs/runbooks-04nov` @ `0abfaf2b` and a `<commit>` placeholder that the integrator fills. Its summary of the ruling (may run to completion; verification, receiving review and Stage A acceptance in O1; B1 set = `t7h8` 8 PASS + anchors + accepted `t7j10` passes) matches the Consequences, and "under review in M3" matches reply (a). |
| 1.1, 2.4 | Not changed (accepted) | Commit-body formatting only. Rewriting reviewed commits would cost more than these cosmetic fixes are worth. |
| 2.5 | Answered | Nothing has been pushed (confirmed above). |
| 3.1 | Answered | The STATUS header now points to the verbatim text in the packet. |

**R-1 MINOR (residual of 3.2).** Items (5) "M10 to start (local worktrees; harness write access requested …)" and (6) "M11 and M13 follow in the Mac agent's order" are still listed under "Author:". The 16:13 text given to this reviewer contains only items 1–4. If (5) and (6) come from the author's message beyond that text, the entry is correct as it stands. If they are the Mac agent's own plan, move them after "Mac agent:". *Fix:* the integrator checks this against the author's full 16:13 message. It does not block the push.
