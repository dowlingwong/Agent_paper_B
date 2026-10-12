"""Locate and pin the governed harness (BUILD_RUNBOOK §0: R1 code pins the harness commit)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def harness_root() -> Path:
    """Harness checkout: $AR_HARNESS_ROOT, else the sibling ``autoresearch_harness``."""
    env = os.environ.get("AR_HARNESS_ROOT")
    if env:
        return Path(env).resolve()
    return (REPO.parent / "autoresearch_harness").resolve()


def import_harness() -> Path:
    """Put the harness ``src`` on sys.path and return the harness root."""
    root = harness_root()
    src = root / "src"
    if not src.is_dir():
        raise RuntimeError(f"harness src not found at {src}; set AR_HARNESS_ROOT")
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return root


def harness_commit(root: Path | None = None) -> dict[str, str | bool]:
    """Commit hash, branch and dirtiness of the harness checkout."""
    root = root or harness_root()

    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()

    try:
        status = git("status", "--porcelain", "--untracked-files=no")
        return {"commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                "dirty": bool(status)}
    except Exception as exc:  # noqa: BLE001 - provenance is best effort, never silently invented
        return {"commit": "unknown", "branch": "unknown", "dirty": True, "error": str(exc)}
