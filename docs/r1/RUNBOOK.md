# Paper B (route R1) — runbook

Canonical plan: [PLAN.md](PLAN.md). Progress goes only into [STATUS.md](STATUS.md). C3 detail: [C3_DESIGN.md](C3_DESIGN.md).

**Revised 23 October 2026, hosts updated 24 October 2026,** by an AI agent (Claude, coordinating session); AI-assisted, not human review. This revision replaces the 12 Oct execution order (L1–L14, E1–E8, the branch-table headroom gate and the L11 configurator scaffold), which the 18 Oct decisions (R1-C3 route A, the A0–A6 ladder, the C3 gate) and the 22–23 Oct decisions (D21 pool of eight, R1-C3-BASE) superseded. What was done under the old order stays recorded in STATUS. Host assignments marked **(proposed)** need an author decision before work depends on them.

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
- **Proposer quantization (24 Oct):** manager models run at Q4_K_M; the size ceiling is roughly 27B dense to 35B-A3B MoE (fits the 4090's 24 GB with a few GB left for the KV cache). Digest and quantization are pinned and reported for every run. Training stays BF16 LoRA (QLoRA only if needed).
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

### Phase C — Post-training and online pilot (target ~20 Dec 2026, only if B.7 passes)

| # | Step | Host | Done when |
|---|---|---|---|
| C.1 | A6 decision-focused GRPO on the best A5 models; custom loop for Kev and Laya (pointer / encoder heads), TRL for StartLux; check the GRPO estimate against the exact 12-action gradient; smoothed-rule comparator | zhixu portal | A6 vs A5 offline, located where T4 §7 predicts |
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
