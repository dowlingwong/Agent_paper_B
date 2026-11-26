AI-assisted (Claude, subagent, 23 Nov 2026). Spot-check list for check (b) of PLAN row R1-PROOF-POLICY. It goes with `AI_PROOF_CHECK_APPENDIX_20261123.md`.

# What the coordinating chat's spot check should re-derive (appendix statements)

R1-PROOF-POLICY (b) asks for at least the key identity or inequality and one edge case per statement. The items marked **key** and **edge** meet that minimum. "out:L" is a line of `ai_proof_check_appendix_20261123_output.txt`. Items marked **new** are claims of check (a) that no packet or audit made; a disagreement there matters most.

## 1. `prop:app-voi` (manuscript ready as written; T2 Prop. 2 after changes)
1. **Key.** Given H, M′ = E[Δ | H, D̄] ∼ N(m, q²), so E[M′⁺] − m⁺ = mΦ(m/q) + qφ(m/q) − m⁺ = qψ(|m|/q) for both signs of m (out:4–5).
2. **Key (new).** With D̄ = L + ξ̄ and Var ξ̄ = s²/r fresh: q_r² = c²/(w + s²/r) = c²r/(wr + s²), with second derivative −2c²s²w/(wr + s²)³ ≤ 0. Concavity holds for vary (L = Δ) and for fixed (L = Δ + e_s) (out:7–9).
3. **Edge.** m ≠ 0: ∂²VoI/∂q² = (m²/q³)φ(m/q) > 0. So diminishing returns in r fail in general: at τ² = 2, σ_d² = 1, μ = 0, H = 4.5, the increments are 6.88e-8, 3.937e-7, 7.509e-7, 9.615e-7 (out:32). At m = 0 the increments decrease (out:33). T2:46's "with diminishing returns" is false.

## 2. `prop:app-split` (after changes)
1. **Key.** Fixed policy, A = τ² + σ_s², u = σ_t²: Cov(Δ, D̄ | H) = τ²u/(A + u) and Var(D̄ | H) = u(1 + 1/r − u/(A + u)), so q² = O(u), with q²/u → τ⁴r/(A²(r + 1)). Hence VoI ≤ qφ(0) → 0, uniformly in H (out:10–11, out:40–44).
2. **Edge.** Vary policy: q² → v₀²/(v₀ + σ_s²/r) > 0, with v₀ = τ²σ_s²/A, so the limit is positive at each H. It is not uniform: 0.0959, 5.35e-5, 1.664e-19, 1.602e-70 at H = 0, 2, 5, 10 (out:12, out:45).
3. Check that the manuscript needs the two replicate models stated (change 1 of §2.3).

## 3. `prop:app-record` and its Scope (after changes)
1. **Key.** With ε | (e, history) ∼ N(ϱe, σ²(1 − ϱ²)), P(δ + ε − e > 0 | e) = Φ((δ − (1 − ϱ)e)/(σ√(1 − ϱ²))), with derivative −(1 − ϱ)φ(·)/(σ√(1 − ϱ²)) < 0 (out:13).
2. **Key / edge (new).** The Scope sentences are false for the joint law as the manuscript states it. ϱ = 0, one null keep from an unselected record: given the recorded comparison h, the kept error is N(h/2, σ²/2), not N(0, σ²); given only the keep, its mean is σ/√π. The kernel still holds: a fresh candidate is independent of it (out:15, out:48, out:50–51). For ϱ = 0.6 in the kernel model: mean +0.357, variance 0.873, Corr 0.573 ≠ ϱ, but regression slope 0.599 and residual variance 0.640 = σ²(1 − ϱ²) (out:49). Re-derive: if e | history ∼ N(m_e, v) and ε = ϱe + σ_cξ, then the regression coefficient is ϱ and Var(ε | e) = σ_c² for every (m_e, v), while Var ε − σ² = ϱ²(v − σ²) (out:14).
3. (b): record = max(e₀, n fresh draws) → ∞ a.s.; P(keep | e_n) = Φ((δ − e_n)/σ) → 0. T2's "expected maximum of n draws" misses e₀ (1.539 against 1.586 at n = 10; out:52).

## 4. `prop:app-verify` (manuscript ready as written; T2 Prop. 5 after changes)
1. **Key.** VoI = qψ(|m|/q) ≤ qψ(0) = qφ(0), and v − q² = Var(Δ | H, D̄) ≥ 0. So VoI ≤ √v φ(0), and 2rg ≥ √v φ(0) means the value never exceeds the cost (out:16, out:55).
2. **Edge (new).** τ → ∞ under vary: v ↑ σ_d² and q² = v²/(v + σ_d²/r) ↑ σ_d²r/(r + 1), so sup max VoI = φ(0)σ_d√(r/(r+1)) = 0.2821, 0.3257, 0.3455 σ_d at r = 1, 2, 3 (out:17, out:19, out:56). Consequence: at r = 2 and g = 0.1σ_node ≥ 0.1σ_d, VoI < φ(0)σ_d < 0.4σ_d ≤ 2rg, so the index cannot verify (R1-A1-VERIFY). At r = 1 it can (out:57).

