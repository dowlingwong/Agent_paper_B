# PLAN §10 row draft — `R1-EXAM-B2-INVALID-TRIALS` (for the author's signature; 14 November 2026; rev 2)

**AI-assisted (Claude, Mac agent). A draft for the author; it governs nothing until the author commits it in PLAN
§10.**

Rev 2 answers review round 1 (`REVIEW_INVALID_round1.md`):
- B1: the first cell is now the bare ID.
- B2: the STOP list uses the B1 row's catch-all wording.
- B3: the worker-guard STOP is no longer narrowed in the Chinese text.
- N1–N5 are addressed.

**Sources.**
- PLAN §10 at the `_d` run HEAD `7912b7ff`: `R1-EXAM-B1-TRUNCATION-INVALID` (11 Nov, l. 1141) and
  `R1-EXAM-B1-MODEL-OUTPUT-INVALID` (13 Nov, l. 1147).
- The B2 hand-off draft `proposals/B2_HANDOFF_DRAFT_20261114.md` §6 (`mac-b2-handoff-20261114` @ `2120956c`).
- The diagnosis `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` §3 (M1–M21) and §4.1.

## Format the B2 author gate requires (`r1/exam/runtime.py::_b2_author_rows` / `_dated_author_decisions`, B2 code unit, under review)

- The row sits in PLAN **§10** in a **two-column table**: a header line, a separator line (`|---|---|`) and the row,
  each on **one line**. A blank line or a line break inside the table ends it.
- The table is under a `### ` heading that contains the word **author** and a date written either with the **full
  month name** (`14 November 2026`) or in ISO form (`2026-11-14`). `14 Nov 2026` is not recognised.
- The first cell is exactly **`R1-EXAM-B2-INVALID-TRIALS`**: no date, no suffix. No cell contains `|`.
- **Only one row in §10 may carry this ID.** So paste **either** the Chinese block **or** the English block, not
  both.
- The decision cell names both **`R1-EXAM-B1-TRUNCATION-INVALID`** and **`R1-EXAM-B1-MODEL-OUTPUT-INVALID`**, in
  ASCII.

## What carries over, and what does not

**Carried over unchanged:** the invalid-trial and STOP rules of the two B1 rows.

- **Truncation (M2).** A proposer reply cut short (finish reason `length` or `content_filter`, raised by the SDK or
  returned) is an invalid trial:
  - its text is discarded;
  - it is recorded as `parse_failed` / `PROPOSAL_PRECONDITION_FAILED`, with no worker run;
  - it is charged its LLM call;
  - the campaign continues.

  Every **proposer** call carries `max_completion_tokens = 16384`. The A4 observer call is **not** capped by this rule
  (it keeps `max_tokens` 4096).
- **M5–M9.** The pre-check runs before execution:
  - a failing proposal is not executed and gets no observer call;
  - its LLM call is charged;
  - it is recorded as `b1_model_output_rejected`;
  - the check is skipped for D25-revised and harness-rejected proposals;
  - a rejection is final.
- **M19 and M20.**
  - M19 after trial 1 and M20 are invalid trials, each **charged its LLM call**.
  - M19 at trial 1 is a STOP.
- **Journal.** Every **proposer call** is journalled to `b1_proposals.jsonl` before its proposal is returned, so
  before any execution. The journal is validated against the ledger and events.
- **Still a STOP:**
  - any proposal that **reaches** the worker guard and fails it (an internal inconsistency, i.e. a code bug);
  - M10, M15, M16, M18, M19 at trial 1, and M21;
  - M17 (for B2 this includes the ten final-Y seeds 9201–9210) and an incomplete final-Y audit;
  - missing `cache_prompt` evidence;
  - an existing production root found on restart;
  - **all infrastructure, authority and other checks** (the B1 row's wording).
- **M14** executes as in B1.

**Not carried over** (B1-run-specific clauses of the two rows):
- the facts of the stopped runs;
- the cap condition against `fffa_20261111_b`;
- the `paper_commit` re-pins;
- the restart hand-offs `_c` and `_d`;
- the reuse assessment;
- the marker retirements;
- the B1 seeds, nodes, budgets and instance counts.

B2's seeds, budgets, nodes and instances are set by their own bindings (B2 config, authorization note,
`R1-EXAM-B2-POWER-PLAN`).

