AI-assisted (Claude, subagent, 23 Nov 2026). The AI proof check under PLAN row R1-PROOF-POLICY.

# AI proof check: T2 Proposition 1; T4 Propositions 6, 7 (with Corollary 7a), 9 (with Corollary 9a) and 10(b)

This is check (a) of R1-PROOF-POLICY. It is not an author check. The coordinating chat's spot check (b) is separate; `AI_PROOF_CHECK_CHECKLIST_20261123.md` lists what it should re-derive. Nothing here changes a theory note, the manuscript, a PLAN row or an existing packet.

**Texts checked.** `../T2_DERIVATIONS.md` §2 and `../T4_FEEDBACK_PROPOSER.md` §§2, 3, 5, 6 at `mac-theory-rho-20261122` @ `cdec7b0e`. Line numbers below (T2:n, T4:n) refer to that commit. Read first: the README and packets P01, P06, P07, P09 of this folder with their scripts and outputs, `../T_AUDIT_20261027.md`, `../../proposals/THEORY_CORRECTIONS_20261027.md`, `../../proposals/T4_PROP10_REVISION_20261028.md` (revision 3), `../../reviews/THEORY_RHO_REVIEW_20261122.md`, and PLAN rows R1-T4-PROOF-CHECK, R1-THEORY-RHO, R1-PROOF-POLICY, R1-E1-PILOT-ACCEPT on `author-minsub-20261122`.

**Method.** Each statement is restated with every assumption it needs. Each proof step is classified as **proven**, **proven with an added assumption** (named), **gap** or **false** (with a counterexample). Evidence is kept in three kinds:
- *symbolic*: a SymPy identity whose printed difference is 0;
- *argument*: a short proof written out here;
- *numeric*: a check at random or extreme parameters. Numeric lines are evidence, not proofs.

Evidence is cited as `out:L (label)`, the line L of `ai_proof_check_20261123_output.txt`, produced by `ai_proof_check_20261123.py` (fixed seeds; the output is byte-reproducible, run time about 2–3 minutes). Lines 1–98 come from the first, interrupted run of this check; this session re-ran them with the same result and added lines 99–130 (XS1–XS4, XN1–XN3) with their own generator. All numbers below are copied from that output or from a cited file.

## Summary

| # | Statement | Readiness | Most important point |
|---|---|---|---|
| 1 | T2 Prop. 1 | **ready after the proposed changes** | The σ_d = 0 sentence (T2:27) is false: t = 0 is the unique optimum for every μ₀. τ > 0, σ_d > 0 (for the "iff" and the error rate), Δ ≠ 0 and independent Gaussian noise must be stated. |
| 2 | T4 Prop. 6 and its scope paragraph | **ready after the proposed changes** | The proposition needs τ_n > 0, D_nᶜ and π_n < 1 (or V\*_n := 0); its proof's use of bit-exactness can be dropped. **New:** the scope sentence "after a keep e is truncated, not Gaussian, so t\*\*_n is an approximation there, and the exact rule has no closed form" (T4:48) is false under the paragraph's own error models: given the ledger, the record error is exactly Gaussian (a Kalman recursion), so t\*\*_n is exact and Var(e \| F_n) ≤ σ² holds automatically. |
| 3 | T4 Prop. 7 and Cor. 7a | **ready after the proposed changes** | Identity, bounds and local form hold; add τ_n > 0 and a finite t̃, and read [t̃, t\*_n] unordered. Cor. 7a must cite (NF) with an execution rule that does not read past keeps (revision R3), not the 18 Oct DI. |
| 4 | T4 Prop. 9 (restated, (i)–(iv)) and Cor. 9a | **ready as written** | All parts check, including the null-set step of (ii.1) and the restriction "\| K" on the right of (iv). One status sentence in the corollary's scope is stale (R1-E1-PILOT-ACCEPT); it is not part of the statement. |
| 5 | T4 Prop. 10(b) | **ready after the proposed changes** | The example is correct. One literal error: "for α < 1.61 the myopic rule loses 1.61 − α" should use G(2, 1) = 1.609548…; for α between G(2, 1) and 1.61 the loss is 0. |

No step of the five main statements is rated a gap after the proposed changes. Two sentences are rated **false**: T2:27's edge case, which the audit already found, and T4:48's "truncated, not Gaussian", which is new here.

---

## 1. T2 Proposition 1 (T2:19–27)

### 1.1 Signable statement

Let Δ ∼ N(μ₀, τ²) with **τ > 0**, and Δ̂ = Δ + η, where η ∼ N(0, σ_d²), σ_d ≥ 0, is **independent of Δ**. In T2 §1, η = e_t + e_s with Δ, e_t, e_s mutually independent, so σ_d² = σ_t² + σ_s². Put s² = τ² + σ_d², z = (t − μ₀)/s and t\* = −μ₀σ_d²/τ². Let f be the N(μ₀, s²) density.
- (a) For every t ∈ ℝ, V(t) := E[Δ · 1{Δ̂ > t}] = μ₀Φ(−z) + (τ²/s)φ(z).
- (b) V′(t) = −(τ²/s²) f(t)(t − t\*). So V is strictly increasing on (−∞, t\*] and strictly decreasing on [t\*, ∞), and t\* is the unique maximiser of V over ℝ.
- (c) Δ̂ > t\* if and only if E[Δ | Δ̂] > 0. *(Optional addition.)* This rule maximises E[Δ k(Δ̂)] over all measurable k: ℝ → {0, 1}.
- (d) If **σ_d > 0**, the default rule (t = 0) is optimal if and only if μ₀ = 0. If σ_d = 0, t = 0 is the unique optimal threshold for every μ₀.
- (e) If **σ_d > 0**, then for a fixed **Δ ≠ 0** the default rule decides wrongly (it keeps when Δ < 0, or discards when Δ > 0) with probability Φ(−|Δ|/σ_d). At Δ = 0 the probability of a keep is 1/2.
- If τ = 0, the threshold formula does not apply: keep iff μ₀ > 0 (ties at μ₀ = 0).

### 1.2 Steps

