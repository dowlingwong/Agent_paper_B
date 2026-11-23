# T2 — When verification and thresholds are worth their cost

> **Historical protocol context.** PLAN §10 later adopts the D4 amendment, the `vary` split policy and D23. Questions below about permitting thresholds and posterior-mean verify, and the unadopted D23 proposal, describe the earlier state. The derivations and their assumptions are unchanged and remain subject to independent audit and author checking.

*Theory track T2 (RUNBOOK §3). Drafted 12 Oct 2026 by an AI agent (Claude) at the author's request. AI-assisted; the author has not checked these proofs yet, and no human has reviewed them (PLAN §9 item 6 requires both before any of this enters a manuscript). Every closed form below is implemented in `r1/theory/acceptance.py` and checked against Monte Carlo in `r1/tests/test_t2_acceptance.py` (20 tests). Numbers quoted from E1 are `PILOT` values (docs/r1/reports/NOISE_FLOOR_20261012.md).*

Notation follows T1 (`docs/r1/theory/T1_MODEL.md`). Φ and φ are the standard normal cdf and pdf; ψ(z) = φ(z) − z Φ(−z) for z ≥ 0 is the knowledge-gradient kernel.

## 1. The one-trial model

At epoch E2 of one trial the campaign has a candidate c and an incumbent c_inc.

- **Proposal law.** The true increment Δ = J(c) − J(c_inc) is a draw from N(μ₀, τ²), the node's distribution of true increments under its proposer. μ₀ < 0 means that most proposals hurt.
- **Campaign comparison.** Δ̂ = Δ + e_t + e_s, with e_t ∼ N(0, σ_t²) from the training seed and e_s ∼ N(0, σ_s²) from the split seed; σ_d² = σ_t² + σ_s². These are *paired* noise terms: a local edit with per-run noise σ and cross-configuration correlation ϱ has σ_d² = 2σ²(1 − ϱ). E1 measures σ_t and σ_s per edit directly.
- **Verify(r).** r paired fresh-seed differences. Under the `"vary"` split policy, D_i = Δ + ξ_i with ξ_i ∼ N(0, σ_d²). Under `"fixed"`, D_i = Δ + e_s + ξ_i with ξ_i ∼ N(0, σ_t²): the campaign's own split error e_s is reused, not resampled. D̄ is their mean.
- **Responses.** The default rule ρ keeps iff Δ̂ > 0. A threshold rule ρ_t keeps iff Δ̂ > t. The harness's frozen verify response keeps iff D̄ > 0 (`_run_verify`). The Bayes response keeps iff E[Δ | Δ̂, D̄] > 0.
- **Value.** In the additive model, the final audited improvement is the sum of the true increments that were kept, so the value of one decision is E[Δ · 1{keep}]. §5 says where the additive model fails.

## 2. Proposition 1 — the default rule and the Bayes threshold

*Status (23 Nov 2026): AI-checked under R1-PROOF-POLICY, not author-checked. Check (a): `author_packets_20261122/AI_PROOF_CHECK_20261123.md` §1; check (b): `author_packets_20261122/SPOT_CHECK_COORDINATOR_20261123.md` §1. The changes those checks proposed are applied below (assumptions made explicit; the σ_d = 0 edge case corrected).*

**Statement.** Assume Δ, e_t and e_s are mutually independent (so Δ̂ − Δ ∼ N(0, σ_d²) is independent of Δ) and τ > 0. For the threshold rule ρ_t, with s² = τ² + σ_d² and z = (t − μ₀)/s:

  V(t) := E[Δ · 1{Δ̂ > t}] = μ₀ Φ(−z) + (τ²/s) φ(z).

V is uniquely maximised over t ∈ ℝ at t* = −μ₀ σ_d² / τ². Equivalently, keep iff the posterior mean E[Δ | Δ̂] is positive. If σ_d > 0, the default rule (t = 0) is optimal if and only if μ₀ = 0. If σ_d > 0, its single-decision error rate on a fixed increment Δ ≠ 0 is Φ(−|Δ|/σ_d).

