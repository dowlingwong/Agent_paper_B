"""G1 replicate-arm campaign loop for FIXR3 and EGATE (design revision 6c). ENGINEERING code.

The pinned harness cannot run one configuration several times from a ``Controller.decide``,
so a replicate arm is executed by this G1-owned loop: the engine decides E2, G1 owns E1,
the manager calls, the single W counter, the exact-w snapshots and the records.  It never
calls ``run_real_campaign`` and never resumes an existing campaign directory.

Authority: ``docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md``
(revision 6c-3, ACCEPTED FOR CODE).  No evidence, label, evaluation or sealed read happens here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from r1.c3.accounting import ChargedRunCounter, UnfundableStep, table_ended_on
from r1.c3.d3.snapshots import (
    SnapshotRecorder,
    config_sha256,
    sha256_json,
)
from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402

REPLICATE_ARMS = ("FIXR3", "EGATE")
PENDING_ACTIONS = {"FIXR3": "fixr3_step", "EGATE": "egate_pair"}


class ReplicateStop(RuntimeError):
    """A pre-declared STOP or a parity failure of the replicate route."""


@dataclass(frozen=True)
class RunAttempt:
    """One worker call of a replicate step (the side record of design §5)."""

    step: int
    role: str
    j: int
    seed: int
    config_sha256: str
    success: bool
    metric: float | None
    seconds: float
    cause: str | None = None
    card_other_processes: tuple[int, int] | None = None
    host_other_processes: tuple[int, int] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.step, "role": self.role, "j": self.j, "seed": self.seed,
            "config_sha256": self.config_sha256, "success": self.success,
            "metric": self.metric, "seconds": self.seconds, "cause": self.cause,
        }


def projection(engine: Any, counter: ChargedRunCounter) -> dict[str, Any]:
    """The documented ordered projection hashed into ``controller_state_sha256``.

    It contains only fields the engine and the counter expose; no object id, ``repr``,
    timestamp or set iteration enters the hash.
    """
    arm = str(getattr(engine, "arm", ""))
    common = {
        "arm": arm,
        "version": str(getattr(engine, "version", "")),
        "instance_seed": int(getattr(engine, "instance_seed")),
        "steps": int(getattr(engine, "steps", 0)),
        "incumbent": getattr(engine, "incumbent", None),
        "seeds": [int(s) for s in getattr(engine, "seeds", ())],
    }
    if arm == "FIXR3":
        metrics = getattr(engine, "incumbent_metrics", None)
        return {**common, "incumbent_metrics": None if metrics is None else [float(x) for x in metrics],
                "zero_variance_cases": int(getattr(engine, "zero_variance_cases", 0))}
    if arm == "EGATE":
        incumbent = getattr(engine, "incumbent", None)
        runs = []
        for j, seed in enumerate(engine.seeds):
            run = counter.lookup(incumbent, seed) if incumbent is not None else None
            runs.append(None if run is None else {
                "j": int(j), "seed": int(seed), "success": bool(run.success),
                "metric": run.metric, "charged": True,
            })
        return {**common, "incumbent_runs": runs}
    raise ReplicateStop(f"unknown replicate arm {arm!r}; refusing a fallback projection")


def _pending(attempts: list[RunAttempt], step: int, *, maximize: bool = True) -> dict[str, Any]:
    candidate = [a.metric for a in attempts if a.step == step and a.role == "candidate" and a.success]
    incumbent = [a.metric for a in attempts if a.step == step and a.role == "incumbent" and a.success]
    sign = 1.0 if maximize else -1.0
    diffs = [sign * (float(c) - float(i)) for c, i in zip(candidate, incumbent)]
    last = [a for a in attempts if a.step == step]
    return {"step": int(step), "j": last[-1].j if last else 0,
            "candidate_metrics": candidate, "incumbent_metrics": incumbent, "diffs": diffs}


@dataclass
class ReplicateUnit:
    """The adapter-supplied part of one replicate campaign.

    ``propose(step_index, incumbent_config, llm_calls)`` makes one manager proposal call
    and returns a proposal object (or ``None`` when the manager stream is exhausted).
    ``validate(proposal)`` returns ``(config_contents, config_sha256)`` for a valid
    proposal, or ``None`` for a control-plane rejection (charged no worker run).
    ``run_trial(proposal, config, seed, j, budget_index)`` runs one configuration and
    returns ``(success, metric, seconds)``; a raised exception is converted by G1 to a
    failed ``RunOutcome`` (the engine still charges it).
    """

    engine: Any
    propose: Callable[[int, dict[str, Any], int], Any]
    validate: Callable[[Any], tuple[dict[str, Any], str] | None]
    run_trial: Callable[[Any, Mapping[str, Any], int, int, int], tuple[bool, float | None, float]]
    start_config: dict[str, Any]
    restore_incumbent: Callable[[Mapping[str, Any]], None] | None = None
    node_spec: Any = None
    memory_context: Any = None


def run_replicate_campaign(*, instance_id: str, repetition: int, unit: ReplicateUnit,
                           recorder: SnapshotRecorder, stage: str = "", node: str = "",
                           W: int = 20, llm_cap: int = 80) -> dict[str, Any]:
    """Run one replicate campaign; write snapshots and return its records.

    The caller owns the campaign directory and the remaining record files.  Every worker
    call is charged exactly once by the engine through ``counter.charge``; G1 reassigns the
    frozen ``ComputeBudget`` before that charge.  Any mismatch is a STOP.
    """
    arm = str(getattr(unit.engine, "arm", ""))
    if arm not in REPLICATE_ARMS:
        raise ReplicateStop(f"not a replicate arm: {arm!r}")
    if int(W) != 20 or int(llm_cap) != 80:
        raise ReplicateStop("a D.3 campaign binds W = 20 and the LLM-call cap = 80")
    counter = ChargedRunCounter(W=W, on_charge=recorder.on_charge)
    if recorder.start_config is not None and recorder.start_config != dict(unit.start_config):
        raise ReplicateStop("the recorder's start config differs from the replicate unit's")
    recorder.start_config = dict(unit.start_config)
    budget_holder = {"value": ComputeBudget(max_worker_runs=W, max_llm_calls=llm_cap)}
    incumbent_config = dict(unit.start_config)
    config_by_sha: dict[str, tuple[Any, dict[str, Any]]] = {
        config_sha256(incumbent_config): (None, dict(incumbent_config))
    }
    attempts: list[RunAttempt] = []
    steps: list[dict[str, Any]] = []
    last_kept: int | None = None
    step_index = 0
    restore_next = False
    ended_on: str | None = None
    proposal_calls = 0

    while counter.left > 0:
        if int(budget_holder["value"].llm_calls) >= llm_cap:
            ended_on = "llm_call_cap"
            break
        budget_holder["value"] = budget_holder["value"].consume_llm_call()
        proposal_calls += 1
        proposal = unit.propose(step_index, dict(incumbent_config),
                                int(budget_holder["value"].llm_calls))
        if proposal is None:
            if int(budget_holder["value"].llm_calls) >= llm_cap:
                ended_on = "llm_call_cap"
                break
            raise ReplicateStop("the manager returned no proposal before the LLM-call cap")
        validated = unit.validate(proposal)
        if validated is None:
            continue  # a control-plane rejection costs its LLM call and no worker run
        candidate_config, candidate_sha = validated
        if config_sha256(candidate_config) != candidate_sha:
            raise ReplicateStop("the adapter's config_sha256 does not hash its config contents")
        config_by_sha[candidate_sha] = (proposal, dict(candidate_config))

        recorder.begin_step(
            trial_id=f"{instance_id}__t{step_index}",
            incumbent_config=incumbent_config,
            start_config=unit.start_config,
            state=projection(unit.engine, counter),
            last_kept_trial_index=last_kept,
            llm_calls=int(budget_holder["value"].llm_calls),
            step_index=step_index,
            pending_action=PENDING_ACTIONS[arm],
        )

        restored = False

        def run_one(*, role: str, config_sha256: str, seed: int, j: int) -> Any:
            nonlocal restored
            from r1.c3.d3_replicate import RunOutcome

            if restore_next and not restored and unit.restore_incumbent is not None:
                unit.restore_incumbent(incumbent_config)
                restored = True
            if role == "candidate":
                found = config_by_sha.get(config_sha256)
                if found is None:
                    raise ReplicateStop(f"the engine asked for an unknown config {config_sha256}")
                proposal_obj, config = found
            else:
                proposal_obj, config = None, dict(incumbent_config)
            budget_holder["value"] = budget_holder["value"].consume_worker_run(0.0)
            try:
                ok, metric, seconds = unit.run_trial(proposal_obj, config, int(seed), int(j),
                                                     counter.used + 1)
                attempt = RunAttempt(step_index, role, int(j), int(seed), config_sha256,
                                     bool(ok), None if metric is None else float(metric),
                                     float(seconds or 0.0))
            except Exception as exc:  # noqa: BLE001 - a worker failure is a failed RunOutcome
                attempt = RunAttempt(step_index, role, int(j), int(seed), config_sha256,
                                     False, None, 0.0, cause=f"{type(exc).__name__}: {exc}"[:300])
            attempts.append(attempt)
            recorder.set_pending(**_pending(attempts, step_index,
                                            maximize=bool(getattr(unit.engine, "maximize", True))))
            if not attempt.success:
                return RunOutcome(False)
            return RunOutcome(True, attempt.metric, attempt.seconds)

        try:
            result = unit.engine.step(candidate_sha, run_one, counter)
        except UnfundableStep:
            ended_on = "no_fundable_candidate"
            break

        budget = budget_holder["value"]
        if counter.used != int(budget.worker_runs):
            raise ReplicateStop(
                f"charged-run parity failure after step {step_index}: counter {counter.used}, "
                f"budget {budget.worker_runs}"
            )
        kept = result.decision == "kept"
        if kept:
            incumbent_config = dict(candidate_config)
            last_kept = step_index
        restore_next = not kept
        steps.append({
            "step": step_index, "trial_id": f"{instance_id}__t{step_index}",
            "decision": result.decision, "runs_charged": int(result.runs_charged),
            "replicates": list(result.replicates), "display_metric": result.display_metric,
            "detail": dict(result.detail or {}),
            "zero_variance_cases": int(getattr(unit.engine, "zero_variance_cases", 0)),
        })
        step_index += 1

    if proposal_calls != int(budget_holder["value"].llm_calls):
        raise ReplicateStop(
            f"LLM-call parity failure: {proposal_calls} proposal calls, "
            f"budget {budget_holder['value'].llm_calls}"
        )
    if ended_on is None:
        if counter.used >= W:
            ended_on = table_ended_on(worker_runs=counter.used, llm_calls=int(budget_holder["value"].llm_calls),
                                      arm=arm, unfundable=False)
        elif int(budget_holder["value"].llm_calls) >= llm_cap:
            ended_on = table_ended_on(worker_runs=counter.used, llm_calls=int(budget_holder["value"].llm_calls),
                                      arm=arm, unfundable=False)
        else:
            raise ReplicateStop("the replicate campaign ended without a declared end condition")

    final_trial = f"{instance_id}__t{step_index - 1}" if step_index else None
    final_sha = recorder.write_final_from_state(
        w_final=counter.used, ended_on=ended_on, incumbent_config=incumbent_config,
        state=projection(unit.engine, counter), last_kept_trial_index=last_kept,
        llm_calls=int(budget_holder["value"].llm_calls), trial_id=final_trial,
        step_index=step_index - 1 if step_index else None,
    )
    return {
        "schema": "r1_d3_replicate_campaign/v1",
        "campaign_id": instance_id, "stage": stage, "arm": arm, "node": node,
        "repetition": int(repetition), "worker_runs": counter.used,
        "llm_calls": int(budget_holder["value"].llm_calls), "proposal_calls": proposal_calls,
        "ended_on": ended_on, "steps": steps, "attempts": [a.as_dict() for a in attempts],
        "snapshots": recorder.snapshot_hashes(), "final_sha256": final_sha,
        "incumbent_config_sha256": config_sha256(incumbent_config),
    }
