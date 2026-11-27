"""D.3 gap G2: the A1/A2/LADDER constants file of the D.3 pre-declaration (revision 4, §5.0, §5.2, §5.3, §5.6, §12 G2).

AI-assisted (Claude, local worker, 27 Nov 2026). Tier E (R1-PROCESS-TIERS: it fixes keep/execute decisions): a committed
independent review, re-checked until accepted, before the file it writes is pinned in the pre-declaration's key block
(§14 ``constants_file_sha256``). Built and tested on synthetic data only; it has not been run on released labels.

**What it reads (§5.0), and nothing else.**

* Label rows of the receipted sweep-2 **train/dev** partition through ``arms_freeze.load_traindev`` (that is
  ``release.traindev_labels(release_root, "sweep2", receipt_sha256=<receipt>)``, the receipt pinned; a receipt that is
  not train/dev or counts evaluation rows, a label row with an evaluation field or evaluation seeds, and a label row of
  a P3 test instance are refused).
* Table fields of the sweep-2 proposal table through ``arms_freeze.load_table_rows`` (``dataset.load_table``, which
  calls ``analysis_guard.guard_table``; a table row carrying a label or evaluation value is refused).
  ``proposals.jsonl`` must equal both the B.2 addendum's pin and the receipt's ``inputs.proposals_sha256``, and
  ``configs.json`` must exist and equal the key block's pin (§14 ``sweep2_table``); any mismatch is a STOP.
* The split file (``p3_split``, sha256-pinned) and the noise constants: ``dataset.noise_table`` on the pinned noise
  summary (§2; sha256-checked here).
* Raw label blocks, evaluation blocks, test partitions and run logs are refused by name before anything is opened
  (``arms_freeze.refuse_input_path``); ``r1_sealed`` paths are refused (``analysis_guard.refuse_sealed``).

**Rows.** Table rows and label rows are filtered to the **P3 dev instances of the seven D.3 nodes before any use**
(§5.0); every other row enters no computation (label rows are first screened as a whole by ``check_label_rows``,
which reads no label value). Population (PRE-A2 C): the full dev population of sweep 2, both memory modes, as
``arms_freeze.training_rows`` builds it (``gate_input_builder._prepare``'s construction; soft labels v2 from the label
seeds 7001-7005 only).

**What it fits.**

* **A1, A2 (§5.2, §5.3):** ``arms_constants.fit`` on the seven nodes' items: A2 is ``gate_input_builder.fit_a2``'s
  own output, A1 ``arms.ConstantPrior`` on the same rows (no-ops included). Each node's vectors use only its rows, so
  they equal bitwise the vectors ``arms_constants`` fits for the arms-frozen record (a test shows it), which the
  record checker requires (``arms_freeze._check_d3_vectors``; R1-D3-MIN; §10).
* **LADDER (§5.6):** per node, on **the same dev rows as A1** (labelled dev rows with a soft label: no-ops included,
  duplicates and divergent labels excluded; first trials are not table rows), maximise

      U_node(eta) = sum_p w_p * Delta_label,p * 1{Delta_hat_p > eta}

  over eta = c * sigma_node, c in LADDER_GRID = {-3.00, -2.95, ..., +3.00} (121 values). Delta_label,p is the label
  row's ``delta_label`` (the mean over the label seeds 7001-7005 that ran; a no-op's inert label is 0, so a no-op adds
  0 to every U), Delta_hat_p the table's logged ``delta_hat``, w_p the row weight (1: every eligible sweep-2 proposal was
  audited; another weight is refused). eta is the IEEE-754 double ``float(c) * float(sigma_node)``, the product the
  LADDER controller computes (``d3_controllers.ladder_eta``), and the comparison is strict. U is summed with
  ``math.fsum`` (correctly rounded, so independent of row order and exactly equal for equal exact sums). Ties of U
  (exact equality): smallest |c|, then smallest c (c = 0 is A0's rule). sigma_node is the noise table's, and every
  table row of the node must carry exactly that value (bitwise), so the controller's eta equals the file's.

**What it writes.** One JSON file, schema ``r1_c3_rule_arm_constants/d3_v1`` (the arms constants schema family, so
``arms_constants.vectors_of`` and the arms-frozen record checker read its A1/A2 vectors), created exclusively (an
existing file is refused), with sorted keys and no timestamp (the same inputs and code give identical bytes): per node
the A1 and A2 vectors, the noise constants used (sigma_node, sigma_local, sigma_structural, delta_n), the dev instances
and row counts, and LADDER's c, eta, the maximal U and its full 121-row search table (c, eta, U, keeps); the receipt,
partition, label block, table, configs, split-file and noise-summary sha256s; the code (this file and
``arms_constants.py``, path and committed sha256, the code commit) and the toolchain. The CLI prints its sha256, which
fills §14 ``constants_file_sha256``.

CLI (run on released data only by whoever the D.3 runbook authorises, once the sweep-2 train/dev labels are released
with their receipt; not by this unit)::

    python -m r1.c3.d3_constants fit --release-root DIR --receipt SHA --table DIR --out FILE
    python -m r1.c3.d3_constants check FILE      # re-parse a written file and print its sha256 and the LADDER c
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from r1.c3 import arms_constants as AC
from r1.c3 import arms_freeze as AF
from r1.c3 import gate_input_builder as B
from r1.c3 import p3_split
from r1.c3.labels import N_BINS

SCHEMA = "r1_c3_rule_arm_constants/d3_v1"
assert SCHEMA.startswith(AC.SCHEMA_PREFIX)
FITTER_PATH = "r1/c3/d3_constants.py"
PREDECLARATION_PATH = "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md"
PREDECLARATION_REVISION = 4
SOURCE = "sweep2"
D3_NODES = AC.D3_NODES                                     # §14 d3_nodes
# §2 / §14 noise_source (also r1/c3/d3_analysis.py NOISE_SOURCE_PATH / NOISE_SOURCE_SHA256)
NOISE_PATH = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
NOISE_KEYS = ("sigma_node", "sigma_local", "sigma_structural", "delta_n")
# §5.0 / §14 sweep2_table
SWEEP2_PROPOSALS_SHA256 = AC.SWEEP2_PROPOSALS_SHA256
SWEEP2_CONFIGS_SHA256 = "de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d"
# §5.6: c in {-3.00, -2.95, ..., +3.00}; the same construction as d3_controllers.LADDER_GRID
LADDER_GRID = tuple(round(-3.0 + 0.05 * k, 2) for k in range(121))
assert len(LADDER_GRID) == 121 and LADDER_GRID[0] == -3.0 and LADDER_GRID[60] == 0.0 and LADDER_GRID[-1] == 3.0
FIT_POPULATION = "sweep-2 dev label block, full dev population (both memory modes), the seven D.3 nodes"
RULES = {"A1": AC.RULES["A1"], "A2": AC.RULES["A2"],
         "LADDER": "argmax over c in LADDER_GRID of U(c) = fsum_p w_p * delta_label_p * [delta_hat_p > c * sigma_node] "
                   "on A1's dev rows; ties: smallest |c|, then smallest c; eta = float(c) * float(sigma_node)"}
LADDER_TIE = "exact equality of fsum U; smallest |c|, then smallest c"
SOURCE_KEYS = ("receipt_sha256", "traindev_partition_sha256", "label_block_sha256", "proposals_sha256",
               "configs_sha256")
TOP_KEYS = {"schema", "written_by", "predeclaration", "fitter", "a1a2_fitter", "gate_input_builder", "toolchain",
            "source", "split_file", "noise_source", "fit_population", "rules", "row_order", "ladder_grid",
            "ladder_tie", "d3_nodes", "nodes"}
NODE_KEYS = {"A1", "A2", "noise", "sigma_node", "dev_instances", "rows", "LADDER"}
LADDER_KEYS = {"c", "eta", "sigma_node", "u_max", "rows", "noop_rows", "search"}
_HEX = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")


def _refuse(msg: str):
    raise AF.ArmsFreezeError(msg)


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ============================================================================================== the LADDER search

def ladder_eta(c: float, sigma_node: float) -> float:
    """eta = c * sigma_node for a declared grid value c (§5.6), as the LADDER controller computes it."""
    if c not in LADDER_GRID:
        _refuse("c must be one of the 121 declared grid values -3.00, -2.95, ..., +3.00 (§5.6)")
    if not (_num(sigma_node) and sigma_node > 0):
        _refuse("sigma_node must be a positive finite number")
    return float(c) * float(sigma_node)


def ladder_pick(table) -> dict:
    """The row of a search table chosen by §5.6: maximal U; ties (exact equality) smallest |c|, then smallest c."""
    return min(table, key=lambda r: (-r["U"], abs(r["c"]), r["c"]))


def ladder_search(entries, sigma_node: float) -> dict:
    """§5.6 on one node. ``entries``: [(w_p, delta_label_p, delta_hat_p)]. Returns c, eta, the maximal U and the
    121-row search table [{c, eta, U, keeps}] in grid order."""
    entries = list(entries)
    if not entries:
        _refuse("LADDER: a node without labelled dev rows has no eta (§5.0 STOP)")
    for w, d, h in entries:
        if not (_num(w) and _num(d) and _num(h)):
            _refuse("LADDER: weights, labels and logged Delta_hat must be finite numbers")
    table = []
    for c in LADDER_GRID:
        eta = ladder_eta(c, sigma_node)
        kept = [float(w) * float(d) for w, d, h in entries if float(h) > eta]
        table.append({"c": c, "eta": eta, "U": math.fsum(kept), "keeps": len(kept)})
    best = ladder_pick(table)
    return {"c": best["c"], "eta": best["eta"], "u_max": best["U"], "search": table}


# ============================================================================================== rows and fit

def d3_dev_rows(rows, labels, assign) -> tuple[list[dict], list[dict]]:
    """Table and label rows of the P3 dev instances of the seven D.3 nodes only (§5.0), selected before any use. Label
    rows are first screened as released train/dev rows (``check_label_rows``: no evaluation field or seed, no test
    instance), table rows for label or evaluation values; neither check reads a label value."""
    AF.check_table_rows(rows)
    drows, dlabels = AC.dev_only(rows, labels, assign)
    nodes = set(D3_NODES)
    return [r for r in drows if r["node"] in nodes], [lab for lab in dlabels if lab.get("node") in nodes]


def check_sigma(items, noise: dict) -> dict:
    """{node: noise constants} for the seven nodes; every dev row's sigma_node must equal the noise table's bitwise."""
    out = {}
    for n in D3_NODES:
        if n not in noise or not all(_num(noise[n].get(k)) for k in NOISE_KEYS) or not noise[n]["sigma_node"] > 0:
            _refuse(f"{n}: no noise constants {list(NOISE_KEYS)} in the noise table (§2)")
        sig = {float(it["row"]["sigma_node"]).hex() for it in items if it["row"]["node"] == n}
        if sig != {float(noise[n]["sigma_node"]).hex()}:
            _refuse(f"{n}: the table's sigma_node differs from the noise table's (§2), so eta would not be the "
                    "controller's")
        out[n] = {k: float(noise[n][k]) for k in NOISE_KEYS}
    return out


def ladder_entries(items, trows, table_rows, labels, node: str) -> tuple[list[tuple], int]:
    """(w, delta_label, delta_hat) of A1's dev rows of ``node`` (``arms_constants.fit_rows``' selection: dev rows with
    a soft label), and the number of no-op rows among them (inert label 0)."""
    by_trow = {r["proposal_id"]: r for r in trows}
    by_row = {r["proposal_id"]: r for r in table_rows}
    by_lab = {lab["proposal_id"]: lab for lab in labels}
    out, noops = [], 0
    for it in items:
        if it["row"]["node"] != node or it["split"] != "dev" or it["soft"] is None:
            continue
        pid = it["row"]["proposal_id"]
        if it["weight"] != 1.0:
            _refuse(f"{pid}: LADDER weight {it['weight']!r} is not 1 (§5.6: every eligible proposal was audited)")
        tr = by_trow[pid]
        if tr["noop"]:
            if tr["label_kind"] != "rule_noop":
                _refuse(f"{pid}: a no-op without its rule_noop label")
            d, noops = 0.0, noops + 1                         # the inert label: Delta = 0, adds 0 to every U
        else:
            if tr["label_kind"] != "audit":
                _refuse(f"{pid}: a LADDER row needs an audit label")
            d = by_lab[pid]["delta_label"]
        h = by_row[pid].get("delta_hat")
        if not _num(h) or not _num(d):
            _refuse(f"{pid}: delta_hat and delta_label must be finite numbers")
        out.append((1.0, float(d), float(h)))
    return out, noops


def fit_d3(rows, labels, noise: dict, *, assign=None) -> dict:
    """The constants of the seven D.3 nodes from sweep-2 table rows and released train/dev label rows. Returns
    {"vectors": {node: {A1, A2}}, "items": [...], "noise": {node: ...}, "ladder": {node: ...}}."""
    assign = assign if assign is not None else p3_split.assignment(p3_split.load())
    drows, dlabels = d3_dev_rows(rows, labels, assign)
    bad = sorted({str(r.get("memory_mode")) for r in drows} - set(B._declared_modes(B.GATE_SOURCES[SOURCE], None)))
    if bad:
        _refuse(f"{SOURCE}: dev rows of undeclared memory modes {bad} (PRE-MEM C; the builder refuses them)")
    trows = AF.training_rows(SOURCE, drows, dlabels, assign=assign)
    items = AC.fit_items({SOURCE: trows})
    vectors = AC.fit(items, D3_NODES)                         # A2 = fit_a2; refuses a node without a constant
    sig = check_sigma(items, noise)
    ladder = {}
    for n in D3_NODES:
        entries, noops = ladder_entries(items, trows, drows, dlabels, n)
        res = ladder_search(entries, sig[n]["sigma_node"])
        ladder[n] = {"c": res["c"], "eta": res["eta"], "sigma_node": sig[n]["sigma_node"], "u_max": res["u_max"],
                     "rows": len(entries), "noop_rows": noops, "search": res["search"]}
    return {"vectors": vectors, "items": items, "noise": sig, "ladder": ladder}


# ============================================================================================== the document

def document(fit: dict, *, source_meta: dict, fitter: dict, a1a2_fitter: dict, builder_sha256: str,
             tools: dict | None = None) -> dict:
    """The constants file's content (checked with ``parse`` before it is returned)."""
    nodes = {}
    for n in D3_NODES:
        info = AC.node_info(fit["items"], n)
        nodes[n] = {"A1": [float(x) for x in fit["vectors"][n]["A1"]],
                    "A2": [float(x) for x in fit["vectors"][n]["A2"]],
                    "noise": dict(fit["noise"][n]), "sigma_node": info["sigma_node"],
                    "dev_instances": info["dev_instances"], "rows": info["rows"],
                    "LADDER": {k: (list(v) if k == "search" else v) for k, v in fit["ladder"][n].items()}}
    doc = {"schema": SCHEMA,
           "written_by": "r1/c3/d3_constants.py (AI-assisted, Claude); D.3 pre-declaration §5.0 / §12 gap G2",
           "predeclaration": {"path": PREDECLARATION_PATH, "revision": PREDECLARATION_REVISION},
           "fitter": dict(fitter), "a1a2_fitter": dict(a1a2_fitter),
           "gate_input_builder": {"path": AC.BUILDER_PATH, "sha256": builder_sha256},
           "toolchain": dict(tools) if tools is not None else AC.toolchain(),
           "source": {"name": SOURCE, **{k: source_meta[k] for k in SOURCE_KEYS}},
           "split_file": {"path": AC.SPLIT_PATH, "sha256": p3_split.P3_SPLIT_SHA256},
           "noise_source": {"path": NOISE_PATH, "sha256": NOISE_SHA256},
           "fit_population": FIT_POPULATION, "rules": dict(RULES), "row_order": "proposal_id",
           "ladder_grid": list(LADDER_GRID), "ladder_tie": LADDER_TIE, "d3_nodes": list(D3_NODES), "nodes": nodes}
    parse(AF._dump(doc))
    return doc


