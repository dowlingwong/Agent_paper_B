# Brief — revising the plan after the sequential-policy comment (4 Nov 2026)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.**

**Your task.** Paper B (route R1) received the comment `docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md`. Revise the plan in response to it: write a proposal, not a decision. The author is Dowling Wong. Report to him in **Chinese**, and write documents in **English**.

Repository: `https://github.com/dowlingwong/agent_paper_b`. Read everything on branch **`mac-int-20261104`**, except the items marked otherwise below.

---

## 1. Files to read

**The comment**
- `docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md`. Its links point to the Mac's `docs/` layout; here the same files are under `docs/r1/`.

**The plan and its state**
- `docs/r1/PLAN.md`: §1–§9 for the question and the claims, and all of §10. The rows dated 3 and 4 November control. Read in particular:
  - the R1-BX rows (benchmark expansion);
  - R1-MAIN-PROPOSER;
  - R1-BX-D8 (aggregate gate) and R1-BX-D10 (Track S fallback);
  - R1-BX-D14 (dates);
  - R1-T1-HOREKA, R1-SERVER-AGENTS-TWO and R1-HOREKA-RUNBOOK;
  - R1-EXAM-*.
- `docs/r1/RUNBOOK.md`: the phases A–E, Track G, Track S, Track P and Track X, and the gates.
- `docs/r1/STATUS.md`: the entries of 3–4 Nov.
- `docs/r1/TECH_ROUTE.md`.

**The parts the comment is about**
- C3, the single-step belief and the gate: `docs/r1/C3_DESIGN.md`.
- The offline environment, which terminates after one step: `r1/c3/env.py`, plus `r1/c3/control.py`, `r1/c3/prior_model.py`, `r1/c3/rules.py`.
- Track S, the sequentiality screen:
  - `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` (design rev 7.x);
  - `docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` (rev 3.3);
  - `docs/r1/proposals/TRACK_S_GPU_EXTENSION_20261104.md`.
- Track P, post-training of the decision model: `docs/r1/TRACK_P_POST_TRAINING.md`.
- The theory: `docs/r1/theory/T1_MODEL.md` to `T5_SIMULATION.md`. T4 covers the feedback proposer, T3 and T5 the simulations.
- The benchmark expansion: `docs/r1/proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md`.
- Questions still open for the author: `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md`.
- The manuscript draft: `papers/r1/main.tex` and `papers/r1/sections/*.tex`.

**The runbooks of the three threads (§4)**
- `docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md` (rev 3.3).
- `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md` (rev 3.3).
- `docs/r1/prompts/HOREKA_RUNBOOK_20261104.md` (rev 3, accepted). Read it on branch `docs/runbooks-04nov`, where it is at its latest head.
- `docs/r1/reports/MAC_HANDOVER_20261104.md`: the Mac-local agent's task state, M1–M15.

## 2. Cost and timeline

**Dates (R1-BX-D14; targets)**

| Date | What |
|---|---|
| ≈ 8 Dec 2026 | **B.7**, the C3 gate, on CPU and T1 labels with the aggregate criterion. The chat session judges 8 Dec with T1 labels unlikely (see below); the new date is the author's open item "H1" |
| ≈ 15 Dec 2026 | **Track S fallback** (R1-BX-D10). With no campaign-level result by then, the DAC-reduction argument falls back to the theorem plus synthetic controls |
| ≈ 3 Jan 2027 | **D.3**, the closed-loop deployment |
| 10 Jan 2027 | **Manuscript.** Writing runs in parallel from early December. Venue: ICML 2027 (R1-VENUE-3) |

**Fixed constraints**
- **HoreKa 2 downtime: 23 Nov – 4 Dec.** The HoreKa runbook's submission freeze is 20 Nov at 12:00.
- **HoreKa queue.** On 4 Nov, `gpu-h100` estimates put the start of 1–4 h one-GPU jobs around 11–12 Nov; the queue probe's live estimates moved between 5 and 11 Nov. The real waits are read on 5 Nov (`reports/HOREKA_QUEUE_20261104.md`).
- **The TASL-7 4090** carries Track X B1/B2 (if the author confirms R1-EXAM-HOST-B1B2-TASL7), then Track P. RUNBOOK says Track X must finish by about 15 Nov, or B.5 moves.

**Costs (estimates from the committed documents)**

| Item | Cost |
|---|---|
| Track X B1 | 15 candidates + 3 anchors, about 240 proposals per model; about 2–4 days |
| Track X B2 | About 5 finalists, a few GPU-h each; about 1–2 days. X.7 (the main proposer) is therefore not before mid-November |
| Sweep 2, T0 part (B.1b) | About 6k proposals; LLM part 10–40 h, then audits on deepthought CPUs |
| T1 tier on HoreKa | Budget **400 GPU-h** (author). The draft estimates about 320 GPU-h at K = 6 and 480 at K = 10 for about 8 task nodes, counting run time only, so these are lower bounds. Floors about 2, executions about 8 and audits 30–50 GPU-h per node |
| Track S | Historical plan cap about **79k LLM calls per node**, including tuning, forks (about 150 per node), campaigns and secondaries. About 1–1.5 GPU-days per node on a 4090 over 1–2 calendar weeks. Track S on a 4090: about 0.7 s per call, serial |
| Sweep 1 on one TITAN X | 5,813 proposals in about 11.6 h (about 7 s per proposal of wall throughput) |
| Track P P.3a | At most 60 GPU-h in total (authorization of 27 Oct, amended 4 Nov) |

