# S2-C3 L40S deployment check — replay results (ENGINEERING_ONLY)

**Verdict: NOT PASS** (criteria 1-6 from the PRE-DECLARED `docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md`, sha256
`63bd0a9b3c52501d93b91549f27199a9b88d7d67a0fd5498df68a0c341f4bcdc`).  ENGINEERING_ONLY: this check is not evidence, produces no label table, starts no B.2
audit, and does not enter training or selection.  No criteria were relaxed after data; the declared tolerances are
applied exactly.

## Per-instance final_y (replay vs B2 EVIDENCE)

| instance | B2 final_y | replay final_y | abs(delta) | criterion 1 |
|---|---|---|---|---|
| digits_mlp__s9011 | 0.9727019 | 0.9727019 | 0.0000000 | PASS |
| digits_mlp__s9012 | 0.9710306 | 0.9710306 | 0.0000000 | PASS |
| digits_mlp__s9013 | 0.9740947 | 0.9740947 | 0.0000000 | PASS |
| digits_mlp__s9014 | 0.9727019 | 0.9727019 | 0.0000000 | PASS |
| openml_credit_approval__s9011 | 0.9365820 | 0.9161570 | 0.0204250 | FAIL |
| openml_credit_approval__s9012 | 0.9216943 | 0.9328142 | 0.0111199 | PASS |
| openml_credit_approval__s9013 | 0.9337075 | 0.9173533 | 0.0163542 | PASS |
| openml_credit_approval__s9014 | 0.9120051 | 0.9192616 | 0.0072565 | PASS |
| openml_ionosphere__s9011 | 0.9041795 | 0.9724456 | 0.0682661 | FAIL |
| openml_ionosphere__s9012 | 0.9749224 | 0.9749224 | 0.0000000 | PASS |
| openml_ionosphere__s9013 | 0.9018575 | 0.9021671 | 0.0003096 | PASS |
| openml_ionosphere__s9014 | 0.9078947 | 0.9068111 | 0.0010836 | PASS |

- mean |delta| = **0.0104012** (bound 0.01); max
  |delta| = **0.0682661** on `openml_ionosphere__s9011` (bound
  0.02); not bitwise identity — this is a stack check.

## Criteria 1-6

| criterion | verdict | values |
|---|---|---|
| 1 final_y | NOT PASS | mean |delta| 0.0104012 (<= 0.01), max 0.0682661 (<= 0.02) |
| 2 parse failures | PASS | 0/240 = 0.0 (<= 0.02) |
| 3 diagnostics | NOT PASS | invalid/duplicates/noops vs pre-data-corrected 20/33/20: invalid 25/20, duplicates 38/33, noops 25/20 |
| 4 full offload | PASS | digits_mlp 61/61; openml_credit_approval 61/61; openml_ionosphere 61/61 |
| 5 throughput | PASS | 1637.0 s total (<= 3635.4 s = 2x B2) |
| 6 no STOP | PASS | all roots rc 0 with complete manifests |

## Pins verified by the comparison

- expected-values source: `docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md` sha256 `63bd0a9b3c52501d93b91549f27199a9b88d7d67a0fd5498df68a0c341f4bcdc`
- pinned replay inputs SHA256SUMS sha256 `6224b75a4d4aec9ac2f289cf913e19cbb814263a9e7d0e7b381122695d0cadf6` (12 B2 off roots; 24 files)
- every job record: paper `8709dce792d45bbb5c05d9f7d239e19454efbb15`, harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, image
  `sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`, model `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`, B2 binding `c502a9aa5e23cb190e712505b8900253fb417cdb1c143b525b3b4b1b8b45290b`,
  label patch sha256 `fd0234c9579b293cdb7db259303e1ef86dffdd6a7e8ed3360f04227badddf741`
- every campaign manifest: `execution_label = ENGINEERING_ONLY`, `replay_marker = s2_c3_replay/v1`, final
  audit seeds 9201-9210; no reserved B.2 seed 7001-7010 anywhere; no label leak.
- three job records, one per node (`digits_mlp, openml_credit_approval, openml_ionosphere`), 12 distinct instances, no duplicates.

## Outputs read

- `/tmp/s2c3_out/digits_mlp` (node digits_mlp, wall 541.0 s)
- `/tmp/s2c3_out/openml_credit_approval` (node openml_credit_approval, wall 546.0 s)
- `/tmp/s2c3_out/openml_ionosphere` (node openml_ionosphere, wall 550.0 s)

Attempted comparison at unspecified.  Independent review is required before any EVIDENCE claim;
this report is an ENGINEERING_ONLY artifact.
