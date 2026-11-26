# writer/20261126-01 with writer/20261126-02 — manuscript restructure after R1-ALIGN-OUTCOME: delivered, re-check accepted with minor, minors applied

Tasks: `writer/20261126-01` (restructure) and `writer/20261126-02` (rows of 26 Nov (g) in the manuscript).
Tier D with a fresh-agent review. AI-assisted (Claude, writer). Base: `main` `54082a05`. The branch merges cleanly with
`main` `166db0eb` (checked with `git merge-tree`; `main` did not touch `papers/r1`).

## Result in five lines

1. `papers/r1` now leads with the campaign-level question. The closed-loop decomposition (A0R − A0, A2 − A0R, A1 − A0,
   A2 − A0, then A3 − A2, A5 − A2, A5 − A3) is the main result table. The offline gate is reported as the preregistered
   test of the one-step claim and no longer decides which arms run. D.3b is unconditional; A0R, the secondary
   outcomes, the reference proposers and the descriptive T1 loop (D.3c) are in the design.
2. The theory section keeps two statements (one-step rule, reduction theorem), textually unchanged, and says why the
   campaign is measured. Everything else moved to four new appendix files; the reviewer confirmed the moves verbatim.
3. Both outcome texts are kept for the five combinations of the alignment proposal's §6: five readings written once
   in `results.tex`, selected by `\ifGatePassed`, `\ifRuleGain`, `\ifLearnedGain`. A draft build prints the three
   readings compatible with its gate outcome; a `\FinalPaper` build stops while a switch or a placeholder is open.
4. Every number is a placeholder macro or a committed fact with its source. No label, test, evaluation or audit file
   was opened.
5. Main text: about 8.85 pages in the draft, down from about 20. **Still above the eight-page target.**

## Branch, builds, hashes

| What | Value |
|---|---|
| Branch | `writer-20261126-01-manuscript-restructure` |
| Tip | `6138b54f` (restructure `6b72e27c` → review `517abb60` → correction round `2527cf2e` → re-check committed → remaining minors `6138b54f`) |
| Draft build, gate not passed | `papers/r1/build/main_draft_gate_not_passed.pdf`, **44 pages**, sha256 `9ec85c0c62e69d5a4c4ac0c7fc82cf7cf0e98f75c9a56b896dfb5e5f63595b7e` |
| Draft build, gate passed (`-usepretex='\def\DraftGatePassed{}'`) | `papers/r1/build/main_draft_gate_passed.pdf`, **42 pages**, sha256 `bd445e4cd397b40c754ec4679e6910177f62a89871d68e913029978f20a05897` |
| Page counts before (at `54082a05`) | 33 and 31 pages; main text about 20 pages |
| Main text now | ends on page 9, right-hand column, about two thirds down (references follow); appendix from page 13 |
| Build checks | `latexmk -pdf`, both builds rc 0, no undefined reference or citation, no duplicate label. `\def\FinalPaper{}` stops at the unset switches and at the first placeholder, as intended |
| Tests | manuscript only; no code changed, so no `r1/tests` run |

The appendix grew (33 → 44 pages) because the moved text sits there in full and six deviation tables and five table
shells were added.

## Review

| Step | Verdict | Record |
|---|---|---|
| Fresh-agent review of `6b72e27c` | **MAJOR REVISION**: 2 MAJOR, 11 MINOR | `docs/r1/reviews/WRITER_RESTRUCTURE_REVIEW_20261126.md`, sha256 `a30140feb4ba092daef8c59adc3b3f6af936b51771fd568b27784e2a02505fd9` |
| Re-check of `2527cf2e` by the same reviewer | **ACCEPT WITH MINOR**: both MAJOR resolved, four small remains (R1–R4) | `docs/r1/reviews/WRITER_RESTRUCTURE_RECHECK_20261126.md`, sha256 `55444e2222bf99b8af0597e98920dcca23b6c89350dd814df1252cc416ca4d96` |
| R1–R4 applied at `6138b54f` | not re-reviewed (four one-line fixes) | — |

