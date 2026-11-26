"""The R1-T1-TASL-ENV cross-host check of the G.1b TASL-7 nodes: their default parts run on both hosts, and the
outcomes must be identical. AI-assisted (Claude). ENGINEERING_ONLY: no label is read.

R1-T1-TASL-ENV: "The G.1b nodes measured on TASL-7 also run their default parts on TASL-2, and the metrics must be
identical, else STOP and that node's G.1b is re-measured on TASL-2." R1-G1B-TASL-DECISIONS (XC A): the three TASL-7
nodes run under a second note "once the reviewed cross-host check job has passed".

**The job.** For each TASL-7 node (``mlab_cifar10``, ``mlgym_cifar10``, ``mlgym_breakout_minatar``) and each host:

- a per-(node, host) spec is derived from the signed G.1b spec (bound by sha256 in the cross-check spec). The run id is
  ``<cross-check run id>-<host>``, the paper commit is the cross-check spec's, the node is assigned to that host, and
  TASL-2 gains the declared ``env_python`` entries the nodes need there (``jax312`` for Breakout). Everything else is
  unchanged: harness pin, envs and freezes, kit pins, data manifests, timeouts, and the host identities and checks;
- the pinned ``g1b_tasl.run_node_job`` runs that node's **default part only** (default and default_repeat, (N + 1) × 2
  = 10 runs) under the same lease, delegated scope, preflight and row gate as G.1b. It is started by
  ``t1_tasl_node.sh xc <cross-check spec> <node> <note> <host> [--enable]``, which asks this script for the node's
  ``cpus`` and the derived run's ``logdir`` (``--host``). The attempt is written under
  ``<runs_root>/<run id>-<host>/<node>/attempt-N/`` and sealed with ``g1b_tasl.py seal`` against the derived spec.
  ``run_xc`` narrows ``g1b_lib.PARTS`` and ``merge_parts`` for the one job and restores them (not re-entrant).

**The comparison.** ``compare --mode`` reads two sealed attempts of a node and refuses inputs that are not the attempts
the mode names:
- receipt, sums (exactly ``out.tar`` and ``job_record.json``) and record bound together (node, run id, host, attempt);
- each side's run id and spec sha256: ``xc`` mode, the two cross-check runs and their derived specs' sha256 (recomputed);
  ``preassembly`` mode, the TASL-7 side is the node's G.1b attempt (the signed run id and spec sha256);
- the harness at the pin, every row of the node, one regular ``out/default/runs.jsonl`` in the tar.

The verdict is PASS when the default and default_repeat outcomes (``g1b_lib._outcome``: the metric bit-identical when
ok, the same failure when failed) of c0..cN are all present and identical on both sides and both sides are
deterministic. Otherwise it is STOP, with a reason: ``incomplete``, ``nondeterministic:<host>`` (not a cross-host
result; a re-measure would be a second draw) or ``cross_host_mismatch`` (the row's re-measure on TASL-2, decision
XC-REMEASURE). It runs twice per node:

1. before the TASL-7 G.1b launch, ``xc`` mode. The three PASS verdicts are committed on main and cited by path and
   sha256 in the second G.1b note's P7; ``check-note2 --draft`` checks the unsigned note before signature, and
   ``check-note2`` (strict) the published note before any TASL-7 node launches;
2. before assembly, ``preassembly`` mode: the node's G.1b TASL-7 attempt against the cross-check's TASL-2 attempt (the
   row's literal comparison). ``assemble`` (``assemble_gated``) is the assembly for the run with TASL-7 nodes: for each
   it recomputes this comparison from the attempts given, requires it to equal the committed step-2 PASS verdict, and
   only then runs ``g1b_tasl.assemble`` with the signed spec, unchanged, and writes ``crosscheck_gate.json`` binding
   the assembly; ``summarise`` (``summarise_gated``) summarises only a run carrying a matching gate record.

**Launch.** A signed note ``docs/r1/authorizations/g1b_xc_t1_tasl_<YYYYMMDD>.md`` on published ``main`` is required
(``check_xc_note``; no unfilled field), as are both keys (``--enable`` and ``G1B_TASL_ENABLE_REAL=1``) and both hosts'
host-check records on ``main``. The launch binding is ``verify_launch_tasl`` with the cross-check spec: its
``paper.commit`` is a code-equal ancestor of the published checkout.

**The short cross-check** (schema ``g1b_tasl_crosscheck_short_spec/1``; R1-G5-AUDIT-TWO-CARDS: "for the others, a
short cross-check under the reviewed ``g1b_crosscheck.py`` before their first TASL-7 audit chunk"). It is the same job
and the same comparison, for G.1b nodes measured on **TASL-2**, with one host run instead of two:

- ``nodes`` are G.1b TASL-2 nodes and ``hosts`` is ``["TASL-7"]``: the only job per node is the default part on
  TASL-7 (10 runs), under its derived spec (as above) and the same lease, scope, preflight and row gate;
- the TASL-2 side is the node's **sealed G.1b TASL-2 attempt** (its default part is the same 10 runs), declared per
  node in ``g1b_tasl2_attempts``: attempt number, ``job_record.json`` sha256, and the spec sha256 its record carries,
  which must be the ``spec_sha256`` of the signed G.1b note named beside it (the first note's predecessor spec only for
  a node outside R1-T1-DATA-MANIFEST's corrected nodes, as in R1-G1B-JOIN);
- ``compare --mode short`` takes the TASL-7 attempt and that G.1b attempt; the PASS criterion is the reviewed one,
  unchanged (every default and default_repeat outcome of c0..cN present and identical, both sides deterministic);
- ``extra_env_additions`` may give TASL-7 an ``extra_env`` entry that the G.1b spec declares for TASL-2, with the same
  value (``mlgym_houseprice``'s ``AR_HOUSEPRICE_TRAIN_CSV``), never one TASL-7 already has;
- each node's verdict has a fixed repository path (``verdicts``), bound by the spec; ``verdict-status`` reports each
  node's committed verdict on ``origin/main`` (PASS, STOP or PENDING) for the G.5 audit-host gate;
- the projection (10 runs per node at the G.1b estimate ratio, plus the setup estimate per job) must stay within
  ``caps.max_gpu_hours``;
- the note is ``docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md`` (P1 cites R1-G5-AUDIT-TWO-CARDS), and the
  launch also needs that row on ``main``. ``check-note2``, ``assemble`` and ``summarise`` refuse a short spec.

- the signed short note carries the author's choices as key lines bound to their allowed values (``xc3_fail`` A|B,
  ``xc3_cap`` R1-G1B-CAP|G5-CAP, ``skip_nodes`` none or some of the nodes); ``launch_xc`` refuses a node the note
  skips, and before each GPU job it refuses unless the GPU lease hours used so far by the run plus that job's
  projection stay within the cap (``short_cap_gate``); in strict mode, once the author's PLAN row
  ``R1-XC3-FAIL-READING`` is on main, ``xc3_fail`` must equal the option its sentence "The xc3 note carries xc3_fail:
  A|B." names. ``short_decisions`` and ``check_xc_note`` are stable helpers for the G.5 audit-host reader;
- each declared G.1b TASL-2 attempt also pins its ``out.tar`` and ``SHA256SUMS`` sha256, and the three pins must be
  consistent (``SHA256SUMS`` as the job writes it); ``compare --mode short`` checks the ``job_record.json`` and
  ``SHA256SUMS`` pins.

``check-xc-note --draft`` checks an unsigned cross-check note before signature (exactly one ``approved: false``; P4,
the review, may still be PENDING; nothing read from ``main``).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "g1b"))
import g1b_tasl as G  # noqa: E402
import g1b_lib as L  # noqa: E402

Stop = G.Stop
XC_SCHEMA = "g1b_tasl_crosscheck_spec/1"
VERDICT_SCHEMA = "g1b_tasl_crosscheck_verdict/1"
XC_NOTE_NAME = re.compile(r"^g1b_xc_t1_tasl_\d{8}\.md$")
CROSS_HOSTS = ("TASL-7", "TASL-2")
DEFAULT_CONDITIONS = ("default", "default_repeat")
MODES = ("xc", "preassembly", "short")
GATE_SCHEMA = "g1b_tasl_crosscheck_gate/1"
SEALED_FILES = {"out.tar", "job_record.json"}
_ACTIVE = {"run": False}

# The short cross-check (R1-G5-AUDIT-TWO-CARDS; module docstring)
XC_SHORT_SCHEMA = "g1b_tasl_crosscheck_short_spec/1"
SHORT_RULE = "R1-G5-AUDIT-TWO-CARDS"
SHORT_HOSTS = ("TASL-7",)
SHORT_MODE = "short"
XC_SHORT_NOTE_NAME = re.compile(r"^g1b_xc_short_t1_tasl_\d{8}\.md$")
SHORT_VERDICT_DIR = "docs/r1/reports/"
# The author's choices in a short note, each one key line bound to its allowed values (signing unchanged adopts the
# first, recommended value): XC3-FAIL (does a non-PASS remove the node from G.5, B, or only from TASL-7 audits, A),
# XC3-CAP (the budget the run's GPU-h count against) and ``skip_nodes`` (nodes the author removes from the run).
SHORT_DECISIONS = {"xc3_fail": ("A", "B"), "xc3_cap": ("R1-G1B-CAP", "G5-CAP")}
# The author's PLAN row recording decision XC3-FAIL (its proposed text ends "The xc3 note carries xc3_fail: A|B.").
XC3_FAIL_ROW = "R1-XC3-FAIL-READING"
XC3_FAIL_ROW_SENTENCE = re.compile(r"The xc3 note carries xc3_fail: ([AB])\.")
# The short verdicts' file names: only the spec's bound paths may carry them on main (G.5 reads them by name).
SHORT_VERDICT_PREFIX = "G1B_XC3_SHORT_VERDICT_"


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _sums_sha(out_tar_sha256: str, job_record_sha256: str) -> str:
    """The sha256 of an attempt's ``SHA256SUMS`` as the job writes it (``g1b_lib._write_sums``: out.tar, then
    job_record.json)."""
    return hashlib.sha256(f"{out_tar_sha256}  out.tar\n{job_record_sha256}  job_record.json\n".encode()).hexdigest()


def is_short(xc: dict) -> bool:
    return xc.get("schema") == XC_SHORT_SCHEMA


def _extra_env_additions(xc: dict, g1b: dict) -> None:
    """A host may gain an ``extra_env`` entry the G.1b spec declares for the other host, with the same value; never one
    the host already has (the derived spec then sets it for that host's job)."""
    adds = xc.get("extra_env_additions") or {}
    if not isinstance(adds, dict):
        raise Stop("STOP: extra_env_additions must map a host to {name: value}")
    for host, envs in adds.items():
        if host not in xc["hosts"] or not isinstance(envs, dict) or not envs:
            raise Stop("STOP: extra_env_additions must map a host of the cross-check to {name: value}")
        other = [h for h in CROSS_HOSTS if h != host]
        theirs = (g1b["hosts"][other[0]].get("extra_env") or {}) if other else {}
        mine = g1b["hosts"][host].get("extra_env") or {}
        for name, value in envs.items():
            if name in mine:
                raise Stop(f"STOP: extra_env_additions.{host}.{name} would override the G.1b spec")
            if theirs.get(name) != value:
                raise Stop(f"STOP: extra_env_additions.{host}.{name} must be the other host's declared extra_env entry "
                           "with the same value")


def short_projection(xc: dict, g1b: dict) -> dict:
    """The short cross-check's projection: per node the default part's runs at the census times x the G.1b estimate
    ratio (and its sensitivity), plus the setup estimate per job; GPU-h for the GPU nodes, core-hours for the CPU-only
    node on its own cpuset."""
    est = g1b["estimate"]
    out = {}
    for label, ratio in (("estimate", est["ratio_4090_over_ada"]), ("sensitivity", est["ratio_sensitivity"])):
        per_node, gpu_h, core_h = {}, 0.0, 0.0
        for name in xc["nodes"]:
            node = G.node_entry(g1b, name)
            runs = (node["n_edits"] + 1) * len(DEFAULT_CONDITIONS)
            hours = (runs * float(node["run_seconds"]) * ratio + est["setup_estimate_s"]) / 3600.0
            per_node[name] = {"runs": runs, "device": node["device"], "hours": round(hours, 3)}
            if node["device"] == "gpu":
                gpu_h += hours
            else:
                core_h += hours * len(G.cpu_list(G.node_cpus(g1b, node)))
        out[label] = {"per_node": per_node, "gpu_hours": round(gpu_h, 3), "cpu_core_hours": round(core_h, 3),
                      "runs": sum(v["runs"] for v in per_node.values())}
    out["cap_gpu_hours"] = (xc.get("caps") or {}).get("max_gpu_hours")
    out["within_cap"] = out["estimate"]["gpu_hours"] <= float(out["cap_gpu_hours"] or 0)
    return out


def _validate_short(xc: dict, g1b: dict, repo: Path) -> None:
    """The short spec's own rules (module docstring)."""
    tasl2 = sorted(n["node"] for n in g1b["nodes"] if n["host"] == "TASL-2")
    nodes = xc.get("nodes") or []
    if not nodes or len(set(nodes)) != len(nodes) or set(nodes) - set(tasl2):
        raise Stop(f"STOP: nodes must be distinct G.1b TASL-2 nodes {tasl2} (the TASL-7 nodes have the xc2 verdicts)")
    if list(xc.get("hosts") or []) != list(SHORT_HOSTS):
        raise Stop(f"STOP: hosts must be {list(SHORT_HOSTS)} (the TASL-2 side is the node's sealed G.1b attempt)")
    if not str(xc.get("rule", "")).startswith(SHORT_RULE):
        raise Stop(f"STOP: rule must cite {SHORT_RULE}")
    if xc.get("env_python_additions"):
        raise Stop("STOP: a short spec runs the TASL-2 nodes' environments, which TASL-7 declares (no env additions)")
    import g1b_tasl_join as J    # noqa: E402  (here: it imports this module)
    attempts = xc.get("g1b_tasl2_attempts") or {}
    if sorted(attempts) != sorted(nodes):
        raise Stop("STOP: g1b_tasl2_attempts must name exactly the cross-check nodes")
    for node, a in attempts.items():
        if not isinstance(a, dict) or type(a.get("attempt")) is not int or a["attempt"] < 1:
            raise Stop(f"STOP: g1b_tasl2_attempts.{node}.attempt must be a positive integer")
        for key in ("spec_sha256", "job_record_sha256", "out_tar_sha256", "sha256sums_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(a.get(key, ""))):
                raise Stop(f"STOP: g1b_tasl2_attempts.{node}.{key} must be a sha256")
        if _sums_sha(a["out_tar_sha256"], a["job_record_sha256"]) != a["sha256sums_sha256"]:
            raise Stop(f"STOP: g1b_tasl2_attempts.{node}: sha256sums_sha256 is not the SHA256SUMS of its out.tar and "
                       "job_record.json pins (a pin names the wrong file)")
        rel = Path(str(a.get("note", "")))
        if rel.is_absolute() or ".." in rel.parts or rel.parent.as_posix() != G.NOTE_DIR or \
                not G.NOTE_NAME.fullmatch(rel.name) or not (repo / rel).is_file():
            raise Stop(f"STOP: g1b_tasl2_attempts.{node}.note must be a signed G.1b note {G.NOTE_DIR}/g1b_t1_tasl_<date>.md")
        f = G._note_fields((repo / rel).read_bytes())
        if f.get("approved") != "true" or f.get("run_id") != g1b["run_id"] or \
                f.get("harness_commit") != g1b["harness"]["commit"] or f.get("spec_sha256") != a["spec_sha256"]:
            raise Stop(f"STOP: {rel} is not a signed G.1b note of run {g1b['run_id']} at the pin with spec_sha256 "
                       f"{a['spec_sha256'][:8]}… ({node})")
        if a["spec_sha256"] != xc["g1b_spec"]["sha256"] and node in J.CORRECTED_NODES:
            raise Stop(f"STOP: {node}'s G.1b attempt must carry the re-issued spec (R1-T1-DATA-MANIFEST, R1-G1B-JOIN)")
    verdicts = xc.get("verdicts") or {}
    if sorted(verdicts) != sorted(nodes) or len(set(verdicts.values())) != len(verdicts):
        raise Stop("STOP: verdicts must give each cross-check node its own repository path")
    for node, rel in verdicts.items():
        rx = rf"{re.escape(SHORT_VERDICT_DIR)}[A-Za-z0-9_./-]*_{re.escape(node)}_\d{{8}}\.json"
        if not re.fullmatch(rx, str(rel)) or ".." in Path(rel).parts:
            raise Stop(f"STOP: verdicts.{node} must be docs/r1/reports/…_{node}_<YYYYMMDD>.json")
    cap = (xc.get("caps") or {}).get("max_gpu_hours")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or not 0 < cap <= G.CROSSCHECK_GPU_HOURS_MAX:
        raise Stop(f"STOP: caps.max_gpu_hours must be in (0, {G.CROSSCHECK_GPU_HOURS_MAX}]")
    proj = short_projection(xc, g1b)
    if not proj["within_cap"]:
        raise Stop(f"STOP: projected {proj['estimate']['gpu_hours']} GPU-h exceeds caps.max_gpu_hours {cap}: author STOP")


def load_xc(xc_path: Path, repo: Path | None = None) -> tuple[dict, dict, Path]:
    """(cross-check spec, signed G.1b spec, its path), validated."""
    repo = Path(repo or G.REPO_ROOT)
    xc = json.loads(Path(xc_path).read_text())
    if xc.get("schema") not in (XC_SCHEMA, XC_SHORT_SCHEMA) or xc.get("label") != G.ENGINEERING_ONLY:
        raise Stop(f"STOP: the cross-check spec must be {XC_SCHEMA} (or {XC_SHORT_SCHEMA}), ENGINEERING_ONLY")
    ref = xc.get("g1b_spec") or {}
    rel = Path(str(ref.get("path", "")))
    if rel.is_absolute() or ".." in rel.parts or not ref.get("sha256"):
        raise Stop("STOP: g1b_spec must name the repository-relative G.1b spec and its sha256")
    g1b_path = repo / rel
    if not g1b_path.is_file() or _sha(g1b_path) != ref["sha256"]:
        raise Stop("STOP: the G.1b spec differs from the one the cross-check spec binds (the signed spec)")
    g1b = G.load_spec(g1b_path)
    run_id = xc.get("run_id")
    if not isinstance(run_id, str) or not L.SAFE.fullmatch(run_id) or not run_id.startswith(g1b["run_id"] + "-"):
        raise Stop(f"STOP: run_id must be a safe '<G.1b run id>-…' component ({g1b['run_id']})")
    paper = xc.get("paper") or {}
    if paper.get("repo") != g1b["paper"]["repo"] or not L.COMMIT.fullmatch(str(paper.get("commit", ""))):
        raise Stop("STOP: paper must name the G.1b repository and a full commit")
    if is_short(xc):
        _validate_short(xc, g1b, repo)
        _extra_env_additions(xc, g1b)
        return xc, g1b, g1b_path
    tasl7 = sorted(n["node"] for n in g1b["nodes"] if n["host"] == "TASL-7")
    if sorted(xc.get("nodes") or []) != tasl7:
        raise Stop(f"STOP: nodes must be exactly the G.1b TASL-7 nodes {tasl7}")
    if list(xc.get("hosts") or []) != list(CROSS_HOSTS):
        raise Stop(f"STOP: hosts must be {list(CROSS_HOSTS)}")
    if xc.get("extra_env_additions"):
        _extra_env_additions(xc, g1b)
    adds = xc.get("env_python_additions") or {}
    for host, envs in adds.items():
        if host not in CROSS_HOSTS or not isinstance(envs, dict):
            raise Stop("STOP: env_python_additions must map a host to {env: python}")
        for env, py in envs.items():
            if env not in g1b["envs"] or not str(py).startswith("/") or ".." in Path(py).parts:
                raise Stop(f"STOP: env_python_additions.{host}.{env} must be a declared env and an absolute path")
            if env in g1b["hosts"][host].get("env_python", {}):
                raise Stop(f"STOP: env_python_additions.{host}.{env} would override the G.1b spec")
    if not str(xc.get("rule", "")).startswith("R1-T1-TASL-ENV"):
        raise Stop("STOP: rule must cite R1-T1-TASL-ENV")
    return xc, g1b, g1b_path


def derived_spec(g1b: dict, xc: dict, node: str, host: str) -> dict:
    """The spec of one (node, host) cross-check job (module docstring)."""
    if node not in xc["nodes"] or host not in CROSS_HOSTS or host not in xc["hosts"]:
        raise Stop(f"STOP: {node} on {host} is not a cross-check job")
    spec = copy.deepcopy(g1b)
    spec["run_id"] = f"{xc['run_id']}-{host}"
    spec["paper"] = dict(xc["paper"])
    for env, py in (xc.get("env_python_additions") or {}).get(host, {}).items():
        spec["hosts"][host]["env_python"][env] = py
    for name, value in (xc.get("extra_env_additions") or {}).get(host, {}).items():
        spec["hosts"][host].setdefault("extra_env", {})[name] = value
    entry = G.node_entry(spec, node)
    entry["host"] = host
    if entry["env"] not in spec["hosts"][host]["env_python"]:
        raise Stop(f"STOP: {node} needs {entry['env']} on {host}; declare it in env_python_additions")
    spec["crosscheck"] = {"node": node, "host": host, "crosscheck_run_id": xc["run_id"],
                          "g1b_spec_sha256": xc["g1b_spec"]["sha256"]}
    if is_short(xc):              # only for the short kind: the xc2 derived specs (and their sha256s) are unchanged
        spec["crosscheck"].update(kind=SHORT_MODE, rule=SHORT_RULE)
    G.validate_spec(spec, launch=True)
    return spec


def derived_bytes(spec: dict) -> bytes:
    """The derived spec file's bytes (its sha256 is what the job record carries as ``spec_sha256``)."""
    return (json.dumps(spec, indent=1, sort_keys=True) + "\n").encode()


def write_derived(spec: dict, node: str) -> Path:
    """Write the derived spec once under its run root; a later call must find the same bytes."""
    host = spec["crosscheck"]["host"]
    path = Path(spec["hosts"][host]["runs_root"]) / spec["run_id"] / "_specs" / f"{node}.json"
    data = derived_bytes(spec)
    if path.exists():
        if path.is_symlink() or path.read_bytes() != data:
            raise Stop(f"STOP: {path} exists with other content")
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _default_only_merge(out: Path, node: dict) -> dict:
    rows = L._rows(out / "default" / "runs.jsonl")
    for row in rows:
        L.check_row_gate(row)
    expected = (node["n_edits"] + 1) * len(DEFAULT_CONDITIONS)
    if len(rows) != expected:
        raise Stop(f"STOP: {node['node']} default part wrote {len(rows)} rows, expected {expected}")
    with (out / "runs.jsonl").open("x") as fh:
        fh.writelines(json.dumps(r, sort_keys=True) + "\n" for r in rows)
    (out / "edits.json").write_bytes((out / "default" / "edits.json").read_bytes())
    return {"expected": expected, "written": len(rows), "successful": sum(1 for r in rows if r["success"]),
            "divergent": sum(1 for r in rows if not r["success"]), "crosscheck_default_part": True}


def run_xc(xc_path: Path, node: str, host: str, **job_kw) -> dict:
    """One cross-check job: the derived spec, then the pinned node job with the default part only."""
    if _ACTIVE["run"]:
        raise Stop("STOP: run_xc is not re-entrant (it patches g1b_lib.PARTS and merge_parts for one job)")
    xc, g1b, _ = load_xc(xc_path)
    spec = derived_spec(g1b, xc, node, host)
    path = write_derived(spec, node)
    saved = (L.PARTS, L.merge_parts)
    if saved[0][0][0] != "default":
        raise Stop("STOP: g1b_lib.PARTS does not start with the default part")
    _ACTIVE["run"] = True
    L.PARTS, L.merge_parts = (L.PARTS[0],), _default_only_merge
    try:
        return G.run_node_job(path, node, **job_kw)
    finally:
        L.PARTS, L.merge_parts = saved
        _ACTIVE["run"] = False


def _sealed_rows(sealed: Path, node: str) -> tuple[dict, list[dict]]:
    """A sealed attempt of ``node``: receipt, sums (exactly ``out.tar`` and ``job_record.json``) and record bound to each
    other, a complete ENGINEERING_ONLY attempt, and its default-part rows (row gate re-checked, every row of ``node``)."""
    sealed = Path(sealed)
    if not (sealed / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: {sealed} has no SEAL_RECEIPT.json (not sealed)")
    if not (sealed / "SHA256SUMS").is_file():
        raise Stop(f"STOP: {sealed} has no SHA256SUMS")
    names = [line.split("  ", 1)[1] for line in (sealed / "SHA256SUMS").read_text().splitlines() if "  " in line]
    if sorted(names) != sorted(SEALED_FILES):
        raise Stop(f"STOP: {sealed}/SHA256SUMS must list exactly {sorted(SEALED_FILES)}, not {sorted(names)}")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed, capture_output=True).returncode != 0:
        raise Stop(f"STOP: {sealed} does not verify against its SHA256SUMS")
    record = json.loads((sealed / "job_record.json").read_text())
    receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    host = (record.get("host") or {}).get("host")
    bound = {"job_record_sha256": receipt.get("job_record_sha256") == _sha(sealed / "job_record.json"),
             "node": receipt.get("node") == record.get("node") == node,
             "run_id": receipt.get("run_id") == record.get("run_id"),
             "host": receipt.get("host") == host,
             "attempt": receipt.get("attempt") == record.get("attempt") and sealed.name == f"attempt-{record.get('attempt')}"}
    bad = sorted(k for k, ok in bound.items() if not ok)
    if bad:
        raise Stop(f"STOP: {sealed} receipt does not bind its job record ({bad})")
    if record.get("label") != G.ENGINEERING_ONLY or record.get("stop_class") not in (None, "node"):
        raise Stop(f"STOP: {sealed} is not a complete ENGINEERING_ONLY attempt (stop_class {record.get('stop_class')})")
    try:
        with tarfile.open(sealed / "out.tar") as tar:
            members = tar.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)):
                raise Stop(f"STOP: {sealed}/out.tar has duplicate members")
            hits = [m for m in members if m.name == "out/default/runs.jsonl"]
            if len(hits) != 1 or not hits[0].isfile():
                raise Stop(f"STOP: {sealed}/out.tar has no single regular out/default/runs.jsonl")
            data = tar.extractfile(hits[0]).read()
    except (tarfile.TarError, OSError) as exc:
        raise Stop(f"STOP: {sealed}/out.tar cannot be read: {exc}") from exc
    rows = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
    for row in rows:
        L.check_row_gate(row)
        if row.get("node") != node:
            raise Stop(f"STOP: a row of {sealed} names node {row.get('node')!r}")
    return record, [r for r in rows if r.get("condition") in DEFAULT_CONDITIONS]


