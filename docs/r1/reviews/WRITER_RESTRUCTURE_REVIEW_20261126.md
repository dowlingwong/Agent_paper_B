# Review: Paper B manuscript restructure (writer/20261126-01, -02)

- **Reviewed:** `papers/r1` at tip `6b72e27c` (branch `writer-20261126-01-manuscript-restructure`) against base `54082a05` (origin/main). The two PDFs under `papers/r1/build/` were not reviewed.
- **Reviewer:** an AI agent (Claude) that did not write the unit. Read-only; nothing in the repository was changed. No label, evaluation or sealed result file was opened.
- **Verdict:** MAJOR REVISION

The two MAJOR findings are small in effort (one phrase; restoring dropped text to the appendix). Everything else is sound: the structure follows R1-ALIGN-OUTCOME and the runbook, the arm lists and contrast families match the rows, the theorem statements are untouched, both drafts build cleanly, and `\FinalPaper` stops.

What was checked and how:
- Every PLAN row named in the brief, the proposal's section 6 and section 4, the runbook's section 3 and the writer's SOUL were read at `54082a05`.
- All main-text sections and `app_design.tex` were read in full at the tip; the other files were covered by the diff and the comparison below.
- Every sentence of the base `problem/theory/method/setup/results/related/limitations/introduction.tex` was compared with all tip files by script, and the non-verbatim ones were read.
- Both drafts and a `\FinalPaper` run were built in a private copy.

---

## MAJOR

### M1. Deviations row on the workstation CPUs understates the disclosure
`sections/appendix.tex`, Table `tab:dev-rules`, row "CPU group on one workstation":
> "Sealed noise-floor results that had used neighbouring CPU sets stand: their fixed-seed determinism checks had passed."

R1-TASL2-CPU says: "Sealed results that used CPUs 8-15 stand". CPUs 8-15 contain the four failed CPUs (8-11). The sealed runs therefore used the failed CPUs, not neighbours of them. The row softens a disclosure, and `app:hardware` (`app_design.tex` line 201) does not mention the point at all.

Fix: "Sealed noise-floor results that had used a CPU set containing these four CPUs stand: their fixed-seed determinism checks had passed, and for one node the cross-host comparison was bit-identical." Add the same clause in `app:hardware`.

### M2. Substantive main-text content was dropped, not moved
The file headers say details "moved ... unchanged". The following base text is in no tip file (checked by grep).

**Method (`method.tex` at base).** After the cut, the forecast-to-rule mapping cannot be reproduced.
- How `μ` and `τ` are computed: "computed from bin midpoints (with ±4 for the two tails) and rescaled by σ_node". Without it the units of `t* = −μσ²/τ²` in the tip's `method.tex` are ambiguous: `μ, τ` are read from bins of `z`, while `σ` is the raw comparison noise.
- The forecaster's inputs: "The forecaster sees the task (node descriptors and metric), the edit (...), and the ledger (...)", and "Language-model forecasters also read the manager's proposal summary and rationale."
- A3: "trained on the structured features with soft labels and the log loss".
- A4: the three typed questions and the calibration map.
- A5: "in two sizes"; "The checkpoint is selected on the validation score, and a temperature is fitted on development instances"; the base-model control (`\citep{qwen35}`). `app:arms` still lists "the base-model control" as a reference row but no longer says what it is.
- The arm-selection rule: "chosen by the mean over nodes of the development skill in ranked probability score against each node's base rate. Ties go to the main sweep alone and then to the smaller model."
- The structural-floor remark: "if a forecaster learns nothing, its output collapses to node constants and the rule reduces to the constant-prior arm. A learned arm can fall below that arm only through miscalibration".

**Setup (`setup.tex` at base).**
- The eight T1 nodes by name ("three from MLAgentBench (CIFAR-10, IMDb, ogbn-arxiv), four from MLGym (...) and a fixed-token variant of autoresearch"). The tip never names them.
- "The suites' agent frameworks are not used, so every node shares one runner, one ledger format and one audit path."
- "within the node's declared editable paths"; "Runs use a fixed step or token budget, not wall-clock time".
- The six OpenML task names in prose (they survive only as table rows).
- The closed loop's memory mode ("with the append-only summary memory"). `limitations.tex` still says "one memory mode" without naming it.

