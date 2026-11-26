Reviewed base: `77f49584` (branch `mac-t4-errata-20261116`; accepted in round 1, confirmed in round 2 at `1081f990`)

# Independent review record — T4 revision 3 (errata of R1-T4-PROOF-CHECK), 16 November 2026

**Unit.** Revision 3 of `docs/r1/proposals/T4_PROP10_REVISION_20261028.md`: the errata (1)–(4), R1 = option (ii),
R4 = 20 proposals and the §6 decision of PLAN §10 R1-T4-PROOF-CHECK (`main` @ `025bfc16`). The script
`t4_prop10_revision_20261028/ex10c.py` and its output are unchanged.

**Process.** One independent reviewer (a separate agent that did not write the revision), two rounds. The reviewer
edited no files. The round texts are reproduced below as delivered.

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `77f49584` (diff from `025bfc16`) | ACCEPTED (8 MINOR) |
| 2 | `1081f990` (diff from `77f49584`; minors in `2434af3e`, `1081f990`) | ACCEPTED (3 optional nits) |
| — | `fba64218`: the three optional nits of round 2, applied after acceptance | not re-reviewed |

---

## Round 1 (commit `77f49584`)

I reviewed T4 revision 3 (`docs/r1/proposals/T4_PROP10_REVISION_20261028.md`, branch `mac-t4-errata-20261116` @ `77f49584` on top of `025bfc16`; worktree /tmp/pb/wt/t4err). I found no BLOCKING or MAJOR issue, only MINOR ones. Nothing in the repo was edited.

**What I checked**
- **Diff scope:** the commit changes only the T4 file. The file at `025bfc16` is the same as at `9ae6d877`, the revision the author approved.
- **Translation:** the errata translation you gave matches the Chinese row (PLAN line 1217). 逐字一致 ≈ "byte for byte" is a fair rendering.
- **(a) Errata and decisions:** all four errata, R1 (ii), R4 (20 proposals), the five §6 checks and the deferred C4 test are applied. No proposition's result changes beyond the errata.
- **(b) Mathematics:**
  - **Step 1 chain (l.118–122) is correct.** From U ⊥ W, decomposition and weak union give U ⊥ Y_{≤n} | x_{1:n}. A second weak union gives U ⊥ Y_n | (x_{1:n}, Y_{<n}). Contraction with (NI) gives Y_n ⊥ (Y_{<n}, U) | x_{1:n}, that is, Y_n ⊥ G_n | x_{1:n}. The tower chain is valid because σ(x_{1:n}) ⊆ O_n ⊆ G_n.
  - **Step 3 (l.128) is correct.** The sum of bounds is the same for every policy because part 1 makes V*_n a function of x_{1:n}, and (NF) gives x_{1:N} the same law under every policy.
  - **8′.4 with τ_n = 0 (l.79–81, 86) is correct.**
    - V*_n = (1 − π_n)μ_n⁺ holds whether or not there is probability mass at zero: if μ_n > 0 then m_n ≥ 0 and E[m_n | O_n] = (1 − π_n)μ_n; if μ_n ≤ 0 then m_n ≤ 0.
    - At μ_n = 0, Δ_n = 0 almost surely, so V*_n = 0; keep and discard are equivalent, and skip is strictly better for g > 0.
    - The identification condition is necessary, and in fact also sufficient.
  - **10(c) gap (l.151–157) is correct.** max(J_myopic, J_probe) − J_myopic = (J_probe − J_myopic)⁺. The β → ∞ expansion and the slope 0.11685 check out.
