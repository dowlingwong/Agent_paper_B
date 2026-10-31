#!/usr/bin/env python3
"""Track X Stage A lease guardian: hold one existing flock and gate its release.

This is the *guardian* half of the cooperative same-UID lease chain; it is not a
production launcher and it does not touch a GPU, a model or a server.  It:

* validates an absolute, SHA-256-pinned manifest (fixed version/argv/files/
  environment, ``argv[0]`` a python interpreter, ``argv[1]`` the expected pinned
  runner script - by default ``<repo>/r1/scripts/exam_runner.py``);
* refuses an existing evidence directory (no resume) and never creates,
  recreates, replaces, links or unlinks the lock path;
* opens the existing lock with no-follow, requires a stable regular inode with
  link count 1, takes an exclusive nonblocking flock and checks that an
  independently opened contender cannot take it;
* starts the pinned runner with the same lock FD in ``pass_fds`` and sets the
  cooperative environment contract (``TRACKX_GPU_LEASE_FD/_DEV/_INO/_UID``,
  ``TRACKX_GPU_GUARDIAN_PID/_START_TICKS``, ``TRACKX_LEASE_EVIDENCE_DIR``);
* after the spawn, proves the runner inherited the SAME open file description
  with ``kcmp(KCMP_FILE)`` in the only legal Yama direction (guardian ancestor
  -> runner descendant); a nonzero rc or EPERM is a STOP + hold;
* releases ONLY on a validated ``lease_completion.json`` written by the runner
  after a genuinely complete Stage A run (schema, batch state COMPLETE, every
  recorded server pid absent or PID-reused, record digests, and the guardian's
  own FD identity re-checked).  On any missing/invalid evidence, runner rc != 0,
  unexpected signal or ambiguity it keeps the process+lock, writes best-effort
  STOP evidence and holds forever.

The holding state machine cannot be talked out of the FD: it ignores SIGPIPE and
terminating signals, redirects stdout/stderr to ``/dev/null``, never raises out
of the hold loop, never closes the lock FD, never calls ``LOCK_UN`` and never
signals a process.  ``SIGKILL``, ``SIGSTOP``, a host crash, or a same-UID actor
that can signal/attach this process are outside any cooperative guarantee.

Same-UID non-interference is an AUTHOR ASSUMPTION, not an observed boundary;
host-global single-server state is NOT CHECKABLE.  The executable manifest is
SHA-256-pinned, but this guardian does not prove immutable paths, trusted path
ancestry, interpreter dependency pins or absence of same-UID mutation.

Run: ``python r1/scripts/trackx_lease_guardian.py --lock L --manifest M
--manifest-sha256 S --evidence-dir E [--expected-runner R]``.
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import math
import os
import re
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

MANIFEST_VERSION = 'trackx_guardian_manifest/v1'
MANIFEST_KEYS = frozenset({'version', 'argv', 'files', 'environment'})
START_SCHEMA = 'trackx_lease_guardian_start/v1'
RUNNER_SCHEMA = 'trackx_lease_guardian_runner/v1'
INHERITANCE_SCHEMA = 'trackx_lease_guardian_inheritance/v1'
RELEASE_SCHEMA = 'trackx_lease_guardian_release/v1'
STOP_SCHEMA = 'trackx_lease_guardian_stop/v1'
COMPLETION_VERSION = 'trackx_lease_completion/v1'
COMPLETION_KEYS = frozenset({'version', 'batch_state', 'batch_state_sha256', 'servers',
                             'runner_pid', 'runner_start_ticks'})
COMPLETION_SERVER_KEYS = frozenset({'pid', 'start_ticks', 'stopped_utc', 'record_sha256', 'record_path'})
INHERITANCE_VERSION = 'trackx_lease_inheritance/v1'
KCMP_METHOD = 'kcmp_same_ofd_ancestor_to_descendant'
KCMP_DIRECTION_NOTE = ('kcmp is called only ancestor->descendant (guardian->runner); an '
                       'error/EPERM is never SAME. Descendant->ancestor kcmp READ permission '
                       'is host/kernel dependent (observed permitted on TASL-2 while '
                       'PTRACE_ATTACH was EPERM) and is not used here.')
RELEASE_REASON = 'validated_completion'
SCOPE = ('cooperative same-UID flock; same-UID non-interference is an author assumption and '
         'host-global single-server is NOT_CHECKABLE; SIGKILL/SIGSTOP/host crash cannot be covered')
PYTHON_BASENAME = re.compile(r'python(\d+(\.\d+)*)?$')


class Stop(RuntimeError):
    """A fail-closed condition; after lock acquisition this means hold forever."""


class ProcessGone(Exception):
    """The process has no /proc entry (it is absent, not merely unobservable)."""


def _utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _is_absolute(value):
    return isinstance(value, str) and value.startswith('/') and '\x00' not in value


def _read_file(path, limit=16 * 1024 * 1024):
    """Read a stable regular file without following a symlink or racing changes."""
    if not _is_absolute(path):
        raise Stop('STOP: path must be absolute')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise Stop('STOP: unable to read pinned file') from exc
    try:
        first = os.fstat(fd)
        if not stat.S_ISREG(first.st_mode) or first.st_nlink != 1:
            raise Stop('STOP: unsafe file (not a stable single-link regular file)')
        pieces, total = [], 0
        while True:
            piece = os.read(fd, min(1024 * 1024, limit + 1 - total))
            if not piece:
                break
            total += len(piece)
            if total > limit:
                raise Stop('STOP: file exceeds the read limit')
            pieces.append(piece)
        second = os.fstat(fd)
        if (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns) != \
           (second.st_dev, second.st_ino, second.st_size, second.st_mtime_ns, second.st_ctime_ns):
            raise Stop('STOP: file changed during read')
        return b''.join(pieces)
    finally:
        os.close(fd)


def _read_dir_file(dirfd, name, limit):
    """Read evidence created by the runner inside the guardian's evidence dir."""
    if not isinstance(name, str) or not name or '/' in name or name in ('.', '..') or '\x00' in name:
        raise Stop('STOP: evidence name must be a plain file name')
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=dirfd)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise Stop('STOP: evidence file cannot be opened safely') from exc
    try:
        first = os.fstat(fd)
        if not stat.S_ISREG(first.st_mode) or first.st_nlink != 1:
            raise Stop('STOP: evidence is not a stable single-link regular file')
        pieces, total = [], 0
        while True:
            piece = os.read(fd, min(1024 * 1024, limit + 1 - total))
            if not piece:
                break
            total += len(piece)
            if total > limit:
                raise Stop('STOP: evidence exceeds the read limit')
            pieces.append(piece)
        second = os.fstat(fd)
        if (first.st_dev, first.st_ino, first.st_size, first.st_mtime_ns, first.st_ctime_ns) != \
           (second.st_dev, second.st_ino, second.st_size, second.st_mtime_ns, second.st_ctime_ns):
            raise Stop('STOP: evidence changed during read')
        return b''.join(pieces)
    finally:
        os.close(fd)


