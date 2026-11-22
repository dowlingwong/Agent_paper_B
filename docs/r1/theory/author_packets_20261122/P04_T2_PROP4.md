AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T2 Proposition 4 (record drift and stagnation)

*It replaces the short packet `author_packets_20261027/P04.md` for this statement. Source: `../T2_DERIVATIONS.md` §5 on this branch. Audit: `../T_AUDIT_20261027.md` ("correct with added assumptions"). There is no proposed correction for this proposition in `../../proposals/THEORY_CORRECTIONS_20261027.md`, and T2 has not been revised since the audit (P01 §0). Section 4 continues the unreviewed analysis of `P09_T4_PROP9.md` §4; everything marked "AI analysis, unreviewed" has not been reviewed by anyone.*

**Why it matters for the paper.** The manuscript's sentence after Proposition "Selection bias of the record" ("Later true improvements then face a raised bar") is this proposition's content; `problem.tex` uses it to say the in-run improvement "is selected on noise". T3 used it as hypothesis H3. T4 Proposition 9 generalises its setting, so both depend on the same conditional-normal kernel.

## 1. Statement to check (as currently written)

Setting: incumbent recorded error e, B = J(c_inc) + e; a candidate with true improvement δ has error ε_c; (ε_c, e) is bivariate normal, equal variance σ², correlation ϱ.

- **(a)** P(keep | e) = Φ((δ − (1 − ϱ)e)/(σ√(1 − ϱ²))), decreasing in e for every ϱ < 1.
- **(b)** If ϱ = 0 and a stretch of proposals has no true effect, e_n is the running maximum of n i.i.d. N(0, σ²) draws; e_n → ∞ a.s., E[e_n] equals the expected maximum of n draws, ≈ σ√(2 ln n); for fixed δ, P(keep δ at step n) → 0 a.s.
- **Reading (T2 §5):** on `digits_mlp` (σ ≈ 0.0125, ϱ ≈ 0.8) "an incumbent recorded one σ too high lowers the acceptance of a true +0.005 edit from Φ(0.005/0.0075) = 0.75 to Φ(0.0025/0.0075) = 0.63"; under CRN the effect is "damped by the factor (1 − ϱ), but not removed".

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| a1 | ε_c \| e ∼ N(ϱe, σ²(1 − ϱ²)) | Regression for a centred bivariate normal. Needs σ > 0, −1 < ϱ < 1 (ϱ = ±1 singular; audit). **This is the kernel. It holds for an unselected record; whether it holds for a record that was kept is section 4.** |
| a2 | keep ⇔ δ + ε_c > e; formula; decreasing in e | One line, given a1. |
| b1 | with ϱ = 0, each keep happens exactly when a fresh draw exceeds the record | Needs candidate errors that are **fresh, independent of the whole past** at every null trial (audit). |
| b2 | e_n = running maximum of n i.i.d. draws | The record also includes the initial value: e_n = max(e₀, ε₁, …, ε_n), i.e. the maximum of n + 1 draws if e₀ is itself an unselected draw (audit: "exactly n i.i.d. draws only under a specified initial indexing"). |
| b3 | e_n → ∞ a.s.; E[e_n] ≈ σ√(2 ln n) | Standard extreme-value facts. The second is **asymptotic** (ratio → 1); at campaign lengths it is far from equality (section 3). |
| b4 | P(keep δ at step n) → 0 a.s. | This is the conditional probability P(keep \| e_n) = Φ((δ − e_n)/σ), a random quantity; it → 0 a.s. by b3. The unconditional probability is a number and → 0 by dominated convergence (audit). The claim is for a hypothetical fixed-δ proposal after the null stretch. |

**Assumptions to state** (audit): σ > 0, −1 < ϱ < 1; for (a), that σ and ϱ describe the **conditional kernel given the actual history** ("a selected incumbent error need not retain the unconditional bivariate normal law"); for (b), independent fresh N(0, σ²) candidate errors at every null trial, a finite initial record, and the indexing of n.

## 3. The audit and the current text, and the numerical check

None of the audit's added assumptions is in the current T2 text, and no proposal covers Proposition 4. Numerical check (run 22 Nov; `check_t2_p6.py`, section P04):

