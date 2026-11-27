"""G.5 audit hosts beyond the TASL pair: the list of audit hosts, the addendum that admits a host, the per-node
admission, the card-share check and the cross-check spec of an addendum host. AI-assisted (Claude). EVIDENCE table.

Authority: R1-HOST-FREE (3) ("the G.5 note is signed as drafted for the TASL pair ... further hosts join it through an
addendum note") and (2)(a)-(b); R1-G5-SIGNATURE (3); R1-G5-AUDIT-TWO-CARDS (the TASL-7 pattern this generalises);
R1-XC3-FAIL-READING (a non-PASS keeps a node's audits where they were); R1-CARD-SHARE (new launchers check free memory,
not an empty card; records list the card's other compute processes); R1-NO-TIMEOUT (2)-(3).

* **The list.** ``audit_hosts(spec, addendum)`` is TASL-7 (the signed spec's ``tasl7_audits`` block, read and checked
  exactly as before by ``g5_tasl``) followed by the hosts of an addendum spec. The signed G.5 spec is not changed: an
  addendum is a separate file (schema ``g5_audit_hosts_addendum/1``) bound to the signed spec by its sha256 and to the
  signed G.5 note by an addendum note ``docs/r1/authorizations/c3_t1_labels_audit_hosts_<YYYYMMDD>.md``. Without an
  addendum every code path of the TASL pair is the one the G.5 note was signed on; the note's key lines never read an
  addendum.
* **An addendum host** is one card (Ada's eight cards are eight entries on one hostname): its identity (hostname, GPU
  UUID, GPU model, driver), its own GPU lease, the free-memory floor of R1-CARD-SHARE, the G5-7 checkout path and the
  table's runs-tree layout, environments, its harness-isolation host check record, its C12 record (under ``cuda_ipc:
  c12``), its hardware class, the cross-check spec it was checked under and, per G5-7 node, the short cross-check PASS
  record against the node's sealed TASL-2 attempt (or ``PENDING short cross-check: <node>``). Autoresearch's audits
  stay on TASL-2 (ar-cond7a exists only there), as for TASL-7.
* **Hardware class (R1-HOST-FREE (2)(a)).** An audit chunk is a slice of (code state x seed) runs of a wave's plan, so a
  proposal's candidate runs and its parent's runs can fall into different chunks and therefore onto different hosts.
  (2)(a) keeps "the candidate and incumbent audits of one proposal" on one hardware class. A host of the table's GPU
  model (``same_gpu_model``) is the class TASL-2 and TASL-7 already form. A host of another GPU model (Ada's RTX 6000
  Ada) is ``cross_model_row``: refused at every admission until the author's row ``R1-G5-AUDIT-HOST-CLASS`` is on main
  naming that GPU model and reading a node's cross-host PASS as one hardware class for that node's audits. Fail closed:
  without the row, no G.5 audit chunk runs on a card of another GPU model.
* **Admission per node** (``check_admission``, at the claim, at the job start and at the registration): the G5-7 family,
  G5-TASL-GPUH A, the node's environment and CPU set on that host filled, the host check record on main at its sha256
  (PASS for that hostname at the seven nodes' G.1b pin, as TASL-7's), the C12 record under ``cuda_ipc: c12``, the
  hardware class, the cross-check spec in the checkout at its sha256, and the node's short cross-check PASS on main at
  its sha256 (this node, mode short, complete, PASS, both sides deterministic, the TASL-2 side the node's declared
  sealed attempt, the host side ``<run>-<host>``) and the one such verdict file of the node and host on main. Any
  failure refuses only that node on that host; nothing else changes (R1-XC3-FAIL-READING: the node's audits stay where
  they are).
* **Card share** (``card_share_check``): an addendum host's job starts beside other compute processes when the card has
  the free memory the entry declares; each check records the count and memory of the card's other compute processes
  (never their owners or commands). An attempt during which another compute process was seen on its card at any check
  is an infrastructure failure and is repeated (R1-NO-TIMEOUT (2): a run's budget decides the proposal only on an
  attempt that had its card to itself; the audit rows are sealed, so the whole attempt is repeated). TASL-7 keeps its
  reviewed empty-card check (R1-CARD-SHARE (5)).
* **The cross-check spec of an addendum host** (schema ``g5_audit_host_crosscheck_spec/1``, ``check_host_xc_spec``):
  the default part of each node on the host, compared with the node's sealed TASL-2 attempt, as xc3. For the four xc3
  nodes that attempt is the sealed G.1b TASL-2 attempt the xc3 spec declares; for the three TASL-7 G.1b nodes it is the
  xc2 TASL-2 attempt (bit-identical to their G.1b TASL-7 attempt by the xc2 step-2 PASS); for autoresearch the sealed
  G.1b-AR TASL-2 attempt. Each reference is checked against the file on main that records it. The spec is a draft: its
  runner (the short kind of ``g1b_crosscheck`` for a host outside the signed G.1b spec, with an RTX 6000 Ada GPU check)
  is a later unit, so nothing here launches it.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

import g5_tasl as S

G, L, PC, X = S.G, S.L, S.PC, S.X
Stop, NodeStop = S.Stop, S.NodeStop
REPO_ROOT = S.REPO_ROOT

ADDENDUM_SCHEMA = "g5_audit_hosts_addendum/1"
HOST_XC_SCHEMA = "g5_audit_host_crosscheck_spec/1"
ADDENDUM_NOTE_NAME = re.compile(r"^c3_t1_labels_audit_hosts_(\d{8})\.md$")
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z0-9]+)*$")
RESERVED = (S.WORKER_HOST, S.AUDIT_HOST)
HOST_FREE_ROW = "R1-HOST-FREE"
HOST_FREE_TERMS = ("further hosts join it through an addendum note", "cross-host PASS")
SIGNATURE_ROW = "R1-G5-SIGNATURE"
SIGNATURE_TERMS = ("join by addendum notes",)
CARD_SHARE_ROW = "R1-CARD-SHARE"
CARD_SHARE_TERMS = ("check free memory, not an empty card",)
# The author's row a host of another GPU model needs (proposed in the unit report; not on main at this unit).
CLASS_ROW = "R1-G5-AUDIT-HOST-CLASS"
CLASS_TERMS = ("one hardware class", "cross-host PASS")
HARDWARE_CLASSES = ("same_gpu_model", "cross_model_row")
SHORT_MODE = "short"
VERDICT_TOKEN = "G5_AUDIT_HOST_XC_VERDICT_"
VERDICT_NAME = re.compile(r"^docs/r1/reports/[A-Za-z0-9_.\-]+/G5_AUDIT_HOST_XC_VERDICT_(?P<host>[A-Za-z0-9-]+?)_"
                          r"(?P<node>[a-z][a-z0-9_]*)_\d{8}\.json$")
SIDE_FIELDS = ("run_id", "spec_sha256", "job_record_sha256", "attempt")
EIGHT = S.T1_NODES
HOST_KEYS = {"host", "hostname", "gpu_model", "gpu_uuid", "driver", "hardware_class", "lease", "card_share",
             "families", "harness_dir", "base", "runs_root", "uv", "cpus", "node_cpus", "env_python", "extra_env",
             "node_extra_env", "isolation_host_check", "c12", "crosscheck", "admission"}
ADDENDUM_KEYS = {"schema", "label", "comment", "authority", "run_id", "g5_spec", "hosts"}
CUDA_IPC_ADDENDUM_ACCEPTANCE = (
    "The author accepts, for the G.5 audit chunks on {hosts} admitted by this addendum, the residual risk that "
    "harness-isolation host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md "
    "§3) is untested on these hosts, as for TASL-2 and TASL-7 in the signed note's cuda_ipc_acceptance line. "
    "Disclosed in the T1 report.")
# The xc2 step-1 verdicts give the TASL-2 attempt of the three TASL-7 G.1b nodes (their TASL-2 sealed attempt).
XC2_STEP1 = S.XC2_VERDICTS["xc"]
AR_REFERENCE_RECORD = "docs/r1/reports/tasl_chain_20261122/AR_G1B_TASL2_RESULT_20261122.md"


def _sha_file(rel: str) -> str | None:
    p = REPO_ROOT / rel
    return L._sha_file(p) if p.is_file() else None


def _abs_or_ph(value) -> bool:
    return isinstance(value, str) and (S._ph(value) or (value.startswith("/") and ".." not in Path(value).parts))


def xc_pending(node: str) -> str:
    return S.xc_pending(node)


# =============================================================================================== the list
def signed_host(spec: dict) -> dict:
    """TASL-7 as the first audit host: the signed spec's ``tasl7_audits`` block (validated by ``g5_tasl``)."""
    t = spec["tasl7_audits"]
    return {"host": S.AUDIT_HOST, "source": "the signed G.5 note (tasl7_audits)", "hostname": t["hostname"],
            "gpu_uuid": t["gpu_uuid"], "gpu_model": spec["gpu_model"], "hardware_class": "same_gpu_model",
            "lease": t["lease"], "lease_kind": "the proposer server's", "families": list(t["families"]),
            "card_check": "no other compute process (reviewed launch code; R1-CARD-SHARE (5))"}


