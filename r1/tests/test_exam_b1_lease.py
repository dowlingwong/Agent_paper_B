"""B1 lease unit tests with temporary files and synthetic child processes only."""
import os
import subprocess
import sys
from pathlib import Path
import pytest
from r1.exam.b1_lease import B1LeaseStop, acquire, verify_server_fd
from r1.exam.runtime import ExamRunner, PreparationStop, handle_live_orphan


def test_shared_lock_is_exclusive_and_not_unlinked(tmp_path):
    path=tmp_path/'gpu0.lock';fd=acquire(path)
    try:
        with pytest.raises(B1LeaseStop,match='held'): acquire(path)
    finally: os.close(fd)
    assert path.is_file()
    fd=acquire(path);os.close(fd)


def test_lock_survives_parent_fd_close_when_child_inherits(tmp_path):
    path=tmp_path/'gpu0.lock';fd=acquire(path)
    child=subprocess.Popen([sys.executable,'-c','import sys; sys.stdin.read()'],stdin=subprocess.PIPE,pass_fds=(fd,))
    os.close(fd)
    try:
        with pytest.raises(B1LeaseStop,match='held'): acquire(path)
    finally:
        child.stdin.close();child.wait(timeout=5)
    fd=acquire(path);os.close(fd)


def test_symlink_lock_and_server_fd_mismatch_fail(tmp_path):
    path=tmp_path/'gpu0.lock';fd=acquire(path)
    try:
        alias=tmp_path/'alias';alias.symlink_to(path)
        with pytest.raises(B1LeaseStop): acquire(alias)
        proc=tmp_path/'proc'/'42'/'fd';proc.mkdir(parents=True)
        (proc/str(fd)).symlink_to(path)
        verify_server_fd(fd,42,tmp_path/'proc')
        (tmp_path/'other').write_text('x')
        other_proc=tmp_path/'proc'/'43'/'fd';other_proc.mkdir(parents=True)
        (other_proc/str(fd)).symlink_to(tmp_path/'other')
        with pytest.raises(B1LeaseStop,match='identity'): verify_server_fd(fd,43,tmp_path/'proc')
    finally: os.close(fd)


def test_real_b1_server_cannot_start_without_lease():
    runner=ExamRunner.__new__(ExamRunner)
    runner.state={'phase':'b1'};runner.cfg={'dryrun':False};runner.b1_lease_fd=None
    with pytest.raises(PreparationStop,match='lease is missing before server start'):
        runner._server({},'off',32768)


def test_b1_previous_server_is_never_signalled(monkeypatch):
    from r1.exam import runtime
    monkeypatch.setattr(runtime.lsi,'orphan_matches',lambda *a:pytest.fail('must not take over'))
    monkeypatch.setattr(runtime.lsi,'stop_orphan',lambda *a:pytest.fail('must not signal'))
    with pytest.raises(PreparationStop,match='preserve without signalling'):
        handle_live_orphan({'pid':123},'b1')
