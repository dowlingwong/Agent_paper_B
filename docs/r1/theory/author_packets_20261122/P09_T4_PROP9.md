# Author proof-check packet: T4 Proposition 9 (the winner's curse holds for every adaptive proposer)

*AI-assisted (Claude, chat session, 22 Nov 2026). Support for the author's own check; **not checked or accepted by the author**. It replaces the short packet `author_packets_20261027/P09.md` for this statement. Source: `../T4_FEEDBACK_PROPOSER.md` §5 on `main` @ `3c3f822a`. Audit: `../T_AUDIT_20261027.md` ("correct with added assumptions"). Section 4 below contains an analysis by the AI that has **not** been reviewed by anyone; treat it as a question to settle, not as a finding.*

**Why this one comes second.** It is the selection-bias statement of C2 for a ledger-dependent proposer, and R1-C1-POSITION lists "theory for a ledger-dependent proposer" among the paper's four stated differences.

## 1. Statement to check

Recorded incumbent value B = J(inc) + e. On a non-no-op proposal the candidate's single-run error is ε_n = ϱ_n e + σ_{c,n} ξ_n with ξ_n ~ N(0,1) **independent of (F_n, e, Δ_n)**, ϱ_n in [0, 1), σ_{c,n} = σ√(1 − ϱ_n²). The default rule keeps iff Δ̂_n = Δ_n + ε_n − e > 0, and then e′ = ε_n. Claim, for every proposer:

- E[e′ | keep, F_n, e, Δ_n] = ϱ_n e + σ_{c,n} λ(a_n), a_n = ((1 − ϱ_n) e − Δ_n)/σ_{c,n}, λ = φ/(1 − Φ);
- E[e′ | keep, ·] > max(e − Δ_n, ϱ_n e);
- (a) null proposal and e ≥ 0: E[e′ | keep] > e; (b) e = 0: E[e′ | keep] = σ_c λ(−Δ_n/σ_c) > 0.

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | Given (F_n, e, Δ_n): ε_n ~ N(ϱ_n e, σ_{c,n}²) | This **is** the kernel assumption. See section 4. |
| 2 | keep ⇔ ε_n > e − Δ_n | Immediate from Δ̂_n > 0. |
| 3 | E[ε \| ε > c] = m + σ_c λ((c − m)/σ_c) | Standard truncated-normal mean; needs σ_c > 0. |
| 4 | λ(a) > 0 and λ(a) > a for all real a | Standard Mills-ratio facts. |
| 5 | "the proposer enters only through Δ_n and ϱ_n, which are F_n-measurable" | **Erratum (audit):** Δ_n is not F_n-measurable; under (A1) it is random given F_n. The proof conditions on Δ_n, which is enough. ϱ_n is F_n-measurable. |

**Assumptions to state** (audit): σ_c > 0, ϱ_n < 1, a keep of positive probability, non-no-op proposals. The statement is about the conditional bias given a keep. It does not say that every proposer meets keeps, or that the unconditional bias of a campaign rises.

## 3. Numerical check (run 22 Nov; `check_p07_p09.py`, output in `check_output.txt`)

Under the proposition's own kernel, four parameter sets (4 × 10⁶ draws each): the formula and the simulation agree within simulation error (for example e = 0.5, Δ = 0, ϱ = 0.3: 1.14705 against 1.14690, s.e. 0.00043), and the inequality holds in each.

## 4. A question about step 1 (AI analysis, unreviewed)

**The question.** The kernel says that, whatever the history, a fresh candidate's error given the incumbent's recorded error e is N(ϱ e, σ_c²). T2 §5 motivates ϱ > 0 by common random numbers on CPU nodes: the two runs share part of their noise. Does the kernel still describe that mechanism **when e is itself the error of a configuration that was kept**, that is, after the first keep?

**Why it may not.** Take the simplest shared-noise model: every run's error is u + v, with u shared by the runs of a campaign (variance ϱσ²) and v independent per run (variance (1 − ϱ)σ²). Two unselected errors are then bivariate normal with correlation ϱ, as T2 §5 assumes. In a comparison u cancels, so a keep selects on v alone. After a keep, the record's error e = u + v has a selected v and an unselected u, and the law of u given e is no longer the normal regression on e. A fresh candidate's error u + v′ given e then does not have mean ϱ e.