| Step | Claim (T2:27 unless noted) | Verdict | Evidence |
|---|---|---|---|
| 1 | (Δ, Δ̂) is bivariate normal with means (μ₀, μ₀), Var Δ̂ = s², Cov = τ² | **proven with an added assumption**: Δ, e_t, e_s mutually independent and Gaussian. T2 §1 gives only the marginals (audit). | argument |
| 2 | E[X 1{Y > t}] = μ_X P(Y > t) + Cov(X, Y) φ((t − μ_Y)/s_Y)/s_Y, via E[(Y − μ_Y)1{Y > t}] = s_Y φ(·) | **proven** (s > 0) | symbolic out:4 (S1.1), out:5 (S1.2); numeric out:31 (N1.1: 600 sets, max abs diff 7.1e-15) |
| 3 | dV/dt = −f(t) E[Δ \| Δ̂ = t] | **proven** | symbolic out:6 (S1.3) |
| 4 | the posterior mean μ₀ + τ²(t − μ₀)/s² vanishes only at t\* and increases in t, so t\* is the unique maximiser | **proven with an added assumption**: τ > 0. Otherwise t\* is undefined and the posterior mean is constant. | symbolic out:7–9 (S1.4–S1.6); numeric out:32 (N1.2: 0 of 2,000 sets beaten), out:33 (N1.3: 0 sign violations) |
| 5 | "Equivalently, keep iff E[Δ \| Δ̂] > 0" (T2:25) | **proven** (τ > 0) as an equivalence of rules. Optimality among all measurable rules is not claimed; it follows in one line: E[Δk(Δ̂)] = E[k(Δ̂)m(Δ̂)] ≤ E[m(Δ̂)⁺] = V(t\*). | symbolic out:5 (S1.2 at t = t\*); numeric out:39 (N1.9: three non-threshold rules lose 0.026, 0.020, 0.282) |
| 6 | default rule optimal iff μ₀ = 0 (T2:25) | **proven with an added assumption**: σ_d > 0. At σ_d = 0, t\* = 0 for every μ₀. | symbolic out:7 (S1.4); numeric out:34 (N1.4) |
| 7 | error rate Φ(−\|Δ\|/σ_d) (T2:25) | **proven with added assumptions**: σ_d > 0, Δ ≠ 0, and noise independent of Δ. At Δ = 0 it is 1/2 under a one-sided convention. | symbolic out:10 (S1.7); numeric out:38 (N1.8: 4 × 10⁶ draws, within about 1 s.e. at Δ = −0.5, 0, 0.2, 1.0) |
| 8 | "if σ_d = 0, every threshold in (−∞, 0] is optimal" | **false.** At σ_d = 0, V(t) = E[Δ1{Δ > t}] and V′(t) = −t f_Δ(t), so t = 0 is the unique optimum for every μ₀. Counterexample: μ₀ = 0, τ = 1 gives V(0) = φ(0) = 0.3989 > V(−1) = φ(1) = 0.2420. | symbolic out:11 (S1.8); numeric out:34 (N1.4: argmax t = 0.0000 for μ₀ ∈ {−2, −0.5, 0, 0.5, 2}; V(0) − V(−0.5) = 0.04688 at μ₀ = 0) |
| 9 | "so 'only if' needs σ_d > 0" | **proven**, by the correct reason (step 8) | as step 8 |

**Edge cases** (numeric): τ → 0 gives V(t\*) → μ₀⁺, the known-mean value (out:35, N1.5). σ_d → 0, equivalently ϱ → 1 in σ_d² = 2σ²(1 − ϱ), gives t\* → 0 and V(t\*) → E[Δ⁺] (out:36, N1.6). Extreme thresholds t\* ± 40s give V → μ₀ and V → 0 (out:37, N1.7).

### 1.3 Proposed wording changes (not applied)

1. T2:21, before "For the threshold rule ρ_t": insert "Assume Δ, e_t and e_s are mutually independent (so Δ̂ − Δ ∼ N(0, σ_d²) is independent of Δ) and τ > 0."
2. T2:25: "V is maximised at t\*" → "V is uniquely maximised over t ∈ ℝ at t\*".
3. T2:25: "The default rule (t = 0) is optimal if and only if μ₀ = 0." → "If σ_d > 0, the default rule (t = 0) is optimal if and only if μ₀ = 0."
4. T2:25: "Its single-decision error rate on a fixed increment Δ is Φ(−|Δ|/σ_d)." → "If σ_d > 0, its single-decision error rate on a fixed increment Δ ≠ 0 is Φ(−|Δ|/σ_d)."
5. T2:27, replace the parenthesis "(Edge case: if σ_d = 0, every threshold in (−∞, 0] is optimal, so "only if" needs σ_d > 0.)" with "(Edge cases: if σ_d = 0, then t\* = 0 and dV/dt = −t f_Δ(t), so t = 0 is the unique optimal threshold for every μ₀; hence "only if" needs σ_d > 0. If τ = 0, keep iff μ₀ > 0.)"
6. *(Optional.)* After "Equivalently, keep iff the posterior mean E[Δ | Δ̂] is positive." add "; this rule maximises E[Δ · keep] over all keep rules that depend on Δ̂ only, since E[Δ k(Δ̂)] = E[k(Δ̂) E[Δ | Δ̂]] ≤ E[E[Δ | Δ̂]⁺]."
7. *(Optional, scope.)* Add: "In a campaign, the comparison noise has mean zero and is independent of Δ only against an unselected record (T4 §2, scope)."
8. *(Optional, outside the statement.)* Reading, T2:31: "t\*/σ_d = −μ₀σ_d/τ² grows with σ_d" holds only when μ₀ < 0; add "when μ₀ < 0".

These agree with the audit and with the unadopted proposal `THEORY_CORRECTIONS_20261027.md` §"T2 Proposition 1".

**Readiness: ready after the proposed changes** (1–5; 6–8 optional).

---

## 2. T4 Proposition 6 (T4:32–44) and its scope paragraph (T4:46–48)

### 2.1 Signable statement (Proposition 6)

Fix n. Assume (A1)–(A2), read conditionally on (F_n, I_nᶜ) and on (F_n, Δ_n, I_nᶜ) respectively, on the event **D_nᶜ** (not a duplicate). Assume **τ_n > 0**. On I_n, Δ_n = 0; Δ̂_n may have any conditional law there (on a bit-exact node, Δ̂_n = 0). Write s_n² = τ_n² + σ_n², t\*_n = −μ_nσ_n²/τ_n² and m₁(h) = μ_n + (τ_n²/s_n²)(h − μ_n). Then, almost surely on {a_n = 1}:
- for every (F_n, Δ̂_n)-measurable k_n ∈ {0, 1}, E[Δ_n k_n | F_n] ≤ V\*_n := (1 − π_n) V(t\*_n; μ_n, τ_n, σ_n), with equality for k_n = 1{Δ̂_n > t\*_n};
- E[Δ_n | F_n, Δ̂_n] = P(I_nᶜ | F_n, Δ̂_n) · m₁(Δ̂_n). So every maximiser agrees with 1{Δ̂_n > t\*_n} where P(I_nᶜ | F_n, Δ̂_n) > 0 and Δ̂_n ≠ t\*_n. Where that probability is 0 (on a bit-exact node with π_n > 0, the event {Δ̂_n = 0}), every decision has value 0;
- if π_n = 1, V\*_n = 0 and every decision has value 0;
- if σ_n > 0 and π_n < 1, the default rule is a maximiser for proposal n iff μ_n = 0.

### 2.2 Steps (Proposition 6)

