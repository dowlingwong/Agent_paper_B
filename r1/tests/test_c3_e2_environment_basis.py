"""e2 (R1-B2-GO): B6 (a) environment basis from the published, reviewed e1 replay report and its checks;
B1 (a) publication on origin/main; the B.2 addendum precondition. Synthetic fixtures only."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from r1.c3 import audit

REPORT = 'docs/r1/reports/e1_replay_20261117'
REVIEW = 'docs/r1/reviews/E1_AMEND_RUN_REVIEW_20261117.md'
PLAN_ROW = ('| R1-B2-GO | e2: B.2 starts (ops-e1-replay-amend-20261117 @ 52992b22, E1_AMEND_RUN_REVIEW_20261117.md); '
            '**B6 (a)** replay report; **B4 (a)** probe record; **B1 (a)** origin/main; deepthought CPU. |\n')
INTERPRETER = {'build': audit.sys.version, 'prefix': '/ceph/venv', 'wrapper_target': '/ceph/venv/bin/python',
               'package_list_sha256': 'c0924', 'newest_dist_info_mtime_utc': '2026-10-26T22:09:12.359336+00:00',
               'python_version': '3.13.15', 'library_versions': {'numpy': '2.4.4', 'pandas': '3.0.3',
                                                                 'scikit-learn': '1.8.0', 'scipy': '1.17.1'}}


CACHES = {node: f'{i}' * 64 for i, node in enumerate(audit.E1_OPENML_CACHE_NODES)}
SUMMARY = {'verdict': 'PASS', 'stop': None, 'tolerance': 0, 'cases_planned': 16, 'cases_run': 16, 'cases_passed': 16,
           'openml_offline_mechanism': {'row': 'R1-E1-OPENML-AMEND', 'post_run': {'source_caches': CACHES}}}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True,
                                   env={**os.environ, 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@t',
                                        'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@t'}).strip()


def fixture(root: Path, monkeypatch, *, summary=None, pins=None, review='text\n\nVERDICT: ACCEPTED\n', plan=PLAN_ROW):
    """A real git checkout with a bare origin: commit 1 carries the e1 report (pinned as E1_REPLAY_COMMIT),
    commit 2 the PLAN row; origin/main is fetched and equals the remote."""
    report = root / REPORT
    report.mkdir(parents=True)
    (root / 'docs/r1/reviews').mkdir(parents=True)
    summary = summary or SUMMARY
    pins = pins or {'harness': {'commit': '6adf3859de66c4814fcf376eed59880fbd8eeaf7', 'path': str(root / 'harness'),
                                'uv_lock_sha256': 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090',
                                'tracked_clean': True, 'pre_existing_untracked_caches': True},
                    'interpreter': INTERPRETER, 'preserved_batch': {'path': audit.E1_REPLAY_BATCH}}
    (report / 'summary.json').write_text(json.dumps(summary))
    (report / 'pins.json').write_text(json.dumps(pins))
    for name in ('REPORT.md', 'cases.jsonl', 'SHA256SUMS.txt'):
        (report / name).write_text(name)
    (root / REVIEW).write_text(review)
    git(root.parent, 'init', '-q', '-b', 'main', str(root))
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'e1 report')
    monkeypatch.setattr(audit, 'E1_REPLAY_COMMIT', git(root, 'rev-parse', 'HEAD'))
    (root / 'docs/r1/PLAN.md').write_text(plan)
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'plan row')
    origin = root.parent / (root.name + '_origin.git')
    git(root.parent, 'init', '-q', '--bare', str(origin))
    git(root, 'remote', 'add', 'origin', str(origin))
    git(root, 'push', '-q', 'origin', 'main')
    git(root, 'fetch', '-q', 'origin')
    pinned = {rel: sha(root / rel) for rel in audit.E1_REPLAY_PINNED}
    monkeypatch.setattr(audit, 'E1_REPLAY_PINNED', pinned)
    return origin


def publish_from(root, monkeypatch):
    """Stand-in for origin/main (addendum tests): published bytes are the fixture files under *root*."""
    read = []
    def published_bytes(_root, rel):
        read.append(rel)
        path = Path(root) / rel
        if not path.is_file():
            raise ValueError(f'NOT CHECKABLE: {rel} is not published on origin/main')
        return path.read_bytes()
    monkeypatch.setattr(audit, '_published_bytes', published_bytes)
    return read


def test_published_reviewed_replay_is_the_environment_basis(tmp_path, monkeypatch):
    root = tmp_path / 'paper'
    fixture(root, monkeypatch)
    basis = audit.replay_environment_basis(root)
    assert basis['ruling'] == 'R1-B2-GO B6 (a)' and basis['e1_commit'] == audit.E1_REPLAY_COMMIT
    assert basis['interpreter']['package_list_sha256'] == 'c0924'
    assert basis['data_caches_sha256'] == CACHES
    assert 'not a launch-bound snapshot' in basis['disclosure'] and 'all 288 roots' in basis['disclosure']


def test_an_erratum_on_main_neither_blocks_nor_invalidates(tmp_path, monkeypatch):
    """Review round 1, finding 3: the pinned files are read at the e1 commit, not at main's tip."""
    root = tmp_path / 'paper'
    fixture(root, monkeypatch)
    (root / REPORT / 'REPORT.md').write_text('corrected per the e1 review minors')
    git(root, 'commit', '-qam', 'erratum')
    git(root, 'push', '-q', 'origin', 'main')
    git(root, 'fetch', '-q', 'origin')
    assert audit.replay_environment_basis(root)['files_sha256'] == audit.E1_REPLAY_PINNED


