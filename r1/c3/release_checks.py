"""Integrity checks of the release step, per source (PRE-STAGE A, §6 integrity carve-out). AI-assisted (Claude).

A check runs only inside ``release.release`` (``release.integrity_context``), may open the audit's run log and
evaluation block, and returns pass/fail, counts and hashes, never a value; the release step reports a failing check by
its exception type only. Registering a new source's check (G.5, once its audit and check are reviewed; sweep 2's is
registered below)
changes this module, not ``release.py``, so earlier receipts and rows stay valid; each receipt records this module's
sha256.

R1-SWEEP1-RELEASE-COMPAT (option A): the sealed sweep-1 B.2 table was built at the B.2 audit commit ``ab79b4ce`` with
featurizer v2, while main's builder is v3 (W2), and its ``build.json`` records the classification sidecar by the absolute
path of the audit's paper root. The sweep-1 check therefore replays the table with the builder of ``ab79b4ce`` itself
(``_sweep1_compat_replay``: a throwaway shared clone at that commit, run in an isolated interpreter that imports nothing
from this checkout), and compares ``build.json`` with ``classification.path`` normalized for provenance (the same
repository-relative file; the classification file's sha256 must still match). Every other check of
``audit.verify_evidence_completion`` is unchanged; sweep 2's check is unchanged.

The table's builder imports the harness (``r1.headroom.e1b_collect``, for the sweep's noise source), so the child gets
the harness root that main's replay would use (``r1.harness.harness_root()``: ``$AR_HARNESS_ROOT``, else the release
checkout's sibling ``autoresearch_harness``) explicitly, and runs with ``-B`` so it writes no bytecode into the audited
harness or anywhere else. Environment and builder failures raise RuntimeError; identity mismatches raise ValueError,
including a ValueError raised by the builder's own source-data checks (the child exits with code 3), so a STOP reported
by exception type tells the two apart.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SWEEP1_TABLE_COMMIT = "ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74"   # the B.2 audit commit that built the sealed table
SWEEP1_FEATURIZER = "c3_features/v2"
SWEEP1_CLASSIFICATION_REL = "results/r1/evidence/C3_sweep_classification_20261028.json"   # the R1-SWEEP1-CLASSIFY row
REPO = Path(__file__).resolve().parents[2]

# Runs in ``python -I -B`` (no PYTHONPATH, no user site, no working directory on sys.path, no bytecode written), from
# the caller's working directory so that relative index paths are recorded as in the sealed build.json. argv: builder
# checkout, then "--probe", "--probe-harness" (also imports the builder's harness-dependent module) or index, out, paper
# root, classification; last the featurizer version.
_CHILD = r"""
import json, sys
from pathlib import Path
src = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(src))
def foreign():
    out = []
    for name, mod in list(sys.modules.items()):
        if name == "r1" or name.startswith("r1."):
            f = getattr(mod, "__file__", None)
            if f is None or not Path(f).resolve().is_relative_to(src):
                out.append(name)
    return out
from r1.c3 import dataset, features
if features.FEATURIZER_VERSION != sys.argv[-1]:
    raise SystemExit("featurizer " + features.FEATURIZER_VERSION + " is not " + sys.argv[-1])
if sys.argv[2] == "--probe-harness":
    import r1.headroom.e1b_collect
elif sys.argv[2] != "--probe":
    index, out, root, classification = sys.argv[2:6]
    try:
        dataset.build_from_sweep(index, out, paper_root=root, classification=classification)
    except ValueError as exc:                    # the builder's own source-data checks: an identity failure
        sys.stderr.write("ValueError: " + str(exc)[:200] + "\n")
        raise SystemExit(3)
bad = foreign()
if bad:
    raise SystemExit("modules not from the builder checkout: " + ",".join(sorted(bad)))
import os
print(json.dumps({"featurizer": features.FEATURIZER_VERSION, "git_head": dataset.git_head(),
                  "dont_write_bytecode": bool(sys.flags.dont_write_bytecode),
                  "harness_root": os.environ.get("AR_HARNESS_ROOT"),
                  "dataset": str(Path(dataset.__file__).resolve().relative_to(src)),
                  "r1_modules": sorted(n for n in sys.modules if n == "r1" or n.startswith("r1."))}))