**Reporting.** The B2 report gives the truncated, rejected and context/encoding invalid trials per candidate, mode
and check.

**Open author questions** of diagnosis §5 carry over unchanged:
- M15: the observer timeout, 60 s at `7912b7ff`; a 180 s standby patch is reviewed only;
- M17: the audit-seed failure;
- M14: the declared ranges.

## Ready to paste — Chinese (one heading line plus three table lines; use either this block or the English one)

```
### 14 November 2026 — B2 invalid trials (author)

| ID | Decision |
|---|---|
| R1-EXAM-B2-INVALID-TRIALS | **R1-EXAM-B1-TRUNCATION-INVALID 与 R1-EXAM-B1-MODEL-OUTPUT-INVALID 中关于无效试验和 STOP 的规则原样延伸到 Stage B2。** 记为无效试验并计入 LLM 预算的情形：截断的提议回复（finish reason 为 `length` 或 `content_filter`）；执行前预检查发现的模型输出问题 M5–M9（不执行，也不调用 observer）；第 1 次试验之后的 M19；M20。每次提议调用设 `max_completion_tokens = 16384`；A4 observer 调用不受此上限约束（仍为 `max_tokens` 4096）。每次提议调用都在提议返回之前（即执行之前）写入 journal（`b1_proposals.jsonl`），并与 ledger 和事件核对。以下情形仍然 STOP：任何到达 worker guard 并未通过的提议（内部不一致，即代码 bug）；M10、M15、M16、M18、M21；第 1 次试验的 M19；M17（B2 包括最终 Y 的十个种子 9201–9210）以及不完整的最终 Y 审计；缺少 `cache_prompt` 证据；重启时发现已有生产根；所有基础设施、授权及其他检查。M14 照 B1 执行。两条 B1 行中只适用于 B1 运行的条款（已停止运行的事实、对 `fffa_20261111_b` 的上限条件、re-pin、重启交接、复用评估、marker 退役，以及 B1 的种子、节点、预算和实例数）不延伸；B2 的种子、预算、节点和实例数由各自的绑定确定。B2 报告按候选模型、模式和检查项列出各类无效试验的计数。本行记录作者 11 月 14 日的指示。 |
```

## Ready to paste — English (one heading line plus three table lines; use either this block or the Chinese one)

```
### 14 November 2026 — B2 invalid trials (author)

| ID | Decision |
|---|---|
| R1-EXAM-B2-INVALID-TRIALS | **The invalid-trial and STOP rules of R1-EXAM-B1-TRUNCATION-INVALID and R1-EXAM-B1-MODEL-OUTPUT-INVALID extend unchanged to Stage B2.** The following are invalid trials, each charged its LLM call: a truncated proposer reply (finish reason `length` or `content_filter`); a model-output fault M5–M9 found by the pre-check before execution (not executed, no observer call); M19 after trial 1; and M20. Every proposer call carries `max_completion_tokens = 16384`; the A4 observer call is not capped by this rule (it keeps `max_tokens` 4096). Every proposer call is journalled (`b1_proposals.jsonl`) before its proposal is returned, so before any execution, and the journal is validated against the ledger and events. The following remain STOPs: any proposal that reaches the worker guard and fails it (an internal inconsistency, i.e. a code bug); M10, M15, M16, M18 and M21; M19 at trial 1; M17 (for B2 including the ten final-Y seeds 9201–9210) and an incomplete final-Y audit; missing `cache_prompt` evidence; an existing production root on restart; and all infrastructure, authority and other checks. M14 executes as in B1. The B1-run-specific clauses of the two B1 rows are not extended: the facts of the stopped runs, the cap condition against `fffa_20261111_b`, the re-pins, the restart hand-offs, the reuse assessment, the marker retirements, and B1's seeds, nodes, budgets and instance counts. B2's seeds, budgets, nodes and instances are set by their own bindings. The B2 report gives the invalid-trial counts per candidate, mode and check. Records the author's instruction of 14 Nov. |
```

The heading date stands for the day the author commits the row. Any date in either accepted form works. Both rows can
share one heading and one table, as two rows under one header; each ID must still appear in only one row.
