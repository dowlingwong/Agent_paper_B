"""Worker layout for RL (design note §4, RL-LAYOUT). ENGINEERING_ONLY.

The isolated worker can read every allow-listed path, "so the validation and test labels wherever a node keeps them
there (a read-only mount does not hide them)" (``isolation.py`` limits). For RL the metric is the reward, so the
worker must not see what it is scored on, and under RL-BUDGET A not even the training data.

**The guarantee is the construction:** the runner builds the worker's mount namespace from the plan, and parent-only
files never reach any allow-listed path (the worker root, the data mount, the shim, a shared ``/dev/shm``).
``check_worker_root`` is a check on top of that, run on the built root before the run. It refuses:

* anything that is not a regular file or a directory (symlinks, FIFOs, sockets, devices), checked with ``lstat``
  before anything is opened;
* a non-empty file with the bytes of a parent-only file (a renamed or moved copy, a hard link);
* a file or directory at the relative path of a parent-only file;
* a data or frozen file that is not in the plan, or whose bytes differ from the plan.

Code files (role ``code``) are edited by every proposal, so they are checked only against the parent-only bytes, and
any file the plan does not list is refused unless it sits directly in a directory that holds a planned code file. What the scan cannot see:
compressed, encoded, partial or embedded copies of a parent-only file (only whole-file bytes are compared); files the
worker creates at run time; paths outside the root. Empty files are not compared by bytes (every empty file has the
same hash).

Layouts (``WORKER_ROLES``):

* ``served`` (RL-LAYOUT A with RL-BUDGET A, recommended): code and frozen files only; the parent serves training rows
  and evaluation inputs through the result channel and keeps every label;
* ``train_and_val_inputs`` (RL-LAYOUT B): code, frozen, the training split and the validation inputs without labels;
  data use is then bounded only by the split's size;
* ``train_only`` (RL-LAYOUT C): code, frozen and the training split; evaluation inputs streamed by the parent.

``shared_dev_shm`` (the host's ``/dev/shm``, through which a worker "can keep state between runs") is refused for RL
training unless a named waiver is given.
"""
from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

ROLES = ("code", "frozen", "train_inputs", "train_labels", "val_inputs", "val_labels", "test_inputs", "test_labels")
WORKER_ROLES = {
    "served": frozenset({"code", "frozen"}),
    "train_and_val_inputs": frozenset({"code", "frozen", "train_inputs", "train_labels", "val_inputs"}),
    "train_only": frozenset({"code", "frozen", "train_inputs", "train_labels"}),
}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


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
    """{relative path: role} -> hashed entries; every role must be known and every file a regular file."""
    out = []
    for rel, role in sorted(roles.items()):
        if role not in ROLES:
            raise LayoutError(f"{rel}: unknown role {role!r}")
        p = Path(root) / rel
        if not stat.S_ISREG(os.lstat(p).st_mode):
            raise LayoutError(f"{rel}: not a regular file")
        out.append(DataFile(rel, role, sha256_file(p)))
    return out


def plan_worker_root(files: list[DataFile], layout: str, *, shared_dev_shm: bool = False,
                     shm_waiver: str | None = None) -> list[DataFile]:
    if layout not in WORKER_ROLES:
        raise LayoutError(f"unknown RL-LAYOUT {layout!r} (status quo layouts are not allowed for RL training)")
    if shared_dev_shm and not shm_waiver:
        raise LayoutError("shared_dev_shm gives the worker a state channel between runs; refused for RL training "
                          "without a named waiver")
    allowed = WORKER_ROLES[layout]
    plan = [f for f in files if f.role in allowed]
    parent_only = {f.sha256 for f in files if f.role not in allowed and f.sha256 != EMPTY_SHA256}
    clash = [f.rel for f in plan if f.sha256 in parent_only]
    if clash:
        raise LayoutError(f"files allowed in the worker have the bytes of a parent-only file: {clash}")
    return plan


def check_worker_root(root: Path, files: list[DataFile], layout: str, **plan_kw) -> dict:
    """Scan a built worker root against the plan (module docstring); returns a small report."""
    root = Path(root)
    plan = {f.rel: f for f in plan_worker_root(files, layout, **plan_kw)}
    allowed = WORKER_ROLES[layout]
    parent_hash = {f.sha256: f.rel for f in files if f.role not in allowed and f.sha256 != EMPTY_SHA256}
    parent_paths = {f.rel for f in files if f.role not in allowed}
    code_dirs = {Path(f.rel).parent.as_posix() for f in plan.values() if f.role == "code"}
    seen = {}
    stack = [root]
    while stack:
        d = stack.pop()
        for entry in sorted(os.listdir(d)):
            p = d / entry
            rel = p.relative_to(root).as_posix()
            mode = os.lstat(p).st_mode
            if stat.S_ISDIR(mode):
                if rel in parent_paths:
                    raise LayoutError(f"{rel}: a directory at the path of a parent-only file")
                stack.append(p)
                continue
            if not stat.S_ISREG(mode):
                raise LayoutError(f"{rel}: not a regular file or directory (symlink, FIFO, socket or device)")
            if rel in parent_paths:
                raise LayoutError(f"{rel}: at the path of a parent-only file")
            digest = sha256_file(p)
            if digest in parent_hash:
                raise LayoutError(f"{rel}: has the bytes of parent-only {parent_hash[digest]}")
            entry_plan = plan.get(rel)
            if entry_plan is None:
                if Path(rel).parent.as_posix() in code_dirs:
                    continue            # a file an edit added in a code directory (checked against parent bytes)
                raise LayoutError(f"{rel}: not in the worker plan")
            if entry_plan.role != "code" and entry_plan.sha256 != digest:
                raise LayoutError(f"{rel}: differs from the planned file")
            seen[rel] = digest
    missing = sorted(r for r, f in plan.items() if f.role != "code" and r not in seen)
    if missing:
        raise LayoutError(f"planned files missing from the worker root: {missing}")
    return {"layout": layout, "files": len(seen), "parent_only_withheld": len(parent_paths)}
