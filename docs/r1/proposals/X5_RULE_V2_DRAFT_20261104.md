# Draft — proposer-exam finalist rule `x5_rule_v2` (4 Nov 2026)

**Status.** AI-assisted draft (Claude, chat session) implementing PLAN §10 R1-MAIN-PROPOSER (a). It is not frozen and it governs nothing yet. Three steps are required, all before the B1 authorization (X.4):

1. The Track X agent writes `r1/exam/rules/x5_rule_v2.yaml` (with its `.sha256`) and the `r1/exam/analyze.py` change.
2. An independent agent reviews both.
3. The author commits a PLAN row **R1-EXAM-RULE-X5V2** carrying the rule's sha256. `runtime.author_gate` requires the sha to appear on a PLAN line containing `R1-EXAM-RULE`, and the B1 and B2 authorization notes bind `rule_sha256`.

**Why it is needed.** `x5_rule_v1` (sha256 `0665903b…`, not yet carried by any PLAN row) differs from the author's 3 Nov choice in three ways:
- it ranks finalists by pooled μ̂ over modes;
- it admits always-thinking models;
- it picks each finalist's B2 mode on the `openml_credit_approval` sensitivity node.

In addition, `analyze.b2_summary` ranks B2 rows by final Y regardless of mode. The author's choice requires the main proposer to be chosen on **thinking-off** performance among models that can run thinking off.

## Proposed rule (YAML)

```yaml
version: x5_rule/v2
supersedes: x5_rule/v1
purpose: main_proposer_selection_thinking_off   # PLAN R1-MAIN-PROPOSER (a)
ranking_quantity: pooled_audited_mean_proposal_increment
ranking_mode: off                                # mu_hat over thinking-off proposals only
eligibility:
  stage_a_pass: true
  d28_pass: true
  thinking_off_capable: true   # registry thinking_policy: mode in {off, on} with off_switch, or a non-thinking model; always_on excluded
finalists:
  top_by_mean: 4
  absent_family_extra: 1
  maximum: 5
  extra_selection: highest_mean_among_eligible_families_absent_from_top_four
  ties: registry_order
thinking_mode:
  primary: off
  b1_sensitivity:                 # descriptive only; never changes the B2 mode
    node: openml_credit_approval
    budget: 2048
  always_on_in_b1: skip           # (proposed) not eligible; the appendix reports them from Stage A. Alternative: run_descriptive
  b2_mode: off
selection:                        # X.7 (a)
  quantity: b2_final_audited_y
  mode: off
  ties: lower_gpu_hours
bootstrap:
  unit: node_instance_cluster
  paired: true
  resamples: 2000
  seed: 20261026
  alpha: 0.05
b2_instances:
  selection: author_decision_from_b1_variance
  gate: author_plan_row_and_authorization_note_required
scope: EXAM_ONLY_NOT_C3
```

## Required `analyze.py` changes (for the Track X agent)

- **`b1_summary`.**
  - Compute `mu_hat` from the observations with `mode == 'off'` only.
  - Mark a row ineligible when its registry entry cannot run thinking off.
  - Keep the thinking-on sensitivity rows as a separate descriptive field.
  - `b2_thinking_mode` is always `off`.
- **`choose_finalists`.** Rank only the eligible rows.
- **`b2_summary`.**
  - Rank only rows with `mode == 'off'` and `purpose == 'primary'`.
  - Raise an error if a primary B2 manifest has another mode.
  - Report thinking-on rows, if any exist, under a separate key.
- **Tests.** The rule loads only with its pinned sha. An always-on model never becomes a finalist. A thinking-on row with a higher Y never wins. Ties fall to lower GPU-h.

## Cost

B2 runs only thinking-off rows, so its GPU time does not exceed v1's. If always-on models skip B1 as proposed, B1 saves about 4 GPU-h per such model: about 240 proposals at the roughly 58 s per request that Stage A measured.

## Open for the author

- Whether always-thinking models skip B1 (proposed) or run descriptively for the appendix.
- Whether to keep the thinking-on sensitivity node. It is descriptive under v2 and costs one node per switchable model.
