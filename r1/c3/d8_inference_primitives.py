"""Synthetic-only resampling indices and two-hypothesis Holm arithmetic.

No data reader, bootstrap interval convention, random seed/PRNG policy,
composite hypothesis, gate decision, or authorization is selected here.
"""
import math


def stratified_indices(node_sizes, *, draws, randbelow):
    """Yield one vector of within-node sampled indices per draw.

    Caller supplies an explicitly seeded sampling function and number of
    replicates. Apply the same vector to all paired quantities in a node.
    The caller must bind seed, RNG algorithm, node order and provenance.
    """
    if not isinstance(node_sizes, (list, tuple)) or not node_sizes:
        raise ValueError('node sizes must be a nonempty sequence')
    if any(type(n) is not int or n <= 0 for n in node_sizes):
        raise ValueError('node sizes must be positive integers')
    if type(draws) is not int or draws <= 0 or not callable(randbelow):
        raise ValueError('explicit draw count and sampler required')
    sizes = tuple(node_sizes)
    def generate():
        for _ in range(draws):
            sample = []
            for n in sizes:
                indices = []
                for _ in range(n):
                    i = randbelow(n)
                    if type(i) is not int or not 0 <= i < n:
                        raise ValueError('sampler produced invalid index')
                    indices.append(i)
                sample.append(tuple(indices))
            yield tuple(sample)
    return generate()


def holm_two(p_a3, p_a5):
    """Return ordinary two-test Holm adjusted p-values; no gate decision."""
    for p in (p_a3, p_a5):
        if type(p) not in (int, float):
            raise ValueError('p-values must be numeric')
        try:
            valid = math.isfinite(p) and 0 <= p <= 1
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError('p-values must be finite and in [0,1]')
    first, second = sorted((('A3', p_a3), ('A5', p_a5)), key=lambda row: row[1])
    adjusted_first = min(1.0, 2 * first[1])
    adjusted_second = min(1.0, max(adjusted_first, second[1]))
    return {first[0]: adjusted_first, second[0]: adjusted_second}
