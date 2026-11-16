# Review: HoreKa runbook integration, R1-HOREKA-RUNBOOK, M10 pointer and R1-HOREKA-AGENT-SUBMIT (4 Nov 2026)

**Reviewer:** a fresh, independent reviewer (Claude). I did not write any of this work. AI-assisted.
**Scope:** `5c1d3f80..33988105` on `mac-int-20261104`, four commits:
- `2b48f4d9`: integrates `docs/runbooks-04nov` `8e455234..c55e2461`
- `44b4d75a`: PLAN §10 row R1-HOREKA-RUNBOOK
- `14a7c986`: Mac runbook M10 HoreKa paragraph
- `33988105`: PLAN §10 row R1-HOREKA-AGENT-SUBMIT (added to the scope by the coordinator)

**Method.** I checked git objects only (`git show`, `git diff`, `git ls-tree`, blob ids), plus `r1/scripts/plan_row_check.py`. I ran no servers, LLMs or GPU jobs. I modified nothing except this untracked file.

**Sources of the author's words.**
- 18:00 (from the coordinator, verbatim): "HoreKa runbook：我采纳 … 开始写 §3 的代码（`hk2_submit.py` 和 `hk2_status.py` 优先，因为 HK1 需要它们）。"
- 18:06 (from the coordinator, verbatim): "HoreKa 正式作业提交：我裁定（4 Nov 18:00）"agent 可以从 agent 节点提交 GPU 作业，包括续作业，同时等 NHR 回复。" … 交新 reviewer 审。"

## Verdict: **not accepted**

There is one MAJOR finding, in `33988105` (MAJOR-1); MINOR findings are numbered 2–8. The recorder's note does not say clearly whether the ruling covers J3 inside GPU batch jobs (NHR question (c)). It states the recorder's inference as fact. `2b48f4d9`, `44b4d75a` and `14a7c986` have no BLOCKING or MAJOR findings. On their own they would be acceptable once the MINOR findings below are fixed or answered.

---

## Check 1 — `2b48f4d9` (integration of `8e455234..c55e2461`)

**Commits in the range** (linear, each a single-parent child of the previous one; `8e455234` is the parent of `72c81f73`):

| Commit | Paths |
|---|---|
| `72c81f73` scan report | A `docs/r1/reports/HOREKA_SCAN_20261104.md`, A `docs/r1/reports/horeka_scan_20261104/probe_out.txt`, A `docs/r1/reports/horeka_scan_20261104/query_scan.txt` |
| `754c575b` queue-probe prompt | A `docs/r1/prompts/HOREKA_QUEUE_PROBE_PROMPT_20261104.md` |
| `0e13a9fc` runbook rev 1 | A `docs/r1/prompts/HOREKA_RUNBOOK_20261104.md` |
| `fbb33c15` runbook rev 2 | M runbook; A `docs/r1/reviews/HOREKA_RUNBOOK_REVIEW_20261104.md` |
| `ea8757eb` runbook rev 3 | M runbook, M review |
| `c55e2461` rev 3 accepted | M runbook, M review |

**Net range** (`git diff --name-status 8e455234 c55e2461`): six paths, all `A`. There are no modifications or deletions of files that already existed at `8e455234`.

**In `2b48f4d9`:** `git diff --name-status 5c1d3f80 2b48f4d9` shows exactly the same six paths, all `A` (create mode 100644). For every path the blob id at `2b48f4d9` equals the blob id at `c55e2461`:
- `HOREKA_QUEUE_PROBE_PROMPT` `fc14639f`
- `HOREKA_RUNBOOK` `dfd68857`
- `HOREKA_SCAN` `3b8edf5f`
- `probe_out.txt` `0f65184b`
- `query_scan.txt` `13b3b00f`
- `HOREKA_RUNBOOK_REVIEW` `14842342`

None of them existed at `5c1d3f80`. The commit has one parent (`5c1d3f80`). This is a file-copy integration, like the earlier `210aa99e` (`0abfaf2b..8e455234`), and not a git merge. The commit message is accurate. `origin/docs/runbooks-04nov` resolves to `c55e2461`.

**Result: pass.**

## Check 2 — `44b4d75a` (R1-HOREKA-RUNBOOK)

**Placement.** `git diff --stat 2b48f4d9 44b4d75a` shows only `docs/r1/PLAN.md`, +18 lines. The new subsection sits after R1-EXAM-STAGEA-ACCEPT (17:54) and immediately before `## 11. Relation to Paper A`, inside §10. No other line changed. **Pass.**

