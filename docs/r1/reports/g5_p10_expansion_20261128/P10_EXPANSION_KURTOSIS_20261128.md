# G.5 P10 basis for the four expansion nodes

Task local/20261128-03, published base `7716cfced1a30105f38590114c2b2d200b6b417d`.
Use this table for the author's node-level tail declarations with the four expansion addenda.

| Node | Addendum scope | Paired c1 − c0 G2 | Paired c2 − c0 G2 | Paired c3 − c0 G2 | Paired c4 − c0 G2 | n per edit | SE per edit |
|---|---|---:|---:|---:|---:|---:|---:|
| gc7rc_etth1 | Scoped 1GC descriptive output | −0.21 | +3.63 | +0.49 | −0.65 | 30 | 0.833 |
| gc7rc_forestcover | Scoped 1GC descriptive output | +0.73 | −0.23 | −0.08 | −0.83 | 30 | 0.833 |
| mlgym_metamaze | MLGym main table and primary gate | −0.18 | +6.51 | +3.54 | −1.08 | 30 | 0.833 |
| mlgym_titanic | MLGym main table and primary gate | −0.78 | −0.58 | +0.78 | +1.42 | 30 | 0.833 |

The archived [g5r_kurt.py](g5r_kurt.py) is byte-for-byte the independent reviewer's original
seven-node script used in `coord/local` report `20261127-08-g5-render-stop.md`.
Its SHA-256 is `1fdc798927c5e714c39111b9f33fafb0de1828038b45e2e95c3ddd54244f313a`.
The script uses each successful finite joint-seed outcome. Within each node and edit, it
pairs by the run ID suffix shared with c0, subtracts c0, then applies the bias-corrected
Fisher excess kurtosis G2. SE is the same normal-reference finite-sample SE. It is a
reference scale for the table, not a separate tail decision.

The expansion copy contains 1,840 engineering census rows, including 600 joint rows
with train and split seed equal. All 30 joint seeds (3001–3030) are present exactly once per
node/configuration and finite. Each paired sample therefore has 30 observations. In the
seven-node basis one non-finite mlab_cifar10 c4 row leaves 29 pairs for that edit.
MetaMaze is the only expansion node with paired G2 above 3 on at least two edits, the
descriptive comparison named in the original seven-node report. ETTh1 has one such edit.
The author's declarations remain pending. The scope comes from the published expansion
binding and the four addendum drafts.

From the repository root:

```sh
python3 docs/r1/reports/g5_p10_expansion_20261128/g5r_kurt.py \
  docs/r1/reports/g5_rel_t1_g1b_20261128/x/runs.jsonl
python3 docs/r1/reports/g5_p10_expansion_20261128/g5r_kurt.py \
  docs/r1/reports/g5_rel_t1_g1b_20261126/seven/runs.jsonl
```

| Published expansion input | SHA-256 |
|---|---|
| runs.jsonl | `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7` |
| summary.json | `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` |
| ASSEMBLY.json | `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077` |
| COPY_RECORD.json | `84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841` |

The source is run `g1b-x-tasl-20261126-a`, from the reviewed expansion D6 copy under
`docs/r1/reports/g5_rel_t1_g1b_20261128/x/`. Its PRE-SPLIT v2 amendment SHA-256 is
`970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.
The work read only the two published engineering census copies and their metadata.
