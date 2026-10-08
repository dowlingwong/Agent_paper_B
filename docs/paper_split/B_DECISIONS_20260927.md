# Paper B: decisions now, 27 September 2026

**Decision:** proceed with a bounded, timing-led research program with replay uncertainty as a validity constraint. The current manuscript and engineering fixtures do **not** yet establish a novel ICML paper. Choose the task direction, outcome, capacity and development budget now; advance on evidence gates immediately instead of waiting for the dates in RUNBOOK §11. This is a research/design decision, not a qualification certificate, live-run authorization, or completed experiment.

This review read the B manuscript's sections and appendices, the novelty memo, active `b_v2` contract and validator, control learners/allocation/evaluation, one-step smoke and three-leaf fixtures, and the existing interface/D0 diagnostics. The source tree is based on commit `96aada3936c3fac7a7142af52d4e63de82631eeb`, with existing uncommitted A work preserved. All proposed live results below remain **PLANNED**.

## Decisions for gaps 7–12

| Gap | Working decision now | What remains genuinely unknown |
|---|---|---|
| 7: novelty | GO for bounded development of N2 timing plus N1 measurement validity; NO-GO for claiming the current draft already supplies the contribution. Drop advantage-versus-matched-ridge-value superiority as a hypothesis. | Whether temporal information and an honestly sourced discrepancy allowance produce useful, reproducible controller differences against strong prior methods. |
| 8: discrepancy p | Use conditional sensitivity analysis. Register p in {0, .005, .01, .02, .05, .10}; .02 is the working assumption, never an estimate. Specify a separate joint path allowance for N2. | Natural live-substrate discrepancy, and whether any audit can upper-bound outcome-relevant omissions with adequate coverage. |
| 9: outcome | Primary U: hidden-test accuracy of the final valid candidate, in [0,1]. Invalid/no candidate by the horizon receives U=0 and an explicit invalid flag. Binary validated completion is secondary. | Whether U supplies decision room on the new task; continuous scoring cannot repair a causally ineffective intervention. |
| 10: design numbers | Primary capacity .25; meaningful gain .02 U; mean no-injected-fault harm tolerance .02 U. Bounded screen/pilot limits below. | Final sample size and final collection budget, determined from pilot variance and cost before final outcomes. |
| 11: task/model | New B-only candidate-consistency task with two online checkpoints; reuse the D7 tool scaffold, abandon the old .7-to-.9 repair mechanism. Sole initial model candidate: Devstral-Small-2-24B-Instruct-2512 on the already planned Ada substrate. | Executable task witnesses, exact artifact/runtime pins, available prepaid capacity, qualification and measured model operability. |
| 12: venue | ICML 2027 is the primary target now. Route decision follows the bounded pilot, not a November waiting date. | Official 2027 CFP/deadline and whether the resulting evidence merits this venue. N1 alone is not automatically an ICML paper. |

## Findings that change the paper

### The old H2 cannot work with the implemented estimators

The experiments section says “The learned advantage allocation beats the plain action-conditioned value” (H2, `papers/paper_b/sections/07_experiments.tex:21`). The implemented learners use identical ridge design matrices, penalties and paired training rows (`experiment_scaffold/src/causal_branch/control/learners.py`, `_Ridge`, `AdvantageLearner`, `ActionValueLearner`). If B is their common linear fitting operator, B(y_v-y_0)=By_v-By_0. Their advantage predictions are identical up to floating-point error, regardless of sample size.

A fresh closed-fixture diagnostic found maximum disagreement **8.743e-16** over 36 checkpoint rows. This is an engineering identity check, not an empirical controller result. Keep this comparison as an implementation consistency check. A nonlinear direct-contrast versus two-head comparison can be a matched secondary ablation, but do not manufacture a contribution through unequal representations, tuning budgets or information. Utility deficit is the fair primary risk-style comparator when U is primary; binary failure risk remains secondary.

The current gate (`control/allocation.py`, `ConservativeSelector`) does not implement p. The current smoke pipeline (`experiments/paper_b/smoke_b.py`) uses S as primary. The sequential fixture (`experiments/paper_b/tree_fixtures.py`) selects supplied leaf values; it is not evidence of live sequential learning. These are implementation gaps, not missing writing alone.

### The old task fails a causal check, not just a completion-rate check

The D0 report states “The matched rule loses accuracy on all eight templates” (`docs/paper_track/interface_amendment_2026-09-26/D0_FAULT_SENSITIVITY.md`, Results). Trusting P/.7 gave 8/8 validated completions versus 6/8 after the proposed .9 rewrite; refitting P gave 8/8 under either initial value. The prescribed change helped zero and harmed two. These are fixed-policy diagnostic results on the historical block, not live-agent effects or a population estimate.

