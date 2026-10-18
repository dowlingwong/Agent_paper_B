"""Reliability event schema copied from ``autoresearch_harness`` (runbook §9).

Only the stdlib-only modules are copied: the event envelope with visibility
classes (``events``) and the adjudication vocabulary (``adjudication``).  The
upstream factory ``ReliabilityEvent.create`` draws ``uuid4`` ids and wall-clock
times; Paper B's ledger (``control.governance``) constructs events directly with
deterministic ids instead.  ``UPSTREAM_COMMIT`` pins the copy.
"""

from .adjudication import AdjudicationRecord, AdjudicationStatus  # noqa: F401
from .events import (  # noqa: F401
    SCHEMA_VERSION, EventVisibility, ReliabilityEvent, ReliabilityEventType,
)

UPSTREAM_REPOSITORY = "github.com/dowlingwong/autoresearch_harness"
UPSTREAM_COMMIT = "da8dcbd1a9821b852173cbe4805dbd1304ba1d17"
