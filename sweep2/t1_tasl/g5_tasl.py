"""G.5 T1 label runs on the TASL pair: the spec validator and the G.5 switch (G.5 code unit, part 3a).

EVIDENCE table. This module validates ``g5_tasl_spec.json``, checks the signed note line by line, and gates every G.5
job start; its runner is ``g5_job.run_job`` (part 3b-1: the campaign waves, audit chunks, diagnostics and STOP
counters), reached only after every check below. The seal step, assembly, release locks and the REL-T1-G1B copy step
are part 3b-2. AI-assisted (Claude). Authority: the G.5 authorization draft revision 8
(``docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md``, accepted in round 4 of
``docs/r1/reviews/T1_G5_DRAFT_TASL_REVIEW_20261122.md``), §2, §4, §5, §7, §9, §11.

* **Decisions (§11).** Every open decision is an explicit field ``decisions.<id>.option`` with the recommended option A
  as default and ``signed: false``. ``apply_options`` switches an option and sets the fields it governs; the validator
  checks each field against the option. What each non-default option changes, or why it is refused:
  - G5-W B: ``campaign.W_semantics`` ``worker_runs`` with ``llm_call_cap`` 80, audited band 150-240. Launch refused:
    the v2-diff engine has no worker-run budget (harness work) and the G.4 pilot ran W = 20 manager calls (P3).
  - G5-TEMP B: temperature 0.0. Launch refused unless the G.4 pilot spec (``g4_tasl_spec.json``'s ``pilot``
    block, which P3 reads) ran at 0, i.e. a re-issued G.4 spec.
  - G5-MEM B: modes ``history`` and ``none``, 12 instances each, audited band doubled. Launch refused unless
    the G.4 pilot spec ran both modes (P3). G5-MEM A needs ``e4_amendment_row`` (it amends E4's "both
    memory modes"). G5-MEM C is refused (not built): the draft gives no assignment of the split file's 12 instances
    to two modes of 6, and C contradicts R1-BX-D8-V3-B's 12 instances per node.
  - G5-AUDIT B: audit scope ``ok`` outcomes only (G5-DIV's denominator is then weaker; reported). ``reuse_parent_runs``
    may be false under either option (§2.4); E5 on any seed block other than the label seeds is refused (it would need
    a row amending R1-B2-DECOUPLE).
  - G5-DIV B and C: per-node thresholds from inputs the spec carries (the pilot's divergent counts; the G.1b
    divergent-row rates), required at launch; ``divergence_threshold`` computes them.
  - G5-TASL-GPUH B: both cards count; needs ``proposer.server_stopped_during_audits`` true and the projection plus the
    campaign hours within the cap.
  - G5-SLOT B: refused (not built, §2.10).
  - G5-ARPEND A: autoresearch's noise-floor copy, environment, P10 declaration and host check are PENDING markers in
    the spec; the switch reads them from the one completion record on published main (STOP 15). B: the spec carries
    them, filled at signature.
  Any option other than the recommended row needs the cap of its row: the validator refuses a cap below the
  pre-pilot projection at ran share 0.6 (K = 10) under the chosen options. That is a floor only; the cap the draft
  sizes (share 0.8 plus 10 %) is carried by the P7 recompute and the signature.
* **Key values (§5).** ``note_lines`` renders every key line of the note from the spec, with K (P4) and the
  freeze-wait date (STOP 14) read from the note: both can move by a docs-only amendment citing an author row on main.
  ``check_note`` requires each line verbatim, the binding fields (``paper_commit``, ``spec_sha256``), P1-P11 PASS, and
  the reviews P5 and P8 cite on main with ``Verdict: ACCEPTED``.
* **The switch** (``launch``): off by default, both keys (``--enable`` and ``G5_TASL_ENABLE_REAL=1``); then the note,
  the decisions row (and the E4 row under G5-MEM A), the TASL-2 host check, the C12 record on main under
  ``cuda_ipc: c12`` (P1), the seven-node REL-T1-G1B copy with its cross-check gate record (reviewed, by sha256), and
  for autoresearch its completion record (STOP 15) or, under G5-ARPEND B, the spec's items, then
  ``g1b_tasl_join.noise_floor_by_node`` on the two copies; a node that does not qualify under D21 is STOP 5; then the
  freeze wait (STOP 14), ``g5_pin_check`` on the two G.5 commits (STOP 13), the node's family checkout at its G.5
  commit and clean, the per-family measurement-path identity against the G.1b pin (P5; no file may be added under
  ``nodes/``, ``third_party/``, ``configs/trackg/`` or ``node_lib/``, and in trackg only the declared G.5 files), and
  the TASL launch binding (``g1b_tasl.verify_launch_tasl`` after the import-source check; LB A).
* **P3** reads what the G.4 pilot ran from ``g4_tasl_spec.json``'s ``pilot`` block, so only a re-issued G.4 spec can
  clear a P3 blocker.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "g4"))
import g1b_tasl as G  # noqa: E402
import g4_tasl as T4  # noqa: E402
import g4_lib  # noqa: E402
import g5_pin_check as PC  # noqa: E402
import g1b_crosscheck as X  # noqa: E402
import g1b_tasl_join as J  # noqa: E402

L = G.L
Stop, NodeStop = G.Stop, G.NodeStop
SCHEMA = "g5_tasl_labels/v1"
EVIDENCE = "EVIDENCE"
GPU_MODEL = G.GPU_MODEL
ADA_MODEL = "NVIDIA RTX 6000 Ada Generation"
WORKER_HOST, PROPOSER_HOST = "TASL-2", "TASL-7"
DRIVERS = {"worker": "535.309.01", "proposer": "580.178.04"}          # R1-T1-TASL-ENV
AR = "autoresearch_fixedtokens"
SEVEN = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist", "mlgym_breakout_minatar",
         "mlgym_houseprice")
T1_NODES = SEVEN + (AR,)
FAMILIES = {"G5-7": PC.PIN_SEVEN, "G5-AR": PC.PIN_AR}                  # G5-PIN B (R1-G5-DECISIONS)
FAMILY_SPECS = {"G5-7": "sweep2/t1_tasl/g1b_tasl_spec.json", "G5-AR": "sweep2/t1_tasl/g1b_tasl_ar_spec.json"}
DECISIONS = ("G5-W", "G5-TEMP", "G5-MEM", "G5-AUDIT", "G5-DIV", "G5-TASL-GPUH", "G5-SLOT", "G5-ARPEND")
OPTIONS = {"G5-W": ["A", "B"], "G5-TEMP": ["A", "B"], "G5-MEM": ["A", "B", "C"], "G5-AUDIT": ["A", "B"],
           "G5-DIV": ["A", "B", "C"], "G5-TASL-GPUH": ["A", "B"], "G5-SLOT": ["A", "B"], "G5-ARPEND": ["A", "B"]}
AR_PENDING = "PENDING: G5-ARPEND A (from the completion record docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md)"
AR_FILL_B = "TODO: G5-ARPEND B (filled at signature)"
AR_PENDING_ITEMS = ["host_check", "noise_floor_copy", "environment", "tails"]   # §2.13: the spec's PENDING markers,
#                                                                       named as the completion record's keys
SCOPE = {"A": "non_inert_non_duplicate_evaluated_incl_divergent_and_timed_out", "B": "ok_outcome_only"}
SPLIT_SHA256 = "b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569"
SPLIT_SALT = "c3_t1_split/v1"
PREREG_SHA256 = "aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5"
GATE = {"path": "r1/c3/gate.py", "commit": "31dab9efb94b7f187ec44cab1bc4a4ad63c1085d",
        "sha256": "a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23"}   # v3.1, R1-BX-D8-CONFIRM-V31
INSTANCE_SEEDS = (5101, 5112)
SEED_BLOCKS = {"10": {"label": [7001, 7005], "evaluation": [7006, 7010]},
               "6": {"label": [7001, 7003], "evaluation": [7006, 7008]}}
RESERVED = ((1001, 3030, "G.1b"), (4001, 4099, "G.4"), (5001, 5006, "the E1b audit seeds"), (7001, 7010, "audit"),
            (8001, 8010, "census"), (9001, 10 ** 9, "exam"))
WAVES = [[1, 4], [5, 12]]
JOBS = ("campaigns-wave1", "audits-wave1", "campaigns-wave2", "audits-wave2")
SEED_RULE = 'sha256(f"{manager_seed}:{step}")[:8]'
ENABLE_ENV = "G5_TASL_ENABLE_REAL"
NOTE_DIR = "docs/r1/authorizations"
NOTE_NAME = re.compile(r"^c3_t1_labels_(\d{8})\.md$")
RUN_ID = re.compile(r"^c3_t1_labels_\d{8}$")
RECORD_NAME = re.compile(r"^docs/r1/reports/[A-Za-z0-9_.\-]+/G5_AR_PREREQUISITES_\d{8}\.md$")
RECORD_TOKEN = "G5_AR_PREREQUISITES"
XC_SPEC = "sweep2/t1_tasl/g1b_crosscheck_spec.json"
G5_TRACKG_ADDITIONS = ("src/autoresearch/trackg/audit_g5.py", "src/autoresearch/trackg/diagnostics_g5.py")  # P5
NO_ADDITIONS = ("nodes/", "third_party/", "configs/trackg/", "src/autoresearch/trackg/node_lib/")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AR_NOTE = re.compile(r"^docs/r1/authorizations/g1b_ar_t1_tasl_\d{8}\.md$")
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-T1-TASL-ENV", "R1-G1B-TIMEOUT", "R1-G5-DECISIONS", "R1-SWEEP2-PREREG",
             "R1-SWEEP2-RELEASE-DECISIONS", "R1-BX-D8-CONFIRM-V31", "R1-G1B-JOIN", "R1-HARNESS-ISOLATION")
ROW_ID = re.compile(r"^R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9]$")
CITED = re.compile(r"^(\S+) sha256 ([0-9a-f]{64})$")
VERDICT_ACCEPTED = re.compile(r"^Verdict: ACCEPTED\s*$", re.M)
PLACEHOLDER = re.compile(r"<[^>]*>")
CUDA_IPC_ACCEPTANCE = (
    "The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2, the residual risk that harness-isolation "
    "host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested "
    "on TASL-2: no frozen parent exports a CUDA tensor, harness 2d09f9a9 documents that no node uses cuda_share or "
    "cuda_open, and every run record that is not effective with empty waivers and exceptions still STOPs its job "
    "(STOP 2). Disclosed in the T1 report.")


# =============================================================================================== small helpers
def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _get(spec: dict, path: tuple):
    cur = spec
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return KeyError
        cur = cur[k]
    return cur


def _set(spec: dict, path: tuple, value) -> None:
    cur = spec
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = value


def _ph(value) -> bool:
    """A placeholder: a string starting with TODO / PENDING / ... (``g1b_lib``), or None."""
    return value is None or L._placeholder(value)


def _rel_ok(rel) -> bool:
    return isinstance(rel, str) and bool(rel) and not rel.startswith("/") and ".." not in Path(rel).parts \
        and not _ph(rel)


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _repo_file_sha(rel: str) -> str | None:
    p = REPO_ROOT / rel
    return L._sha_file(p) if p.is_file() else None


def options(spec: dict) -> dict:
    return {k: (spec.get("decisions") or {}).get(k, {}).get("option") for k in DECISIONS}


def node_entry(spec: dict, name: str) -> dict:
    for node in spec["nodes"]:
        if node["node"] == name:
            return node
    raise Stop(f"STOP: {name} is not a G.5 node")


# =============================================================================================== options
def audited_band(opts: dict) -> list[int]:
    """STOP 9's band (§2.1, §4 item 9): 100-200 under G5-W A, 150-240 under B; doubled under G5-MEM B."""
    lo, hi = (100, 200) if opts["G5-W"] == "A" else (150, 240)
    k = 2 if opts["G5-MEM"] == "B" else 1
    return [lo * k, hi * k]


def divergence_block(option: str, pilot_nodes: list[str]) -> dict:
    """The ``divergence`` block of each G5-DIV option (§2.5); inputs that come from measurements are PENDING."""
    common = {"min_audited": 40, "denominator": "audited label proposals",
              "numerator": "E5-divergent on the label seeds"}
    if option == "A":
        return {"rule": "fixed", "threshold": 0.2, "literal_2x_census": 0.25, **common}
    if option == "B":
        return {"rule": "pilot_cp", "cap": 0.2, "floor": 0.1, "other_nodes": 0.2, "cp_level": 0.95, **common,
                "pilot_counts": {n: {"divergent": "PENDING", "proposals": "PENDING"} for n in pilot_nodes}}
    return {"rule": "g1b_2x", "cap": 0.2, **common,
            "g1b_divergent_rows": {n: {"divergent": "PENDING", "rows": "PENDING"} for n in T1_NODES}}


