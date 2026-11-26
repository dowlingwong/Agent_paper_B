"""L13: the deployment controller reads only the control view and chooses continue or verify."""
from __future__ import annotations

from r1.controllers import IndexController
from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.controller import build_control_view  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

NOISE = {"sigma_d": 0.01, "sigma_t": 0.006, "sigma_s": 0.008}


class Rec:
    trial_id, budget_index, decision, delta_vs_best = "t", 3, None, None
    parsed_metrics = {"val_score": 0.951}


def _view(epoch):
    spec = load_registered_node("digits_mlp", repo_root=HARNESS)
    return build_control_view(epoch=epoch, budget_index=3, current_best=0.95, provisional=Rec() if epoch == "E2" else None,
                              budget={"worker_runs_remaining": 10}, node=spec)


def test_index_controller_uses_the_score_and_the_mask():
    seen = []
    ctl = IndexController(lambda p: seen.append(p) or 1.0, 0.0, "digits_mlp", NOISE, total_runs=20)
    assert ctl.decide(_view("E2"), {"continue": True, "verify": True}).action == "verify"
    assert abs(seen[-1]["features"]["delta_hat"] - 0.001) < 1e-12
    assert ctl.decide(_view("E2"), {"continue": True, "verify": False}).action == "continue"
    assert ctl.decide(_view("E1"), {"continue": True, "skip": True}).action == "continue"
    low = IndexController(lambda p: -1.0, 0.0, "digits_mlp", NOISE, total_runs=20)
    assert low.decide(_view("E2"), {"continue": True, "verify": True}).action == "continue"