| Step | Claim (T4:42) | Verdict | Evidence |
|---|---|---|---|
| 1 | E[Δ_n k \| F_n] = E[k E[Δ_n \| F_n, Δ̂_n] \| F_n], so 1{posterior mean > 0} is a pointwise maximiser | **proven.** E\|Δ_n\| < ∞ holds under (A1). a_n is F_n-measurable (T4:27), so "conditioning on a_n = 1" means "on {a_n = 1}". | argument |
| 2 | P(Δ̂_n = 0, I_nᶜ \| F_n) = 0 | **proven** (s_n > 0, from τ_n > 0) | argument |
| 3 | {Δ̂_n = 0} coincides a.s. with I_n | **proven with an added assumption**: a bit-exact node (Δ̂_n = 0 on I_n). This is in T4 §1 but not in the statement. **Not needed**: see step 3′. | argument |
| 4 | on {Δ̂_n ≠ 0}, (Δ_n, Δ̂_n) is bivariate normal given F_n | **proven with the same added assumption.** Otherwise the law given {Δ̂_n ≠ 0} is a mixture. | argument |
| 3′ | (replacement for 3–4) E[Δ_n \| F_n, Δ̂_n] = E[Δ_n 1_{I_nᶜ} \| F_n, Δ̂_n] = P(I_nᶜ \| F_n, Δ̂_n) m₁(Δ̂_n). Hence V\*_n = E[1_{I_nᶜ} m₁(Δ̂_n)⁺ \| F_n] = (1 − π_n) E[Δ_n 1{Δ̂_n > t\*_n} \| F_n, I_nᶜ] = (1 − π_n)V(t\*_n) | **proven for any law of Δ̂_n on I_n.** This confirms P06 §4.2 (AI analysis, unreviewed there). | argument; numeric out:41–44 (N6.1: four parameter sets, bit-exact and non-bit-exact no-ops; the grid-best threshold equals t\*_n, and simulated values are within 1 s.e. of (1 − π)V(t\*)) |
| 5 | posterior mean > 0 iff Δ̂_n > t\*_n | **proven** (τ_n > 0) | symbolic out:7 (S1.4) |
| 6 | value on I_nᶜ is V(t\*_n) (T2 Prop. 1, conditionally on F_n), times 1 − π_n | **proven**, given §1. π_n < 1 is needed for the normal component to be defined; at π_n = 1 set V\*_n := 0. | §1; out:41–44 |
| 7 | Reading (T4:44): "ρ is optimal for proposal n iff μ_n = 0" | **proven with added assumptions**: σ_n > 0, π_n < 1, τ_n > 0. It is false at σ_n = 0, where t\*_n = 0 for every μ_n. | symbolic out:7; numeric out:44 (σ = 0, μ = +0.1: t\* = 0) |
| 8 | restriction to D_nᶜ (T4:24) | **needed.** On D_n the comparison is known before the run, so (A2) cannot hold. | argument |

### 2.3 The scope paragraph (T4:46–48)

**Signable content.** Under CRN, the comparison noise is η_n = ε_n − e. In Corollary 9a's kernel it is η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n.
- (S-a) Assume that, given F_n, e ∼ N(m_e, v), Δ_n ∼ N(μ_n, τ_n²) and ξ_n ∼ N(0, 1) are independent, with τ_n > 0, on I_nᶜ ∩ D_nᶜ. Then the Bayes rule keeps iff Δ̂_n > t\*\*_n = −(1 − ϱ_n)m_e − μ_n w_n²/τ_n², where w_n² = σ_{c,n}² + (1 − ϱ_n)² v.
- (S-b) With σ_{c,n}² = σ²(1 − ϱ_n²) and σ_n² = 2σ²(1 − ϱ_n):
  - t\*\*_n − t\*_n = −(1 − ϱ_n)m_e + μ_n(1 − ϱ_n)²(σ² − v)/τ_n²;
  - at an unselected record (m_e = 0, v = σ²), t\*\*_n = t\*_n;
  - if m_e ≥ 0, μ_n ≤ 0 and v ≤ σ², then t\*\*_n ≤ t\*_n, so the deployed rule keeps a subset of what the Bayes rule keeps;
  - if m_e < 0 and μ_n = 0, then t\*\*_n > t\*_n;
  - if μ_n > 0, the sign is not determined.
- (S-c) The shared-component analogue holds with v_rec in place of (1 − ϱ_n)e.
- (S-d) **New (AI analysis), replacing the last-but-two sentence of T4:48:** under the generative error models of §5, e | F_n is exactly Gaussian. Lemma K below states the conditions.

**Lemma K (AI analysis, new; kernel model).** Take the kernel as the generative model at every executed comparison j: ε_j = ϱ_j e_j + σ_{c,j}ξ_j, with σ_{c,j} = σ√(1 − ϱ_j²) > 0 and ξ_j ∼ N(0, 1) independent of F_j, of Δ_j and of all earlier latent variables. Assume:
- (K1) e_1 | F_1 ∼ N(m_1, v_1) with v_1 ≤ σ². For example, the initial record is unselected and F_1 carries no information about its error: m_1 = 0, v_1 = σ².
- (K2) For each executed non-no-op trial j, Δ_j | (F_j, e_j, earlier latent variables) ∼ N(μ_j, τ_j²), with (μ_j, τ_j) F_j-measurable. That is, the proposal depends on the latent errors only through F_j.
- (K3) F_{j+1} adds the recorded comparison Δ̂_j of an executed trial, as T4 §1 defines F_n ("its recorded metric"), the decisions, and a next proposal and control-plane randomness. The decisions are functions of (F_j, Δ̂_j) and of independent randomisation. The proposal and the randomness are conditionally independent of the latent variables given (F_j, Δ̂_j, k_j).
- (K4) Every executed no-op is identified (bit-exact node), and it leaves the record's error unchanged.

Then e_n | F_n ∼ N(m_n, v_n) and e_n ⊥ Δ_n | F_n for every n. The moments follow a Kalman recursion. A skip or an identified no-op leaves (m, v) unchanged. Otherwise, with h = Δ̂_n, M = μ_n − (1 − ϱ)m, S² = τ_n² + σ_c² + (1 − ϱ)²v and C = σ_c² − ϱ(1 − ϱ)v:
- keep: m ← ϱm + C(h − M)/S², v ← ϱ²v + σ_c² − C²/S²;
- discard: m ← m − (1 − ϱ)v(h − M)/S², v ← v − (1 − ϱ)²v²/S².

Moreover v_n ≤ σ² for every n. *Proof.* By induction on n:
1. Given F_n, (e_n, Δ_n, ξ_n) are independent Gaussians, by the induction hypothesis, (K2) and the kernel. So (e_n, ε_n, Δ̂_n) is jointly Gaussian given F_n, and conditioning on Δ̂_n gives the stated moments of e_n (discard) and of ε_n (keep).
2. By (K3), adding k_n, x_{n+1} and the randomness to the conditioning does not change the conditional law of the latent variables given (F_n, Δ̂_n). The keep event is σ(F_n, Δ̂_n)-measurable, so it truncates nothing.
3. e_{n+1} = ε_n on a keep and e_n otherwise. (K2) at n + 1 gives e_{n+1} ⊥ Δ_{n+1} | F_{n+1}.
4. Variance: σ² − v_keep = ϱ²(σ² − v) + C²/S² and v − v_disc = (1 − ϱ)²v²/S² (symbolic, out:100, XS1), so v ≤ σ² is preserved. ∎

