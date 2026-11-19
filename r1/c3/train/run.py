"""Track P run plumbing: config check, evaluation-seed guard, GPU lease, run manifest (RUNBOOK Track P 1.6, §0).

ENGINEERING_ONLY; AI-assisted (Claude).

* **Config.** ``load_config`` refuses any ``TODO_VERIFY*`` value (dotted paths listed; ``comment`` ignored).
* **Seeds.** Training labels come only from audit seeds 7001–7005 (``*_train`` columns). ``guard_rows`` refuses
  evaluation columns (``*_eval``, seeds 7006–7010) unless the caller is the P.4 final evaluation *and* its
  authorization note exists (``docs/r1/authorizations/trackp_p4_<date>.md``).
* **GPU lease (R1-PORTAL-SCHEDULE).** ``gpu_lease`` checks the Track X evidence marker
  ``~/r1_locks/trackx_evidence.active`` (present while B1 or B2 runs; R1-TRACKX-MARKER, 26 Oct), STATUS on
  ``origin/main`` for a running Track X evidence phase (kept as a second check), that ``nvidia-smi`` lists no
  compute process, then holds ``~/r1_locks/gpu0.lock`` with ``flock``
  semantics (``fcntl.flock``, non-blocking — the same lock ``flock -n`` takes) and logs start/end.
* **Manifest.** ``run_manifest`` records base revision, adapter/heads sha256, data-manifest hash, seed, git commits
  of both repos, the GPU-lease log, the evidence label and the config digest.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import socket
import subprocess
import time
from pathlib import Path
from typing import Iterable, Iterator

from r1.harness import REPO, harness_root

PLACEHOLDER = "TODO_VERIFY"
EVIDENCE_LABELS = ("ENGINEERING_ONLY", "DRYRUN", "EVIDENCE")
TRAIN_SEEDS = (7001, 7002, 7003, 7004, 7005)
EVAL_SEEDS = (7006, 7007, 7008, 7009, 7010)
EVAL_COLUMNS = re.compile(r"(^|_)eval($|_)|^y_eval|^z_eval|^u_eval|^mu_eval|(^|\D)70(0[6-9]|10)(\D|$)")
LOCK_PATH = Path.home() / "r1_locks" / "gpu0.lock"
TRACKX_MARKER = Path.home() / "r1_locks" / "trackx_evidence.active"   # exists while Track X B1 or B2 runs
LEASE_LOG = Path.home() / "r1_trackp" / "runs" / "gpu_lease_log.jsonl"
AUTH_DIR = REPO / "docs" / "r1" / "authorizations"
# Track X evidence phases (PORTAL_EXAM_RUNBOOK B1/B2) in STATUS.md (newest entry first). The newest heading that
# names Track X/exam B1 or B2 decides: running/started/launched/in progress -> running, unless it also says
# accepted/stopped/done/complete/finished. Proposed marker for the Track X agent: "## <date> — Track X B1 running" /
# "... B1 done". The flock and nvidia-smi checks protect a running job regardless of STATUS.
TRACK_X_HEADING = re.compile(r"^##.*\b(Track X|exam)\b.*\b(B1|B2)\b.*$", re.I | re.M)
RUNNING_WORDS = re.compile(r"\b(running|started|launched|in progress)\b", re.I)
ENDED_WORDS = re.compile(r"\b(accepted|stopped|done|complete|completed|finished)\b", re.I)


class TrackPStop(RuntimeError):
    """A runbook STOP: the run must not continue."""


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------- config

def placeholders(obj, path: str = "") -> list[str]:
    """Dotted paths of every unresolved ``TODO_VERIFY*`` value (the free-text ``comment`` keys are ignored)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "comment":
                continue
            out += placeholders(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += placeholders(v, f"{path}[{i}]")
    elif isinstance(obj, str) and obj.startswith(PLACEHOLDER):
        out.append(path)
    return out


def load_config(path: Path | str, allow_placeholders: bool = False) -> dict:
    cfg = json.loads(Path(path).read_text())
    left = placeholders(cfg)
    if left and not allow_placeholders:
        raise TrackPStop(f"config {path} still holds {PLACEHOLDER}* values: {', '.join(left)}")
    return cfg


def config_digest(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()


# ---------------------------------------------------------------------- seeds

def authorization_note(phase: str) -> Path | None:
    notes = sorted(AUTH_DIR.glob(f"trackp_{phase}_*.md")) if AUTH_DIR.is_dir() else []
    return notes[-1] if notes else None


def _keys(obj, depth: int = 0) -> Iterator[str]:
    """Every key of a row, nested dicts and a DecisionPrompt's ``meta`` included."""
    if depth > 6:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _keys(v, depth + 1)
    elif hasattr(obj, "meta") and isinstance(getattr(obj, "meta"), dict):
        yield from _keys(obj.meta, depth + 1)


def guard_rows(rows: Iterable[dict], *, purpose: str) -> list[dict]:
    """Refuse evaluation-seed columns unless ``purpose == "p4_final_eval"`` with its authorization note present."""
    rows = list(rows)
    eval_cols = sorted({k for r in rows for k in _keys(r) if EVAL_COLUMNS.search(k)})
    if not eval_cols:
        return rows
    if purpose != "p4_final_eval":
        raise TrackPStop(f"evaluation-seed columns {eval_cols} offered to {purpose!r}; seeds 7006-7010 are read only "
                         "in the P.4 final evaluation")
    if authorization_note("p4") is None:
        raise TrackPStop("P.4 final evaluation needs docs/r1/authorizations/trackp_p4_<date>.md")
    return rows


def strip_eval_columns(rows: Iterable[dict]) -> list[dict]:
    """Training view of a label table: every evaluation-seed column removed."""
    return [{k: v for k, v in r.items() if not EVAL_COLUMNS.search(k)} for r in rows]


# ---------------------------------------------------------------------- GPU lease

def track_x_running(status_text: str | None = None) -> bool:
    if status_text is None:
        subprocess.run(["git", "-C", str(REPO), "fetch", "-q", "origin", "main"], check=False, timeout=60)
        res = subprocess.run(["git", "-C", str(REPO), "show", "origin/main:docs/r1/STATUS.md"],
                             capture_output=True, text=True, timeout=60)
        if res.returncode != 0:
            raise TrackPStop("cannot read STATUS.md on origin/main to check for a Track X evidence phase")
        status_text = res.stdout
    m = TRACK_X_HEADING.search(status_text)
    return bool(m and RUNNING_WORDS.search(m.group(0)) and not ENDED_WORDS.search(m.group(0)))


def foreign_compute_processes() -> list[str]:
    res = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
                         capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise TrackPStop(f"nvidia-smi failed: {res.stderr.strip()}")
    mine = os.getpid()
    return [ln for ln in res.stdout.splitlines() if ln.strip() and int(ln.split(",")[0]) != mine]


def tasl7_driver_snapshot() -> dict:
    """Fail closed and record per-job host and driver state required by P.3a."""
    try:
        proc = Path("/proc/driver/nvidia/version").read_text().strip()
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        uptime = subprocess.run(["uptime"], capture_output=True, text=True, check=True, timeout=30).stdout.strip()
        smi = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, check=True, timeout=30).stdout.strip().splitlines()
        pkg = subprocess.run(["dpkg-query", "-W", "-f=${Package} ${Version}\n", "nvidia-utils-580", "libnvidia-compute-580"],
                             capture_output=True, text=True, check=True, timeout=30).stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError) as exc:
        raise TrackPStop(f"TASL-7 driver snapshot failed: {exc}") from exc
    match = re.search(r"Kernel Module\s+(\d+\.\d+\.\d+)", proc)
    if not match or not smi or any(v.strip() != match.group(1) for v in smi):
        raise TrackPStop("TASL-7 NVIDIA kernel/user driver mismatch or empty nvidia-smi result")
    if {line.split()[0] for line in pkg if line.split()} != {"nvidia-utils-580", "libnvidia-compute-580"} or any(len(line.split()) != 2 or line.split()[1].split("-")[0] != match.group(1) for line in pkg):
        raise TrackPStop("TASL-7 NVIDIA installed package/kernel driver mismatch")
    return {"uptime": uptime, "nvidia_kernel_module": proc, "nvidia_smi_driver": smi,
            "nvidia_packages": pkg, "boot_id": boot_id}


