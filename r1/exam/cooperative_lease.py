"""Synthetic-first cooperative GPU lease guard; not a production launcher.

Only the *existing* inode may be locked. The same open file description must
be explicitly passed to each potentially surviving child via ``pass_fds``.
Holding a marker or opening the same inode separately is never a substitute.

The child->guardian edge is authorised without kcmp: (i) a /proc guardian PID
+ start-tick + state observation, (ii) the exact FD dev/ino/uid observed
through /proc, and (iii) a flock re-lock plus independent-contender test,
labelled ``flock_relock_while_guardian_live``.  kcmp is used only in the
ancestor->descendant direction (guardian->runner in the guardian, runner->
native server in ``cache_runtime.verify_server_lease_inheritance``).  On the
portal (kernel 6.8.0-136, Yama ``ptrace_scope=1``) a descendant->ancestor
kcmp READ was observed to succeed while ``PTRACE_ATTACH`` was EPERM - Yama
restricts attach mode, not the kcmp READ check - so that permission is
host/kernel dependent: no edge relies on it, and an error is never accepted as
SAME.  An EPERM or any ambiguity is a STOP, never a pass.

Production dispatch remains blocked until the guardian lifecycle and native
server FD retention are independently tested and reviewed.
"""
import ctypes
import errno
import fcntl
import hashlib
import json
import math
import os
import stat
import time
from pathlib import Path

COMPLETION_VERSION = 'trackx_lease_completion/v1'
COMPLETION_KEYS = frozenset({'version', 'batch_state', 'batch_state_sha256', 'servers',
                             'runner_pid', 'runner_start_ticks'})
COMPLETION_SERVER_KEYS = frozenset({'pid', 'start_ticks', 'stopped_utc', 'record_sha256', 'record_path'})
GUARDIAN_WITNESS_METHOD = 'proc_pid_start_state_fd_identity'
FLOCK_INHERITANCE_METHOD = 'flock_relock_while_guardian_live'
KCMP_NOT_USED_NOTE = ('kcmp(KCMP_FILE) was not used for the child->guardian edge: /proc '
                      'identity, exact FD dev/ino/uid and the flock re-lock/contender checks '
                      'authorise it. On TASL-2 (kernel 6.8.0-136, Yama ptrace_scope=1) a '
                      'child->parent kcmp READ was observed to succeed while PTRACE_ATTACH was '
                      'EPERM, so descendant->ancestor kcmp permission is host/kernel dependent '
                      'and is never relied on; an error never counts as SAME.')
WITNESS_KEYS = frozenset({'pid', 'start_ticks', 'fd', 'dev', 'ino', 'uid', 'state', 'method'})


class LeaseStop(RuntimeError):
    pass


def kcmp_file_result(pid_a, pid_b, fd_a, fd_b):
    """``(rc, errno)`` of the x86-64 Linux ``KCMP_FILE`` syscall (312).

    ``rc == 0`` means both processes share one file description; a positive
    ``rc`` means they do not; ``rc is None`` means the check was not performed
    or failed (unsupported ABI, EPERM under Yama, bad arguments).  Errors are
    never evidence of SAME: callers must treat ``None`` as unproven.
    """
    vals = (pid_a, pid_b, fd_a, fd_b)
    if any(type(value) is not int or value > 2 ** 31 - 1 for value in vals):
        return (None, None)
    if pid_a <= 0 or pid_b <= 0 or fd_a < 0 or fd_b < 0:
        return (None, None)
    try:
        system = os.uname()
        if system.sysname != 'Linux' or system.machine != 'x86_64' or ctypes.sizeof(ctypes.c_void_p) != 8:
            return (None, None)
        call = ctypes.CDLL(None, use_errno=True).syscall
        call.restype = ctypes.c_long
        ctypes.set_errno(0)
        result = call(ctypes.c_long(312), ctypes.c_int(pid_a), ctypes.c_int(pid_b), ctypes.c_int(0),
                      ctypes.c_ulong(fd_a), ctypes.c_ulong(fd_b))
        if result == -1:
            return (None, ctypes.get_errno())
        return (int(result), 0)
    except (OSError, AttributeError, ValueError, TypeError, ctypes.ArgumentError):
        return (None, None)