**Proof.** (Δ, Δ̂) is bivariate normal with means (μ₀, μ₀), Var Δ̂ = s² and Cov(Δ, Δ̂) = τ². For a bivariate normal (X, Y), E[X · 1{Y > t}] = μ_X P(Y > t) + Cov(X, Y) φ((t − μ_Y)/s_Y)/s_Y. This follows from X = μ_X + (Cov/s_Y²)(Y − μ_Y) + independent noise, together with E[(Y − μ_Y) 1{Y > t}] = s_Y φ((t − μ_Y)/s_Y). Differentiating, dV/dt = −f_Δ̂(t) · E[Δ | Δ̂ = t]. This is zero exactly where the posterior mean μ₀ + τ²(t − μ₀)/s² vanishes, i.e. at t = −μ₀σ_d²/τ². The posterior mean is increasing in t, so dV/dt is positive below t* and negative above it, and t* is the unique maximiser. The error rate is P(sign(Δ + e) ≠ sign Δ) = Φ(−|Δ|/σ_d). ∎ (Edge cases: if σ_d = 0, then t* = 0 and dV/dt = −t f_Δ(t), so t = 0 is the unique optimal threshold for every μ₀; hence "only if" needs σ_d > 0. If τ = 0, keep iff μ₀ > 0. *Corrected 23 Nov 2026: the earlier text said every threshold in (−∞, 0] is optimal when σ_d = 0, which is false.*)

**Reading.** t* is the Ladder idea (Blum & Hardt 2015) with a Bayes justification: raise the bar in proportion to how often proposals hurt (−μ₀/τ²) and to how noisy one comparison is (σ_d²). Two consequences:
- When μ₀ < 0, ρ accepts too many noise-driven keeps.
- When μ₀ < 0, t*/σ_d = −μ₀σ_d/τ² grows with σ_d, so noisy nodes need a higher bar.

**Implementability.** Under D4 the keep rule may change only through verify's frozen response, so ρ_t cannot be deployed directly. Its implementable form is "verify when 0 < Δ̂ < t" (§3). The offline table reports ρ_t only as a reference. (Question for the author: whether D4 should allow a declared threshold keep rule as its own action version.)

## 3. Proposition 2 — the value of information of verify(r)

*Status (23 Nov 2026): AI-checked under R1-PROOF-POLICY, not author-checked. Check (a): `author_packets_20261122/AI_PROOF_CHECK_APPENDIX_20261123.md` §1; check (b): `author_packets_20261122/SPOT_CHECK_APPENDIX_COORDINATOR_20261123.md` §1. The changes check (a) §1.3 (1–4) proposed are applied below (assumptions made explicit; the case s̃ = 0; "with diminishing returns" corrected; concavity of s̃² in r proved for both split policies).*

**Statement.** Assume Δ, e_t, e_s and the replicate errors are mutually independent Gaussians (under `"fixed"`, e_s is reused), and r ≥ 1 is an integer. Write m = E[Δ | Δ̂] and v = Var(Δ | Δ̂). Let s̃² = Var(E[Δ | Δ̂, D̄] | Δ̂) be the preposterior variance; it is computed by Gaussian conditioning on the joint covariance of (Δ, Δ̂, D̄) (`preposterior_sd`). With the Bayes response, the value of information is

  VoI_r(Δ̂) = E[max(E[Δ | Δ̂, D̄], 0) | Δ̂] − max(m, 0) = s̃ ψ(|m| / s̃) for s̃ > 0; VoI_r := 0 if s̃ = 0.

VoI_r is
- maximal where m = 0 (i.e. at Δ̂ = t*);
- decreasing in |m|, hence in the distance |Δ̂ − t*|;
- increasing in r. Diminishing returns hold at m = 0, where VoI_r = s̃φ(0), but not in general: for m ≠ 0 the increments in r can increase. *(Corrected 23 Nov 2026; AI-checked under R1-PROOF-POLICY, not author-checked: the earlier text said "with diminishing returns", which is false for m ≠ 0.)*

