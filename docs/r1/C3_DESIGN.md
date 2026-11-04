# C3 design — learned per-proposal prior under the C2 rule ("PCP control")

**Status:** drafted 18 Oct 2026 by an AI agent (Claude, coordinating session). **Fixed by the author on 18 Oct 2026 (PLAN §10):** route A as C3 (R1-C3), the arm ladder of §5 plus the §10 reference arms (R1-C3 ladder), the C3 gate of §6, and the D4 amendment, D18, D21, D23 and `"vary"` split rows it depends on. Everything else below is a proposal. Theory: `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` (Propositions 6–10). Nothing here is evidence.

> **Later decisions.** The old §5 bin-as-action and greedy-bin deployment, and related prior-only training description, are superseded by separated belief and execute/skip outputs (PLAN §10 R1-C3-POST). R1-SOFT-SIGMA replaces the per-proposal audit-SE label for new tables; duplicates are rule-skipped and excluded from labels rather than assigned the no-op bin (22 Oct duplicates row). The 22 Oct row fixes g; K=10 is the total audit seed count. R1-INFER-LLAMACPP, R1-VENUE-3 and the current RUNBOOK supersede the old backend and venue references. Historical simulation assumptions, costs and dates below are retained; the venue decision did not itself adopt a new timeline.

> **4 Nov 2026 (PLAN §10 R1-BX-D1 … D14, R1-BX-REVISIONS).** Where this file conflicts, these rows control:
> - **Labels come from T0 and T1.** T0 is the 8 CPU nodes (single-parameter edits, the low-interaction condition); T1 is GPU label nodes from autoresearch, 1GC-7RC and MLGym (code-level diffs, fixed step budgets, one GPU model per table). T2 nodes are evaluation only. Primary generalisation is **leave-one-suite-out**; LONO within T0 is secondary (§6).
> - **K.** K = 10 until an author row puts K = 6 (3 label + 3 evaluation seeds) into force after the sweep-1 subsampling check passes (R1-BX-D3; scope *proposed*: T1 audits only). The soft-label width uses each node's own σ̂ (s = σ̂_node/√K_label). Divergent runs are a separate outcome class (§4).
> - **Ladder additions (§5):** the Karpathy default and fixed-r replication + t-test (R1-BX-D7); TabPFN information-matched, in regression mode (R1-BX-D13).
> - **Gate (§6):** the aggregate IQM of gap closed and probability of improvement with node-stratified bootstrap CIs replaces the per-node criterion (R1-BX-D8); its numbers are fixed in **R1-BX-D8-CONFIRM** before any sweep-2 label is analysed.
> - **Self-control arm:** A4 (R1-BX-D9). The decision-focused stage A6 is called "decision-focused fine-tuning"; only R-B (an optional ablation) is called RL.

## 1. One-paragraph summary

The learned component does **not** choose actions. It predicts, **before a run is spent**, the distribution of the true increment of the proposed edit: the inert probability π, the mean μ and the spread τ, conditional on the edit and the ledger. These three numbers go into rules derived in C2:
- **E1 screening** — execute iff (1 − π)·V(t*; μ, τ, σ) ≥ g (T4 Proposition 8);
- **E2 acceptance** — keep iff Δ̂ > t* = −μσ²/τ² (T4 Proposition 6; needs the D4 amendment).

σ (comparison noise) is measured per node and edit kind (E1), not learned; g (run price) is fixed at 0.1 σ_node, with 0.05 and 0.2 σ_node as declared sensitivity values (PLAN §10, 22 Oct). Because every estimator emits the same (π, μ, τ), the arms differ **only** in the quality of the prior:

constant (index policy) → rules → tabular → LLM zero-shot → small LM (SFT) → small LM (decision-focused GRPO).

This ladder is C3.

## 2. Why this is robust

