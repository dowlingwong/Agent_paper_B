# Paper C plan — addendum of 19 Nov 2026 (to revision 2 of 5 Nov and the addendum of 15 Nov)

**AI-assisted (Claude, chat session), written 19 Nov 2026 after the author's decisions of that day; revised the same night after independent review round 1 (`reviews/PLAN_ADDENDUM_20261119_REVIEW_20261119.md`).** It amends `proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md` (rev 2, "the plan") and `PLAN_ADDENDUM_20261115.md` ("addendum 15 Nov"). Where they conflict, this addendum controls. The author rows are in `docs/r1/PLAN.md` §10, section "19 November 2026 — Paper C (author)". Real-node runs still need their own runbook, review and authorization (addendum 15 Nov §C).

**Sources of the decisions.** On 19 Nov the author adopted every recommendation of the decision memo "Paper C 待定决策：说明与推荐" (a Claude Docs document, private to the author: https://claude.ai/artifact/YZZ5mxAiWHqSxqMGyf5fyf). The author also adopted the plan, set out in the chat the same day, for carrying the review of five research directions into Paper C. Two kinds of text are marked below:
- **[correction]**: a value in the memo that was wrong and is corrected here; it waits for the author's confirmation;
- **[recorder]**: an operational reading, or a detail the memo did not state, written by the recorder so that the pre-declaration can be carried out.

Each marked item is listed in §G for the author to confirm or change.

Changes:
- **A.** Pre-declarations that the plan left open: definitions, the SPT-1 go/no-go statistics, the decision-relevance gate before SPT-2, the equivalence design, nodes and channels, and OPE support on real nodes.
- **B.** A fork-restore fidelity requirement for the SPT runner (B11): an A/A replay at fork points before fork data are used.
- **C.** The estimand stated explicitly: running out of budget is termination, not censoring.
- **D.** Governance metrics reported per arm as secondary, descriptive guards.
- **E.** Positioning against current agent research, and the scope boundary: the memory-reset fork branch goes to a separate later paper, not into Paper C.
- **F.** The harness pin for B11 and process items.
- **G.** Open points for the author.

Evidence cited below comes from `reports/` on `paperc-build-20261115` at `cf045c39`. E-SYN results are engineering validations, not evidence about real loops.

Numbering:
- "runbook phase P5" and the like are build phases (`BUILD_RUNBOOK.md`);
- "plan item P1–P9" are plan §17's decisions;
- "open item P10" is addendum 15 Nov §D.

---

## A. Pre-declarations

### A.0 Definitions (frozen in the SPT-1 pre-declaration unless stated)

- **σ_node and σ_d** (census §1, `reports/HEADROOM_CENSUS_20261116.md`).
  - σ_node is Track S's comparison-noise unit: the median, over a node's five C1 edits, of the paired standard deviation.
  - σ_d is Paper B's sweep unit: the median paired standard deviation over the node's *material* C1 edits.
  - On tabular_mlp, σ_d = 1.87 σ_node; on digits_mlp the two agree.
  - Units in this addendum: bands near a threshold are in σ_node, stakes are in σ_d, and δ_n is in raw units of Y (plan §11.3).
- **g** is the declared real price of one worker run, in σ_node. The author declares it in the SPT-1 pre-declaration. Track S used g = 0.1 σ_node (addendum 15 Nov §B.3). [recorder: the value is open, §G]
- **V\*** is the deployed per-proposal forecaster's predicted value of executing a proposal. "price/V\*" uses the median of V\* over eligible E1 decisions, as in census §3.1.
- **h** is the keep threshold of the declared E2 keep rule on m̂, declared in the SPT-1 pre-declaration. The cluster structure that runbook phase P7 validated corresponds to h = 0 (keep iff m̂ > 0, as in Track S S0.5). [recorder: the value is open, §G]
- **Decision regret** is C1's `decision_regret` field (part of the D28 composite; census §1): the median over the node's edits, in σ_d.

### A.1 SPT-1 go/no-go (plan §6)

The plan fixes the two statistics but leaves four things open: which fork contrast, whether epochs are pooled, the continuation policies, and the floors. They are fixed here.

1. **Statistic 1** is the between-fork heterogeneity of the **continuation difference d**, not of the total fork difference q. It is computed per E-T0 node and **per epoch** (E1 and E2 separately), weighted by 1/p_select, with a cluster bootstrap over root instances.
2. **Continuation policies:** N1 (tuned static threshold) and N0, with r = 2 continuations each. Budget-aware continuation policies (N3, N4) are not used. N1 is tuned on development instances, disjoint from SPT-1's go/no-go forks (plan §11.1).
3. **Statistic 1 passes** when, in at least one epoch, τ̂_d ≥ 0.5 δ_n and the 95 % lower bound of τ̂²_d is above 0.
4. **Statistic 2** is the cross-fitted N6 value per campaign: the Horvitz–Thompson sum of per-decision gains over all eligible decisions of a campaign, both epochs together. It passes when it is ≥ δ_n and the lower bound of its primary (refit) interval is above 0. The fixed-decision interval is reported, not used.
5. **Decision:** if either statistic passes on either E-T0 node, multi-step RL is trained. Otherwise Q3 is reported as "not testable at this budget" (plan §6, unchanged).
6. q, pooled and per epoch, is descriptive only. As a sensitivity analysis, the report also states the decision with statistic 1's floor at 0.25 δ_n. [recorder: the memo gives one sensitivity value; it is read here as statistic 1's floor, §G]
7. **Multiplicity, stated plainly.**
   - Up to six checks can open the gate: 2 nodes × (statistic 1 in E1, statistic 1 in E2, and statistic 2). There is no multiplicity adjustment.
   - Each check is strict (a magnitude floor plus a lower bound), but their union is lenient.
   - This is acceptable because the gate only decides whether RL is trained. Q3 is tested on fresh test blocks at its own α.
   - A passed go/no-go is not reported as evidence of headroom.
