"""Synthetic D13 tests; no model or real label data is loaded."""
import numpy as np
import pytest
from r1.c3.matched_view import MatchedView, bin_regression_cdf


class ForbiddenRows:
    def __iter__(self):
        raise AssertionError('unverified rows must not be consumed')


def test_pca_refuses_even_self_labelled_training_without_verified_provenance():
    with pytest.raises(RuntimeError, match='training-partition'):
        MatchedView().fit(ForbiddenRows(), None)
    with pytest.raises(RuntimeError, match='fitted'):
        MatchedView().transform([], np.ones((1, 20)))
    assert 'raw proposal' not in MatchedView.serialize([1., 2.])


def test_regression_cdf_is_binned_and_noop_stays_separate():
    p = bin_regression_cdf(np.linspace(.05, .95, 10))
    assert p.shape == (12,) and p[0] == 0 and p.sum() == pytest.approx(1)
    assert bin_regression_cdf(None, inert=True)[0] == 1
    with pytest.raises(ValueError, match='nondecreasing'):
        bin_regression_cdf(np.linspace(.95, .05, 10))
