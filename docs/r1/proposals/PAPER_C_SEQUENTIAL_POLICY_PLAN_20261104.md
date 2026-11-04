# Paper C (working name) — sequential policies for governed autoresearch loops: multi-step transitions, the Sequential Policy Track, and multi-step RL (research plan draft, 4 Nov 2026)

**Status.** AI-assisted research-plan draft (Claude, chat session), written at the author's request on 4 Nov 2026. **Not adopted, authorizes nothing, allocates no resources, not evidence.** No Paper C run starts before Paper B's submission (10 Jan 2027) except the logging that Paper B itself adopts (Paper B revision proposal, W1/W2). "Paper C" is a working name (open item O7 of the revision proposal).

**Sources.** The sequential-policy comment (`docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md`, on `docs/runbooks-04nov`; "the comment" below, with its section numbers), `SEQUENTIAL_POLICY_REVISION_20261104.md` (the Paper B revision; "the revision"), Track S design rev 7.4 and its code on `trackS-ops-20261030`, the T4 Proposition 10 revision draft (`T4_PROP10_REVISION_20261028.md`), Track P, C3_DESIGN and the 4 Nov benchmark review.

---

## 0. Summary

Paper B asks whether a learned **single-step** belief improves noisy acceptance, proves when the loop **reduces** to independent one-step decisions (no feedback (NF), no information (NI), fixed price), and screens on whole campaigns whether a tuned state-dependent threshold beats a tuned static one (Track S, one-way). Paper C takes up what Paper B deliberately does not claim:

1. **L1, at strength.** Where in real loops is sequential control worth anything, and through which channel: budget, information, incumbent interaction or proposer feedback?
2. **L2.** With the same immediate information, does accounting for the future help, and does a model-based or supervised multi-step method already capture it?
3. **L3.** Does multi-step RL add anything **beyond** strong non-RL sequential methods (tuned dynamic thresholds, budget DP, model-based rollout, multi-step supervised regression, behaviour cloning, DAgger) at matched information, data, interaction and tuning budget?
4. **L4, multi-step.** Does a language decision model that reads the proposal add value **in the multi-step policy**, beyond structured state encoders, and can it be trained multi-step at an affordable cost?

The experimental core is the **Sequential Policy Track (SPT)**: a transition dataset collected under a logged behaviour mixture plus repeated fork trees, a fixed method ladder trained and selected on development instances, and frozen evaluation on fresh campaigns with fresh-seed audits. Real closed-loop online RL and multi-step RL of the LLM decision model are the last two stages, entered only through declared gates. Every outcome of the four questions is reportable: the levels can hold or fail independently (comment §1).

---

## 1. What Paper C inherits from Paper B

