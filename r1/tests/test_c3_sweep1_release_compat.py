"""R1-SWEEP1-RELEASE-COMPAT (option A): the sweep-1 integrity check of the release step replays the sealed table with the
builder of the table's own commit and compares build.json with the classification path normalized for provenance.

Synthetic fixture: a small builder repository with two commits, featurizer v2 (the sealed table's) and v3 (main's), whose
``budget_frac_left`` differs on ledgers with skipped proposals, as in the diagnosis; the "sealed" table is built at a
/ceph-like paper root and replayed at a /work-like one. Like the real one, the synthetic builder needs the harness
(``$AR_HARNESS_ROOT/src``, a fake harness here) and imports a module from it. No sealed data, label or evaluation value
is used.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from r1.c3 import analysis_guard, audit, release_checks as C

ROOT = Path(__file__).resolve().parents[2]

FEATURES = '''FEATURIZER_VERSION = "{version}"


def budget_frac_left(b, used, total):
    return {formula}
'''
DATASET = r'''import hashlib, json, os, subprocess, sys
from pathlib import Path
from r1.c3 import features
REPO = Path(__file__).resolve().parents[2]


def git_head():
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build_from_sweep(index, out, *, paper_root=None, classification=None):
    harness = Path(os.environ.get("AR_HARNESS_ROOT", "/nonexistent")) / "src"    # as r1.harness.import_harness
    if not harness.is_dir():
        raise RuntimeError(f"harness src not found at {harness}; set AR_HARNESS_ROOT")
    sys.path.insert(0, str(harness))
    import fakeharness                                   # as r1.headroom.e1b_collect imports the harness
    root = Path(paper_root)
    idx = json.loads((root / index).read_text()) if not Path(index).is_absolute() else json.loads(Path(index).read_text())
    if idx.get("moved"):
        raise ValueError("moved sweep differs from original commit blobs")      # a source-data identity check
    out = Path(out)
    out.mkdir(parents=True)
    rows = []
    for r in idx["records"]:
        rows.append({"proposal_id": r["id"], "features": {"budget_frac_left": round(
            features.budget_frac_left(r["b"], r["used"], idx["runs_total"]), 6)}})
    (out / "proposals.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
    (out / "configs.json").write_text(json.dumps(idx["configs"], sort_keys=True))
    meta = {"label": "EVIDENCE", "commit": git_head(),
            "classification": {"path": str(Path(classification).resolve()), "sha256": _sha(classification),
                               "native_index_label": idx["label"]},
            "sweep_index": {"path": str(index), "sha256": _sha(root / index)}, "replay_checks": len(rows)}
    (out / "build.json").write_text(json.dumps(meta, indent=1))
    return meta
'''
INDEX = {"label": "ENGINEERING_ONLY", "runs_total": 20, "configs": {"c1": {"lr": 0.1}},
         "records": [{"id": "p1", "b": 1, "used": 0}, {"id": "p2", "b": 3, "used": 2},
                     {"id": "p3", "b": 6, "used": 3},          # a skipped proposal before it: v2 and v3 differ
                     {"id": "p4", "b": 9, "used": 5}]}
CLASSIFICATION_REL = "results/r1/evidence/C3_sweep_classification_20261028.json"
INDEX_REL = "results/r1/evidence/C3_sweep_index.json"


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *a], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture()
def world(tmp_path, monkeypatch):
    repo = tmp_path / "builder"
    (repo / "r1" / "c3").mkdir(parents=True)
    _git(tmp_path, "init", "-q", str(repo))
    for p in ("r1/__init__.py", "r1/c3/__init__.py"):
        (repo / p).write_text("")
    (repo / "r1/c3/dataset.py").write_text(DATASET)
    (repo / "r1/c3/features.py").write_text(FEATURES.format(version="c3_features/v2", formula="1 - (b - 1) / total"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v2 featurizer (the sealed table's builder)")
    v2 = _git(repo, "rev-parse", "HEAD")
    (repo / "r1/c3/features.py").write_text(FEATURES.format(version="c3_features/v3", formula="1 - used / total"))
    _git(repo, "commit", "-q", "-am", "v3 featurizer (W2, main)")
    v3 = _git(repo, "rev-parse", "HEAD")
    roots = {}
    for name in ("ceph", "work"):                       # the audit's paper root and the release's
        root = tmp_path / name / "paper"
        (root / "results/r1/evidence").mkdir(parents=True)
        (root / INDEX_REL).write_text(json.dumps(INDEX))
        (root / CLASSIFICATION_REL).write_text('{"schema": "r1.c3_classification/1"}\n')
        roots[name] = root
    harness = tmp_path / "harness"
    (harness / "src").mkdir(parents=True)
    (harness / "src" / "fakeharness.py").write_text("VALUE = 1\n")
    monkeypatch.setenv("AR_HARNESS_ROOT", str(harness))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(audit, "_local_scratch_mount", lambda parent: ["ext4", "/dev/test"])
    guarded = []
    monkeypatch.setattr(analysis_guard, "guard_table", lambda *a: guarded.append(a))
    # the sealed table: built by the v2 builder at the /ceph-like root
    with C.tempfile.TemporaryDirectory() as t:
        src = C._builder_checkout(Path(t) / "src", repo=repo, commit=v2)
        table = tmp_path / "sealed_table"
        C._run_builder(src, [INDEX_REL, str(table), str(roots["ceph"]), str(roots["ceph"] / CLASSIFICATION_REL)],
                       "c3_features/v2", harness_root=harness)
    return {"repo": repo, "v2": v2, "v3": v3, "roots": roots, "table": table, "guarded": guarded, "tmp": tmp_path,
            "harness": harness}


def _compat(w, *, root="work", classification=None, table=None, **kw):
    root = w["roots"][root]
    kw = {"repo": w["repo"], "commit": w["v2"], "featurizer": "c3_features/v2", **kw}
    return C._sweep1_compat_replay(table or w["table"], root, Path(INDEX_REL),
                                   classification or root / CLASSIFICATION_REL, **kw)


def _builder_as_main(w, commit, monkeypatch):
    """main's ``r1.c3.dataset.build_from_sweep`` replaced by the synthetic builder at ``commit`` (for the unfixed path)."""
    import r1.c3.dataset as main_dataset

    def build(index, out, *, paper_root=None, classification=None):
        with C.tempfile.TemporaryDirectory() as t:
            src = C._builder_checkout(Path(t) / "src", repo=w["repo"], commit=commit)
            version = "c3_features/v2" if commit == w["v2"] else "c3_features/v3"
            C._run_builder(src, [str(index), str(out), str(paper_root), str(classification)], version,
                           harness_root=w["harness"])
    monkeypatch.setattr(main_dataset, "build_from_sweep", build)


