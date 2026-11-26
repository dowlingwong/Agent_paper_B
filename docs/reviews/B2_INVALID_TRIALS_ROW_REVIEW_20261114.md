Reviewed base: d1ac667859afced092541dff52c1885c10dd5ff5

# PLAN-row draft R1-EXAM-B2-INVALID-TRIALS — independent review record (14 November 2026)

Branch `mac-b2-plan-20261114`: draft `a0018635`, rev 2 `d1ac6678`. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude), against PLAN l. 1141/1147 at `7912b7ff`, the model-output diagnosis, hand-off §6 and the B1 code. Round 1 (`a0018635`): changes requested (dated first cell fails the gate; the STOP catch-all was narrower than the B1 row; the Chinese narrowed the worker-guard STOP). Round 2 (`d1ac6678`): **accepted**; content carries the two B1 rows over without widening or narrowing, and the paste blocks pass the gate functions. Notes, not blocking: the author should put the commit date in the heading; re-run the gate check if the gate code changes before the code unit is accepted.

Accepted commit (last round): d1ac667859afced092541dff52c1885c10dd5ff5

The round texts are reproduced unchanged below.

---

# Review — PLAN §10 row draft `R1-EXAM-B2-INVALID-TRIALS` (round 1)

Reviewed commit: a0018635ca807e531701f269b815104904a68402
Branch: `mac-b2-plan-20261114` (worktree `/tmp/pb/wt/b2plan`), file
`docs/r1/proposals/PLAN_ROW_R1-EXAM-B2-INVALID-TRIALS_DRAFT_20261114.md`.

Verdict: changes requested

Independent reviewer (AI, Claude), 14 Nov 2026. No worktree was modified; scratch work was kept in `/tmp/rev_inv` and has been removed.

## Sources checked

- `git show 7912b7ff:docs/r1/PLAN.md`: `R1-EXAM-B1-TRUNCATION-INVALID` (l. 1141) and `R1-EXAM-B1-MODEL-OUTPUT-INVALID`
  (l. 1147). Both line numbers in the draft are correct.
- `git show 7912b7ff:docs/r1/reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md`: §3 (M1–M21), §4.1–4.3 and §5.
- `git show 2120956c:docs/r1/proposals/B2_HANDOFF_DRAFT_20261114.md`: §0.4 and §6.
- Code at `7912b7ff`: `r1/exam/b1_proposal_precheck.py`, `b1_llm_truncation.py`, `b1_proposal_journal.py`,
  `b1_proposal_guard.py`, and `campaign.py` l. 306–311 (final-Y audit).
- The B2 author gate. It is **uncommitted** working-tree code in `/tmp/pb/wt/b2code/r1/exam/runtime.py`
  (l. 423–491: `B2_INVALID_TRIALS_ROW`, `_dated_author_decisions` and `_b2_author_rows`). Branch
  `mac-b2-code-20261114` itself is still at `7912b7ff`. I copied the two functions verbatim into a scratch script and
  ran them against synthetic §10 snippets built from the draft row.

## What is correct

Every substantive class matches the two B1 rows, the diagnosis and hand-off §6:

- **Truncation (M2).** The draft gives finish reason `length` or `content_filter`, whether the SDK raises it or the reply
  is returned. The text is discarded. The trial is recorded as `parse_failed` / `PROPOSAL_PRECONDITION_FAILED` with no
  worker run, it is charged, and the campaign continues. The `llm_call` fields and the 16,384 cap match. The A4
  observer is not capped. This agrees with PLAN l. 1141 and with the code: `B1_MAX_COMPLETION_TOKENS = 16384` and
  `TRUNCATING_FINISH_REASONS = {'length','content_filter'}`, at l. 48–50 of `b1_llm_truncation.py`.
- **M5–M9.** The list of conditions matches PLAN l. 1147 item (1), diagnosis §3, hand-off §6 and the `CHECKS` in
  `b1_proposal_precheck.py`. The draft also gets these right:
  - the trial is not executed, has no observer call, and its call is charged;
  - the record is `b1_model_output_rejected`;
  - the check is skipped for D25-revised and harness-rejected proposals;
  - a rejection is final.
