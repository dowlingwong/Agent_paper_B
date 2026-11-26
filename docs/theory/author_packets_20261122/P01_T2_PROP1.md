AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T2 Proposition 1 (default rule, Bayes threshold, value formula V(t))

*It replaces the short packet `author_packets_20261027/P01.md` for this statement. Source: `../T2_DERIVATIONS.md` §2 on this branch (`main` @ `3c3f822a` + `b3400558`). Audit: `../T_AUDIT_20261027.md` ("Wrong (edge-case claim in the proof); main formula correct with added assumptions"). Proposed correction (not adopted): `../../proposals/THEORY_CORRECTIONS_20261027.md` §"T2 Proposition 1". Analysis marked "AI analysis, unreviewed" is new in this packet and has not been reviewed by anyone.*

**Why this one comes first.** T4 Proposition 7 differentiates V(t) (P07 step 1), T4 Proposition 6 takes its value V*_n from it, and the manuscript defines V in `papers/r1/sections/theory.tex` and states "the default rule (t = 0) is optimal for a proposal only if μ_n = 0". The D4 amendment (PLAN §10) cites T2 Proposition 1 and T4 Proposition 6 for the declared threshold rule. None of these can be marked author-checked before this statement is.

## 0. Has T2 been revised since the audit?

No. The only change to `T2_DERIVATIONS.md` after the audit is the "Historical protocol context" banner added on 27 Oct (commit `c5ea0374`; the banner itself says "the derivations and their assumptions are unchanged"). Every ref in the repository carries the same T2 text (blob `693efb68`) or the version before the banner. PLAN R1-THEORY-REPAIR-PROPOSAL and R1-T4-DI-FIX say that T2 stays unchanged and that corrections are proposals for the author. The corrections for Propositions 1, 2 and 5 exist only in `THEORY_CORRECTIONS_20261027.md`, which is marked "not adopted, not author checked". This applies to P01–P05.

## 1. Statement to check (as currently written)

For the threshold rule ρ_t, with s² = τ² + σ_d² and z = (t − μ₀)/s:

- V(t) := E[Δ · 1{Δ̂ > t}] = μ₀ Φ(−z) + (τ²/s) φ(z);
- V is maximised at t\* = −μ₀ σ_d²/τ²; equivalently, keep iff E[Δ | Δ̂] > 0;
- the default rule (t = 0) is optimal if and only if μ₀ = 0;
- its single-decision error rate on a fixed increment Δ is Φ(−|Δ|/σ_d);
- (in the proof) "Edge case: if σ_d = 0, every threshold in (−∞, 0] is optimal, so 'only if' needs σ_d > 0."

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | (Δ, Δ̂) bivariate normal, means (μ₀, μ₀), Var Δ̂ = s², Cov = τ² | Needs Δ, e_t, e_s **mutually independent and jointly Gaussian** (audit: T2 §1 declares only marginals). Not stated in T2 §1. |
| 2 | E[X 1{Y > t}] = μ_X P(Y > t) + Cov(X, Y) φ((t − μ_Y)/s_Y)/s_Y | Regression decomposition X = μ_X + (Cov/s_Y²)(Y − μ_Y) + independent noise, plus E[(Y − μ_Y)1{Y > t}] = s_Y φ(·). Two lines by hand. Needs s > 0. |
| 3 | dV/dt = −f_Δ̂(t) E[Δ \| Δ̂ = t] | Differentiate step 2 (φ′(z) = −zφ(z)), or the general identity. One line. |
| 4 | E[Δ \| Δ̂ = t] = μ₀ + τ²(t − μ₀)/s² vanishes only at t\* and increases in t | Needs **τ > 0** (else t\* is undefined and the posterior mean is constant). Then t\* is the unique maximiser among thresholds. |
| 5 | "equivalently, keep iff E[Δ \| Δ̂] > 0" | The two rules coincide (step 4). The proof shows optimality **among thresholds**. Optimality among all measurable keep rules needs the one-line pointwise argument used in T4 Proposition 6 (E[Δk] = E[k E[Δ \| Δ̂]]). The proposed correction states it that way. |
| 6 | default rule optimal iff μ₀ = 0 | t\* = 0 iff μ₀σ_d² = 0. "Only if" needs **σ_d > 0** (T2 notes this). |
| 7 | error rate Φ(−\|Δ\|/σ_d) | For Δ > 0: P(Δ + e ≤ 0); for Δ < 0: P(Δ + e > 0). Needs **Δ ≠ 0 and σ_d > 0**; at Δ = 0 the "sign error" needs a convention (audit). |
| 8 | edge case σ_d = 0: "every t ≤ 0 is optimal" | **False (audit), and still in the current text.** At σ_d = 0, τ > 0, V(t) = E[Δ 1{Δ > t}], which is uniquely maximised at t = 0 for every μ₀: a threshold t < 0 also keeps the negative increments in (t, 0). The conclusion drawn from it ("only if needs σ_d > 0") is right; the reason given is wrong. |

