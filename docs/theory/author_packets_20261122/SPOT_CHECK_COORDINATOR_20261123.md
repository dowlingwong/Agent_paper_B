AI-assisted (Claude, coordinating chat, 23 Nov 2026). Check (b) of PLAN row R1-PROOF-POLICY. Not an author check.

# Spot check (b): T2 Proposition 1; T4 Propositions 6 (with its scope paragraph), 7 (with Corollary 7a), 9 (with Corollary 9a) and 10(b)

**What this is.** R1-PROOF-POLICY (b): the coordinating chat re-derives, independently of check (a), at least each statement's key identity or inequality and one edge case, records what it checked and the result here, and states whether it disagrees with (a) (`AI_PROOF_CHECK_20261123.md` at `2e5adcaf`). The derivations below were done by hand in this chat. The script `spot_check_coordinator_20261123.py` was written in this chat without importing code or numbers from `ai_proof_check_20261123.py`; its output is `spot_check_coordinator_20261123_output.txt` (59 lines, fixed seeds, reproducible; SymPy 1.14.0, NumPy 2.5.3, SciPy 1.18.1, mpmath 1.3.0; about 5 minutes, most of it the 50-digit quadrature of SC-T4-7a). Evidence is cited by the line tag (SC-…).

**Result.** No disagreement with check (a) on any key item, any verdict or any proposed change. Three remarks of my own on the scope of the new Lemma K are in §2.3; they narrow how the replacement for T4:48 should be worded but do not change its verdict.

| # | Statement | Check (a) | Check (b) | May enter the main text |
|---|---|---|---|---|
| 1 | T2 Prop. 1 | ready after changes | agrees | after changes 1–5 of (a) §1.3 are applied |
| 2 | T4 Prop. 6 and scope paragraph | ready after changes | agrees, including Lemma K; wording remarks in §2.3 | after changes 1–7 of (a) §2.4 are applied, with §2.3's remarks in change 6 |
| 3 | T4 Prop. 7 and Cor. 7a | ready after changes | agrees | after changes 1, 3, 4, 5 of (a) §3.4 are applied |
| 4 | T4 Prop. 9 (i)–(iv) and Cor. 9a | ready as written | agrees | yes; update the stale status sentence at T4:125 (not part of the statement) |
| 5 | T4 Prop. 10(b) | ready after changes | agrees | after change 1 of (a) §5.3 is applied |

---

## 1. T2 Proposition 1

**Key identity (by hand).** Under Δ ⊥ η, both Gaussian, τ > 0: E[Δ | Δ̂] = m(Δ̂) = μ₀ + (τ²/s²)(Δ̂ − μ₀). So V(t) = E[m(Δ̂)1{Δ̂ > t}] = μ₀Φ(−z) + (τ²/s²)E[(Δ̂ − μ₀)1{Δ̂ > t}] = μ₀Φ(−z) + (τ²/s)φ(z). Differentiating with dz/dt = 1/s: V′(t) = −(φ(z)/s)[μ₀ + τ²(t − μ₀)/s²] = −f(t)m(t), and m(t) = (τ²/s²)(t − t\*) with t\* = −μ₀σ_d²/τ². Hence V′ > 0 left of t\*, < 0 right of it: t\* is the unique maximiser. SymPy confirms V′ + (τ²/s²)f(t)(t − t\*) ≡ 0 (SC-T2-1); Monte Carlo at one point agrees with the closed form within 0.5 s.e. (SC-T2-2).

**Edge case.** σ_d = 0: Δ̂ = Δ, t\* = 0 for every μ₀, and V′(t) = −t f_Δ(t), so t = 0 is the unique optimum. The grid argmax is 0 at μ₀ ∈ {−1, 0, +1}, and V(0) − V(−1) > 0 in each case (+0.157 at μ₀ = 0, which is φ(0) − φ(1)) (SC-T2-3). T2:27's "every threshold in (−∞, 0] is optimal" is false, as (a) and the audit say.

**Verdict.** Agree with (a): ready after changes 1–5.

## 2. T4 Proposition 6 and its scope paragraph

### 2.1 Proposition 6