The two MAJOR findings were: the CPU-group disclosure said "neighbouring CPU sets" where the row says the sealed
results used a set that contained the failed CPUs (fixed); and text of the 23 Nov build had been dropped instead of
moved (method details, the T1 paragraph, a caveat after the one-step proposition, the verification sentences;
restored in the appendix).

## writer/20261126-02 (rows of 26 Nov (g))

1. Deviations: `tab:dev-rules`, row "Rules that depended on a date" (all date rules withdrawn; T1 node set by
   determinism PASS; no node left out for being late; optional items by completion; dated fallbacks apply at assembly),
   with rows for wall-clock limits and shared cards (R1-CARD-SHARE, R1-NO-TIMEOUT) and for placement (R1-HOST-FREE).
2. Methods appendix: `app:hardware` (shared cards; timing descriptive; a lost attempt is repeated; the run budget
   counts only on an attempt alone on its card; which hardware produced which rows, as a placeholder until rows exist).
   It is three short paragraphs, not one.
3. No sentence promises a submission date (checked by grep and by the reviewer).

## Also placed (card -01: decisions of 25–26 Nov)

G.4b pilot and the diff recount; the four expansion candidates; D21 recorded and not a filter on T1; the excluded CPU
group; D.3b unconditional; A0R; secondary outcomes; reference rows; D.3c. In the setup, the design appendix, the
limitations and `tab:dev-nov`. The incidental-output disclosure of P4-INCID A is a row of `tab:dev-rules`.

## Placeholders that need the author

1. Title. Options in `main.tex` (comment): (1) "Which Control Decisions Pay? A Matched-Budget Decomposition of a
   Governed Autoresearch Loop"; (2) "What Noise-Aware Control Buys an Autoresearch Loop at a Fixed Budget";
   (3) "De-duplication, Noise-Aware Keeps and Learned Forecasts: Auditing the Control of Autoresearch Loops";
   (4) the present title. Recommended: (1).
2. The abstract (drafted for the first time) and the wording of the four contributions.
3. How the proof status is disclosed (theory section and theory appendix).
4. The readings: what "A2 > A0" and "A3 or A5 > A2" mean operationally; the wording when the gain is de-duplication
   alone (the text now says "rule-based control" and points to the decomposition, the table keeps the declared
   "noise-aware rule control is enough"); the case where a learned arm beats A0 and A2 does not; a statistical STOP of
   the gate. All four belong in revision 4 of the D.3 pre-declaration or in a row.
5. The companion-manuscript reference; the AI-assistance disclosure; the workshop-overlap statement (unchanged, open).
6. Wording of the incidental-output disclosure row.
7. Where the last 0.85 page comes from, if eight pages are binding for the draft: options in the sheet of
   `writer/20261126-03`, §2.

Placeholders that wait for evidence or a signed file, not for the author: every `\Loop…`, `\Gate…` and `\COne…` macro;
the citation and hash of the signed D.3 pre-declaration, with the charging of skips and the stopping rule; the T1 node
set and funnel; hardware per table; training details of A5. Counts of `\TBD` in the sources: main text 23, appendix 67,
`numbers.tex` 42 macro definitions.

## Decided alone (level 0)

Structure, wording, what moved to the appendix; the section title "The One-Step Rule and Its Scope"; splitting the new
deviations into two tables; committing both PDFs under `papers/r1/build/`; a fresh-agent review although tier D asks
for none; the three closed-loop outcome switches in `main.tex`; leaving the title unchanged.

## What other roles need to do

- **Coordinator:** check and merge `6138b54f` (documentation only). `writer/20261126-03` sits on top of it at
  `78886f11`. Put item 4 above on the author's list.
- **Local worker (`local/20261126-03`, revision 4):** the manuscript waits for the contrast families with their
  multiplicity, the charging of a skip, the campaign's stopping rule, the rule-layer setting of the three reference
  rules, and the readings of item 4.
- **Compute:** nothing.

## Next

Nothing runnable is left in the writer queue. Result tables are blocked until results are released.
