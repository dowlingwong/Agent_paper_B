# Re-check: Paper B manuscript restructure, correction round

- **Re-checked:** `papers/r1` at `2527cf2e` against the review committed at `517abb60` (diff `6b72e27c..2527cf2e`, PDFs under `build/` excluded).
- **Reviewer:** an AI agent (Claude) that did not write the unit. Read-only; no label, evaluation or credential file was opened.
- **Verdict:** ACCEPT WITH MINOR

Both MAJOR findings are resolved. What remains is four small wording points in the restored appendix text (R1 to R4 below). The corrected tip builds in a private copy with no undefined reference or citation and no duplicate label.

## Findings of the review

| Finding | Status | Remark |
|---|---|---|
| M1 CPU disclosure | resolved | `tab:dev-rules` now says "a CPU set containing the four CPUs", with the cross-host clause; the same sentence is in `app:hardware`. Matches R1-TASL2-CPU. |
| M2 dropped text | resolved, with small remains | Restored in `app_design.tex`: the method text (bin midpoints and rescaling, inputs, A3/A4/A5 details, base-model control, selection rule, structural floor), the T1 paragraph with the eight node names, and the verification and information sentences. Restored in `app_theory_main.tex`: the closed-form caveat. The memory mode and "one repetition" are back in `setup.tex`. `method.tex` now states the units of μ and τ. Remains: R1 to R3. |
| m1 "noise-aware" credit | resolved as far as wording allows | Both readings now say "Rule-based control" and carry a `\TBD` pointing to the decomposition. Passed to the author, as intended. |
| m2 draft banner | resolved | One banner per switch (`\ifLoopOutcomeSet`, `\ifGateOutcomeSet`). |
| m3 table reference | resolved | Now `tab:dev-rules`. |
| m4 duplicated sentence | resolved | |
| m5 theory restatements and status note | resolved | The scope bullet now says "Proposition prop:bias gives the direction of the selection"; "For σ_n>0" is back; the status note lists `prop:bias` and `prop:failures`(a) as AI-checked only and carries the "not compared since 22 Nov" caveat. |
| m6 "weighted mean" | resolved | Restored in `problem.tex`. "so it is credited the run price" was not restored; harmless. |
| m7 incident row | resolved | "an audited-increment field with its number". |
| m8 "two of the eight" | resolved | Now "few" in `limitations.tex` and `tab:dev-nov`, and a `\TBD` for the count in `app:nodes`. |
| m9 skip charging | resolved | The call charge, the memory line and the stopping rule are now inside a `\TBD` awaiting the signed pre-declaration. |
| m10 stale wording | partly resolved | Fixed: "beside it", "being screened", the `related.tex` comment, a note on the leave-one-suite-out `\TBD`. Remains: R3. |
| m11 sentences ahead of evidence | resolved | Abstract says "can go"; both gate-fail passages now state the power value instead of the inequality. |
| N9 timing cell | resolved | The cell now names what had been seen. Supported: the sweep label releases are PLAN rows, and an A3 run report dated 23 Nov is in the tree at `54082a05`. |
| N10 limitations | resolved | A `\TBD` for the closed-loop outcome was added. |
| C1 matched budget | resolved | Sentence added in `setup.tex` and `app:closed`. |
| C2 noise-aware contrast | resolved | "The noise-aware part of the question rests on A2 − A0R and A1 − A0". |
| C3 "is enough" | resolved in the text | `\ReadingRuleFail` now says "we find no gain from learning". Table `tab:readings` keeps the declared "is enough", so text and table differ until the author rules; the source comment says so. |
| C4 abstract | resolved | |
| C5 theory scope sentence | resolved | Moved to the section's opening. |

## What remains

- **R1. Wrong pointer in restored text.** `app_design.tex`, `app:arms`: "one no-op bin and the 11 bins of Section~\ref{sec:setup}". The bin edges are now in the "Soft labels" paragraph of the same appendix, not in Section `sec:setup`.
- **R2. Restored text contradicts the main text on a count.** `app_design.tex`, `app:arms`: "The method has two parts." The main-text Method says "The method has three parts" (it counts the rule layer). Change the appendix sentence or drop it.
- **R3. Dangling "that stage".** `app_design.tex`, `app:arms`: "frozen in its own record before it runs in the closed loop; ... and can appear only in that stage". After the edit no stage is named. Write "and can appear only in the closed loop".
- **R4. Two base sentences still absent.** "It needs no independence across trials and no independence between the control plane's randomness U and the trial outcomes" (after the one-step proposition), and the six OpenML task names in prose (they remain as table rows). Low value; restore or leave.

## Newly broken

Nothing substantive. No new statement contradicts a PLAN row, and no new number was typed by hand. The only new defects are R1 to R3, which come from restoring the 23 Nov text verbatim into a new place.
