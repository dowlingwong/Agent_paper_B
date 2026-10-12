| Node | default m | bit-identical at fixed seed | σ_train | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all edits | mean P(wrong), material | regret share, material | campaign-seed decision wrong | sd_train/sd_joint, material | median s/run | D21 (proposed) | split policy (proposed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 0.9554 | yes | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 5 / 5 / 5 | 0.16 | 0.15 | 0/5 | 0.65 | 1.2 | qualifies | `fixed` |
| `tabular_mlp` | 0.9141 | yes | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 3 / 3 / 5 | 0.10 | 0.08 | 0/3 | 0.56 | 1.1 | qualifies | `fixed` |
| `lr_synthetic` | 0.9213 | yes | 0.0001 | 0.0152 | 0.0099 | 0.0003 | 0 / 2 / 5 | – | – | 0/2 | 0.01 | 0.7 | does not qualify | `vary` |
| `mlp_synthetic` | 0.9994 | yes | 0.0001 | 0.0013 | 0.0016 | 0.0003 | 0 / 1 / 5 | – | – | 0/1 | 0.06 | 14.9 | does not qualify | `vary` |
| `openml_breast_w` | 0.9932 | yes | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 2 / 2 / 5 | 0.16 | 0.17 | 0/2 | 0.39 | 1.3 | qualifies | `vary` |
| `openml_credit_approval` | 0.9097 | yes | 0.0000 | 0.0080 | 0.0169 | 0.0031 | 2 / 3 / 5 | 0.09 | 0.09 | 0/3 | 0.15 | 1.4 | more seeds needed | `vary` |
| `openml_diabetes` | 0.8297 | yes | 0.0000 | 0.0336 | 0.0317 | 0.0024 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | 1.2 | more seeds needed | `vary` |
| `openml_ionosphere` | 0.9845 | yes | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 2 / 2 / 5 | 0.16 | 0.14 | 1/2 | 0.06 | 1.4 | qualifies | `vary` |
| `openml_wdbc` | 0.9976 | yes | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 2 / 2 / 5 | 0.16 | 0.10 | 0/2 | 0.11 | 1.5 | qualifies | `vary` |
| `mlagentbench_vectorization` | 13.2126 | no | 2.4240 | 2.2334 | 2.2893 | – | 0 / 0 / 0 | – | – | 0/0 | 1.06 | 0.5 | does not qualify | `fixed` |

### Per-edit rows

| Node | Edit | Δ̂_J (± 2 se) | material | ϱ_joint | sd(Δ̂) joint | sd train | sd split | P(wrong) | flip rate | campaign Δ̂ | campaign wrong |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | LEARNING_RATE_INIT 1e-3 -> 0.002 | 0.0089 ± 0.0048 | yes | 0.80 | 0.0075 | 0.0049 | 0.0071 | 0.12 | 0.10 | 0.0084 | no |
| `digits_mlp` | MAX_ITER 40 -> 80 | 0.0089 ± 0.0041 | yes | 0.87 | 0.0064 | 0.0027 | 0.0064 | 0.08 | 0.20 | 0.0084 | no |
| `digits_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0134 ± 0.0091 | yes | 0.57 | 0.0143 | 0.0108 | 0.0140 | 0.18 | 0.20 | -0.0139 | no |
| `digits_mlp` | HIDDEN_UNITS 32 -> 64 | 0.0067 ± 0.0060 | yes | 0.69 | 0.0095 | 0.0063 | 0.0100 | 0.24 | 0.20 | 0.0251 | no |
| `digits_mlp` | BATCH_SIZE 64 -> 32 | 0.0067 ± 0.0043 | yes | 0.84 | 0.0068 | 0.0042 | 0.0059 | 0.16 | 0.20 | 0.0111 | no |
| `tabular_mlp` | MAX_ITER 40 -> 20 | -0.0097 ± 0.0029 | yes | 0.97 | 0.0046 | 0.0021 | 0.0028 | 0.02 | 0.00 | -0.0115 | no |
| `tabular_mlp` | ALPHA 1e-4 -> 5e-05 | -0.0000 ± 0.0000 | no | 1.00 | 0.0001 | 0.0001 | 0.0001 | 0.48 | – | – | – |
| `tabular_mlp` | BATCH_SIZE 64 -> 32 | 0.0022 ± 0.0012 | yes | 0.99 | 0.0019 | 0.0011 | 0.0016 | 0.12 | 0.10 | 0.0027 | no |
| `tabular_mlp` | ALPHA 1e-4 -> 0.0002 | -0.0000 ± 0.0000 | no | 1.00 | 0.0000 | 0.0001 | 0.0001 | 0.40 | – | – | – |
| `tabular_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0059 ± 0.0039 | yes | 0.92 | 0.0061 | 0.0048 | 0.0040 | 0.17 | 0.20 | -0.0014 | no |
| `lr_synthetic` | LEARNING_RATE 5e-4 -> 0.001 | -0.0001 ± 0.0002 | no | 1.00 | 0.0003 | 0.0001 | 0.0004 | 0.37 | – | – | – |
| `lr_synthetic` | N_EPOCHS 80 -> 160 | -0.0001 ± 0.0002 | no | 1.00 | 0.0003 | 0.0001 | 0.0004 | 0.37 | – | – | – |
| `lr_synthetic` | REGULARIZATION 0.001 -> 0.002 | 0.0000 ± 0.0000 | no | 1.00 | 0.0000 | 0.0000 | 0.0000 | 0.50 | – | – | – |
| `lr_synthetic` | LEARNING_RATE 5e-4 -> 0.00025 | 0.0002 ± 0.0002 | no | 1.00 | 0.0003 | 0.0002 | 0.0004 | 0.26 | 0.40 | 0.0006 | no |
| `lr_synthetic` | N_EPOCHS 80 -> 40 | 0.0002 ± 0.0002 | no | 1.00 | 0.0003 | 0.0002 | 0.0004 | 0.26 | 0.40 | 0.0006 | no |
| `mlp_synthetic` | LEARNING_RATE 0.01 -> 0.005 | -0.0002 ± 0.0003 | no | 0.98 | 0.0005 | 0.0001 | 0.0002 | 0.37 | – | – | – |
| `mlp_synthetic` | N_EPOCHS 10000 -> 20000 | 0.0000 ± 0.0002 | no | 0.98 | 0.0003 | 0.0001 | 0.0001 | 0.45 | – | – | – |
| `mlp_synthetic` | REGULARIZATION 0.001 -> 0.0005 | -0.0002 ± 0.0002 | no | 0.99 | 0.0003 | 0.0001 | 0.0003 | 0.21 | 0.20 | -0.0002 | no |
| `mlp_synthetic` | HIDDEN_DIM 64 -> 128 | -0.0000 ± 0.0001 | no | 0.99 | 0.0002 | 0.0001 | 0.0002 | 0.49 | – | – | – |
| `mlp_synthetic` | BATCH_SIZE 128 -> 64 | 0.0000 ± 0.0002 | no | 0.98 | 0.0003 | 0.0001 | 0.0001 | 0.43 | – | – | – |
| `openml_breast_w` | C 0.15 -> 0.075 | -0.0001 ± 0.0002 | no | 0.99 | 0.0004 | 0.0000 | 0.0005 | 0.41 | – | – | – |
| `openml_breast_w` | C 0.15 -> 0.3 | -0.0002 ± 0.0003 | no | 0.99 | 0.0005 | 0.0000 | 0.0004 | 0.33 | – | – | – |
| `openml_breast_w` | model_type logistic_regression -> random_forest | -0.0025 ± 0.0015 | yes | 0.85 | 0.0024 | 0.0011 | 0.0049 | 0.15 | 0.30 | -0.0020 | no |
| `openml_breast_w` | model_type logistic_regression -> gradient_boosting | -0.0050 ± 0.0034 | yes | 0.54 | 0.0054 | 0.0017 | 0.0073 | 0.17 | 0.10 | -0.0028 | no |
| `openml_breast_w` | class_weight balanced -> null | 0.0001 ± 0.0001 | no | 1.00 | 0.0002 | 0.0000 | 0.0003 | 0.32 | – | – | – |
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0012 ± 0.0019 | no | 0.98 | 0.0031 | 0.0000 | 0.0019 | 0.35 | – | – | – |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0003 ± 0.0013 | no | 0.99 | 0.0020 | 0.0000 | 0.0015 | 0.43 | – | – | – |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0189 ± 0.0084 | yes | 0.70 | 0.0133 | 0.0016 | 0.0125 | 0.08 | 0.00 | 0.0120 | no |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0183 ± 0.0093 | yes | 0.62 | 0.0147 | 0.0028 | 0.0202 | 0.11 | 0.10 | 0.0056 | no |
| `openml_credit_approval` | class_weight balanced -> null | 0.0006 ± 0.0006 | no | 1.00 | 0.0009 | 0.0000 | 0.0007 | 0.25 | 0.50 | 0.0019 | no |
| `openml_diabetes` | C 0.15 -> 0.075 | 0.0009 ± 0.0015 | no | 1.00 | 0.0024 | 0.0000 | 0.0012 | 0.36 | – | – | – |
| `openml_diabetes` | C 0.15 -> 0.3 | -0.0004 ± 0.0010 | no | 1.00 | 0.0015 | 0.0000 | 0.0010 | 0.40 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> random_forest | 0.0127 ± 0.0168 | no | 0.55 | 0.0265 | 0.0053 | 0.0196 | 0.32 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> gradient_boosting | -0.0013 ± 0.0155 | no | 0.64 | 0.0245 | 0.0009 | 0.0206 | 0.48 | – | – | – |
| `openml_diabetes` | class_weight balanced -> null | 0.0011 ± 0.0012 | no | 1.00 | 0.0019 | 0.0000 | 0.0015 | 0.29 | – | – | – |
| `openml_ionosphere` | C 0.15 -> 0.075 | -0.0014 ± 0.0086 | no | 0.95 | 0.0135 | 0.0000 | 0.0085 | 0.46 | – | – | – |
| `openml_ionosphere` | C 0.15 -> 0.3 | -0.0025 ± 0.0102 | no | 0.95 | 0.0162 | 0.0000 | 0.0145 | 0.44 | – | – | – |
| `openml_ionosphere` | model_type logistic_regression -> random_forest | 0.0502 ± 0.0245 | yes | 0.47 | 0.0387 | 0.0023 | 0.0288 | 0.10 | 0.10 | 0.0077 | no |
| `openml_ionosphere` | model_type logistic_regression -> gradient_boosting | 0.0291 ± 0.0242 | yes | 0.51 | 0.0382 | 0.0022 | 0.0687 | 0.22 | 0.20 | -0.0139 | yes |
| `openml_ionosphere` | class_weight balanced -> null | 0.0003 ± 0.0034 | no | 0.99 | 0.0054 | 0.0000 | 0.0060 | 0.48 | – | – | – |
| `openml_wdbc` | C 0.15 -> 0.075 | -0.0002 ± 0.0006 | no | 0.99 | 0.0009 | 0.0000 | 0.0010 | 0.40 | – | – | – |
| `openml_wdbc` | C 0.15 -> 0.3 | 0.0002 ± 0.0005 | no | 0.99 | 0.0008 | 0.0000 | 0.0012 | 0.42 | – | – | – |
| `openml_wdbc` | model_type logistic_regression -> random_forest | -0.0075 ± 0.0073 | yes | 0.49 | 0.0115 | 0.0021 | 0.0081 | 0.26 | 0.10 | -0.0024 | no |
| `openml_wdbc` | model_type logistic_regression -> gradient_boosting | -0.0325 ± 0.0134 | yes | 0.39 | 0.0212 | 0.0009 | 0.0219 | 0.06 | 0.00 | -0.0159 | no |
| `openml_wdbc` | class_weight balanced -> null | 0.0000 ± 0.0004 | no | 1.00 | 0.0007 | 0.0000 | 0.0006 | 0.50 | – | – | – |
