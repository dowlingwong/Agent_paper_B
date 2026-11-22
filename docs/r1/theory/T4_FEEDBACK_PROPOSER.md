# T4 — Acceptance under noise with a ledger-dependent proposer

> **Historical protocol context.** This theory uses a generic run price g; the later 22 Oct PLAN §10 row fixes g for the C3 gate and states the accounting convention. The forecast-GRPO and prior-only training discussion is historical relative to R1-C3-POST's separated belief/action design. The propositions and assumptions below are unchanged and remain subject to audit and author checking.

*Theory track, extension of T2. Drafted 18 Oct 2026 by an AI agent (Claude, coordinating session) at the author's request. AI-assisted; the author has not checked these proofs yet and no human has reviewed them (PLAN §9 item 6). The two closed forms that carry the C3 design (the gain identity of Proposition 7 and the truncated-mean formula now stated as Corollary 9a; reference updated 22 Nov 2026 (R1-THEORY-RHO), AI-assisted, not author-checked) were checked against Monte Carlo on 18 Oct 2026 (2–4 × 10⁶ draws; agreement to MC error); the check script is not yet committed as a test.*

Notation follows T1 and T2: Φ, φ are the standard normal cdf and pdf; ψ(z) = φ(z) − zΦ(−z); λ(a) = φ(a)/Φ(−a) is the inverse Mills ratio. V(t; μ, τ, σ) = μΦ(−z) + (τ²/s)φ(z) with s² = τ² + σ², z = (t − μ)/s, is the T2 Proposition 1 value of a threshold t.

## 0. Why this note exists

T2 treats one decision with a proposal law N(μ₀, τ²) that is the same for every trial, and §8 there says that no result covers a proposer whose law depends on the ledger. That is the main thing that separates the governed loop from classical ranking & selection: the LLM manager reads the ledger (memory mode, D24), so the distribution of the next proposal depends on what was kept, discarded and displayed. This note:

1. shows that T2's Bayes rule survives a ledger-dependent proposer **trial by trial**, but with a **per-proposal** prior (Proposition 6). This is the formal basis of C3;
2. gives the exact value of using a per-proposal prior instead of a constant one, and a bound that can be estimated before any model is trained (Proposition 7). This is the theory part of C3 ("route B");
3. derives the pre-execution screening rule (skip) under a run price (Proposition 8);
4. shows that the winner's curse of `current_best` holds for **every** adaptive proposer, generalising T2 Proposition 4 (Proposition 9);
5. states exactly when trial-by-trial (myopic) acceptance is globally optimal, and shows by example that it can fail by an arbitrary amount when the proposer's law depends on the keep decision (Proposition 10).

## 1. Setting

