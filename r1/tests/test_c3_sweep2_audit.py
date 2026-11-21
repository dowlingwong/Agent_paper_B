"""The sweep-2 batch (``r1.c3.sweep2_batch``), the sweep-2 audit profile of ``r1.c3.audit`` and the sweep-2 integrity
check: synthetic sealed chunks only (one node, two instances, both memory modes); no label, audit or evaluation file
of a real sweep is opened. AI-assisted (Claude)."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from r1.c3 import audit, dataset as D, features as F, release_checks, sweep2_batch as SB
from r1.harness import REPO

NODE = "digits_mlp"
SEEDS = (104, 114)
START = {"train.py": "HIDDEN_UNITS = 32\nALPHA = 1e-4\nMAX_ITER = 40\n"}
VALUES = {"HIDDEN_UNITS": ["16", "32", "64", "128"], "ALPHA": ["1e-5", "1e-4", "1e-3", "1e-2"],
          "MAX_ITER": ["20", "40", "80", "160"]}


@pytest.fixture(autouse=True)
def _control_plane_skip(monkeypatch):
    try:
        F._is_control_plane_skip({"decision": "kept", "extra": {}})
    except ImportError:
        def stand_in(row):
            c = (row.get("extra") or {}).get("control") or {}
            return row.get("decision") == "skipped" and c.get("action") == "skip" and c.get("reason") != "inactive_key"
        monkeypatch.setattr(F, "_is_control_plane_skip", stand_in)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _metric(cfg: dict) -> float:
    h = int(hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:8], 16)
    return round(0.85 + (h % 1000) / 10000.0, 4)


def _ledger(inst: str, n: int = 10) -> list[dict]:
    rng = np.random.default_rng(int(inst.rsplit("__s", 1)[1]))
    inc = {"HIDDEN_UNITS": "32", "ALPHA": "1e-4", "MAX_ITER": "40"}
    best, rows = None, []
    for b in range(1, n + 1):
        key = list(VALUES)[int(rng.integers(3))]
        new = inc[key] if b == 4 else str(rng.choice([v for v in VALUES[key] if v != inc[key]]))
        cand = {**inc, key: new}
        m = _metric(cand)
        kept = best is None or m > best
        rows.append({"budget_index": b, "decision": "kept" if kept else "discarded",
                     "parsed_metrics": {"val_score": m}, "current_best_before": best,
                     "delta_vs_best": None if best is None else m - best,
                     "extra": {"manager": {"structured_edit": {"symbol": key, "old": inc[key], "new": new,
                                                               "path": "train.py"}}}})
        if kept:
            inc, best = cand, m
    return rows


@pytest.fixture()
def world(tmp_path, monkeypatch):
    """A paper root (pinned noise summary and sweep-2 authorization copied from the repository) and a synthetic
    sealed run directory in the sweep-2 seal layout."""
    monkeypatch.setattr(SB, "NODES", [NODE])
    monkeypatch.setattr(SB, "INSTANCES", len(SEEDS))
    paper = tmp_path / "paper"
    for rel in (SB.NOISE_SOURCE["path"], SB.AUTHORIZATION["path"]):
        (paper / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, paper / rel)
    sealed = tmp_path / "sealed" / SB.RUN_ID
    from r1.headroom.e1b_collect import node_noise
    noise = node_noise(paper / SB.NOISE_SOURCE["path"], NODE)
    records = {}
    for k, (chunk, node, mode) in enumerate(SB.chunks()):
        c = sealed / chunk
        files = {"job_record.json": json.dumps({
            "schema": "s2_c2_job_record/1", "run_id": SB.RUN_ID, "chunk_id": chunk, "label": "EVIDENCE",
            "paper_commit": SB.PAPER_COMMIT, "image_digest": SB.IMAGE, "harness_commit": SB.HARNESS_COMMIT,
            "b2_audits": "none (no B.2 audits; audit seeds 7001-7010 untouched)",
            "finished_utc": f"2026-11-21T0{k}:00:00Z", "cpu": {"model": "X"}, "site": {"fqdn": "g4401"}})}
        manifest = {"schema": "r1.e1b_headroom/1", "label": "EVIDENCE", "split": "c3_labels",
                    "started_utc": f"2026112{k}", "harness": {"root": f"/srv/{chunk}/harness", "commit": SB.HARNESS_COMMIT},
                    "manager_backend": "llamacpp", "manager": {"kind": "langgraph", "proposal_schema": "manager_proposal/v1"},
                    "memory_mode": mode, "arm": None, "arm_role": SB.MODES[mode], "seed_policy": "d26",
                    "nodes": [node], "instances": len(SEEDS), "runs": 20, "points": 0, "reps": 0, "audit_seeds": 0,
                    "verify_r": 3, "verify_split_policy": "vary",
                    "noise": {node: {**noise, "source": f"/srv/{chunk}/paper/{SB.NOISE_SOURCE['path']}"}},
                    "host": {"platform": chunk}, "work": f"/srv/{chunk}/work", "sessions": [{"chunk": chunk}],
                    "roots_only": True, "root_failures": "record",
                    "c3_label_sweep": {"schema": "r1.c3_label_sweep/1", "memory_mode": mode,
                                       "arm_role": SB.MODES[mode], "label": "EVIDENCE", "s2_c2": True,
                                       "backend": "llamacpp", "noise_source": dict(SB.NOISE_SOURCE),
                                       "audit": "none", "b2_audits": "none"}}
        files["out/manifest.json"] = json.dumps(manifest)
        for s in SEEDS:
            inst = f"{node}__s{s}"
            files[f"out/roots/{inst}.json"] = json.dumps({"start_files": START})
            files[f"work/roots/{inst}/root_trials.jsonl"] = "".join(json.dumps(r) + "\n" for r in _ledger(inst))
            files[f"work/roots/{inst}/root_events.jsonl"] = "{}\n"
        for rel, text in files.items():
            (c / rel).parent.mkdir(parents=True, exist_ok=True)
            (c / rel).write_text(text)
        (c / "SHA256SUMS").write_text("".join(f"{_sha((c / rel).read_bytes())}  {rel}\n" for rel in sorted(files)))
        (c / "SEAL_RECEIPT.json").write_text(json.dumps({"chunk_id": chunk}))
        records[chunk] = _sha((c / "job_record.json").read_bytes())
    counts = {"run_id": SB.RUN_ID, "paper_commit": SB.PAPER_COMMIT, "chunks": len(SB.chunks()),
              "chunk_record_sha256": records}
    (sealed / "collection_counts.json").write_text(json.dumps(counts))
    monkeypatch.setattr(SB, "COLLECTION_COUNTS_SHA256", _sha((sealed / "collection_counts.json").read_bytes()))
    return {"paper": paper, "sealed": sealed, "tmp": tmp_path}


def _reseal(chunk_dir: Path) -> None:
    rels = [line.split("  ", 1)[1] for line in (chunk_dir / "SHA256SUMS").read_text().splitlines() if line.strip()]
    (chunk_dir / "SHA256SUMS").write_text("".join(f"{_sha((chunk_dir / r).read_bytes())}  {r}\n" for r in rels))


def test_extract_verify_build_and_plan(world):
    out = SB.extract(world["sealed"], world["paper"])
    index = Path(out["index"])
    assert index.parent == SB.batch_dir(world["paper"]) and index.name == SB.index_name()
    v = SB.verify(index, world["paper"])
    assert v["index_sha256"] == out["index_sha256"] and v["files"] == out["files"]
    data = json.loads(index.read_text())
    assert data["label"] == "EVIDENCE" and data["nodes"] == [NODE] and data["sweep2"]["run_id"] == SB.RUN_ID
    assert [s["memory_mode"] for s in data["sweeps"]] == list(SB.MODES)
    m = json.loads((SB.batch_dir(world["paper"]) / "sweeps/none/manifest.json").read_text())
    assert m["noise"][NODE]["source"] == SB.NOISE_SOURCE["path"] and m["noise"][NODE]["source_at_collection"]
    # the existing table builder reads the batch through the index (no classification sidecar)
    table = world["tmp"] / "table"
    meta = D.build_from_sweep(index, table, paper_root=world["paper"])
    assert meta["label"] == "EVIDENCE" and "classification" not in meta and meta["table_sha256"]
    assert meta["replay_checks_total"]["zero_delta_violations"] == 0
    c = SB.counts(table)
    assert c["proposals"] == meta["n_proposals"] == c["eligible"] + c["duplicates"] + c["noops"]
    assert c["noops"] == 2 * len(SEEDS) and c["seed_runs"] == 10 * c["unique_configs"]
    # the audit's sweep-2 plan: batch re-verified, table equal to a full replay, same partition as sweep 1
    plan, binding = audit.evidence_plan(table, world["paper"], index, None, "sweep2")
    assert binding["source"] == "sweep2" and binding["extract_sha256"] == v["extract_sha256"]
    assert binding["counts"] == {"noops": c["noops"], "duplicates": c["duplicates"], "eligible": c["eligible"]}
    assert len(plan) == c["eligible"] and "classification_sha256" not in binding
    with pytest.raises(ValueError, match="no classification sidecar"):
        audit.evidence_plan(table, world["paper"], index, index, "sweep2")
    # a table not built from this index, or altered, is refused
    meta2 = json.loads((table / "build.json").read_text())
    meta2["sweep_index"]["sha256"] = "0" * 64
    (table / "build.json").write_text(json.dumps(meta2))
    with pytest.raises(ValueError, match="not the sweep-2 EVIDENCE table"):
        audit.evidence_plan(table, world["paper"], index, None, "sweep2")


@pytest.mark.parametrize("case,match", [
    ("ledger_byte", "differs from its sealed SHA256SUMS"),
    ("record_not_counted", "not the one the collection counted"),
    ("record_pins", "job record pins differ"),
    ("audit_seeds", "collector manifest fails"),
    ("noise_value", "noise constants differ"),
    ("root_failure", "root failures"),
    ("missing_campaign", "root ledgers"),
    ("unlisted", "not in its SHA256SUMS"),
    ("counts_file", "not the published, pinned file"),
])
def test_extract_refusals(world, monkeypatch, case, match):
    sealed = world["sealed"]
    chunk = sealed / f"{NODE}-none"
    if case == "ledger_byte":
        p = chunk / f"work/roots/{NODE}__s104/root_trials.jsonl"
        p.write_text(p.read_text().replace('"kept"', '"Kept"', 1))
    elif case in ("record_not_counted", "record_pins"):
        rec = json.loads((chunk / "job_record.json").read_text())
        rec["paper_commit" if case == "record_pins" else "started_utc"] = "x"
        (chunk / "job_record.json").write_text(json.dumps(rec))
        _reseal(chunk)
        if case == "record_pins":      # recount it, so that only the pin check refuses
            counts = json.loads((sealed / "collection_counts.json").read_text())
            counts["chunk_record_sha256"][chunk.name] = _sha((chunk / "job_record.json").read_bytes())
            (sealed / "collection_counts.json").write_text(json.dumps(counts))
            monkeypatch.setattr(SB, "COLLECTION_COUNTS_SHA256", _sha((sealed / "collection_counts.json").read_bytes()))
    elif case in ("audit_seeds", "noise_value"):
        m = json.loads((chunk / "out/manifest.json").read_text())
        if case == "audit_seeds":
            m["audit_seeds"] = 10
        else:
            m["noise"][NODE]["sigma_t"] = 9.0
        (chunk / "out/manifest.json").write_text(json.dumps(m))
        _reseal(chunk)
    elif case == "root_failure":
        (chunk / "out/failures").mkdir()
        (chunk / "out/failures/x.json").write_text("{}")
    elif case == "missing_campaign":
        lines = [x for x in (chunk / "SHA256SUMS").read_text().splitlines() if "__s114" not in x]
        (chunk / "SHA256SUMS").write_text("\n".join(lines) + "\n")
        for p in (chunk / f"work/roots/{NODE}__s114").iterdir():
            p.rename(world["tmp"] / f"moved_{p.name}")
        (chunk / f"work/roots/{NODE}__s114").rmdir()
        (chunk / f"out/roots/{NODE}__s114.json").rename(world["tmp"] / "moved_root.json")
    elif case == "unlisted":
        lines = [x for x in (chunk / "SHA256SUMS").read_text().splitlines() if "out/roots" not in x]
        (chunk / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    elif case == "counts_file":
        monkeypatch.setattr(SB, "COLLECTION_COUNTS_SHA256", "0" * 64)
    with pytest.raises(SB.BatchError, match=match):
        SB.extract(sealed, world["paper"])
    assert not SB.batch_dir(world["paper"]).exists()


def test_mode_manifest_needs_equal_chunks(world, monkeypatch):
    """The eight chunk manifests of a mode must agree on every common field; the nodes and noise are merged."""
    monkeypatch.setattr(SB, "NODES", [NODE, "tabular_mlp"])
    from r1.headroom.e1b_collect import node_noise
    pinned = world["paper"] / SB.NOISE_SOURCE["path"]
    base = json.loads((world["sealed"] / f"{NODE}-none/out/manifest.json").read_text())
    other = json.loads(json.dumps(base))
    other["nodes"] = ["tabular_mlp"]
    other["noise"] = {"tabular_mlp": {**node_noise(pinned, "tabular_mlp"), "source": "/x/" + SB.NOISE_SOURCE["path"]}}
    merged = SB.mode_manifest({f"{NODE}-none": base, "tabular_mlp-none": other}, "none", pinned)
    assert merged["nodes"] == [NODE, "tabular_mlp"] and set(merged["noise"]) == {NODE, "tabular_mlp"}
    other["verify_split_policy"] = "fixed"
    with pytest.raises(SB.BatchError, match="differs from the other chunks"):
        SB.mode_manifest({f"{NODE}-none": base, "tabular_mlp-none": other}, "none", pinned)
    with pytest.raises(SB.BatchError, match="chunk manifests"):
        SB.mode_manifest({f"{NODE}-none": base}, "none", pinned)


def test_extract_never_overwrites_and_verify_catches_tampering(world):
    SB.extract(world["sealed"], world["paper"])
    with pytest.raises(SB.BatchError, match="written once"):
        SB.extract(world["sealed"], world["paper"])
    batch = SB.batch_dir(world["paper"])
    index = batch / SB.index_name()
    ledger = batch / f"sweeps/none/ledgers/{NODE}__s104/root_trials.jsonl"
    original = ledger.read_bytes()
    ledger.write_bytes(original.replace(b'"kept"', b'"Kept"', 1))
    with pytest.raises(SB.BatchError, match="differs from EXTRACT.json"):
        SB.verify(index, world["paper"])
    ledger.write_bytes(original)
    (batch / "sweeps/none/ledgers/extra.txt").write_text("x")
    with pytest.raises(SB.BatchError, match="batch files differ from EXTRACT.json"):
        SB.verify(index, world["paper"])
    (batch / "sweeps/none/ledgers/extra.txt").rename(world["tmp"] / "extra.txt")
    # a mode manifest edited together with its EXTRACT entry and the index binding is still caught (re-derived)
    mpath = batch / "sweeps/none/manifest.json"
    m = json.loads(mpath.read_text())
    m["runs"] = 21
    mpath.write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")
    ex = json.loads((batch / "EXTRACT.json").read_text())
    ex["files"]["sweeps/none/manifest.json"]["sha256"] = _sha(mpath.read_bytes())
    (batch / "EXTRACT.json").write_text(json.dumps(ex, indent=1, sort_keys=True) + "\n")
    idx = json.loads(index.read_text())
    idx["sweep2"]["extract"]["sha256"] = _sha((batch / "EXTRACT.json").read_bytes())
    index.write_text(json.dumps(idx, indent=1, sort_keys=True) + "\n")
    with pytest.raises(SB.BatchError, match="not the derived mode manifest"):
        SB.verify(index, world["paper"])
    with pytest.raises(SB.BatchError, match="not the sweep-2 index"):
        SB.verify(world["tmp"] / "elsewhere.json", world["paper"])


def test_sweep2_addendum_and_start_row(monkeypatch, tmp_path):
    commit = "c" * 40
    good = (f"# Addendum\nR1-SWEEP2-B2-GO; run {SB.RUN_ID}; code {commit}; harness {audit.AUDIT_HARNESS}; K = 10\n")
    row = f"| R1-SWEEP2-B2-GO | sweep-2 B.2 {SB.RUN_ID}: B6 (a), B4 (a), B1 (a) as for sweep 1 |\n"
    published = {"docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md": good.encode(),
                 "docs/r1/PLAN.md": row.encode()}
    monkeypatch.setattr(audit, "_published_bytes", lambda root, rel: published[rel])
    rel = Path("docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md")
    out = audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    assert out == {"path": str(rel), "sha256": _sha(good.encode())}
    with pytest.raises(ValueError, match="c3_sweep2_b2_addendum_"):
        audit.b2_addendum(tmp_path, Path("docs/r1/authorizations/c3_b2_addendum_20261122.md"), commit, "sweep2")
    with pytest.raises(ValueError, match="c3_b2_addendum_"):        # and the sweep-1 profile refuses a sweep-2 file
        audit.b2_addendum(tmp_path, rel, commit, "sweep1")
    for text, match in ((good.replace(SB.RUN_ID, "s2ev-x"), "run id"),
                        (good.replace("R1-SWEEP2-B2-GO", "R1-B2-GO"), "R1-SWEEP2-B2-GO"),
                        (good.replace("K = 10", "K = 6"), "K = 10")):
        published[str(rel)] = text.encode()
        with pytest.raises(ValueError, match=match):
            audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    published[str(rel)] = good.encode()
    published["docs/r1/PLAN.md"] = row.replace("B4 (a), ", "").encode()
    with pytest.raises(ValueError, match="start row"):
        audit.b2_addendum(tmp_path, rel, commit, "sweep2")
    with pytest.raises(ValueError, match="unknown audit source"):
        audit.b2_addendum(tmp_path, rel, commit, "sweep3")


def _git(repo, *args):
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
           "PATH": "/usr/bin:/bin"}
    res = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert res.returncode == 0, res.stderr
    return res.stdout.strip()


def test_harness_equivalence(monkeypatch, tmp_path):
    h = tmp_path / "harness"
    h.mkdir()
    _git(h, "init", "-q")
    for rel in ("nodes/digits_mlp/train.py", "src/autoresearch/worker/w.py", "src/autoresearch/llm/x.py"):
        (h / rel).parent.mkdir(parents=True, exist_ok=True)
        (h / rel).write_text("a\n")
    _git(h, "add", "-A")
    _git(h, "commit", "-q", "-m", "audit pin")
    a = _git(h, "rev-parse", "HEAD")
    (h / "src/autoresearch/llm/x.py").write_text("b\n")            # outside the audited paths: allowed
    _git(h, "commit", "-q", "-am", "sweep-2 pin")
    b = _git(h, "rev-parse", "HEAD")
    monkeypatch.setattr(audit, "AUDIT_HARNESS", a)
    monkeypatch.setattr(SB, "HARNESS_COMMIT", b)
    out = audit.sweep2_harness_equivalence(h)
    assert out["diff"] == "empty" and out["sweep2_harness"] == b
    (h / "src/autoresearch/worker/w.py").write_text("c\n")
    _git(h, "commit", "-q", "-am", "worker change")
    monkeypatch.setattr(SB, "HARNESS_COMMIT", _git(h, "rev-parse", "HEAD"))
    with pytest.raises(ValueError, match="differs from"):
        audit.sweep2_harness_equivalence(h)
    monkeypatch.setattr(SB, "HARNESS_COMMIT", "f" * 40)
    with pytest.raises(ValueError, match="NOT CHECKABLE"):
        audit.sweep2_harness_equivalence(h)


def _completion_world(tmp_path, monkeypatch, source):
    """The synthetic evidence-run fixture of test_c3_evidence_split_blocks, for either profile."""
    monkeypatch.setattr(audit, "b2_addendum", lambda *a: {"path": "docs/r1/authorizations/x.md", "sha256": "addendum"})
    monkeypatch.setattr(audit, "sweep2_harness_equivalence", lambda h: {"diff": "empty"})
    table = tmp_path / "table"
    table.mkdir(parents=True)
    for name, data in [("build.json", "{}"), ("proposals.jsonl", "{}\n"),
                       ("configs.json", json.dumps({"c": {"files": {}}, "i": {"files": {}}}))]:
        (table / name).write_text(data)
    for rel in ("docs/r1/authorizations/c3_sweep1_20261027.md", SB.AUTHORIZATION["path"]):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(rel)
    index, classification = tmp_path / "index", tmp_path / "classification"
    index.write_text("index")
    classification.write_text("classification")
    rows = [{"proposal_id": "p", "node": "n", "noop": False, "duplicate": False, "sigma_node": 0.5}]
    monkeypatch.setattr(D, "load_table", lambda _: rows)
    plan = [{"proposal_id": "p", "node": "n", "candidate_hash": "c", "incumbent_hash": "i"}]
    env = {"worker_python": "/venv/bin/python3", "worker_prefix": "/venv",
           "worker_versions": {"scikit-learn": "1.8.0", "numpy": "2.4.4", "pandas": "3.0.3", "scipy": "1.17.1"},
           "package_list_sha256": "abc", "harness_root": "/h", "environment_basis": {},
           "harness_untracked": {"data_caches_sha256": {"n": "d"}}}
    monkeypatch.setattr(audit, "evidence_environment", lambda *a: dict(env))
    monkeypatch.setattr(audit, "harness_untracked_state", lambda *a: {"data_caches_sha256": {"n": "d"}})
    monkeypatch.setattr(audit, "evidence_paper_provenance", lambda *a: {})
    binding = {"counts": {"eligible": 1, "noops": 0, "duplicates": 0}}
    if source == "sweep2":
        binding.update(source="sweep2", extract_sha256="e" * 64)
    monkeypatch.setattr(audit, "evidence_plan", lambda *a: (plan, binding))
    monkeypatch.setattr(audit, "evidence_resources", lambda *a: {})
    monkeypatch.setattr(audit, "monitor_evidence_resources", lambda *a: {})

    class Future:
        def __init__(self, key): self.key = key
        def result(self):
            runtime = {"worker_python": env["worker_python"], "prefix": env["worker_prefix"], "base_prefix": "/s",
                       "versions": env["worker_versions"], "package_list_sha256": env["package_list_sha256"],
                       "worker_command_python": "/w/python3", "worker_python_realpath": "/s/python3"}
            return [{"seed": s, "success": True, "changed_files": False, "metric": float(s) + (self.key == "c"),
                     "wall_seconds": 1.0, "worker_runtime": runtime} for s in audit.DEFAULT_SEEDS]

    class Pool:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def submit(self, fn, node, files, seeds, scratch, stop, journal, identity): return Future(identity["config_hash"])
    monkeypatch.setattr(audit, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(audit, "wait", lambda pending, **kw: ({pending[0]}, set(pending[1:])))
    out = tmp_path / "results/r1/evidence/C3_audit_EVIDENCE_fake"
    audit.evidence_run(table, tmp_path, index, None if source == "sweep2" else classification, out, 1, 300,
                       scratch_root=tmp_path / "scratch", source=source)
    shutil.rmtree(tmp_path / "scratch")         # local fixture scratch only
    return json.loads((out / "evidence_completion.json").read_text()), out


SWEEP1_KEYS = ["schema", "label", "authorization_sha256", "b2_addendum_sha256", "classification_sha256",
               "index_sha256", "build_sha256", "proposals_sha256", "configs_sha256", "plan_sha256",
               "label_block_sha256", "evaluation_block_sha256", "runs_sha256", "environment_sha256",
               "per_run_worker_runtime", "worker_runtime_basis", "environment_basis", "resources_sha256", "counts",
               "label_seeds", "evaluation_seeds"]


def test_completion_records_by_profile(tmp_path, monkeypatch):
    c1, _ = _completion_world(tmp_path / "s1", monkeypatch, "sweep1")
    assert list(c1) == SWEEP1_KEYS and c1["schema"] == "r1.c3_audit_completion/3"     # sweep 1 unchanged
    assert c1["authorization_sha256"] == _sha(b"docs/r1/authorizations/c3_sweep1_20261027.md")
    c2, out2 = _completion_world(tmp_path / "s2", monkeypatch, "sweep2")
    assert c2["schema"] == audit.SWEEP2_COMPLETION_SCHEMA and c2["source"] == "sweep2"
    assert c2["extract_sha256"] == "e" * 64 and "classification_sha256" not in c2
    assert c2["authorization_sha256"] == _sha(SB.AUTHORIZATION["path"].encode())
    assert list(c2) == [k for k in SWEEP1_KEYS if k != "classification_sha256"][:4] + ["source", "extract_sha256"] + \
        SWEEP1_KEYS[5:]
    env = json.loads((out2 / "environment.json").read_text())
    assert env["source"] == "sweep2" and env["sweep2_harness_equivalence"] == {"diff": "empty"}
    from r1.c3 import release
    assert release.evidence_tier(out2) == "T0"            # the run log stays locked as T0


def test_sweep2_integrity_is_registered_and_wraps_the_verifier(monkeypatch, tmp_path):
    assert release_checks.INTEGRITY_CHECKS["sweep2"] is release_checks.sweep2_integrity
    assert release_checks.INTEGRITY_CHECKS["sweep1"] is release_checks.sweep1_integrity
    seen = {}

    def verify(table, block, paper_root, index, classification, source="sweep1"):
        seen.update(table=table, block=block, classification=classification, source=source)
        return {"schema": audit.SWEEP2_COMPLETION_SCHEMA, "source": "sweep2", "label_block_sha256": "l",
                "extract_sha256": "e", "index_sha256": "i", "counts": {}, "secret": "never copied"}
    monkeypatch.setattr(audit, "verify_evidence_completion", verify)
    monkeypatch.setattr(release_checks, "_sweep2_batch_published", lambda: None)
    (tmp_path / "evidence_completion.json").write_text("{}")
    out = release_checks.sweep2_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path / "i.json")
    assert seen == {"table": tmp_path, "block": tmp_path / "label_block.jsonl", "classification": None,
                    "source": "sweep2"}
    assert out["pass"] and out["completion"] == {"schema": audit.SWEEP2_COMPLETION_SCHEMA, "source": "sweep2",
                                                 "label_block_sha256": "l", "extract_sha256": "e",
                                                 "index_sha256": "i", "counts": {}}
    monkeypatch.setattr(audit, "verify_evidence_completion",
                        lambda *a, **k: {"schema": "r1.c3_audit_completion/3", "label_block_sha256": "l"})
    with pytest.raises(ValueError, match="not a sweep-2 audit completion"):
        release_checks.sweep2_integrity(tmp_path, tmp_path, paper_root=tmp_path, index=tmp_path / "i.json")


def test_sweep2_batch_must_be_the_module_beside_the_checks(monkeypatch):
    monkeypatch.setattr(SB, "__file__", "/elsewhere/sweep2_batch.py")
    with pytest.raises(ValueError, match="shadowed"):
        release_checks._sweep2_batch_published()


def test_verify_completion_refuses_a_profile_mismatch(tmp_path, monkeypatch):
    """A sweep-2 audit cannot be consumed as sweep 1, nor a sweep-1 audit as sweep 2 (environment source record)."""
    c2, out2 = _completion_world(tmp_path / "s2", monkeypatch, "sweep2")
    table, index = tmp_path / "s2/table", tmp_path / "s2/index"
    monkeypatch.setattr(audit, "require_integrity_or_test_release", lambda *a: None, raising=False)
    from r1.c3 import release
    monkeypatch.setattr(release, "require_integrity_or_test_release", lambda *a: None)
    with pytest.raises(ValueError, match="offered as sweep 1"):
        audit.verify_evidence_completion(table, out2 / "label_block.jsonl", tmp_path / "s2", index,
                                         tmp_path / "s2/classification", "sweep1")
    c1, out1 = _completion_world(tmp_path / "s1", monkeypatch, "sweep1")
    with pytest.raises(ValueError, match="sweep-2 source or harness-equivalence"):
        audit.verify_evidence_completion(tmp_path / "s1/table", out1 / "label_block.jsonl", tmp_path / "s1",
                                         tmp_path / "s1/index", None, "sweep2")
