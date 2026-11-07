import os
import signal
import subprocess
from unittest.mock import Mock
import pytest
from r1.scripts import b1_engineering_timeout as t


def test_group_identity_checked_before_signal(monkeypatch):
    child=Mock(pid=1234)
    calls=[]
    monkeypatch.setattr(t, 'observed_exit', lambda child: calls.append('identity'))
    monkeypatch.setattr(t.os, 'killpg', lambda pid,sig: calls.append((pid,sig)))
    monkeypatch.setattr(t.time, 'sleep', lambda n: None)
    t.stop_owned_group(child)
    assert calls == ['identity', (1234,signal.SIGTERM), (1234,signal.SIGKILL)]
    child.wait.assert_called_once_with(timeout=30)


def test_nonchild_is_never_signalled(monkeypatch):
    child=Mock(pid=1234)
    def fail(child): raise ChildProcessError('not our child')
    monkeypatch.setattr(t, 'observed_exit', fail)
    kill=Mock(); monkeypatch.setattr(t.os, 'killpg',kill)
    with pytest.raises(ChildProcessError): t.stop_owned_group(child)
    kill.assert_not_called(); child.wait.assert_not_called()


def test_signal_failure_still_reaps_own_child(monkeypatch):
    child=Mock(pid=1234)
    monkeypatch.setattr(t, 'observed_exit', lambda child: None)
    monkeypatch.setattr(t.os, 'killpg', Mock(side_effect=PermissionError('refused')))
    with pytest.raises(PermissionError): t.stop_owned_group(child)
    child.wait.assert_called_once_with(timeout=30)