- (a) for an unselected bivariate-normal record (σ = 1, ϱ = 0.6, δ = 0.3; 8 × 10⁶ draws), formula against simulation: e ≈ −1: 0.8092 / 0.8094; e ≈ 0: 0.6462 / 0.6472; e ≈ +1: 0.4503 / 0.4500; e ≈ +2: 0.2660 / 0.2667.
- The digits reading's arithmetic: σ√(1 − ϱ²) = 0.00750; Φ(0.005/0.0075) = 0.7475; Φ((0.005 − 0.2 × 0.0125)/0.0075) = 0.6306. Correct under the kernel.
- (b) expected record E[max of n + 1 draws] against √(2 ln n) (σ = 1): n = 10: 1.586 vs 2.146 (ratio 0.739); n = 40: 2.171 vs 2.716 (0.799); n = 1,000: 3.242 vs 3.717 (0.872); n = 10⁵: 4.384 vs 4.799 (0.914). The "≈" overstates the record by about a quarter at 20–40-run campaign lengths.
- (b) a.s. divergence and the a.s. limit cannot be checked by simulation; the trend can: acceptance of δ = 0.005 (σ = 0.0125, ϱ = 0) after 5, 20, 40, 200 null trials is 0.234, 0.092, 0.053, 0.014 (4 × 10⁵ campaigns).

## 4. The kernel after a keep: P09 §4's question for Proposition 4 (AI analysis, unreviewed)

P09 §4 asks whether ε | e ∼ N(ϱe, σ_c²) still holds when e is the error of a configuration that was kept. The audit already warned in general terms (step a1 above). Here are the three questions the coordinating session asked, answered for three generative models of the errors:

- **kernel model**: a configuration's error is ϱ × its parent's error + fresh noise (σ√(1 − ϱ²)). This is what T3 and T5 simulate (below).
- **shared-component model** (P09 §4): every run's error is u + v, u shared by the campaign (variance ϱσ²), v per configuration (variance (1 − ϱ)σ²). Two unselected errors have correlation ϱ, as T2 §5 assumes.
- **fresh draws**: ϱ = 0, every candidate error independent of the past.

Simulation at digits scale (σ = 0.0125, ϱ = 0.8, δ = 0.005; 2 × 10⁷ draws; P(keep δ | record e), with e within ±0.05σ of the target; s.e. ≤ 0.0009):

| model | e | formula (a) | unselected record | record kept once (null keep) |
|---|---|---:|---:|---:|
| kernel, ϱ = 0.8 | 0 | 0.7475 | 0.7476 | 0.7477 |
| kernel, ϱ = 0.8 | σ | 0.6306 | 0.6298 | 0.6316 |
| shared, ϱ = 0.8 | 0 | 0.7475 | 0.7477 | 0.6316 |
| shared, ϱ = 0.8 | σ | 0.6306 | 0.6317 | 0.5322 |
| fresh, ϱ = 0 | 0 | 0.6554 | 0.6553 | 0.6550 |
| fresh, ϱ = 0 | σ | 0.2743 | 0.2751 | 0.2730 |

**Q1. Does (b)'s fresh-draw regime survive?** Yes. With ϱ = 0 and candidate errors independent of the past, the kernel ε | e ∼ N(0, σ²) holds after any number of keeps (last two rows). (b) is unaffected, given the audit's assumptions.

**Q2. Does (a)'s formula hold for a record that was kept?** It depends on the error model, which the statement does not fix. Under the kernel model it holds by construction (rows 1–2). Under the shared-component model it fails after one keep: at e = σ the acceptance is 0.5322, not 0.6306. Reason: in a comparison u cancels, so a keep is decided by v alone, P(keep | v) = Φ((δ − v)/(σ√(1 − ϱ))). After a keep, v is selected and u is not, so the record's error is no longer split between them in the regression proportions that give formula (a).

**Q3. Does the "digits_mlp" reading in T2 §5 use the kernel for a possibly kept record?** Yes. "An incumbent recorded one σ too high" is, in a campaign, typically a record that was kept (selection is what makes records too high). The 0.63 is right under the kernel model; under the shared-component model the corresponding figure after one null keep is 0.53.

**A consequence for the "damped by (1 − ϱ)" reading.** Under the shared-component model, null keeps make v the running maximum of fresh N(0, (1 − ϱ)σ²) draws. So (b)'s stagnation holds for ϱ > 0 as well, with σ√(1 − ϱ) in place of σ: acceptance after n null trials = E[Φ(δ/(σ√(1 − ϱ)) − M_{n+1})], M_{n+1} the maximum of n + 1 standard normals. Simulation against this closed form (σ = 0.0125, ϱ = 0.8, δ = 0.005, 4 × 10⁵ campaigns):