**Theory.** `app_theory_main.tex` says "MOVED from theory.tex (paragraphs after Proposition prop:onestep)", but the first of those paragraphs is gone:
> "The proof uses only the tower property and the measurability of a_n and k_n. The closed form is an additional assumption stated relative to O_n, which depends on the policy. A Gaussian law given a finer history generally becomes a mixture given O_n."

This is a scope caveat on the closed form that the arms apply. Also gone: "It needs no independence across trials and no independence between the control plane's randomness U and the trial outcomes."

**Problem.** "The displayed memory and the remaining budgets are functions of O_n"; "Verification runs are not priced in it"; the definition of verification ("it may spend 2r further runs on a paired fresh-seed verification"). `app:design` still uses `r_n`.

Fix: restore these into `app:arms`, `app:nodes`, `app:closed` and `app:theory-main`, verbatim. Keep one clause on the units of `μ, τ` in the main-text Method.

---

## MINOR

### m1. The readings credit "noise-aware" control on a condition that does not separate it (items 2, 8)
`results.tex` `\ReadingRulePass` and `\ReadingRuleFail` open with "Noise-aware rule control raises the audited gain of a campaign". Both are selected by `\ifRuleGain`, which is "A2 > A0". A2 − A0 can come entirely from the rule layer (A0R − A0), which is de-duplication. The decomposition exists to tell these apart, and the headline sentence pre-empts it.

The proposal's wording has the same gap, so this goes to the author. Wording that stays inside the declared reading: "Rule-based control (the rule layer with the one-step rule) raises the audited gain ...; Table tab:decomp says how much of this is de-duplication and how much is the noise-aware rule."

### m2. Draft banner in `results.tex` is keyed to the wrong switch (item 7)
Lines 25-27 print "No closed-loop campaign has run, and the gate has not been read" whenever `\ifLoopOutcomeSet` is false. The expected intermediate state is gate read and D.3 pending. The banner will then say the gate is unread and that the build "shows the text for the outcome in which the gate passes/does not pass", as if it were hypothetical. Conversely, with the loop set and the gate unset, a draft prints the not-passed text with no banner.

Fix: two banners, one per switch (`\ifGateOutcomeSet\else ...\fi`, `\ifLoopOutcomeSet\else ...\fi`).

### m3. Wrong table reference
`appendix.tex`, caption of `tab:dev-hosts`: "The placement rule for later runs is in Table~\ref{tab:dev-nov}." The placement row (R1-HOST-FREE) is in `tab:dev-rules`.

### m4. Duplicated sentence
`theory.tex` line 37: "Consider two conditions. Consider two conditions."

### m5. Main-text theory: two loosened restatements and a thinner status note (item 4)
The statements of Proposition `prop:onestep` and Theorem `thm:reduction`, the definitions of (NF) and (NI) and the definition of `V` are byte-identical to base (checked by script). Propositions `prop:bias`, `prop:failures` and Corollary `cor:bias-kernel` are identical in the appendix. No new theorem was added. Three points remain.
- Scope bullet 1: "A keep replaces that error by a selected one, which is biased upward on every noise-driven keep for any adaptive proposer (Proposition prop:bias)". The proposition gives `e' > e − Δ_n` on every keep, `e' > e` for a null proposal, and a positive conditional mean only under the zero-mean condition. The base text warns that it can fail otherwise. Reword: "which exceeds the old error on every keep of a null proposal, for any proposer (Proposition prop:bias(i))".
- Reading paragraph: "The default keep threshold 0 is optimal only if μ_n=0" drops the base's "For σ_n>0".
- The status `\TBD` in `theory.tex` names only `prop:onestep` and `thm:reduction`. The scope argument now rests on `prop:bias` and `prop:failures`, both AI-checked only, and the base caveat "Theorem thm:reduction as worded here has not been compared with its author-checked source since 22 Nov" is now only in the appendix. R1-PROOF-POLICY asks for each statement's status to be marked precisely. Add both to the main note.

### m6. Definition of the preregistered quantity changed without a comment (item 5)
`problem.tex`: base "the weighted mean over the campaign's logged proposals" is now "the mean over the campaign's logged proposals". If the preregistered utility is weighted, restore the word. Also dropped: "so it is credited the run price".

### m7. Incident row is vague where the record is specific
`tab:dev-rules`, last row: "in two lines a field of an earlier engineering manifest". The disclosure record (`TRACKP_P4_RUNNER_20261122.md`) says each of the two lines showed a `delta_audit` field and its number. "No evaluation value was shown" is correct. Say "in two lines an audit increment value from an earlier engineering manifest". The row already carries a `\TBD` to confirm the wording.

