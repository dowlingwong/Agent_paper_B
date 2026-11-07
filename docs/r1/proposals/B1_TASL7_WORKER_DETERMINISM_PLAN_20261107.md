# TASL-7 B1 real-worker seed determinism: execution candidate

AI-assisted (Codex). **Proposed engineering-only procedure; independent review required before execution.** This does not authorize B1 or establish any site observation. It runs `r1/tests/test_b1_real_worker_determinism.py::test_b1_real_worker_run_is_seed_deterministic`: two real pinned `LocalWorker` invocations on the synthetic CPU `tabular_mlp` node, both with joint seed 7001. It uses the same node, seed, real worker and exact metric-equality assertion as the original general test, adding the B1 `preserve_node_outputs=True` and `stop_on_invalid=True` path and finite-metric assertion. The original test remains unchanged; independent review must decide whether this B1-specific version meets the author’s real-worker determinism condition. No LLM server or GPU is needed. It does not read B1 audit values. The current Paper B audit copies the selected node into a unique pytest-owned temporary directory; the harness runs `python3 train.py`, and the pinned `tabular_mlp` benchmark writes its metrics to stdout and does not itself persist model files. Its two separate trial logs and other outputs must remain inspectable. This narrow test does not establish server or lease behavior.

## Prerequisites and boundary

1. Independently review this procedure and final combined checkout. Set `PAPER_HEAD` to that exact reviewed full SHA; local Paper checkout must be clean, and its committed files must include the reviewed audit preservation fix. `HARNESS_HEAD=a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` in a clean, locally verified pinned harness checkout. `git archive` carries tracked committed files, not `.git`; record and independently verify the local commits, archives and transferred hashes. No untracked source or existing track checkout is copied. A source/venv change, failed command or test failure is a STOP: preserve the unique run directory and logs and report, without retrying automatically.
2. Before execution obtain a fresh read-only TASL-7 identity, `~/r1_locks` and complete applicable STATUS snapshots, process and resource census; record UTC and outputs. The author permits continuation despite unrelated operator processes; never signal or otherwise preempt them, and do not modify another track's checkout, processes, work or data. Use CPU only, no GPU or model. If CPU, memory or disk cannot accommodate the two bounded worker runs without material interference, wait and recheck. Confirm free space for both copied source archives and retained test artifacts; at least 2 GiB available is an engineering floor for this probe, not the full B1 capacity criterion. Snapshots do not guarantee future availability.
3. Identify a pre-existing, readable TASL-7 Python virtual environment by read-only inspection; do not install or alter it. Select its absolute `bin/python` path as `HOST_PYTHON` in the command below. Confirm executable and imports of pytest, NumPy and scikit-learn, then prove that PATH resolves the worker's literal `python3` to the same venv interpreter. Record versions and paths. If a matching `python3` is not available, STOP; do not silently substitute system Python or change the host environment. Compare these facts later with actual reviewed B1 worker environment, which may differ.
4. Use a never-before-used dated `RUN_ID` comprising only ASCII letters, digits, `_` and `-`. All remote files belong to this engineering test, under `~/r1_b1_engineering/$RUN_ID`; never remove any of them. Normal pytest-owned temp/lock and Python caches may clean themselves under the author's 7 November exception. The test uses a not-yet-existing pytest basetemp, so pytest does not remove an existing directory. User-specified source and captured outputs must be retained on success and failure.

## Concrete command sequence

The following is a candidate for review, not an execution receipt. Run from a local shell with `set -euo pipefail` and `set -o noclobber`; set the four variables to independently verified values before starting. The remote SSH alias `tasl7` is from `TASL7_READONLY_CENSUS_20261107.md`. Save the complete console transcript in a new local file and record UTC, command exit codes, SHA-256 and identities. Treat SSH transport loss as STOP and inspect the scene before any further action. Do not rerun in the same or another run directory automatically.