**Simulation** (2 × 10⁷ campaigns, ϱ = 0.5, σ = 1, null proposals; mean of a fresh error given the record's error e):

| e | kernel's ϱ e | given an unselected record | given a record that was kept once |
|---:|---:|---:|---:|
| −0.9 | −0.450 | −0.448 | −0.778 |
| 0.0 | 0.000 | +0.001 | −0.231 |
| +0.9 | +0.450 | +0.448 | +0.306 |
| +1.9 | +0.950 | +0.945 | +0.876 |

(standard errors 0.001 to 0.002). The kernel holds for an unselected record and fails after one keep in this model.

**What would follow, if the author agrees.**
- The proposition is correct as a statement about its kernel. For ϱ_n = 0 (fresh draws) the kernel holds after any number of keeps, so nothing changes there.
- For ϱ > 0 the exact formula and the bound "> ϱ_n e" describe the first keep from an unselected record, or any mechanism in which the kernel is assumed to hold. The same applies to T2 Proposition 4(a), which uses the same conditional law.
- **The core of the claim does not need the kernel at all.** A keep happens exactly when ε_n > e − Δ_n, and then e′ = ε_n. So on every keep, for every proposer and every noise law, e′ > e − Δ_n. For a null proposal, e′ > e on every keep: the record's error rises at each noise-driven keep, path by path. In the simulation this holds on every first and every second keep. And if e = 0 and the candidate's error has conditional mean zero, E[e′ | keep] > 0 whenever a discard has positive probability, because truncating from below raises a mean.
- A possible restatement for the manuscript: give the kernel-free inequalities as the proposition ("for every proposer and every error law"), and give the truncated-normal formula as a corollary under the kernel, with its scope stated. That is a stronger headline with weaker assumptions.

**What the author should settle.**
1. Is the shared-noise model above a fair description of how ϱ arises on the CPU nodes (E1 measured ϱ between 0.39 and 1.00 per edit)? If the correlation comes from another mechanism, the kernel may hold more widely.
2. If yes: adopt the restatement, and add the same scope note to T2 Proposition 4(a) and to the reading in T2 §5 ("an incumbent recorded one σ too high lowers the acceptance…", which uses the kernel for a record that may have been kept).
3. T5's simulations of the feedback channel: which error model do they use? If they use the kernel at every step, their numbers are for the kernel model; if they use shared components, they already contain the effect.

## 5. Smaller points

- Reading, T4 §5: "the bias is a property of the acceptance rule, not of the proposer" is supported by the kernel-free inequality.
- The debiased-memory display (route D) is cut from the submission version (R1-SUBMISSION-CUTS); the sentence proposing it can go to the appendix or be dropped.

## 6. If it checks out

Record the result as an author row with errata (the Δ_n measurability erratum at least), and say which form goes into the main text.

## 7. Status after R1-THEORY-RHO (22 Nov 2026)

*Added 22 Nov 2026 (R1-THEORY-RHO); AI-assisted (Claude, subagent); not author-checked.*

The author adopted the restatement of section 4 (PLAN row R1-THEORY-RHO, decision (1), on branch `author-minsub-20261122`). The new text is in `../T4_FEEDBACK_PROPOSER.md` §5:
- **Proposition 9 (restated)** is kernel-free: (i) e′ > e − Δ_n on every keep, and e′ > e on every null keep; (ii) for any σ-field G containing σ(e, Δ_n) and E|ε_n| < ∞, E[e′ | keep, G] > e − Δ_n where a keep has positive conditional probability, and E[e′ | keep, G] > E[ε_n | G] where a discard also has positive conditional probability; (iii) the e = 0 positivity under a conditional-mean-zero candidate error; (iv) a version for coarser information (F_n alone). Each part is proved in a few lines.
- **Corollary 9a** is the 18 Oct truncated-normal formula under the kernel, with its scope: exact for ϱ = 0 after any number of keeps; for ϱ > 0 from an unselected record about which the history carries no further information, or wherever the kernel is the generative model (T3 `crn`, T5 `record`); not exact under the shared-component model.
- The audit's erratum (Δ_n is not F_n-measurable) is applied: every statement conditions on Δ_n.
- Two small changes against the 18 Oct text, for the author to check: Corollary 9a(a) drops the restriction e ≥ 0 (not needed, since the bound > e − Δ_n = e holds for every e); and a remark gives the threshold-rule version (e − Δ_n + t in place of e − Δ_n).
- New in the restated scope (AI analysis, unreviewed): under the shared-component model, earlier recorded comparisons against the same unselected record already inform the split of e, so "exact from an unselected record" needs a history that carries no such information.
- Numerical check of the kernel-free inequalities under the shared-component model with a proposer that reads the displayed record: new function `prop9_kernel_free` in `check_p07_p09.py` (own random generator; the earlier output lines are unchanged), output in the last seven lines of `check_output.txt`. The inequalities hold on every keep and in all five (e, Δ) bins; the kernel formula is off by 0.10 to 0.24 in those bins.

Still open: the author's proof check of the restated text (R1-MINSUB-CHOICES (3)); the empirical question of section 4, item 1 (PLAN R1-THEORY-RHO (5)).