def process_start_ticks(pid, *, proc_root='/proc'):
    """``/proc/<pid>/stat`` start time; ProcessGone when the pid is absent."""
    if type(pid) is not int or pid <= 0:
        raise Stop('STOP: invalid PID')
    try:
        raw = (Path(proc_root) / str(pid) / 'stat').read_text()
    except FileNotFoundError as exc:
        raise ProcessGone(pid) from exc
    except OSError as exc:
        raise Stop('STOP: process identity not observable') from exc
    close = raw.rfind(')')
    if close < 0:
        raise Stop('STOP: process stat unparseable')
    fields = raw[close + 2:].split()
    if len(fields) < 20:
        raise Stop('STOP: process stat truncated')
    try:
        ticks = int(fields[19])
    except (ValueError, IndexError) as exc:
        raise Stop('STOP: process start time unparseable') from exc
    if ticks <= 0:
        raise Stop('STOP: invalid process start time')
    return ticks


def _observe_ticks(pid, start_ticks, proc_root):
    if start_ticks is process_start_ticks:
        return process_start_ticks(pid, proc_root=proc_root)
    return start_ticks(pid)


def process_state(pid, *, proc_root='/proc'):
    try:
        status = (Path(proc_root) / str(pid) / 'status').read_text()
    except OSError as exc:
        raise Stop('STOP: process state not observable') from exc
    for line in status.splitlines():
        if line.startswith('State:'):
            fields = line.split()
            if len(fields) >= 2 and fields[1]:
                return fields[1]
            break
    raise Stop('STOP: process state unreadable')


