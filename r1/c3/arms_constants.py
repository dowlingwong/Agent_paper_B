"""A1/A2 constants fitter: the per-node constant forecasts of the rule arms A1 and A2, fitted exactly as
``gate_input_builder.fit_a2`` fits A2 (PRE-A2 C), on the released dev label block of the gate sources.

AI-assisted (Claude, subagent, 23 Nov 2026). Tier E (R1-PROCESS-TIERS): reviewed, and its sha256 entered in the
post-freeze reads amendment's final block (A§13, ``constants_fitter_sha256``), before the arms-frozen record is
committed (A§12 item 22: no fallback).

**One unit for two documents.**

* The post-freeze reads amendment (``C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_*``), A§8 unit 1, A§3.1, A§3.2, A§9: the
  arms-frozen record's ``rule_arms.A1`` and ``rule_arms.A2`` vectors, for all eight T0 nodes (the PRE-WDBC sensitivity
  set) and every node of the frozen T1 set (written into the record by ``arms_freeze.postfreeze_fields``).
* The D.3 pre-declaration draft (``D3_PREDECLARATION_DRAFT_20261122.md``), gap G2 of §12, the A1 and A2 part of §5.0:
  the seven D.3 nodes' vectors. Each node's vectors use only that node's rows, so fitting eight T0 nodes and the T1
  nodes leaves the seven D.3 nodes' vectors bitwise unchanged (a test shows it). The LADDER η search of D.3 §5.6 is
  **not** in this unit.

**What it fits.** Per node n:

* A1, ``arms.ConstantPrior``: the weighted mean soft label c_n of the node's labelled dev rows, no-ops included (no
  rule layer; offline there is no verify).
* A2, ``arms.RulesPrior`` as ``gate_input_builder.fit_a2`` fits it: the same rows without the rule-skipped ones
  (no-ops, within-campaign duplicates), bin 0 zeroed and renormalised. The A2 vectors are ``fit_a2``'s own output: this
  module builds the item list ``fit_a2`` takes and calls it. A1 is fitted on the row list ``fit_a2`` builds from the
  same items (``fit_rows``, a copy of its comprehension; a test checks the copy reproduces ``fit_a2`` bitwise).

The rows are those ``fit_a2`` uses at step 6 (amendment A§3.1): the dev instances' label block of the gate sources
(sweep 2 for the T0 nodes, G.5 for the frozen T1 nodes), the full dev population of every memory mode in the table,
built by ``arms_freeze.training_rows`` (the builder's construction, tested against ``_prepare``: a no-op gets the
inert soft label; an ``audit`` label gets ``soft_label(Δ_label, None, σ_node, "pooled_node", k_label)``; within-campaign
duplicates and ``divergent`` labels have no soft label and do not enter), weights 1, **in ``proposal_id`` order across
sources** as ``_prepare`` sorts them (``arms._wmean`` sums in row order, so the order is what makes the vectors bitwise
equal to ``fit_a2``'s). No pooled fallback: a required node without a labelled non-inert dev proposal is refused, as
the builder refuses it; rows of a node outside the required set are refused.

**What it reads, and refuses.** For each gate source given (``sweep2`` always; ``g5`` exactly when the frozen T1 set is
non-empty; ``sweep1`` is refused: PRE-A2 C fits on the gate sources only):

* the receipted train/dev partition through ``arms_freeze.load_traindev``: ``release.traindev_labels`` with the receipt
  sha256 pinned (``release.open_partition`` re-checks the receipt, its row and the P3 membership of every row); a
  receipt that is not train/dev or counts evaluation rows, a label row with an evaluation field or evaluation seeds,
  and a label row of a P3 test instance are refused;
* the released table through ``arms_freeze.load_table_rows`` (``dataset.load_table``, which calls
  ``analysis_guard.guard_table``); a table row carrying a label or evaluation value is refused; ``proposals.jsonl`` must
  be the table the receipt released (``inputs.proposals_sha256``) and, for sweep 2, the addendum's pin
  ``SWEEP2_PROPOSALS_SHA256`` (D.3 draft §5.0: a mismatch with either is a STOP);
* raw label blocks, evaluation blocks, test partitions and run logs are refused by name before anything is opened
  (``arms_freeze.refuse_input_path``).

Table rows and label rows are **filtered to P3 dev instances first** (D.3 draft §5.0), from the pinned split file;
train and test rows enter no computation.

**What it writes.** One JSON file, schema ``r1_c3_rule_arm_constants/v1``, written once: per node the A1 and A2 12-bin
vectors (JSON floats round-trip exactly), σ_node, the dev instances and row counts (no label value beyond the two
vectors); the fitter's path, sha256 and code commit; per source the receipt, train/dev partition, label block and table
sha256s; the split file's and the builder's sha256s; the T1 setting. The arms-frozen record pins it by sha256; the D.3
pre-declaration can pin the same file.

CLI (run by the cluster agent under ``docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md``, step 4b)::

    python -m r1.c3.arms_constants fit --release-root sweep2=DIR --receipt sweep2=SHA --table sweep2=DIR \\
        [--release-root g5=DIR --receipt g5=SHA --table g5=DIR --t1 T1.json] --out FILE
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from r1.c3 import arms_freeze as AF
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split
from r1.c3.arms import ConstantPrior, is_duplicate, is_noop
from r1.c3.labels import INERT, N_BINS

SCHEMA = "r1_c3_rule_arm_constants/v1"
SCHEMA_PREFIX = "r1_c3_rule_arm_constants/"
FITTER_PATH = "r1/c3/arms_constants.py"
SPLIT_PATH = "r1/c3/splits/c3_p3_split_v1.json"
BUILDER_PATH = "r1/c3/gate_input_builder.py"
FIT_POPULATION = "dev label block, full dev population, gate sources"       # amendment A§9
A1_OFFLINE = "no rule layer; no verify offline"                              # amendment A§9
RULES = {"A1": "arms.ConstantPrior on the rows gate_input_builder.fit_a2 builds; no rule layer; no verify offline",
         "A2": "gate_input_builder.fit_a2 (arms.RulesPrior), PRE-A2 C"}
D3_NODES = B.SEVEN_T0                       # D.3 draft §14 d3_nodes (the seven C3b nodes)
# D.3 draft §5.0: the sweep-2 table, copied from docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md
# (table_proposals_sha256); also the sweep-2 train/dev receipt's inputs.proposals_sha256 (runbook I-P4).
SWEEP2_PROPOSALS_SHA256 = "379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9"
SUM_TOL = 1e-9
_HEX = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")


def _refuse(msg: str):
    raise AF.ArmsFreezeError(msg)


# ============================================================================================== rows

def dev_only(rows, labels, assign) -> tuple[list[dict], list[dict]]:
    """Table rows and label rows of P3 **dev** instances only, selected before any other use (D.3 draft §5.0). Label
    rows are first checked as ``arms_freeze`` checks released label rows (no evaluation field or seed, no test
    instance); a table row outside the split file is refused (the builder's ``_instance``)."""
    AF.check_label_rows(labels, assign)
    keep = []
    for r in rows:
        try:
            _, split = B._instance(r, assign)
        except B.BuilderError as exc:
            raise AF.ArmsFreezeError(str(exc)) from exc
        if split == "dev":
            keep.append(r)
    return keep, [lab for lab in labels if assign[str(lab["proposal_id"]).split(":")[1]]["split"] == "dev"]


def fit_items(trows_by_source: dict) -> list[dict]:
    """The items ``gate_input_builder.fit_a2`` takes (its ``prepared`` form: row flags, split, soft label, weight), from
    ``arms_freeze.training_rows`` output of the gate sources' dev instances, in ``proposal_id`` order across sources."""
    items, seen = [], set()
    for src in sorted(trows_by_source):
        if src not in B.GATE_SOURCES:
            _refuse(f"{src}: A1/A2 are fitted on the gate sources only (PRE-A2 C), not {src}")
        for r in trows_by_source[src]:
            if r["split"] != "dev":
                _refuse(f"{r['proposal_id']}: only dev rows enter the fit (PRE-A2 C)")
            if r["proposal_id"] in seen:
                _refuse(f"duplicate proposal id {r['proposal_id']}")
            seen.add(r["proposal_id"])
            items.append({"row": {"proposal_id": r["proposal_id"], "node": r["node"], "noop": r["noop"],
                                  "duplicate": r["duplicate"], "features": r["features"],
                                  "instance": r["instance"], "sigma_node": r["sigma_node"]},
                          "split": "dev", "soft": r["soft"], "weight": r["weight"]})
    items.sort(key=lambda it: it["row"]["proposal_id"])          # gate_input_builder._prepare's canonical order
    return items


def fit_rows(items) -> list[dict]:
    """The training rows ``gate_input_builder.fit_a2`` builds from its items (a copy of its comprehension, so that A1 is
    fitted on exactly the rows A2 is fitted on before the rule filter)."""
    return [{"node": r["row"]["node"], "noop": is_noop(r["row"]), "duplicate": is_duplicate(r["row"]),
             "features": r["row"].get("features", {}), "soft": r["soft"], "weight": r["weight"]}
            for r in items if r["split"] == "dev" and r["soft"] is not None]


def fit(items, required_nodes) -> dict:
    """{node: {"A1": ndarray(12), "A2": ndarray(12)}} for exactly ``required_nodes``. A2 is ``fit_a2``'s output; A1 is
    ``ConstantPrior`` on ``fit_rows(items)``. Refuses a required node without a labelled non-inert dev proposal (no
    pooled fallback) and rows of any other node."""
    required = set(required_nodes)
    stray = sorted({it["row"]["node"] for it in items} - required)
    if stray:
        _refuse(f"rows of nodes outside the required set (eight T0 nodes and the frozen T1 nodes): {stray}")
    try:
        a2 = B.fit_a2(items)
    except B.BuilderError as exc:
        raise AF.ArmsFreezeError(str(exc)) from exc
    missing = sorted(required - set(a2.by_node))
    if missing:
        _refuse(f"{missing}: no labelled non-inert dev proposal, so no A1/A2 constant (PRE-A2 C; no pooled fallback)")
    a1 = ConstantPrior().fit(fit_rows(items))
    return {n: {"A1": a1.by_node[n], "A2": a2.by_node[n]} for n in sorted(required)}


def node_info(items, node: str) -> dict:
    """Label-free facts of one node's fit: σ_node (one value per node), dev instances, row counts."""
    mine = [it for it in items if it["row"]["node"] == node]
    sig = {it["row"]["sigma_node"] for it in mine}
    if len(sig) != 1:
        _refuse(f"{node}: the dev rows carry {len(sig)} sigma_node values, not one")
    rows = fit_rows(mine)
    return {"sigma_node": float(sig.pop()), "dev_instances": sorted({it["row"]["instance"] for it in mine}),
            "rows": {"dev": len(mine), "A1": len(rows), "A2": sum(not (r["noop"] or r["duplicate"]) for r in rows)}}


def fit_sources(sources: dict, *, t1: B.Tier1 | None = None, assign=None) -> tuple[dict, list[dict]]:
    """``sources``: {source: (table rows, released train/dev label rows)}. Returns ({node: {"A1", "A2"}}, items)."""
    assign = assign if assign is not None else p3_split.assignment(p3_split.load())
    t1_nodes = set(t1.suites) if t1 is not None else set()
    want = {"sweep2"} | ({"g5"} if t1_nodes else set())
    if set(sources) != want:
        _refuse(f"sources must be exactly {sorted(want)} (sweep 2 for T0; G.5 iff the frozen T1 set is non-empty)")
    trows = {}
    for src in sorted(sources):
        rows, labels = sources[src]
        AF.check_table_rows(rows)
        drows, dlabels = dev_only(rows, labels, assign)
        trows[src] = AF.training_rows(src, drows, dlabels, assign=assign, t1=t1)
    items = fit_items(trows)
    return fit(items, set(B.ALL_T0) | t1_nodes), items


# ============================================================================================== the document

def document(fitted: dict, items, *, sources_meta: dict, t1: B.Tier1 | None, fitter: dict, builder_sha256: str) -> dict:
    """The constants file's content (checked with ``parse`` before it is returned)."""
    t1_nodes = set(t1.suites) if t1 is not None else set()
    nodes = {}
    for n, v in sorted(fitted.items()):
        nodes[n] = {"tier": "T1" if n in t1_nodes else "T0", "source": "g5" if n in t1_nodes else "sweep2",
                    "A1": [float(x) for x in v["A1"]], "A2": [float(x) for x in v["A2"]], **node_info(items, n)}
    doc = {"schema": SCHEMA,
           "written_by": "r1/c3/arms_constants.py (AI-assisted, Claude); post-freeze reads amendment A§8 unit 1, "
                         "D.3 pre-declaration gap G2 (A1 and A2)",
           "fitter": dict(fitter), "fit_population": FIT_POPULATION, "rules": dict(RULES), "row_order": "proposal_id",
           "split_file": {"path": SPLIT_PATH, "sha256": p3_split.P3_SPLIT_SHA256},
           "gate_input_builder": {"path": BUILDER_PATH, "sha256": builder_sha256},
           "sources": {s: dict(m) for s, m in sorted(sources_meta.items())},
           "t1": {"suites": dict(t1.suites) if t1 is not None else {},
                  "modes": list(t1.modes) if t1 is not None else [], "d3_k6": bool(t1.d3_k6) if t1 else False},
           "t0_nodes": list(B.ALL_T0), "d3_nodes": list(D3_NODES), "nodes": nodes}
    parse(AF._dump(doc))
    return doc


def check_vector(v, what: str, *, a2: bool) -> None:
    """A 12-bin distribution: finite, non-negative, summing to 1 within 1e-9; A2's bin 0 is exactly 0."""
    if not isinstance(v, list) or len(v) != N_BINS or \
            not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0 for x in v):
        _refuse(f"{what}: must be {N_BINS} finite non-negative numbers")
    if abs(math.fsum(v) - 1.0) > SUM_TOL:
        _refuse(f"{what}: does not sum to 1")
    if a2 and v[INERT] != 0.0:
        _refuse(f"{what}: A2's no-op bin must be 0 (arms.RulesPrior._noninert)")


