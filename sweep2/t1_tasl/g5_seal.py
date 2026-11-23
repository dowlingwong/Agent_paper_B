"""G.5 T1 labels on the TASL pair: the seal step, the sealed tree's access-logged reader, the TASL-7 server seal and
the proposer spans (G.5 code unit part 3b-2). AI-assisted (Claude). EVIDENCE table.

Authority: the G.5 authorization draft revision 8 (``docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md``) §6
(sealing and staged release), §4 STOP 11, §9, §10 C6, C9; the seal list of part 3b-1's report §5 item 8 and its
review's carried items (ruling 2: the G5-TASL-GPUH B meter from TASL-7's server spans).

**The seal is procedural** (§6; ``key_values.seal_mode: procedural``). The operator, the cluster agent and the author
share one account, so file modes restrict nobody. What the seal adds is checkable: every sealed directory carries
``SEAL_RECEIPT.json`` with the sha256 of every file in it (changes are detected; reads are not), nothing is ever
overwritten, and every opening of sealed content goes through ``SealedTree`` (or, on TASL-7, ``open_server_log``),
which requires the release lock of its purpose and writes one line to the sealed tree's ``ACCESS_LOG.jsonl`` (who,
when, why, which lock) before anything is read; ``check_access_log`` is STOP 11 over that log. The encryption
alternative (§6, C6) is **not built**: ``check_seal_mode`` refuses any other mode.

**What is sealed** (3b-1 report §5 item 8 and its review):
- ``seal_attempt``: one attempt of a job or audit chunk (``out.tar``, ``job_record.json``, ``diagnostics.json``,
  ``SHA256SUMS``, its node wrapper log, and any ``out/`` left in clear after a tar failure, a deadline or a crash,
  as ``out_clear.tar``; the clear ``out/`` is removed only after the sealed tar is verified). A closed attempt
  (``close-attempt``) has a record and no sums: its receipt is its only integrity record.
- ``seal_node``: after every attempt of the node is sealed and none is running, the node's audit plans (``plan.tar``
  and ``plan_index.json`` per wave) and its ``wave_checks_wave<N>.json``.
- ``seal_run``: after every started node is sealed, the run-level files: the job-code access log
  ``_access_log.jsonl``, ``_k_lock.json``, ``_refusals/`` and ``_logs/`` (as tars), and ``_server_spans/``.
- ``seal_server`` (on TASL-7): a stopped server's ``server-N/`` (``server_record.json``, ``server_end.json``,
  ``llama-server.log``, ``bin_manifest.txt``) as ``server.tar`` under ``proposer.sealed_root``; the clear
  ``llama-server.log`` (it holds the prompts, which carry per-step metric values) is removed after the tar is verified
  (option (a) of 3b-1 §5 item 8). While the server runs, the log is in clear on TASL-7, governed by STOP 11 alone;
  option (b), prompt logging off, changes ``server_argv`` and is the author's decision (not built here).

**Locks** (§6, PRE-STAGE A, REL-SCOPE A). Each purpose names the release row it needs:
``assembly traindev`` and ``release integrity traindev`` need R1-T1-LABELS-UNSEAL; ``assembly test``, ``release
integrity test`` and ``server log`` need R1-T1-LABELS-TEST-RELEASE (and the test row needs the arms-frozen record,
which ``release.release_row`` checks); the two ``release integrity`` purposes also need the release step's integrity
context (``release.integrity_context``, the §6 carve-out). The row checks are ``r1.c3.release.release_row`` itself
(the committed PLAN, the exact row text, its bindings). The job code's own reads during the table (audit planning, the
wave E5 on the label seeds) stay with ``g5_job.access`` and its log, which this step seals.

**Proposer spans** (G5-TASL-GPUH B; 3b-1 review ruling 2). ``seal_server`` writes the server's span (``started_utc``
of its record to ``stopped_utc`` of its end) into its receipt. ``register_server_span`` files a copy of that receipt on
TASL-2 under ``<run_id>/_server_spans/``, and ``proposer_seconds`` counts the proposer card from those spans; a server
named by a campaign job record without a registered span is counted as open until now (an upper bound). Under B an
audit job refuses until every campaign's server has its span registered (``require_server_spans``).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g5_tasl as S  # noqa: E402

L = G.L
Stop = G.Stop
RECEIPT_SCHEMA = "g5_tasl_seal_receipt/1"
SERVER_RECEIPT_SCHEMA = "g5_tasl_server_seal_receipt/1"
ACCESS_SCHEMA = "g5_tasl_sealed_access/1"
RECEIPT = "SEAL_RECEIPT.json"
ACCESS_LOG = "ACCESS_LOG.jsonl"
WHO = "g5_seal"
ATTEMPT_FILES = ("out.tar", "job_record.json", "diagnostics.json", "SHA256SUMS")
UNSEAL_ROW, TEST_ROW = "R1-T1-LABELS-UNSEAL", "R1-T1-LABELS-TEST-RELEASE"
# purpose prefix -> (stage of the release row it needs, needs the release step's integrity context)
PURPOSES = {"assembly traindev:": ("traindev", False), "assembly test:": ("test", False),
            "release integrity traindev:": ("traindev", True), "release integrity test:": ("test", True),
            "server log:": ("test", False)}
CHUNK = re.compile(r"^chunk-(0|[1-9][0-9]*)$")
SERVER = re.compile(r"^server-[1-9][0-9]*$")
UTC = "%Y-%m-%dT%H:%M:%SZ"
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def utc(t: float | None = None) -> str:
    return time.strftime(UTC, time.gmtime(t if t is not None else time.time()))


def parse_utc(s: str) -> float:
    return datetime.strptime(s, UTC).replace(tzinfo=timezone.utc).timestamp()


def check_seal_mode(spec: dict) -> str:
    """Only the procedural seal is built (§6). The encryption alternative (``out.tar`` encrypted inside the job to the
    author's release key) needs its own code, key handling and cluster test C6: refused here."""
    mode = spec["key_values"].get("seal_mode")
    if mode != "procedural":
        raise Stop(f"STOP: seal_mode {mode!r}: only the procedural seal (receipts and access log) is built; the "
                   f"encryption alternative of §6 is not built (needs its own code unit and cluster test C6)")
    return mode


def run_root(spec: dict) -> Path:
    return Path(spec["worker"]["runs_root"]) / spec["run_id"]


def sealed_run(spec: dict) -> Path:
    return Path(spec["worker"]["sealed_root"]) / spec["run_id"]


def _no_symlink(target: Path) -> None:
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists() or p.is_symlink()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")


def _files(d: Path) -> dict[str, str]:
    """{relative name: sha256} of every regular file under ``d`` except the receipt; a symlink or other entry STOPs."""
    out = {}
    for p in sorted(Path(d).rglob("*")):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise Stop(f"STOP: {p} in a sealed directory is not a regular file")
        if p.is_file() and p.name != RECEIPT:
            out[p.relative_to(d).as_posix()] = L._sha_file(p)
    return out


def _write_receipt(target: Path, receipt: dict) -> dict:
    receipt = {"schema": RECEIPT_SCHEMA, "label": S.EVIDENCE, "seal_mode": "procedural", **receipt,
               "sealed_path": str(target), "files": _files(target), "who": WHO, "host": socket.gethostname(),
               "sealed_utc": utc()}
    with (target / RECEIPT).open("x") as fh:
        fh.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    return receipt


def verify_sealed(d: Path) -> dict:
    """A sealed directory against its receipt: every file listed with its sha256, none missing, none extra."""
    d = Path(d)
    rp = d / RECEIPT
    if rp.is_symlink() or not rp.is_file():
        raise Stop(f"STOP: {d} has no {RECEIPT}")
    receipt = json.loads(rp.read_text())
    if receipt.get("schema") not in (RECEIPT_SCHEMA, SERVER_RECEIPT_SCHEMA):
        raise Stop(f"STOP: {rp} is not a G.5 seal receipt")
    got = _files(d)
    if got != receipt.get("files"):
        diff = sorted(set(got.items()) ^ set((receipt.get("files") or {}).items()))
        raise Stop(f"STOP: {d} differs from its seal receipt (sealed content changed): {diff[:4]}")
    return receipt


def _tar_dir(src_parent: Path, name: str, tar_path: Path) -> int:
    """``tar -cf tar_path -C src_parent name``, then verify the tar lists exactly the files under it; returns the count."""
    files = sorted(p.relative_to(src_parent).as_posix() for p in (src_parent / name).rglob("*") if p.is_file())
    if subprocess.run(["tar", "-cf", str(tar_path), "-C", str(src_parent), name], capture_output=True).returncode:
        raise Stop(f"STOP: cannot tar {src_parent / name}")
    with tarfile.open(tar_path) as tar:
        listed = sorted(m.name for m in tar if m.isfile())
    if listed != files:
        raise Stop(f"STOP: {tar_path} does not hold exactly the files of {src_parent / name}")
    return len(files)


# =============================================================================================== seal steps
def _attempt_parts(spec: dict, attempt_dir: Path) -> dict:
    try:
        rel = Path(attempt_dir).resolve().relative_to(run_root(spec).resolve()).parts
    except ValueError:
        raise Stop(f"STOP: {attempt_dir} is not <run_id>/<node>/<job>[/chunk-i]/attempt-N of this run") from None
    if len(rel) not in (3, 4) or rel[0] not in S.T1_NODES or rel[1] not in S.JOBS or not G.ATTEMPT.fullmatch(rel[-1]):
        raise Stop(f"STOP: {attempt_dir} is not <run_id>/<node>/<job>[/chunk-i]/attempt-N")
    kind, _ = rel[1].split("-wave")
    chunk = None
    if kind == "audits":
        if len(rel) != 4 or not CHUNK.fullmatch(rel[2]):
            raise Stop(f"STOP: an audit attempt lives under its chunk: {attempt_dir}")
        chunk = int(rel[2].split("-")[1])
    elif len(rel) != 3:
        raise Stop(f"STOP: a campaign attempt has no chunk: {attempt_dir}")
    return {"rel": Path(*rel), "node": rel[0], "job": rel[1], "chunk": chunk, "attempt": int(rel[-1].split("-")[1])}


def seal_attempt(spec: dict, attempt_dir: Path) -> dict:
    """Seal one finished attempt (a job record exists) to ``<sealed_root>/<run_id>/<same path>/``, never overwriting:
    the sums are verified (when the attempt has them), the four transfer files and the node wrapper log are copied,
    and an ``out/`` left in clear is sealed as ``out_clear.tar`` and then removed from the runs tree."""
    check_seal_mode(spec)
    src = Path(attempt_dir)
    if src.is_symlink():
        raise Stop(f"STOP: {src} is a symlink")
    parts = _attempt_parts(spec, src)
    rec_path = src / "job_record.json"
    if not rec_path.is_file():
        raise Stop(f"STOP: {src} has no job record (running, or close it with close-attempt first)")
    record = json.loads(rec_path.read_text())
    want = {"schema": "g5_tasl_job_record/1", "label": S.EVIDENCE, "run_id": spec["run_id"], "node": parts["node"],
            "job": parts["job"], "chunk": parts["chunk"], "attempt": parts["attempt"]}
    bad = [k for k, v in want.items() if record.get(k) != v]
    if bad:
        raise Stop(f"STOP: {rec_path} does not match its place in the run: {bad}")
    sums = src / "SHA256SUMS"
    if sums.is_file():
        if subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=src, capture_output=True).returncode:
            raise Stop(f"STOP: {src} does not verify against its SHA256SUMS")
    elif record.get("stop") is None or (src / "out.tar").exists():
        raise Stop(f"STOP: {src} has no SHA256SUMS; only a closed attempt (a STOP without out.tar) may lack them")
    target = sealed_run(spec) / parts["rel"]
    _no_symlink(target)
    target.mkdir(parents=True, mode=0o700)
    copied = []
    for name in ATTEMPT_FILES:
        if (src / name).is_file():
            shutil.copy2(src / name, target / name)
            copied.append(name)
    log = record.get("node_log")
    logs_dir = (run_root(spec) / "_logs").resolve()
    node_log = None
    if log and Path(log).is_file() and Path(log).resolve().parent == logs_dir:
        shutil.copy2(log, target / "node.log")
        node_log = str(log)
    out_clear = None
    if (src / "out").is_dir():                   # a tar failure, a deadline or a crash left out/ in clear
        out_clear = _tar_dir(src, "out", target / "out_clear.tar")
    receipt = _write_receipt(target, {"kind": "attempt", "run_id": spec["run_id"], "node": parts["node"],
                                      "job": parts["job"], "chunk": parts["chunk"], "attempt": parts["attempt"],
                                      "source": str(src), "copied": copied, "node_log": node_log,
                                      "out_clear_files": out_clear, "stop": record.get("stop"),
                                      "stop_class": record.get("stop_class"),
                                      "job_record_sha256": L._sha_file(target / "job_record.json")})
    if out_clear is not None:
        shutil.rmtree(src / "out")               # sealed and verified: out/ leaves the clear runs tree
    return receipt


