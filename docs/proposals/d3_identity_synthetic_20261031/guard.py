"""Synthetic-only building blocks for a future reviewed D3 launcher.

NOT A LAUNCHER. No production acceptance: callers cannot make Stage A runnable.
Directory-FD traversal with no symlink following binds bytes to held FDs, but
only protects against peers if every directory is actually owned by a separate
trusted UID. Synthetic tests use the current UID and prove no such separation.
"""
from __future__ import annotations
import ctypes
import errno
import hashlib
import os
import stat
from dataclasses import dataclass

class GuardStop(RuntimeError):
    pass


def fail_closed_os(fn):
    """Map every otherwise-unhandled OS failure at the boundary to STOP."""
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except OSError as e:
            raise GuardStop('STOP: protected-input OS operation failed') from e
    return wrapped

@dataclass(frozen=True)
class FileIdentity:
    dev: int
    ino: int
    mode: int
    uid: int
    nlink: int
    size: int
    mtime_ns: int
    ctime_ns: int


def ident(st: os.stat_result) -> FileIdentity:
    return FileIdentity(st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_nlink,
                        st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def require_safe(st: os.stat_result, *, uid: int, directory: bool) -> None:
    if st.st_uid != uid:
        raise GuardStop('STOP: unexpected owner')
    if bool(directory) != stat.S_ISDIR(st.st_mode):
        raise GuardStop('STOP: unexpected file type')
    if not directory and not stat.S_ISREG(st.st_mode):
        raise GuardStop('STOP: non-regular input')
    if st.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise GuardStop('STOP: shared-writable input or directory')
    if not directory and st.st_nlink != 1:
        raise GuardStop('STOP: hard-linked input')


@fail_closed_os
def open_root(path: str, *, uid: int) -> int:
    # The caller must separately prove ownership and stability of the whole
    # root ancestry and the mount; this only validates the opened root inode.
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise GuardStop('STOP: required no-follow directory primitives unavailable')
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as e:
        raise GuardStop('STOP: cannot open protected root') from e
    try:
        require_safe(os.fstat(fd), uid=uid, directory=True)
        return fd
    except BaseException:
        os.close(fd)
        raise


@fail_closed_os
def open_input(root_fd: int, relpath: str, *, uid: int, expected_sha256: str) -> tuple[int, FileIdentity]:
    if not isinstance(relpath, str) or not relpath or relpath.startswith('/'):
        raise GuardStop('STOP: invalid relative path')
    parts = relpath.split('/')
    if any(x in ('', '.', '..') or '\x00' in x for x in parts):
        raise GuardStop('STOP: invalid path component')
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(c not in '0123456789abcdef' for c in expected_sha256):
        raise GuardStop('STOP: malformed SHA-256')
    current = os.dup(root_fd)
    try:
        require_safe(os.fstat(current), uid=uid, directory=True)
        for component in parts[:-1]:
            try:
                nxt = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
            except OSError as e:
                raise GuardStop('STOP: protected directory unavailable') from e
            # Detach the old descriptor before close: after a close failure its
            # state is indeterminate and retrying could close an unrelated FD.
            old, current = current, None
            try:
                os.close(old)
            except OSError:
                # nxt is distinct and has not been subject to a failed close.
                # Attempt its close exactly once, never retry either descriptor.
                try:
                    os.close(nxt)
                except OSError:
                    pass
                raise
            current = nxt
            require_safe(os.fstat(current), uid=uid, directory=True)
        try:
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=current)
        except OSError as e:
            raise GuardStop('STOP: protected input unavailable') from e
        try:
            before = ident(os.fstat(fd))
            require_safe(os.fstat(fd), uid=uid, directory=False)
            digest = hashlib.sha256()
            while True:
                b = os.read(fd, 1024 * 1024)
                if not b: break
                digest.update(b)
            after = ident(os.fstat(fd))
            if before != after or digest.hexdigest() != expected_sha256:
                raise GuardStop('STOP: identity or bytes changed')
            os.lseek(fd, 0, os.SEEK_SET)
            # Before ownership of fd can transfer to the caller, close the
            # containing directory. If that fails, caller receives no file FD;
            # close the distinct file FD once and never retry the uncertain dir.
            old, current = current, None
            try:
                os.close(old)
            except OSError:
                file_to_close, fd = fd, None
                try:
                    os.close(file_to_close)
                except OSError:
                    pass
                raise
            return fd, after
        except OSError as e:
            if fd is not None:
                file_to_close, fd = fd, None
                os.close(file_to_close)
            raise GuardStop('STOP: cannot read or validate protected input') from e
        except BaseException:
            if fd is not None:
                file_to_close, fd = fd, None
                os.close(file_to_close)
            raise
    finally:
        if current is not None:
            os.close(current)


@fail_closed_os
def validate_held_fd(fd: int, saved: FileIdentity, expected_sha256: str) -> None:
    # Checking again detects ordinary inode modifications; it is not a defense
    # against a privileged writer or an untrusted owner who can race reads.
    try:
        start = ident(os.fstat(fd))
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        while True:
            b = os.read(fd, 1024 * 1024)
            if not b: break
            digest.update(b)
        end = ident(os.fstat(fd))
        os.lseek(fd, 0, os.SEEK_SET)
    except OSError as e:
        raise GuardStop('STOP: cannot revalidate held input') from e
    if start != saved or end != saved or digest.hexdigest() != expected_sha256:
        raise GuardStop('STOP: held input changed')


def kcmp_file_verdict(pid_a: int, pid_b: int, fd_a: int, fd_b: int) -> str:
    """Direct Linux x86-64 KCMP_FILE only; no caller-supplied syscall number.

    The Linux x86-64 ABI defines kcmp=312. All other ABIs/platforms are
    NOT_CHECKABLE, including compat/x32 processes: check pointer width too.
    Permission failures and unsupported kernels are NOT_CHECKABLE, never PASS.
    0 means same OFD, a positive result means different OFDs.
    """
    try:
        system = os.uname()
    except OSError:
        return 'NOT_CHECKABLE'
    if system.sysname != 'Linux' or system.machine != 'x86_64' or ctypes.sizeof(ctypes.c_void_p) != 8:
        return 'NOT_CHECKABLE'
    syscall_nr = 312
    # ctypes.c_int truncates silently: reject non-integers, bools, negatives,
    # zero PIDs and values outside the ABI range before crossing the FFI.
    vals = (pid_a, pid_b, fd_a, fd_b)
    if any(type(v) is not int or v > 2**31 - 1 for v in vals):
        return 'NOT_CHECKABLE'
    if pid_a <= 0 or pid_b <= 0 or fd_a < 0 or fd_b < 0:
        return 'NOT_CHECKABLE'
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        call = libc.syscall
        call.restype = ctypes.c_long
        ctypes.set_errno(0)
        result = call(ctypes.c_long(syscall_nr), ctypes.c_int(pid_a), ctypes.c_int(pid_b), ctypes.c_int(0),
                      ctypes.c_ulong(fd_a), ctypes.c_ulong(fd_b))
    except (OSError, AttributeError, ValueError, TypeError, ctypes.ArgumentError):
        return 'NOT_CHECKABLE'
    if result == 0: return 'SAME'
    if result > 0: return 'DIFFERENT'
    return 'NOT_CHECKABLE'


def production_entry(*args, **kwargs):
    raise GuardStop('STOP: synthetic candidate is not an authorized production launcher')
