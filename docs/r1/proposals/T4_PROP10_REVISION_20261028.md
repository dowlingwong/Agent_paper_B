# T4 Proposition 10 revision — one-step theorem, primitive sufficient condition, and two failure channels (28 October 2026)

AI-assisted proposal (Claude, chat session), drafted at the author's request after the author chose the combined route (PLAN §10 R1-T4-DI-FIX).

**Status after the proof check (revision 3, 16 Nov 2026).** The author's proof check is recorded in PLAN §10 **R1-T4-PROOF-CHECK** (16 Nov). It approves the main conclusions and proofs of Propositions 8′, 10(a′) and 10(c) in revision 2 (this file @ `main` `9ae6d877`), subject to four errata. It also decides R1 (option (ii)), R4 (20 proposals) and the §6 checks (five offline checks enter the plan; the C4 forced-branch test is deferred).
- Revision 3 applies exactly those errata and decisions, as an independently reviewed unit. The mapping is in §9. The Mac agent (Claude, AI-assisted) prepared it.
- Changes beyond the row are editorial only, and §9 lists them.
- `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` and `T2_DERIVATIONS.md` are not changed by this unit.
- This file authorizes no experiment, run or protocol change. Each §6 check is carried out as its own unit.

**Revision 2 (28 Oct).** The first version was reviewed independently (`docs/r1/reviews/T4_PROP10_REVISION_REVIEW_20261028.md`). That review found three blocking issues:
- **B1:** duplicate and no-op status depend on the policy;
- **B2:** T4 Proposition 9's noise model also violates (NF);
- **B3:** the summed gain needs (NF) and (NI) together, not (NF) alone.

It also listed minor findings. All are addressed below; the mapping is in §8.

Builds on: `docs/r1/theory/T_AUDIT_20261027.md` (Propositions 8 and 10), `docs/r1/proposals/THEORY_CORRECTIONS_20261027.md` (Options A and B), `docs/r1/reviews/LOCAL_THEORY_CORRECTIONS_REVIEW_20261027.md` (finding 1: state a primitive sufficient condition instead of value equalities).

## 0. What changes and why

The audit found a gap in T4 Proposition 10(a). Its decision-independence (DI) condition conditions on Δ̂_n even after a skip, when Δ̂_n is never observed. The branch-copy proof therefore silently gives both branches the same information. Executing has **information value** that the myopic rule ignores, and DI as written does not exclude it. The proof also uses an observational conditional law where an interventional one is needed. Separately, the summed gain in Proposition 8 adds expectations taken under different policy-induced history laws.

This proposal replaces Propositions 8 and 10(a) with the following statements and adds one example:

| New | Role | Replaces |
|---|---|---|
| **Proposition 8′** | One-step (index) theorem, valid without any independence condition | Proposition 8's statement |
| **Proposition 10(a′)** | Global optimality of the myopic rule under two primitive conditions, **no feedback (NF)** and **no information (NI)** | Proposition 10(a) |
| Proposition 10(b) | Unchanged: failure of NF can cost an unbounded amount | — |
| **Proposition 10(c)** | New: failure of NI, with NF intact, can cost an unbounded amount | — |

Read together, these say that the loop is a **sequence of independent one-step decisions**, for which myopic play is optimal, when nothing responds to the control plane's decisions and nothing it observes predicts later outcomes. Each condition can fail on its own, and each failure can make myopic play arbitrarily bad. Hard run budgets are not covered (§5, R2).

## 1. Setting and information

Trials n = 1, …, N, where N is fixed (the LLM-call cap).

**Exogenous variables of trial n.** W_n = (x_n, Y_n), where:
- x_n is the proposal;
- the outcome tuple is Y_n = (1{I_n}, Δ_n, η_n);
- 1{I_n} is the no-op indicator; on I_n, Δ_n = 0;
- Δ_n is the true increment;
- η_n is the comparison noise.

An execution reveals H_n = Δ_n + η_n on I_nᶜ. On a bit-exact node (T4 §1) H_n = 0 on I_n; on other nodes H_n = η_n there. On a bit-exact node, {H_n = 0} identifies I_n almost surely only if, in addition, the comparison value on I_nᶜ has no probability mass at zero: P(Δ_n + η_n = 0, I_nᶜ | O_n) = 0. **Execution reveals only H_n.** Any other run output that predicts later increments (absolute metric, learning curves, wall time, crashes) must be included in H_n, and hence in Y_n, for §3 to apply.