def kcmp_same_ofd(pid_a, pid_b, fd_a, fd_b):
    """Linux x86-64 KCMP_FILE; errors and unsupported ABI never count as SAME."""
    return kcmp_file_result(pid_a, pid_b, fd_a, fd_b)[0] == 0


def validate_guardian_witness(witness):
    """Validate the /proc + FD identity record a guardian witness must present.

    Only an observed, well-formed witness is accepted; a boolean or a partial
    record is a STOP.  The method string is fixed so evidence cannot be
    relabelled as a kcmp proof it never performed.
    """
    if not isinstance(witness, dict) or set(witness) != WITNESS_KEYS:
        raise LeaseStop('STOP: guardian witness schema invalid')
    pid, ticks, fd = witness['pid'], witness['start_ticks'], witness['fd']
    dev, ino, uid = witness['dev'], witness['ino'], witness['uid']
    if any(type(value) is not int for value in (pid, ticks, fd, dev, ino, uid)):
        raise LeaseStop('STOP: guardian witness types invalid')
    if pid <= 0 or ticks <= 0 or fd < 3 or dev < 0 or ino <= 0 or uid < 0:
        raise LeaseStop('STOP: guardian witness values invalid')
    if witness['method'] != GUARDIAN_WITNESS_METHOD:
        raise LeaseStop('STOP: guardian witness method invalid')
    state = witness['state']
    if not isinstance(state, str) or not state or state in ('Z', 'X'):
        raise LeaseStop('STOP: guardian witness state not live')
    return witness


def _open_existing(path):
    if not hasattr(os, 'O_NOFOLLOW'):
        raise LeaseStop('STOP: lease nofollow unavailable')
    try:
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
        st = os.fstat(fd)
        live = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or (st.st_dev, st.st_ino) != (live.st_dev, live.st_ino):
            raise LeaseStop('STOP: lease inode is not a stable regular file')
        return fd, (st.st_dev, st.st_ino)
    except BaseException:
        if 'fd' in locals():
            os.close(fd)
        raise


def acquire_existing(path):
    """Acquire exclusive nonblocking cooperative flock, return owned descriptor.

    Caller MUST retain descriptor until all GPU services are confirmed ended;
    callers must use pass_fds, not merely copy an FD number or re-open a path.
    """
    fd, identity = _open_existing(path)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        os.close(fd)
        raise LeaseStop(f'STOP: GPU cooperative lease unavailable: {exc}') from exc
    return fd, identity


