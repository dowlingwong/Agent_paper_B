# M10 steps 0–1 — Track G port kit and diff support: hand-off (9 Nov 2026)

**Written 9 Nov 2026 (about 02:15–03:00 CET) by a Mac-local worker agent (Claude), AI-assisted, for runbook `MAC_OVERNIGHT_RUNBOOK_20261109.md` §2 (Task 2).** Governing text: `MAC_LOCAL_RUNBOOK_20261104.md` §M10 steps 0–1, `TRACK_G_RUNBOOK.md` §§2–4 (G.1, G.2), `HOREKA_RUNBOOK_20261104.md` HK2 "Needs", RUNBOOK Track G rows G.1/G.2, PLAN §10 R1-BX-D2, D4, D5, R1-BX-REVISIONS (c), (g), R1-BX-PROPOSED-CONFIRM (D4 (E3), REVISIONS (c) (E5)).

Review: pending

**Status.** Code and tests are committed on the two branches below. Nothing is pushed. Not independently reviewed yet: the HoreKa agent must not build on these commits until a fresh reviewer has accepted them (HK2 "Needs": "the Mac agent's M10 step 0 (the shared pieces), reviewed"), and G.2 is pinned in the RUNBOOK pin table only after that review. No server was touched; nothing was measured.

## 1. Commits for the HoreKa agent (after review)

| Repo | Branch | Commit | Content |
|---|---|---|---|
| harness `autoresearch_harness` | `r1-local-trackg-20261109` | `45ada5ab97cca25421c3c721d249d2c108ad2f4e` | Step 0 shared pieces and step 1 diff support (package `autoresearch.trackg`), T0 identity test |
| harness | same | `6a82e80860fcffbc1bb9babfb832a97b078a46ae` | Representative-edit manifest (`scripts/trackg_declare_edits.py`) |
| harness | same | **`b457516211ece3aa1c8e3873a2557a8f77f8ccf7` (HEAD; use this one)** | Stub-manager smoke campaign (`autoresearch.trackg.smoke`) |
| paper `agent_paper_B` | `mac-trackg-20261109` | **`30d93207688d60f665ccb12fadd59b49b4868fa1`** | `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md`, index row in `prompts/README.md` |

**Harness base.** The runbook says "from `origin/r1`". The local copy of `origin/r1` was stale (`897d83c`, 26 Oct), and the B1 harness pin `a3fedbb` descends from it (checked: `897d83c` is an ancestor of `a3fedbb`). The branch was therefore created from **`a3fedbb`**. Nothing at `a3fedbb` was changed and the pin was not moved; the three commits only add files. The paper branch starts at `origin/mac-int-20261107` (`a15300ca`).

## 2. What was built

All harness code is additive: **no existing harness file is modified** (`git diff --stat a3fedbb..b457516` lists only new files under `src/autoresearch/trackg/`, `tests/trackg/`, `configs/trackg/` and two new scripts). Nothing in the T0 path imports the new package.

### Step 0 — shared pieces for the ports (G.1)

