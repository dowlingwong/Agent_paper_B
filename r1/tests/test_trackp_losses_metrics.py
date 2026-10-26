"""Track P 1.3: losses and metrics against hand-computed values. ENGINEERING_ONLY; AI-assisted (Claude)."""
import math

import numpy as np
import pytest
import torch

from r1.c3.labels import N_BINS, soft_label
from r1.c3.train import losses as Ls
from r1.c3.train import metrics as M


def onehot(k):
    p = np.zeros(N_BINS)
    p[k] = 1.0
    return p


UNIFORM = np.r_[0.0, np.full(11, 1 / 11)]


@pytest.mark.parametrize("p,y,want", [
    (onehot(0), onehot(6), 0.75),          # Brier0 1; R = 1 from bin 6 on -> 5 of 10 terms -> 0.5
    (onehot(1), onehot(11), 0.5),          # Q = 1 everywhere, R = 0 -> ordinal 1
    (UNIFORM, onehot(6), 1 / 22),          # sum (k/11)^2 k<=5 + (1-k/11)^2 k=6..10 = 110/121 -> mean 1/11
    (np.r_[0.6, np.full(11, 0.4 / 11)], onehot(0), 0.08),  # inert label: only Brier0 (0.4^2)/2
    (UNIFORM, UNIFORM, 0.0),
])
def test_rps_hand_values(p, y, want):
    assert M.rps(p[None], y[None])[0] == pytest.approx(want, abs=1e-12)
    got = Ls.rps(torch.tensor(p[None]), torch.tensor(y[None]))[0].item()
    assert got == pytest.approx(want, abs=1e-6)


def test_rps_torch_equals_numpy_and_is_bounded_and_proper():
    rng = np.random.default_rng(0)
    p = rng.dirichlet(np.ones(N_BINS), size=64)
    y = rng.dirichlet(np.ones(N_BINS), size=64)
    np.testing.assert_allclose(Ls.rps(torch.tensor(p), torch.tensor(y)).numpy(), M.rps(p, y), atol=1e-6)
    assert (M.rps(p, y) >= 0).all() and (M.rps(p, y) <= 1).all()
    # properness on a soft label: the label itself scores no worse than any perturbation of it
    yy = soft_label(0.3, None, 1.0, k_label=5)[None]
    base = M.rps(yy, yy)[0]
    for _ in range(50):
        q = np.clip(yy + 0.05 * rng.normal(size=yy.shape), 0, None)
        q /= q.sum()
        assert M.rps(q, yy)[0] >= base - 1e-12


def test_soft_ce_and_stage_s():
    y = torch.tensor([[0.5, 0.5] + [0.0] * 10])
    p = torch.tensor([[0.25, 0.25, 0.5] + [0.0] * 9])
    assert Ls.soft_ce(p, y).item() == pytest.approx(math.log(4), rel=1e-6)
    assert Ls.stage_s_loss(p, y).item() == pytest.approx(Ls.rps(p, y).item() + math.log(4), rel=1e-6)
    assert Ls.stage_s_loss(p, y, ce=False).item() == pytest.approx(Ls.rps(p, y).item())


def test_action_loss_cost_sensitive_bce():
    logit = torch.zeros(2)
    u = torch.tensor([2.0, -1.0])
    assert Ls.action_loss(logit, u).item() == pytest.approx(1.5 * math.log(2), rel=1e-6)
    # u = 0 rows carry no weight
    assert Ls.action_loss(torch.tensor([5.0]), torch.tensor([0.0])).item() == 0.0
    # gradient direction: positive u pushes the logit up, negative u down
    x = torch.zeros(2, requires_grad=True)
    Ls.action_loss(x, u).backward()
    assert x.grad[0] < 0 < x.grad[1]


def test_smoothed_rule_loss_hand_value():
    p = torch.tensor(UNIFORM[None])
    y = torch.tensor(onehot(6)[None])
    v = torch.arange(N_BINS, dtype=torch.float32)       # V(p) = sum_k k/11 for k=1..11 = 6
    u = torch.tensor([0.4])
    # a_tau = sigmoid((6 - 6)/0.5) = 0.5 -> 1/22 - 2 * 0.5 * 0.4
    got = Ls.smoothed_rule_loss(p, y, u, v, g=6.0, tau=0.5, lam=2.0).item()
    assert got == pytest.approx(1 / 22 - 0.4, abs=1e-6)
    assert Ls.rule_value(p, v).item() == pytest.approx(6.0, abs=1e-5)


def test_rps_skill():
    y = np.stack([onehot(6), onehot(7)])
    base = M.base_rate(y)                    # half on 6, half on 7
    assert M.rps_skill(y, y, base) == pytest.approx(1.0)
    assert M.rps_skill(np.broadcast_to(base, y.shape), y, base) == pytest.approx(0.0)
    # base RPS: each row has |Q - R| = 0.5 at k = 6 only -> 0.5 * 0.25 / 10 = 0.0125
    assert M.mean_rps(np.broadcast_to(base, y.shape), y) == pytest.approx(0.0125)


def test_ece_all_bins_and_top1():
    p = np.array([[0.8, 0.2] + [0.0] * 10])
    y = np.array([[0.0, 1.0] + [0.0] * 10])
    # pairs (0.8, 0) and (0.2, 1) each off by 0.8; ten (0, 0) pairs exact -> 1.6 / 12
    assert M.ece_all_bins(p, y) == pytest.approx(1.6 / 12)
    assert M.ece_top1(p, y) == pytest.approx(0.8)
    assert M.ece_all_bins(y, y) == 0.0 and M.ece_top1(y, y) == 0.0


def test_pit_histogram_flat_when_forecast_equals_label_and_u_shaped_when_overconfident():
    y = np.stack([soft_label(z, None, 1.0, k_label=5) for z in np.linspace(-2, 2, 9)])
    np.testing.assert_allclose(M.pit_histogram(y, y, n=10), np.ones(10), atol=1e-9)
    np.testing.assert_allclose(M.pit_histogram(UNIFORM[None], UNIFORM[None], n=11), np.ones(11), atol=1e-9)
    h = M.pit_histogram(onehot(6)[None], UNIFORM[None], n=10)
    # outcome bins 1-5: point mass at 0 (5/11); bin 6: U(0, 1) (1/11); bins 7-11: point mass at 1 (5/11)
    want = np.full(10, 1 / 110)
    want[0] += 5 / 11
    want[-1] += 5 / 11
    np.testing.assert_allclose(h, want * 10, atol=1e-9)
    assert h.sum() / 10 == pytest.approx(1.0)


def test_pit_values_fall_in_the_bin_interval():
    v = M.pit_values(np.stack([UNIFORM] * 100), np.zeros(100), rng=np.random.default_rng(1))
    assert ((v >= 5 / 11) & (v <= 6 / 11)).all()       # z = 0 lies in bin 6 = the 6th of 11


def test_width_ratio():
    y = np.stack([soft_label(z, None, 1.0, k_label=5) for z in (-1.0, 0.0, 1.0)])
    assert M.width_ratio(y, y) == pytest.approx(1.0)
    collapsed = np.stack([onehot(int(np.argmax(r))) for r in y])
    assert M.width_ratio(collapsed, y) == pytest.approx(0.0)
    assert math.isnan(M.width_ratio(y[:1], np.stack([onehot(0)])))  # all-inert labels: undefined


def test_disagreement_rate():
    assert M.disagreement_rate([1, 0, 1, 1], [1, 1, 1, 0]) == 0.5
    with pytest.raises(ValueError):
        M.disagreement_rate([1], [1, 0])
