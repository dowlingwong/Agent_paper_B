import math
import pytest
from r1.c3.d8_point_statistics import node_iqm, node_equal_probability_of_improvement


def test_iqm_quantile_boundaries_and_order():
    assert node_iqm([9]) == 9
    assert node_iqm([4, 1, 3, 2]) == 2.5
    assert node_iqm([4, 0, 2, 3, 1]) == 2
    assert node_iqm([1, 2, 100]) == pytest.approx(109 / 6)


def test_probability_is_paired_ties_half_and_equal_node_weight():
    assert node_equal_probability_of_improvement([([3, 1], [2, 1]), ([0], [1])]) == 0.375
    assert node_equal_probability_of_improvement([([1], [1]), ([2, 2, 2], [1, 1, 1])]) == 0.75


@pytest.mark.parametrize('bad', [[], [True], [math.nan], [math.inf], ['1']])
def test_iqm_refuses_invalid_inputs(bad):
    with pytest.raises(ValueError): node_iqm(bad)


@pytest.mark.parametrize('bad', [[], [([], [])], [([1, 2], [1])], [([True], [0])], [([0], [math.nan])]])
def test_probability_refuses_invalid_inputs(bad):
    with pytest.raises(ValueError): node_equal_probability_of_improvement(bad)
