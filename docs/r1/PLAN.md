# Paper B (route R1) — canonical plan

**Status:** canonical from 9 October 2026; revised 12 October 2026 (R1-REFRAME, R1-INDEX and R1-GATE-FIRST in §1). This is the only plan for Paper B. Every plan, runbook, decision sheet, prompt pack and review written for the earlier Paper B route is archived under `archive/old_b_2026-10-09/` and has no authority.

**Owner:** Dowling Wong (author; decides). This plan was drafted by an AI agent (Claude, coordinating session) from the author's decisions of 9 October 2026 and two AI-assisted inputs in `docs/r1/inputs/`. None of this is human or external review.

**Companion files**

| File | What it is |
|---|---|
| `docs/r1/RUNBOOK.md` | Execution: phases, tasks, acceptance criteria, gates. |
| `docs/r1/STATUS.md` | Dated progress log; the only place that says what is done. |
| `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md` | Problem definition draft: setting, actions, estimands, arms, open decisions D1–D13. |
| `docs/r1/inputs/NOVELTY_SWEEP_20261009.md` | Prior-work sweep and venue check, as of 9 Oct 2026. |

---

## 1. Decisions adopted on 9 October 2026 (author)

| ID | Decision |
|---|---|
| R1-ROUTE | Paper B takes route R1: **noise-aware learned control of governed autoresearch loops**. DAC is related-work vocabulary only, not the headline framing. |
| R1-VENUE | Target a **rolling-submission journal** instead of a conference deadline. Made concrete by R1-VENUE-2. |
| R1-CARRY | Old Paper B was evaluated for R1. Only high-value, low-risk parts carry over (§8). |
| R1-ARCHIVE | All old Paper B plans and records move to `archive/old_b_2026-10-09/`. |
| R1-PLAN | This file is the canonical plan, and `docs/r1/RUNBOOK.md` is the runbook. |
| R1-VENUE-2 (later, 9 Oct) | **Primary venue: TMLR** (closes D17). The quality bar is the **ICML main-track standard**, defined in §9. |
| R1-FORMAT (9 Oct) | **No manuscript format is fixed yet.** The ICML-standard bar (§9) is about content quality, not template or page count. |
| R1-BENCH (9 Oct) | **ResNet-trigger is removed from the experiments.** Experiments and configurator training use **agent benchmarks** across the board. Which benchmarks is D20 (proposal in §6). |
| R1-LEDGERS (9 Oct) | The original trial ledgers (1,355 trials) are **lost**. Closes D12: there is no per-trial development analysis. Only aggregate tables survive (§6). |
| R1-REFRAME (12 Oct) | **Headline: incremental acceptance decisions under noise.** The governed loop is formalised as a noisy sequential selection problem with an incumbent. The paper derives when verify and a raised keep threshold are worth their cost, as functions of \|Δ̂\|/σ_n, ϱ and remaining budget, and characterises the winner's-curse bias of `current_best` and how it drives stagnation. Theory tools: ranking & selection, knowledge gradient (Frazier & Powell), racing (F-Race / irace), best-arm identification. This is B's own theory, not Paper A's (§2, §3 C2). |
| R1-INDEX (12 Oct) | **The learning question is narrowed:** how much does a learned configurator add *above a theory-grounded index policy* (KG-style or PACE-style)? This replaces "who controls best" as the primary contrast and roughly halves the experiment matrix (§3 C3, §5). The LLM self-control arm stays; a **stronger manager** is used at least as a deployment check (D22). |
| R1-GATE-FIRST (12 Oct) | **Two questions are answered before any model is built.** (1) Which CPU nodes have enough training-seed and split-seed noise? (2) On a branch table, does hindsight oracle minus the strongest simple baseline (noise-aware threshold or PACE-style gate) exceed the practical target? Kev/CLM architecture selection (D16) and the configurator scaffold (L11) are deferred until the headroom gate passes. If it fails, the fallback paper is C1 + C2 theory, a complete TMLR paper (§3). |

Superseded by this plan:
- the two-checkpoint verification-timing study (N2) and its N1 replay tax;
- the candidate-consistency task (attempts 1 and 2) and P-B1;
- RUNBOOK §16–§20 decisions (D-AGENCY, D-COMPLY, D-TESTPOOL, D-HEADROOM, R-1, R-4 as written);
- the ICML 2027 route and the 15 / 30 November cutoffs;
- the Devstral / Ada binding plan;
- the 9 October prompt pack;
- (12 Oct) the 9 Oct framing of §2–§3 as "who should control the loop", and the 9 Oct §7 proposal as a work item. Both survive only as context where marked.

## 2. The question

In a governed autoresearch campaign, an LLM manager proposes bounded edits to a training script and a worker trains. A control plane keeps an edit only when the parsed metric strictly beats the incumbent. This default rule makes measurable errors:

1. **Wasted runs.** Invalid trials consume budget. Healthy autoresearch seeds showed invalid rates of 0.10–0.30.
2. **Noise-driven keeps and discards.** As an illustration only, from the old ResNet-trigger node (removed from R1): the measured seed s.d. is about 0.0138 AUC. Assuming a cross-config correlation of 0.5, a true ±0.005 change is decided wrongly about 36 % of the time. Verifying with 1 or 3 extra seeds lowers this only to about 30 % or 23 %.

The correlation is assumed; Phase 0 measures it (inputs §4.4).

**Question (revised 12 Oct, R1-REFRAME).** The governed loop is a noisy sequential selection problem with an incumbent. Each trial draws a candidate, observes one noisy metric, and accepts or rejects it against an incumbent whose own value is a noisy, selected draw. Three sub-questions:

1. **When is verification worth its cost?** Derive the value of verify (r paired fresh-seed runs) and of a raised keep threshold as functions of the observed margin |Δ̂|/σ_n, the cross-config correlation ϱ and the remaining budget.
2. **How biased is the incumbent?** Characterise the winner's-curse bias of `current_best` (a maximum of noisy draws) and how it lowers the acceptance rate of later true improvements, i.e. how it drives stagnation.
3. **How much does learning add?** Above the index policy that follows from 1–2 (KG-style or PACE-style), how much does a learned configurator gain at matched compute, and where does LLM self-control sit?

The 9 Oct question (LLM vs configurator vs hybrid; does the problem need RL) survives inside 3. It is no longer the headline.

## 3. Planned contributions (claims are falsifiable; none is established)

> **18 Oct 2026 (R1-C3, R1-C4, §10): current contributions.** The table below the box is kept as history.
> - **C1** — measured control errors (unchanged), including wasted runs on duplicate and inert edits.
> - **C2** — theory of acceptance under noise: T2 plus `theory/T4_FEEDBACK_PROPOSER.md`. T4 covers the ledger-dependent proposer, the per-proposal gain bound and skip rule, the winner's curse for any adaptive proposer, and decision independence. Its empirical checks (Proposition 7 bound vs realised gain, Proposition 8 screening term, the T4 §7 SFT-vs-GRPO prediction) use C3's labels and are reported with C3.
> - **C3** — learned per-proposal prior under the C2 rule: the A0–A6 ladder and the C3 gate (`docs/r1/C3_DESIGN.md`).
> - **C4 (secondary)** — **proposer feedback**: (i) a test of the decision-independence condition (T4 Proposition 10) on forced-decision branch pairs at matched histories; (ii) a debiased-memory intervention that shows the manager the run-free posterior estimate of the incumbent instead of the raw record (T4 §5). C4 also decides whether online RL (A7) is warranted. A small effect is reported as such; C4 then shrinks without affecting C1–C3.

| ID | Contribution | Kind | Evidence that would establish it |
|---|---|---|---|
| C1 | **Measured control errors in governed autoresearch:** false keep, false discard and wasted-run rates per node, from noise-floor measurements (training seed and split seed separately) and fresh-seed audits of ledgered candidates. | Phenomenon | Phase 0–1 audits on nodes with real training- or split-seed noise (D21) |
| C2 | **Theory of incremental acceptance under noise** (R1-REFRAME). The governed loop as noisy sequential selection with an incumbent: (i) the value of verify and of a raised keep threshold as functions of \|Δ̂\|/σ_n, ϱ and remaining budget; (ii) the winner's-curse bias of `current_best` and its effect on later acceptance (stagnation); (iii) the index policy that follows (KG-style or PACE-style, D23). Built on ranking & selection, knowledge gradient, racing and best-arm identification. The identification ladder Q^ρ → V^L0 → V^π and the rule for when RL is needed remain as a secondary part. | Formulation and theory (main) | Full proofs; predictions checked against measured σ_n and ϱ, and against simulation |
| C3 | **How much does learning add above the index policy?** (R1-INDEX). On held-out instances at matched compute, the trained configurator (and hybrid H1) is compared with three primary comparators: the C2 index policy, a PACE-style gate and a noise-aware threshold. LLM self-control is an arm, with a stronger manager at least as a deployment check (D22). An action ablation shows where any gain comes from. | Main empirical result | Phase 3 deployment |
| C4 | **Configurator training recipe** (secondary). Full-information supervised learning on branch labels, then RL only if the ladder shows it is needed. Built only after the headroom gate passes (R1-GATE-FIRST). | Method, secondary | Phase 2–3 |

**Fallback if the headroom gate fails (RUNBOOK 0.4b pre-check or 1.5 gate).** If the hindsight oracle cannot beat the best simple baseline by the practical target, nothing is learned and no configurator is built. The paper becomes **C1 + C2 theory**, plus the measured statement that on these nodes there is no room for learning above the index policy. That is a complete TMLR paper.

**Novelty position** (inputs/NOVELTY_SWEEP): no prior work trains a policy for when and how to intervene in an autoresearch keep/discard loop. Each piece, however, has close neighbours:
- Harness-MDP (2607.05458): small offline-RL controller over a frozen LLM;
- Centaur (2603.24647): LLM plus CMA-ES on autoresearch, untrained;
- PACE (2606.08106): statistical commit gate;
- COTA (2608.21027): tiny advisor trained on counterfactual branches;
- PrimeScientist (2609.17846): budgeted allocation over autoresearch;
- Rehearse (2607.27687): the LLM judge degrades late in a campaign.

The paper must win on the **combination** and on three differentiators (revised 12 Oct):
1. a measured, unplanted noise mechanism (C1);
2. **a theory of acceptance under noise that is B's own** (C2). It connects the agent loop to ranking & selection, knowledge gradient, racing and best-arm identification. What those classical results do not cover: a proposer whose proposal distribution depends on the ledger, an incumbent-relative keep with restore, and a winner's-curse bias that feeds back into the proposer;
3. a sharp learning question: the gain above the theory-grounded index policy at matched compute, with an explicit LLM self-control arm (C3).