- **M19 and M20.** M19 is an invalid trial after trial 1 and a STOP at trial 1. The code agrees:
  `status.budget_index <= 1` raises the STOP. M20 is an invalid trial.
- **Journal.** Proposals are journalled before they are returned and validated against ledger and events, in both the
  manifest and the batch verification. This matches PLAN l. 1147 item (3) and `b1_proposal_journal.py`.
- **Still a STOP.** The draft lists: a proposal that fails at the worker guard, M10, M15, M16, M17, M18, M21, missing
  `cache_prompt` evidence and an existing production root. It also says M14 executes as in B1. All of this matches.
  The B2 addition to M17 (the final-Y seeds 9201–9210, and an incomplete final-Y audit) comes from hand-off §6. It
  restates existing code (`campaign.py` l. 308–309: `run_config(..., stop_on_invalid=True)` and
  `STOP: incomplete final Y audit`), so it does not widen anything.
- **Invalid-trial set.** The draft does not widen it. M1, M3, M4 and M11–M13 stay on their harness paths, and M14
  executes. It does not narrow it either: no B1 invalid class is dropped.
- **No overclaims.** The draft says it "governs nothing until the author commits it in PLAN §10 under a dated author
  heading". Nothing in it sets approval or uses `approved`, and it does not claim adoption.
- **The table row.** The English row has exactly two cells (three `|`). There is no `|` inside a cell, and no
  backtick span contains a `|`. The decision cell names both `R1-EXAM-B1-TRUNCATION-INVALID` and
  `R1-EXAM-B1-MODEL-OUTPUT-INVALID`.

## BLOCKING

### B1. The suggested first cell `R1-EXAM-B2-INVALID-TRIALS (⟨date⟩)` fails the B2 author gate

The draft's table row begins `| R1-EXAM-B2-INVALID-TRIALS (⟨date⟩) |`. This follows the B1 convention, for example
`| R1-EXAM-B1-TRUNCATION-INVALID (11 Nov) |`. But the gate matches the first cell exactly:
`cells[0].strip()!=row_id` → skip (`runtime.py`, in `_dated_author_decisions`).

I ran the gate code on a synthetic §10 with the heading `### 14 November 2026 — B2 rules (author)`, a two-column
table and a minimal valid power-plan row:

| Invalid-trials first cell | `_b2_author_rows(plan, 4)` |
|---|---|
| `R1-EXAM-B2-INVALID-TRIALS (14 Nov)` (draft with the date filled in) | False → `STOP: dated §10 B2 power-plan and invalid-trial author rows required` |
| `R1-EXAM-B2-INVALID-TRIALS (⟨date⟩)` (draft as written) | False |
| `R1-EXAM-B2-INVALID-TRIALS` (bare) | True |

**Fix.** Make the first cell exactly `R1-EXAM-B2-INVALID-TRIALS`. Put the date in the `###` heading only, or inside
the decision cell. Say explicitly in the draft that the first cell must carry no date or suffix.

### B2. The "Still a STOP" check list in the English row and the Chinese text is narrower than the B1 row

The two B1 rows say different things here:

- PLAN l. 1147 item (4) says "…and all infrastructure, authority and other checks".
- Diagnosis §3, last paragraph, names these as not model output and unchanged: "filesystem, preservation and lease
  guards (`b1_node_artifacts`, `b1_editable_preserve`, `b1_worker_artifact_guard`, `b1_state_preserve`,
  `b1_openml_cache_guard`), authority and binding checks, and server start and identity checks".

The draft is inconsistent with itself. Its expanded section, l. 53, says "all infrastructure, authority, pin, sha and
host checks". But the text to be signed lists less:

- The English row says only "every pin, sha, authority and host check".
- The Chinese text says only "所有 pin、sha、授权和主机检查".

That list reads as exhaustive. It leaves out the infrastructure, preservation, lease and server-identity checks, and
the "other checks" catch-all. Hand-off §6 uses similar wording ("any pin, sha, authority or host mismatch"). But this
row's stated purpose is to carry the B1 rows over unchanged, so the B1 row's wording governs. The later sentence
"Everything else stays as in the two B1 rows" softens the gap but does not remove it from the enumerated list.

**Fix.** In both texts, use "every infrastructure, preservation, pin, sha, authority, host and other check", and in the
Chinese "所有基础设施、保全、pin、sha、授权、主机及其他检查", or equivalent.

