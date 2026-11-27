# G.5 expansion addendum draft for `gc7rc_etth1`

Draft for `local/20261127-29`, based on published `main` `cbc86fc5b628ed328b1889f42e7b4e0235c004f3`. R1-G5-S9 and R1-STEP-ORDER (2)(a) govern this join.
The G.1b result and seal below establish eligibility. The coordinator publishes the addendum after the main G.5
note, the applicable prerequisites, and acceptance of the filled draft. Inherit the main note's K, campaign settings,
run-budget rule, host checks, STOP rules and release order.

```text
approved: false
node: gc7rc_etth1
base_g5_note: PENDING published main G.5 note path and SHA-256
base_g5_spec: PENDING published main G.5 spec path and SHA-256
launch_code: PENDING exact shared paper.commit and reviewed addendum switch binding
g1b_note: docs/r1/authorizations/g1b_x_t1_tasl_20261126.md sha256 16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539
g1b_spec: sweep2/t1_tasl/g1b_tasl_x_spec.json sha256 d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238
g1b_determinism: PASS; docs/r1/reports/g1b_x_20261127/G1B_X_RESULT_20261127.md sha256 2328994a0dcb4c95bf61715a26124b2dfaec6eaa60de994d46c72daecdee0ebd
g1b_seal: docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_gc7rc_etth1.json sha256 96dad194c74b5dafb790ea3451cb7c6dd7763efd2c5e28737fe9306dd2bd02d7
g1b_noise_floor: docs/r1/reports/g1b_x_20261127/summary.json sha256 67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10; docs/r1/reports/g1b_x_20261127/ASSEMBLY.json sha256 b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077; PENDING reviewed D6 runs copy, sealed runs SHA-256 c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7
node_spec_entry: PENDING reviewed G.5 spec entry path and SHA-256
node_bindings: G.1b inputs below; PENDING G.5 harness commit, isolation check and environment binding
execution_layout: G.1b reference TASL-2 CPU-only, CPUs 16-31; PENDING G.5 placement and lease binding
label_tail: PENDING node-specific P10 declaration before G.5 label assembly
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: PENDING published PRE-SPLIT amendment path and SHA-256
supply: separate descriptive per-node G.5 output; excluded from SFT, arms and primary gate
gpu_hour_projection: PENDING G.5 estimate for this node under R1-NO-TIMEOUT (3)
review: PENDING independent acceptance of the filled addendum and its launch checks
```

## Published G.1b bindings

- The accepted result review is `docs/r1/reviews/G1B_X_RESULT_REVIEW_20261127_ROUND2.md sha256 346f079c2fdf6960d5d68fd650706920cf0a96e847d13794279f4578d2f3893a`. The node sealed attempt 1 under run
  `g1b-x-tasl-20261126-a` with 460/460 runs, zero divergence and deterministic PASS.
- Kit `docs/r1/reports/tasl_chain_20261122/ETTH1_KIT_20261125.md` SHA-256 `e1b94a76a2caf84cde6f0143cd094fdcbb31549e8f154d3441dc92da94079417`. The G.1b harness kit pin is
  `3a06d86721b0c1826b165b68a9781a561e4993f4` and its node spec is `configs/trackg/nodes/gc7rc_etth1.yaml`.
- `node_spec_sha256` is `8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c`.
- `committed_pin_sha256` is `818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27`.
- `data_manifest_sha256` is `eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b`.
- Environment `torch312`, Python `3.12.16`, `uv` freeze SHA-256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`.
- The signed G.1b CPU layout used CPUs `16-31` and lease `~/r1_locks/cpus-16-31.lock`. Its engine admission
  mode was `census_override`.
- The G.1b run budget was `34.518` s, three times its `11.506` s slowest census record.

Before publication, check that the G.5 harness descends from this kit pin and preserves its measurement path. Check
CPU-only admission, the approved environment and placement, `R1-TASL2-CPU`, and the addendum runner's output
and release routing. The G.1b lease and run budget above are citations to that run. Bind the reviewed G.5 placement
and retain the signed budget rule in the filled addendum.