1. **Structural floor.** If the predictor learns nothing, (π, μ, τ) collapse to node constants and the rule reduces exactly to the C2 index policy. A learned arm can lose to the index policy only through miscalibration, and that is measured offline before deployment.
2. **It saves runs instead of spending them.** T2 Proposition 5 (verify rarely pays) and E1b (zero verify headroom) are the reason screening has value: each correctly skipped run is worth ≈ g (T4 Proposition 8).
3. **The signal exists in pilot data.** 18 Oct offline check (`~/scratch/offline_a.py` on the Mac VM; not committed):
   - 39–77 % of LLM trials repeat an evaluated configuration;
   - 9–14 % are bit-identical to the incumbent;
   - among informative trials the mean increment differs strongly by edit type (`digits_mlp`: `BATCH_SIZE` −0.012, n = 94, vs `HIDDEN_UNITS` +0.004, n = 181, against a paired noise of ≈ 0.0075);
   - with memory on, only 24 % of informative proposals improve, so μ₀ < 0 and the Bayes threshold is above 0.

   Small samples, single-campaign Δ̂: the premise is not refuted, not established.
4. **Every outcome is reportable.**
   - Learning adds above rules + index: C3 positive.
   - Tabular ties LM in distribution but LM wins on held-out nodes: transfer result.
   - Nothing adds: T4 Proposition 7's dispersion bound explains why, and C1 + C2 stand.
5. **RL has a learning signal here, unlike in E1b.**
   - In E1b the reward was the campaign-final Y, and continue vs verify branches ended in nearly the same place, so group-relative advantages ≈ 0.
   - Here the reward is per proposal, immediate (valid under DI, T4 Proposition 10) and computed from a fresh-seed audited label. Execute vs skip, or different keep thresholds, give different rewards on the same proposal whenever its value is near g or Δ̂ is near t*.

## 3. The predictor

**Output head (all arms).** A categorical distribution over 12 bins of the standardised increment z = Δ / σ_node:
- one **no-op** bin (exactly zero: the edit leaves the active configuration unchanged). **Duplicates** of an earlier evaluated configuration are *not* in this bin: their increment is generally non-zero, their result is already known, and the rule layer skips them (T4 Corollary 8a as revised 19 Oct). They get no training label;
- 11 bins with edges −∞, −3, −2, −1, −0.5, −0.15, 0.15, 0.5, 1, 2, 3, +∞.

π = mass of the inert bin. μ and τ are the mean and sd of the non-inert part, using bin midpoints and ±4 for the tails, rescaled by σ_node. Standardising by σ_node makes outputs comparable across nodes, which the transfer test needs. A categorical forecast scored by log loss is a strictly proper probabilistic forecast, and for an LM it is a single next-token distribution: no regression through generated text.

**Input.**

| Group | Features (structured; the LM sees them serialised as text) |
|---|---|
| Task | node id, dataset descriptor (rows, features, class balance), metric, current `model_type` |
| Edit | key, old → new, log ratio, direction, edit kind (local / structural), active-key flag (D25), config-hash seen-before flag (D27) |
| Ledger | times this key was edited; last Δ̂ and decision for this key; keeps so far; trials since last keep; recorded gain so far; budget fraction left; memory mode |
| Text (LM arms only) | the manager's proposal summary and rationale |

**Leakage rules** (from PLAN §7 interface): no audit value of the current or any future proposal; no sibling or branch outcomes; train / dev / test split by instance seed, plus leave-one-node-out (LONO). Never split by trial.

## 4. Labels

- **Source of proposals.** LLM-manager root campaigns, exactly as in R1-E1B-RERUN2 (pinned `qwen2.5-coder:7b`, memory `append_only_summary` primary, `none` contrast, W = 20). **No branching is needed for C3 training.** Labels are per proposal, which is much cheaper than branch tables.
- **Audit.** For each non-inert evaluated proposal: run candidate and incumbent configurations on K = 10 common fresh joint seeds (7001–7010; the first 5 give the training label, the last 5 the evaluation value; revised 22 Oct 2026 — the 19 Oct pilot used K = 6, split 3 + 3), giving Δ_audit and se_audit. No-ops are labelled by rule (no-op bin = 1). Duplicates get no label (revised 19 Oct 2026).
- **Separate label and evaluation seeds.** The fresh-seed audit seeds are split (proposed K = 10: 5 for labels, 5 for offline evaluation). Sharing seeds made the pilot gate "pass" spuriously (C3 offline pilot).
- **Soft target.** The label is N(Δ_audit, se_audit²) integrated over the bins: the posterior of Δ under a flat prior given the audit. This keeps the log loss proper under label noise.
- **Scale.**
  - One rerun-2-sized sweep (4 nodes × 18 instances × 2 memory modes × 20) gives ≈ 2,900 proposals, of which ≈ 1,000 are non-inert.
  - Audit cost: ≈ 12 runs × 1–2 s per proposal, about 6 CPU-hours per sweep; under an hour on Ada cores.
  - Target ≈ 8–10k labelled proposals, from: the OpenML pool extended to 12–15 datasets (D20, small new code), 3 MLP nodes, and a second manager model for proposal diversity. That is 2–3 sweeps. *(3 Nov, PLAN R1-MAIN-PROPOSER: the main sweep uses the Track X pick, thinking off; `qwen2.5-coder:7b` sweep 1 is the second manager.)*