def audit_hosts(spec: dict, addendum: dict | None = None) -> list[dict]:
    """TASL-7, then each host of the addendum (in its order). Without an addendum: TASL-7 alone."""
    out = [signed_host(spec)]
    for h in (addendum or {}).get("hosts") or []:
        out.append(dict(h, source="addendum", lease_kind="its own",
                        card_check=f"free memory at least {h['card_share']['min_free_mib']} MiB (R1-CARD-SHARE)"))
    return out


def host_entry(addendum: dict | None, host: str) -> dict:
    for h in (addendum or {}).get("hosts") or []:
        if h.get("host") == host:
            return h
    raise Stop(f"STOP: {host} is not an audit host of the addendum (the TASL pair's hosts are {list(RESERVED)})")


# =============================================================================================== the addendum spec
def load_addendum(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise Stop(f"STOP: the addendum spec {path} cannot be read as JSON: {exc}") from None


def validate_addendum(spec: dict, spec_path: Path, add: dict, *, launch: bool = False) -> dict:
    """The addendum spec against the signed G.5 spec (module docstring). ``launch``: no placeholder anywhere a job
    reads (identity, lease, paths, environments, records). Returns ``{"hosts": [names], "sha256s": {...}}``."""
    if not isinstance(add, dict) or set(add) != ADDENDUM_KEYS:
        raise Stop(f"STOP: the addendum spec must carry exactly {sorted(ADDENDUM_KEYS)}")
    if add["schema"] != ADDENDUM_SCHEMA or add["label"] != S.EVIDENCE:
        raise Stop(f"STOP: the addendum spec must be {ADDENDUM_SCHEMA}, label {S.EVIDENCE}")
    if not str(add["authority"]).startswith(f"{HOST_FREE_ROW} (3)"):
        raise Stop(f"STOP: the addendum's authority must cite {HOST_FREE_ROW} (3) first")
    if add["run_id"] != spec["run_id"]:
        raise Stop(f"STOP: the addendum's run_id must be the G.5 run's ({spec['run_id']})")
    g = add["g5_spec"]
    if not isinstance(g, dict) or set(g) != {"path", "sha256"} or g["sha256"] != L._sha_file(Path(spec_path)):
        raise Stop("STOP: the addendum's g5_spec must name the signed G.5 spec and its sha256 (the spec is unchanged)")
    hosts = add["hosts"]
    if not isinstance(hosts, list) or not hosts:
        raise Stop("STOP: the addendum must list at least one host")
    names, uuids, leases = set(), set(), set()
    pair = {spec["worker"]["hostname"], spec["tasl7_audits"]["hostname"]}
    for h in hosts:
        if isinstance(h, dict) and h.get("hostname") in pair:
            raise Stop(f"STOP: {h.get('host')} is on a host of the TASL pair ({h['hostname']}); its cards are the "
                       f"signed note's")
        _check_host(spec, h, launch=launch)
        if h["host"] in names:
            raise Stop(f"STOP: audit host {h['host']} is named twice")
        names.add(h["host"])
        if not S._ph(h["gpu_uuid"]):
            if h["gpu_uuid"] in uuids:
                raise Stop(f"STOP: the GPU {h['gpu_uuid']} is named by two audit hosts")
            uuids.add(h["gpu_uuid"])
        key = (h["hostname"], os.path.normpath(str(h["lease"])))
        if key in leases:
            raise Stop(f"STOP: two audit hosts on {h['hostname']} share the lease {h['lease']} (one lease per card)")
        leases.add(key)
    return {"hosts": [h["host"] for h in hosts]}


def _check_host(spec: dict, h: dict, *, launch: bool) -> None:
    if not isinstance(h, dict) or set(h) != HOST_KEYS:
        raise Stop(f"STOP: an addendum host carries exactly {sorted(HOST_KEYS)}")
    name = h["host"]
    if not isinstance(name, str) or not NAME.fullmatch(name) or name in RESERVED:
        raise Stop(f"STOP: audit host name {name!r} must be a simple name other than {list(RESERVED)}")
    where = f"audit host {name}"
    for key in ("hostname", "gpu_uuid", "driver"):
        v = h[key]
        if not isinstance(v, str) or not v or (launch and S._ph(v)):
            raise Stop(f"STOP: {where}: {key} must be filled")
    if not S._ph(h["gpu_uuid"]) and not re.fullmatch(r"GPU-[0-9a-f-]{36}", h["gpu_uuid"]):
        raise Stop(f"STOP: {where}: gpu_uuid must be an nvidia-smi GPU UUID")
    if not isinstance(h["gpu_model"], str) or not h["gpu_model"] or S._ph(h["gpu_model"]):
        raise Stop(f"STOP: {where}: gpu_model must be the card's nvidia-smi name (the hardware class rests on it)")
    want_class = "same_gpu_model" if h["gpu_model"] == spec["gpu_model"] else "cross_model_row"
    if h["hardware_class"] != want_class:
        raise Stop(f"STOP: {where}: hardware_class must be {want_class!r} for {h['gpu_model']} (the table's GPU model is "
                   f"{spec['gpu_model']}; R1-HOST-FREE (2)(a))")
    lease = h["lease"]
    if not isinstance(lease, str) or not (lease.startswith("~/") or lease.startswith("/")) or \
            ".." in Path(lease).parts or (launch and S._ph(lease)):
        raise Stop(f"STOP: {where}: lease must be the card's own lease file (~/… or an absolute path)")
    cs = h["card_share"]
    if not isinstance(cs, dict) or set(cs) != {"rule", "min_free_mib"} or cs["rule"] != CARD_SHARE_ROW or \
            isinstance(cs["min_free_mib"], bool) or not isinstance(cs["min_free_mib"], int) or cs["min_free_mib"] <= 0:
        raise Stop(f"STOP: {where}: card_share must be {{rule: {CARD_SHARE_ROW}, min_free_mib: a positive integer}}")
    if h["families"] != ["G5-7"]:
        raise Stop(f"STOP: {where}: families must be ['G5-7'] (autoresearch's audits stay on {S.WORKER_HOST})")
    if h["harness_dir"] != spec["harness_families"]["G5-7"]["harness_dir"]:
        raise Stop(f"STOP: {where}: harness_dir must be the G5-7 checkout path "
                   f"({spec['harness_families']['G5-7']['harness_dir']}; a checkout of the G5-7 commit on that host)")
    if h["runs_root"] != spec["worker"]["runs_root"]:
        raise Stop(f"STOP: {where}: runs_root must be the table's runs-tree layout ({spec['worker']['runs_root']}): "
                   f"claims, plans and attempts copy by relative path")
    for key in ("base", "uv"):
        if not _abs_or_ph(h[key]) or (launch and S._ph(h[key])):
            raise Stop(f"STOP: {where}: {key} must be an absolute path")
    _cpus(h["cpus"], f"{where}: cpus", launch)
    own = {n["node"]: n["cpus"] for n in spec["nodes"] if n.get("cpus") and n["family"] == "G5-7"}
    nc = h["node_cpus"]
    if not isinstance(nc, dict) or sorted(nc) != sorted(own):
        raise Stop(f"STOP: {where}: node_cpus must give exactly the nodes with their own CPU set {sorted(own)} a set "
                   f"on this host")
    for n, v in nc.items():
        got = _cpus(v, f"{where}: node_cpus.{n}", launch)
        if got is not None and len(got) != len(G.cpu_list(own[n])):
            raise Stop(f"STOP: {where}: node_cpus.{n} must have the size of its G.1b set ({own[n]})")
    envs = {n["env"] for n in spec["nodes"] if n["family"] == "G5-7"}
    ep = h["env_python"]
    if not isinstance(ep, dict) or sorted(ep) != sorted(envs) or \
            not all(_abs_or_ph(v) and not (launch and S._ph(v)) for v in ep.values()):
        raise Stop(f"STOP: {where}: env_python must map exactly the G5-7 environments {sorted(envs)} to interpreters")
    for key in ("extra_env",):
        if not isinstance(h[key], dict) or not all(isinstance(v, str) for v in h[key].values()):
            raise Stop(f"STOP: {where}: {key} maps names to strings")
    nx = h["node_extra_env"]
    if not isinstance(nx, dict) or not set(nx) <= set(S.SEVEN) or \
            not all(isinstance(v, dict) and all(isinstance(x, str) for x in v.values()) for v in nx.values()):
        raise Stop(f"STOP: {where}: node_extra_env maps seven-node names to {{name: value}}")
    hc = h["isolation_host_check"]
    if not isinstance(hc, dict) or set(hc) != {"record", "sha256"} or \
            not (S._ph(hc["record"]) or (S._rel_ok(hc["record"]) and hc["record"].startswith("docs/r1/reports/"))):
        raise Stop(f"STOP: {where}: isolation_host_check must name a report under docs/r1/reports/ and its sha256")
    if launch and S._ph(hc["record"]):
        raise Stop(f"STOP: {where}: isolation_host_check.record must be filled")
    L._sha(hc["sha256"], f"{where}.isolation_host_check.sha256", allow_placeholder=not launch)
    c12 = h["c12"]
    if c12 is not None:
        if not isinstance(c12, dict) or set(c12) != {"record", "sha256", "review"} or not S._rel_ok(c12["record"]):
            raise Stop(f"STOP: {where}: c12 is null or {{record, sha256, review}}")
        L._sha(c12["sha256"], f"{where}.c12.sha256", allow_placeholder=False)
    xc = h["crosscheck"]
    if not isinstance(xc, dict) or set(xc) != {"spec", "sha256", "host"} or not S._rel_ok(xc["spec"]):
        raise Stop(f"STOP: {where}: crosscheck must be {{spec, sha256, host}} (the cross-check spec it was checked under)")
    if _sha_file(xc["spec"]) != xc["sha256"]:
        raise Stop(f"STOP: {where}: the cross-check spec {xc['spec']} in the checkout differs from its sha256")
    xspec = json.loads((REPO_ROOT / xc["spec"]).read_text())
    check_host_xc_spec(xspec)
    xh = xspec["host"]
    if xc["host"] != xh["name"] or xh["gpu_model"] != h["gpu_model"] or \
            (not S._ph(xh["hostname"]) and xh["hostname"] != h["hostname"]):
        raise Stop(f"STOP: {where}: the cross-check spec's host ({xh['name']}, {xh['hostname']}, {xh['gpu_model']}) is "
                   f"not this host's")
    adm = h["admission"]
    if not isinstance(adm, dict) or sorted(adm) != sorted(S.SEVEN):
        raise Stop(f"STOP: {where}: admission must name exactly the seven G5-7 nodes ({S.AR}'s audits stay on "
                   f"{S.WORKER_HOST})")
    for node, entries in adm.items():
        _check_admission_entry(where, xc["host"], xspec, node, entries)


def _cpus(text, what: str, launch: bool):
    if S._ph(text) and not launch:
        return None
    try:
        return G.cpu_list(text)
    except (ValueError, TypeError):
        raise Stop(f"STOP: {what} is not a CPU list") from None


def _check_admission_entry(where: str, xc_host: str, xspec: dict, node: str, entries) -> None:
    if entries == xc_pending(node):
        return
    ok = isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict) and \
        set(entries[0]) == {"record", "sha256", "mode", "crosscheck_run_id"}
    if ok:
        e = entries[0]
        m = VERDICT_NAME.fullmatch(str(e["record"]))
        ok = bool(m) and m.group("host") == xc_host and m.group("node") == node and e["mode"] == SHORT_MODE and \
            e["crosscheck_run_id"] == xspec["run_id"] and e["record"] == xspec["verdicts"].get(node)
    if not ok:
        raise Stop(f"STOP: {where}: admission.{node} must be exactly one short PASS record "
                   f"docs/r1/reports/<dir>/{VERDICT_TOKEN}{xc_host}_{node}_<YYYYMMDD>.json (the cross-check spec's "
                   f"verdict path, mode short, run {xspec['run_id']}) or {xc_pending(node)!r}")
    L._sha(entries[0]["sha256"], f"{where}.admission.{node}.sha256", allow_placeholder=False)


