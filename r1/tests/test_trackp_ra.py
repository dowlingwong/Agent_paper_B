"""R-A1 detached action head and the §6.4 rollback rule (r1/c3/train/ra.py). Synthetic; ENGINEERING_ONLY."""
import pytest

torch = pytest.importorskip("torch")
from r1.c3.train import ra  # noqa: E402


def test_detached_head_learns_without_touching_the_shared_state():
    torch.manual_seed(0)
    trunk = torch.nn.Linear(4, 6)
    head = ra.DetachedActionHead(6)
    x = torch.randn(64, 4)
    u = torch.where(x[:, 0] > 0, torch.tensor(1.0), torch.tensor(-1.0))
    opt = torch.optim.SGD(head.parameters(), lr=0.5)
    first = None
    for _ in range(200):
        out = {"state": trunk(x)}
        loss = ra.ra1_loss(head, out, u)
        opt.zero_grad()
        loss.backward()
        first = float(loss) if first is None else first
        opt.step()
    assert trunk.weight.grad is None            # stop-gradient: no gradient reaches the shared state
    assert float(loss) < first
    # a LayerNorm precedes the linear layer (R1-HEADS-LN): the output does not change when the state is rescaled
    s = torch.randn(5, 6)
    assert isinstance(head.norm, torch.nn.LayerNorm)
    assert torch.allclose(head(s), head(7.5 * s), atol=1e-4)
    with pytest.raises(ValueError, match="return_state"):
        ra.ra1_loss(head, {"state": None}, u)


S = ra.ValMetrics(ece_all_bins=0.05, rps=0.20, rps_se=0.01, utility=1.0, width_ratio=1.0, entropy=2.0)


@pytest.mark.parametrize("change,steps,reason", [
    ({"ece_all_bins": 0.0701}, 500, "ECE"),
    ({"rps": 0.2101}, 500, "RPS"),
    ({"width_ratio": 0.79}, 500, "width"),
    ({"entropy": 1.59}, 100, "entropy"),
])
def test_each_rollback_condition(change, steps, reason):
    cur = ra.ValMetrics(**{**S.__dict__, **change})
    out = ra.stop_rule(S, cur, steps_since_stage_s=steps)
    assert out["rollback"] and any(reason in r for r in out["reasons"])


def test_no_rollback_at_the_boundaries_and_when_utility_improved():
    edge = ra.ValMetrics(ece_all_bins=0.07, rps=0.21, rps_se=0.01, utility=1.0, width_ratio=0.8, entropy=1.6)
    assert not ra.stop_rule(S, edge, steps_since_stage_s=50)["rollback"]
    worse_rps_better_u = ra.ValMetrics(**{**S.__dict__, "rps": 0.25, "utility": 1.1})
    assert not ra.stop_rule(S, worse_rps_better_u, steps_since_stage_s=500)["rollback"]
    late_entropy = ra.ValMetrics(**{**S.__dict__, "entropy": 1.0})
    assert not ra.stop_rule(S, late_entropy, steps_since_stage_s=101)["rollback"]
