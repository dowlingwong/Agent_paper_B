# M3 dry runs — environment replay plan and B.2 audit plan (DRYRUN)

**4 November 2026. Mac-local worker (Claude), MAC_LOCAL_RUNBOOK_20261104 M3 step 4; AI-assisted. DRYRUN: no worker ran on any sweep configuration and no metric was produced. Nothing here is evidence or a label.**

**Where they ran.**
- Code: `mac-b2-20261104` @ `7bf11d9c`.
- Run from a Git clone of that commit in the session scratch directory, outside the repository. The clone is a byte copy of the frozen corpus layout: the same index, sidecar and relocated sweep directories, with Git trees `6b1c0c61…` (append-only) and `468e57ce…` (none). The original records were only read.
- Environment: Linux cloud workspace, Python 3.13. The harness checkout `897d83c` was used only to read the pinned NodeSpecs at `6adf385`, via `git show`.

Commands, run from the clone root with `AR_HARNESS_ROOT` set:
```
python -B -m r1.scripts.c3_env_replay --paper-root . --out <scratch>/replay_dryrun --dry-run --harness $AR_HARNESS_ROOT
python -B -m r1.scripts.c3_audit_dryrun --paper-root . --out <scratch>/audit_dryrun
```
Outputs (scratch files, not committed; the tables below are copied from them):
- `replay_plan.json`, SHA256 `3ec741425c86c67deb76819b2f8b258adbaa9c1894929de2bcae3481385f1110`;
- `audit_dryrun.json`, SHA256 `51ea746c070f4170e48fdf17961f0963f51af6d9370d785e06570e98efa15765`.

The same checks also run as tests on the committed corpus: `test_dry_run_on_the_frozen_corpus_selects_the_declared_16_cases` and `test_dryrun_on_the_frozen_corpus_partitions_the_whole_population`.

## 1. Environment-replay plan (packet e1)

**Source checks passed:**
- the index SHA256 `812468e2…`, the sidecar `bb6d891c…`, and both manifests (`f18f8a8b…`, `50530673…`);
- the frozen trees as above;
- the original-blob mapping: every relocated file equals its blob at the original sweep commit;
- the collector binding, read from `ccb4712:r1/headroom/e1b_collect.py` (blob SHA256 `0001260442f9…3271`): the instance-seed rule and `LocalWorker(..., train_seed=seed, split_seed=seed)`.

**For all 16 cases:**
- the recovered patch equals the ledger `patch_hash` and the archived `patch.diff`;
- the archived original `run.log` carries the recorded metric token;
- trial 1 is `kept`;
- trial 2's `current_best_before` equals trial 1's metric.

**Environment checks:** `DEFERRED_TO_HOST`. They need the batch wrappers and the venv on deepthought.

| Case | Decision | Metric | Recorded token | Seed (train = split) | Edit | Patch sha256 (recorded = recovered) |
|---|---|---|---|---|---|---|
| `digits_mlp__s104:t001` | kept | val_score | 0.718663 | 104 | `LEARNING_RATE_INIT` 1e-3 → 1e-4 | `ee8bc5b7f0ed…` |
| `digits_mlp__s104:t002` | kept | val_score | 0.799443 | 104 | `HIDDEN_UNITS` 32 → 64 | `c6429906e1dc…` |
| `tabular_mlp__s102:t001` | kept | val_score | 0.738750 | 102 | `LEARNING_RATE_INIT` 1e-3 → 1e-4 | `ee8bc5b7f0ed…` |
| `tabular_mlp__s102:t002` | kept | val_score | 0.909325 | 102 | `HIDDEN_UNITS` 32 → 64 | `c6429906e1dc…` |
| `openml_breast_w__s105:t001` | kept | val_auc | 0.992351 | 105 | `max_iter` 100 → 200 | `8ddfb662ea12…` |
| `openml_breast_w__s105:t002` | discarded | val_auc | 0.992351 | 105 | `max_iter` 200 → 250 | `5deeff62687b…` |
| `openml_ionosphere__s103:t001` | kept | val_auc | 0.941176 | 103 | `C` 0.15 → 0.5 | `8b131cc69e79…` |
| `openml_ionosphere__s103:t002` | discarded | val_auc | 0.941176 | 103 | `max_iter` 1000 → 2000 | `a150943df1c2…` |
| `openml_wdbc__s100:t001` | kept | val_auc | 1.000000 | 100 | `max_iter` 100 → 200 | `8ddfb662ea12…` |
| `openml_wdbc__s100:t002` | discarded | val_auc | 1.000000 | 100 | `max_iter` 200 → 500 | `a4823db3810e…` |
| `openml_credit_approval__s100:t001` | kept | val_auc | 0.895052 | 100 | `max_iter` 1000 → 2000 | `a150943df1c2…` |
| `openml_credit_approval__s100:t002` | discarded | val_auc | 0.895052 | 100 | `max_iter` 2000 → 2500 | `341ea56c11ab…` |
| `openml_sonar__s105:t001` | kept | val_auc | 0.844538 | 105 | `max_iter` 100 → 200 | `8ddfb662ea12…` |
| `openml_sonar__s105:t002` | discarded | val_auc | 0.844538 | 105 | `max_iter` 200 → 500 | `a4823db3810e…` |
| `openml_climate__s104:t001` | kept | val_auc | 0.889961 | 104 | `max_iter` 1000 → 2000 | `a150943df1c2…` |
| `openml_climate__s104:t002` | discarded | val_auc | 0.889961 | 104 | `max_iter` 2000 → 3000 | `395921b41a86…` |

