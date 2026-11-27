"""CPU learners for E-SYN Round B (P8). ENGINEERING_ONLY.

N6 fits total fork differences for one declared continuation. R0 uses
finite-horizon fitted Q iteration with tree regressors and gamma=1.
R1 uses a small CPU IQL network with expectile regression, a lagged
double critic, and advantage-weighted behavioural cloning.

Algorithm references are Ernst et al. (2005), https://www.jmlr.org/papers/v6/ernst05a.html
and Kostrikov et al. (2021), https://arxiv.org/abs/2110.06169.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Callable

import numpy as np

from paperc import forks, ope


def stage(obs):
    return 2 * (obs["llm_cap"] - obs["slots_left"]) - int(obs["epoch"] == "E2")


def features(obs, scale, *, eligible=True):
    """Shared legal observation with both resources, their scales, and the epoch."""
    return [obs["runs_left"] / obs["W"], obs["slots_left"] / obs["llm_cap"],
            obs["calls_left"] / obs["llm_cap"],
            *[(obs[key] or 0.0) / scale for key in ("v_star", "m_hat", "tau", "sigma")],
            float(obs["epoch"] == "E2"), float(eligible)]


def _rows(batch, scale):
    return np.asarray([features(o, scale, eligible=bool(e)) for o, e in zip(batch.obs, batch.eligible)])


def _digest(*values):
    h = hashlib.sha256()
    for value in values:
        if isinstance(value, str):
            h.update(value.encode() + b"\0")
        else:
            a = np.asarray(value)
            h.update(str((a.shape, a.dtype)).encode() + b"\0" + a.tobytes())
    return h.hexdigest()[:16]


@dataclass(frozen=True)
class LearnedPolicy:
    method: str
    sha: str
    scale: float
    predict: Callable
    stochastic = False
    version = "p8/v1"

    @property
    def name(self):
        return f"{self.method.lower()}:{self.sha}"

    def actions(self, x, stages):
        return np.asarray(self.predict(x, stages), dtype=int)

    def act(self, obs):
        x = np.asarray([features(obs, self.scale)])
        action = self.actions(x, np.asarray([stage(obs)]))[0]
        return ope.ACTIONS[obs["epoch"]][action], 1.0, None

    def probabilities_on(self, batch):
        result = np.eye(2)[batch.actions]
        idx = np.flatnonzero(batch.eligible)
        if len(idx):
            result[idx] = np.eye(2)[self.actions(_rows(batch, self.scale)[idx], batch.stages[idx])]
        return result


@dataclass(frozen=True)
class ForkTraining:
    indices: np.ndarray   # rows in the checked and replayed training batch
    differences: np.ndarray


@dataclass(frozen=True)
class N6Config:
    alpha: float


@dataclass(frozen=True)
class FQIConfig:
    leaves: int
    rounds: int


@dataclass(frozen=True)
class IQLConfig:
    expectile: float
    inverse_temperature: float
    width: int = 32
    critic_steps: int = 3200
    actor_steps: int = 1200


def _fork_arrays(train, data):
    idx = np.asarray(data.indices)
    diff = np.asarray(data.differences, dtype=float)
    if (idx.ndim != 1 or idx.shape != diff.shape or idx.dtype.kind not in "iu"
            or np.any(idx < 0) or np.any(idx >= len(train.obs)) or len(np.unique(idx)) != len(idx)
            or not np.isfinite(diff).all() or not train.eligible[idx].all()):
        raise ValueError("N6 needs finite fork differences aligned to unique eligible training rows")
    return idx, diff


def fit_n6(train, data: ForkTraining, config: N6Config, *, scale):
    """Unweighted per-epoch ridge on Q(1)-Q(0), followed by one greedy step."""
    idx, diff = _fork_arrays(train, data)
    x = _rows(train, scale)[idx]
    epochs = train.stages[idx] % 2
    fits = {}
    for epoch in (0, 1):
        mask = epochs == epoch
        if not mask.any():
            raise ValueError("N6 needs forks in both epochs")
        fits[epoch] = forks._ridge_fit(x[mask], diff[mask] / scale, config.alpha)

    def predict(obs, stages):
        acts = np.empty(len(obs), dtype=int)
        for epoch, model in fits.items():
            mask = (stages % 2) == epoch
            acts[mask] = forks._ridge_predict(model, obs[mask]) > 0
        return acts

    sha = _digest(*(a for model in fits.values() for a in model))
    return LearnedPolicy("N6", sha, scale, predict)


def rewards(batch, *, shaped):
    """Potential differences from accumulated keep forecasts, zero at absorption."""
    result = batch.rewards.copy()
    if shaped:
        kept = np.asarray([o["epoch"] == "E2" and a == 1 for o, a in zip(batch.obs, batch.actions)])
        gains = np.asarray([(o["m_hat"] or 0.0) if k else 0.0 for o, k in zip(batch.obs, kept)])
        result += gains
        result[batch.ends] -= np.add.reduceat(gains, batch.starts)
    return result


def successors(batch):
    idx = np.arange(len(batch.obs)) + 1
    idx[batch.ends] = len(batch.obs)  # index of an absorbing state with value zero
    return idx


def fit_r0(train, config: FQIConfig, *, scale, seed, shaped=False):
    """Backward FQI over decision stages with a supported-action Bellman maximum."""
    from lightgbm import Dataset, train as train_tree

    x = _rows(train, scale)
    r = rewards(train, shaped=shaped) / scale
    nxt = successors(train)
    v = np.zeros(len(x) + 1)
    models, action_support = {}, {}
    for s in np.unique(train.stages)[::-1]:
        idx = np.flatnonzero(train.stages == s)
        a = train.actions[idx]
        model = train_tree(
            {"objective": "regression", "device_type": "cpu", "num_threads": 1, "verbosity": -1,
             "seed": seed, "deterministic": True, "force_col_wise": True, "num_leaves": config.leaves,
             "min_data_in_leaf": 12, "learning_rate": 0.10, "lambda_l2": 1.0},
            Dataset(ope._design(x[idx], a), label=r[idx] + v[nxt[idx]]), num_boost_round=config.rounds,
        )
        legal = np.unique(a[train.eligible[idx]])
        models[int(s)], action_support[int(s)] = model, legal
        q = ope._action_values(lambda z: model.predict(z, num_threads=1), x[idx])
        forced = ~train.eligible[idx]
        v[idx[forced]] = q[forced, a[forced]]
        if len(legal):
            v[idx[~forced]] = np.max(q[~forced][:, legal], axis=1)

    def predict(obs, stages):
        acts = np.empty(len(obs), dtype=int)
        for s in np.unique(stages):
            if s not in models or len(action_support[s]) == 0:
                raise ValueError(f"insufficient data at FQI stage {s}")
            mask = stages == s
            legal = action_support[s]
            q = ope._action_values(lambda z: models[s].predict(z, num_threads=1), obs[mask])
            acts[mask] = legal[np.argmax(q[:, legal], axis=1)]
        return acts

    sha = _digest(*(model.model_to_string() for model in models.values()))
    return LearnedPolicy("R0", sha, scale, predict)


def expectile_loss(residual, expectile):
    """Asymmetric squared loss for residual Q_target - V."""
    import torch

    return (torch.where(residual > 0, expectile, 1 - expectile) * residual.square()).mean()


def fit_r1(train, config: IQLConfig, *, scale, seed, shaped=False):
    """CPU double-critic IQL, evaluated with the mode of the extracted actor."""
    from copy import deepcopy
    import torch
    from torch import nn

    x = torch.as_tensor(_rows(train, scale), dtype=torch.float32, device="cpu")
    # The absorbing feature row is never queried for a bootstrap.
    x_next = torch.cat((x, torch.zeros((1, x.shape[1]), device="cpu")), dim=0)
    nxt = torch.as_tensor(successors(train), device="cpu")
    r = torch.as_tensor(rewards(train, shaped=shaped) / scale, dtype=torch.float32, device="cpu")
    a = torch.as_tensor(train.actions, device="cpu")
    actor_rows = torch.as_tensor(np.flatnonzero(train.eligible), device="cpu")
    generator = torch.Generator(device="cpu").manual_seed(seed)

    def network(out):
        return nn.Sequential(nn.Linear(x.shape[1], config.width, device="cpu"), nn.ReLU(),
                             nn.Linear(config.width, config.width, device="cpu"), nn.ReLU(),
                             nn.Linear(config.width, out, device="cpu"))

    def selected(q, indices):
        return q(x[indices]).gather(1, a[indices, None]).squeeze(1)

    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        q1, q2, val, actor = network(2), network(2), network(1), network(2)
    target1, target2 = deepcopy(q1).requires_grad_(False), deepcopy(q2).requires_grad_(False)
    q_opt = torch.optim.Adam([*q1.parameters(), *q2.parameters()], lr=0.001)
    v_opt = torch.optim.Adam(val.parameters(), lr=0.001)
    actor_opt = torch.optim.Adam(actor.parameters(), lr=0.001)

    for _ in range(config.critic_steps):
        ix = torch.randint(len(x), (256,), generator=generator, device="cpu")
        with torch.no_grad():
            q_min = torch.minimum(selected(target1, ix), selected(target2, ix))
        v_opt.zero_grad()
        expectile_loss(q_min - val(x[ix]).squeeze(1), config.expectile).backward()
        v_opt.step()
        with torch.no_grad():
            bootstrap = val(x_next[nxt[ix]]).squeeze(1)
            target = r[ix] + torch.where(nxt[ix] < len(x), bootstrap, 0.0)
        q_opt.zero_grad()
        loss = (selected(q1, ix) - target).square().mean() + (selected(q2, ix) - target).square().mean()
        loss.backward()
        q_opt.step()
        with torch.no_grad():
            for lagged, current in zip([*target1.parameters(), *target2.parameters()],
                                       [*q1.parameters(), *q2.parameters()]):
                lagged.lerp_(current, 0.01)

    for _ in range(config.actor_steps):
        ix = actor_rows[torch.randint(len(actor_rows), (256,), generator=generator, device="cpu")]
        with torch.no_grad():
            q_min = torch.minimum(selected(target1, ix), selected(target2, ix))
            advantage = q_min - val(x[ix]).squeeze(1)
            weight = torch.exp(torch.clamp(config.inverse_temperature * advantage, max=np.log(100.0)))
        actor_opt.zero_grad()
        loss = (weight * nn.functional.cross_entropy(actor(x[ix]), a[ix], reduction="none")).mean()
        loss.backward()
        actor_opt.step()

    actor.eval()

    def predict(obs, stages):
        with torch.inference_mode():
            return actor(torch.as_tensor(obs, dtype=torch.float32, device="cpu")).argmax(1).numpy()

    sha = _digest(*(value.detach().numpy() for value in actor.state_dict().values()))
    return LearnedPolicy("R1", sha, scale, predict)


def _uniform_actions(batch):
    p = np.eye(2)[batch.actions]
    p[batch.eligible] = 0.5
    return p


def prefit_support(train, screen, cluster):
    """Audit both legal actions before fitting any of the three learners."""
    if train.context != screen.context or set(train.instances) & set(screen.instances):
        raise ValueError("learner train and screen need the same context and disjoint roots")
    return ope.support_diagnostics(train, screen, _uniform_actions(screen), cluster,
                                   train_target_p=_uniform_actions(train))


def fit_supported(method, train, screen, config, *, scale, seed, cluster, fork_data=None, shaped=False):
    """Return a candidate only if the logging and candidate support checks pass."""
    initial = prefit_support(train, screen, cluster)
    receipt = {"prefit": initial, "candidate": None}
    if initial["status"] != "meets thresholds":
        return None, receipt
    if method == "N6":
        indices = np.empty(0, dtype=int) if fork_data is None else _fork_arrays(train, fork_data)[0]
        labelled_stages = set(train.stages[indices])
        labelled_clusters = {(train.obs[i]["epoch"], cluster(train.obs[i])) for i in indices}
        missing_stages = (set(train.stages[train.eligible]) | set(screen.stages[screen.eligible])) - labelled_stages
        required_clusters = {(obs["epoch"], cluster(obs)) for batch in (train, screen)
                             for obs, eligible in zip(batch.obs, batch.eligible) if eligible}
        missing_clusters = required_clusters - labelled_clusters
        status = "insufficient data" if missing_stages or missing_clusters else "meets thresholds"
        receipt["fork_labels"] = {"status": status, "n": len(indices),
                                  "missing_stages": sorted(map(int, missing_stages)),
                                  "missing_clusters": sorted(map(repr, missing_clusters))}
        if status == "insufficient data":
            return None, receipt
        policy = fit_n6(train, fork_data, config, scale=scale)
    else:
        fitter = {"R0": fit_r0, "R1": fit_r1}[method]
        policy = fitter(train, config, scale=scale, seed=seed, shaped=shaped)
    check = ope.support_diagnostics(train, screen, policy.probabilities_on(screen), cluster,
                                   train_target_p=policy.probabilities_on(train))
    receipt["candidate"] = check
    return (policy if check["status"] == "meets thresholds" else None), receipt
