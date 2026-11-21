# Sweep 2 launch and worker-gate STOP (21 November 2026)

**ENGINEERING_ONLY post-launch record. Labels remain sealed (R1-BX-D8-CONFIRM).**

- launch commit: published `main` `4aac52092813b2b01ddb96cd7d135c390aeff645`; sweep-2 note sha `349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a`.
- C3b at the launch commit (job 759811, H200): 7/8 with exactly the declared R1-S2C3B-WDBC `openml_wdbc` `invalid_rate` shortfall (observed 0.30, required `< 0.3`); record `liveness_results.declared_exception` = R1-S2C3B-WDBC, `pass: true`; sealed `/ceph/srv/dwong/paperb/sweep2/s2c3b-20261121-a/liveness-prompt/`.
- launch: S2-C5 enabled with both keys for `s2ev-20261119-a` only; 16/16 H200 chunks submitted; specs/JDLs re-rendered at the launch commit pinning the published note sha. No change to `main` before/after the launch.

## Chunks

| cluster | chunk | host | GPU (UUID) | trials | successes | failures | runtime_errors | chunk gate |
|---|---|---|---|---|---|---|---|---|
| 759812 | digits_mlp-append_only_summary | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 360 | 0 | 0 | PASS |
| 759813 | digits_mlp-none | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 360 | 0 | 0 | PASS |
| 759814 | openml_breast_w-append_only_summary | g4401.nemo.privat | NVIDIA H200 (f3216e16-4d89-30dd-ebd8-b14d1a1cff4e) | 360 | 272 | 88 | 2 | **STOP** |
| 759815 | openml_breast_w-none | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 360 | 0 | 0 | PASS |
| 759816 | openml_climate-append_only_summary | g4402.nemo.privat | NVIDIA H200 (c483223d-b4a2-1f86-6b86-5b4e9899f2dd) | 360 | 276 | 84 | 2 | **STOP** |
| 759817 | openml_climate-none | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 360 | 0 | 0 | PASS |
| 759818 | openml_credit_approval-append_only_summary | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 289 | 71 | 1 | **STOP** |
| 759819 | openml_credit_approval-none | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 332 | 28 | 0 | PASS |
| 759820 | openml_ionosphere-append_only_summary | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 309 | 51 | 0 | PASS |
| 759821 | openml_ionosphere-none | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 337 | 23 | 0 | PASS |
| 759822 | openml_sonar-append_only_summary | g4401.nemo.privat | NVIDIA H200 (f3216e16-4d89-30dd-ebd8-b14d1a1cff4e) | 360 | 313 | 47 | 0 | PASS |
| 759823 | openml_sonar-none | g4402.nemo.privat | NVIDIA H200 (c483223d-b4a2-1f86-6b86-5b4e9899f2dd) | 360 | 360 | 0 | 0 | PASS |
| 759824 | openml_wdbc-append_only_summary | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 292 | 68 | 1 | **STOP** |
| 759825 | openml_wdbc-none | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 360 | 0 | 0 | PASS |
| 759826 | tabular_mlp-append_only_summary | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 360 | 0 | 0 | PASS |
| 759827 | tabular_mlp-none | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 360 | 0 | 0 | PASS |

- totals: **5760 worker trials, 5300 successes, 460 failures (pooled rate 7.9861%), 6 runtime_error**.

## STOP chunks (worker gate: any runtime_error is a declared STOP)

- `openml_breast_w-append_only_summary`: 272/360 successes, 88 failures (`invalid_config` 86, `runtime_error` 2); exact runtime-error trials: openml_breast_w__s145 t16, openml_breast_w__s155 t19; `worker_failure_message` = `exit code 1` (worker process exited without an emitted metric); host/GPU as in the table.
- `openml_climate-append_only_summary`: 276/360 successes, 84 failures (`invalid_config` 82, `runtime_error` 2); exact runtime-error trials: openml_climate__s264 t19, openml_climate__s264 t20; `worker_failure_message` = `exit code 1` (worker process exited without an emitted metric); host/GPU as in the table.
- `openml_credit_approval-append_only_summary`: 289/360 successes, 71 failures (`invalid_config` 70, `runtime_error` 1); exact runtime-error trials: openml_credit_approval__s200 t11; `worker_failure_message` = `exit code 1` (worker process exited without an emitted metric); host/GPU as in the table.
- `openml_wdbc-append_only_summary`: 292/360 successes, 68 failures (`invalid_config` 67, `runtime_error` 1); exact runtime-error trials: openml_wdbc__s150 t20; `worker_failure_message` = `exit code 1` (worker process exited without an emitted metric); host/GPU as in the table.

The four STOP chunks are all `append_only_summary`; the matching `none` chunks and the other 8 chunks have `runtime_error = 0`. No rerun or resume was attempted: a STOP-listed cause wins (R1-SWEEP2-STOP-PRECEDENCE), and the chunk records are retained/sealed.

## Collection gate

`python3 -m sweep2.s2_c2_lib collect --run-id s2ev-20261119-a --paper-commit 4aac5209…` stops as expected: `STOP: unexpected, stopped or duplicate chunk record: …/openml_breast_w-append_only_summary/job_record.json`; no EVIDENCE collection/label table was produced. Pooled failure rate would be 7.99% (below the pooled sweep-1 + 5 pp bound), but the per-chunk runtime_error STOP is decisive.

## Sealing

All 16 chunk outputs (including the four STOP records) are sealed under `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/<chunk>/` with `SHA256SUMS`/`SEAL_RECEIPT.json`.

## Related

- R1-T1-HOST-H200 isolation check on NEMO2 H200: **FAIL** (no delegated cgroup v2 subtree, `ptrace_scope=0`, sandbox STOP at accept); per the row the whole T1 table moves to Ada. Report branch `ops-t1-h200-isolation-20261121` @ `9c93d041`.
- C3b STOP record from 20 Nov: `ops-s2c3b-launch-stop-20261120` @ `0e635c9f` (job 759810).

## Author decision needed

The launch is a declared STOP at the chunk worker gate (6 worker runtime errors in 4 append-only openml chunks; all other chunks pass). No threshold was relaxed and no chunk was rerun. Decide: (a) accept a sweep-2 EVIDENCE run with the four STOP-affected append-only chunks excluded/rerun under a new authorization, (b) investigate the append-only worker `exit code 1` failures before any rerun, or (c) another instruction. Seven-node primary analysis cannot remove these chunks automatically; they are node/memory-mode units.