**Context line.** The four 17:12 quotations ("批准第 1 步的排队实测"; "400GPU小时没问题"; "11月12开始太晚了"; "写 HoreKa 执行 runbook") are byte-identical to runbook §8 at `c55e2461`. The added 18:00 instruction sentence ("请按 runbook §8 记成 … 交新 reviewer 审。") is a verbatim substring of his message. **Pass.**

**Decision cell.** The cell runs from "我采纳 `prompts/HOREKA_RUNBOOK_20261104.md` rev 3" to "作为 HoreKa agent 的执行 runbook。". I verified it as a byte-exact substring of the 18:00 message. Only the topic label "HoreKa runbook：" is dropped. "这段话", read together with "其余写进 consequences", means the adopting sentence and not the whole message. The cell therefore uses the right part. The time is in the column header "(4 Nov 2026, 18:00)", as in the neighbouring rows, which satisfies §8's "with the time". **Pass.**

**Consequences against runbook §8.**
- *(proposed)* governs bullet: verbatim, except that "(the revision as accepted)" becomes "(rev 3, as accepted at `c55e2461`)". This is a correct specialisation.
- "Rows this amends or settles": all four sub-bullets are verbatim. "§7 item 1" becomes "the runbook's §7 item 1".
- *(open)* §7 items 1–9: label kept, with a summary added (see MINOR-3 and MINOR-4).
- The M10-pointer bullet is attributed "(author, 18:00)". It carries his M10 and §3-code instruction, which is what he said.
- The heading "Consequences noted by the recording agent (not part of the decision)" matches §8.
- Nothing else is added. **Pass.**

**Summary of §7 items 1–9.** Checked against runbook §7 at `c55e2461`, lines 501–515. Items 1, 2, 4, 5, 6, 7 and 8 are accurate. On item 3, see MINOR-3. On item 9, see MINOR-4.

## Check 3 — `14a7c986` (Mac runbook M10)

- `git diff --stat 44b4d75a 14a7c986` shows one file, 1+/1−. A line-by-line comparison (526 lines in both versions) shows only line 416, the M10 "4 Nov" paragraph, differs. Nothing else in the Mac runbook changed. **Pass.**
- The old paragraph survives byte-identical after "*Superseded text, kept for history:*". I checked that the new line ends with the old line minus its leading `**4 Nov`. **Pass.**
- **Items against HoreKa runbook §3:**

  | M10 paragraph | HoreKa runbook §3 |
  |---|---|
  | `hk2_submit.py` | item 1 |
  | `hk2_status.py` | item 2 |
  | `slurm` host mode | item 3 |
  | GPU slot allocator | item 4 |
  | resumable units with sharded audits | item 5 |
  | evidence/engineering split | item 6 |
  | templates J0–J5 | item 7 |

  All seven items are present and in order. "reviewed before use" matches the §3 heading. "HK1 needs them" matches HK1's **Needs** line ("`hk2_submit.py` and `hk2_status.py` (§3), reviewed"). **Pass.**
- On the "items that touch files another task owns … wait" sentence, see MINOR-5.

## Check 4 — `plan_row_check.py`

- `--result 14a7c986` with the seven sources: every source has all items present byte-identical. **MISSING total: 0.**
- I re-ran the check with `--result 33988105`: **MISSING total: 0.**
- Two `EDITED-BY` / `SUPERSEDED-IN` notes, both on the "Historical index" line, predate this range (`c55e2461`, `f52db28e`) and are kept in the result. **Pass.**

## Additional scope — `33988105` (R1-HOREKA-AGENT-SUBMIT)

- **Placement.** `git diff --stat 14a7c986 33988105` shows only `docs/r1/PLAN.md`, +16 lines. The new subsection sits immediately before `## 11`, after R1-HOREKA-RUNBOOK. **Pass.**
- **Decision cell.** "agent 可以从 agent 节点提交 GPU 作业，包括续作业，同时等 NHR 回复。" is a byte-exact substring of the 18:06 message, and it is the sentence he called "这句原话". The time is 18:00, as he states his ruling time; the heading uses 18:00 and the context line uses 18:06. **Pass.**
- **Context line.** It is a byte-exact prefix of his message, from "HoreKa 正式作业提交" to "立即 STOP。" (see MINOR-6).
- **Consequences** are labelled "the author's own, from his 18:06 message":
  1. **Settles R1-T1-HOREKA's (open) item and is the §7 item 1 ruling.** These are his words. The English excerpt "until NHR@KIT answers … the author submits production jobs" is a fair elision of R1-T1-HOREKA's text.
  2. **The §0.3 interim rule lapses.** These are his words, including his parenthetical.
  3. **NHR reply ⇒ immediate STOP under §5.** These are his words. It matches §5's second bullet at `c55e2461` ("Any reply from NHR@KIT that restricts agent submission or LLM loops in batch jobs").
  4. **The `hk2_submit.py` refusal is conditioned on this row.** These are his words.

  Nothing beyond what he said is in the consequences. **Pass.**