**Observations (not conclusions):**
- In all six OpenML nodes, trial 2 was `discarded` with the same recorded value as trial 1. Each trial-2 case is still a zero-tolerance check of a distinct recovered configuration and a separate run. The selection is fixed by the protocol and was not changed.
- Several campaigns share a first edit (`max_iter` or `LEARNING_RATE_INIT`) on the same per-family template, so their patch hashes coincide.
- Every recorded token has 6 decimals. The comparison is on the emitted token and is never re-rounded.

## 2. B.2 audit plan

**Design check:** K = 10; label seeds 7001–7005; evaluation seeds 7006–7010; disjoint (`r1.c3.audit.split_seeds(DEFAULT_SEEDS)`).

**Table.** Built from the relocated ledgers with the classification: the same replay as `build_from_sweep`, minus its `origin/main` publication check, which is gate B1.
- 5,813 ledger rows produce 4,999 proposals and 302 distinct configurations.
- Replay checks: 0 zero-delta violations and 0 repeat-metric violations.
- 526 rows were skipped as invalid: 473 `invalid_config` (exit code 2) and 53 `proposal_precondition_failed`. These rows carry no metric and are not proposals.
- `proposals.jsonl` SHA256 `b713c42338c4…`; `configs.json` SHA256 `b585b7275866…`.

**Counts by kind.** The partition is complete; it comes from `partition_population`, the function `evidence_plan` uses.

| Kind | Count | Audited | Label | Evaluation row |
|---|---|---|---|---|
| no-op (rule) | 0 | no | `rule_noop`, Δ = 0, se = 0 | no |
| duplicate | 3,274 | no | **none** | no |
| eligible | 1,725 | yes, K = 10 | `audit`, seeds 7001–7005 | yes, seeds 7006–7010 |
| **total** | **4,999** | | 1,725 label rows | 1,725 evaluation rows |

| Node | Duplicates | Eligible | Total |
|---|---|---|---|
| digits_mlp | 415 | 269 | 684 |
| openml_breast_w | 414 | 228 | 642 |
| openml_climate | 372 | 163 | 535 |
| openml_credit_approval | 467 | 169 | 636 |
| openml_ionosphere | 342 | 172 | 514 |
| openml_sonar | 425 | 226 | 651 |
| openml_wdbc | 407 | 246 | 653 |
| tabular_mlp | 432 | 252 | 684 |
| **all** | **3,274** | **1,725** | **4,999** |

| Memory mode | Duplicates | Eligible |
|---|---|---|
| append_only_summary | 999 | 1,412 |
| none | 2,275 | 313 |

**Audit workload:** 466 unique (node, configuration) pairs to run, so 466 × 10 = **4,660 seed runs**.
- *Estimate only:* recorded sweep-1 trial wall times average 1.95 s over 5,287 successful trials, which gives about 2.5 CPU-h, or roughly 10–15 min of wall time at 16 workers plus overhead.
- This is not a measurement. The authorization's provisional estimate is 2–3 h.

**Block rules.** Checked with `evidence_blocks` on **synthetic placeholder metrics**: shape only, not a worker run, never a label value.
- There is one label row per no-op and per eligible proposal, and **0 for duplicates**.
- Every no-op is labelled by rule with exactly 0. None occur in sweep 1; the rule path is covered by `test_noops_are_labelled_by_rule_duplicates_get_no_label` and `test_blocks_keep_seed_roles_separate_and_handle_rules`.
- Audit labels carry seeds 7001–7005 only; evaluation rows carry seeds 7006–7010 only.
- The evaluation block covers exactly the eligible set.
- Neither block carries the other role's values.

**Observations (not conclusions):**
- **Sweep 1 has no rule no-ops.** The harness rejects inactive-key edits (one `proposal_rejected_inactive_key` event in the append-only mode), so every proposal changes the active projection.
- **65 % of proposals are duplicates** and get no label: 3,274 of 4,999 overall, and 2,275 of 2,588 in memory mode `none`. This is the duplicate rate (C1 waste) that Phase 9's report must state.
