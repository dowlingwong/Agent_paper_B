# local/20261128-07 — D.3a P5 evidence accounting

for: coordinator

for: compute

- Base `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907`, coordinator queue `a064fd47b96d070ec3e0dba5f2add37e133c8f13`. Delivery `local-20261128-07-d3-evidence-accounting` @ `bb3f2e8e388322dbe4ceaa786a13889255c51baa`. Code-Commit `befe3fef62dfcf61d7f3594ae51b22f0eb694762`.
- The deployment chunk writes each retained campaign's proposer GPU seconds and whole-chunk attempt count to the existing G7 summary. Both harness and FIXR3/EGATE routes seal timing provenance in `campaign.json` and the source receipts in `retry_ledger.json`.
- Independent tier-E R2 **ACCEPTED**. R1 found wrong-card fallback and unverified retry identity. R2 reproduced the fixes and ran 97 focused tests plus a synthetic scope lock-retention check. [Review](https://github.com/dowlingwong/Agent_paper_B/blob/bb3f2e8e388322dbe4ceaa786a13889255c51baa/docs/r1/reviews/D3_EVIDENCE_ACCOUNTING_REVIEW_20261128.md)
- **Full suite** 4,751 → 4,770 passed. All 143 failure and 27 error IDs match, with 168 skips on each checkout. Serial fresh `TMPDIR`s, Python 3.11.5, pytest 7.4.0, LightGBM off the path and clean harness `9bb416805175149eb87b71f28d77530572aa4bce`. Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`. [Exact failure and error IDs](20261128-02-p11-full-suite-ids.txt)
- Next for the coordinator is publication of the accepted unit. Compute's existing `compute/20261128-11` supplies the live route verification and P7/P8 records. The D.3a authorization still needs the actual layout and environment fields, launch-commit rechecks and the author's signature.

## Accounting and Compute handoff

The metric measures one GPU reservation over the retained campaign execution interval. It uses a monotonic clock inside the lease or Condor allocation. This includes time while the proposer card remains reserved during CPU work, and excludes time between campaigns, placement wait, and lost chunks. The per-campaign receipt stores the elapsed nanoseconds and GPU UUID. The G7 field is elapsed nanoseconds divided by 1,000,000,000. Counts in the campaign budget and the signed schema use their existing definitions. A reissued LLM call is handled inside its existing budget rule and adds no separate chunk attempt.

Before any dispatch, reconcile the proposed run ID, chunk and attempt ID with the operator retry ledger, the HTCondor queue/history or SSH scope, and the reserved card. Each prior started chunk classified as an infrastructure loss under §3.1 retains its original output and operator/scheduler record. Check each sealed job record's digest and job ID against its loss receipt. Placement denials and unsuccessful submissions without a started chunk do not enter this count.

Use one ordered launch `retry_ledger` for the verified history of that run and chunk. Its keys are `schema: r1_d3_retry_ledger/v1`, `run_id`, `chunk`, and `attempts`. The `chunk` object carries `stage`, `node`, `arm`, `repetition`, `instance_seeds`, `manifest_sha256` and the bound `gpu_model`. Each earlier entry contains `attempt_id`, `job_id`, `state: infrastructure_lost`, `receipt_path` and `receipt_sha256`. The original UTF-8 loss receipt has schema `r1_d3_infrastructure_loss/v1`, the same `run_id`, `chunk`, `attempt_id`, `job_id` and `state`, plus the original `job_record_sha256`. Compute writes that receipt from the preserved job record. The launchers verify the receipt bytes and identity and embed them for the job to recheck. The final entry contains only the fresh `attempt_id` and `state: current`. A first attempt has only that final entry.

Use a live probe with `observed.probe: true`. SSH binds `hardware.proposer_gpu_uuid` to the selected `gpu<index>.lock` or `GPU-<uuid>.lock`, and the wrapper retains the lock while the chunk runs under its scope. The HTCondor probe resolves the one assigned CUDA device to its UUID. Keep dry-run staging separate from the real attempt. Use a fresh SSH staging and remote attempt directory, or a fresh Condor submit directory. Collect the Condor result from `<submit_dir>/out`, the job's transferred directory. [HTCondor GPU assignment variables](https://htcondor.readthedocs.io/en/25.0/users-manual/env-of-job.html) · [CUDA device identity API](https://docs.nvidia.com/cuda/cuda-driver-api/cuda_driver_api/group__CUDA__DEVICE.html)

The P5 meter uses the verified reservation. Before evidence, Compute must document and independently review that the exact pinned manifest endpoint serves the pinned proposer on that reserved UUID. Record the live server-to-device check in the P7 selected-route receipt and verify it for each launch. On HTCondor this includes the execute-side server wrapper using the job's assigned card. The desk tests used synthetic scheduler, GPU and campaign inputs. Live route verification and actual operator receipt creation remain with Compute.

## P5 Code-Commit and review set

Published deliveries and intervening runtime corrections were reconciled against the base. The branch references below identify the reviewed code and its associated review record.

| P5 unit | Reviewed Code-Commit and delivery lineage | Accepted review |
|---|---|---|
| G1 snapshots and chunk | `44075323d56efc76573590aea4ec7b28567b3490` | `381262de` [G1 R3](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G1_SNAPSHOT_CORE_REVIEW_R3_20261127.md) |
| G1/A0 adapter | `2da347e2f2662770daf67521a9821b2bde557aef`, delivery `ac01717e` | `9cd66d19` [Adapter R2](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G1_ADAPTER_REVIEW_R2_20261127.md) |
| G1 terminal snapshot | `292cde9787750436a5ee769ed78982aa3b3cedbc`, delivery `ff244366` | `d5acf3ab` [Terminal snapshot and recheck](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G1_FINAL_SNAPSHOT_REVIEW_20261127.md) |
| G1 launchers and probe | `3cfaa6fe88e315b5be6a0f234a8a5d2c261ecb92`, delta `f4cbda4b718b54a8216aeeec799fc1c6b9194b25`, delivery `ead7375a` | `acc43a3a` [Launcher R4](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G1_LAUNCHERS_REVIEW_R4_20261127.md) |
| G11/A0R | `65285c2dee480a3106328a51c969f4be4347f2e5`, delivery `f81739c8`, shared corrections `c56e94f4` | `27564dbb` [Controller review](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md) |
| G2 fitter and fit | `e95cb1d4fdd5d67e0bd3cdbe6170e9d56e546345`, fit artifact delivery `79b0a0ce` | `6cf882b0` [Fitter](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G2_CONSTANTS_REVIEW_20261127.md) and `f8f0c2ac` [Fit](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G2_CONSTANTS_FIT_REVIEW_20261127.md) |
| G3/FIXR3 and G4/EGATE | `bac81fc7e03a7ea56d433bd1bfeb333a3679fc43` and `56c6cf6194c84916f3511b173e3518747c690a55`, deliveries `2d4e9cf2`/`871d4712` with `c56e94f4`. Shared G1 adapter for these arms `02ad2370627c06404079bc9749105bb86227568b`, delivery `478c3348` | `27564dbb` [Controllers](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md) and `2ba6435e` [Replicate route R2](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G1_REPLICATE_UNIT_REVIEW_20261127_R2.md) |
| G5/LADDER | `4be7e70637164cc0e8bf4e7d9a256a6f85a0d56d`, delivery `222de37a`, corrections `c56e94f4` | `27564dbb` [Controller review](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md) |
| G6 audit | `b4b15ddb37ab8022f067c78f1cc15ff07c00c174`, delivery `0716ed8d`, smoke refusal restored by `345f4c97dc9b6f2db2336ba9ceea53726f12cbde` | `8899aa4e` [G6 R2](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_G6_AUDIT_REVIEW_R2_20261127.md) and `6eadf655` [Smoke refusal](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/G6_SMOKE_AUDIT_REVERT_REVIEW_20261127.md) |
| G7 outcome table and G1/G6/G7 integration | `12dc1ab62a1965e42fc8215b8b3601e583df98ea`, delivery `e33abaef`, corrections `c56e94f4`. Integration `d8cfd7d0a715ba52a93d6cbf8578666b7e05399b`, delivery `39df5b92`. Step (8) header binding published in `474c998d` | `27564dbb` [G7](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md), `dc76484d` [Integration R2](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_INTEGRATION_REVIEW_R2_20261127.md), `ad6e5f18` [Step (8)](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_STEP8_BINDING_REVIEW_20261128.md) |
| G8 replicate and call accounting | `b556396616f3811d5ac68e5df26feffb91ad8576`, delivery `e775b38c`, corrections `c56e94f4` | `27564dbb` [Controller review](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reviews/D3_CONTROLLERS_REVIEW_20261127.md) |
| P5 reservation and retry producer | `befe3fef62dfcf61d7f3594ae51b22f0eb694762` | `bb3f2e8e` [Tier-E R2](https://github.com/dowlingwong/Agent_paper_B/blob/bb3f2e8e388322dbe4ceaa786a13889255c51baa/docs/r1/reviews/D3_EVIDENCE_ACCOUNTING_REVIEW_20261128.md) |

| Binding | SHA-256 |
|---|---|
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Pinned analysis | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| Pinned analysis tests | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| G2 constants | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| P5 producer | `df60e4e4e722c3b9917b8005576f87bb423b2246039a5937a5141d1b94ac87b4` |
| Independent review | `f9c4a9cd33bf1bae50a092572c6a15e7cb1e739da724290ca29818631552eaa7` |
| Full-suite failure and error IDs | `3771032d2b7bcd14852da852ebcff69eff8e1af38aa25474eaf9ff61347ae1fb` |

Decided alone to measure monotonic reserved-card time over each campaign and to use sealed, byte-verified retry receipts. The assigned linked Git metadata refused the fetch, so this task used the existing writable nested Git worktrees within the assignment. The 16 pre-existing project paths match published G.5 work at `1afa7d62` or `dbce0316`. Local submitted zero host jobs and opened no sealed partition.

## Queue after delivery

Fetched after the task push. Published main `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907`, coordinator `a064fd47b96d070ec3e0dba5f2add37e133c8f13`, incoming Local `1946faeea858100f4025d7e30eb92769abf0742d`, Compute `b72b1aa8871dcdaab3894586e132181b59f9728f`, Writer `d507bb0f3c482f149e28d9c98a95dd49bce1baec`.

| Lane | Last recorded status and next check |
|---|---|
| Local | No remaining runnable card. The G.5 final render `local/20261126-08` waits for accepted P11 host coverage and final `paper.commit`. Expansion addenda wait on the base note plus reviewed launch, harness and host bindings. The rows (g) repeat-list and monitor await `R1-G5-SHARED-REPEAT`. The further audit-host unit remains parked on placement and binding. |
| Compute · G.5 P11 | `compute/20261128-10` owns the fresh matrix on TASL-2 and TASL-7. Earlier stamp `g5-p11-20261128T014000Z` is a retained STOP. No fresh rerun job ID or stamp is in the fetched reports. Check the compute ledger and both leases before any retry. |
| Compute · D.3 | Screening `SMEAS_EVIDENCE_20261128T001405Z` and step (8) are complete. `compute/20261128-11` follows the P11 matrix record, then the layout, per-arm smoke and deepthought check. At 04:40:33 UTC, TOpAS A100 `c03-001-175` still had `Start=false` and deepthought2's ETP L40S had no pool ad. Check actual eligibility and current IDs before submitting. Removed IDs are `760148`, `760149`, `760152`, `759624` and `759625`. `760065` was withdrawn. |
| Houseprice | `local/20261126-01` and `local/20261127-27` are complete. The exact rerun procedure is in the existing Compute handoff. Published S14 run `tasl2-cpuset-mlgym_houseprice-20261128` has three bit-identical seals for CPUs 0–7. [Accepted handoff](20261127-27-houseprice-two-attempts.md#compute-handoff) |
| P.4 and Paper C | Ada E0 repeat `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) and TASL-7 repeat `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) are complete. The author owns the E0 criterion decision before P.4 phase 1/A5. Paper C CPU work awaits operator pins and authorization. E-INT `compute/20261127-28` awaits its bound spec, staged data/tokenizer, eligible Ada lease and engineering smoke. |
| Writer and offline gate | Writer is idle pending a released-results card. The offline gate awaits G.5, the downstream bindings, arms freeze and explicit release. |

Compute's 02:55–02:56 UTC direct-host read reported idle Paper B hosts. The later 04:40:33 UTC batch read had no `dwong` queue entry and its prior R2 job `760158.0` was no longer listed. This was a batch re-check only. No new Paper B job ID was reported. [Direct-host status](https://github.com/dowlingwong/Agent_paper_B/blob/3b9a1b81/reports/20261128-15-round-status.md) · [Batch re-check](https://github.com/dowlingwong/Agent_paper_B/blob/b72b1aa8/reports/20261128-16-d3-preflight-recheck3.md)
