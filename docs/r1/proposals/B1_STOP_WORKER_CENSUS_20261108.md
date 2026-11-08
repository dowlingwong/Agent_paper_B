# B1 STOP: bounded read-only process census proposal

Candidate for fresh independent review; not executed. The 01:19:49 UTC capture `/private/tmp/paper-b-monitor-6835-20261108.rC5qn9Op/ssh.log` reports STOPPED, 36 completed roots, no active root, pane exit 1, server record stopped and its `/proc` lookup not checkable, and no GPU compute apps. It does not establish that all worker descendants exited. Existing `run_job` reaps a successful root and clears `self.child`; the exception STOP group path applies only while a child is owned. Preserve all data and STOP state; no signals, retry or automatic changes.

Run this only after independent review, with the accepted SSH receipt wrapper and a fresh exclusive local capture. It reads metadata of visible `/proc` entries; only processes with UID 1011 have cmdline read, solely to match the unique B1 output path, and unrelated cmdlines are never printed. No process is signalled. The old active PID 1585590 lacks retained start ticks in the prior capture; it cannot be identified by PID alone. Hash and retain the local wrapper, remote script, log and separate exit status. SSH failure or observer errors mean STOP and preserve the capture.

```python
import os
from pathlib import Path

needle = b'/home/dowling/exam-x/work/b1_6835_20261108_a/'
uid = 1011
errors = 0
matched = 0
print('B1_CENSUS_BEGIN', flush=True)
for name in sorted(os.listdir('/proc'), key=lambda n: int(n) if n.isdigit() else -1):
    if not name.isdigit():
        continue
    p = Path('/proc') / name
    try:
        st = p.stat()
        if st.st_uid != uid:
            continue
        cmd = (p / 'cmdline').read_bytes()
        if needle not in cmd:
            continue
        # Capture only metadata; command arguments are not emitted.
        raw = (p / 'stat').read_text()
        end = raw.rfind(')')
        if end < 0:
            raise ValueError('malformed stat')
        fields = raw[end + 2:].split()
        if len(fields) < 20:
            raise ValueError('short stat')
        print('MATCH pid={} uid={} state={} ppid={} pgid={} sid={} start_ticks={}'.format(
            name, uid, fields[0], fields[1], fields[2], fields[3], fields[19]), flush=True)
        matched += 1
    except FileNotFoundError:
        # Normal exit or PID race; non-atomic census cannot establish absence.
        errors += 1
    except (OSError, ValueError) as e:
        errors += 1
        print('NOT_CHECKABLE pid={} error={}'.format(name, type(e).__name__), flush=True)
print('B1_CENSUS_END matches={} raced_or_unreadable={}'.format(matched, errors), flush=True)
```

A match is an observation, not permission to signal or proof of ownership by path alone. No match does not prove absence of hidden processes, detached descendants without the path in argv, inaccessible proc entries, or processes that exit or start during traversal. All identities are point-in-time and PID reuse is possible. Read-only follow-up and any restoration remain subject to existing STOP and author rules.
