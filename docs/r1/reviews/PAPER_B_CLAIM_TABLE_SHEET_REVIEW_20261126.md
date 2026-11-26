# Review: Paper B revised outline and claim-to-table sheet

- **Reviewed:** `docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md` at commit `3a402490` (task `writer/20261126-03`).
- **Checked against, all at `3a402490`:** `papers/r1/main.tex`, `generated/numbers.tex`, the fourteen section files (the thirteen named plus `app_related.tex`), `docs/r1/PLAN.md` §10, `canon/PAPER_B_PLAN.md` §1, §2, §4, and §6 of `GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md`. `papers/r1` is identical at `6b72e27c` and `3a402490`.
- **Reviewer:** an AI agent (Claude) that did not write the unit. Everything was read with `git show`; no label, evaluation, test or credential file was opened; nothing in the repository was changed.
- **Tier S:** one fresh review, one correction round.
- **Not done:** the PDF was not rebuilt, so the page figures are checked for arithmetic only. The preregistration and the D.3 pre-declaration draft were not read, so "G7" and the timing of the per-node and per-tier tables (step 5 or step 10) are not verified.

**Verdict: ACCEPT WITH MINOR**

No MAJOR finding. Every macro and label the sheet names exists, the two contrast families match the rows, and no number comes from an unreleased result. The MINOR findings are one internal contradiction, a few rows where the sheet's placement or step is imprecise, items missing from §5, and page figures that do not agree with each other.

## 1. Macros, labels, omissions

1.1 **Passes.** All 71 macros named in the sheet are defined: 68 in `numbers.tex`, and the three switches `\ifRuleGain`, `\ifLearnedGain`, `\ifGatePassed` in `main.tex` (the sheet calls them switches, which is right). All 27 labels named exist and are referenced. The `SOne/STwo` shorthand covers the five `…STwo` macros.

1.2 **MINOR. `\ResultNoiseFloor` is both used and unused.** Row N1 lists "`\NoiseFloorTable`, `\ResultNoiseFloor`" as its macros; the line under §3.4 says "Unused in the text after the restructure: `\ResultOfflineGate`, `\ResultNoiseFloor`". The manuscript uses neither `\Result…` macro. Fix: delete `\ResultNoiseFloor` from N1.

1.3 **MINOR. Macros listed against a table that does not hold them.**
- L2 and L3 name only `tab:decomp`, but `\LoopYATwo` and `\LoopYAOne` occur only in `tab:closed` (`appendix.tex`). Fix: add `tab:closed` to both rows.
- L7 names `fig:budget`, `tab:app-mech`, but its four macros (`\LoopRunsToMatch`, `\LoopDupShareAZero`, `\LoopRuleSkips`, `\LoopValueSkips`) occur only in the prose of §6.1; the figure and the table hold `\FigShell` and `\Cell`. Fix: add "§6.1 text".
- X1: `\LoopRankAgreement` occurs in the §6.3 prose, not in `tab:app-agree`. Fix: add "§6.3 text".
- C1: `\COneHeadline` is in the introduction and `\SweepTwoAuditCounts` in the design appendix (audit protocol). Fix: name both places.

1.4 **MINOR. Design-value macros have no row.** `\LoopW`, `\LoopCalls`, `\LoopInstances`, `\LoopAuditK` (block (a2)) are used in `setup.tex`, `results.tex`, `limitations.tex`, `app_design.tex`. `numbers.tex` says "They are checked against the signed pre-declaration (revision 4) before submission." Fix: add a row (level: committed row values, R1-MINSUB-CHOICES (4), R1-D3-CHOICES (2); confirmed at step 7).

1.5 **NOTE. Omitted and not result macros:** `\SweepOne…` (six), `\SweepTwo…` (five; `\SweepTwoAdmittedErrors` is unused in the text), `\ExTenCSlope`, `\ExTenCProbeValue`, `\PilotTOne…` (four), `\FigShell`. Only the first and the pilot appear in §5 item 10; see 5.2.

