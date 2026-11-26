"""The nested DRYRUN source commit must work with either clean or edited trees."""
import subprocess
import pytest
from r1.scripts.rerun2_dryrun import commit_source_fixture


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


@pytest.mark.parametrize('changed', [False, True])
def test_fixture_commit_records_clean_or_modified_tree(tmp_path, changed):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    git(tmp_path, 'config', 'user.name', 'DRYRUN fixture')
    git(tmp_path, 'config', 'user.email', 'fixture@example.invalid')
    item=tmp_path/'tracked.txt'; item.write_text('original\n')
    git(tmp_path, 'add', 'tracked.txt')
    git(tmp_path, 'commit', '-qm', 'parent')
    parent=git(tmp_path, 'rev-parse', 'HEAD')
    if changed: item.write_text('revised\n')
    commit_source_fixture(tmp_path)
    assert git(tmp_path, 'rev-parse', 'HEAD^') == parent
    assert git(tmp_path, 'show', 'HEAD:tracked.txt') == ('revised' if changed else 'original')
    assert git(tmp_path, 'status', '--porcelain') == ''
