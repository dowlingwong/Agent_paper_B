"""Capture preregistration §4 step 6 and export the A§4.2 point utilities for D.3 §7.5(e).

After the test release, the step-5 operator passes receipted builder sources, the hash-checked
frozen A3/A5 predictions, and the PRE-DELTA noise pins to ``stage_inputs``. Publish its receipt
and the three named inputs. From that published state use ``capture RUN`` once for each of
``primary``, ``dup_secondary`` and ``wdbc_sensitivity``. Archive each capture and its manifest
on main before calling ``utility``. A recorded statistical STOP is a valid step-6 capture.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from r1.c3 import analysis_guard, arms_freeze, gate, gate_input_builder, p3_split, release
from r1.c3.d3_analysis import NODES, OFFLINE_ONLINE_ARMS
from r1.c3.d3_constants import load_noise
from r1.c3.release import _sha
from r1.harness import REPO


CAPTURE_ROOT = Path("results/r1/evidence/d8_gate_step6")
STAGING_ROOT = Path("results/r1/evidence/d8_gate_step5")
UTILITY_PATH = Path("results/r1/evidence/d3_offline_online_utility/gate_utility.json")
UTILITY_KEY = "per_node_utility"
RUNS = ("primary", "dup_secondary", "wdbc_sensitivity")
INPUT_NAME = "input.json"
REPORT_NAME = "gate_report.json"
STOP_NAME = "statistical_stop.txt"
MANIFEST_NAME = "SHA256SUMS"
BUILD_RECEIPT = "build.json"
BUILD_SCHEMA = "r1_d8_step5_gate_inputs/v1"
BUILD_PINS = ("arms_frozen_sha256", "prereg_sha256", "gate_sha256", "builder_sha256", "split_sha256")
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

    return json.loads(data.decode("utf-8"), object_pairs_hook=gate._no_duplicate_keys,
                      parse_constant=gate._no_constant, parse_float=finite_float)


def _encode(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


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
    for key in ("arms_frozen_path", *BUILD_PINS):
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
    arms_freeze._pin(record["gate_input_builder"], "gate_input_builder", release.BUILDER_PATH, t0["builder_sha256"])
    if record["split_file"] != p3_split.pin_of_sha(t0["split_sha256"]):
        raise ValueError("arms-frozen split differs from the test release")
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


def stage_inputs(sources, predictions: dict, noise: dict) -> None:
    """Run the pinned step-5 builder on the operator's receipted and frozen inputs, binding its named exports.

    The caller assembles the sources with release.builder_source, verifies the frozen prediction and PRE-DELTA
    pins, and commits this staging directory before invoking step 6.
    """
    directory = _path(STAGING_ROOT)
    if directory.exists():
        raise FileExistsError(f"{STAGING_ROOT} already exists; retain the existing builder export")
    record, row = _release_record()
    layout = record["t1"]
    g5 = next((source for source in sources if source.name == "g5"), None)
    t1 = None
    if layout["suites"]:
        if g5 is None or g5.split_sha256 != row["split_sha256"]:
            raise ValueError("G.5 builder source does not bind the frozen split")
        t1 = gate_input_builder.Tier1(layout["suites"], tuple(layout["modes"]), layout["d3_k6"],
                                     tail_laws=g5.tail_laws)
    split = _path(Path(record["split_file"]["path"]))
    runs = gate_input_builder.runs(sources, predictions, noise, primary_t0=record["t0_nodes"],
                                 t1=t1, split_path=split)
    inputs = {run: _encode(runs[run][0]) for run in RUNS}
    for run, data in inputs.items():
        _validated_input(data, run, record)
    receipt = {"schema": BUILD_SCHEMA, "pins": {key: row[key] for key in BUILD_PINS},
               "inputs": {run: _sha(data) for run, data in inputs.items()},
               "reports": {run: runs[run][1] for run in RUNS}}
    directory.mkdir(parents=True, exist_ok=False)
    for run, data in inputs.items():
        with (directory / f"{run}.json").open("xb") as handle:
            handle.write(data)
    with (directory / BUILD_RECEIPT).open("xb") as handle:
        handle.write(_encode(receipt))


def _read_published(relative: Path) -> bytes:
    _path(relative)
    path = relative.as_posix()
    data = release._committed(path)
    if data != release._git("show", f"refs/remotes/origin/main:{path}"):
        raise ValueError(f"{relative}: committed bytes differ from published main")
    return data


def _build_receipt(row: dict) -> tuple[dict, str]:
    data = _read_published(STAGING_ROOT / BUILD_RECEIPT)
    receipt = _json(data)
    if (not isinstance(receipt, dict) or set(receipt) != {"schema", "pins", "inputs", "reports"}
            or receipt["schema"] != BUILD_SCHEMA or receipt["pins"] != {key: row[key] for key in BUILD_PINS}
            or not isinstance(receipt["inputs"], dict) or set(receipt["inputs"]) != set(RUNS)
            or not isinstance(receipt["reports"], dict) or set(receipt["reports"]) != set(RUNS)
            or not all(isinstance(report, dict) for report in receipt["reports"].values())
            or not all(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
                       for digest in receipt["inputs"].values())):
        raise ValueError("committed step-5 receipt does not bind the three builder exports and frozen release")
    return receipt, _sha(data)


def _require_fields(value, fields: dict, label: str) -> None:
    if (not isinstance(value, dict) or set(value) != set(fields)
            or any(type(value[key]) not in kinds for key, kinds in fields.items())):
        raise ValueError(f"{label} differs from the v3.1 report schema")


def _protocol(nodes: dict, gate_sha256: str) -> dict:
    return {
        "gate_version": gate.GATE_VERSION, "interval": gate.INTERVAL, "resamples": gate.N_RESAMPLES,
        "seed": gate.SEED, "rng": gate.RNG, "numpy_version": gate.NUMPY_VERSION, "numpy_pin": gate.NUMPY_VERSION,
        "environment": gate.ENVIRONMENT, "elig_z_min": gate.ELIG_Z_MIN, "test_floor": gate.TEST_FLOOR,
        "split": gate.SPLIT, "design_instances": gate.DESIGN_INSTANCES,
        "design_split": {tier: list(counts) for tier, counts in gate.DESIGN_SPLIT.items()},
        "quantile_method": gate.QUANTILE_METHOD, "tstar_inf": gate.TSTAR_INF, "t0_nodes": list(gate.T0_NODES),
        "declared_t0_nodes": [name for name, node in nodes.items() if node["tier"] == "T0"],
        "suites": list(gate.SUITES), "family_alpha": gate.FAMILY_ALPHA, "levels": list(gate.LEVELS),
        "practical_size": gate.PRACTICAL_SIZE, "arms": list(gate.ARMS), "gate_sha256": gate_sha256,
    }


def _validate_report(data: bytes, nodes: dict, gate_sha256: str) -> None:
    report = _json(data)
    if not isinstance(report, dict) or set(report) != REPORT_FIELDS:
        raise ValueError("gate stdout does not have the v3.1 report fields")
    if (report["schema"] != gate.OUTPUT_SCHEMA or report["gate_version"] != gate.GATE_VERSION
            or report["verdict"] not in ("PASS", "FAIL") or report["first_ranked_arm"] not in gate.ARMS
            or not isinstance(report["arms"], dict) or set(report["arms"]) != set(gate.ARMS)
            or not all(isinstance(arm, dict) for arm in report["arms"].values())
            or not isinstance(report["nodes"], dict) or set(report["nodes"]) != set(nodes)
            or _encode(report["protocol"]) != _encode(_protocol(nodes, gate_sha256))):
        raise ValueError("gate stdout differs from its schema, input population or gate pin")
    fields = dict.fromkeys(("tested", "passed", "meets_practical_size"), (bool,))
    fields.update(dict.fromkeys(("rank", "resamples_with_infinite_tstar"), (int,)))
    fields.update(dict.fromkeys(("level", "lower_iqm_gap_closed", "lower_probability_of_improvement", "ranking_p_iqm",
                                 "ranking_p_poi", "ranking_p_composite", "iqm_gap_closed", "se_iqm_gap_closed",
                                 "probability_of_improvement"), (int, float)))
    fields["tstar_quantile"] = (int, float, type(None))
    for arm, result in report["arms"].items():
        _require_fields(result, fields, arm)
    _bind_point_report(report, nodes)


def _statistical_stop(nodes: dict) -> bytes | None:
    try:
        gate._point(nodes)
    except gate.GateStop as exc:
        return (str(exc) + "\n").encode("utf-8")
    return None


def capture(run: str) -> None:
    """Run the unchanged gate CLI once in a fresh, fixed capture directory."""
    if run not in RUNS:
        raise ValueError("unknown step-6 gate run")
    relative = CAPTURE_ROOT / run
    directory = _path(relative)
    if directory.exists():
        raise FileExistsError(f"{relative} already exists; retain the existing gate attempt")
    record, release_row = _release_record()
    if release._git("ls-tree", "--name-only", "refs/remotes/origin/main", "--", relative.as_posix()):
        raise FileExistsError(f"{relative} already exists on published main; retain the existing gate attempt")
    receipt, _ = _build_receipt(release_row)
    data = _read_published(STAGING_ROOT / f"{run}.json")
    if _sha(data) != receipt["inputs"][run]:
        raise ValueError(f"{run}: staged input differs from the named builder export hash")
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
        files[name] = _read_published(relative / name)
    raw_manifest = files.pop(MANIFEST_NAME)
    if raw_manifest != _manifest(files):
        raise ValueError(f"{run}: committed step-6 files differ from SHA256SUMS")
    return files


def _bind_point_report(report: dict, nodes: dict) -> None:
    eligible, point_rows, point_summary = gate._point(nodes)
    counts = {name: [node[f"n_{part}"] for part in gate.SPLITS] for name, node in nodes.items()}
    t1_by_suite = {suite: sum(node["tier"] == "T1" and node["suite"] == suite for node in nodes.values())
                   for suite in gate.SUITES}
    metadata = {
        "excluded_from_iqm": [name for name in nodes if name not in eligible],
        "ineligible_nodes": {name: node["ineligible_reasons"] for name, node in nodes.items() if name not in eligible},
        "below_test_floor": [name for name, node in nodes.items() if "test_floor" in node["ineligible_reasons"]],
        "off_design_size": {name: {"n_total": node["n_total"], "design": gate.DESIGN_INSTANCES[node["tier"]]}
                            for name, node in nodes.items() if node["n_total"] != gate.DESIGN_INSTANCES[node["tier"]]},
        "off_split": {name: {"counts": counts[name], "p3": list(gate.DESIGN_SPLIT[node["tier"]])}
                      for name, node in nodes.items() if node["n_total"] == gate.DESIGN_INSTANCES[node["tier"]]
                      and tuple(counts[name]) != gate.DESIGN_SPLIT[node["tier"]]},
        "t1_suites_without_labelled_node": [suite for suite, count in t1_by_suite.items() if count == 0],
        "node_counts": {"total": len(nodes), "t1_by_suite": t1_by_suite,
                        "by_tier": {tier: sum(node["tier"] == tier for node in nodes.values()) for tier in gate.TIERS}},
        "tier_descriptive": gate._tier_descriptive(nodes, point_rows, eligible),
    }
    for key, value in metadata.items():
        if _encode(report[key]) != _encode(value):
            raise ValueError(f"{key}: gate report metadata differs from the input")
    for name, point_row in point_rows.items():
        if not isinstance(report["nodes"][name], dict):
            raise ValueError(f"{name}: gate report node differs from the v3.1 schema")
        actual = dict(report["nodes"][name])
        if name in eligible:
            count = actual.pop("resamples_nonpositive_denominator", None)
            if type(count) is not int or not 0 <= count <= gate.N_RESAMPLES:
                raise ValueError(f"{name}: invalid gate resample count")
        if _encode(actual) != _encode(point_row):
            raise ValueError(f"{name}: gate point row differs from the input")
    for arm, summary in point_summary.items():
        if any(report["arms"][arm].get(key) != value for key, value in summary.items()):
            raise ValueError(f"{arm}: gate summary differs from the input")


def write_utility() -> None:
    """After §4 step 6, use the committed primary capture for the D.3 descriptive artifact."""
    path = _path(UTILITY_PATH)
    if path.parent.exists():
        raise FileExistsError(f"{UTILITY_PATH.parent} already exists; retain the existing utility artifact")
    record, row = _release_record()
    receipt, receipt_sha = _build_receipt(row)
    captures = {run: _committed_capture(run) for run in RUNS}
    for run, files in captures.items():
        if _sha(files[INPUT_NAME]) != receipt["inputs"][run]:
            raise ValueError(f"{run}: committed step-6 input differs from the named builder export hash")
    files = captures["primary"]
    nodes = _validated_input(files[INPUT_NAME], "primary", record)
    if STOP_NAME in files:
        if files[REPORT_NAME] or files[STOP_NAME] != _statistical_stop(nodes):
            raise ValueError("committed primary gate STOP differs from the primary input")
    else:
        _validate_report(files[REPORT_NAME], nodes, row["gate_sha256"])
    utility = _point_utilities(nodes, load_noise(REPO))
    artifact = {
        "schema": "r1_d3_gate_utility/v1",
        "unit": "sigma_node",
        "arms_frozen_sha256": row["arms_frozen_sha256"],
        "gate_sha256": row["gate_sha256"],
        "noise_sha256": arms_freeze.NOISE_SHA256,
        "step5_receipt_sha256": receipt_sha,
        "step6_sha256": {name: _sha(data) for name, data in files.items()},
        "gate_statistical_stop": STOP_NAME in files,
        UTILITY_KEY: utility,
    }
    data = _encode(artifact)
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
    commands.add_parser("utility")
    args = parser.parse_args(argv)
    try:
        if args.command == "capture":
            capture(args.run)
        else:
            write_utility()
    except (KeyError, OSError, RuntimeError, TypeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"gate output stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
