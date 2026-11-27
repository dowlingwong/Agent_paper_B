"""SPT transition record ``spt_transition/v1`` and its mechanical checks (build runbook P1; plan §4.1–§4.2).

AI-assisted (Claude, chat session, 15 Nov 2026; revised after review round 1). ENGINEERING_ONLY.

One row per decision point of one trajectory. A trajectory is a root campaign (``branch_path == []``) or one
continuation of a fork (``branch_path`` names the fork arms taken from the root, e.g. ``["f3:skip:r1"]``).

Track S names (``r1/tracks/schema.py`` on ``trackS-ops-20261030`` @ ``fab88fc``) are reused where the meaning is the
same: ``uniform``, ``oversample``, ``p_select``, ``channel_arms``, ``prior_skips``, ``key_seen``,
``manager_gguf_sha256``, the ``Forecast`` tuple (pi, mu, tau, sigma, v_star, m_hat, g), ``immediate_measured``,
``y_start``, ``y_terminal``, ``y_terminal_per_seed``, ``audit_seeds``, ``myopic_action`` (here
``behaviour_action``, the action the behaviour policy itself would have taken, logged on forced rows), and the
``Provenance`` fields ``controller_version`` / ``prior_sha256``. This module is a port, not an import. Units are the
node's raw metric units; ``sigma_node`` is recorded for standardising.

Epochs and actions (plan §3.3, extended by R1-PAPERC-REFRAME for evaluation control):

* ``E1``: ``execute`` / ``skip``;      ``E2``: ``keep`` / ``discard``;
* ``verify``: ``verify`` (re-measure the candidate) / ``no_verify``, between an execute and its E2;
* ``reaudit``: ``reaudit`` (re-measure the incumbent) / ``no_reaudit``, anywhere between decisions;
* ``final``: ``select`` — at most once, as the last row; ``Action.selected`` names the chosen configuration.

There is no stop action yet, so ``EpisodeEnd.reason = "policy_stop"`` is rejected (plan §3.3 round C).

Row conventions:

* every E1 row consumes one LLM call and one proposal slot (``slots_left``), rule-forced rows included;
* executing actions (``execute``, ``verify``, ``reaudit``) consume >= 1 run and carry exactly one of
  ``delta_hat`` / ``divergent`` / ``failure_category`` (Track S's ``failed_invalid`` class); non-executing actions
  consume 0 runs and carry none;
* a divergent or invalid candidate is not kept: its E2 row is a ``discard`` (plan §3.1), including the first row of
  an E2 fork (row rule);
* ``candidate_obs`` counts the candidate's measurements (its execute plus verify rows); ``candidate_divergent`` /
  ``candidate_delta_hat`` describe its latest measurement;
* ``incumbent_recorded`` / ``incumbent_obs`` change only after a keep, a reaudit or a final selection;
* a W termination means fewer than ``env.constants["run_cost"]`` (default 1) runs remain;
* the incumbent changes only by an E2 ``keep`` (to ``State.candidate_hash``) or a ``final`` ``select``
  (to ``Action.selected``);
* ``immediate_measured`` (Track S) lives on the E2 row of a kept candidate when an audit exists, else null;
* ``rule_forced`` rows (duplicate / no-op skips, the first trial's execute-and-keep) are not eligible, carry an
  ``Action.rule`` starting with ``rule_`` and ``action_prob = 1.0``; forced rows (fork arms, interventions) carry
  ``action_prob = null`` (no defined propensity, plan §6.1) and log ``behaviour_action`` / ``behaviour_prob``.

Checks (``check_campaign``) — the plan §4.2 bullets, plus consistency checks the review asked for:

* ``budget``: used + left == cap per row, consumed <= left, the chain across rows, a root starts at 0, a fork's first
  row has its parent's counters at the same step (when the parent is in the batch);
* ``contiguous``: step indices of a trajectory are contiguous; a root starts at step 0;
* ``terminal``: exactly one ``Terminal`` on the last row of a terminated trajectory, none on a truncated one, an
  ``EpisodeEnd`` on the last row only, a reason that matches its kind, and the ledger agreeing with W / llm_cap;
* ``next_state``: the incumbent changes only by keep / select, and the next row (or the fork's first row) starts
  from this row's ``next_incumbent_hash``;
* ``propensity``: ``behaviour`` replayed on a decision-time view (no action, outcome or terminal) reproduces the
  logged action and probability on non-forced, non-rule rows;
* ``design_weight``: ``p_select`` is recomputable from the design fields;
* ``no_future``: no future or audit value in a state (field names; E1 states carry no ``m_hat`` and no candidate
  result);
* ``seed``: no seed field (instance, worker, epsilon, audit block, terminal audit seeds) lies in a Paper B block;
* ``outcome`` (row level): actions fit their epoch; consumption, ``delta_hat`` / ``divergent`` and ``kept`` fit
  the action;
* ``epoch_sequence``: an E2 row follows its execute (verify rows between them only), carries that execute's result,
  and discards a divergent candidate; a root starts at E1; ``final`` only last;
* ``constant``: node, suite, tier, instance, campaign identity, env, seeds and fork design are constant within a
  trajectory; fork rows have ``fork_id`` and ``replicate >= 1``;
* ``counters``: ``keeps_so_far``, ``prior_skips`` and ``slots_left`` follow the rows.

**Amendment of 16 Nov 2026 (build runbook P3; BUILD_LIST B17): final-selection candidates.** ``State.candidates``
lists the configurations a ``final`` row chooses among, each with its recorded value and number of measurements; it
is empty on every other row, and ``Action.selected`` must name one of them when the list is non-empty. Compatibility:
the field is optional with an empty default, so rows written before it remain valid (backward); ``to_dict`` omits
the field when the list is empty, so every row without candidates is also accepted by the P1 validator of 15 Nov
(forward). Only final rows that carry candidates need this amendment. ``check_campaign`` (``epoch_sequence``) checks
that candidate hashes are unique and that every candidate was the incumbent earlier in the trajectory (or its
ancestors), with the recorded value and count it last had there. Deferred: the A/A replay bullet of plan §4.2 (a continuation whose forced action equals the root's action
reproduces the root's later rows). It needs A/A fork leaves and the runner's restore path, so it is implemented
with the SPT runner (BUILD_LIST B11; Track S's ``aa_reproduced``), not on logged rows alone.
"""
from __future__ import annotations

