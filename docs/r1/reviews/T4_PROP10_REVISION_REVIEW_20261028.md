# Independent review: T4 Proposition 10 revision (28 Oct 2026)

**Reviewed:** `/mnt/user-data/outputs/t4/T4_PROP10_REVISION_20261028.md` (cited as `REV:line`), together with `t4_prop10_revision_20261028/ex10c.py` and `ex10c_output.txt`.
**Context read:** `docs/r1/theory/T4_FEEDBACK_PROPOSER.md` (`T4:line`), `T2_DERIVATIONS.md` §1–2, `T_AUDIT_20261027.md` (Props 6–10), `proposals/THEORY_CORRECTIONS_20261027.md`, `reviews/LOCAL_THEORY_CORRECTIONS_REVIEW_20261027.md`.
**Status:** this is an AI-assisted mathematical review. It is not an author proof check. I did not edit the document.

**Overall verdict: Correct with fixes. Three findings block adoption.** The core argument holds: the per-trial bound in Proposition 10(a′) and its attainment by the myopic rule are valid under (NF) and (NI) as formally stated. The closed forms and the table in Proposition 10(c) reproduce exactly. The three blocking problems are elsewhere:
- the setting of §1 quietly makes (NF) policy-dependent through the duplicate and no-op filters;
- Remark R1 misses that T4 Proposition 9's model also violates (NF);
- Remark R3 claims a campaign-sum result under (NF) alone, and the paper's own example 10(c) refutes that claim.

## Summary of verdicts

| Item | Verdict |
|---|---|
| 1. Proposition 8′ (incl. edge cases, O_n) | **Correct with fixes** (minor) |
| 2. Proposition 10(a′), Steps 1–3, part 3 | **Correct as stated, with a hidden setting assumption (Gap, blocking B1)** |
| 3. Removal of the second clause of (NI) | **Correct**; the justification needs rewording |
| 4. Proposition 10(c) | **Correct** (closed forms, slope and table verified); minor fixes |
| 5. R1 | **Correct but incomplete (blocking B2)**. R3: **Wrong (blocking B3)**. R6: **Correct with fixes** |
| 6. Overclaims | Several wording fixes (minor), listed in §6 |

---

## 1. Proposition 8′ — Correct with fixes

I checked the following and they hold:
- **Part 1.** The tower-property argument and the pointwise maximiser k = 1{m > 0} are correct for any (O_n ∨ σ(H_n))-measurable k_n.
- **Integrability.** E|Δ_n| < ∞ gives E m_n⁺ ≤ E|Δ_n| < ∞, so no further integrability assumption is needed.
- **Parts 2–3.** The algebra max(V − g, 0) − (V − g) = (g − V)⁺ is correct.
- **Ties.** These are handled correctly ("either at equality").
- **π_n = 1.** This gives Δ_n = 0 a.s., so V*_n = 0 and skipping is optimal for g > 0 (a tie at g = 0).
- **τ_n = 0, π_n ∈ (0,1).** On a bit-exact node with σ_n > 0, {H_n = 0} identifies I_n a.s. Otherwise m_n = μ_n, so V*_n = (1 − π_n)μ_n⁺. The case σ_n = 0 also works, because then H_n = μ_n ≠ 0 still separates I_n from I_nᶜ. If μ_n = 0, every decision ties.
- **O_n.** The information set is defined correctly. O_n contains a_j H_j and a_j, so a skip (a_j = 0, a_j H_j = 0) reveals nothing, and an executed result of 0 can be told apart from a skip. This fixes the defect in T4's DI that the audit identified (T_AUDIT:47, 55).

Fixes:

- **1a (minor, REV:31).** "m_n(h) = E[Δ_n | O_n, H_n = h] **on {a_n = 1}**" leaves m_n, and therefore V*_n = E[m_n⁺ | O_n], undefined on {a_n = 0}. Yet the E1 rule must evaluate V*_n *before* a_n is chosen, which makes the definition circular. a_n is O_n-measurable, so "conditioning on a_n = 1" adds nothing.
  *Fix:* define m_n := E[Δ_n | O_n ∨ σ(H_n)] on the whole space. H_n is a well-defined potential outcome even when it is not observed. Then state Part 1 as an a.s. inequality E[Δ_n k_n | O_n] ≤ V*_n for every admissible k_n.