## 5. `prop:app-rules` (after changes)
1. **Key (new).** For a duplicate on a bit-exact node with fixed seeds, H_n is O_n-measurable. So m_n = E[Δ_n | O_n] and, by `prop:onestep`, executing under the Bayes keep rule is worth E[Δ_n | O_n]⁺ − g, not −g. Example: earlier default-rule discard with h = −0.1, same incumbent, forecast μ = 1, τ = σ = 1. Then E[Δ_n | O_n] = 1 + ½(−1.1) = 0.45, and at g = 0.1 the value is +0.35 (out:59). (ii) is true only under a keep rule that discards the duplicate.
2. **Key.** (iii): if every keep was a strict default-rule keep, B never decreases. A duplicate's metric m satisfies m ≤ B_k ≤ B_n (discarded at k, or kept and later replaced by a larger value), so its comparison is ≤ 0.
3. **Edge.** With a looser keep rule the record can fall and duplicates are kept: keep iff comparison > −0.5 gives 19,528 duplicates kept and 25,865 record decreases, against 0 and 0 under the default rule (out:60–61).

## 6. Edge cases of `prop:onestep` (after changes)
1. **Key.** τ_n = 0: Δ_n ∈ {0, μ_n} has the sign of μ_n, so m_n⁺ = 1{μ_n > 0}m_n and V\*_n = (1 − π_n)μ_n⁺ (REV 8′.4).
2. **Edge (new).** Without exact observation of no-ops, the separation "iff" fails. With τ_n > 0, "keeps every proposal" fails. Counterexample: π = 0.3, μ = 0.1, τ = σ = 1, no-op observed as N(0, 1). Then P(no-op | H) ∈ (0, 1) at every H, and m_n(−3) = −1.3496, so the rule discards (out:65). With τ_n = 0 and a lattice atom at −μ: P(non-no-op | H = 0) = 0.7·0.2/(0.3 + 0.14) = 0.3182 > 0, so every executed proposal is kept, and the value 0.0140 = (1 − π)μ is unchanged (out:63).

## 7. "Summed gains need both conditions" (ready as written)
1. **Key.** J(one-step) = 10φ(0)/√2 − 0.5 = 2.3209 (probe skipped, since φ(0) < 0.5). J(always) = φ(0) + 10φ(0) − 1 = 3.3884 (θ is known at trial 2 after the noiseless probe). The difference −1.0674 is the rounded exact −1.067417; the rounded values would give −1.0675. Σ(g − V\*_n)⁺ = (0.5 − φ(0)) + 0 = 0.1011 (out:20, out:68).
2. **Edge.** The example satisfies (NF) and violates (NI), so the negative gain shows that Theorem (3)'s sum needs (NI).

## 8. "Bias of offline evaluation" (ready as written)
1. **Key.** O^on_n ⊆ O^off_n on a common realisation under (NF). Then (m^on)⁺ ≤ E[(m^off)⁺ | O^on, H_n] and (V^on − g)⁺ ≤ E[(V^off − g)⁺ | O^on] (Jensen twice), so offline ≥ online per trial. Under (NI), Theorem (1) makes the two V\*_n equal.
2. **Edge.** In the `prop:failures`(b) example (β = 10), a sweep reveals θ before trial 2. Offline value βψ(g/β) = 10(φ(0.05) − 0.05Φ(−0.05)) = 3.7444, against online 2.3209: optimistic by +1.4235 (out:70). Learned forecasters can give either sign (out:72–73).

## 9. Information example and Table `tab:ex-info` (after one wording change)
1. **Key.** Probe first = αφ(0) − g + E[(βθ − g)⁺] = αφ(0) − g + βφ(g/β) − gΦ(−g/β). One-step = (βφ(0)/√(1 + κ²) − g)⁺ for g > αφ(0). Recompute one table row: β = 10 gives 2.3209, 3.6434, 1.3224 (out:76). All four rows match to four places (out:75–78).
2. **Key.** d/dβ[βψ(g/β)] = φ(g/β), so above the kink the slope of the difference is φ(g/β) − φ(0)/√2: 0.1046 at β = 2, rising to 0.11685 (out:21, out:79). T:117's "grows linearly … with slope 0.117" holds only asymptotically.
3. **Edge.** κ = 0: the difference tends to αφ(0) − g/2 = 0.1489, bounded. β → 0: it tends to αφ(0) − g = −0.1011, so the gap is 0 (out:23–24, out:80–81).

To record: what was re-derived and the result, in this folder, per R1-PROOF-POLICY (b). A disagreement on any **key** item keeps that statement out of the main text.
