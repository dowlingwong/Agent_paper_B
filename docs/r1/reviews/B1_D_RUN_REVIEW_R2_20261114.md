# B1 `_d` completion record rev 2 — independent re-review (14 November 2026)

**Record reviewed.** Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `mac-b1-20261107`, tip
`10e361094157e1b857264f2a9bc457becea1688e`; `docs/r1/reports/B1_D_RUN_20261113.md` (sha256
`b322ab40da3d344ed87d1804a2db64f45ccff559d9c2cda89d2c7273d5d2f27b`, blob `15aa5d8e`, 78 lines). Round 1 reviewed
`10b92464797f6d3abe1e20a1463e723ae5073ebe` (report sha `a1622acb3119097966dc5d746ef5c8e69ebbec2c7398b490893a0006583241c8`).
All checks read-only (fresh `/tmp` clone; TASL-7 SSH reads only).

## Finding status

1. **FIXED — §2 `.err` deviation.** The paragraph now attributes the direct `$ERRF` redirect to the accepted rev-2 unit
   `491e12416622f2d84580995cf96c90ec3a922471` (file blob `f2be3f0fbe36daa68dd4d28e18f9f9c065c49c77f97a6dbde26ddf28143cc5b5`);
   at that commit the unit sets `ERRF="$RUN_DIR/marker-retirement_after_run.err"` and writes `2> "$ERRF"` with no `.err`
   `mv`. `$TMP.err` / `mv "$TMP.err" "$ERRF"` is the rev-1 unit `2c60b300`, as the report now implies; no stale
   `$TMP.err` claim remains (grep clean). The wrapper-only same-file `mv` is correctly named the deviation, and
   `stageB.log` line 1 shows `…marker-retirement_after_run.err and … are the same file`.
2. **FIXED — §8 `raw_reply`.** Host journal (236 `b1_proposals.jsonl`, `_to_delete` excluded): 4,827 records, `raw_reply`
   present in **4,818**; all **14** rejected records carry `raw_reply`; the 9 records without it are exactly the 9
   `parse_failed` records. Checks: 4,720 passed, 68 not_applicable, 14 rejected (7 `directive_symbol_differs` +
   7 `directive_new_differs`), 23 harness_precondition, 2 d25_inactive_key — consistent with §4/§6.
3. **FIXED — §8 appendix draft.** `docs/r1/reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md` at
   `999759b7fec7158e930950544db6aac4988569bb` has sha `90ed083bd0902aceb500a82e723d9d8cb06d404120021bb68b0f4c230745be34`
   and still contains `⟨table: candidate, mode, proposer calls, rejected, by check⟩`; the path is absent at
   `origin/mac-b1-20261107` (10e36109). "Not filled by this record" and "not yet on mac-b1-20261107" are accurate.
4. **FIXED — §1 capture manifest.** `/private/tmp/b1-d-postrun-20261114T101550Z/` now has `SHA256SUMS` (sha
   `c67f887ac7e29ed1a70f85757159dadcebdfa53dce4a7c750e3a45c10d0b5de4`) with 13 entries; `shasum -a 256 -c` gives
   13/13 OK (rc 0). The directory holds exactly those 13 capture files plus `SHA256SUMS`; the report's "over the 13
   capture files" matches.
5. **PASS — counts and hashes.** `$RUN_DIR` is now 26 files: 17 → 21 at retirement (only the four `*_after_run.*`
   additions in `run.sha256`/`run_after.sha256`) → 26 after the five verifier outputs; the distinction is now explicit.
   Host hashes match the report: `b1.exit` `9a271f2a…`, `b1.log` `98dac957…`, `batch_state.json` `1753fe96…`
   (COMPLETE, 260 completed, 0 interruptions), `marker-receipt.json` `a28f0f78…` (dev 66306, ino 56261619, marker
   `60cd40fb…`), `marker-retirement_after_run.json` `13e04a2e…`, `.rc` `9a271f2a…`, `.err` `e3b0c442…` (0 bytes),
   `complete_batch_verifier.json` `07cb62de…`, `completion_usage.txt` `b5107bcb…`, `candidate_halves.txt` `c2cfa0c3…`.
   `batch.sha256` = `batch_after.sha256` (53,778 entries); both STOPs `e3b0c442…`. §6 per-candidate counts spot-check
   (olmo31_32b 11, glm47_flash 1, qwen3_coder_30b_a3b 2) match the journal. STATUS still requests review before
   publishing the manifests/verifier; the record claims no publication.
6. **PASS — scope.** `git diff 10b92464 10e36109` touches only the report (+15/−10); no code, pin or STATUS change.

## Residual notes (non-blocking)

- §2 still gives 53,778 without the stated `_to_delete` exclusion (host `$BATCH` has 88,024 files).
- `SHA256SUMS` is a post-hoc manifest (written after the 11:16–11:17 capture) but all 13 entries verify, so it attests
  the current capture contents.
- The round-1 non-`_d` leftovers (stale tmux server, `ollama serve`) are still present and remain outside §1's "no
  processes" claim for the run.

VERDICT: accepted
