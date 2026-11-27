import json
from pathlib import Path

import pytest

from r1.c3 import d3_gate_output as output, gate, release
from r1.c3.d3_analysis import NODES, OFFLINE_ONLINE_ARMS, offline_online_agreement


def gate_input(run="primary", *, stop=False):
    names = gate.T0_NODES if run == "wdbc_sensitivity" else NODES
    nodes = []
    for index, name in enumerate(names):
        n_test = 8 if stop or index == 0 else 9
        nodes.append({
            "node": name, "tier": "T0", "suite": None, "delta_n": 0.5,
            "train": {"instance_ids": ["train"], "oracle": [5], "A2": [2]},
            "dev": {"instance_ids": ["dev"], "oracle": [5], "A2": [2]},
            "test": {"instance_ids": [f"test{i}" for i in range(n_test)],
                     "oracle": [10] * n_test, "A2": [2] * n_test,
                     "A3": [4] * n_test, "A5": [6] * n_test},
        })
    return {"schema": gate.INPUT_SCHEMA, "split": gate.SPLIT, "t0_nodes": list(names), "nodes": nodes}


@pytest.fixture
def checkout(monkeypatch, tmp_path):
    monkeypatch.setattr(output, "REPO", tmp_path)
    record = {"t0_nodes": list(NODES), "t1": {"suites": {}}}
    row = {"gate_sha256": gate.gate_file_sha256(), "arms_frozen_sha256": "d" * 64}
    monkeypatch.setattr(output, "_release_record", lambda: (record, row))
    monkeypatch.setattr(output.analysis_guard, "require_d8_confirmation", lambda: None)
    # The fixtures provide bytes standing in for the step-6 commit in utility tests.
    monkeypatch.setattr(release, "_committed", lambda relative: (tmp_path / relative).read_bytes())
    monkeypatch.setattr(release, "_git", lambda *args: b"")
    monkeypatch.setattr(output, "load_noise", lambda _: {n: {"sigma_node": 2, "delta_n": 0.5} for n in NODES})
    return tmp_path


def stage(root: Path, run="primary", *, stop=False):
    data = json.dumps(gate_input(run, stop=stop)).encode("utf-8")
    path = root / f"{run}-staged.json"
    path.write_bytes(data)
    return path, output._sha(data)


def capture_all(root, *, primary_stop=False):
    for run in output.RUNS:
        source = stage(root, run, stop=primary_stop and run == "primary")
        if primary_stop and run == "primary":
            with pytest.raises(gate.GateStop, match="no node is IQM-eligible"):
                output.capture(run, *source)
        else:
            output.capture(run, *source)


def test_capture_retains_exact_stdout_and_excludes_a_second_launch(checkout, monkeypatch, capsys):
    staged, sha = stage(checkout)
    assert gate.main([str(staged)]) == 0
    expected = capsys.readouterr().out.encode("utf-8")
    actual_main = gate.main
    calls = []

    def record_main(args):
        calls.append(args)
        return actual_main(args)

    monkeypatch.setattr(gate, "main", record_main)
    output.capture("primary", staged, sha)
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert calls == [[str(saved / output.INPUT_NAME)]]
    assert (saved / output.REPORT_NAME).read_bytes() == expected
    assert (saved / output.MANIFEST_NAME).read_bytes() == output._manifest(
        {output.INPUT_NAME: staged.read_bytes(), output.REPORT_NAME: expected})
    assert capsys.readouterr().out == ""
    with pytest.raises(FileExistsError):
        output.capture("primary", staged, sha)
    assert len(calls) == 1


def test_utility_uses_only_primary_test_means_in_sigma_units(checkout, monkeypatch):
    capture_all(checkout)

    def forbid(*args):
        pytest.fail("utility must not run the gate, bootstrap or Holm again")

    for name in ("main", "_evaluate", "_bootstrap", "_holm_decision"):
        monkeypatch.setattr(gate, name, forbid)
    output.write_utility()
    path = checkout / output.UTILITY_PATH
    artifact = json.loads(path.read_bytes())
    utility = artifact[output.UTILITY_KEY]
    assert utility == {arm: dict.fromkeys(NODES, idx) for idx, arm in enumerate(OFFLINE_ONLINE_ARMS, start=1)}
    # The first node was below the test floor and its descriptive point still belongs in the table.
    assert offline_online_agreement(utility, utility)["mean_kendall_tau"] == 1.0
    assert artifact["unit"] == "sigma_node"
    assert artifact["gate_statistical_stop"] is False
    assert (path.parent / output.MANIFEST_NAME).read_bytes() == output._manifest({path.name: path.read_bytes()})
    with pytest.raises(FileExistsError):
        output.write_utility()


