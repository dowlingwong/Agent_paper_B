#!/usr/bin/env bash
# DRAFT: engineering-only, one process, no remote evidence writes.
# Run only after fresh independent review and authorized site conditions.
set -euo pipefail
printf 'UTC: '; date -u +%FT%TZ
printf 'host: '; hostname -s
printf 'identity: '; id
if [[ $(hostname -s) != TASL-7 || $(id -u) != 1011 || $HOME != /home/dowling ]]; then
  printf 'STOP: host or account differs from the reviewed scope\n' >&2; exit 1
fi
printf '%s\n' 'LOCK DIRECTORY'
ls -la "$HOME/r1_locks"
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  p="$repo/docs/r1/STATUS.md"
  if [[ -L $p || ! -f $p || ! -r $p ]]; then
    printf 'STOP: STATUS missing, unreadable, non-regular or symlink: %s\n' "$p" >&2; exit 1
  fi
  before=$(sha256sum "$p" | cut -d ' ' -f1)
  printf 'STATUS BEGIN %s sha256=%s\n' "$p" "$before"
  cat "$p"
  after=$(sha256sum "$p" | cut -d ' ' -f1)
  [[ $before == "$after" ]] || { printf 'STOP: STATUS changed during read\n' >&2; exit 1; }
  printf 'STATUS END %s sha256=%s\n' "$p" "$after"
done
for marker in trackx_evidence.active trackp_evidence.active; do
  p="$HOME/r1_locks/$marker"
  if [[ -e $p || -L $p ]]; then printf 'STOP: active or ambiguous marker %s\n' "$p" >&2; exit 1; fi
done
printf '%s\n' 'GPU OBSERVATION'
gpu=$(nvidia-smi --query-gpu=uuid,utilization.gpu --format=csv,noheader,nounits)
printf '%s\n' "$gpu"
printf '%s\n' "$gpu" | awk -F, '
  { gsub(/^[[:space:]]+|[[:space:]]+$/, "", $1); gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2) }
  NR == 1 && NF == 2 && $1 == "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1" &&
    $2 ~ /^[0-9]+([.][0-9]+)?$/ && ($2 + 0) <= 5 { ok = 1 }
  END { if (NR != 1 || !ok) exit 1 }
' || { printf 'STOP: GPU UUID or observed utilization differs\n' >&2; exit 1; }
apps=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits)
printf 'compute-app-pids: %s\n' "$apps"
[[ -z ${apps//[[:space:]]/} ]] || { printf 'STOP: GPU compute app present or census ambiguous\n' >&2; exit 1; }
for marker in trackx_evidence.active trackp_evidence.active; do
  p="$HOME/r1_locks/$marker"
  if [[ -e $p || -L $p ]]; then printf 'STOP: marker appeared %s\n' "$p" >&2; exit 1; fi
done
printf '%s\n' 'SINGLE-PROCESS LEASE AND CAPABILITY CHECK'
command -v python3
python3 -I -S -B - <<'PY'
import ctypes
import fcntl
import os
import platform
import select
import stat
import sys

path = '/home/dowling/r1_locks/gpu0.lock'
print('system_python:', sys.executable, sys.version.replace('\n', ' '), flush=True)
if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    raise SystemExit('STOP: kcmp ABI is not Linux x86_64')
before = os.stat(path, follow_symlinks=False)
if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or before.st_nlink != 1:
    raise SystemExit('STOP: existing lock identity is not an owned single-link regular file')
fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
try:
    actual = os.fstat(fd)
    named = os.stat(path, follow_symlinks=False)
    key = lambda info: (info.st_dev, info.st_ino, info.st_uid, info.st_nlink, stat.S_IFMT(info.st_mode))
    if key(actual) != key(before) or key(actual) != key(named):
        raise RuntimeError('STOP: lock descriptor and pathname identity differ')
    print('lock_identity:', actual.st_dev, actual.st_ino, actual.st_uid, actual.st_nlink, flush=True)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        print('flock_acquire: STOP errno=%s' % exc.errno, flush=True)
        raise
    try:
        named = os.stat(path, follow_symlinks=False)
        if key(os.fstat(fd)) != key(named):
            raise RuntimeError('STOP: lock pathname changed during lease')
        print('flock_acquire: PASS single-process point-in-time', flush=True)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        print('flock_unlock: returned successfully', flush=True)
    # Capability observations occur after unlock, so they cannot prolong the lease.
    # This process never forks and no other process inherits fd.
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    ctypes.set_errno(0)
    pid = os.getpid()
    rc = libc.syscall(ctypes.c_long(312), ctypes.c_long(pid), ctypes.c_long(pid),
                      ctypes.c_long(0), ctypes.c_ulong(fd), ctypes.c_ulong(fd))
    error = ctypes.get_errno() if rc < 0 else 0
    print('kcmp_self_same_fd:', 'PASS' if rc == 0 else 'NOT_CHECKABLE', 'rc=%s errno=%s' % (rc, error), flush=True)
    try:
        pidfd = os.pidfd_open(pid, 0)
    except (AttributeError, OSError) as exc:
        print('pidfd_self: NOT_CHECKABLE', type(exc).__name__, getattr(exc, 'errno', None), flush=True)
    else:
        try:
            with open('/proc/self/fdinfo/%d' % pidfd, encoding='ascii') as handle:
                values = [line.split(':', 1)[1].strip() for line in handle if line.startswith('Pid:')]
            watcher = select.poll()
            watcher.register(pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
            ready = watcher.poll(0)
            status = 'PASS' if values == [str(pid)] and not ready else 'NOT_CHECKABLE'
            print('pidfd_self:', status, 'pid_matches=%s ready=%s' % (values == [str(pid)], bool(ready)), flush=True)
        finally:
            os.close(pidfd)
finally:
    os.close(fd)
print('probe_complete: descriptors closed; process returning', flush=True)
PY