def required_settings(spec: dict) -> dict:
    """{field path: value} that the chosen options fix (the validator compares each)."""
    o = options(spec)
    w_a, mem = o["G5-W"] == "A", o["G5-MEM"]
    req = {("campaign", "W"): 20,
           ("campaign", "W_semantics"): "manager_calls" if w_a else "worker_runs",
           ("campaign", "llm_call_cap"): None if w_a else g4_lib.G5_LLM_CALL_CAP,
           ("campaign", "temperature"): 0.2 if o["G5-TEMP"] == "A" else 0.0,
           ("memory", "modes"): ["history"] if mem == "A" else ["history", "none"],
           ("memory", "instances_per_mode"): 6 if mem == "C" else 12,
           ("key_values", "audited_band"): audited_band(o),
           ("audit", "scope"): SCOPE.get(o["G5-AUDIT"]),
           ("audit", "cross_instance_duplicates"): "audit_once",
           ("audit", "e5_seed_block"): "label",
           ("divergence", "rule"): {"A": "fixed", "B": "pilot_cp", "C": "g1b_2x"}.get(o["G5-DIV"]),
           ("cap", "counts"): "worker_card" if o["G5-TASL-GPUH"] == "A" else "both_cards",
           ("slots", "worker_slots"): 1,
           ("ar_prerequisites", "mode"): o["G5-ARPEND"]}
    if o["G5-TASL-GPUH"] == "B":
        req[("proposer", "server_stopped_during_audits")] = True
    return req


def apply_options(spec: dict, choices: dict) -> dict:
    """A copy of the spec with the given options and every field they govern; the options are left unsigned."""
    out = copy.deepcopy(spec)
    for key, opt in choices.items():
        if key not in DECISIONS or opt not in OPTIONS[key]:
            raise Stop(f"STOP: unknown decision or option {key}={opt}")
        out["decisions"][key]["option"] = opt
        out["decisions"][key]["signed"] = False
    for path, value in required_settings(out).items():
        _set(out, path, copy.deepcopy(value))
    o = options(out)
    if "G5-DIV" in choices:
        out["divergence"] = divergence_block(o["G5-DIV"], out["pilot_basis"]["nodes"])
    if "G5-TASL-GPUH" in choices and o["G5-TASL-GPUH"] == "A":
        out["proposer"]["server_stopped_during_audits"] = False
    if "G5-MEM" in choices:
        out["e4_amendment_row"] = ("PENDING: G5-MEM A needs the author's PLAN row amending E4's 'both memory modes'"
                                   if o["G5-MEM"] == "A" else None)
    if "G5-ARPEND" in choices:
        marker = AR_PENDING if o["G5-ARPEND"] == "A" else AR_FILL_B
        ar = node_entry(out, AR)
        ar["env"], ar["tails"] = marker, marker
        out["noise_floor"]["ar"].update(copy=marker, sha256=marker, review=marker, sealed_path=marker)
        out["harness_families"]["G5-AR"]["isolation_host_check"] = marker if o["G5-ARPEND"] == "A" else \
            {"record": marker, "sha256": marker}
        out["ar_prerequisites"]["pending"] = list(AR_PENDING_ITEMS) if o["G5-ARPEND"] == "A" else []
        if o["G5-ARPEND"] == "B":
            prop = out["ar_prerequisites"]["proposed_environment"]
            out["envs"][prop["name"]] = {"freeze": prop["freeze"], "sha256": prop["sha256"], "python": prop["python"]}
        else:
            out["envs"].pop(out["ar_prerequisites"]["proposed_environment"]["name"], None)
    return out


def clopper_pearson_upper(x: int, n: int, level: float = 0.95) -> float:
    """The upper limit of the two-sided Clopper-Pearson interval at ``level`` (tail (1 - level) / 2), by bisection on
    the binomial CDF."""
    if not (isinstance(x, int) and isinstance(n, int) and 0 <= x <= n and n > 0):
        raise Stop("STOP: Clopper-Pearson needs integer counts 0 <= x <= n, n > 0")
    if x == n:
        return 1.0
    tail = (1.0 - level) / 2.0

    def cdf(p: float) -> float:
        return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(x + 1))
    lo, hi = x / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(mid) > tail:
            lo = mid
        else:
            hi = mid
    return hi


def divergence_threshold(spec: dict, node: str) -> dict:
    """STOP 1's threshold for one node under the chosen G5-DIV option (§2.5)."""
    d = spec["divergence"]
    if d["rule"] == "fixed":
        return {"node": node, "threshold": d["threshold"], "literal_2x_census": d["literal_2x_census"],
                "min_audited": d["min_audited"], "rule": "G5-DIV A"}
    if d["rule"] == "pilot_cp":
        counts = (d.get("pilot_counts") or {}).get(node)
        if counts is None:
            return {"node": node, "threshold": d["other_nodes"], "min_audited": d["min_audited"],
                    "rule": "G5-DIV B (not a pilot node)"}
        if not all(isinstance(counts.get(k), int) for k in ("divergent", "proposals")):
            raise Stop(f"STOP: G5-DIV B needs the pilot's divergent and proposal counts for {node}")
        ub = clopper_pearson_upper(counts["divergent"], counts["proposals"], d["cp_level"])
        return {"node": node, "threshold": round(min(d["cap"], max(2 * ub, d["floor"])), 6), "cp_upper": ub,
                "min_audited": d["min_audited"], "rule": "G5-DIV B"}
    rows = (d.get("g1b_divergent_rows") or {}).get(node) or {}
    if not all(isinstance(rows.get(k), int) for k in ("divergent", "rows")) or rows["rows"] <= 0:
        raise Stop(f"STOP: G5-DIV C needs the G.1b divergent-row counts for {node}")
    return {"node": node, "threshold": round(min(d["cap"], 2 * rows["divergent"] / rows["rows"]), 6),
            "min_audited": d["min_audited"], "rule": "G5-DIV C"}


def audit_seeds(spec: dict, k: int) -> dict:
    """The label and evaluation seeds at K (STOP 10: under K = 6, 7004-7005 and 7009-7010 are never used)."""
    if k not in (10, 6):
        raise Stop("STOP: K is 10 or 6")
    b = spec["audit"]["seed_blocks"][str(k)]
    return {"label": list(range(b["label"][0], b["label"][1] + 1)),
            "evaluation": list(range(b["evaluation"][0], b["evaluation"][1] + 1))}


def instance_seeds(spec: dict) -> list[int]:
    lo, hi = spec["instances"]["seeds"]
    return list(range(lo, hi + 1))


def split_from_rule(node: str, seeds: list[int]) -> dict:
    """§2.7: the 12 instances ordered by sha256("c3_t1_split/v1:" + node + ":" + seed); 6 test, 2 dev, 4 train."""
    order = sorted(seeds, key=lambda s: hashlib.sha256(f"{SPLIT_SALT}:{node}:{s}".encode()).hexdigest())
    ids = [f"{node}__s{s}" for s in order]
    return {"test": sorted(ids[:6]), "dev": sorted(ids[6:8]), "train": sorted(ids[8:])}


# =============================================================================================== projection
def dates_params(spec: dict) -> dict:
    """The R1-BX-D14 recompute inputs for the eight-node G.5 table: ``g4_tasl_dates_params.json`` with the spec's nodes
    and census times, the nodes censused on the 4090 exempt from the ratio, and the options' W, memory modes, parent
    reuse and cap."""
    p = json.loads((HERE / "g4_tasl_dates_params.json").read_text())
    o = options(spec)
    p["t1_nodes"] = [n["node"] for n in spec["nodes"]]
    p["run_seconds"] = {n["node"]: n["run_seconds"] for n in spec["nodes"]}
    p["ratio_exempt_nodes"] = sorted(n["node"] for n in spec["nodes"] if n.get("census_gpu_model") == GPU_MODEL)
    p["w_semantics"] = spec["campaign"]["W_semantics"]
    p["mem_modes"] = len(spec["memory"]["modes"]) if o["G5-MEM"] == "B" else 1
    p["reuse_parent_runs"] = bool(spec["audit"]["reuse_parent_runs"])
    p["g5_cap_gpu_hours"] = spec["key_values"]["cap_gpu_hours"]
    p["llm_seconds_fallback"] = spec["projection"]["llm_seconds_fallback"]
    p["startup_s"] = spec["projection"]["startup_s"]
    return p


def projection(spec: dict) -> dict:
    """Pre-pilot GPU-hours under the chosen options at ran share 0.6 and 0.8 (K = 10 and 6), the cap's basis per
    G5-TASL-GPUH (A: worker card; B: worker card + the proposer card over the campaign waves, server stopped during
    the audits)."""
    out = {}
    both = options(spec)["G5-TASL-GPUH"] == "B"
    for share in (0.6, 0.8):
        p = dates_params(spec) | {"ran_share_fallback": share}
        r = T4.recompute_dates({}, p, today=date(2026, 11, 23))
        for k in ("10", "6"):
            per = r["g5_by_K"][k]["per_node"]
            worker = round(sum(v["gpu_hours"] for v in per.values()), 1)
            campaign = round(sum(v["campaign_gpu_hours"] for v in per.values()), 1)
            out[f"share={share} K={k}"] = {"worker_gpu_hours": worker, "campaign_gpu_hours": campaign,
                                           "capped_gpu_hours": round(worker + campaign, 1) if both else worker}
    return out


# =============================================================================================== the spec
def _check_split(spec: dict) -> dict:
    sf = spec["instances"]["split_file"]
    if sf.get("path") != "r1/c3/splits/c3_p3_split_v1.json" or sf.get("sha256") != SPLIT_SHA256 \
            or sf.get("salt") != SPLIT_SALT:
        raise Stop("STOP: instances.split_file must be r1/c3/splits/c3_p3_split_v1.json, sha256 b5967dd7…, salt "
                   "c3_t1_split/v1 (R1-SWEEP2-PREREG, PRE-SPLIT A)")
    raw = (REPO_ROOT / sf["path"]).read_bytes()
    if _sha_bytes(raw) != SPLIT_SHA256:
        raise Stop("STOP: the split file in the checkout differs from its frozen sha256")
    t1 = (json.loads(raw).get("t1") or {}).get("nodes") or {}
    if sorted(t1) != sorted(T1_NODES):
        raise Stop(f"STOP: the split file's T1 nodes {sorted(t1)} are not the eight G.5 nodes")
    for node, parts in t1.items():
        want = split_from_rule(node, instance_seeds(spec))
        if {k: sorted(v) for k, v in parts.items()} != want:
            raise Stop(f"STOP: the split file's assignment for {node} differs from the §2.7 rule")
    return {"path": sf["path"], "sha256": SPLIT_SHA256, "nodes": len(t1)}


def _check_seeds(spec: dict) -> None:
    inst = spec.get("instances") or {}
    if inst.get("per_node") != 12 or inst.get("seeds") != list(INSTANCE_SEEDS) or inst.get("waves") != WAVES:
        raise Stop("STOP: instances must be 12 per node, seeds 5101-5112, waves 1-4 and 5-12 (R1-BX-D8-V3-B, §3)")
    seeds = instance_seeds(spec)
    for lo, hi, what in RESERVED:
        clash = [s for s in seeds if lo <= s <= hi]
        if clash:
            raise Stop(f"STOP: instance seeds {clash} fall in the reserved {what} block")
    if (spec.get("audit") or {}).get("seed_blocks") != SEED_BLOCKS:
        raise Stop("STOP: audit.seed_blocks must be K = 10: 7001-7005 / 7006-7010 and K = 6: 7001-7003 / 7006-7008")


def g4_spec() -> dict:
    """The G.4 pilot spec on this checkout (P3 reads its ``pilot`` block)."""
    return json.loads((HERE / "g4_tasl_spec.json").read_text())


def pilot_settings(g4: dict) -> dict:
    """What the G.4 pilot ran (P3), from ``g4_tasl_spec.json``'s ``pilot`` block: W counts manager calls in the v2-diff
    pilot (``budget``), one memory mode, the temperature. Only a re-issued G.4 spec changes these."""
    pilot = g4["pilot"]
    return {"W_semantics": pilot.get("W_semantics", "manager_calls"), "W": pilot["budget"],
            "memory_modes": [pilot["memory_mode"]], "temperature": pilot["temperature"]}


def other_checkouts() -> set[str]:
    """The harness checkouts of G.1b (both specs, every host) and G.4: a G.5 family checkout is none of them."""
    out = set()
    for rel in FAMILY_SPECS.values():
        out |= {h.get("harness_dir") for h in json.loads((REPO_ROOT / rel).read_text())["hosts"].values()}
    out.add(g4_spec()["worker"].get("harness_dir"))
    return out - {None}


