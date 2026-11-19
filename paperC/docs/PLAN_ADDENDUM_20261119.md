# Paper C plan — addendum of 19 Nov 2026 (to revision 2 of 5 Nov and the addendum of 15 Nov)

**AI-assisted (Claude, chat session), written 19 Nov 2026 after the author's decisions of that day.** It amends `proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md` (rev 2, "the plan") and `PLAN_ADDENDUM_20261115.md` ("addendum 15 Nov"). Where they conflict, this addendum controls. The author rows are in `docs/r1/PLAN.md` §10, section "19 November 2026 — Paper C (author)". Real-node runs still need their own runbook, review and authorization (addendum 15 Nov §C).

Changes:
- **A.** Pre-declarations that the plan left open: the SPT-1 go/no-go statistics, the decision-relevance gate before SPT-2, the equivalence design, nodes and channels, and OPE support on real nodes.
- **B.** A fork-restore fidelity requirement for the SPT runner (B11) and a replay check before fork data are used.
- **C.** The estimand stated explicitly: running out of budget is termination, not censoring.
- **D.** Governance metrics reported per arm as secondary, descriptive guards.
- **E.** Positioning against current agent research, and the scope boundary: the memory-reset fork branch goes to a separate later paper, not into Paper C.
- **F.** The harness pin for B11 and three process items.

Evidence cited below comes from `reports/` on `paperc-build-20261115` at `cf045c39`. E-SYN results are engineering validations, not evidence about real loops.

---

## A. Pre-declarations

### A.1 SPT-1 go/no-go (plan §6)

The plan fixes the two statistics but not which fork contrast, whether epochs are pooled, the continuation policies or the floors. These are now fixed.

1. **Statistic 1** is the between-fork heterogeneity of the **continuation difference d**, not of the total fork difference q. It is computed per E-T0 node and **per epoch** (E1 and E2 separately), weighted by 1/p_select, with a cluster bootstrap over root instances.
2. **Continuation policies:** N1 (tuned static threshold) and N0, r = 2 continuations each. Budget-aware continuation policies (N3, N4) are not used.
3. **Statistic 1 passes** when, in at least one epoch, τ̂_d ≥ 0.5 δ_n and the 95 % lower bound of τ̂²_d is above 0.
4. **Statistic 2** is the cross-fitted N6 value per campaign (the Horvitz–Thompson sum of per-decision gains). It passes when it is ≥ δ_n and the lower bound of its primary (refit) interval is above 0. The fixed-decision interval is reported, not used.
5. **Decision:** if either statistic passes on either E-T0 node, multi-step RL is trained. Otherwise Q3 is reported as "not testable at this budget" (plan §6, unchanged).
6. q, pooled and per epoch, is descriptive only. As a sensitivity analysis, the report also states the decision at floors of 0.25 δ_n.

Why (`reports/FORK_VALIDATION_20261116.md`):
- q cannot separate the null world from the channel worlds: population τ²_q is 21.8 × 10⁻⁶ in strict_null and 23.4–1201 × 10⁻⁶ in the six channel worlds, because q contains the one-step value that a myopic rule already sees.
- d is zero under the null, but only when the continuation policy's later decisions do not depend on bookkeeping that differs between the arms (runs left, keeps so far, the incumbent's measurement). N1 and N0 meet this; N3 and N4 do not.
- Pooling the epochs adds the difference between epoch means to τ². In shared_error, τ²_d is almost entirely in E2.
- Bootstrap intervals are narrow (standard error to empirical SD 0.70–1.20), hence the lower-bound condition. With 40 roots, N6's lower bound never exceeded 0 in any world.

Why these floors: δ_n is the gain Paper B already treats as meaningful (plan §11.3). A spread of 0.5 δ_n in single-decision effects means a real share of decisions matter at the scale of δ_n. If the sum of all one-step improvements stays below δ_n, an RL policy is unlikely to gain δ_n.

Expected consequence: at SPT-1's size, the go/no-go will most likely fail unless a real channel is about as strong as E-SYN's interaction (τ_d = 0.49 σ) or keep_feedback (0.78 σ) worlds. That is the intended conservatism.

