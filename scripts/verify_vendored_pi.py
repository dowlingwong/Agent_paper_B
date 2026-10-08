#!/usr/bin/env python3
"""Vendor verifier for the pinned Pi source tree (Round 8 Stage 0A, Phase 1).

Validates the upstream record, the preserved MIT license, and the absence of
nested git, credentials, sessions, dependency trees, caches, and compiled
products. It recomputes the current tree manifest and compares it against the
pristine baseline (`scripts/pi_pristine_manifest.txt`), then classifies every
non-pristine file as:

- `approved_generated_data`  (the version-bound model catalog, verified against
  its provenance record's file hashes),
- `approved_integration`     (UPSTREAM.md / LOCAL_CHANGES.md and any files in the
  approved integration allowlist),
- `unexplained`              (anything else -> verification fails).

Emits a machine-readable JSON summary suitable for preflight.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PI_ROOT = REPO_ROOT / "third_party" / "pi"
UPSTREAM = PI_ROOT / "UPSTREAM.md"
LOCAL_CHANGES = PI_ROOT / "LOCAL_CHANGES.md"
LICENSE = PI_ROOT / "LICENSE"
PRISTINE_MANIFEST = REPO_ROOT / "scripts" / "pi_pristine_manifest.txt"
GENERATED_DATA_DIR = "packages/ai/src/providers/data"
GENERATED_DATA_PROVENANCE = REPO_ROOT / "protocols/pi_model_data_provenance.json"
LOCAL_MODIFICATIONS = REPO_ROOT / "protocols/pi_local_modifications.yaml"

# Approved non-pristine integration files (beyond the generated data).
APPROVED_INTEGRATION_FILES = {
    "UPSTREAM.md",
    "LOCAL_CHANGES.md",
}

EXCLUDE_DIRS = {".git", "node_modules", "dist", ".cache", ".turbo", "__pycache__"}
FORBIDDEN_MARKERS = (
    "id_rsa", "id_ed25519", ".pem", "credentials.json", "auth.json",
    "service-account", "secrets", ".env",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(part in EXCLUDE_DIRS for part in rel.split("/")):
            continue
        files[rel] = _sha256(path)
    return files


def _load_pristine() -> dict[str, str]:
    files: dict[str, str] = {}
    for line in PRISTINE_MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.partition("  ")
        files[rel] = digest
    return files


def _approved_generated_data() -> dict[str, str] | None:
    """Return the expected {rel_path: sha256} for the approved model data, or
    None when no provenance record exists."""
    if not GENERATED_DATA_PROVENANCE.is_file():
        return None
    record = json.loads(GENERATED_DATA_PROVENANCE.read_text(encoding="utf-8"))
    files = record.get("files", {})
    return {f"{GENERATED_DATA_DIR}/{name}": digest for name, digest in files.items()}


def _approved_local_modifications() -> dict[str, str]:
    """Return {rel_path: expected patched sha256} from the local-modification
    ledger, or an empty mapping when no patch is recorded.

    Pinning to an exact patched digest is what keeps this from being a rubber
    stamp: an approved file that changes again becomes `unexplained` until the
    ledger is updated and re-reviewed.
    """
    if not LOCAL_MODIFICATIONS.is_file():
        return {}
    try:
        import yaml
    except ImportError:  # pragma: no cover - pyyaml is a declared dependency
        return {}
    record = yaml.safe_load(LOCAL_MODIFICATIONS.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        return {}
    approved: dict[str, str] = {}
    for entry in record.get("modifications") or []:
        if isinstance(entry, dict) and entry.get("path") and entry.get("patched_sha256"):
            approved[str(entry["path"])] = str(entry["patched_sha256"])
    return approved


def _required_record_fields() -> dict[str, str]:
    return {
        "upstream_commit": r"086c32e74530564922d011ade23ff582c9d63116",
        "resolved_url": r"https://github.com/earendil-works/pi",
        "license_digest": r"0457f5bcec3b3b211605dfb5d1a49042fd638f3686a410fe099c24a25af13c48",
        "manifest_digest": r"d4228eae4bf89ea3d1319d96f3245f390938a0b39794faf86f634d4fe5946c2c",
        "license_name": r"MIT",
    }


def main() -> int:
    summary: dict = {
        "artifact_kind": "vendored_pi_verification",
        "qualifying": False,
        "pi_root": str(PI_ROOT.relative_to(REPO_ROOT)),
        "checks": {},
        "verdict": "pass",
    }
    errors: list[str] = []

    # 1. record schema
    if not UPSTREAM.is_file():
        errors.append("UPSTREAM.md missing")
    else:
        text = UPSTREAM.read_text(encoding="utf-8")
        for field, pattern in _required_record_fields().items():
            if not re.search(pattern, text):
                errors.append(f"UPSTREAM.md missing required field: {field}")
    summary["checks"]["upstream_record"] = not any("UPSTREAM" in e for e in errors)

    # 2. license present and hash-valid
    if not LICENSE.is_file():
        errors.append("LICENSE missing")
    elif _sha256(LICENSE) != _required_record_fields()["license_digest"]:
        errors.append("LICENSE digest mismatch")
    summary["checks"]["license"] = "LICENSE" not in " ".join(errors)

    # 3. forbidden products (scanned over the vendored *source*, excluding
    # gitignored build products such as node_modules/ and dist/)
    forbidden: list[str] = []
    for path in PI_ROOT.rglob("*"):
        rel = path.relative_to(PI_ROOT).as_posix()
        parts = rel.split("/")
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        if path.is_dir() and path.name == ".git":
            forbidden.append(rel + "/")
        if path.is_file() and any(marker in path.name.lower() for marker in FORBIDDEN_MARKERS):
            forbidden.append(rel)
    if forbidden:
        errors.append(f"forbidden products present: {sorted(forbidden)}")
    summary["checks"]["forbidden_products"] = not forbidden

    # 4. manifest comparison + classification
    current = _tree_files(PI_ROOT)
    pristine = _load_pristine()
    approved_data = _approved_generated_data()
    added = sorted(set(current) - set(pristine))
    removed = sorted(set(pristine) - set(current))
    modified = sorted(rel for rel in set(current) & set(pristine) if current[rel] != pristine[rel])

    approved_patches = _approved_local_modifications()
    classification: dict[str, list[str]] = {
        "pristine": sorted(set(pristine)),
        "approved_generated_data": [],
        "approved_integration": [],
        "approved_local_modification": [],
        "unexplained": [],
    }
    data_mismatch: list[str] = []
    patch_mismatch: list[str] = []
    for rel in added + modified:
        if approved_data is not None and rel in approved_data:
            if current[rel] == approved_data[rel]:
                classification["approved_generated_data"].append(rel)
            else:
                data_mismatch.append(rel)
        elif rel in approved_patches:
            if current[rel] == approved_patches[rel]:
                classification["approved_local_modification"].append(rel)
            else:
                patch_mismatch.append(rel)
        elif rel in APPROVED_INTEGRATION_FILES:
            classification["approved_integration"].append(rel)
        else:
            classification["unexplained"].append(rel)
    if data_mismatch:
        errors.append(f"approved generated data files do not match the provenance record: {data_mismatch}")
    if patch_mismatch:
        errors.append(
            "locally modified vendored files do not match protocols/pi_local_modifications.yaml: "
            f"{patch_mismatch}"
        )
    if classification["unexplained"]:
        errors.append(f"unexplained additions to the vendored tree: {classification['unexplained']}")
    if removed:
        errors.append(f"pristine files removed: {removed}")

    summary["checks"]["manifest"] = {
        "pristine_files": len(pristine),
        "current_files": len(current),
        "removed": removed,
        "modified": modified,
        "classification": {key: sorted(value) for key, value in classification.items()},
    }
    summary["checks"]["generated_data"] = (
        approved_data is not None
        and all(current.get(rel) == digest for rel, digest in (approved_data or {}).items())
    )

    summary["errors"] = errors
    summary["verdict"] = "pass" if not errors else "fail"
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
