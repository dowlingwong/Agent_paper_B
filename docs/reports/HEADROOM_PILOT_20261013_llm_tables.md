### digits_mlp: 18 decision points, 6 instances

- best simple baseline: `always_verify`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle +0.0001 [-0.0000, +0.0003] (biased down); naive oracle +0.0001 [+0.0000, +0.0004] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: +0.0009; share of points where verify changed the leaf value: 0.33
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0109 | [+0.0083, +0.0133] | – | [–, –] | 0.00 |
| `always_verify` | +0.0119 | [+0.0096, +0.0136] | +0.0009 | [-0.0003, +0.0027] | 1.00 |
| `margin_threshold` | +0.0110 | [+0.0085, +0.0134] | +0.0001 | [-0.0003, +0.0005] | 0.78 |
| `harness_heuristic` | +0.0119 | [+0.0096, +0.0136] | +0.0009 | [-0.0003, +0.0027] | 1.00 |
| `kg_index` | +0.0117 | [+0.0095, +0.0135] | +0.0007 | [-0.0003, +0.0026] | 0.67 |
| `ridge_advantage` | +0.0113 | [+0.0091, +0.0135] | +0.0004 | [+0.0000, +0.0012] | 0.28 |
| `awr_mlp` | +0.0118 | [+0.0096, +0.0136] | +0.0009 | [-0.0000, +0.0026] | 0.44 |
| `random_matched` | +0.0113 | [+0.0091, +0.0134] | +0.0004 | [-0.0002, +0.0014] | 0.72 |
| `oracle_naive` | +0.0120 | [+0.0097, +0.0138] | +0.0011 | [+0.0000, +0.0028] | – |
| `oracle_leafsplit` | +0.0120 | [+0.0097, +0.0138] | +0.0010 | [-0.0001, +0.0028] | – |

### openml_ionosphere: 18 decision points, 6 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle +0.0000 [+0.0000, +0.0000] (biased down); naive oracle +0.0000 [+0.0000, +0.0000] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: +0.0000; share of points where verify changed the leaf value: 0.00
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0000 | [+0.0000, +0.0000] | – | [–, –] | 0.00 |
| `always_verify` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 1.00 |
| `margin_threshold` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `harness_heuristic` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `ridge_advantage` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `awr_mlp` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `random_matched` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `oracle_naive` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_leafsplit` | +0.0000 | [+0.0000, +0.0000] | +0.0000 | [+0.0000, +0.0000] | – |

### ALL: 36 decision points, 12 instances

- best simple baseline: `always_verify`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle +0.0001 [-0.0000, +0.0002] (biased down); naive oracle +0.0001 [+0.0000, +0.0002] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: +0.0005; share of points where verify changed the leaf value: 0.17
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0055 | [+0.0022, +0.0088] | – | [–, –] | 0.00 |
| `always_verify` | +0.0059 | [+0.0026, +0.0094] | +0.0005 | [-0.0001, +0.0014] | 1.00 |
| `margin_threshold` | +0.0055 | [+0.0022, +0.0089] | +0.0000 | [-0.0002, +0.0003] | 0.89 |
| `harness_heuristic` | +0.0059 | [+0.0026, +0.0094] | +0.0005 | [-0.0001, +0.0014] | 1.00 |
| `kg_index` | +0.0058 | [+0.0025, +0.0092] | +0.0004 | [-0.0002, +0.0013] | 0.83 |
| `ridge_advantage` | +0.0058 | [+0.0025, +0.0092] | +0.0004 | [-0.0002, +0.0013] | 0.42 |
| `awr_mlp` | +0.0059 | [+0.0025, +0.0093] | +0.0004 | [-0.0000, +0.0013] | 0.56 |
| `random_matched` | +0.0056 | [+0.0024, +0.0090] | +0.0002 | [-0.0002, +0.0007] | 0.81 |
| `oracle_naive` | +0.0060 | [+0.0026, +0.0095] | +0.0005 | [+0.0000, +0.0014] | – |
| `oracle_leafsplit` | +0.0060 | [+0.0026, +0.0095] | +0.0005 | [-0.0000, +0.0014] | – |
