**AI-assisted (Claude, writer, 26 Nov 2026). PROPOSAL, task `writer/20261126-03`. It decides nothing.** The claims,
contrasts and estimands are those of PLAN §10 (R1-ALIGN-OUTCOME, R1-D3B-UNCONDITIONAL, R1-D3-DECOMP, R1-D3-OUTCOMES2,
R1-D3-HPO-REF, R1-D3-ORDER, R1-STEP-ORDER (2)(c), (2)(d) and (3)). Where this sheet words a claim, the wording is a draft for the author.
A point that would change a claim, an estimand, an arm or a contrast is listed in §5 and goes to the author through
the design agent and the coordinator.

# Paper B: revised outline and claim-to-table sheet

Manuscript state: `papers/r1` on branch `writer-20261126-01-manuscript-restructure` @ `e360d425` (the sheet was written against `6b72e27c`; the branch has since had its review rounds, title option 1 and the trim to eight pages)
`54082a05`). No label, test, evaluation or audit output was opened. **The sheet takes no figure from an unreleased
result:** every result cell below is a placeholder macro of `papers/r1/generated/numbers.tex`.

## 1. The line from question to claim

| | |
|---|---|
| Question | At a matched budget of worker runs and manager calls, which control decisions raise the fresh-seed audited gain of a campaign, and by how much? |
| Method | Each arm controls fresh campaigns on the same instances. Four arms cross the rule layer with the one-step rule (A0, A0R, A1, A2). Two arms replace A2's constant forecast with a learned one (A3, A5). |
| Measurement | Y: the final incumbent's audited improvement over the start configuration, K = 10 fresh seeds, in units of σ_node, at W = 20 worker runs and 80 manager calls. Paired differences in Y, two-sided, Holm within each family (R1-D3-CHOICES (2); the multiplicity of the enlarged families is set by revision 4 of the pre-declaration). |
| Claim | The size of each paired difference, with its interval: what the rule layer adds, what the one-step rule adds, what a learned forecast adds. Which of the five declared readings applies (Table `tab:readings`). |
| Separate claim | Offline, on logged proposals, a learned forecast improves one-step decisions against A2 (the preregistered gate, read once). It answers a different question and does not decide which arms run. |

## 2. Revised outline with page targets

Pages are those of the draft build with the gate not passed (43 pages in total at `e360d425`; after the trim of 27 Nov the main text ends on page 8, which meets the target; the per-section "Draft pages" column below was measured before the trim at `6b72e27c`, about 8.7 pages; 23 Nov build: about 20 pages). The limit of the 2026 style is eight pages of main text.

| § | Section | Content | Draft pages | Target |
|---|---|---|---|---|
| — | Abstract | question, design, outcome, two results | 0.15 | 0.15 |
| 1 | Introduction | the loop; two ways to lose budget; the question; the measurement; contributions in the order closed loop, gate, C1, theory | 1.0 | 0.9 |
| 2 | Problem formulation | governed loop (E1, E2), observation model, the outcome Y, the priced objective, three levels of evidence | 0.9 | 0.8 |
| 3 | The one-step rule and its scope | Proposition (one-step index), (NF), (NI), Theorem (reduction), why the campaign is measured | 1.1 | 1.0 |
| 4 | Method | rule layer, forecast, rule, table of arms | 0.9 | 0.8 |
| 5 | Experimental design | nodes, sweeps and audits; the closed loop; the offline gate; declared readings (table) | 1.6 | 1.5 |
| 6 | Results | headline; decomposition table; learned arms; budget curve; gate table; agreement; control errors | 2.2 | 2.0 |
| 7 | Related work | three paragraphs; full text in the appendix | 0.4 | 0.4 |
| 8 | Limitations | closed loop, gate, theory, nodes and labels, open points | 0.45 | 0.4 |
| | **Main text** | | **about 8.7** | **about 8.0** |
| A–J | Appendix (as before) | deviations (now six tables), scope, further theory, proofs, further results, exams, compute, disclosures | | |
| new | Design details | DAC mapping, proxy caveat, C1 definitions, node qualification, T1 node set and pilot, sweeps, audit protocol, arms, the gate in full, closed-loop design values, hardware and timing | | |
| new | Theory moved from the main text | status note, remarks, selection bias of the record, (NF) conditions, failure examples, scope | | |
| new | Full reports | C1 in full, the ladder and gate in full for both outcomes, secondary analyses | | |
| new | Extended related work | the 23 Nov text | | |

