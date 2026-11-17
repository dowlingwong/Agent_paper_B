Reviewed base: `457a097a` (branch `mac-tracks-appendix-20261116`; accepted in round 2)

# Independent review record — Track S appendix draft, per-decision wording (16 November 2026)

**Unit.** Revision of `docs/r1/reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md` to the per-decision wording of
Proposition 8′ parts 2–3, with no campaign-level conclusion (PLAN §10 R1-T4-PROOF-CHECK, consequence clause;
R1-TRACKS-STOP4-CONSEQUENCES item 5). Authority: `main` @ `025bfc16`. Theory text: T4 revision 3
(`mac-t4-errata-20261116`, review accepted; final `fba64218`).

**Process.** One independent reviewer (a separate agent that did not write the revision), two rounds. The reviewer
edited no files. The round texts are reproduced below as delivered.

| Round | Commit reviewed | Verdict |
|---|---|---|
| 1 | `ba26c940` (diff from `025bfc16`) | NOT ACCEPTED (4 MAJOR, 6 MINOR) |
| 2 | `457a097a` (diff from `ba26c940`) | ACCEPTED (3 MINOR) |
| — | `ee1c45fa`: the round-2 minors, applied after acceptance | not re-reviewed |

---

## Round 1 (commit `ba26c940`)

Review of `docs/r1/reports/TRACKS_PILOT_FINDINGS_APPENDIX_DRAFT_20261115.md` at `ba26c940` (branch `mac-tracks-appendix-20261116`), base `025bfc16`. I edited nothing. Line numbers refer to the file at `ba26c940`.