| Piece | File | Behaviour |
|---|---|---|
| Node template | `configs/trackg/node_template.yaml`, `src/autoresearch/trackg/node_template.py` | `trackg_node/v1`: `editable_paths`, `frozen_paths` (must be non-empty, no overlap), run command (`{budget}` placeholder), `metric_name`/`metric_direction`, metric regexes, **`run_budget` with `kind: steps` or `kind: tokens` and a positive integer**, fixed `workers.dataloader_workers`/`workers.threads`, `selection`, `determinism`, `seed_env`. Strict loader (unknown keys refused). **Any wall-clock-looking key at any depth is refused** (`WallClockBudgetError`), including `default_budget.max_wall_clock_hours`. `to_base_node_spec()` gives the harness `NodeSpec` so the existing scope validator applies unchanged. |
| Base metric parser | `src/autoresearch/trackg/outcome.py` | `RunOutcome` is exactly one of `ok(value)`, `divergent(reason)`, `infrastructure_failure(reason)`; the constructor enforces that only `ok` carries a (finite) value. Order: infrastructure first (launch error, **timeout**, killed by signal or exit 137/143, no exit status, infrastructure log pattern such as `No space left on device` or Slurm `DUE TO TIME LIMIT`), then **non-finite loss → divergent**, non-zero exit → divergent, **no metric at the budget → divergent**, non-finite or unparsable metric → divergent, budget not reached (if `steps_regex` is declared) → divergent; else `ok`. |
| Deterministic settings | `src/autoresearch/trackg/determinism.py` | Environment: `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTHONHASHSEED=0`, `OMP/MKL/OPENBLAS/NUMEXPR/VECLIB` threads, `AR_NUM_THREADS`, `AR_NUM_WORKERS`. A `sitecustomize` shim put first on the run's `PYTHONPATH` sets `cudnn.benchmark=False` (and `cudnn.deterministic=True`), `torch.use_deterministic_algorithms(True)` (optional per-node `warn_only`), `torch.set_num_threads`, in every Python interpreter of the run, and the first interpreter writes a record of each setting as `forced` / `not_forced` with the reason. **torch absent is recorded (`torch_absent`), not fatal.** A non-Python command or a shadowed shim is recorded as `shim_not_loaded`. |
| Per-run working-copy runner | `src/autoresearch/trackg/runner.py` | Copies the node into `<runs_root>/<run_id>/work` (run ids never reused; symlinks kept as symlinks), optionally applies a diff there (step 1), runs the budgeted command with **GPU by UUID** (`CUDA_VISIBLE_DEVICES=GPU-…`/`MIG-…`; indices refused; none = GPUs hidden), **CPU cap** (`sched_setaffinity`), **memory cap** (`RLIMIT_DATA`, `RLIMIT_AS`, or `external` for a scheduler cgroup, recorded), **timeout = factor × measured run time** (default factor 3; a provisional timeout only for the measuring run, flagged), process-group kill on timeout, seeds via `seed_env`, and writes `run_record.json` (`trackg_run/v1`: outcome, limits, applied environment, determinism record, incumbent and resulting code-state hashes, diff provenance, log sha256). Infrastructure failures are not registered as evaluated states (they are rerun, not deduplicated). |
| Validation-only selection | `src/autoresearch/trackg/selection.py` | The loader refuses a test-scored spec that does not select on the validation split, lacks `test_metric_name`, uses the same name or regex for both, or whose selection metric looks like a test metric. `select_best` takes `RunOutcome`s only (never raw metric dicts) and ignores non-`ok` runs. The test metric is parsed into a `sealed` block that `manager_view` removes. |
| Representative edits | `src/autoresearch/trackg/declared_edits.py`, `scripts/trackg_declare_edits.py` | Checks 3–5 declared diffs in throw-away copies (each must apply through the scope validator, not be inert, not duplicate the baseline or another edit) and writes a `trackg_representative_edits/v1` manifest once (never overwrites), printing its sha256 and each edit's sha256. Nothing is run. |
| Stub-manager smoke | `src/autoresearch/trackg/smoke.py` | Baseline plus a fixed list of v2-diff proposals against the current incumbent; keeps strict validation improvements of `ok` runs; never-overwritten `smoke_ledger.jsonl`. For G.1 step 4 only. |
| Checklist (paper) | `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` | Node spec, fixed-step wrapper, the 3–5 edits declared, hashed and **committed before any measurement**, runner settings per host, smoke and review. |

### Step 1 — diff support (G.2)

`src/autoresearch/trackg/diff_support.py` and `src/autoresearch/trackg/proposal_v2_diff.py`:

- **Application in the per-run copy through the existing scope validator.** `apply_diff` parses the unified diff strictly (git extended headers allowed only for `diff --git`, `index`, new/deleted file mode; renames, copies, mode changes and binary patches refused; hunk counts must match; prose around the diff refused), refuses absolute paths, `..`, quoted paths and **any path with a symlink component** (a symlinked directory inside an editable path could otherwise reach a frozen path), and then calls `autoresearch.control_plane.permissions.validate_edit_scope` on the files touched: **any hunk in a file outside `editable_paths` or inside `frozen_paths` refuses the whole diff**. Hunks apply with zero fuzz: at the stated line, or else at the unique exact match of their context (the offset is recorded; zero or several matches refuse). Nothing is written unless every hunk applies.
- **Inert detection.** For `.py` files the AST (`ast.dump`, attributes off) of each touched file is compared with the incumbent's; other files are compared after removing trailing whitespace, blank lines and `#` comment lines. An empty diff is inert. An inert diff is not written (reasons `empty_diff`, `no_change…`, `normalised_equal…`, suffix `_ast_equal_to_incumbent` when a Python file is involved).
- **Duplicate detection.** `EvaluatedStates` holds every evaluated state of the campaign: the normalised diff hash (removed and added lines per file, without headers, line numbers, context, blank or comment lines, trailing whitespace) and the resulting code-state hash (the same normalisation over every editable file of the copy, frozen files and `__pycache__` excluded). A diff matching either is reported `duplicate` with `duplicate_kind` and `duplicate_of`, and is not written.
- **Provenance** (in the run record under `diff`): `schema: manager_proposal/v2-diff`, `diff_text`, `diff_sha256`, `normalised_diff_sha256`, `files_touched`, `scope`, `hunks` (with offsets), `incumbent_code_state_sha256` (+ raw), `code_state_sha256` (+ raw), `inert`/`inert_reason`, `duplicate`/`duplicate_kind`/`duplicate_of`, `refusal`/`refusal_detail`, `status`.
- **Schema `manager_proposal/v2-diff`**: four string fields in this order — `rationale`, `summary`, `objective`, `diff` — with a structure-only `response_format` (`manager_proposal_v2_diff`) and a strict parser (a leading `<think>` block is removed; nothing else is repaired). It lives in its own module; `autoresearch.llm.providers.manager_response_format` is unchanged and still refuses every version except v1 (tested).

### The T0 path is byte-identical (tested)

`tests/trackg/test_trackg_t0_identity.py` with `scripts/trackg_t0_identity_probe.py`:

- The probe runs one `manager_proposal/v1` campaign (budget 5) on the CPU node `lr_synthetic` with `LangGraphManager(model="llamacpp/fixture", proposal_schema="manager_proposal/v1")`, the `LocalWorker`, an event store and the default controller, against a local fake llama-server that returns four valid proposals and one malformed reply and stores every request body byte for byte.
- The test exports `src`, `nodes/lr_synthetic` and `configs/nodes/lr_synthetic.yaml` of the **base commit `a3fedbb`** with `git archive` into a temporary directory (no worktree, no change to the repository; override with `TRACKG_T0_BASE_COMMIT`), runs the probe against that tree and then against the current checkout, **in the same working-directory path** (the first run's directory is renamed before the second starts), so absolute paths are identical by construction.
- Compared **unnormalised, byte for byte**: all 5 request bodies (`requests/000.json` … `004.json`) and the final `train.py`.
- Compared byte for byte **after textual replacement of the values of exactly these keys**, which differ between two runs of the *same* commit (checked by running the probe twice at HEAD): `timestamp`, `timestamp_start`, `timestamp_end`, `event_id` (random id), `latency_ms`, `wall_clock_seconds`, `elapsed_seconds`. This applies to `trials.jsonl` and `events.jsonl`; key order, spacing and every other byte are compared. A second test pins the normalisation to those keys only.
- Mutation checks done by hand (then reverted with `git checkout`, not committed): adding one space to a prompt string the manager sends made the test fail on `requests/000.json`; adding a key to the `decision_made` event payload made it fail on `events.jsonl`. (A first mutation of a prompt line that this code path does not send did not fail the test, as expected.)

## 3. Tests

Environment: the container's Python 3.13.18 with a private venv `/tmp/trackg_venv` (system site-packages plus `langgraph` 1.2.20, `langchain-core` 1.7.6, `langchain-openai` 1.7.4 and the other harness `langchain-*` dependencies, which the container lacked); numpy 2.5.3, pytest 9.1.1, PyYAML 6.0.3, scikit-learn 1.9.1, pandas 3.0.5; **torch not installed** (determinism with torch present is covered by a fake `torch` module in one test; real torch is not exercised).

Commands:

```
# harness, new tests
cd <harness worktree> && python -m pytest -p no:cacheprovider -q tests/trackg
# harness, full suite (one module fails to import at baseline, hence the flag)
cd <harness worktree> && python -m pytest -p no:cacheprovider -q -rfE --continue-on-collection-errors
# paper, the 17 test files that import the harness (none is a dry-run test that copies the harness tree)
cd <paper worktree> && AR_HARNESS_ROOT=<harness worktree> python -m pytest -p no:cacheprovider -q -rfE \
  --continue-on-collection-errors $(grep -l "AR_HARNESS_ROOT\|autoresearch" r1/tests/test_*.py)
```

Results:

| Suite | Base (`a3fedbb`, paper `a15300ca`) | After (harness `b457516`, paper `30d93207`) |
|---|---|---|
| harness `tests/trackg` | — | **102 passed** |
| harness full | 14 failed (12 + 2 subtests), 476 passed, 1 error | 14 failed (same), **578 passed** (+102 new), 1 error (same) |
| paper, 17 harness-importing files | 5 failed, 152 passed | 5 failed (same), 152 passed |

**Failure sets — identical before and after** (harness, 15 entries):

```
ERROR tests/test_legacy_noop_skip.py                      (ModuleNotFoundError: src.autoresearch_worker)
FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_connection_refused_is_a_transport_error
FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_dropped_request_is_retried_once_with_the_same_seed
FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm
FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist
FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns
FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns
FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist
FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance
FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance
FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance
FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links
FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance
SUBFAILED(node='openml_blood_transfusion') tests/stage2/test_r1_l8.py::TestOpenmlPool22Oct::test_dataset_json_and_template_files
SUBFAILED(node='openml_sonar') tests/stage2/test_r1_l8.py::TestOpenmlPool22Oct::test_dataset_json_and_template_files
```

(paper, 5 entries):

```
FAILED r1/tests/test_c3_evidence_guards.py::test_evidence_environment_rejects_harness_import_spoof
FAILED r1/tests/test_c3_evidence_guards.py::test_evidence_environment_rejects_wrong_locked_sklearn
FAILED r1/tests/test_c3_evidence_guards.py::test_evidence_plan_covers_all_and_rejects_stale_table
FAILED r1/tests/test_c3_evidence_guards.py::test_replay_detects_deleted_rows_despite_self_signed_table
FAILED r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun
```

The pre-existing failures are environmental (missing KDD paper and ledger files in this checkout, `R1-BX-D8-CONFIRM`/gate absent, `git commit` inside a fixture without a configured identity, and so on); none involves the new code. The paper-side change is documentation only; the other 65 paper test files do not import the harness and were not run. The test `test_artifact_completeness_and_manifest` writes an untracked `paper/tables/artifact_completeness_report.txt` into the harness worktree on every full run; it was moved out to `/tmp` each time and is not committed.

## 4. Known limits (not done in this unit)

- **v2-diff is not wired into a manager or into `run_real_campaign`.** The schema, parser, application, inert/duplicate detection and provenance exist; a `LangGraphManager` prompt for diffs, the label-sweep/closed-loop path for T1 nodes, and the campaign policy for inert and duplicate diffs (skip and count, as D27 does for no-ops, or something else) are later M10/M3 work. `run_smoke_campaign` covers only the G.1 smoke.
- **Token budgets:** the parser checks "budget reached" only for step budgets with a `steps_regex`; a token-budget wrapper must itself refuse to print the metric before the budget.
- The determinism shim acts at interpreter start; a task script can override it (the checklist forbids that). An environment with its own `sitecustomize` shadows the shim (recorded as `shim_not_loaded`).
- `RLIMIT_DATA`/`RLIMIT_AS` and CUDA: CUDA reserves large virtual mappings, so `rlimit_as` is unsuitable on GPU runs; `rlimit_data` is untested with CUDA here; on HoreKa use `memory_method: external` (Slurm `--mem`).
- The runner does not run `setup_command`; ports run it once per host.
- Diff application assumes UTF-8 text with `\n` line endings (CRLF files would not match).
- Not in steps 0–1 and not done: M10 step 2 (S1.1 edit–edit interaction analysis for diffs), step 3 (divergence class in the trial record and `r1/c3/labels`), step 4 (Apptainer option), step 5 (API proposer), step 6 (drafts); the RUNBOOK pin-table entry for G.2 (after review).

## 5. Open questions (options and recommendation)

1. **A run that exits non-zero without being killed** (Python exception, CUDA OOM): *(a)* `divergent` (implemented; matches E5 "no metric at the fixed budget"); *(b)* a fourth class `crashed`; *(c)* `infrastructure_failure`. **Recommendation: (a)**, with host-level messages caught by `infrastructure_log_patterns`; since one GPU model per table (R1-BX-D5), an OOM is a property of the proposal on that table. Paste-ready: `M10：非零退出（未被 kill）按 divergent 处理，采纳 (a)。`
2. **`default_budget.max_wall_clock_hours` in Track G specs:** *(a)* refused like any wall-clock key (implemented); *(b)* allowed as a campaign safety cap. **Recommendation: (a)**: a time cap makes the number of trials host-dependent; the per-run timeout already guards hangs. Paste-ready: `M10：Track G 节点禁止任何 wall-clock 预算字段，采纳 (a)。`
3. **`torch.use_deterministic_algorithms(True)` can make a baseline crash** (an op without a deterministic kernel → `divergent`): *(a)* strict by default, per-node `deterministic_warn_only: true` only with census evidence and the port review's acceptance (implemented); *(b)* `warn_only` everywhere; *(c)* not forced at all, only recorded. **Recommendation: (a).** Paste-ready: `M10：确定性设置默认严格，个别节点凭 census 证据经审查后可用 warn_only，采纳 (a)。`
4. **Docstring-only diffs:** *(a)* not inert (implemented; the AST includes docstrings, which code can read); *(b)* inert. **Recommendation: (a).**
5. **Hunk line numbers that are off** (common in LLM diffs): *(a)* accept only a unique exact context match elsewhere, record the offset (implemented); *(b)* exact line numbers only. **Recommendation: (a)**; the offset is in provenance and D28 liveness will show how often it is used.
6. **Harness base commit:** the branch is on `a3fedbb` (the B1 pin), not on the stale local `origin/r1` (`897d83c`, an ancestor). **Recommendation:** keep; if the author wants a different base, rebase the three additive commits (no conflicts are possible: only new files).

## 6. Files

Harness (`r1-local-trackg-20261109`, all new):
`configs/trackg/node_template.yaml`; `scripts/trackg_t0_identity_probe.py`; `scripts/trackg_declare_edits.py`; `src/autoresearch/trackg/{__init__,node_template,outcome,determinism,runner,selection,diff_support,proposal_v2_diff,declared_edits,smoke}.py`; `tests/trackg/{__init__,fixtures,test_trackg_node_template,test_trackg_outcome,test_trackg_runner,test_trackg_selection,test_trackg_diff_support,test_trackg_proposal_v2_diff,test_trackg_declared_edits,test_trackg_smoke,test_trackg_t0_identity}.py`.

Paper (`mac-trackg-20261109`): `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` (new), `docs/r1/prompts/README.md` (one index row), this report.
