import pytest

from r1.c3.d3_analysis import LLM_CALL_CAP, sweep_instance_seed_universe
from r1.c3.d3_verify_namespaces import D3InputError, check_verify_namespaces


def test_proposed_verify_allocation_is_disjoint():
    assert check_verify_namespaces() == {
        "verdict": "PASS",
        "verify_seed_base": 20000,
        "verify_runs": 2,
        "checked_budget_indexes": [1, LLM_CALL_CAP],
        "min_seed": 20010,
        "max_seed": 20801,
        "seed_count": 160,
    }


@pytest.mark.parametrize(
    ("seed_base", "namespace"),
    [
        (1000, "D21 noise floors"),
        (6191, "instance"),
        (min(sweep_instance_seed_universe()) - 10, "sweep 1 and sweep 2 instance seeds"),
    ],
)
def test_refuses_the_first_conflicting_seed(seed_base, namespace):
    with pytest.raises(D3InputError, match=namespace):
        check_verify_namespaces(seed_base)


@pytest.mark.parametrize("seed_base", [True, -1, "20000"])
def test_refuses_an_invalid_seed_base(seed_base):
    with pytest.raises(D3InputError, match="non-negative integer"):
        check_verify_namespaces(seed_base)
