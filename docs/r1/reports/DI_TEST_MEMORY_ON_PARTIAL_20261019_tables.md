# Memory-on partial and memory-off DI tables — 19 Oct 2026

AI-assisted by Codex. PILOT, PARTIAL, not evidence. PARTIAL applies to the memory-on interrupted arm.

## Memory on — partial rerun-2 arm A


AI-assisted by Codex. PILOT, PARTIAL, not evidence.

Input revision: `d7a9dc3e3fd1fb8c2d035d06d959de4beff1aa4e`; 9999 draws; seed 20261019.

### Decisions changed (point-repetitions)

| Node | Promotion | Demotion | Unchanged |
|---|---:|---:|---:|
| openml_breast_w | 0 | 0 | 106 |
| openml_ionosphere | 0 | 0 | 106 |
| tabular_mlp | 18 | 8 | 82 |

### Distances and inference

| Group | k | Metric | Changed points | D_changed | D_null paired | D_unchanged | Excess null [95% CI] | Excess unchanged [95% CI] | p null | p unchanged | Holm p |
|---|---:|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| openml_breast_w | 1 | abs_metric | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 1 | key_tv | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 1 | signed_log_edit | 0 | NA | NA | 0.00627336 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 1 | active_novelty | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 1 | duplicate_fraction | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 1 | metric_identical | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | abs_metric | 0 | NA | NA | 1.01258e-05 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | key_tv | 0 | NA | NA | 0.0125786 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | signed_log_edit | 0 | NA | NA | 0.0262034 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | active_novelty | 0 | NA | NA | 0.0220126 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | duplicate_fraction | 0 | NA | NA | 0.0220126 | NA NA | NA NA | NA | NA | NA |
| openml_breast_w | 3 | metric_identical | 0 | NA | NA | 0.0125786 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | abs_metric | 0 | NA | NA | 0.00018984 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | key_tv | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | signed_log_edit | 0 | NA | NA | 0.00210513 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | active_novelty | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | duplicate_fraction | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | metric_identical | 0 | NA | NA | 0.00943396 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | abs_metric | 0 | NA | NA | 0.00032128 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | key_tv | 0 | NA | NA | 0.00628931 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | signed_log_edit | 0 | NA | NA | 0.0200046 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | active_novelty | 0 | NA | NA | 0.0345912 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | duplicate_fraction | 0 | NA | NA | 0.0345912 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | metric_identical | 0 | NA | NA | 0.00628931 | NA NA | NA NA | NA | NA | NA |
| tabular_mlp | 1 | abs_metric | 13 | 0.00231346 | 0.00108462 | 0.00054939 | 0.00122885 [0.000319434, 0.002375] | 0.00176407 [0.000438745, 0.00332095] | 0.0002 | 0.0018 | 0.0036 |
| tabular_mlp | 1 | key_tv | 13 | 0.538462 | 0.269231 | 0.109756 | 0.269231 [0.0625, 0.555556] | 0.428705 [0.184524, 0.722222] | 0.0005 | 0.0008 | NA |
| tabular_mlp | 1 | signed_log_edit | 13 | 0.864692 | 0.453989 | 0.157308 | 0.410703 [-0.0411433, 1.17852] | 0.707384 [0.0447743, 1.47126] | 0.0324 | 0.0058 | NA |
| tabular_mlp | 1 | active_novelty | 13 | 0.576923 | 0.115385 | 0.0365854 | 0.461538 [0.125, 0.762045] | 0.540338 [0.241776, 0.8055] | 0.0002 | 0.0001 | NA |
| tabular_mlp | 1 | duplicate_fraction | 13 | 0.576923 | 0.115385 | 0.0365854 | 0.461538 [0.125, 0.762045] | 0.540338 [0.241776, 0.8055] | 0.0002 | 0.0001 | NA |
| tabular_mlp | 1 | metric_identical | 13 | 0 | 0 | 0.0121951 | 0 [0, 0] | -0.0121951 [-0.0375, 0] | 1 | 1 | NA |
| tabular_mlp | 3 | abs_metric | 13 | 0.00167949 | 0.00129231 | 0.000270224 | 0.000387179 [-2.70833e-05, 0.00112963] | 0.00140926 [0.000594189, 0.00223392] | 0.0001 | 0.0002 | 0.0008 |
| tabular_mlp | 3 | key_tv | 13 | 0.384615 | 0.25641 | 0.0609756 | 0.128205 [0.0128205, 0.266667] | 0.32364 [0.177536, 0.49915] | 0.0001 | 0.0001 | NA |
| tabular_mlp | 3 | signed_log_edit | 13 | 0.555833 | 0.518193 | 0.139494 | 0.0376394 [-0.320714, 0.439443] | 0.416338 [0.155161, 0.746514] | 0.0103 | 0.0005 | NA |
| tabular_mlp | 3 | active_novelty | 13 | 0.371795 | 0.166667 | 0.0162602 | 0.205128 [0.0769231, 0.333333] | 0.355535 [0.207397, 0.472272] | 0.0001 | 0.0001 | NA |
| tabular_mlp | 3 | duplicate_fraction | 13 | 0.371795 | 0.166667 | 0.0162602 | 0.205128 [0.0769231, 0.333333] | 0.355535 [0.207397, 0.472272] | 0.0001 | 0.0001 | NA |
| tabular_mlp | 3 | metric_identical | 13 | 0.0128205 | 0.0128205 | 0.0121951 | 0 [0, 0] | 0.000625391 [-0.0116279, 0.0147992] | 0.7548 | 0.5663 | NA |
| pooled_value_eligible | 1 | abs_metric | 13 | 0.00231346 | 0.00108462 | 0.00054939 | 0.00122885 [0.000319434, 0.002375] | 0.00176407 [0.000438745, 0.00332095] | 0.0002 | 0.0018 | 0.0036 |
| pooled_value_eligible | 1 | key_tv | 13 | 0.538462 | 0.269231 | 0.109756 | 0.269231 [0.0625, 0.555556] | 0.428705 [0.184524, 0.722222] | 0.0005 | 0.0008 | NA |
| pooled_value_eligible | 1 | signed_log_edit | 13 | 0.864692 | 0.453989 | 0.157308 | 0.410703 [-0.0411433, 1.17852] | 0.707384 [0.0447743, 1.47126] | 0.0324 | 0.0058 | NA |
| pooled_value_eligible | 1 | active_novelty | 13 | 0.576923 | 0.115385 | 0.0365854 | 0.461538 [0.125, 0.762045] | 0.540338 [0.241776, 0.8055] | 0.0002 | 0.0001 | NA |
| pooled_value_eligible | 1 | duplicate_fraction | 13 | 0.576923 | 0.115385 | 0.0365854 | 0.461538 [0.125, 0.762045] | 0.540338 [0.241776, 0.8055] | 0.0002 | 0.0001 | NA |
| pooled_value_eligible | 1 | metric_identical | 13 | 0 | 0 | 0.0121951 | 0 [0, 0] | -0.0121951 [-0.0375, 0] | 1 | 1 | NA |
| pooled_value_eligible | 3 | abs_metric | 13 | 0.00167949 | 0.00129231 | 0.000270224 | 0.000387179 [-2.70833e-05, 0.00112963] | 0.00140926 [0.000594189, 0.00223392] | 0.0001 | 0.0002 | 0.0008 |
| pooled_value_eligible | 3 | key_tv | 13 | 0.384615 | 0.25641 | 0.0609756 | 0.128205 [0.0128205, 0.266667] | 0.32364 [0.177536, 0.49915] | 0.0001 | 0.0001 | NA |
| pooled_value_eligible | 3 | signed_log_edit | 13 | 0.555833 | 0.518193 | 0.139494 | 0.0376394 [-0.320714, 0.439443] | 0.416338 [0.155161, 0.746514] | 0.0103 | 0.0005 | NA |
| pooled_value_eligible | 3 | active_novelty | 13 | 0.371795 | 0.166667 | 0.0162602 | 0.205128 [0.0769231, 0.333333] | 0.355535 [0.207397, 0.472272] | 0.0001 | 0.0001 | NA |
| pooled_value_eligible | 3 | duplicate_fraction | 13 | 0.371795 | 0.166667 | 0.0162602 | 0.205128 [0.0769231, 0.333333] | 0.355535 [0.207397, 0.472272] | 0.0001 | 0.0001 | NA |
| pooled_value_eligible | 3 | metric_identical | 13 | 0.0128205 | 0.0128205 | 0.0121951 | 0 [0, 0] | 0.000625391 [-0.0116279, 0.0147992] | 0.7548 | 0.5663 | NA |