def test_statistical_stop_carries_point_rows_without_a_verdict(checkout):
    capture_all(checkout, primary_stop=True)
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert (saved / output.REPORT_NAME).read_bytes() == b""
    assert b"no node is IQM-eligible" in (saved / output.STOP_NAME).read_bytes()
    output.write_utility()
    artifact = json.loads((checkout / output.UTILITY_PATH).read_bytes())
    assert artifact["gate_statistical_stop"] is True
    assert "verdict" not in artifact
    assert artifact[output.UTILITY_KEY]["A2"] == dict.fromkeys(NODES, 1)


def test_utility_requires_all_step6_captures(checkout):
    output.capture("primary", *stage(checkout))
    with pytest.raises(FileNotFoundError):
        output.write_utility()
    assert not (checkout / output.UTILITY_PATH).exists()


@pytest.mark.parametrize("rebuild_manifest", [False, True])
def test_utility_refuses_modified_primary_report(checkout, rebuild_manifest):
    capture_all(checkout)
    saved = checkout / output.CAPTURE_ROOT / "primary"
    input_bytes = (saved / output.INPUT_NAME).read_bytes()
    report = json.loads((saved / output.REPORT_NAME).read_bytes())
    report["nodes"][NODES[0]]["poi_A3"] = 0.7
    changed = json.dumps(report).encode("utf-8")
    (saved / output.REPORT_NAME).write_bytes(changed)
    if rebuild_manifest:
        (saved / output.MANIFEST_NAME).write_bytes(
            output._manifest({output.INPUT_NAME: input_bytes, output.REPORT_NAME: changed}))
    match = "differs from the primary input" if rebuild_manifest else "differ from SHA256SUMS"
    with pytest.raises(ValueError, match=match):
        output.write_utility()
    assert not (checkout / output.UTILITY_PATH).exists()


def test_invalid_stdout_is_preserved_without_a_manifest(checkout, monkeypatch):
    def invalid_report(_):
        print('{"schema": "r1_d8_gate_result/v3.1"}')
        return 0

    monkeypatch.setattr(gate, "main", invalid_report)
    with pytest.raises(ValueError, match="stdout does not have the v3.1 report fields"):
        output.capture("primary", *stage(checkout))
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert (saved / output.REPORT_NAME).exists()
    assert not (saved / output.MANIFEST_NAME).exists()


def test_capture_refuses_sealed_input_or_alias_before_release_check(checkout, monkeypatch):
    sealed = checkout / "r1_sealed" / "input.json"
    sealed.parent.mkdir()
    alias = checkout / "alias.json"
    alias.symlink_to(sealed)
    monkeypatch.setattr(output, "_release_record", lambda: pytest.fail("release must not be reached"))
    for path in (sealed, alias):
        with pytest.raises(RuntimeError, match="r1_sealed"):
            output.capture("primary", path, "a" * 64)


def test_capture_checks_releases_before_opening_the_input(tmp_path, monkeypatch):
    monkeypatch.setattr(output, "REPO", tmp_path)
    staged, sha = stage(tmp_path)
    read_bytes = Path.read_bytes

    def no_staged_read(path):
        assert path != staged
        return read_bytes(path)

    def missing_row(tier, stage_name):
        assert stage_name == "test"
        if tier == "T1":
            raise release.ReleaseStop("test release missing")
        return {}

    monkeypatch.setattr(Path, "read_bytes", no_staged_read)
    monkeypatch.setattr(release, "release_row", missing_row)
    with pytest.raises(release.ReleaseStop, match="test release missing"):
        output.capture("primary", staged, sha)
    assert not (tmp_path / output.CAPTURE_ROOT).exists()


def test_capture_refuses_wrong_input_hash_or_population(checkout):
    staged, sha = stage(checkout, "wdbc_sensitivity")
    with pytest.raises(ValueError, match="differs from the supplied builder export hash"):
        output.capture("primary", staged, "0" * 64)
    with pytest.raises(ValueError, match="T0 set differs"):
        output.capture("primary", staged, sha)
    assert not (checkout / output.CAPTURE_ROOT).exists()


def test_capture_refuses_relaunch_from_checkout_before_published_capture(checkout, monkeypatch):
    monkeypatch.setattr(release, "_git", lambda *args: b"published capture\n")
    with pytest.raises(FileExistsError, match="exists on published main"):
        output.capture("primary", *stage(checkout))
    assert not (checkout / output.CAPTURE_ROOT).exists()
