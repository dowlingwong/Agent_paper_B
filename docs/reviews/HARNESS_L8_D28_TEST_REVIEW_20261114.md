Reviewed base: a56c3a28972ee34435a9412144c956d8a5642bed (harness)

# Harness L8 template test against the D28 start configs — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 8.3 (the author's Q9 item 5, test only). Harness branch `r1-local-l8-d28-20261114` from `a3fedbb`; one commit `a56c3a2` touching only `tests/stage2/test_r1_l8.py`. The record lives in the paper repository because the harness has no review directory. One round by a freshly spawned independent reviewer agent (AI-assisted, Claude): **accepted** at harness `a56c3a2`.

Accepted commit (round 1, last): harness a56c3a28972ee34435a9412144c956d8a5642bed

Notes, not blocking: the new comment says D28 moved "these two pool nodes" although `6adf385` changed four (`openml_breast_w` and `openml_wdbc` are in `NEW_OPENML`, which no template test covers); `a56c3a2` is not `a3fedbb` and must never be B1's `AR_HARNESS_ROOT` — it is a test-only candidate for the next harness pin.

The round text is reproduced unchanged below.

---

# Independent review: L8 template test vs D28 start configs (Unit 8 item 3, round 1)

Reviewed commit: a56c3a28972ee34435a9412144c956d8a5642bed

