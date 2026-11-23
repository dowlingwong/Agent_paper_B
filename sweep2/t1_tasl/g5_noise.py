"""The T1 noise input of the gate run: σ_node and D18's δ_n per T1 node, from the REL-T1-G1B copies of each node's
G.1b run (ARMS-T1FEAT A; the G.5 code unit part 3b-2 report §5 item 3; R1-T1-FEAT-DECISIONS D6 A and D6-σ B).
AI-assisted (Claude). ENGINEERING_ONLY: G.1b noise-floor data only; no label is read.

Authority: the frozen preregistration's PRE-DELTA A ("D18's δ_n unscaled"; "T1 from each node's sealed G.1b summary",
read under REL-T1-G1B as the summary on the T1 host, copied out of the sealed tree by a reviewed step with its sha256
before the T1 train/dev row); D18 (δ_n = max(0.002, 0.25 × median paired sd(Δ̂)) per node, in metric units);
R1-T1-FEAT-DECISIONS, which decides the ARMS-T1FEAT report's §5: **D6 A** (REL-T1-G1B's copy list is amended: each
G.1b run's ``ASSEMBLY.json`` and ``runs.jsonl`` are copied beside the summary copy by the reviewed copy step,
``g5_relcopy``) and **D6-σ B** (T1's σ_node by T0's definition).

**What the gate input builder takes** (``r1.c3.gate_input_builder.build``'s ``noise``): {node: {"delta_n",
"sigma_node"}}; it refuses a node without a positive δ_n and a node whose table rows carry another σ_node. For T0 the
caller takes both from ``r1.c3.dataset.noise_table`` on the pinned noise source (σ_node: median sd_joint over material
edits; δ_n: max(0.002, 0.25 × median sd_joint over all edits)). ``builder_noise`` gives T1 the same form, and
``merge_noise`` joins the two tiers.

**One computation, two users.** ``node_delta`` computes, from one node's bound G.1b run (``ASSEMBLY.json``,
``runs.jsonl``), by ``r1.noise.e1_report``'s definitions: per edit k the sd (numpy, ddof 1) over the joint seeds of
m(c_k, s) − m(c0, s), from successful runs with a metric, at least three paired seeds; ``material`` as in
``e1_report`` (resolved: |Δ̂_J| > 2 se, or Δ̂_J ≠ 0 when se = 0; and |Δ̂_J| ≥ 0.002). From these:
- **σ_node (D6-σ B)** is ``dataset.noise_table``'s rule: the median ``sd_joint`` over material edits, or over all
  edits with an sd if none is material (``sigma_node_t0_definition``);
- **δ_n** is D18 unscaled (PRE-DELTA A): max(0.002, 0.25 × the median ``sd_joint`` over all edits with an sd).
``g5_assemble.noise_by_node`` (the table's σ_node, spec field ``noise_floor.t1_sigma_node: "t0_definition"``) calls
``node_delta`` on the committed copies beside each cited summary copy, and ``derive`` takes its values from
``noise_by_node``; so the noise record's σ_node and the table rows' ``sigma_node`` are one value by construction. The
G.1b summary's ``sigma_joint`` (the sd of the baseline's own runs over the joint seeds, the 3b-2 default, D6-σ A) is
no longer used for σ_node; it is reported beside it for disclosure only.

**Binding.** The summary copy's ``assembly_sha256`` must be the sha256 of the ``ASSEMBLY.json`` beside it, and that
file's ``runs_sha256`` the sha256 of the ``runs.jsonl`` beside it; the edit count and every edit's paired-seed count
must equal the summary's ``n_edits`` and ``paired_joint_n``.

**Inputs and guards.** Under D6 A ``derive`` reads only the reviewed repository copies (the directory of each summary
copy). Like ``dataset.noise_table``, every read goes through ``r1.c3.analysis_guard.refuse_sealed``'s check
(``r1_sealed`` paths, the label seal, are refused). ``g1b_rows`` refuses a ``runs.jsonl`` with any record whose seed
(``seed``, ``train_seed``, ``split_seed`` or any other ``*_seed`` field) lies in the audit block 7001–7010 (the G.5
label and evaluation seeds): G.1b runs use the seeds 1001–1030, 2001–2030, 3001–3030 and default runs (no seed). The
copy step (``g5_relcopy``) applies the same check before it copies anything.
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
import g5_tasl as S  # noqa: E402
# g5_assemble imports this module (noise_by_node); derive imports g5_assemble when it is called.

Stop = G.Stop
NOISE_SCHEMA = "g5_t1_noise/2"          # /2: σ_node by T0's definition (D6-σ B); /1 carried sigma_joint (D6-σ A)
T1_SIGMA_NODE = "t0_definition"         # the spec's noise_floor.t1_sigma_node (R1-T1-FEAT-DECISIONS D6-σ B)
AUDIT_SEEDS = range(7001, 7011)         # the G.5 label and evaluation seeds (K = 10); never in a G.1b run
D18_FLOOR = 0.002
D18_SCALE = 0.25
MIN_EFFECT = 0.002      # e1_report.MIN_EFFECT: a material edit has |delta_hat_J| >= 0.002 (metric units)
MIN_PAIRED = 3          # e1_report: fewer than three paired joint seeds is "insufficient runs" (no sd)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sd(x: list[float]) -> float:
    """``e1_report._sd`` (numpy, ddof 1), so the value is bit-identical to the pinned report's ``sd_joint``."""
    import numpy as np
    return float(np.std(np.asarray(x, dtype=float), ddof=1))