**What I checked**
- **Parts 2–3 are unchanged by the errata.** I diffed rev 2 (`025bfc16`, which is byte-identical to `9ae6d877` for this file) against rev 3 (`77f49584`). The errata change four places: §1 (U-independence removed; the no-mass-at-zero condition added), the §2 statement preamble ("no independence between U and W needed"), part 4 (the μ_n = 0 bullet: for g > 0 skip is strictly better; the H_n separation condition), and 10(a′)/10(c). Parts 1–3 of 8′ are textually identical in rev 2 and rev 3. Line 27 is therefore right in substance.
- **Numbers (check 4).** I compared every decimal, multi-digit and % token below the `## A.x` heading between the two commits. They are identical; the only extra tokens are "§A.x.4" and "S02". I spot-checked table values against `TRACKS_S05_SUMMARY_20261115.md` §4: 429/399, 148/170/53, 158/192/51, 2.58–2.61 and 4.04–4.06, 0.036 and 0.018, the m̂ percentiles, 46/38 and 94 %/100 % all match. No number changed.
- **R1 (ii) sentences (lines 104–107).** They match R1-T4-PROOF-CHECK ("实际 loop 不在 10(a′) 覆盖范围内，campaign 收益按实测报告"; 8′ values computed conditional on e's posterior) and rev 3 §5 R1.

**Findings**

1. **MAJOR — Parts 2–3 drop "immediate" (and "best"), so the per-decision statements can be read as total-value statements (lines 80–88).**
   - Rev 3 says part 2 is about "the **best immediate** payoff of executing" and part 3 about "the **immediate conditional** gain at this history".
   - The draft writes "Executing pays V\*_n − g in expectation" (l. 80) and "the gain at that history is (g − V\*_n)⁺" (l. 81–82).
   - It then concludes "screening this decision gains nothing" (l. 86) and "skipping it gives up V\*_n − g > 0 in expectation, whether the skip comes from a forecaster or from a dynamic threshold" (l. 87–88).
   - Without "immediate", l. 86–88 read as statements that a skip is worse overall. That is exactly the trajectory or campaign reading that 10(b)/10(c) refute: a dynamic threshold may skip for feedback, information or budget reasons.
   - "Immediate" is the qualifier that makes the statement per-decision, which is what the authority requires.
   - Fix: restore the rev 3 wording: "the best immediate payoff of executing (with the part-1 keep) is V\*_n − g", "immediate conditional gain", "gives up V\*_n − g of immediate expected payoff", "screening this decision has zero immediate gain".
   - Also (minor, same lines): rev 3 says "execute if V\*_n > g, skip if V\*_n < g, either at equality". "Execute iff V\*_n > g" (l. 80) turns the tie case into a necessary condition. Similarly "keep iff m_n > 0" (l. 76) should read "keeping iff m_n > 0 is optimal".

2. **MAJOR — The list of where else value can come from leaves out feedback (lines 97–99).**
   - "Any value a dynamic E1 rule could add at a decision must come from budget or information effects that Proposition 8′ does not cover."
   - Rev 3 names three channels: no feedback (NF; 10(b), the proposer reacting to execute/keep decisions or the display), no information (NI; 10(c)), and budget coupling (R2). The sentence omits feedback, so its "must come from" claim is wrong as stated.
   - It also edges toward a campaign-level statement: it says where a dynamic rule's value could arise.
   - Fix: "Proposition 8′ says nothing about a decision's effect on later decisions — through the proposer's reaction (feedback, (NF)), through what an execution reveals (information, (NI)), or through the budget (R2). Any such effect is outside its scope."

3. **MAJOR — The duplicate case is attributed to 8′ part 4 and given V\*_n = 0, which neither part 4 nor T4 supports (lines 91–94; also l. 27–28).**
   - Rev 3 part 4 covers detectable no-ops (π_n = 1) and the known-increment case (τ_n = 0). It says nothing about duplicates.
   - T4 §1 (`025bfc16:docs/r1/theory/T4_FEEDBACK_PROPOSER.md` l. 24) says the opposite: for a duplicate "**Δ_n is generally not 0**", and duplicates are explicitly not no-ops (l. 79).
   - Corollary 8a (ii)–(iii) reaches "skip optimal for g > 0" by a different route: a duplicate run returns the ledger metric, carries no information, and under ρ can never be kept, so executing pays 0 − g. That is not "V\*_n = 0" in 8′'s Bayes-keep sense.
   - Separately, "part 4 as corrected" (l. 94) and "where the corrected wording is used" (l. 28) mis-target the erratum. The π_n = 1 bullet already read "skipping is optimal for g > 0 (a tie at g = 0)" in rev 2. Erratum (2) corrected the τ_n = 0, μ_n = 0 bullet.
   - Fix: split the paragraph.
     - **No-op:** "a rule-detected no-op has π_n = 1, so V\*_n = 0, and for g > 0 skipping is strictly better (8′ part 4; part 3 gives immediate gain g)."
     - **Duplicate:** "a rule-detected duplicate on a bit-exact node returns the metric already in the ledger, carries no information and under the keep rule ρ is never kept, so executing it pays −g; for g > 0 skipping is optimal (T4 Corollary 8a (ii)–(iii))."
     - Adjust l. 27–28 to match.

4. **MAJOR — "A2-U does not model e (`R1-TRACKS-S02` (g)), which is one more reason its index is not V\*_n" (lines 107–108) has the wrong source and adds a claim about A2-U.**
   - (a) R1-TRACKS-S02 (g) says only that "the incumbent-error model (T4 revision R1) is not needed by Track S and stays open for the proof check" (draft D8: "Track S measures empirically and does not need the model"). It says nothing about A2-U's structure.
   - The fact itself is true. A2-U's declared model (`proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` l. 123–129) is a hierarchical normal model of the increment per (key, sign), updated from executed Δ̂, with no incumbent-error term. But (g) is not the source for it.
   - (b) "One more reason its index is not V\*_n" is a new statement about A2-U as a forecaster. R1-TRACKS-STOP4-END says the appendix "如实报告 A2-U 校准失败，不对 A2-U 本身作任何主张", and the draft's own l. 170–172 rules out claims about A2-U beyond the gate failure and the description of its pilot behaviour.
   - (c) "One more reason" also implies the gate failure shows the index *is not* V\*_n. §A.x.4 says only that it is "not validated" (l. 166).
   - (d) This is new content, beyond "per-decision wording only".
   - Fix: keep "Under that model, V\*_n is computed conditional on the posterior of the incumbent's error e." Delete the A2-U clause. If a pointer is wanted: "A2-U's declared model has no incumbent-error term (runbook §…); this section makes no claim about how its index relates to V\*_n."

5. **MINOR — The status and conditions-for-use text certifies its own compliance and leaves out a pending dependency (lines 22–28, 35–36).**
   - It does not claim manuscript approval, and l. 5 and l. 16 correctly leave that to the author.
   - But "The same row sets the condition this revision meets" (l. 24) is the AI author's own judgement, and findings 1–3 show the condition is not yet fully met.
   - The section quotes the corrected part 4 from rev 3, which sits on unmerged branch `mac-t4-errata-20261116` under separate review. The conditions should say so.
   - "The hold … therefore no longer applies" (l. 23) is literally right about item 5's trigger. Still, the proof-check row only says the appendix "可按…修改" (may be revised), subject to its condition.
   - Fix: "…sets the condition this revision is meant to meet (for review and the author to judge)". Add: "The theory text quoted is revision 3 (`77f49584`, under independent review, not on main); if that review changes part 4, §A.x.2 follows it." Pin `77f49584` in Sources (l. 35–36).

6. **MINOR — Two limits are attributed to the wrong row (l. 11, l. 101), and l. 27 is imprecise.**
   - "Three limits apply (`R1-T4-PROOF-CHECK`)" and "the scope limits the proof check sets". The fixed-price/hard-budget limit comes from R1-T4-DI-FIX (4) and proposal §5 R2, not the proof check. The A2-U clause comes from neither.
   - L. 27 says "§1 of the proposition". It should be "§1 of the proposal, the statement preamble and part 4 of the proposition".
   - Fix: cite each limit to its own source.

7. **MINOR — "Track S measured none" (l. 105–106) is loose.**
   - The pilot did record campaign outcomes, including the between-policy sd of 0.
   - Fix: "Track S reports none: its evidence phases did not run, and its pilot records are ENGINEERING_ONLY (RUNBOOK §1)."

8. **MINOR — The descriptive campaign-level pilot numbers fit, with one wording risk (l. 122–124, 132–134, 175–180).**
   - The identical action sequences, identical truncation results and between-policy sd = 0 are the grounds R1-TRACKS-STOP4-END itself cites for the stop. As a disclosure of why Track S stopped they are compatible with "no campaign-level conclusion" and with STOP4-CONSEQUENCES item 9.
   - L. 134 handles this correctly: "a description of the pilot records, not a statement about the value of either policy over a campaign".
   - Remaining risks:
     - (a) The table row "Between-policy sd of the campaign outcome … 0; 0" reads like a comparison result. Annotate it as "mechanically implied by the identical action sequences; not a comparison of the policies".
     - (b) "What the pilot shows" (heading l. 112, l. 175) is result-style language. Use "What the pilot records show" (as l. 134 does) and frame l. 176–180 as the reason for stopping.

9. **MINOR — Internal consistency of "every E1 decision" and "eligible" (l. 114, 119, 129, 178).**
   - L. 178 says "every E1 decision of the pilot policies was in the configuration … for a low price". But the 429/399 duplicate skips (l. 121) are E1 decisions with V\* = 0 < g. It should say "every eligible (non-duplicate) E1 decision".
   - Pre-existing and outside this revision's scope, but relevant: the summary has 318 (digits) and 350 (tabular) non-duplicate executions against 298 and 330 "eligible" E1 decisions. So "eligible (non-duplicate)" in l. 119 equates two different sets, and l. 114 ("every eligible") and l. 129 ("every valid … non-duplicate … executed") refer to different sets. Define "eligible" once, or drop the parenthetical.
   - Also l. 132: "that rule took the same action" — there are two rules. Say "the two E1 rules took the same action as each other at every E1 decision".

10. **MINOR — Clarity.**
    - L. 76 uses m_n without defining it. Rev 3 defines it as E[Δ_n | O_n ∨ σ(H_n)]; add "given O_n and the result H_n".
    - L. 89, "the only part of the decision that carries value is the E2 keep": better "the only choice with value still at stake is the E2 keep".
    - L. 53–55: the line break after "The" is a leftover from the edit (cosmetic).

**Summary against the six checks**
1. **Campaign-level conclusions:** l. 86–88 (via finding 1) and l. 97–99 (finding 2) still need fixing. The descriptive pilot numbers are acceptable with the annotations in finding 8.
2. **Statements of 8′:** parts 2–3 are unchanged by the errata, but the draft's wording of them drops "immediate". The part 4 duplicate attribution and the "as corrected" target are wrong (findings 1 and 3).
3. **R1 (ii) and the A2-U claim:** the R1 (ii) sentences are supported. The A2-U/e claim has the wrong source and oversteps (finding 4).
4. **Numbers:** none changed.
5. **Status text:** it does not claim approval, but it self-certifies and omits the rev 3 dependency (finding 5).
6. **Consistency and clarity:** findings 6–10.

VERDICT: NOT ACCEPTED

### Author's response to round 1 (commit `457a097a`)

All ten findings applied. §A.x.2 was rewritten: immediate-payoff wording of parts 2–3 with the tie case and "keeping
iff m_n > 0 is optimal"; m_n defined; the three uncovered channels (feedback/(NF)/10(b), information/(NI)/10(c),
budget/R2) stated as outside 8′'s scope; the no-op via part 4 (π_n = 1) and Corollary 8a (i), the duplicate via T4 §1
and Corollary 8a (ii)–(iii); the A2-U/e clause removed; each limit cited to its own row. The status text now says
"meant to meet, for review and the author to judge" and states the dependency on revision 3. "Track S reports none";
"eligible" defined against 318/350 executions; "What the pilot records show"; the sd row annotated; "the two rules …
as each other"; the line-break leftover removed.

