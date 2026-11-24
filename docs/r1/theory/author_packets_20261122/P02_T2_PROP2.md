AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T2 Proposition 2 (value of information of verify(r))

*It replaces the short packet `author_packets_20261027/P02.md` for this statement. Source: `../T2_DERIVATIONS.md` §3 on this branch. Audit: `../T_AUDIT_20261027.md` ("Wrong (diminishing returns as stated)"). Proposed correction (not adopted): `../../proposals/THEORY_CORRECTIONS_20261027.md` §"T2 Proposition 2". T2 has not been revised since the audit (P01 §0). The point in section 4 marked "AI analysis, unreviewed" has not been reviewed by anyone.*

**Why it matters for the paper.** Arm A1 "keeps knowledge-gradient verification" (`papers/r1/sections/setup.tex`); its index (D23, T2 §6) computes VoI with this formula. The manuscript itself says verification "is an information action, and these results do not cover it", so no main-text theorem rests on this proposition. It enters through A1's definition and through P05.

## 1. Statement to check (as currently written)

With m = E[Δ | Δ̂], v = Var(Δ | Δ̂), s̃² = Var(E[Δ | Δ̂, D̄] | Δ̂), and the Bayes response:

VoI_r(Δ̂) = E[max(E[Δ | Δ̂, D̄], 0) | Δ̂] − max(m, 0) = s̃ ψ(|m|/s̃).

VoI_r is maximal where m = 0 (at Δ̂ = t\*), decreasing in |m|, and **increasing in r, with diminishing returns**. The proof says: under `"vary"`, s̃² = v − 1/(a + rb) is increasing and concave in r, and "that concavity is the diminishing-returns claim".

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | Given Δ̂, M′ = E[Δ \| Δ̂, D̄] ∼ N(m, s̃²) | Tower property plus joint Gaussianity of (Δ, Δ̂, D̄). Needs the independence assumptions of T2 §1 stated (audit), r a positive integer. |
| 2 | E[max(M′, 0)] = mΦ(m/s̃) + s̃φ(m/s̃) | Standard. Needs s̃ > 0; at s̃ = 0 define VoI = 0 (audit). |
| 3 | minus max(m, 0) gives s̃ψ(\|m\|/s̃) | Uses Φ(x) = 1 − Φ(−x). One line. |
| 4 | maximal at m = 0, decreasing in \|m\| | ψ′(z) = −Φ(−z) < 0, and s̃ does not depend on Δ̂ (Gaussian model). m = 0 iff Δ̂ = t\*. |
| 5 | s̃ increasing in r | More independent replicates lower Var(Δ \| ·). Vary: explicit. Fixed: true as well (audit: "nondecreasing under independent new training-seed draws"). |
| 6 | s̃² concave in r (vary) | Correct: s̃² = v − 1/(1/v + r/σ_d²). |
| 7 | "that concavity is the diminishing-returns claim" | **Does not follow (audit), and still in the current text.** VoI = s̃ψ(\|m\|/s̃) is convex in s̃ for m ≠ 0 (d²VoI/ds̃² = (m²/s̃³)φ(m/s̃) > 0), so concavity of s̃² does not carry over. Diminishing returns hold at m = 0, where VoI = s̃φ(0). |
| 8 | the formula is for the Bayes response | The harness's frozen response (D̄ > 0) has a different value (T2 §3 says so). The D4 amendment adds a posterior-mean response as a declared version. |

**Assumptions to state** (audit): joint Gaussianity and independence of Δ, e_t, e_s and the replicate errors (with the reuse of e_s under `"fixed"`), r ≥ 1 integer, τ > 0, s̃ > 0 or VoI := 0 at s̃ = 0.

## 3. The audit and the current text

| Audit finding | In current T2? | In the proposal? |
|---|---|---|
| Diminishing returns in r not true in general | No: the claim and the "concavity" sentence are still there | Yes: "nondecreasing … diminishing returns are not asserted in general" |
| VoI := 0 at s̃ = 0 | No | Yes |
| Formula is for the Bayes response | Yes (T2 §3 already says so) | Yes |
| Independence assumptions | No | Yes |

