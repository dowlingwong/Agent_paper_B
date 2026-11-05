"""Read-only OpenML replay input snapshot; not a sandbox or execution authority.

This helper cannot determine whether a cache is complete and must never be used
alone to enable a replay. Production OpenML replay remains stopped until the
independently reviewed Linux execution boundary and all-case preflight exist.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

HARNESS_COMMIT = '6adf3859de66c4814fcf376eed59880fbd8eeaf7'
NODE_FILES = ('dataset.json', 'benchmark.py', 'config.yaml', 'train.py')


class SnapshotStop(RuntimeError):
    pass


def _bytes_hash(data):
    return hashlib.sha256(data).hexdigest()


def _regular(path):
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise SnapshotStop(f'STOP: inaccessible input: {path}') from exc
    if not stat.S_ISREG(mode):
        raise SnapshotStop(f'STOP: non-regular or symlink input: {path}')
    return path.read_bytes()


def cache_snapshot(root):
    """Fingerprint a nonempty regular-file cache without following symlinks."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise SnapshotStop('STOP: cache must be a real directory')
    entries = []
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        for name in dirs:
            p = here / name
            if p.is_symlink() or not p.is_dir():
                raise SnapshotStop(f'STOP: cache contains a non-directory or symlink: {p}')
        for name in files:
            p = here / name
            data = _regular(p)
            entries.append({'path': p.relative_to(root).as_posix(), 'size': len(data),
                            'sha256': _bytes_hash(data)})
    if not entries:
        raise SnapshotStop('STOP: cache is empty')
    entries.sort(key=lambda row: row['path'])
    canonical = json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()
    return {'files': entries, 'sha256': _bytes_hash(canonical)}


def snapshot(harness, node, cache):
    """Bind a node identity, committed source bytes and full cache file list.

    STOP on any mismatch. A matching snapshot establishes identity only, not
    cache completeness, network isolation, or offline executability.
    """
    harness = Path(harness)
    if not isinstance(node, str) or not node.startswith('openml_') or '/' in node or '\\' in node:
        raise SnapshotStop('STOP: invalid OpenML node')
    try:
        head = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SnapshotStop('STOP: cannot read harness HEAD') from exc
    if head != HARNESS_COMMIT:
        raise SnapshotStop('STOP: wrong harness commit')
    source = {}; dataset_raw = None
    for name in NODE_FILES:
        rel = f'nodes/{node}/{name}'
        path = harness / rel
        raw = _regular(path)
        try:
            expected = subprocess.check_output(['git', '-C', str(harness), 'show', f'{head}:{rel}'], stderr=subprocess.DEVNULL)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise SnapshotStop(f'STOP: missing pinned node file: {rel}') from exc
        if raw != expected:
            raise SnapshotStop(f'STOP: node file differs from pinned commit: {rel}')
        source[name] = _bytes_hash(raw)
        if name == 'dataset.json': dataset_raw = raw
    try:
        identity = json.loads(dataset_raw)
        dataset_id = identity['dataset_id']
        if identity['node_name'] != node or type(dataset_id) is not int or dataset_id <= 0:
            raise ValueError('invalid identity')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SnapshotStop('STOP: invalid pinned dataset identity') from exc
    return {'harness_commit': head, 'node': node, 'dataset_id': dataset_id,
            'source_sha256': source, 'cache': cache_snapshot(cache),
            'offline_executability': 'NOT_ESTABLISHED'}