def sealed_attempt_of(spec: dict, attempt_dir: Path) -> Path:
    return sealed_run(spec) / _attempt_parts(spec, attempt_dir)["rel"]


def _node_attempts(spec: dict, node: str) -> list[Path]:
    root = run_root(spec) / node
    out = []
    for job in S.JOBS:
        base = root / job
        if not base.is_dir():
            continue
        dirs = sorted(base.glob("chunk-*")) if job.startswith("audits") else [base]
        for d in dirs:
            out += [p for _, p in G.attempts(d)]
    return out


def node_finished(spec: dict, node: str) -> str | None:
    """Why the node has ended: its wave-2 checks are written, or a node or timing STOP is on record (as
    ``g5_job.node_stopped`` reads them); None while it can still run."""
    root = run_root(spec) / node
    if (root / "wave_checks_wave2.json").is_file():
        return "wave 2 checked"
    for rec in sorted(root.rglob("job_record.json")):
        if json.loads(rec.read_text()).get("stop_class") in ("node", "timing"):
            return f"STOP on record: {rec.parent.relative_to(root)}"
    for wc in sorted(root.glob("wave_checks_wave*.json")):
        if any(s.get("class") in ("node", "timing") for s in json.loads(wc.read_text()).get("stops", [])):
            return f"STOP on record: {wc.name}"
    return None


