# W2 — budget fields from worker runs (9 Nov 2026)

**AI-assisted (Claude, Mac-local overnight agent); engineering only.** Implements work item W2 of `proposals/SEQUENTIAL_POLICY_REVISION_20261104.md` §4.2 (branch `docs/seq-revision-04nov`), adopted by the author as R1-SEQ-BUDGET-FIELDS with the 9 Nov overnight start message (runbook `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §0.4 line A3, §5). Branch `mac-w2-budget-20261109` from `mac-int-20261107` (`a15300ca`). No sweep table, label, audit value or seed 7001–7010 file was read.

## Change

| Where | Before | After |
|---|---|---|
| `r1/c3/features.py` | `budget_frac_left = 1 − (b − 1)/W` (trial index) | `1 − worker_runs_used/W`, with `worker_runs_used` summed over the observed prefix rows by the new `row_worker_runs(row)` |
| `r1/c3/train/serialize.py` | budget line "… (W − (b − 1) worker runs left before this trial)" | the same text with the true worker runs left, from the prefix rows; `budget_line(b, W)` without a count (the synthetic exam, which has no ledger) keeps the old value |
| `serialize.ROW_FIELDS` | six fields | adds `worker_mode` (past rows only; needed to count runs) |

`row_worker_runs` is the rule `r1/c3/accounting.campaign_usage` already uses for H.6 accounting (harness `ComputeBudget` semantics): a row whose worker ran counts 1; `worker_mode == "control_plane"` (E1 skips and D25 inactive-key skips, `campaign._skipped_record`) and `worker_mode` ending in `_precheck` (precondition rejections) count 0; a KG verify adds 2 r re-runs. A row without `worker_mode` (older fixtures) counts 0 if it is a skip carrying a control record, else 1. A test checks the rule against `campaign_usage` on mixed rows. `accounting.py` itself is unchanged.

LLM calls left and proposal slots left are not shown in the prompt today, so nothing was added there (W2: "where shown").

## Identity on execute-all campaigns

On a campaign where every row ran the worker exactly once (no skips, no precheck rejections, no verify), `worker_runs_used = b − 1` for every trial, so the feature is bit-identical and the budget line byte-identical. `r1/tests/test_w2_budget_fields.py` checks this on five generated execute-all campaigns of W = 20 trials, with and without `worker_mode` on the rows, for the feature value (exact `==`), the budget line and the line inside the serialized prompt. Other tests: skips, precheck rejections and a verify follow the true count; the missing-`worker_mode` fallback; the accounting equivalence; the check script.

**Not shown tonight:** identity on the real sweep-1 tables (they hold label seeds that may not be read tonight). `r1/scripts/w2_execute_all_identity_check.py <root_trials.jsonl> … --runs-total W` does that check: it reads only `budget_index`, `decision`, `worker_mode` and `extra.control` of each row (no metric, delta, edit or label), refuses sealed paths, and exits 3 on any difference (W2: a difference is a STOP). If sweep 1 holds D25 inactive-key skips or precheck rejections, its worker-run count is not b − 1 on those campaigns and the check will STOP; that is a real difference between the two definitions, not a bug, and goes to the author.

## Existing test changed

`test_c3_featurizer_online.py::test_control_plane_skips_do_not_count_as_invalid`: its online fixture wrote the skip row with `worker_mode: "local"`, which the harness never does for a skip (it writes `"control_plane"`). With W2 the worker-run count would then differ between the online and replay paths. The fixture now sets `worker_mode: "control_plane"` on that row; the assertions are unchanged.

## Versions

`FEATURIZER_VERSION` (`c3_features/v2`) and `PROMPT_VERSION` (`trackp_prompt/v1`) are not bumped, so that execute-all tables and prompts stay byte-identical, including their version fields. On campaigns with skips or verify the values differ from the earlier code under the same version string. Whether to bump is in the question list.

## Tests

Relevant files (`test_c3_env`, `test_c3_features`, `test_c3_featurizer_online`, `test_c3_control*` except dry-run, `test_trackp_*`, new `test_w2_budget_fields`): failure set unchanged apart from new tests. Two failures exist at the base commit too and are unrelated: `test_trackp_exam_synthetic::test_committed_set_matches_its_hash_and_regenerates_byte_identically` and `test_trackp_soft_label_v2::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical`.

Review: pending.
