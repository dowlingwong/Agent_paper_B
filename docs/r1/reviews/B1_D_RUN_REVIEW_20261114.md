# B1 `_d` normal completion / post-run retirement — independent review (14 November 2026)

**Record reviewed.** Repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `mac-b1-20261107`, tip
`10b92464797f6d3abe1e20a1463e723ae5073ebe`; `docs/r1/reports/B1_D_RUN_20261113.md` (sha256
`a1622acb3119097966dc5d746ef5c8e69ebbec2c7398b490893a0006583241c8`, 73 lines) and the STATUS entry. Read-only
review in a `/tmp` clone; TASL-7 read-only SSH. The accepted retirement unit is
`docs/r1/proposals/B1_D_POSTRUN_RETIREMENT_20261113.md` rev 2 at
`491e12416622f2d84580995cf96c90ec3a922471` (sha256
`f2be3f0fbe36daa68dd4d28e18f9f9c065c49c77f97a6dbde26ddf28143cc5b5`, 116 lines); rev 1 is `2c60b300`.

## Checks (all read-only)

- **Completion — PASS.** `b1.exit` sha256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`
  ("0\n"); `b1.log` `98dac95718b0ae00fc99b4d6eca599abd4663f7ecef3bb7579fcd1a51d74b735` ("B1_EXIT=0",
  no STOP); `batch_state.json` `1753fe96a1226e4aff75455a7f60c4c29c81c671110797949c5939c237d16a4c`
  (`status` COMPLETE, `completed` 260 entries, `interruptions` [], no failed units). All 260 roots in
  `completion_usage.txt` show completed yes (LLM 236). Only `trks_watch` in default tmux; `gpu0.lock`
  flock-free; no active marker; the two STOPs are empty `e3b0c442…` with dev/ino/size/content unchanged
  (mtime-only change 13:00:52Z→13:47:35Z, pre-existing and allowed).
- **Retirement artifacts — PASS.** `marker-receipt.json` `a28f0f78…` (dev 66306, ino 56261619, marker
  `60cd40fb…`); `marker-retirement_after_run.json` `13e04a2e565ac10a7dede6fdcaa7c97d76df0dbe40102e4bf46dd0d05f518d8c`
  (`retired: trackx_evidence.active.230b602ac3bd4400850ec008fc300304`, run/head correct); `.rc` "0\n"
  `9a271f2a…`; `.err` empty `e3b0c442…`; `.note` `48249582…` names the receipt path + `a28f0f78…`. Archived
  marker exists at `~/r1_locks/_to_delete/trackx_evidence.active.230b602ac3bd4400850ec008fc300304` with sha
  `60cd40fba5000330c6155859b861594bf4e4902e684f3efc4e6b5e32a9ddca7b`; nothing deleted. Watcher log has the
  new `2026-11-14T10:16:36Z marker gone: resume by hand …` line; no new priority marker, no `FORCED`.
- **Baselines — PASS (with scope notes below).** `run.sha256` 17 → `run_after.sha256` 21: only the four
  `*_after_run.*` additions; all 17/21 hashes still verify on TASL-7. All 53,778 non-`_to_delete` files in
  `batch.sha256` verify against the host (`sha256sum -c --quiet` rc 0); `batch.sha256` and `batch_after.sha256`
  are identical. STOP content/identity unchanged.
- **Report numbers — PASS.** Verifier rc 0 and `complete_batch_verifier.json`
  `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc`; 18 rows (3 anchors incl.
  `qwen25_coder_7b` + 15 candidates), phase b1, rule v2. `completion_usage.txt`
  `b5107bcbd5c106531f8176d618ac33d5e01b64bdc9083ebd5443e8b690b122f4`, rc 1, largest 16384, margin 0,
  9 truncated, 0 unencodable, 0 context_over, 9 parse_failed. `candidate_halves.txt`
  `c2cfa0c3003fc1ef30be0ebace104d50087fc4de8afd295db19f634d1d0281f6`, rc 0, descriptive only. Proposal
  journals: 4,827 total = 4,720 passed + 68 not_applicable + 14 rejected (7 `directive_symbol_differs` +
  7 `directive_new_differs`) + 23 `harness_precondition` + 2 `d25_inactive_key`; the §6 per-candidate/mode
  counts (incl. 11 on `olmo31_32b`) match. Anchor point `0.004596`, CI `[-0.000624, 0.008944]`, 12 instance
  pairs / 2000 bootstrap / seed 20261026, duplicate rate `0.4959` in `[0.4239, 0.5800]`, `DRYRUN_gate_override`
  false — all match `batch_state.json`.

## Findings

1. **MAJOR — report §2, lines 28–32: the `.err` deviation is described against the rev-1 unit, not the
   accepted rev-2 unit.** The accepted rev-2 block (`491e1241`, sha `f2be3f0f…`) defines
   `ERRF="$RUN_DIR/marker-retirement_after_run.err"` and writes it directly (`2> "$ERRF"`), with no `.err`
   `mv`; `$TMP.err` and `mv "$TMP.err" "$ERRF"` are the rev-1 block (`2c60b300`). The report's "which uses
   `$TMP.err`" and "instead of `$TMP.err`" are therefore false; the actual deviation is the wrapper's
   same-file `mv` (`stageB.log`), not the redirect path. The final artifact set and the unchanged unit file
   are correct. **Fix:** rewrite the paragraph to say the accepted rev-2 unit writes `$ERRF` directly and has
   no `.err` `mv`; the wrapper added the rev-1 `mv` (or an equivalent same-file `mv`), which was the no-op;
   keep the disclosure that the unit file was not changed and the four artifacts match.
2. **MINOR — report §8, line 72: "raw reply bodies are not retained by design" is false.** The 236 per-root
   `b1_proposals.jsonl` files retain `raw_reply` for 4,818/4,827 records, including all 14 rejected (e.g.
   `…/qwen3_coder_30b_a3b/b1/off/openml_credit_approval__s9001/b1_proposals.jsonl` has a 405-char
   `raw_reply` for a `directive_new_differs` rejection). **Fix:** say "the journal retains `raw_reply`; this
   report does not reproduce it" (or remove the parenthetical).
3. **MINOR — report §8, line 72: "the appendix draft's `⟨…⟩` fields are filled from §6" is not supported.**
   `docs/r1/reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md` at `999759b7` (sha
   `90ed083bd0902aceb500a82e723d9d8cb06d404120021bb68b0f4c230745be34`) still has
   `⟨table: candidate, mode, proposer calls, rejected, by check⟩`; the file is also absent from the report's
   branch at `10b9246`. **Fix:** "are to be filled from §6", or fill/merge the table.
4. **MINOR — report §1, lines 14–15: the capture listing includes `SHA256SUMS`, which is absent.**
   `/private/tmp/b1-d-postrun-20261114T101550Z/` has 13 files and no `SHA256SUMS` (its baselines are
   `batch.sha256`, `batch_after.sha256`, `run.sha256`, `run_after.sha256`, `stop.sha256`,
   `stop_after.sha256`). **Fix:** remove `SHA256SUMS` from the list or generate it.

## Residual notes (non-blocking)

- `$RUN_DIR` currently has 26 files: the 21-file retirement baseline plus the five verifier outputs
  (`complete_batch_verifier.json/.err/.rc`, `completion_usage.txt`, `candidate_halves.txt`). §2's "after 21"
  is the step-5 baseline, not the final count; STATUS's "changed only by the four" should likewise say "at
  retirement" or note the five later outputs.
- `$BATCH` has 88,024 files: 53,778 compared (all non-`_to_delete`) and 34,246 under `_to_delete` (including
  per-candidate retirement dirs). The report gives the 53,778 count but not the stated `_to_delete` exclusion.
- "No processes" holds for the `_d` run, but a stale `b1_handover_6835_20261108_a` tmux server (pid 1570627)
  and `ollama serve` (pid 1786525) remain on TASL-7; neither is a `_d` run process.
- The report does not claim the B1 manifests/verifier are published; STATUS says review is requested before
  publication. That is consistent.

VERDICT: changes required
