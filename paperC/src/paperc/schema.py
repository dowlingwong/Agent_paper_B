"""SPT transition record ``spt_transition/v1`` and its mechanical checks (build runbook P1; plan §4.1–§4.2).

AI-assisted (Claude, chat session, 15 Nov 2026). ENGINEERING_ONLY.

One row per decision point of one trajectory. A trajectory is a root campaign (``branch_path == []``) or one
continuation of a fork (``branch_path`` names the fork arms taken from the root, e.g. ``["f3:execute:r1"]``).
Field names follow Track S ``r1/tracks/schema.py`` (branch ``trackS-ops-20261030`` @ ``fab88fc``) where the meaning is
the same: ``immediate_measured``, ``p_select``, ``channel_arms``, the ``Forecast`` tuple (pi, mu, tau, sigma, v_star,
m_hat), ``y_start``, ``y_terminal``, ``y_terminal_per_seed``, ``audit_seeds``, ``Provenance``. This module is a port of
those definitions, not an import.

Units: metric quantities are in the node's raw declared metric units, as in Track S. ``sigma_node`` is recorded so
that analyses can standardise.

Epochs and actions (plan §3.3, extended by R1-PAPERC-REFRAME for evaluation control):

* ``E1``: ``execute`` / ``skip``;
* ``E2``: ``keep`` / ``discard``;
* ``verify``: ``verify`` (re-measure the candidate with extra seeds) / ``no_verify``;
* ``reaudit``: ``reaudit`` (re-measure the incumbent) / ``no_reaudit``;
* ``final``: ``select`` (the final incumbent choice at campaign end; ``Action.selected`` names the configuration).

Deliberately deferred fields of plan §4.1 (none): every group of the plan's table is present. ``State.history_ref``
and ``State.proposal_ref`` are pointers (paths or content hashes) to the history summary and to the diff/edit text,
which are stored outside the row.

Checks (``check_campaign``), one per plan §4.2 bullet:

* ``budget``: runs_used + runs_left == W and calls_used + calls_left == llm_cap on every row, both >= 0, and the
  next row's counters equal this row's plus ``Outcome.runs_consumed`` / ``calls_consumed``;
* ``contiguous``: step indices of a trajectory are contiguous; a root trajectory starts at 0;
* ``terminal``: a trajectory whose last row ends with ``terminated`` has exactly one ``Terminal``, on its last
  row; a ``truncated`` trajectory has none; every trajectory ends with an ``EpisodeEnd`` on its last row and on no
  other row;
* ``next_state``: the next row's ``incumbent_hash`` equals this row's ``Outcome.next_incumbent_hash``;
* ``propensity``: with a ``behaviour`` callable, re-running it on a non-forced row reproduces the logged action and
  ``action_prob``;
* ``design_weight``: ``ForkDesign.p_select`` is recomputable from its design fields and lies in (0, 1];
* ``no_future``: a ``State`` carries no field whose name is on ``FORBIDDEN_STATE_NAMES`` (checked by ``validate``
  on dict rows and statically on the dataclass);
* ``seed``: with a ``registry``, no (node, instance seed) key lies in a Paper B block.

``validate`` additionally enforces field types, closed vocabularies, and the row-level rules of plan §3.1 and §4.1
(a divergent run has no ``delta_hat`` and is not kept; a rule-forced row is not eligible; actions belong to their
epoch).
"""
from __future__ import annotations

import dataclasses
import math
import types
import typing
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Callable, Literal, Mapping, Protocol, Sequence, Union

SCHEMA = "spt_transition/v1"

Epoch = Literal["E1", "E2", "verify", "reaudit", "final"]
ActionName = Literal[
    "execute", "skip", "keep", "discard", "verify", "no_verify", "reaudit", "no_reaudit", "select",
]
EPOCH_ACTIONS: dict[str, tuple[str, ...]] = {
    "E1": ("execute", "skip"),
    "E2": ("keep", "discard"),
    "verify": ("verify", "no_verify"),
    "reaudit": ("reaudit", "no_reaudit"),
    "final": ("select",),
}
Label = Literal["ENGINEERING_ONLY", "PILOT", "EVIDENCE", "FIXTURE"]
Tier = Literal["E-SYN", "E-T0", "E-INT", "E-HELD", "E-SIM"]
SelectionRule = Literal["uniform", "oversample", "both"]
EndKind = Literal["terminated", "truncated"]

