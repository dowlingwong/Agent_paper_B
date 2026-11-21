# Track G G.0 U2 — `autoresearch_fixedtokens` under option A on TASL-2 — RESULT (21 November 2026)

**Status: PASS (ENGINEERING_ONLY U2 census row; one host difference: TASL-2 instead of the earlier Ada
attempt).** Authority: `R1-TRACKG-AR-COND7` option A, author-signed `R1-TRACKG-AR-U2-TASL2` (starts now;
reaches main after the sweep-2 launch), R1-TRACKG-G0-GO, R1-HARNESS-ISOLATION, R1-TRACKG-PORT-DECISIONS.
The T1 labels themselves run on H200 (`R1-T1-HOST-H200`); this is a U2 raw-cost row only.

## Kit / host / preconditions

- **Unit provenance:** reviewed U2 unit `U2_ISO_AUTORESEARCH_UNIT_20261121.md` sha `3bb015a1…`; executed
  amended unit (TASL-2 adaptations: host TASL-2, env `ar-cond7a`, data root `/home/dowling/r1_trackp/data`,
  20,000 MiB free-floor instead of 40 GiB, no Paper A gate, host difference disclosed) is preserved as
  `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` beside this result (sha b83d9159…; the reviewed `3bb015a1…`
  bytes were not preserved, recorded residual); the one clean smoke is the U2 measurement
  under author-signed `R1-TRACKG-AR-U2-TASL2` (the unit's pre-U2-smoke→U2 sequence is collapsed and recorded).
- Kit worktree `/home/dowling/r1_trackp/harness_cond7a_20261121` @ **`7330338`** (base `448f682`; isolation
  core `68cdd1a` + accepted Ada fix `5403392e` + option A), detached/clean; committed
  `frozen_pin_sha256` **`147f0d35…`** (20 entries), deployed TASL-2 pin **`ca049086…`** (21 entries, path-
  dependent data link; Ada's deployed value `069e987a…` is not expected here), spec raw `5c1bdf3d…`.
- TASL-2 host §3 checks PASS and independently ACCEPTED (`TASL2_ISOLATION_HOST_CHECK_20261121.md`/review):
  userns/cgroup/ptrace/non-root/sys.path/sandboxed smoke/GPU-in-sandbox all pass; CUDA IPC remains untested
  and is not used by option A.
- Env separate `/home/dowling/r1_trackp/venvs/ar-cond7a` (Python 3.12.15, torch 2.6.0+cu124; freeze 122
  lines `11def6ad…`); data `/home/dowling/r1_trackp/data/autoresearch_fixedtokens`, manifest
  **`ab7186d2…`** (13 files, 963 M, HF revision `915333b4…`).
- Run: one exclusive RTX 4090 (`GPU-4d623e76…`) under `flock ~/r1_locks/gpu0.lock` (no lease-log write),
  live delegated scope `MemoryMax=8G`, `AR_TEST_CGROUP_PARENT`, CUDA masked, cpus 0-7, one
  `port_smoke_gpu`; 9 records = 8 executed + refused s001; `CHECKLIST_E_PASSED`; no co-tenant; no retry.

## Isolation / option A

Every executed record `isolation.effective:true`, `waivers {}`, `exceptions []`, private `/dev/shm`
(`shared_dev_shm:false`), log intact, result channel, cgroup kill; the option-A node has no
`cuda_share`/`cuda_open`/`bind_cuda` call sites; the worker→parent logits transfer is the CPU memfd path;
`torch.cuda.init()` present in `cuda_open` (helper unused by this node). Cgroup peak 5.17 GiB, OOM events 0,
swap 0; peak worker VRAM baseline 1,980.1 MB; parent peak 6,560.3 MB; max of any run 3,720.4 MB; whole-smoke GPU sampler upper bound
12,436 MiB (labelled, includes co-tenants by construction).

## Raw cost / slowdown (TASL-2, vs the 17 Nov Ada un-isolated baseline)

| quantity | value |
|---|---|
| B1 `s000_baseline` | **218.951 s**, `val_bpb 1.293937` (B1/B2 median 218.7935 s) |
| B2 repeat | **218.443 s**, `val_bpb 1.293937` (exact) |
| whole smoke wall | **1,791.0 s** (29:49) |
| B1 vs Ada 67.901 s | **3.225×** (+151.05 s) |
| transfer surrogate | **0.2345 s per logits request** ((B1−67.901)/644), in the predicted 0.15–0.25 s band |
| B1 bpb vs Ada 1.291068 | +0.002869, cross-host 4090/TASL-2 vs L40S/Ada (disclosed, not normalised) |
| whole smoke `time -v` | user 1,529.05 s, sys 395.16 s, max RSS 3,204,520 kB; wall 1,791.0 s (time-v 1,789.26 s) |

The 3.2× slowdown is the measured **cross-host** option-A cost and will be recorded in the census after this
result review; the 5,211.3 MB peak in the Ada report is a different host/base, not the TASL-2 row.

## Record

- Smoke result report `TASL2_AR_COND7A_RESULT_20261121.md` sha `8814eecc…` + captures `_captures/`
  (7,056 files, 170 MiB, SHA256SUMS `32f5009a…`).
- This U2 result is the same single clean smoke (the task's one clean isolated smoke); no second U2 run was
  made; `s001` refused record is 166,300 B; the capture bundle content is 152,751,278 B (the 161,531,825 B figure
  is the Mac bundle/packaging size, not content); the initial false STOP had an empty stderr and is preserved. A false first `RESULT_STATUS` STOP caused by a slowdown-script parse error is preserved and disclosed;
  the smoke was not re-run; final verifier rc 0 / issue [].
- Deviations: host TASL-2 (authorized by the author-signed row, which is not yet on committed main at
  execution time), 4090 vs Ada L40S; **3.2× is a cross-host option-A slowdown, not a within-host comparison**;
  bpb/VRAM not normalised; no Paper A gate needed on TASL-2 but exclusivity controls used; no prewarm
  (B1≈B2 shows no compile distortion); **ENGINEERING_ONLY: not evidence, no T1 label, no noise floor/D21/D28,
  one node, no CUDA IPC claim**; the census row is added only after this result review and the U4 update review.
- Attempt-1 archive and TASL-7 untouched; no deletion/push/HTCondor; T1 labels remain H200.

## Revision note (21 Nov)

Reviewed object: `ca3bcadd…` (57 lines/3,893 B). Intermediates: `8430854c…` (67/5,181 B) and `c03f0cbd…`
(67/5,204 B, +23 B parent-peak text). Current sha/size are recorded in the U4 acceptance sidecar; reviewed→final = +19 lines/+1,948 B and
`c03f0cbd…`→final +9 lines/+637 B. Old bytes are not preserved; measured values are unchanged. Executed
unit sibling `b83d9159…` is 74 lines/6,374 B and is byte-identical to the committed Ada-targeted unit; reviewed
`3bb015a1…` not preserved. Open U2-review C3/C4 residuals: author-row record location and the reviewed/executed
unit preservation nuance.
