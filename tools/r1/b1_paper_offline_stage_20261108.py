#!/usr/bin/env python3
"""Package a clean committed Paper checkout locally; receive once, exclusively."""
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-C', str(root), *args], text=True).strip()


def check(root, head):
    if not re.fullmatch(r'[0-9a-f]{40}', head): raise ValueError('expected full commit SHA')
    if git(root, 'rev-parse', '--verify', 'HEAD') != head: raise RuntimeError('wrong HEAD')
    if git(root, 'status', '--porcelain', '--untracked-files=all'): raise RuntimeError('dirty checkout')
    if git(root, 'remote'): raise RuntimeError('unexpected clone remote')
    print('HEAD', head, 'CLEAN and NO REMOTE: PASS', flush=True)


def pack(source, dest, head):
    if git(source, 'rev-parse', '--verify', 'HEAD') != head: raise RuntimeError('source HEAD mismatch')
    if git(source, 'status', '--porcelain', '--untracked-files=all'): raise RuntimeError('source dirty')
    if not re.fullmatch(r'[0-9a-f]{40}', head): raise ValueError('expected full commit SHA')
    dest.mkdir(mode=0o700)
    root = dest / 'paper'
    subprocess.run(['git', 'clone', '--no-local', '--no-hardlinks', '--no-checkout', str(source), str(root)], check=True)
    subprocess.run(['git', '-C', str(root), 'checkout', '--detach', head], check=True)
    subprocess.run(['git', '-C', str(root), 'remote', 'remove', 'origin'], check=True)
    check(root, head)
    archive = dest / 'paper.tar'
    with tarfile.open(archive, 'x') as tar:
        for parent, dirs, files in os.walk(root, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
            dirs.sort(); files.sort()
            for name in dirs + files:
                p = Path(parent) / name
                if not (p.is_file() or p.is_dir() or p.is_symlink()): raise RuntimeError('special entry: '+str(p))
                tar.add(p, arcname=str(p.relative_to(dest)), recursive=False)
    print('PAYLOAD', archive, 'SHA256', sha256(archive), flush=True)


def within_root(link_name, target):
    target_path = PurePosixPath(target)
    if target_path.is_absolute() or not target: return False
    parts = list(PurePosixPath(link_name).parent.parts)
    for part in target_path.parts:
        if part == '..':
            if len(parts) <= 1: return False
            parts.pop()
        elif part not in ('', '.'): parts.append(part)
    return bool(parts and parts[0] == 'paper')


def receive(dest, head, expected):
    if not re.fullmatch(r'[0-9a-f]{64}', expected): raise ValueError('expected full payload SHA256')
    if not re.fullmatch(r'[0-9a-f]{40}', head): raise ValueError('expected full commit SHA')
    dest.mkdir(mode=0o700)
    archive = dest / 'paper.tar'
    with archive.open('xb') as f: shutil.copyfileobj(sys.stdin.buffer, f)
    if sha256(archive) != expected: raise RuntimeError('payload hash mismatch')
    with tarfile.open(archive, 'r:') as tar:
        entries = tar.getmembers(); seen = set()
        for member in entries:
            p = PurePosixPath(member.name)
            normalized = p.as_posix()
            if (p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != 'paper'
                or normalized != member.name or normalized in seen
                or not (member.isfile() or member.isdir() or member.issym())):
                raise RuntimeError('unsafe archive member: '+member.name)
            if member.issym() and not within_root(member.name, member.linkname):
                raise RuntimeError('unsafe symlink: '+member.name)
            seen.add(normalized)
        link_paths = {m.name for m in entries if m.issym()}
        for member in entries:
            if any(parent.as_posix() in link_paths for parent in PurePosixPath(member.name).parents):
                raise RuntimeError('archive member under symlink: '+member.name)
        (dest / 'paper').mkdir(mode=0o700)
        # Links are created last, so files are never written through archive symlinks.
        for member in entries:
            if member.issym(): continue
            p = dest.joinpath(*PurePosixPath(member.name).parts)
            if member.isdir(): p.mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with tar.extractfile(member) as src, p.open('xb') as dst: shutil.copyfileobj(src, dst)
                os.chmod(p, member.mode & 0o777)
        for member in entries:
            if member.issym():
                p = dest.joinpath(*PurePosixPath(member.name).parts)
                p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                os.symlink(member.linkname, p)
    check(dest/'paper', head)
    print('STAGED', dest/'paper', flush=True)


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == 'pack': pack(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
    elif len(sys.argv) == 5 and sys.argv[1] == 'receive': receive(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
    else: raise SystemExit('usage: pack SOURCE NEW_DEST HEAD | receive NEW_DEST HEAD PAYLOAD_SHA256')