def kcmp_file_result(pid_a, pid_b, fd_a, fd_b):
    """``(rc, errno)`` of x86-64 Linux ``KCMP_FILE`` (syscall 312); errors are None."""
    import ctypes
    values = (pid_a, pid_b, fd_a, fd_b)
    if any(type(value) is not int or value > 2 ** 31 - 1 for value in values):
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


def _kcmp_check(kcmp, pid_a, pid_b, fd):
    """Interpret an injected ``kcmp_same_ofd``-compatible callable as (rc, errno)."""
    result = kcmp(pid_a, pid_b, fd, fd)
    if isinstance(result, tuple) and len(result) == 2:
        rc, err = result
        return (rc if type(rc) is int else None, err if type(err) is int else None)
    if result is True:
        return (0, 0)
    return (None, None)


def validate_manifest(raw, expected_sha, *, expected_runner):
    """Validate the pinned manifest bytes; every deviation from the fixed schema is a STOP."""
    if not _is_sha256(expected_sha):
        raise Stop('STOP: malformed manifest sha')
    if _sha256(raw) != expected_sha:
        raise Stop('STOP: manifest hash mismatch')
    try:
        manifest = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise Stop('STOP: invalid manifest JSON') from exc
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_KEYS:
        raise Stop('STOP: unexpected manifest schema')
    if manifest['version'] != MANIFEST_VERSION:
        raise Stop('STOP: unsupported manifest version')
    argv, files, env = manifest['argv'], manifest['files'], manifest['environment']
    if not isinstance(argv, list) or len(argv) < 2:
        raise Stop('STOP: invalid argv')
    if not all(isinstance(item, str) and item and '\x00' not in item for item in argv):
        raise Stop('STOP: invalid argv entry')
    if not _is_absolute(argv[0]) or not _is_absolute(argv[1]):
        raise Stop('STOP: interpreter and runner must be absolute paths')
    if not PYTHON_BASENAME.match(Path(argv[0]).name):
        raise Stop('STOP: argv[0] must be a python interpreter, not a wrapper')
    if not argv[1].endswith('.py'):
        raise Stop('STOP: argv[1] must be a python runner script')
    if not _is_absolute(expected_runner) or os.path.normpath(argv[1]) != os.path.normpath(expected_runner):
        raise Stop('STOP: argv[1] is not the expected pinned runner')
    if not isinstance(files, list) or len(files) < 2:
        raise Stop('STOP: invalid file pin list')
    if not isinstance(env, dict):
        raise Stop('STOP: invalid environment')
    if not all(type(key) is str and type(value) is str and key and '=' not in key and '\x00' not in key + value
               for key, value in env.items()):
        raise Stop('STOP: invalid environment entry')
    # The guardian owns every TRACKX_ variable; a manifest may not pre-seed one.
    if any(key.startswith('TRACKX_') for key in env):
        raise Stop('STOP: reserved TRACKX_ environment key in manifest')
    checked = {}
    for row in files:
        if not isinstance(row, dict) or set(row) != {'path', 'sha256'}:
            raise Stop('STOP: invalid file pin entry')
        path, digest = row['path'], row['sha256']
        if not _is_absolute(path):
            raise Stop('STOP: pinned path must be absolute')
        if path in checked:
            raise Stop('STOP: duplicate pinned path')
        if not _is_sha256(digest):
            raise Stop('STOP: malformed file pin digest')
        if _sha256(_read_file(path, 1024 * 1024 * 1024)) != digest:
            raise Stop('STOP: executable file pin mismatch')
        checked[path] = digest
    # argv[1] (the runner) must be pinned; the interpreter may be pinned too, in
    # which case its bytes are verified above, but a python interpreter is also
    # accepted bare because the reviewed launcher pins the manuscript tree.
    if argv[1] not in checked:
        raise Stop('STOP: runner is not pinned')
    return manifest


