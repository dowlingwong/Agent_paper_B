"""Cooperative B1 normal-exit receipt; not cryptographic process attestation."""
from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import stat
from pathlib import Path

from r1.exam.b1_state_preserve import ACTIVE, EXIT_RECEIPT, _NOREPLACE, _renameat2, write_exclusive_json

MAX_BYTES = 16 * 1024 * 1024
RETIRED_ACTIVE = '_to_delete/B1_ACTIVE.completed.json'
UNCERTAIN = 'B1_COMMIT_UNCERTAIN.json'


def _mount_for(path, mountinfo):
    """Choose the unambiguous most-specific Linux mount for an absolute path."""
    path = str(path)
    if not path.startswith('/') or os.path.normpath(path) != path:
        raise RuntimeError('STOP: B1 batch path is not canonical')
    matches = []
    for line in mountinfo.splitlines():
        left, separator, right = line.partition(' - ')
        fields, tail = left.split(), right.split()
        if not separator or len(fields) < 6 or len(tail) < 3 or not fields[0].isdigit() or int(fields[0]) <= 0:
            raise RuntimeError('STOP: Linux mountinfo is malformed')
        # Linux mountinfo escapes space, tab, newline and backslash as octal.
        raw = fields[4]
        mount = re.sub(r'\\(040|011|012|134)', lambda m: chr(int(m.group(1), 8)), raw)
        if '\\' in re.sub(r'\\(040|011|012|134)', '', raw):
            raise RuntimeError('STOP: Linux mountpoint escape is unsupported')
        if not mount.startswith('/') or os.path.normpath(mount) != mount:
            raise RuntimeError('STOP: Linux mountpoint is not canonical')
        if path == mount or path.startswith(mount.rstrip('/') + '/'):
            matches.append((len(mount), mount, fields[2], tail[0], fields[0]))
    if not matches:
        raise RuntimeError('STOP: B1 mount is not visible')
    longest = max(item[0] for item in matches)
    chosen = [item for item in matches if item[0] == longest]
    if len(chosen) != 1:
        raise RuntimeError('STOP: B1 mount identity is ambiguous')
    return chosen[0]


def _require_local_filesystem(batch):
    """Conservatively allow ext4/xfs; operator must qualify actual site semantics.

    Linux rename(2) documents NOREPLACE support for ext4 and xfs. This is a
    type/identity check, not proof of device locality, error atomicity or I/O
    durability. Unknown/network/FUSE/overlay mounts fail closed.
    """
    batch = Path(batch)
    if not batch.is_absolute() or batch.resolve() != batch:
        raise RuntimeError('STOP: B1 batch path is an alias')
    try:
        info = os.stat(batch, follow_symlinks=False)
        table = Path('/proc/self/mountinfo').read_text()
        _, mountpoint, dev, filesystem, mount_id = _mount_for(batch, table)
        major, minor = (int(value) for value in dev.split(':'))
    except (OSError, ValueError) as exc:
        raise RuntimeError('STOP: B1 local filesystem identity is unavailable') from exc
    if (not stat.S_ISDIR(info.st_mode) or (os.major(info.st_dev), os.minor(info.st_dev)) != (major, minor)
            or filesystem not in ('ext4', 'xfs')):
        raise RuntimeError('STOP: B1 requires a site-qualified ext4/xfs batch filesystem')
    return (mount_id, mountpoint, dev, filesystem)


def read_owned_regular(path):
    """Read a stable, non-symlink, user-owned regular file, bounded in size."""
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path:
        raise RuntimeError('STOP: B1 receipt input path is an alias')
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or before.st_mode & 0o022 or before.st_size > MAX_BYTES):
            raise RuntimeError('STOP: B1 receipt input is not an owned regular file')
        chunks = []
        total = 0
        while True:
            piece = os.read(fd, min(65536, MAX_BYTES + 1 - total))
            if not piece:
                break
            total += len(piece)
            if total > MAX_BYTES:
                raise RuntimeError('STOP: B1 receipt input too large')
            chunks.append(piece)
        after = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if key(before) != key(after) or key(after) != key(named):
            raise RuntimeError('STOP: B1 receipt input changed while read')
        return b''.join(chunks)
    finally:
        os.close(fd)


