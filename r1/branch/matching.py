"""Information / capacity / tuning parity across arms (``matching_report``; PLAN §5 'Matching').

Ported from the legacy ``timing.py::matching_report`` and generalised: every
arm declares a descriptor; the report fails on any mismatch in the matched
fields.  Arms that are allowed to differ (the model family, by design) are not
matched fields.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

MATCHED_FIELDS = ("information_set", "spending_rule", "intervention_cap", "compute_budget",
                  "llm_call_cap", "tuning_budget", "dev_instances")


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


def matching_report(arms: list[ArmDescriptor]) -> dict:
    if not arms:
        raise MatchingError("no arms")
    rows = [asdict(a) for a in arms]
    mismatched = [f for f in MATCHED_FIELDS if len({r[f] for r in rows}) > 1]
    if mismatched:
        detail = {f: sorted({str(r[f]) for r in rows}) for f in mismatched}
        raise MatchingError(f"arm matching failed on {mismatched}: {detail}")
    return {"matched": True, "matched_fields": list(MATCHED_FIELDS), "arms": rows}