The targets take about 0.2 page from §6 and about 0.5 page from the other sections, 0.05 to 0.1 page each. In §6:
(1) the draft prints three candidate headline readings where the final build prints one (about 0.15 page); (2) the
long placeholder notes become shorter prose. If more is needed: (3) the figure of the budget curve and the gate table
can share one float; (4) the control-error subsection can shrink to three sentences. Elsewhere the saving is
line-level tightening. None of this changes a claim.

## 3. Claim-to-table sheet

Evidence levels: **DEV** development (training and development instances; selects and calibrates; supports no claim),
**GATE** the preregistered offline gate, **LOOP** the closed loop D.3, **LOG** logged sweeps scored against audits
(C1), **PROOF** a mathematical statement. "Step" is the step of `canon/PAPER_B_PLAN.md` §4 whose completion fills the
macros.

### 3.1 Closed loop (headline; R1-ALIGN-OUTCOME)

| # | Claim as the paper words it | Contrast | Table or figure | Level | Macros | Filled after |
|---|---|---|---|---|---|---|
| L1 | What the rule layer adds under the default keep rule | A0R − A0 | `tab:decomp` row 1; `tab:closed` | LOOP, confirmatory (D.3a family) | `\LoopDAZeroRvAZero`, `\LoopYAZero`, `\LoopYAZeroR` | step 9, D.3a (needs steps 6–8) |
| L2 | What the one-step rule adds once the rule layer is in place | A2 − A0R | `tab:decomp` row 2 | LOOP, confirmatory (D.3a) | `\LoopDATwovAZeroR`; mean in `tab:closed`: `\LoopYATwo` | step 9, D.3a |
| L3 | The one-step rule without the rule layer; both together | A1 − A0; A2 − A0 | `tab:decomp` rows 3–4 | LOOP, confirmatory (D.3a) | `\LoopDAOnevAZero`, `\LoopDATwovAZero`; mean in `tab:closed`: `\LoopYAOne` | step 9, D.3a |
| L4 | What a learned forecast adds to the rule-based arm | A3 − A2; A5 − A2 (also A3 − A0, A5 − A0) | `tab:decomp` rows 5–6; `tab:closed` | LOOP, confirmatory (D.3b family) | `\LoopDAThreevATwo`, `\LoopDAFivevATwo`, `\LoopDAThreevAZero`, `\LoopDAFivevAZero`, `\LoopYAThree`, `\LoopYAFive` | step 9, D.3b (needs step 5's arms-frozen record; not the gate verdict) |
| L5 | The two full forecasting arms against each other (model and input differ) | A5 − A3 | `tab:decomp` row 7 | LOOP, confirmatory (D.3b) | `\LoopDAFivevAThree` | step 9, D.3b |
| L6 | Three rules from the literature at the same budget, charged for their runs | FIXR3, EGATE, LADDER − A0; LADDER − A2 | `tab:closed` | LOOP, confirmatory (D.3a) | `\LoopYFixR`, `\LoopYEGate`, `\LoopYLadder`, `\LoopDFixRvAZero`, `\LoopDEGatevAZero`, `\LoopDLaddervAZero`, `\LoopDLaddervATwo` | step 9, D.3a |
| L7 | Where the gain comes from and what it costs | none (descriptive) | §6.1 prose (the macros); `fig:budget`, `tab:app-mech` (cells) | LOOP, descriptive (R1-D3-OUTCOMES2 (a)–(d)) | `\LoopRunsToMatch`, `\LoopDupShareAZero`, `\LoopRuleSkips`, `\LoopValueSkips` | step 9 and the Y(w) audits |
| L8 | Classical configuration methods as the proposer | none (descriptive rows) | `tab:closed`, last block | LOOP, descriptive, optional | `\LoopYRandom`, `\LoopYSmac` | the HPO reference unit; enters only if complete (R1-STEP-ORDER (2)(c)) |
| L9 | Code-level edits: A0, A2, A3, A5 on three T1 nodes | A2, A3, A5 against A0, paired, descriptive, no test | §6.1 prose (the macro); `tab:app-tone` | LOOP, descriptive, optional | `\LoopTOneSummary` | step 9, D.3c (needs step 4 for the labels, step 5 for the frozen A3 and A5, and its scoping memo, pre-declaration and authorisation note, R1-D3-ORDER) |
| L10 | Decision-focused fine-tuning, only if it was trained after a gate that passes (R1-D3-MIN, unchanged) | A6 − A5 | appendix `app:closed`; no table shell and no macro yet | LOOP, D.3b family if A6 enters | none | step 9, D.3b, after A6's own frozen record |
| L11 | Design values of the closed loop | — | §5.2 | committed design values, checked against the signed pre-declaration | `\LoopW`, `\LoopCalls`, `\LoopInstances`, `\LoopAuditK` | step 7 |
| L0 | The headline sentence (one of five readings) | set by L3, L4 and G1 | §6 "Headline"; `tab:readings` | LOOP + GATE | `\LoopHeadline`; switches `\ifRuleGain`, `\ifLearnedGain`, `\ifGatePassed` | steps 5 and 9 |

### 3.2 Offline gate (the one-step claim; R1-SWEEP2-PREREG, unchanged)

| # | Claim | Contrast | Table or figure | Level | Macros | Filled after |
|---|---|---|---|---|---|---|
| G1 | A learned per-proposal forecast improves one-step decisions on logged proposals against A2 | A3 and A5 against A2: IQM of gap closed, PoI; Holm, one read | `tab:gate` (main); `tab:ladder` (appendix) | GATE, confirmatory | `\GateVerdict`, `\GatePassingArms`, `\GateHolmFirst`, `\GateIQMAThree`, `\GatePoIAThree`, `\GateIQMAFive`, `\GatePoIAFive`, `\GateReadDate`, `\GateEligibleNodes`, `\GateExcludedNodes`, `\GateDupLeftOut`, `\TOneNodesUsed` | step 5 (the one read) |
| G2 | The ladder and the secondary analyses | none (descriptive) | `tab:ladder`, `tab:sens`, `tab:loso`, `tab:app-gate-nodes`, `tab:app-secondary`, `tab:app-lono`, `tab:app-sweep1` | GATE, descriptive | table cells (`\Cell`); also `fig:ladder` | step 10 (test release, post-freeze reads). `tab:app-secondary` still carries a placeholder on whether its test reads are inside the preregistered scope, and a TabPFN column whose information-matched form is cut (R1-SUBMISSION-CUTS); both are checked before the read |
| G3 | If the gate does not pass: how far per-proposal thresholds spread around A2's | none (an estimate, not a bound on learning) | `tab:app-dispersion` | GATE, descriptive | `\DispBoundAThree`, `\DispBoundAFive` | step 10 |
| G4 | The gate's power, as simulated | — | §5.3 | committed fact | `\GatePowerMain`, `\GatePowerSmallTOne`, `\GatePowerEffect` | filled |

### 3.3 The two levels together

| # | Claim | Contrast | Table | Level | Macros | Filled after |
|---|---|---|---|---|---|---|
| X1 | Whether the arms order the same way offline and in the loop | none (rank agreement) | §6.3 prose (the macro); `tab:app-agree` (cells) | GATE + LOOP, descriptive (R1-D3-OUTCOMES2 (e)) | `\LoopRankAgreement` | steps 9 and 10 |
| X2 | Whether learning matters more with code-level edits | A5 − A3 and A5 − A2 by tier | `tab:app-tier` | GATE, descriptive (R1-D3-OUTCOMES2 (f)) | table cells | step 10 |

### 3.4 Supporting evidence and theory

| # | Claim | Table | Level | Macros | Filled after |
|---|---|---|---|---|---|
| C1 | Control errors of the default loop against audited increments: false keeps, missed keeps, record bias, wasted runs; two proposers. Supporting, not a first measurement (R1-C1-POSITION) | §6.4; `tab:c1`, `fig:c1`, `tab:app-dup` (appendix) | LOG, descriptive, definitions signed before any rate is computed (R1-POSTFREEZE-READS) | `\COneHeadline`, `\COneFalseKeepSOne/STwo`, `\COneFalseKeepRange`, `\COneMissedKeepSOne/STwo`, `\COneRecordBiasSOne/STwo`, `\COneWastedSOne/STwo`, `\COneDupSOne/STwo`; `\COneHeadline` is in the introduction and `\SweepTwoAuditCounts` in the design appendix | step 10; the partial form if the T0 test release row does not exist when the paper is assembled |
| C1c | The audit can see a known effect (positive control) | `tab:app-controls` | accepted noise-floor runs, descriptive, optional (R1-CONTROLS-ROW; R1-STEP-ORDER (2)(c)) | `\COnePositiveControl` | merge of the reviewed controls unit |
| T1 | The one-step rule under a run price | Proposition `prop:onestep` | PROOF (source author-checked; closed form AI-checked) | — | disclosure wording is the author's |
| T2 | When the rule is optimal for the campaign | Theorem `thm:reduction` | PROOF (source author-checked) | — | one comparison of the manuscript wording with its source is still open |
| T3 | Why the campaign is measured: reused incumbent score, ledger-reading proposer, hard budget | §3 scope; appendix: `prop:bias`, `prop:failures` | PROOF, in the appendix: `prop:bias` and `prop:failures`(a) AI-checked under R1-PROOF-POLICY; `prop:failures`(b) AI-checked as worded, with an author-checked source | `\CRNThresholdShiftDigits` | the T5 correction round on `main` |
| D1 | Forecast skill that selected each learned arm | `tab:app-devskill` | DEV | table cells | step 5 (arms-frozen record) |
| N1 | Noise floors and the screening funnel | appendix design details | committed records | `\NoiseFloorTable` | step 1 (expansion nodes; the eight nodes' floors are sealed) |

Unused in the text after the restructure: `\ResultOfflineGate`, `\ResultNoiseFloor` (kept from the skeleton).

Correction round, 26 Nov 2026: the eighteen MINOR findings and the notes of
`docs/r1/reviews/PAPER_B_CLAIM_TABLE_SHEET_REVIEW_20261126.md` (ACCEPT WITH MINOR) are applied in this file.

## 4. Arm contrasts and what each one identifies

| Contrast | Identifies | Does not identify |
|---|---|---|
| A0R − A0 | the rule layer (skip duplicates and detectable no-ops) under the default keep rule | anything about noise-aware decisions |
| A2 − A0R | the one-step rule with one constant forecast per node, once duplicates are removed | which of the two thresholds acts. If the screen with a constant forecast makes no value skip at g = 0.1 σ_node (the proposal's §2 M2 reports this for the Track S pilot, R1-TRACKS-STOP4-END; engineering data, not a result), this is the keep threshold alone; the mechanism counts say so |
| A3 − A2, A5 − A2 | a per-proposal forecast in place of the constant forecast, same rule and rule layer | the cause of a difference between A3 and A5 |
| A5 − A3 | the difference between the two full forecasting arms | model family against input: A5 reads the proposal text (on T1 an excerpt of the diff) and A3 does not |
| A1 − A0 | the one-step rule without de-duplication | — |
| A2 − A0 | rule layer and one-step rule together. This contrast sets `\ifRuleGain` and so the headline reading | which of the two parts the gain comes from; that is A0R − A0 and A2 − A0R |
| (A2 − A0R) − (A1 − A0) | the interaction of rule layer and one-step rule | **not a declared contrast.** The paper does not report it unless the pre-declaration adds it |

## 5. For the author to confirm or decide

Each item is a claim or a reading that the manuscript now words and that the rows do not fix word for word.

1. **What "A2 > A0" and "A3 or A5 > A2" mean in the five readings.** The proposal's §6 does not say. Draft
   operational reading: the Holm rejection, in the favourable direction, of A2 − A0 in the D.3a family; and of
   A3 − A2 or A5 − A2 in the D.3b family. A significant difference in the wrong direction needs a reading too.
   Recommendation: fix this in revision 4 of the D.3 pre-declaration, so the switches `\ifRuleGain` and
   `\ifLearnedGain` are set by rule. The manuscript carries a placeholder for it (`tab:readings`).
2. **The fifth reading.** The declared reading that R1-ALIGN-OUTCOME adopts includes "Not an ICML submission in the
   present form." The manuscript writes the measured negative and keeps that sentence out of the paper text. Confirm
   that it stays out of the text.
2a. **A gain that comes from the rule layer alone.** (The corrected manuscript now opens readings three and four with
   "Rule-based control" and points to the decomposition; `tab:readings` keeps the declared "noise-aware rule control
   is enough". Text and table differ until the author rules.) If A2 − A0 and A0R − A0 are rejected and A2 − A0R is not, readings
   three and four would still open with "Noise-aware rule control raises the audited gain", which credits the one-step
   rule with a de-duplication gain. The five readings do not separate this case. Recommendation: revision 4 states it,
   and the headline then says "de-duplication raises the audited gain; the one-step rule adds no demonstrated gain".
   This refines a declared reading, so it is the author's decision.
2b. **A statistical STOP of the gate** (no eligible node, or a nonpositive test denominator) is neither pass nor fail.
   `tab:readings` has no row for it and its text is not drafted. Recommendation: the closed-loop reading stands on
   its own and the gate is reported as a STOP with no verdict; to be declared before the read.
3. **The contribution order and wording** in the introduction (the order follows R1-ALIGN-OUTCOME; only the wording
   is open): closed-loop decomposition; offline test of the
   one-step claim; control errors as supporting evidence; the rule and its scope.
4. **The abstract** (drafted; it was a placeholder before) and the **title** (27 Nov: option 1 is set in `main.tex`, on the coordinator's record that the author chose it). Options, in `main.tex` as a comment:
   (1) *Which Control Decisions Pay? A Matched-Budget Decomposition of a Governed Autoresearch Loop*;
   (2) *What Noise-Aware Control Buys an Autoresearch Loop at a Fixed Budget*;
   (3) *De-duplication, Noise-Aware Keeps and Learned Forecasts: Auditing the Control of Autoresearch Loops*;
   (4) the present title. Recommendation: (1), since the present title names the framing and not the question.
5. **The section title "The One-Step Rule and Its Scope"** and the move of the selection-bias proposition and the
   failure examples to the appendix. The main text keeps two statements, both with an author-checked source.
6. **How the proof status is disclosed** (R1-PROOF-POLICY fixes what must be said; the wording is open; the note is now at the start of the theory appendix).
7. **Offline–online agreement covers A2, A3 and A5 only** in the draft table. A0R and the three reference rules have
   no offline read (R1-D3-DECOMP; R1-D3-MIN; for LADDER, R1-MINSUB-CHOICES (4)). A0 and A1 can join if the post-freeze amendment's test rows exist.
   Confirm that this is the intended scope of R1-D3-OUTCOMES2 (e).
8. **A statement of what D.3 can detect.** The results text reserves a sentence for the smallest difference the design
   could detect. The pre-declaration draft would need to state it. If it will not, the sentence is removed.
9. **The disclosure row on incidental terminal output from sealed files** (R1-P4-TESTPLAN-DECISIONS, P4-INCID A) is
   worded from the runner report. That it is cited is decided (P4-INCID A); confirm the wording.
10. **Committed facts used in the text:** 3,274 duplicates among 4,999 replayed proposals of sweep 1 (introduction),
    and the T1 pilot's 126 of 180 proposals run, 0.62 to 0.82 per node (appendix; an engineering pilot, cited as a
    pilot). Confirm that the pilot may be quoted. The introduction also quotes two figures from other papers (49.9 % of neutral
    candidates kept; an apparent gain 2.7 times a threshold), carried over from the 23 Nov text. R1-C1-POSITION
    requires both to be checked against the PDFs before submission; that check is not recorded yet.

## 6. For the design agent and the coordinator

- Revision 4 of the D.3 pre-declaration (`local/20261126-03`) should state: the two families with their contrasts as
  in §3.1 (D.3a: A0R − A0, A2 − A0R, A1 − A0, A2 − A0, FIXR3 − A0, EGATE − A0, LADDER − A0, LADDER − A2; D.3b:
  A3 − A2, A5 − A2, A3 − A0, A5 − A0, A5 − A3, and A6 − A5 should A6 enter) and their multiplicity; the rule for item 1 of §5; whether the rule
  layer is on for FIXR3, EGATE and LADDER (the table of arms has a placeholder); how a repeated attempt after an
  infrastructure failure is charged; and the detectable difference of item 8.
- The outcome-table unit of the D.3 chain should write the macros of §3.1 by name into `generated/numbers.tex`, block (b2).
- If the screening measurement adds a further rule arm (the "seventh" of R1-D3-CHOICES (1); the eighth since A0R), `tab:arms`, `tab:closed`, the family in
  §3.1 and this sheet change together.
