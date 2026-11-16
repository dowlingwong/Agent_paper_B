# Track X Stage A — fifth attempt STOP 5 (stale diagnostic llama-server; occupancy pre-check)

Date: 2026-11-02 ~06:43 UTC (07:43 Europe/Berlin). Attempt `r1_stagea_20261102_t7d4` on
TASL-7 (manifest `517ba55b…`, checkpoint `746b3d6`, real lock 06:38 UTC).

## STOP 5

The attempt stopped at its FIRST qualification (`qwen25_coder_7b`) with
`RuntimeError: STOP: observed server count or identity mismatch`. A stale `llama-server`
for `ornith10_9b` (pid 2589942, started 06:25 UTC, `-ngl 0` CPU-only) had been left behind by
the earlier killed template-screen diagnostic; the D3 census correctly saw two `llama-server`
processes and failed closed. Two anchor rows existed; no server was started by this attempt;
no `stage_a_table.json`; not Stage A evidence.

Classification: operator-side hygiene (a diagnostic leftover), not a pipeline defect. The
runtime census behaved correctly. Note for the record: that stale server was CPU-only
(`-ngl 0`), so the `/proc` executable-basename scan — not the GPU compute-app check — is the
guard that matters here.

## Recovery (author's standing authorization)

At 07:09:48 UTC the stale server 2589942, the preserved qwen25 server 2595132 and the
guardian 2593920 were ended; verified LOCK-FREE (`gpu0.lock` inode 56251186, size 0, nlink 1)
and GPU idle. Evidence: `~/exam-x/work/r1_stop5_shutdown_20261102T070948Z/`. The STOP-5 batch
is not resumed or reused.

## Fix (independently reviewed)

The reviewed launcher now refuses to prepare a run when the host is already occupied:
`visible_llama_servers()` scans `/proc/*/exe` for executable basename exactly `llama-server`
(unreadable/vanished links skipped; explicitly an occupancy check, not an exclusivity proof)
and `host_occupancy_check()` refuses if such a server exists or if
`llama_server_instance.gpu_compute_apps()` reports a compute process (skipped only when
nvidia-smi is unavailable). It runs before the manifest is written, so a doomed batch is
refused instead of stopping at its first qualification; the runtime census is unchanged and
remains the gate. Committed at `caa2f70`; config binding `5d66967`
(`paper_commit=caa2f70`). Independent scoped review:
`docs/r1/reviews/TRACKX_STAGEA_STOP5_OCCUPANCY_REVIEW_20261102.md` (ACCEPT with conditions;
snapshot v11 `SHA256SUMS` `f2c6adf5…`). Relevant Mac subset: 386 passed, 1 skipped.

## New attempt after the fix

A fresh TASL-7 real-lock preflight under the fix passed at 07:14 UTC (route (i)
`offloaded 29/29`, FD/OFD `kcmp` rc 0, zero generation, validated release
`records_verified: 1`, lock free; preflight manifest `0f584eaa…`). The new, separately
identified attempt **`r1_stagea_20261102_t7e5`** was launched at 07:14:25 UTC (manifest
`4abb1b83…`, 187 pinned files, 22/22 models verified) under the reviewed guardian
(pid 2602930), which holds the real `gpu0.lock` for the whole multi-night run.
Out: `~/exam-x/work/r1_stagea_20261102_t7e5`; lease evidence:
`~/exam-x/work/r1_stagea_lease_20261102_t7e5`. Checks are periodic; template-class hits
become candidate rows; any STOP preserves the site and is recovered only under the author's
standing authorization.

Operational note: the killed template-screen diagnostic left the stale server because its
child ran in a new session; future diagnostics must kill their process groups in a `finally`
block (the launcher occupancy check now catches any such leftover before a run).