| null trials | fresh (ϱ = 0) | kernel (ϱ = 0.8) | shared (ϱ = 0.8) | shared, closed form |
|---:|---:|---:|---:|---:|
| 5 | 0.234 | 0.620 | 0.380 | 0.380 |
| 20 | 0.092 | 0.420 | 0.189 | 0.189 |
| 40 | 0.053 | 0.299 | 0.124 | 0.124 |
| 200 | 0.014 | 0.103 | 0.042 | 0.042 |

So how much CRN damps stagnation is model-dependent: at 40 null trials the shared-component model keeps less than half of the kernel model's acceptance.

**Which error model T5 (and T3) use.** Read from the code:
- T5 (`r1/theory/simulate_t4.py`, module docstring and lines 406–413, 466–470), noise model `record`: each configuration's error has a split and a training part. A candidate's parts are ϱ × the current record's parts + fresh noise σ√(1 − ϱ²), and a keep makes the candidate's error the new record. That is **the kernel model, applied at every step, including after keeps**. Noise model `iid`: Δ̂ = Δ + σ_d z with fresh zero-mean noise per comparison (T4 (A2)); the displayed record moves by Δ̂ on a keep. Neither is the shared-component model.
- T3 (`r1/theory/simulate.py`, lines 71–74 and 101): regime `crn` uses the same parent-kernel recursion; regime `fresh` uses fresh draws.
- Consequences: T5's agreement with T4 Proposition 9 (residuals ≤ 0.018 × 10⁻³) compares a formula with a simulation generated from the same kernel; it checks algebra and code, not whether the kernel describes CRN noise after keeps. T3's "damped under CRN (0.76 → 0.61), as (1 − ϱ) predicts" is a kernel-model result.

## 5. Points for the author to decide

1. **Is the shared-component model a fair description of how ϱ arises on the CPU nodes** (E1: ϱ_joint 0.39–1.00 per edit)? The split seed is fixed for the campaign, so a split-induced bias common to nearby configurations is plausible; a parent-to-child inheritance (kernel model) is another possibility. This is the same question as P09 §4 item 1, and it is empirical: the revision's §6 check 4 (residuals within an incumbent spell and after keeps), which you put in the plan, can speak to it.
2. **State the kernel as an assumption in (a)**, as the audit asks ("σ and correlation refer to a conditional kernel given the actual history"), and give its scope: exact for a comparison against an unselected record and for ϱ = 0; for later comparisons only under a model like the kernel model.
3. **The digits reading.** Either say that it assumes the kernel model, or replace it by a statement that holds for the first keep from an unselected record.
4. **(b) wording.** Use "the running maximum of the initial record and n fresh draws", write E[e_n] ∼ σ√(2 ln n) as an asymptotic statement (and quote exact values if a campaign-length number is used), and write the vanishing probability as P(keep | e_n).
5. **"Damped by (1 − ϱ)"**: keep it only as a statement about the kernel model, or drop it.

## 6. If it checks out

Record an author row with errata: the kernel stated as an assumption with its scope, ϱ ∈ (−1, 1), (b)'s indexing and asymptotic "∼", the conditional probability in (b), and the scope of the digits reading. The kernel-free part ("on every null keep the record rises", P09 §4) is a stronger, assumption-light statement for the main text if the author adopts it there.

## 7. Status after R1-THEORY-RHO (22 Nov 2026)

*Added 22 Nov 2026 (R1-THEORY-RHO); AI-assisted (Claude, subagent); not author-checked.*

The author's decision (PLAN row R1-THEORY-RHO, decision (3), on branch `author-minsub-20261122`) is applied in `../T2_DERIVATIONS.md` §5:
- **Proposition 4(a)** is unchanged, and a "Scope of (a)" paragraph now follows it: the kernel ε_c | e ∼ N(ϱe, σ²(1 − ϱ²)) must hold given the actual history (σ > 0, −1 < ϱ < 1); it is exact for ϱ = 0 with fresh draws, for ϱ > 0 at an unselected record about which the history carries no further information, and for a kept record only under the kernel model (T3 `crn`, T5 `record`); under the shared-component model it fails for a kept record (0.5322 against 0.6306, section 4). It points to T4 Proposition 9 (restated, kernel-free) and Corollary 9a.
- **The `digits_mlp` reading** in T2 §5 now gives the range 0.53 to 0.63 over the two error models, instead of 0.63 alone, citing section 4 above and `check_t2_p6_output.txt`.

Not changed (the decision did not ask for it; for the author): the (b) wording of section 5 item 4 (indexing, the asymptotic "≈", the conditional probability), and the "damped by the factor (1 − ϱ)" phrase of section 5 item 5, which holds only under the kernel model and is still in the T2 reading.