def seal_node(spec: dict, node: str) -> dict:
    """Seal a node's audit plans and wave checks once the node has ended (``node_finished``) and every attempt of
    it is sealed (none running, none unsealed, the sealed copy's record equal to the runs tree's)."""
    check_seal_mode(spec)
    S.node_entry(spec, node)
    ended = node_finished(spec, node)
    if ended is None:
        raise Stop(f"STOP: {node} has not ended (no wave-2 checks and no node STOP): its plans are sealed at its end")
    attempts = _node_attempts(spec, node)
    for a in attempts:
        if not (a / "job_record.json").is_file():
            raise Stop(f"STOP: {a} has no job record: the node is still running (or close the attempt first)")
        sealed = sealed_attempt_of(spec, a)
        verify_sealed(sealed)
        if L._sha_file(sealed / "job_record.json") != L._sha_file(a / "job_record.json"):
            raise Stop(f"STOP: {a}'s sealed record differs from the runs tree's")
    target = sealed_run(spec) / node / "_node"
    _no_symlink(target)
    target.mkdir(parents=True, mode=0o700)
    names = []
    for wave in (1, 2):
        d = run_root(spec) / node / f"audits-wave{wave}"
        for name in ("plan.tar", "plan_index.json"):
            if (d / name).is_file():
                shutil.copy2(d / name, target / f"wave{wave}_{name}")
                names.append(f"wave{wave}_{name}")
        wc = run_root(spec) / node / f"wave_checks_wave{wave}.json"
        if wc.is_file():
            shutil.copy2(wc, target / wc.name)
            names.append(wc.name)
    for wave in (1, 2):                          # a plan is sealed with its index, and the index binds the tar
        idx = target / f"wave{wave}_plan_index.json"
        if idx.is_file() and json.loads(idx.read_text())["plan_tar_sha256"] != L._sha_file(target / f"wave{wave}_plan.tar"):
            raise Stop(f"STOP: {node} wave {wave}: plan.tar differs from its index")
    return _write_receipt(target, {"kind": "node", "run_id": spec["run_id"], "node": node, "copied": names,
                                   "ended": ended, "attempts": [str(a) for a in attempts]})


