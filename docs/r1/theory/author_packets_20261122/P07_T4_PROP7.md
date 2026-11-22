# Author proof-check packet: T4 Proposition 7 (value of a per-proposal prior over a constant one)

*AI-assisted (Claude, chat session, 22 Nov 2026). Support for the author's own check; **not checked or accepted by the author**. It replaces the short packet `author_packets_20261027/P07.md` for this statement. Source: `../T4_FEEDBACK_PROPOSER.md` §3 on `main` @ `3c3f822a`. Audit: `../T_AUDIT_20261027.md` ("correct with added assumptions").*

**Why this one comes first.** If the C3 gate does not pass, the paper reports C3 as a measured negative "with Proposition 7's dispersion bound" (RUNBOOK B.7 and §6). The gate's simulated power is 0.36 at effect size 0.3, so that text is the more likely one to be used.

## 1. Statement to check

Fix n and F_n with π_n < 1. Let t̃ be any finite F_n-measurable threshold, s_n² = τ_n² + σ_n², f_n the N(μ_n, s_n²) density, t\*_n = −μ_n σ_n²/τ_n². Then

- **Identity:** V\*_n − (1 − π_n) V(t̃) = (1 − π_n)(τ_n²/s_n²) ∫ from t̃ to t\*_n of f_n(u)(t\*_n − u) du ≥ 0.
- **Bounds:** (1 − π_n)(τ_n²/(2 s_n²)) · min f_n on the interval · (t\*_n − t̃)² ≤ gap ≤ (1 − π_n) τ_n² (t\*_n − t̃)² / (2√(2π) s_n³).
- **Local form:** gap ≈ (1 − π_n) τ_n² f_n(t\*_n)(t\*_n − t̃)²/(2 s_n²) near t\*_n.

## 2. What the proof rests on

| Step | Claim | Where it comes from | Check |
|---|---|---|---|
| 1 | V(t) = μ Φ(−z) + (τ²/s) φ(z), z = (t − μ)/s | T2 Proposition 1 | Not author-checked. The 27 Oct audit found gaps in T2 Propositions 1 and 2. T2 has not been revised since: the corrections exist only as an unadopted proposal (`proposals/THEORY_CORRECTIONS_20261027.md`; see `P01_T2_PROP1.md`). **Proposition 7 inherits Proposition 1**, so check P01 first. The value formula itself is confirmed numerically; the open points in Proposition 1 are its edge case and missing assumptions. |
| 2 | dV/dt = −f(t)·E[Δ \| Δ̂ = t] = −f(t)(τ²/s²)(t − t\*) | differentiate step 1, or the general identity d/dt E[X 1{Y > t}] = −f_Y(t) E[X \| Y = t] | One line by hand: φ′(z) = −zφ(z). |
| 3 | V(t\*) − V(t̃) = (τ²/s²) ∫ from t̃ to t\* f(u)(t\* − u) du | integrate step 2 | Sign: for t̃ < t\* the integrand is positive on an interval run forwards; for t̃ > t\* it is negative on an interval run backwards. Both give ≥ 0. The absolute value in the T4 text is redundant. |
| 4 | bounds | bound f between its minimum on the interval and 1/(s√(2π)); ∫\|t\* − u\| du = (t\* − t̃)²/2 | "[t̃, t\*]" must be read as the interval between the two points in either order (audit). |
| 5 | factor (1 − π_n) | on a no-op, Δ = 0 and every keep decision is worth 0 | Needs Proposition 6's treatment of {Δ̂ = 0}. |

**Assumptions the statement needs but does not list** (from the audit; the manuscript's version should state them): τ_n > 0 (otherwise t\* is not finite), s_n > 0, π_n < 1, t̃ finite, and (A1)–(A2) of T4 §1.

## 3. Numerical check (run 22 Nov; `check_p07_p09.py`, output in `check_output.txt`)

- 2,000 random parameter sets (μ ~ N(0,1), τ, σ in [0.2, 2], t̃ = t\* + N(0, 2²)): the identity holds to 7 × 10⁻¹⁶; the lower and the upper bound hold in every case.
- Step 1's closed form against simulation (4 × 10⁶ draws, one parameter set): 0.01153 against 0.01147 (s.e. 0.00017).

These confirm the algebra for the current text. They say nothing about the points in section 4.

## 4. Points for the author to decide

1. **Step 1.** Settle T2 Proposition 1 first (`P01_T2_PROP1.md`): its σ_d = 0 sentence is false as written, and its assumptions need stating. Proposition 7 cannot be marked checked before it.
2. **The "Reading" claim is not part of the proposition.** T4 §3 says the upper bound, computed from a *pilot* predictor's (μ_n, τ_n), "gives an estimate of how much any better predictor could still add". The algebra bounds the gap in terms of the **true** (μ_n, τ_n). With predicted parameters the bound is an estimate whose error is not controlled by the proposition (audit). For the negative-outcome text this matters: "the dispersion bound shows little room" is supported only as far as the predicted parameters are right. Suggested wording for the manuscript: report the bound as computed from the fitted forecast, call it an estimate, and say what would make it wrong (a forecast that is too smooth understates the dispersion of t\*_n, and so understates the room).
3. **Corollary 7a** (campaign-level gain = E[Σ a_n · gap_n]) needs decision independence, i.e. Proposition 10(a′) as corrected on 28 Oct and accepted with errata in R1-T4-PROOF-CHECK. Confirm that the corollary cites the corrected condition (NF and NI), not the original DI of the 18 Oct draft.
4. **The local form** is a second-order statement (the gap is quadratic in the threshold error); the T4 text calls it "first-order Taylor expansion of f_n". Wording only.

## 5. If it checks out

Record it as an author row (as R1-T4-PROOF-CHECK did for 8′, 10(a′), 10(c)), with any errata. The manuscript then moves this statement from "not author-checked" to the main text.
