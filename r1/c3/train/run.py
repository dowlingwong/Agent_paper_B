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
import subprocess
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


def _log_lease(event: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


@contextlib.contextmanager
def gpu_lease(job: str, *, lock_path: Path = LOCK_PATH, log_path: Path = LEASE_LOG, run_log: list | None = None,
              status_text: str | None = None, check_processes: bool = True,
              marker_path: Path = TRACKX_MARKER) -> Iterator[dict]:
    """Hold the GPU lease for one job (R1-PORTAL-SCHEDULE). Raises TrackPStop if it may not start."""
    if marker_path.exists():
        raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
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
        if marker_path.exists():   # re-read under the lock: a B1/B2 start between the check and the lock wins
            raise TrackPStop(f"Track X evidence marker {marker_path} exists (B1/B2 running): do not start")
        start = {"event": "start", "job": job, "pid": os.getpid(), "utc": utcnow(),
                 "trackx_marker": f"absent: {marker_path}"}
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
    dirty = [ln[3:] for ln in g("status", "--porcelain", "--untracked-files=no").splitlines() if ln.strip()]
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


def run_manifest(*, subcommand: str, evidence: str, cfg: dict, seed: int, base: dict, model_files: dict,
                 data_hash: str, lease_log: list, extra: dict | None = None) -> dict:
    if evidence not in EVIDENCE_LABELS:
        raise ValueError(f"evidence label must be one of {EVIDENCE_LABELS}")
    return {"schema": "trackp_run_manifest/v1", "created_utc": utcnow(), "subcommand": subcommand,
            "evidence_label": evidence, "seed": seed, "base": base, "model_files_sha256": model_files,
            "data_manifest_sha256": data_hash, "config_sha256": config_digest(cfg),
            "git": {"paper": git_commit(REPO), "harness": git_commit(harness_root())},
            "environment": environment_record(),
            "gpu_lease": lease_log, **(extra or {})}