### B3. The Chinese text narrows the worker-guard STOP

- The Chinese says "通过预检查后在 worker guard 处失败的提议（代码 bug）": a proposal that fails at the worker guard
  **after passing the pre-check**.
- The English row, PLAN l. 1147 item (4) and hand-off §6 say: any proposal that **reaches** the worker guard and fails
  it.

Diagnosis §4.1 describes the case the STOP is for: "A proposal failing the guard at the worker has bypassed the
manager check, which is an internal inconsistency". Under the Chinese wording, a proposal that never went through the
pre-check would not plainly be a STOP. That is exactly the bypass case.

**Fix.** Use "到达 worker guard 并在该处失败的任何提议（内部不一致，即代码 bug）".

## NON-BLOCKING

### N1. The gate's other format requirements are not stated in the draft

These were checked against the gate code and synthetic runs. The draft only says "a dated author heading".

- **Heading.** The `###` heading must start at column 0 and contain "author" (case-insensitive). Its date must parse
  as `%d %B %Y` with the full month name, or as `%Y-%m-%d`.
  - `### 14 Nov 2026 — … (author)` fails (dated = False).
  - `### 14 November 2026 — … (author)` and `### 2026-11-14 — … (author)` pass.
- **Table.** The row must sit in a table with a two-column header line and a `|---|---|` separator. A row pasted
  without a header is not counted (synthetic result: `[]`).
- **One line.** The row must be a single line, because a blank line or a line break ends the table.
- **Exactly one row with this ID.** It must be the only row with the ID `R1-EXAM-B2-INVALID-TRIALS` in the whole of §10.
  - If the author adds both an English and a Chinese table row with this ID, `len(invalid)` is 2 and the gate fails.
  - If the Chinese is to be the row instead, it must be one line, using `<br>` for breaks as the existing PLAN rows
    do, with a bare first cell. The two B1 IDs must stay in ASCII. The Chinese text already has them.
  - The Chinese blockquote as drafted is not a table row. It is safe as surrounding text but does not satisfy the
    gate.

The draft should state these requirements next to the row.

### N2. "Everything else stays as in the two B1 rows" is broader than the invalid-trial rules

The signed text "原样延伸" supports carrying the rules over. But the two B1 rows also contain B1-run-specific clauses:

- the cap condition against the completions of `fffa_20261111_b`;
- re-pins of `paper_commit`;
- the restart hand-offs `_c`/`_d`;
- the reuse assessment;
- marker retirements;
- the "Unchanged" lists naming B1's seeds, nodes and budgets (W = 20, LLM-call cap 80).

For B2, `llm_call_cap`, the instances and the seeds are bound separately (hand-off §0.2, §2 and §3; the power-plan
row). Suggested wording: "The invalid-trial and STOP rules of the two B1 rows otherwise apply unchanged. Their
B1-run-specific clauses (stopped-run facts, condition, re-pins, restart, reuse, marker) do not, and B2 seeds, budgets,
nodes and instances are set by their own rows." The expanded "Unchanged" paragraph of the draft already avoids
seeds, budgets and nodes, which is right.

### N3. The English row does not say M19 and M20 trials are charged

The English row says M19 after trial 1 and M20 "are invalid trials" but not that they are charged. The Chinese header
("计入 LLM 预算") covers all four classes. Diagnosis §3 says "charged" for both, and the code charges every proposer
call. Add "(LLM call charged)" so the two texts match.

### N4. Journal wording

- PLAN l. 1147 item (3) says "Every proposer call is journalled … before the proposal is returned".
- The draft's English row says "Every proposal is written to the journal".
- The draft's Chinese says "每个提议在返回前写入 journal".
- The signed text says "提议执行前写入 journal".

In code these are equivalent. `b1_llm_truncation.py::B1CappedLangGraphManager._b1_journal` writes one fsynced row per
proposer call, including truncated and overflowed calls, before `propose_next_trial` returns. The validator requires
one row per proposer `llm_call`. Still, "every proposer call" is the exact B1 term. Suggested wording:
- English: "Every proposer call is journalled … before its proposal is returned, so before any execution."
- Chinese: "每次提议调用在提议返回前（即执行前）写入 journal".

