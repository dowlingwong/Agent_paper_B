### Table 1 — re-measured nodes: E1 vs. the 30-seed re-measurement

| Node | data | σ_train | σ_split [95 % CI] | σ_joint | median sd(Δ̂) | δ_n (D18) | material / resolved / all | mean P(wrong), material | regret share | campaign-seed wrong | sd_train/sd_joint | D21 (E1 rule) | split policy (E1 rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | E1 (10 seeds, 12 Oct) | 0.0000 | 0.0080 [0.0055, 0.0146] | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.09 | 0.09 | 0/3 | 0.15 | more seeds needed | `vary` |
| `openml_credit_approval` | new, seeds 1–10 (= E1 seeds) | 0.0000 | 0.0080 [0.0055, 0.0146] | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.07 | 0.07 | 0/3 | 0.24 | more seeds needed | `vary` |
| `openml_credit_approval` | new, seeds 11–30 (independent) | 0.0000 | 0.0195 [0.0148, 0.0285] | 0.0323 | 0.0034 | 0.0020 | 2 / 2 / 5 | 0.21 | 0.23 | 1/2 | 0.16 | qualifies | `vary` |
| `openml_credit_approval` | new, all 30 seeds | 0.0000 | 0.0176 [0.0140, 0.0237] | 0.0279 | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.24 | 0.23 | 1/3 | 0.23 | qualifies | `vary` |
| `openml_diabetes` | E1 (10 seeds, 12 Oct) | 0.0000 | 0.0336 [0.0231, 0.0613] | 0.0317 | 0.0024 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |
| `openml_diabetes` | new, seeds 1–10 (= E1 seeds) | 0.0000 | 0.0336 [0.0231, 0.0613] | 0.0317 | 0.0024 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |
| `openml_diabetes` | new, seeds 11–30 (independent) | 0.0000 | 0.0378 [0.0287, 0.0551] | 0.0365 | 0.0032 | 0.0020 | 1 / 1 / 5 | 0.31 | 0.31 | 1/1 | 0.06 | more seeds needed | `vary` |
| `openml_diabetes` | new, all 30 seeds | 0.0000 | 0.0359 [0.0286, 0.0482] | 0.0357 | 0.0028 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |

σ values: sd of the baseline c0 metric over the seeds of one condition; CI is the Gaussian chi-square interval. P(wrong) selection cap Φ(−2/√n): n=10 → 0.26, n=20 → 0.33, n=30 → 0.36.

### Table 2 — per-edit, E1 (10 seeds) vs. new (30 seeds)

| Node | Edit | Δ̂_J ± 2se, E1 | Δ̂_J ± 2se, 30 | sd(Δ̂) joint, E1 → 30 | sd split, E1 → 30 | sd train, E1 → 30 | P(wrong), E1 → 30 | material, E1 → 30 | regret |Δ̂|·P, 30 |
|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0012 ± 0.0019 | -0.0020 ± 0.0010 | 0.0031 → 0.0027 | 0.0019 → 0.0025 | 0.0000 → 0.0000 | 0.35 → 0.24 | no → no | 0.0005 |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0003 ± 0.0013 | 0.0006 ± 0.0011 | 0.0020 → 0.0030 | 0.0015 → 0.0023 | 0.0000 → 0.0000 | 0.43 → 0.43 | no → no | 0.0002 |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0189 ± 0.0084 | 0.0123 ± 0.0047 | 0.0133 → 0.0129 | 0.0125 → 0.0144 | 0.0016 → 0.0037 | 0.08 → 0.17 | yes → yes | 0.0021 |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0183 ± 0.0093 | 0.0082 ± 0.0059 | 0.0147 → 0.0162 | 0.0202 → 0.0205 | 0.0028 → 0.0028 | 0.11 → 0.31 | yes → yes | 0.0025 |
| `openml_credit_approval` | class_weight balanced -> null | 0.0006 ± 0.0006 | 0.0002 ± 0.0003 | 0.0009 → 0.0008 | 0.0007 → 0.0008 | 0.0000 → 0.0000 | 0.25 → 0.42 | no → no | 0.0001 |
| `openml_diabetes` | C 0.15 -> 0.075 | 0.0009 ± 0.0015 | 0.0005 ± 0.0008 | 0.0024 → 0.0022 | 0.0012 → 0.0018 | 0.0000 → 0.0000 | 0.36 → 0.42 | no → no | 0.0002 |
| `openml_diabetes` | C 0.15 -> 0.3 | -0.0004 ± 0.0010 | -0.0000 ± 0.0006 | 0.0015 → 0.0016 | 0.0010 → 0.0013 | 0.0000 → 0.0000 | 0.40 → 0.49 | no → no | 0.0000 |
| `openml_diabetes` | model_type logistic_regression -> random_forest | 0.0127 ± 0.0168 | 0.0029 ± 0.0088 | 0.0265 → 0.0241 | 0.0196 → 0.0225 | 0.0053 → 0.0048 | 0.32 → 0.45 | no → no | 0.0013 |
| `openml_diabetes` | model_type logistic_regression -> gradient_boosting | -0.0013 ± 0.0155 | -0.0088 ± 0.0092 | 0.0245 → 0.0253 | 0.0206 → 0.0276 | 0.0009 → 0.0012 | 0.48 → 0.36 | no → no | 0.0032 |
| `openml_diabetes` | class_weight balanced -> null | 0.0011 ± 0.0012 | 0.0010 ± 0.0010 | 0.0019 → 0.0028 | 0.0015 → 0.0018 | 0.0000 → 0.0000 | 0.29 → 0.36 | no → no | 0.0004 |

### Table 3 — bootstrap stability of the proposed D21 verdict (joint seeds resampled, paired across configs)

| Node | data | seeds | P(qualifies) | P(#material = 0/1/2/3+) | mean P(wrong) over material, 5 / 50 / 95 % |
|---|---|---|---|---|---|
| `openml_credit_approval` | E1 (10 seeds) | 10 | 0.39 | 0.00 / 0.01 / 0.80 / 0.18 | 0.01 / 0.09 / 0.17 |
| `openml_diabetes` | E1 (10 seeds) | 10 | 0.09 | 0.56 / 0.33 / 0.10 / 0.00 | 0.06 / 0.19 / 0.26 |
| `openml_credit_approval` | new (30 seeds) | 30 | 0.87 | 0.00 / 0.13 / 0.49 / 0.38 | 0.15 / 0.21 / 0.27 |
| `openml_diabetes` | new (30 seeds) | 30 | 0.03 | 0.43 / 0.55 / 0.03 / 0.00 | 0.22 / 0.31 / 0.35 |

### Table 4 — side by side with the five D21 nodes (E1, 10 seeds) and δ_n per D18

| Node | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / all | mean P(wrong), material | regret share | sd_train/sd_joint | D21 (E1 rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 | 0.16 | 0.15 | 0.65 | qualifies |
| `tabular_mlp` | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 5 | 0.10 | 0.08 | 0.56 | qualifies |
| `openml_breast_w` | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 5 | 0.16 | 0.17 | 0.39 | qualifies |
| `openml_ionosphere` | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 5 | 0.16 | 0.14 | 0.06 | qualifies |
| `openml_wdbc` | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 5 | 0.16 | 0.10 | 0.11 | qualifies |
| `openml_credit_approval` | 30 | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 0.0020 | 2 / 5 | 0.24 | 0.23 | 0.23 | qualifies |
| `openml_diabetes` | 30 | 0.0000 | 0.0359 | 0.0357 | 0.0028 | 0.0020 | 0 / 5 | – | – | 0.00 | more seeds needed |

δ_n uses D18 as written: median over all of a node's edits of the joint paired sd(Δ̂) (the E1 'median sd(Δ̂)' column).

### Table 5 — bit-reproducibility of E1's runs (same node, config, condition and seeds)

| Node:config | identical | different |
|---|---|---|
| `openml_credit_approval:c0` | 32 | 0 |
| `openml_credit_approval:c1` | 32 | 0 |
| `openml_credit_approval:c2` | 32 | 0 |
| `openml_credit_approval:c3` | 2 | 30 |
| `openml_credit_approval:c4` | 4 | 28 |
| `openml_credit_approval:c5` | 32 | 0 |
| `openml_diabetes:c0` | 32 | 0 |
| `openml_diabetes:c1` | 32 | 0 |
| `openml_diabetes:c2` | 32 | 0 |
| `openml_diabetes:c3` | 0 | 32 |
| `openml_diabetes:c4` | 5 | 27 |
| `openml_diabetes:c5` | 32 | 0 |

