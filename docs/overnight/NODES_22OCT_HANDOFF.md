# D21 pool extension nodes (22 Oct 2026) — handoff

**ENGINEERING_ONLY. AI-assisted (Claude), implementation agent.** Nothing here is evidence. No OpenML data was fetched (openml.org is blocked from the VM); no LLM, Ollama, GPU or SSH use. Not merged, not pushed. `docs/r1/PLAN.md` and `docs/r1/STATUS.md` untouched.

| Repo | Branch / worktree | Base | Commit |
|---|---|---|---|
| harness | `r1-nodes-22oct` / `autoresearch_harness/.claude-worktrees/r1-nodes-22oct` | `r1` @ `4d68c54` | `4012897` |
| paper | `nodes-22oct` / `agent_paper_B/.claude-worktrees/nodes-22oct` | `main` @ `d983e5a` | `0593eaa` + this file |

**Merge order: harness first.** With `AR_HARNESS_ROOT` pointing at an `r1` without `4012897`, `test_openml_active_keys_match_harness_configs` fails (it reads the new node configs).

## What was added

**Harness (`4012897`)**, following L8 (`b55209f`):
- `nodes/openml_sonar` (OpenML 40), `nodes/openml_blood_transfusion` (1464), `nodes/openml_qsar_biodeg` (1494): `benchmark.py`, `train.py`, `config.yaml` and `README.md` are byte-identical to `nodes/openml_template` (a test checks this), plus `dataset.json` (`target: "Class"`).
- `nodes/<node>/data_cache/.gitignore` (`*`, `!.gitignore`, `!.gitkeep`, copied from `openml_credit_g`) and `.gitkeep`. Checked with `git check-ignore`: cache contents are ignored.
- `configs/nodes/<node>.yaml` derived from `openml_credit_approval.yaml` (name, description, dataset fields), with `active_keys.dataset_excluded: ["imputer"]`.
- Registry entries in `src/autoresearch/nodes/registry.py`.
- Tests: `tests/stage2/test_r1_l8.py` (new class `TestOpenmlPool22Oct`: registration, config, dataset.json, template identity, ignored `data_cache` for the three and for `credit_g`, and a synthetic-frame test of the positive label and of imputer inactivity), `tests/stage2/test_r1_d25_active_keys.py` (imputer inactive for the three nodes under every model type, with the same keys as ionosphere; imputer active for `credit_g`).

**Paper (`0593eaa`)**:
- `r1/c3/features.py`: `NODE_INFO` for `openml_credit_g`, `openml_sonar`, `openml_blood_transfusion`, `openml_qsar_biodeg`. `OPENML_DATASET_EXCLUDED`: `credit_g` = `set()` (imputer active), the other three = `{"imputer"}`. `NODE_CODES` appended as 6, 7, 8, 9; codes 0–5 are unchanged, and a test pins them.
- `r1/diagnostics/di_test.py` `project`: same projection for the four nodes (imputer added for `credit_g`, as for `credit_approval`).
- `r1/c3/dataset.py` `noise_table`: **needed fix.** It iterated over all of `NODE_INFO` and indexed the 12 Oct E1 summary. That worked for `wdbc` and `credit_approval` only because the 12 Oct summary happens to contain them. With the new nodes it raised `KeyError: 'openml_credit_g'` (2 failures in `test_c3_dataset.py`). The fix skips nodes that the summary does not cover, so no constants are invented and any later use fails with a `KeyError`. Existing values are unchanged.
- `r1/noise/e1_noise_floor.py`: the three new nodes are appended to `DEFAULT_NODES` (`credit_g` was already listed). Measurement logic is unchanged.
- `r1/noise/check_caches.py`: the readiness check (see below).
- Tests: `test_c3_features.py` (+1), `test_c3_dataset.py` (+1), new `test_check_caches.py` (+3).

## Test counts

