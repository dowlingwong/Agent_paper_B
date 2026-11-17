# Track G port checklist — declaring a node and its 3–5 representative edits

**Written 9 Nov 2026 by a Mac-local worker agent (Claude), AI-assisted, for M10 step 0.** Not independently reviewed yet (Review: pending, see `reports/M10_PORTKIT_HANDOFF_20261109.md`). This file authorizes nothing: RUNBOOK Track G (G.1, G.1b), `TRACK_G_RUNBOOK.md` §2–§4, `HOREKA_RUNBOOK_20261104.md` HK2 and the PLAN §10 rows govern (R1-BX-D4, D5, R1-BX-REVISIONS (c), (g), R1-BX-PORTING-CONFIRM, R1-BX-PROPOSED-CONFIRM). Where they differ, the dated PLAN rows win.

**Who uses it.** The HoreKa agent, once per ported task, on its own port branch (proposed `hk2-trackg-<date>`), built on the harness commits named in the hand-off. Each port is reviewed by a fresh agent before use; the reviewer ticks this list too.

*Update 17 Nov 2026 (`R1-TRACKG-PORT-OWNER`):* the Mac agent writes the port kits (one independently reviewed bundle per suite) and the experiment agent deploys and smoke-tests them on Ada; this replaces the HoreKa-agent assignment above. Section F (licence and provenance) was added the same day, at the author's request, following the U1 audit's recommendation (`reports/trackg_g0_20261117/U1_LICENCE_AVAILABILITY_20261117.md` §10, on `ops-tasl-20261116`).

**Shared pieces it builds on** (harness, package `autoresearch.trackg`):

| Piece | Where |
|---|---|
| Node template `trackg_node/v1` | `configs/trackg/node_template.yaml`; loader `autoresearch.trackg.node_template.load_trackg_node_spec` |
| Base metric parser (ok / divergent / infrastructure_failure) | `autoresearch.trackg.outcome` |
| Per-run working-copy runner with limits | `autoresearch.trackg.runner.WorkingCopyRunner`, `ResourceLimits` |
| Deterministic settings and their record | `autoresearch.trackg.determinism` |
| Validation-only selection | `autoresearch.trackg.selection` |
| Diff application, inert and duplicate detection, provenance | `autoresearch.trackg.diff_support` |
| `manager_proposal/v2-diff` schema | `autoresearch.trackg.proposal_v2_diff` |
| Representative-edit manifest | `scripts/trackg_declare_edits.py` (`autoresearch.trackg.declared_edits`) |
| Stub-manager smoke campaign | `autoresearch.trackg.smoke.run_smoke_campaign` |

---

## A. Node spec (one YAML per task)

Copy `configs/trackg/node_template.yaml` to `configs/trackg/nodes/<node>.yaml` on the port branch and fill every field. The loader is strict; it must load without error.

*Deviation from `TRACK_G_RUNBOOK.md` §2, stated:* the runbook puts a Track G `NodeSpec` "under `configs/nodes/` … registered in `nodes/registry.py`". The kit uses `configs/trackg/nodes/` and its own loader (`load_trackg_node_spec`), with no registry entry, because `manager_proposal/v2-diff` is not yet wired into the campaign path; the loader's `to_base_node_spec()` gives the harness `NodeSpec` view. How T1 nodes reach the label-sweep path (a registry entry pointing at the Track G loader, or a T1 sweep entry point) is decided when v2-diff is wired in (later M10/M3 work).