**Proof.** Given Δ̂, the updated mean M′ = E[Δ | Δ̂, D̄] is normal with mean m (tower property) and variance s̃². For M′ ∼ N(m, s̃²), E[max(M′, 0)] = m Φ(m/s̃) + s̃ φ(m/s̃). Subtracting max(m, 0) and using Φ(x) = 1 − Φ(−x) gives s̃ [φ(m/s̃) − (|m|/s̃) Φ(−|m|/s̃)] = s̃ ψ(|m|/s̃). This is the knowledge-gradient formula of Frazier, Powell & Dayanik (2008) applied to a two-alternative choice (keep or discard).
- ψ is decreasing on [0, ∞), since ψ′(z) = −Φ(−z) < 0.
- s̃² = v − Var(Δ | Δ̂, D̄), and conditioning on more independent replicates lowers the second term, so s̃ increases in r. Under either policy D̄ = L + ξ̄, with ξ̄ fresh of variance s²/r (vary: L = Δ, s² = σ_d²; fixed: L = Δ + e_s, s² = σ_t²). So s̃² = c²/(w + s²/r), with c = Cov(Δ, L | Δ̂) and w = Var(L | Δ̂), is increasing and concave in r. That concavity does not carry over to VoI_r, which is convex in s̃ for m ≠ 0 (d²VoI/ds̃² = (m²/s̃³)φ(m/s̃)). With τ² = 2, σ_d² = 1, μ₀ = 0 and Δ̂ = 4.5 (m = 3), the vary increments over r = 1, …, 5 are 6.88e-8, 3.94e-7, 7.51e-7 and 9.62e-7 (`AI_PROOF_CHECK_APPENDIX_20261123.md` §1).
∎

**The harness's frozen response is not the Bayes response.** (L14 review: the figures below are for the `"vary"` policy. Under the adopted `"fixed"` policy the loss at Δ̂ = 2σ_d is about 1–2 × 10⁻⁵.) Keeping iff D̄ > 0 throws away Δ̂. Its value, E[Δ · 1{D̄ > 0} | Δ̂] (`frozen_response_value`), is below the Bayes value. Far from the boundary it can be *worse than not verifying*: at Δ̂ = 2σ_d on a digits-like node, the frozen response loses about 0.0003 against ρ, because a noisy D̄ vetoes a confident keep. (Question for the author: whether verify's frozen response should be the posterior-mean rule instead. It would still be frozen and declared in advance.)

## 4. Proposition 3 — verify can only correct the noise it resamples

*Status (23 Nov 2026): AI-checked under R1-PROOF-POLICY, not author-checked. Check (a): `author_packets_20261122/AI_PROOF_CHECK_APPENDIX_20261123.md` §2; check (b): `author_packets_20261122/SPOT_CHECK_APPENDIX_COORDINATOR_20261123.md` §2. The changes check (a) §2.3 (2–4) proposed are applied below (the `"vary"` limit stated as pointwise; the two gaps of the proof closed by explicit limits).*

**Statement.** Under the `"fixed"` split policy, VoI_r^fixed(Δ̂) → 0 as σ_t → 0, for every Δ̂, r and σ_s. Under `"vary"`, VoI_r^vary(Δ̂) has a positive limit as σ_t → 0 for each fixed Δ̂, whenever τ, σ_s > 0. The limit is pointwise in Δ̂, not uniform: it tends to 0 as |Δ̂| → ∞. (μ, τ, σ_s and r fixed; the independence assumptions of §3.)

**Proof.** Under `"fixed"`, D̄ − Δ̂ = ξ̄ − e_t, where ξ̄ ∼ N(0, σ_t²/r) is independent of e_t ∼ N(0, σ_t²). Hence Var(D̄ − Δ̂) = σ_t²(1 + 1/r) → 0. With A = τ² + σ_s² and u = σ_t², Cov(Δ, D̄ | Δ̂) = τ²u/(A + u) and Var(D̄ | Δ̂) = u(1 + 1/r − u/(A + u)), so s̃² = τ⁴u/((A + u)²(1 + 1/r − u/(A + u))) = O(u). (If A = 0, Δ is constant and VoI = 0.) Hence s̃ → 0 and VoI = s̃ ψ(|m|/s̃) ≤ s̃ φ(0) → 0.

Under `"vary"`, D̄ = Δ + ξ̄ with Var ξ̄ = σ_d²/r, independent of (Δ, e_t, e_s). Conditioning on D̄ in addition to Δ̂ strictly lowers Var(Δ | ·) when τ > 0 and σ_d > 0. As σ_t → 0, v → v₀ = τ²σ_s²/A > 0 and s̃² → v₀²/(v₀ + σ_s²/r) > 0, while m stays finite at fixed Δ̂. So VoI tends to a positive value. ∎

