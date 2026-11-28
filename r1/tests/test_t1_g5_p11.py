"""Desk coverage of the engineering boundary. The delegated CUDA test runs on TASL."""
import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sweep2" / "t1_tasl"))
import g5_assemble
import g5_job as J
import g5_p11 as P
import g5_tasl as S

RUN_ID = "g5-p11-20261128T120000Z"


@pytest.fixture
def recipe(tmp_path, monkeypatch):
    monkeypatch.setattr(P.Path, "home", lambda: tmp_path)
    monkeypatch.delenv(S.ENABLE_ENV, raising=False)
    path = Path(P.create(RUN_ID)["spec"])
    return path, S.load_spec(path, engineering=True)


def test_disjoint_recipe_paths_and_identity(recipe):
    path, spec = recipe
    assert S.output_label(spec) == P.LABEL
    assert {n["node"] for n in spec["nodes"]} == set(P.NODES)
    assert all(n["data_manifest_sha256"] is None for n in spec["nodes"])
    for root in (J.run_root(spec), J.SE.sealed_run(spec), J.SE.proposer_sealed_run(spec)):
        assert root.is_relative_to(P.root())
    with pytest.raises(S.Stop, match="explicit engineering"):
        S.load_spec(path)
    with pytest.raises(S.Stop, match="synthetic recipe"):
        S.load_spec(S.REPO_ROOT / P.TEMPLATE, engineering=True)
    with pytest.raises(S.Stop):
        S.validate_spec(spec, launch=True)
    with pytest.raises(S.Stop, match="P11 run id"):
        P.create("c3_t1_labels_20261128")


def test_launch_refuses_evidence_keys_and_retains_host_route(recipe, monkeypatch):
    path, _ = recipe
    monkeypatch.setattr(P, "context", lambda spec, node, host, *_: {"label": P.LABEL, "host": host, "K": 10})
    kwargs = {"job": "audits-wave1", "enable": False, "today": date(2026, 11, 28), "engineering": True,
              "host": S.AUDIT_HOST, "chunk": 1, "runner": lambda *args: args[-1]}
    out = S.launch(path, None, P.NODES[0], **kwargs)
    assert (out["label"], out["host"], out["K"], out["chunk"]) == (P.LABEL, S.AUDIT_HOST, 10, 1)
    with pytest.raises(S.Stop, match="take neither"):
        S.launch(path, Path("an-evidence-note.md"), P.NODES[0], **kwargs)
    with pytest.raises(S.Stop, match="take neither"):
        S.launch(path, None, P.NODES[0], **(kwargs | {"enable": True}))
    monkeypatch.setenv(S.ENABLE_ENV, "1")
    with pytest.raises(S.Stop, match="unset"):
        S.launch(path, None, P.NODES[0], **kwargs)


def test_rejects_extra_fields_and_symlinked_state(recipe, tmp_path):
    path, spec = recipe
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (P.root() / "runs").symlink_to(foreign, target_is_directory=True)
    with pytest.raises(S.Stop, match="symlink"):
        S.load_spec(path, engineering=True)
    raw = {"schema": P.SCHEMA, "label": P.LABEL, "run_id": RUN_ID, "worker": {"runs_root": str(foreign)}}
    with pytest.raises(S.Stop, match="exact engineering recipe"):
        P.load(path, raw)
    with pytest.raises(S.Stop, match="stage P11 transfers"):
        P.incoming(spec, foreign / "file")


def test_release_refuses_marker_even_after_copy(recipe, tmp_path):
    path, spec = recipe
    marker = Path(P.table_marker(spec)["path"])
    for directory in (marker, tmp_path / "copied"):
        if directory != marker:
            directory.mkdir()
            (directory / "build.json").write_bytes((marker / "build.json").read_bytes())
        with pytest.raises(S.Stop, match="engineering outputs"):
            g5_assemble.verify_evidence(directory, directory, test=False)


def test_synthetic_seal_has_engineering_label(recipe):
    _, spec = recipe
    run = J.run_root(spec)
    node = P.NODES[0]
    attempt = J.job_dir(spec, node, "campaigns-wave1") / "attempt-1"
    attempt.mkdir(parents=True)
    record = {"schema": J.RECORD_SCHEMA, "label": P.LABEL, "run_id": RUN_ID, "node": node,
              "job": "campaigns-wave1", "attempt": 1, "chunk": None,
              "stop": "synthetic interruption", "stop_class": "node"}
    (attempt / "job_record.json").write_text(json.dumps(record))
    receipt = J.SE.seal_attempt(spec, attempt)
    assert receipt["label"] == P.LABEL
    assert J.SE.verify_sealed(J.SE.sealed_attempt_of(spec, attempt)) == receipt
    J.SE.seal_node(spec, node)
    run_receipt = J.SE.seal_run(spec, not_run=(P.NODES[1],))
    assert run_receipt["label"] == P.LABEL and run.is_dir()
