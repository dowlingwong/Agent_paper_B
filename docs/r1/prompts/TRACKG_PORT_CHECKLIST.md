# Track G port checklist — declaring a node and its 3–5 representative edits

**Written 9 Nov 2026 by a Mac-local worker agent (Claude), AI-assisted, for M10 step 0.** Not independently reviewed yet (Review: pending, see `reports/M10_PORTKIT_HANDOFF_20261109.md`). This file authorizes nothing: RUNBOOK Track G (G.1, G.1b), `TRACK_G_RUNBOOK.md` §2–§4, `HOREKA_RUNBOOK_20261104.md` HK2 and the PLAN §10 rows govern (R1-BX-D4, D5, R1-BX-REVISIONS (c), (g), R1-BX-PORTING-CONFIRM, R1-BX-PROPOSED-CONFIRM). Where they differ, the dated PLAN rows win.

**Who uses it.** The HoreKa agent, once per ported task, on its own port branch (proposed `hk2-trackg-<date>`), built on the harness commits named in the hand-off. Each port is reviewed by a fresh agent before use; the reviewer ticks this list too.

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

- [ ] `name`, `description`, `suite`, `domain` filled; the description says what the fixed budget means for this task.
- [ ] `editable_paths` lists only what a diff may touch (for example `train.py`, a `model/` directory).
- [ ] `frozen_paths` lists the evaluator, the data loader, the metric code, the data, `prepare.py`-type scripts **and the fixed-step wrapper itself**. It is not empty, and no path is both editable and frozen.
- [ ] `run_budget` is `kind: steps` or `kind: tokens` with a positive integer. **No wall-clock budget** anywhere (R1-BX-D5): the loader refuses any wall-clock key, including `default_budget.max_wall_clock_hours`. A task whose own script has a wall-clock budget (autoresearch) gets a fixed-step wrapper.
- [ ] Label runs take about 1–2 min at the budget on the table's GPU model; closed-loop evaluation runs up to about 5 min (R1-BX-D5). The value is fixed before the census and not changed afterwards without a new review.
- [ ] `workers.dataloader_workers` and `workers.threads` are fixed integers; the wrapper reads `AR_NUM_WORKERS` (and does not choose its own count).
- [ ] `metric.metric_regex` matches the **validation** metric line the wrapper prints at the end (one capture group; the last match counts). `metric_direction` is right.
- [ ] `metric.loss_regex` matches every training-loss line the wrapper prints, so a non-finite loss is caught as `divergent`.
- [ ] `metric.steps_regex` (recommended for step budgets) matches the step counter, so a run that stops before the budget is `divergent` (`budget_not_reached`).
- [ ] Extra `metric.infrastructure_log_patterns` only for messages that cannot be caused by a proposal (disk, file system, scheduler). Never CUDA OOM or a Python exception: those are the proposal's (divergent).
- [ ] `selection`: for a test-scored task `test_scored: true`, `selection_split: validation`, `test_metric_name` set and different from `metric_name` (R1-TRACKG-ROLE). The test metric is never printed under the validation metric's name.
- [ ] `determinism` left at the defaults (`cudnn_benchmark: false`, `deterministic_algorithms: true`, `cublas_workspace_config: ":4096:8"`). `deterministic_warn_only: true` only if the census shows the baseline cannot run otherwise; say so in the port report.
- [ ] `seed_env` names the variables the wrapper reads for the training and split seeds.

## B. Fixed-step wrapper and task assets

- [ ] Native port in the harness venv where possible (R1-BX-REVISIONS (g)); a container only if the task ships only as an image (Apptainer, `.sif` sha256 in provenance; M10 step 4, not in this kit).
- [ ] The wrapper runs exactly `run_budget.value` steps (or tokens) and then prints the validation metric; it reads the budget from `{budget}` in the run command or `AR_BUDGET_VALUE`.
- [ ] It reads the training and split seeds from `seed_env`; seeds never appear in a proposal.
- [ ] It does **not** set `torch.backends.cudnn.benchmark = True` or turn deterministic algorithms off (that would override the runner's settings).
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
- [ ] CPU list and memory cap set. Under Slurm, use `memory_method: external` (the job's `--mem` cgroup enforces it; the record says so); `rlimit_data` is for hosts without a cgroup cap.
- [ ] Timeout = 3 × the measured run time at the budget (`measured_run_seconds`). Only the first, measuring run may use `provisional_timeout_seconds`, and its record says so.
- [ ] One GPU model per label table (R1-BX-D5); the placement is recorded with each run.

## E. Smoke and review (G.1 steps 3–4)

- [ ] Stub-manager smoke on the census host with `run_smoke_campaign` (the declared edits plus one frozen-path diff and one deliberately broken diff as the stub manager's proposals): a frozen-path diff is refused (`refusal: scope_violation`), the baseline run is `ok`, a deliberately broken diff gives `divergent`, and `run_record.json` is complete (outcome, limits, determinism record, code-state hashes, diff provenance).
- [ ] The run record's `determinism.not_forced` list is empty, or each entry is explained in the port report.
- [ ] A fresh reviewer has accepted the port (spec, wrapper, edits manifest, smoke records) before any census measurement.
