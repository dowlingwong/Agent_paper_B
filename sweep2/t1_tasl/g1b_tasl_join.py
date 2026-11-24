"""Joining the G.1b noise floors on the TASL pair after R1-T1-DATA-MANIFEST. AI-assisted (Claude). ENGINEERING_ONLY:
no label is read.

**Why.** R1-T1-DATA-MANIFEST re-issues the seven-node spec ``sweep2/t1_tasl/g1b_tasl_spec.json`` with two corrected
census data manifests (``mlgym_fmnist``, ``mlgym_cifar10``) and a new ``paper.commit``; the run id stays
``g1b-tasl-20261121-b``. The three sealed TASL-2 nodes (``mlab_ogbn_arxiv``, ``mlab_imdb``, ``mlgym_houseprice``) stay
under the first note and are not rerun, so their job records carry the first spec's sha256 (``060aac91…``), while
``mlgym_fmnist`` (amendment note) and the three TASL-7 nodes (note 2) carry the re-issued spec's. ``g1b_tasl.assemble``
admits one spec sha256 per table, so the seven-node row cannot assemble unchanged. This module is the assembly rule
of decision **G1B-JOIN** (option A; ``docs/r1/reports/tasl_chain_20261122/TASL_CHAIN_20261122.md``). It refuses to run
unless the author row ``R1-G1B-JOIN`` is on published ``main`` (``JOIN_ROW``; the name is the proposal's).

**The rule (option A).**
- The predecessor spec is the first note's (given as a file, e.g. ``git show 985dd45d:sweep2/t1_tasl/g1b_tasl_spec.json``):
  its sha256 and ``paper.commit`` must equal the ``spec_sha256`` and ``paper_commit`` of the signed first note
  ``docs/r1/authorizations/g1b_t1_tasl_20261121.md`` on published ``main``. The re-issued spec is the one the
  cross-check binds (``g1b_spec.sha256``; ``assemble_join`` requires the expected sha256 as an argument).
- The two have the same run id and node list, and differ in exactly ``paper.commit`` and the ``data_manifest_sha256``
  of the corrected nodes (``CORRECTED_NODES``), nothing else (``spec_difference``).
- A sealed attempt may carry the predecessor's spec sha256 only for a node outside ``CORRECTED_NODES`` (its node entry
  is then identical in both specs); every other attempt carries the re-issued spec's sha256.
- Each group is assembled by the reviewed ``g1b_tasl.assemble`` with its own spec and sha256 (receipt, sums, run id,
  harness, host, GPU, stop class, sibling attempts: all as before). The two groups are merged into one run directory
  whose ``ASSEMBLY.json`` names the re-issued spec (so ``g1b_tasl.summarise`` and ``g1b_lib.summarise`` read it as
  the seven-node table) and records the join: both spec sha256s and paper commits, the nodes under each, the job-code
  files that differ between the two paper commits (``git diff --name-only``; reviewed: only the autoresearch-only
  branches of ``g1b_tasl.py`` and the cross-check kind of ``t1_tasl_node.sh``), and the unsealed attempts given as
  not used (``mlgym_fmnist``'s two infrastructure attempts under the first spec, in the runs tree).
- For the TASL-7 nodes, ``assemble_gated_join`` first runs the cross-check gate of ``g1b_crosscheck.assemble_gated``
  (the committed step-2 PASS equals the comparison recomputed from the attempts given) and writes the same
  ``crosscheck_gate.json``, so ``g1b_crosscheck.summarise`` (``summarise_gated``) summarises the joined run unchanged.

**Autoresearch joins by node.** Its noise floor is its own run (``g1b-ar-tasl-20261122-a``, third note, harness
``2d09f9a9``) with its own summary (``g1b_tasl_ar_summary/1``). ``noise_floor_by_node`` joins the seven-node summary
and the autoresearch summary per node, refusing an overlap, and requires the union to be exactly the eight T1 nodes of
the split file ``r1/c3/splits/c3_p3_split_v1.json`` (R1-SWEEP2-PREREG PRE-SPLIT A). The two summaries are never merged
into one assembly: their specs, harness pins and environments differ (G5-PIN B).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "g1b"))
import g1b_tasl as G  # noqa: E402
import g1b_crosscheck as X  # noqa: E402
import g1b_lib as L  # noqa: E402

Stop = L.Stop
JOIN_ROW = "R1-G1B-JOIN"
FIRST_NOTE = "docs/r1/authorizations/g1b_t1_tasl_20261121.md"
JOB_CODE_PATHS = ("sweep2/t1_tasl/g1b_tasl.py", "sweep2/t1_tasl/t1_tasl_node.sh", "sweep2/g1b", "r1/noise",
                  "r1/harness.py")
SEVEN_RUN_ID = "g1b-tasl-20261121-b"
AR_RUN_ID = "g1b-ar-tasl-20261122-a"
CORRECTED_NODES = ("mlgym_fmnist", "mlgym_cifar10")       # R1-T1-DATA-MANIFEST
JOIN_SCHEMA = "g1b_tasl_join/1"
FLOOR_SCHEMA = "g1b_tasl_floor_by_node/1"
SPLIT_REL = "r1/c3/splits/c3_p3_split_v1.json"


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _diff(a, b, path=()) -> list[tuple]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(path + (k,))
            else:
                out += _diff(a[k], b[k], path + (k,))
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [path]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += _diff(x, y, path + (i,))
        return out
    return [] if a == b and type(a) is type(b) else [path]


def spec_difference(predecessor: dict, amended: dict) -> dict:
    """The JSON paths where the two seven-node specs differ, checked against the R1-T1-DATA-MANIFEST rule: the same run
    id and node list, and differences only in ``paper.commit`` and the corrected nodes' ``data_manifest_sha256``."""
    if predecessor.get("run_id") != amended.get("run_id"):
        raise Stop("STOP: the re-issued spec must keep the predecessor's run id")
    names = [n.get("node") for n in predecessor.get("nodes", [])]
    if names != [n.get("node") for n in amended.get("nodes", [])]:
        raise Stop("STOP: the re-issued spec must list the predecessor's nodes in the same order")
    allowed = {("paper", "commit")}
    allowed |= {("nodes", i, "data_manifest_sha256") for i, n in enumerate(names) if n in CORRECTED_NODES}
    paths = _diff(predecessor, amended)
    extra = [p for p in paths if p not in allowed]
    if extra:
        raise Stop(f"STOP: the re-issued spec differs from the predecessor outside R1-T1-DATA-MANIFEST: {extra[:5]}")
    changed_nodes = sorted({names[p[1]] for p in paths if p[0] == "nodes"})
    return {"paths": [".".join(map(str, p)) for p in paths], "corrected_nodes": changed_nodes,
            "unchanged_nodes": [n for n in names if n not in CORRECTED_NODES]}


