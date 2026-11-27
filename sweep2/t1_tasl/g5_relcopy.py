"""The REL-T1-G1B copy step (G.5 code unit part 3b-2). AI-assisted (Claude). ENGINEERING_ONLY: the G.1b summaries are
noise floors; no label is read.

Authority: R1-SWEEP2-RELEASE-DECISIONS REL-T1-G1B ("each summary copied out of the sealed tree by a reviewed step with
its sha256 before the T1 train/dev row"), PRE-DELTA A as so amended, the G.5 draft revision 8 §3 and §5 ``noise_floor``,
and what part 3a's switch checks (``g5_tasl.check_seven_copy`` / ``check_g1b_copy``, the spec's ``noise_floor`` block,
``check_ar_record``'s ``noise_floor_copy`` and ``g1b_sealed_summary`` lines).

* **Seven nodes** (run ``g1b-tasl-20261121-b``, joined under G1B-JOIN): the joined, gated run directory holds
  ``summary.json`` (``g1b_crosscheck.summarise_gated``), ``ASSEMBLY.json``, ``runs.jsonl`` and ``crosscheck_gate.json``.
  The step checks what ``summarise_gated`` and 3a's switch check: the summary is ``g1b_tasl_summary/1``,
  ENGINEERING_ONLY, of that run, with exactly the seven nodes; its ``assembly_sha256`` is the directory's
  ``ASSEMBLY.json``, whose ``runs_sha256`` is its ``runs.jsonl``; the gate record is ``g1b_tasl_crosscheck_gate/1`` for
  the cross-check spec the G.5 spec binds (its three TASL-7 nodes, its G.1b spec sha256, its run id) and binds that
  ``ASSEMBLY.json`` and ``runs.jsonl``. It then copies ``summary.json`` and ``crosscheck_gate.json`` byte-identically
  into ``<dest>/`` (``crosscheck_gate.json`` beside the summary, as ``noise_floor.seven.gate_copy`` must be) and
  writes ``COPY_RECORD.json``. It prints the spec's ``noise_floor.seven`` fields and the needles the review must name.
* **Autoresearch** (run ``g1b-ar-tasl-20261122-a``): its ``g1b_tasl_ar_summary/1`` summary, of that run, with exactly
  ``autoresearch_fixedtokens``, bound to its ``ASSEMBLY.json`` (``g1b_tasl_ar_assembly/1``) and ``runs.jsonl``; copied
  to ``<dest>/``. It prints the completion record's ``noise_floor_copy`` and ``g1b_sealed_summary`` lines (G5-ARPEND A)
  or the spec's ``noise_floor.ar`` fields (G5-ARPEND B).
* **Expansion** (run ``g1b-x-tasl-20261126-a``): the four-node TASL-2 assembly beside ``sealed_g1b``. The source
  must match the published summary and assembly, the signed G.1b spec and the published PRE-SPLIT v2 amendment.
* **D6 A (R1-T1-FEAT-DECISIONS, amending REL-T1-G1B's copy list).** The step also copies the run
  directory's ``ASSEMBLY.json`` and ``runs.jsonl`` byte-identically beside the summary copy, each with its sha256 in
  ``COPY_RECORD.json`` (``assembly_copy``, ``assembly_sha256``, ``runs_copy``, ``runs_sha256``), in the spec fields it
  prints (``noise_floor.seven.*``, or ``noise_floor.ar.*`` under G5-ARPEND B) and in the needles the review must name.
  Before copying it checks what ``g5_noise.derive`` will check on the copies: the binding (summary
  ``assembly_sha256`` → ``ASSEMBLY.json``; its ``runs_sha256`` → ``runs.jsonl``), and for every node whose verdict
  qualifies under D21 or carries counts, the edit count and every edit's paired-seed count against the summary's
  ``n_edits`` and ``paired_joint_n`` (``g5_noise.edit_stats``). A verdict ``g1b_lib.summarise`` writes without counts
  (a node that failed fixed-seed determinism or was stopped: it does not qualify) is passed through; the copy step
  must not block the other nodes' copy (review M1), and ``g5_noise.node_delta`` re-checks every node a row cites.
  ``runs.jsonl`` holds validation metrics at the G.1b seeds only; a record of any node with a seed in the audit block
  7001–7010 is a STOP (``g5_noise.g1b_rows``), and no file is copied. Every source path passes
  ``r1.c3.analysis_guard.refuse_sealed``'s check (``g5_noise._refuse_sealed``) before it is opened and must be a
  regular file. The files are written from the checked bytes into a sibling directory renamed into place at the end;
  a STOP leaves no partial copy.
* **Source and destination.** The summary is a regular file with no symlink on its path. The original two kinds
  come from their G.1b spec's sealed root. ``dest`` is a repository path under ``docs/r1/reports/``; nothing is
  overwritten. The copies are committed and reviewed by the coordinating chat; the review names each copy's path and
  sha256, the sealed path, and for the seven nodes the gate copy and its sha256 (3a's ``check_g1b_copy``).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g1b_crosscheck as X  # noqa: E402
import g1b_tasl_join as JN  # noqa: E402
import g5_noise as N  # noqa: E402
import g5_tasl as S  # noqa: E402

L = G.L
Stop = G.Stop
COPY_SCHEMA = "g5_rel_t1_g1b_copy/1"
X_RUN_ID = "g1b-x-tasl-20261126-a"
X_NOTE = "docs/r1/authorizations/g1b_x_t1_tasl_20261126.md"
X_RESULT = "docs/r1/reports/g1b_x_20261127"
X_REVIEW = "docs/r1/reviews/G1B_X_RESULT_REVIEW_20261127_ROUND2.md"
X_RESULT_SHA256 = {
    "summary.json": "67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10",
    "ASSEMBLY.json": "b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077",
}
X_SPLIT_SHA256 = "970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7"
KINDS = {"seven": (G.SUMMARY_SCHEMA, JN.SEVEN_RUN_ID, list(S.SEVEN), G.ASSEMBLY_SCHEMA, "G5-7"),
         "ar": (G.AR_SUMMARY_SCHEMA, JN.AR_RUN_ID, [S.AR], G.AR_ASSEMBLY_SCHEMA, "G5-AR"),
         "x": (G.X_SUMMARY_SCHEMA, X_RUN_ID, list(G.X_NODES), G.X_ASSEMBLY_SCHEMA, "G5-X")}


def _sealed_roots(spec: dict, family: str) -> set[Path]:
    g1b = json.loads((S.REPO_ROOT / S.FAMILY_SPECS[family]).read_text())
    return {Path(h["sealed_root"]).resolve() for h in g1b["hosts"].values() if h.get("sealed_root")}


def _expansion_binding(summary: Path) -> dict:
    from g5_addendum import G1B_SPEC, release

    try:
        amendment = release.split_v2_amendment(S.REPO_ROOT)
    except release.ReleaseStop as exc:
        raise Stop(str(exc)) from None
    if amendment["sha256"] != X_SPLIT_SHA256:
        raise Stop("STOP: the expansion copy needs the published R1-G5-S9 PRE-SPLIT v2 amendment")

    paths = (X_NOTE, G1B_SPEC, f"{X_RESULT}/summary.json", f"{X_RESULT}/ASSEMBLY.json", X_REVIEW)
    published = {path: G._read_main(path) for path in paths}
    if missing := [path for path, raw in published.items() if not raw]:
        raise Stop(f"STOP: expansion G.1b copy requires these records on published main: {missing}")
    review = published[X_REVIEW].decode("utf-8")
    if not any(line.startswith("**Verdict: ACCEPTED.**") for line in review.splitlines()):
        raise Stop("STOP: the expansion G.1b result has no accepted review on published main")
    for name, sha in X_RESULT_SHA256.items():
        if N._sha(published[f"{X_RESULT}/{name}"]) != sha:
            raise Stop(f"STOP: the published expansion {name} differs from the accepted G.1b result")
    spec_raw = published[G1B_SPEC]
    spec = json.loads(spec_raw)
    spec_sha = N._sha(spec_raw)
    note = G._note_fields(published[X_NOTE])
    if (note.get("approved"), note.get("label"), note.get("run_id"), note.get("spec_sha256"),
        note.get("labels_read")) != ("true", G.ENGINEERING_ONLY, X_RUN_ID, spec_sha, "none") or not G.is_x(spec) or \
            spec.get("run_id") != X_RUN_ID or sorted(entry["node"] for entry in spec["nodes"]) != sorted(G.X_NODES):
        raise Stop("STOP: the signed expansion G.1b note does not bind the four-node spec/run")
    sealed_root = Path(spec["hosts"][S.WORKER_HOST]["sealed_root"])
    expected = sealed_root.parent / "assembly" / X_RUN_ID / "summary.json"
    if summary != expected:
        raise Stop(f"STOP: expansion summary must be {expected}")
    return {"summary_raw": published[f"{X_RESULT}/summary.json"],
            "assembly_raw": published[f"{X_RESULT}/ASSEMBLY.json"],
            "spec_sha256": spec_sha, "spec_json_sha256": N._sha(json.dumps(spec, sort_keys=True).encode()),
            "pre_split_amendment": f"{amendment['path']} sha256 {amendment['sha256']}"}


def check_source(spec: dict, kind: str, summary: Path) -> dict:
    """The sealed summary and its run directory, checked as 3a's switch and ``summarise_gated`` check them."""
    if kind not in KINDS:
        raise Stop(f"STOP: kind must be one of {sorted(KINDS)}")
    schema, run_id, nodes, asm_schema, family = KINDS[kind]
    summary = Path(summary)
    if not summary.is_absolute() or any(p.is_symlink() for p in [summary, *summary.parents]):
        raise Stop(f"STOP: {summary} must be an absolute path without symlinks")
    run_dir = summary.parent
    asm_path, runs_path, gate_path = run_dir / "ASSEMBLY.json", run_dir / "runs.jsonl", run_dir / "crosscheck_gate.json"
    N._refuse_sealed(summary, asm_path, runs_path, gate_path)          # before any of them is opened (review m1)
    expansion = _expansion_binding(summary) if kind == "x" else None
    if not summary.is_file():
        raise Stop(f"STOP: {summary} is not a file")
    if expansion is None:
        roots = _sealed_roots(spec, family)
        if not any(r in summary.resolve().parents for r in roots):
            raise Stop(f"STOP: {summary} is not in the sealed G.1b tree {sorted(map(str, roots))} (REL-T1-G1B: copied out "
                       f"of the sealed tree)")
    raw = summary.read_bytes()
    s = json.loads(raw)
    if s.get("schema") != schema or s.get("label") != G.ENGINEERING_ONLY or s.get("run_id") != run_id:
        raise Stop(f"STOP: {summary} is not the {schema} ENGINEERING_ONLY summary of run {run_id}")
    if sorted(s.get("verdicts") or {}) != sorted(nodes):
        raise Stop(f"STOP: {summary} covers {sorted(s.get('verdicts') or {})}, not {sorted(nodes)}")
    if not asm_path.is_file() or not runs_path.is_file() or asm_path.is_symlink() or runs_path.is_symlink():
        raise Stop(f"STOP: {run_dir} is not an assembled G.1b run directory (ASSEMBLY.json, runs.jsonl as regular "
                   f"files)")
    asm_raw = asm_path.read_bytes()
    if expansion and (raw != expansion["summary_raw"] or asm_raw != expansion["assembly_raw"]):
        raise Stop("STOP: expansion G.1b source summary or ASSEMBLY.json differs from the reviewed published result")
    asm = json.loads(asm_raw)
    if expansion and (asm.get("spec_json_sha256") != expansion["spec_json_sha256"] or
                      sorted(job.get("node", "") for job in asm.get("jobs", ())) != sorted(nodes) or
                      any(job.get("spec_sha256") != expansion["spec_sha256"] for job in asm["jobs"])):
        raise Stop("STOP: expansion G.1b assembly does not bind all four jobs to the published spec")
    runs_raw = runs_path.read_bytes()
    if s.get("assembly_sha256") != N._sha(asm_raw) or asm.get("schema") != asm_schema or \
            asm.get("run_id") != run_id or asm.get("runs_sha256") != N._sha(runs_raw):
        raise Stop(f"STOP: {summary} is not bound to its directory's ASSEMBLY.json ({asm_schema}) and runs.jsonl")
    rows = N.g1b_rows(runs_raw, str(runs_path))     # D6 A: no record of any node at a seed in 7001-7010
    if expansion and {row.get("node") for row in rows} != set(nodes):
        raise Stop("STOP: expansion G.1b runs.jsonl must cover exactly the four expansion nodes")
    for node in sorted(nodes):                       # what g5_noise.derive checks on the copies (review M1:
        v = s["verdicts"].get(node) or {}            # g1b_lib.summarise writes no counts for a node that failed
        n_edits, pj = v.get("n_edits"), v.get("paired_joint_n")      # determinism or was stopped; such a verdict
        if v.get("qualifies_D21") is not True and n_edits is None and pj is None:    # does not qualify and is
            continue                                 # passed through; node_delta re-checks every cited node)
        if isinstance(n_edits, bool) or not isinstance(n_edits, int) or n_edits < 1 or not isinstance(pj, list):
            raise Stop(f"STOP: {summary}: the verdict for {node} has no n_edits / paired_joint_n (D6 A, D18)")
        if N.edit_stats(rows, node, n_edits)[1] != pj:
            raise Stop(f"STOP: {node}: the paired-seed counts in {runs_path} differ from the summary's paired_joint_n")
    out = {"kind": kind, "summary": summary, "raw": raw, "sha256": N._sha(raw), "run_id": run_id,
           "nodes": sorted(nodes), "qualifies_D21": {n: (v or {}).get("qualifies_D21") is True
                                                     for n, v in s["verdicts"].items()},
           "assembly_sha256": s["assembly_sha256"], "assembly": asm_path, "assembly_raw": asm_raw,
           "runs": runs_path, "runs_raw": runs_raw, "runs_sha256": N._sha(runs_raw)}
    if kind == "seven":
        xs = spec["noise_floor"]["seven"]["crosscheck_spec"]
        if L._sha_file(S.REPO_ROOT / xs["path"]) != xs["sha256"]:
            raise Stop("STOP: the cross-check spec in the checkout is not the one the G.5 spec binds")
        xc = json.loads((S.REPO_ROOT / xs["path"]).read_text())
        if xc["g1b_spec"]["sha256"] != spec["harness_families"]["G5-7"]["g1b_spec"]["sha256"]:
            raise Stop("STOP: the cross-check spec does not bind the seven-node G.1b spec the G.5 spec binds")
        if not gate_path.is_file() or gate_path.is_symlink():
            raise Stop(f"STOP: {run_dir} has no crosscheck_gate.json (not assembled through the cross-check gate)")
        gate_raw = gate_path.read_bytes()
        gate = json.loads(gate_raw)
        problems = [k for k, ok in (
            ("schema", gate.get("schema") == X.GATE_SCHEMA),
            ("nodes", sorted(gate.get("nodes") or {}) == sorted(xc["nodes"])),
            ("g1b_spec_sha256", gate.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"]),
            ("crosscheck_run_id", gate.get("crosscheck_run_id") == xc["run_id"]),
            ("assembly_json_sha256", gate.get("assembly_json_sha256") == N._sha(asm_raw)),
            ("runs_jsonl_sha256", gate.get("runs_jsonl_sha256") == N._sha(runs_raw))) if not ok]
        if problems:
            raise Stop(f"STOP: {gate_path} does not bind this assembly and the TASL-7 nodes: {problems}")
        out.update(gate=gate_path, gate_raw=gate_raw, gate_sha256=N._sha(gate_raw))
    elif expansion:
        out.update(pre_split_amendment=expansion["pre_split_amendment"], g1b_spec_sha256=expansion["spec_sha256"])
    return out


def _write_verified(path: Path, raw: bytes, sha256: str, what: str) -> None:
    """Write bytes that were checked (never re-read from the sealed tree) and verify the written file's sha256."""
    with Path(path).open("xb") as fh:
        fh.write(raw)
    if L._sha_file(path) != sha256:
        raise Stop(f"STOP: the {what} copy differs from the checked sealed bytes")


def copy_summary(spec: dict, kind: str, summary: Path, dest: str, *, repo: Path | None = None) -> dict:
    """Copy one sealed G.1b summary (and, for the seven nodes, its cross-check gate record beside it), with its run's
    ``ASSEMBLY.json`` and ``runs.jsonl`` (D6 A), into the repository at ``dest`` (a directory under docs/r1/reports/,
    new), byte-identically from the bytes ``check_source`` checked, with ``COPY_RECORD.json``. Everything is written
    into a new sibling directory. Once every file is verified, reserve ``dest`` exclusively and rename into it.
    A STOP leaves no partial copy (review m2)."""
    repo = Path(repo or S.REPO_ROOT)
    if not S._rel_ok(dest) or not dest.startswith("docs/r1/reports/"):
        raise Stop("STOP: dest must be a repository path under docs/r1/reports/")
    src = check_source(spec, kind, summary)
    target = repo / dest.rstrip("/")
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents]):
        raise Stop(f"STOP: {target} exists (a REL-T1-G1B copy is written once)")
    target.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f".{target.name}.partial-", dir=target.parent))
    umask = os.umask(0)
    os.umask(umask)
    os.chmod(work, 0o777 & ~umask)                   # as a plain mkdir would create it (mkdtemp gives 0700)
    try:
        record = _write_copies(src, kind, dest.rstrip("/"), work)
        try:
            target.mkdir()
        except FileExistsError:
            raise Stop(f"STOP: {target} exists (a REL-T1-G1B copy is written once)") from None
        try:
            os.rename(work, target)
        except BaseException:
            target.rmdir()      # the empty reservation created by this invocation
            raise
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise
    return record