Holm family: 4 evaluable primary node/pool × horizon tests. NA is unavailable, not zero.

### Value residual (point means; cluster bootstrap)

| Group | Changed points | Changed instances | Audit difference | Immediate proxy | Budget correction | Residual | 95% CI | Valid draws |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| openml_breast_w | 0 | 0 | NA | NA | NA | NA | NA | NA |
| openml_ionosphere | 0 | 0 | NA | NA | NA | NA | NA | NA |
| tabular_mlp | 13 | 9 | -0.000254647 | 0.000827885 | 0.000139019 | -0.00122155 | [-0.00222152, -0.000257005] | 9999 |
| pooled_value_eligible | 13 | 9 | -0.000254647 | 0.000827885 | 0.000139019 | -0.00122155 | [-0.00222152, -0.000257005] | 9999 |

### record_shift

| group | changed | point_repetitions | mean |
| --- | --- | --- | --- |
| openml_breast_w | True | 0 | NA |
| openml_breast_w | False | 106 | 0 |
| openml_ionosphere | True | 0 | NA |
| openml_ionosphere | False | 106 | 0 |
| tabular_mlp | True | 26 | -0.000782692 |
| tabular_mlp | False | 82 | 0 |
| pooled_value_eligible | True | 26 | -0.000782692 |
| pooled_value_eligible | False | 82 | 0 |

### mechanism

| group | changed | point_repetitions | memory_differs | continue_repeat | continue_reverse | verify_repeat | verify_reverse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| openml_breast_w | True | 0 | NA | NA | NA | NA | NA |
| openml_breast_w | False | 106 | 0 | 0.462264 | 0 | 0.471698 | 0 |
| openml_ionosphere | True | 0 | NA | NA | NA | NA | NA |
| openml_ionosphere | False | 106 | 0 | 0.443396 | 0 | 0.443396 | 0 |
| tabular_mlp | True | 26 | 1 | 0.269231 | 0 | 0.0384615 | 0 |
| tabular_mlp | False | 82 | 0 | 0.195122 | 0 | 0.195122 | 0 |
| pooled_value_eligible | True | 26 | 1 | 0.269231 | 0 | 0.0384615 | 0 |
| pooled_value_eligible | False | 82 | 0 | 0.195122 | 0 | 0.195122 | 0 |

### Metric-identical fraction (equal branch weight)

| Node | k | Action | Fraction |
|---|---:|---|---:|
| openml_breast_w | 1 | continue | 0.669811 |
| openml_breast_w | 1 | verify | 0.669811 |
| openml_breast_w | 3 | continue | 0.616352 |
| openml_breast_w | 3 | verify | 0.616352 |
| openml_ionosphere | 1 | continue | 0.188679 |
| openml_ionosphere | 1 | verify | 0.179245 |
| openml_ionosphere | 3 | continue | 0.166667 |
| openml_ionosphere | 3 | verify | 0.166667 |
| tabular_mlp | 1 | continue | 0.0277778 |
| tabular_mlp | 1 | verify | 0.0185185 |
| tabular_mlp | 3 | continue | 0.0246914 |
| tabular_mlp | 3 | verify | 0.0308642 |

