#!/usr/bin/env bash
# Read-only engineering candidate. Do not run before independent review.
set -euo pipefail
printf 'utc='; date -u +%FT%TZ
printf 'host='; hostname -s
printf 'identity='; id
[[ $(hostname -s) == TASL-7 && $(id -u) == 1011 && $HOME == /home/dowling ]] || {
  printf 'STOP: wrong host or account\n' >&2; exit 1;
}
printf '%s\n' 'current membership:'
cat /proc/self/cgroup
printf '%s\n' 'read-only cgroup metadata:'
base=/sys/fs/cgroup/user.slice/user-1011.slice
service="$base/user@1011.service"
for p in /sys/fs/cgroup /sys/fs/cgroup/user.slice "$base" "$service"; do
  [[ ! -L $p && -d $p ]] || { printf 'STOP: unsafe or missing cgroup directory: %s\n' "$p" >&2; exit 1; }
  stat -c 'directory uid=%u gid=%g mode=%a path=%n' "$p"
done
for p in "$base/cgroup.procs" "$service/cgroup.procs"; do
  [[ ! -L $p && -f $p ]] || { printf 'STOP: unsafe or missing cgroup.procs: %s\n' "$p" >&2; exit 1; }
  stat -c 'procs uid=%u gid=%g mode=%a path=%n' "$p"
  if [[ -w $p ]]; then access=yes; else access=no; fi
  printf 'write_access=%s path=%s\n' "$access" "$p"
done
for p in "$base/cgroup.type" "$base/cgroup.subtree_control" "$service/cgroup.type" "$service/cgroup.subtree_control"; do
  [[ ! -L $p && -f $p && -r $p ]] || { printf 'STOP: unreadable cgroup control: %s\n' "$p" >&2; exit 1; }
  printf 'control %s: ' "$p"; cat "$p"
done
printf '%s\n' 'service delegation xattr (observation only):'
python3 -I -S -B - "$service" <<'PY'
import errno
import os
import sys
try:
    value = os.getxattr(sys.argv[1], 'user.delegate', follow_symlinks=False)
except OSError as exc:
    print('user.delegate: NOT_CHECKABLE errno=%s' % exc.errno)
else:
    print('user.delegate bytes:', repr(value))
PY
printf '%s\n' 'inspection_complete: read-only; no delegation or migration inferred'
