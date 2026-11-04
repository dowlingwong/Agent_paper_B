# Agent prompts and runbooks — which ones are in use (4 Nov 2026)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request ("你帮我整理一下repo"); AI-assisted.** This is an index only: no file was moved or changed. If this index and `../PLAN.md` §10 disagree, the PLAN wins.

Since R1-HANDOVER-04NOV and R1-SERVER-AGENTS-TWO (4 Nov), three agent threads do the work: the Mac-local agent, the operator (TASL-2, TASL-7, deepthought, Ada) and the HoreKa agent (HoreKa 2, the T1 tier).

## In use

| File | Who follows it | What for |
|---|---|---|
| `MAC_LOCAL_RUNBOOK_20261104.md` | Mac-local agent | Code, drafts, integration (`mac-int-20261104`), tasks M1–M15; worker subagents allowed (§0, rev 3.3) |
| `OPERATOR_RUNBOOK_20261104.md` | operator | Phases O0–O11 on TASL-2, TASL-7, deepthought and Ada; T1 belongs to the HoreKa thread (O8) |
| `HOREKA_SCAN_PROMPT_20261104.md` | HoreKa scan agent | Read-only HoreKa 2 scan, rev 5.6 (review `../reviews/HOREKA_SCAN_PROMPT_REV54_REVIEW_20261104.md`, round 3 PASS). The HoreKa execution runbook follows the scan report |
| `TRACK_G_RUNBOOK.md` | HoreKa agent (with Mac-agent code, M10) | Track G: T1 census, ports, fixed budgets, sweep |
| `PORTAL_EXAM_RUNBOOK.md` | operator (O1, O2) | Track X exam procedures: Stage A, B1, B2 |
| `TRACK_S_OPERATOR_RUNBOOK_20261030.md` | operator (O3) | Track S on TASL-2 |
| `PORTAL_TRACK_P_RUNBOOK.md` | operator (O7) | Track P (host is TASL-7 since R1-TASL7-TRACKP) |
| `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` | operator (reference) | deepthought host details (§1), cited by the operator runbook's host table |

## History (kept, not followed)

| File(s) | Date | Replaced by |
|---|---|---|
| `MAC_LOCAL_RUNBOOK.md` | 26 Oct | `MAC_LOCAL_RUNBOOK_20261104.md` |
| `OPERATOR_HANDOVER_20261027.md` | 27 Oct | R1-HANDOVER-04NOV and `OPERATOR_RUNBOOK_20261104.md` |
| `BUILD_BATCH1_PROMPT.md` … `BUILD_BATCH4C_PROMPT.md` | 9–14 Oct | Done build batches |
| `ADA_DT4_RERUN_PROMPT.md`, `ADA_DT4_RECOVERY_PROMPT.md`, `ADA_E1B_RERUN2_PROMPT.md`, `ADA_RERUN2_DIAG_AND_DI_TEST_PROMPT.md`, `ADA_DI_TEST_MEMORY_ON_PARTIAL_PROMPT.md` | 13–18 Oct | Done pilot runs and recoveries on Ada |
| `DEEPTHOUGHT_BATCH1_PROMPT.md`, `DEEPTHOUGHT_NODE_REPAIR_PROMPT.md`, `IONOSPHERE_DIAGNOSIS_PROMPT.md` | 13–27 Oct | Done deepthought batches and diagnoses |
| `TRACK_S_REV2_REVIEW_PROMPT_20261029.md`, `TRACK_S_REV3_REVIEW_PROMPT_20261029.md` | 29 Oct | Done review rounds (records in `../reviews/`) |

Branches are listed in `../BRANCHES_20261104.md`.