### Excluded whole points

- `openml_breast_w__s235 b004`: openml_breast_w__s235__b004__continue__r1, openml_breast_w__s235__b004__continue__r2, openml_breast_w__s235__b004__verify__r1, openml_breast_w__s235__b004__verify__r2
- `openml_ionosphere__s123 b008`: openml_ionosphere__s123__b008__continue__r1, openml_ionosphere__s123__b008__continue__r2, openml_ionosphere__s123__b008__verify__r2

### Decision audit

| Instance | Point | Rep | Direction | Verify mean delta |
|---|---:|---:|---|---:|
| openml_breast_w__s105 | 4 | 1 | unchanged | -0.000805 |
| openml_breast_w__s105 | 4 | 2 | unchanged | -0.000805 |
| openml_breast_w__s105 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s105 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s105 | 12 | 1 | unchanged | -0.000805 |
| openml_breast_w__s105 | 12 | 2 | unchanged | -0.000805 |
| openml_breast_w__s115 | 4 | 1 | unchanged | -0.000403 |
| openml_breast_w__s115 | 4 | 2 | unchanged | -0.000403 |
| openml_breast_w__s115 | 8 | 1 | unchanged | -0.000403 |
| openml_breast_w__s115 | 8 | 2 | unchanged | -0.000403 |
| openml_breast_w__s115 | 12 | 1 | unchanged | -0.000403 |
| openml_breast_w__s115 | 12 | 2 | unchanged | -0.000403 |
| openml_breast_w__s125 | 4 | 1 | unchanged | 0.000402 |
| openml_breast_w__s125 | 4 | 2 | unchanged | 0.000402 |
| openml_breast_w__s125 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s125 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s125 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s125 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s135 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s135 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s135 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s135 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s135 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s135 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s145 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s145 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s145 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s145 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s145 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s145 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s155 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s155 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s155 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s155 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s155 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s155 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s165 | 4 | 1 | unchanged | -0.000402 |
| openml_breast_w__s165 | 4 | 2 | unchanged | -0.000402 |
| openml_breast_w__s165 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s165 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s165 | 12 | 1 | unchanged | -0.000402 |
| openml_breast_w__s165 | 12 | 2 | unchanged | -0.000402 |
| openml_breast_w__s175 | 4 | 1 | unchanged | -0.002415 |
| openml_breast_w__s175 | 4 | 2 | unchanged | -0.002415 |
| openml_breast_w__s175 | 8 | 1 | unchanged | -0.002415 |
| openml_breast_w__s175 | 8 | 2 | unchanged | -0.002415 |
| openml_breast_w__s175 | 12 | 1 | unchanged | -0.005233 |
| openml_breast_w__s175 | 12 | 2 | unchanged | -0.005233 |
| openml_breast_w__s185 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s185 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s185 | 8 | 1 | unchanged | -0.000805 |
| openml_breast_w__s185 | 8 | 2 | unchanged | -0.000805 |
| openml_breast_w__s185 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s185 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s195 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s195 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s195 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s195 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s195 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s195 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s205 | 4 | 1 | unchanged | 0.000403 |
| openml_breast_w__s205 | 4 | 2 | unchanged | 0.000403 |
| openml_breast_w__s205 | 8 | 1 | unchanged | -0.000403 |
| openml_breast_w__s205 | 8 | 2 | unchanged | -0.000403 |
| openml_breast_w__s205 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s205 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s215 | 4 | 1 | unchanged | -0.000403 |
| openml_breast_w__s215 | 4 | 2 | unchanged | -0.000403 |
| openml_breast_w__s215 | 8 | 1 | unchanged | -0.000403 |
| openml_breast_w__s215 | 8 | 2 | unchanged | -0.000403 |
| openml_breast_w__s215 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s215 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s225 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s225 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s225 | 8 | 1 | unchanged | -0.000805 |
| openml_breast_w__s225 | 8 | 2 | unchanged | -0.000805 |
| openml_breast_w__s225 | 12 | 1 | unchanged | -0.000805 |
| openml_breast_w__s225 | 12 | 2 | unchanged | -0.000805 |
| openml_breast_w__s235 | 8 | 1 | unchanged | -0.000805 |
| openml_breast_w__s235 | 8 | 2 | unchanged | -0.000805 |
| openml_breast_w__s235 | 12 | 1 | unchanged | -0.000805 |
| openml_breast_w__s235 | 12 | 2 | unchanged | -0.000805 |
| openml_breast_w__s245 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s245 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s245 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s245 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s245 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s245 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s255 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s255 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s255 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s255 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s255 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s255 | 12 | 2 | unchanged | 0 |
| openml_breast_w__s265 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s265 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s265 | 8 | 1 | unchanged | -0.000403 |
| openml_breast_w__s265 | 8 | 2 | unchanged | -0.000403 |
| openml_breast_w__s265 | 12 | 1 | unchanged | -0.000403 |
| openml_breast_w__s265 | 12 | 2 | unchanged | -0.000403 |
| openml_breast_w__s275 | 4 | 1 | unchanged | 0 |
| openml_breast_w__s275 | 4 | 2 | unchanged | 0 |
| openml_breast_w__s275 | 8 | 1 | unchanged | 0 |
| openml_breast_w__s275 | 8 | 2 | unchanged | 0 |
| openml_breast_w__s275 | 12 | 1 | unchanged | 0 |
| openml_breast_w__s275 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s103 | 4 | 1 | unchanged | 0.003096 |
| openml_ionosphere__s103 | 4 | 2 | unchanged | 0.003096 |
| openml_ionosphere__s103 | 8 | 1 | unchanged | -0.010835 |
| openml_ionosphere__s103 | 8 | 2 | unchanged | -0.010835 |
| openml_ionosphere__s103 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s103 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s113 | 4 | 1 | unchanged | -0.001548 |
| openml_ionosphere__s113 | 4 | 2 | unchanged | -0.001548 |
| openml_ionosphere__s113 | 8 | 1 | unchanged | -0.001548 |
| openml_ionosphere__s113 | 8 | 2 | unchanged | -0.001548 |
| openml_ionosphere__s113 | 12 | 1 | unchanged | -0.001548 |
| openml_ionosphere__s113 | 12 | 2 | unchanged | -0.001548 |
| openml_ionosphere__s123 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s123 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s123 | 12 | 1 | unchanged | -0.029412 |
| openml_ionosphere__s123 | 12 | 2 | unchanged | -0.029412 |
| openml_ionosphere__s133 | 4 | 1 | unchanged | -0.001548 |
| openml_ionosphere__s133 | 4 | 2 | unchanged | -0.001548 |
| openml_ionosphere__s133 | 8 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s133 | 8 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s133 | 12 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s133 | 12 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s143 | 4 | 1 | unchanged | -0.004644 |
| openml_ionosphere__s143 | 4 | 2 | unchanged | -0.004644 |
| openml_ionosphere__s143 | 8 | 1 | unchanged | -0.004644 |
| openml_ionosphere__s143 | 8 | 2 | unchanged | -0.004644 |
| openml_ionosphere__s143 | 12 | 1 | unchanged | -0.004644 |
| openml_ionosphere__s143 | 12 | 2 | unchanged | -0.004644 |
| openml_ionosphere__s153 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s153 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s153 | 8 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s153 | 8 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s153 | 12 | 1 | unchanged | -0.00774 |
| openml_ionosphere__s153 | 12 | 2 | unchanged | -0.00774 |
| openml_ionosphere__s163 | 4 | 1 | unchanged | -0.006192 |
| openml_ionosphere__s163 | 4 | 2 | unchanged | -0.006192 |
| openml_ionosphere__s163 | 8 | 1 | unchanged | -0.006192 |
| openml_ionosphere__s163 | 8 | 2 | unchanged | -0.006192 |
| openml_ionosphere__s163 | 12 | 1 | unchanged | -0.006192 |
| openml_ionosphere__s163 | 12 | 2 | unchanged | -0.006192 |
| openml_ionosphere__s173 | 4 | 1 | unchanged | 0.001548 |
| openml_ionosphere__s173 | 4 | 2 | unchanged | 0.001548 |
| openml_ionosphere__s173 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s173 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s173 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s173 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s183 | 4 | 1 | unchanged | -0.012384 |
| openml_ionosphere__s183 | 4 | 2 | unchanged | -0.012384 |
| openml_ionosphere__s183 | 8 | 1 | unchanged | -0.012384 |
| openml_ionosphere__s183 | 8 | 2 | unchanged | -0.012384 |
| openml_ionosphere__s183 | 12 | 1 | unchanged | -0.012384 |
| openml_ionosphere__s183 | 12 | 2 | unchanged | -0.012384 |
| openml_ionosphere__s193 | 4 | 1 | unchanged | -0.049536 |
| openml_ionosphere__s193 | 4 | 2 | unchanged | -0.049536 |
| openml_ionosphere__s193 | 8 | 1 | unchanged | -0.049536 |
| openml_ionosphere__s193 | 8 | 2 | unchanged | -0.049536 |
| openml_ionosphere__s193 | 12 | 1 | unchanged | -0.049536 |
| openml_ionosphere__s193 | 12 | 2 | unchanged | -0.049536 |
| openml_ionosphere__s203 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s203 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s203 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s203 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s203 | 12 | 1 | unchanged | -0.013932 |
| openml_ionosphere__s203 | 12 | 2 | unchanged | -0.013932 |
| openml_ionosphere__s213 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s213 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s213 | 8 | 1 | unchanged | -0.018576 |
| openml_ionosphere__s213 | 8 | 2 | unchanged | -0.018576 |
| openml_ionosphere__s213 | 12 | 1 | unchanged | -0.018576 |
| openml_ionosphere__s213 | 12 | 2 | unchanged | -0.018576 |
| openml_ionosphere__s223 | 4 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s223 | 4 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s223 | 8 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s223 | 8 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s223 | 12 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s223 | 12 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s233 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s233 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s233 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s233 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s233 | 12 | 1 | unchanged | -0.003096 |
| openml_ionosphere__s233 | 12 | 2 | unchanged | -0.003096 |
| openml_ionosphere__s243 | 4 | 1 | unchanged | -0.029412 |
| openml_ionosphere__s243 | 4 | 2 | unchanged | -0.029412 |
| openml_ionosphere__s243 | 8 | 1 | unchanged | -0.03096 |
| openml_ionosphere__s243 | 8 | 2 | unchanged | -0.03096 |
| openml_ionosphere__s243 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s243 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s253 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s253 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s253 | 8 | 1 | unchanged | -0.009288 |
| openml_ionosphere__s253 | 8 | 2 | unchanged | -0.009288 |
| openml_ionosphere__s253 | 12 | 1 | unchanged | -0.010836 |
| openml_ionosphere__s253 | 12 | 2 | unchanged | -0.010836 |
| openml_ionosphere__s263 | 4 | 1 | unchanged | 0.004644 |
| openml_ionosphere__s263 | 4 | 2 | unchanged | 0.004644 |
| openml_ionosphere__s263 | 8 | 1 | unchanged | -0.003096 |
| openml_ionosphere__s263 | 8 | 2 | unchanged | -0.003096 |
| openml_ionosphere__s263 | 12 | 1 | unchanged | -0.003096 |
| openml_ionosphere__s263 | 12 | 2 | unchanged | -0.003096 |
| openml_ionosphere__s273 | 4 | 1 | unchanged | -0.02322 |
| openml_ionosphere__s273 | 4 | 2 | unchanged | -0.02322 |
| openml_ionosphere__s273 | 8 | 1 | unchanged | -0.02322 |
| openml_ionosphere__s273 | 8 | 2 | unchanged | -0.02322 |
| openml_ionosphere__s273 | 12 | 1 | unchanged | -0.02322 |
| openml_ionosphere__s273 | 12 | 2 | unchanged | -0.02322 |
| tabular_mlp__s102 | 4 | 1 | unchanged | 6.25e-05 |
| tabular_mlp__s102 | 4 | 2 | unchanged | 6.25e-05 |
| tabular_mlp__s102 | 8 | 1 | unchanged | -0.00205 |
| tabular_mlp__s102 | 8 | 2 | unchanged | -0.00205 |
| tabular_mlp__s102 | 12 | 1 | promotion | 0.0011875 |
| tabular_mlp__s102 | 12 | 2 | promotion | 0.0011875 |
| tabular_mlp__s112 | 4 | 1 | unchanged | -0.0058125 |
| tabular_mlp__s112 | 4 | 2 | unchanged | -0.0058125 |
| tabular_mlp__s112 | 8 | 1 | promotion | 0.0005625 |
| tabular_mlp__s112 | 8 | 2 | promotion | 0.0005625 |
| tabular_mlp__s112 | 12 | 1 | promotion | 0.0004 |
| tabular_mlp__s112 | 12 | 2 | promotion | 0.0004 |
| tabular_mlp__s122 | 4 | 1 | unchanged | 0.0024375 |
| tabular_mlp__s122 | 4 | 2 | unchanged | 0.0024375 |
| tabular_mlp__s122 | 8 | 1 | unchanged | -0.0194625 |
| tabular_mlp__s122 | 8 | 2 | unchanged | -0.0194625 |
| tabular_mlp__s122 | 12 | 1 | demotion | -0.000125 |
| tabular_mlp__s122 | 12 | 2 | demotion | -0.000125 |
| tabular_mlp__s132 | 4 | 1 | unchanged | -0.0038625 |
| tabular_mlp__s132 | 4 | 2 | unchanged | -0.0038625 |
| tabular_mlp__s132 | 8 | 1 | promotion | 5.55112e-17 |
| tabular_mlp__s132 | 8 | 2 | promotion | 5.55112e-17 |
| tabular_mlp__s132 | 12 | 1 | unchanged | -0.0007625 |
| tabular_mlp__s132 | 12 | 2 | unchanged | -0.0007625 |
| tabular_mlp__s142 | 4 | 1 | unchanged | -0.0046 |
| tabular_mlp__s142 | 4 | 2 | unchanged | -0.0046 |
| tabular_mlp__s142 | 8 | 1 | unchanged | -0.00225 |
| tabular_mlp__s142 | 8 | 2 | unchanged | -0.00225 |
| tabular_mlp__s142 | 12 | 1 | unchanged | -0.0052875 |
| tabular_mlp__s142 | 12 | 2 | unchanged | -0.0052875 |
| tabular_mlp__s152 | 4 | 1 | unchanged | -0.0059625 |
| tabular_mlp__s152 | 4 | 2 | unchanged | -0.0059625 |
| tabular_mlp__s152 | 8 | 1 | promotion | 0.0015125 |
| tabular_mlp__s152 | 8 | 2 | promotion | 0.0015125 |
| tabular_mlp__s152 | 12 | 1 | promotion | 2.5e-05 |
| tabular_mlp__s152 | 12 | 2 | promotion | 2.5e-05 |
| tabular_mlp__s162 | 4 | 1 | unchanged | -0.0010875 |
| tabular_mlp__s162 | 4 | 2 | unchanged | -0.0010875 |
| tabular_mlp__s162 | 8 | 1 | unchanged | -0.0036625 |
| tabular_mlp__s162 | 8 | 2 | unchanged | -0.0036625 |
| tabular_mlp__s162 | 12 | 1 | unchanged | -0.037275 |
| tabular_mlp__s162 | 12 | 2 | unchanged | -0.037275 |
| tabular_mlp__s172 | 4 | 1 | unchanged | -0.002225 |
| tabular_mlp__s172 | 4 | 2 | unchanged | -0.002225 |
| tabular_mlp__s172 | 8 | 1 | unchanged | -0.0035 |
| tabular_mlp__s172 | 8 | 2 | unchanged | -0.0035 |
| tabular_mlp__s172 | 12 | 1 | unchanged | -0.00205 |
| tabular_mlp__s172 | 12 | 2 | unchanged | -0.00205 |
| tabular_mlp__s182 | 4 | 1 | demotion | -0.0005625 |
| tabular_mlp__s182 | 4 | 2 | demotion | -0.0005625 |
| tabular_mlp__s182 | 8 | 1 | promotion | 0.000125 |
| tabular_mlp__s182 | 8 | 2 | promotion | 0.000125 |
| tabular_mlp__s182 | 12 | 1 | unchanged | -0.0038625 |
| tabular_mlp__s182 | 12 | 2 | unchanged | -0.0038625 |
| tabular_mlp__s192 | 4 | 1 | unchanged | 0.001075 |
| tabular_mlp__s192 | 4 | 2 | unchanged | 0.001075 |
| tabular_mlp__s192 | 8 | 1 | unchanged | -0.000175 |
| tabular_mlp__s192 | 8 | 2 | unchanged | -0.000175 |
| tabular_mlp__s192 | 12 | 1 | unchanged | -0.001925 |
| tabular_mlp__s192 | 12 | 2 | unchanged | -0.001925 |
| tabular_mlp__s202 | 4 | 1 | demotion | -0.0034 |
| tabular_mlp__s202 | 4 | 2 | demotion | -0.0034 |
| tabular_mlp__s202 | 8 | 1 | unchanged | 0 |
| tabular_mlp__s202 | 8 | 2 | unchanged | 0 |
| tabular_mlp__s202 | 12 | 1 | unchanged | -0.0010625 |
| tabular_mlp__s202 | 12 | 2 | unchanged | -0.0010625 |
| tabular_mlp__s212 | 4 | 1 | unchanged | -0.0040875 |
| tabular_mlp__s212 | 4 | 2 | unchanged | -0.0040875 |
| tabular_mlp__s212 | 8 | 1 | unchanged | -0.00355 |
| tabular_mlp__s212 | 8 | 2 | unchanged | -0.00355 |
| tabular_mlp__s212 | 12 | 1 | unchanged | -0.0021875 |
| tabular_mlp__s212 | 12 | 2 | unchanged | -0.0021875 |
| tabular_mlp__s222 | 4 | 1 | unchanged | -0.0043875 |
| tabular_mlp__s222 | 4 | 2 | unchanged | -0.0043875 |
| tabular_mlp__s222 | 8 | 1 | unchanged | -0.0136125 |
| tabular_mlp__s222 | 8 | 2 | unchanged | -0.0136125 |
| tabular_mlp__s222 | 12 | 1 | unchanged | -0.01575 |
| tabular_mlp__s222 | 12 | 2 | unchanged | -0.01575 |
| tabular_mlp__s232 | 4 | 1 | demotion | -0.0027125 |
| tabular_mlp__s232 | 4 | 2 | demotion | -0.0027125 |
| tabular_mlp__s232 | 8 | 1 | unchanged | 7.5e-05 |
| tabular_mlp__s232 | 8 | 2 | unchanged | 7.5e-05 |
| tabular_mlp__s232 | 12 | 1 | unchanged | -0.00295 |
| tabular_mlp__s232 | 12 | 2 | unchanged | -0.00295 |
| tabular_mlp__s242 | 4 | 1 | unchanged | -0.004625 |
| tabular_mlp__s242 | 4 | 2 | unchanged | -0.004625 |
| tabular_mlp__s242 | 8 | 1 | unchanged | -2.5e-05 |
| tabular_mlp__s242 | 8 | 2 | unchanged | -2.5e-05 |
| tabular_mlp__s242 | 12 | 1 | unchanged | -0.0034 |
| tabular_mlp__s242 | 12 | 2 | unchanged | -0.0034 |
| tabular_mlp__s252 | 4 | 1 | unchanged | -0.0019375 |
| tabular_mlp__s252 | 4 | 2 | unchanged | -0.0019375 |
| tabular_mlp__s252 | 8 | 1 | promotion | 1.25e-05 |
| tabular_mlp__s252 | 8 | 2 | promotion | 1.25e-05 |
| tabular_mlp__s252 | 12 | 1 | promotion | 0.0001375 |
| tabular_mlp__s252 | 12 | 2 | promotion | 0.0001375 |
| tabular_mlp__s262 | 4 | 1 | unchanged | 0.005 |
| tabular_mlp__s262 | 4 | 2 | unchanged | 0.005 |
| tabular_mlp__s262 | 8 | 1 | unchanged | -0.0011375 |
| tabular_mlp__s262 | 8 | 2 | unchanged | -0.0011375 |
| tabular_mlp__s262 | 12 | 1 | unchanged | 0.0024875 |
| tabular_mlp__s262 | 12 | 2 | unchanged | 0.0024875 |
| tabular_mlp__s272 | 4 | 1 | unchanged | 0.0058125 |
| tabular_mlp__s272 | 4 | 2 | unchanged | 0.0058125 |
| tabular_mlp__s272 | 8 | 1 | unchanged | -0.001475 |
| tabular_mlp__s272 | 8 | 2 | unchanged | -0.001475 |
| tabular_mlp__s272 | 12 | 1 | unchanged | -0.00035 |
| tabular_mlp__s272 | 12 | 2 | unchanged | -0.00035 |