### A.2 Decision-relevance gate before SPT-2 (addendum 15 Nov §B.3)

- **Band** b = 0.5 σ_node, the band Track S STOP 4 used; shares at 0.25 and 1.0 σ_node are reported as well.
- **E1:** |V\* − g| is computed against the **declared real run price** g, not against N1's tuned threshold. The share of eligible decisions inside the band must have a point estimate ≥ 10 % and a 95 % cluster-interval lower bound ≥ 5 %.
- **E2:** |m̂ − h| with the same share condition, **and** a stakes floor: a median kept increment ≥ 0.5 σ_d or a decision regret ≥ 0.1 σ_d.
- The gate is applied per node and per epoch. An epoch that fails is not run in round A on that node; the other epoch may still run.
- If the pilot is too small for the interval, the result is "not assessed", not "no decision-relevant states" (P5 keeps the two apart).
- The gate is a necessary condition only. Whether sequential control has value is decided by A.1.

Why: Track S STOP 4 had no E1 decision within ±0.5 σ_node (V\* − g was 2.6–4.1 σ_node). On the OpenML nodes the census found E2 near-margin shares of 58–83 % but median kept increments of only 0.08–0.18 σ_d: a share without stakes would let such nodes pass (`reports/HEADROOM_CENSUS_20261116.md` §5). The stakes floor needs census measurement (a) (A.4).

### A.3 Equivalence design (plan §11.3 and R1-PAPERC-DELTA)

- **δ is unchanged:** δ_n on E-T0; 10 % of the DP-minus-best-myopic gap on E-SYN.
- **E-SYN:** the test-block n is the smallest n at which a pre-declared whole-pipeline simulation gives zero-effect TOST power ≥ 0.80. E-SYN campaigns cost milliseconds of CPU.
- **E-T0:** the affordable n is set from SPT-1's σ_D and the §12 cost model. If TOST power at that n is below 0.80, equivalence for that node is declared untestable in advance (plan §11.3, unchanged). Neither δ nor n changes after an outcome.
- **Variance reduction, declared now:** common random numbers (both arms use the same proposer and worker seed streams); K fresh audit seeds per terminal incumbent, with K as in Paper B's tier rule (K = 10 on the CPU nodes of T0, K = 6 on T1; R1-BX-D3, R1-BX-PROPOSED-CONFIRM); linear regression adjustment on the start configuration's audited metric.
- Q1's negative is worded with the same rule.

Why: P9 found 0 TOST rejections in 12 repetitions at 512 pairs per node on short-budget E-SYN (95 % interval 0.00–0.26), against the required 0.80 (`reports/POWER_VALIDATION_20261117.md`). For planning, TOST at a true difference of 0, α = 0.025 per side and power 0.80 needs about n ≈ 10.5 (σ_D/δ)² pairs; δ/σ_D = 0.125 gives about 670 pairs per comparison and node. Since δ_n is set from per-edit noise s̃_n and σ_D is campaign-level, equivalence on real nodes will often be declared untestable. The manuscript prepares the Q3 wording for that case.

### A.4 Nodes and channels (R1-PAPERC-CORE follows the measurements)

- **Measure first.** The two CPU measurements of `reports/HEADROOM_CENSUS_20261116.md` §6.2 are approved, on a Paper C seed block:
  - **(a)** fresh-seed audits of sweep-1 keeps and final incumbents on digits_mlp, tabular_mlp, openml_credit_approval and openml_ionosphere, giving measured false-keep and missed-keep rates and a measured winner's curse. The audit runs are shared with Paper B's B.2 where they coincide;
  - **(b)** a small run with a guarded first acceptance (trial 1 compared with the start configuration) on digits_mlp and tabular_mlp, removing the trial-1 artefact before E2 is judged.
