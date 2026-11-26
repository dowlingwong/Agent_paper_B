# Report — kit c1 disposition record (P2 of the expansion G.1b note)

**Task:** `experiment/20261126-01` with `compute/20261126-04`.
**Result: PASS.** The record is written, independently reviewed **ACCEPTED** (no BLOCKING, no MAJOR), and pushed.

- **Branch:** `compute-kit-c1-disposition-20261126`
- **Tip:** `0503953f12d366bced3fc8958857249491396056`
- **Base:** `origin/main` `54082a057fc010e0cbd596a2146a6c997cfef57c` (contains `95249de3`, rows of 26 Nov (f)(g); docs-only descendant)
- **Record:** `docs/r1/reports/tasl_chain_20261122/KIT_C1_DISPOSITION_20261126.md`
  sha256 `6b8a78554c6784174f8b112e90c27f53d71f44572d6426f09b9c5ba447eaec1b`
- **Review:** `docs/r1/reviews/KIT_C1_DISPOSITION_REVIEW_20261126.md`
  sha256 `46fcfd1dd2d5c5000dd546d8ba037b436ac11c57b017758cda7caff953fd0a95`
- **Review verdict:** `ACCEPTED`.

## What the record does

One line for each of the 33 MINOR items of the four kit reviews (Titanic m1–m8; MountainCar/MetaMaze m1–m10;
ETTh1 m1–m8; Forest Cover m1–m7). Each item is **applied** as a paper-side corrigendum in the record or **waived
for G.1b** with its reason and the right later condition. The seven frozen-file residuals named by
`compute/20261126-04` (Titanic m1; MetaMaze m1, m3, m9; ETTh1 m1, m7; Forest Cover m5) are deferred under **c8**
(the re-pin rule); no frozen file is edited. The only label-table condition, ETTh1 **c6(iii)** (author/legal
licence line), is named and left standing. The record cites the four review sha256 values (equal to the note
draft's P2 line) and the four kit-report sha256 values, and closes with: **no pin, frozen file, census value or
spec field changes.**

## Review

The independent review recomputed all eight sha256 values, checked all 33 items and the frozen residuals, checked
that c8 is not used as a label-table condition and that ETTh1 c6(iii) is, and verified the diff contains only the
record and the review. It found **no BLOCKING and no MAJOR**. Its MINOR notes are wording only (present-tense
"the report says" for corrigenda; abbreviated Forest Cover m1/m3/m7 and coordinator next-step wording). I left the
accepted record unchanged rather than churn a re-review; none affects a disposition.

## Tests and evidence

Docs-only: the branch changes no code, spec, pin or data. `git diff --stat origin/base` is two new Markdown files.
No `r1/tests` run applies; the coordinator's D8/docs guard is the merge check. No label, evaluation or sweep-2
file was opened (`labels_read: none`). No GPU or evidence job was started for this task.

## Decided alone

Which MINOR items were paper-side corrigenda (applied here) and which were frozen-file or evidence-root items
(waived for G.1b under c8 / deferred as evidence maintenance). This is level 0; it changes no pin, census value,
spec field or signed file.

## What happens next

The coordinator: merge this record; set **P2 PASS** in the expansion note (P4 and the four gate lines are already
PASS); set `approved: true`; run `check-note-x … --draft`, publish, run the strict `check-note-x`; then write the
launch task. Compute waits for that task before any G.1b launch. No compute item is blocked by anything else in
this delivery.