def _check_ladder(n: str, e: dict) -> None:
    lad = e.get("LADDER")
    if not isinstance(lad, dict) or set(lad) != LADDER_KEYS:
        _refuse(f"constants file: {n}.LADDER must be {sorted(LADDER_KEYS)}")
    sig = lad["sigma_node"]
    if not (_num(sig) and sig > 0) or float(sig).hex() != float(e["sigma_node"]).hex() or \
            float(sig).hex() != float(e["noise"]["sigma_node"]).hex():
        _refuse(f"constants file: {n}.LADDER.sigma_node must equal the node's sigma_node and noise sigma_node")
    if lad["c"] not in LADDER_GRID or isinstance(lad["c"], bool):
        _refuse(f"constants file: {n}.LADDER.c is not a declared grid value (§5.6)")
    if not _num(lad["eta"]) or float(lad["eta"]).hex() != ladder_eta(lad["c"], sig).hex():
        _refuse(f"constants file: {n}.LADDER.eta must be float(c) * float(sigma_node) exactly")
    for k in ("rows", "noop_rows"):
        if not isinstance(lad[k], int) or isinstance(lad[k], bool):
            _refuse(f"constants file: {n}.LADDER.{k} must be an integer")
    if not 0 <= lad["noop_rows"] <= lad["rows"] or lad["rows"] != e["rows"]["A1"]:
        _refuse(f"constants file: {n}.LADDER.rows must be A1's row count (§5.6: the same dev rows as A1)")
    t = lad["search"]
    if not isinstance(t, list) or len(t) != len(LADDER_GRID):
        _refuse(f"constants file: {n}.LADDER.search must have one row per grid value")
    for r, c in zip(t, LADDER_GRID):
        if not isinstance(r, dict) or set(r) != {"c", "eta", "U", "keeps"} or r["c"] != c or \
                isinstance(r["c"], bool) or not _num(r["eta"]) or float(r["eta"]).hex() != ladder_eta(c, sig).hex() \
                or not _num(r["U"]) or not isinstance(r["keeps"], int) or isinstance(r["keeps"], bool) or \
                not 0 <= r["keeps"] <= lad["rows"]:
            _refuse(f"constants file: {n}.LADDER.search row for c = {c} is malformed")
    if any(a["keeps"] < b["keeps"] for a, b in zip(t, t[1:])):
        _refuse(f"constants file: {n}.LADDER.search keeps must not increase with c")
    best = ladder_pick(t)
    if best["c"] != lad["c"] or float(best["U"]).hex() != float(lad["u_max"]).hex():
        _refuse(f"constants file: {n}.LADDER.c is not the §5.6 choice from its search table")


