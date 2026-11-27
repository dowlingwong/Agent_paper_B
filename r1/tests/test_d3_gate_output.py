import json
from pathlib import Path

import pytest

from r1.c3 import d3_gate_output as output, gate, p3_split, release
from r1.c3.d3_analysis import NODES, OFFLINE_ONLINE_ARMS, offline_online_agreement


def gate_input(run="primary", *, stop=False):
    names = gate.T0_NODES if run == "wdbc_sensitivity" else NODES
    nodes = []
    for index, name in enumerate(names):
        n_test = 8 if stop or index == 0 else 9
        a2 = 1 if run == "dup_secondary" else 2
        nodes.append({
            "node": name, "tier": "T0", "suite": None, "delta_n": 0.5,
            "train": {"instance_ids": ["train"], "oracle": [5], "A2": [2]},
            "dev": {"instance_ids": ["dev"], "oracle": [5], "A2": [2]},
            "test": {"instance_ids": [f"test{i}" for i in range(n_test)],
                     "oracle": [10] * n_test, "A2": [a2] * n_test,
                     "A3": [4] * n_test, "A5": [6] * n_test},
        })
    return {"schema": gate.INPUT_SCHEMA, "split": gate.SPLIT, "t0_nodes": list(names), "nodes": nodes}


@pytest.fixture
def checkout(monkeypatch, tmp_path):
    monkeypatch.setattr(output, "REPO", tmp_path)
    record = {"t0_nodes": list(NODES), "t1": {"suites": {}}, "split_file": p3_split.SPLIT_FILES[1]}
    row = dict.fromkeys(output.BUILD_PINS, "d" * 64)
    row.update(gate_sha256=gate.gate_file_sha256(), split_sha256=p3_split.P3_SPLIT_SHA256)
    monkeypatch.setattr(output, "_release_record", lambda: (record, row))
    monkeypatch.setattr(output.analysis_guard, "require_d8_confirmation", lambda: None)
    # The fixtures provide bytes standing in for the step-6 commit in utility tests.
    monkeypatch.setattr(release, "_committed", lambda relative: (tmp_path / relative).read_bytes())
    def published(command, ref, *args):
        if command == "ls-tree":
            return b""
        return (tmp_path / ref.split(":", 1)[1]).read_bytes()

    monkeypatch.setattr(release, "_git", published)
    monkeypatch.setattr(output, "load_noise", lambda _: {n: {"sigma_node": 2, "delta_n": 0.5} for n in NODES})
    return tmp_path


def stage(root: Path, monkeypatch, *, primary_stop=False):
    def build(sources, predictions, noise, *, primary_t0, t1, split_path):
        assert primary_t0 == list(NODES)
        assert split_path == root / p3_split.V1_REL
        return {run: (gate_input(run, stop=primary_stop and run == "primary"), {}) for run in output.RUNS}

    monkeypatch.setattr(output.gate_input_builder, "runs", build)
    output.stage_inputs([], {}, {})
    return root / output.STAGING_ROOT


def capture_all(root, monkeypatch, *, primary_stop=False):
    stage(root, monkeypatch, primary_stop=primary_stop)
    for run in output.RUNS:
        if primary_stop and run == "primary":
            with pytest.raises(gate.GateStop, match="no node is IQM-eligible"):
                output.capture(run)
        else:
            output.capture(run)


def test_capture_retains_exact_stdout_and_excludes_a_second_launch(checkout, monkeypatch, capsys):
    staged = stage(checkout, monkeypatch) / "primary.json"
    assert gate.main([str(staged)]) == 0
    expected = capsys.readouterr().out.encode("utf-8")
    actual_main = gate.main
    calls = []

    def record_main(args):
        calls.append(args)
        return actual_main(args)

    monkeypatch.setattr(gate, "main", record_main)
    output.capture("primary")
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert calls == [[str(saved / output.INPUT_NAME)]]
    assert (saved / output.REPORT_NAME).read_bytes() == expected
    assert (saved / output.MANIFEST_NAME).read_bytes() == output._manifest(
        {output.INPUT_NAME: staged.read_bytes(), output.REPORT_NAME: expected})
    assert capsys.readouterr().out == ""
    with pytest.raises(FileExistsError):
        output.capture("primary")
    assert len(calls) == 1


def test_utility_uses_only_primary_test_means_in_sigma_units(checkout, monkeypatch):
    capture_all(checkout, monkeypatch)

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


def test_statistical_stop_carries_point_rows_without_a_verdict(checkout, monkeypatch):
    capture_all(checkout, monkeypatch, primary_stop=True)
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert (saved / output.REPORT_NAME).read_bytes() == b""
    assert b"no node is IQM-eligible" in (saved / output.STOP_NAME).read_bytes()
    output.write_utility()
    artifact = json.loads((checkout / output.UTILITY_PATH).read_bytes())
    assert artifact["gate_statistical_stop"] is True
    assert "verdict" not in artifact
    assert artifact[output.UTILITY_KEY]["A2"] == dict.fromkeys(NODES, 1)


def test_utility_requires_all_step6_captures(checkout, monkeypatch):
    stage(checkout, monkeypatch)
    output.capture("primary")
    with pytest.raises(FileNotFoundError):
        output.write_utility()
    assert not (checkout / output.UTILITY_PATH).exists()


