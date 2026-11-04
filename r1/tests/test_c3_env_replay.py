"""C3 environment replay driver (M3). Fixture tests only: no batch, no venv, no LLM, no evidence."""
import difflib
import hashlib
import io
import json
import os
import stat
import sys
import tarfile
import types
from pathlib import Path

import pytest

from r1.scripts import c3_env_replay as R

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _replay_process_without_llm_modules(monkeypatch):
    """The real replay runs in its own process; other tests in this pytest session may have
    imported LLM client modules, which the driver's guard (correctly) treats as a STOP."""
    for name in [m for m in sys.modules if any(m == p or m.startswith(p + '.') for p in R.LLM_MODULES)]:
        monkeypatch.delitem(sys.modules, name)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------- the real frozen corpus (read-only)

def test_dry_run_on_the_frozen_corpus_selects_the_declared_16_cases(tmp_path):
    out = tmp_path / 'plan'
    before = R.file_sha256(REPO / R.INDEX)
    result = R.run(REPO, out, dry_run=True, harness=Path(os.environ['AR_HARNESS_ROOT'])
                   if (Path(os.environ.get('AR_HARNESS_ROOT', '/nonexistent')) / '.git').exists() else None)
    assert result['label'] == 'DRYRUN' and result['cases'] == 16
    plan = json.loads((out / 'replay_plan.json').read_text())
    assert plan['tolerance'] == 0 and plan['environment'] == 'DEFERRED_TO_HOST'
    index = json.loads((REPO / R.INDEX).read_text())
    ledgers = REPO / 'results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z/provenance/ledgers/roots'
    for node in index['nodes']:
        smallest = min(int(p.name.rsplit('__s', 1)[1]) for p in ledgers.glob(f'{node}__s*'))
        cases = [c for c in plan['cases'] if c['node'] == node]
        assert [c['budget_index'] for c in cases] == [1, 2]
        assert {c['instance_seed'] for c in cases} == {smallest}
        assert all(c['train_seed'] == c['split_seed'] == smallest and smallest not in range(7001, 7011) for c in cases)
        assert all(c['metric_key'] == R.metric_name(node) for c in cases)
        assert cases[0]['decision'] == 'kept'
    assert all('NOT CHECKABLE' in c['seed_provenance']['per_process_identity'] for c in plan['cases'])
    assert R.file_sha256(REPO / R.INDEX) == before  # nothing in the corpus is written


def test_dry_run_refuses_an_output_inside_the_corpus():
    with pytest.raises(R.Stop, match='inside the preserved'):
        R.run(REPO, REPO / next(iter(R.CORPUS_TREES)) / 'replay_out', dry_run=True)


# ---------------------------------------------------------------------------- synthetic corpus for STOP paths