```bash
PAPER_DIR=/absolute/path/to/clean/reviewed/paper
HARNESS_DIR=/absolute/path/to/clean/pinned/harness
PAPER_HEAD=FULL_REVIEWED_COMMIT_SHA
RUN_ID=b1_worker_engineering_20261107_UNIQUE
HOST_PYTHON=/absolute/path/to/verified/venv/bin/python
HARNESS_HEAD=a3fedbbd44309b3fdf99d853ad841b9ec2c299e2
case "$RUN_ID" in *[!A-Za-z0-9_-]*|'') exit 1;; esac
case "$HOST_PYTHON" in *[!A-Za-z0-9_./-]*|'') exit 1;; esac
case "$HOST_PYTHON" in /*/bin/python) ;; *) exit 1;; esac
test "$(git -C "$PAPER_DIR" rev-parse HEAD)" = "$PAPER_HEAD"
test -z "$(git -C "$PAPER_DIR" status --porcelain)"
test "$(git -C "$HARNESS_DIR" rev-parse HEAD)" = "$HARNESS_HEAD"
test -z "$(git -C "$HARNESS_DIR" status --porcelain --untracked-files=no)"
mkdir "/private/tmp/$RUN_ID"
git -C "$PAPER_DIR" archive --format=tar "$PAPER_HEAD" > "/private/tmp/$RUN_ID/paper.tar"
git -C "$HARNESS_DIR" archive --format=tar "$HARNESS_HEAD" > "/private/tmp/$RUN_ID/harness.tar"
shasum -a 256 "/private/tmp/$RUN_ID/paper.tar" "/private/tmp/$RUN_ID/harness.tar"
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "mkdir -p \$HOME/r1_b1_engineering && mkdir \$HOME/r1_b1_engineering/$RUN_ID && mkdir \$HOME/r1_b1_engineering/$RUN_ID/paper \$HOME/r1_b1_engineering/$RUN_ID/harness \$HOME/r1_b1_engineering/$RUN_ID/tmp \$HOME/r1_b1_engineering/$RUN_ID/home"
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "cat > \$HOME/r1_b1_engineering/$RUN_ID/paper.tar" < "/private/tmp/$RUN_ID/paper.tar"
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "cat > \$HOME/r1_b1_engineering/$RUN_ID/harness.tar" < "/private/tmp/$RUN_ID/harness.tar"
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "sha256sum \$HOME/r1_b1_engineering/$RUN_ID/paper.tar \$HOME/r1_b1_engineering/$RUN_ID/harness.tar"
# STOP unless both printed remote archive hashes equal the local hashes, then:
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "tar -xf \$HOME/r1_b1_engineering/$RUN_ID/paper.tar -C \$HOME/r1_b1_engineering/$RUN_ID/paper && tar -xf \$HOME/r1_b1_engineering/$RUN_ID/harness.tar -C \$HOME/r1_b1_engineering/$RUN_ID/harness"
```

The selected clean Git archives must be inspected for unsafe absolute paths, `..`, symlinks escaping extraction roots and other collisions before the transfer; any finding is STOP. Archive extraction occurs only into newly created empty own directories. The following remote script uses an exclusively created per-run log; it does not launch a server or GPU workload. Substitute only the already validated values and preserve the script itself as part of the reviewed commands. The parent's local shell must retain complete stdout/stderr and SSH exit status independently of the remote log.

```bash
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 "RUN_ID=$RUN_ID HOST_PYTHON=$HOST_PYTHON bash -s" <<'REMOTE'
set -euo pipefail
set -o noclobber
base="$HOME/r1_b1_engineering/$RUN_ID"
test -x "$HOST_PYTHON"
test ! -e "$base/pytest"
venv_bin="$(dirname "$HOST_PYTHON")"
test -x "$venv_bin/python3"
# Record both logical and resolved interpreter paths; venv symlinks are allowed.
readlink -f "$HOST_PYTHON"
readlink -f "$venv_bin/python3"
test "$(readlink -f "$HOST_PYTHON")" = "$(readlink -f "$venv_bin/python3")"
"$HOST_PYTHON" -c 'import sys,pytest,numpy,sklearn; print("python",sys.executable,sys.version); print("pytest",pytest.__version__,pytest.__file__); print("numpy",numpy.__version__,numpy.__file__); print("sklearn",sklearn.__version__,sklearn.__file__)'
"$venv_bin/python3" -c 'import sys,pytest,numpy,sklearn; print("worker_python",sys.executable,sys.prefix,pytest.__version__,numpy.__version__,sklearn.__version__)'
test "$("$HOST_PYTHON" -c 'import sys; print(sys.prefix)')" = "$("$venv_bin/python3" -c 'import sys; print(sys.prefix)')"
cd "$base/paper"
# No other PATH python precedes the reviewed venv's python3.
env -i HOME="$base/home" TMPDIR="$base/tmp" PATH="$venv_bin:/usr/bin:/bin" \
  PYTHONPATH="$base/paper:$base/harness/src" AR_HARNESS_ROOT="$base/harness" \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CUDA_VISIBLE_DEVICES='' \
  "$HOST_PYTHON" -m pytest -p no:cacheprovider --basetemp="$base/pytest" \
  -v r1/tests/test_b1_real_worker_determinism.py::test_b1_real_worker_run_is_seed_deterministic \
  > "$base/pytest.log" 2>&1
cat "$base/pytest.log"
find "$base/pytest" -type f -name run.log -print -exec sha256sum {} \; -exec cat {} \;
REMOTE
```

A failed pytest exits before the final `cat` and `find`; operator must subsequently perform read-only capture of the same files and exit code without rerunning. The result is a pass only if the test actually runs (not skipped), both worker runs succeed, their reported finite metrics are exactly equal, both retained logs confirm the worker execution, and the independent reviewer checks the identified checkout/pin, test code, all commands, environment, paths and timestamps. Log contents and archive hashes are evidence; do not publish unrelated process command lines or secrets.

## Separate remaining launch checks

This CPU test does not establish the actual llama-server descriptor or shared open-file description, cooperative GPU lease at launch, expected GPU UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, complete B1 output capacity, final author gate, host dry run, or Track S/P handover. These require their own independently reviewed checks and current host observations. It does not replace final checkout acceptance or an approved B1 note. No cgroup is required by the author's 7 November decision.
