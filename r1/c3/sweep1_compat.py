"""Sweep-1 release compatibility replay (R1-SWEEP1-RELEASE-COMPAT option A).

The sweep-1 B.2 table was built at ``ab79b4ce`` with the v2 featurizer.  Main's featurizer is v3, so a normal
``dataset.build_from_sweep`` replay changes ``features.budget_frac_left`` for the control-plane/precheck/verify
rows of the sweep-1 ledgers.  This module runs the **builder of the sealed table's own commit** in an isolated
subprocess.  It never imports ``r1.c3.dataset`` from the running (v3) checkout.

Only the release path calls this module; the sweep-2 integrity check does not.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

# The commit recorded in the sealed sweep-1 B.2 table's build.json (v2 featurizer).
V2_BUILDER_COMMIT = "ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74"

_RUN = r"""
import sys, pathlib
sys.path.insert(0, sys.argv[1])
from r1.c3.dataset import build_from_sweep
build_from_sweep(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]),
                 paper_root=pathlib.Path(sys.argv[4]), classification=pathlib.Path(sys.argv[5]))
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _extract_commit(repo: Path, commit: str, dest: Path) -> None:
    """Extract the exact commit tree into ``dest`` (no working-tree files)."""
    tar_path = dest.parent / "builder.tar"
    try:
        subprocess.run(["git", "-C", str(repo), "archive", "--output", str(tar_path), commit], check=True,
                       timeout=600)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"sweep-1 compatibility builder commit {commit} is not available") from exc
    try:
        with tarfile.open(tar_path, mode="r:") as tf:
            for member in tf.getmembers():
                if member.name.startswith("/") or ".." in Path(member.name).parts:
                    raise ValueError("unsafe member in the sealed builder tree")
            # The repository archive contains regular files, directories and a few internal symlinks.  The
            # tarfile data filter rejects absolute/escaping links; no link is followed by the replay.
            tf.extractall(dest, filter="data")
    except (OSError, tarfile.TarError) as exc:
        raise ValueError("the sealed builder archive is unreadable") from exc


def rebuild_v2_table(*, index: Path, paper_root: Path, classification: Path, out: Path) -> None:
    """Rebuild the sweep-1 table with the v2 builder at the sealed table's commit.

    ``out`` must not exist.  The data/index/classification come from the current (published-main) checkout, as
    the release step requires; the code comes only from the pinned v2 tree.
    """
    repo = _repo_root()
    index, paper_root, classification, out = (Path(index).resolve(), Path(paper_root).resolve(),
                                               Path(classification).resolve(), Path(out).resolve())
    if out.exists():
        raise ValueError("compatibility replay output already exists")
    with tempfile.TemporaryDirectory(prefix="r1_sweep1_v2_builder_") as temp:
        tree = Path(temp) / "tree"
        tree.mkdir()
        _extract_commit(repo, V2_BUILDER_COMMIT, tree)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(tree)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # The old builder's own published-authority check uses the supplied paper root's origin/main; the
        # release step has already checked that root.  AR_HARNESS_ROOT is carried through unchanged.
        try:
            subprocess.run([sys.executable, "-B", "-c", _RUN, str(tree), str(index), str(out),
                            str(paper_root), str(classification)], check=True, cwd=str(tree), env=env, timeout=1800)
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError("the sealed v2 builder replay failed") from exc
    for name in ("proposals.jsonl", "configs.json", "build.json"):
        if not (out / name).is_file():
            raise ValueError(f"the sealed v2 builder replay did not write {name}")