---

## Round 2 (commit `457a097a`)

All 10 round-1 findings are fixed at `457a097a`, and I found no new BLOCKING or MAJOR issue. What remains is three minor points the author can apply without a further review round. I edited nothing. Line numbers refer to the file at `457a097a`.

**Did the T4 revision-3 move to `fba64218` break any quote?** No. In `fba64218`, parts 1–3 and the π_n = 1 bullet of part 4 read exactly as in `77f49584` and in rev 2. Only the τ_n = 0 bullet changed ("keep iff m_n > 0", plus the iff identification condition). The appendix no longer quotes that bullet: it uses part 4 only for π_n = 1 (l. 30–31, l. 102–103). Its wording still matches `fba64218`:
- Part 1, l. 84–85: the definition of m_n matches §1.
- Part 2, l. 88–89: "best immediate expected payoff … with the part-1 keep", including the tie case.
- Part 3, l. 90–91: "immediate conditional gain".
- Part 4, l. 102: "strictly better" follows from part 2, since V\*_n − g = −g < 0.
- l. 29–30 correctly says the errata change §1, the statement preamble, part 4 and 10(a′)/10(c), and not parts 1–3.

**Numbers.** Every data number below `## A.x` is the same as at `025bfc16`. The only new numbers are 318 and 350. Both equal keep + discard (148 + 170 and 158 + 192) and the summary's E1 execute counts (`TRACKS_S05_SUMMARY_20261115.md` l. 109). The other new tokens are "10(b)", "10(c)" and "§A.x.4".