@pytest.mark.parametrize("rebuild_manifest", [False, True])
def test_utility_refuses_modified_primary_report(checkout, monkeypatch, rebuild_manifest):
    capture_all(checkout, monkeypatch)
    saved = checkout / output.CAPTURE_ROOT / "primary"
    input_bytes = (saved / output.INPUT_NAME).read_bytes()
    report = json.loads((saved / output.REPORT_NAME).read_bytes())
    report["nodes"][NODES[0]]["poi_A3"] = 0.7
    changed = json.dumps(report).encode("utf-8")
    (saved / output.REPORT_NAME).write_bytes(changed)
    if rebuild_manifest:
        (saved / output.MANIFEST_NAME).write_bytes(
            output._manifest({output.INPUT_NAME: input_bytes, output.REPORT_NAME: changed}))
    match = "differs from the input" if rebuild_manifest else "differ from SHA256SUMS"
    with pytest.raises(ValueError, match=match):
        output.write_utility()
    assert not (checkout / output.UTILITY_PATH).exists()


def test_invalid_stdout_is_preserved_without_a_manifest(checkout, monkeypatch):
    stage(checkout, monkeypatch)
    def invalid_report(_):
        print('{"schema": "r1_d8_gate_result/v3.1"}')
        return 0

    monkeypatch.setattr(gate, "main", invalid_report)
    with pytest.raises(ValueError, match="stdout does not have the v3.1 report fields"):
        output.capture("primary")
    saved = checkout / output.CAPTURE_ROOT / "primary"
    assert (saved / output.REPORT_NAME).exists()
    assert not (saved / output.MANIFEST_NAME).exists()


def test_capture_refuses_sealed_alias_before_opening(checkout, monkeypatch):
    staging = stage(checkout, monkeypatch)
    sealed = checkout / "r1_sealed" / "input.json"
    sealed.parent.mkdir()
    alias = staging / "primary.json"
    alias.rename(staging / "original.json")
    alias.symlink_to(sealed)
    with pytest.raises(RuntimeError, match="r1_sealed"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT).exists()


def test_capture_checks_releases_before_opening_the_input(tmp_path, monkeypatch):
    monkeypatch.setattr(output, "REPO", tmp_path)
    staged = tmp_path / output.STAGING_ROOT / "primary.json"
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
        output.capture("primary")
    assert not (tmp_path / output.CAPTURE_ROOT).exists()


def test_capture_refuses_valid_full_input_substituted_for_primary(checkout, monkeypatch):
    staged = stage(checkout, monkeypatch)
    (staged / "primary.json").write_bytes((staged / "dup_secondary.json").read_bytes())
    with pytest.raises(ValueError, match="differs from the named builder export hash"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT).exists()


def test_stage_serializes_named_outputs_of_the_real_builder(checkout):
    from r1.tests.test_gate_input_builder import _first, _world

    sources, predictions, noise = _world()
    node = NODES[0]
    train = next(row for row in sources[0].rows if row["instance"] == _first(node, "train"))
    test = next(row for row in sources[0].rows
                if row["instance"] == _first(node, "test") and not row["noop"] and not row["duplicate"])
    for key in ("incumbent_hash", "candidate_hash"):
        test[key] = train[key]
    split = checkout / p3_split.V1_REL
    split.parent.mkdir(parents=True)
    split.write_bytes(p3_split.render(p3_split.build()))
    expected = output.gate_input_builder.runs(sources, predictions, noise, primary_t0=NODES, split_path=split)
    assert expected["primary"][0] != expected["dup_secondary"][0]
    output.stage_inputs(sources, predictions, noise)
    root = checkout / output.STAGING_ROOT
    receipt = json.loads((root / output.BUILD_RECEIPT).read_bytes())
    for name, (gate_input, builder_report) in expected.items():
        raw = (root / f"{name}.json").read_bytes()
        assert json.loads(raw) == gate_input
        assert receipt["inputs"][name] == output._sha(raw)
        assert receipt["reports"][name] == json.loads(output._encode(builder_report))


def test_capture_refuses_relaunch_from_checkout_before_published_capture(checkout, monkeypatch):
    stage(checkout, monkeypatch)
    monkeypatch.setattr(release, "_git", lambda *args: b"published capture\n")
    with pytest.raises(FileExistsError, match="exists on published main"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT).exists()


def test_capture_refuses_unpublished_stage_bytes(checkout, monkeypatch):
    stage(checkout, monkeypatch)
    publish = release._git
    monkeypatch.setattr(release, "_git", lambda *args: publish(*args) if args[0] != "show" else b"other bytes")
    with pytest.raises(ValueError, match="differ from published main"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT).exists()


def test_capture_refuses_utf8_bom_before_creating_attempt(checkout, monkeypatch):
    stage_root = stage(checkout, monkeypatch)
    path = stage_root / "primary.json"
    data = b"\xef\xbb\xbf" + path.read_bytes()
    path.write_bytes(data)
    receipt = stage_root / output.BUILD_RECEIPT
    index = json.loads(receipt.read_bytes())
    index["inputs"]["primary"] = output._sha(data)
    receipt.write_bytes(output._encode(index))
    with pytest.raises(ValueError, match="UTF-8 BOM"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT).exists()


@pytest.mark.parametrize("field", ["node_counts", "lower_iqm_gap_closed"])
def test_capture_refuses_malformed_nested_report(checkout, monkeypatch, field):
    stage(checkout, monkeypatch)
    load = gate.load_and_evaluate

    def malformed(path):
        report = load(path)
        if field == "node_counts":
            report[field] = "wrong type"
        else:
            del report["arms"]["A3"][field]
        return report

    monkeypatch.setattr(gate, "load_and_evaluate", malformed)
    with pytest.raises(ValueError, match="metadata differs|differs from the v3.1 report schema"):
        output.capture("primary")
    assert not (checkout / output.CAPTURE_ROOT / "primary" / output.MANIFEST_NAME).exists()
