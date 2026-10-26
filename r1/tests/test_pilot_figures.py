import json

import pytest

from r1.analysis.pilot_figures import PILOT, waste_counts


def test_waste_counts_preserves_strata_and_categories():
    rows = [
        {"source": "a", "node": "n", "memory_mode": "none", "inert": True, "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "none", "inert": True, "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "on", "inert": False, "inert_kind": None},
    ]
    assert waste_counts(rows) == [("a", "n", "none", "duplicate", 2, 2, 1.0), ("a", "n", "on", "non-inert", 1, 1, 1.0)]


def test_rejects_missing_and_contradictory_inert_labels():
    base = {"source": "a", "node": "n", "memory_mode": "none"}
    with pytest.raises(ValueError):
        waste_counts([base])
    with pytest.raises(ValueError):
        waste_counts([{**base, "inert": True, "inert_kind": None}])
    with pytest.raises(ValueError):
        waste_counts([{**base, "inert": False, "inert_kind": "duplicate"}])


def test_committed_pilot_categories_preserve_source_rows():
    with (PILOT / "proposals.jsonl").open() as handle:
        counts = waste_counts(json.loads(line) for line in handle if line.strip())
    assert sum(row[4] for row in counts) == 1323
    assert sum(row[4] for row in counts if row[3] == "duplicate") == 727
    assert all(row[5] > 0 and 0 <= row[6] <= 1 for row in counts)
