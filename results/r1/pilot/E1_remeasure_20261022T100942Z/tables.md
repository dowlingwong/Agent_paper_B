| Node | default m | bit-identical at fixed seed | σ_train | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all edits | mean P(wrong), material | regret share, material | campaign-seed decision wrong | sd_train/sd_joint, material | median s/run | D21 (proposed) | split policy (proposed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | 0.9097 | yes | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.24 | 0.23 | 1/3 | 0.23 | 1.0 | qualifies | `vary` |
| `openml_diabetes` | 0.8297 | yes | 0.0000 | 0.0359 | 0.0357 | 0.0028 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | 1.0 | more seeds needed | `vary` |

### Per-edit rows

| Node | Edit | Δ̂_J (± 2 se) | material | ϱ_joint | sd(Δ̂) joint | sd train | sd split | P(wrong) | flip rate | campaign Δ̂ | campaign wrong |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0020 ± 0.0010 | no | 1.00 | 0.0027 | 0.0000 | 0.0025 | 0.24 | 0.30 | 0.0022 | yes |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0006 ± 0.0011 | no | 0.99 | 0.0030 | 0.0000 | 0.0023 | 0.43 | – | – | – |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0123 ± 0.0047 | yes | 0.89 | 0.0129 | 0.0037 | 0.0144 | 0.17 | 0.23 | 0.0135 | no |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0082 ± 0.0059 | yes | 0.81 | 0.0162 | 0.0028 | 0.0205 | 0.31 | 0.37 | 0.0064 | no |
| `openml_credit_approval` | class_weight balanced -> null | 0.0002 ± 0.0003 | no | 1.00 | 0.0008 | 0.0000 | 0.0008 | 0.42 | – | – | – |
| `openml_diabetes` | C 0.15 -> 0.075 | 0.0005 ± 0.0008 | no | 1.00 | 0.0022 | 0.0000 | 0.0018 | 0.42 | – | – | – |
| `openml_diabetes` | C 0.15 -> 0.3 | -0.0000 ± 0.0006 | no | 1.00 | 0.0016 | 0.0000 | 0.0013 | 0.49 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> random_forest | 0.0029 ± 0.0088 | no | 0.74 | 0.0241 | 0.0048 | 0.0225 | 0.45 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> gradient_boosting | -0.0088 ± 0.0092 | no | 0.73 | 0.0253 | 0.0012 | 0.0276 | 0.36 | – | – | – |
| `openml_diabetes` | class_weight balanced -> null | 0.0010 ± 0.0010 | no | 1.00 | 0.0028 | 0.0000 | 0.0018 | 0.36 | – | – | – |