**Where the critical path is.** The chain is: B1 → B2 → X.7 → HoreKa proposer qualification and pilot (HK4–HK5) → sweep 2 T1 and audits (HK6–HK7) → R1-BX-D8-CONFIRM → B.7. Most of HK6–HK7 will fall after 5 Dec.

## 3. The current plan, in brief

- **Question.** Noisy incumbent-relative acceptance in governed autoresearch loops: can a learned controller decide better than a noise-aware rule, which proposals to execute or keep under noise and a budget?
- **Controllers.**
  - C1/C2: rules and noise-aware rules (A1 constant prior, A2 node-level prior, A2-U history-updated).
  - **C3:** a learned single-step belief about each proposal's audited increment, plus the rule. Its gate is B.7: does the learned prediction beat A2 by the margin on the aggregate criterion?
- **Labels.**
  - Sweep 1, with `qwen2.5-coder:7b` as manager, is the second source.
  - **Sweep 2**, with the Track X pick, thinking off, is the main source: on the 8 CPU nodes (T0), and on GPU task nodes (T1) from autoresearch, MLGym and MLAgentBench.
  - T2 nodes are evaluation only.
  - Audits use K = 10, or K = 6 on T1 once an author row puts it in force. Seeds 7001–7005 are for labels and 7006–7010 for evaluation.
- **Tracks.**
  - **Track X** (proposer exam): Stage A is done and accepted. B1 and B2 select the main proposer (X.7).
  - **Track G:** the T1/T2 real-task tier, on HoreKa 2 H100. It is the critical path.
  - **Track S:** a sequentiality screen, comparing a dynamic-threshold policy with a tuned static one at campaign level, plus the S3a forks and the S4 mechanism diagnostics.
  - **Track P:** post-training of the decision model (belief, action head, R-A/R-B arms, P.3a/P.3b exam). Mostly single-step targets.
  - **Track H:** the DAC interface.
- **Phases.**
  - B: labels, audits, gate.
  - C: C.1 R-A, C.2 DAgger round, C.3 pilot, C.4 A/B, only if B.7 passes.
  - D: D.1 fold retraining, D.3 closed loop, D.4 tables.
  - E: manuscript.
- **The second proposer.** For the closed loop, the author said "用 exam 第二名" (the exam runner-up instead of an API model). It is not yet a PLAN row; R1-BX-D6 still says an API model.

## 4. The three threads and what each does

| Thread | Agent | Hosts | What it does now |
|---|---|---|---|
| **Mac-local** | Mac-local agent (a new agent took over on 4 Nov evening; handover `MAC_HANDOVER_20261104.md`) | none: code, documents, analysis | Integrates documents on `mac-int-20261104`; is the single editor of `r1/exam/`, `r1/scripts/exam_*` and `r1/c3/train/`. Current work: M2 (`x5_rule_v2`, for B1), M3 (b2-repair review), M5 review of `ab74203`, the B1 authorization draft, M10 (HoreKa code: `hk2_submit.py`, `hk2_status.py`, G.2 diff support), M11 (baselines, aggregate gate). Later: M4 (sweep code), M6 (Track S GPU design), M12 (K check), M13 (Track P template), M14–M15 (calibration, D tables) |
| **Operator** | operator agent (`OPERATOR_RUNBOOK_20261104.md`) | TASL-2, TASL-7, deepthought, Ada | O0 census done; O1 Stage A accepted. Next: O2 Track X B1/B2 (on TASL-7 if confirmed), O3 Track S S0.1 re-run on TASL-2, O7 Track P P.3a (TASL-7, after or between B1/B2), O4 B.2 replay and sweep-1 audits (deepthought CPUs, after M3), O5 deepthought dual-card check, O6 sweep 2 T0, O9 A4, O10 Phase C, O11 D.3 |
| **HoreKa** | HoreKa agent (`HOREKA_RUNBOOK_20261104.md` rev 3) | HoreKa 2 only, through the `agent`-partition tunnel | The whole T1 tier: HK0 queue facts (5 Nov) → HK1 environment → HK2 ports and smoke → HK3 census and noise floors → HK4/HK4b proposer qualification and D28 liveness (after X.7) → HK5 pilot → HK6 sweep 2 T1 → HK7 audits and merge. Budget 400 GPU-h. The author ruled at 18:00 that the agent may submit GPU jobs from the agent node, pending NHR@KIT's reply |
