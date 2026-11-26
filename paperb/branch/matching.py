"""Information / capacity / tuning parity across arms (``matching_report``; PLAN §5 'Matching').

Ported from the legacy ``timing.py::matching_report`` and generalised: every
arm declares a descriptor; the report fails on any mismatch in the matched
fields.  Arms that are allowed to differ (the model family, by design) are not
matched fields.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass

MATCHED_FIELDS = ("information_set", "spending_rule", "intervention_cap", "compute_budget",
                  "llm_call_cap", "tuning_budget", "dev_instances")
# Matched only when some arm declares them (Track H.7, 25 Oct 2026); absent fields keep
# the historical report unchanged.
OPTIONAL_MATCHED_FIELDS = ("instances",)


class MatchingError(ValueError):
    pass


@dataclass(frozen=True)
class ArmDescriptor:
    name: str
    family: str                      # e.g. "rule", "kg_index", "pace", "awr_mlp", "llm_self", "configurator"
    information_set: str             # hash/name of the feature view the arm may read
    spending_rule: str               # the shared online spending rule (name/version)
    intervention_cap: int | None
    compute_budget: int | None
    llm_call_cap: int | None
    tuning_budget: int               # number of candidate configurations calibrated on dev
    dev_instances: str               # hash/name of the development instance set
    instances: str | None = None     # hash/name of the evaluation instance set (online campaigns; H.7)


@dataclass(frozen=True)
class CampaignUsage:
    """What one online campaign of one arm declared and spent (Track H.6/H.7; ``r1.c3.accounting``).

    ``worker_run_cap`` is W and ``llm_call_cap`` the LLM-call cap the campaign
    ran under.  ``llm_calls`` counts every charged call (manager proposals and
    revisions plus controller calls such as A4 queries); sidecar forecasts cost
    compute only (``sidecar_compute_s``); latency is descriptive (13 Oct rule).
    """

    arm: str
    instance: str
    information_set: str
    worker_run_cap: int | None
    llm_call_cap: int | None
    worker_runs: int
    llm_calls: int
    controller_llm_calls: int = 0
    sidecar_calls: int = 0
    sidecar_compute_s: float = 0.0
    prior_unavailable: int = 0
    controller_latency_s: float = 0.0
    trial_budget: int | None = None  # the campaign's trial budget (review F6: must not bind)
    trials: int = 0                  # trials the campaign recorded


def _usage_section(arms: list[ArmDescriptor], usage: list[CampaignUsage]) -> dict:
    """Checks that every arm ran the same instances under the same W, LLM cap and information set."""
    by_arm: dict[str, list[CampaignUsage]] = defaultdict(list)
    for u in usage:
        by_arm[u.arm].append(u)
    names = [a.name for a in arms]
    if sorted(by_arm) != sorted(names):
        raise MatchingError(f"usage arms {sorted(by_arm)} != descriptor arms {sorted(names)}")
    problems = []
    instance_sets = {arm: tuple(sorted(u.instance for u in rows)) for arm, rows in by_arm.items()}
    if len(set(instance_sets.values())) > 1:
        problems.append(f"instances differ: {instance_sets}")
    for field_name in ("worker_run_cap", "llm_call_cap", "information_set"):
        values = {getattr(u, field_name) for u in usage}
        if len(values) > 1:
            problems.append(f"{field_name} differs across campaigns: {sorted(map(str, values))}")
    desc = {a.name: a for a in arms}
    for u in usage:
        d = desc[u.arm]
        if u.worker_run_cap != d.compute_budget or u.llm_call_cap != d.llm_call_cap:
            problems.append(f"{u.arm}/{u.instance}: declared W/LLM cap {d.compute_budget}/{d.llm_call_cap} "
                            f"!= campaign {u.worker_run_cap}/{u.llm_call_cap}")
        if u.information_set != d.information_set:
            problems.append(f"{u.arm}/{u.instance}: information set {u.information_set} != {d.information_set}")
        if u.worker_run_cap is not None and u.worker_runs > u.worker_run_cap:
            problems.append(f"{u.arm}/{u.instance}: {u.worker_runs} worker runs > W = {u.worker_run_cap}")
        if u.llm_call_cap is not None and u.llm_calls > u.llm_call_cap:
            problems.append(f"{u.arm}/{u.instance}: {u.llm_calls} LLM calls > cap {u.llm_call_cap}")
        # Review F6 (D1): W and the LLM-call cap bind; a campaign must not end on its trial budget.
        if u.trial_budget is not None:
            if u.llm_call_cap is not None and u.trial_budget < u.llm_call_cap:
                problems.append(f"{u.arm}/{u.instance}: trial budget {u.trial_budget} < LLM cap {u.llm_call_cap}")
            w_hit = u.worker_run_cap is not None and u.worker_runs >= u.worker_run_cap
            cap_hit = u.llm_call_cap is not None and u.llm_calls >= u.llm_call_cap
            if u.trials >= u.trial_budget and not (w_hit or cap_hit):
                problems.append(f"{u.arm}/{u.instance}: ended on the trial budget ({u.trials} trials) with "
                                f"{u.worker_runs}/{u.worker_run_cap} runs and {u.llm_calls}/{u.llm_call_cap} LLM calls")
    if problems:
        raise MatchingError("campaign matching failed: " + "; ".join(problems))
    totals = {}
    for arm, rows in sorted(by_arm.items()):
        totals[arm] = {"campaigns": len(rows), "instances": list(instance_sets[arm]),
                       "W": rows[0].worker_run_cap, "llm_call_cap": rows[0].llm_call_cap,
                       "information_set": rows[0].information_set,
                       "worker_runs": sum(u.worker_runs for u in rows), "llm_calls": sum(u.llm_calls for u in rows),
                       "controller_llm_calls": sum(u.controller_llm_calls for u in rows),
                       "sidecar_calls": sum(u.sidecar_calls for u in rows),
                       "prior_unavailable": sum(u.prior_unavailable for u in rows),
                       "descriptive": {"sidecar_compute_s": sum(u.sidecar_compute_s for u in rows),
                                       "controller_latency_s": sum(u.controller_latency_s for u in rows)}}
    for arm, rows in sorted(by_arm.items()):
        totals[arm]["ended_on"] = sorted({_ended_on(u) for u in rows})
    return {"matched": True, "checked": ["instances", "W", "llm_call_cap", "information_set",
                                         "worker_runs <= W", "llm_calls <= cap",
                                         "trial budget >= LLM cap and never binding"], "arms": totals}


def _ended_on(u: CampaignUsage) -> str:
    if u.worker_run_cap is not None and u.worker_runs >= u.worker_run_cap:
        return "W"
    if u.llm_call_cap is not None and u.llm_calls >= u.llm_call_cap:
        return "llm_cap"
    if u.trial_budget is not None and u.trials >= u.trial_budget:
        return "trial_budget"
    return "other"


def matching_report(arms: list[ArmDescriptor], usage: list[CampaignUsage] | None = None) -> dict:
    """Fail on any mismatch in the matched fields; with ``usage`` also on the online campaigns (H.7)."""
    if not arms:
        raise MatchingError("no arms")
    rows = [asdict(a) for a in arms]
    optional = [f for f in OPTIONAL_MATCHED_FIELDS if any(r[f] is not None for r in rows)]
    for r in rows:
        for f in OPTIONAL_MATCHED_FIELDS:
            if f not in optional:
                del r[f]
    fields = list(MATCHED_FIELDS) + optional
    mismatched = [f for f in fields if len({r[f] for r in rows}) > 1]
    if mismatched:
        detail = {f: sorted({str(r[f]) for r in rows}) for f in mismatched}
        raise MatchingError(f"arm matching failed on {mismatched}: {detail}")
    report = {"matched": True, "matched_fields": fields, "arms": rows}
    if usage is not None:
        report["campaigns"] = _usage_section(arms, usage)
    return report