Verdict: **violated in value terms**.
## Memory off — DT4 re-analysis


AI-assisted by Codex. PILOT, PARTIAL, not evidence.

Input revision: `d7a9dc3e3fd1fb8c2d035d06d959de4beff1aa4e`; 9999 draws; seed 20261019.

### Decisions changed (point-repetitions)

| Node | Promotion | Demotion | Unchanged |
|---|---:|---:|---:|
| digits_mlp | 12 | 0 | 24 |
| openml_ionosphere | 0 | 0 | 36 |

### Distances and inference

| Group | k | Metric | Changed points | D_changed | D_null paired | D_unchanged | Excess null [95% CI] | Excess unchanged [95% CI] | p null | p unchanged | Holm p |
|---|---:|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| digits_mlp | 1 | abs_metric | 6 | 0.0060355 | 0.0046425 | 0.00197308 | 0.001393 [-0.00185667, 0.00348213] | 0.00406242 [0.00126086, 0.00689974] | 0.1209 | 0.0037 | 0.4796 |
| digits_mlp | 1 | key_tv | 6 | 0.583333 | 0.583333 | 0.416667 | 0 [-0.666667, 0.4] | 0.166667 [-0.21875, 0.396104] | 0.8465 | 0.2917 | NA |
| digits_mlp | 1 | signed_log_edit | 6 | 0 | 0 | 0 | 0 [0, 0] | 0 [0, 0] | 1 | 1 | NA |
| digits_mlp | 1 | active_novelty | 6 | 0.916667 | 0.0833333 | 0.0416667 | 0.833333 [0.333333, 1] | 0.875 [0.623077, 1] | 0.0011 | 0.0001 | NA |
| digits_mlp | 1 | duplicate_fraction | 6 | 0.916667 | 0.0833333 | 0.0416667 | 0.833333 [0.333333, 1] | 0.875 [0.623077, 1] | 0.0011 | 0.0001 | NA |
| digits_mlp | 1 | metric_identical | 6 | 0.25 | 0.25 | 0.208333 | 0 [0, 0] | 0.0416667 [-0.225, 0.392857] | 1 | 0.5364 | NA |
| digits_mlp | 3 | abs_metric | 6 | 0.0044105 | 0.00332711 | 0.00127667 | 0.00108339 [-0.00185722, 0.00336617] | 0.00313383 [7.72639e-05, 0.0062521] | 0.1199 | 0.0076 | 0.4796 |
| digits_mlp | 3 | key_tv | 6 | 0.194444 | 0.25 | 0.25 | -0.0555556 [-0.222222, 0] | -0.0555556 [-0.189744, 0.110256] | 0.5556 | 0.8341 | NA |
| digits_mlp | 3 | signed_log_edit | 6 | 0 | 0 | 0 | 0 [0, 0] | 0 [0, 0] | 1 | 1 | NA |
| digits_mlp | 3 | active_novelty | 6 | 0.611111 | 0.222222 | 0.138889 | 0.388889 [-0.111111, 0.619048] | 0.472222 [0.215686, 0.663151] | 0.0115 | 0.0007 | NA |
| digits_mlp | 3 | duplicate_fraction | 6 | 0.611111 | 0.222222 | 0.138889 | 0.388889 [-0.111111, 0.619048] | 0.472222 [0.215686, 0.663151] | 0.0115 | 0.0007 | NA |
| digits_mlp | 3 | metric_identical | 6 | 0.194444 | 0.194444 | 0.125 | 0 [0, 0] | 0.0694444 [-0.05, 0.395833] | 1 | 0.3025 | NA |
| openml_ionosphere | 1 | abs_metric | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | key_tv | 0 | NA | NA | 0.194444 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | signed_log_edit | 0 | NA | NA | 0.0691553 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | active_novelty | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | duplicate_fraction | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 1 | metric_identical | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | abs_metric | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | key_tv | 0 | NA | NA | 0.138889 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | signed_log_edit | 0 | NA | NA | 0.0528149 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | active_novelty | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | duplicate_fraction | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| openml_ionosphere | 3 | metric_identical | 0 | NA | NA | 0 | NA NA | NA NA | NA | NA | NA |
| pooled_value_eligible | 1 | abs_metric | 6 | 0.0060355 | 0.0046425 | 0.00197308 | 0.001393 [-0.00185667, 0.00348213] | 0.00406242 [0.00126086, 0.00689974] | 0.1209 | 0.0037 | 0.4796 |
| pooled_value_eligible | 1 | key_tv | 6 | 0.583333 | 0.583333 | 0.416667 | 0 [-0.666667, 0.4] | 0.166667 [-0.21875, 0.396104] | 0.8465 | 0.2917 | NA |
| pooled_value_eligible | 1 | signed_log_edit | 6 | 0 | 0 | 0 | 0 [0, 0] | 0 [0, 0] | 1 | 1 | NA |
| pooled_value_eligible | 1 | active_novelty | 6 | 0.916667 | 0.0833333 | 0.0416667 | 0.833333 [0.333333, 1] | 0.875 [0.623077, 1] | 0.0011 | 0.0001 | NA |
| pooled_value_eligible | 1 | duplicate_fraction | 6 | 0.916667 | 0.0833333 | 0.0416667 | 0.833333 [0.333333, 1] | 0.875 [0.623077, 1] | 0.0011 | 0.0001 | NA |
| pooled_value_eligible | 1 | metric_identical | 6 | 0.25 | 0.25 | 0.208333 | 0 [0, 0] | 0.0416667 [-0.225, 0.392857] | 1 | 0.5364 | NA |
| pooled_value_eligible | 3 | abs_metric | 6 | 0.0044105 | 0.00332711 | 0.00127667 | 0.00108339 [-0.00185722, 0.00336617] | 0.00313383 [7.72639e-05, 0.0062521] | 0.1199 | 0.0076 | 0.4796 |
| pooled_value_eligible | 3 | key_tv | 6 | 0.194444 | 0.25 | 0.25 | -0.0555556 [-0.222222, 0] | -0.0555556 [-0.189744, 0.110256] | 0.5556 | 0.8341 | NA |
| pooled_value_eligible | 3 | signed_log_edit | 6 | 0 | 0 | 0 | 0 [0, 0] | 0 [0, 0] | 1 | 1 | NA |
| pooled_value_eligible | 3 | active_novelty | 6 | 0.611111 | 0.222222 | 0.138889 | 0.388889 [-0.111111, 0.619048] | 0.472222 [0.215686, 0.663151] | 0.0115 | 0.0007 | NA |
| pooled_value_eligible | 3 | duplicate_fraction | 6 | 0.611111 | 0.222222 | 0.138889 | 0.388889 [-0.111111, 0.619048] | 0.472222 [0.215686, 0.663151] | 0.0115 | 0.0007 | NA |
| pooled_value_eligible | 3 | metric_identical | 6 | 0.194444 | 0.194444 | 0.125 | 0 [0, 0] | 0.0694444 [-0.05, 0.395833] | 1 | 0.3025 | NA |