- **Recorder's note.** It is labelled "(not the author's words)". See MAJOR-1, MINOR-7 and MINOR-8.

---

## Findings

### BLOCKING
None.

### MAJOR

**MAJOR-1. `33988105` — the recorder's note implies, without stating it, that the ruling covers J3 inside GPU batch jobs (NHR question (c)), and it states that inference as fact.**

*Evidence.* Runbook §7 item 1 (ii) at `c55e2461` has two parts:
- "the HoreKa agent submits production jobs from the `agent` node (continuations included)"
- "J3 runs inside GPU batch jobs, pending NHR@KIT's answer"

§0.3 frames question (c) separately: "does an LLM proposer loop inside a GPU batch job count as an 'AI agent workload'?". §6 says "The NHR@KIT question (c) stays open (§0.3, §7 item 1)".

The author's sentence names only submission from the agent node and continuations. The note says so correctly. It then says: "his STOP condition on "LLM 循环 in 批作业" refers to the J3 part". That is stated as fact, not as the recorder's reading. The note never says whether the J3 part of (ii), and so question (c), is now ruled or still open.

A reader, including the HoreKa agent at HK4b, HK5 and HK6 (all J3), is left to infer authorisation from a STOP clause. This is the policy-sensitive item behind the runbook's own round-1 BLOCKING-1.

*Fix.* Reword the note so that it flags the reading rather than asserting it. Something like: "Whether the ruling also covers option (ii)'s second part, J3 (the LLM proposer loop) inside GPU batch jobs, NHR question (c), is not stated in his sentence. The recorder reads his STOP condition on '批作业里的 LLM 循环' as contemplating it. **For the author to confirm**; until then question (c) is treated as open (§0.3, §6)." The author could also simply be asked one line in chat. Note that he said "其余写进 consequences" only for the earlier row. This row's consequences must stay limited to his words, so the clarification belongs in the note or in an author answer.

### MINOR

**MINOR-2. `44b4d75a` — the commit message describes the decision cell as "his 18:00 paragraph verbatim".** The cell is the adopting sentence only, which is correct (Check 2). The message is imprecise. It needs no rewrite of history; I note it so later readers do not take the cell to be the whole message.

**MINOR-3. `44b4d75a` — the summary of §7 item 3 omits half of it.** Runbook §7 item 3 is "F, C and D (20 Nov 12:00, 20 Nov 20:00, 21 Nov 18:00), and your availability for sessions on 20–21 Nov". The row says only "F, C and D".

*Fix.* Add "with the proposed times, and his availability on 20–21 Nov". Alternatively, state that the parenthesis gives short labels and not the full items.

**MINOR-4. `44b4d75a` — "PLAN item H1" is ambiguous inside PLAN.** In PLAN, "H1" is also the hybrid arm (§3 C3, line 75; §5, line 137; §7, line 215). The runbook defines "PLAN item H1" (line 30) as the pending B.7-date and partial-T1-fallback decision. That is H1 of the 11:29 recommendations (PLAN line 767: "H1 (the B.7 timing and its partial-T1 fallback)"). The row gives no gloss.

*Fix.* Write "PLAN item H1 (the B.7 timing and its partial-T1 fallback)".

**MINOR-5. `14a7c986` — the "items that touch files another task owns … wait until that task's branch is merged" sentence reads as part of the author's 18:00 instruction.** It sits inside the paragraph headed "4 Nov (18:00, R1-HOREKA-RUNBOOK)" with no attribution. It is the Mac agent's own scheduling:
- The author said nothing about it.
- HoreKa runbook §3 has no such condition.
- §4 schedules all "§3 code" for 4–6 Nov.

It does not contradict §3, because it does not drop any item. It is consistent with the Mac runbook's Separation rule: "Shared files go to one worker only, and the others wait", which names `r1/scripts/c3_label_sweep.py`. `r1/c3/audit.py` carries code on `codex/b2-repair-20261031`, which M3 continues. However, "until that task's branch is merged" is stricter than "no two workers edit the same file at the same time". It also does not name the task (M3, and M4 for `c3_label_sweep.py`). It can delay §3 items 3 and 5, which HK3 and later need, beyond the §4 estimate.