**Duplicates and no-ops.** In T4, duplicate status D_n and no-op status I_n are defined relative to earlier *evaluated* configurations and to the current incumbent. Both therefore depend on past decisions. §3 adds an assumption (NF-c) that removes this dependence; §2 needs none.

**Decisions.** a_n ∈ {0, 1} at E1 and k_n ∈ {0, 1} at E2, with k_n ≤ a_n. U collects **all** control-plane randomness. That includes the policy's own randomization, the memory summariser's sampling, the forecaster's sampling, and any seeds or caches the control plane draws. No independence between U and W_{1:N} is assumed here. That assumption is part of (NF) in §3, and Proposition 8′ does not need it.

**Information.** The pre-execution information is O_n = σ(x_{1:n}, (a_j, k_j, a_j H_j)_{j<n}, U).
- After a skip nothing more is observed.
- After an execution H_n is observed, and k_n may depend on O_n ∨ σ(H_n).
- Because O_n contains both a_j and a_j H_j, an executed result of 0 is distinguishable from a skip.
- The displayed memory and the remaining budgets are functions of O_n.
- **A skip does not reveal H_n.** This is where T4's DI went wrong.

**Policies.** Non-anticipating: a_n is O_n-measurable; k_n is (O_n ∨ σ(H_n))-measurable and is 0 when a_n = 0. Both actions are feasible at every history (the Lagrangian relaxation; no hard budget).

**Objective.** J_g(π) = E^π[Σ_{n ≤ N} (Δ_n k_n − g a_n)], with g ≥ 0 fixed and E|Δ_n| < ∞.

**Per-proposal quantities.** H_n is defined as a potential outcome whether or not it is observed. Define, on the whole space,
- m_n := E[Δ_n | O_n ∨ σ(H_n)], the posterior mean of the increment given the pre-execution information and the result;
- V*_n := E[m_n⁺ | O_n], the best expected keep value after an execution.

E|Δ_n| < ∞ gives E m_n⁺ < ∞.

**Gaussian closed form.** The closed form below is a **new assumption**, stated relative to O_n. O_n is coarser than T4's F_n and depends on the policy, so a Gaussian law given F_n generally becomes a mixture given O_n. Under (NF) and (NI) the relevant σ-field is σ(x_{1:n}) for every policy (Proposition 10(a′).1), and the issue disappears. Suppose, at a given history, the conditional law given O_n satisfies T4's (A1)–(A2) with τ_n > 0, on a bit-exact node with a continuous comparison law on I_nᶜ. Then {H_n = 0} identifies I_n almost surely, and on {H_n ≠ 0}, m_n > 0 ⟺ H_n > t*_n with t*_n = −μ_n σ_n²/τ_n². This gives V*_n = (1 − π_n) V(t*_n; μ_n, τ_n, σ_n) (Proposition 6). On non-bit-exact nodes, or for metrics on a finite lattice, V*_n is a mixture posterior value with no such closed form.

## 2. Proposition 8′ — the one-step (index) theorem

**Statement.** Assume E|Δ_n| < ∞. No independence between U and W_{1:N} is needed. Almost surely on O_n:
1. **E2.** For every admissible k_n, E[Δ_n k_n | O_n] ≤ a_n V*_n. Equality holds for k_n = a_n · 1{m_n > 0}. Under the Gaussian closed form of §1, this is the Bayes threshold rule of Proposition 6 on {H_n ≠ 0}; on {H_n = 0} every k has value 0.
2. **E1.** The best immediate payoff of executing is V*_n − g; skipping pays 0. Execute if V*_n > g, skip if V*_n < g, either at equality. The best immediate conditional payoff is (V*_n − g)⁺.
3. **Gain at the same history.** Relative to "always execute, then apply part 1", the immediate conditional gain at this history is (g − V*_n)⁺.
4. **Edge cases.**
   - If π_n = 1 (a detectable no-op), V*_n = 0, and skipping is optimal for g > 0 (a tie at g = 0).
   - If τ_n = 0 on I_nᶜ (known increment μ_n), keep iff m_n > 0 after execution, and V*_n = (1 − π_n) μ_n⁺.
     - On a bit-exact node, H_n separates I_n from I_nᶜ (so the rule keeps exactly when μ_n > 0 and the proposal is not a no-op) only if the comparison value μ_n + η_n has no probability mass at zero given O_n and I_nᶜ. μ_n ≠ 0 alone is not enough.
     - If μ_n = 0, then Δ_n = 0 almost surely and V*_n = 0. Keep and discard are equivalent after an execution. But execute and skip tie only at g = 0: for g > 0, skipping is strictly better, because executing pays −g.

