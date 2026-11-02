# Track X Stage A — fourth attempt STOP 4 (pinned-build chat-template parser vs `olmo31_32b`)

Date: 2026-11-02 ~04:00 UTC (05:00 Europe/Berlin). Attempt `r1_stagea_20261101_t7c3` on
TASL-7 (manifest `f568cd4f…`, checkpoint `7a386f8`, real lock 18:55 UTC previous day).

## What completed before the stop

Seven rows: anchors `random_valid`, `scripted`, model anchor `qwen25_coder_7b`, and
candidates `qwen38_27b`, `qwen36_27b`, `gemma4_31b`, `muse_glimmer_30b`. Every offload record
was `full: true, route: log_line` with no CPU fallback; cold true-first held. `muse_glimmer_30b`
completed but is a **candidate failure** (`failure_classes: ["grammar", "template"]`;
template render checks 5/5 false, thinking-on grammar requirement not met) — a recorded model
failure, not a STOP. The always-on thinking model took about 4 h (as predicted).

## STOP 4

`RuntimeError: STOP: root worker exit 1` at
`olmo31_32b/stage-a/32768/qualification`. The retained pinned-build server log shows
`init: chat template parsing error: Unable to generate parser for this template` →
`Unknown (built-in) filter 'tojson' for type Undefined (hint: 'tools')` →
`llama_server: exiting due to model loading error`. The GGUF embedded template is
byte-identical to the pinned HF template (`r1_template_scan_20261102/summary.json`), so this
is a **pinned llama.cpp build (620d222) template-parser incompatibility**, not an
offload/GPU/lease/cache failure.

Classification: the runbook keeps `template` as a candidate-level failure class; the
qualification path instead escalated it to an infrastructure STOP and ended the attempt,
losing the batch for evidence purposes (a STOPped batch is not Stage A evidence).

## Fix (independently reviewed)

- `qualify.py`: evidenced template parser failure (retained in-attempt server log, pinned
  build/model, recorded exit, explicit template error + model-loading error) becomes
  `TEMPLATE_FAILURE` with evidence; everything else stays `PREPARATION_STOP`. Exit code 0
  only for that evidenced class so the runner can classify it.
- `run_fresh_qualification` re-validates evidence kind, in-attempt log path and digest.
- `_stage_a_cooperative` writes a candidate row (`passed: false`, `failure_classes:
  ["template"]`, retained evidence, no prefill) and continues with the next candidate; it
  never starts that candidate's server and does not attempt the 16k fallback.
- Committed code `140e7d0` (qualify.py/exam_runner.py/tests/fixtures probe) and `0d4e987`
  (retained server-log fixture; the .gitignore needed `-f`), config binding `746b3d6`
  (`paper_commit=0d4e987`). Provenance note: the first commit's message was mislabeled by a
  failed shell chain; history was not rewritten and the reason is recorded in `0d4e987`.
- Independent review: v9 was **BLOCKed** because the classifier required `pins_match`/
  `server_stop` fields the real probe does not have (`docs/r1/reviews/TRACKX_STAGEA_STOP4_TEMPLATE_REVIEW_20261102.md`);
  the corrected real-shape classifier and the retained probe/log fixtures were **ACCEPTed**
  (`docs/r1/reviews/TRACKX_STAGEA_STOP4_TEMPLATE_REREVIEW_20261102.md`; snapshot v10
  `SHA256SUMS` `4f387beb…`). Relevant Mac subset: 384 passed, 1 skipped.

## Recovery (author's standing authorization)

At 06:20 UTC only the STOP guardian (pid 2306409) was still alive; the qualification server
and worker had already exited. The guardian was ended; verified LOCK-FREE (`gpu0.lock`
inode 56251186, size 0, nlink 1 unchanged) and GPU idle. Evidence:
`~/exam-x/work/r1_stop4_shutdown_20261102T062008Z/` (before/after, hashes). The STOP-4 batch
is not resumed or reused and is not Stage A evidence.

## Open author decisions (template policy)

`olmo31_32b` (and possibly other candidates with unguarded `tools`/`tojson` constructs —
`nemotron35_30b_a3b`, `qwen3_coder_30b_a3b` flagged in the scan) are now *excluded rows* under
the fix rather than batch STOPs. Whether to (a) accept the exclusion, (b) declare one template
repair per affected model (runbook allows one, declared before Phase 5), or (c) change the
llama.cpp build pin to one whose parser handles the template, remains an author decision.
The fix does not itself repair templates or change the pool.

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the fix passed at 06:37 UTC (route (i)
`offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation, validated release
`records_verified: 1`, lock free; preflight manifest `d9ae94be…`). The new, separately
identified attempt **`r1_stagea_20261102_t7d4`** was launched at 06:38 UTC (manifest
`517ba55b…`, 187 pinned files, 22/22 models verified) under the reviewed guardian
(pid 2593920), which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261102_t7d4`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261102_t7d4`. Checks are periodic (GPU/server,
journal/ledger progress, guardian/lease/`/proc/locks`, disk). Template-class hits become
candidate rows and do not stop the batch; any STOP preserves the site and is recovered only
under the author's standing authorization.