def same_bits(a, b) -> bool:
    """Bitwise equality of two vectors of floats."""
    return len(a) == len(b) and all(float(x).hex() == float(y).hex() for x, y in zip(a, b))


def _sha_pin(obj, what: str) -> None:
    if not isinstance(obj, dict) or not _HEX.fullmatch(str(obj.get("sha256"))):
        _refuse(f"{what}: needs a sha256")


def vectors_of(obj: dict, what: str = "constants file") -> dict:
    """{"A1": {node: list}, "A2": {node: list}} of a constants document of this schema family (also used for the D.3
    constants file, which must carry the same per-node ``A1`` / ``A2`` vectors)."""
    if not isinstance(obj, dict) or not str(obj.get("schema", "")).startswith(SCHEMA_PREFIX) or \
            not isinstance(obj.get("nodes"), dict) or not obj["nodes"]:
        _refuse(f"{what}: not a {SCHEMA_PREFIX}* document with nodes")
    out = {"A1": {}, "A2": {}}
    for n, e in obj["nodes"].items():
        if not isinstance(e, dict):
            _refuse(f"{what}: node {n} is not an object")
        for arm in ("A1", "A2"):
            check_vector(e.get(arm), f"{what}: {n}.{arm}", a2=arm == "A2")
            out[arm][n] = e[arm]
    return out


