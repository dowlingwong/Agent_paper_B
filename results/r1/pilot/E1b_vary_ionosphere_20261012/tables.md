### openml_ionosphere: 18 decision points, 6 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle -0.0047 [-0.0106, +0.0007] (biased down); naive oracle +0.0010 [+0.0001, +0.0025] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: -0.0007; share of points where verify changed the leaf value: 0.67
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0189 | [+0.0090, +0.0283] | – | [–, –] | 0.00 |
| `always_verify` | +0.0182 | [+0.0087, +0.0275] | -0.0007 | [-0.0042, +0.0021] | 1.00 |
| `margin_threshold` | +0.0174 | [+0.0072, +0.0273] | -0.0015 | [-0.0043, +0.0002] | 0.78 |
| `harness_heuristic` | +0.0176 | [+0.0077, +0.0269] | -0.0014 | [-0.0041, +0.0000] | 0.17 |
| `kg_index` | +0.0174 | [+0.0072, +0.0273] | -0.0015 | [-0.0043, +0.0002] | 0.78 |
| `ridge_advantage` | +0.0190 | [+0.0089, +0.0285] | +0.0001 | [-0.0003, +0.0005] | 0.44 |
| `awr_mlp` | +0.0178 | [+0.0077, +0.0275] | -0.0011 | [-0.0038, +0.0004] | 0.56 |
| `random_matched` | +0.0192 | [+0.0094, +0.0279] | +0.0002 | [-0.0011, +0.0021] | 0.72 |
| `oracle_naive` | +0.0200 | [+0.0101, +0.0286] | +0.0010 | [+0.0001, +0.0025] | – |
| `oracle_leafsplit` | +0.0142 | [+0.0026, +0.0269] | -0.0047 | [-0.0106, +0.0007] | – |

### ALL: 18 decision points, 6 instances

- best simple baseline: `rho`. Headroom bracket (true oracle headroom lies between, in expectation): leaf-split oracle -0.0047 [-0.0106, +0.0007] (biased down); naive oracle +0.0010 [+0.0001, +0.0025] (biased up; its upper bound is conservative)
- mean leaf difference verify − continue: -0.0007; share of points where verify changed the leaf value: 0.67
- mean worker runs per branch: continue 12.0, verify 12.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0189 | [+0.0090, +0.0283] | – | [–, –] | 0.00 |
| `always_verify` | +0.0182 | [+0.0087, +0.0275] | -0.0007 | [-0.0042, +0.0021] | 1.00 |
| `margin_threshold` | +0.0174 | [+0.0072, +0.0273] | -0.0015 | [-0.0043, +0.0002] | 0.78 |
| `harness_heuristic` | +0.0176 | [+0.0077, +0.0269] | -0.0014 | [-0.0041, +0.0000] | 0.17 |
| `kg_index` | +0.0174 | [+0.0072, +0.0273] | -0.0015 | [-0.0043, +0.0002] | 0.78 |
| `ridge_advantage` | +0.0190 | [+0.0089, +0.0285] | +0.0001 | [-0.0003, +0.0005] | 0.44 |
| `awr_mlp` | +0.0178 | [+0.0077, +0.0275] | -0.0011 | [-0.0038, +0.0004] | 0.56 |
| `random_matched` | +0.0192 | [+0.0094, +0.0279] | +0.0002 | [-0.0011, +0.0021] | 0.72 |
| `oracle_naive` | +0.0200 | [+0.0101, +0.0286] | +0.0010 | [+0.0001, +0.0025] | – |
| `oracle_leafsplit` | +0.0142 | [+0.0026, +0.0269] | -0.0047 | [-0.0106, +0.0007] | – |

