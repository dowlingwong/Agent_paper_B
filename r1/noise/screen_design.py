#!/usr/bin/env python3
"""Design of the direct screening measurement R1-SCREEN-MEASURE (tier E). Pure: no harness, no run, no outcome.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md``.

What this module fixes, from pinned files only (every input is checked against its sha256 before use):

* the eight T0 nodes (``r1/c3/p3_split.py`` ``T0_NODES``, a tested copy of ``gate.T0_NODES``);
* per node, the five E1 single edits c1..c5 of the pinned noise source
  ``results/r1/noise/D28_REPAIR_20261027/summary.json`` (the source both sweeps and the D.3 draft pin), in the order of
  the edits file that source cites for the node, each with ``rho_joint`` = corr(c0, c_k) over the 30 joint seeds
  3001-3030 of that E1 run;
* the two-edit children c_ij = c0 + e_i + e_j (every pair i < j), after the two exclusion rules written before any run:
  - ``same_symbol``: e_i and e_j set the same symbol, so no single configuration holds both;
  - ``identical_to:<id>``: the child's active projection (the D25 active keys of ``r1/c3/features.py`` for its
    ``model_type``; every symbol on the MLP nodes) equals that of c0, a single edit or a child earlier in (i, j)
    order, so it is the same configuration as one already in the design (identical metrics under CRN);
* the lineage triples: for each retained child, (c0, c_i, c_ij), whose g -> p link applies e_i and whose p -> c link
  applies e_j, and (c0, c_j, c_ij), with the links the other way round;
* the near-duplicate links: a link whose edit has ``rho_joint`` >= 0.95 (``NEAR_DUPLICATE``) in the pinned E1 data, or
  no ``rho_joint`` (fail closed);
* the primary triples: those with **neither** link near-duplicate. The population partial correlation under a shared
  component tends to 0 as either link's correlation tends to 1 (it is symmetric in the two links), so a triple with a
  near-duplicate link cannot show a shared component of the reference size; such triples enter only the secondary
  analysis. Each triple carries its population partial under the two reference shares (``REFERENCE_SHARES``), computed
  from the E1 correlations of its two links (``reference_partial``), which documents this per triple;
* the testable nodes: those with at least one primary triple. A node without one is NOT_TESTED by design.

Run: ``python -m r1.noise.screen_design --out <json>`` writes the design (metadata only; no metric is read).
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

from r1.harness import REPO

SCHEMA = "r1_screen_measure_design/v2"
RUN_ID = "smeas-20261123-a"                     # proposed; no run has used it
SEED_BLOCK = tuple(range(3301, 3421))          # 120 fresh joint seeds (train seed = split seed); screen_seeds.py
NEAR_DUPLICATE = 0.95                          # a link's E1 rho_joint at or above this: near-duplicate link
# The two shared shares behind R1-SCREEN-MEASURE's power figures (report SCREENING_TEST_20261122 §4.2 and
# r1/noise/screening_test.py POWER_SHARES, branch mac-screening-test-20261122): with link correlation 0.82 they give a
# sibling partial of 0.24 (the E1 proxy's lower end) and 0.37 (its point estimate).
REFERENCE_SHARES = (0.7082, 0.7891)
T0_NODES = ('digits_mlp', 'openml_breast_w', 'openml_climate', 'openml_credit_approval', 'openml_ionosphere',
            'openml_sonar', 'openml_wdbc', 'tabular_mlp')       # == r1.c3.p3_split.T0_NODES (tested)
DECISION_NODES = T0_NODES                      # R1-SCREEN-MEASURE: "on all eight T0 nodes ... If any node returns SHARED"
SEVEN_NODES = tuple(n for n in T0_NODES if n != "openml_wdbc")  # PRE-WDBC primary set; reported as a second reading

NOISE_SOURCE = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SOURCE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
# The edits files the noise source cites (its "sources"), with their sha256 and the status of the run they come from.
EDIT_SOURCES = {
    "results/r1/pilot/E1_20261022T214606Z/edits.json":
        ("a37adfa3ffbfb7847f3e03fee061760172af7923d453c6c0649bbf730df6a7f6",
         ("digits_mlp", "tabular_mlp", "openml_ionosphere", "openml_credit_approval"),
         "accepted (R1-E1-PILOT-ACCEPT): E1 common run of 22 Oct, aarch64 VM, harness 4012897a"),
    "results/r1/pilot/E1_D28_REPAIR_20261027/edits.json":
        ("2e232470254312574ae290e3700acebdb1c2ec491460719c2d1a8c81067d78c3",
         ("openml_breast_w", "openml_sonar", "openml_wdbc"),
         "PILOT (no acceptance row): D21 re-measurement of the repaired nodes (R1-D28-REPAIR), deepthought, harness 6adf3859"),
    "results/r1/pilot/E1_D28_CLIMATE_20261027/edits.json":
        ("5331765d1a58204cb0f6b7ba0273691507d8e5dfd2739b95d863feee16e725f2", ("openml_climate",),
         "PILOT (no acceptance row): D21 measurement of the reserve node, deepthought, harness 6adf3859"),
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


def declared_edits(repo: Path = REPO) -> tuple[dict[str, list[dict]], dict[str, str]]:
    """node -> five edits {symbol, old, new, rho_joint} in the order of the cited edits file (pinned), and
    node -> the status of the data its rho_joint comes from."""
    summary = _load_pinned(NOISE_SOURCE, NOISE_SOURCE_SHA256, repo)
    out, status = {}, {}
    for rel, (sha, nodes, why) in EDIT_SOURCES.items():
        edits = _load_pinned(rel, sha, repo)
        for node in nodes:
            rows = summary["nodes"][node]["edits"]
            rho = {r["edit"]: r.get("rho_joint") for r in rows}
            node_edits = edits[node]
            if len(node_edits) != 5 or [edit_label(e) for e in node_edits] != [r["edit"] for r in rows]:
                raise DesignError(f"STOP: {node}: edits file and noise source disagree")
            out[node] = [{**e, "rho_joint": rho[edit_label(e)]} for e in node_edits]
            status[node] = f"{why}; {rel}"
    if set(out) != set(T0_NODES):
        raise DesignError(f"STOP: edit sources cover {sorted(out)}, not the eight T0 nodes")
    return {n: out[n] for n in T0_NODES}, {n: status[n] for n in T0_NODES}


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
        if "model_type" not in full:
            raise DesignError(f"STOP: {node}: the design edits no model_type, so activity cannot be projected")
        from r1.c3.features import openml_active_keys
        active = openml_active_keys(node, full["model_type"])
    else:
        active = set(full)
    return tuple(sorted((k, v) for k, v in full.items() if k in active))


def link_coefficient(rho: float, s: float) -> float:
    """r_w with s + (1 - s) r_w = rho, clipped at 0 (``screening_test.link_coefficient``)."""
    return max(0.0, (rho - s) / (1 - s)) if s < 1 else 0.0


def shared_lineage_partial(s: float, rho_gp: float, rho_pc: float) -> float:
    """Population corr(c, g | p) under e = u + w: u shared by every configuration at a seed (share s), w with the
    product kernel over edits, each link's marginal correlation set to its E1 rho_joint (r_w clipped at 0)."""
    a, b = link_coefficient(rho_gp, s), link_coefficient(rho_pc, s)
    gp, pc, gc = s + (1 - s) * a, s + (1 - s) * b, s + (1 - s) * a * b
    den = (1 - gp * gp) * (1 - pc * pc)
    return (gc - gp * pc) / math.sqrt(den) if den > 0 else 0.0