**Assumptions the statement needs but does not list** (audit, and the proposal): τ > 0; σ_d > 0 for the iff and for the error rate; Δ ≠ 0 for the error rate; joint Gaussianity and independence of Δ, e_t, e_s. At τ = 0 the known-mean rule applies (keep iff μ₀ > 0); the proposed correction says so.

**One more scope condition (AI analysis, unreviewed).** The proposition is about its own one-trial model, in which the comparison noise e_t + e_s has mean zero and is independent of Δ. In a campaign that holds for a comparison against an incumbent whose recorded error is not selected (for example the start configuration). After a keep, under T4 §5's record model or under a shared-noise model, the comparison noise given the history has a non-zero mean (T4 revision remark R1; P09 §4; P06 §4 here). The algebra is unaffected; the application to later trials is. The author chose option (ii) for this (R1-T4-PROOF-CHECK); P06 shows what it does to the threshold.

## 3. The audit and the current text

| Audit finding (27 Oct) | In current T2? | In the proposal (not adopted)? |
|---|---|---|
| Edge assertion at σ_d = 0 is false; t = 0 is the unique optimum | No: the false sentence is still there | Yes: removed, replaced by "at σ = 0 and τ > 0, threshold zero is optimal for every μ" |
| τ = 0 makes t\* undefined | No | Yes: known-mean action |
| Error rate needs Δ ≠ 0 and a tie convention | No | Partly: "for a fixed nonzero Δ" |
| Joint Gaussianity / independence must be assumed | No | Yes: "H = Δ + ε with ε ∼ N(0, σ²) independent, τ > 0 and σ > 0" |
| Optimality among all measurable rules | Not claimed | Yes: stated among measurable decisions |

So the audit's points are addressed in the proposal, not in T2.

## 4. Numerical check (run 22 Nov; `check_t2_p6.py`, output in `check_t2_p6_output.txt`, section P01)

- Value formula against an independent quadrature over Δ (E[Δ Φ((Δ − t)/σ_d)]), 1,000 random parameter sets: maximum difference 1.8 × 10⁻¹⁴. Against simulation (4 × 10⁶ draws, μ = −0.4, τ = 0.7, σ_d = 1.1, t = 0.3): 0.01153 against 0.01146 (s.e. 0.00017).
- t\* is the maximiser: in 0 of 1,000 sets does any point of a 20,001-point grid beat V(t\*); dV/dt changes sign from + to − at t\* in all 741 sets where the check is numerically reliable (|t\* − μ| < 2s).
- "keep iff posterior mean > 0" and "Δ̂ > t\*" agree on every one of 2 × 10⁵ draws.
- Error rate, σ_d = 0.8, 4 × 10⁶ draws: Δ = −0.5: 0.26599 against 0.26579; Δ = +0.2: 0.40129 against 0.40128; Δ = +1.0: 0.10565 against 0.10559.
- Edge case σ_d = 0, μ = 0, τ = 1: V(0) = 0.39894, V(−0.1) = 0.39695, V(−1) = 0.24197, so t ≤ 0 is not "every threshold optimal". On a grid over [−2, 2] the argmax is t = 0 for μ = −0.5, 0 and +0.5.

These confirm the algebra of the main formula and the audit's counterexample. They do not check the joint-Gaussian modelling assumption or its fit to real nodes (T2 §8: heavy tails on some edits).

## 5. Points for the author to decide

1. **The edge-case sentence.** Accept the audit's correction (t = 0 is the unique optimum at σ_d = 0, τ > 0, for every μ₀), as in the proposal, or give another wording. The T2 file still carries the false sentence; it should not be copied into any appendix.
2. **Conditions in the statement.** Add τ > 0, σ_d > 0 (for the iff and the error rate), Δ ≠ 0 (error rate), and the joint-Gaussian independent-noise assumption. The manuscript's definition of V already says "η ∼ N(0, σ²) independent of Δ"; its "only if μ_n = 0" needs σ_n > 0, which the manuscript's "noise with a continuous law" implies.
3. **Optimality class.** Decide whether the paper claims optimality among thresholds (what the T2 proof shows) or among all measurable keep rules (one more line, as in T4 Proposition 6).
4. **Scope in a campaign.** Decide whether the manuscript states, next to V, that the zero-mean independent noise holds for comparisons against an unselected record only, and refers to the incumbent-error model chosen in R1-T4-PROOF-CHECK (option (ii)) for later comparisons.
5. **Editorial.** The "Implementability" paragraph (D4 forbids ρ_t) is historical: the D4 amendment now allows a declared threshold rule.

## 6. If it checks out

Record an author row with errata: (1) the σ_d = 0 sentence replaced; (2) τ > 0, σ_d > 0, Δ ≠ 0 and the independence assumption added. Then P07 step 1 and P06 step 6 can cite it, and V(t) and the "default rule optimal only if μ = 0" sentence can stay in the main text.
