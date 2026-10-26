# Deepthought Phase 2 recheck at the restart pins — 26 October 2026

AI-assisted (Claude, implementation agent on deepthought). **ENGINEERING_ONLY, not evidence.**
Authority: `docs/r1/PLAN.md` §10 (R1-DT-RESTART, R1-DT-TESTGATE, R1-DT-SCRATCH, R1-DT-PIN, R1-SCHEMA),
the restart prompt, `docs/r1/prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phase 2.

Phase 2 was redone at the new pins because batch B (A.10, llama.cpp backend) is now merged on `main`
and harness `r1` has moved to `897d83c`.

## 1. Pins verified

| Item | Value | Check |
|---|---|---|
| Host | `deepthought` (`deepthought.etp.kit.edu`), RHEL 8.10, 40 CPUs | `platform.node().split('.')[0]` = `deepthought`, which the runner compares against `allowed_hosts` |
| Paper branch | `dt-sweep1-20261026`, from `origin/main` | created from `origin/main` `7611338`; `origin/main` later moved to `fc3e0da` (Track P / Ada rows) and was merged in |
| Paper `main` HEAD | `fc3e0dab0e38256e8ce77d2040fb23138ceeb947` | recorded as the Phase-4-completion head (R1-DT-PIN); see the caveat in §6 |
| Harness | `897d83c8efa364ec2fdd37288241cc42e01d7274` on branch `r1`, fast-forwarded from `origin/r1` | equals `r1/scripts/HARNESS_PIN_C3` on `main`; also equals `HARNESS_PIN_EXAM` |
| llama.cpp backend merged | yes | `r1/scripts/llama_server_instance.py`, `llamacpp_probe.py`, `c3_fake_llama_server.py` and the `backend: llamacpp` path are on `main` (`d560490`, `607f78e`, `adab041`, `8122600`) |
| Cherry-picks | six 25 Oct documentation commits | `fc7b2a8 7a8ee19 bc380b9 84a6628 f968de8 75c8f5c` → `a83d2ab c465a8f bbe80ca e4ead41 c645bb9 6d49ddf`; the five report blobs are byte-identical to `origin/dt-sweep1-20261025`; the six STATUS conflicts were resolved by keeping both sides, the cherry-picked entries below the newer `main` entries, with no text changed |

The old branch `dt-sweep1-20261025` was neither worked on nor merged.

## 2. Repository and runtime locations (R1-DT-SCRATCH)

| Role | Path |
|---|---|
| Paper checkout (sweep clone) | `/ceph/dwong/agent_paper_B` |
| Harness checkout | `/ceph/dwong/r1_prepare_20261025/autoresearch_harness` (branch `r1`, `897d83c`) |
| Locked environment | `/ceph/dwong/r1_prepare_20261025/venv` (uv 0.12.5, managed CPython 3.13.15) |
| llama.cpp build | `/ceph/dwong/opt/llama.cpp/build-gcc13/bin/llama-server` |
| GGUF | `/ceph/dwong/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf` |
| Scratch, `TMPDIR`, logs, probe output | `/tmp/r1_sweep1_dwong_20261026/` (**local disk**, per R1-DT-SCRATCH) |

Durable sweep outputs stay where the runner config puts them; nothing durable was written to Ceph by this phase.

**Headroom at the start of this phase and after it:** Ceph `ceph.quota.max_files` = 500,000 with
`ceph.dir.rfiles` = 269,574 at the start and 275,839 at the end, i.e. **45 % file-count headroom**
(the 10 % floor is far away; on 25 Oct the count was 421,393, so ~150,000 files were freed since).
`ceph.quota.max_bytes` = 0 (no byte quota); `/ceph` reports 303 TiB available, far above the 50 GiB floor.
Local `/` (which carries `/tmp`) has 119 GiB available.

## 3. Environment

`python -VV`: `3.13.15 (main, Aug 14 2026, 15:34:59) [Clang 22.1.3]`.
Harness lock `uv.lock` sha256 `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090`
(unchanged from the 25 Oct preparation).

| Component | Version | Note |
|---|---|---|
| scikit-learn | 1.8.0 | matches the 22 Oct E1 manifest |
| numpy | 2.4.4 | matches |
| pandas | 3.0.3 | matches |
| scipy | 1.17.1 | matches |
| lightgbm | 4.7.0 | test extra, installed `--no-deps` on 25 Oct |
| narwhals | 2.27.1 | **added here**, see §4 finding 2 |
| langchain-core / langgraph / openai | 1.3.3 / 1.1.10 / 2.36.0 | |

Python 3.13.16 (the common-run manifest's patch) has no downloadable managed build on this host;
3.13.15 is used, as on 25 Oct. The metric libraries match exactly.

### Two environment findings that change how the sweep must be launched

1. **`PATH` must put the venv's `bin` first.** The harness `LocalWorker` runs the node's training
   command as bare `python3`. On this host `python3` on the default `PATH` is
   `/home/dwong/anaconda3/bin/python3` with **scikit-learn 1.5.1**, not the locked 1.8.0. Three harness
   tests failed for exactly this reason (§4) and passed once
   `/ceph/dwong/r1_prepare_20261025/venv/bin` was first on `PATH`. A sweep launched without that
   `PATH` would run its worker runs under the wrong scikit-learn, which STATUS 22 Oct records as
   changing tree-model metrics. The launch environment file sets it.
2. **`narwhals` was missing.** `lightgbm==4.7.0` was installed with `--no-deps` on 25 Oct, so
   `import lightgbm` raised `ModuleNotFoundError: No module named 'narwhals'`. `narwhals==2.27.1` was
   installed with `--no-deps` (it has no dependencies of its own); the four metric library versions
   were re-verified unchanged afterwards. This is the same gap the 25 Oct report found and had worked
   around only inside an isolated copy.

## 4. Test suites

Run with `TMPDIR` on local disk and the venv `bin` first on `PATH`.

### Harness suite — at the accepted baseline

`PYTHONPATH=src python -m pytest --continue-on-collection-errors -q -p no:cacheprovider tests`
→ **454 passed, 8 failed, 1 collection error, 55 subtests passed, 111.0 s.**

This equals the coordinating session's 26 Oct baseline for `897d83c` (454 passed / 8 failed / 1
collection error). The failing set is the accepted environmental one: three
`test_artifact_completeness_and_manifest.py` tests and five `test_kdd_paper_sections.py` tests (all
about the KDD manuscript artifacts and ledgers that are not in this checkout), plus the expected
`tests/test_legacy_noop_skip.py` collection error (`src.autoresearch_worker` does not exist on `r1`).
`test_checked_in_report_contains_all_plan_campaigns`, the one extra failure on 25 Oct, passes here;
the suite rewrites the untracked `paper/tables/artifact_completeness_report.txt`, as the batch B
handoff documents, so this test's outcome depends on run order. Nothing in the failing set touches
the runner, the backend or the C3 pipeline.

An earlier run of the suite showed three further failures —
`tests/stage2/test_r1_defects.py::TestSeedInjection::test_same_seed_reproduces_and_different_seed_changes`,
`tests/stage2/test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`,
`tests/stage2/test_r1_l7.py::TestRestoreAudit::test_replay_reproduces_metric_bit_for_bit`. Diagnosis:
all three run a real `LocalWorker` campaign whose `python3 train.py` failed under anaconda's
scikit-learn 1.5.1 (finding 1). With the venv `bin` first on `PATH` all three pass (8.1 s). No
assertion, seed, fixture or deadline was changed.

### Paper suite — baseline plus the two accepted deadline failures

`python -m pytest -q -p no:cacheprovider --continue-on-collection-errors r1/tests`
→ **528 passed, 6 failed, 25 skipped, 4 collection errors, 1,073.7 s.**

| Failure / error | Verdict |
|---|---|
| `test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` | the known accepted baseline failure |
| `test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_retry_and_permanent_failure` | **R1-DT-TESTGATE (a)**, environmental; see §5 |
| `test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_from_the_deepthought_config` | **R1-DT-TESTGATE (a)**, environmental; see §5 |
| `test_c3_sidecar.py::test_refuses_an_adapter_whose_sha256_differs_from_the_pin` | environmental: `r1/c3/serve.py` imports `torch`, absent from this environment |
| `test_trackp_losses_metrics.py`, `test_trackp_model.py`, `test_trackp_sidecar_loader.py`, `test_trackp_trainer.py` (collection errors) | environmental: `import torch` |

The five torch-dependent items are Track P / sidecar code. Track P runs on the portal and, since
26 Oct evening, on TASL-7 (R1-TASL7-TRACKP); none of it is in the C3 sweep path, and `torch` is not
in the harness lock. **Deliberate decision not to install torch here:** it would add a large
dependency outside the lock to the environment the sweep's own metrics are computed in, against the
Phase 2 rule that the locked versions must match exactly. Recorded as an environmental gap, not
fixed.

Two earlier paper-suite failures were engineering problems and are fixed:

- `test_c3_control_dryrun.py::test_control_dryrun_end_to_end` failed with
  `STOP: runner exited (rc 1) before the interruption`; the runner log showed
  `ModuleNotFoundError: No module named 'narwhals'` from `r1/c3/arms.py` → `lightgbm`. After
  installing `narwhals==2.27.1` it **passes** (154.2 s).
- `test_trackp_soft_label_v2.py::test_existing_pilot_table_rebuilt_under_v1_is_byte_identical` failed
  in the same run and **passes** after the same fix.

Two tests in `r1/tests/test_c3_sweep_deepthought_config.py` asserted that the deepthought config is
still a *draft* carrying exactly the nine `TODO_VERIFY_ON_HOST` values. Phase 4 fills them, so those
assertions no longer describe the file. They were updated on this branch (the draft assertions now
apply to the still-open zhixu portal config) and a new test asserts that the completed deepthought
config has no placeholder, passes `--check-config`, and carries
`proposal_schema = manager_proposal/v1`. The module passes: 6 tests. No design assertion (nodes,
instances, W, memory modes, audit seeds, watchdog, `min_live_nodes`) was weakened.

## 5. R1-DT-TESTGATE

### (a) The retry/permanent-failure integration test above 75 s — accepted as environmental, with timings

Both `test_c3_sweep_dryrun` tests that drive `--scenario both` hardcode `--deadline 75`. On this host
the `retry` scenario does not fit in 75 s. Each scenario was then run on its own through
`r1/scripts/c3_sweep_dryrun.py` with `--deadline 300`, the llama.cpp ones from the deepthought config
with `--fake-offload silent` (this build prints no offload line):

| Scenario | Backend / base | Wall | `elapsed_seconds` | Checks |
|---|---|---|---|---|
| `retry` | ollama fixture | 93 s | 93.1 | **passed** |
| `permanent` | ollama fixture | 45 s | 44.2 | **passed** |
| `retry` | llamacpp, `c3_sweep_deepthought.json` | 107 s | 107.3 | **passed** |
| `permanent` | llamacpp, `c3_sweep_deepthought.json` | 48 s | 48.0 | **passed** |
| `interrupt` | llamacpp, `c3_sweep_deepthought.json` | 124 s | 123.5 | **passed** |
| `watchdog` | llamacpp, `c3_sweep_deepthought.json` | 101 s | 101.1 | **passed** |

The condition in R1-DT-TESTGATE (a) is met: the watchdog test passes and the retry/permanent-failure
scenarios pass with a longer timeout. The 75 s limit is the only thing that fails; every assertion
inside the scenarios holds. Contributing host factors, measured: `/ceph` latency (the first full
paper-suite run on Ceph scratch took 675.9 s on 25 Oct) and CPU co-tenancy — about 12.4 cores of 40
were in use by three other users while these ran.

### (b) The interrupted-root archive assertion — resolved, with evidence

**The interrupt scenario passes on this host, on both backends**, inside the full suite and again
standalone (123.5 s, llama.cpp, deepthought config), including the assertions on the archived
interrupted root and its partial ledger. One attempt was needed, not three.

Why it failed on 25 Oct and does not now: the 25 Oct preparation ran against harness `7305434` and
paper `3d3ec48`, i.e. **before batch B**. Batch B's review explicitly addressed this exact case —
`docs/r1/overnight/BATCH_B_25OCT_HANDOFF.md`, deviation 5: the shared `interrupt` check "no longer
requires an archived partial ledger for a re-run root that had not logged a trial when the runner was
killed (a root started by a freed worker between the snapshot and the kill). One llama.cpp interrupt
run failed with an assertion message of only `openml_breast_w__s105`", which is the message the
25 Oct report recorded. The handoff states the race is inferred, not shown, and that "a root with
logged trials at the kill must still have its partial ledger archived" — that assertion is unchanged
and passes here. So the 25 Oct failure is explained by the pre-batch-B code, and the current pinned
code passes the check. Nothing was relaxed on this branch to make it pass.

## 6. Data caches — all nine `ok`

`python -m r1.noise.check_caches` (network disabled in-process), harness
`/ceph/dwong/r1_prepare_20261025/autoresearch_harness`, versions
`{python 3.13.15, sklearn 1.8.0, numpy 2.4.4, pandas 3.0.3}`:

| Node | Source | Shape | Verdict |
|---|---|---|---|
| `digits_mlp` | bundled/generated, offline | 1797 × 64 | ok |
| `tabular_mlp` | bundled/generated, offline | 2000 × 20 | ok |
| `openml_breast_w` | OpenML 15, node `data_cache` | 699 × 9 | ok |
| `openml_ionosphere` | OpenML 59, node `data_cache` | 351 × 34 | ok |
| `openml_wdbc` | OpenML 1510, node `data_cache` | 569 × 30 | ok |
| `openml_credit_approval` | OpenML 29, node `data_cache` | 690 × 15 | ok |
| `openml_sonar` | OpenML 40, node `data_cache` | 208 × 60 | ok |
| `openml_blood_transfusion` | OpenML 1464, node `data_cache` | 748 × 4 | ok |
| `openml_climate` | OpenML 1467, node `data_cache` | 540 × 20 | ok (reserve) |

`check_caches` reports `ready: 7/7 OpenML nodes` and deliberately skips the two non-OpenML nodes;
those two were verified separately by calling each node's own frozen `load_pool()` with the network
blocked in-process (record: `bundled_data_checks_20261026.json`). NODE_INFO, the D25
categorical/imputer rule, class counts and positive labels matched for every OpenML node; no source
correction was needed. **All nine nodes report `ok`, including climate.**

Nothing was fetched: every cache was already present from the 25 Oct preparation.

## 7. llama.cpp backend and `json_schema` support

- **Runner `--help`** documents the `backend` config key with `"llamacpp"`: a dedicated `llama-server`
  per batch (`r1/scripts/llama_server_instance.py`), GGUF sha256 and the `llama-server --version`
  build line pinned before every start, `/health`, `/v1/models`, `/props`, a one-token probe, full GPU
  offload required from the server log with CPU fallback or partial offload a STOP, the watchdog
  polling `/health` and `/v1/models`, and orphans matched by pid, owner, process group and command
  line. This matches `BATCH_B_25OCT_HANDOFF.md` items 1–3.
- **R1-SCHEMA is implemented and wired end to end.** `c3_label_sweep.py` accepts a top-level
  `proposal_schema`, refuses it unless `backend == "llamacpp"` and the value is exactly
  `manager_proposal/v1`, passes `--proposal-schema` to the collectors and the liveness check, and
  records it in the manifest. In the harness, `manager_response_format()` builds
  `{"type": "json_schema", "json_schema": {... "strict": true ...}}` over exactly six string fields
  with `rationale` present and `additionalProperties: false` — structure only, so D25 key and value
  validity stays the model's. `langchain_client` passes `response_format` **only** for the `llamacpp`
  provider. In `langgraph_manager`, a parse failure under the schema sets `parse_ok = False`,
  `parse_failed = True`, records the raw text's hash and then clears the parsed object and objective
  with the comment "never substitute the free-path heuristic", so a failure is recorded and counted,
  never replaced by a default — exactly R1-SCHEMA.
- **The pinned llama-server build advertises JSON-schema constrained decoding:** its `--help` lists
  `-j, --json-schema SCHEMA` and `-jf, --json-schema-file FILE`. That is the CLI form. Whether this
  v0.7.0 build honours a **per-request** `response_format: {"type": "json_schema", ...}` on
  `/v1/chat/completions` is **not established by `--help` alone** and is checked with a real request
  in Phase 5, with the schema on.

## 8. Phase 2 verdict

Done, with the two environment fixes and the two accepted test items recorded above:

- pins verified (paper, harness `897d83c`, backend merged);
- all nine data caches `ok`, climate included;
- harness suite at the accepted baseline (454/8/1);
- paper suite at baseline plus the R1-DT-TESTGATE (a) deadline failures and the five torch-dependent
  Track P items, with R1-DT-TESTGATE (b) resolved;
- llama.cpp backend and the `manager_proposal/v1` schema path confirmed in code and in the runner CLI;
  the per-request `response_format` behaviour of this build is deferred to Phase 5.

**Caveat carried into Phase 7.** The runner's `preconditions` phase refuses to launch unless the paper
checkout is exactly at the remote `main` head and the harness head equals
`r1/scripts/HARNESS_PIN_C3`. `main` moved twice during this phase (`7611338` → `fc3e0da`). The
sweep-1 paper pin can therefore only be fixed as "the `main` head at launch", which the author's
authorization note must match; the coordinator must merge this branch's config into `main` before
Phase 7, and the launch checkout must then be at that head.

Raw logs, probe records and scenario summaries: `/tmp/r1_sweep1_dwong_20261026/logs/` and
`/tmp/r1_sweep1_dwong_20261026/probe_np1_01/` (local disk, not pushed).