def test_replay_basis_rejects_changed_bytes_at_the_e1_commit(tmp_path, monkeypatch):
    root = tmp_path / 'paper'
    fixture(root, monkeypatch)
    monkeypatch.setitem(audit.E1_REPLAY_PINNED, f'{REPORT}/REPORT.md', '0' * 64)
    with pytest.raises(ValueError, match='differs from the reviewed bytes'):
        audit.replay_environment_basis(root)


def test_replay_basis_requires_the_e1_commit_on_published_main(tmp_path, monkeypatch):
    root = tmp_path / 'paper'
    origin = fixture(root, monkeypatch)
    git(root, 'checkout', '-q', '--orphan', 'other')
    git(root, 'commit', '-q', '--allow-empty', '-m', 'unrelated history')
    git(root, 'push', '-q', '-f', 'origin', 'other:main')
    git(root, 'fetch', '-q', '-f', 'origin')
    with pytest.raises(ValueError, match='not an ancestor of published main'):
        audit.replay_environment_basis(root)


def test_published_bytes_fail_closed_without_a_reachable_main(tmp_path):
    with pytest.raises(ValueError, match='not reachable|stale'):
        audit._published_bytes(tmp_path, 'docs/r1/PLAN.md')


def test_published_bytes_refuse_a_stale_fetch_and_read_the_remote_not_the_worktree(tmp_path, monkeypatch):
    root = tmp_path / 'paper'
    fixture(root, monkeypatch)
    (root / 'docs/r1/PLAN.md').write_text('local edit, never published\n')
    assert audit._published_bytes(root, 'docs/r1/PLAN.md').decode() == PLAN_ROW
    other = tmp_path / 'other_clone'
    git(tmp_path, 'clone', '-q', '-b', 'main', str(tmp_path / 'paper_origin.git'), str(other))
    (other / 'docs/r1/PLAN.md').write_text(PLAN_ROW + '| R1-NEW | x |\n')
    git(other, 'commit', '-qam', 'new row')
    git(other, 'push', '-q', 'origin', 'main')
    with pytest.raises(ValueError, match='stale'):
        audit._published_bytes(root, 'docs/r1/PLAN.md')


def test_pinned_hashes_equal_the_reviewed_e1_commit():
    """The real pins against the real e1 commit, when this checkout has it (it is merged on this branch)."""
    from r1.harness import REPO
    try:
        subprocess.run(['git', '-C', str(REPO), 'cat-file', '-e', audit.E1_REPLAY_COMMIT], check=True,
                       capture_output=True)
    except (subprocess.CalledProcessError, OSError):
        pytest.skip('e1 replay commit not in this checkout')
    for rel, want in audit.E1_REPLAY_PINNED.items():
        data = subprocess.check_output(['git', '-C', str(REPO), 'show', f'{audit.E1_REPLAY_COMMIT}:{rel}'])
        assert hashlib.sha256(data).hexdigest() == want, rel
    summary = json.loads(subprocess.check_output(
        ['git', '-C', str(REPO), 'show', f'{audit.E1_REPLAY_COMMIT}:{REPORT}/summary.json']))
    assert sorted(summary['openml_offline_mechanism']['post_run']['source_caches']) == \
        sorted(audit.E1_OPENML_CACHE_NODES)


@pytest.mark.parametrize('change', [{'verdict': 'STOP'}, {'tolerance': 1e-12}, {'cases_passed': 15},
                                    {'stop': 'x'}, {'openml_offline_mechanism': {'row': 'R1-E1-OPENML'}}])
