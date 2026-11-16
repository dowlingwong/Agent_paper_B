# Independent B1 worker Python environment review — 5 November 2026

AI-assisted (Codex). **Round 1: NOT ACCEPTED.** Reviewed exact candidate `1ee8c82a52e94aaac2feffe256c84db565bc3856`, diff against `1288793`. No host was contacted and no model, real worker, GPU, or experiment was run.

## Finding — an unexecutable first entry silently falls through to a different Python

`r1/exam/runtime.py:109–120` checks only that `sys.executable` and the sibling `python3` refer to the same inode; it neither checks that the file is executable nor verifies which `python3` the resulting PATH actually resolves to. It then appends the caller's original PATH. In the pinned harness, all three B1 node specs invoke `python3 train.py` (`configs/nodes/digits_mlp.yaml:11`, `openml_credit_approval.yaml:11`, `openml_ionosphere.yaml:11`), and `LocalWorker._run_command` launches that command through `shell=True` (`src/autoresearch/worker/local_worker.py:288–299`), with `seed_environment` inheriting PATH.

Independent inert fixture reproduction: a non-executable temporary `venv/bin/python` and its same-file `python3` symlink pass `worker_environment`; a second temporary PATH directory contains an executable inert `python3` shell fixture. `subprocess.run('python3', shell=True, env=...)` exits 0 and prints `WRONG_INTERPRETER`. This proves shell fallback can violate the stated binding if the intended executable is not executable at the relevant check; no Python model or training ran. The existing tests create non-executable dummy files and incorrectly count their same-file match as a valid binding. Filesystem changes between checks remain a separate process/host assumption and should not be claimed prevented without evidence.

**Unblock:** refuse non-regular/non-executable interpreter candidates and check that command resolution in the produced environment identifies the intended same-file executable; add an inert subprocess regression demonstrating a later PATH entry cannot silently win. Retain the current missing/different-inode checks, B1-only scope and before-server preflight. **Owner:** Mac implementer and same reviewer. **Effort:** roughly 30–60 minutes plus recheck; actual TASL-7 environment is an operator check.

## Other scope and checks

The proposed environment is selected only for B1 in `ExamRunner.run_job`; Stage A retains its previous environment. Parent preflight runs before the batch output/server and is repeated before the worker starts. The pinned harness's seed environment copies `os.environ`, preserving the B1 PATH in ordinary execution. This does not establish runtime immutability, host dependency versions, or deterministic numerical results. The earlier real-worker test's failure cause remains unverified; passing an inert environment test is not a replacement for running that prohibited test later under separate authority.

Independent CPU-only local suite: `AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q r1/tests/test_exam_b1_parent_binding.py r1/tests/test_exam_b1_lease.py`: **15 passed in 1.02 s**. These tests do not cover the fallback counterexample above. This review gives no author approval or B1 launch readiness.

## Same-reviewer recheck — accepted for B1 Python environment binding

**ACCEPTED in the bounded code/test scope**, at candidate `bc52181f1b5f00a0477f93db15e59659abece2a8`. The candidate requires the sibling `python3` to be a regular executable and the same file as the runner interpreter; it verifies `shutil.which` over the resulting PATH resolves to that same file and refuses before output/server startup if not. An inert fallback-executable regression confirms the missing/non-executable intended interpreter is refused before subprocess launch. Another independent inert shell probe with both valid intended and fallback executables selected the intended executable and printed `expected`. Stage A retains its previous environment.

Independent CPU-only synthetic suite (`test_exam_b1_parent_binding.py`, `test_exam_b1_lease.py`, `test_exam_stagea_preserve.py`): **30 passed in 0.98 s**. This is not an actual-worker determinism result, does not identify the cause of the historic failure, and does not verify the future TASL-7 interpreter, dependencies, or immutability across filesystem races. The real-worker test remains unrun under the overnight no-model instruction; operator site checks and all author/phase gates remain open. No server, model, GPU, experiment, or host access occurred.