import dataclasses
import math
import types
import typing
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Any, Callable, Literal, Mapping, NamedTuple, Protocol, Sequence, Union

SCHEMA = "spt_transition/v1"
SCHEMA_ID = "urn:paperc:spt_transition:v1"

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
EXECUTING = frozenset({"execute", "verify", "reaudit"})
Label = Literal["ENGINEERING_ONLY", "PILOT", "EVIDENCE", "FIXTURE"]
Tier = Literal["E-SYN", "E-T0", "E-INT", "E-HELD", "E-SIM"]
SelectionRule = Literal["uniform", "oversample", "both"]
EndKind = Literal["terminated", "truncated"]
FailureCategory = Literal["syntax_error", "runtime_error", "metric_missing", "invalid_edit_scope", "invalid_config",
                          "proposal_precondition_failed"]
# harness failure categories (the last two appear in Paper B sweep 1, harness 6adf385) minus "degraded_metric",
# which is a valid result (a worse metric), not a failure
EndReason = Literal["W", "llm_cap", "policy_stop", "infrastructure", "protocol_stop", "parse", "host"]
END_REASONS = {"terminated": ("W", "llm_cap"), "truncated": ("infrastructure", "protocol_stop", "parse", "host")}

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
    fork_id: str | None = None    # required on fork rows; equals the first element of branch_path up to ':'


@dataclass
class EnvContext:
    proposer_model: str           # e.g. the Track X pick's registry name, or "scripted" on E-SYN
    manager_gguf_sha256: str | None
    thinking: str                 # "off" | "on" | "n/a"
    W: int                        # worker-run cap
    llm_cap: int                  # LLM-call cap N
    memory_mode: str
    skip_display: str
    edit_schema: str              # "v1" | "v2-diff" | "synthetic"
    run_budget: str               # e.g. "steps:200", "minutes:2", "synthetic"
    constants: dict[str, float] = field(default_factory=dict)   # declared environment constants


@dataclass
class PolicyInfo:
    policy: str                   # policy string, e.g. "static:g,h", "a2u:g0", "n6:<sha>"
    policy_sha: str | None
    action_prob: float | None     # P(logged action | behaviour); 1.0 deterministic/rule; null on forced rows
    eps: float = 0.0              # epsilon of the logged randomisation (0 = none)
    eps_seed: int | None = None   # RNG key of the epsilon draw (required when eps > 0)
    behaviour_component: str | None = None    # mixture component name (SPT-2)
    continuation_policy_id: str | None = None  # policy that runs a fork continuation
    behaviour_action: ActionName | None = None   # forced rows: what the behaviour policy would have done
    behaviour_prob: float | None = None          # forced rows: its probability under the behaviour policy


@dataclass
class ForkDesign:
    selection_rule: SelectionRule
    q_uniform: float              # inclusion rate of the uniform sample
    q_oversample: float           # inclusion rate of the near-threshold oversample
    near_threshold: bool          # the fork point lies in the declared near band
    uniform: bool                 # drawn in the uniform sample (Track S name)
    oversample: bool              # drawn in the oversample (Track S name)
    p_select: float               # = 1 - (1 - q_uniform) * (1 - q_oversample * near_threshold)
    channel_arms: bool            # E1 fork in the third that gets the instrument arms
    replicate: int                # continuation replicate index (>= 1)


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
    m_hat: float | None           # posterior mean of the increment given the result (E2 and later only)
    g: float | None = None        # declared run price used by this forecaster's rule


@dataclass
class Candidate:
    """One configuration a final selection can choose (B17): its recorded value and number of measurements."""
    hash: str
    recorded: float | None
    obs: int