def seal_run(spec: dict, *, not_run: tuple = ()) -> dict:
    """Seal the run-level files once the table has ended: every node sealed, or declared ``not_run`` (refused at the
    switch, e.g. STOP 5, so it has no node directory); then the job-code access log, the K lock, the refusals and
    the node wrapper logs (as tars) and the registered server spans."""
    check_seal_mode(spec)
    root = run_root(spec)
    unknown = sorted(set(not_run) - set(S.T1_NODES))
    if unknown:
        raise Stop(f"STOP: {unknown} are not G.5 nodes")
    for node in S.T1_NODES:
        if node in not_run:
            if (root / node).exists():
                raise Stop(f"STOP: {node} is declared not run but has a node directory")
            continue
        if not (root / node).is_dir():
            raise Stop(f"STOP: {node} has not run; the run is sealed at the table's end (declare it --not-run if "
                       f"the switch refused it)")
        verify_sealed(sealed_run(spec) / node / "_node")
    target = sealed_run(spec) / "_run"
    _no_symlink(target)
    target.mkdir(parents=True, mode=0o700)
    names = []
    for name in ("_access_log.jsonl", "_k_lock.json"):
        if (root / name).is_file():
            shutil.copy2(root / name, target / name)
            names.append(name)
    for name in ("_refusals", "_logs", "_server_spans"):
        if (root / name).is_dir():
            _tar_dir(root, name, target / f"{name.lstrip('_')}.tar")
            names.append(f"{name.lstrip('_')}.tar")
    return _write_receipt(target, {"kind": "run", "run_id": spec["run_id"], "copied": names,
                                   "not_run": sorted(not_run)})


