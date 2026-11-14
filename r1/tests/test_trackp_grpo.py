"""Track P Stage R-B (GRPO) known-answer and synthetic tests. No label, table, seed 7001-7010 or API call."""
import math

import numpy as np
import pytest

from r1.c3.train import grpo as G


def test_constants_follow_the_spec():
    assert (G.GROUP_SIZE, G.CLIP_EPS, G.UPDATE_EPOCHS, G.BETAS, G.FORMAT_PENALTY) == (8, 0.2, 2, (0.0, 0.02), 0.5)
    assert (G.LORA_RANK, G.LR_RANGE, G.MAX_STEPS, G.ANALYSIS_MAX_TOKENS) == (16, (1e-6, 5e-6), 500, 256)


def test_loo_advantage_known_answer():
    r = np.array([[1.0, 2.0, 3.0, 6.0]])
    # A_i = r_i - mean(others): 1 - 11/3, 2 - 10/3, 3 - 3, 6 - 2
    assert np.allclose(G.loo_advantages(r), [[1 - 11 / 3, 2 - 10 / 3, 0.0, 4.0]])
    # LOO advantages are G/(G-1) times the centred rewards: no std normalisation
    assert np.allclose(G.loo_advantages(r), (r - r.mean()) * 4 / 3)


def test_std_advantage_known_answer_and_zero_groups():
    r = np.array([[1.0, 3.0], [2.0, 2.0]])
    assert np.allclose(G.std_advantages(r), [[-1.0, 1.0], [0.0, 0.0]])
    assert G.zero_advantage_share(r) == 0.5
    assert np.allclose(G.loo_advantages(r)[1], 0.0)
    with pytest.raises(ValueError):
        G.loo_advantages(np.array([1.0]))


def test_reward_rule():
    r = G.rb_reward([0.1, 0.2, 0.0], [True, False, True], [5.0, 5.0, -9.0], u_max=2.0,
                    format_violation=[False, False, True], lambda_a=0.5)
    assert np.allclose(r, [-0.1 + 0.5 * 2.0, -0.2, 0.0 + 0.5 * -2.0 - 0.5])
    with pytest.raises(ValueError, match="RPS"):
        G.rb_reward([1.5], [True], [0.0], u_max=1.0, format_violation=[False], lambda_a=1.0)
    assert G.u_max_from_train(np.arange(-100, 101)) == pytest.approx(np.percentile(np.abs(np.arange(-100, 101)), 99))


def test_clipped_surrogate_known_answer():
    lo = np.log(np.array([[0.5, 0.5, 0.5]]))
    ln = np.log(np.array([[0.5 * 1.5, 0.5 * 0.9, 0.5]]))      # rho = 1.5, 0.9, 1.0
    mask = np.array([[1, 1, 0]])
    loss_pos, clip_pos = G.np_clipped_surrogate(ln, lo, [2.0], mask)
    # A > 0: min(1.5*2, 1.2*2) = 2.4 and min(0.9*2, 0.9*2) = 1.8; summed over tokens (no length normalisation)
    assert loss_pos == pytest.approx(-(2.4 + 1.8)) and clip_pos == pytest.approx(0.5)
    loss_neg, _ = G.np_clipped_surrogate(ln, lo, [-2.0], mask)
    # A < 0: min(-3, -2.4) = -3 and min(-1.8, -1.6) = -1.8
    assert loss_neg == pytest.approx(3.0 + 1.8)


def test_k3_known_answer():
    ln = np.log(np.array([[0.5, 0.25]])); lr = np.log(np.array([[0.25, 0.25]]))
    agg, mean = G.np_k3(ln, lr, np.ones((1, 2)))
    d = math.log(0.5)
    assert agg == pytest.approx(math.exp(d) - d - 1) and mean == pytest.approx((math.exp(d) - d - 1) / 2)


def test_estimator_check_meets_the_spec_threshold():
    rng = np.random.default_rng(20261114)
    logits, u = rng.normal(0, 1.5, 256), rng.normal(0, 1, 256)
    res = G.estimator_check(logits, u, group=8, resamples=64, seed=1)
    assert res["passes"] and res["cosine"] >= 0.95
    assert res["prompts"] == 256 and res["group"] == 8 and res["resamples"] == 64
    # the threshold is not met trivially: with too little sampling (G = 2, one resample) the estimate is too noisy
    weak = G.estimator_check(logits, u, group=2, resamples=1, seed=1)
    assert not weak["passes"] and weak["cosine"] < 0.9
    assert G.estimator_check(logits, u, advantage="std", seed=1)["advantage"] == "std"


def test_loo_estimator_is_unbiased_where_the_std_variant_is_not_required():
    rng = np.random.default_rng(3)
    logits, u = rng.normal(0, 1, 64), rng.normal(0, 1, 64)
    many = G.estimator_check(logits, u, resamples=2000, seed=2)
    assert many["cosine"] > 0.995