**What E1 says.** On the OpenML logistic-regression nodes the training seed does not move the metric at all (σ_train = 0.0000 on all five nodes). On those nodes `"fixed"` verify is worthless *by construction*, whatever the budget. For model-type edits the ratio sd_train/sd_joint is 0.06–0.39. On `digits_mlp` and `tabular_mlp` it is 0.56–0.65, so `"fixed"` recovers about half of the value of `"vary"` (table in §6). This is a direct, cheap test of the theory, and it bears on the 9 Oct verify-split decision (keep `"fixed"` everywhere).

## 5. Proposition 4 — the incumbent's recorded value drifts upward, and true improvements stall

The additive model of §1 treats each decision separately. The harness couples them through B = `current_best`, the recorded metric of the incumbent.

**Setting.** Let e be the incumbent's recorded error, B = J(c_inc) + e. A candidate with true improvement δ over the incumbent has error ε_c. Assume (ε_c, e) is bivariate normal with equal variance σ² and correlation ϱ:
- ϱ = 0 is the fresh-draw regime (GPU or timing-based nodes);
- ϱ > 0 is the CRN regime with a local edit (CPU nodes; E1 measures ϱ_joint between 0.39 and 1.00 per edit).

**Statement (a): acceptance given the incumbent's error.**

  P(keep | e) = Φ((δ − (1 − ϱ) e) / (σ √(1 − ϱ²))).

It is decreasing in e for every ϱ < 1.

