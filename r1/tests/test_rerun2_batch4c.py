"""Batch-4c regressions and guarded real-runner integration fixture."""
import ast
import builtins
import dis
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import types
from unittest import mock

import pytest

from r1.scripts.dryrun_guard import validate_dryrun
from r1.tests.test_ada_e1b_rerun2 import _load_runner, _prepare_env, _run_prepare, _run_launcher, _prepare_batch, _launcher_env

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def desktop_host(monkeypatch):
    """Pure guard fixtures emulate a desktop; never launch DRYRUN on Ada."""
    monkeypatch.setattr(platform, 'node', lambda: 'desktop-test')


def undefined_globals(runner_source, helper_source):
    # Match the exec loader: helper module executes in the runner's globals;
    # ignore only the dropped __main__ guards and the loader's own exec call.
    tree = ast.parse(runner_source)
    helper = ast.parse(helper_source)
    helper.body.pop()
    tree.body = [n for n in tree.body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'exec')]
    tree.body += helper.body
    code = compile(ast.fix_missing_locations(tree), '<merged rerun-2>', 'exec')
    defined = set(dir(builtins)) | {'__file__', '__name__', '__package__'}
    defined |= {i.argval for i in dis.get_instructions(code) if i.opname in ('STORE_NAME', 'STORE_GLOBAL')}
    used = set()
    def visit(c):
        local_names = {i.argval for i in dis.get_instructions(c) if i.opname == 'STORE_NAME'}
        used.update(i.argval for i in dis.get_instructions(c)
                    if i.opname == 'LOAD_GLOBAL' or (i.opname == 'LOAD_NAME' and i.argval not in local_names))
        for item in c.co_consts:
            if isinstance(item, types.CodeType):
                visit(item)
    visit(code)
    return used - defined


def test_exec_loaded_globals_are_defined_and_guard_catches_original():
    helper = (REPO / 'r1/scripts/deepthought_batch1_resume.py').read_text()
    runner = (REPO / 'r1/scripts/ada_e1b_rerun2.py').read_text()
    assert not undefined_globals(runner, helper)
    original_runner = subprocess.check_output(['git', 'show', '69b2bbd:r1/scripts/ada_e1b_rerun2.py'], cwd=REPO, text=True)
    original_helper = subprocess.check_output(['git', 'show', '69b2bbd:r1/scripts/deepthought_batch1_resume.py'], cwd=REPO, text=True)
    assert 'MODELS' in undefined_globals(original_runner, original_helper)
    assert 'OTHER_MISSING_GLOBAL' in undefined_globals(runner + '\ndef injected(): return OTHER_MISSING_GLOBAL\n', helper)
    assert 'OTHER_MISSING_GLOBAL' in undefined_globals(runner + '\nPROBE = OTHER_MISSING_GLOBAL\n', helper)
    assert 'OTHER_MISSING_GLOBAL' in undefined_globals(runner + '\nclass Injected:\n    probe = OTHER_MISSING_GLOBAL\n', helper)