- **Provisional E-T0 nodes:** digits_mlp and tabular_mlp. A node whose median kept increment after removing the trial-1 artefact (measurement b) is below 0.5 σ_d is descriptive only in round A.
- **Core channels:** incumbent interaction, and acceptance under noise (E2) with verify and re-audit. E1 enters only with a per-proposal forecaster, a declared real price and 0.3 ≤ price/V\* ≤ 3.
- openml_credit_approval or openml_ionosphere serves as a descriptive control.
- A T1 census on HoreKa / HTCondor is scheduled in the GPU-tier plan.
- After (a) and (b), R1-PAPERC-CORE is written with the chosen nodes and channels (R-C3). If neither node meets the stakes floor, Paper C's core is E-SYN plus descriptive E-T0, and the contribution is the map of when sequential control pays (R1-PAPERC-REFRAME).

### A.5 OPE clusters and support on real nodes (plan §6.1)

- **State clusters (8):** epoch (E1, E2) × forecast region (E1: V\* ≥ the declared price g; E2: m̂ > h) × whether more than half of the run budget remains. This is the structure P7 validated on E-SYN, with the region boundaries set by the declared prices.
- **Support targets (unchanged):** at least 30 training observations per action per cluster; an FQE-screen effective sample size of at least 200 decisions per candidate. A shortfall is reported as "insufficient data".
- **Statistical cluster unit:** the campaign instance (node, instance seed, start configuration), as in P5, P6 and P9.
- **Behaviour mixture:** the plan's 15 components (5 base policies × plain, ε = 0.1, ε = 0.25); ε seeds are logged.
- If the cost model after SPT-1 shows that SPT-2 does not fit, E1 or a node is cut first; the support targets are not relaxed.

Rough scale, worst case: if support came only from ε = 0.1, the rarer action would be about 5 % of decisions, and 30 occurrences in each of 8 clusters would need about 4,800 eligible decisions, i.e. about 240–340 SPT-2 campaigns per node at 14–20 eligible decisions per campaign. The five base policies differ, so in many clusters both actions occur anyway. This is an estimate to be replaced after SPT-1.

Why: P7 validated these rules on E-SYN; the deliberately unsupported case returned "insufficient data" for N0, whose execute actions had zero propensity in 124 held-out rows (`reports/OPE_VALIDATION_20261117.md`). Real-node clusters were left open there.

---

## B. Fork-restore fidelity (B11, SPT-0; checked before SPT-3 data are used)

