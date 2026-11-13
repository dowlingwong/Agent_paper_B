"""Track P Stage D: DAgger data aggregation (spec TRACK_P_POST_TRAINING.md §6.5, RUNBOOK C.2). ENGINEERING_ONLY.

AI-assisted (Claude). Synthetic environments only in this commit: no label table, no audit, no seed 7001-7010.

§6.5, one round per C.2 (R1-BX-D11: on 1-2 T1 nodes only):
1. run the loop with the current configurator on fresh training instances (``rollout``);
2. collect the states it visits and label the new ones with the expert (in C.2 the expert label is the audit of
   the newly proposed edit with the 10-seed protocol, label half 7001-7005; here an injected ``expert``);
3. aggregate with the existing labelled states (``AggregatedDataset``: a state is keyed by ``key``; a state already
   present keeps its first label and round, so nothing is relabelled or double-counted);
4. retrain from the Stage S recipe (``fit``: called on the whole aggregated set, never warm-started from the
   previous round's model, as "retrain from the Stage S recipe" says).

Reported per round: states visited, new states, aggregate size, and the disagreement between the configurator's
action and the expert-derived action on the visited states. The spec reads the proposer-behaviour shift as evidence
of a state-distribution shift, not of a policy-value gap (PLAN R1-WORDING-30OCT); this module only aggregates.

``OfflineBanditEnv`` (``r1/c3/env.py``) is a one-step environment: the configurator cannot change which proposals
appear, so on it a DAgger round adds no new states beyond the fresh instances themselves. ``offline_rollout`` adapts
it for the plumbing; the sequential effect needs an environment in which decisions change later states
(``SyntheticCampaign`` in the tests, the real loop in C.2).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Hashable, Iterable, Sequence

import numpy as np

LABEL_SEEDS = range(7001, 7011)          # C3 label and evaluation seeds: never used by a synthetic expert
EXAM_SEED_MIN = 9001                     # exam instances and audits (9001+, 9101-9104, 9201-9210)


def check_synthetic_seed(seed: int) -> int:
    """Refuse seeds reserved for C3 labels or for the exam; synthetic experts and environments use others."""
    if type(seed) is not int:
        raise ValueError("seed must be an int")
    if seed in LABEL_SEEDS or seed >= EXAM_SEED_MIN:
        raise ValueError(f"seed {seed} is reserved (C3 label seeds 7001-7010 or exam seeds 9001+)")
    return seed


@dataclass
class AggregatedDataset:
    rows: dict[Hashable, dict[str, Any]] = field(default_factory=dict)

    def add(self, states: Iterable[dict[str, Any]], expert: Callable[[dict[str, Any]], Any], round_: int) -> int:
        new = 0
        for s in states:
            k = s["key"]
            if k in self.rows:
                continue
            self.rows[k] = {"state": s, "label": expert(s), "round": round_}
            new += 1
        return new

    def __len__(self) -> int:
        return len(self.rows)

    def items(self) -> list[dict[str, Any]]:
        return [self.rows[k] for k in sorted(self.rows, key=repr)]


def run_dagger(initial_states: Sequence[dict[str, Any]], *, expert: Callable[[dict[str, Any]], Any],
               fit: Callable[[list[dict[str, Any]]], Any],
               rollout: Callable[[Any, int], list[dict[str, Any]]],
               act: Callable[[Any, dict[str, Any]], Any],
               expert_action: Callable[[dict[str, Any], Any], Any],
               rounds: int = 1) -> dict[str, Any]:
    """Round 0 fits on ``initial_states`` (expert-labelled); then ``rounds`` DAgger rounds (§6.5 steps 1-4)."""
    if type(rounds) is not int or rounds < 1:
        raise ValueError("rounds must be a positive integer")
    data = AggregatedDataset()
    data.add(initial_states, expert, 0)
    model = fit(data.items())
    history = [{"round": 0, "visited": 0, "new": len(data), "aggregate": len(data), "disagreement": None}]
    for r in range(1, rounds + 1):
        visited = rollout(model, r)
        # each new state is labelled once (the expert may be a costly audit); a state already in the aggregate
        # keeps its stored label, which the disagreement then uses
        new = data.add(visited, expert, r)
        disagree = (float(np.mean([act(model, s) != expert_action(s, data.rows[s["key"]]["label"]) for s in visited]))
                    if visited else None)
        model = fit(data.items())                     # retrain from the recipe on the aggregate
        history.append({"round": r, "visited": len(visited), "new": new, "aggregate": len(data),
                        "disagreement": disagree})
    return {"model": model, "history": history, "dataset": data}


def offline_rollout(env, act: Callable[[Any, dict[str, Any]], int], model, indices: Sequence[int]) -> list[dict[str, Any]]:
    """Visit ``indices`` of an ``OfflineBanditEnv`` with the configurator; one state per row (one-step episodes)."""
    states = []
    for i in indices:
        obs, info = env.reset(options={"index": int(i)})
        state = {"key": info["proposal_id"], "obs": obs, "info": info}
        b = int(act(model, state))
        _, reward, terminated, truncated, step_info = env.step(b)
        if not terminated or truncated:
            raise RuntimeError("OfflineBanditEnv episodes are one step")
        state.update(action=b, reward=reward, execute=step_info["execute"])
        states.append(state)
    return states
