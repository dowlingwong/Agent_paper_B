# Track X Stage A — third attempt STOP 3 (per-candidate deadline vs always-on thinking)

Date: 2026-11-01 ~21:13 UTC (22:13 Europe/Berlin). Attempt `r1_stagea_20261101_t7b2` on
TASL-7 (manifest `8fb258b1…`, checkpoint `9b7fdd1`, real lock acquired 18:55 UTC).

## What completed before the stop

Six candidates: anchors `random_valid`, `scripted` plus `qwen25_coder_7b` (7B),
`qwen38_27b`, `qwen36_27b`, `gemma4_31b`. **Every offload record was `full: true`,
`route: log_line` with `offloaded N/N` and no CPU fallback** (route A fix works on TASL-7);
cold true-first was observed on `qwen38_27b` (`first_prompt_calls=50`,
`first_prompt_cache_hits=0`); no lease/FD/OFD anomaly.

## STOP 3

`batch_state: STOPPED`, reason `TimeoutError: STOP: campaign deadline`;
`root_timeout_seconds = 3600` fired while `muse_glimmer_30b` was in its descriptive replay.
Measured rate: **~58 s per request** (journal sequence 118→119 monotonic delta); the
candidate needs ~400 calls (200 true + 200 false), i.e. 5–6 h. `muse_glimmer_30b` is an
**always-on thinking** model (2048-token budget); the registry has five such candidates
(`muse_glimmer_30b`, `lfm25_24b_a2b`, `gpt_oss_20b`, `rico03_qwen36_27b`,
`olmo31_32b_think`).

Classification: **infrastructure/tooling (deadline) STOP**, not a model/offload/cache/lease
failure. Qualification had PASS (`footprint_mib 16172`, `route log_line`); the replay was
progressing when the cap fired. Because Stage A workers must never be signalled, the timeout
left a preserved orphan worker still writing into the STOPped batch; that orphan is not
evidence, and the batch is not Stage A evidence.

## Author decisions and recovery

The author authorized (1) recovery by the coordinator, (2) a deadline fix, (3) a multi-night
continuous run with the guardian holding the lock and periodic checks.

Recovery (recorded, 21:42:10 UTC): ended the preserved native server **2256704** (FD 4 →
`gpu0.lock`), the orphan `r1.exam.stage_a` worker **2256930**, and the STOP guardian
**2206538**; verified LOCK-FREE (`gpu0.lock` inode 56251186, size 0, nlink 1 unchanged) and
GPU idle. Evidence: `~/exam-x/work/r1_stop3_shutdown_20261101T214210Z/` (before/after,
hashes). STOP-1/STOP-2/STOP-3 evidence untouched; no batch resumed or reused.

## Deadline fix (independently reviewed)

`root_timeout_seconds`: 3600 → **43200** (12 h per worker). It is a watchdog cap, not a
scheduling target; the dedicated-server watchdog still detects hangs; B1/B2 remain hard STOP.
Committed at `7a386f8` (config-only; `paper_commit` stays `d6841e6`, no runtime-checked path
changed). Independent scoped review ACCEPT with conditions:
`docs/r1/reviews/TRACKX_STAGEA_STOP3_DEADLINE_REVIEW_20261101.md` (SHA-256
`48ac9b8e…a28`; snapshot v8 `SHA256SUMS` `2f947752…`). The reviewer recorded that a
worker alive but making no progress can still hold the GPU up to the cap, so periodic checks
include journal/ledger progress; a future reviewed progress-based watchdog is recommended.

## Consequence for the schedule

Stage A is a multi-night run: five always-on thinking candidates at ~5–6 h each plus 17
faster candidates (~10–20 min each) is roughly 20–30 h of GPU time. The author accepted a
continuous run; the guardian holds the real lock across the run, checks are periodic, and
the attempt is monitored.

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the v8 config/manifest passed at 21:47 UTC
(route (i) `offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation,
validated release `records_verified: 1`, lock free; preflight manifest `f5086123…`).
The new, separately identified attempt **`r1_stagea_20261101_t7c3`** was then launched at
21:47:49 UTC (manifest `f568cd4f…`, 187 pinned files, all 22 models verified) under the
reviewed guardian, which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261101_t7c3`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261101_t7c3`. The preflight/Stage A evidence is new and does
not reuse any STOP batch; checks are periodic (GPU/server, journal/ledger progress,
guardian/lease/`/proc/locks`, disk). On any STOP the site is preserved and recovery requires
the author's authorization.
