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
  file and ended without a finite metric, read narrowly so that no infrastructure failure becomes a label:
  - it exited 0 without a finite metric (it ran to its end; a NaN or inf metric line does not parse); or
  - it exited with code 1 (``exit code 1``), with no ``FAILURE_CATEGORY`` or ``runtime_error``, and the tail of its
    log (recorded in the run row as ``log_tail``, with ``failure_category``) names a non-finite value (``nan``,
    ``inf``, ``infinity``, ``non-finite``, ``not finite``).
  Everything else stays a STOP, as under D4 A: exit 2 or ``invalid_config`` (a configuration rejection), any other
  exit code, a signal (a negative code, or 128 and above, such as an OOM kill), a timeout, a worker exception
  (``run_command raised ...``), a changed file, or a failed run whose log cannot be read.
- *Per role block* (label seeds 7001–7005, evaluation seeds 7006–7010, each on its own), in the shapes of the frozen
  gate-input builder (``r1/c3/gate_input_builder.py``, pinned by the signed sweep-2 preregistration, PRE-DIV A):
  - More than half of the candidate's runs divergent (3 or more of 5) makes the proposal **divergent** in that block.
    Label: ``label_kind: divergent``, no belief-bin value (``delta_label``, ``se_label``, ``soft_parameters`` null);
    REVISIONS (c)'s action target ``u = -g`` (``ACTION_TARGET_RULE``) is recorded once in the completion's
    ``d4b_contingency``. Evaluation: ``divergent_seeds`` listed, ``k_evaluation`` = 5 − their number, no value
    (PRE-DIV A: r = −g × execute).
  - Otherwise (at most 2 divergent) the value is the paired mean over the other seeds, marked **partial** when any
    diverged: ``label_kind: audit`` with ``soft_parameters.k_label`` = 3 or 4; evaluation rows with
    ``divergent_seeds`` and ``k_evaluation``. A complete row is exactly D4 A's row (no extra key).
  - Divergent and partial proposals are counted separately, per block, in the completion.
  - **An incumbent's divergent run is a STOP.** E5 speaks of the proposal's runs; the incumbent is the already kept
    configuration, its divergence is not a property of the proposal, and the builder has no field for it. The author
    decides (this rule is listed for the author row).
- REVISIONS (c)'s Student-t for a heavy-tailed node "declared before labels are built" is not implemented: no node is
  declared heavy-tailed. A declaration would need its own row and code.
- After a divergent seed run, the remaining seeds of that configuration run in a fresh copy of the node (the used
  copy is kept beside it, renamed), so a crashed run's outputs never reach the next seed.

**Consumers.** A contingency audit's completion has schema ``r1.c3_audit_completion/5`` and a ``d4b_contingency``
record. ``release_checks.sweep2_integrity`` accepts only ``/4``; ``release.evidence_tier`` treats any other schema as
T0, so the sweep-2 release refuses it; ``sft_data.LabelBlockSource`` refuses ``/5`` by name. A contingency label
block is consumable only after a reviewed change to those consumers; the rows themselves already have the shapes the
frozen gate-input builder reads.

**Verification.** ``audit.verify_evidence_completion`` re-checks the contingency record (``recheck_contingency``)
against the copy of the stopped audit's ``STOP.json`` bound inside the contingency audit (``d4b_stopped_STOP.json``)
and against the author row on ``origin/main`` (by its sha256): the stopped directory may later be archived, but the
row's text must stay as signed.
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
DIVERGENT_EXIT = "exit code 1"
DIVERGENT_CATEGORIES = (None, "runtime_error")
NONFINITE = re.compile(r"(?i)\bnan\b|\binf(?:inity)?\b|non-?finite|not finite")
LOG_TAIL_CHARS = 4000
STOP_COPY = "d4b_stopped_STOP.json"
BLOCK = 5                                   # seeds per role block (7001-7005 label, 7006-7010 evaluation)


def _finite(value) -> bool:
    return value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def is_divergent(row: dict) -> bool:
    """A divergent seed run (module docstring): no file changed, no finite metric, and either exit 0, or exit 1 with
    no failure category (or ``runtime_error``) and a non-finite value named in the recorded log tail."""
    if row.get("changed_files") is not False or _finite(row.get("metric")):
        return False
    if row.get("success") is True:
        return True
    return row.get("failure") == DIVERGENT_EXIT and row.get("failure_category") in DIVERGENT_CATEGORIES and \
        isinstance(row.get("log_tail"), str) and bool(NONFINITE.search(row["log_tail"]))


