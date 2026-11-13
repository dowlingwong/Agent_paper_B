"""Track P Stage D (DAgger) on synthetic environments only: no label table, audit or seed 7001-7010."""
import numpy as np
import pytest

from r1.c3.features import FEATURES
from r1.c3.train import dagger as D


class SyntheticCampaign:
    """A campaign of W proposals whose later states depend on earlier decisions.

    State: (quality q of the proposal, budget fraction left). The expert executes iff q > threshold(budget left),
    with a threshold that rises as budget runs out; executing consumes budget, so a configurator that executes too
    much visits low-budget states the expert's own rollouts rarely reach.
    """

    def __init__(self, seed: int, W: int = 10):
        self.rng = np.random.default_rng(D.check_synthetic_seed(seed))
        self.W = W

    @staticmethod
    def expert_action(state, label=None):
        q, left = state["obs"]
        return bool(q > 0.2 + 0.6 * (1.0 - left))

    def rollout(self, decide, instances: int, tag: str):
        states = []
        for i in range(instances):
            left = 1.0
            for t in range(self.W):
                q = float(self.rng.uniform(-1, 1))
                s = {"key": f"{tag}-{i}-{t}", "obs": (q, left)}
                states.append(s)
                if decide(s):
                    left = max(left - 1.0 / self.W * 2, 0.0)
                if left <= 0:
                    break
        return states


def fit(rows):
    """Stage-S stand-in: least-squares linear classifier on (q, left, 1) -> expert label."""
    X = np.array([[r["state"]["obs"][0], r["state"]["obs"][1], 1.0] for r in rows])
    y = np.array([1.0 if r["label"] else -1.0 for r in rows])
    return np.linalg.lstsq(X, y, rcond=None)[0]


def act(model, s):
    q, left = s["obs"]
    return bool(model @ np.array([q, left, 1.0]) > 0)


def test_seed_guard():
    for bad in (7001, 7005, 7010, 9001, 9101, 9210):
        with pytest.raises(ValueError, match="reserved"):
            D.check_synthetic_seed(bad)
    assert D.check_synthetic_seed(123) == 123


def test_aggregation_never_relabels_or_double_counts():
    data = D.AggregatedDataset()
    calls = []
    expert = lambda s: calls.append(s["key"]) or s["key"]
    assert data.add([{"key": "a"}, {"key": "b"}], expert, 0) == 2
    assert data.add([{"key": "b"}, {"key": "c"}], expert, 1) == 1
    assert len(data) == 3 and calls == ["a", "b", "c"]
    assert {r["state"]["key"]: r["round"] for r in data.items()} == {"a": 0, "b": 0, "c": 1}


def test_dagger_round_adds_on_policy_states_and_reduces_disagreement():
    env = SyntheticCampaign(seed=11)
    # round 0: expert rollouts only (behaviour cloning); the expert labels its own visited states
    initial = env.rollout(lambda s: SyntheticCampaign.expert_action(s), 40, "expert")
    expert = lambda s: SyntheticCampaign.expert_action(s)
    eval_env = SyntheticCampaign(seed=12)

    def rollout(model, r):
        return env.rollout(lambda s: act(model, s), 40, f"r{r}")

    res = D.run_dagger(initial, expert=expert, fit=fit, rollout=rollout, act=act,
                       expert_action=SyntheticCampaign.expert_action, rounds=3)
    h = res["history"]
    assert [x["round"] for x in h] == [0, 1, 2, 3]
    assert h[0]["aggregate"] == len(initial) and all(x["new"] == x["visited"] for x in h[1:])  # fresh instances
    assert h[-1]["aggregate"] == len(initial) + sum(x["new"] for x in h[1:])
    # on-policy disagreement after aggregation is no larger than after behaviour cloning alone
    bc = fit([{"state": s, "label": expert(s)} for s in initial])
    test_states = eval_env.rollout(lambda s: act(res["model"], s), 60, "eval")
    dis = lambda m: np.mean([act(m, s) != expert(s) for s in test_states])
    assert dis(res["model"]) <= dis(bc) + 1e-9


def test_rounds_must_be_positive():
    with pytest.raises(ValueError):
        D.run_dagger([], expert=lambda s: 0, fit=lambda r: None, rollout=lambda m, r: [], act=lambda m, s: 0,
                     expert_action=lambda s, l: 0, rounds=0)


def test_offline_rollout_on_the_offline_bandit_env():
    from r1.c3.env import OfflineBanditEnv
    rng = np.random.default_rng(42)
    rows = []
    for i in range(12):
        feats = {c: 0.0 for c in FEATURES}
        rows.append({"proposal_id": f"p{i}", "node": "digits_mlp", "features": feats, "noop": False,
                     "duplicate": False, "delta_label": float(rng.normal()), "weight": 1.0, "sigma_node": 1.0,
                     "sigma_cmp": 0.5, "delta_hat": float(rng.normal())})
    env = OfflineBanditEnv(rows, split="label", tau_node={"digits_mlp": 1.0})
    states = D.offline_rollout(env, lambda m, s: 11 if s["info"]["delta_hat"] > 0 else 0, None, range(12))
    assert [s["key"] for s in states] == [f"p{i}" for i in range(12)]
    assert all(set(s) >= {"obs", "info", "action", "reward", "execute"} for s in states)
    data = D.AggregatedDataset()
    assert data.add(states, lambda s: s["info"]["proposal_id"], 1) == 12
    assert data.add(D.offline_rollout(env, lambda m, s: 0, None, range(12)), lambda s: None, 2) == 0   # one-step env


def test_expert_is_called_once_per_new_state_and_never_on_known_states():
    """The expert may be a costly audit: each new state is labelled once; revisited states reuse their label."""
    calls = []

    def expert(s):
        calls.append(s["key"])
        return SyntheticCampaign.expert_action(s)

    initial = [{"key": f"a{i}", "obs": (0.5 - i / 10, 1.0)} for i in range(6)]
    revisit = initial[:3] + [{"key": "new1", "obs": (0.9, 0.5)}, {"key": "new2", "obs": (-0.9, 0.5)}]
    D.run_dagger(initial, expert=expert, fit=fit, rollout=lambda m, r: list(revisit), act=act,
                 expert_action=SyntheticCampaign.expert_action, rounds=2)
    assert sorted(calls) == sorted([s["key"] for s in initial] + ["new1", "new2"])