The truncated-normal law of Proposition 9 and Corollary 9a is the law of ε_n given (F_n, e, Δ_n) and the keep. Those are not the control plane's information: the control plane sees Δ̂_n, not e or Δ_n. **Shared-component analogue:** take the state v_rec, the record's fresh component, with Δ̂ = Δ + v_new − v_rec. Under the same conditions (with v_1 ≤ (1 − ϱ)σ², and F_n informative about the errors only through the recorded comparisons), v_rec | F_n is Gaussian and Var(v_rec | F_n) ≤ (1 − ϱ)σ² (out:101, XS2). **Consequence:** in both models, under (K1)–(K4), t\*\*_n computed with these moments is the **exact** Bayes threshold given F_n. The variance condition of T4:48 then holds automatically, so the deployed rule is conservative exactly when E[e | F_n] ≥ 0 and μ_n ≤ 0. Where the control plane conditions on less than the ledger (for example only on the keep pattern), or where the increments or a no-op mixture on a non-bit-exact node are not Gaussian, t\*\*_n is only an approximation.

| Step | Claim (T4:46–48) | Verdict | Evidence |
|---|---|---|---|
| S1 | η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n in the kernel | **proven** (algebra) | argument |
| S2 | its conditional mean is (ϱ_n − 1)E[e \| F_n] | **proven** (ξ_n ⊥ (F_n, e, Δ_n)) | argument |
| S3 | the Bayes rule is still "keep iff E[Δ_n \| F_n, Δ̂_n] > 0" | **proven** (step 1 uses no noise law) | argument |
| S4 | t\*\*_n and w_n² (S-a) | **proven** under the stated Gaussian and independence hypotheses, with τ_n > 0 on I_nᶜ ∩ D_nᶜ | symbolic out:12 (S6.1) |
| S5 | at an unselected record, w_n² = 2σ²(1 − ϱ_n) = σ_n², so t\*\*_n = t\*_n | **proven** | symbolic out:13 (S6.2) |
| S6 | location shift −(1 − ϱ_n)E[e \| F_n]; the variance term lowers the threshold further when μ_n ≤ 0 and Var(e \| F_n) ≤ σ² (w_n ≤ σ_n); hence t\*\*_n ≤ t\*_n under the three conditions | **proven**, under S4's hypotheses | symbolic out:14 (S6.3), out:15 (S6.4); numeric out:45 (N6.2: 0 violations among 202,721 random sets meeting the conditions, ϱ up to 0.999); out:46–48 (dropping any one condition gives t\*\* > t\* in 59 %, 43 %, 41 % of sets) |
| S7 | E[e \| F_n] < 0 with μ_n = 0: the deployed rule keeps too many | **proven**: t\*\*_n = (1 − ϱ_n)\|m_e\| > 0 = t\*_n. The "Var = σ²" in that sentence is not needed when μ_n = 0, but it is harmless. | argument; out:46 |
| S8 | μ_n > 0: direction not determined | **proven** | out:48 |
| S9 | "a keep whose Δ̂_n fell below its prior mean can leave E[e \| F_n] < 0" | **proven**: in Lemma K's keep update, C > 0 when v ≤ σ² (out:100), so h < M gives m_keep < ϱm. | symbolic out:100 (XS1); numeric out:126 (XN2: E[e \| F] < 0 in 3.4 % of trial-6 histories at illustrative `digits_mlp`-like parameters under the deployed rule), out:127 (30.9 % in a ϱ = 0 near-null stress case) |
| S10 | "After a keep e is truncated, not Gaussian, so t\*\*_n is an approximation there, and the exact rule has no closed form." | **false** under the paragraph's own kernel used as the generative model (T3 `crn`, T5 `record`) and under the shared-component model, when F_n contains the recorded comparisons (T4 §1) and (K1)–(K4) hold. Counterexample: Lemma K. The record error given F_n is exactly Gaussian, and t\*\*_n with Kalman moments is the exact Bayes threshold, a closed form. The truncation the sentence has in mind is conditional on (e, Δ_n, keep), not on the ledger. The sentence is right only for coarser information or non-Gaussian components. | argument (Lemma K); symbolic out:100–101 (XS1–XS2); numeric out:104–123 (XN1: an independent implementation by explicit Gaussian conditioning; standardized residuals are consistent with N(0, 1) (mean, sd, skewness, kurtosis within sampling error) in narrow bins of (Δ̂_1, Δ̂_2) for all four keep patterns, in three models, although the raw record error is skewed, up to +0.225); out:124–128 (XN2: 96 conditional Hermite-moment tests per model, max \|t\| 2.24, 2.57 and 2.27, against 537.7, 642.1 and 898.7 for the naive standardization); out:50–76 (N6.4: under the t\*\* policy, the mean Δ_4 at the threshold is +0.0039e-3 (s.e. 0.0569e-3) for t\*\* against +0.3714e-3 (s.e. 0.0575e-3) for t\*, kernel; and t\*\* beats shifted thresholds and t\* at trial 4) |
| S11 | variance condition Var(e \| F_n) ≤ σ² | **proven to hold automatically** under (K1)–(K4) (new) | symbolic out:100; numeric out:126–128 (max Var(e \| F)/σ² over all trials 0.963 and 0.506; shared: Var(v_rec \| F)/((1 − ϱ)σ²) at most 0.795) |
| S12 | shared-component form t\*\*_n = −E[v_rec \| F_n] − μ_n w′_n²/τ_n², equality at an unselected record, direction under three conditions | **proven** | symbolic out:16 (S6.5); numeric out:49 (N6.3: 0 violations among 202,038 sets) |
| S13 | Size on `digits_mlp` (T5 §4.8: +0.47 δ_n feasible, +1.84 δ_n oracle; ranges 0.2–5.7 and 1.3–10.0 δ_n) | **not verified** (ENGINEERING_ONLY simulation on another branch; not part of the mathematics) | — |
| S14 | "the E1 input is not accepted by the author" | **stale status, not mathematics.** R1-E1-PILOT-ACCEPT (23 Nov) accepts the 22 Oct E1 runs; the sibling check on them stays an unreviewed proxy. | PLAN R1-E1-PILOT-ACCEPT |

### 2.4 Proposed wording changes (not applied)

