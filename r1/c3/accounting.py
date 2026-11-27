"""Run and LLM-call accounting of online C3 campaigns (RUNBOOK Track H.6). ENGINEERING_ONLY; AI-assisted (Claude).

``campaign_usage`` reads one campaign's ledger and event stream and returns a
``r1.branch.matching.CampaignUsage`` for ``matching_report(..., usage=...)``:

* worker runs: trials whose worker ran (not control-plane skips, not
  precondition rejections), plus 2 r per verify;
* LLM calls: every manager proposal and revision of a non-deterministic manager
  (one call each, as the harness charges them) plus the controller's charged
  calls (``control_decision.llm_calls``: A4 queries, LLM self-control);
* sidecar forecasts: counted, compute seconds summed (compute only; not LLM
  calls); controller latency summed (descriptive).

D.3 gap G8 (pre-declaration revision 4, §5 "Run accounting", §3.1; G1/G6 design §2.2 "Charged-run counter"):

* **Replicate runs.**  Every candidate and incumbent replicate run of FIXR3 and EGATE is recorded in its trial's
  record under ``extra.control.replicates`` (``replicate_entries``: role, j, seed, success, charged) and counted by
  ``campaign_usage``: a ``charged`` entry adds one worker run; a reused incumbent run (``charged: false``) adds none
  and is counted as ``replicate_runs_reused``.  The trial's own run (candidate, j = 0) is the record's worker run
  and never appears in the list.
* **One W counter.**  ``ChargedRunCounter`` is the campaign's single counter of charged worker runs: trial runs,
  every verify run (2 r per verify, each charged singly) and every replicate run draw from it one run at a time; a
  step that needs n runs is refused before it starts when fewer than n are left (``require`` ->
  ``UnfundableStep``), and a charge beyond W is refused (``OverBudget``: a campaign over W is a STOP, §10).  A
  per-run hook (``on_charge``) sees every charge, so G1 can write its snapshots at w = 5, 10, 15, 20 exactly.
* **LLM calls issued again** after an infrastructure failure (R1-NO-TIMEOUT (1), §3.1 item 2) are the same call: the
  runner logs each re-issue as an ``llm_call_reissued`` event, only the call that returns creates its proposal
  event, and ``campaign_usage`` never counts a re-issue against the cap (``reissued_llm_calls``, descriptive).
* **Infrastructure failures** (§3.1, R1-CARD-SHARE (3)): ``classify_worker_failure`` says whether a failed run is
  the proposal's failure (charged, counted in the §10 failure rate) or an infrastructure failure (the chunk is
  attempted again whole; nothing of the lost attempt is charged; never an outcome, never a STOP).
  ``campaign_usage`` reads one attempt directory only, so nothing of a lost attempt can enter it.
* **``ended_on``** of the outcome table (§8): ``table_ended_on`` applies the pinned analysis's rule
  (``d3_analysis._check_ended_on``).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from r1.branch.matching import CampaignUsage

REPLICATE_ROLES = ("candidate", "incumbent")
LLM_CALL_REISSUED_EVENT = "llm_call_reissued"
CHARGE_KINDS = ("trial", "verify", "replicate")


def _jsonl(path: Path) -> list[dict]:
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def campaign_usage(records_path: Path | str, events_path: Path | str, *, arm: str, instance: str,
                   information_set: str, worker_run_cap: int | None, llm_call_cap: int | None,
                   manager_deterministic: bool, trial_budget: int | None = None) -> CampaignUsage:
    rows, events = _jsonl(Path(records_path)), _jsonl(Path(events_path))
    runs = replicate_runs = reused = 0
    for r in rows:
        mode = str(r.get("worker_mode") or "")
        ran = mode != "control_plane" and not mode.endswith("_precheck")
        if ran:
            runs += 1
        verify = (r.get("extra", {}).get("control") or {}).get("verify")
        if verify:
            runs += 2 * int(verify.get("r", len(verify.get("pairs") or [])))
        entries = replicate_entries(r)
        if entries and not ran:
            raise ValueError(f"trial {r.get('budget_index')}: replicate runs recorded on a trial whose worker "
                             "did not run")
        charged = sum(1 for e in entries if e["charged"])
        replicate_runs += charged
        reused += len(entries) - charged
    runs += replicate_runs
    manager_calls = 0
    if not manager_deterministic:
        manager_calls = sum(1 for e in events if e["event_type"] in ("proposal_created", "proposal_revised"))
        manager_calls += sum(1 for e in events if e["event_type"] == "proposal_rejected_inactive_key"
                             and not e["payload"].get("skipped"))
    decisions = [e["payload"] for e in events if e["event_type"] == "control_decision"]
    controller_calls = sum(int(d.get("llm_calls") or 0) for d in decisions)
    details = [d.get("detail") or {} for d in decisions]
    sidecar = [d for d in details if "sidecar_compute_s" in d]
    return CampaignUsage(arm=arm, instance=instance, information_set=information_set,
                         worker_run_cap=worker_run_cap, llm_call_cap=llm_call_cap, worker_runs=runs,
                         llm_calls=manager_calls + controller_calls, controller_llm_calls=controller_calls,
                         sidecar_calls=len(sidecar), sidecar_compute_s=float(sum(d["sidecar_compute_s"] for d in sidecar)),
                         prior_unavailable=sum(1 for e in events if e["event_type"] == "prior_unavailable"),
                         controller_latency_s=float(sum(float(d.get("latency_s") or 0.0) for d in details)),
                         trial_budget=trial_budget, trials=len(rows), replicate_runs=replicate_runs,
                         replicate_runs_reused=reused,
                         reissued_llm_calls=sum(1 for e in events if e["event_type"] == LLM_CALL_REISSUED_EVENT))


def replicate_entries(record: dict) -> list[dict]:
    """The validated ``extra.control.replicates`` of one trial record (G8); ``[]`` if absent.

    Each entry: ``{"role": "candidate" | "incumbent", "j": 0..9, "seed": int, "success": bool, "charged": bool}``
    (other keys, e.g. ``metric`` or ``config_sha256``, are kept).  Refused (fail closed): a malformed entry; a
    candidate entry with j = 0 (that run is the trial's own record); an uncharged candidate entry (only incumbent
    runs are reused); the same (role, j) twice.
    """
    from r1.c3.d3_analysis import MAX_REPLICATE_J  # §4.1: j = 1..9 (j = 0 is the instance seed); lazy import
    control = (record.get("extra") or {}).get("control") or {}
    entries = control.get("replicates")
    if entries is None:
        return []
    where = f"trial {record.get('budget_index')}"
    if not isinstance(entries, list):
        raise ValueError(f"{where}: extra.control.replicates must be a list")
    seen: set[tuple[str, int]] = set()
    for e in entries:
        if not isinstance(e, dict):
            raise ValueError(f"{where}: a replicate entry must be an object")
        role, j, seed = e.get("role"), e.get("j"), e.get("seed")
        if role not in REPLICATE_ROLES:
            raise ValueError(f"{where}: replicate role must be one of {REPLICATE_ROLES}")
        for name, value in (("j", j), ("seed", seed)):
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{where}: replicate {name} must be an integer")
        if not 0 <= j <= MAX_REPLICATE_J:
            raise ValueError(f"{where}: replicate j must lie in 0..{MAX_REPLICATE_J}")
        for name in ("success", "charged"):
            if not isinstance(e.get(name), bool):
                raise ValueError(f"{where}: replicate {name} must be a boolean")
        if role == "candidate" and j == 0:
            raise ValueError(f"{where}: the candidate's j = 0 run is the trial's own run, not a replicate")
        if role == "candidate" and not e["charged"]:
            raise ValueError(f"{where}: a candidate replicate is always charged (only incumbent runs are reused)")
        if (role, j) in seen:
            raise ValueError(f"{where}: replicate ({role}, j = {j}) recorded twice")
        seen.add((role, j))
    return entries


# ---------------------------------------------------------------------------
# The campaign's single W counter (G8; G1/G6 design §2.2)
# ---------------------------------------------------------------------------

class UnfundableStep(RuntimeError):
    """A step needs more charged runs than the campaign has left; it is refused before it starts."""


class OverBudget(RuntimeError):
    """A charge beyond W or a count above the cap: a STOP (pre-declaration §10); never caught to continue."""


@dataclass(frozen=True)
class ChargedRun:
    w: int                 # the charged-run count after this run (1..W)
    kind: str              # "trial" | "verify" | "replicate"
    role: str              # "candidate" | "incumbent"
    seed: int              # train seed = split seed of the run
    config_sha256: str
    success: bool
    j: int | None = None   # replicate index (0..9) where it applies
    metric: float | None = None
    seconds: float = 0.0


@dataclass
class ChargedRunCounter:
    """One campaign's charged worker runs; W binds, every run is charged singly (no block charges)."""

    W: int
    on_charge: Callable[[ChargedRun], Any] | None = None
    runs: list[ChargedRun] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.W, int) or isinstance(self.W, bool) or self.W < 1:
            raise ValueError("W must be an integer >= 1")
        if self.runs:
            raise ValueError("a counter starts empty (no resume, G1/G6 design §1)")

    @property
    def used(self) -> int:
        return len(self.runs)

    @property
    def left(self) -> int:
        return self.W - self.used

    def can_fund(self, n: int) -> bool:
        if not isinstance(n, int) or isinstance(n, bool) or n < 0:
            raise ValueError("a step needs a non-negative integer number of runs")
        return n <= self.left

    def require(self, n: int) -> None:
        """Refuse a step of ``n`` runs before it starts if fewer than ``n`` are left."""
        if not self.can_fund(n):
            raise UnfundableStep(f"step needs {n} charged runs, {self.left} left of W = {self.W}")

    def charge(self, *, kind: str, role: str, seed: int, config_sha256: str, success: bool, j: int | None = None,
               metric: float | None = None, seconds: float = 0.0) -> ChargedRun:
        if kind not in CHARGE_KINDS:
            raise ValueError(f"charge kind must be one of {CHARGE_KINDS}")
        if role not in REPLICATE_ROLES:
            raise ValueError(f"charge role must be one of {REPLICATE_ROLES}")
        if not isinstance(success, bool):
            raise ValueError("success must be a boolean")
        if j is not None:
            from r1.c3.d3_analysis import MAX_REPLICATE_J
            if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j <= MAX_REPLICATE_J:
                raise ValueError(f"replicate j must be None or an integer in 0..{MAX_REPLICATE_J}")
            if kind == "verify":
                raise ValueError("a verify run has no replicate index")
        elif kind == "replicate":
            raise ValueError("a replicate run names its j")
        if metric is not None and not math.isfinite(float(metric)):
            raise ValueError("a recorded metric must be finite (a non-finite result is a failed run)")
        if success and metric is None:
            raise ValueError("a successful run records its metric")
        if self.left < 1:
            raise OverBudget(f"charge beyond W = {self.W} (a campaign over W is a STOP, §10)")
        run = ChargedRun(w=self.used + 1, kind=kind, role=role, seed=int(seed), config_sha256=str(config_sha256),
                         success=success, j=j, metric=None if metric is None else float(metric),
                         seconds=max(float(seconds), 0.0))
        self.runs.append(run)
        if self.on_charge is not None:
            self.on_charge(run)
        return run

    def lookup(self, config_sha256: str, seed: int) -> ChargedRun | None:
        """The latest charged run of this configuration at this seed (for incumbent reuse; a failed run is
        returned too: runs are deterministic, so a failed (configuration, seed) run is never re-run)."""
        for run in reversed(self.runs):
            if run.config_sha256 == config_sha256 and run.seed == int(seed):
                return run
        return None


