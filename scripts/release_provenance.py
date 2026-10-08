"""Verify release bytes against both the package and the declared Git commit."""
from __future__ import annotations
import hashlib
import subprocess
from pathlib import Path, PurePosixPath


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=root, stderr=subprocess.PIPE)


def verify_manifest(root: Path, package: Path, manifest: dict) -> list[str]:
    errors = []
    source = manifest.get('source_commit', '')
    try:
        resolved = git(root, 'rev-parse', '--verify', source + '^{commit}').decode().strip()
        if source != resolved:
            errors.append('source_commit must be a full commit hash')
        git(root, 'merge-base', '--is-ancestor', source, 'HEAD')
        git(root, 'show', source + ':papers/paper_b/main.tex')
    except subprocess.CalledProcessError:
        return ['source commit is absent, not an ancestor, or lacks the B manuscript anchor']
    if manifest.get('source_commit_dirty') is not False:
        errors.append('source_commit_dirty is not false')
    rows = manifest.get('files', [])
    if not rows or manifest.get('file_count') != len(rows):
        errors.append('manifest file count mismatch or empty manifest')
    seen = set()
    for row in rows:
        name = row.get('path', '')
        path = PurePosixPath(name)
        if not name or path.is_absolute() or '..' in path.parts or name in seen:
            errors.append('unsafe or duplicate manifest path: ' + name)
            continue
        seen.add(name)
        try:
            original = git(root, 'show', source + ':' + name)
            actual = (package / name).read_bytes()
        except (subprocess.CalledProcessError, OSError):
            errors.append('missing source/package file: ' + name)
            continue
        expected = hashlib.sha256(original).hexdigest()
        if row.get('sha256') != expected or hashlib.sha256(actual).hexdigest() != expected:
            errors.append('hash mismatch: ' + name)
        if row.get('bytes') != len(original):
            errors.append('size mismatch: ' + name)
    actual_paths = {str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
    extra = actual_paths - seen - {'README.md', 'MANIFEST.json'}
    if extra:
        errors.append('unmanifested files: ' + ', '.join(sorted(extra)))
    return errors