**Round-1 findings**
1. **Immediate wording (MAJOR): fixed.** l. 82 and 88–97 now say "immediate" throughout, including the tie case and "keeping iff m_n > 0 is optimal".
2. **Missing feedback channel (MAJOR): fixed.** l. 111–114 name all three channels: feedback/(NF)/10(b), information/(NI)/10(c), and budget/R2, the last as "outside its scope". 10(b) is the proposal's (NF)-failure example, so the citation is right.
3. **Duplicates attributed to part 4 (MAJOR): fixed.** I checked each new citation:
   - The no-op bullet (l. 102–103) matches Corollary 8a (i): "π_n = 1, so V\*_n = 0, skipping is optimal for every g > 0".
   - The duplicate bullet (l. 104–106) matches T4 §1 l. 24 ("Δ_n is generally not 0") and Corollary 8a (ii): "carries no information and its value is 0 − g". It also matches (iii): "under ρ a duplicate can never be kept".
   - l. 31 now says part 4 is used only for the unchanged π_n = 1 bullet.
4. **A2-U/e claim (MAJOR): fixed.** The claim is removed. l. 122–124 restates R1 (ii) correctly and now makes no claim about A2-U ("no claim about how A2-U's index relates to V\*_n beyond §A.x.4").
5. **Status text certifying its own compliance (MINOR): fixed.** l. 25–26 now say "meant to meet, for review and the author to judge". l. 32–33 state the dependency on rev 3. See new point A.
6. **Limits cited to the wrong rows (MINOR): fixed.**
   - Fixed price is cited to `R1-T4-DI-FIX` (4), which says hard run budgets are excluded from every theorem, and to R2.
   - Per-decision and Bayes quantity are cited to `R1-T4-PROOF-CHECK`.
   - l. 29 is precise.