def _refuse_sealed(*paths) -> None:
    """``r1.c3.analysis_guard.refuse_sealed``, copied so that no repository path is put on ``sys.path`` (a test checks
    that both refuse the same paths): a lexical or symlink-resolved ``r1_sealed`` component is refused before
    opening."""
    for raw in paths:
        if raw is None:
            continue
        path = Path(raw).expanduser()
        if any(part.casefold() == "r1_sealed" for part in (*path.parts, *path.resolve().parts)):
            raise RuntimeError("STOP: r1_sealed paths are not analysis inputs")


def g1b_rows(runs_raw: bytes, where: str) -> list[dict]:
    """The records of a G.1b ``runs.jsonl``. A record with a seed in the audit block 7001–7010 (``seed`` or any
    ``*_seed`` field) is refused: G.1b noise-floor runs use the seeds 1001–1030, 2001–2030, 3001–3030 and default runs
    without a seed, so such a record is not a G.1b noise-floor run (the label and evaluation seeds are never read
    here). The STOP names the file, not the record or its values."""
    rows = []
    for line in runs_raw.decode().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if not isinstance(r, dict):
            raise Stop(f"STOP: {where} holds a line that is not a JSON object (not a G.1b runs.jsonl)")
        seeds = [v for k, v in r.items() if (k == "seed" or k.endswith("_seed")) and isinstance(v, int)
                 and not isinstance(v, bool)]
        if any(v in AUDIT_SEEDS for v in seeds):
            raise Stop(f"STOP: {where} holds a record with a seed in the audit block 7001-7010 (G.5 label and "
                       f"evaluation seeds); a G.1b runs.jsonl holds noise-floor runs at the G.1b seeds only")
        rows.append(r)
    return rows