- **1b (minor, REV:31).** "m_n > 0 ⟺ H_n > t*_n" is false on {H_n = 0} when t*_n < 0 (μ_n > 0). That event has probability π_n > 0, and there m_n = 0 < H_n − t*_n. The value formula is unaffected, because a kept no-op is worth 0, but the equivalence is not. It also needs τ_n > 0, since t* is undefined at τ_n = 0.
  *Fix:* "on {H_n ≠ 0} and for τ_n > 0, m_n > 0 ⟺ H_n > t*_n", which is how T4 Prop. 6 (T4:36–38) states it.
- **1c (minor, REV:26, 31).** "H_n = 0 on I_n" holds only on bit-exact nodes. "{H_n = 0} identifies I_n" also needs a continuous comparison law on I_nᶜ. That fails for metrics on a finite lattice (accuracy on a finite test set), where H_n = 0 has positive probability on I_nᶜ. Part 1 in its general form (m_n = E[Δ_n | O_n, H_n]) still holds; only the Gaussian closed form V*_n = (1 − π_n)V(t*_n) fails.
  *Fix:* state the bit-exact and continuous-metric restriction for the closed form. Say that on non-bit-exact nodes H_n = η_n on I_n and V*_n is a mixture posterior value.
- **1d (minor, REV:31, 36).** "(A1)–(A2) restated with O_n in place of F_n" is a new assumption, not a restatement. O_n is policy-dependent and coarser than F_n. Gaussianity given F_n generally turns into a Gaussian *mixture* given O_n, so the two versions cannot both hold for all policies. Under (NI) this problem disappears, because the relevant σ-field becomes σ(x_{1:n}).
  *Fix:* in Prop. 8′.1, write "if, at this history, the conditional law of (1{I_n}, Δ_n, η_n) given O_n satisfies (A1)–(A2)". Do not imply that T4's F_n-version delivers this.
- **1e (minor, REV:35).** "Fix … a supported pre-execution history" should be "almost surely on O_n". With continuous H_j in the history, individual histories have probability 0. This is the audit's convention (T_AUDIT:5).
- **1f (minor, REV:28).** "Skip does not reveal H_n" is correct *within the model*, but the model assumes execution reveals **only** H_n. A real run also reveals the candidate's absolute metric (equivalent to H_n given B), learning curves, wall time and crash status. Any such output that can predict later increments must be included in Y_n = (1{I_n}, Δ_n, η_n) and covered by (NI). If it is left out, Step 1's inclusion O_n ⊆ σ(x_{1:n}, Y_{<n}, U) fails.
  *Fix:* add to §1: "execution reveals H_n and nothing else (or: Y_n includes every output an execution reveals)".

## 2. Proposition 10(a′) — proof correct; hidden setting assumption (B1)

### Step 1 — correct

Proof by induction:
- a_j is O_j-measurable.
- k_j is (O_j ∨ σ(H_j))-measurable.
- H_j is a function of Y_j.

So every past decision and every revealed observation lies in σ(x_{1:n−1}, Y_{<n}, U), and O_n ⊆ G_n := σ(x_{1:n}, Y_{<n}, U). The doc's x_{1:n−1} is right for the decisions; the bound uses x_{1:n}.

Combining the two independence facts:
- U ⊥ W_{1:N} gives U ⊥ (Y_n, Y_{<n}) | x_{1:n} by weak union.
- With (NI), the joint conditional law then factorises, so Y_n ⊥ (Y_{<n}, U) | x_{1:n}.

Since σ(x_{1:n}) ⊆ O_n ⊆ G_n, E[f(Y_n) | O_n] = E[E[f(Y_n) | G_n] | O_n] = E[f(Y_n) | x_{1:n}]. Hence (Δ_n, H_n) ⊥ O_n | x_{1:n}. Weak union gives Δ_n ⊥ O_n | (x_{1:n}, H_n), which is Part 1.

U ⊥ W is enough, provided **all** randomness the control plane uses is in U. That includes any LLM sampling in the memory summariser or the forecaster, and any shared seeds or caches with the proposer. Randomness correlated with W breaks the step. State this explicitly (minor, REV:27).

### Step 2 — correct for arbitrary randomized non-anticipating policies

- k_n = a_n k_n is (O_n ∨ σ(H_n))-measurable on the whole space, so E[Δ_n k_n | O_n ∨ σ(H_n)] = k_n m_n(x_{1:n}, H_n).
- k_n m_n ≤ k_n m_n⁺ ≤ a_n m_n⁺.
- E[a_n m_n⁺ | O_n] = a_n E[m_n⁺ | x_{1:n}] by Step 1, which gives a_n(V*_n − g) ≤ (V*_n − g)⁺.

