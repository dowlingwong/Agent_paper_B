"""Training-split-only worker layout (design note §4, RL-LAYOUT). ENGINEERING_ONLY.

The isolated worker can read every allow-listed path, "so the validation and test labels wherever a node keeps them
there (a read-only mount does not hide them)" (``isolation.py`` limits). For RL the metric is the reward, so the
worker must not see what it is scored on. Every data file of a node gets a role; ``plan_worker_root`` returns the
files the worker root may hold, and ``check_worker_root`` scans a built root and refuses:

* any file whose sha256 equals a parent-only file's (a renamed or re-pathed copy of a label file is caught);
* any path whose name is a parent-only file's name;
* symlinks (the root is built from copies or bind mounts, never links), and anything outside the root;
* any file the plan does not list (the root holds exactly the planned files).

RL-LAYOUT A (``"train_and_val_inputs"``): code, frozen files, the training split (inputs and labels) and the
validation **inputs** without labels; the parent keeps validation labels and all test files and scores the worker's
answers. RL-LAYOUT B (``"train_only"``): no evaluation file at all; the parent streams evaluation inputs through the
result channel. Validation inputs alone reveal no label, but under A the worker can still overfit to them
(transductively); B closes that too.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

ROLES = ("code", "frozen", "train_inputs", "train_labels", "val_inputs", "val_labels", "test_inputs", "test_labels")
WORKER_ROLES = {
    "train_and_val_inputs": frozenset({"code", "frozen", "train_inputs", "train_labels", "val_inputs"}),
    "train_only": frozenset({"code", "frozen", "train_inputs", "train_labels"}),
}


class LayoutError(ValueError):
    """A refused layout."""


@dataclass(frozen=True)
class DataFile:
    rel: str           # path inside the node kit / data directory
    role: str
    sha256: str


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def manifest(root: Path, roles: dict[str, str]) -> list[DataFile]:
    """{relative path: role} -> hashed entries; every role must be known and every file must exist."""
    out = []
    for rel, role in sorted(roles.items()):
        if role not in ROLES:
            raise LayoutError(f"{rel}: unknown role {role!r}")
        p = Path(root) / rel
        if not p.is_file() or p.is_symlink():
            raise LayoutError(f"{rel}: not a regular file")
        out.append(DataFile(rel, role, sha256_file(p)))
    return out


def plan_worker_root(files: list[DataFile], layout: str) -> list[DataFile]:
    if layout not in WORKER_ROLES:
        raise LayoutError(f"unknown RL-LAYOUT {layout!r} (status quo layouts are not allowed for RL training)")
    allowed = WORKER_ROLES[layout]
    plan = [f for f in files if f.role in allowed]
    parent_only = {f.sha256 for f in files if f.role not in allowed}
    clash = [f.rel for f in plan if f.sha256 in parent_only]
    if clash:
        raise LayoutError(f"files allowed in the worker have the bytes of a parent-only file: {clash}")
    return plan


def check_worker_root(root: Path, files: list[DataFile], layout: str) -> dict:
    """Scan a built worker root against the plan (module docstring); returns a small report."""
    root = Path(root).resolve()
    plan = {f.rel: f for f in plan_worker_root(files, layout)}
    allowed = WORKER_ROLES[layout]
    parent_hash = {f.sha256: f.rel for f in files if f.role not in allowed}
    parent_names = {Path(f.rel).name for f in files if f.role not in allowed}
    seen = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                raise LayoutError(f"{p.relative_to(root)}: symlink in the worker root")
        for name in filenames:
            p = Path(dirpath) / name
            rel = p.relative_to(root).as_posix()
            digest = sha256_file(p)
            if digest in parent_hash:
                raise LayoutError(f"{rel}: has the bytes of parent-only {parent_hash[digest]}")
            if name in parent_names:
                raise LayoutError(f"{rel}: carries the name of a parent-only file")
            if rel not in plan:
                raise LayoutError(f"{rel}: not in the worker plan")
            if plan[rel].sha256 != digest:
                raise LayoutError(f"{rel}: differs from the planned file")
            seen[rel] = digest
    missing = sorted(set(plan) - set(seen))
    if missing:
        raise LayoutError(f"planned files missing from the worker root: {missing}")
    return {"layout": layout, "files": len(seen), "parent_only_withheld": len(parent_hash)}
