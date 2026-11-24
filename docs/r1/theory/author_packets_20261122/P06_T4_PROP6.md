AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T4 Proposition 6 (the per-proposal Bayes keep rule)

*It replaces the short packet `author_packets_20261027/P06.md` for this statement. Source: `../T4_FEEDBACK_PROPOSER.md` §2 on this branch (`main` @ `3c3f822a` + `b3400558`). Audit: `../T_AUDIT_20261027.md` ("correct with added assumptions"). Related: `../../proposals/T4_PROP10_REVISION_20261028.md` (revision 3) §1 "Gaussian closed form", Proposition 8′.1 and remark R1, as checked by the author in PLAN §10 R1-T4-PROOF-CHECK. Sections 4.2 and 4.3 contain analysis that has **not** been reviewed by anyone.*

**Why this one comes second.** It is the keep rule that C3 and the paper rest on. The manuscript's Proposition "One-step index" (`papers/r1/sections/theory.tex`) has two parts: (i)–(ii) are Proposition 8′, which the author checked on 16 Nov; the Gaussian part ("on {H_n ≠ 0} the keep rule is the per-proposal Bayes threshold t\*_n …, V\*_n = (1 − π_n)V(t\*_n)") is this proposition. `appendix.tex` lists both as needing an author-checked proof. Arms A1–A5 use this closed form (`setup.tex`), and it is the primary instance of the D4 amendment.

## 1. Statement to check (as currently written in T4)

Under (A1)–(A2), for each n and every F_n, among all (F_n, Δ̂_n)-measurable k_n the conditional value E[Δ_n k_n | F_n, a_n = 1] is maximised by k_n = 1{Δ̂_n > t\*_n}, t\*_n = −μ_n σ_n²/τ_n², on {Δ̂_n ≠ 0}. On {Δ̂_n = 0} every decision has value 0. The maximal value is V\*_n = (1 − π_n) V(t\*_n; μ_n, τ_n, σ_n).

The manuscript's version differs: it conditions on O_n (the revision's information set) instead of F_n, assumes τ_n > 0, noise "with a continuous law", and "no-ops are observed exactly".

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | E[Δ_n k \| F_n] = E[k E[Δ_n \| F_n, Δ̂_n] \| F_n], so k = 1{posterior mean > 0} is a pointwise maximiser | Tower property. Needs E\|Δ_n\| < ∞, and conditioning on a_n = 1 needs positive probability (audit). Proposition 8′.1 replaces the conditioning by an a.s. inequality; that form was author-checked. |
| 2 | On I_nᶜ, Δ̂_n has a continuous law, so P(Δ̂_n = 0, I_nᶜ \| F_n) = 0 | Needs s_n > 0, i.e. τ_n > 0 or σ_n > 0. This is the "no mass at zero" condition of the author's erratum (2) to 8′. |
| 3 | {Δ̂_n = 0} = I_n a.s. | Needs a bit-exact node (Δ̂_n = 0 exactly on I_n). See 4.2: **the rule and the value do not need this step**. |
| 4 | Given F_n, on I_nᶜ: (Δ_n, Δ̂_n) bivariate normal, means (μ_n, μ_n), Var Δ̂_n = s_n², Cov τ_n² | This is (A1)–(A2): η_n independent of Δ_n given F_n, **mean zero**. See 4.1 for what the author's R1 decision does to this. |
| 5 | E[Δ_n \| F_n, Δ̂_n] = μ_n + (τ_n²/s_n²)(Δ̂_n − μ_n) > 0 iff Δ̂_n > t\*_n | Needs τ_n > 0. At σ_n = 0 it gives t\*_n = 0, which is correct. |
| 6 | Value on I_nᶜ is V(t\*_n; μ_n, τ_n, σ_n), times P(I_nᶜ \| F_n) = 1 − π_n | **Depends on T2 Proposition 1 (P01)**, applied conditionally on F_n. On I_n, Δ_n = 0, so any decision contributes 0. |
| 7 | Reading: "the default rule is optimal for proposal n iff μ_n = 0" | Needs σ_n > 0 and π_n < 1 (audit). At σ_n = 0, t\*_n = 0 for every μ_n. |

