from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .checkpoint import FileSnapshotManager


SAFE_BRANCH_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")


@dataclass(frozen=True)
class BranchManifest:
    schema_version: str
    branch_id: str
    checkpoint_id: str
    root_id: str
    parent_branch_id: str | None
    checkpoint_tree_hash: str


class FileBranchIsolationManager:
    """Creates one filesystem tree per branch under an explicit branch root."""

    def __init__(self, branch_root: Path, snapshots: FileSnapshotManager | None = None) -> None:
        self.branch_root = branch_root
        self.snapshots = snapshots or FileSnapshotManager()

    def fork(
        self,
        snapshot_dir: Path,
        *,
        branch_id: str,
        parent_branch_id: str | None,
    ) -> Path:
        if not SAFE_BRANCH_ID.fullmatch(branch_id):
            raise ValueError("branch_id contains unsafe characters")
        branch_dir = self.branch_root / branch_id
        if branch_dir.exists():
            raise FileExistsError(branch_dir)
        workspace = branch_dir / "workspace"
        manifest = self.snapshots.restore(snapshot_dir, workspace)
        branch_manifest = BranchManifest(
            schema_version="0.1",
            branch_id=branch_id,
            checkpoint_id=manifest.checkpoint_id,
            root_id=manifest.root_id,
            parent_branch_id=parent_branch_id,
            checkpoint_tree_hash=manifest.tree_hash,
        )
        branch_dir.mkdir(parents=True, exist_ok=True)
        (branch_dir / "branch_manifest.json").write_text(
            json.dumps(asdict(branch_manifest), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return workspace
