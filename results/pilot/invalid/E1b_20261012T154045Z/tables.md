### digits_mlp: 18 decision points, 6 instances

- best simple baseline: `rho`; headroom (cross-fitted oracle − best simple): -0.0001 [-0.0007, +0.0004]; naive oracle headroom +0.0000
- mean leaf difference verify − continue: -0.0003; share of points where verify changed the leaf value: 0.11
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0085 | [+0.0070, +0.0100] | – | [–, –] | 0.00 |
| `always_verify` | +0.0083 | [+0.0067, +0.0097] | -0.0003 | [-0.0007, +0.0000] | 1.00 |
| `margin_threshold` | +0.0085 | [+0.0069, +0.0100] | -0.0001 | [-0.0002, +0.0000] | 0.61 |
| `harness_heuristic` | +0.0085 | [+0.0070, +0.0100] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0085 | [+0.0070, +0.0100] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `ridge_advantage` | +0.0085 | [+0.0069, +0.0100] | -0.0001 | [-0.0002, +0.0000] | 0.89 |
| `awr_mlp` | +0.0083 | [+0.0067, +0.0097] | -0.0003 | [-0.0007, +0.0000] | 1.00 |
| `random_matched` | +0.0085 | [+0.0070, +0.0100] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `oracle_naive` | +0.0085 | [+0.0070, +0.0100] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_crossfit` | +0.0084 | [+0.0065, +0.0101] | -0.0001 | [-0.0007, +0.0004] | – |

### openml_ionosphere: 18 decision points, 6 instances

- best simple baseline: `rho`; headroom (cross-fitted oracle − best simple): -0.0036 [-0.0101, +0.0012]; naive oracle headroom +0.0000
- mean leaf difference verify − continue: +0.0000; share of points where verify changed the leaf value: 0.00
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0139 | [+0.0030, +0.0245] | – | [–, –] | 0.00 |
| `always_verify` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `margin_threshold` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `harness_heuristic` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `kg_index` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `ridge_advantage` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `awr_mlp` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `random_matched` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `oracle_naive` | +0.0139 | [+0.0030, +0.0245] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_crossfit` | +0.0103 | [-0.0016, +0.0233] | -0.0036 | [-0.0101, +0.0012] | – |

### ALL: 36 decision points, 12 instances

- best simple baseline: `rho`; headroom (cross-fitted oracle − best simple): -0.0019 [-0.0053, +0.0005]; naive oracle headroom +0.0000
- mean leaf difference verify − continue: -0.0001; share of points where verify changed the leaf value: 0.06
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0112 | [+0.0057, +0.0170] | – | [–, –] | 0.00 |
| `always_verify` | +0.0111 | [+0.0055, +0.0169] | -0.0001 | [-0.0003, +0.0000] | 1.00 |
| `margin_threshold` | +0.0112 | [+0.0057, +0.0170] | -0.0000 | [-0.0001, +0.0000] | 0.78 |
| `harness_heuristic` | +0.0112 | [+0.0057, +0.0170] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0112 | [+0.0057, +0.0170] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `ridge_advantage` | +0.0112 | [+0.0057, +0.0170] | -0.0000 | [-0.0001, +0.0000] | 0.94 |
| `awr_mlp` | +0.0111 | [+0.0055, +0.0169] | -0.0001 | [-0.0003, +0.0000] | 0.92 |
| `random_matched` | +0.0112 | [+0.0057, +0.0170] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `oracle_naive` | +0.0112 | [+0.0057, +0.0170] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_crossfit` | +0.0093 | [+0.0037, +0.0159] | -0.0019 | [-0.0053, +0.0005] | – |