def expected_sides(xc: dict, g1b: dict, node: str, mode: str) -> dict:
    """{host: (run_id, spec_sha256)} the two attempts must carry. ``xc``: both cross-check jobs (spec sha256 of each
    derived spec, recomputed). ``preassembly``: the node's G.1b TASL-7 attempt (the signed G.1b run id and spec) against
    the cross-check's TASL-2 attempt."""
    if mode not in MODES:
        raise Stop(f"STOP: mode must be one of {MODES}")
    if (mode == SHORT_MODE) != is_short(xc):
        raise Stop(f"STOP: mode {mode} is not a mode of this cross-check spec ({xc.get('schema')})")
    if mode == SHORT_MODE:       # the TASL-7 job against the node's declared sealed G.1b TASL-2 attempt
        t7 = (f"{xc['run_id']}-TASL-7",
              hashlib.sha256(derived_bytes(derived_spec(g1b, xc, node, "TASL-7"))).hexdigest())
        return {"TASL-7": t7, "TASL-2": (g1b["run_id"], xc["g1b_tasl2_attempts"][node]["spec_sha256"])}
    out = {h: (f"{xc['run_id']}-{h}", hashlib.sha256(derived_bytes(derived_spec(g1b, xc, node, h))).hexdigest())
           for h in CROSS_HOSTS}
    if mode == "preassembly":
        out["TASL-7"] = (g1b["run_id"], xc["g1b_spec"]["sha256"])
    return out