def parse(data: bytes) -> dict:
    """A constants file of this schema, checked: provenance pins, toolchain, rules, the grid, and per D.3 node the two
    vectors, the noise constants, the dev instances and counts, and LADDER's c, eta and search table (c re-derived from
    the table by §5.6's rule). Returns the document with ``vectors`` ({A1, A2}: {node: list}) and ``ladder_c``."""
    c = AC.load_json(data, "constants file")
    if not isinstance(c, dict) or c.get("schema") != SCHEMA:
        _refuse(f"constants file: schema must be {SCHEMA}")
    if set(c) != TOP_KEYS:
        _refuse(f"constants file: top-level keys must be {sorted(TOP_KEYS)}")
    if c["predeclaration"] != {"path": PREDECLARATION_PATH, "revision": PREDECLARATION_REVISION}:
        _refuse("constants file: predeclaration must name revision 4 of the D.3 pre-declaration")
    for key, path, commit in (("fitter", FITTER_PATH, True), ("a1a2_fitter", AC.FITTER_PATH, False),
                              ("gate_input_builder", AC.BUILDER_PATH, False)):
        f, want = c[key], {"path", "sha256"} | ({"code_commit"} if commit else set())
        if not isinstance(f, dict) or set(f) != want or f["path"] != path or not _HEX.fullmatch(str(f["sha256"])) \
                or (commit and not _COMMIT.fullmatch(str(f["code_commit"]))):
            _refuse(f"constants file: {key} must be {{path: {path}, sha256"
                    + (", code_commit (40 hex)}}" if commit else "}}"))
    tc = c["toolchain"]
    if not isinstance(tc, dict) or set(tc) != AC.TOOLCHAIN_KEYS or \
            not all(isinstance(v, str) and v.strip() for v in tc.values()):
        _refuse(f"constants file: toolchain must give {sorted(AC.TOOLCHAIN_KEYS)} as non-empty strings")
    s = c["source"]
    if not isinstance(s, dict) or set(s) != {"name", *SOURCE_KEYS} or s["name"] != SOURCE or \
            not all(_HEX.fullmatch(str(s[k])) for k in SOURCE_KEYS):
        _refuse(f"constants file: source must be {SOURCE} with {list(SOURCE_KEYS)} as sha256s")
    if s["proposals_sha256"] != SWEEP2_PROPOSALS_SHA256 or s["configs_sha256"] != SWEEP2_CONFIGS_SHA256:
        _refuse("constants file: the table is not the pinned sweep-2 table (§5.0, §14 sweep2_table)")
    if c["split_file"] != {"path": AC.SPLIT_PATH, "sha256": p3_split.P3_SPLIT_SHA256}:
        _refuse("constants file: split_file is not the pinned P3 split file")
    if c["noise_source"] != {"path": NOISE_PATH, "sha256": NOISE_SHA256}:
        _refuse("constants file: noise_source is not the pinned noise summary (§2)")
    if c["fit_population"] != FIT_POPULATION or c["rules"] != RULES or c["row_order"] != "proposal_id" or \
            c["ladder_grid"] != list(LADDER_GRID) or c["ladder_tie"] != LADDER_TIE:
        _refuse("constants file: population, rules, row order, grid or tie rule are not this fitter's")
    if c["d3_nodes"] != list(D3_NODES) or not isinstance(c["nodes"], dict) or set(c["nodes"]) != set(D3_NODES):
        _refuse("constants file: d3_nodes and nodes must be exactly the seven D.3 nodes")
    for n, e in c["nodes"].items():
        if not isinstance(e, dict) or set(e) != NODE_KEYS:
            _refuse(f"constants file: {n} must be {sorted(NODE_KEYS)}")
        for arm in ("A1", "A2"):
            AC.check_vector(e[arm], f"constants file: {n}.{arm}", a2=arm == "A2")
        nz = e["noise"]
        if not isinstance(nz, dict) or set(nz) != set(NOISE_KEYS) or not all(_num(nz[k]) for k in NOISE_KEYS):
            _refuse(f"constants file: {n}.noise must give {list(NOISE_KEYS)}")
        if not (_num(e["sigma_node"]) and e["sigma_node"] > 0) or not isinstance(e["dev_instances"], list) or \
                not e["dev_instances"]:
            _refuse(f"constants file: {n} needs sigma_node > 0 and its dev instances")
        r = e["rows"]
        if not isinstance(r, dict) or set(r) != {"dev", "A1", "A2"} or \
                not all(isinstance(v, int) and not isinstance(v, bool) for v in r.values()) or \
                not 1 <= r["A2"] <= r["A1"] <= r["dev"]:
            _refuse(f"constants file: {n}.rows must be counts with 1 <= A2 <= A1 <= dev")
        _check_ladder(n, e)
    vec = AC.vectors_of(c)
    assert all(len(v) == N_BINS for arm in vec.values() for v in arm.values())
    return {**c, "vectors": vec, "ladder_c": {n: c["nodes"][n]["LADDER"]["c"] for n in D3_NODES}}