def test_the_sealed_table_is_v2_and_differs_from_v3_on_skips(world):
    rows = [json.loads(x) for x in (world["table"] / "proposals.jsonl").read_text().splitlines()]
    assert [r["features"]["budget_frac_left"] for r in rows] == [1.0, 0.9, 0.75, 0.6]      # v2: 1 - (b-1)/total
    meta = json.loads((world["table"] / "build.json").read_text())
    assert meta["commit"] == world["v2"] and meta["classification"]["path"].startswith(str(world["roots"]["ceph"]))


def test_the_refusal_reproduces_without_the_fix(world, monkeypatch):
    """The unchanged ``audit._verify_replay``: main's v3 builder refuses on proposals; even the v2 builder refuses on
    build.json, because the sealed classification path is the audit's root (the two gates of the diagnosis)."""
    root, cls = world["roots"]["work"], world["roots"]["work"] / CLASSIFICATION_REL
    _builder_as_main(world, world["v3"], monkeypatch)
    with pytest.raises(ValueError, match="evidence table differs from full source replay: proposals.jsonl"):
        audit._verify_replay(world["table"], root, Path(INDEX_REL), cls)
    _builder_as_main(world, world["v2"], monkeypatch)
    with pytest.raises(ValueError, match="evidence build metadata differs from full source replay"):
        audit._verify_replay(world["table"], root, Path(INDEX_REL), cls)


def test_the_fix_accepts_the_real_metadata_pattern(world, monkeypatch):
    """v2 table, v3 main, replay at another paper root: the compatibility replay passes, without main's builder."""
    import r1.c3.dataset as main_dataset
    monkeypatch.setattr(main_dataset, "build_from_sweep",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("main's builder must not be used")))
    assert _compat(world) is None
    assert world["guarded"] and world["guarded"][0][0] == world["table"]          # the table guard still runs
    assert _compat(world, root="ceph") is None                                      # and at the audit's own root