def load_json(data: bytes, what: str) -> dict:
    try:
        obj = json.loads(data)
    except ValueError as exc:
        raise AF.ArmsFreezeError(f"{what}: not JSON") from exc
    return obj


def parse(data: bytes) -> dict:
    """A constants file of this schema, checked: the fitter pin, the fit population, the split file, the sources and
    the T1 setting, and per node the two vectors, σ_node, the dev instances and counts, for exactly the eight T0 nodes
    and the T1 setting's nodes."""
    c = load_json(data, "constants file")
    if not isinstance(c, dict) or c.get("schema") != SCHEMA:
        _refuse(f"constants file: schema must be {SCHEMA}")
    f = c.get("fitter")
    if not isinstance(f, dict) or set(f) != {"path", "sha256", "code_commit"} or f["path"] != FITTER_PATH or \
            not _HEX.fullmatch(str(f["sha256"])) or not _COMMIT.fullmatch(str(f["code_commit"])):
        _refuse(f"constants file: fitter must be {{path: {FITTER_PATH}, sha256, code_commit (40 hex)}}")
    if c.get("fit_population") != FIT_POPULATION:
        _refuse(f"constants file: fit_population must be {FIT_POPULATION!r}")
    if c.get("split_file") != {"path": SPLIT_PATH, "sha256": p3_split.P3_SPLIT_SHA256}:
        _refuse("constants file: split_file is not the pinned P3 split file")
    t1 = c.get("t1")
    if not isinstance(t1, dict) or set(t1) != {"suites", "modes", "d3_k6"} or not isinstance(t1["suites"], dict):
        _refuse("constants file: t1 must be {suites, modes, d3_k6}")
    srcs = c.get("sources")
    want = {"sweep2"} | ({"g5"} if t1["suites"] else set())
    if not isinstance(srcs, dict) or set(srcs) != want:
        _refuse(f"constants file: sources must be exactly {sorted(want)}")
    for s, m in srcs.items():
        keys = ("receipt_sha256", "traindev_partition_sha256", "label_block_sha256", "proposals_sha256")
        if not isinstance(m, dict) or set(m) != set(keys) or not all(_HEX.fullmatch(str(m[k])) for k in keys):
            _refuse(f"constants file: sources.{s} must give {list(keys)} as sha256s")
    vec = vectors_of(c)
    nodes = set(B.ALL_T0) | set(t1["suites"])
    if set(c["nodes"]) != nodes:
        _refuse("constants file: nodes must be exactly the eight T0 nodes and the frozen T1 nodes")
    for n, e in c["nodes"].items():
        if not isinstance(e.get("sigma_node"), (int, float)) or not e["sigma_node"] > 0 or \
                not isinstance(e.get("dev_instances"), list) or not e["dev_instances"]:
            _refuse(f"constants file: {n} needs sigma_node > 0 and its dev instances")
    return {**c, "vectors": vec}


