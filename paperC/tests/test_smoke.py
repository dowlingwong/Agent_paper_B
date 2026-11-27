"""Scaffold smoke test (runbook P0): the package imports and declares its schema version."""
import paperc


def test_package_imports():
    assert paperc.SCHEMA_VERSION == "spt_transition/v1"