# =============================================================================================== the addendum note
def note_lines(spec: dict, spec_path: Path, add: dict, add_path: Path) -> dict:
    """The addendum note's key lines, rendered from the addendum (and the signed spec's run and sha256)."""
    rel = _repo_rel(add_path)
    lines = {"g5_run_id": spec["run_id"], "g5_spec_sha256": L._sha_file(Path(spec_path)), "addendum_spec": rel,
             "audit_hosts": f"{S.AUDIT_HOST} (the signed note's tasl7_audits, unchanged); "
                            + "; ".join(f"{h['host']} ({h['gpu_model']})" for h in add["hosts"])}
    cuda = spec["key_values"]["cuda_ipc"]
    for h in add["hosts"]:
        hc, xc = h["isolation_host_check"], h["crosscheck"]
        cls = ("hardware class: the table's GPU model" if h["hardware_class"] == "same_gpu_model" else
               f"hardware class: another GPU model than the table's {spec['gpu_model']}; no audit chunk runs here "
               f"unless {CLASS_ROW} is on main naming {h['gpu_model']} (R1-HOST-FREE (2)(a))")
        adm = "; ".join(f"{n}: " + (f"{e[0]['record']} sha256 {e[0]['sha256']}" if isinstance(e, list) else
                                    "PENDING (runs on the TASL pair only)")
                        for n, e in sorted(h["admission"].items()))
        lines[f"audit_host_{h['host'].replace('-', '_')}"] = (
            f"{h['hostname']} {h['gpu_uuid']} {h['gpu_model']} driver {h['driver']}; lease {h['lease']} (its own; "
            f"free memory at least {h['card_share']['min_free_mib']} MiB, the card's other compute processes recorded, "
            f"{CARD_SHARE_ROW}); host check {hc['record']} sha256 {hc['sha256']}; G5-7 checkout {h['harness_dir']}; "
            f"{cls}; per node the short cross-check PASS against its sealed TASL-2 attempt under {xc['spec']} sha256 "
            f"{xc['sha256']}: {adm}")
    if cuda.get("mode") == "c12":
        lines["addendum_cuda_ipc"] = "; ".join(
            (f"C12 PASS: {h['c12']['record']} sha256 {h['c12']['sha256']} ({h['host']})" if h["c12"] else
             f"no C12 record for {h['host']}: no G.5 audit chunk runs there") for h in add["hosts"])
    else:
        lines["addendum_cuda_ipc"] = CUDA_IPC_ADDENDUM_ACCEPTANCE.format(hosts=", ".join(h["host"] for h in add["hosts"]))
    lines["addendum_scope"] = (
        f"G.5 audit chunks of the G5-7 family only ({S.AR}'s audits stay on {S.WORKER_HOST}); campaign waves, a wave's "
        f"plan and its last chunk (E5) stay on {S.WORKER_HOST}; a chunk is claimed on {S.WORKER_HOST} for one host, one "
        f"open claim per host, and every attempt is registered on {S.WORKER_HOST} before it counts; its hours count "
        f"inside cap_gpu_hours (R1-NO-TIMEOUT (3)); an attempt during which another compute process was seen on its "
        f"card is an infrastructure failure and is repeated (R1-NO-TIMEOUT (2), {CARD_SHARE_ROW} (3)); a node without "
        f"its PASS on main runs on the TASL pair only (R1-XC3-FAIL-READING)")
    return lines