# ============================================================================================== CLI

def _code_commit() -> tuple[str, str]:
    """(HEAD, sha256 of the committed fitter) of a clean checkout whose fitter is the committed file."""
    from r1.c3 import release
    data = release._committed(FITTER_PATH)
    if release._git("status", "--porcelain", "--untracked-files=no").decode().strip():
        _refuse("the fitter needs a clean checkout (tracked changes present)")
    return release._head(), AF._sha(data)


def _fit_cmd(a) -> dict:
    from r1.harness import REPO
    tables, receipts, roots = AF._kv(a.table), AF._kv(a.receipt), AF._kv(a.release_root)
    if not (set(tables) == set(receipts) == set(roots)):
        _refuse("--table, --receipt and --release-root must name the same sources")
    out = Path(a.out)
    AF.refuse_input_path(out)
    if out.exists():
        _refuse(f"{out} exists; the constants file is written once")
    t1 = AF._tier1(a.t1)
    if "sweep1" in tables:
        _refuse("sweep 1 does not enter A1/A2 (PRE-A2 C: the gate sources only)")
    commit, fitter_sha = _code_commit()
    assign = p3_split.assignment(p3_split.load())
    sources, meta = {}, {}
    for src in sorted(tables):
        if src not in B.GATE_SOURCES:
            _refuse(f"unknown source {src}")
        labels, receipt = AF.load_traindev(roots[src], src, receipts[src])
        rows = AF.load_table_rows(tables[src])          # refuse_input_path, guard_table, no label/evaluation values
        table_sha = AF._sha_file(Path(tables[src]) / "proposals.jsonl")
        if table_sha != (receipt.get("inputs") or {}).get("proposals_sha256"):
            _refuse(f"{src}: the table is not the one the receipt released")
        if src == "sweep2" and table_sha != SWEEP2_PROPOSALS_SHA256:
            _refuse(f"sweep2: the table is not the pinned sweep-2 table {SWEEP2_PROPOSALS_SHA256[:12]}… "
                    "(D.3 draft §5.0)")
        sources[src] = (rows, labels)
        meta[src] = {"receipt_sha256": receipts[src],
                     "traindev_partition_sha256": receipt["outputs"]["label_block.traindev.jsonl"],
                     "label_block_sha256": receipt["inputs"]["label_block_sha256"], "proposals_sha256": table_sha}
    fitted, items = fit_sources(sources, t1=t1, assign=assign)
    doc = document(fitted, items, sources_meta=meta, t1=t1,
                   fitter={"path": FITTER_PATH, "sha256": fitter_sha, "code_commit": commit},
                   builder_sha256=AF._sha_file(REPO / BUILDER_PATH))
    data = AF._dump(doc)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"out": str(out), "sha256": AF._sha(data), "nodes": sorted(doc["nodes"]), "code_commit": commit,
            "fitter_sha256": fitter_sha}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="A1/A2 constants fitter (dev label block of the gate sources only)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="fit A1 and A2 per node and write the constants file")
    f.add_argument("--release-root", action="append", required=True, help="SOURCE=DIR holding SOURCE/traindev")
    f.add_argument("--table", action="append", required=True, help="SOURCE=DIR of the released table")
    f.add_argument("--receipt", action="append", required=True, help="SOURCE=sha256 of its traindev RECEIPT.json")
    f.add_argument("--t1", help="JSON {suites, modes, d3_k6} of the frozen T1 set (omit for T0 only)")
    f.add_argument("--out", required=True, help="the constants file to write (must not exist)")
    a = ap.parse_args(argv)
    print(json.dumps(_fit_cmd(a), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
