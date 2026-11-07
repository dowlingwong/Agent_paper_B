"""B1 marker publication/retirement primitives; caller must check handover gates."""
import argparse
import ctypes
import hashlib
import json
import os
import stat
import sys
import uuid
from pathlib import Path

NAME = 'trackx_evidence.active'


def directory(path):
    path = Path(path).absolute()
    if str(path) != os.path.realpath(path):
        raise RuntimeError('directory path contains a symlink')
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    if os.fstat(fd).st_uid != os.getuid():
        os.close(fd)
        raise RuntimeError('directory owner mismatch')
    return fd


def create(lock_dir, status_path, run_id, head):
    if not run_id or not all(c.isalnum() or c in '-_' for c in run_id):
        raise ValueError('invalid run id')
    if len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
        raise ValueError('invalid checkout HEAD')
    lockfd = directory(lock_dir)
    statusfd = None
    markerfd = None
    try:
        statusfd = os.open(status_path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        info = os.fstat(statusfd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise RuntimeError('STATUS is not an owned regular file')
        data = (json.dumps({'run_id': run_id, 'head': head}, sort_keys=True) + '\n').encode()
        markerfd = os.open(NAME, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=lockfd)
        info = os.fstat(markerfd)
        with os.fdopen(markerfd, 'wb', closefd=False) as stream:
            stream.write(data)
        status = f'\n## Track X B1 running — {run_id}\n\nReviewed checkout HEAD: `{head}`.\n'.encode()
        with os.fdopen(statusfd, 'ab', closefd=False) as stream:
            stream.write(status)
        return {'run_id': run_id, 'head': head, 'dev': info.st_dev, 'ino': info.st_ino,
                'sha256': hashlib.sha256(data).hexdigest()}
    finally:
        if markerfd is not None: os.close(markerfd)
        if statusfd is not None: os.close(statusfd)
        os.close(lockfd)


def retire(lock_dir, receipt):
    if not sys.platform.startswith('linux'):
        raise RuntimeError('retirement requires Linux renameat2')
    lockfd = directory(lock_dir)
    archivefd = markerfd = None
    try:
        markerfd = os.open(NAME, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=lockfd)
        info = os.fstat(markerfd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
            raise RuntimeError('marker is not an owned regular file')
        data = b''
        while True:
            part = os.read(markerfd, 4096)
            if not part: break
            data += part
            if len(data) > 4096: raise RuntimeError('marker too large')
        if (info.st_dev, info.st_ino, hashlib.sha256(data).hexdigest()) != (receipt['dev'], receipt['ino'], receipt['sha256']):
            raise RuntimeError('marker does not match receipt')
        current = os.stat(NAME, dir_fd=lockfd, follow_symlinks=False)
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise RuntimeError('marker changed')
        try: os.mkdir('_to_delete', 0o700, dir_fd=lockfd)
        except FileExistsError: pass
        archivefd = os.open('_to_delete', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=lockfd)
        archive = os.fstat(archivefd)
        if archive.st_uid != os.getuid() or archive.st_dev != info.st_dev:
            raise RuntimeError('unsafe marker archive')
        name = (NAME + '.' + uuid.uuid4().hex).encode()
        rename = ctypes.CDLL(None, use_errno=True).renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(lockfd, NAME.encode(), archivefd, name, 1):
            raise OSError(ctypes.get_errno(), 'marker retirement failed')
        return {'retired': os.fsdecode(name), **receipt}
    finally:
        for fd in (markerfd, archivefd, lockfd):
            if fd is not None: os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['create', 'retire'])
    parser.add_argument('--lock-dir', required=True)
    parser.add_argument('--status')
    parser.add_argument('--run-id')
    parser.add_argument('--head')
    parser.add_argument('--receipt')
    args = parser.parse_args()
    if args.operation == 'create':
        if not all((args.status, args.run_id, args.head)): parser.error('create needs --status --run-id --head')
        result = create(args.lock_dir, args.status, args.run_id, args.head)
    else:
        if not args.receipt: parser.error('retire needs --receipt')
        result = retire(args.lock_dir, json.loads(Path(args.receipt).read_text()))
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
