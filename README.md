# Paper B — noisy incumbent-relative acceptance in governed autoresearch loops (route R1)

Authoritative remote: [Agent_paper_B](https://github.com/dowlingwong/Agent_paper_B).
Target venue: ICML 2027 (changed from TMLR on 24 Oct 2026, PLAN R1-VENUE-3), with the ICML-main-track quality bar (docs/r1/PLAN.md §9).

**Start here:** [docs/r1/PLAN.md](docs/r1/PLAN.md) (canonical plan and dated author
decisions), [docs/r1/RUNBOOK.md](docs/r1/RUNBOOK.md) (phases, gates) and
[docs/r1/STATUS.md](docs/r1/STATUS.md) (the only record of what is done).
Execution is split between two agents: the Mac-local agent
([docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md](docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md):
code, drafts, analysis, manuscript) and one experiment operator with SSH to the servers
([docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md](docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md)).

## The question

An LLM manager proposes bounded edits to a training script, a worker trains, and a
control plane keeps an edit only if the noisy metric strictly beats the incumbent's
recorded value. R1 treats this loop as noisy sequential selection with an incumbent:

- **C1** — measured control errors: false keeps and discards, and wasted runs.
- **C2** — theory of acceptance under noise: Bayes keep threshold, value of verify,
  the winner's curse of `current_best`, and a proposer whose law depends on the ledger
  (`docs/r1/theory/`).
- **C3** — a learned per-proposal prior plugged into the C2 rule (pre-execution skip
  and a per-proposal keep threshold), evaluated as a ladder of arms above the C2
  index policy (`docs/r1/C3_DESIGN.md`).
- **C4** (secondary) — proposer feedback: a test of when trial-by-trial acceptance
  is optimal (decision independence), and a debiased-memory intervention.

## Benchmarks and data (revised 4 Nov 2026, PLAN §10 R1-BX-*)

| Tier | Role | Tasks |
|---|---|---|
| T0 | Controlled testbed: theory checks, Track S, ablations; single-parameter edits as the low-interaction condition | The 8 CPU nodes (OpenML and small-MLP) |
| T1 | C3 labels and closed-loop evaluation (also with a second, API proposer); the B.7 gate | GPU tasks from autoresearch, MLGym and MLAgentBench, run at fixed step budgets with code-level diffs |
| T2 | Evaluation only (closed loop, also with the API proposer) | Heavier MLGym and MLAgentBench tasks |

- **Target:** 12–16 real tasks from ≥ 3 suites and ≥ 5 domains.
- **Primary generalisation:** leave-one-suite-out.
- **Integration:** the suites' task assets run as harness nodes; their agent frameworks are not used.
- **Suites:** 1GC-7RC was dropped because its repository is not public (4 Nov); the T1/T2 lists are fixed by the author after the Track G census.
- **Proposers:** the main proposer is the Track X exam pick, run with thinking off (R1-MAIN-PROPOSER). `qwen2.5-coder:7b` (sweep 1, frozen) is the second source.
- **Dates:** current targets are B.7 ≈ 8 Dec 2026, D.3 ≈ 3 Jan 2027, manuscript 10 Jan 2027 (R1-BX-D14). They are recomputed after the T1 pilot.

## Tracks

| Track | What it does |
|---|---|
| B | C3 label sweeps and audits: sweep 1 (7B, frozen), sweep 2 (main proposer; T0 and T1 parts), offline arms, the B.7 gate |
| G | Real-task benchmarks, tiers T1/T2 (the critical path since 4 Nov) |
| X | Proposer exam that selects the main proposer (Stage A, B1, B2) |
| S | Sequentiality screen: whether one-step decisions suffice (DAC reduction); 2 CPU nodes plus 1–2 GPU nodes; fallback ≈ 15 Dec |
| P | Decision-model post-training for A5/A6 (Kev, Qwen control, TabPFN) |
| H | Control interface for the learned prior (E1 skip, E2 keep) |

All numbers in this repository so far are `PILOT` or `ENGINEERING_ONLY`, except the sweep-1
proposal batch, which R1-SWEEP1-CLASSIFY classes as EVIDENCE; it has no audited labels yet, so
no result exists (RUNBOOK §1, STATUS).

## Layout

| Path | What it is |
|---|---|
| `r1/` | R1 analysis code: noise pilot (`noise/`), headroom pilot (`headroom/`), theory code (`theory/`), liveness, branch schema, baselines, Ada/Deepthought runners (`scripts/`), tests (`tests/`). |
| `docs/r1/` | Plan, runbooks, status, specs (`C3_DESIGN.md`, `TRACK_P_POST_TRAINING.md`, `TECH_ROUTE.md`), theory notes (T1–T5), proposals, authorizations, reports, reviews and agent prompts (`prompts/`). |
| `results/r1/` | Committed pilot and engineering outputs (`pilot/`, `engineering/`). |
| `papers/` | Manuscript (not started; format open, PLAN R1-FORMAT). |
| `archive/old_b_2026-10-09/` | The retired route: plans (`docs_paper_split/`), manuscript (`paper_b_manuscript/`) and, since 18 Oct 2026, all its code, tests, protocols, release tooling and the vendored Pi tree (`code/`, with `PROVENANCE.md` and licences). Read-only history. |

Harness changes live on branch `r1` of the separate `autoresearch_harness`
repository (PLAN D14); R1 code runs against that checkout.

## Checks

```sh
make r1-test AR_HARNESS_ROOT=../autoresearch_harness   # R1 test suite
make r1-e2e                                            # R1 end-to-end smoke
make legacy-test LEGACY_PY=/path/to/python3.13         # old-route suites (212/6/12)
```

LLM workloads never run on the Mac (PLAN R1-COMPUTE). They run on the servers: two RTX 4090 hosts
(TASL-2, TASL-7), deepthought (4 × TITAN X; CPU audits; the main proposer may be served across two cards if a
dual-card qualification passes)
and Ada (8 × RTX 6000 Ada, shared, resumable work only; the Track G census starts there).
