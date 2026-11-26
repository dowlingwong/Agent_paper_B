import math
import random
import pytest
from r1.c3.d8_inference_primitives import holm_two, stratified_indices


def test_reproducible_explicit_seed_and_node_strata():
    def run(seed):
        rng = random.Random(seed)
        return list(stratified_indices([3, 1, 2], draws=2000, randbelow=rng.randrange))
    a = run(1234)
    assert len(a) == 2000 and a == run(1234) and a != run(1235)
    assert all(len(x) == 3 and len(x[0]) == 3 and x[1] == (0,) and len(x[2]) == 2 for x in a)
    assert all(all(0 <= j < n for j in part) for x in a for n, part in zip([3, 1, 2], x))


def test_invalid_sampler_output_rejected():
    with pytest.raises(ValueError): list(stratified_indices([2], draws=1, randbelow=lambda n: True))
    with pytest.raises(ValueError): list(stratified_indices([2], draws=1, randbelow=lambda n: n))


@pytest.mark.parametrize('sizes,draws', [([], 1), ([0], 1), ([True], 1), ([1], 0), ([1], True)])
def test_invalid_dimensions(sizes, draws):
    with pytest.raises(ValueError): stratified_indices(sizes, draws=draws, randbelow=lambda n: 0)


def test_holm_two_adjustment_order_ties_and_caps():
    assert holm_two(.01, .04) == {'A3': .02, 'A5': .04}
    assert holm_two(.8, .01) == {'A3': .8, 'A5': .02}
    assert holm_two(.03, .03) == {'A3': .06, 'A5': .06}
    assert holm_two(.9, 1.0) == {'A3': 1.0, 'A5': 1.0}


@pytest.mark.parametrize('bad', [-.01, 1.01, math.nan, math.inf, True, '0.01'])
def test_holm_rejects_invalid_pvalues(bad):
    with pytest.raises(ValueError): holm_two(bad, .01)
