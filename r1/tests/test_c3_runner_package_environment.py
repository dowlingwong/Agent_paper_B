"""Isolated package provenance checks; no evidence job is executed."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from r1.scripts import c3_label_sweep as sweep


def _probe(executable='/venv/bin/python', prefix='/venv', packages=None):
    return {'executable': executable, 'prefix': prefix, 'base_prefix': '/usr',
            'packages': packages or ['numpy==2.4.4', 'scikit-learn==1.8.0']}


def test_package_list_hash_is_canonical_and_records_resolved_interpreter(monkeypatch):
    calls = []
    def check(argv, **kwargs):
        calls.append((argv, kwargs))
        return json.dumps(_probe())
    monkeypatch.setattr(sweep.subprocess, 'check_output', check)
    info = sweep.package_runtime('/batch/.venv/bin/python3')
    expected = hashlib.sha256(b'numpy==2.4.4\nscikit-learn==1.8.0\n').hexdigest()
    assert info['package_list_sha256'] == expected
    assert info['command'] == '/batch/.venv/bin/python3'
    assert info['executable'] == '/venv/bin/python' and info['prefix'] == '/venv'
    assert info['package_count'] == 2
    assert calls[0][0][1] == '-B' and calls[0][1]['env']['PYTHONDONTWRITEBYTECODE'] == '1'


@pytest.mark.parametrize('data', [None, {}, {'packages': []}, _probe(packages=['z==1', 'a==1'])])
def test_incomplete_or_unsorted_package_probe_stops(monkeypatch, data):
    monkeypatch.setattr(sweep.subprocess, 'check_output', lambda *a, **k: json.dumps(data))
    with pytest.raises(sweep.Stop, match='package list'):
        sweep.package_runtime('/test/python')


def test_probe_errors_are_stop(monkeypatch):
    def bad(*a, **k):
        raise subprocess.TimeoutExpired('python', 60)
    monkeypatch.setattr(sweep.subprocess, 'check_output', bad)
    with pytest.raises(sweep.Stop, match='package list'):
        sweep.package_runtime('/test/python')


def test_worker_and_collector_use_same_interpreter_and_packages(monkeypatch):
    monkeypatch.setattr(sweep.shutil, 'which', lambda name: '/batch/python3')
    common = {'executable': '/shared/venv/bin/python', 'prefix': '/shared/venv', 'base_prefix': '/usr',
              'package_list_sha256': 'a' * 64, 'package_count': 2}
    monkeypatch.setattr(sweep, 'package_runtime', lambda path: {'command': path, **common})
    result = sweep.package_environment('/batch/python')
    assert result['worker_python3']['executable'] == '/shared/venv/bin/python'
    monkeypatch.setattr(sweep, 'package_runtime', lambda path: {'command': path, **common,
                         'package_list_sha256': ('a' if path.endswith('python') else 'b') * 64})
    with pytest.raises(sweep.Stop, match='environments differ'):
        sweep.package_environment('/batch/python')


def test_native_manifest_must_match_launch_environment(tmp_path):
    runner = object.__new__(sweep.SweepRunner)
    runner.host, runner.dryrun, runner.label = 'deepthought', False, 'EVIDENCE'
    runner.state = {'launch_provenance': {'pin': 'p'}, 'package_environment': {'worker': {'sha': 'a'}},
                    'evidence_authorization': {'note': 'n'}}
    manifest = {'launch_provenance': {'pin': 'p'}, 'label': 'EVIDENCE',
                'evidence_authorization': {'note': 'n'}, 'package_environment': {'worker': {'sha': 'bad'}}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(sweep.Stop, match='package environment mismatch'):
        runner.check_launch_manifest(tmp_path)
    manifest['package_environment'] = runner.state['package_environment']
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    runner.check_launch_manifest(tmp_path)


def test_same_venv_python_symlinks_are_allowed(monkeypatch):
    directory = str(Path(sys.executable).parent)
    monkeypatch.setenv('PATH', directory + os.pathsep + os.environ.get('PATH', ''))
    observed = sweep.package_environment(sys.executable)
    assert observed['collector']['prefix'] == observed['worker_python3']['prefix']
    assert observed['collector']['package_list_sha256'] == observed['worker_python3']['package_list_sha256']


@pytest.mark.parametrize('command', [
    'python train.py', '/usr/bin/python3 train.py', 'uv run python3 train.py',
    'python3 -m train', 'python3 train.py; echo unsafe', 'python3 train.py > out',
    'python3 train.py --config other.yaml', 'python3 train.py\npython train.py',
])
def test_evidence_rejects_uncontrolled_node_commands(monkeypatch, command):
    monkeypatch.setattr(sweep.subprocess, 'check_output',
                        lambda *a, **k: json.dumps({'node': command}))
    with pytest.raises(sweep.Stop, match='not a verified direct python3'):
        sweep.evidence_node_commands('/venv/bin/python', Path('/pinned'), ['node'])


def test_evidence_accepts_only_exact_pinned_direct_commands(monkeypatch):
    calls = []
    def check(argv, **kwargs):
        calls.append((argv, kwargs))
        return json.dumps({'digits_mlp': 'python3 train.py',
                           'openml_wdbc': 'python3 train.py --config config.yaml'})
    monkeypatch.setattr(sweep.subprocess, 'check_output', check)
    commands = sweep.evidence_node_commands('/venv/bin/python', Path('/pinned'), ['digits_mlp', 'openml_wdbc'])
    assert len(commands) == 2
    assert calls[0][0][1] == '-B'
    assert calls[0][1]['env']['PYTHONDONTWRITEBYTECODE'] == '1'


def test_dryrun_manifest_package_environment_is_checked(tmp_path):
    runner = object.__new__(sweep.SweepRunner)
    runner.host, runner.dryrun, runner.label = 'unit-test-host', True, 'DRYRUN'
    runner.state = {'package_environment': {'worker': {'sha': 'a'}}}
    (tmp_path / 'manifest.json').write_text(json.dumps({'package_environment': {'worker': {'sha': 'b'}}}))
    with pytest.raises(sweep.Stop, match='package environment mismatch'):
        runner.check_launch_manifest(tmp_path)