"""

COMPLETION_KEEP = ("schema", "label", "label_block_sha256", "evaluation_block_sha256", "proposals_sha256",
                   "build_sha256", "configs_sha256", "plan_sha256", "counts", "label_seeds", "evaluation_seeds",
                   "index_sha256", "classification_sha256", "source", "extract_sha256")


def _builder_checkout(dest: Path, *, repo: Path = REPO, commit: str = SWEEP1_TABLE_COMMIT) -> Path:
    """A throwaway clone of ``repo`` at ``commit`` (objects shared by alternates; nothing is written to ``repo``)."""
    def git(*args, cwd=None):
        try:
            return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300,
                                  check=True).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError(f"the builder checkout failed: git {args[0] if args[0] != '-C' else args[2]}") from exc
    git("clone", "-q", "--shared", "--no-checkout", str(repo), str(dest))
    git("-C", str(dest), "checkout", "-q", "--detach", commit)
    if git("-C", str(dest), "rev-parse", "HEAD").strip() != commit or \
            git("-C", str(dest), "status", "--porcelain").strip():
        raise RuntimeError("the builder checkout is not a clean checkout of the table's commit")
    return dest


def checkout_bytes(*, repo: Path = REPO, commit: str = SWEEP1_TABLE_COMMIT) -> int:
    """Bytes of the files a checkout of ``commit`` writes (``git ls-tree -r -l``; for the scratch capacity check)."""
    try:
        out = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-l", commit], capture_output=True, text=True,
                             timeout=300, check=True).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("the table's commit is not in the release checkout") from exc
    return sum(int(f[3]) for f in (line.split(None, 4) for line in out.splitlines()) if f[1] == "blob")


def child_harness_root() -> Path:
    """The harness root main's replay would use (``r1.harness.harness_root()``); RuntimeError if it has no ``src``."""
    from r1 import harness
    root = harness.harness_root()
    if not (root / "src").is_dir():
        raise RuntimeError(f"harness src not found at {root / 'src'}; set AR_HARNESS_ROOT to the audited harness")
    return root


def _run_builder(src: Path, args: list[str], featurizer: str, *, harness_root: Path | None = None) -> dict:
    env = dict(os.environ)
    env.pop("AR_HARNESS_ROOT", None)
    if harness_root is not None:
        env["AR_HARNESS_ROOT"] = str(harness_root)
    try:
        res = subprocess.run([sys.executable, "-I", "-B", "-c", _CHILD, str(src), *args, featurizer], cwd=os.getcwd(),
                             env=env, capture_output=True, text=True, timeout=7200)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("sweep-1 compatibility replay timed out in the table's builder (7200 s)") from exc
    last = (res.stderr.strip().splitlines() or ["no output"])[-1][:200]
    if res.returncode == 3:
        raise ValueError(f"the table's builder refused the source data: {last}")
    if res.returncode != 0:
        raise RuntimeError(f"sweep-1 compatibility replay failed in the table's builder: {last}")
    out = json.loads(res.stdout.strip().splitlines()[-1])
    if out.get("dont_write_bytecode") is not True:
        raise RuntimeError("the table's builder ran with bytecode writing enabled")
    return out


def probe_builder(*, repo: Path = REPO, commit: str = SWEEP1_TABLE_COMMIT, featurizer: str = SWEEP1_FEATURIZER,
                  harness_root: Path | None = None) -> dict:
    """Import the table's builder in the isolated interpreter without building (a check of the pin; no data read).
    With ``harness_root``, also import its harness-dependent module ``r1.headroom.e1b_collect`` with that root."""
    with tempfile.TemporaryDirectory(prefix="r1_c3_sweep1_builder_") as temp:
        src = _builder_checkout(Path(temp) / "src", repo=repo, commit=commit)
        mode = "--probe" if harness_root is None else "--probe-harness"
        return _run_builder(src, [mode], featurizer, harness_root=harness_root)


def normalize_provenance(rebuilt: dict, sealed: dict, paper_root: Path) -> tuple[dict, dict]:
    """``build.json`` of the replay and of the sealed table with ``commit`` dropped and ``classification.path``
    replaced by its repository-relative form. The replay's classification file must be ``paper_root`` /
    ``SWEEP1_CLASSIFICATION_REL`` (the R1-SWEEP1-CLASSIFY sidecar), the sealed path must be absolute and end with that
    same repository-relative path, and every other classification field (its sha256 included) must be equal; otherwise
    ValueError."""
    rebuilt, sealed = json.loads(json.dumps(rebuilt)), json.loads(json.dumps(sealed))
    rebuilt.pop("commit", None)
    sealed.pop("commit", None)
    rc, sc = rebuilt.get("classification"), sealed.get("classification")
    if not isinstance(rc, dict) or not isinstance(sc, dict) or set(rc) != set(sc) or "path" not in rc:
        raise ValueError("evidence build metadata differs from full source replay (classification record)")
    if {k: v for k, v in rc.items() if k != "path"} != {k: v for k, v in sc.items() if k != "path"}:
        raise ValueError("evidence build metadata differs from full source replay (classification bytes)")
    try:
        rel = Path(rc["path"]).resolve().relative_to(Path(paper_root).resolve()).as_posix()
    except ValueError:
        raise ValueError("the replay's classification file is outside the paper root") from None
    if rel != SWEEP1_CLASSIFICATION_REL or not str(sc["path"]).startswith("/") or \
            not str(sc["path"]).endswith("/" + rel):
        raise ValueError("evidence build metadata differs from full source replay (classification path)")
    rc["path"] = sc["path"] = "<paper_root>/" + rel
    return rebuilt, sealed