# Names that must never appear in a State: outcomes of this or later steps, and audit values (plan §4.2).
FORBIDDEN_STATE_NAMES = frozenset({
    "y_terminal", "y_terminal_per_seed", "y_start", "audit_seeds", "immediate_measured", "delta_hat", "kept",
    "next_incumbent_hash", "divergent", "runs_consumed", "calls_consumed", "terminal", "episode_end", "outcome",
})
FORBIDDEN_STATE_PREFIXES = ("audit", "future", "next_", "y_")

FLOAT_TOL = 1e-9


# ---------------------------------------------------------------- record groups (plan §4.1)

@dataclass
class Identity:
    node: str
    suite: str
    tier: Tier
    instance_id: str              # cluster id: one per campaign instance (node, instance seed, start configuration)
    campaign_id: str              # the root campaign; fork continuations share it
    step_index: int               # 0-based decision index within the campaign
    epoch: Epoch
    branch_path: list[str] = field(default_factory=list)   # [] for the root trajectory
    root_id: str | None = None
    fork_id: str | None = None


@dataclass
class EnvContext:
    proposer_model: str           # e.g. the Track X pick's registry name, or "scripted" on E-SYN
    proposer_gguf_sha256: str | None
    thinking: str                 # "off" | "on" | "n/a"
    W: int                        # worker-run cap
    llm_cap: int                  # LLM-call cap N
    memory_mode: str
    skip_display: str
    edit_schema: str              # "v1" | "v2-diff" | "synthetic"
    run_budget: str               # e.g. "steps:200", "minutes:2", "synthetic"
    constants: dict[str, float] = field(default_factory=dict)   # declared environment constants (g, prices, ...)


@dataclass
class PolicyInfo:
    policy: str                   # policy string, e.g. "static:g,h", "a2u:g0", "n6:<sha>"
    policy_sha: str | None
    action_prob: float            # probability of the logged action under the behaviour policy (1.0 if deterministic)
    eps: float = 0.0              # epsilon of the logged randomisation (0 = none)
    eps_seed: int | None = None   # RNG seed of the epsilon draw (required when eps > 0)
    behaviour_component: str | None = None   # mixture component name (SPT-2)
    continuation_policy_id: str | None = None  # policy that runs a fork continuation


@dataclass
class ForkDesign:
    selection_rule: SelectionRule
    q_uniform: float              # inclusion rate of the uniform sample
    q_oversample: float           # inclusion rate of the near-threshold oversample
    near_threshold: bool          # the fork point lies in the declared near band
    in_uniform: bool
    in_oversample: bool
    p_select: float               # = 1 - (1 - q_uniform) * (1 - q_oversample * near_threshold)
    channel_arms: bool            # E1 fork in the third that gets the instrument arms
    replicate: int                # continuation replicate index (1-based)


@dataclass
class Seeds:
    instance_seed: int
    manager_rep: int
    worker_seed: int | None
    audit_seed_block: list[int]   # [first, last] of the reserved audit seeds used for this campaign


@dataclass
class Forecast:
    pi: float | None
    mu: float | None
    tau: float | None
    sigma: float | None
    v_star: float | None          # E1 one-step value (no price subtracted)
    m_hat: float | None           # E2 posterior mean of the increment given the result


@dataclass
class State:
    proposal_hash: str
    proposal_ref: str | None      # pointer to the diff / edit text
    duplicate: bool
    noop: bool
    eligible: bool                # a policy decision (False for rule-forced rows)
    rule_forced: bool             # forced by a rule (duplicate / no-op); consumes a call and a slot
    incumbent_hash: str
    runs_used: int
    runs_left: int
    calls_used: int
    calls_left: int
    slots_left: int
    keeps_so_far: int
    skips_so_far: int
    sigma_node: float | None
    noise_source: str | None
    history_ref: str | None       # pointer to the fixed-length history summary
    forecasts: dict[str, Forecast] = field(default_factory=dict)   # belief model name -> forecast