def host_driver_snapshot(expected_driver: str | None = None) -> dict:
    """Host-parameterized driver/boot snapshot for the reviewed P.3a attempt-2 hosts (R1-TRACKP-D2).

    TASL-7 keeps the unchanged ``tasl7_driver_snapshot`` (including its 580 package assertions). Other reviewed
    hosts (TASL-2, driver ``535.309.01``) read the same ``/proc`` + ``nvidia-smi`` primitives, require kernel/user
    driver agreement and — when given — the caller's expected driver pin. The driver-branch package inventory is
    recorded best-effort because the Ubuntu package names are branch-specific (e.g. ``nvidia-utils-535``).
    """
    host = socket.gethostname().lower().split(".")[0]
    if host == "tasl-7":
        snapshot = tasl7_driver_snapshot()
        drivers = [str(value).strip() for value in snapshot.get("nvidia_smi_driver") or []]
        if expected_driver is not None and (not drivers or any(value != expected_driver for value in drivers)):
            raise TrackPStop(f"NVIDIA driver {drivers} is not the reviewed {expected_driver} on TASL-7")
        return snapshot
    return _generic_driver_snapshot(host, expected_driver)


def _generic_driver_snapshot(host: str, expected_driver: str | None) -> dict:
    """Portal-host driver snapshot: kernel/user driver agreement + the reviewed expected driver; no 580-only probe."""
    try:
        proc = Path("/proc/driver/nvidia/version").read_text().strip()
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        uptime = subprocess.run(["uptime"], capture_output=True, text=True, check=True, timeout=30).stdout.strip()
        smi = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, check=True, timeout=30).stdout.strip().splitlines()
    except (OSError, subprocess.SubprocessError) as exc:
        raise TrackPStop(f"{host} driver snapshot failed: {exc}") from exc
    match = re.search(r"Kernel Module\s+(\d+\.\d+\.\d+)", proc)
    if not match or not smi or any(value.strip() != match.group(1) for value in smi):
        raise TrackPStop(f"{host} NVIDIA kernel/user driver mismatch or empty nvidia-smi result")
    driver = match.group(1)
    if expected_driver is not None and driver != expected_driver:
        raise TrackPStop(f"NVIDIA driver {driver} is not the reviewed {expected_driver} on {host}")
    branch = driver.split(".")[0]
    package_names = (f"nvidia-utils-{branch}", f"libnvidia-compute-{branch}")
    packages, packages_checked = [], False
    try:
        res = subprocess.run(["dpkg-query", "-W", "-f=${Package} ${Version}\n", *package_names],
                             capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            packages = [line for line in res.stdout.strip().splitlines() if line.strip()]
            packages_checked = True
    except (OSError, subprocess.SubprocessError):
        packages = []
    if packages_checked:
        seen = {line.split()[0] for line in packages if line.split()}
        if seen != set(package_names) or any(len(line.split()) != 2 or line.split()[1].split("-")[0] != driver
                                             for line in packages):
            raise TrackPStop(f"{host} NVIDIA installed package/kernel driver mismatch")
    return {"uptime": uptime, "nvidia_kernel_module": proc, "nvidia_smi_driver": smi,
            "nvidia_packages": packages, "nvidia_packages_checked": packages_checked,
            "nvidia_packages_expected": list(package_names), "boot_id": boot_id,
            "expected_driver": expected_driver, "driver_branch": branch, "hostname": socket.gethostname()}


def driver_record(tiny: bool, a3_short: bool) -> dict:
    """Host-aware driver/boot record for a run manifest (R1-TRACKP-D2 host contract).

    TASL-7 keeps the unchanged ``tasl7_driver`` record. The attempt-2 probes path (``--a3-short``) on another
    reviewed host (TASL-2) records the generic ``host_driver`` snapshot that the probes-only supervisor verifies;
    every other portal run records no driver snapshot, exactly as before.
    """
    if tiny:
        return {}
    if socket.gethostname().lower().split(".")[0] == "tasl-7":
        return {"tasl7_driver": tasl7_driver_snapshot()}
    if a3_short:
        return {"host_driver": host_driver_snapshot()}
    return {}


def _log_lease(event: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


@contextlib.contextmanager
def gpu_lease(job: str, *, lock_path: Path = LOCK_PATH, log_path: Path = LEASE_LOG, run_log: list | None = None,
              status_text: str | None = None, check_processes: bool = True,
              marker_path: Path = TRACKX_MARKER, record_host_driver: bool = False) -> Iterator[dict]:
    """Hold the GPU lease for one job (R1-PORTAL-SCHEDULE). Raises TrackPStop if it may not start."""
    portal_guard = socket.gethostname().lower().split(".")[0] != "tasl-7"
    if portal_guard and marker_path.exists():
        raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
    if portal_guard and track_x_running(status_text):
        raise TrackPStop("a Track X evidence phase (B1/B2) is running on the card: do not start")
    if check_processes:
        other = foreign_compute_processes()
        if other:
            raise TrackPStop(f"another compute process holds the GPU: {other}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "a")
    acquired_monotonic = None
    end_logged = False
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired_monotonic = time.monotonic()
            _log_lease({"event": "acquired", "job": job, "pid": os.getpid(), "utc": utcnow(),
                        "monotonic_s": acquired_monotonic, "trackx_marker": "pending checks"}, log_path)
        except BlockingIOError:
            raise TrackPStop(f"GPU lock {lock_path} is held by another job") from None
        if portal_guard and marker_path.exists():   # re-read under the lock on the portal
            raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
        if check_processes:
            other = foreign_compute_processes()
            if other:
                raise TrackPStop(f"another compute process holds the GPU after lock acquisition: {other}")
        initial_driver = tasl7_driver_snapshot() if not portal_guard and check_processes else None
        initial_host_driver = (host_driver_snapshot() if portal_guard and check_processes and record_host_driver
                               else None)
        start = {"event": "start", "job": job, "pid": os.getpid(), "utc": utcnow(), "monotonic_s": acquired_monotonic,
                 "trackx_marker": f"absent: {marker_path}" if portal_guard else "not applicable on TASL-7",
                 "tasl7_driver": initial_driver}
        if initial_host_driver is not None:
            start["host_driver"] = initial_host_driver
        _log_lease(start, log_path)
        if run_log is not None:
            run_log.append(start)
        lease = {"start": start["utc"], "job": job}
        try:
            yield lease
        finally:
            final_driver = tasl7_driver_snapshot() if initial_driver is not None else None
            if initial_driver is not None and final_driver["boot_id"] != initial_driver["boot_id"]:
                raise TrackPStop("TASL-7 boot ID changed during the job")
            final_host_driver = host_driver_snapshot() if initial_host_driver is not None else None
            if initial_host_driver is not None and final_host_driver["boot_id"] != initial_host_driver["boot_id"]:
                raise TrackPStop("boot ID changed during the job")
            # Stamp just after actual unlock; includes all time holding the exclusive lease.
            fcntl.flock(fh, fcntl.LOCK_UN)
            end = {"event": "end", "job": job, "pid": os.getpid(), "utc": utcnow(), "monotonic_s": time.monotonic(),
                   "tasl7_driver": final_driver}
            if final_host_driver is not None:
                end["host_driver"] = final_host_driver
            _log_lease(end, log_path)
            end_logged = True
            if run_log is not None:
                run_log.append(end)
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        if acquired_monotonic is not None and not end_logged:
            failure_end = {"event": "end", "job": job, "pid": os.getpid(), "utc": utcnow(),
                           "monotonic_s": time.monotonic(), "status": "failed_before_normal_release"}
            try:
                _log_lease(failure_end, log_path)
                if run_log is not None:
                    run_log.append(failure_end)
            finally:
                fh.close()
        else:
            fh.close()


# ---------------------------------------------------------------------- manifest

def git_commit(repo: Path) -> dict:
    def g(*a):
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout.strip()
    raw = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "-z", "--untracked-files=no"],
                         capture_output=True, text=True).stdout   # unstripped: "XY path" entries, NUL-separated
    dirty = [e[3:] for e in raw.split("\0") if len(e) > 3]
    return {"path": str(repo), "commit": g("rev-parse", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(dirty), "dirty_files": dirty}


def data_manifest_hash(rows: Iterable[dict]) -> str:
    """Hash of the training data as used (row order and content; DecisionPrompt objects by their fields)."""
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, default=lambda o: getattr(o, "__dict__", str(o))).encode())
        h.update(b"\n")
    return h.hexdigest()


