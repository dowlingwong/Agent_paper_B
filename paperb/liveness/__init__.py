"""Liveness check (D28/P4, criterion 2 revised 14 Oct), gate (P5) and the runner.

The criteria are PLAN §10 D28 and D28 (revised criterion 2): a node is live
under a given manager and memory mode when, over its campaign ledgers,

1. at least one keep happened after trial 1;
2. at least 50 % of evaluated trials have an active-key configuration that
   differs from the incumbent's and from every configuration evaluated earlier
   (including before a resume; skipped trials are not evaluated);
3. the invalid rate is below 30 %.

ENGINEERING_ONLY: a liveness pass is a precondition for LLM-backed
collection, never a result.
"""
from r1.liveness.check import (
    ACTIVE_NOVELTY_FRACTION,
    CRITERIA,
    INVALID_RATE_MAX,
    NOVELTY_MIN,
    evaluate_ledger_paths,
    evaluate_records,
    evaluate_segments,
    write_reports,
)
from r1.liveness.gate import load_liveness_manifest, require_live
from r1.liveness.novelty import load_segments

__all__ = [
    "ACTIVE_NOVELTY_FRACTION",
    "CRITERIA",
    "INVALID_RATE_MAX",
    "NOVELTY_MIN",
    "evaluate_ledger_paths",
    "evaluate_records",
    "evaluate_segments",
    "load_segments",
    "write_reports",
    "load_liveness_manifest",
    "require_live",
]