### m8. Hand-typed count without a committed source (item 3)
`limitations.tex`: "under the noise criterion used for T0, two of the eight would qualify". `app_design.tex` (`app:nodes`): "where it would leave two of the eight nodes". `tab:dev-nov`: "The noise floors of the eight nodes had been read."

R1-T1-D21-SCOPE states the two qualifying nodes from "the official seven-node assembly". I found no committed value for the eighth node in the files read. Make it a macro with its source, or write "two of the nodes measured so far".

### m9. Design values stated as decided whose source is not on main (item 1)
`setup.tex`: "A skipped proposal is charged no worker run and one manager call, and the manager is asked again." `app:closed`: "A campaign ends when it has used its 20 worker runs or its 80 manager calls."

R1-D3-DECOMP fixes only "charged no run". The call charge and the stopping rule come from the pre-declaration draft, which is not in the tree at `54082a05` and is unsigned. Both places sit next to a `\TBD`, but the sentences read as settled. Put them inside the `\TBD` or prefix "In the draft pre-declaration".

The other design values check out:
- `\LoopCalls` = 80, two-sided tests, Holm at 0.05, one repetition: R1-D3-CHOICES (2).
- `\LoopW` = 20, `\LoopInstances` = 18, `\LoopAuditK` = 10: R1-MINSUB-CHOICES (4).
- Seven rule arms, and the contrast families of both stages including A5 − A3: R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-D3-DECOMP, R1-D3B-UNCONDITIONAL.

### m10. Stale wording that survives in moved text (item 1)
- `app_design.tex` line 32: "we report a closed loop on T0 beside it". The closed loop is now the headline.
- `app_design.tex` line 107: A6 "frozen in its own record before the second closed-loop stage; ... can appear only in that stage". The tip no longer defines stages.
- `app_results_main.tex` lines 160 and 178 (`\TBD` text): "had no labelled T1 node when the arms were frozen". Under R1-STEP-ORDER (2)(b) no node is left out for being late; the remaining case is a node removed by an author row.
- `setup.tex` line 17: "four further candidates are being screened" is a status sentence that will age. The row says "at most four", and `tab:dev-nov` already says "Up to four".
- `related.tex` header says "No citation ... was added", but `\citep{lindauer2022smac}` is new in the text. The bib entry already existed and the comment is not paper text.

No sentence in the tip makes learned arms conditional on the gate, states a date rule as current, or promises a submission date. "One GPU model per table" appears only in the past tense or in a "Planned" column.

### m11. Sentences slightly ahead of their evidence (item 3)
- Abstract: "so part of a fixed budget goes to duplicates and to keeps that do not hold up". The duplicate share is a committed sweep-1 count. The false-keep rates are still placeholders (`\COneFalseKeepSOne`). Write "can go", or lean on the cited external results.
- `results.tex`, gate-not-passed branch: "a true gap closed of \GatePowerEffect{} fails the gate more often than it passes". This hard-codes an inequality derived from `\GatePowerMain` = 0.36. That value is a mean over scenarios with headroom of at least 1, with only the 97.5% step simulated. Write "in that simulation the gate passed in \GatePowerMain{} of runs at a true gap closed of \GatePowerEffect{} (qualifiers in Appendix app:gate)".

---

## NOTES

**N1. The five readings match the proposal's section 6 (item 2).** Same five cases, same switch structure. "A4 and A5 of §4" in the proposal are its secondary outcomes (mechanism counts, agreement), and the tip renders them correctly. No negative is softened. Three differences:
- The fifth reading omits "Not an ICML submission in the present form". This is flagged for the author in a source comment; it is a venue statement, not paper text.
- The first reading adds "so the one-step claim and the campaign-level result point the same way".
- The fifth adds "at this budget", which narrows it.

**N2. The fifth reading can contradict the data.** It covers "any" learned-arm outcome. If A3 or A5 beat A0 while A2 does not, "the loop is not limited by its keep and screen decisions" would be false. The gap is inherited from the proposal and is for the author.

**N3. New numbers match their source (item 3).** In `numbers.tex` block (a2), 180 proposals, 126 ran, and 0.62 / 0.82 match section 4 of `G4B_TASL_PILOT_RESULT_20261125.md` (0.6167 and 0.8167). "An earlier pilot ... refused most proposals" matches 155 of 180 refused, 122 of them for hunk headers. All closed-loop results are `\Cell` or `\TBD` macros.