def acquire_existing(lock_path):
    """Open exactly the existing lock path (never create/replace) and flock it."""
    fd = None
    try:
        if not _is_absolute(lock_path) or '\x00' in lock_path:
            raise Stop('STOP: lock path not absolute')
        fd = os.open(lock_path, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        current = os.fstat(fd)
        live = os.stat(lock_path, follow_symlinks=False)
        if not stat.S_ISREG(current.st_mode):
            raise Stop('STOP: lock is not a regular file')
        if current.st_nlink != 1:
            raise Stop('STOP: lock link count is not 1')
        if (current.st_dev, current.st_ino) != (live.st_dev, live.st_ino):
            raise Stop('STOP: lock path was replaced during open')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd, current
    except (OSError, Stop) as exc:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if isinstance(exc, Stop):
            raise
        raise Stop('STOP: GPU lock cannot be acquired') from exc


def assert_held(lock_path, fd, expected):
    """Re-check the held lock against a fresh independent contender; never unlock."""
    try:
        current = os.fstat(fd)
        live = os.stat(lock_path, follow_symlinks=False)
        if (current.st_dev, current.st_ino, current.st_uid) != (expected.st_dev, expected.st_ino, expected.st_uid):
            raise Stop('STOP: held lock identity changed')
        if (live.st_dev, live.st_ino) != (current.st_dev, current.st_ino):
            raise Stop('STOP: lock path no longer names the held inode')
        if current.st_nlink != 1 or live.st_nlink != 1:
            raise Stop('STOP: lock link count changed')
        contender = os.open(lock_path, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            observed = os.fstat(contender)
            if (observed.st_dev, observed.st_ino) != (current.st_dev, current.st_ino):
                raise Stop('STOP: contender opened a different inode')
            try:
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    raise Stop('STOP: lock contention unknown') from exc
            else:
                raise Stop('STOP: lease is not held against an independent contender')
        finally:
            os.close(contender)
        # Re-flock only the guardian's existing OFD; no LOCK_UN anywhere.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_uid) != (expected.st_dev, expected.st_ino, expected.st_uid):
            raise Stop('STOP: held lock identity changed after re-flock')
    except Stop:
        raise
    except OSError as exc:
        raise Stop('STOP: lock inspection failed') from exc
    return True


def persist_exclusive(dirfd, name, obj):
    """Write one evidence file exclusively inside the evidence dir (never overwrite)."""
    payload = (json.dumps(obj, sort_keys=True) + '\n').encode()
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600, dir_fd=dirfd)
    try:
        written = 0
        while written < len(payload):
            count = os.write(fd, payload[written:])
            if count <= 0:
                raise OSError('zero write')
            written += count
        os.fsync(fd)
    finally:
        os.close(fd)


def validate_completion(completion, *, runner_pid, runner_start_ticks, lock_path, lock_fd,
                        expected_lock, start_ticks=process_start_ticks, proc_root='/proc',
                        completion_sha256=None):
    """Validate the runner's completion evidence; any ambiguity is a STOP.

    The completion is only acceptable when the run genuinely finished: the
    batch state says COMPLETE, every named server pid is absent from /proc or
    has a different start-tick value (PID reuse), the server record files still
    digest-match, every server record is covered and carries a SAME-OFD lease
    inheritance row, and the guardian's own lock FD identity is unchanged.
    """
    assert_held(lock_path, lock_fd, expected_lock)
    if not isinstance(completion, dict) or set(completion) != COMPLETION_KEYS:
        raise Stop('STOP: completion schema is not the pinned contract')
    if completion['version'] != COMPLETION_VERSION:
        raise Stop('STOP: unsupported completion version')
    if type(completion['runner_pid']) is not int or completion['runner_pid'] != runner_pid:
        raise Stop('STOP: completion runner pid is not the runner this guardian started')
    if type(completion['runner_start_ticks']) is not int or \
       completion['runner_start_ticks'] != runner_start_ticks:
        raise Stop('STOP: completion runner start ticks changed')
    batch_state = completion['batch_state']
    if not _is_absolute(batch_state):
        raise Stop('STOP: completion batch_state must be an absolute path')
    if not _is_sha256(completion['batch_state_sha256']):
        raise Stop('STOP: completion batch_state digest malformed')
    state_raw = _read_file(batch_state, 16 * 1024 * 1024)
    if _sha256(state_raw) != completion['batch_state_sha256']:
        raise Stop('STOP: completion batch_state digest mismatch')
    try:
        state = json.loads(state_raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise Stop('STOP: completion batch_state is not JSON') from exc
    if not isinstance(state, dict) or state.get('status') != 'COMPLETE':
        raise Stop('STOP: completion batch_state is not COMPLETE')
    servers = completion['servers']
    if not isinstance(servers, list) or not servers:
        raise Stop('STOP: completion names no stopped servers')
    cleaned = []
    seen = set()
    for row in servers:
        if not isinstance(row, dict) or set(row) != COMPLETION_SERVER_KEYS:
            raise Stop('STOP: completion server entry schema invalid')
        pid, ticks, stopped, record_sha = row['pid'], row['start_ticks'], row['stopped_utc'], row['record_sha256']
        record_path = row['record_path']
        if not _is_absolute(record_path) or '\x00' in record_path:
            raise Stop('STOP: completion server record_path must be absolute')
        if type(pid) is not int or pid <= 0:
            raise Stop('STOP: completion server pid invalid')
        if type(ticks) is not int or ticks <= 0:
            raise Stop('STOP: completion server start_ticks invalid')
        if not isinstance(stopped, str) or not stopped or len(stopped) > 64 or '\x00' in stopped:
            raise Stop('STOP: completion server stopped_utc must be a non-empty ISO-8601 string')
        try:
            from datetime import datetime
            datetime.fromisoformat(stopped[:-1] + '+00:00' if stopped.endswith('Z') else stopped)
        except ValueError as exc:
            raise Stop('STOP: completion server stopped_utc is not ISO-8601') from exc
        if not _is_sha256(record_sha):
            raise Stop('STOP: completion server record digest malformed')
        if pid in seen:
            raise Stop('STOP: duplicate completion server pid')
        seen.add(pid)
        try:
            observed = _observe_ticks(pid, start_ticks, proc_root)
        except ProcessGone:
            observed = None
        if observed is not None and observed == ticks:
            raise Stop(f'STOP: recorded server pid {pid} is still live with the same start ticks')
        cleaned.append({'pid': pid, 'start_ticks': ticks, 'stopped_utc': stopped,
                        'record_sha256': record_sha, 'record_path': os.path.realpath(record_path)})
    # The run root is the batch-state directory; EVERY native-server record the
    # runner ever wrote under it must be covered by the completion (qualification
    # probes, replay servers and CPU-control servers alike), and no unlisted
    # record may exist (survivor blind spot).  Symlinks are never followed.
    run_root = Path(batch_state).parent
    candidates = []
    try:
        for dirpath, dirnames, filenames in os.walk(run_root, followlinks=False):
            dirnames[:] = [name for name in dirnames if not name.startswith('.')]
            for name in filenames:
                if name.startswith('llama_server_') and name.endswith('.json'):
                    candidates.append(Path(dirpath) / name)
    except OSError as exc:
        raise Stop('STOP: server record tree unreadable') from exc
    candidates.sort()
    if not candidates:
        raise Stop('STOP: completion names no server record files under the run root')
    records = []
    for path in candidates:
        raw = _read_file(str(path), 16 * 1024 * 1024)
        real_path = os.path.realpath(path)
        try:
            document = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as exc:
            raise Stop('STOP: server record is not JSON') from exc
        if not isinstance(document, dict):
            raise Stop('STOP: server record schema invalid')
        pid = document.get('pid')
        if type(pid) is not int or pid <= 0:
            raise Stop('STOP: server record pid invalid')
        inheritance = document.get('lease_inheritance')
        if not isinstance(inheritance, dict):
            raise Stop('STOP: server record lacks lease inheritance evidence')
        if inheritance.get('version') != INHERITANCE_VERSION or inheritance.get('kcmp_rc') != 0 or \
           inheritance.get('kcmp_same_ofd') is not True or inheritance.get('server_pid') != pid:
            raise Stop('STOP: server record lease inheritance is not a SAME-OFD proof')
        ticks = inheritance.get('server_start_ticks')
        if type(ticks) is not int or ticks <= 0:
            raise Stop('STOP: server record start ticks invalid')
        stopped = document.get('stopped_utc')
        if not isinstance(stopped, str) or not stopped:
            raise Stop('STOP: server record has no stop time')
        records.append({'path': real_path, 'sha256': _sha256(raw), 'pid': pid, 'start_ticks': ticks,
                        'stopped_utc': stopped})
    record_paths = [record['path'] for record in records]
    if len(set(record_paths)) != len(record_paths):
        raise Stop('STOP: duplicate server record path under the run root')
    completion_paths = [row['record_path'] for row in cleaned]
    records_set, completion_set = set(record_paths), set(completion_paths)
    if records_set != completion_set:
        missing = sorted(records_set - completion_set)
        extra = sorted(completion_set - records_set)
        raise Stop(f'STOP: completion does not cover every server record under the run root '
                   f'(uncovered={len(missing)}, foreign={len(extra)})')
    by_path = {record['path']: record for record in records}
    for row in cleaned:
        record = by_path[row['record_path']]
        if record['sha256'] != row['record_sha256'] or record['pid'] != row['pid']:
            raise Stop('STOP: completion server record digest/pid does not match its record file')
        if record['start_ticks'] != row['start_ticks'] or record['stopped_utc'] != row['stopped_utc']:
            raise Stop('STOP: completion server identity/time differs from its record')
    assert_held(lock_path, lock_fd, expected_lock)
    return {'batch_state': batch_state, 'batch_state_sha256': completion['batch_state_sha256'],
            'runner_pid': runner_pid, 'runner_start_ticks': runner_start_ticks,
            'servers': [{'pid': row['pid'], 'start_ticks': row['start_ticks'],
                         'record_sha256': row['record_sha256']} for row in cleaned],
            'completion_sha256': completion_sha256,
            'record_files': [record['path'] for record in records],
            'records_verified': len(records),
            'scope': SCOPE}


def hold_forever(lock_path, fd, expected, dirfd, reason):
    """Retain the FD and the flock unconditionally.

    Nothing here can release the lock or terminate the process: SIGPIPE and the
    catching-terminating signals are ignored, stdout/stderr are replaced by
    ``/dev/null`` so no write can raise, STOP evidence is best effort, and the
    loop swallows every exception.  The lock FD is never closed and LOCK_UN is
    never called.
    """
    ignore = ('SIGPIPE', 'SIGHUP', 'SIGINT', 'SIGQUIT', 'SIGTERM', 'SIGUSR1', 'SIGUSR2', 'SIGALRM')
    for name in ignore:
        number = getattr(signal, name, None)
        if number is None:
            continue
        try:
            signal.signal(number, signal.SIG_IGN)
        except (OSError, ValueError, RuntimeError):
            pass
    try:
        null = os.open(os.devnull, os.O_WRONLY)
        try:
            for target in (1, 2):
                try:
                    os.dup2(null, target)
                except OSError:
                    pass
        finally:
            if null > 2:
                try:
                    os.close(null)
                except OSError:
                    pass
    except OSError:
        pass
    try:
        persist_exclusive(dirfd, 'STOP.json', {
            'schema': STOP_SCHEMA, 'status': 'STOP', 'reason': str(reason),
            'guardian_pid': os.getpid(), 'lock_path': lock_path,
            'dev': expected.st_dev, 'ino': expected.st_ino, 'uid': expected.st_uid,
            'lease_retained': True, 'retry_permitted': False,
            'completed_release': False, 'utc': _utc(), 'monotonic_ns': time.monotonic_ns(),
            'scope': SCOPE})
    except BaseException:
        pass
    while True:
        try:
            time.sleep(30)
        except BaseException:
            continue


def _retain_forever(lock_path, fd, expected, dirfd, reason):
    """Belt-and-braces wrapper: the process must never leave this loop alive."""
    while True:
        try:
            hold_forever(lock_path, fd, expected, dirfd, reason)
        except BaseException:
            continue


def _release(dirfd, fd, expected, lock_path, runner_pid, summary):
    """Write release evidence, then close the FD (dropping the flock) and return."""
    persist_exclusive(dirfd, 'lease_release.json', {
        'schema': RELEASE_SCHEMA, 'released': True, 'reason': RELEASE_REASON,
        'guardian_pid': os.getpid(), 'lease_fd': fd, 'lock_path': lock_path,
        'dev': expected.st_dev, 'ino': expected.st_ino, 'uid': expected.st_uid,
        'lock_file_modified': False, 'lock_file_deleted': False,
        'method': 'close_fd_after_validated_completion',
        'completion': summary, 'utc': _utc(), 'monotonic_ns': time.monotonic_ns(),
        'kcmp_direction': 'guardian_ancestor->runner_descendant',
        'scope': SCOPE})
    os.close(fd)
    return summary


def run(lock_path, manifest_path, manifest_sha, evidence_dir, *, expected_runner,
        start_ticks=process_start_ticks, proc_root='/proc', kcmp=kcmp_file_result):
    """Acquire, hold and either release on validated completion or hold forever."""
    manifest = validate_manifest(_read_file(manifest_path), manifest_sha, expected_runner=expected_runner)
    if not _is_absolute(evidence_dir):
        raise Stop('STOP: evidence dir must be absolute')
    if os.path.lexists(evidence_dir):
        raise Stop('STOP: evidence directory exists; never resume an existing attempt')
    os.mkdir(evidence_dir, 0o700)
    dirfd = os.open(evidence_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    fd = None
    expected = None
    try:
        fd, expected = acquire_existing(lock_path)
        guardian_pid = os.getpid()
        try:
            guardian_ticks = _observe_ticks(guardian_pid, start_ticks, proc_root)
        except ProcessGone as exc:
            raise Stop('STOP: guardian process identity vanished') from exc
        assert_held(lock_path, fd, expected)
        env = dict(manifest['environment'])
        env.update({'TRACKX_GPU_LEASE_FD': str(fd),
                    'TRACKX_GPU_LEASE_DEV': str(expected.st_dev),
                    'TRACKX_GPU_LEASE_INO': str(expected.st_ino),
                    'TRACKX_GPU_LEASE_UID': str(expected.st_uid),
                    'TRACKX_GPU_GUARDIAN_PID': str(guardian_pid),
                    'TRACKX_GPU_GUARDIAN_START_TICKS': str(guardian_ticks),
                    'TRACKX_LEASE_EVIDENCE_DIR': evidence_dir})
        persist_exclusive(dirfd, 'start.json', {
            'schema': START_SCHEMA, 'guardian_pid': guardian_pid,
            'guardian_start_ticks': guardian_ticks, 'lease_fd': fd,
            'dev': expected.st_dev, 'ino': expected.st_ino, 'uid': expected.st_uid,
            'lock_path': lock_path, 'lock_nlink': expected.st_nlink,
            'manifest_sha256': manifest_sha, 'expected_runner': expected_runner,
            'argv': manifest['argv'], 'evidence_dir': evidence_dir,
            'environment_keys': sorted(env), 'utc': _utc(),
            'monotonic_ns': time.monotonic_ns(), 'scope': SCOPE})
        stop_requested = [False]

        def record_signal(signum, frame):
            stop_requested[0] = True

        for name in ('SIGHUP', 'SIGINT', 'SIGTERM'):
            number = getattr(signal, name, None)
            if number is not None:
                signal.signal(number, record_signal)
        process = subprocess.Popen(manifest['argv'], env=env, pass_fds=(fd,), close_fds=True,
                                   start_new_session=True)
        try:
            runner_ticks = _observe_ticks(process.pid, start_ticks, proc_root)
        except ProcessGone as exc:
            raise Stop('STOP: runner process identity vanished before kcmp') from exc
        persist_exclusive(dirfd, 'runner.json', {
            'schema': RUNNER_SCHEMA, 'runner_pid': process.pid, 'runner_start_ticks': runner_ticks,
            'utc': _utc(), 'monotonic_ns': time.monotonic_ns()})
        rc, errno_value = _kcmp_check(kcmp, process.pid, guardian_pid, fd)
        if rc != 0:
            raise Stop(f'STOP: guardian cannot prove the runner inherited the lease FD '
                       f'(kcmp ancestor->descendant rc={rc} errno={errno_value})')
        persist_exclusive(dirfd, 'lease_inheritance.json', {
            'schema': INHERITANCE_SCHEMA, 'method': KCMP_METHOD, 'kcmp_rc': rc,
            'kcmp_errno': errno_value, 'kcmp_same_ofd': True, 'kcmp_errors_never_same': True,
            'kcmp_pid_a': process.pid, 'kcmp_pid_b': guardian_pid,
            'kcmp_fd_a': fd, 'kcmp_fd_b': fd, 'lease_fd': fd,
            'dev': expected.st_dev, 'ino': expected.st_ino, 'uid': expected.st_uid,
            'guardian_pid': guardian_pid, 'guardian_start_ticks': guardian_ticks,
            'runner_pid': process.pid, 'runner_start_ticks': runner_ticks,
            'yama_direction': f'kcmp(ancestor guardian {guardian_pid} -> descendant runner {process.pid}); '
                              f'{KCMP_DIRECTION_NOTE}',
            'utc': _utc(), 'monotonic_ns': time.monotonic_ns(),
            'scope': ('same-UID cooperative assumption; OFD identity proved only for this '
                      'ancestor->descendant edge at this sample; host-global single-server NOT_CHECKABLE')})
        while True:
            if stop_requested[0]:
                raise Stop('STOP: guardian received a termination signal; lease retained')
            assert_held(lock_path, fd, expected)
            code = process.poll()
            if code is None:
                time.sleep(1)
                continue
            if code != 0:
                raise Stop(f'STOP: runner ended rc={code}; descendants/completion not proven')
            raw = _read_dir_file(dirfd, 'lease_completion.json', 1024 * 1024)
            if raw is None:
                raise Stop('STOP: runner exited 0 without lease_completion.json')
            try:
                completion = json.loads(raw)
            except (ValueError, UnicodeDecodeError) as exc:
                raise Stop('STOP: lease_completion.json is not JSON') from exc
            summary = validate_completion(completion, runner_pid=process.pid,
                                          runner_start_ticks=runner_ticks, lock_path=lock_path,
                                          lock_fd=fd, expected_lock=expected,
                                          start_ticks=start_ticks, proc_root=proc_root,
                                          completion_sha256=_sha256(raw))
            return _release(dirfd, fd, expected, lock_path, process.pid, summary)
    except BaseException as exc:
        if fd is None:
            raise
        _retain_forever(lock_path, fd, expected, dirfd, exc)


def _default_expected_runner():
    return str(Path(__file__).resolve().parents[2] / 'r1/scripts/exam_runner.py')


def _best_effort_stderr(message):
    try:
        os.write(2, (message + '\n').encode())
    except BaseException:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description='Track X Stage A cooperative lease guardian')
    parser.add_argument('--lock', required=True, help='existing GPU lock file; never created here')
    parser.add_argument('--manifest', required=True, help='absolute pinned manifest path')
    parser.add_argument('--manifest-sha256', required=True, help='SHA-256 of the manifest bytes')
    parser.add_argument('--evidence-dir', required=True, help='new evidence directory; no resume')
    parser.add_argument('--expected-runner', default=_default_expected_runner(),
                        help='the one pinned runner argv[1] must equal (default: repo exam_runner.py)')
    args = parser.parse_args(argv)
    try:
        run(args.lock, args.manifest, args.manifest_sha256, args.evidence_dir,
            expected_runner=args.expected_runner)
    except Stop as exc:
        # Only reachable before the lock is retained; a retained guardian never returns.
        _best_effort_stderr(f'STOP: {exc}')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