**Key (by hand).** Tower property: E[Δ_n k | F_n] = E[k E[Δ_n | F_n, Δ̂_n] | F_n] ≤ E[E[Δ_n | F_n, Δ̂_n]⁺ | F_n], with equality for k = 1{posterior mean > 0}. On I_n, Δ_n = 0, so E[Δ_n | F_n, Δ̂_n] = E[Δ_n 1_{I_nᶜ} | F_n, Δ̂_n] = P(I_nᶜ | F_n, Δ̂_n) m₁(Δ̂_n) whatever Δ̂_n does on a no-op; positive iff Δ̂_n > t\*_n where the probability is positive. This is (a)'s step 3′; I agree that bit-exactness is not needed.

**Edge case.** σ_n = 0 gives t\*_n = 0 for every μ_n, so the reading "ρ optimal iff μ_n = 0" needs σ_n > 0 (as in §1). π_n = 1: V\*_n must be set to 0.

### 2.2 Scope paragraph: t\*\*_n

**Key (by hand, then SymPy).** Given F_n, with e ∼ N(m, v), Δ_n ∼ N(μ, τ²), ξ ∼ N(0, 1) independent: Δ̂ = Δ − (1 − ϱ)e + σ_cξ has mean M = μ − (1 − ϱ)m and variance τ² + w², w² = σ_c² + (1 − ϱ)²v. E[Δ | Δ̂] = μ + τ²(Δ̂ − M)/(τ² + w²) = 0 at Δ̂ = −(1 − ϱ)m − μw²/τ² = t\*\*_n (SC-T4-6a). At m = 0, v = σ²: w² = 2σ²(1 − ϱ) = σ_n² (SC-T4-6b). t\*\*_n − t\*_n = −(1 − ϱ)m + μ(1 − ϱ)²(σ² − v)/τ² (SC-T4-6c), from which the three-condition direction and the two counter-directions follow by sign inspection.

### 2.3 Lemma K (the new claim of (a)) and the T4:48 sentence

**Re-derivation (by hand).** Induction hypothesis: e_n | F_n ∼ N(m, v) and, by (K2), e_n, Δ_n, ξ_n are independent Gaussians given F_n.
1. (e_n, ε_n, Δ̂_n) is a linear image of (e_n, Δ_n, ξ_n), so it is jointly Gaussian given F_n. I computed the covariances from the matrix A = [[1, 0, 0], [ϱ, 0, σ_c], [−(1 − ϱ), 1, σ_c]] acting on diag(v, τ², 1): Cov(ε, Δ̂) = σ_c² − ϱ(1 − ϱ)v = C, Var Δ̂ = S², Cov(e, Δ̂) = −(1 − ϱ)v (SC-K-3). Conditioning on Δ̂_n = h gives (a)'s keep and discard updates.
2. The keep decision is a function of (F_n, Δ̂_n) and independent randomisation. Given the value Δ̂_n = h the decision is determined, so conditioning on it as well removes nothing: there is no truncation. The truncated law of Proposition 9 conditions on {Δ̂_n > 0} *without* the value of Δ̂_n, and on (e, Δ_n), which the control plane does not see.
3. Under (K3) the next proposal and randomness add no information on the latent errors; under (K2) e_{n+1} ⊥ Δ_{n+1} | F_{n+1}.
4. σ² − v_keep = ϱ²(σ² − v) + C²/S² and v − v_disc = (1 − ϱ)²v²/S² (SC-K-1, SC-K-2), so v ≤ σ² is preserved.

**Numeric check (independent implementation).** Three-trial campaigns under the kernel as the generative model, the deployed rule t\*_n with σ_n² = 2σ²(1 − ϱ), illustrative μ_j = (−0.30, −0.05, +0.20) and τ_j = (0.50, 0.80, 0.40), 3 × 10⁶ campaigns per ϱ ∈ {0, 0.6, 0.9}. The Kalman residual r = (e₄ − m₄)/√v₄:
- has mean, variance, skewness and excess kurtosis consistent with N(0, 1), overall and within every keep pattern with at least 20,000 campaigns (SC-K-4, SC-K-5), although the raw record error given the keep pattern has means from +0.08 to +1.66 and skewness up to +0.20;
- is uncorrelated, in r and in r² − 1, with six nonlinear functions of the ledger (36 t-statistics in all; largest |t| 2.31, which is in line with the largest of 36 draws from N(0, 1)) (SC-K-6);
- by contrast, standardising e₄ with its moments given the keep pattern only (the coarser information the T4:48 sentence has in mind) leaves a strong dependence on the last recorded comparison: t = +405, +832, +107 (SC-K-7).