Same-state counterfactual labels with stated identification conditions stay as a supporting point, not a differentiator. Restore is bit-exact on the CPU nodes (STATUS, L7), so p ≈ 0 there, and p-aware labels are unlikely to change a decision.

Three risks have to be neutralised in the experiments themselves:
- "it is just HPO scheduling": HPO baselines plus an action ablation;
- "a small controller over an LLM is known": a self-control failure, a hybrid result, and transfer;
- "branch labels are standard": measured p, plus a case where p-aware labels change a decision;
- "it is just ranking & selection / racing" (added 12 Oct): state what the classical models assume (i.i.d. arms, a fixed arm set, no incumbent restore), show where the loop departs, and include racing and KG-style baselines.

The sweep is rerun before submission. From 12 Oct it also covers ranking & selection, knowledge gradient (Frazier & Powell), racing (F-Race / irace) and best-arm identification, which the 9 Oct sweep did not cover.

## 4. Setting and estimands (summary; full text in inputs §1–§5)

**Instance and episode**
- An instance is ι = (node, seed, manager, compute budget C, start config).
- An episode is one campaign.
- Decision epochs inside a trial:
  - E0, before the proposal;
  - E1, after the proposal and before execution;
  - E2, after the metric and before commit.

**Actions**
- Core set, proposed in D3: continue, skip (E1), revise (E1), verify with a frozen response rule that can demote a noise keep (E2).
- stop is added if the budget unit is compute (D1).
- Extensions: scope/step-size, memory-mode switch, low fidelity / early stop, accept-worse.

**Outcome.** Y is the fresh-seed audited improvement of the final incumbent over the start config, normalised per node. The audit uses common seeds across arms and lies outside the campaign budget. The in-run `current_best` is never the outcome.

**Estimands**
- **Primary: V^π.** The deployed policy's value at matched compute and LLM-call cap, on held-out instances.
- Secondary: one-step Q^ρ from branch labels, and V^L0.
- No Markov claim for any compressed state.

**Where Paper A enters**
- Branch labels come from restored states, so Paper A's discrepancy allowance p qualifies them: 2p sufficient, p/(1−p) necessary, Γ in between.
- Deployment contrasts involve no restoration, so **p does not tax the primary result**. The old N1 problem disappears.
- Seed and GPU nondeterminism count as kernel noise, not discrepancy (D5, proposed).

## 5. Arms and baselines

**Primary comparator (R1-INDEX, 12 Oct).** Every learned arm must beat the C2 index policy (KG-style or PACE-style, D23). The primary contrasts are configurator − index policy and H1 − index policy. Configurator vs LLM self-control is secondary.

**Arms**
1. **LLM self-control.** A side query on a forked context returns an action and per-action scores. It never enters the manager context, and its tokens are charged to the arm. Branch data use the pinned local manager (D15). A stronger manager (D22) runs at least as a deployment check, so the arm is not a strawman.
2. **Trained configurator.** Architecture is open; see §7.
3. **Hybrid H1.** The configurator decides *whether/when*; the LLM decides *how*.
4. **Hybrid H2** (secondary; dropped first if the matrix must shrink). The LLM's scores and rationale are inputs to the configurator.

**Baselines** (trimmed 12 Oct)

Required:
- ρ, the default rule;
- the C2 index policy (KG-style or PACE-style);
- a PACE-style anytime-valid commit gate;
- a noise-aware keep threshold;
- a racing-style re-evaluation rule (F-Race / irace style);
- harness heuristics: repeated-bad and doom-loop skip;
- random at matched realised budget;
- an offline-RL (AWR) MLP controller in the style of Harness-MDP;
- a hindsight oracle on the branch table, used for headroom only.

Secondary (appendix; dropped first if compute is short):
- fixed schedules;
- a risk-ranked vs advantage-ranked comparator on Z;
- the two-step continuation-value rule (Longstaff–Schwartz / FQE) for budgeted verify;
- successive halving / ASHA, for the fidelity extension only.

**Matching.**
- Every arm faces the same instances, manager, compute C, LLM-call cap and intervention cap.
- All arms share one online spending rule and calibrate it with the same tuning budget on development instances.
- Information parity is checked mechanically by `matching_report`, carried over (§8).

**Inference.** Cluster bootstrap by instance, results by node, and leave-one-node-out as a descriptive check.

## 6. Data and instances (agent benchmarks; D20 proposal)

The decision is made (R1-BENCH): no ResNet; agent benchmarks throughout. Which benchmarks is still open. Every environment must have the R1 loop shape: propose an edit, run, evaluate, keep or discard. A benchmark without a noisy keep decision cannot show C1.

| Pool | Candidates | Why | Cost and status |
|---|---|---|---|
| Training workhorse (many cheap instances) | OpenML / AutoML-style tabular tasks; existing harness nodes `lr_synthetic`, `openml_*` | Hundreds of instances, CPU-cheap, real seed noise | Seconds per run. 10–20+ tasks to add (small new code). |
| Noisy CPU nodes (added 12 Oct, D21) | SGD-trained small MLP / small CNN nodes on CPU where the training seed moves the metric; existing nodes run with the split seed varied | C1 and C2 need nodes where the noise exists. On `lr_synthetic` the training seed moves val_score by ≤ 1e-4 while the split seed moves it by ~0.01 (STATUS, 9 Oct). The five OpenML nodes are deterministic at a fixed seed. | Small new code (L8b); E1 measures them |
| Agent benchmarks, primary | **MLGym-Bench** (13 open-ended AI-research tasks; Gym interface; open-sourced) [arXiv 2502.14499]; **MLAgentBench** (an adapter already exists in the harness) | Recognised ML-research-agent benchmarks; MLGym is built for RL training of agents | Per-task compute varies; the 0.4 pilot measures it. Light tasks for training, heavy ones held out. |
| Agent benchmark, held out | **MLE-bench Lite** (low-complexity Kaggle split) [arXiv 2410.07095] | Cross-benchmark generalisation is the strongest test of the configurator | Kaggle data and terms, larger compute; evaluation only. |
| Deployment showcase | autoresearch (Karpathy-style, GPU) | The setting the story starts from | About 5 min per run; deployment only, never branched. |
| Possible instance generator | ML-AutoResearch auto-generated environments [arXiv 2603.17216] | Many synthetic ML-research environments | Release not confirmed. It trains the agent by SFT, not a controller, so it is a neighbour to cite. |
| Excluded | ResNet-trigger; RE-Bench (8-hour H100 tasks); general agent benchmarks (τ-bench, WebShop, SWE-bench) unless D20 says otherwise | No ResNet by decision; RE-Bench is too costly; general benchmarks lack the keep/discard loop and sit on Harness-MDP's and COTA's turf | — |

**Generalisation design (proposed):** train on the OpenML pool and MLGym light tasks; hold out MLAgentBench and the MLE-bench Lite subset; report leave-one-benchmark-out.

- **The earlier trials.** The 1,355 trials behind the ETAAI workshop paper are lost, and only aggregate tables survive. They are in the workshop-paper repository (`~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation/tables/*.csv`, also a submodule of the harness), for example `governance_metrics.csv`. These are context only. **All R1 numbers come from new runs**, starting with the Phase 0 pilot.
- **Workshop numbers cannot be re-audited.** The `ClawWorker` sign issue (RUNBOOK 0.2, item 2) cannot be checked against the lost ledgers. R1 never reuses workshop-paper numbers as evidence.
- **Harness code.** Local clone at `~/Documents/autoresearch_harness`, cloned 9 Oct 2026 at `da8dcbd`, with submodules not initialised. R1 work goes on branch `r1` (D14).

## 7. Configurator architecture (proposal for discussion; D16 open)

> **Deferred (R1-GATE-FIRST, 12 Oct).** No architecture is selected and no configurator scaffold is built until the headroom gate passes (RUNBOOK 0.4b pre-check, then 1.5). This section is context for that later decision, not a work item. If the gate fails, it is not needed.

**Verified open candidates** (repository pages read 9 Oct 2026):

| Candidate | What it is | Post-training | Fit |
|---|---|---|---|
| **Kev** (`github.com/jaredpalmer/kev`) | Small Jev-like typed decision models: `noul` (probability), `choice` (option probabilities and confidence), `score` (ordinal). Calibrated by default. Sizes 0.8B / 4B / 9B (Qwen3.5-Base) and 27B. API-compatible with the TypeSafe SDK. Apache-2.0. | LoRA (rank 16) cross-entropy fine-tuning on own labels. RL is not in the repo; policy gradient can be applied directly to the `choice` distribution. | **Recommended primary.** It natively emits the calibrated per-action probabilities the shared spending rule needs. |
| **CLM** (`github.com/Contrastive-LM/CLM`) | Contrastive state/action dual encoder on frozen Qwen3-8B with about 20M-parameter projection heads; typed Noul/Choice/Score plus `rank`. Post-trained on about 1M agent trajectories. Apache-2.0. Served through a vLLM pooling server. | Fine-tune the heads (`train/finetune.py`); RL on the heads is possible. | Ablation: does a frozen representation with a light head suffice? |
| Generative small LLM (Qwen3 / Qwen3.5, 0.6–4B) via TRL, verl or MLX-LM-LoRA | Writes reasoning, then an action | SFT, then GRPO | Ablation: does free-text reasoning add anything over typed decisions? It can also produce the *how* (revision text). |
| Tabular: LightGBM / ridge / **TabPFN-2** (weights under the Prior Labs License: Apache-2.0 plus attribution; versions 2.5 and later are non-commercial); offline RL via d3rlpy (IQL / CQL / AWR-style MLP) | Structured ledger features | Supervised; offline RL | **Required strong baselines.** The AWR-MLP mirrors Harness-MDP. |

**Proposed design (to discuss).**

- **Primary configurator: Kev at two sizes, 0.8B and 4B.** Each epoch is posed as typed questions, for example:
  - E1: `choice{execute, skip, revise}`;
  - E2: `noul`: "is this keep explained by noise?" and `choice{commit, verify}`.
- **Post-training ladder** (D8):
  1. LoRA cross-entropy on full-information branch labels (the best action, with calibration);
  2. policy-gradient / GRPO on the `choice` distribution with rewards from the counterfactual table;
  3. online RL on CPU instances, only if the ladder shows greedy deployment underperforms.
