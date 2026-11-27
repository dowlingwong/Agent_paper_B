"""Check the proposed D.3 verify worker seeds before pre-declaration and launch."""

import argparse
import json

from r1.c3.d3_analysis import (
    LLM_CALL_CAP,
    RESERVED_SEED_NAMESPACES,
    D3InputError,
    declared_d3_seeds,
    sweep_instance_seed_universe,
)

VERIFY_SEED_BASE = 20_000
VERIFY_RUNS = 2


def check_verify_namespaces(verify_seed_base: int = VERIFY_SEED_BASE) -> dict:
    """Check both seeds at every possible verify index up to the proposer call cap."""
    if type(verify_seed_base) is not int or verify_seed_base < 0:
        raise D3InputError("verify_seed_base must be a non-negative integer")

    seeds = {
        verify_seed_base + 10 * budget_index + pair_index
        for budget_index in range(1, LLM_CALL_CAP + 1)
        for pair_index in range(VERIFY_RUNS)
    }
    for name, namespace in declared_d3_seeds().items():
        overlap = seeds & namespace
        if overlap:
            raise D3InputError(f"D.3 verify seeds meet {name!r} at {min(overlap)}")

    for name, interval in RESERVED_SEED_NAMESPACES.items():
        if interval is None:
            overlap = seeds & sweep_instance_seed_universe()
        else:
            low, high = interval
            overlap = {seed for seed in seeds if low <= seed <= high}
        if overlap:
            raise D3InputError(f"D.3 verify seeds meet reserved namespace {name!r} at {min(overlap)}")

    return {
        "verdict": "PASS",
        "verify_seed_base": verify_seed_base,
        "verify_runs": VERIFY_RUNS,
        "checked_budget_indexes": [1, LLM_CALL_CAP],
        "min_seed": min(seeds),
        "max_seed": max(seeds),
        "seed_count": len(seeds),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        verdict = check_verify_namespaces()
    except D3InputError as exc:
        parser.exit(1, f"STOP: {exc}\n")
    print(json.dumps(verdict, sort_keys=True))


if __name__ == "__main__":
    main()
