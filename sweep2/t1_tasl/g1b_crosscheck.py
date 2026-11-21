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
   sha256 in the second G.1b note's P7; ``check-note2`` checks that before signature;
2. before assembly, ``preassembly`` mode: the node's G.1b TASL-7 attempt against the cross-check's TASL-2 attempt (the
   row's literal comparison). ``assemble`` (``assemble_gated``) is the assembly for the run with TASL-7 nodes: for each
   it recomputes this comparison from the attempts given, requires it to equal the committed step-2 PASS verdict, and
   only then runs ``g1b_tasl.assemble`` with the signed spec, unchanged.

**Launch.** A signed note ``docs/r1/authorizations/g1b_xc_t1_tasl_<YYYYMMDD>.md`` on published ``main`` is required
(``check_xc_note``; no unfilled field), as are both keys (``--enable`` and ``G1B_TASL_ENABLE_REAL=1``) and both hosts'
host-check records on ``main``. The launch binding is ``verify_launch_tasl`` with the cross-check spec: its
``paper.commit`` is a code-equal ancestor of the published checkout.
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
MODES = ("xc", "preassembly")
SEALED_FILES = {"out.tar", "job_record.json"}
_ACTIVE = {"run": False}


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_xc(xc_path: Path, repo: Path | None = None) -> tuple[dict, dict, Path]:
    """(cross-check spec, signed G.1b spec, its path), validated."""
    repo = Path(repo or G.REPO_ROOT)
    xc = json.loads(Path(xc_path).read_text())
    if xc.get("schema") != XC_SCHEMA or xc.get("label") != G.ENGINEERING_ONLY:
        raise Stop(f"STOP: the cross-check spec must be {XC_SCHEMA}, ENGINEERING_ONLY")
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
    tasl7 = sorted(n["node"] for n in g1b["nodes"] if n["host"] == "TASL-7")
    if sorted(xc.get("nodes") or []) != tasl7:
        raise Stop(f"STOP: nodes must be exactly the G.1b TASL-7 nodes {tasl7}")
    if list(xc.get("hosts") or []) != list(CROSS_HOSTS):
        raise Stop(f"STOP: hosts must be {list(CROSS_HOSTS)}")
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
    if node not in xc["nodes"] or host not in CROSS_HOSTS:
        raise Stop(f"STOP: {node} on {host} is not a cross-check job")
    spec = copy.deepcopy(g1b)
    spec["run_id"] = f"{xc['run_id']}-{host}"
    spec["paper"] = dict(xc["paper"])
    for env, py in (xc.get("env_python_additions") or {}).get(host, {}).items():
        spec["hosts"][host]["env_python"][env] = py
    entry = G.node_entry(spec, node)
    entry["host"] = host
    if entry["env"] not in spec["hosts"][host]["env_python"]:
        raise Stop(f"STOP: {node} needs {entry['env']} on {host}; declare it in env_python_additions")
    spec["crosscheck"] = {"node": node, "host": host, "crosscheck_run_id": xc["run_id"],
                          "g1b_spec_sha256": xc["g1b_spec"]["sha256"]}
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
    if reason is None:
        on_stop = None
    elif reason == "incomplete":
        on_stop = f"STOP: {node}'s default part is incomplete on a host; the author decides"
    elif reason == "cross_host_mismatch":
        on_stop = (f"STOP: {node}'s G.1b is re-measured on TASL-2 (R1-T1-TASL-ENV); the re-measure spec and its "
                   "assembly are decision XC-REMEASURE")
    else:
        on_stop = (f"STOP: {node} is not deterministic on {reason.split(':', 1)[1]}; not a cross-host result, and a "
                   "re-measure would be a second draw; the author decides")
    return {"schema": VERDICT_SCHEMA, "label": G.ENGINEERING_ONLY, "node": node, "rule": "R1-T1-TASL-ENV",
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


def check_xc_note(note_path: Path, xc_path: Path, xc: dict, g1b: dict, *, on_main) -> dict:
    """The author-signed cross-check note (module docstring): on main, approved, ENGINEERING_ONLY, binding the paper
    commit, the cross-check spec and the signed G.1b spec, the run id and the harness pin, P1-P4 PASS."""
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != G.NOTE_DIR.split("/") or not XC_NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the note must be {G.NOTE_DIR}/g1b_xc_t1_tasl_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    if not on_main(f"{G.NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note is not committed byte-identically on origin/main")
    fields = {}
    for line in raw.decode().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate note field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    unfilled = sorted(k for k, v in fields.items() if "<FILL" in v)
    if unfilled:
        raise Stop(f"STOP: note fields not filled: {unfilled}")
    want = {"approved": "true", "label": G.ENGINEERING_ONLY, "labels_read": "none",
            "paper_commit": xc["paper"]["commit"], "xc_spec_sha256": _sha(xc_path),
            "g1b_spec_sha256": xc["g1b_spec"]["sha256"], "run_id": xc["run_id"],
            "harness_commit": g1b["harness"]["commit"]}
    for key, value in want.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    cites = {"P1": "R1-T1-TASL-ENV", "P2": g1b["hosts"]["TASL-2"]["isolation_host_check"]["record"],
             "P3": g1b["hosts"]["TASL-7"]["isolation_host_check"]["record"], "P4": "docs/r1/reviews/"}
    for key, cite in cites.items():
        if not fields.get(key, "").upper().startswith(("PASS — ", "PASS - ")) or cite not in fields[key]:
            raise Stop(f"STOP: {key} must read PASS citing {cite}")
    return fields


def launch_xc(xc_path: Path, note_path: Path, node: str, host: str, *, enable: bool, on_main=G._note_on_main,
              read_main=G._read_main, launch_binding=None, runner=None) -> dict:
    xc, g1b, _ = load_xc(xc_path)
    derived_spec(g1b, xc, node, host)                 # validates before anything else
    check_xc_note(note_path, xc_path, xc, g1b, on_main=on_main)
    if not enable or os.environ.get(G.ENABLE_ENV) != "1":
        raise Stop(f"STOP: real cross-check runs are disabled (needs --enable AND {G.ENABLE_ENV}=1)")
    for h in G.HOSTS:
        G.check_host_record(g1b["hosts"][h], g1b["harness"]["commit"], read_main)
    rows = G.PLAN_ROWS + ("R1-T1-TASL-ENV", "R1-G1B-TASL-DECISIONS")
    binding = (launch_binding or (lambda repo, s, r: G.verify_launch_tasl(repo, s, r, spec_path=Path(xc_path))))(
        G.REPO_ROOT, {"paper": xc["paper"]}, rows)
    return (runner or run_xc)(xc_path, node, host) | {"launch": binding}


def check_note2(note_path: Path, xc_path: Path, verdict_paths: list[Path], *, on_main=G._note_on_main,
                read_main=G._read_main) -> dict:
    """The second G.1b note (the TASL-7 nodes, R1-G1B-TASL-DECISIONS XC A) before signature and before any TASL-7 node
    launches: ``g1b_tasl.check_note`` against the signed spec, no unfilled field, and P7 PASS citing R1-T1-TASL-ENV and,
    for every cross-check node, a step-1 (``xc``) PASS verdict committed on origin/main by path and sha256."""
    xc, g1b, g1b_path = load_xc(xc_path)
    fields = G.check_note(note_path, g1b_path, g1b["paper"]["commit"], on_main=on_main, spec=g1b)
    unfilled = sorted(k for k, v in fields.items() if "<FILL" in v)
    if unfilled:
        raise Stop(f"STOP: note fields not filled: {unfilled}")
    p7 = fields.get("P7", "")
    if not p7.upper().startswith(("PASS — ", "PASS - ")) or "R1-T1-TASL-ENV" not in p7:
        raise Stop("STOP: P7 must read PASS citing R1-T1-TASL-ENV")
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
    return {"note": str(note_path), "p7": "PASS", "verdicts": {n: r for n, (r, _, _) in sorted(verdicts.items())}}


def assemble_gated(xc_path: Path, dest: Path, sealed_dirs: list[Path], verdict_paths: list[Path],
                   xc_tasl2: list[Path], *, read_main=G._read_main) -> dict:
    """``g1b_tasl.assemble`` behind the R1-T1-TASL-ENV gate (XC A: the cross-check PASS is a required input to
    assembly for the TASL-7 nodes). For each TASL-7 node: its committed step-2 (``preassembly``) verdict is PASS, and the
    comparison recomputed now from the G.1b TASL-7 attempt being assembled and the cross-check TASL-2 attempt gives the
    same verdict (the same sides by job-record sha256, run id and spec sha256, and the same rows). Then the signed spec's
    assembly, unchanged."""
    xc, g1b, g1b_path = load_xc(xc_path)
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
    gate_record = {"schema": "g1b_tasl_crosscheck_gate/1", "rule": "R1-T1-TASL-ENV", "nodes": gate}
    (Path(dest) / "crosscheck_gate.json").write_text(json.dumps(gate_record, indent=1, sort_keys=True) + "\n")
    return {**out, "crosscheck_gate": gate_record} if isinstance(out, dict) else {"crosscheck_gate": gate_record}


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
    asm = sub.add_parser("assemble")
    asm.add_argument("xc_spec")
    asm.add_argument("dest")
    asm.add_argument("--sealed", action="append", required=True, help="one sealed G.1b attempt per node (x7)")
    asm.add_argument("--verdict", action="append", required=True, help="repository path of a step-2 verdict (x3)")
    asm.add_argument("--xc-tasl2", action="append", required=True, help="the cross-check TASL-2 attempt (x3)")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            for node in xc["nodes"]:
                for host in CROSS_HOSTS:
                    derived_spec(g1b, xc, node, host)
            print(json.dumps({"ok": True, "run_id": xc["run_id"], "nodes": xc["nodes"]}, indent=1))
        elif a.cmd == "derived":
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            print(str(write_derived(derived_spec(g1b, xc, a.node, a.host), a.node)))
        elif a.cmd in ("cpus", "logdir"):
            xc, g1b, _ = load_xc(Path(a.xc_spec))
            spec = derived_spec(g1b, xc, a.node, a.host)
            print(G.node_cpus(spec, G.node_entry(spec, a.node)) if a.cmd == "cpus" else
                  str(Path(spec["hosts"][a.host]["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "check-note2":
            print(json.dumps(check_note2(Path(a.note), Path(a.xc_spec), [Path(v) for v in a.verdict]), indent=1))
        elif a.cmd == "assemble":
            out = assemble_gated(Path(a.xc_spec), Path(a.dest), [Path(x) for x in a.sealed],
                                 [Path(v) for v in a.verdict], [Path(x) for x in a.xc_tasl2])
            print(json.dumps(out, indent=1, default=str))
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
