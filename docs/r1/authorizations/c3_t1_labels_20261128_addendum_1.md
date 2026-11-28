# G.5 expansion addendum for `mlgym_titanic`

Draft under R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a), R1-G5-S9 and R1-G5-TAILS-EXPANSION.
The coordinator publishes the approved note after the per-node binding and independent tier-E review.
This node enters the T1 MLGym suite for the arms and primary gate after the signed releases.

```text
approved: false
run_id: c3_t1_labels_20261128_addendum_1
node: mlgym_titanic
paper_commit: 9b044b59f58109b3d1e4eb1822623160958b1d95
spec_sha256: 2b68a4f40212acbc30a84867486e07ae6485efd4134a4cb778392f2e9f50ad5b
base_g5_note: docs/r1/authorizations/c3_t1_labels_20261128.md sha256 4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59
base_g5_spec: sweep2/t1_tasl/g5_tasl_spec.json sha256 7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md sha256 970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7
supply: g5_addendum_mlgym
review: docs/r1/reviews/G5_EXPANSION_ADDENDA_TITANIC_METAMAZE_LAUNCH_REVIEW_20261128.md sha256 de343ac4e6d10d29b2f7a8c3d1493e1a2f5bb3916008a35ca1d398bc9ba3a9cb
```

## Eligibility and deployment

- Expansion G.1b ended with determinism PASS for this node. The published seal is `docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_titanic.json sha256 13773f1541b2d84cb5545fb80601babf6e087ae9b535cc50849870c03de00207`.
  The spec binds the signed G.1b note, exact expansion spec and reviewed D6 copy. The copy and its
  review are `docs/r1/reports/g5_rel_t1_g1b_20261128/x/COPY_RECORD.json sha256 84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841` and `docs/r1/reviews/G5_EXPANSION_RELCOPY_SOURCE_REVIEW_20261128.md sha256 4b7ef4e818579b38e96aa1af84c4b9fe30f4700ca3be96cca1b9ae5bed9eb234`.
- TASL-2 performs both waves on CPUs `12-15` under `torch312` at `/home/dowling/r1_tracks/t1_tasl_x/harness_titanic_g5`.
  The G.5 harness is `d2ce4701faf03f00efaf9c475879acf213411d3b`, an exact descendant of the census kit `3a67042ba7e4211feb9681524f3879643c8cf635`.
  The run takes the main worker-slot lease, the two S13 CPU-set leases and `~/r1_locks/cpus-12-15.lock`
  when it differs from the S13 leases. The census interpreter is `/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python`.
- The host isolation record with items 1–7 PASS at the exact G.5 pin is `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_titanic_20261128.md sha256 3d76372dc02ccfe01dfccb15f4c9180fbf59c2d33fa035d5a66faee9d3ece1f2`.
  Its accepted review is `docs/r1/reviews/G5_EXPANSION_ISOLATION_TITANIC_REVIEW_20261128.md sha256 7251f40d618024488870e09759ffd92f82fd7fc0b4fdea5281745bd490ff5849`. The harness comparison is `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md sha256 4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- The label law is Gaussian, as declared by R1-G5-TAILS-EXPANSION before label assembly.
  The proposal run budget is three times the 155.965 s slowest census
  record, or 467.895 s. Both waves use the published main settings,
  history mode, 12 instances, W = 20 manager calls, K = 10, signed seed blocks and STOP rules.
- TASL-7 serves the proposer under this addendum's own ID and spec digest. Before submitting,
  check the current run ledger and both hosts' leases. Keep each job's attempt and seal under this run ID.

## Resource projection

Use the existing G.5 pre-pilot planning formula with the TASL-2 CPU census time of 138.183 s,
no GPU/census time ratio, 60 s per manager call, 0.60 run share, no duplicate discount and 1.25 inflation.
The estimate is 89.14 worker-slot hours including audit and startup,
and 12.20 separately metered TASL-7 proposer card hours for the campaign waves and startup.
The worker and audits execute on CPU while the worker-slot lease is held. Use the signed 425 worker-card
GPU-hour reporting threshold and report actual occupancy and hours per job under R1-NO-TIMEOUT (3).
The projection supplies planning information and sets no pass criterion.
