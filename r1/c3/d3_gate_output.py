"""Capture preregistration §4 step 6 and export the A§4.2 point utilities for D.3 §7.5(e)."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import json
import math
from pathlib import Path
import sys

from r1.c3 import analysis_guard, arms_freeze, gate, release
from r1.c3.d3_analysis import NODES, OFFLINE_ONLINE_ARMS
from r1.c3.d3_constants import load_noise
from r1.c3.release import _sha
from r1.harness import REPO


CAPTURE_ROOT = Path("results/r1/evidence/d8_gate_step6")
UTILITY_PATH = Path("results/r1/evidence/d3_offline_online_utility/gate_utility.json")
UTILITY_KEY = "per_node_utility"
RUNS = ("primary", "dup_secondary", "wdbc_sensitivity")
INPUT_NAME = "input.json"
REPORT_NAME = "gate_report.json"
STOP_NAME = "statistical_stop.txt"
MANIFEST_NAME = "SHA256SUMS"
REPORT_FIELDS = {
    "schema", "gate_version", "verdict", "first_ranked_arm", "arms", "nodes", "excluded_from_iqm",
    "ineligible_nodes", "below_test_floor", "off_design_size", "off_split", "t1_suites_without_labelled_node",
    "node_counts", "tier_descriptive", "protocol",
}


def _json(data: bytes) -> dict:
    def finite_float(raw: str) -> float:
        value = float(raw)
        if not math.isfinite(value):
            gate._no_constant(raw)
        return value

    return json.loads(data, object_pairs_hook=gate._no_duplicate_keys,
                      parse_constant=gate._no_constant, parse_float=finite_float)


def _manifest(files: dict[str, bytes]) -> bytes:
    return "".join(f"{_sha(data)}  {name}\n" for name, data in sorted(files.items())).encode("ascii")


def _path(relative: Path) -> Path:
    path = REPO / relative
    analysis_guard.refuse_sealed(path)
    if path.resolve() != REPO.resolve() / relative or path.is_symlink():
        raise ValueError(f"{relative}: a symlink redirects the declared path")
    return path


def _release_record() -> tuple[dict, dict]:
    """Check both published test release rows and their common committed arms-frozen record."""
    rows = [release.release_row(tier, "test") for tier in gate.TIERS]
    t0, t1 = rows
    for key in ("arms_frozen_path", "arms_frozen_sha256", "split_sha256", "prereg_sha256", "gate_sha256",
                "builder_sha256"):
        if t0[key] != t1[key]:
            raise ValueError(f"test release rows differ on {key}")
    published_plan = release._git("show", "refs/remotes/origin/main:docs/r1/PLAN.md").decode("utf-8")
    published_rows = release.author_rows(published_plan)
    for row in rows:
        digests = [_sha(text.encode("utf-8")) for key, text in published_rows if key == row["row_id"]]
        if digests != [row["decision_sha256"]]:
            raise ValueError(f"{row['row_id']} must match the unique author row on published main")
    arms_path = t0["arms_frozen_path"]
    data = release._committed(arms_path)
    if _sha(data) != t0["arms_frozen_sha256"]:
        raise ValueError("arms-frozen record does not match the published release bindings")
    record = arms_freeze.parse_record(data.decode("utf-8"))
    if record.get("schema") != arms_freeze.RECORD_SCHEMA:
        raise ValueError("arms-frozen record schema is invalid")
    arms_freeze._pin(record["noise_source"], "noise_source", arms_freeze.NOISE_PATH, arms_freeze.NOISE_SHA256)
    arms_freeze._pin(record["gate"], "gate", release.GATE_PATH, t0["gate_sha256"])
    analysis_guard.require_d8_confirmation()
    gate._require_pins()
    return record, t0


def _validated_input(data: bytes, run: str, record: dict) -> dict:
    gate_input = _json(data)
    nodes = gate._validate(gate_input)
    expected_t0 = gate.T0_NODES if run == "wdbc_sensitivity" else record["t0_nodes"]
    if sorted(gate_input["t0_nodes"]) != sorted(expected_t0):
        raise ValueError(f"{run}: gate input T0 set differs from its declared population")
    suites = record["t1"]["suites"]
    if any(name not in suites or suites[name] != row["suite"]
           for name, row in nodes.items() if row["tier"] == "T1"):
        raise ValueError(f"{run}: gate input has a T1 node or suite outside the arms-frozen record")
    return nodes


def _validate_report(data: bytes, nodes: dict, gate_sha256: str) -> dict:
    report = _json(data)
    if not isinstance(report, dict) or set(report) != REPORT_FIELDS:
        raise ValueError("gate stdout does not have the v3.1 report fields")
    if (report["schema"] != gate.OUTPUT_SCHEMA or report["gate_version"] != gate.GATE_VERSION
            or report["verdict"] not in ("PASS", "FAIL") or report["first_ranked_arm"] not in gate.ARMS
            or not isinstance(report["arms"], dict) or set(report["arms"]) != set(gate.ARMS)
            or not all(isinstance(arm, dict) for arm in report["arms"].values())
            or not isinstance(report["nodes"], dict) or set(report["nodes"]) != set(nodes)
            or not isinstance(report["protocol"], dict)
            or report["protocol"].get("gate_sha256") != gate_sha256):
        raise ValueError("gate stdout differs from its schema, input population or gate pin")
    for name, node in nodes.items():
        actual = report["nodes"][name]
        if not isinstance(actual, dict) or any(actual.get(key) != node[key]
                                               for key in ("tier", "suite", "n_train", "n_dev", "n_test")):
            raise ValueError(f"{name}: gate report differs from the input layout")
    return report


def _statistical_stop(nodes: dict) -> bytes | None:
    try:
        gate._point(nodes)
    except gate.GateStop as exc:
        return (str(exc) + "\n").encode("utf-8")
    return None


def capture(run: str, input_path: Path, input_sha256: str) -> None:
    """Run the unchanged gate CLI once in a fresh, fixed capture directory."""
    if run not in RUNS:
        raise ValueError("unknown step-6 gate run")
    relative = CAPTURE_ROOT / run
    directory = _path(relative)
    analysis_guard.refuse_sealed(input_path)
    if directory.exists():
        raise FileExistsError(f"{relative} already exists; retain the existing gate attempt")
    if input_path.is_symlink() or not input_path.is_file():
        raise ValueError("gate input must be a regular staged file")
    record, release_row = _release_record()
    if release._git("ls-tree", "--name-only", "refs/remotes/origin/main", "--", relative.as_posix()):
        raise FileExistsError(f"{relative} already exists on published main; retain the existing gate attempt")
    data = input_path.read_bytes()
    if _sha(data) != input_sha256:
        raise ValueError("gate input sha256 differs from the supplied builder export hash")
    nodes = _validated_input(data, run, record)
    directory.mkdir(parents=True, exist_ok=False)
    staged_input = directory / INPUT_NAME
    with staged_input.open("xb") as handle:
        handle.write(data)
    report_path = directory / REPORT_NAME
    try:
        with report_path.open("x", encoding="utf-8", newline="\n") as stdout, redirect_stdout(stdout):
            if gate.main([str(staged_input)]) != 0:
                raise RuntimeError("gate CLI failed")
    except gate.GateStop as exc:
        reason = (str(exc) + "\n").encode("utf-8")
        if report_path.stat().st_size != 0 or reason != _statistical_stop(nodes):
            raise
        with (directory / STOP_NAME).open("xb") as handle:
            handle.write(reason)
        with (directory / MANIFEST_NAME).open("xb") as handle:
            handle.write(_manifest({INPUT_NAME: data, REPORT_NAME: b"", STOP_NAME: reason}))
        raise
    report = report_path.read_bytes()
    _validate_report(report, nodes, release_row["gate_sha256"])
    with (directory / MANIFEST_NAME).open("xb") as handle:
        handle.write(_manifest({INPUT_NAME: data, REPORT_NAME: report}))


def _point_utilities(nodes: dict, noise: dict) -> dict:
    """A§4.2: equally weighted test-instance means of U / sigma_node, for the D.3 node set."""
    output = {arm: {} for arm in OFFLINE_ONLINE_ARMS}
    for name in NODES:
        if name not in nodes or nodes[name]["tier"] != "T0" or name not in noise:
            raise ValueError(f"{name}: missing primary gate series or pinned noise")
        sigma = noise[name]["sigma_node"]
        if not math.isfinite(sigma) or sigma <= 0 or noise[name]["delta_n"] != nodes[name]["delta_n"]:
            raise ValueError(f"{name}: invalid sigma or delta_n differs from the pinned noise source")
        for arm in OFFLINE_ONLINE_ARMS:
            mean = float((nodes[name]["test"][arm] / sigma).mean())
            if not math.isfinite(mean):
                raise ValueError(f"{name} {arm}: non-finite mean utility")
            output[arm][name] = mean
    return output


def _committed_capture(run: str) -> dict[str, bytes]:
    relative = CAPTURE_ROOT / run
    files = {}
    names = [INPUT_NAME, REPORT_NAME, MANIFEST_NAME]
    if _path(relative / STOP_NAME).exists():
        names.append(STOP_NAME)
    for name in names:
        source = relative / name
        _path(source)
        files[name] = release._committed(source.as_posix())
    raw_manifest = files.pop(MANIFEST_NAME)
    if raw_manifest != _manifest(files):
        raise ValueError(f"{run}: committed step-6 files differ from SHA256SUMS")
    return files


def _bind_point_report(report: dict, nodes: dict) -> None:
    eligible, point_rows, point_summary = gate._point(nodes)
    for name, point_row in point_rows.items():
        actual = dict(report["nodes"][name])
        if name in eligible:
            count = actual.pop("resamples_nonpositive_denominator", None)
            if type(count) is not int or not 0 <= count <= gate.N_RESAMPLES:
                raise ValueError(f"{name}: invalid gate resample count")
        if actual != point_row:
            raise ValueError(f"{name}: committed gate point row differs from the primary input")
    for arm, summary in point_summary.items():
        if any(report["arms"][arm].get(key) != value for key, value in summary.items()):
            raise ValueError(f"{arm}: committed gate summary differs from the primary input")


def write_utility() -> None:
    """After §4 step 6, use the committed primary capture for the D.3 descriptive artifact."""
    path = _path(UTILITY_PATH)
    if path.parent.exists():
        raise FileExistsError(f"{UTILITY_PATH.parent} already exists; retain the existing utility artifact")
    record, row = _release_record()
    captures = {run: _committed_capture(run) for run in RUNS}
    files = captures["primary"]
    nodes = _validated_input(files[INPUT_NAME], "primary", record)
    if STOP_NAME in files:
        if files[REPORT_NAME] or files[STOP_NAME] != _statistical_stop(nodes):
            raise ValueError("committed primary gate STOP differs from the primary input")
    else:
        report = _validate_report(files[REPORT_NAME], nodes, row["gate_sha256"])
        _bind_point_report(report, nodes)
    utility = _point_utilities(nodes, load_noise(REPO))
    artifact = {
        "schema": "r1_d3_gate_utility/v1",
        "unit": "sigma_node",
        "arms_frozen_sha256": row["arms_frozen_sha256"],
        "gate_sha256": row["gate_sha256"],
        "noise_sha256": arms_freeze.NOISE_SHA256,
        "step6_sha256": {name: _sha(data) for name, data in files.items()},
        "gate_statistical_stop": STOP_NAME in files,
        UTILITY_KEY: utility,
    }
    data = (json.dumps(artifact, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=False)
    with path.open("xb") as handle:
        handle.write(data)
    with path.with_name(MANIFEST_NAME).open("xb") as handle:
        handle.write(_manifest({path.name: data}))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_cmd = commands.add_parser("capture")
    capture_cmd.add_argument("run", choices=RUNS)
    capture_cmd.add_argument("input", type=Path)
    capture_cmd.add_argument("input_sha256")
    commands.add_parser("utility")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            capture(args.run, args.input, args.input_sha256)
        else:
            write_utility()
    except (KeyError, OSError, RuntimeError, ValueError, TypeError) as exc:
        print(f"gate output stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