def compare(a: Path, b: Path, node: str, *, mode: str, xc_path: Path, repo: Path | None = None) -> dict:
    """The verdict of two sealed attempts of ``node`` on different hosts (module docstring). Inputs that are not the
    attempts the mode names are refused (Stop); a verdict STOP is about the outcomes."""
    xc, g1b, _ = load_xc(xc_path, repo)
    if node not in xc["nodes"]:
        raise Stop(f"STOP: {node} is not a cross-check node")
    want = expected_sides(xc, g1b, node, mode)
    configs = ["c0"] + [f"c{k}" for k in range(1, G.node_entry(g1b, node)["n_edits"] + 1)]
    pin = g1b["harness"]["commit"]
    sides = {}
    for path in (a, b):
        record, rows = _sealed_rows(path, node)
        host = (record.get("host") or {}).get("host")
        if host not in CROSS_HOSTS or host in sides:
            raise Stop(f"STOP: {path} is not an attempt of {node} on the other host")
        got = (record.get("run_id"), record.get("spec_sha256"))
        if got != want[host]:
            raise Stop(f"STOP: {path} is not the {mode} attempt on {host}: run_id/spec_sha256 {got} != {want[host]}")
        if record.get("harness_commit") != pin:
            raise Stop(f"STOP: {path} ran harness {record.get('harness_commit')}, not the pin {pin}")
        if mode == SHORT_MODE and host == "TASL-2":
            declared = xc["g1b_tasl2_attempts"][node]
            if record.get("attempt") != declared["attempt"] or \
                    _sha(Path(path) / "job_record.json") != declared["job_record_sha256"] or \
                    _sha(Path(path) / "SHA256SUMS") != declared["sha256sums_sha256"]:
                raise Stop(f"STOP: {path} is not {node}'s declared sealed G.1b TASL-2 attempt "
                           f"(attempt {declared['attempt']}, job_record {declared['job_record_sha256'][:8]}…, "
                           f"SHA256SUMS {declared['sha256sums_sha256'][:8]}…)")
        outcomes = {}
        for row in rows:
            key = (row["config"], row["condition"])
            if key in outcomes:
                raise Stop(f"STOP: {path} has two rows for {key}")
            outcomes[key] = L._outcome(row)
        det = L.determinism_check(rows)
        sides[host] = {"sealed": str(path), "job_record_sha256": _sha(Path(path) / "job_record.json"),
                       "run_id": got[0], "spec_sha256": got[1], "attempt": record.get("attempt"),
                       "harness_commit": record.get("harness_commit"), "deterministic": det["deterministic"],
                       "outcomes": outcomes}
    t7, t2 = sides["TASL-7"], sides["TASL-2"]
    expected = {(c, cond) for c in configs for cond in DEFAULT_CONDITIONS}
    complete = all(set(s["outcomes"]) == expected for s in (t7, t2))
    per = {f"{c}/{cond}": {"TASL-7": t7["outcomes"].get((c, cond)), "TASL-2": t2["outcomes"].get((c, cond)),
                          "identical": (c, cond) in t7["outcomes"] and (c, cond) in t2["outcomes"]
                          and t7["outcomes"][(c, cond)] == t2["outcomes"][(c, cond)]}
           for c, cond in sorted(expected | set(t7["outcomes"]) | set(t2["outcomes"]))}
    if not complete:
        reason = "incomplete"
    elif not (t7["deterministic"] and t2["deterministic"]):
        reason = "nondeterministic:" + ",".join(h for h in CROSS_HOSTS if not sides[h]["deterministic"])
    elif not all(v["identical"] for v in per.values()):
        reason = "cross_host_mismatch"
    else:
        reason = None
    for s in sides.values():
        s.pop("outcomes")
    short = mode == SHORT_MODE
    if reason is None:
        on_stop = None
    elif short:                  # R1-G5-AUDIT-TWO-CARDS: the gate is the audit host; nothing is re-measured
        on_stop = (f"STOP ({reason}): {node}'s G.5 audits stay on TASL-2 ({SHORT_RULE}); its TASL-2 G.1b noise floor "
                   "is not re-measured; whether the node stays in G.5 is the note's rule (decision XC3-FAIL)")
    elif reason == "incomplete":
        on_stop = f"STOP: {node}'s default part is incomplete on a host; the author decides"
    elif reason == "cross_host_mismatch":
        on_stop = (f"STOP: {node}'s G.1b is re-measured on TASL-2 (R1-T1-TASL-ENV); the re-measure spec and its "
                   "assembly are decision XC-REMEASURE")
    else:
        on_stop = (f"STOP: {node} is not deterministic on {reason.split(':', 1)[1]}; not a cross-host result, and a "
                   "re-measure would be a second draw; the author decides")
    return {"schema": VERDICT_SCHEMA, "label": G.ENGINEERING_ONLY, "node": node,
            "rule": SHORT_RULE if short else "R1-T1-TASL-ENV",
            "mode": mode, "crosscheck_run_id": xc["run_id"], "g1b_run_id": g1b["run_id"],
            "g1b_spec_sha256": xc["g1b_spec"]["sha256"], "harness_commit": pin, "configs": configs,
            "verdict": "PASS" if reason is None else "STOP", "reason": reason, "complete": complete,
            "sides": sides, "rows": per, "on_stop": on_stop}


