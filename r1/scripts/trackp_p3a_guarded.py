"""One-shot P.3a supervisor. AI-assisted; DRYRUN then EVIDENCE; never resumes.

Attempt 1 (``p3a_operator_20261027``) ran the multi-base campaign below up to the interrupted
``qwen3.5-4b-base/probes`` unit (CUDA OOM in the descriptive A3 2k/8k loop). Attempt 2 runs **probes only** in a new
root, under the reviewed A3-short code delta, with attempt-1 provenance bound read-only and the 45-h lease clock
(36.318161 h used) sealed from attempt 1's journal STOP. ``--probes-only`` selects that path; without it the
attempt-1 campaign code path is unchanged. No bare ``trackp.py probes`` command is used by either path.
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import shutil
import signal
import socket
import subprocess
import sys
import time

from r1.c3.train import run as R

BASES = ("kev-0.8b", "kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base",
         "laya", "startlux-0.8b", "startlux-2b", "startlux-4b")
LIMIT_SECONDS = 45 * 3600  # GPU lease seconds; includes attempt 1, DRYRUN and EVIDENCE (R1-P3A-BUDGET-CLOCK)
CAP_SECONDS = 60 * 3600    # P.3a cap, includes attempt 1 (recorded, not an extra allowance)
SCRIPT = R.REPO / "r1/scripts/trackp.py"

# --- pins the attempt-2 preflight verifies (b9ad6f8f = origin/trackp-20261026; the A3-short delta is on top) ---
PAPER_BRANCH = "trackp-20261026"
PAPER_BASE_PIN = "b9ad6f8fe2e771732100f704accd7f2ce7cf20f0"
PAPER_RUNNER_PATH = "r1/scripts/trackp_p3a_guarded.py"
PAPER_CHILD_SCRIPT = "r1/scripts/trackp.py"
CODE_UNITS_RECORD = "docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md"
# MAJOR-2: the paper HEAD must be exactly the reviewed probes-only runner commit, its docs-only child (r1/ tree
# identical), or the mechanical delivery-pin child that writes only EXPECTED_PAPER_HEAD + CODE_UNITS_RECORD.
EXPECTED_PAPER_HEAD = "7c9e8b0829450a70c462f2513873a56abcb8efdf"          # reviewed probes-only runner commit
EXPECTED_PAPER_HEAD_DOCS_CHILD = "8a3d3eaf048c7dd0a109719175dace72333bbd04"  # docs-only child, r1/ unchanged
EXPECTED_PAPER_BRANCH = "trackp-p3a-code-20261116"        # or a detached HEAD at the pinned commit ("HEAD")
EXECUTING_RUNNER = Path(__file__).resolve()               # the runner actually executing (its sha256 is recorded)
HARNESS_PIN = "897d83c8efa364ec2fdd37288241cc42e01d7274"
E0_V1_PATH = "r1/c3/train/data/e0_v1.jsonl.gz"
E0_V1_SHA256 = "4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290"
RULE_PATH = "r1/c3/rules/p3_rule_v2.yaml"
RULE_SHA256 = "8c0ef9089589eafcea04aea9c5936c7ab57625d19f2a7ab736de204d09840242"
CONFIG_PATH = "r1/scripts/configs/trackp_portal.json"
CONFIG_APPROVED_COMMIT = "607e85e"
FREEZE_PIN = "docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt"
EXPECTED_DRIVER = "580.178.04"
MIN_FREE_DISK_BYTES = 10 * 1024 ** 3

# --- P.3a attempt-2 (probes-only) contract: authorization, attempt-1 provenance, template order, marker ---
PROBES_ONLY_BASE = "qwen3.5-4b-base"     # the single interrupted attempt-1 unit that is re-run
DRYRUN_BASE = "kev-0.8b"                 # cheap changed-path DRYRUN, first
DRYRUN_N_PROBE = 8
EVIDENCE_N_PROBE = 100
PROJECTED_SECONDS = {"DRYRUN": 600.0, "EVIDENCE": 1800.0}   # conservative refusal projection, per unit
AUTHORIZATION_AMEND_SHA256 = "cd867e95ddab0525827a48d68ea570743977bbf1b6ea819fefb98b3cf460f32d"
AUTHORIZATION_AMEND_PATH = "docs/r1/authorizations/trackp_p3a_amend_20261104.md"
MARKER_PHASE = "p3a"
EXPECTED_MARKER_SHA256 = "f457a04ef1bbaba1750d9c04aa9211d51df1692ac36139bb720318f2d2533cec"
ATTEMPT1_ROOT_NAME = "p3a_operator_20261027"
NEW_ROOT_PREFIX = "p3a_attempt2_"
NEW_ROOT_UTC_FORMAT = "%Y%m%dT%H%M%SZ"           # p3a_attempt2_<UTC>; checked for format and real calendar time
EXPECTED_ATTEMPT1_JOURNAL_SHA256 = "1e73e80fac2fb5262cffb8d599c8bd861d99d9f4b23b3c20f56543bca501a344"
EXPECTED_ATTEMPT1_LEASE_LOG_SHA256 = "6950509182f4230dd2c7e2bad4253748415fa969e84ef9bdac21e19242b55077"
EXPECTED_ATTEMPT1_PAPER_COMMIT = "b9ad6f8fe2e771732100f704accd7f2ce7cf20f0"
EXPECTED_ATTEMPT1_BOOT_ID = "2c9bb104-cc3c-4c60-be67-c1c8f0287fe4"   # attempt-1 journal campaign_start.boot_id
ATTEMPT1_GPU_SECONDS_TOTAL = 130745.3789889291     # attempt-1 journal STOP; 36.318161 h
EXPECTED_PROMPT_VERSION = "trackp_prompt/v1"       # r1/c3/train/types.py:26
TEMPLATE_ORDER = "history_first"                   # M13 order record: history-before-proposal for both families
M13_ORDER_RECORD = "docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md"
M13_ORDER_RECORD_SHA256 = "351611c55516ca2aa2134b1efa0ca9d43bbec9b880a047ad1485baf16c94bce1"
UNIT_MANIFEST_SCHEMA = "trackp_p3a_unit_manifest/v1"
A3_SHORT_MARKER = "R1-P3A-OOM-OPTION3"
A3_DESCRIPTIVE_LEVELS = (2000, 8000)               # exam_synthetic.A3_DESCRIPTIVE at the pin
ATTEMPT1_ENVIRONMENT = {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True", "HF_HUB_OFFLINE": "1",
                        "TRANSFORMERS_OFFLINE": "1", "PYTHONUNBUFFERED": "1"}

# Declared per-family template descriptors (M13 order record §2.4/§3.2, pinned to model.py/kev/model.py at b9ad6f8f).
FRAMES = {
    "kev": {
        "frame": "kev_pointer_v1",
        "field_order": ["state", "proposal", "question", "options", "decide"],
        "readout": {"kind": "pointer", "decide_token": "<|fim_suffix|>", "options_read_at": "</opt>",
                    "source": "kev/model.py:104-111,125"},
    },
    "qwen_control": {
        "frame": "qwen_bintoken_v1",
        "field_order": ["state", "proposal", "question", "bins", "belief", "action"],
        "readout": {"kind": "belief_action", "belief_position": "last token of 'Belief:'",
                    "action_position": "last token of '\\nAction:'", "source": "r1/c3/train/model.py:649-662"},
    },
}
WRAPPER_CONFIG_KEYS = {"kev": ("kev_hybrid", "pointer_temperature", "released_temperature"),
                       "qwen_control": ("list_bins", "bin_order")}
FOREIGN_JOB_PATTERN = re.compile(r"(r1\.scripts\.trackp|r1/scripts/trackp|trackp_p3a|r1\.c3\.train\.|"
                                 r"phase2|equivalence|startlux|trackS_)")


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


def _write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_json_atomic(path, obj):
    """M6: write via a same-directory temp file + ``os.replace`` so a crash never leaves a partial record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(temporary, "w") as fh:
            fh.write(json.dumps(obj, indent=2, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(directory) -> dict:
    """Every file of ``directory`` by relative path with its sha256, plus a composite hash of that map."""
    directory = Path(directory)
    if not directory.is_dir():
        raise R.TrackPStop(f"attempt-1 artifact directory missing: {directory}")
    files, symlinks = {}, {}
    for path in sorted(directory.rglob("*")):
        rel = path.relative_to(directory).as_posix()
        if path.is_symlink():
            symlinks[rel] = os.readlink(path)      # never followed: attempt-1 artifacts must be plain files
        elif path.is_file():
            files[rel] = sha256_file(path)
    if not files:
        raise R.TrackPStop(f"attempt-1 artifact directory has no files: {directory}")
    composite = hashlib.sha256(json.dumps({"files": files, "symlinks": symlinks},
                                          sort_keys=True).encode()).hexdigest()
    return {"directory": str(directory), "file_count": len(files), "files_sha256": files,
            "symlinks": symlinks, "composite_sha256": composite}


def lease_log_total(path) -> float:
    """Sum of the complete (start/end paired, per pid) GPU-lease intervals recorded in ``path``."""
    path = Path(path)
    if not path.exists():
        return 0.0
    starts: dict[int, float] = {}
    total = 0.0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        pid = event.get("pid")
        if event.get("event") in ("acquired", "start"):
            starts.setdefault(pid, float(event["monotonic_s"]))
        elif event.get("event") == "end" and pid in starts:
            total += max(0.0, float(event["monotonic_s"]) - starts.pop(pid))
    return total


def is_ancestor(commit: str, repo=R.REPO) -> bool:
    res = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, "HEAD"],
                         capture_output=True, text=True, timeout=60)
    return res.returncode == 0


