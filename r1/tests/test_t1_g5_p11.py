"""Desk coverage of the engineering boundary. The delegated CUDA test runs on TASL."""
import json
import os
import re
import runpy
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

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
    monkeypatch.setattr(P, "paper_pin", lambda: "a" * 40)
    path = Path(P.create(RUN_ID)["spec"])
    return path, S.load_spec(path, engineering=True)


def test_disjoint_recipe_paths_and_identity(recipe):
    path, spec = recipe
    assert S.output_label(spec) == P.LABEL
    assert spec["paper_commit"] == "a" * 40
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
        from r1.c3.release import ReleaseStop, release
        with pytest.raises(ReleaseStop, match="engineering outputs"):
            release("traindev", source="g5", table_dir=directory, audit_dir=directory,
                    out_root=tmp_path / "release", integrity_args={})


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


def test_restart_transport_error_is_infrastructure_stop_12(recipe, monkeypatch):
    from urllib.error import URLError

    def offline(*args):
        raise URLError("synthetic server stopped")

    _, spec = recipe
    monkeypatch.setattr(J.T4, "server_identity", offline)
    with pytest.raises(S.Stop, match="STOP 12: after the wave"):
        J._post_wave_identity(spec, None)
    with pytest.raises(URLError):
        J._post_wave_identity({}, None)


def test_synthetic_parent_exposes_budget_step_and_keeps_scores_isolated(monkeypatch, capsys):
    result_lines = []
    channel = SimpleNamespace(write=result_lines.append, close=lambda: None)
    worker = SimpleNamespace(call=lambda *_: ({"checksum": 8}, None), close=lambda: None)
    monkeypatch.setitem(sys.modules, "ar_isolated",
                        SimpleNamespace(parent_start=lambda: channel, Worker=lambda _: worker))
    runpy.run_path(str(P.FIXTURE / "parent.py"))
    stdout = capsys.readouterr().out
    assert stdout == "step 5\n"
    node = json.loads((P.FIXTURE / "node.json").read_bytes())
    assert re.findall(node["metric"]["steps_regex"], stdout, re.MULTILINE) == [str(node["run_budget"]["value"])]
    assert result_lines == ["step 5 loss: 0.998046875", "val_accuracy: 0.001953125", "test_accuracy: 0.001953125"]


def test_close_scan_ignores_only_calling_cli_and_parent_shells(tmp_path):
    directory = tmp_path / "attempt-1"
    proc_root = tmp_path / "proc"
    caller = os.getpid()
    shell, outer_shell, supervisor, sibling, engine = range(caller + 1, caller + 6)
    for pid, parent, executable in (
        (caller, shell, "python3"), (shell, outer_shell, "bash"), (outer_shell, supervisor, "sh"),
        (supervisor, 0, "worker"), (sibling, outer_shell, "bash"), (engine, sibling, "python3"),
    ):
        entry = proc_root / str(pid)
        entry.mkdir(parents=True)
        (entry / "status").write_text(f"PPid:\t{parent}\n")
        (entry / "exe").symlink_to(f"/usr/bin/{executable}")
        (entry / "cmdline").write_bytes(f"{executable}\x00{directory}\x00".encode())
    assert S.close_scan(False)(directory, proc_root) == list(range(caller, engine + 1))
    assert P.close_processes(directory, proc_root) == [supervisor, sibling, engine]


@pytest.mark.parametrize("command", ["close-attempt", "close-server"])
def test_engineering_close_cli_selects_its_process_scan(recipe, command, monkeypatch):
    path, _ = recipe
    seen = []
    if command == "close-attempt":
        monkeypatch.setattr(J, "close_attempt", lambda *a, scan, **kw: seen.append(scan))
        extra = ["--node", P.NODES[0], "--job", "campaigns-wave1"]
    else:
        monkeypatch.setattr(J.SE, "close_server", lambda *a, scan: seen.append(scan))
        extra = []
    assert S.main([command, str(path), "/synthetic", "--reason", "synthetic interruption",
                   "--engineering", *extra]) == 0
    assert seen == [P.close_processes]
