# Paper C (working name) — sequential policies for governed autoresearch loops: multi-step transitions, the Sequential Policy Track, and multi-step RL (research plan draft, revision 2, 5 Nov 2026)

**Status.** AI-assisted research-plan draft (Claude, chat session), written at the author's request on 4 Nov 2026 and revised on 5 Nov 2026. **Not adopted, authorizes nothing, allocates no resources, not evidence.** No Paper C run starts before Paper B's submission (10 Jan 2027). The only Paper C-relevant work before then is what Paper B itself adopts (the W1 archive and exporter of the Paper B revision). "Paper C" is a working name (open item O7 of the revision proposal).

**Sources.** The sequential-policy comment (`docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md`, on `docs/runbooks-04nov`; "the comment" below, with its section numbers), `SEQUENTIAL_POLICY_REVISION_20261104.md` rev 2 ("the revision"), Track S design rev 7.4 and its code on `trackS-ops-20261030`, the T4 Proposition 10 revision draft (`T4_PROP10_REVISION_20261028.md`), Track P, C3_DESIGN and the 4 Nov benchmark review.

### Revision 2 (5 Nov 2026) — what changed and why

Revision 1 (commit `5b3b714`) was reviewed independently: `docs/r1/reviews/PAPER_C_PLAN_REVIEW_20261104.md`, verdict **REVISE** (1 BLOCKING · 13 MAJOR · 16 MINOR). In chat on 5 Nov the author gave the following positions. They are reflected below but are **not decisions until rows are committed** (draft rows in §17):

- (a) **Proposer of record = the exam winner** (the Track X pick, thinking off), the same as Paper B's main proposer (R1-MAIN-PROPOSER).
- (b) **A core version for the first submission** (§14), with the rest as a stated extension.
- (c) **The equivalence margin δ for "RL adds nothing"** is the one recommended in §11.3: Paper B's practical threshold δ_n on E-T0, and 10 % of the oracle gap on E-SYN, with a pre-registered power check.

| Review finding | Change in this revision | Where |
|---|---|---|
| B1 Q3 has no powered tier with headroom; negative read as equivalence | Hypotheses per tier × channel; Q3 = superiority **and** TOST equivalence at δ; confirmatory only on E-T0 with in-tier training and a passed go/no-go; E-INT descriptive | §2, §11.3 |
| M1 "multi-step" rule inconsistent; belief not fixed | Rule applies to learning methods only; planning methods multi-step by objective; Q1 and Q3 sets enumerated; one belief model for every arm | §7 |
| M2 Q2 level-shift win | Myopic arm with g tuned on dev; matched-level guard; Ĉ fitted on training forks, tested on fresh campaigns | §2, §7 |
| M3 formulation gaps | γ = 1 with time-to-go in both resources; termination vs truncation defined; divergence is an outcome; truncation rates by arm | §3.1, §3.4 |
| M4 schema gaps | Fork design weights, y_start, immediate audited increment, eligibility, continuation policy, environment constants, divergence, ε seed; propensity-replay check | §4.1, §4.2 |
| M5 OPE under-specified | Explicit OPE section: forks as designed interventions; FQE primary, per-decision DR check; numerical support targets | §6.1 |
| M6 pooled MDPs; logs lack terminal audits | Environment contexts; confirmatory training only on the pick's logs; Track S (7B) logs as a separate context; sweep final incumbents re-audited; statuses corrected | §4.3 |
| M7 Track S inheritance does not cover E-INT | E-INT prerequisites listed; frozen E2 rule per tier | §5.1 |
| M8 go/no-go statistic | Between-fork heterogeneity τ̂² and the cross-fitted N6 improvement value, floor in δ units | §6 |
| M9 baseline definitions | N8 → AggreVaTe-style with charged rollouts; arms matched in runs + calls + audits; N7 dropped (kept as M1); N2b single-step action head; R0 FQI; oracle and random rows | §7, §8 |
| M10 cost on the wrong latency; count inconsistencies | Costs in calls, with hours as calls × L for the pick's measured latency L; counts recomputed and consistent; 2 E-T0 nodes; servers and shards stated | §12 |
| M11 statistics | α split; estimand = dev-selected artifact; fresh test blocks for SPT-7/8; E-HELD checkpoints retrained; E-INT exploratory | §11 |
| M12 minimal version does not fit May 2027 | Core version defined; allocation requests in Jan | §14 |
| M13 no positioning | New §3.6 Positioning; dataset release as an option | §3.6, §17 |
| m1–m16 | E-d vs E-c primary; Q1 on round B; training on Y/σ_node; seed registry from code; draft rows as proposed; dataset loader renamed; ghost/ctrl-only as instruments; shared incumbent-error channel; AWR cited, DACBench/CARL disambiguated; M3 baseline and controller cost; online campaign count from SNR; shards; node count; descriptive interaction regression; MPC pointer fixed in the revision; Q1 as a replication of Track S | throughout |

---

## 0. Summary

Paper B asks whether a learned **single-step** belief improves noisy acceptance, proves when the loop **reduces** to independent one-step decisions (no feedback (NF), no information (NI), fixed price) and notes that in the governed loop these conditions fail by construction, and screens on whole campaigns whether a tuned state-dependent threshold beats a tuned static one (Track S, one-way, one calibrated control). Paper C takes up what Paper B deliberately does not claim:

1. **L1, at strength.** Where in real loops is non-myopic control worth anything, and through which channel: budget, information, incumbent interaction, proposer feedback, or the shared incumbent error?
2. **L2.** With the same immediate information, does accounting for the future help, and does a planning or supervised multi-step method already capture it?
3. **L3.** Does multi-step RL add anything **beyond** strong non-RL sequential methods (tuned non-myopic thresholds, budget DP, multi-step supervised regression; model-based rollout and on-policy aggregation in the extension) at matched information, data, interaction and tuning budget — and if not, can that be shown as an equivalence, not just a failed test?
4. **L4, multi-step.** Does a language decision model that reads the proposal add value **in the multi-step policy**, beyond structured state encoders?

The experimental core is the **Sequential Policy Track (SPT)**: a transition dataset collected under a logged behaviour mixture plus repeated fork trees, a fixed method ladder trained and selected on development instances, and frozen evaluation on fresh campaigns with fresh-seed audits. The **core version** (§14) runs on synthetic worlds and two CPU nodes with the exam winner as proposer; interaction-rich GPU nodes are descriptive. Real closed-loop online RL and multi-step RL of the LLM decision model are extensions, entered only through declared gates. Every outcome of the four questions is reportable: the levels can hold or fail independently (comment §1).

---

## 1. What Paper C inherits from Paper B

