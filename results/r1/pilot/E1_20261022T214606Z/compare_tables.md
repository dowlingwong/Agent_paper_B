### Table 1 — C1 noise-floor table: ten nodes, 30 seeds per condition, adopted D21 rule

| Node | seeds train/split/joint | default m | σ_train [95 % CI] | σ_split [95 % CI] | σ_joint [95 % CI] | median sd(Δ̂) | δ_n (D18) | material / resolved / all | mean P(wrong), material | regret share | campaign-seed wrong | split policy (E1 rule) | **D21 verdict (adopted rule)** | bootstrap P(qualifies) (not decisive) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 30/30/30 | 0.9554 | 0.0068 [0.0054, 0.0092] | 0.0073 [0.0058, 0.0099] | 0.0102 [0.0081, 0.0137] | 0.0066 | 0.0020 | 5 / 5 / 5 | 0.101 | 0.10 | 0/5 | `fixed` | **qualifies** | 0.48 |
| `tabular_mlp` | 30/30/30 | 0.9141 | 0.0029 [0.0023, 0.0039] | 0.0123 [0.0098, 0.0165] | 0.0121 [0.0096, 0.0163] | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.125 | 0.09 | 0/3 | `fixed` | **qualifies** | 0.75 |
| `openml_breast_w` | 30/30/30 | 0.9932 | 0.0000 [0.0000, 0.0000] | 0.0050 [0.0040, 0.0067] | 0.0038 [0.0031, 0.0051] | 0.0007 | 0.0020 | 2 / 2 / 5 | 0.233 | 0.23 | 0/2 | `vary` | **qualifies** | 0.97 |
| `openml_ionosphere` | 30/30/30 | 0.9845 | 0.0000 [0.0000, 0.0000] | 0.0485 [0.0386, 0.0651] | 0.0410 [0.0327, 0.0551] | 0.0160 | 0.0040 | 2 / 2 / 5 | 0.195 | 0.17 | 1/2 | `vary` | **qualifies** | 0.92 |
| `openml_wdbc` | 30/30/30 | 0.9976 | 0.0000 [0.0000, 0.0000] | 0.0061 [0.0048, 0.0082] | 0.0079 [0.0063, 0.0106] | 0.0007 | 0.0020 | 2 / 4 / 5 | 0.174 | 0.12 | 2/4 | `vary` | **qualifies** | 0.99 |
| `openml_credit_approval` | 30/30/30 | 0.9097 | 0.0000 [0.0000, 0.0000] | 0.0176 [0.0140, 0.0237] | 0.0279 [0.0222, 0.0375] | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.229 | 0.22 | 1/3 | `vary` | **qualifies** | 0.90 |
| `openml_credit_g` | 30/30/30 | 0.7691 | 0.0000 [0.0000, 0.0000] | 0.0482 [0.0384, 0.0648] | 0.0335 [0.0267, 0.0450] | 0.0038 | 0.0020 | 1 / 4 / 5 | 0.294 | 0.29 | 2/4 | `vary` | does not qualify | 0.52 |
| `openml_sonar` | 30/30/30 | 0.7563 | 0.0000 [0.0000, 0.0000] | 0.0603 [0.0480, 0.0810] | 0.0597 [0.0475, 0.0802] | 0.0128 | 0.0032 | 4 / 4 / 5 | 0.196 | 0.14 | 2/4 | `vary` | **qualifies** | 1.00 |
| `openml_blood_transfusion` | 30/30/30 | 0.7845 | 0.0000 [0.0000, 0.0000] | 0.0556 [0.0443, 0.0747] | 0.0564 [0.0449, 0.0758] | 0.0030 | 0.0020 | 2 / 2 / 5 | 0.103 | 0.09 | 0/2 | `vary` | **qualifies** | 0.48 |
| `openml_qsar_biodeg` | 30/30/30 | 0.9389 | 0.0000 [0.0000, 0.0000] | 0.0217 [0.0173, 0.0292] | 0.0180 [0.0143, 0.0241] | 0.0023 | 0.0020 | 0 / 2 / 5 | – | – | 0/2 | `vary` | does not qualify | 0.10 |

