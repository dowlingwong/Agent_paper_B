"""Known-answer paired inference and power checks (P9)."""
from dataclasses import replace
import json
import math

import numpy as np
import pytest

from paperc import power_validation as power
from paperc import statistics as stats


def test_holm_known_values_ties_and_order():
    assert stats.holm([0.04, 0.01, 0.03, 0.002]).tolist() == pytest.approx([0.06, 0.03, 0.06, 0.008])
    assert stats.holm([0.02, 0.02, 0.9]).tolist() == pytest.approx([0.06, 0.06, 0.9])
    assert stats.holm([]).size == 0
    with pytest.raises(ValueError, match="finite p-values"):
        stats.holm([math.nan])


def test_tost_and_superiority_against_df2_closed_form():
    out = stats.paired_test([1, 2, 3], 4.0)
    sf2 = lambda z: (1 - z / math.sqrt(z * z + 2)) / 2
    assert out.mean == pytest.approx(2.0)
    assert out.se == pytest.approx(1 / math.sqrt(3))
    assert out.p_superiority == pytest.approx(sf2(2 * math.sqrt(3)))
    assert out.p_lower == pytest.approx(sf2(6 * math.sqrt(3)))
    assert out.p_upper == pytest.approx(sf2(2 * math.sqrt(3)))
    assert out.p_tost == out.p_upper
    assert stats.paired_test([3, 4, 5], 4.0).p_upper == pytest.approx(0.5)
    assert stats.paired_test([-5, -4, -3], 4.0).p_lower == pytest.approx(0.5)


def test_joint_superiority_equivalence_and_planned_gates():
    draws = np.tile([0.25, 0.5, 0.75], 8)
    a = stats.paired_test(draws, 1.0)
    d = stats.family_decisions({"a": a, "b": None}, equivalence_power_at_zero={"a": 0.80})
    assert d["a"]["superiority_p_holm"] == pytest.approx(2 * a.p_superiority)
    assert d["a"]["tost_p_holm"] == pytest.approx(2 * a.p_tost)
    assert d["a"]["decision"] == "superiority and equivalence"
    assert d["b"]["decision"] == "not testable at this budget"
    gate = stats.family_decisions({"a": a}, equivalence_power_at_zero={"a": 0.799})["a"]
    assert gate["tost_rejects"] and not gate["equivalence"] and gate["superiority"]
    bad = stats.family_decisions({"a": a}, go_no_go={"a": False})["a"]
    assert bad["decision"] == "not testable at this budget" and not bad["superiority"]


def test_degenerate_pairs_and_zero_margin():
    bad = stats.paired_test([1, 1, 1], 0.1)
    assert bad.status == "unresolved variance" and bad.ci is None
    assert stats.family_decisions({"n": bad})["n"]["decision"] == "not testable at this budget"
    assert stats.paired_test([1], 0.1).status == "insufficient pairs"
    zero = stats.paired_test([-0.04, 0, 0.04], 0)
    assert not stats.family_decisions({"n": zero}, equivalence_power_at_zero={"n": 1.0})["n"]["equivalence"]
    assert stats.et0_margin(0.001) == pytest.approx(0.002)
    assert stats.et0_margin(0.02) == pytest.approx(0.005)
    assert stats.esyn_margin(0.05, 0.04) == pytest.approx(0.001)


def test_pairing_aggregates_audits_then_reps_without_pseudoreplication():
    a = stats.CampaignKey("n", 1, "start")
    b = stats.CampaignKey("n", 2, "start")
    c = stats.CampaignKey("n", 3, "start")
    x = [
        stats.CampaignOutcome(a, 2, 0, 10), stats.CampaignOutcome(a, 4, 0, 11),
        stats.CampaignOutcome(a, 10, 1, 12), stats.CampaignOutcome(b, 3),
        stats.CampaignOutcome(c, None),
    ]
    y = [replace(row, value=0) for row in x]
    p = stats.pair_campaigns(reversed(x), y)
    assert p.keys == (a, b) and p.differences == (6.5, 3.0)
    assert (p.attempted, p.excluded, p.left_incomplete, p.right_incomplete) == (3, 1, 1, 0)
    with pytest.raises(ValueError, match="attempted campaign keys"):
        stats.pair_campaigns(x, y[:-1])
    with pytest.raises(ValueError, match="one frozen fit"):
        stats.pair_campaigns([replace(x[0], fit_seed=1), *x[1:]], y)
    with pytest.raises(ValueError, match="audit IDs"):
        stats.pair_campaigns(x, [replace(y[0], audit_seed=99), *y[1:]])


def test_closed_form_matches_monte_carlo_to_four_binomial_standard_errors():
    rows = power.normal_control(seed=power.POWER_KEY, reps=2048)
    for case in rows:
        for name, p in case["exact"].items():
            sample = case["simulation"][name]
            se = math.sqrt(p * (1 - p) / sample["n"])
            assert abs(sample["probability"] - p) <= 4 * se + 1 / sample["n"]
    assert rows[0]["exact"]["superiority"] == pytest.approx(0.025)


def test_planning_shift_preserves_variance_without_sample_recentering():
    first, independent = [1, 2, 3], [-2, 0, 0]
    case = power.paired_scenarios(first, independent, 0.2)
    assert case["raw"].tolist() == first
    assert case["zero"].tolist() == pytest.approx(np.array([3, 2, 3]) / math.sqrt(2))
    assert case["positive"] - case["zero"] == pytest.approx(np.full(3, 0.4))
    with pytest.raises(ValueError, match="equal-size"):
        power.paired_scenarios([1, 2], [1], 0.2)


def test_world_replicates_and_splits_are_disjoint():
    contexts = [power.setup(node, rep)[0] for rep in range(power.N_REP) for node in power.NODES]
    assert len({w.code for w in contexts}) == len(contexts)
    ranges = power.TRAIN, power.SCREEN, power.DEV, power.TEST, power.TEST_CONTROL
    assert all(a.stop <= b.start for a, b in zip(ranges, ranges[1:]))


def test_validation_output_is_current_and_complete():
    report = json.loads(power.OUT.read_text())
    assert report["code_sha256"] == power.code_sha256()
    assert power.REPORT.read_text() == power.markdown(report)
    assert report["summary"] == power.summarise(report["raw"])
    assert len(report["raw"]) == power.N_REP
    for rep in report["raw"]:
        for row in rep["nodes"].values():
            for method, details in row["fit_grid"].items():
                assert len(details["candidates"]) == len(power.p8.GRIDS[method])
            for family in power.FAMILIES:
                assert set(row["families"][family]) == {"dev_difference", *power.SCENARIOS}
    for family in power.FAMILIES:
        tested = sum(result["scenarios"]["raw"]["tested"] for result in report["summary"][family].values())
        assert tested > 0
