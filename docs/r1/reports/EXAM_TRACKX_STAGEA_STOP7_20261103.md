# Track X Stage A — seventh stop (lease completion fix after a COMPLETE batch)

Date: 2026-11-03 ~09:16 UTC (10:16 Europe/Berlin). Attempt `r1_stagea_20261102_t7f6` on
TASL-7 (manifest `108b6318…`, checkpoint `9d2e213`, real lock 2026-11-02 16:54 UTC).

## What completed

The batch **completed all rows**: `batch_state.json` `status: COMPLETE`, 24 rows = 2 software
anchors (`random_valid`, `scripted`) + 20 candidates + model anchor `qwen25_coder_7b` +
sensitivity `olmo31_32b_think`. Every replay offload record is `full: true,
route: log_line` with no CPU fallback. Candidate outcomes: 10 PASS; template-class
failures `gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`, `laguna_xs21`,
`devstral_small2_24b`, `ministral3_14b`, `olmo31_32b` (parser), `lfm25_24b_a2b`
(+grammar), `muse_glimmer_30b` (+grammar); grammar-only `gpt_oss_20b`; offload
`nemotron35_30b_a3b` (evidenced 32k OOM row, then 16k retry also OOM). The STOP-4
(template row/continue) and STOP-6 (real-shape 32k OOM → 16k retry) fixes were validated
live in this batch.

## STOP 7 (post-completion lease accounting)

The runner then failed its own lease-completion check:
`STOP: server record incomplete for lease completion`. The guardian correctly retained the
lease (`STOP.json`, `completed_release: false`, `retry_permitted: false`). Retained state
shows exactly three `llama_server_*.json` records without `stopped_utc`: the **failed-start
qualification probe servers** for `olmo31_32b` (template parser error) and
`nemotron35_30b_a3b` (32k and 16k KV-cache OOM). `LlamaServerInstance.start()`'s
"exited before readiness" branch recorded `exited_early`/`failed_utc`/`log_tail` but never
finalized `stopped_utc`/`returncode`, so fail-closed completion accounting rejected the batch.
This is a record-finalization tooling defect, not a model/offload/lease behavioural failure;
the batch is nevertheless not Stage A evidence (a STOPped lease is not a validated release).

## Recovery

Only the retained guardian (pid 2911993) remained; it was ended under the author's standing
recovery authorization and the lock verified free (`gpu0.lock` inode 56251186, size 0,
nlink 1) with the GPU idle. Evidence:
`~/exam-x/work/r1_stop7_shutdown_20261103T093541Z/` (before: batch COMPLETE, the three
incomplete records, lease hashes; after: clean site). The t7f6 batch is not resumed or reused.

## Fix (independently reviewed)

`LlamaServerInstance.start()` now captures the SAME-OFD `lease_inheritance` proof
**immediately after Popen**, before the readiness loop: the lease FD is inherited at
fork/exec, so the reviewed ancestor→descendant `kcmp(KCMP_FILE)` + `/proc` FD dev/ino
verification works while the child is barely alive; the proof (and its `server_start_ticks`)
is stored in the record. If the child is already gone, the record carries
`lease_inheritance_capture {captured:false}` and no proof is invented — the guardian then
rejects the completion (intended fail-closed residual). If the child is alive but the proof
fails, the start still STOPs. The "exited before readiness" branch finalizes `stopped_utc`,
`returncode` and `stopped_before_ready: true` before raising the existing start-failure STOP.
The process was never healthy (no `healthy_utc`), so it could not have served a request; its
record now satisfies the runner's completion accounting **and** the guardian's completion
validation (which also requires the inheritance row) instead of permanently blocking release.
The completion validator, guardian, `stop()` path and preserved-server semantics are
unchanged. Committed at `6f1b90b` (config binding `70a7a6f`, `paper_commit=6f1b90b`).
Independent review: v14 was **BLOCKed** because it added only `stopped_utc` while the
guardian also requires `lease_inheritance` (`docs/r1/reviews/TRACKX_STAGEA_STOP7_COMPLETION_REVIEW_20261103.md`);
v14b (pre-readiness proof capture + the test file frozen in the snapshot) was **ACCEPTed**
(`docs/r1/reviews/TRACKX_STAGEA_STOP7_COMPLETION_REREVIEW_20261103.md`; snapshot v14b
`SHA256SUMS` `9724933f…`). Relevant Mac subset: 391 passed, 1 skipped; the three pre-existing
`test_llama_server_instance.py` failures are macOS /proc-only limits (verified against base).

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the fix passed at 10:47 UTC (route (i)
`offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation, validated release
`records_verified: 1`, lock free; preflight manifest `007b8e8a…`). The new, separately
identified attempt **`r1_stagea_20261103_t7g7`** was launched at 10:49:04 UTC (manifest
`7d032351…`, 187 pinned files, 22/22 models verified) under the reviewed guardian
(pid 3589647), which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261103_t7g7`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261103_t7g7`. Periodic checks include progress; the
failed-start lease proof is exercised by the template/OOM candidates; completion must now
validate for all server records.

## Consequence

A fresh attempt is required (STOP batches are never resumed). The completed t7f6 data set
remains preserved as engineering evidence and as the candidate outcome map (useful for the
template failure analysis), but it does not enter Stage A evidence; the new attempt
`r1_stagea_20261103_t7g7` re-measures all 22 models after the fix. The author's template
policy (accept exclusion rows now; targeted byte-equal repairs after completion; build-pin
change only after a diagnostic) remains in force.
