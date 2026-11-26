# Independent review — R1-EXAM-A1-M1-REQUIREMENTS and its follow-up records (4 Nov 2026)

**Reviewer:** fresh independent reviewer (AI agent, Claude), not the author of the reviewed commits. Read-only apart from this file; nothing staged, committed or pushed. No servers, LLMs or GPU used.

**Scope:** `009d859a..fe193b3b` on `mac-int-20261104`:
- `2ed9380b` — PLAN §10 subsection "4 November 2026 (16:39) — A1 amendment and `t7j10`: three requirements", row R1-EXAM-A1-M1-REQUIREMENTS;
- `fe193b3b` — heading change in `docs/r1/reports/EXAM_TEMPLATE_AMENDMENT_IMPLEMENTED_20261104.md`, operator message in `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` ("Hand-off to the operator — gated"), STATUS entry.

Everything below was checked against git objects (`git show`, `git grep` at named commits), not against summaries. Note: `origin/mac-int-20261104` is still at `009d859a`, so neither reviewed commit has been pushed yet. The local head is now `316ba2a5`, two out-of-scope commits past `fe193b3b`.

## Verdict

**accepted** — 0 BLOCKING, 0 MAJOR, 5 MINOR. None of the MINOR findings changes what the author decided or blocks the push. Findings 4 and 5 should be dealt with before the operator message is sent, or before M2 and M4 are accepted, as noted in each finding.

## 1. `2ed9380b` — PLAN §10 row

**Scope of change.** `git diff --numstat 009d859a fe193b3b` gives `19 0 docs/r1/PLAN.md` for `2ed9380b`: insertions only, no deletions. The block sits between the 15:44 subsection's recorder's note (ends at line 863) and `## 11. Relation to Paper A` (now line 884), so it is inside §10. No existing line is altered. **OK.**

**Verbatim check.** I wrote the author's 16:39 message (as given in the task) to a file and searched for each fragment in `fe193b3b:docs/r1/PLAN.md`. The opening sentence, the body text of (1), (2) and (3), and "不要动正在跑的 `t7j10`。" each occur exactly once, byte for byte. The decision cell `"关于 A1 修订和 `t7j10`（M1），我补三条要求"` occurs once (line 871). The lead paragraph quotes the instruction up to "并交新 reviewer 审". **OK.**

**Decision-cell reading.** "决策格用我这句话" most naturally means "the sentence I am writing now", that is, the opening sentence before the colon. The integrator kept its first clause and left out the meta-instructions ("请写进 PLAN（…），并交新 reviewer 审"). Those instructions are still quoted verbatim in the lead paragraph. Another reading is possible: the whole sentence up to the colon. Putting instructions to the recorder in a decision cell would be odd, though, and either reading attributes the same words to the author. The other conceivable reading, the whole message, conflicts with "细节放 consequences". The choice is reasonable and does not misrepresent him. As a result the cell carries no decision content of its own; the substance is in the Consequences, which is what he asked for. Not a finding.