### N5. Cap scope in the Chinese text

The signed text says "每次调用 max_completion_tokens 16384". The draft correctly restricts the cap to proposer calls,
"每次提议调用", as PLAN l. 1141 does: the A4 observer keeps `max_tokens` 4096. This is a faithful reading of the B1
row, not a deviation. It would help to also say "A4 observer call not capped" in the English row and the Chinese text,
so the narrower reading of "每次调用" is explicit.

### N6. Out of scope, for the caller: the power-plan draft row at `a97c2f94` would also fail the gate

`PLAN_ROW_R1-EXAM-B2-POWER-PLAN_DRAFT_20261114.md` has the same problem as B1: its first cell is
`R1-EXAM-B2-POWER-PLAN (⟨date⟩)`. Its decision cell also contains `b2_instances_per_node = 4` twice. The scratch run
found `['4', '4']`, and `_b2_author_rows` requires exactly one match. So that row would fail the gate even with a bare
first cell. This needs its own review.

### N7. The gate is uncommitted

The format check above is against the uncommitted gate in `/tmp/pb/wt/b2code`. If that code changes before review,
B1 and N1 should be rechecked against the committed version.

## Re-review scope

- **B1:** check the first cell of the row.
- **B2 and B3:** compare the English row and the Chinese text against PLAN l. 1147 item (4).
- **N1–N5:** optional, but recommended.

---

# Review — PLAN §10 row draft `R1-EXAM-B2-INVALID-TRIALS` (round 2)

Reviewed commit: d1ac667859afced092541dff52c1885c10dd5ff5
Branch: `mac-b2-plan-20261114` (worktree `/tmp/pb/wt/b2plan`).
File: `docs/r1/proposals/PLAN_ROW_R1-EXAM-B2-INVALID-TRIALS_DRAFT_20261114.md`, rev 2.
Parent chain: `a0018635` (round 1) → `5a317b14` (power-plan draft rev 2, a different file) → `d1ac6678`, which changes
only this draft.

Verdict: accepted

Independent reviewer (AI, Claude), 14 Nov 2026. No worktree was modified. Scratch work was kept in `/tmp/rev_inv`
and has been removed.

## Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| B1: first cell carried `(⟨date⟩)` | **Resolved** | In both paste blocks the first cell is exactly `R1-EXAM-B2-INVALID-TRIALS`. The date is in the `###` heading. The gate result is below. |
| B2: STOP list narrower than PLAN l. 1147 item (4) | **Resolved** | The English row now ends its STOP list with "and all infrastructure, authority and other checks", the B1 wording. The Chinese has "所有基础设施、授权及其他检查". The expanded section matches. |
| B3: Chinese narrowed the worker-guard STOP | **Resolved** | The Chinese now reads "任何到达 worker guard 并未通过的提议（内部不一致，即代码 bug）". That is the same as the English "any proposal that reaches the worker guard and fails it", PLAN l. 1147 and diagnosis §4.1. |
| N1: gate format not stated | Resolved | A new section "Format the B2 author gate requires" covers all the format points listed under "Gate format" below, and the rule to paste one block only. |
| N2: "Everything else stays as in the two B1 rows" was too broad | Resolved | The row now scopes the extension to "the invalid-trial and STOP rules". It lists the B1-run-specific clauses that are not extended: stopped-run facts, the `fffa_20261111_b` cap condition, re-pins, restart hand-offs, reuse, marker retirements, and B1's seeds, nodes, budgets and instance counts. It says B2 sets these through its own bindings, as hand-off §0.2 and §2 do. |
| N3: M19/M20 not stated as charged | Resolved | English: "The following are invalid trials, each charged its LLM call: … M19 after trial 1; and M20". Chinese: "记为无效试验并计入 LLM 预算的情形：… 第 1 次试验之后的 M19；M20". |
| N4: journal wording | Resolved | English: "Every proposer call is journalled … before its proposal is returned, so before any execution". Chinese: "每次提议调用都在提议返回之前（即执行之前）写入 journal". This matches PLAN l. 1147 item (3) and `B1CappedLangGraphManager._b1_journal`, which writes one fsynced row per proposer call before `propose_next_trial` returns. |
| N5: cap scope | Resolved | Both texts say the cap applies to every proposer call and that the A4 observer call is not capped (`max_tokens` 4096, as in PLAN l. 1141). |
| N6: power-plan row (out of scope) | Addressed in `5a317b14` for gate purposes | The power-plan row's paste blocks now state `b2_instances_per_node = 4` once, with a bare first cell (gate result below). Its content was not reviewed here. |
| N7: gate uncommitted | Still true | The draft labels the gate "B2 code unit, under review". The check below is against the current working tree of `/tmp/pb/wt/b2code`. |