def _verdict_core(v: dict) -> dict:
    """The parts of a verdict that do not depend on where the sealed directories were read (in JSON form, as committed)."""
    return json.loads(json.dumps({**{k: v.get(k) for k in ("schema", "node", "mode", "crosscheck_run_id", "g1b_run_id", "g1b_spec_sha256",
                                     "harness_commit", "configs", "verdict", "reason", "complete", "rows")},
            "sides": {h: {k: x for k, x in (s or {}).items() if k != "sealed"}
                      for h, s in (v.get("sides") or {}).items()}}, sort_keys=True, default=list))


def _committed_verdicts(paths: list[Path], read_main) -> dict[str, tuple[str, bytes, dict]]:
    """{node: (repository path, bytes, verdict)} of verdict files committed byte-identically on origin/main."""
    out = {}
    for path in map(Path, paths):
        rel = path.as_posix()
        if path.is_absolute() or ".." in path.parts or not rel.startswith("docs/r1/reports/"):
            raise Stop(f"STOP: verdict {rel} must be a repository path under docs/r1/reports/")
        raw = (G.REPO_ROOT / rel).read_bytes()
        if read_main(rel) != raw:
            raise Stop(f"STOP: verdict {rel} is not committed byte-identically on origin/main")
        v = json.loads(raw)
        if v.get("schema") != VERDICT_SCHEMA or v.get("node") in out:
            raise Stop(f"STOP: {rel} is not a verdict, or a second verdict for {v.get('node')}")
        out[v["node"]] = (rel, raw, v)
    return out


