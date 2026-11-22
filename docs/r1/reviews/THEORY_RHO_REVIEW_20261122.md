# Review: R1-THEORY-RHO theory and manuscript commits

*AI-assisted independent review (Claude, fresh session, no part in writing the commits), 22 Nov 2026. Reviewed: `3f53190c` (branch `mac-theory-rho-20261122`) and `32591582` (branch `mac-manuscript-20261122`). Governing row: PLAN R1-THEORY-RHO on `author-minsub-20261122`. This review is not an author check.*

## Verdict: REVISE (small)

The kernel-free Proposition 9 (i)–(iv), its proofs, the threshold remark and Corollary 9a are correct. Two sentences claim more than the mathematics gives. Each needs one missing hypothesis added. One example in a scope bullet is false under the shared-component model. No re-derivation is needed. The numerical check reproduces byte for byte. The manuscript builds cleanly.

Counts: 2 MAJOR, 2 MINOR, 7 NOTE.

## What was checked and holds

- **Prop. 9 (i)** (T4:94): K = {ε_n > e − Δ_n} and e' = ε_n on K. This is an identity and is correct.
- **(ii.1)** (T4:95–96, proof T4:105): Y ≥ 0, so E[Y | G] exists. It is finite because E|ε_n| < ∞ and c is G-measurable. The null-set argument (A ∈ G, E[Y1_A] = 0 ⇒ P(K∩A) = 0 ⇒ E[p_G 1_A] = 0 ⇒ P(A) = 0) is complete.
- **(ii.2)** (proof T4:106): E[ε_n 1_{Kᶜ} | G] ≤ c(1 − p_G), and the mixture identity gives (1 − p_G)(E[ε|K,G] − E[ε|Kᶜ,G]) > 0. This is correct. The appendix version (appendix.tex:341–347) is algebraically equivalent and correct.
- **(iv)** (T4:99, proof T4:108): Z = (ε_n − e + Δ_n)1_K is integrable under the three moment conditions, and the (ii.1) argument applies with G′. The restriction "right side also conditional on the keep" is necessary. Without it the claim is false. Example: e ∈ {0, 10} with probability ½ each, ε ∼ N(0,1) independent, null proposal. Then E[e' | K] ≈ 0.80 < E[e] = 5. The text's disclaimer at T4:101 is correct.
- **Threshold remark** (T4:101): with t G-measurable, c becomes e − Δ_n + t. (i), (ii.1) and (ii.2) go through. This is correct and harmless.
- **Corollary 9a** (T4:110–118): the truncated-normal mean with a_n = ((1 − ϱ)e − Δ)/σ_c is correct. Dropping e ≥ 0 from (a) is correct, because max(e, ϱe) ≥ e for every e. (b) and "shrinks as Δ/σ_c grows" are correct. λ is increasing.
- **Corollary scope**: exact for ϱ = 0 after any number of keeps (fresh N(0, σ²) errors, independent of the past and of Δ_n). The partial covariance ϱ(1 − ϱ)σ² of a spell's Δ̂_j with u given e (T4:122) checks: cov(−v_rec, u) − cov(−v_rec, e)cov(u, e)/σ² = ϱ(1 − ϱ)σ².
- **Prop. 6 derivation** (T4:46–48): Δ̂ = Δ − (1 − ϱ)e + σ_c ξ. Given F_n, Δ̂ is Gaussian with mean μ − (1 − ϱ)m_e and variance τ² + w². The posterior mean is positive iff Δ̂ > −(1 − ϱ)m_e − μw²/τ². This matches t** and w² as stated. At an unselected record w² = σ²(1 − ϱ²) + (1 − ϱ)²σ² = 2σ²(1 − ϱ) = σ_n². Var(e | F_n) ≤ σ² ⇒ w ≤ σ_n. The μ_n > 0 sentence is correct. appendix.tex:270–276 states all three conditions (E[e|O_n] ≥ 0, Var ≤ σ², μ_n ≤ 0) and nothing stronger.
- **T2 Prop. 4(a)** (T2:77, T2:90): 0.5322 and 0.6306 trace to `check_t2_p6_output.txt` lines 46 and 48 and to P04 §4 table rows 4–5. The scope sentence matches Corollary 9a's scope and adds no claim.
- **Numerics**: `python3 check_p07_p09.py` reproduces `check_output.txt` byte for byte. Lines 1–13 are identical to the parent commit. The figures cited at T4:125 (+0.513, −0.001, −0.514, +0.691) and P09:78 ("off by 0.10 to 0.24") match the output.
- **Manuscript**: the theory.tex proposition (theory.tex:53–60) and corollary are no stronger than T4. They are weaker, since (iv) and the threshold remark are omitted. The TBDs at theory.tex:4 and in the appendix proofs mark every restated item as not author-checked. `\CRNThresholdShiftDigits` is a `\TBD` (numbers.tex:54) and renders as a TBD in the PDF. `latexmk -pdf` exits 0, 26 pages, with no undefined or multiply defined references and no overfull boxes. `latexmk -C` was run afterwards, and both worktrees are clean.

## Findings

**M1 (MAJOR), T4_FEEDBACK_PROPOSER.md:48: missing hypothesis E[e | F_n] ≥ 0.** "In that case t**_n ≤ t*_n" refers back to "μ_n ≤ 0 and Var(e | F_n) ≤ σ²" only. Without E[e | F_n] ≥ 0 the implication is false. Take μ_n = 0, Var(e | F_n) = σ², E[e | F_n] = −m < 0: then t** = (1 − ϱ)m > 0 = t*, and the deployed rule keeps too many. E[e | F_n] < 0 does happen after keeps. Keeping a proposal whose Δ̂ fell below its prior mean gives E[ε | F_{n+1}] ∝ (Δ̂ − μ) < 0 (Prop. 9 bounds E[e' | K, G] only for G containing e and Δ_n). The PLAN row and appendix.tex:276 list the condition; T4 omits it. *Fix:* "…when E[e | F_n] ≥ 0, μ_n ≤ 0 and Var(e | F_n) ≤ σ² …". Also qualify "After keeps the location … shifts down" with "(when E[e | F_n] > 0)".

**M2 (MAJOR), papers/r1/sections/theory.tex:62: the reading drops the hypothesis of (iii).** "For an unbiased record, even a true improvement enters the record with a positive expected error whenever a discard was possible" omits E[ε_n | G] = 0. Under the shared-component model, which the paper says may apply on `digits_mlp`, this is false. Counterexample (simulation, 2 × 10⁷ campaigns, ϱ = 0.5, σ = 1): take a record kept once by a null keep, with e ≈ 0 and Δ_n = 3. Then P(keep) = 0.9995 and E[e' | keep] = −0.229 (s.e. 0.001), because E[u | e = 0, kept] < 0. Prop. 9(iii) itself (theory.tex:58; T4:98) is correct. *Fix:* "For an unbiased record and a candidate error with conditional mean zero, …".

**m1 (MINOR), T4:122: the example "first comparison after a fresh measurement of the incumbent" fails under the shared-component model** when the ledger keeps the incumbent's earlier record. B_new − B_old = v_new − v_old is in F_n, and its partial covariance with u given e is ϱ(1 − ϱ)σ² ≠ 0. Simulation (ϱ = 0.5): for a re-measured, previously kept incumbent at e ≈ 0.9, E[ε | e, F_n] is 0.868, 0.474 and 0.058 for B_new − B_old < −0.5, ∈ (−0.5, 0.5) and > 0.5. The kernel gives 0.45, which is right only given e alone (0.450). The general condition in the same bullet ("history carries no further information") is right; only the example is wrong. The manuscript does not carry the example. *Fix:* delete the example, or use "the first comparison against the campaign's initial, never-compared record".

**m2 (MINOR), T4:118 and appendix.tex:348: integrability in the corollary's proof.** "The inequality is Proposition 9(ii)" uses E|ε_n| < ∞. Under the corollary that requires E|e| < ∞, which is not assumed. The inequality still holds, because given G_n, ε_n is Gaussian. T4 covers this with the Mills-ratio parenthetical; the appendix has only the (ii) route. *Fix:* in the appendix, add "(or directly from λ(a) > max(0, a))", or assume E|e| < ∞. Optionally weaken (ii)'s condition to E[|ε_n| | G] < ∞ a.s.

**N1, Prop. 9(iii) (T4:98, theory.tex:58).** The conclusion E[e' | K, G] > 0 uses only E[ε_n | G] = 0; e = 0 is not used. It only supports the reading "from an unbiased record". This is harmless. A remark could say so.

**N2, the CRN scope is stated in kernel form.** t** and the conditions (Var(e | ·) ≤ σ²) are derived under Corollary 9a's kernel (T4:46; appendix.tex:270). The limitation applied to `digits_mlp` (limitations.tex:13) and theory.tex:35 refer to the shared-component case, and theory.tex:35 does not say "under the kernel". Under the shared-component model the same algebra gives t** = −E[v_rec | ·] − μw′²/τ², with w′² = (1 − ϱ)σ² + Var(v_rec | ·). The conditions become E[v_rec | ·] ≥ 0 and Var(v_rec | ·) ≤ (1 − ϱ)σ². The qualitative claim survives. The PLAN's wording is itself kernel-form, so this is not a deviation. *Suggest* one sentence in T4 §2 and the appendix. "Bayes-optimal only against an unselected record" (limitations.tex:13; theory.tex:35) should add "about which the history carries no further information".

**N3, T2:90.** "Between 0.53 and 0.63" consists of two points, not bounds. Under the shared-component model the acceptance falls further after more keeps: 0.465 at e = σ after two null keeps (my simulation, ≈1.1 × 10⁵ rows). The parenthetical specifies the cases, and the PLAN asked for this range, so this is a NOTE. *Suggest* "(lower after further keeps)".

**N4, numerical check (`check_p07_p09.py`, `prop9_kernel_free`).** The test is fair for the stated purpose: the shared-component model, a proposer that reads the displayed B (μ depends on B), and records selected at least once. Two caveats. (a) The pathwise check (i) is true by construction (`keep = d + eps − e > 0`), so it tests nothing. (b) The bins coarsen G, so the bin comparison checks (iv) and an approximate (ii.2). The margins are large (≥ 0.36), so the inequalities are not stressed near equality. The kernel-formula column does show that the corollary fails in this model.

**N5, stale cross-references.** T4:5 still calls the truncated-mean formula "of Proposition 9"; it is now Corollary 9a. `T5_SIMULATION.md:180` ("Proposition 9's inverse-Mills record bias") and `T5_HANDOFF.md:21` likewise. *Fix:* T4:5 → "Corollary 9a". The T5 files are outside this row, so leave them for the T5 re-run.

**N6, out-of-row items left unchanged.** The P04 status section flags these correctly: "damped by the factor (1 − ϱ)" (T2:90) holds only under the kernel model, and the (b) wording errata remain open. This is no defect of these commits.

**N7, additions beyond the row.** Corollary 9a(a) without e ≥ 0, part (iv), the threshold remark, and the manuscript scope remark on Prop. 4(a) (appendix.tex:233–234) are all correct and harmless. All are marked "Revised 22 Nov 2026 (R1-THEORY-RHO); AI-assisted; not author-checked". No preregistered constant, arm or Prop. 6 statement changed.

## Not checked

The empirical claims from `check_kernel_e1_output.txt` (+0.37 [0.24, 0.51]) were not re-run; they are cited as unreviewed. Neither was the T3/T5 code's noise model. The P06 §4.1 numbers were not re-run.