def test_models_directory_is_required_before_start(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    plan = Path(runner.PAPER) / 'docs/r1/PLAN.md'
    plan.parent.mkdir(parents=True)
    plan.write_text('\n'.join(runner.ROWS))
    monkeypatch.delenv('R1_OLLAMA_MODELS')
    with pytest.raises(RuntimeError, match='STOP: R1_OLLAMA_MODELS is required'):
        runner.preconditions()
    monkeypatch.setenv('R1_OLLAMA_MODELS', str(tmp_path / 'absent'))
    with pytest.raises(RuntimeError, match='directory is missing'):
        runner.preconditions()


def test_preconditions_constructs_model_command_from_environment(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    plan = Path(runner.PAPER) / 'docs/r1/PLAN.md'
    plan.parent.mkdir(parents=True)
    plan.write_text('\n'.join(runner.ROWS))
    models = tmp_path / 'models'
    models.mkdir()
    monkeypatch.setattr(runner, 'git_output', lambda *a: 'pin')
    monkeypatch.setattr(runner, 'select_card', lambda: '0, GPU-fixture, fixture, 40000')
    monkeypatch.setattr(runner, 'check_gpu', lambda: None)
    monkeypatch.setattr(runner.socket, 'socket', mock.MagicMock())
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **kw: types.SimpleNamespace(returncode=1))
    seen = []
    def capture(args, **kw):
        seen.append(args)
        raise RuntimeError('captured before any inference')
    monkeypatch.setattr(runner, 'cmd', capture)
    with pytest.raises(RuntimeError, match='captured before any inference'):
        runner.preconditions()
    assert f'OLLAMA_MODELS={models}' in seen[0][-1]


def test_launcher_requires_git_identity_and_records_dev_setup(tmp_path):
    env = _prepare_env(tmp_path, harness_rc=0, harness_output='397 passed in 1s')
    (tmp_path / 'batches').mkdir(exist_ok=True)
    no_identity = {k:v for k,v in env.items() if k not in ('R1_GIT_NAME', 'R1_GIT_EMAIL')}
    result = _run_launcher(['--prepare'], no_identity)
    assert result.returncode and 'R1_GIT_NAME and R1_GIT_EMAIL are required' in result.stdout
    uv = tmp_path / 'stubbin/uv'
    uv.write_text(uv.read_text().replace('if [ "$1" = "sync" ]; then', 'echo "$@" >> "$STUB_UV_LOG"\nif [ "$1" = "sync" ]; then'))
    env['STUB_UV_LOG'] = str(tmp_path / 'uv_calls.log')
    batch = _run_prepare(tmp_path, env)
    setup = json.loads((batch / 'prepare.json').read_text())
    assert setup['git_identity']['name'] == env['R1_GIT_NAME']
    assert setup['push_dry_run'] == {'paper': True, 'harness': True}
    assert setup['pytest_version'] == 'pytest-stub-9'
    assert 'sync --extra dev' in (tmp_path / 'uv_calls.log').read_text()
    started = _run_launcher(['--start', str(batch)], env)
    assert started.returncode == 0, started.stdout + started.stderr
    assert 'SELF-CHECK:' in started.stdout and 'pytest=' in started.stdout and 'models=' in started.stdout


def test_launcher_installs_declared_dev_extra(tmp_path):
    env = _prepare_env(tmp_path, harness_rc=0, harness_output='397 passed in 1s')
    uv = tmp_path / 'stubbin/uv'
    uv.write_text(uv.read_text().replace('if [ "$1" = "sync" ]; then', 'echo "$@" >> "$STUB_UV_LOG"\nif [ "$1" = "sync" ]; then'))
    env['STUB_UV_LOG'] = str(tmp_path / 'uv_calls.log')
    _run_prepare(tmp_path, env)
    assert 'sync --extra dev' in (tmp_path / 'uv_calls.log').read_text()


def test_dryrun_refuses_ada_and_unmarked_paths(monkeypatch, desktop_host):
    monkeypatch.setenv('R1_DRYRUN', '1')
    with mock.patch('platform.node', return_value='ucrtasl'):
        with pytest.raises(RuntimeError, match='forbidden on Ada'):
            validate_dryrun()
    monkeypatch.setenv('R1_DRYRUN_ROOT', '/')
    with pytest.raises(RuntimeError, match='marked temporary directory'):
        validate_dryrun()


def test_dryrun_refuses_escaped_batch_root(tmp_path, monkeypatch, desktop_host):
    (tmp_path / '.dryrun').write_text('DRYRUN\n')
    monkeypatch.setenv('R1_DRYRUN', '1')
    monkeypatch.setenv('R1_DRYRUN_ROOT', str(tmp_path))
    monkeypatch.delenv('AR_HARNESS_ROOT', raising=False)
    monkeypatch.setenv('R1_RERUN2_BATCH_ROOT', '/Users')
    with pytest.raises(RuntimeError, match='escapes the temporary directory'):
        validate_dryrun()


def test_production_design_constants_remain_fixed(tmp_path, monkeypatch):
    runner = _load_runner(tmp_path, monkeypatch)
    assert runner.NODES == ['digits_mlp', 'tabular_mlp', 'openml_ionosphere', 'openml_breast_w']
    assert (runner.INSTANCES, runner.RUNS, runner.POINTS, runner.REPS, runner.AUDIT_SEEDS) == (18, 20, [4, 8, 12], 2, 6)
    assert runner.OLLAMA_PORT == 11434


def test_launcher_refuses_invalid_committer_before_push(tmp_path):
    env = _prepare_env(tmp_path, harness_rc=0, harness_output='397 passed in 1s')
    (tmp_path / 'batches').mkdir()
    git = tmp_path / 'stubbin/git'
    git.write_text(git.read_text().replace('case "$*" in', 'if [ "$1" = "var" ]; then exit 1; fi\ncase "$*" in'))
    result = _run_launcher(['--prepare'], env)
    assert result.returncode and 'STOP: invalid Git committer identity' in result.stdout


def test_dryrun_start_refuses_external_batch_before_log_write(tmp_path):
    root = tmp_path / 'marked_root'
    root.mkdir()
    (root / '.dryrun').write_text('DRYRUN\n')
    batch = _prepare_batch(tmp_path)
    env = _launcher_env(tmp_path, hostname='desktop')
    env.pop('AR_HARNESS_ROOT', None)
    env.update(R1_DRYRUN='1', R1_DRYRUN_ROOT=str(root))
    result = _run_launcher(['--start', str(batch)], env)
    error = result.stdout + result.stderr
    assert result.returncode and ('escapes the temporary directory' in error or 'DRYRUN is forbidden on Ada' in error)
    assert not (batch / 'paper_identity_start.log').exists()
    assert not (batch / 'runner.log').exists()


def test_dryrun_refuses_all_effective_push_urls_without_network(tmp_path, monkeypatch, desktop_host):
    for key in tuple(os.environ):
        if key.startswith(('R1_RERUN2_', 'R1_C3_')) or key in ('R1_BATCH_DIRECTORY', 'R1_PAPER_ROOT', 'AR_HARNESS_ROOT'):
            monkeypatch.delenv(key, raising=False)
    (tmp_path / '.dryrun').write_text('DRYRUN\n')
    monkeypatch.setenv('R1_DRYRUN', '1')
    monkeypatch.setenv('R1_DRYRUN_ROOT', str(tmp_path))
    monkeypatch.delenv('AR_HARNESS_ROOT', raising=False)
    repo, bare = tmp_path / 'paper', tmp_path / 'paper.git'
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    subprocess.run(['git', 'init', '--bare', '-q', str(bare)], check=True)
    subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'dryrun', str(bare)], check=True)
    monkeypatch.setenv('R1_PAPER_ROOT', str(repo))
    assert validate_dryrun()
    subprocess.run(['git', '-C', str(repo), 'config', '--add', 'remote.dryrun.pushurl', str(bare)], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', '--add', 'remote.dryrun.pushurl', 'https://example.invalid/forbidden.git'], check=True)
    with pytest.raises(RuntimeError, match='only to a local temporary bare remote'):
        validate_dryrun()


@pytest.mark.parametrize('escape', ['out', 'work'])
def test_dryrun_liveness_paths_refuse_before_any_write_or_worker(tmp_path, monkeypatch, escape):
    from r1.liveness.__main__ import run_campaigns
    from r1.headroom import e1b_collect
    root = tmp_path / 'marked_root'
    root.mkdir()
    monkeypatch.setenv('R1_DRYRUN_ROOT', str(root))
    monkeypatch.setattr('r1.scripts.dryrun_guard.validate_dryrun', lambda: True)
    worker = mock.Mock(side_effect=AssertionError('worker must not run'))
    monkeypatch.setattr(e1b_collect, 'run_root', worker)
    outside = tmp_path / 'external'
    args = types.SimpleNamespace(out=str(outside if escape == 'out' else root / 'out'),
                                work=str(outside if escape == 'work' else root / 'work'), runs=4)
    with pytest.raises(RuntimeError, match='liveness output/work escapes'):
        run_campaigns(args)
    worker.assert_not_called()
    assert not outside.exists() and not (root / 'out').exists() and not (root / 'work').exists()


@pytest.mark.skipif(os.environ.get('R1_DRYRUN_CHILD') == '1' or platform.node().split('.')[0] == 'ucrtasl',
                    reason='desktop integration forbidden on Ada; suppress recursion in fresh-clone suite')
def test_real_runner_desktop_dryrun(tmp_path):
    env = {k:v for k,v in os.environ.items() if k != 'R1_DRYRUN'}
    completed = subprocess.run([sys.executable, str(REPO / 'r1/scripts/rerun2_dryrun.py'), '--out', str(tmp_path / 'dryrun_result')], cwd=REPO, env=env, capture_output=True, text=True, timeout=900)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((tmp_path / 'dryrun_result/summary.json').read_text())
    assert summary['label'] == 'DRYRUN' and summary['completed'] and summary['restart_refused']
