### digits_mlp: 18 decision points, 6 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle -0.0002 [-0.0013, +0.0007] (biased down); naive oracle +0.0002 [+0.0000, +0.0003] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: -0.0006; share of points where verify changed the leaf value: 0.61
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0083 | [+0.0064, +0.0101] | – | [–, –] | 0.00 |
| `always_verify` | +0.0077 | [+0.0054, +0.0097] | -0.0006 | [-0.0013, +0.0000] | 1.00 |
| `margin_threshold` | +0.0083 | [+0.0064, +0.0101] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `harness_heuristic` | +0.0083 | [+0.0064, +0.0101] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0083 | [+0.0064, +0.0101] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `ridge_advantage` | +0.0085 | [+0.0065, +0.0104] | +0.0002 | [+0.0000, +0.0003] | 0.28 |
| `awr_mlp` | +0.0082 | [+0.0064, +0.0099] | -0.0001 | [-0.0005, +0.0002] | 0.28 |
| `random_matched` | +0.0083 | [+0.0064, +0.0101] | -0.0000 | [-0.0000, +0.0000] | 0.22 |
| `oracle_naive` | +0.0085 | [+0.0065, +0.0104] | +0.0002 | [+0.0000, +0.0003] | – |
| `oracle_leafsplit` | +0.0081 | [+0.0059, +0.0100] | -0.0002 | [-0.0013, +0.0007] | – |

### openml_ionosphere: 18 decision points, 6 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle -0.0046 [-0.0107, +0.0010] (biased down); naive oracle +0.0004 [+0.0000, +0.0009] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: -0.0014; share of points where verify changed the leaf value: 0.61
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0189 | [+0.0090, +0.0283] | – | [–, –] | 0.00 |
| `always_verify` | +0.0175 | [+0.0075, +0.0274] | -0.0014 | [-0.0042, +0.0005] | 1.00 |
| `margin_threshold` | +0.0186 | [+0.0087, +0.0278] | -0.0004 | [-0.0008, +0.0000] | 0.11 |
| `harness_heuristic` | +0.0189 | [+0.0090, +0.0283] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0188 | [+0.0090, +0.0280] | -0.0002 | [-0.0005, +0.0000] | 0.06 |
| `ridge_advantage` | +0.0187 | [+0.0088, +0.0279] | -0.0002 | [-0.0009, +0.0003] | 0.22 |
| `awr_mlp` | +0.0177 | [+0.0078, +0.0272] | -0.0012 | [-0.0041, +0.0003] | 0.56 |
| `random_matched` | +0.0189 | [+0.0087, +0.0283] | -0.0000 | [-0.0008, +0.0006] | 0.44 |
| `oracle_naive` | +0.0194 | [+0.0091, +0.0289] | +0.0004 | [+0.0000, +0.0009] | – |
| `oracle_leafsplit` | +0.0143 | [+0.0027, +0.0274] | -0.0046 | [-0.0107, +0.0010] | – |

### ALL: 36 decision points, 12 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle -0.0024 [-0.0058, +0.0005] (biased down); naive oracle +0.0003 [+0.0001, +0.0006] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: -0.0010; share of points where verify changed the leaf value: 0.61
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0136 | [+0.0080, +0.0198] | – | [–, –] | 0.00 |
| `always_verify` | +0.0126 | [+0.0073, +0.0184] | -0.0010 | [-0.0025, +0.0000] | 1.00 |
| `margin_threshold` | +0.0136 | [+0.0080, +0.0198] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `harness_heuristic` | +0.0136 | [+0.0080, +0.0198] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0136 | [+0.0080, +0.0198] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `ridge_advantage` | +0.0129 | [+0.0077, +0.0185] | -0.0007 | [-0.0021, +0.0000] | 0.14 |
| `awr_mlp` | +0.0135 | [+0.0079, +0.0196] | -0.0001 | [-0.0004, +0.0001] | 0.31 |
| `random_matched` | +0.0136 | [+0.0080, +0.0197] | -0.0000 | [-0.0002, +0.0001] | 0.25 |
| `oracle_naive` | +0.0139 | [+0.0082, +0.0203] | +0.0003 | [+0.0001, +0.0006] | – |
| `oracle_leafsplit` | +0.0112 | [+0.0049, +0.0185] | -0.0024 | [-0.0058, +0.0005] | – |

