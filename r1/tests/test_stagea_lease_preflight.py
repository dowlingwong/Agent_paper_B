"""Preflight fixture guard rails only; it never starts a server, model or GPU here."""
from r1.tests import stagea_lease_preflight as preflight


def test_preflight_refuses_without_lease_evidence_dir(monkeypatch, tmp_path):
    monkeypatch.delenv('TRACKX_LEASE_EVIDENCE_DIR', raising=False)
    monkeypatch.delenv('TRACKX_GPU_LEASE_FD', raising=False)
    import pytest
    with pytest.raises(RuntimeError, match='guardian evidence directory absent'):
        preflight.main(['--config', '/nonexistent', '--out', str(tmp_path / 'out'), '--candidate', 'x'])


def test_preflight_refuses_without_inherited_fd(monkeypatch, tmp_path):
    import pytest
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(evidence))
    monkeypatch.delenv('TRACKX_GPU_LEASE_FD', raising=False)
    with pytest.raises(RuntimeError, match='inherited GPU lease FD absent'):
        preflight.main(['--config', '/nonexistent', '--out', str(tmp_path / 'out'), '--candidate', 'x'])
