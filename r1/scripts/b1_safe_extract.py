"""Hash-check and extract a trusted Git archive without links or overwrites."""
import argparse
import hashlib
import os
import shutil
import tarfile
from pathlib import Path, PurePosixPath


def extract(archive, destination, expected):
    destination = Path(destination)
    if not destination.is_dir() or destination.is_symlink() or any(destination.iterdir()):
        raise ValueError('destination must be a new empty directory')
    with open(archive, 'rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
        if h.hexdigest() != expected:
            raise ValueError('archive sha256 mismatch')
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode='r:') as tar:
            seen = set()
            members = tar.getmembers()
            for member in members:
                path = PurePosixPath(member.name)
                if (path.is_absolute() or not path.parts or '..' in path.parts or
                    member.name in seen or not (member.isdir() or member.isfile())):
                    raise ValueError('unsafe or duplicate archive entry: ' + member.name)
                seen.add(member.name)
            for member in members:
                target = destination.joinpath(*PurePosixPath(member.name).parts)
                if member.isdir():
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, member.mode & 0o777)
                    with os.fdopen(fd, 'wb') as out, tar.extractfile(member) as source:
                        shutil.copyfileobj(source, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive'); parser.add_argument('destination'); parser.add_argument('sha256')
    args = parser.parse_args()
    extract(args.archive, args.destination, args.sha256)


if __name__ == '__main__': main()
