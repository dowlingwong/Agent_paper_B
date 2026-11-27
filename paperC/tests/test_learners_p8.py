"""Known-answer and artifact checks for the P8 CPU learners."""
from dataclasses import replace
import json

import numpy as np
import pytest

from paperc import learner_validation as validation, learners, ope


def toy(n=256):
    a0 = np.arange(n) % 2
    a1 = (np.arange(n) // 2) % 2
    actions = np.column_stack((a0, a1)).ravel()
    obs = tuple({
        "epoch": "E2" if i % 2 else "E1", "llm_cap": 3, "W": 2,
        "slots_left": 1 if i % 2 else 2, "calls_left": 1 if i % 2 else 2,
        "runs_left": 1, "v_star": 0.003, "m_hat": 0.01 if i % 2 else None,
        "tau": 0.01, "sigma": 0.01,
    } for i in range(2 * n))
    return ope.Batch(
        obs, tuple(map(str, range(n))), tuple(map(str, range(n))),
        np.arange(n) * 2, np.full(n, 2), np.zeros((2 * n, 1)),
        np.tile([2, 3], n), actions, np.ones(2 * n, dtype=bool), np.full((2 * n, 2), 0.5),
        np.column_stack((np.zeros(n), 0.02 * a0 + 0.01 * (1 - a1))).ravel(), ("toy",),
    )


def test_shaping_preserves_root_total_and_uses_the_two_resources():
    batch = toy()
    shaped = learners.rewards(batch, shaped=True)
    assert np.add.reduceat(shaped, batch.starts) == pytest.approx(batch.rewards[batch.ends])
    # Move one awarded keep ahead of a subsequent terminal transition.
    x = replace(batch, starts=np.array([0]), lengths=np.array([len(batch.obs)]))
    redistributed = learners.rewards(x, shaped=True)
    assert redistributed.sum() == pytest.approx(x.rewards.sum())
    assert (redistributed[:-1] != x.rewards[:-1]).any()
    a = batch.obs[0]
    b = {**a, "runs_left": 2, "slots_left": 1, "calls_left": 1}
    assert learners.features(a, 0.01)[:3] != learners.features(b, 0.01)[:3]


def test_n6_fits_total_fork_advantage_by_epoch():
    batch = toy()
    idx = np.arange(len(batch.obs))
    data = learners.ForkTraining(idx, np.tile([0.02, -0.01], len(batch.ids)))
    policy = learners.fit_n6(batch, data, learners.N6Config(1.0), scale=0.01)
    assert policy.act(batch.obs[0])[0] == "execute"
    assert policy.act(batch.obs[1])[0] == "discard"
    with pytest.raises(ValueError, match="unique eligible"):
        learners.fit_n6(batch, learners.ForkTraining(np.array([0, 0]), np.array([1, 2])),
                        learners.N6Config(1.0), scale=0.01)


def test_fqi_backs_up_delayed_reward_with_gamma_one():
    batch = toy()
    # The terminal observation exposes the first action, so the Bellman target
    # can distinguish delayed gains earned by the two initial actions.
    obs = list(batch.obs)
    for j in batch.starts:
        obs[j + 1] = {**obs[j + 1], "runs_left": 2 - int(batch.actions[j])}
    batch = replace(batch, obs=tuple(obs))
    policy = learners.fit_r0(batch, learners.FQIConfig(7, 48), scale=0.01, seed=validation.FIT_KEY)
    assert policy.act(obs[0])[0] == "execute"
    assert policy.act(obs[1])[0] == "discard"


def test_iql_expectile_and_advantage_weighted_cpu_actor():
    import torch

    torch.set_num_threads(1)
    residual = torch.tensor([-1.0, 2.0], device="cpu")
    assert learners.expectile_loss(residual, 0.75).item() == pytest.approx(1.625)
    n = 256
    batch = toy(n)
    x = replace(batch, obs=batch.obs[::2], starts=np.arange(n), lengths=np.ones(n, dtype=int),
                stages=batch.stages[::2], features=batch.features[::2], actions=batch.actions[::2],
                eligible=batch.eligible[::2], behaviour=batch.behaviour[::2], rewards=0.02 * batch.actions[::2])
    cfg = learners.IQLConfig(0.7, 4.0, width=16, critic_steps=450, actor_steps=250)
    p = learners.fit_r1(x, cfg, scale=0.01, seed=validation.FIT_KEY)
    assert p.act(x.obs[0])[0] == "execute"
    again = learners.fit_r1(x, cfg, scale=0.01, seed=validation.FIT_KEY)
    assert p.name == again.name


def test_n6_reports_missing_fork_labels_even_with_supported_roots():
    train = toy()
    screen = replace(train, instances=tuple(f"heldout-{i}" for i in range(len(train.ids))))
    idx = train.starts
    data = learners.ForkTraining(idx, np.ones(len(idx)))
    p, receipt = learners.fit_supported("N6", train, screen, learners.N6Config(1.0), scale=0.01,
                                        seed=validation.FIT_KEY, cluster=lambda _: 0, fork_data=data)
    assert receipt["prefit"]["status"] == "meets thresholds"
    assert p is None and receipt["candidate"] is None
    assert receipt["fork_labels"]["status"] == "insufficient data"
    assert receipt["fork_labels"]["missing_stages"] == [3]
    assert receipt["fork_labels"]["missing_clusters"] == ["('E2', 0)"]


def test_removed_support_returns_no_candidate_before_training():
    world, _, _ = validation.setup()
    rows = validation.removed_support(world)
    assert set(rows) == set(validation.GRIDS)
    for row in rows.values():
        assert row["policy"] is None and row["support"]["candidate"] is None
        p = row["support"]["prefit"]
        assert p["status"] == "insufficient data" and p["zero_propensity_target_rows"] > 0


def test_learner_benchmark_is_current_and_reports_gain_recovery():
    result = json.loads(validation.OUT.read_text())
    assert result["code_sha256"] == validation.code_sha256()
    assert validation.REPORT.read_text() == validation.markdown(result)
    assert result["training"]["prefit"]["status"] == "meets thresholds"
    gap = result["reference"]["gap"]
    assert gap > 0
    for row in result["methods"].values():
        assert row["test"]["status"] == "evaluated"
        assert len(row["policy_ids"]) == validation.N_FIT
        assert all(r["candidate"]["status"] == "meets thresholds" for r in row["refits"])
        assert row["test"]["gain_share"] == pytest.approx(row["test"]["mean"] / gap)
        assert row["test"]["gain_share"] >= validation.GAIN_FLOOR
        assert row["test"]["clears_gain_floor"]
    for row in result["removed_support"].values():
        assert row["policy"] is None and row["support"]["prefit"]["status"] == "insufficient data"
