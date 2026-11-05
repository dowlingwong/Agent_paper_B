# Prompt — Mac-local agent, overnight hands-off run (5 Nov 2026, from about 01:00 CET)

**Written 5 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.** The author's words: "让它继续，高质量完成，不要停下，我会去睡觉，handsoff". Paste everything below the line into the Mac-local agent.

---

The author is asleep until about 08:00 CET and will not answer. **Keep working the whole time; do not stop to wait for him.**
- When something needs his decision, write it down (§4) and move to the next item.
- Do not end your turn while useful work remains.
- At about 07:30 CET, write the morning report (§4).

## 1. Unchanged hard limits

- No server access, no experiment, no model run, no GPU.
- **No author decisions.** Never write a decision cell for him, and never treat silence or elapsed time as a decision.
- Never push `main`, `r1` or `exam-x-*`; never force-push; never delete anything (retire into `_to_delete/`).
- Every unit is accepted only by a fresh independent reviewer. You never accept your own work or your workers' work.
- At most 3 worker subagents, each in its own worktree and branch. Only you integrate.

## 2. Quality rules for tonight

The safety findings so far are good: the prose-mention gap in the authorization gate was a real catch. But by 01:00, nothing on the critical path has been accepted after about seven hours. Tonight the goal is **accepted, minimal, working units**, not further conditional designs.

- **Minimal first.** Implement the simplest version that meets the requirement as the runbook and PLAN state it. Write a new design document only if a requirement truly cannot be met otherwise.
- **No open-ended gates.** A fail-closed gate is right. But each STOP you add or keep must be listed with three things: what unblocks it, who must act, and the effort.
  - "Pending a trust root" or "pending further design" is not an acceptable final state for anything on the B1 path.
  - If a stronger guarantee is desirable but not required, implement the required version now. Put the stronger one in the author's question list as an *(open)* option.
- **Finish before you start.** Prefer taking one item to ACCEPTED over opening three.
- **Time-box.** If an item has gone through 3 review rounds, or about 2 hours, without acceptance, record the blocker precisely (§4) and move to the next item. Come back later if time allows.
- **Commit and push** each accepted unit at once. Keep STATUS entries short: what was accepted, the commit, and what remains.

## 3. Work, in priority order

### Priority 1 — B1 ready for the author's signature by morning

B1 leads to X.7, and X.7 gates the HoreKa T1 work and sweep 2. The target: in the morning the author says one line, and B1 can start.

**(a) M2 / `x5_rule_v2`: freeze it.**
- The author answered both open questions at 20:38:
  - R1-EXAM-X5-B1-SENSITIVITY: "保留描述性检查";
  - R1-EXAM-X5-D28-SCOPE: "只用 thinking-off 作门槛".
- Apply exactly these to the rule and the code, with tests.
- Compute the **final** rule sha.
- Take M2 to ACCEPTED, scoped to what B1 needs. B2 ranking may stay STOP, provided it is outside B1's path and its STOP entry is complete (§2).

**(b) The B1 authorization gate (the X5 v2 authority STOP).**
- Implement the minimal verifier consistent with the existing reviewed design: `runtime.author_gate` reads the authorization note and PLAN from the **host checkout's committed HEAD**.
- Required behaviour:
  - Parse PLAN §10 **table rows strictly**: the first cell is exactly the required row id, the decision cell is non-empty, and the row sits under a dated author subsection. Never match prose.
  - The note file exists, with every required field: `author`, `phase`, `approved: true`, `rule_sha256`, `nodes`, the Stage A table sha256 values, `llm_call_cap`.
  - Every sha binding matches the files on disk.
  - The working tree is clean, and HEAD is recorded in the manifest.
- Write the residual risk in one paragraph: anyone with write access to the repository could add such a row, and that is mitigated by process (independent review and the author's instruction). Put any stronger provenance scheme, such as signatures or a trusted publishing root, in the author's question list as an *(open)* option. It does not block B1.
- Independent review to ACCEPTED.

**(c) The B1 authorization note: final draft.**
- Bind the values the author chose (R1-EXAM-B1-DRAFT-VALUES, "按照建议决定"): the digits node, `llm_call_cap` 80, `workers` 20.
- Also bind the final rule sha from (a) and both Stage A table sha256 values.
- Propose one concrete format for `stage_a_amendment_acceptance_sha256`. The format choice goes in the question list.
- Review to ACCEPTED.
- Then prepare, without committing either as a decision:
  - the text of row R1-EXAM-RULE-X5V2, with an empty decision cell for the author's words;
  - operator message v3: B1 on TASL-7 at the reviewed SHA, with the TASL-7 handover steps of operator runbook O2.

**(d) The 39 failing tests.**
- Classify every one: environmental (state why), pre-existing defect outside the B1 path, or **on the B1 path**.
- Fix those on the B1 path.
- For the rest, draft a test-exceptions row for the author: the list, the reasons, and an empty decision cell.
- Include the classification in the M2 review.

### Priority 2 — M10: ready for HK1

- Implement the real submission path of `hk2_submit.py` and `hk2_status.py`. Follow HoreKa runbook §3 items 1–2 and the author's rows:
  - R1-HOREKA-AGENT-SUBMIT;
  - R1-HOREKA-UNIFIED-SUBMISSION ("采用统一提交与等待记账").
- Requirements:
  - standard library only, Python 3.9;
  - every refusal in §3 item 1;
  - the budget guard, with "wait for accounting" semantics;
  - F/C/D;
  - a scrubbed environment.
- Tests run against a fake `sbatch`/`squeue`/`sacct`.
- Keep real submission switched off by **one** explicit configuration switch, which the HoreKa agent turns on at HK1 only.
- List any site capability that only HK1 can verify, for example accounting delay or `PrivateData` effects, as an HK1 check, not as a reason to keep the code unfinished.
- Review to ACCEPTED.

### Priority 3 — M3 and M11

- **M3:** the minimal offline enforcement the reviewed proposal requires, with tests against the pinned OpenML loader. Then review. The five out-of-scope files stay with the author.
- **M11:** guards in the existing readers (refuse sweep-2 tables before R1-BX-D8-CONFIRM, and refuse `r1_sealed/`). The synthetic prototype stays synthetic-only.

## 4. Questions and the morning report

**Questions.** Collect every question for the author in `docs/r1/reports/MAC_OVERNIGHT_QUESTIONS_20261105.md`. For each one, give:
- the context in one or two sentences;
- the options;
- your recommendation;
- a paste-ready answer line.

Order them by what they unblock: B1 first.

**Morning report.** At about 07:30 CET, write `docs/r1/reports/MAC_OVERNIGHT_REPORT_20261105.md` and push everything. Then send the author a short Chinese summary:
- what reached ACCEPTED (commits, review files);
- what is ready for his signature (B1 note, R1-EXAM-RULE-X5V2 row text, operator v3), as the exact lines he would send;
- what is still open, with the blocker for each;
- the question list.
