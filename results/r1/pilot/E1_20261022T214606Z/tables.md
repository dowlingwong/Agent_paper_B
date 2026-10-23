| Node | default m | bit-identical at fixed seed | σ_train | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all edits | mean P(wrong), material | regret share, material | campaign-seed decision wrong | sd_train/sd_joint, material | median s/run | D21 (proposed) | split policy (proposed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 0.9554 | yes | 0.0068 | 0.0073 | 0.0102 | 0.0066 | 5 / 5 / 5 | 0.10 | 0.10 | 0/5 | 0.82 | 0.8 | qualifies | `fixed` |
| `tabular_mlp` | 0.9141 | yes | 0.0029 | 0.0123 | 0.0121 | 0.0019 | 3 / 3 / 5 | 0.13 | 0.09 | 0/3 | 0.64 | 0.8 | qualifies | `fixed` |
| `openml_breast_w` | 0.9932 | yes | 0.0000 | 0.0050 | 0.0038 | 0.0007 | 2 / 2 / 5 | 0.23 | 0.23 | 0/2 | 0.32 | 0.9 | qualifies | `vary` |
| `openml_ionosphere` | 0.9845 | yes | 0.0000 | 0.0485 | 0.0410 | 0.0160 | 2 / 2 / 5 | 0.19 | 0.17 | 1/2 | 0.05 | 0.9 | qualifies | `vary` |
| `openml_wdbc` | 0.9976 | yes | 0.0000 | 0.0061 | 0.0079 | 0.0007 | 2 / 4 / 5 | 0.17 | 0.12 | 2/4 | 0.10 | 0.8 | qualifies | `vary` |
| `openml_credit_approval` | 0.9097 | yes | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.23 | 0.22 | 1/3 | 0.22 | 0.8 | qualifies | `vary` |
| `openml_credit_g` | 0.7691 | yes | 0.0000 | 0.0482 | 0.0335 | 0.0038 | 1 / 4 / 5 | 0.29 | 0.29 | 2/4 | 0.09 | 0.8 | more seeds needed | `vary` |
| `openml_sonar` | 0.7563 | yes | 0.0000 | 0.0603 | 0.0597 | 0.0128 | 4 / 4 / 5 | 0.20 | 0.14 | 2/4 | 0.24 | 0.9 | qualifies | `vary` |
| `openml_blood_transfusion` | 0.7845 | yes | 0.0000 | 0.0556 | 0.0564 | 0.0030 | 2 / 2 / 5 | 0.10 | 0.09 | 0/2 | 0.17 | 0.9 | qualifies | `vary` |
| `openml_qsar_biodeg` | 0.9389 | yes | 0.0000 | 0.0217 | 0.0180 | 0.0023 | 0 / 2 / 5 | – | – | 0/2 | 0.00 | 0.9 | more seeds needed | `vary` |

### Per-edit rows

| Node | Edit | Δ̂_J (± 2 se) | material | ϱ_joint | sd(Δ̂) joint | sd train | sd split | P(wrong) | flip rate | campaign Δ̂ | campaign wrong |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | LEARNING_RATE_INIT 1e-3 -> 0.002 | 0.0080 ± 0.0024 | yes | 0.77 | 0.0066 | 0.0050 | 0.0054 | 0.11 | 0.17 | 0.0084 | no |
| `digits_mlp` | MAX_ITER 40 -> 80 | 0.0085 ± 0.0022 | yes | 0.82 | 0.0059 | 0.0043 | 0.0048 | 0.07 | 0.10 | 0.0084 | no |
| `digits_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0159 ± 0.0040 | yes | 0.60 | 0.0110 | 0.0121 | 0.0095 | 0.07 | 0.13 | -0.0139 | no |
| `digits_mlp` | HIDDEN_UNITS 32 -> 64 | 0.0089 ± 0.0030 | yes | 0.71 | 0.0083 | 0.0077 | 0.0078 | 0.14 | 0.17 | 0.0251 | no |
| `digits_mlp` | BATCH_SIZE 64 -> 32 | 0.0068 ± 0.0019 | yes | 0.86 | 0.0053 | 0.0044 | 0.0049 | 0.10 | 0.13 | 0.0111 | no |
| `tabular_mlp` | MAX_ITER 40 -> 20 | -0.0087 ± 0.0013 | yes | 0.97 | 0.0036 | 0.0021 | 0.0034 | 0.01 | 0.00 | -0.0115 | no |
| `tabular_mlp` | ALPHA 1e-4 -> 5e-05 | 0.0000 ± 0.0000 | no | 1.00 | 0.0000 | 0.0001 | 0.0001 | 0.49 | – | – | – |
| `tabular_mlp` | BATCH_SIZE 64 -> 32 | 0.0025 ± 0.0007 | yes | 0.99 | 0.0019 | 0.0012 | 0.0013 | 0.10 | 0.07 | 0.0027 | no |
| `tabular_mlp` | ALPHA 1e-4 -> 0.0002 | -0.0000 ± 0.0000 | no | 1.00 | 0.0001 | 0.0000 | 0.0001 | 0.49 | – | – | – |
| `tabular_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0038 ± 0.0023 | yes | 0.88 | 0.0062 | 0.0062 | 0.0044 | 0.27 | 0.27 | -0.0014 | no |
| `openml_breast_w` | C 0.15 -> 0.075 | -0.0002 ± 0.0002 | no | 0.98 | 0.0007 | 0.0000 | 0.0005 | 0.38 | – | – | – |
| `openml_breast_w` | C 0.15 -> 0.3 | -0.0001 ± 0.0002 | no | 0.99 | 0.0006 | 0.0000 | 0.0005 | 0.46 | – | – | – |
| `openml_breast_w` | model_type logistic_regression -> random_forest | -0.0035 ± 0.0019 | yes | 0.72 | 0.0052 | 0.0021 | 0.0043 | 0.25 | 0.30 | -0.0020 | no |
| `openml_breast_w` | model_type logistic_regression -> gradient_boosting | -0.0057 ± 0.0027 | yes | 0.48 | 0.0073 | 0.0017 | 0.0184 | 0.22 | 0.20 | -0.0028 | no |
| `openml_breast_w` | class_weight balanced -> null | 0.0000 ± 0.0001 | no | 1.00 | 0.0002 | 0.0000 | 0.0004 | 0.42 | – | – | – |
| `openml_ionosphere` | C 0.15 -> 0.075 | -0.0040 ± 0.0051 | no | 0.96 | 0.0140 | 0.0000 | 0.0085 | 0.39 | – | – | – |
| `openml_ionosphere` | C 0.15 -> 0.3 | -0.0023 ± 0.0058 | no | 0.92 | 0.0160 | 0.0000 | 0.0122 | 0.44 | – | – | – |
| `openml_ionosphere` | model_type logistic_regression -> random_forest | 0.0500 ± 0.0146 | yes | 0.34 | 0.0399 | 0.0022 | 0.0449 | 0.11 | 0.10 | 0.0077 | no |
| `openml_ionosphere` | model_type logistic_regression -> gradient_boosting | 0.0255 ± 0.0164 | yes | 0.28 | 0.0449 | 0.0022 | 0.0616 | 0.28 | 0.30 | -0.0139 | yes |
| `openml_ionosphere` | class_weight balanced -> null | 0.0001 ± 0.0021 | no | 0.99 | 0.0057 | 0.0000 | 0.0047 | 0.49 | – | – | – |
| `openml_wdbc` | C 0.15 -> 0.075 | -0.0003 ± 0.0002 | no | 1.00 | 0.0007 | 0.0000 | 0.0007 | 0.34 | 0.63 | 0.0000 | yes |
| `openml_wdbc` | C 0.15 -> 0.3 | 0.0003 ± 0.0002 | no | 1.00 | 0.0007 | 0.0000 | 0.0009 | 0.32 | 0.60 | -0.0006 | yes |
| `openml_wdbc` | model_type logistic_regression -> random_forest | -0.0061 ± 0.0033 | yes | 0.68 | 0.0091 | 0.0015 | 0.0059 | 0.25 | 0.13 | -0.0024 | no |
| `openml_wdbc` | model_type logistic_regression -> gradient_boosting | -0.0316 ± 0.0088 | yes | 0.59 | 0.0242 | 0.0007 | 0.0246 | 0.10 | 0.00 | -0.0159 | no |
| `openml_wdbc` | class_weight balanced -> null | 0.0000 ± 0.0002 | no | 1.00 | 0.0006 | 0.0000 | 0.0004 | 0.50 | – | – | – |
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0020 ± 0.0010 | no | 1.00 | 0.0027 | 0.0000 | 0.0025 | 0.24 | 0.30 | 0.0022 | yes |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0006 ± 0.0011 | no | 0.99 | 0.0030 | 0.0000 | 0.0023 | 0.43 | – | – | – |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0130 ± 0.0048 | yes | 0.88 | 0.0130 | 0.0035 | 0.0141 | 0.16 | 0.20 | 0.0120 | no |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0085 ± 0.0059 | yes | 0.81 | 0.0162 | 0.0026 | 0.0199 | 0.30 | 0.30 | 0.0056 | no |
| `openml_credit_approval` | class_weight balanced -> null | 0.0002 ± 0.0003 | no | 1.00 | 0.0008 | 0.0000 | 0.0008 | 0.42 | – | – | – |
| `openml_credit_g` | C 0.15 -> 0.075 | 0.0019 ± 0.0014 | no | 0.99 | 0.0038 | 0.0000 | 0.0040 | 0.30 | 0.30 | -0.0032 | yes |
| `openml_credit_g` | C 0.15 -> 0.3 | -0.0014 ± 0.0012 | no | 1.00 | 0.0032 | 0.0000 | 0.0042 | 0.33 | 0.33 | -0.0038 | no |
| `openml_credit_g` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0074 | no | 0.83 | 0.0203 | 0.0083 | 0.0161 | 0.44 | – | – | – |
| `openml_credit_g` | model_type logistic_regression -> gradient_boosting | -0.0150 ± 0.0101 | yes | 0.66 | 0.0277 | 0.0026 | 0.0262 | 0.29 | 0.27 | -0.0698 | no |
| `openml_credit_g` | class_weight balanced -> null | 0.0011 ± 0.0011 | no | 1.00 | 0.0031 | 0.0000 | 0.0037 | 0.36 | 0.37 | -0.0008 | yes |
| `openml_sonar` | C 0.15 -> 0.075 | 0.0062 ± 0.0041 | yes | 0.98 | 0.0113 | 0.0000 | 0.0117 | 0.29 | 0.40 | 0.0000 | yes |
| `openml_sonar` | C 0.15 -> 0.3 | -0.0087 ± 0.0047 | yes | 0.98 | 0.0128 | 0.0000 | 0.0098 | 0.25 | 0.27 | 0.0126 | yes |
| `openml_sonar` | model_type logistic_regression -> random_forest | 0.0569 ± 0.0163 | yes | 0.67 | 0.0447 | 0.0211 | 0.0581 | 0.10 | 0.10 | 0.1261 | no |
| `openml_sonar` | model_type logistic_regression -> gradient_boosting | -0.1041 ± 0.0352 | yes | 0.24 | 0.0964 | 0.0467 | 0.1051 | 0.14 | 0.13 | -0.0672 | no |
| `openml_sonar` | class_weight balanced -> null | 0.0008 ± 0.0014 | no | 1.00 | 0.0039 | 0.0000 | 0.0033 | 0.41 | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.075 | 0.0006 ± 0.0010 | no | 1.00 | 0.0027 | 0.0000 | 0.0037 | 0.42 | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.3 | -0.0004 ± 0.0007 | no | 1.00 | 0.0018 | 0.0000 | 0.0019 | 0.42 | – | – | – |
| `openml_blood_transfusion` | model_type logistic_regression -> random_forest | -0.0260 ± 0.0087 | yes | 0.91 | 0.0240 | 0.0060 | 0.0338 | 0.14 | 0.10 | -0.0366 | no |
| `openml_blood_transfusion` | model_type logistic_regression -> gradient_boosting | -0.0664 ± 0.0163 | yes | 0.76 | 0.0446 | 0.0042 | 0.0439 | 0.07 | 0.07 | -0.0562 | no |
| `openml_blood_transfusion` | class_weight balanced -> null | 0.0004 ± 0.0011 | no | 1.00 | 0.0030 | 0.0000 | 0.0017 | 0.45 | – | – | – |
| `openml_qsar_biodeg` | C 0.15 -> 0.075 | -0.0017 ± 0.0008 | no | 0.99 | 0.0023 | 0.0000 | 0.0021 | 0.23 | 0.17 | -0.0016 | no |
| `openml_qsar_biodeg` | C 0.15 -> 0.3 | 0.0010 ± 0.0007 | no | 0.99 | 0.0020 | 0.0000 | 0.0026 | 0.30 | 0.30 | 0.0004 | no |
| `openml_qsar_biodeg` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0055 | no | 0.68 | 0.0151 | 0.0042 | 0.0159 | 0.42 | – | – | – |
| `openml_qsar_biodeg` | model_type logistic_regression -> gradient_boosting | -0.0005 ± 0.0061 | no | 0.64 | 0.0166 | 0.0026 | 0.0147 | 0.49 | – | – | – |
| `openml_qsar_biodeg` | class_weight balanced -> null | 0.0005 ± 0.0005 | no | 1.00 | 0.0015 | 0.0000 | 0.0020 | 0.37 | – | – | – |
