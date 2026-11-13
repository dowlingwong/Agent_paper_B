"""Resume-safe work units for HTCondor jobs that may be evicted and restarted. AI-assisted draft.

A job that HTCondor evicts is started again from the beginning (the pool holds a job after 6
starts). Work is split into units; a unit counts as complete only once its output manifest
``<unit_dir>/UNIT_COMPLETE.json`` exists. The manifest is written atomically (temporary file in the
same directory, fsync, ``os.replace``, fsync of the directory) **after** the unit's outputs, and it
lists each output file with its size and SHA-256. On restart, ``run_units`` skips complete units.

A manifest whose listed outputs are missing or differ is a STOP (``UnitError``): a unit is never
silently redone over half-trusted outputs. A unit directory without a manifest is incomplete; its
partial outputs are moved into ``<unit_dir>/_to_delete/attempt-<n>/`` (never deleted) before the unit
runs again.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Iterable

MANIFEST = "UNIT_COMPLETE.json"
SCHEMA = "htc_unit_complete/v1"


class UnitError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mark_complete(unit_dir: Path, outputs: Iterable[str], extra: dict | None = None) -> dict:
    """Write the unit's manifest atomically after its outputs exist (paths relative to unit_dir)."""
    unit_dir = Path(unit_dir)
    files = {}
    for rel in sorted(set(outputs)):
        p = unit_dir / rel
        if rel == MANIFEST or rel.startswith("_to_delete") or not p.is_file() or p.is_symlink():
            raise UnitError(f"output {rel!r} is not a regular file in {unit_dir}")
        with open(p, "rb") as fh:
            os.fsync(fh.fileno())
        files[rel] = {"bytes": p.stat().st_size, "sha256": _sha256(p)}
    _fsync_dir(unit_dir)
    manifest = {"schema": SCHEMA, "unit": unit_dir.name, "outputs": files, "extra": extra or {}}
    tmp = unit_dir / (MANIFEST + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, unit_dir / MANIFEST)
    _fsync_dir(unit_dir)
    return manifest


def is_complete(unit_dir: Path) -> bool:
    """True if the manifest exists and every listed output matches; UnitError if it does not match."""
    unit_dir = Path(unit_dir)
    m = unit_dir / MANIFEST
    if not m.exists():
        return False
    try:
        manifest = json.loads(m.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise UnitError(f"unreadable unit manifest {m}: {exc}") from exc
    if manifest.get("schema") != SCHEMA or manifest.get("unit") != unit_dir.name or not isinstance(manifest.get("outputs"), dict):
        raise UnitError(f"invalid unit manifest {m}")
    for rel, meta in manifest["outputs"].items():
        p = unit_dir / rel
        if not p.is_file() or p.stat().st_size != meta.get("bytes") or _sha256(p) != meta.get("sha256"):
            raise UnitError(f"unit {unit_dir.name}: output {rel!r} differs from its completion manifest")
    return True


def _set_aside(unit_dir: Path) -> Path | None:
    entries = [e for e in unit_dir.iterdir() if e.name != "_to_delete"] if unit_dir.exists() else []
    if not entries:
        return None
    attic = unit_dir / "_to_delete"
    attic.mkdir(exist_ok=True)
    n = 1 + sum(1 for e in attic.iterdir() if e.name.startswith("attempt-"))
    target = attic / f"attempt-{n}"
    target.mkdir()
    for e in entries:
        os.replace(e, target / e.name)
    return target


def run_units(root: Path, units: Iterable[str], work: Callable[[str, Path], Iterable[str]]) -> dict:
    """Run ``work(unit, unit_dir)`` for each incomplete unit; it returns the output file names."""
    root = Path(root)
    done, ran, set_aside = [], [], {}
    for unit in units:
        if not unit or "/" in unit or unit.startswith((".", "_")):
            raise UnitError(f"invalid unit name {unit!r}")
        d = root / unit
        if is_complete(d):
            done.append(unit)
            continue
        moved = _set_aside(d)
        if moved:
            set_aside[unit] = str(moved)
        d.mkdir(parents=True, exist_ok=True)
        outputs = list(work(unit, d))
        mark_complete(d, outputs)
        ran.append(unit)
    return {"skipped_complete": done, "ran": ran, "set_aside": set_aside}
