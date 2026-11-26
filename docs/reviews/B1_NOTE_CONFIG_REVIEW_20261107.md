# Independent review — unsigned B1 note and config, 7 November 2026

AI-assisted (Codex). **ACCEPTED for unsigned note/config candidate scope only**, target `4365315e987bb576bc637fee670dd3ac9b423797`, reviewed on a separate clean clone. This review does not approve the final authorization note, exact final checkout, host preflight, or B1 launch. No remote host, model, GPU, server or experiment was accessed or run.

## Exact reviewed inputs

- `docs/r1/proposals/AUTH_DRAFT_trackx_b1_20261107.md` SHA-256 `a53bfb5ca2dcec5896b6aa09452ef41f890f6a0900345a5d834c7091824dd285`.
- `r1/scripts/configs/exam_b1_v2.json` SHA-256 `5d1cf9f241dc08288f88a99e17b60aeb8621602fb264dde969e06d9efae38267`.
- `docs/r1/PLAN.md` SHA-256 `8bdd57da88f514422214aad0285bce0ae1cdfa01c7e7451d32c9561b183287ba`; source prompt `docs/r1/prompts/MAC_OVERNIGHT_PROMPT_20261107.md` SHA-256 `4c4a2e6dfdaa8f12ea14399de23bdf73a1f019fbb14a5726822203fe03cbfedb`.

## Checks

1. PLAN §10's dated 7 November table records the author's supplied Q0 wording verbatim in `R1-EXAM-RULE-X5V2`, Q1 in `R1-EXAM-B1-ACCEPTANCE-RECORD-07NOV`, the fixed Q2 instruction and the author host/B1 words, with a pointer to the full prompt. Q0 is conditional: it does not establish completion of launch gates. The new proposal has exactly one JSON block and `approved: false`; the configured live authorization path `docs/r1/authorizations/trackx_b1_20261105.md` is absent in this checkout.
2. Config and candidate note agree on rule SHA `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`, nodes `digits_mlp`, `openml_credit_approval`, `openml_ionosphere`, call cap 80, workers 20, host TASL-7 and GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`. The rule file's actual SHA matches. Note and config both carry the original Stage A SHA `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c`, amendment SHA `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`, and Q1 O1 acceptance SHA `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e`. The latter matches the actual committed O1 report; the report identifies both table hashes. Actual TASL-7 table bytes were not inspected by this review.
3. Config source `docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json` hashes to `84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd`; this matches the note's `anchor_duplicate_reference_sha256`. Config lower/upper equal the JSON's `0.42386590667728663` and `0.5800007633587785`. A local call to the existing `verify_anchor_reference` against the reviewed config passed; it performed no inference or remote access. The separate `B1_ANCHOR_DUPLICATE_REFERENCE_REVIEW_20261107.md` accepts the fixed Q2 computation and definition match; this note review does not independently repeat that computation.
4. The proposed code pin `fde124751be70d96aabbdbbce4ea565ee9735a49` is an ancestor of `4365315`; `git diff --name-only` from that pin to the target is empty for the exact protected exam paths checked by `ExamRunner`. Earlier independent reviews accept the anchor-note digest binding and host/GPU note-to-config binding within their synthetic code scope. Their presence does not establish live GPU identity or lease continuity.

## Remaining STOPs

The final note remains unsigned and must not be made `approved: true` or installed merely because this candidate review passes. The required synthetic Stage A-to-B1 interruption coverage, B1-related historical failures/full-suite assessment, live TASL-7 worker determinism and host checks, independently reviewed adapted handover, preflight and exact final combined-checkout review remain separate prompt §0.3 conditions. Host bytes, available full-output space, actual 20-worker headroom, process ownership and lease/server descriptor must be established at the authorized site before launch. B2, X.7 and sweep 2 remain unauthorized. If a condition fails, preserve the state and follow the prompt's STOP procedure.