7. **"Measured none" (MINOR): fixed.** l. 121 now reads "Track S reports none … ENGINEERING_ONLY (RUNBOOK §1)", which matches RUNBOOK §1 and STOP4-CONSEQUENCES item 9.
8. **Descriptive campaign-level numbers (MINOR): fixed.**
   - The sd row is annotated as implied by the identical sequences (l. 141). At W = 12 this is backed by the identical-truncation row at l. 140.
   - The headings now read "What the pilot records show", and l. 193 adds "as the reason Track S stopped".
9. **"Every E1 decision" and "eligible" (MINOR): fixed.**
   - l. 196 says "every eligible E1 decision".
   - l. 136 drops "(non-duplicate)".
   - l. 74–75 discloses 298/330 eligible against 318/350 executions.
   - l. 149 says "the two rules … as each other".
10. **Clarity (MINOR): fixed.** m_n is defined (l. 84), and "the only choice … with value still at stake" is at l. 98.

**Checked for new claims.** Nothing new is claimed about A2-U. l. 74–75 is descriptive, l. 123–124 is a non-claim, and l. 131 keeps the existing "(not the Bayes V\*_n)", which agrees with §A.x.4's "not validated". There is no new campaign-level conclusion: l. 108–109 is a per-decision conditional, and l. 111–114 and l. 117–121 are scope statements.

**New points**
- **A. MINOR: the rev-3 status is out of date (l. 32–33, 40–41).** The text says rev 3 is "under independent review" and pins only `77f49584` as "first reviewed". You report that the review was accepted at `fba64218`; I found no review file for it in the repo, so I am relying on your report. `fba64218` is still not on `gh/main`, so "not on `main`" is correct.
  - Suggested fix: "revision 3 (`mac-t4-errata-20261116` @ `fba64218`, review accepted; not yet on `main`)". Keep the "§A.x.2 follows it" clause, to cover the merge.
- **B. MINOR, optional: say why 20 executions per node are not eligible (l. 74–75).** "Eligible" is a per-decision flag in the ledger, which the summary scripts read (`policy_diag.py` l. 49, `diag1.py` l. 26), so "the summary's term" is slightly loose. The design runbook (`TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` l. 202) says "Duplicates, no-ops and trial 1 are not eligible". The gap of exactly 20 per node (one per instance) fits trial 1. I did not confirm this from the ledgers.
  - Suggested fix, if confirmed: "(trial 1 of each campaign is not eligible)".
  - This also explains why l. 196–197 pair "every eligible E1 decision" with "each valid non-duplicate proposal executed". The second phrase also covers the 20 trial-1 executions, which the V\* statement does not cover.
- **C. MINOR, cosmetic: line wrapping.** l. 60 is one overlong line. l. 149–151 has a broken wrap ("So their" / "action sequences").

VERDICT: ACCEPTED

### Author's response to round 2 (commit `ee1c45fa`, after acceptance)

A: revision 3 is now pinned as `mac-t4-errata-20261116` @ `fba64218`, review accepted
(`reviews/T4_PROP10_REVISION3_REVIEW_20261116.md` on that branch), not yet on `main`; §A.x.2 follows the merged
version. B: "eligible" is described as the per-decision ledger flag read by the summary scripts (`policy_diag.py`,
`diag1.py`). The trial-1 explanation was not added, because the runbook line cited is the S3a fork-point rule and the
ledgers were not checked. C: the two wraps are fixed. Not re-reviewed.

---

Accepted commit: `457a097a` (round 2). Final draft commit including the round-2 minors: `ee1c45fa`.
