#!/usr/bin/env python3
"""Design of the direct screening measurement R1-SCREEN-MEASURE (tier E). Pure: no harness, no run, no outcome.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md``.

What this module fixes, from pinned files only (every input is checked against its sha256 before use):

* the eight T0 nodes (``r1/c3/p3_split.py`` ``T0_NODES``, a tested copy of ``gate.T0_NODES``);
* per node, the five E1 single edits c1..c5 of the pinned noise source
  ``results/r1/noise/D28_REPAIR_20261027/summary.json`` (the source both sweeps pin), in the order of the edits file
  that source cites for the node, with each edit's ``rho_joint`` (corr(c0, c_k) over 30 joint seeds);
* the two-edit children c_ij = c0 + e_i + e_j (i < j), after the two exclusion rules written before any run:
  - ``same_symbol``: e_i and e_j set the same symbol, so no single configuration holds both;
  - ``identical_to:<id>``: the child's active projection (the D25 active keys of ``r1/c3/features.py`` for its
    ``model_type``; every symbol on the MLP nodes) equals that of c0, a single edit or a child earlier in
    (i, j) order, so it is the same configuration as one already in the design;
* the lineage triples: for each retained child, (c0, c_i, c_ij), whose p -> c link applies e_j, and (c0, c_j, c_ij),
  whose p -> c link applies e_i;
* the primary triples: those whose p -> c link applies an edit with ``rho_joint`` < 0.95 in the pinned source
  (``NEAR_DUPLICATE`` = 0.95). The others are near-duplicate links and enter only the secondary analysis.

Run: ``python -m r1.noise.screen_design --out <json>`` writes the design (metadata only).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from r1.harness import REPO

SCHEMA = "r1_screen_measure_design/v1"
RUN_ID = "smeas-20261123-a"                     # proposed; no run has used it
SEED_BLOCK = tuple(range(3301, 3421))          # 120 fresh joint seeds (train seed = split seed); screen_seeds.py
NEAR_DUPLICATE = 0.95                          # rho_joint of the link's edit at or above this: near-duplicate link
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval', 'openml_ionosphere',
            'openml_sonar', 'openml_wdbc', 'tabular_mlp')       # == r1.c3.p3_split.T0_NODES (tested)
DECISION_NODES = T0_NODES                      # R1-SCREEN-MEASURE: "If any node returns SHARED" (all eight)
SEVEN_NODES = tuple(n for n in T0_NODES if n != "openml_wdbc")  # PRE-WDBC primary set; reported as a second reading

NOISE_SOURCE = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SOURCE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
# The edits files the noise source cites (its "sources"), with their sha256: the E1 common run (accepted under
# R1-E1-PILOT-ACCEPT) for the four unchanged nodes; the D28 repair and climate runs (PILOT) for the other four.
EDIT_SOURCES = {
    "results/r1/pilot/E1_20261022T214606Z/edits.json":
        ("a37adfa3ffbfb7847f3e03fee061760172af7923d453c6c0649bbf730df6a7f6",
         ("digits_mlp", "tabular_mlp", "openml_ionosphere", "openml_credit_approval")),
    "results/r1/pilot/E1_D28_REPAIR_20261027/edits.json":
        ("2e232470254312574ae290e3700acebdb1c2ec491460719c2d1a8c81067d78c3",
         ("openml_breast_w", "openml_sonar", "openml_wdbc")),
    "results/r1/pilot/E1_D28_CLIMATE_20261027/edits.json":
        ("5331765d1a58204cb0f6b7ba0273691507d8e5dfd2739b95d863feee16e725f2", ("openml_climate",)),
}


class DesignError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_pinned(rel: str, sha: str, repo: Path) -> object:
    path = Path(repo) / rel
    got = sha256_file(path)
    if got != sha:
        raise DesignError(f"STOP: {rel} sha256 {got} differs from the pinned {sha}")
    return json.loads(path.read_text())


def edit_label(edit: dict) -> str:
    return f"{edit['symbol']} {edit['old']} -> {edit['new']}"


def declared_edits(repo: Path = REPO) -> dict[str, list[dict]]:
    """node -> five edits {symbol, old, new, rho_joint} in the order of the cited edits file (pinned)."""
    summary = _load_pinned(NOISE_SOURCE, NOISE_SOURCE_SHA256, repo)
    out = {}
    for rel, (sha, nodes) in EDIT_SOURCES.items():
        edits = _load_pinned(rel, sha, repo)
        for node in nodes:
            rows = summary["nodes"][node]["edits"]
            rho = {r["edit"]: r.get("rho_joint") for r in rows}
            node_edits = edits[node]
            if len(node_edits) != 5 or [edit_label(e) for e in node_edits] != [r["edit"] for r in rows]:
                raise DesignError(f"STOP: {node}: edits file and noise source disagree")
            out[node] = [{**e, "rho_joint": rho[edit_label(e)]} for e in node_edits]
    if set(out) != set(T0_NODES):
        raise DesignError(f"STOP: edit sources cover {sorted(out)}, not the eight T0 nodes")
    return {n: out[n] for n in T0_NODES}


def _norm(value) -> str:
    v = str(value).strip().strip("\"'")
    return "null" if v.lower() in {"none", "null", "~"} else v


def active_projection(node: str, overrides: dict, edits: list[dict]) -> tuple:
    """The configuration over the symbols the design edits, restricted to the keys active under its model_type.

    Symbols the design never edits hold c0's value in every configuration of the node and their activity depends
    only on model_type, which the projection carries, so equality of this projection is equality of the full
    active projection (``r1.c3.features.active_projection``)."""
    base = {e["symbol"]: _norm(e["old"]) for e in edits}
    full = {**base, **{k: _norm(v) for k, v in overrides.items()}}
    if node.startswith("openml_"):
        from r1.c3.features import openml_active_keys
        active = openml_active_keys(node, full["model_type"])
    else:
        active = set(full)
    return tuple(sorted((k, v) for k, v in full.items() if k in active))


def build_node(node: str, edits: list[dict]) -> dict:
    configs = {"c0": {"edits": [], "overrides": {}}}
    for k, e in enumerate(edits, start=1):
        configs[f"c{k}"] = {"edits": [k], "overrides": {e["symbol"]: e["new"]}}
    seen = {active_projection(node, c["overrides"], edits): cid for cid, c in configs.items()}
    if len(seen) != len(configs):
        raise DesignError(f"STOP: {node}: two of c0..c5 are the same configuration")
    excluded, triples = {}, []
    for i, j in itertools.combinations(range(1, len(edits) + 1), 2):
        ei, ej = edits[i - 1], edits[j - 1]
        cid = f"c{i}{j}"
        if ei["symbol"] == ej["symbol"]:
            excluded[cid] = "same_symbol"
            continue
        overrides = {ei["symbol"]: ei["new"], ej["symbol"]: ej["new"]}
        proj = active_projection(node, overrides, edits)
        if proj in seen:
            excluded[cid] = f"identical_to:{seen[proj]}"
            continue
        seen[proj] = cid
        configs[cid] = {"edits": [i, j], "overrides": overrides}
        for parent, link in ((f"c{i}", j), (f"c{j}", i)):
            rho = edits[link - 1]["rho_joint"]
            near = rho is None or not (float(rho) < NEAR_DUPLICATE)
            triples.append({"id": f"c0>{parent}>{cid}", "g": "c0", "p": parent, "c": cid,
                            "link_pc_edit": link, "link_pc_rho_joint": rho,
                            "link_gp_rho_joint": edits[int(parent[1:]) - 1]["rho_joint"],
                            "near_duplicate_pc": near, "primary": not near})
    return {"edits": edits, "configs": configs, "excluded_children": excluded, "triples": triples,
            "n_configs": len(configs), "n_triples": len(triples),
            "n_primary_triples": sum(t["primary"] for t in triples)}


def build_design(repo: Path = REPO) -> dict:
    edits = declared_edits(repo)
    nodes = {n: build_node(n, edits[n]) for n in T0_NODES}
    n_cfg = sum(v["n_configs"] for v in nodes.values())
    return {"schema": SCHEMA, "run_id": RUN_ID, "seed_block": [SEED_BLOCK[0], SEED_BLOCK[-1], len(SEED_BLOCK)],
            "near_duplicate": NEAR_DUPLICATE, "decision_nodes": list(DECISION_NODES),
            "noise_source": {"path": NOISE_SOURCE, "sha256": NOISE_SOURCE_SHA256},
            "edit_sources": {k: v[0] for k, v in EDIT_SOURCES.items()},
            "nodes": nodes, "n_configs": n_cfg, "n_seed_runs": n_cfg * len(SEED_BLOCK),
            "n_repeat_runs": n_cfg, "n_triples": sum(v["n_triples"] for v in nodes.values()),
            "n_primary_triples": sum(v["n_primary_triples"] for v in nodes.values())}


def design_sha256(design: dict) -> str:
    return hashlib.sha256(json.dumps(design, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    d = build_design()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"design_sha256": design_sha256(d), "n_configs": d["n_configs"], "n_seed_runs": d["n_seed_runs"],
                      "n_triples": d["n_triples"], "n_primary_triples": d["n_primary_triples"],
                      "per_node": {n: [v["n_configs"], v["n_triples"], v["n_primary_triples"],
                                       v["excluded_children"]] for n, v in d["nodes"].items()}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
