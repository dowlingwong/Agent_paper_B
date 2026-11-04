# Paper B (route R1) — runbook

Canonical plan: [PLAN.md](PLAN.md). Progress goes only into [STATUS.md](STATUS.md). C3 detail: [C3_DESIGN.md](C3_DESIGN.md).

**Revised 23 October 2026, hosts updated 24 October 2026, Tracks X, H and P added 25 October 2026,** by an AI agent (Claude, coordinating session); AI-assisted, not human review. This revision replaces the 12 Oct execution order (L1–L14, E1–E8, the branch-table headroom gate and the L11 configurator scaffold), which the 18 Oct decisions (R1-C3 route A, the A0–A6 ladder, the C3 gate) and the 22–23 Oct decisions (D21 pool of eight, R1-C3-BASE) superseded. What was done under the old order stays recorded in STATUS. Host assignments marked **(proposed)** need an author decision before work depends on them.

> **Current routing and historical rows.** The sweep host is `deepthought.etp.kit.edu` (see `prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md` §1), not the deepthought2 hostname in the older host table. R1-TASL7-TRACKP moves Track P and its listed 4B/LONO work from portal to TASL-7 after the host-equivalence gate; R1-ADA-OVERFLOW permits scoped resumable overflow. R1-INFER-LLAMACPP replaces Ollama for sweep 1. R1-EXAM-CTX sets 32,768 context with the specified 16,384 fallback; R1-EXAM-TRANSFER governs transfer without portal GitHub credentials. Track X and Track P have their own independent review loops. Older rows below are retained as history where they conflict with these later decisions.

> **4 Nov 2026 revision (PLAN §10 R1-BX-D1 … R1-BX-D14, R1-BX-REVISIONS; the author adopted `proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` in full).** These rows control wherever older text below conflicts:
> - **Tiers.** T0 = the 8 CPU nodes (controlled testbed, single-parameter low-interaction condition); T1 = GPU label + evaluation tasks; T2 = GPU evaluation only. Target 12–16 real tasks, ≥ 3 suites (autoresearch, 1GC-7RC, MLGym), ≥ 5 domains. Primary generalisation is leave-one-suite-out.
> - **Track G is the critical path** and starts now (rewritten below). GPU-node census and noise floors start on Ada while Track X holds TASL-2.
> - **Labels on GPU nodes:** fixed step budgets, code-level diffs, one GPU model per table, divergence as its own outcome class; K = 6 only if the sweep-1 subsampling check passes (R1-BX-D3), otherwise K = 10.
> - **Gate:** B.7 uses the aggregate IQM gap closed and probability of improvement with node-stratified bootstrap CIs (R1-BX-D8), on CPU + T1 labels, ≈ 8 Dec.
> - **Cuts:** B.6 cut; Stage D (C.2) one round on 1–2 T1 nodes; R-B optional. A4 is the self-control arm; R-A is "decision-focused fine-tuning".
> - **Additions:** practitioner baselines (Karpathy default, fixed-r + t-test); an information-matched TabPFN comparison in regression mode; an API proposer in closed-loop evaluation only; 1–2 GPU nodes for Track S with a fallback date ≈ 15 Dec.
> - **Dates (targets, recomputed after the T1 pilot):** B.7 ≈ 8 Dec, Track S fallback ≈ 15 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan with writing from early December.
> - **Execution split:** `prompts/MAC_LOCAL_RUNBOOK_20261104.md` (the Claude on the Mac) and `prompts/OPERATOR_RUNBOOK_20261104.md` (the single SSH operator), both revision 3.

> **Venue changed to ICML 2027 (author, 24 Oct).** The deadline is not yet announced; a projection from the previous cycle puts abstract registration around 16 Jan 2027 and full papers around 22 Jan 2027. Only the venue changed: the plan, the phase targets and the quality bar stay as they are (author, 24 Oct).

## 1. Ground rules (unchanged)

- **Authority.** PLAN.md, this runbook and STATUS.md are the only planning documents. No new plan or decision files outside `docs/r1/`. Phase-end reviews go to `docs/r1/reviews/`. Archived files are history, never instructions.
- **Decisions.** Only the author decides. A decision is a dated row in PLAN §10 before work depends on it. Agents propose and never adopt.
- **Evidence runs.** A run is evidence when its outcomes feed a claim (the C3 label sweeps used for the gate, the online deployment). Each needs an authorization note `docs/r1/authorizations/<phase>_<date>.md`, written and committed by the author. Engineering runs and pilots are labelled ENGINEERING_ONLY or PILOT and never quoted as results.
- **Pre-declaration.** The C3 gate is fixed (PLAN §10, 18 Oct; **its criterion is replaced since 4 Nov by R1-BX-D8, confirmed in R1-BX-D8-CONFIRM before any sweep-2 label is analysed**). Online-deployment contrasts, sample sizes and the analysis script are committed with a hash before any outcome exists.
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
| **deepthought** (`deepthought.etp.kit.edu`, code under `/ceph/dwong/`; *4 Nov: may serve the main proposer across two TITANs if the dual-card qualification passes, R1-BX-REVISIONS (f)*) | Many CPU cores, large RAM and storage; 4 × TITAN 12 GB | **Exclusive** | Long LLM-backed collection that must not be interrupted: C3 label sweeps (one pinned manager per TITAN, CPU workers and audits on the cores), liveness checks, A4 zero-shot queries, the aggregation round, online deployment of arms that fit 12 GB. |
| **zhixu portal** (TASL-2) | 1 × RTX 4090 24 GB | **Exclusive** | Track X proposer exam (R1-EXAM-HOST). Until 26 Oct also Track P; Track P moved to TASL-7 (R1-TASL7-TRACKP). |
| **TASL-7** (Tailscale; added 26 Oct) | 1 × RTX 4090 24 GB; driver 580 / CUDA 13.0 | **Exclusive** | Track P: small-model training and evaluation ≤ 4B (spikes, decision-model exam, A5 SFT, A6, R-B, LONO retraining); 4B sidecar arms in C.3/D.3 (R1-TASL7-TRACKP). |
| **zhixu experiment** (Ada, `ucrtasl`, SSH alias `experiment_zhixu`) | 8 × RTX 6000 Ada 48 GB | **Shared; jobs may be interrupted** | *4 Nov (R1-BX-D14): first host of the Track G census and GPU-node noise floors.* Overflow and parallel capacity only, for jobs that are resumable in short segments (checkpoint per campaign root or per training epoch): extra sweep shards, the C4 debiased-memory A/B, replicate seeds. Never the only copy of a long, un-resumable job. |

Host rules:

- **GPU co-tenancy (13 Oct)** applies on shared cards: free memory ≥ our measured footprint + 2 GiB; never disturb other users' jobs; CPU fallback, OOM or losing the margin is a STOP for that step.
- **Paper A coordination (19 Oct):** no Paper B GPU launch on zhixu experiment while a Paper A campaign there waits for a card.
- **Interruption on zhixu experiment:** every job there must resume from its last completed unit without re-running completed units. An interrupted unit is re-run whole, never patched. The run log records each interruption.
- **One manager backend per table (D6, D15):** all proposals of one labelled table come from one host type with the pinned manager digest. Mixing hosts within one table needs an author decision.
- **Proposer quantization (24 Oct; size rule replaced 25 Oct):** manager models run at Q4_K_M. The 24 Oct size ceiling (27B dense to 35B-A3B MoE) is replaced by the fit rule of R1-EXAM-POOL (Track X): any model the pinned llama.cpp build serves fully on one RTX 4090 at Q4_K_M with 16k context and q8_0 KV cache. Digest and quantization are pinned and reported for every run. Training stays BF16 LoRA (QLoRA only if needed).
- **Precision:** the TITANs are an older generation; check bf16 and kernel support (Qwen3.5's linear-attention layers) before planning any training there. Training defaults to zhixu portal.
- **GPU lease on zhixu portal (26 Oct, R1-PORTAL-SCHEDULE):** Track X evidence phases (B1, B2) have priority; every GPU job takes `flock ~/r1_locks/gpu0.lock` and first checks that no other compute process is on the card; Track P never pre-empts a Track X evidence run.

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

Added 25 Oct: Track X (proposer exam, zhixu portal) starts with X.1–X.2 once A.10/A.11 are done and must finish before B.5 uses the same card; Track H (DAC interface, Mac) and P.0 (post-training spikes, zhixu portal) run during Phase B and must be done before C.3. Added 26 Oct: Track P runs by `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`; P.0 spikes and P.3a use the 4090 in Track X's gaps (R1-PORTAL-SCHEDULE).

Added 27 Oct (R1-LAYOUT-FLATTEN): after the labels freeze (3 Nov), with every agent at a STOP and no evidence job running, the coordinator removes the `r1` directory layer in one reviewed batch (merge branches, `git mv`-only commit, path-reference commit, old→new path map, `r1` package shim). Until then every path in this runbook and in the agent prompts stays as written.

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

### Phase B — C3 labels and the offline gate (target ≈ 8 Dec 2026, R1-BX-D14; was ~22 Nov)

| # | Step | Host | Done when |
|---|---|---|---|
| B.1 | C3 label sweep 1: 8 nodes × 18 instances × 2 memory modes × W = 20 (≈ 5,800 proposals), manager `qwen2.5-coder:7b`. **Since 3 Nov (R1-MAIN-PROPOSER): the second source**, frozen (R1-B1-CORPUS-FREEZE) | deepthought only (24 Oct: no mixing hosts within one table) | Manifest; completion or a documented STOP (done; classified EVIDENCE by R1-SWEEP1-CLASSIFY) |
| **B.1b** | **C3 label sweep 2 — the main source (added 3 Nov, R1-MAIN-PROPOSER):** the B.1 design with the Track X pick (thinking off) as manager, on the same instances; spec below | one RTX 4090 host for the whole sweep (TASL-2 or TASL-7), or the proposer on deepthought across two TITANs (R1-BX-REVISIONS (f), after O5) | Manifest; completion or a documented STOP. **4 Nov:** this is sweep 2's **T0 part**; its **T1 part** is Track G G.5 |
| B.2 | Fresh-seed audits, K = 10 (5 label + 5 evaluation seeds), for sweep 1 and (after B.1b) for sweep 2 under the same rules. **4 Nov (R1-BX-D3):** after sweep-1 B.2, the K = 10 → 6 subsampling check runs on the Mac (CPU, label seeds only); K = 6 takes effect only if it passes and an author row puts it into force (scope *proposed*: T1 audits only) | deepthought CPUs (sweep 2: proposed, R1-MAIN-PROPOSER (e)) | Labels for every non-inert, non-duplicate proposal, per source |
| B.3 | A0–A3 offline (rules, constant prior, LightGBM, NGBoost). **4 Nov:** plus the practitioner baselines in their offline form (R1-BX-D7). The TabPFN rows, native and information-matched (R1-BX-D13), run on **TASL-7** (R1-TABPFN; operator O7); the Mac writes their code and CPU fixture tests only | Mac | Offline one-step values with CIs |
| B.4 | A4: manager zero-shot typed questions; isotonic calibration on dev. Main row with the main proposer (the pick); the 7B row is secondary | 4090 host for the pick; deepthought for the 7B row | Calibrated A4 table |
| B.5 | A5 SFT per Track P.4 (belief only; soft-label RPS + CE, R1-SOFT-SIGMA) on the P.3 finalists plus the Qwen3.5-0.8B/4B-Base control (R1-C3-CONTROL); candidates screened by the decision-model exam P.3 from Kev-0.8B/4B, StartLux 0.8B/2B/4B (if trainable after P.0) and Laya 421M | zhixu portal | RPS skill, calibration (all-bins and top-1 ECE, PIT, width ratio), offline value per model |
| B.6 | ~~Second manager for diversity~~: covered by sweep 1 as the second source since 3 Nov (R1-MAIN-PROPOSER (c)). ~~Still open: extend toward 8–10k with extra OpenML / MLP nodes, only if the A5 learning curve asks for it~~ **Cut 4 Nov (R1-BX-D11):** replaced by the T1 GPU nodes (Track G) | the main proposer's sweep host | Manifest, if run |
| B.7 | **STOP — C3 gate (author), ≈ 8 Dec (R1-BX-D14).** **Since 4 Nov (R1-BX-D8):** the primary criterion is the across-node aggregate — IQM of gap closed and probability of improvement of A3 or A5 over A2, with node-stratified bootstrap CIs — on the main proposer's labels from T0 (sweep 2) **and T1** (Track G G.5); the per-node table and the cross-proposer table are reported beside it. The numbers of the criterion are confirmed in a separate author row **R1-BX-D8-CONFIRM**, with the gate-code sha, before any sweep-2 (T0 or T1) label table is copied back for analysis or read by any analysis code. ~~A3 or A5 beats A2 by ≥ δ_n on ≥ 2 nodes, lower 95 % bound > 0~~ (18 Oct criterion, superseded) | Mac (author) | PLAN §10 row: pass → Phase C; fail → C3 reported as the measured negative, C1 + C2 carry the paper |

#### B.1b — sweep 2 with the main proposer (added 3 Nov 2026, revised 4 Nov after independent review; R1-MAIN-PROPOSER)

**Purpose.** The labelled proposals that C3 is trained and gated on, from the proposer the paper deploys. Sweep 1 (`qwen2.5-coder:7b`) is the second source.

**Design: sweep 1's.**
- **Nodes.** The eight in `authorizations/c3_sweep1_20261027.md`, with the same start configurations, D21 noise source and repair rule.
- **Instances.** 18 per node, on **sweep 1's instance seeds**: `_instance_seed(node, k)`, `r1/headroom/e1b_collect.py:142`. The same seed is also each campaign's `train_seed` / `split_seed`, so every sweep-2 campaign has a sweep-1 twin on the same start and the same splits. The manifest records the instance-seed list and checks it against the sweep-1 index. A mismatch is a STOP.
- **Fixed settings.** W = 20; memory `append_only_summary` and `none`; `vary` split; structure-only `manager_proposal/v1`; temperature 0.2 with the D26 seed; transport retry 3; watchdog and resume as in sweep 1.
- **Audits.** K = 10; seeds 7001–7005 for labels and 7006–7010 for evaluation. Duplicates get no label, and no-ops are labelled by rule. The seed rules of R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE apply unchanged.

**Differences from sweep 1 besides the manager.** Every cross-proposer table lists these:
- `cache_prompt` is `false` here; sweep 1 used the default;
- the llama.cpp commit is the same (620d222) but built for a 4090 (sm_89), not a TITAN X (sm_52) — or, if the proposer runs on deepthought (R1-BX-REVISIONS (f)), the same sm_52 build split across two TITANs;
- the CPU host of the in-campaign runs;
- the context size;
- q8_0 KV cache and `--jinja`;
- the thinking flag;
- the harness pin (`6adf385` against the next pin, which carries the `cacheprompt-20261031` fix at `a3fedbb` with its Track S ancestry and any R1-HARNESS-NEXT-PIN fixes) and the paper commit. Prerequisite 3 checks that the harness defaults the sweep relies on are unchanged.

**Manager and server.**
- **Model.** The Track X pick (X.7 (a), as amended). Use its registry entry: HF repo @ revision, GGUF sha256, quantization source, chat-template source and any declared template repair. Use the pinned llama.cpp build, with full offload on the sweep card.
- **Thinking off, set at the server, as in the exam.** The sweep's server start (`c3_label_sweep.py` `start_llamacpp`, about line 1146) passes the pick's `thinking_policy` with mode `off` to `LlamaServerInstance`. That produces `--chat-template-kwargs {"enable_thinking":false}` through `llama_server_instance.thinking_args`, together with the exam's `--jinja --cache-type-k q8_0 --cache-type-v q8_0`. Check that these flags appear in the pinned build's `--help`, as the exam runtime does. This is a **paper-repo change**; the harness has no thinking switch and needs none.
- **`cache_prompt: false` on every call.** This needs the accepted harness fix on branch `cacheprompt-20261031` @ `a3fedbb` (R1-CACHEPROMPT-FALSE, 31 Oct, recorded on `trackS-ops-20261030`): the llamacpp provider sends `cache_prompt` explicitly on every request, default false. It is not yet in the sweep's harness pin `6adf385` and not merged into harness `r1`. Merge it as the next harness pin. (The earlier opt-in switch on `trackS-20261029` @ `415d99e` is superseded and unused.)
- **Context.** 16,384. Every admitted model qualified at 16,384 or more in Stage A. Prompt lengths are re-measured with the pick's tokenizer at the D28 run. The 25 Oct figure of ≤ 1,345 tokens was counted with the 7B's tokenizer.
- **Recorded per call.** `cache_prompt`, the seed, prompt and completion tokens, latency, and the server's thinking flag (in the server record).
- **Thinking content.** A completion with a non-empty `reasoning_content`, a `<think>` tag in `content`, or `reasoning_tokens > 0` counts as thinking content. More than 1 % of calls is a STOP.

**Prerequisites, in order.** Each is reviewed before the next.
1. **The exam rule `x5_rule_v2`** with its code changes in `r1/exam/analyze.py` and `r1/scripts/exam_runner.py` (draft: `proposals/X5_RULE_V2_DRAFT_20261104.md`), reviewed, with PLAN row R1-EXAM-RULE-X5V2 carrying the sha, all **before B1 starts**. Then B1, B2 and the X.7 row.
2. **Sweep-1 B.2 complete** (R1-HARNESS-NEXT-PIN), or an explicit author exception.
3. **Code:**
   - the harness pin with the `cache_prompt` switch;
   - the paper-side sweep change that passes the thinking policy and the exam's server flags, and threads `cache_prompt` through the manager config. A resume with other values is refused;
   - a check that the harness defaults the sweep relies on are unchanged by the new pin.
   - Tests against a stand-in server; independent review.
4. **Config** `r1/scripts/configs/c3_sweep2_<host>.json`: the pick's model path and sha256, build, `ctx_size`, GPU UUID, `allowed_hosts` = the sweep host, workers from that host's census, `extra_args` as above, and the thinking policy.
5. **D28 liveness** of the pick on the eight nodes (ENGINEERING_ONLY; 2 instances × W = 10, memory on, as in sweep 1), with the prompt-length re-measurement. A failing node is a STOP for the author; no node is dropped silently.
6. **Projection.** Calls × the pick's thinking-off latency + runs × CPU time / workers. More than 4 days of one 4090 is a STOP for the author (proposed, R1-MAIN-PROPOSER (h)). *4 Nov: if the proposer is served on deepthought (R1-BX-REVISIONS (f)), the same 4-day STOP applies to the two-TITAN serving configuration (proposed).*
7. **Authorization note** by the author: `docs/r1/authorizations/c3_sweep2_<date>.md`. Sweep 2's data are classed EVIDENCE. This section authorizes nothing.

**Host and priority.**
- One 4090 host for the whole sweep: TASL-2 or TASL-7, chosen by the author with the Track S and Track P schedules in view. This is an amendment of R1-SWEEP-HOST, as R1-MAIN-PROPOSER (f) states. **4 Nov (R1-BX-REVISIONS (f), amends (f); the conditions are proposed):** alternatively the proposer is served on deepthought across two TITANs, only if O5 passes against the author's committed criterion; one serving configuration for the whole T0 part. If so, add to the differences list: the sm_52 build and the two-card layer split.
- The host's lease (`flock ~/r1_locks/gpu0.lock`) and priority markers apply. Track X evidence keeps priority on TASL-2 and Track P evidence on TASL-7, unless the authorization note rules otherwise.
- **Audits on deepthought's CPUs (proposed).** Copy the batch directory and audit with the B.2 code and pins. If the runner cannot audit a transferred batch, run the audits on the sweep host and audit 50 proposals on both hosts.

**STOPs.** All the sweep-1 STOPs in `prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md` §2, plus:
- a `cache_prompt` or thinking-flag mismatch;
- more than 1 % thinking content;
- the pick's pin differing from the X.7 row;
- an instance-seed mismatch with sweep 1;
- a priority marker appearing. This one is a pause, not a failure.

**Operator runbook.** Written once the pick is known, from `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phases 4–9, adding the 4090 host's lease and watcher and the audit-transfer step. It is independently reviewed before the authorization note.

**Analysis additions** (C3 table; Track P §3.6):
- **Splits.** One instance → train/dev/test assignment for both sources. Duplicates are grouped across sources by (instance, incumbent hash, edit hash) for folds and for deduplication. Twin campaigns give the same (instance, incumbent, edit) the same label in both sources.
- **Proposal statistics per source,** paired by instance: duplicate, no-op and valid rates; the audited-increment distribution; the rule-skippable share.
- **Cross-proposer table** (with the B.7 gate, which is read on sweep 2): one source's train partition → the other source's test partition, both directions. Report RPS skill, ECE and decision utility, with instance-cluster bootstrap intervals and the stack differences listed above.
- **Disclosure.** The exam nodes are among the eight sweep nodes. Instances and seeds are disjoint, but the pick's absolute Y carries a selection effect, so results lead with paired contrasts.

### Track G — Real-task benchmarks: tiers T1 and T2 (rewritten 4 Nov 2026; R1-BX-D1, D2, D4, D5, D12, R1-BX-REVISIONS; **the critical path**)

**Why it changed.** Six of the eight CPU nodes share one OpenML logistic-regression template, and the 7B manager edits almost only `max_iter` and `C`. The CPU pool alone cannot carry the main evidence, and C3 cannot be trained and gated only there (review document P1–P3). Since 4 Nov:
- the CPU nodes are **tier T0**, the controlled testbed;
- part of the GPU tasks are **label nodes (T1)** that train C3 and enter the B.7 gate;
- the rest are **evaluation only (T2)**;
- the primary generalisation test is **leave-one-suite-out**.

Track G starts now; it no longer waits for B.7. The older Track G text (24–27 Oct: autoresearch plus MLGym if a container exists by 10 Nov; evaluation/transfer only; steps G.1–G.5) is superseded; it is in git at `fa60704e`. Its rule that test-scored tasks select on validation only stands (R1-TRACKG-ROLE).

**Target.** 12–16 real tasks from ≥ 3 suites and ≥ 5 domains. Variants of one task do not count.

| Tier | Role | Candidates (cost per run verified one by one in G.0) |
|---|---|---|
| T0 | Theory validation, Track S, ablations, low-interaction condition | The 8 CPU nodes of sweep 1 |
| T1 | Label + evaluation: train C3, the B.7 gate, leave-one-suite-out | autoresearch (short fixed-step variant); 1GC-7RC lighter tasks: TinyShakespeare, Forest Cover, ETTh1, AG News, possibly ogbg-molhiv; MLGym lighter tasks: CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task (to be checked against the MLGym task table in G.0) |
| T2 | Evaluation only: closed-loop transfer, the API proposer | 1GC-7RC TinyImageNet and VOC; optional fourth suite: MLAgentBench light tasks (cifar10, imdb, ogbn-arxiv) |
| Not used | — | RE-Bench and MLE-bench (hours per run, cannot be audited); DACBench (different problem type) |

**Integration principle.** Each suite's **task assets** (data, baseline script, evaluator) become a harness node with a `NodeSpec` (editable and frozen paths, run command, metric and direction, fixed step budget). The suites' agent frameworks are not used. Every node then shares one runner, one provenance record and one audit path, and most of the need for containers disappears.

**Fixed rules for every T1/T2 node.**
- **Budget:** a fixed step or token budget, never wall-clock (R1-BX-D5). Label runs take 1–2 min; closed-loop evaluation may use longer fixed budgets (about 5 min).
- **Hardware:** one GPU model per label table, and the noise floor that sets σ̂ for a table is measured on that table's GPU model.
- **Edits:** code-level diffs under `manager_proposal/v2-diff` (proposed name), within the node's `editable_paths` (R1-BX-D4).
- **Outcomes:** a divergence is its own outcome class and is never folded into the mean (R1-BX-REVISIONS (c); *proposed definition:* a non-finite loss, or no metric at the fixed budget).
- **Audits:** K = 10 until an author row puts R1-BX-D3's K = 6 (3 + 3) into force after its check passes (scope *proposed*: T1 only). Label seeds come from 7001–7005 and evaluation seeds from 7006–7010, never mixed, under the R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE rules. *(proposed: at K = 6, labels 7001–7003 and evaluation 7006–7008.)*
- **Screening funnel:** every screened candidate is reported with its D21 and D28 verdicts, per suite; non-qualifying nodes are evaluated in an appendix (R1-BX-D12).

| # | Step | Host | Done when |
|---|---|---|---|
| G.0 | **Availability and raw cost** (ENGINEERING_ONLY): per candidate task, the repository and dataset licences and whether the task assets can be used — in particular whether the 1GC-7RC repository (arXiv 2605.17046) is public now; if not, **STOP** for the author (R1-BX-D2 (open)) — and the run time and VRAM of the suite's own baseline script at a candidate step count, on each GPU model available. No code beyond the suite's own script and a step-count argument; where a script has no such argument (autoresearch has a wall-clock budget), its raw cost is measured after G.1, at the fixed-step wrapper. **Ada first**, while Track X holds TASL-2; Ada is checked for Paper A occupancy first. | Operator: Ada, then the 4090s when free | First part of `docs/r1/reports/TRACKG_CENSUS_<date>.md` |
| G.1 | **Port task assets into harness nodes** (review document §7 routes porting to the server agent): data preparation, a fixed-step wrapper, a metric parser that reports divergence, a `NodeSpec` with `editable_paths` / `frozen_paths`, a per-run working copy and resource limits, and **3–5 representative edits declared as diffs before any measurement**. Native in the harness venv where possible; containers only where a task ships only as an image, through Apptainer (R1-BX-REVISIONS (g)). **Starts only after the author confirms R1-BX-REVISIONS (h)'s porting exception.** *(proposed)* The operator holds a scoped exception to "never edit code" for these new node assets only, on its own branch `ops-trackg-<date>`, each port independently reviewed before use (R1-BX-REVISIONS (h)). The Mac agent supplies the shared pieces first: the node template, a base metric parser with the divergence class, and the per-run working-copy runner (MAC M10 step 0). | Operator (ports, host smoke); Mac (shared pieces) | Smoke campaign per node with a stub manager; a frozen-path edit refused; review accepted |
| G.1b | **Census measurements** (ENGINEERING_ONLY), on the ported nodes: determinism (same seed twice); a 10-seed noise floor on the declared representative edits plus the baseline, with training seeds **8001–8010** *(proposed: disjoint from the audit seeds 7001–7010, the sweep instance seeds and the exam's 9001+)*; σ̂ for training and split seeds, and the tail shape; the D21 verdict; later D28 diff liveness with the main proposer (after X.7 and G.2). | Operator: Ada first | Census report complete, with the screening funnel per suite (R1-BX-D12) |
| G.2 | **Harness diff support (R1-BX-D4):** diff application; inert and duplicate detection for diffs (a normalised diff hash, and an AST or whitespace-insensitive equality check against the incumbent); provenance (diff text, hash, files touched); the `manager_proposal/v2-diff` schema *(proposed name)*; the S1.1 interaction analysis for diffs. Drafted, reviewed and pinned before any GPU sweep. The single-parameter path for T0 stays unchanged and byte-identical (tested). | Mac (harness `r1-local-*` branch) | Tests; independent review; pin recorded in the RUNBOOK pin table |
| G.3 | **T1 selection.** From the census, the author fixes the T1 and T2 lists (12–16 tasks in all, ≥ 3 suites, ≥ 5 domains), the T1 label-run GPU model, and the proposer host. The proposer may be served on deepthought across two TITANs if the dual-card qualification (operator O5) passes (R1-BX-REVISIONS (f); conditions proposed). | Mac (author) | PLAN §10 row |
| G.4 | **T1 pilot:** on 2–3 T1 nodes, a short sweep-2-shaped run (proposer on its host, task runs on the T1 GPU model) to measure throughput, diff liveness, the duplicate and inert rates for diffs, and the divergence rate. ENGINEERING_ONLY. **The Mac agent then recomputes the R1-BX-D14 dates from the operator's measured throughput and reports any change to the author before applying it.** | Operator: the hosts fixed in G.3 | Pilot report; date recomputation sent to the author |
| G.5 | **Sweep 2, T1 part:** W = 20, about 12 campaigns per T1 node *(proposed)*, about 150 audited proposals per node; the main proposer, thinking off, `cache_prompt: false`; the S1.1 edit–edit interaction measurement, with per-node interaction strength as a covariate. Then audits at the K in force (K = 10 unless an author row puts R1-BX-D3's K = 6 into force). EVIDENCE: needs the author's authorization note. The label table is copied back for analysis only after **R1-BX-D8-CONFIRM**. | Operator | Manifests; labels per node |
| G.6 | **Closed-loop evaluation on T1 and T2 nodes** with the main proposer and with the **API proposer** (R1-BX-D6; closed-loop only, not seed-replayable), plus the non-qualifying nodes for the R1-BX-D12 appendix. Part of D.3. The API provider and its request log are Mac code (M10); the calls go from the host the authorization note names. | Operator (+ API) | Closed-loop tables, part of D.3/D.4 |

**Cost (rough; calibrate with G.4).** About 40 GPU-h per T1 node at 2-minute runs and K = 6: noise floor about 2, sweep-2 executions (about 12 campaigns × W = 20) about 8, audits (150 × 6) about 30. About 400 GPU-h for 10 T1 nodes, and about 600 with T2. At K = 10 the audits take about 50 GPU-h per node.

**Execution.** `docs/r1/prompts/TRACK_G_RUNBOOK.md` (rewritten 4 Nov) holds the step detail. The Mac agent writes the shared pieces for G.1, G.2, the API provider and the drafts (MAC_LOCAL M10); the operator does G.0, the G.1 ports and smoke runs, G.1b and G.4–G.6 (OPERATOR O8).

### Track S — 4 Nov additions (R1-BX-D10)

The Track S design (rev 7.4) and its operator runbook (rev 3.3 of record) are on branch `docs/trackS-decisions-30oct` and enter this file through the Mac agent's integration (MAC_LOCAL M1). The 4 Nov decisions add:
- **1–2 GPU nodes:** autoresearch (short fixed-step variant) and one RL-type task with high noise and interacting edits, chosen from the Track G census. The GPU-node design is a Track S design revision, drafted in `proposals/TRACK_S_GPU_EXTENSION_20261104.md`, reviewed and committed before any GPU-node Track S run. Which manager runs on the GPU nodes is open (R1-BX-D10).
- **Fallback date ≈ 15 Dec 2026.** If Track S has no campaign-level result by then, the DAC-reduction argument rests on the theorem plus synthetic controls, and the paper says so explicitly. *(proposed)* Track S may continue after that date, off the critical path.

### Track X — Proposer candidacy exam (appendix; added 25 Oct)

**Pool and host adopted by the author (25 Oct, R1-EXAM-POOL); protocol X.2–X.6 adopted with two amendments (26 Oct, R1-EXAM-PROTOCOL).**

**What exists and why it is not reused as evidence.** The model "exam" the author remembered is the Round-7 candidacy exam of the Paper A repo (`agent-checkpoint-intervention`: `paper/appendices/C_protocol.tex`, subsection "Model candidacy: the completed Round-7 exam"; `round10/CANONICAL_EXAM_RESULTS.md`; evidence `evidence/round7-blackwell-grouped/run/`). Its code also survives here as `archive/old_b_2026-10-09/code/experiment_scaffold/src/causal_branch/round5_titan_exam.py` (protocol `round5_titan_compact_exam_v1`, Stage A compatibility + Stage B 30-root exam, hard gates, score `100·(0.5Y + 0.15C + 0.15S + 0.1T + 0.1R)`, selection by successes per GPU-hour). It completed on 4 Sep 2026: twelve candidates on two leased 48 GB Ada cards; three cleared the 12/30 gate; Devstral Small 2 24B was selected provisionally; all pairwise success differences among the three had bootstrap intervals covering zero. It cannot answer R1's question:
- **Different task.** A Pi coding agent writes an artifact and calls `submit_candidate` on a tabular task adjudicated on 40 hidden rows. R1's manager emits one structured `ManagerProposal` per trial in a governed keep/discard loop under noise. Tool-use competence is not proposal quality.
- **Confounded by interface conformance.** Several low rows were submission-format failures, not task failures (Qwen3.6-35B-A3B 2/30 valid submissions, Qwen3.6-27B 5/30, Muse Glimmer 7/30), under one frozen runtime with thinking disabled (`ENABLE_THINKING = False` in the protocol).
- **Statistically an eligibility screen only.** 30 roots, one draw; the archived Paper B limitations section says the screen "licenses no ranking of models".
- **Different hardware.** Two-card layer split, not one 4090.

Reused: the machinery (artifact pinning and quantization/licence blockers, Wilson intervals, paired template bootstrap, occupancy and contamination handling, frozen selection rule before data). Not reused: its numbers or its pool verdicts.

**Purpose.** (i) Choose, by a rule frozen before data, **the main proposer of Paper B, run with thinking off** (R1-MAIN-PROPOSER, 3 Nov; previously the D22 deployment-check proposer and the B.6 second manager). (ii) An appendix table of how proposer choice moves the C3-relevant quantities (duplicate and no-op rates, audited proposal increments, final audited Y). Exam campaigns are never C3 labels.

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
| X.5 | **B1 analysis and finalist rule (frozen before X.4 starts, committed with a hash; since 3 Nov `x5_rule_v2`: eligibility adds "can run with thinking off", and the ranking uses thinking-off μ̂, R1-MAIN-PROPOSER (a)).** Per candidate: valid-proposal rate, novelty (D28), no-op and duplicate rates, invalid-run rate, audited mean proposal increment μ̂ and P(Δ > 0), dispersion of audited increments (the input to T4 Proposition 7's bound), A4 log score and calibration, s/proposal, GPU-h; cluster bootstrap by instance. Eligibility = Stage A pass + D28 criteria. **Finalists:** top 4 by μ̂, plus the best model of any family absent from them (≤ 5). μ̂ is the ranking quantity because it is resolvable here (≈ 80–110 audited proposals per model after duplicates, rough se ≈ 0.001 on `digits_mlp`; corrected 26 Oct) while final Y is not (rough se ≈ 0.002 with 12 instances). | Mac | B1 report |
| X.6 | **Stage B2 (finalists, power-planned).** Final audited Y (K = 10, seeds 9201–9210) on the three nodes with fresh instances 9011+, the number of instances fixed from the B1 variance before B2 starts; plus one Track G node only if G.1 and G.3 are done *(old Track G numbering of 24 Oct; superseded by the 4 Nov Track G steps)*, the node runs on zhixu portal beside the manager within the fit rule, and the author adds it; otherwise transfer to Track G nodes stays in Track G (G.5). ~~Top 3 also rerun once with thinking off where possible.~~ **Since 3 Nov (R1-MAIN-PROPOSER (a)), under rule `x5_rule_v2`:** the top-3 rerun is a thinking-on rerun, descriptive; only finalists that can run with thinking off are finalists, and every finalist runs B2 with thinking off (thinking-on rows, if any, are descriptive). | zhixu portal only (R1-EXAM-HOST) | B2 report `docs/r1/reports/PROPOSER_EXAM_<date>.md` |
| X.7 | **Amended 3 Nov (R1-MAIN-PROPOSER), applied through the new frozen rule `x5_rule_v2` (R1-EXAM-RULE-X5V2), which replaces `x5_rule_v1` before B1 starts:** (a) is now the **main proposer** = the best B2 audited Y **with thinking off** among the finalists that can run thinking off (always-thinking models are not eligible; ties → lower GPU-h); it is also the strong LLM of the self-control comparison. The author's pick row names it as the **D22 pick** as well, because the exam runner's free-sensitivity guard looks for `D22` and the pick's id on one PLAN line (`exam_runner.py:97`). (b) is retired: sweep 1's `qwen2.5-coder:7b` is the second source. (c) stays. Original text: **Author, by role:** (a) **D22 strong proposer** = best B2 Y (ties → lower GPU-h); (b) **B.6 second manager** = the finalist whose proposal distribution (edited key and step-size distribution, declared distance) differs most from `qwen2.5-coder:7b` among those that fit the B.6 sweep host; if none fits a 12 GB TITAN, the second sweep's host changes (R1-SWEEP-HOST: one host type per table); (c) **appendix:** C3 premises (rule-skippable share, increment dispersion, A4 calibration) against proposer strength. If the anchors and the finalists do not differ on any C3 quantity beyond CI, the appendix reports that null and B.6 chooses by cost. | Mac (author) | PLAN §10 row |

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
| H.7 | *4 Nov (R1-BX-D9, D7): the self-control arm is A4; R-B only as an optional ablation; the practitioner baselines go through the same `decide()`.* Direct-action arms through the same `decide()`: AWR-MLP (Harness-MDP style), LLM self-control (`r1/llm_control.py`), hybrid (prior decides whether, LLM decides how). `matching_report` extended to identical instances, W, LLM cap and information set. This is the three-way comparison of PLAN D.2. | Mac | Report on a dry run |
| H.8 | Environments (`r1/c3/env.py`, Gymnasium API): `OfflineBanditEnv` over a labelled table (context = proposal features; action = bin; reward r = Δ_audit·keep − g·execute under the rules); Track P trains directly on the label table. The execute/skip amendment and unaccepted `row["prompt"]` follow-up are deferred until A7/C4 needs an environment (R1-H8-DEFERRED); `OnlineCampaignEnv` (DACBench-style instance set over the harness) built only if C4 finds a material DI violation (A7). | Mac | OfflineBanditEnv reproduces offline one-step values |
| H.9 | End-to-end dry run: fake llama-server + fake sidecar, 2 nodes, arms A0–A6 (A5/A6 stubbed), interruption and resume, `matching_report` passes. | Mac → deepthought | Dry-run manifest |
| H.10 | Fresh-session review + one correction round; author accepts. Must be done before C.3. | — | Review in `docs/r1/reviews/` |

### Track P — Post-training pipeline for A5/A6 (added 25 Oct; revised and adopted 26 Oct, R1-C3-POST)

**28 Oct (PLAN §10 R1-C3-POOL, R1-C3-POOL-EXAM, R1-TABPFN):** the decision-model candidates are **Kev-0.8B and Kev-4B**, with the Qwen3.5-0.8B/4B-Base control; **StartLux and Laya are removed**; **TabPFN** is added as a ladder rung (in-context, fine-tuned, R-A0, R-A1; not in P.3a, not in R-B). Where the text below names StartLux or Laya as candidates, these rows control. **Also 28 Oct (R1-CONTEXT-BASELINE):** a context-only rung A1-ctx (node descriptors only, fitted across training nodes per LONO fold) and a context-aware vs context-oblivious prompt ablation on Kev-0.8B at Stage S.

**4 Nov (R1-BX-D9, D11, D13, R1-BX-REVISIONS (c)(d)):** the self-control arm of the three-way comparison is **A4**, not R-B; **R-B (P.6) is an optional trained-self-control ablation**; R-A (P.5) is called **decision-focused fine-tuning** in the paper, and only R-B is called RL; the proposal is serialised **after** the history, immediately before `<decide>`, with a new E6 probe comparing the two orders; each node's soft-label width uses its own σ̂, and divergence is a separate outcome class; TabPFN gets an information-matched comparison; Stage D is one round on 1–2 T1 nodes.

Technical specification: `docs/r1/TRACK_P_POST_TRAINING.md`. Reading list: `docs/r1/references/README.md`. **Execution:** one agent running on zhixu portal itself follows `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` with a STOP and an independent review after every phase (R1-TRACKP-RUNBOOK).

**Facts checked 25 Oct (repo pages; to be confirmed by P.0).**
- **Kev** (`jaredpalmer/kev`, Apache-2.0): rank-16 LoRA (attention, MLP and DeltaNet projections) plus a pointer head scoring each option's `</opt>` state against the question's `<decide>` state; on Qwen3.5 hybrid bases each question runs as its own row; trainer `python -m kev.train` on JSONL with one hard `label` per question, cross-entropy, `--init_from` a released adapter (lr 2e-5 suggested). **No soft labels and no RL code.** Kev-0.8B trains in bf16 on a 4 GB GPU.
- **StartLux-Decision v1.1** (`StartLuxLabs/StartLux-Decision`; code Apache-2.0, weights CC BY-NC 4.0): Instant models answer in one forward pass with **bidirectional attention over the prompt** (served through a vLLM plugin); **no training code is published**; AutoThink RL is only described in its report. R1-C3-BASE's statement that StartLux "fits TRL GRPO directly" is therefore unverified.
- **Laya** (`NandhaKishorM/laya`, Apache-2.0): ModernBERT-large encoder, 421M, 1,024-context typed-decisions checkpoint; fine-tuning via `notebooks/laya_finetune_typed_decisions_2xT4_kaggle.ipynb` and `notebooks/laya_finetune_typed_decisions_mps.py` ("RLCD": RL against strictly proper scoring rules), temperature calibration per option count. Soft-label support not documented. Cannot generate text.

**Design (R1-C3-POST, 26 Oct).**
- **Belief and action are separate outputs.** The 12-bin belief is trained only with bounded proper scores (RPS; CE allowed in supervised A5 only); the decision reward trains only an action output (execute/skip). The 25 Oct A6 objective (12 bins as actions, exact expected reward + KL, deploy the greedy bin) is dropped: its maximiser is a point mass and destroys the belief's calibration. The smoothed-rule loss stays as an ablation.
- **Hard labels are never used for training** (argmax-style targets collapse outcome distributions; Jev's Choice vs Noul behaviour is the reference case).
- **Decision-model exam (P.3)** narrows A5/A6 to 1–2 finalists plus the Qwen control (R1-C3-CONTROL), with a label-free part (E0 aleatoric pass-through, E6 architecture probes) that runs before B.2 labels exist.
- RL rewards never contain the log score; RL monitoring adds width ratio and entropy (RL sharpens distributions).

| # | Step | Host | Done when |
|---|---|---|---|
| P.0 | **Spike per base (≈ 1 day each):** load, forward one 12-option question, attach LoRA, 100-example toy SFT with soft targets, save/reload, sha256, compare probabilities before/after reload; record whether a custom 4D mask + position_ids is accepted (tree packing; expected to fail on Qwen3.5 hybrids). StartLux must show a training forward with the correct bidirectional prompt mask in plain transformers; if it cannot, StartLux stays an inference-only zero-shot rung and the author decides. | zhixu portal | Spike report per base |
| P.1 | **Control base (adopted 26 Oct, R1-C3-CONTROL):** Qwen3.5-0.8B-Base and -4B-Base + LoRA r = 16, 12 reserved bin tokens read from the LM head (belief) and `<exec>/<skip>` tokens (action). **Amended 26 Oct evening (R1-CONTROL-READOUT): the primary belief readout is a fresh LayerNorm + linear head; the bin-token readout is a secondary row; the bin list stays in the prompt in canonical order.** Same base as Kev, so A5(Kev) − A5(control) isolates Kev's decision pre-training; it is also the guaranteed-trainable fallback. | zhixu portal | Control trains in the shared loop |
| P.2 | **One `DecisionModel` adapter, one training loop** (`r1/c3/train/`, PyTorch + PEFT; no TRL): each family exposes `belief_logits[12]` (Kev pointer head; StartLux option readout; Laya head; control: a fresh LayerNorm + linear head as primary, LM-head bin tokens as a secondary row — R1-CONTROL-READOUT) and an optional `action_logit` (linear head on the decision state; control: `<exec>/<skip>`). Shared serialisation (one text template, ≤ 1,024 tokens for Laya, fixed bin names and order). Tree packing (shared state, isolated proposal branches, tree-depth position ids) only where P.0 shows it works. Real loader for the H.5 sidecar. | Mac (code) + portal | Same toy batch trains on every family, both outputs |
| P.3a | **Decision-model exam, label-free** (while B.1/B.2 run): **E0** aleatoric pass-through — synthetic prompts stating (m, s), soft-label targets N(m, s²) over the bins, held-out (m, s) cells, plus a hard-label contrast; **E6** probes — A1 branch isolation, A2 sibling-order invariance (packed models), A3 history-length robustness, A4 width monotonicity in s, A5 bin-slot bias. | zhixu portal | E0 pass or disqualified, under E0 protocol v2 (26 Oct, R1-E0-PROTOCOL / R1-E0-BUDGET): width slope vs the label's std ≥ 0.6 with bootstrap 95 % lower bound > 0, mean slope ≥ 0.8 (R1-E0-THRESHOLDS; replaces width slope ≥ 0.7, mean slope ≥ 0.8); A3 at 0/25/50/100 % of the pool budget (R1-A3-BUDGET); probe table |
| P.3b | **Decision-model exam, labelled** (once ≈ 400–500 training-partition labels exist from B.2): E1 zero-shot (native decision interfaces; verbalized top-k instruct LLM via llama.cpp; Jev rung through TypeSafe's official API, R1-JEV-RUNG), E2 frozen probe, E3 short LoRA SFT (300 steps × 3 seeds), E4 VRAM/speed/reload at 1,024 tokens, E5 ECE; E7 belief-head form (softmax-12 vs cumulative-11) on the top 2. Non-LLM floor (embedding + ordinal regression; GBDT) included; base vs instruct recorded. Selection rule committed with its sha256 before any P.3b data. | zhixu portal (+ API) | Pre-registered rule (spec §5.7): top model + optional second of a different class if statistically tied; Qwen control always kept; no LLM beats the floor → stop and escalate. Author confirms finalists (PLAN row). Appendix table |
| P.4 | **A5 SFT (belief only)** on the finalists + control: soft-label RPS + CE on the B.2 labels (soft label per R1-SOFT-SIGMA); LoRA r = 16, adapter lr from the grid {1e-5, 3e-5, 1e-4} chosen by val RPS for every family (26 Oct, R1-LR-GRID), early stop on dev RPS, best checkpoint; temperature / isotonic recalibration on dev. Kev's trainer is patched (or bypassed via `kev/model.py`) to accept soft targets. Report RPS skill, NLL, all-bins and top-1 ECE, PIT, width ratio, then offline one-step value through `rules.decide`; learning curve 250/500/1k/2k. **RL gate** for P.5/P.6: RPS skill > 0 significantly, > 99 % mass on bin outputs over 3 seeds, all-bins ECE ≤ 0.05, width ratio in [0.8, 1.25]. | zhixu portal | A5 table (B.5); gate record |
| P.5 | **A6 decoupled stage** (only after B.7 passes; = C.1): arms R-A0 rule on the A5 belief; R-A1 action head on detached features; R-A2 action head with shared LoRA (belief still RPS-only); R-A3 smoothed-rule ablation. Action loss = cost-sensitive BCE with target 1[u > 0], weight \|u\|, u = mean over label seeds of Δ·keep − g (keep from the rules under the A1 reference prior; g = 0.1 σ_node). GRPO (K = 8, group-mean baseline) on R-A1 checked against the exact gradient (cosine ≥ 0.95); report zero-variance groups. Report action/rule disagreement. Rollback if dev ECE +0.02, dev RPS worse by > 1 s.e. without utility gain, width ratio < 0.8, or entropy −20 % within 100 steps. Deploy rule(belief) or the action head, never the greedy bin. | zhixu portal | A6 vs A5 offline, located where T4 §7 predicts |
| P.6 | **Reasoning arm (trained LLM self-control; feeds H.7). Optional ablation since 4 Nov (R1-BX-D9); A4 is the self-control arm:** generative bases only (Qwen control; Kev's base LM). `<analysis>` ≤ 256 tokens → belief (read) → action token (sampled). Warm-up SFT on ≈ 500 demonstration analyses written by DeepSeek-V4.1-Flash-1017 (`deepseek-flash`) via the DeepSeek API from the same leak-guarded view, without access to labels (R1-RB-TEACHER); fallback: format-only SFT. GRPO, group 8–16, β ∈ {0, 0.02}, lr 1e-6 → 5e-6, ≤ 500 steps; reward = −RPS(belief) + λ_a · 1[exec] · u (clipped) − format penalty; never the log score. Same rollback rule as P.5; ablation with vs without analysis. Reported as a distilled arm. | zhixu portal (+ API) | R-B row as an optional ablation beside the three-way comparison (since 4 Nov, R1-BX-D9) |
| P.7 | Pins: base revision, adapter + heads sha256, calibration map, training seed, data-manifest hash; every A5/A6 arm served by H.5 from these pins only. Jev rung: exact model version returned by the API, endpoint, date, full request/response log. DeepSeek demonstrations: returned model version, prompts, outputs. | — | Pin file per arm |

**Labels (how they are solved).**
1. **Source:** sweep 1 (B.1, ≈ 5,800 proposals on 8 nodes × 2 memory modes, one pinned manager, one host type).
2. **Audit (B.2):** each non-inert, non-duplicate proposal and its incumbent on K = 10 common fresh joint seeds; seeds 7001–7005 give the **training label**, 7006–7010 the **evaluation value**. Never mixed: the 19 Oct pilot gate "pass" came from sharing them.
3. **Belief target (R1-SOFT-SIGMA, 26 Oct):** the soft label p_b = ∫_bin N(μ, s²) on z = Δ/σ_node (`r1/c3/labels.soft_label`), μ = mean of the label seeds, **s = σ̂_node/√K_label with σ̂ pooled from the C1 30-seed table** (replaces the per-proposal se_audit; versioned soft-label function). No-ops → one-hot no-op bin by rule; duplicates excluded (their result is known).
4. **Action target / A6 reward:** r = Δ_audit(label seeds)·keep − g·execute, g = 0.1 σ_node (22 Oct); the action target u uses keep from the rules under the fixed A1 reference prior and the logged Δ̂, so it does not depend on the model. Offline evaluation uses only the evaluation seeds.
5. **Splits:** *(4 Nov, R1-BX-D1: leave-one-suite-out is primary; LONO within T0 secondary.)* By instance seed (train/dev/test) plus leave-one-node-out; never by trial; duplicates grouped by edit hash across splits. The P.3b exam set is a fixed subset of the training partition. *(3 Nov, R1-MAIN-PROPOSER (e): one instance assignment for both sweeps; cross-source duplicates grouped by (instance, incumbent hash, edit hash). Proposed: the P.3b exam set is drawn from sweep 2's training partition; if P.3b must run before sweep 2, from sweep 1's, disclosed.)*
6. **Volume:** *(4 Nov, R1-BX-D11: B.6 is cut; volume beyond the T0 sweeps comes from the T1 nodes, about 150 audited proposals each.)* ≈ 1/3 of proposals are non-inert, so ≈ 2,000 labels from sweep 1; B.6 (second sweep, second manager) and the D20 pool extension target 8–10k, decided by the A5 learning curve. *(3 Nov: sweep 2 with the main proposer adds a comparable volume; sweep 1 is the second source, so B.6's second manager is covered.)*
7. **Label noise:** carried in s; K raised on proposals near t* (then s = σ̂/√K).
8. **Covariate shift:** one DAgger-style aggregation round (C.2) under the deployed tabular arm.

**Host change (26 Oct, evening, R1-TASL7-TRACKP; R1-ADA-OVERFLOW).** Track P moves to the dedicated 4090 node **TASL-7**; wherever this section says zhixu portal for Track P work, read TASL-7. zhixu experiment (Ada) takes resumable overflow runs; one comparison table stays on one GPU type and one pinned environment. **Hardware and card schedule (R1-PORTAL-SCHEDULE, 26 Oct; now the portal is Track X's only).** All A5/A6 training and the exam on zhixu portal (4090 24 GB): ≤ 4B LoRA in bf16; the Track P agent, its code and its CPU-only unit tests also live on the portal; the Mac runs no Track P work. Track X evidence phases (B1, B2) have priority on the card; Track P uses it only in the gaps (P.0 and P.3a during Track X's code phase, ≈ 27 Oct–1 Nov, and after B2). One GPU job at a time, enforced by `flock` on `~/r1_locks/gpu0.lock` on the portal plus a check that no other compute process is on the card. API calls (Jev, DeepSeek) run on the portal (fallback deepthought; never the Mac without the author's approval); keys live only in `~/.config/r1/secrets.env` (mode 600) on that host.

**Open items.** StartLux rung after P.0 (author). Track H.8 retains the accepted bin-action `OfflineBanditEnv`. Track P trains directly on the label table; the execute/skip amendment and unaccepted sidecar prompt follow-up are deferred until A7/C4 needs an environment (R1-H8-DEFERRED).

### Phase C — Post-training and online pilot (only if B.7 passes; dates follow R1-BX-D14 and the T1 pilot)

| # | Step | Host | Done when |
|---|---|---|---|
| C.1 | A6 decoupled stage on the A5 finalists, per Track P.5 (rule on belief; action head detached/shared; smoothed-rule ablation; GRPO checked against the exact action gradient) | zhixu portal | A6 vs A5 offline, located where T4 §7 predicts |
| C.2 | Aggregation round (DAgger-style): collect proposals under the deployed tabular arm, audit, retrain. **4 Nov (R1-BX-D11): one round on 1–2 T1 nodes only** | deepthought *(3 Nov: a 4090 host, since the proposer is the main proposer, R1-MAIN-PROPOSER (f); to be planned)* | Retrained arms |
| C.3 | Online pilot A1–A5 on qualifying nodes (manager + small LM co-resident: ≤ 2B models on TITANs, 4B on zhixu portal; *3 Nov: with the main proposer, co-residence on a 4090 must be re-planned against the pick's footprint*) | deepthought + zhixu portal *(3 Nov: 4090 hosts, to be planned)* | PILOT report |
| C.4 | C4: DI test on existing branch pairs (offline) and the debiased-memory A/B on 2–4 nodes | Mac (analysis); A/B on zhixu experiment (resumable, a few GPU-hours) | C4 report |

### Phase D — Transfer, pre-declaration, deployment (D.3 closed loop ≈ 3 Jan 2027, R1-BX-D14)

| # | Step | Host | Done when |
|---|---|---|---|
| D.1 | **Leave-one-suite-out (primary since 4 Nov, R1-BX-D1)** and leave-one-node-out within T0 (secondary) for A3, A5, A6; transfer to the T2 nodes (Track G G.6) | zhixu portal | LONO and transfer tables |
| D.2 | Pre-declare deployment: contrasts H1–H5, including the three-way comparison (LLM self-control A4 vs trained configurator A5/A6 vs hybrid; R-B only as an optional ablation, R1-BX-D9), the practitioner baselines (R1-BX-D7), the API proposer's closed-loop rows (R1-BX-D6), the non-qualifying-node appendix (R1-BX-D12), instances, sample sizes, matched W and LLM-call cap, analysis script, with hash | Mac (author commits) | Hash in PLAN §10 |
| D.3 | Authorization note; online deployment, 18 instances per node, 2 repetitions, fresh-seed audited Y; **≈ 3 Jan 2027**, on T0, T1 and T2 nodes (R1-BX-D14) | deepthought (+ zhixu portal for 4B arms) *(3 Nov: 4090 hosts with the main proposer, to be planned)* | Manifests; completion or STOP |
| D.4 | Analysis: contrasts as pre-declared, C1 error rates per arm, T4 bound vs realised gain | Mac | Report |

### Phase E — Write-up (manuscript 10 Jan 2027, writing in parallel from early December; R1-BX-D14)

| # | Step | Host | Done when |
|---|---|---|---|
| E.1 | Manuscript in `papers/r1/` on the ICML 2027 template (venue changed 24 Oct). **4 Nov wording (R1-BX-D9, D12):** R-A is "decision-focused fine-tuning", only R-B is called RL; the screening funnel per suite is reported; the T0 single-parameter nodes are presented as the low-interaction condition | Mac | Draft |
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
| The R1-BX-D3 subsampling check fails | K stays 10; STOP for the author (cost and dates are recomputed at K = 10) |
| The 1GC-7RC repository is still not public (G.0) | STOP for the author: rebuild its tasks from the paper and public data (disclosed), or make MLAgentBench the third suite |
| The main proposer fails diff liveness on a T1 node | STOP for the author; no node is dropped silently |
| Track S has no campaign-level result by ≈ 15 Dec | The DAC-reduction argument rests on the theorem plus synthetic controls; the paper says so explicitly (R1-BX-D10) |
| A T1 node diverges often under the fixed budget | Divergence is reported as its own class; the author decides whether the node stays in T1 |

## 7. Reporting

Each implementation session ends with a STATUS entry: date; tasks done with commits; checks with results; what is not done and why; decisions needed, phrased as questions for the author.