def ladder_constant(doc: dict, node: str) -> tuple[float, float]:
    """(c, eta) of ``node`` from a parsed constants file: what G1 passes to ``d3_controllers.ladder_controller``."""
    lad = doc["nodes"][node]["LADDER"]
    return lad["c"], lad["eta"]


# ============================================================================================== CLI

def _code() -> tuple[str, dict, dict]:
    """(HEAD, fitter pin, A1/A2 fitter pin) of a clean checkout whose fitters are the committed files."""
    from r1.c3 import release
    if release._git("status", "--porcelain", "--untracked-files=no").decode().strip():
        _refuse("the fitter needs a clean checkout (tracked changes present)")
    head = release._head()
    return (head, {"path": FITTER_PATH, "sha256": AF._sha(release._committed(FITTER_PATH)), "code_commit": head},
            {"path": AC.FITTER_PATH, "sha256": AF._sha(release._committed(AC.FITTER_PATH))})


def load_noise(repo) -> dict:
    """``dataset.noise_table`` on the pinned noise summary, sha256-checked (§2)."""
    from r1.c3.analysis_guard import refuse_sealed
    from r1.c3.dataset import noise_table
    path = Path(repo) / NOISE_PATH
    refuse_sealed(path)
    if not path.is_file() or AF._sha_file(path) != NOISE_SHA256:
        _refuse(f"{NOISE_PATH}: missing or not the pinned noise summary (§2)")
    return noise_table(path)


