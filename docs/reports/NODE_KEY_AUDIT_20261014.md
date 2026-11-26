# Node key audit — 14 October 2026 (ENGINEERING_ONLY)

*AI-assisted (BUILD_BATCH3, A1), opencode/deepseek-v4.1-flash, at the author's request. Read-only: this audit ran no worker, no LLM and no GPU. Evidence is the harness checkout at `~/Documents/autoresearch_harness` branch `r1`, commit `4540fa5` (paper commit `0a3f284` + batch-3 work). Not evidence for any claim; input to the author's E3 node decisions.*

D25 (PLAN §10, 14 Oct 2026) requires that each node may declare which editable keys are active for the current configuration, and that "all other nodes are audited for inert keys before E3". This audit lists, for every registered node, each editable symbol as **active** or **inert**, with the code location that decides it, under each relevant configuration.

**Active** means an edit to that symbol changes the training configuration that is actually used. **Inert** means the frozen code ignores the symbol or overrides it, so the edit cannot change the run (it wastes a worker run and pollutes C1 as a false edit).

## Headline

- The seven `openml_*` nodes now carry a D25 declaration (`configs/nodes/openml_*.yaml`). The declaration matches the template code for all model types (`nodes/openml_template/benchmark.py`, and the inline copies in `nodes/openml_bank_marketing/benchmark.py` and `nodes/openml_credit_g/benchmark.py`).
- Two decision points below rest on metadata that is **not in this repository** (no OpenML download allowed): the `imputer` activity on `openml_bank_marketing` and `openml_credit_g`. Both are **declared active** (no exclusion) and flagged for the author.
- One node with no declaration has configuration-dependent inert keys: **`resnet_trigger`** (`BATCH_SIZE`, `EPOCHS` under fast-search; `LEARNING_RATE` values above the MPS cap). Flagged for the author.
- `autoresearch_linux` has a registered config but **no node directory** in this checkout (flagged, pre-existing).
- Every other node (`digits_mlp`, `tabular_mlp`, `lr_synthetic`, `mlp_synthetic`, `mlagentbench_vectorization`, `autoresearch_macos`) has all editable symbols active in every configuration this repository defines, so it needs no declaration.

## Summary

| Node | Declaration | Inert keys | Status |
|---|---|---|---|
| `digits_mlp` | not needed | none | clean |
| `tabular_mlp` | not needed | none | clean |
| `lr_synthetic` | not needed | none | clean |
| `mlp_synthetic` | not needed | none | clean |
| `mlagentbench_vectorization` | not needed | none | clean |
| `openml_ionosphere` | declared | `imputer` (dataset), `class_weight` (GB) | declared |
| `openml_wdbc` | declared | `imputer` (dataset), `class_weight` (GB) | declared |
| `openml_breast_w` | declared | `imputer` (dataset), `class_weight` (GB) | declared |
| `openml_diabetes` | declared | `imputer` (dataset), `class_weight` (GB) | declared |
| `openml_credit_approval` | declared | `class_weight` (GB) | declared |
| `openml_bank_marketing` | declared | `class_weight` (GB); `imputer` undecided | **flagged** |
| `openml_credit_g` | declared | `class_weight` (GB); `imputer` undecided | **flagged** |
| `resnet_trigger` | none | `BATCH_SIZE`, `EPOCHS` (fast-search); `LEARNING_RATE` above MPS cap | **flagged** |
| `autoresearch_macos` | not needed | none | clean |
| `autoresearch_linux` | not needed | none | **flagged** (no node directory) |

## Per-node detail

### `digits_mlp` — `train.py`, val_score (maximize)

