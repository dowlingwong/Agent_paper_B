#!/usr/bin/env python3
"""Generate and guard ETP HTCondor jobs. AI-assisted, draft: independent review required.

Manifest schema ``htc_job/v1`` (all keys required unless marked optional; no other key):

* ``schema``: "htc_job/v1";
* ``name``: job label, ``[A-Za-z0-9_.-]+`` (log, output and error file stem);
* ``kind``: "probe" (a pool probe) or "track_g" (a Track G run table, see below);
* ``image``: container image reference (``Universe = docker``);
* ``cpus`` (int >= 1), ``memory_mb`` (int >= 1), ``disk_kb`` (int >= 1), ``walltime_s`` (int >= 1);
* ``gpus``: int 0..max_gpus, whole GPUs only (``RequestGPUMemoryMB`` is never rendered and the
  key ``gpu_memory_mb`` is refused);
* ``gpu_device_name``: exact ``GPUs_DeviceName`` from the config list, required when gpus > 0, null
  otherwise;
* ``placement``: "local" (``requirements = TARGET.ProvidesETPResources``: /work, /home, /ceph) or
  "remote" (``+RemoteJob = True``; never combined with ProvidesETPResources). A GPU job must be remote;
* ``cloud_site`` (optional, remote only): a ``TARGET.CloudSite`` value from the config list;
* ``etp_ceph`` (optional bool, remote only): require ``TARGET.ProvidesEtpCeph =?= True`` (/ceph/srv);
* ``accounting_group`` (optional): one of the config's groups;
* ``executable`` and ``arguments`` (list of single-line strings);
* ``transfer_input_files`` and ``transfer_output_files`` (lists of relative or absolute paths,
  no commas); the input files must exist and total at most max_transfer_input_mb;
* optional ``executable_in_image`` (bool): the executable lives in the image (``transfer_executable = False``);
  otherwise it must exist here and counts toward the transfer limit;
* optional ``resume_dir``: a relative sandbox directory for ``htc_units`` completion markers; it is rendered
  as input and output with ``when_to_transfer_output = ON_EXIT_OR_EVICT`` so it survives an eviction.
  Without it a restarted job starts with only its inputs (HTCondor manual), so resume works only when the
  unit root is on persistent storage (``/work`` on local jobs);
* for kind "track_g" also ``table_id`` (the run table), ``runner_timeout_s`` (the timeout the M10 runner will
  use: factor x measured run time, or the provisional value), ``runs_per_job`` (runs executed one after another
  in the job; walltime must exceed runs_per_job x runner_timeout_s + the config margin, setup time included in
  the margin) and, when gpus > 0, the pinned device name above, because a CUDA OOM is classified ``divergent``
  only on a table with one pinned GPU model (author's answer to Q8). A Track G GPU table without a device
  name is refused, and ``--table-pins`` keeps one device name per table across manifests.

Arguments may not contain ``$`` (condor_submit and the starter expand ``$(...)``) or control characters.
The transfer limit is in decimal megabytes (10^6 bytes).

``--dry-run`` renders the JDL and, if ``condor_submit`` is on PATH, runs ``condor_submit -dry-run``
on it. ``--submit`` is refused while ``real_submission_enabled`` is false (the shipped value).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = HERE / "htc_config.json"
CONFIG_SCHEMA = "htc_config/v1"
STATUS_PREFIXES = ("ruled:", "measured:", "proposed:")
REQUIRED_CONFIG = ("real_submission_enabled", "max_transfer_input_mb", "max_gpus", "max_walltime_s",
                   "gpu_device_names", "cloud_sites", "accounting_groups", "runner_timeout_margin_s")
MANIFEST_SCHEMA = "htc_job/v1"
BASE_KEYS = {"schema", "name", "kind", "image", "cpus", "memory_mb", "disk_kb", "walltime_s", "gpus",
             "gpu_device_name", "placement", "executable", "arguments", "transfer_input_files",
             "transfer_output_files"}
OPTIONAL_KEYS = {"cloud_site", "etp_ceph", "accounting_group", "executable_in_image", "resume_dir"}
TRACK_G_KEYS = {"table_id", "runner_timeout_s", "runs_per_job"}
CONTROL = re.compile(r"[\x00-\x1f\x7f\u2028\u2029]")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
IMAGE = re.compile(r"^[a-z0-9][a-z0-9._/-]*(:[A-Za-z0-9_.-]+)?(@sha256:[0-9a-f]{64})?$")
DEVICE = re.compile(r"^[A-Za-z0-9 ._()-]+$")
PATH_TEXT = re.compile(r"^[A-Za-z0-9_./+-]+$")


class HtcError(RuntimeError):
    """A refusal: nothing is rendered or submitted."""


def load_config(path: Path | None = None) -> dict:
    target = Path(path) if path else DEFAULT_CONFIG
    raw = target.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("schema") != CONFIG_SCHEMA:
        raise HtcError(f"{target}: schema must be {CONFIG_SCHEMA}")
    values, statuses = {}, {}
    for key in REQUIRED_CONFIG:
        entry = payload.get(key)
        if not isinstance(entry, dict) or set(entry) != {"value", "status"}:
            raise HtcError(f"{target}: key {key!r} must be {{'value': ..., 'status': ...}}")
        status = str(entry["status"])
        if not status.startswith(STATUS_PREFIXES):
            raise HtcError(f"{target}: status of {key!r} must start with one of {STATUS_PREFIXES}")
        values[key], statuses[key] = entry["value"], status
    if type(values["real_submission_enabled"]) is not bool:
        raise HtcError("real_submission_enabled must be a JSON boolean")
    for key in ("max_transfer_input_mb", "max_gpus", "max_walltime_s", "runner_timeout_margin_s"):
        v = values[key]
        if type(v) not in (int, float) or not math.isfinite(v) or v < 0:
            raise HtcError(f"{key} must be a nonnegative finite number")
    for key in ("gpu_device_names", "cloud_sites", "accounting_groups"):
        if not isinstance(values[key], list) or not all(isinstance(x, str) and x for x in values[key]):
            raise HtcError(f"{key} must be a list of nonempty strings")
    proposed = sorted(k for k, s in statuses.items() if s.startswith("proposed:"))
    return {"values": values, "statuses": statuses, "proposed": proposed,
            "sha256": hashlib.sha256(raw).hexdigest()}


def _int(data, key, lo, hi=None):
    v = data.get(key)
    if type(v) is not int or v < lo or (hi is not None and v > hi):
        raise HtcError(f"invalid {key}: integer in [{lo}, {hi if hi is not None else 'inf'}] required")
    return v


def _lines(data, key, allow_empty=True):
    v = data.get(key)
    if not isinstance(v, list) or (not allow_empty and not v):
        raise HtcError(f"{key} must be a list")
    for x in v:
        if not isinstance(x, str) or not x or CONTROL.search(x):
            raise HtcError(f"{key} entries must be nonempty single-line strings without control characters")
    return v


def validate_manifest(data, config, base_dir: Path | None = None) -> dict:
    """Return a normalised manifest or raise HtcError. Input files are checked relative to base_dir."""
    v = config["values"]
    if not isinstance(data, dict) or data.get("schema") != MANIFEST_SCHEMA:
        raise HtcError(f"manifest schema must be {MANIFEST_SCHEMA}")
    if "gpu_memory_mb" in data or any("gpumemory" in str(k).lower().replace("_", "") for k in data):
        raise HtcError("RequestGPUMemoryMB is refused: jobs request whole GPUs only")
    kind = data.get("kind")
    if kind not in ("probe", "track_g"):
        raise HtcError("kind must be probe or track_g")
    allowed = BASE_KEYS | OPTIONAL_KEYS | (TRACK_G_KEYS if kind == "track_g" else set())
    missing = (BASE_KEYS | (TRACK_G_KEYS if kind == "track_g" else set())) - set(data)
    extra = set(data) - allowed
    if missing or extra:
        raise HtcError(f"manifest keys: missing {sorted(missing)}, unknown {sorted(extra)}")
    name = data["name"]
    if not isinstance(name, str) or not SAFE.fullmatch(name) or set(name) == {"."}:
        raise HtcError("invalid name")
    if not isinstance(data["image"], str) or not IMAGE.fullmatch(data["image"]):
        raise HtcError("invalid image reference")
    cpus = _int(data, "cpus", 1)
    _int(data, "memory_mb", 1)
    _int(data, "disk_kb", 1)
    walltime = _int(data, "walltime_s", 1, int(v["max_walltime_s"]))
    gpus = _int(data, "gpus", 0, int(v["max_gpus"]))
    device = data["gpu_device_name"]
    placement = data["placement"]
    if placement not in ("local", "remote"):
        raise HtcError("placement must be local or remote")
    if gpus > 0:
        if placement != "remote":
            raise HtcError("a GPU job needs placement remote (+RemoteJob = True)")
        if not isinstance(device, str) or not DEVICE.fullmatch(device) or device not in v["gpu_device_names"]:
            raise HtcError("a GPU job needs an exact GPUs_DeviceName from the config list")
    elif device is not None:
        raise HtcError("gpu_device_name must be null when gpus is 0")
    if placement == "local" and ("cloud_site" in data or "etp_ceph" in data):
        raise HtcError("cloud_site and etp_ceph apply to remote jobs only")
    if "cloud_site" in data and data["cloud_site"] not in v["cloud_sites"]:
        raise HtcError("cloud_site not in the config list")
    if "etp_ceph" in data and type(data["etp_ceph"]) is not bool:
        raise HtcError("etp_ceph must be a boolean")
    if "accounting_group" in data and data["accounting_group"] not in v["accounting_groups"]:
        raise HtcError("accounting_group not in the config list")
    exe = data["executable"]
    if not isinstance(exe, str) or not PATH_TEXT.fullmatch(exe):
        raise HtcError("invalid executable path")
    for arg in _lines(data, "arguments"):
        if "$" in arg:
            raise HtcError("'$' in arguments is refused: condor_submit and the starter expand $(...) macros")
    files_in = _lines(data, "transfer_input_files")
    files_out = _lines(data, "transfer_output_files")
    for f in files_in + files_out:
        if not PATH_TEXT.fullmatch(f):
            raise HtcError(f"transfer path {f!r} has characters outside [A-Za-z0-9_./+-]")
    if "executable_in_image" in data and type(data["executable_in_image"]) is not bool:
        raise HtcError("executable_in_image must be a boolean")
    resume = data.get("resume_dir")
    if resume is not None:
        if not isinstance(resume, str) or not PATH_TEXT.fullmatch(resume) or os.path.isabs(resume) \
                or ".." in Path(resume).parts or resume in files_out:
            raise HtcError("resume_dir must be a relative path in the sandbox, not also an output file")
    base = Path(base_dir) if base_dir else Path.cwd()
    total = 0
    if not data.get("executable_in_image"):
        # HTCondor transfers the executable by default: it counts toward the limit and must exist here
        exe_path = Path(exe) if os.path.isabs(exe) else base / exe
        if not exe_path.is_file() or exe_path.is_symlink():
            raise HtcError(f"executable {exe!r} is not a regular file (set executable_in_image for one in the image)")
        total += exe_path.stat().st_size
    for f in files_in:
        p = Path(f) if os.path.isabs(f) else base / f
        if not p.is_file() or p.is_symlink():
            raise HtcError(f"transfer input {f!r} is not a regular file")
        total += p.stat().st_size
    if total > float(v["max_transfer_input_mb"]) * 1_000_000:
        raise HtcError(f"transfer input totals {total} bytes, over {v['max_transfer_input_mb']} MB: use /ceph or xrootd")
    if kind == "track_g":
        table = data["table_id"]
        if not isinstance(table, str) or not SAFE.fullmatch(table):
            raise HtcError("invalid table_id")
        rt = data["runner_timeout_s"]
        if type(rt) not in (int, float) or not math.isfinite(rt) or rt <= 0:
            raise HtcError("runner_timeout_s must be a positive number")
        runs = data["runs_per_job"]
        if type(runs) is not int or runs < 1:
            raise HtcError("runs_per_job must be a positive integer")
        if walltime <= runs * rt + float(v["runner_timeout_margin_s"]):
            raise HtcError("walltime must exceed runs_per_job x the runner timeout plus the margin, so every run "
                           "times out by the runner before an HTCondor walltime hold")
    return {"total_input_bytes": total, "cpus": cpus, "gpus": gpus}


def condor_arguments(argv) -> str:
    """HTCondor 'new syntax': the whole value in double quotes; each argument containing a space or a
    single quote is wrapped in single quotes with single quotes doubled; double quotes are doubled."""
    parts = []
    for a in argv:
        a = a.replace('"', '""')
        if any(c in a for c in " \t'"):
            a = "'" + a.replace("'", "''") + "'"
        parts.append(a)
    return '"' + " ".join(parts) + '"'


def requirements(data) -> str:
    clauses = []
    if data["placement"] == "local":
        clauses.append("TARGET.ProvidesETPResources")
    if data["gpus"] > 0:
        clauses.append(f'TARGET.GPUs_DeviceName =?= "{data["gpu_device_name"]}"')
    if data.get("cloud_site"):
        clauses.append(f'TARGET.CloudSite =?= "{data["cloud_site"]}"')
    if data.get("etp_ceph"):
        clauses.append("TARGET.ProvidesEtpCeph =?= True")
    return " && ".join(f"({c})" for c in clauses)


def render_jdl(data, digest: str) -> str:
    n = data["name"]
    lines = [f"# manifest_sha256 = {digest}", "universe = docker", f"docker_image = {data['image']}",
             f"executable = {data['executable']}", f"arguments = {condor_arguments(data['arguments'])}",
             f"log = {n}.log", f"output = {n}.out", f"error = {n}.err",
             f"request_cpus = {data['cpus']}", f"request_memory = {data['memory_mb']}",
             f"request_disk = {data['disk_kb']}", f"+RequestWalltime = {data['walltime_s']}"]
    if data["gpus"] > 0:
        lines.append(f"request_GPUs = {data['gpus']}")
    if data["placement"] == "remote":
        lines.append("+RemoteJob = True")
    req = requirements(data)
    if req:
        lines.append(f"requirements = {req}")
    if data.get("accounting_group"):
        lines.append(f"accounting_group = {data['accounting_group']}")
    if data.get("executable_in_image"):
        lines.append("transfer_executable = False")
    resume = data.get("resume_dir")
    # With ON_EXIT a restarted job starts with only its inputs; ON_EXIT_OR_EVICT brings the resume directory back
    # (the pool's HTCondor version must support it: cluster report).
    lines += ["should_transfer_files = YES",
              "when_to_transfer_output = " + ("ON_EXIT_OR_EVICT" if resume else "ON_EXIT")]
    inputs = list(data["transfer_input_files"]) + ([resume] if resume else [])
    outputs = list(data["transfer_output_files"]) + ([resume] if resume else [])
    if inputs:
        lines.append("transfer_input_files = " + ",".join(inputs))
    if outputs:
        lines.append("transfer_output_files = " + ",".join(outputs))
    lines.append("queue 1")
    text = "\n".join(lines) + "\n"
    if re.search(r"(?i)RequestGPUMemory", text):
        raise HtcError("rendered JDL would request a GPU share")
    if data["placement"] == "remote" and "ProvidesETPResources" in text:
        raise HtcError("remote job must not require ProvidesETPResources")
    return text


def dry_run(jdl_path: Path, cwd: Path, runner=subprocess.run) -> dict:
    """``condor_submit -dry-run`` in ``cwd`` (the manifest's directory, where relative paths were validated)."""
    exe = shutil.which("condor_submit")
    if not exe:
        return {"condor_submit": None, "note": "condor_submit not on PATH; JDL rendered only"}
    out = jdl_path.resolve().with_suffix(".dryrun.txt")
    res = runner([exe, "-dry-run", str(out), str(jdl_path.resolve())], capture_output=True, text=True, timeout=120,
                 cwd=str(cwd))
    return {"condor_submit": exe, "rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr,
            "dry_run_file": str(out)}


def check_table_pin(path: Path, data: dict) -> dict:
    """One GPU model per Track G table (author's answer to Q8): the first manifest of a table pins its device name
    in ``path`` (JSON table_id -> device); later manifests of the table must match. Entries are only added."""
    if data.get("kind") != "track_g":
        return {}
    pins = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(pins, dict):
        raise HtcError(f"{path}: table pins must be a JSON object")
    table, device = data["table_id"], data["gpu_device_name"]
    if table in pins and pins[table] != device:
        raise HtcError(f"table {table!r} is pinned to {pins[table]!r}; this manifest asks for {device!r}")
    if table not in pins:
        pins[table] = device
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(pins, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)
    return pins


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("manifest", type=Path)
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    p.add_argument("--out", type=Path, default=None, help="directory for the rendered JDL (default: next to the manifest)")
    p.add_argument("--table-pins", type=Path, default=None,
                   help="JSON file table_id -> GPU device name; required for track_g manifests")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--submit", action="store_true")
    a = p.parse_args(argv)
    try:
        raw = a.manifest.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw.decode("utf-8"))
        config = load_config(a.config)
        validate_manifest(data, config, base_dir=a.manifest.parent)
        if a.submit and config["values"]["real_submission_enabled"] is not True:
            raise HtcError("real submission disabled by configuration (real_submission_enabled is false)")
        if data["kind"] == "track_g":
            if a.table_pins is None:
                raise HtcError("track_g manifests need --table-pins (one GPU model per table)")
            check_table_pin(a.table_pins, data)
        jdl = render_jdl(data, digest)
        out_dir = a.out or a.manifest.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        jdl_path = out_dir / f"{data['name']}.jdl"
        jdl_path.write_text(jdl, encoding="utf-8")
        if a.submit:
            raise HtcError("real submission is not implemented in this draft; use the reviewed JDL by hand")
        print(f"manifest_sha256={digest}")
        print("proposed_config=" + ",".join(config["proposed"]))
        print(jdl, end="")
        print(json.dumps(dry_run(jdl_path, a.manifest.parent.resolve()), sort_keys=True))
        return 0
    except (HtcError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