def _repo_rel(path: Path) -> str:
    p = Path(path).resolve()
    try:
        return p.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        raise Stop(f"STOP: the addendum spec {path} is not inside the repository checkout") from None


def check_note(note_path: Path, add_path: Path, spec_path: Path, g5_note_path: Path, *, spec: dict, add: dict,
               on_main=G._note_on_main, read_main=G._read_main, draft: bool = False) -> dict:
    """The addendum note ``docs/r1/authorizations/c3_t1_labels_audit_hosts_<YYYYMMDD>.md``: on main byte-identically
    with ``approved: true`` (``draft``: exactly one ``approved: false`` line), ``g5_note`` the signed G.5 note the
    launch uses, ``addendum_spec_sha256`` the addendum's sha256, no ``<…>`` placeholder, every key line of
    ``note_lines`` verbatim, and the rows R1-HOST-FREE, R1-G5-SIGNATURE and R1-CARD-SHARE on main."""
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != S.NOTE_DIR.split("/") or \
            not ADDENDUM_NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the addendum note must be {S.NOTE_DIR}/c3_t1_labels_audit_hosts_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    approved = [ln for ln in raw.decode().splitlines() if re.match(r"^approved\s*:", ln)]
    if draft:
        if approved != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned addendum note (exactly one line 'approved: false')")
    elif approved != ["approved: true"] or not on_main(f"{S.NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the addendum note must read approved: true and be committed byte-identically on origin/main")
    fields = G._note_fields(raw)
    want = note_lines(spec, spec_path, add, add_path)
    binding = {"g5_note": f"{S.NOTE_DIR}/{Path(g5_note_path).name}", "addendum_spec_sha256": L._sha_file(add_path)}
    for key, value in binding.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: addendum note field {key} must be {value!r}")
    if not draft:
        unfilled = sorted(k for k, v in fields.items() if S.PLACEHOLDER.search(v) or L._placeholder(v))
        if unfilled:
            raise Stop(f"STOP: addendum note fields not filled (placeholder): {unfilled}")
        for row, terms in ((HOST_FREE_ROW, HOST_FREE_TERMS), (SIGNATURE_ROW, SIGNATURE_TERMS),
                           (CARD_SHARE_ROW, CARD_SHARE_TERMS)):
            S.plan_row(row, read_main, terms=terms)
    bad = sorted(k for k, v in want.items() if fields.get(k) != v)
    if bad:
        raise Stop(f"STOP: addendum note key lines differ from the addendum spec: {bad}")
    return fields


