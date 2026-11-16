# Agent prompts and runbooks — which ones are in use (16 Nov 2026)

**Updated 16 Nov 2026 by the coordinating chat (Claude) during the repo cleanup the author asked for; AI-assisted.** This is an index. If it disagrees with `../PLAN.md` §10, PLAN wins. The 4 Nov version of this index is in git history.

Four agent threads do the work (see the top-level README): the Mac agent (desk only), the experiment agent (TASL-7, TASL-2, Ada), the cluster agent (deepthought, ETP HTCondor) and the HoreKa agent (idle).

## In use

| File | Who follows it | What for |
|---|---|---|
| `SWEEP2_HTCONDOR_RUNBOOK_20261116.md` | cluster agent, Mac agent | Sweep 2 (and later sweeps) on HTCondor: units S2-M1…M5, S2-C1…C8, prerequisites P1–P7; host row R1-SWEEP-HOST-HTC, settings R1-SWEEP2-SETTINGS |
| `HTCONDOR_PREP_RUNBOOK_20261114.md` + `HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md` | cluster agent (reference) | The HTCondor chain (S1–S6, I2/I3), done; cited by `r1/scripts/htcondor/` |
| `EXPERIMENT_AGENT_RUNBOOK_20261111.md` | experiment agent | Standing rules for TASL hosts (B1/B2 parts done) |
| `MAC_LOCAL_RUNBOOK_20261104.md` | Mac agent | Desk-only work, bundles, worker subagents (§0); cited by code |
| `PORTAL_TRACK_P_RUNBOOK.md` | experiment agent | Track P (host TASL-7 since R1-TASL7-TRACKP) |
| `TRACK_G_RUNBOOK.md`, `TRACKG_PORT_CHECKLIST.md` | experiment agent (Ada census), cluster agent (G.1b on L40S), Mac agent (code) | Track G |
| `PORTAL_EXAM_RUNBOOK.md` | reference | Track X exam procedures (Stage A, B1, B2), done; cited by PLAN and code |
| `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` | reference | Sweep 1 host details; cited by the sweep-1 authorization |

## Kept in place for references (not followed)

These are cited by PLAN rows, authorizations or code, so they stay where they are:
- `MAC_LOCAL_RUNBOOK.md` (26 Oct);
- `OPERATOR_RUNBOOK_20261104.md` (replaced by the experiment- and cluster-agent split, 15–16 Nov);
- `HOREKA_RUNBOOK_20261104.md`, `HOREKA_SCAN_PROMPT_20261104.md`, `HOREKA_STARTUP_RUNBOOK_20261109.md` (HoreKa idle; sweeps moved to HTCondor);
- `TRACK_S_OPERATOR_RUNBOOK_20261030.md` (Track S ended at STOP 4);
- `MAC_OVERNIGHT_PROMPT_20261107.md`, `MAC_OVERNIGHT_RUNBOOK_20261109.md`, `MAC_OVERNIGHT_RUNBOOK_20261113.md` (done);
- `AUTHOR_B1_EVENING_REPLY_20261107.md`, `AUTHOR_B1_FOLLOWUP_REPLY_20261107.md`;
- `BUILD_BATCH1_PROMPT.md`, `BUILD_BATCH2_PROMPT.md`, `ADA_DT4_RECOVERY_PROMPT.md`, `ADA_DI_TEST_MEMORY_ON_PARTIAL_PROMPT.md` (October; done).

## Archive (`archive/`)

Superseded prompts that nothing cites were moved, unchanged, to `archive/` on 16 Nov:
- `ADA_DT4_RERUN_PROMPT.md`, `ADA_E1B_RERUN2_PROMPT.md`, `ADA_RERUN2_DIAG_AND_DI_TEST_PROMPT.md`;
- `BUILD_BATCH3_PROMPT.md`, `BUILD_BATCH4_PROMPT.md`, `BUILD_BATCH4B_PROMPT.md`, `BUILD_BATCH4C_PROMPT.md`;
- `DEEPTHOUGHT_BATCH1_PROMPT.md`, `DEEPTHOUGHT_NODE_REPAIR_PROMPT.md`, `IONOSPHERE_DIAGNOSIS_PROMPT.md`;
- `HOREKA_QUEUE_PROBE_PROMPT_20261104.md`, `MAC_AGENT_HANDOVER_PROMPT_20261104.md`, `OPERATOR_HANDOVER_20261027.md`;
- `TRACK_S_REV2_REVIEW_PROMPT_20261029.md`, `TRACK_S_REV3_REVIEW_PROMPT_20261029.md`.

Branches are listed in `../BRANCHES.md`.
