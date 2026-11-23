"""The T1 noise input of the gate run: σ_node and D18's δ_n per T1 node, bound by sha256 to the REL-T1-G1B copies
(ARMS-T1FEAT A; the G.5 code unit part 3b-2 report §5 item 3). AI-assisted (Claude). ENGINEERING_ONLY: G.1b noise-floor
data only; no label is read.

Authority: the frozen preregistration's PRE-DELTA A ("D18's δ_n unscaled"; "T1 from each node's sealed G.1b summary",
read under REL-T1-G1B as the summary on the T1 host, copied out of the sealed tree by a reviewed step with its sha256
before the T1 train/dev row); D18 (δ_n = max(0.002, 0.25 × median paired sd(Δ̂)) per node, in metric units).

**What the gate input builder takes** (``r1.c3.gate_input_builder.build``'s ``noise``): {node: {"delta_n",
"sigma_node"}}; it refuses a node without a positive δ_n and a node whose table rows carry another σ_node. For T0 the
caller takes both from ``r1.c3.dataset.noise_table`` on the pinned noise source (σ_node: median sd_joint over material
edits; δ_n: max(0.002, 0.25 × median sd_joint over all edits)). ``builder_noise`` gives T1 the same form, and
``merge_noise`` joins the two tiers.

**σ_node** is taken by ``g5_assemble.noise_by_node``, the function the G.5 table itself uses: each node's G.1b summary
as the train/dev row cites it, checked against the spec's REL-T1-G1B copy (path and sha256), its ``sigma_joint``. So the
value is the table rows' ``sigma_node`` by construction.

**δ_n.** The G.1b summary carries ``sigma_joint`` (the sd of the baseline's own runs over the joint seeds),
``sigma_train``, ``sigma_split``, ``n_edits`` and the per-edit paired-seed counts ``paired_joint_n``, but not the median
paired sd over the edits that D18 names (part 3b-2 report §5 item 3). That median is computed here from the G.1b run's
``runs.jsonl``, by ``r1.noise.e1_report``'s definitions (per edit k, the sd (ddof 1) over the joint seeds of
m(c_k, s) − m(c0, s), from successful runs with a metric, at least three paired seeds; the median over the edits that
have it), and bound to the copy: the copy's ``assembly_sha256`` is the run directory's ``ASSEMBLY.json``, whose
``runs_sha256`` is its ``runs.jsonl``; the edit count and every edit's paired-seed count must equal the summary's
``n_edits`` and ``paired_joint_n``. Reading ``runs.jsonl`` goes beyond the copies REL-T1-G1B names (the summaries
only); the report lists this as an author decision (a reviewed copy of ``runs.jsonl`` beside the summary copy, or a
run of ``derive`` on the T1 host against the sealed G.1b tree).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_tasl as G  # noqa: E402
import g5_assemble as A  # noqa: E402
import g5_tasl as S  # noqa: E402

Stop = G.Stop
NOISE_SCHEMA = "g5_t1_noise/1"
D18_FLOOR = 0.002
D18_SCALE = 0.25
MIN_PAIRED = 3          # e1_report: fewer than three paired joint seeds is "insufficient runs" (no sd)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sd(x: list[float]) -> float:
    """``e1_report._sd`` (numpy, ddof 1), so the value is bit-identical to the pinned report's ``sd_joint``."""
    import numpy as np
    return float(np.std(np.asarray(x, dtype=float), ddof=1))


def paired_sds(rows: list[dict], node: str, n_edits: int) -> tuple[list[float], list[int]]:
    """Per edit c1..c_n of ``node``: the sd of the joint-condition paired differences against c0 (``e1_report``'s
    ``sd_joint``; only edits with at least ``MIN_PAIRED`` paired seeds have one), and every edit's paired-seed count."""
    joint: dict[tuple, float] = {}
    for r in rows:
        if r.get("node") != node or r.get("condition") != "joint" or not r.get("success") or r.get("metric") is None:
            continue
        joint[(r["config"], (r.get("train_seed"), r.get("split_seed")))] = float(r["metric"])
    sds, counts = [], []
    for k in range(1, n_edits + 1):
        seeds = sorted((s for (c, s) in joint if c == "c0" and (f"c{k}", s) in joint), key=str)
        counts.append(len(seeds))
        if len(seeds) >= MIN_PAIRED:
            sds.append(_sd([joint[(f"c{k}", s)] - joint[("c0", s)] for s in seeds]))
    return sds, counts