def write_exclusive(out: Path, data: bytes) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out, "xb") as fh:
            fh.write(data)
    except FileExistsError:
        _refuse(f"{out} exists; the constants file is written once")


def _fit_cmd(a) -> dict:
    from r1.c3.analysis_guard import refuse_sealed
    from r1.harness import REPO
    out, table_dir = Path(a.out), Path(a.table)
    AF.refuse_input_path(out, table_dir, a.release_root)
    refuse_sealed(out, table_dir, a.release_root)
    if out.exists():
        _refuse(f"{out} exists; the constants file is written once")
    commit, fitter, a1a2 = _code()
    builder_sha = AF._sha_file(REPO / AC.BUILDER_PATH)
    if builder_sha != AF._prereg_block(REPO)["gate_input_builder_sha256"]:
        _refuse("the checkout's gate_input_builder.py is not the one the preregistration binds (fit_a2 is its code)")
    noise = load_noise(REPO)
    labels, receipt = AF.load_traindev(a.release_root, SOURCE, a.receipt)
    table_sha = AF._sha_file(table_dir / "proposals.jsonl")
    if table_sha != (receipt.get("inputs") or {}).get("proposals_sha256"):
        _refuse(f"{SOURCE}: the table is not the one the receipt released (§5.0 STOP)")
    if table_sha != SWEEP2_PROPOSALS_SHA256:
        _refuse(f"{SOURCE}: the table is not the pinned sweep-2 table {SWEEP2_PROPOSALS_SHA256[:12]}… (§5.0 STOP)")
    configs = table_dir / "configs.json"
    if not configs.is_file() or AF._sha_file(configs) != SWEEP2_CONFIGS_SHA256:
        _refuse(f"{SOURCE}: configs.json is missing or not the pinned {SWEEP2_CONFIGS_SHA256[:12]}… (§14 STOP)")
    rows = AF.load_table_rows(table_dir)          # refuse_input_path, guard_table, no label/evaluation values
    fit = fit_d3(rows, labels, noise)
    meta = {"receipt_sha256": a.receipt, "traindev_partition_sha256": receipt["outputs"]["label_block.traindev.jsonl"],
            "label_block_sha256": receipt["inputs"]["label_block_sha256"], "proposals_sha256": table_sha,
            "configs_sha256": SWEEP2_CONFIGS_SHA256}
    doc = document(fit, source_meta=meta, fitter=fitter, a1a2_fitter=a1a2, builder_sha256=builder_sha)
    data = AF._dump(doc)
    write_exclusive(out, data)
    return {"out": str(out), "sha256": AF._sha(data), "code_commit": commit, "fitter_sha256": fitter["sha256"],
            "ladder_c": {n: doc["nodes"][n]["LADDER"]["c"] for n in D3_NODES}, "toolchain": doc["toolchain"],
            "fills": "D3_PREDECLARATION_DRAFT_20261122.md §14 constants_file_sha256"}


def _check_cmd(a) -> dict:
    data = Path(a.file).read_bytes()
    doc = parse(data)
    return {"file": a.file, "sha256": AF._sha(data), "ladder_c": doc["ladder_c"],
            "ladder_eta": {n: doc["nodes"][n]["LADDER"]["eta"] for n in D3_NODES}}


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="D.3 G2: A1/A2/LADDER constants from the sweep-2 train/dev release only")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="fit A1, A2 and LADDER per D.3 node and write the constants file (once)")
    f.add_argument("--release-root", required=True, help="DIR holding sweep2/traindev (the receipted partition)")
    f.add_argument("--receipt", required=True, help="sha256 of the sweep-2 traindev RECEIPT.json")
    f.add_argument("--table", required=True, help="DIR of the released sweep-2 table (proposals.jsonl, configs.json)")
    f.add_argument("--out", required=True, help="the constants file to write (must not exist)")
    k = sub.add_parser("check", help="parse a written constants file; print its sha256 and the LADDER c per node")
    k.add_argument("file")
    a = ap.parse_args(argv)
    print(json.dumps(_fit_cmd(a) if a.cmd == "fit" else _check_cmd(a), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
