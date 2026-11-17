"""Regression and known-answer checks for P7."""
import json
from dataclasses import replace

import numpy as np
import pytest

from paperc import ope, ope_validation as v, schema
from paperc.esyn import dp, policies, sim
from paperc.esyn.extra import WORLDS


@pytest.mark.parametrize("name", v.BENCHMARKS)
def test_exact_recursion_matches_existing_dp(name):
    world = WORLDS[name]
    optimum = dp.solve(world)
    assert v.exact_policy_value(world, policies.Threshold(optimum.table)) == pytest.approx(optimum.value, abs=1e-14)
    g = 0.001
    assert v.exact_policy_value(world, policies.Static(g, 0.0)) == pytest.approx(dp.static_value(world, g), abs=1e-14)


def test_logged_mixture_uses_history_and_ignores_rule_steps():
    world = WORLDS["budget"]
    members = (
        ope.EpsilonPolicy(policies.Static(0.0, 0.0), 0.1, "execute"),
        ope.EpsilonPolicy(policies.Static(1.0, 0.0), 0.25, "skip"),
    )
    mixture = ope.CampaignMixture(members, (0.4, 0.6))
    rows = v.campaign_rows(world, mixture, 51, seed=v.COMPONENT_KEY)
    member = next(p for p in members if p.component == rows[0]["policy"]["behaviour_component"])
    assert not schema.check_campaign(rows, behaviour=sim.behaviour_for(member))
    batch = ope.load_campaigns(list(reversed(rows)), mixture)

    component_likelihood = np.ones(2)
    priors = np.array(mixture.priors)
    for i, (obs, action) in enumerate(zip(batch.obs, batch.actions)):
        if batch.eligible[i]:
            probs = mixture.probabilities(obs)
            before = priors @ component_likelihood
            component_likelihood *= probs[:, action]
            assert batch.behaviour[i, action] == pytest.approx((priors @ component_likelihood) / before)
        else:
            assert batch.behaviour[i, action] == 1
    chosen = batch.behaviour[np.arange(len(rows)), batch.actions]
    assert np.prod(chosen) == pytest.approx(priors @ component_likelihood, abs=1e-15)
    terminal = rows[-1]["terminal"]
    assert batch.rewards[:-1].sum() == 0
    assert batch.rewards[-1] == pytest.approx(terminal["y_terminal"] - terminal["y_start"])

    idx = next(i for i in range(len(rows)) if batch.eligible[i])
    rows[idx]["policy"]["action_prob"] = 0.99
    with pytest.raises(ope.OPEError, match="logged component propensity"):
        ope.load_campaigns(rows, mixture)


def test_wdr_handles_variable_lengths_and_weight_collapse():
    batch = ope.Batch(obs=({}, {}, {}), ids=("a", "b"), instances=("1", "2"),
                      starts=np.array([0, 1]), lengths=np.array([1, 2]),
                      features=np.zeros((3, 1)), stages=np.array([0, 0, 1]),
                      actions=np.array([0, 0, 0]), eligible=np.ones(3, dtype=bool),
                      behaviour=np.tile([1.0, 0.0], (3, 1)), rewards=np.array([1.0, 0.0, 3.0]), context=())
    q = np.array([[2., 4.], [8., 9.], [4., 5.]])
    on_policy = ope._weighted_dr(batch, batch.behaviour, q)
    assert on_policy["value"] == pytest.approx(2.0)
    assert on_policy["ess_by_step"] == [2.0, 2.0]
    assert on_policy["live_ess_by_step"] == [2.0, 1.0]
    incompatible = np.tile([0.0, 1.0], (3, 1))
    model_only = ope._weighted_dr(batch, incompatible, q)
    assert model_only["value"] == pytest.approx(6.5)
    assert model_only["zero_weight_steps"] == [0, 1]


@pytest.mark.parametrize("method", v.METHODS)
def test_fqe_known_terminal_only_problem(method):
    # Repeated two-stage trajectories each have a deterministic terminal
    # reward and a forced common action. Backups must reach the initial state.
    n = 24
    batch = ope.Batch(obs=tuple({} for _ in range(2 * n)), ids=tuple(map(str, range(n))),
                      instances=tuple(map(str, range(n))), starts=2 * np.arange(n), lengths=np.full(n, 2),
                      features=np.zeros((2 * n, 1)), stages=np.tile([0, 3], n), actions=np.zeros(2 * n, dtype=int),
                      eligible=np.zeros(2 * n, dtype=bool), behaviour=np.tile([1., 0.], (2 * n, 1)),
                      rewards=np.tile([0., 3.5], n), context=("same node",))
    fitted = ope.evaluate(batch, replace(batch, instances=tuple(map(str, range(n, 2 * n)))),
                          None, method=method, cluster=lambda _: None, seed=v.FIT_KEY)
    assert fitted["fqe"] == pytest.approx(3.5)
    assert fitted["wdr"]["value"] == pytest.approx(3.5)
    assert fitted["support"]["status"] == "insufficient data"
    with pytest.raises(ope.OPEError, match="disjoint"):
        ope.evaluate(batch, batch, None, method=method, cluster=lambda _: None, seed=v.FIT_KEY)


def test_ipw_contrast_and_removed_support():
    a = np.array([1, 0, 1, 0])
    y = np.array([2.0, 1.0, 2.0, 1.0])
    assert ope.ipw_population_contrast(y, a, np.tile([0.5, 0.5], (4, 1))) == pytest.approx(1.0)
    with pytest.raises(ope.OPEError, match="positive probabilities"):
        ope.ipw_population_contrast(y, a, np.tile([1.0, 0.0], (4, 1)))
    failure = v.removed_support()
    assert failure["status"] == "insufficient data"
    assert failure["zero_propensity_target_rows"] > 0


def test_validation_output_is_current():
    result = json.loads(v.OUT.read_text())
    assert result["code_sha256"] == v.code_sha256()
    assert v.REPORT.read_text() == v.markdown(result)
    for world in result["worlds"].values():
        assert set(world["truth"]) == set(v.TARGETS)
        for target in world["summary"].values():
            for summary in target.values():
                assert summary["n"] > 0