def _check_family(spec: dict, fam: str, launch: bool, o: dict) -> dict:
    f = (spec.get("harness_families") or {}).get(fam) or {}
    if f.get("g1b_pin") != FAMILIES[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_pin must be {FAMILIES[fam]} (G5-PIN B)")
    L._commit(f.get("g5_commit"), f"harness_families.{fam}.g5_commit", allow_placeholder=not launch)
    G._abs(f.get("harness_dir"), f"harness_families.{fam}.harness_dir")
    gs = f.get("g1b_spec") or {}
    if gs.get("path") != FAMILY_SPECS[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec.path must be {FAMILY_SPECS[fam]}")
    if gs.get("sha256") != _repo_file_sha(gs["path"]):
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec.sha256 differs from {gs['path']} in the checkout")
    g1b = json.loads((REPO_ROOT / gs["path"]).read_text())
    if gs.get("run_id") != g1b["run_id"] or g1b["harness"]["commit"] != FAMILIES[fam]:
        raise Stop(f"STOP: harness_families.{fam}.g1b_spec must name that spec's run_id and pin")
    if f["harness_dir"] in other_checkouts():
        raise Stop(f"STOP: harness_families.{fam}.harness_dir must not be a G.1b or G.4 checkout (they stay at their "
                   f"pins)")
    check = f.get("isolation_host_check")
    if fam == "G5-AR" and o["G5-ARPEND"] == "A":
        if check != AR_PENDING:
            raise Stop("STOP: under G5-ARPEND A, G5-AR's isolation_host_check is the PENDING marker (§2.13)")
    else:
        if not isinstance(check, dict) or not str(check.get("record", "")).startswith(("docs/r1/reports/", "TODO",
                                                                                         "PENDING")):
            raise Stop(f"STOP: harness_families.{fam}.isolation_host_check must name a report under docs/r1/reports/")
        if launch and _ph(check.get("record")):
            raise Stop(f"STOP: harness_families.{fam}.isolation_host_check.record must be filled")
        L._sha(check.get("sha256"), f"harness_families.{fam}.isolation_host_check.sha256",
               allow_placeholder=not launch)
    return g1b


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """The spec schema and its consistency with the decisions. Returns the options, the projection, the unsigned
    decisions and the launch blockers; ``launch=True`` raises on any blocker or unfilled field."""
    allow = not launch
    if spec.get("schema") != SCHEMA or spec.get("label") != EVIDENCE:
        raise Stop(f"STOP: spec must be {SCHEMA}, label {EVIDENCE}")
    run_id = spec.get("run_id")
    if not (_ph(run_id) and allow) and not (isinstance(run_id, str) and RUN_ID.fullmatch(run_id)):
        raise Stop("STOP: run_id must be c3_t1_labels_<YYYYMMDD>")
    for key, repo in (("paper", L.PAPER_REPO), ("harness", L.HARNESS_REPO)):
        if (spec.get(key) or {}).get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
    L._commit(spec["paper"].get("commit"), "paper.commit", allow_placeholder=allow)
    # --- decisions
    dec = spec.get("decisions") or {}
    if sorted(dec) != sorted(DECISIONS):
        raise Stop(f"STOP: decisions must be exactly {list(DECISIONS)} (§11 items 1-8)")
    for key in DECISIONS:
        d = dec[key]
        if d.get("options") != OPTIONS[key] or d.get("recommended") != "A" or d.get("option") not in OPTIONS[key] \
                or not isinstance(d.get("signed"), bool):
            raise Stop(f"STOP: decisions.{key} must carry option in {OPTIONS[key]}, recommended A, signed true/false")
    o = options(spec)
    unsigned = [k for k in DECISIONS if not dec[k]["signed"]]
    if o["G5-SLOT"] == "B":
        raise Stop("STOP: G5-SLOT B (audits on TASL-7 while campaigns pause) is not built (G.5 draft §2.10)")
    if o["G5-MEM"] == "C":
        raise Stop("STOP: G5-MEM C is not built: the draft gives no assignment of the split file's 12 instances to two "
                   "memory modes of 6 each, and C contradicts R1-BX-D8-V3-B (12 instances per node); an author row "
                   "would have to fix both first (G.5 draft §2.3)")
    bad = {"/".join(p): (_get(spec, p), v) for p, v in required_settings(spec).items() if _get(spec, p) != v}
    if bad:
        raise Stop(f"STOP: fields inconsistent with the chosen options (use apply_options): {bad}")
    blockers = []
    pb = spec.get("pilot_basis") or {}
    g4 = g4_spec()
    if set(pb) != {"run_id", "note", "nodes", "settings"} or pb.get("run_id") != g4["run_id"] or \
            not re.fullmatch(r"docs/r1/authorizations/g4_t1_tasl_\d{8}\.md", str(pb.get("note", ""))) \
            or pb.get("nodes") != [n["node"] for n in g4["nodes"]]:
        raise Stop("STOP: pilot_basis must name exactly the G.4 pilot run, its note and its nodes; what the pilot ran "
                   "is read from g4_tasl_spec.json's pilot block, not declared here (P3)")
    ran = pilot_settings(g4)
    for field, want in (("W_semantics", spec["campaign"]["W_semantics"]), ("W", spec["campaign"]["W"]),
                        ("memory_modes", spec["memory"]["modes"]), ("temperature", spec["campaign"]["temperature"])):
        if ran[field] != want:
            blockers.append(f"P3: the G.4 pilot {g4['run_id']} (g4_tasl_spec.json) ran {field} = {ran[field]!r}, "
                            f"the options need {want!r}: the pilot is re-run or amended first (a re-issued G.4 spec)")
    if o["G5-W"] == "B":
        blockers.append("G5-W B: the v2-diff engine has no worker-run budget with an LLM-call cap (harness code "
                        "unit, G.5 draft §9); not built")
    # --- harness families, identity, environments
    g1b = {fam: _check_family(spec, fam, launch, o) for fam in FAMILIES}
    dirs = [spec["harness_families"][f]["harness_dir"] for f in FAMILIES]
    if len(set(dirs)) != 2:
        raise Stop("STOP: the two G.5 harness families need two checkouts (G5-PIN B)")
    if spec.get("gpu_model") != GPU_MODEL or spec.get("model") != T4.MODEL:
        raise Stop("STOP: gpu_model must be the RTX 4090 and model the pinned gemma4_31b GGUF")
    if (spec.get("timeout_decision") or {}).get("basis") != g1b["G5-7"]["timeout_decision"]["basis"] or \
            not str(spec["timeout_decision"].get("authority", "")).startswith("R1-G1B-TIMEOUT"):
        raise Stop("STOP: timeout_decision must be census_slowest_x3 under R1-G1B-TIMEOUT (one basis for the table)")
    if not str((spec.get("host_decision") or {}).get("authority", "")).startswith("R1-T1-TASL-ENV"):
        raise Stop("STOP: host_decision.authority must be R1-T1-TASL-ENV")
    w = spec.get("worker") or {}
    ref = g1b["G5-7"]["hosts"][WORKER_HOST]
    if w.get("host") != WORKER_HOST or w.get("hostname") != ref["hostname"] or w.get("gpu_uuid") != ref["gpu_uuid"] \
            or w.get("driver") != DRIVERS["worker"] or w.get("lease") != "~/r1_locks/gpu0.lock":
        raise Stop("STOP: the worker is TASL-2 with the RTX 4090, driver and lease of the G.1b spec")
    for key in ("base", "runs_root", "sealed_root", "uv"):
        G._abs(w.get(key), f"worker.{key}")
    if w["sealed_root"] in (ref["sealed_root"], g4["worker"]["sealed_root"]):
        raise Stop("STOP: worker.sealed_root must be G.5's own (not G.1b's or G.4's)")
    G.cpu_list(w.get("cpus", ""))
    p = spec.get("proposer") or {}
    for key in ("host", "hostname", "gpu_uuid", "tailscale_address", "server_url", "binary", "binary_sha256",
                "expected_build", "model_path", "lease", "args", "bin_dir_manifest_sha256"):
        if p.get(key) != g4["proposer"][key]:
            raise Stop(f"STOP: proposer.{key} must equal the G.4 spec's (the server of the signed G.4 note)")
    T4.server_url_parts(p["server_url"])
    G._abs(p.get("run_dir"), "proposer.run_dir")
    if p["run_dir"] == g4["proposer"]["run_dir"] or p.get("driver") != DRIVERS["proposer"] or \
            not isinstance(p.get("server_stopped_during_audits"), bool):
        raise Stop("STOP: proposer.run_dir must be G.5's own, driver 580.178.04, server_stopped_during_audits a bool")
    G._abs(p.get("sealed_root"), "proposer.sealed_root")          # part 3b-2: the TASL-7 server seal
    run_dir, prop_sealed = Path(p["run_dir"]), Path(p["sealed_root"])
    if prop_sealed == run_dir or run_dir in prop_sealed.parents or prop_sealed in run_dir.parents:
        raise Stop("STOP: proposer.sealed_root must be apart from proposer.run_dir (the server seal, part 3b-2)")
    envs = dict(spec.get("envs") or {})
    prop_env = spec["ar_prerequisites"]["proposed_environment"]
    ar_env_ref = json.loads((REPO_ROOT / FAMILY_SPECS["G5-AR"]).read_text())["envs"]
    if {k: v for k, v in envs.items() if k != prop_env["name"]} != g4["envs"]:
        raise Stop("STOP: envs must be the census freezes torch312 and jax312 of R1-T1-TASL-ENV")
    if o["G5-ARPEND"] == "A" and prop_env["name"] in envs:
        raise Stop("STOP: under G5-ARPEND A autoresearch's environment comes from the completion record, not envs")
    if o["G5-ARPEND"] == "B" and envs.get(prop_env["name"]) != {k: prop_env[k] for k in ("freeze", "sha256",
                                                                                         "python")}:
        raise Stop("STOP: under G5-ARPEND B envs must carry autoresearch's environment (the proposed one)")
    ref_env = ar_env_ref.get(prop_env.get("name")) or {}
    if prop_env.get("name") != G.AR_ENV or any(prop_env.get(k) != ref_env.get(k) for k in ("freeze", "sha256",
                                                                                          "python")):
        raise Stop("STOP: ar_prerequisites.proposed_environment must be ar-cond7a as in the AR G.1b spec (P9)")
    # --- campaign, memory, audit, divergence
    c = spec.get("campaign") or {}
    if c.get("proposal_schema") != "manager_proposal/v2-diff" or c.get("cache_prompt") is not False \
            or c.get("max_tokens") != g4_lib.MAX_TOKENS or c.get("ctx") != T4.CTX or c.get("per_call_seed_rule") != SEED_RULE:
        raise Stop("STOP: campaign must be manager_proposal/v2-diff, cache_prompt false, cap 4096, ctx 32768, and the "
                   "engine's per-call seed rule")
    a = spec.get("audit") or {}
    if not isinstance(a.get("reuse_parent_runs"), bool) or \
            a.get("duplicate_key") != "instance, incumbent hash, candidate hash":
        raise Stop("STOP: audit.reuse_parent_runs must be a bool and the duplicate key R1-MAIN-PROPOSER (e)'s")
    _check_seeds(spec)
    split = _check_split(spec)
    d = spec.get("divergence") or {}
    if d != {**divergence_block(o["G5-DIV"], pb["nodes"]), **{k: d.get(k) for k in ("pilot_counts",
                                                                                   "g1b_divergent_rows") if k in d}}:
        raise Stop("STOP: the divergence block is not the one of the chosen G5-DIV option (§2.5)")
    if o["G5-DIV"] == "B" and sorted(d.get("pilot_counts") or {}) != sorted(pb["nodes"]):
        raise Stop("STOP: G5-DIV B needs pilot_counts for exactly the pilot nodes")
    if o["G5-DIV"] == "C" and sorted(d.get("g1b_divergent_rows") or {}) != sorted(T1_NODES):
        raise Stop("STOP: G5-DIV C needs g1b_divergent_rows for exactly the eight nodes")
    if o["G5-DIV"] in ("B", "C"):
        for n in (pb["nodes"] if o["G5-DIV"] == "B" else T1_NODES):
            try:
                divergence_threshold(spec, n)
            except Stop as exc:
                blockers.append(str(exc))
    # --- nodes
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or [n.get("node") for n in nodes] != list(T1_NODES):
        raise Stop(f"STOP: nodes must be the eight T1 nodes {list(T1_NODES)} (G5-AR A, R1-G5-DECISIONS)")
    on_4090 = T4.census_on_4090_nodes()
    for n in nodes:
        fam = "G5-AR" if n["node"] == AR else "G5-7"
        if n.get("family") != fam:
            raise Stop(f"STOP: {n['node']} runs on harness family {fam} (G5-PIN B)")
        r = {x["node"]: x for x in g1b[fam]["nodes"]}.get(n["node"])
        for key in ("spec_path", "node_dir", "node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256",
                    "run_seconds", "slowest_census_seconds", "census_record", "device", "cpus"):
            if n.get(key) != r.get(key):
                raise Stop(f"STOP: {n['node']}.{key} differs from its G.1b spec")
        if n.get("census_gpu_model") != (GPU_MODEL if n["node"] in on_4090 else ADA_MODEL):
            raise Stop(f"STOP: {n['node']}.census_gpu_model does not match the G.1b specs")
        if n["node"] == AR and o["G5-ARPEND"] == "A":
            if n.get("env") != AR_PENDING or n.get("tails") != AR_PENDING:
                raise Stop("STOP: under G5-ARPEND A autoresearch's env and tails are the PENDING marker (§2.13)")
            continue
        if n.get("env") != r["env"]:
            raise Stop(f"STOP: {n['node']}.env must be its G.1b environment {r['env']}")
        if n["env"] not in envs or n["env"] not in (w.get("env_python") or {}):
            raise Stop(f"STOP: {n['node']} needs {n['env']} in envs and worker.env_python")
        if n.get("tails") not in ("gaussian", "student_t") and not (allow and _ph(n.get("tails"))):
            raise Stop(f"STOP: {n['node']}.tails must be gaussian or student_t (P10)")
    for name, py in (w.get("env_python") or {}).items():
        G._abs(py, f"worker.env_python.{name}")
    # --- noise floor, autoresearch's prerequisites
    nf = spec.get("noise_floor") or {}
    for key, fam, schema in (("seven", "G5-7", G.SUMMARY_SCHEMA), ("ar", "G5-AR", G.AR_SUMMARY_SCHEMA)):
        e = nf.get(key) or {}
        if e.get("run_id") != spec["harness_families"][fam]["g1b_spec"]["run_id"] or e.get("schema") != schema:
            raise Stop(f"STOP: noise_floor.{key} must be the {schema} summary of run "
                       f"{spec['harness_families'][fam]['g1b_spec']['run_id']}")
        if key == "ar" and o["G5-ARPEND"] == "A":
            if any(e.get(k) != AR_PENDING for k in ("copy", "sha256", "review", "sealed_path")):
                raise Stop("STOP: under G5-ARPEND A noise_floor.ar is the PENDING marker (§2.13)")
            continue
        if launch and (not _rel_ok(e.get("copy")) or not _rel_ok(e.get("review"))):
            raise Stop(f"STOP: noise_floor.{key} must name its reviewed REL-T1-G1B copy and review")
        if launch and not str(e.get("sealed_path", "")).startswith("/"):
            raise Stop(f"STOP: noise_floor.{key}.sealed_path must be the sealed summary's absolute path")
        L._sha(e.get("sha256"), f"noise_floor.{key}.sha256", allow_placeholder=allow)
        if key == "seven":           # M3: the cross-check gate record travels with the seven-node copy
            xs = e.get("crosscheck_spec") or {}
            if xs.get("path") != XC_SPEC or xs.get("sha256") != _repo_file_sha(XC_SPEC):
                raise Stop(f"STOP: noise_floor.seven.crosscheck_spec must be {XC_SPEC} at its sha256 in the checkout")
            L._sha(e.get("gate_sha256"), "noise_floor.seven.gate_sha256", allow_placeholder=allow)
            if launch and (not _rel_ok(e.get("gate_copy")) or
                           Path(e["gate_copy"]) != Path(e["copy"]).parent / "crosscheck_gate.json"):
                raise Stop("STOP: noise_floor.seven.gate_copy must be crosscheck_gate.json beside the summary copy")
    ap = spec.get("ar_prerequisites") or {}
    if ap.get("node") != AR or ap.get("record_dir") != "docs/r1/reports" or \
            ap.get("record_name") != "G5_AR_PREREQUISITES_YYYYMMDD.md" or \
            ap.get("pending") != (AR_PENDING_ITEMS if o["G5-ARPEND"] == "A" else []):
        raise Stop("STOP: ar_prerequisites must name autoresearch, the record pattern and the PENDING items of "
                   "the chosen G5-ARPEND option")
    # --- key values, cap, gate, preregistration, rows
    kv = spec.get("key_values") or {}
    for key in ("liveness_floor", "invalid_share_stop", "infrastructure_stop_share"):
        if not isinstance(kv.get(key), (int, float)) or isinstance(kv[key], bool) or not 0 < kv[key] < 1:
            raise Stop(f"STOP: key_values.{key} must be a share in (0, 1)")
    try:
        deadline = date.fromisoformat(str(kv.get("freeze_wait_release_date")))
    except ValueError:
        raise Stop("STOP: key_values.freeze_wait_release_date must be an ISO date") from None
    if kv.get("seal_mode") != "procedural":
        raise Stop("STOP: key_values.seal_mode: only the procedural seal is built (the encryption alternative needs "
                   "cluster test C6 and its own code; G.5 draft §6)")
    cuda = kv.get("cuda_ipc") or {}
    if cuda.get("mode") == "c12":
        if not _rel_ok(cuda.get("c12_record")) or not str(cuda["c12_record"]).startswith("docs/r1/reports/"):
            raise Stop("STOP: cuda_ipc c12 needs its record under docs/r1/reports/")
        L._sha(cuda.get("c12_sha256"), "key_values.cuda_ipc.c12_sha256", allow_placeholder=False)
        if cuda.get("c12_review") is not None and (not _rel_ok(cuda["c12_review"]) or
                                                   not cuda["c12_review"].startswith("docs/r1/reviews/")):
            raise Stop("STOP: cuda_ipc.c12_review must be a review under docs/r1/reviews/ (or null)")
    elif cuda.get("mode") != "acceptance" and not (allow and _ph(cuda.get("mode"))):
        raise Stop("STOP: key_values.cuda_ipc.mode must be c12 or acceptance (P1)")
    cap = kv.get("cap_gpu_hours")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or cap <= 0:
        raise Stop("STOP: key_values.cap_gpu_hours must be positive")
    proj = projection(spec)
    low, high = proj["share=0.6 K=10"]["capped_gpu_hours"], proj["share=0.8 K=10"]["capped_gpu_hours"]
    if low > cap:
        raise Stop(f"STOP: the chosen options project {low} GPU-h at ran share 0.6 (K = 10) above the cap {cap}: "
                   f"they need the cap of their row, which the signature fixes (§2.6, §11 item 9)")
    p7 = (spec.get("projection") or {}).get("gpu_hours_p7")
    if not (allow and _ph(p7)) and not (isinstance(p7, (int, float)) and not isinstance(p7, bool) and 0 < p7 <= cap):
        raise Stop("STOP: projection.gpu_hours_p7 must be the P7 recompute, within the cap")
    if spec.get("gate") != GATE or _repo_file_sha(GATE["path"]) != GATE["sha256"]:
        raise Stop("STOP: gate must be r1/c3/gate.py v3.1 (sha256 a3f7d002…), as in the checkout")
    pr = spec.get("preregistration") or {}
    if pr.get("path") != "docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md" or \
            pr.get("sha256") != PREREG_SHA256 or _repo_file_sha(pr["path"]) != PREREG_SHA256:
        raise Stop("STOP: preregistration must be the frozen C3_SWEEP2_ANALYSIS_PREREG_20261121.md (sha256 aa1a961b…)")
    rows = {"decisions_row": spec.get("decisions_row"), "e4_amendment_row": spec.get("e4_amendment_row")}
    if o["G5-MEM"] != "A" and rows["e4_amendment_row"] is not None:
        raise Stop("STOP: e4_amendment_row is only for G5-MEM A (null otherwise)")
    for key, value in rows.items():
        if key == "e4_amendment_row" and o["G5-MEM"] != "A":
            continue
        if not (allow and _ph(value)) and not (isinstance(value, str) and ROW_ID.fullmatch(value)):
            raise Stop(f"STOP: {key} must be a PLAN row id")
    if launch:
        if unsigned:
            raise Stop(f"STOP: decisions not signed: {unsigned} (§11; the author's row signs them)")
        if blockers:
            raise Stop("STOP: the chosen options cannot launch: " + "; ".join(blockers))
        if cuda.get("mode") not in ("c12", "acceptance"):
            raise Stop("STOP: key_values.cuda_ipc.mode must be c12 or acceptance before launch (P1)")
    return {"spec": spec, "run_id": run_id, "options": o, "unsigned": unsigned, "launch_blockers": blockers,
            "projection": proj, "cap_gpu_hours": cap, "share_0_8_with_margin": round(high * 1.1, 1),
            "audited_band": kv["audited_band"], "freeze_wait_release_date": deadline.isoformat(), "split": split,
            "e4_amendment_needed": o["G5-MEM"] == "A",
            "divergence_denominator_weaker": o["G5-AUDIT"] == "B"}


# =============================================================================================== the note (§5)
def _range(block: list[int]) -> str:
    return f"{block[0]}-{block[1]}"


def note_lines(spec: dict, *, k: int = 10, k_row: str | None = None, freeze: str | None = None,
               freeze_row: str | None = None) -> dict:
    """Every key line of the signed note (§5, plus the §11 values), rendered from the spec. ``check_note`` requires
    each verbatim; ``audit_K`` and the two seed lines follow the note's K (P4), and ``freeze_wait`` the note's date
    (the spec's, or a later one moved by a docs-only amendment citing an author row)."""
    o = options(spec)
    w, p = spec["worker"], spec["proposer"]
    fam = spec["harness_families"]
    nodes = spec["nodes"]
    a_mode = o["G5-ARPEND"] == "A"
    record = "docs/r1/reports/*/G5_AR_PREREQUISITES_YYYYMMDD.md"
    pe = spec["ar_prerequisites"]["proposed_environment"]
    ar_env = (f"autoresearch: from the completion record {record} (G5-ARPEND A; proposed {pe['name']} "
              f"sweep2/g1b/{pe['freeze']} {pe['sha256']}, Python {pe['python']})" if a_mode else
              f"{pe['name']} sweep2/g1b/{pe['freeze']} {pe['sha256']} (Python {pe['python']}; autoresearch only)")
    names = []
    for n in nodes:
        suffix = " (CPU-only)" if n["device"] == "cpu" else " (G5-AR A, R1-G5-DECISIONS)" if n["node"] == AR else ""
        names.append(n["node"] + suffix)
    seeds = spec["audit"]["seed_blocks"][str(k)]
    if k == 10:
        k_line = ("10 (R1-G5-DECISIONS; K = 6 only after a published K-check author row, by a docs-only amendment of "
                  "this line and the two seed lines citing that row)")
    else:
        k_line = f"6 (K-check row {k_row}; R1-G5-DECISIONS; docs-only amendment of the signed note)"
    modes = spec["memory"]["modes"]
    nf = spec["noise_floor"]
    seven = (f"seven nodes: {nf['seven']['copy']} sha256 {nf['seven']['sha256']} with its cross-check gate record "
             f"{nf['seven'].get('gate_copy')} sha256 {nf['seven'].get('gate_sha256')} (REL-T1-G1B copy of "
             f"{nf['seven']['run_id']}, joined under G1B-JOIN behind the cross-check gate)")
    ar_nf = (f"autoresearch: from the completion record {record} (G5-ARPEND A)" if a_mode else
             f"autoresearch: {nf['ar']['copy']} sha256 {nf['ar']['sha256']} (REL-T1-G1B copy of {nf['ar']['run_id']})")
    kv = spec["key_values"]
    band = kv["audited_band"]
    div = spec["divergence"]
    div_line = {"fixed": f"G5-DIV A: {div.get('threshold')} of the audited label proposals, E5 on the label seeds, "
                         f"from {div['min_audited']} audited, at the end of each wave's audits; the literal "
                         f"2 x census ({div.get('literal_2x_census')}) kept, it never binds below "
                         f"{div.get('threshold')}",
                "pilot_cp": f"G5-DIV B: min({div.get('cap')}, max(2 x the upper limit of the two-sided "
                            f"{round(100 * div.get('cp_level', 0))} % Clopper-Pearson interval (upper tail "
                            f"{round(50 * (1 - div.get('cp_level', 0)), 2)} %) of the pilot's divergent share, "
                            f"{div.get('floor')})) for the pilot nodes, "
                            f"{div.get('other_nodes')} for the others, on the audited label proposals from "
                            f"{div['min_audited']}",
                "g1b_2x": f"G5-DIV C: min({div.get('cap')}, 2 x the node's G.1b divergent-row rate), on the audited "
                          f"label proposals from {div['min_audited']}"}[div["rule"]]
    cuda = kv["cuda_ipc"]
    lines = {
        "label": EVIDENCE,
        "run_id": spec["run_id"],
        "hosts": f"worker TASL-2 (RTX 4090 {w['gpu_uuid']}, driver {w['driver']}), proposer TASL-7 (RTX 4090 "
                 f"{p['gpu_uuid']}, driver {p['driver']}) over Tailscale {p['server_url']}",
        "host_authority": "R1-T1-HOST-TASL; environment row R1-T1-TASL-ENV; for autoresearch, R1-G1B-AR-ENV's "
                          "ar-cond7a (amended by R1-G1B-AR-PY) extended to its G.5 jobs by this note (P9)",
        "environments": f"torch312 {spec['envs']['torch312']['sha256']}, jax312 {spec['envs']['jax312']['sha256']} "
                        f"(census freezes, Python 3.12.16); {ar_env}",
        "llama_server_sha256": f"{p['binary_sha256']}; build {p['expected_build']}; build-directory manifest "
                               f"{p['bin_dir_manifest_sha256']} (as in the signed G.4 note)",
        "gguf_sha256": spec["model"]["sha256"],
        "harness_commit": f"G5-7 {fam['G5-7']['g5_commit']} (seven nodes); G5-AR {fam['G5-AR']['g5_commit']} "
                          f"(autoresearch); g5_pin_check.py PASS on the pair (G5-PIN B, R1-G5-DECISIONS); per family, "
                          f"the measurement path byte-identical to its G.1b pin (P5)",
        "g1b_harness_commit": f"{fam['G5-7']['g1b_pin']} (seven nodes); {fam['G5-AR']['g1b_pin']} (autoresearch)",
        "gpu_model": f"{GPU_MODEL} (campaigns and audits on TASL-2; server on TASL-7)",
        "nodes": ",".join(names),
        "data_manifests": ", ".join(f"{n['node']} {n['data_manifest_sha256'] or 'none'}" for n in nodes)
                          + "; each equal to the node's G.1b spec (R1-T1-TASL-ENV; R1-T1-DATA-MANIFEST for "
                            "mlgym_fmnist and mlgym_cifar10)",
        "instances_per_node": (f"{spec['memory']['instances_per_mode']} per memory mode ({', '.join(modes)})"
                               if len(modes) > 1 else f"{spec['memory']['instances_per_mode']} (memory mode {modes[0]})"),
        "instance_seeds": f"{_range(spec['instances']['seeds'])} ({spec['instances']['rule']})",
        "instance_split": f"{spec['instances']['split_file']['path']} sha256 {spec['instances']['split_file']['sha256']} "
                          f"(R1-SWEEP2-PREREG, PRE-SPLIT A; rule of §2.7)",
        "memory_mode": f"{' and '.join(modes)} (G5-MEM {o['G5-MEM']})",
        "campaign_W": ("20 manager calls (G5-W A)" if o["G5-W"] == "A" else
                       f"20 worker runs with an LLM-call cap of {spec['campaign']['llm_call_cap']} (G5-W B)"),
        "proposer": "gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false)",
        "temperature": f"{spec['campaign']['temperature']} (G5-TEMP {o['G5-TEMP']}); per-call seed {SEED_RULE}",
        "completion_cap_tokens": str(spec["campaign"]["max_tokens"]),
        "proposal_schema": spec["campaign"]["proposal_schema"],
        "timeout_basis": "census_slowest_x3 (R1-G1B-TIMEOUT)",
        "audit_K": k_line,
        "audit_seeds_label": _range(seeds["label"]),
        "audit_seeds_evaluation": _range(seeds["evaluation"]),
        "audit_scope": (f"G5-AUDIT {o['G5-AUDIT']}: {spec['audit']['scope']}; reuse_parent_runs "
                        f"{str(spec['audit']['reuse_parent_runs']).lower()}; E5 on the label seeds only; duplicate key "
                        f"({spec['audit']['duplicate_key']}); cross-instance groups audited once; gate repeats per "
                        f"PRE-DUP A"),
        "divergence_stop": div_line,
        "liveness_floor": str(kv["liveness_floor"]),
        "invalid_share_stop": str(kv["invalid_share_stop"]),
        "infrastructure_stop": str(kv["infrastructure_stop_share"]),
        "audited_band": f"{band[0]}-{band[1]} per node (G5-W {o['G5-W']}, G5-MEM {o['G5-MEM']})",
        "noise_floor": f"{seven}; {ar_nf}; joined by node (g1b_tasl_join.py floor-by-node; the split file's eight "
                       f"T1 nodes)",
        "tails": ", ".join(f"{n['node']} " + ("from the completion record (G5-ARPEND A)"
                                              if n["node"] == AR and a_mode else str(n["tails"])) for n in nodes),
        "job_layout": "per node on TASL-2 in sequence (G5-SLOT A), wave 1 (instances 1-4) campaigns then audits, "
                      "wave 2 (instances 5-12) campaigns then audits; audits in chunks with declared deadlines",
        "launch": "the TASL launch binding (LB A of R1-G1B-TASL-DECISIONS, as G4-LB A): a published checkout at or "
                  "after the commit that publishes this note and the spec, code equal to paper_commit outside docs/ "
                  "and the spec",
        "gpu_hours": f"{spec['projection']['gpu_hours_p7']} (P7, post-pilot recompute)",
        "cap_gpu_hours": f"{kv['cap_gpu_hours']}, counted per " + (
            "the worker card (G5-TASL-GPUH A)" if o["G5-TASL-GPUH"] == "A" else
            "both cards (G5-TASL-GPUH B, server stopped during audits)"),
        "proposer_card_hours": "metered and reported",
        "cuda_ipc": (f"C12 PASS: {cuda.get('c12_record')} sha256 {cuda.get('c12_sha256')}" if cuda.get("mode") == "c12"
                     else "the acceptance line cuda_ipc_acceptance, signed"),
        "freeze_wait": f"the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of this "
                       f"table until {freeze or kv['freeze_wait_release_date']}"
                       + (f" (moved by author row {freeze_row})" if freeze_row else "")
                       + "; no G.5 job starts on or after this date (STOP 14)",
        "ar_prerequisites": (f"PENDING until the completion record {record} (G5-ARPEND A; STOP 15)" if a_mode else
                             "PASS, cited in noise_floor, environments, tails and P1 (G5-ARPEND B)"),
        "gate": f"{GATE['path']} @ {GATE['commit']} sha256 {GATE['sha256']} (v3.1, R1-BX-D8-CONFIRM-V31)",
        "preregistration": f"{spec['preregistration']['path']} sha256 {spec['preregistration']['sha256']} (frozen)",
        "release_rows": "R1-T1-LABELS-UNSEAL (train and validation), R1-T1-LABELS-TEST-RELEASE (test labels and every "
                        "evaluation block) (§6; PRE-STAGE A, REL-SCOPE A, REL-T1-G1B)",
        "seal": "procedural (receipts and access log)",
        "decisions": ", ".join(f"{d} {o[d]}" for d in DECISIONS) + f" (row {spec['decisions_row']})",
    }
    if o["G5-MEM"] == "A":
        lines["e4_amendment_row"] = str(spec["e4_amendment_row"])
    if cuda.get("mode") != "c12":
        lines["cuda_ipc_acceptance"] = CUDA_IPC_ACCEPTANCE
    return lines


P_CITES = {"P1": ("R1-T1-HOST-TASL",), "P3": (), "P4": ("R1-G5-DECISIONS",), "P5": ("docs/r1/reviews/",),
           "P6": (), "P7": (), "P8": ("docs/r1/reviews/",), "P9": ("R1-T1-TASL-ENV",), "P2": (), "P10": (),
           "P11": ()}


def note_k(fields: dict) -> tuple[int, str | None]:
    """``audit_K`` read from the note (P4): 10, or 6 with the K-check row it names."""
    m = re.fullmatch(r"(10|6) \((.*)\)", fields.get("audit_K", ""))
    if not m:
        raise Stop("STOP: the note's audit_K line must read '10 (...)' or '6 (K-check row R1-...; ...)'")
    if m.group(1) == "10":
        return 10, None
    row = re.match(r"K-check row (R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])(?![A-Za-z0-9-])", m.group(2))
    if not row:
        raise Stop("STOP: audit_K 6 must name the K-check PASS row (P4)")
    return 6, row.group(1)


FREEZE_LINE = re.compile(r"^the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of "
                         r"this table until (?P<date>\d{4}-\d{2}-\d{2})(?: \(moved by author row "
                         r"(?P<row>R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])\))?; no G\.5 job starts on or after this date "
                         r"\(STOP 14\)$")


def note_freeze(fields: dict, spec: dict) -> tuple[str, str | None]:
    """The freeze-wait release date read from the note (m3): the spec's date, or another date moved by a docs-only
    amendment of the note that names the author row (which ``check_note`` requires on main, naming the date)."""
    m = FREEZE_LINE.fullmatch(fields.get("freeze_wait", ""))
    if not m:
        raise Stop("STOP: the note's freeze_wait line is not in the required form (STOP 14)")
    d, row = m.group("date"), m.group("row")
    try:
        date.fromisoformat(d)
    except ValueError:
        raise Stop("STOP: the note's freeze_wait date is not a date") from None
    if (d != spec["key_values"]["freeze_wait_release_date"]) != bool(row):
        raise Stop("STOP: a freeze_wait date other than the spec's needs the author row that moves it (and only "
                   "then names one)")
    return d, row


def plan_row(row: str, read_main, *, terms: tuple[str, ...] = ()) -> str:
    """The row's line on published main's PLAN (exactly once), naming every term (a term may not run on into a
    letter or digit: "G5-W A" does not match "G5-W AB")."""
    if not isinstance(row, str) or not ROW_ID.fullmatch(row):
        raise Stop(f"STOP: {row!r} is not a PLAN row id")
    plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
    lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(row)} \|", ln)]
    if len(lines) != 1:
        raise Stop(f"STOP: the PLAN row {row} must exist exactly once on published main")
    text = lines[0].split("|", 2)[2]                 # the row's text, without its id cell
    missing = [t for t in terms if not re.search(re.escape(t) + r"(?![A-Za-z0-9])", text)]
    if missing:
        raise Stop(f"STOP: the PLAN row {row} does not name {missing}")
    return lines[0]


def check_note(note_path: Path, spec_path: Path, *, spec: dict, on_main=G._note_on_main, read_main=G._read_main,
               draft: bool = False) -> dict:
    """The signed G.5 note ``docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`` (named by the spec's run_id): on
    published main byte-identically, ``approved: true`` (``draft=True``: exactly one ``approved: false`` line, need
    not be on main), no ``<…>`` placeholder, ``paper_commit`` and ``spec_sha256`` binding the spec, P1-P11 PASS with
    their citations, and every key line of ``note_lines`` verbatim, with K read from the note (P4). Returns the
    fields with ``_K`` and ``_K_row``."""
    note_path = Path(note_path)
    m = NOTE_NAME.fullmatch(note_path.name)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not m:
        raise Stop(f"STOP: the note must be {NOTE_DIR}/c3_t1_labels_<YYYYMMDD>.md")
    if note_path.name != f"{spec['run_id']}.md":
        raise Stop(f"STOP: the note's name must be the spec's run_id ({spec['run_id']}.md)")
    raw = note_path.read_bytes()
    approved = [ln for ln in raw.decode().splitlines() if re.match(r"^approved\s*:", ln)]
    if draft:
        if approved != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned note (exactly one line 'approved: false')")
    elif approved != ["approved: true"] or not on_main(f"{NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note must read approved: true and be committed byte-identically on origin/main")
    fields = G._note_fields(raw)
    k, k_row = note_k(fields)
    freeze, freeze_row = note_freeze(fields, spec)
    want = note_lines(spec, k=k, k_row=k_row, freeze=freeze, freeze_row=freeze_row)
    unfilled = sorted(key for key, v in fields.items()
                      if (PLACEHOLDER.search(v) or L._placeholder(v)) and v != want.get(key))
    if unfilled:
        raise Stop(f"STOP: note fields not filled (placeholder): {unfilled}")
    for key, value in (("paper_commit", spec["paper"]["commit"]), ("spec_sha256", L._sha_file(spec_path))):
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    cites = dict(P_CITES)
    cites["P1"] = cites["P1"] + (spec["harness_families"]["G5-7"]["isolation_host_check"]["record"],)
    cites["P2"] = (spec["noise_floor"]["seven"]["copy"],)
    cites["P3"] = (spec["pilot_basis"]["run_id"],)
    cites["P6"] = (str(spec["decisions_row"]),)
    for key, needles in cites.items():
        value = fields.get(key, "")
        if not value.upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: {key} must be PASS")
        missing = [n for n in needles if n not in value]
        if missing:
            raise Stop(f"STOP: {key} must cite {missing}")
    if k == 6:
        plan_row(k_row, read_main, terms=("K-check", "PASS"))
    if freeze_row:
        plan_row(freeze_row, read_main, terms=(freeze,))
    for key in ("P5", "P8"):          # the reviews these prerequisites cite are on main and accepted
        reviews = T4.REVIEW_PATH.findall(fields[key])
        if not reviews:
            raise Stop(f"STOP: {key} must cite a review file docs/r1/reviews/<name>.md")
        for review in reviews:
            text = (read_main(review) or b"").decode("utf-8", "replace")
            if not VERDICT_ACCEPTED.search(text):
                raise Stop(f"STOP: {key} cites {review}, which is not on published main with 'Verdict: ACCEPTED'")
    bad = sorted(key for key, value in want.items() if fields.get(key) != value)
    if bad:
        raise Stop(f"STOP: note key lines differ from the spec (§5): {bad}")
    return {**fields, "_K": k, "_K_row": k_row, "_freeze": freeze, "_freeze_row": freeze_row}


# =============================================================================================== REL-T1-G1B copies
def _review_names(review: str, needles: list[str], read_main, what: str) -> None:
    rv = read_main(review) if _rel_ok(review) and str(review).startswith("docs/r1/reviews/") else None
    text = rv.decode("utf-8", "replace") if rv is not None else ""
    missing = [n for n in needles if n not in text]
    if rv is None or missing or not VERDICT_ACCEPTED.search(text):
        raise Stop(f"STOP: the review {review} of {what} must be on published main, name {missing or needles} and "
                   f"read 'Verdict: ACCEPTED'")


def check_g1b_copy(entry: dict, *, schema: str, run_id: str, nodes: list[str], read_main,
                   gate_for: dict | None = None) -> dict:
    """A REL-T1-G1B copy of a sealed G.1b summary (R1-SWEEP2-RELEASE-DECISIONS): a committed file on published main
    with the declared sha256, of the summary schema and run, covering exactly the given nodes, and an independent
    review on main that names the copy's path and sha256 and the sealed summary's path (``sealed_path``; the copy is
    byte-identical to it) with ``Verdict: ACCEPTED``.

    ``gate_for`` (the seven-node copy, M3): the cross-check gate record ``crosscheck_gate.json`` is copied beside the
    summary copy (``gate_copy``, ``gate_sha256``), named with its sha256 in the same review, and binds the summary's
    assembly: schema ``g1b_tasl_crosscheck_gate/1``, the cross-check spec's TASL-7 nodes, G.1b spec sha256 and run id,
    and ``assembly_json_sha256`` equal to the summary's ``assembly_sha256`` (as ``g1b_tasl_join.noise_floor_by_node``
    requires). Returns each node's D21 verdict; the caller STOPs a node that does not qualify (STOP 5)."""
    rel, sha, review, sealed = entry.get("copy"), entry.get("sha256"), entry.get("review"), entry.get("sealed_path")
    if not _rel_ok(rel) or not _rel_ok(review) or not str(review).startswith("docs/r1/reviews/"):
        raise Stop("STOP: a REL-T1-G1B copy needs a repository path and a review under docs/r1/reviews/")
    if not isinstance(sealed, str) or not sealed.startswith("/"):
        raise Stop("STOP: a REL-T1-G1B copy names the absolute path of the sealed summary it was taken from")
    raw = read_main(rel)
    if raw is None or _sha_bytes(raw) != sha:
        raise Stop(f"STOP: the REL-T1-G1B copy {rel} is not on published main with sha256 {sha}")
    s = json.loads(raw)
    if s.get("schema") != schema or s.get("label") != G.ENGINEERING_ONLY or s.get("run_id") != run_id:
        raise Stop(f"STOP: {rel} is not the {schema} summary of run {run_id}")
    verdicts = s.get("verdicts") or {}
    if sorted(verdicts) != sorted(nodes):
        raise Stop(f"STOP: {rel} covers {sorted(verdicts)}, not {sorted(nodes)}")
    needles = [rel, sha, sealed]
    out = {"copy": rel, "sha256": sha, "review": review, "sealed_path": sealed, "raw": raw,
           "qualifies_D21": {n: (v or {}).get("qualifies_D21") is True for n, v in verdicts.items()}}
    if gate_for is not None:
        gate_rel, gate_sha = entry.get("gate_copy"), entry.get("gate_sha256")
        if not _rel_ok(gate_rel) or Path(gate_rel) != Path(rel).parent / "crosscheck_gate.json":
            raise Stop("STOP: the seven-node copy needs crosscheck_gate.json copied beside it (gate_copy)")
        gate_raw = read_main(gate_rel)
        if gate_raw is None or _sha_bytes(gate_raw) != gate_sha:
            raise Stop(f"STOP: the cross-check gate copy {gate_rel} is not on published main with sha256 {gate_sha}")
        gate = json.loads(gate_raw)
        xc = gate_for
        problems = [k for k, ok in (
            ("schema", gate.get("schema") == X.GATE_SCHEMA),
            ("nodes", sorted(gate.get("nodes") or {}) == sorted(xc["nodes"])),
            ("g1b_spec_sha256", gate.get("g1b_spec_sha256") == xc["g1b_spec"]["sha256"]),
            ("crosscheck_run_id", gate.get("crosscheck_run_id") == xc["run_id"]),
            ("assembly_json_sha256", isinstance(s.get("assembly_sha256"), str)
             and gate.get("assembly_json_sha256") == s["assembly_sha256"])) if not ok]
        if problems:
            raise Stop(f"STOP: the cross-check gate record {gate_rel} does not bind this summary's assembly and the "
                       f"TASL-7 nodes (R1-T1-TASL-ENV): {problems}")
        needles += [gate_rel, gate_sha]
        out.update(gate_copy=gate_rel, gate_sha256=gate_sha, gate_raw=gate_raw)
    _review_names(review, needles, read_main, f"the REL-T1-G1B copy {rel}")
    return out


def check_seven_copy(spec: dict, read_main) -> dict:
    """The seven-node REL-T1-G1B copy with its cross-check gate record (M3)."""
    xs = spec["noise_floor"]["seven"]["crosscheck_spec"]
    xc = json.loads((REPO_ROOT / xs["path"]).read_text())
    if L._sha_file(REPO_ROOT / xs["path"]) != xs["sha256"] or \
            xc["g1b_spec"]["sha256"] != spec["harness_families"]["G5-7"]["g1b_spec"]["sha256"]:
        raise Stop("STOP: the cross-check spec must be the bound one and bind the seven-node G.1b spec")
    return check_g1b_copy(spec["noise_floor"]["seven"], schema=G.SUMMARY_SCHEMA,
                          run_id=spec["noise_floor"]["seven"]["run_id"], nodes=list(SEVEN), read_main=read_main,
                          gate_for=xc)


def floor_by_node(seven: dict, ar: dict) -> dict:
    """``g1b_tasl_join.noise_floor_by_node`` on the two copies (draft §5 ``noise_floor``: "g1b_tasl_join.py
    floor-by-node"), run on byte-identical temporary files: the seven-node summary beside its gate record, and
    autoresearch's summary; the union must be the split file's eight T1 nodes."""
    with tempfile.TemporaryDirectory(prefix="g5_floor_") as tmp:
        d7, dar = Path(tmp) / "seven", Path(tmp) / "ar"
        d7.mkdir()
        dar.mkdir()
        (d7 / "summary.json").write_bytes(seven["raw"])
        (d7 / "crosscheck_gate.json").write_bytes(seven["gate_raw"])
        (dar / "summary.json").write_bytes(ar["raw"])
        out = J.noise_floor_by_node(d7 / "summary.json", dar / "summary.json",
                                    REPO_ROOT / "r1/c3/splits/c3_p3_split_v1.json")
    for node, v in out["nodes"].items():
        v["summary"] = seven["copy"] if v["schema"] == G.SUMMARY_SCHEMA else ar["copy"]
    return out


def check_c12(spec: dict, read_main) -> dict:
    """P1 under ``cuda_ipc: c12`` (M1): the C12 record on published main at its sha256. While the C12 record format is
    not fixed: either the record carries ``c12_host: <TASL-2's host name>`` and ``c12_verdict: PASS`` (both must then
    be right), or a review on main (``c12_review``) names the record and its sha256 and reads ``Verdict: ACCEPTED``."""
    c = spec["key_values"]["cuda_ipc"]
    rel, sha = c["c12_record"], c["c12_sha256"]
    raw = read_main(rel) if _rel_ok(rel) else None
    if raw is None:
        raise Stop(f"STOP: the C12 record {rel} is not on published main (P1)")
    if _sha_bytes(raw) != sha:
        raise Stop(f"STOP: the C12 record {rel} differs from its declared sha256 (P1)")
    fields = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        m = re.match(r"^(c12_[a-z_]+):\s*(.*?)\s*$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate {m.group(1)} in the C12 record")
            fields[m.group(1)] = m.group(2)
    out = {"record": rel, "sha256": sha}
    if "c12_host" in fields or "c12_verdict" in fields:
        if fields.get("c12_host") != spec["worker"]["hostname"] or fields.get("c12_verdict") != "PASS":
            raise Stop(f"STOP: the C12 record does not read a PASS on {spec['worker']['hostname']}: "
                       f"{ {k: fields.get(k) for k in ('c12_host', 'c12_verdict')} } (P1)")
        out["fields"] = fields
    elif c.get("c12_review") is None:
        raise Stop("STOP: the C12 record has no c12_host / c12_verdict lines and no c12_review names it (P1)")
    if c.get("c12_review") is not None:
        _review_names(c["c12_review"], [rel, sha], read_main, f"the C12 record {rel}")
        out["review"] = c["c12_review"]
    return out


# =============================================================================================== STOP 15
def list_main(prefix: str = "") -> list[str]:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "ls-tree", "-r", "--name-only", "origin/main",
                          *(["--", prefix] if prefix else [])], capture_output=True, text=True)
    if res.returncode:
        raise Stop("STOP: cannot list published main")
    return res.stdout.splitlines()


