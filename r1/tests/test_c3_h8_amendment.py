"""CPU fixture tests for table-derived H.8 utility; no model inference."""
import numpy as np
import pytest

from r1.c3.env import OfflineBanditEnv, onehot
from r1.c3.features import FEATURES
from r1.c3.labels import action_target


def row(split='train', name='r', node='n'):
    return {'proposal_id': name, 'node': node, 'split': split,
            'features': {k: 0.0 for k in FEATURES}, 'sigma_node': 0.01, 'sigma_cmp': 0.01,
            'delta_hat': 0.0, 'z_train': [2.0, 4.0], 'z_eval': [-2.0, -4.0],
            'y_train': onehot(11), 'weight': 1.0, 'noop': False, 'duplicate': False}


def provider(_):
    return onehot(8)


def test_split_selects_label_block_and_fixed_train_a1():
    rows = [row('train', 'tr'), row('val', 'val'), row('test', 'te')]
    rows[1]['y_train'] = onehot(1)  # validation labels must not fit A1
    rows[2]['y_train'] = onehot(1)  # test labels must not fit A1
    env = OfflineBanditEnv(rows, belief_provider=provider)
    for i, key in enumerate(('z_train', 'z_train', 'z_eval')):
        obs, info = env.reset(options={'index': i})
        assert info['split'] == rows[i]['split'] and 'delta_hat' not in info
        np.testing.assert_array_equal(obs['belief'], onehot(8))
        _, reward, _, _, step = env.step(0)
        expected = action_target(np.mean(rows[i][key]) * rows[i]['sigma_node'], rows[i]['delta_hat'],
                                 onehot(11), rows[i]['sigma_node'], rows[i]['sigma_cmp'])
        assert reward == pytest.approx(expected) and step['execute']
    env.reset(options={'index': 2})
    assert env.step(1)[1] == 0


def test_training_reward_never_reads_eval_labels():
    r = row()
    env = OfflineBanditEnv([r], belief_provider=provider)
    env.reset()
    expected = env.step(0)[1]
    r['z_eval'] = [9999.0, -9999.0]
    env2 = OfflineBanditEnv([r], belief_provider=provider)
    env2.reset()
    assert env2.step(0)[1] == expected


def test_a1_is_training_only_weighted_and_per_node():
    a, b, test = row('train', 'a'), row('train', 'b'), row('test', 'c')
    b.update(y_train=onehot(1), weight=3.0)
    test['y_train'] = onehot(8)
    env = OfflineBanditEnv([a, b, test], belief_provider=provider)
    expected_a1 = (onehot(11) + 3 * onehot(1)) / 4
    np.testing.assert_allclose(env._a1.predict([test])[0], expected_a1)
    env.reset(options={'index': 2})
    _, got, *_ = env.step(0)
    assert got == pytest.approx(action_target(-0.03, 0.0, expected_a1, 0.01, 0.01))


@pytest.mark.parametrize('kwargs', [{'split': 'label'}, {'g_units': 0.2}])
def test_new_mode_rejects_caller_split_and_price(kwargs):
    with pytest.raises(ValueError, match='table and configuration'):
        OfflineBanditEnv([row()], belief_provider=provider, **kwargs)


def test_unknown_split_no_training_and_invalid_labels_fail_closed():
    with pytest.raises(ValueError, match='table split'):
        OfflineBanditEnv([row('unknown')], belief_provider=provider)
    with pytest.raises(ValueError, match='training-split'):
        OfflineBanditEnv([row('test')], belief_provider=provider)
    r = row()
    r['y_train'] = [0.0] * 12
    with pytest.raises(ValueError, match='y_train'):
        OfflineBanditEnv([r], belief_provider=provider)
    r = row()
    r['z_train'] = []
    env = OfflineBanditEnv([r], belief_provider=provider)
    env.reset()
    with pytest.raises(ValueError, match='z_train'):
        env.step(0)


def test_no_outcome_provider_and_failed_reset_clears_state():
    r = row()
    seen = []
    def safe(public):
        seen.append(public)
        assert not {'delta_hat', 'z_train', 'z_eval', 'y_train', 'u_train', 'u_eval'} & public.keys()
        return onehot(11)
    env = OfflineBanditEnv([r], belief_provider=safe)
    env.reset()
    env.step(0)
    assert seen
    env.belief_provider = lambda _: (_ for _ in ()).throw(RuntimeError('provider'))
    with pytest.raises(RuntimeError, match='provider'):
        env.reset()
    with pytest.raises(RuntimeError, match='reset'):
        env.step(0)


def test_duplicate_skip_and_legacy_mode():
    r = row()
    d = row('test', 'duplicate')
    d['duplicate'] = True
    env = OfflineBanditEnv([r, d], belief_provider=provider)
    env.reset(options={'index': 1})
    assert env.step(0)[1] == 0
    legacy = dict(r, delta_label=0.03, delta_true=0.02, eval_weight=1.0)
    old = OfflineBanditEnv([legacy], version='bin/v0', plugin='greedy', tau_node={'n': 1.0})
    old.reset()
    assert old.step(0)[1] == 0
