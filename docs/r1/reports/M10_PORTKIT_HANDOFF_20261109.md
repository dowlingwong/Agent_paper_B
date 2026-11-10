# M10 steps 0–1 — Track G port kit and diff support: hand-off (9 Nov 2026)

**Written 9 Nov 2026 (about 02:15–03:00 CET; revised about 03:10–03:40 CET after review round 1 and on 10 Nov about 10:30–11:15 CET after review round 2) by a Mac-local worker agent (Claude), AI-assisted, for runbook `MAC_OVERNIGHT_RUNBOOK_20261109.md` §2 (Task 2).** Governing text: `MAC_LOCAL_RUNBOOK_20261104.md` §M10 steps 0–1, `TRACK_G_RUNBOOK.md` §§2–4 (G.1, G.2), `HOREKA_RUNBOOK_20261104.md` HK2 "Needs", RUNBOOK Track G rows G.1/G.2, PLAN §10 R1-BX-D2, D4, D5, R1-BX-REVISIONS (c), (g), R1-BX-PROPOSED-CONFIRM (D4 (E3), REVISIONS (c) (E5)).

Review: **accepted** in round 3 (harness `76bc49f`, paper `f4e09f87`); record `reviews/M10_PORTKIT_REVIEW_20261109.md`, answers `reviews/M10_PORTKIT_REVIEW_ANSWERS_20261109.md`. The two optional round-3 notes (SIGTERM to children that left the group; pass the run's real interpreter to the shadowing check when v2-diff is wired in) are open for later M10 work.

**Status.** Code and tests are committed on the two branches below. Nothing is pushed. Not accepted by an independent reviewer yet: the HoreKa agent must not build on these commits until a fresh reviewer has accepted them (HK2 "Needs": "the Mac agent's M10 step 0 (the shared pieces), reviewed"), and G.2 is pinned in the RUNBOOK pin table only after that review. No server was touched; nothing was measured.

## 1. Commits for the HoreKa agent (after review)

| Repo | Branch | Commit | Content |
|---|---|---|---|
| harness `autoresearch_harness` | `r1-local-trackg-20261109` | `45ada5ab97cca25421c3c721d249d2c108ad2f4e` | Step 0 shared pieces and step 1 diff support (package `autoresearch.trackg`), T0 identity test |
| harness | same | `6a82e80860fcffbc1bb9babfb832a97b078a46ae` | Representative-edit manifest (`scripts/trackg_declare_edits.py`) |
| harness | same | `b457516211ece3aa1c8e3873a2557a8f77f8ccf7` | Stub-manager smoke campaign (`autoresearch.trackg.smoke`) |
| harness | same | `c642b6fbf6ab7a276646244b13ea81b8e12d0e8b` | T0 identity test fails instead of skipping when the base commit is missing |
| harness | same | `aea6405005fdf734962d0ec6910c706c84dc0cc4` | Review round 1 fixes (see the answers file) |
| harness | same | **`76bc49f25258185ae8547f6f04921dd4c5fa036a` (HEAD; use this one)** | Review round 2 fixes (see the answers file) |
| paper `agent_paper_B` | `mac-trackg-20261109` | the commit that adds the answers file (named in the coordinator report; a file cannot name its own commit) | `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` (first `30d93207`, revised after review), index row in `prompts/README.md`, this report, the answers file |

**Harness base.** The runbook says "from `origin/r1`". The local copy of `origin/r1` was stale (`897d83c`, 26 Oct), and the B1 harness pin `a3fedbb` descends from it (checked: `897d83c` is an ancestor of `a3fedbb`). The branch was therefore created from **`a3fedbb`**. Nothing at `a3fedbb` was changed and the pin was not moved; the six commits only add files, or change files they added themselves. The paper branch starts at `origin/mac-int-20261107` (`a15300ca`).

## 2. What was built

All harness changes are additive with respect to `a3fedbb`: `git diff --diff-filter=MDRT --name-only a3fedbb 76bc49f` is empty, and `git diff --name-status a3fedbb..76bc49f` lists 26 files, all `A`, under `src/autoresearch/trackg/`, `tests/trackg/`, `configs/trackg/` and two new scripts. No module outside `src/autoresearch/trackg/` imports the new package. A test checks both, against HEAD and against the working tree.

### Step 0 — shared pieces for the ports (G.1)

| Piece | File | Behaviour |
|---|---|---|
| Node template | `configs/trackg/node_template.yaml`, `src/autoresearch/trackg/node_template.py` | `trackg_node/v1`: `editable_paths`, `frozen_paths` (non-empty; no editable entry covered by a frozen entry after normalisation; `.` refused), run command (`{budget}` placeholder), `metric_name`/`metric_direction`, metric regexes (`metric_regex` and **`loss_regex` required**), **`run_budget` with `kind: steps` or `kind: tokens` and a positive integer**, fixed `workers.dataloader_workers`/`workers.threads`, `selection`, `determinism` (strict booleans), `seed_env`, `allow_new_files` (default false). Strict loader (unknown keys refused). **Wall-clock refusal:** `WallClockBudgetError` is raised for any key whose name contains a time word (`time`, `timeout`, `hour`, `minute`, `second`, `duration`, `deadline`, `wall`, `clock`, `runtime`, `sec`/`min`/`hr` as words) at any depth — including `default_budget.max_wall_clock_hours` and keys under `notes`/`external_benchmark` — and for a `run_command` that passes a time budget (`--time-budget`, `--timeout`, `--max-time`, `--time`, `TIME_BUDGET=…`, `timeout <n>`). String values (free text) are not scanned. `to_base_node_spec()` gives the harness `NodeSpec` view, so the existing scope validator applies unchanged. |
| Base metric parser | `src/autoresearch/trackg/outcome.py` | `RunOutcome` is exactly one of `ok(value)`, `divergent(reason)`, `infrastructure_failure(reason)`; only `ok` carries a (finite) value. Order: infrastructure first (launch error including a failure while applying limits, **timeout**, killed by signal or exit 137/143, no exit status, infrastructure log pattern such as `No space left on device` or Slurm `DUE TO TIME LIMIT`), then **non-finite loss → divergent** (also non-numeric loss tokens containing `nan`/`inf`, such as `tensor(nan)`), a selection-metric match overlapping a test-metric line → divergent (`metric_regex_matches_test_line`), non-zero exit → divergent, **no metric at the budget → divergent**, non-finite or unparsable metric → divergent, budget not reached (if `steps_regex` is declared) → divergent; else `ok`. |
| Deterministic settings | `src/autoresearch/trackg/determinism.py` | Environment: `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTHONHASHSEED=0`, thread variables, `AR_NUM_THREADS`, `AR_NUM_WORKERS`. A `sitecustomize` shim first on the run's `PYTHONPATH` applies, in every Python interpreter of the run: `cudnn.benchmark=False` (and `cudnn.deterministic=True`), `torch.use_deterministic_algorithms(True)` (optional per-node `warn_only`) and `torch.set_num_threads`. The first interpreter writes a record of each setting as `forced` / `not_forced` with the reason. **torch absent is recorded (`torch_absent`), not fatal.** A non-Python command or a shadowed shim is recorded as `shim_not_loaded`. `dataloader_workers` is always listed as `not_forced` (advertised only). |
| Per-run working-copy runner | `src/autoresearch/trackg/runner.py` | Copies the node into `<runs_root>/<run_id>/work` (run ids are never reused; symlinks are kept), optionally applies a diff (step 1), and snapshots the code to `<run_dir>/code` before the run. It runs the budgeted command with these limits: <br>• **GPU by UUID** (indices refused; none = GPUs hidden); <br>• **CPU cap** (`sched_setaffinity`; the list must lie in the process's CPU set, checked before the copy); <br>• **memory cap** (`RLIMIT_DATA`/`RLIMIT_AS`, or `external` with a stated `external_limit` such as `slurm --mem=64G`). <br>**Caps are required**: a run without one needs an explicit `uncapped_reason`, which is recorded with the list of missing caps. **Timeout = factor × measured run time** (default 3; a provisional timeout only for the measuring run, flagged). On timeout it sends SIGTERM to the process group, then after the grace period **SIGKILL to the group if any non-zombie member is still alive**, whatever the shell's state. Processes left after a normal exit are SIGKILLed too. "Group" here means the run's process group **and** its session (a child that left the group with `setpgid` is included; one that called `setsid` is not). `killed_with` and `leftover_processes_killed` are recorded. It writes `run_record.json` (`trackg_run/v1`). Infrastructure failures are not registered as evaluated states. |
| Validation-only selection | `src/autoresearch/trackg/selection.py` | The loader refuses a test-scored spec that does any of the following: does not select on validation; lacks `test_metric_name`; uses the same name or regex for both metrics; has a selection metric that looks like a test metric; or has a `metric_regex` that matches a typical test-metric line (`<test>: 0.5`, `<test>=0.5`, `<test> 0.5`). At run time an overlapping match is divergent (above). `select_best` takes `RunOutcome`s only and ignores non-`ok` runs. The test metric is parsed into a `sealed` block that `manager_view` removes. |
| Representative edits | `src/autoresearch/trackg/declared_edits.py`, `scripts/trackg_declare_edits.py` | Checks 3–5 declared diffs in throw-away copies with the node's own `allow_new_files`: each must apply through the scope validator, must not be inert, and must not duplicate the baseline or another edit. Each entry records its starting (incumbent) code-state hash. Writes a `trackg_representative_edits/v1` manifest once (never overwrites). Nothing is run. |
| Stub-manager smoke | `src/autoresearch/trackg/smoke.py` | Runs the baseline plus a fixed list of v2-diff proposals against the current incumbent, and keeps strict validation improvements of `ok` runs. The next incumbent is the kept run's **pre-run code snapshot**, never the post-run work directory, so no checkpoints or outputs are carried over. Writes a never-overwritten `smoke_ledger.jsonl`. For G.1 step 4 only. |
| Checklist (paper) | `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` | Node spec, fixed-step wrapper, the 3–5 edits declared, hashed and **committed before any measurement**, runner settings per host, smoke and review. |

### Step 1 — diff support (G.2)

`src/autoresearch/trackg/diff_support.py` and `src/autoresearch/trackg/proposal_v2_diff.py`:

- **Application in the per-run copy through the existing scope validator.**
  - Parsing is strict. The only git extended headers allowed are `diff --git`, `index`, `new file mode 100644` and `deleted file mode`. Renames, copies, mode changes, other file modes and binary patches are refused; hunk counts must match; prose is refused.
  - Absolute paths, `..`, quoted paths and **any path with a symlink component** are refused.
  - Then `autoresearch.control_plane.permissions.validate_edit_scope` checks the files touched: **any hunk in a file outside `editable_paths` or inside `frozen_paths` refuses the whole diff**.
  - New files are refused unless the node sets `allow_new_files`. Even then, a new file is refused (`shadowing_module`) if a path component **that does not exist yet in the copy**, or the new module's own name (stem of a `.py/.pyc/.so/.pth` file or package), could shadow an import: `sitecustomize`, `usercustomize`, a name in `sys.stdlib_module_names` or `sys.builtin_module_names`, or a top-level module found on a **fixed import path**. That path is the run interpreter's (`python3`) `sys.path` queried with working directory `/`, without `''`, `/`, the harness's current directory and the copy; it falls back to the harness's `sys.path` with the same exclusions. Existing directories are not checked (they cannot newly shadow anything). The basis is recorded as `shadow_check` (`basis`, `import_path`) in the provenance, and the result does not depend on where the harness was started (tested from four directories).
  - Hunks apply with zero fuzz: at the stated line, or else at the unique exact context match (the offset is recorded). Nothing is written unless every hunk applies.
- **Inert detection.** For `.py` files: the AST (`ast.dump`, attributes off) plus the shebang and PEP 263 coding lines. For other files: the lines without trailing whitespace, blank lines and `#` comment lines, keeping a line-1 shebang. An empty diff is inert. An inert diff is not written.
- **Duplicate detection.** `EvaluatedStates` holds every evaluated state. **The resulting code-state hash decides**: a diff is `duplicate` (`duplicate_kind: code_state`, `duplicate_of`) if and only if its resulting code state — the same normalisation over every editable file; files that are not UTF-8 hashed by their bytes; frozen files and `__pycache__` excluded — was already evaluated; a duplicate is not written. The normalised diff hash (per file and per hunk, the context, removed and added lines in order, each normalised; no headers or line numbers) is **information only**, because diffs with identical context (for example `-U0` diffs, or edits to different copies of a repeated block) share it while reaching different code:
  - `same_diff_hash_other_state`: the same diff hash was evaluated on the same incumbent but this diff reaches a different code state;
  - `seen_diff_other_incumbent`: the same diff hash was evaluated against another incumbent (see §5 question 7).
- **Provenance** (in the run record under `diff`): `schema: manager_proposal/v2-diff`, `diff_text`, `diff_sha256`, `normalised_diff_sha256`, `files_touched`, `scope`, `hunks` (with offsets), `incumbent_code_state_sha256` (+ raw), `code_state_sha256` (+ raw), `inert`/`inert_reason`, `duplicate`/`duplicate_kind`/`duplicate_of`, `same_diff_hash_other_state`, `seen_diff_other_incumbent`, `shadow_check`, `refusal`/`refusal_detail`, `status`.
- **Schema `manager_proposal/v2-diff`**: four string fields in this order — `rationale`, `summary`, `objective`, `diff` — with a structure-only `response_format` and a strict parser. `autoresearch.llm.providers.manager_response_format` is unchanged and still refuses every version except v1 (tested).

### The T0 path is byte-identical (tested)

`tests/trackg/test_trackg_t0_identity.py` with `scripts/trackg_t0_identity_probe.py`:

- **The probe** runs one `manager_proposal/v1` campaign (budget 5) on the CPU node `lr_synthetic`. It uses `LangGraphManager(model="llamacpp/fixture", proposal_schema="manager_proposal/v1")`, the `LocalWorker`, an event store and the default controller. The manager talks to a local fake llama-server (four valid proposals, one malformed reply) that stores every request body byte for byte.
- **The base tree.** The test exports `src`, `nodes/lr_synthetic` and `configs/nodes/lr_synthetic.yaml` of the **base commit `a3fedbb`** with `git archive`. This makes no worktree and changes nothing in the repository. Override the commit with `TRACKG_T0_BASE_COMMIT`. If the commit cannot be exported, the test fails unless `TRACKG_T0_ALLOW_SKIP=1`.
- **Same path.** The probe runs against the base tree and then against the current checkout, **in the same working-directory path**, so absolute paths are identical by construction.
- **Compared unnormalised, byte for byte:** the 5 request bodies and **every other file of the run directory**, except `__pycache__`. That includes the worker artifacts (`artifacts/trial-*/run.log`, `patch.diff`, …), the node copy (including `node/.autoresearch_baseline/**`) and the final `train.py`.
- **Compared byte for byte after normalisation:** `out/trials.jsonl` and `out/events.jsonl`, after textual replacement of the values of exactly these keys, which differ between two runs of the *same* commit: `timestamp`, `timestamp_start`, `timestamp_end`, `event_id` (random id), `latency_ms`, `wall_clock_seconds`, `elapsed_seconds`. A second test pins the normalisation to those keys.
- **Structural test.** A third test covers the T0 configurations the probe does not exercise. It checks that no file of the base commit differs at HEAD (`git diff --diff-filter=MDRT`), and that no module outside `src/autoresearch/trackg/` imports `autoresearch.trackg`.
- **Mutation checks**, done by hand and reverted with `git checkout` (not committed):
  - one extra space in a prompt string the manager sends → fails on `out/requests/000.json`;
  - an extra key in the `decision_made` payload → fails on `out/events.jsonl`;
  - a prefix in the worker's `run.log` → fails on `artifacts/trial-001/run.log`. Before the round-1 fix this mutation passed.
- **After a rebase** onto a newer harness base, set `TRACKG_T0_BASE_COMMIT` to the new merge base. Otherwise legitimate upstream T0 changes will fail these tests.

## 3. Tests

**Environment.** The container's Python 3.13.18, with a private venv `/tmp/trackg_venv`: system site-packages plus `langgraph` 1.2.20, `langchain-core` 1.7.6, `langchain-openai` 1.7.4 and the other harness `langchain-*` dependencies; numpy 2.5.3, pytest 9.1.1, PyYAML 6.0.3, scikit-learn 1.9.1, pandas 3.0.5. **torch is not installed.** A fake `torch` module covers determinism with torch present; real torch is not exercised.

Commands:

```
# harness, new tests
cd <harness worktree> && python -m pytest -p no:cacheprovider -q tests/trackg
# harness, full suite (one module fails to import at baseline, hence the flag)
cd <harness worktree> && python -m pytest -p no:cacheprovider -q -rfE --continue-on-collection-errors
# paper, the 16 test files that import the harness (none is a dry-run test that copies the harness tree)
cd <paper worktree> && AR_HARNESS_ROOT=<harness worktree> python -m pytest -p no:cacheprovider -q -rfE \
  --continue-on-collection-errors $(grep -l "AR_HARNESS_ROOT\|autoresearch" r1/tests/test_*.py)
```

Results:

| Suite | Base (`a3fedbb`, paper `a15300ca`) | After (harness `76bc49f`, paper branch HEAD) |
|---|---|---|
| harness `tests/trackg` | — | **161 passed** |
| harness full | 14 failed (12 + 2 subtests), 476 passed, 1 error | 14 failed (same), **637 passed** (+161 new), 1 error (same) |
| paper, 16 harness-importing files | 5 failed, 152 passed | 5 failed (same), 152 passed |

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

- **The pre-existing failures are environmental:** missing KDD paper and ledger files in this checkout, `R1-BX-D8-CONFIRM`/gate absent, `git commit` inside a fixture without a configured identity, and so on. None involves the new code.
- **Paper tests not run.** The paper-side change is documentation only. The other 65 paper test files (81 in all) do not import the harness and were not run.
- **Untracked report.** The full harness run writes an untracked `paper/tables/artifact_completeness_report.txt`. It was moved to `/tmp/trackg_logs/` each time and is not committed.
- **Logs** and failure-set files are in `/tmp/trackg_logs/`: `harness_baseline_failset.txt`, `paper_baseline_failset.txt`, and for the current state `harness_after_r2_failset.txt` and `paper_after_r2_failset.txt` (logs `harness_after_r2.txt`, `paper_after_r2.txt`). The round-1 files `harness_after_r1_failset.txt` and `paper_after_r1_failset.txt` are kept.

## 4. Known limits (not done in this unit)

- **v2-diff is not wired into a manager or into `run_real_campaign`.** The campaign policy for inert and duplicate diffs and for `seen_diff_other_incumbent` is later M10/M3 work. `run_smoke_campaign` covers only the G.1 smoke.
- **Node specs live in `configs/trackg/nodes/` with their own loader**, not in `configs/nodes/` + `nodes/registry.py` as `TRACK_G_RUNBOOK.md` §2 says. How T1 nodes reach the label-sweep path is decided when v2-diff is wired in.
- **Metric forging is possible by construction.** The metric is parsed from stdout, which editable code shares, so a diff could print a forged metric line. The checklist asks for a frozen-wrapper prefix (`AR_METRIC …`) printed after training and an anchored `metric_regex`. This reduces the risk but does not remove it.
- **Determinism shim.**
  - It imports `torch` at start-up in every Python interpreter of the run, so the import time is part of the measured run time (the timeout basis).
  - Environment variables a task sets in-script before `import torch` (for example `PYTORCH_CUDA_ALLOC_CONF`) no longer take effect.
  - A task script can override the settings after start-up (the checklist forbids it).
  - An environment with its own `sitecustomize` shadows the shim (`shim_not_loaded`).
  - The data-loader worker count is advertised, not enforced.
- **The shadowing check** queries `python3`'s import path as a stand-in for the run's interpreter; a run command that uses another interpreter (for example `.venv/bin/python`) may have modules this check does not see. Existing editable files can still be edited, by design.
- **Process cleanup** covers the run's process group and session. A child that calls `setsid()` itself leaves both and is not killed. In theory, after an empty group's leader PID is freed it could be reused before `killpg`; with sequential PID allocation this is negligible.
- **Wall-clock refusal is conservative.** It also refuses innocent keys in the free-form mappings (`min_lr`, `n_timesteps`, `second_order`, `datetime_split`, `wallet`) and some step-type flags (`--log-every-seconds`, `--eval-timeout`, `--max-time-steps`). The error names the matched word; porters rename such keys or move them into prose or the wrapper.
- **Token budgets:** "budget reached" is checked only for step budgets with a `steps_regex`.
- **Memory caps and CUDA:** `rlimit_as` is unsuitable for CUDA runs, and `rlimit_data` is untested with CUDA here. On HoreKa use `memory_method: external`.
- The runner does not run `setup_command`. Diff application assumes UTF-8 text with `\n` line endings.
- **Not in steps 0–1 and not done:** M10 steps 2–6, and the RUNBOOK pin-table entry for G.2 (after review).

## 5. Open questions (options and recommendation)

1. **A run that exits non-zero without being killed** (Python exception, CUDA OOM).
   - Options: *(a)* `divergent` (implemented; matches E5 "no metric at the fixed budget"); *(b)* a fourth class `crashed`; *(c)* `infrastructure_failure`.
   - **Recommendation: (a).**
   - Note the asymmetry: a **host OOM kill under Slurm** (`slurmstepd: error: … oom_kill`) matches a default infrastructure pattern and is `infrastructure_failure`, while a **CUDA OOM** exception is `divergent`. I recommend keeping it: a CUDA OOM is a property of the proposal on the table's one GPU model, while a cgroup OOM kill depends on the job's `--mem`, which is infrastructure.
   - Paste-ready: `M10：非零退出（未被 kill）按 divergent；Slurm cgroup OOM 按 infrastructure_failure，CUDA OOM 按 divergent，采纳 (a)。`
2. **Wall-clock keys in Track G specs.**
   - Options: *(a)* refused, both keys and run-command flags (implemented); *(b)* allow a campaign safety cap.
   - **Recommendation: (a).**
   - Paste-ready: `M10：Track G 节点禁止任何 wall-clock 预算字段与时间参数，采纳 (a)。`
3. **`torch.use_deterministic_algorithms(True)` can make a baseline crash.**
   - Options: *(a)* strict by default, with per-node `deterministic_warn_only` only on census evidence and review (implemented); *(b)* `warn_only` everywhere; *(c)* record only.
   - **Recommendation: (a).**
   - Paste-ready: `M10：确定性设置默认严格，个别节点凭 census 证据经审查后可用 warn_only，采纳 (a)。`
4. **Docstring-only diffs.**
   - Options: *(a)* not inert (implemented); *(b)* inert.
   - **Recommendation: (a).**
5. **Hunk line numbers that are off.**
   - Options: *(a)* accept the unique exact context match elsewhere and record the offset (implemented); *(b)* exact line numbers only.
   - **Recommendation: (a).**
6. **Harness base commit.**
   - The branch is on `a3fedbb` (the B1 pin) rather than the stale local `origin/r1`.
   - **Recommendation:** keep it. After a rebase, set `TRACKG_T0_BASE_COMMIT` to the new merge base.
7. **The same diff against a different incumbent** (after a keep).
   - Options: *(a)* not a duplicate: run it and report `seen_diff_other_incumbent` (implemented; it reaches a new code state, so it is a new evaluated state under G.2's "against every evaluated state"); *(b)* treat it as a duplicate, like D27's "seen before".
   - **Recommendation: (a).** The campaign policy can still choose to skip it using the reported field.
   - Paste-ready: `M10：同一 diff 在不同 incumbent 上不算重复，记录 seen_diff_other_incumbent，采纳 (a)。`
8. **A proposal that makes training more than 3× slower, or makes it hang.**
   - Such a run is `infrastructure_failure/timeout`, and infrastructure failures are rerun, so without a cap it would be rerun indefinitely.
   - Options: *(a)* the campaign caps reruns: after 2 timeouts of the same code state the proposal is `divergent` with reason `timeout_repeated`; *(b)* treat every timeout as divergent; *(c)* no cap.
   - **Recommendation: (a)**, implemented in the campaign path when v2-diff is wired in (not in this kit).
   - Paste-ready: `M10：同一代码状态两次超时后判为 divergent（timeout_repeated），采纳 (a)。`

## 6. Files

Harness (`r1-local-trackg-20261109`, all new relative to `a3fedbb`):

- `configs/trackg/node_template.yaml`
- `scripts/trackg_t0_identity_probe.py`, `scripts/trackg_declare_edits.py`
- `src/autoresearch/trackg/{__init__,node_template,outcome,determinism,runner,selection,diff_support,proposal_v2_diff,declared_edits,smoke}.py`
- `tests/trackg/{__init__,fixtures,test_trackg_node_template,test_trackg_outcome,test_trackg_runner,test_trackg_selection,test_trackg_diff_support,test_trackg_proposal_v2_diff,test_trackg_declared_edits,test_trackg_smoke,test_trackg_t0_identity,test_trackg_review_round1,test_trackg_review_round2}.py`

Paper (`mac-trackg-20261109`):

- `docs/r1/prompts/TRACKG_PORT_CHECKLIST.md` (new)
- `docs/r1/prompts/README.md` (one index row)
- this report
- `docs/r1/reviews/M10_PORTKIT_REVIEW_ANSWERS_20261109.md`