Randomization enters only through U ∈ O_n. Regular conditional laws are not needed: everything is a conditional expectation, and m_n(x, h) and V*_n(x) exist by Doob–Dynkin. The versions are unique up to null sets of the common law of (x_{1:n}, H_n), and under (NF) that law is the same for every policy, so the myopic rule is well defined across policies.

### Step 3 — correct

- The myopic rule attains equality in both inequalities.
- (NF) makes the law of x_{1:N}, and therefore the law of V*_n(x_{1:n}), policy-invariant, so the bound Σ_n E[(V*_n − g)⁺] is common to all policies.
- **Part 3 is valid.** Under always-execute, the information is finer, but by Part 1 m_n and V*_n are unchanged, so J = Σ E[V*_n − g] under the same law of x.

This fixes the audit's summed-gain objection (T_AUDIT:47) **under (NF) + (NI)**.

### B1 (blocking): duplicate and no-op filtering is policy-dependent, so (NF) as glossed cannot hold in the stated setting (REV:24, 26, 48)

- §1 removes duplicates "from the sequence by the rule layer" and says they "are not trials here" (REV:24).
- T4's D_n is defined relative to *earlier evaluated* configurations other than the incumbent (T4:24). Whether x_n is a duplicate therefore depends on a_{1:n−1}, and also on k_{1:n−1}, through the incumbent.
- An edit re-proposed after a **skip** is a fresh trial. The same edit re-proposed after an **execution** is a duplicate and is removed.
- So the identity, the number (N is the LLM-call cap and duplicates consume calls) and the law of the re-indexed trial sequence W_{1:N} differ across policies.
- The same applies to I_n ("leaves the incumbent's effective configuration unchanged", T4:23). An edit that sets a key to a value becomes a no-op after an identical edit has been kept.

(NF) is a stated assumption, so the theorem is not wrong. But its verbal gloss (REV:48) omits this channel. In practice the channel is not marginal: in the C3 pilot, 727 of 841 rule-detectable proposals were duplicates (T4:24). Exact re-proposals also **violate (NI)** if they are kept in the sequence: with bit-exact fixed-seed nodes, Y_n = Y_j for x_n = x_j, which cannot be conditionally independent given x_{1:n} unless Y_j is a function of x.

*Fix:* add an explicit assumption to (NF). Either
- (i) duplicate and no-op status are functions of x_{1:n} alone and are the same under every policy, and filtered proposals do not consume the horizon; or
- (ii) the horizon contains no re-proposal of an earlier effective configuration.

State that (NF) excludes the "re-proposed after skip" pattern, and that exact repeats are an (NI) violation if kept.

### Further hidden or mis-cited assumptions (minor)

- **2a (REV:48).** "an edit's true increment does not depend on which earlier edits were kept (non-interacting edits, the additive model of T2 §1)". T2 §1's additive model (T2:17) is the value statement "final improvement = sum of kept increments". With Δ_n defined relative to the current incumbent, that is an exact telescoping identity and says nothing about interactions. Non-interaction (the law of Δ_n does not depend on inc_n) is a **new, substantive** assumption. T4 §8 (T4:125) notes it is contradicted on `digits_mlp`.
  *Fix:* cite it as a new assumption, not as T2 §1.
- **2b (REV:48).** (NF) also requires that the comparison noise η_n not depend on the incumbent's identity. This fails in T4 Prop. 9's model; see B2.

## 3. Removal of the second (NI) clause — Correct; reword the justification

The proof uses (NI) only at the current trial and conditions on x_{1:n} (Step 1). Nothing in Steps 2–3 needs a condition linking later proposals to earlier outcomes, and the policy-invariance of the law of x_{1:N} comes from (NF). So removing the clause is justified.

The stated reason (REV:49: "under (NF) a proposer cannot react to revealed results, since what is revealed depends on the policy") is imprecise. (NF) does permit x_m to depend on earlier outcomes Y_j *exogenously*, for example an oracle or a shadow evaluation independent of the control plane. What (NF) excludes is dependence on the *policy-dependent record*. Such dependence is harmless for the proof, but it can itself make (NI) fail through conditioning on x_{1:n} (a collider: for example, x_n a function of Y_j and correlated with Y_n). So the test of (NI) must condition on the full proposal history.

*Fix:* "No separate condition linking later proposals to earlier outcomes is needed: the proof uses (NI) only at the current trial, conditional on the whole proposal history x_{1:n}. If proposals depend on earlier outcomes, that dependence is absorbed by conditioning on x_{1:n} (and may itself cause (NI) to fail)."

## 4. Proposition 10(c) — Correct; minor fixes

