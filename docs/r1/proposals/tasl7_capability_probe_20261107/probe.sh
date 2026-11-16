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

def identity(info):
    return (info.st_dev, info.st_ino, info.st_uid, info.st_nlink, stat.S_IFMT(info.st_mode))


def verify_directory_chain(chain):
    # Bound pathnames back to the same held directory descriptors. This is a
    # point-in-time cooperative check, not protection against a later writer.
    if identity(os.stat('/', follow_symlinks=False)) != identity(os.fstat(chain[0][0])):
        raise RuntimeError('STOP: root directory identity changed')
    for index in range(1, len(chain)):
        fd, name, expected_uid = chain[index]
        named = os.stat(name, dir_fd=chain[index - 1][0], follow_symlinks=False)
        opened = os.fstat(fd)
        if (not stat.S_ISDIR(named.st_mode) or named.st_uid != expected_uid
                or identity(named) != identity(opened)):
            raise RuntimeError('STOP: lock directory ancestor identity changed: ' + name)


def open_trusted_lock_directory():
    # All opens are relative to already verified directory FDs, without
    # following a symlink at any component; no directory or file is created.
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    chain = []
    try:
        root = os.open('/', flags)
        chain.append((root, '/', 0))
        root_info = os.fstat(root)
        if not stat.S_ISDIR(root_info.st_mode) or root_info.st_uid != 0:
            raise RuntimeError('STOP: root directory is not root-owned')
        for name, owner in (('home', 0), ('dowling', os.getuid()), ('r1_locks', os.getuid())):
            parent = chain[-1][0]
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISDIR(named.st_mode) or named.st_uid != owner:
                raise RuntimeError('STOP: unsafe lock directory component: ' + name)
            fd = os.open(name, flags, dir_fd=parent)
            chain.append((fd, name, owner))
            if identity(named) != identity(os.fstat(fd)):
                raise RuntimeError('STOP: lock directory component changed: ' + name)
        verify_directory_chain(chain)
        return chain
    except BaseException:
        for fd, _, _ in reversed(chain):
            os.close(fd)
        raise


def require_no_markers(dirfd):
    for name in ('trackx_evidence.active', 'trackp_evidence.active'):
        try:
            os.stat(name, dir_fd=dirfd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise RuntimeError('STOP: active or ambiguous marker: ' + name)


print('system_python:', sys.executable, sys.version.replace('\n', ' '), flush=True)
if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    raise SystemExit('STOP: kcmp ABI is not Linux x86_64')
chain = open_trusted_lock_directory()
fd = None
try:
    lockdir = chain[-1][0]
    require_no_markers(lockdir)
    before = os.stat('gpu0.lock', dir_fd=lockdir, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid() or before.st_nlink != 1:
        raise RuntimeError('STOP: existing lock is not an owned single-link regular file')
    fd = os.open('gpu0.lock', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=lockdir)
    actual = os.fstat(fd)
    named = os.stat('gpu0.lock', dir_fd=lockdir, follow_symlinks=False)
    if identity(actual) != identity(before) or identity(actual) != identity(named):
        raise RuntimeError('STOP: lock descriptor and pathname identity differ')
    verify_directory_chain(chain)
    require_no_markers(lockdir)
    print('lock_directory_identity:', identity(os.fstat(lockdir)), flush=True)
    print('lock_identity:', actual.st_dev, actual.st_ino, actual.st_uid, actual.st_nlink, flush=True)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        print('flock_acquire: STOP errno=%s' % exc.errno, flush=True)
        raise
    try:
        verify_directory_chain(chain)
        require_no_markers(lockdir)
        named = os.stat('gpu0.lock', dir_fd=lockdir, follow_symlinks=False)
        if identity(os.fstat(fd)) != identity(named):
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
    if fd is not None:
        os.close(fd)
    for directory_fd, _, _ in reversed(chain):
        os.close(directory_fd)
print('probe_complete: descriptors closed; process returning', flush=True)
PY