def _sweep1_compat_replay(table: Path, paper_root: Path, index: Path, classification: Path, *, repo: Path = REPO,
                          commit: str = SWEEP1_TABLE_COMMIT, featurizer: str = SWEEP1_FEATURIZER) -> None:
    """``audit._verify_replay`` for the sealed sweep-1 table, with the table's own builder (R1-SWEEP1-RELEASE-COMPAT A):
    the same guards, scratch checks and byte comparisons; ``build.json`` compared after ``normalize_provenance``. The
    scratch check adds the builder checkout's size to audit's 2x the table."""
    from r1.c3 import audit
    from r1.c3.analysis_guard import guard_table, refuse_sealed
    if classification is None:
        raise ValueError("the sweep-1 compatibility replay needs the classification sidecar")
    table = Path(table)
    refuse_sealed(paper_root, index, classification)
    guard_table(table, table / "proposals.jsonl", table / "configs.json")
    sealed_meta = json.loads((table / "build.json").read_text())
    if sealed_meta.get("commit") != commit:
        raise ValueError("the compatibility replay applies only to the sealed sweep-1 table built at " + commit[:8])
    harness_root = child_harness_root()
    local = Path("/tmp")
    audit._local_scratch_mount(local)
    minimum = sum((table / name).stat().st_size for name in ("proposals.jsonl", "configs.json")) * 2 \
        + checkout_bytes(repo=repo, commit=commit)
    if shutil.disk_usage(local).free < minimum:
        raise ValueError("local scratch capacity insufficient for verification replay")
    with tempfile.TemporaryDirectory(prefix="r1_c3_sweep1_compat_", dir=str(local)) as temp:
        src = _builder_checkout(Path(temp) / "src", repo=repo, commit=commit)
        rebuilt = Path(temp) / "table"
        probe = _run_builder(src, [str(index), str(rebuilt), str(paper_root), str(classification)], featurizer,
                             harness_root=harness_root)
        if probe["git_head"] != commit:
            raise RuntimeError("the replay did not run the table's builder")
        for name in ("proposals.jsonl", "configs.json"):
            if (rebuilt / name).read_bytes() != (table / name).read_bytes():
                raise ValueError(f"evidence table differs from full source replay: {name}")
        new, old = normalize_provenance(json.loads((rebuilt / "build.json").read_text()), sealed_meta, paper_root)
        if new != old:
            raise ValueError("evidence build metadata differs from full source replay")


@contextlib.contextmanager
def _sweep1_replay_installed(audit):
    """Within the sweep-1 check only, ``audit._verify_replay`` is the compatibility replay; restored on exit."""
    original = audit._verify_replay
    audit._verify_replay = _sweep1_compat_replay
    try:
        yield
    finally:
        audit._verify_replay = original


def sweep1_integrity(table_dir: Path, audit_dir: Path, *, paper_root: Path, index: Path, classification: Path) -> dict:
    """The sweep-1 B.2 audit: ``audit.verify_evidence_completion`` (re-derives both role blocks from the raw seed
    results and binds the completion record), its table replay done with the table's own builder at ``ab79b4ce``
    (R1-SWEEP1-RELEASE-COMPAT A)."""
    from r1.c3 import audit
    from r1.c3.release import integrity_context
    with integrity_context(), _sweep1_replay_installed(audit):
        completion = audit.verify_evidence_completion(Path(table_dir), Path(audit_dir) / "label_block.jsonl",
                                                      Path(paper_root), Path(index), Path(classification))
    return {"check": "audit.verify_evidence_completion (table replay: builder of ab79b4ce, provenance-normalized "
                     "classification path; R1-SWEEP1-RELEASE-COMPAT A)", "pass": True,
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