Holm family: 4 evaluable primary node/pool × horizon tests. NA is unavailable, not zero.

### Value residual (point means; cluster bootstrap)

| Group | Changed points | Changed instances | Audit difference | Immediate proxy | Budget correction | Residual | 95% CI | Valid draws |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| digits_mlp | 6 | 4 | 0.00282425 | 0.00232142 | -7.73611e-06 | 0.000510569 | [-0.00258821, 0.0041781] | 9987 |
| openml_ionosphere | 0 | 0 | NA | NA | NA | NA | NA | NA |
| pooled_value_eligible | 6 | 4 | 0.00282425 | 0.00232142 | -7.73611e-06 | 0.000510569 | [-0.00258821, 0.0041781] | 9987 |

### record_shift

| group | changed | point_repetitions | mean |
| --- | --- | --- | --- |
| digits_mlp | True | 12 | -0.005107 |
| digits_mlp | False | 24 | 0 |
| openml_ionosphere | True | 0 | NA |
| openml_ionosphere | False | 36 | 0 |
| pooled_value_eligible | True | 12 | -0.005107 |
| pooled_value_eligible | False | 24 | 0 |

### mechanism

| group | changed | point_repetitions | memory_differs | continue_repeat | continue_reverse | verify_repeat | verify_reverse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| digits_mlp | True | 12 | 0 | 0.5 | 0 | 0 | 0 |
| digits_mlp | False | 24 | 0 | 0.541667 | 0 | 0.458333 | 0 |
| openml_ionosphere | True | 0 | NA | NA | NA | NA | NA |
| openml_ionosphere | False | 36 | 0 | 0.527778 | 0 | 0.555556 | 0 |
| pooled_value_eligible | True | 12 | 0 | 0.5 | 0 | 0 | 0 |
| pooled_value_eligible | False | 24 | 0 | 0.541667 | 0 | 0.458333 | 0 |

