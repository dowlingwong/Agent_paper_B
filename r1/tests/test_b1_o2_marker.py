import json
import os
import pytest
from r1.scripts import b1_o2_marker as marker


def test_create_is_exclusive_and_status_append(tmp_path):
    locks = tmp_path / 'locks'; locks.mkdir()
    status = tmp_path / 'STATUS.md'; status.write_text('original\n')
    receipt = marker.create(locks, status, 'b1-test', 'a' * 40)
    assert json.loads((locks / marker.NAME).read_text())['run_id'] == 'b1-test'
    assert status.read_text().startswith('original\n')
    assert receipt['ino'] == (locks / marker.NAME).stat().st_ino
    with pytest.raises(FileExistsError): marker.create(locks, status, 'second', 'a' * 40)
    assert 'second' not in status.read_text()


def test_mismatched_marker_is_preserved(tmp_path, monkeypatch):
    locks = tmp_path / 'locks'; locks.mkdir()
    status = tmp_path / 'STATUS.md'; status.write_text('original\n')
    receipt = marker.create(locks, status, 'b1-test', 'a' * 40)
    (locks / marker.NAME).write_text('changed')
    monkeypatch.setattr(marker.sys, 'platform', 'linux')
    with pytest.raises(RuntimeError, match='match receipt'): marker.retire(locks, receipt)
    assert (locks / marker.NAME).read_text() == 'changed'


def test_status_symlink_is_not_followed(tmp_path):
    locks = tmp_path / 'locks'; locks.mkdir()
    actual = tmp_path / 'actual'; actual.write_text('unchanged')
    link = tmp_path / 'link'; link.symlink_to(actual)
    with pytest.raises(OSError): marker.create(locks, link, 'b1-test', 'a' * 40)
    assert actual.read_text() == 'unchanged' and not (locks / marker.NAME).exists()


def test_status_parent_symlink_is_not_followed(tmp_path):
    locks = tmp_path / 'locks'; locks.mkdir()
    actual = tmp_path / 'actual'; actual.mkdir()
    status = actual / 'STATUS.md'; status.write_text('unchanged')
    link = tmp_path / 'link'; link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(RuntimeError, match='symlink'):
        marker.create(locks, link / 'STATUS.md', 'b1-test', 'a' * 40)
    assert status.read_text() == 'unchanged' and not (locks / marker.NAME).exists()