- **(d) Numbers:** with /tmp/np244/bin/python (Python 3.13.18, NumPy 2.4.4, SciPy 1.17.1), `python -I ex10c.py > /tmp/t4rev/out.txt` gives return code 0, and `cmp` with `ex10c_output.txt` shows the files are identical. `closed_form(1, 0.1, 1, 0.5)` gives myopic 0.0, probe −0.1010577, so the difference is ≈ −0.1011 and the gap is 0. E[(βθ − g)⁺] = 5.3e−9. A Monte Carlo run agrees: −0.1007 ± 0.0004. The difference turns positive between β = 0.5 and 0.8. The four table rows are all positive.
- **(e) Consistency:** no U ⊥ W assumption is left in §1. The remaining mentions are l.88 (8′ doesn't need it), l.96 ((NF)) and l.147 (checking (NF) in the 10(c) example), all correct. R3 is consistent with R1 (ii). For R6, see finding 6.
- **(f) offline_eval.py:** the R4 claims are true. `CAMPAIGN_RUNS = 20`. `per_campaign = CAMPAIGN_RUNS * np.average(r, weights=eval_weight)` per node, with r = Δ_true·keep − g·execute, and `gain_per20` is computed the same way. This matches PLAN l.443, "Run accounting in the 20-run scaling", option A (c = 1 equals the primary).

**Findings**

1. **MINOR — l.79, §9 l.295–300.** The keep rule in 8′.4 changed from "keep iff μ_n > 0" (revision 2) to "keep iff m_n > 0". The change gives the same value: with τ_n = 0, both rules attain V*_n, and they differ only on detected no-ops, where Δ_n = 0. But erratum (2) did not ask for it, and the §9 editorial list does not include it. **Fix:** list it in §9 as editorial, noting that both rules are optimal.

2. **MINOR — l.197.** "Proposition 8′ applies as stated, because m_n and V*_n condition on O_n, which carries the information about e" is a justification the row does not contain, and it slightly overstates.
   - Parts 1–4 are distribution-free, so they do hold.
   - But the Gaussian closed-form sentence of 8′.1 (l.74, via l.69) needs (A2) relative to O_n. Under option (ii), η_n given O_n has mean (ϱ_n − 1)E[e | O_n] ≠ 0 (R1, l.188), so the threshold t*_n of Proposition 6 does not apply without a correction.
   - **Fix:** either drop the because-clause, keeping the row's wording ("values of 8′ computed conditional on the posterior of e"), or limit it to "parts 1–4", with the closed form needing the comparison corrected by (1 − ϱ_n)E[e | O_n] and the posterior variance of e.

3. **MINOR — l.234.** The (NF-a) display row is marked "in the plan (check 1)", but its Test cell also contains "Then compare memory `none` vs `append_only_summary` (D24)". The row admits only the display audit (显示审计). **Fix:** status "in the plan (check 1: display audit only; the D24 comparison is not decided)".

4. **MINOR — proof gaps (l.86, l.122).**
   - l.86 jumps from "Δ_n ∈ {0, μ_n} has the sign of μ_n" to V*_n = (1 − π_n)μ_n⁺. The missing step: m_n inherits the sign of μ_n (μ_n is O_n-measurable), so m_n⁺ = 1{μ_n > 0}·m_n and E[m_n | O_n] = E[Δ_n | O_n] = (1 − π_n)μ_n. §9 says this proof was written out, so it should include that step.
   - l.122: "(Δ_n, H_n) ⊥ O_n | x_{1:n}, which is part 1" leaves out that getting m_n = E[Δ_n | x_{1:n}, H_n] takes one more weak union, Δ_n ⊥ O_n | (x_{1:n}, H_n). This gap was already in revision 2, and it may be what revision 2's "weak union" was referring to. **Fix:** add the one clause.

5. **MINOR — wording, l.46 and l.80.** "Only if" can be "if and only if" (for 0 < π_n < 1). The parenthetical at l.80 ("so the rule keeps exactly when μ_n > 0 and the proposal is not a no-op") also holds without the condition when π_n = 0. Worth saying: without the condition, the m_n-rule may keep some no-ops when μ_n > 0, but V*_n and all values are unchanged.

6. **MINOR — consistency with R1 (ii), l.207 and l.214–217.** R6's signed results, including "A1 and A1-ctx are unaffected", and R4's link to 10(a′).3 are stated under (NF). R1 (ii) says (NF) fails for the actual loop through the incumbent error e. The file does not say so. They are not contradictory, since the statements are conditional, but a reader could apply R6 to the actual loop. **Fix (optional, a consequence rather than a decision):** a one-line cross-reference in R6 and R4: under R1 (ii) the actual loop is in the "otherwise" case, where the sign of the offline bias is not determined.

7. **MINOR — additions beyond the row.**
   - l.9: "Each §6 check is carried out as its own unit" is a process statement the row does not make; it is harmless.
   - l.280: "in this version" now reads ambiguously, since the paragraph means revision 2.
   - l.228: double blank line.

8. **MINOR — notes.**
   - R4 (l.209): the "20 proposals" horizon is a declared convention. §1 (l.37) defines N as the LLM-call cap, which is not 20 in the sweeps; one clause could tie the 10(a′).3 comparison to N = 20.
   - `offline_eval.gate_verdict` is a NOT_AVAILABLE placeholder (the R1-BX-D8 aggregate gate). The claim that offline_eval matches the gate is true of the scaling computation, but no gate is implemented yet.
   - The script output still labels the signed difference "loss"; l.170 could note that.
   - l.118 strictly uses decomposition before weak union.

**(c) The editorial list:** all five listed items change no result. The unlisted items are findings 1 and 2.

VERDICT: ACCEPTED

### Author's response to round 1 (commits `2434af3e`, `1081f990`)

All eight minors applied: the keep-rule change listed in §9 as editorial; "if and only if" identification for
0 < π_n < 1, with the no-op keeping remark; the part-4 and Step-1 proof steps written out; R1 (ii): parts 1–4 hold,
and the closed form needs the comparison corrected by (1 − ϱ_n)E[e | O_n] and (1 − ϱ_n)² Var(e | O_n) added to the
noise variance (`1081f990` corrected the scaling); R4 and R6 note the "otherwise" case under R1 (ii); R4 ties
10(a′).3 to N = 20 and notes the `gate_verdict` placeholder; check 1 limited to the display audit; the process
sentence removed; "revision 2" in §8; the double blank line removed; the script's "loss" label noted.

---

## Round 2 (commit `1081f990`)

Round 2: all 8 round-1 minors are fixed correctly in `2434af3e` and `1081f990`, the new mathematics checks out, and nothing new is presented as an author decision. Only the T4 file changed (31 lines); the script, its output and r1/ are untouched. I made no edits.

**The four passages you asked about**
1. **Part-4 proof (l.87).** Correct.
   - μ_n is O_n-measurable and Δ_n ∈ {0, μ_n}, so m_n = E[Δ_n | O_n ∨ σ(H_n)] has the sign of μ_n.
   - Hence m_n⁺ = 1{μ_n > 0}·m_n, and the tower property gives V*_n = 1{μ_n > 0}·E[Δ_n | O_n] = (1 − π_n)μ_n⁺.
2. **Step-1 weak-union clause (l.123).** Correct.
   - Weak union on (Δ_n, H_n) ⊥ O_n | x_{1:n} gives Δ_n ⊥ O_n | (x_{1:n}, H_n), which yields the m_n formula.
   - V*_n = E[m_n⁺ | x_{1:n}] follows from H_n ⊥ O_n | x_{1:n}, since m_n⁺ is a function of (x_{1:n}, H_n).
   - The parenthetical now correctly confines "tower property" to the step from G_n to O_n.
3. **"Iff" identification (l.46, l.80).** Correct. On a bit-exact node, {H_n = 0} is I_n together with {Δ_n + η_n = 0} ∩ I_nᶜ, so identification holds exactly when P(Δ_n + η_n = 0, I_nᶜ | O_n) = 0. The restriction 0 < π_n < 1 is not needed, but it does no harm.
   - With separation, the rule keeps exactly when μ_n > 0 and the proposal is not a no-op.
   - The new note that the two keep rules differ only on detected no-ops is also correct. If μ_n ≤ 0, neither rule keeps. If μ_n > 0 without separation, m_n > 0 everywhere, so the rules coincide. With separation, they differ only on {H_n = 0} = I_n, where Δ_n = 0. Both attain V*_n.
4. **R1 (ii) closed-form remark (l.198).** Correct, given Proposition 9's η_n = (ϱ_n − 1)e + σ_{c,n}ξ_n.
   - The corrected comparison Δ̂_n + (1 − ϱ_n)E[e | O_n] has noise (ϱ_n − 1)(e − E[e | O_n]) + σ_{c,n}ξ_n, with mean 0 and variance σ²_{c,n} + (1 − ϱ_n)²Var(e | O_n). So the `1081f990` scaling fix is right.
   - The correlation sentence is right: within a spell, these residuals all contain e − E[e | O_n] and are therefore correlated.
   - Saying that parts 1–4 of 8′ hold as stated is right, since they are distribution-free.

**The other fixes**
- Revision 2's "keep iff μ_n > 0" is now noted and listed in §9.
- R4 and R6 now say the actual loop under R1 (ii) is in their "otherwise" case.
- R4 now says the match with 10(a′).3 needs N = 20, and that `gate_verdict` is a placeholder pending R1-BX-D8. Both are true.
- §6 check 1 is limited to the display audit and states that the D24 comparison is not decided.
- "Each check is its own unit" is removed. §8 now says "revision 2". The script note now mentions the "loss" label.
- §9 lists all the new edits as editorial.

**No new author decisions.** Every addition is a consequence or a wording fix, listed in §9. The one decision-adjacent statement, "the D24 comparison is not decided", is accurate.

**Optional nits, none of them blocking**
- l.80: "may also keep some no-ops" understates it. When μ_n > 0, 0 < π_n < 1 and there is mass at zero, {H_n = 0} is one event on which m_n > 0, so the rule keeps every no-op.
- l.198: the two corrections are what the closed form needs, not all it needs. For it to hold exactly, the posterior of e given O_n must also be Gaussian, and e must be conditionally independent of Δ_n given O_n. Otherwise the law is a mixture or the noise is correlated with Δ_n. One clause would cover it.
- l.198: the analysis sits inside the "Author decision" bullet list. Labelling it "(analysis; not part of the decision)" would keep the boundary clear. §9 already lists it as editorial.

VERDICT: ACCEPTED

### Author's response to round 2 (commit `fba64218`, after acceptance)

The three nits applied: without separation and with μ_n > 0 the m_n-rule keeps every proposal, no-ops included; the
closed form also needs a Gaussian posterior of e and e conditionally independent of Δ_n given O_n; the R1 (ii)
analysis is labelled "Analysis, not part of the decision". Not re-reviewed.

---

Accepted commit: `77f49584` (round 1), confirmed at `1081f990` (round 2). Final commit including the round-2 nits:
`fba64218`.