A fork difference is a counterfactual contrast only if the restored state continues the way the live run would have. Pakhomov and Nijkamp ([arXiv:2611.05650](https://arxiv.org/abs/2611.05650)) report that snapshots restored into seeded processes diverged from the live run until the position of the random stream was restored as well, and that matching state hashes did not guarantee matching continuations. Paper B's PLAN §11 (relation to Paper A) already names restore audits; this section makes them a requirement for Paper C's forks.

1. **Snapshot content.** A fork snapshot holds the position of every random stream that later draws depend on, in addition to the workspace, ledger and proposer memory: proposer sampling seeds or call counters, worker training seeds, the behaviour policy's ε stream, and the audit-seed cursor. B11's runbook lists the streams that exist in the pinned harness.
2. **Replay check.** At a declared sample of fork points per node, the state is restored and the logged action is re-run under the logged continuation policy. The continuation is compared with the live run: the same proposals (edit hashes), the same keep/discard decisions, and metric values equal within a declared tolerance (bitwise where the computation is deterministic; a declared tolerance where it is not). The match rate is reported per node.
3. **Gate.** A node's SPT-3 fork data are used only after its match rate meets the threshold that B11's runbook declares. This extends SPT-1's A/A identity check from whole campaigns to restored fork points.
4. A low match rate is reported, not hidden: fork variance then includes replay noise, and SPT-1's fork-repeat-vs-between-fork variance comparison is read with that in mind.

## C. Estimand and censoring (plan §3.1)

- Y is the audited final incumbent of a campaign that runs within its run budget W and call cap N. Exhausting W or N is **termination**: it is part of the outcome, not censoring. Policies already receive time-to-go in both resources (plan §3.1). In the terms of Pardo et al. (ICML 2018), these limits belong to the task; they are not a device that only truncates experience.
- Truncation keeps the plan's rules (infrastructure failure, protocol STOP, parse failure beyond retry, host loss; never treated as complete; rates per arm; an imbalance beyond the declared level is a STOP). In addition, truncation rates are reported per state cluster (A.5), so that a learner trained on completed episodes can be checked for a systematic gap.

## D. Governance metrics as secondary, descriptive guards

Per arm and node, the report gives, with intervals: the rate of failed_invalid trials by failure category, the repeated-bad-proposal rate, and the number of proposals the control plane rejected for scope. They sit beside Q1 and Q3 as descriptive guards. They belong to neither confirmatory family and carry no claim of their own; a difference between arms beyond a level declared before SPT-6 is flagged in the report. The aim is to show whether a sequential policy changes how often the proposer produces invalid or out-of-scope edits, which the governed harness catches either way.

## E. Positioning and scope

### E.1 Positioning (adds to plan §3.6)

- The contribution is framed as a measured map of when sequential control pays in a governed loop, and which method is enough. In the terms of current agent research: fork contrasts are credit assignment with executed counterfactuals; verify, re-audit and final selection are active information acquisition; re-auditing the incumbent tests whether stored experience is still valid.
- Claims stay within the evidence. On short-budget E-SYN, N6 recovers 88.6 % of the N1-to-DP gap, but against the best short-horizon static rule its interval spans zero, and R0 and R1 are below zero (`reports/LEARNER_VALIDATION_20261117.md`). Transfer to code agents in general is discussion, not a result.
- **Related work to add** (each opened and checked on 19 Nov 2026):
  - TRACE, EMNLP 2026 ([anthology](https://aclanthology.org/2026.emnlp-main.1610/)): rollout-budget allocation over prompts and intermediate prefixes in agentic RL. Paper C does not claim adaptive fork allocation as new.
  - Counterfactual Rollout Replay ([arXiv:2609.33875](https://arxiv.org/abs/2609.33875)): restored states and branch returns as step-level credit for software-engineering agents.
  - Calibration Is Not Control ([arXiv:2606.21399](https://arxiv.org/abs/2606.21399)): supervising intervention utility rather than failure risk. It is the closest relative of N6; Paper C differs in audited outcomes, an exact DP oracle on E-SYN, and acceptance decisions owned by a governed control plane.
  - Pakhomov and Nijkamp ([arXiv:2611.05650](https://arxiv.org/abs/2611.05650)): executed counterfactuals and restoration fidelity (§B).
  - Pardo et al., Time Limits in Reinforcement Learning, ICML 2018 ([PMLR](https://proceedings.mlr.press/v80/pardo18a.html)) (§C).

### E.2 Scope (author, 19 Nov)

- The review of the five research directions changes nothing in Paper C's experiments: no channel, arm or phase is added.
- The memory-reset fork branch ("A2": how much future value one context reset loses) is **not** a Paper C extension. It moves to the separate later paper, whose main axis is when to re-verify evidence after resuming work across sessions. Paper C's fork, audit and OPE code is that paper's starting point.
- Also outside Paper C: cross-interface transfer of the controller, a model × memory factorial, multi-agent settings, a staleness channel, and learning from trajectories with scope violations.

## F. Pins and process items

- **B11 harness pin.** The SPT runner ports the Track S hooks against the harness pin recorded in Paper B sweep 2's launch record (R1-SWEEP2-AUTH), so that Paper C's logs are comparable with the main proposer's sweep-2 runs. B11's runbook names that commit; any other pin needs its own row.
- **Runbook phase P10** (BUILD_LIST B12, single-teacher distillation on E-SYN) continues. It is CPU-only and depends on none of the items above. Open item P10 of addendum 15 Nov §D (M4a in the core version) stays open.
- **Theory note** on `codex/paperc-theory-20261117` (T-C1, T-C2, rollout cases): an independent review, then a merge into the build line, before the manuscript cites it.
- After measurements (a) and (b), R1-PAPERC-CORE is drafted for the author (A.4).
