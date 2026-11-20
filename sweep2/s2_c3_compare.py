#!/usr/bin/env python3
"""S2-C3 comparison — apply the PRE-DECLARED criteria 1-6 to the three replay job outputs.

Reads the three transferred replay job outputs (`out.tar`/`work.tar` + `job_record.json` + `llama-server.log`),
verifies every pin in the job records (paper/harness/commit, image digest, model, ranking binding, label patch,
driver shim + patched-source pins, declared-inputs manifest + every-item verification, server argv/manager settings,
ENGINEERING_ONLY label, replay marker, audit seeds), re-checks every manifest `job_sha256` against
`out/<root>/job.json`, extracts the 12 per-instance campaign manifests, and applies
criteria 1-6 exactly as written in `docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md` (pinned by SHA-256). The
B2 expected values are embedded from that criteria document and cross-checked against the 12 pinned B2 off-root
manifests shipped in `docs/r1/reports/sweep2_20261116/c3_replay_inputs/` (SHA256SUMS-pinned).

Hard STOP (no report, no verdict): a missing/unreadable job output, a pin mismatch, a label leak, a missing or
duplicate instance, an audit-seed mismatch, or a reserved B.2 audit seed. Soft NOT PASS is a legitimate verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import s2_c3_replay as replay  # noqa: E402

REPORT_NAME = "S2_C3_RESULTS.md"

# --- B2 expected values: final_y table copied verbatim from the pre-declared criteria document ------------------
EXPECTED_FINAL_Y = {
    "digits_mlp__s9011": 0.9727019,
    "digits_mlp__s9012": 0.9710306,
    "digits_mlp__s9013": 0.9740947,
    "digits_mlp__s9014": 0.9727019,
    "openml_credit_approval__s9011": 0.9365820,
    "openml_credit_approval__s9012": 0.9216943,
    "openml_credit_approval__s9013": 0.9337075,
    "openml_credit_approval__s9014": 0.9120051,
    "openml_ionosphere__s9011": 0.9041795,
    "openml_ionosphere__s9012": 0.9749224,
    "openml_ionosphere__s9013": 0.9018575,
    "openml_ionosphere__s9014": 0.9078947,
}
# The criteria were corrected PRE-DATA on 16 Nov 2026: the original text quoted the 24-root candidate batch
# (58/82/58 over "480 trials"); this replay is the 12 thinking-off roots (240 trials) whose pinned totals are
# 20/33/20.  The corrected numbers are the applied criterion; the original is retained only for transparency.
EXPECTED_DIAG_DECLARED = {"invalid": 20, "duplicates": 33, "noops": 20}
EXPECTED_DIAG_DECLARED_ORIGINAL = {"invalid": 58, "duplicates": 82, "noops": 58}
EXPECTED_DIAG_OFF = {"trials": 240, "evaluated": 240, "invalid": 20, "duplicates": 33, "noops": 20,
                     "parse_failed": 0, "forecast_queries": 240, "forecast_query_failed": 0}
B2_GPU_HOURS_OFF = replay.B2_GPU_HOURS_OFF
TOLERANCES = {"final_y_abs": 0.02, "final_y_mean_abs": 0.01, "parse_failure_rate": 0.02,
              "diagnostic_relative": 0.10, "b2_offload_layers": 61, "throughput_multiple": 2.0}
EXPECTED_SOURCE_SHA256 = replay.CRITERIA_SHA256
DIAG_KEYS = ("trials", "evaluated", "invalid", "duplicates", "noops", "parse_failed", "forecast_queries",
             "forecast_query_failed")
EPS = 1e-12
Stop = replay.Stop


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _within(value: float, expected: float, rel: float) -> bool:
    return abs(value - expected) <= rel * expected + 1e-9


# ------------------------------------------------------------------ expected-value source verification
def verify_expected_sources(repo_root: Path = ROOT) -> dict:
    """Pin the expected-values source: the criteria document and the 12 shipped B2 off-root manifests."""
    repo_root = Path(repo_root)
    criteria = repo_root / replay.CRITERIA_PATH
    if not criteria.is_file() or _sha_file(criteria) != EXPECTED_SOURCE_SHA256:
        raise Stop("STOP: the pre-declared criteria document is missing or its sha256 pin does not match")
    inputs = repo_root / replay.INPUTS_DIR
    sums_path = inputs / "SHA256SUMS"
    if not sums_path.is_file() or _sha_file(sums_path) != replay.INPUTS_SHA256SUMS_SHA256:
        raise Stop("STOP: the pinned replay-input SHA256SUMS is missing or its sha256 pin does not match")
    sums = replay.parse_sha256sums(sums_path.read_text())
    derived = {}
    diag = {key: 0 for key in DIAG_KEYS}
    for root in replay.ROOTS:
        path = inputs / root / "campaign_manifest.json"
        if not path.is_file() or _sha_file(path) != sums[f"{root}/campaign_manifest.json"]:
            raise Stop(f"STOP: pinned B2 manifest {root} is missing or does not match SHA256SUMS")
        manifest = json.loads(path.read_text())
        finals = manifest.get("final_audits") or []
        if len(finals) != 1:
            raise Stop(f"STOP: pinned B2 manifest {root} has no single final audit")
        derived[root] = finals[0]["final_y"]
        for key in DIAG_KEYS:
            diag[key] += int((manifest.get("diagnostics") or {}).get(key, 0))
    if set(derived) != set(EXPECTED_FINAL_Y):
        raise Stop("STOP: pinned B2 manifests do not cover exactly the 12 replay instances")
    for root, value in EXPECTED_FINAL_Y.items():
        if abs(derived[root] - value) > 5e-7:
            raise Stop(f"STOP: embedded B2 final_y for {root} ({value}) != the pinned manifest ({derived[root]})")
    for key, value in EXPECTED_DIAG_OFF.items():
        if diag.get(key) != value:
            raise Stop(f"STOP: derived B2 off-root diagnostics {key}={diag.get(key)} != the pinned {value}")
    return {"criteria": str(criteria), "criteria_sha256": EXPECTED_SOURCE_SHA256,
            "pinned_inputs_sha256sums_sha256": replay.INPUTS_SHA256SUMS_SHA256,
            "derived_final_y": derived, "derived_off_root_diagnostics": diag,
            "declared_criterion3_diagnostics": EXPECTED_DIAG_DECLARED,
            "criterion3_denominator_defect": False,
            "note": ("criterion 3 was corrected PRE-DATA on 16 Nov 2026 to the 12 off-root totals 20/33/20 over "
                     "240 trials (the original text's 58/82/58 over 480 trials was the 24-root candidate batch); "
                     "the corrected numbers are applied and the original is retained in the criteria document.")}


# ------------------------------------------------------------------ job outputs
def _materialise(chunk_dir: Path) -> None:
    for name in ("out", "work"):
        tar = chunk_dir / f"{name}.tar"
        dest = chunk_dir / name
        if tar.is_file() and not dest.exists():
            dest.mkdir(mode=0o700)
            subprocess.run(["tar", "-xf", str(tar), "-C", str(dest)], check=True)


def _scan_label_leaks(obj, where: str = "manifest") -> list[str]:
    leaks = []

    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if "label" in key.lower() and isinstance(item, str) and item in ("EVIDENCE", "DRYRUN"):
                    leaks.append(f"{where}{path}.{key}={item}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")

    walk(obj, "")
    return leaks


def _find_manifests(out_dir: Path) -> list[Path]:
    if not out_dir.is_dir():
        raise Stop(f"STOP: replay job output has no materialised out/ directory ({out_dir})")
    return sorted(out_dir.rglob("campaign_manifest.json"))


def load_job_output(chunk_dir: Path) -> dict:
    chunk_dir = Path(chunk_dir)
    if not chunk_dir.is_dir():
        raise Stop(f"STOP: replay job output directory missing: {chunk_dir}")
    _materialise(chunk_dir)
    record_path = chunk_dir / "job_record.json"
    try:
        record = json.loads(record_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Stop(f"STOP: {chunk_dir} has no readable job_record.json: {exc}") from None
    if record.get("schema") != replay.RECORD_SCHEMA:
        raise Stop(f"STOP: {chunk_dir} job record is not an S2-C3 replay record")
    if record.get("label") != replay.LABEL or record.get("replay_marker") != replay.REPLAY_MARKER:
        raise Stop(f"STOP: label leak in {chunk_dir}: record label is "
                   f"{record.get('label')!r}/{record.get('replay_marker')!r}, not ENGINEERING_ONLY")
    pins = {"paper_commit": replay.PAPER_COMMIT, "harness_commit": replay.HARNESS_COMMIT,
            "image_digest": replay.IMAGE_DIGEST, "model_sha256": replay.GGUF_SHA256}
    for key, want in pins.items():
        if record.get(key) != want:
            raise Stop(f"STOP: {chunk_dir} job record pin {key} {record.get(key)!r} != {want!r}")
    patch = record.get("label_patch") or {}
    if (patch.get("patch_sha256") or patch.get("label_patch_sha256")) != replay.PATCH_SHA256:
        raise Stop(f"STOP: {chunk_dir} job record label-patch sha256 != the reviewed pin")
    shim = record.get("driver_shim") or {}
    if (shim.get("patch_sha256") or shim.get("shim_patch_sha256")) != replay.SHIM_SHA256:
        raise Stop(f"STOP: {chunk_dir} job record driver-shim sha256 != the reviewed pin")
    if shim.get("patched_source_sha256") != replay.PATCHED_SOURCE_SHA256:
        raise Stop(f"STOP: {chunk_dir} job record patched-source pins != the reviewed pins")
    if set(shim.get("targets") or []) != set(replay.SHIM_TARGETS):
        raise Stop(f"STOP: {chunk_dir} job record driver-shim targets != the reviewed targets")
    declared = record.get("declared_inputs") or {}
    if declared.get("manifest_sha256") != replay.DECLARED_SHA256:
        raise Stop(f"STOP: {chunk_dir} job record declared-inputs manifest sha256 != the reviewed pin")
    if declared.get("items_verified") != declared.get("items_declared") or not declared.get("items_declared"):
        raise Stop(f"STOP: {chunk_dir} job record did not verify every declared input item")
    if declared.get("independent_of_tasl") is not True:
        raise Stop(f"STOP: {chunk_dir} job record declared inputs are not TASL-independent")
    binding = record.get("binding") or {}
    if binding.get("recomputed") != replay.BINDING or binding.get("unchanged_by_rewrite") is not True:
        raise Stop(f"STOP: {chunk_dir} job record B2 binding is not the verified pin")
    if record.get("status") != "COMPLETE":
        raise Stop(f"STOP: {chunk_dir} job record status is {record.get('status')!r}, not COMPLETE")
    if not isinstance(record.get("server"), dict):
        raise Stop(f"STOP: {chunk_dir} job record has no server identity")
    for key in ("pid", "base_url", "build", "offloaded_layers", "total_layers", "argv", "manager_settings"):
        if key not in record["server"]:
            raise Stop(f"STOP: {chunk_dir} server record lacks {key}")
    argv = record["server"]["argv"]
    if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv):
        raise Stop(f"STOP: {chunk_dir} server record argv is not a list of strings")
    settings = record["server"]["manager_settings"]
    expected_settings = {"ctx": 32768, "n_gpu_layers": 999, "parallel": 1, "thinking": False,
                         "cache_prompt": False, "cache_type_k": "q8_0", "cache_type_v": "q8_0"}
    for key, want in expected_settings.items():
        if not isinstance(settings, dict) or settings.get(key) != want:
            raise Stop(f"STOP: {chunk_dir} server manager setting {key} != the pinned {want!r}")
    node = record.get("node")
    if node not in replay.NODES or record.get("chunk_id") != node:
        raise Stop(f"STOP: {chunk_dir} job record node/chunk are not a replay node")
    roots = record.get("roots") or []
    if [entry.get("instance_id") for entry in roots] != replay.ordered_roots(node):
        raise Stop(f"STOP: {chunk_dir} job record does not list its 4 node roots in order")
    if any(entry.get("returncode") != 0 for entry in roots):
        raise Stop(f"STOP: {chunk_dir} job record contains a nonzero root exit")
    server_log = chunk_dir / "llama-server.log"
    if not server_log.is_file():
        raise Stop(f"STOP: {chunk_dir} has no transferred llama-server.log (full-offload evidence)")
    try:
        log_offload = replay.lib.offload_check(server_log.read_text(errors="replace"))
    except replay.lib.Stop as exc:
        raise Stop(f"STOP: {chunk_dir} server log cannot prove full offload: {exc}") from None
    if (int(record["server"]["offloaded_layers"]), int(record["server"]["total_layers"])) != \
            (log_offload["offloaded_layers"], log_offload["total_layers"]):
        raise Stop(f"STOP: {chunk_dir} server record offload differs from the transferred server log")
    manifests = {}
    for path in _find_manifests(chunk_dir / "out"):
        manifest = json.loads(path.read_text())
        leaks = _scan_label_leaks(manifest, where=str(path))
        if leaks:
            raise Stop(f"STOP: label leak in replay output: {leaks[:3]}")
        instance = manifest.get("final_audits") and manifest["final_audits"][0].get("instance_id")
        if not isinstance(instance, str) or not replay.SAFE.fullmatch(instance):
            raise Stop(f"STOP: {path} has no valid final-audit instance id")
        if instance in manifests:
            raise Stop(f"STOP: duplicate instance {instance} across the replay outputs")
        manifests[instance] = {"manifest": manifest, "path": path}
    if not manifests:
        raise Stop(f"STOP: {chunk_dir} contains no campaign manifests")
    if not isinstance(record.get("wall_s"), (int, float)) or isinstance(record.get("wall_s"), bool):
        raise Stop(f"STOP: {chunk_dir} job record has no numeric wall_s")
    return {"dir": str(chunk_dir), "record": record, "manifests": manifests,
            "server": record["server"], "log_offload": log_offload, "wall_s": float(record["wall_s"])}


def collect(job_dirs: list[Path]) -> dict:
    if len(job_dirs) != 3:
        raise Stop("STOP: exactly three replay job outputs are required (one per B2 node)")
    outputs = [load_job_output(path) for path in job_dirs]
    nodes = [output["record"].get("node") for output in outputs]
    if sorted(nodes) != sorted(replay.NODES):
        raise Stop(f"STOP: the three replay jobs must cover {list(replay.NODES)} exactly; got {nodes}")
    instances: dict[str, dict] = {}
    for output in outputs:
        for instance, data in output["manifests"].items():
            if instance in instances:
                raise Stop(f"STOP: duplicate instance {instance} across the three replay jobs")
            instances[instance] = data
    if set(instances) != set(replay.ROOTS):
        missing = sorted(set(replay.ROOTS) - set(instances))
        extra = sorted(set(instances) - set(replay.ROOTS))
        raise Stop(f"STOP: the replay does not cover exactly the 12 recorded roots "
                   f"(missing={missing} extra={extra})")
    for instance, data in instances.items():
        manifest = data["manifest"]
        job_path = Path(data["path"]).parent / "job.json"
        if not job_path.is_file() or manifest.get("job_sha256") != _sha_file(job_path):
            raise Stop(f"STOP: {instance} campaign manifest job_sha256 does not bind out/{instance}/job.json")
        finals = manifest.get("final_audits") or []
        if len(finals) != 1:
            raise Stop(f"STOP: {instance} does not carry exactly one final audit")
        if finals[0].get("seeds") != list(replay.AUDIT_SEEDS):
            raise Stop(f"STOP: {instance} final-audit seeds are not 9201-9210")
        replay._scan_forbidden_seeds(manifest, label=instance)
        if manifest.get("status") != "COMPLETE" or manifest.get("label") != "EXAM":
            raise Stop(f"STOP: {instance} campaign manifest is not COMPLETE/EXAM")
        if manifest.get("job_binding") != replay.BINDING:
            raise Stop(f"STOP: {instance} campaign binding is not the pinned B2 binding")
        if manifest.get("execution_label") != replay.LABEL:
            raise Stop(f"STOP: label leak: {instance} execution_label is "
                       f"{manifest.get('execution_label')!r}")
        if manifest.get("replay_marker") != replay.REPLAY_MARKER:
            raise Stop(f"STOP: {instance} lacks the replay marker")
        if manifest.get("phase") != "b2" or manifest.get("mode") != "off":
            raise Stop(f"STOP: {instance} is not a B2 thinking-off campaign")
        final_y = finals[0].get("final_y")
        if not isinstance(final_y, (int, float)) or isinstance(final_y, bool):
            raise Stop(f"STOP: {instance} final_y missing")
        data["final_y"] = float(final_y)
        data["diagnostics"] = manifest.get("diagnostics") or {}
    return {"outputs": outputs, "instances": instances}


# ------------------------------------------------------------------ criteria
def apply_criteria(collected: dict) -> dict:
    instances = collected["instances"]
    results = {}
    # 1. final_y
    diffs = {instance: abs(data["final_y"] - EXPECTED_FINAL_Y[instance]) for instance, data in instances.items()}
    mean_abs = sum(diffs.values()) / len(diffs)
    worst = max(diffs, key=diffs.get)
    c1_pass = all(value <= TOLERANCES["final_y_abs"] + EPS for value in diffs.values()) and \
        mean_abs <= TOLERANCES["final_y_mean_abs"] + EPS
    results["1_final_y"] = {
        "pass": c1_pass, "mean_abs_delta": round(mean_abs, 8), "max_abs_delta": round(diffs[worst], 8),
        "worst_instance": worst,
        "rule": f"every |delta| <= {TOLERANCES['final_y_abs']} and mean |delta| <= "
                f"{TOLERANCES['final_y_mean_abs']}",
        "per_instance": {instance: round(value, 8) for instance, value in diffs.items()}}
    # 2. parse failures
    totals = {key: sum(int(data["diagnostics"].get(key, 0)) for data in instances.values()) for key in DIAG_KEYS}
    queries = totals["forecast_queries"]
    parse_failed = totals["parse_failed"]
    if queries <= 0:
        results["2_parse_failures"] = {"pass": False, "reason": "no forecast queries in the replay",
                                       "parse_failed": parse_failed, "forecast_queries": queries}
    else:
        rate = parse_failed / queries
        results["2_parse_failures"] = {
            "pass": rate <= TOLERANCES["parse_failure_rate"] + EPS, "rate": round(rate, 8),
            "parse_failed": parse_failed, "forecast_queries": queries,
            "rule": f"parse_failed / forecast_queries <= {TOLERANCES['parse_failure_rate']} (B2: 0/240)"}
    # 3. diagnostics within +/-10% of the corrected pre-data 20/33/20 (original 58/82/58 retained for transparency)
    diag = {}
    for key, expected in EXPECTED_DIAG_DECLARED.items():
        observed = totals[key]
        within = _within(observed, expected, TOLERANCES["diagnostic_relative"])
        off_expected = EXPECTED_DIAG_OFF[key]
        diag[key] = {"observed": observed, "declared_expected": expected, "within_declared": within,
                     "off_root_derived_expected": off_expected,
                     "within_off_root_derived": _within(observed, off_expected, TOLERANCES["diagnostic_relative"])}
    results["3_diagnostics"] = {
        "pass": all(item["within_declared"] for item in diag.values()),
        "rule": "invalid/duplicates/noops each within +/-10% of the pre-data-corrected B2 off totals 20/33/20",
        "values": diag, "totals": totals,
        "declared_denominator_defect": False}
    # 4. full offload
    offloads = []
    for output in collected["outputs"]:
        server = output["server"]
        logged = output.get("log_offload") or {}
        done, total = int(server.get("offloaded_layers") or 0), int(server.get("total_layers") or 0)
        offloads.append({"node": output["record"].get("node"), "offloaded": done, "total": total,
                         "logged_offloaded": logged.get("offloaded_layers"),
                         "logged_total": logged.get("total_layers"),
                         "full": bool(total and done == total and logged.get("offloaded_layers") == done
                                      and logged.get("total_layers") == total),
                         "matches_b2_layers": total == TOLERANCES["b2_offload_layers"]})
    c4_pass = all(item["full"] and item["matches_b2_layers"] for item in offloads)
    results["4_full_offload"] = {
        "pass": c4_pass, "servers": offloads,
        "rule": (f"every replay server log shows full offload and {TOLERANCES['b2_offload_layers']}/"
                 f"{TOLERANCES['b2_offload_layers']} layers at the B2 setting (a different layer count is not "
                 "accepted silently and needs an author explanation)")}
    # 5. throughput
    per_job = {output["record"].get("node"): float(output.get("wall_s") or 0.0) for output in collected["outputs"]}
    total_wall = sum(per_job.values())
    limit = TOLERANCES["throughput_multiple"] * B2_GPU_HOURS_OFF * 3600
    results["5_throughput"] = {
        "pass": total_wall <= limit + EPS,
        "replay_total_wall_s": round(total_wall, 1), "per_job_wall_s": per_job,
        "critical_path_wall_s": round(max(per_job.values()) if per_job else 0.0, 1),
        "limit_s": round(limit, 1),
        "rule": (f"replay total wall <= {TOLERANCES['throughput_multiple']}x the B2 EVIDENCE GPU time "
                 f"({B2_GPU_HOURS_OFF} GPU-hours = {B2_GPU_HOURS_OFF * 3600:.1f} s); limit {limit:.1f} s; "
                 "the per-job critical path is reported alongside")}
    # 6. no STOP (the hard STOPs above already refused a report; this is the positive statement)
    no_stop = all(output["record"].get("status") == "COMPLETE" for output in collected["outputs"])
    results["6_no_stop"] = {"pass": bool(no_stop),
                            "rule": ("every root campaign exits 0 with a complete campaign_manifest, no label "
                                     "leak, no pin mismatch, audit seeds 9201-9210, no reserved B.2 audit")}
    results["overall_pass"] = all(item["pass"] for item in results.values() if isinstance(item, dict))
    return results


def totals_trials_defect(totals: dict) -> dict:
    return {"replay_trials": totals.get("trials"), "replay_evaluated": totals.get("evaluated"),
            "replay_forecast_queries": totals.get("forecast_queries"),
            "declared_expectation": "58/82/58 over '480 trials' (the 24-root candidate batch)",
            "off_root_derived_expectation": dict(EXPECTED_DIAG_OFF),
            "statement": ("the pre-declared criterion-3 denominator is the 24-root batch total, not the 12-root "
                          "replay; the declared numbers are applied unchanged and this defect is disclosed.  A "
                          "correct replay may therefore FAIL criterion 3 as pre-declared; only the author may "
                          "amend the criteria, before any replay data exists.")}


# ------------------------------------------------------------------ report
def _fmt(value, digits=7):
    return "n/a" if value is None else f"{value:.{digits}f}"


def write_report(collected: dict, results: dict, sources: dict, path: Path, *, attempted_at: str = "") -> str:
    instances = collected["instances"]
    c1 = results["1_final_y"]["per_instance"]
    rows = []
    for instance in replay.ROOTS:
        data = instances[instance]
        rows.append(f"| {instance} | {_fmt(EXPECTED_FINAL_Y[instance])} | {_fmt(data['final_y'])} | "
                    f"{c1[instance]:.7f} | {'PASS' if c1[instance] <= TOLERANCES['final_y_abs'] + EPS else 'FAIL'} |")
    criteria_rows = []
    labels = {
        "1_final_y": ("1 final_y", f"mean |delta| {results['1_final_y']['mean_abs_delta']:.7f} "
                                   f"(<= {TOLERANCES['final_y_mean_abs']}), max "
                                   f"{results['1_final_y']['max_abs_delta']:.7f} "
                                   f"(<= {TOLERANCES['final_y_abs']})"),
        "2_parse_failures": ("2 parse failures",
                             f"{results['2_parse_failures'].get('parse_failed')}/"
                             f"{results['2_parse_failures'].get('forecast_queries')} = "
                             f"{results['2_parse_failures'].get('rate', 'n/a')} (<= "
                             f"{TOLERANCES['parse_failure_rate']})"),
        "3_diagnostics": ("3 diagnostics",
                          "invalid/duplicates/noops vs pre-data-corrected 20/33/20: " + ", ".join(
                              f"{key} {item['observed']}/{item['declared_expected']}"
                              for key, item in results["3_diagnostics"]["values"].items())),
        "4_full_offload": ("4 full offload", "; ".join(
            f"{item['node']} {item['offloaded']}/{item['total']}" for item in results["4_full_offload"]["servers"])),
        "5_throughput": ("5 throughput", f"{results['5_throughput']['replay_total_wall_s']} s total (<= "
                                         f"{results['5_throughput']['limit_s']} s = 2x B2)"),
        "6_no_stop": ("6 no STOP", "all roots rc 0 with complete manifests"),
    }
    for key, (label, detail) in labels.items():
        verdict = "PASS" if results[key]["pass"] else "NOT PASS"
        criteria_rows.append(f"| {label} | {verdict} | {detail} |")
    overall = "PASS" if results["overall_pass"] else "NOT PASS"
    diag = results["3_diagnostics"]
    defect = sources.get("criterion3_denominator_defect")
    defect_block = ""
    if defect:
        d = diag["values"]
        defect_block = f"""