def active_and_state(batch, head, pid, *, retired=False):
    batch = Path(batch)
    if os.path.lexists(batch / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch has a STOP record')
    active_bytes = read_owned_regular(batch / (RETIRED_ACTIVE if retired else ACTIVE))
    active = json.loads(active_bytes)
    mount_identity = _require_local_filesystem(batch)
    if (not isinstance(active, dict) or set(active) != {'version','runner_pid','authorization_checkout_head','mount_identity'}
            or active.get('version') != 'b1_active/v1' or type(pid) is not int or pid <= 0
            or type(active.get('runner_pid')) is not int
            or active.get('runner_pid') != pid or active.get('authorization_checkout_head') != head
            or active.get('mount_identity') != list(mount_identity)):
        raise RuntimeError('STOP: B1 active sentinel does not bind the waited runner and authority')
    state_bytes = read_owned_regular(batch / 'batch_state.json')
    state = json.loads(state_bytes)
    if (not isinstance(state, dict) or state.get('status') != 'COMPLETE'
            or state.get('phase') != 'b1' or state.get('execution_label') != 'EVIDENCE'):
        raise RuntimeError('STOP: B1 waited runner did not leave a complete evidence state')
    if os.path.lexists(batch / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch gained a STOP record')
    return active_bytes, state_bytes


def _verified_finalization(batch, head):
    # The containment implementation must supply this module. Without it,
    # B1 cannot publish or verify a waited-exit receipt.
    try:
        from r1.exam.b1_finalization import verify_finalization
    except ImportError as exc:
        raise RuntimeError('STOP: B1 guardian finalization verifier is unavailable') from exc
    verify_finalization(batch, head)
    return read_owned_regular(Path(batch) / 'FINALIZED.json')


def _require_publication_signal_mask():
    """Caller must block catchable signals through process exit after commit."""
    try:
        masked = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        required = signal.valid_signals() - {signal.SIGKILL, signal.SIGSTOP}
    except (AttributeError, OSError, ValueError) as exc:
        raise RuntimeError('STOP: B1 publication signal mask unavailable') from exc
    if not required.issubset(masked):
        raise RuntimeError('STOP: B1 publication requires blocked catchable signals')


def _retire_active_last(batch, expected_active):
    """Linearize success with a no-replace rename; no later STOP-gated I/O.

    The receipt, finalization and state must already be validated and fsynced.
    Directory fsync before the rename makes earlier receipt publication durable;
    a crash that loses the final rename leaves ACTIVE and thus fails closed.
    Correctness of local filesystem atomicity/error behavior is a site check.
    """
    batch = Path(batch)
    current_mount = _require_local_filesystem(batch)
    try:
        active_object = json.loads(expected_active)
    except (ValueError, TypeError) as exc:
        raise RuntimeError('STOP: B1 active sentinel is malformed') from exc
    if not isinstance(active_object, dict) or active_object.get('mount_identity') != list(current_mount):
        raise RuntimeError('STOP: B1 mount changed before active retirement')
    if read_owned_regular(batch / ACTIVE) != expected_active:
        raise RuntimeError('STOP: B1 active sentinel changed before retirement')
    if os.path.lexists(batch / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch has a STOP record before retirement')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    batch_fd = os.open(batch, flags)
    archive_fd = None
    try:
        archive_fd = os.open('_to_delete', flags, dir_fd=batch_fd)
        parent = os.fstat(batch_fd)
        archive = os.fstat(archive_fd)
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid() or parent.st_mode & 0o022
                or not stat.S_ISDIR(archive.st_mode) or archive.st_uid != os.getuid()
                or archive.st_mode & 0o022 or parent.st_dev != archive.st_dev):
            raise RuntimeError('STOP: B1 active retirement directory is unsafe')
        os.fsync(archive_fd)
        os.fsync(batch_fd)
        # This is the final fallible publication step. The supervisor blocks
        # catchable signals and exits after return. Existing target => STOP.
        _renameat2(batch_fd, ACTIVE, archive_fd, 'B1_ACTIVE.completed.json', _NOREPLACE)
    finally:
        # Closing these already-used directory FDs is not a post-commit STOP
        # gate; close failures are ignored and process exit will close them.
        for fd in (archive_fd, batch_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


def publish_waited_success(batch, head, pid, wait_result):
    """A cooperative supervisor calls this only with its actual child's wait result."""
    if type(wait_result) is not int or wait_result != 0:
        raise RuntimeError('STOP: B1 runner did not exit successfully')
    _require_publication_signal_mask()
    _require_local_filesystem(batch)
    active, state = active_and_state(batch, head, pid)
    finalized = _verified_finalization(batch, head)
    receipt = {'version':'b1_waited_exit/v1','runner_pid':pid,'exit_code':0,
               'authorization_checkout_head':head,
               'active_sha256':hashlib.sha256(active).hexdigest(),
               'batch_state_sha256':hashlib.sha256(state).hexdigest(),
               'finalization_sha256':hashlib.sha256(finalized).hexdigest()}
    write_exclusive_json(Path(batch) / EXIT_RECEIPT, receipt)
    _retire_active_last(batch, active)
    return receipt


def publish_after_wait(child, batch, head):
    """Wait for the actual runner; no success receipt on failure or signal."""
    result = child.wait()
    return publish_waited_success(batch, head, child.pid, result)


def _reject_commit_uncertainty(batch):
    # Presence alone blocks: partial writes and symlinks are not approval.
    # Unlike lexists(), lstat preserves permission/I/O errors as refusals.
    try:
        os.lstat(Path(batch) / UNCERTAIN)
    except FileNotFoundError:
        return
    raise RuntimeError('STOP: B1 commit outcome is uncertain; author review required')


def verify_waited_success(batch, head):
    """Fail closed without the receipt; trusts the cooperative receipt writer."""
    _require_local_filesystem(batch)
    _reject_commit_uncertainty(batch)
    if os.path.lexists(Path(batch) / ACTIVE):
        raise RuntimeError('STOP: B1 active sentinel has not been retired')
    raw = read_owned_regular(Path(batch) / EXIT_RECEIPT)
    receipt = json.loads(raw)
    if (not isinstance(receipt,dict) or set(receipt) != {
            'version','runner_pid','exit_code','authorization_checkout_head',
            'active_sha256','batch_state_sha256','finalization_sha256'} or receipt.get('version') != 'b1_waited_exit/v1'
            or type(receipt.get('exit_code')) is not int or receipt['exit_code'] != 0
            or receipt.get('authorization_checkout_head') != head):
        raise RuntimeError('STOP: invalid B1 waited-exit receipt')
    active, state = active_and_state(batch, head, receipt.get('runner_pid'), retired=True)
    finalized = _verified_finalization(batch, head)
    if (receipt.get('active_sha256') != hashlib.sha256(active).hexdigest()
            or receipt.get('batch_state_sha256') != hashlib.sha256(state).hexdigest()
            or receipt.get('finalization_sha256') != hashlib.sha256(finalized).hexdigest()):
        raise RuntimeError('STOP: B1 waited-exit receipt bytes mismatch')
    if os.path.lexists(Path(batch) / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch has a STOP record')
    if os.path.lexists(Path(batch) / ACTIVE):
        raise RuntimeError('STOP: B1 active sentinel reappeared')
    _reject_commit_uncertainty(batch)
    return receipt