**Recorder's notes.** They are labelled "*Recorder's notes (not the author's words):*". Checked:
- "supersedes the "M1-only" wording in R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED ("repairs SHA-pinned/reviewed/M1-only")": PLAN line 717 contains exactly "repairs SHA-pinned/reviewed/M1-only". **Accurate.**
- "At `74a0790` the registry's `template_repair` is read by `r1.exam.runtime.template_repair_args`, which the replay server and the qualification probe call (SHA mismatch is a STOP)". `git grep template_repair_args 74a07907 -- r1` finds:
  - the definition at `r1/exam/runtime.py:29`. It reads `spec['template_repair']`; a missing file raises `RuntimeError('STOP: template repair file missing')` and a digest mismatch raises `'STOP: template repair digest mismatch'`;
  - the replay-server call `ExamRunner._server`, `runtime.py:356`;
  - the qualification-probe call `r1/exam/qualify.py:117`;
  - tests in `r1/tests/test_template_repair.py`.

  `74a0790` resolves uniquely to `74a0790739b7…`. **Accurate.**
- "the Mac agent is the `r1/exam/` editor": matches R1-TRACKX-HANDOVER-RULING's consequences ("takes over `r1/exam/` from `74a0790`"). **Accurate.**
- "Requirement (3) is for the manuscript (M8)": M8 is "Theory and manuscript" in `MAC_LOCAL_RUNBOOK_20261104.md`. **Accurate.**

**Format.** The heading pattern ("### 4 November 2026 (HH:MM) — … (author; recorded by an AI agent, Claude, Mac-local agent)"), the lead paragraph with the quote and gloss, the two-column table "| Decision | Author decision (4 Nov 2026, HH:MM) |" with a bare row ID, the "**Consequences** (…; not part of the decision cell)" list and the italic recorder's note all match the 15:44 subsection directly above. **OK.**

## 2. Row check

`python3 r1/scripts/plan_row_check.py --result mac-int-20261104 --source origin/codex/coordinator-20261031 --source origin/docs/main-proposer-03nov --source origin/docs/runbooks-04nov --source origin/codex/b2-repair-20261031 --source 13badb0 --source origin/trackS-ops-20261030`:

| source | items | present byte-identical |
|---|---|---|
| origin/codex/coordinator-20261031 | 853 | 853 |
| origin/docs/main-proposer-03nov | 847 | 847 |
| origin/docs/runbooks-04nov | 856 | 856 |
| origin/codex/b2-repair-20261031 | 798 | 798 |
| 13badb0 | 817 | 817 |
| origin/trackS-ops-20261030 | 887 | 887 |

**MISSING total: 0.** The RESULT-ONLY items are the new 16:39 lines, the 15:44 subsection's lines and the three Mac STATUS entries, all of which were added on this branch. That is expected.

While I was reviewing, the local branch moved past the reviewed range: `210aa99e` (runbooks-04nov 0abfaf2b..8e455234) and `316ba2a5` (repo-tidy). Both are outside this review's scope. I therefore also ran the same command with `--result fe193b3b`:
- PLAN §10 rows: all present byte-identical (coordinator 235/235, main-proposer 230/230, runbooks 264/264, b2-repair 193/193, 13badb0 207/207, trackS-ops 200/200);
- STATUS: as in the table;
- **MISSING total: 0.**

In "§10 other lines", one item per source is not byte-identical: the "Historical index" blockquote. The tool already classifies it as EDITED-BY/SUPERSEDED-IN `origin/docs/runbooks-04nov` (`reports/MAC_PLAN_ROW_CHECK_20261104.md:22–35`), it is untouched by `2ed9380b`, and it does not count as missing.

## 3. `fe193b3b` — follow-up records

**Report heading.** `## Declared repairs (SHA-pinned, M1-only)` became `## Declared repairs (SHA-pinned, effective from M1, carried with the model)`. "Effective from M1, carried with the model" is a faithful rendering of "M1 起生效，随模型延续", and it is the same rendering PLAN uses. An italic dated note follows. It cites the row, quotes the author's instruction verbatim and states the old wording ("it read "M1-only""). The note is honest and complete. The report is not pinned by hash anywhere: neither the old blob `d0c47255…` nor its sha256 is referenced on the branch, and RUNBOOK §5 cites the report by path only. The edit therefore breaks no pin. **OK.**

**Other "M1-only" wording that (1) would cover.** I ran `git grep -E "M1.only|only.{0,12}\bM1\b" fe193b3b -- docs` and also searched the branch for "repair" near "M1", "only" or "amendment measurement".
- In the report: the only scope statements left are about the *measurement* ("M1 is not spliced into the t7h8 table…"). They are not about the repairs, and the heading at line 8 already says the A1 rule "applies to normal Stage A runs, not just M1".
- `EXAM_TEMPLATE_AMENDMENT_PROPOSAL_20261104.md` §4 and §6 say repairs are "measured in the M1 attempt" and that "every repaired row is measured in M1". Neither says "only".
- The STATUS entry of the A1 implementation says "Repairs SHA-pinned, probe==replay, launcher pins templates", with no M1 limit.
- The registry `template_repair.reason` fields at `74a07907` carry no M1 limit.
- Apart from PLAN line 717, which is excluded and must stay, the only remaining hits are the new 16:39 records themselves.

**Nothing else needs changing.**

**Operator message.** The single changed line keeps the earlier text and inserts two sentences before "No other new server step is unlocked by M1." Against criterion (2):
- the three anchors (`random_valid`, `scripted`, `qwen25_coder_7b`) ✓;
- the three quantities (parse rate, reproducibility, template result) ✓;
- the comparison is against `t7h8` ✓;
- "if they do not, `t7j10` is not accepted" ✓;
- "you report to the author before anything else" ✓. This renders "先报告我"; "before anything else" is a slightly stronger rendering of "先" (see finding 3).

"In `t7j10`" stands for the author's "在 M1 里". That is correct, because `t7i9` was STOPped and not reused (R1-EXAM-STOP9-JOURNAL), so M1 = `t7j10`. "Do not touch the running `t7j10`." is carried over. Strictly, the author addressed that sentence to the Mac agent, and only (2) was to go into the operator message. Passing it on to the operator is still consistent with R1-TRACKX-HANDOVER-RULING (`t7j10` runs to completion), and the reviewer brief asks for it. The message adds no other content. **OK, subject to findings 3 and 4.**

**STATUS entry.** It is accurate against PLAN and the packet. It covers (1) with the heading change and the M2/M4 routing, (2) "added to the operator message in the packet", (3) "for M8", and "the running `t7j10` is not touched". It is placed newest-first and labelled as an AI-assisted record. **OK, subject to finding 5.**

## Findings

**1 MINOR — the English rendering of (1) weakens two words.** PLAN line 874 (and the report note) render "…都**必须**用同一个 SHA 固定的修复模板" as "…*uses* the same SHA-pinned repair template". The author's "must" becomes a present-tense "uses". The same rendering turns "是否已经从 registry 的 `template_repair` **自动**读取" into "already reads the registry's `template_repair`", which drops "automatically". The Chinese, which is verbatim, governs. Still, the English is what the operator and later workers read, and "automatically" is the very property the author asked to have checked and tested: no manual flag or per-config entry. **Fix:** in the PLAN gloss, write "must use the same SHA-pinned repair template" and "already reads … automatically". Changing the gloss is a wording fix to a line added in this same commit range, so it does not touch an existing row.

**2 MINOR — criterion (2) is underspecified for two of the three anchors, and this should be put to the author instead of being left for the operator to interpret.** At `t7h8`'s code (`3b3283f:r1/scripts/exam_runner.py:115`) and at `74a07907` (`exam_runner.py:146–148`), the Stage A rows for `random_valid` and `scripted` are software-anchor stubs: `{'passed': True, 'software_anchor': True, 'prompts': 0, 'failure_classes': [], 'mechanical_model_checks': 'not_applicable'}`. They have no parse rate, reproducibility or template result. Only `qwen25_coder_7b` carries those numbers (`schema_parse_successes`, `seed_reproducible`, `template_checks`/`template_checks_frozen` in `r1/exam/stage_a.py`). "一致" also leaves open whether the parse rate must match exactly (e.g. 50/50 = 50/50) or within a tolerance. The author's wording must stay as written. If the operator meets either ambiguity, the failure is safe ("先报告我"). **Fix (optional, recorder's note only):** add to the 16:39 recorder's notes that for `random_valid`/`scripted` the Stage A row has no model numbers, so the comparison reduces to an identical anchor row; that only `qwen25_coder_7b` has parse/reproducibility/template values; and that "一致" is read as exact equality unless the author says otherwise. Alternatively, ask the author in one line before the message goes out.

**3 MINOR — small inconsistency between the PLAN gloss and the operator message on "先报告我".** PLAN says "the operator reports to the author first"; the message says "you report to the author before anything else". Both are defensible, and "the operator" as subject is a fair inference from "这条放进你要转给 operator 的消息". For a criterion that is quoted twice, though, one rendering is better. **Fix:** use "report to the author first" in both, or keep "before anything else" in both.

**4 MINOR — the hand-off gate paragraph is stale for the new row; fix before sending.** `AUTHOR_DECISIONS_20261104.md`, "Hand-off to the operator — gated", line 217 still names only R1-TRACKX-HANDOVER-RULING as the gate ("That row is committed …, independently reviewed …, and pushed with the branch"). The message now cites PLAN §10 R1-EXAM-A1-M1-REQUIREMENTS, and the author asked that this row "交新 reviewer 审". `<commit>` must therefore be a pushed head that contains `fe193b3b` and this review. `origin/mac-int-20261104` is still at `009d859a`. **Fix:**
- add to the gate paragraph that the message also waits for R1-EXAM-A1-M1-REQUIREMENTS to be committed, reviewed (this file) and pushed;
- confirm that no copy of the earlier template, which pointed at a head without criterion (2), has already reached the operator. If one has, send the criterion as an addendum before the operator starts O1's acceptance of `t7j10`.

**5 MINOR — the "check first" part of requirement (1) is routed in prose only and is not yet in any worker's brief; the facts the check would find are already visible.** The PLAN note and STATUS say "the proof for the B1/B2 path is M2's" and "'every later sweep' falls to the sweep-2 code (M4)". But:
- M2's brief (`MAC_LOCAL_RUNBOOK_20261104.md` §M2, steps 0–6) has no template-repair test, and the M2 worker is already running (`mac-x5v2-20261104` @ `74a07907`);
- M4's brief (step 2(a), line 330) passes `thinking_policy` and "the exam's server flags (`--jinja`, q8_0 KV)" to `LlamaServerInstance`, but not `template_repair`.

The current state of the code, for the record:
- *B1/B2:* at `74a07907` the reachable entry `exam_runner.evidence()` (line 225) unconditionally raises `PreparationStop('STOP: B1/B2 reviewed harness pin …')`. The retained body `_evidence_unreviewed` (line 270) starts servers through `runner.server(...)`, and from there `ExamRunner._server` appends `template_repair_args(spec)` for every phase. The repair would therefore reach B1/B2 automatically once that path is enabled. No test asserts it for a `b1`/`b2` phase: the tests in `test_template_repair.py` cover only the helper and launcher pinning, and the same is true on `mac-x5v2-20261104`. This is the "是的话补一个测试证明" branch.
- *Sweeps:* at `fe193b3b`, `r1/scripts/c3_label_sweep.py` and `r1/scripts/llama_server_instance.py` contain no `template_repair` or `--chat-template-file` handling. Only `llama_server_instance.py:84` handles `--chat-template-kwargs`. If a repaired model becomes the pick, sweep serving would use the GGUF-embedded template. This is the "不是的话改代码加测试" branch. It also covers the HoreKa `slurm` mode of the same file (`HOREKA_T1_JOBS_DRAFT_20261104.md` §5 item 3).

**Fix:**
- add a step to M2's worker brief: a test that a `b1`/`b2`-phase `ExamRunner._server` start for a spec with `template_repair` passes `--chat-template-file` with the pinned path, and STOPs on a digest mismatch;
- add a step to M4 step 2(a): thread the pick's registry `template_repair` through `start_llamacpp`/`LlamaServerInstance`, with the same SHA check and a test;
- optionally put the two code facts above into the 16:39 recorder's notes, so the "先查" result is on record.

Neither M2 nor M4 should be accepted without these.

## Summary table

| # | Commit | Grade | Subject | When |
|---|---|---|---|---|
| 1 | 2ed9380b | MINOR | (1) gloss drops "must" and "automatically" | with next PLAN edit |
| 2 | 2ed9380b / fe193b3b | MINOR | criterion (2) has no numbers for the software anchors; "一致" exact? | before the message is sent (note or one-line question) |
| 3 | 2ed9380b / fe193b3b | MINOR | "first" vs "before anything else" | with 4 |
| 4 | fe193b3b | MINOR | hand-off gate paragraph does not name the new row; branch not pushed | before sending |
| 5 | 2ed9380b / fe193b3b | MINOR | M2/M4 briefs lack the template-repair check; sweep code has none | before M2/M4 acceptance |

---

## Re-check of `869e3b48` (parent `316ba2a5`)

**Scope:** only `869e3b48`. The two commits between `fe193b3b` and `316ba2a5` (`210aa99e`, `316ba2a5`) are under a separate review.

**Verdict: accepted** — 0 BLOCKING, 0 MAJOR, 1 new MINOR (R-1, fix before the message is sent). Findings 1, 3 and 4 are fixed. The note parts of 2 and 5 are fixed. The author is being asked the question in 2.

**Nothing else changed.** `git diff 316ba2a5 869e3b48 --stat` shows two files. `docs/r1/PLAN.md` has 5 lines changed: the two English glosses replaced and one recorder's note added. `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` has 11: the gate paragraph, the message line and a new notes section at the end of the file. No code, STATUS, RUNBOOK or report file changed.

**Decision cell and quotes unchanged.** I counted the same fragments as in round 1 at `fe193b3b` and at `869e3b48`. The row `| R1-EXAM-A1-M1-REQUIREMENTS | "关于 A1 修订和 `t7j10`（M1），我补三条要求" |`, the opening sentence, the Chinese text of (1), (2) and (3), and "不要动正在跑的 `t7j10`。" each occur exactly once in both. In the diff, the changed lines differ only after the closing quote ("— …" English part).

| Finding | Status | Evidence |
|---|---|---|
| 1 | **FIXED** | The (1) gloss now reads "must use the same SHA-pinned repair template" and "already reads the registry's `template_repair` automatically". |
| 2 (note part) | **FIXED** | New bullet under "*Recorder's notes (not the author's words):*", so it is labelled. Accurate: at `3b3283f:r1/scripts/exam_runner.py:114–116` the `random_valid`/`scripted` rows are `{'passed': True, 'software_anchor': True, 'prompts': 0, 'failure_classes': [], 'mechanical_model_checks': 'not_applicable'}`. `3b3283f` is `t7h8`'s code per R1-EXAM-STAGEA-COMPLETE (PLAN line 713). The note does not rewrite the criterion; it puts the question to the author. |
| 3 | **FIXED** | The PLAN (2) gloss and the operator message both say "before anything else". |
| 4 | **FIXED** | The gate paragraph names both rows and both reviews and requires them to be in PLAN §10, reviewed and pushed. It records that the author passed on an earlier template (at `009d859a`, without the anchor criterion). The message now opens "This supersedes the earlier message that named `009d859a`." Whether the earlier message was actually forwarded is the integrator's statement and cannot be checked in git. Either way the wording is safe. |
| 5 (note part) | **FIXED** | New "Notes for later tasks" section. **M4:** accurate. `git grep "template_repair\|chat-template-file"` finds nothing in `r1/scripts/c3_label_sweep.py` or `r1/scripts/llama_server_instance.py` at `fe193b3b`, and still nothing at `869e3b48`. "Record its sha in the manifest" goes slightly beyond the author's words, but it is a fair way to implement "SHA 固定" in a task note, not a PLAN row. **M2:** accurate; the test target `r1.exam.runtime.template_repair_args` is the function that `ExamRunner._server` calls for every phase. "Briefed on requirement (1)" is the integrator's statement: `MAC_LOCAL_RUNBOOK_20261104.md` §M2 is unchanged, so the brief lives outside git. That is acceptable for a note. **M8:** accurate. |

**"Supersedes" line.** The PLAN recorder's note "Requirement (1) supersedes the "M1-only" wording in R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED (…); that row stays as history" is unchanged and still correct; PLAN line 717 still holds "M1-only". The new "This supersedes the earlier message…" sentence in the operator message is also correct (see finding 4).

**R-1 MINOR (new, fix before sending) — the rewritten operator message still says `docs/runbooks-04nov` @ `0abfaf2b`.** `869e3b48` rewrote the message line but kept "It integrates coordinator `10742f85`, `docs/runbooks-04nov` @ `0abfaf2b`, …". Its own parent already integrates `docs/runbooks-04nov` @ `8e455234` (`210aa99e`) and `docs/repo-tidy-20261104` @ `d413dc81` (`316ba2a5`). Once `<commit>` is filled with the pushed head, the message misstates what that head contains. This is the same class as 3.4 in `MAC_RULING_ROW_REVIEW_20261104.md`. The practical effect is small: `git diff 009d859a 316ba2a5 -- docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md docs/r1/RUNBOOK.md` is empty, and runbooks 0abfaf2b..8e455234 changes only the HoreKa scan prompt and its review. **Fix:** write `docs/runbooks-04nov` @ `8e455234` and add `docs/repo-tidy-20261104` @ `d413dc81` (branch inventory, prompts index), or replace the list with "see the packet header". The packet header itself (line 5, still "later `0abfaf2b`") belongs to the separate review of `210aa99e`.
