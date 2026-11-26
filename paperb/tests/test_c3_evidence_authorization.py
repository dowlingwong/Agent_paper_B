"""Isolated evidence admission tests; fixture outputs are not scientific evidence."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from r1.scripts import c3_label_sweep as sweep


def _repo(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


@pytest.fixture
def admission(tmp_path, monkeypatch):
    paper = tmp_path / 'paper'
    paper.mkdir()
    _repo(paper, 'init', '-q')
    note = paper / 'docs/r1/authorizations/new_batch.md'
    note.parent.mkdir(parents=True)
    config_file = paper / 'config.json'
    config_file.write_bytes((Path(__file__).resolve().parents[2] /
                             'r1/scripts/configs/c3_sweep_deepthought.json').read_bytes())
    cfg = json.loads(config_file.read_text())
    pins = {'harness_commit': 'a' * 40,
            'config_sha256': hashlib.sha256(config_file.read_bytes()).hexdigest(),
            'model_sha256': cfg['llamacpp']['model_sha256'], 'llamacpp_build': cfg['llamacpp']['build']}
    monkeypatch.setattr(sweep, 'DEEPTHOUGHT_AUTHORIZED_PINS', pins)
    monkeypatch.setenv('R1_C3_EVIDENCE_NOTE', 'docs/r1/authorizations/new_batch.md')
    monkeypatch.delenv('R1_DRYRUN', raising=False)
    batch = tmp_path / 'new_batch'
    batch.mkdir()
    payload = {'schema': 'r1.c3.new_b1_authorization/1',
               'decision': 'AUTHOR_AUTHORIZES_NEW_B1_EVIDENCE',
               'batch_name': batch.name, 'host': 'deepthought',
               'paper_commit_policy': 'main_at_launch', **pins}

    def commit_payload(data):
        note.write_text("Committed on the author's instruction (fixture).\n\n```json\n" +
                        json.dumps(data) + '\n```\n')
        _repo(paper, 'add', '.')
        _repo(paper, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
              'commit', '-qm', 'fixture authorization')
        return _repo(paper, 'rev-parse', 'HEAD')

    head = commit_payload(payload)
    runner = sweep.SweepRunner(sweep.load_config(config_file), batch=batch, paper=paper,
                               harness=tmp_path / 'harness', python='not-used', config_path=config_file)
    runner.host = 'deepthought'
    return runner, note, config_file, payload, head, commit_payload


def test_matching_committed_note_binds_batch_and_head(admission):
    runner, note, _, _, head, _ = admission
    record = runner.check_evidence_authorization(head, 'a' * 40)
    assert record == {'path': 'docs/r1/authorizations/new_batch.md',
                      'sha256': hashlib.sha256(note.read_bytes()).hexdigest(),
                      'paper_commit': head, 'batch_name': 'new_batch',
                      'pins': {k: admission[3][k] for k in ('harness_commit', 'config_sha256',
                                                           'model_sha256', 'llamacpp_build')}}
    assert runner.label == 'ENGINEERING_ONLY'  # no promotion until preconditions pass


def test_old_note_and_path_escape_refused(admission):
    runner, _, _, _, head, _ = admission
    for path in ('docs/r1/authorizations/c3_sweep1_20261027.md', '../other.md',
                 '/tmp/other.md', 'docs/r1/authorizations/../other.md'):
        runner.evidence_note = path
        with pytest.raises(sweep.Stop):
            runner.check_evidence_authorization(head, 'a' * 40)


def test_mismatch_and_uncommitted_note_refused(admission):
    runner, note, config, payload, head, commit = admission
    note.write_text(note.read_text() + 'uncommitted change')
    with pytest.raises(sweep.Stop):
        runner.check_evidence_authorization(head, 'a' * 40)
    wrong = {**payload, 'batch_name': 'another_batch'}
    head = commit(wrong)
    with pytest.raises(sweep.Stop):
        runner.check_evidence_authorization(head, 'a' * 40)
    head = commit(payload)
    config.write_text('changed config')
    with pytest.raises(sweep.Stop):
        runner.check_evidence_authorization(head, 'a' * 40)


def test_dryrun_and_existing_batch_never_promoted(admission, monkeypatch):
    runner, _, _, _, _, _ = admission
    monkeypatch.setattr(sweep, 'validate_dryrun', lambda: True)
    with pytest.raises(sweep.Stop):
        sweep.SweepRunner(runner.config, batch=runner.batch, paper=runner.paper,
                          harness=runner.harness, python='not-used')
    monkeypatch.setattr(sweep, 'validate_dryrun', lambda: False)
    (runner.batch / 'batch_state.json').write_text('{}')
    with pytest.raises(sweep.Stop):
        sweep.SweepRunner(runner.config, batch=runner.batch, paper=runner.paper,
                          harness=runner.harness, python='not-used')


def test_evidence_manifest_fails_closed(admission, tmp_path):
    runner, _, _, _, head, _ = admission
    authorization = runner.check_evidence_authorization(head, 'a' * 40)
    runner.label = 'EVIDENCE'
    runner.state['evidence_authorization'] = authorization
    runner.state['launch_provenance'] = {'paper_commit': head}
    out = tmp_path / 'out'
    out.mkdir()
    path = out / 'manifest.json'
    record = {'launch_provenance': {'paper_commit': head}, 'label': 'EVIDENCE',
              'evidence_authorization': authorization}
    path.write_text(json.dumps(record))
    runner.check_launch_manifest(out)
    path.write_text(json.dumps({**record, 'label': 'PILOT'}))
    with pytest.raises(sweep.Stop):
        runner.check_launch_manifest(out)
    # Engineering liveness remains engineering; it is not promoted.
    runner.check_launch_manifest(out, engineering_liveness=True)


def test_running_session_rechecks_its_own_authorization_not_legacy(admission, monkeypatch):
    runner, _, _, _, head, _ = admission
    record = runner.check_evidence_authorization(head, 'a' * 40)
    runner.label = 'EVIDENCE'
    runner.state.update(evidence_authorization=record, paper_head_at_launch=head,
                        scratch_root=str(runner.scratch), launch_provenance={
                            'paper_commit': head, **record['pins']})
    runner.scratch.mkdir(parents=True)
    (runner.batch / 'prepare.json').write_text(json.dumps({
        'ok': True, 'paper_head': head, 'harness_head': 'a' * 40}))
    monkeypatch.setattr(runner, 'check_tracked_clean', lambda: None)
    monkeypatch.setattr(runner, 'check_paper_history', lambda _: None)
    monkeypatch.setattr(runner, 'git', lambda *a: 'a' * 40)
    monkeypatch.setattr(runner, 'llamacpp_pins', lambda: {
        'model_sha256': record['pins']['model_sha256'],
        'build': {'version_line': record['pins']['llamacpp_build']}})
    runner.verify_resumed_provenance()  # does not read the legacy authorization
    runner.state['launch_provenance']['model_sha256'] = '0' * 64
    with pytest.raises(sweep.Stop):
        runner.verify_resumed_provenance()


def test_launcher_predeclared_prepare_then_start_uses_same_note_without_jobs(tmp_path):
    """Shell orchestration uses mocked tools only; no Git remote, server, or GPU is contacted."""
    root = tmp_path / 'batches'
    root.mkdir()
    fakebin = tmp_path / 'bin'
    fakebin.mkdir()
    trace = tmp_path / 'trace'
    git = fakebin / 'git'
    git.write_text('''#!/bin/bash
if [ "$1" = clone ]; then
  mkdir -p "$4/r1/scripts"
  printf '%040d\\n' 0 > "$4/r1/scripts/HARNESS_PIN_C3"
elif [ "$1" = -C ] && [ "$3" = rev-parse ]; then
  printf '%040d\\n' 0
fi
''')
    tmux = fakebin / 'tmux'
    tmux.write_text('''#!/bin/bash
if [ "$1" = has-session ]; then exit 1; fi
printf '%s\\n' "$*" >> "$TRACE"
''')
    fakepy = fakebin / 'fakepython'
    fakepy.write_text('''#!/bin/bash
printf '%s\\n' "$*" >> "$TRACE"
if [[ "$1" = */c3_prepare_check.py ]]; then printf '{"ok":true}\\n' > "$2/prepare.json"; fi
''')
    make = fakebin / 'make'
    make.write_text('#!/bin/bash\nexit 0\n')
    python3 = fakebin / 'python3'
    python3.write_text('#!/bin/bash\nexit 0\n')
    for path in (git, tmux, fakepy, make, python3):
        path.chmod(0o755)
    name = 'r1_c3_sweep_EVIDENCE_testbatch01'
    note = 'docs/r1/authorizations/new_batch.md'
    env = {**os.environ, 'PATH': str(fakebin) + os.pathsep + os.environ['PATH'],
           'TRACE': str(trace), 'R1_C3_BATCH_ROOT': str(root),
           'R1_C3_EVIDENCE_BATCH_NAME': name, 'R1_C3_EVIDENCE_NOTE': note,
           'R1_C3_VENV_PYTHON': str(fakepy), 'R1_GIT_NAME': 'fixture',
           'R1_GIT_EMAIL': 'fixture@example.invalid'}
    env.pop('R1_DRYRUN', None)
    launcher = Path(__file__).resolve().parents[2] / 'r1/scripts/c3_label_sweep_launch.sh'
    prepare = subprocess.run(['bash', str(launcher), '--prepare'], env=env, capture_output=True, text=True)
    assert prepare.returncode == 0, prepare.stderr
    batch = root / name
    assert f'export R1_C3_EVIDENCE_NOTE={note}' in (batch / 'env.sh').read_text()
    assert 'check_evidence_authorization' in trace.read_text()  # mocked admission invocation
    duplicate = subprocess.run(['bash', str(launcher), '--prepare'], env=env, capture_output=True, text=True)
    assert duplicate.returncode != 0 and 'already exists' in duplicate.stderr
    started = subprocess.run(['bash', str(launcher), '--start', str(batch)], env=env, capture_output=True, text=True)
    assert started.returncode == 0, started.stderr
    assert f'export R1_C3_EVIDENCE_NOTE={note}' in trace.read_text()  # tmux is mocked
