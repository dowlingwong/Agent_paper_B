#!/usr/bin/env python3
"""One-shot retained Darwin atomic rename capability probe. Never cleanup."""
import ctypes
import errno
import hashlib
import os
import stat
import sys

NAME = 'paper_b_mac_rename_probe_20261107_f4e6b9c2187a4d52'
if sys.platform != 'darwin' or not sys.dont_write_bytecode:
    raise RuntimeError('STOP: requires Darwin and Python -B at interpreter start')
if os.path.realpath('/private/tmp') != '/private/tmp':
    raise RuntimeError('STOP: unexpected /private/tmp identity')
D = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
fds = []
try:
    parent = os.open('/private/tmp', D)
    fds.append(parent)
    named = os.stat('/private/tmp', follow_symlinks=False)
    opened = os.fstat(parent)
    if not stat.S_ISDIR(opened.st_mode) or (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
        raise RuntimeError('STOP: temporary parent identity changed')
    # Existing name is a STOP; never reuse or remove it.
    os.mkdir(NAME, 0o700, dir_fd=parent)
    root = os.open(NAME, D, dir_fd=parent)
    fds.append(root)
    root_info = os.fstat(root)
    root_named = os.stat(NAME, dir_fd=parent, follow_symlinks=False)
    if (root_info.st_uid != os.getuid() or root_info.st_mode & 0o077 or
        root_info.st_dev != opened.st_dev or
        (root_info.st_dev, root_info.st_ino) != (root_named.st_dev, root_named.st_ino)):
        raise RuntimeError('STOP: unsafe probe root')
    print('probe_root:', '/private/tmp/' + NAME, 'dev:', root_info.st_dev, flush=True)
    os.mkdir('_to_delete', 0o700, dir_fd=root)
    archive = os.open('_to_delete', D, dir_fd=root)
    fds.append(archive)
    archive_info = os.fstat(archive)
    archive_named = os.stat('_to_delete', dir_fd=root, follow_symlinks=False)
    if (archive_info.st_uid != os.getuid() or archive_info.st_mode & 0o077 or
        archive_info.st_dev != root_info.st_dev or
        (archive_info.st_dev, archive_info.st_ino) != (archive_named.st_dev, archive_named.st_ino)):
        raise RuntimeError('STOP: unsafe archive directory')

    def create(name, content):
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=root)
        try:
            view = memoryview(content)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError('short write')
                view = view[written:]
            os.fsync(fd)
            info = os.fstat(fd)
            return (info.st_dev, info.st_ino)
        finally:
            os.close(fd)

    def check(directory, name, expected_identity, expected_bytes):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        try:
            info = os.fstat(fd)
            named_info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            data = b''
            while True:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                data += chunk
            identity = (info.st_dev, info.st_ino)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or
                info.st_nlink != 1 or identity != expected_identity or
                identity != (named_info.st_dev, named_info.st_ino) or data != expected_bytes):
                raise RuntimeError('STOP: content or identity mismatch: ' + name)
            print('file:', name, 'identity:', identity, 'sha256:', hashlib.sha256(data).hexdigest(), flush=True)
        finally:
            os.close(fd)

    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameatx_np
    except AttributeError as exc:
        raise RuntimeError('STOP: renameatx_np unavailable') from exc
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int

    def move(srcdir, src, dstdir, dst, flag):
        if rename(srcdir, os.fsencode(src), dstdir, os.fsencode(dst), flag):
            code = ctypes.get_errno()
            raise OSError(code, 'renameatx_np failed', src + ' -> ' + dst)

    a, b = b'Paper B Mac rename probe A\n', b'Paper B Mac rename probe B\n'
    aid, bid = create('a', a), create('b', b)
    check(root, 'a', aid, a)
    check(root, 'b', bid, b)
    try:
        move(root, 'a', root, 'b', 0x4)  # RENAME_EXCL
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    else:
        raise RuntimeError('STOP: EXCL collision unexpectedly succeeded')
    check(root, 'a', aid, a)
    check(root, 'b', bid, b)
    print('exclusive_collision: PASS EEXIST', flush=True)
    move(root, 'a', archive, 'c', 0x4)
    os.fsync(root)
    os.fsync(archive)
    try:
        os.stat('a', dir_fd=root, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise RuntimeError('STOP: old name still exists after move')
    check(archive, 'c', aid, a)
    check(root, 'b', bid, b)
    print('exclusive_cross_directory_move: PASS', flush=True)
    move(root, 'b', archive, 'c', 0x2)  # RENAME_SWAP
    os.fsync(root)
    os.fsync(archive)
    check(root, 'b', aid, a)
    check(archive, 'c', bid, b)
    print('swap_cross_directory: PASS; both files retained', flush=True)
    print('probe_complete: no cleanup requested', flush=True)
finally:
    for fd in reversed(fds):
        os.close(fd)