def node_delta(node: str, summary_raw: bytes, run_dir: Path) -> dict:
    """D18's δ_n of one node from its G.1b run directory, bound to the summary copy's bytes."""
    s = json.loads(summary_raw)
    v = (s.get("verdicts") or {}).get(node) or {}
    run_dir = Path(run_dir)
    asm_path, runs_path = run_dir / "ASSEMBLY.json", run_dir / "runs.jsonl"
    if not asm_path.is_file() or not runs_path.is_file():
        raise Stop(f"STOP: {run_dir} is not an assembled G.1b run directory (ASSEMBLY.json, runs.jsonl)")
    asm_raw, runs_raw = asm_path.read_bytes(), runs_path.read_bytes()
    asm = json.loads(asm_raw)
    if s.get("assembly_sha256") != _sha(asm_raw) or asm.get("runs_sha256") != _sha(runs_raw):
        raise Stop(f"STOP: {run_dir} is not the run of the summary copy for {node} (assembly_sha256 / runs_sha256)")
    n_edits, pj = v.get("n_edits"), v.get("paired_joint_n")
    if isinstance(n_edits, bool) or not isinstance(n_edits, int) or n_edits < 1 or not isinstance(pj, list):
        raise Stop(f"STOP: the summary's verdict for {node} has no n_edits / paired_joint_n")
    rows = [json.loads(x) for x in runs_raw.decode().splitlines() if x.strip()]
    sds, counts = paired_sds(rows, node, n_edits)
    if counts != pj:
        raise Stop(f"STOP: {node}: the paired-seed counts from runs.jsonl {counts} differ from the summary's "
                   f"paired_joint_n {pj}")
    if not sds:
        raise Stop(f"STOP: {node}: no edit has {MIN_PAIRED} paired joint seeds (D18 needs a median paired sd)")
    import numpy as np
    med = float(np.median(sds))                 # e1_report's median_sd_joint
    return {"delta_n": max(D18_FLOOR, D18_SCALE * med), "median_paired_sd": med, "n_edits": n_edits,
            "n_edits_with_sd": len(sds), "paired_joint_n": counts, "run_dir": str(run_dir),
            "assembly_sha256": _sha(asm_raw), "runs_sha256": _sha(runs_raw)}


def derive(spec: dict, row: dict, run_dirs: dict, *, ar_record=None) -> dict:
    """The T1 noise record of the nodes the train/dev row cites: σ_node as the table takes it, δ_n by D18 from each
    node's G.1b run (``run_dirs``: {node: the run directory of its summary}), every value bound to the copy's sha256."""
    noise = A.noise_by_node(spec, row, ar_record=ar_record)
    if set(run_dirs) != set(noise):
        raise Stop(f"STOP: run directories are given for {sorted(run_dirs)}, the row cites {sorted(noise)}")
    nodes = {}
    for node, n in sorted(noise.items()):
        raw = (S.REPO_ROOT / n["summary"]).read_bytes()
        if _sha(raw) != n["summary_sha256"]:
            raise Stop(f"STOP: {n['summary']} changed after its check")
        nodes[node] = {"sigma_node": n["sigma_node"], "summary": n["summary"], "summary_sha256": n["summary_sha256"],
                       **node_delta(node, raw, run_dirs[node])}
    return {"schema": NOISE_SCHEMA, "label": G.ENGINEERING_ONLY,
            "rule": "sigma_node: the cited G.1b summary's sigma_joint (g5_assemble.noise_by_node); delta_n: D18, "
                    "max(0.002, 0.25 x median over edits of the joint paired sd), unscaled (PRE-DELTA A)",
            "spec_run_id": spec["run_id"],
            "train_dev_row": {"row_id": row.get("row_id"), "decision_sha256": row.get("decision_sha256")},
            "nodes": nodes}


def write_record(record: dict, dest: str, *, repo: Path | None = None) -> str:
    """Write the record once at ``dest`` (a repository path under docs/r1/reports/); returns its sha256."""
    repo = Path(repo or S.REPO_ROOT)
    if not S._rel_ok(dest) or not dest.startswith("docs/r1/reports/") or not dest.endswith(".json"):
        raise Stop("STOP: dest must be a .json repository path under docs/r1/reports/")
    raw = (json.dumps(record, indent=1, sort_keys=True, allow_nan=False) + "\n").encode()
    path = repo / dest
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as fh:
        fh.write(raw)
    return _sha(raw)


def builder_noise(record: dict, *, sha256: str | None = None, raw: bytes | None = None) -> dict:
    """{node: {"delta_n", "sigma_node"}} for ``gate_input_builder.build`` from a T1 noise record (given its bytes, they
    must hash to ``sha256``)."""
    if raw is not None:
        if sha256 is None or _sha(raw) != sha256:
            raise Stop("STOP: the T1 noise record differs from the sha256 it is cited with")
        record = json.loads(raw)
    if record.get("schema") != NOISE_SCHEMA:
        raise Stop(f"STOP: not a {NOISE_SCHEMA} record")
    out = {}
    for node, n in sorted(record["nodes"].items()):
        d, s = n.get("delta_n"), n.get("sigma_node")
        if not all(isinstance(x, float) and math.isfinite(x) and x > 0 for x in (d, s)):
            raise Stop(f"STOP: {node} has no positive finite delta_n and sigma_node")
        out[node] = {"delta_n": d, "sigma_node": s}
    return out


def merge_noise(t0: dict, t1: dict) -> dict:
    """The builder's ``noise`` over both tiers: T0 from ``dataset.noise_table`` (its delta_n and sigma_node), T1 from
    ``builder_noise``. A node in both is refused."""
    both = sorted(set(t0) & set(t1))
    if both:
        raise Stop(f"STOP: {both} have a T0 and a T1 noise entry")
    out = {n: {"delta_n": float(v["delta_n"]), "sigma_node": float(v["sigma_node"])} for n, v in t0.items()}
    out.update({n: dict(v) for n, v in t1.items()})
    return out
