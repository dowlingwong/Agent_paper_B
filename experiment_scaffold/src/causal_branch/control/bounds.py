"""Shared one-sided Hoeffding bounds for the declared contrast range (F3).

Both the replay-allowance module and the allocator must use the same radius.
The signed contrast ``d(W)*(U^v - U^0)`` lies in ``[-1, 1]`` for ``U`` in
``[0, 1]``, so the default width is **2**.  A width of 1 silently halves every
radius; deriving the width from the declared contrast range is the point of
this module.
"""

from __future__ import annotations

import math

import numpy as np

DEFAULT_CONTRAST_RANGE = (-1.0, 1.0)
DEFAULT_CONTRAST_WIDTH = 2.0


def contrast_width(contrast_range=DEFAULT_CONTRAST_RANGE) -> float:
    low, high = contrast_range
    if not low < high:
        raise ValueError("contrast_range must be ordered")
    return float(high - low)


def hoeffding_radius(n, alpha, *, width: float = DEFAULT_CONTRAST_WIDTH) -> float:
    """One-sided Hoeffding radius ``width * sqrt(log(1/alpha) / (2n))``."""

    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must lie in (0,1)")
    if not width > 0.0:
        raise ValueError("width must be positive")
    return float(width) * math.sqrt(math.log(1.0 / float(alpha)) / (2.0 * n))


def radius_for_range(n, alpha, contrast_range=DEFAULT_CONTRAST_RANGE) -> float:
    return hoeffding_radius(n, alpha, width=contrast_width(contrast_range))


def one_sided_lcb(values, alpha, *, contrast_range=DEFAULT_CONTRAST_RANGE) -> float:
    """Mean minus the shared radius; refuses empty/non-finite input."""

    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("values must be a non-empty 1-D array")
    if not np.isfinite(values).all():
        raise ValueError("values must be finite")
    return float(np.mean(values)) - radius_for_range(values.size, alpha, contrast_range)
