"""Fixture-only checks of the H.8 execute/skip interface."""
import numpy as np
import pytest

from r1.c3.env import OfflineBanditEnv, evaluate_policy, onehot
from r1.c3.features import FEATURES
from r1.c3.labels import N_BINS


@pytest.fixture
def row():
    return {"proposal_id": "fixture", "node": "n", "features": {c: 0.0 for c in FEATURES},
            "sigma_node": 0.01, "sigma_cmp": 0.01, "delta_hat": 0.0,
            "delta_true": 0.02, "delta_label": 0.03, "weight": 2.0, "eval_weight": 3.0,
            "noop": False, "duplicate": False, "belief": onehot(11)}


def test_binary_action_and_moment_keep(row):
    env = OfflineBanditEnv([row])
    obs, info = env.reset()
    assert obs['features'].shape == (len(FEATURES),)
    np.testing.assert_array_equal(obs['belief'], onehot(11))
    assert info['weight'] == 2
    _, reward, term, trunc, info = env.step(0)
    assert term and not trunc and info['execute'] and info['keep']
    assert reward == pytest.approx(0.03 - 0.001)
    env.reset()
    _, reward, _, _, info = env.step(1)
    assert not info['execute'] and not info['keep'] and reward == 0
    # At the same observed delta, a negative prior produces a positive keep threshold.
    row['belief'] = onehot(1)
    env.reset()
    _, reward, _, _, info = env.step(0)
    assert info['execute'] and not info['keep'] and reward == pytest.approx(-0.001)


def test_belief_provider_and_snapshot(row):
    p = onehot(11)
    env = OfflineBanditEnv([row], belief_provider=lambda r: p)
    obs, _ = env.reset()
    obs['belief'][:] = 0
    p[:] = 0
    returned, _, _, _, info = env.step(0)
    np.testing.assert_array_equal(returned['belief'], onehot(11))
    assert info['keep']


@pytest.mark.parametrize('belief', [None, [1.0], [0.0] * N_BINS,
                                    [float('nan')] + [0.0] * 11,
                                    [-0.1, 1.1] + [0.0] * 10])
def test_invalid_belief(row, belief):
    row['belief'] = belief
    env = OfflineBanditEnv([row])
    with pytest.raises(ValueError, match='belief'):
        env.reset()
    with pytest.raises(RuntimeError):
        env.step(0)


@pytest.mark.parametrize('action', [-1, 2, 1.0, True, '0'])
def test_invalid_actions(row, action):
    env = OfflineBanditEnv([row])
    env.reset()
    with pytest.raises(ValueError):
        env.step(action)


def test_duplicate_rule_layer(row):
    row.update(duplicate=True, delta_label=None)
    with pytest.raises(ValueError, match='no rows'):
        OfflineBanditEnv([row], split='label')
    for layer, execute in [(True, False), (False, True)]:
        env = OfflineBanditEnv([row], split='eval', rule_layer=layer)
        env.reset()
        _, reward, _, _, info = env.step(0)
        assert info['execute'] == execute
        assert info['keep'] == execute
        assert reward == pytest.approx(0.019 if execute else 0.0)


def test_split_weights_and_weighted_policy(row):
    other = dict(row, proposal_id='other', delta_label=-0.01, delta_true=0.04,
                 weight=1.0, eval_weight=6.0)
    label = OfflineBanditEnv([row, other], split='label')
    ev = OfflineBanditEnv([row, other], split='eval')
    assert evaluate_policy(label, lambda obs, info: 0)['n']['mean_per_proposal'] == pytest.approx((2 * .029 - .011) / 3)
    assert evaluate_policy(ev, lambda obs, info: 0)['n']['mean_per_proposal'] == pytest.approx((3 * .019 + 6 * .039) / 9)
    assert evaluate_policy(ev, lambda obs, info: 1)['n']['exec_rate'] == 0
    ignored = dict(row, proposal_id='ignored', weight=0, eval_weight=0)
    assert len(OfflineBanditEnv([row, ignored])) == 1
    assert len(OfflineBanditEnv([row, ignored], split='eval')) == 1


def test_legacy_bin_explicit(row):
    env = OfflineBanditEnv([row], version='bin/v0', plugin='greedy', tau_node={'n': 1.0})
    obs, _ = env.reset()
    assert obs.shape == (len(FEATURES),)
    _, reward, _, _, info = env.step(0)
    assert not info['execute'] and reward == 0
    env.reset()
    with pytest.raises(ValueError):
        env.step(N_BINS)
