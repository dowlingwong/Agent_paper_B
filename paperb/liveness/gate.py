"""D28 gate (P5, revised 14 Oct): refuse LLM-backed collection on dead nodes.

The runner calls :func:`require_live` with the nodes it is about to collect
and a liveness manifest (a committed ``liveness.json`` report or an equivalent
mapping).  A missing or failed node raises ``RuntimeError`` with a ``STOP:``
prefix, which the remote batch script turns into a stopped run.

The gate consumes only LLM-backed (``manager_kind: langgraph``), memory-on
liveness manifests.  The **memory-off contrast arm** of D24 (a collection
whose manifest says ``memory_mode: none`` and ``arm_role: contrast``) is
exempt from the memory-mode match: its node eligibility comes from the
memory-on liveness check (PLAN §10 D28).  The exemption never admits a
scripted or memory-off liveness manifest.

AI-assisted (BUILD_BATCH3 P5; exemption added in BUILD_BATCH4, P6);
ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path

MEMORY_ON_MODES = ("append_only_summary", "append_only_summary_with_rationale")


def load_liveness_manifest(path: str | Path) -> dict:
    """Load a liveness report written by :func:`r1.liveness.check.write_reports`."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "nodes" not in payload:
        raise ValueError(f"not a liveness manifest: {path}")
    return payload


def require_live(
    nodes: list[str],
    manifest: dict,
    *,
    memory_mode: str | None = None,
    arm_role: str | None = None,
) -> dict:
    """Return the manifest when every node passed D28, else raise ``STOP:``.

    *manifest* maps node names to verdicts under ``manifest["nodes"]`` (the
    report format), or is a bare mapping from node to verdict.  *memory_mode*
    and *arm_role* describe the collection about to start; a memory-off
    contrast collection is exempt from the memory-mode match (never from the
    manifest's own LLM/memory-on requirement).
    """
    exempt = memory_mode == "none" and arm_role == "contrast"
    kind = manifest.get("manager_kind")
    manifest_mode = manifest.get("memory_mode")
    if kind != "langgraph":
        raise RuntimeError(
            "STOP: liveness manifest is not from an LLM-backed run "
            f"(manager_kind={kind!r}); run `python -m r1.liveness --run --manager langgraph` first"
        )
    if manifest_mode not in MEMORY_ON_MODES:
        raise RuntimeError(
            "STOP: liveness manifest is not from a memory-on run "
            f"(memory_mode={manifest_mode!r}); the D28 check is the memory-on one"
        )
    if not exempt and memory_mode is not None and memory_mode != manifest_mode:
        raise RuntimeError(
            f"STOP: collection memory_mode={memory_mode!r} does not match the "
            f"liveness manifest memory_mode={manifest_mode!r}"
        )
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
