"""The EVIDENCE entry point must fail before any side effects until attested."""
import pytest

from r1.c3 import audit


def test_evidence_stops_before_files_or_worker_preflight(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(audit, 'evidence_paper_provenance',
                        lambda *args: called.append('provenance'))
    out = tmp_path / 'out'
    scratch = tmp_path / 'scratch'
    with pytest.raises(ValueError, match='actual task-native runtime attestation'):
        audit.evidence_run(tmp_path, tmp_path, tmp_path, tmp_path, out, 1, 30,
                           scratch_root=scratch)
    assert called == []
    assert not out.exists()
    assert not scratch.exists()