@dataclass
class State:
    proposal_hash: str
    proposal_ref: str | None      # pointer to the diff / edit text
    candidate_hash: str | None    # configuration hash after applying the proposal (null for reaudit / final)
    duplicate: bool
    noop: bool
    eligible: bool                # a policy decision (== not rule_forced)
    rule_forced: bool             # forced by a rule; consumes a call and a slot at E1
    key_seen: bool                # the edited key was executed before in this campaign (Track S)
    incumbent_hash: str
    incumbent_recorded: float | None   # the incumbent's recorded metric (what the loop compares against)
    incumbent_obs: int            # number of measurements behind incumbent_recorded
    candidate_delta_hat: float | None  # E2 / verify: the candidate's observed increment so far (null at E1)
    candidate_divergent: bool     # E2 / verify: the candidate's latest measurement diverged (False at E1)
    candidate_invalid: bool       # E2 / verify: the candidate's run failed as invalid (False at E1)
    candidate_obs: int            # E2 / verify: measurements of the candidate so far (0 at E1)
    runs_used: int
    runs_left: int
    calls_used: int
    calls_left: int
    slots_left: int
    keeps_so_far: int
    prior_skips: int              # E1 skips before this row (rule-forced skips included)
    sigma_node: float | None
    noise_source: str | None
    history_ref: str | None       # pointer to the fixed-length history summary
    forecasts: dict[str, Forecast] = field(default_factory=dict)   # belief model name -> forecast
    candidates: list[Candidate] = field(default_factory=list)      # final rows only: the selectable configurations


@dataclass
class Action:
    action: ActionName
    forced: bool                  # forced by a fork arm or an intervention
    rule: str                     # "policy", "rule_duplicate", "rule_noop", "rule_first_trial", "rule_divergent",
                                  # "fork_arm", "intervention"
    selected: str | None = None   # final epoch only: hash of the selected configuration


@dataclass
class Outcome:
    runs_consumed: int
    calls_consumed: int
    next_incumbent_hash: str
    delta_hat: float | None = None           # executing actions: observed increment (null if divergent)
    divergent: bool = False                  # executing actions: no metric at the fixed budget
    failure_category: FailureCategory | None = None   # executing actions: the run failed as invalid
    kept: bool | None = None                 # E2 only
    immediate_measured: float | None = None  # E2 keep with an audit: audited increment of the kept edit
    wall_time_s: float | None = None


@dataclass
class EpisodeEnd:
    kind: EndKind
    reason: EndReason


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
    controller_version: str | None = None   # behaviour controller / belief model version (Track S)
    prior_sha256: str | None = None         # belief model file (Track S: A2-U prior)


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


class DecisionView(NamedTuple):
    """What a behaviour policy may see when its decision is replayed (no action, outcome, terminal, audits)."""
    identity: Identity
    env: EnvContext
    instance_seed: int
    manager_rep: int
    state: State
    policy: str
    behaviour_component: str | None
    eps: float
    eps_seed: int | None


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
        _, val_tp = typing.get_args(tp)
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
        elif value < 0:
            errors.append(f"{path}: must be >= 0")
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


# Row rules return (check, message).