| Symbol | Status | Evidence |
|---|---|---|
| `HIDDEN_UNITS` | active | `nodes/digits_mlp/train.py:13`, passed `hidden_units=HIDDEN_UNITS` at `:22` into `run_benchmark` (`nodes/digits_mlp/benchmark.py:35`), used in `MLPClassifier` at `:47` |
| `ALPHA` | active | `nodes/digits_mlp/train.py:14` → `:23` → `benchmark.py:48` |
| `LEARNING_RATE_INIT` | active | `nodes/digits_mlp/train.py:15` → `:24` → `benchmark.py:48` |
| `BATCH_SIZE` | active | `nodes/digits_mlp/train.py:16` → `:25` → `benchmark.py:49` |
| `MAX_ITER` | active | `nodes/digits_mlp/train.py:17` → `:26` → `benchmark.py:49` |

No other configuration axis. No declaration required.

### `tabular_mlp` — `train.py`, val_score (maximize)

Identical structure to `digits_mlp`: symbols at `nodes/tabular_mlp/train.py:13-17`, passed at `:22-26`, used in `MLPClassifier` at `nodes/tabular_mlp/benchmark.py:52-54`. All active. No declaration required.

### `lr_synthetic` — `train.py`, val_score (maximize)

| Symbol | Status | Evidence |
|---|---|---|
| `LEARNING_RATE` | active | `nodes/lr_synthetic/train.py:27`, passed `lr=` at `:148` |
| `REGULARIZATION` | active | `:28`, passed `reg=` at `:149` |
| `N_EPOCHS` | active | `:29`, passed `n_epochs=` at `:150` |
| `BATCH_SIZE` | active | `:30`, passed `batch_size=` at `:151` |

No declaration required.

### `mlp_synthetic` — `train.py`, val_score (maximize)

| Symbol | Status | Evidence |
|---|---|---|
| `LEARNING_RATE` | active | `nodes/mlp_synthetic/train.py:7` → `:16` |
| `HIDDEN_DIM` | active | `:8` → `:17` |
| `REGULARIZATION` | active | `:9` → `:18` |
| `N_EPOCHS` | active | `:10` → `:19` |
| `BATCH_SIZE` | active | `:11` → `:20` |

No declaration required.

### `mlagentbench_vectorization` — `config.yaml`, speed_score (maximize)