def _cited(fields: dict, key: str, read_main, *, on_main: bool = True) -> tuple[str, str]:
    m = CITED.fullmatch(fields.get(key, ""))
    if not m:
        raise Stop(f"STOP 15: the completion record's {key} must read '<path> sha256 <64 hex>'")
    path, sha = m.groups()
    if on_main:
        raw = read_main(path) if _rel_ok(path) else None
        if raw is None or _sha_bytes(raw) != sha:
            raise Stop(f"STOP 15: {key} {path} is not on published main with sha256 {sha}")
    return path, sha


ENV_LINE = re.compile(r"^(?P<name>[A-Za-z0-9_.-]+) freeze (?P<freeze>\S+) sha256 (?P<sha>[0-9a-f]{64}) python "
                      r"(?P<python>\d+\.\d+\.\d+) interpreter (?P<interp>/\S+)$")


def check_ar_record(spec: dict, spec_path: Path, *, read_main, list_main=list_main) -> dict:
    """G5-ARPEND A's completion record (§2.13, STOP 15; round-4 nit): exactly one file on published main matching
    ``docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md`` (none, or two or more, is a STOP), naming this spec's
    sha256 (every other path on main naming ``G5_AR_PREREQUISITES``, outside ``docs/r1/reviews/`` where its reviews
    live, is a STOP too: a near-miss name or a deeper directory is never silently ignored), with every cited file on
    main at its sha256, an independent review on main that names the record's path
    and sha256 with ``Verdict: ACCEPTED``, and an item for each of the spec's PENDING markers. Returns autoresearch's
    noise-floor copy, environment, tails and host check, which the switch then uses."""
    found = sorted(p for p in list_main() if RECORD_TOKEN in p and not p.startswith("docs/r1/reviews/"))
    odd = [p for p in found if not RECORD_NAME.fullmatch(p)]
    if odd:
        raise Stop(f"STOP 15: paths on published main that name {RECORD_TOKEN} but are not "
                   f"docs/r1/reports/<dir>/G5_AR_PREREQUISITES_<YYYYMMDD>.md: {odd[:5]}")
    if len(found) != 1:
        raise Stop(f"STOP 15: exactly one completion record G5_AR_PREREQUISITES_<YYYYMMDD>.md must be on published "
                   f"main; found {len(found)}: {found[:5]}")
    rel = found[0]
    raw = read_main(rel)
    if raw is None:
        raise Stop(f"STOP 15: cannot read {rel} from published main")
    rec_sha = _sha_bytes(raw)
    f = G._note_fields(raw)
    open_fields = sorted(k for k, v in f.items() if PLACEHOLDER.search(v) or L._placeholder(v))
    if open_fields:
        raise Stop(f"STOP 15: the completion record has unfilled fields: {open_fields}")
    for key, want in (("schema", "g5_ar_prerequisites/1"), ("node", AR), ("verdict", "PASS"),
                      ("g5_spec_sha256", L._sha_file(spec_path))):
        if f.get(key) != want:
            raise Stop(f"STOP 15: the completion record's {key} must be {want!r}")
    missing = [m for m in spec["ar_prerequisites"]["pending"] if m not in f]
    if missing:
        raise Stop(f"STOP 15: the completion record does not complete the spec's PENDING items {missing}")
    # the review of the record itself
    review = f.get("review", "")
    rv = read_main(review) if _rel_ok(review) and review.startswith("docs/r1/reviews/") else None
    text = rv.decode("utf-8", "replace") if rv is not None else ""
    if rv is None or rel not in text or rec_sha not in text or not VERDICT_ACCEPTED.search(text):
        raise Stop(f"STOP 15: the record's review must be on main, name {rel} and its sha256 {rec_sha}, and read "
                   f"'Verdict: ACCEPTED'")
    # P1: the TASL-2 host check at autoresearch's pin
    hc_path, hc_sha = _cited(f, "host_check", read_main)
    host = G.check_host_record({"hostname": spec["worker"]["hostname"],
                                "isolation_host_check": {"record": hc_path, "sha256": hc_sha}}, PC.PIN_AR, read_main)
    # P2: the third G.1b note
    note_path, _ = _cited(f, "g1b_note", read_main)
    if not AR_NOTE.fullmatch(note_path):
        raise Stop("STOP 15: g1b_note must be docs/r1/authorizations/g1b_ar_t1_tasl_<YYYYMMDD>.md")
    nf = G._note_fields(read_main(note_path))
    if nf.get("approved") != "true" or nf.get("run_id") != spec["noise_floor"]["ar"]["run_id"] or \
            nf.get("harness_commit") != PC.PIN_AR or \
            nf.get("spec_sha256") != spec["harness_families"]["G5-AR"]["g1b_spec"]["sha256"]:
        raise Stop("STOP 15: the third G.1b note must be signed, for run g1b-ar-tasl-20261122-a at harness 2d09f9a9, "
                   "binding the autoresearch G.1b spec this G.5 spec binds (harness_families.G5-AR.g1b_spec)")
    # the REL-T1-G1B copy of its sealed summary, with the D21 verdict
    copy_path, copy_sha = _cited(f, "noise_floor_copy", read_main)
    sealed_path, sealed_sha = _cited(f, "g1b_sealed_summary", read_main, on_main=False)
    if sealed_sha != copy_sha:
        raise Stop("STOP 15: the REL-T1-G1B copy is not byte-identical to the sealed summary it cites")
    floor = check_g1b_copy({"copy": copy_path, "sha256": copy_sha, "review": f.get("noise_floor_copy_review"),
                            "sealed_path": sealed_path},
                           schema=G.AR_SUMMARY_SCHEMA, run_id=spec["noise_floor"]["ar"]["run_id"], nodes=[AR],
                           read_main=read_main)
    d21 = "qualifies" if floor["qualifies_D21"][AR] else "does_not_qualify"
    if f.get("d21_verdict") != d21:
        raise Stop(f"STOP 15: d21_verdict must be the copy's verdict ({d21})")
    # P10
    if f.get("tails") not in ("gaussian", "student_t"):
        raise Stop("STOP 15: tails must be gaussian or student_t (P10)")
    decl_path, _ = _cited(f, "tails_declaration", read_main)
    other = {"gaussian": "student_t", "student_t": "gaussian"}[f["tails"]]
    lines = [ln for ln in read_main(decl_path).decode("utf-8", "replace").splitlines() if AR in ln]
    word = lambda w, ln: re.search(rf"(?<![A-Za-z0-9_-]){w}(?![A-Za-z0-9_-])", ln)  # noqa: E731
    if not lines or not all(word(f["tails"], ln) and not word(other, ln) for ln in lines):
        raise Stop(f"STOP 15: the tails declaration {decl_path} must name {AR} with {f['tails']} (P10)")
    # P9: the environment
    m = ENV_LINE.fullmatch(f.get("environment", ""))
    if not m:
        raise Stop("STOP 15: environment must read '<name> freeze <path> sha256 <hex> python <x.y.z> interpreter "
                   "<abs path>'")
    env = m.groupdict()
    freeze_raw = read_main(env["freeze"]) if _rel_ok(env["freeze"]) else None
    if freeze_raw is None or _sha_bytes(freeze_raw) != env["sha"]:
        raise Stop(f"STOP 15: the environment freeze {env['freeze']} is not on main with sha256 {env['sha']}")
    pe = spec["ar_prerequisites"]["proposed_environment"]
    proposed = (env["name"], env["freeze"], env["sha"], env["python"]) == \
        (pe["name"], f"sweep2/g1b/{pe['freeze']}", pe["sha256"], pe["python"])
    if proposed:
        if env["interp"] != spec["worker"]["env_python"].get(pe["name"]):
            raise Stop("STOP 15: the proposed environment must use the spec's interpreter for it")
        env_row = None
    else:                          # §2.13: a different environment needs the row that names its use for G.5 too
        env_row = f.get("environment_row", "")
        if not ROW_ID.fullmatch(env_row):
            raise Stop("STOP 15: an environment other than the proposed ar-cond7a needs environment_row")
        plan_row(env_row, read_main, terms=(env["name"], "G.5"))
    return {"record": rel, "sha256": rec_sha, "review": review, "host_check": host, "noise_floor": floor,
            "qualifies_D21": floor["qualifies_D21"][AR], "tails": f["tails"],
            "environment": {"name": env["name"], "freeze": env["freeze"], "sha256": env["sha"],
                            "python": env["python"], "interpreter": env["interp"], "row": env_row}}