def _git_text(*arguments, repo=None) -> str:
    repo = R.REPO if repo is None else Path(repo)
    res = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        raise R.TrackPStop(f"git {' '.join(arguments)} failed in {repo}: {res.stderr.strip()[:300]}")
    return res.stdout.strip()


def _r1_tree_equal(left: str, right: str, repo=None) -> bool:
    """True when two commits have byte-identical ``r1/`` trees (diff --quiet exit code 0)."""
    res = subprocess.run(["git", "-C", str(R.REPO if repo is None else repo), "diff", "--quiet",
                          left, right, "--", "r1/"], capture_output=True, text=True, timeout=60)
    if res.returncode not in (0, 1):
        raise R.TrackPStop(f"cannot compare r1/ trees of {left} and {right}: {res.stderr.strip()[:300]}")
    return res.returncode == 0


def _delivery_pin_child(commit: str, repo=None) -> bool:
    """True only for the mechanical delivery-pin commit: direct child of EXPECTED_PAPER_HEAD whose ``r1/`` diff is
    exactly the one ``EXPECTED_PAPER_HEAD = "<commit>"`` assignment (plus the code-units record)."""
    try:
        parent = _git_text("rev-parse", commit + "^", repo=repo)
    except R.TrackPStop:
        return False
    if parent != EXPECTED_PAPER_HEAD:
        return False
    changed = set(_git_text("diff", "--name-only", EXPECTED_PAPER_HEAD, commit, repo=repo).splitlines())
    allowed = {PAPER_RUNNER_PATH, CODE_UNITS_RECORD}
    if PAPER_RUNNER_PATH not in changed or not changed <= allowed:
        return False
    patch = _git_text("diff", "-U0", EXPECTED_PAPER_HEAD, commit, "--", PAPER_RUNNER_PATH, repo=repo)
    added = [line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in patch.splitlines() if line.startswith("-") and not line.startswith("---")]
    assignment = "EXPECTED_PAPER_HEAD = "
    return (len(added) == 1 and len(removed) == 1 and assignment in added[0] and assignment in removed[0]
            and EXPECTED_PAPER_HEAD in added[0])


def verify_paper_head(paper: dict, repo=None) -> dict:
    """MAJOR-2: exact reviewed commit identity, not merely "a descendant of the base pin".

    Accepted: the reviewed runner commit itself, its docs-only child when ``r1/`` is byte-identical, or the single
    mechanical delivery-pin child that records the reviewed runner commit in ``EXPECTED_PAPER_HEAD``. Anything else
    (including an arbitrary descendant) is a STOP before any root/marker/GPU work.
    """
    branch = paper.get("branch")
    if branch not in (EXPECTED_PAPER_BRANCH, "HEAD"):
        raise R.TrackPStop(f"paper branch {branch!r} is not {EXPECTED_PAPER_BRANCH!r} or a detached HEAD at the "
                           f"reviewed commit")
    commit = paper.get("commit")
    if commit == EXPECTED_PAPER_HEAD:
        kind = "exact_reviewed_runner_commit"
    elif commit == EXPECTED_PAPER_HEAD_DOCS_CHILD and _r1_tree_equal(EXPECTED_PAPER_HEAD, commit, repo=repo):
        kind = "docs_child_r1_identical"
    elif _delivery_pin_child(commit, repo=repo):
        kind = "delivery_pin_child"
    else:
        raise R.TrackPStop(f"paper HEAD {commit!r} is not the reviewed runner commit {EXPECTED_PAPER_HEAD!r}, its "
                           f"docs-only child {EXPECTED_PAPER_HEAD_DOCS_CHILD!r} (r1/ identical), or the mechanical "
                           f"delivery-pin child; STOP")
    if not is_ancestor(EXPECTED_PAPER_HEAD, repo or R.REPO):
        raise R.TrackPStop(f"reviewed runner commit {EXPECTED_PAPER_HEAD!r} is not an ancestor of paper HEAD "
                           f"{commit!r}")
    return {"kind": kind, "commit": commit, "branch": branch, "expected_commit": EXPECTED_PAPER_HEAD,
            "docs_child": EXPECTED_PAPER_HEAD_DOCS_CHILD, "runner_script_path": PAPER_RUNNER_PATH}


def verify_attempt1_boot_id(current_boot_id: str, attempt1_boot_id: str = EXPECTED_ATTEMPT1_BOOT_ID) -> dict:
    """MAJOR-1: the attempt-2 session must run in the reviewed attempt-1 boot, not just be stable within itself."""
    if not current_boot_id:
        raise R.TrackPStop("current boot id is empty")
    if current_boot_id != attempt1_boot_id:
        raise R.TrackPStop(f"unplanned reboot since attempt 1: boot id {current_boot_id!r} != reviewed attempt-1 boot "
                           f"id {attempt1_boot_id!r}; STOP before creating the attempt-2 root")
    return {"boot_id": current_boot_id, "attempt1_boot_id": attempt1_boot_id, "match": True}


def runs_dir() -> Path:
    return Path(os.environ.get("R1_RUNS", str(R.LEASE_LOG.parent))).expanduser()