def _row_rules(t: Transition) -> list[tuple[str, str]]:
    errs: list[tuple[str, str]] = []
    add = lambda check, msg: errs.append((check, msg))   # noqa: E731
    if t.schema != SCHEMA:
        add("schema", f"schema: {t.schema!r} != {SCHEMA!r}")
    ep, act, s, o, pol = t.identity.epoch, t.action.action, t.state, t.outcome, t.policy

    # outcome: actions fit epochs; consumption and results fit actions
    if act not in EPOCH_ACTIONS[ep]:
        add("outcome", f"action.action: {act!r} not allowed in epoch {ep!r}")
    if (ep == "final") != (t.action.selected is not None):
        add("outcome", "action.selected: set exactly in the final epoch")
    if s.candidates and ep != "final":
        add("outcome", "state.candidates: only on final rows")
    if s.candidates and t.action.selected is not None and t.action.selected not in {c.hash for c in s.candidates}:
        add("outcome", "action.selected: not among state.candidates")
    n_results = (o.delta_hat is not None) + o.divergent + (o.failure_category is not None)
    if act in EXECUTING:
        if o.runs_consumed < 1:
            add("outcome", f"outcome.runs_consumed: {act} consumes >= 1 run")
        if n_results != 1:
            add("outcome", f"outcome: {act} carries exactly one of delta_hat / divergent / failure_category")
    else:
        if o.runs_consumed != 0:
            add("outcome", f"outcome.runs_consumed: {act} consumes no run")
        if n_results:
            add("outcome", f"outcome: {act} carries no delta_hat / divergent / failure_category")
    if ep == "E2" and (s.candidate_divergent or s.candidate_invalid) and act != "discard":
        add("outcome", "a divergent or invalid candidate must be discarded")
    if (ep == "E2") != (o.kept is not None):
        add("outcome", "outcome.kept: set exactly in the E2 epoch")
    elif ep == "E2" and o.kept != (act == "keep"):
        add("outcome", "outcome.kept: disagrees with the action")
    if o.immediate_measured is not None and not (ep == "E2" and act == "keep"):
        add("outcome", "outcome.immediate_measured: only on an E2 keep")
    if ep == "E1" and o.calls_consumed < 1:
        add("outcome", "outcome.calls_consumed: an E1 row consumes the proposal's LLM call")
    if ep in ("E1", "E2", "verify") and s.candidate_hash is None:
        add("outcome", "state.candidate_hash: required in E1, E2 and verify rows")

    # flags
    if s.eligible == s.rule_forced:
        add("outcome", "state: eligible must equal not rule_forced")
    if s.rule_forced != t.action.rule.startswith("rule_"):
        add("outcome", "action.rule: rule_* exactly on rule-forced rows")
    if ep == "E1" and (s.duplicate or s.noop) and not s.rule_forced:
        add("outcome", "state: a duplicate / no-op proposal is rule-forced at E1")
    if s.rule_forced and t.action.forced:
        add("outcome", "action: a row is rule-forced or forced, not both")

    # propensity fields
    if t.action.forced:
        if pol.action_prob is not None:
            add("propensity", "policy.action_prob: null on forced rows (no defined propensity)")
        if pol.behaviour_action is None:
            add("propensity", "policy.behaviour_action: required on forced rows")
        elif pol.behaviour_action not in EPOCH_ACTIONS[ep]:
            add("propensity", f"policy.behaviour_action: {pol.behaviour_action!r} not an action of epoch {ep!r}")
    else:
        if pol.action_prob is None or not (0.0 < pol.action_prob <= 1.0):
            add("propensity", "policy.action_prob: must lie in (0, 1] on non-forced rows")
        if s.rule_forced and pol.action_prob != 1.0:
            add("propensity", "policy.action_prob: 1.0 on rule-forced rows")
        if pol.behaviour_action is not None or pol.behaviour_prob is not None:
            add("propensity", "policy.behaviour_*: only on forced rows")
    if pol.behaviour_prob is not None and not (0.0 <= pol.behaviour_prob <= 1.0):
        add("propensity", "policy.behaviour_prob: must lie in [0, 1]")
    if not (0.0 <= pol.eps < 1.0):
        add("propensity", "policy.eps: must lie in [0, 1)")
    if pol.eps > 0 and pol.eps_seed is None:
        add("propensity", "policy.eps_seed: required when eps > 0")
    if pol.action_prob is not None and 0.0 < pol.action_prob < 1.0 and pol.eps_seed is None:
        add("propensity", "policy.eps_seed: required on a randomised row (0 < action_prob < 1)")

    # no future values at decision time
    if ep == "E1":
        if any(f.m_hat is not None for f in s.forecasts.values()):
            add("no_future", "state.forecasts[*].m_hat: the result-conditional mean does not exist at E1")
        if s.candidate_delta_hat is not None or s.candidate_divergent or s.candidate_invalid or s.candidate_obs != 0:
            add("no_future", "state.candidate_*: no candidate result exists at E1")

    # identity / fork
    if t.identity.branch_path:
        if t.fork is None:
            add("constant", "fork: required on fork continuations (non-empty branch_path)")
        if not t.identity.fork_id or t.identity.branch_path[0].split(":")[0] != t.identity.fork_id:
            add("constant", "identity.fork_id: required on fork rows and must match branch_path[0]")
        if t.fork is not None and t.fork.replicate < 1:
            add("constant", "fork.replicate: must be >= 1")
        last_part = t.identity.branch_path[-1].split(":")[-1]
        if t.fork is not None and last_part.startswith("r") and last_part[1:].isdigit() \
                and int(last_part[1:]) != t.fork.replicate:
            add("constant", "fork.replicate: disagrees with the r<N> of branch_path")
    else:
        if t.fork is not None or t.identity.fork_id is not None:
            add("constant", "fork / fork_id: only on fork continuations")

    # seeds and terminal
    if len(t.seeds.audit_seed_block) != 2 or t.seeds.audit_seed_block[0] > t.seeds.audit_seed_block[1]:
        add("schema", "seeds.audit_seed_block: must be [first, last] with first <= last")
    if t.episode_end is not None and t.episode_end.reason not in END_REASONS[t.episode_end.kind]:
        add("terminal", f"episode_end: reason {t.episode_end.reason!r} is not a {t.episode_end.kind} reason")
    if t.terminal is not None:
        tm = t.terminal
        if len(tm.y_terminal_per_seed) != len(tm.audit_seeds) or not tm.audit_seeds:
            add("terminal", "terminal: one value per audit seed, at least one")
        elif abs(sum(tm.y_terminal_per_seed) / len(tm.y_terminal_per_seed) - tm.y_terminal) \
                > 1e-9 * max(1.0, abs(tm.y_terminal)):
            add("terminal", "terminal.y_terminal: must equal the mean over audit seeds")
        if len(t.seeds.audit_seed_block) == 2:
            lo, hi = t.seeds.audit_seed_block
            if any(not (lo <= a <= hi) for a in tm.audit_seeds):
                add("terminal", "terminal.audit_seeds: outside the campaign's audit block")
    return errs


def parse_checked(row) -> tuple[Transition | None, list[tuple[str, str]]]:
    """Build a Transition from a JSON row; return (transition or None, [(check, message)])."""
    if not isinstance(row, Mapping):
        return None, [("schema", "row: expected an object")]
    errors: list[str] = []
    t = _build(Transition, row, "row", errors)
    tagged = [("no_future" if "forbidden in a state" in e else "schema", e) for e in errors]
    if t is not None and not errors:
        tagged += _row_rules(t)
    return (t if not tagged else None), tagged


