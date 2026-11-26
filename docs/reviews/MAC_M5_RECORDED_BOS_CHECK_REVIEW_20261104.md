# Independent review: recorded BOS consistency check

Date: 2026-11-04. AI-assisted (OpenAI Codex). Initial verdict: **NOT ACCEPTED**. Re-check verdict: **ACCEPTED**, within the conditional limits below.

Reviewed the supplementary script and report in `/private/tmp/paper-b-mac-20261104/docs/r1/reports/MAC_M5_RECORDED_BOS_CHECK_20261104.{py,md}`, the copied t7j10 evidence under `/private/tmp/paper-b-o1-evidence/j10`, and the committed O1 audit script, output and report. No server, model, network, or tokenizer was accessed.

## Finding: conditional inference needs an explicit journal-identity assumption

The supplementary script consumes the **local copied** journals; the O1 tokenizer audit script reads the original host-side paths. For its conclusion to combine the two, the corresponding journal request/response records must be identical to those O1 recomputed. The table SHA binds the table, not the journal files. The local script checks that each response matches the digest stored beside it; that self-consistency check does not independently bind the copied journal to O1's original. Add this identity assumption explicitly to the report's conditional inference and state that this check does not establish it. Alternatively, document and verify an authoritative O1-time journal digest binding the relevant originals and copies. This finding does not claim a mismatch exists.

## Checks and limits

- The script SHA-256 is `b94bc077c06f1fff2c24b0e955eff79311013ed569478ad59d411863eefdd9ef`. The copied table SHA-256 is `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103`, matching `OPS_O1_20261104.md`.
- Running the script on the copy reproduced 110 byte checks, 330 token checks and zero first-ID mismatches. A separately written read-only count of the row methods and first recorded response IDs reproduced those totals. Both software anchors are excluded.
- The O1 source checks the tokenizer's `bos_token_id` against the recorded ID and requires `hf == prefix + served` and server IDs equal HF IDs, but requires only `len(prefix)==1`; its output reports 55/55 for each of the same eight model rows. Thus, conditional on that audit being correct and on the corresponding journal records being the same, the supplementary first-ID comparison closes the specific missing equality for the observed token cases. This review did not rerun the tokenizer audit.
- This check does not independently establish HF renders, tokenizer identity, actual server behavior, or absence of swallowed D3 STOPs. It is not a new Stage A measurement or acceptance and does not revalidate the entire dataset. The row-to-wire pairing is by sequence and row order and rests on the original evidence structure; request hashes and full provenance are outside this script's verification.

## Re-check

The revised report explicitly conditions its inference on copied-journal identity and distinguishes the journal's self-recorded digest from independent provenance. The finding above is resolved. One further wording correction remains: the report says O1 recomputed the token rule and server-token equality for all 440 comparisons, but 110 comparisons took the byte path; the O1 code checks token equality only for the remaining 330. Describe all 440 as template comparisons and 330 as token-path comparisons.

The authoring agent corrected the 440/330 wording. Re-check **ACCEPTED** for the reviewed report SHA-256 `9f08126f872b8971021d253696b8d9ce078879f4b01d0e22db1e1902ca0dca10` and script SHA-256 `b94bc077c06f1fff2c24b0e955eff79311013ed569478ad59d411863eefdd9ef`. The conditional inference and provenance limitations above remain essential. This is not acceptance of a new experiment or of any stronger tokenizer-based conclusion.
