# D.3 revision 4 G2 binding review — 27 Nov 2026

Independent review by a fresh Codex agent for `local/20261127-13`. I did not write the candidate.
Base `98c571d22251a9d57a6d157950bd5ac8c340e17b`. Reviewed commit
`ba120290c196cf725bbf61f046ec777ebcd6ee4e`. The updated draft's SHA-256 is
`d1cd146a40dbfdf72bccf9d9b3d47d41bf85229f89d79b34bae7ae5c2efc93d4`.

The diff binds the G2 artifact in §5.0 and §14 of `D3_PREDECLARATION_DRAFT_20261122.md`.
I verified its published blob and the working copy at
`docs/r1/reports/d3_g2_20261127/d3_constants.json` both hash to
`4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`, matching both places in the
draft and the `compute/20261127-17` receipt. This is the artifact whose independent re-fit was
byte-identical. The first candidate cited the fitter-code acceptance. The re-check confirms the corrected
citation to the separately published artifact acceptance, `D3_G2_CONSTANTS_FIT_REVIEW_20261127.md`.

`python -B -m r1.c3.d3_constants check docs/r1/reports/d3_g2_20261127/d3_constants.json` returned 0
and reported the expected SHA-256 and seven node selections. All seven files listed in
`captures/SHA256SUMS` verified from the report directory. `git diff --check` passed, with just the draft
changed and no code or test edits. I used the artifact and committed records without opening release
partitions or running a fit.

The existing harness and verify-seed bindings carry through. The SMAC3 version and environment, the
gate-report path and key, `signed_by` and `frozen_utc` are still pending. The draft has `frozen: false`.
The coordinator can receive this pin after review. The complete declaration, script and tests still
require step (5) review and the diff-only re-check before the coordinator can freeze the declaration.

Verdict: ACCEPTED for the G2 pin-only update.
