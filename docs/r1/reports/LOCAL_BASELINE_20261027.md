# Local baseline, 26–27 October 2026

AI-assisted. These are engineering test outcomes, not experimental evidence or scientific results. L0 review is pending.

## Provenance and conditions

- Paper branch `local-20261026`, based on `origin/main` at `8ba81b68c70c58d40612c7a316e8d1669ff5ca33`. The precise launch HEAD was not captured and is not established by the retained evidence. The paper JUnit timestamp predates the creation of `ad90149`; during the run `ad90149` updated PLAN and `5505eb1` updated STATUS. `git diff 8ba81b68..5505eb1 -- r1 Makefile` is empty; document and working-tree state at launch cannot be inferred from that fact.
- Harness `r1` at `897d83c8efa364ec2fdd37288241cc42e01d7274`, tested in a disposable local clone. The original checkout was not changed. The harness pin is unchanged.
- Python 3.13.4, a `uv` virtual environment outside both repositories; installed package versions are in [environment.txt](local_baseline_20261026/environment.txt). The harness dependencies follow the committed exam test requirements; torch, transformers, peft, safetensors and pytest-timeout were added for the merged Track P tests.
- **Operator-reported conditions:** tests ran in the restricted Mac sandbox with `CUDA_VISIBLE_DEVICES=''`, `PYTORCH_ENABLE_MPS_FALLBACK=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, an empty isolated `HF_HOME`, and Hugging Face offline mode. Track P wrappers default to CPU; the operator reports no real base weights downloaded or loaded. Fake local servers could not bind in this sandbox. A per-test timeout of 590 seconds was configured; configuration alone does not prove each individual runtime or accelerator usage. The retained logs do not independently establish every environment variable, the empty cache, or the process exit status.
- Attempt record: the first dependency installation was interrupted after sandbox network retries; installation succeeded in the isolated environment with approved network access. Harness attempt 1 stopped at collection on `tests/test_legacy_noop_skip.py` (`src.autoresearch_worker` missing); its [log](local_baseline_20261026/harness-attempt1.log.gz) is retained. Attempt 2 used `--continue-on-collection-errors` to collect the remaining outcomes, preserving the same error. The paper suite ran once via `make r1-test`, with one test deselected under the author's time limit.

## Baseline results

| Suite | Result | Evidence |
|---|---|---|
| Paper `make r1-test` | 500 passed, 66 failed, 72 skipped, 1 deselected; exit 2 from make | [JUnit](local_baseline_20261026/paper-junit.xml.gz), [log](local_baseline_20261026/paper-tests.log.gz), [failure and skip IDs](local_baseline_20261026/paper-ids.md) |
| Harness `pytest tests` | 433 passed, 27 failed, 3 errors; 55 subtests passed; exit 1 | [JUnit](local_baseline_20261026/harness-junit.xml.gz), [log](local_baseline_20261026/harness-attempt2.log.gz), [failure and error IDs](local_baseline_20261026/harness-failing-ids.md) |

The paper's deselected kill-and-resume test allows a 600-second checkpoint wait in addition to other runs, exceeding the author’s approximate per-test limit. The isolated empty model cache caused tokenizer-dependent tests to skip. Many fake-server tests failed with socket `PermissionError`; other failures include worker and environment-dependent checks, historical artifact availability, and test-data expectations. The logs and JUnit preserve the individual failure details; this baseline does not classify every failure as environmental or compare it as identical to another host's baseline.

The independent reviewer reproduced a decompressed record-level difference in the E0 synthetic-set regeneration test, in addition to the separate pilot-table byte-identity failure; both remain unresolved test findings, with no cause assigned. See [the review](../reviews/LOCAL_L0_REVIEW_20261027.md).

## Operator-recorded commands

The following are transcribed from the execution session, not recovered from the output logs. They document the intended invocation for comparison; the logs and JUnit do not independently prove every setting. The paper exit status 2 is likewise operator-reported.

```sh
env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/private/tmp/paper-b-local-empty-hf PYTORCH_ENABLE_MPS_FALLBACK=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 AR_HARNESS_ROOT=/private/tmp/paper-b-local-harness-20261026 PYTHONPATH=/private/tmp/paper-b-local-harness-20261026/src PYTEST_ADDOPTS='--timeout=590 --timeout-method=signal --junitxml=/private/tmp/paper-b-local-paper-junit.xml -ra --deselect=r1/tests/test_trackp_cli.py::test_toy_kill_and_resume_matches_an_uninterrupted_run' make r1-test R1_PY=/private/tmp/paper-b-local-20261026-venv/bin/python
```

```sh
env CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HOME=/private/tmp/paper-b-local-empty-hf PYTORCH_ENABLE_MPS_FALLBACK=0 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /private/tmp/paper-b-local-20261026-venv/bin/python -m pytest -q -p no:cacheprovider -p pytest_timeout --timeout=590 --timeout-method=signal --continue-on-collection-errors --junitxml=/private/tmp/paper-b-local-harness-junit-attempt2.xml -ra tests
```

## Document inventory

[document-inventory.tsv](local_baseline_20261026/document-inventory.tsv) records the paths and SHA-256 hashes at the orientation commit. It includes PLAN, RUNBOOK, the STATUS snapshot, C3 design, Track P specification, T1–T5, the problem and novelty inputs, the three host runbooks, this Mac runbook, and the reference README. PLAN §10 governs current decisions; older design text and pilot records remain historical where superseded.

## Open follow-up

Independent review must verify the captured counts, IDs, conditions and inventory before L0 is accepted. The sandbox-constrained failures are the baseline for later comparisons in this environment; they do not establish that a remote host is ready for an evidence run.
