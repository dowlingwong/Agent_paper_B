from concurrent.futures import Future
from unittest.mock import patch

import pytest

from r1.exam import campaign


class Pool:
    submitted = []

    def __init__(self, max_workers):
        self.submitted = []
        Pool.current = self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, fn, *args):
        future = Future()
        self.submitted.append(future)
        if len(self.submitted) == 1:
            future.set_exception(RuntimeError('audit failure'))
        return future


def test_audit_failure_notifies_parent_and_does_not_submit_remaining(tmp_path):
    configs = {str(i): {'files': {}} for i in range(5)}
    with patch('concurrent.futures.ProcessPoolExecutor', Pool), \
         patch.dict(campaign.os.environ, {'R1_B1_STOP_FD': '12'}), \
         patch.object(campaign.os, 'write') as notify:
        with pytest.raises(RuntimeError, match='audit failure'):
            campaign.run_b1_audits('digits_mlp', configs,
                {'workers': 2, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)
    assert len(Pool.current.submitted) == 2
    assert Pool.current.submitted[1].cancelled()
    notify.assert_called_once_with(12, b'1')


def test_audit_refuses_missing_stop_channel(tmp_path, monkeypatch):
    monkeypatch.delenv('R1_B1_STOP_FD', raising=False)
    with pytest.raises(KeyError, match='R1_B1_STOP_FD'):
        campaign.run_b1_audits('digits_mlp', {},
            {'workers': 2, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)


def test_audit_broken_log_still_notifies_parent(tmp_path):
    configs = {'a': {'files': {}}}
    with patch('concurrent.futures.ProcessPoolExecutor', Pool), \
         patch.dict(campaign.os.environ, {'R1_B1_STOP_FD': '12'}), \
         patch.object(campaign.os, 'write') as notify, \
         patch('builtins.print', side_effect=OSError('disk full')):
        with pytest.raises(RuntimeError, match='audit failure'):
            campaign.run_b1_audits('digits_mlp', configs,
                {'workers': 1, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)
    notify.assert_called_once_with(12, b'1')


def test_failed_pipe_creates_exclusive_parent_stop_marker(tmp_path):
    configs = {'a': {'files': {}}}
    with patch('concurrent.futures.ProcessPoolExecutor', Pool), \
         patch.dict(campaign.os.environ, {'R1_B1_STOP_FD': '12'}), \
         patch.object(campaign.os, 'write', side_effect=OSError('broken pipe')):
        with pytest.raises(RuntimeError, match='audit failure'):
            campaign.run_b1_audits('digits_mlp', configs,
                {'workers': 1, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)
    assert (tmp_path / 'audit_stop_notification').read_text().startswith('STOP: audit failure')