8. Plan §9.1 gate 1 ("τ̂² above its floor") reads τ̂² as statistic 1 of this section.

Why (`reports/FORK_VALIDATION_20261116.md`):
- **q cannot separate the null world from the channel worlds.** Population τ²_q is 21.8 × 10⁻⁶ in strict_null and 23.4–1201 × 10⁻⁶ in the six channel worlds. The reason is that q contains the one-step value that a myopic rule already sees.
- **d is zero under the null, with a condition.** The continuation policy's later decisions must not depend on bookkeeping that differs between the arms (runs left, keeps so far, the incumbent's measurement). N1 and N0 meet this; N3 and N4 do not.
- **Pooling the epochs inflates τ².** It adds the difference between the epoch means. In shared_error, τ²_d is almost entirely in E2.
- **Bootstrap intervals can be up to 30 % too narrow** (bootstrap standard error to empirical SD 0.70–1.20). A lower bound alone is therefore not relied on: the magnitude floor carries the decision, and the lower bound only screens out noise-level estimates.
- **N6 at 40 roots:** its per-decision primary lower bound never exceeded 0 in any world. The per-campaign value's lower bound was not tabulated.

Why these floors:
- δ_n is the gain Paper B already treats as meaningful (plan §11.3).
- A spread of 0.5 δ_n in single-decision effects means a real share of decisions matter at the scale of δ_n.
- The N6 floor at δ_n is a heuristic, not a theorem. In E-SYN's budget world one exact rollout update captures 59 % of the static-to-optimal gap (theory note on `codex/paperc-theory-20261117`, not yet reviewed), so the optimum can gain more than one improvement step.

Size and cost:
- With r = 2 under two continuation policies, each fork arm has four continuations. Plan §12's SPT-1 row (60 forks × 2 arms × 20 calls) assumed one.
- The SPT-1 pre-declaration therefore recomputes the cost. At 60 forks per node, the fork part becomes 9.6k proposer calls, and the SPT-1 total about 15.6k instead of 8.4k.
- The E-SYN detection rates were measured with a few hundred forks per 40-root collection (381 on average in strict_null). At 60 forks per node, split across two epochs, they are optimistic.

Expected consequence: SPT-1 will most likely return no-go, unless a real channel is about as strong as E-SYN's interaction world (τ_d = 0.49 σ) or keep_feedback world (0.78 σ).

### A.2 Decision-relevance gate before SPT-2 (addendum 15 Nov §B.3)