def check_xc_note(note_path: Path, xc_path: Path, xc: dict, g1b: dict, *, on_main, draft: bool = False,
                  read_main=G._read_main) -> dict:
    """The author-signed cross-check note (module docstring): on main, approved, ENGINEERING_ONLY, binding the paper
    commit, the cross-check spec and the signed G.1b spec, the run id and the harness pin, P1-P4 PASS.

    ``draft=True`` (before signature): the unsigned note (any path, e.g. the draft under ``docs/r1/proposals/``; the
    path and name are checked in strict mode), exactly one line ``approved: false``, not read from main;
    every other check runs, except that P4 (the review of the unit, which exists only after review) may read
    ``PENDING — …`` and is the only field that may hold ``<FILL``."""
    note_path = Path(note_path)
    short = is_short(xc)
    name_rx, name = (XC_SHORT_NOTE_NAME, "g1b_xc_short_t1_tasl") if short else (XC_NOTE_NAME, "g1b_xc_t1_tasl")
    if not draft and (note_path.parent.as_posix().split("/")[-3:] != G.NOTE_DIR.split("/")
                      or not name_rx.fullmatch(note_path.name)):          # a draft lives under docs/r1/proposals/
        raise Stop(f"STOP: the note must be {G.NOTE_DIR}/{name}_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    if draft:
        if [ln for ln in raw.decode().splitlines() if ln.startswith("approved:")] != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned note (exactly one line 'approved: false')")
    elif not on_main(f"{G.NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note is not committed byte-identically on origin/main")
    fields = {}
    for line in raw.decode().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate note field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    pending_ok = {"P4"} if draft and fields.get("P4", "").upper().startswith(("PENDING — ", "PENDING - ")) else set()
    unfilled = sorted(k for k, v in fields.items() if "<FILL" in v and k not in pending_ok)
    if unfilled:
        raise Stop(f"STOP: note fields not filled: {unfilled}")
    want = {"approved": "false" if draft else "true", "label": G.ENGINEERING_ONLY, "labels_read": "none",
            "paper_commit": xc["paper"]["commit"], "xc_spec_sha256": _sha(xc_path),
            "g1b_spec_sha256": xc["g1b_spec"]["sha256"], "run_id": xc["run_id"],
            "harness_commit": g1b["harness"]["commit"]}
    for key, value in want.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    cites = {"P1": SHORT_RULE if short else "R1-T1-TASL-ENV",
             "P2": g1b["hosts"]["TASL-2"]["isolation_host_check"]["record"],
             "P3": g1b["hosts"]["TASL-7"]["isolation_host_check"]["record"], "P4": "docs/r1/reviews/"}
    for key, cite in cites.items():
        if key in pending_ok:
            continue
        if not fields.get(key, "").upper().startswith(("PASS — ", "PASS - ")) or cite not in fields[key]:
            raise Stop(f"STOP: {key} must read PASS citing {cite}")
    if short:
        chosen = short_decisions(fields, xc)
        if not draft:                       # the PLAN row of decision XC3-FAIL, once on main, must agree
            row = xc3_fail_row_option(read_main)
            if row is not None and row != chosen["xc3_fail"]:
                raise Stop(f"STOP: note field xc3_fail is {chosen['xc3_fail']}, but the PLAN row {XC3_FAIL_ROW} on main "
                           f"says xc3_fail: {row}")
    return fields


def xc3_fail_row_option(read_main=G._read_main) -> str | None:
    """The option (A or B) the author's PLAN row ``R1-XC3-FAIL-READING`` on published main records, from its sentence
    "The xc3 note carries xc3_fail: A|B."; None while the row is not on main. A row present twice, or without exactly
    one such sentence, refuses."""
    plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
    lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(XC3_FAIL_ROW)} \|", ln)]
    if not lines:
        return None
    hits = XC3_FAIL_ROW_SENTENCE.findall(lines[0]) if len(lines) == 1 else []
    if len(lines) != 1 or len(hits) != 1:
        raise Stop(f"STOP: the PLAN row {XC3_FAIL_ROW} on main must appear once and say once 'The xc3 note carries "
                   "xc3_fail: A.' or '… B.'")
    return hits[0]


