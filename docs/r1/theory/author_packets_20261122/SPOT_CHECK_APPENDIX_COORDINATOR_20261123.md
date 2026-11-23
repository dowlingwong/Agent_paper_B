AI-assisted (Claude, coordinating chat, 23 Nov 2026). Check (b) of PLAN row R1-PROOF-POLICY for the appendix statements. Not an author check.

# Spot check (b): the appendix statements of `AI_PROOF_CHECK_APPENDIX_20261123.md`

**What this is.** The coordinating chat's independent re-derivation of at least each statement's key identity or inequality and one edge case, as R1-PROOF-POLICY (b) requires, for check (a) at `7db47e95`. The derivations below were done by hand in this chat. The script `spot_check_appendix_coordinator_20261123.py` was written here without importing code or numbers from `ai_proof_check_appendix_20261123.py`; its output `spot_check_appendix_coordinator_20261123_output.txt` (32 lines, fixed seeds, reproducible, about 10 s) is cited by line tag (SC-A…).

**Result.** No disagreement with check (a) on any key item, any verdict or any required change. One consequence that check (a) draws outside the statements (item 4 below, R1-A1-VERIFY) needs an assumption I could not verify.

| # | Statement | Check (a), manuscript / source | Check (b) |
|---|---|---|---|
| 1 | `prop:app-voi` | ready as written / T2 after changes | agrees |
| 2 | `prop:app-split` | after changes / after changes | agrees |
| 3 | `prop:app-record` and Scope | after changes / after changes | agrees, including the new finding |
| 4 | `prop:app-verify` | ready as written / T2 after changes | agrees; remark on R1-A1-VERIFY |
| 5 | `prop:app-rules` | after changes / after changes | agrees, including the new finding |
| 6 | edge cases of `prop:onestep` | after changes / (source author-checked) | agrees |
| 7 | summed gains | ready as written | agrees |
| 8 | offline-evaluation bias | ready as written | agrees (argument only) |
| 9 | information example, `tab:ex-info` | after one wording change; table ready | agrees |

## 1. `prop:app-voi`
**Key (by hand).** Given H, M′ = E[Δ | H, D̄] ∼ N(m, q²). For m > 0, E[M′⁺] − m = mΦ(m/q) + qφ(m/q) − m = q[φ(m/q) − (m/q)Φ(−m/q)] = qψ(|m|/q); for m < 0 the same expression results without subtracting m. Quadrature agrees to 10 digits at three points (SC-A1a). With f(q) = qφ(a/q) − aΦ(−a/q), f′(q) = φ(a/q) and f″(q) = (a²/q³)φ(a/q) > 0 for a = |m| > 0, so the value is convex in q.
**Edge.** τ² = 2, σ_d² = 1, μ = 0, H = 4.5 (m = 3): increments over r = 1…5 are 2.6·10⁻¹⁰, 6.88·10⁻⁸, 3.94·10⁻⁷, 7.51·10⁻⁷, 9.62·10⁻⁷, increasing (SC-A1b); at m = 0 they decrease (SC-A1c). T2's "with diminishing returns" is false in general.

## 2. `prop:app-split`
**Key (by hand).** Under the fixed policy, D̄ = Δ + e_s + ξ̄ and H = Δ + e_t + e_s: as σ_t → 0 both tend to Δ + e_s, so D̄ adds nothing given H and q → 0; the bound VoI ≤ qφ(0) makes the limit uniform in H. I computed the conditional moments from the joint covariance in my own code: q φ(0) = 6.6·10⁻², 6.9·10⁻³, 2.2·10⁻⁴ at σ_t² = 10⁻¹, 10⁻³, 10⁻⁶ (SC-A2).
**Edge.** Under the vary policy q tends to 0.4364 (τ² = 1, σ_s² = 0.5, r = 2) and VoI at H = 0 to 0.1741 (SC-A2): a positive limit at fixed H. The manuscript must state the two replicate models, as change 1 of (a) §2.3 does.

## 3. `prop:app-record` and its Scope
**Key (by hand).** With ε | (e, history) ∼ N(ϱe, σ²(1 − ϱ²)), P(δ + ε − e > 0 | e) = Φ((δ − (1 − ϱ)e)/(σ√(1 − ϱ²))), strictly decreasing in e for ϱ < 1; simulation agrees at three values of e (SC-A3c).
**Edge, the new finding.** After one null keep from an unselected record at ϱ = 0, ε and e₀ i.i.d. N(0, σ²): given the keep only, E[e] = σ/√π and Var e = σ²(1 − 1/π), since E[ε | ε − e₀ > 0] = (σ²/(σ√2))·λ(0) and λ(0) = √(2/π); simulation 0.5632 and 0.6821 against 0.5642 and 0.6817 (SC-A3a). Given the recorded comparison h, e ∼ N(h/2, σ²/2) (SC-A3b). So "centred bivariate normal with common variance σ² given the history" fails exactly where the Scope says it holds, while the kernel, which is all the formula needs, still holds (a fresh candidate is independent of e). This is the same structure as Lemma K of the first check.

