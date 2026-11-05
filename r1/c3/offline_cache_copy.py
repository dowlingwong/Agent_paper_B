"""Planning-only cache copy on a cooperative local filesystem.

Not a sandbox, an immutable snapshot, or authority to replay. Concurrent or
privileged writers and filesystem aliases are outside the verified guarantee.
On failure, preserve the partially created destination for inspection.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat


class CopyStop(RuntimeError):
    pass


def _flags(directory=False):
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise CopyStop('STOP: no-follow directory operations unavailable')
    return os.O_RDONLY | os.O_NOFOLLOW | (os.O_DIRECTORY if directory else 0)


def _open_directory(path):
    """Open each absolute path component without traversing a symlink."""
    path = Path(path)
    if '..' in path.parts:
        raise CopyStop('STOP: parent traversal in cache path')
    absolute = path.absolute()
    fd = os.open('/', _flags(True))
    try:
        for part in absolute.parts[1:]:
            new_fd = os.open(part, _flags(True), dir_fd=fd)
            os.close(fd)
            fd = new_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


def _stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_nlink)


def _same_entry(fd, name, s):
    return _stamp(os.stat(name, dir_fd=fd, follow_symlinks=False)) == _stamp(s)


def _write_all(fd, data):
    while data:
        written = os.write(fd, data)
        if written <= 0:
            raise CopyStop('STOP: short destination write')
        data = data[written:]


def _copy_dir(source_fd, target_fd, prefix, records):
    before = os.fstat(source_fd)
    names = sorted(os.listdir(source_fd))
    for name in names:
        info = os.stat(name, dir_fd=source_fd, follow_symlinks=False)
        rel = f'{prefix}/{name}' if prefix else name
        if stat.S_ISDIR(info.st_mode):
            child = os.open(name, _flags(True), dir_fd=source_fd)
            try:
                if not _same_entry(source_fd, name, os.fstat(child)):
                    raise CopyStop('STOP: source directory changed during open')
                os.mkdir(name, mode=0o700, dir_fd=target_fd)
                dest = os.open(name, _flags(True), dir_fd=target_fd)
                try:
                    _copy_dir(child, dest, rel, records)
                finally:
                    os.close(dest)
                if not _same_entry(source_fd, name, os.fstat(child)):
                    raise CopyStop('STOP: source directory changed during copying')
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode):
            if info.st_nlink != 1:
                raise CopyStop('STOP: multiply linked source file')
            inp = os.open(name, _flags(), dir_fd=source_fd)
            try:
                initial = os.fstat(inp)
                if not stat.S_ISREG(initial.st_mode) or initial.st_nlink != 1 or not _same_entry(source_fd, name, initial):
                    raise CopyStop('STOP: source file changed during open')
                out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=target_fd)
                try:
                    digest = hashlib.sha256()
                    while True:
                        chunk = os.read(inp, 1024 * 1024)
                        if not chunk:
                            break
                        digest.update(chunk)
                        _write_all(out, chunk)
                    os.fsync(out)
                finally:
                    os.close(out)
                if _stamp(initial) != _stamp(os.fstat(inp)) or not _same_entry(source_fd, name, initial):
                    raise CopyStop('STOP: source file changed during copying')
                check = os.open(name, _flags(), dir_fd=target_fd)
                try:
                    saved = os.fstat(check)
                    if not stat.S_ISREG(saved.st_mode) or saved.st_nlink != 1 or (saved.st_dev, saved.st_ino) == (initial.st_dev, initial.st_ino):
                        raise CopyStop('STOP: destination is not a fresh regular file')
                    actual = hashlib.sha256()
                    while True:
                        chunk = os.read(check, 1024 * 1024)
                        if not chunk:
                            break
                        actual.update(chunk)
                    if digest.digest() != actual.digest() or saved.st_size != initial.st_size:
                        raise CopyStop('STOP: copied bytes differ from source')
                finally:
                    os.close(check)
                records.append({'path': rel, 'size': initial.st_size, 'sha256': digest.hexdigest()})
            finally:
                os.close(inp)
        else:
            raise CopyStop('STOP: symlink or special file in source cache')
    if _stamp(before) != _stamp(os.fstat(source_fd)) or names != sorted(os.listdir(source_fd)):
        raise CopyStop('STOP: source directory changed during copying')
    os.fsync(target_fd)


def copy_cache(source, destination):
    """Create a new cache directory; leave it untouched on STOP for inspection.

    Refuses symlinks and hard-linked source files, verifies fresh destination
    inode and file bytes, and detects ordinary source changes during copying.
    It cannot rule out concurrent adversarial writes, mount aliases, changes
    after return, or filesystems with unreliable metadata. Do not use as an
    offline-execution or production authorization gate.
    """
    source, destination = Path(source), Path(destination)
    source_abs, target_abs = source.absolute(), destination.absolute()
    if source_abs == target_abs or source_abs in target_abs.parents or target_abs in source_abs.parents:
        raise CopyStop('STOP: source and destination must not overlap')
    if destination.name in ('', '.', '..') or '..' in destination.parts:
        raise CopyStop('STOP: invalid destination path')
    src = parent = dst = None
    try:
        src = _open_directory(source)
        parent = _open_directory(destination.parent)
        os.mkdir(destination.name, mode=0o700, dir_fd=parent)
        dst = os.open(destination.name, _flags(True), dir_fd=parent)
        records = []
        _copy_dir(src, dst, '', records)
        if not records:
            raise CopyStop('STOP: empty source cache')
        return {'files': records, 'state': 'IDENTITY_ONLY', 'offline_executability': 'NOT_ESTABLISHED'}
    except OSError as exc:
        raise CopyStop(f'STOP: cache copy failed: {exc}') from exc
    finally:
        for fd in (dst, parent, src):
            if fd is not None:
                os.close(fd)