Consequently, increasing task completion or switching to U does not rescue that E3 mechanism. Preserve the old NO-GO. The revised candidate interface is an operability improvement to test separately; it is not evidence that verification helps. Historical Devstral 1/24 versus Qwen 5/24 g0 completions used different deployments, so they cannot identify model superiority (`BOUNDED_DIAGNOSTICS_ROUND2.md`, in the same directory).

### The novelty must survive a stronger prior comparison

[Calibration Is Not Control](https://arxiv.org/html/2606.21399v1), §§3–4, already uses prefix branching, intervention advantage and conservative action-value selection. Thus branch labels, risk insufficiency and an LCB alone cannot carry B's novelty. N1's 2p correction is a useful transfer of A's measurement bound, not by itself a new learning theorem.

[Strategic Verification for Long-Running LLM Agents](https://www.preprints.org/manuscript/202608.2057), §§3–4, already discusses verification timing, finite budgets, deferral for information and reserving resources for later checks. This preprint must be compared at the method level; its reported performance has not been independently reproduced here. Add a frozen reserve/VOI scheduling baseline. General “verify now or later” novelty is unavailable on this evidence.

[Calibrate-Then-Act](https://arxiv.org/html/2602.16699v1), abstract and introduction, also treats cost-aware information gathering and selective testing. B must isolate the narrower contribution: original-root, action-dependent two-checkpoint evaluation under an explicit replay-uncertainty contract, with matched timing baselines. This is a candidate contribution requiring demonstration, not an established novelty claim.

## A concrete B1 manuscript spine

**Working title:** When to Spend a Verification Budget under Replay Uncertainty.

**Prospective abstract:** Verification can improve an agent's result, consume resources without benefit, or remove a more valuable opportunity to check later. We study a fixed verification-and-response regime with at most one use across two online checkpoints. A paired branch-tree design compares verifying now, reserving verification for later, and never verifying on the original root population, including early termination and infeasibility. Policy assessment separates sampling uncertainty from an explicitly conditional allowance for outcome-relevant reconstruction error. The planned evaluation tests whether preserving a later verification opportunity improves bounded task utility against matched myopic and reserve-based controllers, and whether conclusions survive plausible reconstruction error. No live benefit or safety result is claimed before this evaluation.

The main paper should contain the two-checkpoint problem, the original-root estimand, the scoped population robustness proposition, the matched controllers and the live evaluation. Move inherited ordinal/abstraction/price theory that is not necessary for these claims out of the main narrative. The present manuscript still frames sequential control as future work and cites v1; B1 must update this to the active v2 design. Also repair the appendix's assertion that cell-measurability makes a pointwise conditional advantage equal its cell average (`appendices/B_proofs.tex:290`); only the conditional expectation identity is generally available. This review does not recertify the entire inherited theory.

### Falsifiable tests, including an inconclusive outcome

**N1 mathematical claim:** under a stated joint discrepancy event of probability at most p, bounded utility, a fixed policy and the required calibration independence, the population gain lower bound loses at most 2p. A counterexample satisfying these assumptions falsifies the claim. Planted-defect simulations test implementation and coverage under known injected laws; they do not estimate natural hidden discrepancy. Monte Carlo rejection-rate uncertainty must be accounted for before declaring a coverage failure.

**N1 practical claim:** at equal allowed resources, adding the allowance improves the declared utility/harm tradeoff relative to the same fitted policy family and sampling-only gate. Report utility, no-fault mean harm, intervention use and abstention. A controller that always abstains can satisfy a validity criterion while failing the practical contribution. Understated-p failures are sensitivity results, not refutations of a conditional theorem.

**N2 primary claim:** the frozen two-checkpoint controller improves original-root mean U against BOTH a repeated-myopic controller and a predeclared reserve/VOI controller at the same allowed verification and total-work budgets. Each root permits at most one verifier call. Use simultaneous confidence intervals for these two primary contrasts, with template families as the sampling units and a prespecified treatment of batch coupling. Never/verify-now/verify-later and sampling-only variants remain diagnostic baselines.

Set the practical target to .02 U. Call a comparison statistically supported when its adjusted lower confidence bound exceeds zero; a point estimate at least .02 also meets the point-estimate practical target. A claim that the gain itself exceeds .02 requires the lower bound to exceed .02. An upper bound below .02 rejects the stated practical target; an interval spanning it is inconclusive. “Not distinguishable from zero” in the current H1 is not a valid falsification rule. At the budget cap, inconclusive means no positive claim and no automatic expansion to chase significance.

## Where p comes from and what it can justify

The default is **sensitivity_assumption**, not validated_evidence. At working p=.02, the worst-case population contrast tax is .04. Include the full registered grid even if only small p values preserve a conclusion. Report the largest p at which the particular frozen-policy conclusion survives, with simultaneous inference if this is a searched assertion.

A global allowance supports a population statement for G(d)=E[d(W)(U_v-U_0)] only when the joint discrepancy event covers the relevant decision information and both regime outputs. Its signed integrand lies in [-1,1], giving at most 2p change. A global p does **not** justify a pointwise gate LCB(w)-2p or a conditional clean-stratum guarantee. Selected and clean strata need separately justified conditional allowances; selection can concentrate all defects. Do not replace 2p with 2qp without additional assumptions. A finite frozen policy family can instead be assessed with simultaneous population lower bounds, then abstain if none qualifies.

For N2 use p_path for the joint discrepancy event covering the decision histories and compared regime outcomes. If only checkpoint-wise bounds p1,p2 are available, use a justified union bound min(1,p1+p2), not independence by default. A one-step allowance does not automatically qualify a two-step trajectory. When the utilities are continuous, do not apply A's sharper R=1 binary-outcome endpoint formula without a new derivation. Rename task-condition prevalence omega to avoid collision with replay p.

Even under independent audits and a perfect discrepancy detector, zero misses in n audits only gives the one-sided 95% upper limit 1-.05^(1/n). With n=24 this is **.11735**; bounding p by .02 requires at least **149** zero-miss audits. Real detectors can miss defects, so these numbers are optimistic. An injected-defect panel estimates detector behavior on its chosen defects, not their natural prevalence or coverage of unknown state omissions. It cannot certify .02 merely by being small and clean.

There is a further qualification nuance: `launch_validator.py` accepts a properly bound **measurement_plan** provenance with p still null. A nonnull measured p is not universally required by the current code. Conversely, entering .02 does not qualify the substrate or validate a safety claim. Current pilot/main/final phases explicitly refuse as unimplemented. Keep those refusals until their actual checks exist.

## Outcome, capacity, harm and resources

Use raw held-out accuracy U for every valid final candidate. Do not first threshold success at baseline+.05 and then define U only on successes; that would discard the intended additional resolution. Neither the agent nor verifier may read hidden labels. Invalid/no submission at the horizon receives U=0 with its reason retained. Collection failure is a data-integrity status, not fabricated zero utility. An unavailable action has no observed outcome; deployment follows its predeclared continue fallback and remains in the original-root analysis. S and validity are secondary outcomes. Costs remain separate vector constraints, without an arbitrary monetary weight folded into U.

Choose q=.25 (already the statistics manuscript's primary capacity), with .05,.10,.50 descriptive only. Preserve the existing one-step ceil(q*n_feasible) convention and report effective capacity for small batches. For the new original-root tree evaluation, explicitly register floor(.25*N_original) as the total verifier-call budget, at most one per root. Unspent capacity stays unspent. These two denominators must never be silently exchanged. Matched *allowed* budgets need not produce equal realized call counts; report both.

Choose mean no-injected-fault utility loss at most .02 versus never-verify as the harm endpoint. This is neither a per-person no-harm guarantee nor a bound on the probability of any degradation. Keep `safety_claim_level: empirical`. Report individual degradation frequency and invalid-output rate separately. Any integrity violation stops collection; it is not covered by the utility harm allowance.

For the initial screen plus pilot, impose the first of these limits reached:

- 512 terminal leaf executions in total, including controls; at most 2,000,000 generated tokens across every model/verifier/prefix call.
- 10 hours aggregate elapsed collection time, 20 accelerator-hours, and 10 GiB newly retained artifacts.
- Zero **new** paid API or rental commitment. Existing prepaid/approved capacity must be confirmed available and metered; this is not a claim that a leased GPU is free. No automatic new rental if it is unavailable.
- One selected model; no model search. Immutable task IDs, no replacement of scientific failures with retries. Operational recovery preserves all attempts and stays within the same cap.

Allocate 8 fresh screen template families × 2 roots × 2 repetitions × 3 leaves = 96 leaves, then 32 disjoint pilot template families × 2 × 2 × 3 = 384. The remaining 32 leaves are reserved for prespecified integrity controls, not best-seed retries. Prefix continuation, second-checkpoint work, verifier overhead, failed attempts and storage count toward their respective ceilings. Three leaves do not mean the same cost as three one-step tails.

The screen and pilot are development data, not confirmatory tests. Thirty-two templates cannot certify a small uniform safety bound: a range-2 Hoeffding radius with eight one-sided endpoints at alpha=.05 is approximately .563. Batch top-q decisions also couple roots; a per-root iid proof cannot be applied unchanged. Use independent batches for such a proof or derive a valid bound; a bootstrap that recomputes allocation is empirical inference, not a replacement safety theorem.

Determine final sample size from independent-template contrast variability, not leaf count. For scale only, a normal approximation for 80% power, one-sided alpha=.025 and gain .02 gives approximately 49/196/784 templates at paired standard deviations .05/.10/.20. These are planning illustrations, not a final power analysis. Set final collection limits and freeze the COMBINE/CORE_ONLY route before final outcomes; do not reuse pilot templates as held-out evidence.

## Task/model choice and event gates

Build a new B-only candidate-consistency task around the corrected evaluated-candidate interface. The fit tool must return the exact executable candidate it evaluated. Verification checks consistency with visible development diagnostics; a frozen response rule may replace a candidate only on a specified strict development improvement, with ties leaving it unchanged. Hidden evaluation remains separate. The second checkpoint must arise online after legitimate new visible information, making the value of waiting observable without future leakage. Do not transplant the rejected lambda-fault story under a new name.

Before any live screen, construct executable fixed-policy witnesses where now, later and never are each best under declared costs, plus uninformative and harmful-check controls. They must run through the actual adapter, not supplied tree leaf constants. Freeze a balanced development screen allocation across these four mechanism classes (two families each); this is an artificial diagnostic law, not natural deployment prevalence. Freeze a distinct pilot law and generator before pilot outcomes. Stop if ordinary refitting makes the verifier redundant or if no legitimate later-information mechanism exists. Do not tune against the historical hidden block to manufacture benefit.

Select `mistralai/Devstral-Small-2-24B-Instruct-2512` as the sole initial candidate for continuity with the existing Ada plan. Bind the actual weight/tokenizer artifact hashes, quantization, server build, context/decoding settings, harness commit and verifier revision from the running configuration before qualification. A model name is not a version pin. Qwen's historical completion count is insufficient grounds to switch; no new model search is justified by this review.

Advance immediately through these gates:

1. Rewrite the B spine and primary hypotheses, update related work and v2 references, and replace H2 with the ridge equivalence check. Finish already authorized local A close-out work without waiting for an outside reader to return before beginning independent B design work.
2. Implement U end-to-end, the correctly scoped population discrepancy calculation, and complete three-leaf records through the real fork path. Preserve refusal of unimplemented live phases. Add the matched reserve/VOI baseline and charge total costs.
3. Pass task witnesses, bind all immutable runtime/task/evaluator/split/provenance artifacts, and implement phase-specific admission checks. The decision YAML accompanying this report supplies design choices; it does not manufacture these artifacts or authorize execution.
4. Run the bounded screen as soon as qualified and authorized; run the pilot as soon as the screen passes. Predeclare screen operability/reachability rules before collecting it. In the pilot check temporal decision room, repeated-myopic/reserve competition, harm, sensitivity and cost. Allow one substantive repair pass and one independent challenge; do not launch an indefinite search.
5. Decide COMBINE or CORE_ONLY before confirmatory outcomes. If N2 fails, do not automatically assert N1 alone is conference-worthy: require a separate substantive novelty case or release a narrower technical report. Freeze a final design and budget before final collection.

The Oct 3/Oct 17/Nov 14/Nov 30/Dec 7 dates are planning history, not permission gates or reasons to wait. ICML 2027 is the chosen target now, but an official 2027 CFP/deadline could not be verified in this review. The official [2026 CFP](https://icml.cc/Conferences/2026/CallForPapers) is only a development-format reference, not authority for 2027 deadlines or rules.

## Saved decisions and verification

`protocols/paper_b/design_decisions_20260927.yaml` records these prospective choices separately from the active launch contract. The active contract remains draft: final runtime hashes, split artifacts and qualification evidence are genuinely missing, and its one-step estimand must be revised deliberately for N2. Keeping these bindings empty is honest; the choices above are no longer deferred. Apply them in the next contract implementation pass with fresh binding digests, never by rewriting historical signed records.

New local validation is in `results/validation_logs/B_decision_review_20260927/`: 49 existing control tests passed; `make check-split` and `git diff --check` passed; the decision YAML parsed and its leaf budget reconciled; the analytic diagnostic confirms ridge equivalence and the audit/concentration calculations; the draft qualification attempt refused as expected. No live model experiment, measured p, outside-reader approval, independent review, merge, release or submission is represented by this decision report.