Max v₄/σ² was 0.72, 0.41 and 0.95 (SC-K-4). E[e₄ | F₄] < 0 in 20 %, 44 % and 8 % of these illustrative histories (SC-K-8). These shares come from illustrative parameters and are not estimates for any node.

**Verdict.** I agree with (a): under (K1)–(K4), e | F_n is exactly Gaussian, t\*\*_n with Kalman moments is the exact Bayes threshold given F_n, Var(e | F_n) ≤ σ² holds at every trial, and the T4:48 sentence "after a keep e is truncated, not Gaussian, so t\*\*_n is an approximation there, and the exact rule has no closed form" is false under those conditions.

**Remarks of my own (scope; they shape change 6's wording, not the verdict).**
1. *Absolute metrics.* The ledger records each run's metric level, not only comparisons. The recursion is the full posterior only if the levels carry no further information about the record's error, for example under a flat prior on the incumbent's true level or a control plane that reads only the comparisons. (a)'s (K3) contains this condition ("F_n informative about the errors only through the recorded comparisons"); the replacement sentence for T4:48 should state it explicitly. If a learned model also reads levels, the posterior is still Gaussian when everything is Gaussian, but over a larger state, and the two-line recursion is not the whole update.
2. *(K2) is a modelling assumption about the loop.* It excludes, for example, increments whose law depends on the incumbent's true level, which is itself correlated with e after lucky keeps. (a) lists it under "not verified"; the theory note should say that Lemma K is exact within the model and that whether the model fits the nodes is the subject of R1-SCREEN-MEASURE.
3. *Feasibility.* The exact rule needs ϱ, σ and every past executed proposal's (μ_j, τ_j). Arms that do not produce (μ_j, τ_j) for past proposals (A0, A1, FIXR3, EGATE, Ladder) cannot compute it. For the closed loop this matters only for the design of the conditional seventh arm in R1-D3-CHOICES (1) ("A2 + keep-count threshold correction"): a Kalman correction over the recorded comparisons is the exact version, within the model, of what the keep count approximates. No PLAN row changes on this; it is a design note for that arm if the supplementary measurement triggers it.
4. *Wording of conservativeness.* Because E[e | F_n] < 0 does occur (S9 of (a); SC-K-8 here), the deployed rule is conservative only on histories with E[e | F_n] ≥ 0 and μ_n ≤ 0. The manuscript must not state conservativeness without that condition. R1-THEORY-RHO (2) is already conditional.

## 3. T4 Proposition 7 and Corollary 7a

**Key identity and bounds (by hand).** V(t\*) − V(t̃) = −∫_{t\*}^{t̃}V′ = (τ²/s²)∫_{t̃}^{t\*} f(u)(t\* − u)du; the integrand has the sign of the orientation, so the oriented integral is ≥ 0 for both orders. The Gaussian density is unimodal, so its minimum over a closed interval is at an endpoint; its maximum is 1/(s√(2π)); and ∫_I |t\* − u|du = (t\* − t̃)²/2. Multiplying gives both bounds, and the factor 1 − π_n comes from Δ_n = 0 on I_n. 200 random sets at 50 digits, with t̃ up to ±6s from t\*: no sign or bound failure; the identity holds to 1.7 × 10⁻⁹ relative, a residual that fell from 7 × 10⁻² to 1.4 × 10⁻⁵ to 1.7 × 10⁻⁹ as the quadrature was refined (SC-T4-7a). (A first double-precision version failed in far-tail cases through cancellation in V, not through the identity; the committed version writes the difference so that μ₀ cancels exactly.)

**Local form (by hand).** With h = t\* − t̃ and f(t\* − x) = f(t\*)[1 + x(t\* − μ)/s² + O(x²)]: ∫₀^h x f(t\* − x)dx = f(t\*)(h²/2)[1 + (2/3)(t\* − μ)h/s² + O(h²)]. At h = ±10⁻³s the ratio to the leading term is 1.0015105 and 0.9984916 against the predicted 1.0015094 and 0.9984906, the remainder being O(h²) (SC-T4-7b). The leading term replaces f by f(t\*), so "first-order Taylor expansion of f_n" is, as (a) says, a misnomer.

**Corollary 7a (argument).** I agree that the 18 Oct decision-independence condition is not enough (it is the audit's gap) and that (NF) with an execution rule that does not read past keep decisions lets both policies be coupled on the same exogenous draws and U, so that a_n and C_n coincide and the per-trial difference is a_n gap_n. Under the shared incumbent error of R1 (ii), (NF) fails for the actual loop, so the corollary is a statement about a model, not about the deployed loop.

**Edge case.** Covered by SC-T4-7a's tail sets (t\* deep in either tail, τ down to 0.05); τ → 0 makes t\* undefined, which is why τ_n > 0 must be stated.

**Verdict.** Agree with (a): ready after changes 1, 3, 4 (Prop. 7) and 5 (Cor. 7a).

## 4. T4 Proposition 9 and Corollary 9a

**Key (by hand).** (i) K = {Δ̂_n > 0} = {ε_n > e − Δ_n}, and e′ = ε_n on K. (ii.1) Y = (ε_n − c)1_K ≥ 0, Y > 0 on K, E[Y | G] finite; for A = {p_G > 0, E[Y | G] = 0} ∈ G, E[Y1_A] = 0 forces P(K ∩ A) = 0 = E[p_G1_A], so P(A) = 0, and dividing by p_G gives E[e′ | K, G] > c on {p_G > 0}. I checked that c being G-measurable (not necessarily integrable) is enough after localising on {|c| ≤ k}. (iv) the same argument with Z = (ε_n − e + Δ_n)1_K, which is why "| K" must stay on the right.

**Edge case.** p_G = 1 (ε uniform on [0, 1], c = −1): E[ε | K] − E[ε] = 0 exactly, so (ii.2)'s strictness needs p_G < 1 (SC-T4-9a). ϱ → 1 (ϱ = 0.9999, e = 0.5): E[e′ | K] = 0.49995 → e for Δ = +0.2 and 0.70099 → e − Δ for Δ = −0.2, matching max(e − Δ, ϱe) in the limit (SC-T4-9d).

**Corollary 9a.** The truncated-normal mean ϱe + σ_cλ(a), a = ((1 − ϱ)e − Δ)/σ_c, agrees with simulation at three sets including ϱ = 0.95 and a negative e (SC-T4-9b; within 1.7 s.e.). λ(a) > max(0, a): by hand, ψ(a) = φ(a) − aΦ(−a) has ψ′ = −Φ(−a) < 0 and ψ(∞) = 0, so ψ > 0; numerically the margin is positive on [−30, 30] (SC-T4-9c).

**Verdict.** Agree with (a): ready as written. The status sentence at T4:125 ("data the author has not yet accepted") is stale since R1-E1-PILOT-ACCEPT and should be updated; it is not part of the statement.

## 5. T4 Proposition 10(b)

**Key (by hand).** Trial 1's increment −α is known, so myopic acceptance discards it; trial 2 then has Δ₂ ∼ N(0, τ²) and earns E[Δ₂⁺] = τφ(0). Keeping trial 1 and then keeping iff Δ₂ > 0 earns −α + E[N(β, τ²)⁺] = −α + βΦ(β/τ) + τφ(β/τ). The myopic loss is (G − α)⁺ with G(β, τ) = βΦ(β/τ) + τφ(β/τ) − τφ(0). G(2, 1) = 1.6095484222 (SC-T4-10a); simulation 1.60877, s.e. 0.00057, 1.4 s.e. away (SC-T4-10b). At α = 1.6097 the loss is 0, not 1.61 − α = 0.0003 (SC-T4-10a): the "α < 1.61" sentence is wrong by rounding.

**Unboundedness.** dG/dβ = Φ(β/τ) > 0 and G ≥ β − τφ(0) (from Φ ≤ 1 and φ ≥ 0); values at β = 2, 10, 100 (SC-T4-10c).

**Edge case.** Noise σ > 0 at trial 2: V(t\*; β) ≥ lim_{t→−∞}V = β and the myopic discard branch has μ = 0, t\* = 0, value τ²φ(0)/s, so G_σ ≥ β − τ²φ(0)/s (SC-T4-10c at σ = 0.5). The example therefore does not need σ → 0.

**Verdict.** Agree with (a): ready after change 1.

---

## 6. What this check did not do

- It did not compare the manuscript (`papers/r1/sections/theory.tex`, `appendix.tex`) with the signable forms; that comparison is part of applying the changes.
- It did not re-run the empirical figures cited in T4:48 and T4:125 (T5 sizes; E1 partial correlation).
- It re-derived the key items and one edge case per statement, as R1-PROOF-POLICY (b) requires, not every step of (a)'s tables.
