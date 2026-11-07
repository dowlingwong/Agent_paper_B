#!/usr/bin/env python3
"""One-shot Mac synthetic edit probe. Do not execute before independent review."""
import ast
import hashlib
import json
import os
import re
import stat
import sys
import time
import types
from pathlib import Path

EXPECTED = {
    'r1/exam/campaign.py': '36258a4335d8fb437fae463c31f18acf65b762a87bee87c5ea5d2042299f5b38',
    'r1/exam/b1_state_preserve.py': 'c1deccb0795d5b30643a7b50b62fceed7eecb2ca440cb22005c7491d9d03942c',
    'r1/c3/features.py': '08822bc9c1f7c846b26a449e891a7f48049e2b1a5b74a134ad3cf677d9885579',
}
ROOT_NAME = 'paper_b_mac_fixture_probe_20261107_2d823ecb5a174b5d'
if sys.platform != 'darwin' or not sys.dont_write_bytecode or not sys.flags.isolated or not sys.flags.no_site:
    raise RuntimeError('STOP: require Darwin and python3 -I -S -B from startup')
repo = Path(__file__).resolve().parents[4]
sources = {}
for relative, expected in EXPECTED.items():
    path = repo / relative
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise RuntimeError('STOP: reviewed source mismatch: ' + relative)
    sources[relative] = raw
    print('source_sha256:', relative, actual, flush=True)

publisher = types.ModuleType('r1.exam.b1_state_preserve')
publisher.__file__ = str(repo / 'r1/exam/b1_state_preserve.py')
exec(compile(sources['r1/exam/b1_state_preserve.py'], publisher.__file__, 'exec'), publisher.__dict__)
r1 = types.ModuleType('r1'); r1.__path__ = []
exam = types.ModuleType('r1.exam'); exam.__path__ = []
r1.exam = exam; exam.b1_state_preserve = publisher
sys.modules['r1'] = r1
sys.modules['r1.exam'] = exam
sys.modules['r1.exam.b1_state_preserve'] = publisher

# Execute unmodified definitions extracted by AST; all omitted campaign imports
# are deliberately absent. WorkerResult is an inert output container.
def extract(relative, names, namespace):
    tree = ast.parse(sources[relative], filename=relative)
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    if len(nodes) != len(names) or {node.name for node in nodes} != names:
        raise RuntimeError('STOP: selected source definitions missing or duplicated')
    code = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(code, relative + ':selected_ast', 'exec'), namespace)

class WorkerResult:
    def __init__(self, *args):
        self.args = args

namespace = {'Path': Path, 'hashlib': hashlib, 'json': json, 'time': time, 're': re, 'WorkerResult': WorkerResult}
extract('r1/c3/features.py', {'_pattern', '_loose', 'apply_edit'}, namespace)
extract('r1/exam/campaign.py', {'fixture_metric', 'DryrunFixturePreservationStop', 'FixtureWorker'}, namespace)

flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
parent_fd = os.open('/private/tmp', flags)
root_fd = None
try:
    parent = os.fstat(parent_fd)
    named = os.stat('/private/tmp', follow_symlinks=False)
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0 or not parent.st_mode & stat.S_ISVTX
            or (parent.st_dev, parent.st_ino) != (named.st_dev, named.st_ino)):
        raise RuntimeError('STOP: /private/tmp owner, sticky bit or identity mismatch')
    os.mkdir(ROOT_NAME, 0o700, dir_fd=parent_fd)
    root_fd = os.open(ROOT_NAME, flags, dir_fd=parent_fd)
    root_info = os.fstat(root_fd)
    by_name = os.stat(ROOT_NAME, dir_fd=parent_fd, follow_symlinks=False)
    if (not stat.S_ISDIR(root_info.st_mode) or root_info.st_uid != os.getuid()
            or stat.S_IMODE(root_info.st_mode) != 0o700 or root_info.st_dev != parent.st_dev
            or (root_info.st_dev, root_info.st_ino) != (by_name.st_dev, by_name.st_ino)):
        raise RuntimeError('STOP: unsafe probe root')
    fd = os.open('fixture.py', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=root_fd)
    try:
        initial = b'RATE = 1\n'
        if os.write(fd, initial) != len(initial): raise OSError('short initial write')
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(root_fd)
    root = Path('/private/tmp') / ROOT_NAME
    canonical = root / 'fixture.py'
    first = publisher.existing_identity(canonical)
    spec = types.SimpleNamespace(editable_paths=['fixture.py'], metric_name='synthetic_metric')
    worker = namespace['FixtureWorker'](root, 42)
    edits = [('1', '2'), ('2', '3')]
    observations = [(first, initial)]
    for index, (old, new) in enumerate(edits):
        proposal = types.SimpleNamespace(extra={'structured_edit': {'path': 'fixture.py', 'symbol': 'RATE', 'old': old, 'new': new}})
        result = worker.run_trial(proposal, spec, index)
        expected = ('RATE = ' + new + '\n').encode()
        current = publisher.existing_identity(canonical)
        if canonical.read_bytes() != expected or current is None:
            raise RuntimeError('STOP: canonical editable mismatch')
        metric = namespace['fixture_metric']({'fixture.py': expected.decode()}, 42)
        if result.args[3] != {'synthetic_metric': metric}:
            raise RuntimeError('STOP: synthetic metric mismatch')
        observations.append((current, expected))
    retained = list((root / '_to_delete').iterdir())
    if len(retained) != 2 or len({identity for identity, _ in observations}) != 3:
        raise RuntimeError('STOP: unexpected version count or identities')
    found = {(publisher.existing_identity(path), path.read_bytes()) for path in retained}
    if found != set(observations[:2]):
        raise RuntimeError('STOP: retained prior bytes/identities mismatch')
    print('probe_root:', root, flush=True)
    for number, (identity, payload) in enumerate(observations):
        print('version:', number, 'identity:', identity, 'sha256:', hashlib.sha256(payload).hexdigest(), flush=True)
    for path in sorted(retained):
        print('retained:', path.name, 'identity:', publisher.existing_identity(path), flush=True)
    print('two_synthetic_edits_and_retention: PASS', flush=True)
    print('probe_complete: no cleanup requested', flush=True)
finally:
    if root_fd is not None: os.close(root_fd)
    os.close(parent_fd)
