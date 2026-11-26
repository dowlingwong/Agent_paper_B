"""M3 non-numerical per-case preflight: synthetic tests, never replay.

Uses the actual pinned node sources (AR_M3_PINNED_HARNESS at 6adf385) and the
16 actual recovered case configurations from the frozen corpus. OpenML data is
SYNTHETIC: sklearn's bundled iris test fixture, reduced to two classes and
relabelled with each node's dataset id; it is not evidence about the real
caches. The MLP nodes use sklearn's bundled digits data and make_classification.
Network is denied in-process (urlopen and socket raise). These tests run the
preflight in the pytest process, *not* under the M3 boundary, and with the
local sklearn (not necessarily the pinned 1.8.0); see
test_m3_supervisor_kernel.py for boundary runs. No model is fitted.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import socket

import pytest

from r1.c3 import offline_case_preflight as pf
from r1.c3.offline_preflight import cache_snapshot


def _harness():
    path = os.environ.get('AR_M3_PINNED_HARNESS')
    if not path:
        if os.environ.get('R1_REQUIRE_M3_HARNESS') == '1':
            pytest.fail('AR_M3_PINNED_HARNESS required')
        pytest.skip('set AR_M3_PINNED_HARNESS')
    return Path(path)


@pytest.fixture(scope='module')
def cases():
    harness = _harness()
    from r1.scripts.c3_env_replay import select_cases, verify_corpus
    paper = Path(__file__).resolve().parents[2]
    return select_cases(paper, verify_corpus(paper), harness)


@pytest.fixture
def no_network(monkeypatch):
    import sklearn.datasets._openml as openml
    attempts = []

    def deny(request, *a, **k):
        attempts.append(getattr(request, 'full_url', str(request)))
        raise RuntimeError('fixture intercepted urlopen attempt')
    monkeypatch.setattr(openml, 'urlopen', deny)
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('no sockets')))
    return attempts


def binary_fixture_cache(cache, data_id):
    """Synthetic two-class OpenML cache for ``data_id`` (iris minus virginica)."""
    import sklearn.datasets.tests.data.openml.id_61 as fixture
    d = Path(fixture.__file__).parent
    arff = gzip.decompress((d / 'data-v1-dl-61.arff.gz').read_bytes()).decode()
    lines = [ln for ln in arff.splitlines(keepends=True) if 'Iris-virginica' not in ln
             or ln.lstrip().startswith('@')]
    arff_bytes = ''.join(lines).encode()
    description = json.loads(gzip.decompress((d / 'api-v1-jd-61.json.gz').read_bytes()))
    description['data_set_description']['id'] = str(data_id)
    description['data_set_description']['md5_checksum'] = hashlib.md5(arff_bytes).hexdigest()
    base = cache / 'openml' / 'openml.org'
    files = {
        base / f'api/v1/json/data/{data_id}.gz': gzip.compress(json.dumps(description).encode()),
        base / f'api/v1/json/data/features/{data_id}.gz': (d / 'api-v1-jdf-61.json.gz').read_bytes(),
        base / f'api/v1/json/data/qualities/{data_id}.gz': (d / 'api-v1-jdq-61.json.gz').read_bytes(),
        base / 'data/v1/download/61/iris.arff.gz': gzip.compress(arff_bytes),
    }
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def materialize(case, harness, root):
    node = root / case['case_id'].replace(':', '_')
    node.mkdir(parents=True)
    for name, data in pf.case_files(case, harness).items():
        (node / name).write_bytes(data)
    if pf.node_kind(case['node']) == 'openml':
        data_id = json.loads((node / 'dataset.json').read_text())['dataset_id']
        binary_fixture_cache(node / 'data_cache', data_id)
    return node


@pytest.fixture
def seeds(monkeypatch):
    def set_for(case):
        monkeypatch.setenv('AR_TRAIN_SEED', str(case['train_seed']))
        monkeypatch.setenv('AR_SPLIT_SEED', str(case['split_seed']))
    return set_for


def test_all_16_recovered_configurations_reach_the_fit_guard_without_training(cases, tmp_path, no_network, seeds):
    harness = _harness()
    assert len(cases) == 16
    seen_models = set()
    for case in cases:
        seeds(case)
        node = materialize(case, harness, tmp_path)
        record = pf.preflight_case(node, pf.node_kind(case['node']))
        assert record['fit_reached'] is True and record['model_fit_performed'] is False
        assert record['estimator_fitted'] is False and record['metric_computed'] is False
        assert record['seeds'] == {'AR_TRAIN_SEED': str(case['train_seed']),
                                   'AR_SPLIT_SEED': str(case['split_seed'])}
        for name, digest in case['configuration_file_sha256'].items():
            assert record['files_sha256'][name] == digest
        assert not (node / 'artifacts').exists()          # emit_success never ran
        if record['kind'] == 'openml':
            assert record['estimator']['class'] == 'sklearn.pipeline.Pipeline'
            assert record['cache_fingerprint'] == cache_snapshot(node / 'data_cache')['sha256']
            assert set(record['train_classes']) == {'0', '1'}
        else:
            assert record['estimator']['class'] == 'sklearn.neural_network._multilayer_perceptron.MLPClassifier'
        seen_models.add(record['estimator']['params_sha256'])
    assert no_network == []
    assert len(seen_models) > 1


def test_guard_is_restored_and_not_swallowable():
    from sklearn.pipeline import Pipeline
    from sklearn.neural_network import MLPClassifier
    original = Pipeline.fit, MLPClassifier.fit
    with pf.FitGuard():
        try:
            try:
                MLPClassifier().fit([[0.0]], [0])
            except Exception:                 # what the pinned train.py catches
                pytest.fail('ReachedFit must not be an Exception')
        except pf.ReachedFit as reached:
            assert reached.y == [0]
    assert (Pipeline.fit, MLPClassifier.fit) == original


def test_missing_cache_is_stop_and_never_downloads(cases, tmp_path, no_network, seeds):
    harness = _harness()
    case = next(c for c in cases if c['node'] == 'openml_ionosphere')
    seeds(case)
    node = materialize(case, harness, tmp_path)
    for p in sorted((node / 'data_cache').rglob('*'), reverse=True):
        if p.name == '59.gz' and 'features' in str(p):
            p.write_bytes(b'not gzip')       # corrupt one cache file
    with pytest.raises(pf.PreflightStop, match='before fit'):
        pf.preflight_case(node, 'openml')


def test_cache_change_during_preflight_is_stop(cases, tmp_path, no_network, seeds):
    harness = _harness()
    case = next(c for c in cases if c['node'] == 'openml_wdbc')
    seeds(case)
    node = materialize(case, harness, tmp_path)
    calls = []

    def snap(root):
        calls.append(root)
        return {'sha256': str(len(calls))}
    with pytest.raises(pf.PreflightStop, match='cache changed'):
        pf.preflight_case(node, 'openml', cache_snapshot=snap)


def test_path_that_never_fits_is_stop(tmp_path):
    node = tmp_path / 'fake'
    node.mkdir()
    (node / 'benchmark.py').write_text('def run_benchmark(**kw):\n    return {"val_score": 1.0}\n')
    (node / 'train.py').write_text('HIDDEN_UNITS = 1\nALPHA = 0.1\nLEARNING_RATE_INIT = 0.1\n'
                                   'BATCH_SIZE = 1\nMAX_ITER = 1\n')
    with pytest.raises(pf.PreflightStop, match='without reaching a model fit'):
        pf.preflight_case(node, 'mlp')


def test_case_files_refuse_edited_hash_mismatch(cases):
    harness = _harness()
    case = dict(cases[0])
    case['files'] = {name: text + '\n# drift\n' for name, text in case['files'].items()}
    with pytest.raises(pf.PreflightStop, match='hash mismatch'):
        pf.case_files(case, harness)


# ---------------------------------------------------------------- host side

def _closure():
    items = [{'source': '/usr/bin/python3', 'target': '/usr/bin/python3', 'sha256': 'c' * 64},
             {'source': 'x', 'target': f'{pf.PAPER_TARGET}/r1/c3/offline_case_preflight.py', 'sha256': 'b' * 64}]
    from r1.c3.offline_runtime_closure import closure_digest
    return {'items': items, 'sha256': closure_digest(items), 'python': '/usr/bin/python3'}


def _binding(cases):
    harness = _harness()
    fingerprints = {c['node']: hashlib.sha256(c['node'].encode()).hexdigest()
                    for c in cases if c['node'].startswith('openml_')}
    closure = _closure()
    return pf.build_case_binding(cases, harness, fingerprints, closure['sha256'], 'b' * 64), fingerprints


def _records(binding, cases, tmp_path):
    from r1.c3.offline_supervisor import spec_content_digest
    harness = _harness()
    closure = _closure()
    by_id = {c['case_id']: c for c in cases}
    out = {}
    for i, row in enumerate(binding['cases']):
        case = by_id[row['case_id']]
        cache = None
        if row['kind'] == 'openml':
            cache = tmp_path / f'cache{i}'
            cache.mkdir()
            (cache / 'x.gz').write_bytes(b'synthetic')
        spec = pf.build_preflight_spec(case, harness, tmp_path / f'staging{i}', closure, cache_dir=cache)
        record = {'schema': pf.SCHEMA, 'status': 'ok', 'kind': row['kind'], 'seeds': row['seeds'],
                  'files_sha256': dict(row['files_sha256']), 'cache_fingerprint': row['cache_fingerprint'],
                  'fit_reached': True, 'model_fit_performed': False, 'metric_computed': False}
        out[row['case_id']] = {'record': record, 'spec': spec,
                               'supervisor': {'status': 'COMPLETE_UNQUALIFIED', 'withdrawn_drain': 'clean',
                                              'spec_content_sha256': spec_content_digest(spec),
                                              'runtime_closure_sha256': closure['sha256']}}
    return out


def test_binding_covers_exactly_the_16_cases(cases):
    binding, _ = _binding(cases)
    assert len(binding['cases']) == 16 and binding['offline_executability'] == 'PREFLIGHT_PENDING'
    assert len(binding['binding_sha256']) == 64
    with pytest.raises(pf.PreflightStop, match='exactly 16'):
        pf.build_case_binding(cases[:15], _harness(), {}, 'a' * 64, 'b' * 64)
    with pytest.raises(pf.PreflightStop, match='no bound cache copy'):
        pf.build_case_binding(cases, _harness(), {}, 'a' * 64, 'b' * 64)


def test_results_accepted_only_when_every_case_matches(cases, tmp_path):
    import copy
    binding, _ = _binding(cases)
    base = _records(binding, cases, tmp_path)
    verdict = pf.check_preflight_results(binding, base)
    assert verdict['preflight'] == 'ALL_16_PASSED_UNQUALIFIED'
    assert verdict['binding_sha256'] == binding['binding_sha256']
    assert verdict['runtime_closure_sha256'] == binding['runtime_closure_sha256']
    first = binding['cases'][0]['case_id']
    openml = next(r['case_id'] for r in binding['cases'] if r['kind'] == 'openml')
    other_closure = [{'source': 'y', 'target': '/usr/bin/python3', 'sha256': 'd' * 64}]

    def respec(r, cid, **change):
        r[cid]['spec'] = {**r[cid]['spec'], **change}
        from r1.c3.offline_supervisor import spec_content_digest
        r[cid]['supervisor']['spec_content_sha256'] = spec_content_digest(r[cid]['spec'])
    mutations = [
        ('missing', lambda r: r.pop(first)),
        ('supervisor', lambda r: r[first]['supervisor'].update(withdrawn_drain='withdrawn')),
        ('status', lambda r: r[first]['supervisor'].update(status='STOP')),
        ('record', lambda r: r[first]['record'].update(status='STOP')),
        ('seeds', lambda r: r[first]['record'].update(seeds={'AR_TRAIN_SEED': '1', 'AR_SPLIT_SEED': '1'})),
        ('files', lambda r: r[first]['record']['files_sha256'].update({'train.py': '0' * 64})),
        ('extra executed file', lambda r: r[first]['record']['files_sha256'].update({'extra.py': '0' * 64})),
        ('cache', lambda r: r[openml]['record'].update(cache_fingerprint='0' * 64)),
        ('fit', lambda r: r[first]['record'].update(model_fit_performed=True)),
        ('no spec', lambda r: r[first].pop('spec')),
        ('supervisor ran another spec', lambda r: r[first]['supervisor'].update(spec_content_sha256='0' * 64)),
        ('supervisor closure', lambda r: r[first]['supervisor'].update(runtime_closure_sha256='0' * 64)),
        ('spec closure', lambda r: respec(r, first, closure=other_closure)),
        ('spec extra work file', lambda r: respec(r, first, work_files=r[first]['spec']['work_files'] + [
            {'source': 'z', 'target': '/work/node/extra.py', 'sha256': '0' * 64}])),
        ('spec seeds', lambda r: respec(r, first, env={**r[first]['spec']['env'], 'AR_TRAIN_SEED': '1'})),
        ('spec command', lambda r: respec(r, first, argv=r[first]['spec']['argv'][:-1] + ['openml'
                                                                                            if r[first]['spec']['argv'][-1] == 'mlp' else 'mlp'])),
    ]
    for label, mutate in mutations:
        results = copy.deepcopy(base)
        mutate(results)
        with pytest.raises(pf.PreflightStop):
            pf.check_preflight_results(binding, results)
    # a binding with another preflight source digest refuses the same runs
    other = {**binding, 'preflight_source_sha256': 'e' * 64}
    with pytest.raises(pf.PreflightStop, match='preflight source'):
        pf.check_preflight_results(other, copy.deepcopy(base))


def test_mlp_edit_beyond_the_constants_is_refused(cases):
    harness = _harness()
    case = dict(next(c for c in cases if c['node'] == 'digits_mlp'))
    pinned = (harness / 'nodes/digits_mlp/train.py').read_text()
    assert pf.mlp_edit_is_constants_only(pinned, pinned.replace('MAX_ITER = 40', 'MAX_ITER = 7'))
    assert not pf.mlp_edit_is_constants_only(pinned, pinned + '\nimport os\n')
    assert not pf.mlp_edit_is_constants_only(pinned, pinned.replace('MAX_ITER = 40', 'MAX_ITER = int("7")'))
    edited = pinned + '\nprint("extra")\n'
    case['files'] = {'train.py': edited}
    case['configuration_file_sha256'] = {'train.py': hashlib.sha256(edited.encode()).hexdigest()}
    with pytest.raises(pf.PreflightStop, match='beyond the five constants'):
        pf.case_files(case, harness)


def test_execution_binding_rechecks_exact_inputs(cases):
    harness = _harness()
    binding, fingerprints = _binding(cases)
    case = next(c for c in cases if c['node'] == 'openml_sonar')
    files = pf.case_files(case, harness)
    fp = fingerprints['openml_sonar']
    rt = binding['runtime_closure_sha256']
    assert pf.verify_execution_binding(binding, case['case_id'], files, fp, rt)
    with pytest.raises(pf.PreflightStop, match='files differ'):
        pf.verify_execution_binding(binding, case['case_id'], {**files, 'config.yaml': b'x'}, fp, rt)
    with pytest.raises(pf.PreflightStop, match='cache differs'):
        pf.verify_execution_binding(binding, case['case_id'], files, '0' * 64, rt)
    with pytest.raises(pf.PreflightStop, match='runtime differs'):
        pf.verify_execution_binding(binding, case['case_id'], files, fp, 'c' * 64)
    with pytest.raises(pf.PreflightStop, match='not preflighted'):
        pf.verify_execution_binding(binding, 'nope', files, fp, rt)