def table_ended_on(*, worker_runs: int, llm_calls: int, arm: str, unfundable: bool = False) -> str:
    """``ended_on`` of an outcome-table row (§8), by the pinned analysis's rule (``d3_analysis._check_ended_on``).

    ``worker_runs`` iff runs = W; else ``llm_call_cap`` iff calls = the cap; else ``no_fundable_candidate`` for
    FIXR3/EGATE whose next required step could not be funded.  Runs above W or calls above the cap are a STOP
    (``OverBudget``); a campaign that matches none of these has not ended (refused).
    """
    from r1.c3 import d3_analysis as D3
    if worker_runs > D3.W or llm_calls > D3.LLM_CALL_CAP:
        raise OverBudget("a campaign over W or over the LLM-call cap is a STOP (§10)")
    if worker_runs == D3.W:
        return "worker_runs"
    if llm_calls == D3.LLM_CALL_CAP:
        return "llm_call_cap"
    if unfundable and arm in D3.REPLICATE_ARMS:
        return "no_fundable_candidate"
    raise ValueError("the campaign has not ended: below W, below the cap and no unfundable step of FIXR3/EGATE")


# ---------------------------------------------------------------------------
# Infrastructure failure or the proposal's failure (§3.1; R1-CARD-SHARE (3)-(4); R1-NO-TIMEOUT (2))
# ---------------------------------------------------------------------------