def lease_is_free(lock_path=R.LOCK_PATH) -> bool:
    """Preflight only: try (and immediately release) the same flock ``trackp.py`` takes per GPU unit."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        finally:
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
            except OSError:
                pass
    return True


def locks_dir() -> Path:
    return Path(os.environ.get("R1_LOCKS", str(Path.home() / "r1_locks")))


def priority_markers() -> list[str]:
    """Any other evidence marker (Track X/Track S/Track P) would make the card a shared resource: STOP."""
    directory = locks_dir()
    if not directory.is_dir():
        return []
    return sorted(str(p) for p in directory.glob("*.active"))


def foreign_experiment_processes(exclude: set[int] | None = None) -> list[str]:
    """Experiment processes of another unit on the host (attempt-1 preflight: none)."""
    skip = {os.getpid(), os.getppid()} | set(exclude or ())
    try:
        res = subprocess.run(["ps", "-eo", "pid=,args="], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise R.TrackPStop(f"cannot census host processes: {exc}") from exc
    if res.returncode != 0:
        raise R.TrackPStop(f"host process census failed: {res.stderr.strip()}")
    out = []
    for line in res.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        pid, command = int(parts[0]), parts[1]
        if pid in skip or command.startswith("ps "):
            continue
        if FOREIGN_JOB_PATTERN.search(command):
            out.append(f"{pid} {command}"[:300])
    return out


def marker_helper_path() -> Path:
    return locks_dir() / "bin" / "trackp-evidence"


def verify_marker_helper() -> dict:
    """The installed marker helper must be the reviewed one (committed copy f457a04e…)."""
    helper = marker_helper_path()
    if not helper.is_file():
        raise R.TrackPStop(f"Track P evidence marker helper missing: {helper}")
    digest = sha256_file(helper)
    if digest != EXPECTED_MARKER_SHA256:
        raise R.TrackPStop(f"marker helper {helper} sha256 {digest} is not the reviewed {EXPECTED_MARKER_SHA256}")
    return {"path": str(helper), "sha256": digest, "phase": MARKER_PHASE}


def run_marker(helper, action: str) -> dict:
    """The helper's actual interface (docs/r1/proposals/trackp-evidence.sh): ``begin|end <phase>``."""
    command = [str(helper), action, MARKER_PHASE]
    res = subprocess.run(command, capture_output=True, text=True, timeout=120)
    return {"command": command, "utc": R.utcnow(), "rc": res.returncode,
            "stdout": res.stdout[-2000:], "stderr": res.stderr[-2000:]}


@contextlib.contextmanager
def evidence_marker(journal, helper: dict, state: dict | None = None):
    """Begin the Track P evidence marker before GPU work and end it in a ``finally`` (success or STOP).

    The job is executed directly (``trackp.py`` takes its own ``flock``): the marker helper is used for its
    begin/end interface only, never as ``trackp-evidence run`` (a nested ``flock`` would deadlock/fail).
    """
    begin = run_marker(helper["path"], "begin")
    emit(journal, {"event": "marker_begin", **begin})
    if begin["rc"] != 0:
        raise R.TrackPStop(f"trackp-evidence begin {MARKER_PHASE} failed rc={begin['rc']}: {begin['stderr'][:300]}")
    try:
        yield
    finally:
        end = run_marker(helper["path"], "end")
        emit(journal, {"event": "marker_end", **end})
        if state is not None:
            state["marker_end"] = end


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

    def require_available(self, projection_seconds: float = 0.0):
        if self.used >= self.limit:
            raise R.TrackPStop("45 GPU-hour lease limit reached")
        projected = self.used + max(0.0, float(projection_seconds))
        if projected >= self.limit:
            raise R.TrackPStop(f"next unit would cross the 45 GPU-hour lease STOP "
                               f"({projected / 3600:.3f} h >= {self.limit / 3600:.0f} h); refusing before it starts")


class Attempt2Budget(GPUBudget):
    """Attempt-2 budget guard: ``used = attempt-1 journal gpu_seconds_total + this run's lease log``.

    The 45-h lease STOP and the 60-h P.3a cap both include attempt 1 (R1-P3A-BUDGET-CLOCK): attempt 1 used
    36.318161 h, so the whole attempt-2 session has 8.681839 h left of the lease and the 60-h cap is recorded,
    not added to the budget. ``lease_log`` stays the global lease log the child ``trackp.py`` writes and the
    watchdog tails; ``new_lease_log`` is this run's own copy (the root's ``gpu_lease_log.jsonl``).
    """
    def __init__(self, attempt1_seconds, new_lease_log, *, limit=LIMIT_SECONDS, cap_seconds=CAP_SECONDS,
                 lease_log=R.LEASE_LOG):
        super().__init__(limit=limit, lease_log=lease_log)
        self.attempt1_seconds = float(attempt1_seconds)
        self.cap_seconds = int(cap_seconds)
        self.new_lease_log = Path(new_lease_log)
        self.refresh()

    def refresh(self) -> float:
        self.used = self.attempt1_seconds + lease_log_total(self.new_lease_log)
        return self.used

    def require_available(self, projection_seconds: float = 0.0):
        self.refresh()
        if self.used > self.cap_seconds:
            raise R.TrackPStop(f"60 GPU-hour P.3a cap reached ({self.used / 3600:.3f} h > "
                               f"{self.cap_seconds / 3600:.0f} h, including attempt 1)")
        super().require_available(projection_seconds)

    def record(self) -> dict:
        self.refresh()
        return {"attempt1_gpu_seconds": self.attempt1_seconds,
                "attempt1_gpu_hours": self.attempt1_seconds / 3600,
                "new_lease_seconds": self.used - self.attempt1_seconds,
                "used_seconds": self.used, "used_hours": self.used / 3600,
                "remaining_seconds": max(0.0, self.limit - self.used),
                "remaining_hours": max(0.0, self.limit - self.used) / 3600,
                "limit_seconds": self.limit, "cap_seconds": self.cap_seconds,
                "cap_hours": self.cap_seconds / 3600,
                "new_lease_log": str(self.new_lease_log),
                "projections_seconds": dict(PROJECTED_SECONDS)}


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