**Assumptions the statement needs but does not list** (audit; revision §1): τ_n > 0 (at τ_n = 0 use the known-mean rule, 8′.4); π_n < 1 for t\*_n to be needed (at π_n = 1, V\*_n = 0); s_n > 0; positive probability of a_n = 1; restriction to D_nᶜ (duplicates, T4 §1); and the Gaussian law of (A1)–(A2) **relative to the information set actually used** (O_n in the revision: a new assumption, since a Gaussian law given F_n becomes a mixture given a coarser, policy-dependent O_n).

**The π_n question (audit).** F_n contains x_n and the incumbent. If no-op status were a function of those, π_n would be 0 or 1. A non-trivial π_n therefore means that the control plane does not know which keys the node actually uses. The same holds for O_n. Suggested: say this in one sentence where π_n is introduced.

## 3. Numerical check (run 22 Nov; `check_t2_p6.py`, output in `check_t2_p6_output.txt`, section P06)

- Bit-exact node, π = 0.4, μ = −0.3, τ = 0.6, σ = 0.8 (4 × 10⁶ draws): (1 − π)V(t\*) = 0.02447 against 0.02439 by simulation (s.e. 0.00009). A grid search over thresholds on the same draws puts the best threshold at +0.533, equal to t\* (grid step 0.05).
- σ = 0, μ = −0.7, τ = 0.5: t\* = 0, and V(0) = 0.01833 exceeds V(0.2) = 0.01432 and V(−0.2) = 0.00993, so at σ = 0 the default rule is optimal although μ ≠ 0 (reading in step 7 needs σ_n > 0).
- Sections 4.2 and 4.3 below have their own checks.

## 4. Points for the author to decide

### 4.1 The incumbent-error model you chose (R1 (ii)) and this keep rule

On 16 Nov you chose option (ii) of the revision's remark R1: the incumbent's recorded error e is a shared latent variable. The revision then notes (as analysis, not part of the decision) that Proposition 8′ parts 1–4 hold unchanged, but **the Gaussian closed form of this proposition does not apply directly**: given O_n the comparison noise is η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n, with mean (ϱ_n − 1)E[e | O_n] ≠ 0 after keeps. The Bayes rule then keeps iff Δ̂_n > t\*\*_n = −(1 − ϱ_n)E[e | O_n] − μ_n w_n²/τ_n², w_n² = σ_{c,n}² + (1 − ϱ_n)² Var(e | O_n), provided e | O_n is Gaussian and independent of Δ_n.

Checked numerically (digits-like scale from T5 and T2 §6: σ = 0.0125, ϱ = 0.82, μ = −0.004, τ = 0.009; the posterior of e is chosen for illustration, not measured):
- at an unselected record (E[e | O] = 0, sd(e | O) = σ), w_n² = 5.6250 × 10⁻⁵ = σ_d², so t\*\* = t\* and Proposition 6 with σ_n = σ_d is exactly right;
- at E[e | O] = 1σ, sd 0.5σ: the grid-best threshold equals t\*\* (+0.340 × 10⁻³, against t\* = +2.778 × 10⁻³); value per proposal 1.1945 × 10⁻³ with t\* against 1.2428 × 10⁻³ with t\*\* (paired s.e. of the difference 0.0007 × 10⁻³);
- at E[e | O] = 2σ, sd 0.5σ: t\*\* = −1.910 × 10⁻³ (grid best the same), value 1.0769 against 1.2394 × 10⁻³ (paired s.e. 0.0010 × 10⁻³).

T5 saw the same effect at campaign level (T5 §1: under the record model a dev-tuned constant threshold is "shifted down by 0.2–0.4 σ_d"; T5 §4: the lookahead gains come from lowering the threshold).