| Symbol | Status | Evidence |
|---|---|---|
| `batch_size` | active | `nodes/mlagentbench_vectorization/train.py:139`, used in `_make_problem` `:143` |
| `image_size` | active | `:140` → `:144` |
| `num_filters` | active | `:141` → `:145` |
| `kernel_size` | active | `:142` → `:146` |
| `implementation` | active | `:150` dispatch (`:155-162`) |
| `stride` | active | `:151` / correctness check `:180` |
| `padding` | active | `:151` / `:181` |
| `repeat_count` | active | `:187` (timing loop; changes the score's noise but not the workload) |

All active; no declaration required.

### `openml_*` (seven nodes) — `config.yaml`, val_auc (maximize)

The pipeline is frozen and shared: `nodes/openml_template/benchmark.py` (five nodes) and the inline copies `nodes/openml_bank_marketing/benchmark.py` and `nodes/openml_credit_g/benchmark.py` (same line numbers for the relevant blocks), driven by the node's `dataset.json` / inline dataset identity.

| Symbol | logistic_regression | random_forest | gradient_boosting | Evidence |
|---|---|---|---|---|
| `model_type` | active | active | active | dispatch `benchmark.py:224-248` |
| `C` | active | inert | inert | only `LogisticRegression(C=...)` `:227` |
| `class_weight` | active | active | **inert** | LR `:228`, RF `:237`; absent from `GradientBoostingClassifier` `:242-247` |
| `max_iter` | active | inert | inert | `LogisticRegression(max_iter=...)` `:229` |
| `n_estimators` | inert | active | active | RF `:235`, GB `:243` |
| `max_depth` | inert | active | active | RF `:236`, GB `:245` |
| `learning_rate` | inert | inert | active | GB `:244` |
| `scaler` | active | active | active | `numeric_steps` `:188-191`; numeric columns exist in every dataset |
| `imputer` | active iff categorical columns | active iff categorical columns | active iff categorical columns | `categorical_columns` `:183-186`; imputer steps `:192-196`; `ColumnTransformer` `:209-214`. With no categorical columns the categorical branch never runs |

Dataset-level `imputer` decisions, from the committed OpenML feature metadata in `experiments/r1/pilot/L8_20261009T152916Z/nodes/<node>/data_cache/openml/openml.org/api/v1/json/data/features/<id>.gz` (and the same cache under `results/r1/pilot/E1b_20261013T151857Z/provenance/snapshots/openml_ionosphere__*/...`), plus `nodes/openml_*/dataset.json`:

| Node | Dataset | Numeric / nominal features | `imputer` | Declaration `dataset_excluded` |
|---|---|---|---|---|
| `openml_ionosphere` | 59 | 34 / 0 | inert | `imputer` |
| `openml_wdbc` | 1510 | 30 / 0 | inert | `imputer` |
| `openml_breast_w` | 15 | 9 / 0 | inert | `imputer` |
| `openml_diabetes` | 37 | 8 / 0 | inert | `imputer` |
| `openml_credit_approval` | 29 | 6 / 9 | active | — |
| `openml_bank_marketing` | 1461 | **not in the repository** | **undecided** | — (declared active) |
| `openml_credit_g` | 31 | **not in the repository** | **undecided** | — (declared active) |

**Flagged for the author (rule 3 stop-and-report).** For `openml_bank_marketing` (OpenML id 1461) and `openml_credit_g` (id 31) no feature metadata exists in either repository (their `data_cache/` directories contain only `.gitkeep`/`.gitignore`; the E1 pilot could not download them because `NOISE_FLOOR_20261012.md:46,77` records "no local data cache; OpenML is blocked from the VM"). The batch prompt forbids downloading. Both declarations therefore leave `imputer` active. Options for the author: (a) accept the declaration as-is (safe but may leave an inert key on a dataset with no categorical columns); (b) allow one OpenML metadata fetch on the Mac to settle it; (c) drop both nodes from E3 until settled. The harness declaration mechanism itself follows D25 either way.

`class_weight` under `gradient_boosting` is omitted from the declaration (inert per the table). The scripted stand-in still draws `class_weight` from its fixed categorical family; when that happens under GB the control plane now rejects the proposal as an inactive key before any worker run (test `tests/stage2/test_r1_d25_active_keys.py`).

### `resnet_trigger` — `train.py`, val_auc (maximize) — **flagged**

No `active_keys` declaration exists. Editable symbols are not listed in the spec (`"editable_symbols"` absent in `configs/nodes/resnet_trigger.yaml`); the manager's bounded candidates are `WEIGHT_DECAY`, `DROPOUT`, `KERNEL_SIZE`, `GRAD_CLIP_NORM`, `BATCH_SIZE`, `EPOCHS`, `LEARNING_RATE` (`src/autoresearch/manager/hyperparam_edits.py`).

| Symbol | default run | fast-search run (`RESNET_TRIGGER_FAST_SEARCH=1`) | Evidence |
|---|---|---|---|
| `BATCH_SIZE` | active | **inert** (env override) | `nodes/resnet_trigger/train.py:62`; overridden at `:85,:117` |
| `EPOCHS` | active | **inert** (env override) | `:63`; overridden at `:86,:118` |
| `LEARNING_RATE` | active below the MPS cap; above the cap the value is clipped | same | `:64`, `:131`; `optimizer_lr = min(config.learning_rate, MPS_MAX_LEARNING_RATE)` `:315`, `MPS_MAX_LEARNING_RATE = 5e-4` `:74` |
| `WEIGHT_DECAY` | active | active | `:65`, `:132` |
| `KERNEL_SIZE` | active | active | `:68`, `:134` |
| `DROPOUT` | active | active | `:69`, `:135` |
| `GRAD_CLIP_NORM` | active | active | `:73`, `:380` |

This is the same declaration mechanism (model_type-keyed) only if the R1 runs are pinned to one mode; the node's inertia is keyed by an environment variable, not by `model_type`. Not fixed here (the prompt restricts the fix to the shared declaration mechanism). **Flagged for the author**: decide (a) a one-key declaration active set per env mode, (b) exclude `BATCH_SIZE`/`EPOCHS` for fast-search campaigns only, or (c) leave as is and accept inert edits on this node.

### `autoresearch_macos` — `train.py`, val_bpb (minimize)

| Symbol | Status | Evidence |
|---|---|---|
| `ASPECT_RATIO` | active | `nodes/autoresearch-macos/train.py:485`, used in `build_model_config` `:533-535` |
| `HEAD_DIM` | active | `:486` → `:534-535` |
| `WINDOW_PATTERN` | active | `:487` → `:537` (values `L`/`S`; invalid values fail at model build) |
| `TOTAL_BATCH_SIZE` | active, coupled | `:490`; divisibility assert `:567` (`TOTAL_BATCH_SIZE % (DEVICE_BATCH_SIZE * MAX_SEQ_LEN) == 0`) and `grad_accum_steps` `:568` |
| `EMBEDDING_LR` | active | `:491` → `:573` |
| `MATRIX_LR` | active | `:493` → `:576` |
| `SCALAR_LR` | active | `:494` → `:575` |
| `WEIGHT_DECAY` | active | `:495` → `:577` and schedule `:600` |
| `WARMDOWN_RATIO` | active | `:499` → `get_lr_multiplier` `:591-597` |
| `FINAL_LR_FRAC` | active | `:500` → `:597` |
| `DEPTH` | active, coupled | `:502` → `:535` (model size); interacts with `ASPECT_RATIO`/`HEAD_DIM` and `TOTAL_BATCH_SIZE` divisibility |
| `DEVICE_BATCH_SIZE` | active, coupled | `:503` → `:566,:570`; couples into the divisibility assert |

All active; some edits are infeasible by precondition (assert) rather than inert. No declaration required for D25; the constraints are already handled by worker validity (failed_invalid) and the `TOTAL_BATCH_SIZE`/`DEVICE_BATCH_SIZE` coupling is a candidate for a later declaration if E3 uses this node.

### `autoresearch_linux` — **flagged**

`configs/nodes/autoresearch_linux.yaml` registers the same symbols as `autoresearch_macos`, but there is **no `nodes/autoresearch_linux/` directory** in this checkout (the registry only maps the config). Any campaign on this node fails at node copy. Pre-existing; flagged for the author. Not fixed here (out of the batch scope).

## What changed in this batch

- `configs/nodes/openml_*.yaml` gained the D25 `active_keys` declaration (seven files, minimal insertion).
- Harness enforcement and prompt filtering are in harness commit `4540fa5` (`nodes/active_keys.py`, `control_plane/campaign.py`, `manager/langgraph_manager.py`), tested in `tests/stage2/test_r1_d25_active_keys.py`.
- The scripted stand-in reads the declaration for its numeric action space (`r1/headroom/scripted_manager.py`), with the pre-change golden in `r1/tests/data/scripted_proposal_golden_E1b_20261012T161034Z.json`.

## Open items for the author (not fixed here)

1. `imputer` activity on `openml_bank_marketing` and `openml_credit_g`: no in-repo metadata; declared active.
2. `resnet_trigger`: configuration-dependent inert keys (`BATCH_SIZE`, `EPOCHS` under fast-search; `LEARNING_RATE` above the MPS cap) and no declaration. The fix is not the same `model_type`-keyed mechanism; options listed above.
3. `autoresearch_linux`: no node directory in this checkout.
4. `autoresearch_macos` coupling constraints (`TOTAL_BATCH_SIZE` divisibility, `DEVICE_BATCH_SIZE`): a validity/precondition concern, not inert keys; no action taken.
