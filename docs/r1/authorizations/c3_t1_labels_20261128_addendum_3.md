# G.5 expansion addendum for `gc7rc_etth1`

Draft under R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a), R1-G5-S9 and R1-G5-TAILS-EXPANSION.
The coordinator publishes the approved note after the per-node binding and independent tier-E review.
ETTh1 supplies a separate descriptive node output under R1-G5-S9 (2). It is excluded from SFT,
arms training and the primary gate.

```text
approved: true
run_id: c3_t1_labels_20261128_addendum_3
node: gc7rc_etth1
paper_commit: 2a58f7ac5147dad1259914593901ccb226a147f9
spec_sha256: 6c3323cae31c1f4e9433412143538dc3045323364f7b29b8d77c003464592758
base_g5_note: docs/r1/authorizations/c3_t1_labels_20261128.md sha256 4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59
base_g5_spec: sweep2/t1_tasl/g5_tasl_spec.json sha256 7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md sha256 970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7
supply: g5_addendum_extra_task
review: docs/r1/reviews/G5_EXPANSION_ADDENDUM_ETTH1_LAUNCH_REVIEW_20261128.md sha256 6951a029a5ccb33dd12533edc7cbe0f1e25056ed15e8284b74f2d1d4aa31f4ad
```

## Eligibility and deployment

- Expansion G.1b ended with determinism PASS for ETTh1. Its seal is `docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_gc7rc_etth1.json sha256 96dad194c74b5dafb790ea3451cb7c6dd7763efd2c5e28737fe9306dd2bd02d7`.
  The spec binds the signed G.1b note, exact expansion spec and reviewed D6 copy. The copy record
  is `docs/r1/reports/g5_rel_t1_g1b_20261128/x/COPY_RECORD.json sha256 84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841`, with independent review `docs/r1/reviews/G5_EXPANSION_RELCOPY_SOURCE_REVIEW_20261128.md sha256 4b7ef4e818579b38e96aa1af84c4b9fe30f4700ca3be96cca1b9ae5bed9eb234`.
- TASL-2 runs both waves and their audits on CPUs 16–31 under `torch312`, at `/home/dowling/r1_tracks/t1_tasl_x/harness_etth1_g5`.
  The G.5 harness `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c` descends from census kit `3a06d86721b0c1826b165b68a9781a561e4993f4`.
  Acquire the main worker-slot lease, both S13 leases and `~/r1_locks/cpus-16-31.lock`.
  The census interpreter is `/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python`.
- The exact-pin TASL-2 host isolation record has items 1–7 PASS.
  Record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261128.md sha256 6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7`.
  Its independent review `docs/r1/reviews/G5_EXPANSION_ISOLATION_ETTH1_REVIEW_20261128.md sha256 68f7d4ba1dc51f585a322583398d90b65724a142c675d646648c3571f16d3a6d` accepted with documentation minors.
  The accepted harness comparison is `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md sha256 4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- The label law is Gaussian under R1-G5-TAILS-EXPANSION. The proposal budget is
  three times the 11.506 s slowest census record, or
  34.518 s. Both waves use the published main settings,
  history mode, 12 instances, W = 20 manager calls, K = 10, signed seed blocks and STOP rules.
- TASL-7 serves the proposer under the addendum's own run ID and spec digest. Check the live ledger
  and both hosts' leases before submitting. Keep each attempt and seal under this run ID.

## Reporting and release

ETTh1 uses a port-implemented baseline and evaluator. Its noise floor was measured on TASL-2 CPU.
The published G.1b note's ETTh1 data-use disclosure and kit review c6(iii) require an author or legal
licence line before any label table cites ETTh1. Kit review `docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md sha256 73df58d5f929d6922223c3b33a926232e5e5189a774cc6a3b7364e5768869202`.
The signed G.5 release rules apply to the descriptive node output.

## Resource projection

Use the existing G.5 pre-pilot planning formula with the 10.908 s TASL-2 census time,
60 s per manager call, 0.60 run share, no duplicate discount and 1.25 inflation.
The estimates are 11.74 worker-slot hours including audit and startup
and 5.42 separately metered TASL-7 proposer card hours including startup.
The worker and audits execute on CPU while the worker-slot lease is held. Use the signed 425
worker-card GPU-hour reporting threshold and report actual occupancy and hours per job under
R1-NO-TIMEOUT (3). The projection supplies planning information and sets no pass criterion.
