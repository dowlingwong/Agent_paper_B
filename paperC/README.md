# Paper C (working name) — sequential control of governed autoresearch loops

**Status (15 Nov 2026).**
- Working plan, not adopted by PLAN rows.
- Infrastructure build started on 15 Nov. Paper C no longer waits for Paper B's submission (author, 15 Nov). No data yet.
- **Reframed after Track S STOP 4** (R1-PAPERC-REFRAME, 15 Nov): a map of where sequential control pays (frame), acceptance and evaluation control as the confirmatory core, expensive GPU runs as the broadening tier, proposer steering as an extension. A headroom census on existing logs comes first (R1-PAPERC-CENSUS-FIRST).

AI-assisted (Claude, chat session).

## Topic

A governed autoresearch loop works like this:
- an LLM proposer suggests an edit;
- a controller decides whether to run it (execute / skip);
- after a noisy evaluation, the controller decides whether to keep it (keep / discard);
- worker runs and LLM calls are capped.

**Paper B** studies each decision on its own:
- C1: a noise floor;
- C2: a one-step index theorem, together with the conditions (no feedback, no information, fixed price) under which the whole loop **reduces** to independent one-step decisions;
- C3: a learned per-proposal belief.

Paper B makes no claim about multi-step control. Its current framing is "noise-aware DAC, and when it reduces to one-step decisions" (PLAN §10 R1-TRACKS-STOP4-CONSEQUENCES).

**Paper C** takes up what Paper B leaves open. In the real loop, those reduction conditions fail by construction:
- the budget binds;
- running an edit reveals information about later edits;
- edits interact with the incumbent;
- the proposer reacts to what was kept;
- the recorded incumbent value carries a shared error.

The questions are where non-myopic control is worth anything, through which of these channels, and whether multi-step RL or a language decision model adds anything beyond strong non-RL sequential methods.

## Research questions

