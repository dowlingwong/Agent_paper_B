"""Candidate verification for a dirfd-pinned read-only bind mount.

Recovered from historical local candidate edits. This checkout does not connect
the module to a launcher. Linux mount/rename/teardown behavior and sklearn's
procfd semantics remain unverified. BLOCK remains in force.
"""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path


def fail(message):
    raise ValueError('STOP: ' + message)


def fd_mount_id(fdinfo: str) -> int:
    matches = [line.split(':', 1)[1].strip() for line in fdinfo.splitlines() if line.startswith('mnt_id:')]
    if len(matches) != 1 or not matches[0].isdigit():
        fail('fdinfo missing unique numeric mount ID')
    return int(matches[0])


def verify_binding(original_stat, mounted_stat, original_fdinfo: str, mounted_fdinfo: str,
                   mountinfo: str, expected_path: Path, *, require_readonly: bool = True) -> dict:
    """Bind dev/inode and mounted FD's mount ID to an exact mount entry."""
    if not expected_path.is_absolute() or '..' in expected_path.parts:
        fail('invalid mountpoint')
    if not stat.S_ISDIR(original_stat.st_mode) or not stat.S_ISDIR(mounted_stat.st_mode):
        fail('source or mounted descriptor is not a directory')
    if (original_stat.st_dev, original_stat.st_ino) != (mounted_stat.st_dev, mounted_stat.st_ino):
        fail('source path changed between pinning and mount')
    before, after = fd_mount_id(original_fdinfo), fd_mount_id(mounted_fdinfo)
    if before == after:
        fail('bind mount did not create a distinct mount object')
    matches = []
    nested = []
    same_path = []
    for line in mountinfo.splitlines():
        left, sep, _ = line.partition(' - ')
        fields = left.split()
        if not sep or len(fields) < 6 or not fields[0].isdigit():
            fail('malformed mountinfo')
        decoded = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), fields[4])
        path = Path(decoded)
        if path == expected_path:
            same_path.append((int(fields[0]), set(fields[5].split(','))))
        if path != expected_path and path.is_relative_to(expected_path):
            nested.append(path)
        if int(fields[0]) == after:
            matches.append((path, set(fields[5].split(',')), fields[6:]))
    if nested:
        fail('nested mount not covered by source bind')
    if len(same_path) != 1 or same_path[0][0] != after:
        fail('ambiguous or stacked mountpoint')
    if len(matches) != 1 or matches[0][0] != expected_path or (require_readonly and 'ro' not in matches[0][1]):
        fail('fd mount ID does not identify the exact required mountpoint')
    if any(value.startswith('shared:') for value in matches[0][2]):
        fail('mounted source is not private')
    return {'dev': mounted_stat.st_dev, 'inode': mounted_stat.st_ino,
            'original_mount_id': before, 'readonly_mount_id': after, 'path': str(expected_path)}


def read_relative_nofollow(directory_fd: int, relative: str) -> bytes:
    """Read only relative to the *retained* read-only bind-mount FD."""
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(p in ('', '.', '..') for p in rel.parts):
        fail('unsafe relative source path')
    current = os.dup(directory_fd)
    try:
        for i, part in enumerate(rel.parts):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
            if i != len(rel.parts) - 1:
                flags |= os.O_DIRECTORY
            nxt = os.open(part, flags, dir_fd=current)
            os.close(current)
            current = nxt
        if not stat.S_ISREG(os.fstat(current).st_mode):
            fail('source is not regular')
        chunks = []
        while True:
            data = os.read(current, 1024 * 1024)
            if not data:
                return b''.join(chunks)
            chunks.append(data)
    except OSError as exc:
        raise ValueError('STOP: relative source missing or unsafe') from exc
    finally:
        os.close(current)