*Fix.* Mark the sentence as the Mac agent's scheduling note, cite Mac runbook §0 "Separation" and §2 "Order", and name the owning task(s). Optionally say that the HK3+ schedule risk is reported to the author.

**MINOR-6. `33988105` — the context-line quotation is truncated without a mark and has ambiguous nested quotation marks.**
- The quoted 18:06 text stops at "立即 STOP。", although his message continues: "另外在 M10 的 `hk2_submit.py` 里，… 改成以这一行为条件。交新 reviewer 审。". The omitted part is paraphrased in consequence 4, but the quotation does not show that it was cut.
- His own ASCII quotation marks around the ruling sit inside the outer ASCII quotation marks, so the outer quote appears to close after "我裁定（4 Nov 18:00）".

*Fix.*
- Either quote the full message, or end the quotation with "…" and point to consequence 4.
- Render his inner quotation marks distinguishably, for example as 「…」 with a note, or quote the outer passage in a blockquote. Keep the verbatim decision cell as it is.

**MINOR-7. `33988105` — the recorder's note misattributes and misquotes.**
- (a) "HoreKa runbook §0.3's other rules stay (dev-QoS limits, never touching another user's jobs, no inherited recovery authorization)". The dev-QoS limits are not in §0.3. They are in §0.1 (the `dev-cpu`/`dev-gpu-h100` row), §1 "Continuations" (line 265: never from a dev partition) and §3 item 1's refusals (lines 422–423). §0.3 holds the other two rules, plus Pins, Run labels, Seeds and so on.
- (b) The note says the "§0.3 interim rule" lapses, but it does not say what happens to the interim block's other two sub-bullets:
  - "You submit only jobs in `dev-cpu`, `dev-gpu-h100` and `cpu`"
  - "No job submits its own continuation"

  Under "包括续作业" both evidently lapse. Continuations then fall under §1 line 265 ("only after the author's ruling in §7 item 1, never from a dev partition …, and only through `hk2_submit.py` with all its guards").
- (c) The phrase in quotation marks, "LLM 循环 in 批作业", is not his wording. He wrote "批作业里的 LLM 循环".

*Fix.* Correct the section references. Say that the interim block's other sub-bullets lapse with it, and that §1's continuation conditions and §3 item 1's dev refusals still apply. Quote "批作业里的 LLM 循环" exactly.

**MINOR-8. `33988105` — the `hk2_submit.py` condition covers only half of the refusal it modifies.** Runbook §3 item 1's last refusal is: "until the §7 item 1 ruling: any `gpu-*` submission without `--author`, **and any submission from inside a job**." The author asked to condition the first half on this row. That is recorded faithfully in consequence 4, and it must stay his words. Under "包括续作业", however, continuations are submissions from inside a job. If only the `--author` half is conditioned, M10 code would still refuse continuations, which contradicts the decision cell.

The runbook's own text ties both halves to the §7 item 1 ruling. The recorder's note should therefore say: "The same §3 item 1 clause also refuses any submission from inside a job until the §7 item 1 ruling. Under 'including continuations' that half lifts as well, except from dev partitions (§3 item 1, line 422). Recorder's reading, for the M10 reviewer and the author."

### Not findings (checked and in order)
- File-copy integration rather than a git merge: consistent with `210aa99e`.
- The R1-BX-PORTING-CONFIRM branch `hk2-trackg-<date>` is reproduced as §8 states it. The runbook's §0.3 marks the branch name itself *(proposed)*, and §8 does not, so the row is faithful to §8.
- The row names (R1-HOREKA-RUNBOOK, R1-HOREKA-AGENT-SUBMIT) are the recording agent's own choices. The first one is the name in the author's 18:00 message.
- The pre-existing untracked file `docs/r1/reviews/MAC_STAGEA_ACCEPT_REVIEW_20261104.md` belongs to another review and was left alone.

## Summary for the author

| Commit | Result |
|---|---|
| `2b48f4d9` | Six files added byte-identical from `c55e2461`; nothing else changed. |
| `44b4d75a` | Decision cell and §8 consequences faithful. Two summary gaps (§7 item 3, the "H1" gloss). |
| `14a7c986` | The pointer to HOREKA_RUNBOOK §3 is accurate. One agent scheduling sentence reads as if it were yours. |
| `33988105` | Decision cell and consequences faithful to your 18:06 words. The recorder's note leaves unclear whether your ruling also covers J3 (the LLM loop) inside GPU batch jobs, which is NHR question (c). This needs a one-line confirmation from you, or a reworded note. |

