# Sweep 2 (C3 T0) — report, 21 November 2026

**EVIDENCE run. Labels remain sealed under R1-BX-D8-CONFIRM; this report reads no labels and makes no analysis claim.**

## Launch and authority

- authorization: `docs/r1/authorizations/c3_sweep2_20261119.md`, sha256 `349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a` (published main).
- launch commit: `4aac52092813b2b01ddb96cd7d135c390aeff645` (published main; note + R1-S2C3B-WDBC row + exception code).
- C3b at the launch commit (job 759811, H200): 7/8 with exactly the declared R1-S2C3B-WDBC `openml_wdbc` `invalid_rate` shortfall (observed 0.30, required `< 0.3`); sealed `/ceph/srv/dwong/paperb/sweep2/s2c3b-20261121-a/liveness-prompt/`.
- S2-C5 enabled with both keys for `s2ev-20261119-a` only; 16/16 H200 chunks submitted at the launch commit; no change to `main` in the launch window.

## Chunks

| cluster | chunk | host | GPU (UUID) | trials | successes | failures | runtime_errors | gate |
|---|---|---|---|---|---|---|---|---|
| 759812 | digits_mlp-append_only_summary | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 360 | 0 | 0 | PASS |
| 759813 | digits_mlp-none | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 360 | 0 | 0 | PASS |
| 759814 | openml_breast_w-append_only_summary | g4401.nemo.privat | NVIDIA H200 (f3216e16-4d89-30dd-ebd8-b14d1a1cff4e) | 360 | 272 | 88 | 2 | **STOP→admitted** |
| 759815 | openml_breast_w-none | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 360 | 0 | 0 | PASS |
| 759816 | openml_climate-append_only_summary | g4402.nemo.privat | NVIDIA H200 (c483223d-b4a2-1f86-6b86-5b4e9899f2dd) | 360 | 276 | 84 | 2 | **STOP→admitted** |
| 759817 | openml_climate-none | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 360 | 0 | 0 | PASS |
| 759818 | openml_credit_approval-append_only_summary | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 289 | 71 | 1 | **STOP→admitted** |
| 759819 | openml_credit_approval-none | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 332 | 28 | 0 | PASS |
| 759820 | openml_ionosphere-append_only_summary | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 309 | 51 | 0 | PASS |
| 759821 | openml_ionosphere-none | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 337 | 23 | 0 | PASS |
| 759822 | openml_sonar-append_only_summary | g4401.nemo.privat | NVIDIA H200 (f3216e16-4d89-30dd-ebd8-b14d1a1cff4e) | 360 | 313 | 47 | 0 | PASS |
| 759823 | openml_sonar-none | g4402.nemo.privat | NVIDIA H200 (c483223d-b4a2-1f86-6b86-5b4e9899f2dd) | 360 | 360 | 0 | 0 | PASS |
| 759824 | openml_wdbc-append_only_summary | g4402.nemo.privat | NVIDIA H200 (ae60c045-b347-98d0-7477-87ab4b8959bb) | 360 | 292 | 68 | 1 | **STOP→admitted** |
| 759825 | openml_wdbc-none | g4401.nemo.privat | NVIDIA H200 (fc65a53b-1e31-b243-eda4-02226cf11519) | 360 | 360 | 0 | 0 | PASS |
| 759826 | tabular_mlp-append_only_summary | g4402.nemo.privat | NVIDIA H200 (a853e181-a8f1-aa6f-88d9-ba45c981e34d) | 360 | 360 | 0 | 0 | PASS |
| 759827 | tabular_mlp-none | g4401.nemo.privat | NVIDIA H200 (424f4b2c-334c-15e6-02d7-39786b8aba21) | 360 | 360 | 0 | 0 | PASS |

- 16 chunks / 8 nodes / 288 campaigns; **5760 worker trials, 5300 successes, 460 failures**, 6 raw `runtime_error` (all six diagnosed and admitted); GPU model used: **NVIDIA H200** only.

## Runtime-error diagnosis and collection admission (R1-SWEEP2-RTE-DIAG)

The four `append_only_summary` openml chunks stopped at the chunk worker gate on six `runtime_error` trials: breast_w s145 t16, s155 t19; climate s264 t19, t20; credit_approval s200 t11; wdbc s150 t20. Each was replayed twice on CPU from the sealed worker input (node copy, exact config edit, seed, harness `a3fedbb`, v1 image) with identical exit 1:

- 5× `yaml.parser.ParserError` from a malformed `class_weight: {0` / `{1` (the proposed custom mapping was truncated to its first token; YAML flow-mapping parse fails before training);
- 1× `TypeError: float(None)` at `benchmark.py:164` from `max_depth: null`.

No OOM/signal/I-O/environment failure; classification (i) for all six. Evidence and independent review: `ops-sweep2-rte-diag-20261121` @ `cab74ccd` (`S2_SWEEP2_RTE_DIAG_REVIEW_20261121.md`, ACCEPTED).

Collection change: `s2-rte-admit-20261121` @ `093fb6d1` admits exactly these six records (bound by chunk `job_record` sha256, campaign/trial id and sealed exception, all admission artifacts hash-checked against the sealed SHA256SUMS); they count as `invalid_config` failures, any other `runtime_error` remains a STOP. Independent review `S2_RTE_ADMIT_REVIEW_20261121.md` round 2 ACCEPTED.

## Collection

`collect_evidence` on the 16 sealed chunks: **PASS** — `collection_counts.json` in the sealed run directory, sha256 `3e29382b4d31cef54b92d0cf77a0819b5dedda92aedd528b708f5030b88b6ec7`; 16/16 chunks, 8 live nodes, 288 campaigns, 5,760 trials, 460 failures (7.986% vs limit 13.212% = pooled sweep-1 + 5 pp), 5,796 LLM calls, 0 parse failures, 6 admitted diagnosed records. The six remain counted as failures; no threshold was changed.

## Analysis scope (R1-S2C3B-WDBC)

- The **primary sweep-2 analysis uses the seven nodes that passed C3b**; `openml_wdbc` is a pre-declared **sensitivity row (with / without)**, disclosed here and in the appendix. All 16 chunks (all eight nodes) ran and were collected; collection still required all 16 node/memory pairs and `min_live_nodes = 8`.
- Labels stay sealed; analysis is gated by the signed R1-BX-D8-CONFIRM and is not part of this report.

## Related host check

- R1-T1-HOST-H200 harness-isolation check on NEMO2 H200: **FAIL** (no delegated cgroup v2 subtree, `ptrace_scope=0`, non-waivable sandbox stop at accept; GPU smoke not exercisable). Per the row, the whole T1 table moves to Ada. Report branch `ops-t1-h200-isolation-20261121` @ `9c93d041`.

## Evidence

- sealed chunks: `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/<chunk>/` (16/16 `SHA256SUMS`/`SEAL_RECEIPT.json`).
- launched/stop report: `ops-sweep2-launch-20261121` @ `c9b5e570`.
- diagnosis: `ops-sweep2-rte-diag-20261121` @ `cab74ccd`.
- admission unit: `s2-rte-admit-20261121` @ `093fb6d1`.
- T1 isolation: `ops-t1-h200-isolation-20261121` @ `9c93d041`.

## Disclosures

- six diagnosed proposal-induced runtime-error records admitted by reviewed collection unit; no other gate relaxed.
- all chunks ran on NVIDIA H200; CPU model and GPU UUIDs recorded per chunk in `chunks_summary.json`/job records.
- C3b 7/8 declared exception; primary analysis seven nodes, wdbc sensitivity row.
- labels not read; no B.2 audits under the sweep-2 note.
