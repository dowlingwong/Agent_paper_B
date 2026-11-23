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
* **D6 A (R1-T1-FEAT-DECISIONS, amending REL-T1-G1B's copy list).** For both kinds the step also copies the run
  directory's ``ASSEMBLY.json`` and ``runs.jsonl`` byte-identically beside the summary copy, each with its sha256 in
  ``COPY_RECORD.json`` (``assembly_copy``, ``assembly_sha256``, ``runs_copy``, ``runs_sha256``), in the spec fields it
  prints (``noise_floor.seven.*``, or ``noise_floor.ar.*`` under G5-ARPEND B) and in the needles the review must name.
  Before copying it checks what ``g5_noise.derive`` will check on the copies: the binding (summary
  ``assembly_sha256`` → ``ASSEMBLY.json``; its ``runs_sha256`` → ``runs.jsonl``), and for every node of the summary
  the edit count and every edit's paired-seed count against the summary's ``n_edits`` and ``paired_joint_n``
  (``g5_noise.edit_stats``). ``runs.jsonl`` holds validation metrics at the G.1b seeds only; a record with a seed in
  the audit block 7001–7010 is a STOP (``g5_noise.g1b_rows``), and no file is copied. Every source path passes
  ``r1.c3.analysis_guard.refuse_sealed``'s check (``g5_noise._refuse_sealed``) and must be a regular file.
* **Out of the sealed G.1b tree.** The summary must lie under the G.1b spec's sealed root (``sealed_g1b``) and be a
  regular file (no symlink on its path). ``dest`` is a repository path under ``docs/r1/reports/``; nothing is
  overwritten. The copies are committed and reviewed by the coordinating chat; the review names each copy's path and
  sha256, the sealed path, and for the seven nodes the gate copy and its sha256 (3a's ``check_g1b_copy``).
"""
from __future__ import annotations

import json
import shutil
import sys
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
KINDS = {"seven": (G.SUMMARY_SCHEMA, JN.SEVEN_RUN_ID, list(S.SEVEN), G.ASSEMBLY_SCHEMA, "G5-7"),
         "ar": (G.AR_SUMMARY_SCHEMA, JN.AR_RUN_ID, [S.AR], G.AR_ASSEMBLY_SCHEMA, "G5-AR")}


def _sealed_roots(spec: dict, family: str) -> set[Path]:
    g1b = json.loads((S.REPO_ROOT / S.FAMILY_SPECS[family]).read_text())
    return {Path(h["sealed_root"]).resolve() for h in g1b["hosts"].values() if h.get("sealed_root")}


def check_source(spec: dict, kind: str, summary: Path) -> dict:
    """The sealed summary and its run directory, checked as 3a's switch and ``summarise_gated`` check them."""
    if kind not in KINDS:
        raise Stop(f"STOP: kind must be one of {sorted(KINDS)}")
    schema, run_id, nodes, asm_schema, family = KINDS[kind]
    summary = Path(summary)
    if not summary.is_absolute() or any(p.is_symlink() for p in [summary, *summary.parents]):
        raise Stop(f"STOP: {summary} must be an absolute path without symlinks")
    if not summary.is_file():
        raise Stop(f"STOP: {summary} is not a file")
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
    run_dir = summary.parent
    asm_path, runs_path = run_dir / "ASSEMBLY.json", run_dir / "runs.jsonl"
    N._refuse_sealed(summary, asm_path, runs_path)
    if not asm_path.is_file() or not runs_path.is_file() or asm_path.is_symlink() or runs_path.is_symlink():
        raise Stop(f"STOP: {run_dir} is not an assembled G.1b run directory (ASSEMBLY.json, runs.jsonl as regular "
                   f"files)")
    asm_raw, runs_raw = asm_path.read_bytes(), runs_path.read_bytes()
    asm = json.loads(asm_raw)
    if s.get("assembly_sha256") != N._sha(asm_raw) or asm.get("schema") != asm_schema or \
            asm.get("run_id") != run_id or asm.get("runs_sha256") != N._sha(runs_raw):
        raise Stop(f"STOP: {summary} is not bound to its directory's ASSEMBLY.json ({asm_schema}) and runs.jsonl")
    rows = N.g1b_rows(runs_raw, str(runs_path))                       # D6 A: no record at a seed in 7001-7010
    for node in sorted(nodes):                                         # what g5_noise.derive checks on the copies
        v = s["verdicts"].get(node) or {}
        n_edits, pj = v.get("n_edits"), v.get("paired_joint_n")
        if isinstance(n_edits, bool) or not isinstance(n_edits, int) or n_edits < 1 or not isinstance(pj, list):
            raise Stop(f"STOP: {summary}: the verdict for {node} has no n_edits / paired_joint_n (D6 A, D18)")
        if N.edit_stats(rows, node, n_edits)[1] != pj:
            raise Stop(f"STOP: {node}: the paired-seed counts in {runs_path} differ from the summary's paired_joint_n")
    out = {"kind": kind, "summary": summary, "raw": raw, "sha256": L._sha_file(summary), "run_id": run_id,
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
        gate_path = run_dir / "crosscheck_gate.json"
        if not gate_path.is_file() or gate_path.is_symlink():
            raise Stop(f"STOP: {run_dir} has no crosscheck_gate.json (not assembled through the cross-check gate)")
        gate = json.loads(gate_path.read_text())
        problems = [k for k, ok in (
            ("schema", gate.get("schema") == X.GATE_SCHEMA),
            ("nodes", sorted(gate.get("nodes") or {}) == sorted(xc["nodes"])),
            ("g1b_spec_sha256", gate.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"]),
            ("crosscheck_run_id", gate.get("crosscheck_run_id") == xc["run_id"]),
            ("assembly_json_sha256", gate.get("assembly_json_sha256") == L._sha_file(asm_path)),
            ("runs_jsonl_sha256", gate.get("runs_jsonl_sha256") == L._sha_file(runs_path))) if not ok]
        if problems:
            raise Stop(f"STOP: {gate_path} does not bind this assembly and the TASL-7 nodes: {problems}")
        out.update(gate=gate_path, gate_raw=gate_path.read_bytes(), gate_sha256=L._sha_file(gate_path))
    return out


def copy_summary(spec: dict, kind: str, summary: Path, dest: str, *, repo: Path | None = None) -> dict:
    """Copy one sealed G.1b summary (and, for the seven nodes, its cross-check gate record beside it) into the
    repository at ``dest`` (a directory under docs/r1/reports/, new), byte-identically, with ``COPY_RECORD.json``."""
    repo = Path(repo or S.REPO_ROOT)
    if not S._rel_ok(dest) or not dest.startswith("docs/r1/reports/"):
        raise Stop("STOP: dest must be a repository path under docs/r1/reports/")
    src = check_source(spec, kind, summary)
    target = repo / dest
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists()):
        raise Stop(f"STOP: {target} exists (a REL-T1-G1B copy is written once)")
    target.mkdir(parents=True)
    rel = f"{dest.rstrip('/')}/summary.json"
    shutil.copyfile(src["summary"], repo / rel)
    if L._sha_file(repo / rel) != src["sha256"]:
        raise Stop("STOP: the copy differs from the sealed summary")
    base = dest.rstrip('/')
    runs = {"assembly_copy": f"{base}/ASSEMBLY.json", "assembly_sha256": src["assembly_sha256"],
            "runs_copy": f"{base}/runs.jsonl", "runs_sha256": src["runs_sha256"]}
    for key, raw_key in (("assembly_copy", "assembly_raw"), ("runs_copy", "runs_raw")):   # D6 A
        with (repo / runs[key]).open("xb") as fh:
            fh.write(src[raw_key])
    if L._sha_file(repo / runs["assembly_copy"]) != runs["assembly_sha256"] or \
            L._sha_file(repo / runs["runs_copy"]) != runs["runs_sha256"]:
        raise Stop("STOP: the ASSEMBLY.json / runs.jsonl copies differ from the sealed run's")
    record = {"schema": COPY_SCHEMA, "label": G.ENGINEERING_ONLY, "kind": kind, "authority": "REL-T1-G1B "
              "(R1-SWEEP2-RELEASE-DECISIONS) with its copy list amended by R1-T1-FEAT-DECISIONS D6 A; PRE-DELTA A",
              "run_id": src["run_id"], "nodes": src["nodes"],
              "qualifies_D21": src["qualifies_D21"], "sealed_path": str(src["summary"]), "copy": rel,
              "sha256": src["sha256"], **runs, "sealed_assembly_path": str(src["assembly"]),
              "sealed_runs_path": str(src["runs"])}
    needles = [runs["assembly_copy"], runs["assembly_sha256"], runs["runs_copy"], runs["runs_sha256"]]
    if kind == "seven":
        gate_rel = f"{dest.rstrip('/')}/crosscheck_gate.json"
        shutil.copyfile(src["gate"], repo / gate_rel)
        if L._sha_file(repo / gate_rel) != src["gate_sha256"]:
            raise Stop("STOP: the gate copy differs from the sealed gate record")
        record.update(gate_copy=gate_rel, gate_sha256=src["gate_sha256"], gate_sealed_path=str(src["gate"]))
        record["spec_fields"] = {"noise_floor.seven.copy": rel, "noise_floor.seven.sha256": src["sha256"],
                                 "noise_floor.seven.sealed_path": str(src["summary"]),
                                 "noise_floor.seven.gate_copy": gate_rel,
                                 "noise_floor.seven.gate_sha256": src["gate_sha256"],
                                 **{f"noise_floor.seven.{k}": v for k, v in runs.items()}}
        record["review_must_name"] = [rel, src["sha256"], str(src["summary"]), gate_rel, src["gate_sha256"], *needles]
    else:
        record["completion_record_lines"] = [f"noise_floor_copy: {rel} sha256 {src['sha256']}",
                                             f"g1b_sealed_summary: {src['summary']} sha256 {src['sha256']}"]
        record["spec_fields_under_arpend_b"] = {"noise_floor.ar.copy": rel, "noise_floor.ar.sha256": src["sha256"],
                                                "noise_floor.ar.sealed_path": str(src["summary"]),
                                                **{f"noise_floor.ar.{k}": v for k, v in runs.items()}}
        record["review_must_name"] = [rel, src["sha256"], str(src["summary"]), *needles]
    record["d21_verdict"] = {n: "qualifies" if q else "does_not_qualify" for n, q in src["qualifies_D21"].items()}
    with (target / "COPY_RECORD.json").open("x") as fh:
        fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record