### Closed forms

All verified analytically, and by quadrature in an independent script.

**Myopic policy**
- V*₁ = E[(αθ)⁺] = αφ(0).
- For g > αφ(0), myopic skips trial 1.
- At trial 2 it uses O₂ = σ(x_{1:2}) with a₁ = 0, which is the correct uninformed information. So Δ₂ ∼ N(0, β²), H₂ = βθ + κβ·ε, t* = −μσ²/τ² = 0, and V*₂ = (τ²/s)φ(0) = β²φ(0)/(β√(1+κ²)) = βφ(0)/√(1+κ²).
- J(myopic) = (βφ(0)/√(1+κ²) − g)⁺. Quadrature of E[(E[Δ₂|H₂])⁺] matches to 4 decimals.

**Probe-first policy**
- It is feasible: H₁ = αθ enters O₂ through a₁H₁, so θ is O₂-measurable (α ≠ 0), and Δ₂ = βθ is known at E1 of trial 2. This is the τ = 0 edge case of 8′.4.
- E[(βθ − g)⁺] = β E[(θ − c)⁺] with c = g/β, which equals β[φ(c) − cΦ̄(c)].
- J(probe) = αφ(0) − g + β[φ(g/β) − (g/β)Φ̄(g/β)].

**Asymptotic slope**
- As β → ∞, β ψ(g/β) = βφ(0) − g/2 + O(1/β).
- So loss = βφ(0)(1 − 1/√(1+κ²)) + αφ(0) − g/2 + o(1).
- Slope at κ = 1 is 0.116847. Checked numerically: loss/β = 0.1168624 at β = 10⁴ and 0.1168476 at β = 10⁶. The intercept also matches αφ(0) − g/2 = 0.14894.
- With κ = 0 the loss stays bounded, so "κ > 0" is needed, as stated.

### Table

- I reran `python3 -I ex10c.py`; the output is byte-identical to `ex10c_output.txt`.
- All four rows of REV:83–86 match my quadrature: 0.0642/0.4716/0.4074, 2.3209/3.6434/1.3224, 27.7095/39.5437/11.8342, 281.5948/398.5913/116.9965. The κ = 0.5 row also matches: 3.0682/3.6434.

### (NF) and (NI)

(NF) holds because:
- x₁ and x₂ are deterministic;
- the law of (θ, ε) does not respond to decisions;
- Δ₂ = βθ whether or not trial 1 was kept (non-interaction);
- U ⊥ W.

(NI) fails: Y₂ = (0, βθ, η₂) is not ⊥ Y₁ = (0, αθ, 0) given x.

### Fixes

- **4a (minor; strengthens the claim).** With N = 2 and (NF), the only non-myopic choice is a₁. Given a₁, the choices k₁ = 1{θ > 0} and Bayes-myopic play at trial 2 are optimal. So the optimum is J* = max(J(myopic), J(probe)), and whenever the loss is positive it is **exactly the optimality gap**, not just a lower bound.
  *Fix:* add one sentence saying so.
- **4b (minor, REV:79, 83–86).** The Monte Carlo "check" is noise-limited at large β, and the doc reports it to 4 decimals without uncertainty. My estimates of the per-policy MC standard error (2·10⁶ draws): about 9·10⁻⁴ (β = 2), 4.6·10⁻³ (β = 10), 0.046 (β = 100) and 0.46 (β = 1000). The β = 1000 discrepancy of 0.23 is within one SE.
  *Fix:* report SEs, or check the *loss* with common random numbers (SE ≈ 0.20 at β = 1000).
- **4c (minor, REV:73).** State explicitly that x₁ and x₂ are fixed and that edits do not interact. (NF) depends on both.
- **4d (minor, REV:90).** The reading "a cheap edit to a key, followed by a larger edit to the same key" is consistent with (NF) only if:
  - edits are relative steps;
  - the response is linear in the key, so Δ₂ = βθ whether or not edit 1 was kept;
  - the manager would have proposed edit 2 regardless of edit 1's outcome.

  With "set key = v" semantics, Δ₂ depends on whether edit 1 was kept, and (NF) fails as well.
  *Fix:* "a stylized version of …", and name these conditions.
- **4e (minor, REV:88).** The script path is given as `docs/r1/proposals/t4_prop10_revision_20261028/ex10c.py`, but the file is currently at `/mnt/user-data/outputs/t4/t4_prop10_revision_20261028/ex10c.py`. Fix the path when the file is committed.
- **10(b) (REV:69).** I checked 2Φ(2) + φ(2) − φ(0) = 1.609548, which is correct. "(NI) holds here" is correct but trivial, because Δ₁ is deterministic. (NI) is stated "under that (common) law", which does not exist when (NF) fails. Say "(NI) holds under each policy's law".

