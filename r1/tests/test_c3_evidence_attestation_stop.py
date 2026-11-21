"""e2 (R1-B2-GO): the task-native attestation STOP is replaced by B4 (a); EVIDENCE still fails closed
before any side effect without the published B.2 addendum and the e1-replayed environment basis.

Until 17 Nov 2026 this module tested that every EVIDENCE run and consumption stopped on the missing
task-native runtime attestation (7df307be). R1-B2-GO B4 (a) accepts the per-run worker_runtime probe
record with its limitation disclosed, so that STOP no longer exists; these tests now check what replaced it.
"""
import pytest

from r1.c3 import audit


@pytest.fixture(autouse=True)
def _after_test_release(monkeypatch):
    """These tests exercise the raw-block readers as they behave once the T0 test release row exists (PRE-STAGE A);
    the lock itself is tested in test_c3_release.py."""
    from r1.c3 import release
    monkeypatch.setattr(release, "test_released", lambda *a, **k: True)


def test_no_attestation_stop_remains():
    assert not hasattr(audit, '_require_task_native_runtime_attestation')


def test_worker_runtime_basis_discloses_the_probe_limitation():
    basis = audit.worker_runtime_basis()
    assert basis['ruling'] == 'R1-B2-GO B4 (a)'
    assert basis['record'] == 'runs.jsonl:worker_runtime'
    assert 'does not attest the task process itself' in basis['limitation']
    basis['limitation'] = 'changed'
    assert audit.worker_runtime_basis()['limitation'] != 'changed'  # a copy, never the shared constant


def test_evidence_without_addendum_stops_before_files(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: called.append('provenance') or {})
    monkeypatch.setattr(audit, 'evidence_environment', lambda *args: called.append('environment') or {})
    out = tmp_path / 'out'
    scratch = tmp_path / 'scratch'
    with pytest.raises(ValueError, match='addendum required'):
        audit.evidence_run(tmp_path, tmp_path, tmp_path, tmp_path, out, 1, 30, scratch_root=scratch)
    assert called == ['provenance']
    assert not out.exists()
    assert not scratch.exists()


def test_evidence_without_replay_report_stops_before_files(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'evidence_paper_provenance', lambda *args: {})
    monkeypatch.setattr(audit, 'b2_addendum', lambda *args: {'path': 'a', 'sha256': 'b'})
    out = tmp_path / 'out'
    with pytest.raises(ValueError, match='not reachable|not published'):
        audit.evidence_run(tmp_path, tmp_path, tmp_path, tmp_path, out, 1, 30, scratch_root=tmp_path / 's')
    assert not out.exists()


def test_evidence_consumption_still_refuses_a_legacy_or_stopped_audit(tmp_path):
    with pytest.raises(ValueError, match='unexpected label block path'):
        audit.verify_evidence_completion(tmp_path, tmp_path / 'audits.jsonl', tmp_path, tmp_path, tmp_path)
