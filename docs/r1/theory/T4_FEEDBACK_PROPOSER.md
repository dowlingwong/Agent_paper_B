# T4 — Acceptance under noise with a ledger-dependent proposer

*Theory track, extension of T2. Drafted 18 Oct 2026 by an AI agent (Claude, coordinating session) at the author's request. AI-assisted; the author has not checked these proofs yet and no human has reviewed them (PLAN §9 item 6). The two closed forms that carry the C3 design (the gain identity of Proposition 7 and the truncated-mean formula of Proposition 9) were checked against Monte Carlo on 18 Oct 2026 (2–4 × 10⁶ draws; agreement to MC error); the check script is not yet committed as a test.*

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

**Setting.** The recorded value of the incumbent is B = J(inc) + e; e is not observed. On I_nᶜ the candidate's single-run error is ε_n = ϱ_n e + σ_{c,n} ξ_n, where ξ_n ∼ N(0, 1) is independent of (F_n, e, Δ_n), and ϱ_n ∈ [0, 1), σ_{c,n} = σ√(1 − ϱ_n²) are F_n-measurable. This is T2 §5's bivariate-normal model, with ϱ allowed to depend on the kind of edit. The comparison is Δ̂_n = Δ_n + ε_n − e, and ρ keeps iff Δ̂_n > 0. After a keep, the new incumbent's recorded error is e' = ε_n.

**Statement.** For every proposer — any F_n-measurable law for x_n, however it uses the ledger or the displayed record B —

  E[e' | keep, F_n, e, Δ_n] = ϱ_n e + σ_{c,n} λ(a_n),  a_n = ((1 − ϱ_n) e − Δ_n) / σ_{c,n},

and E[e' | keep, F_n, e, Δ_n] > max(e − Δ_n, ϱ_n e). In particular:
- (a) for a null proposal (Δ_n = 0) and e ≥ 0, E[e' | keep, ·] > e: each noise-driven keep raises the record's bias in expectation, for every ϱ < 1;
- (b) if e = 0, E[e' | keep, ·] = σ_{c,n} λ(−Δ_n/σ_{c,n}) > 0: even a true improvement enters the record with a positive bias, which shrinks as Δ_n/σ_{c,n} grows.

**Proof.** Given (F_n, e, Δ_n), ε_n ∼ N(ϱ_n e, σ_{c,n}²), and keep ⇔ ε_n > e − Δ_n. By the mean of a normal truncated from below at c: E[ε | ε > c] = m + σ_c λ((c − m)/σ_c), with m = ϱ_n e and c = e − Δ_n. This gives the formula. The Mills-ratio inequalities λ(a) > 0 and λ(a) > a for all real a give E[e' | ·] > m = ϱ_n e and E[e' | ·] > m + σ_c a = c = e − Δ_n. (a) and (b) follow by substitution. The proposer enters only through Δ_n and ϱ_n, which are F_n-measurable; the bound holds pointwise, so it holds for every proposer law. ∎

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