def diagnostics(result) -> dict:
    """What the contingency records beside a seed run (``audit.run_config`` with ``continue_on_divergence``): the
    worker's failure category and, for a failed run, the tail of its log (an unreadable log records an empty tail,
    which is never divergence)."""
    out = {}
    category = (getattr(result, "extra", None) or {}).get("failure_category")
    if category:
        out["failure_category"] = category
    if not result.success:
        try:
            text = Path(result.raw_log_ref).read_text(encoding="utf-8", errors="replace") if result.raw_log_ref else ""
        except OSError:
            text = ""
        out["log_tail"] = text[-LOG_TAIL_CHARS:]
    return out


def is_valid_finite(row: dict) -> bool:
    return row.get("success") is True and row.get("changed_files") is False and _finite(row.get("metric"))


def _row_and_stop(paper_root: Path, stop_bytes: bytes) -> tuple[str, dict]:
    """The STOP is a seed-run STOP and PLAN §10 on origin/main holds exactly one author row D4B_ROW naming the run id,
    the rule and the STOP's sha256."""
    from r1.c3 import sweep2_batch
    from r1.c3.audit import _published_bytes
    from r1.c3.release import author_rows
    stop = json.loads(stop_bytes)
    if stop.get("label") != "EVIDENCE" or not STOP_REASON.fullmatch(str(stop.get("reason", ""))):
        raise ValueError("D4B: the stopped audit's STOP is not a seed-run STOP (invalid audit result for ...)")
    stop_sha = hashlib.sha256(stop_bytes).hexdigest()
    plan = _published_bytes(Path(paper_root), "docs/r1/PLAN.md").decode("utf-8")
    rows = [d for i, d in author_rows(plan) if i == D4B_ROW]
    if len(rows) != 1 or not all(t in rows[0] for t in (sweep2_batch.RUN_ID, RULE, stop_sha)):
        raise ValueError(f"D4B is OFF: no single author row {D4B_ROW} on origin/main naming the run id, {RULE} and "
                         f"the stopped audit's STOP.json sha256 {stop_sha}")
    return rows[0], stop


def _stopped_dir(paper_root: Path, stopped_audit: Path) -> tuple[Path, Path]:
    """``results/r1/evidence/C3_audit_EVIDENCE_<stamp>`` inside the paper root, with no symlink on the way."""
    root = Path(paper_root).resolve()
    stopped = Path(stopped_audit)
    if stopped.is_absolute():
        try:
            rel = stopped.relative_to(root)
        except ValueError:
            raise ValueError("D4B: the stopped audit must lie inside the paper root") from None
    else:
        rel = stopped
    if rel.parts[:3] != ("results", "r1", "evidence") or len(rel.parts) != 4 or \
            not rel.parts[3].startswith("C3_audit_EVIDENCE_"):
        raise ValueError("D4B: the stopped audit must be results/r1/evidence/C3_audit_EVIDENCE_<stamp>")
    probe = root
    for part in rel.parts:
        probe = probe / part
        if probe.is_symlink():
            raise ValueError(f"D4B: the stopped audit path has a symlink component ({probe})")
    return root / rel, rel


def check_contingency(paper_root: Path, stopped_audit: Path) -> dict:
    """The enabling conditions at run time (module docstring); returns the record bound into the environment and
    completion. ``stopped_audit`` is the D4 A audit that STOPped: not completed, not itself a contingency audit."""
    base, rel = _stopped_dir(paper_root, stopped_audit)
    stop_path, env_path = base / "STOP.json", base / "environment.json"
    if not stop_path.is_file() or not env_path.is_file() or (base / "evidence_completion.json").exists():
        raise ValueError("D4B: the stopped audit has no STOP.json/environment.json, or completed")
    environment = json.loads(env_path.read_text())
    if environment.get("source") != "sweep2":
        raise ValueError("D4B: the stopped audit is not a sweep-2 audit")
    if "d4b_contingency" in environment:
        raise ValueError("D4B: the stopped audit is itself a contingency audit; only a D4 A STOP enables D4B")
    stop_bytes = stop_path.read_bytes()
    row, stop = _row_and_stop(paper_root, stop_bytes)
    return {"row": D4B_ROW, "row_sha256": hashlib.sha256(row.encode()).hexdigest(), "rule": RULE,
            "stopped_audit": str(rel), "stop_sha256": hashlib.sha256(stop_bytes).hexdigest(),
            "stop_reason": stop["reason"]}