**N4. Moved text is otherwise verbatim (item 5).** `app_related.tex` equals the base `related.tex` in every sentence. In `app_theory_main.tex` and `app_results_main.tex` the only non-verbatim sentences are the announced ones (section intros, the STEP-ORDER rewording of the C1 placeholder, the rewritten "what carries the paper" paragraph, one retargeted reference). Nine passages were spot-checked as identical:
- the DAC mapping, the control-error definitions, the qualification paragraph, the audit protocol;
- the gate in full, the A6 paragraphs;
- `prop:bias`, `cor:bias-kernel`, `prop:failures` with its example.

**N5. Not restored from the introduction.** The four stated differences (a) to (d) of R1-C1-POSITION were a list in the base introduction. They now appear only piecewise in `related.tex` and in full in `app_related.tex`. Acceptable; the author may want (a) and (b) back in one sentence of the introduction.

**N6. Task card -02 (item 6).** All three items are present.
- `tab:dev-rules` row "Rules that depended on a date" covers the expansion cutoff, the arms-frozen cutoff, the optional-items date and the dated fallbacks, with the node set by determinism pass and optional items by completion.
- `app:hardware` covers shared cards, descriptive timing, repeated attempts and the run budget counting only when alone on the card. It runs to three paragraphs, not one. "Which hardware produced which rows" is a `\TBD`, which is correct while no rows exist.
- No sentence promises a submission date.

**N7. Build (item 7).** Both drafts build with no undefined reference, no undefined citation and no duplicate label. The default draft prints three readings with the gate-fail variants; `\DraftGatePassed` prints the pass variants. `\def\FinalPaper{}` stops at "Gate-outcome switch not set". `fig:ladder` is defined but never referenced, as at base. Ten overfull boxes, the worst 54pt.

**N8. Length.** In the draft, Limitations starts on page 9 and the appendix on page 12, so the main text is above the eight-page target. The draft prints three readings and several `\TBD` banners.

**N9. Timing cell of the first rows of `tab:dev-nov`.** "Before the gate read, the arms-frozen record and any closed-loop run" is true. A sceptical reader will ask what had been seen: the sweep-2 train and dev label blocks, and any development results of the learned arms. State that too.

**N10. `limitations.tex`, "What the outcome leaves open".** It branches on the gate only and has no text for the closed-loop outcomes.

**N11. Evidence levels.** `problem.tex` has "Three levels of evidence"; the runbook's section 3 item 5 says "four evidence levels". Check which is intended.

---

## Clarity for a sceptical reader (item 8)

**C1. "Matched budget" (`setup.tex`, `sec:setup-closed`).** Skips are free in worker runs, so A0R and A2 see more proposals than A0 within the same 20 runs. A reader will ask whether the rule layer's gain is just "more manager calls". Add: "Arms are matched on the budget, not on realised use: an arm that skips issues more manager calls, up to the common cap. Table tab:closed reports the runs and calls each arm used."

**C2. From "noise-aware" to the measured contrast (`results.tex`, readings; see m1).** The claim word is "noise-aware" and the switch is A2 − A0. State once, in the setup: "The noise-aware part of the claim rests on A2 − A0R (and A1 − A0); A2 − A0 alone does not separate it from de-duplication."

**C3. "Is enough" (`tab:readings` row 4, `\ReadingRuleFail`).** A non-rejection at low power does not show sufficiency. The proposal's wording is binding, but the sentence can carry its own limit: "... we find no gain from learning, in the loop or offline; the intervals of Tables tab:decomp and tab:gate bound how much it could add."

**C4. Abstract.** "noise-aware one-step rule with a constant forecast" and "audited gain" come before they are defined, and the abstract says "proposer calls" where the paper says "manager calls". Suggested: "... which control decisions raise a campaign's gain, re-measured on fresh seeds? ... We compare four controllers on fresh campaigns: the default loop; the default loop with duplicates skipped; a rule that sets its run and keep thresholds from the measured noise and one fixed forecast per task; and the same rule with a learned forecast per proposal."

**C5. Theory scope, last sentence (`theory.tex` line 61).** "The theory therefore motivates the arms; it does not predict their campaign-level gain" is the key link and comes late. Move it to the section's opening paragraph: "The section derives the rule the arms apply. It does not predict what the rule gains in a campaign; that is measured (Section sec:results-closed)."