# =============================================================================================== admission per node
def host_check(entry: dict, read_main) -> dict:
    """The host's harness-isolation host check record on main at its sha256, PASS for its hostname at the seven nodes'
    G.1b pin (as TASL-7's, ``g5_tasl.tasl7_host_check``)."""
    return G.check_host_record({"hostname": entry["hostname"], "isolation_host_check": entry["isolation_host_check"]},
                               PC.PIN_SEVEN, read_main)


def check_c12(spec: dict, entry: dict, read_main) -> dict:
    """Under ``cuda_ipc: c12``: the host's own C12 record on main at its sha256, reading ``c12_host: <hostname>`` and
    ``c12_verdict: PASS``, or named with its sha256 by an accepted review (as ``g5_tasl.check_c12``)."""
    c = entry["c12"]
    if c is None:
        raise Stop(f"STOP: under cuda_ipc c12 an audit chunk on {entry['host']} needs its C12 PASS record (c12 is null)")
    raw = read_main(c["record"]) if S._rel_ok(c["record"]) else None
    if raw is None or S._sha_bytes(raw) != c["sha256"]:
        raise Stop(f"STOP: the C12 record {c['record']} of {entry['host']} is not on published main at its sha256")
    fields = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        m = re.match(r"^(c12_[a-z_]+):\s*(.*?)\s*$", line)
        if m:
            if m.group(1) in fields:
                raise Stop("STOP: duplicate " + m.group(1) + " in the C12 record")
            fields[m.group(1)] = m.group(2)
    out = {"record": c["record"], "sha256": c["sha256"], "host": entry["host"]}
    if "c12_host" in fields or "c12_verdict" in fields:
        if fields.get("c12_host") != entry["hostname"] or fields.get("c12_verdict") != "PASS":
            raise Stop(f"STOP: the C12 record does not read a PASS on {entry['hostname']}")
    elif c.get("review") is None:
        raise Stop("STOP: the C12 record has no c12_host / c12_verdict lines and no review names it")
    if c.get("review") is not None:
        S._review_names(c["review"], [c["record"], c["sha256"]], read_main, f"the C12 record {c['record']}")
        out["review"] = c["review"]
    return out


def hardware_class(spec: dict, entry: dict, read_main) -> dict:
    """R1-HOST-FREE (2)(a): the table's GPU model, or another one only with the author's row on main naming it."""
    if entry["hardware_class"] == "same_gpu_model" and entry["gpu_model"] == spec["gpu_model"]:
        return {"class": "same_gpu_model", "gpu_model": entry["gpu_model"]}
    if entry["hardware_class"] != "cross_model_row":
        raise Stop(f"STOP: {entry['host']}: unknown hardware class {entry['hardware_class']!r}")
    try:
        line = S.plan_row(CLASS_ROW, read_main, terms=CLASS_TERMS + (entry["gpu_model"],))
    except Stop as exc:
        raise Stop(f"STOP: {entry['host']} is a {entry['gpu_model']}, not the table's {spec['gpu_model']}: the "
                   f"candidate and incumbent audits of one proposal stay on one hardware class (R1-HOST-FREE (2)(a)); "
                   f"no G.5 audit chunk runs there without {CLASS_ROW} on main ({exc})") from None
    return {"class": "cross_model_row", "gpu_model": entry["gpu_model"], "row": CLASS_ROW,
            "row_sha256": S._sha_bytes(line.encode())}


def _verdict_files(host: str, node: str, list_main) -> list[str]:
    """The node's verdict files for this host on main (captures ignored; near-miss names refused; two refused)."""
    token = f"{VERDICT_TOKEN}{host}_{node}_"
    cands = [p for p in list_main("docs/r1/reports/") if p.endswith(".json") and token in p.split("/")[-1]
             and not any(x.endswith("_captures") for x in p.split("/")[:-1])]
    odd = [p for p in cands if not (VERDICT_NAME.fullmatch(p) and VERDICT_NAME.fullmatch(p).group("host") == host
                                    and VERDICT_NAME.fullmatch(p).group("node") == node)]
    if odd:
        raise Stop(f"STOP: .json paths on published main name {token} but are not docs/r1/reports/<dir>/"
                   f"{token}<YYYYMMDD>.json: {sorted(odd)[:5]}")
    if len(cands) > 1:
        raise Stop(f"STOP: {len(cands)} cross-check verdicts of {node} on {host} on published main: {sorted(cands)[:5]}")
    return sorted(cands)