**Proof.**
- *Part 1.* Since a_n is O_n-measurable and k_n = a_n k_n is (O_n ∨ σ(H_n))-measurable, the tower property gives E[Δ_n k_n | O_n] = E[k_n m_n | O_n] ≤ a_n E[m_n⁺ | O_n] = a_n V*_n, with equality for k_n = a_n 1{m_n > 0}.
- *Parts 2 and 3.* Compare V*_n − g with 0, and use max(V*_n − g, 0) − (V*_n − g) = (g − V*_n)⁺.
- *Part 4.* π_n = 1 gives Δ_n = 0 a.s. τ_n = 0 makes Δ_n = μ_n known on I_nᶜ. So Δ_n ∈ {0, μ_n} has the sign of μ_n, and V*_n = E[m_n⁺ | O_n] = (1 − π_n) μ_n⁺. μ_n = 0 gives Δ_n = 0 a.s., so V*_n = 0, and part 2 gives "skip" strictly for g > 0. ∎

The proof uses only the tower property and the measurability of a_n and k_n. It does not use U ⊥ W_{1:N}.

**What it does not say.** Nothing about later trials: no trajectory optimality, no campaign gain and no hard-budget statement. Every campaign-level use of the screening gain needs §3, and §5 R3 states what holds without it.

## 3. Proposition 10(a′) — when myopic play is globally optimal

**Conditions.** These are primitive conditions with testable implications (§6). (NF) quantifies over all policies, so it is not itself directly checkable.

- **(NF) No feedback.** The joint law of the exogenous sequence W_{1:N} is the same under every feasible policy, and U is independent of W_{1:N}. This is the only place the independence of U is assumed (revision 3 moved it here from §1). (NF) holds if (NF-a)–(NF-c) below hold and U ⊥ W_{1:N}; these are also the ways it typically fails:
  - **(NF-a) Non-reactive proposer.** The manager's proposals do not depend on which edits were executed or kept, or on what was displayed.
  - **(NF-b) Non-interacting edits and incumbent-independent noise.** An edit's true increment does not depend on which earlier edits were kept, and the joint law of the comparison noises (η_m)_m, including its relation to the other components of W, does not depend on the incumbent's identity or history. This is a **new, substantive assumption**. T2 §1's additive model is a telescoping value identity and does not imply it, and T4 §8 notes that non-interaction fails on `digits_mlp`.
  - **(NF-c) Policy-invariant trial sequence.** Duplicate and no-op status are functions of x_{1:n} alone, the same under every policy, and filtered proposals do not use up the horizon. Alternatively, under every policy, no earlier effective configuration is re-proposed within the horizon (this also rules out no-ops that depend on the incumbent, i.e. it forces π_n = 0). Either version excludes the pattern "an edit re-proposed after a skip is a fresh trial, but re-proposed after an execution is a duplicate". In the C3 pilot, 727 of 841 rule-detectable proposals were duplicates (T4 §1), so this pattern is common in our data.
- **(NI) No information.** Under that law, for every n, Y_n = (1{I_n}, Δ_n, η_n) is conditionally independent of (Y_j)_{j<n} given x_{1:n}. In words: no earlier result carries information about this trial's outcome beyond what the whole proposal history says.
  - No separate condition linking later proposals to earlier outcomes is needed, because the proof uses (NI) only at the current trial, conditional on x_{1:n}.
  - If proposals depend on earlier outcomes exogenously, conditioning on x_{1:n} absorbs that dependence. That dependence may itself make (NI) fail, since x_n can then act as a collider.
  - Exact repeats that are kept in the sequence violate (NI): on a bit-exact node at fixed seeds, Y_n = Y_j when x_n = x_j.

**Statement.** Under the setting of §1, (NF) and (NI):
1. For every n, the per-proposal quantities depend on the history only through the proposals: m_n = E[Δ_n | x_{1:n}, H_n] and V*_n = E[m_n⁺ | x_{1:n}], almost surely.
2. The myopic policy of Proposition 8′ (execute iff V*_n > g, then keep iff m_n > 0) maximises J_g over all feasible non-anticipating policies, randomized ones included. Its value is J_g(myopic) = Σ_n E[(V*_n − g)⁺].
3. J_g(myopic) − J_g(always execute, keep by Proposition 8′.1) = Σ_n E[(g − V*_n)⁺], with the expectation taken under the common law of x_{1:N}.