def parse(row) -> tuple[Transition | None, list[str]]:
    t, tagged = parse_checked(row)
    return t, [m for _, m in tagged]


def validate(row) -> list[str]:
    """Field-level and row-level errors of one row ([] if valid)."""
    if isinstance(row, Transition):
        row = to_dict(row)
    return parse(row)[1]


def to_dict(t: Transition) -> dict:
    d = asdict(t)
    if not d["state"].get("candidates"):           # amendment of 16 Nov: keep rows readable by the 15 Nov validator
        d["state"].pop("candidates", None)
    return d


def from_dict(row: Mapping) -> Transition:
    t, errors = parse(row)
    if errors:
        raise SchemaError("; ".join(errors))
    return t


# ---------------------------------------------------------------- JSON schema export

_RANGES = {
    ("PolicyInfo", "action_prob"): {"exclusiveMinimum": 0, "maximum": 1},
    ("PolicyInfo", "behaviour_prob"): {"minimum": 0, "maximum": 1},
    ("PolicyInfo", "eps"): {"minimum": 0, "exclusiveMaximum": 1},
    ("ForkDesign", "p_select"): {"exclusiveMinimum": 0, "maximum": 1},
    ("ForkDesign", "q_uniform"): {"minimum": 0, "maximum": 1},
    ("ForkDesign", "q_oversample"): {"minimum": 0, "maximum": 1},
    ("ForkDesign", "replicate"): {"minimum": 1},
}


def _json_type(tp, extra: dict | None = None) -> dict:
    optional, inner = _is_optional(tp)
    if optional:
        return {"anyOf": [_json_type(inner, extra), {"type": "null"}]}
    origin = typing.get_origin(tp)
    if origin is Literal:
        return {"enum": list(typing.get_args(tp))}
    if is_dataclass(tp):
        return {"$ref": f"#/$defs/{tp.__name__}"}
    if origin is list:
        return {"type": "array", "items": _json_type(typing.get_args(tp)[0])}
    if origin is dict:
        return {"type": "object", "additionalProperties": _json_type(typing.get_args(tp)[1])}
    base = {bool: {"type": "boolean"}, int: {"type": "integer", "minimum": 0}, float: {"type": "number"},
            str: {"type": "string"}}[tp]
    return {**base, **(extra or {})}


def _object_schema(cls) -> dict:
    hints = _hints(cls)
    props = {}
    for f in fields(cls):
        js = _json_type(hints[f.name], _RANGES.get((cls.__name__, f.name)))
        if f.default is not dataclasses.MISSING:
            js = {**js, "default": f.default}
        elif f.default_factory is not dataclasses.MISSING:
            js = {**js, "default": f.default_factory()}
        props[f.name] = js
    if cls is Seeds:
        props["audit_seed_block"] = {**props["audit_seed_block"], "minItems": 2, "maxItems": 2}
    if cls is Transition:
        props["schema"] = {"const": SCHEMA}
    return {"type": "object", "properties": props, "required": sorted(_required(cls)),
            "additionalProperties": False}


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
    root.update({
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA_ID,
        "title": "SPT transition record (spt_transition/v1)",
        "description": "Field shapes only. Row and campaign rules (and integer vs float, NaN) are enforced by "
                       "paperc.schema.validate / check_campaign, which are authoritative. Amended 16 Nov 2026 "
                       "(build runbook P3, B17): optional state.candidates on final rows.",
        "$defs": dict(sorted(defs.items())),
    })
    return root


# ---------------------------------------------------------------- campaign checks

@dataclass(frozen=True)
class Violation:
    check: str
    trajectory: tuple
    step_index: int | None
    message: str


class SeedRegistry(Protocol):
    def paper_b_block(self, node: str, instance_seed: int) -> str | None:
        """Name of the Paper B block containing the seed, or None."""

    # Optional: ``paper_b_range(lo, hi) -> str | None`` names a Paper B block intersecting [lo, hi]; when present it
    # is used for ``audit_seed_block`` (otherwise both ends are checked).


Behaviour = Callable[[DecisionView], tuple[str, float]]


def trajectory_key(t: Transition) -> tuple:
    return (t.identity.campaign_id, tuple(t.identity.branch_path))


def _p_select(d: ForkDesign) -> float:
    return 1.0 - (1.0 - d.q_uniform) * (1.0 - d.q_oversample * (1.0 if d.near_threshold else 0.0))


def _view(t: Transition) -> DecisionView:
    return DecisionView(t.identity, t.env, t.seeds.instance_seed, t.seeds.manager_rep, t.state, t.policy.policy,
                        t.policy.behaviour_component, t.policy.eps, t.policy.eps_seed)


def _key_of(row) -> tuple:
    try:
        idn = row["identity"]
        return (idn["campaign_id"], tuple(idn.get("branch_path") or ()))
    except (TypeError, KeyError):
        return ("?",)


def _step_of(row):
    try:
        return row["identity"]["step_index"]
    except (TypeError, KeyError):
        return None


