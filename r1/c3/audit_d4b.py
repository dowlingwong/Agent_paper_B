"""The D4 option-B contingency of the sweep-2 fresh-seed audit: R1-BX-PROPOSED-CONFIRM REVISIONS (c) (E5, partial
labels), implemented now and kept OFF (R1-SWEEP2-B2-DECISIONS: "the Mac agent implements D4 option B ... now, as an
independently reviewed code path that stays unused; it may be used only after a D4 STOP and a further author row").
AI-assisted (Claude). ENGINEERING code; it opens no label or evaluation file of a real audit.

**Default (D4 A, unchanged).** Without the contingency, ``audit.evidence_run`` STOPs at the first failed, missing,
non-finite or file-changing seed run, as for sweep 1. Nothing in this module runs.

**Enabling.** ``audit.evidence_run(..., d4b_after_stop=<stopped audit dir>)`` (CLI ``--d4b-after-stop``) runs only when
``check_contingency`` passes:

- the stopped audit is a sweep-2 EVIDENCE audit output (``results/r1/evidence/C3_audit_EVIDENCE_*``) with a
  ``STOP.json`` whose reason is a seed-run STOP (``invalid audit result for <node>/<config>``) and an
  ``environment.json`` with ``source: sweep2``: the D4 STOP the row speaks of;
- PLAN §10 on ``origin/main`` holds exactly one dated author row ``D4B_ROW`` (``R1-SWEEP2-B2-D4B``) that names the
  sweep-2 run id, ``R1-BX-PROPOSED-CONFIRM REVISIONS (c)`` and the sha256 of that ``STOP.json``. No such row exists
  when this code is written; the author writes it after a D4 STOP.

The contingency audit is a new, complete audit directory like any other (no resume of the stopped one).

**E5, as implemented.**

- *A divergent seed run* (REVISIONS (c): "a non-finite loss, or no metric at the fixed budget"): a run that changed no
  file and ended without a finite metric while the training process itself ran to its end. That means either it
  exited 0 with no finite metric (a NaN or inf metric does not parse), or it exited non-zero (``exit code N``). A
  timeout, a worker exception (``run_command raised ...``) or a changed file is not divergence: it stays a STOP.
- *Per role block* (label seeds 7001–7005, evaluation seeds 7006–7010, each on its own): a seed pair is usable when
  neither the candidate's nor the incumbent's run diverged.
  - More than half of the candidate's runs divergent (3 or more of 5) makes the proposal **divergent** in that
    block. It gets no belief-bin label (``label_kind: divergent``, ``delta_label: null``), is counted separately, and
    carries the action-target rule ``u = -g`` of REVISIONS (c).
  - Otherwise the label comes from the usable pairs and is marked **partial** when fewer than 5 were usable
    (``k_label`` = the number used, ``diverged_seeds`` listed). Fewer than 2 usable pairs is a STOP: no standard
    error, and an incumbent's divergence is not a property of the proposal.
- REVISIONS (c)'s Student-t for a heavy-tailed node "declared before labels are built" is not implemented: no node is
  declared heavy-tailed. A declaration would need its own row and code.

**Consumers.** A contingency audit's completion has schema ``r1.c3_audit_completion/5`` and a ``d4b_contingency``
record. The release check and the readers accept only ``/4``, so a contingency label block is consumable only after
a reviewed change to those consumers. That is deliberate: divergent and partial labels change what a reader gets.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

D4B_ROW = "R1-SWEEP2-B2-D4B"
D4B_COMPLETION_SCHEMA = "r1.c3_audit_completion/5"
RULE = "R1-BX-PROPOSED-CONFIRM REVISIONS (c)"
ACTION_TARGET_RULE = "u = -g (R1-BX-PROPOSED-CONFIRM REVISIONS (c))"
STOP_REASON = re.compile(r"^invalid audit result for [^/\s]+/[0-9a-f]+$")
EXIT_CODE = re.compile(r"^exit code -?\d+$")
BLOCK = 5                                   # seeds per role block (7001-7005 label, 7006-7010 evaluation)


def _finite(value) -> bool:
    return value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def is_divergent(row: dict) -> bool:
    """A divergent seed run (module docstring): no file changed, no finite metric, and the process ran to its end."""
    if row.get("changed_files") is not False or _finite(row.get("metric")):
        return False
    if row.get("success") is True:
        return True
    return isinstance(row.get("failure"), str) and bool(EXIT_CODE.fullmatch(row["failure"]))


def is_valid_finite(row: dict) -> bool:
    return row.get("success") is True and row.get("changed_files") is False and _finite(row.get("metric"))


def check_contingency(paper_root: Path, stopped_audit: Path) -> dict:
    """The enabling conditions (module docstring); returns the record bound into the environment and completion."""
    from r1.c3 import sweep2_batch
    from r1.c3.audit import _published_bytes
    from r1.c3.release import author_rows
    stopped = Path(stopped_audit)
    rel = stopped.resolve().relative_to(Path(paper_root).resolve()) if stopped.is_absolute() else stopped
    if rel.parts[:3] != ("results", "r1", "evidence") or len(rel.parts) != 4 or \
            not rel.parts[3].startswith("C3_audit_EVIDENCE_"):
        raise ValueError("D4B: the stopped audit must be results/r1/evidence/C3_audit_EVIDENCE_<stamp>")
    base = Path(paper_root) / rel
    stop_path, env_path = base / "STOP.json", base / "environment.json"
    if not stop_path.is_file() or not env_path.is_file() or (base / "evidence_completion.json").exists():
        raise ValueError("D4B: the stopped audit has no STOP.json/environment.json, or completed")
    stop_bytes = stop_path.read_bytes()
    stop = json.loads(stop_bytes)
    if stop.get("label") != "EVIDENCE" or not STOP_REASON.fullmatch(str(stop.get("reason", ""))):
        raise ValueError("D4B: the stopped audit's STOP is not a seed-run STOP (invalid audit result for ...)")
    if json.loads(env_path.read_text()).get("source") != "sweep2":
        raise ValueError("D4B: the stopped audit is not a sweep-2 audit")
    stop_sha = hashlib.sha256(stop_bytes).hexdigest()
    plan = _published_bytes(Path(paper_root), "docs/r1/PLAN.md").decode("utf-8")
    rows = [d for i, d in author_rows(plan) if i == D4B_ROW]
    if len(rows) != 1 or not all(t in rows[0] for t in (sweep2_batch.RUN_ID, RULE, stop_sha)):
        raise ValueError(f"D4B is OFF: no single author row {D4B_ROW} on origin/main naming the run id, {RULE} and "
                         f"the stopped audit's STOP.json sha256 {stop_sha}")
    return {"row": D4B_ROW, "row_sha256": hashlib.sha256(rows[0].encode()).hexdigest(), "rule": RULE,
            "stopped_audit": str(rel), "stop_sha256": stop_sha, "stop_reason": stop["reason"]}


def validate_results(plan: list[dict], cache, seeds) -> list[dict]:
    """Every seed run present and either valid-finite or divergent; anything else is a STOP. Divergent metrics are
    carried as None (the pair is dropped in its block)."""
    out = []
    for p in plan:
        metrics = {}
        for key in ("candidate_hash", "incumbent_hash"):
            vals = []
            for s in seeds:
                row = cache.get(p["node"], p[key], s)
                if row is None:
                    raise ValueError("missing evidence audit run")
                if is_valid_finite(row):
                    vals.append(float(row["metric"]))
                elif is_divergent(row):
                    vals.append(None)
                else:
                    raise ValueError(f"evidence audit run neither valid nor divergent ({p['node']}/{p[key]}/{s})")
            metrics[key] = vals
        out.append({"proposal_id": p["proposal_id"], "node": p["node"], "reason": p.get("reason"),
                    "candidate_hash": p["candidate_hash"], "incumbent_hash": p["incumbent_hash"],
                    "seeds": list(seeds), "candidate_metrics": metrics["candidate_hash"],
                    "incumbent_metrics": metrics["incumbent_hash"]})
    return out


def block_label(cand: list, inc: list, seeds: list[int]) -> dict:
    """E5 for one role block of 5 seeds (module docstring)."""
    from r1.c3.audit import paired
    if len(cand) != BLOCK or len(inc) != BLOCK or len(seeds) != BLOCK:
        raise ValueError("D4B: a role block has five seeds")
    cand_div = [s for s, c in zip(seeds, cand) if c is None]
    inc_div = [s for s, i in zip(seeds, inc) if i is None]
    if len(cand_div) * 2 > BLOCK:
        return {"divergent": True, "candidate_diverged_seeds": cand_div, "incumbent_diverged_seeds": inc_div}
    usable = [k for k in range(BLOCK) if cand[k] is not None and inc[k] is not None]
    if len(usable) < 2:
        raise ValueError("D4B: fewer than two usable seed pairs in a role block; STOP")
    stats = paired([cand[k] for k in usable], [inc[k] for k in usable])
    return {"divergent": False, "delta": stats["delta_audit"], "se": stats["se"], "k": len(usable),
            "partial": len(usable) < BLOCK, "candidate_diverged_seeds": cand_div, "incumbent_diverged_seeds": inc_div}


def blocks(table: Path, results: list[dict]) -> tuple[list[dict], list[dict]]:
    """The two role blocks under E5: rule no-ops as in D4 A, duplicates unlabelled, audited proposals by
    ``block_label`` per block."""
    from r1.c3.arms import is_duplicate, is_noop
    from r1.c3.audit import DEFAULT_SEEDS
    from r1.c3.dataset import load_table
    rows = load_table(Path(table))
    audits = {r["proposal_id"]: r for r in results}
    if len(audits) != len(results):
        raise ValueError("duplicate proposal ID in audit results")
    labels, evaluations, used = [], [], set()
    lab_seeds, ev_seeds = list(DEFAULT_SEEDS[:BLOCK]), list(DEFAULT_SEEDS[BLOCK:])
    for row in rows:
        pid, node = row["proposal_id"], row["node"]
        if is_noop(row):
            labels.append({"proposal_id": pid, "node": node, "label_kind": "rule_noop", "delta_label": 0.0,
                           "se_label": 0.0, "soft_parameters": {"inert": True}})
            continue
        if is_duplicate(row):
            if pid in audits:
                raise ValueError("duplicate proposal must not receive an audit label")
            continue
        result = audits.get(pid)
        if result is None or result.get("node") != node or result.get("seeds") != list(DEFAULT_SEEDS):
            raise ValueError("evidence result does not cover eligible table rows")
        sigma = float(row["sigma_node"])
        if not math.isfinite(sigma) or sigma <= 0:
            raise ValueError("invalid node sigma for evidence soft-label parameters")
        c, i = result["candidate_metrics"], result["incumbent_metrics"]
        lab = block_label(c[:BLOCK], i[:BLOCK], lab_seeds)
        ev = block_label(c[BLOCK:], i[BLOCK:], ev_seeds)
        common = {"candidate_diverged_seeds": lab["candidate_diverged_seeds"],
                  "incumbent_diverged_seeds": lab["incumbent_diverged_seeds"], "rule": RULE}
        if lab["divergent"]:
            labels.append({"proposal_id": pid, "node": node, "label_kind": "divergent", "seeds": lab_seeds,
                           "delta_label": None, "se_label": None, "action_target_rule": ACTION_TARGET_RULE,
                           "soft_parameters": None, **common})
        else:
            labels.append({"proposal_id": pid, "node": node, "label_kind": "audit_partial" if lab["partial"]
                           else "audit", "seeds": lab_seeds, "delta_label": lab["delta"], "se_label": lab["se"],
                           "k_label": lab["k"], "partial": lab["partial"],
                           "soft_parameters": {"inert": False, "sigma_node": sigma, "k_label": lab["k"],
                                               "delta_label": lab["delta"], "se_label": lab["se"]}, **common})
        ev_common = {"candidate_diverged_seeds": ev["candidate_diverged_seeds"],
                     "incumbent_diverged_seeds": ev["incumbent_diverged_seeds"]}
        evaluations.append({"proposal_id": pid, "node": node, "seeds": ev_seeds, "divergent": ev["divergent"],
                            "delta_evaluation": None if ev["divergent"] else ev["delta"],
                            "se_evaluation": None if ev["divergent"] else ev["se"],
                            "k_evaluation": None if ev["divergent"] else ev["k"],
                            "partial": False if ev["divergent"] else ev["partial"], **ev_common})
        used.add(pid)
    if used != set(audits):
        raise ValueError("audit results contain unexpected proposal IDs")
    return labels, evaluations


def counts(labels: list[dict]) -> dict:
    """Divergent proposals are counted separately (REVISIONS (c))."""
    kinds = [x["label_kind"] for x in labels]
    return {"divergent": kinds.count("divergent"), "partial": kinds.count("audit_partial"),
            "complete": kinds.count("audit"), "rule_noop": kinds.count("rule_noop")}