# =============================================================================================== STOP 14
def freeze_wait_check(spec: dict, *, today: date, released: list[str] = (), stopped: list[str] = (),
                      before_arms_frozen: bool = False, deadline: str | None = None) -> dict:
    """STOP 14 (§2.11). At a job start: a G.5 job on or after the release deadline cannot lead to that node's release
    by the deadline, so it STOPs for the author. Before the arms-frozen record (``before_arms_frozen``): every
    un-STOPped node released by the deadline and no node STOPped at G.5; otherwise STOP. Only an author row may freeze
    the arms without a node."""
    deadline = date.fromisoformat(deadline or spec["key_values"]["freeze_wait_release_date"])
    if before_arms_frozen:
        unknown = sorted((set(released) | set(stopped)) - set(T1_NODES))
        if unknown:
            raise Stop(f"STOP 14: unknown nodes {unknown}")
        if stopped:
            raise Stop(f"STOP 14: nodes STOPped at G.5 {sorted(stopped)}: the author decides before the arms-frozen "
                       f"record (only an author row may freeze the arms without them)")
        late = sorted(set(T1_NODES) - set(released) - set(stopped))
        if late and today < deadline:      # not yet: wait (a refusal, but not a STOP for the author)
            raise Stop(f"WAIT (not yet): the train/dev release of {late} is not done; the arms-frozen record waits "
                       f"until {deadline} ({(deadline - today).days} days left)")
        if late:
            raise Stop(f"STOP 14: the release deadline {deadline} has passed ({today}) and the train/dev release of "
                       f"{late} is not done: the coordinating agent STOPs for the author")
        return {"deadline": deadline.isoformat(), "released": sorted(released)}
    if today >= deadline:
        raise Stop(f"STOP 14: the freeze-wait release deadline {deadline} is reached ({today}): no further G.5 job; "
                   f"the coordinating agent STOPs for the author")
    return {"deadline": deadline.isoformat(), "days_left": (deadline - today).days}


