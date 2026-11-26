AI-assisted (Claude, subagent, 23 Nov 2026). Spot-check list for check (b) of PLAN row R1-PROOF-POLICY. It goes with `AI_PROOF_CHECK_20261123.md`.

# What the coordinating chat's spot check should re-derive

R1-PROOF-POLICY (b) asks for at least the key identity or inequality and one edge case per statement. The items marked **key** and **edge** below meet that minimum. "out:L" is a line of `ai_proof_check_20261123_output.txt`.

## 1. T2 Proposition 1 (report: ready after the proposed changes)
1. **Key.** V(t) = μ₀Φ(−z) + (τ²/s)φ(z). Use Δ = μ₀ + (τ²/s²)(Δ̂ − μ₀) + an independent residual, and E[(Δ̂ − μ₀)1{Δ̂ > t}] = sφ(z). This needs Δ ⊥ η, both Gaussian (out:4–5).
2. **Key.** V′(t) = −(τ²/s²)f(t)(t − t\*). So t\* = −μ₀σ_d²/τ² is the unique maximiser when τ > 0 (out:8).
3. **Edge.** σ_d = 0 gives V(t) = E[Δ1{Δ > t}] and V′ = −t f_Δ(t), so t = 0 is the unique optimum for every μ₀. T2:27's "every t ≤ 0 is optimal" is false: at μ₀ = 0, τ = 1, V(0) = 0.3989 > V(−1) = 0.2420 (out:11, out:34).
4. "t = 0 optimal iff μ₀ = 0" needs σ_d > 0. The error rate Φ(−|Δ|/σ_d) needs σ_d > 0 and Δ ≠ 0 (out:10, out:38).

## 2. T4 Proposition 6 and the scope paragraph (report: ready after the proposed changes)
1. **Key.** Tower property: E[Δ_n k | F_n] = E[k E[Δ_n | F_n, Δ̂_n] | F_n], so the pointwise maximiser is 1{posterior mean > 0}. On I_nᶜ the posterior mean is positive iff Δ̂_n > t\*_n (τ_n > 0).
2. The mixture identity E[Δ_n | F_n, Δ̂_n] = P(I_nᶜ | F_n, Δ̂_n) m₁(Δ̂_n) gives the rule and V\*_n = (1 − π_n)V(t\*_n) for any law of Δ̂_n on a no-op, so bit-exactness is not needed (out:41–44).
3. **Key (scope).** t\*\*_n = −(1 − ϱ)m_e − μ_n w²/τ_n² with w² = σ_c² + (1 − ϱ)²v. At m_e = 0 and v = σ², w² = 2σ²(1 − ϱ). Also t\*\*_n − t\*_n = −(1 − ϱ)m_e + μ_n(1 − ϱ)²(σ² − v)/τ_n² (out:12–15).
4. **New claim, re-derive this one.** Lemma K (report §2.3): under the kernel as the generative model, with F_n containing the recorded comparisons and (K1)–(K4), e | F_n is exactly Gaussian. Check one induction step: (e, ε, Δ̂) is jointly Gaussian given F_n, and the keep event is σ(F_n, Δ̂_n)-measurable. Check one keep update, and the identity σ² − v_keep = ϱ²(σ² − v) + C²/S² (out:100). If it holds, the T4:48 sentence "truncated, not Gaussian … no closed form" is false (out:104–128).
5. **Edge.** At σ_n = 0, t\*_n = 0 for every μ_n, so the reading "ρ optimal iff μ_n = 0" needs σ_n > 0 (out:44). With μ_n = 0 and m_e < 0, t\*\* > t\*, so the deployed rule keeps too many.

## 3. T4 Proposition 7 and Corollary 7a (report: ready after the proposed changes)
1. **Key.** gap = (1 − π)(τ²/s²)∫_{t̃}^{t\*} f(u)(t\* − u)du, by integrating V′. The oriented integral is ≥ 0 for both orders (out:18–19, out:78).
2. **Key.** Both bounds: min f on the interval (the minimum is at an endpoint) and max f = 1/(s√(2π)), with ∫|t\* − u|du = (t\* − t̃)²/2 (out:20, out:78, out:130).
3. Local form: the leading term is f(t\*)h²/2 with h = t\* − t̃, and the relative error is (2/3)(t\* − μ)h/s². Check against N7.2 at h = ∓0.001s, which gives 1.000710 and 0.999291 (out:79, out:102). "First-order Taylor expansion of f_n" is a misnomer.
4. **Key (7a).** Under (NF), with an execution rule that does not read past keeps, couple the two policies on the same exogenous draws. Then a_n and C_n coincide, and the difference per trial is a_n gap_n. The 18 Oct DI is not enough (audit). "Zero iff" holds a.s. on {a_n = 1, π_n < 1} (out:80–81).
5. **Edge.** τ = 1e-3, σ = 1e-4 and t̃ = t\* ± 5s at 50 digits: identity and bounds hold (out:130).

## 4. T4 Proposition 9, restated, and Corollary 9a (report: ready as written)
1. **Key.** (i): K = {ε_n > e − Δ_n}, and e′ = ε_n on K.
2. **Key.** (ii.1), the null-set step: A = {p_G > 0, E[Y | G] = 0} ∈ G and E[Y1_A] = 0 imply P(A) = 0. Note that E[Y | G] is finite.
3. (ii.2): E[ε | Kᶜ, G] ≤ c, and the mixture identity. **Edge:** at p_G = 1 equality holds, so strictness needs p_G < 1 (out:87).
4. (iv) needs "| K" on the right. The review's example (e ∈ {0, 10}, null proposal) gives E[e′ | K] = 0.80 < E[e] = 5 (out:89).
5. Corollary 9a: the truncated-normal mean ϱe + σ_cλ(a), with a = ((1 − ϱ)e − Δ)/σ_c, and λ(a) > max(0, a) via ψ > 0. **Edge:** ϱ → 1 (out:22–25, out:90).

## 5. T4 Proposition 10(b) (report: ready after the proposed changes)
1. **Key.** The keep branch earns E[(N(β, τ²))⁺] = βΦ(β/τ) + τφ(β/τ). The myopic discard branch earns τφ(0), and trial 1 is discarded because Δ₁ = −α is known (out:27).
2. G(2, 1) = 2Φ(2) + φ(2) − φ(0) = 1.609548…, and the loss is (G − α)⁺. So "for α < 1.61 … loses 1.61 − α" should read "for α < G(2, 1) … loses G(2, 1) − α" (out:29, out:95–96).
3. **Key.** Unboundedness: dG/dβ = Φ(β/τ) > 0 and G ≥ β − τφ(0) (out:28, out:97).
4. **Edge.** Noise σ > 0 at trial 2: G_σ ≥ β − τ²φ(0)/s, because V(t\*; β) ≥ lim_{t→−∞} V = β and V(0; 0) = τ²φ(0)/s (out:98, out:103).

To record: what was re-derived and the result, in this folder, per R1-PROOF-POLICY (b). A disagreement on any **key** item keeps that statement out of the main text.