**Proof.**

*Step 1 (conditional independence).* By induction on j:
- a_j is O_j-measurable;
- k_j is (O_j ∨ σ(H_j))-measurable;
- H_j is a function of Y_j.

Hence O_n ⊆ G_n := σ(x_{1:n}, Y_{<n}, U).
- (NF) gives U ⊥ W_{1:N}, so by weak union U ⊥ (Y_n, Y_{<n}) | x_{1:n}, and again by weak union U ⊥ Y_n | (x_{1:n}, Y_{<n}).
- (NI) gives Y_n ⊥ Y_{<n} | x_{1:n}.
- Together (contraction), Y_n ⊥ (Y_{<n}, U) | x_{1:n}, that is, Y_n ⊥ G_n | x_{1:n}.

Since σ(x_{1:n}) ⊆ O_n ⊆ G_n, the tower property gives, for every bounded f, E[f(Y_n) | O_n] = E[E[f(Y_n) | G_n] | O_n] = E[E[f(Y_n) | x_{1:n}] | O_n] = E[f(Y_n) | x_{1:n}]. So (Δ_n, H_n) ⊥ O_n | x_{1:n}, which is part 1. (Revision 2 called this step weak union; it is the tower property.) The functions m_n(x_{1:n}, h) and V*_n(x_{1:n}) exist by the Doob–Dynkin lemma. Their versions are unique up to null sets of the law of (x_{1:n}, H_n), and (NF) makes that law the same for every policy.

*Step 2 (per-trial bound for an arbitrary policy).* This is Proposition 8′.1 and 8′.2 with V*_n now a function of x_{1:n}: E[Δ_n k_n − g a_n | O_n] ≤ a_n (V*_n − g) ≤ (V*_n − g)⁺.

*Step 3 (attainment and summation).*
- The myopic policy attains equality in both inequalities of Step 2 at every n.
- The per-trial bounds can be added across trials for two reasons. (NF) gives every policy the same law of the proposal sequence x_{1:N}. (NI), through part 1, means that the executed history, given the proposal history, does not change the current posterior. So each V*_n is the same function of x_{1:n} under every policy, with the same law. Σ_n E[(V*_n − g)⁺] therefore does not depend on the policy and bounds J_g(π) for every π. This gives part 2.
- For part 3: "always execute" has finer information, but by part 1 its V*_n is the same function of x_{1:n}, so it earns Σ_n E[V*_n − g] under the same law. ∎

