# writer/20261126-01 follow-up — title option 1 and the trim to eight pages: delivered

Task: the follow-up to `writer/20261126-01` that `STATE.md` of 27 Nov 00:35 names ("title option 1, trim to eight
pages. Merge after that trim"). Tier D. AI-assisted (Claude, writer). Base: the delivered tip `6138b54f`.
Merges cleanly with `main` `47df6f55` (`git merge-tree`).

## Result in five lines

1. **Main text: 8.0 pages.** It ends on page 8 in both draft builds; the references start on page 9. Before: about 8.85.
2. **Title:** "Which Control Decisions Pay? A Matched-Budget Decomposition of a Governed Autoresearch Loop"; running
   title "Which Control Decisions Pay?".
3. How the page came out: (a) while the closed-loop outcome is unknown, the main text prints one declared reading, as
   the final paper will, and a new appendix subsection (`app:readings`) prints the other two for the build's gate
   outcome; (b) long drafting prompts moved from placeholders into source comments, each placeholder keeps one line;
   (c) line-level tightening in every section. The removed sentences that carried content are in the appendix.
4. No claim, contrast, arm, design value or theory statement changed. The proposition and the theorem are untouched.
5. Not re-reviewed: the diff is wording and placement only (11 files, +95 −61 lines outside the PDFs).

## Branches, builds, hashes

| What | Value |
|---|---|
| Restructure branch | `writer-20261126-01-manuscript-restructure` @ **`e360d425`** |
| Sheet branch (on top of it) | `writer-20261126-03-claim-table-sheet` @ **`acf7d37b`**; sheet sha256 `55bfedbc710db3622cb5339b6990a211398956e14b288946043fcfd6c5706aef` |
| Draft, gate not passed | `papers/r1/build/main_draft_gate_not_passed.pdf`, **43 pages**, sha256 `67e072f34bfe61190e5b0283b679d576a738454ee1703b8dc8fdc10ebdd13371` |
| Draft, gate passed | `papers/r1/build/main_draft_gate_passed.pdf`, **41 pages**, sha256 `e76c174b07294a11d58126226084d81fac791abb52eb1e4b00b492d8f87e39d4` |
| Build checks | both rc 0, no undefined reference or citation, no duplicate label; `\def\FinalPaper{}` stops at the unset switches |
| Placeholders in the main text | 22 (was 26) |
| Tests | manuscript only; no code |
| Review | none for this step (tier D); the restructure's re-check verdict stands for `2527cf2e`: ACCEPT WITH MINOR |

## One point the coordinator should confirm before merging

`STATE.md` says the author gave the title and the trim "to the writer in its pane". **No such message reached this
writer session.** The trim is inside the card ("main text toward eight pages"), so it needs no further word. The title
is the author's choice: it is set on the coordinator's record alone, and `main.tex` says so in a comment. If the
author did not choose option 1, the two title lines of `main.tex` are the only change to revert.

## Decided alone (level 0)

Which sentences to cut; printing one reading in the draft's main text and the others in the appendix; keeping the
drafting prompts as source comments; no new review for a wording-only diff.

## Next

Nothing runnable in the writer queue. Result tables stay blocked until results are released. The manuscript still
waits for revision 4 of the D.3 pre-declaration (`local/20261126-16`): contrast families and multiplicity, charging of
a skip, the stopping rule, the rule-layer setting of the reference rules, and the four open points of the readings.
