# One new synthetic Stage A worker-to-B1 recovery test

**Candidate for independent review; do not execute before acceptance.** The author has explicitly allowed exactly one new-directory, localhost-enabled synthetic attempt after the first retained STOP. That earlier scene `/private/tmp/paper-b-stagea-real-child-test-20261108-a` and its log `873c53005d5881fe688c80a69274fa3799539e1770b7e2ced12b45e9157fdf58` remain untouched; its `STOPPED` batch is never resumed. This attempt is synthetic engineering only: no real model, GPU, real Stage A lease or host experiment, and no cgroup/supervisor. No retry is permitted if this one fails or is uncertain.

Relative to the first candidate, the fixture now constructs the actual `ExamRunner` in marked DRYRUN, and `exam_runner.stage_a` calls its unmodified `ExamRunner.run_job` for each candidate. The actual parent job dispatch passes a test-owned pipe FD and starts a child subprocess; a test-scoped Popen adapter substitutes only the child entry module so that the child enters the real `stage_a.main` after installing the explicit test-only D3/cold/identity/recorder/journal-validation/telemetry substitutions. The child asserts it inherited the synthetic descriptor and logs its PID; the parent verifies three unique child identities. A real test-owned localhost fake llama-server is started and stopped through its existing instance API and receives synthetic `/completion`, `/tokenize`, `/apply-template` and `/v1/chat/completions` requests; it uses dummy fixture files, not model weights. The real Stage A parent watchdog runs against the fake server. The command fixes fake GPU memory to zero, so fake server instances create no PID-named `gpu_apps` files, and selects the fake offload log-line route; no actual GPU is involved. This is not proof of the production OFD lease, coldness, real journals, native server, GPU or real Stage A data.

The fixture retires prior synthetic Stage A rows and fake-server records into `_to_delete` before each rewrite, using a test-only Mac-compatible retire-then-exclusive record writer. A test-only B1 runner/worker bootstrap similarly retires existing batch-state, server-record and audit-cache JSON versions and copied node edit/restore files before the existing synthetic code writes them; harness-owned pending-guard cleanup follows the author exception. All output lives under the unique pytest root. The adapter changes test instrumentation and does not modify production paths. The scoped prior collision/lock unit has an independent acceptance (`B1_SYNTHETIC_RETENTION_UNIT_REVIEW_20261108.md`); additional local-only tests cover batch/audit JSON versions, server record versions, stale temp refusal and actual pinned snapshot restore. Their retained log `/private/tmp/paper-b-retention-unit-20261108-c.log` SHA-256 `77d565fdfedc1cb67e83fa85ec247e98dd648d618f9927b0af68f98bd71355a9` reports four passing bounded tests. These are not the end-to-end test. The later existing B1 test launches the actual synthetic B1 runner, waits for an owned in-progress root, kills only its owned parent, confirms the test-owned worker/server self-exit and preserves the interrupted tree before exercising DRYRUN crash recovery. This is not production STOP recovery: a recorded STOP must never be resumed. A test-only wrapper prints the chained real `ExamRunner.server` exception traceback before the existing main handler records STOP, so an execution failure should identify the operation if Python captured it; no diagnosis is asserted in advance.

After independent review of the exact candidate/test, the operator may execute **once** in an environment where local loopback bind/connect are permitted. If that requires an execution permission escalation, its review must permit the specific local synthetic test; do not access another host or alter other processes. Fill `EXPECTED_HEAD` with the independently accepted test candidate SHA and re-review the resulting command. Use the exact f2-based candidate and fixed harness; check that all three paths below, including symlinks, are absent before pytest starts because pytest can clear an existing `--basetemp`. The operator must ensure the environment does not cause a previously owned fixture to be targeted. Preserve this new root, log and rc regardless of outcome. An output collision, nonzero or missing exit, timeout, STOP, disconnect or unclear result ends the attempt; no rerun, cleanup or state repair.

```bash
set -u
set -o pipefail
umask 077
unset TRACKX_GPU_LEASE_FD LLAMACPP_CACHE_PROMPT PYTHONHOME PYTHONUSERBASE
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONNOUSERSITE=1
TEST_REPO=/private/tmp/paper-b-b1-synthetic-retention-unit-20261108
EXPECTED_HEAD=REPLACE_WITH_EXACT_REVIEWED_TEST_HEAD
HARNESS=/private/tmp/paper-b-b1-tests-harness-20261107
PY=/Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python
ROOT=/private/tmp/paper-b-stagea-real-child-test-20261108-b
LOG=/private/tmp/paper-b-stagea-real-child-test-20261108-b.log
RC=/private/tmp/paper-b-stagea-real-child-test-20261108-b.rc
for p in "$ROOT" "$LOG" "$RC"; do [ ! -e "$p" ] && [ ! -L "$p" ] || exit 1; done
case "$EXPECTED_HEAD" in *[!0-9a-f]*|'') exit 1;; esac
[ "${#EXPECTED_HEAD}" -eq 40 ] || exit 1
HEAD=$(git --no-optional-locks -C "$TEST_REPO" rev-parse HEAD) || exit 1
[ "$HEAD" = "$EXPECTED_HEAD" ] || exit 1
STATUS=$(git --no-optional-locks -C "$TEST_REPO" status --porcelain --untracked-files=all) || exit 1
[ -z "$STATUS" ] || exit 1
HARNESS_HEAD=$(git --no-optional-locks -C "$HARNESS" rev-parse HEAD) || exit 1
[ "$HARNESS_HEAD" = a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 ] || exit 1
HARNESS_STATUS=$(git --no-optional-locks -C "$HARNESS" status --porcelain --untracked-files=all) || exit 1
[ -z "$HARNESS_STATUS" ] || exit 1
cd "$TEST_REPO" || exit 1
set -C
export AR_HARNESS_B1_ROOT="$HARNESS" AR_HARNESS_ROOT="$HARNESS" R1_REQUIRE_B1_HARNESS=1
export PYTHONPATH="$TEST_REPO:$HARNESS/src" PATH="/Users/wongdowling/Documents/autoresearch_harness/.venv/bin:/usr/bin:/bin"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export C3_FAKE_LLAMA_GPU_MIB=0 C3_FAKE_LLAMA_OFFLOAD=line
if "$PY" -m pytest -q -p no:cacheprovider --basetemp="$ROOT" r1/tests/test_exam_stagea_b1_real_child_recovery_20261108.py > "$LOG" 2>&1; then result=0; else result=$?; fi
printf '%s\n' "$result" > "$RC"
shasum -a 256 "$LOG" "$RC"
printf 'synthetic test exit=%s; preserve root=%s\n' "$result" "$ROOT"
exit "$result"
```

PASS requires a normal test exit 0 and an independently inspected retained log and root proving actual Stage A parent job dispatch, three worker child PIDs, fake-server traffic and lease substitution, complete synthetic Stage A table, the owned B1 parent kill, preserved partial tree and unchanged completed roots, and final DRYRUN completion. Review must explicitly check the pre-existing strict no-deletion rules against all test fixture writes and cleanup behavior before any execution. This candidate makes no claim that the attempted test will pass or that it supplies live host evidence.