# =============================================================================================== P5, STOP 13
ENGINE_FILES = ("manager_v2_diff.py", "campaign_v2_diff.py", "proposal_v2_diff.py", "pilot_g4.py")
TRACKG = "src/autoresearch/trackg/"
PATH_DIRS = (TRACKG, "nodes/", "third_party/", "configs/trackg/")
NOISE_FLOOR = TRACKG + "noise_floor.py"


def _ls(repo: Path, commit: str) -> set[str]:
    out = PC._git(repo, "ls-tree", "-r", "-z", "--name-only", commit).stdout
    return {p for p in out.split("\0") if p}


def _module_file(mod: str, files: set[str]) -> str | None:
    base = "src/" + mod.replace(".", "/")
    for cand in (base + ".py", base + "/__init__.py"):
        if cand in files:
            return cand
    return None


def import_closure(repo: Path, commit: str, root: str = NOISE_FLOOR) -> set[str]:
    """The files of ``autoresearch.*`` modules that ``root`` imports, transitively (absolute and relative imports,
    at any depth in the module, with the packages' ``__init__.py``). Dynamic loads (importlib, a file loaded by path)
    are not followed; the directories of the measurement path cover them."""
    files = _ls(repo, commit)
    if root not in files:
        raise Stop(f"STOP: {root} is not at {commit[:8]}")
    seen, todo = set(), [root]
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        parts = path[len("src/"):-len(".py")].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        pkg_parts = parts if path.endswith("__init__.py") else parts[:-1]
        for i in range(1, len(pkg_parts) + 1):            # the packages a module import executes
            init = "src/" + "/".join(pkg_parts[:i]) + "/__init__.py"
            if init in files:
                todo.append(init)
        tree = ast.parse(PC._git(repo, "show", f"{commit}:{path}").stdout, filename=path)
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = pkg_parts[:len(pkg_parts) - (node.level - 1)]
                    mod = ".".join(base + ([node.module] if node.module else []))
                else:
                    mod = node.module or ""
                mods = [mod] + [f"{mod}.{a.name}" for a in node.names]
            for mod in mods:
                if mod.split(".")[0] != "autoresearch":
                    continue
                hit = _module_file(mod, files)
                if hit:
                    todo.append(hit)
    return seen


