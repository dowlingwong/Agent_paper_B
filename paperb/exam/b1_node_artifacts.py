"""Keep previous B1 node output when a pinned node reuses ``artifacts/``.

The active node directory is owned by this B1 campaign.  The node's fixed
output path remains unchanged; before a subsequent invocation its previous
directory is moved intact into a fresh, no-replace archive name.
"""
from __future__ import annotations

import ctypes
import os
import stat
import sys
import uuid
from pathlib import Path


class B1ArtifactPreservationStop(SystemExit):
    """Do not let the pinned harness turn an output-preservation error into an invalid trial."""


def preserve_node_artifacts(node_root: Path) -> None:
    """Retire the previous node artifacts before running another B1 worker.

    This is cooperative local process management, not protection against a
    concurrent hostile writer.  A failure retains the scene and raises STOP.
    """
    fds = []
    body_failed = False
    try:
        root = Path(node_root)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        root_fd = os.open(root, flags)
        fds.append(root_fd)
        root_stat = os.fstat(root_fd)
        if root_stat.st_uid != os.getuid():
            raise RuntimeError('node root is not owned by the B1 user')
        try:
            source = os.stat('artifacts', dir_fd=root_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        if not stat.S_ISDIR(source.st_mode) or source.st_uid != os.getuid() or source.st_dev != root_stat.st_dev:
            raise RuntimeError('node artifacts directory is unsafe')
        try:
            os.mkdir('_to_delete', 0o700, dir_fd=root_fd)
        except FileExistsError:
            pass
        archive_fd = os.open('_to_delete', flags, dir_fd=root_fd)
        fds.append(archive_fd)
        archive = os.fstat(archive_fd)
        if archive.st_uid != os.getuid() or archive.st_mode & 0o077 or archive.st_dev != root_stat.st_dev:
            raise RuntimeError('node archive directory is unsafe')
        current = os.stat('artifacts', dir_fd=root_fd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (source.st_dev, source.st_ino):
            raise RuntimeError('node artifacts directory changed before retirement')
        if sys.platform.startswith('linux'):
            symbol, no_replace = 'renameat2', 1
        elif sys.platform == 'darwin':
            symbol, no_replace = 'renameatx_np', 4
        else:
            raise RuntimeError('atomic no-replace rename is unavailable')
        rename = getattr(ctypes.CDLL(None, use_errno=True), symbol)
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        destination = os.fsencode('artifacts.' + uuid.uuid4().hex)
        if rename(root_fd, b'artifacts', archive_fd, destination, no_replace) != 0:
            raise OSError(ctypes.get_errno(), 'no-replace artifact retirement failed')
    except Exception as exc:
        body_failed = True
        raise B1ArtifactPreservationStop('STOP: could not preserve prior B1 node outputs') from exc
    except BaseException:
        body_failed = True
        raise
    finally:
        close_error = None
        for fd in reversed(fds):
            try:
                os.close(fd)
            except OSError as exc:
                if close_error is None:
                    close_error = exc
        if close_error is not None and not body_failed:
            raise B1ArtifactPreservationStop('STOP: could not close B1 output preservation handles') from close_error
