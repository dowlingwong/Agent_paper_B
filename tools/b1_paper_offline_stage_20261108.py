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
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='0', GIT_NO_REPLACE_OBJECTS='1', GIT_TERMINAL_PROMPT='0')
    return subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(root), *args], text=True, env=env).strip()


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
    dotgit = source / '.git'
    if dotgit.is_symlink() or not dotgit.is_dir(): raise RuntimeError('source must have a standalone .git directory')
    if git(source, 'rev-parse', '--is-shallow-repository') != 'false': raise RuntimeError('shallow source')
    if git(source, 'rev-parse', '--show-object-format') != 'sha1': raise RuntimeError('unsupported object format')
    if list((dotgit/'objects/pack').glob('*.promisor')): raise RuntimeError('partial clone unsupported')
    if git(source, 'rev-parse', '--shared-index-path'): raise RuntimeError('split index unsupported')
    if (dotgit/'objects/info/alternates').exists() or (dotgit/'objects/info/alternates').is_symlink(): raise RuntimeError('alternates unsupported')
    if (dotgit/'info/grafts').exists() or (dotgit/'info/grafts').is_symlink(): raise RuntimeError('grafts unsupported')
    root.mkdir(mode=0o700)
    (root/'.git').mkdir(mode=0o700)
    (root/'.git/refs/heads').mkdir(parents=True, mode=0o700)
    (root/'.git/refs/tags').mkdir(mode=0o700)
    def copyfile(src, dst):
        if src.is_symlink() or not src.is_file(): raise RuntimeError('unsafe source file: '+str(src))
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with src.open('rb') as f, dst.open('xb') as g: shutil.copyfileobj(f, g)
        os.chmod(dst, src.stat().st_mode & 0o777)
    copyfile(dotgit/'index', root/'.git/index')
    objects = dotgit/'objects'
    if objects.is_symlink() or not objects.is_dir(): raise RuntimeError('unsafe objects directory')
    for parent, dirs, files in os.walk(objects, followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        for name in dirs:
            p = Path(parent)/name
            if p.is_symlink(): raise RuntimeError('symlink object directory')
            (root/'.git/objects'/p.relative_to(objects)).mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in files:
            p = Path(parent)/name
            copyfile(p, root/'.git/objects'/p.relative_to(objects))
    with (root/'.git/HEAD').open('x') as f: f.write(head+'\n')
    with (root/'.git/config').open('x') as f: f.write('[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n')
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_COUNT='0', GIT_NO_REPLACE_OBJECTS='1', GIT_TERMINAL_PROMPT='0')
    tracked = subprocess.check_output(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null', '-C', str(source), 'ls-files', '-z'], env=env).split(b'\0')
    for raw in tracked:
        if not raw: continue
        rel = Path(os.fsdecode(raw))
        if rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0] == '.git': raise RuntimeError('unsafe tracked path')
        src, dst = source/rel, root/rel
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if src.is_symlink(): os.symlink(os.readlink(src), dst)
        else: copyfile(src, dst)
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
        for member in entries:
            if not member.issym(): continue
            parts = list(PurePosixPath(member.name).parent.parts)
            for part in PurePosixPath(member.linkname).parts:
                if part == '..': parts.pop()
                elif part not in ('', '.'): parts.append(part)
                if '/'.join(parts) in link_paths: raise RuntimeError('symlink target passes through symlink: '+member.name)
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