def measurement_paths(repo: Path, commit: str) -> tuple[list[str], set[str]]:
    """P5's measurement path at the G.1b pin: all of ``src/autoresearch/trackg/`` except the v2-diff engine files,
    plus ``nodes/``, ``third_party/``, ``configs/trackg/`` (``node_lib/`` is inside trackg), and every module of
    ``noise_floor``'s import closure outside trackg; only files present at the pin."""
    files = _ls(repo, commit)
    closure = import_closure(repo, commit)
    engine = {TRACKG + f for f in ENGINE_FILES}
    paths = {p for p in files if p.startswith(PATH_DIRS) and p not in engine} | closure
    return sorted(paths), closure


def measurement_path_check(repo: Path, g1b_pin: str, g5_commit: str) -> dict:
    """P5 per family (G5-7 against c025f89a, G5-AR against 2d09f9a9): the G.5 commit descends from its G.1b pin, no
    measurement-path file present at the pin differs (content, mode or type, or deleted), and ``noise_floor``'s import
    closure is the same at both commits (so no measurement-path module imports a file G.5 added)."""
    repo = Path(repo)
    pin, g5 = PC._commit(repo, g1b_pin), PC._commit(repo, g5_commit)
    if not PC._descends(repo, pin, g5):
        raise Stop(f"STOP: the G.5 commit {g5[:8]} does not descend from its G.1b pin {pin[:8]} (P5)")
    paths, closure = measurement_paths(repo, pin)
    all_changed = set(PC._changed(repo, pin, g5))
    changed = sorted(all_changed & set(paths))
    if changed:
        raise Stop(f"STOP: the measurement path differs between the G.1b pin {pin[:8]} and G.5 {g5[:8]}: {changed[:10]}")
    added = sorted(all_changed - _ls(repo, pin))
    bad_added = [a for a in added if a.startswith(NO_ADDITIONS) or (a.startswith(TRACKG) and a not in G5_TRACKG_ADDITIONS)]
    if bad_added:                                            # m4: a new file could shadow a module or config there
        raise Stop(f"STOP: G.5 adds files inside the measurement directories (only {list(G5_TRACKG_ADDITIONS)} may be "
                   f"added in trackg/): {bad_added[:10]}")
    closure_g5 = import_closure(repo, g5)
    if closure_g5 != closure:
        raise Stop(f"STOP: noise_floor's import closure changed at G.5 (a G.5 file entered the measurement path): "
                   f"{sorted(closure_g5 ^ closure)[:10]}")
    engine_in_closure = sorted(p for p in closure if p.rsplit("/", 1)[-1] in ENGINE_FILES and p.startswith(TRACKG))
    return {"g1b_pin": pin, "g5_commit": g5, "paths": len(paths), "closure": sorted(closure),
            "closure_outside_trackg": sorted(p for p in closure if not p.startswith(TRACKG)),
            "engine_files_in_closure": engine_in_closure,
            "g5_added": added}