def stopped_bytes(paper_root: Path, record: dict) -> bytes:
    """The stopped audit's STOP.json bytes, as bound by the record (copied into the contingency audit at its start)."""
    base, _ = _stopped_dir(paper_root, Path(record["stopped_audit"]))
    data = (base / "STOP.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != record["stop_sha256"]:
        raise ValueError("D4B: the stopped audit's STOP.json changed since the check")
    return data


def recheck_contingency(paper_root: Path, record: dict, out: Path) -> None:
    """At verification: the STOP copy bound inside the contingency audit and the author row on origin/main (same
    sha256) still give the recorded contingency. The stopped directory itself is not needed any more; its recorded
    path is informational from then on (the binding is the STOP's sha256, which the row names)."""
    if not isinstance(record, dict) or set(record) != {"row", "row_sha256", "rule", "stopped_audit", "stop_sha256",
                                                       "stop_reason"}:
        raise ValueError("D4B: malformed contingency record")
    copy = Path(out) / STOP_COPY
    if copy.is_symlink() or not copy.is_file():
        raise ValueError(f"D4B: the contingency audit lacks its {STOP_COPY}")
    data = copy.read_bytes()
    row, stop = _row_and_stop(paper_root, data)
    want = {"row": D4B_ROW, "row_sha256": hashlib.sha256(row.encode()).hexdigest(), "rule": RULE,
            "stopped_audit": record["stopped_audit"], "stop_sha256": hashlib.sha256(data).hexdigest(),
            "stop_reason": stop["reason"]}
    if want != record:
        raise ValueError("the D4B contingency record no longer matches its author row and STOP")


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
    """E5 for one role block of 5 seeds (module docstring): divergent when 3 or more of the candidate's runs diverged,
    else the paired mean over the other seeds (partial when any diverged). An incumbent's divergent run is a STOP."""
    from r1.c3.audit import paired
    if len(cand) != BLOCK or len(inc) != BLOCK or len(seeds) != BLOCK:
        raise ValueError("D4B: a role block has five seeds")
    inc_div = [s for s, i in zip(seeds, inc) if i is None]
    if inc_div:
        raise ValueError(f"D4B: the incumbent diverged at seeds {inc_div}; not a property of the proposal: STOP")
    div = [s for s, c in zip(seeds, cand) if c is None]
    if len(div) * 2 > BLOCK:
        return {"divergent": True, "divergent_seeds": div, "k": BLOCK - len(div)}
    usable = [k for k in range(BLOCK) if cand[k] is not None]
    stats = paired([cand[k] for k in usable], [inc[k] for k in usable])
    return {"divergent": False, "delta": stats["delta_audit"], "se": stats["se"], "k": len(usable),
            "partial": bool(div), "divergent_seeds": div}


def blocks(table: Path, results: list[dict]) -> tuple[list[dict], list[dict]]:
    """The two role blocks under E5 in the frozen gate-input builder's shapes: rule no-ops as in D4 A, duplicates
    unlabelled, audited proposals by ``block_label`` per block; complete rows are exactly D4 A's."""
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
        if lab["divergent"]:
            labels.append({"proposal_id": pid, "node": node, "label_kind": "divergent", "seeds": lab_seeds,
                           "delta_label": None, "se_label": None, "soft_parameters": None})
        else:
            labels.append({"proposal_id": pid, "node": node, "label_kind": "audit", "seeds": lab_seeds,
                           "delta_label": lab["delta"], "se_label": lab["se"],
                           "soft_parameters": {"inert": False, "sigma_node": sigma, "k_label": lab["k"],
                                               "delta_label": lab["delta"], "se_label": lab["se"]}})
        evaluation = {"proposal_id": pid, "node": node, "seeds": ev_seeds,
                      "delta_evaluation": None if ev["divergent"] else ev["delta"],
                      "se_evaluation": None if ev["divergent"] else ev["se"]}
        if ev["divergent_seeds"]:            # PRE-DIV A: both or neither; neither = complete (D4 A's row)
            evaluation.update(divergent_seeds=ev["divergent_seeds"], k_evaluation=BLOCK - len(ev["divergent_seeds"]))
        evaluations.append(evaluation)
        used.add(pid)
    if used != set(audits):
        raise ValueError("audit results contain unexpected proposal IDs")
    return labels, evaluations


def counts(labels: list[dict], evaluations: list[dict]) -> dict:
    """Divergent and partial proposals, counted separately per block (REVISIONS (c), PRE-DIV A)."""
    lab = {"divergent": 0, "partial": 0, "complete": 0, "rule_noop": 0}
    for x in labels:
        if x["label_kind"] in ("divergent", "rule_noop"):
            lab[x["label_kind"]] += 1
        else:
            lab["partial" if x["soft_parameters"]["k_label"] < BLOCK else "complete"] += 1
    ev = {"divergent": 0, "partial": 0, "complete": 0}
    for x in evaluations:
        n = len(x.get("divergent_seeds") or [])
        ev["divergent" if n * 2 > BLOCK else "partial" if n else "complete"] += 1
    return {"labels": lab, "evaluations": ev, "action_target_rule": ACTION_TARGET_RULE}
