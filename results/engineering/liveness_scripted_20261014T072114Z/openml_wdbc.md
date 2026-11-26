# Liveness: openml_wdbc — FAIL

ENGINEERING_ONLY (D28). Thresholds: keep after trial 1 ≥ 1; metric-different fraction ≥ 0.5; invalid rate < 0.3.

| criterion | required | observed |
|---|---|---|
| keep_after_trial_1 | at least 1 keep with budget_index > 1 | 2 |
| metric_diff_fraction | >= 0.5 | 0.3889 (7/18) |
| invalid_rate | < 0.3 | 0.0000 |

Trials: 20. Failed criteria: metric_diff_fraction.

Ledgers:
- `/Users/wongdowling/Documents/agent_paper_B/results/r1/engineering/liveness_scripted_20261014T072114Z/ledgers/openml_wdbc__s100/root_trials.jsonl`
- `/Users/wongdowling/Documents/agent_paper_B/results/r1/engineering/liveness_scripted_20261014T072114Z/ledgers/openml_wdbc__s110/root_trials.jsonl`
