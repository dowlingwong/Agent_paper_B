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
when, why, which lock, which kind and members) before anything is read; ``check_access_log`` is STOP 11 over that log
(TASL-2's, and TASL-7's for the server seal). A purpose takes only the members of its kind (the ledgers, a plan, a
chunk's two members), and a chunk's rows leave the reader only reduced to the stage's seeds (``reduce_rows``: at the
train/dev stage no evaluation-seed kind or value is returned). Each seal step writes into ``<target>.partial`` and
renames it after the receipt; a leftover ``.partial`` is an interrupted seal and STOPs. The runs-tree copies of
``out.tar`` and ``plan.tar`` stay in clear after the seal (the job code reads them during the table; nobody opens them
after). The encryption alternative (§6, C6) is **not built**: ``check_seal_mode`` refuses any other mode.

**What is sealed** (3b-1 report §5 item 8 and its review):
- ``seal_attempt``: one attempt of a job or audit chunk (``out.tar``, ``job_record.json``, ``diagnostics.json``,
  ``SHA256SUMS``, its node wrapper log, and any ``out/`` left in clear after a tar failure, a deadline or a crash,
  as ``out_clear.tar``; the clear ``out/`` is removed only after the sealed tar is verified). A closed attempt
  (``close-attempt``) has a record and no sums: its receipt is its only integrity record.
- R1-G5-AUDIT-TWO-CARDS: ``seal_node`` refuses while the node has an open TASL-7 claim, and ``seal_run`` while any
  claim is open or, where TASL-7 had claims, without the final registration of TASL-7's access log after every other
  TASL-7 record (``check_remote_final``); ``node_finished`` does not report a node with an open claim as ended.
- ``seal_node``: after every attempt of the node is sealed and none is running, the node's audit plans (``plan.tar``
  and ``plan_index.json`` per wave) and its ``wave_checks_wave<N>.json``.
- ``seal_run``: after every started node is sealed, the run-level files: the job-code access log
  ``_access_log.jsonl``, ``_k_lock.json``, ``_refusals/`` and ``_logs/`` (as tars), ``_server_spans/``, and
  ``_remote/`` (R1-G5-AUDIT-TWO-CARDS: the TASL-7 chunk claims, the registration records and the registered copies of
  TASL-7's job-code access log; the registered TASL-7 attempts themselves lie in their chunks and are sealed as
  attempts).
- ``seal_server`` (on TASL-7): a stopped server's ``server-N/`` (``server_record.json``, ``server_end.json``,
  ``llama-server.log``, ``bin_manifest.txt``) as ``server.tar`` under ``proposer.sealed_root``; the clear
  ``llama-server.log`` (it holds the prompts, which carry per-step metric values) is removed after the tar is verified
  (option (a) of 3b-1 §5 item 8). While the server runs, the log is in clear on TASL-7, governed by STOP 11 alone;
  option (b), prompt logging off, changes ``server_argv`` and is the author's decision (not built here).
  ``close_server`` closes a server that ended without ``server_end.json`` (killed, OOM, reboot), guarded like
  close-attempt, with the closing time as its conservative end, so that it can be sealed.

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
named by a campaign job record without a registered span, and a gap in the registered server numbers, are counted as
open until now (upper bounds). Under B an audit job refuses until every campaign's server has its span registered and
the registered servers are server-1..N without a gap (``require_server_spans``).
"""
from __future__ import annotations

import hashlib
import json
import math
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


# R1-G5-AUDIT-TWO-CARDS: the TASL-7 claims under <run_id>/_remote (written by g5_job; their state is read here, where
# the seal needs it, and g5_job uses these helpers)
REMOTE = "_remote"
REMOTE_HOST = "TASL-7"


def claim_files(spec: dict) -> list[Path]:
    root = run_root(spec) / REMOTE / "claims"
    return sorted(root.glob("*/audits-wave*/chunk-*.json")) if root.is_dir() else []


def abandon_path(spec: dict, node: str, job: str, chunk: int) -> Path:
    return run_root(spec) / REMOTE / "abandoned" / node / job / f"chunk-{chunk}.json"


def final_path(spec: dict, host: str = REMOTE_HOST) -> Path:
    return run_root(spec) / REMOTE / host / "final.json"


def claim_hosts(spec: dict) -> list[str]:
    """The hosts the run's claims name: TASL-7, and any audit host an addendum admitted (R1-HOST-FREE (3))."""
    return sorted({json.loads(p.read_text()).get("host", REMOTE_HOST) for p in claim_files(spec)})


