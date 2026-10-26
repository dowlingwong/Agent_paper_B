# Paper B (route R1) — runbook

Canonical plan: [PLAN.md](PLAN.md). Progress goes only into [STATUS.md](STATUS.md). C3 detail: [C3_DESIGN.md](C3_DESIGN.md).

**Revised 23 October 2026, hosts updated 24 October 2026, Tracks X, H and P added 25 October 2026,** by an AI agent (Claude, coordinating session); AI-assisted, not human review. This revision replaces the 12 Oct execution order (L1–L14, E1–E8, the branch-table headroom gate and the L11 configurator scaffold), which the 18 Oct decisions (R1-C3 route A, the A0–A6 ladder, the C3 gate) and the 22–23 Oct decisions (D21 pool of eight, R1-C3-BASE) superseded. What was done under the old order stays recorded in STATUS. Host assignments marked **(proposed)** need an author decision before work depends on them.

> **Venue changed to ICML 2027 (author, 24 Oct).** The deadline is not yet announced; a projection from the previous cycle puts abstract registration around 16 Jan 2027 and full papers around 22 Jan 2027. Only the venue changed: the plan, the phase targets and the quality bar stay as they are (author, 24 Oct).

## 1. Ground rules (unchanged)

- **Authority.** PLAN.md, this runbook and STATUS.md are the only planning documents. No new plan or decision files outside `docs/r1/`. Phase-end reviews go to `docs/r1/reviews/`. Archived files are history, never instructions.
- **Decisions.** Only the author decides. A decision is a dated row in PLAN §10 before work depends on it. Agents propose and never adopt.
- **Evidence runs.** A run is evidence when its outcomes feed a claim (the C3 label sweeps used for the gate, the online deployment). Each needs an authorization note `docs/r1/authorizations/<phase>_<date>.md`, written and committed by the author. Engineering runs and pilots are labelled ENGINEERING_ONLY or PILOT and never quoted as results.
- **Pre-declaration.** The C3 gate is fixed (PLAN §10, 18 Oct). Online-deployment contrasts, sample sizes and the analysis script are committed with a hash before any outcome exists.
- **Honesty.** AI-assisted work is labelled. A box is ticked only when its acceptance condition was checked. A stopped run is reported as stopped.
- **Repos.** Harness work on branch `r1` of `autoresearch_harness`; this repo pins the harness commit of every run. Never force-push, rewrite pushed history or delete ledgers.
- **Reviews.** One fresh-session review at the end of each phase plus one correction round.
- **Language.** All written documents in English.

## 2. Roles (unchanged)

| Role | Who | Does |
|---|---|---|
| Author | Dowling Wong | Decides; writes authorization notes; final read |
| Implementation agent | Any session given a phase prompt | Executes tasks, runs checks, updates STATUS |
| Coordinator | Planning session (Claude) | Writes prompts, reviews, keeps PLAN/RUNBOOK current |

## 3. Compute hosts (updated 23 Oct)

| Host | Hardware | Access | Use for |
|---|---|---|---|
| **Mac** | MacBook Pro, M1 Max, 64 GB unified memory | Exclusive | Code, docs, tests, theory, analysis, offline evaluation of non-LLM arms (A0–A3), CPU pilots with the scripted proposer, fetching OpenML caches (networked). **LLM and small-model work only as a last resort** (R1-COMPUTE revised 24 Oct): allowed only when no other host can do the step, with the author's approval per use. The hardware can run LoRA SFT or single-token RL for ≤ 4B models (MLX / MPS). |
| **deepthought** (deepthought2.etp.kit.edu, code under `/ceph/dwong/`) | Many CPU cores, large RAM and storage; 4 × TITAN 12 GB | **Exclusive** | Long LLM-backed collection that must not be interrupted: C3 label sweeps (one pinned manager per TITAN, CPU workers and audits on the cores), liveness checks, A4 zero-shot queries, the aggregation round, online deployment of arms that fit 12 GB. |
| **zhixu portal** | 1 × RTX 4090 24 GB | **Exclusive** | Small-model training and evaluation ≤ 4B: A5 SFT and A6 GRPO for Kev, StartLux and Laya; online arms whose small LM does not fit beside the manager on a TITAN. |
| **zhixu experiment** (Ada, `ucrtasl`, SSH alias `experiment_zhixu`) | 8 × RTX 6000 Ada 48 GB | **Shared; jobs may be interrupted** | Overflow and parallel capacity only, for jobs that are resumable in short segments (checkpoint per campaign root or per training epoch): extra sweep shards, the C4 debiased-memory A/B, replicate seeds. Never the only copy of a long, un-resumable job. |

Host rules:

