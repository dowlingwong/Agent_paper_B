from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared planning dependency
    yaml = None  # type: ignore[assignment]

# Superseded layer name. The manuscript's restoration surface calls the layer
# "External tool state" (`07_evaluation.tex`); the pre-Round-6 E0 protocol and
# test fixtures used the obsolete internal name. Any occurrence is rejected so
# old fixtures cannot silently pass with the wrong semantics.
OBSOLETE_RESTORE_LAYER_NAMES = frozenset({"declared_internal_tool_state"})


def tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass(frozen=True)
class CheckpointManifest:
    schema_version: str
    checkpoint_id: str
    root_id: str
    parent_checkpoint_id: str | None
    tree_hash: str
    budget_remaining: dict[str, float]
    feasible_regimes: list[str]
    availability_registry_version: str = "unregistered"
    availability_evaluator_version: str = "unregistered"
    availability_evidence_hash: str = ""
    environment_digest: str | None = None
    history_digest: str | None = None
    layer_digests: dict[str, str] | None = None

    @classmethod
    def load(cls, path: Path) -> "CheckpointManifest":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


class FileSnapshotManager:
    """Filesystem-only reference implementation for deterministic toy fixtures."""

    def capture(
        self,
        workspace: Path,
        snapshot_dir: Path,
        *,
        checkpoint_id: str,
        root_id: str,
        parent_checkpoint_id: str | None,
        budget_remaining: Mapping[str, float],
        feasible_regimes: Sequence[str],
        availability_registry_version: str = "unregistered",
        availability_evaluator_version: str = "unregistered",
        availability_evidence_hash: str = "",
        environment_digest: str | None = None,
        history_digest: str | None = None,
        layer_digests: Mapping[str, str] | None = None,
    ) -> CheckpointManifest:
        if snapshot_dir.exists():
            raise FileExistsError(snapshot_dir)
        payload = snapshot_dir / "workspace"
        snapshot_dir.mkdir(parents=True)
        shutil.copytree(workspace, payload)
        manifest = CheckpointManifest(
            schema_version="0.1",
            checkpoint_id=checkpoint_id,
            root_id=root_id,
            parent_checkpoint_id=parent_checkpoint_id,
            tree_hash=tree_hash(payload),
            budget_remaining=dict(budget_remaining),
            feasible_regimes=sorted(feasible_regimes),
            availability_registry_version=availability_registry_version,
            availability_evaluator_version=availability_evaluator_version,
            availability_evidence_hash=availability_evidence_hash,
            environment_digest=environment_digest,
            history_digest=history_digest,
            layer_digests=dict(layer_digests or {"workspace_filesystem": tree_hash(payload)}),
        )
        (snapshot_dir / "manifest.json").write_text(
            json.dumps(asdict(manifest), sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return manifest

    def restore(self, snapshot_dir: Path, target_workspace: Path) -> CheckpointManifest:
        manifest = CheckpointManifest.load(snapshot_dir / "manifest.json")
        if target_workspace.exists():
            raise FileExistsError(
                f"restore target already exists; refusing destructive overwrite: {target_workspace}"
            )
        shutil.copytree(snapshot_dir / "workspace", target_workspace)
        if tree_hash(target_workspace) != manifest.tree_hash:
            raise RuntimeError("restored workspace hash mismatch")
        return manifest

    def validate(self, snapshot_dir: Path, restored_workspace: Path) -> bool:
        manifest = CheckpointManifest.load(snapshot_dir / "manifest.json")
        return tree_hash(restored_workspace) == manifest.tree_hash


@dataclass(frozen=True)
class RestoreLayerResult:
    layer: str
    expected_digest: str | None
    observed_digest: str | None
    match: bool
    required: bool
    detail: str = ""


@dataclass(frozen=True)
class RestoreOnlyReport:
    schema_version: str
    checkpoint_id: str
    executes_scientific_regime: bool
    exact_restore: bool
    layer_results: tuple[RestoreLayerResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "checkpoint_id": self.checkpoint_id,
            "executes_scientific_regime": self.executes_scientific_regime,
            "exact_restore": self.exact_restore,
            "layer_results": [asdict(result) for result in self.layer_results],
        }


def e0_protocol_restore_layers(repo_root: Path) -> dict[str, tuple[str, ...]]:
    """Load the required and declared-non-restorable layers from the hash-bound
    E0 instrument protocol.  Missing required layers fail closed."""

    path = repo_root / "protocols/e0_instrument_protocol.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"E0 instrument protocol is missing: {path}")
    if yaml is None:
        raise RuntimeError("pyyaml is required to load the E0 instrument protocol")
    with path.open(encoding="utf-8") as handle:
        record = yaml.safe_load(handle)
    probe = record.get("restore_only_probe", {})
    required = tuple(probe.get("required_layers") or ())
    nonrestorable = tuple(probe.get("declared_nonrestorable_layers") or ())
    if not required:
        raise ValueError("E0 instrument protocol does not declare required restore layers")
    return {"required_layers": required, "nonrestorable_layers": nonrestorable}


def restore_only_compare(
    manager: FileSnapshotManager,
    snapshot_dir: Path,
    target_workspace: Path,
    *,
    layer_probes: Mapping[str, Callable[[Path, CheckpointManifest], str | None]] | None = None,
    required_layers: Sequence[str],
    nonrestorable_layers: Sequence[str] = (),
) -> RestoreOnlyReport:
    """Restore and compare registered layers without executing any regime.

    `required_layers` must be supplied explicitly: the E0 path passes the set
    loaded from the hash-bound protocol via `e0_protocol_restore_layers`, and
    the toy smoke passes its own declared subset.  A required layer with no
    probe or no registered digest fails closed.  Obsolete layer names and
    required layers that the protocol declares non-restorable are rejected.
    """

    if not required_layers:
        raise ValueError("restore-only probe requires an explicit required layer set")
    obsolete = OBSOLETE_RESTORE_LAYER_NAMES.intersection(required_layers)
    if obsolete:
        raise ValueError(
            f"obsolete restore layer name rejected: {sorted(obsolete)}; "
            "use declared_external_tool_state"
        )
    nonrestorable = set(nonrestorable_layers)
    overlap = nonrestorable.intersection(required_layers)
    if overlap:
        raise ValueError(
            f"required layers are declared non-restorable: {sorted(overlap)}"
        )
    manifest = manager.restore(snapshot_dir, target_workspace)
    expected = dict(manifest.layer_digests or {})
    expected.setdefault("workspace_filesystem", manifest.tree_hash)
    probes = dict(layer_probes or {})
    probes.setdefault("workspace_filesystem", lambda path, _: tree_hash(path))
    results: list[RestoreLayerResult] = []
    for layer in sorted(set(expected) | set(required_layers) | set(probes)):
        expected_digest = expected.get(layer)
        probe = probes.get(layer)
        observed = probe(target_workspace, manifest) if probe is not None else None
        required = layer in required_layers
        match = expected_digest is not None and observed == expected_digest
        detail = "" if match else ("probe_missing" if probe is None else "digest_mismatch_or_unregistered")
        results.append(
            RestoreLayerResult(layer, expected_digest, observed, match, required, detail)
        )
    exact = all(result.match for result in results if result.required)
    return RestoreOnlyReport(
        schema_version="0.1",
        checkpoint_id=manifest.checkpoint_id,
        executes_scientific_regime=False,
        exact_restore=exact,
        layer_results=tuple(results),
    )