# =============================================================================================== locks, the reader
def release_lock(stage: str) -> dict:
    """The T1 release row of ``stage`` on the committed PLAN, through ``r1.c3.release.release_row`` (exact text,
    preregistration, split file, release-code commit; for the test row the arms-frozen record; for the train/dev row
    the G.1b summaries). A missing or changed row raises ``ReleaseStop``."""
    if str(S.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(S.REPO_ROOT))
    from r1.c3 import release as R          # noqa: PLC0415 - imported only when a lock is checked
    return R.release_row("T1", stage)


def in_integrity_context() -> bool:
    if str(S.REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(S.REPO_ROOT))
    from r1.c3 import release as R          # noqa: PLC0415
    return bool(R._INTEGRITY.get())


def require(purpose: str, *, lock=None) -> dict:
    """The lock of a purpose: its release row (and the train/dev row too for a test purpose), and for the release
    integrity purposes the release step's integrity context. Returns what the access log records."""
    hit = [p for p in PURPOSES if purpose.startswith(p)]
    if len(hit) != 1:
        raise Stop(f"STOP 11: sealed G.5 content is opened only for a declared purpose {sorted(PURPOSES)}, not "
                   f"{purpose!r}")
    stage, integrity = PURPOSES[hit[0]]
    if integrity and not in_integrity_context():
        raise Stop(f"STOP 11: {hit[0]!r} reads run only inside the release step's integrity check (§6 carve-out)")
    check = lock or release_lock
    rows = [check("traindev")] + ([check("test")] if stage == "test" else [])
    return {"stage": stage, "rows": [{"row_id": r["row_id"], "decision_sha256": r["decision_sha256"]} for r in rows]}


