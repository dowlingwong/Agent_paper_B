# Independent review — kit c1 disposition record for the four T1 expansion kits (26 November 2026)

**Verdict: ACCEPTED — no BLOCKING, no MAJOR.**

**Reviewer.** I am an independent, AI-assisted reviewer in a fresh session. I did not write
`docs/r1/reports/tasl_chain_20261122/KIT_C1_DISPOSITION_20261126.md`, and I had no part in the four kits,
their reviews, the U2 censuses, the expansion note draft or the disposition record. This was a read-only
review: the only file I wrote is this review. I changed no record, kit report, review, spec, code, pin,
frozen file or census value.

## Inputs reviewed (with sha256)

| Input | Ref / path | sha256 |
|---|---|---|
| Record under review | `docs/r1/reports/tasl_chain_20261122/KIT_C1_DISPOSITION_20261126.md` (this branch, `ce7dc075`) | `6b8a78554c6784174f8b112e90c27f53d71f44572d6426f09b9c5ba447eaec1b` |
| Titanic review | `origin/main:docs/r1/reviews/TITANIC_KIT_REVIEW_20261125.md` | `3c1d98601148485f5b319f1de1b8e5f9a688c9d3207a0aefe4554873a3344574` |
| MountainCar/MetaMaze review | `origin/main:docs/r1/reviews/MOUNTAINCAR_KIT_REVIEW_20261125.md` | `5b867480ed81d3b5ece0f46657333cbb446d173cb0ed79f03bcebcd89d3e9950` |
| ETTh1 review | `origin/main:docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md` | `73df58d5f929d6922223c3b33a926232e5e5189a774cc6a3b7364e5768869202` |
| Forest Cover review | `origin/main:docs/r1/reviews/FORESTCOVER_KIT_REVIEW_20261125.md` | `8a4412bc307986077af5c8907ec06235fa1dec6901eaf56b29f5976d05e4bed5` |
| Titanic kit report | `origin/main:docs/r1/reports/tasl_chain_20261122/TITANIC_KIT_20261125.md` | `a1844bfef44e742795e6b74eef1738f70bec228bd4e13d6d58aa2eb13457ed10` |
| MountainCar kit report | `origin/main:docs/r1/reports/tasl_chain_20261122/MOUNTAINCAR_KIT_20261125.md` | `0cede51b0dba90af8cc485748d577c2049d3671361f07facff70baabed635e7e` |
| ETTh1 kit report | `origin/main:docs/r1/reports/tasl_chain_20261122/ETTH1_KIT_20261125.md` | `e1b94a76a2caf84cde6f0143cd094fdcbb31549e8f154d3441dc92da94079417` |
| Forest Cover kit report | `origin/main:docs/r1/reports/tasl_chain_20261122/FORESTCOVER_KIT_20261125.md` | `ecc3e236cddd8660af73024a9bdf2b255b2cea064dcb81eaac0d0e4d363f12d1` |
| Task `experiment/20261126-01` | `origin/coord/coordinator:tasks/experiment/20261126-01-kit-c1.md` | `421f611d68eedf69628a8f51ae814c3d91dc3b3aa6f9e89817a21eccdf884056` |
| Task `compute/20261126-04` | `origin/coord/coordinator:tasks/compute/20261126-04-kit-c1-launch-path.md` | `f75b2e86014f9bf36f2880804f450324d2a1cf45322e96e7b88ead6b0e5812f6` |
| Expansion note draft | `origin/coord-xnote-prep-20261126:docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` (P2 at l.108) | `b0f5f634cc056ee4d516f705ca4940019e240139edeafbd17a6b98dbdbd96d15` |

The four review sha256 values above are exactly the four cited in the P2 line of the expansion note draft:
`TITANIC … 3c1d9860…`, `MOUNTAINCAR … 5b867480…`, `ETTH1 … 73df58d5…`, `FORESTCOVER … 8a4412bc…`.

## Verification method (read-only)

- Recomputed every cited sha256 from the blob on `origin/main` with
  `git show origin/main:<path> | shasum -a 256`; all eight review/report hashes match the record, and the
  four review hashes match P2 of the note draft.
- Read the two task files in full with `git show origin/coord/coordinator:…`, including the corrections in
  `compute/20261126-04` (frozen-file list, c8 vs the label-table condition, the `P2`/`P4`/gate/`approved`
  sequence, and the launch sequence).
- Enumerated the record's item rows and counted them: Titanic m1–m8 (8), MountainCar/MetaMaze m1–m10 (10),
  ETTh1 m1–m8 (8), Forest Cover m1–m7 (7) = 33, each exactly once.
- Compared every disposition line against the corresponding review finding, including the numbers and file
  counts (e.g. Titanic's 7 `.py`/15 entries; MetaMaze's +2/−1 README change, 5 × 20M, 8 G cap, 32,201 B +
  4,226 B; ETTh1's MSE deltas; Forest Cover's 40-epoch footnote and timestamps).
- Checked the frozen residuals named in the task correction one by one: Titanic m1; MetaMaze m1, m3, m9;
  ETTh1 m1, m7; Forest Cover m5. Checked that the paper-side part is applied where possible and the frozen
  part is deferred under c8, not claimed as edited.
- Checked the c8 usage: c8 is used only as the re-pin rule; the only label-table condition named is ETTh1
  c6(iii), with the author/legal licence line before any label table cites ETTh1.
- Checked `git merge-base --is-ancestor 95249de3 origin/main` (rc 0) and the record's base commit.
- Checked the worktree scope with `git diff origin/main --stat` and `git status --porcelain` before writing
  this review: only the new record file was present in the diff and the worktree.
