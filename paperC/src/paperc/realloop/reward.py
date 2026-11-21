"""Reward and attribution of run outcomes for real-loop RL (design note §3, RL-INFRA). ENGINEERING_ONLY.

The isolated harness classifies every run as ``ok``, ``divergent`` or ``infrastructure_failure``
(``autoresearch.trackg.outcome``). Its campaign reruns an infrastructure failure up to ``max_infra_reruns`` times
without a manager call and without registering the code state as evaluated, and ``isolation.py`` records the limit:
"its output can contain an infrastructure log pattern, which makes the run an infrastructure_failure (rerun, not
registered as evaluated) -- an RL reward must not treat that class as neutral without the author's decision". A
policy (or a proposer it steers) that learns to make edited runs print such a pattern gets free rerolls and dodges bad
outcomes; one that learns to cause a host-looking fault gets its bad episodes deleted.

``attribute`` maps one run attempt to one of:

* ``ok`` / ``proposal_failure`` — in-episode outcomes; a proposal failure consumed its runs, gives no gain, and the
  code state counts as evaluated (the harness's ``divergent`` — incl. measured ``timeout`` and ``timeout_repeated``
  — an OOM kill, and the reattributed infrastructure cases below);
* ``truncate_host`` — the episode is truncated with reason ``host`` (addendum 19 Nov §C);
* ``stop`` — a protocol STOP (a provisional timeout has no place in RL).

**Host evidence** (``HostEvidence``) is restricted to faults the job cannot cause: a GPU Xid on the hardware
allow-list (``HARDWARE_XIDS``; application-triggerable Xids such as 13, 31 and 43 are not evidence), a preemption by
scheduler priority (not a hold or remove for exceeding a resource request), a node drain, and a full filesystem the
worker cannot write. It comes from the parent or the scheduler, never from the worker's output. It is checked first,
so a preemption that surfaces as a measured timeout truncates. Residual risk: a job-caused fault that the scheduler
or driver reports as one of these is truncated; the truncation-rate checks (``truncation_check`` and the trainer's
level) bound how much that can matter.

RL-INFRA option A (``"host_evidence"``): without host evidence, a launch error truncates (nothing of the proposal
ran) and every worker-producible infrastructure signal (log pattern, kill, missing exit status — the last is the
parent's status and listed conservatively) is a proposal failure, unless the code is trusted (the deployed start
configuration only; an incumbent is policy-chosen edited code). Option B (``"control_rerun"``): an ambiguous failure
is resolved by rerunning the **start configuration** in the same slot: it truncates only if the control fails as
infrastructure too. "Neutral" (rerun for free) is refused: it needs an author row.
"""
from __future__ import annotations

from dataclasses import dataclass, field

OK, DIVERGENT, INFRA = "ok", "divergent", "infrastructure_failure"
ATTRIBUTIONS = ("ok", "proposal_failure", "truncate_host", "stop")
INFRA_POLICIES = ("host_evidence", "control_rerun")
WORKER_PRODUCIBLE = ("infrastructure_log_pattern", "killed", "no_exit_status")
HARDWARE_XIDS = frozenset({48, 63, 64, 74, 79, 92, 94, 95})


class RewardError(ValueError):
    """A refused configuration or an inconsistent record."""


@dataclass(frozen=True)
class HostEvidence:
    """Parent- or scheduler-side facts about a run, restricted to faults the job cannot cause."""

    xid: int | None = None                  # a GPU Xid reported by the driver (only HARDWARE_XIDS count)
    preempted_by_priority: bool = False     # a scheduler preemption by priority (not a resource-limit hold/remove)
    node_drain: bool = False
    disk_full_unwritable_fs: bool = False   # a full filesystem the worker cannot write

    def any(self) -> bool:
        return (self.xid in HARDWARE_XIDS) or self.preempted_by_priority or self.node_drain or \
            self.disk_full_unwritable_fs


@dataclass(frozen=True)
class RunRecord:
    """One run attempt as the controller sees it (fields of the harness run record)."""

    kind: str                         # ok | divergent | infrastructure_failure
    reason: str = ""
    value: float | None = None        # the run's metric (ok only)
    runs_consumed: int = 1
    trusted_code: bool = False        # True only for the deployed start configuration
    host: HostEvidence = HostEvidence()
    prior_attempts: tuple = field(default=())   # attempts the runner made before this one (should be empty, §8)

    def __post_init__(self):
        if (self.kind == OK) != (self.value is not None):
            raise RewardError("only an ok run carries a value, and it must")
        if self.runs_consumed < 1:
            raise RewardError("a run consumes at least one run")


def attribute(run: RunRecord, *, policy: str, control: RunRecord | None = None) -> str:
    """One of ``ATTRIBUTIONS`` for one attempt (module docstring)."""
    if policy == "neutral":
        raise RewardError("a neutral infrastructure class needs an author row (isolation.py limits; RL-INFRA)")
    if policy not in INFRA_POLICIES:
        raise RewardError(f"unknown RL-INFRA policy {policy!r}")
    if run.kind not in (OK, DIVERGENT, INFRA):
        raise RewardError(f"unknown run kind {run.kind!r}")
    if run.kind == INFRA and run.reason == "timeout":
        return "stop"                  # provisional timeouts belong to the census, never to RL
    if run.kind != OK and run.host.any():
        return "truncate_host"
    if run.kind == OK:
        return "ok"
    if run.kind == DIVERGENT:
        return "proposal_failure"
    if run.reason == "launch_error" or run.trusted_code:
        return "truncate_host"
    if run.reason not in WORKER_PRODUCIBLE:
        raise RewardError(f"unclassified infrastructure reason {run.reason!r}")
    if policy == "host_evidence":
        return "proposal_failure"
    if control is None:
        raise RewardError("RL-INFRA B needs the control rerun of the start configuration")
    if not control.trusted_code:
        raise RewardError("the control rerun must be of the trusted start configuration")
    return "truncate_host" if control.kind == INFRA else "proposal_failure"


def attribute_attempts(run: RunRecord, *, policy: str, control: RunRecord | None = None) -> tuple[str, int]:
    """The attribution of an ``execute`` and the runs it consumed, all attempts included: the **first** attempt
    decides (a reroll never replaces it), and every attempt's runs are charged."""
    attempts = list(run.prior_attempts) + [RunRecord(run.kind, run.reason, run.value, run.runs_consumed,
                                                     run.trusted_code, run.host)]
    first = attempts[0]
    if first.prior_attempts:
        raise RewardError("nested prior attempts")
    return attribute(first, policy=policy, control=control), sum(a.runs_consumed for a in attempts)


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
    more than ``level`` (the declared imbalance level, addendum 19 Nov §C); a spread equal to the level passes."""
    rates = {}
    for arm, (trunc, n) in counts.items():
        if n <= 0 or not 0 <= trunc <= n:
            raise RewardError(f"arm {arm}: bad counts {trunc}/{n}")
        rates[arm] = trunc / n
    spread = max(rates.values()) - min(rates.values()) if rates else 0.0
    if spread > level:
        raise RewardError(f"STOP: truncation rates differ by {spread:.3f} > {level} across arms {rates}")
    return {"rates": rates, "spread": spread, "level": level}
