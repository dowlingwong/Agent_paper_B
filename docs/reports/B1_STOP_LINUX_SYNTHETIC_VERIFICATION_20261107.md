# B1 STOP candidate: Linux synthetic verification plan (engineering only)

**DRAFT, not executed on TASL-7, not an acceptance or launch authorization.** Candidate: `0606f5cd4b339b08737fc0e93392c080cc18a01f`; review must cover the exact code ultimately deployed. This plan runs no node, model, GPU or server and signals only subprocesses it creates. A fresh independent reviewer must assess the code, the host evidence and any deviations before acceptance. The B1 launch conditions and separate host-operator authority remain in force.

## Preconditions and evidence

An authorized operator identifies an idle private working directory and an existing evidence parent on TASL-7. The exact committed candidate must be checked out cleanly in an isolated worktree; do not modify other worktrees. Check the interpreter has `os.waitid`, `os.WNOWAIT`, and the project's runtime dependencies, and that `/proc` exposes the operator's own processes. Abort if not. This is an engineering test only; no experiment directories or existing logs are used. Commands below create a unique evidence directory and retain it, including on failure. Do not clean it up. The script cleans up only its own synthetic subprocesses. It does not use cgroups, a supervisor, or signals to processes identified only by a host-wide scan.

Replace the three example values before running. `EVIDENCE_PARENT` must be an existing private directory on a filesystem with sufficient space. Never use an existing experiment directory.

```bash
set -eu
set -o pipefail
umask 077
PAPER_DIR=/absolute/path/to/isolated/candidate-checkout
PYTHON=/absolute/path/to/project/python
EVIDENCE_PARENT=/absolute/path/to/private/engineering-evidence
cd "$PAPER_DIR"
export PYTHONPATH="$PAPER_DIR${PYTHONPATH:+:$PYTHONPATH}"
test "$(uname -s)" = Linux
test "$(git rev-parse HEAD)" = 0606f5cd4b339b08737fc0e93392c080cc18a01f
test -z "$(git status --porcelain --untracked-files=all)"
test -d "$EVIDENCE_PARENT"
"$PYTHON" -c 'import os; from r1.exam import runtime; assert all(hasattr(os, x) for x in ("waitid", "WNOWAIT", "P_PID")); assert os.path.isdir("/proc/self")'
EVIDENCE_DIR=$(mktemp -d "$EVIDENCE_PARENT/b1-stop-synthetic-20261107.XXXXXXXX")
export EVIDENCE_DIR
printf 'Evidence directory: %s\n' "$EVIDENCE_DIR"
```

The clean check is before evidence creation. Record `HEAD`, Python version, Linux kernel, script, UTC time, exit status and transcript below; retain partial evidence on errors. The following uses no pinned harness and never invokes a node. The process group ID is held by the unreaped root until both STOP signals have been sent. The sentinel process is independently owned by the test and must stay alive through the STOP.

