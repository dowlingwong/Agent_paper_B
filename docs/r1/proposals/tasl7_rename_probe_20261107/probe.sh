#!/usr/bin/env bash
# DRAFT ENGINEERING_ONLY. Do not run before exact-byte independent review.
set -euo pipefail
printf 'UTC: '; date -u +%FT%TZ
printf 'host: '; hostname -s
printf 'identity: '; id
if [[ $(hostname -s) != TASL-7 || $(id -u) != 1011 || $HOME != /home/dowling ]]; then
  printf 'STOP: wrong host/account/home\n' >&2; exit 1
fi
printf '%s\n' 'LOCK DIRECTORY'
ls -la "$HOME/r1_locks"
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  p="$repo/docs/r1/STATUS.md"
  [[ ! -L $p && -f $p && -r $p ]] || { printf 'STOP: invalid STATUS %s\n' "$p" >&2; exit 1; }
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
' || { printf 'STOP: GPU UUID or utilization differs\n' >&2; exit 1; }
apps=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits)
printf 'compute-app-pids: %s\n' "$apps"
[[ -z ${apps//[[:space:]]/} ]] || { printf 'STOP: GPU compute app present or census ambiguous\n' >&2; exit 1; }
command -v python3
python3 -I -S -B - <<'PY'
import ctypes
import errno
import hashlib
import os
import platform
import stat
import sys

# Fixed name permits a single invocation, never a retry or reuse. Any collision STOPs.
NAME = 'rename_capability_probe_20261107_7d322b6c3a1e4c2f'
NOREPLACE, EXCHANGE = 1, 2
DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
OPEN_NEW = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
fds = []

def identity(info):
    return (info.st_dev, info.st_ino, info.st_uid, stat.S_IFMT(info.st_mode))

def open_component(parent, name, owner):
    named = os.stat(name, dir_fd=parent, follow_symlinks=False)
    if not stat.S_ISDIR(named.st_mode) or named.st_uid != owner:
        raise RuntimeError('STOP: unsafe ancestor '+name)
    fd = os.open(name, DIRECTORY, dir_fd=parent)
    fds.append(fd)
    if identity(named) != identity(os.fstat(fd)):
        raise RuntimeError('STOP: ancestor changed '+name)
    return fd

def no_markers(home):
    locks = open_component(home, 'r1_locks', os.getuid())
    for name in ('trackx_evidence.active', 'trackp_evidence.active'):
        try:
            os.stat(name, dir_fd=locks, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise RuntimeError('STOP: evidence marker present or ambiguous '+name)
    print('evidence_markers: absent at observation', flush=True)

def mount_type(fd):
    # Bind the actual opened work directory to the kernel mount ID, not $HOME.
    mnt = None
    with open('/proc/self/fdinfo/%d' % fd, encoding='ascii') as stream:
        for line in stream:
            if line.startswith('mnt_id:'):
                mnt = int(line.split(':', 1)[1].strip())
    if mnt is None:
        raise RuntimeError('STOP: work mount ID missing')
    found = []
    with open('/proc/self/mountinfo', encoding='utf-8') as stream:
        for line in stream:
            fields = line.split()
            if fields and int(fields[0]) == mnt:
                sep = fields.index('-')
                found.append((fields[sep+1], fields[2], fields[4]))
    if len(found) != 1:
        raise RuntimeError('STOP: work mount ID not unique')
    return mnt, found[0]

def create_file(directory, name, payload):
    fd = os.open(name, OPEN_NEW, 0o600, dir_fd=directory)
    try:
        view = memoryview(payload)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise RuntimeError('STOP: short file write')
            view = view[n:]
        os.fsync(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise RuntimeError('STOP: new file identity invalid')
        return identity(info)
    finally:
        os.close(fd)

def read_file(directory, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise RuntimeError('STOP: observed file identity invalid')
        pieces = []
        while True:
            part = os.read(fd, 4096)
            if not part:
                break
            pieces.append(part)
        data = b''.join(pieces)
        return identity(info), data
    finally:
        os.close(fd)

def rename(directory, old, new, flags):
    result = function(directory, os.fsencode(old), directory, os.fsencode(new), flags)
    if result != 0:
        code = ctypes.get_errno()
        raise OSError(code, 'renameat2 failed', old + ' -> ' + new)

def check(directory, name, wanted_identity, wanted_data):
    actual_identity, actual_data = read_file(directory, name)
    if actual_identity != wanted_identity or actual_data != wanted_data:
        raise RuntimeError('STOP: bytes or inode differ for '+name)
    print('file:', name, 'identity:', actual_identity,
          'sha256:', hashlib.sha256(actual_data).hexdigest(), flush=True)

try:
    if sys.platform != 'linux' or platform.machine() != 'x86_64':
        raise RuntimeError('STOP: Linux x86_64 required')
    print('system_python:', sys.executable, sys.version.replace('\n', ' '), flush=True)
    root = os.open('/', DIRECTORY); fds.append(root)
    if os.fstat(root).st_uid != 0:
        raise RuntimeError('STOP: unsafe root owner')
    homeparent = open_component(root, 'home', 0)
    home = open_component(homeparent, 'dowling', os.getuid())
    no_markers(home)
    exam = open_component(home, 'exam-x', os.getuid())
    work = open_component(exam, 'work', os.getuid())
    mnt, (fstype, major_minor, mountpoint) = mount_type(work)
    print('work_mount:', mnt, fstype, major_minor, mountpoint, flush=True)
    if fstype != 'ext4':
        raise RuntimeError('STOP: expected observed ext4 work mount')
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        function = libc.renameat2
    except AttributeError as exc:
        raise RuntimeError('STOP: renameat2 unavailable') from exc
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    # Recheck names immediately before creating a test-owned object.
    for fd, parent, name in ((homeparent, root, 'home'), (home, homeparent, 'dowling'),
                             (exam, home, 'exam-x'), (work, exam, 'work')):
        if identity(os.fstat(fd)) != identity(os.stat(name, dir_fd=parent, follow_symlinks=False)):
            raise RuntimeError('STOP: ancestor changed before creation '+name)
    no_markers(home)
    print('probe_directory:', '/home/dowling/exam-x/work/'+NAME, flush=True)
    os.mkdir(NAME, 0o700, dir_fd=work)  # EEXIST is STOP; no reuse or cleanup.
    probe = os.open(NAME, DIRECTORY, dir_fd=work); fds.append(probe)
    info = os.fstat(probe)
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o077 or info.st_dev != os.fstat(work).st_dev):
        raise RuntimeError('STOP: probe directory identity/permissions invalid')
    if mount_type(probe) != (mnt, (fstype, major_minor, mountpoint)):
        raise RuntimeError('STOP: probe and work mount identities differ')
    os.fsync(work)
    a, b = b'B1 rename probe A\n', b'B1 rename probe B\n'
    aid, bid = create_file(probe, 'a', a), create_file(probe, 'b', b)
    os.fsync(probe)
    check(probe, 'a', aid, a); check(probe, 'b', bid, b)
    # Existing destination must survive a no-replace failure byte-for-byte.
    try:
        rename(probe, 'a', 'b', NOREPLACE)
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        print('noreplace_collision: PASS EEXIST', flush=True)
    else:
        raise RuntimeError('STOP: no-replace collision unexpectedly succeeded')
    check(probe, 'a', aid, a); check(probe, 'b', bid, b)
    rename(probe, 'a', 'c', NOREPLACE)
    os.fsync(probe)
    try:
        os.stat('a', dir_fd=probe, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise RuntimeError('STOP: original name still exists after move')
    check(probe, 'c', aid, a); check(probe, 'b', bid, b)
    print('noreplace_move: PASS', flush=True)
    rename(probe, 'b', 'c', EXCHANGE)
    os.fsync(probe)
    check(probe, 'b', aid, a); check(probe, 'c', bid, b)
    print('exchange: PASS; both files retained under b and c', flush=True)
    print('probe_complete: no cleanup requested', flush=True)
except BaseException as exc:
    print('STOP:', type(exc).__name__, str(exc), flush=True)
    raise
finally:
    for fd in reversed(fds):
        os.close(fd)
PY
