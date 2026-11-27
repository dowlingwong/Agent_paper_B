"""D.3 outcome-table builder (gap G7): campaign summaries + audit rows -> ``r1_d3_outcome/v2``. AI-assisted (Claude).

ENGINEERING_ONLY until a signed D.3 note cites the reviewed unit.  Source: the D.3 pre-declaration revision 4 §8 (the
schema), §7.1 (Y), §7.5 (secondary outcomes), §12 G7; the G1/G6 design on ``main``
(``docs/r1/proposals/d3_design_20261126/``) §2.2, §3.1, §3.3, as revision 4 amends it (G7 writes v2).  The table the
builder writes is validated by the pinned analysis's own ``d3_analysis.validate_table`` before it is written, so a
table this module writes is one the analysis accepts; nothing here changes the analysis.

Inputs (contracts for G1 and G6; neither exists yet):

* **Campaign summary** (G1, one per campaign; ``r1_d3_campaign_summary/v1``): exactly ``SUMMARY_KEYS``.  The
  mechanism counts and ``last_keep_run`` come from ``mechanism_counts`` on the campaign's ledger and events; the
  compute fields from the job record.  ``status`` other than ``complete`` (``stop``, ``error``) refuses the whole
  stage: no table is built from a partial design (§10).  ``unfundable`` is true only when FIXR3/EGATE ended because
  the next required step could not be funded.  ``infra_attempts`` counts the attempts of the campaign's chunk
  (§3.1; >= 1).
* **Audit rows** (G6; ``r1_d3_audit_row/v1``): ``{"schema", "campaign_id", "point", "keep_run", "config_sha256",
  "y_raw"}`` with ``point`` ``"final"`` (the final incumbent at the actual final charged-run count, the primary Y),
  ``"5"``/``"10"``/``"15"``/``"20"`` (the snapshots, §7.5 (a)) or ``"keep"`` (every kept incumbent, at charged run
  ``keep_run``, for ``last_improving_run``, §7.5 (d); §13 item 25).  A configuration equal to the start has
  y_raw = 0 by rule and G6 still writes its row (flagged by G6, not read here).  A campaign with no charged run
  (w_final = 0) has no audit row at all and y_raw = 0.

Every input path is checked by ``d3_analysis.refuse_input_path``'s rules where it applies and by
``analysis_guard.refuse_sealed``; the builder opens no label, evaluation or test file.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Callable, Iterable

from r1.c3 import d3_analysis as D3
from r1.c3.accounting import replicate_entries, table_ended_on

SUMMARY_SCHEMA = "r1_d3_campaign_summary/v1"
AUDIT_ROW_SCHEMA = "r1_d3_audit_row/v1"
SUMMARY_KEYS = frozenset({"schema", "stage", "arm", "node", "instance_seed", "repetition", "status", "gpu_model",
                          "infra_attempts", "worker_runs", "llm_calls", "unfundable", "start_config_hash",
                          "final_config_hash", "last_keep_run", *D3.COMPUTE_INT_KEYS, *D3.COMPUTE_SECONDS_KEYS,
                          *D3.MECHANISM_KEYS})
AUDIT_KEYS = frozenset({"schema", "campaign_id", "point", "keep_run", "config_sha256", "y_raw"})
POINTS = ("final", "keep", *(str(w) for w in D3.BUDGET_POINTS))
RULE_SKIP_REASONS = ("rule_noop", "rule_duplicate")
VALUE_SKIP_REASONS = ("prior_no_gain",)


class OutcomeTableError(ValueError):
    """A refusal of the builder: nothing is written."""


# ---------------------------------------------------------------------------
# §7.5 (d): mechanism counts from one campaign's harness ledger and events
# ---------------------------------------------------------------------------

def _ran(record: dict) -> bool:
    mode = str(record.get("worker_mode") or "")
    return mode != "control_plane" and not mode.endswith("_precheck")


def charged_runs_of(record: dict) -> int:
    """Charged worker runs of one trial record: its own run, 2 r per verify, its charged replicate runs (G8)."""
    n = 1 if _ran(record) else 0
    verify = ((record.get("extra") or {}).get("control") or {}).get("verify")
    if verify:
        n += 2 * int(verify.get("r", len(verify.get("pairs") or [])))
    return n + sum(1 for e in replicate_entries(record) if e["charged"])


def mechanism_counts(records: list[dict], events: list[dict], *, config_of: Callable[[dict], str | None]) -> dict:
    """``MECHANISM_KEYS`` + ``last_keep_run`` + ``worker_runs`` of one campaign (§7.5 (d)).

    Duplicates are the rule layer's ``duplicate`` flag in the trial's E1 ``control_decision`` detail (every D.3
    controller logs it, with the rule layer on or off: ``RuleController``, ``d3_controllers.RuleLayerController``);
    a rule skip is a skip with ``skip_reason`` ``rule_noop``/``rule_duplicate``, a value skip one with
    ``prior_no_gain``; keeps count every kept trial (the first valid trial included); ``last_keep_run`` is the
    charged-run count when the last kept trial's runs were spent; ``config_of(record)`` gives the executed
    configuration's sha256 (G1 knows it), and a trial that ran without one is refused.
    """
    flags: dict[str, dict] = {}
    for e in events:
        if e.get("event_type") == "control_decision" and (e.get("payload") or {}).get("epoch") == "E1":
            flags[str(e.get("trial_id"))] = ((e["payload"].get("detail") or {}).get("rule") or {})
    w, out, configs, last_keep = 0, {k: 0 for k in D3.MECHANISM_KEYS}, set(), None
    for r in sorted(records, key=lambda r: int(r["budget_index"])):
        ran = _ran(r)
        w += charged_runs_of(r)
        dup = bool(flags.get(str(r.get("trial_id")), {}).get("duplicate"))
        out["duplicates_proposed"] += dup
        out["duplicates_executed"] += dup and ran
        reason = ((r.get("extra") or {}).get("control") or {}).get("skip_reason")
        if r.get("decision") == "skipped":
            out["rule_skips"] += reason in RULE_SKIP_REASONS
            out["value_skips"] += reason in VALUE_SKIP_REASONS
        if ran:
            cfg = config_of(r)
            if not isinstance(cfg, str) or not cfg:
                raise OutcomeTableError(f"trial {r.get('budget_index')}: executed without a configuration sha256")
            configs.add(cfg)
        if r.get("decision") == "kept":
            out["keeps"] += 1
            last_keep = w
    out["distinct_configs_executed"] = len(configs)
    return {**out, "last_keep_run": last_keep, "worker_runs": w}


def last_improving_run(keep_audits: Iterable[tuple[int, float]]) -> int | None:
    """§7.5 (d): the charged-run count at the last keep whose new incumbent's audited y_raw exceeds the previous
    incumbent's (the start configuration's y_raw is 0 by rule); None if no keep improved."""
    prev, last = 0.0, None
    for run, y in sorted(keep_audits):
        if y > prev:
            last = run
        prev = y
    return last


# ---------------------------------------------------------------------------
# Rows and table
# ---------------------------------------------------------------------------

def _is_int(x) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def _check_summary(s: dict, stage: str) -> str:
    if not isinstance(s, dict) or set(s) != SUMMARY_KEYS:
        raise OutcomeTableError(f"a campaign summary must hold exactly {sorted(SUMMARY_KEYS)}")
    if s["schema"] != SUMMARY_SCHEMA or s["stage"] != stage:
        raise OutcomeTableError(f"campaign summary schema must be {SUMMARY_SCHEMA!r} for stage {stage!r}")
    for key in ("instance_seed", "repetition", "worker_runs", "llm_calls", "infra_attempts"):
        if not _is_int(s[key]):
            raise OutcomeTableError(f"campaign summary {key} must be an integer")
    cid = D3.campaign_id(stage, s["arm"], s["node"], s["instance_seed"], s["repetition"])
    if s["status"] != "complete":
        raise OutcomeTableError(f"{cid}: status {s['status']!r}; a stage with a campaign that is not complete is a "
                                "STOP and no outcome table is built from it (§10)")
    if not isinstance(s["unfundable"], bool):
        raise OutcomeTableError(f"{cid}: unfundable must be a boolean")
    return cid


def _audits_by_campaign(audits: Iterable[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for a in audits:
        if not isinstance(a, dict) or set(a) != AUDIT_KEYS or a["schema"] != AUDIT_ROW_SCHEMA:
            raise OutcomeTableError(f"an audit row must hold exactly {sorted(AUDIT_KEYS)} with schema "
                                    f"{AUDIT_ROW_SCHEMA!r}")
        if a["point"] not in POINTS:
            raise OutcomeTableError(f"audit point must be one of {POINTS}")
        y = a["y_raw"]
        if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(float(y)):
            raise OutcomeTableError(f"{a['campaign_id']}: audit y_raw must be finite (a non-finite audit is a STOP)")
        slot = by.setdefault(a["campaign_id"], {"keep": []})
        if a["point"] == "keep":
            if not _is_int(a["keep_run"]) or a["keep_run"] < 1:
                raise OutcomeTableError(f"{a['campaign_id']}: a keep audit names its charged run (>= 1)")
            slot["keep"].append(a)
        else:
            if a["keep_run"] is not None:
                raise OutcomeTableError(f"{a['campaign_id']}: keep_run is only for keep audits")
            if a["point"] in slot:
                raise OutcomeTableError(f"{a['campaign_id']}: audit point {a['point']} given twice")
            slot[a["point"]] = a
    return by


def build_row(stage: str, s: dict, audit: dict | None) -> dict:
    cid = _check_summary(s, stage)
    runs = s["worker_runs"]
    hpo = stage == "HPO-REF"
    if hpo:  # §5.8: W runs, or (RS only) the proposal cap of 80 draws
        if s["unfundable"]:
            raise OutcomeTableError(f"{cid}: a reference row never ends on an unfundable step")
        if runs == D3.W:
            ended_on = "worker_runs"
        elif s["arm"] == "RS" and s["proposals"] == D3.HPO_PROPOSAL_CAP:
            ended_on = "proposal_cap"
        else:
            raise OutcomeTableError(f"{cid}: the reference campaign has not ended (below W and below the cap)")
    else:
        try:
            ended_on = table_ended_on(worker_runs=runs, llm_calls=s["llm_calls"], arm=s["arm"],
                                      unfundable=s["unfundable"])
        except ValueError as exc:
            raise OutcomeTableError(f"{cid}: {exc}") from None
    audit = audit or {"keep": []}
    start, final = s["start_config_hash"], s["final_config_hash"]
    if runs == 0:
        if set(audit) != {"keep"} or audit["keep"]:
            raise OutcomeTableError(f"{cid}: a campaign with no charged run has no audit row")
        if final != start:
            raise OutcomeTableError(f"{cid}: no charged run, so the final configuration is the start")
        y_raw = 0.0
    else:
        if "final" not in audit:
            raise OutcomeTableError(f"{cid}: the final-incumbent audit is missing")
        if audit["final"]["config_sha256"] != final:
            raise OutcomeTableError(f"{cid}: the final audit is of another configuration than the final incumbent")
        y_raw = float(audit["final"]["y_raw"])
    y_w = {}
    for w in D3.BUDGET_POINTS:
        key = str(w)
        if runs < w:
            if key in audit:
                raise OutcomeTableError(f"{cid}: an audit at w = {w} for a campaign that ended at {runs} runs")
            y_w[key] = None
        else:
            if key not in audit:
                raise OutcomeTableError(f"{cid}: the snapshot audit at w = {w} is missing")
            y_w[key] = float(audit[key]["y_raw"])
    if runs == D3.W and (audit[str(D3.W)]["config_sha256"] != final or y_w[str(D3.W)] != y_raw):
        raise OutcomeTableError(f"{cid}: at w = {D3.W} the snapshot audit is the final audit (one canonical audit)")
    keeps = sorted(audit["keep"], key=lambda a: a["keep_run"])
    if len(keeps) != s["keeps"] or len({a["keep_run"] for a in keeps}) != len(keeps):
        raise OutcomeTableError(f"{cid}: one keep audit per keep is required (§7.5 (d); §13 item 25)")
    if keeps:
        if keeps[-1]["keep_run"] != s["last_keep_run"]:
            raise OutcomeTableError(f"{cid}: the last keep audit is not at last_keep_run")
        if keeps[-1]["config_sha256"] != final or float(keeps[-1]["y_raw"]) != y_raw:
            raise OutcomeTableError(f"{cid}: the last kept incumbent is the final incumbent; its audits must agree")
    elif final != start:
        raise OutcomeTableError(f"{cid}: no keep, so the final configuration is the start")
    row = {"campaign_id": cid, "stage": stage, "arm": s["arm"], "node": s["node"],
           "instance_id": D3.instance_id(s["node"], s["instance_seed"]), "instance_seed": s["instance_seed"],
           "repetition": s["repetition"], "memory_mode": D3.HPO_MEMORY_MODE if hpo else D3.MEMORY_MODE,
           "status": "complete", "y_raw": y_raw, "worker_runs": runs, "llm_calls": s["llm_calls"],
           "audit_seeds": list(D3.audit_seeds(s["instance_seed"])), "start_config_hash": start,
           "final_config_hash": final, "gpu_model": s["gpu_model"], "infra_attempts": s["infra_attempts"],
           "y_raw_w": y_w, "last_keep_run": s["last_keep_run"],
           "last_improving_run": last_improving_run((a["keep_run"], float(a["y_raw"])) for a in keeps),
           "ended_on": ended_on}
    for key in (*D3.COMPUTE_INT_KEYS, *D3.COMPUTE_SECONDS_KEYS, *D3.MECHANISM_KEYS):
        row[key] = s[key]
    return row


def sigma_from_noise_source(summary_path=None) -> dict:
    """sigma_node of the seven nodes by ``dataset.noise_table`` on the pinned noise summary (sha256-checked)."""
    from r1.c3.analysis_guard import refuse_sealed
    from r1.c3.dataset import noise_table
    from r1.harness import REPO
    path = Path(summary_path) if summary_path is not None else REPO / D3.NOISE_SOURCE_PATH
    refuse_sealed(path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != D3.NOISE_SOURCE_SHA256:
        raise OutcomeTableError("the noise summary's sha256 differs from the pinned noise source")
    table = noise_table(path)
    return {node: float(table[node]["sigma_node"]) for node in D3.NODES}


def build_table(stage: str, summaries: Iterable[dict], audits: Iterable[dict], *, predeclaration_path,
                d3b_note=None, repetitions: int = D3.REPETITIONS, noise_summary_path=None) -> dict:
    """The validated ``r1_d3_outcome/v2`` table of one stage.  D.3b reads ``a6_entered`` from the signed D.3b note
    (``d3_analysis.read_a6_declaration``); D.3a and HPO-REF take no note."""
    if stage not in D3.STAGES:
        raise OutcomeTableError(f"stage must be one of {D3.STAGES}")
    pre = Path(predeclaration_path)
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(pre)
    pre_sha = hashlib.sha256(pre.read_bytes()).hexdigest()
    if stage == "D.3b":
        if d3b_note is None:
            raise OutcomeTableError("a D.3b table needs the signed D.3b note (a6_entered)")
        a6 = D3.read_a6_declaration(d3b_note)
        arms = list(D3.ARMS_D3B_WITH_A6 if a6 else D3.ARMS_D3B)
    else:
        if d3b_note is not None:
            raise OutcomeTableError("only a D.3b table reads the D.3b note")
        a6, arms = None, list(D3.ARMS_D3A if stage == "D.3a" else D3.ARMS_HPO)
    by = _audits_by_campaign(audits)
    rows, used = [], set()
    for s in summaries:
        cid = _check_summary(s, stage)
        rows.append(build_row(stage, s, by.get(cid)))
        used.add(cid)
    if set(by) - used:
        raise OutcomeTableError(f"{len(set(by) - used)} audited campaigns have no summary")
    order = {a: i for i, a in enumerate(arms)}
    rows.sort(key=lambda r: (order.get(r["arm"], len(order)), D3.NODES.index(r["node"]) if r["node"] in D3.NODES
                             else len(D3.NODES), r["instance_seed"], r["repetition"]))
    table = {"schema": D3.SCHEMA, "stage": stage, "predeclaration_sha256": pre_sha,
             "noise_source_sha256": D3.NOISE_SOURCE_SHA256, "sigma_node": sigma_from_noise_source(noise_summary_path),
             "arms": arms, "a6_entered": a6, "repetitions": repetitions, "rows": rows}
    return D3.validate_table(table, stage)


def write_table(table: dict, out_path) -> Path:
    """Write a validated table with exclusive create (an existing file is never overwritten)."""
    out = Path(out_path)
    if out.suffix != ".json":
        raise OutcomeTableError("an outcome table is a .json file")
    D3.validate_table(table, table.get("stage"))
    data = (json.dumps(table, indent=1, sort_keys=True) + "\n").encode()
    if len(data) > D3.MAX_TABLE_BYTES:
        raise OutcomeTableError(f"outcome table larger than {D3.MAX_TABLE_BYTES} bytes")
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    return out