def short_decisions(fields: dict, xc: dict) -> dict:
    """A stable helper (also for the G.5 audit-host reader, with ``check_xc_note``). The author's choices in a short note (``SHORT_DECISIONS`` and ``skip_nodes``), each bound to its allowed
    values: ``xc3_fail`` A or B, ``xc3_cap`` R1-G1B-CAP or G5-CAP, ``skip_nodes`` ``none`` or a comma-separated list
    of the spec's nodes (not all of them). Returns them, ``skip_nodes`` as a list."""
    out = {}
    for key, allowed in SHORT_DECISIONS.items():
        if fields.get(key) not in allowed:
            raise Stop(f"STOP: note field {key} must be one of {list(allowed)} (the author's choice; the first is the "
                       "recommended one)")
        out[key] = fields[key]
    raw = fields.get("skip_nodes")
    skip = [] if raw == "none" else [n.strip() for n in str(raw or "").split(",")]
    if raw is None or (raw != "none" and (not all(skip) or len(set(skip)) != len(skip) or set(skip) - set(xc["nodes"])
                                          or set(skip) == set(xc["nodes"]))):
        raise Stop(f"STOP: note field skip_nodes must be 'none' or a comma-separated list of some of {xc['nodes']}")
    out["skip_nodes"] = skip
    return out


def short_consumed_gpu_hours(xc: dict, g1b: dict) -> dict:
    """The GPU lease hours the short run's TASL-7 GPU jobs have used so far: every attempt of a GPU node under
    ``<runs_root>/<run id>-TASL-7/<node>/attempt-N/``, from its job record's start and finish (an infrastructure
    attempt counts too: it held the lease). An attempt without a job record refuses (the author decides)."""
    import calendar
    import time as _time
    root = Path(g1b["hosts"]["TASL-7"]["runs_root"]) / f"{xc['run_id']}-TASL-7"
    per, total = {}, 0.0
    for node in xc["nodes"]:
        if G.node_entry(g1b, node)["device"] != "gpu":
            continue
        for _, d in G.attempts(root / node):
            rec_path = d / "job_record.json"
            if not rec_path.is_file():
                raise Stop(f"STOP: {d} has no job record; its lease time is unknown (the author decides)")
            rec = json.loads(rec_path.read_text())
            fmt = "%Y-%m-%dT%H:%M:%SZ"
            try:
                hours = (calendar.timegm(_time.strptime(rec["finished_utc"], fmt))
                         - calendar.timegm(_time.strptime(rec["started_utc"], fmt))) / 3600.0
            except (KeyError, ValueError, TypeError):
                raise Stop(f"STOP: {rec_path} has no readable start and finish (the author decides)") from None
            if hours < 0:
                raise Stop(f"STOP: {rec_path} finishes before it starts; its lease time is unknown (the author decides)")
            per[f"{node}/{d.name}"] = round(hours, 4)
            total += hours
    return {"attempts": per, "gpu_hours": round(total, 4)}


def short_cap_gate(xc: dict, g1b: dict, node: str) -> dict:
    """The stop rule between jobs: a GPU job starts only if the GPU-h used so far plus its own projected hours stay
    within ``caps.max_gpu_hours``; otherwise author STOP (the CPU-only node uses no GPU-h)."""
    used = short_consumed_gpu_hours(xc, g1b)
    if G.node_entry(g1b, node)["device"] != "gpu":
        return used | {"next_hours": 0.0, "cap_gpu_hours": xc["caps"]["max_gpu_hours"]}
    nxt = short_projection(xc, g1b)["estimate"]["per_node"][node]["hours"]
    cap = float(xc["caps"]["max_gpu_hours"])
    if used["gpu_hours"] + nxt > cap:
        raise Stop(f"STOP: {node}: {used['gpu_hours']} GPU-h used plus its projected {nxt} GPU-h exceeds the cap "
                   f"{cap} GPU-h (caps.max_gpu_hours): author STOP before the job")
    return used | {"next_hours": nxt, "cap_gpu_hours": cap}


def launch_rows(xc: dict) -> tuple[str, ...]:
    """The PLAN rows ``verify_launch_tasl`` requires on published main for this cross-check spec."""
    rows = G.PLAN_ROWS + ("R1-T1-TASL-ENV", "R1-G1B-TASL-DECISIONS")
    return rows + (SHORT_RULE,) if is_short(xc) else rows


def _require_xc_kind(xc: dict, what: str) -> None:
    if is_short(xc):
        raise Stop(f"STOP: {what} is for the TASL-7 nodes' cross-check (R1-T1-TASL-ENV), not a short spec")


def launch_xc(xc_path: Path, note_path: Path, node: str, host: str, *, enable: bool, on_main=G._note_on_main,
              read_main=G._read_main, launch_binding=None, runner=None) -> dict:
    xc, g1b, _ = load_xc(xc_path)
    derived_spec(g1b, xc, node, host)                 # validates before anything else
    fields = check_xc_note(note_path, xc_path, xc, g1b, on_main=on_main, read_main=read_main)
    gate = None
    if is_short(xc):
        if node in short_decisions(fields, xc)["skip_nodes"]:
            raise Stop(f"STOP: the signed note removes {node} from this run (skip_nodes)")
        gate = short_cap_gate(xc, g1b, node)
    if not enable or os.environ.get(G.ENABLE_ENV) != "1":
        raise Stop(f"STOP: real cross-check runs are disabled (needs --enable AND {G.ENABLE_ENV}=1)")
    for h in G.HOSTS:
        G.check_host_record(g1b["hosts"][h], g1b["harness"]["commit"], read_main)
    rows = launch_rows(xc)
    binding = (launch_binding or (lambda repo, s, r: G.verify_launch_tasl(repo, s, r, spec_path=Path(xc_path))))(
        G.REPO_ROOT, {"paper": xc["paper"]}, rows)
    out = (runner or run_xc)(xc_path, node, host) | {"launch": binding}
    return out | {"cap_gate": gate} if gate is not None else out


XC_NOTE_CITE = re.compile(r"docs/r1/authorizations/g1b_xc_t1_tasl_\d{8}\.md")


def check_note2(note_path: Path, xc_path: Path, verdict_paths: list[Path], *, draft: bool = False,
                on_main=G._note_on_main, read_main=G._read_main) -> dict:
    """The second G.1b note (the TASL-7 nodes, R1-G1B-TASL-DECISIONS XC A): ``g1b_tasl.check_note`` against the signed
    spec, no unfilled field, and P7 PASS citing R1-T1-TASL-ENV, the signed cross-check note on origin/main and, for every
    cross-check node, a step-1 (``xc``) PASS verdict committed on origin/main by path and sha256, with no ``<…>`` left.

    Two recorded steps: ``draft=True`` before signature (the note is not yet on main and reads ``approved: false``;
    every other check runs on a copy reading ``approved: true``), then strict mode after publication and before any
    TASL-7 node launches."""
    xc, g1b, g1b_path = load_xc(xc_path)
    _require_xc_kind(xc, "check-note2")
    note_path = Path(note_path)
    if draft:
        raw = note_path.read_text()
        lines = [ln for ln in raw.splitlines() if ln.startswith("approved:")]
        if lines != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned note (exactly one line 'approved: false')")
        with tempfile.TemporaryDirectory(prefix="g1b_note2_") as tmp:
            copy_path = Path(tmp) / G.NOTE_DIR / note_path.name
            copy_path.parent.mkdir(parents=True)
            copy_path.write_text("".join("approved: true\n" if ln.rstrip("\r\n") == "approved: false" else ln
                                         for ln in raw.splitlines(keepends=True)))
            fields = G.check_note(copy_path, g1b_path, g1b["paper"]["commit"], on_main=lambda rel, b: True, spec=g1b)
    else:
        fields = G.check_note(note_path, g1b_path, g1b["paper"]["commit"], on_main=on_main, spec=g1b)
    unfilled = sorted(k for k, v in fields.items() if "<FILL" in v)
    if unfilled:
        raise Stop(f"STOP: note fields not filled: {unfilled}")
    p7 = fields.get("P7", "")
    if not p7.upper().startswith(("PASS — ", "PASS - ")) or "R1-T1-TASL-ENV" not in p7:
        raise Stop("STOP: P7 must read PASS citing R1-T1-TASL-ENV")
    if re.search(r"<[^>]*>", p7):
        raise Stop("STOP: P7 still holds a <...> template placeholder")
    xc_notes = XC_NOTE_CITE.findall(p7)
    xc_raw = read_main(xc_notes[0]) if len(set(xc_notes)) == 1 else None
    if not xc_raw:
        raise Stop("STOP: P7 must cite the signed cross-check note docs/r1/authorizations/g1b_xc_t1_tasl_<date>.md "
                   "on origin/main")
    with tempfile.TemporaryDirectory(prefix="g1b_xcnote_") as tmp:      # its fields, as check_xc_note reads them
        xc_copy = Path(tmp) / xc_notes[0]
        xc_copy.parent.mkdir(parents=True)
        xc_copy.write_bytes(xc_raw)
        check_xc_note(xc_copy, xc_path, xc, g1b, on_main=lambda rel, b: b == xc_raw)
    verdicts = _committed_verdicts(verdict_paths, read_main)
    if sorted(verdicts) != sorted(xc["nodes"]):
        raise Stop(f"STOP: step-1 verdicts for {sorted(verdicts)}, expected {sorted(xc['nodes'])}")
    for node, (rel, raw, v) in sorted(verdicts.items()):
        want = expected_sides(xc, g1b, node, "xc")
        got = {h: ((v.get("sides") or {}).get(h, {}).get("run_id"), (v.get("sides") or {}).get(h, {}).get("spec_sha256"))
               for h in CROSS_HOSTS}
        if v.get("mode") != "xc" or v.get("verdict") != "PASS" or got != want or \
                v.get("g1b_spec_sha256") != xc["g1b_spec"]["sha256"]:
            raise Stop(f"STOP: {rel} is not a step-1 PASS of {node} for this cross-check run")
        if rel not in p7 or hashlib.sha256(raw).hexdigest() not in p7:
            raise Stop(f"STOP: P7 must cite {rel} with its sha256")
    return {"note": str(note_path), "mode": "draft" if draft else "strict", "p7": "PASS", "xc_note": xc_notes[0],
            "verdicts": {n: r for n, (r, _, _) in sorted(verdicts.items())}}


