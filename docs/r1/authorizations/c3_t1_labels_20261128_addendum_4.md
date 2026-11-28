# G.5 expansion addendum for `gc7rc_forestcover`

Draft under R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a), R1-G5-S9 and R1-G5-TAILS-EXPANSION.
The coordinator publishes the approved note after the per-node binding and independent tier-E review.
Under R1-G5-S9 (2), Forest Cover supplies a separate descriptive node output. SFT, arms training and
the primary gate exclude this output.

```text
approved: false
run_id: c3_t1_labels_20261128_addendum_4
node: gc7rc_forestcover
paper_commit: f532176f3f0241909c9fb8df63a58e6fbefaefbd
spec_sha256: 2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78
base_g5_note: docs/r1/authorizations/c3_t1_labels_20261128.md sha256 4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59
base_g5_spec: sweep2/t1_tasl/g5_tasl_spec.json sha256 7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md sha256 970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7
supply: g5_addendum_extra_task
review: PENDING
```

## Eligibility and deployment

- Expansion G.1b completed 460 of 460 runs with determinism PASS. The published seal is
  `docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_gc7rc_forestcover.json sha256 2940254a01b7136d76eb2ed310536a7bf92cf5b03b373cffa8408ca285433506`.
  The spec binds the signed expansion G.1b note and spec, and the reviewed D6 copy.
  Copy record `docs/r1/reports/g5_rel_t1_g1b_20261128/x/COPY_RECORD.json sha256 84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841`.
  Independent review `docs/r1/reviews/G5_EXPANSION_RELCOPY_SOURCE_REVIEW_20261128.md sha256 4b7ef4e818579b38e96aa1af84c4b9fe30f4700ca3be96cca1b9ae5bed9eb234`.
- Run both G.5 waves and their audits CPU-only on TASL-2 CPUs 4–7 under `torch312`, using
  `/home/dowling/r1_tracks/t1_tasl_x/harness_forestcover_g5` at `3f7b09febf401a83f3aa881f00eecdd032024416`.
  This exact pin descends from census kit `85851664679d10889c5af406843c4a3fc38f7a49`.
  CPUs 4–7 are the determinism-checked replacement under R1-TASL2-CPU.
  Hold the main worker-slot lease `~/r1_locks/gpu0.lock` and both S13 leases
  `~/r1_locks/cpus-0-3.lock` and `~/r1_locks/cpus-4-7.lock`. The latter is also the census deployment's lease.
  Use the census interpreter `/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python`.
- The exact-pin isolation record reports C1–7 PASS. Record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261128.md sha256 00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12`.
  Its independent review accepted the host check with documentation minors.
  `docs/r1/reviews/G5_EXPANSION_ISOLATION_FORESTCOVER_REVIEW_20261128.md sha256 42702d3a8414bc6827a886474fff5182a6e4808a785f20bb3baf82d2210545cf`.
  The accepted harness comparison is `docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md sha256 4c7217762ebd5f5143433de05e004c84ae7db994bff4c333919c9e313e4304b3`.
- Use the Gaussian P10 law signed in R1-G5-TAILS-EXPANSION. The proposal budget is three times the
  255.723 s slowest census record, or 767.169 s.
  Both waves inherit the signed main settings, history mode, 12 instances, W = 20 manager calls,
  K = 10, seed blocks and STOP rules.
- TASL-7 serves the proposer under the addendum's own run ID and spec digest. Check the current run
  ledger and both hosts' leases before any submission. Keep all attempts and seals under this run ID.

## Reporting and release

Forest Cover uses a port-implemented baseline and evaluator. Its noise floor was measured on TASL-2 CPU.
The selection metric uses validation and the held-out test partition stays sealed under the signed release
rules. Data attribution is Covertype dataset, UCI Machine Learning Repository (Blackard, J. and Dean, D.,
1998), DOI 10.24432/C50K5N, CC BY 4.0. The pinned download and derived arrays stay outside the repository
and bundles. The appendix and funnel retain the kit review's disclosures.
Kit review `docs/r1/reviews/FORESTCOVER_KIT_REVIEW_20261125.md sha256 8a4412bc307986077af5c8907ec06235fa1dec6901eaf56b29f5976d05e4bed5`.

## Resource projection

Use the existing G.5 pre-pilot planning formula with the 93.406 s TASL-2 CPU census baseline,
60 s per manager call, 0.60 run share, no duplicate discount and 1.25 inflation. The projections are
62.08 worker-slot hours including audits and startup and 9.81 separately metered
TASL-7 proposer card hours including startup. The worker and audits execute on CPU while the
worker-slot lease is held. Report actual occupancy and hours under R1-NO-TIMEOUT (3) and the signed
425 worker-card GPU-hour reporting threshold. The projection supplies planning information.
