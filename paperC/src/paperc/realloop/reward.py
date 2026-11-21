"""Reward and attribution of run outcomes for real-loop RL (design note §3, RL-INFRA). ENGINEERING_ONLY.

The isolated harness classifies every run as ``ok``, ``divergent`` or ``infrastructure_failure``
(``autoresearch.trackg.outcome``). Its campaign reruns an infrastructure failure without registering the code state
as evaluated, and ``isolation.py`` records the limit: "its output can contain an infrastructure log pattern, which
makes the run an infrastructure_failure (rerun, not registered as evaluated) -- an RL reward must not treat that
class as neutral without the author's decision". A policy (or a proposer it steers) that learns to make edited runs
print such a pattern would get free reruns and dodge bad outcomes.

``attribute`` maps one run to one of:

* ``ok`` / ``proposal_failure`` — in-episode outcomes; a proposal failure consumed its runs, gives no gain, and the
  code state counts as evaluated (the harness's ``divergent``, plus the reattributed infrastructure cases below);
* ``truncate`` — the episode is truncated (addendum 19 Nov §C: never treated as complete, rates per arm, an
  imbalance beyond the declared level is a STOP);
* ``stop`` — a protocol STOP (a provisional timeout has no place in RL: only measured timeouts are used there).

RL-INFRA option A (``"host_evidence"``): an infrastructure failure truncates only with evidence the worker cannot
produce — a launch error, or parent-side host evidence (scheduler eviction or preemption, a GPU Xid, a node drain, a
host disk-full seen by the parent) — or on an unedited code state (the baseline or the incumbent); otherwise a log
pattern, a kill or a missing exit status on an edited code state is a proposal failure. Option B
(``"control_rerun"``): an ambiguous case is resolved by rerunning the incumbent in the same slot: it truncates only
if the control fails as infrastructure too. "Neutral" (rerun for free) is refused: it needs an author row.
"""
from __future__ import annotations

from dataclasses import dataclass

OK, DIVERGENT, INFRA = "ok", "divergent", "infrastructure_failure"
ATTRIBUTIONS = ("ok", "proposal_failure", "truncate", "stop")
INFRA_POLICIES = ("host_evidence", "control_rerun")
WORKER_PRODUCIBLE = ("infrastructure_log_pattern", "killed", "no_exit_status")


class RewardError(ValueError):
    """A refused configuration or an inconsistent record."""


@dataclass(frozen=True)
class HostEvidence:
    """Parent- or scheduler-side facts about a run; none of them can be written by the worker."""

    scheduler_eviction: bool = False
    gpu_xid: bool = False
    node_drain: bool = False
    host_disk_full: bool = False

    def any(self) -> bool:
        return self.scheduler_eviction or self.gpu_xid or self.node_drain or self.host_disk_full


@dataclass(frozen=True)
class RunRecord:
    """One run as the controller sees it (fields of the harness run record)."""

    kind: str                         # ok | divergent | infrastructure_failure
    reason: str = ""
    value: float | None = None        # the run's metric (ok only)
    runs_consumed: int = 1
    edited: bool = True               # False for the baseline or a rerun of the incumbent
    host: HostEvidence = HostEvidence()


def attribute(run: RunRecord, *, policy: str, control: RunRecord | None = None) -> str:
    """One of ``ATTRIBUTIONS`` (module docstring)."""
    if policy == "neutral":
        raise RewardError("a neutral infrastructure class needs an author row (isolation.py limits; RL-INFRA)")
    if policy not in INFRA_POLICIES:
        raise RewardError(f"unknown RL-INFRA policy {policy!r}")
    if run.kind == OK:
        if run.value is None:
            raise RewardError("an ok run carries a value")
        return "ok"
    if run.kind == DIVERGENT:
        return "proposal_failure"
    if run.kind != INFRA:
        raise RewardError(f"unknown run kind {run.kind!r}")
    if run.reason == "timeout":
        return "stop"                  # provisional timeouts belong to the census, never to RL
    if run.reason == "launch_error" or run.host.any() or not run.edited:
        return "truncate"
    if run.reason not in WORKER_PRODUCIBLE:
        raise RewardError(f"unclassified infrastructure reason {run.reason!r}")
    if policy == "host_evidence":
        return "proposal_failure"
    if control is None:
        raise RewardError("RL-INFRA B needs the control rerun of the incumbent")
    if control.edited:
        raise RewardError("the control rerun must be of the unedited incumbent")
    return "truncate" if control.kind == INFRA else "proposal_failure"


@dataclass(frozen=True)
class RewardSpec:
    """Reward in sigma_node units: per executing step -g x runs; at the end of a terminated episode the audited
    terminal increment (y_terminal - y_start) / sigma_node. g is the declared price of one worker run."""

    g: float
    sigma_node: float

    def __post_init__(self):
        if not (self.g >= 0 and self.sigma_node > 0):
            raise RewardError("g must be >= 0 and sigma_node > 0")

    def step(self, attribution: str, runs_consumed: int) -> float:
        if attribution not in ("ok", "proposal_failure"):
            raise RewardError(f"no step reward for {attribution!r} (truncation and STOP end the episode)")
        return -self.g * runs_consumed

    def terminal(self, y_terminal: float, y_start: float) -> float:
        return (y_terminal - y_start) / self.sigma_node


def truncation_check(counts: dict[str, tuple[int, int]], level: float) -> dict:
    """counts: {arm: (truncated, episodes)}. STOP (``RewardError``) when the truncation rates of two arms differ by
    more than ``level`` (the declared imbalance level, addendum 19 Nov §C)."""
    rates = {}
    for arm, (trunc, n) in counts.items():
        if n <= 0 or not 0 <= trunc <= n:
            raise RewardError(f"arm {arm}: bad counts {trunc}/{n}")
        rates[arm] = trunc / n
    spread = max(rates.values()) - min(rates.values()) if rates else 0.0
    if spread > level:
        raise RewardError(f"STOP: truncation rates differ by {spread:.3f} > {level} across arms {rates}")
    return {"rates": rates, "spread": spread, "level": level}
