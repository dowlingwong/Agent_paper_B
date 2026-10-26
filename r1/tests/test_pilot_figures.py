from r1.analysis.pilot_figures import waste_counts


def test_waste_counts_preserves_strata_and_categories():
    rows = [
        {"source": "a", "node": "n", "memory_mode": "none", "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "none", "inert_kind": "duplicate"},
        {"source": "a", "node": "n", "memory_mode": "on", "inert_kind": None},
    ]
    assert waste_counts(rows) == [("a", "n", "none", "duplicate", 2, 2, 1.0), ("a", "n", "on", "non-inert", 1, 1, 1.0)]
