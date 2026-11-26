"""D25/P2 golden: the scripted proposer's sequence is unchanged by the
declaration-based action space.

The golden file was generated from pre-change code (harness 9c4902d) by
``python -m r1.scripts.gen_scripted_golden`` for every instance of
``E1b_20261012T161034Z``, repetitions 0-2, budget indices 1-20.

AI-assisted (BUILD_BATCH3, P2); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.headroom.scripted_golden import replay

GOLDEN = (
    Path(__file__).resolve().parent / "data"
    / "scripted_proposal_golden_E1b_20261012T161034Z.json"
)


def _load() -> dict:
    return json.loads(GOLDEN.read_text())


def test_golden_was_generated_before_the_change():
    payload = _load()
    assert payload["source_run"] == "E1b_20261012T161034Z"
    assert str(payload["harness_commit"]).startswith("9c4902d")  # pre-D25 harness


def test_every_seed_repetition_and_budget_index_is_identical():
    payload = _load()
    mismatches = []
    for instance, repetitions in payload["instances"].items():
        node, seed = instance.rsplit("__s", 1)
        for repetition, expected in repetitions.items():
            actual = replay(node, int(seed), int(repetition))
            if actual != expected:
                mismatches.append((instance, repetition))
    assert not mismatches, f"golden sequence changed for: {mismatches}"


def test_golden_covers_categorical_switches():
    payload = _load()
    symbols = {
        step["symbol"]
        for repetitions in payload["instances"].values()
        for sequence in repetitions.values()
        for step in sequence
    }
    assert {"model_type", "class_weight", "scaler"} <= symbols
