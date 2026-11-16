#!/usr/bin/env bash
# DRAFT: engineering-only, parent and test-owned child, no remote evidence writes.
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
printf '%s\n' 'PARENT-CHILD SHARED OFD CAPABILITY CHECK'
command -v python3
python3 -I -S -B - <<'PY'
import ctypes
import fcntl
import os
import platform
import select
import stat
import subprocess
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


def ticks(pid):
    with open('/proc/%d/stat' % pid, encoding='ascii') as handle:
        value = handle.read()
    end = value.rfind(')')
    if end < 0:
        raise RuntimeError('STOP: malformed proc stat')
    return int(value[end + 2:].split()[19])


CHILD = r"""
import os, select, sys
fd, read_end, ready_end = map(int, sys.argv[1:])
os.fstat(fd)
os.write(ready_end, b'R')
os.close(ready_end)
poll = select.poll()
poll.register(read_end, select.POLLIN | select.POLLHUP | select.POLLERR)
# Exit on EOF or timeout. Never unlock; exit closes the inherited descriptor.
if not poll.poll(15000):
    raise SystemExit('STOP: child timed out waiting for parent EOF')
if os.read(read_end, 1) != b'':
    raise SystemExit('STOP: unexpected parent pipe data')
os.close(read_end)
"""

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
    safe_to_unlock = True
    try:
        verify_directory_chain(chain)
        require_no_markers(lockdir)
        if identity(os.fstat(fd)) != identity(os.stat('gpu0.lock', dir_fd=lockdir, follow_symlinks=False)):
            raise RuntimeError('STOP: lock pathname changed during lease')
        print('flock_acquire: PASS', flush=True)
        child = None
        ends = []
        pidfds = []
        try:
            child_read, parent_write = os.pipe()
            ends.extend((child_read, parent_write))
            parent_read, child_write = os.pipe()
            ends.extend((parent_read, child_write))
            parent_pid = os.getpid()
            parent_ticks = ticks(parent_pid)
            safe_to_unlock = False
            child = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', CHILD,
                                      str(fd), str(child_read), str(child_write)],
                                     pass_fds=(fd, child_read, child_write),
                                     stdin=subprocess.DEVNULL, close_fds=True)
            for end in (child_read, child_write):
                os.close(end)
                ends.remove(end)
            poll = select.poll()
            poll.register(parent_read, select.POLLIN | select.POLLHUP | select.POLLERR)
            if not poll.poll(5000) or os.read(parent_read, 1) != b'R':
                raise RuntimeError('STOP: owned child did not become ready')
            child_ticks = ticks(child.pid)
            watchers = []
            for pid in (parent_pid, child.pid):
                pidfd = os.pidfd_open(pid, 0)
                pidfds.append(pidfd)
                with open('/proc/self/fdinfo/%d' % pidfd, encoding='ascii') as handle:
                    pids = [line.split(':', 1)[1].strip() for line in handle if line.startswith('Pid:')]
                watcher = select.poll()
                watcher.register(pidfd, select.POLLIN | select.POLLHUP | select.POLLERR)
                if pids != [str(pid)] or watcher.poll(0):
                    raise RuntimeError('STOP: pidfd identity/liveness check failed')
                watchers.append(watcher)
            if identity(os.stat('/proc/%d/fd/%d' % (child.pid, fd))) != identity(os.fstat(fd)):
                raise RuntimeError('STOP: child lock descriptor identity differs')
            libc = ctypes.CDLL(None, use_errno=True)
            libc.syscall.restype = ctypes.c_long
            ctypes.set_errno(0)
            rc = libc.syscall(ctypes.c_long(312), ctypes.c_long(parent_pid), ctypes.c_long(child.pid),
                              ctypes.c_long(0), ctypes.c_ulong(fd), ctypes.c_ulong(fd))
            error = ctypes.get_errno() if rc < 0 else 0
            print('kcmp_parent_child:', 'PASS' if rc == 0 else 'STOP',
                  'rc=%s errno=%s' % (rc, error), flush=True)
            if rc != 0:
                raise RuntimeError('STOP: shared OFD was not established')
            if ticks(parent_pid) != parent_ticks or ticks(child.pid) != child_ticks or any(w.poll(0) for w in watchers):
                raise RuntimeError('STOP: identity changed or process exited during kcmp')
            print('identity_and_liveness: PASS parent=%s/%s child=%s/%s' %
                  (parent_pid, parent_ticks, child.pid, child_ticks), flush=True)
        finally:
            # Closing the sole parent writer delivers EOF. Do not signal or kill.
            for end in ends:
                os.close(end)
            if child is not None:
                code = child.wait()
                safe_to_unlock = True
                print('owned_child_wait:', code, flush=True)
                if code != 0:
                    raise RuntimeError('STOP: owned child exited unsuccessfully')
            for pidfd in pidfds:
                os.close(pidfd)
    finally:
        if safe_to_unlock:
            fcntl.flock(fd, fcntl.LOCK_UN)
            print('flock_unlock: returned successfully', flush=True)
        else:
            print('STOP: child exit not confirmed; only closing own fd, no explicit unlock', flush=True)
finally:
    if fd is not None:
        os.close(fd)
    for directory_fd, _, _ in reversed(chain):
        os.close(directory_fd)
print('probe_complete: descriptors closed; process returning', flush=True)
PY