- **Comparisons at matched information:** Kev vs CLM heads vs generative LLM vs tabular / TabPFN vs AWR-MLP vs LLM self-control. Plus a size ladder of 0.8B → 4B (→ 9B if needed).
- **Natural hybrid H1:** Kev decides *whether / when*; the manager LLM decides *how*.

**Why this is interesting.** It asks a question the closest prior work does not: does a calibrated typed-decision model, post-trained on counterfactual labels, beat both generative reasoning policies and tabular controllers at controlling an agent loop?

**Data-scale caution.** LoRA fine-tuning needs hundreds to thousands of labelled decisions. That is why the cheap OpenML pool carries training (§6).

**Interface requirements** (inputs §8):
- input (Z, M, epoch);
- output a masked action distribution plus one scalar score per action;
- ≤ ~1 s latency per call;
- deterministic and logged as a `control_decision` event;
- never sees audit or test metrics, sibling outcomes or future records;
- never writes the ledger.

## 8. Old Paper B evaluated for R1

Criterion: carry an item only if it is useful for R1, cheap to adapt, and has low risk of importing old assumptions.

**Carry over: code, adapted in place (`experiment_scaffold/src/causal_branch/control/`)**

| Module | Use in R1 | Adaptation |
|---|---|---|
| `schema.py`, `branch_tree.py` | Branch records, leak-safe learner projection, integrity status distinct from outcome | Sibling sets per trial epoch instead of three fixed leaves |
| `evaluate.py`, `evaluate_tree.py`, `bounds.py` | Cluster bootstrap with shared draws; Hoeffding radius | Cluster = instance |
| `controllers.py` (`matching_report`) | Information / capacity / tuning parity across arms | New arm list |
| `learners.py` | Ridge, utility-deficit and failure-risk learners | Tabular baselines; the risk-vs-advantage comparator |
| `timing.py` | Two-step continuation-value rule | Baseline for budgeted verify |
| `configurator/` | Serialiser rules, encoder slot, heads | Architecture family (c); serialiser retargeted to ledger events |
| `allocator.py` | Two-phase batch allocator | Offline batch evaluation only; deployment uses the online spending rule |
| `replay_validity.py` | Population allowance | Appendix only |

**Carry over: principles**
- original-population estimands: no conditioning on valid metrics; skipped and invalid trials stay in;
- collection failure is an integrity status, never a utility value;
- treatments are executed by the control plane and are never optional for the LLM (the old D-COMPLY);
- primary contrasts are declared before the data that tests them;
- a hindsight-oracle headroom gate runs before training;
- evidence runs need an author-made authorization note;
- AI-assisted work is labelled as such.

**Archived (no authority; kept for provenance)**
- every file of the old `docs/paper_split/`: plans, runbooks, decision sheets, reviews, prompts, claims ledger, scope;
- the candidate-consistency task and its realism reports;
- the N1 / N2 hypotheses, the 0.02 U target, P-B1, and the cutoffs;
- the Pi-backed executor plans, the Devstral / Ada binding plan, and the DAC configurator amendment as a framing document.

**Legacy code and manuscript** (moved to `archive/old_b_2026-10-09/code/` on 18 Oct 2026; see §10)
- `experiments/paper_b/task_cc*`, the Pi path in `control/executor.py`, `control/world.py`, `control/tree.py`;
- `protocols/paper_b/` (contracts v1–v3, launch validator);
- `papers/paper_b/` (the old manuscript);
- release scripts.

They stay where they are only because tests and release tooling import them. RUNBOOK task 0.1 decides whether to move them into the archive once R1's reuse is settled. Treat them as read-only history.

## 9. Venue, quality bar and timeline

**Venue (decided 9 Oct): TMLR.**

> **Superseded 24 Oct (R1-VENUE-3): ICML 2027.** Only the venue changed; the timeline and quality bar below stay as they are.
- TMLR accepts when claims are supported and of interest to part of its audience. There is no novelty-magnitude bar, and there is no deadline pressure.
- Paper A also targets TMLR. Cite it anonymously as a companion.
- TMLR pauses over the holidays; check the dates before planning a submission around them.
- A conference version stays possible if the results are ready before a suitable deadline. Decide at the end of Phase 3; nothing is planned around one.

**Quality bar: ICML main-track standard (decided 9 Oct).** Concretely, the paper must meet all of the following before submission.

1. **Clarity and length.** The core argument is concise, and the rest goes to the appendix. No template or page count is fixed yet (R1-FORMAT). TMLR's own regular/long-submission threshold is checked when the format is chosen.
2. **Baselines.**
   - The strongest relevant baselines, re-implemented and tuned with the same budget as our arms.
   - At least: the C2 index policy, a PACE-style gate, a racing-style rule, an AWR-MLP controller in the style of Harness-MDP, a noise-aware threshold, harness heuristics, and HPO-style schedulers where the action is HPO-like.
   - No strawmen. The tuning protocol is identical for every arm, and `matching_report` checks it.
3. **Statistics.**
   - Primary contrasts, sample sizes and analysis are pre-declared.
   - Cluster-bootstrap intervals by instance, with multiplicity stated.
   - Held-out instances and a held-out node.
   - Effect sizes stated in practical units.
4. **Ablations and mechanism.**
   - An action ablation.
   - Information ablations (with and without LLM text, with and without remaining budget).
   - A model-size ablation for family (b), only if family (b) is trained.
   - The ladder V^ρ ≤ V^L0 ≤ V^greedy ≤ V^RL.
5. **Generalisation.** Transfer to a held-out benchmark (leave-one-benchmark-out) and a second manager model, both reported.
6. **Theory.**
   - C2 (acceptance under noise) is the main theory. Its statements carry full proofs, an AI-assisted audit and the author's own check, and its predictions are checked against measured σ_n and ϱ.
   - Assumptions are stated where they are used.
7. **Reproducibility.**
   - Code, configs, seeds and compute reported per arm.
   - An anonymised artifact.
   - Every number regenerated by a script from committed data.
8. **Positioning.**
   - The novelty sweep is rerun within 4 weeks of submission.
   - An explicit differentiator against each of the closest works (§3), including ranking & selection, knowledge gradient, racing and best-arm identification.
9. **Honesty.**
   - Negative and null results reported.
   - AI assistance disclosed.
   - Workshop-paper overlap disclosed.

**Internal milestones** (planning targets, not promises):

| Milestone | Target |
|---|---|
| Phase 0 complete; open decisions taken | ~31 Oct 2026 |
| C2 theory draft (derivations and simulator, T1–T3) | ~15 Nov 2026 |
| Phase 1 headroom gate | ~15 Dec 2026 |
| Phase 2 configurator selected (only if the gate passes) | ~31 Jan 2027 |
| Phase 3 deployment analysed | ~28 Feb 2027 |
| TMLR submission | ~31 Mar 2027 |

## 10. Open decisions

D1–D13 are defined in `inputs/PROBLEM_SPEC_DRAFT_20261009.md` §9, each with options and a recommendation. They are decided at the Phase 0 STOP using Phase 0 numbers, except where a phase needs one earlier.

**Decided 9 Oct 2026 by the author (recorded from `prompts/BUILD_BATCH1_PROMPT.md`).** These rows are fixed, not proposals.

| ID | Decision (decided 9 Oct 2026 by the author) |
|---|---|
| D1 | Budget is **compute** (worker runs; worker-seconds on mixed nodes) plus an **LLM-call cap**. The trial-count budget stays available. |
| D3 | Core actions: **continue, skip (E1), revise (E1), verify with demote (E2), stop (E0)**. |
| D4 | The keep rule is overridden **only by verify's frozen response**. |
| D14 | Harness changes go on **branch `r1` of `~/Documents/autoresearch_harness`**; analysis code goes in **`~/Documents/agent_paper_B/r1/`**. |
| D19 | Worker backend **`LocalWorker`**; do not initialise the claw-code submodule. |
| D20 | **ML-research benchmarks only** (MLGym, MLAgentBench, MLE-bench Lite plus an OpenML pool). Not needed in this batch. |

**Decided 9 Oct 2026 by the author (recorded from `prompts/BUILD_BATCH2_PROMPT.md`).** These rows are fixed, not proposals.

| ID | Decision (decided 9 Oct 2026 by the author) |
|---|---|
| D15 | Manager model for local runs: **`qwen2.5-coder:7b` via Ollama, pinned by digest**. |
| Verify split policy | Keep the **default `"fixed"` for every node**. The Phase 0 noise pilot (E1) measures train-seed versus split-seed noise per node before anything changes. |
| D20 (OpenML pool, batch 2) | The local OpenML pool for this batch is **5 small binary-classification datasets** selected by the L8 criteria (binary; ≤20k rows and ≤100 features; preferably OpenML-CC18; seconds per run on CPU; permissive licence), recorded with their IDs. |

**Decided 12 Oct 2026 by the author (R1-REFRAME, R1-INDEX, R1-GATE-FIRST).** These rows are fixed, not proposals.

| ID | Decision (decided 12 Oct 2026 by the author) |
|---|---|
| R1-REFRAME | The headline is incremental acceptance under noise, and C2 is B's own theory (§1, §3). |
| R1-INDEX | The primary contrasts are learned arms vs the C2 index policy. LLM self-control stays, with a stronger manager at least as a deployment check (§5). |
| R1-GATE-FIRST | Phase 0 answers the noise-node and pilot-headroom questions before any model is built. D16 and L11 are deferred until the gate passes. Fallback = C1 + C2 (§3). |
| R1-COMPUTE (12 Oct, evening) | **No LLM runs on the Mac.** Every LLM workload goes to deepthought (deepthought2.etp.kit.edu, `/ceph/dwong/`) or Ada: the manager, LLM self-control side queries, LLM-backed pilots and any model training. The Mac does code, docs, CPU-only pilots with the scripted proposer, and analysis. D15 keeps `qwen2.5-coder:7b` pinned by digest, now served on deepthought. |

**Decided 12 Oct 2026 by the author (Deepthought batch 1 follow-up).**