def assemble_gated(xc_path: Path, dest: Path, sealed_dirs: list[Path], verdict_paths: list[Path],
                   xc_tasl2: list[Path], *, read_main=G._read_main) -> dict:
    """``g1b_tasl.assemble`` behind the R1-T1-TASL-ENV gate (XC A: the cross-check PASS is a required input to
    assembly for the TASL-7 nodes). For each TASL-7 node: its committed step-2 (``preassembly``) verdict is PASS, and the
    comparison recomputed now from the G.1b TASL-7 attempt being assembled and the cross-check TASL-2 attempt gives the
    same verdict (the same sides by job-record sha256, run id and spec sha256, and the same rows). Then the signed spec's
    assembly, unchanged."""
    xc, g1b, g1b_path = load_xc(xc_path)
    _require_xc_kind(xc, "assemble")
    by_node = {}
    for d in map(Path, sealed_dirs):
        node = json.loads((d / "job_record.json").read_text()).get("node")
        if node in by_node:
            raise Stop(f"STOP: two sealed attempts given for {node}")
        by_node[node] = d
    t2 = {}
    for d in map(Path, xc_tasl2):
        node = json.loads((d / "job_record.json").read_text()).get("node")
        if node in t2:
            raise Stop(f"STOP: two cross-check TASL-2 attempts given for {node}")
        t2[node] = d
    verdicts = _committed_verdicts(verdict_paths, read_main)
    gate = {}
    for node in xc["nodes"]:
        if node not in by_node or node not in t2 or node not in verdicts:
            raise Stop(f"STOP: {node} needs its G.1b TASL-7 attempt, its cross-check TASL-2 attempt and its verdict")
        rel, _, committed = verdicts[node]
        if committed.get("mode") != "preassembly" or committed.get("verdict") != "PASS":
            raise Stop(f"STOP: {rel} is not a step-2 PASS for {node} (R1-T1-TASL-ENV); no assembly")
        now = compare(by_node[node], t2[node], node, mode="preassembly", xc_path=xc_path)
        if _verdict_core(now) != _verdict_core(committed):
            raise Stop(f"STOP: {rel} is not the comparison of the attempts given for {node}")
        gate[node] = {"verdict": rel, "tasl7_job_record_sha256": now["sides"]["TASL-7"]["job_record_sha256"]}
    extra = sorted(set(verdicts) - set(xc["nodes"])) + sorted(set(t2) - set(xc["nodes"]))
    if extra:
        raise Stop(f"STOP: verdicts or cross-check attempts for non-TASL-7 nodes {extra}")
    out = G.assemble(list(map(Path, sealed_dirs)), g1b, Path(dest), xc["g1b_spec"]["sha256"])
    dest = Path(dest)
    gate_record = {"schema": GATE_SCHEMA, "rule": "R1-T1-TASL-ENV", "nodes": gate,
                   "g1b_spec_sha256": xc["g1b_spec"]["sha256"], "crosscheck_run_id": xc["run_id"],
                   "assembly_json_sha256": _sha(dest / "ASSEMBLY.json"), "runs_jsonl_sha256": _sha(dest / "runs.jsonl")}
    (Path(dest) / "crosscheck_gate.json").write_text(json.dumps(gate_record, indent=1, sort_keys=True) + "\n")
    return {**out, "crosscheck_gate": gate_record} if isinstance(out, dict) else {"crosscheck_gate": gate_record}


def summarise_gated(xc_path: Path, run_dir: Path, paper_root: Path) -> dict:
    """``g1b_tasl.summarise`` only for a run assembled by ``assemble_gated``: its ``crosscheck_gate.json`` names every
    TASL-7 node and binds this run directory's ``ASSEMBLY.json`` and ``runs.jsonl`` as they are now."""
    xc, g1b, _ = load_xc(xc_path)
    _require_xc_kind(xc, "summarise")
    run_dir = Path(run_dir)
    gate_path = run_dir / "crosscheck_gate.json"
    if not gate_path.is_file():
        raise Stop(f"STOP: {run_dir} was not assembled through the cross-check gate (no crosscheck_gate.json)")
    gate = json.loads(gate_path.read_text())
    ok = (gate.get("schema") == GATE_SCHEMA and sorted(gate.get("nodes") or {}) == sorted(xc["nodes"])
          and gate.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"] and gate.get("crosscheck_run_id") == xc["run_id"]
          and gate.get("assembly_json_sha256") == _sha(run_dir / "ASSEMBLY.json")
          and gate.get("runs_jsonl_sha256") == _sha(run_dir / "runs.jsonl"))
    if not ok:
        raise Stop(f"STOP: {gate_path} does not bind this assembly and the three TASL-7 nodes")
    return G.summarise(run_dir, g1b, Path(paper_root))


def _list_main_reports() -> list[str] | None:
    res = subprocess.run(["git", "-C", str(G.REPO_ROOT), "ls-tree", "-r", "--name-only", "origin/main", "--",
                          SHORT_VERDICT_DIR], capture_output=True, text=True)
    return res.stdout.splitlines() if res.returncode == 0 else None