## Pre-declared criteria defect disclosed (criterion 3)

The criteria document pre-declares criterion 3 as "invalid/duplicates/noops counts each within ±10 % of B2's
58/82/58 over the 12 roots (480 trials, 480 evaluated, 58 invalid, 82 duplicates, 58 noops, ...)". The 480-trial /
58-82-58 figure is the **24-root candidate batch** (thinking-off + descriptive thinking-on), while this replay is
the **12 thinking-off roots** (240 trials). The pinned B2 off-root totals are
**invalid {EXPECTED_DIAG_OFF['invalid']}, duplicates {EXPECTED_DIAG_OFF['duplicates']}, noops {EXPECTED_DIAG_OFF['noops']}**
over {EXPECTED_DIAG_OFF['trials']} trials (verified from the SHA256SUMS-pinned manifests; log in
`sweep2/evidence/s2_c3_preflight_local_20261116.txt`).
The pre-declared numbers are applied **exactly** (no post-hoc relaxation): observed
{d['invalid']['observed']}/{d['duplicates']['observed']}/{d['noops']['observed']}, declared expectation
58/82/58, off-root-derived expectation 20/33/20. A correct replay may therefore be NOT PASS under criterion 3 as
written; only the author may amend the pre-declaration, and only before any replay data exists.

