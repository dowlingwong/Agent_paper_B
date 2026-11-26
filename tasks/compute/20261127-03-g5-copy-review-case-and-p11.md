# compute/20261127-03 — G.5: fix the copy review's verdict line; assemble the P11 host-test record

Owner: compute. Runbook §2 order 2B. After the expansion launch (`compute/20261127-02` item 1), before D.3 code.

1. **B3 of the G.5 render review.** `docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md` (on `main` since `166db0eb`) reads
   `verdict: ACCEPTED` in lower case, and the switch (`g5_tasl.check_seven_copy`) checks case-sensitively, so every G.5 job would
   STOP. Read the exact line `check_seven_copy` requires, then add that line in a one-commit docs branch from `main` with the same
   reviewer's confirmation. The content of the review does not change. Report the new sha256: the spec's review path stays, and
   the local worker re-renders with the new hash.
2. **P11 host-test record (prepare now; the author's reading is pending).** One table for C1–C16 of the G.5 draft §10: for each
   item, existing evidence at the current code (G.4b pilot, `main-t1-g5-smoke-20261124`, the G5 prep of 26 Nov, xc2/xc3, the
   REL copy) with path and sha256, or "not covered". Run nothing new yet. The coordinator's sheet
   `sheets/G5_P10_P11_S9_SHEET_20261127.md` option (b) says which parts are needed before publication. Once the author decides,
   a task file names the tests to run.

Report: the branch tip and hash for 1; the table for 2 (tier D, on a branch).
