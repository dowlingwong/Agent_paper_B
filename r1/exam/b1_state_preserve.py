"""Preserve old production B1 batch states using Linux atomic rename exchange.

This protects state bytes during normal publication. It does not serialize an
asynchronous STOP, establish ownership of the batch, or protect other files.
"""
from __future__ import annotations

import ctypes
import errno
import json
import os
import re
import stat
import uuid
from pathlib import Path

_NOREPLACE = 1
_EXCHANGE = 2


def write_exclusive_json(path, value):
    """Create one diagnostic without replacing an existing file."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')


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


def _identity(info):
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
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


def publish_audit_cache(path, cache, expected_identity):
    """Publish B1's canonical audit cache, retaining each earlier version."""
    return _publish_named(path, cache, expected_identity, 'audit_cache')


def publish_server_record(path, record, expected_identity):
    """Publish a B1 server record, retaining each earlier version."""
    return _publish_named(path, record, expected_identity, 'server_record')


def _publish_named(path, state, expected_identity, kind):
    """Atomically publish a narrowly named file under the cooperative B1 model.

    The caller owns and serializes the directory and passes the exact prior
    identity (or None only when no file existed). This alone does not establish
    async STOP synchronization or filesystem/site behavior.
    """
    path = Path(path)
    allowed = ((kind == 'batch_state' and path.name == 'batch_state.json') or
               (kind == 'audit_cache' and path.name == 'audit_cache.json') or
               (kind == 'server_record' and re.fullmatch(r'llama_server_[0-9]+(?:_r[0-9]+)?\.json', path.name)))
    if not allowed or not path.is_absolute():
        raise RuntimeError('STOP: invalid B1 snapshot location')
    payload = (json.dumps(state, indent=2, allow_nan=False) + '\n').encode()
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
        name = kind + '.' + uuid.uuid4().hex + '.json'
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
        _renameat2(archive_fd, name, parent_fd, path.name,
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