def check_verdict(xspec: dict, node: str, rel: str, raw: bytes) -> dict:
    """One short cross-check PASS of ``node`` on the cross-check spec's host against its sealed TASL-2 attempt: schema
    ``g1b_tasl_crosscheck_verdict/1``, ENGINEERING_ONLY, this node, mode short, PASS with no reason, complete, the
    spec's rule and run id, the node's G.1b pin and spec, sides exactly TASL-2 and the host, each with
    run_id/spec_sha256/job_record_sha256/attempt and deterministic, the TASL-2 side the declared reference, the host
    side ``<run>-<host>``."""
    try:
        v = json.loads(raw)
    except ValueError:
        v = None
    v = v if isinstance(v, dict) else {}
    host, ref = xspec["host"]["name"], xspec["references"][node]
    g1b = xspec["g1b_specs"][ref["family"]]
    sides = v.get("sides")
    sides_ok = isinstance(sides, dict) and sorted(sides) == sorted((S.WORKER_HOST, host)) and \
        all(isinstance(x, dict) and all(k in x for k in SIDE_FIELDS) and x.get("deterministic") is True
            for x in sides.values())
    if sides_ok:
        sides_ok = all(sides[S.WORKER_HOST][k] == ref[k] for k in SIDE_FIELDS) and \
            sides[host]["run_id"] == f"{xspec['run_id']}-{host}"
    problems = [k for k, ok in (
        ("schema", v.get("schema") == X.VERDICT_SCHEMA),
        ("label", v.get("label") == G.ENGINEERING_ONLY),
        ("node", v.get("node") == node),
        ("verdict", v.get("verdict") == "PASS" and v.get("reason") is None),
        ("complete", v.get("complete") is True),
        ("mode", v.get("mode") == SHORT_MODE),
        ("rule", v.get("rule") == xspec["rule_id"]),
        ("harness_commit", v.get("harness_commit") == g1b["harness_commit"]),
        ("g1b_spec_sha256", v.get("g1b_spec_sha256") == g1b["sha256"]),
        ("crosscheck_run_id", v.get("crosscheck_run_id") == xspec["run_id"]),
        ("sides", sides_ok)) if not ok]
    if problems:
        raise Stop(f"STOP: {rel} is not a short cross-check PASS of {node} on {host}: {problems}")
    return {"record": rel, "sha256": S._sha_bytes(raw), "mode": SHORT_MODE, "crosscheck_run_id": xspec["run_id"]}


def check_admission(spec: dict, entry: dict, node: str, read_main, list_main) -> dict:
    """Whether ``node``'s audit chunks may run on the addendum host ``entry`` now (module docstring). Each failure is a
    STOP naming why; it refuses only that node on that host."""
    host = entry["host"]
    n = S.node_entry(spec, node)
    if node == S.AR or node not in S.SEVEN or n["family"] not in entry["families"]:
        raise Stop(f"STOP: {node}'s audits stay on {S.WORKER_HOST} ({host} takes the G5-7 family only)")
    if S.options(spec)["G5-TASL-GPUH"] == "B":
        raise Stop(f"STOP: audit chunks on {host} are not built under G5-TASL-GPUH B")
    open_env = env_open(entry, node)
    if open_env:
        raise Stop(f"STOP: {node}'s environment on {host} is not filled ({open_env}); it may not run there yet (it may "
                   f"still run on the TASL pair)")
    out = {"host": host, "node": node, "hardware_class": hardware_class(spec, entry, read_main),
           "host_check": host_check(entry, read_main)}
    if spec["key_values"]["cuda_ipc"]["mode"] == "c12":
        out["cuda_ipc"] = check_c12(spec, entry, read_main)
    xc = entry["crosscheck"]
    if _sha_file(xc["spec"]) != xc["sha256"]:
        raise Stop(f"STOP: the cross-check spec {xc['spec']} in the checkout differs from its sha256")
    xspec = json.loads((REPO_ROOT / xc["spec"]).read_text())
    check_host_xc_spec(xspec)
    entries = entry["admission"][node]
    if not isinstance(entries, list):
        raise Stop(f"STOP: {xc_pending(node)} on {host}: no short cross-check PASS is listed; {node}'s audits run on "
                   f"the TASL pair only (R1-HOST-FREE (2)(b), R1-XC3-FAIL-READING)")
    e = entries[0]
    raw = read_main(e["record"]) if S._rel_ok(e["record"]) else None
    if raw is None or S._sha_bytes(raw) != e["sha256"]:
        raise Stop(f"STOP: the cross-host PASS record {e['record']} of {node} on {host} is not on published main with "
                   f"sha256 {e['sha256']}; {node}'s audits do not run on {host}")
    rec = check_verdict(xspec, node, e["record"], raw)
    found = _verdict_files(xc["host"], node, list_main)
    if found != [e["record"]]:
        raise Stop(f"STOP: the cross-check verdict files of {node} on {xc['host']} on published main ({found}) are not "
                   f"exactly the listed {e['record']}")
    out["crosshost_pass"] = {"node": node, "source": "addendum", "host": host, "records": [rec]}
    return out


def env_open(entry: dict, node: str) -> list[str]:
    """The node's environment entries on the host that are still placeholders (and its CPU set, if it has its own)."""
    nx = (entry.get("node_extra_env") or {}).get(node) or {}
    out = sorted(k for k, v in nx.items() if S._ph(v))
    if node in (entry.get("node_cpus") or {}) and S._ph(entry["node_cpus"][node]):
        out.append("node_cpus")
    return out


# =============================================================================================== the job side
def host_worker(spec: dict, entry: dict) -> dict:
    """The worker block of an addendum host, in the shape ``g5_job.host_worker`` gives for TASL-2 and TASL-7."""
    return {k: entry[k] for k in ("hostname", "gpu_uuid", "driver", "lease", "base", "runs_root", "uv", "cpus",
                                  "env_python", "extra_env")} | {"host": entry["host"],
                                                                  "sealed_root": spec["worker"]["sealed_root"]}


