"""Retire an owned synthetic interrupted root without overwriting any name.

The test operator owns the batch and serializes writers. This does not infer
that a recorded STOP may be resumed, establish cross-process quiescence, or
qualify actual filesystem and crash behavior.
"""
from __future__ import annotations

import os
import stat
import uuid
from pathlib import Path

from r1.exam.b1_state_preserve import _NOREPLACE, _renameat_dryrun


def _owned_dir(info, device=None):
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or info.st_mode & 0o022 or (device is not None and info.st_dev != device)):
        raise RuntimeError('STOP: unsafe DRYRUN interrupted-root directory')
    return info.st_dev, info.st_ino, info.st_uid


def retire_dryrun_root(batch, source):
    """Atomically move a synthetic root under ``_to_delete`` with no replacement.

    Both paths must be absolute, with source a lexical descendant of batch. All
    components inside batch are opened as owned non-symlink directories on the
    same device. The atomic OS operation refuses a target collision; unsupported
    platforms/filesystems fail closed. A failure after rename leaves the moved
    directory in its archive and is not a success or permission to retry.
    """
    batch, source = Path(batch), Path(source)
    if not batch.is_absolute() or not source.is_absolute():
        raise RuntimeError('STOP: DRYRUN interrupted-root paths must be absolute')
    try:
        parts = source.relative_to(batch).parts
    except ValueError as exc:
        raise RuntimeError('STOP: DRYRUN interrupted root outside batch') from exc
    if not parts or any(x in ('', '.', '..', '_to_delete') for x in parts):
        raise RuntimeError('STOP: invalid DRYRUN interrupted-root path')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    opened = []
    body_failed = False
    try:
        rootfd = os.open(batch, flags); opened.append(rootfd)
        root_info = os.fstat(rootfd)
        root_identity = _owned_dir(root_info)
        parentfd = rootfd
        for component in parts[:-1]:
            parentfd = os.open(component, flags, dir_fd=parentfd); opened.append(parentfd)
            _owned_dir(os.fstat(parentfd), root_identity[0])
        name = parts[-1]
        source_info = os.stat(name, dir_fd=parentfd, follow_symlinks=False)
        source_identity = _owned_dir(source_info, root_identity[0])
        sourcefd = os.open(name, flags, dir_fd=parentfd); opened.append(sourcefd)
        if _owned_dir(os.fstat(sourcefd), root_identity[0]) != source_identity:
            raise RuntimeError('STOP: DRYRUN interrupted-root identity changed')
        try:
            os.mkdir('_to_delete', 0o700, dir_fd=rootfd)
        except FileExistsError:
            pass
        archivefd = os.open('_to_delete', flags, dir_fd=rootfd); opened.append(archivefd)
        _owned_dir(os.fstat(archivefd), root_identity[0])
        if _owned_dir(os.stat(name, dir_fd=parentfd, follow_symlinks=False), root_identity[0]) != source_identity:
            raise RuntimeError('STOP: DRYRUN interrupted-root changed before retirement')
        target = 'interrupted.' + uuid.uuid4().hex
        _renameat_dryrun(parentfd, name, archivefd, target, _NOREPLACE)
        if _owned_dir(os.stat(target, dir_fd=archivefd, follow_symlinks=False), root_identity[0]) != source_identity:
            raise RuntimeError('STOP: DRYRUN retired-root identity changed')
        os.fsync(parentfd)
        os.fsync(archivefd)
        return batch / '_to_delete' / target
    except BaseException:
        body_failed = True
        raise
    finally:
        close_error = None
        for fd in reversed(opened):
            try:
                os.close(fd)
            except BaseException as exc:
                if close_error is None:
                    close_error = exc
        if not body_failed and close_error is not None:
            raise close_error
