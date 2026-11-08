#!/bin/bash
set -eu
exec /usr/bin/python3 -B - <<'PY'
import os
import time

needle = b'/home/dowling/exam-x/work/b1_6835_20261108_a/'
uid = 1011
errors = 0
matched = 0
print('B1_CENSUS_BEGIN utc=' + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), flush=True)
proc = os.open('/proc', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
try:
    for name in sorted(os.listdir(proc), key=lambda n: int(n) if n.isdigit() else -1):
        if not name.isdigit():
            continue
        directory = None
        try:
            directory = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=proc)
            if os.fstat(directory).st_uid != uid:
                continue
            fd = os.open('cmdline', os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            with os.fdopen(fd, 'rb') as f:
                cmd = f.read()
            if needle not in cmd:
                continue
            fd = os.open('stat', os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            with os.fdopen(fd, 'r') as f:
                raw = f.read()
            end = raw.rfind(')')
            if end < 0:
                raise ValueError('malformed stat')
            fields = raw[end + 2:].split()
            if len(fields) < 20:
                raise ValueError('short stat')
            print('MATCH pid={} uid={} state={} ppid={} pgid={} sid={} start_ticks={}'.format(
                name, uid, fields[0], fields[1], fields[2], fields[3], fields[19]), flush=True)
            matched += 1
        except (OSError, ValueError) as e:
            errors += 1
            print('NOT_CHECKABLE pid={} error={}'.format(name, type(e).__name__), flush=True)
        finally:
            if directory is not None:
                os.close(directory)
finally:
    os.close(proc)
print('B1_CENSUS_END matches={} raced_or_unreadable={}'.format(matched, errors), flush=True)
PY