def _near(rho) -> bool:
    return rho is None or not (float(rho) < NEAR_DUPLICATE)


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
        for gp_edit, pc_edit in ((i, j), (j, i)):
            r_gp, r_pc = edits[gp_edit - 1]["rho_joint"], edits[pc_edit - 1]["rho_joint"]
            near_gp, near_pc = _near(r_gp), _near(r_pc)
            ref = ({f"{s:.4f}": round(shared_lineage_partial(s, float(r_gp), float(r_pc)), 6) for s in REFERENCE_SHARES}
                   if r_gp is not None and r_pc is not None else None)
            triples.append({"id": f"c0>c{gp_edit}>{cid}", "g": "c0", "p": f"c{gp_edit}", "c": cid,
                            "link_gp_edit": gp_edit, "link_pc_edit": pc_edit,
                            "link_gp_rho_joint": r_gp, "link_pc_rho_joint": r_pc,
                            "near_duplicate_gp": near_gp, "near_duplicate_pc": near_pc,
                            "primary": not (near_gp or near_pc),
                            "pc_only_rule": not near_pc,     # the superseded draft rule; a secondary reading only
                            "reference_partial": ref})
    n_primary = sum(t["primary"] for t in triples)
    return {"edits": edits, "configs": configs, "excluded_children": excluded, "triples": triples,
            "n_configs": len(configs), "n_triples": len(triples), "n_primary_triples": n_primary,
            "testable": n_primary > 0}


def build_design(repo: Path = REPO) -> dict:
    edits, status = declared_edits(repo)
    nodes = {n: {**build_node(n, edits[n]), "rho_source": status[n]} for n in T0_NODES}
    n_cfg = sum(v["n_configs"] for v in nodes.values())
    return {"schema": SCHEMA, "run_id": RUN_ID, "seed_block": [SEED_BLOCK[0], SEED_BLOCK[-1], len(SEED_BLOCK)],
            "near_duplicate": NEAR_DUPLICATE, "reference_shares": list(REFERENCE_SHARES),
            "decision_nodes": list(DECISION_NODES), "seven_nodes": list(SEVEN_NODES),
            "testable_nodes": [n for n in T0_NODES if nodes[n]["testable"]],
            "noise_source": {"path": NOISE_SOURCE, "sha256": NOISE_SOURCE_SHA256},
            "edit_sources": {k: v[0] for k, v in EDIT_SOURCES.items()},
            "nodes": nodes, "n_configs": n_cfg, "n_seed_runs": n_cfg * len(SEED_BLOCK),
            "n_repeat_runs": n_cfg, "n_triples": sum(v["n_triples"] for v in nodes.values()),
            "n_primary_triples": sum(v["n_primary_triples"] for v in nodes.values())}


def design_sha256(design: dict) -> str:
    return hashlib.sha256(json.dumps(design, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def summary_line(design: dict) -> dict:
    return {"design_sha256": design_sha256(design), "n_configs": design["n_configs"],
            "n_seed_runs": design["n_seed_runs"], "n_repeat_runs": design["n_repeat_runs"],
            "n_triples": design["n_triples"], "n_primary_triples": design["n_primary_triples"],
            "testable_nodes": design["testable_nodes"],
            "per_node": {n: {"configs": v["n_configs"], "triples": v["n_triples"], "primary": v["n_primary_triples"],
                             "excluded_children": v["excluded_children"]} for n, v in design["nodes"].items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    d = build_design()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary_line(d), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