def test_tampered_proposals_configs_or_classification_are_refused(world, tmp_path):
    import shutil
    def copy():
        t = tmp_path / f"t{len(list(tmp_path.glob('t*')))}"
        shutil.copytree(world["table"], t)
        return t
    t = copy()
    p = t / "proposals.jsonl"
    p.write_text(p.read_text().replace("0.75", "0.8"))
    with pytest.raises(ValueError, match="differs from full source replay: proposals.jsonl"):
        _compat(world, table=t)
    t = copy()
    (t / "configs.json").write_text(json.dumps({"c1": {"lr": 0.2}}, sort_keys=True))
    with pytest.raises(ValueError, match="differs from full source replay: configs.json"):
        _compat(world, table=t)
    cls = world["roots"]["work"] / CLASSIFICATION_REL                # other classification bytes at the release root
    cls.write_text('{"schema": "r1.c3_classification/1", "x": 1}\n')
    with pytest.raises(ValueError, match="classification bytes"):
        _compat(world)
    cls.write_text('{"schema": "r1.c3_classification/1"}\n')
    other = world["roots"]["work"] / "results/r1/evidence/elsewhere.json"   # same bytes, another repository path
    other.write_text(cls.read_text())
    with pytest.raises(ValueError, match="classification path"):
        _compat(world, classification=other)
    outside = tmp_path / "outside.json"
    outside.write_text(cls.read_text())
    with pytest.raises(ValueError, match="outside the paper root"):
        _compat(world, classification=outside)


def test_other_build_metadata_and_the_pin_are_still_checked(world, tmp_path):
    import shutil
    t = tmp_path / "meta"
    shutil.copytree(world["table"], t)
    meta = json.loads((t / "build.json").read_text())
    meta["replay_checks"] = 99
    (t / "build.json").write_text(json.dumps(meta, indent=1))
    with pytest.raises(ValueError, match="evidence build metadata differs from full source replay$"):
        _compat(world, table=t)
    meta["replay_checks"], meta["commit"] = 4, world["v3"]                    # a table not built at the pinned commit
    (t / "build.json").write_text(json.dumps(meta, indent=1))
    with pytest.raises(ValueError, match="applies only to the sealed sweep-1 table"):
        _compat(world, table=t)
    v3src = C._builder_checkout(tmp_path / "v3src", repo=world["repo"], commit=world["v3"])
    with pytest.raises(RuntimeError, match="featurizer c3_features/v3 is not c3_features/v2"):
        C._run_builder(v3src, ["--probe"], "c3_features/v2")         # a builder of another featurizer is refused
    with pytest.raises(ValueError, match="needs the classification sidecar"):
        C._sweep1_compat_replay(world["table"], world["roots"]["work"], Path(INDEX_REL), None, repo=world["repo"],
                                commit=world["v2"], featurizer="c3_features/v2")


def test_normalize_provenance_only_touches_the_classification_path():
    assert C.SWEEP1_CLASSIFICATION_REL == CLASSIFICATION_REL
    sealed = {"commit": "a", "classification": {"path": "/ceph/x/paper/" + CLASSIFICATION_REL, "sha256": "s", "n": 1},
              "sweep_index": {"path": "results/i.json"}}
    rebuilt = {"commit": "b", "classification": {"path": "/work/y/paper/" + CLASSIFICATION_REL, "sha256": "s", "n": 1},
               "sweep_index": {"path": "results/i.json"}}
    new, old = C.normalize_provenance(rebuilt, sealed, Path("/work/y/paper"))
    assert new == old and new["classification"]["path"] == "<paper_root>/" + CLASSIFICATION_REL and "commit" not in new
    assert sealed["classification"]["path"].startswith("/ceph")                     # the inputs are not modified
    with pytest.raises(ValueError, match="classification record"):
        C.normalize_provenance({**rebuilt, "classification": {**rebuilt["classification"], "extra": 1}}, sealed,
                               Path("/work/y/paper"))
    for path in (CLASSIFICATION_REL, "/ceph/x/paper/results/r1/C3_sweep_classification_20261028.json"):
        with pytest.raises(ValueError, match="classification path"):            # relative, or another sealed path
            C.normalize_provenance(rebuilt, {**sealed, "classification": {**sealed["classification"], "path": path}},
                                   Path("/work/y/paper"))
    other = {**rebuilt, "classification": {**rebuilt["classification"], "path": "/work/y/paper/results/c.json"}}
    with pytest.raises(ValueError, match="classification path"):                # not the R1-SWEEP1-CLASSIFY sidecar
        C.normalize_provenance(other, {**sealed, "classification": {**sealed["classification"],
                                                                    "path": "/ceph/x/paper/results/c.json"}},
                               Path("/work/y/paper"))