| Inherited | From | Use in Paper C |
|---|---|---|
| One-step index theorem, reduction theorem, Props 10(b)/(c), the hard-budget scope note | C2 (after the author's proof check) | Where non-myopic gain can exist; design of the synthetic worlds; the information principle |
| Transition-logging contract, archives and offline exporter | Revision W1 (proposed) | Paper B campaigns become data, with gap lists (§4.3) |
| Track S code: arm-override hook, ghost and controller-only arms, forced E2 keep/discard, instance-level seed keys, fork collector, A2-U, static/dynamic families, π′, synthetic nodes | Track S S0.3 (pin `d10b05b7`, harness `a3fedbb`) | SPT's fork trees and mechanism arms on E-T0, without new harness surgery (E-INT needs more, §5.1) |
| Track S outcomes: binding shares, σ_D, flip rates, fork channel contrasts Δ_B, Δ_I, Δ_F, S1.1 interaction, S0.6/W4 sensitivity | Track S, revision W4 | Pilot variances, power planning, choice of nodes and channels, Q1 hypotheses |
| Budget-DP rule | Revision W3 (proposed) | Rung N4 of the non-RL ladder |
| C3 belief models (A3, TabPFN, Kev-0.8B/4B, Qwen controls) and labels | Paper B C3, Track P | **The** immediate-value component of every Paper C arm (one frozen belief, §7.0), retrained without the E-HELD suite where E-HELD is used (§11) |
| (NI) masking test, (NF-c) quantification, the DI diagnostic | Revision W5, C4 | Which channels to expect on which nodes |
| Node census with per-node noise and edit–edit interaction strength | Track G (G.1b, S1.1 on T1) | Choice of interaction-rich nodes |
| **Proposer of record: the exam winner** (Track X pick, thinking off), as Paper B's main proposer; runner-up for generalisation | R1-MAIN-PROPOSER, X.7, R1-BX-D6-EXAM-RUNNER-UP; author position 5 Nov | All confirmatory collection and tests. Track S's `qwen2.5-coder:7b` logs are a separate environment context (§4.3) |

---

## 2. Research questions, hypotheses and outcomes

Hypotheses are stated **per tier and channel**. The E-T0 hypotheses are fixed after Paper B's Track S outcome and before any Paper C data; Paper C's Q1 on E-T0 is therefore a **confirmatory replication and extension** of Track S on fresh instances, with the pick as proposer, a different belief model and a larger method set. Track S's instances never enter Paper C's test.

| ID | Question | Primary comparison (fixed before the test) | Hypothesis per tier | Reading of each outcome |
|---|---|---|---|---|
| **Q1** (L1) | Does non-myopic control beat the tuned static rule? | The dev-selected best of the Q1 candidate set {N3, N4, N6} vs N1 (tuned static on the same belief), on fresh E-T0 campaigns, in the **round-B** action space (execute/skip and keep/discard) | **E-T0**, budget binding by design (W from SPT-1), keep feedback with memory on: a gain at most of the size Track S estimated, through the budget and keep-feedback channels; if Track S found no gain, the hypothesis is a null and Q1 is read through its equivalence part. **E-SYN**: gains exactly in the worlds with a channel on, none in the strict null. **E-INT**: descriptive | Superiority → non-myopic value on these nodes. Equivalence (TOST at δ, §11.3) → "below δ on these nodes at power p", never "the loop is one-step". Neither → inconclusive |
| **Q2** (L2) | With the same immediate estimate, does a continuation term help? | Continuation-aware (N2 + Ĉ_future) vs myopic N2 with **g tuned on dev**, same belief; plus a **matched-level guard**: a static rule at the continuation-aware arm's realised mean threshold | Ĉ_future fitted on **training** forks predicts a gain on **fresh** campaigns where the training-fork continuation differences are non-zero | A gain that the matched-level guard also achieves is a level shift, not a continuation effect |
| **Q3** (L3) | Does multi-step RL beat the strongest non-RL multi-step method? | The dev-selected best of {R0, R1} vs the dev-selected best of {N4, N6}, matched in information, data, tuning budget and (for online arms) runs + calls + audits | Confirmatory **only on E-T0**, and only if the SPT-1 go/no-go (§6) passes with in-tier training and dev data. E-INT: descriptive. E-SYN: per-world, against the DP oracle | Two-part pre-declared decision (§11.3): superiority (one-sided) → "RL adds value here"; equivalence passes → "RL's gain is below δ at power p"; neither → "inconclusive"; go/no-go fails → "not testable at this budget" |
| **Q4** (L4) | Does a decision model that reads the proposal add value in the multi-step policy? | N6 with the LM-hidden-state encoder E-d vs N6 with the information-matched encoder E-c (structured features + PCA text embedding), equal data | In-distribution on E-T0: little or no gain. Transfer (E-HELD): extension only | E-d vs E-a is labelled an **information ablation**, not a Q4 result |
| **Q5** | Which channel produces the gain? | factorial and intervention designs of §10 | Budget first; information on high-noise nodes; feedback with memory on | Gains are not attributable; reported as such |

The two **confirmatory** families are Q1 and Q3 (comment §9.3), each at α = 0.025 (§11). Q2, Q4 and Q5 are pre-declared secondaries with their own multiplicity control.

---

## 3. Problem formulation

### 3.1 Episode, outcome, horizon and constraints

- **Episode** = one campaign: from the deployed start configuration until termination or truncation.
  - **Termination:** W exhausted, the LLM-call cap N exhausted, or the policy's stop action (round C, extension).
  - **Truncation:** infrastructure failure, a protocol STOP (A/A failure, watchdog, liveness), parse failure beyond retry, host loss. Truncated episodes never enter return targets as if complete (comment §5.1). Truncation rates are reported per arm; a difference between arms beyond a declared level is a STOP for the comparison, and otherwise a sensitivity analysis.
  - **Divergence** of a worker run (no metric at the fixed budget, as on GPU nodes) is an **in-episode outcome**, not truncation: the run is consumed, its Δ̂ is recorded as divergent, and the declared keep rule treats it as "not improved". Paper B records divergence as its own outcome class (R1-BX-REVISIONS (c)); Paper C does the same.
- **Horizon and discounting.** Finite horizon, **γ = 1** for every value method. Every encoder receives time-to-go in **both** resources (runs left and calls/slots left). Discounting with γ < 1 (the IQL/CQL default) would make the learned objective prefer episodes that end sooner, i.e. budget-exhausting policies, so it is not used. Bootstrapped methods bootstrap at the last observed state of a truncated episode; Monte Carlo targets drop it, and the drop is reported per arm.
- **Outcome** Y = the final incumbent's metric, averaged over K fresh audit seeds from a reserved audit block, oriented so that higher is better. Per node, comparisons use paired raw-unit differences; cross-node summaries use Y/σ_node with σ_node declared in advance; raw units are never averaged across nodes (comment §3.1). Pooled training across nodes uses sign-oriented Y/σ_node.
- **Matched resources** for every compared policy on an instance: the same instance seed key, start configuration, W, N, proposer, manager repetition and audit seeds.

### 3.2 State and information principle

The decision state s_t contains (comment §3.2):
- the proposal (diff or structured edit) and its duplicate/no-op flags;
- the incumbent configuration and its observation history;
- worker runs used/left, LLM calls used/left, proposal slots left — **from the budget ledger, never the trial index**;
- recent accept/reject history, previously executed configurations, repeat flags;
- the noise estimate and its source;
- the environment context (proposer, W, N, memory mode, edit schema, run budget), when data from several contexts are pooled (§4.3);
- a fixed-length history summary for learned encoders.

**Information principle.** At a decision point every compared policy receives the same legal information. A gain of a method with a richer view (for example full history for the RL policy, current proposal only for a baseline) is not attributed to the method. Ablations that deliberately change information are labelled as information ablations.

**Partial observability.** The proposer is an LLM whose internal state is hidden and whose memory display depends on past decisions; the problem is a POMDP in general. Policies act on the logged observation s_t; history summaries are the declared approximation.

### 3.3 Action space, staged (comment §3.3)

| Round | Actions controlled by the policy | Frozen | Role |
|---|---|---|---|
| **A** | E1 execute / skip | E2 acceptance = a shared frozen rule per tier (E-T0: the A2-U Bayes margin; E-INT: the C3 belief's Bayes margin, §5.1) | Development stage: implementation, RL debugging, budget/screening-only L1; **descriptive** |
| **B** | + E2 keep / discard (forced, via the Track S hook) | — | **Confirmatory stage** for Q1 and Q3: it contains the keep-feedback channel, the only channel with calibrated sensitivity in Track S (P2+ concentrated), and matches Track S's families |
| **C** (extension) | + verify (2r runs, racing-style), stop campaign early | — | verify costs more than one run; stop changes the horizon |
| not planned | revise, memory switch, display changes as actions | — | action attribution and coverage explode (comment §3.3) |

Ghost and controller-only arms are **instruments** for §10, not deployable actions; they are excluded from the action space and from OPE.

### 3.4 Reward

- **Primary:** r_t = 0 for t < T, r_T = Y_final − Y_start, where Y_start is the audited start configuration on the same audit seeds (a per-instance shift of Y).
- **Shaping** is allowed as a training device only, declared in advance; final evaluation uses the unmodified audited terminal Y. Intermediate rewards never use audit values that are not visible at deployment unless they are explicitly a training target. Potential-based shaping is checked for termination, discounting and implementation conditions before any invariance is claimed (comment §3.4).
- **Costs** (executions, wall time, LLM calls) are reported separately and are not mixed into the objective while W is fixed.

### 3.5 Relation to DAC and to Paper B's theory

- **DAC view.** The target algorithm is the governed loop, instances are (node, seed), and the policy sets per-step thresholds.
- **Paper B's reduction theorem.** A policy can beat the Bayes one-step rule only where (NF) or (NI) fails or the budget is hard. In the governed loop these fail by construction, so every environment has some headroom in principle. Paper C's environments are chosen so that each channel can be switched on or off (§5), and its analysis reports gains per channel.
- **Theory work items** (proposals, to be proved or dropped):
  - **T-C1.** A bound on the gain of the optimal budget policy over the best static price under a hard budget with i.i.d. one-step values (stochastic knapsack, multisecretary; verify against Arlotto & Gurvich 2019 before relying on it).
  - **T-C2.** A value-of-information bound for the NI channel in the Gaussian latent-sensitivity model of Prop 10(c), linked to the knowledge gradient.
  - **T-C3.** Conditions under which multi-step supervised regression on fork outcomes (one policy-improvement step) is already within a stated gap of the optimum. This frames Q3's equivalence result.

### 3.6 Positioning (one line per area; citations to be verified before the manuscript)

- **Dynamic algorithm configuration.** DAC (Biedenkapp et al. 2020; Adriaensen et al. 2022); DACBench (Eimer et al., IJCAI 2021); contextual RL benchmarks, CARL (Benjamins, Eimer et al., TMLR 2023); theory-inspired DAC benchmarks with known optimal policies (Biedenkapp et al., GECCO 2022). *Paper C:* E-SYN plays the same role for a governed loop whose "algorithm" is an LLM proposer under noisy acceptance, and the real tiers carry ground truth from fork contrasts.
- **Costly inspection and index policies.** Pandora's box (Weitzman 1979) and its correlated variants are the classical model of the execute decision and of (NI) failures. *Paper C:* measures when the index policy is beaten in a loop with a reactive proposer.
- **Stochastic and dynamic knapsack, multisecretary** (Kleywegt & Papastavrou 1998; Arlotto & Gurvich 2019). Bandits with knapsacks (Badanidiyuru, Kleinberg & Slivkins). *Paper C:* the budget channel (N4, T-C1).
- **Ranking and selection, racing, multi-fidelity early stopping.** Knowledge gradient (Frazier et al. 2008); Hoeffding races (Maron & Moore); successive halving and Hyperband (Karnin et al. 2013; Jamieson & Talwalkar 2016; Li et al. 2018). *Paper C:* verify and stop (round C).
- **Offline RL and off-policy evaluation.**
  - Offline RL: IQL (Kostrikov et al. 2021, arXiv:2110.06169), CQL (Kumar et al. 2020, arXiv:2006.04779), AWR (Peng et al. 2019, arXiv:1910.00177), BCQ, TD3+BC, and fitted Q iteration (Ernst et al. 2005).
  - Off-policy evaluation: FQE (Le et al. 2019), doubly robust (Jiang & Li 2016), and the Voloshin et al. empirical OPE study.
  - *Paper C:* fork-based ground truth for OPE in a real loop.
- **Imitation with cost-to-go.** DAgger (Ross et al. 2011); AggreVaTe (Ross & Bagnell 2014). *Paper C:* the N8 comparator (extension).
- **RL for LLM agents.** ILQL (Snell et al. 2022), which is close to M2; ArCHer; multi-turn GRPO variants (RAGEN/StarPO). *Paper C:* M1 (core), M2 and M3 (extension).
- **LLM-driven ML-experiment agents.** MLAgentBench, MLGym, AIDE, autoresearch. *Paper C:* the controller *around* such a proposer, not the proposer itself.
- **Possible contribution.** The transition and fork dataset, with fork-based OPE ground truth, could be released (open decision P8).

---

## 4. The multi-step transition dataset

### 4.1 Record schema (one row per decision point)

| Group | Field | Notes |
|---|---|---|
| Identity | node, suite, tier, instance_id, campaign_id, root_id, fork_id, branch path, step_index, epoch (E1/E2/verify) | campaign_id is the clustering unit |
| Environment context | proposer (model, GGUF sha, thinking policy), W, LLM cap N, memory mode, skip display, edit schema (v1 / v2-diff), run budget (steps or minutes) | constant per campaign; needed for pooling (§4.3) |
| Policy | policy string, policy version/sha, behaviour-mixture component, **action probability** under the behaviour policy, ε-randomisation flag and **ε RNG seed**, continuation-policy id per branch | deterministic policies log 1.0 and the deterministic rule |
| Fork design | selection rule (`uniform` / `oversample`), **`p_select`**, `channel_arms`, replicate index | for design-based weights (§6.1); from Track S `Selection` |
| Seeds | instance seed key, manager repetition, worker seed, audit seed block | instance-level keys as in Track S |
| State | proposal hash + diff/edit text pointer, incumbent config hash, duplicate/no-op flags, **eligible vs rule-forced** flag, forecast tuple (π, μ, τ, σ, V̂\*, m̂) from each declared belief model, runs used/left, LLM calls used/left, slots left, keeps/skips so far, history-summary pointer | rule-forced skips consume a call and a slot but are not policy decisions |
| Action | action, forced or chosen, rule that produced it | forced actions only in forks or interventions |
| Outcome | observed Δ̂ (if executed) or divergence, keep decision, next incumbent hash, runs and calls consumed, wall time; **immediate audited increment** (`immediate_measured`) where audited | C = Y − immediate underlies Δ_B, Δ_I, Δ_F |
| Episode end | `terminated` (W, N, policy stop) vs `truncated` (§3.1) with reason | |
| Terminal | Y_terminal, per-seed audited values, audit seeds; **`y_start`** on the same seeds | on the last record of the campaign |
| Provenance | host, GPU, harness and paper commits, GGUF sha, llama.cpp build, `cache_prompt`, label (PILOT/EVIDENCE) | as Track S `Provenance` |

### 4.2 Mechanical checks (run on every batch)

- Budget conservation: Σ runs consumed = W − runs left at every step, and the same for calls.
- Contiguous step indices, and exactly one terminal record per complete campaign.
- Next-state consistency: s_{t+1}'s incumbent hash equals the keep outcome at t.
- A/A replay: a fork that takes the root's action reproduces the root's ledger (Track S arm-invariance test 4).
- **Propensity replay:** re-running the logged behaviour component on the logged state reproduces the action and its logged probability.
- **Design-weight check:** the fork weights 1/p_select can be recomputed from the logged design fields.
- No field of a future step, and no audit value, appears in a state.
- Seed keys never collide with Paper B's. Test against a registry generated from code (§11).

### 4.3 Sources of transitions and environment contexts

Each (proposer, W, N, memory mode, run budget, edit schema) is a separate **environment context**. Confirmatory training uses only logs from the proposer of record (the pick). Other contexts may be used for pre-training or as auxiliary data, with the context in the state, and never in a confirmatory test.

| Source | Proposer | Behaviour policy | Coverage it adds | Status |
|---|---|---|---|---|
| Paper B sweep 2 T0, HoreKa T1 sweep | pick | execute-all | executed transitions only, many nodes. **No terminal audits**: sweep audits are per-proposal labels, so Y_terminal needs a CPU re-audit of final incumbents on a Paper C audit block (≈ 1 audit per campaign, §12) | planned; exportable if revision W1 is adopted and the sweeps run |
| Paper B D.3 | pick | the deployed arms | on-policy states of myopic controllers; may use ≈ 5-min runs (R1-BX-D5), so it is a different context | planned; sidecar if W1 is adopted |
| Paper B Track S S0.4–S0.7, S3e | `qwen2.5-coder:7b` | execute-all, A2-U at two prices, 15 static, 4 dynamic, π\*, m\*, matched static, secondaries | threshold diversity, binding budgets: **separate context** (different proposer, LLM cap 40, W from S0.5b) | planned; exportable from the archive if W1 is adopted |
| Paper B Track S S3a | `qwen2.5-coder:7b` | forks with skip/execute (+ ghost/ctrl-only), keep/discard | (s, a, Monte Carlo return) pairs for N6 pre-training; post-fork transitions only if the leaf ledgers are archived | planned; 150 forks per node |
| **SPT-2** (new) | pick | behaviour mixture with logged randomisation | action support where deterministic policies give none | Paper C |
| **SPT-3** (new) | pick | repeated fork trees | Q^{π_b} differences with replication | Paper C |
| **SPT-7** (extension) | pick | the learner's own policy online | on-policy data | Paper C extension |

Whether Track S itself is repeated with the pick is Paper B's open decision (R1-TRACKS-PICK-REPEAT-DEFER). Paper C collects its own E-T0 data with the pick in any case.

---

## 5. Environments

| Tier | Environment | Channels on | Role |
|---|---|---|---|
| **E-SYN** | Synthetic worlds (revision W4, extended): budget opportunity cost, information (Prop 10(c)), incumbent interaction, proposer feedback, **shared incumbent error**, strict null; exact DP optimum where the state space allows | One at a time, then pairs | Implementation checks, false-positive rates, oracle gaps, method behaviour per channel, Q3's per-world equivalence; never evidence about the real loop |
| **E-T0** | **Two** of Paper B's CPU nodes, `digits_mlp` and `tabular_mlp`, with single-parameter edits and binding W. The OpenML nodes are an optional low-interaction condition | Budget; keep feedback with memory on; weak information; shared incumbent error | The real-loop tier for the full SPT; confirmatory Q1 and Q3 |
| **E-INT** | Interaction-rich real nodes: T1 tasks chosen by measured edit–edit interaction (S1.1) and noise, with short fixed-step budgets and code-level diffs | All channels plausible | **Descriptive** in the core version (1 node); a powered tier only in the extension, with in-tier training and dev budgets |
| **E-HELD** (extension) | One held-out suite or task family, never used for training or selection, including by any inherited checkpoint | — | Transfer (Q4) |
| **E-SIM** (extension; training aid) | A learned transition model fitted on SPT data: proposal-value model, keep model, budget dynamics, next-proposal category model | As learned | MPC rollouts (N5) and model-based training only. Its error is reported, and no conclusion rests on it (comment §4.2 B2, §11) |

**Task selection rule.** E-INT nodes are chosen by declared criteria (interaction strength, noise, budget binding, run cost) from the census, before any SPT outcome, and the screening funnel is reported (as R1-BX-D12). Easy and hard nodes are reported separately, never averaged into one score (comment §7.4). A cross-node "headroom vs interaction strength" relation over 3–6 nodes is descriptive only.

### 5.1 E-INT prerequisites

None of these is inherited from Track S:
- **A diff-capable base forecaster.** A2-U is a hierarchical model over (edit key, sign of the step) with one parameter per proposal, so it does not apply to diffs. The frozen C3 belief takes its place.
- **A keep rule for diffs**, and so the frozen E2 rule of round A on E-INT: the C3 belief's Bayes margin.
- **Diff-level duplicate detection.**
- **S0.1-style identity** for the pick on the E-INT hosts.
- **G.2 diff support** in the harness, and the open items of the Track S GPU-node design (manager, budget, seed replay). Their role in Paper B is open under R1-BX-D10.

---

## 6. The Sequential Policy Track (SPT)

| Phase | What | Where | Done when |
|---|---|---|---|
| **SPT-0** Contract and infrastructure | Freeze §3–§4. Port the Track S hooks into the SPT runner. Build a **logged-transition dataset loader** (no simulator: it cannot answer unlogged actions). Build the seed registry from code, the analysis code, and the E-SYN suite with DP oracles. Fix the frozen belief model (§7.0) | desktop + review | tests pass; independent review accepted; author row |
| **SPT-1** Pilot (not used for testing) | Per node: variance of campaign Y between policies and repetitions; fork repeat variance vs between-fork variance; proposer-seed vs worker-seed share; A/A identity; **in-campaign latency of the pick** and cost per campaign; binding shares and the W that binds; the go/no-go statistics (below) | E-T0 | numbers in the pre-declaration; go/no-go for RL |
| **SPT-2** Behaviour-mixture collection | Training instances only. 5 base policies (execute-all, tuned static N1, non-myopic members N3, budget DP N4, deployed myopic C3 policy N2) × {plain, ε = 0.1, ε = 0.25} = **15 components**, at E1 and, in round B, at E2. Probabilities and ε seeds logged | E-T0 | support targets met (§6.1), or a declared shortfall |
| **SPT-3** Fork trees | Roots under the mixture; fork points sampled uniformly plus a near-threshold oversample, with `p_select` logged. E1 arms: skip/execute (+ ghost/ctrl-only on a third, as instruments). E2 arms: keep/discard. **r = 2 continuations per arm under 2 declared continuation policies** (4 per arm). Depth-2 forks only in the extension | E-T0 | Q^{π_b}(s, a) − Q^{π_b}(s, a′) estimates with intervals; channel contrasts |
| **SPT-4** Coverage, support and OPE diagnostics | §6.1 | desktop | candidates with unsupported actions flagged or constrained |
| **SPT-5** Training and selection | The method ladder (§7) on training data. OPE screens candidates; dev campaigns choose hyperparameters, checkpoints and the "strongest" member of each set by a fixed rule; 3 training seeds for the chosen configuration | CPU/GPU (small models) | frozen artifacts + hashes; pre-declaration of SPT-6 |
| **SPT-6** Final test | Frozen artifacts on fresh test instances, paired; fresh audit seeds; exact A/A placebo on a subset | E-T0; E-INT descriptive | report; confirmatory Q1/Q3 |
| **SPT-7** Online fine-tuning (extension; §8) | Bounded online interaction on training instances, matched in runs + calls + audits for all arms | E-T0 | separate pre-declaration and authorization; its own fresh test block |
| **SPT-8** LLM decision model, multi-step (extension; §9) | After the gates of §9.1 | E-T0 | separate pre-declaration and authorization; its own fresh test block |

**Go/no-go for RL after SPT-1.** A sequential policy gains through **state-dependent sign changes** in Q(s, execute) − Q(s, skip) (and keep − discard). A mean Q difference near zero is therefore no evidence against headroom. Two statistics, per node, each with a floor in units of δ_n (§11.3), declared before SPT-1:
1. the **between-fork heterogeneity** of true fork Q differences, τ̂² = (between-fork variance) − (mean within-fork s.e.²), which the replicates r = 2 make estimable;
2. the **cross-fitted value of the N6 improvement step**: the estimated gain of acting on f̂(s) over π_b, on held-out forks.

If both are below their floors on both E-T0 nodes, multi-step RL is not trained. Q3 is reported as "not testable at this budget", and the paper rests on Q1, Q2 and Q5. This is the lesson of E1b in Paper B, where campaign-final rewards made the continue-vs-verify group advantages ≈ 0.

### 6.1 Off-policy evaluation and support

- **Fork data are designed interventions.** They enter estimates with state weights 1/p_select, all arms observed, and continuations under a known policy. They do not enter through behaviour propensities: a forced action has no defined likelihood ratio under a deterministic behaviour component.
- **Behaviour-mixture data.** Use the marginal mixture propensity (the balance heuristic) rather than the component propensity. Both are valid when the components are known; the marginal one has lower variance.
- **Estimators.**
  - **FQE is primary.** Per-decision weighted doubly robust is a check. With ε = 0.1 at E1 and about 14–20 eligible decisions per campaign, trajectory-level importance weights explode, so doubly robust is effectively model-based, and this is stated.
  - Inverse-propensity weighting is used for **population averages** (channel contrasts, mean Q differences), not for fitting N6, where weighting by 1/p only adds variance.
- **OPE only screens.** Candidates are selected on dev campaigns, and conclusions come only from SPT-6.
- **Numerical support targets, declared before SPT-2:**
  - for each action, at least 30 logged occurrences per state cluster (clusters of the forecast and budget state, fixed in SPT-0);
  - for each candidate, an effective sample size of at least 200 decisions in the FQE screen.
  - A shortfall is reported as "insufficient data", not hidden behind a more complex algorithm (comment §12 step 5).

---

## 7. Methods ladder

### 7.0 Common rules

- **One belief model for every arm.** Every arm uses the same frozen immediate-value forecaster for V̂\* and m̂. This is the C3 belief chosen in SPT-0 from Paper B's frozen models, retrained without the E-HELD suite if E-HELD is used. N1 is the tuned static rule *on that forecaster*, not on A2-U. A2-U is kept as a reference row on E-T0 only.
- **Same inputs, same budget.** All methods get the same state view (§3.2), the same training instances and transitions, and a declared, equal tuning budget (§12, SPT-5). Small, transparent models come first (comment §5.4).
- **What counts as multi-step.**
  - A **learning** method (supervised or RL) is multi-step only if its target is a multi-step return or a bootstrapped multi-step target. Re-using the per-proposal immediate u under any algorithm is single-step (comment §5.4).
  - A **planning** method (N4, N5) is multi-step by its objective.
  - A threshold rule tuned by black-box search on terminal Y (N1, N3) is a tuned rule. Its level is set by its form: static (N1) or non-myopic (N3).

### 7.1 Non-RL

| ID | Method | Learns from | Set | Version |
|---|---|---|---|---|
| N0 | default rule / execute-all | — | floor | core |
| N1 | tuned static thresholds (g, h) on the common belief | dev campaigns | Q1 reference | core |
| N2 | myopic one-step rule on the common belief, **g tuned on dev** | per-proposal labels + dev | Q2 reference | core |
| N2b | single-step learned action head (R-A1 style, cost-sensitive classification on per-proposal outcomes) | per-proposal labels | single-step control for "RL on multi-step returns" with the same encoder | core |
| N3 | non-myopic threshold members (Track S's dynamic members, re-fitted on the common belief), tuned | dev campaigns | Q1 candidate | core |
| N4 | budget DP (stochastic knapsack) | V̂\* distribution and slot-skip rate on training data | Q1 candidate; Q3 comparator | core |
| N5 | MPC / finite-horizon rollout on E-SIM, completed by a frozen base policy | transitions | Q3 comparator | extension |
| N6 | multi-step supervised regression on fork Q differences (π′ generalised; one approximate policy-improvement step) | SPT-3 forks (training forks only) | Q1 candidate; Q3 comparator (comment §6.2.3) | core |
| N8 | AggreVaTe-style on-policy aggregation: fork-rollout labels at the learner's states, rollouts charged in runs + calls + audits | online labels on training instances | comparator for SPT-7 | extension |
| ref | hindsight / fork oracle row; random at matched realised budget; A2-U (E-T0) | — | diagnostics only (comment §6.1, §6.4) | core |

Revision 1's N7 (behaviour cloning of the strongest policy) is dropped from the small-model ladder: it can at best tie its teacher. It is kept as the LLM route M1 (§9), where it tests representation.

### 7.2 RL

| ID | Method | Target | Notes | Version |
|---|---|---|---|---|
| R0 | fitted Q iteration with LightGBM (Ernst et al. 2005) | bootstrapped multi-step, γ = 1 | the most transparent multi-step learner for binary actions on about 10⁴ transitions | core |
| R1 | IQL (expectile value, advantage-weighted extraction) — **primary deep method** | multi-step return / bootstrap, γ = 1 | in-sample learning against distribution shift (Kostrikov et al. 2021, arXiv:2110.06169) | core |
| R2 | CQL (Kumar et al. 2020, arXiv:2006.04779) or AWR (Peng et al. 2019, arXiv:1910.00177) | same | alternative | extension |
| R3 | online fine-tuning of the selected offline policy (SPT-7) | on-policy returns | §8 | extension |
| R4 | LLM decision-model variants | §9 | — | M1 core; M2/M3 extension |

**Enumerated sets.** Q1 candidates: {N3, N4, N6}. Q3 non-RL comparators: {N4, N6} in the core version, plus {N5, N8} in the extension. Q3 RL set: {R0, R1} in the core version, plus {R2, R3} in the extension. The "best" member of each set is chosen on dev by a fixed rule (the highest dev mean paired gain over N1, with ties going to the simpler method).

### 7.3 State encoders (Q4)

- **E-a:** structured features → MLP.
- **E-b:** LightGBM / TabPFN on the same features, for value regression where applicable.
- **E-c:** the same features plus a PCA-reduced proposal-text embedding (the information-matched view of R1-BX-D13).
- **E-d:** the LM decision model's hidden state (Kev / Qwen control).

Q4's primary is E-d vs E-c **within N6**, on equal data; it is matched only approximately (PCA embedding vs full text), and this is stated. E-d vs E-a is an information ablation. LM encoders inside R1 are the M2 route (extension).

---

## 8. Real closed-loop multi-step RL (online; extension)

**Design** (comment §5.5):
- All online interaction is on **training instances only**, under fixed caps on new worker runs, LLM calls and audits.
- Three arms, **matched in new worker runs + LLM calls + audits**, not in campaigns:
  1. offline data only;
  2. offline + new data for a supervised/planning learner (N6 or N8, with N8's fork rollouts charged);
  3. offline + new data for online RL (R3).
- Frozen evaluation is on a **separate fresh test block**. The difference (3) − (2) is the RL-specific effect; (2) − (1) is the data effect.

**Mechanics.**
- Campaign workers run asynchronously. The policy is updated after each batch of B completed campaigns, and the policy version is logged per decision.
- Exploration comes only through the logged ε-randomisation of §6 or the policy's own stochasticity, with probabilities logged.
- STOP on: return collapse on dev, a budget-accounting mismatch, an unsupported-action rate above a declared level, an A/A failure, or the cap. Dev monitoring campaigns are counted in the cap.

**Size.** The number of online campaigns is derived from SPT-1's advantage signal-to-noise, not fixed in advance. Revision 1's "2,000" is withdrawn. Cost per E-T0 campaign is 40 · L proposer-seconds plus ≈ 40 s of CPU (§12). E-INT online RL is not planned: at ≈ 0.85 GPU-h per campaign (2-minute runs; ≈ 2.5× at 5-minute runs) it is unaffordable beyond a token budget.

---

## 9. Multi-step RL of the LLM decision model

### 9.1 Entry gates (comment §12 step 6)

All must hold before any SPT-8 run. Gates are read on dev campaigns or on SPT-6's reported summaries; SPT-8 is evaluated only on its own fresh test block, so the SPT-6 test set is never reused after an adaptive choice.
1. SPT-6 shows sequential headroom on at least one tier: Q1 superiority, or the fork heterogeneity τ̂² above its floor.
2. The strongest non-RL multi-step baseline (N6) and a small-model RL policy (R0/R1) exist with interpretable results.
3. The SPT-4 transition data pass the support targets.
4. The proposal text is shown to matter for the multi-step value (E-c or E-d beats E-a in N6 on **dev**); otherwise a language model has nothing to add.
5. The cost projection below fits an authorized budget.

M1 (distillation) is in the core version and needs only gates 2 and 3.

### 9.2 Model and interface

- **Base:** the Paper B finalists (Kev-0.8B/4B; Qwen3.5 base controls), LoRA as in Track P.
- **Input:** the history summary and budget fields first, the proposal last, immediately before the readout (R1-BX-REVISIONS (d) / P13 ordering).
- **Belief/action decoupling is kept.** The belief head stays trained by a bounded proper score on per-proposal labels. A separate value/advantage head (or action head) carries the multi-step target. This preserves calibration and keeps the single-step belief comparable with Paper B.

### 9.3 Three training routes, cheapest first

| Route | What | Data | Cost | Version |
|---|---|---|---|---|
| **M1 distillation** | Advantage-weighted SFT of the action head on N6/R0/R1 advantages (or BC of the best small-model policy) | existing transitions | small: a few GPU-h per model on TASL-7 | core (Q4 secondary, in-distribution) |
| **M2 offline value learning with an LM encoder** | IQL (R1) with the decision model's hidden state as encoder; belief head frozen or co-trained with RPS | SPT-2/3 transitions | moderate (offline, GPU-hours) | extension |
| **M3 on-policy, fork-grouped policy gradient** | GRPO/PPO-style updates where a group is the set of continuations from one root state; reward = terminal audited Y; the **value head is the baseline** for decisions after the root (PPO/GAE), with leave-one-out only at the root; KL to the M1/M2 checkpoint | new online rollouts | large (below) | extension |

**M3 cost.** One batch of 16 root states × 8 continuations = 128 continuations of ≈ 10 remaining decisions, i.e. ≈ 20 proposer calls each, so ≈ 2,560 calls, or 2,560 · L seconds of proposer time, plus ≈ 20 s of CPU per continuation. 200 updates therefore take ≈ 512k calls. Add controller inference, and the memory cost of co-locating the proposer with Kev-4B LoRA training on a 24 GB card (likely not possible on one card; a second card or time-slicing is required). On the two contested 4090s this is weeks of exclusive use even at the 7B's 0.7 s per call. On E-INT one batch is ≈ 128 × 0.5 GPU-h ≈ 64 GPU-h, and 200 updates ≈ 12,800 GPU-h: **infeasible**. M3 is E-T0-only and an extension.

### 9.4 Monitors and stop rules

As in Track P §6.4 (ECE drift, width ratio, entropy collapse, KL), plus the share of zero-advantage groups, the unsupported-action rate, and the return on dev campaigns. Roll back to the best checkpoint on any breach.

### 9.5 What a result would mean

- **M1 ≈ N6 with E-c on E-T0:** the LM adds nothing multi-step beyond its single-step belief in-distribution — an L4 negative for sequential control on this tier.
- **M1/M2 better on E-HELD only** (extension): the LM's value is transfer, not in-distribution control.
- **M3 better than M2 at equal interaction** (extension): evidence for on-policy multi-step RL of an LM controller, conditional on the node tier.

---

## 10. Mechanism attribution (powered versions of Track S's diagnostics)

| Channel | Design | Prediction / reading |
|---|---|---|
| Budget | Worker-run cap as a factor (loose vs binding), LLM cap fixed. Report the binding share, the execute rate per step, and runs left at the end | A gain only under binding caps that N4 recovers is a budget-allocation (DAC) gain, not one specific to RL or feedback. Budget levels are fixed in advance, never chosen after results (comment §7.1) |
| Information | Execute with the result visible vs ghost-like execution with the result hidden from the controller, at matched budget (Track S ghost/ctrl-only instruments) | Δ_I > 0 where (NI) fails; the masking test predicts where |
| Proposer feedback | Forced keep/discard at matched histories (a powered DI test); memory none vs `append_only_summary`; a prompt-display ablation; the debiased-memory intervention, if the author moves the C4 A/B here (revision O6) | Changes in the later proposal law and in audited increments over each branch's incumbent (R1-C4-ENDPOINT) |
| Shared incumbent error | Re-audit the recorded incumbent on fresh seeds at fork points vs carry its recorded value (E-SYN world plus an E-T0 intervention) | With e as a shared latent the loop lies outside 10(a′) (T4 revision R1); the core C1 phenomenon |
| Incumbent interaction | 2 × 2 factorials of edit pairs (A alone, B alone, A + B, both orders) on the E-INT node; per-node interaction strength as a covariate | Descriptive across nodes |

Every intervention arm is verified to change only its intended channel: prompt bytes, novelty set, metric leakage, budget, incumbent restore, controller state and seed mapping (comment §7.3). Common random numbers after a fork are not assumed to pair later proposals; the pairing gain is measured.

---

## 11. Statistics

### 11.1 Units, splits and seeds

- **Unit:** the campaign instance i = (node, instance seed, start configuration), with paired D_i = Y_i(π_a) − Y_i(π_b). Training seeds, proposer repetitions and audit seeds are nested, never counted as independent campaigns (comment §9.1).
- **Splits:**
  - training instances: collection, forks and training;
  - development instances: tuning, checkpoint and method selection, the "strongest" rule, and the §9.1 gates;
  - test instances: frozen artifacts only, with **separate fresh test blocks for SPT-6, SPT-7 and SPT-8**;
  - audit seeds: never used in training or selection.
  - Leakage checks beyond instance seeds: shared edit templates and start configurations across splits (comment §9.2).
- **E-HELD:** Paper B's belief checkpoints were trained with leave-one-suite-out over all three suites. Before any Paper C use with E-HELD, the belief is retrained or frozen from a checkpoint that never saw the held-out suite.
- **Seed registry:** generated **from code, not prose** (Track S `collect.py` blocks: instance blocks 30000–30250, 30250–30500, 30500–31000, 31000–32000, 32000–33000, 36000–37000, 39000–40000; audit bases 100k–700k; `SELECTION_SEED = 35001`; leaf repetitions at `REP_BASE + r` (100+); sweep instance seeds from `e1b_collect._instance_seed`; E1b 5001–5006; audits 7001–7010; G.1b 8001–8010; exam 9001+, 9101+, 9201+). Paper C reserves disjoint blocks, and a test asserts that no (node, instance seed) key collides with Paper B's.

### 11.2 Confirmatory families and estimand

- **Confirmatory:** Q1 and Q3 only, each at **α = 0.025 one-sided** (an even split, so the familywise rate over the confirmatory slate is ≤ 0.05), with Holm across the two E-T0 nodes within each family. Q2, Q4 and Q5 are pre-declared secondaries with their own Holm family. Paper B's Track S false-positive budget is not reused.
- **Estimand for learned methods:** the **artifact chosen by the pre-declared dev rule**, conditional on its training run. The spread over the 3 training seeds of the chosen configuration is reported descriptively; the best seed is never reported as the result (comment §9.5).
- **Power:** from SPT-1 variances, by simulating the whole pipeline (training, tuning, selection, test) rather than with a fixed-policy formula, including winner's-curse effects from selection. Track S's n = 300 is not copied (comment §9.4). An under-powered comparison is declared exploratory in advance. E-INT is exploratory.

### 11.3 Equivalence margin δ and the two-part decision (author position, 5 Nov)

- **Q3 decision rule, pre-declared:**
  - **Superiority:** one-sided test of best RL vs best non-RL comparator at α = 0.025 (Holm across nodes).
  - **Equivalence:** TOST at margin δ, each side at α = 0.025.
  - Reading: superiority → "RL adds value here"; equivalence passes → "RL's gain is below δ at power p"; neither → "inconclusive"; go/no-go fails → "not testable at this budget".
  - Q1's negative is worded with the same TOST rule, as a secondary statement.
- **Margin on E-T0:** per node, **δ_n = max(0.002, 0.25 · s̃_n)** on the paired difference of terminal raw Y, where s̃_n is Paper B's frozen median paired standard deviation over the node's edits.
  - This is the practical threshold Paper B already uses for a meaningful gain (`setup.tex`, offline gate), so "RL adds nothing" means "no gain Paper B would have called meaningful", and the margin is not chosen to make equivalence easy.
  - Sensitivity: 0.5 · δ_n.
- **Margin on E-SYN:** per world, **10 % of the gap between the DP oracle and the best myopic rule**: RL may close at most this much more of the gap than the best non-RL method and still count as equivalent.
- **Pre-registered power check:** at the planned test n and SPT-1's variance (whole-pipeline simulation), TOST must have power ≥ 0.80 at a true difference of 0.
  - If it does not, the equivalence part is declared **untestable in advance** for that node. Neither δ nor n is changed after any test outcome.
- **Timing:** δ, the power rule and the decision table are committed before any Paper C data exist (draft row R1-PAPERC-DELTA).

---

## 12. Cost model (recompute after SPT-1)

**Formula** (comment §10): total = training trajectories + fork continuations + baseline tuning + test campaigns + independent audits (+ online interaction).
- Costs are logged as worker runs, proposer calls and tokens, audit runs, controller inference time, training GPU/CPU time, wall time, and API cost if any.
- Two comparisons are reported: at equal deployment budget, and including development cost (how many deployments repay it).

**Latency.** All E-T0 figures are given in **proposer calls**. Hours are calls × **L**, the pick's in-campaign latency with thinking off, which is **not yet measured**. R1-MAIN-PROPOSER (h) projects it before sweep 2, and SPT-1 re-measures it in campaign, where prompts grow with memory. For scale, the 7B's measured 0.7 s per call (`cache_prompt: false`, fixed probe prompts) gives the lower row; a larger pick could be several times slower. A campaign also has ≈ 40 s of worker and audit CPU. With ≥ 3 concurrent shards per server the proposer is the bottleneck (the Track S collector is serial and would need sharding).

**Per E-T0 node, core version** (≤ 40 calls per campaign, ≈ 20 per fork continuation):

| Item | Count | Proposer calls |
|---|---|---|
| SPT-1 pilot | 150 campaigns + 60 forks × 2 arms × 20 | 8.4k |
| SPT-2 mixture | 15 components × 40 instances = 600 campaigns | 24k |
| SPT-3 forks, E1 | 300 forks × 2.67 arms (skip/execute + ghost/ctrl-only on a third) × 4 continuations × 20 | 64k |
| SPT-3 forks, E2 (round B) | 150 forks × 2 arms × 4 continuations × 20 | 24k |
| SPT-3 roots | ≈ 100 root campaigns (3 forks per root) | 4k |
| SPT-5 dev selection | threshold methods N1–N4 as Track S S0.7 (≈ 460 campaigns); 4 learned methods (N2b, N6, R0, R1) × 3 OPE-screened candidates × 30 dev instances (360); 3 seeds of each chosen configuration × 30 (360) | 47k |
| SPT-6 test | 9 arms × 300 instances (placeholder n) + 50 A/A campaigns | 110k |
| **Total** | ≈ 7,000 campaign-equivalents | **≈ 282k** |

The 9 SPT-6 arms are: N0; N1; best Q1 candidate; N2 (tuned g); N2 + Ĉ_future; the matched-level guard; best RL; best non-RL Q3 comparator, which shares campaigns with the Q1 best when they coincide; and N2b.

- **Proposer time:** ≈ 282k · L per node and ≈ 564k · L for the two nodes. At L = 0.7 s that is ≈ 55 h per node (≈ 110 h for both); at L = 2 s, ≈ 156 h per node (≈ 313 h, about 6.5 days on both 4090s if exclusive).
- **Servers:** two RTX 4090 hosts exist (TASL-2, TASL-7), both contested by Paper B work until its submission. deepthought (TITAN X) ran the 7B at 7.26 s per call and is not a realistic proposer host.
- **Additional costs:** a CPU re-audit of the final incumbents of re-used sweep campaigns on a Paper C audit block; small-model training (CPU, minutes to hours); M1 SFT (a few GPU-h per model on TASL-7).

**E-INT, core (descriptive, 1 node).**
- Paper B's T1 logs are used for training-side description.
- At most 100 test campaigns at ≈ 0.85 GPU-h each (2-minute runs, W = 20, K = 5), i.e. ≈ 85 GPU-h, plus start audits.
- At 5-minute runs (R1-BX-D5) that becomes ≈ 2.5×, ≈ 215 GPU-h.
- No forks.
- An allocation of ≈ 250 GPU-h is requested in **January**, using the Track G census costs.

**Extension (not costed in detail).** Powered E-INT needs in-tier training, dev and forks at several hundred GPU-h per node: revision 1's minimal figure was ≈ 575 GPU-h per node, with fork roots (≈ 21 GPU-h) omitted. SPT-7 and N8 are sized from SPT-1's signal-to-noise. M3 is in §9.3.

---

## 13. Other items moved from Paper B to Paper C (proposed)

| Item | Paper B status | In Paper C |
|---|---|---|
| A7 online RL | proposed to leave Paper B (revision §9, R1-SEQ-A7-MOVE, draft) | §8 (extension) |
| Two-step continuation-value rule (Longstaff–Schwartz / FQE) for budgeted verify | proposed to leave Paper B (same draft row) | round C (extension); R0 covers FQI |
| C4 debiased-memory A/B | open (revision O6) | §10 feedback row, if moved |
| H.8 execute/skip environment amendment | deferred (R1-H8-DEFERRED) | SPT-0 logged-transition loader; E-SIM for unlogged actions |
| E2 keep/discard and verify as controllable actions; racing / sequential verification baselines | Track S has forced keep/discard for forks only; verify off | §3.3 rounds B–C |
| Stop, revise, memory-switch actions | not planned | not planned (listed so they are not added silently) |
| Track S repeat with the pick | decided after the Track S outcome (R1-TRACKS-PICK-REPEAT-DEFER) | Paper C collects E-T0 data with the pick regardless |
| Track S on GPU nodes | role open (R1-BX-D10; M6's design revision) | E-INT |
| Second proposer (exam runner-up) in sequential evaluation | closed-loop check only in Paper B (R1-BX-D6-EXAM-RUNNER-UP) | E-T0 proposer-generalisation fold (extension) |
| Model-based rollout / MPC (comment §4.2 B2) | not in Paper B | N5, E-SIM (extension) |
| R-B as a multi-step arm | single-step optional ablation in Paper B | M3 (extension) |
| LLM self-control as a **sequential** controller (the proposer shown budget and history decides execute/skip/stop) | A4 is single-step in Paper B | an extension arm in SPT-6, with its call cost counted |
| Development-cost amortisation reporting | not in Paper B | §12 |

---

## 14. Core version and timeline (proposal; no date is committed)

**Core version (first submission; author position 5 Nov).**
- **Tiers:** E-SYN and two E-T0 nodes, with the pick as proposer.
- **Questions:** Q1 confirmatory (round B). Q3 confirmatory only if the go/no-go passes, as a two-part decision at δ; otherwise "not testable at this budget". Q2 and Q5 as secondaries. Q4 in-distribution only (E-d vs E-c in N6, with M1).
- **Methods:** N0–N4, N2b, N6, the reference rows, R0 and R1.
- **E-INT:** descriptive on 1 node (Paper B T1 logs plus ≤ 100 test campaigns).

**Extension (stated, not promised).** E-INT powered with in-tier training; E-HELD transfer; E-SIM and N5; N8 and SPT-7 online RL; R2; M2 and M3; round C; depth-2 forks; the proposer-generalisation fold; the sequential LLM self-control arm.

| Window | Work |
|---|---|
| Nov 2026 – 10 Jan 2027 | **Inside Paper B only:** revision W1 archive/exporter, Track S rev 8, W3/W4 if adopted. No Paper C runs |
| mid-Jan – Feb 2027 | Author rows (proposer, δ, core); E-INT allocation request (≈ 250 GPU-h); SPT-0 contract, seed registry, E-SYN suite, loader, review; SPT-1 pilot on both E-T0 nodes; T-C1–T-C3 started. Overlaps with Paper B's ICML review period |
| Mar 2027 | SPT-2/3 on E-T0 (≈ 120k calls per node); SPT-4 diagnostics; go/no-go for RL; E-INT node choice |
| Apr 2027 | SPT-5 training and selection; SPT-6 test on E-T0; E-INT descriptive test; M1. Overlaps with Paper B's rebuttal |
| May 2027 | Writing |
| Venue | The author's choice (for example NeurIPS 2027 if its deadline falls in mid-May — verify — or TMLR / ICLR 2028). Thesis writing is expected in summer 2027, so the extension is a follow-up, not a revision target |

---

## 15. Risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Too little action/state coverage | Offline RL over-estimates unseen actions | Logged ε-mixtures; numerical support targets (§6.1); behaviour-constrained methods; report "insufficient data" |
| Sparse, noisy terminal reward | Zero-advantage groups, unstable RL | Fork replication; near-threshold oversampling; heterogeneity-based go/no-go |
| A failed superiority test read as "RL adds nothing" | Over-claiming a null | Two-part decision with TOST at a pre-declared δ and a power check (§11.3) |
| Level-shift wins | Spurious non-myopic gains | Tuned-g myopic arm; matched-level guard (Q2); matched static (Q1) |
| Pick latency higher than assumed | Core version does not fit Mar–Apr | Costs in calls; L measured before sweep 2 and in SPT-1; the core shrinks test n or methods, by a pre-declared rule, before SPT-5 |
| Proposer non-reproducibility | Fork pairing fails | `cache_prompt: false`; exact A/A placebo; S0.1-style identity test per host |
| Fork restore inconsistency | Invalid causal contrasts | Track S arm-invariance tests 1–5 on every runner change |
| Strong simple baselines explain all gains | No L3 effect | A reportable result through the equivalence part; N4/N6 confirmatory comparators by design |
| Unequal tuning or interaction budgets | The most complex method wins by search | Declared budgets per method; matching in runs + calls + audits; costs reported |
| Pooling contexts | Wrong transition kernel | Environment context in the state; confirmatory training only on the pick's logs |
| Simulator bias | Gains on E-SIM that vanish on real loops | E-SIM only for training (extension); conclusions only from SPT-6 |
| Environments chosen to favour RL | Circular evidence | Declared selection criteria before outcomes; easy and hard tiers separate; strict null in E-SYN |
| Schedule against Paper B's rebuttal and the thesis | Paper C late | Core version only; extension deferred |

---

## 16. What Paper B must leave in place for Paper C

1. The transition contract (revision W1): archives of Track S roots, events and leaves, and of sweep run directories, with sha256 manifests and the offline exporter; the D.3 sidecar.
2. Track S's hooks and fork collector preserved at their pins.
3. The budget fields from worker runs (revision W2) in features and prompts, and derivable in every record.
4. The synthetic-world suite and budget-DP code (W3/W4) as reusable modules, if adopted.
5. Sweep-2, T1 and D.3 ledgers kept with their prompts and diffs (the history summaries are rebuilt from them).
6. The pick's measured latency and the Track G census costs.
7. No Paper B seed block re-used; the registry generated from code.

## 17. Open decisions and draft rows for the author

| # | Decision | Recommendation / status |
|---|---|---|
| P1 | Adopt this plan as the follow-up paper's scope (in principle) | yes, as a working plan; revisit after Paper B's submission |
| P2 | Round for confirmatory Q1/Q3 | round B (round A as a descriptive development stage) |
| P3 | E-INT in the core version | 1 node, descriptive; selection by declared census criteria |
| P4 | Offline RL in the core version | R0 (FQI-LightGBM) and R1 (IQL); R2 in the extension |
| P5 | Estimand for learned policies | the dev-selected artifact; training-seed spread descriptive |
| P6 | E-INT allocation request | ≈ 250 GPU-h, requested in January |
| P7 | Venue and target date | the author's choice after Paper B |
| P8 | Release the transition and fork dataset as a contribution | decide at SPT-0; it would need documentation and OPE ground truth from forks |
| P9 | A cheap interaction-rich real tier for training (e.g. CPU nodes with code-level diffs) | not in the core version; the first candidate for making Q3 powered where headroom is plausible |
| — | Proposer of record | **exam winner** (author position, 5 Nov) |
| — | Core version for the first submission | **yes** (author position, 5 Nov) |
| — | δ for Q3 (and Q1's negative) | **§11.3** (author position, 5 Nov) |

```
| R1-PAPERC-PROPOSER (date) | The follow-up paper's proposer of record is the exam winner (Track X pick, thinking off), as Paper B's main proposer (R1-MAIN-PROPOSER). All confirmatory collection and tests use it. Logs from other proposers (Track S's qwen2.5-coder:7b) are separate environment contexts, usable only for pre-training or auxiliary data with the context in the state. Costs are planned in proposer calls; hours use the pick's measured in-campaign latency. |
| R1-PAPERC-CORE (date) | The first submission of the follow-up paper is the core version of `proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md` (rev 2) §14: E-SYN and two E-T0 nodes; Q1 confirmatory in round B; Q3 confirmatory only after a passed go/no-go, as a two-part decision; Q2, Q4 (in-distribution, M1) and Q5 secondary; N0–N4, N2b, N6, R0, R1; E-INT descriptive on one node. Everything else is a stated extension. |
| R1-PAPERC-DELTA (date; before any Paper C data) | Equivalence rule for the follow-up paper. Q3 is decided by a one-sided superiority test and a TOST at margin δ, each at α = 0.025 (Holm across nodes). On E-T0, δ_n = max(0.002, 0.25·s̃_n) on the paired terminal raw-Y difference, with Paper B's frozen s̃_n; sensitivity 0.5·δ_n. On E-SYN, δ is 10 % of the DP-oracle-minus-best-myopic gap per world. TOST must have power ≥ 0.80 at a true difference of 0 at the planned n (whole-pipeline simulation from SPT-1); otherwise the equivalence part is declared untestable in advance. δ and n are never changed after a test outcome. Q1's negative is worded with the same rule. |
```