def claim_state(spec: dict, claim: dict) -> str:
    """``abandoned`` (an abandonment record exists: the chunk went back to TASL-2), ``closed`` (an attempt in the
    claimed chunk, every one of them registered from TASL-7, is complete or ended in an author STOP), or ``open``."""
    if abandon_path(spec, claim["node"], claim["job"], claim["chunk"]).is_file():
        return "abandoned"
    d = run_root(spec) / claim["node"] / claim["job"] / f"chunk-{claim['chunk']}"
    for _, p in G.attempts(d):
        rec = p / "job_record.json"
        if rec.is_file() and json.loads(rec.read_text()).get("stop_class") in (None, "node", "timing"):
            return "closed"
    return "open"


def open_claims(spec: dict, node: str | None = None) -> list[dict]:
    out = []
    for p in claim_files(spec):
        c = json.loads(p.read_text())
        if (node is None or c["node"] == node) and claim_state(spec, c) == "open":
            out.append(c)
    return out


def _utc_of(paths) -> list[str]:
    return [json.loads(Path(p).read_text()).get("utc", "") for p in paths]


def check_remote_final(spec: dict) -> dict | None:
    """Before ``seal_run``, if any TASL-7 claim exists: no claim open, and the final registration of TASL-7's access log
    (``g5_job.finalize_remote``) exists, made after every registration and abandonment, naming the last registered
    copy of the log. None when TASL-7 ran nothing. With claims for an addendum's audit hosts (R1-HOST-FREE (3)) the
    same holds per host, over that host's own registrations, abandonments and log copies; the result is then
    ``{"hosts": {host: final}}`` (TASL-7 alone keeps the signed form)."""
    if not claim_files(spec):
        return None
    if open_claims(spec):
        raise Stop(f"STOP: TASL-7 claims are open {[(c['node'], c['job'], c['chunk']) for c in open_claims(spec)]}; "
                   f"every TASL-7 attempt must be registered (or the claim abandoned) before the run is sealed")
    hosts = claim_hosts(spec)
    if hosts == [REMOTE_HOST]:
        return _host_final(spec, REMOTE_HOST, only=True)
    return {"hosts": {h: _host_final(spec, h, only=False) for h in hosts}}


def _host_final(spec: dict, host: str, *, only: bool) -> dict:
    fp = final_path(spec, host)
    if not fp.is_file():
        raise Stop(f"STOP: {host} ran audit chunks but its access log has no final registration (g5_tasl.py "
                   f"finalize-remote) after its last job")
    final = json.loads(fp.read_text())
    remote = run_root(spec) / REMOTE
    recs = list((remote / "registrations").rglob("*.json")) + list((remote / "abandoned").rglob("*.json"))
    if not only:                                 # several hosts: each host's own records (abandonments name theirs)
        recs = [p for p in recs if json.loads(p.read_text()).get("host", REMOTE_HOST) == host]
    later = [u for u in _utc_of(recs) if u > final.get("utc", "")]
    logs = sorted((remote / host).glob("access_log-*.jsonl"), key=lambda q: int(q.stem.split("-")[1]))
    if later or not logs or final.get("access_log_sha256") != L._sha_file(logs[-1]):
        raise Stop(f"STOP: the final {host} access-log registration is not the last {host} record (a registration or "
                   f"an abandonment came after it, or it names another log copy)")
    return final


def _no_symlink(target: Path) -> None:
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists() or p.is_symlink()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")


def partial_of(target: Path) -> Path:
    return Path(target).with_name(Path(target).name + ".partial")