- **GPU co-tenancy (13 Oct)** applies on shared cards: free memory ≥ our measured footprint + 2 GiB; never disturb other users' jobs; CPU fallback, OOM or losing the margin is a STOP for that step.
- **Paper A coordination (19 Oct):** no Paper B GPU launch on zhixu experiment while a Paper A campaign there waits for a card.
- **Interruption on zhixu experiment:** every job there must resume from its last completed unit without re-running completed units. An interrupted unit is re-run whole, never patched. The run log records each interruption.
- **One manager backend per table (D6, D15):** all proposals of one labelled table come from one host type with the pinned manager digest. Mixing hosts within one table needs an author decision.
- **Proposer quantization (24 Oct; size rule replaced 25 Oct):** manager models run at Q4_K_M. The 24 Oct size ceiling (27B dense to 35B-A3B MoE) is replaced by the fit rule of R1-EXAM-POOL (Track X): any model the pinned llama.cpp build serves fully on one RTX 4090 at Q4_K_M with 16k context and q8_0 KV cache. Digest and quantization are pinned and reported for every run. Training stays BF16 LoRA (QLoRA only if needed).
- **Precision:** the TITANs are an older generation; check bf16 and kernel support (Qwen3.5's linear-attention layers) before planning any training there. Training defaults to zhixu portal.

## 4. Where we stand (23 Oct, from STATUS)

Done (ENGINEERING_ONLY or PILOT, none is evidence):

- Harness hooks, actions, D24–D28 proposer fixes, liveness gate, dedicated Ollama instance per batch, sweep runner with Paper A gate, desktop dry run.
- Theory T1–T4 (Propositions 1–10) and T5 simulation; Monte-Carlo checks of Propositions 7 and 9.
- Common 30-seed noise floor over ten nodes: D21 pool = 8 qualifying nodes, two borderline (digits_mlp, openml_blood_transfusion).
- C3 offline pipeline: labels, features, audits, arms A1–A3, offline evaluation, gate at the declared g. Pilot (166 proposals): gate not passed; sample too small for a decision.
- C1 pilot duplicate rate: memory-on duplicates 51–66 % of proposals.
- C4 DI diagnostics: undetermined in both memory modes.

## 5. Execution plan

Host is where the step runs.

### Immediate queue (24 Oct)

Order of the Phase A steps, with what each waits for. Steps on the same line can run in parallel.

1. ~~Author decisions A.1, A.3, A.6 host choice~~ adopted 24 Oct; PLAN §10 rows and C3_DESIGN §5 committed 24 Oct.
2. Code, in parallel: A.4 (sweep-index adapter), A.5 (resumable sweep), A.8 (Ollama watchdog). Mac. Also A.1b: measure `openml_climate` at 30 seeds (CPU only, scripted proposer). Mac or deepthought CPUs.
3. Port and check the sweep config on deepthought (A.6), after 2. Mac → deepthought.
4. digits_mlp repair, then D28 liveness on eight nodes (A.7), after 3. deepthought.
5. Authorization note for sweep 1 (A.9), after 4. Mac (author).
6. Sweep 1 starts (B.1). deepthought.

A.2 (T4 proof check) runs alongside, on the Mac; it gates the manuscript, not the sweep.

Added 25 Oct: Track X (proposer exam, zhixu portal) starts with X.1–X.2 once A.10/A.11 are done and must finish before B.5 uses the same card; Track H (DAC interface, Mac) and P.0 (post-training spikes, zhixu portal) run during Phase B and must be done before C.3.

### Phase A — Close out preparation (target ~1 Nov 2026)

| # | Step | Host | Done when |
|---|---|---|---|
| A.1 | ~~Author accepts the common 30-seed run as the C1 noise-floor table~~ **Adopted 24 Oct** | Mac (author) | PLAN §10 row |
| A.1b | Measure the reserve node `openml_climate` under the same 30-seed protocol (D21 rule) as backup for the pool of eight | Mac or deepthought CPUs | Verdict appended to the noise-floor report |
| A.2 | Author checks the T4 proofs (Propositions 6–10) | Mac (author) | Note in `docs/r1/theory/`; STATUS entry |
| A.3 | R1-C3-BASE **adopted 24 Oct**: commit the PLAN §10 row; update C3_DESIGN §5 (A5/A6 base models: Kev-0.8B/4B, StartLux-Decision-v1.1 0.8B/2B/4B, Laya 421M) | Mac | Row and design text committed |
| A.4 | Adapter from the sweep index to `dataset.build` | Mac | Unit test on the 19 Oct pilot table |
| A.5 | Make the sweep resumable per campaign root (needed for any zhixu experiment shard); fault-injection test of an interruption mid-campaign | Mac | Desktop dry run resumes without re-running completed roots |
| A.6 | Port the sweep config to deepthought (**adopted 24 Oct: deepthought is the primary sweep host; no mixing hosts within one table**): one manager per TITAN, models path, port, OpenML caches present | Mac → deepthought | `--check-config` passes on deepthought |
| A.7 | digits_mlp proposer repair, then D28 LLM liveness on all eight nodes | deepthought | Liveness manifest; digits passes or the author decides |
| A.8 | Ollama SIGTERM: add runner watchdog and logging so a lost runner is detected and the unit re-run | Mac, then deepthought smoke | Smoke with an injected runner kill recovers |
| A.9 | Author: authorization note for the first C3 label sweep | Mac (author) | Note committed |
| A.10 | Port from Ollama to llama.cpp (R1-INFER-LLAMACPP, 25 Oct): `llama-server` instance manager, GGUF sha256 + build-commit pin, health/offload checks, watchdog, fake server for dry runs, configs; check the harness `llamacpp` provider (OpenAI-compatible base URL with `/v1`, D26 seed pass-through) | Mac (code) | Dry runs and resume/watchdog tests pass on the llama.cpp path |
| A.11 | Build llama.cpp on the sweep host and run a one-token GPU load probe of the pinned GGUF (TITAN X: compute 5.2, driver 525, so build against a CUDA toolkit the driver supports, `CMAKE_CUDA_ARCHITECTURES=52`) | deepthought (author's terminal) | Probe shows full GPU offload, or the author picks another host |

### Phase B — C3 labels and the offline gate (target ~22 Nov 2026)

| # | Step | Host | Done when |
|---|---|---|---|
| B.1 | C3 label sweep 1: 8 nodes × 18 instances × 2 memory modes × W = 20 (≈ 5,800 proposals) | deepthought only (24 Oct: no mixing hosts within one table) | Manifest; completion or a documented STOP |
| B.2 | Fresh-seed audits, K = 10 (5 label + 5 evaluation seeds) | deepthought CPUs | Labels for every non-inert, non-duplicate proposal |
| B.3 | A0–A3 offline (rules, constant prior, LightGBM, NGBoost) | Mac | Offline one-step values with CIs |
| B.4 | A4: manager zero-shot typed questions; isotonic calibration on dev | deepthought | Calibrated A4 table |
| B.5 | A5 SFT, soft-label cross-entropy on 12 bin tokens: Kev-0.8B, Kev-4B, StartLux 0.8B / 2B / 4B (LoRA r = 16); Laya 421M (encoder rung) | zhixu portal | Log score, calibration, offline value per model |
| B.6 | Extend labels toward 8–10k: second sweep (extra OpenML / MLP nodes, second manager model for diversity) | deepthought (+ zhixu experiment shards) | Second manifest |
| B.7 | **STOP — C3 gate (author):** A3 or A5 beats A2 by ≥ δ_n on ≥ 2 nodes, lower 95 % bound > 0 | Mac (author) | PLAN §10 row: pass → Phase C; fail → C3 reported as the measured negative, C1 + C2 carry the paper |

### Track G — Harder benchmarks (added 24 Oct; runs alongside Phases B–D)

Adopted (author, 24 Oct): Karpathy's autoresearch, 1GC-7RC (2026) and MLGym (Meta) join the benchmark set. **Their role is proposed, not adopted:** evaluation and transfer nodes, because one audited proposal on a 5-minute GPU run costs about 100 GPU-minutes, too much for full-scale labels. C3 arms trained on the CPU pool are tested on them without retraining (extends H2b).

| # | Step | Host | Done when |
|---|---|---|---|
| G.1 | Adapters: check and update the harness autoresearch node (5-min `train.py` runs, val_bpb); 1GC-7RC light tasks (T1 TinyShakespeare, T5 Forest Cover, T6 ETTh1, T7 AG News; `train.py` + locked `prepare.py`); MLGym light tasks | Mac (code) | Smoke campaign per node |
| G.2 | Container check for MLGym: Docker or Podman on deepthought (pending with the admin) or zhixu portal | deepthought / zhixu portal | MLGym task runs, or MLGym dropped with a reason |
| G.3 | Noise floor on the new nodes: determinism, σ_n for training and split seeds, run cost (fewer seeds than the CPU pool if cost requires; declared in advance) | zhixu portal (autoresearch also on zhixu experiment, resumable) | Rows added to the noise-floor report |
| G.4 | Author: role of the new nodes (evaluation/transfer only, or small label sets) and their audit budget | Mac (author) | PLAN §10 row |
| G.5 | Transfer evaluation of A1–A6 on the new nodes with a reduced, pre-declared audit budget | zhixu portal (+ zhixu experiment, resumable) | Transfer table, part of D.1 |

### Track X — Proposer candidacy exam (appendix; added 25 Oct)

**Pool and host adopted by the author (25 Oct, R1-EXAM-POOL); protocol X.2–X.6 adopted with two amendments (26 Oct, R1-EXAM-PROTOCOL).**

**What exists and why it is not reused as evidence.** The model "exam" the author remembered is the Round-7 candidacy exam of the Paper A repo (`agent-checkpoint-intervention`: `paper/appendices/C_protocol.tex`, subsection "Model candidacy: the completed Round-7 exam"; `round10/CANONICAL_EXAM_RESULTS.md`; evidence `evidence/round7-blackwell-grouped/run/`). Its code also survives here as `archive/old_b_2026-10-09/code/experiment_scaffold/src/causal_branch/round5_titan_exam.py` (protocol `round5_titan_compact_exam_v1`, Stage A compatibility + Stage B 30-root exam, hard gates, score `100·(0.5Y + 0.15C + 0.15S + 0.1T + 0.1R)`, selection by successes per GPU-hour). It completed on 4 Sep 2026: twelve candidates on two leased 48 GB Ada cards; three cleared the 12/30 gate; Devstral Small 2 24B was selected provisionally; all pairwise success differences among the three had bootstrap intervals covering zero. It cannot answer R1's question:
- **Different task.** A Pi coding agent writes an artifact and calls `submit_candidate` on a tabular task adjudicated on 40 hidden rows. R1's manager emits one structured `ManagerProposal` per trial in a governed keep/discard loop under noise. Tool-use competence is not proposal quality.
- **Confounded by interface conformance.** Several low rows were submission-format failures, not task failures (Qwen3.6-35B-A3B 2/30 valid submissions, Qwen3.6-27B 5/30, Muse Glimmer 7/30), under one frozen runtime with thinking disabled (`ENABLE_THINKING = False` in the protocol).
- **Statistically an eligibility screen only.** 30 roots, one draw; the archived Paper B limitations section says the screen "licenses no ranking of models".
- **Different hardware.** Two-card layer split, not one 4090.

Reused: the machinery (artifact pinning and quantization/licence blockers, Wilson intervals, paired template bootstrap, occupancy and contamination handling, frozen selection rule before data). Not reused: its numbers or its pool verdicts.

**Purpose.** (i) Choose, by a rule frozen before data, the strong proposer for the D22 deployment check and the second manager for B.6. (ii) An appendix table of how proposer choice moves the C3-relevant quantities (duplicate and no-op rates, audited proposal increments, final audited Y). Exam campaigns are never C3 labels.

**Pool (author, 25 Oct).** Every candidate below enters Stage A. TeichAI/Qwen3.6-27B-Claude-Opus-Reasoning-Distill-v2 is excluded by the author.

| Group | Candidates |
|---|---|
| Dense ≥ 20B | Qwen3.8-27B; Qwen3.6-27B; Gemma 4 31B; Muse Glimmer 30B; OLMo 3.1 32B Instruct (Think variant as a sensitivity row); Devstral Small 2 24B |
| MoE | Qwen3.6-35B-A3B; Gemma 4 26B-A4B; Nemotron 3.5 Lightning 30B-A3B; GLM-4.7-Flash (30B-A3B); LFM2.5-24B-A2B; Laguna XS 2.1 (33B-A3B); Ornith-1.0-35B-A3B; Qwen3-Coder-30B-A3B-Instruct; gpt-oss-20b (native MXFP4, declared exception to Q4_K_M) |
| ≤ 14B | Qwen3.5-9B; Gemma 4 12B; Ornith-1.0-9B; Ministral 3 14B |
| Community post-trained | rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled; skiboyvv/Qwopus3.6-27B-v4 (both labelled "community fine-tune, data provenance not audited" in every table) |
| Anchors (not candidates) | random-valid proposer; scripted stand-in; `qwen2.5-coder:7b` (D15, current manager) |

**STOP 0 amendment (author, 26 Oct; PLAN R1-EXAM-ORNITH):** Ornith-1.0-31B is removed because it is not publicly released, with no substitute. The effective pool has 21 candidates and 3 anchors. Ornith-1.0-35B-A3B maps to `ornith-ai/Ornith-1.0-35B` (MIT); check vendor `ornith-ai/Ornith-1.0-35B-GGUF` Q4_K_M first in Phase 2. Storage is `/home/dowling/exam-x/{models,work}` (author correction of the initial `/ceph` paths), with a 100 GB available-space STOP floor. Transfer code by SSH pushes from the Mac to bare repositories under `/home/dowling/exam-x/work/`, with no GitHub credentials on portal. User-level uv/Python installation is permitted under `/home/dowling`, without sudo or system Python changes; record versions. Licence approval and exact scope are recorded in PLAN §10 R1-EXAM-LICENCES.

**Fit rule (author, 25 Oct; replaces the size ceiling of R1-PROPOSER-QUANT; amended 25 Oct, R1-EXAM-FIT).** Admissibility is **estimated from the Q4_K_M GGUF** (author: Q4_K_M is the baseline for the fit estimate): file size + KV cache at the declared context (from `config.json`: 2 × attention layers × KV heads × head dim × context × 1 byte for q8_0; sliding-window layers counted at their window; DeltaNet/Mamba layers carry a fixed state) + 1.5 GiB for compute buffers ≤ 23.5 GiB. The estimate is confirmed by the X.2 probe (full offload, prefill to the declared context); a model that fails the probe is excluded with its measured numbers. **Declared context: 32,768 tokens (author, 26 Oct, R1-EXAM-CTX).** Measured 25 Oct from the pilot `llm_call` records: manager prompts are 645 tokens (memory off, DT4) and at most 1,345 tokens (memory on, W = 20, rerun-2), completions at most 115 tokens. So 8k–16k is ample for the CPU pool; 32k is for thinking budgets and the Track G nodes, whose prompts carry code. A model that fits at 16k but not at 32k is admitted for the CPU-pool rows only and flagged. Q4_K_M stays the quantization; gpt-oss-20b runs at its native MXFP4.

| # | Step | Host | Done when |
|---|---|---|---|
| X.1 | Registry: per candidate HF repo @ revision, licence, GGUF sha256, quantization source per R1-QUANT-SOURCE (vendor Q4_K_M, else bartowski imatrix Q4_K_M; 26 Oct), chat-template source, thinking policy, vendor sampling. Port `quantization_blockers` / licence blockers / Wilson / paired bootstrap from the archived `round5_titan_exam.py` into `r1/exam/` (tests carried). | Mac (code) | Registry committed; ported tests pass |
| X.2 | **Stage A (mechanical; no worker runs).** Per candidate: full-offload + prefill probe at the declared 32,768 context (fit rule; a model that fails it is re-probed at 16,384 and, if it passes, admitted for CPU-pool rows only and flagged); template check (llama-server `--jinja` render vs the HF template on 5 fixed prompts, byte-equal); 50 frozen manager prompts replayed from real memory-on ledgers across ≥ 4 nodes → `ManagerProposal` parse rate ≥ 0.95 and active-key validity rate reported; D26 seed reproducibility (two calls, identical output at temperature 0.2); latency p50/p95 and tokens per proposal. Parse rate is reported twice: free generation (descriptive) and llama-server `json_schema` decoding of `manager_proposal/v1`, which exam and sweeps both use (author, 26 Oct, R1-SCHEMA). Failure classes kept apart: offload, template, parse, timeout. One template repair per model is allowed, declared before Stage B. | zhixu portal | Stage A table; excluded rows carry a class and reason |
| X.3 | **Discrimination check with anchors** on the X.4 design: random-valid < scripted on audited mean proposal increment, and `qwen2.5-coder:7b` reproduces its pilot duplicate rate within CI. If the exam cannot order the anchors, STOP: it has no discriminating power. | zhixu portal + CPU | Anchor table |
| X.4 | **Stage B1 (screen, all admissible candidates).** Nodes: three D21 nodes (proposed: `digits_mlp` if D28 passes, else `tabular_mlp`; `openml_credit_approval`; `openml_ionosphere`). Exam-namespace instance seeds 9001–9004 (never used by any sweep), W = 20, memory `append_only_summary`, `"vary"` split, temperature 0.2 + D26 seed. Thinking (amended 26 Oct): thinking off is the primary mode for every model that can switch it off; those models also run thinking on (2,048-token budget) on one node, and the mode with the higher audited μ̂ is used in B2; always-thinking models run with a 2,048-token budget. After each proposal one charged side query asks the model for P(Δ > 0) and P(no effect) of its own edit (the A4 question), scored against the audit. Audits: each non-inert, non-duplicate proposal on K = 4 fresh seeds (9101–9104, disjoint from 7001–7010). | zhixu portal (manager) + CPU workers | Manifest per candidate; completion or STOP |
| X.5 | **B1 analysis and finalist rule (frozen before X.4 starts, committed with a hash).** Per candidate: valid-proposal rate, novelty (D28), no-op and duplicate rates, invalid-run rate, audited mean proposal increment μ̂ and P(Δ > 0), dispersion of audited increments (the input to T4 Proposition 7's bound), A4 log score and calibration, s/proposal, GPU-h; cluster bootstrap by instance. Eligibility = Stage A pass + D28 criteria. **Finalists:** top 4 by μ̂, plus the best model of any family absent from them (≤ 5). μ̂ is the ranking quantity because it is resolvable here (≈ 80–110 audited proposals per model after duplicates, rough se ≈ 0.001 on `digits_mlp`; corrected 26 Oct) while final Y is not (rough se ≈ 0.002 with 12 instances). | Mac | B1 report |
| X.6 | **Stage B2 (finalists, power-planned).** Final audited Y (K = 10, seeds 9201–9210) on the three nodes with fresh instances 9011+, the number of instances fixed from the B1 variance before B2 starts; plus one Track G node only if G.1 and G.3 are done, the node runs on zhixu portal beside the manager within the fit rule, and the author adds it; otherwise transfer to Track G nodes stays in Track G (G.5). Top 3 also rerun once with thinking off where possible. | zhixu portal only (R1-EXAM-HOST) | B2 report `docs/r1/reports/PROPOSER_EXAM_<date>.md` |
| X.7 | **Author, by role:** (a) **D22 strong proposer** = best B2 Y (ties → lower GPU-h); (b) **B.6 second manager** = the finalist whose proposal distribution (edited key and step-size distribution, declared distance) differs most from `qwen2.5-coder:7b` among those that fit the B.6 sweep host; if none fits a 12 GB TITAN, the second sweep's host changes (R1-SWEEP-HOST: one host type per table); (c) **appendix:** C3 premises (rule-skippable share, increment dispersion, A4 calibration) against proposer strength. If the anchors and the finalists do not differ on any C3 quantity beyond CI, the appendix reports that null and B.6 chooses by cost. | Mac (author) | PLAN §10 row |

Cost and order: Stage A ≈ 10–15 min per model; B1 ≈ 240 proposals per model (+ the non-thinking node), 0.3–3 GPU-h depending on speed and thinking; B2 ≈ 5 models × a few GPU-h; ≈ 3–5 days in all. The 4090 is also the B.5 training card, so Track X must finish by ~15 Nov or B.5 moves. X.1–X.2 start after A.10/A.11 (llama.cpp path).

**Execution:** one agent with SSH access to zhixu portal follows `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` (host facts, code gaps, downloads, Stage A, B1, B2), with a STOP after every phase (R1-EXAM-RUNBOOK, 26 Oct).

### Track H — DAC control interface for the learned prior (added 25 Oct; plan adopted by the author, R1-DAC-INTERFACE)

**What exists (harness `r1`, this repo `r1/`).** E0/E1/E2 hooks with `Controller.decide(view, mask) -> ControlDecision` and leak-guarded `ControlView`; actions stop, demote, skip, revise, verify; `control_decision` events with input hash; keep rule `bayes_threshold/v1` with a `KeepPriorProvider` (constant `KeepPrior` or a callable of the view) at E2; verify response `posterior_mean/v1`; the `llamacpp` provider. Offline: `r1/c3/features.py` builds features by `replay_campaign` over ledgers; `r1/c3/rules.py` holds `execute`, `keep`, `decide(π, μ, τ, σ, g, Δ̂)`; `r1/c3/arms.py` holds ConstantPrior, RulesPrior, LGBMPrior.

**Gap.** No online prior model; the E1 skip is not driven by (π, μ, τ); online features are not guaranteed equal to the offline replay; no small-model serving; no environment wrapper. C.3 (online pilot) assumes all of these.

| # | Step | Host | Done when |
|---|---|---|---|
| H.1 | `PriorModel` protocol (`r1/c3/prior_model.py`): `forecast(features) -> Forecast(probs[12], version, digest, latency_s)`; moments via `labels.moments`. Implementations wrap the existing arms (A1 constant, A2 rules, A3 LightGBM/NGBoost) and add A4 (manager typed questions + isotonic map) and `SidecarPrior` (A5/A6). | Mac | Wrapped A1–A3 reproduce `offline_eval` numbers on the 19 Oct pilot table exactly |
| H.2 | One featurizer for both paths: `features_from_view(view, node_ctx)`; `dataset.build` calls it through the replay. | Mac | Replaying every pilot campaign, the online-style features at each E1 hash-equal the dataset rows; leak test (no audit, sibling or future fields reachable) |
| H.3 | `RuleController(prior, sigma_node, tau_node, g)` implementing `decide()`: at E1 apply A2 rule skips first (logged as such), then `rules.execute` → skip / continue; cache the forecast per trial and serve the same (μ, τ, σ) to E2 through `KeepPriorProvider`, so E1 and E2 use one forecast. Every decision records probs, π, μ, τ, t*, V, g, prior version and digest. All arms A1–A6 differ only in the `PriorModel` passed in. | harness `r1` + `r1/` | Unit tests; A1 through `RuleController` equals the index-policy arm on a scripted campaign |
| H.4 | Skip semantics: a skipped trial spends no worker run, counts its LLM call, and is credited by the 22 Oct run-accounting row. **Decided 25 Oct (author, R1-SKIP-DISPLAY):** the manager's memory shows one line for a skipped proposal, "skipped by the control plane: predicted no gain", with no metric. This changes the proposal law, so it is recorded in every campaign manifest and is part of the DI question (C4). | harness `r1` + `r1/` | Memory-summary test: the line appears, no metric leaks; manifests record the display version |
| H.5 | Sidecar service `r1/c3/serve.py`: loads base + LoRA adapter + head (sha256-pinned), `POST /forecast` → 12 probabilities; timeout 1 s → fall back to the A1 prior and log `prior_unavailable` (never crash the campaign); a fake sidecar for dry runs. Co-residency: ≤ 2B models beside the manager on a TITAN, 4B on zhixu portal. | Mac (code); deepthought smoke | Fake-sidecar dry run; timeout fallback test |
| H.6 | Accounting: A4 queries count against the LLM-call cap; sidecar calls count only compute; latency descriptive (13 Oct rule). | Mac | `matching_report` shows equal W and LLM cap across arms |
| H.7 | Direct-action arms through the same `decide()`: AWR-MLP (Harness-MDP style), LLM self-control (`r1/llm_control.py`), hybrid (prior decides whether, LLM decides how). `matching_report` extended to identical instances, W, LLM cap and information set. This is the three-way comparison of PLAN D.2. | Mac | Report on a dry run |
| H.8 | Environments (`r1/c3/env.py`, Gymnasium API): `OfflineBanditEnv` over a labelled table (context = proposal features; action = bin; reward r = Δ_audit·keep − g·execute under the rules), used by Track P; `OnlineCampaignEnv` (DACBench-style instance set over the harness) built only if C4 finds a material DI violation (A7). | Mac | OfflineBanditEnv reproduces offline one-step values |
| H.9 | End-to-end dry run: fake llama-server + fake sidecar, 2 nodes, arms A0–A6 (A5/A6 stubbed), interruption and resume, `matching_report` passes. | Mac → deepthought | Dry-run manifest |
| H.10 | Fresh-session review + one correction round; author accepts. Must be done before C.3. | — | Review in `docs/r1/reviews/` |

### Track P — Post-training pipeline for A5/A6 (added 25 Oct; proposal)

**Facts checked 25 Oct (repo pages; to be confirmed by P.0).**
- **Kev** (`jaredpalmer/kev`, Apache-2.0): rank-16 LoRA (attention, MLP and DeltaNet projections) plus a pointer head scoring each option's `</opt>` state against the question's `<decide>` state; on Qwen3.5 hybrid bases each question runs as its own row; trainer `python -m kev.train` on JSONL with one hard `label` per question, cross-entropy, `--init_from` a released adapter (lr 2e-5 suggested). **No soft labels and no RL code.** Kev-0.8B trains in bf16 on a 4 GB GPU.
- **StartLux-Decision v1.1** (`StartLuxLabs/StartLux-Decision`; code Apache-2.0, weights CC BY-NC 4.0): Instant models answer in one forward pass with **bidirectional attention over the prompt** (served through a vLLM plugin); **no training code is published**; AutoThink RL is only described in its report. R1-C3-BASE's statement that StartLux "fits TRL GRPO directly" is therefore unverified.
- **Laya** (`NandhaKishorM/laya`, Apache-2.0): ModernBERT-large encoder, 421M, 1,024-context typed-decisions checkpoint; fine-tuning via `notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb` and `notebooks/laya_finetune_typed_decisions_mps.py` ("RLCD": RL against strictly proper scoring rules), temperature calibration per option count. Soft-label support not documented.

| # | Step | Host | Done when |
|---|---|---|---|
| P.0 | **Spike per base (≈ 1 day each):** load, forward one 12-option question, attach LoRA, 100-example toy SFT with soft targets, save/reload, sha256, compare probabilities before/after reload. StartLux must show a training forward with the correct bidirectional prompt mask in plain transformers; if it cannot, StartLux stays an inference-only zero-shot rung and the author decides (R1-C3-BASE amendment). | zhixu portal | Spike report per base |
| P.1 | **Control base (proposed addition):** Qwen3.5-0.8B-Base and -4B-Base + LoRA r = 16, 12 reserved bin tokens read from the LM head at the last position. Same base as Kev, so A5(Kev) − A5(control) isolates Kev's decision pre-training; it is also the guaranteed-trainable fallback. | zhixu portal | Author adopts or declines |
| P.2 | **One `DecisionModel` adapter, one training loop** (`r1/c3/train/`, PyTorch + PEFT; TRL optional): each family exposes `logits[12] = f(x)` (Kev pointer head; StartLux option readout; Laya head; control LM-head tokens). Shared serialisation (one text template, ≤ 1,024 tokens for Laya, fixed bin names and order; an option-order permutation test as a diagnostic for the pointer heads). | Mac (code) + portal | Same toy batch trains on every family |
| P.3 | **A5 SFT:** soft-label cross-entropy (proper log score) on the B.2 labels; LoRA r = 16, lr 2e-5 from released adapters, early stop on dev log score; temperature / isotonic recalibration on dev; select by log score and calibration of P(Δ > 0) and π, then offline one-step value. Kev's trainer is patched (or bypassed via `kev/model.py`) to accept soft targets. | zhixu portal | A5 table (B.5) |
| P.4 | **A6 decision-focused stage** (only after B.7 passes): with 12 actions the objective J(θ) = Σ_b q_θ(b|x) r(b,x) − β·KL(q_θ ‖ q_SFT) is computed **exactly**; GRPO (K = 8, group-mean baseline) is run as the RL estimator and checked against the exact gradient (cosine ≥ 0.95 on held-out batches); smoothed-rule loss as the comparator optimiser. Track ECE and log score every epoch; stop if calibration degrades beyond a tolerance declared in advance. Report the fraction of zero-variance groups. Deploy the greedy bin. | zhixu portal | A6 vs A5 offline, located where T4 §7 predicts |
| P.5 | Pins: base revision, adapter + head sha256, calibration map, training seed, data-manifest hash; every A5/A6 arm served by H.5 from these pins only. | — | Pin file per arm |

**Labels (how they are solved).**
1. **Source:** sweep 1 (B.1, ≈ 5,800 proposals on 8 nodes × 2 memory modes, one pinned manager, one host type).
2. **Audit (B.2):** each non-inert, non-duplicate proposal and its incumbent on K = 10 common fresh joint seeds; seeds 7001–7005 give the **training label**, 7006–7010 the **evaluation value**. Never mixed: the 19 Oct pilot gate "pass" came from sharing them.
3. **SFT target:** the soft label p_b = ∫_bin N(Δ_audit, se_audit²) on z = Δ/σ_node (`r1/c3/labels.soft_label`); no-ops → one-hot no-op bin by rule; duplicates excluded (their result is known).
4. **A6 reward:** r = Δ_audit(label seeds)·keep − g·execute, with keep and execute from the rules applied to the bin and the logged Δ̂; g = 0.1 σ_node (22 Oct). Offline evaluation uses only the evaluation seeds.
5. **Splits:** by instance seed (train/dev/test) plus leave-one-node-out; never by trial.
6. **Volume:** ≈ 1/3 of proposals are non-inert, so ≈ 2,000 labels from sweep 1; B.6 (second sweep, second manager) and the D20 pool extension target 8–10k.
7. **Label noise:** carried in se_audit; K raised on proposals near t*.
8. **Covariate shift:** one DAgger-style aggregation round (C.2) under the deployed tabular arm.

**Hardware.** All A5/A6 training on zhixu portal (4090 24 GB): ≤ 4B LoRA in bf16; nothing on the Mac (R1-COMPUTE). Track X and B.5 share this card (see Track X timing).

### Phase C — Post-training and online pilot (target ~20 Dec 2026, only if B.7 passes)

| # | Step | Host | Done when |
|---|---|---|---|
| C.1 | A6 decision-focused stage on the best A5 models, per Track P.4 (one training loop for all families; exact 12-action objective with GRPO checked against it; smoothed-rule comparator) | zhixu portal | A6 vs A5 offline, located where T4 §7 predicts |
| C.2 | Aggregation round (DAgger-style): collect proposals under the deployed tabular arm, audit, retrain | deepthought | Retrained arms |
| C.3 | Online pilot A1–A5 on qualifying nodes (manager + small LM co-resident: ≤ 2B models on TITANs, 4B on zhixu portal) | deepthought + zhixu portal | PILOT report |
| C.4 | C4: DI test on existing branch pairs (offline) and the debiased-memory A/B on 2–4 nodes | Mac (analysis); A/B on zhixu experiment (resumable, a few GPU-hours) | C4 report |

### Phase D — Transfer, pre-declaration, deployment (target ~28 Feb 2027)

| # | Step | Host | Done when |
|---|---|---|---|
| D.1 | Leave-one-node-out transfer (H2b) for A3, A5, A6, plus transfer to the Track G nodes (G.5) | zhixu portal | LONO and transfer tables |
| D.2 | Pre-declare deployment: contrasts H1–H5, including the three-way comparison (LLM self-control A4 vs trained configurator A5/A6 vs hybrid), instances, sample sizes, matched W and LLM-call cap, analysis script, with hash | Mac (author commits) | Hash in PLAN §10 |
| D.3 | Authorization note; online deployment, 18 instances per node, 2 repetitions, fresh-seed audited Y | deepthought (+ zhixu portal for 4B arms) | Manifests; completion or STOP |
| D.4 | Analysis: contrasts as pre-declared, C1 error rates per arm, T4 bound vs realised gain | Mac | Report |

### Phase E — Write-up (target ~31 Mar 2027)

| # | Step | Host | Done when |
|---|---|---|---|
| E.1 | Manuscript in `papers/r1/` on the ICML 2027 template (venue changed 24 Oct) | Mac | Draft |
| E.2 | Rerun the novelty sweep; read SAGE, FOREAGENT, Beneath the Diff, arXiv 2610.15738 in full before citing specifics | Mac | Related work updated |
| E.3 | Disclosure (ETAAI workshop paper), anonymised harness copy, Paper A cited anonymously | Mac | Package ready |
| E.4 | PLAN §9 quality-bar checklist; ICML 2027 abstract registration and full submission | Mac (author) | Submitted |

## 6. If something fails

| Situation | Response |
|---|---|
| Too few nodes stay live after A.7 (pool < 8) | Author decides: add reserve nodes (e.g. `openml_climate`) or narrow; no silent substitution |
| A sweep unit is interrupted on zhixu experiment | Re-run that unit whole from the last checkpoint; log the interruption |
| C3 gate fails (B.7) | Report C3 as the measured negative with T4 Proposition 7's dispersion bound; C1 + C2 carry the paper |
| A6 does not beat A5 | Report it; T4 §7 predicts where it should and should not |
| LLM self-control (A4) matches the trained models | A finding, not a failure; report under H4 |
| DI strongly violated (C4) | One-step offline values are biased; A7 (online RL) becomes justified, with T4 Proposition 10(b) |
| 4B models do not fit or are too slow | Drop to ≤ 2B for online arms; keep 4B offline only |

## 7. Reporting

Each implementation session ends with a STATUS entry: date; tasks done with commits; checks with results; what is not done and why; decisions needed, phrased as questions for the author.
