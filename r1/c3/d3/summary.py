"""D.3 G1 → G7 campaign summary and the per-keep records (ENGINEERING code).

The G7 builder accepts one ``r1_d3_campaign_summary/v1`` per campaign, with exactly
``d3_outcome_table.SUMMARY_KEYS``.  This module produces that record from the records the G1
chunk actually wrote: the ledger, the event log and the recorder's per-trial configuration
captures.  It also produces the per-keep list G6 audits (revision 4 item 25: every kept
incumbent at its charged-run count).

No campaign, GPU job, audit, label or evaluation value is read here.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

from r1.c3 import d3_analysis as D3
from r1.c3.accounting import replicate_entries
from r1.c3.d3.snapshots import config_sha256

SUMMARY_SCHEMA = "r1_d3_campaign_summary/v1"
RULE_SKIP_REASONS = ("rule_noop", "rule_duplicate")
VALUE_SKIP_REASONS = ("prior_no_gain",)
#: Arms whose controller has no rule layer and therefore logs no E1 rule flags.
NO_RULE_FLAGS = ("A0", "FIXR3", "EGATE")
#: A campaign that ended on one of these is complete; a stop/error is not a table row.
COMPLETE_ENDED_ON = ("worker_runs", "llm_call_cap", "no_fundable_candidate")


class SummaryStop(RuntimeError):
    """The production records cannot produce a G7 summary; nothing is written."""


def table_stage(stage: str) -> str:
    """The chunk's ``a``/``b`` stage as the G7 table's ``D.3a``/``D.3b``."""
    return {"a": "D.3a", "b": "D.3b"}.get(str(stage), str(stage))


def _ran(record: Mapping[str, Any]) -> bool:
    mode = str(record.get("worker_mode") or "")
    return mode != "control_plane" and not mode.endswith("_precheck")


def charged_runs_of(record: Mapping[str, Any]) -> int:
    """The charged worker runs of one trial (own run, verify pairs, charged replicates)."""
    n = 1 if _ran(record) else 0
    verify = ((record.get("extra") or {}).get("control") or {}).get("verify")
    if verify:
        n += 2 * int(verify.get("r", len(verify.get("pairs") or [])))
    return n + sum(1 for e in replicate_entries(dict(record)) if e["charged"])


def _flags(records: list[dict], events: list[dict]) -> dict[str, dict | None]:
    flags: dict[str, dict | None] = {}
    for event in events:
        if event.get("event_type") != "control_decision":
            continue
        payload = event.get("payload") or {}
        if payload.get("epoch") != "E1":
            continue
        detail = payload.get("detail") or {}
        if "rule" in detail:
            flags[str(event.get("trial_id"))] = detail["rule"] or {}
        elif str(detail.get("reason") or "").startswith(("no_features", "featurize_failed")):
            flags[str(event.get("trial_id"))] = {}
        else:
            flags[str(event.get("trial_id"))] = None
    return flags


def mechanism_counts(records: Iterable[dict], events: Iterable[dict], *,
                     config_by_trial: Mapping[int, Mapping[str, Any]], arm: str) -> dict[str, int]:
    """``MECHANISM_KEYS`` + ``last_keep_run`` + ``worker_runs`` from the G1 records.

    This mirrors G7's ``mechanism_counts`` but tolerates the declared no-rule arms (A0 and the
    two replicate engines), which have no rule layer to log.  An A1/A2/LADDER/A0R trial that
    ran without its E1 rule flags is a STOP, as in G7.
    """
    records = sorted((dict(r) for r in records), key=lambda r: int(r["budget_index"]))
    events = [dict(e) for e in events]
    flags = _flags(records, events)
    w, out, configs, last_keep = 0, {k: 0 for k in D3.MECHANISM_KEYS}, set(), None
    for record in records:
        ran = _ran(record)
        w += charged_runs_of(record)
        flag = flags.get(str(record.get("trial_id")))
        if ran and flag is None and arm not in NO_RULE_FLAGS:
            raise SummaryStop(
                f"trial {record.get('budget_index')}: executed without an E1 decision that logs the "
                "rule flags (A1/A2/LADDER/A0R must run a flag-logging controller)")
        duplicate = bool((flag or {}).get("duplicate"))
        out["duplicates_proposed"] += int(duplicate)
        out["duplicates_executed"] += int(duplicate and ran)
        control = (record.get("extra") or {}).get("control") or {}
        reason = control.get("skip_reason")
        if record.get("decision") == "skipped":
            out["rule_skips"] += int(reason in RULE_SKIP_REASONS)
            out["value_skips"] += int(reason in VALUE_SKIP_REASONS)
        if ran:
            captured = config_by_trial.get(int(record["budget_index"]))
            sha = str((captured or {}).get("config_sha256") or "")
            if not sha:
                raise SummaryStop(
                    f"trial {record.get('budget_index')}: executed without a captured configuration sha256")
            configs.add(sha)
        if str(record.get("decision")) in ("keep", "kept"):
            out["keeps"] += 1
            last_keep = w
    out["distinct_configs_executed"] = len(configs)
    return {**out, "last_keep_run": last_keep, "worker_runs": w}


def keep_records(records: Iterable[dict], *,
                 config_by_trial: Mapping[int, Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every kept incumbent with its charged-run count and captured configuration."""
    out: list[dict[str, Any]] = []
    w = 0
    for record in sorted((dict(r) for r in records), key=lambda r: int(r["budget_index"])):
        w += charged_runs_of(record)
        if str(record.get("decision")) not in ("keep", "kept"):
            continue
        captured = config_by_trial.get(int(record["budget_index"]))
        if not captured:
            raise SummaryStop(
                f"trial {record.get('budget_index')}: kept without a captured configuration")
        files = dict(captured["files"])
        sha = config_sha256(files)
        if sha != captured["config_sha256"]:
            raise SummaryStop(f"trial {record.get('budget_index')}: captured config sha256 differs")
        out.append({"keep_run": int(w), "config_sha256": sha, "files": files})
    return out


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def compute_fields(records: Iterable[dict], events: Iterable[dict], *,
                   attempts: Iterable[dict] | None = None) -> dict[str, Any]:
    """Compute/token fields G7 requires; missing telemetry is 0 (never invented)."""
    records, events = list(records), [dict(e) for e in events]
    proposals = sum(1 for e in events if e.get("event_type") == "proposal_created")
    if not proposals:
        proposals = len(records)
    prompt = completion = 0
    worker_seconds = 0.0
    controller_seconds = 0.0
    for event in events:
        payload = event.get("payload") or {}
        meta = payload.get("llm_meta") or {}
        prompt += _int(meta.get("prompt_tokens", payload.get("prompt_tokens")))
        completion += _int(meta.get("completion_tokens", payload.get("completion_tokens")))
        if event.get("event_type") == "worker_finished":
            worker_seconds += float(payload.get("elapsed_seconds") or 0.0)
        if event.get("event_type") == "control_decision":
            detail = payload.get("detail") or {}
            controller_seconds += float(payload.get("latency_s") or detail.get("latency_s") or 0.0)
    if attempts is not None and worker_seconds == 0.0:
        worker_seconds = math.fsum(float(a.get("seconds") or 0.0) for a in attempts)
    return {
        "proposals": int(proposals),
        "llm_tokens_prompt": int(prompt),
        "llm_tokens_completion": int(completion),
        "worker_seconds": float(worker_seconds),
        "controller_seconds": float(controller_seconds),
    }