**Notes.**
- The proof needs no backward induction and no value-function equality. It is a per-trial bound that a single policy attains at every trial simultaneously. This is the primitive sufficient condition that the review's finding 1 asked for.
- **Testable implication of part 1.** Under (NF) and (NI), the **Bayes** forecast given the whole proposal history x_{1:n} gains nothing from executed results. Suppose two forecasters are both given x_{1:n}, and the one also shown past results improves out of sample beyond estimation error. That is evidence against (NI). The absence of such an improvement does not establish (NI). The test also says nothing about a forecaster that sees only x_n: past results can proxy for x_{1:n−1}, so they may help it even under (NI).
- **Contrapositive (replaces T4 §6's "when RL is needed").** For any policy to beat the myopic rule, (NF) or (NI) must fail. This failure is necessary, not sufficient. Propositions 10(b) and 10(c) show that, when either fails, the gain can be unbounded. Nothing here says that RL in particular is needed.

## 4. Failure of each condition

**Proposition 10(b) (unchanged; NF fails).** σ → 0, g = 0, N = 2, and trial 1 has a known Δ₁ = −α < 0. Keeping it shifts trial 2's increment law from N(0, τ²) to N(β, τ²). With τ = 1 and β = 2, the myopic loss is 2Φ(2) + φ(2) − φ(0) − α = 1.60955 − α for α < 1.60955, and it grows without bound in β. (NF) fails because the keep decision changes the proposal law. (NI) holds under each policy's law; there is no common law to state it under. Audit status: correct as an existence example.

**Proposition 10(c) (new; NI fails, NF holds).** There are loops satisfying (NF) whose myopic policy loses an amount that grows without bound.

*Example.* N = 2. The two proposals x₁ and x₂ are fixed in advance, and the two edits do not interact. They share a latent node sensitivity θ ∼ N(0, 1).
- Trial 1 is a small probe, Δ₁ = αθ, observed without noise if executed (σ₁ = 0).
- Trial 2 is a large edit, Δ₂ = βθ, whether or not trial 1 was kept, observed with noise σ₂ = κβ, κ > 0.
- No-op probabilities are 0.

(NF) holds: the proposals are fixed, the law of (θ, noise) does not respond to any decision, and U ⊥ W. (NI) fails: H₁ = αθ predicts Y₂.

- **Myopic.** V*₁ = E[(αθ)⁺] = αφ(0). Take g > αφ(0), so trial 1 is skipped and θ stays unobserved. At trial 2 the myopic rule uses the uninformed information σ(x_{1:2}): Δ₂ ∼ N(0, β²), so t* = 0 and V*₂ = βφ(0)/√(1 + κ²). Hence J_g(myopic) = (βφ(0)/√(1 + κ²) − g)⁺.
- **Probe-first.** Execute trial 1 (pay g). Then a₁H₁ = αθ enters O₂, so θ is known at trial 2. Keep trial 1 iff θ > 0, worth αφ(0). Trial 2 is then the τ = 0 case of 8′.4: execute and keep iff βθ > g, worth E[(βθ − g)⁺] = β[φ(g/β) − (g/β) Φ̄(g/β)].
- **Optimality gap.** With N = 2 and (NF), the only non-myopic choice is a₁. So the optimum is max(J(myopic), J(probe-first)), and the exact optimality gap of the myopic rule is the positive part

  gap = (J_g(probe-first) − J_g(myopic))⁺, where J_g(probe-first) − J_g(myopic) = αφ(0) − g + E[(βθ − g)⁺] − (βφ(0)/√(1 + κ²) − g)⁺.

  The difference itself can be negative, in which case myopic play is optimal and the gap is 0. For example, at α = 1, β = 0.1, g = 0.5, κ = 1 the difference is about −0.1011 (J(myopic) = 0, J(probe-first) ≈ −0.1011), so the gap is 0. In all four rows of the table below the difference is positive, so there it equals the gap.

  For fixed α, g and κ > 0 the difference is βφ(0)(1 − 1/√(1 + κ²)) + αφ(0) − g/2 + o(1) as β → ∞. It grows linearly in β, with slope ≈ 0.1168 at κ = 1, so the gap is unbounded. At κ = 0 it stays bounded, so κ > 0 is needed.

  **What the paper keeps** (R1-T4-PROOF-CHECK): the existence statement. Even when (NF) holds, there are examples in which (NI) fails and the myopic rule's loss is arbitrarily large.

*Numbers.* α = 1, g = 0.5, κ = 1. Closed form, with a Monte Carlo check (2·10⁶ draws, common random numbers, mean ± s.e.) in parentheses:

| β | J(myopic) | J(probe-first) | gap (difference > 0) |
|---|---|---|---|
| 2 | 0.0642 (0.0646 ± 0.0009) | 0.4716 (0.4724 ± 0.0011) | 0.4074 (0.4078 ± 0.0005) |
| 10 | 2.3209 (2.3232 ± 0.0046) | 3.6434 (3.6466 ± 0.0044) | 1.3224 (1.3234 ± 0.0020) |
| 100 | 27.7095 (27.7320 ± 0.0459) | 39.5437 (39.5753 ± 0.0416) | 11.8342 (11.8433 ± 0.0197) |
| 1000 | 281.5948 (281.8200 ± 0.4586) | 398.5913 (398.9061 ± 0.4133) | 116.9965 (117.0861 ± 0.1967) |

Script and output: `docs/r1/proposals/t4_prop10_revision_20261028/ex10c.py`, `ex10c_output.txt`. The author's proof check re-ran the script, and its output matched the repository file byte for byte. This unit re-ran it too (Python 3.13, NumPy 2.4.4, SciPy 1.17.1), with the same result. The script is unchanged in revision 3; the β = 0.1 value above comes from its `closed_form` function, with the Monte Carlo part not run.

*Reading.* The myopic rule prices a run only by its immediate keep value, never by the information it reveals. Here trial 1 is worth running only because it tells the loop whether trial 2 is good.

This is a **stylized** version of a cheap edit to a key followed by a larger edit to the same key on the same node. It satisfies (NF) only under three conditions:
- the edits are relative steps;
- the response is linear in the key, so Δ₂ = βθ whether or not edit 1 was kept;
- the manager proposes edit 2 regardless of edit 1's outcome.

With "set key = v" semantics, Δ₂ depends on whether edit 1 was kept, and (NF) fails as well.

A Bayes-updating myopic rule does not fix this. It would use H₁ if it had it, but it never pays to get it.

## 5. Remarks for the author's check

- **R1. T4 Proposition 9's noise model violates both (NI) and (NF), and it is inconsistent with T4's (A2). This is an inconsistency inside T4.** Proposition 9 writes the comparison as Δ̂_n = Δ_n + ε_n − e, where e is the recorded incumbent's error. So η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n.
  - **(NI) fails.** Within an incumbent spell, Cov(η_n, η_j | x) = (1 − ϱ_n)(1 − ϱ_j) Var(e) > 0.
  - **(NF) fails.** A keep replaces e by the selected error e′ = ε_kept, which Proposition 9 shows is biased upward. So the law of later η_m depends on the keep policy. In the independent review's simulation (σ = 1, ϱ = 0.3, Δ₁ ∼ N(0, 0.25)), E[η₂] is 0.001 under "never keep" and −0.303 under the default keep rule ρ.
  - **(A2) fails.** (A2) ("η_n | F_n, Δ_n ∼ N(0, σ_n²)") holds at the first comparison against a fresh incumbent. It fails later in the same spell and after any keep. Knowing e is not enough: η_n then has mean (ϱ_n − 1)e ≠ 0, and (A2) holds only for the corrected comparison Δ̂_n + (1 − ϱ_n)e.

  Two consistent options:
  - (i) State (A2) and this proposal for comparisons against an incumbent whose error is re-drawn independently at each comparison (for example, re-measured on fresh seeds), or known and subtracted. This option is needed for (NF) as well as (NI). Re-measuring costs runs, which changes the g-accounting.
  - (ii) Keep Proposition 9's model and treat e as a shared latent variable. Then Propositions 6–8 condition on the posterior of e, and the loop lies **entirely outside** Proposition 10(a′). KG verify is an information action analogous to the one Proposition 10(c) prices.

  Separately, on bit-exact nodes at fixed seeds, η_n is deterministic per configuration and seed, so similar configurations probably have correlated noise. (NI) may then fail generically, beyond the shared-e mechanism.

  **Author decision (R1-T4-PROOF-CHECK): option (ii).**
  - The incumbent error e is treated as a shared latent variable, and the values of Proposition 8′ are computed conditional on the posterior of e. Proposition 8′ applies as stated, because m_n and V*_n condition on O_n, which carries the information about e.
  - The actual loop lies outside the scope of Proposition 10(a′).
  - Campaign gains are reported as measured, not derived (R3).
- **R2. Hard budget.** All statements are for a fixed price g with both actions always feasible. Under the hard budget E[Σ a_n] ≤ W, or with freed runs re-spent, the opportunity cost of a run depends on the remaining budget and the incumbent. T4 §1's weak-duality remark is then the only statement. This is the third channel (budget coupling). It stays a declared sensitivity, not a theorem.
- **R3. Summed gains.**
  - **Proposition 8's campaign sum E[Σ(g − V*_n)⁺] is valid under (NF) and (NI) together** (Proposition 10(a′).3). It is **not** valid under (NF) alone, where the screening gain can be negative. In the 10(c) example with α = 1, β = 10, κ = 1, g = 0.5:
    - J(myopic) = 2.3209 and J(always execute, Bayes keep) = 3.3884, so the actual screening gain is −1.0674;
    - the formula with the myopic V*'s gives +0.1011.
  - **Corollary 7a** holds under (NF) alone if the execution rule does not depend on past keeps (so both compared policies have the same O_n), and if (A1)–(A2) hold relative to O_n.
  - **Without (NF) and (NI),** report campaign gains as measured, not derived.
- **R4. C3 gate.** The gate scales the offline one-step gain to a 20-run campaign. That scaling is a declared definition and stays unchanged. Under (NF) and (NI) it matches Proposition 10(a′).3 if the 20 decisions have a common per-decision mean. Otherwise it has **no guaranteed sign relation** to the campaign gain (R3), and the manuscript says so. 10(a′).3 sums over proposals, not runs, and the two differ under skipping.

  **Author decision (R1-T4-PROOF-CHECK): 20 counts proposals.** The gate's scaling is 20 × the weighted mean utility per recorded proposal. This matches the 22 Oct main analysis (PLAN "Run accounting in the 20-run scaling", option A) and `r1/c3/offline_eval.py` (`CAMPAIGN_RUNS = 20`; the primary accounting is 20 × Σ w·r / Σ w over recorded proposals). The paper also notes that the actual sweep sets its budget as 20 worker runs.
- **R5. T4 §6 "Reading."** Replace three claims, which the audit found do not follow from the theorem or the example, with the corrected contrapositive in §3:
  - "Statement (b) is the precise scope of RL";
  - the RL-necessity reading;
  - "an observed DI violation that is small means stage 3 … can be dropped".
- **R6. Offline-evaluation bias.** Sweep tables execute every proposal, so a skipping controller evaluated offline sees later histories containing results it would not have observed online. Its offline information contains its online information.
  - For a **Bayes** myopic controller under (NF), Jensen's inequality applied twice gives E[(V*_n^off − g)⁺] ≥ E[(V*_n^on − g)⁺]: offline evaluation of skipping is optimistic. The bias is zero under (NI), by Proposition 10(a′).1.
  - For a learned, non-Bayes forecaster the sign is not determined, even under (NI).
  - Arms whose forecasts use proposals only (A1, A1-ctx) are unaffected under (NF), provided their E1 decisions do not use past results through the budget line, the incumbent or the display.

## 6. Empirical counterparts

**Author decision (R1-T4-PROOF-CHECK).** Five offline checks enter the plan:
1. the memory `none` display audit;
2. the duplicate re-proposal count (NF-c);
3. the (NI) masking test with the full proposal history held fixed;
4. the residual test within an incumbent spell and after keeps (the R1 mechanism);
5. the (NF-b) interaction test on pairs the sweeps already provide.

The C4 forced-branch test is deferred. This file does not start any check; each is carried out as its own unit. The table keeps its revision-2 content, with a status column added.


| Condition | Observable consequence | Test | Status |
|---|---|---|---|
| (NF-a), keep channel | the proposal law after a forced keep equals the law after a forced discard, at matched histories | C4 decision-independence test on forced-decision branch pairs (E2). This tests only the keep channel: it does not test execute vs skip, or what is displayed | **deferred** (C4) |
| (NF-a), display | under memory `none` the manager is shown nothing that depends on past decisions | **check item:** verify what the harness displays under `none`. If it still shows the incumbent configuration, (NF-a) fails there too. Then compare memory `none` vs `append_only_summary` (D24) | **in the plan** (check 1) |
| (NF-b), increments | an edit's audited increment does not depend on which earlier edits were kept | interaction check on audited pairs of edits, applied over different incumbents, where the sweep provides them | **in the plan** (check 5) |
| (NF-c) | duplicate and no-op status do not depend on the policy | count, in sweep campaigns, re-proposals of configurations that a skip would have left unevaluated | **in the plan** (check 2) |
| (NI) | showing past results to a Bayes-style forecaster given x_{1:n} does not improve it (Proposition 10(a′).1) | masking test: the C3 forecaster with vs without executed results in its history, both given the same proposal history, compared out of sample on RPS and decision utility. Offline; no new labels. An improvement beyond estimation error is evidence against (NI); its absence does not establish (NI) | **in the plan** (check 3) |
| (NI) and (NF) via shared e (R1) | comparison residuals are correlated within an incumbent spell, and have a negative mean after keeps | residual correlation within vs across incumbent spells; mean residual after keeps vs at fresh incumbents | **in the plan** (check 4) |

## 7. Open items for the author

All four items were decided in R1-T4-PROOF-CHECK (16 Nov 2026):
1. Propositions 8′, 10(a′) and 10(c) and their proofs: approved, with the errata applied in revision 3 (§9).
2. R1: option (ii).
3. R4: 20 counts proposals.
4. §6: five offline checks enter the plan; the C4 forced-branch test is deferred.

## 8. Review findings and how revision 2 addresses them

| Finding | Where addressed |
|---|---|
| B1 duplicate/no-op filtering depends on the policy | §1 "Duplicates and no-ops"; (NF-c); (NI) note on kept repeats; §6 (NF-c) row |
| B2 Proposition 9's model violates (NF) too | R1 rewritten; §6 last row |
| B3 R3 wrong under (NF) alone | R3 rewritten with the 10(c) counterexample; script prints the check |
| 1a m_n defined only on {a_n = 1} | §1: m_n defined on the whole space; 8′.1 as an a.s. inequality |
| 1b ⟺ fails on {H_n = 0}, undefined at τ = 0 | §1 Gaussian closed form; 8′.1 |
| 1c bit-exact and continuous-metric scope | §1 Gaussian closed form |
| 1d (A1)–(A2) relative to O_n is a new assumption | §1 Gaussian closed form |
| 1e a.s. phrasing | 8′ statement |
| 1f execution must reveal only H_n | §1 |
| U must contain all control-plane randomness | §1 Decisions |
| 2a non-interaction mis-cited to T2 §1 | (NF-b) |
| 2b noise must not depend on the incumbent | (NF-b) |
| §3 wording of the removed (NI) clause | (NI) notes |
| 4a exact optimality gap | 10(c) "Optimality gap" |
| 4b Monte Carlo standard errors | 10(c) table; CRN in the script |
| 4c fixed proposals, non-interacting edits | 10(c) example |
| 4d same-key reading conditions | 10(c) Reading |
| 4e script path | repository path, committed with this file |
| 10(b) (NI) phrasing | 10(b) |
| R1 "unless e is known", "exactly the kind", fixed-seed correlation | R1 |
| R4 sign; trials vs runs | R4; §7 item 3 |
| R6 Bayes qualifier and conditions | R6 |
| 6a "contextual bandit" | §0 wording |
| 6b "checkable" | §3 conditions preamble |
| 6c contrapositive logic | §3 notes |
| 6d testable-implication scope | §3 notes; §6 (NI) row |
| 6e branch pairs test only the keep channel; memory display | §6 first two rows |

**Re-review of revision 2:** ACCEPTED for the author's proof check (same review file, section "Re-review of revision 2"). Its non-blocking wording points N1–N4 are applied in this version: "(NF) and (NI)" in §1, (NF) components as sufficient, joint noise law in (NF-b), "under every policy" in (NF-c). N5 (paths) is resolved by committing the review and the script at the repository paths cited above.

## 9. Revision 3: the errata and decisions of R1-T4-PROOF-CHECK, and where they are applied

| Item in R1-T4-PROOF-CHECK | Where applied |
|---|---|
| Erratum (1): 8′'s one-step proof does not need U ⊥ W_{1:N}; move the assumption from §1 to (NF) and say that 8′ does not need it | §1 "Decisions" (assumption removed); §2 statement and the line after the proof; §3 (NF) |
| Erratum (2): at μ_n = 0, keep and discard are equivalent, but for g > 0 skip is strictly better than execute ("every decision ties" holds only at g = 0); identifying a no-op by H_n = 0 also needs the non-no-op comparison value to have no mass at zero | §2 part 4 and its proof; §1 "Exogenous variables" |
| Erratum (3): the three-step proof of 10(a′) holds; Step 1's reduction from G_n to O_n is the tower property (revision 2 said weak union); the per-trial bounds add because (NF) gives every policy the same law of the proposal sequence and (NI) means the executed history, given the proposal history, does not change the current posterior | §3 Step 1 and Step 3 |
| Erratum (4): the exact optimality gap is (J_probe − J_myopic)⁺; at α = 1, β = 0.1, g = 0.5, κ = 1 the plain difference is about −0.1011 and the gap is 0; the four table rows are all positive; the script re-run matches the repository output byte for byte; the paper keeps the existence statement | §4 Proposition 10(c): "Optimality gap", table header, the script note, "What the paper keeps" |
| R1: option (ii) | §5 R1 |
| R4: 20 proposals | §5 R4 |
| §6: five offline checks enter the plan; C4 forced-branch test deferred | §6 preamble and status column |
| Consequence for the Track S appendix (per-decision wording, 8′ parts 2–3; no campaign-level conclusion) | not in this file; a separate unit revises the appendix draft |

**Editorial changes beyond the row**, listed so that the review can check that they change no result:
- the status paragraph at the top, and §7 marked as decided;
- §3 Step 1 names the contraction step and writes the tower-property chain out;
- §2 part 4's proof writes out why V*_n = (1 − π_n) μ_n⁺ when τ_n = 0: Δ_n ∈ {0, μ_n} has the sign of μ_n;
- §4 states the β → ∞ limit as the difference, which equals the gap once it is positive;
- §4 records that this unit re-ran `ex10c.py` with the same output.