def _write_copies(src: dict, kind: str, base: str, work: Path) -> dict:
    """The files of one copy, written into ``work`` (later renamed to ``base``), and the copy record."""
    rel = f"{base}/summary.json"
    _write_verified(work / "summary.json", src["raw"], src["sha256"], "summary")
    runs = {"assembly_copy": f"{base}/ASSEMBLY.json", "assembly_sha256": src["assembly_sha256"],
            "runs_copy": f"{base}/runs.jsonl", "runs_sha256": src["runs_sha256"]}
    _write_verified(work / "ASSEMBLY.json", src["assembly_raw"], runs["assembly_sha256"], "ASSEMBLY.json")   # D6 A
    _write_verified(work / "runs.jsonl", src["runs_raw"], runs["runs_sha256"], "runs.jsonl")
    record = {"schema": COPY_SCHEMA, "label": G.ENGINEERING_ONLY, "kind": kind, "authority": "REL-T1-G1B "
              "(R1-SWEEP2-RELEASE-DECISIONS) with its copy list amended by R1-T1-FEAT-DECISIONS D6 A; PRE-DELTA A",
              "run_id": src["run_id"], "nodes": src["nodes"],
              "qualifies_D21": src["qualifies_D21"], "sealed_path": str(src["summary"]), "copy": rel,
              "sha256": src["sha256"], **runs, "sealed_assembly_path": str(src["assembly"]),
              "sealed_runs_path": str(src["runs"])}
    needles = [runs["assembly_copy"], runs["assembly_sha256"], runs["runs_copy"], runs["runs_sha256"]]
    if kind == "seven":
        gate_rel = f"{base}/crosscheck_gate.json"
        _write_verified(work / "crosscheck_gate.json", src["gate_raw"], src["gate_sha256"], "cross-check gate")
        record.update(gate_copy=gate_rel, gate_sha256=src["gate_sha256"], gate_sealed_path=str(src["gate"]))
        record["spec_fields"] = {"noise_floor.seven.copy": rel, "noise_floor.seven.sha256": src["sha256"],
                                 "noise_floor.seven.sealed_path": str(src["summary"]),
                                 "noise_floor.seven.gate_copy": gate_rel,
                                 "noise_floor.seven.gate_sha256": src["gate_sha256"],
                                 **{f"noise_floor.seven.{k}": v for k, v in runs.items()}}
        record["review_must_name"] = [rel, src["sha256"], str(src["summary"]), gate_rel, src["gate_sha256"], *needles]
    elif kind == "ar":
        record["completion_record_lines"] = [f"noise_floor_copy: {rel} sha256 {src['sha256']}",
                                             f"g1b_sealed_summary: {src['summary']} sha256 {src['sha256']}"]
        record["spec_fields_under_arpend_b"] = {"noise_floor.ar.copy": rel, "noise_floor.ar.sha256": src["sha256"],
                                                "noise_floor.ar.sealed_path": str(src["summary"]),
                                                **{f"noise_floor.ar.{k}": v for k, v in runs.items()}}
        record["review_must_name"] = [rel, src["sha256"], str(src["summary"]), *needles]
    else:
        record.update(pre_split_amendment=src["pre_split_amendment"], g1b_spec_sha256=src["g1b_spec_sha256"],
                      g1b_copy={"copy": rel, "sha256": src["sha256"], "sealed_path": str(src["summary"]), **runs},
                      review_must_name=[rel, src["sha256"], str(src["summary"]), *needles,
                                        src["pre_split_amendment"], src["g1b_spec_sha256"]])
    record["d21_verdict"] = {n: "qualifies" if q else "does_not_qualify" for n, q in src["qualifies_D21"].items()}
    with (work / "COPY_RECORD.json").open("x") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record