| Suite | Before | After |
|---|---|---|
| Harness, `python -m pytest -q -p no:cacheprovider --continue-on-collection-errors` in the worktree | 420 passed, 10 failed, 1 collection error | 427 passed, 9 failed, 1 collection error |
| Paper, `python -m pytest -q r1/tests -p no:cacheprovider --deselect …test_real_runner_desktop_dryrun` | 290 passed (`AR_HARNESS_ROOT` = main harness `r1`; also 290 with the harness worktree) | 295 passed (`AR_HARNESS_ROOT` = harness worktree) |

Notes on the harness suite:
- Without `--continue-on-collection-errors`, pytest stops at collection: `tests/test_legacy_noop_skip.py` imports `src.autoresearch_worker`, which does not exist on `r1`. The brief's "421 passed" was not reproduced. The worktree has no `experiments/` (git-ignored), so the ledger-dependent tests fail there.
- After the change, the failures are a subset of the baseline failures. The one that disappeared, `test_checked_in_report_contains_all_plan_campaigns`, depends on test order: it passes once `paper/tables/artifact_completeness_report.txt` exists, and the first run had written that file. I deleted the file from the worktree afterwards. This is also where the untracked file in the main checkout comes from.

## Positive class for AUC

The template encodes the target with `LabelEncoder().fit_transform(y.astype(str))` and scores `predict_proba[:, 1]`, so the positive class is `sorted(labels)[1]`. It is reported as `positive_label` in `metrics.json`.
- sonar: labels `Mine`/`Rock` → positive **`Rock`**.
- blood-transfusion, qsar-biodeg: `'1'`/`'2'` → positive **`'2'`**, as on `wdbc`, which shows `'1'`/`'2'` in its cache.
- credit-g: `bad`/`good` → positive `good`.

This choice does not affect anything E1 measures. Binary ROC AUC computed from the positive-class probability does not change when the labels are swapped. Accuracy at a 0.5 threshold and `class_weight="balanced"` are also symmetric. Ionosphere already scores its majority class `'g'`. The synthetic test checks the label order and that `val_auc > 0.5`. **Not verified:** which of `'1'`/`'2'` means RB/NRB (qsar) or donated/not donated (blood). I believe `'2'` is the minority class in both, but this is from memory, and the metric does not depend on it.

## `openml_credit_g` check

- `dataset_excluded: []` is consistent: credit-g has categorical columns (13 of 20, from memory of the OpenML metadata; `check_caches.py` flags any mismatch once the cache exists). The registry entry exists. `data_cache/.gitignore` is correct and the contents are ignored.
- `benchmark.py` differs from the template only in its hard-coded `NODE_NAME/DATA_ID/DATASET_NAME/TARGET_NAME` (checked with `diff`). E1 applies the same five edits as on the template nodes.
- Inconsistencies that I did **not** change, because none is a clear bug and none affects E1:
  - The config has no `branch_state_paths`, so E2 snapshots use `DEFAULT_BRANCH_STATE_PATHS`, which lacks `data_cache`. The L8 nodes declare `["artifacts", "data_cache"]`.
  - The config has no `held_out` (it defaults to false).
  - The node has the older layout: `NodeSpec.yaml`, `requirements.txt`, `.autoresearch_baseline/`, no `dataset.json`, and a different `frozen_paths`.
- Its `data_cache/` exists but is empty. E1's `_prepare_node` therefore never uses the L8 pilot fallback for it, which is correct because there is no pilot cache for it.

## E1 readiness

- Cache location: `_prepare_node` copies the node directory. If the copy has a `data_cache` directory, that directory is used as it is, **even when empty**. The L8 pilot fallback (`experiments/r1/pilot/L8_20261009T152916Z/nodes/<node>/data_cache`) applies only when the node has no `data_cache` directory, which is the case for the five L8 nodes. That fallback is git-ignored and exists only in the **main** harness checkout, not in worktrees.
- The new nodes and `credit_g` have a `data_cache/`, so their caches must be fetched into `<AR_HARNESS_ROOT>/nodes/<node>/data_cache`, in the checkout E1 will use. That means the main checkout after merging `r1-nodes-22oct`, using the fetch command of `NOISE_REMEASURE_20261022.md` with `data_id` 31, 40, 1464, 1494.
- Edit set: for all four nodes, `candidate_edits` gives the same five edits as `wdbc` (C ×0.5, C ×2, model_type → random_forest, model_type → gradient_boosting, class_weight → null).
- Smoke test without data: `run_one("openml_sonar", c1 = C 0.15→0.075)` applied the edit and then failed in 3.9 s with `exit code 1`. **E1 has no cache pre-check:** a missing cache produces failed rows (metric `null`), and the run is not aborted. Run `check_caches` first.

