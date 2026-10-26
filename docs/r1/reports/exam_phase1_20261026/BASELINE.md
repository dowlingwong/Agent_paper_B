# Phase 1 test baseline (26 October 2026)

AI-assisted; ENGINEERING_ONLY. Before any implementation code changes in either repository.

Scratch venv: `/private/tmp/exam-x-20261026/venv`, CPython 3.13.4, created with the Mac's existing uv. Dependencies exported from the harness's existing `uv.lock` using `uv export --frozen --extra dev --no-emit-project --no-hashes`; installed versions are preserved in `test_requirements.txt`. No portal installation has been performed.

Code baseline: paper `8304156` (subsequent pre-implementation commits `acf0426` / `ef2377a` record only author decisions); harness `6afdb0e`. Test command in each repository:

```sh
env PATH=/private/tmp/exam-x-20261026/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 /private/tmp/exam-x-20261026/venv/bin/python -m pytest -p no:cacheprovider --continue-on-collection-errors -q -ra
```

Paper additionally uses `PYTHONPATH` containing paper root and harness src. Both authoritative baselines ran outside the sandbox so fake HTTP servers could bind. Results:

| Repository | Passed | Failed | Skipped | Errors | Duration |
|---|---:|---:|---:|---:|---:|
| Paper | 417 | 22 | 9 | 0 | 645.08 s |
| Harness | 448 | 8 | 0 | 1 | 95.12 s |

Exact failing IDs and tracebacks are in `paper_baseline.log` and `harness_baseline.log`. The paper failure set includes Mac `/proc` limitations and desktop integration failures; these are measured pre-existing failures, not a claim that a Linux suite was run. Harness includes missing legacy-submodule/manuscript/artifact fixtures.

Earlier environment attempts are preserved under `/private/tmp/exam-x-20261026/*environment_attempt.log`: the first harness attempt did not put the scratch interpreter on worker PATH (438 passed, 16 failed, 3 errors); the first paper attempt was sandboxed and interrupted after identifying that socket permissions and worker PATH would invalidate its comparison. Those are not the authoritative baseline. Only the agent's own paper baseline process was interrupted; no experiment or remote workload was touched.