- Branch: `r1-local-l8-d28-20261114` (harness worktree `/tmp/pb/wt/l8`, git dir `/tmp/pb/harness/.git`)
- Parent: `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (single commit on top of the B1 pin, as required)
- Scope: overnight runbook `69b3576b` §8 item 3; author Q9 item 5 ("L8 模板测试改为对照 D28 配置（仅测试）"); background: handoff `5cd32efc` §3 and §4 Q1, paper PLAN `7912b7ff` §10 row R1-D28-REPAIR (line 595).
- Reviewer: independent (did not write the change). Read-only; all runs and mutations in scratch copies under `/tmp/rev_u83` (removed afterwards).

## 1. The diff touches only tests

`git diff --stat a3fedbb a56c3a2`: `tests/stage2/test_r1_l8.py | 45 +++++++++++++++++++++++++++++++++++++++++++--` (1 file, 43+/2-). No node, config, source or fixture file changed. The blobs of `nodes/openml_template/config.yaml` (`d427188`) and of the four D28 nodes' `config.yaml` (`fd2c8e5`) are identical at `6adf385`, `a3fedbb` and `a56c3a2`, so the D28 values did not move. **OK.**

Change summary:
- `D28_START_CONFIGS = {"openml_sonar": {"C": "0.01", "max_iter": "100"}, "openml_blood_transfusion": {"C": "0.01", "max_iter": "100"}}`.
- `expected_config(node, template)`: returns the template unchanged for every other node; for a D28 node, replaces the `C:` and `max_iter:` lines (each must appear exactly once in the template, else AssertionError).
- `test_dataset_json_and_template_files`: unchanged for `benchmark.py`, `train.py`, `README.md` (byte equality with the template) and for `config.yaml` of non-D28 nodes; for the two D28 nodes `config.yaml` must equal `expected_config(...)` byte for byte.
- New `test_d28_start_configs_differ_from_the_template_only_in_the_recorded_keys`: D28 nodes are in `POOL_22OCT`; same line count as the template; the set of differing keys equals exactly the recorded keys; the recorded values are not all equal to the template's (guards against a vacuous exemption).

## 2. Recorded values match `6adf385`

`git show 6adf385` changes, for each of `openml_blood_transfusion`, `openml_breast_w`, `openml_sonar`, `openml_wdbc`, exactly `C: 0.15` → `C: 0.01` and `max_iter: 1000` → `max_iter: 100`; no other line. The test records `C: "0.01"`, `max_iter: "100"` for sonar and blood_transfusion, and rewrites lines as `f"{key}: {value}\n"`, which reproduces the `6adf385` bytes exactly (control run passes; the template has LF endings and a final newline, checked with `cat -A`). **OK.**

## 3. Mutation testing (scratch copy of the tip tree, `/tmp/rev_u83/mut`, recreated per case)

Ran `test_dataset_json_and_template_files` and the new D28 test after each mutation. Control (no mutation): 2 passed, 6 subtests passed.

| Mutation | Result |
|---|---|
| sonar `C: 0.01` → `0.02` (wrong value) | CAUGHT |
| blood `max_iter: 100` → `1000` (reverted to template) | CAUGHT |
| blood `C: 0.01` → `0.15` (reverted to template) | CAUGHT |
| sonar `C: 0.01 ` (trailing space) | CAUGHT |
| sonar `C: 1e-2` (numerically equal, textually different) | CAUGHT |
| sonar extra changed key `scaler: robust` | CAUGHT |
| blood extra changed key `class_weight: null` | CAUGHT |
| sonar extra appended line `tol: 0.001` | CAUGHT |
| sonar lines 2/3 swapped | CAUGHT |
| sonar missing final newline | CAUGHT |
| sonar `train.py` changed | CAUGHT |
| sonar `benchmark.py` changed | CAUGHT |
| blood `README.md` changed | CAUGHT |
| qsar_biodeg `config.yaml` replaced by the D28 config | CAUGHT |
| qsar_biodeg `config.yaml` `C` changed | CAUGHT |
| climate `config.yaml` `max_iter` changed | CAUGHT |
| climate `train.py` changed | CAUGHT |
| template `config.yaml` `C` changed (caught via qsar_biodeg and climate) | CAUGHT |
| template `config.yaml` non-D28 key changed | CAUGHT |
| template `train.py` changed | CAUGHT |
| test constant: sonar `C` recorded as `0.02` | CAUGHT |
| test constant: extra recorded key equal to template (`scaler: standard`) | CAUGHT (by the differing-keys check) |
| test constant: blood `max_iter` recorded as template value `1000` and file reverted | CAUGHT (by the differing-keys check) |

The four required classes (wrong value; extra changed key; change to any other template file; change to a non-D28 node's `config.yaml`) are all caught. The byte-equality check for every other file and node is unchanged in strength. **OK.**

## 4. `openml_breast_w` and `openml_wdbc`

Both were changed by `6adf385` and still carry the D28 values at `a3fedbb`/`a56c3a2`. They are **not** in `POOL_22OCT`; they are in `NEW_OPENML`, whose tests (`TestOpenmlPool.test_new_nodes_registered_and_configured`, `test_dataset_json_matches_registry`) check registry metadata and `dataset.json` only and never compare node files with `openml_template`. No other test in `tests/` compares against `openml_template` (grep), and the only other `C: 0.15` text use (`test_r1_d27_novelty.py:447`) works on `openml_ionosphere`, not a D28 node. So these two nodes do not fail at `a3fedbb` and need no exemption; leaving them out of `D28_START_CONFIGS` is correct (adding them would trip the `<= set(POOL_22OCT)` assertion). Their non-config files are byte-identical to the template at `a3fedbb` (checked by blob hash), but nothing tests that. See NON-BLOCKING N1.

## 5. Test results (venv `/tmp/trackg_venv`)

`tests/stage2/test_r1_l8.py`:
- tip `a56c3a2` (in `/tmp/pb/wt/l8`, command as given): **9 passed, 19 subtests passed**. Worktree left clean.
- base `a3fedbb` (scratch worktree): **2 failed, 8 passed, 15 subtests passed**; the failures are exactly `SUBFAILED(node='openml_sonar')` and `SUBFAILED(node='openml_blood_transfusion')` in `TestOpenmlPool22Oct::test_dataset_json_and_template_files` (`C: 0.01` vs `C: 0.15`), matching handoff §3.

Full `tests/` (scratch worktrees at both commits, `--continue-on-collection-errors`, no network):
- base: 14 failed, 476 passed, 1 error, 53 subtests passed.
- tip: 12 failed, 477 passed, 1 error, 57 subtests passed.
- Failure-set diff (base minus tip): exactly the two L8 subtests above. Nothing new fails at the tip. Common failures (both): collection error `tests/test_legacy_noop_skip.py`; `test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`; four in `test_artifact_completeness_and_manifest.py`; five in `test_kdd_paper_sections.py`; two in `test_r1_llamacpp_provider.py` (`test_connection_refused_is_a_transport_error`, `test_dropped_request_is_retried_once_with_the_same_seed`; environment: no network/proxy here, identical at both commits). The full run writes untracked `paper/tables/artifact_completeness_report.txt` (known, handoff §3); this happened only in the scratch worktrees.

## Findings

- **NON-BLOCKING N1 (comment accuracy).** The comment above `D28_START_CONFIGS` says the rule "moved these two pool nodes' start config", which reads as if D28 touched only two nodes. `6adf385` / R1-D28-REPAIR changed four (`openml_breast_w`, `openml_wdbc` as well). Fix (optional, test-only, next time the file is touched): add one line such as "`openml_breast_w` and `openml_wdbc` (NEW_OPENML) carry the same D28 values but are not template-checked by any test." Not required for acceptance; does not affect behaviour.
- **NON-BLOCKING N2 (use of this commit).** `a56c3a2` is not `a3fedbb`. Nothing in the commit points B1 at it, but it must not be used as B1's `AR_HARNESS_ROOT`; B1 stays at exactly `a3fedbb`. Fix: none to the code; the morning report should state that this branch is a candidate test-only commit for the next pin (R1-HARNESS-NEXT-PIN), not a B1 harness.

No BLOCKING findings.

## Verdict

Verdict: accepted

Accepted commit: a56c3a28972ee34435a9412144c956d8a5642bed