def assert_held_and_bound(fd, path, identity, *, guardian_check):
    """Verify a trusted owner's FD plus independent contender; no unlock occurs.

    The first independent contender must be blocked before the presented FD is
    re-locked. Under a continuously held guardian lock, LOCK_EX on that FD then
    succeeds only for the same flock open-file-description; a separately opened
    FD conflicts. A second contender must also remain blocked. This is a
    sampled cooperative check: guardian death between samples, PID reuse,
    concurrency, network filesystem semantics and same-UID attackers are not
    ruled out here.
    """
    if not callable(guardian_check):
        raise LeaseStop('STOP: guardian witness verifier missing')
    witnesses = []

    def guardian_alive():
        try:
            witness = guardian_check()
            validate_guardian_witness(witness)
        except LeaseStop:
            raise
        except Exception as exc:
            raise LeaseStop('STOP: lease guardian liveness check failed') from exc
        if witness['pid'] == os.getpid():
            raise LeaseStop('STOP: guardian witness is this process, not an owner')
        if witness['fd'] != fd:
            raise LeaseStop('STOP: guardian lease FD number changed')
        if (witness['dev'], witness['ino']) != identity:
            raise LeaseStop('STOP: guardian lease FD identity changed')
        witnesses.append(witness)
        return witness

    if type(fd) is not int or fd < 0:
        raise LeaseStop('STOP: missing lease FD')
    try:
        guardian_alive()
        st = os.fstat(fd)
        actual = (st.st_dev, st.st_ino)
        if actual != identity:
            raise LeaseStop('STOP: lease FD identity changed')
        uid = st.st_uid
        if witnesses[-1]['uid'] != uid:
            raise LeaseStop('STOP: guardian lease FD owner differs')
        contender, contender_identity = _open_existing(path)
        try:
            if contender_identity != identity:
                raise LeaseStop('STOP: lease path identity changed')
            try:
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise LeaseStop('STOP: lease contention unknown') from exc
            else:
                # Independent open unexpectedly acquired: FD is not proven held.
                # Closing this independent description releases only its lock.
                raise LeaseStop('STOP: independent contender acquired lease')
        finally:
            os.close(contender)
        guardian_alive()
        try:
            # Do not LOCK_UN. If guardian remains alive and holds the original
            # inode, an independently opened FD cannot acquire this flock.
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise LeaseStop('STOP: presented lease FD does not share held flock') from exc
        # If the guardian died between contention and re-flock, a distinct FD
        # can have acquired an abandoned lock. Never accept that as inheritance.
        guardian_alive()
        contender, contender_identity = _open_existing(path)
        try:
            if contender_identity != identity:
                raise LeaseStop('STOP: lease path identity changed')
            try:
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise LeaseStop('STOP: second lease contention unknown') from exc
            else:
                raise LeaseStop('STOP: second contender acquired lease')
        finally:
            os.close(contender)
        guardian_alive()
    except LeaseStop:
        raise
    except OSError as exc:
        raise LeaseStop('STOP: lease evidence unavailable') from exc
    return {'dev': identity[0], 'inode': identity[1], 'uid': uid,
            'method': FLOCK_INHERITANCE_METHOD,
            'kcmp_used': False,
            'kcmp_note': KCMP_NOT_USED_NOTE,
            'guardian': witnesses[-1],
            'guardian_witness_samples': len(witnesses),
            'contender': 'blocked',
            'scope': ('cooperative flock; same UID trusted; guardian liveness and continuous '
                      'possession NOT_CHECKABLE here; child->guardian OFD equality not kcmp-checked')}


def _read_stable_bytes(path, *, limit, label):
    if not isinstance(path, str) or not path.startswith('/') or '\x00' in path:
        raise LeaseStop(f'STOP: {label} path must be absolute')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise LeaseStop(f'STOP: {label} unreadable') from exc
    try:
        first = os.fstat(fd)
        if not stat.S_ISREG(first.st_mode) or first.st_nlink != 1:
            raise LeaseStop(f'STOP: {label} is not a stable regular file')
        pieces = []
        total = 0
        while True:
            piece = os.read(fd, 1024 * 1024)
            if not piece:
                break
            total += len(piece)
            if total > limit:
                raise LeaseStop(f'STOP: {label} exceeds the size limit')
            pieces.append(piece)
        second = os.fstat(fd)
        if (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns) != \
           (second.st_dev, second.st_ino, second.st_size, second.st_mtime_ns, second.st_ctime_ns):
            raise LeaseStop(f'STOP: {label} changed during read')
        return b''.join(pieces)
    finally:
        os.close(fd)


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _validate_iso_utc(value):
    """The recorded stop time is the ISO-8601 string written by ``_utc()``."""
    if not isinstance(value, str) or not value or len(value) > 64 or '\x00' in value:
        raise LeaseStop('STOP: completion server stopped_utc must be a non-empty ISO-8601 string')
    try:
        from datetime import datetime
        datetime.fromisoformat(value[:-1] + '+00:00' if value.endswith('Z') else value)
    except ValueError as exc:
        raise LeaseStop('STOP: completion server stopped_utc is not ISO-8601') from exc
    return value