1.6 **NOTE. Omitted result figure:** `fig:ladder` (`app_results_main.tex`, utility per arm and tier) belongs in G2. The six `tab:dev-*` tables and `tab:ex-info` carry no result and need no row.

1.7 **NOTE.** L0 omits the guard switches `\ifLoopOutcomeSet` and `\ifGateOutcomeSet` of `main.tex`; they decide whether the draft prints three candidate readings.

## 2. Claim rows

2.1 **Passes.** The families of §3.1 and §6 match the rows: D.3a = each rule arm against A0 (R1-D3-MIN), LADDER against A0 and A2 (R1-MINSUB-CHOICES (4)), A0R − A0 and A2 − A0R (R1-D3-DECOMP), eight contrasts; D.3b = A3 and A5 against A2 and A0 (R1-D3-MIN) and A5 − A3 (R1-D3B-UNCONDITIONAL), five contrasts. "Confirmatory" for D.3 follows canon §1 ("Both confirmatory families"). L7 (a)–(d), X1 (e), X2 (f), L8 (descriptive, outside the Holm families, optional) and L9 (descriptive, optional) match R1-D3-OUTCOMES2, R1-D3-HPO-REF, R1-D3-ORDER and R1-STEP-ORDER (2)(c). Steps 5, 9 and 10 are cited as canon §4 numbers them. `tab:decomp` rows 1 to 7 are as the sheet says.

2.2 **MINOR. L9, "needs step 4 and its own pre-declaration".** D.3c runs A3 and A5, which exist only after step 5's arms-frozen record, and R1-D3-ORDER also requires "its own pre-declaration and authorization note (tier E) before any run" and a scoping memo first. Fix: "step 9, D.3c (needs steps 4 and 5, the scoping memo, its own pre-declaration and authorization note)". The contrast cell says "none (descriptive)", while `\LoopTOneSummary` and `tab:app-tone` give paired differences of A2, A3, A5 to A0. Fix: "A2, A3, A5 − A0, descriptive, no verdict".

2.3 **MINOR. A6 is missing.** The manuscript carries A6 (method, `app:arms`, `app:closed`, limitations: "Decision-focused fine-tuning (A6) is trained only after a gate that passes"), and R1-D3-MIN puts "A6 against A5, should A6 enter" in the D.3b contrasts; R1-D3B-UNCONDITIONAL says "A6 stays as R1-D3-MIN states". Neither §3.1 nor the D.3b list in §6 mentions it. Fix: add a conditional row (A6 − A5, D.3b, only after a passing gate, optional, no macro or table yet) and the same clause in §6.

2.4 **MINOR. C1c is not marked optional.** R1-CONTROLS-ROW: "Optional under R1-SUBMISSION-MIN's 3 Jan rule", and R1-STEP-ORDER (2)(c) lists "the controls" among optional items. Fix: "descriptive, optional" in the level cell.

2.5 **MINOR. G2 states `tab:app-secondary` as a settled step-10 read.** The table's own caption has "\TBD{… whether the test reads of these arms are inside the preregistered scope.}", it has a TabPFN column although canon §2 lists "the information-matched TabPFN comparison" as cut, and R1-D3-MIN says "an arm reads test only if it is in the arms-frozen record and inside the preregistration's PRE-SECONDARY scope". Fix: mark the row "scope open" and add it to §5 or §6.

2.6 **MINOR. T3 gives one status for two statements.** "PROOF (AI-checked), in the appendix" covers `prop:bias` and `prop:failures`. The status note in `app_theory_main.tex` gives `prop:bias` and `prop:failures`(a) as AI-checked, and `prop:failures`(b) as having an author-checked source with AI-checked wording. R1-PROOF-POLICY requires each status to be marked "precisely". Fix: split the cell.

2.7 **MINOR. N1, "steps 1–2 (expansion nodes)".** Step 2 is the G.5 label runs, which produce no noise floor. Noise floors come from G.1b (step 1 for the expansion nodes; canon §3 says the eight nodes are sealed). Fix: "step 1".