def build_campaign_summary(*, stage: str, arm: str, node: str, instance_seed: int,
                           repetition: int, gpu_model: str, status: str,
                           records: Iterable[dict], events: Iterable[dict],
                           config_by_trial: Mapping[int, Mapping[str, Any]],
                           start_config: Mapping[str, Any], final_config: Mapping[str, Any],
                           worker_runs: int, llm_calls: int, ended_on: str,
                           wall_seconds: float, attempts: Iterable[dict] | None = None,
                           infra_attempts: int = 1, proposer_gpu_seconds: float = 0.0) -> dict[str, Any]:
    """The exact ``SUMMARY_KEYS`` record G7's ``build_row`` reads."""
    records = [dict(r) for r in records]
    events = [dict(e) for e in events]
    mech = mechanism_counts(records, events, config_by_trial=config_by_trial, arm=arm)
    compute = compute_fields(records, events, attempts=attempts)
    out = {
        "schema": SUMMARY_SCHEMA, "stage": table_stage(stage), "arm": arm, "node": node,
        "instance_seed": int(instance_seed), "repetition": int(repetition),
        "status": status, "gpu_model": str(gpu_model),
        "infra_attempts": int(infra_attempts), "worker_runs": int(worker_runs),
        "proposer_gpu_seconds": proposer_gpu_seconds,
        "llm_calls": int(llm_calls), "unfundable": ended_on == "no_fundable_candidate",
        "start_config_hash": config_sha256(dict(start_config)),
        "final_config_hash": config_sha256(dict(final_config)),
        "last_keep_run": mech["last_keep_run"],
        **compute,
        **{k: int(mech[k]) for k in D3.MECHANISM_KEYS},
        "wall_seconds": float(wall_seconds),
    }
    from r1.c3.d3_outcome_table import SUMMARY_KEYS

    missing = sorted(SUMMARY_KEYS - set(out))
    extra = sorted(set(out) - SUMMARY_KEYS)
    if missing or extra:
        raise SummaryStop(f"the G7 summary keys are not exact: missing={missing} extra={extra}")
    return out