- **4 Nov additions (R1-BX-D3, D4, D5, R1-BX-REVISIONS (c)).**
  - On T1 nodes a proposal is a code-level diff. Inert and duplicate detection for diffs is part of the harness change (a normalised diff hash and an equality check against the incumbent's code); no-ops are labelled by rule as on T0.
  - σ̂ for a T1 node comes from that node's own noise floor, measured on the label table's GPU model. If the floor is heavy-tailed, a Student-t soft label is declared before labels are built *(proposed)*.
  - A run that diverges is recorded as its own outcome class and never averaged into μ (R1-BX-REVISIONS (c)). *(proposed:* divergence = a non-finite loss, or no metric at the fixed budget; it gets no z-value and is reported separately.*)*
  - About 150 audited proposals per T1 node; K = 10 unless an author row puts R1-BX-D3's K = 6 into force.
- **Covariate shift.** Deployed arms skip and re-propose, so the proposal distribution shifts. One aggregation round fixes this: collect proposals under the deployed tabular arm, audit them, retrain (DAgger-style).

## 5. Arms (the ladder) and training

| Arm | Prior source | Training |
|---|---|---|
| A0 | ρ, the default rule | — |
| A1 | **C2 index policy:** constant (π, μ, τ) per node; constant Bayes threshold; KG verify per D23 | dev campaigns |
| A2 | A1 + **rules:** π = 1 on hash duplicates and inactive keys (D25, D27) | — |
| A3 | **tabular:** LightGBM multiclass on the 12 bins (plus an NGBoost-Gaussian variant) | log loss, soft labels |
| A4 | **LLM zero-shot:** the manager answers typed questions (P(no effect), P(Δ > 0), size bucket), mapped to bins by isotonic calibration fitted on dev | calibration map only |
| A5 | **small LM, stage 1:** Kev-0.8B / Kev-4B and StartLux-Decision-v1.1 0.8B / 2B / 4B (main), Laya 421M as an encoder rung (R1-C3-BASE, 24 Oct; ≤ 4B), LoRA r = 16, next-token distribution over 12 bin tokens | SFT with soft-label cross-entropy (log score) |
| A6 | **small LM, stage 2:** A5 then decision-focused post-training | see below |
| (A7) | stage 3 online RL | only if the DI test (§7) shows a material violation |
| ref | AWR-MLP acting on actions directly (Harness-MDP style); PACE gate | as PLAN §5 |
| prac-1 (4 Nov) | **Karpathy default:** always execute, single run, keep if Δ̂ > 0 (if A0 is exactly this rule, A0 is relabelled rather than duplicated) | — |
| prac-2 (4 Nov) | **Fixed-r replication + t-test** (racing style): r runs per candidate, keep by a one-sided t-test at a declared level *(proposed: r = 3, Welch, α = 0.05)*, charged for its runs at matched compute | — |
| TabPFN (28 Oct; 4 Nov) | In-context and fine-tuned beliefs on the featurizer features (R1-TABPFN), **plus an information-matched row (R1-BX-D13):** hand features + a PCA-reduced proposal-text embedding for TabPFN, and the same information for Kev; TabPFN in regression mode with its predictive distribution binned | as R1-TABPFN |

**Stage 2, precisely.**
- **Environment:** the plug-in rules plus the logged labels. It is an offline contextual bandit; no harness runs during training.
- **Action:** one bin token b ∼ q_θ(· | x, F).
- **Plug-in:** μ = σ·mid(b), τ = σ·τ̂_node (dev-estimated), π = 1{b = inert}. The rules give (execute, keep) using the campaign's logged Δ̂.
- **Reward:** r = Δ_audit · keep − g · execute, from the logged label.
- **GRPO:** K = 8 samples per prompt, group-mean baseline, KL to A5. Generation is a single token, so rollouts are nearly free. With 12 actions the expected reward can even be computed exactly by enumeration, so the GRPO estimate can be checked against the exact gradient.
- **Comparator optimiser:** the smoothed-rule decision-focused loss (indicators replaced by annealed sigmoids; standard predict-then-optimise practice), so a gain can be attributed to the decision-focused objective rather than to the RL estimator.
- **Deployment:** greedy (mode) bin, matching the GRPO policy's limit.
- **Prediction (T4 §7):** A6 > A5 only where A5 is miscalibrated near t* or near g. The within-group reward variance concentrates on those proposals, and that is reported.

**Compute.**
- SFT: about 7M tokens per epoch, under an hour on one RTX 6000 Ada.
- GRPO: single-token rollouts, tens of minutes.
- Online deployment: manager plus small LM co-resident on one card (5.6 GB + ≤ 4 GB), within the co-tenancy rule (PLAN §10).
- Nothing runs on the Mac (R1-COMPUTE).

## 6. Evaluation

**Offline, one-step (fast; gate and model selection).** For held-out proposals, the realised one-step value is Σ (Δ_audit · keep − g · execute) under each arm's prior, using the logged Δ̂ (independent of the audit seeds). Under DI this is unbiased for the J_g contribution. Also reported:
- log score;
- calibration of P(Δ > 0) and of π;
- T4 Proposition 7's upper bound vs the realised threshold gain;
- Proposition 8's screening term E(g − V*)⁺ vs the realised screening gain.

**Online, primary estimand V^π (PLAN §4).** Arms A1–A6 (A0 for reference) control fresh campaigns at matched W = 20 runs and matched LLM-call cap. Outcome Y = fresh-seed audited final improvement. 18 instances per node, 2 repetitions. Cluster bootstrap by instance; results per node and pooled; LONO.

**Pre-declared contrasts** (to be frozen before Phase 3 per PLAN §9):

| ID | Contrast | Claim it tests |
|---|---|---|
| H1 | A3 − A2 | learning adds above rules + index |
| H2a | A5 − A3, in distribution | does an LM prior add over structured features (may tie) |
| H2b | A5 − A3, LONO held-out nodes | LM priors transfer where tabular has no history (expected main LM result) |
| H3 | A6 − A5 | decision-focused post-training adds, located where T4 §7 predicts |
| H4 | A4 vs A5 | the manager's own zero-shot judgement vs a small trained model (the LLM-self-control arm in its useful form) |
| H5 | gain by memory mode | screening value is largest for the weaker proposal law (memory off) |

**C3 gate, since 4 Nov (PLAN §10 R1-BX-D8; replaces the 18 Oct per-node criterion below).** The primary criterion is the **across-node aggregate**: the IQM of gap closed and the probability of improvement of A3 or A5 over A2, with node-stratified bootstrap CIs, on the main proposer's T0 + T1 labels. The per-node table is secondary. The numbers are fixed in a separate author row **R1-BX-D8-CONFIRM** (with the gate-code sha) before any sweep-2 label table is copied back for analysis. The row's proposed operationalisation:
- gap closed per node = (U_arm − U_A2)/(U_oracle − U_A2) on test instances with `y_eval`, U_oracle being the noisy-oracle ceiling of TRACK_P §7.1;
- the IQM across nodes;
- probability of improvement = the per-node share of test instances where the arm beats A2 (ties ½), averaged over nodes;
- 2,000 node-stratified bootstrap resamples;
- nodes whose denominator U_oracle − U_A2 is below δ_n on dev are excluded from the IQM (listed) and kept in the probability of improvement;
- pass if, for A3 or A5 with Holm at family-wise one-sided α = 0.05 (one-sided 97.5 % bounds for the first-ranked arm, 95 % for the second), the lower bound of the IQM gap closed is > 0 and the lower bound of the probability of improvement is > 0.5; the point IQM is reported against a practical size of 0.1.

**Generalisation, since 4 Nov (R1-BX-D1):** leave-one-suite-out is the primary transfer test; LONO within T0 is secondary. The H2b contrast is read on held-out suites first.

*Superseded (18 Oct):* **C3 gate (replaces RUNBOOK 1.5 for C3; adopted 18 Oct, PLAN §10).** Proceed to online deployment if the offline one-step gain of A3 or A5 over A2, scaled to a 20-run campaign, reaches δ_n (D18) on at least two nodes, with its lower 95 % bound above 0. Otherwise report C3 as the measured negative, with T4 Proposition 7's dispersion bound as the explanation; C1 + C2 carry the paper.

## 7. Add-ons: B (part of C2) and D (= C4)

Placement fixed on 18 Oct 2026 (PLAN §10, R1-C4).

**B — theory of the gain. Part of C2; its empirical checks are reported with C3.**
- Propositions 6–10 are written in T4. The empirical side reuses C3's labels: bound vs realised gain (Proposition 7), the screening term (Proposition 8), and the T4 §7 prediction about A6 vs A5.
- Cost: about a week of analysis code, no new runs.

**D — proposer feedback = C4 (secondary): the DI test and debiased memory.**
- **DI test, free:** the E1b LLM branch pairs (`results/r1/pilot/E1b_20261013T151857Z`) already contain forced different decisions at matched histories (continue vs verify-demote). Compare the next proposals' keys, sizes, novelty and (after audit) μ across the pair. This measures how far T4 Proposition 10's DI condition fails for the pinned manager, and decides whether A7 is needed.
- **Debiased display, cheap:** one memory-summary variant that shows B̃ (cumulative posterior-mean increments of kept edits, T4 §5) instead of the raw record B. Run one A/B sweep on 2–4 nodes on Ada (a few GPU-hours) and audit as in §4. Outcomes: proposal distribution shift, audited μ of proposals, and Y.
- This is the only direct measurement of the proposer-feedback channel that classical selection theory does not model.

## 8. Risks and mitigations

| Risk | Effect | Mitigation |
|---|---|---|
| Most predictable waste is rule-detectable | Learning gain small in distribution | A2 is a declared baseline. The LM's claim moves to transfer (H2b) and to free-form edits later. |
| Tabular ties LM | H2a null | Reported as such; H2b and H4 carry the LM part |
| Too few nodes for LONO | Weak transfer evidence | Extend the OpenML pool and MLP nodes to ≥ 8 qualifying nodes (L8b-style code) |
| Toy nodes only (4 Nov review, P1–P3) | Labels and gate on one template with one knob; near-bandit by construction | T1 GPU label nodes with code-level diffs; leave-one-suite-out; T0 kept as the low-interaction condition (R1-BX-D1, D2, D4) |
| Node screening favours the method (P9) | Selection-bias criticism | Screening funnel per suite; non-qualifying nodes in an appendix (R1-BX-D12) |
| g mis-tuned | Over- or under-skipping | g tuned on dev instances; sensitivity curve reported |
| DI violated strongly | Plug-in rule not optimal; one-step offline value biased | Measured by the D test; then A7 (online RL) becomes justified, with the T4 Proposition 10(b) explanation |
| Predictor miscalibration | T5 (check 6): a predictor that is uncalibrated, or overconfident in τ, does **worse than the constant-prior baseline** | Calibration is the primary model-selection criterion (log score, reliability of P(Δ > 0) and π) before any deployment. Isotonic recalibration on dev instances. Ship only arms whose offline one-step value beats A2. |
| Open small LMs judge ML edits poorly | FOREAGENT reports 52–55 % pairwise accuracy for open Qwen models | A3 (tabular) and A4 (manager zero-shot) are full arms; the LM's case rests on calibrated forecasts and transfer (H2b), not on raw accuracy |
| Label noise | Blurred targets | Soft labels; K raised to 10 on edits near t* |

## 9. Timeline (fits PLAN §9)

> **Superseded 4 Nov (R1-BX-D14):** B.7 ≈ 8 Dec 2026 on T0 + T1 labels, D.3 ≈ 3 Jan 2027, manuscript 10 Jan 2027; recomputed after the T1 pilot. The table below is history.

| By | Step |
|---|---|
| ~1 Nov | Decisions (D4 amendment, D18, D21, split policy, D23); audit pipeline; audit the rerun-2 proposals; DI test on existing E1b branch pairs; A2 and A3 offline |
| ~22 Nov | Extended node pool and 2nd sweep; A4 calibration; A5 SFT; offline C3 gate |
| ~20 Dec | Online pilot A1–A5 on the qualifying nodes; aggregation round; D sweep |
| ~31 Jan | A6 GRPO; LONO; pre-declare Phase 3 |
| ~28 Feb | Phase 3 deployment analysed |
| ~31 Mar | TMLR submission |

## 10. Novelty position (after the 18 Oct novelty sweep, part 2: `inputs/NOVELTY_SWEEP_PART2_20261018.md`)

**No work was found (abstract level) that combines an LLM proposer, noisy incumbent-relative acceptance, and a learned per-proposal prior or pre-execution screening.** Three 2026 papers each cover two of the three, and reviewers will know them:
- **SAGE** (arXiv 2609.36043): a paired, statistical acceptance gate against the incumbent, citing the optimizer's curse. It has no prior, no screening and no run price.
- **FOREAGENT** (ACL 2026, arXiv 2601.05930): pairwise pre-execution preference with predict-then-verify for ML agents. It has no increment distribution, no noise model and no decision threshold.
- **Beneath the Diff** (arXiv 2609.00077): the same keep-if-better ML-edit loop, with repetitive edits and a validation gate. It has no statistical model.

**Full-text read, 19 Oct (`inputs/NOVELTY_FULLTEXT_20261019.md`):** two claims are narrowed. (i) Pre-execution skipping exists (FOREAGENT's confidence-gated best-of-10; the DAPS similarity filter in Beneath the Diff). Ours is a value-based skip rule under a run price, driven by a trained increment-distribution predictor. (ii) Re-proposal of rejected candidates is published ("Visible but Not Avoided", arXiv 2610.15738: 28–63 % of iterations in a deterministic setting). C4's novelty is the decision-independence condition and its test under noise. Additional baselines: a SAGE-style gate charged for its runs; a FOREAGENT-style pairwise screen; the DAPS duplicate filter; a one-sentence "rejection status" memory display as the control for the debiased display.

**Consequences for the design:**
1. **Positioning.** The C2 formulas for the Bayes threshold and the verify VoI are classical (Xie & Frazier 2013; Chick & Frazier 2012; Smith & Winkler 2006; the Ladder). They are presented as instantiations. The C2 contributions to defend are:
   - verify competing with **new proposals** for one run budget;
   - the winner's-curse bound for **any** adaptive proposer (T4 Proposition 9);
   - the per-proposal gain bound and skip rule (T4 Propositions 7–8);
   - the decision-independence condition (T4 Proposition 10).
2. **C3 differentiators.**
   - Labels are fresh-seed-audited increments relative to the incumbent, not pairwise preferences or single noisy outcomes.
   - The forecast is a distribution plugged into a derived rule.
   - The post-training reward is the decision regret under that rule. No prior work was found doing decision-focused RL post-training of an LLM predictor that feeds an accept/skip rule.
3. **Reference arms added** (beside §5):
   - a SAGE-style paired one-sided test gate (needs paired evaluations, so it spends runs, like PACE);
   - a FOREAGENT-style pairwise predictor used for screening;
   - a Ladder-style margin rule;
   - a posterior-mean incumbent.

   Proposer-side alternatives (GEAR population search, DAPS) are discussed and, if cheap, run as appendix arms, so that control-plane gains are separated from proposer gains.
4. **To read in full before citing specifics:** SAGE, FOREAGENT, Beneath the Diff, and arXiv 2610.15738 ("Visible but Not Avoided", on state-dependent re-proposal of rejected candidates). The last could not be fetched and bears directly on the ledger-dependent proposer.