1. T4:34: "Under (A1)–(A2), for each n and every F_n, among all (F_n, Δ̂_n)-measurable k_n the conditional value E[Δ_n k_n | F_n, a_n = 1] is maximised by" → "Under (A1)–(A2) on D_nᶜ, with τ_n > 0, for each n, almost surely on {a_n = 1}, among all (F_n, Δ̂_n)-measurable k_n the conditional value E[Δ_n k_n | F_n] is maximised by".
2. T4:40: after "V\*_n = (1 − π_n) · V(t\*_n; μ_n, τ_n, σ_n)" add "(V\*_n = 0 if π_n = 1)".
3. T4:42, proof: replace "On I_nᶜ, Δ̂_n has a continuous conditional law, … where Δ_n = 0 and every k has value 0. On {Δ̂_n ≠ 0}, conditionally on F_n, (Δ_n, Δ̂_n) is bivariate normal …" with: "Since Δ_n = 0 on I_n, E[Δ_n | F_n, Δ̂_n] = P(I_nᶜ | F_n, Δ̂_n) · m₁(Δ̂_n), where m₁(h) = μ_n + (τ_n²/s_n²)(h − μ_n) is the posterior mean under the bivariate normal law of (Δ_n, Δ̂_n) given (F_n, I_nᶜ). It is positive iff Δ̂_n > t\*_n wherever P(I_nᶜ | F_n, Δ̂_n) > 0, and 0 elsewhere (on a bit-exact node with π_n > 0: on {Δ̂_n = 0}, the no-op event). This holds for any law of Δ̂_n on I_n." *Minimal alternative:* add "on a bit-exact node (§1)" to the statement.
4. T4:44 (Reading): "The default rule ρ (t = 0) is optimal for proposal n iff μ_n = 0." → "If σ_n > 0 and π_n < 1, the default rule ρ (t = 0) is optimal for proposal n iff μ_n = 0."
5. T4:48: "So when E[e | F_n] ≥ 0, μ_n ≤ 0 and Var(e | F_n) ≤ σ², t\*\*_n ≤ t\*_n" → "So, under that Gaussian hypothesis, when E[e | F_n] ≥ 0, μ_n ≤ 0 and Var(e | F_n) ≤ σ², t\*\*_n ≤ t\*_n".
6. T4:48: replace "After a keep e is truncated, not Gaussian, so t\*\*_n is an approximation there, and the exact rule has no closed form." with: "If the kernel is the generative model at every comparison, F_n contains every recorded comparison, Δ_n depends on the latent errors only through F_n, the initial record's error is Gaussian given F_1 and executed no-ops are identified, then e | F_n is exactly Gaussian, with moments from a Kalman recursion over the recorded comparisons. A keep is a function of a recorded value, so conditioning on it truncates nothing; the truncated law of Proposition 9 is the law given the keep and (e, Δ_n), not given the ledger. Then t\*\*_n is the exact Bayes threshold, and Var(e | F_n) ≤ σ² holds at every trial. The same holds for v_rec under the shared-component model, with Var(v_rec | F_n) ≤ (1 − ϱ_n)σ². Where the control plane conditions on less, or the increments or a no-op mixture are not Gaussian, t\*\*_n is an approximation. (AI analysis: `author_packets_20261122/AI_PROOF_CHECK_20261123.md` §2.3.)" Keep the following sentence on P06 §4.1.
7. *(Status.)* T4:48: "the E1 input is not accepted by the author" → "the E1 runs were accepted on 23 Nov (R1-E1-PILOT-ACCEPT), but the sibling check on them is an unreviewed proxy".
8. *(Optional, Reading.)* T4:44, "What a learned model must supply is exactly (π_n, μ_n, τ_n)": this holds under (A2) with σ_n known. Under CRN with a selected incumbent, the control plane must also supply E[e | F_n] and Var(e | F_n). By Lemma K these follow from the ledger and the model's (ϱ, σ) (P06 §4.3).

**Readiness: ready after the proposed changes** (1–6; 7 is a status update; 8 is optional).

---

## 3. T4 Proposition 7 and Corollary 7a (T4:50–64)

### 3.1 Signable statement (Proposition 7)

Fix n. Assume the hypotheses of §2.1 with **π_n < 1**. Let t̃ be a **real-valued** F_n-measurable threshold, f_n the N(μ_n, s_n²) density, and gap_n := V\*_n − (1 − π_n)V(t̃; μ_n, τ_n, σ_n). This is the value of 1{Δ̂_n > t\*_n} minus that of 1{Δ̂_n > t̃}, given F_n; the no-op part contributes 0 to both, whatever Δ̂_n is on I_n. Then, almost surely:
- gap_n = (1 − π_n)(τ_n²/s_n²) ∫_{t̃}^{t\*_n} f_n(u)(t\*_n − u) du ≥ 0. This is an oriented integral, non-negative for either order of t̃ and t\*_n, and positive iff t̃ ≠ t\*_n.
- With I the closed interval between t̃ and t\*_n: (1 − π_n)(τ_n²/(2s_n²)) · min_I f_n · (t\*_n − t̃)² ≤ gap_n ≤ (1 − π_n)τ_n²(t\*_n − t̃)²/(2√(2π) s_n³). Here min_I f_n = min(f_n(t̃), f_n(t\*_n)).
- gap_n = (1 − π_n)τ_n² f_n(t\*_n)(t\*_n − t̃)²/(2s_n²) · [1 + (2/3)(t\*_n − μ_n)(t\*_n − t̃)/s_n² + O((t\*_n − t̃)²(1 + (t\*_n − μ_n)²/s_n²)/s_n²)].

### 3.2 Steps (Proposition 7)