```bash
set -o noclobber
printf 'head=%s\npython=%s\nkernel=%s\nutc=%s\n' "$(git rev-parse HEAD)" "$("$PYTHON" --version 2>&1)" "$(uname -sr)" "$(date -u +%FT%TZ)" > "$EVIDENCE_DIR/metadata.txt"
cat > "$EVIDENCE_DIR/check_stop.py" <<'PY'
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from r1.exam.runtime import _b1_child_exit, _stop_b1_worker_group

out = Path(os.environ['EVIDENCE_DIR'])
ready = out / 'child-ready'
child_code = '''import signal, sys, time
from pathlib import Path
signal.signal(signal.SIGTERM, signal.SIG_IGN)
with open(sys.argv[1], 'x') as f: f.write('ready\\n')
time.sleep(120)
'''
root_code = '''import subprocess, sys, time
from pathlib import Path
p = subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
for _ in range(500):
    if Path(sys.argv[2]).exists(): break
    time.sleep(.01)
else: raise SystemExit(8)
print(p.pid, flush=True)
raise SystemExit(7)
'''

def identity(pid):
    # Own-process /proc only. The name in parentheses may contain spaces.
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return {'state': fields[0], 'pgrp': int(fields[2]), 'session': int(fields[3]),
                'start_ticks': int(fields[19])}
    except FileNotFoundError:
        return None

sentinel = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'],
                            start_new_session=True)
root = None
stop_attempted = False
try:
    root = subprocess.Popen([sys.executable, '-c', root_code, child_code, str(ready)],
                            stdout=subprocess.PIPE, text=True, start_new_session=True)
    line = root.stdout.readline().strip()
    if not line.isdigit(): raise RuntimeError('synthetic child did not become ready')
    owned_pid = int(line)
    initial = identity(owned_pid)
    if not initial or initial['pgrp'] != root.pid or initial['session'] != root.pid:
        raise RuntimeError(f'owned group identity mismatch: {initial}')
    deadline = time.monotonic() + 10
    while (status := _b1_child_exit(root)) is None:
        if time.monotonic() >= deadline: raise RuntimeError('root exit timeout')
        time.sleep(.02)
    if status != 7: raise RuntimeError(f'unexpected root status {status}')
    print(f'root={root.pid} root_status={status} owned={owned_pid} initial={initial}', flush=True)
    stop_attempted = True
    _stop_b1_worker_group(root)
    deadline = time.monotonic() + 5
    while True:
        current = identity(owned_pid)
        # An orphan zombie is already stopped; do not wait for the host's PID 1
        # to reap it, and do not signal a recycled PID.
        stopped = current is None or current['start_ticks'] != initial['start_ticks'] or current['state'] == 'Z'
        if stopped: break
        if time.monotonic() >= deadline: raise RuntimeError(f'owned child remains live: {current}')
        time.sleep(.05)
    if sentinel.poll() is not None: raise RuntimeError('unrelated owned sentinel exited')
    print(f'owned_final={current} sentinel_alive=yes root_returncode={root.returncode}', flush=True)
    if root.returncode != 7: raise RuntimeError('unexpected reaped root status')
    print('PASS: exited root, TERM-resistant owned descendant stopped, sentinel unaffected', flush=True)
finally:
    # On a pre-STOP setup failure, clean up the one group created by this test
    # while its root is still unreaped. Never retry a failed STOP automatically.
    if root is not None and root.returncode is None and not stop_attempted:
        try: _stop_b1_worker_group(root)
        except Exception as exc: print(f'cleanup failed: {exc!r}', file=sys.stderr, flush=True)
    sentinel.terminate()
    try: sentinel.wait(timeout=5)
    except subprocess.TimeoutExpired:
        sentinel.kill()
        sentinel.wait(timeout=5)
PY
set +e
"$PYTHON" "$EVIDENCE_DIR/check_stop.py" > "$EVIDENCE_DIR/transcript.txt" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > "$EVIDENCE_DIR/exit-status.txt"
cat "$EVIDENCE_DIR/transcript.txt"
test "$rc" -eq 0
```

**STOP on any failure:** retain the directory and transcript; report the exact error, PIDs and identities recorded, and who must resolve it. Do not retry automatically, start B1, or signal an unidentified process. No conclusion about GPU work, malicious same-UID processes or detached descendants follows from this test. If the same candidate is integrated at a different commit, a reviewer must verify the exact code and adapt the HEAD check before testing; do not silently substitute it.

## Additional checks and limitations

- The Mac synthetic suite at candidate `0606f5cd` passed 26 tests, including a live-root audit STOP and a root-exit case with a TERM-resistant child. Mac Python 3.11 needed a Darwin `libc.waitid` fallback; production Linux should use Python's `os.waitid`. A Mac group containing only a zombie produced `EPERM` on the second group signal; the candidate records this as a shutdown error rather than claiming success. Do not assume either result applies to Linux without evidence.
- Linux `/proc` may retain an already-dead orphan as a zombie. `kill(pid, 0)` alone cannot distinguish that from a live worker; the verification above records state and start ticks. This is why the existing Mac-oriented root-exit pytest is not by itself sufficient on Linux.
- Separately run the already reviewed live-root audit STOP integration test on Linux in an isolated Python environment if its pinned harness and dependencies are available, preserving its pytest evidence; `r1/tests/test_b1_stop_owned_process_integration.py::test_audit_stop_notifies_parent_and_stops_owned_processes` is the test. Pytest temporary-directory cleanup is allowed by the author's 7 Nov clarification; retain its transcript and any STOP evidence. Never run the full experiment as a diagnostic.
- A process intentionally leaving the B1 session is outside this process-group check. Review the actual worker spawning paths and any host wrappers for `setsid`/new sessions before acceptance. A successful synthetic result is engineering evidence, not proof of all production process behavior.
