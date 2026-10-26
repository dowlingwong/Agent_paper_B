# Proposed theory corrections — 27 October 2026

AI-assisted proposals for author proof check; **not adopted, not author checked and not manuscript claims**. The original T2/T4 claims remain unedited. Sources: `docs/r1/theory/T2_DERIVATIONS.md` §§2–3, 6; `T4_FEEDBACK_PROPOSER.md` §§4, 6; independent `T_AUDIT_20261027.md` and packets P01, P02, P05, P08, P10. These statements do not authorize experiments or a protocol change.

## T2 Proposition 1: threshold and degenerate cases

**Proposed statement.** Let Δ ∼ N(μ,τ²), H = Δ + ε with ε ∼ N(0,σ²) independent, τ>0 and σ>0. Among measurable keep/discard decisions, keep iff E[Δ|H]>0, equivalently H>t*=−μσ²/τ², maximizes E[Δ·keep]. For z=(t−μ)/√(τ²+σ²), its threshold value is μΦ(−z)+τ²φ(z)/√(τ²+σ²). The zero threshold is optimal iff μ=0. For a fixed nonzero Δ, the sign error probability is Φ(−|Δ|/σ). At σ=0 and τ>0, threshold zero is optimal for every μ; the original assertion that every negative threshold is optimal is removed. At τ=0 the threshold expression does not apply; use the known-mean optimal action, with ties arbitrary at μ=0.

**Check:** derive the posterior mean and differentiate threshold value; handle σ=0 and Δ=0 separately. The author should verify how strict ties and all degenerate cases are stated.

## T2 Proposition 2: verify value

**Proposed statement.** Under the independent Gaussian increment, campaign training/split errors and fresh replicate errors of T2 §1, with fixed-policy reuse of the campaign split error or vary-policy fresh split draws, let r be a positive integer and, conditional almost surely on H, m=E[Δ|H], v=Var(Δ|H), and q²=Var(E[Δ|H,D̄]|H). Compare the best Bayes keep/discard decision using H alone against the updated Bayes decision using H and the verify data. For q>0 the Bayes-response value of information is q[φ(|m|/q)−(|m|/q)Φ(−|m|/q)]; at q=0 it is zero by continuity. For fixed q it is maximal at m=0 and decreases in |m|. For nested independent verify samples it is nondecreasing with sample count, but **diminishing returns in sample count are not asserted in general**; the audit supplies a counterexample. The expression is for the Bayes response, not automatically the frozen response.

**Check:** truncated-normal identity; nested-information monotonicity; audit's counterexample and the special m=0 concavity case.

## T2 Proposition 5: priced index, not hard-budget optimality

**Proposed statement.** In the one-step priced comparison, if a verify operation consumes 2r runs, has conditional Bayes-response value VoI_r and the externally fixed Lagrangian price is g per run, its net value relative to not verifying is VoI_r−2rg. The index verifies when this is positive and the action is feasible. Under the Gaussian assumptions of Proposition 2, VoI_r ≤ √v φ(0), so the index never verifies when 2rg ≥ √v φ(0). This does **not** establish optimality under a finite hard budget, an evolving incumbent, or a call cap; those require additional state and continuation analysis.

**Check:** verify the cost accounting and response implementation, equality/ties, and the distinction between fixed price and state-dependent opportunity cost.

## T4 Proposition 8: screening

**Option A — one-step statement.** At almost every supported pre-execution history in a specified information set, exclude duplicates and assume an integrable no-op mixture with Δ=H=0 on a no-op and independent Gaussian increment/noise on the non-inert event, with τ>0 and σ≥0. If no-op status is already measurable in the chosen information set, π is 0 or 1; a nontrivial mixture requires a coarser information set. For π=1 define V*=0; for τ=0 use the known-mean decision instead of a finite threshold. If both execute and skip are feasible, the best immediate execution payoff is V*−g and skipping pays zero. Execute for V*>g, skip for V*<g, and either at equality. Relative to always executing at the *same* pre-execution history, the immediate gain is (g−V*)⁺. This statement alone makes no trajectory-optimality or hard-budget claim.

**Option B — interventional continuation invariance.** Consider a finite-horizon controlled process with integrable additive priced rewards, regular conditional kernels and feasible non-anticipating policies. At every relevant supported pre-execution history, require both (i) after execution, conditional on each actually observed H, optimal continuation value is invariant across every feasible keep/discard intervention, including measurable H-dependent choices; and (ii) the conditional expectation of that common post-execution continuation equals optimal continuation under skip, with each branch's real information and policy class. The interventions include every observation disclosed by execution; skip is not given H. Under these sufficient value equalities, backward induction selects the Bayes keep at E2 and compares V*−g with zero at E1. Establish these equalities at all histories needed for induction; an equality averaged over H for fixed keep actions is insufficient. A summed campaign gain additionally requires proof that a coupling/common history law has the correct policy-specific conditional immediate-reward marginals at each stage, or a valid policy-specific performance identity. Without that proof retain only the conditional one-step gain.

**Check:** whether the strong intervention condition is scientifically plausible and empirically testable, no-op/duplicate treatment, support and the policy-induced history distribution.

## T4 Proposition 10(a): decision independence

**Proposed statement.** Under the fixed-horizon additive Lagrangian objective and the two conditional interventional continuation equalities in Option B above, the myopic rule is optimal by backward induction. This condition is stronger than observational equality conditioned on an execution result that a skip never reveals. Alternatively retain only the one-step/index claim in Option A and remove global DI optimality. Neither version proves a hard-budget optimum or a feedback effect.

**Check:** explicitly specify filtration, interventions, possible execute/skip information asymmetry and continuation policy class. The prospective C4 audited-increment endpoint is an empirical question, not proof that the assumption holds or fails.

**Author decisions:** choose Option A or a precisely stated Option B; approve or revise each corrected statement and proof before any theory claim enters the manuscript. No substantive claim in T2 or T4 was changed by this file.
