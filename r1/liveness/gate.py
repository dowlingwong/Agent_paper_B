"""D28 gate (P5): refuse LLM-backed collection on nodes without a liveness pass.

The runner calls :func:`require_live` with the nodes it is about to collect
and a liveness manifest (a committed ``liveness.json`` report or an equivalent
mapping).  A missing or failed node raises ``RuntimeError`` with a ``STOP:``
prefix, which the remote batch script turns into a stopped run.

AI-assisted (BUILD_BATCH3, P5); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_liveness_manifest(path: str | Path) -> dict:
    """Load a liveness report written by :func:`r1.liveness.check.write_reports`."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "nodes" not in payload:
        raise ValueError(f"not a liveness manifest: {path}")
    return payload


def require_live(nodes: list[str], manifest: dict) -> dict:
    """Return the manifest when every node passed D28, else raise ``STOP:``.

    *manifest* maps node names to verdicts under ``manifest["nodes"]`` (the
    report format), or is a bare mapping from node to verdict.
    """
    verdicts = manifest.get("nodes", manifest)
    missing, failed = [], []
    for node in nodes:
        verdict = verdicts.get(node)
        if verdict is None:
            missing.append(node)
        elif not verdict.get("pass"):
            failed.append(f"{node} ({', '.join(verdict.get('failed_criteria') or ['unknown'])})")
    if missing or failed:
        parts = []
        if missing:
            parts.append(f"no liveness verdict for: {', '.join(missing)}")
        if failed:
            parts.append(f"failed D28 liveness: {', '.join(failed)}")
        raise RuntimeError("STOP: " + "; ".join(parts))
    return manifest
