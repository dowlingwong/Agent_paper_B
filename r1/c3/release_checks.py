"""Integrity checks of the release step, per source (PRE-STAGE A, §6 integrity carve-out). AI-assisted (Claude).

A check runs only inside ``release.release`` (``release.integrity_context``), may open the audit's run log and
evaluation block, and returns pass/fail, counts and hashes, never a value; the release step reports a failing check by
its exception type only. Registering a new source's check (sweep 2, G.5, once their audits and checks are reviewed)
changes this module, not ``release.py``, so earlier receipts and rows stay valid; each receipt records this module's
sha256.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

COMPLETION_KEEP = ("schema", "label", "label_block_sha256", "evaluation_block_sha256", "proposals_sha256",
                   "build_sha256", "configs_sha256", "plan_sha256", "counts", "label_seeds", "evaluation_seeds",
                   "index_sha256", "classification_sha256")


def sweep1_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path, classification: Path) -> dict:
    """The sweep-1 B.2 audit: ``audit.verify_evidence_completion`` (re-derives both role blocks from the raw seed
    results and binds the completion record)."""
    from r1.c3 import audit
    from r1.c3.release import integrity_context
    with integrity_context():
        completion = audit.verify_evidence_completion(Path(table_dir), Path(audit_dir) / "label_block.jsonl",
                                                      Path(paper_root), Path(index), Path(classification))
    return {"check": "audit.verify_evidence_completion", "pass": True,
            "completion_sha256": hashlib.sha256((Path(audit_dir) / "evidence_completion.json").read_bytes()).hexdigest(),
            "completion": {k: completion[k] for k in COMPLETION_KEEP if k in completion}}


INTEGRITY_CHECKS = {"sweep1": sweep1_integrity}