def check_campaign(rows: Sequence, *, registry: SeedRegistry | None = None,
                   behaviour: Behaviour | None = None) -> list[Violation]:
    """All violations in a batch of rows (any number of trajectories)."""
    out: list[Violation] = []
    V = lambda check, key, step, msg: out.append(Violation(check, key, step, msg))   # noqa: E731
    parsed: list[Transition] = []
    for r in rows:
        if isinstance(r, Transition):
            r = to_dict(r)
        t, tagged = parse_checked(r)
        if t is None:
            hard = [x for x in tagged if x[0] == "schema"]
            for check, msg in tagged:
                V(check, _key_of(r), _step_of(r), msg)
            if hard:
                continue
            # row-rule violations only: keep the row for the campaign checks
            errors: list[str] = []
            t = _build(Transition, r, "row", errors)
        parsed.append(t)

    groups: dict[tuple, list[Transition]] = {}
    for t in parsed:
        groups.setdefault(trajectory_key(t), []).append(t)
    by_step = {k: {t.identity.step_index: t for t in v} for k, v in groups.items()}

    for key, traj in groups.items():
        traj.sort(key=lambda t: t.identity.step_index)
        steps = [t.identity.step_index for t in traj]
        is_root = key[1] == ()
        if len(set(steps)) != len(steps):
            V("contiguous", key, None, "duplicate step indices")
        if steps != list(range(steps[0], steps[0] + len(steps))):
            V("contiguous", key, None, f"steps not contiguous: {steps}")
        if is_root and steps[0] != 0:
            V("contiguous", key, steps[0], "root trajectory must start at step 0")

        # constant within trajectory
        first = traj[0]
        for t in traj[1:]:
            for what, a, b in (("identity", (first.identity.node, first.identity.suite, first.identity.tier,
                                             first.identity.instance_id, first.identity.root_id,
                                             first.identity.fork_id),
                                (t.identity.node, t.identity.suite, t.identity.tier, t.identity.instance_id,
                                 t.identity.root_id, t.identity.fork_id)),
                               ("env", first.env, t.env), ("seeds", first.seeds, t.seeds),
                               ("fork", first.fork, t.fork)):
                if a != b:
                    V("constant", key, t.identity.step_index, f"{what} changes within the trajectory")

        # budget per row
        for t in traj:
            s, o, env, st = t.state, t.outcome, t.env, t.identity.step_index
            if s.runs_used + s.runs_left != env.W:
                V("budget", key, st, f"runs_used {s.runs_used} + runs_left {s.runs_left} != W {env.W}")
            if s.calls_used + s.calls_left != env.llm_cap:
                V("budget", key, st, f"calls_used {s.calls_used} + calls_left {s.calls_left} != cap {env.llm_cap}")
            if o.runs_consumed > s.runs_left:
                V("budget", key, st, f"runs_consumed {o.runs_consumed} > runs_left {s.runs_left}")
            if o.calls_consumed > s.calls_left:
                V("budget", key, st, f"calls_consumed {o.calls_consumed} > calls_left {s.calls_left}")
        if is_root and steps[0] == 0 and (first.state.runs_used or first.state.calls_used):
            V("budget", key, 0, "a root starts with runs_used == calls_used == 0")
        if not is_root:
            parent = by_step.get((key[0], key[1][:-1]), {}).get(first.identity.step_index)
            if parent is not None:
                ps, fs = parent.state, first.state
                if (ps.runs_used, ps.calls_used, ps.slots_left, ps.keeps_so_far, ps.prior_skips) != \
                        (fs.runs_used, fs.calls_used, fs.slots_left, fs.keeps_so_far, fs.prior_skips):
                    V("budget", key, first.identity.step_index, "fork's first row does not start from its "
                                                                "parent's counters at the same step")
                if ps.incumbent_hash != fs.incumbent_hash:
                    V("next_state", key, first.identity.step_index,
                      "fork's first row does not start from its parent's incumbent")

        # next state per row and across rows
        for t in traj:
            s, o, a = t.state, t.outcome, t.action
            if t.identity.epoch == "E2" and a.action == "keep":
                expected = s.candidate_hash
            elif t.identity.epoch == "final":
                expected = a.selected
            else:
                expected = s.incumbent_hash
            if o.next_incumbent_hash != expected:
                V("next_state", key, t.identity.step_index,
                  f"next_incumbent_hash should be {expected!r} after {t.identity.epoch} {a.action}")
        for a_, b_ in zip(traj, traj[1:]):
            if b_.state.incumbent_hash != a_.outcome.next_incumbent_hash:
                V("next_state", key, b_.identity.step_index,
                  "incumbent_hash != previous row's next_incumbent_hash")
            if b_.state.runs_used != a_.state.runs_used + a_.outcome.runs_consumed:
                V("budget", key, b_.identity.step_index, "runs_used does not follow from runs_consumed")
            if b_.state.calls_used != a_.state.calls_used + a_.outcome.calls_consumed:
                V("budget", key, b_.identity.step_index, "calls_used does not follow from calls_consumed")
            # counters
            ea, aa = a_.identity.epoch, a_.action.action
            if b_.state.keeps_so_far != a_.state.keeps_so_far + int(ea == "E2" and aa == "keep"):
                V("counters", key, b_.identity.step_index, "keeps_so_far does not follow the rows")
            if b_.state.prior_skips != a_.state.prior_skips + int(ea == "E1" and aa == "skip"):
                V("counters", key, b_.identity.step_index, "prior_skips does not follow the rows")
            if b_.state.slots_left != a_.state.slots_left - int(ea == "E1"):
                V("counters", key, b_.identity.step_index, "slots_left does not follow the rows")
        for t in traj:
            if t.state.slots_left > t.env.llm_cap:
                V("counters", key, t.identity.step_index, "slots_left exceeds llm_cap")
        if is_root and steps[0] == 0 and (first.state.keeps_so_far or first.state.prior_skips
                                          or first.state.slots_left != first.env.llm_cap):
            V("counters", key, 0, "a root starts with keeps_so_far == prior_skips == 0 and all slots")
        for a_, b_ in zip(traj, traj[1:]):
            changes = (a_.identity.epoch == "E2" and a_.action.action == "keep") or \
                      a_.action.action in ("reaudit", "select")
            if not changes and (b_.state.incumbent_recorded, b_.state.incumbent_obs) != \
                    (a_.state.incumbent_recorded, a_.state.incumbent_obs):
                V("counters", key, b_.identity.step_index,
                  "incumbent_recorded / incumbent_obs change without a keep, reaudit or selection")

        # epoch sequence
        last = traj[-1]
        terminated = last.episode_end is not None and last.episode_end.kind == "terminated"
        if is_root and first.identity.epoch != "E1":
            V("epoch_sequence", key, first.identity.step_index, "a root starts at E1")
        pending = None          # the execute row awaiting its E2
        meas = []               # the candidate's measurements so far (execute, then verify rows)
        for i, t in enumerate(traj):
            ep, act = t.identity.epoch, t.action.action
            st = t.identity.step_index
            if ep == "final" and t is not last:
                V("epoch_sequence", key, st, "final appears only as the last row")
            if ep in ("verify", "E2"):
                if pending is None and i > 0:
                    V("epoch_sequence", key, st, f"{ep} row without a preceding execute")
                if pending is not None:
                    latest = meas[-1].outcome
                    if t.state.candidate_hash != pending.state.candidate_hash:
                        V("epoch_sequence", key, st, f"{ep} row is about another candidate than its execute")
                    bad = latest.divergent or latest.failure_category is not None
                    if ep == "E2" and bad and act != "discard":
                        V("epoch_sequence", key, st, "a divergent or invalid candidate must be discarded")
                    if t.state.candidate_divergent != latest.divergent:
                        V("epoch_sequence", key, st, "state.candidate_divergent disagrees with the latest measurement")
                    if t.state.candidate_invalid != (latest.failure_category is not None):
                        V("epoch_sequence", key, st, "state.candidate_invalid disagrees with the latest measurement")
                    if t.state.candidate_obs != len(meas):
                        V("epoch_sequence", key, st, f"state.candidate_obs should be {len(meas)}")
                    if not bad and len(meas) == 1 and t.state.candidate_delta_hat != latest.delta_hat:
                        V("epoch_sequence", key, st, "state.candidate_delta_hat disagrees with the execute")
                if ep == "verify" and act == "verify" and pending is not None:
                    meas.append(t)
                if ep == "E2":
                    pending, meas = None, []
            elif ep == "E1":
                if pending is not None:
                    V("epoch_sequence", key, st, "an executed candidate has no E2 row")
                pending = t if act == "execute" else None
                meas = [t] if act == "execute" else []
            elif ep in ("reaudit", "final") and pending is not None:
                V("epoch_sequence", key, st, f"{ep} row between an execute and its E2")
        if pending is not None and terminated:     # a missing episode_end is reported by the terminal check
            V("epoch_sequence", key, pending.identity.step_index, "an executed candidate has no E2 row")

        if last.identity.epoch == "final" and last.state.candidates:
            cands = last.state.candidates
            if len({c.hash for c in cands}) != len(cands):
                V("epoch_sequence", key, last.identity.step_index, "state.candidates: duplicate hashes")
            record, k = {}, key            # hash -> (recorded, obs) it last had as the incumbent, ancestors first
            chain = []
            while k in groups:
                chain.append(k)
                if not k[1]:
                    break
                k = (k[0], k[1][:-1])
            for kk in reversed(chain):
                child_first = None if kk == key else \
                    min(r.identity.step_index for r in groups[chain[chain.index(kk) - 1]])
                for t in sorted(groups[kk], key=lambda r: r.identity.step_index):
                    if child_first is not None and t.identity.step_index >= child_first:
                        break
                    record[t.state.incumbent_hash] = (t.state.incumbent_recorded, t.state.incumbent_obs)
            for c in cands:
                if c.hash not in record:
                    V("epoch_sequence", key, last.identity.step_index,
                      f"state.candidates: {c.hash!r} was never the incumbent")
                    continue
                rec, obs = record[c.hash]
                if obs != c.obs or (rec is None) != (c.recorded is None) or \
                        (rec is not None and abs(rec - c.recorded) > FLOAT_TOL * max(1.0, abs(rec))):
                    V("epoch_sequence", key, last.identity.step_index,
                      f"state.candidates: {c.hash!r} does not carry the record it last had as the incumbent")

        if last.identity.epoch == "final" and last.action.selected is not None:
            seen, k = set(), key
            while k in groups:
                for t in groups[k]:
                    seen.update(h for h in (t.state.incumbent_hash, t.state.candidate_hash) if h)
                if not k[1]:
                    break
                k = (k[0], k[1][:-1])
            if last.action.selected not in seen:
                V("epoch_sequence", key, last.identity.step_index, "final selection names a configuration never "
                                                                   "seen in the campaign")

        # terminal
        for t in traj[:-1]:
            if t.episode_end is not None:
                V("terminal", key, t.identity.step_index, "episode_end before the last row")
            if t.terminal is not None:
                V("terminal", key, t.identity.step_index, "terminal before the last row")
        ls, lo_ = last.state, last.outcome
        if last.episode_end is None:
            V("terminal", key, last.identity.step_index, "last row has no episode_end")
        elif last.episode_end.kind == "terminated":
            if last.terminal is None:
                V("terminal", key, last.identity.step_index, "terminated trajectory has no terminal")
            run_cost = int(last.env.constants.get("run_cost", 1))
            if last.episode_end.reason == "W" and last.env.W - (ls.runs_used + lo_.runs_consumed) >= run_cost:
                V("terminal", key, last.identity.step_index, "terminated at W but a run can still be paid")
            if last.episode_end.reason == "llm_cap" and ls.calls_used + lo_.calls_consumed != last.env.llm_cap:
                V("terminal", key, last.identity.step_index, "terminated at llm_cap but calls remain")
        elif last.terminal is not None:
            V("terminal", key, last.identity.step_index, "truncated trajectory has a terminal")

        for t in traj:
            st = t.identity.step_index
            if t.fork is not None:
                d = t.fork
                ok_rule = {"uniform": d.uniform and not d.oversample,
                           "oversample": d.oversample and not d.uniform,
                           "both": d.uniform and d.oversample}[d.selection_rule]
                if not (0.0 < d.p_select <= 1.0) or abs(d.p_select - _p_select(d)) > FLOAT_TOL:
                    V("design_weight", key, st, f"p_select {d.p_select} != recomputed {_p_select(d):.12g}")
                if not ok_rule or (d.oversample and not d.near_threshold):
                    V("design_weight", key, st, "selection flags inconsistent with selection_rule / near_threshold")
            if behaviour is not None and not t.action.forced and not t.state.rule_forced:
                res = behaviour(_view(t))
                act, prob = res if isinstance(res, tuple) and len(res) == 2 else (None, None)
                if not isinstance(prob, (int, float)) or isinstance(prob, bool) or not math.isfinite(prob):
                    V("propensity", key, st, f"replay returned an invalid probability {prob!r}")
                elif act != t.action.action or abs(prob - (t.policy.action_prob or 0.0)) > FLOAT_TOL:
                    V("propensity", key, st, f"replay gave ({act}, {prob}) vs logged "
                                             f"({t.action.action}, {t.policy.action_prob})")
            if registry is not None:
                seeds_to_check = [("instance_seed", t.seeds.instance_seed), ("worker_seed", t.seeds.worker_seed),
                                  ("eps_seed", t.policy.eps_seed)]
                if hasattr(registry, "paper_b_range") and len(t.seeds.audit_seed_block) == 2:
                    hit = registry.paper_b_range(*t.seeds.audit_seed_block)
                    if hit is not None:
                        V("seed", key, st, f"audit_seed_block {t.seeds.audit_seed_block} intersects Paper B "
                                           f"block {hit}")
                else:
                    seeds_to_check += [("audit_seed_block", x) for x in t.seeds.audit_seed_block]
                if t.terminal is not None:
                    seeds_to_check += [("terminal.audit_seeds", x) for x in t.terminal.audit_seeds]
                for name, val in seeds_to_check:
                    if val is None:
                        continue
                    hit = registry.paper_b_block(t.identity.node, val)
                    if hit is not None:
                        V("seed", key, st, f"{name} {val} lies in Paper B block {hit}")
                # Paper C membership (when the registry offers it): every seed inside its own Paper C block
                pc = getattr(registry, "paper_c_check", None)
                if pc is not None:
                    roles = [("instance", t.seeds.instance_seed, None), ("worker", t.seeds.worker_seed, None),
                             ("eps", t.policy.eps_seed, None)]
                    if len(t.seeds.audit_seed_block) == 2:
                        roles.append(("audit", *t.seeds.audit_seed_block))
                    for role, lo, hi in roles:
                        if lo is not None:
                            msg = pc(role, lo, hi)
                            if msg:
                                V("seed", key, st, msg)
                    if t.identity.tier != "E-SYN" and t.seeds.worker_seed is None:
                        V("seed", key, st, "worker_seed must be explicit on real-node rows (None means the node's "
                                           "default seed 42, a Paper B seed)")
                prefix = getattr(registry, "campaign_prefix", None)
                if prefix and not t.identity.campaign_id.startswith(prefix):
                    V("seed", key, st, f"campaign_id {t.identity.campaign_id!r} lacks the Paper C prefix {prefix!r}")
    return out
