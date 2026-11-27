# G.5 expansion addendum draft for `mlgym_metamaze`

Draft for `local/20261127-29`, based on published `main` `cbc86fc5b628ed328b1889f42e7b4e0235c004f3`. R1-G5-S9 and R1-STEP-ORDER (2)(a) govern this join.
The G.1b result and seal below establish eligibility. The coordinator publishes the addendum after the main G.5
note, the applicable prerequisites, and acceptance of the filled draft. Inherit the main note's K, campaign settings,
run-budget rule, host checks, STOP rules and release order.

```text
approved: false
node: mlgym_metamaze
base_g5_note: PENDING published main G.5 note path and SHA-256
base_g5_spec: PENDING published main G.5 spec path and SHA-256
launch_code: PENDING exact shared paper.commit and reviewed addendum switch binding
g1b_note: docs/r1/authorizations/g1b_x_t1_tasl_20261126.md sha256 16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539
g1b_spec: sweep2/t1_tasl/g1b_tasl_x_spec.json sha256 d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238
g1b_determinism: PASS; docs/r1/reports/g1b_x_20261127/G1B_X_RESULT_20261127.md sha256 2328994a0dcb4c95bf61715a26124b2dfaec6eaa60de994d46c72daecdee0ebd
g1b_noise_floor: PENDING independently reviewed REL-T1-G1B and D6 copies of summary, assembly and runs
node_spec_entry: PENDING reviewed G.5 spec entry path and SHA-256
node_bindings: G.1b inputs below; PENDING G.5 harness commit, isolation check and environment binding
execution_layout: G.1b reference TASL-2 CPU-only, CPUs 0-3; PENDING G.5 placement and lease binding
label_tail: PENDING node-specific P10 law and provenance before G.5 label assembly. For Student-t bind nu and use scale = sd * sqrt((nu - 2) / nu)
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: PENDING published PRE-SPLIT amendment path and SHA-256
supply: T1 suite MLGym; arms and primary gate after the signed releases
gpu_hour_projection: PENDING G.5 estimate for this node under R1-NO-TIMEOUT (3)
review: PENDING independent acceptance of the filled addendum and its launch checks
```

## Published G.1b bindings

- The accepted result review is `docs/r1/reviews/G1B_X_RESULT_REVIEW_20261127_ROUND2.md sha256 346f079c2fdf6960d5d68fd650706920cf0a96e847d13794279f4578d2f3893a`. The node sealed attempt 1 under run
  `g1b-x-tasl-20261126-a` with 460/460 runs, zero divergence and deterministic PASS.
- Per-node seal `docs/r1/reports/g1b_x_20261127/SEAL_RECEIPT_mlgym_metamaze.json sha256 897fadbaceef595386554cf4f4aef05dac5cf83cbf1a705264f53cb8f3e5de10`.
- Published result inputs `docs/r1/reports/g1b_x_20261127/summary.json sha256 67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` and `docs/r1/reports/g1b_x_20261127/ASSEMBLY.json sha256 b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077`. The assembly binds engineering runs SHA-256 `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7`. The separately reviewed D6 copy is pending with Compute.
- Kit `docs/r1/reports/tasl_chain_20261122/MOUNTAINCAR_KIT_20261125.md` SHA-256 `0cede51b0dba90af8cc485748d577c2049d3671361f07facff70baabed635e7e`. The G.1b harness kit pin is
  `aa354485bff6b5746c48ddadcb50d92e9c6f3645` and its node spec is `third_party/mlgym/configs/trackg/nodes/mlgym_metamaze.yaml`.
- `node_spec_sha256` is `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9`.
- `committed_pin_sha256` is `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db`.
- `data_manifest_sha256` is `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`.
- Environment `venv_jax`, Python `3.12.16`, `pip` freeze SHA-256 `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`.
- The signed G.1b CPU layout used CPUs `0-3` and lease `~/r1_locks/cpus-0-3.lock`. Its engine admission
  mode was `census_override`.
- The G.1b run budget was `163.878` s, three times its `54.626` s slowest census record.

Before publication, check that the G.5 harness descends from this kit pin and preserves its measurement path. Check
CPU-only admission, the approved environment and placement, `R1-TASL2-CPU`, and the addendum runner's output
and release routing. The G.1b lease and run budget above are citations to that run. Bind the reviewed G.5 placement
and retain the signed budget rule in the filled addendum.

The switch review must show refusal for a missing or failing G.1b completion, an unpublished note, a changed pin,
an incompatible CPU placement, the wrong split or a 1GC supply request. Cite those checks in the final review field.