def _mirror_lease(mirror, kind, event, unit):
    """Copy the observed lease start/end into this run's own lease log (attempt 2 budget accounting)."""
    if mirror is None:
        return
    mirror = Path(mirror)
    mirror.parent.mkdir(parents=True, exist_ok=True)
    with mirror.open("a") as fh:
        fh.write(json.dumps({"event": kind, "job": event.get("job"), "pid": event.get("pid"),
                             "utc": event.get("utc"), "monotonic_s": float(event["monotonic_s"]),
                             "unit": unit}, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def run_unit(root, journal, boot_id, budget, label, base, name, arguments, gpu=True, *,
             template_id=None, attempt1_input=None, projection_seconds=0.0, lease_mirror=None,
             sidecar_builder=None, unit_start_verifier=None):
    """Run one child ``trackp.py`` unit under the watchdog/process-group safety.

    Attempt 2 (``--probes-only``) passes ``template_id``/``attempt1_input`` (recorded on ``unit_start``),
    ``projection_seconds`` (refused before start if the 45-h projection crosses), ``lease_mirror`` (the run's own
    lease log), ``sidecar_builder`` (the per-unit ``runner_manifest.json``) and ``unit_start_verifier`` (re-reads
    the attempt-1 provenance/input hashes and recomputes the declared template *before* the child starts; drift is
    a STOP). The attempt-1 multi-base path passes none of them and behaves exactly as before.
    """
    budget.require_available(projection_seconds)
    if R.tasl7_driver_snapshot()["boot_id"] != boot_id:
        raise R.TrackPStop("unplanned reboot: boot ID changed")
    directory = root / label / base / name
    if directory.exists():
        raise R.TrackPStop(f"unit path already exists; preserve interrupted unit: {directory}")
    verify_live_pins(journal)
    unit_start_check = None
    if unit_start_verifier is not None:
        unit_start_check = unit_start_verifier(label=label, base=base)
        if template_id is not None and unit_start_check.get("template_id") != template_id:
            raise R.TrackPStop(f"template at unit start {unit_start_check.get('template_id')!r} != campaign "
                               f"declaration {template_id!r}")
    directory.parent.mkdir(parents=True, exist_ok=True)
    log = directory.parent / (name + ".stdout.log")
    cmd = [sys.executable, str(SCRIPT), *arguments, "--evidence", label,
           "--run-dir", str(directory)]
    unit = {"label": label, "base": base, "unit": name}
    started = {"event": "unit_start", "label": label, "base": base, "unit": name,
               "utc": R.utcnow(), "argv": cmd, "gpu_seconds_before": budget.used}
    if template_id is not None:
        started["template_id"] = template_id
    if attempt1_input is not None:
        started["attempt1_input"] = attempt1_input
    if unit_start_check is not None:
        started["unit_start_verification"] = unit_start_check
    emit(journal, started)
    seconds_before = budget.used
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
                        if start is None:
                            start = observed
                            _mirror_lease(lease_mirror, "start", event, unit)
                    elif event.get("event") == "end":
                        if start is None or end is not None:
                            raise R.TrackPStop("invalid GPU lease end")
                        end = float(event["monotonic_s"])
                        _mirror_lease(lease_mirror, "end", event, unit)
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
    if hasattr(budget, "refresh"):
        budget.refresh()                  # attempt 2: used = attempt-1 total + this run's lease log
    complete = {"event": "unit_complete", "label": label, "base": base, "unit": name,
                "utc": R.utcnow(), "gpu_seconds_total": budget.used}
    if template_id is not None:
        complete["template_id"] = template_id
        complete["gpu_seconds_unit"] = max(0.0, budget.used - seconds_before)
    if sidecar_builder is not None:
        sidecar = sidecar_builder(report=report, manifest=manifest, directory=directory, label=label,
                                  base=base, name=name, budget=budget,
                                  gpu_seconds_unit=max(0.0, budget.used - seconds_before))
        if not isinstance(sidecar, dict) or sidecar.get("schema") != UNIT_MANIFEST_SCHEMA:
            raise R.TrackPStop(f"runner manifest builder returned no {UNIT_MANIFEST_SCHEMA} record")
        sidecar_path = directory / "runner_manifest.json"
        write_json_atomic(sidecar_path, sidecar)
        if read_json_finite(sidecar_path) != sidecar:
            raise R.TrackPStop(f"runner manifest did not round-trip: {sidecar_path}")
        complete["runner_manifest_sha256"] = sha256_file(sidecar_path)
    emit(journal, complete)
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


# =====================================================================================================================
# P.3a attempt 2: probes-only runner (Unit A plan §1c.2; R2 review conditions 2-6)
# =====================================================================================================================

BIN_COUNT = 12   # types.BIN_OPTIONS / N_BINS at the pin
EXPECTED_DERIVED_TEMPLATE_IDS = {   # M13 order record §3.5: the retro-tagged attempt-1 template ids
    "kev": "trackp_prompt/v1/kev_pointer_v1/history_first/kev@2074cc44256200bb37540103fa4572901faa10f3",
    "qwen_control": "trackp_prompt/v1/qwen_bintoken_v1/history_first/transformers@5.19.0+qwen3.5-tokenizers",
}


def prompt_version() -> str:
    """The template version string is imported from the pinned source, never copied (M13 §3.2)."""
    from r1.c3.train.types import PROMPT_VERSION
    if PROMPT_VERSION != EXPECTED_PROMPT_VERSION:
        raise R.TrackPStop(f"PROMPT_VERSION {PROMPT_VERSION!r} is not the attempt-1 template "
                           f"{EXPECTED_PROMPT_VERSION!r}; attempt 2 must run the attempt-1 template")
    return PROMPT_VERSION


def installed_kev_encoder() -> dict:
    """Installed Kev encoder commit + ``kev/model.py`` sha256, from the Kev dist-info (M13 §3.2/§1.3)."""
    import importlib.metadata as md
    try:
        dist = md.distribution("kev")
        direct = dist.read_text("direct_url.json")
    except md.PackageNotFoundError as exc:
        raise R.TrackPStop("installed Kev encoder dist-info missing") from exc
    commit = ((json.loads(direct or "{}").get("vcs_info") or {}).get("commit_id"))
    if not commit:
        raise R.TrackPStop("installed Kev encoder records no commit_id in direct_url.json")
    model_path = Path(dist.locate_file("kev/model.py")).resolve()
    if not model_path.is_file():
        raise R.TrackPStop(f"installed Kev encoder source missing: {model_path}")
    return {"commit": commit, "model_path": str(model_path), "model_sha256": sha256_file(model_path)}


def encoder_block(family: str, manifest: dict, *, kev_encoder: dict | None = None) -> dict:
    """Declared encoder of one family, from the installed package and the manifest's recorded environment."""
    env = manifest.get("environment") or {}
    base = manifest.get("base") or {}
    if family == "kev":
        kev_encoder = kev_encoder or installed_kev_encoder()
        recorded = ((env.get("packages") or {}).get("kev") or {}).get("pip_commit")
        if recorded and recorded != kev_encoder["commit"]:
            raise R.TrackPStop(f"Kev encoder mismatch: manifest records {recorded}, installed {kev_encoder['commit']}")
        return {"kind": "kev.model.encode", "repo": "jaredpalmer/kev", "commit": kev_encoder["commit"],
                "kev_model_sha256": kev_encoder["model_sha256"], "id": f"kev@{kev_encoder['commit']}"}
    if family in ("qwen_control", "qwen_reason"):
        version = env.get("transformers")
        if not version:
            raise R.TrackPStop(f"{family}: manifest records no transformers version")
        return {"kind": "transformers", "version": version, "tokenizer_repo": base.get("base_repo"),
                "tokenizer_revision": base.get("base_revision"),
                "id": f"transformers@{version}+qwen3.5-tokenizers"}
    raise R.TrackPStop(f"no declared attempt-2 template for family {family!r}")


def wrapper_config_block(family: str, saved_manifest: dict) -> dict:
    """Wrapper configuration copied from the loaded attempt-1 saved model (``describe()``)."""
    if saved_manifest.get("family") != family:
        raise R.TrackPStop(f"loaded saved model family {saved_manifest.get('family')!r} != {family!r}")
    if family == "kev":
        if saved_manifest.get("kev_hybrid") is not True:
            raise R.TrackPStop("attempt-1 loaded Kev model is not the hybrid/rows frame")
        return {key: saved_manifest.get(key) for key in WRAPPER_CONFIG_KEYS["kev"]}
    if saved_manifest.get("list_bins") is not True or saved_manifest.get("bin_order") != list(range(BIN_COUNT)):
        raise R.TrackPStop("attempt-1 loaded Qwen model does not list the canonical bins (0..11)")
    return {"list_bins": True, "bin_order": list(range(BIN_COUNT))}


def template_block(family: str, manifest: dict, saved_manifest: dict, *, kev_encoder: dict | None = None) -> dict:
    """The accepted M13 §3.2 ``attempt2_template`` block (also used for the derived attempt-1 id)."""
    spec = FRAMES[family]
    encoder = encoder_block(family, manifest, kev_encoder=kev_encoder)
    version = prompt_version()
    return {"version": version, "version_source": "r1/c3/train/types.py:26",
            "family": family, "frame": spec["frame"], "order": TEMPLATE_ORDER,
            "field_order": list(spec["field_order"]), "readout": dict(spec["readout"]),
            "encoder": encoder, "wrapper_config": wrapper_config_block(family, saved_manifest),
            "template_id": f"{version}/{spec['frame']}/{TEMPLATE_ORDER}/{encoder['id']}"}


def attempt1_input(attempt1_root, base: str) -> dict:
    """Bind the attempt-1 ``EVIDENCE/<base>/final/saved`` model read-only: recorded + re-hashed file list."""
    final = Path(attempt1_root) / "EVIDENCE" / base / "final"
    saved = final / "saved"
    final_manifest = read_json_finite(final / "manifest.json")
    saved_manifest = read_json_finite(saved / "manifest.json")
    recorded = final_manifest.get("model_files_sha256") or {}
    if not recorded:
        raise R.TrackPStop(f"attempt-1 {base}/final manifest records no model_files_sha256")
    if saved_manifest.get("files") != recorded:
        raise R.TrackPStop(f"attempt-1 {base}/final/saved manifest files disagree with final/manifest model_files_sha256")
    hashed = hash_directory(saved)
    for rel, digest in recorded.items():
        if hashed["files_sha256"].get(rel) != digest:
            raise R.TrackPStop(f"attempt-1 input {base}/final/saved/{rel} does not match its recorded sha256")
    unexpected = set(hashed["files_sha256"]) - set(recorded) - {"manifest.json"}
    if unexpected:
        raise R.TrackPStop(f"attempt-1 {base}/final/saved has unrecorded files: {sorted(unexpected)}")
    describe_keys = ("family", "model_version", "head_form", "action_head", "kev_hybrid", "pointer_temperature",
                     "released_temperature", "list_bins", "bin_order")
    describe = {key: saved_manifest.get(key) for key in describe_keys if key in saved_manifest}
    return {"root": str(attempt1_root), "base": base, "loaded_artifact": str(saved),
            "model_files_sha256": recorded, "loaded_hash": hashed, "saved_describe": describe}


def build_attempt1_provenance(attempt1_root) -> dict:
    """Read-only attempt-1 provenance: journal/lease-log hashes, paper commit and the STOP GPU seconds."""
    root = Path(attempt1_root)
    if not root.is_dir():
        raise R.TrackPStop(f"attempt-1 root missing: {root}")
    journal = root / "journal.jsonl"
    lease_log = root.parent / "gpu_lease_log.jsonl"
    if not journal.is_file():
        raise R.TrackPStop(f"attempt-1 journal missing: {journal}")
    if not lease_log.is_file():
        raise R.TrackPStop(f"attempt-1 lease log missing: {lease_log}")
    events = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
    if not events or events[0].get("event") != "campaign_start":
        raise R.TrackPStop("attempt-1 journal does not start with campaign_start")
    stops = [event for event in events if event.get("event") == "STOP"]
    if len(stops) != 1:
        raise R.TrackPStop(f"attempt-1 journal must end with exactly one STOP; found {len(stops)}")
    gpu_seconds = stops[0].get("gpu_seconds_total")
    if not isinstance(gpu_seconds, (int, float)) or not math.isfinite(gpu_seconds) or gpu_seconds <= 0:
        raise R.TrackPStop("attempt-1 STOP records no finite gpu_seconds_total")
    paper = (events[0].get("pins") or {}).get("paper") or {}
    if not paper.get("commit"):
        raise R.TrackPStop("attempt-1 campaign_start records no paper commit")
    attempt1_boot_id = events[0].get("boot_id")
    if not isinstance(attempt1_boot_id, str) or not attempt1_boot_id.strip():
        raise R.TrackPStop("attempt-1 campaign_start records no boot_id")
    return {"root": str(root), "journal": str(journal), "journal_sha256": sha256_file(journal),
            "lease_log": str(lease_log), "lease_log_sha256": sha256_file(lease_log),
            "journal_events": len(events), "stop_utc": stops[0].get("utc"),
            "paper_commit": paper["commit"], "paper_branch": paper.get("branch"),
            "paper_dirty": paper.get("dirty"),
            "attempt1_boot_id": attempt1_boot_id, "expected_attempt1_boot_id": EXPECTED_ATTEMPT1_BOOT_ID,
            "gpu_seconds_total": float(gpu_seconds), "gpu_hours_total": float(gpu_seconds) / 3600,
            "derived_prompt_version": EXPECTED_PROMPT_VERSION, "derived_order": TEMPLATE_ORDER,
            "derived_template_ids_by_family": dict(EXPECTED_DERIVED_TEMPLATE_IDS),
            "recorded_at_run_time": False, "label": "derived",
            "derivation": {"doc": M13_ORDER_RECORD, "sha256": M13_ORDER_RECORD_SHA256}}


def assert_attempt1_pins(provenance: dict) -> None:
    """Fail closed unless the preserved attempt 1 is the reviewed one (hashes, boot id and STOP GPU seconds)."""
    checks = (("journal_sha256", EXPECTED_ATTEMPT1_JOURNAL_SHA256),
              ("lease_log_sha256", EXPECTED_ATTEMPT1_LEASE_LOG_SHA256),
              ("paper_commit", EXPECTED_ATTEMPT1_PAPER_COMMIT),
              ("attempt1_boot_id", EXPECTED_ATTEMPT1_BOOT_ID))
    for key, expected in checks:
        if provenance.get(key) != expected:
            raise R.TrackPStop(f"attempt-1 {key} {provenance.get(key)!r} != reviewed {expected!r}")
    if abs(float(provenance["gpu_seconds_total"]) - ATTEMPT1_GPU_SECONDS_TOTAL) > 1e-6:
        raise R.TrackPStop(f"attempt-1 gpu_seconds_total {provenance['gpu_seconds_total']!r} != reviewed "
                           f"{ATTEMPT1_GPU_SECONDS_TOTAL!r}")


def attempt1_environment() -> dict:
    """Set (if absent) and record the attempt-1 launcher environment (R2 P-M9); no other env change."""
    applied = {}
    for key, value in ATTEMPT1_ENVIRONMENT.items():
        os.environ.setdefault(key, value)
        applied[key] = os.environ[key]
    return applied


def verify_probes_only_pins(amend_sha256: str, disk_path=None) -> dict:
    """Attempt-2 fail-closed live preflight (Unit A plan §1c.2; R2 conditions 2 and 6)."""
    if amend_sha256 != AUTHORIZATION_AMEND_SHA256:
        raise R.TrackPStop(f"--authorization-amend-sha256 {amend_sha256!r} is not the reviewed "
                           f"{AUTHORIZATION_AMEND_SHA256!r}")
    paper = R.git_commit(R.REPO)
    if paper["dirty"]:
        raise R.TrackPStop(f"paper checkout dirty: {paper['dirty_files'][:5]}")
    paper_identity = verify_paper_head(paper)
    if not is_ancestor(PAPER_BASE_PIN, R.REPO):
        raise R.TrackPStop(f"pinned base {PAPER_BASE_PIN} is not an ancestor of paper HEAD {paper['commit']}")
    harness = R.git_commit(R.harness_root())
    if harness["commit"] != HARNESS_PIN or harness["dirty"]:
        raise R.TrackPStop(f"harness pin mismatch or dirty harness: {harness['commit']} dirty={harness['dirty']}")
    try:
        subprocess.run(["git", "-C", str(R.REPO), "ls-files", "--error-unmatch",
                        PAPER_RUNNER_PATH, "r1/scripts/trackp_p3a_watchdog.py", "r1/scripts/trackp_p3a_gate.py",
                        PAPER_CHILD_SCRIPT], check=True, capture_output=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise R.TrackPStop(f"runner/watchdog/gate/child scripts are not tracked at the paper HEAD: {exc}") from exc
    for path, expected in ((E0_V1_PATH, E0_V1_SHA256), (RULE_PATH, RULE_SHA256)):
        digest = sha256_file(R.REPO / path)
        if digest != expected:
            raise R.TrackPStop(f"authorized hash mismatch: {path}")
    config_path = R.REPO / CONFIG_PATH
    try:
        original = subprocess.run(["git", "-C", str(R.REPO), "show", CONFIG_APPROVED_COMMIT + ":" + CONFIG_PATH],
                                  capture_output=True, check=True, timeout=60).stdout
        actual = subprocess.run(["/home/dowling/.local/bin/uv", "pip", "freeze", "--python", sys.executable],
                                capture_output=True, text=True, check=True, timeout=120).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise R.TrackPStop(f"pin verification command failed: {exc}") from exc
    if original != config_path.read_bytes():
        raise R.TrackPStop("trackp_portal.json changed from the approved configuration")
    frozen = (R.REPO / FREEZE_PIN).read_text()
    if sorted(actual.splitlines()) != sorted(frozen.splitlines()):
        raise R.TrackPStop("run environment freeze does not match the recorded TASL-7 pin")
    from r1.c3.train.registry import reverify
    bad = reverify(R.REPO / "r1/c3/train/registry.yaml")
    if bad:
        raise R.TrackPStop(f"registered model files mismatch: {bad[:5]}")
    if socket.gethostname().lower().split(".")[0] != "tasl-7":
        raise R.TrackPStop("P.3a attempt 2 is authorized on TASL-7 only")
    driver = R.tasl7_driver_snapshot()
    drivers = [line.strip() for line in (driver.get("nvidia_smi_driver") or [])]
    if not drivers or any(value != EXPECTED_DRIVER for value in drivers):
        raise R.TrackPStop(f"NVIDIA driver {drivers} is not the reviewed {EXPECTED_DRIVER}")
    boot = verify_attempt1_boot_id(driver.get("boot_id"), EXPECTED_ATTEMPT1_BOOT_ID)
    disk = shutil.disk_usage(str(disk_path or R.REPO))
    if disk.free < MIN_FREE_DISK_BYTES:
        raise R.TrackPStop(f"disk free {disk.free} bytes < required {MIN_FREE_DISK_BYTES}")
    census = R.foreign_compute_processes()
    if census:
        raise R.TrackPStop(f"GPU compute census is not empty: {census[:5]}")
    if not lease_is_free():
        raise R.TrackPStop(f"GPU lease {R.LOCK_PATH} is held; do not start")
    markers = priority_markers()
    if markers:
        raise R.TrackPStop(f"another evidence marker is present: {markers}")
    processes = foreign_experiment_processes()
    if processes:
        raise R.TrackPStop(f"another experiment process is running: {processes[:5]}")
    marker = verify_marker_helper()
    amend_path = R.REPO / AUTHORIZATION_AMEND_PATH
    if amend_path.is_file() and sha256_file(amend_path) != AUTHORIZATION_AMEND_SHA256:
        raise R.TrackPStop(f"amendment file {amend_path} does not match the reviewed sha256")
    child_script = R.REPO / PAPER_CHILD_SCRIPT
    if not child_script.is_file():
        raise R.TrackPStop(f"child script missing under the paper checkout: {child_script}")
    return {"paper": paper, "paper_identity": paper_identity,
            "paper_base_pin": {"commit": PAPER_BASE_PIN, "is_ancestor": True},
            "harness": harness, "e0_v1_sha256": E0_V1_SHA256, "p3_rule_v2_sha256": RULE_SHA256,
            "config": {"path": CONFIG_PATH, "unchanged_from_commit": CONFIG_APPROVED_COMMIT},
            "freeze": "matches TASL-7 recorded freeze", "model_registry": "all files reverified",
            "hostname": socket.gethostname(),
            "boot_id": boot["boot_id"], "attempt1_boot_id": boot["attempt1_boot_id"], "boot_id_match": boot["match"],
            "driver": driver,
            "runner_script_path": str(EXECUTING_RUNNER),
            "runner_script_sha256": sha256_file(EXECUTING_RUNNER),
            "child_script_path": str(child_script), "child_script_sha256": sha256_file(child_script),
            "disk": {"free_bytes": disk.free, "total_bytes": disk.total, "used_bytes": disk.used},
            "gpu_census": "empty", "lease": "free", "priority_markers": markers,
            "other_experiment_processes": processes, "marker": marker,
            "authorization_amend_sha256": amend_sha256,
            "authorization_amend_file_present": amend_path.is_file()}


def verify_a3_short_report(report: dict, label: str, template_id: str) -> None:
    """Prove the child ran the *changed* A3 path (budget-v2 rows, descriptive levels skipped)."""
    a3 = report.get("A3") or {}
    if a3.get("protocol") != "v2_budget":
        raise R.TrackPStop(f"{label}: probes report did not run the A3 budget-v2 path "
                           f"(protocol={a3.get('protocol')!r}, template {template_id})")
    descriptive = report.get("A3_descriptive")
    if not isinstance(descriptive, dict) or set(descriptive) != {"skipped", "levels", "pass"}:
        raise R.TrackPStop(f"{label}: A3_descriptive is not the A3-short skipped marker: {descriptive!r}")
    if descriptive.get("skipped") != A3_SHORT_MARKER or descriptive.get("pass") is not None:
        raise R.TrackPStop(f"{label}: A3_descriptive marker is {descriptive!r}, not {A3_SHORT_MARKER}")
    if [int(level) for level in descriptive.get("levels") or []] != list(A3_DESCRIPTIVE_LEVELS):
        raise R.TrackPStop(f"{label}: A3-short recorded levels {descriptive.get('levels')!r} are not the "
                           f"descriptive {list(A3_DESCRIPTIVE_LEVELS)}")


def probes_only_units(attempt1_root) -> list[dict]:
    """The exactly-two attempt-2 commands: changed-path Kev-0.8B DRYRUN first, then the 4b EVIDENCE probes."""
    attempt1_root = Path(attempt1_root)
    units = []
    for label, base, n_probe in (("DRYRUN", DRYRUN_BASE, DRYRUN_N_PROBE),
                                 ("EVIDENCE", PROBES_ONLY_BASE, EVIDENCE_N_PROBE)):
        load = attempt1_root / "EVIDENCE" / base / "final" / "saved"
        units.append({"label": label, "base": base, "unit": "probes", "n_probe": n_probe,
                      "load": str(load), "projection_seconds": PROJECTED_SECONDS[label],
                      "arguments": ["probes", "--base", base, "--head-form", "linear12", "--budget",
                                    "--a3-short", "--n-probe", str(n_probe), "--load", str(load)]})
    return units


def make_sidecar_builder(provenance: dict, unit_inputs: dict, campaign_templates: dict, kev_encoder: dict,
                         amend_sha256: str):
    """Per-unit ``runner_manifest.json`` (M13 §3.2/§3.3, schema ``trackp_p3a_unit_manifest/v1``).

    M2: ``attempt1_provenance.derived_template_id`` is the *per-unit* composite id of the unit's family (the
    campaign-level record carries ``derived_template_ids_by_family``); it must equal the unit's
    ``attempt2_template.template_id`` and the reviewed M13 §3.5 id.
    """
    def build(*, report, manifest, directory, label, base, name, budget, gpu_seconds_unit):
        family = (manifest.get("base") or {}).get("family")
        if family not in campaign_templates:
            raise R.TrackPStop(f"unit {label}/{base}: child manifest family {family!r} has no declared template")
        template = template_block(family, manifest, unit_inputs[base]["saved_describe"], kev_encoder=kev_encoder)
        if template != campaign_templates[family]:
            raise R.TrackPStop(f"unit {label}/{base}: per-unit template disagrees with the campaign declaration")
        if template["template_id"] != EXPECTED_DERIVED_TEMPLATE_IDS[family]:
            raise R.TrackPStop(f"unit {label}/{base}: template {template['template_id']!r} != the reviewed "
                               f"attempt-1 {EXPECTED_DERIVED_TEMPLATE_IDS[family]!r}")
        unit_provenance = dict(provenance)
        unit_provenance["derived_template_id"] = template["template_id"]
        unit_provenance["derived_template_family"] = family
        if unit_provenance["derived_template_ids_by_family"].get(family) != template["template_id"]:
            raise R.TrackPStop(f"unit {label}/{base}: attempt-1 provenance template id disagrees with the template")
        return {"schema": UNIT_MANIFEST_SCHEMA,
                "unit": {"label": label, "base": base, "unit": name, "run_dir": str(directory)},
                "attempt2_template": template,
                "attempt1_provenance": unit_provenance,
                "attempt1_input": {"root": provenance["root"], "base": base,
                                   "loaded_artifact": unit_inputs[base]["loaded_artifact"],
                                   "model_files_sha256": unit_inputs[base]["model_files_sha256"],
                                   "loaded_hash": unit_inputs[base]["loaded_hash"]},
                "inputs": {"child_manifest_sha256": sha256_file(Path(directory) / "manifest.json"),
                           "child_report_sha256": sha256_file(Path(directory) / "report.json"),
                           "authorization_amend_sha256": amend_sha256},
                "cost": {"gpu_seconds": gpu_seconds_unit},
                "created_utc": R.utcnow()}
    return build


def make_unit_start_verifier(attempt1_root, provenance: dict, unit_inputs: dict, attempt1_manifests: dict,
                             campaign_templates: dict, kev_encoder: dict):
    """M4/M13 §3.3: re-read the attempt-1 provenance/input hashes and recompute the declared template at
    ``unit_start`` (before the child is spawned) and STOP on any drift. The post-child template check stays."""
    def verify(*, label, base):
        fresh = build_attempt1_provenance(attempt1_root)
        for key in ("journal_sha256", "lease_log_sha256", "paper_commit", "attempt1_boot_id"):
            if fresh.get(key) != provenance.get(key):
                raise R.TrackPStop(f"attempt-1 provenance drift at {label}/{base} unit start: {key}")
        if abs(float(fresh["gpu_seconds_total"]) - float(provenance["gpu_seconds_total"])) > 1e-6:
            raise R.TrackPStop(f"attempt-1 provenance drift at {label}/{base} unit start: gpu_seconds_total")
        fresh_input = attempt1_input(attempt1_root, base)
        if fresh_input["loaded_hash"] != unit_inputs[base]["loaded_hash"]:
            raise R.TrackPStop(f"attempt-1 input drift at {label}/{base} unit start: loaded_hash")
        family = unit_inputs[base]["saved_describe"]["family"]
        fresh_template = template_block(family, attempt1_manifests[base], unit_inputs[base]["saved_describe"],
                                        kev_encoder=kev_encoder)
        if fresh_template != campaign_templates[family]:
            raise R.TrackPStop(f"campaign template drift at {label}/{base} unit start")
        return {"template_id": fresh_template["template_id"],
                "attempt1_input_composite_sha256": fresh_input["loaded_hash"]["composite_sha256"],
                "journal_sha256": fresh["journal_sha256"], "lease_log_sha256": fresh["lease_log_sha256"]}
    return verify


def validate_probes_only_args(args) -> None:
    """Fail-closed argument contract of the probes-only attempt-2 mode."""
    if not args.attempt1_root:
        raise R.TrackPStop("--probes-only needs --attempt1-root")
    if not args.base:
        raise R.TrackPStop(f"--probes-only needs --base {PROBES_ONLY_BASE}")
    if args.base != PROBES_ONLY_BASE:
        raise R.TrackPStop(f"probes-only attempt 2 re-runs only {PROBES_ONLY_BASE}; got {args.base!r}")
    if not args.a3_short:
        raise R.TrackPStop("--probes-only needs --a3-short: attempt 2 runs the A3-short path (R1-P3A-OOM-OPTION3)")
    if not args.authorization_amend_sha256:
        raise R.TrackPStop("--probes-only needs --authorization-amend-sha256")
    if args.authorization_amend_sha256 != AUTHORIZATION_AMEND_SHA256:
        raise R.TrackPStop(f"--authorization-amend-sha256 {args.authorization_amend_sha256!r} is not the reviewed "
                           f"{AUTHORIZATION_AMEND_SHA256!r}")
    attempt1_raw = Path(args.attempt1_root)
    if not attempt1_raw.is_absolute():
        raise R.TrackPStop(f"--attempt1-root must be absolute; got {str(attempt1_raw)!r}")
    if not args.root.is_absolute():
        raise R.TrackPStop("campaign root must be absolute")
    if os.path.lexists(args.root):
        raise R.TrackPStop("campaign root already exists (or is a dangling symlink); preserve it and STOP")
    if not args.root.name.startswith(NEW_ROOT_PREFIX):
        raise R.TrackPStop(f"campaign root must be a new {NEW_ROOT_PREFIX}<UTC> directory; got {args.root.name!r}")
    stamp = args.root.name[len(NEW_ROOT_PREFIX):]
    try:
        parsed = datetime.strptime(stamp, NEW_ROOT_UTC_FORMAT)
    except ValueError as exc:
        raise R.TrackPStop(f"campaign root name {args.root.name!r} is not {NEW_ROOT_PREFIX}{NEW_ROOT_UTC_FORMAT} "
                           f"(UTC); got {stamp!r}") from exc
    if parsed.strftime(NEW_ROOT_UTC_FORMAT) != stamp:
        raise R.TrackPStop(f"campaign root name {args.root.name!r} is not a canonical UTC timestamp")
    runs = runs_dir().resolve()
    root = args.root.resolve()
    if root.parent != runs:
        raise R.TrackPStop(f"campaign root must sit directly under the runs directory {runs}; got {root.parent}")
    attempt1 = attempt1_raw.resolve()
    if attempt1 == root or attempt1 in root.parents or root in attempt1.parents:
        raise R.TrackPStop(f"attempt-1 root {attempt1} may not be reused or nested in the attempt-2 root {root}")
    if root.name == ATTEMPT1_ROOT_NAME:
        raise R.TrackPStop(f"attempt-1 root name {ATTEMPT1_ROOT_NAME} may not be reused")


def campaign_start_record(args, pins: dict, provenance: dict, unit_inputs: dict, templates: dict,
                          budget: Attempt2Budget, environment: dict) -> dict:
    inputs = {base: {"loaded_artifact": value["loaded_artifact"],
                     "model_files_sha256": value["model_files_sha256"],
                     "loaded_hash": value["loaded_hash"],
                     "saved_describe": value["saved_describe"]}
              for base, value in unit_inputs.items()}
    return {"event": "campaign_start", "utc": R.utcnow(), "mode": "probes_only",
            "boot_id": pins["boot_id"], "expected_attempt1_boot_id": EXPECTED_ATTEMPT1_BOOT_ID,
            "attempt1_boot_id": provenance["attempt1_boot_id"], "attempt1_boot_id_match": True,
            "hostname": pins["hostname"], "pins": pins,
            "paper_head": pins["paper"]["commit"], "paper_identity": pins["paper_identity"],
            "runner_script_path": pins["runner_script_path"], "runner_script_sha256": pins["runner_script_sha256"],
            "child_script_path": pins["child_script_path"], "child_script_sha256": pins["child_script_sha256"],
            "gpu_limit_seconds": budget.limit, "gpu_cap_seconds": budget.cap_seconds,
            "budget": budget.record(), "serialisation_schema": UNIT_MANIFEST_SCHEMA,
            "templates": templates, "attempt1_provenance": provenance, "attempt1_inputs": inputs,
            "authorization": {"note": str(R.authorization_note("p3a") or ""),
                              "amendment_sha256": args.authorization_amend_sha256,
                              "expected_amendment_sha256": AUTHORIZATION_AMEND_SHA256,
                              "amendment_file_present": pins["authorization_amend_file_present"]},
            "marker": pins["marker"], "environment": environment,
            "probes_only": {"base": PROBES_ONLY_BASE, "dryrun_base": DRYRUN_BASE,
                            "dryrun_n_probe": DRYRUN_N_PROBE, "evidence_n_probe": EVIDENCE_N_PROBE,
                            "a3_short": True},
            "argv": list(sys.argv)}


def run_probes_only_campaign(args) -> None:
    """One GPU session: new root, marker, changed-path DRYRUN, the single 4b EVIDENCE probes unit; no retry."""
    validate_probes_only_args(args)
    environment = attempt1_environment()
    pins = verify_probes_only_pins(args.authorization_amend_sha256, disk_path=args.root.parent)
    provenance = build_attempt1_provenance(args.attempt1_root)
    assert_attempt1_pins(provenance)
    verify_attempt1_boot_id(pins["boot_id"], provenance["attempt1_boot_id"])   # MAJOR-1: journal-bound boot id
    kev_encoder = installed_kev_encoder()
    bases = (DRYRUN_BASE, PROBES_ONLY_BASE)
    unit_inputs = {base: attempt1_input(args.attempt1_root, base) for base in bases}
    provenance["loaded_artifacts"] = {base: {"loaded_artifact": value["loaded_artifact"],
                                             "model_files_sha256": value["model_files_sha256"],
                                             "loaded_hash": value["loaded_hash"]}
                                      for base, value in unit_inputs.items()}
    attempt1_manifests = {base: read_json_finite(Path(args.attempt1_root) / "EVIDENCE" / base / "final" / "manifest.json")
                          for base in bases}
    templates = {}
    for base in bases:
        family = unit_inputs[base]["saved_describe"].get("family")
        if family not in FRAMES:
            raise R.TrackPStop(f"attempt-1 {base} saved model family {family!r} has no declared frame")
        templates[family] = template_block(family, attempt1_manifests[base],
                                           unit_inputs[base]["saved_describe"], kev_encoder=kev_encoder)
    if set(templates) != {"kev", "qwen_control"}:
        raise R.TrackPStop(f"attempt-2 must declare exactly the two attempt-1 families; got {sorted(templates)}")
    for family, block in templates.items():   # attempt 2 runs the attempt-1 template, never a re-labelled one
        if block["template_id"] != EXPECTED_DERIVED_TEMPLATE_IDS[family]:
            raise R.TrackPStop(f"attempt-2 {family} template {block['template_id']!r} != derived attempt-1 "
                               f"{EXPECTED_DERIVED_TEMPLATE_IDS[family]!r}")
    args.root.mkdir(parents=True)
    journal = args.root / "journal.jsonl"
    new_lease_log = args.root / "gpu_lease_log.jsonl"
    budget = Attempt2Budget(provenance["gpu_seconds_total"], new_lease_log)
    state = {"template_id": templates["qwen_control"]["template_id"], "unit_template_id": None}
    sidecar_builder = make_sidecar_builder(provenance, unit_inputs, templates, kev_encoder,
                                           args.authorization_amend_sha256)
    unit_start_verifier = make_unit_start_verifier(args.attempt1_root, provenance, unit_inputs,
                                                   attempt1_manifests, templates, kev_encoder)
    try:
        emit(journal, campaign_start_record(args, pins, provenance, unit_inputs, templates, budget, environment))
        units = probes_only_units(args.attempt1_root)
        if [(unit["label"], unit["base"]) for unit in units] != [("DRYRUN", DRYRUN_BASE),
                                                                 ("EVIDENCE", PROBES_ONLY_BASE)]:
            raise R.TrackPStop("probes-only command sequence is not DRYRUN kev-0.8b then EVIDENCE qwen3.5-4b-base")
        with evidence_marker(journal, pins["marker"], state):
            for unit in units:
                family = unit_inputs[unit["base"]]["saved_describe"]["family"]
                template_id = templates[family]["template_id"]
                state["unit_template_id"] = template_id
                report = run_unit(args.root, journal, pins["boot_id"], budget, unit["label"], unit["base"],
                                  unit["unit"], unit["arguments"],
                                  projection_seconds=unit["projection_seconds"], template_id=template_id,
                                  attempt1_input={"root": provenance["root"],
                                                  "loaded_artifact": unit_inputs[unit["base"]]["loaded_artifact"],
                                                  "loaded_model_files_sha256":
                                                      unit_inputs[unit["base"]]["model_files_sha256"]},
                                  lease_mirror=new_lease_log, sidecar_builder=sidecar_builder,
                                  unit_start_verifier=unit_start_verifier)
                verify_a3_short_report(report, unit["label"], template_id)
        marker_end = state.get("marker_end") or {}
        if marker_end.get("rc") != 0:
            raise R.TrackPStop(f"trackp-evidence end {MARKER_PHASE} failed rc={marker_end.get('rc')}")
        emit(journal, {"event": "complete", "utc": R.utcnow(), "mode": "probes_only",
                       "gpu_seconds_total": budget.used, "template_id": state["template_id"],
                       "budget": budget.record()})
    except BaseException as exc:
        emit(journal, {"event": "STOP", "utc": R.utcnow(), "mode": "probes_only", "error": str(exc),
                       "gpu_seconds_total": budget.used,
                       "unobserved_lease_upper_s": budget.unobserved_lease_upper_s,
                       "template_id": state.get("unit_template_id") or state["template_id"],
                       "marker_end": state.get("marker_end")})
        raise


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--root", required=True, type=Path,
                    help="new campaign root (must not exist; attempt 2: a new p3a_attempt2_<UTC> directory)")
    ap.add_argument("--probes-only", action="store_true",
                    help="attempt 2: one new-root GPU session, changed-path DRYRUN then the single 4b probes unit")
    ap.add_argument("--base", help="probes-only: the single EVIDENCE base (qwen3.5-4b-base)")
    ap.add_argument("--attempt1-root", type=Path, help="probes-only: preserved attempt-1 root (read-only)")
    ap.add_argument("--a3-short", action="store_true",
                    help="probes-only: run the A3-short path (R1-P3A-OOM-OPTION3)")
    ap.add_argument("--authorization-amend-sha256", help="probes-only: reviewed 4 Nov amendment sha256")
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if socket.gethostname().lower().split(".")[0] != "tasl-7":
        raise R.TrackPStop("P.3a is authorized on TASL-7 only")
    if R.authorization_note("p3a") is None:
        raise R.TrackPStop("P.3a authorization missing")
    if args.probes_only:
        run_probes_only_campaign(args)
        return
    for flag, value in (("--base", args.base), ("--attempt1-root", args.attempt1_root),
                        ("--a3-short", args.a3_short),
                        ("--authorization-amend-sha256", args.authorization_amend_sha256)):
        if value:
            raise R.TrackPStop(f"{flag} is probes-only (--probes-only); the attempt-1 multi-base campaign is unchanged")
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