@dataclass
class Action:
    action: ActionName
    forced: bool                  # forced by a fork arm or an intervention
    rule: str                     # what produced it: "policy", "rule_duplicate", "rule_noop", "fork_arm", ...
    selected: str | None = None   # final epoch only: hash of the selected configuration


@dataclass
class Outcome:
    runs_consumed: int
    calls_consumed: int
    next_incumbent_hash: str
    delta_hat: float | None = None          # observed increment if executed and not divergent
    divergent: bool = False                 # executed, but no metric at the fixed budget
    kept: bool | None = None                # E2 only
    immediate_measured: float | None = None  # audited increment of this trial's edit if kept here (Track S)
    wall_time_s: float | None = None


@dataclass
class EpisodeEnd:
    kind: EndKind
    reason: str                   # "W", "llm_cap", "policy_stop", "infrastructure", "protocol_stop", "parse", "host"


@dataclass
class Terminal:
    y_terminal: float
    y_terminal_per_seed: list[float]
    audit_seeds: list[int]
    y_start: float                # audited start configuration on the same audit seeds


@dataclass
class Provenance:
    host: str
    gpu: str | None
    harness_commit: str | None
    paper_commit: str | None
    llama_build: str | None
    cache_prompt: bool | None
    phase: str
    label: Label


@dataclass
class Transition:
    schema: str
    identity: Identity
    env: EnvContext
    policy: PolicyInfo
    seeds: Seeds
    state: State
    action: Action
    outcome: Outcome
    provenance: Provenance
    fork: ForkDesign | None = None
    episode_end: EpisodeEnd | None = None
    terminal: Terminal | None = None


# ---------------------------------------------------------------- typing helpers

def _hints(cls) -> dict[str, Any]:
    return typing.get_type_hints(cls)


def _is_optional(tp) -> tuple[bool, Any]:
    origin = typing.get_origin(tp)
    if origin in (Union, types.UnionType):
        args = [a for a in typing.get_args(tp) if a is not type(None)]
        if len(args) < len(typing.get_args(tp)):
            return True, args[0] if len(args) == 1 else Union[tuple(args)]
    return False, tp


def _required(cls) -> set[str]:
    return {f.name for f in fields(cls)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING}


def state_field_violations(names) -> list[str]:
    """Names that a State must not carry (plan §4.2 'no future field and no audit value in a state')."""
    return sorted(n for n in names
                  if n in FORBIDDEN_STATE_NAMES or any(n.startswith(p) for p in FORBIDDEN_STATE_PREFIXES))


# The dataclass itself must be clean; this runs at import time.
assert not state_field_violations(f.name for f in fields(State)), "State declares a forbidden field"


# ---------------------------------------------------------------- dict -> dataclass with type checking

class SchemaError(ValueError):
    pass


def _coerce(tp, value, path: str, errors: list[str]):
    optional, inner = _is_optional(tp)
    if value is None:
        if not optional:
            errors.append(f"{path}: null not allowed")
        return None
    tp = inner
    origin = typing.get_origin(tp)
    if origin is Literal:
        allowed = typing.get_args(tp)
        if value not in allowed:
            errors.append(f"{path}: {value!r} not in {list(allowed)}")
        return value
    if is_dataclass(tp):
        if not isinstance(value, Mapping):
            errors.append(f"{path}: expected object")
            return None
        return _build(tp, value, path, errors)
    if origin is list:
        (item_tp,) = typing.get_args(tp)
        if not isinstance(value, list):
            errors.append(f"{path}: expected list")
            return None
        return [_coerce(item_tp, v, f"{path}[{i}]", errors) for i, v in enumerate(value)]
    if origin is dict:
        key_tp, val_tp = typing.get_args(tp)
        if not isinstance(value, Mapping):
            errors.append(f"{path}: expected object")
            return None
        return {k: _coerce(val_tp, v, f"{path}.{k}", errors) for k, v in value.items()}
    if tp is bool:
        if not isinstance(value, bool):
            errors.append(f"{path}: expected bool")
        return value
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{path}: expected int")
        return value
    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{path}: expected number")
            return value
        if not math.isfinite(float(value)):
            errors.append(f"{path}: not finite")
        return float(value)
    if tp is str:
        if not isinstance(value, str):
            errors.append(f"{path}: expected string")
        return value
    return value