The deployed rule uses the uncorrected form: `C3_DESIGN.md` §1 says σ "is measured per node and edit kind (E1), not learned", and the keep rule is "keep iff Δ̂ > t\* = −μσ²/τ²".

**What to decide.**
1. What the paper calls the deployed keep rule. Under option (ii), H_n > t\*_n with the measured σ_n is the Bayes rule only for comparisons against an unselected record (or option (i), a re-measured incumbent). Elsewhere it is the Bayes rule of a declared model that ignores the record's selection. Suggested wording: "the Bayes threshold under (A2); under the shared incumbent error of Proposition [bias], (A2) holds only at an unselected record, and the threshold is not corrected for the record's selection".
2. Whether the manuscript's TBD in `theory.tex` ("Author decision on the incumbent-error model …") is replaced by the 16 Nov decision. `theory.tex` was last changed on 28 Oct and does not yet reflect it.
3. The exact corrected closed form needs e | O_n Gaussian. After a keep, e is selected (truncated), so it is not Gaussian; the rule "keep iff E[Δ_n | O_n, H_n] > 0" (8′.1) remains, but with no closed form. Whether this is worth stating, or left as "campaign gains are reported as measured" (R3), is your call. *Correction (23 Nov 2026, AI-checked under R1-PROOF-POLICY): the second sentence is false when O_n contains the recorded comparisons and the kernel or the shared-component model is the generative model; then e | O_n is exactly Gaussian (Kalman recursion) and the corrected rule has a closed form. See `AI_PROOF_CHECK_20261123.md` §2.3 (Lemma K) and `SPOT_CHECK_COORDINATOR_20261123.md` §2.3.*

### 4.2 Bit-exactness is not needed for the rule or the value (AI analysis, unreviewed)

On I_n, Δ_n = 0 whatever is observed. So, for any law of H_n on a no-op, E[Δ_n | O_n, H_n] = P(I_nᶜ | O_n, H_n) · m₁(H_n), where m₁ is the Gaussian posterior mean on I_nᶜ. Its sign is the sign of m₁(H_n) whenever P(I_nᶜ | ·) > 0, so the Bayes rule is H_n > t\*_n, and V\*_n = E[m_n⁺ | O_n] = (1 − π_n) E[m₁⁺ | I_nᶜ, O_n] = (1 − π_n)V(t\*_n). Bit-exactness only lets H_n = 0 identify a no-op, which changes no value.

Numerical check (same draws as section 3, but H = η on a no-op instead of 0): the mixture's Bayes rule agrees with H > t\* on every draw (agreement 1.000000), and its value is 0.02439 (s.e. 0.00009) against (1 − π)V(t\*) = 0.02447.

If this is right: (a) the manuscript's hypothesis "no-ops are observed exactly" can be dropped from the Gaussian part; (b) the revision's sentence (§1) "On non-bit-exact nodes … V\*_n is a mixture posterior value with no such closed form" is too strong for the no-op mixture (it stays right for metrics on a finite lattice, where the I_nᶜ component is not Gaussian). Both are for the author to accept or reject.

### 4.3 Smaller points

1. "What a learned model must supply is exactly (π_n, μ_n, τ_n)" (T4 Reading) holds under (A2) with σ_n known. Under 4.1 it must also supply, or the control plane must estimate, the record's posterior error.
2. The audit's restriction to D_nᶜ is essential: a duplicate's Δ̂_n is known before the run, and its Δ_n is not 0 (T4 §1).

## 5. If it checks out

Record an author row with errata: at least τ_n > 0, s_n > 0, π_n < 1, a_n = 1 of positive probability, D_nᶜ, the Gaussian law relative to O_n, σ_n > 0 for the "iff μ_n = 0" reading, and the decision in 4.1 on what the threshold is optimal for. With P01 also checked, the Gaussian part of the manuscript's "One-step index" can then move to the main text with the scope sentence from 4.1.