def _stage(target: Path) -> Path:
    """A seal is written into ``<target>.partial`` and renamed to ``<target>`` only after its receipt (review m2). An
    existing ``.partial`` is an interrupted seal: STOP. The operator reports it and does not touch it; after the
    author's (or the coordinator's) inspection it is moved aside (for example to ``_to_delete/``), never into place,
    and the seal step is run again."""
    target = Path(target)
    part = partial_of(target)
    if part.exists() or part.is_symlink():
        raise Stop(f"STOP: {part} exists: an interrupted seal; report it, leave it as it is, and after inspection move "
                   f"it aside (never into place) before sealing again")
    _no_symlink(target)
    part.mkdir(parents=True, mode=0o700)
    return part


def _commit(part: Path, target: Path) -> None:
    if target.exists():
        raise Stop(f"STOP: {target} appeared during the seal; {part} is left for inspection")
    part.rename(target)


def _files(d: Path) -> dict[str, str]:
    """{relative name: sha256} of every regular file under ``d`` except the receipt; a symlink or other entry STOPs."""
    out = {}
    for p in sorted(Path(d).rglob("*")):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise Stop(f"STOP: {p} in a sealed directory is not a regular file")
        if p.is_file() and p.name != RECEIPT:
            out[p.relative_to(d).as_posix()] = L._sha_file(p)
    return out


def _write_receipt(part: Path, target: Path, receipt: dict) -> dict:
    """The receipt of the staged directory ``part`` (its files), naming the final ``target``; then ``part`` becomes
    ``target``."""
    receipt = {"schema": RECEIPT_SCHEMA, "label": S.EVIDENCE, "seal_mode": "procedural", **receipt,
               "sealed_path": str(target), "files": _files(part), "who": WHO, "host": socket.gethostname(),
               "sealed_utc": utc()}
    with (part / RECEIPT).open("x") as fh:
        fh.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    _commit(part, target)
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
    if receipt.get("sealed_path") is not None and Path(receipt["sealed_path"]).resolve() != d.resolve():
        raise Stop(f"STOP: {rp} names another sealed path")
    got = _files(d)
    if got != receipt.get("files"):
        diff = sorted(set(got.items()) ^ set((receipt.get("files") or {}).items()))
        raise Stop(f"STOP: {d} differs from its seal receipt (sealed content changed): {diff[:4]}")
    return receipt


