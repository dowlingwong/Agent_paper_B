"""Hash-pinned runtime closure for an M3 boundary run (candidate).

Builds the ``closure`` list of the bootstrap specification for a Python
workload: the interpreter, every shared library it and the selected packages'
extension modules load (from ``ldd``), the standard library and the selected
top-level site-packages entries, plus explicitly named extra files. Each entry
is bound at its own host path, read-only, with its SHA-256; the closure digest
is what the preflight binding and the later real execution compare.

The closure is computed on the host that runs the boundary. Completeness is
not proved here: anything missing makes the boundary run fail (an import or
loader error), which is a STOP, never a silent fallback.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import sysconfig

SKIP_DIRS = {'test', 'tests', 'idlelib', 'tkinter', 'turtledemo', 'ensurepip', 'lib2to3'}


class ClosureStop(RuntimeError):
    pass


def _sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _walk(root, *, skip=()):
    for current, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and d not in skip
                         and not d.endswith('.dist-info'))
        for name in sorted(files):
            if name.startswith('_tkinter'):
                continue
            yield Path(current) / name


def _ldd(path):
    try:
        out = subprocess.run(['ldd', str(path)], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClosureStop(f'STOP: ldd unavailable for {path}') from exc
    libs = set()
    for line in out.splitlines():
        parts = line.split()
        if '=>' in parts:
            i = parts.index('=>')
            if i + 1 < len(parts) and parts[i + 1].startswith('/'):
                libs.add(os.path.normpath(parts[i + 1]))   # $ORIGIN/../.. forms
        elif parts and parts[0].startswith('/'):
            libs.add(os.path.normpath(parts[0]))
    return libs


def build_closure(packages, *, extra=(), python=None):
    """Return ``{'items': [...], 'sha256': ...}`` for ``python`` + ``packages``.

    ``packages`` are top-level site-packages names (directories or modules,
    including vendored ``*.libs`` directories). ``extra`` is a list of
    ``(source, target)`` pairs, e.g. trusted repository modules.
    """
    python = Path(python or sys.executable).resolve()
    stdlib = Path(sysconfig.get_paths()['stdlib'])
    platstdlib = Path(sysconfig.get_paths()['platstdlib'])
    purelib = Path(sysconfig.get_paths()['purelib'])
    files = {}

    def add(source, target=None):
        source = Path(source)
        real = source.resolve()
        if not real.is_file():
            return
        st = real.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_mode & (stat.S_ISUID | stat.S_ISGID):
            raise ClosureStop(f'STOP: unusable closure file {real}')
        files[str(target or source)] = str(real)

    add(python)
    for lib in _ldd(python):
        add(lib)              # bound at the path the loader asks for
    for root in sorted({stdlib, platstdlib}):
        for p in _walk(root, skip=('site-packages', 'dist-packages', 'config-3.13-x86_64-linux-gnu')):
            add(p)
    for name in packages:
        hits = [purelib / name, purelib / (name + '.py')]
        hits += sorted(purelib.glob(name + '.cpython-*.so'))
        found = [h for h in hits if h.exists()]
        if not found:
            raise ClosureStop(f'STOP: package {name} not found in {purelib}')
        for hit in found:
            for p in (_walk(hit) if hit.is_dir() else [hit]):
                add(p)
    for so in [s for s in list(files.values()) if '.so' in Path(s).name]:
        for lib in _ldd(so):
            add(lib)
    if Path('/etc/ld.so.cache').is_file():
        add('/etc/ld.so.cache')
    for source, target in extra:
        add(source, target)
    items = []
    for target, source in sorted(files.items()):
        items.append({'source': source, 'target': target, 'sha256': _sha_file(source)})
    digest = hashlib.sha256(json.dumps([[i['target'], i['sha256']] for i in items],
                                       separators=(',', ':')).encode()).hexdigest()
    return {'items': items, 'sha256': digest, 'python': str(python)}