def _build(cls, data: Mapping, path: str, errors: list[str]):
    hints = _hints(cls)
    names = {f.name for f in fields(cls)}
    extra = set(data) - names
    if cls is State:
        bad = state_field_violations(extra)
        for n in bad:
            errors.append(f"{path}.{n}: forbidden in a state (future or audit value)")
        extra -= set(bad)
    for n in sorted(extra):
        errors.append(f"{path}.{n}: unknown field")
    for n in sorted(_required(cls) - set(data)):
        errors.append(f"{path}.{n}: missing required field")
    kwargs = {n: _coerce(hints[n], data[n], f"{path}.{n}", errors) for n in names if n in data}
    try:
        return cls(**kwargs)
    except TypeError:
        return None


def _row_rules(t: Transition) -> list[str]:
    errs = []
    if t.schema != SCHEMA:
        errs.append(f"schema: {t.schema!r} != {SCHEMA!r}")
    ep, act = t.identity.epoch, t.action.action
    if act not in EPOCH_ACTIONS[ep]:
        errs.append(f"action.action: {act!r} not allowed in epoch {ep!r}")
    if ep == "final" and not t.action.selected:
        errs.append("action.selected: required in the final epoch")
    if ep != "final" and t.action.selected is not None:
        errs.append("action.selected: only in the final epoch")
    o, s = t.outcome, t.state
    if o.divergent:
        if o.delta_hat is not None:
            errs.append("outcome.delta_hat: must be null for a divergent run")
        if o.kept:
            errs.append("outcome.kept: a divergent run is not kept")
    if (ep == "E2") != (o.kept is not None):
        errs.append("outcome.kept: set exactly in the E2 epoch")
    if ep == "E2" and o.kept != (act == "keep"):
        errs.append("outcome.kept: disagrees with the action")
    if s.rule_forced and s.eligible:
        errs.append("state: a rule-forced row is not eligible")
    if s.rule_forced and t.action.rule == "policy":
        errs.append("action.rule: a rule-forced row is not a policy decision")
    if not (0.0 < t.policy.action_prob <= 1.0):
        errs.append("policy.action_prob: must lie in (0, 1]")
    if t.policy.eps < 0 or t.policy.eps >= 1:
        errs.append("policy.eps: must lie in [0, 1)")
    if t.policy.eps > 0 and t.policy.eps_seed is None:
        errs.append("policy.eps_seed: required when eps > 0")
    if (t.identity.branch_path == []) != (t.fork is None):
        errs.append("fork: present exactly on fork continuations (non-empty branch_path)")
    if len(t.seeds.audit_seed_block) != 2 or t.seeds.audit_seed_block[0] > t.seeds.audit_seed_block[1]:
        errs.append("seeds.audit_seed_block: must be [first, last] with first <= last")
    if t.terminal is not None:
        tm = t.terminal
        if len(tm.y_terminal_per_seed) != len(tm.audit_seeds):
            errs.append("terminal: one value per audit seed")
        elif tm.y_terminal_per_seed and abs(sum(tm.y_terminal_per_seed) / len(tm.y_terminal_per_seed)
                                            - tm.y_terminal) > 1e-9 * max(1.0, abs(tm.y_terminal)):
            errs.append("terminal.y_terminal: must equal the mean over audit seeds")
        lo, hi = t.seeds.audit_seed_block
        if any(not (lo <= a <= hi) for a in tm.audit_seeds):
            errs.append("terminal.audit_seeds: outside the campaign's audit block")
    return errs