def edit_stats(rows: list[dict], node: str, n_edits: int) -> tuple[list[dict], list[int]]:
    """Per edit c1..c_n of ``node`` with at least ``MIN_PAIRED`` paired joint seeds: ``e1_report``'s ``sd_joint`` and
    ``material``; and every edit's paired-seed count."""
    joint: dict[tuple, float] = {}
    for r in rows:
        if r.get("node") != node or r.get("condition") != "joint" or not r.get("success") or r.get("metric") is None:
            continue
        joint[(r["config"], (r.get("train_seed"), r.get("split_seed")))] = float(r["metric"])
    import numpy as np
    stats, counts = [], []
    for k in range(1, n_edits + 1):
        seeds = sorted((s for (c, s) in joint if c == "c0" and (f"c{k}", s) in joint), key=str)
        counts.append(len(seeds))
        if len(seeds) >= MIN_PAIRED:
            dj = np.array([joint[(f"c{k}", s)] - joint[("c0", s)] for s in seeds])
            delta, sd = float(dj.mean()), _sd(dj)
            se = sd / math.sqrt(dj.size)
            resolved = bool(abs(delta) > 2 * se) if se > 0 else bool(delta != 0)
            stats.append({"sd_joint": sd, "material": bool(resolved and abs(delta) >= MIN_EFFECT)})
    return stats, counts


def paired_sds(rows: list[dict], node: str, n_edits: int) -> tuple[list[float], list[int]]:
    """Per edit: ``e1_report``'s ``sd_joint`` (edits with at least ``MIN_PAIRED`` paired seeds), and the counts."""
    stats, counts = edit_stats(rows, node, n_edits)
    return [e["sd_joint"] for e in stats], counts


def node_noise(node: str, summary_raw: bytes, asm_raw: bytes, runs_raw: bytes, where: str) -> dict:
    """σ_node by T0's definition (D6-σ B) and D18's δ_n of one node from the bytes of its G.1b run's ``ASSEMBLY.json``
    and ``runs.jsonl``, bound to the summary copy's bytes (``where`` names the run for the STOP texts). Used by
    ``node_delta`` (files) and by the switch's pre-check (``g5_tasl.noise_precheck``, bytes on published main). A
    non-finite sd or median is a STOP (on finite inputs the values are unchanged)."""
    s = json.loads(summary_raw)
    v = (s.get("verdicts") or {}).get(node) or {}
    try:
        asm = json.loads(asm_raw)
    except ValueError:
        asm = None
    if not isinstance(asm, dict) or s.get("assembly_sha256") != _sha(asm_raw) or \
            asm.get("runs_sha256") != _sha(runs_raw):
        raise Stop(f"STOP: {where} is not the run of the summary copy for {node} (assembly_sha256 / runs_sha256)")
    n_edits, pj = v.get("n_edits"), v.get("paired_joint_n")
    if isinstance(n_edits, bool) or not isinstance(n_edits, int) or n_edits < 1 or not isinstance(pj, list):
        raise Stop(f"STOP: the summary's verdict for {node} has no n_edits / paired_joint_n")
    rows = g1b_rows(runs_raw, where)
    stats, counts = edit_stats(rows, node, n_edits)
    sds = [e["sd_joint"] for e in stats]
    if counts != pj:
        raise Stop(f"STOP: {node}: the paired-seed counts from runs.jsonl {counts} differ from the summary's "
                   f"paired_joint_n {pj}")
    if not sds:
        raise Stop(f"STOP: {node}: no edit has {MIN_PAIRED} paired joint seeds (D18 needs a median paired sd)")
    import numpy as np
    med = float(np.median(sds))                 # e1_report's median_sd_joint
    material = [e["sd_joint"] for e in stats if e["material"]]
    sigma_t0 = float(np.median(material or sds))  # dataset.noise_table's sigma_node: T1's σ_node (D6-σ B)
    if not all(math.isfinite(x) for x in sds) or not math.isfinite(med) or not math.isfinite(sigma_t0):
        raise Stop(f"STOP: {node}: a non-finite paired sd or median in {where} (D18 and σ_node need finite values)")
    return {"delta_n": max(D18_FLOOR, D18_SCALE * med), "median_paired_sd": med,
            "sigma_node_t0_definition": sigma_t0, "n_material_edits": len(material), "n_edits": n_edits,
            "n_edits_with_sd": len(sds), "paired_joint_n": counts,
            "assembly_sha256": _sha(asm_raw), "runs_sha256": _sha(runs_raw)}


