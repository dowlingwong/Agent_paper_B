# G.5 expansion addendum for `mlgym_metamaze`

Draft under R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a), R1-G5-S9 and R1-G5-TAILS-EXPANSION.
The coordinator publishes the approved note after the per-node binding and independent tier-E review.
This node enters the T1 MLGym suite for the arms and primary gate after the signed releases.

```text
approved: true
run_id: c3_t1_labels_20261128_addendum_2
node: mlgym_metamaze
paper_commit: 9b044b59f58109b3d1e4eb1822623160958b1d95
spec_sha256: 4112e44995dedf1136d1c926c57c9d9bd052a07be339cd0d93a134e070d0f85d
base_g5_note: docs/r1/authorizations/c3_t1_labels_20261128.md sha256 4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59
base_g5_spec: sweep2/t1_tasl/g5_tasl_spec.json sha256 7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md sha256 970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7
supply: g5_addendum_mlgym
review: docs/r1/reviews/G5_EXPANSION_ADDENDA_TITANIC_METAMAZE_LAUNCH_REVIEW_20261128.md sha256 de343ac4e6d10d29b2f7a8c3d1493e1a2f5bb3916008a35ca1d398bc9ba3a9cb
```

## Eligibility and deployment

- Expansion G.1b ended with determinism PASS for this node. The published seal is `docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_mlgym_metamaze.json sha256 897fadbaceef595386554cf4f4aef05dac5cf83cbf1a705264f53cb8f3e5de10`.
  The spec binds the signed G.1b note, exact expansion spec and reviewed D6 copy. The copy and its
  review are `docs/r1/reports/g5_rel_t1_g1b_20261128/x/COPY_RECORD.json sha256 84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841` and `docs/r1/reviews/G5_EXPANSION_RELCOPY_SOURCE_REVIEW_20261128.md sha256 4b7ef4e818579b38e96aa1af84c4b9fe30f4700ca3be96cca1b9ae5bed9eb234`.
- TASL-2 performs both waves on CPUs `0-3` under `venv_jax` at `/home/dowling/r1_tracks/t1_tasl_x/harness_metamaze_g5`.
  The G.5 harness is `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685`, an exact descendant of the census kit `aa354485bff6b5746c48ddadcb50d92e9c6f3645`.
  The run takes the main worker-slot lease, the two S13 CPU-set leases and `~/r1_locks/cpus-0-3.lock`
  when it differs from the S13 leases. The census interpreter is `/home/dowling/r1_trackg_20261125/venv_jax/bin/python`.
- The host isolation record with items 1–7 PASS at the exact G.5 pin is `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261128.md sha256 80581d24da323dd9a9ef212585bfe3908165b72f583bd6f40e09b9bf6f1231c0`.
  Its accepted review is `docs/r1/reviews/G5_EXPANSION_ISOLATION_METAMAZE_REVIEW_20261128.md sha256 b999b26d5dd7d695c126073f81980714849a7f9eb0e37714f1b6478d31140cfd`. The harness comparison is `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md sha256 4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- The label law is Student-t with ν = 5, with scale s × √((ν−2)/ν) for declared standard deviation s, as declared by R1-G5-TAILS-EXPANSION before label assembly.
  The proposal run budget is three times the 54.626 s slowest census
  record, or 163.878 s. Both waves use the published main settings,
  history mode, 12 instances, W = 20 manager calls, K = 10, signed seed blocks and STOP rules.
- TASL-7 serves the proposer under this addendum's own ID and spec digest. Before submitting,
  check the current run ledger and both hosts' leases. Keep each job's attempt and seal under this run ID.

## Resource projection

Use the existing G.5 pre-pilot planning formula with the TASL-2 CPU census time of 53.721 s,
no GPU/census time ratio, 60 s per manager call, 0.60 run share, no duplicate discount and 1.25 inflation.
The estimate is 37.63 worker-slot hours including audit and startup,
and 7.70 separately metered TASL-7 proposer card hours for the campaign waves and startup.
The worker and audits execute on CPU while the worker-slot lease is held. Use the signed 425 worker-card
GPU-hour reporting threshold and report actual occupancy and hours per job under R1-NO-TIMEOUT (3).
The projection supplies planning information and sets no pass criterion.