### `r1/noise/check_caches.py`

`python -m r1.noise.check_caches [--nodes …] [--json out.json]` (paper repo root, `AR_HARNESS_ROOT` = the harness checkout that E1 will use). For each OpenML node in the 10-node common list, it:
1. runs E1's own `_prepare_node` into a temporary directory;
2. loads the node's `benchmark._load_frame()`, with socket connect and sklearn's `urlopen` disabled in the process;
3. prints the cache source, shape, categorical-column count, missing values, class counts, positive label and minority share, together with library versions;
4. flags mismatches with `NODE_INFO` (rows, features, minority ±0.0015) and with D25 (imputer excluded ⇔ no categorical column).

The exit status is 0 only if every OpenML node is ready. The real cache is never touched.

Output now (sklearn 1.9.1, numpy 2.5.4, pandas 3.0.6, Python 3.13.16):
- `AR_HARNESS_ROOT` = main harness `r1`:
  - `breast_w`, `ionosphere`, `wdbc`, `credit_approval` are **ok via the L8 pilot fallback**, and all match `NODE_INFO`. For example, `wdbc` is 569 × 30 with classes {'1': 357, '2': 212}, and `credit_approval` has 9 categorical columns.
  - `credit_g` reports **cache missing (node data_cache is empty)**.
  - The three new nodes report *not in harness*, because they are not merged yet.
  - Result: ready 4/8, exit 1.
- `AR_HARNESS_ROOT` = harness worktree:
  - All 8 OpenML nodes report cache missing. The four new or credit_g nodes report "node data_cache is empty"; the four L8 nodes report "no node data_cache, no L8 pilot cache", because the worktree has no `experiments/`.
  - The two MLP nodes are skipped.

## Uncertain or open

1. **`NODE_INFO` for the four nodes has not been checked against data.** Rows and features are the OpenML shapes from the brief. The minority shares are the UCI class counts from memory: credit-g 300/1000 = 0.300, sonar 97/208 = 0.466, blood 178/748 = 0.238, qsar 356/1055 = 0.337. They are marked as unverified in a code comment. `check_caches` will flag any difference; correct the values then.
2. `"licence": "Public"` in the three configs is copied from the template configs and has not been checked on openml.org.
3. The PLAN row "D21 common measurement" says "all **nine** nodes (5 original + `credit_approval` + 4 candidates)", but that is 10 nodes, and the brief lists 10. `check_caches` uses 10.
4. The D21 rule requires library versions in every measurement manifest, but the E1 manifest still records only the Python version. I did not change E1 (that was outside the brief); `check_caches` prints the versions. Decide whether E1 should add them before the common run.
5. Node lists not updated, because they belong to pool decisions not yet taken: `r1/liveness/__main__.py` `DEFAULT_RUN_NODES`, `r1/scripts/c3_label_sweep.py` `D21_NODES`. `r1/c3/audit.py` and `r1/headroom/e1b_collect.py` carry the same pilot-cache fallback as E1 and work for the new nodes once their own caches exist.
6. `r1/c3/dataset.py` `E1_SUMMARY` still points at the 12 Oct summary. After the common run it must be repointed, otherwise the new nodes have no noise constants. They now fail loudly with a `KeyError`.
7. Fetching into `nodes/<node>/data_cache` on `r1` **before** merging the harness branch leaves the cache as untracked files there, because the `.gitignore` arrives with the merge. Merge first, then fetch.
