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
            "noop": False, "duplicate": False, "belief": onehot(11), "u_train": 0.029, "u_eval": 0.019, "u_reference": "A1", "u_g_units": 0.1}


def test_binary_action_uses_fixed_reference_utility(row):
    env = OfflineBanditEnv([row], belief_provider=lambda _: row["belief"])
    obs, info = env.reset()
    assert obs['features'].shape == (len(FEATURES),)
    np.testing.assert_array_equal(obs['belief'], onehot(11))
    assert info['weight'] == 2
    _, reward, term, trunc, info = env.step(0)
    assert term and not trunc and info['execute'] and info['keep'] is None
    assert reward == pytest.approx(0.029)
    env.reset()
    _, reward, _, _, info = env.step(1)
    assert not info['execute'] and reward == 0
    row['belief'] = onehot(1)
    env.reset()
    _, reward, _, _, info = env.step(0)
    assert info['execute'] and reward == pytest.approx(0.029)


def test_belief_provider_and_snapshot(row):
    p = onehot(11)
    env = OfflineBanditEnv([row], belief_provider=lambda r: p)
    obs, _ = env.reset()
    obs['belief'][:] = 0
    p[:] = 0
    returned, _, _, _, info = env.step(0)
    np.testing.assert_array_equal(returned['belief'], onehot(11))
    assert info['execute']


@pytest.mark.parametrize('belief', [None, [1.0], [0.0] * N_BINS,
                                    [float('nan')] + [0.0] * 11,
                                    [-0.1, 1.1] + [0.0] * 10])
def test_invalid_belief(row, belief):
    row['belief'] = belief
    env = OfflineBanditEnv([row], belief_provider=lambda _: row["belief"])
    with pytest.raises(ValueError, match='belief'):
        env.reset()
    with pytest.raises(RuntimeError):
        env.step(0)


@pytest.mark.parametrize('action', [-1, 2, 1.0, True, '0'])
def test_invalid_actions(row, action):
    env = OfflineBanditEnv([row], belief_provider=lambda _: row["belief"])
    env.reset()
    with pytest.raises(ValueError):
        env.step(action)


def test_duplicate_rule_layer(row):
    row.update(duplicate=True, delta_label=None)
    with pytest.raises(ValueError, match='no rows'):
        OfflineBanditEnv([row], split='label', belief_provider=lambda _: row['belief'])
    for layer, execute in [(True, False), (False, True)]:
        env = OfflineBanditEnv([row], split='eval', rule_layer=layer, belief_provider=lambda _: row['belief'])
        env.reset()
        _, reward, _, _, info = env.step(0)
        assert info['execute'] == execute
        assert info['keep'] is None
        assert reward == pytest.approx(0.019 if execute else 0.0)


def test_split_weights_and_weighted_policy(row):
    other = dict(row, proposal_id='other', delta_label=-0.01, delta_true=0.04,
                 u_train=-0.011, u_eval=0.039, weight=1.0, eval_weight=6.0)
    label = OfflineBanditEnv([row, other], split='label', belief_provider=lambda _: onehot(11))
    ev = OfflineBanditEnv([row, other], split='eval', belief_provider=lambda _: onehot(11))
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


def test_provider_never_sees_outcomes_and_failed_reset_is_safe(row):
    seen = []
    def provider(public):
        seen.append(public)
        assert not {'delta_hat', 'delta_true', 'delta_label', 'u_train', 'u_eval', 'belief'} & public.keys()
        return onehot(11)
    env = OfflineBanditEnv([row], belief_provider=provider)
    env.reset()
    env.step(0)
    assert seen and 'features' in seen[0]
    env.belief_provider = lambda public: (_ for _ in ()).throw(RuntimeError('provider'))
    with pytest.raises(RuntimeError, match='provider'):
        env.reset()
    with pytest.raises(RuntimeError, match='reset'):
        env.step(0)


def test_missing_utility_is_not_silently_recomputed(row):
    del row['u_train']
    env = OfflineBanditEnv([row], belief_provider=lambda _: row["belief"])
    env.reset()
    with pytest.raises(ValueError, match='u_train'):
        env.step(0)
    env.reset()
    assert env.step(1)[1] == 0


def test_no_logged_outcome_in_policy_info(row):
    env = OfflineBanditEnv([row], belief_provider=lambda _: onehot(11))
    _, info = env.reset()
    assert not {'delta_hat', 'delta_true', 'delta_label', 'u_train', 'u_eval'} & info.keys()


def test_utility_provenance_and_price_checked(row):
    env = OfflineBanditEnv([row], belief_provider=lambda _: onehot(11), g_units=0.05)
    env.reset()
    with pytest.raises(ValueError, match='provenance'):
        env.step(0)
    row['u_g_units'] = 0.05
    row['u_reference'] = 'other'
    env.reset()
    with pytest.raises(ValueError, match='provenance'):
        env.step(0)


def test_fixed_a1_utility_uses_only_fixed_reference():
    from r1.c3.env import fixed_a1_utility
    assert fixed_a1_utility(0.02, 0.02, mu=0.0, tau=0.01, sigma_cmp=0.01,
                            sigma_node=0.01, g_units=0.1) == pytest.approx(0.019)
    assert fixed_a1_utility(0.02, -0.02, mu=0.0, tau=0.01, sigma_cmp=0.01,
                            sigma_node=0.01, g_units=0.1) == pytest.approx(-0.001)
