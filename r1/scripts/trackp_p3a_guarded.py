"""One-shot P.3a supervisor. AI-assisted; DRYRUN then EVIDENCE; never resumes.

Attempt 1 (``p3a_operator_20261027``) ran the multi-base campaign below up to the interrupted
``qwen3.5-4b-base/probes`` unit (CUDA OOM in the descriptive A3 2k/8k loop). Attempt 2 runs **probes only** in a new
root, under the reviewed A3-short code delta, with attempt-1 provenance bound read-only and the 45-h lease clock
(36.318161 h used) sealed from attempt 1's journal STOP. ``--probes-only`` selects that path; without it the
attempt-1 campaign code path is unchanged. No bare ``trackp.py probes`` command is used by either path.

Host contract (R1-TRACKP-D2): attempt 2 accepts TASL-7 (normalized hostname ``tasl-7``, NVIDIA driver
``580.178.04``) or TASL-2 (``tasl-2``, driver ``535.309.01``), each with its own driver/freeze pin. The attempt-1
boot-id equality check is replaced by verification of the attempt-1 artifacts against their recorded hashes (journal,
the four ``EVIDENCE/<base>/final/manifest.json`` files and every saved/model file they list, the backup archive and
the attempt-1 lease log); the current boot id is recorded and disclosed, not compared.
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
# MAJOR-2 (round 2), byte-exact delivery identity. The reviewed *code* commit C cannot name itself (a commit sha
# covers the file that contains the pin), so C's ``EXPECTED_PAPER_HEAD`` still names the previous reviewed code
# commit and the single mechanical delivery-pin child D changes exactly that one canonical line to C. The preflight
# accepts exactly: C; a docs-only child of C whose ``r1/`` tree is byte-identical; and D, byte-for-byte C's runner
# blob with that one canonical assignment substituted (D^ == C, single parent, no other ``r1/`` change; docs files
# outside ``r1/`` may change). Nothing else is accepted, including any arbitrary descendant.
EXPECTED_PAPER_HEAD = "9dc4afbaa29546dafb1d1274e37d3910c5d9ed0e"          # reviewed probes-only runner commit
EXPECTED_PAPER_BRANCH = "trackp-p3a-code-20261116"        # or a detached HEAD at the pinned commit ("HEAD")
EXECUTING_RUNNER = Path(__file__).resolve()               # the runner actually executing (its sha256 is recorded)
PIN_LINE_TEMPLATE = 'EXPECTED_PAPER_HEAD = "{}"          # reviewed probes-only runner commit'
PIN_LINE_RE = re.compile(r'^EXPECTED_PAPER_HEAD = "[0-9a-f]{40}"[ \t]*(?:#[^\n]*)?$', re.MULTILINE)
# The executing checkout's runner/child/watched/imported files must be byte-identical to the ``HEAD:`` blobs:
# ``git status --porcelain --untracked-files=no`` (R.git_commit) misses assume-unchanged/skip-worktree edits and an
# executing copy outside the checkout, so the preflight re-hashes these files against HEAD (MAJOR-1/round-2).
EXECUTING_FILES = (PAPER_RUNNER_PATH, PAPER_CHILD_SCRIPT,
                   "r1/scripts/trackp_p3a_watchdog.py", "r1/scripts/trackp_p3a_gate.py",
                   "r1/c3/train/run.py", "r1/c3/train/types.py", "r1/c3/train/model.py",
                   "r1/c3/train/exam_run.py", "r1/c3/train/trainer.py", "r1/c3/train/registry.py",
                   "r1/c3/train/serialize.py", "r1/c3/labels.py")
HARNESS_PIN = "897d83c8efa364ec2fdd37288241cc42e01d7274"
E0_V1_PATH = "r1/c3/train/data/e0_v1.jsonl.gz"
E0_V1_SHA256 = "4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290"
RULE_PATH = "r1/c3/rules/p3_rule_v2.yaml"
RULE_SHA256 = "8c0ef9089589eafcea04aea9c5936c7ab57625d19f2a7ab736de204d09840242"
CONFIG_PATH = "r1/scripts/configs/trackp_portal.json"
CONFIG_APPROVED_COMMIT = "607e85e"
# --- host contract (R1-TRACKP-D2): two reviewed hosts, each with its own driver and freeze pin ---
HOST_TASL7 = "tasl-7"                       # attempt-1's host; the Unit B primary (R1-TRACKP-UNITB)
HOST_TASL2 = "tasl-2"                       # host-equivalence PASSED 17 Nov (R1-TRACKP-TASL2-HOST)
EXPECTED_DRIVER_TASL7 = "580.178.04"
EXPECTED_DRIVER_TASL2 = "535.309.01"
FREEZE_PIN = "docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt"   # TASL-7
# TASL-2 has no separate committed freeze file; its host-equivalence/rehearsal units recorded the portal freeze
# (121 lines, sha256 50238e5a…) as byte-identical to this committed file (== the TASL-7 pin's content).
FREEZE_PIN_TASL2 = "docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt"
MIN_FREE_DISK_BYTES = 10 * 1024 ** 3

# --- P.3a attempt-2 (probes-only) contract: authorization, attempt-1 provenance, template order, marker ---
PROBES_ONLY_BASE = "qwen3.5-4b-base"     # the single interrupted attempt-1 unit that is re-run
DRYRUN_BASE = "kev-0.8b"                 # cheap changed-path DRYRUN, first
# MINOR-4 (round 2): the DRYRUN is a short path-exercising run, not a replication of the attempt-1 probe sample.
# Attempt-1 probe leases at n=100 were 67.8-148.4 s (attempt-1 journal/reports), and n=8 exercises the same changed
# argv/A3 path; the real A3 budget rows (and A4/A5) are asserted from the DRYRUN child report by
# ``verify_a3_short_report`` (A3.protocol == v2_budget + the A3-short skipped marker), not by the sample count. The
# EVIDENCE unit keeps the planned n=100. Deviation from the accepted-plan review's attempt-1-style n=32 is recorded
# in the code-units record §2.6.
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
# The attempt-1 saved/models backup archive copied to both hosts (313 M; TASL-7 local, TASL-2 copy verified
# identical 17 Nov): `<attempt1-root>/../../backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz`.
ATTEMPT1_ARCHIVE_NAME = "p3a_attempt1_final_saved_20261117T0015Z.tar.gz"
EXPECTED_ATTEMPT1_ARCHIVE_SHA256 = "fa2437ee52d8873075c0bed6e88fba16d04deb2428e931a365dc602cdf902c87"
# The four attempt-1 EVIDENCE units whose `final/manifest.json` and listed saved/model files are hash-verified
# (journal `1e73e80f…`; TASL-2 has the same root staged from the archive at `/home/dowling/r1_trackp/runs/...`).
ATTEMPT1_EVIDENCE_BASES = ("kev-0.8b", "kev-4b", "qwen3.5-0.8b-base", "qwen3.5-4b-base")
ATTEMPT1_BASE_FAMILIES = {"kev-0.8b": "kev", "kev-4b": "kev",
                          "qwen3.5-0.8b-base": "qwen_control", "qwen3.5-4b-base": "qwen_control"}
ATTEMPT1_MANIFEST_SCHEMA = "trackp_run_manifest/v1"
# MINOR-1 (review round 1): the four `final/manifest.json` and `final/saved/manifest.json` bytes are pinned from the
# committed 16 Nov attempt-1 inventory capture (branch `ops-tasl-20261116`), so a self-consistent manifest/saved swap
# cannot pass the artifact verification.
EXPECTED_ATTEMPT1_MANIFEST_SHA256 = {
    "kev-0.8b": "5ee8842a9c7fda453b95bd50e187307b71eb1ce102e4308bd733ca0efbcb7006",
    "kev-4b": "9d7b333d859c24bc25e2c2e74821b87e6fba9cd675540081b01647eabcbec6bb",
    "qwen3.5-0.8b-base": "0381f73aeecae332ce509f291cd2d078cab7298ef3d1053468a222d9482244d1",
    "qwen3.5-4b-base": "9e1d5f08c5e3360870cbedd7eab3f7353fa9421cd8f055079c526ee10736c688",
}
EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256 = {
    "kev-0.8b": "26d80be0d7a6990c6867559c3337374c53e5c3ced22d15bf62c307e6f3ff090c",
    "kev-4b": "e898d51ac173dedf053851cc1b5b89c5407308966024671e3e78e39dfde02d57",
    "qwen3.5-0.8b-base": "8524b5033fb6f7094cd2cc022603107981bf93855d42db5f451f703f5d29e935",
    "qwen3.5-4b-base": "f4c366588a3727d51cda0dc1be1c6b04ff218ec6256b826a829303a569fce401",
}
EXPECTED_ATTEMPT1_PAPER_COMMIT = "b9ad6f8fe2e771732100f704accd7f2ce7cf20f0"
EXPECTED_ATTEMPT1_BOOT_ID = "2c9bb104-cc3c-4c60-be67-c1c8f0287fe4"   # attempt-1 journal campaign_start.boot_id
# BLOCKING-1 (round 2): the attempt-1 lease log is the live global ``<attempt1-root>/../gpu_lease_log.jsonl``
# (== R.LEASE_LOG on TASL-7) that the attempt-2 child appends to, so its bytes must be snapshotted read-only into the
# new root at campaign start and the unit-start verifier must check that immutable copy, never the growing live log.
# On TASL-2 the live global log is a different (TASL-2) log; the attempt-1 log was copied to
# ``<attempt1-root>/../_attempt1_gpu_lease_log.jsonl`` (sha 69505091…), hence the per-host discovery order.
ATTEMPT1_PROVENANCE_DIRNAME = "attempt1_provenance"
LEASE_LOG_SNAPSHOT_NAME = "gpu_lease_log.jsonl"
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


def normalized_hostname(hostname: str | None = None) -> str:
    """The normalized short hostname (lower-case, first label): ``TASL-7``/``tasl-7`` -> ``tasl-7``."""
    raw = socket.gethostname() if hostname is None else hostname
    return str(raw).strip().lower().split(".")[0]


def host_profile(hostname: str | None = None) -> dict:
    """R1-TRACKP-D2 host contract: the reviewed host's own driver pin, freeze pin, and lease-log discovery order.

    Two hosts are accepted: TASL-7 (driver ``580.178.04``, the attempt-1 host) and TASL-2 (driver ``535.309.01``,
    host-equivalence PASSED 17 Nov). Any other host, or the wrong driver for the matched host, is a STOP.
    """
    name = normalized_hostname(hostname)
    if name == HOST_TASL7:
        return {"name": HOST_TASL7, "expected_driver": EXPECTED_DRIVER_TASL7, "freeze_pin": FREEZE_PIN,
                "backup_dir_name": "backups",
                "attempt1_lease_log_names": ("gpu_lease_log.jsonl",)}
    if name == HOST_TASL2:
        return {"name": HOST_TASL2, "expected_driver": EXPECTED_DRIVER_TASL2, "freeze_pin": FREEZE_PIN_TASL2,
                "backup_dir_name": "backups",
                "attempt1_lease_log_names": ("_attempt1_gpu_lease_log.jsonl", "gpu_lease_log.jsonl")}
    raise R.TrackPStop(f"host {name!r} is not a reviewed P.3a host ({HOST_TASL7} or {HOST_TASL2}); STOP before any "
                       f"root/marker/GPU work")


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


def _git_bytes(*arguments, repo=None) -> bytes:
    repo = R.REPO if repo is None else Path(repo)
    res = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True, timeout=60)
    if res.returncode != 0:
        raise R.TrackPStop(f"git {' '.join(arguments)} failed in {repo}: "
                           f"{res.stderr.decode('utf-8', 'replace').strip()[:300]}")
    return res.stdout


def _git_text(*arguments, repo=None) -> str:
    return _git_bytes(*arguments, repo=repo).decode("utf-8").strip()


def _git_is_ancestor(ancestor: str, descendant: str, repo=None) -> bool:
    res = subprocess.run(["git", "-C", str(R.REPO if repo is None else repo), "merge-base", "--is-ancestor",
                          ancestor, descendant], capture_output=True, text=True, timeout=60)
    if res.returncode not in (0, 1):
        raise R.TrackPStop(f"cannot test ancestry of {ancestor!r} in {descendant!r}: {res.stderr.strip()[:300]}")
    return res.returncode == 0


def is_ancestor(commit: str, repo=R.REPO) -> bool:
    return _git_is_ancestor(commit, "HEAD", repo=repo)


def _r1_tree_equal(left: str, right: str, repo=None) -> bool:
    """True when two commits have byte-identical ``r1/`` trees (diff --quiet exit code 0)."""
    res = subprocess.run(["git", "-C", str(R.REPO if repo is None else repo), "diff", "--quiet",
                          left, right, "--", "r1/"], capture_output=True, text=True, timeout=60)
    if res.returncode not in (0, 1):
        raise R.TrackPStop(f"cannot compare r1/ trees of {left} and {right}: {res.stderr.strip()[:300]}")
    return res.returncode == 0


def canonical_paper_head_line(commit: str) -> str:
    """The single canonical ``EXPECTED_PAPER_HEAD`` assignment line (the only line a delivery pin may change)."""
    return PIN_LINE_TEMPLATE.format(commit)


def expected_pin_runner_blob(repo=None) -> bytes:
    """The exact runner bytes of the mechanical delivery-pin child of ``EXPECTED_PAPER_HEAD``.

    Take the reviewed code commit's runner blob and substitute its single canonical ``EXPECTED_PAPER_HEAD =
    "<40 hex>"`` line with the same canonical line naming ``EXPECTED_PAPER_HEAD`` (formatting/comment preserved by
    construction). The delivery pin is accepted only when its runner blob is byte-identical to this.
    """
    blob = _git_bytes("show", f"{EXPECTED_PAPER_HEAD}:{PAPER_RUNNER_PATH}", repo=repo)
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError as exc:      # pragma: no cover - the reviewed runner is UTF-8 text
        raise R.TrackPStop(f"reviewed runner blob is not UTF-8: {exc}") from exc
    matches = list(PIN_LINE_RE.finditer(text))
    if len(matches) != 1:
        raise R.TrackPStop(f"reviewed runner {EXPECTED_PAPER_HEAD}:{PAPER_RUNNER_PATH} must contain exactly one "
                           f"canonical EXPECTED_PAPER_HEAD assignment; found {len(matches)}")
    match = matches[0]
    return (text[:match.start()] + canonical_paper_head_line(EXPECTED_PAPER_HEAD) + text[match.end():]).encode()


def _delivery_pin_child(commit: str, repo=None) -> bool:
    """True only for the mechanical delivery-pin child D of ``EXPECTED_PAPER_HEAD`` (round-2 MAJOR-1, byte-exact).

    D must have exactly one parent, that parent must be ``EXPECTED_PAPER_HEAD``; ``D:r1/scripts/trackp_p3a_guarded.py``
    must be byte-identical to ``expected_pin_runner_blob()``; no other file under ``r1/`` may change (docs files
    outside ``r1/`` may, e.g. the code-units record). A one-line child with injected code, or any other code edit,
    is refused.
    """
    try:
        parents = _git_text("rev-list", "--parents", "-n", "1", commit, repo=repo).split()
        if len(parents) != 2 or parents[1] != EXPECTED_PAPER_HEAD:
            return False
        changed = set(_git_text("diff", "--name-only", EXPECTED_PAPER_HEAD, commit, repo=repo).splitlines())
        if PAPER_RUNNER_PATH not in changed:
            return False
        outside_runner = changed - {PAPER_RUNNER_PATH}
        if any(not path.startswith("docs/") for path in outside_runner):
            return False
        expected = expected_pin_runner_blob(repo=repo)
    except R.TrackPStop:
        return False
    return _git_bytes("show", f"{commit}:{PAPER_RUNNER_PATH}", repo=repo) == expected


def _docs_child_of_reviewed(commit: str, repo=None) -> bool:
    """True for a descendant of ``EXPECTED_PAPER_HEAD`` whose ``r1/`` tree is byte-identical (docs-only child).

    Kept as a function-level acceptance (the round-1 record's docs-child branch is re-based on EXPECTED_PAPER_HEAD
    instead of the stale ``8a3d3eaf`` constant, which is an ancestor with a different ``r1/`` tree). It is a
    theoretical identity only: because the executing files must equal the ``HEAD:`` blobs (see
    ``verify_executing_files``) and the pin lives in those bytes, a clean checkout runs only the delivery-pin child.
    """
    if commit == EXPECTED_PAPER_HEAD:
        return False
    if not _git_is_ancestor(EXPECTED_PAPER_HEAD, commit, repo=repo):
        return False
    return _r1_tree_equal(EXPECTED_PAPER_HEAD, commit, repo=repo)


def verify_paper_head(paper: dict, repo=None) -> dict:
    """MAJOR-2 (round 2): byte-exact reviewed-commit identity, not merely "a descendant of the base pin".

    Accepted identities: (i) the reviewed code commit ``EXPECTED_PAPER_HEAD``; (ii) a docs-only child of it whose
    ``r1/`` tree is byte-identical; (iii) the single mechanical delivery-pin child D, byte-exact as computed by
    ``expected_pin_runner_blob``. Anything else -- an arbitrary descendant, an ancestor, a crafted one-line child,
    a child that edits another ``r1/`` file -- is a STOP before any root/marker/GPU work.
    """
    branch = paper.get("branch")
    if branch not in (EXPECTED_PAPER_BRANCH, "HEAD"):
        raise R.TrackPStop(f"paper branch {branch!r} is not {EXPECTED_PAPER_BRANCH!r} or a detached HEAD at the "
                           f"reviewed commit")
    commit = paper.get("commit")
    if commit == EXPECTED_PAPER_HEAD:
        kind = "exact_reviewed_runner_commit"
    elif _docs_child_of_reviewed(commit, repo=repo):
        kind = "docs_child_r1_identical"
    elif _delivery_pin_child(commit, repo=repo):
        kind = "delivery_pin_child"
    else:
        raise R.TrackPStop(f"paper HEAD {commit!r} is not the reviewed code commit {EXPECTED_PAPER_HEAD!r}, a "
                           f"docs-only child of it with a byte-identical r1/ tree, or its byte-exact mechanical "
                           f"delivery-pin child; STOP")
    if not is_ancestor(EXPECTED_PAPER_HEAD, repo or R.REPO):
        raise R.TrackPStop(f"reviewed runner commit {EXPECTED_PAPER_HEAD!r} is not an ancestor of paper HEAD "
                           f"{commit!r}")
    return {"kind": kind, "commit": commit, "branch": branch, "expected_commit": EXPECTED_PAPER_HEAD,
            "runner_script_path": PAPER_RUNNER_PATH}


def verify_executing_files(repo=None) -> dict:
    """MAJOR-1 (round 2): pin the executing bytes, not only the checkout.

    The runner that is executing must be the tracked runner of ``repo`` at ``PAPER_RUNNER_PATH``, and every
    ``EXECUTING_FILES`` entry must be byte-identical to its ``<HEAD>:`` blob. This refuses a modified copy run from
    elsewhere, an ``assume-unchanged``/``skip-worktree``/ignored edit that ``git status --porcelain
    --untracked-files=no`` does not report, and any untracked difference. Each file's sha256 is recorded.
    """
    repo = Path(R.REPO if repo is None else repo)
    executing = Path(EXECUTING_RUNNER).resolve()
    tracked_runner = (repo / PAPER_RUNNER_PATH).resolve()
    if executing != tracked_runner:
        raise R.TrackPStop(f"executing runner {executing} is not the tracked runner {tracked_runner} of the paper "
                           f"checkout; run the reviewed checkout's own script")
    if not is_ancestor(EXPECTED_PAPER_HEAD, repo):
        raise R.TrackPStop(f"reviewed runner commit {EXPECTED_PAPER_HEAD!r} is not an ancestor of paper HEAD")
    files = {}
    for relative in EXECUTING_FILES:
        path = repo / relative
        if not path.is_file():
            raise R.TrackPStop(f"executing file missing from the checkout: {path}")
        on_disk = path.read_bytes()
        try:
            committed = _git_bytes("show", f"HEAD:{relative}", repo=repo)
        except R.TrackPStop as exc:
            raise R.TrackPStop(f"executing file {relative} is not tracked at HEAD: {exc}") from exc
        if on_disk != committed:
            raise R.TrackPStop(f"executing file {relative} differs from HEAD:{relative} (dirty/untracked/ignored "
                               f"working-tree difference); STOP before any root/marker/GPU work")
        files[relative] = {"path": str(path), "sha256": hashlib.sha256(on_disk).hexdigest(), "bytes": len(on_disk)}
    return {"repo": str(repo), "runner_script_path": str(executing),
            "runner_script_sha256": files[PAPER_RUNNER_PATH]["sha256"], "files": files}


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
    if R.host_driver_snapshot()["boot_id"] != boot_id:
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
    # TASL-7 child records ``tasl7_driver`` (unchanged); a reviewed portal host records ``host_driver``.
    driver = manifest.get("tasl7_driver") or manifest.get("host_driver") or {}
    if manifest.get("evidence_label") != label or driver.get("boot_id") != boot_id:
        raise R.TrackPStop(f"unit manifest label or boot ID mismatch: {directory}")
    if gpu:
        events = manifest.get("gpu_lease", [])
        if [e.get("event") for e in events] != ["start", "end"] or start is None or end is None:
            raise R.TrackPStop(f"unit lacks complete lease record: {directory}")
        if any(((e.get("tasl7_driver") or e.get("host_driver")) or {}).get("boot_id") != boot_id for e in events):
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


def attempt1_journal_facts(attempt1_root) -> dict:
    """Read-only facts of the pinned attempt-1 journal (hash, STOP GPU seconds, paper commit, boot id).

    This is the immutable half of the attempt-1 provenance: it never reads the live global lease log, so it is safe
    to re-run at every ``unit_start`` (BLOCKING-1, round 2).
    """
    root = Path(attempt1_root)
    if root.is_symlink() or not root.is_dir():
        raise R.TrackPStop(f"attempt-1 root missing or symlinked: {root}")
    journal = root / "journal.jsonl"
    if journal.is_symlink():
        raise R.TrackPStop(f"attempt-1 journal must be a plain file, not a symlink: {journal}")
    if not journal.is_file():
        raise R.TrackPStop(f"attempt-1 journal missing: {journal}")
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
            "journal_events": len(events), "stop_utc": stops[0].get("utc"),
            "paper_commit": paper["commit"], "paper_branch": paper.get("branch"),
            "paper_dirty": paper.get("dirty"),
            "attempt1_boot_id": attempt1_boot_id,
            "gpu_seconds_total": float(gpu_seconds), "gpu_hours_total": float(gpu_seconds) / 3600}


def _require_plain_file(path, what: str) -> Path:
    """Fail closed unless ``path`` is a regular non-symlink file (attempt-1 artifacts are plain files)."""
    path = Path(path)
    if path.is_symlink():
        raise R.TrackPStop(f"attempt-1 {what} must be a plain file, not a symlink: {path}")
    if not path.is_file():
        raise R.TrackPStop(f"attempt-1 {what} missing: {path}")
    return path


def _require_plain_dir(path, what: str) -> Path:
    """Fail closed unless ``path`` is a real directory (MINOR-2: intermediate symlinks are not followed)."""
    path = Path(path)
    if path.is_symlink():
        raise R.TrackPStop(f"attempt-1 {what} must be a plain directory, not a symlink: {path}")
    if not path.is_dir():
        raise R.TrackPStop(f"attempt-1 {what} missing: {path}")
    return path


def verify_attempt1_manifest(attempt1_root, base: str, *, attempt1_boot_id: str | None = None) -> dict:
    """Verify one ``EVIDENCE/<base>/final/manifest.json`` and every saved/model file it lists.

    The attempt-1 manifest schema is ``trackp_run_manifest/v1``: ``model_files_sha256`` maps each relative saved-file
    path to its sha256, and ``final/saved/manifest.json`` repeats that map as ``files``. Every listed file is re-hashed
    from disk; a missing, symlinked, extra or mismatched file is a STOP (fail closed, R1-TRACKP-D2).
    """
    evidence = _require_plain_dir(Path(attempt1_root) / "EVIDENCE", "EVIDENCE directory")
    base_dir = _require_plain_dir(evidence / base, f"EVIDENCE/{base} directory")
    final = _require_plain_dir(base_dir / "final", f"{base}/final directory")
    manifest_path = _require_plain_file(final / "manifest.json", f"{base}/final/manifest.json")
    manifest = read_json_finite(manifest_path)
    manifest_sha256 = sha256_file(manifest_path)
    if manifest_sha256 != EXPECTED_ATTEMPT1_MANIFEST_SHA256[base]:
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json sha256 {manifest_sha256} != recorded "
                           f"{EXPECTED_ATTEMPT1_MANIFEST_SHA256[base]}")
    if manifest.get("schema") != ATTEMPT1_MANIFEST_SCHEMA:
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json schema {manifest.get('schema')!r} is not "
                           f"{ATTEMPT1_MANIFEST_SCHEMA!r}")
    if manifest.get("evidence_label") != "EVIDENCE":
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json evidence_label "
                           f"{manifest.get('evidence_label')!r} is not 'EVIDENCE'")
    expected_family = ATTEMPT1_BASE_FAMILIES[base]
    family = (manifest.get("base") or {}).get("family")
    if family != expected_family:
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json family {family!r} is not {expected_family!r}")
    recorded = manifest.get("model_files_sha256")
    if not isinstance(recorded, dict) or not recorded:
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json records no model_files_sha256")
    saved = _require_plain_dir(final / "saved", f"{base}/final/saved directory")
    files = {}
    for relative, digest in recorded.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json has a non-string model file entry")
        relative_path = Path(relative)
        if not relative or relative_path.is_absolute() or ".." in relative_path.parts:
            raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json records an unsafe model file path {relative!r}")
        target = _require_plain_file(saved / relative_path, f"{base}/final/saved/{relative}")
        actual = sha256_file(target)
        if actual != digest:
            raise R.TrackPStop(f"attempt-1 model file {base}/final/saved/{relative} sha256 {actual} != its recorded "
                               f"{digest}")
        files[relative] = {"sha256": actual, "bytes": target.stat().st_size}
    saved_manifest_path = _require_plain_file(saved / "manifest.json", f"{base}/final/saved/manifest.json")
    saved_manifest = read_json_finite(saved_manifest_path)
    saved_manifest_sha256 = sha256_file(saved_manifest_path)
    if saved_manifest_sha256 != EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256[base]:
        raise R.TrackPStop(f"attempt-1 {base}/final/saved/manifest.json sha256 {saved_manifest_sha256} != recorded "
                           f"{EXPECTED_ATTEMPT1_SAVED_MANIFEST_SHA256[base]}")
    if saved_manifest.get("files") != recorded:
        raise R.TrackPStop(f"attempt-1 {base}/final/saved/manifest.json files disagree with final/manifest "
                           f"model_files_sha256")
    if saved_manifest.get("family") not in (None, expected_family):
        raise R.TrackPStop(f"attempt-1 {base}/final/saved/manifest.json family "
                           f"{saved_manifest.get('family')!r} is not {expected_family!r}")
    present = {path.relative_to(saved).as_posix() for path in saved.rglob("*")
               if path.is_file() or path.is_symlink()}
    unrecorded = sorted(present - set(recorded) - {"manifest.json"})
    if unrecorded:
        raise R.TrackPStop(f"attempt-1 {base}/final/saved has unrecorded files: {unrecorded}")
    # MINOR-1 (review round 1): the identity metadata is required, not merely cross-checked when present, so a
    # manifest stripped of its attempt-1 identity cannot pass even with a re-pinned hash.
    git = manifest.get("git") or {}
    driver = manifest.get("tasl7_driver") or {}
    for field, actual, expected in (
        ("git.paper.commit", (git.get("paper") or {}).get("commit"), EXPECTED_ATTEMPT1_PAPER_COMMIT),
        ("git.harness.commit", (git.get("harness") or {}).get("commit"), HARNESS_PIN),
        ("tasl7_driver.boot_id", driver.get("boot_id"), attempt1_boot_id),
    ):
        if expected is not None and actual != expected:
            raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json records {field}={actual!r} != required "
                               f"{expected!r}")
    recorded_drivers = driver.get("nvidia_smi_driver")
    values = [str(value).strip() for value in (recorded_drivers or [])]
    if not values or any(value != EXPECTED_DRIVER_TASL7 for value in values):
        raise R.TrackPStop(f"attempt-1 {base}/final/manifest.json recorded NVIDIA driver {recorded_drivers!r} is not "
                           f"the required attempt-1 host driver {EXPECTED_DRIVER_TASL7}")
    return {"base": base, "family": expected_family, "manifest": str(manifest_path),
            "manifest_sha256": manifest_sha256, "model_files_sha256": recorded,
            "verified_files": files, "saved": str(saved),
            "saved_manifest": str(saved_manifest_path), "saved_manifest_sha256": saved_manifest_sha256,
            "model_file_count": len(files)}


def attempt1_archive_path(attempt1_root, profile: dict | None = None) -> Path:
    """The attempt-1 backup archive: ``<attempt1-root>/../../backups/<archive>`` on both reviewed hosts."""
    profile = profile or host_profile()
    return Path(attempt1_root).parent.parent / profile.get("backup_dir_name", "backups") / ATTEMPT1_ARCHIVE_NAME


def verify_attempt1_archive(attempt1_root, profile: dict | None = None) -> dict:
    """Verify the attempt-1 saved/models backup archive against its recorded sha256."""
    path = attempt1_archive_path(attempt1_root, profile)
    if path.parent.is_symlink():
        raise R.TrackPStop(f"attempt-1 backup directory must be a plain directory, not a symlink: {path.parent}")
    path = _require_plain_file(path, "backup archive")
    digest = sha256_file(path)
    if digest != EXPECTED_ATTEMPT1_ARCHIVE_SHA256:
        raise R.TrackPStop(f"attempt-1 backup archive {path} sha256 {digest} != recorded "
                           f"{EXPECTED_ATTEMPT1_ARCHIVE_SHA256}")
    return {"path": str(path), "sha256": digest, "bytes": path.stat().st_size,
            "path_rule": "<attempt1-root>/../../backups/<archive>"}


def attempt1_lease_log_candidates(attempt1_root, profile: dict | None = None) -> list[Path]:
    """The host-ordered attempt-1 lease-log candidates under ``<attempt1-root>/..``."""
    profile = profile or host_profile()
    parent = Path(attempt1_root).parent
    if parent.is_symlink():
        raise R.TrackPStop(f"attempt-1 runs directory must be a plain directory, not a symlink: {parent}")
    return [parent / name for name in profile.get("attempt1_lease_log_names") or ()]


def attempt1_lease_log_path(attempt1_root, profile: dict | None = None) -> Path:
    """Host-aware attempt-1 lease-log discovery, shared by the verifier, provenance and the lease-log snapshot.

    TASL-7: ``<attempt1-root>/../gpu_lease_log.jsonl`` (the live global log at attempt-1's end). TASL-2: the staged
    attempt-1 copy ``<attempt1-root>/../_attempt1_gpu_lease_log.jsonl`` (TASL-2's live global log is a different log),
    with the global-log name as a fail-closed fallback. Missing/symlinked candidates STOP.
    """
    profile = profile or host_profile()
    candidates = attempt1_lease_log_candidates(attempt1_root, profile)
    tried = [str(path) for path in candidates]
    for path in candidates:
        if path.is_symlink():
            raise R.TrackPStop(f"attempt-1 lease log must be a plain file, not a symlink: {path}")
        if path.is_file():
            return path
    raise R.TrackPStop(f"attempt-1 lease log missing on host {profile['name']!r}; tried {tried}")


def verify_attempt1_lease_log(attempt1_root, profile: dict | None = None) -> dict:
    """Verify the attempt-1 lease log (host-discovered) against its recorded sha256."""
    profile = profile or host_profile()
    path = attempt1_lease_log_path(attempt1_root, profile)
    candidates = [str(candidate) for candidate in attempt1_lease_log_candidates(attempt1_root, profile)]
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_ATTEMPT1_LEASE_LOG_SHA256:
        raise R.TrackPStop(f"attempt-1 lease log {path} sha256 {digest} != recorded "
                           f"{EXPECTED_ATTEMPT1_LEASE_LOG_SHA256}; candidates {candidates}")
    return {"path": str(path), "sha256": digest, "bytes": len(data), "lines": data.count(b"\n"),
            "host": profile["name"], "candidates": candidates}


def verify_attempt1_artifacts(attempt1_root, current_boot_id: str, profile: dict | None = None) -> dict:
    """R1-TRACKP-D2: bind attempt 1 by its recorded artifact hashes and record the current boot id.

    This replaces the old attempt-1 boot-id equality check. The current boot id is *recorded and disclosed*, never
    compared with the attempt-1 boot id: the attempt-1 identity is bound by the recorded hashes of its journal, the
    four ``EVIDENCE/<base>/final/manifest.json`` files and every saved/model file they list, the backup archive, and
    the attempt-1 lease log. Any missing or mismatched artifact is a STOP before the attempt-2 root exists.
    """
    if not isinstance(current_boot_id, str) or not current_boot_id.strip():
        raise R.TrackPStop("current boot id is empty; it must be recorded with the attempt-1 artifact record")
    profile = profile or host_profile()
    root = Path(attempt1_root)
    if root.is_symlink() or not root.is_dir():
        raise R.TrackPStop(f"attempt-1 root missing: {root}")
    facts = attempt1_journal_facts(root)
    if facts["journal_sha256"] != EXPECTED_ATTEMPT1_JOURNAL_SHA256:
        raise R.TrackPStop(f"attempt-1 journal sha256 {facts['journal_sha256']} != recorded "
                           f"{EXPECTED_ATTEMPT1_JOURNAL_SHA256}")
    if facts["paper_commit"] != EXPECTED_ATTEMPT1_PAPER_COMMIT:
        raise R.TrackPStop(f"attempt-1 journal paper commit {facts['paper_commit']!r} != recorded "
                           f"{EXPECTED_ATTEMPT1_PAPER_COMMIT!r}")
    if facts["attempt1_boot_id"] != EXPECTED_ATTEMPT1_BOOT_ID:
        raise R.TrackPStop(f"attempt-1 journal boot id {facts['attempt1_boot_id']!r} != recorded "
                           f"{EXPECTED_ATTEMPT1_BOOT_ID!r}")
    manifests = {base: verify_attempt1_manifest(root, base, attempt1_boot_id=facts["attempt1_boot_id"])
                 for base in ATTEMPT1_EVIDENCE_BASES}
    archive = verify_attempt1_archive(root, profile)
    lease = verify_attempt1_lease_log(root, profile)
    return {"schema": "trackp_p3a_attempt1_artifacts/v1", "attempt1_root": str(root), "host": profile["name"],
            "current_boot_id": current_boot_id,
            "attempt1_boot_id": facts["attempt1_boot_id"],
            "boot_id_matches_attempt1": current_boot_id == facts["attempt1_boot_id"],
            "boot_id_required": False,
            "journal": {key: facts[key] for key in ("journal", "journal_sha256", "journal_events", "stop_utc",
                                                    "paper_commit", "paper_branch", "paper_dirty",
                                                    "attempt1_boot_id", "gpu_seconds_total", "gpu_hours_total")},
            "expected": {"journal_sha256": EXPECTED_ATTEMPT1_JOURNAL_SHA256,
                         "archive_sha256": EXPECTED_ATTEMPT1_ARCHIVE_SHA256,
                         "lease_log_sha256": EXPECTED_ATTEMPT1_LEASE_LOG_SHA256,
                         "archive_name": ATTEMPT1_ARCHIVE_NAME,
                         "evidence_bases": list(ATTEMPT1_EVIDENCE_BASES)},
            "manifests": manifests, "archive": archive, "lease_log": lease,
            "verified_utc": R.utcnow(),
            "note": "the attempt-1 boot id is provenance only; the current boot id is recorded and attempt 1 is bound "
                    "by its recorded artifact hashes (no boot-id equality check)"}


def build_attempt1_provenance(attempt1_root, *, artifacts: dict | None = None,
                              profile: dict | None = None) -> dict:
    """Read-only attempt-1 provenance: journal/lease-log hashes, paper commit and the STOP GPU seconds.

    MAJOR-1 (review round 1): the attempt-1 lease log is discovered per host (TASL-7 live global log; TASL-2 staged
    ``_attempt1_gpu_lease_log.jsonl``). The campaign passes the preflight's verified ``attempt1_artifacts`` record
    (path + sha256 re-checked here); direct callers pass ``profile``. ``snapshot_attempt1_lease_log`` then snapshots
    this selected path (BLOCKING-1), so a TASL-2 run snapshots the attempt-1 copy, never the different live TASL-2 log.
    """
    root = Path(attempt1_root)
    facts = attempt1_journal_facts(root)
    if artifacts is not None:
        verified = artifacts.get("lease_log") or {}
        path, recorded = verified.get("path"), verified.get("sha256")
        if not path or not recorded:
            raise R.TrackPStop("attempt-1 artifact record carries no verified lease log path/sha256")
        lease_log = Path(path)
        if lease_log.is_symlink() or not lease_log.is_file():
            raise R.TrackPStop(f"attempt-1 lease log missing: {lease_log}")
        digest = sha256_file(lease_log)
        if digest != recorded:
            raise R.TrackPStop(f"attempt-1 lease log changed after the preflight verification: {digest} != "
                               f"{recorded}")
        lease_source = f"verified preflight artifact record ({artifacts.get('host', 'unknown host')})"
    else:
        profile = profile or host_profile()
        lease_log = attempt1_lease_log_path(root, profile)
        digest = sha256_file(lease_log)
        if digest != EXPECTED_ATTEMPT1_LEASE_LOG_SHA256:
            raise R.TrackPStop(f"attempt-1 lease log {lease_log} sha256 {digest} != recorded "
                               f"{EXPECTED_ATTEMPT1_LEASE_LOG_SHA256}")
        lease_source = f"host-aware discovery for {profile['name']}"
    facts.update({"lease_log": str(lease_log), "lease_log_sha256": digest, "lease_log_source": lease_source,
                  "expected_attempt1_boot_id": EXPECTED_ATTEMPT1_BOOT_ID,
                  "derived_prompt_version": EXPECTED_PROMPT_VERSION, "derived_order": TEMPLATE_ORDER,
                  "derived_template_ids_by_family": dict(EXPECTED_DERIVED_TEMPLATE_IDS),
                  "recorded_at_run_time": False, "label": "derived",
                  "derivation": {"doc": M13_ORDER_RECORD, "sha256": M13_ORDER_RECORD_SHA256}})
    return facts


def snapshot_attempt1_lease_log(root, provenance: dict) -> dict:
    """BLOCKING-1 (round 2): copy the attempt-1 lease-log bytes into the new root and make the copy read-only.

    ``provenance["lease_log"]`` is the host-aware attempt-1 log selected by ``build_attempt1_provenance`` (TASL-7:
    the live global log that attempt 2's own child keeps appending to, so it cannot be re-hashed at unit starts;
    TASL-2: the staged ``_attempt1_gpu_lease_log.jsonl`` copy). This snapshot is created after the new root exists and
    before any journal/marker/child work; the bytes must equal the ``lease_log_sha256`` recorded (and pinned) at
    campaign start. Nothing is written into attempt 1.
    """
    root = Path(root)
    source = Path(provenance["lease_log"])
    destination = root / ATTEMPT1_PROVENANCE_DIRNAME / LEASE_LOG_SNAPSHOT_NAME
    if destination.exists() or destination.is_symlink():
        raise R.TrackPStop(f"attempt-1 lease-log snapshot already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != provenance["lease_log_sha256"]:
        raise R.TrackPStop(f"attempt-1 lease log changed between campaign start and the snapshot: {digest} != "
                           f"{provenance['lease_log_sha256']}")
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(descriptor, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.chmod(destination, 0o444)                    # read-only copy: no later accidental write
    if sha256_file(destination) != digest or destination.stat().st_size != len(data):
        raise R.TrackPStop(f"attempt-1 lease-log snapshot did not round-trip: {destination}")
    return {"schema": "trackp_p3a_attempt1_lease_log_snapshot/v1", "path": str(destination),
            "sha256": digest, "bytes": len(data), "lines": data.count(b"\n"),
            "source": str(source), "source_sha256_at_snapshot": digest, "read_only": True, "mode": "0444",
            "created_utc": R.utcnow(),
            "note": "immutable attempt-1 lease-log copy; the live global log grows during attempt 2 and is never "
                    "re-hashed at unit starts (only its campaign-start hash is provenance metadata)"}


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


def verify_probes_only_pins(amend_sha256: str, disk_path=None, attempt1_root=None) -> dict:
    """Attempt-2 fail-closed live preflight (Unit A plan §1c.2; R2 conditions 2 and 6; R1-TRACKP-D2 hosts).

    When ``attempt1_root`` is given the preflight also records the attempt-1 artifact-hash verification and the
    current boot id (no boot-id equality check; the artifacts carry the attempt-1 identity).
    """
    if amend_sha256 != AUTHORIZATION_AMEND_SHA256:
        raise R.TrackPStop(f"--authorization-amend-sha256 {amend_sha256!r} is not the reviewed "
                           f"{AUTHORIZATION_AMEND_SHA256!r}")
    profile = host_profile()                       # R1-TRACKP-D2: tasl-7 or tasl-2, each with its own driver pin
    paper = R.git_commit(R.REPO)
    if paper["dirty"]:
        raise R.TrackPStop(f"paper checkout dirty: {paper['dirty_files'][:5]}")
    paper_identity = verify_paper_head(paper)
    executing = verify_executing_files()          # MAJOR-1 (round 2): the executing bytes must be HEAD's bytes
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
    frozen = (R.REPO / profile["freeze_pin"]).read_text()
    if sorted(actual.splitlines()) != sorted(frozen.splitlines()):
        raise R.TrackPStop(f"run environment freeze does not match the recorded {profile['name']} pin")
    from r1.c3.train.registry import reverify
    bad = reverify(R.REPO / "r1/c3/train/registry.yaml")
    if bad:
        raise R.TrackPStop(f"registered model files mismatch: {bad[:5]}")
    driver = R.host_driver_snapshot(profile["expected_driver"])
    drivers = [line.strip() for line in (driver.get("nvidia_smi_driver") or [])]
    if not drivers or any(value != profile["expected_driver"] for value in drivers):
        raise R.TrackPStop(f"NVIDIA driver {drivers} is not the reviewed {profile['expected_driver']} for host "
                           f"{profile['name']}")
    boot_id = driver.get("boot_id")
    if not isinstance(boot_id, str) or not boot_id.strip():
        raise R.TrackPStop("current boot id is empty; the attempt-2 preflight must record it")
    artifacts = None
    if attempt1_root is not None:
        artifacts = verify_attempt1_artifacts(attempt1_root, boot_id, profile=profile)
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
            "freeze": f"matches the recorded {profile['name']} freeze pin", "model_registry": "all files reverified",
            "hostname": socket.gethostname(), "host": profile["name"],
            "host_profile": {"name": profile["name"], "expected_driver": profile["expected_driver"],
                             "freeze_pin": profile["freeze_pin"],
                             "attempt1_lease_log_names": list(profile["attempt1_lease_log_names"])},
            "expected_driver": profile["expected_driver"],
            "boot_id": boot_id, "boot_id_required": False,
            "attempt1_artifacts": artifacts,
            "driver": driver,
            "runner_script_path": executing["runner_script_path"],
            "runner_script_sha256": executing["runner_script_sha256"],
            "executing_files": executing,
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


def make_unit_start_verifier(attempt1_root, provenance: dict, snapshot: dict, unit_inputs: dict,
                             attempt1_manifests: dict, campaign_templates: dict, kev_encoder: dict):
    """M4/M13 §3.3: re-read the *immutable* attempt-1 provenance/input hashes and recompute the declared template at
    ``unit_start`` (before the child is spawned) and STOP on any drift. The post-child template check stays.

    BLOCKING-1 (round 2): the attempt-1 lease log is the live global log that this campaign's own children append to,
    so this verifier re-hashes the read-only campaign-start snapshot (and the pinned journal, which is immutable),
    never the live log. Only the snapshot bytes and byte count are compared.
    """
    def verify(*, label, base):
        facts = attempt1_journal_facts(attempt1_root)      # immutable journal only: no live lease-log read
        for key in ("journal_sha256", "paper_commit", "attempt1_boot_id"):
            if facts.get(key) != provenance.get(key):
                raise R.TrackPStop(f"attempt-1 provenance drift at {label}/{base} unit start: {key}")
        if abs(float(facts["gpu_seconds_total"]) - float(provenance["gpu_seconds_total"])) > 1e-6:
            raise R.TrackPStop(f"attempt-1 provenance drift at {label}/{base} unit start: gpu_seconds_total")
        snapshot_path = Path(snapshot["path"])
        if not snapshot_path.is_file():
            raise R.TrackPStop(f"attempt-1 lease-log snapshot missing at {label}/{base} unit start: {snapshot_path}")
        snapshot_sha256 = sha256_file(snapshot_path)
        snapshot_bytes = snapshot_path.stat().st_size
        if snapshot_sha256 != snapshot["sha256"]:
            raise R.TrackPStop(f"attempt-1 lease-log snapshot drift at {label}/{base} unit start: {snapshot_sha256} "
                               f"!= {snapshot['sha256']}")
        if snapshot_bytes != snapshot["bytes"]:
            raise R.TrackPStop(f"attempt-1 lease-log snapshot size drift at {label}/{base} unit start: "
                               f"{snapshot_bytes} != {snapshot['bytes']}")
        if snapshot_sha256 != provenance.get("lease_log_sha256"):
            raise R.TrackPStop(f"attempt-1 lease-log snapshot disagrees with the campaign-start pin at {label}/{base} "
                               f"unit start")
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
                "journal_sha256": facts["journal_sha256"],
                "lease_log_snapshot_path": str(snapshot_path),
                "lease_log_snapshot_sha256": snapshot_sha256,
                "lease_log_snapshot_bytes": snapshot_bytes,
                "lease_log_source": "immutable campaign-start snapshot (the live global log grows and is not checked)"}
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
            "boot_id": pins["boot_id"], "boot_id_required": False,
            "expected_attempt1_boot_id": EXPECTED_ATTEMPT1_BOOT_ID,
            "attempt1_boot_id": provenance["attempt1_boot_id"],
            "attempt1_boot_id_match": pins["boot_id"] == provenance["attempt1_boot_id"],   # MINOR-5: disclosed only
            "host": pins["host"], "hostname": pins["hostname"],
            "attempt1_artifacts": pins.get("attempt1_artifacts"), "pins": pins,
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
    pins = verify_probes_only_pins(args.authorization_amend_sha256, disk_path=args.root.parent,
                                   attempt1_root=args.attempt1_root)
    # R1-TRACKP-D2: the preflight bound attempt 1 by its recorded artifact hashes and recorded the current boot id;
    # there is no attempt-1 boot-id equality gate any more (the boot id is disclosed in the journal, not compared).
    if not pins.get("attempt1_artifacts"):
        raise R.TrackPStop("attempt-1 artifact verification record missing from the preflight; STOP")
    # MAJOR-1 (review round 1): provenance/assert/snapshot use the *verified* host-discovered attempt-1 lease log
    # (TASL-7 live global log; TASL-2 staged `_attempt1_gpu_lease_log.jsonl`), never a second hard-wired path.
    provenance = build_attempt1_provenance(args.attempt1_root, artifacts=pins["attempt1_artifacts"])
    assert_attempt1_pins(provenance)
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
    # BLOCKING-1: after the new root exists and before any journal/marker/child, snapshot the mutable global
    # attempt-1 lease log read-only; every unit start verifies that immutable copy, not the growing live log.
    snapshot = snapshot_attempt1_lease_log(args.root, provenance)
    provenance["lease_log_snapshot"] = snapshot
    journal = args.root / "journal.jsonl"
    new_lease_log = args.root / "gpu_lease_log.jsonl"
    budget = Attempt2Budget(provenance["gpu_seconds_total"], new_lease_log)
    state = {"template_id": templates["qwen_control"]["template_id"], "unit_template_id": None}
    sidecar_builder = make_sidecar_builder(provenance, unit_inputs, templates, kev_encoder,
                                           args.authorization_amend_sha256)
    unit_start_verifier = make_unit_start_verifier(args.attempt1_root, provenance, snapshot, unit_inputs,
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
    if args.probes_only:
        host_profile()          # R1-TRACKP-D2: TASL-7 or TASL-2, each with its own driver/freeze pin
    elif normalized_hostname() != HOST_TASL7:
        raise R.TrackPStop("the attempt-1 multi-base campaign is authorized on TASL-7 only")
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