- **Band:** b = 0.5 σ_node, the band Track S STOP 4 used. Shares at 0.25 and 1.0 σ_node are reported as well.
- **E1:** |V\* − g| is computed against the declared real run price g (A.0), not against N1's tuned threshold. The share of eligible decisions inside the band must have a point estimate ≥ 10 % and a 95 % cluster-interval lower bound ≥ 5 %.
- **E2:** |m̂ − h|, with the same share condition **and** a stakes floor: a median kept increment ≥ 0.5 σ_d **or** a decision regret ≥ 0.1 σ_d.
- **Data.** The gate is computed on SPT-1's pilot campaigns, run with the pick. Kept increments are measured with measurement (a)'s fresh-seed audit procedure (A.4). [recorder, §G]
- **Consequence.** The gate is applied per node and per epoch. An epoch that fails on a node is not controlled there in SPT-2 and SPT-3: its actions follow the frozen tier rule, no forks are drawn at that epoch, and it enters no confirmatory comparison on that node. The other epoch may still run. [recorder: the memo said "not run in round A", but plan §3.3's round A controls only E1, so the consequence is restated per epoch, §G]
- **Too small a pilot:** if the interval is too wide, the result is "not assessed", not "no decision-relevant states" (runbook phase P5 keeps the two apart).
- **Necessary condition only.** Whether sequential control has value is decided by A.1.

Why:
- In Track S STOP 4, no E1 decision lay within ±0.5 σ_node of the price (V\* − g was 2.6–4.1 σ_node).
- On the OpenML nodes other than climate, the census found E2 near-margin shares of 58–80 % but median kept increments of only 0.08–0.18 σ_d. A share condition without stakes would let such nodes pass (census §5).

### A.3 Equivalence design (plan §11.3 and R1-PAPERC-DELTA)

- **δ is unchanged:** δ_n on E-T0; 10 % of the DP-minus-best-myopic gap on E-SYN.
- **E-SYN:** the test-block n is the smallest n at which a pre-declared whole-pipeline simulation gives zero-effect TOST power ≥ 0.80. E-SYN campaigns cost milliseconds of CPU.
- **E-T0:** the affordable n is set from SPT-1's σ_D and the §12 cost model, and TOST power at that n is computed by the whole-pipeline simulation that R1-PAPERC-DELTA requires. If power is below 0.80, equivalence for that node is declared untestable in advance. Neither δ nor n changes after an outcome.
- **Variance reduction, declared now:**
  - **Common random numbers:** both arms use the same proposer and worker seed streams. The pairing gain is measured, not assumed (plan §10).
  - **K fresh audit seeds per terminal incumbent,** following Paper B's tier rule:
    - on the CPU nodes of T0, K = 10 (R1-BX-PROPOSED-CONFIRM);
    - on T1, K = 10 until R1-BX-D3's subsampling check has passed and been recorded in a PLAN row, then K = 6.
    - [correction: the memo said "K = 6, as in Paper B", but Paper B's rule for T0 is K = 10. Plan §12's E-INT cost, which assumed K = 5, is recomputed accordingly]
  - **Regression adjustment** on the start configuration's audited metric. The estimate is the intercept of an OLS fit of D_i on centred y_start, and the same estimator is used in the power simulation. Within a pair, y_start is shared, so the adjustment helps only through effect heterogeneity. [recorder: the estimator, §G]
- **Q1's negative** is worded with the same rule.

Why:
- **The current design is underpowered.** Runbook phase P9 found 0 TOST rejections in 12 repetitions at 512 pairs per node on short-budget E-SYN (95 % interval 0.00–0.26), against the required 0.80 (`reports/POWER_VALIDATION_20261117.md`).
- **Planning formula (not the decision rule).** TOST at a true difference of 0, with α = 0.025 per side and power 0.80, needs about n ≈ 10.5 (σ_D/δ)² pairs. At δ/σ_D = 0.125 that is about 670 pairs per comparison and node.
- **Consequence for real nodes.** δ_n is set from per-edit noise s̃_n, while σ_D is campaign-level, so equivalence on real nodes will often be declared untestable. The manuscript prepares the Q3 wording for that case.

### A.4 Nodes and channels (R1-PAPERC-CORE follows the measurements)

- **Measure first.** The two CPU measurements of census §6.2 are approved. Both are real-node runs, each with its own runbook, review and authorization.
  - **(a)** Fresh-seed audits of sweep-1 keeps and final incumbents on digits_mlp, tabular_mlp, openml_credit_approval and openml_ionosphere. They give measured false-keep and missed-keep rates and a measured winner's curse.
    - They use Paper C audit seeds.
    - Where Paper B's B.2 label-seed audits (7001–7005) of the same keeps exist, they may be reused as additional, labelled data.
    - B.2's evaluation seeds 7006–7010 are not used (R1-SWEEP1-CLASSIFY).
  - **(b)** A small run with a guarded first acceptance (trial 1 compared with the start configuration) on digits_mlp and tabular_mlp. It removes the trial-1 artefact before E2 is judged. [recorder: the proposer for (b) is open; proposal: the pick, R1-PAPERC-PROPOSER, §G]
- **Provisional E-T0 nodes:** digits_mlp and tabular_mlp. A node whose median kept increment, after removing the trial-1 artefact (measurement b), is below 0.5 σ_d gets no confirmatory Q1/Q3 test; its runs are reported descriptively.
  - [recorder: this restates the memo's "descriptive only in round A".]
  - [recorder: this screen uses only the kept-increment criterion, as the memo did, while A.2 also accepts decision regret. How a node that passes A.2 on regret alone is treated is left to R1-PAPERC-CORE, §G]
- **Core channels:** incumbent interaction, and acceptance under noise (E2) with verify and re-audit.
  - E1 enters only with a per-proposal forecaster, a declared real price, and 0.3 ≤ price/V\* ≤ 3.
  - Whether forks and OPE cover verify, re-audit and final selection is decided in R1-PAPERC-CORE.
- **Descriptive control:** openml_credit_approval or openml_ionosphere.
- **GPU tier:** a T1 census on HoreKa / HTCondor is scheduled in the GPU-tier plan.
- **R1-PAPERC-CORE** is written after (a) and (b), with the chosen nodes and channels (R-C3). Nothing about the core is pre-decided here. If neither node meets the stakes floor, R1-PAPERC-CORE chooses among the census options (census §6).

### A.5 OPE clusters and support on real nodes (plan §6.1)

- **State clusters:** epoch (E1, E2) × forecast region (E1: V\* ≥ g; E2: m̂ > h; see A.0) × whether more than half of the run budget remains.
  - That is 8 clusters when both epochs are controlled, and 4 (E2 only) when E1 is not in the core.
  - A cluster with no eligible decisions is reported as empty, not as a shortfall. [recorder: the empty-cluster rule, §G]
- **Support targets (unchanged):** at least 30 training observations per action per cluster, and an FQE-screen effective sample size of at least 200 decisions per candidate. A shortfall is reported as "insufficient data".
- **Statistical cluster unit:** the campaign instance (node, instance seed, start configuration), as in runbook phases P5, P6 and P9.
- **Behaviour mixture:** the plan's 15 components (5 base policies × plain, ε = 0.1, ε = 0.25). ε seeds are logged.
- **If SPT-2 does not fit** the cost model after SPT-1, E1 or a node is cut first. The support targets are not relaxed.

Rough scale, worst case:
- Suppose support came only from ε = 0.1. The rarer action would then be about 5 % of decisions.
- 30 occurrences in each of 8 equally occupied clusters would need about 4,800 eligible decisions. At 14–20 eligible decisions per campaign, that is about 240–340 SPT-2 campaigns per node.
- The smallest cluster governs, so unequal occupancy needs more. On the other hand, the five base policies differ, so in many clusters both actions occur anyway.
- This estimate is replaced after SPT-1.

Why: runbook phase P7 validated these rules on E-SYN. In the deliberately unsupported case it returned "insufficient data" for N0, whose execute actions had zero propensity in 124 held-out rows (`reports/OPE_VALIDATION_20261117.md`). Real-node clusters were left open there.

---

## B. Fork-restore fidelity (B11, SPT-0; checked before SPT-1's go/no-go is read)

A fork difference is a counterfactual contrast only if a restored state continues the way the live run would have.
- Pakhomov and Nijkamp ([arXiv:2611.05650](https://arxiv.org/abs/2611.05650)) report that snapshots restored into seeded processes diverged from the live run until the position of the random stream was restored as well. Matching state hashes did not guarantee matching continuations.
- Paper B's PLAN §11 (relation to Paper A) already names restore audits. This section makes them a requirement for Paper C's forks.

1. **Snapshot content.** A fork snapshot holds the workspace, the ledger, the proposer memory, and the position of every random stream that later draws depend on: proposer sampling seeds or call counters, worker training seeds, the behaviour policy's ε stream, and the audit-seed cursor. B11's runbook lists the streams that exist in the pinned harness.
2. **Both arms start from the restored snapshot.** No arm continues in the live process.
3. **A/A replay at fork points** (plan §4.2's A/A check, applied at restored states). At a declared sample of fork points per node:
   - restore the snapshot;
   - take the root's logged action;
   - continue under the root's own behaviour component, with its logged ε stream;
   - compare the result with the root's live continuation through termination.
4. **Match.** A replay matches when every step agrees: edit hash, action, keep decision, and metric equal within a declared tolerance (bitwise where the computation is deterministic). The step where a replay first diverges is reported, and the match rate is reported per node.
5. **When and threshold.** The sample size, tolerance and match-rate threshold are declared in B11's runbook before the check runs. The check runs in SPT-0/SPT-1, before SPT-1's go/no-go is read.
6. **Below the threshold:** STOP for the author. That node's fork data are not used for τ̂², N6 or OPE until the author decides. Whether SPT-1's go/no-go on such a node is then "not assessed" is an open point (§G).
7. **Optional and follow-on.**
   - B11's runbook may add a separate replay of recorded fork leaves.
   - A low but accepted match rate means fork variance includes replay noise. SPT-1's fork-repeat-vs-between-fork variance comparison is read with that in mind.

## C. Estimand and censoring (plan §3.1)

- **Budget exhaustion is termination.** Y is the audited final incumbent of a campaign that runs within its run budget W and call cap N. Exhausting W or N is part of the outcome, not censoring.
  - Policies already receive time-to-go in both resources (plan §3.1).
  - In the terms of Pardo et al. (ICML 2018), these limits belong to the task; they are not a device that only truncates experience.
- **Truncation keeps the plan's rules:** infrastructure failure, protocol STOP and host loss; truncated episodes are never treated as complete; rates are reported per arm; an imbalance beyond the declared level is a STOP.
- **Parse failures.** B11's runbook states how the pinned harness handles them. Where they are charged as invalid trials against the call budget, as in Paper B's exam (R1-EXAM-B1-TRUNCATION-INVALID), they are in-episode outcomes, not truncation.
- **Assumption.** Dropping truncated episodes assumes that truncation does not depend on arm or outcome. The per-arm truncation rates, and truncation rates per state cluster (A.5), are diagnostics for that assumption, not a guarantee. [recorder: the per-cluster report, §G]

## D. Governance metrics as secondary, descriptive guards

Per arm and node, the report gives, with intervals:
- the rate of failed_invalid trials, by failure category;
- the repeated-bad-proposal rate;
- the number of proposals the control plane rejected for scope.

These sit beside Q1 and Q3 as descriptive guards. They belong to neither confirmatory family and carry no claim of their own. A difference between arms beyond a level declared before SPT-6 is flagged in the report.

The aim is to show whether a sequential policy changes how often the proposer produces invalid or out-of-scope edits. The governed harness catches such edits either way.

## E. Positioning and scope

### E.1 Positioning (adds to plan §3.6)

- **The contribution** is framed as a measured map of when sequential control pays in a governed loop, and which method is enough. In the terms of current agent research:
  - fork contrasts are credit assignment with executed counterfactuals;
  - verify, re-audit and final selection are active information acquisition;
  - re-auditing the incumbent tests whether stored experience is still valid.
- **Claims stay within the evidence.** On short-budget E-SYN, N6 recovers 88.6 % of the N1-to-DP gap. Against the best short-horizon static rule, however, its interval spans zero, and R0 and R1 are below zero (`reports/LEARNER_VALIDATION_20261117.md`). Transfer to code agents in general is discussion, not a result.
- **Related work to add** (each opened and checked on 19 Nov 2026):
  - TRACE, EMNLP 2026 ([anthology](https://aclanthology.org/2026.emnlp-main.1610/)): rollout-budget allocation over prompts and intermediate prefixes in agentic RL. Paper C does not claim adaptive fork allocation as new.
  - Counterfactual Rollout Replay ([arXiv:2609.33875](https://arxiv.org/abs/2609.33875)): restored states and branch returns as step-level credit for software-engineering agents.
  - Calibration Is Not Control ([arXiv:2606.21399](https://arxiv.org/abs/2606.21399)): supervising intervention utility rather than failure risk. It is the closest relative of N6. Paper C differs in three ways: audited outcomes, an exact DP oracle on E-SYN, and acceptance decisions owned by a governed control plane.
  - Pakhomov and Nijkamp ([arXiv:2611.05650](https://arxiv.org/abs/2611.05650)): executed counterfactuals and restoration fidelity (§B).
  - Pardo et al., Time Limits in Reinforcement Learning, ICML 2018 ([PMLR](https://proceedings.mlr.press/v80/pardo18a.html)): the estimand statement (§C).

### E.2 Scope (author, 19 Nov)

- **No new experiments.** The review of the five research directions adds no channel, arm or phase to Paper C.
- **The memory-reset fork branch moves out.** This is item A2 of that review (unrelated to A2-U): how much future value one context reset loses. It is **not** a Paper C extension.
  - It moves to the separate later paper, called "Paper D" here as a working name. That paper's main axis is when to re-verify evidence after resuming work across sessions, and Paper C's fork, audit and OPE code is its starting point.
  - The review itself is the Claude Docs document "五个研究方向与 Paper B / C：贴合度、可能性与建议" (19 Nov, private to the author: https://claude.ai/artifact/HsjyhZ9hpJuysTsVHrcm47).
- **Also outside Paper C** (author, 19 Nov):
  - cross-interface transfer of the controller;
  - a model × memory factorial;
  - multi-agent settings;
  - a staleness channel (information that loses value over time; different from re-auditing the incumbent, which is core);
  - learning from trajectories with scope violations.

## F. Pins and process items

- **B11 harness pin.** The SPT runner ports the Track S hooks against the harness pin recorded in Paper B sweep 2's launch record (R1-SWEEP2-AUTH, on `main`). Paper C's logs are then comparable with the main proposer's sweep-2 runs.
  - Sweep 2 had not launched on 19 Nov. B11's runbook waits for the launch record and names that commit.
  - Any other pin needs its own row.
- **Runbook phase P10** (BUILD_LIST B12, single-teacher distillation on E-SYN) continues (memo item 6). It is CPU-only and depends on none of the items above. Open item P10 of addendum 15 Nov §D (M4a in the core version) stays open.
- **Theory note** on `codex/paperc-theory-20261117` (T-C1, T-C2 and the rollout cases): an independent review, then a merge into the build line, before the manuscript cites it (memo item 7).
- **Merging.** `main`'s PLAN has no R1-PAPERC rows yet: the 15 Nov and 19 Nov Paper C sections exist only on the Paper C line. Before this line is merged, both sections are rebased into `main`'s §10 in date order, so that cross-references such as R1-SWEEP2-AUTH resolve.
- **R1-PAPERC-CORE** is drafted for the author after measurements (a) and (b) (A.4).

## G. Open points for the author

Each item is the recorder's reading or proposal. The default holds until the author changes it.

| # | Point | Default written above |
|---|---|---|
| G1 | Consequence of a failed relevance gate (A.2), and of a node below the stakes floor (A.4) | failed epoch: not controlled in SPT-2/SPT-3 on that node, no forks, no confirmatory comparison. Node below the floor: no confirmatory Q1/Q3, descriptive only |
| G2 | Data for the relevance gate (A.2) | SPT-1 pilot campaigns with the pick; kept increments by measurement (a)'s audit procedure |
| G3 | Node screen (A.4) uses kept increment only, while A.2 also accepts decision regret | kept increment only; a node that passes A.2 on regret alone is settled in R1-PAPERC-CORE. Recommendation: accept either criterion in both places |
| G4 | Q3's node scope if the go/no-go passes on one node only | not stated. Recommendation: test Q3 only on nodes where the go/no-go passed, with Holm across those nodes |
| G5 | Sensitivity floor (A.1 item 6) | statistic 1 at 0.25 δ_n; statistic 2 unchanged |
| G6 | Continuation policies in SPT-3 | not stated. Recommendation: the same N1 and N0 with r = 2 (plan §6's SPT-3 already asks for two declared continuation policies) |
| G7 | Values of g and h (A.0) | declared in the SPT-1 pre-declaration. Recommendation for h: 0 (keep iff m̂ > 0), the value runbook phase P7 validated |
| G8 | Proposer for measurement (b) | the pick (R1-PAPERC-PROPOSER) |
| G9 | Go/no-go on a node that fails the replay threshold (B.6) | STOP for the author. Recommendation: "not assessed" for that node |
| G10 | K correction (A.3) | K = 10 on T0; on T1, K = 10 until R1-BX-D3's check is recorded, then K = 6 |
| G11 | Recorder's additions | as written: the regression-adjusted estimator (A.3), the empty-cluster rule (A.5), and per-cluster truncation rates (C) |
