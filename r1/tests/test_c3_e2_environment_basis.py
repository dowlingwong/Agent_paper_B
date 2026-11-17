"""e2 (R1-B2-GO): B6 (a) environment basis from the published, reviewed e1 replay report and its checks;
B1 (a) publication on origin/main; the B.2 addendum precondition. Synthetic fixtures only."""
import hashlib
import json
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


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixture(root: Path, monkeypatch, *, summary=None, pins=None, review='text\n\nVERDICT: ACCEPTED\n', plan=PLAN_ROW):
    report = root / REPORT
    report.mkdir(parents=True)
    (root / 'docs/r1/reviews').mkdir(parents=True)
    summary = summary or {'verdict': 'PASS', 'stop': None, 'tolerance': 0, 'cases_planned': 16, 'cases_run': 16,
                          'cases_passed': 16, 'openml_offline_mechanism': {'row': 'R1-E1-OPENML-AMEND'}}
    pins = pins or {'harness': {'commit': '6adf3859de66c4814fcf376eed59880fbd8eeaf7', 'path': str(root / 'harness'),
                                'uv_lock_sha256': 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090'},
                    'interpreter': INTERPRETER, 'preserved_batch': {'path': audit.E1_REPLAY_BATCH}}
    (report / 'summary.json').write_text(json.dumps(summary))
    (report / 'pins.json').write_text(json.dumps(pins))
    for name in ('REPORT.md', 'cases.jsonl', 'SHA256SUMS.txt'):
        (report / name).write_text(name)
    (root / REVIEW).write_text(review)
    (root / 'docs/r1/PLAN.md').write_text(plan)
    pinned = {rel: sha(root / rel) for rel in audit.E1_REPLAY_PINNED}
    monkeypatch.setattr(audit, 'E1_REPLAY_PINNED', pinned)
    return publish_from(root, monkeypatch)


def publish_from(root, monkeypatch):
    """Stand-in for origin/main: published bytes are the fixture files under *root*."""
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
    published = fixture(tmp_path, monkeypatch)
    basis = audit.replay_environment_basis(tmp_path)
    assert basis['ruling'] == 'R1-B2-GO B6 (a)'
    assert basis['interpreter']['package_list_sha256'] == 'c0924'
    assert 'not a launch-bound snapshot' in basis['disclosure']
    # B1 (a): the PLAN row, every report file and the review are read from origin/main.
    assert sorted(published) == sorted(['docs/r1/PLAN.md', *audit.E1_REPLAY_PINNED])


def test_replay_basis_rejects_changed_bytes(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    (tmp_path / REPORT / 'REPORT.md').write_text('edited')
    with pytest.raises(ValueError, match='differs from the reviewed bytes'):
        audit.replay_environment_basis(tmp_path)


def test_replay_basis_rejects_unpublished_files(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch)
    publish_from(tmp_path / 'empty_main', monkeypatch)
    with pytest.raises(ValueError, match='not published on origin/main'):
        audit.replay_environment_basis(tmp_path)


def test_published_bytes_fail_closed_without_a_reachable_main(tmp_path):
    with pytest.raises(ValueError, match='not reachable|stale'):
        audit._published_bytes(tmp_path, 'docs/r1/PLAN.md')


@pytest.mark.parametrize('change', [{'verdict': 'STOP'}, {'tolerance': 1e-12}, {'cases_passed': 15},
                                    {'stop': 'x'}, {'openml_offline_mechanism': {'row': 'R1-E1-OPENML'}}])
def test_replay_basis_requires_a_full_pass(tmp_path, monkeypatch, change):
    summary = {'verdict': 'PASS', 'stop': None, 'tolerance': 0, 'cases_planned': 16, 'cases_run': 16,
               'cases_passed': 16, 'openml_offline_mechanism': {'row': 'R1-E1-OPENML-AMEND'}, **change}
    fixture(tmp_path, monkeypatch, summary=summary)
    with pytest.raises(ValueError, match='16/16 PASS'):
        audit.replay_environment_basis(tmp_path)


def test_replay_basis_requires_an_accepted_review_and_the_plan_row(tmp_path, monkeypatch):
    fixture(tmp_path, monkeypatch, review='VERDICT: NOT ACCEPTED\n')
    with pytest.raises(ValueError, match='VERDICT: ACCEPTED'):
        audit.replay_environment_basis(tmp_path / '.')
    other = tmp_path / 'other'
    other.mkdir()
    fixture(other, monkeypatch, plan='| R1-B2-DECOUPLE | B.2 does not start |\n')
    with pytest.raises(ValueError, match='R1-B2-GO missing'):
        audit.replay_environment_basis(other)


def test_replay_basis_requires_the_sweep_runtime_pins(tmp_path, monkeypatch):
    pins = {'harness': {'commit': '0' * 40, 'path': '/h',
                        'uv_lock_sha256': 'dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090'},
            'interpreter': INTERPRETER, 'preserved_batch': {'path': audit.E1_REPLAY_BATCH}}
    fixture(tmp_path, monkeypatch, pins=pins)
    with pytest.raises(ValueError, match='sweep-1 runtime'):
        audit.replay_environment_basis(tmp_path)


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
