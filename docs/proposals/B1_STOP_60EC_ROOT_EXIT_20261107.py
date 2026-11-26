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
