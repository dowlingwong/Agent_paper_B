# Paper B (route R1) — canonical plan

**Status:** canonical from 9 October 2026. This is the only plan for Paper B. Every plan, runbook, decision sheet, prompt pack and review written for the earlier Paper B route is archived under `archive/old_b_2026-10-09/` and has no authority.

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

Superseded by this plan:
- the two-checkpoint verification-timing study (N2) and its N1 replay tax;
- the candidate-consistency task (attempts 1 and 2) and P-B1;
- RUNBOOK §16–§20 decisions (D-AGENCY, D-COMPLY, D-TESTPOOL, D-HEADROOM, R-1, R-4 as written);
- the ICML 2027 route and the 15 / 30 November cutoffs;
- the Devstral / Ada binding plan;
- the 9 October prompt pack.

## 2. The question

In a governed autoresearch campaign, an LLM manager proposes bounded edits to a training script and a worker trains. A control plane keeps an edit only when the parsed metric strictly beats the incumbent. This default rule makes measurable errors:

1. **Wasted runs.** Invalid trials consume budget. Healthy autoresearch seeds showed invalid rates of 0.10–0.30.
2. **Noise-driven keeps and discards.** As an illustration only, from the old ResNet-trigger node (removed from R1): the measured seed s.d. is about 0.0138 AUC. Assuming a cross-config correlation of 0.5, a true ±0.005 change is decided wrongly about 36 % of the time. Verifying with 1 or 3 extra seeds lowers this only to about 30 % or 23 %.

The correlation is assumed; Phase 0 measures it (inputs §4.4).

**Question.** Who should decide *when and how* to intervene in this loop at matched compute: the LLM itself, a small trained configurator, or a hybrid? And does the problem need RL at all, or is full-information supervised learning on counterfactual labels enough?

## 3. Planned contributions (claims are falsifiable; none is established)

| ID | Contribution | Kind | Evidence that would establish it |
|---|---|---|---|
| C1 | **Measured control errors in governed autoresearch:** false keep, false discard and wasted-run rates per node, from noise-floor measurements and fresh-seed audits of ledgered candidates. | Phenomenon | Phase 0–1 audits on ≥ 10 nodes |
| C2 | **Loop-level control formulation** with "how to intervene" actions (skip, revise, verify with frozen response, and possibly stop). Includes an identification ladder Q^ρ → V^L0 → V^π linking branch labels to Paper A's replay identification, and a rule for when RL is needed. | Formulation and theory | Proofs or derivations, checked on branch data |
| C3 | **Matched-compute comparison** on held-out instances: LLM self-control vs trained configurator vs two hybrids, against statistical gates, harness heuristics, an offline-RL controller and HPO-style schedulers. Includes an action ablation showing where the value comes from. | Main empirical result | Phase 3 deployment |
| C4 | **Configurator training recipe.** Full-information supervised learning on branch labels, then RL only if the ladder shows it is needed. Reports which rung the problem requires. | Method, secondary | Phase 2–3 |

**Fallback if the headroom gate fails (RUNBOOK Phase 1).** If no learned controller can beat the best simple baseline, the paper becomes C1 + C2 plus a negative C3. That is still a complete journal paper.

**Novelty position** (inputs/NOVELTY_SWEEP): no prior work trains a policy for when and how to intervene in an autoresearch keep/discard loop. Each piece, however, has close neighbours:
- Harness-MDP (2607.05458): small offline-RL controller over a frozen LLM;
- Centaur (2603.24647): LLM plus CMA-ES on autoresearch, untrained;
- PACE (2606.08106): statistical commit gate;
- COTA (2608.21027): tiny advisor trained on counterfactual branches;
- PrimeScientist (2609.17846): budgeted allocation over autoresearch;
- Rehearse (2607.27687): the LLM judge degrades late in a campaign.

The paper must win on the **combination** and on three differentiators:
1. a measured, unplanted noise mechanism;
2. an explicit LLM self-control arm at matched compute;
3. same-state counterfactual labels with stated identification conditions.

Three risks have to be neutralised in the experiments themselves:
- "it is just HPO scheduling": HPO baselines plus an action ablation;
- "a small controller over an LLM is known": a self-control failure, a hybrid result, and transfer;
- "branch labels are standard": measured p, plus a case where p-aware labels change a decision.

The sweep is rerun before submission.

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

**Arms**
1. **LLM self-control.** A side query on a forked context returns an action and per-action scores. It never enters the manager context, and its tokens are charged to the arm.
2. **Trained configurator.** Architecture is open; see §7.
3. **Hybrid H1.** The configurator decides *whether/when*; the LLM decides *how*.
4. **Hybrid H2.** The LLM's scores and rationale are inputs to the configurator.