| Inherited | From | Use in Paper C |
|---|---|---|
| One-step index theorem, reduction theorem, Props 10(b)/(c), the hard-budget scope note | C2 (after the author's proof check) | Where non-myopic gain can exist; design of the synthetic worlds; the information principle |
| Transition-logging contract and sidecars | Revision W1/W2 | Every Paper B campaign (sweep 2 T0/T1, Track S, D.3) becomes data |
| Track S code: arm-override hook, ghost and controller-only arms, forced E2 keep/discard, instance-level seed keys, fork collector, A2-U, static/dynamic families, π′, synthetic nodes | Track S S0.3 (pin `d10b05b7`, harness `a3fedbb`) | SPT's fork trees and mechanism arms, without new harness surgery |
| Track S outcomes: binding shares, σ_D, flip rates, fork channel contrasts Δ_B, Δ_I, Δ_F, S1.1 interaction, S0.6/W4 sensitivity | Track S, revision W4 | Pilot variances, power planning, choice of nodes and channels |
| Budget-DP baseline | Revision W3 | Rung of the non-RL ladder |
| C3 belief models (A3, TabPFN, Kev-0.8B/4B, Qwen controls) and labels | Paper B C3, Track P | The immediate-value component of every multi-step method; the L4 comparison |
| (NI) masking test, (NF-c) count, the DI diagnostic | Revision W5, C4 | Which channels to expect on which nodes |
| Node census with per-node noise and edit–edit interaction strength | Track G (G.1b, S1.1 on T1) | Choice of interaction-rich nodes |
| Main proposer (Track X pick, thinking off) and runner-up | X.7, R1-BX-D6-EXAM-RUNNER-UP | Proposer of record; generalisation check |

---

## 2. Research questions, hypotheses and outcomes

| ID | Question | Primary comparison (fixed before the test) | Hypothesis | What a negative means |
|---|---|---|---|---|
| **Q1** (L1) | Does state-dependent control beat the tuned static rule? | strongest pre-specified **non-RL** dynamic policy vs tuned static, on fresh campaigns | Positive on budget-binding and interaction-rich nodes; null on T0 single-parameter nodes | Sequential value below the stated sensitivity on these nodes; never "the loop is one-step" |
| **Q2** (L2) | With the same immediate estimate, does a continuation term help? | continuation-aware vs myopic, **same** belief model, only Ĉ_future toggled (comment §4.3) | Helps exactly where the fork contrasts show non-zero continuation differences | Future-value effects are too small to exploit with this information |
| **Q3** (L3) | Does multi-step RL beat the strongest non-RL multi-step method? | best RL policy vs strongest pre-specified non-RL multi-step policy (selected on dev by a fixed rule), matched information, data and tuning budget | Small or no gain offline; any gain more likely with online interaction, which is then tested against equal-interaction DAgger/planning | RL adds nothing beyond planning/supervision here — a clean result |
| **Q4** (L4) | Does a decision model that reads the proposal add value in the multi-step policy? | the same multi-step method with an LM state encoder vs a structured-feature encoder (MLP/LightGBM), equal data | Gains, if any, on transfer to held-out suites, not in-distribution | Structured state suffices for sequential control |
| **Q5** | Which channel produces the gain? | factorial and intervention designs of §10 | Budget first; information on high-noise nodes; feedback with memory on | Gains are not attributable; reported as such |

The two **confirmatory** comparisons are Q1 and Q3 (comment §9.3). Q2, Q4 and Q5 are pre-declared secondaries with their own multiplicity control.

---

## 3. Problem formulation

### 3.1 Episode, outcome and constraints

- **Episode** = one campaign: from the deployed start configuration until the worker-run budget W or the LLM-call cap N is exhausted, or the protocol stops it.
- **Outcome** Y = the final incumbent's metric, averaged over K fresh audit seeds from a reserved audit block. Per node, comparisons use paired raw-unit differences; cross-node summaries use Y/σ_node with σ_node declared in advance; raw units are never averaged across nodes (comment §3.1).
- **Matched resources** for every compared policy on an instance: the same instance seed key, start configuration, W, N, proposer, manager repetition and audit seeds.

### 3.2 State and information principle

The decision state s_t contains (comment §3.2):
- the proposal (diff or structured edit) and its duplicate/no-op flags;
- the incumbent configuration and its observation history;
- worker runs used/left, LLM calls used/left, proposal slots left — **from the budget ledger, never the trial index**;
- recent accept/reject history, previously executed configurations, repeat flags;
- the noise estimate and its source;
- a fixed-length history summary for learned encoders.

**Information principle.** At a decision point every compared policy receives the same legal information. A gain of a method with a richer view (for example full history for the RL policy, current proposal only for a baseline) is not attributed to the method. Ablations that deliberately change information are labelled as information ablations.

**Partial observability.** The proposer is an LLM whose internal state is hidden and whose memory display depends on past decisions; the problem is a POMDP in general. Policies act on the logged observation s_t; history summaries are the declared approximation.

### 3.3 Action space, staged (comment §3.3)

| Round | Actions controlled by the policy | Frozen | Why this order |
|---|---|---|---|
| **A** | E1 execute / skip | E2 acceptance = a shared frozen rule (the A2-U Bayes margin) | Isolates the budget and screening question |
| **B** | + E2 keep / discard (forced, via the Track S hook) | — | keep/discard changes the incumbent and the proposer's context (feedback channel) |
| **C** (optional) | + verify (2r runs, racing-style), stop campaign early | — | verify costs more than one run; stop changes the horizon |
| not planned | revise, memory switch, display changes as actions | — | action attribution and coverage explode (comment §3.3) |

A round starts only after the previous round's final test is complete.

### 3.4 Reward

- **Primary:** r_t = 0 for t < T, r_T = Y_final − Y_start (a per-instance shift of Y).
- **Shaping** is allowed as a training device only, declared in advance; final evaluation uses the unmodified audited terminal Y. Intermediate rewards never use audit values that are not visible at deployment unless they are explicitly a training target. Potential-based shaping is checked for termination, discounting and implementation conditions before any invariance is claimed (comment §3.4).
- **Costs** (executions, wall time, LLM calls) are reported separately and are not mixed into the objective while W is fixed.

### 3.5 Relation to DAC and to Paper B's theory

- DAC view (Biedenkapp et al. 2020; Adriaensen et al. 2022): the target algorithm is the governed loop, instances are (node, seed), the policy sets per-step thresholds; contextual DAC benchmarks (Eimer et al. 2021) motivate the instance split.
- Paper B's reduction theorem says a policy can beat the Bayes one-step rule only where (NF) or (NI) fails or the budget is hard. Paper C's environments are chosen so that each channel can be on or off (§5), and its analysis reports gains per channel.
- **Theory work items for Paper C** (proposals, to be proved or dropped):
  - T-C1: a bound on the gain of the optimal budget policy over the best static price under a hard budget with i.i.d. one-step values (stochastic knapsack; cite and verify Arlotto & Gurvich 2019 and the dynamic-knapsack literature before relying on them);
  - T-C2: a value-of-information bound for the NI channel in the Gaussian latent-sensitivity model of Prop 10(c), linked to the knowledge gradient;
  - T-C3: conditions under which multi-step supervised regression on fork outcomes (one policy-improvement step) is already within a stated gap of the optimum, to frame Q3's null.

---

## 4. The multi-step transition dataset

### 4.1 Record schema (one row per decision point)

| Group | Field | Notes |
|---|---|---|
| Identity | node, suite, tier, instance_id, campaign_id, root_id, fork_id, branch path, step_index, epoch (E1/E2/verify) | campaign_id is the clustering unit |
| Policy | policy string, policy version/sha, behaviour-mixture component, **action probability** under the behaviour policy, ε-randomisation flag | deterministic policies log 1.0 and the deterministic rule |
| Seeds | instance seed key, manager repetition, worker seed, audit seed block | instance-level keys as in Track S |
| State | proposal hash + diff/edit text pointer, incumbent config hash, duplicate/no-op flags, forecast tuple (π, μ, τ, σ, V̂\*, m̂) from each declared belief model, runs used/left, LLM calls used/left, slots left, keeps/skips so far, history-summary pointer | state is stored as values plus pointers to the ledger and prompt files |
| Action | action, forced or chosen, rule that produced it | forced actions only in forks or interventions |
| Outcome | observed Δ̂ (if executed), keep decision, next incumbent hash, runs and calls consumed, wall time | |
| Episode end | `terminated` (W or N exhausted, or a declared stop) vs `truncated` (crash, timeout, pre-emption, parse failure beyond retry, host loss) with reason | truncated episodes never enter return targets as if complete (comment §5.1) |
| Terminal | Y_terminal, per-seed audited values, audit seeds | on the last record of the campaign |
| Provenance | host, GPU, harness and paper commits, GGUF sha, llama.cpp build, `cache_prompt`, label (PILOT/EVIDENCE) | as Track S `Provenance` |

### 4.2 Mechanical checks (run on every batch)

- budget conservation: Σ runs consumed = W − runs left at every step; calls likewise;
- contiguous step indices and exactly one terminal record per complete campaign;
- next-state consistency: s_{t+1}'s incumbent hash equals the keep outcome at t;
- A/A replay: a fork that takes the root's action reproduces the root's ledger (Track S arm-invariance test 4);
- no field of a future step or an audit value appears in a state;
- seed blocks disjoint from every Paper B block (one seed registry file).

### 4.3 Sources of transitions

| Source | Behaviour policy | Coverage it adds | Status |
|---|---|---|---|
| Paper B sweep 2 T0/T1 | execute-all | executed transitions only, many nodes | logged under W2 |
| Paper B Track S S0.4–S0.7, S3e | execute-all, A2-U at two prices, 15 static, 4 dynamic, π\*, m\*, matched static, secondaries | threshold diversity; binding budgets | logged under W2 / derived |
| Paper B Track S S3a | forks with skip/execute/ghost/ctrl-only, keep/discard | counterfactual action pairs at matched roots | logged; 150 forks per node |
| Paper B D.3 | the deployed arms | on-policy states of contextual controllers | logged under W2 |
| **SPT-2** (new) | behaviour mixture with logged randomisation | action support where Paper B's policies are deterministic | Paper C |
| **SPT-3** (new) | repeated fork trees | Q^{π_b} differences with replication | Paper C |
| **SPT-7** (new, optional) | the learner's own policy online | on-policy data under RL or DAgger | Paper C |

---

## 5. Environments

| Tier | Environment | Channels on | Role |
|---|---|---|---|
| **E-SYN** | synthetic worlds (revision W4): budget opportunity cost, information (Prop 10(c)), incumbent interaction, proposer feedback, strict null; exact DP optimum where the state space allows | one at a time, then pairs | implementation checks, false-positive rates, oracle gaps, method behaviour per channel; never evidence about the real loop |
| **E-T0** | Paper B's CPU nodes (`digits_mlp`, `tabular_mlp`, and the OpenML nodes as a low-interaction condition), single-parameter edits, binding W | budget; weak information; feedback with memory on | cheap real-loop tier for the full SPT |
| **E-INT** | interaction-rich real nodes: T1 tasks selected by measured edit–edit interaction (S1.1) and noise, short fixed-step budgets, code-level diffs; at least one high-noise RL-type task | all four channels plausible | the tier where L1–L3 can show headroom |
| **E-HELD** | one held-out suite or task family, never used for training or selection | — | transfer (Q4) |
| **E-SIM** (training aid) | a learned transition model fitted on SPT data (proposal-value model, keep model, budget dynamics, next-proposal category model) | as learned | MPC rollouts and model-based training only; its error is reported; no conclusion rests on it (comment §4.2 B2, §11) |

**Task selection rule.** E-INT nodes are chosen by declared criteria (interaction strength, noise, budget binding, run cost) from the census, before any SPT outcome, with the screening funnel reported (as R1-BX-D12). Easy and hard nodes are reported separately, never averaged into one score (comment §7.4).

---

## 6. The Sequential Policy Track (SPT)

| Phase | What | Where | Done when |
|---|---|---|---|
| **SPT-0** Contract and infrastructure | Freeze §3–§4; port the Track S hooks into the SPT runner; implement the multi-step offline environment over logged transitions (the deferred H.8 execute/skip amendment, generalised to episodes); seed registry; analysis code; synthetic-world suite with DP oracles | desktop + review | tests pass; independent review accepted; author row |
| **SPT-1** Pilot (not used for testing) | per node: variance of campaign Y between policies and repetitions; fork repeat variance vs between-fork variance; proposer-seed vs worker-seed share; A/A identity; cost per campaign; binding shares; first estimate of the **advantage signal-to-noise** at forks | E-T0, 1–2 E-INT nodes | numbers in the pre-declaration; a go/no-go for RL (below) |
| **SPT-2** Behaviour-mixture collection | training instances only; mixture of execute-all, tuned static (grid), Track S dynamic members, budget DP, the deployed contextual C3 policy, and ε-randomised versions of each (ε ∈ {0.1, 0.25} at E1, and at E2 in round B), probabilities logged | E-T0, E-INT | coverage targets of SPT-4 met or a declared shortfall |
| **SPT-3** Fork trees | roots under the mixture; fork points sampled uniformly plus near-threshold oversample (IPW weights); arms skip/execute (+ ghost/ctrl-only on a third), keep/discard in round B; **r ≥ 2 continuations per arm** under ≥ 2 declared continuation policies; depth-2 forks on a subset | E-T0, E-INT | Q^{π_b}(s, a) − Q^{π_b}(s, a′) estimates with intervals; channel contrasts |
| **SPT-4** Coverage and support diagnostics | action support per state cluster; propensity overlap; effective sample size; fitted-Q evaluation and doubly robust off-policy estimates of each candidate on dev | desktop | candidates with unsupported actions flagged or constrained |
| **SPT-5** Training and selection | the method ladder (§7) on training data; hyperparameters, checkpoints and "strongest non-RL" chosen on dev campaigns by a fixed rule; multiple training seeds | GPU/CPU (small models) | frozen policies + hashes; pre-declaration of SPT-6 |
| **SPT-6** Final test | frozen policies on fresh test instances, paired; fresh audit seeds; placebos (exact A/A, repetition) | E-T0, E-INT, E-HELD | report; confirmatory Q1/Q3 |
| **SPT-7** Online fine-tuning (optional; §8) | bounded online interaction on training instances, matched for all arms | E-T0 first | separate pre-declaration and authorization |
| **SPT-8** LLM decision model, multi-step (optional; §9) | after the gates of §9.1 | E-T0, then E-INT | separate pre-declaration and authorization |

**Go/no-go for RL after SPT-1.** If the estimated fork-level advantage signal-to-noise (|mean Q difference| / its per-fork s.e. at the planned replication) is below a declared floor on every node, multi-step RL is not trained; Q3 is reported as "not testable at this budget", and the paper rests on Q1, Q2 and Q5. This is the lesson of E1b in Paper B, where campaign-final rewards made continue-vs-verify group advantages ≈ 0.

---

## 7. Methods ladder

All methods use the same state view (§3.2), the same training instances and transitions, and a declared, equal tuning budget (number of configurations × dev campaigns). Small, transparent models come first (comment §5.4).

### 7.1 Non-RL

| ID | Method | Learns from | Notes |
|---|---|---|---|
| N0 | default rule / execute-all | — | practitioner floor |
| N1 | tuned static thresholds (g, h) | dev campaigns | Track S `static` |
| N2 | contextual one-step rule with the learned belief (Paper B C3 / R-A0) | per-proposal labels | the myopic reference for Q2 |
| N3 | Track S dynamic members, tuned | dev campaigns | single-channel state dependence |
| N4 | budget DP (stochastic knapsack) | V̂\* distribution on training data | revision W3 |
| N5 | MPC / finite-horizon rollout on E-SIM, completed by a frozen base policy | transitions | model error reported |
| N6 | multi-step supervised regression on fork Q differences (π′ generalised; one approximate policy-improvement step) | SPT-3 forks | the key strong baseline for Q3 (comment §6.2.3) |
| N7 | behaviour cloning of the strongest of N3–N6 | its rollouts | does RL exceed copying a good policy? |
| N8 | DAgger / on-policy aggregation with the same new-interaction budget as RL | online labels on training instances | comparator for SPT-7 |

### 7.2 RL

| ID | Method | Target | Notes |
|---|---|---|---|
| R1 | IQL (expectile value, advantage-weighted policy extraction) — **primary** | multi-step return / bootstrap | chosen on dev; addresses distribution shift by in-sample learning (Kostrikov et al. 2021, arXiv:2110.06169) |
| R2 | CQL or a behaviour-regularised actor-critic / AWR — **alternative** | same | (Kumar et al. 2020, arXiv:2006.04779) |
| R3 | online fine-tuning of the selected offline policy (SPT-7) | on-policy returns | §8 |
| R4 | LLM decision-model variants | §9 | — |

**Rule.** A method counts as multi-step only if its training signal is a multi-step return or a bootstrapped multi-step target. Re-using the per-proposal immediate u under any RL algorithm is a single-step method (comment §5.4).

### 7.3 State encoders (Q4)

E-a structured features → MLP; E-b LightGBM / TabPFN on the same features (for value regression where applicable); E-c the same features + a PCA-reduced proposal-text embedding (the information-matched view of R1-BX-D13); E-d the LM decision model's hidden state (Kev / Qwen control). Q4 compares E-d with E-a/E-c **within one method** (N6 or R1), equal data.

---

## 8. Real closed-loop multi-step RL (online)

**Design** (comment §5.5):
- all online interaction on **training instances only**, under fixed caps on new worker runs, LLM calls and audits;
- three arms with the **same** number of new campaigns: (1) offline data only; (2) offline + new data for a supervised/planning learner (N6 or N8); (3) offline + new data for online RL (R3);
- frozen evaluation on fresh test instances; the difference (3) − (2) is the RL-specific effect, (2) − (1) the data effect.

**Mechanics.**
- Campaign workers run asynchronously; the policy is updated after each batch of B completed campaigns; the policy version is logged per decision.
- Exploration only through the logged ε-randomisation of §6 or the policy's own stochasticity, with probabilities logged.
- STOP on: return collapse on dev, budget-accounting mismatch, unsupported-action rate above a declared level, A/A failure, or the cap.

**Cost (rough; recompute from SPT-1).**
- E-T0: a campaign is ≤ 40 proposer calls (≈ 28 s at the measured ≈ 0.7 s per call on a 4090) plus ≈ 40 s of worker and audit CPU (Track S design §9). 2,000 online campaigns per node ≈ 80k calls ≈ 16 h on one server. Affordable.
- E-INT: at 2-minute fixed-step runs, W = 20 and K = 5 terminal audits, one campaign is ≈ 50 GPU-minutes (≈ 0.85 GPU-h) before proposer cost. 2,000 campaigns ≈ 1,700 GPU-h per node. **Not affordable**; online RL on E-INT is limited to a small fine-tuning budget (for example ≤ 200 campaigns) or dropped.

---

## 9. Multi-step RL of the LLM decision model

### 9.1 Entry gates (comment §12 step 6)

All must hold before any SPT-8 run:
1. SPT-6 shows sequential headroom on at least one tier (Q1 positive, or the oracle/fork gap above the declared margin);
2. the strongest non-RL multi-step baseline (N6) and a small-model RL policy (R1) exist with interpretable results;
3. SPT-4 transition data pass the coverage checks;
4. the proposal text is shown to matter for the multi-step value (E-c or E-d beats E-a in N6), otherwise a language model has nothing to add;
5. the cost projection below fits an authorized budget.

### 9.2 Model and interface

- Base: the Paper B finalists (Kev-0.8B/4B; Qwen3.5 base controls), LoRA as in Track P.
- Input: the history summary and budget fields first, the proposal last, immediately before the readout (R1-BX-REVISIONS / P13 ordering).
- **Belief/action decoupling is kept:** the belief head stays trained by a bounded proper score on per-proposal labels; a separate **value/advantage head** (or action head) carries the multi-step target. This preserves calibration and makes the single-step belief comparable with Paper B.

### 9.3 Three training routes, cheapest first

| Route | What | Data | Cost | Risk |
|---|---|---|---|---|
| **M1 distillation** | advantage-weighted SFT of the action head on N6/R1 advantages (or BC of the best small-model policy) | existing transitions | small (single forward passes) | inherits the small model's errors; tests Q4 cleanly |
| **M2 offline value learning with an LM encoder** | IQL (R1) with the decision model's hidden state as encoder; belief head frozen or co-trained with RPS | SPT-2/3 transitions | moderate (offline, GPU-hours) | over-fitting, distribution shift; monitored with SPT-4 diagnostics |
| **M3 on-policy, fork-grouped policy gradient** | GRPO/PPO-style updates where a **group** is the set of continuations from one root state (different first actions or seeds), reward = terminal audited Y (or a declared proxy), leave-one-out baseline, KL to the M1/M2 checkpoint | new online rollouts | large (below) | sparse, high-variance reward (E1b); sharpening; cost |

**M3 cost (rough).** One update batch of 16 root states × 8 continuations = 128 continuations. On E-T0 a continuation of ≈ 10 remaining decisions is ≈ 20 proposer calls + runs ≈ 30 s, so one batch ≈ 64 min on one server and 200 updates ≈ 210 server-hours (≈ 2–3 days on four servers). On E-INT one batch is ≈ 128 × 0.5 GPU-h ≈ 64 GPU-h, so 200 updates ≈ 13,000 GPU-h: **infeasible**. M3 is therefore planned on E-T0 only, with short horizons, and only if the SPT-1 advantage signal-to-noise passes. E-INT receives M1/M2 policies for evaluation.

### 9.4 Monitors and stop rules

As Track P §6.4 (ECE drift, width ratio, entropy collapse, KL) plus: share of zero-advantage groups, unsupported-action rate, return on dev campaigns. Roll back to the best checkpoint on any breach.

### 9.5 What a result would mean

- M1 ≈ M2 ≈ small-model R1 on E-T0 and E-INT: the LM adds nothing multi-step beyond its single-step belief — an L4 negative for sequential control.
- M1/M2 better on E-HELD only: the LM's value is transfer, not in-distribution control.
- M3 better than M2 at equal interaction: evidence for on-policy multi-step RL of an LM controller, conditional on the node tier.

---

## 10. Mechanism attribution (powered versions of Track S's diagnostics)

| Channel | Design | Prediction / reading |
|---|---|---|
| Budget | worker-run cap as a factor (loose vs binding), LLM cap fixed; report binding share, execute rate per step, runs left at the end | a gain only under binding caps that N4 recovers is a budget-allocation (DAC) gain, not an RL- or feedback-specific one; budget levels are fixed in advance, never chosen after results (comment §7.1) |
| Information | execute-with-result-visible vs ghost-like execution with the result hidden from the controller, at matched budget (Track S ghost/ctrl-only) | Δ_I > 0 where (NI) fails; the masking test predicts where |
| Proposer feedback | forced keep/discard at matched histories (powered DI test); memory none vs `append_only_summary`; prompt-display ablation; the **debiased-memory intervention** (Paper B C4 A/B, moved here) | changes in later proposal law and in audited increments over each branch's incumbent (R1-C4-ENDPOINT) |
| Incumbent interaction | 2 × 2 factorials of edit pairs (A alone, B alone, A + B, both orders) on E-INT nodes; per-node interaction strength as a covariate | headroom for sequential control rises with interaction strength |

Every intervention arm is verified to change only its intended channel (prompt bytes, novelty set, metric leakage, budget, incumbent restore, controller state, seed mapping; comment §7.3). Common random numbers after a fork are not assumed to pair later proposals; the pairing gain is measured.

---

## 11. Statistics

- **Unit:** the campaign instance i = (node, instance seed, start configuration); paired D_i = Y_i(π_a) − Y_i(π_b); training seeds, proposer repetitions and audit seeds are nested, never counted as independent campaigns (comment §9.1).
- **Splits:** training instances (collection, forks, training), development instances (tuning, checkpoint and method selection, the "strongest" rule), test instances (frozen policies only), audit seeds (never used in training or selection). Leakage checks beyond instance seeds: shared edit templates and start configurations across splits (comment §9.2).
- **Seed blocks:** new blocks for SPT instances, forks, workers, proposers and audits, disjoint from every Paper B block (5001–5006, 7001–7010, 8001–8010, 9001+, and Track S's five instance blocks and S3e audit block), recorded in one registry before SPT-1.
- **Confirmatory comparisons:** Q1 and Q3 only, one-sided, Holm across nodes within each, with declared practical thresholds. Q2, Q4, Q5 pre-declared secondaries with their own Holm family. Paper B's Track S false-positive budget is not reused.
- **Power:** from SPT-1 variances, by simulating the whole pipeline (training, tuning, selection, test) rather than a fixed-policy formula; winner's-curse from selection included. Track S's n = 300 is not copied (comment §9.4). An under-powered comparison is declared exploratory in advance.
- **Training randomness:** ≥ 3 independent training seeds per learned method at equal budget; the reported policy is fixed in advance (seed-averaged evaluation or dev-selected checkpoint), never the best seed (comment §9.5).

---

## 12. Cost model (rough; recompute after SPT-1)

**Formula** (comment §10): total = training trajectories + fork continuations + baseline tuning + test campaigns + independent audits (+ online interaction). Costs are logged as worker runs, proposer calls and tokens, audit runs, controller inference time, training GPU/CPU time, wall time, and API cost if any. Two comparisons are reported: at equal deployment budget, and including development cost (how many deployments repay it).

**Per E-T0 node** (≤ 40 calls per campaign, ≈ 0.7 s per call, one server; CPU worker time overlaps):

| Item | Campaigns / continuations | Proposer calls | Server-hours |
|---|---|---|---|
| SPT-1 pilot | ≈ 150 campaigns + 60 forks | ≈ 8k | ≈ 1.5 |
| SPT-2 mixture | 6 components × 100 instances = 600 | ≈ 24k | ≈ 5 |
| SPT-3 forks | 300 forks × 4 arms × 3 continuations × ≈ 20 calls | ≈ 72k | ≈ 14 |
| SPT-5 dev selection | ≈ 600 | ≈ 24k | ≈ 5 |
| SPT-6 test | 6 policies × 300 instances = 1,800 | ≈ 72k | ≈ 14 |
| **Total (without SPT-7/8)** | | **≈ 200k** | **≈ 40 (≈ 20 on two servers)** |

**Per E-INT node** (≈ 0.85 GPU-h per campaign at 2-minute runs, W = 20, K = 5):

| Version | What | GPU-h |
|---|---|---|
| minimal | pilot 40 campaigns; forks 100 × 2 arms × 2 continuations (about half a campaign each); test 4 policies × 100 instances | ≈ 34 + ≈ 200 (400 continuations at ≈ 0.5 GPU-h) + ≈ 340 ≈ **575** |
| full | as E-T0 | several thousand: not planned |

So the E-INT tier carries the **test** and a reduced fork set; training data come mainly from E-T0, E-SYN and E-SIM, plus Paper B's logged T1 campaigns. HoreKa or Ada allocations would have to be requested for Paper C specifically.

---

## 13. Other items moved from Paper B to Paper C

| Item | Paper B status | In Paper C |
|---|---|---|
| A7 online RL | removed by the revision (R1-SEQ-A7-MOVE) | §8 |
| C4 debiased-memory A/B | "appendix or later" → moved | §10 feedback row |
| H.8 execute/skip environment amendment | deferred (R1-H8-DEFERRED) | SPT-0 multi-step environment |
| E2 keep/discard and verify as controllable actions; racing / sequential verification baselines | Track S has forced keep/discard for forks only; verify off | §3.3 rounds B–C |
| Stop, revise, memory-switch actions | not planned | not planned (listed so they are not added silently) |
| Track S repeat with the final exam pick | decided after the Track S outcome (R1-TRACKS-PICK-REPEAT-DEFER) | proposer generalisation of Q1 |
| Track S on GPU nodes at full power | descriptive only in Paper B | E-INT test |
| Second proposer (exam runner-up) in sequential evaluation | closed-loop check only in Paper B (R1-BX-D6-EXAM-RUNNER-UP) | E-T0 proposer-generalisation fold |
| Model-based rollout / MPC (comment §4.2 B2) | not in Paper B | N5, E-SIM |
| R-B as a multi-step arm | single-step optional ablation in Paper B | M3 |
| LLM self-control as a **sequential** controller (the proposer shown budget and history decides execute/skip/stop) | A4 is single-step in Paper B | an extra arm in SPT-6, with its call cost counted |
| Development-cost amortisation reporting | not in Paper B | §12 |

---

## 14. Timeline (proposal; no date is committed)

| Window | Work |
|---|---|
| Nov 2026 – 10 Jan 2027 | **Inside Paper B only:** W1/W2 logging, Track S rev 8, W3/W4. No Paper C runs |
| mid-Jan – Feb 2027 | Author decisions; SPT-0 contract, seed registry, synthetic suite, multi-step environment, review; SPT-1 pilot on E-T0; theory items T-C1–T-C3 started |
| Mar 2027 | SPT-2/3 on E-T0 (≈ 1 server-day per node per phase); E-INT node choice from the census; SPT-4 diagnostics; go/no-go for RL |
| Apr 2027 | SPT-5 training and selection; SPT-6 test on E-T0; E-INT minimal test; M1/M2 if the gates of §9.1 pass |
| May 2027 | optional SPT-7 (E-T0) and M3 (E-T0); writing |
| Venue | to be decided by the author (e.g. NeurIPS 2027 if its deadline falls in May — verify — or TMLR / ICLR 2028). Only the minimal version (E-SYN, E-T0, E-INT test, N0–N8, R1, M1/M2) fits a May deadline |

---

## 15. Risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Too little action/state coverage | offline RL over-estimates unseen actions | logged ε-mixtures; SPT-4 support checks; behaviour-constrained methods; report "insufficient data" rather than hide it behind a more complex algorithm (comment §12 step 5) |
| Sparse, noisy terminal reward | zero-advantage groups, unstable RL | fork-level replication; near-threshold oversampling; SPT-1 go/no-go on advantage SNR |
| Proposer non-reproducibility | fork pairing fails | `cache_prompt: false`; exact A/A placebo; S0.1-style identity test per host |
| Fork restore inconsistency | invalid causal contrasts | Track S arm-invariance tests 1–5 on every runner change |
| Strong simple baselines explain all gains | no L3 effect | a clean, reportable result; N4/N6 are confirmatory comparators by design |
| Unequal tuning or interaction budgets | the most complex method wins by search | declared budgets per method; equal-interaction DAgger arm; costs reported |
| Simulator bias | gains on E-SIM that vanish on real loops | E-SIM only for training; conclusions only from SPT-6 |
| Environments chosen to favour RL | circular evidence | declared selection criteria before outcomes; easy and hard tiers reported separately; strict null in E-SYN |
| GPU cost | E-INT under-powered | minimal E-INT test only; training on E-T0/E-SYN; explicit exploratory labelling |
| Schedule against the PhD timeline | Paper C late | minimal version first; online RL and M3 optional |

---

## 16. What Paper B must leave in place for Paper C

1. The transition contract and sidecars (revision W1/W2), with byte-identical-ledger tests, on every campaign runner Paper B uses.
2. Track S's hooks and fork collector preserved at their pins; Track S raw roots, leaves and ledgers archived with sha256 (they are the first fork dataset).
3. The real budget fields in every record (revision §3.6).
4. The synthetic-world suite and budget-DP code (W3/W4) as reusable modules.
5. Sweep-2 and D.3 ledgers kept with their prompts and diffs (the history summaries are rebuilt from them).
6. No Paper B seed block re-used; the Paper B seed ranges listed for Paper C's registry.

## 17. Open decisions for the author

| # | Decision | Recommendation |
|---|---|---|
| P1 | Adopt this plan as the follow-up paper's scope (in principle) | yes, as a working plan; revisit after Paper B's submission |
| P2 | First action round only (execute/skip, frozen acceptance) for the first version | yes |
| P3 | E-INT nodes: how many and which suites | 2–3 nodes from the census by interaction strength; one high-noise RL-type task |
| P4 | Primary offline RL algorithm | IQL primary, CQL/AWR alternative, chosen on dev |
| P5 | Whether online RL (SPT-7) and LLM M3 are in the first submission | optional; decided after SPT-1's go/no-go |
| P6 | Compute requests (HoreKa/Ada) for E-INT | prepare after SPT-1 with measured costs |
| P7 | Venue and target date | the author's choice after Paper B |
