"""One-shot P.3a supervisor. AI-assisted; DRYRUN then EVIDENCE; never resumes."""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import select
import socket
import subprocess
import sys
import time

from r1.c3.train import run as R

BASES = ("kev-0.8b", "kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base",
         "laya", "startlux-0.8b", "startlux-2b", "startlux-4b")
LIMIT_SECONDS = 45 * 3600  # GPU lease seconds; includes DRYRUN and EVIDENCE
SCRIPT = R.REPO / "r1/scripts/trackp.py"


def verify_pins():
    """Fail closed on authorization pins and the recorded TASL-7 freeze."""
    paper, harness = R.git_commit(R.REPO), R.git_commit(R.harness_root())
    if paper["branch"] != "trackp-20261026" or paper["dirty"]:
        raise R.TrackPStop("paper branch must be clean trackp-20261026")
    if harness["commit"] != "897d83c8efa364ec2fdd37288241cc42e01d7274" or harness["dirty"]:
        raise R.TrackPStop("harness pin mismatch or dirty harness")
    subprocess.run(["git", "-C", str(R.REPO), "ls-files", "--error-unmatch",
                    "r1/scripts/trackp_p3a_guarded.py", "r1/scripts/trackp_p3a_watchdog.py",
                    "r1/scripts/trackp_p3a_gate.py"], check=True, capture_output=True)
    for path, expected in (
        ("r1/c3/train/data/e0_v1.jsonl.gz", "4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290"),
        ("r1/c3/rules/p3_rule_v2.yaml", "8c0ef9089589eafcea04aea9c5936c7ab57625d19f2a7ab736de204d09840242"),
    ):
        digest = hashlib.sha256((R.REPO / path).read_bytes()).hexdigest()
        if digest != expected:
            raise R.TrackPStop(f"authorized hash mismatch: {path}")
    config = "r1/scripts/configs/trackp_portal.json"
    original = subprocess.run(["git", "-C", str(R.REPO), "show", "607e85e:" + config],
                              capture_output=True, check=True).stdout
    if original != (R.REPO / config).read_bytes():
        raise R.TrackPStop("trackp_portal.json changed from approved configuration")
    frozen = (R.REPO / "docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt").read_text()
    actual = subprocess.run(["/home/dowling/.local/bin/uv", "pip", "freeze", "--python", sys.executable],
                            capture_output=True, text=True, check=True, timeout=120).stdout
    if sorted(actual.splitlines()) != sorted(frozen.splitlines()):
        raise R.TrackPStop("run environment freeze does not match the recorded TASL-7 pin")
    from r1.c3.train.registry import reverify
    bad = reverify(R.REPO / "r1/c3/train/registry.yaml")
    if bad:
        raise R.TrackPStop(f"registered model files mismatch: {bad[:5]}")
    return {"paper": paper, "harness": harness, "model_registry": "all files reverified",
            "freeze": "matches TASL-7 recorded freeze"}