CODE_PACKAGES = {"kev": "kev", "laya": "laya", "startlux_decide": "startlux_decide"}


def environment_record() -> dict:
    """Library versions and, per code-pinned package, the commit pip recorded and the git state of the directory the
    import actually resolves to (R1-ENV-PIN)."""
    import importlib
    import importlib.metadata as md
    out: dict = {"packages": {}}
    for lib in ("torch", "transformers", "peft"):
        try:
            out[lib] = importlib.import_module(lib).__version__
        except ImportError:
            out[lib] = None
    for dist, mod in CODE_PACKAGES.items():
        rec: dict = {}
        try:
            direct = md.distribution(dist).read_text("direct_url.json")
            rec["pip_commit"] = (json.loads(direct).get("vcs_info") or {}).get("commit_id") if direct else None
        except md.PackageNotFoundError:
            rec["pip_commit"] = None
        try:
            src = Path(importlib.import_module(mod).__file__).resolve().parent
            rec["path"] = str(src)
            if (src.parent / ".git").exists():
                rec["git"] = git_commit(src.parent)
        except ImportError:
            rec["path"] = None
        out["packages"][dist] = rec
    return out


def check_environment(cfg: dict, env: dict | None = None) -> dict:
    """STOP unless torch and the code pins are the configured ones (R1-ENV-PIN): pip's recorded commit, and the
    imported checkout (if it is one) at that commit with a clean tree."""
    env = environment_record() if env is None else env
    want_torch = cfg["venv"]["torch"]
    if env["torch"] != want_torch:
        raise TrackPStop(f"torch {env['torch']} is not the pinned {want_torch}")
    for dist, pin in cfg["code_pins"].items():
        commit = pin.split("@")[-1]
        rec = env["packages"].get(dist) or {}
        if rec.get("pip_commit") != commit:
            raise TrackPStop(f"{dist}: installed commit {rec.get('pip_commit')} is not the pinned {commit}")
        g = rec.get("git")
        if g and (g["commit"] != commit or g["dirty"]):
            raise TrackPStop(f"{dist}: imported from {rec['path']} at {g['commit']} (dirty={g['dirty']}), "
                             f"not the pinned {commit}")
    return env