## 4. Numerical check (run 22 Nov; `check_t2_p6.py`, section P02)

- Pointwise VoI against simulation that uses the **true Δ** (mean of Δ(1{M′ > 0} − 1{m > 0}) over draws with Δ̂ in a window of ±0.02 around the target; 6 × 10⁶ draws): vary (μ = −0.3, τ = 0.8, sd_t = 0.5, sd_s = 0.6, r = 2, Δ̂ ≈ 0.1) 0.11552 against 0.11621 (s.e. 0.00113); fixed, same parameters, 0.04993 against 0.04965 (s.e. 0.00110); vary (μ = 0, τ = 1, sd_t = sd_s = 0.7, r = 3, Δ̂ ≈ 1.0) 0.05240 against 0.05335 (s.e. 0.00106).
- The explicit s̃² formulas (vary; audit's fixed formula) against generic Gaussian conditioning, 2,000 random sets: differences ≤ 1.1 × 10⁻¹⁵.
- s̃ non-decreasing in r = 1..30 in all 2,000 sets for both policies; s̃² concave in r in all 2,000 sets for vary **and** for fixed (fixed concavity is observed only, not proven).
- VoI(m, s̃ = 1) is decreasing on |m| ∈ [0, 5], maximal at m = 0.
- The audit's counterexample (v = 1, σ_d = 1, m = 3) reproduces exactly: VoI at r = 1, 2, 3 = 0.0000016775, 0.0000235513, 0.0000583861; increments 0.0000218738, 0.0000348348 (increasing).
- At m = 0 (τ² = 2, σ_d² = 1, vary) the increments in r are decreasing: 0.0402, 0.0197, 0.0118, 0.0079, 0.0057.

**A correction to the audit's counterexample (AI analysis, unreviewed).** The audit says its parameters are "realizable with τ² = 2, σ_d² = 1 and suitable H". Under `"vary"` in T2's model, v = τ²σ_d²/(τ² + σ_d²) < σ_d², so v = 1 with σ_d = 1 cannot occur, and τ² = 2, σ_d² = 1 gives v = 2/3 (script: v = 0.333333, 0.666667, 0.990099, 0.999999 at τ² = 0.5, 2, 100, 10⁶). **The audit's conclusion survives** with attainable parameters: τ² = 2, σ_d² = 1, μ₀ = 0, Δ̂ = 4.5 (so m = 3) gives VoI at r = 1..4 = 2.640 × 10⁻¹⁰, 6.906 × 10⁻⁸, 4.628 × 10⁻⁷, 1.214 × 10⁻⁶, with increasing increments 6.880 × 10⁻⁸, 3.937 × 10⁻⁷, 7.509 × 10⁻⁷. The same holds under `"fixed"` (τ² = 2, sd_t² = sd_s² = 0.5, m = 3: increments 5.380 × 10⁻¹⁵, 1.854 × 10⁻¹³, 9.567 × 10⁻¹³). Note that all these values are tiny: the failure of diminishing returns happens far from the boundary, where verify is worth almost nothing.

Not checked: the frozen-response figures in T2 §3 ("loses about 0.0003 against ρ" at Δ̂ = 2σ_d on a digits-like node, "1–2 × 10⁻⁵" under `"fixed"`). Their inputs are not specified in T2.

## 5. Points for the author to decide

1. **Drop or restrict "with diminishing returns".** Options: the proposal's "nondecreasing in r; diminishing returns not asserted in general"; or a restricted statement at m = 0 (VoI = s̃φ(0), concave in r under vary because s̃² is concave and the square root is concave and increasing). A statement for a neighbourhood of m = 0 would need its own proof; none is given here.
2. **The audit's counterexample text** uses parameters that are not attainable in T2's model (above). If the counterexample is cited, use attainable values.
3. **Scope for A1.** The paper uses this formula only inside A1's index. Decide whether the manuscript states it at all, or only cites the KG formula (Frazier, Powell & Dayanik 2008) for A1's definition.

## 6. If it checks out

Record an author row with errata: (1) "diminishing returns" removed or restricted to m = 0; (2) the "concavity is the diminishing-returns claim" sentence removed; (3) assumptions added. The formula itself can then support A1's definition.