**Baselines**
- ρ, the default rule;
- fixed schedules;
- random at matched realised budget;
- harness heuristics: repeated-bad and doom-loop skip;
- a noise-aware keep threshold;
- a PACE-style anytime-valid commit gate;
- an offline-RL (AWR) MLP controller in the style of Harness-MDP;
- a risk-ranked vs advantage-ranked comparator on Z (answers the earlier critique's ranking question at no extra cost);
- the two-step continuation-value rule (Longstaff–Schwartz / FQE) for budgeted verify;
- successive halving / ASHA for the fidelity extension only;
- a hindsight oracle on the branch table, used for headroom only.

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

**Legacy code and manuscript (left in place for now)**
- `experiments/paper_b/task_cc*`, the Pi path in `control/executor.py`, `control/world.py`, `control/tree.py`;
- `protocols/paper_b/` (contracts v1–v3, launch validator);
- `papers/paper_b/` (the old manuscript);
- release scripts.

They stay where they are only because tests and release tooling import them. RUNBOOK task 0.1 decides whether to move them into the archive once R1's reuse is settled. Treat them as read-only history.

## 9. Venue, quality bar and timeline

**Venue (decided 9 Oct): TMLR.**
- TMLR accepts when claims are supported and of interest to part of its audience. There is no novelty-magnitude bar, and there is no deadline pressure.
- Paper A also targets TMLR. Cite it anonymously as a companion.
- TMLR pauses over the holidays; check the dates before planning a submission around them.
- A conference version stays possible if the results are ready before a suitable deadline. Decide at the end of Phase 3; nothing is planned around one.

**Quality bar: ICML main-track standard (decided 9 Oct).** Concretely, the paper must meet all of the following before submission.

1. **Clarity and length.** The core argument is concise, and the rest goes to the appendix. No template or page count is fixed yet (R1-FORMAT). TMLR's own regular/long-submission threshold is checked when the format is chosen.
2. **Baselines.**
   - The strongest relevant baselines, re-implemented and tuned with the same budget as our arms.
   - At least: a PACE-style gate, an AWR-MLP controller in the style of Harness-MDP, a noise-aware threshold, harness heuristics, and HPO-style schedulers where the action is HPO-like.
   - No strawmen. The tuning protocol is identical for every arm, and `matching_report` checks it.
3. **Statistics.**
   - Primary contrasts, sample sizes and analysis are pre-declared.
   - Cluster-bootstrap intervals by instance, with multiplicity stated.
   - Held-out instances and a held-out node.
   - Effect sizes stated in practical units.
4. **Ablations and mechanism.**
   - An action ablation.
   - Information ablations (with and without LLM text, with and without remaining budget).
   - A model-size ablation for family (b).
   - The ladder V^ρ ≤ V^L0 ≤ V^greedy ≤ V^RL.
5. **Generalisation.** Transfer to a held-out benchmark (leave-one-benchmark-out) and a second manager model, both reported.
6. **Theory.**
   - C2's statements carry full proofs, an AI-assisted audit and the author's own check.
   - Assumptions are stated where they are used.
7. **Reproducibility.**
   - Code, configs, seeds and compute reported per arm.
   - An anonymised artifact.
   - Every number regenerated by a script from committed data.
8. **Positioning.**
   - The novelty sweep is rerun within 4 weeks of submission.
   - An explicit differentiator against each of the closest works (§3).
9. **Honesty.**
   - Negative and null results reported.
   - AI assistance disclosed.
   - Workshop-paper overlap disclosed.

**Internal milestones** (planning targets, not promises):

| Milestone | Target |
|---|---|
| Phase 0 complete; open decisions taken | ~31 Oct 2026 |
| Phase 1 headroom gate | ~15 Dec 2026 |
| Phase 2 configurator selected | ~31 Jan 2027 |
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
| D16 | Configurator architecture | §7 discussion | Phase 2 |
| D17 | Primary venue | **Closed 9 Oct:** TMLR, ICML-standard quality bar (§9) | — |
| D18 | Practical target and headroom threshold | Set from Phase 0 noise floors | Phase 1 gate |
| D20 | Benchmark set and scope | §6 proposal: ML-research agent benchmarks (MLGym, MLAgentBench, MLE-bench Lite) plus an OpenML pool; general agent benchmarks excluded unless the author wants them | 0.4 |
| D19 | Worker backend | `LocalWorker` (structured edits, no `claw-code` submodule) for CPU nodes; `ClawWorker` only if an arm needs free-form code edits | 0.3 |

## 11. Relation to Paper A

- Paper A stays an independent measurement paper.
- R1 cites A for replay identification (anonymously while both are under review) and uses it for branch labels and restore audits.
- R1 does not depend on A's live replay panel.
- Paper A's clean-vs-clean nondeterminism floor is related evidence. R1 measures its own noise floors per node.
