"""Track P run plumbing: config check, evaluation-seed guard, GPU lease, run manifest (RUNBOOK Track P 1.6, §0).

ENGINEERING_ONLY; AI-assisted (Claude).

* **Config.** ``load_config`` refuses any ``TODO_VERIFY*`` value (dotted paths listed; ``comment`` ignored).
* **Seeds.** Training labels come only from audit seeds 7001–7005 (``*_train`` columns). ``guard_rows`` refuses
  evaluation columns (``*_eval``, seeds 7006–7010) unless the caller is the P.4 final evaluation *and* its
  authorization note exists (``docs/r1/authorizations/trackp_p4_<date>.md``).
* **GPU lease (R1-PORTAL-SCHEDULE, R1-CARD-SHARE).** Keep the Track X marker and schedule guards. For a local
  lease, resolve the selected card, hold its ``gpu<index>.lock``, check that card's occupancy, and expose only
  its UUID to CUDA. Log the other compute processes' count and memory on that card at start and end.
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
import sys
from pathlib import Path
from typing import Iterable, Iterator

from r1.harness import REPO, harness_root

PLACEHOLDER = "TODO_VERIFY"
EVIDENCE_LABELS = ("ENGINEERING_ONLY", "DRYRUN", "EVIDENCE")
TRAIN_SEEDS = (7001, 7002, 7003, 7004, 7005)
EVAL_SEEDS = (7006, 7007, 7008, 7009, 7010)
EVAL_COLUMNS = re.compile(r"(^|_)eval($|_)|^y_eval|^z_eval|^u_eval|^mu_eval|(^|\D)70(0[6-9]|10)(\D|$)|^(delta_true|delta_audit_all|se_audit|candidate_metrics|incumbent_metrics)$")
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
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _keys(v, depth + 1)
    elif hasattr(obj, "meta") and isinstance(getattr(obj, "meta"), dict):
        yield from _keys(obj.meta, depth + 1)


def guard_rows(rows: Iterable[dict], *, purpose: str) -> list[dict]:
    """Refuse evaluation-seed columns unless ``purpose == "p4_final_eval"`` with its authorization note present."""
    rows = list(rows)
    from r1.c3.evidence_boundary import is_identifiable_sweep_evidence
    if any(is_identifiable_sweep_evidence(row) for row in rows):
        if purpose != 'p4_final_eval':
            raise TrackPStop('identifiable C3 sweep EVIDENCE rows require a verified label-only training boundary')
        if authorization_note('p4') is None:
            raise TrackPStop('P.4 final evaluation needs docs/r1/authorizations/trackp_p4_<date>.md')
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


def _nvidia_rows(*args: str) -> list[list[str]]:
    try:
        res = subprocess.run(["nvidia-smi", *args, "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TrackPStop(f"nvidia-smi unavailable: {type(exc).__name__}") from exc
    if res.returncode != 0:
        raise TrackPStop(f"nvidia-smi {args[0]} failed (exit {res.returncode})")
    return [[field.strip() for field in line.split(",")] for line in res.stdout.splitlines() if line.strip()]


def _leased_card(gpu: str | None, visible: str | None) -> tuple[int, str]:
    selector = visible if gpu is None else gpu
    query = ["--query-gpu=index,uuid"]
    if selector is not None and not re.fullmatch(r"(?:0|[1-9][0-9]*|GPU-[0-9a-fA-F-]+)", selector):
        raise TrackPStop("select exactly one GPU by physical index or UUID")
    # A single device exposed by a scheduler/container may have CUDA ordinal 0 and a different NVML index.
    only_local_ordinal = gpu is None and visible == "0"
    rows = _nvidia_rows(*query) if selector is None or only_local_ordinal else []
    if selector is not None and len(rows) != 1:
        rows = _nvidia_rows(*query, f"--id={selector}")
        only_local_ordinal = False
    if len(rows) != 1 or len(rows[0]) != 2:
        raise TrackPStop("select exactly one GPU by physical index or UUID")
    index, uuid = rows[0]
    if not index.isascii() or not index.isdecimal() or not re.fullmatch(r"GPU-[0-9a-fA-F-]+", uuid):
        raise TrackPStop("nvidia-smi did not identify the selected GPU")
    if selector is not None and not only_local_ordinal and selector not in (index, uuid):
        raise TrackPStop("nvidia-smi returned a different GPU than selected")
    if visible is not None and not only_local_ordinal and visible not in (index, uuid):
        raise TrackPStop("selected GPU disagrees with CUDA_VISIBLE_DEVICES")
    return int(index), uuid


def foreign_compute_processes(uuid: str) -> dict:
    """Selected card only. Exclude our own process and omit all process identities."""
    count, memory_mib = 0, 0
    known_memory = True
    for row in _nvidia_rows("--query-compute-apps=gpu_uuid,pid,used_memory"):
        if row[0] != uuid:
            continue
        if len(row) != 3 or not row[1].isdecimal():
            raise TrackPStop("nvidia-smi returned an invalid process record for the selected GPU")
        if int(row[1]) == os.getpid():
            continue
        count += 1
        if row[2].isdecimal():
            memory_mib += int(row[2])
        else:
            known_memory = False
    return {"count": count, "memory_mib": memory_mib if known_memory else None}


def _log_lease(event: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


@contextlib.contextmanager
def gpu_lease(job: str, *, lock_path: Path = LOCK_PATH, log_path: Path = LEASE_LOG, run_log: list | None = None,
              status_text: str | None = None, check_processes: bool = True,
              marker_path: Path = TRACKX_MARKER, gpu: str | None = None) -> Iterator[dict]:
    """Hold one empty card before CUDA initializes, or a job-local lock under the checked P.4 outer lease."""
    if marker_path.exists():
        raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
    if track_x_running(status_text):
        raise TrackPStop("a Track X evidence phase (B1/B2) is running on the card: do not start")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    card = {}
    if check_processes:
        index, uuid = _leased_card(gpu, visible)
        torch = sys.modules.get("torch")
        if torch is not None and torch.cuda.is_initialized():
            if torch.cuda.device_count() != 1 or f"GPU-{torch.cuda.get_device_properties(0).uuid}" != uuid:
                raise TrackPStop("CUDA already initialized with a different GPU selection")
        lock_path = lock_path.with_name(f"gpu{index}.lock")
        card = {"gpu_index": index, "gpu_uuid": uuid}
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise TrackPStop(f"GPU lock {lock_path} is held by another job") from None
        if marker_path.exists():   # re-read under the lock: a B1/B2 start between the check and the lock wins
            raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
        start = {"event": "start", "job": job, "pid": os.getpid(), "utc": utcnow(),
                 "trackx_marker": f"absent: {marker_path}", **card}
        if card:
            start["other_processes"] = foreign_compute_processes(uuid)
            if start["other_processes"]["count"]:
                raise TrackPStop(f"GPU {index} ({uuid}) needs to be empty: {start['other_processes']}")
        _log_lease(start, log_path)
        if run_log is not None:
            run_log.append(start)
        if card:
            os.environ["CUDA_VISIBLE_DEVICES"] = uuid
        try:
            yield {"start": start["utc"], "job": job, **card}
        finally:
            end = {"event": "end", "job": job, "pid": os.getpid(), "utc": utcnow(), **card}
            if card:
                if visible is None:
                    os.environ.pop("CUDA_VISIBLE_DEVICES", None)
                else:
                    os.environ["CUDA_VISIBLE_DEVICES"] = visible
                try:
                    end["other_processes"] = foreign_compute_processes(uuid)
                except TrackPStop as exc:
                    end["other_processes"] = {"error": str(exc)}
            _log_lease(end, log_path)
            if run_log is not None:
                run_log.append(end)


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
    host = host_record()
    for event in lease_log:
        if event.get("event") == "start" and event.get("gpu_uuid"):
            host["cuda_visible_devices"] = event["gpu_uuid"]
            break
    return {"schema": "trackp_run_manifest/v1", "created_utc": utcnow(), "subcommand": subcommand,
            "evidence_label": evidence, "seed": seed, "base": base, "model_files_sha256": model_files,
            "data_manifest_sha256": data_hash, "config_sha256": config_digest(cfg),
            "git": {"paper": git_commit(REPO), "harness": git_commit(harness_root())},
            "environment": environment_record(), "host": host,
            "gpu_lease": lease_log, **(extra or {})}