| ID | Decision (decided 12 Oct 2026 by the author) |
|---|---|
| R1-COMPUTE (batch 1 fallback host) | For Deepthought batch 1, **`deepthought.etp.kit.edu` may be used if a GPU is idle**, in addition to the originally named `deepthought2.etp.kit.edu`. This records the author's reply "Use deepthought.etp.kit.edu if idle". The pinned D15 model, no-Mac-LLM rule, shared-machine constraints and open E2 decisions are unchanged. |
| R1-COMPUTE (batch 1 automatic resumption) | Author follow-up on 12 Oct: keep checking both authorized Deepthought hosts and automatically resume DT1–DT4 when a GPU has no other user process. **The one-hour GPU wait limit is lifted.** Keep the exact pinned 7B model and all other rules. Before DT1 latency or later campaigns, verify actual GPU offload using Ollama VRAM telemetry and a process on the selected card; CPU fallback is a STOP. |
| R1-COMPUTE (batch 1 Ada migration) | Author follow-up on 12 Oct: **use Ada GPU 0** (`experiment_zhixu`, hostname `ucrtasl`) for DT1–DT4. Prepare fresh R1 checkouts, run both suites and verify the same pinned 7B model’s actual GPU offload before proceeding. Prevent duplicate runs on Deepthought by disabling the previous launch watchers and retaining their shared claim. All other batch rules and open E2 decisions are unchanged. |
| R1-COMPUTE (Ada environmental test exception) | Author follow-up on 12 Oct: treat the Ada missing `/bin/zsh` failure in `TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm` as environmental. Continue DT1–DT4 on Ada GPU 0 **once duplicate Deepthought runs are prevented and the same pinned 7B model passes actual GPU offload**. This exception applies only to the missing-zsh failure; all other rules remain in force. |
| R1-COMPUTE (Ada idle-card selection, 13 Oct) | Author follow-up: for **unstarted DT2–DT4, use an idle Ada GPU instead of waiting for GPU 0**. Select one card with no processes, retain the exact pinned 7B model, reverify offload on the selected UUID, prevent duplicate launches and preserve all old claims/results. All other rules and open decisions remain unchanged; DT1 is not repeated. |

**Decided 13 Oct 2026 by the author (GPU co-tenancy; DT4 rerun).** These rows are fixed, not proposals.

| ID | Decision (decided 13 Oct 2026 by the author) |
|---|---|
| R1-COMPUTE (GPU co-tenancy, 13 Oct) | **A GPU may be shared with other users' processes when its free memory is enough for our workload; LLM latency is descriptive only.** This records the author's decision "显存够就允许共卡，延迟只当描述性数据" (if the VRAM is sufficient, sharing a card is allowed; latency is treated only as descriptive data). It replaces the "idle card / no other user process" condition in the earlier R1-COMPUTE rows, for Ada and Deepthought alike. Unchanged: never stop or disturb other users' jobs; one card per manager instance; the exact pinned D15 model; actual GPU offload verified on the selected card (Ollama `size_vram > 0` and our process on that card), with CPU fallback a STOP; duplicate-launch prevention; no-Mac-LLM rule. Latency and throughput are recorded together with a GPU census (other processes, free memory, utilisation) and reported as descriptive; no result, threshold or gate depends on them. |
| R1-COMPUTE (DT4 rerun, 13 Oct) | Author: "现在就改启动脚本，然后在 Ada 上把 DT4 重新排上" (update the launch scripts now, then re-queue DT4 on Ada). A **fresh DT4 attempt on Ada** under the co-tenancy row, with DT4's design unchanged: `digits_mlp` and `openml_ionosphere`, 6 instances each, W = 20 worker runs, E2 points 4/8/12, continue and verify (r = 2, frozen response), 2 repetitions, 6 audit seeds, `"fixed"` split, pinned `qwen2.5-coder:7b`. DT1–DT3 are not repeated. The interrupted attempt `results/r1/pilot/E1b_20261013T090510Z` stays preserved and is never resumed or analysed. Runner `r1/scripts/ada_rerun_dt4.py`, started with `r1/scripts/ada_dt4_rerun_launch.sh`. The model is kept resident (`OLLAMA_KEEP_ALIVE=-1`) and must be fully offloaded (`size_vram = size`) at load and after collection. Output is PILOT. |
| R1-COMPUTE (DT4 commit-only recovery, 13 Oct) | Author: "我同意" (agreed, 22:50) to the proposed recovery after the DT4 rerun stopped at artifact staging (collection complete: 144 leaves, 0 collection or parse failures; the tables Markdown ended with a blank line, which failed `git diff --check`). **No re-collection.** Fix the generator (`e1b_analyze.markdown` ends with one newline; test added); in the Ada batch clone, re-run `e1b_analyze` on the existing collection, which must reproduce `analysis.json` byte for byte (otherwise STOP); commit the collection, tables and report; run the committed-data regeneration check; record a recovery STATUS entry. The after-collection offload check passed but its telemetry was not saved; this is recorded as a gap, not repaired. Prompt: `docs/r1/prompts/ADA_DT4_RECOVERY_PROMPT.md`. |

*Operational default for "enough memory" (proposed by the AI agent when recording this row; the author may change it):* at selection and again before each step, the card's free memory must be at least the workload's measured footprint plus 2 GiB (for the pinned 7B model: about 5.2 GiB `size_vram` + 2 GiB ≈ 7.2 GiB free). A card that falls below that during a run, an out-of-memory error, or an Ollama fallback to CPU is a STOP for that step; it is not retried automatically.

**Decided 14 Oct 2026 by the author (proposer decisions after the ionosphere diagnosis).** These rows are fixed, not proposals. The author adopted all five proposals of `docs/r1/reports/PROPOSER_DECISIONS_20261014.md` ("草案的五条建议全部采纳"); that file gives the facts and options behind each row.

| ID | Decision (decided 14 Oct 2026 by the author) |
|---|---|
| D24 | **Manager memory mode.** Primary proposal law for every LLM-backed R1 run: `append_only_summary`. Before it is used, the summary line shows the node's own `metric_name`, handles a metric of exactly 0.0, and the best-strategy line respects `metric_direction`. `none` is kept only as a declared secondary contrast in E1b (DT4 is its first arm). The collector takes the memory mode from the manifest, never as a literal; manifests without the field mean `none` (historical runs). Branch continuations use the same memory mode as their root. |
| D25 | **Node-declared active keys.** Each node may declare which editable keys are active for the current configuration (for the OpenML template: keyed by `model_type`, plus dataset-level exclusions such as `imputer` without categorical columns). The manager is shown only active keys; a proposal naming an inactive key is rejected before any worker run, as a validation failure the manager may revise (it costs LLM calls, not runs). The scripted stand-in reads the same declaration instead of its private `OPENML_ACTIVE`, and its proposal sequence for existing seeds must stay identical. Nodes without a declaration behave exactly as before. All other nodes are audited for inert keys before E3. |
| D26 | **Manager sampling seed.** Temperature stays 0.2 (D15). Every manager call gets an Ollama `seed` derived deterministically from (instance, trial index, repetition), recorded in its `llm_call` event. Reproducibility measure only. |
| D27 | **No-op and duplicate edits.** Record-only flags on every trial: effective config equal to the incumbent's, equal to an earlier evaluated config, or metric bit-identical to the incumbent's. They count as wasted runs in C1 and change no behaviour in the primary arms. Add an E1 harness-heuristic arm that skips a known no-op or duplicate (the PLAN §5 doom-loop skip). |
| D28 | **Node liveness check before LLM-backed collection.** Per node, with the chosen memory mode: 1–2 instances, W = 10, no branching. Pass requires at least one keep after trial 1, at least 50 % of trials with a metric different from the incumbent's, and an invalid rate below 30 % (thresholds as proposed, adopted). A failing node is fixed or excluded and recorded in STATUS; the batch runner enforces the check as a STOP. |

**Decided 14 Oct 2026 by the author (after the batch-3 review).** These rows are fixed, not proposals. The author agreed to the coordinating session's recommendations ("我同意你建议的决定"). The D4 amendment (run-free acceptance rules) was **not** decided and stays open; it is not part of the rerun below.

