# Liveness: openml_wdbc — PASS

ENGINEERING_ONLY (D28, revised criterion 2). Thresholds: keep after trial 1 ≥ 1; active-key novelty ≥ 0.5 of evaluated trials; invalid rate < 0.3.

| criterion | required | observed |
|---|---|---|
| keep_after_trial_1 | at least 1 keep with budget_index > 1 | 1 |
| active_novelty_fraction | >= 0.5 | 0.7500 (15/20, events) |
| invalid_rate | < 0.3 | 0.0000 |

Evaluated trials: 20 (equals incumbent 0, seen before 5).
Inactive-key rejections (separate count): 0.
Trials: 20. Failed criteria: none.

Ledgers:
- `/ceph/dwong/agent_paper_B/results/r1/engineering/liveness_llamacpp_20261027T122913Z/ledgers/openml_wdbc__s100/root_trials.jsonl`
- `/ceph/dwong/agent_paper_B/results/r1/engineering/liveness_llamacpp_20261027T122913Z/ledgers/openml_wdbc__s110/root_trials.jsonl`
