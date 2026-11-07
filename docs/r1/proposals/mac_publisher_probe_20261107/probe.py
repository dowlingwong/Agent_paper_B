#!/usr/bin/env python3
"""One-shot, retained Mac test of the exact reviewed DRYRUN publisher.

Do not run without the accompanying independent review and operator checks.
"""
import hashlib
import json
import os
import stat
import sys
import types
from pathlib import Path

EXPECTED_SOURCE = 'c1deccb0795d5b30643a7b50b62fceed7eecb2ca440cb22005c7491d9d03942c'
ROOT_NAME = 'paper_b_mac_publisher_probe_20261107_4dfe33725b0140b8'

if sys.platform != 'darwin' or not sys.dont_write_bytecode or not sys.flags.isolated or not sys.flags.no_site:
    raise RuntimeError('STOP: require Darwin and python3 -I -S -B from startup')
repo = Path(__file__).resolve().parents[4]
source_path = repo / 'r1/exam/b1_state_preserve.py'
source = source_path.read_bytes()
source_sha = hashlib.sha256(source).hexdigest()
if source_sha != EXPECTED_SOURCE:
    raise RuntimeError('STOP: reviewed publisher source hash mismatch')
module = types.ModuleType('b1_state_preserve_qualification')
module.__file__ = str(source_path)
exec(compile(source, str(source_path), 'exec'), module.__dict__)
print('publisher_source_sha256:', source_sha, flush=True)

flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
parent_fd = os.open('/private/tmp', flags)
root_fd = None
try:
    parent = os.fstat(parent_fd)
    named = os.stat('/private/tmp', follow_symlinks=False)
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
            or not parent.st_mode & stat.S_ISVTX
            or (parent.st_dev, parent.st_ino) != (named.st_dev, named.st_ino)):
        raise RuntimeError('STOP: /private/tmp owner, sticky bit or identity mismatch')
    os.mkdir(ROOT_NAME, 0o700, dir_fd=parent_fd)
    root_fd = os.open(ROOT_NAME, flags, dir_fd=parent_fd)
    root_info = os.fstat(root_fd)
    by_name = os.stat(ROOT_NAME, dir_fd=parent_fd, follow_symlinks=False)
    if (not stat.S_ISDIR(root_info.st_mode) or root_info.st_uid != os.getuid()
            or stat.S_IMODE(root_info.st_mode) != 0o700
            or root_info.st_dev != parent.st_dev
            or (root_info.st_dev, root_info.st_ino) != (by_name.st_dev, by_name.st_ino)):
        raise RuntimeError('STOP: probe root ownership, mode or identity mismatch')
    root = Path('/private/tmp') / ROOT_NAME
    state_path = root / 'batch_state.json'
    versions = [{'label':'DRYRUN', 'sequence':1}, {'label':'DRYRUN', 'sequence':2}]
    payloads = [(json.dumps(v, indent=2, allow_nan=False) + '\n').encode() for v in versions]
    if module.existing_identity(state_path) is not None:
        raise RuntimeError('STOP: new root already contains batch state')
    old_identity = module.publish_dryrun_state(state_path, versions[0], None)
    if state_path.read_bytes() != payloads[0] or module.existing_identity(state_path) != old_identity:
        raise RuntimeError('STOP: first publication bytes or identity mismatch')
    new_identity = module.publish_dryrun_state(state_path, versions[1], old_identity)
    archive = root / '_to_delete'
    retained = list(archive.iterdir())
    if len(retained) != 1 or not retained[0].name.startswith('batch_state.') or not retained[0].name.endswith('.json'):
        raise RuntimeError('STOP: unexpected retained names')
    if (state_path.read_bytes() != payloads[1]
            or module.existing_identity(state_path) != new_identity
            or retained[0].read_bytes() != payloads[0]
            or module.existing_identity(retained[0]) != old_identity
            or old_identity == new_identity):
        raise RuntimeError('STOP: final bytes or inode bindings mismatch')
    print('probe_root:', root, flush=True)
    print('first_identity:', old_identity, 'sha256:', hashlib.sha256(payloads[0]).hexdigest(), flush=True)
    print('current_identity:', new_identity, 'sha256:', hashlib.sha256(payloads[1]).hexdigest(), flush=True)
    print('retained_name:', retained[0].name, flush=True)
    print('two_publisher_versions: PASS', flush=True)
    print('probe_complete: no cleanup requested', flush=True)
finally:
    if root_fd is not None:
        os.close(root_fd)
    os.close(parent_fd)