def _row_on_main(read_main) -> None:
    plan = (read_main("docs/r1/PLAN.md") or b"").decode()
    if not re.search(rf"^\| {re.escape(JOIN_ROW)} \|", plan, re.M):
        raise Stop(f"STOP: the joined assembly needs the author row {JOIN_ROW} on published main (decision G1B-JOIN)")


def _first_note(read_main) -> dict:
    raw = read_main(FIRST_NOTE)
    if not raw:
        raise Stop(f"STOP: the signed first note {FIRST_NOTE} is not on published main")
    f = G._note_fields(raw)
    if f.get("approved") != "true":
        raise Stop(f"STOP: {FIRST_NOTE} on main is not signed")
    return f


def _code_diff(old: str, new: str, repo: Path) -> list[str]:
    res = L._git(repo, "diff", "--name-only", old, new, "--", *JOB_CODE_PATHS)
    if res.returncode:
        raise Stop(f"STOP: cannot diff the job code between {old} and {new} in {repo}: {res.stderr.strip()[:200]}")
    return res.stdout.split()


def _unsealed(paths) -> list[dict]:
    out = []
    for d in map(Path, paths or []):
        rec = json.loads((d / "job_record.json").read_text())
        if rec.get("stop_class") != "infrastructure":
            raise Stop(f"STOP: {d} is not an infrastructure attempt (only those are listed as not used)")
        out.append({"path": str(d), "node": rec.get("node"), "attempt": rec.get("attempt"),
                    "spec_sha256": rec.get("spec_sha256"), "stop": rec.get("stop"),
                    "job_record_sha256": L._sha_file(d / "job_record.json")})
    return out