- Checked the ENGINEERING_ONLY / `labels_read: none` boundary. The record opens no label, evaluation or
  sweep-2 file. It repeats validation/test metric values only as they already appear in the four engineering
  kit reviews (for example ETTh1 m3's 0.384/0.655 and Titanic m4's 0.808989/0.775281); I do not treat that
  as a label read, but the values are review-derived, not independently opened partitions.

## Findings

**No BLOCKING, no MAJOR.** The record's application or waiver of every one of the 33 m-items is
substantively correct: the 33 items are all present exactly once, every frozen-file item is either split
(paper-side applied, frozen part deferred under c8) or waived with c8 named, and the record does not claim
to have edited a frozen file, pin, census value or spec field. The four review hashes and the four report
hashes are correct, and the review hashes match P2.

The following are MINOR notes; none changes the disposition or the verdict.

1. **MINOR — present-tense "the report says" for corrigenda (Titanic m1 l.45, MetaMaze m1 l.58, ETTh1 m1
   l.73).** The record writes corrected wording as if the kit reports already carry it ("the report says
   'the MLGym Titanic candidate'", "the report/status line says 'candidate 3 in the lead's parallel-kit
   order'", "the report, `README.md` and `test_port_1gc.py` say 'the 1GC-7RC ETTh1 candidate'"). The kit
   reports are deliberately not edited and their cited sha256 are the pre-corrigendum blobs; a reader who
   checks the report will still see "candidate 1", "candidate 3" and "candidate 2". Say "the report is
   corrected to say …" or "the corrigendum reads …". The ETTh1 m1 line is the sharpest case: it groups
   `README.md` (a frozen node file) and `test_port_1gc.py` (a surveyed-branch file, not the node's frozen
   pin) with the paper-side report, while the disposition only waives "frozen files" and the later condition
   only says a change to the test file would need re-review. State explicitly: paper-side report corrected;
   `README.md` left under c8; `test_port_1gc.py` left unchanged and re-reviewed if changed. This is a
   precision issue, not a claim that a frozen file was edited.

2. **MINOR — MetaMaze m7's README §2 note (l.64).** "the same nuance in the README §2 table is corrected
   paper-side" can read as applying a correction to a frozen README. The review's m7 says the README §2
   table has the same nuance, and MetaMaze's `README.md` is in the node's frozen list. The record should say
   the README is not edited (the paper-side report records the nuance and the README wording is left under
   c8), or defer that part. As written, the later condition "None for G.1b" is too weak if the README
   nuance is considered part of m7. The task correction's frozen list does not name MetaMaze m7, so I do not
   treat this as a missed frozen residual, but the wording should not imply a frozen-file correction.

3. **MINOR — abbreviated corrigenda for Forest Cover m1, m3 and m7 (ll.86, 88, 92).** The core corrections
   are applied, but three recorded corrigenda are thinner than the review text:
   - m3: the review asks to state the final measured accuracies (0.8964 validation / 0.8947 test, with
     convergence unmeasured); the record says only that "the final measured accuracies are stated", without
     the values. The correction is described, not actually written out.
   - m7: the review asks for E1 and E4 >10 SE, E3 ≈3.6 SE and E2 ≈2.2 SE; the record gives only E3 ≈3.6 SE.
     "replaced by the numbers" is therefore incomplete.
   - m1: the record gives the 40-epoch/40-min correction but not the port's 8,000 steps ≈71 epochs that the
     review's replacement text uses to explain why the port's baseline exceeds 0.806.
   These are completeness notes, not wrong numbers, and they do not change the "applied" judgment.

4. **MINOR — the closing statement's coordinator next step is abbreviated (ll.96–110).** The record says
   the coordinator merges the record, sets P2 PASS in the expansion note, runs `check-note-x … --draft`,
   publishes, and runs the strict `check-note-x`. Per `compute/20261126-04` item 4, the coordinator also
   writes the note at `docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md`, sets P4 PASS
   (`G1B_EXPANSION_REVIEW_20261126.md`), sets the four gate lines PASS, and sets `approved: true` (under
   R1-T1-NODE-EXPANSION). The record points to `compute/20261126-04`, so the sentence is not false, but it
   does not fully say what the coordinator does next. Add those steps or say the sentence covers only the
   P2 part.

5. **MINOR — two wording points in the closing/§7 paragraphs (l.101 and ll.103–105).** (i) "the only
   deferred items are the frozen-file items named above" should read "the only c1 items deferred for G.1b":
   several applied lines carry optional evidence-root follow-ups (Titanic m5/m6/m7, MetaMaze m10, ETTh1
   m4/m5, Forest Cover m6), which are not c1 deferrals but make the broad sentence ambiguous. (ii) The
   label-table paragraph names Forest Cover c6(iii), which is a licence-attribution condition, not a
   label-table condition; it is not wrong to say it still stands, but say explicitly that the only
   label-table gate remains ETTh1 c6(iii), so the paragraph cannot be read as creating a second one.

## Scope confirmation

I changed nothing except writing this review file. Before writing it, `git status --porcelain` was clean and
`git diff origin/main --stat` showed only
`docs/r1/reports/tasl_chain_20261122/KIT_C1_DISPOSITION_20261126.md` (110 insertions). After writing, the
worktree contains that record plus this review file only; no record, kit report, review, spec, code, pin,
frozen file or census value was edited, and nothing was committed or pushed by me.

verdict: ACCEPTED