## 4. `prop:app-verify`
**Key (by hand).** ψ is decreasing on [0, ∞) with ψ(0) = φ(0), so VoI = qψ(|m|/q) ≤ qφ(0); and v − q² = Var(Δ | H, D̄) ≥ 0, so q ≤ √v.
**Edge.** Under the vary policy, v ↑ σ_d² as τ → ∞ and q² = v²/(v + σ_d²/r) ↑ σ_d²r/(r + 1): the maximal value approaches φ(0)σ_d√(r/(r + 1)) = 0.2821, 0.3257, 0.3455 σ_d at r = 1, 2, 3 (SC-A4).
**Remark.** Check (a) concludes that at r = 2 and g = 0.1σ_node the index can never verify (R1-A1-VERIFY), because VoI < φ(0)σ_d < 0.4σ_d ≤ 2rg. The last step needs σ_d ≤ σ_node. With σ_d² = 2σ²(1 − ϱ) for a per-run σ, that holds when ϱ ≥ 1/2 and σ_node ≥ σ; I did not check how σ_node is defined (PRE-DELTA) against σ_d per node. This is outside the statement and changes no readiness.

## 5. `prop:app-rules`
**Key, the new finding (by hand).** On a bit-exact node with fixed seeds, a duplicate's comparison H_n is already in the ledger, so m_n = E[Δ_n | O_n] and, by `prop:onestep`, executing under the Bayes keep rule is worth E[Δ_n | O_n]⁺ − g. With a recorded comparison −0.1, forecast μ = 1 and τ = σ = 1, the posterior mean is 0.45 and the value +0.35 at g = 0.1 (SC-A5a); the threshold rule (t\* = −1) would keep it. So "(ii) its value is −g for every g > 0" holds only under a keep rule that discards the duplicate.
**Key (iii).** If every keep was a strict default-rule keep, the record never decreases, so a duplicate's fixed metric is at most the record at its own evaluation and hence at most the current record. A toy ledger with 199,700 duplicate proposals gives 0 with a positive comparison under the default rule and 4,272 under "keep iff comparison > −0.5" (SC-A5b).

## 6. Edge cases of `prop:onestep`
**Key (by hand).** τ_n = 0: Δ_n ∈ {0, μ_n}, so m_n⁺ = 1{μ_n > 0}m_n and V\*_n = (1 − π_n)μ_n⁺.
**Edge.** With π = 0.3, μ = 0.1, τ = σ = 1 and a no-op observed as N(0, 1) (no exact observation), P(non-no-op | H) is strictly between 0 and 1 at every H (0.9307, 0.6220, 0.8318 at H = −3, 0, 2) and m_n(−3) = −1.3496 < 0, so the rule does not keep every proposal (SC-A6). The two sentences need "no-ops observed exactly" and "τ_n = 0", as the author-checked revision 8′.4 has them.

## 7. Summed gains
**Key.** One-step: βφ(0)/√(1 + κ²) − g = 2.3209; always executing with a Bayes keep: αφ(0) + βφ(0) − 2g = 3.3884; difference −1.067417, which the paper rounds to −1.0674; Σ(g − V\*_n)⁺ = g − αφ(0) = 0.1011 (SC-A7). **Edge:** the example satisfies (NF) and violates (NI), so a negative gain is consistent with Theorem (3) needing both.

## 8. Offline-evaluation bias
**Key (argument).** Under (NF), on a common realisation the offline history contains the online one; (·)⁺ is convex, so by Jensen the offline one-step values dominate the online ones trial by trial, and under (NI) the two coincide. I did not run a simulation for this item.

## 9. Information example and `tab:ex-info`
**Key.** Probe first = αφ(0) − g + βφ(g/β) − gΦ(−g/β); at β = 10: one-step 2.3209, probe-first 3.6434, gap 1.3224 (SC-A9a). d/dβ[βψ(g/β)] = φ(g/β), by hand (the two g²/β² terms cancel) and numerically (SC-A9c), so the gap's slope above the kink is φ(g/β) − φ(0)/√2: 0.10457 at β = 2, rising to 0.11685 (SC-A9b). "Grows linearly with slope 0.117" holds only as β → ∞.

## What this check did not do
- It re-derived the key items and one edge case per statement, not every step of (a)'s tables, and it did not recompute every row of `tab:ex-info` (one row).
- It did not check T2 §3's frozen-response figures or T2 §6's table (check (a) could not either: T2 does not give their inputs).
- Whether the error models describe the real nodes is R1-SCREEN-MEASURE's question.