def short_verdict_status(xc_path: Path, *, read_main=G._read_main, repo: Path | None = None,
                         list_main=_list_main_reports) -> dict:
    """Each short cross-check node's committed verdict on ``origin/main`` at the path the spec binds:
    ``{node: {"path", "status": "PASS" | "STOP" | "PENDING", "sha256", "reason", "tasl7_audits": bool}}``. PENDING: no
    file at the path yet. A file at the path that is not this spec's short verdict of that node (schema, mode, run id,
    G.1b spec, harness pin, the sides' run ids and spec sha256s, the declared G.1b TASL-2 job record) is refused
    (Stop), not read as a STOP; so is a PASS that is not one in every part (``complete`` true, every row
    ``identical``, both sides deterministic). It refuses when ``origin/main`` does not resolve (``docs/r1/PLAN.md``
    unreadable there), rather than report PENDING, and when ``docs/r1/reports/`` on main holds a file named
    ``G1B_XC3_SHORT_VERDICT_*`` other than the bound paths (a capture keeps its copy as ``captured_verdict_<node>.json``).
    Only PASS allows the node's G.5 audits on TASL-7 (R1-G5-AUDIT-TWO-CARDS)."""
    xc, g1b, _ = load_xc(xc_path, repo)
    if not is_short(xc):
        raise Stop("STOP: verdict-status reads a short cross-check spec's verdicts")
    if read_main("docs/r1/PLAN.md") is None:
        raise Stop("STOP: origin/main does not resolve here (fetch it); no verdict status without it")
    listed = list_main()
    if listed is None:
        raise Stop("STOP: cannot list docs/r1/reports/ on origin/main")
    stray = sorted(p for p in listed if Path(p).name.startswith(SHORT_VERDICT_PREFIX)
                   and p not in set(xc["verdicts"].values()))
    if stray:                # a capture's copy must be named captured_verdict_<node>.json (the note's publication line)
        raise Stop(f"STOP: files named {SHORT_VERDICT_PREFIX}* on origin/main other than the bound verdict paths: "
                   f"{stray[:4]}")
    out = {}
    for node in xc["nodes"]:
        rel = xc["verdicts"][node]
        raw = read_main(rel)
        if raw is None:
            out[node] = {"path": rel, "status": "PENDING", "sha256": None, "reason": None, "tasl7_audits": False}
            continue
        try:
            v = json.loads(raw)
        except ValueError:
            v = {}
        sides = v.get("sides") or {}
        got = {h: ((sides.get(h) or {}).get("run_id"), (sides.get(h) or {}).get("spec_sha256")) for h in CROSS_HOSTS}
        ok = (v.get("schema") == VERDICT_SCHEMA and v.get("node") == node and v.get("mode") == SHORT_MODE
              and v.get("crosscheck_run_id") == xc["run_id"] and v.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"]
              and v.get("harness_commit") == g1b["harness"]["commit"]
              and got == expected_sides(xc, g1b, node, SHORT_MODE)
              and (sides.get("TASL-2") or {}).get("job_record_sha256")
              == xc["g1b_tasl2_attempts"][node]["job_record_sha256"]
              and v.get("verdict") in ("PASS", "STOP") and (v.get("verdict") == "PASS") == (v.get("reason") is None))
        if ok and v["verdict"] == "PASS":         # a PASS must be one in every part, as compare writes it
            rows = v.get("rows") or {}
            ok = (v.get("complete") is True and bool(rows)
                  and all(isinstance(r, dict) and r.get("identical") is True for r in rows.values())
                  and all((sides.get(h) or {}).get("deterministic") is True for h in CROSS_HOSTS))
        if not ok:
            raise Stop(f"STOP: {rel} on origin/main is not the short cross-check verdict of {node} for run {xc['run_id']}")
        out[node] = {"path": rel, "status": v["verdict"], "sha256": hashlib.sha256(raw).hexdigest(),
                     "reason": v.get("reason"), "tasl7_audits": v["verdict"] == "PASS"}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("xc_spec")
    r = sub.add_parser("run-node")
    r.add_argument("xc_spec")
    r.add_argument("--node", required=True)
    r.add_argument("--host", required=True, choices=CROSS_HOSTS)
    r.add_argument("--note", required=True)
    r.add_argument("--enable", action="store_true")
    d = sub.add_parser("derived")
    d.add_argument("xc_spec")
    d.add_argument("--node", required=True)
    d.add_argument("--host", required=True, choices=CROSS_HOSTS)
    for name in ("cpus", "logdir"):               # for t1_tasl_node.sh xc
        q = sub.add_parser(name)
        q.add_argument("xc_spec")
        q.add_argument("--node", required=True)
        q.add_argument("--host", required=True, choices=CROSS_HOSTS)
    c = sub.add_parser("compare")
    c.add_argument("xc_spec")
    c.add_argument("--mode", required=True, choices=MODES)
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--node", required=True)
    c.add_argument("--out", required=True)
    n2 = sub.add_parser("check-note2")
    n2.add_argument("xc_spec")
    n2.add_argument("--note", required=True)
    n2.add_argument("--verdict", action="append", required=True, help="repository path of a step-1 verdict (x3)")
    n2.add_argument("--draft", action="store_true", help="before signature: the unsigned note, not yet on main")
    sm = sub.add_parser("summarise")
    sm.add_argument("xc_spec")
    sm.add_argument("run_dir")
    sm.add_argument("--paper-root", required=True)
    asm = sub.add_parser("assemble")
    asm.add_argument("xc_spec")
    asm.add_argument("dest")
    asm.add_argument("--sealed", action="append", required=True, help="one sealed G.1b attempt per node (x7)")
    asm.add_argument("--verdict", action="append", required=True, help="repository path of a step-2 verdict (x3)")
    asm.add_argument("--xc-tasl2", action="append", required=True, help="the cross-check TASL-2 attempt (x3)")
    xn = sub.add_parser("check-xc-note")
    xn.add_argument("xc_spec")
    xn.add_argument("--note", required=True)
    xn.add_argument("--draft", action="store_true", help="before signature: the unsigned note, not read from main")
    vs = sub.add_parser("verdict-status")
    vs.add_argument("xc_spec")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            for node in xc["nodes"]:
                for host in xc["hosts"]:
                    derived_spec(g1b, xc, node, host)
            res = {"ok": True, "run_id": xc["run_id"], "nodes": xc["nodes"]}
            if is_short(xc):
                res.update(kind=SHORT_MODE, hosts=xc["hosts"], projection=short_projection(xc, g1b))
            print(json.dumps(res, indent=1))
        elif a.cmd == "derived":
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            print(str(write_derived(derived_spec(g1b, xc, a.node, a.host), a.node)))
        elif a.cmd in ("cpus", "logdir"):
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            spec = derived_spec(g1b, xc, a.node, a.host)
            print(G.node_cpus(spec, G.node_entry(spec, a.node)) if a.cmd == "cpus" else
                  str(Path(spec["hosts"][a.host]["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "check-note2":
            print(json.dumps(check_note2(Path(a.note), Path(a.xc_spec), [Path(v) for v in a.verdict], draft=a.draft),
                             indent=1))
        elif a.cmd == "summarise":
            print(json.dumps(summarise_gated(Path(a.xc_spec), Path(a.run_dir), Path(a.paper_root)), indent=1,
                             default=str))
        elif a.cmd == "assemble":
            out = assemble_gated(Path(a.xc_spec), Path(a.dest), [Path(x) for x in a.sealed],
                                 [Path(v) for v in a.verdict], [Path(x) for x in a.xc_tasl2])
            print(json.dumps(out, indent=1, default=str))
        elif a.cmd == "check-xc-note":
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            fields = check_xc_note(Path(a.note), Path(a.xc_spec), xc, g1b, on_main=G._note_on_main, draft=a.draft)
            print(json.dumps({"ok": True, "mode": "draft" if a.draft else "strict", "run_id": fields["run_id"],
                              "paper_commit": fields["paper_commit"], "xc_spec_sha256": fields["xc_spec_sha256"]},
                             indent=1))
        elif a.cmd == "verdict-status":
            print(json.dumps(short_verdict_status(Path(a.xc_spec)), indent=1))
        elif a.cmd == "run-node":
            rec = launch_xc(Path(a.xc_spec), Path(a.note), a.node, a.host, enable=a.enable)
            print(json.dumps({"ok": True, "node": a.node, "host": a.host, "runs": rec.get("runs")}, indent=1))
        else:
            out = Path(a.out)
            if out.exists():
                raise Stop(f"STOP: {out} exists (no overwrite)")
            verdict = compare(Path(a.a), Path(a.b), a.node, mode=a.mode, xc_path=Path(a.xc_spec))
            out.write_text(json.dumps(verdict, indent=1, sort_keys=True, default=list) + "\n")
            print(json.dumps({"node": a.node, "verdict": verdict["verdict"]}, indent=1))
            return 0 if verdict["verdict"] == "PASS" else 3
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