2.8 **MINOR. The §6 bullet "a seventh rule arm (R1-D3-CHOICES (1))".** `setup.tex` says "Seven rule arms run" since A0R was added, so an added arm would be the eighth. The row's "seventh D.3a arm" was written before R1-D3-DECOMP. Fix: "an eighth rule arm (the 'seventh D.3a arm' of R1-D3-CHOICES (1), named before A0R was added)". The manuscript's `app_design.tex` has the same wording.

2.9 **NOTE. "Holm within each family" (§1) is stated as fixed.** R1-D3-CHOICES (2) fixes "two-sided tests, Holm within each stage, α = 0.05", but R1-D3B-UNCONDITIONAL says the revised pre-declaration "sets the multiplicity of the enlarged family", and `setup.tex` keeps "\TBD{Multiplicity of the enlarged families, from the signed pre-declaration.}". §6 of the sheet already asks revision 4 for it; add "pending revision 4" in §1.

2.10 **NOTE. L6** is confirmatory by the rows, as the sheet says; `results.tex` calls its paragraph "One descriptive paragraph". The manuscript, not the sheet, needs the change.

2.11 **NOTE. C1** says "definitions signed before any rate is computed"; R1-POSTFREEZE-READS says "before any audit value is read". Use the row's words. `\SweepTwoAuditCounts` is a count of the sweep-2 audit, which canon §3 reports as done, so it may not need to wait for step 10; check.

2.12 **NOTE. Claims of the manuscript with no row:** the two external figures of the introduction (see 5.2), and the case of a statistical STOP of the gate (see 3.4). Every claim of the abstract, the four contributions and the results section otherwise has a row.

2.13 **NOTE.** "G7" (§6) does not occur in PLAN or canon, which name "units G1, G3 to G8 of the draft's §12"; not verified.

## 3. Sections 4 and 5

3.1 **MINOR. §4 cites a result without a source.** "If the screen with a constant forecast makes no value skip at g = 0.1 σ_node (as in the Track S pilot)". The only source found is the proposal's §7 table: "At g = 0.1 σ_node the constant-prior screen makes no value skip on T0 (Track S)". The manuscript does not mention Track S. Fix: cite the Track S report by path, or drop the parenthesis and keep the conditional.

3.2 **MINOR. §4 omits A2 − A0**, the contrast that sets `\ifRuleGain` and so the headline. Fix: add a line (rule layer and one-step rule together; not which of them; its point estimate is the sum of rows 1 and 2 of `tab:decomp`). A2 − A1 is a second undeclared contrast of the 2 × 2 and could sit beside the interaction line. The rest of §4 agrees with R1-D3-DECOMP and `method.tex`.

3.3 **MINOR. Missing from §5: the reading when the gain is the rule layer's.** The readings are keyed to A2 > A0. If A0R − A0 is rejected and A2 − A0R is not, readings 3 and 4 still open with "Noise-aware rule control raises the audited gain" and "Noise-aware rule control is enough", which credits the one-step rule with a gain from de-duplication. The proposal's §6 does not split this case, and `results.tex` only has "\TBD{If most of A2 − A0 comes from the rule layer, say so in those words.}". This changes how a claim is worded, so it belongs in §5 under the sheet's own rule.

3.4 **MINOR. Missing from §5: a gate that ends in a statistical STOP.** `results.tex` says "A statistical STOP of the gate is neither gate branch; its text is not drafted", and `tab:readings` has only pass and fail. Fix: add the item, or cite the row that covers it.

3.5 **MINOR. Item 2 is partly decided.** R1-ALIGN-OUTCOME: "The outcome table of the proposal's §6 is the declared reading", and that table's fifth row ends "Not an ICML submission in the present form." The sheet's "The venue is the author's choice at that point" reads as if the row left it open. R1-STEP-ORDER (3) gives the author the venue choice only "if it is not [complete in time]". Fix: say that the reading is adopted by R1-ALIGN-OUTCOME and that the author is asked only to confirm that the sentence stays out of the paper text.