def _tar_dir(src_parent: Path, name: str, tar_path: Path) -> int:
    """``tar -cf tar_path -C src_parent name``, then verify the tar holds exactly the files under it, each with the
    source file's sha256 (review m3), before any source is removed; returns the count."""
    files = {p.relative_to(src_parent).as_posix(): L._sha_file(p) for p in (src_parent / name).rglob("*")
             if p.is_file()}
    if subprocess.run(["tar", "-cf", str(tar_path), "-C", str(src_parent), name], capture_output=True).returncode:
        raise Stop(f"STOP: cannot tar {src_parent / name}")
    listed = {}
    with tarfile.open(tar_path) as tar:
        for m in tar:
            if m.isfile():
                h = hashlib.sha256()
                fh = tar.extractfile(m)
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
                listed[m.name] = h.hexdigest()
    if listed != files:
        raise Stop(f"STOP: {tar_path} does not hold exactly the files of {src_parent / name} with their sha256")
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
    part = _stage(target)
    copied = []
    for name in ATTEMPT_FILES:
        if (src / name).is_file():
            shutil.copy2(src / name, part / name)
            copied.append(name)
    log = record.get("node_log")
    logs_dir = (run_root(spec) / "_logs").resolve()
    node_log = None
    if log and Path(log).is_file() and Path(log).resolve().parent == logs_dir:
        shutil.copy2(log, part / "node.log")
        node_log = str(log)
    out_clear = None
    if (src / "out").is_dir():                   # a tar failure, a deadline or a crash left out/ in clear
        out_clear = _tar_dir(src, "out", part / "out_clear.tar")
    receipt = _write_receipt(part, target, {"kind": "attempt", "run_id": spec["run_id"], "node": parts["node"],
                                      "job": parts["job"], "chunk": parts["chunk"], "attempt": parts["attempt"],
                                      "source": str(src), "copied": copied, "node_log": node_log,
                                      "out_clear_files": out_clear, "stop": record.get("stop"),
                                      "stop_class": record.get("stop_class"),
                                      "job_record_sha256": L._sha_file(part / "job_record.json")})
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
    if open_claims(spec, node):                  # R1-G5-AUDIT-TWO-CARDS: a TASL-7 chunk of the node is outstanding
        return None
    sw = root / S.SWITCH_STOP                    # the switch's node STOP (XC3-FAIL B; review round 2, N1)
    if sw.is_file() and json.loads(sw.read_text()).get("stop_class") in ("node", "timing"):
        return f"STOP on record: {S.SWITCH_STOP}"
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
    if open_claims(spec, node):
        raise Stop(f"STOP: {node} has an open TASL-7 claim: every TASL-7 attempt must be registered (or the claim "
                   f"abandoned) before the node is sealed")
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
    part = _stage(target)
    names = []
    for wave in (1, 2):
        d = run_root(spec) / node / f"audits-wave{wave}"
        for name in ("plan.tar", "plan_index.json"):
            if (d / name).is_file():
                shutil.copy2(d / name, part / f"wave{wave}_{name}")
                names.append(f"wave{wave}_{name}")
        wc = run_root(spec) / node / f"wave_checks_wave{wave}.json"
        if wc.is_file():
            shutil.copy2(wc, part / wc.name)
            names.append(wc.name)
    sw = run_root(spec) / node / S.SWITCH_STOP
    if sw.is_file():
        shutil.copy2(sw, part / S.SWITCH_STOP)
        names.append(S.SWITCH_STOP)
    for wave in (1, 2):                          # a plan is sealed with its index, and the index binds the tar
        idx = part / f"wave{wave}_plan_index.json"
        if idx.is_file() and json.loads(idx.read_text())["plan_tar_sha256"] != L._sha_file(part / f"wave{wave}_plan.tar"):
            raise Stop(f"STOP: {node} wave {wave}: plan.tar differs from its index ({part} is left for inspection)")
    return _write_receipt(part, target, {"kind": "node", "run_id": spec["run_id"], "node": node, "copied": names,
                                   "ended": ended, "attempts": [str(a) for a in attempts]})


def seal_run(spec: dict, *, not_run: tuple = ()) -> dict:
    """Seal the run-level files once the table has ended: every node sealed, or declared ``not_run`` (refused at the
    switch, e.g. STOP 5, so it has no node directory); then the job-code access log, the K lock, the refusals and
    the node wrapper logs (as tars) and the registered server spans."""
    check_seal_mode(spec)
    remote_final = check_remote_final(spec)      # R1-G5-AUDIT-TWO-CARDS: no open claim, the final TASL-7 log (M2)
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
    part = _stage(target)
    names = []
    for name in ("_access_log.jsonl", "_k_lock.json"):
        if (root / name).is_file():
            shutil.copy2(root / name, part / name)
            names.append(name)
    for name in ("_refusals", "_logs", "_server_spans", "_remote"):    # _remote: TASL-7 claims, registrations, logs
        if (root / name).is_dir():
            _tar_dir(root, name, part / f"{name.lstrip('_')}.tar")
            names.append(f"{name.lstrip('_')}.tar")
    return _write_receipt(part, target, {"kind": "run", "run_id": spec["run_id"], "copied": names,
                                   "not_run": sorted(not_run), "remote_final": remote_final})


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


# What each opening may take (review M1): the members of each kind, and the tar they come from. The ledger pattern and
# the chunk members equal g5_job's (a test checks it); g5_job is not imported here (it imports this module).
LEDGER_MEMBER = re.compile(r"^out/campaign/(instance_\d+_(?:history|none))/campaign_ledger\.jsonl$")
CHUNK_MEMBERS = ("out/chunk.json", "out/audit/rows.jsonl")
PLAN_TAR = re.compile(r"^wave[12]_plan\.tar$")
WHAT = ("ledgers", "plan", "chunk", "server_log")


def _member_ok(what: str, name: str) -> bool:
    if what == "ledgers":
        return bool(LEDGER_MEMBER.fullmatch(name))
    if what == "plan":
        return name == "plan.json"
    if what == "chunk":
        return name in CHUNK_MEMBERS
    return bool(re.fullmatch(r"server-[1-9][0-9]*/llama-server\.log", name))