def test_sweep1_integrity_installs_the_replay_only_for_its_check(monkeypatch, tmp_path):
    """sweep1_integrity runs verify_evidence_completion with the compatibility replay and restores
    audit._verify_replay afterwards, also on failure; sweep2_integrity is unchanged and uses the original replay."""
    original = audit._verify_replay
    seen = []
    monkeypatch.setattr(C, "_sweep1_compat_replay", lambda *a, **k: seen.append(a))

    def fake_verify(table, label_block, paper_root, index, classification, source="sweep1"):
        audit._verify_replay(table, paper_root, index, classification)
        if source == "sweep2":
            assert audit._verify_replay is original
        return {"schema": audit.SWEEP2_COMPLETION_SCHEMA if source == "sweep2" else "x", "source": source}
    monkeypatch.setattr(audit, "verify_evidence_completion", fake_verify)
    (tmp_path / "audit").mkdir()
    (tmp_path / "audit" / "evidence_completion.json").write_text("{}")
    out = C.sweep1_integrity(tmp_path / "table", tmp_path / "audit", paper_root=tmp_path, index=Path("i.json"),
                             classification=tmp_path / "c.json")
    assert out["pass"] and "ab79b4ce" in out["check"] and len(seen) == 1
    assert audit._verify_replay is original

    def failing(*a, **k):
        raise ValueError("boom")
    monkeypatch.setattr(C, "_sweep1_compat_replay", failing)
    with pytest.raises(ValueError, match="boom"):
        C.sweep1_integrity(tmp_path / "table", tmp_path / "audit", paper_root=tmp_path, index=Path("i.json"),
                           classification=tmp_path / "c.json")
    assert audit._verify_replay is original
    monkeypatch.setattr(audit, "_verify_replay", lambda *a: seen.append(("sweep2",) + a))
    monkeypatch.setattr(C, "_sweep2_batch_published", lambda: None)
    original = audit._verify_replay
    assert C.sweep2_integrity(tmp_path / "table", tmp_path / "audit", paper_root=tmp_path, index=Path("i.json"))["pass"]
    assert seen[-1][0] == "sweep2" and C.INTEGRITY_CHECKS["sweep2"] is C.sweep2_integrity


def _pycache(root):
    """Every bytecode file under ``root`` with its size and mtime (new or rewritten .pyc files show)."""
    return {str(p): (p.stat().st_size, p.stat().st_mtime_ns) for p in Path(root).rglob("*.pyc")}


def test_the_child_gets_the_harness_explicitly_and_writes_no_bytecode(world, tmp_path, monkeypatch):
    """The builder's child gets AR_HARNESS_ROOT from the parent's resolution (not by inheritance), runs with -B, and a
    replay leaves no bytecode in the harness or the builder checkout; without a harness the replay stops early with
    RuntimeError, before any build."""
    src = C._builder_checkout(tmp_path / "probe_src", repo=world["repo"], commit=world["v2"])
    monkeypatch.setenv("AR_HARNESS_ROOT", "/somewhere/else")
    out = C._run_builder(src, ["--probe"], "c3_features/v2", harness_root=world["harness"])
    assert out["harness_root"] == str(world["harness"]) and out["dont_write_bytecode"] is True
    assert C._run_builder(src, ["--probe"], "c3_features/v2")["harness_root"] is None     # nothing inherited
    monkeypatch.setenv("AR_HARNESS_ROOT", str(world["harness"]))
    seen = []
    real = C._run_builder
    monkeypatch.setattr(C, "_run_builder", lambda *a, **k: seen.append(k) or real(*a, **k))
    assert _compat(world) is None
    assert [k["harness_root"] for k in seen] == [world["harness"].resolve()]
    assert _pycache(world["harness"]) == {} and _pycache(src) == {}
    import r1.harness
    monkeypatch.delenv("AR_HARNESS_ROOT")
    monkeypatch.setattr(r1.harness, "REPO", tmp_path / "nowhere" / "repo")           # no sibling harness either
    seen.clear()
    with pytest.raises(RuntimeError, match="harness src not found"):
        _compat(world)
    assert seen == []
    monkeypatch.setenv("AR_HARNESS_ROOT", str(world["harness"]))
    with pytest.raises(RuntimeError, match="failed in the table's builder: RuntimeError: harness src not found"):
        C._run_builder(src, [INDEX_REL, str(tmp_path / "t"), str(world["roots"]["work"]),
                             str(world["roots"]["work"] / CLASSIFICATION_REL)], "c3_features/v2")   # no root passed


