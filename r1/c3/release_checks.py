"""Integrity checks of the release step, per source (PRE-STAGE A, §6 integrity carve-out). AI-assisted (Claude).

A check runs only inside ``release.release`` (``release.integrity_context``), may open the audit's run log and
evaluation block, and returns pass/fail, counts and hashes, never a value; the release step reports a failing check by
its exception type only. Registering a new source's check (G.5, once its audit and check are reviewed; sweep 2's is
registered below)
changes this module, not ``release.py``, so earlier receipts and rows stay valid; each receipt records this module's
sha256.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

COMPLETION_KEEP = ("schema", "label", "label_block_sha256", "evaluation_block_sha256", "proposals_sha256",
                   "build_sha256", "configs_sha256", "plan_sha256", "counts", "label_seeds", "evaluation_seeds",
                   "index_sha256", "classification_sha256", "source", "extract_sha256")


def sweep1_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path, classification: Path) -> dict:
    """The sweep-1 B.2 audit: ``audit.verify_evidence_completion`` (re-derives both role blocks from the raw seed
    results and binds the completion record).

    R1-SWEEP1-RELEASE-COMPAT option A: the sealed table was built at ``ab79b4ce`` with the v2 featurizer; main's
    featurizer is v3.  The release path therefore replays with the sealed builder commit in an isolated
    subprocess, and the invocation-root path fields in ``build.json`` are normalised as provenance while the
    classification bytes' sha256 is still checked.  Every other check is unchanged; the sweep-2 check is
    untouched.
    """
    from r1.c3 import audit, sweep1_compat
    from r1.c3.release import integrity_context
    with integrity_context():
        completion = audit.verify_evidence_completion(
            Path(table_dir), Path(audit_dir) / "label_block.jsonl", Path(paper_root), Path(index),
            Path(classification), replay_builder=sweep1_compat.rebuild_v2_table)
    return {"check": "audit.verify_evidence_completion", "pass": True,
            "completion_sha256": hashlib.sha256((Path(audit_dir) / "evidence_completion.json").read_bytes()).hexdigest(),
            "completion": {k: completion[k] for k in COMPLETION_KEEP if k in completion}}


def _sweep2_batch_published() -> None:
    """``release.py`` (pinned by the release row) checks the modules it knows are published and unshadowed; the
    sweep-2 check also runs ``r1/c3/sweep2_batch.py``, so it checks that module the same way here."""
    import subprocess
    from r1.c3 import sweep2_batch
    here = Path(__file__).resolve().parent
    if Path(sweep2_batch.__file__).resolve() != here / "sweep2_batch.py":
        raise ValueError("r1.c3.sweep2_batch is not the module file beside release_checks.py (shadowed?)")
    repo = here.parents[1]
    differs = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", "refs/remotes/origin/main", "HEAD", "--",
                              "r1/c3/sweep2_batch.py"], capture_output=True).returncode
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", "r1/c3/sweep2_batch.py"],
                           capture_output=True, text=True).stdout.strip()
    if differs or dirty:
        raise ValueError("r1/c3/sweep2_batch.py differs from origin/main or is modified")


def sweep2_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path) -> dict:
    """The sweep-2 B.2 audit (R1-SWEEP2-SETTINGS (2)): ``audit.verify_evidence_completion`` with ``source='sweep2'``
    (re-verifies the sweep-2 batch and its index, rebuilds the table, re-derives both role blocks from the raw seed
    results and binds the schema-/4 completion record, the sweep-2 addendum and its start row)."""
    from r1.c3 import audit
    from r1.c3.release import integrity_context
    _sweep2_batch_published()
    with integrity_context():
        completion = audit.verify_evidence_completion(Path(table_dir), Path(audit_dir) / "label_block.jsonl",
                                                      Path(paper_root), Path(index), None, source="sweep2")
    if completion.get("source") != "sweep2" or completion.get("schema") != audit.SWEEP2_COMPLETION_SCHEMA:
        raise ValueError("not a sweep-2 audit completion")
    return {"check": "audit.verify_evidence_completion(source='sweep2')", "pass": True,
            "completion_sha256": hashlib.sha256((Path(audit_dir) / "evidence_completion.json").read_bytes()).hexdigest(),
            "completion": {k: completion[k] for k in COMPLETION_KEEP if k in completion}}


INTEGRITY_CHECKS = {"sweep1": sweep1_integrity, "sweep2": sweep2_integrity}