class SealedTree:
    """The access-logged reader of the sealed G.5 tree on TASL-2. Every opening checks the purpose's lock, verifies
    the sealed directory against its receipt, and logs one line before anything is read."""

    def __init__(self, spec: dict, *, lock=None, who: str = WHO):
        self.spec, self.lock, self.who = spec, lock, who
        self.root = sealed_run(spec)

    def log(self, path: Path, purpose: str, grant: dict) -> dict:
        entry = {"schema": ACCESS_SCHEMA, "utc": utc(), "who": self.who, "pid": os.getpid(),
                 "host": socket.gethostname(), "path": str(path), "sha256": L._sha_file(path), "purpose": purpose,
                 "lock": grant}
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ACCESS_LOG).open("a") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def open_members(self, sealed_dir: Path, tar_name: str, wanted, purpose: str) -> dict[str, bytes]:
        """The named members (a tuple of names, or a compiled pattern whose group 1 names the member) of one tar in a
        sealed directory, as bytes; nothing else in the tar is opened."""
        grant = require(purpose, lock=self.lock)
        sealed_dir = Path(sealed_dir)
        if self.root.resolve() not in sealed_dir.resolve().parents:
            raise Stop(f"STOP: {sealed_dir} is not in this run's sealed tree")
        verify_sealed(sealed_dir)
        tar_path = sealed_dir / tar_name
        self.log(tar_path, purpose, grant)
        out = {}
        with tarfile.open(tar_path) as tar:
            for m in tar:
                if not m.isfile():
                    continue
                if isinstance(wanted, tuple):
                    key = m.name if m.name in wanted else None
                else:
                    hit = wanted.fullmatch(m.name)
                    key = hit.group(1) if hit else None
                if key is not None:
                    if key in out:
                        raise Stop(f"STOP: {tar_path} holds {key} twice")
                    out[key] = tar.extractfile(m).read()
        if isinstance(wanted, tuple) and sorted(out) != sorted(wanted):
            raise Stop(f"STOP: {tar_path} lacks {sorted(set(wanted) - set(out))}")
        return out