def reduce_rows(spec: dict, lines: list[str], chunk: dict, stage: str) -> dict:
    """The audit rows of one chunk, reduced inside the reader (review M1): {(unit, seed): (kind, value)} for the label
    seeds, and at the test stage for the evaluation seeds too. At the train/dev stage an evaluation-seed row gives
    nothing back, neither its kind nor its value: it is only checked (every planned run has a row, as the job checks;
    an ok row carries a finite numeric ``outcome.value``, review m7) and then dropped."""
    import g5_job as J                          # noqa: PLC0415 - loaded already; a cycle at import time otherwise
    if stage not in ("traindev", "test"):
        raise Stop(f"STOP: unknown stage {stage!r}")
    J.read_rows(lines, chunk)                   # schema, plan, seeds, isolation, code states, one row per planned run
    seeds = S.audit_seeds(spec, chunk["K"])
    label, evaluation = set(seeds["label"]), set(seeds["evaluation"])
    out, dropped = {}, 0
    for line in lines:
        if not line.strip():
            continue
        r = json.loads(line)
        kind = r["outcome"]["kind"]
        if kind == "infrastructure_failure":
            raise Stop("STOP: a complete chunk holds an infrastructure row (contract)")
        value = r["outcome"].get("value") if kind == "ok" else None
        if kind == "ok" and (not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value)):
            raise Stop("STOP: an ok audit row lacks a finite numeric outcome.value (contract: non-finite is divergent)")
        if r["seed"] in label or (stage == "test" and r["seed"] in evaluation):
            out[(r["unit"], r["seed"])] = (kind, float(value) if value is not None else None)
        elif r["seed"] in evaluation:
            dropped += 1
        else:
            raise Stop(f"STOP 10: seed {r['seed']} is not an audit seed of K = {chunk['K']}")
    return {"rows": out, "evaluation_rows_dropped": dropped}


class SealedTree:
    """The access-logged reader of the sealed G.5 tree on TASL-2. Every opening checks the purpose's lock, verifies
    the sealed directory against its receipt, and logs one line (purpose, rows, kind and member names) before anything
    is read. A purpose may take only the members of its kind (ledgers, a plan, a chunk's two members); a chunk's rows
    leave the reader only through ``chunk_rows``, reduced to the stage's seeds."""

    def __init__(self, spec: dict, *, lock=None, who: str = WHO):
        self.spec, self.lock, self.who = spec, lock, who
        self.root = sealed_run(spec)

    def log(self, path: Path, purpose: str, grant: dict, what: str, members: list[str]) -> dict:
        entry = {"schema": ACCESS_SCHEMA, "utc": utc(), "who": self.who, "pid": os.getpid(),
                 "host": socket.gethostname(), "path": str(path), "sha256": L._sha_file(path), "purpose": purpose,
                 "lock": grant, "what": what, "members": sorted(members)}
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ACCESS_LOG).open("a") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def _open(self, sealed_dir: Path, tar_name: str, what: str, purpose: str) -> dict:
        grant = require(purpose, lock=self.lock)
        sealed_dir = Path(sealed_dir)
        if self.root.resolve() not in sealed_dir.resolve().parents:
            raise Stop(f"STOP: {sealed_dir} is not in this run's sealed tree")
        if what not in ("ledgers", "plan", "chunk") or \
                (what == "plan") != bool(PLAN_TAR.fullmatch(tar_name)) or (what != "plan" and tar_name != "out.tar"):
            raise Stop(f"STOP 11: {what!r} is not read from {tar_name}")
        verify_sealed(sealed_dir)
        tar_path = sealed_dir / tar_name
        with tarfile.open(tar_path) as tar:
            names = [m.name for m in tar if m.isfile() and _member_ok(what, m.name)]
        if not names or what == "plan" and names != ["plan.json"] or \
                what == "chunk" and sorted(names) != sorted(CHUNK_MEMBERS):
            raise Stop(f"STOP: {tar_path} does not hold exactly the {what} members")
        if len(set(names)) != len(names):
            raise Stop(f"STOP: {tar_path} holds a member twice")
        self.log(tar_path, purpose, grant, what, names)
        out = {}
        with tarfile.open(tar_path) as tar:
            for name in names:
                out[name] = tar.extractfile(name).read()
        if what == "chunk":            # raw rows never leave the reader: reduced here to the purpose's stage (review n1)
            stage = next(PURPOSES[p][0] for p in PURPOSES if purpose.startswith(p))
            chunk = json.loads(out["out/chunk.json"])
            return {"chunk": chunk,
                    **reduce_rows(self.spec, out.pop("out/audit/rows.jsonl").decode().splitlines(), chunk, stage)}
        return out

    def ledgers(self, sealed_dir: Path, purpose: str) -> dict[str, list[str]]:
        """{instance_<k>_<mode>: ledger lines} of a sealed campaign attempt."""
        got = self._open(sealed_dir, "out.tar", "ledgers", purpose)
        return {LEDGER_MEMBER.fullmatch(n).group(1): raw.decode().splitlines() for n, raw in got.items()}

    def plan(self, node_dir: Path, wave: int, purpose: str) -> bytes:
        return self._open(node_dir, f"wave{wave}_plan.tar", "plan", purpose)["plan.json"]

    def chunk_rows(self, sealed_dir: Path, purpose: str) -> dict:
        """A sealed chunk's file and its rows reduced to the purpose's stage (``reduce_rows``)."""
        return self._open(sealed_dir, "out.tar", "chunk", purpose)          # the purpose is checked there first