def parse(row: Mapping) -> tuple[Transition | None, list[str]]:
    """Build a Transition from a JSON row; return (transition or None, errors)."""
    errors: list[str] = []
    t = _build(Transition, row, "row", errors)
    if t is not None and not errors:
        errors.extend(_row_rules(t))
    return (t if not errors else None), errors


def validate(row: Mapping | Transition) -> list[str]:
    """Field-level and row-level errors of one row ([] if valid)."""
    if isinstance(row, Transition):
        row = to_dict(row)
    return parse(row)[1]


def to_dict(t: Transition) -> dict:
    return asdict(t)


def from_dict(row: Mapping) -> Transition:
    t, errors = parse(row)
    if errors:
        raise SchemaError("; ".join(errors))
    return t


# ---------------------------------------------------------------- JSON schema export

def _json_type(tp) -> dict:
    optional, inner = _is_optional(tp)
    if optional:
        return {"anyOf": [_json_type(inner), {"type": "null"}]}
    origin = typing.get_origin(tp)
    if origin is Literal:
        return {"enum": list(typing.get_args(tp))}
    if is_dataclass(tp):
        return {"$ref": f"#/$defs/{tp.__name__}"}
    if origin is list:
        return {"type": "array", "items": _json_type(typing.get_args(tp)[0])}
    if origin is dict:
        return {"type": "object", "additionalProperties": _json_type(typing.get_args(tp)[1])}
    return {bool: {"type": "boolean"}, int: {"type": "integer"}, float: {"type": "number"},
            str: {"type": "string"}}[tp]


def _object_schema(cls) -> dict:
    hints = _hints(cls)
    return {
        "type": "object",
        "properties": {f.name: _json_type(hints[f.name]) for f in fields(cls)},
        "required": sorted(_required(cls)),
        "additionalProperties": False,
    }


def to_json_schema() -> dict:
    defs, todo = {}, [Transition]
    while todo:
        cls = todo.pop()
        if cls.__name__ in defs:
            continue
        defs[cls.__name__] = _object_schema(cls)
        for tp in _hints(cls).values():
            stack = [tp]
            while stack:
                x = stack.pop()
                if is_dataclass(x):
                    todo.append(x)
                stack.extend(typing.get_args(x))
    root = dict(defs.pop("Transition"))
    root.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA,
                 "title": "SPT transition record", "$defs": dict(sorted(defs.items()))})
    return root


# ---------------------------------------------------------------- campaign checks (plan §4.2)

@dataclass(frozen=True)
class Violation:
    check: str
    trajectory: tuple
    step_index: int | None
    message: str


class SeedRegistry(Protocol):
    def paper_b_block(self, node: str, instance_seed: int) -> str | None:
        """Name of the Paper B block containing (node, instance_seed), or None."""


Behaviour = Callable[[Transition], tuple[str, float]]


def trajectory_key(t: Transition) -> tuple:
    return (t.identity.campaign_id, tuple(t.identity.branch_path))


def _p_select(d: ForkDesign) -> float:
    return 1.0 - (1.0 - d.q_uniform) * (1.0 - d.q_oversample * (1.0 if d.near_threshold else 0.0))


