AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packets, 22 Nov 2026

These packets support the author's own proof check of the statements in `../T2_DERIVATIONS.md` (Propositions 1–5) and `../T4_FEEDBACK_PROPOSER.md` (Propositions 6, 7, 9). They replace the short packets in `../author_packets_20261027/` for those statements. Nothing here is author-checked. The manuscript's main text may carry only author-checked statements (PLAN §10 R1-T4-DI-FIX, R1-T4-PROOF-CHECK).

P07 and P09 (with `check_p07_p09.py`, `check_output.txt`) were written by the coordinating session; P01–P06, `check_t2_p6.py` and `check_t2_p6_output.txt` by a subagent. Every number in the packets comes from one of the two script outputs or from a cited file.

**T2 has not been revised since the 27 Oct audit.** The only later change to `T2_DERIVATIONS.md` is a "historical protocol context" banner (commit `c5ea0374`), which says the derivations are unchanged; PLAN R1-THEORY-REPAIR-PROPOSAL and R1-T4-DI-FIX keep T2 unchanged. The audit's corrections to T2 Propositions 1, 2 and 5 exist only as proposals in `../../proposals/THEORY_CORRECTIONS_20261027.md` (not adopted). There is no proposal for Propositions 3 and 4. Each T2 packet compares the current text with the audit and with that proposal.

## Recommended order and verdicts