| diagnostic | replay | declared 58±10% | within declared | off-root 20/33/20 ±10% | within off-root |
|---|---|---|---|---|---|
| invalid | {d['invalid']['observed']} | {d['invalid']['declared_expected']} | {d['invalid']['within_declared']} | {d['invalid']['off_root_derived_expected']} | {d['invalid']['within_off_root_derived']} |
| duplicates | {d['duplicates']['observed']} | {d['duplicates']['declared_expected']} | {d['duplicates']['within_declared']} | {d['duplicates']['off_root_derived_expected']} | {d['duplicates']['within_off_root_derived']} |
| noops | {d['noops']['observed']} | {d['noops']['declared_expected']} | {d['noops']['within_declared']} | {d['noops']['off_root_derived_expected']} | {d['noops']['within_off_root_derived']} |
"""
    text = f"""# S2-C3 L40S deployment check — replay results (ENGINEERING_ONLY)

**Verdict: {overall}** (criteria 1-6 from the PRE-DECLARED `{replay.CRITERIA_PATH}`, sha256
`{EXPECTED_SOURCE_SHA256}`).  ENGINEERING_ONLY: this check is not evidence, produces no label table, starts no B.2
audit, and does not enter training or selection.  No criteria were relaxed after data; the declared tolerances are
applied exactly.

