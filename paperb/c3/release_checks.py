"""Integrity checks of the release step, per source (PRE-STAGE A, §6 integrity carve-out). AI-assisted (Claude).

A check runs only inside ``release.release`` (``release.integrity_context``), may open the audit's run log and
evaluation block, and returns pass/fail, counts and hashes, never a value; the release step reports a failing check by
its exception type only. Registering a new source's check (G.5, once its audit and check are reviewed; sweep 2's is
registered below)
changes this module, not ``release.py``, so earlier receipts and rows stay valid; each receipt records this module's
sha256. The G.5 check (``g5_integrity``) is registered by part 3b-2 of the G.5 code unit.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

COMPLETION_KEEP = ("schema", "label", "label_block_sha256", "evaluation_block_sha256", "proposals_sha256",
                   "build_sha256", "configs_sha256", "plan_sha256", "counts", "label_seeds", "evaluation_seeds",
                   "index_sha256", "classification_sha256", "source", "extract_sha256")


def _sweep1_compat_published() -> None:
    """The sweep-1 compatibility replay runs ``r1/c3/sweep1_compat.py``; pin it like ``sweep2_batch.py``."""
    import subprocess
    from r1.c3 import sweep1_compat
    here = Path(__file__).resolve().parent
    if Path(sweep1_compat.__file__).resolve() != here / "sweep1_compat.py":
        raise ValueError("r1.c3.sweep1_compat is not the module file beside release_checks.py (shadowed?)")
    repo = here.parents[1]
    differs = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", "refs/remotes/origin/main", "HEAD", "--",
                              "r1/c3/sweep1_compat.py"], capture_output=True).returncode
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", "r1/c3/sweep1_compat.py"],
                           capture_output=True, text=True).stdout.strip()
    if differs or dirty:
        raise ValueError("r1/c3/sweep1_compat.py differs from origin/main or is modified")


def sweep1_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path,
                     classification: Path) -> dict:
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
    _sweep1_compat_published()
    try:
        sealed = json.loads((Path(table_dir) / "build.json").read_text())
    except (OSError, ValueError) as exc:
        raise ValueError("sealed sweep-1 build.json is unreadable") from exc
    if sealed.get("commit") != sweep1_compat.V2_BUILDER_COMMIT:
        raise ValueError("sealed sweep-1 table is not from the pinned v2 builder commit")
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


G5_PATHS = ("sweep2/t1_tasl", "sweep2/g1b", "sweep2/g4", "sweep2/s2_c2_lib.py")
G5_SPEC = "sweep2/t1_tasl/g5_tasl_spec.json"


def _g5_git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """One git call of the G.5 publication check (a seam for the tests)."""
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def _g5_unpublished(repo: Path, paths) -> None:
    differs = _g5_git(repo, "diff", "--quiet", "refs/remotes/origin/main", "HEAD", "--", *paths).returncode
    dirty = _g5_git(repo, "status", "--porcelain", "--untracked-files=no", "--", *paths).stdout.strip()
    if differs or dirty:
        raise ValueError(f"the G.5 code ({', '.join(paths)}) differs from origin/main or is modified")


def _g5_published():
    """``release.py`` checks the r1/c3 modules it runs; the G.5 check also runs the G.5 code in ``sweep2/`` (the
    modules ``g5_tasl.IMPORT_SOURCES`` lists and the committed spec), so those files must equal origin/main, be
    unmodified, and be the files the imported modules come from. The directories are checked before anything is
    imported; after the import, every file of ``IMPORT_SOURCES`` must lie inside them and is checked again by name
    (review m4). Returns the ``g5_assemble`` module."""
    import sys
    here = Path(__file__).resolve().parent
    repo = here.parents[1]
    _g5_unpublished(repo, G5_PATHS)
    sys.path.insert(0, str(repo / "sweep2" / "t1_tasl"))
    import g5_assemble
    sources = dict(g5_assemble.S.IMPORT_SOURCES)
    derived = sorted(set(sources.values()) | {G5_SPEC})
    outside = [r for r in derived if not any(r == p or r.startswith(p + "/") for p in G5_PATHS)]
    if outside:
        raise ValueError(f"G.5 modules outside the checked paths: {outside}")
    _g5_unpublished(repo, derived)
    for name, rel in sources.items():
        mod = sys.modules.get(name)
        if mod is not None and Path(mod.__file__).resolve() != (repo / rel).resolve():
            raise ValueError(f"{name} is not the module file {rel} (shadowed?)")
    return g5_assemble


def g5_integrity(table_dir: Path, audit_dir: Path) -> dict:
    """The G.5 T1 tables (part 3b-2 of the G.5 code unit; REL-CODE A): ``g5_assemble.verify_evidence`` re-derives the
    table and label block (and, once R1-T1-LABELS-TEST-RELEASE exists, the evaluation block) from the sealed G.5 tree
    through its access-logged reader, inside the integrity context, and compares bytes; before the test row it reads
    label seeds only. Its completion schema is ``g5_t1_evidence_completion/1`` (not the B.2 audit's)."""
    from r1.c3.release import integrity_context, test_released
    g5_assemble = _g5_published()
    test = test_released("T1")
    with integrity_context():
        out = g5_assemble.verify_evidence(Path(table_dir), Path(audit_dir), test=test)
    if out.get("pass") is not True or out["completion"].get("schema") != g5_assemble.COMPLETION_SCHEMA:
        raise ValueError("not a G.5 evidence completion")
    return {"check": out["check"], "pass": True, "stage": out["stage"], "completion_sha256": out["completion_sha256"],
            "completion": {k: out["completion"][k] for k in COMPLETION_KEEP if k in out["completion"]}}


INTEGRITY_CHECKS = {"sweep1": sweep1_integrity, "sweep2": sweep2_integrity, "g5": g5_integrity}
