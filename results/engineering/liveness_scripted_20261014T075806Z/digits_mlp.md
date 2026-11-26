# Liveness: digits_mlp — FAIL

ENGINEERING_ONLY (D28, revised criterion 2). Thresholds: keep after trial 1 ≥ 1; active-key novelty ≥ 0.5 of evaluated trials; invalid rate < 0.3.

| criterion | required | observed |
|---|---|---|
| keep_after_trial_1 | at least 1 keep with budget_index > 1 | 4 |
| active_novelty_fraction | >= 0.5 | 0.3500 (7/20, events) |
| invalid_rate | < 0.3 | 0.0000 |

Evaluated trials: 20 (equals incumbent 13, seen before 11).
Inactive-key rejections (separate count): 0.
Trials: 20. Failed criteria: active_novelty_fraction.

Ledgers:
- `results/r1/engineering/liveness_scripted_20261014T075806Z/ledgers/digits_mlp__s104/root_trials.jsonl`
- `results/r1/engineering/liveness_scripted_20261014T075806Z/ledgers/digits_mlp__s114/root_trials.jsonl`