def check_usable(node: str, st: dict) -> None:
    """σ_node by T0's definition positive and finite, δ_n finite (the table and the gate input need both)."""
    sigma, delta = st["sigma_node_t0_definition"], st["delta_n"]
    if not math.isfinite(sigma) or sigma <= 0:
        raise Stop(f"STOP: {node} has no positive σ_node by T0's definition (D6-σ B) in its G.1b run")
    if not math.isfinite(delta) or delta <= 0:
        raise Stop(f"STOP: {node} has no finite positive δ_n (D18) from its G.1b run")


def node_delta(node: str, summary_raw: bytes, run_dir: Path) -> dict:
    """``node_noise`` of one node from its G.1b run directory (under D6 A the REL-T1-G1B copy directory), every path
    passing the ``refuse_sealed`` check before it is opened. No absolute path is returned (the values enter the
    table's ``build.json``, which must not depend on where the checkout lies)."""
    run_dir = Path(run_dir)
    asm_path, runs_path = run_dir / "ASSEMBLY.json", run_dir / "runs.jsonl"
    _refuse_sealed(run_dir, asm_path, runs_path)
    if not asm_path.is_file() or not runs_path.is_file():
        raise Stop(f"STOP: {run_dir} is not an assembled G.1b run directory (ASSEMBLY.json, runs.jsonl)")
    return node_noise(node, summary_raw, asm_path.read_bytes(), runs_path.read_bytes(), str(run_dir))


def derive(spec: dict, row: dict, run_dirs: dict | None = None, *, ar_record=None) -> dict:
    """The T1 noise record of the nodes the train/dev row cites, from ``g5_assemble.noise_by_node`` (the function the
    table uses): σ_node by T0's definition and δ_n by D18, both from the REL-T1-G1B copies of each node's G.1b run
    beside its summary copy (D6 A), every value bound to the copies' sha256s. ``run_dirs`` ({node: directory}) is
    optional; given, each must be the copy directory of the node's summary (D6 A: no other directory is read)."""
    import g5_assemble as A                                  # noqa: PLC0415 - g5_assemble imports this module
    noise = A.noise_by_node(spec, row, ar_record=ar_record)
    if run_dirs is not None:
        if set(run_dirs) != set(noise):
            raise Stop(f"STOP: run directories are given for {sorted(run_dirs)}, the row cites {sorted(noise)}")
        for node, d in sorted(run_dirs.items()):
            if Path(d).resolve() != (S.REPO_ROOT / noise[node]["runs_copy"]).parent.resolve():
                raise Stop(f"STOP: {node}: under D6 A (R1-T1-FEAT-DECISIONS) the G.1b run is read from the REL-T1-G1B "
                           f"copy beside the summary copy ({Path(noise[node]['runs_copy']).parent}), not from {d}")
    nodes = {}
    for node, n in sorted(noise.items()):
        if n["sigma_node"] != n["sigma_node_t0_definition"] or n["sigma_node_rule"] != T1_SIGMA_NODE:
            raise Stop(f"STOP: {node}: the table's sigma_node is not T0's definition (D6-σ B)")
        nodes[node] = dict(n)
    return {"schema": NOISE_SCHEMA, "label": G.ENGINEERING_ONLY,
            "rule": "sigma_node: dataset.noise_table's definition (median sd_joint over material edits, over all "
                    "edits with an sd if none is material; e1_report's material) on the REL-T1-G1B copy of the node's "
                    "G.1b runs.jsonl, as g5_assemble.noise_by_node gives it to the table (D6-sigma B); delta_n: D18, "
                    "max(0.002, 0.25 x median over edits of the joint paired sd), unscaled (PRE-DELTA A); "
                    "sigma_joint: the G.1b summary's, disclosure only",
            "t1_sigma_node": T1_SIGMA_NODE, "decisions_row": "R1-T1-FEAT-DECISIONS",
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