### Metric-identical fraction (equal branch weight)

| Node | k | Action | Fraction |
|---|---:|---|---:|
| digits_mlp | 1 | continue | 0.25 |
| digits_mlp | 1 | verify | 0.25 |
| digits_mlp | 3 | continue | 0.203704 |
| digits_mlp | 3 | verify | 0.166667 |
| openml_ionosphere | 1 | continue | 1 |
| openml_ionosphere | 1 | verify | 1 |
| openml_ionosphere | 3 | continue | 1 |
| openml_ionosphere | 3 | verify | 1 |

### Excluded whole points

None.

### Decision audit

| Instance | Point | Rep | Direction | Verify mean delta |
|---|---:|---:|---|---:|
| digits_mlp__s104 | 4 | 1 | unchanged | -0.0013925 |
| digits_mlp__s104 | 4 | 2 | unchanged | -0.0013925 |
| digits_mlp__s104 | 8 | 1 | promotion | 0.002786 |
| digits_mlp__s104 | 8 | 2 | promotion | 0.002786 |
| digits_mlp__s104 | 12 | 1 | promotion | 0.0027855 |
| digits_mlp__s104 | 12 | 2 | promotion | 0.0027855 |
| digits_mlp__s114 | 4 | 1 | unchanged | 0.011142 |
| digits_mlp__s114 | 4 | 2 | unchanged | 0.011142 |
| digits_mlp__s114 | 8 | 1 | promotion | 0.0027855 |
| digits_mlp__s114 | 8 | 2 | promotion | 0.0027855 |
| digits_mlp__s114 | 12 | 1 | unchanged | -0.0027855 |
| digits_mlp__s114 | 12 | 2 | unchanged | -0.0027855 |
| digits_mlp__s124 | 4 | 1 | unchanged | -0.005571 |
| digits_mlp__s124 | 4 | 2 | unchanged | -0.005571 |
| digits_mlp__s124 | 8 | 1 | unchanged | 5e-07 |
| digits_mlp__s124 | 8 | 2 | unchanged | 5e-07 |
| digits_mlp__s124 | 12 | 1 | unchanged | -0.0013925 |
| digits_mlp__s124 | 12 | 2 | unchanged | -0.0013925 |
| digits_mlp__s134 | 4 | 1 | unchanged | -0.0013925 |
| digits_mlp__s134 | 4 | 2 | unchanged | -0.0013925 |
| digits_mlp__s134 | 8 | 1 | promotion | 0.002786 |
| digits_mlp__s134 | 8 | 2 | promotion | 0.002786 |
| digits_mlp__s134 | 12 | 1 | unchanged | -0.0013925 |
| digits_mlp__s134 | 12 | 2 | unchanged | -0.0013925 |
| digits_mlp__s144 | 4 | 1 | promotion | 0.001393 |
| digits_mlp__s144 | 4 | 2 | promotion | 0.001393 |
| digits_mlp__s144 | 8 | 1 | promotion | 0.0013925 |
| digits_mlp__s144 | 8 | 2 | promotion | 0.0013925 |
| digits_mlp__s144 | 12 | 1 | unchanged | -0.001393 |
| digits_mlp__s144 | 12 | 2 | unchanged | -0.001393 |
| digits_mlp__s154 | 4 | 1 | unchanged | -0.002786 |
| digits_mlp__s154 | 4 | 2 | unchanged | -0.002786 |
| digits_mlp__s154 | 8 | 1 | unchanged | -0.006964 |
| digits_mlp__s154 | 8 | 2 | unchanged | -0.006964 |
| digits_mlp__s154 | 12 | 1 | unchanged | -0.009749 |
| digits_mlp__s154 | 12 | 2 | unchanged | -0.009749 |
| openml_ionosphere__s103 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s103 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s103 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s103 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s103 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s103 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s113 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s113 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s113 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s113 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s113 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s113 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s123 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s123 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s123 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s123 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s123 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s123 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s133 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s133 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s133 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s133 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s133 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s133 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s143 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s143 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s143 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s143 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s143 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s143 | 12 | 2 | unchanged | 0 |
| openml_ionosphere__s153 | 4 | 1 | unchanged | 0 |
| openml_ionosphere__s153 | 4 | 2 | unchanged | 0 |
| openml_ionosphere__s153 | 8 | 1 | unchanged | 0 |
| openml_ionosphere__s153 | 8 | 2 | unchanged | 0 |
| openml_ionosphere__s153 | 12 | 1 | unchanged | 0 |
| openml_ionosphere__s153 | 12 | 2 | unchanged | 0 |

Verdict: **undetermined at this sample size**.