def _corpus(tmp_path, *, drop_trial=None, fail_trial=None, bad_patch=False, bad_log=False, trial1_discarded=False):
    """One-node, one-campaign corpus in the frozen layout (append-only sweep only)."""
    node = 'digits_mlp'
    seed = 100 + sum(map(ord, node)) % 7  # collector rule, k = 0
    camp = f'{node}__s{seed}'
    paper = tmp_path / 'paper'
    sweep = paper / 'results/r1/evidence/S'
    ledger_dir = sweep / 'provenance/ledgers/roots' / camp
    ledger_dir.mkdir(parents=True)
    (sweep / 'roots').mkdir()
    start = {'train.py': 'HIDDEN_UNITS = 32\nLEARNING_RATE_INIT = 1e-3\n'}
    (sweep / 'roots' / f'{camp}.json').write_text(json.dumps(
        {'instance': camp, 'node': node, 'seed': seed, 'snapshots': [], 'start_files': start}))
    edits = [{'path': 'train.py', 'symbol': 'LEARNING_RATE_INIT', 'old': '1e-3', 'new': '1e-4', 'type': 'python_constant'},
             {'path': 'train.py', 'symbol': 'HIDDEN_UNITS', 'old': '32', 'new': '64', 'type': 'python_constant'}]
    files, rows, members = dict(start), [], {}
    values = [0.718663, 0.799443]
    for b, (edit, value) in enumerate(zip(edits, values), start=1):
        cand = dict(files)
        cand['train.py'] = cand['train.py'].replace(f"{edit['symbol']} = {edit['old']}", f"{edit['symbol']} = {edit['new']}")
        diff = ''.join(difflib.unified_diff(files['train.py'].splitlines(keepends=True),
                                            cand['train.py'].splitlines(keepends=True), fromfile='a/train.py',
                                            tofile='b/train.py'))
        if bad_patch and b == 2:
            diff += ' '
        log = f'val_score: {value:.6f}\ntrain_loss: 1.0\n' if not (bad_log and b == 1) else 'val_score: 0.5\n'
        orig = f'/tmp/work/roots/{camp}/art/trial-{b:03d}'
        members[orig + '/patch.diff'] = diff.encode()
        members[orig + '/run.log'] = log.encode()
        decision = 'kept' if (b == 1 and not trial1_discarded) or b == 2 else 'discarded'
        rows.append({'budget_index': b, 'campaign_id': camp, 'memory_mode': R.MEMORY_MODE,
                     'execution_status': 'failure' if fail_trial == b else 'success', 'validity_status': 'valid',
                     'decision': decision, 'current_best_before': None if b == 1 else values[0],
                     'parsed_metrics': {'val_score': value}, 'training_seed': None, 'trial_id': f'{camp}-trial-{b:03d}',
                     'patch_hash': _sha(diff.encode()) if not (bad_patch and b == 2) else _sha(diff[:-1].encode()),
                     'patch_ref': orig + '/patch.diff', 'raw_log_ref': orig + '/run.log',
                     'extra': {'manager': {'structured_edit': edit}}})
        if decision == 'kept':
            files = cand
    if drop_trial:
        rows = [r for r in rows if r['budget_index'] != drop_trial]
    (ledger_dir / 'root_trials.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (ledger_dir / 'root_events.jsonl').write_text('')
    buf = io.BytesIO()
    refs = []
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for orig, data in members.items():
            member = 'work/' + orig.split('/tmp/work/', 1)[1]
            info = tarfile.TarInfo(member)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
            refs.append({'original_ref': orig, 'member': member, 'sha256': _sha(data)})
    (sweep / 'temporary_provenance.tar.gz').write_bytes(buf.getvalue())
    (sweep / 'temporary_provenance_index.json').write_text(json.dumps({'references': refs}))
    (sweep / 'manifest.json').write_text(json.dumps({'local_work_archive': {
        'path': 'temporary_provenance.tar.gz', 'sha256': R.file_sha256(sweep / 'temporary_provenance.tar.gz'),
        'index': 'temporary_provenance_index.json',
        'index_sha256': R.file_sha256(sweep / 'temporary_provenance_index.json')}}))
    index = {'nodes': [node], 'instances': 1, 'sweeps': [{'memory_mode': R.MEMORY_MODE, 'out': 'results/r1/pilot/S',
             'ledgers': 'results/r1/pilot/S/provenance/ledgers/roots', 'commit': 'c' * 40}]}
    corpus = {'index_doc': index, 'sweeps': {R.MEMORY_MODE: {'new_dir': 'results/r1/evidence/S'}}}
    return paper, corpus


def test_synthetic_corpus_recovers_both_configurations_and_tokens(tmp_path):
    paper, corpus = _corpus(tmp_path)
    cases = R.select_cases(paper, corpus, None)
    assert [c['budget_index'] for c in cases] == [1, 2]
    assert 'LEARNING_RATE_INIT = 1e-4' in cases[1]['files']['train.py']  # trial 2 builds on the kept trial 1
    assert 'HIDDEN_UNITS = 64' in cases[1]['files']['train.py']
    assert [c['recorded_token'] for c in cases] == ['0.718663', '0.799443']
    assert cases[0]['recorded_precision'] == 6


@pytest.mark.parametrize('kwargs, message', [
    ({'drop_trial': 2}, 'missing or unsuccessful; no later trial'),
    ({'fail_trial': 1}, 'missing or unsuccessful'),
    ({'bad_patch': True}, 'differs from the recorded patch'),
    ({'bad_log': True}, 'does not carry the recorded'),
    ({'trial1_discarded': True}, 'not a recorded kept incumbent'),
])
def test_unrecoverable_cases_are_a_stop_and_never_substituted(tmp_path, kwargs, message):
    paper, corpus = _corpus(tmp_path, **kwargs)
    with pytest.raises(R.Stop, match=message):
        R.select_cases(paper, corpus, None)


def test_archive_member_tampering_is_a_stop(tmp_path):
    paper, corpus = _corpus(tmp_path)
    index = paper / 'results/r1/evidence/S/temporary_provenance_index.json'
    index.write_text(index.read_text().replace('"work/', '"work/x'))
    with pytest.raises(R.Stop, match='archive or its index differs'):
        R.select_cases(paper, corpus, None)


# ---------------------------------------------------------------------------- comparison and execution loop

def _case(**kw):
    return {'case_id': 'n__s1:t001', 'node': 'digits_mlp', 'metric_key': 'val_score', 'recorded_token': '0.718663',
            'recorded_value': 0.718663, 'files': {}, 'train_seed': 104, 'split_seed': 104, 'budget_index': 1, **kw}


@pytest.mark.parametrize('token, ok', [('0.718663', True), ('0.718664', False), ('0.7186630', False), (None, False)])
def test_zero_tolerance_compares_the_emitted_token_without_rerounding(token, ok):
    result = {'success': True, 'changed_files': [], 'data_cache_unchanged': True, 'replay_token': token,
              'recorded_token': '0.718663', 'recorded_value': 0.718663}
    assert R.case_passes(result) is ok


def test_changed_files_or_cache_writes_fail_the_case():
    base = {'success': True, 'changed_files': [], 'data_cache_unchanged': True, 'replay_token': '0.5',
            'recorded_token': '0.5', 'recorded_value': 0.5}
    assert R.case_passes(base)
    assert not R.case_passes({**base, 'changed_files': ['train.py']})
    assert not R.case_passes({**base, 'data_cache_unchanged': False})
    assert not R.case_passes({**base, 'success': False})


def _host_run(tmp_path, monkeypatch, execute, n=16):
    cases = [_case(case_id=f'c{i}:t001') for i in range(n)]
    monkeypatch.setattr(R, 'verify_corpus', lambda paper: {'index_doc': {'nodes': list('abcdefgh')}, 'sweeps': {}})
    monkeypatch.setattr(R, 'verify_collector_binding', lambda paper: {})
    monkeypatch.setattr(R, 'select_cases', lambda *a: cases)
    monkeypatch.setattr(R.platform, 'node', lambda: 'deepthought.etp.kit.edu')
    monkeypatch.setattr(R, 'check_environment', lambda b, h: {'worker_path': '/bin'})
    monkeypatch.setattr(R, 'check_harness', lambda h, n: {'data_caches_sha256': {}})
    monkeypatch.setattr(R, 'check_resources', lambda o, s, m: {})
    batch = tmp_path / 'batch'
    harness = batch / 'autoresearch_harness'
    harness.mkdir(parents=True)
    monkeypatch.setenv('AR_HARNESS_ROOT', str(harness))
    monkeypatch.setenv('PYTHONDONTWRITEBYTECODE', '1')
    out = tmp_path / 'out'
    summary = R.run(tmp_path, out, dry_run=False, harness=harness, batch=batch, scratch=tmp_path / 'scratch',
                    min_free_bytes=1, execute=execute)
    return summary, out


def _fake_execute(tokens):
    calls = []

    def execute(case, harness, scratch, env):
        calls.append((case['case_id'], dict(env)))
        token = tokens(len(calls))
        return {'case_id': case['case_id'], 'success': True, 'changed_files': [], 'failure': None,
                'replay_token': token, 'recorded_token': case['recorded_token'], 'replay_value': None,
                'recorded_value': case['recorded_value'], 'wall_seconds': 0.0, 'data_cache_unchanged': True,
                'log_text': f'val_score: {token}\n', 'work_dir': str(scratch)}
    return execute, calls


def test_all_sixteen_identical_cases_pass(tmp_path, monkeypatch):
    execute, calls = _fake_execute(lambda i: '0.718663')
    summary, out = _host_run(tmp_path, monkeypatch, execute)
    assert summary['verdict'] == 'PASS' and summary['cases_passed'] == 16 and (out / 'summary.json').exists()
    assert len((out / 'cases.jsonl').read_text().splitlines()) == 16 and len(list((out / 'raw').iterdir())) == 16
    assert all(env['OMP_NUM_THREADS'] == '1' and env['PYTHONDONTWRITEBYTECODE'] == '1' and
               env['CUDA_VISIBLE_DEVICES'] == '' for _, env in calls)


def test_first_mismatch_stops_without_retry_and_keeps_artifacts(tmp_path, monkeypatch):
    execute, calls = _fake_execute(lambda i: '0.718663' if i != 3 else '0.718664')
    summary, out = _host_run(tmp_path, monkeypatch, execute)
    assert summary['verdict'] == 'STOP' and 'zero tolerance' in summary['stop']
    assert len(calls) == 3  # stops at the first mismatch; no later case, no retry
    assert (out / 'STOP.json').exists() and not (out / 'summary.json').exists()
    assert len((out / 'cases.jsonl').read_text().splitlines()) == 3
    assert (out / 'replay_plan.json').exists() and (tmp_path / 'scratch').exists()


def test_interruption_is_a_stop_and_retains_partial_output(tmp_path, monkeypatch):
    def execute(case, harness, scratch, env):
        raise KeyboardInterrupt()
    summary, out = _host_run(tmp_path, monkeypatch, execute)
    assert summary['verdict'] == 'STOP' and 'interrupted' in summary['stop']
    assert (out / 'replay_plan.json').exists()


def test_host_run_refuses_other_hosts_and_missing_bytecode_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(R, 'verify_corpus', lambda paper: {'index_doc': {'nodes': list('abcdefgh')}, 'sweeps': {}})
    monkeypatch.setattr(R, 'verify_collector_binding', lambda paper: {})
    monkeypatch.setattr(R, 'select_cases', lambda *a: [_case(case_id=f'c{i}') for i in range(16)])
    monkeypatch.setattr(R.platform, 'node', lambda: 'mac')
    with pytest.raises(R.Stop, match='deepthought only'):
        R.run(tmp_path, tmp_path / 'o', dry_run=False)


def test_llm_client_modules_in_the_process_are_a_stop(monkeypatch):
    monkeypatch.setitem(sys.modules, 'openai', types.ModuleType('openai'))
    with pytest.raises(R.Stop, match='LLM client modules'):
        R.no_llm_modules()


# ---------------------------------------------------------------------------- real worker on a fixture node

def test_execute_case_runs_the_pinned_local_worker_at_the_recorded_seed(tmp_path, monkeypatch):
    pytest.importorskip('yaml')
    harness_src = Path(os.environ.get('AR_HARNESS_ROOT', '')) / 'src'
    if not harness_src.is_dir():
        pytest.skip('harness checkout not available')
    root = tmp_path / 'fixture_harness'
    (root / 'configs/nodes').mkdir(parents=True)
    node = root / 'nodes/digits_mlp'
    node.mkdir(parents=True)
    spec = json.loads((Path(os.environ['AR_HARNESS_ROOT']) / 'configs/nodes/digits_mlp.yaml').read_text())
    (root / 'configs/nodes/digits_mlp.yaml').write_text(json.dumps(spec))
    (node / 'train.py').write_text('X = 1\n')
    (node / 'benchmark.py').write_text('')
    script = ("import os\nX = 2\nprint('seeds', os.environ['AR_TRAIN_SEED'], os.environ['AR_SPLIT_SEED'], "
              "os.environ['OMP_NUM_THREADS'])\nprint('val_score: 0.71866' + str(int(os.environ['AR_TRAIN_SEED']) % 10))\n")
    scratch = tmp_path / 'scratch'
    scratch.mkdir()
    case = _case(files={'train.py': script}, train_seed=103, split_seed=103, recorded_token='0.718663')
    result = R.execute_case(case, root, scratch, {'OMP_NUM_THREADS': '1'})
    assert 'seeds 103 103 1' in result['log_text']
    assert result['replay_token'] == '0.718663' and result['success'] and result['changed_files'] == []
    assert R.case_passes(result)
    assert (node / 'train.py').read_text() == 'X = 1\n'  # the source node is never edited


def test_openml_node_without_local_cache_is_a_stop_before_running(tmp_path):
    root = tmp_path / 'h'
    (root / 'configs/nodes').mkdir(parents=True)
    (root / 'nodes/openml_sonar/data_cache').mkdir(parents=True)
    (root / 'nodes/openml_sonar/data_cache/.gitkeep').write_text('')
    real = Path(os.environ.get('AR_HARNESS_ROOT', '')) / 'configs/nodes/openml_sonar.yaml'
    if not real.is_file():
        pytest.skip('harness checkout not available')
    (root / 'configs/nodes/openml_sonar.yaml').write_text(real.read_text())
    case = _case(node='openml_sonar', metric_key='val_auc', files={'config.yaml': 'C: 1\n'})
    (tmp_path / 's').mkdir()
    with pytest.raises(R.Stop, match='would download'):
        R.execute_case(case, root, tmp_path / 's', {})


# ---------------------------------------------------------------------------- host environment checks

@pytest.fixture
def host_env(tmp_path, monkeypatch):
    batch = tmp_path / 'batch'
    bindir = batch / 'autoresearch_harness/.venv/bin'
    bindir.mkdir(parents=True)
    shared = '/shared/venv/bin/python'
    for name in ('python', 'python3'):
        p = bindir / name
        p.write_text(f'#!/bin/sh\nexec {shared} "$@"\n')
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    lock = batch / 'autoresearch_harness/uv.lock'
    lock.write_text('lock')
    freeze = tmp_path / 'freeze.txt'
    freeze.write_text('numpy==2.4.4\nscikit-learn==1.8.0\n')
    monkeypatch.setattr(R, 'SHARED_PYTHON', shared)
    monkeypatch.setattr(R, 'UV_LOCK_SHA256', R.file_sha256(lock))
    monkeypatch.setattr(R, 'FREEZE', str(freeze))
    monkeypatch.setattr(R, 'FREEZE_SHA256', R.file_sha256(freeze))
    state = {'packages': {'numpy': '2.4.4', 'scikit-learn': '1.8.0', 'narwhals': '2.27.1'},
             'version': list(R.PYTHON_VERSION), 'versions': dict(R.VERSIONS), 'prefix': sys.prefix,
             'base_prefix': '/usr', 'mtime': 1761600000.0}  # 2025-10-27, before launch

    def probe(python):
        return {'executable': python, 'realpath': shared, 'prefix': state['prefix'], 'base_prefix': state['base_prefix'],
                'version': state['version'], 'build': 'b', 'versions': state['versions'],
                'packages': dict(state['packages']), 'newest_dist_info_mtime': state['mtime']}
    monkeypatch.setattr(R, 'probe', probe)
    monkeypatch.setenv('PATH', '/usr/bin')
    return batch, state


def test_environment_accepts_only_the_documented_narwhals_addition(host_env):
    batch, state = host_env
    record = R.check_environment(batch, batch / 'autoresearch_harness')
    assert record['difference_from_freeze']['added'] == {'narwhals': '2.27.1'}
    assert record['current_package_list_sha256'] == R.sha256(record['current_package_list'].encode())


@pytest.mark.parametrize('change, message', [
    (lambda s: s['packages'].update(extra='1'), 'beyond narwhals'),
    (lambda s: s['packages'].update(numpy='2.4.5'), 'beyond narwhals'),
    (lambda s: s['versions'].update(numpy='2.4.5'), 'library versions differ'),
    (lambda s: s.update(version=[3, 13, 14]), 'library versions differ'),
    (lambda s: s.update(base_prefix=s['prefix']), 'not a virtual environment'),
    (lambda s: s.update(mtime=1793116800.0), 'at or after launch'),
])
def test_environment_differences_are_a_stop(host_env, change, message):
    batch, state = host_env
    change(state)
    with pytest.raises(R.Stop, match=message):
        R.check_environment(batch, batch / 'autoresearch_harness')


def test_wrapper_to_another_interpreter_is_a_stop(host_env):
    batch, _ = host_env
    (batch / 'autoresearch_harness/.venv/bin/python3').write_text('#!/bin/sh\nexec /other/python "$@"\n')
    with pytest.raises(R.Stop, match='do not exec the recorded shared venv'):
        R.check_environment(batch, batch / 'autoresearch_harness')


def test_cli_dry_run(tmp_path, capsys):
    code = R.main(['--paper-root', str(REPO), '--out', str(tmp_path / 'cli'), '--dry-run'])
    assert code == 0 and json.loads(capsys.readouterr().out)['cases'] == 16


def test_resources_require_new_local_tmp_scratch_and_headroom(tmp_path):
    with pytest.raises(R.Stop, match='directly under /tmp'):
        R.check_resources(tmp_path / 'out', tmp_path / 'r1_c3_env_replay_x', 1)
    scratch = Path('/tmp') / f'r1_c3_env_replay_test_{os.getpid()}'
    with pytest.raises(R.Stop, match='headroom'):
        R.check_resources(tmp_path / 'out', scratch, 10**18)
    (tmp_path / 'out').mkdir()
    with pytest.raises(R.Stop, match='must be new'):
        R.check_resources(tmp_path / 'out', scratch, 1)
    assert not scratch.exists()
