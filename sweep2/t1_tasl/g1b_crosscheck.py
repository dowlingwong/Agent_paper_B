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
  = 10 runs) under the same lease, delegated scope, preflight and row gate as G.1b. The attempt is written under
  ``<runs_root>/<run id>-<host>/<node>/attempt-N/`` and sealed with ``g1b_tasl.py seal`` against the derived spec.

**The comparison.** ``compare`` reads two sealed attempts of a node (each verified against its receipt and sums, row
gate re-checked). It requires the same configurations with identical outcomes (``g1b_lib._outcome``: the metric
bit-identical when ok, the same failure when failed) for default and for default_repeat. Each side must also be
deterministic. It writes a verdict (PASS or STOP). It runs twice per node:

1. before the TASL-7 G.1b launch: the cross-check's TASL-7 attempt against its TASL-2 attempt (the job "has passed");
2. before assembly: the node's G.1b TASL-7 attempt (default part) against the cross-check's TASL-2 attempt (the row's
   literal comparison). A STOP there re-measures the node on TASL-2 (the author's step).

**Launch.** A signed note ``docs/r1/authorizations/g1b_xc_t1_tasl_<YYYYMMDD>.md`` on published ``main`` is required
(``check_xc_note``), as are both keys (``--enable`` and ``G1B_TASL_ENABLE_REAL=1``) and both hosts' host-check records
on ``main``. The launch binding is ``verify_launch_tasl`` with the cross-check spec: its ``paper.commit`` is a code-equal
ancestor of the published checkout.
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


def write_derived(spec: dict, node: str) -> Path:
    """Write the derived spec once under its run root; a later call must find the same bytes."""
    host = spec["crosscheck"]["host"]
    path = Path(spec["hosts"][host]["runs_root"]) / spec["run_id"] / "_specs" / f"{node}.json"
    data = (json.dumps(spec, indent=1, sort_keys=True) + "\n").encode()
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
    xc, g1b, _ = load_xc(xc_path)
    spec = derived_spec(g1b, xc, node, host)
    path = write_derived(spec, node)
    saved = (L.PARTS, L.merge_parts)
    L.PARTS, L.merge_parts = (L.PARTS[0],), _default_only_merge
    try:
        return G.run_node_job(path, node, **job_kw)
    finally:
        L.PARTS, L.merge_parts = saved


def _sealed_rows(sealed: Path) -> tuple[dict, list[dict]]:
    sealed = Path(sealed)
    if not (sealed / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: {sealed} has no SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed, capture_output=True).returncode != 0:
        raise Stop(f"STOP: {sealed} does not verify against its SHA256SUMS")
    record = json.loads((sealed / "job_record.json").read_text())
    receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    if receipt.get("job_record_sha256") != _sha(sealed / "job_record.json") or \
            receipt.get("node") != record.get("node") or receipt.get("run_id") != record.get("run_id"):
        raise Stop(f"STOP: {sealed} receipt does not bind its job record")
    if record.get("label") != G.ENGINEERING_ONLY or record.get("stop_class") not in (None, "node"):
        raise Stop(f"STOP: {sealed} is not a complete ENGINEERING_ONLY attempt (stop_class {record.get('stop_class')})")
    with tempfile.TemporaryDirectory(prefix="g1b_xc_") as tmp:
        with tarfile.open(sealed / "out.tar") as tar:
            member = next((m for m in tar.getmembers() if m.name.lstrip("./") == "out/default/runs.jsonl"), None)
            if member is None or not member.isfile():
                raise Stop(f"STOP: {sealed}/out.tar has no out/default/runs.jsonl")
            tar.extract(member, tmp, filter="data")
        rows = L._rows(Path(tmp) / member.name)
    for row in rows:
        L.check_row_gate(row)
    return record, [r for r in rows if r.get("condition") in DEFAULT_CONDITIONS]


def compare(a: Path, b: Path, node: str) -> dict:
    """The verdict of two sealed attempts of ``node`` on different hosts (module docstring)."""
    sides = {}
    for path in (a, b):
        record, rows = _sealed_rows(path)
        host = (record.get("host") or {}).get("host")
        if record.get("node") != node or host not in CROSS_HOSTS or host in sides:
            raise Stop(f"STOP: {path} is not an attempt of {node} on the other host")
        outcomes = {}
        for row in rows:
            key = (row["config"], row["condition"])
            if key in outcomes:
                raise Stop(f"STOP: {path} has two rows for {key}")
            outcomes[key] = L._outcome(row)
        det = L.determinism_check(rows)
        sides[host] = {"sealed": str(path), "job_record_sha256": _sha(Path(path) / "job_record.json"),
                       "run_id": record.get("run_id"), "spec_sha256": record.get("spec_sha256"),
                       "harness_commit": record.get("harness_commit"), "deterministic": det["deterministic"],
                       "outcomes": outcomes}
    t7, t2 = sides["TASL-7"], sides["TASL-2"]
    keys = sorted(set(t7["outcomes"]) | set(t2["outcomes"]))
    per = {f"{c}/{cond}": {"TASL-7": t7["outcomes"].get((c, cond)), "TASL-2": t2["outcomes"].get((c, cond)),
                          "identical": t7["outcomes"].get((c, cond)) == t2["outcomes"].get((c, cond))
                          and (c, cond) in t7["outcomes"] and (c, cond) in t2["outcomes"]}
           for c, cond in keys}
    configs = {c for c, _ in keys}
    complete = all((c, cond) in s["outcomes"] for s in (t7, t2) for c in configs for cond in DEFAULT_CONDITIONS)
    ok = bool(per) and complete and all(v["identical"] for v in per.values()) and \
        t7["deterministic"] and t2["deterministic"] and t7["harness_commit"] == t2["harness_commit"]
    for s in sides.values():
        s.pop("outcomes")
    return {"schema": VERDICT_SCHEMA, "label": G.ENGINEERING_ONLY, "node": node, "rule": "R1-T1-TASL-ENV",
            "verdict": "PASS" if ok else "STOP", "complete": complete, "sides": sides, "rows": per,
            "on_stop": None if ok else f"STOP: {node}'s G.1b is re-measured on TASL-2 (R1-T1-TASL-ENV); the author decides"}


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
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--node", required=True)
    c.add_argument("--out", required=True)
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
        elif a.cmd == "run-node":
            rec = launch_xc(Path(a.xc_spec), Path(a.note), a.node, a.host, enable=a.enable)
            print(json.dumps({"ok": True, "node": a.node, "host": a.host, "runs": rec.get("runs")}, indent=1))
        else:
            out = Path(a.out)
            if out.exists():
                raise Stop(f"STOP: {out} exists (no overwrite)")
            verdict = compare(Path(a.a), Path(a.b), a.node)
            out.write_text(json.dumps(verdict, indent=1, sort_keys=True, default=list) + "\n")
            print(json.dumps({"node": a.node, "verdict": verdict["verdict"]}, indent=1))
            return 0 if verdict["verdict"] == "PASS" else 3
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