def gpu_check(entry: dict, smi=G._sh) -> dict:
    """The card of an addendum host: its UUID on this host, of the entry's GPU model and driver."""
    res = smi(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total", "--format=csv,noheader"])
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi failed: {res.stderr.strip()[:200]}")
    gpus = {r[0]: r for r in ([x.strip() for x in ln.split(",")] for ln in res.stdout.splitlines() if ln.strip())}
    want = entry["gpu_uuid"]
    if want not in gpus:
        raise Stop(f"STOP: the leased GPU {want} is not on this host ({sorted(gpus)})")
    if gpus[want][1] != entry["gpu_model"]:
        raise Stop(f"STOP: {want} is {gpus[want][1]}, not {entry['gpu_model']} (the addendum's GPU model for "
                   f"{entry['host']})")
    if len(gpus[want]) > 2 and gpus[want][2] != entry["driver"]:
        raise Stop(f"STOP: {want} runs driver {gpus[want][2]}, not {entry['driver']} (the addendum's)")
    return {"uuid": want, "name": gpus[want][1], "driver": gpus[want][2], "memory_total": gpus[want][3]}


def card_share_check(entry: dict, gpu_uuid: str | None, when: str, smi=G._sh) -> dict:
    """R1-CARD-SHARE on an addendum host: the card's free memory at least ``card_share.min_free_mib`` (else an
    infrastructure STOP: wait for memory and start again) and the count and memory of its other compute processes."""
    if gpu_uuid is None:
        return {"when": when, "device": "cpu", "other_processes": 0, "other_memory_mib": 0}
    res = smi(["nvidia-smi", "--query-gpu=uuid,memory.free", "--format=csv,noheader,nounits"])
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi memory query failed: {res.stderr.strip()[:200]}")
    free = None
    for ln in res.stdout.splitlines():
        parts = [x.strip() for x in ln.split(",")]
        if len(parts) >= 2 and parts[0] == gpu_uuid:
            try:
                free = int(float(parts[1]))
            except ValueError:
                free = None
    if free is None:
        raise Stop(f"STOP: the free memory of {gpu_uuid} could not be read ({when})")
    others = G.foreign_processes(gpu_uuid, {os.getpid()}, smi)
    mem = 0
    for p in others:
        m = re.match(r"^\s*(\d+)", str(p.get("used_memory") or ""))
        mem += int(m.group(1)) if m else 0
    out = {"when": when, "free_mib": free, "min_free_mib": entry["card_share"]["min_free_mib"],
           "other_processes": len(others), "other_memory_mib": mem}
    if free < entry["card_share"]["min_free_mib"]:
        raise Stop(f"STOP: {gpu_uuid} has {free} MiB free {when}, below the {entry['card_share']['min_free_mib']} MiB "
                   f"the addendum declares ({CARD_SHARE_ROW}; an infrastructure failure: start again when memory is "
                   f"free)")
    return out


def shared(checks: list[dict]) -> bool:
    return any(c.get("other_processes") for c in checks)


SHARED_STOP = ("STOP: another compute process was on the card during this attempt ({checks}); a run's budget decides a "
               "proposal only on an attempt that had its card to itself (R1-NO-TIMEOUT (2)), and the audit rows are "
               "sealed, so the attempt is an infrastructure failure and is repeated (R1-CARD-SHARE (3))")


# =============================================================================================== the cross-check spec
HOST_XC_KEYS = {"schema", "label", "status", "run_id", "comment", "rule_id", "rule", "host", "g1b_specs", "nodes",
                "part", "references", "verdicts", "pass_rule", "estimate", "caps"}
HOST_XC_HOST_KEYS = {"name", "hostname", "gpu_model", "gpu_uuid", "driver", "lease", "card_share", "base", "runs_root",
                     "uv", "cpus", "env_python", "extra_env", "isolation_host_check"}
XC_STATUS = ("draft: not launched; its runner (the short kind of g1b_crosscheck.py for a host outside the signed G.1b "
             "spec, with that host's GPU check) is a later reviewed unit")


def check_host_xc_spec(xc: dict, *, repo: Path | None = None) -> dict:
    """The cross-check spec of an addendum host (module docstring): structure, the eight nodes' references against the
    records in the checkout, the verdict paths, and the projection within the cap. Returns the projection."""
    repo = Path(repo or REPO_ROOT)
    if not isinstance(xc, dict) or set(xc) != HOST_XC_KEYS:
        raise Stop(f"STOP: the host cross-check spec carries exactly {sorted(HOST_XC_KEYS)}")
    if xc["schema"] != HOST_XC_SCHEMA or xc["label"] != G.ENGINEERING_ONLY or xc["status"] != XC_STATUS:
        raise Stop(f"STOP: the host cross-check spec must be {HOST_XC_SCHEMA}, ENGINEERING_ONLY, status as drafted")
    if xc["rule_id"] != HOST_FREE_ROW or not str(xc["rule"]).startswith(HOST_FREE_ROW + " (2)(b)"):
        raise Stop(f"STOP: the host cross-check spec's rule is {HOST_FREE_ROW} (2)(b)")
    h = xc["host"]
    if not isinstance(h, dict) or set(h) != HOST_XC_HOST_KEYS or not NAME.fullmatch(str(h["name"])) or \
            h["name"] in RESERVED or S._ph(h["gpu_model"]):
        raise Stop(f"STOP: host must carry exactly {sorted(HOST_XC_HOST_KEYS)}, a name other than {list(RESERVED)} and "
                   f"its GPU model")
    g7 = json.loads((repo / "sweep2/t1_tasl/g1b_tasl_spec.json").read_text())
    run_id = xc["run_id"]
    if not isinstance(run_id, str) or not L.SAFE.fullmatch(run_id) or not run_id.startswith(g7["run_id"] + "-xh-"):
        raise Stop(f"STOP: run_id must be a safe '{g7['run_id']}-xh-…' component")
    fam_specs = {"G5-7": "sweep2/t1_tasl/g1b_tasl_spec.json", "G5-AR": "sweep2/t1_tasl/g1b_tasl_ar_spec.json"}
    gs = xc["g1b_specs"]
    if not isinstance(gs, dict) or sorted(gs) != sorted(fam_specs):
        raise Stop(f"STOP: g1b_specs names the G.1b specs of {sorted(fam_specs)}")
    g1b = {}
    for fam, rel in fam_specs.items():
        e = gs[fam]
        doc = json.loads((repo / rel).read_text())
        want = {"path": rel, "sha256": L._sha_file(repo / rel), "run_id": doc["run_id"],
                "harness_commit": doc["harness"]["commit"]}
        if e != want:
            raise Stop(f"STOP: g1b_specs.{fam} must be {want}")
        g1b[fam] = doc
    if list(xc["nodes"]) != list(EIGHT):
        raise Stop(f"STOP: nodes must be the eight T1 nodes {list(EIGHT)}")
    refs = xc["references"]
    if not isinstance(refs, dict) or sorted(refs) != sorted(EIGHT):
        raise Stop("STOP: references must name each of the eight nodes' sealed TASL-2 attempt")
    xc3 = json.loads((repo / S.XC3_SPEC_REL).read_text())
    for node in EIGHT:
        _check_reference(node, refs[node], xc3, repo)
    verdicts = xc["verdicts"]
    if not isinstance(verdicts, dict) or sorted(verdicts) != sorted(EIGHT) or len(set(verdicts.values())) != 8:
        raise Stop("STOP: verdicts must give each node its own repository path")
    for node, rel in verdicts.items():
        m = VERDICT_NAME.fullmatch(str(rel))
        if not m or m.group("host") != h["name"] or m.group("node") != node:
            raise Stop(f"STOP: verdicts.{node} must be docs/r1/reports/<dir>/{VERDICT_TOKEN}{h['name']}_{node}_"
                       f"<YYYYMMDD>.json")
    proj = host_xc_projection(xc, g1b)
    cap = (xc["caps"] or {}).get("max_gpu_hours")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or not 0 < cap <= G.CROSSCHECK_GPU_HOURS_MAX:
        raise Stop(f"STOP: caps.max_gpu_hours must be in (0, {G.CROSSCHECK_GPU_HOURS_MAX}]")
    if proj["sensitivity"]["gpu_hours"] > cap:
        raise Stop(f"STOP: the projection at the sensitivity ratio ({proj['sensitivity']['gpu_hours']} GPU-h) exceeds "
                   f"caps.max_gpu_hours {cap}")
    return proj


def _check_reference(node: str, ref: dict, xc3: dict, repo: Path) -> None:
    keys = {"family", "run_id", "attempt", "spec_sha256", "job_record_sha256", "source"}
    if not isinstance(ref, dict) or set(ref) != keys:
        raise Stop(f"STOP: references.{node} carries exactly {sorted(keys)}")
    src = ref["source"]
    if not isinstance(src, dict) or set(src) != {"record", "sha256"} or _sha_file(src["record"]) != src["sha256"]:
        raise Stop(f"STOP: references.{node}.source must name a file in the checkout at its sha256")
    want_fam = "G5-AR" if node == S.AR else "G5-7"
    if ref["family"] != want_fam:
        raise Stop(f"STOP: references.{node}.family must be {want_fam}")
    if node in S.X_NODES or node in xc3["nodes"]:
        rel = XC2_STEP1.format(node=node) if node in S.X_NODES else xc3["verdicts"][node]
        if src["record"] != rel:
            raise Stop(f"STOP: references.{node}.source must be {rel} (the verdict that records its sealed TASL-2 "
                       f"attempt)")
        side = json.loads((repo / rel).read_text())["sides"]["TASL-2"]
        bad = [k for k in SIDE_FIELDS if side.get(k) != ref[k]]
        if node in xc3["nodes"]:
            a = xc3["g1b_tasl2_attempts"][node]
            bad += [k for k, v in (("attempt", a["attempt"]), ("spec_sha256", a["spec_sha256"]),
                                   ("job_record_sha256", a["job_record_sha256"])) if ref[k] != v]
        if bad:
            raise Stop(f"STOP: references.{node} differs from its recorded sealed TASL-2 attempt in {sorted(set(bad))}")
        return
    if node != S.AR or src["record"] != AR_REFERENCE_RECORD:
        raise Stop(f"STOP: references.{node}.source must be {AR_REFERENCE_RECORD}")
    text = (repo / AR_REFERENCE_RECORD).read_text()
    ar = json.loads((repo / "sweep2/t1_tasl/g1b_tasl_ar_spec.json").read_text())
    if ref["run_id"] != ar["run_id"] or ref["attempt"] != 1 or ref["spec_sha256"] != L._sha_file(
            repo / "sweep2/t1_tasl/g1b_tasl_ar_spec.json") or ref["job_record_sha256"] not in text or \
            ref["spec_sha256"] not in text or "attempt-1" not in text:
        raise Stop(f"STOP: references.{node} is not the sealed G.1b-AR TASL-2 attempt that {AR_REFERENCE_RECORD} "
                   f"records")


def host_xc_projection(xc: dict, g1b: dict) -> dict:
    """Per node the default part's runs ((n_edits + 1) x 2 conditions) at the census times x the ratio, plus the setup
    estimate; GPU-h for the GPU nodes (the CPU-only node's core-hours apart). The census ran on RTX 6000 Ada cards, so
    the estimate ratio is 1.0; the sensitivity 1.5 is the G.1b spec's."""
    est = g1b["G5-7"]["estimate"]
    out = {}
    for label, ratio in (("estimate", 1.0), ("sensitivity", est["ratio_sensitivity"])):
        per, gpu_h, core_h = {}, 0.0, 0.0
        for node in xc["nodes"]:
            doc = g1b["G5-AR"] if node == S.AR else g1b["G5-7"]
            n = G.node_entry(doc, node)
            runs = (n["n_edits"] + 1) * len(X.DEFAULT_CONDITIONS)
            hours = (runs * float(n["run_seconds"]) * ratio + est["setup_estimate_s"]) / 3600.0
            per[node] = {"runs": runs, "device": n["device"], "hours": round(hours, 3)}
            if n["device"] == "gpu":
                gpu_h += hours
            else:
                core_h += hours * len(G.cpu_list(n["cpus"]))
        out[label] = {"per_node": per, "gpu_hours": round(gpu_h, 3), "cpu_core_hours": round(core_h, 3)}
    return out