## Per-instance final_y (replay vs B2 EVIDENCE)

| instance | B2 final_y | replay final_y | abs(delta) | criterion 1 |
|---|---|---|---|---|
{chr(10).join(rows)}

- mean |delta| = **{results['1_final_y']['mean_abs_delta']:.7f}** (bound {TOLERANCES['final_y_mean_abs']}); max
  |delta| = **{results['1_final_y']['max_abs_delta']:.7f}** on `{results['1_final_y']['worst_instance']}` (bound
  {TOLERANCES['final_y_abs']}); not bitwise identity — this is a stack check.

## Criteria 1-6

| criterion | verdict | values |
|---|---|---|
{chr(10).join(criteria_rows)}

## Pins verified by the comparison

- expected-values source: `{replay.CRITERIA_PATH}` sha256 `{EXPECTED_SOURCE_SHA256}`
- pinned replay inputs SHA256SUMS sha256 `{replay.INPUTS_SHA256SUMS_SHA256}` (12 B2 off roots; 24 files)
- every job record: paper `{replay.PAPER_COMMIT}`, harness `{replay.HARNESS_COMMIT}`, image
  `{replay.IMAGE_DIGEST.split('@')[-1]}`, model `{replay.GGUF_SHA256}`, B2 binding `{replay.BINDING}`,
  label patch sha256 `{replay.PATCH_SHA256}`