3.6 **NOTE. Items partly decided by a row; cite it and narrow the question.**
- Item 3: the order follows R1-ALIGN-OUTCOME ("the manuscript's contribution list follows this row") and canon §1; C1 as supporting evidence is R1-C1-POSITION. Only the wording is open.
- Item 6: R1-PROOF-POLICY fixes that each statement is marked "author-checked" or "AI-checked under R1-PROOF-POLICY" and that no text implies an author check that was not made. Only placement and wording are open.
- Item 9: R1-P4-TESTPLAN-DECISIONS (P4-INCID A) fixes that "the paper's deviations list cites it". Only the wording is open, as the sheet says.

3.7 **NOTE. Item 7** is accurate: `tab:app-agree` has A2, A3, A5; R1-POSTFREEZE-READS (a) adds A0 and A1 test rows. LADDER's missing offline read is R1-MINSUB-CHOICES (4), not R1-D3-MIN; add the citation.

3.8 **Passes.** Items 1, 4, 5, 8 and 10 are accurate. The four title options match the comment in `main.tex`. Item 5's "two statements, both with an author-checked source" matches the status note.

## 4. Page figures

4.1 **Passes.** Draft column: 0.15 + 1.0 + 0.9 + 1.1 + 0.9 + 1.6 + 2.2 + 0.4 + 0.45 = 8.70, as stated.

4.2 **MINOR. The draft total disagrees with the stated end of the main text.** "main text ends about one third down page 9" is about 8.3 pages; the column sums to 8.7 and the text below speaks of "the remaining 0.7 page". Fix: reconcile (0.3 or 0.7 to cut) and say how the per-section figures were measured.

4.3 **MINOR. The savings list does not match the Target column.** The Target column sums to 7.95 (stated 8.0) and takes 0.2 page from §6 and 0.55 from §1–§5 and §8. All four listed sources of savings are in §6. Fix: either move the cuts in the Target column to §6 or name where the 0.55 page in the other sections comes from.

4.4 **NOTE.** "A–K | Appendix (as before)": `appendix.tex` has ten sections, so A–J. The contents listed for the appendix rows match the files.

## 5. Unreleased results

5.1 **Passes.** No result value appears in the sheet. Item 10's two facts are committed: `counts.json` of `b2_audit_20261119` gives `proposals_total` 4999 and `duplicates` 3274; `G4B_TASL_PILOT_RESULT_20261125.md` gives 126 of 180 ran and per-node liveness 0.6167, 0.6667, 0.8167 (0.62 to 0.82). Both match `numbers.tex`. The design values (K = 10, W = 20, 80 calls) and the gate power (0.36, 0.26, 0.3) are row values and committed facts.

5.2 **MINOR. Item 10 is headed "Committed facts used in the text" and is incomplete.** The introduction also quotes two external figures, "49.9\% of truly neutral candidates" and "2.7 times a preregistered threshold". R1-C1-POSITION: "figures are checked against the PDFs before the manuscript quotes them". Fix: add them to item 10 with the state of that check. The sweep counts, gate power and failure-example constants could be listed there by macro name for completeness.

5.3 See 3.1 for the one unsourced reference to a result (no figure).

## 6. Language and consistency

6.1 **Passes.** The sheet is plain and consistent in its terms, apart from 1.2, 2.8 and 4.2–4.3.

6.2 **NOTE.** The header cites "R1-STEP-ORDER (3)" (as the task card does); (3) is the venue rule. The rows the sheet relies on are (2)(c) and (2)(d); cite those as well.

6.3 **NOTE.** The header list of rows omits several the body cites (R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-POSTFREEZE-READS, R1-PROOF-POLICY, R1-C1-POSITION, R1-CONTROLS-ROW, R1-D3-CHOICES).

## Deliverables of the task card

All present: claims, table or figure, evidence level, the four named contrasts, macros, filling step, outline with page targets, the statement that no figure comes from an unreleased result, and the list for the author (§5, to be extended by 3.3, 3.4 and 5.2).