def check_access_log(spec: dict, *, root: Path | None = None) -> list[dict]:
    """STOP 11 over a sealed tree's access log (TASL-2's, or TASL-7's with ``root``): every line by this step's code,
    for a declared purpose, with the rows its lock names, and only members of its kind."""
    log = Path(root or sealed_run(spec)) / ACCESS_LOG
    out = [json.loads(x) for x in log.read_text().splitlines() if x.strip()] if log.is_file() else []
    bad = []
    for e in out:
        hit = [p for p in PURPOSES if str(e.get("purpose", "")).startswith(p)]
        rows = [r.get("row_id") for r in (e.get("lock") or {}).get("rows") or []]
        need = [UNSEAL_ROW] + ([TEST_ROW] if hit and PURPOSES[hit[0]][0] == "test" else [])
        what, members = e.get("what"), e.get("members")
        kind_ok = what in WHAT and isinstance(members, list) and members and \
            all(_member_ok(what, str(m)) for m in members) and \
            ((what == "server_log") == (bool(hit) and hit[0] == "server log:"))
        if e.get("schema") != ACCESS_SCHEMA or e.get("who") != WHO or len(hit) != 1 or rows != need or not kind_ok:
            bad.append(e)
    if bad:
        raise Stop(f"STOP 11: sealed G.5 content opened outside a declared, locked purpose: {bad[:3]}")
    return out


# =============================================================================================== TASL-7: the server
def proposer_sealed_run(spec: dict) -> Path:
    return Path(spec["proposer"]["sealed_root"]) / spec["run_id"]