def assemble_join(sealed_dirs: list[Path], amended_path: Path, predecessor_path: Path, dest: Path, *,
                  expected_amended_sha256: str, unsealed: list[Path] = (), read_main=G._read_main,
                  repo: Path | None = None) -> dict:
    """The seven-node assembly across the first note's attempts (predecessor spec) and the amendment's and note 2's
    attempts (re-issued spec), by the rule in the module docstring."""
    _row_on_main(read_main)
    first = _first_note(read_main)
    dest = Path(dest)
    if dest.exists():
        raise Stop(f"STOP: {dest} exists (no overwrite)")
    amended_path, predecessor_path = Path(amended_path), Path(predecessor_path)
    amended, predecessor = G.load_spec(amended_path), G.load_spec(predecessor_path)
    G.validate_spec(copy.deepcopy(amended))
    G.validate_spec(copy.deepcopy(predecessor))
    diff = spec_difference(predecessor, amended)
    sha_new, sha_old = L._sha_file(amended_path), L._sha_file(predecessor_path)
    if sha_new == sha_old:
        raise Stop("STOP: the predecessor and the re-issued spec are the same file; use g1b_tasl.assemble")
    if sha_old != first.get("spec_sha256") or predecessor["paper"]["commit"] != first.get("paper_commit"):
        raise Stop(f"STOP: the predecessor spec must be the signed first note's ({first.get('spec_sha256')}, paper "
                   f"commit {first.get('paper_commit')})")
    if sha_new != expected_amended_sha256:
        raise Stop(f"STOP: the re-issued spec {sha_new} is not the one expected ({expected_amended_sha256}: the spec the "
                   "cross-check binds)")
    code_diff = _code_diff(predecessor["paper"]["commit"], amended["paper"]["commit"], Path(repo or G.REPO_ROOT))
    not_used = _unsealed(unsealed)
    groups: dict[str, list[Path]] = {sha_old: [], sha_new: []}
    nodes_by_group: dict[str, list[str]] = {sha_old: [], sha_new: []}
    for d in map(Path, sealed_dirs):
        rec = json.loads((d / "job_record.json").read_text())
        node, sha = rec.get("node"), rec.get("spec_sha256")
        if sha not in groups:
            raise Stop(f"STOP: {d} carries spec sha256 {sha}, neither the predecessor's nor the re-issued spec's")
        if sha == sha_old and node in CORRECTED_NODES:
            raise Stop(f"STOP: {node} has a corrected data manifest; its attempt must carry the re-issued spec")
        groups[sha].append(d)
        nodes_by_group[sha].append(node)
    all_nodes = nodes_by_group[sha_old] + nodes_by_group[sha_new]
    if len(set(all_nodes)) != len(all_nodes):
        raise Stop("STOP: two sealed attempts given for one node")
    with tempfile.TemporaryDirectory(prefix="g1b_join_", dir=str(dest.parent) if dest.parent.exists() else None) as tmp:
        parts = []
        for sha, spec in ((sha_old, predecessor), (sha_new, amended)):
            if groups[sha]:
                out = Path(tmp) / sha[:12]
                parts.append((sha, out, G.assemble(groups[sha], spec, out, sha)))
        dest.mkdir(parents=True)
        rows, edits, jobs = [], {}, []
        for sha, out, manifest in parts:
            rows += [json.loads(line) for line in (out / "runs.jsonl").read_text().splitlines() if line.strip()]
            edits.update(json.loads((out / "edits.json").read_text()))
            jobs += manifest["jobs"]
            shutil.move(str(out / "_unpacked"), str(dest / f"_unpacked_{sha[:12]}"))
    (dest / "runs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (dest / "edits.json").write_text(json.dumps(edits, indent=1) + "\n")
    manifest = {"schema": G.ASSEMBLY_SCHEMA, "run_id": amended["run_id"], "jobs": jobs,
                "spec_json_sha256": hashlib.sha256(json.dumps(amended, sort_keys=True).encode()).hexdigest(),
                "runs_sha256": L._sha_file(dest / "runs.jsonl"),
                "join": {"schema": JOIN_SCHEMA, "rule": JOIN_ROW, "authority": "R1-T1-DATA-MANIFEST",
                         "predecessor_spec_sha256": sha_old, "spec_sha256": sha_new, "difference": diff,
                         "paper_commits": {"predecessor": predecessor["paper"]["commit"],
                                           "spec": amended["paper"]["commit"]},
                         "job_code_files_differing": code_diff,
                         "nodes_under_predecessor": sorted(nodes_by_group[sha_old]),
                         "nodes_under_spec": sorted(nodes_by_group[sha_new]),
                         "unsealed_attempts_not_used": not_used}}
    (dest / "ASSEMBLY.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def assemble_gated_join(xc_path: Path, dest: Path, sealed_dirs: list[Path], verdict_paths: list[Path],
                        xc_tasl2: list[Path], predecessor_path: Path, *, unsealed: list[Path] = (),
                        read_main=G._read_main) -> dict:
    """``g1b_crosscheck.assemble_gated`` with the joined assembly: the same R1-T1-TASL-ENV gate for the TASL-7 nodes
    (their committed step-2 PASS equals the comparison recomputed now), then ``assemble_join`` with the re-issued spec
    the cross-check binds, then the same ``crosscheck_gate.json``."""
    xc, g1b, g1b_path = X.load_xc(xc_path)
    by_node, t2 = {}, {}
    for target, dirs, what in ((by_node, sealed_dirs, "sealed attempts"), (t2, xc_tasl2, "cross-check TASL-2 attempts")):
        for d in map(Path, dirs):
            node = json.loads((d / "job_record.json").read_text()).get("node")
            if node in target:
                raise Stop(f"STOP: two {what} given for {node}")
            target[node] = d
    verdicts = X._committed_verdicts(verdict_paths, read_main)
    gate = {}
    for node in xc["nodes"]:
        if node not in by_node or node not in t2 or node not in verdicts:
            raise Stop(f"STOP: {node} needs its G.1b TASL-7 attempt, its cross-check TASL-2 attempt and its verdict")
        rel, _, committed = verdicts[node]
        if committed.get("mode") != "preassembly" or committed.get("verdict") != "PASS":
            raise Stop(f"STOP: {rel} is not a step-2 PASS for {node} (R1-T1-TASL-ENV); no assembly")
        now = X.compare(by_node[node], t2[node], node, mode="preassembly", xc_path=xc_path)
        if X._verdict_core(now) != X._verdict_core(committed):
            raise Stop(f"STOP: {rel} is not the comparison of the attempts given for {node}")
        gate[node] = {"verdict": rel, "tasl7_job_record_sha256": now["sides"]["TASL-7"]["job_record_sha256"]}
    extra = sorted(set(verdicts) - set(xc["nodes"])) + sorted(set(t2) - set(xc["nodes"]))
    if extra:
        raise Stop(f"STOP: verdicts or cross-check attempts for non-TASL-7 nodes {extra}")
    out = assemble_join(list(map(Path, sealed_dirs)), g1b_path, predecessor_path, Path(dest),
                        expected_amended_sha256=xc["g1b_spec"]["sha256"], unsealed=unsealed, read_main=read_main)
    dest = Path(dest)
    gate_record = {"schema": X.GATE_SCHEMA, "rule": "R1-T1-TASL-ENV", "nodes": gate,
                   "g1b_spec_sha256": xc["g1b_spec"]["sha256"], "crosscheck_run_id": xc["run_id"],
                   "assembly_json_sha256": X._sha(dest / "ASSEMBLY.json"), "runs_jsonl_sha256": X._sha(dest / "runs.jsonl")}
    (dest / "crosscheck_gate.json").write_text(json.dumps(gate_record, indent=1, sort_keys=True) + "\n")
    return {**out, "crosscheck_gate": gate_record}


def noise_floor_by_node(seven_summary: Path, ar_summary: Path, split_file: Path) -> dict:
    """{node: its noise-floor source} for the eight T1 nodes: the seven-node summary (``g1b_tasl_summary/1``, run
    ``g1b-tasl-20261121-b``) and autoresearch's (``g1b_tasl_ar_summary/1``, its own run), joined by node. Refuses a
    node in both, a summary of the wrong kind, and a union other than the split file's T1 nodes."""
    out, seen = {}, {}
    for path, schema, run_id in ((seven_summary, G.SUMMARY_SCHEMA, SEVEN_RUN_ID),
                                 (ar_summary, G.AR_SUMMARY_SCHEMA, AR_RUN_ID)):
        raw = Path(path).read_bytes()
        s = json.loads(raw)
        if s.get("schema") != schema or s.get("label") != G.ENGINEERING_ONLY or s.get("run_id") != run_id:
            raise Stop(f"STOP: {path} is not a {schema} ENGINEERING_ONLY summary of run {run_id}")
        if schema == G.SUMMARY_SCHEMA:          # the seven-node row passes the cross-check gate (R1-T1-TASL-ENV)
            gate_path = Path(path).parent / "crosscheck_gate.json"
            gate = json.loads(gate_path.read_text()) if gate_path.is_file() else {}
            if gate.get("schema") != X.GATE_SCHEMA or gate.get("assembly_json_sha256") != s.get("assembly_sha256"):
                raise Stop(f"STOP: {path} does not sit beside the cross-check gate record of its assembly")
        for node, verdict in (s.get("verdicts") or {}).items():
            if node in seen:
                raise Stop(f"STOP: {node} has a noise floor in both {seen[node]} and {path}")
            seen[node] = str(path)
            out[node] = {"summary": str(path), "summary_sha256": _sha_bytes(raw), "run_id": s.get("run_id"),
                         "schema": schema, "qualifies_D21": verdict.get("qualifies_D21"),
                         "assembly_sha256": s.get("assembly_sha256")}
    split = json.loads(Path(split_file).read_text())
    t1 = sorted((split.get("t1") or {}).get("nodes") or [])
    if sorted(out) != t1:
        raise Stop(f"STOP: the noise floors cover {sorted(out)}, the split file's T1 nodes are {t1}")
    return {"schema": FLOOR_SCHEMA, "split_file_sha256": L._sha_file(Path(split_file)), "nodes": out}


_FIELD_FILL = re.compile(r"^[A-Za-z0-9_]+[^\S\n]*:.*<FILL", re.M)      # the parser's key\s*: on one line
_P4_PASS = re.compile(r"^P4[^\S\n]*: PASS — .*$", re.M)
_P4_ERRATUM = re.compile(r"census erratum record docs/r1/\S+ sha256 [0-9a-f]{64}\b")
_CITED = re.compile(r"(docs/r1/[A-Za-z0-9_.\-/]+) sha256 ([0-9a-f]{64})\b")
_CITING_FIELDS = re.compile(r"^(P4|census_erratum)[^\S\n]*:(.*)$", re.M)


LAUNCH_TABLE_REL = "docs/r1/reports/tasl_chain_20261122/launch_table.json"


def _fetch_origin() -> bool:
    return subprocess.run(["git", "-C", str(G.REPO_ROOT), "fetch", "-q", "origin"],
                          capture_output=True).returncode == 0


def _main_erratum() -> dict | None:
    """The reviewed erratum record the published chain names (``erratum`` of its launch table on origin/main)."""
    res = subprocess.run(["git", "-C", str(G.REPO_ROOT), "show", f"origin/main:{LAUNCH_TABLE_REL}"],
                         capture_output=True)
    if res.returncode != 0:
        return None
    return (json.loads(res.stdout) or {}).get("erratum")


def _main_sha256(rel: str) -> str | None:
    """sha256 of ``rel`` on the freshly fetched ``origin/main`` of the paper repo, or None if it is not there."""
    res = subprocess.run(["git", "-C", str(G.REPO_ROOT), "show", f"origin/main:{rel}"], capture_output=True)
    return hashlib.sha256(res.stdout).hexdigest() if res.returncode == 0 else None


def publication_check(text: str, *, p4: bool = False, main_sha256=None, erratum=None) -> list[str]:
    """The coordinating chat's check of a signed note before it is published (chain review, round 2 m1 and the
    confirmation's C1): no ``key:`` field line still carries ``<FILL`` (prose lines and the ``<path>``/``<date>``
    templates of a PENDING P7 are not fields with ``<FILL``), and, for the amendment and note 2 (``p4``), exactly one
    ``P4: PASS — `` line that cites ``census erratum record docs/r1/… sha256 <64 hex>`` (a deleted clause is refused). ``g1b_tasl.check_note`` reads only P4's leading "PASS — " and its review citation, so an
    amendment signed as "PASS — … <FILL …>" would otherwise launch. With ``main_sha256`` (the CLI passes the
    ``origin/main`` reader), every ``docs/r1/… sha256 <64 hex>`` citation in P4 or ``census_erratum`` must name a file
    on ``main`` with that sha256, and with ``erratum`` (the CLI passes the published launch table's) a citation of the
    erratum record must carry exactly the sha256 its review fixed, as the chain names it: the cited bytes are the
    reviewed ones (chain review rounds 3–4). Returns the problems (empty = publishable)."""
    bad = [f"field still to fill: {m.group(0)[:80]}" for m in _FIELD_FILL.finditer(text)]
    if p4:
        p4_lines = _P4_PASS.findall(text)
        if len(p4_lines) != 1:
            bad.append("P4 must be one line reading 'P4: PASS — …'")
        elif not _P4_ERRATUM.search(p4_lines[0]):       # the clause filled, not deleted
            bad.append("P4 must cite 'census erratum record docs/r1/… sha256 <64 hex>'")
    if main_sha256 is not None:
        for field in _CITING_FIELDS.finditer(text):
            for rel, want in _CITED.findall(field.group(2)):
                if erratum is not None and rel == erratum.get("record") and want != erratum.get("sha256"):
                    bad.append(f"{field.group(1)} cites {rel} sha256 {want[:12]}…, not the reviewed "
                               f"{str(erratum.get('sha256'))[:12]}… the chain names")
                got = main_sha256(rel)
                if got is None:
                    bad.append(f"{field.group(1)} cites {rel}, which is not on origin/main")
                elif got != want:
                    bad.append(f"{field.group(1)} cites {rel} sha256 {want[:12]}…, origin/main has {got[:12]}…")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assemble", help="the gated joined assembly of the seven-node row (decision G1B-JOIN)")
    a.add_argument("xc_spec")
    a.add_argument("--dest", required=True)
    a.add_argument("--predecessor-spec", required=True, help="the first note's spec file (sha256 060aac91…)")
    a.add_argument("--sealed", nargs="+", required=True)
    a.add_argument("--verdict", nargs="+", required=True)
    a.add_argument("--xc-tasl2", nargs="+", required=True)
    a.add_argument("--unsealed", nargs="*", default=[], help="infrastructure attempts in the runs tree, not used")
    f = sub.add_parser("floor-by-node", help="the eight T1 nodes' noise-floor sources, joined by node")
    f.add_argument("seven_summary")
    f.add_argument("ar_summary")
    f.add_argument("--split", default=str(G.REPO_ROOT / SPLIT_REL))
    c = sub.add_parser("publication-check", help="a signed note before publication: no field left to fill")
    c.add_argument("note")
    c.add_argument("--p4", action="store_true", help="the amendment and note 2: P4 must read PASS")
    args = ap.parse_args(argv)
    if args.cmd == "publication-check":
        if not _fetch_origin():
            print("STOP: git fetch origin failed; origin/main may be stale", file=sys.stderr)
            return 2
        erratum = _main_erratum()
        if not erratum:
            print(f"STOP: {LAUNCH_TABLE_REL} with its erratum is not on origin/main (publish the chain first)",
                  file=sys.stderr)
            return 2
        bad = publication_check(Path(args.note).read_text(), p4=args.p4, main_sha256=_main_sha256, erratum=erratum)
        for b in bad:
            print(b, file=sys.stderr)
        return 2 if bad else 0
    try:
        if args.cmd == "assemble":
            out = assemble_gated_join(Path(args.xc_spec), Path(args.dest), list(map(Path, args.sealed)),
                                      list(map(Path, args.verdict)), list(map(Path, args.xc_tasl2)),
                                      Path(args.predecessor_spec), unsealed=list(map(Path, args.unsealed)))
        else:
            out = noise_floor_by_node(Path(args.seven_summary), Path(args.ar_summary), Path(args.split))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
