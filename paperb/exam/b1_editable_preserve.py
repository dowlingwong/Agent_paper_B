"""Preserve B1 node editables while running the pinned harness unchanged on disk.

This is a B1-only in-process I/O adapter, not an assertion that the harness
executes without an overlay. It retains old inodes before each write or unlink;
a partial replacement is retained on failure. Paths are cooperative B1-owned
single-file node copies, not a defense against a hostile same-UID writer.
"""
from __future__ import annotations

import ctypes
import os
import stat
import sys
import uuid
from contextlib import contextmanager
from pathlib import Path


class B1EditablePreservationStop(SystemExit):
    """Escape the pinned harness's Exception-to-invalid conversion."""


def _retire_or_create(path: Path, root: Path, data: bytes | None, *, missing_ok=False):
    """Retire an owned file using atomic no-replace; optionally write new bytes."""
    fds=[]
    body_failed=False
    try:
        if path.parent != root or path.name in ('', '.', '..', '_to_delete'):
            raise RuntimeError('editable is not a direct child of the owned node root')
        root_fd=os.open(root,os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        fds.append(root_fd)
        root_stat=os.fstat(root_fd)
        if root_stat.st_uid!=os.getuid(): raise RuntimeError('node root has unexpected owner')
        try:
            old=os.stat(path.name,dir_fd=root_fd,follow_symlinks=False)
        except FileNotFoundError:
            old=None
        if old is None and data is None:
            if missing_ok: return
            raise FileNotFoundError(str(path))
        mode=0o666
        if old is not None:
            if not stat.S_ISREG(old.st_mode) or old.st_uid!=os.getuid() or old.st_nlink!=1 or old.st_dev!=root_stat.st_dev:
                raise RuntimeError('unsafe editable source')
            if data is not None and not os.access(path,os.W_OK):
                raise PermissionError('editable is not writable')
            mode=stat.S_IMODE(old.st_mode)
            try: os.mkdir('_to_delete',0o700,dir_fd=root_fd)
            except FileExistsError: pass
            archive_fd=os.open('_to_delete',os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,dir_fd=root_fd)
            fds.append(archive_fd)
            archive=os.fstat(archive_fd)
            if archive.st_uid!=os.getuid() or archive.st_mode & 0o077 or archive.st_dev!=root_stat.st_dev:
                raise RuntimeError('unsafe editable archive directory')
            current=os.stat(path.name,dir_fd=root_fd,follow_symlinks=False)
            if (current.st_dev,current.st_ino)!=(old.st_dev,old.st_ino):
                raise RuntimeError('editable changed before retirement')
            if sys.platform.startswith('linux'): symbol,flag='renameat2',1
            elif sys.platform=='darwin': symbol,flag='renameatx_np',4
            else: raise RuntimeError('atomic no-replace rename unavailable')
            rename=getattr(ctypes.CDLL(None,use_errno=True),symbol)
            rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
            rename.restype=ctypes.c_int
            dest=os.fsencode(path.name+'.'+uuid.uuid4().hex+'.retired')
            if rename(root_fd,os.fsencode(path.name),archive_fd,dest,flag)!=0:
                raise OSError(ctypes.get_errno(),'no-replace editable retirement failed')
        if data is not None:
            fd=os.open(path.name,os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,mode,dir_fd=root_fd)
            fds.append(fd)
            if old is not None: os.fchmod(fd,mode)
            view=memoryview(data)
            while view:
                count=os.write(fd,view)
                if count<=0: raise OSError('short editable write')
                view=view[count:]
    except Exception as exc:
        body_failed=True
        raise B1EditablePreservationStop('STOP: failed to preserve B1 editable version') from exc
    except BaseException:
        body_failed=True
        raise
    finally:
        close_error=None
        for fd in reversed(fds):
            try: os.close(fd)
            except OSError as exc:
                if close_error is None: close_error=exc
        if close_error is not None and not body_failed:
            raise B1EditablePreservationStop('STOP: failed to close B1 editable preservation handles') from close_error


def _guarded_path_type(root, editable_paths):
    root=Path(root).absolute()
    allowed=frozenset(editable_paths)
    if not allowed or any(Path(x).name!=x or x in ('.','..','_to_delete') for x in allowed):
        raise B1EditablePreservationStop('STOP: unsupported B1 editable paths')
    class GuardedPath(type(Path())):
        def _check(self):
            if self.parent != root or self.name not in allowed:
                raise B1EditablePreservationStop('STOP: editable path outside B1 node root')
        def write_text(self, data, encoding=None, errors=None, newline=None):
            self._check()
            if not isinstance(data,str): raise TypeError('data must be str')
            # The pinned worker specifies UTF-8; encode before moving anything.
            if newline not in (None,''): raise B1EditablePreservationStop('STOP: unsupported newline translation')
            content=data.encode(encoding or 'utf-8',errors or 'strict')
            _retire_or_create(Path(self),root,content)
            return len(data)
        def write_bytes(self, data):
            self._check()
            content=bytes(memoryview(data))
            _retire_or_create(Path(self),root,content)
            return len(content)
        def unlink(self, missing_ok=False):
            self._check()
            _retire_or_create(Path(self),root,None,missing_ok=missing_ok)
    return GuardedPath


@contextmanager
def preserve_pinned_editables(worker, node_spec):
    """Bind the pinned worker and campaign path construction for one B1 call.

    The harness checkout and its edit/restore algorithms remain unchanged, but
    their file operations use this B1 overlay. This assumes serialized use of
    these module globals in the isolated campaign process.
    """
    from autoresearch.control_plane import campaign as harness_campaign
    root=Path(worker._node_root).absolute()
    guarded=_guarded_path_type(root,node_spec.editable_paths)
    original=harness_campaign._editable_path
    def guarded_editable_path(node_root, path_str):
        value=original(node_root,path_str)
        result=guarded(value)
        result._check()
        return result
    previous=getattr(worker,'_b1_editable_path_type',None)
    worker._b1_editable_path_type=guarded
    harness_campaign._editable_path=guarded_editable_path
    try:
        yield
    finally:
        harness_campaign._editable_path=original
        if previous is None:
            del worker._b1_editable_path_type
        else:
            worker._b1_editable_path_type=previous