## Gate format: runs of the gate code

I took `B2_INVALID_TRIALS_ROW`, `_dated_author_decisions` and `_b2_author_rows` from
`/tmp/pb/wt/b2code/r1/exam/runtime.py` (l. 423–495, uncommitted working tree), read-only. I copied them verbatim into a
scratch script. Each fenced paste block of the draft was extracted and pasted unchanged into a synthetic §10. That §10
had a preceding dated author table and was followed by `## 11.`. The power-plan rows came from the paste blocks of
`5a317b14`, or from a minimal one-line row.

| Synthetic §10 | Invalid-trials decisions (dated?) | `_b2_author_rows(plan, 4)` |
|---|---|---|
| Chinese invalid block + Chinese power block | 1 (True) | **True** |
| Chinese invalid block + English power block | 1 (True) | **True** |
| English invalid block + Chinese power block | 1 (True) | **True** |
| English invalid block + English power block | 1 (True) | **True** |
| Each invalid block + a minimal power row under an ISO-dated author heading | 1 (True) | **True** |
| Both rows in one shared table under one heading, for each language | — | **True** |
| Real `7912b7ff:docs/r1/PLAN.md` with the Chinese, or the English, invalid and power blocks inserted at the end of §10 | 1 (True) | **True** |
| Real PLAN, no B2 rows (baseline) | 0 | False |

Negative controls behave as the draft's format section says:

| Synthetic §10 | Result |
|---|---|
| Both invalid blocks pasted | 2 rows → False |
| Heading `14 Nov 2026` | False |
| `_b2_author_rows(plan, 3)` | False |

Both rows have three `|` and two cells. No cell contains `|`, and each decision cell names both B1 IDs in ASCII.

## Content (check 1) and fidelity (check 2)

- **The rules carried over** match PLAN l. 1141 and l. 1147, diagnosis §3, §4.1 and §5, hand-off §6, and the code at
  `7912b7ff`:
  - **Invalid trials, each charged:** M2 truncation (`length` or `content_filter`), M5–M9 (not executed, no observer
    call), M19 after trial 1, and M20.
  - **Cap and journal:** a cap of 16,384 per proposer call, and the journal written before the proposal is returned.
  - **Still STOP:** the worker guard, M10, M15, M16, M17 including the final-Y seeds and an incomplete final-Y audit,
    M18, M19 at trial 1, M21, `cache_prompt` evidence, an existing root, and all infrastructure, authority and other
    checks.
  - **M14** executes.
- **Width.** Nothing is widened or narrowed. The final-Y clause restates `campaign.py` l. 308–309. The not-extended list
  covers only B1-run-specific clauses, not rules.
- **The Chinese row** matches the English row clause by clause.
- **The signed text** is reflected faithfully:
  - "截断与模型输出问题记为无效试验并计入 LLM 预算": yes.
  - "每次调用 max_completion_tokens 16384": yes. This is read as every proposer call, per PLAN l. 1141, and the draft says
    so explicitly.
  - "提议执行前写入 journal": yes.
  - "代码 bug 仍 STOP": yes.

## Overclaims (check 4)

There are none. The draft "governs nothing until the author commits it in PLAN §10". Nothing sets approval. "Records
the author's instruction of 14 Nov" is row text for the author to commit.

## BLOCKING

None.

## NON-BLOCKING

- **NB1.** The paste blocks fix the heading date as `14 November 2026`. The draft says any date in either accepted form
  works, and the gate tests confirm it. The author should use the commit date.
- **NB2.** The gate is still uncommitted. If `_dated_author_decisions` or `_b2_author_rows` change before the B2 code
  unit is accepted, the runs above should be repeated against the committed code.

Accepted commit: d1ac667859afced092541dff52c1885c10dd5ff5