def check_access_log(spec: dict, *, root: Path | None = None) -> list[dict]:
    """STOP 11 over a sealed tree's access log: every line by this step's code, for a declared purpose, with the
    rows its lock names."""
    log = Path(root or sealed_run(spec)) / ACCESS_LOG
    out = [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.is_file() else []
    bad = []
    for e in out:
        hit = [p for p in PURPOSES if str(e.get("purpose", "")).startswith(p)]
        rows = [r.get("row_id") for r in (e.get("lock") or {}).get("rows") or []]
        need = [UNSEAL_ROW] + ([TEST_ROW] if hit and PURPOSES[hit[0]][0] == "test" else [])
        if e.get("schema") != ACCESS_SCHEMA or e.get("who") != WHO or len(hit) != 1 or rows != need:
            bad.append(e)
    if bad:
        raise Stop(f"STOP 11: sealed G.5 content opened outside a declared, locked purpose: {bad[:3]}")
    return out


# =============================================================================================== TASL-7: the server
def proposer_sealed_run(spec: dict) -> Path:
    return Path(spec["proposer"]["sealed_root"]) / spec["run_id"]


def seal_server(spec: dict, server_dir: Path, *, alive=None) -> dict:
    """On TASL-7: seal a stopped server's ``server-N/`` as ``server.tar`` under ``proposer.sealed_root`` with a receipt
    that carries its span, then remove the clear ``llama-server.log`` (it holds the prompts). The server must have
    ended (``server_end.json`` binding its record and log) and its process must be gone."""
    check_seal_mode(spec)
    src = Path(server_dir)
    expected = Path(spec["proposer"]["run_dir"]) / spec["run_id"]
    if src.is_symlink() or src.resolve().parent != expected.resolve() or not SERVER.fullmatch(src.name):
        raise Stop(f"STOP: {src} is not a server-N directory of {expected}")
    for name in ("server_record.json", "server_end.json", "llama-server.log"):
        if not (src / name).is_file() or (src / name).is_symlink():
            raise Stop(f"STOP: {src} has no {name} (a running server is sealed after it stops)")
    rec = json.loads((src / "server_record.json").read_text())
    end = json.loads((src / "server_end.json").read_text())
    same_dir = Path(str(rec.get("server_dir"))).resolve() == src.resolve()
    if rec.get("run_id") != spec["run_id"] or not same_dir:
        raise Stop("STOP: the server record names another run or directory")
    if end.get("server_record_sha256") != L._sha_file(src / "server_record.json") or \
            end.get("server_log_sha256") != L._sha_file(src / "llama-server.log"):
        raise Stop("STOP: server_end.json does not bind this record and log (changed after the server stopped)")

    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
    if rec.get("pid") is not None and (alive or _alive)(int(rec["pid"])):
        raise Stop(f"STOP: the server process {rec['pid']} is still alive")
    started, stopped = rec.get("started_utc"), end.get("stopped_utc")
    try:
        span = parse_utc(stopped) - parse_utc(started)
    except (TypeError, ValueError):
        raise Stop("STOP: the server record and end need started_utc and stopped_utc") from None
    if span < 0:
        raise Stop("STOP: the server stopped before it started")
    target = proposer_sealed_run(spec) / src.name
    _no_symlink(target)
    target.mkdir(parents=True, mode=0o700)
    _tar_dir(src.parent, src.name, target / "server.tar")
    with tarfile.open(target / "server.tar") as tar:
        log_member = hashlib.sha256(tar.extractfile(f"{src.name}/llama-server.log").read()).hexdigest()
    if log_member != end["server_log_sha256"]:
        raise Stop("STOP: the sealed server.tar does not hold the log server_end.json binds")
    receipt = {"schema": SERVER_RECEIPT_SCHEMA, "label": S.EVIDENCE, "seal_mode": "procedural", "kind": "server",
               "run_id": spec["run_id"], "server": src.name, "source": str(src), "pid": rec.get("pid"),
               "started_utc": started, "stopped_utc": stopped, "span_seconds": round(span, 1),
               "server_record_sha256": end["server_record_sha256"], "server_log_sha256": end["server_log_sha256"],
               "server_end_sha256": L._sha_file(src / "server_end.json"), "sealed_path": str(target),
               "files": _files(target), "who": WHO, "host": socket.gethostname(), "sealed_utc": utc()}
    with (target / RECEIPT).open("x") as fh:
        fh.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    (src / "llama-server.log").unlink()          # sealed and verified: the prompts leave the clear tree
    return receipt


def open_server_log(spec: dict, server: str, purpose: str, *, lock=None) -> bytes:
    """A sealed server log, only after the T1 test release row (it holds prompts with per-step metric values), with a
    line in the TASL-7 sealed tree's access log."""
    grant = require(purpose, lock=lock)
    if not purpose.startswith("server log:"):
        raise Stop("STOP 11: a server log is opened only for the 'server log:' purpose")
    d = proposer_sealed_run(spec) / server
    receipt = verify_sealed(d)
    tree = SealedTree(spec, lock=lock)
    tree.root = proposer_sealed_run(spec)
    tree.log(d / "server.tar", purpose, grant)
    with tarfile.open(d / "server.tar") as tar:
        raw = tar.extractfile(f"{receipt['server']}/llama-server.log").read()
    return raw


# =============================================================================================== TASL-2: spans, meter
def spans_dir(spec: dict) -> Path:
    return run_root(spec) / "_server_spans"


def register_server_span(spec: dict, receipt_path: Path) -> dict:
    """File a TASL-7 server seal receipt (copied to TASL-2) under ``<run_id>/_server_spans/<server>.json``: the span
    of one server for the G5-TASL-GPUH B meter. Written once; the same bytes again are accepted, different bytes STOP."""
    raw = Path(receipt_path).read_bytes()
    r = json.loads(raw)
    if r.get("schema") != SERVER_RECEIPT_SCHEMA or r.get("run_id") != spec["run_id"] or \
            not SERVER.fullmatch(str(r.get("server"))) or not re.fullmatch(r"[0-9a-f]{64}", str(r.get("server_record_sha256"))):
        raise Stop(f"STOP: {receipt_path} is not a server seal receipt of {spec['run_id']}")
    span = parse_utc(r["stopped_utc"]) - parse_utc(r["started_utc"])
    if span < 0 or abs(span - float(r["span_seconds"])) > 1.0:
        raise Stop("STOP: the receipt's span does not match its times")
    d = spans_dir(spec)
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"{r['server']}.json"
    if target.exists():
        if target.read_bytes() != raw:
            raise Stop(f"STOP: {target} exists with other content (a span is registered once)")
        return r
    with target.open("xb") as fh:
        fh.write(raw)
    return r


def registered_spans(spec: dict) -> dict[str, dict]:
    """{server_record_sha256: receipt} of the registered spans."""
    out = {}
    d = spans_dir(spec)
    for p in sorted(d.glob("server-*.json")) if d.is_dir() else []:
        r = json.loads(p.read_text())
        if r.get("schema") != SERVER_RECEIPT_SCHEMA or r.get("run_id") != spec["run_id"] or \
                p.name != f"{r.get('server')}.json":
            raise Stop(f"STOP: {p} is not a registered server span of this run")
        if r["server_record_sha256"] in out:
            raise Stop(f"STOP: two registered spans name the server record {r['server_record_sha256'][:12]}")
        out[r["server_record_sha256"]] = r
    return out


def campaign_servers(spec: dict) -> dict[str, str]:
    """{server_record_sha256: started_utc} of the servers named by the run's G.5 campaign job records."""
    out = {}
    root = run_root(spec)
    for rec in sorted(root.rglob("job_record.json")) if root.is_dir() else []:
        r = json.loads(rec.read_text())
        sr = r.get("server_record") or {}
        if r.get("schema") == "g5_tasl_job_record/1" and str(r.get("job", "")).startswith("campaigns") and sr:
            if not re.fullmatch(r"[0-9a-f]{64}", str(sr.get("sha256"))) or not sr.get("started_utc"):
                raise Stop(f"STOP: {rec} names a server record without its sha256 and start time")
            out[sr["sha256"]] = sr["started_utc"]
    return out


def proposer_seconds(spec: dict, *, now=time.time) -> dict:
    """The proposer card's held seconds (G5-TASL-GPUH B): every registered span, plus, for a server a campaign job
    record names without a registered span, the time from its start until now (an open span; an upper bound)."""
    spans = registered_spans(spec)
    used = campaign_servers(spec)
    closed = sum(float(r["span_seconds"]) for r in spans.values())
    open_ = {sha: max(0.0, now() - parse_utc(start)) for sha, start in used.items() if sha not in spans}
    return {"seconds": round(closed + sum(open_.values()), 1), "registered": len(spans), "open": len(open_),
            "open_servers": sorted(open_)}


def require_server_spans(spec: dict) -> dict:
    """Under G5-TASL-GPUH B, before an audit job: every server a campaign job used has stopped and its span is
    registered, so the meter counts closed spans only."""
    spans = registered_spans(spec)
    missing = sorted(sha for sha in campaign_servers(spec) if sha not in spans)
    if missing:
        raise Stop(f"STOP: G5-TASL-GPUH B: the span of the server(s) {[m[:12] for m in missing]} is not registered; "
                   f"seal the stopped server on TASL-7 (seal-server) and register its receipt here (server-span) "
                   f"before an audit job")
    return {"registered": len(spans)}