def family_checkout(spec: dict, fam: str, git=G._sh) -> dict:
    """The node's family checkout at its G.5 commit and clean (only nodes/<node>/data links), as G.1b's
    ``harness_checkout``: a node at the other family's checkout STOPs (STOP 13)."""
    f = spec["harness_families"][fam]
    shim = {"hosts": {WORKER_HOST: {"harness_dir": f["harness_dir"]}}, "harness": {"commit": f["g5_commit"]}}
    try:
        return G.harness_checkout(shim, WORKER_HOST, git)
    except Stop as exc:
        raise Stop(f"STOP 13: {fam}: {exc}") from None


# =============================================================================================== the switch
IMPORT_SOURCES = {**T4.IMPORT_SOURCES, "g4_tasl": "sweep2/t1_tasl/g4_tasl.py",
                  "g5_pin_check": "sweep2/t1_tasl/g5_pin_check.py", "g5_tasl": "sweep2/t1_tasl/g5_tasl.py",
                  "g1b_crosscheck": "sweep2/t1_tasl/g1b_crosscheck.py", "g1b_tasl_join": "sweep2/t1_tasl/g1b_tasl_join.py",
                  "g5_job": "sweep2/t1_tasl/g5_job.py"}


def check_import_sources(repo: Path = None) -> dict:
    """As ``g4_tasl.check_import_sources``, over the modules this script imports."""
    repo = Path(repo or REPO_ROOT).resolve()
    out = {}
    for name, rel in IMPORT_SOURCES.items():
        mod = sys.modules.get(name)
        if mod is None:
            continue
        got = Path(getattr(mod, "__file__", "") or "").resolve()
        if got != repo / rel:
            raise Stop(f"STOP: module {name} was imported from {got}, not the reviewed {rel}")
        out[name] = rel
    return out


def job_runner(spec_path, node_name, job, context) -> dict:
    """The real job entry (part 3b-1): ``g5_job.run_job``, reached only through ``launch`` after every check."""
    import g5_job                                            # noqa: PLC0415 - g5_job imports this module
    check_import_sources()                                   # again, now that g5_job is imported (3b-1 review m4)
    return g5_job.run_job(spec_path, node_name, job, context)


def launch(spec_path: Path, note_path: Path, node_name: str, *, job: str, enable: bool, today: date,
           on_main=G._note_on_main, read_main=G._read_main, list_main=list_main, pin_check=None, mpath_check=None,
           checkout=None, launch_binding=None, runner=None, server_record: Path | None = None) -> dict:
    """The G.5 switch at every job start (§9). Off unless both keys are given; every check below must pass before the
    runner is called (the default runner is ``g5_job.run_job``, part 3b-1). ``server_record``: the proposer's
    ``server_record.json`` copied from TASL-7, for campaign jobs."""
    if job not in JOBS:
        raise Stop(f"STOP: job must be one of {JOBS}")
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    node = node_entry(spec, node_name)
    fields = check_note(note_path, spec_path, spec=spec, on_main=on_main, read_main=read_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: real G.5 runs are disabled (needs --enable AND {ENABLE_ENV}=1)")
    o = options(spec)
    context: dict = {"job": job, "K": fields["_K"], "K_row": fields["_K_row"], "options": o}
    if job.startswith("audits"):
        context["audit_seeds"] = audit_seeds(spec, fields["_K"])
    rows = list(PLAN_ROWS)
    plan_row(spec["decisions_row"], read_main, terms=tuple(f"{d} {o[d]}" for d in DECISIONS))
    rows.append(spec["decisions_row"])
    if o["G5-MEM"] == "A":                  # it amends E4's "both memory modes" (R1-BX-PROPOSED-CONFIRM E4)
        plan_row(spec["e4_amendment_row"], read_main, terms=("E4", "G5-MEM"))
        rows.append(spec["e4_amendment_row"])
    if fields["_K_row"]:
        rows.append(fields["_K_row"])
    fam = node["family"]
    seven_check = spec["harness_families"]["G5-7"]["isolation_host_check"]
    context["host_check"] = {"G5-7": G.check_host_record({"hostname": spec["worker"]["hostname"],
                                                          "isolation_host_check": seven_check}, PC.PIN_SEVEN,
                                                         read_main)}
    if spec["key_values"]["cuda_ipc"]["mode"] == "c12":                                              # P1 (M1)
        context["cuda_ipc"] = check_c12(spec, read_main)
    seven = check_seven_copy(spec, read_main)                                                       # M3
    context["noise_floor"] = {"seven": seven}
    ar_copy = None
    if fam == "G5-AR":
        if o["G5-ARPEND"] == "A":
            rec = check_ar_record(spec, spec_path, read_main=read_main, list_main=list_main)        # STOP 15
            context.update(ar_record=rec, ar_environment=rec["environment"], ar_tails=rec["tails"])
            context["host_check"]["G5-AR"] = rec["host_check"]
            qualifies = rec["qualifies_D21"]
            ar_copy = rec["noise_floor"]
            if rec["environment"]["row"]:
                rows.append(rec["environment"]["row"])
        else:
            context["host_check"]["G5-AR"] = G.check_host_record(
                {"hostname": spec["worker"]["hostname"],
                 "isolation_host_check": spec["harness_families"]["G5-AR"]["isolation_host_check"]}, PC.PIN_AR,
                read_main)
            ar = check_g1b_copy(spec["noise_floor"]["ar"], schema=G.AR_SUMMARY_SCHEMA,
                                run_id=spec["noise_floor"]["ar"]["run_id"], nodes=[AR], read_main=read_main)
            context["noise_floor"]["ar"] = ar
            qualifies = ar["qualifies_D21"][AR]
            ar_copy = ar
        context["floor_by_node"] = floor_by_node(seven, ar_copy)          # the eight nodes joined by node
    else:
        qualifies = seven["qualifies_D21"][node_name]
    if not qualifies:
        raise NodeStop(f"STOP 5: {node_name} does not qualify under D21 at G.1b: not run in G.5; the author decides "
                       f"on T2 (R1-BX-D12)")
    context["freeze_wait"] = freeze_wait_check(spec, today=today, deadline=fields["_freeze"])        # STOP 14
    fams = spec["harness_families"]
    repo = Path(fams[fam]["harness_dir"])
    try:
        context["pin_check"] = (pin_check or PC.check)(repo, fams["G5-7"]["g5_commit"], fams["G5-AR"]["g5_commit"])
    except PC.Stop as exc:                                                                          # STOP 13
        raise Stop(f"STOP 13: {exc}") from None
    context["checkout"] = (checkout or family_checkout)(spec, fam)
    context["measurement_path"] = (mpath_check or measurement_path_check)(repo, fams[fam]["g1b_pin"],
                                                                         fams[fam]["g5_commit"])     # P5
    if context["measurement_path"].get("g5_commit") != fams[fam]["g5_commit"]:
        raise Stop("STOP: the measurement-path check ran on another commit")

    def bind(repo_root, s, r):
        imports = check_import_sources(repo_root)        # first: no shadowed module's code runs as the binding
        return {**G.verify_launch_tasl(repo_root, s, r, spec_path=spec_path), "imports": imports}
    context["launch"] = (launch_binding or bind)(REPO_ROOT, spec, tuple(rows))
    if server_record is not None:
        context["server_record"] = str(server_record)
    return (runner or job_runner)(spec_path, node_name, job, context) | {"context": context}


# =============================================================================================== CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    op = sub.add_parser("options"); op.add_argument("spec"); op.add_argument("--set", action="append", default=[],
                                                                               help="DECISION=OPTION")
    kl = sub.add_parser("key-lines"); kl.add_argument("spec"); kl.add_argument("--k", type=int, default=10)
    kl.add_argument("--k-row")
    cn = sub.add_parser("check-note"); cn.add_argument("spec"); cn.add_argument("--note", required=True)
    cn.add_argument("--draft", action="store_true")
    ar = sub.add_parser("check-ar-record"); ar.add_argument("spec")
    mp = sub.add_parser("measurement-path"); mp.add_argument("repo"); mp.add_argument("g1b_pin")
    mp.add_argument("g5_commit")
    fw = sub.add_parser("freeze-wait"); fw.add_argument("spec"); fw.add_argument("--today", required=True)
    fw.add_argument("--released", nargs="*", default=[]); fw.add_argument("--stopped", nargs="*", default=[])
    fw.add_argument("--before-arms-frozen", action="store_true")
    dt = sub.add_parser("dates"); dt.add_argument("spec"); dt.add_argument("sealed", nargs="*")
    dt.add_argument("--today", required=True)
    r = sub.add_parser("run"); r.add_argument("spec"); r.add_argument("--note", required=True)
    r.add_argument("--node", required=True); r.add_argument("--job", required=True, choices=JOBS)
    r.add_argument("--enable", action="store_true"); r.add_argument("--server-record")
    sv = sub.add_parser("serve"); sv.add_argument("spec"); sv.add_argument("--note", required=True)
    sv.add_argument("--enable", action="store_true")
    for name in ("cpus", "logdir"):
        q = sub.add_parser(name); q.add_argument("spec"); q.add_argument("--node", required=True)
    ca = sub.add_parser("close-attempt"); ca.add_argument("spec"); ca.add_argument("attempt_dir")
    ca.add_argument("--node", required=True); ca.add_argument("--job", required=True, choices=JOBS)
    ca.add_argument("--chunk", type=int); ca.add_argument("--reason", required=True)
    wc = sub.add_parser("wave-checks"); wc.add_argument("spec"); wc.add_argument("--node", required=True)
    wc.add_argument("--wave", type=int, required=True, choices=(1, 2))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            out = validate_spec(load_spec(Path(a.spec)), launch=a.launch)
            out.pop("spec")
            print(json.dumps({"ok": True, **out}, indent=1))
        elif a.cmd == "options":
            choices = dict(s.split("=", 1) for s in a.set)
            print(json.dumps(apply_options(load_spec(Path(a.spec)), choices), indent=1, ensure_ascii=False))
        elif a.cmd == "key-lines":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            lines = {"approved": "true", **note_lines(spec, k=a.k, k_row=a.k_row),
                     "paper_commit": spec["paper"]["commit"], "spec_sha256": L._sha_file(Path(a.spec))}
            print("\n".join(f"{key}: {value}" for key, value in lines.items()))
        elif a.cmd == "check-note":
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=not a.draft)
            fields = check_note(Path(a.note), Path(a.spec), spec=spec, draft=a.draft)
            print(json.dumps({"ok": True, "K": fields["_K"], "mode": "draft" if a.draft else "strict"}, indent=1))
        elif a.cmd == "check-ar-record":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            out = check_ar_record(spec, Path(a.spec), read_main=G._read_main)
            out["noise_floor"].pop("raw", None)
            print(json.dumps(out, indent=1))
        elif a.cmd == "measurement-path":
            print(json.dumps(measurement_path_check(Path(a.repo), a.g1b_pin, a.g5_commit), indent=1))
        elif a.cmd == "freeze-wait":
            print(json.dumps(freeze_wait_check(load_spec(Path(a.spec)), today=date.fromisoformat(a.today),
                                               released=a.released, stopped=a.stopped,
                                               before_arms_frozen=a.before_arms_frozen), indent=1))
        elif a.cmd == "serve":
            import g5_job                                    # noqa: PLC0415
            check_import_sources()
            print(json.dumps(g5_job.serve_launch(Path(a.spec), Path(a.note), enable=a.enable), indent=1,
                             default=str))
        elif a.cmd in ("cpus", "logdir"):
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            node = node_entry(spec, a.node)
            print(node.get("cpus") or spec["worker"]["cpus"] if a.cmd == "cpus" else
                  str(Path(spec["worker"]["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "close-attempt":
            import g5_job                                    # noqa: PLC0415
            check_import_sources()
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            print(json.dumps(g5_job.close_attempt(spec, Path(a.spec), a.node, a.job, Path(a.attempt_dir), a.reason,
                                                  chunk=a.chunk), indent=1))
        elif a.cmd == "wave-checks":
            import g5_job                                    # noqa: PLC0415
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            print(json.dumps(g5_job.wave_checks(spec, a.node, a.wave), indent=1))
        elif a.cmd == "dates":
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            g4_path = HERE / "g4_tasl_spec.json"
            g4spec, g4sha = T4.load_spec(g4_path), L._sha_file(g4_path)
            summaries = {}
            for sealed in a.sealed:
                s = T4.read_sealed_summary(Path(sealed), g4spec, g4sha)
                if s["node"] in summaries:
                    raise Stop(f"STOP: two sealed attempts given for {s['node']}")
                summaries[s["node"]] = s
            print(json.dumps(T4.recompute_dates(summaries, dates_params(spec), today=date.fromisoformat(a.today)),
                             indent=1, default=str))
        else:
            out = launch(Path(a.spec), Path(a.note), a.node, job=a.job, enable=a.enable, today=date.today(),
                         server_record=Path(a.server_record) if a.server_record else None)
            print(json.dumps({"ok": True, "node": a.node, "job": a.job}, indent=1, default=str))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
