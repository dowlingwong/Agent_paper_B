"""Round-B off-policy evaluation on complete root campaigns (P7, plan §6.1).

ENGINEERING_ONLY. Finite-horizon FQE follows Le, Voloshin and Yue (2019),
https://proceedings.mlr.press/v97/le19a.html. The per-decision WDR check
uses Thomas and Brunskill (2016), https://proceedings.mlr.press/v48/thomasa16.html.

Campaign-level mixture logging requires a history-conditional denominator.
Updating component weights by the observed action likelihood at every step
makes the product of marginal denominators the mixture trajectory likelihood
(balance heuristic). Rule steps have likelihood one. The audited terminal
difference is the only reward. FQE backs it up by remaining proposal slot and
epoch, with gamma=1. A zero WDR weight sum ends the correction at that step,
which is reported explicitly. Support cutoffs screen estimates and do not
guarantee support in states absent from the behaviour data.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Hashable, Sequence

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from paperc import schema
from paperc.esyn import sim

ACTIONS = {"E1": ("skip", "execute"), "E2": ("discard", "keep")}
FEATURES = ("runs_left", "slots_left", "calls_left", "keeps_so_far", "incumbent_obs",
            "candidate_obs", "key_seen", "v_star", "m_hat", "tau", "sigma", "candidate_delta_hat")


class OPEError(ValueError):
    pass


@dataclass(frozen=True)
class EpsilonPolicy:
    """Replayable epsilon-greedy wrapper for the P4 binary policy interface."""

    base: object
    eps: float
    component: str

    def __post_init__(self):
        if not 0 <= self.eps <= 1 or getattr(self.base, "stochastic", False):
            raise OPEError("epsilon requires a deterministic base policy and a rate in [0, 1]")
        if getattr(self.base, "privileged", False):
            raise OPEError("OPE uses non-privileged policies")

    @property
    def name(self):
        return f"ope:{self.component}"

    @property
    def stochastic(self):
        return self.eps > 0

    def probabilities(self, obs):
        return self.eps / 2 + (1 - self.eps) * policy_probabilities(self.base, obs)

    def act(self, obs):
        p = self.probabilities(obs)
        arm = int(obs["u"] >= p[0]) if self.stochastic else int(p[1] == 1)
        return ACTIONS[obs["epoch"]][arm], float(p[arm]), None


def policy_probabilities(policy, obs) -> np.ndarray:
    if getattr(policy, "privileged", False):
        raise OPEError("OPE uses non-privileged policies")
    if hasattr(policy, "probabilities"):
        p = np.asarray(policy.probabilities(obs), dtype=float)
    else:
        if getattr(policy, "stochastic", False):
            raise OPEError("stochastic targets must provide an action probability vector")
        action, prob, _ = policy.act(obs)
        actions = ACTIONS[obs["epoch"]]
        if prob != 1 or action not in actions:
            raise OPEError(f"invalid deterministic action {action!r} at {obs['epoch']}")
        p = np.asarray([action == arm for arm in actions], dtype=float)
    if p.shape != (2,) or not np.isfinite(p).all() or np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise OPEError("policy probabilities must give a finite binary distribution")
    return p


@dataclass(frozen=True)
class CampaignMixture:
    """Component probabilities before the campaign, in declared component order."""

    components: tuple[EpsilonPolicy, ...]
    priors: tuple[float, ...]

    def __post_init__(self):
        names = {p.component for p in self.components}
        weights = np.asarray(self.priors, dtype=float)
        if (not names or len(names) != len(self.components) or weights.shape != (len(names),)
                or not np.isfinite(weights).all() or np.any(weights <= 0) or not np.isclose(weights.sum(), 1)):
            raise OPEError("mixture needs distinct components with positive priors summing to one")

    def probabilities(self, obs) -> np.ndarray:
        return np.stack([p.probabilities(obs) for p in self.components])


@dataclass(frozen=True)
class Batch:
    obs: tuple[dict, ...]
    ids: tuple[str, ...]
    instances: tuple[str, ...]
    starts: np.ndarray
    lengths: np.ndarray
    features: np.ndarray
    stages: np.ndarray
    actions: np.ndarray
    eligible: np.ndarray
    behaviour: np.ndarray
    rewards: np.ndarray
    context: tuple

    @property
    def ends(self):
        return self.starts + self.lengths - 1

    def target(self, policy):
        p = np.eye(2)[self.actions]
        for i in np.flatnonzero(self.eligible):
            p[i] = policy_probabilities(policy, self.obs[i])
        return p


def load_campaigns(rows: Sequence, mixture: CampaignMixture, *, belief="a2u") -> Batch:
    """Build an OPE batch from complete, single-context E1/E2 root records.

    Requires a known root-level mixture and component probabilities. Fork
    contrasts use the existing design-weighted `forks.fork_means` API.
    """
    if not rows:
        raise OPEError("OPE requires root records")
    defects = schema.check_campaign(rows)
    if defects:
        raise OPEError(f"invalid campaign records: {defects[0]}")
    groups = defaultdict(list)
    for row in rows:
        t = row if isinstance(row, schema.Transition) else schema.from_dict(row)
        if t.identity.branch_path or t.action.forced or t.fork is not None:
            raise OPEError("forks and interventions require design weights")
        if t.identity.epoch not in ACTIONS:
            raise OPEError("P7 supports E1/E2 campaigns")
        groups[t.identity.campaign_id].append(t)

    component = {p.component: i for i, p in enumerate(mixture.components)}
    contexts, instances, all_obs, offsets, lengths = [], [], [], [], []
    features, stages, actions, eligible, behaviour, rewards = [], [], [], [], [], []
    for cid, trajectory in sorted(groups.items()):
        trajectory.sort(key=lambda t: t.identity.step_index)
        first, last = trajectory[0], trajectory[-1]
        if last.terminal is None or last.episode_end is None or last.episode_end.kind != "terminated":
            raise OPEError(f"{cid}: complete terminated campaign required")
        if last.terminal.y_start is None or not np.isfinite([last.terminal.y_terminal, last.terminal.y_start]).all():
            raise OPEError(f"{cid}: finite paired terminal reward required")
        contexts.append((first.identity.node, first.env))
        instances.append(first.identity.instance_id)
        name = first.policy.behaviour_component
        if name not in component:
            raise OPEError(f"{cid}: unknown behaviour component {name!r}")
        k = component[name]
        member = mixture.components[k]
        posterior = np.asarray(mixture.priors, dtype=float)
        offsets.append(len(all_obs))
        lengths.append(len(trajectory))
        for j, t in enumerate(trajectory):
            ep = t.identity.epoch
            if (t.policy.behaviour_component != name or t.policy.policy != first.policy.policy
                    or t.policy.policy_sha != first.policy.policy_sha or t.policy.eps != member.eps):
                raise OPEError(f"{cid}: behaviour component, policy and epsilon must be constant")
            a = ACTIONS[ep].index(t.action.action)
            obs = sim.obs_from_state(ep, t.state, t.env)
            obs["bonus"] = 0.0
            f = t.state.forecasts.get(belief)
            obs.update({field: getattr(f, field) if f else None for field in ("v_star", "m_hat", "tau", "sigma")})
            decision = t.state.eligible and not t.state.rule_forced
            if decision:
                required = ("v_star", "tau", "sigma") if ep == "E1" else ("m_hat", "tau", "sigma")
                if any(obs[field] is None for field in required):
                    raise OPEError(f"{cid}: eligible {ep} is missing forecasts for {belief!r}")
                likelihoods = mixture.probabilities(obs)
                p = posterior @ likelihoods
                if likelihoods[k, a] <= 0 or t.policy.action_prob is None or not np.isclose(
                        likelihoods[k, a], t.policy.action_prob, rtol=0, atol=1e-10):
                    raise OPEError(f"{cid}: logged component propensity disagrees at step {j}")
                posterior = posterior * likelihoods[:, a] / p[a]
            else:
                if not t.state.rule_forced or t.policy.action_prob != 1:
                    raise OPEError(f"{cid}: ineligible steps must be common rules with probability one")
                p = np.eye(2)[a]
            vector = [0.0 if obs[field] is None else float(obs[field]) for field in FEATURES]
            if not np.isfinite(vector).all():
                raise OPEError(f"{cid}: non-finite feature at step {j}")
            stage = 2 * (t.env.llm_cap - t.state.slots_left) - int(ep == "E2")
            if stage < 0 or stage >= 2 * t.env.llm_cap or (j and stage <= stages[-1]):
                raise OPEError(f"{cid}: invalid E1/E2 proposal order")
            all_obs.append(obs)
            features.append([*vector, float(decision)])
            stages.append(stage)
            actions.append(a)
            eligible.append(decision)
            behaviour.append(p)
            rewards.append(0.0)
        rewards[-1] = last.terminal.y_terminal - last.terminal.y_start
    if any(context != contexts[0] for context in contexts[1:]):
        raise OPEError("OPE batches require a common node and environment context")
    return Batch(tuple(all_obs), tuple(sorted(groups)), tuple(instances), np.array(offsets), np.array(lengths),
                 np.array(features), np.array(stages), np.array(actions), np.array(eligible),
                 np.array(behaviour), np.array(rewards), contexts[0])


def _design(features, action):
    a = np.broadcast_to(action, (len(features),))[:, None]
    return np.column_stack((features, a, features * a))


def _regress(method, x, y, seed):
    if method == "linear":
        model = make_pipeline(StandardScaler(), Ridge(alpha=2.0))
        return model.fit(x, y).predict
    if method != "lightgbm":
        raise OPEError(f"unknown FQE model {method!r}")
    from lightgbm import Dataset, train
    model = train({
        "objective": "regression", "device_type": "cpu", "num_threads": 1, "verbosity": -1,
        "seed": seed, "deterministic": True, "force_col_wise": True, "num_leaves": 7,
        "min_data_in_leaf": 8, "learning_rate": 0.10, "lambda_l2": 1.0,
    }, Dataset(x, label=y), num_boost_round=24)
    return lambda z: model.predict(z, num_threads=1)


def _action_values(predict, features):
    return predict(np.vstack((_design(features, 0), _design(features, 1)))).reshape(2, -1).T


def _fqe(train, target, *, method, seed):
    """One regressor per stage, fitted in backward topological order."""
    p = train.target(target)
    v = np.zeros(len(train.obs) + 1)
    successor = np.arange(len(train.obs)) + 1
    successor[train.ends] = len(train.obs)
    models = {}
    for s in np.unique(train.stages)[::-1]:
        idx = np.flatnonzero(train.stages == s)
        x = train.features[idx]
        y = train.rewards[idx] + v[successor[idx]]
        predict = _regress(method, _design(x, train.actions[idx]), y, seed)
        models[int(s)] = predict
        v[idx] = (p[idx] * _action_values(predict, x)).sum(axis=1)
    return models


def effective_size(w):
    w = np.asarray(w, dtype=float)
    total = w.sum()
    return float(total ** 2 / (w @ w)) if total else 0.0


def support_diagnostics(train: Batch, evaluation: Batch, target_p: np.ndarray,
                        cluster: Callable[[dict], Hashable], *, min_action=30, min_ess=200):
    counts = defaultdict(lambda: np.zeros(2, dtype=int))
    for i in np.flatnonzero(train.eligible):
        ob = train.obs[i]
        counts[ob["epoch"], cluster(ob)][train.actions[i]] += 1
    idx = np.flatnonzero(evaluation.eligible)
    cells = {(evaluation.obs[i]["epoch"], cluster(evaluation.obs[i])) for i in idx}
    for cell in cells:
        counts[cell]  # include cells encountered only in evaluation
    action_counts = [{"epoch": ep, "cluster": repr(group), "action": ACTIONS[ep][a], "count": int(n)}
                     for (ep, group), ns in sorted(counts.items(), key=lambda item: repr(item[0]))
                     for a, n in enumerate(ns)]
    failures = [cell for cell in action_counts if cell["count"] < min_action]
    unsupported = int(np.count_nonzero(np.any((target_p[idx] > 0) & (evaluation.behaviour[idx] == 0), axis=1)))
    a = evaluation.actions[idx]
    ess = effective_size(target_p[idx, a] / evaluation.behaviour[idx, a])
    return {"status": "insufficient data" if failures or unsupported or ess < min_ess else "meets thresholds",
            "action_counts": action_counts, "action_shortfalls": failures, "n_clusters": len(counts), "min_action": min_action,
            "ess": ess, "min_ess": min_ess, "n_evaluation_decisions": len(idx),
            "zero_propensity_target_rows": unsupported}


def _weighted_dr(batch: Batch, target_p, q):
    """Weighted TD corrections, using absorbing padding for finished campaigns."""
    a = batch.actions
    steps = np.arange(len(a))
    v = np.sum(target_p * q, axis=1)
    successor_value = np.r_[v[1:], 0.0]
    successor_value[batch.ends] = 0.0
    residual = batch.rewards + successor_value - q[steps, a]
    with np.errstate(divide="ignore"):
        increments = np.log(target_p[steps, a]) - np.log(batch.behaviour[steps, a])
    n, horizon = len(batch.ids), int(batch.lengths.max())
    log_weights = np.empty((n, horizon))
    errors = np.zeros((n, horizon))
    alive = np.arange(horizon) < batch.lengths[:, None]
    for j, (start, length) in enumerate(zip(batch.starts, batch.lengths)):
        stop = start + length
        prefix = np.cumsum(increments[start:stop])
        log_weights[j, :length] = prefix
        log_weights[j, length:] = prefix[-1]
        errors[j, :length] = residual[start:stop]
    value = float(v[batch.starts].mean())
    ess, live_ess, exhausted = [], [], []
    for t, logw in enumerate(log_weights.T):
        if np.isneginf(logw).all():
            exhausted.append(t)
            ess.append(0.0)
            live_ess.append(0.0)
            continue
        w = np.exp(logw - logw.max())
        ess.append(effective_size(w))
        live_ess.append(effective_size(w[alive[:, t]]))
        value += float((w @ errors[:, t]) / w.sum())
    return {"value": value, "ess_by_step": ess, "live_ess_by_step": live_ess, "zero_weight_steps": exhausted}


def evaluate(train: Batch, evaluation: Batch, target, *, method: str, cluster, seed: int) -> dict:
    """A held-out FQE screen and WDR check for one specified policy."""
    if train.context != evaluation.context:
        raise OPEError("training and evaluation must use the same context")
    if set(train.instances) & set(evaluation.instances):
        raise OPEError("training and evaluation must use disjoint root instances")
    p = evaluation.target(target)
    support = support_diagnostics(train, evaluation, p, cluster)
    missing = sorted(set(evaluation.stages) - set(train.stages))
    if missing:
        support["status"] = "insufficient data"
        return {"fqe": None, "wdr": None, "support": support, "unfitted_stages": [int(s) for s in missing]}
    models = _fqe(train, target, method=method, seed=seed)
    q = np.empty_like(p)
    for stage in np.unique(evaluation.stages):
        rows = evaluation.stages == stage
        q[rows] = _action_values(models[stage], evaluation.features[rows])
    return {"fqe": float(np.sum(p[evaluation.starts] * q[evaluation.starts], axis=1).mean()),
            "wdr": _weighted_dr(evaluation, p, q), "support": support, "unfitted_stages": []}


def ipw_population_contrast(outcome, action, behaviour) -> float:
    """HT mean outcome contrast arm 1 minus arm 0 on a common state population.

    Pass one reward and one logged action per state, and the two marginal
    action probabilities at each state. This is a single-decision contrast.
    """
    y, a, p = np.asarray(outcome, float), np.asarray(action), np.asarray(behaviour, float)
    if (y.ndim != 1 or not y.size or a.shape != y.shape or p.shape != (len(y), 2)
            or not np.isfinite(y).all() or not np.isfinite(p).all() or not np.isin(a, (0, 1)).all()
            or np.any(p <= 0) or not np.allclose(p.sum(axis=1), 1)):
        raise OPEError("IPW requires a finite binary contrast with positive probabilities for both arms")
    a = a.astype(int)
    return float(np.mean(y * (2 * a - 1) / p[np.arange(len(y)), a]))
