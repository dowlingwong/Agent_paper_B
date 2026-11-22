AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T2 Proposition 3 (verify can only correct the noise it resamples)

*It replaces the short packet `author_packets_20261027/P03.md` for this statement. Source: `../T2_DERIVATIONS.md` §4 on this branch. Audit: `../T_AUDIT_20261027.md` ("correct with added assumptions"). There is no proposed correction for this proposition in `../../proposals/THEORY_CORRECTIONS_20261027.md`, and T2 has not been revised since the audit (P01 §0).*

**Why it matters for the paper.** PLAN §10 "Verify split policy" adopts `"vary"` on every node and cites this proposition ("Under `"fixed"`, verify is a no-op on the OpenML logistic-regression nodes (σ_train = 0; T2 Proposition 3), and `"vary"` is never less informative"). The manuscript does not state it. It matters if the paper justifies its split policy by theory.

## 1. Statement to check (as currently written)

Under `"fixed"`, VoI_r^fixed(Δ̂) → 0 as σ_t → 0, for every Δ̂, r and σ_s. Under `"vary"`, VoI_r^vary(Δ̂) stays bounded away from zero as σ_t → 0 whenever τ, σ_s > 0.

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | Fixed: D̄ − Δ̂ = ξ̄ − e_t, Var = σ_t²(1 + 1/r) → 0 | Correct. |
| 2 | "The Gaussian posterior moves continuously with the covariance, so s̃ → 0" | **Insufficient as written (audit):** the limit covariance is singular, and continuity at a singular point is what has to be shown. The audit's explicit calculation closes it: with A = τ² + σ_s², u = σ_t², Cov(Δ, D̄ \| Δ̂) = τ²u/(A + u), Var(D̄ \| Δ̂) = u(1 + 1/r − u/(A + u)), so s̃² = O(u). Needs A > 0 (if A = 0, Δ is constant and VoI = 0). |
| 3 | VoI ≤ s̃φ(0) → 0 | Correct (ψ ≤ φ(0)). |
| 4 | Vary: D̄ = Δ + ξ̄, independent; conditioning on D̄ strictly lowers Var(Δ \| ·), so s̃ > 0 | Correct, and the limit is explicit: v → τ²σ_s²/A, s̃² → v²/(v + σ_s²/r) > 0. With m finite at fixed Δ̂, VoI tends to a positive value. |
| 5 | "bounded away from zero" | **Pointwise in Δ̂ only (audit):** VoI → 0 as \|Δ̂\| → ∞ at any fixed σ_t. "Uniformly bounded away from zero" would be false. |

**Assumptions to state** (audit): finite μ, τ, σ_s and fixed r; the common independence assumptions of T2 §1; A > 0 for the fixed-policy rate; the vary claim is pointwise in Δ̂.

## 3. The audit and the current text

The audit found no error, only missing assumptions and the insufficient continuity step. None of these is in the current T2 text, and the 27 Oct proposals do not cover Proposition 3. So **the audit's points are addressed nowhere yet**; they are small and are listed in section 5.

## 4. Numerical check (run 22 Nov; `check_t2_p6.py`, section P03)

- μ = −0.3, τ = 0.8, sd_s = 0.6, r = 2, Δ̂ = 0, sd_t from 0.5 down to 10⁻⁴: fixed-policy VoI at m = 0 (its maximum) falls as 8.957 × 10⁻², 2.071 × 10⁻², 2.085 × 10⁻³, 2.085 × 10⁻⁴, 2.085 × 10⁻⁵, i.e. linearly in sd_t; s̃²/sd_t² tends to 0.2731, equal to the audit's limit τ⁴/(A²(1/r + 1)) = 0.2731. Vary-policy VoI stays at 0.0959–0.0961.
- Vary limit: s̃² = v²/(v + σ_s²/r) = 0.129347, computed at sd_t = 10⁻⁶: 0.129347.
- Pointwise, not uniform: the vary limit VoI at Δ̂ = 0, 2, 5, 10 is 9.59 × 10⁻², 5.35 × 10⁻⁵, 1.66 × 10⁻¹⁹, 1.60 × 10⁻⁷⁰.
- PLAN's "vary is never less informative": in 0 of 10,000 cases (2,000 random parameter sets × r = 1..5) is s̃_fixed > s̃_vary. This is a numerical observation, not a proof.
- T2 §4's "fixed recovers about half of the value of vary" on `digits_mlp`/`tabular_mlp`: with the reconstructed σ_d = 0.00857 of P05 (an assumption; T2 does not state its inputs) and τ = 0.009, the ratio of maximal VoI fixed/vary at r = 2 is 0.488 and 0.577 at sd_train/sd_joint = 0.56 and 0.65, and 0.050 and 0.330 at 0.06 and 0.39.

## 5. Points for the author to decide

1. **Replace the continuity sentence** by the explicit conditional calculation (two lines; the audit gives it).
2. **Say "for each fixed Δ̂"** in the vary claim.
3. **"Never less informative".** If the paper or PLAN keeps this claim for `"vary"`, it needs its own short argument (it is not part of Proposition 3). The numerical check found no counterexample. A proof would compare the two conditional variances Var(Δ | Δ̂, D̄) directly.
4. **E1 reading.** The "about half" figure depends on τ/σ_d as well as on the training share. If it is quoted, give the inputs.

## 6. If it checks out

Record an author row with the two editorial errata (explicit calculation; pointwise statement). The result can then back the `"vary"` decision in the appendix.