def test_a_source_data_refusal_inside_the_builder_stays_a_value_error(world, tmp_path):
    """The builder's own source-data checks raise ValueError; the child exits with code 3 and the parent raises
    ValueError (an identity failure), not RuntimeError (environment)."""
    src = C._builder_checkout(tmp_path / "src3", repo=world["repo"], commit=world["v2"])
    root = world["roots"]["work"]
    (root / "results/r1/evidence/moved_index.json").write_text(json.dumps({**INDEX, "moved": True}))
    with pytest.raises(ValueError, match="builder refused the source data: ValueError: moved sweep differs"):
        C._run_builder(src, ["results/r1/evidence/moved_index.json", str(tmp_path / "t3"), str(root),
                             str(root / CLASSIFICATION_REL)], "c3_features/v2", harness_root=world["harness"])


def test_the_scratch_check_counts_the_builder_checkout(world, monkeypatch):
    size = C.checkout_bytes(repo=world["repo"], commit=world["v2"])
    assert size == sum(len((world["repo"] / p).read_bytes()) for p in ("r1/__init__.py", "r1/c3/__init__.py",
                                                                         "r1/c3/dataset.py")) + len(
        FEATURES.format(version="c3_features/v2", formula="1 - (b - 1) / total").encode())
    table = sum((world["table"] / n).stat().st_size for n in ("proposals.jsonl", "configs.json"))
    Usage = type("Usage", (), {})
    for free, ok in ((2 * table + size - 1, False), (2 * table + size, True)):
        u = Usage()
        u.free = free
        monkeypatch.setattr(C.shutil, "disk_usage", lambda p, u=u: u)
        if ok:
            assert _compat(world) is None
        else:
            with pytest.raises(ValueError, match="local scratch capacity insufficient"):
                _compat(world)
    with pytest.raises(RuntimeError, match="not in the release checkout"):
        C.checkout_bytes(repo=world["repo"], commit="0" * 40)


def test_the_real_pin_imports_the_v2_builder_in_isolation():
    """In this repository, commit ab79b4ce's builder imports in the isolated interpreter: featurizer v2, its own git
    head, and every r1 module from the throwaway checkout (none from this checkout's v3 builder)."""
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", C.SWEEP1_TABLE_COMMIT + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("commit ab79b4ce is not in this repository")
    out = C.probe_builder()
    assert out["featurizer"] == "c3_features/v2" and out["git_head"] == C.SWEEP1_TABLE_COMMIT
    assert {"r1.c3.dataset", "r1.c3.features"} <= set(out["r1_modules"]) and out["dont_write_bytecode"] is True


def test_the_real_pin_imports_its_harness_module_with_the_resolved_root():
    """With a harness available here, ab79b4ce's ``r1.headroom.e1b_collect`` (what its sweep sources import for the
    noise source) imports in the child with the parent's harness root, and writes no bytecode into the harness."""
    if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", C.SWEEP1_TABLE_COMMIT + "^{commit}"],
                      capture_output=True).returncode:
        pytest.skip("commit ab79b4ce is not in this repository")
    try:
        root = C.child_harness_root()
    except RuntimeError:
        pytest.skip("no harness checkout available (AR_HARNESS_ROOT)")
    before = _pycache(root / "src")
    out = C.probe_builder(harness_root=root)
    assert "r1.headroom.e1b_collect" in out["r1_modules"] and out["harness_root"] == str(root)
    assert out["dont_write_bytecode"] is True and _pycache(root / "src") == before