def host_record() -> dict:
    """Host and GPU of the run (R1-ADA-OVERFLOW: every manifest records them; one GPU type per comparison table)."""
    gpus = None
    try:
        res = subprocess.run(["nvidia-smi", "--query-gpu=name,compute_cap,driver_version,uuid",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            gpus = [dict(zip(("name", "compute_capability", "driver", "uuid"), (x.strip() for x in ln.split(","))))
                    for ln in res.stdout.splitlines() if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    device = None   # the card this process uses, by UUID (nvidia-smi and CUDA may order cards differently)
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(torch.cuda.current_device())
            device = {"name": props.name, "uuid": f"GPU-{props.uuid}",
                      "compute_capability": f"{props.major}.{props.minor}"}
    except (ImportError, RuntimeError, AttributeError):
        pass
    return {"hostname": socket.gethostname(), "gpus": gpus, "device": device,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "cuda_device_order": os.environ.get("CUDA_DEVICE_ORDER")}


def run_manifest(*, subcommand: str, evidence: str, cfg: dict, seed: int, base: dict, model_files: dict,
                 data_hash: str, lease_log: list, extra: dict | None = None) -> dict:
    if evidence not in EVIDENCE_LABELS:
        raise ValueError(f"evidence label must be one of {EVIDENCE_LABELS}")
    return {"schema": "trackp_run_manifest/v1", "created_utc": utcnow(), "subcommand": subcommand,
            "evidence_label": evidence, "seed": seed, "base": base, "model_files_sha256": model_files,
            "data_manifest_sha256": data_hash, "config_sha256": config_digest(cfg),
            "git": {"paper": git_commit(REPO), "harness": git_commit(harness_root())},
            "environment": environment_record(), "host": host_record(),
            "gpu_lease": lease_log, **(extra or {})}
