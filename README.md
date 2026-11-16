# Paper B — noisy incumbent-relative acceptance in governed autoresearch loops (route R1)

Authoritative remote: [Agent_paper_B](https://github.com/dowlingwong/Agent_paper_B).
Target venue: ICML 2027 (changed from TMLR on 24 Oct 2026, PLAN R1-VENUE-3), with the ICML-main-track quality bar (docs/r1/PLAN.md §9).

**Start here:**
- [docs/r1/PLAN.md](docs/r1/PLAN.md): the canonical plan. Its §10 holds the dated author decisions, and these take precedence over every other file.
- [docs/r1/RUNBOOK.md](docs/r1/RUNBOOK.md): phases and gates.
- [docs/r1/STATUS.md](docs/r1/STATUS.md): the only record of what is done.
- [docs/r1/BRANCHES.md](docs/r1/BRANCHES.md): which branches exist, what `main` means, and the archive tags.

## Where things stand (16 November 2026)

- **Track X (proposer exam): done.**
  - B1 `_d` and B2 are EVIDENCE runs on TASL-7, and STOP 6 was accepted.
  - The pick is `gemma4_31b`, run with thinking off (PLAN R1-EXAM-X7). It was the only finalist, because it was the only candidate to pass D28.
  - Disclosed: its B1 μ̂ lies below the scripted anchor and the `qwen2.5-coder:7b` anchor, within CI.
  - Records: `docs/r1/reports/b1_d_20261113_evidence/` and `docs/r1/reports/b2_exec_20261115/` (`B2_REPORT_20261115.md`).
- **Track S (sequentiality screen): ended at STOP 4.**
  - The calibration gate failed on both nodes (R1-TRACKS-STOP4-END).
  - Its pilot findings are disclosure only, and the appendix wording is per decision (R1-T4-PROOF-CHECK).
  - Records: `results/r1/tracks/` and the `TRACKS_*` reports and reviews.
- **Theory (T4):** Prop. 8′, 10(a′) and 10(c) were approved with errata. The incumbent-error model is a shared latent variable, and the gate counts 20 proposals (R1-T4-PROOF-CHECK).
- **Track B (C3 labels): sweep 2 is in preparation.**
  - Sweep 1 (`qwen2.5-coder:7b`, deepthought) is frozen as the second source.
  - Sweep 2 (the pick) and all later sweeps run as HTCondor jobs. LLM label runs use NEMO2 L40S only, at context 32,768 with the exam's server settings (R1-SWEEP-HOST-HTC, R1-SWEEP2-SETTINGS).
  - Work plan: `docs/r1/prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`.
  - Sweep-2 labels are sealed until R1-BX-D8-CONFIRM. Gate conventions 1–3 are decided (R1-BX-D8-V3-A); the pass rule and the test floor are pending.
- **Track P:** the decision-model work resumes on TASL-7. The `c3_features/v3` + `trackp_prompt/v2` tables have been rebuilt (EVIDENCE), and R1-B2-REPAIR-SCOPE-ACK and R1-W2-3-STOP are signed.
- **Track G (real-task nodes, critical path):** the G.0 census runs on Ada; the G.1b GPU noise floors run on L40S (R1-TRACKG-G1B-HOST).
- **Dates:** the targets are B.7 ≈ 8 Dec 2026, D.3 ≈ 3 Jan 2027 and the manuscript on 10 Jan 2027 (R1-BX-D14).

## Who does what

| Agent | Hosts | Rules |
|---|---|---|
| Mac agent (Claude) | the Mac only: code, drafts, simulations, reviews | cannot SSH; delivers git bundles plus an append-only `READY.txt` |
| Experiment agent | TASL-7, TASL-2 (Tailscale), Ada | the only operator on those hosts |
| Cluster agent | deepthought, ETP HTCondor (NEMO2 L40S/H200, TOpAS V100S) | the only operator there; image `ghcr.io/dowlingwong/r1-htc-*` by digest |
| HoreKa agent | HoreKa | idle (needs the KIT VPN, which conflicts with Tailscale) |
| Coordinating chat | none | reviews, pushes bundles, commits author rows that the author signs in chat |

Every unit gets a fresh independent reviewer. Branches and hosts have one operator each. Nobody force-pushes. Nothing is deleted: files move to `_to_delete/`, and branches are archived as tags (see `docs/r1/BRANCHES.md`).

## The question

An LLM manager proposes bounded edits to a training script, a worker trains, and a control plane keeps an edit only if the noisy metric strictly beats the incumbent's recorded value. R1 treats this loop as noisy sequential selection with an incumbent:

- **C1** — measured control errors: false keeps and discards, and wasted runs.
- **C2** — theory of acceptance under noise: Bayes keep threshold, value of verify, the winner's curse of `current_best`, and a proposer whose law depends on the ledger (`docs/r1/theory/`).
- **C3** — a learned per-proposal prior plugged into the C2 rule (pre-execution skip and a per-proposal keep threshold), evaluated as a ladder of arms above the C2 index policy (`docs/r1/C3_DESIGN.md`).
- **C4** (secondary) — proposer feedback: a test of when trial-by-trial acceptance is optimal (decision independence), and a debiased-memory intervention.

## Benchmarks and data (PLAN §10 R1-BX-*)

| Tier | Role | Tasks |
|---|---|---|
| T0 | Controlled testbed: theory checks, ablations; single-parameter edits as the low-interaction condition | The 8 CPU nodes (OpenML and small-MLP) |
| T1 | C3 labels and closed-loop evaluation (also with a second, API proposer); the B.7 gate | GPU tasks from autoresearch, MLGym and MLAgentBench, at fixed step budgets with code-level diffs |
| T2 | Evaluation only | Heavier MLGym and MLAgentBench tasks |

- **Proposers:** the main proposer is the Track X pick, `gemma4_31b`, thinking off. `qwen2.5-coder:7b` (sweep 1, frozen) is the second source. Cross-proposer tables disclose the host, settings and harness differences, and also the smaller share of duplicate/no-op proposals under the pick (X.7(c) appendix).
- **Primary generalisation:** leave-one-suite-out.

## Tracks

| Track | What it does | State (16 Nov) |
|---|---|---|
| B | C3 label sweeps and audits, offline arms, the B.7 gate | sweep 1 frozen; sweep 2 in preparation on HTCondor |
| G | Real-task benchmarks, tiers T1/T2 | G.0 census on Ada |
| X | Proposer exam that selected the main proposer | done (X.7 signed) |
| S | Sequentiality screen | ended at STOP 4 |
| P | Decision-model post-training for A5/A6 | resuming on TASL-7 |
| H | Control interface for the learned prior (E1 skip, E2 keep) | code in `r1/` |

Execution labels: `EVIDENCE` only where an author authorization note matches (`docs/r1/authorizations/`). Everything else is `PILOT` or `ENGINEERING_ONLY`.

## Layout

| Path | What it is |
|---|---|
| `r1/` | R1 code: C3 (`c3/`), exam (`exam/`), Track S (`tracks/`), noise and headroom pilots, theory code, scripts (`scripts/`, including `scripts/htcondor/` for the HTCondor adapter and image), tests (`tests/`). |
| `sweep2/` | (on the cluster branches until merged) HTCondor job wrapper for sweep 2. |
| `docs/r1/` | Plan, runbook, status, specs (`C3_DESIGN.md`, `TRACK_P_POST_TRAINING.md`, `TECH_ROUTE.md`), theory notes, and: `authorizations/` (author notes), `proposals/` (drafts), `reports/` (records), `reviews/` (independent reviews), `prompts/` (agent runbooks; index in `prompts/README.md`, superseded ones in `prompts/archive/`). |
| `results/r1/` | Committed outputs: `evidence/` (sweep-1 EVIDENCE batch), `tracks/` (Track S), `pilot/`, `engineering/`. Large run outputs stay on the hosts and on `/ceph/srv/dwong/paperb/`. |
| `papers/` | Manuscript (format open, PLAN R1-FORMAT). |
| `archive/old_b_2026-10-09/` | The retired route (plans, manuscript, code). Read-only history. |
| `_to_delete/` | Files set aside for the author to delete. |

Harness changes live on branch `r1` of the separate `autoresearch_harness` repository (PLAN D14). R1 code runs against that checkout; the current pin for B2 and sweep 2 is `a3fedbb`.

## Checks

```sh
make r1-test AR_HARNESS_ROOT=../autoresearch_harness   # R1 test suite
make r1-e2e                                            # R1 end-to-end smoke
make legacy-test LEGACY_PY=/path/to/python3.13         # old-route suites
```

LLM workloads never run on the Mac (PLAN R1-COMPUTE). They run on:
- two RTX 4090 hosts (TASL-7 for Track P evidence, TASL-2);
- ETP HTCondor (NEMO2 L40S for all sweeps from sweep 2 on; CPU classes for audits);
- deepthought (CPU; sweep 1);
- Ada (8 × RTX 6000 Ada, shared, resumable work only).