σ: sd of the baseline c0 metric over the 30 seeds of one condition; CI is the Gaussian chi-square interval. δ_n = max(0.002, 0.25 × median over all five edits of the joint paired sd(Δ̂)). Mean P(wrong) is shown to three decimals because two nodes sit within 0.004 of the 0.10 threshold. P(wrong) selection cap at n = 30: Φ(−2/√30) = 0.36.

### Table 2 — the adopted rule, criterion by criterion, and an independent recomputation

| Node | 30 seeds per condition | ≥ 2 material edits | mean P(wrong) ≥ 0.10 | σ_joint > 0 | verdict | recomputed from raw joint differences (#material, mean P(wrong), verdict) | e1_report label |
|---|---|---|---|---|---|---|---|
| `digits_mlp` | yes | yes | yes | yes | **qualifies** | 5, 0.101, qualifies | qualifies |
| `tabular_mlp` | yes | yes | yes | yes | **qualifies** | 3, 0.125, qualifies | qualifies |
| `openml_breast_w` | yes | yes | yes | yes | **qualifies** | 2, 0.233, qualifies | qualifies |
| `openml_ionosphere` | yes | yes | yes | yes | **qualifies** | 2, 0.195, qualifies | qualifies |
| `openml_wdbc` | yes | yes | yes | yes | **qualifies** | 2, 0.174, qualifies | qualifies |
| `openml_credit_approval` | yes | yes | yes | yes | **qualifies** | 2, 0.229, qualifies | qualifies |
| `openml_credit_g` | yes | no | yes | yes | does not qualify | 1, 0.294, does not qualify | more seeds needed |
| `openml_sonar` | yes | yes | yes | yes | **qualifies** | 4, 0.196, qualifies | qualifies |
| `openml_blood_transfusion` | yes | yes | yes | yes | **qualifies** | 2, 0.103, qualifies | qualifies |
| `openml_qsar_biodeg` | yes | no | no | yes | does not qualify | 0, –, does not qualify | more seeds needed |

### Table 3 — seed-bootstrap of the rule's outcome (joint seeds resampled, paired across configs; reported, not decisive)

| Node | seeds | P(qualifies) | P(#material = 0 / 1 / 2 / 3+) | mean P(wrong) over material, 5 / 50 / 95 % |
|---|---|---|---|---|
| `digits_mlp` | 30 | 0.48 | 0.00 / 0.00 / 0.00 / 1.00 | 0.07 / 0.10 / 0.13 |
| `tabular_mlp` | 30 | 0.75 | 0.00 / 0.00 / 0.17 / 0.83 | 0.04 / 0.12 / 0.15 |
| `openml_breast_w` | 30 | 0.97 | 0.00 / 0.03 / 0.97 / 0.00 | 0.15 / 0.22 / 0.27 |
| `openml_ionosphere` | 30 | 0.92 | 0.00 / 0.06 / 0.52 / 0.42 | 0.11 / 0.21 / 0.27 |
| `openml_wdbc` | 30 | 0.99 | 0.00 / 0.01 / 0.99 / 0.00 | 0.13 / 0.17 / 0.21 |
| `openml_credit_approval` | 30 | 0.90 | 0.00 / 0.09 / 0.49 / 0.42 | 0.14 / 0.21 / 0.26 |
| `openml_credit_g` | 30 | 0.52 | 0.10 / 0.38 / 0.35 / 0.18 | 0.17 / 0.26 / 0.33 |
| `openml_sonar` | 30 | 1.00 | 0.00 / 0.00 / 0.01 / 0.99 | 0.14 / 0.18 / 0.23 |
| `openml_blood_transfusion` | 30 | 0.48 | 0.00 / 0.00 / 1.00 / 0.00 | 0.04 / 0.10 / 0.16 |
| `openml_qsar_biodeg` | 30 | 0.10 | 0.63 / 0.27 / 0.09 / 0.01 | 0.12 / 0.24 / 0.35 |

B = 2000 resamples, numpy default_rng(20261022). The bootstrap applies the rule's effect criteria and σ_joint > 0 to each resample.

### Table 4 — per-edit rows (30 seeds), with the 12 Oct E1 (10 seeds) where it measured the node

| Node | Edit | Δ̂_J ± 2se | material | sd(Δ̂) joint | sd train | sd split | ϱ_joint | P(wrong) | regret \|Δ̂\|·P | 12 Oct: Δ̂_J ± 2se | 12 Oct: sd(Δ̂) joint | 12 Oct: P(wrong) | 12 Oct: material |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | LEARNING_RATE_INIT 1e-3 -> 0.002 | 0.0080 ± 0.0024 | yes | 0.0066 | 0.0050 | 0.0054 | 0.77 | 0.11 | 0.0009 | 0.0089 ± 0.0048 | 0.0075 | 0.12 | yes |
| `digits_mlp` | MAX_ITER 40 -> 80 | 0.0085 ± 0.0022 | yes | 0.0059 | 0.0043 | 0.0048 | 0.82 | 0.07 | 0.0006 | 0.0089 ± 0.0041 | 0.0064 | 0.08 | yes |
| `digits_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0159 ± 0.0040 | yes | 0.0110 | 0.0121 | 0.0095 | 0.60 | 0.07 | 0.0012 | -0.0134 ± 0.0091 | 0.0143 | 0.18 | yes |
| `digits_mlp` | HIDDEN_UNITS 32 -> 64 | 0.0089 ± 0.0030 | yes | 0.0083 | 0.0077 | 0.0078 | 0.71 | 0.14 | 0.0012 | 0.0067 ± 0.0060 | 0.0095 | 0.24 | yes |
| `digits_mlp` | BATCH_SIZE 64 -> 32 | 0.0068 ± 0.0019 | yes | 0.0053 | 0.0044 | 0.0049 | 0.86 | 0.10 | 0.0007 | 0.0067 ± 0.0043 | 0.0068 | 0.16 | yes |
| `tabular_mlp` | MAX_ITER 40 -> 20 | -0.0087 ± 0.0013 | yes | 0.0036 | 0.0021 | 0.0034 | 0.97 | 0.01 | 0.0001 | -0.0097 ± 0.0029 | 0.0046 | 0.02 | yes |
| `tabular_mlp` | ALPHA 1e-4 -> 5e-05 | 0.0000 ± 0.0000 | no | 0.0000 | 0.0001 | 0.0001 | 1.00 | 0.49 | 0.0000 | -0.0000 ± 0.0000 | 0.0001 | 0.48 | no |
| `tabular_mlp` | BATCH_SIZE 64 -> 32 | 0.0025 ± 0.0007 | yes | 0.0019 | 0.0012 | 0.0013 | 0.99 | 0.10 | 0.0002 | 0.0022 ± 0.0012 | 0.0019 | 0.12 | yes |
| `tabular_mlp` | ALPHA 1e-4 -> 0.0002 | -0.0000 ± 0.0000 | no | 0.0001 | 0.0000 | 0.0001 | 1.00 | 0.49 | 0.0000 | -0.0000 ± 0.0000 | 0.0000 | 0.40 | no |
| `tabular_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0038 ± 0.0023 | yes | 0.0062 | 0.0062 | 0.0044 | 0.88 | 0.27 | 0.0010 | -0.0059 ± 0.0039 | 0.0061 | 0.17 | yes |
| `openml_breast_w` | C 0.15 -> 0.075 | -0.0002 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0005 | 0.98 | 0.38 | 0.0001 | -0.0001 ± 0.0002 | 0.0004 | 0.41 | no |
| `openml_breast_w` | C 0.15 -> 0.3 | -0.0001 ± 0.0002 | no | 0.0006 | 0.0000 | 0.0005 | 0.99 | 0.46 | 0.0000 | -0.0002 ± 0.0003 | 0.0005 | 0.33 | no |
| `openml_breast_w` | model_type logistic_regression -> random_forest | -0.0035 ± 0.0019 | yes | 0.0052 | 0.0021 | 0.0043 | 0.72 | 0.25 | 0.0009 | -0.0025 ± 0.0015 | 0.0024 | 0.15 | yes |
| `openml_breast_w` | model_type logistic_regression -> gradient_boosting | -0.0057 ± 0.0027 | yes | 0.0073 | 0.0017 | 0.0184 | 0.48 | 0.22 | 0.0012 | -0.0050 ± 0.0034 | 0.0054 | 0.17 | yes |
| `openml_breast_w` | class_weight balanced -> null | 0.0000 ± 0.0001 | no | 0.0002 | 0.0000 | 0.0004 | 1.00 | 0.42 | 0.0000 | 0.0001 ± 0.0001 | 0.0002 | 0.32 | no |
| `openml_ionosphere` | C 0.15 -> 0.075 | -0.0040 ± 0.0051 | no | 0.0140 | 0.0000 | 0.0085 | 0.96 | 0.39 | 0.0016 | -0.0014 ± 0.0086 | 0.0135 | 0.46 | no |
| `openml_ionosphere` | C 0.15 -> 0.3 | -0.0023 ± 0.0058 | no | 0.0160 | 0.0000 | 0.0122 | 0.92 | 0.44 | 0.0010 | -0.0025 ± 0.0102 | 0.0162 | 0.44 | no |
| `openml_ionosphere` | model_type logistic_regression -> random_forest | 0.0500 ± 0.0146 | yes | 0.0399 | 0.0022 | 0.0449 | 0.34 | 0.11 | 0.0053 | 0.0502 ± 0.0245 | 0.0387 | 0.10 | yes |
| `openml_ionosphere` | model_type logistic_regression -> gradient_boosting | 0.0255 ± 0.0164 | yes | 0.0449 | 0.0022 | 0.0616 | 0.28 | 0.28 | 0.0073 | 0.0291 ± 0.0242 | 0.0382 | 0.22 | yes |
| `openml_ionosphere` | class_weight balanced -> null | 0.0001 ± 0.0021 | no | 0.0057 | 0.0000 | 0.0047 | 0.99 | 0.49 | 0.0001 | 0.0003 ± 0.0034 | 0.0054 | 0.48 | no |
| `openml_wdbc` | C 0.15 -> 0.075 | -0.0003 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0007 | 1.00 | 0.34 | 0.0001 | -0.0002 ± 0.0006 | 0.0009 | 0.40 | no |
| `openml_wdbc` | C 0.15 -> 0.3 | 0.0003 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0009 | 1.00 | 0.32 | 0.0001 | 0.0002 ± 0.0005 | 0.0008 | 0.42 | no |
| `openml_wdbc` | model_type logistic_regression -> random_forest | -0.0061 ± 0.0033 | yes | 0.0091 | 0.0015 | 0.0059 | 0.68 | 0.25 | 0.0015 | -0.0075 ± 0.0073 | 0.0115 | 0.26 | yes |
| `openml_wdbc` | model_type logistic_regression -> gradient_boosting | -0.0316 ± 0.0088 | yes | 0.0242 | 0.0007 | 0.0246 | 0.59 | 0.10 | 0.0030 | -0.0325 ± 0.0134 | 0.0212 | 0.06 | yes |
| `openml_wdbc` | class_weight balanced -> null | 0.0000 ± 0.0002 | no | 0.0006 | 0.0000 | 0.0004 | 1.00 | 0.50 | 0.0000 | 0.0000 ± 0.0004 | 0.0007 | 0.50 | no |
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0020 ± 0.0010 | no | 0.0027 | 0.0000 | 0.0025 | 1.00 | 0.24 | 0.0005 | -0.0012 ± 0.0019 | 0.0031 | 0.35 | no |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0006 ± 0.0011 | no | 0.0030 | 0.0000 | 0.0023 | 0.99 | 0.43 | 0.0002 | 0.0003 ± 0.0013 | 0.0020 | 0.43 | no |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0130 ± 0.0048 | yes | 0.0130 | 0.0035 | 0.0141 | 0.88 | 0.16 | 0.0021 | 0.0189 ± 0.0084 | 0.0133 | 0.08 | yes |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0085 ± 0.0059 | yes | 0.0162 | 0.0026 | 0.0199 | 0.81 | 0.30 | 0.0026 | 0.0183 ± 0.0093 | 0.0147 | 0.11 | yes |
| `openml_credit_approval` | class_weight balanced -> null | 0.0002 ± 0.0003 | no | 0.0008 | 0.0000 | 0.0008 | 1.00 | 0.42 | 0.0001 | 0.0006 ± 0.0006 | 0.0009 | 0.25 | no |
| `openml_credit_g` | C 0.15 -> 0.075 | 0.0019 ± 0.0014 | no | 0.0038 | 0.0000 | 0.0040 | 0.99 | 0.30 | 0.0006 | – | – | – | – |
| `openml_credit_g` | C 0.15 -> 0.3 | -0.0014 ± 0.0012 | no | 0.0032 | 0.0000 | 0.0042 | 1.00 | 0.33 | 0.0005 | – | – | – | – |
| `openml_credit_g` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0074 | no | 0.0203 | 0.0083 | 0.0161 | 0.83 | 0.44 | 0.0013 | – | – | – | – |
| `openml_credit_g` | model_type logistic_regression -> gradient_boosting | -0.0150 ± 0.0101 | yes | 0.0277 | 0.0026 | 0.0262 | 0.66 | 0.29 | 0.0044 | – | – | – | – |
| `openml_credit_g` | class_weight balanced -> null | 0.0011 ± 0.0011 | no | 0.0031 | 0.0000 | 0.0037 | 1.00 | 0.36 | 0.0004 | – | – | – | – |
| `openml_sonar` | C 0.15 -> 0.075 | 0.0062 ± 0.0041 | yes | 0.0113 | 0.0000 | 0.0117 | 0.98 | 0.29 | 0.0018 | – | – | – | – |
| `openml_sonar` | C 0.15 -> 0.3 | -0.0087 ± 0.0047 | yes | 0.0128 | 0.0000 | 0.0098 | 0.98 | 0.25 | 0.0022 | – | – | – | – |
| `openml_sonar` | model_type logistic_regression -> random_forest | 0.0569 ± 0.0163 | yes | 0.0447 | 0.0211 | 0.0581 | 0.67 | 0.10 | 0.0058 | – | – | – | – |
| `openml_sonar` | model_type logistic_regression -> gradient_boosting | -0.1041 ± 0.0352 | yes | 0.0964 | 0.0467 | 0.1051 | 0.24 | 0.14 | 0.0146 | – | – | – | – |
| `openml_sonar` | class_weight balanced -> null | 0.0008 ± 0.0014 | no | 0.0039 | 0.0000 | 0.0033 | 1.00 | 0.41 | 0.0003 | – | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.075 | 0.0006 ± 0.0010 | no | 0.0027 | 0.0000 | 0.0037 | 1.00 | 0.42 | 0.0002 | – | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.3 | -0.0004 ± 0.0007 | no | 0.0018 | 0.0000 | 0.0019 | 1.00 | 0.42 | 0.0002 | – | – | – | – |
| `openml_blood_transfusion` | model_type logistic_regression -> random_forest | -0.0260 ± 0.0087 | yes | 0.0240 | 0.0060 | 0.0338 | 0.91 | 0.14 | 0.0036 | – | – | – | – |
| `openml_blood_transfusion` | model_type logistic_regression -> gradient_boosting | -0.0664 ± 0.0163 | yes | 0.0446 | 0.0042 | 0.0439 | 0.76 | 0.07 | 0.0045 | – | – | – | – |
| `openml_blood_transfusion` | class_weight balanced -> null | 0.0004 ± 0.0011 | no | 0.0030 | 0.0000 | 0.0017 | 1.00 | 0.45 | 0.0002 | – | – | – | – |
| `openml_qsar_biodeg` | C 0.15 -> 0.075 | -0.0017 ± 0.0008 | no | 0.0023 | 0.0000 | 0.0021 | 0.99 | 0.23 | 0.0004 | – | – | – | – |
| `openml_qsar_biodeg` | C 0.15 -> 0.3 | 0.0010 ± 0.0007 | no | 0.0020 | 0.0000 | 0.0026 | 0.99 | 0.30 | 0.0003 | – | – | – | – |
| `openml_qsar_biodeg` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0055 | no | 0.0151 | 0.0042 | 0.0159 | 0.68 | 0.42 | 0.0012 | – | – | – | – |
| `openml_qsar_biodeg` | model_type logistic_regression -> gradient_boosting | -0.0005 ± 0.0061 | no | 0.0166 | 0.0026 | 0.0147 | 0.64 | 0.49 | 0.0002 | – | – | – | – |
| `openml_qsar_biodeg` | class_weight balanced -> null | 0.0005 ± 0.0005 | no | 0.0015 | 0.0000 | 0.0020 | 1.00 | 0.37 | 0.0002 | – | – | – | – |

### Table 5 — node level: 12 Oct E1 (10 seeds) vs. this run, for the six nodes E1 measured

| Node | data | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / resolved / all | mean P(wrong), material | effect criteria of the rule met (at the n shown) |
|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 / 5 | 0.156 | yes |
| `digits_mlp` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 / 5 | 0.156 | yes |
| `digits_mlp` | this run, seeds 11–30 (independent) | 20 | 0.0072 | 0.0074 | 0.0088 | 0.0063 | 0.0020 | 5 / 5 / 5 | 0.076 | no |
| `digits_mlp` | this run, all 30 seeds | 30 | 0.0068 | 0.0073 | 0.0102 | 0.0066 | 0.0020 | 5 / 5 / 5 | 0.101 | yes |
| `tabular_mlp` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.103 | yes |
| `tabular_mlp` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.103 | yes |
| `tabular_mlp` | this run, seeds 11–30 (independent) | 20 | 0.0028 | 0.0125 | 0.0105 | 0.0020 | 0.0020 | 3 / 3 / 5 | 0.140 | yes |
| `tabular_mlp` | this run, all 30 seeds | 30 | 0.0029 | 0.0123 | 0.0121 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.125 | yes |
| `openml_breast_w` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 2 / 5 | 0.162 | yes |
| `openml_breast_w` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 2 / 5 | 0.162 | yes |
| `openml_breast_w` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0051 | 0.0042 | 0.0008 | 0.0020 | 2 / 2 / 5 | 0.244 | yes |
| `openml_breast_w` | this run, all 30 seeds | 30 | 0.0000 | 0.0050 | 0.0038 | 0.0007 | 0.0020 | 2 / 2 / 5 | 0.233 | yes |
| `openml_ionosphere` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 2 / 5 | 0.160 | yes |
| `openml_ionosphere` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 2 / 5 | 0.160 | yes |
| `openml_ionosphere` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0539 | 0.0403 | 0.0163 | 0.0041 | 2 / 2 / 5 | 0.214 | yes |
| `openml_ionosphere` | this run, all 30 seeds | 30 | 0.0000 | 0.0485 | 0.0410 | 0.0160 | 0.0040 | 2 / 2 / 5 | 0.195 | yes |
| `openml_wdbc` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 2 / 5 | 0.160 | yes |
| `openml_wdbc` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 2 / 5 | 0.160 | yes |
| `openml_wdbc` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0057 | 0.0080 | 0.0006 | 0.0020 | 2 / 4 / 5 | 0.182 | yes |
| `openml_wdbc` | this run, all 30 seeds | 30 | 0.0000 | 0.0061 | 0.0079 | 0.0007 | 0.0020 | 2 / 4 / 5 | 0.174 | yes |
| `openml_credit_approval` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0080 | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.092 | no |
| `openml_credit_approval` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0080 | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.092 | no |
| `openml_credit_approval` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0195 | 0.0323 | 0.0034 | 0.0020 | 2 / 2 / 5 | 0.192 | yes |
| `openml_credit_approval` | this run, all 30 seeds | 30 | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.229 | yes |

Only the 30-seed row is a verdict under the adopted rule; the 10- and 20-seed rows show the same criteria at other n for comparison.

### Table 6 — `openml_credit_approval`: 22 Oct re-measurement (sklearn 1.9.1) vs. this run (sklearn 1.8.0), same 30 seeds

| data | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all | mean P(wrong), material | effect criteria met |
|---|---|---|---|---|---|---|
| 22 Oct re-measurement (venv313: sklearn 1.9.1, numpy 2.5.4) | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.239 | yes |
| this run (hvenv: sklearn 1.8.0, numpy 2.4.4) | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.229 | yes |

| Edit | Δ̂_J ± 2se, 22 Oct | Δ̂_J ± 2se, this run | sd(Δ̂) joint, 22 Oct → this run | P(wrong), 22 Oct → this run | material, 22 Oct → this run |
|---|---|---|---|---|---|
| C 0.15 -> 0.075 | -0.0020 ± 0.0010 | -0.0020 ± 0.0010 | 0.0027 → 0.0027 | 0.24 → 0.24 | no → no |
| C 0.15 -> 0.3 | 0.0006 ± 0.0011 | 0.0006 ± 0.0011 | 0.0030 → 0.0030 | 0.43 → 0.43 | no → no |
| model_type logistic_regression -> random_forest | 0.0123 ± 0.0047 | 0.0130 ± 0.0048 | 0.0129 → 0.0130 | 0.17 → 0.16 | yes → yes |
| model_type logistic_regression -> gradient_boosting | 0.0082 ± 0.0059 | 0.0085 ± 0.0059 | 0.0162 → 0.0162 | 0.31 → 0.30 | yes → yes |
| class_weight balanced -> null | 0.0002 ± 0.0003 | 0.0002 ± 0.0003 | 0.0008 → 0.0008 | 0.42 → 0.42 | no → no |

### Table 7 — bit-reproducibility of earlier runs at identical node, config, condition and seeds

c0–c2 and c5 are the logistic-regression / small-edit configs on OpenML nodes; c3 = random forest, c4 = gradient boosting.

| Node:config | vs 12 Oct E1: identical | different | vs 22 Oct re-measurement: identical | different |
|---|---|---|---|---|
| `digits_mlp:c0` | 32 | 0 | – | – |
| `digits_mlp:c1` | 32 | 0 | – | – |
| `digits_mlp:c2` | 32 | 0 | – | – |
| `digits_mlp:c3` | 32 | 0 | – | – |
| `digits_mlp:c4` | 32 | 0 | – | – |
| `digits_mlp:c5` | 32 | 0 | – | – |
| `openml_breast_w:c0` | 32 | 0 | – | – |
| `openml_breast_w:c1` | 32 | 0 | – | – |
| `openml_breast_w:c2` | 32 | 0 | – | – |
| `openml_breast_w:c3` | 32 | 0 | – | – |
| `openml_breast_w:c4` | 32 | 0 | – | – |
| `openml_breast_w:c5` | 32 | 0 | – | – |
| `openml_credit_approval:c0` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c1` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c2` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c3` | 32 | 0 | 2 | 90 |
| `openml_credit_approval:c4` | 32 | 0 | 8 | 84 |
| `openml_credit_approval:c5` | 32 | 0 | 92 | 0 |
| `openml_ionosphere:c0` | 32 | 0 | – | – |
| `openml_ionosphere:c1` | 32 | 0 | – | – |
| `openml_ionosphere:c2` | 32 | 0 | – | – |
| `openml_ionosphere:c3` | 32 | 0 | – | – |
| `openml_ionosphere:c4` | 32 | 0 | – | – |
| `openml_ionosphere:c5` | 32 | 0 | – | – |
| `openml_wdbc:c0` | 32 | 0 | – | – |
| `openml_wdbc:c1` | 32 | 0 | – | – |
| `openml_wdbc:c2` | 32 | 0 | – | – |
| `openml_wdbc:c3` | 32 | 0 | – | – |
| `openml_wdbc:c4` | 32 | 0 | – | – |
| `openml_wdbc:c5` | 32 | 0 | – | – |
| `tabular_mlp:c0` | 32 | 0 | – | – |
| `tabular_mlp:c1` | 32 | 0 | – | – |
| `tabular_mlp:c2` | 32 | 0 | – | – |
| `tabular_mlp:c3` | 32 | 0 | – | – |
| `tabular_mlp:c4` | 32 | 0 | – | – |
| `tabular_mlp:c5` | 32 | 0 | – | – |

### Table 8 — noise-node pool under the adopted rule

| | nodes | count |
|---|---|---|
| qualify | `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion` | 8 |
| do not qualify | `openml_credit_g`, `openml_qsar_biodeg` | 2 |
| PLAN target | ≥ 8 | met |