| Step | Claim (T4:62) | Verdict | Evidence |
|---|---|---|---|
| 1 | dV/dt = −f_n(t)(τ_n²/s_n²)(t − t\*_n) | **proven**, from §1 (V's formula) | symbolic out:8 (S1.5) |
| 2 | V(t\*_n) − V(t̃) = (τ_n²/s_n²)∫_{t̃}^{t\*_n} f_n(u)(t\*_n − u)du | **proven** (fundamental theorem of calculus; closed-form antiderivative) | symbolic out:18 (S7.1), out:19 (S7.1b); numeric out:78 (N7.1: 2,201 sets, t̃ up to ±15 s from t\*, max abs diff 2.7e-15); out:130 (XN3: 306 extreme cases, τ down to 1e-3, σ down to 1e-4, 50 digits, max rel diff 4.4e-18) |
| 3 | the oriented integral is ≥ 0; the absolute value in T4:54 is redundant | **proven**: the integrand has the sign of t\*_n − u, which is the orientation | argument; out:130 (gap < 0 in 0 cases) |
| 4 | factor 1 − π_n | **proven**: on I_n, Δ_n = 0, so both rules have value 0 there (no bit-exactness needed) | argument |
| 5 | bounds, via min_I f_n ≤ f_n ≤ 1/(s_n√(2π)) and ∫_I \|t\* − u\|du = (t\* − t̃)²/2 | **proven**, with [t̃, t\*_n] read as the interval between the two points (audit) | symbolic out:20 (S7.2); numeric out:78 (0 failures of either bound; the minimum of f on the interval is at an endpoint in every set), out:130 (0 failures; min gap/lower 1.0, max gap/upper 0.99999992) |
| 6 | "Near t\*_n, gap ≈ …", via "the first-order Taylor expansion of f_n at t\*_n" | **proven as a leading-order term; the wording is imprecise.** The approximation replaces f_n by f_n(t\*_n), its zeroth-order Taylor polynomial. Equivalently it is the second-order Taylor expansion of V at t\*_n, since V″(t\*_n) = −f_n(t\*_n)τ_n²/s_n². The relative error is (2/3)(t\*_n − μ_n)(t\*_n − t̃)/s_n² + …. | symbolic out:9 (S1.6), out:21 (S7.3), out:102 (XS3); numeric out:79 (N7.2: the ratio is 1.000710 at t̃ − t\* = +0.001s; the formula gives 1/(1 − 0.000709)) |
| 7 | assumptions τ_n > 0 (t\*_n finite), s_n > 0, finite t̃ | **proven with added assumptions** (not in T4:52; audit) | — |

### 3.3 Signable statement (Corollary 7a)

Assume **(NF)** of the revised Proposition 10(a′) (`T4_PROP10_REVISION_20261028.md` §3): the law of the exogenous sequence is the same under every policy, and the control plane's randomness U is independent of it. Compare two policies with the **same execution rule** a_n = A_n(x_{1:n}, (a_j, a_jΔ̂_j)_{j<n}, U), one that **does not read past keep decisions**. The first keeps by a_n 1{Δ̂_n > t\*_n}, the second by a_n 1{Δ̂_n > t̃_n}, where t̃_n is real-valued and measurable with respect to C_n := σ(x_{1:n}, (a_j, a_jΔ̂_j)_{j<n}, U). Under both policies O_n = C_n. Assume (A1)–(A2) relative to C_n, with τ_n > 0, on D_nᶜ, at every n. Then J_g(t\*) − J_g(t̃) = E[Σ_n a_n gap_n], with the expectation under the common law. It is zero iff t̃_n = t\*_n almost surely on {a_n = 1, π_n < 1} for every n.

| Step | Claim (T4:64) | Verdict | Evidence |
|---|---|---|---|
| 1 | "Under the decision-independence condition of Proposition 10" | **gap as cited**: the 18 Oct DI has the audit's gap (T_AUDIT, Proposition 10). **Proven with added assumptions**: (NF), plus an execution rule that does not read past keeps (revision R3). Under these, both policies can be coupled on the same exogenous sequence and the same U, so a_n and C_n coincide. | argument; numeric out:80–81 (N7.3: (NF) holds, (NI) fails through a shared latent θ, and the execution rule reads a past result: differences +0.00026 (s.e. 0.00026) and +0.00014 (s.e. 0.00032) between the simulated gain and E[Σ a_n gap_n], for two rules t̃) |
| 2 | per-trial difference a_n gap_n | **proven**: E[Δ_n(k_n − k̃_n) \| C_n] = a_n gap_n by §3.1 relative to C_n | argument |
| 3 | summation | **proven**, under the common law | argument |
| 4 | "zero iff t̃_n = t\*_n on the executed trials" | **proven** when read as "a.s. on {a_n = 1, π_n < 1}" (gap_n > 0 iff t̃_n ≠ t\*_n there) | argument |
| 5 | scope | under R1 (ii) (shared incumbent error), (NF) fails for the actual loop (revision B2), so 7a does not apply to it. Campaign gains are reported as measured (R3). | revision §5 R1, R3 |

### 3.4 Proposed wording changes (not applied)

1. T4:52: "Fix n and F_n with π_n < 1, and let t̃ be any F_n-measurable threshold" → "Fix n. Under (A1)–(A2) on D_nᶜ with τ_n > 0 and π_n < 1, let t̃ be any real-valued F_n-measurable threshold".
2. T4:54: after the display, add "Call the left side gap_n." *(Optional:* drop the absolute value and say "the oriented integral is non-negative for either order".)
3. T4:58: "min_{u ∈ [t̃, t\*_n]} f_n(u)" → "the minimum of f_n over the interval between t̃ and t\*_n (that is, min(f_n(t̃), f_n(t\*_n)))".
4. T4:62: "The approximation is the first-order Taylor expansion of f_n at t\*_n." → "The approximation replaces f_n by f_n(t\*_n) (equivalently, it is the second-order Taylor expansion of V at t\*_n); its relative error is (2/3)(t\*_n − μ_n)(t\*_n − t̃)/s_n² + O((t\*_n − t̃)²/s_n²)."
5. T4:64: "Under the decision-independence condition of Proposition 10, the gain of the per-proposal threshold over any threshold rule t̃_n, at the same execution decisions, is E[Σ_n a_n · gap_n]. It is zero iff t̃_n = t\*_n on the executed trials." → "Under (NF) of the revised Proposition 10(a′), if both rules use the same execution rule, which does not read past keep decisions, and (A1)–(A2) hold relative to the common information C_n = σ(x_{1:n}, (a_j, a_jΔ̂_j)_{j<n}, U), the gain of the per-proposal threshold over any C_n-measurable threshold rule t̃_n is E[Σ_n a_n · gap_n] under the common law. It is zero iff t̃_n = t\*_n almost surely on {a_n = 1, π_n < 1} for every n. Under the shared incumbent error of R1 (ii), (NF) fails for the actual loop, and the corollary does not apply to it (revision R3)."
6. *(Reading, T4:66; not part of the statement.)* "gives an estimate of how much any better predictor could still add" → "gives an estimate (not a bound: the proposition bounds the gap in terms of the true (μ_n, τ_n)) of how much …" (audit; P07 §4.2).

**Readiness: ready after the proposed changes** (1, 3, 4 for Proposition 7 and 5 for Corollary 7a; 2 and 6 are optional).

---

## 4. T4 Proposition 9, restated (T4:87–108), and Corollary 9a (T4:110–125)

### 4.1 Signable statement

These are the T4 statements, with every hypothesis explicit. On I_nᶜ, Δ̂_n = Δ_n + ε_n − e. The keep event is K = {Δ̂_n > 0}, and e′ = ε_n on K. No assumption is made on the joint law of (F_n, e, ε_n, Δ_n) or on the proposer. For a σ-field G, p_G = P(K | G) and E[X | K, G] = E[X 1_K | G]/p_G on {p_G > 0}.
- (i) On K, e′ > e − Δ_n. On K ∩ {Δ_n = 0}, e′ > e.
- (ii) Let e and Δ_n be G-measurable and E|ε_n| < ∞. Then, a.s.:
  - (ii.1) on {p_G > 0}, E[e′ | K, G] > e − Δ_n;
  - (ii.2) on {0 < p_G < 1}, E[e′ | K, G] > E[ε_n | G].
- (iii) With G as in (ii), on {E[ε_n | G] = 0} ∩ {0 < p_G < 1}, E[e′ | K, G] > 0.
- (iv) For any σ-field G′, if E|e|, E|Δ_n| and E|ε_n| are finite, then E[e′ | K, G′] > E[e − Δ_n | K, G′] on {P(K | G′) > 0}.
- *Threshold rules:* (i), (ii.1) hold with e − Δ_n + t for a G-measurable t, and (ii.2) holds unchanged.
- **Corollary 9a.** Assume ε_n = ϱ_n e + σ_{c,n}ξ_n, where ξ_n ∼ N(0, 1) is independent of (F_n, e, Δ_n), and ϱ_n ∈ [0, 1) and σ_{c,n} > 0 are F_n-measurable. Then E[e′ | K, F_n, e, Δ_n] = ϱ_n e + σ_{c,n}λ(a_n), with a_n = ((1 − ϱ_n)e − Δ_n)/σ_{c,n}. This exceeds max(e − Δ_n, ϱ_n e). In particular (a) for Δ_n = 0 it exceeds e for every e, and (b) for e = 0 it equals σ_{c,n}λ(−Δ_n/σ_{c,n}) > 0, which is decreasing in Δ_n/σ_{c,n}. No moment of e is needed.

### 4.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| (i) | K = {ε_n > e − Δ_n}, and e′ = ε_n on K | **proven** (identity) | argument |
| (ii.1) | Y = (ε_n − c)1_K ≥ 0 with Y > 0 on K. E[Y \| G] = E[ε_n1_K \| G] − c p_G is finite. For A = {p_G > 0, E[Y \| G] = 0} ∈ G: E[Y1_A] = 0 ⇒ P(K ∩ A) = 0 ⇒ E[p_G1_A] = 0 ⇒ P(A) = 0 | **proven.** Taking out c needs only c G-measurable: localise on {\|c\| ≤ k} ∈ G. | argument; numeric out:84 (N9.1: 430 cells, six non-Gaussian laws of ε \| G, one of them discrete, exact quadrature or sums, thresholds of both signs: 0 violations, min margin 5.0e-2) |
| (ii.2) | E[ε_n1_{Kᶜ} \| G] ≤ c(1 − p_G); the mixture identity gives (1 − p_G)(E[ε \| K, G] − E[ε \| Kᶜ, G]) > 0 | **proven.** p_G < 1 is necessary for strictness. | argument; numeric out:85 (383 cells, 0 violations), out:87 (N9.2: equality at p_G = 1) |
| (iii) | substitute E[ε_n \| G] = 0 in (ii.2); e is not used | **proven** | argument; numeric out:86 (335 cells, 0 violations), out:93 (review M2: without the zero-mean hypothesis the conclusion fails; E[e′ \| keep] = −0.2289 at P(keep) = 0.9995) |
| (iv) | Z = (ε_n − e + Δ_n)1_K is integrable, ≥ 0, and > 0 on K; the argument of (ii.1) with G′ applies | **proven.** "\| K" on the right is necessary. | argument; numeric out:88 (N9.3: heavy-tailed skewed errors, a proposer that reads B, G′ = deciles of B: min t-statistic 350), out:89 (the review's example: E[e′ \| K] = 0.7979 < E[e] = 5) |
| threshold remark | c = e − Δ_n + t | **proven** | numeric out:84 (thresholds t ∈ {0, −0.5, 0.4}) |
| 9a formula | given G_n = σ(F_n, e, Δ_n), ε_n ∼ N(ϱ_n e, σ_{c,n}²) and 0 < p < 1; truncated-normal mean m + σ_cλ((c − m)/σ_c) with (c − m)/σ_c = a_n | **proven** | symbolic out:22 (S9.1), out:25 (S9.4); numeric out:90 (N9.4: 100 sets with ϱ up to 0.999 and P(keep) from about 1e-72 to about 1, against 40-digit quadrature: max rel diff 7.1e-11), out:91 (simulation, 4 sets) |
| 9a inequality | λ(a) > max(0, a) for all a, since ψ(a) = φ(a) − aΦ(−a) > 0 (ψ′ = −Φ(−a), ψ(∞) = 0) | **proven**; no moment of e needed | symbolic out:23 (S9.2); numeric out:90 (0 margins ≤ 0; the smallest margin, 10^−980.4, is still positive in 40-digit arithmetic) |
| 9a (a), (b) | substitution; λ increasing (λ′ = λ(λ − a) > 0) | **proven** | symbolic out:24 (S9.3) |
| scope bullets | exact for ϱ = 0 with fresh draws; exact at an unselected record carrying no further information; the shared-component partial covariance ϱ(1 − ϱ)σ² | **proven** | symbolic out:26 (S9.5) |
| scope numbers | "−0.231 at e = 0 and +0.306 at e = 0.9" (Monte Carlo, P09 §4) | **consistent**: semi-analytic −0.2303 and +0.3059, within the Monte Carlo s.e. 0.001–0.002 | numeric out:92 (N9.5) |
| scope numbers | 4,864,272 keeps; +0.513 (s.e. 0.004), −0.001, −0.514, +0.691 | **match** `check_output.txt` (last lines) | file |

Edge cases: ϱ → 1 (σ_c → 0; a_n → ±∞; out:90); Δ_n = 0 and e of both signs (out:84–86, out:90–91); p_G → 0 and p_G → 1 (out:87, out:90).

### 4.3 Proposed wording changes

None required. Optional, not affecting readiness:
1. (iii), T4:98: "if the candidate's error has conditional mean zero, E[ε_n | G] = 0, then …" may be read on the event {E[ε_n | G] = 0}; the proof gives the conclusion there.
2. *(Status, scope of the corollary, T4:125.)* "(…; AI analysis, unreviewed, of data the author has not yet accepted)" → the E1 runs were accepted on 23 Nov (R1-E1-PILOT-ACCEPT); the sibling check on them stays an unreviewed proxy.

**Readiness: ready as written** (Proposition 9 (i)–(iv), the threshold remark and Corollary 9a).

---

## 5. T4 Proposition 10(b) (T4:137)

### 5.1 Signable statement

For every M > 0 there is a two-trial loop with N = 2, g = 0, noiseless comparisons and no no-ops, in which the myopic policy earns at least M less than the optimal policy. The myopic policy executes iff V\*_n ≥ g and keeps iff the posterior mean of the increment is positive.

*Example.* Trial 1 has a known increment Δ₁ = −α, α > 0 (τ₁ = 0). If trial 1 is kept, Δ₂ ∼ N(β, τ²); otherwise Δ₂ ∼ N(0, τ²), with τ > 0 and β ≥ 0.
- The myopic policy discards trial 1 and earns τφ(0).
- Keeping trial 1 and then keeping iff Δ₂ > 0 earns −α + βΦ(β/τ) + τφ(β/τ).
- The myopic loss is (G(β, τ) − α)⁺, where G(β, τ) = βΦ(β/τ) + τφ(β/τ) − τφ(0) and G(2, 1) = 2Φ(2) + φ(2) − φ(0) = 1.6095484222….
- G is increasing in β, and G(β, τ) ≥ β − τφ(0). So for fixed α and τ the loss tends to ∞ as β → ∞.

The law of Δ₂ depends on the keep decision of trial 1, so (NF), and T4's DI, fail. *Extension (AI analysis):* the conclusion holds for any noise σ₂ ≥ 0 at trial 2, with G replaced by G_σ = V(t\*; β, τ, σ₂) − V(0; 0, τ, σ₂) ≥ β − τ²φ(0)/√(τ² + σ₂²).

### 5.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | myopic acceptance discards trial 1 | **proven.** τ₁ = 0, so this is the known-mean case (revision 8′.4), not Proposition 6's threshold, which needs τ_n > 0. At g = 0 execute and skip tie; both give k₁ = 0. | argument |
| 2 | discard branch earns E[max(Δ₂, 0)] = τφ(0) | **proven** (σ = 0: keep iff Δ₂ > 0) | symbolic out:27 (S10.1 at β = 0) |
| 3 | keep branch earns −α + βΦ(β/τ) + τφ(β/τ) | **proven** | symbolic out:27 (S10.1) |
| 4 | the difference at τ = 1, β = 2 is "1.61 − α" | **proven**: G(2, 1) = 1.6095484222153969596 | symbolic out:29 (S10.3); numeric out:95 (N10.1), out:96 (N10.2: simulation 1.60941, s.e. 0.00028) |
| 5 | "for α < 1.61 the myopic rule loses 1.61 − α" | **false by rounding**: the loss is (G(2, 1) − α)⁺. For α ∈ [1.60955, 1.61) it is 0, not 1.61 − α. For 0 < α < G(2, 1) it is G(2, 1) − α. | argument; numeric out:97 (N10.3) |
| 6 | the loss grows without bound in β | **proven**: dG/dβ = Φ(β/τ) > 0, G(0) = 0, G ≥ β − τφ(0) | symbolic out:28 (S10.2); numeric out:97 (G = 99.60106 at β = 100) |
| 7 | "σ → 0" | the formulas are the σ = 0 values. **Proven** for every σ₂ ≥ 0 with G_σ (new) | symbolic out:103 (XS4); numeric out:98 (N10.4: G_σ = 1.64712 at β = 2, σ = 0.5; simulation 1.64781, s.e. about 0.0007) |
| 8 | DI fails | **proven** (the law of Δ₂ depends on k₁) | argument |

### 5.3 Proposed wording changes (not applied)

1. T4:137: "With τ = 1 and β = 2 the difference is 1.61 − α, so for α < 1.61 the myopic rule loses 1.61 − α" → "With τ = 1 and β = 2 the difference is G(2, 1) − α, where G(2, 1) = 2Φ(2) + φ(2) − φ(0) ≈ 1.6095, so for 0 < α < G(2, 1) the myopic rule loses G(2, 1) − α".
2. *(Optional.)* "Example (σ → 0, g = 0, N = 2)" → "Example (σ = 0, g = 0, N = 2; with noise σ > 0 at trial 2 the loss is at least β − τ²φ(0)/√(τ² + σ²) − α, so the conclusion holds for every σ ≥ 0)".
3. *(Optional.)* "Myopic acceptance discards trial 1" → "Myopic acceptance (keep iff the posterior mean is positive; Δ₁ is known) discards trial 1".
4. *(Optional, heading.)* "failure without DI" → "failure of (NF)" (revision §4). The revision's remark R5 replaces the "Reading" claims T4:141 ("the precise scope of RL"); that reading is not part of the statement.

**Readiness: ready after the proposed changes** (1; 2–4 optional).

---

## 6. New relative to the packets, the audit and the review

1. **T4:48 is false where it says the exact rule has no closed form** (§2.3, S10, Lemma K). Under the kernel used as the generative model, and under the shared-component model, the record error given the ledger is exactly Gaussian, by a Kalman recursion over the recorded comparisons. t\*\*_n with those moments is the exact Bayes threshold, and the variance condition holds automatically. P06 §4.1 item 3 ("after a keep, e is selected (truncated), so it is not Gaussian") and the analysis note under revision R1 ("for it to hold exactly, the posterior of e given O_n must also be Gaussian") are affected in the same way: that condition is met in these models. The review did not raise it. Consequences:
   - the deployed rule's conservativeness (R1-THEORY-RHO (2)) holds exactly in these models whenever E[e | F_n] ≥ 0 and μ_n ≤ 0;
   - E[e | F_n] < 0 does occur: 3.4 % of trial-6 histories at illustrative `digits_mlp`-like parameters (out:126);
   - within the model, a feasible corrected rule exists in closed form. It needs ϱ, σ and the past (μ_j, τ_j), and it conditions on the whole recorded history, not only on the keep count. This bears on the seventh-arm question of R1-D3-CHOICES (1), but changes no row.
   This is AI analysis, unreviewed.
2. **Proposition 7's local form**: an explicit relative error (2/3)(t\*_n − μ_n)(t\*_n − t̃)/s_n² (XS3, out:102; it matches N7.2 to six digits).
3. **Proposition 10(b)**: the rounding error "α < 1.61" (§5, step 5). The revision text already uses 1.60955. The example also holds for σ > 0 at trial 2 (XS4, N10.4), whereas the audit called it a "σ = 0 limiting case".
4. **Status**: T4:48 and T4:125 still say the E1 data are not accepted, which R1-E1-PILOT-ACCEPT (23 Nov) has overtaken.
5. *(Minor, not in the theory text.)* P09 §4's Monte Carlo value at e = −0.9 (−0.778) lies about 0.006 from the semi-analytic −0.7836 (out:92), more than its quoted s.e. This is probably the averaging over a bin of e. T4 does not cite that value.

Confirmed rather than new: P06 §4.2 (bit-exactness is not needed for Proposition 6); revision R3 (Corollary 7a under (NF) with an execution rule that does not read past keeps); the audit's T2 counterexample; review M1, M2, m2 and N1 as applied in the text.

## 7. What was not verified

- The T5 sizes in T4:48 (+0.47 δ_n, +1.84 δ_n and the ranges) and the E1 partial correlation in T4:125 (+0.37, interval +0.24 to +0.51): empirical or ENGINEERING_ONLY figures, not re-run.
- Whether the kernel or the shared-component model, (K2) in particular, describes the real nodes and an LLM proposer: an empirical question (R1-SCREEN-MEASURE).
- The manuscript (`papers/r1/sections/theory.tex`, `appendix.tex`) was not compared with these signable forms.
- Inequalities are proven by argument. SymPy checks the identities they rest on; it does not prove the inequalities themselves.
- One fact about this run: a first version of XN1 (2 × 10⁷ campaigns, bins of half-width 0.06 s) gave two skewness values at 2.5 and 2.7 s.e. in the ϱ = 0 model. A 4 × 10⁶-row check by keep pattern then gave |skew| ≤ 0.002 (s.e. ≤ 0.002). The committed version uses 4 × 10⁷ campaigns, bins of half-width 0.1 s and lines by keep pattern (out:104–123). The per-sample standardization makes the bin width irrelevant to validity.

## 8. Files

- `ai_proof_check_20261123.py`: script; `python3 ai_proof_check_20261123.py > ai_proof_check_20261123_output.txt` (SymPy 1.14.0, NumPy 2.5.3, SciPy 1.18.1, mpmath 1.3.0; run time on stderr).
- `ai_proof_check_20261123_output.txt`: output, 130 lines.
- `AI_PROOF_CHECK_CHECKLIST_20261123.md`: points for the coordinating chat's spot check (check (b)).
