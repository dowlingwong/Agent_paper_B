# Track X Stage A — sixth attempt STOP 6 (real-shape 32k OOM at `nemotron35_30b_a3b`)

Date: 2026-11-02 ~13:55 UTC (14:55 Europe/Berlin). Attempt `r1_stagea_20261102_t7e5` on
TASL-7 (manifest `4abb1b83…`, checkpoint `5d66967`, real lock 07:14 UTC).

## What completed before the stop

Eleven rows: anchors `random_valid`/`scripted`, model anchor `qwen25_coder_7b`, candidates
`qwen38_27b`, `qwen36_27b`, `gemma4_31b`, `muse_glimmer_30b`, `olmo31_32b`,
`devstral_small2_24b`, `qwen36_35b_a3b`, `gemma4_26b_a4b`. Every offload record was
`full: true, route: log_line` with no CPU fallback. The template-classification fix was
validated in a real run: `olmo31_32b` became a `passed:false / failure_classes:['template']`
row with `chat_template_parse_error` evidence, `retry_at_16k: false`, no replay server and no
16k fallback, and the batch continued. `muse_glimmer_30b` recorded candidate failures
`grammar`+`template`; `gemma4_31b` recorded `template` (both deterministic across attempts).

## STOP 6

`RuntimeError: STOP: root worker exit 1` at `nemotron35_30b_a3b` qualification. Retained
pinned-build log: `ggml_backend_cuda_buffer_type_alloc_buffer: allocating 102.00 MiB on
device 0: cudaMalloc failed: out of memory` → `failed to allocate buffer for kv cache` →
`exiting due to model loading error`. This is the expected 32k-context OOM for a 30B-class
candidate on a 24 GB GPU; the runbook intends an evidenced mechanical failure with a 16k
retry. The accepted classifier required `server_stop.returncode` and `pins_match` — fields
the real startup-failure probe leaves unset (the same real-shape defect found in STOP 4) —
and its OOM regex was anchored at column 0 while real logs prefix the line with a
timestamp/level. The evidenced OOM therefore remained `PREPARATION_STOP` and ended the batch
after 11 rows; the batch is not Stage A evidence.

## Fix (independently reviewed)

- `known_load_oom(raw, cfg, out, spec)`: real-shape preconditions — retained in-attempt log
  (SHA stored), `verdict=STOP`, no footprint, top-level `gpu_uuid`/`binary_sha256`/
  `model_sha256`/`build.version_line` equal to the accepted pins, a recorded startup exit
  (`server_stop.returncode` or `exited during start (rc=N)`), the cudaMalloc-OOM line
  anywhere in the log, and the post-stop healthy-idle census; evidence records log path+SHA,
  matched line, exit evidence and pins.
- `run_fresh_qualification`: re-verifies the OOM evidence kind, `healthy_idle_after_stop`,
  and the evidence log's in-attempt path + digest; the 16k fallback path is otherwise
  unchanged.
- Tests use the retained STOP-6 probe + log as fixtures: real-shape positive
  (MECHANICAL_FAILURE, exit 0, `(rc=1)` exit evidence, healthy idle); negatives (mutated
  binary/model/build, missing OOM line, no recorded exit) → PREPARATION_STOP; the synthetic
  32k→16k fallback test now retains the OOM log + digest. Committed at `14b9f79` (config
  binding `9d2e213`, `paper_commit=14b9f79`); independent scoped review
  `docs/r1/reviews/TRACKX_STAGEA_STOP6_OOM_REVIEW_20261102.md` (ACCEPT with conditions;
  snapshot v12 `SHA256SUMS` `3aa26eda…`). The only condition was fixture provenance: the
  log fixture had been captured through `cat` over SSH and replaced with the exact retained
  bytes (`9ec47056…`, 21,187 B, 225 lines; snapshot v13 `SHA256SUMS` `75e37587…`), which the
  reviewer verified byte-identical. Relevant Mac subset: 388 passed, 1 skipped.

## Recovery (author's standing authorization)

At 16:47 UTC only the guardian 2602930 was alive (the qualification server and worker had
exited); it was ended and the lock verified free (`gpu0.lock` inode 56251186, size 0, nlink 1)
with the GPU idle. Evidence: `~/exam-x/work/r1_stop6_shutdown_20261102T164722Z/`. The STOP-6
batch is not resumed or reused.

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the fix passed at 16:53 UTC (route (i)
`offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation, validated release
`records_verified: 1`, lock free; preflight manifest `cb5fb2b2…`). The new, separately
identified attempt **`r1_stagea_20261102_t7f6`** was launched at 16:54:31 UTC (manifest
`108b6318…`, 187 pinned files, 22/22 models verified) under the reviewed guardian
(pid 2911993), which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261102_t7f6`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261102_t7f6`. Periodic checks include progress; template
hits remain candidate rows; the 16k fallback is reachable only through an evidenced
healthy-idle 32k OOM.

## Consequence

A fresh attempt is required (STOP batches are never resumed). With the real-shape OOM fix,
future 32k OOMs become evidenced mechanical failures with a 16k retry instead of batch STOPs;
template-class hits remain candidate rows. The author's template policy decision (accept
exclusion rows now; targeted byte-equal repairs after completion; build-pin change only after
a diagnostic) remains in force.