def read_json_finite(path):
    def reject(value):
        raise ValueError(f"non-finite JSON constant {value}")
    def walk(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("non-finite float")
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        if isinstance(value, list):
            for v in value:
                walk(v)
    with path.open() as fh:
        obj = json.load(fh, parse_constant=reject)
    walk(obj)
    return obj


def emit(path, record):
    with path.open("a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def verify_live_pins(journal):
    campaign = json.loads(journal.read_text().splitlines()[0])
    expected = campaign["pins"]
    for key, path in (("paper", R.REPO), ("harness", R.harness_root())):
        observed = R.git_commit(path)
        if observed["dirty"] or observed["commit"] != expected[key]["commit"]:
            raise R.TrackPStop(f"{key} pin changed after campaign start")
    for path, sha in (("r1/c3/train/data/e0_v1.jsonl.gz", "4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290"),
                      ("r1/c3/rules/p3_rule_v2.yaml", "8c0ef9089589eafcea04aea9c5936c7ab57625d19f2a7ab736de204d09840242")):
        if hashlib.sha256((R.REPO / path).read_bytes()).hexdigest() != sha:
            raise R.TrackPStop(f"authorized hash changed: {path}")

class GPUBudget:
    """Count actual exclusive GPU lease time across all P.3a jobs."""
    def __init__(self, limit=LIMIT_SECONDS, lease_log=R.LEASE_LOG):
        self.limit, self.used, self.lease_log = limit, 0.0, Path(lease_log)
        self.unobserved_lease_upper_s = 0.0

    def require_available(self):
        if self.used >= self.limit:
            raise R.TrackPStop("45 GPU-hour lease limit reached")


def worker_parent_death_guard(expected_parent):
    # Capture the expected parent before fork, and fail closed on either side of prctl.
    if os.getppid() != expected_parent:
        os.kill(os.getpid(), signal.SIGKILL)
    if ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_PDEATHSIG) failed")
    if os.getppid() != expected_parent:
        os.kill(os.getpid(), signal.SIGKILL)


def start_watchdog(proc, log, lease_path, offset, remaining):
    from r1.scripts.trackp_p3a_watchdog import process_state
    parent = os.getpid()
    state = process_state(parent)
    if state is None:
        raise R.TrackPStop("cannot identify supervisor for watchdog")
    ready_r, ready_w = os.pipe()
    script = R.REPO / "r1/scripts/trackp_p3a_watchdog.py"
    try:
        watchdog = subprocess.Popen([sys.executable, str(script), str(parent), state[1], str(proc.pid),
                                     str(log), str(ready_w), str(lease_path), str(offset), str(remaining)],
                                    pass_fds=(ready_w,), stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
    finally:
        os.close(ready_w)
    try:
        ready, _, _ = select.select([ready_r], [], [], 5)
        if not ready or os.read(ready_r, 1) != b"1" or watchdog.poll() is not None:
            raise R.TrackPStop("independent watchdog readiness handshake failed")
    finally:
        os.close(ready_r)
    return watchdog


def stop_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()
    for _ in range(100):
        try:
            os.killpg(proc.pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    raise R.TrackPStop("stopped process group did not disappear; manual investigation required")


def run_unit(root, journal, boot_id, budget, label, base, name, arguments, gpu=True):
    budget.require_available()
    if R.tasl7_driver_snapshot()["boot_id"] != boot_id:
        raise R.TrackPStop("unplanned reboot: boot ID changed")
    directory = root / label / base / name
    if directory.exists():
        raise R.TrackPStop(f"unit path already exists; preserve interrupted unit: {directory}")
    verify_live_pins(journal)
    directory.parent.mkdir(parents=True, exist_ok=True)
    log = directory.parent / (name + ".stdout.log")
    cmd = [sys.executable, str(SCRIPT), *arguments, "--evidence", label,
           "--run-dir", str(directory)]
    emit(journal, {"event": "unit_start", "label": label, "base": base, "unit": name,
                   "utc": R.utcnow(), "argv": cmd, "gpu_seconds_before": budget.used})
    budget.lease_log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("x") as fh, budget.lease_log.open("a+") as leases:
        leases.seek(0, os.SEEK_END)
        offset = leases.tell()
        gate_r, gate_w = os.pipe()
        expected_parent = os.getpid()
        gate = R.REPO / "r1/scripts/trackp_p3a_gate.py"
        launched_monotonic = time.monotonic()
        try:
            proc = subprocess.Popen([sys.executable, str(gate), str(gate_r), *cmd], stdout=fh,
                                    stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(gate_r,),
                                    preexec_fn=lambda: worker_parent_death_guard(expected_parent))
        finally:
            os.close(gate_r)
        start = end = None
        accounted = False
        def account(assume_unobserved=False):
            nonlocal accounted
            if accounted:
                return
            if start is not None and end is not None:
                budget.used += max(0.0, end - start)
            elif start is not None:
                budget.unobserved_lease_upper_s += max(0.0, time.monotonic() - start)
            elif assume_unobserved and gpu:
                budget.unobserved_lease_upper_s += max(0.0, time.monotonic() - launched_monotonic)
            accounted = True
        watchdog = None
        try:
            watchdog = start_watchdog(proc, directory.parent / (name + ".watchdog.log"),
                                      budget.lease_log, offset, budget.limit - budget.used)
            os.write(gate_w,b"1")
            os.close(gate_w)
            gate_w = None
            while True:
                if proc.poll() is None and watchdog.poll() is not None:
                    raise R.TrackPStop("independent worker-group watchdog exited unexpectedly")
                for line in leases:
                    event = json.loads(line)
                    if event.get("pid") != proc.pid:
                        continue
                    if event.get("event") in ("acquired", "start"):
                        observed = float(event["monotonic_s"])
                        if start is not None and start != observed:
                            raise R.TrackPStop("inconsistent GPU lease start")
                        start = observed
                    elif event.get("event") == "end":
                        if start is None or end is not None:
                            raise R.TrackPStop("invalid GPU lease end")
                        end = float(event["monotonic_s"])
                active = (end if end is not None else time.monotonic()) - start if start is not None else 0.0
                if active < 0 or not math.isfinite(active):
                    raise R.TrackPStop("invalid GPU lease duration")
                if budget.used + active >= budget.limit:
                    raise R.TrackPStop("45 GPU-hour lease limit reached; interrupted unit retained")
                rc = proc.poll()
                if rc is not None:
                    break
                time.sleep(0.5)
        except BaseException:
            try:
                stop_group(proc)
            finally:
                account(assume_unobserved=True)
            raise
        finally:
            if gate_w is not None:
                os.close(gate_w)
            if watchdog is not None:
                try:
                    watchdog_rc = watchdog.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    try:
                        stop_group(proc)
                    finally:
                        account(assume_unobserved=True)
                    raise R.TrackPStop("worker process group or watchdog remained after unit")
                if watchdog_rc:
                    try:
                        stop_group(proc)
                    finally:
                        account(assume_unobserved=True)
                    raise R.TrackPStop(f"independent watchdog STOP rc={watchdog_rc}; unobserved lease time is bounded, not measured")
    if start is not None and end is None:
        try:
            stop_group(proc)
        finally:
            account(assume_unobserved=True)
        raise R.TrackPStop(f"GPU lease missing end record: {directory}; duration is an upper bound")
    if rc:
        try:
            stop_group(proc)
        finally:
            account(assume_unobserved=True)
        raise R.TrackPStop(f"unit failed rc={rc}: {directory}; see {log}")
    account(assume_unobserved=gpu)
    report = read_json_finite(directory / "report.json")
    manifest = read_json_finite(directory / "manifest.json")
    driver = manifest.get("tasl7_driver") or {}
    if manifest.get("evidence_label") != label or driver.get("boot_id") != boot_id:
        raise R.TrackPStop(f"unit manifest label or boot ID mismatch: {directory}")
    if gpu:
        events = manifest.get("gpu_lease", [])
        if [e.get("event") for e in events] != ["start", "end"] or start is None or end is None:
            raise R.TrackPStop(f"unit lacks complete lease record: {directory}")
        if any((e.get("tasl7_driver") or {}).get("boot_id") != boot_id for e in events):
            raise R.TrackPStop(f"unit lease driver state missing or boot ID mismatch: {directory}")
        if events[0].get("monotonic_s") != start or events[1].get("monotonic_s") != end:
            raise R.TrackPStop(f"unit manifest and lease log disagree: {directory}")
    elif start is not None:
        raise R.TrackPStop("CPU-only selection unexpectedly took the GPU lease")
    emit(journal, {"event": "unit_complete", "label": label, "base": base, "unit": name,
                   "utc": R.utcnow(), "gpu_seconds_total": budget.used})
    return report


def run_base(root, journal, boot, budget, label, base, short):
    from r1.c3.train.registry import reverify
    budget.require_available()
    bad = reverify(R.REPO / "r1/c3/train/registry.yaml")
    if bad:
        raise R.TrackPStop(f"registered model files mismatch before {base}: {bad[:5]}")
    parent = root / label / base
    for lr in ("1e-05", "3e-05", "0.0001"):
        args = ["e0", "--base", base, "--stage", "screen", "--variant", "fresh", "--lr", lr]
        if short:
            args += ["--steps", "200"]
        run_unit(root, journal, boot, budget, label, base, "screen_lr" + lr, args)
    args = ["e0-select", "--runs", *(str(parent / ("screen_lr" + lr)) for lr in ("1e-05", "3e-05", "0.0001"))]
    selection = run_unit(root, journal, boot, budget, label, base, "select", args, gpu=False)
    lr = str(selection["selected"]["lr"])
    for name, variant, hard in (("final", "fresh", False), ("hard", "fresh", True), ("native", "native", False)):
        args = ["e0", "--base", base, "--stage", "final", "--variant", variant, "--lr", lr]
        if hard:
            args += ["--hard"]
        if short:
            args += ["--steps", "400"]
        run_unit(root, journal, boot, budget, label, base, name, args)
    run_unit(root, journal, boot, budget, label, base, "probes",
             ["probes", "--base", base, "--head-form", "linear12", "--budget", "--n-probe",
              "32" if short else "100", "--load", str(parent / "final" / "saved")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    args = ap.parse_args()
    if socket.gethostname().lower().split(".")[0] != "tasl-7":
        raise R.TrackPStop("P.3a is authorized on TASL-7 only")
    if R.authorization_note("p3a") is None:
        raise R.TrackPStop("P.3a authorization missing")
    if args.root.exists():
        raise R.TrackPStop("campaign root already exists; preserve it and STOP")
    if not args.root.is_absolute():
        raise R.TrackPStop("campaign root must be absolute")
    pins = verify_pins()
    boot = R.tasl7_driver_snapshot()["boot_id"]
    args.root.mkdir(parents=True)
    journal = args.root / "journal.jsonl"
    budget = GPUBudget()
    try:
        emit(journal, {"event": "campaign_start", "utc": R.utcnow(), "boot_id": boot,
                       "pins": pins, "gpu_limit_seconds": LIMIT_SECONDS})
        run_base(args.root, journal, boot, budget, "DRYRUN", "kev-0.8b", True)
        for base in BASES:
            run_base(args.root, journal, boot, budget, "EVIDENCE", base, False)
        emit(journal, {"event": "complete", "utc": R.utcnow(), "gpu_seconds_total": budget.used})
    except Exception as exc:
        emit(journal, {"event": "STOP", "utc": R.utcnow(), "error": str(exc),
                       "gpu_seconds_total": budget.used,
                       "unobserved_lease_upper_s": budget.unobserved_lease_upper_s})
        raise


if __name__ == "__main__":
    main()