| Order | Packet | Statement | Verdict | Most important point for the author |
|---|---|---|---|---|
| 1 | `P01_T2_PROP1.md` | T2 Prop. 1: V(t), Bayes threshold, default rule | **gap found** (audit's, still open); main formula: **algebra confirmed** | The false σ_d = 0 sentence ("every t ≤ 0 is optimal") is still in T2; t = 0 is the unique optimum. Add τ > 0, σ_d > 0, Δ ≠ 0, independence. P07 and P06 inherit V(t). |
| 2 | `P06_T4_PROP6.md` | T4 Prop. 6: per-proposal Bayes keep rule | **algebra confirmed**; **depends on** P01; **question for the author** | Under your 16 Nov choice R1 (ii) (shared incumbent error), t\*_n = −μσ²/τ² with the measured σ is the Bayes rule only against an unselected record; after keeps the Bayes threshold shifts down by (1 − ϱ)E[e \| O_n]. Decide what the paper calls the deployed rule. |
| 3 | `P07_T4_PROP7.md` | T4 Prop. 7: value of a per-proposal prior | (coordinating session) identity and bounds confirmed numerically; **depends on** P01 | Step 1 is T2 Prop. 1; the "Reading" about a pilot predictor is an estimate, not part of the proposition. |
| 4 | `P09_T4_PROP9.md` | T4 Prop. 9: winner's curse for every proposer | (coordinating session) formula confirmed under its kernel; **question for the author** | Whether the kernel ε \| e ∼ N(ϱe, σ_c²) holds after a keep; a kernel-free restatement is available. |
| 5 | `P04_T2_PROP4.md` | T2 Prop. 4: record drift and stagnation | (a) **depends on** the error model; (b) **algebra confirmed** under the audit's assumptions; **question for the author** | (b)'s fresh-draw regime survives; (a)'s formula and the `digits_mlp` reading (0.63) hold for a kept record under the kernel model but not under a shared-component model (0.53). T5 and T3 simulate the kernel model. |
| 6 | `P05_T2_PROP5.md` | T2 Prop. 5: verify index and run price | **gap found** (audit's, still open); bound: **algebra confirmed** | "A fixed budget is better spent on fresh proposals" does not follow. R1-A1-VERIFY's inequality holds at r = 2 (max VoI < 0.33 σ_d) but not at r = 1. |
| 7 | `P02_T2_PROP2.md` | T2 Prop. 2: VoI of verify(r) | **gap found** (audit's, still open); formula: **algebra confirmed** | "Diminishing returns in r" is false in general (true at m = 0). The audit's counterexample parameters are not attainable in T2's model, but an attainable one exists. |
| 8 | `P03_T2_PROP3.md` | T2 Prop. 3: verify corrects only resampled noise | **algebra confirmed** (with the audit's added assumptions, which are in neither T2 nor a proposal) | Replace the continuity sentence by the explicit calculation; the vary claim is pointwise in Δ̂. |

## T4 Proposition 8 (unprimed) and Proposition 10(b)

**Proposition 8.** The manuscript does not cite it: its screening statement is part (ii) of "One-step index" (revision Proposition 8′) and its summed gain is the third item of "Reduction to independent one-step decisions" (revision 10(a′).3), both author-checked on 16 Nov. Proposition 8 is still cited by name in `docs/r1/C3_DESIGN.md` (lines 17, 29, 155) and in PLAN's C2 description (line 67, "Proposition 8 screening term"), and T5 §2 checks its summed term E[Σ(g − V\*_n)⁺]. By the revision's remark R3 that sum holds under (NF) and (NI) together, and under R1 (ii) the actual loop is outside 10(a′); any of these uses that reaches the paper should cite 8′ / 10(a′).3 with that scope. Corollary 8a (the rule layer: no-ops and duplicates) is not part of 8′ and is not author-checked. Its part (i) coincides with 8′.4 (π_n = 1); part (iii) (a duplicate is never kept) uses the monotone record under ρ and does not hold under a threshold t\* < 0, as T4 itself notes. The manuscript's "rule layer" (`setup.tex`) relies on it informally.

**Proposition 10(b).** The manuscript needs it: Proposition "Failure of each condition" (a) is 10(b), and `appendix.tex` asks for "author-checked statements and computations for … T4 Propositions 10(b) and 10(c)". The author's check (R1-T4-PROOF-CHECK) covered 10(c), not 10(b). The audit classified 10(b) as a correct existence example (known first increment, σ → 0 limit). Numerical check (`check_t2_p6.py`): the keep-branch gain minus the myopic gain at τ = 1, β = 2 is 1.60955 in closed form and 1.60985 by simulation (s.e. 0.00028, common random numbers). `RUNBOOK.md` line 392 and `C3_DESIGN.md` line 173 still read 10(b) as justifying online RL; the revision's remark R5 says that reading does not follow, and the manuscript's contrapositive wording is the corrected one. A short author check of 10(b) is still needed before the manuscript's Proposition (a) can stay.

## Errata found

**From the 27 Oct audit, still open in the theory files** (each packet's section "the audit and the current text"):
1. T2 Prop. 1: the σ_d = 0 edge sentence is false; t = 0 is the unique optimum (P01).
2. T2 Prop. 1: τ > 0, σ_d > 0 (iff, error rate), Δ ≠ 0 (error rate), joint Gaussian independent noise not stated (P01).
3. T2 Prop. 2: "diminishing returns in r" false in general; "that concavity is the diminishing-returns claim" does not follow (P02).
4. T2 Prop. 2: VoI := 0 at s̃ = 0; independence assumptions (P02).
5. T2 Prop. 3: covariance-continuity step insufficient at the singular limit; vary claim pointwise in Δ̂, not uniform (P03).
6. T2 Prop. 4(a): the kernel must be a conditional kernel given the actual history; ϱ ∈ (−1, 1) (P04).
7. T2 Prop. 4(b): initial-record indexing; conditional vs unconditional probability; fresh independent draws at every null trial (P04).
8. T2 Prop. 5: "a fixed budget is better spent on fresh proposals" is not a hard-budget result; g = V(t\*) as an opportunity value needs assumptions; ties (P05).
9. T4 Prop. 6: τ_n > 0, π_n < 1, s_n > 0, positive probability of a_n = 1, D_nᶜ; "iff μ_n = 0" needs σ_n > 0; a non-trivial π_n needs an information limitation (P06).
10. T4 Prop. 9: Δ_n is not F_n-measurable (P09, audit).

**New in these packets (AI analysis, unreviewed):**
11. T4 Prop. 6 under the author's R1 (ii) decision: the closed-form threshold is Bayes-optimal only against an unselected record; after keeps the Bayes threshold is −(1 − ϱ_n)E[e | O_n] − μ_n w_n²/τ_n² (if e | O_n is Gaussian and independent of Δ_n). The revision's remark R1 states the needed correction; the packet checks it numerically and points out that the deployed rule (C3_DESIGN §1) does not apply it (P06 §4.1).
12. T4 Prop. 6 and the revision's §1: bit-exactness is not needed for the threshold rule or for V\*_n = (1 − π_n)V(t\*_n); the revision's "no such closed form on non-bit-exact nodes" is too strong for the no-op mixture, and the manuscript's "no-ops are observed exactly" can be dropped (P06 §4.2).
13. The audit's counterexample to T2 Prop. 2 uses v = 1 with σ_d = 1, which T2's vary model cannot produce (v < σ_d²), and its "realizable with τ² = 2, σ_d² = 1" gives v = 2/3. The audit's conclusion holds with attainable parameters (P02 §4).
14. T2 Prop. 4: under a shared-component noise model the formula of (a) fails for a record that was kept (0.5322 against 0.6306 at e = σ, digits scale); the `digits_mlp` reading uses it for a record that is typically kept; and stagnation as in (b) also holds for ϱ > 0 with σ√(1 − ϱ) in place of σ, so "damped by (1 − ϱ)" is model-dependent (P04 §4; continues P09 §4).
15. T2 Prop. 4(b): "E[e_n] ≈ σ√(2 ln n)" is asymptotic only; at n = 40 the exact value is 0.799 of it (P04 §3).
16. R1-A1-VERIFY's "VoI < 0.4 σ_cmp ≤ 2rg" holds at r = 2 (sup 0.3257 σ_d) but not at r = 1 (sup 0.2821 σ_d > 2rg = 0.2 σ_node when σ_cmp = σ_node) (P05 §4).
17. T2 §6 table: internally consistent with σ_d = 0.00857, which is not stated and differs from the paired sds quoted elsewhere for `digits_mlp` (P05 §4).

## What was not checked

- Almost-sure and asymptotic statements (T2 Prop. 4(b)'s divergence and limit, the √(2 ln n) rate): only trends at finite n.
- T2 §3's frozen-response figures (0.0003; 1–2 × 10⁻⁵) and T2 §6's table: inputs not stated (the table is only reconstructed under an assumption).
- Whether the joint-Gaussian model, or the kernel versus shared-component noise model, describes the real nodes: empirical (revision §6 check 4 can speak to the latter).
- Concavity of s̃² in r under `"fixed"` and "vary is never less informative than fixed": observed in every random case, not proven.

## Files

- `P01_T2_PROP1.md` … `P06_T4_PROP6.md`, `P07_T4_PROP7.md`, `P09_T4_PROP9.md`: packets.
- `check_t2_p6.py` → `check_t2_p6_output.txt` (P01–P06, 10(b); about 1 minute on 2 CPUs, seed 20261122).
- `check_p07_p09.py` → `check_output.txt` (P07, P09).
