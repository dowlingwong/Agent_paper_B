# ENGINEERING_ONLY — end-to-end plumbing check (L13). Not evidence; numbers are not results.

```
{
  "label": "ENGINEERING_ONLY",
  "banner": "ENGINEERING_ONLY \u2014 end-to-end plumbing check (L13). Not evidence; numbers are not results.",
  "utc": "20261012T163133Z",
  "harness": {
    "root": "/sessions/rcw-01bdc7uov9ttaxvnrnts7as1/mnt/autoresearch_harness",
    "commit": "c686517f2f7832f3c70cb9b0131f593cc9a4a615",
    "branch": "r1",
    "dirty": false
  },
  "table": {
    "points": 2,
    "instances": 2
  },
  "deployment": {
    "default": {
      "trials": 8,
      "kept": 2,
      "verifies": 0
    },
    "kg_index": {
      "trials": 8,
      "kept": 2,
      "verifies": 0
    }
  }
}
```

### digits_mlp: 2 decision points, 2 instances

- best simple baseline: `rho`; headroom (cross-fitted oracle − best simple): +0.0007 [-0.0007, +0.0021]; naive oracle headroom +0.0000
- mean leaf difference verify − continue: -0.0014; share of points where verify changed the leaf value: 1.00
- mean worker runs per branch: continue 5.0, verify 5.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0028 | [+0.0021, +0.0035] | – | [–, –] | 0.00 |
| `always_verify` | +0.0014 | [+0.0000, +0.0028] | -0.0014 | [-0.0021, -0.0007] | 1.00 |
| `margin_threshold` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `harness_heuristic` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `ridge_advantage` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `awr_mlp` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `random_matched` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `oracle_naive` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_crossfit` | +0.0035 | [+0.0028, +0.0042] | +0.0007 | [-0.0007, +0.0021] | – |

### ALL: 2 decision points, 2 instances

- best simple baseline: `rho`; headroom (cross-fitted oracle − best simple): +0.0007 [-0.0007, +0.0021]; naive oracle headroom +0.0000
- mean leaf difference verify − continue: -0.0014; share of points where verify changed the leaf value: 1.00
- mean worker runs per branch: continue 5.0, verify 5.0 (same compute budget; verify's runs replace later trials)

| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |
|---|---|---|---|---|---|
| `rho` | +0.0028 | [+0.0021, +0.0035] | – | [–, –] | 0.00 |
| `always_verify` | +0.0014 | [+0.0000, +0.0028] | -0.0014 | [-0.0021, -0.0007] | 1.00 |
| `margin_threshold` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `harness_heuristic` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `kg_index` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `ridge_advantage` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `awr_mlp` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | 0.00 |
| `random_matched` | +0.0024 | [+0.0021, +0.0028] | -0.0003 | [-0.0007, +0.0000] | 0.50 |
| `oracle_naive` | +0.0028 | [+0.0021, +0.0035] | +0.0000 | [+0.0000, +0.0000] | – |
| `oracle_crossfit` | +0.0035 | [+0.0028, +0.0042] | +0.0007 | [-0.0007, +0.0021] | – |

