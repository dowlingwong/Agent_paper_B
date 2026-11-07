"""Preserve old production B1 batch states using Linux atomic rename exchange.

This protects state bytes during normal publication. It does not serialize an
asynchronous STOP, establish ownership of the batch, or protect other files.
"""
from __future__ import annotations

import ctypes
import errno
import json
import locale
import os
import re
import stat
import sys
import uuid
from pathlib import Path

_NOREPLACE = 1
_EXCHANGE = 2
ACTIVE = 'B1_ACTIVE.json'
EXIT_RECEIPT = 'B1_EXIT_RECEIPT.json'


def write_exclusive_json(path, value):
    """Write a new receipt/sentinel without ever replacing an existing file.

    Any partial file remains in place. A failure before this routine returns is
    not a durable-success signal; callers must not start work or issue a receipt.
    """
    path = Path(path)
    payload = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        pending = memoryview(payload)
        while pending:
            count = os.write(fd, pending)
            if count <= 0:
                raise OSError(errno.EIO, 'short receipt write')
            pending = pending[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _renameat2(old_fd, old_name, new_fd, new_name, flags):
    """Call Linux renameat2; an unsupported filesystem must fail closed."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, 'renameat2 unavailable') from exc
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(old_fd, os.fsencode(old_name), new_fd, os.fsencode(new_name), flags):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def _renameat_dryrun(old_fd, old_name, new_fd, new_name, flags):
    """Fail closed unless the OS supplies atomic no-replace/exchange.

    Darwin's renameatx_np uses a different no-replace flag; Linux uses the
    production renameat2. A failed/unsupported operation retains both names.
    This is for synthetic DRYRUN state only, not a production capability claim.
    """
    if sys.platform.startswith('linux'):
        return _renameat2(old_fd, old_name, new_fd, new_name, flags)
    if sys.platform != 'darwin' or flags not in (_NOREPLACE, _EXCHANGE):
        raise OSError(errno.ENOSYS, 'atomic DRYRUN rename unavailable')
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameatx_np
    except AttributeError as exc:
        raise OSError(errno.ENOSYS, 'renameatx_np unavailable') from exc
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                       ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    # Darwin sys/stdio.h: RENAME_EXCL=0x4, RENAME_SWAP=0x2.
    native_flag = 0x4 if flags == _NOREPLACE else 0x2
    if rename(old_fd, os.fsencode(old_name), new_fd, os.fsencode(new_name), native_flag):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code))


def _identity(info):
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o022):
        raise RuntimeError('STOP: B1 batch state is not an owned regular file')
    return info.st_dev, info.st_ino


def existing_identity(path):
    """Return a non-symlink state identity or None; do not change the file."""
    try:
        return _identity(os.stat(path, follow_symlinks=False))
    except FileNotFoundError:
        return None


def publish_state(path, state, expected_identity):
    """Publish one B1 batch state and retain its previous inode."""
    return _publish_named(path, state, expected_identity, 'batch_state')


def publish_dryrun_state(path, state, expected_identity):
    """Preserve each synthetic batch snapshot without replacing its bytes."""
    return _publish_named(path, state, expected_identity, 'batch_state',
                          rename=_renameat_dryrun)


def publish_dryrun_stage_a_result(path, result):
    """Publish a synthetic Stage A result, retaining every prior version.

    The caller owns a stable test directory and has serialized its writer.
    An existing result is accepted only under that cooperative assumption.
    No old bytes are overwritten; an unsupported atomic rename fails closed.
    """
    path = Path(path)
    if not path.is_absolute() or path.name != 'stage_a.json':
        raise RuntimeError('STOP: invalid DRYRUN Stage A result location')
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = existing_identity(path)
    return _publish_named(path, result, expected, 'stage_a_result',
                          rename=_renameat_dryrun)


def publish_dryrun_stage_a_table(path, table):
    """Publish a synthetic Stage A table while retaining each earlier version.

    The caller must serialize writes in a stable owned test directory. The
    canonical table name remains unchanged for readers; unsupported atomic
    operations fail closed and no previously published bytes are discarded.
    """
    path = Path(path)
    if not path.is_absolute() or path.name != 'stage_a_table.json':
        raise RuntimeError('STOP: invalid DRYRUN Stage A table location')
    path.parent.mkdir(parents=True, exist_ok=True)
    expected = existing_identity(path)
    return _publish_named(path, table, expected, 'stage_a_table',
                          rename=_renameat_dryrun)


def publish_audit_cache(path, cache, expected_identity):
    """Publish B1's canonical audit cache, retaining each earlier version."""
    return _publish_named(path, cache, expected_identity, 'audit_cache')


def publish_server_record(path, record, expected_identity):
    """Publish a B1 server record, retaining each earlier version."""
    return _publish_named(path, record, expected_identity, 'server_record')


def publish_dryrun_server_record(path, record, expected_identity):
    """Retain synthetic server record snapshots using the portable DRYRUN rename."""
    return _publish_named(path, record, expected_identity, 'server_record',
                          rename=_renameat_dryrun)


def _dryrun_fixture_edit_path(root, relative):
    """Resolve a registered synthetic editable without following an alias."""
    root = Path(root)
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise RuntimeError('STOP: invalid DRYRUN fixture editable name')
    rel = Path(relative)
    if (rel.is_absolute() or any(p in ('', '.', '..', '_to_delete') for p in rel.parts)
            or rel.as_posix() != relative or not root.is_absolute()
            or root.resolve(strict=True) != root):
        raise RuntimeError('STOP: unsafe DRYRUN fixture editable path')
    path = root / rel
    if path.parent.resolve(strict=True) != path.parent or not path.parent.is_relative_to(root):
        raise RuntimeError('STOP: DRYRUN fixture editable parent aliases outside node')
    return path


def read_dryrun_fixture_text(root, relative):
    """Read the same text as Path.read_text while binding the current inode."""
    path = _dryrun_fixture_edit_path(root, relative)
    identity = existing_identity(path)
    if identity is None:
        raise RuntimeError('STOP: DRYRUN fixture editable is missing')
    text = path.read_text()
    if existing_identity(path) != identity:
        raise RuntimeError('STOP: DRYRUN fixture editable changed during read')
    return text, identity


def publish_dryrun_fixture_text(root, relative, text, expected_identity):
    """Replace one synthetic editable only by retaining its old inode."""
    if not isinstance(text, str) or expected_identity is None:
        raise RuntimeError('STOP: invalid DRYRUN fixture editable content or identity')
    path = _dryrun_fixture_edit_path(root, relative)
    return _publish_named(path, text, expected_identity, 'fixture_text',
                          rename=_renameat_dryrun)


def _publish_named(path, state, expected_identity, kind, *, rename=None):
    """Atomically publish a narrowly named file under the cooperative B1 model.

    The caller owns and serializes the directory and passes the exact prior
    identity (or None only when no file existed). This alone does not establish
    async STOP synchronization or filesystem/site behavior.
    """
    path = Path(path)
    allowed = ((kind == 'batch_state' and path.name == 'batch_state.json') or
               (kind == 'audit_cache' and path.name == 'audit_cache.json') or
               (kind == 'stage_a_result' and path.name == 'stage_a.json') or
               (kind == 'stage_a_table' and path.name == 'stage_a_table.json') or
               (kind == 'fixture_text' and path.name not in ('', '.', '..', '_to_delete')) or
               (kind == 'server_record' and re.fullmatch(r'llama_server_[0-9]+(?:_r[0-9]+)?\.json', path.name)))
    if not allowed or not path.is_absolute():
        raise RuntimeError('STOP: invalid B1 snapshot location')
    # Path.write_text() uses the interpreter's locale/default text encoding;
    # keep its DRYRUN fixture bytes rather than JSON-encoding Python source.
    if kind == 'fixture_text':
        if not isinstance(state, str):
            raise RuntimeError('STOP: DRYRUN fixture editable must be text')
        payload = state.encode(locale.getpreferredencoding(False))
    else:
        # The legacy server writer uses json.dumps' default allow_nan=True.
        payload = (json.dumps(state, indent=2, allow_nan=(kind == 'server_record')) + '\n').encode()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    parent_fd = os.open(path.parent, flags)
    archive_fd = None
    candidate_fd = None
    try:
        parent = os.fstat(parent_fd)
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.getuid()
                or parent.st_mode & 0o022):
            raise RuntimeError('STOP: B1 state directory is not owned')
        try:
            current = _identity(os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False))
        except FileNotFoundError:
            current = None
        if current != expected_identity:
            raise RuntimeError('STOP: B1 batch state identity changed')
        if current is not None and current[0] != parent.st_dev:
            raise RuntimeError('STOP: B1 state is on another filesystem')
        try:
            os.mkdir('_to_delete', 0o700, dir_fd=parent_fd)
        except FileExistsError:
            pass
        archive_fd = os.open('_to_delete', flags, dir_fd=parent_fd)
        archive = os.fstat(archive_fd)
        if (not stat.S_ISDIR(archive.st_mode) or archive.st_uid != os.getuid()
                or archive.st_mode & 0o022 or archive.st_dev != parent.st_dev):
            raise RuntimeError('STOP: B1 state retirement directory is unsafe')
        name = kind + '.' + uuid.uuid4().hex + ('.txt' if kind == 'fixture_text' else '.json')
        file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
        candidate_fd = os.open(name, file_flags, 0o600, dir_fd=archive_fd)
        pending = memoryview(payload)
        while pending:
            count = os.write(candidate_fd, pending)
            if count <= 0:
                raise OSError(errno.EIO, 'short state write')
            pending = pending[count:]
        os.fsync(candidate_fd)
        new_identity = _identity(os.fstat(candidate_fd))
        if new_identity[0] != parent.st_dev:
            raise RuntimeError('STOP: B1 state candidate crossed a filesystem')
        # Verify the source name still references the fd before exchanging it.
        if _identity(os.stat(name, dir_fd=archive_fd, follow_symlinks=False)) != new_identity:
            raise RuntimeError('STOP: B1 state candidate identity changed')
        try:
            before = _identity(os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False))
        except FileNotFoundError:
            before = None
        if before != current:
            raise RuntimeError('STOP: B1 batch state changed before publication')
        (rename or _renameat2)(archive_fd, name, parent_fd, path.name,
                              _NOREPLACE if current is None else _EXCHANGE)
        if _identity(os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)) != new_identity:
            raise RuntimeError('STOP: B1 published state identity changed')
        if current is not None and _identity(os.stat(name, dir_fd=archive_fd, follow_symlinks=False)) != current:
            raise RuntimeError('STOP: B1 retired state identity changed')
        os.fsync(archive_fd)
        os.fsync(parent_fd)
        return new_identity
    finally:
        if candidate_fd is not None:
            os.close(candidate_fd)
        if archive_fd is not None:
            os.close(archive_fd)
        os.close(parent_fd)
