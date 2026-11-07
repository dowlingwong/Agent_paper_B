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


def test_audit_failure_stops_group_and_does_not_submit_remaining(tmp_path):
    configs = {str(i): {'files': {}} for i in range(5)}
    with patch('concurrent.futures.ProcessPoolExecutor', Pool), \
         patch.object(campaign.os, 'getpid', return_value=123), \
         patch.object(campaign.os, 'getpgrp', return_value=123), \
         patch.object(campaign.os, 'killpg') as kill, \
         patch('signal.signal'):
        with pytest.raises(RuntimeError, match='audit failure'):
            campaign.run_b1_audits('digits_mlp', configs,
                {'workers': 2, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)
    assert len(Pool.current.submitted) == 2
    assert Pool.current.submitted[1].cancelled()
    kill.assert_called_once()


def test_audit_refuses_shared_process_group(tmp_path):
    with patch.object(campaign.os, 'getpid', return_value=123), \
         patch.object(campaign.os, 'getpgrp', return_value=456):
        with pytest.raises(RuntimeError, match='process-group leader'):
            campaign.run_b1_audits('digits_mlp', {},
                {'workers': 2, 'audit_seeds': [1]}, tmp_path, {}, lambda: None)