def check_campaign(rows: Sequence[Mapping | Transition], *, registry: SeedRegistry | None = None,
                   behaviour: Behaviour | None = None) -> list[Violation]:
    """All plan §4.2 violations in a batch of rows (any number of trajectories)."""
    out: list[Violation] = []
    parsed: list[Transition] = []
    for i, r in enumerate(rows):
        if isinstance(r, Transition):
            r = to_dict(r)
        t, errs = parse(r)
        if errs:
            names = [e for e in errs if "forbidden in a state" in e]
            for e in names:
                out.append(Violation("no_future", ("?",), r.get("identity", {}).get("step_index"), e))
            for e in errs:
                if e not in names:
                    out.append(Violation("schema", ("?",), r.get("identity", {}).get("step_index"), e))
            continue
        parsed.append(t)

    groups: dict[tuple, list[Transition]] = {}
    for t in parsed:
        groups.setdefault(trajectory_key(t), []).append(t)

    for key, traj in groups.items():
        traj.sort(key=lambda t: t.identity.step_index)
        steps = [t.identity.step_index for t in traj]
        if len(set(steps)) != len(steps):
            out.append(Violation("contiguous", key, None, "duplicate step indices"))
        if steps != list(range(steps[0], steps[0] + len(steps))):
            out.append(Violation("contiguous", key, None, f"steps not contiguous: {steps}"))
        if key[1] == () and steps[0] != 0:
            out.append(Violation("contiguous", key, steps[0], "root trajectory must start at step 0"))

        for t in traj:
            s, env = t.state, t.env
            if s.runs_used + s.runs_left != env.W or s.runs_left < 0 or s.runs_used < 0:
                out.append(Violation("budget", key, t.identity.step_index,
                                     f"runs_used {s.runs_used} + runs_left {s.runs_left} != W {env.W}"))
            if s.calls_used + s.calls_left != env.llm_cap or s.calls_left < 0 or s.calls_used < 0:
                out.append(Violation("budget", key, t.identity.step_index,
                                     f"calls_used {s.calls_used} + calls_left {s.calls_left} != cap {env.llm_cap}"))
        for a, b in zip(traj, traj[1:]):
            if b.state.runs_used != a.state.runs_used + a.outcome.runs_consumed:
                out.append(Violation("budget", key, b.identity.step_index,
                                     "runs_used does not follow from the previous row's runs_consumed"))
            if b.state.calls_used != a.state.calls_used + a.outcome.calls_consumed:
                out.append(Violation("budget", key, b.identity.step_index,
                                     "calls_used does not follow from the previous row's calls_consumed"))
            if b.state.incumbent_hash != a.outcome.next_incumbent_hash:
                out.append(Violation("next_state", key, b.identity.step_index,
                                     "incumbent_hash != previous row's next_incumbent_hash"))

        last = traj[-1]
        for t in traj[:-1]:
            if t.episode_end is not None:
                out.append(Violation("terminal", key, t.identity.step_index, "episode_end before the last row"))
            if t.terminal is not None:
                out.append(Violation("terminal", key, t.identity.step_index, "terminal before the last row"))
        if last.episode_end is None:
            out.append(Violation("terminal", key, last.identity.step_index, "last row has no episode_end"))
        elif last.episode_end.kind == "terminated" and last.terminal is None:
            out.append(Violation("terminal", key, last.identity.step_index, "terminated trajectory has no terminal"))
        elif last.episode_end.kind == "truncated" and last.terminal is not None:
            out.append(Violation("terminal", key, last.identity.step_index, "truncated trajectory has a terminal"))

        for t in traj:
            if t.fork is not None:
                d = t.fork
                ok_rule = {"uniform": d.in_uniform and not d.in_oversample,
                           "oversample": d.in_oversample and not d.in_uniform,
                           "both": d.in_uniform and d.in_oversample}[d.selection_rule]
                if not (0.0 < d.p_select <= 1.0) or abs(d.p_select - _p_select(d)) > FLOAT_TOL:
                    out.append(Violation("design_weight", key, t.identity.step_index,
                                         f"p_select {d.p_select} != recomputed {_p_select(d):.12g}"))
                if not ok_rule or (d.in_oversample and not d.near_threshold):
                    out.append(Violation("design_weight", key, t.identity.step_index,
                                         "selection flags inconsistent with selection_rule / near_threshold"))
            if behaviour is not None and not t.action.forced and not t.state.rule_forced:
                act, prob = behaviour(t)
                if act != t.action.action or abs(prob - t.policy.action_prob) > FLOAT_TOL:
                    out.append(Violation("propensity", key, t.identity.step_index,
                                         f"replay gave ({act}, {prob}) vs logged "
                                         f"({t.action.action}, {t.policy.action_prob})"))
            if registry is not None:
                hit = registry.paper_b_block(t.identity.node, t.seeds.instance_seed)
                if hit is not None:
                    out.append(Violation("seed", key, t.identity.step_index,
                                         f"instance seed {t.seeds.instance_seed} lies in Paper B block {hit}"))
    return out