# §13 item 31 (open author item).  Built and recommended: the row's literal condition -- a per-run budget hit or an
# out-of-memory is an infrastructure failure only with another compute process on the job's CARD; CPU sharing alone
# does not count.  True implements the alternative (draft row R1-D3-R4-CPUSHARE) and then needs the host's other
# compute processes recorded at start and end (``host_other_processes``).
CPU_SHARING_IS_INFRASTRUCTURE = False
ALWAYS_INFRASTRUCTURE = ("host_kill", "reset", "connection_lost", "walltime", "no_progress", "server_lost")
CONDITIONAL_INFRASTRUCTURE = ("budget_hit", "oom")
PROPOSAL_FAILURES = ("invalid_config", "admitted_runtime_error")


def _count(value, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name} must be a recorded non-negative integer (R1-CARD-SHARE (4)); unknown is refused")
    return value


def classify_worker_failure(cause: str, *, card_other_processes: tuple[int, int] | None = None,
                            host_other_processes: tuple[int, int] | None = None,
                            cpu_sharing_is_infrastructure: bool = CPU_SHARING_IS_INFRASTRUCTURE) -> str:
    """``"infrastructure"`` (sealed, recorded, the chunk attempted again whole, nothing charged, never an outcome)
    or ``"proposal"`` (charged, counted in the §10 failure rate).

    ``card_other_processes`` = (count at job start, count at job end) of the other compute processes on the job's
    card, as R1-CARD-SHARE (4) records them; required for ``budget_hit`` / ``oom``, and an unknown count is refused
    (fail closed: the scene is kept for a decision, never guessed).  An unknown cause is refused.  A worker
    ``runtime_error`` outside the two pre-admitted classes is a STOP (§10) and is not classified here.
    """
    if cause in ALWAYS_INFRASTRUCTURE:
        return "infrastructure"
    if cause in PROPOSAL_FAILURES:
        return "proposal"
    if cause not in CONDITIONAL_INFRASTRUCTURE:
        raise ValueError(f"unknown failure cause {cause!r}")
    if card_other_processes is None or len(card_other_processes) != 2:
        raise ValueError("a budget hit or out-of-memory needs the card's other compute processes at start and end")
    if any(_count(v, "card_other_processes") > 0 for v in card_other_processes):
        return "infrastructure"
    if cpu_sharing_is_infrastructure:
        if host_other_processes is None or len(host_other_processes) != 2:
            raise ValueError("with CPU sharing counted, the host's other compute processes at start and end are "
                             "required")
        if any(_count(v, "host_other_processes") > 0 for v in host_other_processes):
            return "infrastructure"
    return "proposal"