def _server_dir(spec: dict, server_dir: Path) -> Path:
    src = Path(server_dir)
    expected = Path(spec["proposer"]["run_dir"]) / spec["run_id"]
    if src.is_symlink() or src.resolve().parent != expected.resolve() or not SERVER.fullmatch(src.name):
        raise Stop(f"STOP: {src} is not a server-N directory of {expected}")
    return src


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def close_server(spec: dict, server_dir: Path, reason: str, *, alive=None, scan=G.processes_mentioning,
                 now=time.time) -> dict:
    """On TASL-7: close a server that ended without ``server_end.json`` (the serve wrapper killed, an OOM kill, a
    reboot; review M3), guarded as ``close-attempt``: the same host, no process names the directory, the server's pid
    gone, and the GPU lease free. It writes ``server_end.json`` with the log's sha256 and the conservative end, the
    closing time (the log's latest modification time recorded beside it), so that ``seal_server`` can seal it."""
    check_seal_mode(spec)
    src = _server_dir(spec, server_dir)
    prop = spec["proposer"]
    if socket.gethostname() != prop["hostname"]:
        raise Stop(f"STOP: this is not {prop['hostname']}; close the server there")
    for name in ("server_record.json", "llama-server.log"):
        if not (src / name).is_file() or (src / name).is_symlink():
            raise Stop(f"STOP: {src} has no {name}")
    if (src / "server_end.json").exists():
        raise Stop(f"STOP: {src} has server_end.json already (seal it with seal-server)")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise Stop("STOP: close-server needs a reason (at least 10 characters)")
    running = scan(src)
    if running:
        raise Stop(f"STOP: processes {running} still name {src}")
    rec = json.loads((src / "server_record.json").read_text())
    if rec.get("run_id") != spec["run_id"] or Path(str(rec.get("server_dir"))).resolve() != src.resolve():
        raise Stop("STOP: the server record names another run or directory")
    if rec.get("pid") is not None and (alive or _pid_alive)(int(rec["pid"])):
        raise Stop(f"STOP: the server process {rec['pid']} is still alive")
    with G.gpu_lease(prop["lease"]):
        closed = now()
        end = {"stopped_utc": utc(closed), "closed": True, "end_basis": "closed_at", "reason": reason.strip(),
               "latest_log_mtime_utc": utc((src / "llama-server.log").stat().st_mtime), "server_rc": None,
               "stop_signal": None, "server_record_sha256": L._sha_file(src / "server_record.json"),
               "server_log_sha256": L._sha_file(src / "llama-server.log"), "closed_by": WHO,
               "host": socket.gethostname()}
        with (src / "server_end.json").open("x") as fh:
            fh.write(json.dumps(end, indent=1) + "\n")
    return end


