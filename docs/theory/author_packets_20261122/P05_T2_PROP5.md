AI-assisted (Claude, subagent, 22 Nov 2026). Support for the author's own check; not checked or accepted by the author.

# Author proof-check packet: T2 Proposition 5 (the verify index and the price of a run)

*It replaces the short packet `author_packets_20261027/P05.md` for this statement. Source: `../T2_DERIVATIONS.md` §6 on this branch. Audit: `../T_AUDIT_20261027.md` ("Gap (index consequence versus hard-budget optimum)"). Proposed correction (not adopted): `../../proposals/THEORY_CORRECTIONS_20261027.md` §"T2 Proposition 5". T2 has not been revised since the audit (P01 §0).*

**Why it matters for the paper.** PLAN §10 R1-A1-VERIFY reports, as "a theory prediction confirmed in the deployment, consistent with T2 Proposition 5", that A1's KG verify cannot fire at g = 0.1 σ_node with r = 2 ("VoI < 0.4 σ_cmp ≤ 2rg when σ_cmp ≤ σ_node"). `C3_DESIGN.md` (line 29) uses it as the reason screening has value ("verify rarely pays"). A1 is in the paper's arm list (`setup.tex`).

## 1. Statement to check (as currently written)

Index: at E2, verify iff VoI_r(Δ̂) > 2r · g and at least 2r runs remain, with g = V(t\*) per run in the stationary additive model. Consequence: VoI_r ≤ s̃φ(0) ≤ √v φ(0); s̃ and v depend neither on Δ̂ nor on μ₀; "so whenever 2r · g ≥ √v φ(0), the index never verifies: **a fixed budget is better spent on fresh proposals**". A table for a `digits_mlp`-like node (g = 0.0026 / 0.0011; max VoI of verify(2) 0.0018 vary, 0.0009 fixed; "needs g < 0.00044").

## 2. What the proof rests on

| Step | Claim | Check |
|---|---|---|
| 1 | The index rule | A definition, not a theorem. Its VoI assumes the Bayes response (P02 step 8). |
| 2 | VoI ≤ s̃φ(0) | ψ(z) ≤ ψ(0) = φ(0). Correct. |
| 3 | s̃ ≤ √v | s̃² = v − Var(Δ \| Δ̂, D̄) ≤ v. Correct. |
| 4 | s̃, v do not depend on Δ̂ or μ₀ | Gaussian conditioning: both come from the covariance only. Correct. |
| 5 | the index never verifies when 2rg ≥ √vφ(0) | Correct for the strict ">" in the index (equality does not trigger it; audit). |
| 6 | "a fixed budget is better spent on fresh proposals" | **Does not follow (audit), and still in the current text.** It is a hard-budget optimality claim; the index is a one-step comparison with an externally fixed price. Integer remaining budgets, the evolving incumbent, the call cap and the frozen verify response all change the comparison. |
| 7 | g = V(t\*) is the value of a displaced run | Needs: one fresh proposal costs exactly one run, has the stationary law, and no other resource binds (audit). PLAN later fixes g = 0.1 σ_node for the C3 gate, which is a declared price, not V(t\*). |
| 8 | the table | Inputs not stated in T2; the audit could not check it. See section 4 for a reconstruction. |

**Assumptions to state:** those of P02, a fixed Lagrangian price, the Bayes response, ties not triggering.

## 3. The audit and the current text

| Audit finding | In current T2? | In the proposal? |
|---|---|---|
| "better spent on fresh proposals" is not a hard-budget result | No: still there | Yes: "This does not establish optimality under a finite hard budget, an evolving incumbent, or a call cap" |
| g = V(t\*) as an opportunity value needs assumptions | No | Partly: "externally fixed Lagrangian price" |
| VoI formula is for the Bayes response; the harness used D̄ > 0 | Yes (T2 §3) | Yes |
| ties | No | Yes ("when this is positive") |
| table inputs unspecified | No | No |

## 4. Numerical check (run 22 Nov; `check_t2_p6.py`, section P05)

- VoI ≤ s̃φ(0) ≤ √vφ(0): 0 violations over 4,000 parameter sets (both policies, r = 1..5) × 50 values of Δ̂.
- **R1-A1-VERIFY.** The supremum over τ of the maximal VoI divided by σ_d (vary, τ → ∞) is 0.2821 at r = 1, 0.3257 at r = 2, 0.3455 at r = 3; the largest value seen at r = 2 over random sets (both policies) is 0.3099. So at r = 2, VoI < 0.33 σ_d < 0.4 σ_d for every τ, and with g = 0.1 σ_node and σ_d ≤ σ_node the index cannot fire: the PLAN row's inequality holds. **At r = 1 it does not:** 2rg = 0.2 σ_node, and the maximal VoI can reach 0.2821 σ_d when τ is large relative to σ_d. (STATUS records a dry run with r = 1 in which no verify fired; that is consistent with small τ/σ_d, not with the bound.)
- **Table reconstruction (an assumption, not T2's stated inputs).** Back-solving σ_d from row 1 (μ₀ = 0, τ = 0.009, g = 0.0026) gives σ_d = 0.00857. With it: row 2 g = V(t\*) = 0.00107 (table: 0.0011); max VoI of verify(2), vary, = 0.00177 (table: 0.0018); verify worth 4 runs only if g < 0.00044 (table: 0.00044); √vφ(0) = 0.00248. The fixed column (0.0009) is reproduced when the training share of the paired variance is about 0.36 (0.00093; 0.00113 at share 0.50, 0.00076 at 0.25), i.e. sd_train/sd_joint ≈ 0.6, inside the 0.56–0.65 range T2 §4 quotes. So the table is internally consistent with one σ_d. That σ_d differs from the paired sd quoted elsewhere for `digits_mlp` (0.0075 in T5's node table; σ√(2(1 − ϱ)) ≈ 0.0079 from T2 §5's σ and ϱ). Which one T2 used is not recorded.

## 5. Points for the author to decide

1. **Drop "a fixed budget is better spent on fresh proposals"** or restrict it to the priced one-step comparison, as the proposal does.
2. **Use in the paper.** R1-A1-VERIFY's statement is the safe form: "at the declared price g = 0.1 σ_node and r = 2, the index cannot verify, because VoI < 0.33 σ_cmp" (with σ_cmp ≤ σ_node). It needs only steps 2–5. If A1 ever uses r = 1, the bound does not hold.
3. **The table.** State its inputs (μ₀, τ, σ_t, σ_s) if it is kept, or drop it; the reconstruction above is not a substitute.
4. **The "prediction for E1b and Phase 1"** is a modelling prediction under the additive model, not part of the proposition.

## 6. If it checks out

Record an author row with errata: the hard-budget sentence removed, the price stated as a fixed Lagrangian price, the response stated as Bayes. Steps 2–5 can then support A1's description and R1-A1-VERIFY.