def write_completion(evidence_dir, *, batch_state_path, servers, runner_pid, runner_start_ticks):
    """Write the Stage A completion release contract for the guardian.

    Called by the runner only after a genuinely complete Stage A run.  The file
    is created exclusively (never overwritten) and appears atomically via a
    same-directory hard link of a fsynced temporary file.  This function does
    not re-verify the lease (the runner may already have stopped its servers);
    the guardian re-verifies everything before releasing.  It refuses to write
    outside the directory the guardian announced in ``TRACKX_LEASE_EVIDENCE_DIR``.
    """
    env_dir = os.environ.get('TRACKX_LEASE_EVIDENCE_DIR', '')
    if not isinstance(evidence_dir, str) or not evidence_dir.startswith('/') or '\x00' in evidence_dir:
        raise LeaseStop('STOP: evidence dir must be an absolute path')
    if not env_dir or os.path.realpath(env_dir) != os.path.realpath(evidence_dir):
        raise LeaseStop('STOP: evidence dir does not match the guardian-provided TRACKX_LEASE_EVIDENCE_DIR')
    try:
        dst = os.stat(evidence_dir, follow_symlinks=False)
    except OSError as exc:
        raise LeaseStop('STOP: evidence dir unobservable') from exc
    if not stat.S_ISDIR(dst.st_mode):
        raise LeaseStop('STOP: evidence dir is not a directory')
    raw = _read_stable_bytes(batch_state_path, limit=16 * 1024 * 1024, label='batch_state')
    try:
        state = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise LeaseStop('STOP: batch_state is not valid JSON') from exc
    if not isinstance(state, dict) or state.get('status') != 'COMPLETE':
        raise LeaseStop('STOP: batch_state is not COMPLETE')
    if not isinstance(servers, list) or not servers:
        raise LeaseStop('STOP: completion requires at least one stopped server record')
    clean = []
    seen = set()
    for row in servers:
        if not isinstance(row, dict) or set(row) != COMPLETION_SERVER_KEYS:
            raise LeaseStop('STOP: completion server schema invalid')
        pid, ticks, stopped, record_sha = row['pid'], row['start_ticks'], row['stopped_utc'], row['record_sha256']
        record_path = row['record_path']
        if type(pid) is not int or pid <= 0:
            raise LeaseStop('STOP: completion server pid invalid')
        if type(ticks) is not int or ticks <= 0:
            raise LeaseStop('STOP: completion server start_ticks invalid')
        _validate_iso_utc(stopped)
        if not _is_sha256(record_sha):
            raise LeaseStop('STOP: completion server record_sha256 invalid')
        if pid in seen:
            raise LeaseStop('STOP: duplicate completion server pid')
        seen.add(pid)
        if not isinstance(record_path, str) or not record_path.startswith('/') or '\x00' in record_path:
            raise LeaseStop('STOP: completion server record_path must be absolute')
        record_raw = _read_stable_bytes(record_path, limit=16 * 1024 * 1024, label='server record')
        if hashlib.sha256(record_raw).hexdigest() != record_sha:
            raise LeaseStop('STOP: completion server record digest mismatch')
        clean.append({'pid': pid, 'start_ticks': ticks, 'stopped_utc': stopped,
                      'record_sha256': record_sha, 'record_path': os.path.realpath(record_path)})
    if type(runner_pid) is not int or runner_pid <= 0 or runner_pid != os.getpid():
        raise LeaseStop('STOP: completion must be written by the runner process itself')
    if type(runner_start_ticks) is not int or runner_start_ticks <= 0:
        raise LeaseStop('STOP: completion runner_start_ticks invalid')
    completion = {'version': COMPLETION_VERSION,
                  'batch_state': os.path.realpath(batch_state_path),
                  'batch_state_sha256': hashlib.sha256(raw).hexdigest(),
                  'servers': clean, 'runner_pid': runner_pid,
                  'runner_start_ticks': runner_start_ticks}
    payload = (json.dumps(completion, sort_keys=True, separators=(',', ':')) + '\n').encode()
    final = os.path.join(evidence_dir, 'lease_completion.json')
    if os.path.lexists(final):
        raise LeaseStop('STOP: completion evidence already exists; no overwrite')
    tmp = os.path.join(evidence_dir, f'.lease_completion.{os.getpid()}.{time.time_ns()}.tmp')
    fd = None
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
        written = 0
        while written < len(payload):
            count = os.write(fd, payload[written:])
            if count <= 0:
                raise OSError('zero write')
            written += count
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.link(tmp, final)
        os.unlink(tmp)
        directory = os.open(evidence_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileExistsError as exc:
        raise LeaseStop('STOP: completion evidence already exists; no overwrite') from exc
    except OSError as exc:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise LeaseStop('STOP: completion evidence cannot be written') from exc
    finally:
        if fd is not None:
            os.close(fd)
    return final