def seal_server(spec: dict, server_dir: Path, *, alive=None) -> dict:
    """On TASL-7: seal a stopped (or closed) server's ``server-N/`` as ``server.tar`` under ``proposer.sealed_root``
    with a receipt that carries its span, then remove the clear ``llama-server.log`` (it holds the prompts). The server
    must have ended (``server_end.json`` binding its record and log) and its process must be gone."""
    check_seal_mode(spec)
    check_access_log(spec, root=proposer_sealed_run(spec))          # STOP 11 over TASL-7's sealed tree (m6)
    src = _server_dir(spec, server_dir)
    for name in ("server_record.json", "server_end.json", "llama-server.log"):
        if not (src / name).is_file() or (src / name).is_symlink():
            raise Stop(f"STOP: {src} has no {name} (a running server is sealed after it stops; a crashed one after "
                       f"close-server)")
    rec = json.loads((src / "server_record.json").read_text())
    end = json.loads((src / "server_end.json").read_text())
    if rec.get("run_id") != spec["run_id"] or Path(str(rec.get("server_dir"))).resolve() != src.resolve():
        raise Stop("STOP: the server record names another run or directory")
    if end.get("server_record_sha256") != L._sha_file(src / "server_record.json") or \
            end.get("server_log_sha256") != L._sha_file(src / "llama-server.log"):
        raise Stop("STOP: server_end.json does not bind this record and log (changed after the server stopped)")
    if rec.get("pid") is not None and (alive or _pid_alive)(int(rec["pid"])):
        raise Stop(f"STOP: the server process {rec['pid']} is still alive")
    started, stopped = rec.get("started_utc"), end.get("stopped_utc")
    try:
        span = parse_utc(stopped) - parse_utc(started)
    except (TypeError, ValueError):
        raise Stop("STOP: the server record and end need started_utc and stopped_utc") from None
    if span < 0:
        raise Stop("STOP: the server stopped before it started")
    target = proposer_sealed_run(spec) / src.name
    part = _stage(target)
    _tar_dir(src.parent, src.name, part / "server.tar")
    receipt = {"schema": SERVER_RECEIPT_SCHEMA, "label": S.EVIDENCE, "seal_mode": "procedural", "kind": "server",
               "run_id": spec["run_id"], "server": src.name, "source": str(src), "pid": rec.get("pid"),
               "started_utc": started, "stopped_utc": stopped, "span_seconds": round(span, 1),
               "closed": bool(end.get("closed")), "latest_log_mtime_utc": end.get("latest_log_mtime_utc"),
               "server_record_sha256": end["server_record_sha256"], "server_log_sha256": end["server_log_sha256"],
               "server_end_sha256": L._sha_file(src / "server_end.json"), "sealed_path": str(target),
               "files": _files(part), "who": WHO, "host": socket.gethostname(), "sealed_utc": utc()}
    with (part / RECEIPT).open("x") as fh:
        fh.write(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    _commit(part, target)
    (src / "llama-server.log").unlink()          # sealed and verified (member sha256): the prompts leave clear
    return receipt


def open_server_log(spec: dict, server: str, purpose: str, *, lock=None) -> bytes:
    """A sealed server log, only after the T1 test release row (it holds prompts with per-step metric values), with a
    line in the TASL-7 sealed tree's access log."""
    if not purpose.startswith("server log:"):
        raise Stop("STOP 11: a server log is opened only for the 'server log:' purpose")
    grant = require(purpose, lock=lock)
    root = proposer_sealed_run(spec)
    check_access_log(spec, root=root)                               # m6
    d = root / server
    receipt = verify_sealed(d)
    member = f"{receipt['server']}/llama-server.log"
    tree = SealedTree(spec, lock=lock)
    tree.root = root
    tree.log(d / "server.tar", purpose, grant, "server_log", [member])
    with tarfile.open(d / "server.tar") as tar:
        return tar.extractfile(member).read()


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


def _server_no(name: str) -> int:
    return int(name.split("-", 1)[1])


def span_gaps(spec: dict) -> list[int]:
    """Server numbers below the highest registered one that have no registered span (``server_attempt`` numbers the
    servers server-1, server-2, … without gaps, so a gap is a server whose span is unknown; review m5)."""
    nos = {_server_no(r["server"]) for r in registered_spans(spec).values()}
    return [k for k in range(1, max(nos, default=0) + 1) if k not in nos]


def proposer_seconds(spec: dict, *, now=time.time) -> dict:
    """The proposer card's held seconds (G5-TASL-GPUH B): every registered span; for a server a campaign job record
    names without a registered span, the time from its start until now; and for a gap in the registered server
    numbers, the time from the previous registered server's stop (or the earliest known start) until now. Open spans
    and gaps are upper bounds."""
    spans = registered_spans(spec)
    used = campaign_servers(spec)
    by_no = {_server_no(r["server"]): r for r in spans.values()}
    closed = sum(float(r["span_seconds"]) for r in spans.values())
    open_ = {sha: max(0.0, now() - parse_utc(start)) for sha, start in used.items() if sha not in spans}
    starts = [parse_utc(r["started_utc"]) for r in spans.values()] + [parse_utc(s) for s in used.values()]
    gaps = {}
    for k in span_gaps(spec):
        lower = [j for j in by_no if j < k]
        since = parse_utc(by_no[max(lower)]["stopped_utc"]) if lower else min(starts)
        gaps[k] = max(0.0, now() - since)
    return {"seconds": round(closed + sum(open_.values()) + sum(gaps.values()), 1), "registered": len(spans),
            "open": len(open_), "open_servers": sorted(open_), "gaps": sorted(gaps)}


def require_server_spans(spec: dict) -> dict:
    """Under G5-TASL-GPUH B, before an audit job: every server a campaign job used has stopped and its span is
    registered, and the registered servers are server-1..N without a gap, so the meter counts closed spans only."""
    spans = registered_spans(spec)
    missing = sorted(sha for sha in campaign_servers(spec) if sha not in spans)
    gaps = span_gaps(spec)
    if missing or gaps:
        raise Stop(f"STOP: G5-TASL-GPUH B: the span of the server(s) {[m[:12] for m in missing]} "
                   f"{'and of server number(s) ' + str(gaps) + ' ' if gaps else ''}is not registered; seal each "
                   f"stopped server on TASL-7 (seal-server, after close-server if it crashed) and register its receipt "
                   f"here (server-span) before an audit job")
    return {"registered": len(spans)}
