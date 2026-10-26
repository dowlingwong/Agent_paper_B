"""Track P run plumbing: config check, evaluation-seed guard, GPU lease, run manifest (RUNBOOK Track P 1.6, §0).

ENGINEERING_ONLY; AI-assisted (Claude).

* **Config.** ``load_config`` refuses any ``TODO_VERIFY*`` value (dotted paths listed; ``comment`` ignored).
* **Seeds.** Training labels come only from audit seeds 7001–7005 (``*_train`` columns). ``guard_rows`` refuses
  evaluation columns (``*_eval``, seeds 7006–7010) unless the caller is the P.4 final evaluation *and* its
  authorization note exists (``docs/r1/authorizations/trackp_p4_<date>.md``).
* **GPU lease (R1-PORTAL-SCHEDULE).** ``gpu_lease`` checks STATUS on ``origin/main`` for a running Track X evidence
  phase, that ``nvidia-smi`` lists no compute process, then holds ``~/r1_locks/gpu0.lock`` with ``flock``
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
import subprocess
from pathlib import Path
from typing import Iterable, Iterator

from r1.harness import REPO, harness_root

PLACEHOLDER = "TODO_VERIFY"
EVIDENCE_LABELS = ("ENGINEERING_ONLY", "DRYRUN", "EVIDENCE")
TRAIN_SEEDS = (7001, 7002, 7003, 7004, 7005)
EVAL_SEEDS = (7006, 7007, 7008, 7009, 7010)
EVAL_COLUMNS = re.compile(r"(^|_)eval($|_)|^y_eval|^z_eval|^u_eval|^mu_eval")
LOCK_PATH = Path.home() / "r1_locks" / "gpu0.lock"
LEASE_LOG = Path.home() / "r1_trackp" / "runs" / "gpu_lease_log.jsonl"
AUTH_DIR = REPO / "docs" / "r1" / "authorizations"
# STATUS headings that mark a running Track X evidence phase (PORTAL_EXAM_RUNBOOK B1/B2)
TRACK_X_RUNNING = re.compile(r"^##.*\b(B1|B2)\b.*\b(running|started|in progress)\b", re.I | re.M)


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


def guard_rows(rows: Iterable[dict], *, purpose: str) -> list[dict]:
    """Refuse evaluation-seed columns unless ``purpose == "p4_final_eval"`` with its authorization note present."""
    rows = list(rows)
    eval_cols = sorted({k for r in rows for k in r if EVAL_COLUMNS.search(k)})
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
    return bool(TRACK_X_RUNNING.search(status_text))


def foreign_compute_processes() -> list[str]:
    res = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
                         capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise TrackPStop(f"nvidia-smi failed: {res.stderr.strip()}")
    mine = os.getpid()
    return [ln for ln in res.stdout.splitlines() if ln.strip() and int(ln.split(",")[0]) != mine]


def _log_lease(event: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


@contextlib.contextmanager
def gpu_lease(job: str, *, lock_path: Path = LOCK_PATH, log_path: Path = LEASE_LOG, run_log: list | None = None,
              status_text: str | None = None, check_processes: bool = True) -> Iterator[dict]:
    """Hold the GPU lease for one job (R1-PORTAL-SCHEDULE). Raises TrackPStop if it may not start."""
    if track_x_running(status_text):
        raise TrackPStop("a Track X evidence phase (B1/B2) is running on the card: do not start")
    if check_processes:
        other = foreign_compute_processes()
        if other:
            raise TrackPStop(f"another compute process holds the GPU: {other}")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "a")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise TrackPStop(f"GPU lock {lock_path} is held by another job") from None
        start = {"event": "start", "job": job, "pid": os.getpid(), "utc": utcnow()}
        _log_lease(start, log_path)
        if run_log is not None:
            run_log.append(start)
        lease = {"start": start["utc"], "job": job}
        try:
            yield lease
        finally:
            end = {"event": "end", "job": job, "pid": os.getpid(), "utc": utcnow()}
            _log_lease(end, log_path)
            if run_log is not None:
                run_log.append(end)
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


# ---------------------------------------------------------------------- manifest

def git_commit(repo: Path) -> dict:
    def g(*a):
        return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True).stdout.strip()
    return {"path": str(repo), "commit": g("rev-parse", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(g("status", "--porcelain", "--untracked-files=no"))}


def data_manifest_hash(rows: Iterable[dict]) -> str:
    """Hash of the training data as used (row order and content; DecisionPrompt objects by their fields)."""
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True, default=lambda o: getattr(o, "__dict__", str(o))).encode())
        h.update(b"\n")
    return h.hexdigest()


def run_manifest(*, subcommand: str, evidence: str, cfg: dict, seed: int, base: dict, model_files: dict,
                 data_hash: str, lease_log: list, extra: dict | None = None) -> dict:
    if evidence not in EVIDENCE_LABELS:
        raise ValueError(f"evidence label must be one of {EVIDENCE_LABELS}")
    return {"schema": "trackp_run_manifest/v1", "created_utc": utcnow(), "subcommand": subcommand,
            "evidence_label": evidence, "seed": seed, "base": base, "model_files_sha256": model_files,
            "data_manifest_sha256": data_hash, "config_sha256": config_digest(cfg),
            "git": {"paper": git_commit(REPO), "harness": git_commit(harness_root())},
            "gpu_lease": lease_log, **(extra or {})}
