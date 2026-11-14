# PLAN §10 row draft — `R1-EXAM-B2-INVALID-TRIALS` (for the author's signature; 14 November 2026)

**AI-assisted (Claude, Mac agent). A draft for the author; it governs nothing until the author commits it in PLAN
§10 under a dated author heading.** The B2 code unit's author gate requires a dated author §10 row
`R1-EXAM-B2-INVALID-TRIALS`.

**Sources.**
- PLAN §10 at the `_d` run HEAD `7912b7ff`: `R1-EXAM-B1-TRUNCATION-INVALID` (11 Nov, l. 1141) and
  `R1-EXAM-B1-MODEL-OUTPUT-INVALID` (13 Nov, l. 1147).
- The B2 hand-off draft `proposals/B2_HANDOFF_DRAFT_20261114.md` §6 (`mac-b2-handoff-20261114` @ `2120956c`).
- The diagnosis `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` §3 (M1–M21).

## What is carried over unchanged

**From `R1-EXAM-B1-TRUNCATION-INVALID`:**
- A proposer reply cut short (finish reason `length` or `content_filter`, raised by the SDK or returned) is an
  **invalid proposal**:
  - its text is discarded even if part of it would parse;
  - it is recorded as an invalid trial (`parse_failed`, `PROPOSAL_PRECONDITION_FAILED`, no worker run);
  - it is **charged to the LLM-call budget**;
  - the campaign continues.
- Its `llm_call` record carries `truncated`, `finish_reason`, `max_completion_tokens` and the discarded character
  counts.
- Every proposer call carries **`max_completion_tokens = 16384`**.
- Every other LLM-call failure stays a STOP.
- The A4 observer call is not capped by the row.

**From `R1-EXAM-B1-MODEL-OUTPUT-INVALID`:**
- **Pre-check before execution.** Before the control plane can call the worker, each proposal headed for execution
  is checked against the worker guard's model-output conditions (M5–M9):
  - directive missing;
  - directive symbol not editable, or different;
  - old or new value different;
  - backslash in a value;
  - `.py` value too long, not a literal, or not a finite number.

  A failing proposal is not executed. It becomes an invalid trial (`PROPOSAL_PRECONDITION_FAILED`, no worker run, no
  observer call), is charged its LLM call, and is recorded as `b1_model_output_rejected` with the edit and the reason.
  The check is skipped for proposals the harness revises (D25 inactive key) or rejects itself. A rejection is final.
- **Context and encoding.** A prompt beyond the context is an invalid trial **after trial 1**; at trial 1 it is a
  STOP (M19). A reply whose summary would make later requests unencodable is discarded as an invalid trial (M20).
- **Journal first.** Every proposer call is journalled to `b1_proposals.jsonl` **before** the proposal is returned.
  The journal is validated against the ledger and events in the root manifest and in the batch verification.
- **Still a STOP:**
  - a proposal that reaches the worker guard and fails it (an internal inconsistency, i.e. a code bug);
  - M10 (edit path ≠ editable file);
  - M16 (replay failure of an executed edit);
  - M17 (an executed configuration fails or is non-finite on an audit seed; **for B2 this includes any of the ten
    final-Y seeds 9201–9210**, and an incomplete final-Y audit);
  - M15 (observer timeout or transport failure);
  - M18 (LLM transport failure);
  - M21 (12 h root deadline);
  - all infrastructure, authority, pin, sha and host checks;
  - missing `cache_prompt` evidence;
  - any existing production root found on restart.
- M14 (out-of-declared-range `digits_mlp` value) executes as in B1.

**Unchanged:** harness pin `a3fedbb`, prompts, schema, temperature, context, thinking policy, `--reasoning-budget`
2048, `x5_rule_v2`, and the D28 and diagnostics semantics (a rejected or truncated trial counts under `invalid`; a
truncated one also under `parse_failed`).

**Reporting.** The B2 report gives the truncated, rejected and context or encoding invalid trials per candidate,
mode and check, as the B1 appendix does.

**Not changed by this row:** the open author questions of diagnosis §5 carry into B2 as they stand. These are the
observer timeout (M15; 60 s at `7912b7ff`, a 180 s patch reviewed only as a standby), the audit-seed failure (M17)
and the declared ranges (M14).

## Row text (English, for the table)

| R1-EXAM-B2-INVALID-TRIALS (⟨date⟩) | **R1-EXAM-B1-TRUNCATION-INVALID and R1-EXAM-B1-MODEL-OUTPUT-INVALID extend unchanged to Stage B2.** A truncated proposer reply (finish reason `length`/`content_filter`) is an invalid trial and is charged to the LLM-call budget; every proposer call carries `max_completion_tokens = 16384`. The model-output faults M5–M9 found by the pre-check before execution are invalid trials (not executed, LLM call charged). M19 after trial 1 and M20 are invalid trials. Every proposal is written to the journal (`b1_proposals.jsonl`) before it is returned, and the journal is validated against ledger and events. Still a STOP: a proposal that reaches the worker guard and fails it (a code bug), M10, M15, M16, M17 (for B2 including the ten final-Y seeds 9201–9210 and an incomplete final-Y audit), M18, M19 at trial 1, M21, missing `cache_prompt` evidence, an existing production root on restart, and every pin, sha, authority and host check. M14 executes as in B1. Everything else stays as in the two B1 rows. The B2 report gives the invalid-trial counts per candidate, mode and check. Records the author's instruction of 14 Nov. |

## 可直接粘贴的中文（作者签字用）

> **R1-EXAM-B2-INVALID-TRIALS（⟨日期⟩）：R1-EXAM-B1-TRUNCATION-INVALID 与 R1-EXAM-B1-MODEL-OUTPUT-INVALID 原样延伸到 Stage B2。**
>
> **记为无效试验（计入 LLM 预算）：**
> - 截断的提议回复（finish reason 为 `length` 或 `content_filter`），每次提议调用设 `max_completion_tokens = 16384`；
> - 执行前预检查发现的模型输出问题 M5–M9（不执行）；
> - 第 1 次试验之后的 M19；
> - M20。
>
> **Journal：** 每个提议在返回前写入 journal（`b1_proposals.jsonl`），并与 ledger 和事件核对。
>
> **仍然 STOP：**
> - 通过预检查后在 worker guard 处失败的提议（代码 bug）；
> - M10、M15、M16、M18、M21；
> - M17（B2 包括 9201–9210 十个最终 Y 种子上的失败）和不完整的最终 Y 审计；
> - 第 1 次试验的 M19；
> - 缺少 `cache_prompt` 证据；
> - 重启时发现已有生产根；
> - 所有 pin、sha、授权和主机检查。
>
> **其他：** M14 照 B1 执行；其余与上述两条 B1 行相同。B2 报告按候选、模式和检查项列出各类无效试验的计数。