Trials n = 1, 2, … . Before trial n the control plane has the history F_n: every earlier proposal, its decision, its recorded metric, the displayed memory, the remaining budgets, and the current proposal x_n (the structured edit plus the manager's text). F_n is a filtration.

- **No-op event** (revised 19 Oct 2026). I_n is the event that x_n leaves the incumbent's effective (active-key) configuration unchanged, e.g. an edit of a key the node does not use. Then Δ_n = 0, and on a node that is bit-exact at fixed seeds (all CPU nodes, STATUS 12 Oct) **Δ̂_n = 0 exactly**.
- **Duplicate event** (added 19 Oct 2026). D_n is the event that x_n's effective configuration equals that of an earlier evaluated configuration *other than the incumbent*. Its campaign metric is already in the ledger, so on a bit-exact node Δ̂_n is known before the run; **Δ_n is generally not 0**. The 18 Oct draft folded D_n into I_n; that was wrong (C3 offline pilot: 727 of 841 rule-detectable proposals were duplicates, and 520 had Δ̂ ≠ 0). Propositions 6–8 apply on D_nᶜ. D_n is handled by Corollary 8a.
- **(A1) Proposal law.** Conditional on F_n: P(I_n | F_n) = π_n, and on I_nᶜ the true increment Δ_n = J(c_n) − J(inc_n) is N(μ_n, τ_n²). The triple (π_n, μ_n, τ_n) is F_n-measurable and may depend on the history in any way. On I_n, Δ_n = 0.
- **(A2) Comparison noise.** On I_nᶜ, Δ̂_n = Δ_n + η_n with η_n | (F_n, Δ_n) ∼ N(0, σ_n²), σ_n F_n-measurable (it may depend on the kind of edit: local vs structural, E1 §5).
- **Actions.** At E1 the control plane chooses a_n ∈ {0, 1} (execute or skip) using F_n. If a_n = 1, a run is spent, Δ̂_n is observed and at E2 it chooses k_n ∈ {0, 1} (keep or discard) using (F_n, Δ̂_n). If a_n = 0, k_n = 0. Skip costs no run; the next proposal costs an LLM call.
- **Objective (Lagrangian form).** For a run price g ≥ 0, J_g(π) = E[Σ_{n ≤ N} (Δ_n k_n − g a_n)], where N is the number of proposals allowed (the LLM-call cap). Under the additive model (T2 §1) the final true improvement is Σ Δ_n k_n.

The Lagrangian form is the relaxation of the hard run budget E[Σ a_n] ≤ W. By weak duality the hard-budget optimum is at most min_g {sup_π J_g(π) + gW}. We do not claim the price policy is optimal under the hard budget. g is tuned on development instances, as in T2 §6, and its sensitivity is reported.

## 2. Proposition 6 — the per-proposal Bayes rule

**Statement.** Under (A1)–(A2), for each n and every F_n, among all (F_n, Δ̂_n)-measurable k_n the conditional value E[Δ_n k_n | F_n, a_n = 1] is maximised by

  k_n = 1{Δ̂_n > t*_n}, with t*_n = −μ_n σ_n² / τ_n²,

on the event {Δ̂_n ≠ 0}. On {Δ̂_n = 0} every decision has value 0. The maximal value is

  V*_n = (1 − π_n) · V(t*_n; μ_n, τ_n, σ_n).

**Proof.** For any (F_n, Δ̂_n)-measurable k, E[Δ_n k | F_n] = E[k · E[Δ_n | F_n, Δ̂_n] | F_n], so k = 1{E[Δ_n | F_n, Δ̂_n] > 0} is a pointwise maximiser. On I_nᶜ, Δ̂_n has a continuous conditional law, so P(Δ̂_n = 0, I_nᶜ | F_n) = 0. The event {Δ̂_n = 0} coincides a.s. with I_n, where Δ_n = 0 and every k has value 0. On {Δ̂_n ≠ 0}, conditionally on F_n, (Δ_n, Δ̂_n) is bivariate normal with means (μ_n, μ_n), Var Δ̂_n = s_n² = τ_n² + σ_n² and covariance τ_n². So E[Δ_n | F_n, Δ̂_n] = μ_n + (τ_n²/s_n²)(Δ̂_n − μ_n), which is positive iff Δ̂_n > t*_n. The value on I_nᶜ is V(t*_n; μ_n, τ_n, σ_n) by T2 Proposition 1, applied conditionally on F_n; multiply by P(I_nᶜ | F_n) = 1 − π_n. ∎

**Reading.** T2's index policy uses one prior (μ₀, τ₀) per node. Proposition 6 says the right threshold is **per proposal**: an edit the history marks as usually harmful (μ_n ≪ 0) needs a high bar, a promising one a low bar. The default rule ρ (t = 0) is optimal for proposal n iff μ_n = 0. Nothing in the proof needs the proposer to be stationary or independent of the ledger. **What a learned model must supply is exactly (π_n, μ_n, τ_n), not an action.** This is C3.

**Scope (common random numbers with a selected incumbent).** *Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked. The statement and proof above are unchanged.* Proposition 6 is the Bayes rule under (A2): given (F_n, Δ_n) the comparison noise η_n has mean zero and a law that does not depend on the history beyond σ_n. Under common random numbers the comparison shares the recorded incumbent's error e (the setting of §5): η_n = ε_n − e. In the kernel of Corollary 9a, η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n. After keeps e is a selected error (Proposition 9), so η_n is not independent of the history: its conditional mean is (ϱ_n − 1)E[e | F_n], which is negative whenever E[e | F_n] > 0. The Bayes rule is still "keep iff E[Δ_n | F_n, Δ̂_n] > 0" (first line of the proof above). If, in addition, e | F_n is Gaussian and independent of Δ_n given F_n, it is the threshold rule
  Δ̂_n > t**_n = −(1 − ϱ_n) E[e | F_n] − μ_n w_n²/τ_n²,  w_n² = σ_{c,n}² + (1 − ϱ_n)² Var(e | F_n)
(`author_packets_20261122/P06_T4_PROP6.md` §4.1). At an unselected record (E[e | F_n] = 0, Var(e | F_n) = σ²) w_n² = 2σ²(1 − ϱ_n) = σ_n², so t**_n = t*_n and Proposition 6 with the measured σ_n is exact. Where E[e | F_n] > 0 (typical after noise-driven keeps, but not guaranteed: Proposition 9 bounds the record's error only given e and Δ_n, and a keep whose Δ̂_n fell below its prior mean can leave E[e | F_n] < 0), the location of the threshold shifts down by (1 − ϱ_n)E[e | F_n]. The variance term moves it further down when μ_n ≤ 0 and Var(e | F_n) ≤ σ², because then w_n ≤ σ_n. So when E[e | F_n] ≥ 0, μ_n ≤ 0 and Var(e | F_n) ≤ σ², t**_n ≤ t*_n, and the deployed rule (t*_n with the measured σ_n, `C3_DESIGN.md` §1) is **conservative**: it keeps a subset of what the Bayes rule keeps, so it keeps too few, not too many. If E[e | F_n] < 0 the location term raises the threshold, and with μ_n = 0 and Var(e | F_n) = σ² the deployed rule keeps too many. For μ_n > 0 the variance term raises the threshold by μ_n(σ_n² − w_n²)/τ_n² and can offset the location shift, so the direction is not determined in general. After a keep e is truncated, not Gaussian, so t**_n is an approximation there, and the exact rule has no closed form. P06 §4.1 checks t**_n numerically at illustrative (not measured) posteriors of e. The derivation above uses the kernel of Corollary 9a. Under the shared-component model of §5 (every run's error u + v, Var u = ϱσ², Var v = (1 − ϱ)σ²) the same algebra holds with the record's own fresh noise component v_rec in place of (1 − ϱ_n)e: η_n = v_new − v_rec, t**_n = −E[v_rec | F_n] − μ_n w′_n²/τ_n² with w′_n² = (1 − ϱ_n)σ² + Var(v_rec | F_n) (if v_rec | F_n is Gaussian and independent of Δ_n), t**_n = t*_n at an unselected record about which the history carries no further information, and t**_n ≤ t*_n when E[v_rec | F_n] ≥ 0, μ_n ≤ 0 and Var(v_rec | F_n) ≤ (1 − ϱ_n)σ². *(Added in the review round, Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked; review N2.)* **Size on `digits_mlp`:** [PLACEHOLDER: to be filled from the ENGINEERING_ONLY re-run of T5 with a shared-component error model (PLAN R1-THEORY-RHO item 4), in progress; no number yet.] It is reported as a limitation, not as evidence.

## 3. Proposition 7 — the value of a per-proposal prior over a constant one

**Statement.** Fix n and F_n with π_n < 1, and let t̃ be any F_n-measurable threshold (for example the constant threshold of the node-level index policy). Write f_n for the N(μ_n, s_n²) density. Then

  V*_n − (1 − π_n) V(t̃; μ_n, τ_n, σ_n) = (1 − π_n) (τ_n² / s_n²) · |∫_{t̃}^{t*_n} f_n(u) (t*_n − u) du| ≥ 0,

and

  (1 − π_n) (τ_n²/(2 s_n²)) · min_{u ∈ [t̃, t*_n]} f_n(u) · (t*_n − t̃)²  ≤  gap  ≤  (1 − π_n) τ_n² (t*_n − t̃)² / (2√(2π) s_n³).

Near t*_n, gap ≈ (1 − π_n) τ_n² f_n(t*_n) (t*_n − t̃)² / (2 s_n²).

**Proof.** From the proof of T2 Proposition 1, applied conditionally on F_n: dV/dt = −f_n(t) E[Δ_n | Δ̂_n = t, F_n] = −f_n(t)(τ_n²/s_n²)(t − t*_n). Hence V(t*_n) − V(t̃) = ∫_{t̃}^{t*_n} dV/du du = (τ_n²/s_n²) ∫_{t̃}^{t*_n} f_n(u)(t*_n − u) du. The integrand has the sign of (t*_n − u), which is the orientation of the interval, so the oriented integral is non-negative. That gives the identity. Bound f_n between its minimum on the interval and its global maximum 1/(s_n√(2π)). Using ∫_{t̃}^{t*}|t* − u| du = (t* − t̃)²/2 gives both bounds. The approximation is the first-order Taylor expansion of f_n at t*_n. ∎

**Corollary 7a (campaign-level gain of the threshold part).** Under the decision-independence condition of Proposition 10, the gain of the per-proposal threshold over any threshold rule t̃_n, at the same execution decisions, is E[Σ_n a_n · gap_n]. It is zero iff t̃_n = t*_n on the executed trials.

**Reading (what to estimate before training).** The gain is governed by the **dispersion of the per-proposal optimal thresholds** around the threshold actually used, weighted by τ²/s³. The upper bound needs only predicted (μ_n, τ_n) and the measured σ_n, so a pilot predictor — a tabular model, or the LLM's own probabilities — gives an estimate of how much any better predictor could still add. The gap is quadratic in the threshold error. Small prior errors therefore cost little, and the benefit concentrates on proposals whose prior is far from the node average. This is the formal version of the 18 Oct offline check (e.g. `digits_mlp`: `BATCH_SIZE` edits average −0.012 and `HIDDEN_UNITS` +0.004, against a paired noise of ≈ 0.0075).

## 4. Proposition 8 — screening before execution (skip)

**Statement.** Assume decision independence (Proposition 10). Then the policy that, at E1, executes iff

  V*_n = (1 − π_n) V(t*_n; μ_n, τ_n, σ_n) ≥ g,

and at E2 applies Proposition 6, maximises J_g over all non-anticipating policies. Its gain over "always execute, then apply Proposition 6" is E[Σ_n (g − V*_n)⁺].

**Proof.** By Proposition 10, the continuation value after trial n does not depend on (a_n, k_n). So the optimal (a_n, k_n) maximise the expected immediate reward E[Δ_n k_n − g a_n | F_n]. If a_n = 1, the best k_n is that of Proposition 6, with value V*_n − g. If a_n = 0, the value is 0. Execute iff V*_n − g ≥ 0. Relative to a_n ≡ 1, the per-trial gain is max(V*_n − g, 0) − (V*_n − g) = (g − V*_n)⁺. ∎

**Corollary 8a (rule-detectable waste; revised 19 Oct 2026).** On a bit-exact node:
- (i) **No-op** (I_n detectable, e.g. inactive keys only): π_n = 1, so V*_n = 0, and skipping is optimal for every g > 0.
- (ii) **Duplicate** (D_n): a run returns the metric already in the ledger, so it carries no information and its value is 0 − g < 0 for every g > 0. Skipping is optimal.
- (iii) **Moreover, under ρ a duplicate can never be kept.** The recorded incumbent value B is non-decreasing in n (ρ replaces B only by a larger recorded value). A duplicate's known metric m was recorded at some earlier trial k with m ≤ B_k ≤ B_n, so Δ̂_n = m − B_n ≤ 0 and the strict keep rule discards it. *Proof:* the monotonicity of B under ρ, plus m ≤ B_k, because either m was discarded at k (m ≤ B_k) or m became the record and was later replaced by a larger one. ∎ The C3 pilot agrees: the maximum Δ̂ over all 727 duplicates is exactly 0.

These cases need no learning. They are the "rule" layer of C3 (D25, D27). The learned layer only matters on the remaining proposals. A duplicate's true increment is not 0, so it is **not** given the no-op label (C3 labels: no training label for duplicates). Under a threshold rule with t* < 0, a duplicate could pass the threshold on its stale recorded value. A rule-based arm skips it instead, and an arm without the rule layer that keeps one is charged its audited (or proxy) Δ.

**Reading.** T2 Proposition 5 showed that at a fixed run budget a run is expensive (price g), so verify, which spends 2r runs, rarely pays. Proposition 8 is the other side of the same fact: a control that **saves** runs earns up to g per avoided run. The value of screening is set by how much prior mass of V*_n lies below g, i.e. by how predictable the bad proposals are. With an LLM-call cap N, skipping spends calls. A binding cap shows up as a positive price on calls, which raises the bar for skipping. That is not modelled here; the empirical design reports it through the matched LLM-call cap.

## 5. Proposition 9 — the winner's curse holds for every adaptive proposer

*Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked. The 18 Oct statement assumed the Gaussian kernel ε_n | (F_n, e, Δ_n) ∼ N(ϱ_n e, σ_{c,n}²). Following the author's decision (PLAN R1-THEORY-RHO (1)), the main statement is now kernel-free, and the 18 Oct formula is Corollary 9a under the kernel, with its scope. Erratum of the 27 Oct audit, kept: Δ_n is not F_n-measurable (under (A1) it is random given F_n); the 18 Oct proof said that the proposer enters only through F_n-measurable Δ_n and ϱ_n. The statements below condition on Δ_n explicitly. Proof-check packet: `author_packets_20261122/P09_T4_PROP9.md`.*

**Setting.** The recorded value of the incumbent is B = J(inc) + e; e is not observed. On I_nᶜ the candidate's recorded value is J(c_n) + ε_n, where ε_n is its recorded error, so the comparison is Δ̂_n = Δ_n + ε_n − e with Δ_n = J(c_n) − J(inc). ρ keeps iff Δ̂_n > 0. A keep replaces the record by the candidate's recorded value, so the new incumbent's recorded error is e' = ε_n. **No assumption is made on the joint law of (F_n, e, ε_n, Δ_n), and none on the proposer.** Write K = {Δ̂_n > 0} for the keep event. For a σ-field G write p_G = P(K | G), and on {p_G > 0} write E[X | K, G] = E[X 1_K | G] / p_G.

**Statement (Proposition 9, restated).** Let the proposal be a non-no-op (on I_nᶜ), and let the proposer be arbitrary: any law for x_n, however it uses the ledger or the displayed record B.
- **(i) Pathwise.** On every keep, e' > e − Δ_n. For a null proposal (Δ_n = 0), e' > e on every keep: the record's error rises at each noise-driven keep, path by path.
- **(ii) In conditional mean.** Let G be any σ-field with respect to which e and Δ_n are measurable (for example G = σ(F_n, e, Δ_n)), and assume E|ε_n| < ∞. Then, almost surely,
  - (ii.1) on {p_G > 0} (a keep has positive conditional probability): E[e' | K, G] > e − Δ_n; for a null proposal, E[e' | K, G] > e;
  - (ii.2) on {0 < p_G < 1} (a keep and a discard both have positive conditional probability): E[e' | K, G] > E[ε_n | G]. Together with (ii.1): E[e' | K, G] > max(e − Δ_n, E[ε_n | G]).
- **(iii) Zero-mean candidate error.** With G as in (ii): if the candidate's error has conditional mean zero, E[ε_n | G] = 0, then E[e' | K, G] > 0 on {0 < p_G < 1}, whatever the sign of Δ_n and of e. The value of e is not used. The case e = 0 is the reading: from an unbiased record and with such a candidate error, even a true improvement enters the record with a positive expected error. *(Review round, Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked; review N1: the hypothesis e = 0 of the first version is dropped because the proof does not use it.)*
- **(iv) Less information.** For any σ-field G′ (for example F_n alone, which contains neither e nor Δ_n), if E|e|, E|Δ_n| and E|ε_n| are finite, then E[e' | K, G′] > E[e − Δ_n | K, G′] on {P(K | G′) > 0}. The right side is also conditional on the keep.

**Assumptions, collected.** Non-no-op proposal (the pathwise part (i) also holds on I_n; on a bit-exact node a no-op has Δ̂_n = 0 and is never kept); a keep of positive conditional probability for (ii.1) and (iv), and in addition a discard of positive conditional probability for (ii.2) and (iii); E|ε_n| < ∞ (and E|e|, E|Δ_n| < ∞ for (iv)); e and Δ_n G-measurable in (ii)–(iii). Corollary 9a does not need E|e| < ∞: its inequality follows directly from the inverse-Mills bounds. The statement is about the record's error after a keep. It does not say how often a proposer produces keeps, and it does not bound the unconditional bias of a campaign. *Threshold rules:* under ρ_t (keep iff Δ̂_n > t, with t G-measurable) the same proof gives (i) and (ii.1) with e − Δ_n + t in place of e − Δ_n, and (ii.2) unchanged.

**Proof.** (i) K = {Δ_n + ε_n − e > 0} = {ε_n > e − Δ_n}, and on K, e' = ε_n.
(ii.1) Put c = e − Δ_n, which is G-measurable, and Y = (ε_n − c) 1_K. Then Y ≥ 0, and Y > 0 on K, so E[Y | G] is well defined, and E[Y | G] = E[ε_n 1_K | G] − c p_G. Let A = {p_G > 0, E[Y | G] = 0} ∈ G. Then E[Y 1_A] = 0, so Y = 0 a.s. on A, so P(K ∩ A) = 0, so E[p_G 1_A] = 0, so P(A) = 0. Hence E[Y | G] > 0 a.s. on {p_G > 0}. Dividing by p_G gives E[ε_n | K, G] > c. With Δ_n = 0 this is the null case.
(ii.2) On Kᶜ, ε_n ≤ c, so on {p_G < 1}, E[ε_n | Kᶜ, G] ≤ c. On {0 < p_G < 1}, E[ε_n | G] = p_G E[ε_n | K, G] + (1 − p_G) E[ε_n | Kᶜ, G], so E[ε_n | K, G] − E[ε_n | G] = (1 − p_G)(E[ε_n | K, G] − E[ε_n | Kᶜ, G]) > 0 by (ii.1).
(iii) Substitute E[ε_n | G] = 0 in (ii.2).
(iv) Z = (ε_n − e + Δ_n) 1_K is integrable, Z ≥ 0 and Z > 0 on K. The argument of (ii.1) with G′ in place of G gives E[Z | G′] > 0 on {P(K | G′) > 0}. Divide by P(K | G′).
No step uses the law of x_n, so the statements hold for every proposer. ∎

**Corollary 9a (the Gaussian kernel; the 18 Oct statement).** Suppose in addition that ε_n = ϱ_n e + σ_{c,n} ξ_n, where ξ_n ∼ N(0, 1) is independent of (F_n, e, Δ_n), and ϱ_n ∈ [0, 1) and σ_{c,n} = σ√(1 − ϱ_n²) > 0 are F_n-measurable. Then, for every proposer,

  E[e' | keep, F_n, e, Δ_n] = ϱ_n e + σ_{c,n} λ(a_n),  a_n = ((1 − ϱ_n) e − Δ_n) / σ_{c,n},

and E[e' | keep, F_n, e, Δ_n] > max(e − Δ_n, ϱ_n e). In particular:
- (a) for a null proposal (Δ_n = 0), E[e' | keep, ·] > e for every e (the 18 Oct text restricted (a) to e ≥ 0; the restriction is not needed);
- (b) if e = 0, E[e' | keep, ·] = σ_{c,n} λ(−Δ_n/σ_{c,n}) > 0, which shrinks as Δ_n/σ_{c,n} grows.

*Proof.* Given G_n = σ(F_n, e, Δ_n), ε_n ∼ N(ϱ_n e, σ_{c,n}²) and K = {ε_n > e − Δ_n}, so 0 < p_{G_n} < 1. The mean of a normal variable with mean m and standard deviation σ_c, truncated from below at c, is m + σ_c λ((c − m)/σ_c). With m = ϱ_n e and c = e − Δ_n this is the formula. The inequality follows directly from λ(a) > max(0, a) for all real a: the mean exceeds m = ϱ_n e and m + σ_{c,n}a_n = e − Δ_n. This route needs no moment of e. (Where E|e| < ∞ it is also Proposition 9(ii) with E[ε_n | G_n] = ϱ_n e.) (a) and (b) follow by substitution. ∎

**Scope of Corollary 9a.** The kernel is an assumption on the conditional law of the candidate's error given the actual history, F_n included. It does not follow from the bivariate-normal model of T2 §5 once the record has been selected. It is exact
- for ϱ_n = 0 when every candidate error is a fresh draw independent of the past: then the kernel holds after any number of keeps;
- for ϱ_n > 0 at a comparison against an unselected record whose error is jointly normal with the candidate's, and about which the history carries no further information (for example the first comparison against the campaign's initial, never-compared record; a re-measured incumbent whose earlier record stays in the ledger is not an example, because B_new − B_old informs the split of e: review m1). Under the shared-component model below, earlier recorded comparisons against the same record already carry such information (AI analysis, unreviewed: given e, the recorded Δ̂_j of the spell have non-zero partial covariance ϱ(1 − ϱ)σ² with the shared component);
- wherever the kernel is assumed as the generative model: a candidate's error is ϱ times the current record's error plus fresh noise, as in T3's `crn` regime and T5's `record` noise model.

It is not exact under a shared-component model, in which every run's error is u + v with u shared by the campaign (variance ϱσ²) and v fresh per run (variance (1 − ϱ)σ²). A keep selects on v alone. After one null keep, the mean of a fresh error given the record's error e is −0.231 at e = 0 and +0.306 at e = 0.9, against the kernel's 0 and 0.45 (ϱ = 0.5, σ = 1; `author_packets_20261122/check_output.txt`, P09 §4). On the PILOT E1 runs of 22 Oct, the screening property that the kernel implies is roughly met on the OpenML nodes and not met on `digits_mlp` (`check_kernel_e1_output.txt`: partial correlation of sibling edits given the default +0.37, bootstrap interval +0.24 to +0.51; AI analysis, unreviewed, of data the author has not yet accepted). Proposition 9 itself holds under every one of these models. Numerical check under the shared-component model with a proposer that reads the displayed record (ϱ = 0.5, σ = 1, 2 × 10⁶ campaigns of 12 trials; `check_p07_p09.py`, last lines of `check_output.txt`): e' > e − Δ_n on all 4,864,272 keeps; on records kept at least once, in the bin e ≈ 0, Δ_n ≈ 0, E[e' | keep] = +0.513 (s.e. 0.004) exceeds both the mean of e − Δ_n over the keeps (−0.001) and the mean candidate error (−0.514), while the kernel formula gives +0.691. The inequalities hold in all five bins checked.

**Reading.** T2 Proposition 4(b) needed ϱ = 0 and i.i.d. null proposals. Proposition 9 needs neither: the bias is a property of the acceptance rule ρ, not of the proposer. No proposer, however it uses its memory, avoids it. What the proposer *can* do is react to the inflated B it is shown. That is the feedback channel of §6 and the subject of the debiased-memory add-on ("route D"): display the run-free posterior estimate B̃ = B̃_prev + E[Δ_n | F_n, Δ̂_n] (Proposition 6's posterior mean, summed over keeps) instead of B.

## 6. Proposition 10 — when myopic acceptance is optimal, and when it is not

**Definition (decision independence, DI).** For each n, the conditional law of the future observables (x_m, 1{I_m}, Δ_m, Δ̂_m)_{m > n}, given (F_n, Δ̂_n, a_n, k_n), does not depend on (a_n, k_n).

**Statement (a).** Under DI, with the horizon N fixed, the myopic policy of Propositions 8 and 6 maximises J_g over all non-anticipating policies.

**Proof.** Backward induction on n. Let C_n(h, a, k) be the supremum, over non-anticipating continuation policies, of the expected future reward E[Σ_{m > n}(Δ_m k_m − g a_m) | F_n, Δ̂_n, a_n = a, k_n = k], with h = (F_n, Δ̂_n). Future rewards are functions of the future observables and the future decisions only. Future decisions are functions of observables, where (a, k) enters as a known constant in each branch. By DI the law of the future observables is the same for every (a, k). So any continuation policy available in branch (a, k) has a counterpart in branch (a', k'), obtained by fixing its (a, k) argument, with the same law of future rewards. Hence C_n(h, a, k) = C_n(h). The total objective from trial n is then the immediate reward plus C_n(h), and the optimal (a_n, k_n) maximise the immediate reward. That is Propositions 8 and 6. ∎

**Statement (b) — failure without DI.** There are proposers for which the myopic policy loses an arbitrarily large amount. Example (σ → 0, g = 0, N = 2): trial 1 proposes a known Δ₁ = −α < 0. If it is kept, trial 2 draws Δ₂ ∼ N(β, τ²); if it is discarded, Δ₂ ∼ N(0, τ²). Myopic acceptance discards trial 1 and earns E[max(Δ₂, 0)] = τφ(0). Keeping earns −α + βΦ(β/τ) + τφ(β/τ). With τ = 1 and β = 2 the difference is 1.61 − α, so for α < 1.61 the myopic rule loses 1.61 − α, and the loss grows without bound in β.

**Reading.**
- DI fails whenever the next proposal's law depends on the keep decision through more than the incumbent's configuration, and that is the normal case for an LLM manager with memory: `append_only_summary` shows what was kept and the record B.
- Statement (a) is therefore the precise scope of T2 and of C3's plug-in rule. Statement (b) is the precise scope of RL: a learned policy can beat the per-proposal Bayes rule only through decisions that change the future proposal law. This is the rule "when RL is needed" (PLAN C2, identification ladder), stated as a condition on the proposer.
- DI can be **tested**. Compare the proposal law (edit sizes, novelty, audited μ of proposals) after keep vs discard decisions forced by the control plane at matched histories (E2 branch pairs already provide this). It can also be **manipulated**: memory off vs on (D24), and raw vs debiased record (route D). An observed DI violation that is small means stage 3 of the post-training ladder can be dropped on evidence.

## 7. Remark — calibration vs decision-focused training of the predictor

C3 trains a predictor q_θ(x, F) of (π_n, μ_n, τ_n) and plugs it into Propositions 6 and 8.
- **If q_θ is exactly the conditional law in (A1)**, the plug-in rule is optimal (Proposition 6, Proposition 10(a)), so no decision-focused objective can improve on it. Training with a strictly proper scoring rule (log score) has the true conditional law as its population optimum.
- **If the model class cannot represent the conditional law**, the scoring-rule optimum and the decision optimum generally differ. The decision loss is the gap of Proposition 7, which weights errors by τ²/s³ near t*_n and the screening loss (g − V*)⁺ near g. A strictly proper score weights all errors in the predicted distribution. Decision-focused training (reward = realised J_g contribution) moves capacity toward proposals near those two boundaries.
- **Prediction for the ladder:** stage 2 (decision-focused GRPO) beats stage 1 (log-score SFT) only to the extent that stage 1 is miscalibrated or capacity-limited near the boundaries. With GRPO, the within-group reward variance on a proposal is non-zero only when sampled forecasts fall on both sides of a boundary, so the learning signal concentrates on exactly those proposals. Both predictions are checked in the C3 design (`docs/r1/C3_DESIGN.md`).

## 8. What is not shown here

- No hard-budget optimality: the run price g is a Lagrange multiplier tuned on development instances.
- No result on verify with a per-proposal prior beyond the remark that T2 Proposition 2 applies conditionally on F_n with (μ_n, τ_n) in place of (μ₀, τ₀).
- The additive model (final improvement = sum of kept true increments) ignores interactions between edits; E1 found the seed effects themselves non-additive on `digits_mlp` (NOISE_FLOOR caveats).
- Gaussianity on I_nᶜ is an assumption. The predictor's output is a discretised distribution (C3_DESIGN §3), and the rules are then applied to its first two moments. A non-Gaussian version of Proposition 6 (keep iff the predictive posterior mean > 0) is immediate, but the closed forms of Propositions 7–8 are Gaussian.
- Proposition 10(b) is an existence example, not an estimate of how often DI fails in practice.
