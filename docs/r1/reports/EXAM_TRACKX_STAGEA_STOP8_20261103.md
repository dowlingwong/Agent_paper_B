# Track X Stage A — eighth stop (transient GPU-busy read at a retry boundary)

Date: 2026-11-03 ~17:27 UTC (18:27 Europe/Berlin). Attempt `r1_stagea_20261103_t7g7` on
TASL-7 (manifest `7d032351…`, checkpoint `70a7a6f`, real lock 10:49 UTC).

## What completed before the stop

Eleven rows: anchors, `qwen25_coder_7b`, `qwen38_27b`, `qwen36_27b`, `gemma4_31b` (template),
`muse_glimmer_30b`, `olmo31_32b` (template), `devstral_small2_24b`, `qwen36_35b_a3b`,
`gemma4_26b_a4b`, plus the **evidenced 32k OOM mechanical-failure row for
`nemotron35_30b_a3b`**. There were no offload deviations (`full:true, route:log_line`).

The STOP-7 fix was validated live twice in this attempt: `olmo31_32b` and `nemotron35_30b_a3b`
are failed-start servers whose retained probe records now carry the SAME-OFD
`lease_inheritance` proof (`kcmp_same_ofd: true`), `stopped_utc`, `returncode` and
`exited_early` — exactly what lease completion requires.

## STOP 8

Entering the 16384 retry for `nemotron35_30b_a3b`, the pre-qualification check raised
`PreparationStop: STOP: GPU not available for independent qualification`. The 32k probe
server had just exited; CUDA teardown can keep a process/memory/utilisation visible in
nvidia-smi for a few seconds, and the single instantaneous observation treated that moment as
"GPU unavailable", aborting the run at a retry boundary. This is a transient-timing tooling
defect, not a model/offload/lease failure. The batch is not Stage A evidence.

## Recovery

Under the author's standing recovery authorization the retained guardian (pid 3589647) was
ended and the lock verified free (`gpu0.lock` inode 56251186, size 0, nlink 1) with the GPU
idle. Evidence: `~/exam-x/work/r1_stop8_shutdown_20261103T202105Z/` (before: batch STOPPED at
11 rows, stop reason, lease STOP.json, hashes; after: clean site). t7g7 is not resumed or
reused.

## Fix (independently reviewed)

`await_idle_gpu(cfg)` adds a **bounded quiescence wait** (12 observations, 5 s apart) at the
pre-qualification call site only. The acceptance criterion is unchanged and fail-closed: the
final observation must have no compute apps, ≥1024 MiB free and ≤5 % utilisation; a foreign
workload never becomes acceptable by waiting (STOP after the deadline, last observation in the
message); an unknown census (`apps is None`) STOPs immediately. Tests: transient
busy→busy→idle returns the idle sample; a persistent foreign app still STOPs; unknown census
STOPs with no waits. Committed at `3b3283f` (config binding `19b8f33`, `paper_commit=3b3283f`);
scoped review `docs/r1/reviews/TRACKX_STAGEA_STOP8_QUIESCENCE_REVIEW_20261103.md` (ACCEPT with
conditions; snapshot v15 `SHA256SUMS` `23689415…`). Relevant Mac subset: 394 passed, 1 skipped.

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the fix passed at 20:25 UTC (route (i)
`offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation, validated release
`records_verified: 1`, lock free; preflight manifest `5f440643…`). The new, separately
identified attempt **`r1_stagea_20261103_t7h8`** was launched at 20:25:49 UTC (manifest
`95bfc8b6…`, 187 pinned files, 22/22 models verified) under the reviewed guardian
(pid 3896322), which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261103_t7h8`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261103_t7h8`. Periodic checks include progress; the
16k retry boundary now waits a bounded time for teardown, and completion must validate the
lease for every server record (failed-start included).

## Consequence

A fresh attempt is required (STOP batches are never resumed). t7g7 remains preserved
engineering evidence (candidate outcome map), but the new attempt `r1_stagea_20261103_t7h8`
re-measures all 22 models after the fix, with the same template/OOM/lease validations.
