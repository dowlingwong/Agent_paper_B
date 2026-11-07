"""Preserve repeat writes in the in-process fake probe fixture only.

All paths belong to a fresh private pytest root, and must remain stable and
cooperative; no production server or pytest execution is authorized here.
"""
from __future__ import annotations

import json
import os
import stat
import uuid
from pathlib import Path


def install_probe_preservation(monkeypatch, server_class, root, binary):
    root = Path(root).resolve(strict=True)
    binary = str(Path(binary).resolve(strict=True))
    info = root.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('STOP: fake probe root must be owned and private')
    old_write_text = Path.write_text

    def replace_preserving(path, contents, encoding='utf-8', errors=None, newline=None):
        if os.path.lexists(path):
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1:
                raise RuntimeError('STOP: unsafe fake probe record')
            archive = root / '_to_delete'
            archive.mkdir(mode=0o700, exist_ok=True)
            info = archive.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise RuntimeError('STOP: unsafe fake probe archive')
            unique = archive / uuid.uuid4().hex
            unique.mkdir(mode=0o700)
            # Private fresh directory is cooperative protection, not renameat2.
            path.rename(unique / path.name)
        with path.open('x', encoding=encoding, errors=errors, newline=newline) as handle:
            return handle.write(contents)

    def preserving_write_text(path, contents, encoding=None, errors=None, newline=None):
        if (path.parent == root / 'logs' and path.name.startswith('probe_')
                and path.name.endswith('.json')):
            return replace_preserving(path, contents, encoding or 'utf-8', errors, newline)
        if newline is None:
            return old_write_text(path, contents, encoding=encoding, errors=errors)
        return old_write_text(path, contents, encoding=encoding, errors=errors, newline=newline)

    def save(instance):
        if (instance.label not in ('ENGINEERING_ONLY probe', 'ENGINEERING_ONLY probe CPU control')
                or instance.binary != binary or getattr(instance, 'b1_containment', None) is not None):
            raise RuntimeError('STOP: fake probe writer used outside fixture scope')
        path = instance.record_path
        parent = path.parent
        if (parent.parent != root / 'logs' or not parent.name.startswith('probe_')
                or parent.is_symlink() or parent.resolve(strict=True) != parent):
            raise RuntimeError('STOP: fake probe server record outside fixture scope')
        replace_preserving(path, json.dumps(instance.record, indent=2) + '\n')

    monkeypatch.setattr(Path, 'write_text', preserving_write_text)
    monkeypatch.setattr(server_class, '_save', save)