- every campaign manifest: `execution_label = ENGINEERING_ONLY`, `replay_marker = {replay.REPLAY_MARKER}`, final
  audit seeds 9201-9210; no reserved B.2 seed 7001-7010 anywhere; no label leak.
- three job records, one per node (`{', '.join(replay.NODES)}`), 12 distinct instances, no duplicates.
{defect_block}
## Outputs read

{chr(10).join(f'- `{output["dir"]}` (node {output["record"].get("node")}, wall {output.get("wall_s")} s)' for output in collected["outputs"])}

Attempted comparison at {attempted_at or 'unspecified'}.  Independent review is required before any EVIDENCE claim;
this report is an ENGINEERING_ONLY artifact.
"""
    Path(path).write_text(text)
    return text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("job_outputs", nargs="+", help="three transferred replay job output directories")
    ap.add_argument("--out", required=True, help=f"report path (default name {REPORT_NAME})")
    ap.add_argument("--repo-root", default=str(ROOT))
    ap.add_argument("--attempted-at", default="")
    a = ap.parse_args(argv)
    sources = verify_expected_sources(Path(a.repo_root))
    collected = collect([Path(path) for path in a.job_outputs])
    results = apply_criteria(collected)
    write_report(collected, results, sources, Path(a.out), attempted_at=a.attempted_at)
    print(json.dumps({"ok": True, "verdict": "PASS" if results["overall_pass"] else "NOT PASS",
                      "criteria": {key: value["pass"] for key, value in results.items()
                                   if isinstance(value, dict) and "pass" in value},
                      "report": str(a.out)}, indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