## 5. Remarks

### R1 — B2 (blocking): correct about (NI) and (A2), but incomplete. T4 Prop. 9's model also violates (NF)

**The (NI) part is correct.** With Δ̂_n = Δ_n + ε_n − e and ε_n = ϱ_n e + σ_c ξ_n (T4:85), η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n. Within an incumbent spell, Cov(η_n, η_j | x) = (1 − ϱ_n)(1 − ϱ_j)Var(e) > 0 for ϱ < 1, so (NI) fails.

**The (A2) part is correct.** (A2) (T4:26) is consistent at the first comparison against a fresh incumbent, where η ∼ N(0, 2σ²(1 − ϱ)). It is inconsistent at later comparisons in the same spell, where the posterior of e given F_n is not centred, and after any keep, by T4 Prop. 9 itself: E[e′ | keep] > 0.

**What R1 misses: (NF) fails too.** After a keep, the incumbent error becomes e′ = ε_kept, and its law is selected (winner's curse, which is exactly the content of Prop. 9). So the law of η_m for later m depends on the keep policy.

Simulation (σ = 1, ϱ = 0.3, Δ₁ ∼ N(0, 0.25), 2·10⁶ draws):

| Policy | E[η₂] |
|---|---|
| never keep | 0.001 |
| keep by ρ | −0.303 |

So the law of W_{1:N} is not policy-invariant. Consequences:
- Under option (ii) (REV:96), the loop falls outside Prop. 10(a′) entirely, not only through (NI). Props 6–8′ then hold one step at a time with e as a latent state, and campaign statements need a different theorem.
- Option (i) (REV:95) is needed for (NF) as well as (NI). Note that re-measuring the incumbent at each comparison costs runs, which changes the g-accounting.

*Fix:* rewrite R1's first sentence as "Shared and keep-updated incumbent error makes both (NI) and (NF) fail in T4's own Proposition 9 model." Add a row to §6: "after a keep, comparison residuals have a negative mean (winner's curse) — an (NF) violation".

**Two smaller R1 corrections:**
- "unless e is known" (REV:94) is imprecise. With e known, η_n | ⋯ ∼ N((ϱ_n − 1)e, σ_{c,n}²), which has a non-zero mean, so (A2) as written still fails. It holds only after debiasing: Δ̂_n + (1 − ϱ_n)e has noise N(0, σ_{c,n}²). Say "unless e is re-drawn independently for each comparison, or known and subtracted".
- "KG verify is then an information action of exactly the kind Proposition 10(c) prices" (REV:96) overstates. 10(c) has (NF) intact; option (ii) does not. Use "an information action analogous to the one in 10(c)".

**Related note (minor).** On bit-exact nodes at fixed seeds, η_n is a deterministic function of the configuration and the seed. Comparisons of similar configurations at shared seeds are therefore likely correlated, so (NI) may fail generically, beyond the shared-e mechanism. This is worth one sentence under R1.

### R3 — B3 (blocking): Wrong as stated (REV:100)

R3 says campaign sums, including "Proposition 8's E[Σ(g − V*)⁺]", "are valid under (NF) by Proposition 10(a′).3". But 10(a′).3 is proved under (NF) **and** (NI), and the claim is false under (NF) alone. The paper's own example 10(c) shows this (α = 1, β = 10, κ = 1, g = 0.5; (NF) holds):

| Quantity | Value |
|---|---|
| J(myopic) | 2.3209 |
| J(always execute, Bayes keep) | 2φ(0)·5.5 − 1 = 3.3884 |
| Actual screening gain | **−1.0674** (screening loses) |
| E Σ(g − V*)⁺ with the myopic V*'s | +0.1011 |
| E Σ(g − V*)⁺ with always-execute's V*'s | +4.3455 |

The formula is always ≥ 0; the actual gain is negative.

Corollary 7a ("at the same execution decisions") is a different case. It *does* hold under (NF) alone, provided:
- the execution rule does not depend on past keep decisions, so both policies have the same O_n; and
- (A1)–(A2) hold relative to O_n.

*Fix:* "Corollary 7a's sum is valid under (NF) when the execution rule does not depend on past keeps. Proposition 8's E[Σ(g − V*)⁺] is valid under (NF) and (NI) (Prop. 10(a′).3). Under (NF) alone the screening gain can be negative (Prop. 10(c) example). Without these, report campaign gains as measured."

### R4 — Correct with fix (minor, REV:101)

"Otherwise it is an approximation" understates the problem. By the R3 counterexample, the sign can flip.
*Fix:* "otherwise it is a declared scaling with no guaranteed sign relation to the campaign gain". Also check that "20-run campaign" means N = 20 *trials (proposals)*. Prop. 10(a′).3 sums over proposals, not runs, and under skipping these differ.

### R6 — Correct with fixes (minor, REV:103)

The direction "optimistic" is right **for a Bayes myopic controller under (NF)**. Offline, the controller's information O_n^off ⊇ O_n^on. Jensen's inequality, applied twice, gives E[V*_n^off | O_n^on] ≥ V*_n^on and E[(V*_n^off − g)⁺] ≥ E[(V*_n^on − g)⁺]. The bias is zero under (NI) by Part 1.

For a learned, non-Bayes forecaster, extra results can help or hurt, so the sign is not determined. This holds even under (NI), because a forecaster can use past results spuriously. The derivation is not contained in "§1 and §4", as R6 claims.
*Fix:* "For a Bayes (posterior-consistent) myopic controller under (NF), offline evaluation of skipping is weakly optimistic, and unbiased under (NI) (proof: information monotonicity via Jensen). For a learned forecaster the sign is not determined." The exemption for proposal-only arms (A1, A1-ctx) is correct under (NF), provided their E1 decisions do not depend on past results through budgets, the incumbent or the display.

### R2, R5 — Correct

R5's replacement text should use the corrected contrapositive wording from finding 6c.

## 6. Overclaims and wording (all minor)

- **6a (REV:20).** "the loop is a contextual bandit (myopic play is optimal)". In a contextual bandit, feedback is used to learn the reward model, and that information channel is exactly what (NI) excludes. Under (NF) + (NI) with a known conditional law, the problem is a sequence of independent one-shot decisions.
  *Fix:* "… reduces to a sequence of independent one-step decisions".
- **6b (REV:63).** "This is what makes the condition checkable". (NF) quantifies over all feasible policies and is not checkable from data. Only its implications can be tested (§6).
  *Fix:* "primitive (stated on the exogenous process rather than on value functions), with testable implications".
- **6c (REV:65).** "This says that a non-myopic policy is needed." The contrapositive says the opposite direction: failure of (NF) or (NI) is **necessary, not sufficient**, for a non-myopic policy to gain.
  *Fix:* "Failure of (NF) or (NI) is necessary for any policy to beat the myopic rule; it is not sufficient. Propositions 10(b) and 10(c) show that, when it fails, the gain can be unbounded."
- **6d (REV:64, 111).** "If a forecaster's skill improves when it is shown past results, (NI) fails." This is valid only for the Bayes forecast given the **full** proposal history x_{1:n}. A forecaster that sees only x_n can improve from past results under (NI), because past results proxy for x_{1:n−1}. A capacity-limited learned forecaster can improve for other reasons. The converse (no improvement ⇒ (NI)) does not hold either: (NI) is a full conditional-independence statement, and forecast skill tests only the predictive margins that are used.
  *Fix:* "Out-of-sample improvement beyond estimation error, with both forecasters given x_{1:n}, is evidence against (NI); its absence does not establish (NI)."
- **6e (REV:109).** The forced keep/discard branch pairs test only the keep channel of (NF). (NF) also requires invariance to execute versus skip, and to what is displayed. A memory-`none` manager that is still shown the current incumbent configuration violates (NF) through the incumbent. This is a check item; I did not verify what the harness displays.

## Blocking vs minor

**Blocking (fix before the author proof check is closed):**
- **B1** (§2; REV:24, 26, 48). Duplicate and no-op status depends on past executions and keeps, which makes the re-indexed trial sequence policy-dependent. State the policy-invariance or no-repeat assumption as part of (NF), and note that exact repeats violate (NI).
- **B2** (§5 R1; REV:94–98). T4 Prop. 9's model violates (NF) as well as (NI): keeps select the incumbent error, shown in simulation as E[η₂] going from 0 to −0.30. Option (ii) takes the loop outside Prop. 10(a′) entirely. Correct "unless e is known".
- **B3** (§5 R3; REV:100). The claim that campaign sums are "valid under (NF)" is wrong for Prop. 8's sum. Counterexample from 10(c): the actual gain is −1.067, while the formula gives ≥ 0. Restrict to (NF) + (NI); Cor. 7a needs (NF) plus an execution rule that ignores past keeps.

**Minor:**
- 1a: m_n is defined only on {a_n = 1}.
- 1b: the ⟺ fails on {H_n = 0} when t* < 0, and is undefined at τ = 0.
- 1c: bit-exact and continuous-metric scope of the closed form.
- 1d: "(A1)–(A2) relative to O_n" is a new, policy-dependent assumption.
- 1e: a.s. phrasing.
- 1f: execution must reveal only H_n, or Y_n must be extended.
- Step 1: U must contain all control-plane randomness.
- 2a: non-interaction mis-cited to T2 §1.
- 3: rewording of the (NI) parenthetical.
- 4a–4e: optimality gap, MC standard errors, fixed proposals and non-interaction, the same-key reading, the script path.
- 10(b): the (NI) phrasing.
- R1: the "exactly the kind" overstatement and the fixed-seed correlation remark.
- R4: wording, and trials vs runs.
- R6: Bayes qualifier.
- 6a–6e: wording.

**Verified without findings:**
- Step 1's conditional independence (given that U contains all control-plane randomness).
- The Step 2 bound for randomized policies.
- Step 3's policy-invariance and Part 3 under (NF) + (NI).
- All closed forms in 10(c), the slope φ(0)(1 − 1/√(1+κ²)) = 0.116847 at κ = 1, and the table (script output byte-identical on rerun).
- The 10(b) number 1.60955.
- R2, R5.

Check scripts (mine): `/tmp/claude-0/-home-claude/15a7f69d-b6ad-5b83-af4f-c543b1341863/scratchpad/chk.py` (quadrature, MC standard errors, slope, intercept, R1 simulation of the (NF) violation). The R3 counterexample was computed inline with the same formulas.

## Re-review of revision 2

**Verdict: ACCEPTED, for the author's proof check only.** This is not author approval, manuscript adoption or authorisation of any protocol change.
- All three blocking findings are fixed correctly and completely.
- Every minor finding is fixed or explicitly deferred.
- I found no new mathematical error.
- Five small wording points remain (N1–N5 below). None is blocking, and none changes a result.

The `REV:line` citations below refer to revision 2 of `/mnt/user-data/outputs/t4/T4_PROP10_REVISION_20261028.md`.

### Script rerun

- `python3 -I ex10c.py` reproduces `ex10c_output.txt` byte for byte.
- The table (REV:149–154) matches the output: closed forms, MC mean ± s.e., and the common-random-numbers (CRN) loss.
- The new always-execute closed form (αφ(0) − g) + (βφ(0) − g) is correct. At β = 2 it gives 0.1968, which I checked by hand.
- The CRN differences are computed on the same θ draws, so the reported s.e. of the loss and of the screening gain are valid.
- The R3 check at β = 10 gives −1.0674 for the actual gain and +0.1011 for the formula, the same as my earlier computation.

### Blocking findings

- **B1 — resolved.**
  - REV:42 states that duplicate and no-op status depend on past decisions.
  - (NF-c) (REV:89) adds the assumption that removes this dependence, with my two alternatives, the excluded "re-proposed after skip" pattern and the C3-pilot prevalence.
  - REV:93 records that kept exact repeats violate (NI).
  - The §6 (NF-c) row adds an observable count.
  - Prop. 8′ correctly needs none of this (REV:42).
- **B2 — resolved.**
  - R1 (REV:171–182) now states that (NI), (NF) and (A2) all fail, with the covariance and the simulation figures.
  - The "known e" case is corrected to the debiased comparison Δ̂_n + (1 − ϱ_n)e.
  - Option (i) is marked as needed for (NF), including its run cost.
  - Option (ii) is placed entirely outside 10(a′), and "analogous" replaces "exactly the kind".
  - The fixed-seed correlation remark is added, and the §6 last row adds the negative post-keep residual mean.
- **B3 — resolved.**
  - R3 (REV:184–189) restricts Prop. 8's sum to (NF) + (NI) and cites the 10(c) counterexample, which the script now prints.
  - Corollary 7a is stated under (NF) with both conditions it needs: an execution rule that ignores past keeps, and (A1)–(A2) relative to O_n.
  - R4 (REV:190) now says the scaling has "no guaranteed sign relation" to the campaign gain.

### Minor findings

Every item in my list is mapped in §8. I checked each one at its new location.

| Finding | Location | Check |
|---|---|---|
| 1a: m_n defined only on {a_n = 1} | REV:57–61, 68, 76 | m_n is now defined on the whole space; 8′.1 is an a.s. inequality with equality at a_n·1{m_n > 0}; the proof is correct. |
| 1b–1d: Gaussian closed-form scope | REV:63 | τ_n > 0, bit-exact node, continuous law on I_nᶜ; the ⟺ is restricted to {H_n ≠ 0}; the condition relative to O_n is labelled a new assumption; non-bit-exact nodes and lattice metrics are excluded. Correct: τ_n > 0 makes H_n continuous on I_nᶜ for any σ_n ≥ 0, and at σ_n = 0 the threshold is t* = 0 with m_n = H_n. |
| 1e: a.s. phrasing | REV:67 | done |
| 1f: execution reveals only H_n | REV:40 | done |
| U must contain all control-plane randomness | REV:44 | done |
| 2a, 2b: non-interaction and noise | (NF-b), REV:88 | done |
| §3: (NI) parenthetical | REV:91–92 | done |
| 4a–4d | REV:132–167 | Exact optimality gap; MC s.e. with CRN; fixed proposals and non-interacting edits stated; same-key reading now stylized, with its three conditions. |
| 10(b) | REV:128 | done |
| R4: trials vs runs | REV:190; §7 item 3 | deferred to an explicit author decision |
| R6 | REV:195–198 | done |
| 6a–6e | REV:27, 84, 123, 124; §6 rows 1–2, 5 | done |
| 4e: script path | REV:156 | deferred to commit (see N5) |

**Edge case in the rewritten 8′.4 (REV:73).** I checked it. "Keep iff μ_n > 0" and V*_n = (1 − π_n)μ_n⁺ hold even when H_n does not separate I_n from I_nᶜ: then m_n = μ_n·P(I_nᶜ | O_n, H_n), which has the sign of μ_n and has mean (1 − π_n)μ_n. So the separation sentence is a sufficient remark, not a needed condition. It is correct as written.

### New-error check on rewritten parts

- **Prop. 10(a′) proof (REV:100–119).** Correct. Step 1 is unchanged in substance. Step 2 now cites 8′.1–8′.2, which is valid because 8′.1 is the general a.s. bound. Step 3 is correct. The Doob–Dynkin sentence about versions is correct.
- **10(c) (REV:130–167).** Correct, including the asymptotic expansion with intercept αφ(0) − g/2. That expansion holds once βφ(0)/√(1+κ²) > g, which is true for large β.
- **R6.** The Jensen argument compares realised values correctly: under (NF), each myopic controller's value is Σ E[(V*_n − g)⁺] on its own information.
- **§6 table.** Consistent with the text.

### Remaining non-blocking wording points

- **N1 (REV:63).** "Under (NI) the relevant σ-field is σ(x_{1:n}) for every policy (Proposition 10(a′).1)". Part 1 uses U ⊥ W, which is part of (NF), and the policy-invariance of the conditional law also comes from (NF).
  *Fix:* "Under (NF) and (NI)".
- **N2 (REV:86).** "Concretely, (NF) requires all of the following". Read literally, (NF-a)–(NF-c) are not strictly necessary: a law-invariant but degenerate dependence on decisions is possible. Together with U ⊥ W, they are the operative sufficient components.
  *Fix:* "(NF) holds if (NF-a)–(NF-c) hold and U ⊥ W; these are also the ways it typically fails."
- **N3 (REV:88).** The noise clause in (NF-b) should cover the **joint** law of (η_m)_m and its relation to the other components of W, not only the law of each η_n.
  *Fix:* "the joint law of the comparison noises does not depend on the incumbent's identity or history".
- **N4 (REV:89).** The alternative "no earlier effective configuration is re-proposed within the horizon" must hold **under every policy**. Because the incumbent is itself an earlier effective configuration, the alternative also excludes incumbent-dependent no-ops (π_n = 0).
  *Fix:* add "under every policy (this also rules out no-ops that depend on the incumbent)". This imprecision came from my own suggested fix.
- **N5 (REV:5, 156).** Two repository paths are not where the files are now:
  - the review is cited as `docs/r1/reviews/T4_PROP10_REVISION_REVIEW_20261028.md` but is currently `/mnt/user-data/outputs/t4/REVIEW_T4_PROP10_REVISION_20261028.md`;
  - the script is cited under `docs/r1/proposals/…` but is currently in `/mnt/user-data/outputs/t4/t4_prop10_revision_20261028/`.

  *Fix:* make these consistent at commit time; §8 already defers the script path.

The open author decisions in §7 (R1 noise model, R4 trials vs runs, which §6 tests to adopt) remain open. They are correctly labelled as not resolved by the proposal.
