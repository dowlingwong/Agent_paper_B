AI-assisted (Claude, subagent, 23 Nov 2026). The AI proof check under PLAN row R1-PROOF-POLICY, for the appendix statements not yet through it.

# AI proof check (a): appendix statements of Paper B

This is check (a) of R1-PROOF-POLICY. It is not an author check. The coordinating chat's spot check (b) is separate; `AI_PROOF_CHECK_APPENDIX_CHECKLIST_20261123.md` lists what it should re-derive. Nothing here changes a theory note, the manuscript, a PLAN row or an existing packet.

**Texts checked.**
- Manuscript: `papers/r1/sections/appendix.tex` and `theory.tex` at `mac-manuscript-20261122` @ `5db543bb` (read with `git show`). Line numbers: A:n (appendix.tex), T:n (theory.tex). The statements are the ones the appendix status note (A:202) lists as "not yet through either check".
- Sources, at `79f6442f` (this branch's base): `../T2_DERIVATIONS.md` (T2:n), `../T4_FEEDBACK_PROPOSER.md` (T4:n), `../../proposals/T4_PROP10_REVISION_20261028.md` revision 3 (REV:n).
- Also read: packets P02–P05 of this folder with `check_t2_p6.py` and its output, `../T_AUDIT_20261027.md`, `../../proposals/THEORY_CORRECTIONS_20261027.md`, `ex10c.py` and its output, the first check `AI_PROOF_CHECK_20261123.md` and `SPOT_CHECK_COORDINATOR_20261123.md`, and PLAN rows R1-PROOF-POLICY, R1-T4-PROOF-CHECK, R1-THEORY-RHO, R1-A1-VERIFY on `author-minsub-20261122` (read with `git show`).
- Author-checked sources (REV 8′.4, 10(c), and the 10(c) example behind `prop:failures`(b)) were not re-litigated; their restatements and numbers in the manuscript were checked. REV R3 and R6 are remarks that R1-T4-PROOF-CHECK did not approve as statements, so they were checked in full.

**Method.** As in the first check. Each statement is restated with every assumption it needs. Each step is classified as **proven**, **proven with an added assumption** (named), **gap** or **false** (with a counterexample). Evidence is *symbolic* (SymPy; printed difference 0), *argument*, or *numeric* (fixed seeds; evidence, not proof). Evidence is cited as `out:L (label)`, line L of `ai_proof_check_appendix_20261123_output.txt` (81 lines), produced by `ai_proof_check_appendix_20261123.py` (seed base 20261125; byte-reproducible, checked by a second run; about 20 s). Every number below comes from that output or from a cited file. The script imports no code from the earlier check scripts.

**Readiness** is given for the manuscript wording and for the source note. Both must agree before a statement enters the main text, so the overall verdict is the weaker of the two.

## Summary

| # | Statement | Manuscript wording | Source note | Most important point |
|---|---|---|---|---|
| 1 | `prop:app-voi` (T2 Prop. 2) | ready as written | after changes | The manuscript is correct and already disclaims diminishing returns. T2 still says "increasing in r, with diminishing returns", which is **false** (audit; attainable counterexample out:32, out:34). **New:** q_r² = c²/(w + s²/r) is increasing and concave in r under **both** split policies (P02 had fixed-policy concavity as observation only). |
| 2 | `prop:app-split` (T2 Prop. 3) | after changes | after changes | True. The manuscript does not say what "re-draws only the training seed" observes; it should state the two replicate models. T2's continuity step and its vary step are **gaps** (audit), closed by the explicit limits (out:10–12). |
| 3 | `prop:app-record` (T2 Prop. 4) and its Scope | after changes | after changes | **New, false as worded:** the hypothesis "centred bivariate normal with common variance σ² … given the history" fails in exactly the cases the Scope paragraph says it holds (fresh errors after keeps; a kept record in the kernel model). After one null keep with ϱ = 0, e has mean 0.5637σ and variance 0.6819σ² (out:48). What holds, and what the formula needs, is the kernel ε \| (e, history) ∼ N(ϱe, σ²(1 − ϱ²)), as in Corollary `cor:bias-kernel`. State it that way. |
| 4 | `prop:app-verify` (T2 Prop. 5) | ready as written | after changes | The manuscript is correct. T2 keeps "a fixed budget is better spent on fresh proposals", a **gap** (audit). **New:** sup over τ of the maximal value is φ(0)σ_d√(r/(r+1)) (vary; out:17, out:56), and R1-A1-VERIFY's inequality at r = 2 follows from this proposition alone: VoI ≤ √v φ(0) < φ(0)σ_d < 0.4σ_d. |
| 5 | `prop:app-rules` (T4 Cor. 8a) | after changes | after changes | **New, false:** (ii) "its value is −g < 0 for every g > 0" holds only under a keep rule that discards the duplicate. Under the Bayes keep rule of `prop:onestep`(i) a run that reveals nothing is worth E[Δ_n \| O_n]⁺ − g, which can be positive: +0.35 at g = 0.1 in a simple example (out:59). (iii) needs every earlier keep to be a default-rule keep (out:60–61). |
| 6 | Edge cases of `prop:onestep` (A:270) | after changes | author-checked (REV 8′.4); consistent | **New:** the restatement drops two qualifiers of the source. The separation "iff" needs no-ops observed exactly, and "keeps every proposal" needs τ_n = 0. Without them both sentences are false (out:65). |
| 7 | "Summed gains need both conditions" (A:292–293) | ready as written | REV R3; consistent | 2.3209, 3.3884, −1.0674 and +0.1011 all check (out:20, out:67–68). |
| 8 | "Bias of offline evaluation" (A:295–296) | ready as written | REV R6; consistent | Proven by Jensen's inequality applied twice. In the paper's own example the offline evaluation of the Bayes one-step rule is optimistic by +1.4235 (closed form; out:70). Learned forecasters give both signs (out:72–73). |
| 9 | Information example (`prop:failures`(b), A:303–308, T:114–119) and Table `tab:ex-info` | after one change | author-checked (REV 10(c)); consistent | All 12 table values, both macros and the asymptotics check (out:75–81, out:21–24). T:117 "grows linearly in β with slope ≈ 0.117" is true only asymptotically: the slope rises from 0.1046 at β = 2 to 0.1168 (out:79). |

**Ratings of gap or false.**
- In the manuscript: the Scope sentences of item 3, (ii) of item 5, and two sentences of item 6 are false as worded (all new). Each has a one-sentence fix.
- In the source notes: T2 Prop. 2's diminishing returns is false and T2 Prop. 4(b)'s "expected maximum of n draws" is false as worded (both known from the audit and P04). T2 Props. 3 and 5 have gaps (known from the audit). T4 Cor. 8a(ii) is false as item 5 says (new).
- After the proposed changes, no step of any of the nine items is rated a gap or false.

---

## 1. `prop:app-voi`: value of verification (A:216–220; T2:37–51)

### 1.1 Signable statement

Let Δ ∼ N(μ, τ²), H = Δ + η with η ∼ N(0, σ_d²) independent of Δ. Let D̄ be the mean of r ≥ 1 paired comparisons D_i = L + ξ_i, where the fresh errors ξ_i are i.i.d., independent of (Δ, η), and (Δ, H, L) is jointly Gaussian (vary: L = Δ; fixed: L = Δ + e_s). Write m = E[Δ | H], v = Var(Δ | H), q² = Var(E[Δ | H, D̄] | H), and VoI := E[max(E[Δ | H, D̄], 0) | H] − max(m, 0), the gain from deciding with D̄ rather than without it, by the Bayes rule in both cases. Then, almost surely:
- VoI = qψ(|m|/q) if q > 0, and VoI = 0 if q = 0. q does not depend on H.
- For q > 0, VoI is strictly decreasing in |m| and strictly increasing in q.
- q_r² = c²/(w + s²/r), with c = Cov(Δ, L | H), w = Var(L | H) and s² the variance of one ξ_i. So q_r² is increasing and concave in r.
- For m ≠ 0, VoI is convex in q, and its increments in r can increase. At m = 0, VoI = qφ(0) is concave in r.
- The value of any other response measurable in (H, D̄) is at most VoI. A fixed response can be worth less than not verifying at all.

### 1.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Given H, M′ = E[Δ \| H, D̄] ∼ N(m, q²), with q² non-random | **proven** (joint Gaussianity; tower property) | argument; out:26–29 (AN1.1: q² equals Cov²/Var to 7e-18) |
| 2 | E[max(M′, 0)] − max(m, 0) = qψ(\|m\|/q); 0 at q = 0 | **proven** | symbolic out:4–5 (AS1.1); numeric out:26–29 (exact conditional sampling, 4 × 10⁶ draws, four sets, both policies: within 1 s.e.), out:30–31 (end-to-end joint simulation: within 1.3 s.e.) |
| 3 | decreasing in \|m\|, increasing in q (A:217) | **proven**: ψ′ = −Φ(−z) < 0 and ∂(qψ(x/q))/∂q = φ(x/q) > 0 | symbolic out:6 (AS1.2) |
| 4 | "q_r² is concave in r" (A:220) | **proven for both policies (new)**: q_r² = c²r/(wr + s²), with d²/dr² = −2c²s²w/(wr + s²)³ ≤ 0. Vary and fixed are both of this form. | symbolic out:7–9 (AS1.3–AS1.5); numeric out:36 (AN1.4: 0 of 4,000 set-policy pairs non-concave; generic conditioning agrees with the closed forms to 7e-10) |
| 5 | "the value is convex in q for m ≠ 0, and the increments of the value can increase with r" (A:220) | **proven**: ∂²VoI/∂q² = (m²/q³)φ(m/q) > 0. Example (attainable, P02 §4): τ² = 2, σ_t² = σ_s² = 0.5, μ = 0, H = 4.5 (m = 3) | symbolic out:6; numeric out:32 (vary increments 6.88e-8, 3.937e-7, 7.509e-7, 9.615e-7), out:34 (fixed, also increasing); at m = 0 the increments decrease (out:33, out:35) |
| 6 | "A fixed response rule, such as keeping when D̄ > 0, can be worth less" (A:220) | **proven**: the Bayes response maximises over (H, D̄)-measurable rules (pointwise argument as in `prop:onestep`(i)). Example: μ = 0, τ = σ_d = 1, r = 1, H = 3. Relative to the Bayes decision on H alone, the frozen response is worth −0.08857 (worse than not verifying), and the Bayes response +0.00001. | numeric out:37–38 (AN1.5) |
| 7 | Source T2:46 "increasing in r, with diminishing returns" | "increasing in r" is **proven** (steps 3–4; strict when c ≠ 0, s > 0). "with diminishing returns" is **false**: counterexample step 5. The proof sentence "That concavity is the diminishing-returns claim" (T2:50) does not follow. Audit; P02 §4 gave attainable parameters. | out:32, out:34 |
| 8 | Source T2:44 "maximal where m = 0 (i.e. at Δ̂ = t\*)" | **proven** with τ > 0 (m = 0 iff Δ̂ = t\*). The manuscript does not state it. | step 3 |

### 1.3 Proposed changes (not applied)

*Theory note (required for agreement):*
1. T2:39, before "Write m": insert "Assume Δ, e_t, e_s and the replicate errors are mutually independent Gaussians (under `"fixed"`, e_s is reused), and r ≥ 1 is an integer."
2. T2:41, after the display: add "for s̃ > 0; VoI_r := 0 if s̃ = 0."
3. T2:46: "increasing in r, with diminishing returns." → "increasing in r. Diminishing returns hold at m = 0, where VoI_r = s̃φ(0), but not in general: for m ≠ 0 the increments in r can increase."
4. T2:50: replace "Under "vary", Var(Δ | Δ̂, D̄) = 1/(a + r b) with a = 1/v and b = 1/σ_d², so s̃² = v − 1/(a + r b) is increasing and concave in r. That concavity is the diminishing-returns claim; the bound s̃ ≤ √v alone does not prove it (corrected after the L14 review)." with "Under either policy D̄ = L + ξ̄, with ξ̄ fresh of variance s²/r (vary: L = Δ, s² = σ_d²; fixed: L = Δ + e_s, s² = σ_t²). So s̃² = c²/(w + s²/r), with c = Cov(Δ, L | Δ̂) and w = Var(L | Δ̂), is increasing and concave in r. That concavity does not carry over to VoI_r, which is convex in s̃ for m ≠ 0 (d²VoI/ds̃² = (m²/s̃³)φ(m/s̃)). With τ² = 2, σ_d² = 1, μ₀ = 0 and Δ̂ = 4.5 (m = 3), the vary increments over r = 1, …, 5 are 6.88e-8, 3.94e-7, 7.51e-7 and 9.62e-7 (`AI_PROOF_CHECK_APPENDIX_20261123.md` §1)."

*Manuscript (optional; the statement is correct as written):*
5. A:217: "The value of observing $\bar D$ before a Bayes keep decision is" → "The value of observing $\bar D$ before the keep decision, $\mathbb{E}[\max(\mathbb{E}[\Delta\mid H,\bar D],0)\mid H]-\max(m,0)$ with the Bayes decision in both cases, is".
6. A:217: "It decreases in $|m|$ and increases in $q$." → "For $q>0$ it decreases in $|m|$ and increases in $q$."
7. A:220: "The posterior quantity $q_r^2$ is concave in $r$" → "The preposterior variance $q_r^2$ is increasing and concave in $r$".

**Readiness:** manuscript **ready as written** (5–7 optional); source note **ready after the proposed changes** 1–4. Overall: ready after changes 1–4 to T2.

---

## 2. `prop:app-split`: which noise verification removes (A:222–224; T2:55–61)

### 2.1 Signable statement

Let η = e_t + e_s, with e_t ∼ N(0, σ_t²) and e_s ∼ N(0, σ_s²) independent of each other and of Δ ∼ N(μ, τ²). Assume τ > 0 and σ_s > 0, and fix μ, r and H. *Fixed policy* (only the training seed is re-drawn): D_i = Δ + e_s + ξ_i with ξ_i ∼ N(0, σ_t²). *Vary policy* (both seeds are re-drawn): D_i = Δ + ξ_i with ξ_i ∼ N(0, σ_t² + σ_s²). The ξ_i are i.i.d. and independent of everything else. Values are those of §1. Then:
- under the fixed policy, VoI ≤ q_f φ(0) with q_f² = τ⁴u/((A + u)²(1 + 1/r − u/(A + u))), where A = τ² + σ_s² and u = σ_t². Hence VoI → 0 as σ_t → 0, uniformly in H;
- under the vary policy, VoI → q₀ψ(|m₀|/q₀) > 0 as σ_t → 0, with v₀ = τ²σ_s²/A, q₀² = v₀²/(v₀ + σ_s²/r) and m₀ = μ + τ²(H − μ)/A. The limit is positive for each H and tends to 0 as |H| → ∞, so it is pointwise, not uniform.

### 2.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | fixed: D̄ − H = ξ̄ − e_t, variance σ_t²(1 + 1/r) | **proven** | argument |
| 2 | "The Gaussian posterior moves continuously with the covariance, so s̃ → 0" (T2:59) | **gap** (singular limit; audit). **Closed** by the explicit q_f² above: q_f² = O(σ_t²), with limit q_f²/σ_t² → τ⁴r/(A²(r + 1)) | symbolic out:10–11 (AS2.1–AS2.2); numeric out:40–44 (q²/σ_t² → 0.273067 = limit; max VoI falls linearly in σ_t) |
| 3 | VoI ≤ qφ(0) → 0 | **proven** (ψ ≤ φ(0)) | symbolic out:16 |
| 4 | vary: "s̃ > 0, and VoI > 0 at every Δ̂" (T2:61) | **gap as a proof of the limit**: positivity at each σ_t does not give a positive limit. **Closed** by the explicit limit q₀ > 0 and finite m₀ | symbolic out:12 (AS2.3); numeric out:40–44 (vary VoI at H = 0 stays at 0.0959–0.0961) |
| 5 | "positive limit for each fixed H … pointwise, not uniform" (A:223) | **proven** | numeric out:45 (limit VoI at H = 0, 2, 5, 10: 0.0959, 5.35e-5, 1.664e-19, 1.602e-70) |
| 6 | the two replicate models | **proven with an added assumption**: the manuscript leaves them implicit. T2 §1 (T2:14–15) defines them. | — |

### 2.3 Proposed changes (not applied)

*Manuscript (required):*
1. A:223: "Let the comparison noise have a training-seed part with variance $\sigma_t^2$ and a split-seed part with variance $\sigma_s^2$, and let $\tau>0$ and $\sigma_s>0$. If verification re-draws only the training seed, its value tends to zero as $\sigma_t\to0$. If it re-draws both seeds, its value has a positive limit for each fixed $H$." → "Let $\eta=e_t+e_s$ with independent $e_t\sim\mathcal{N}(0,\sigma_t^2)$ (training seed) and $e_s\sim\mathcal{N}(0,\sigma_s^2)$ (split seed), let $\tau>0$ and $\sigma_s>0$, and fix $\mu$, $r$ and $H$. If verification re-draws only the training seed ($D_i=\Delta+e_s+\xi_i$ with $\xi_i\sim\mathcal{N}(0,\sigma_t^2)$), its value in Proposition~\ref{prop:app-voi} tends to zero as $\sigma_t\to0$, uniformly in $H$. If it re-draws both seeds ($D_i=\Delta+\xi_i$ with $\xi_i\sim\mathcal{N}(0,\sigma_t^2+\sigma_s^2)$), its value has a positive limit for each fixed $H$."

*Theory note (required):*
2. T2:57: "stays bounded away from zero as σ_t → 0 whenever τ, σ_s > 0." → "has a positive limit as σ_t → 0 for each fixed Δ̂, whenever τ, σ_s > 0. The limit is pointwise in Δ̂, not uniform: it tends to 0 as |Δ̂| → ∞. (μ, τ, σ_s and r fixed; the independence assumptions of §3.)"
3. T2:59: replace "The pair (Δ̂, D̄) is then a.s. a function of Δ̂ alone in the limit. The Gaussian posterior moves continuously with the covariance, so s̃ → 0" with "With A = τ² + σ_s² and u = σ_t², Cov(Δ, D̄ | Δ̂) = τ²u/(A + u) and Var(D̄ | Δ̂) = u(1 + 1/r − u/(A + u)), so s̃² = τ⁴u/((A + u)²(1 + 1/r − u/(A + u))) = O(u). (If A = 0, Δ is constant and VoI = 0.) Hence s̃ → 0".
4. T2:61: "So s̃ > 0, and VoI > 0 at every Δ̂." → "As σ_t → 0, v → v₀ = τ²σ_s²/A > 0 and s̃² → v₀²/(v₀ + σ_s²/r) > 0, while m stays finite at fixed Δ̂. So VoI tends to a positive value."

**Readiness:** manuscript **ready after the proposed change** 1; source **ready after** 2–4.

---

## 3. `prop:app-record`: acceptance against a biased record, and its Scope (A:226–237; T2:65–94)

### 3.1 Signable statement

Let e be the incumbent's recorded error and ε a candidate's, so that a proposal with fixed true increment δ has comparison δ + ε − e. The default rule keeps it iff δ + ε − e > 0.
- (a) Suppose that, given the history and e, **ε ∼ N(ϱe, σ²(1 − ϱ²))**, with σ > 0 and ϱ ∈ (−1, 1). This holds, for example, if (e, ε) is centred bivariate normal with common variance σ² and correlation ϱ given the history. Then P(keep | e, history) = Φ((δ − (1 − ϱ)e)/(σ√(1 − ϱ²))), and this is strictly decreasing in e.
- (b) Suppose every trial of a stretch is a null proposal (Δ = 0, not a no-op) that is executed and judged by the default rule. Suppose its error is a fresh N(0, σ²) draw, independent of everything earlier, and the initial record e₀ is finite. Then the record's error e_n = max(e₀, ε₁, …, ε_n) → ∞ almost surely. For a later proposal with fixed δ and a fresh N(0, σ²) error, P(keep | e_n) = Φ((δ − e_n)/σ) → 0 almost surely.
- *Scope.* The kernel in (a) must hold given the actual history. It holds for fresh errors (ϱ = 0) after any number of keeps. For ϱ > 0 it holds at an unselected record about which the history carries no further information. For a kept record it holds only in a model that imposes it at every step (the kernel model, T3 `crn`, T5 `record`). It does not hold for a kept record under a shared-component model. **In none of the post-keep cases is the joint law of (e, ε) given the history centred with common variance σ².**

### 3.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | the keep-probability formula | **proven with an added assumption**: the comparison δ + ε − e and the strict default rule. The manuscript states neither; T2 does (T2:69, T2:86). | symbolic out:13 (AS3.1); numeric out:47 (unselected record: within simulation error at e ≈ −1, 0, 1, 2) |
| 2 | strictly decreasing in e | **proven** (σ > 0, −1 < ϱ < 1) | symbolic out:13 |
| 3 | hypothesis "centred bivariate normal with common variance σ² … given the history" (A:227) | **sufficient, but not what the scope needs.** The formula uses only the conditional kernel. | argument; symbolic out:14 (AS3.2: with e ∼ N(m_e, v) given the history and ε = ϱe + σ_cξ, the regression coefficient is ϱ and the residual variance is σ²(1 − ϱ²) for every (m_e, v); Var ε − σ² = ϱ²(v − σ²)) |
| 4 | (b): record → ∞ a.s.; conditional keep probability → 0 | **proven** with the record as max(e₀, n fresh draws) and a later proposal whose error is fresh (or follows the kernel with ϱ < 1) | argument; numeric out:53 (trend only: mean P(keep \| e_n) 0.234, 0.092, 0.054, 0.014 after 5, 20, 40, 200 null trials) |
| 5 | Scope, sentence 1: "must hold given the actual history, not only given e; a selected incumbent error need not keep it" | **proven** | out:48–49 |
| 6 | Scope, sentence 2: "It [the bivariate normal law of the first part] holds for fresh errors (ϱ = 0) after any number of keeps" | **false as worded (new).** After one null keep from an unselected record, e has mean σ/√π = 0.5642σ and variance σ²(1 − 1/π) = 0.6817σ² given the keep (simulated 0.5637, 0.6819). Given the recorded comparison h it is N(h/2, σ²/2). So the centred common-variance law fails. The **kernel** still holds: a fresh candidate's regression slope is −0.0002 and its residual variance 0.9989, and P(keep \| e ≈ 1) = 0.2142 (s.e. 0.0016) against the formula's 0.2119. | symbolic out:15 (AS3.3); numeric out:48, out:50, out:51 |
| 7 | Scope, sentence 2 continued: "for ϱ > 0 at an unselected record about which the history carries no further information" | **proven** | argument |
| 8 | Scope, sentence 3: "For a record that was kept it holds only in a model that imposes it at every step" | **false as worded for the joint law (new); true for the kernel.** Kernel model, ϱ = 0.6, after one null keep: mean e = +0.3573, Var e = 0.8729, Corr(e, ε_next) = 0.5733 ≠ ϱ. The regression slope is 0.5991 and the residual variance 0.6398 (kernel: 0.6, 0.64). P(keep \| e ≈ 1) is 0.4038 (s.e. 0.0021) against 0.4013. Given the ledger, e is N(m_n, v_n) with m_n ≠ 0 and v_n < σ² (Lemma `lem:app-kalman`). | numeric out:49; symbolic out:14 |
| 9 | "with an error component shared by the campaign it does not" | **proven** (P04 §4: 0.5322 against 0.6306) | file `check_t2_p6_output.txt`, section P04 |
| 10 | Source (b) T2:81–82: "e_n is the running maximum of n i.i.d. N(0, σ²) draws … E[e_n] equals the expected maximum of n draws, ≈ σ√(2 ln n)" | **false as worded** (indexing; known from the audit and P04): the record includes e₀. E max of 10 draws is 1.539 and of 11 draws 1.586, against √(2 ln 10) = 2.146. "≈" holds only as a ratio tending to 1. | numeric out:52 (AN3.5) |
| 11 | Source T2:83: "P(keep δ at step n) → 0 almost surely" | **proven** only as the conditional probability P(keep \| e_n). Audit; the manuscript already says "conditional". | argument |

### 3.3 Proposed changes (not applied)

*Manuscript (required):*
1. A:227–230: "Let the incumbent's recorded error $e$ and a candidate's error be centred bivariate normal with common variance $\sigma^2>0$ and correlation $\varrho\in(-1,1)$, given the history. For a proposal with fixed true increment $\delta$," → "Let $e$ be the incumbent's recorded error and $\varepsilon$ a candidate's, so that a proposal with fixed true increment $\delta$ has comparison $\delta+\varepsilon-e$, and the default rule keeps it when this is positive. Suppose that, given the history and $e$, $\varepsilon\sim\mathcal{N}(\varrho e,\sigma^2(1-\varrho^2))$ with $\sigma>0$ and $\varrho\in(-1,1)$; this holds, for example, when $(e,\varepsilon)$ is centred bivariate normal with common variance $\sigma^2$ and correlation $\varrho$ given the history. Then".
2. A:231: "the conditional keep probability of a later proposal with fixed $\delta$ tends to zero." → "the conditional keep probability of a later proposal with fixed $\delta$ and a fresh $\mathcal{N}(0,\sigma^2)$ error tends to zero."
3. A:237: "The bivariate normal law of the first part must hold given the actual history, not only given $e$; a selected incumbent error need not keep it." → "The conditional law of the first part, $\varepsilon\mid e\sim\mathcal{N}(\varrho e,\sigma^2(1-\varrho^2))$, must hold given the actual history, not only given $e$; a selected incumbent error need not keep it." After "with an error component shared by the campaign it does not." add "After a keep, the joint law of $(e,\varepsilon)$ given the history is in general neither centred nor of common variance $\sigma^2$, even where the kernel holds."

*Theory note (required for agreement; P04 §5 item 4, not yet applied):*
4. T2:81: "e_n is the running maximum of n i.i.d. N(0, σ²) draws" → "e_n is the running maximum of the initial record e₀ and n i.i.d. N(0, σ²) draws".
5. T2:82: "E[e_n] equals the expected maximum of n draws, ≈ σ√(2 ln n)" → "E[e_n] ∼ σ√(2 ln n) as n → ∞ (a ratio tending to 1; at n = 10 and 40 the expected maximum of n + 1 standard draws is 1.586 and 2.171, against √(2 ln n) = 2.146 and 2.716)".
6. T2:83: "P(keep δ at step n) → 0 almost surely" → "P(keep δ at step n | e_n) = Φ((δ − e_n)/σ) → 0 almost surely".

**Readiness:** manuscript **ready after the proposed changes** 1–3; source **ready after** 4–6. T2's own Scope of (a) (T2:79) already speaks of the conditional law and is consistent with change 3.

---

## 4. `prop:app-verify`: verification under a run price (A:239–243; T2:96–116)

### 4.1 Signable statement

In the model of §1, VoI ≤ qφ(0) ≤ √v φ(0), where v = Var(Δ | H). If each run has an externally fixed additive price g, then verification with r paired comparisons (2r runs), followed by the Bayes response, has net value VoI − 2rg. It is positive only if VoI > 2rg, and never when 2rg ≥ √v φ(0). This is a one-step comparison, not a hard-budget optimum. *Addition (new):* under the vary policy, sup over τ of max_H VoI = φ(0)σ_d√(r/(r + 1)), approached as τ → ∞. Under the fixed policy the bound is the same with σ_t in place of σ_d.

### 4.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | VoI ≤ qφ(0) | **proven**: ψ is decreasing on [0, ∞) with ψ(0) = φ(0) | symbolic out:6, out:16 |
| 2 | q ≤ √v | **proven**: v − q² = Var(Δ \| H, D̄) ≥ 0; in the form of §1, v − c²/(w + s²/r) ≥ (vw − c²)/(w + s²/r) ≥ 0 | symbolic out:16 (AS4.1); numeric out:55 (820,000 cases: 0 violations of either inequality) |
| 3 | "never when 2rg ≥ √v φ(0)" | **proven** (VoI ≤ √v φ(0) ≤ 2rg, so VoI never exceeds 2rg) | — |
| 4 | Remark: not a hard-budget optimum; not "better spent on fresh proposals" | **proven** as a disclaimer (audit) | — |
| 5 | Source T2:104 "a fixed budget is better spent on fresh proposals" | **gap** (does not follow; audit, P05). Still in T2. | — |
| 6 | Source T2:106–109 table | **not verified**: inputs unstated (P05 §4 reconstructs σ_d = 0.00857). The manuscript does not use it. | — |
| 7 | (new) sup over τ: φ(0)σ_d√(r/(r+1)) (vary), φ(0)σ_t√(r/(r+1)) (fixed) | **proven**: q² = v²/(v + σ_d²/r) is increasing in v and v ↑ σ_d² as τ → ∞. This gives P05's numerical 0.2821, 0.3257, 0.3455 in closed form. | symbolic out:17–19 (AS4.2–AS4.4); numeric out:56 |
| 8 | (new) R1-A1-VERIFY: at g = 0.1σ_node, r = 2 and σ_d ≤ σ_node, the index cannot verify | **proven from this proposition alone**: VoI ≤ √v φ(0) < φ(0)σ_d = 0.39894σ_d < 0.4σ_d ≤ 2rg. At r = 1 it can fire: max VoI > 0.2σ_d in 794 of 4,000 random set-policy pairs | out:57 (AN4.3) |

*Reading note (not a mathematical error).* `problem.tex` says "Verification runs are not priced in [J_g]". The proposition prices them at g, as A1's index does (method.tex:57). One sentence saying that the index prices verification at g, outside J_g, would remove the apparent conflict.

### 4.3 Proposed changes (not applied)

*Manuscript (optional):*
1. A:240: "The value of verification with $r$ paired runs" → "The value of verification with $r$ paired comparisons ($2r$ runs)".

*Theory note (required for agreement):*
2. T2:104: "So whenever 2r · g ≥ √v φ(0), the index never verifies: a fixed budget is better spent on fresh proposals." → "So whenever 2r · g ≥ √v φ(0), the index never verifies. This is a one-step comparison at an externally fixed price g with the Bayes response. It does not show that a hard budget is better spent on fresh proposals: integer remaining budgets, the evolving incumbent, the call cap and the frozen response all change the comparison."
3. *(Optional.)* T2:104, after the first sentence: "Under `"vary"`, sup over τ of the maximal VoI_r is φ(0)σ_d√(r/(r + 1)) (0.282σ_d, 0.326σ_d, 0.345σ_d at r = 1, 2, 3)."

**Readiness:** manuscript **ready as written**; source **ready after** change 2.

---

## 5. `prop:app-rules`: rule-detectable waste (A:258–267; T4:82–87)

### 5.1 Signable statement

Consider a node whose metric is bit-exact at fixed seeds, with the seeds fixed within a campaign.
- (i) If proposal n is a detectable no-op (I_n ∈ O_n), then π_n = 1 and V\*_n = 0. Skipping is optimal for the immediate payoff (`prop:onestep`(ii)) for every g > 0, with a tie at g = 0. Bit-exactness is not needed for (i).
- (ii) If proposal n repeats an earlier evaluated configuration other than the incumbent, a run returns the metric already in the ledger. So H_n is O_n-measurable, m_n = E[Δ_n | O_n], and V\*_n = E[Δ_n | O_n]⁺. Under a keep rule that discards it, executing it is worth −g < 0 for every g > 0.
- (iii) Suppose every keep so far was made by the default (strict) rule and the incumbent changes only by keeps. Then the recorded incumbent value has never decreased, so the duplicate's comparison is ≤ 0 and the default rule discards it. By (ii), executing it is then worth −g.

### 5.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | (i) π_n = 1, V\*_n = 0, skip optimal for g > 0 | **proven**, for the immediate payoff (`prop:onestep`(ii)). Global optimality would also need that executing rather than skipping changes no later law (for example through the displayed ledger line), an (NF)-type condition. | argument (REV 8′.4) |
| 2 | (ii) "a run returns the metric already in the ledger. It reveals nothing" | **proven with an added assumption**: the campaign's runs use the same seeds | argument |
| 3 | (ii) "its value is −g < 0 for every g > 0" | **false in general (new).** By `prop:onestep` itself, executing is worth E[Δ_n \| O_n]⁺ − g under the Bayes keep rule. That is −g only if E[Δ_n \| O_n] ≤ 0. Counterexample: the configuration was discarded earlier by the default rule with recorded comparison h = −0.1, the incumbent is unchanged, and the forecast at trial n is μ = 1, τ = σ = 1. Then E[Δ_n \| O_n] = 0.45 and, at g = 0.1, execute-and-keep earns +0.35 > 0 > −g. **True** under any keep rule that discards the duplicate, in particular the default rule by (iii). | numeric out:59 (AN5.1: 0.4500, simulated 0.4460, s.e. 0.0039) |
| 4 | (iii) record non-decreasing, so a duplicate is never kept | **proven with an added assumption**: every earlier keep was a default-rule keep, with no restoration. With a looser rule the record can fall and duplicates can be kept. | argument (T4:85); numeric out:60 (default rule: 185,305 duplicates, 0 kept, 0 record decreases, max comparison −7.1e-6), out:61 (keep iff comparison > −0.5: 19,528 duplicates kept, 25,865 record decreases) |
| 5 | "A duplicate's true increment is generally not zero, so it does not receive the no-op label." | **proven** (a labelling convention) | — |
| 6 | Source T4:84 "its value is 0 − g < 0 for every g > 0. Skipping is optimal." | **false in general**, as step 3. T4:87 already notes that a threshold rule with t\* < 0 could keep a duplicate on its stale comparison. Cor. 8a also sits under the 18 Oct Proposition 8 (DI), which the revision replaced by 8′. | as step 3 |

`results.tex:78` ("cannot be kept under the default rule … so its run is lost whatever the noise") uses the true, restricted form.

### 5.3 Proposed changes (not applied)

*Manuscript (required):*
1. A:259: "Consider a node whose metric is bit-exact at fixed seeds." → "Consider a node whose metric is bit-exact at fixed seeds, with the seeds fixed within a campaign."
2. A:261: "and skipping is optimal for every $g>0$." → "and skipping is optimal for the immediate payoff (Proposition~\ref{prop:onestep}(ii)) for every $g>0$."
3. A:262: "It reveals nothing, and its value is $-g<0$ for every $g>0$." → "It reveals nothing: $m_n=\mathbb{E}[\Delta_n\mid\mathcal{O}_n]$. Under a keep rule that discards it, executing it is worth $-g<0$ for every $g>0$; under the Bayes keep rule it is worth $\mathbb{E}[\Delta_n\mid\mathcal{O}_n]^+-g$, which can be positive."
4. A:263: "Under the default keep rule the recorded incumbent value never decreases, so such a duplicate can never be kept." → "If every keep so far was made by the default keep rule, the recorded incumbent value has never decreased, so the default rule discards such a duplicate, and by (ii) executing it is worth $-g$."

*Theory note (required for agreement):*
5. T4:83: "skipping is optimal for every g > 0." → "skipping is optimal for the immediate payoff (revision Proposition 8′.2) for every g > 0."
6. T4:84: "a run returns the metric already in the ledger, so it carries no information and its value is 0 − g < 0 for every g > 0. Skipping is optimal." → "a run returns the metric already in the ledger, so it carries no information: m_n = E[Δ_n | F_n] and V\*_n = E[Δ_n | F_n]⁺. Under a keep rule that discards it (under ρ, by (iii)), executing it is worth −g < 0 for every g > 0, and skipping is optimal for the immediate payoff. Under the Bayes keep rule it is worth E[Δ_n | F_n]⁺ − g, which can be positive (`author_packets_20261122/AI_PROOF_CHECK_APPENDIX_20261123.md` §5)."
7. T4:85: "Moreover, under ρ a duplicate can never be kept." → "Moreover, if every keep so far was made by ρ, a duplicate can never be kept by ρ."

**Readiness:** manuscript **ready after the proposed changes** 1–4; source **ready after** 5–7.

---

## 6. Edge cases of `prop:onestep` (A:269–270; source REV:77–82, author-checked)

### 6.1 Signable statement

In the setting of `prop:onestep`:
- If π_n = 1, then V\*_n = 0. Skipping is optimal for the immediate payoff when g > 0, and the two actions tie at g = 0.
- If τ_n = 0 for a non-no-op (known increment μ_n), the rule keeps iff m_n > 0, and V\*_n = (1 − π_n)μ_n⁺. This holds for any noise law.
- **On a node where no-ops are observed exactly** (H_n = 0 on I_n), with 0 < π_n < 1: {H_n = 0} = I_n a.s. iff the comparison value of a non-no-op has no probability mass at zero, given O_n. For τ_n = 0, μ_n ≠ 0 alone is not enough: a lattice noise can have an atom at −μ_n.
- **If, in addition, τ_n = 0**, μ_n > 0 and there is no separation, the rule keeps every executed proposal, no-ops included. Its value is (1 − π_n)μ_n, as with separation.

### 6.2 Steps

| Step | Claim (A:270) | Verdict | Evidence |
|---|---|---|---|
| 1 | π_n = 1 case | **proven** (REV 8′.4) | argument |
| 2 | τ_n = 0 case | **proven** (REV 8′.4 proof: Δ_n ∈ {0, μ_n} has the sign of μ_n) | argument; out:63–64 (value 0.0140 = (1 − π)μ⁺) |
| 3 | "With 0 < π_n < 1, the observation separates … iff the comparison value of a non-no-op has no probability mass at zero" | **false as worded (new); proven with the source's assumption** "on a bit-exact node", which the restatement drops. Counterexample: a no-op observed with noise, τ_n = 1, μ_n = 0.1, π = 0.3, σ = 1. The non-no-op law has no atom, yet P(no-op \| H) is 0.0693, 0.3780 and 0.0522 at H = −3, 0, +3, so there is no separation. | numeric out:65 (AN6.2) |
| 4 | "Without separation and with μ_n > 0, the rule keeps every proposal, no-ops included" | **false as worded (new); proven with τ_n = 0**, which the source states (it is a sub-case of τ_n = 0 at REV:80) and the restatement leaves implicit. Counterexample (same setting, τ_n > 0): at H = −3, m_n = −1.3496, so the rule discards. With τ_n = 0 and a lattice atom at −μ: P(non-no-op \| H = 0) = 0.3182, m_n(0) = +0.00636, every executed proposal is kept, and the value is 0.0140 = (1 − π)μ⁺. | numeric out:63, out:65 |

### 6.3 Proposed changes (not applied)

*Manuscript (required):*
1. A:270: "With $0<\pi_n<1$, the observation separates no-ops from other proposals if and only if the comparison value of a non-no-op has no probability mass at zero; $\mu_n\neq0$ alone is not enough. Without separation and with $\mu_n>0$, the rule keeps every proposal, no-ops included, and the value is unchanged because keeping a no-op gains nothing." → "On a node where no-ops are observed exactly ($H_n=0$ on a no-op) and with $0<\pi_n<1$, the observation separates no-ops from other proposals if and only if the comparison value of a non-no-op has no probability mass at zero; for $\tau_n=0$, $\mu_n\neq0$ alone is not enough. If $\tau_n=0$, $\mu_n>0$ and there is no separation, the rule keeps every executed proposal, no-ops included, and the value is unchanged because keeping a no-op gains nothing."
2. *(Optional.)* A:270: "skipping is optimal for $g>0$" → "skipping is optimal for the immediate payoff for $g>0$".

No change to the source (REV 8′.4 is correct and author-checked).

**Readiness:** manuscript **ready after the proposed change** 1.

---

## 7. "Summed gains need both conditions" (A:292–293; REV:202–207)

### 7.1 Signable statement

Theorem `thm:reduction`(3) needs (NF) and (NI). In the example of `prop:failures`(b), with α = 1, β = 10, κ = 1 and g = 0.5, (NF) holds and (NI) fails. There J(one-step) = 10φ(0)/√2 − 0.5 = 2.32094791774 and J(always execute, Bayes keep) = αφ(0) + βφ(0) − 2g = 3.38836508442, so the screening gain is −1.06741716668. The formula Σ_n(g − V\*_n)⁺ with the one-step rule's V\*_n gives (0.5 − φ(0))⁺ + 0 = 0.101057719599.

### 7.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | Under always-execute, θ is known at trial 2 (H₁ = αθ, no noise), so trial 2 earns βφ(0) − g; trial 1 earns αφ(0) − g | **proven** | argument; matches `ex10c.py` (`always`) |
| 2 | the four numbers | **proven**: 2.3209, 3.3884, −1.0674, +0.1011 are the closed forms rounded to four places. The difference of the two rounded values would be −1.0675; the paper's −1.0674 is the rounded exact difference, which is correct. | symbolic out:20 (AS7.1); numeric out:67 (common random numbers: 2.3228, 3.3885, −1.0657, s.e. 0.0032, 0.0032, 0.0014), out:68 |
| 3 | "Under (NF) alone the screening gain can be negative"; "Without both conditions, campaign gains must be measured" | **proven** (the example; REV R3) | — |

**Proposed change (optional).** A:293: "while the formula evaluated with the one-step values gives $+0.1011$" → "while the formula $\sum_n(g-V^*_n)^+$ evaluated with the one-step rule's $V^*_n$ gives $+0.1011$".

**Readiness: ready as written.**

---

## 8. "Bias of offline evaluation" (A:295–296; REV:215–219)

### 8.1 Signable statement

Assume (NF), and E|Δ_n| < ∞ for every n. A sweep executes every proposal, so its pre-execution information at n is O_n^off = σ(x_{1:n}, H_{<n}, U), up to the sweep's own decisions, which are functions of these. A one-step controller, run online on the same (W, U), has O_n^on ⊆ O_n^off, because its decisions are functions of what it has observed. Let the controller be Bayes with respect to its information: it executes iff V\*_n ≥ g and keeps iff m_n > 0. Then, for every n, E[(V\*_n^off − g)⁺] ≥ E[(V\*_n^on − g)⁺]. So the offline one-step utility, summed with any fixed non-negative weights, is at least the online value. Under (NF) and (NI) the two are equal, path by path. For a non-Bayes (learned) forecaster the sign is not determined, even under (NF) and (NI). Outside (NF) these results do not determine the sign.

### 8.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | O_n^on ⊆ O_n^off on a common realisation; under (NF) both have the law of W | **proven** (induction on the decisions; (NF) gives the same law of ω and U ⊥ ω) | argument |
| 2 | Jensen 1: (m^on)⁺ ≤ E[(m^off)⁺ \| O^on, H_n], so V^on ≤ E[V^off \| O^on] | **proven** (tower property, x⁺ convex) | argument |
| 3 | Jensen 2: (V^on − g)⁺ ≤ E[(V^off − g)⁺ \| O^on] | **proven** ((x − g)⁺ convex and non-decreasing) | argument |
| 4 | each side is the trial-n expected one-step value (`prop:onestep` online; the logged evaluation offline) | **proven** | argument |
| 5 | "the bias is zero under (NI)" | **proven** with (NF): by Theorem `thm:reduction`(1), V\*_n = E[m_n⁺ \| x_{1:n}] for every policy, the sweep included | numeric out:71 (identical decisions on every path) |
| 6 | example in the paper's own setting ((NF) holds, (NI) fails, β = 10) | online 2.3209, offline βψ(g/β) = 3.7444: **optimistic by +1.4235** (closed forms). A sweep shows H₁ = αθ, so offline the rule knows θ at trial 2. | numeric out:70 (simulated +1.4204, s.e. 0.0014, 2.2 s.e. from the closed form; evidence only) |
| 7 | "For a learned forecaster the sign is not determined, even under (NI)" | **proven** by two examples under (NF) and (NI). A forecaster that reads the uninformative H₁ offline is pessimistic (−1.4276). One that reacts online to the "skipped" line is optimistic (+2.3236). | numeric out:72–73 |
| 8 | "The actual loop lies outside (NF), so for it the sign is not determined either." | a scope statement: **proven** as "these results do not determine it" | — |

**Proposed change (optional).** A:296: "so for it the sign is not determined either." → "so these results do not determine the sign for it."

**Readiness: ready as written.**

---

## 9. The information example (`prop:failures`(b); T:106–119, A:303–325, A:377–378) and Table `tab:ex-info`

### 9.1 Signable statement

N = 2. The proposals are fixed in advance and the edits do not interact. θ ∼ N(0, 1). The probe has Δ₁ = αθ, observed without noise. The later edit has Δ₂ = βθ, observed with noise N(0, (κβ)²), κ > 0. U ⊥ θ and the noises. Then (NF) holds and (NI) fails. Assume g > αφ(0).
- The one-step rule skips the probe and has value (βφ(0)/√(1 + κ²) − g)⁺.
- Probe first has value αφ(0) − g + βφ(g/β) − gΦ(−g/β).
- The optimum is the larger of the two, so the gap is the positive part of the difference.
- As β → ∞ the difference is βφ(0)(1 − 1/√(1 + κ²)) + αφ(0) − g/2 + o(1). Its slope φ(g/β) − φ(0)/√(1 + κ²) rises to φ(0)(1 − 1/√(1 + κ²)).
- At κ = 0 the difference tends to αφ(0) − g/2, so it stays bounded. As β → 0 it tends to αφ(0) − g < 0.

### 9.2 Steps

| Step | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | one-step value; probe-first value; optimum = max (A:304–306, A:378) | **proven** (author-checked source; restatement matches REV:150–154) | argument; out:75–78 (MC with common random numbers) |
| 2 | Table `tab:ex-info`, all 12 values (A:319–322) | **proven**: closed forms at 30 digits round to every entry, and each gap equals probe − one-step, rounded | out:75–78 (AN9.1: "match" on all four rows). MC differences sit 0.2–1.9 s.e. from the closed forms: evidence, not proof. |
| 3 | `\ExTenCProbeValue` = 0.40, `\ExTenCSlope` = 0.117 (`generated/numbers.tex`) | **proven**: αφ(0) = 0.398942, slope 0.116847 | out:81 |
| 4 | T:117 "the difference grows linearly in β with slope φ(0)(1 − 1/√2) ≈ 0.117" | **true only asymptotically; the wording is imprecise.** The slope is φ(g/β) − φ(0)/√2: 0.1046 at β = 2, 0.1163 at β = 10, then 0.11684 in the limit. The proof (A:378) states the correct o(1) form. | symbolic out:21–22 (AS9.1–AS9.2); numeric out:79 |
| 5 | "For small β the difference is negative … gap zero"; "At κ = 0 the difference stays bounded" | **proven** | symbolic out:23–24; numeric out:80–81 (β = 0.1: −0.101058, the revision's −0.1011) |
| 6 | Caption "the gap grows roughly linearly in β" | **proven** ("roughly") | out:79 |

### 9.3 Proposed changes (not applied)

*Manuscript:*
1. *(Required, minor.)* T:117: "For fixed $\alpha$, $g$ and $\kappa=1$, the difference grows linearly in $\beta$ with slope $\phi(0)(1-1/\sqrt{2})\approx\ExTenCSlope$." → "For fixed $\alpha$, $g$ and $\kappa=1$, the difference grows asymptotically linearly in $\beta$, with slope $\phi(0)(1-1/\sqrt{2})\approx\ExTenCSlope$ as $\beta\to\infty$."
2. *(Optional.)* A:304: "the one-step rule skips the probe when $g>\alpha\phi(0)$ and has value" → "if $g>\alpha\phi(0)$, the one-step rule skips the probe and has value".

**Readiness:** manuscript **ready after the proposed change** 1. The table is **ready as written**.

---

## New relative to the packets and the audit

1. **`prop:app-record`'s hypothesis and Scope (§3).** The manuscript states a centred common-variance joint law given the history. That law fails after any keep, including the fresh-error and kernel-model cases the Scope says it covers (out:48–51). The formula needs only the kernel, which is what the audit, T2:79 and Corollary `cor:bias-kernel` state. A manuscript wording error, not in T2.
2. **`prop:app-rules`(ii) and T4 Cor. 8a(ii) (§5).** "Value −g" is false under the Bayes keep rule whenever E[Δ_n | O_n] > 0 (out:59). It holds under keep rules that discard duplicates, the default rule among them, which is how results.tex:78 uses it. (iii) needs a history of default-rule keeps (out:60–61).
3. **Edge cases of `prop:onestep` (§6).** The restatement dropped "on a bit-exact node" and the τ_n = 0 context of the author-checked REV 8′.4. Both sentences are false without them (out:65).
4. **Concavity in r for both split policies (§1).** q_r² = c²/(w + s²/r) proves concavity under `"fixed"` as well (out:7–9). P02 §4 had it as observation only.
5. **Closed-form supremum of the value of verification (§4).** φ(0)σ_d√(r/(r+1)) under `"vary"` reproduces P05's 0.2821, 0.3257, 0.3455 (out:17, out:19, out:56). R1-A1-VERIFY's inequality at r = 2 follows from the proposition alone (VoI < φ(0)σ_d < 0.4σ_d). At r = 1 it does not hold, as P05 found (out:57). No PLAN row changes.
6. **Offline bias in the paper's own example (§8).** Offline 3.7444 against online 2.3209 (+1.4235), plus two learned-forecaster examples, one of each sign (out:70–73).
7. **Frozen response (§1).** In an illustrative example (μ = 0, τ = σ_d = 1, r = 1, H = 3), keeping iff D̄ > 0 is worth −0.08857 relative to not verifying (out:37). This illustrates the manuscript's remark. T2 §3's own figures were not reproduced (below).
8. **Slope wording (§9).** The slope of the difference is not constant (out:79).

Confirmed rather than new: the audit's verdicts on T2 Props. 2–5; P02's attainable counterexample (out:32 reproduces its numbers); P03's limits (out:40–45); P04's indexing point (out:52); the 10(c) table and REV R3's numbers (out:20, out:75–78); REV R6's Jensen argument.

## What was not verified

- T2 §3's frozen-response figures ("about 0.0003" at Δ̂ = 2σ_d; "1–2 × 10⁻⁵" under `"fixed"`) and the T2 §6 table: T2 does not state their inputs (P02, P05). Neither is in the manuscript.
- T2 §4's E1 reading ("fixed recovers about half of the value of vary") and PLAN §10's "vary is never less informative": empirical, or not part of these statements, and not proven here.
- Whether the kernel model or the shared-component model describes the real nodes (R1-SCREEN-MEASURE). Statements 3 and 5 are exact within their models.
- The author-checked sources (REV 8′.4, 10(c)) were not re-derived beyond what their manuscript restatements needed. Theorem `thm:reduction` and the other appendix statements (already AI-checked) were not re-checked.
- Inequalities are proven by argument. SymPy checks the identities they rest on. Monte Carlo lines are evidence only. Two MC rows of AN9.1 (β = 2, 10) lie 1.8–1.9 s.e. below the exact closed forms, which this script (30 digits) and `ex10c.py` agree on. AN8.1's simulated offline bias is 2.2 s.e. from its closed form.
- No sealed label, test or evaluation file was opened, and nothing was run on a remote host.

## Files

- `ai_proof_check_appendix_20261123.py`: script. Run `python3 ai_proof_check_appendix_20261123.py > ai_proof_check_appendix_20261123_output.txt` (SymPy 1.14.0, NumPy 2.5.3, SciPy 1.18.1, mpmath 1.3.0; about 20 s, run time on stderr).
- `ai_proof_check_appendix_20261123_output.txt`: output, 81 lines.
- `AI_PROOF_CHECK_APPENDIX_CHECKLIST_20261123.md`: points for the coordinating chat's spot check (b).