**Scope of (a).** *Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked. Statement (a) and its proof are unchanged.* The proof uses the conditional law ε_c | e ∼ N(ϱe, σ²(1 − ϱ²)), with σ > 0 and −1 < ϱ < 1. It must be the law **given the actual history**, not only given e (27 Oct audit): a selected incumbent error need not keep the unconditional bivariate-normal law. (a) is therefore exact for ϱ = 0 when candidate errors are fresh draws independent of the past (after any number of keeps); for ϱ > 0 at a comparison against an unselected record about which the history carries no further information; and for a record that was kept only under a model that imposes this kernel at every step (T3's `crn` regime, T5's `record` noise model). Under a shared-component model (every run's error u + v, u shared by the campaign with variance ϱσ², v fresh with variance (1 − ϱ)σ²) it fails for a record that was kept: at `digits_mlp`-like parameters (σ = 0.0125, ϱ = 0.8, δ = 0.005, e = σ) the acceptance after one null keep is 0.5322 against the formula's 0.6306 (`author_packets_20261122/P04_T2_PROP4.md` §4; `check_t2_p6_output.txt`, section P04). This is the same scope as T4 Corollary 9a; the kernel-free statement is T4 Proposition 9 (restated 22 Nov 2026).

**Statement (b): stagnation under null proposals, fresh-draw regime.** Suppose ϱ = 0 and a stretch of proposals has no true effect. Then each keep happens exactly when a fresh draw exceeds the record, so e_n is the running maximum of n i.i.d. N(0, σ²) draws. Then:
- e_n → ∞ almost surely, and E[e_n] equals the expected maximum of n draws, ≈ σ√(2 ln n);
- for any fixed true improvement δ, P(keep δ at step n) → 0 almost surely.

**Proof.**
- (a): ε_c | e ∼ N(ϱe, σ²(1 − ϱ²)), and keep iff δ + ε_c > e. Monotonicity in e follows because the coefficient −(1 − ϱ) is negative.
- (b): The maximum of n i.i.d. normal draws diverges almost surely, and its mean grows like σ√(2 ln n) by standard extreme-value asymptotics. Then apply (a) with ϱ = 0 and e_n → ∞.
∎

**Reading.**
- With fresh draws, a noisy keep is not just a one-off loss. It raises the bar for every later trial, which is the stagnation hypothesis H3.
- Under CRN with local edits, and under the kernel model of (a), the effect is damped by the factor (1 − ϱ), but not removed; under the shared-component model the damping is weaker (P04 §4, stagnation table). On `digits_mlp` (σ ≈ 0.0125 per run, ϱ ≈ 0.8, i.e. 1 − ϱ ≈ 0.2), an incumbent recorded one σ too high lowers the acceptance of a true +0.005 edit from Φ(0.005/0.0075) = 0.75 (an unbiased, unselected record) to 0.63 or 0.53 after one keep, depending on the error model. These are the values under the two models after one keep, not bounds: Φ(0.0025/0.0075) = 0.63 under the kernel of (a) (an unselected record, or a kept record under the kernel model), and 0.53 for a record kept once by a null keep under the shared-component model (simulation, s.e. ≤ 0.0009; `author_packets_20261122/P04_T2_PROP4.md` §4, `check_t2_p6_output.txt`, section P04). Under the shared-component model further keeps lower the acceptance further (an unreviewed simulation in `../reviews/THEORY_RHO_REVIEW_20261122.md`, N3, gives 0.465 after two null keeps). *(Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked. The 12 Oct text gave 0.63 only; the qualification of "damped by (1 − ϱ)" and the wording "values after one keep, not bounds" were added in the review round.)*
- Re-measuring the incumbent resets e to a fresh draw. That is the one place where repeated evaluation has value beyond the current decision.
- This is the mechanism that the additive value of §3 leaves out. A campaign-level study (T3, E1b) must therefore measure it rather than assume it.

## 6. Proposition 5 — the verify index and the price of a run

**Index.** Under a hard budget of worker runs, verify(r) costs 2r runs that could instead go to fresh proposals. Let g be the value of one run spent on a fresh proposal. In the stationary additive model with the Bayes threshold, g = V(t*) per run (`run_price`). The KG-style index policy is:

  at E2, verify iff VoI_r(Δ̂) > 2r · g and at least 2r runs remain; otherwise continue.

This is implementable under D4, because it only decides *whether* to verify. It is the D23 KG-style candidate.

**Immediate consequence (a falsifiable prediction).** VoI_r ≤ s̃ φ(0) ≤ √v φ(0), where v = Var(Δ | Δ̂). In the Gaussian model, s̃ and v do not depend on Δ̂ or μ₀, so the maximum VoI (attained at m = 0) is the same for both proposal laws below (corrected after the L14 review). So whenever 2r · g ≥ √v φ(0), the index never verifies: a fixed budget is better spent on fresh proposals. With E1-scale parameters this is the typical case. On a `digits_mlp`-like node:

| Proposal law | g = V(t*) per run | max VoI of verify(2), `vary` | max VoI, `fixed` | Verify ever worth 4 runs? |
|---|---|---|---|---|
| μ₀ = 0, τ = 0.009 | 0.0026 | 0.0018 | 0.0009 | no |
| μ₀ = −0.004, τ = 0.009 | 0.0011 | 0.0018 | 0.0009 | no (needs g < 0.00044) |

The verify region opens only when g is small, that is, when fresh proposals rarely improve. Three sources make that happen:
1. **Diminishing returns late in a campaign.** μ₀ falls as the incumbent improves, so g(B) falls with spent budget. *This is how remaining budget enters the index.*
2. **An LLM-call cap that binds before the run budget.** A fresh proposal costs an LLM call and verify does not, so the effective price of verify falls.
3. **The stagnation externality of §5.** It is not in g, and it adds value to correcting a false keep.

**Prediction for E1b and Phase 1.** On E1-like nodes, the headroom of verify-based control over ρ at matched compute is small, unless the campaign runs into diminishing returns or the LLM cap binds. This agrees with the evolutionary-computation result that ignoring noise can beat re-evaluation (Antipov & Doerr 2024), and it says when that result flips. If E1b finds large verify headroom early in a campaign, the additive model is wrong for the harness, and §5 is the first suspect.

## 7. Proposed D23 (for the author; not adopted)

- **Primary comparator: the KG-style index of §6.** Reasons:
  - it uses exactly the quantities E1 measures (σ_t, σ_s, ϱ);
  - it is implementable under D4;
  - it has a closed form and a stated optimality scope (myopic, additive model);
  - it makes the sharp prediction above.

  Its proposal-law parameters (μ₀, τ) and the run price g come from development campaigns only.
- **Second comparator: a PACE-style gate**, as its own declared verify version. It always verifies, with an anytime-valid e-process response at level α and a run cap. It guards a different target: false commits, not value. Note that its response differs from the frozen D̄ > 0 rule, so it is a new action version under D4.

## 8. What is not shown here

- No result covers the full campaign with a feedback proposer. §5 is the only multi-step statement, and it assumes null proposals.
- The Gaussian model is checked only by simulation against itself. Its fit to real nodes is a T3/E1b question. E1 shows heavy-tailed paired differences on some edits (for example `openml_ionosphere`, gradient boosting, sd_split 0.069).
- The stationary price g is a modelling choice. A dynamic-programming price over the remaining budget is the natural next step, and it is where the RL question of PLAN §5.5 enters.
