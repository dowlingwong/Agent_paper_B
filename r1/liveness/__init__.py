"""Liveness check (D28/P4), gate (P5) and the collector-path runner (P4).

The criteria are exactly PLAN §10 D28: a node is live under a given manager
and memory mode when, over its campaign ledgers,

1. at least one keep happened after trial 1;
2. at least 50 % of trials have a metric different from the incumbent's;
3. the invalid rate is below 30 %.

ENGINEERING_ONLY: a liveness pass is a precondition for LLM-backed
collection, never a result.
"""
from r1.liveness.check import (
    CRITERIA,
    METRIC_DIFF_MIN,
    INVALID_RATE_MAX,
    evaluate_ledger_paths,
    evaluate_records,
    write_reports,
)
from r1.liveness.gate import load_liveness_manifest, require_live

__all__ = [
    "CRITERIA",
    "METRIC_DIFF_MIN",
    "INVALID_RATE_MAX",
    "evaluate_ledger_paths",
    "evaluate_records",
    "write_reports",
    "load_liveness_manifest",
    "require_live",
]