def test_replay_basis_requires_a_full_pass(tmp_path, monkeypatch, change):
    summary = {**SUMMARY, **change}
    fixture(tmp_path / 'paper', monkeypatch, summary=summary)
    with pytest.raises(ValueError, match='16/16 PASS'):
        audit.replay_environment_basis(tmp_path / 'paper')


def test_replay_basis_requires_an_accepted_review_and_the_plan_row(tmp_path, monkeypatch):
    fixture(tmp_path / 'paper', monkeypatch, review='VERDICT: NOT ACCEPTED\n')
    with pytest.raises(ValueError, match='VERDICT: ACCEPTED'):
        audit.replay_environment_basis(tmp_path / 'paper')
    other = tmp_path / 'other'
    fixture(other, monkeypatch, plan='| R1-B2-DECOUPLE | B.2 does not start |\n')
    with pytest.raises(ValueError, match='R1-B2-GO missing'):
        audit.replay_environment_basis(other)


def test_replay_basis_requires_the_sweep_runtime_pins(tmp_path, monkeypatch):
    pins = {'harness': {'commit': '0' * 40, 'path': '/h',
                        'uv_lock_sha256': 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090'},
            'interpreter': INTERPRETER, 'preserved_batch': {'path': audit.E1_REPLAY_BATCH}}
    fixture(tmp_path / 'paper', monkeypatch, pins=pins)
    with pytest.raises(ValueError, match='sweep-1 runtime'):
        audit.replay_environment_basis(tmp_path / 'paper')


def test_replay_basis_requires_the_cache_digests_and_harness_state(tmp_path, monkeypatch):
    summary = {**SUMMARY, 'openml_offline_mechanism': {'row': 'R1-E1-OPENML-AMEND', 'post_run': {'source_caches': {}}}}
    fixture(tmp_path / 'paper', monkeypatch, summary=summary)
    with pytest.raises(ValueError, match='six OpenML cache digests'):
        audit.replay_environment_basis(tmp_path / 'paper')


def _checks(monkeypatch, tmp_path, observed=None, stop=None):
    from r1.scripts import c3_env_replay
    current = {'build': INTERPRETER['build'], 'prefix': INTERPRETER['prefix'],
               'wrapper_target': INTERPRETER['wrapper_target'],
               'current_package_list_sha256': INTERPRETER['package_list_sha256'],
               'newest_dist_info_mtime_utc': INTERPRETER['newest_dist_info_mtime_utc'], **(observed or {})}
    def check(batch, harness):
        assert str(batch) == audit.E1_REPLAY_BATCH and str(harness) == audit.E1_REPLAY_BATCH + '/autoresearch_harness'
        if stop:
            raise c3_env_replay.Stop(stop)
        return current
    monkeypatch.setattr(c3_env_replay, 'check_environment', check)
    monkeypatch.setenv('AR_HARNESS_ROOT', str(tmp_path / 'harness'))
    monkeypatch.setattr(audit.sys, 'prefix', INTERPRETER['prefix'])
    return {'harness_path': str(tmp_path / 'harness'),
            'interpreter': {k: v for k, v in INTERPRETER.items() if k != 'library_versions'}}


def test_current_environment_checks_match_the_replay(tmp_path, monkeypatch):
    basis = _checks(monkeypatch, tmp_path)
    checks = audit.replay_environment_checks(basis)
    assert checks['package_list_sha256'] == 'c0924' and checks['checked_utc'].endswith('Z')


@pytest.mark.parametrize('field,value', [('current_package_list_sha256', 'other'),
                                         ('newest_dist_info_mtime_utc', '2026-11-20T00:00:00+00:00'),
                                         ('prefix', '/other'), ('wrapper_target', '/other/python')])
def test_current_environment_differing_from_the_replay_stops(tmp_path, monkeypatch, field, value):
    basis = _checks(monkeypatch, tmp_path, observed={field: value})
    with pytest.raises(ValueError, match='differs from the e1 replay record'):
        audit.replay_environment_checks(basis)


def test_replay_check_stop_and_wrong_harness_stop(tmp_path, monkeypatch):
    basis = _checks(monkeypatch, tmp_path, stop='dist-info modified at or after launch')
    with pytest.raises(ValueError, match='e1 replay environment check failed now'):
        audit.replay_environment_checks(basis)
    basis = _checks(monkeypatch, tmp_path)
    monkeypatch.setenv('AR_HARNESS_ROOT', str(tmp_path / 'elsewhere'))
    with pytest.raises(ValueError, match='not the harness the e1 replay checked'):
        audit.replay_environment_checks(basis)


def test_audit_interpreter_must_be_the_replayed_one(tmp_path, monkeypatch):
    basis = _checks(monkeypatch, tmp_path)
    monkeypatch.setattr(audit.sys, 'prefix', '/another/venv')
    with pytest.raises(ValueError, match='interpreter the e1 replay checked'):
        audit.replay_environment_checks(basis)


def _addendum(root, monkeypatch, text, name='c3_b2_addendum_20261117.md'):
    path = root / 'docs/r1/authorizations' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return f'docs/r1/authorizations/{name}', publish_from(root, monkeypatch)


def test_addendum_binds_ruling_code_harness_and_k(tmp_path, monkeypatch):
    commit = 'a' * 40
    text = f'R1-B2-GO\nPaper code {commit}\nHarness 6adf3859de66c4814fcf376eed59880fbd8eeaf7\nK = 10\n'
    rel, published = _addendum(tmp_path, monkeypatch, text)
    record = audit.b2_addendum(tmp_path, rel, commit)
    assert record == {'path': rel, 'sha256': sha(tmp_path / rel)}
    assert published == [rel]
    with pytest.raises(ValueError, match='repository-relative'):
        audit.b2_addendum(tmp_path, tmp_path / rel, commit)
    with pytest.raises(ValueError, match='does not bind'):
        audit.b2_addendum(tmp_path, rel, 'b' * 40)


def test_addendum_must_exist_in_the_authorizations_directory(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match='addendum required'):
        audit.b2_addendum(tmp_path, None, 'a' * 40)
    rel, _ = _addendum(tmp_path, monkeypatch, 'R1-B2-GO', name='other.md')
    with pytest.raises(ValueError, match='c3_b2_addendum_'):
        audit.b2_addendum(tmp_path, rel, 'a' * 40)
    with pytest.raises(ValueError, match='not published'):
        audit.b2_addendum(tmp_path, 'docs/r1/authorizations/c3_b2_addendum_missing.md', 'a' * 40)


# ---------------------------------------------------------------- review round 1, finding 1: the e1 harness state

def _harness(tmp_path, untracked=()):
    from r1.scripts.c3_env_replay import tree_digest
    h = tmp_path / 'harness'
    (h / 'src').mkdir(parents=True)
    (h / 'src' / 'x.py').write_text('x = 1\n')
    for node in audit.E1_OPENML_CACHE_NODES:
        d = h / 'nodes' / node / 'data_cache'
        d.mkdir(parents=True)
        if node in ('openml_climate', 'openml_sonar'):     # these ship a tracked .gitignore at 6adf385
            (d / '.gitignore').write_text('*\n!.gitignore\n')
    git(tmp_path, 'init', '-q', '-b', 'main', str(h))
    git(h, 'add', '-A')
    git(h, 'commit', '-q', '-m', 'harness')
    for node in audit.E1_OPENML_CACHE_NODES:
        (h / 'nodes' / node / 'data_cache' / f'{node}.arff').write_text(node)
    (h / 'paper' / 'tables').mkdir(parents=True)
    (h / 'paper' / 'tables' / 'artifact_completeness_report.txt').write_text('r')
    for rel in untracked:
        (h / rel).parent.mkdir(parents=True, exist_ok=True)
        (h / rel).write_text('stray')
    digests = {n: tree_digest(h / 'nodes' / n / 'data_cache') for n in audit.E1_OPENML_CACHE_NODES}
    return h, {'data_caches_sha256': digests}


def test_harness_with_exactly_the_e1_untracked_files_is_accepted(tmp_path):
    h, basis = _harness(tmp_path)
    assert git(h, 'status', '--porcelain', '--untracked-files=all')        # the old check would have STOPped
    state = audit.harness_untracked_state(h, basis)
    assert state['data_caches_sha256'] == basis['data_caches_sha256'] and state['untracked_count'] >= 5


def test_harness_untracked_outside_the_e1_record_or_changed_caches_stop(tmp_path):
    h, basis = _harness(tmp_path, untracked=['src/shadow.py'])
    with pytest.raises(ValueError, match='outside the e1 record'):
        audit.harness_untracked_state(h, basis)
    h2, basis2 = _harness(tmp_path / 'b')
    (h2 / 'nodes' / 'openml_wdbc' / 'data_cache' / 'openml_wdbc.arff').write_text('changed')
    with pytest.raises(ValueError, match='e1 post-run tree digests'):
        audit.harness_untracked_state(h2, basis2)