| ID | Question | Status in the core version |
|---|---|---|
| Q1 | Does non-myopic control beat the tuned static rule on whole campaigns? | confirmatory (E-T0, keep/discard included) |
| Q2 | With the same immediate estimate, does a continuation term help, beyond a level shift? | secondary |
| Q3 | Does multi-step RL beat the strongest non-RL multi-step method at matched information, data and budget? Decided as superiority **or** TOST equivalence at a pre-declared δ | confirmatory only after a passed go/no-go; otherwise "not testable at this budget" |
| Q4 | Does a decision model that reads the proposal text add value in the multi-step policy? | secondary, in-distribution |
| Q5 | Which channel produces the gain: budget, information, feedback, interaction, or shared incumbent error? | secondary |
| OPD | Does on-policy distillation (dense teacher signal on the student's own states) beat offline distillation and sparse-return RL at equal interaction? | added 15 Nov (route M4); core status is open item P10 |

## Approach

- **Sequential Policy Track (SPT).**
  - Transitions are collected under a logged behaviour mixture, plus repeated fork trees.
  - A fixed method ladder is trained and selected on development instances.
  - Frozen arms are tested on fresh campaigns with fresh-seed audits.
- **Environments.**
  - E-SYN: synthetic worlds with one channel switched on at a time, and exact or certified oracles.
  - E-T0: two CPU nodes of Paper B, `digits_mlp` and `tabular_mlp`.
  - E-INT: one interaction-rich GPU task, descriptive only.
  - E-HELD and E-SIM: extensions.
- **Methods.**
  - Non-RL rungs, all on one frozen belief: N0 execute-all, N1 tuned static, N2 myopic, N2b single-step action head, N3 non-myopic thresholds, N4 budget DP, N6 fork-Q regression.
  - Offline RL: R0 fitted Q iteration, R1 IQL.
  - LM routes on Paper B's decision models (Kev, Qwen controls):
    - M1: offline distillation;
    - M2: offline value learning with an LM encoder;
    - M3: fork-grouped policy gradient;
    - **M4: single-teacher on-policy distillation** — M4a at the loop level, M4b at the token level.
- **Proposer of record.** The Track X exam winner, thinking off, the same model as Paper B's main proposer.
- **Statistics.**
  - Unit: the campaign instance, with paired differences.
  - Q1 and Q3 at α = 0.025 each, Holm across nodes.
  - δ_n = max(0.002, 0.25 · s̃_n) on E-T0.
  - On E-SYN, δ is 10 % of the gap between the DP oracle and the best myopic rule.

**Core version** (first submission): E-SYN and the two E-T0 nodes; Q1 confirmatory; Q3 as above; Q2, Q4 and Q5 secondary; N0–N4, N2b, N6, R0, R1, M1; E-INT descriptive on one node.

**Extension** (stated, not promised): E-INT powered; E-HELD transfer; E-SIM/MPC; online RL; M2, M3, M4b; verify and stop actions; depth-2 forks; a second proposer.

## Decisions and open items

| Item | Status |
|---|---|
| Multi-step claims, Sequential Policy Track and multi-step RL moved out of Paper B into a follow-up paper | author, 4 Nov (sequential-policy comment) |
| Proposer of record = the exam winner; core version first; δ as in plan §11.3 | author positions, 5 Nov. Draft rows R1-PAPERC-PROPOSER / -CORE / -DELTA are **not yet committed** in PLAN |
| Single-teacher OPD goes into Paper C | author, 15 Nov (addendum §A) |
| No waiting for Paper B's submission; real-node phases need their own runbook, review and authorization | author, 15 Nov (addendum §C) |
| PLAN rows R1-PAPERC-PROPOSER, -DELTA, -OPD, -NOWAIT, -HOME | recorded in `docs/r1/PLAN.md` §10, 15 Nov |
| Track S ended at STOP 4 without evidence; consequences for Paper C | addendum §B |
| Reframing after STOP 4 (R-C1) and census first (R-C2) | author, 15 Nov: R1-PAPERC-REFRAME, R1-PAPERC-CENSUS-FIRST |
| R1-PAPERC-CORE (nodes and channels of the core version) | after the census report (R-C3) |
| P1–P9 of plan §17; P10 (M4a in the core version) | open |

## Layout

```
paperC/
  README.md                         this file
  docs/
    proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md   the plan, rev 2 (5 Nov)
    PLAN_ADDENDUM_20261115.md       OPD route M4, Track S STOP 4 consequences, no waiting for Paper B
    proposals/PAPER_C_REFRAME_AFTER_TRACKS_STOP4_20261115.md  options after STOP 4 and the recommendation
    BUILD_LIST.md                   what has to be built (B0–B15)
    BUILD_RUNBOOK.md                phases P0–P10, done-when, review, STOP rules
    reviews/PAPER_C_PLAN_REVIEW_20261104.md                independent review of plan rev 1
    inputs/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md    the comment that started Paper C
  src/paperc/                       Python package (code from P1 on)
  tests/                            pytest suite for paperC only
```

Run the tests:

```
PYTHONPATH=paperC/src python3 -m pytest -q -p no:cacheprovider paperC/tests
```

## Provenance of the moved files

| File | Source |
|---|---|
| `docs/proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md` | `docs/r1/proposals/` on branch `docs/seq-revision-04nov` @ `4af310e` (rev 2), unchanged |
| `docs/reviews/PAPER_C_PLAN_REVIEW_20261104.md` | `docs/r1/reviews/` on `docs/seq-revision-04nov` @ `4af310e`, unchanged |
| `docs/inputs/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md` | `docs/r1/proposals/` on `docs/runbooks-04nov` @ `78000a6`, unchanged |

Paths inside these files still point to `docs/r1/...`. Neither file existed in the canonical line (`author-qtorch-20261115`), so nothing was removed there.

**Related, left in place:**
- the Paper B side of the same revision (`SEQUENTIAL_POLICY_REVISION_20261104.md`, work items W1–W5, on `docs/seq-revision-04nov`);
- the Track S code (`r1/tracks/`, on `trackS-ops-20261030`) that the SPT ports from.

## Working rules

- Paper C runs alongside Paper B. It does not wait for Paper B's submission (R1-PAPERC-NOWAIT).
- Every real-node phase gets its own runbook, an independent review and an author authorization before it runs.
- Seeds come from the Paper C registry.
- Hosts follow the PLAN host rows. HoreKa 2 and the ETP HTCondor GPUs are the natural Paper C hosts; TASL-2 and TASL-7 are used only where a row allocates them.
- The build phases P0–P10 are CPU-only and change nothing outside `paperC/`.
