# D28 repair rule — predeclared 27 October 2026

AI-assisted (OpenAI Codex). ENGINEERING_ONLY / PILOT; not evidence. Authority: PLAN R1-D28-REPAIR and `docs/r1/prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md`. This rule is declared before any repaired-node measurement.

For each of `openml_breast_w`, `openml_sonar`, `openml_blood_transfusion`, and `openml_wdbc`, set the tracked starting `config.yaml` fields `C: 0.001` and `max_iter: 100`; retain every other field. These are respectively the lower endpoints of the existing allowed ranges [0.001, 100.0] and [100, 3000]. The same fixed rule applies to all four; the four passing nodes are unchanged. Neither allowed values/ranges, edit space, manager prompt, schema, nor D21/D28 criteria change.

The pre-existing liveness diagnosis reported no positive increment in 20 proposals for each failed node, frequent inert iteration increases on already-converged models, and near-ceiling validation AUC for breast_w and wdbc. Starting at the lower allowed regularization parameter and iteration count is a simple outcome-blind fixed rule intended to leave room for valid edits; neither improvement nor convergence is assumed. Blood transfusion had nominal headroom but no helpful proposal; this rule is not tailored to its outcome. Re-measure D21 for all four before D28; preserve every failure and apply the author-approved reserve rule if required. No repaired-node run has informed this selection.

## Pre-measurement correction

Before any repaired-node measurement, code inspection of `r1/noise/e1_noise_floor.py:candidate_edits` showed that `C = 0.001` clips the prescribed C × 0.5 edit back to 0.001, making it a no-op. To preserve both standard C edits under the unchanged D21 procedure, amend the rule to **`C: 0.01` and `max_iter: 100`** for all four nodes; C × 0.5 = 0.005 and C × 2 = 0.02 lie within the same allowed range. The original rule is retained above as history. No repaired-node D21, D28 or other measurement has been run. The first attempted configuration-only validation was stopped before commit after this issue was identified; it did not produce experiment results.