`plan_row_check`: MISSING 0 at both `14a7c986` and `33988105`.

---

## Re-check: `8537dab3` (fixes for MAJOR-1 and MINOR-3 to MINOR-8)

**Re-check verdict: accepted.** The overall verdict for `5c1d3f80..33988105` together with `8537dab3` is **accepted**.

**Scope.** The parent of `8537dab3` is `c87a277a`. Four commits lie between `33988105` and `8537dab3`: `4e0a00d0`, `f5f29801`, `a52aa7b1` and `c87a277a`. They are under another review and I did not check them. I checked only `8537dab3` against its parent.

| Check | Result | Evidence |
|---|---|---|
| Files touched | Pass | `git diff --stat c87a277a 8537dab3` shows only `docs/r1/PLAN.md` (+8/−3) and `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md` (+1/−1). |
| PLAN hunks | Pass | Three hunks. One is in "4 November 2026 (18:00) — HoreKa agent runbook adopted": the §7 summary bullet. Two are in "4 November 2026 (18:00) — HoreKa production submission": the context line and the recorder's notes. Nothing changed outside these two subsections, and the 18:10 subsection that follows them is untouched. |
| Mac runbook | Pass | Both versions have 526 lines; only line 416 differs. The superseded text after "*Superseded text, kept for history:*" is byte-identical. |
| Decision cells | Pass | The R1-HOREKA-RUNBOOK and R1-HOREKA-AGENT-SUBMIT table lines are byte-identical before and after. |
| `plan_row_check.py --result 8537dab3` (same seven sources) | Pass | MISSING total: 0. The only notes are the existing "Historical index" EDITED-BY / SUPERSEDED-IN notes. |

**The findings, one by one**

- **MAJOR-1: resolved.** The note now:
  - splits §7 item 1 (ii) into two parts. Part (1) is submission from the `agent` node, continuations included. Part (2) is J3 inside GPU batch jobs, which is NHR question (c), citing §0.3.
  - says his sentence names only part (1).
  - calls the reading of "批作业里的 LLM 循环" as covering part (2) "the recorder's reading only".
  - states: "Whether part (2), question (c), is decided stays open until the author confirms."

  This matches runbook §0.3, §6 and §7 item 1 at `c55e2461`. Nothing in the row or its consequences now implies that J3 inside batch jobs is authorised.

- **MINOR-2: answered** in the commit message. The reviewed commits were not rewritten, and I accept that.

- **MINOR-3: resolved.** The summary now gives "F, C and D (proposed 20 Nov 12:00, 20 Nov 20:00, 21 Nov 18:00) and the author's availability for sessions on 20–21 Nov". This matches §7 item 3.

- **MINOR-4: resolved.** The summary now reads "PLAN item H1, i.e. the B.7 timing and its partial-T1 fallback (not the hybrid arm H1 of D.2), after HK3 and HK5". This matches runbook line 30, §7 item 9, and PLAN line 767. NIT, no action required: the hybrid arm is defined in PLAN §5 ("Hybrid H1"); RUNBOOK D.2 lists H1–H5 as contrasts. Either reference is understandable.

- **MINOR-5: resolved.** The sentence is now labelled "*(Mac agent's scheduling, not an author instruction:)*". It names §3 items 3 and 5, the two files, and M3, and it says a spec is written in the meantime. That M3 owns the work fits Mac runbook M3, which is based on `codex/b2-repair-20261031` (that branch holds the `r1/c3/audit.py` and `c3_label_sweep*` code), and M4 rebases after M3. The sentence no longer contradicts §3.

- **MINOR-6: resolved.** The context line now gives the whole 18:06 message as a blockquote, labelled "the whole message, verbatim". It is byte-identical to the message the coordinator relayed. His inner quotation marks no longer collide with outer ones.

- **MINOR-7: resolved.** The note now:
  - lists all three interim rules of the §0.3 block "Until the author rules on this (§7 item 1)" correctly: dev/cpu-only submission, `gpu-*` jobs submitted by the author with `--author`, and no self-continuation. It says the ruling lifts them for submission and continuations.
  - keeps "Never touch what you did not start".
  - places the dev-QoS limits in §0.1, §1 and §3 item 1.
  - quotes "批作业里的 LLM 循环" exactly.

- **MINOR-8: resolved.** The note says that §3 item 1 ties two refusals to the ruling. It quotes both correctly. It says "包括续作业" implies the second refusal too, and it flags this for the M10 reviewer. It is kept in the recorder's notes, so the consequences remain limited to the author's own words.

**No new findings.**
