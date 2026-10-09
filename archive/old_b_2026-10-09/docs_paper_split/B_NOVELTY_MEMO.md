# B novelty memo — draft for author, 2026-09-26

> **27 September update:** The working verdict and additional timing prior are in [B_DECISIONS_20260927.md](B_DECISIONS_20260927.md). GO for bounded N2-led development with N1 validity constraints; current-paper novelty remains unestablished. Generic verification timing is already discussed in Strategic Verification for Long-Running LLM Agents; compare a reserve/VOI scheduler. The matched ridge advantage and action-value contrast are algebraically identical. These findings supersede any reading of the candidate “yes” labels below as an established novelty verdict.

This is a method-level reading memo, not an author novelty decision. All B
additions and their evaluation below are **PLANNED**. Public PDFs were downloaded
from arXiv; hashes/page counts are in `results/validation_logs/L7-sources.json`.
Page numbers below are PDF pages. The ETAAI overlap is recorded separately in
PRIOR_DISCLOSURE.md. No model or external review service was used.

## Nearest prior: Calibration Is Not Control (2606.21399)

**Branching and reconstruction.** Section 3, pp5–6, executes continue, the
benchmark intervention and quit from each selected prefix. On interactive
benchmarks it replays the original trajectory, checks step agreement and
explicitly discards mismatches; Appendix B.1/Fig.3, p17 repeats that rule.
Its 100% match rate is a property of retained rows, not an unconditional
reconstruction guarantee (pp6,17). Appendix B.6, p21 explicitly says each
branched action is executed once; B.7's 24-prefix shallow check repeats actions
twice and explains that deeper cached histories are truncated (p21).

**Estimand and controller.** Expected intervention advantage is the utility
difference versus continue (Eq.1, p4); scalar sufficiency preserves its sign
(Proposition 1, p4; Appendix A, pp15–17). The operational regret uses an oracle
that selects the best *realized* branch, not an oracle of known expected values
(§4.3 Eq.6, p7). The witness predicts action success from prefix-only features,
converts it to expected utility, subtracts a per-tree uncertainty penalty, and
selects the largest resulting utility (§4.1 Eqs.4–5, p6). Appendix B.5 specifies
200-tree, depth-6 random forests and feature dimensions (pp19–20). Thus neither
branch labels, action-conditioned learning, conservatism alone, nor failure-risk
insufficiency is a new B contribution relative to this paper (inference from
those stated methods).

**Costs, masks, splits, safety.** Utility includes intervention and step costs;
quit has utility zero (Appendix B.2/Table 3, pp17–18). Prefixes from one base
trajectory share a split (p6; B.3 p18); run-level paired bootstrap is explicit
(B.6 p21). The primary feature comparison is prefix-only; preview-aware
features are auxiliary (B.5 pp19–20). B.1 says “available actions” (p17), but I
did not find a separately formalized pre-action feasibility mask or an
unavailable-versus-missing-outcome rule in §§3–4/B.1–B.6. This is a limitation
of the inspected description, not proof that its implementation has no masks.
Its RF/LCB formula addresses estimated action uncertainty (§4.1 p6); no
coverage theorem for outcome-relevant reconstruction error was identified in
that section or Appendix A's sufficiency/abstraction results (pp15–17).

**Restored-state identification.** Yes, the empirical interpretation treats
validated reconstruction as the same decision state (p6; B.1 p17). That is an
inference about the role of its explicit reconstruction procedure, not an
assertion that it assumes physically perfect capture of every hidden layer.
Rejecting mismatches changes the retained target population; whether a remaining
hidden discrepancy matters is not answered by the reported retained match rate
(pp6/17; A's inference, not the prior's claim).

## Other nearby methods