| ID | Decision (decided 14 Oct 2026 by the author) |
|---|---|
| D27 (F3 fix) | `config_seen_before` must cover configurations evaluated before a resume, **without changing `TrialRecord` bytes**. The `edit_novelty` event carries `effective_config_sha256` and `active_config_sha256` (projection on the node's active keys; equal to the full configuration on undeclared nodes) and two further flags, `active_config_equals_incumbent` and `active_config_seen_before`. An E2 snapshot stores the sets of hashes seen so far, and `resume_campaign` seeds them; snapshots without these sets mean "unknown before resume", which is documented, not silently treated as empty. |
| D28 (revised criterion 2) | Criterion 2 becomes **novelty**: at least 50 % of evaluated trials must have an active-key configuration that differs from the incumbent's and from every configuration evaluated earlier in the campaign, including before a resume. This replaces "metric different from the incumbent's", which cannot tell a stuck proposer from a node whose metric is insensitive to small edits (`openml_wdbc` scripted smoke: 7/18). Criteria 1 (a keep after trial 1) and 3 (invalid rate < 30 %) are unchanged. Ledgers without `edit_novelty` events (DT4 and older) are scored by replaying their structured edits from the start configuration. The **memory-off contrast arm** of D24 is exempt from the gate: node eligibility comes from the memory-on liveness check. |
| R1-E1B-RERUN2 (14 Oct) | **LLM E1b rerun on Ada (PILOT).** Nodes `digits_mlp`, `tabular_mlp`, `openml_ionosphere`, `openml_breast_w` (`openml_wdbc` deferred until the revised D28 is in place; D21 itself stays open). 18 instances per node (k = 0–17, so the first 6 are the DT4 instances). Design otherwise as DT4: W = 20 worker runs, E2 points 4/8/12, continue vs verify (r = 2, frozen response), 2 repetitions, 6 audit seeds 5001–5006, `"fixed"` split. Three arms on the same harness head: **(A) LLM, `append_only_summary`** (primary); **(B) LLM, `none`** (contrast; T2 Proposition 5 predicts that memory raises g and lowers the value of verify); **(C) scripted stand-in** (reference, CPU). D28 LLM liveness (memory on) runs first and gates arms A and B. Nodes that fail are excluded and recorded. |

**Decided 14 Oct 2026 by the author (before the Ada rerun-2).** This row is fixed, not a proposal.

| ID | Decision (decided 14 Oct 2026 by the author) |
|---|---|
| R1-COMPUTE (Ada environmental test exception 2) | Treat the harness test `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` as **environmental on fresh Ada checkouts**, in addition to the missing-`/bin/zsh` exception of 12 Oct. It checks a checked-in workshop-paper report, which is absent from a fresh clone (documented as a generated-report flake in STATUS, 12 Oct), and it does not touch R1 code. The rerun-2 launcher's accepted-failure set gains exactly this one test ID, for Ada only. Every other failure still refuses `--start`. |

**Decided 18 Oct 2026 by the author (C3 route; legacy code).** These rows are fixed, not proposals.

| ID | Decision (decided 18 Oct 2026 by the author) |
|---|---|
| R1-C3 (18 Oct) | **C3 is the adjusted route A: a learned per-proposal prior under the C2 rule.** A predictor emits (π, μ, τ) for each proposal before execution; the rules of T4 Propositions 6 and 8 decide skip (E1) and keep (E2). Arms form a ladder (index policy → rules → tabular → LLM zero-shot → small LM SFT → small LM decision-focused GRPO); online RL only if the DI test calls for it. Records the author's "我其实挺欣赏你A调整后的路线，我们把它定为C3". Supersedes the 9/12 Oct C3 (configurator vs index policy on verify-based control) and C4 as written. Design: `docs/r1/C3_DESIGN.md` (proposal); theory: `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` (AI-assisted, unchecked). The C3 gate, D18, D21, D23 and the D4 amendment remain open. |
| RUNBOOK 0.1 (legacy code, 18 Oct) | At the author's request, **all old-route code moved to `archive/old_b_2026-10-09/code/`** (experiment scaffold, `experiments/paper_b`, `protocols/paper_b` and the Pi provenance files, release tooling, `scripts/`, the legacy test suites, `third_party/pi`, `results/paper_b`, `results/validation_logs`, `PROVENANCE.md`, `requirements.lock`). Allowed by RUNBOOK 0.1 because `r1/` imports none of it; the legacy tests moved with it and still pass there (212 / 6 / 12; `make legacy-test`). |

**Decided 18 Oct 2026 by the author (open Phase 0 decisions; C3 ladder and gate).** These rows are fixed, not proposals. The author adopted all recommendations put to them on 18 Oct ("开放决定，我认为你的建议合理，全部采纳") and confirmed C3 as route A with the baseline ladder and the proposed C3 gate ("C3主要按路线A走，做基线阶梯。C3提议门槛加进去").

| ID | Decision (decided 18 Oct 2026 by the author) |
|---|---|
| D4 amendment | **Allowed.** A declared, frozen, run-free acceptance rule may exist as its own action version. Primary instance: the Bayes keep threshold t* = −μσ²/τ² (T2 Proposition 1; T4 Proposition 6), with a constant prior in arm A1 and a per-proposal prior in arms A3–A6. In the same decision: (i) verify gains a **posterior-mean response** as a new declared version, and "D̄ > 0" is kept for continuity; (ii) when every verify pair fails, the **original decision stands** and `verify_failed` is recorded. |
| D21 | Noise nodes: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`. Re-measure `openml_credit_approval` and `openml_diabetes` with 30 seeds. `lr_synthetic` and `mlp_synthetic` are engineering-only. `mlagentbench_vectorization` is excluded (timing metric). Fetch and measure `openml_credit_g` on the Mac. **Extend the pool to at least 8 qualifying nodes** for leave-one-node-out (OpenML datasets and MLP nodes, L8b-style). Before `digits_mlp` is used with memory on, diagnose why it failed D28 liveness on 14 Oct (no keep after trial 1). |
| Verify split policy | **`"vary"` on every node.** It replaces the 9 Oct "fixed everywhere" default. Under `"fixed"`, verify is a no-op on the OpenML logistic-regression nodes (σ_train = 0; T2 Proposition 3), and `"vary"` is never less informative. |
| D18 | Practical target δ_n = max(0.002, 0.25 × median paired sd(Δ̂)) per node, in metric units (≈ 0.002 on `digits_mlp`, ≈ 0.004 on `openml_ionosphere` with E1 numbers). It is also the unit of the C3 gate, scaled to a 20-run campaign. |
| D23 | **Primary comparator: the KG-style index policy with a constant (node-level) prior**: a constant Bayes threshold, constant-prior screening, and KG verify priced on the executed response under the campaign split policy. This is arm A1 and the floor of the C3 ladder. The PACE-style gate is a secondary comparator (appendix), as its own verify version. |
| R1-E1B-RERUN2 (revision) | **Not re-run as designed.** First read the cause of the 14 Oct collection failure from the preserved Ada logs. Then convert the run into the C3 label sweep: root campaigns only (no branching), memory `append_only_summary` and `none`, `"vary"` split, nodes per D21, W = 20, with fresh-seed audits of evaluated proposals (C3_DESIGN §4). |
| R1-C3 (ladder) | C3 is evaluated as the arm ladder A0–A6 of `C3_DESIGN.md` §5: ρ → constant-prior index policy → rules → tabular → LLM zero-shot → small LM (SFT) → small LM (decision-focused GRPO). Online RL (A7) only if the DI test calls for it. The reference arms of §10 are added: SAGE-style gate, FOREAGENT-style pairwise predictor, Ladder margin rule, posterior-mean incumbent. |
| C3 gate | **Proceed to online deployment only if** the offline one-step gain of A3 or A5 over A2, scaled to a 20-run campaign, reaches δ_n (D18) on at least two nodes, with its lower 95 % bound above 0. **Otherwise** C3 is reported as a measured negative, explained by T4 Proposition 7's dispersion bound, and C1 + C2 carry the paper. This replaces RUNBOOK 1.5 for C3. |

**Decided 18 Oct 2026 by the author (placement of the add-ons).** Fixed, not a proposal.

| ID | Decision (decided 18 Oct 2026 by the author) |
|---|---|
| R1-C4 (18 Oct) | **Route B joins C2; route D becomes C4 (secondary): proposer feedback.** C4 is the DI test plus the debiased-memory A/B (`C3_DESIGN.md` §7). It replaces the 9 Oct C4 ("configurator training recipe"), which R1-C3 superseded. Records the author's "同意“B 并进 C2、D 列为 C4”". |

**Decided 19 Oct 2026 by the author.** Fixed, not a proposal.

| ID | Decision (decided 19 Oct 2026 by the author) |
|---|---|
| Partial rerun-2 arm A (19 Oct) | **The preserved, interrupted R1-E1B-RERUN2 arm A (memory on; 648 leaves, 7 failed) may be snapshotted into the repository and analysed as a PILOT diagnostic for the C4 DI test.** It is not resumed or completed and is never evidence. This is an exception to the default "preserved, never analysed" handling of interrupted batches. Records the author's "我授权". Prompt: `docs/r1/prompts/ADA_DI_TEST_MEMORY_ON_PARTIAL_PROMPT.md`. Any DI test uses absolute metrics or audited values, never Δ̂ relative to branch-specific records (DI_TEST_E1B_20261019 addendum). |
| Duplicate ≠ no-op (19 Oct) | **Rule-detectable proposals are split into two kinds.** A *no-op* leaves the incumbent's active configuration unchanged (Δ = 0). A *duplicate* repeats an earlier evaluated non-incumbent configuration: its result is known, Δ is generally ≠ 0, and under ρ it can never be kept (T4 Corollary 8a(iii)). The rule layer (A2+) skips both. Only no-ops get the zero label; duplicates get no training label, and in offline evaluation an arm without the rule layer that keeps one is charged its audited Δ (or the logged Δ̂ as a counted proxy). Implemented in `r1/c3/` (`noop`, `duplicate`, `rule_skip`, `known_metric`). Records the author's "我同意拆开，去改". |
| R1-COMPUTE (Paper A coordination, 19 Oct) | **No Paper B GPU workload starts on Ada while a Paper A live campaign there is waiting for a card.** Paper A's replay panel v4 live (repository `agent-checkpoint-intervention`, branch `paper-a-v4-ada`, RUN `results/paper_a/replay_panel_v4/live_20261018T234416Z`) needs a fully idle card for its first start. Paper B's co-tenancy rule (13 Oct) would otherwise let a Paper B process occupy a card that was about to become idle. Before any Paper B GPU launch on Ada (the C3 label sweep, a memory-on branch run, or anything that starts Ollama or training), the operator: (i) checks the Paper A run's status; (ii) proceeds only if no Paper A live campaign is waiting for a card, i.e. it has its card and is computing, or it has finished or stopped. Otherwise the operator waits or runs the workload on Deepthought instead. CPU-only and file-only Paper B work (diagnostics, audits on CPU, analysis) is unaffected. Paper B never stops, signals or competes with Paper A processes. Records the author's "把这条协调规则写进 PLAN". |

**Decided 22 Oct 2026 by the author (before the first C3 label sweep).** These rows are fixed, not proposals. The author adopted option A for decisions 1–3 and the coordinating session's recommendations for the node pool and `digits_mlp` ("决定1用方案a，决定2也用方案a，决定3也用方案a，两个小决定按照你建议来").

| ID | Decision (decided 22 Oct 2026 by the author) |
|---|---|
| Duplicates (22 Oct; confirms 19 Oct) | **Option A.** Confirms the 19 Oct "Duplicate ≠ no-op" row: three rule-detectable kinds — *inactive edit* (changes only keys inactive for the node's model; Δ = 0), *incumbent repeat* (returns to the incumbent's active configuration; Δ = 0), both counted as **no-ops**; and *duplicate* (repeats an earlier evaluated non-incumbent configuration; result known from the ledger, Δ generally ≠ 0). The rule layer (A2+) skips all three, and the run each skip saves is credited to A2 as in the run-accounting row below. Duplicates are **excluded from LM/tabular training and from the learned-arm evaluation set**; they are counted separately. **New:** C1 reports the duplicate rate and the runs they would cost as wasted runs, per node and memory mode, next to the published 28–63 % ("Visible but Not Avoided", arXiv 2610.15738). |
| g (22 Oct) | **Option A.** Run price g = 0.1 σ_node, where σ_node is the node's paired comparison-noise sd of Δ̂ (E1, the same σ that standardises the bins). Sensitivity values g ∈ {0.05, 0.2} σ_node are declared now and reported, but **the C3 gate is judged at g = 0.1 σ_node only.** g is fixed before any gate is computed on sweep data and is not changed afterwards. Replaces C3_DESIGN §1 "g is tuned on development instances". |
| Run accounting in the 20-run scaling (22 Oct) | **Option A.** In the primary analysis a skip is credited at the price g (reward r = Δ_audit · keep − g · execute); freed runs are **not** re-spent. This is a stated convention, consistent with g being declared as the value of one run, not a derived opportunity cost; the report says so. Sensitivity (wording corrected 22 Oct at acceptance; the author's choice of option A is unchanged): a literal replay is impossible because root ledgers hold exactly one proposal per run, so no logged proposal exists beyond the end of a campaign. Instead, freed runs are re-spent on further proposals exchangeable with the arm's own, under a cap of c × W LLM proposals per campaign: value = m × min(W, e·c·W), with m the arm's mean realised reward per executed proposal and e its execution rate. c = 1 equals the primary; c = 2 is reported as the sensitivity and c = ∞ as an optimistic upper bound. No pass/fail is attached to either. |
| Node pool (22 Oct) | Extends D21. Candidates to reach ≥ 8 qualifying nodes, in order: `openml_credit_approval` and `openml_diabetes` (qualify only if the 30-seed `"vary"` re-measurement shows non-trivial noise under D21's criterion); `openml_credit_g` (fetch its data cache, then measure). If fewer than 8 qualify, add 2–3 further OpenML classification datasets, measured the same way. The re-measurement is CPU-only (Mac or Deepthought). |
| `digits_mlp` (22 Oct) | **Repair rather than exclude.** It is the only node with a positive gate quantity in the pilot. Keep it in the pool; diagnose the Ollama SIGTERM and proposer repetition, then re-run D28 liveness. It stays out of memory-on collection until D28 passes. If it cannot pass, the author decides between keeping it memory-off only and exclusion, with the diagnosis in hand. |

**Decided 22 Oct 2026 by the author (noise-node rule and pool extension, after the 30-seed re-measurement).** These rows are fixed, not proposals. The author agreed to all four recommendations of the coordinating session ("我同意，把这四条写进 PLAN §10"). Declared **before** any 30-seed measurement of the original five nodes or of the new candidates.

| ID | Decision (decided 22 Oct 2026 by the author) |
|---|---|
| D21 rule (22 Oct) | **Adopted, amending E1's proposal.** A node is a *noise node* iff, measured with **30 seeds per condition** (training, split and joint seeds; `"vary"` split), it has **≥ 2 material edits** (resolved, \|Δ̂_J\| > 2 se, and \|Δ̂_J\| ≥ 0.002) on the standard E1 edit set, with **mean plug-in P(wrong) ≥ 0.10** over those edits, and σ_joint > 0. The seed count is fixed at 30 for every node, so the rule's selection cap is the same everywhere. The seed-bootstrap probability of qualifying is reported but is **not** part of the decision. Library versions (Python, scikit-learn, numpy) are recorded in every measurement manifest. |
| D21 uniform application (22 Oct) | The rule applies to **every** node, including the five 18 Oct D21 nodes, which are re-measured at 30 seeds in the same environment as the candidates. A node that fails is removed from the noise-node pool: it does not count towards the ≥ 8 target and does not enter the C3 gate; it may remain an engineering node. No exception after the results are seen. |
| D21 pool (22 Oct) | `openml_credit_approval` **added** (qualified at 30 seeds on 22 Oct; it is re-checked in the common run). `openml_diabetes` **dropped** (no material edit at 30 seeds; not re-measured). New candidates, measured together with the others: `openml_credit_g` (OpenML 31), `openml_sonar` (40), `openml_blood_transfusion` (1464), `openml_qsar_biodeg` (1494); IDs checked on openml.org on 22 Oct. Not chosen: `ilpd` (1480; same risk profile as diabetes); `climate-model-simulation-crashes` (1467) is the reserve. Data caches are fetched on the author's Mac (the VMs have no openml.org access). Optional, later: one further MLP-type node for diversity (six of the eight target nodes share the OpenML template's edit space). |
| D21 common measurement (22 Oct) | One 30-seed E1 run over all ten nodes (5 original + `credit_approval` + 4 candidates; "nine" in the first version of this row was a counting error, corrected 22 Oct), CPU only, one environment, accepted by the coordinating session before merging. This run is the C1 noise-floor table. |

**Decided 23 Oct 2026 by the author (reserve node).** Fixed, not a proposal.

| ID | Decision (decided 23 Oct 2026 by the author) |
|---|---|
| D21 reserve (23 Oct) | After the common run left the pool at exactly 8 (two nodes borderline), **measure the reserve `openml_climate` (OpenML 1467, climate-model-simulation-crashes)** with the same procedure: 30 seeds, the harness-locked environment of the common run, the standard E1 edit set, the D21 rule of 22 Oct unchanged. If it qualifies it joins the pool (9 nodes); if not, the pool stays at 8. Records the author's "把后备的 climate（OpenML 1467）也按同样流程测一下". |

**Decided 24 Oct 2026 by the author (base models, hosts, C1 floor, venue, benchmarks).** These rows are fixed, not proposals. Recorded by an AI agent (Claude, coordinating session) at the author's request.

| ID | Decision (decided 24 Oct 2026 by the author) |
|---|---|
| R1-C3-BASE (24 Oct) | **C3 decision-model base models (A5/A6).** Main: **Kev** and **StartLux-Decision**; additional rung: **Laya** (encoder; separates text-reading from prior knowledge). **Sizes ≤ 4B only.** Candidates: Kev-0.8B, Kev-4B; StartLux-Decision-v1.1 0.8B / 2B / 4B; Laya 421M (1,024-context checkpoint). CLM dropped (frozen 8B encoder, candidate-relative probabilities). StartLux weights are CC BY-NC 4.0: research use only. Kev and Laya need a short custom RL loop (pointer / encoder heads); StartLux's LM-head readout fits TRL GRPO directly. |
| R1-HOSTS (24 Oct) | Hosts: **deepthought** (4 × TITAN 12 GB, exclusive); **zhixu portal** (1 × RTX 4090 24 GB, exclusive); **zhixu experiment** (`experiment_zhixu`, 8 × RTX 6000 Ada 48 GB, shared, jobs may be interrupted: resumable overflow work only); the author's Mac is an M1 Max with 64 GB. |
| R1-COMPUTE (revised 24 Oct) | The Mac is **not used for LLM or small-model workloads while deepthought, zhixu portal or zhixu experiment can do the step**. It is a last resort only, used with the author's approval per use and labelled in STATUS. Replaces the 12 Oct "no LLM runs on the Mac" rule. Proposals within one labelled table still come from one host type (D6, D15). |
| R1-SWEEP-HOST (24 Oct) | **deepthought is the primary host for C3 label sweeps**, one pinned manager per TITAN. **No mixing hosts within one labelled table.** `r1/scripts/configs/c3_sweep_ada.json` is ported to a deepthought config (RUNBOOK A.6). |
| R1-C1-FLOOR (24 Oct) | The common 30-seed run (`results/r1/pilot/E1_20261022T214606Z/`; `reports/NOISE_FLOOR_COMMON_20261022.md`) is **accepted as the C1 noise-floor table**; pool = 8. The reserve `openml_climate` is measured under the same protocol as backup (D21 reserve, 23 Oct). |
| R1-VENUE-3 (24 Oct) | **Target venue changed from TMLR to ICML 2027** (replaces R1-VENUE-2's venue; closes R1-FORMAT: ICML template). **Only the venue changes:** the plan, the timeline and the quality bar stay as they are. |
| R1-BENCH-HARD (24 Oct) | **Karpathy's autoresearch, 1GC-7RC (2026) and MLGym (Meta) are added** to the benchmark set, to address the small-testbed weakness (RUNBOOK Track G). Their role and audit budget are still open (proposed: evaluation and transfer nodes; C3 arms trained on the CPU pool are tested on them without retraining). |
| R1-PROPOSER-QUANT (24 Oct) | Proposer (manager) models run at **Q4_K_M**. Size ceiling roughly **27B dense to 35B-A3B MoE**. Digest and quantization are pinned and reported for every run. Training stays BF16 LoRA (QLoRA only if needed). |

**Decided 25 Oct 2026 by the author (inference backend).** Fixed, not a proposal. Recorded by an AI agent (Claude, coordinating session).

| ID | Decision (decided 25 Oct 2026 by the author) |
|---|---|
| R1-INFER-LLAMACPP (25 Oct) | **LLM inference uses llama.cpp (`llama-server`), not Ollama.** The manager model is pinned by the sha256 of its Q4_K_M GGUF file and the llama.cpp build commit. Sweep 1 and every later table use this backend only (D6, D15); all Ollama-era runs stay PILOT and liveness (D28) is re-run under llama.cpp. The runner, watchdog, fake server and configs are ported (RUNBOOK A.10). |

**Decided 25 Oct 2026 by the author (proposer exam pool; DAC interface).** Fixed, not proposals. Recorded by an AI agent (Claude, coordinating session).

| ID | Decision (decided 25 Oct 2026 by the author) |
|---|---|
| R1-EXAM-POOL (25 Oct) | **Proposer exam (appendix) pool and host.** All candidates of RUNBOOK Track X enter the exam except TeichAI/Qwen3.6-27B-Claude-Opus-Reasoning-Distill-v2 (excluded by the author). The exam runs on **zhixu portal (1 × RTX 4090)**. **Size rule replaced:** instead of the 24 Oct ceiling (27B dense to 35B-A3B MoE), any model that the pinned llama.cpp build serves fully on one RTX 4090 at Q4_K_M is admissible, which brings in 31–33B dense models (Gemma 4 31B, Muse Glimmer 30B, OLMo 3.1 32B). Q4_K_M stays (gpt-oss-20b at native MXFP4 as a declared exception). The operational fit test (16k context, q8_0 KV, ≥ 1 GiB free, measured not estimated) and the exam protocol X.2–X.6 are **proposed, not adopted**. The 2026-09 Round-7 candidacy exam (Paper A repo) is reused for machinery only, not as evidence. |
| R1-DAC-INTERFACE (25 Oct) | **The DAC control-interface plan is adopted** as RUNBOOK Track H ("按你的建议来"): `PriorModel` protocol, one shared featurizer, one `RuleController` for every A1–A6 arm, a pinned small-model sidecar with fallback to the A1 prior, LLM-cap accounting, direct-action arms through the same `decide()`, Gymnasium-style offline (and, only if DI fails, online) environments. The manager-memory display of a skipped proposal (H.4) was decided the same evening (R1-SKIP-DISPLAY). |
| R1-SKIP-DISPLAY (25 Oct, evening) | **H.4 decided as proposed:** a proposal skipped by the control plane appears in the manager's memory as one line, "skipped by the control plane: predicted no gain", with no metric (author: "按你的建议来"). Recorded as a versioned display in every manifest; campaigns without the field had no skips. |
| R1-EXAM-FIT (25 Oct, evening) | **The fit estimate for exam admissibility is based on the Q4_K_M GGUF** (file size + KV at the declared context + compute buffers ≤ 23.5 GiB on the RTX 4090), confirmed by the X.2 probe. The declared context (proposed 32,768) and the revised Stage B design (B1 screen ranked on audited proposal increments, B2 power-planned finalists, roles separated) are proposals. |

**Decided 26 Oct 2026 by the author (exam execution).** Fixed, not proposals. Recorded by an AI agent (Claude, coordinating session).

| ID | Decision (decided 26 Oct 2026 by the author) |
|---|---|
| R1-EXAM-CTX (26 Oct) | Declared exam context **32,768 tokens** (q8_0 KV); a model that fits only at 16,384 is admitted for CPU-pool rows only and flagged. Measured manager prompts are ≤ 1,345 tokens; 32k is for thinking budgets and Track G code prompts. |
| R1-SCHEMA (26 Oct) | **Structured output, structure only, in both the exam and the C3 sweeps:** llama-server `json_schema` decoding of `manager_proposal/v1` (six string fields, `rationale` first; no enum of keys or values, so D25 validation and value errors stay the model's). Recorded in every manifest; under the schema a parse failure is recorded and counted, never replaced by the heuristic default. Stage A also reports free-generation parse rates (descriptive). A B2 sensitivity compares schema vs free on one node for the 7B anchor and the D22 pick. Track G free-form code nodes are not affected. Must be in place before sweep 1. |
| R1-QUANT-SOURCE (26 Oct) | GGUF source: the vendor's own Q4_K_M where the vendor publishes one; otherwise **bartowski**'s imatrix Q4_K_M; gpt-oss-20b at native MXFP4. Every file recorded with repo @ revision, file name and sha256. Non-uniform research quants (e.g. ISTA-DASLab GSQ-RCO, IQ2–IQ3 types) are not Q4_K_M and are not in the pool. Replaces the "quantize from BF16" policy of X.1. |
| R1-EXAM-RUNBOOK (26 Oct) | Host facts, code gaps and the exam steps go into one agent runbook, `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md`, executed step by step by one agent with SSH access to zhixu portal, with a STOP after every phase. The X.2–X.6 protocol itself still awaits adoption (Phase 4 gate). |
| R1-EXAM-PROTOCOL (26 Oct) | **Exam protocol X.2–X.6 adopted** with two amendments: (1) thinking off is the primary mode for every model that can switch it off, with thinking on (2,048-token budget) on one node and the better mode carried into B2; always-thinking models use a 2,048-token budget; (2) B1 and B2 are evidence runs and need authorization notes. The B1 precision estimate is corrected to ≈ 80–110 audited proposals per model (rough se ≈ 0.001). |
| R1-EXAM-REVIEW (26 Oct) | **Independent review at every exam phase:** the executing agent spawns a fresh independent reviewer agent; the reviewer reviews, the executing agent fixes, the independent reviewer accepts (review files in `docs/r1/reviews/`). The executing agent never accepts its own phase. |
| R1-A1-VERIFY (26 Oct) | **Q10 (Track H): A1 keeps its D23 definition including KG verify.** That KG verify cannot pay at g = 0.1 σ_node with r = 2 (VoI < 0.4 σ_cmp ≤ 2rg when σ_cmp ≤ σ_node) is reported as a theory prediction confirmed in the deployment, consistent with T2 Proposition 5 and E1b; g is not changed to make verify fire. |
| R1-EXAM-HOST (26 Oct) | **The whole exam runs on zhixu portal only** (restates the author's 25 Oct "we test on the 4090"; one host type for every exam table). RUNBOOK X.6 no longer allows zhixu experiment for a Track G node; a Track G node enters B2 only if it runs on the portal beside the manager within the fit rule. Stage A probes at 32,768 with a 16,384 fallback probe (CPU-pool rows only). Resolves the two conflicts the exam agent reported before Phase 0. |
| R1-C3-POST (26 Oct) | **Track P revised and adopted as a whole** (spec `docs/r1/TRACK_P_POST_TRAINING.md`, RUNBOOK Track P): belief and action are separate outputs — the 12-bin belief is trained only with bounded proper scores (RPS; CE in supervised A5 only), the decision reward trains only an execute/skip action output; the 25 Oct A6 objective (12 bins as actions + KL, deploy the greedy bin) is dropped, the smoothed-rule loss is an ablation; hard labels are never used for training; RL rewards never contain the log score; decision-model exam P.3a (label-free E0 + probes E6) and P.3b (labelled screen with a pre-committed rule) narrow A5/A6 to 1–2 finalists; reasoning arm P.6. Recorded by the coordinating session from the author's answers in chat. |
| R1-C3-CONTROL (26 Oct) | P.1 adopted: Qwen3.5-0.8B-Base and -4B-Base + LoRA as the control (same base as Kev) and guaranteed-trainable fallback; always carried as an ablation arm, not counted among the finalists. |
| R1-SOFT-SIGMA (26 Oct) | Soft-label width s = σ̂_node/√K_label with σ̂ pooled from the C1 30-seed noise-floor table, replacing the per-proposal se_audit (5-seed variances are too noisy); new versioned `labels.soft_label` mode, old mode kept for reproducing existing tables. |
| R1-PORTAL-SCHEDULE (26 Oct; amended the same day: evidence marker) | The 4090 on zhixu portal: Track X evidence phases (B1, B2) have priority; Track P uses the card only in the gaps (P.0 and P.3a during Track X's code phase, otherwise after B2); one GPU job at a time via `flock ~/r1_locks/gpu0.lock` plus a check that no other compute process is on the card; Track P never pre-empts a Track X evidence run.  **Amendment (author, 26 Oct):** while Track X B1 or B2 runs, the file `~/r1_locks/trackx_evidence.active` exists on the portal (created before the first B1 job, removed after the last B2 job or when the phase is stopped for good), and the Track X agent pushes STATUS headings `## <date> — Track X B1 running` / `B2 running` / `B2 done` (or `stopped`). The marker is authoritative for the Track P GPU lease; STATUS is the fallback. |
| R1-JEV-RUNG (26 Oct) | The Jev zero-shot rung is run, through **TypeSafe's official API** with the author's key: a versioned model name pinned (never an alias), the version returned by the API, endpoint, date and full request/response logged, three repeats per state; proposal diffs and loop state are sent to TypeSafe (accepted by the author); Jev outputs are never labels. |
| R1-RB-TEACHER (26 Oct) | The P.6 warm-up demonstrations (≈ 500) are written by **DeepSeek-V4.1-Flash-1017** (`deepseek-flash`) via the DeepSeek API, from the same leak-guarded view the decision model sees and never with labels or audit fields; the returned model version, prompts and outputs are logged; off-peak hours; R-B is reported as a distilled arm. |
| R1-TRACKP-RUNBOOK (26 Oct; revised the same night) | Track P is executed by one agent (Claude Code) **running on zhixu portal itself**, started by the author, following `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`: its own clone of the repos in the Track P work dir on the portal, code and CPU-only unit tests there, GPU jobs in `tmux` under the GPU lease, API calls from the portal, keys only in `~/.config/r1/secrets.env` (mode 600; never read, printed or passed on a command line), labels pulled from `main`; a STOP and an independent review after every phase (same loop as R1-EXAM-REVIEW). The Mac runs no Track P work. Replaces the first version of this row (agent on the Mac driving the portal over SSH); decided by the author. |
| R1-EXAM-STORAGE (26 Oct, STOP 0) | **Author approved** `/home/dowling/exam-x/models` and `/home/dowling/exam-x/work` (author corrected the initially supplied `/ceph` paths after the portal check found no `/ceph` mount). Stop any download or run if available space on that filesystem falls below **100 GB (100,000,000,000 bytes)**. Verify the actual filesystem and enforce the floor before and during downloads/runs; use these corrected home-directory paths; do not substitute another filesystem. |
| R1-EXAM-LICENCES (26 Oct, STOP 0) | **Author approved the exam licences for research evaluation and publication of results**, including Nemotron (OpenMDW-1.1), Laguna XS 2.1 (OpenMDW-1.1), and LFM2.5 (LFM 1.0). This is the author's decision, not an agent's legal determination or a claim that authenticated gated-repository access has been configured. |
| R1-EXAM-ORNITH (26 Oct, STOP 0) | **Remove Ornith-1.0-31B from the pool, with no substitute:** not publicly released (author checked 26 Oct: `ornith-ai`, `deepreinforce-ai` and the official collection list only 9B, 35B, 397B). Effective pool: **21 candidates and 3 anchors**, plus the declared OLMo Think sensitivity. The 35B candidate maps to `ornith-ai/Ornith-1.0-35B` (35B-A3B, MIT). In Phase 2 check vendor `ornith-ai/Ornith-1.0-35B-GGUF` for Q4_K_M first, as required by R1-QUANT-SOURCE. |
| R1-EXAM-TRANSFER (26 Oct, STOP 0) | **No GitHub credentials on portal.** Push code from the Mac over SSH to bare repositories under `/home/dowling/exam-x/work/`, then check out from those repositories into the approved work location. Keep bare repositories (e.g. `work/remotes/*.git`) separate from working checkouts under that same approved work directory. Never push protected branches to GitHub or transfer credentials. |
| R1-EXAM-USER-RUNTIME (26 Oct, STOP 0) | **Author permits installation of uv and user-level Python >=3.11 under `/home/dowling`**, no sudo and no changes to system Python. Record installed paths/versions. STOP 0 disk/licence/identity decisions are resolved by these rows; proceed with Phase 1 and its independent STOP 1 review. Later phase and evidence authorisation gates remain in force. |

**Decided 26 Oct 2026 by the author (Track P after the overnight run).** Fixed, not proposals. Recorded by an AI agent (Claude, Track P agent on zhixu portal) on branch `trackp-20261026` from the author's decisions in chat, answering the questions of `docs/r1/reports/TRACKP_OVERNIGHT_20261026.md`.

| ID | Decision (decided 26 Oct 2026 by the author) |
|---|---|
| R1-STARTLUX-TRAINABLE (26 Oct) | **StartLux Instant is a trainable candidate** (runbook STOP 3; resolves spec §5.1 "only if P.0 passes training"). Its CC BY-NC 4.0 licence (non-commercial research use) is noted in the model registry (`r1/c3/train/registry.yaml`) and in the appendix. *(Implementation note by the Track P agent, not the author's wording: until a rule v2 drops StartLux from `pending_author_families`, its P.3b records carry `author_rung: trainable` with this row.)* |
| R1-E0-PROTOCOL (26 Oct) | **E0 protocol fix before any Phase 5 evidence run** (spec §5.5, v2): (a) the width slope regresses the predicted std on the **label's own std** (the binned soft label's std with the same bin representatives); the label's own slope vs s is reported as the ceiling; the same reference applies to A4. (b) **Train to convergence**: validation cells held out of the training grid, early stopping, at most 2,000 steps, the same budget for every model. (c) A **fresh LayerNorm + linear belief head at lr 1e-3 for every model**; released heads are reported separately. The DRYRUN is re-run on Kev-0.8B and Qwen-0.8B under v2 and reported; **the author then sets the E0 and A4 thresholds in a PLAN row** and writes the Phase 5 authorization. |
| R1-A3-BUDGET (26 Oct) | **A3** prepends irrelevant history at **0 / 25 % / 50 % / maximum of the remaining token budget**, using the **smallest context limit in the pool** (1,024 tokens) for every model; longer levels (2k / 8k) are descriptive only. |
| R1-RPS-NORM (26 Oct) | RPS is normalised by **1/(K−1)** (spec §6.1). |
| R1-EDGES-10 (26 Oct) | **10 finite bin edges**: the cumulative head has 10 threshold sigmoids (plus the no-op Bernoulli) and the Jev rung asks **10 yes/no questions**; the spec's "11" is corrected. |
| R1-TIEBREAK (26 Oct) | **Exam rule step 4** (spec §5.7): a lexicographic tie-break on point estimates, applied only inside the tied set, in the order E2 probe skill, \|width ratio − 1\|, base over instruct, cost. |
| R1-HEADS-LN (26 Oct) | A **LayerNorm before every new head** (action, cumulative, linear belief): accepted. |
| R1-LAYA-POOL (26 Oct) | **Laya's new heads read the mean-pooled encoder output** (over valid tokens): accepted. |
| R1-TEMPERATURE (26 Oct) | **Kev's built-in pointer temperature is fixed at 1 during training**; **post-hoc temperature scaling on dev is applied uniformly to all models**. |
| R1-TOKEN-INIT (26 Oct) | The bin tokens `<b0>…<b11>` and `<exec>`/`<skip>` are **initialised from the mean of the existing token embeddings**; those rows train **in fp32 at a lower lr** (lower than what is not stated; the Track P agent reads it as lower than the new heads' 1e-3 and uses 1e-4 — author to confirm). |
| R1-LR-GRID (26 Oct) | **One learning-rate grid {1e-5, 3e-5, 1e-4} for every family, chosen by val RPS** (replaces the per-family lr of spec §4; new heads stay at 1e-3). |
| R1-ENV-PIN (26 Oct) | Keep **torch 2.6.0+cu124 on driver 535** and pin it. **Kev's code is pinned at the exact commit used in P.0** (`2074cc4`), with its diff to the release tag `kev-1.0` recorded. Jev model **`jev-1.14.0`**; verify with the key that the name exists before Phase 7. |
| R1-TRACKX-MARKER (26 Oct) | **Track X evidence marker:** `~/r1_locks/trackx_evidence.active` exists while B1 or B2 runs. Track P reads it before every GPU job and does not start while it exists. The author tells the Track X agent. |
| R1-TRACKP-MERGE (26 Oct) | Harness `r1` with `6afdb0e` is pushed by the author; Track P re-runs the four Track H test modules once it is on GitHub. **Track P does not merge to `main`**: the coordinating session reviews `trackp-20261026` and merges it; Track P continues on its branch. |

*Implementation choices by the Track P agent under these rows (not decided by the author; listed for confirmation, `docs/r1/reports/TRACKP_E0V2_DRYRUN_20261026.md`):* (1) token rows at lr 1e-4 — 10× below the new heads, but not below the top of the adapter grid; (2) the lr grid also applies to released heads (Kev's pointer head, Laya's decision head), which train at the adapter lr; (3) E0 v2: validation cells (1,3), (3,2), (5,4), (8,2), (0,3), (9,3); evaluation every 100 steps, patience 5 evaluations, the starting model counted as a candidate; the 2,000-step cap applies to each stage (head fit and LoRA, so ≤ 4,000 steps in all); the lr is chosen on the fresh-head soft run and reused for the hard-label contrast and the native-readout run; the Qwen control's new token rows stay frozen in the fresh-head run; (4) A4 v2 criterion form: predicted std non-decreasing wherever the label's std increases (plus the median per-prompt slope on the label std); (5) A3 budget = 1,024 − the longest rendering of the prompt over the pool families, levels filled to the word.

**Decided 26 Oct 2026 (evening) by the author (Track P, after the E0 v2 DRYRUN).** Fixed, not proposals. Recorded by an AI agent (Claude, Track P agent on zhixu portal) on branch `trackp-20261026` from the author's decisions in chat, answering `docs/r1/reports/TRACKP_E0V2_DRYRUN_20261026.md`.

| ID | Decision (decided 26 Oct 2026, evening, by the author) |
|---|---|
| R1-E0-THRESHOLDS (26 Oct) | **E0 pass (a floor, not a ranking):** width slope vs the label's own std **≥ 0.6, with its bootstrap 95 % lower bound > 0**; mean slope **≥ 0.8**. **A4:** predicted std monotone vs the label's std on **≥ 95 % of prompts**. |
| R1-E0-BUDGET (26 Oct) | **Two stages, the same for every model:** (1) **lr screen** on the grid, ≤ 2,000 steps, the lr chosen by val RPS; (2) **one run at the selected lr**: cap **6,000 steps, evaluation every 100, patience 10**. The E0 metrics come from that run. |
| R1-E0-HEADFIT (26 Oct) | The frozen-backbone head fit is **descriptive only**: cached frozen features, **full-batch L-BFGS to convergence on CPU**. |
| R1-CONTROL-READOUT (26 Oct; amends R1-C3-CONTROL) | **Qwen control: primary readout = a fresh LayerNorm + linear head**; the bin-token readout is reported as a secondary row. **A5 is read on the readout used for selection, descriptive only.** The bin list stays in the prompt in canonical order. |
| R1-TRACKP-CHOICES (26 Oct) | The Track P agent's implementation choices are **confirmed**: token-row lr 1e-4; the E0 validation cells (disjoint from the held-out test cells, stated in the report); evaluation every 100 steps; the selected lr reused for the hard-label and native runs; the Qwen token rows frozen in the fresh-head run. |
| R1-EXAM-RULE-V2 (26 Oct) | **Exam rule v2:** finalist 1 = the **E3 point-estimate top**; the tie-break order (E2 skill, \|width ratio − 1\|, base over instruct, cost) **only picks the optional second finalist**, among tied models of a different class; "tied" on E2 = an RPS-skill difference ≤ 0.01; the rule includes the E0 v2 thresholds. Committed with its sha256; `exam_analyze` accepts v2 only. Supersedes R1-TIEBREAK where they differ. |
| R1-P3A-READY (26 Oct) | Validate the two-stage driver with a short DRYRUN on kev-0.8b, then **STOP** with rule v2 committed and the branch pushed; the author then writes `trackp_p3a_<date>.md`. **zhixu experiment is not used by Track P until a PLAN row allows it.** |

| ID | Topic | Recommended default | Needed before |
|---|---|---|---|
| D1 | Budget unit | Compute (worker runs or seconds) + LLM-call cap | 0.3 hooks |
| D2 | Terminal outcome | Fresh-seed audit, + test where available | Phase 1 |
| D3 | Core actions | continue, skip, revise, verify(+demote); stop if D1 = compute | 0.3 hooks |
| D4 | Keep-rule override | Only through verify's frozen response | 0.3 hooks |
| D5 | Seed noise vs discrepancy | Kernel noise | Phase 1 |
| D6 | Manager backend for branching | Pinned local model | Phase 1 |
| D7 | Label horizon | Truncated h, declared as Q^ρ_h | Phase 1 |
| D8 | Learning route | Staged supervised → RL per the ladder | Phase 2 |
| D9 | Remaining budget in configurator Z | Yes (Paper A's decision untouched) | Phase 2 |
| D10 | Instance pool | Superseded by R1-BENCH / D20 | — |
| D11 | Primary estimand | V^π at matched compute | Phase 3 declaration |
| D12 | Existing 1,355 trials | **Closed 9 Oct:** ledgers lost; aggregate tables are context only | — |
| D13 | Old B path | **Closed by R1-ROUTE / R1-ARCHIVE** | — |
| D14 | Code location | Default set 9 Oct: harness changes on branch `r1` of the clone `~/Documents/autoresearch_harness`, pinned by commit from this repo; analysis, plan and manuscript in this repo. Confirm. | 0.1 |
| D15 | Manager model for experiments | Pinned local open-weight model (Ollama digest); one API model as a deployment check | 0.4 |
| D16 | Configurator architecture | §7 discussion; **deferred until the headroom gate passes** (R1-GATE-FIRST) | Phase 2, only if the gate passes |
| D17 | Primary venue | **Closed 9 Oct:** TMLR, ICML-standard quality bar (§9) | — |
| D18 | Practical target and headroom threshold | Set from Phase 0 noise floors | 0.4b pilot pre-check |
| D20 | Benchmark set and scope | §6 proposal: ML-research agent benchmarks (MLGym, MLAgentBench, MLE-bench Lite) plus an OpenML pool; general agent benchmarks excluded unless the author wants them | 0.4 |
| D19 | Worker backend | `LocalWorker` (structured edits, no `claw-code` submodule) for CPU nodes; `ClawWorker` only if an arm needs free-form code edits | 0.3 |
| D21 | Noise nodes | Keep only nodes where the measured training-seed or split-seed noise makes the default rule err at a non-trivial rate. Add SGD-trained CPU nodes if too few qualify. Choose the `fixed` or `vary` split policy per node from E1. | E2 STOP |
| D22 | Stronger manager for the self-control arm | One API model, or a larger open model on Ada (one card); at least as a deployment check | Phase 3 declaration |
| D23 | Index policy used as the primary comparator | KG-style (Bayesian; uses σ_n and ϱ) vs PACE-style (anytime-valid e-process); possibly both | After the T2 draft, before 0.4b |

## 11. Relation to Paper A

- Paper A stays an independent measurement paper.
- R1 cites A for replay identification (anonymously while both are under review) and uses it for branch labels and restore audits.
- R1 does not depend on A's live replay panel.
- Paper A's clean-vs-clean nondeterminism floor is related evidence. R1 measures its own noise floors per node.
