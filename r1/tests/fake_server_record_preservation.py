"""Test-only preserving record writer for in-process fake server fixtures.

The test-owned root must be fresh, private, and unchanged by other processes.
This helper does not qualify pytest, spawned probes, or any real server.
"""
from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path


def install_preserving_fake_record(monkeypatch, instance, root):
    root = Path(root).resolve(strict=True)
    root_stat = root.stat()
    if not stat.S_ISDIR(root_stat.st_mode) or root_stat.st_uid != os.getuid() or root_stat.st_mode & 0o077:
        raise RuntimeError('STOP: fake-server fixture root must be owned and private')

    def save():
        if instance.label != 'DRYRUN' or getattr(instance, 'b1_containment', None) is not None:
            raise RuntimeError('STOP: test-only fake record writer used outside its scope')
        path = instance.record_path
        if path.parent.resolve(strict=True) != root / 'batch' or path.parent.is_symlink():
            raise RuntimeError('STOP: fake record is outside the fixture batch')
        if os.path.lexists(path):
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise RuntimeError('STOP: unsafe fake record')
            archive = root / '_to_delete'
            archive.mkdir(mode=0o700, exist_ok=True)
            info = archive.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise RuntimeError('STOP: unsafe fake record archive')
            unique = archive / uuid.uuid4().hex
            unique.mkdir(mode=0o700)
            # The destination directory is fresh and private. Path.rename is
            # not no-replace against an uncooperative concurrent writer.
            path.rename(unique / path.name)
        with path.open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(instance.record, indent=2) + '\n')

    monkeypatch.setattr(instance, '_save', save)