def open_dir_absolute_nofollow(path: Path) -> int:
    """Open an absolute directory by component without following symlinks."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        fail('unsafe absolute source directory')
    current = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for part in path.parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
            os.close(current)
            current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def _raw_mount(source: str | None, target: str, flags: int) -> None:
    """Direct kernel mount(2), without userspace path canonicalization."""
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    libc.mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p]
    libc.mount.restype = ctypes.c_int
    src = os.fsencode(source) if source is not None else None
    if libc.mount(src, os.fsencode(target), None, flags, None) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def bind_readonly_fd_pinned(path: Path, namespace_attestation: dict) -> tuple[int, dict]:
    """Bind+remount a pinned directory; retain and return verified ro mount FD.

    ONLY call from a previously verified private mount namespace. This function
    has not been tested against the target Linux kernel and is not accepted.
    """
    path = Path(path)
    if os.getuid() != 0 or namespace_attestation.get('child_mount_namespace') != os.readlink('/proc/self/ns/mnt'):
        fail('verified child mount namespace missing')
    mountinfo = Path('/proc/self/mountinfo').read_text()
    for line in mountinfo.splitlines():
        left, sep, _ = line.partition(' - ')
        fields = left.split()
        if not sep or len(fields) < 6:
            fail('malformed mountinfo')
        if any(x.startswith('shared:') for x in fields[6:]):
            fail('mount propagation is not private')
        decoded = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), fields[4])
        mounted = Path(decoded)
        if mounted != path and mounted.is_relative_to(path):
            fail('nested source mount present before bind')
    source = open_dir_absolute_nofollow(path)
    temporary = -1
    verified = -1
    try:
        original_stat = os.fstat(source)
        original_info = Path(f'/proc/self/fdinfo/{source}').read_text()
        _raw_mount(f'/proc/self/fd/{source}', f'/proc/self/fd/{source}', 4096)  # MS_BIND
        temporary = open_dir_absolute_nofollow(path)
        temporary_stat = os.fstat(temporary)
        if (temporary_stat.st_dev, temporary_stat.st_ino) != (original_stat.st_dev, original_stat.st_ino):
            fail('source changed before bind reopened')
        verify_binding(original_stat, temporary_stat, original_info,
                       Path(f'/proc/self/fdinfo/{temporary}').read_text(),
                       Path('/proc/self/mountinfo').read_text(), path, require_readonly=False)
        _raw_mount(None, f'/proc/self/fd/{temporary}', 4096 | 32 | 1)  # MS_BIND|MS_REMOUNT|MS_RDONLY
        verified = open_dir_absolute_nofollow(path)
        proof = verify_binding(original_stat, os.fstat(verified), original_info,
                               Path(f'/proc/self/fdinfo/{verified}').read_text(),
                               Path('/proc/self/mountinfo').read_text(), path)
        result, verified = verified, -1
        return result, proof
    finally:
        os.close(source)
        if temporary >= 0:
            os.close(temporary)
        if verified >= 0:
            os.close(verified)


def manifest_directory_nofollow(directory_fd: int) -> dict[str, str]:
    """Enumerate all regular files from a retained open directory FD."""
    import hashlib
    result = {}
    def walk(fd, prefix):
        for name in sorted(os.listdir(fd)):
            if name in ('.', '..') or '/' in name:
                fail('invalid directory entry')
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            path = prefix / name
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                try:
                    walk(child, path)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                result[str(path)] = hashlib.sha256(read_relative_nofollow(fd, name)).hexdigest()
            else:
                fail('source tree contains symlink or special file')
    try:
        walk(directory_fd, Path())
    except OSError as exc:
        raise ValueError('STOP: source tree enumeration failed') from exc
    if not result:
        fail('source tree is empty')
    return result


def manifest_relative_nofollow(directory_fd: int, relative: str) -> dict[str, str]:
    """Enumerate and hash all regular files below an already verified mount FD."""
    rel = Path(relative)
    if rel.is_absolute() or not rel.parts or any(p in ('', '.', '..') for p in rel.parts):
        fail('unsafe relative directory')
    current = os.dup(directory_fd)
    try:
        for part in rel.parts:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=current)
            os.close(current)
            current = nxt
        return manifest_directory_nofollow(current)
    except OSError as exc:
        raise ValueError('STOP: source tree enumeration failed') from exc
    finally:
        os.close(current)


def verify_retained_mount(directory_fd: int, proof: dict) -> None:
    """Recheck the same retained FD and live mount table before/after reads."""
    from types import SimpleNamespace
    expected = SimpleNamespace(st_mode=stat.S_IFDIR, st_dev=proof['dev'], st_ino=proof['inode'])
    observed = verify_binding(expected, os.fstat(directory_fd),
                              'mnt_id:\t' + str(proof['original_mount_id']),
                              Path(f'/proc/self/fdinfo/{directory_fd}').read_text(),
                              Path('/proc/self/mountinfo').read_text(), Path(proof['path']))
    if observed != proof:
        fail('retained readonly mount identity changed')