| Paper | Method, reconstruction, estimand and controller | Costs, masks and safety boundary |
|---|---|---|
| Harness-R1, 2608.02276 | Same full task batch is rerun after a separately trained engineer installs lifecycle hooks; all original successes remain in the batch (§3.1–3.2, pp4–5). Reward is mean patched-minus-baseline reward, zero for invalid/incomplete patches (Eq.1 p5). It trains the editor by SFT then GRPO, caching baseline records (pp5–6); this is a transductive task-rerun objective, not a learned one-checkpoint verify gate (p5, inference from objective). Appendix C defines initialization, pre-decision, pre-action and post-feedback hooks (p17). | Hooks may block, rewrite or force actions where enabled; DBBench forbids SQL rewrites/forced commits (Appendix C p17). Task splits precede patch generation (Appendix D pp17–18). This is explicit action-interface restriction, not A/B's feasibility estimand. The method's reward has no separate complete execution-cost term (Eq.1 p5); this statement concerns that equation only. Negative valid-patch rewards and observed regressions are retained (pp17,21–22), not a no-harm guarantee. No hidden-state discrepancy allowance or mismatch-discard rule was found in §§3/C/D; same tasks control composition but are not a demonstrated restored-state identification theorem (p5). |
| Causal Agent Replay, 2606.08275 | Models the agent trajectory as an SCM; forces, resamples or swaps actions/observations/context/policy and runs stochastic continuations (§2 p2). Requires exact decision-state reconstruction and reports action-match fidelity (§3 p2). Contrastive effects are shifts from the observed run; the latest step with nonzero CI localizes commitment. Shapley uses uncached coalition rollouts and antithetic permutations (§4 p3). These are attribution procedures, not learned intervention allocation (inference from §4). | Monte Carlo is budget bounded with a circuit breaker (§4 p3); side-effecting real tools are out of scope and examples use mocks (§7 p5). No mask or quantitative hidden-state-error allowance was found in §§2–4/7; that is an inspected-text limitation. It explicitly relies on faithful reconstruction (§3 p2), while recognizing provider nondeterminism. No appendix is present in the five-page PDF; methods, validation and limitations were read (pp2–5). |
| The Replay Gap, 2608.08239 | Fresh containers replay pre-fork actions, check return codes, seed recorded history and continue with swap and same-model control arms at two fork positions (§3 p3). Measures trajectory, patch and correctness discrepancies, and compares log stitching against executed branches (§§4.1–4.5 pp4–6). Appendix B p9 gives 707/708 exact reconstructed branches by return-code agreement. Thus it tests static-replay identification rather than taking post-switch logged trajectories as valid (pp3,6). | Fixed step/context limits and serving configuration are reported (§3 p3); budget exhaustion is descriptive (§4.3 p5). There is no learned allocation controller in this design (§3 p3); no feasibility mask was found there. Appendix B p9 supports reconstruction only on checked returns, not every hidden layer (inference). The mismatch is counted; the text inspected does not explicitly say whether that one branch is excluded from every downstream table. No general harm-control guarantee is established by the descriptive outcome-flip counts (§4.2 p5). |
| Stage-Replay, 2607.28495 | Separates retained-live, incremental and fresh-prefill caches, with storage-isolated replicas and matched tokens/roles/positions/masks (§3.1–3.4 pp4–6). Tests fixed-prefix precision, prospective live/incremental agreement and whole-cache bidirectional transplantation (§3.5–3.7 pp7–8). Primary outputs are fidelity/disagreement and donor following, not controller value (pp6–8). It directly challenges restored-state identification: repeatability alone does not establish live-state fidelity (§5 pp12–13). | Exact integrity gates, no row exclusions in the 200-item matrices, explicit token caps and role-visibility masks are specified (pp4–6; contract Table3 p9). Those attention masks differ from pre-action feasibility masks (p4, inference). Outcome-conditioned and outcome-blind transplant strata have separate denominators and qualifications (pp7–8,11–14). No learned budget allocator or intervention no-harm result is claimed in these sections; this is an inspected-scope observation. No appendix is present in the 16-page PDF; methods pp4–9 and results/limitations pp10–14 were read. |

## Candidate incremental contributions and falsification

**N1 = yes: measurement-aware pessimism — PLANNED.** B would combine sampling
uncertainty with an explicitly sourced replay-discrepancy allowance, abstain
when the robust advantage does not clear the action/cost rule, and evaluate on
an original-root population with declared feasibility. The comparison must
include an otherwise matched sampling-only conservative controller: the prior
already has RF/LCB conservatism (§4.1 p6). A falsifying result is that, under
valid declared allowances in planted-defect worlds, the claimed robust lower
bound excludes the intended effect or a nominal harm guarantee fails its
specified error control. A valid engineering implementation that never improves
utility at matched cost would also falsify a practical-value claim. Understated
allowances are a sensitivity failure case, not evidence against a conditional
guarantee. This adds a measurement contract only if demonstrated; it is not
new merely because p is subtracted from an LCB.

**N2 = yes: three-leaf timing tree — PLANNED.** B would compare verify-now,
continue then conditionally verify/continue at a reachable second checkpoint,
and never verify, with action-dependent reachability, remaining-budget updates
and original-root denominators. This differs from the nearest prior's isolated
same-prefix three-action choice (§3 pp5–6; B.1 p17), although Harness-R1 already
has lifecycle-spanning stateful hooks (Appendix C p17; cases pp20–22); sequential
intervention in general cannot be claimed as new. A falsifying result is no
advantage over a capacity- and budget-matched repeated one-step rule in a world
with a prespecified valuable later opportunity, or a result that disappears
when unreachable descendants stay in the root denominator. Leakage between
siblings invalidates that evaluation rather than supporting a sequential claim.
Only schema/CPU fixtures are currently authorized; a sequential learner remains
behind the pilot gate.

**Author decision still needed:** whether these distinctions support a publishable
B contribution after a matched comparison and method-level independent review.
The author has chosen N1 and N2 for implementation; this memo does not reverse
those choices or award novelty, design readiness, safety or empirical success.