- [ ] `name`, `description`, `suite`, `domain` filled; the description says what the fixed budget means for this task.
- [ ] `editable_paths` lists only what a diff may touch (for example `train.py`, a `model/` directory).
- [ ] `frozen_paths` lists the evaluator, the data loader, the metric code, the data, `prepare.py`-type scripts **and the fixed-step wrapper itself**. It is not empty, and no editable entry is covered by a frozen entry (checked after normalisation).
- [ ] **No frozen script lives in an editable directory**, and no editable directory is on a frozen script's import path other than as intended: a file created there could shadow the frozen script's imports.
- [ ] `allow_new_files` is `false` unless the task needs new files; even when `true`, a new module or new directory named like an importable module (standard library, a package on the run interpreter's path, `sitecustomize`, `usercustomize`) is refused. `scripts/trackg_declare_edits.py` uses the same flag, so declared edits and runs agree.
- [ ] `run_budget` is `kind: steps` or `kind: tokens` with a positive integer. **No wall-clock budget** (R1-BX-D5): the loader refuses any key whose name contains a time word (`time`, `timeout`, `hour`, `minute`, `second`, `duration`, `deadline`, `wall`, `clock`, `runtime`, …) at any depth, including `default_budget.max_wall_clock_hours` and keys under `notes` and `external_benchmark`, and a `run_command` that passes a time budget (`--time-budget`, `--timeout`, `--max-time`, `--time`, `TIME_BUDGET=…`). Environment prefixes such as `TIMEOUT=…` or `MAX_SECONDS=…` are refused too. Free text in string values is not scanned: do not put a time budget in prose either. The refusal is conservative and names the matched word: rename a key that is not a time budget (for example `min_lr` → `lr_min`, `n_timesteps` → `n_steps_env`) or move it into prose, and move step-type flags that contain a time word (`--eval-timeout`) into the wrapper. A task whose own script has a wall-clock budget (autoresearch) gets a fixed-step wrapper.
- [ ] Label runs take about 1–2 min at the budget on the table's GPU model; closed-loop evaluation runs up to about 5 min (R1-BX-D5). The value is fixed before the census and not changed afterwards without a new review.
- [ ] `workers.dataloader_workers` and `workers.threads` are fixed integers; the wrapper reads `AR_NUM_WORKERS` (and does not choose its own count).
- [ ] `metric.metric_regex` matches the **validation** metric line the wrapper prints at the end (one capture group; the last match counts) and is **anchored** (`^…`). Recommended: the frozen wrapper prints the metric after the training call returns with a distinctive prefix (for example `AR_METRIC val_accuracy=0.71`), and `metric_regex` anchors on that prefix. The loader refuses a `metric_regex` that matches a typical test-metric line, and at run time a selection match overlapping a test-metric line is `divergent` (`metric_regex_matches_test_line`). `metric_direction` is right.
- [ ] `metric.loss_regex` (**required**) matches every training-loss line the wrapper prints, so a non-finite loss (also `tensor(nan)`-style tokens) is caught as `divergent`.
- [ ] `metric.steps_regex` (recommended for step budgets) matches the step counter, so a run that stops before the budget is `divergent` (`budget_not_reached`).
- [ ] Extra `metric.infrastructure_log_patterns` only for messages that cannot be caused by a proposal (disk, file system, scheduler). Never CUDA OOM or a Python exception: those are the proposal's (divergent).
- [ ] `selection`: for a test-scored task `test_scored: true`, `selection_split: validation`, `test_metric_name` set and different from `metric_name` (R1-TRACKG-ROLE). The test metric is never printed under the validation metric's name.
- [ ] `determinism` left at the defaults (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `cublas_workspace_config: ":4096:8"`). `deterministic_warn_only: true` only if the census shows the baseline cannot run otherwise; say so in the port report.
- [ ] `seed_env` names two **different** variables the wrapper reads for the training and split seeds.

## B. Fixed-step wrapper and task assets

- [ ] Native port in the harness venv where possible (R1-BX-REVISIONS (g)); a container only if the task ships only as an image (Apptainer, `.sif` sha256 in provenance; M10 step 4, not in this kit).
- [ ] The wrapper runs exactly `run_budget.value` steps (or tokens) and then prints the validation metric; it reads the budget from `{budget}` in the run command or `AR_BUDGET_VALUE`.
- [ ] It reads the training and split seeds from `seed_env`; seeds never appear in a proposal.
- [ ] It does **not** set `torch.backends.cudnn.benchmark = True` or turn deterministic algorithms off (that would override the runner's settings).
- [ ] Environment variables that must be set before `import torch` (for example `PYTORCH_CUDA_ALLOC_CONF`) are set in the run command or the wrapper's environment, not in-script: the runner's determinism shim imports `torch` at interpreter start. That import time is part of the measured run time (the timeout basis).
- [ ] Known limit to keep in mind: the metric is parsed from stdout, which editable code shares, so a diff could print a forged metric line. The `AR_METRIC` prefix printed by the frozen wrapper after training reduces but does not remove this; the port review checks that the wrapper, not the editable code, prints the metric.
- [ ] Large data live outside the node directory and are reached through a symlink in a frozen path (the runner copies the node per run and keeps symlinks as symlinks); diffs through symlinks are refused.
- [ ] Data preparation is a one-off `setup_command` step, not part of the run command.

## C. Representative edits — declared as diffs **before any measurement**

1. [ ] Write **3–5** unified diffs against the node's baseline, one file each, for example `nodes/<node>/representative_edits/E1.diff` … `E5.diff`. Cover the range a proposer is likely to produce:
   - a small, plausible hyperparameter change;
   - a larger change of the same kind (or the opposite direction);
   - a code-level change (optimizer, schedule, architecture detail);
   - if the task allows it, one edit likely to diverge or interact with another (for the S1.1 interaction measurement and the divergence class).
2. [ ] Every diff touches only `editable_paths`, is not inert and does not duplicate another. Check with
   `python3 scripts/trackg_declare_edits.py --spec configs/trackg/nodes/<node>.yaml --node-dir nodes/<node> --out nodes/<node>/representative_edits/manifest.json nodes/<node>/representative_edits/E*.diff`.
   The script refuses a set with fewer than 3 or more than 5 edits, a scope violation, an inert diff or a duplicate. It runs nothing.
3. [ ] **Commit** the diffs and `manifest.json` on the port branch. Record in the port report: the commit SHA, the manifest's sha256 (printed by the script), and each edit's sha256.
4. [ ] Only after that commit: the determinism check, the 10-seed noise floor (seeds 8001–8010), the D21 verdict (G.1b). Every measurement record cites the manifest sha256. An edit changed after measurement starts is a new edit with a new manifest; the old one is kept, never overwritten (no-deletion rule).

## D. Runner settings per host

- [ ] GPU by **UUID** (`GPU-…` or `MIG-…`, from `nvidia-smi -L`); indices are refused.
- [ ] CPU list and memory cap set; the runner refuses limits without them unless an explicit `uncapped_reason` is given (recorded). Under Slurm, use `memory_method: external` with `external_limit` naming the enforcement (for example `"slurm --mem=64G"`); `rlimit_data` is for hosts without a cgroup cap. The CPU list must lie inside the job's CPU set.
- [ ] Timeout = 3 × the measured run time at the budget (`measured_run_seconds`). Only the first, measuring run may use `provisional_timeout_seconds`, and its record says so.
- [ ] One GPU model per label table (R1-BX-D5); the placement is recorded with each run.

## F. Licence and provenance (per node; added 17 Nov 2026)

Datasets are **never redistributed**: no task data, pretrained weights or derived arrays are committed to the port branch or placed in a bundle. The node carries a download script and hashes only.

- [ ] `nodes/<node>/LICENCES.md` is listed in `frozen_paths` and records:
  - the upstream repository URL and the **pinned commit** read by the port (use the HEAD shas resolved by the U1 audit, §7, where it gives them; never track a moving branch);
  - the code licence (SPDX) and where it is stated: the licence file path upstream, or the README statement where no file exists;
  - for each dataset and pretrained asset: the source URL, the licence or terms **exactly as the U1 audit cites them** (or "unknown / not stated" where it says so), the hub revision read, and the dataset hash, or where it is recorded;
  - the attribution string; for CC-BY-NC material, the licence notice, the "modified" indication with the list of changes, and any MIT/Apache sub-components that apply;
  - the container image digest, if a container is used.
- [ ] Every dataset is fetched by the frozen one-off `setup_command`, from its source URL, into a directory **outside** the node that is linked as a frozen `data/` path. The fetch writes the sha256 of every file to a data manifest that every run checks before training.
- [ ] Hashes known in advance (for example a file inside a pinned upstream commit, or an archive md5 published by its loader) are pinned in the frozen script and checked. Hub revisions are checked against the revision the U1 audit observed: a different revision STOPs the setup unless the author has accepted the new one. For the remaining files, the census records the data manifest's sha256 when it first runs the setup, and later setups must reproduce it.
- [ ] The port's tests use synthetic data only.
- [ ] The reviewer checks `LICENCES.md` against the U1 audit and confirms that the branch contains no task data.

## E. Smoke and review (G.1 steps 3–4)

- [ ] Stub-manager smoke on the census host with `run_smoke_campaign` (the declared edits plus one frozen-path diff and one deliberately broken diff as the stub manager's proposals): a frozen-path diff is refused (`refusal: scope_violation`), the baseline run is `ok`, a deliberately broken diff gives `divergent`, and `run_record.json` is complete (outcome, limits, determinism record, code-state hashes, diff provenance).
- [ ] The run record's `determinism.not_forced` list contains only `dataloader_workers` (always: the count is advertised via `AR_NUM_WORKERS`, not enforced), or each further entry is explained in the port report.
- [ ] After a timeout, `process.killed_with` is recorded; no process of the run survives (the runner SIGKILLs the process group after the grace period).
- [ ] A fresh reviewer has accepted the port (spec, wrapper, edits manifest, licence and provenance record, smoke records) before any census measurement.
