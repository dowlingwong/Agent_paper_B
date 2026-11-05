#!/usr/bin/env python3
"""Generate and guard HoreKa jobs. AI-assisted, draft: independent review required.

Manifest schema hk2_job/v1: account, partition, time, mem, cpus, gpus, phase,
kind (engineering or evidence), production (boolean), and argv (nonempty argument
array). Evidence submission is disabled until its authorisation gate is implemented.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

import hk2_common as c

SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")


def require_submission_readiness(config):
    """The sole submit switch is off in the shipped configuration; HK1 may enable it."""
    if config["values"].get("real_submission_enabled") is not True:
        raise c.Hk2Error("real submission disabled by configuration; enable only at reviewed HK1")


def validate_manifest(data, config):
    if not isinstance(data, dict) or data.get("schema") != "hk2_job/v1":
        raise c.Hk2Error("manifest schema must be hk2_job/v1")
    for key in ("account", "partition", "time", "mem", "phase", "kind"):
        if not isinstance(data.get(key), str) or not data[key] or not SAFE.fullmatch(data[key]) and key not in ("time",):
            raise c.Hk2Error("missing or invalid " + key)
    for key in ("cpus", "gpus"):
        if type(data.get(key)) is not int or data[key] < (1 if key == "cpus" else 0):
            raise c.Hk2Error("invalid " + key)
    argv = data.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x and "\x00" not in x and "\n" not in x for x in argv):
        raise c.Hk2Error("argv must be a nonempty array of single-line arguments")
    if data["kind"] not in ("engineering", "evidence"):
        raise c.Hk2Error("kind must be engineering or evidence")
    if type(data.get("production")) is not bool:
        raise c.Hk2Error("production must be a boolean")
    if data["kind"] == "evidence":
        raise c.Hk2Error("evidence submission needs an authorisation gate that is not implemented")
    if data["phase"] not in ("HK1", "HK2", "HK3", "HK4", "HK4b", "HK5"):
        raise c.Hk2Error("unrecognised or evidence phase; no evidence authorisation gate exists")
    if data["account"] != config["values"]["account"]:
        raise c.Hk2Error("account mismatch")
    seconds = c.parse_slurm_time(data["time"])
    if seconds <= 0:
        raise c.Hk2Error("time must be positive")
    mem = c.parse_mem_mb(data["mem"])
    part = data["partition"]
    dev = part in config["values"]["dev_partitions"]
    if dev and (data["production"] or data["phase"] not in ("HK1", "HK2")):
        raise c.Hk2Error("production job on dev partition")
    if dev and seconds > c.parse_slurm_time(str(config["values"]["dev_max_time"])):
        raise c.Hk2Error("dev time exceeds limit")
    shape = config["values"]["probed_shape"]
    if data["gpus"] > int(shape["gpus"]) or data["cpus"] > int(shape["cpus_per_task"]) or mem > float(shape["mem_mb"]):
        raise c.Hk2Error("request exceeds probed shape")
    if part.startswith("gpu-") and (data["gpus"] < 1 or seconds > float(config["values"]["t_max_hours"]) * 3600):
        raise c.Hk2Error("invalid production GPU count or T_max exceeded")
    if part.startswith("dev-gpu") and data["gpus"] < 1:
        raise c.Hk2Error("dev-gpu requires an explicit GPU")
    return seconds


def check_guards(data, config, plan, outstanding, accounted, now, author=False, inside=None):
    seconds = validate_manifest(data, config)
    v = config["values"]
    if Path(c.expand_path(str(v["stop_marker"]))).exists():
        raise c.Hk2Error("STOP marker exists")
    if (c.records_dir(config) / "SUBMISSION_UNCERTAIN").exists():
        raise c.Hk2Error("previous submission outcome requires manual reconciliation")
    if now >= c.parse_iso(str(v["freeze_F"])):
        raise c.Hk2Error("submission freeze reached")
    if now + dt.timedelta(seconds=seconds) > c.parse_iso(str(v["cutoff_C"])):
        raise c.Hk2Error("job cannot finish before cutoff")
    if len(outstanding) >= int(v["max_outstanding"]):
        raise c.Hk2Error("submission would exceed outstanding-job limit")
    unified, _ = c.plan_has_row(Path(plan), "R1-HOREKA-UNIFIED-SUBMISSION")
    if not unified:
        raise c.Hk2Error("PLAN unified submission ruling absent")
    dev_parts = v["dev_partitions"]
    if data["partition"] in dev_parts and any(j["partition"] in dev_parts or j["qos"] == "dev" for j in outstanding):
        raise c.Hk2Error("dev QoS already has an outstanding job")
    inside = dict(os.environ) if inside is None else inside
    if inside.get("SLURM_JOB_ID"):
        current = inside.get("SLURM_JOB_PARTITION")
        if not current:
            raise c.Hk2Error("current Slurm partition unavailable")
        if current in dev_parts:
            raise c.Hk2Error("submission from a dev job is forbidden")
    ruled, _ = c.plan_has_row(Path(plan), str(v["ruling_row_id"]))
    if not ruled and (inside.get("SLURM_JOB_ID") or (data["partition"].startswith("gpu-") and not author)):
        raise c.Hk2Error("PLAN submission ruling absent")
    c.require_submission_accounted(config, outstanding, accounted)
    budget = c.budget_state(outstanding, accounted)
    proposed = c.gpu_hours(seconds, data["gpus"])
    total = budget["used_gpu_h"] + budget["reserved_gpu_h"] + proposed
    if total > float(v["budget_stop_gpu_h"]):
        raise c.Hk2Error("GPU-hour STOP threshold exceeded")
    return {"used_gpu_h": budget["used_gpu_h"], "reserved_gpu_h": budget["reserved_gpu_h"], "new_gpu_h": proposed, "total_gpu_h": total}


def render_script(data, digest, config):
    v = config["values"]
    # All directive values have been validated; argv uses POSIX shell quoting.
    lines = ["#!/bin/bash", "# manifest_sha256=" + digest, "#SBATCH -A " + data["account"],
             "#SBATCH -p " + data["partition"], "#SBATCH --time=" + data["time"],
             "#SBATCH -N 1", "#SBATCH -n 1", "#SBATCH -c " + str(data["cpus"]),
             "#SBATCH --mem=" + data["mem"], "#SBATCH --deadline=" + c.parse_iso(str(v["cutoff_C"])).replace(tzinfo=None, microsecond=0).isoformat(),
             "#SBATCH --signal=B:USR1@600"]
    if data["gpus"]:
        lines.append("#SBATCH --gpus=" + str(data["gpus"]))
    lines += ["", " ".join(shlex.quote(x) for x in data["argv"]) + " &", "pid=$!",
              "trap 'kill -USR1 \"$pid\" 2>/dev/null || :' USR1", "wait \"$pid\"", "rc=$?",
              "if [ \"$rc\" -gt 128 ]; then wait \"$pid\"; rc=$?; fi", "exit \"$rc\"", ""]
    return "\n".join(lines)


def scrubbed_environment():
    allowed = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TZ")
    return {k: os.environ[k] for k in allowed if k in os.environ}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--config", type=Path, default=c.DEFAULT_CONFIG)
    p.add_argument("--plan", type=Path, default=c.DEFAULT_PLAN)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--submit", action="store_true")
    p.add_argument("--author", action="store_true")
    args = p.parse_args(argv)
    try:
        raw = args.manifest.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw.decode("utf-8"))
        config = c.load_config(args.config)
        validate_manifest(data, config)
        script = render_script(data, digest, config)
        if args.dry_run:
            print("manifest_sha256=" + digest)
            print("proposed_config=" + ",".join(config["proposed"]))
            print("DRY RUN: live queue, budget and submission guards have not been checked")
            print(script, end="")
            return 0
        require_submission_readiness(config)
        if args.author:
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                raise c.Hk2Error("--author requires an interactive terminal")
            if input("Enter the first 8 characters of manifest sha256: ").strip() != digest[:8]:
                raise c.Hk2Error("manifest confirmation mismatch")
        directory = c.records_dir(config)
        with c.QueryLock(directory / "query.lock"):
            outstanding, accounted = c.query_snapshot(config)
            budget = check_guards(data, config, args.plan, outstanding, accounted, c.utc_now(), args.author)
            c.refuse_deadline_resubmission(config, digest, accounted)
            directory.mkdir(parents=True, exist_ok=True)
            script_path = directory / (digest + ".sbatch")
            script_path.write_text(script, encoding="utf-8")
            env = scrubbed_environment()
            test = subprocess.run(["sbatch", "--test-only", str(script_path)], env=env, capture_output=True, text=True, timeout=120)
            record = {"manifest_sha256": digest, "config_sha256": config["sha256"], "config_proposed": config["proposed"],
                      "phase": data["phase"], "budget": budget, "test_only_rc": test.returncode,
                      "test_only_stdout": test.stdout, "test_only_stderr": test.stderr, "time": c.iso(c.utc_now())}
            log = directory / "submissions.jsonl"
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(record, event="test-only"), sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            if test.returncode:
                raise c.Hk2Error("sbatch --test-only failed; see submission record")
            # Time limits may have crossed a boundary while test-only waited.
            check_guards(data, config, args.plan, outstanding, accounted, c.utc_now(), args.author)
            marker = directory / "SUBMISSION_UNCERTAIN"
            # Created and synced before sbatch: a timeout or crash cannot silently
            # permit a second submission before the first is reconciled.
            with marker.open("x", encoding="utf-8") as fh:
                fh.write(json.dumps({"manifest_sha256": digest, "time": c.iso(c.utc_now())}) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            dirfd = os.open(str(directory), os.O_RDONLY)
            try:
                os.fsync(dirfd)
            finally:
                os.close(dirfd)
            submit = subprocess.run(["sbatch", "--parsable", str(script_path)], env=env, capture_output=True, text=True, timeout=120)
            match = re.fullmatch(r"(\d+)(?:;[A-Za-z0-9_.-]+)?\s*", submit.stdout)
            with log.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(dict(record, event="submit", submit_rc=submit.returncode,
                                         submit_stdout=submit.stdout, submit_stderr=submit.stderr,
                                         job_id=match.group(1) if match else ""), sort_keys=True) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            if submit.returncode or not match:
                raise c.Hk2Error("sbatch outcome uncertain or failed; inspect record before any retry")
            archive = directory / "_to_delete"
            archive.mkdir(exist_ok=True)
            os.replace(str(marker), str(archive / ("submitted-" + match.group(1) + "-" + digest + ".json")))
            print("submitted job " + match.group(1))
        return 0
    except c.AccountingPending as exc:
        print("WAIT: " + str(exc) + "; retry after at least 60 seconds", file=sys.stderr)
        return 75
    except (c.Hk2Error, OSError, ValueError, subprocess.SubprocessError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
