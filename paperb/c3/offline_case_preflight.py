"""M3 non-numerical per-case preflight (candidate; not wired to replay).

Two halves:

* **Workload side** (:func:`preflight_case`, also the script entry): runs
  *inside* the M3 boundary, on a private copy of one case's node directory.
  It calls the node's actual pinned entry function (``run_openml_benchmark``
  or ``run_benchmark``) with every model ``fit`` replaced by a guard that
  raises :class:`ReachedFit` (a ``BaseException``, so the pinned code's
  ``except Exception`` cannot swallow it). The real path therefore executes
  verbatim (seed variables, config parsing and validation, data loading from
  the private cache copy or bundled/synthetic data, label encoding, the split,
  preprocessing and the configuration-dependent estimator construction) and
  stops at the first model fit. No model is trained and no metric is
  computed. ``StandardScaler.fit`` in the MLP nodes (feature means) is
  preprocessing and does run. The cache tree is fingerprinted before and after.

* **Host side** (:func:`build_case_binding`, :func:`check_preflight_results`,
  :func:`verify_execution_binding`): binds every case's exact files, cache-copy
  fingerprint and runtime closure digest into one manifest; accepts the
  16 preflight records only if each matches its binding and its supervisor run
  was ``COMPLETE_UNQUALIFIED`` with a clean withdrawn-notification drain; and
  re-verifies the same identities immediately before a later real execution.

Not established here: target-host qualification, that the fit itself reads no
external input (a frozen-code review item), or authorization of any replay.
The production OpenML replay STOP in ``c3_env_replay.py`` is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

SCHEMA = 'm3_case_preflight/v1'
BINDING_SCHEMA = 'm3_case_preflight_binding/v1'
MLP_CONSTANTS = ('HIDDEN_UNITS', 'ALPHA', 'LEARNING_RATE_INIT', 'BATCH_SIZE', 'MAX_ITER')


class PreflightStop(RuntimeError):
    pass


class ReachedFit(BaseException):
    """Raised by the fit guard; carries what the real run would train on."""

    def __init__(self, estimator, x, y):
        super().__init__('fit reached')
        self.estimator, self.x, self.y = estimator, x, y


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str).encode()


# ------------------------------------------------------------- workload side

def _fit_guard_targets():
    from sklearn.pipeline import Pipeline
    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    return [(Pipeline, 'fit'), (Pipeline, 'fit_predict'), (Pipeline, 'fit_transform'),
            (MLPClassifier, 'fit'), (MLPClassifier, 'partial_fit'),
            (LogisticRegression, 'fit'), (RandomForestClassifier, 'fit'),
            (GradientBoostingClassifier, 'fit')]


class FitGuard:
    """Context manager: every model fit raises ReachedFit; restored on exit."""

    def __enter__(self):
        self.saved = []
        for cls, name in _fit_guard_targets():
            self.saved.append((cls, name, cls.__dict__.get(name)))

            def guard(est, x=None, y=None, *a, **k):
                raise ReachedFit(est, x, y)
            setattr(cls, name, guard)
        return self

    def __exit__(self, *exc):
        for cls, name, original in reversed(self.saved):
            if original is None:
                delattr(cls, name)
            else:
                setattr(cls, name, original)
        return False


def _load_benchmark(node_dir):
    node_dir = Path(node_dir)
    sys.modules.pop('benchmark', None)
    sys.path.insert(0, str(node_dir))
    spec = importlib.util.spec_from_file_location('benchmark', node_dir / 'benchmark.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules['benchmark'] = module
    spec.loader.exec_module(module)
    return module


def mlp_constants(train_py):
    """Module-level literal constants of the pinned MLP train.py (no exec)."""
    import ast
    tree = ast.parse(Path(train_py).read_text(encoding='utf-8'))
    found = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id in MLP_CONSTANTS):
            found[node.targets[0].id] = ast.literal_eval(node.value)
    if set(found) != set(MLP_CONSTANTS):
        raise PreflightStop('STOP: MLP train.py constants incomplete')
    return found


def _data_digest(x, y):
    import numpy as np
    try:
        import pandas as pd
    except ImportError:          # pragma: no cover - pandas is in the pinned closure
        pd = None
    parts = []
    for item in (x, y):
        if pd is not None and isinstance(item, (pd.DataFrame, pd.Series)):
            parts.append(pd.util.hash_pandas_object(item, index=True).to_numpy().tobytes())
            types = item.dtypes if isinstance(item, pd.DataFrame) else [item.dtype]
            parts.append(_canonical([str(t) for t in types]))
        else:
            arr = np.ascontiguousarray(np.asarray(item))
            parts.append(str(arr.dtype).encode() + str(arr.shape).encode() + arr.tobytes())
    return _sha(b'\0'.join(parts))


def _estimator_identity(estimator):
    params = estimator.get_params(deep=True)
    flat = {k: (repr(v) if hasattr(v, 'get_params') else v) for k, v in params.items()}
    return {'class': type(estimator).__module__ + '.' + type(estimator).__name__,
            'params_sha256': _sha(_canonical(flat))}


def preflight_case(node_dir, kind, *, config_name='config.yaml', cache_snapshot=None):
    """Run one case's pinned path up to the first model fit. Workload side.

    ``kind`` is ``'openml'`` or ``'mlp'``. The caller has already set
    ``AR_TRAIN_SEED``/``AR_SPLIT_SEED`` as the real worker would. Returns the
    preflight record; any error raises :class:`PreflightStop`.
    """
    from r1.c3.offline_preflight import cache_snapshot as default_snapshot
    snap = cache_snapshot or default_snapshot
    node_dir = Path(node_dir)
    if kind not in ('openml', 'mlp'):
        raise PreflightStop('STOP: unknown preflight kind')
    files = {}
    for name in sorted(os.listdir(node_dir)):
        p = node_dir / name
        if p.is_file() and not p.is_symlink():
            files[name] = _sha(p.read_bytes())
    cache_dir = node_dir / 'data_cache'
    try:
        before = snap(cache_dir) if kind == 'openml' else None
    except Exception as exc:
        raise PreflightStop(f'STOP: cache copy unusable before preflight: {exc}') from exc
    try:
        bench = _load_benchmark(node_dir)
        with FitGuard():
            try:
                if kind == 'openml':
                    bench.run_openml_benchmark(node_dir / config_name)
                else:
                    c = mlp_constants(node_dir / 'train.py')
                    bench.run_benchmark(hidden_units=c['HIDDEN_UNITS'], alpha=c['ALPHA'],
                                        learning_rate_init=c['LEARNING_RATE_INIT'],
                                        batch_size=c['BATCH_SIZE'], max_iter=c['MAX_ITER'])
            except ReachedFit as reached:
                fit = reached
            else:
                raise PreflightStop('STOP: pinned path returned without reaching a model fit')
    except PreflightStop:
        raise
    except Exception as exc:
        raise PreflightStop(f'STOP: preflight failed before fit: {type(exc).__name__}: {exc}') from exc
    try:
        after = snap(cache_dir) if kind == 'openml' else None
    except Exception as exc:
        raise PreflightStop(f'STOP: cache copy unreadable after preflight: {exc}') from exc
    if before != after:
        raise PreflightStop('STOP: cache changed during preflight')
    import numpy as np
    from sklearn.exceptions import NotFittedError
    from sklearn.utils.validation import check_is_fitted
    try:
        check_is_fitted(fit.estimator)
    except NotFittedError:
        pass
    else:
        raise PreflightStop('STOP: estimator is fitted after preflight')
    y = np.asarray(fit.y)
    classes, counts = np.unique(y, return_counts=True)
    return {
        'schema': SCHEMA, 'kind': kind, 'files_sha256': files,
        'seeds': {'AR_TRAIN_SEED': os.environ.get('AR_TRAIN_SEED'),
                  'AR_SPLIT_SEED': os.environ.get('AR_SPLIT_SEED')},
        'cache_fingerprint': before['sha256'] if before else None,
        'fit_reached': True, 'model_fit_performed': False, 'metric_computed': False,
        'estimator_fitted': False,
        'estimator': _estimator_identity(fit.estimator),
        'train_shape': list(np.shape(fit.x)),
        'train_classes': {str(k): int(v) for k, v in zip(classes.tolist(), counts.tolist())},
        'train_data_sha256': _data_digest(fit.x, fit.y),
    }


def main(argv=None):
    """Workload entry inside the boundary: prints one JSON line, exit 0/3."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--node-dir', required=True)
    parser.add_argument('--kind', required=True, choices=('openml', 'mlp'))
    args = parser.parse_args(argv)
    try:
        record = preflight_case(args.node_dir, args.kind)
    except PreflightStop as exc:
        print(json.dumps({'schema': SCHEMA, 'status': 'STOP', 'reason': str(exc)}, sort_keys=True))
        return 3
    print('M3_PREFLIGHT ' + json.dumps({**record, 'status': 'ok'}, sort_keys=True))
    return 0


# ----------------------------------------------------------------- host side

def node_kind(node):
    if node.startswith('openml_'):
        return 'openml'
    if node in ('digits_mlp', 'tabular_mlp'):
        return 'mlp'
    raise PreflightStop(f'STOP: no preflight rule for node {node}')


def case_files(case, harness):
    """Exact bytes of one case's node directory: pinned files + recorded edits."""
    harness = Path(harness)
    node_dir = harness / 'nodes' / case['node']
    files = {}
    # Same top-level file set the real path's copytree carries (data_cache is
    # bound separately by its fingerprint; subdirectories other than it STOP).
    for p in sorted(node_dir.iterdir()):
        if p.is_symlink():
            raise PreflightStop(f'STOP: symlink in pinned node directory: {p.name}')
        if p.is_dir():
            if p.name in ('data_cache', '__pycache__', '.autoresearch_artifacts'):
                continue
            raise PreflightStop(f'STOP: unexpected directory in pinned node: {p.name}')
        files[p.name] = p.read_bytes()
    edits = case.get('files')
    if not isinstance(edits, dict) or not edits:
        raise PreflightStop(f"STOP: case {case.get('case_id')} has no recovered editable files")
    for name, data in edits.items():
        if isinstance(data, str):
            data = data.encode('utf-8')     # the real path uses write_text(utf-8)
        if name not in files or not isinstance(data, (bytes, bytearray)):
            raise PreflightStop(f"STOP: case {case.get('case_id')} edits an unknown file {name}")
        expected = case['configuration_file_sha256'].get(name)
        if _sha(bytes(data)) != expected:
            raise PreflightStop(f"STOP: case {case.get('case_id')} edited file hash mismatch: {name}")
        files[name] = bytes(data)
    if node_kind(case['node']) == 'mlp':
        pinned = (node_dir / 'train.py').read_bytes()
        if not mlp_edit_is_constants_only(pinned, files['train.py']):
            raise PreflightStop(f"STOP: case {case.get('case_id')} edits train.py beyond the five constants")
    return files


def mlp_edit_is_constants_only(pinned, edited):
    """The edited MLP train.py equals the pinned one except the five constants' literal values.

    The preflight calls ``run_benchmark`` with those constants instead of
    executing ``train.py``; this check makes that equivalent to the real path.
    """
    import ast

    def normalised(src):
        tree = ast.parse(src)
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id in MLP_CONSTANTS):
                ast.literal_eval(node.value)          # must stay a literal
                node.value = ast.Constant(None)
        return ast.dump(tree, include_attributes=False)
    try:
        return normalised(pinned) == normalised(edited)
    except (SyntaxError, ValueError):
        return False


def build_case_binding(cases, harness, cache_fingerprints, runtime_closure_sha256, preflight_source_sha256):
    """One manifest binding all 16 cases to exact inputs; no I/O besides reads."""
    if len(cases) != 16 or len({c['case_id'] for c in cases}) != 16:
        raise PreflightStop('STOP: exactly 16 distinct cases required')
    if not isinstance(runtime_closure_sha256, str) or len(runtime_closure_sha256) != 64:
        raise PreflightStop('STOP: runtime closure digest required')
    rows = []
    for case in sorted(cases, key=lambda c: c['case_id']):
        kind = node_kind(case['node'])
        files = case_files(case, harness)
        fingerprint = None
        if kind == 'openml':
            fingerprint = cache_fingerprints.get(case['node'])
            if not isinstance(fingerprint, str) or len(fingerprint) != 64:
                raise PreflightStop(f"STOP: no bound cache copy for {case['node']}")
        if case['train_seed'] != case['split_seed']:
            raise PreflightStop(f"STOP: unequal seeds for {case['case_id']}")
        rows.append({'case_id': case['case_id'], 'node': case['node'], 'kind': kind,
                     'files_sha256': {n: _sha(b) for n, b in sorted(files.items())},
                     'seeds': {'AR_TRAIN_SEED': str(case['train_seed']),
                               'AR_SPLIT_SEED': str(case['split_seed'])},
                     'cache_fingerprint': fingerprint})
    payload = {'schema': BINDING_SCHEMA, 'cases': rows,
               'runtime_closure_sha256': runtime_closure_sha256,
               'preflight_source_sha256': preflight_source_sha256,
               'offline_executability': 'PREFLIGHT_PENDING'}
    return {**payload, 'binding_sha256': _sha(_canonical(payload))}


def _spec_node_files(spec):
    prefix = '/work/node/'
    return {i['target'][len(prefix):]: i['sha256'] for i in spec['work_files']
            if i['target'].startswith(prefix) and not i['target'].startswith(prefix + 'data_cache/')}


def check_preflight_results(binding, results):
    """Accept only if all 16 bound cases preflighted cleanly under the bound runtime.

    ``results`` maps case_id -> {'supervisor': <supervise() return>,
    'record': <workload JSON>, 'spec': <the build_preflight_spec() dict run>}.
    For every case: the supervisor run is clean and ran exactly ``spec``
    (``spec_content_sha256``) with the bound runtime closure; ``spec`` carries
    exactly the bound node files, the bound seeds, the preflight argv and the
    bound preflight source; the record reports exactly the bound files (no
    extra file), the bound cache fingerprint and a stop at the fit. Any
    missing, extra, failed or mismatching case STOPs the whole set.
    """
    from r1.c3.offline_runtime_closure import closure_digest
    from r1.c3.offline_supervisor import spec_content_digest
    expected = {row['case_id']: row for row in binding['cases']}
    if set(results) != set(expected):
        raise PreflightStop('STOP: preflight results do not cover exactly the bound cases')
    closure_sha = binding['runtime_closure_sha256']
    source_target = f'{PAPER_TARGET}/r1/c3/offline_case_preflight.py'
    for case_id, row in sorted(expected.items()):
        sup = results[case_id].get('supervisor') or {}
        rec = results[case_id].get('record') or {}
        spec = results[case_id].get('spec')
        if sup.get('status') != 'COMPLETE_UNQUALIFIED' or sup.get('withdrawn_drain') != 'clean':
            raise PreflightStop(f'STOP: {case_id} supervisor run not clean')
        if not isinstance(spec, dict):
            raise PreflightStop(f'STOP: {case_id} executed specification missing')
        try:
            ran = spec_content_digest(spec)
            spec_closure = closure_digest(spec['closure'])
        except (KeyError, TypeError) as exc:
            raise PreflightStop(f'STOP: {case_id} malformed specification') from exc
        if sup.get('spec_content_sha256') != ran:
            raise PreflightStop(f'STOP: {case_id} supervisor ran a different specification')
        if sup.get('runtime_closure_sha256') != closure_sha or spec_closure != closure_sha:
            raise PreflightStop(f'STOP: {case_id} runtime closure differs from binding')
        sources = [i['sha256'] for i in spec['closure'] if i['target'] == source_target]
        if sources != [binding['preflight_source_sha256']]:
            raise PreflightStop(f'STOP: {case_id} preflight source differs from binding')
        if _spec_node_files(spec) != row['files_sha256']:
            raise PreflightStop(f'STOP: {case_id} specification files differ from binding')
        env = spec.get('env') or {}
        if {k: env.get(k) for k in ('AR_TRAIN_SEED', 'AR_SPLIT_SEED')} != row['seeds']:
            raise PreflightStop(f'STOP: {case_id} specification seeds differ from binding')
        if list(spec.get('argv') or [])[1:] != ['-B', source_target, '--node-dir', '/work/node',
                                                '--kind', row['kind']]:
            raise PreflightStop(f'STOP: {case_id} specification command is not the preflight')
        if rec.get('schema') != SCHEMA or rec.get('status') != 'ok':
            raise PreflightStop(f'STOP: {case_id} preflight record not ok')
        if rec.get('kind') != row['kind'] or rec.get('seeds') != row['seeds']:
            raise PreflightStop(f'STOP: {case_id} kind or seeds differ from binding')
        if rec.get('files_sha256') != row['files_sha256']:
            raise PreflightStop(f'STOP: {case_id} executed files differ from binding (exact set)')
        if rec.get('cache_fingerprint') != row['cache_fingerprint']:
            raise PreflightStop(f'STOP: {case_id} cache copy differs from binding')
        if rec.get('fit_reached') is not True or rec.get('model_fit_performed') is not False \
                or rec.get('metric_computed') is not False:
            raise PreflightStop(f'STOP: {case_id} preflight did not stop exactly at the fit')
    digest = _sha(_canonical({k: results[k]['record'] for k in sorted(results)}))
    return {'schema': SCHEMA + '+check', 'binding_sha256': binding['binding_sha256'],
            'records_sha256': digest, 'cases': len(expected),
            'runtime_closure_sha256': closure_sha,
            'preflight': 'ALL_16_PASSED_UNQUALIFIED',
            'offline_executability': 'PREFLIGHT_PASSED_PENDING_SITE_QUALIFICATION'}


def verify_execution_binding(binding, case_id, files, cache_fingerprint, runtime_closure_sha256):
    """Call immediately before a later real execution of ``case_id``.

    ``files`` are the exact bytes to be placed in the execution copy. Any
    difference from the preflight binding is a STOP. Not yet called by
    ``c3_env_replay.run``: wiring is a separate reviewed step.
    """
    rows = {row['case_id']: row for row in binding['cases']}
    row = rows.get(case_id)
    if row is None:
        raise PreflightStop(f'STOP: {case_id} was not preflighted')
    if {n: _sha(b) for n, b in sorted(files.items())} != row['files_sha256']:
        raise PreflightStop(f'STOP: {case_id} execution files differ from preflight')
    if cache_fingerprint != row['cache_fingerprint']:
        raise PreflightStop(f'STOP: {case_id} execution cache differs from preflight')
    if runtime_closure_sha256 != binding['runtime_closure_sha256']:
        raise PreflightStop(f'STOP: {case_id} execution runtime differs from preflight')
    return True


PAPER_TARGET = '/runtime/paper'
# Top-level site-packages entries the pinned node code imports up to the fit
# (measured with the local sklearn 1.9.1 stack; the host list must be
# re-derived for the pinned environment, e.g. sklearn 1.8.0 may not need
# narwhals). A missing entry fails the boundary run as an import error.
PREFLIGHT_PACKAGES = ('numpy', 'numpy.libs', 'pandas', 'sklearn', 'scikit_learn.libs', 'scipy',
                      'scipy.libs', 'joblib', 'threadpoolctl.py', 'yaml', '_yaml', 'dateutil',
                      'six.py', 'narwhals')
PREFLIGHT_MODULES = ('r1/__init__.py', 'r1/c3/__init__.py', 'r1/c3/offline_case_preflight.py',
                     'r1/c3/offline_preflight.py')
THREAD_ENV = {'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
              'NUMEXPR_NUM_THREADS': '1'}


def preflight_extra_files(paper_root):
    """(source, target) pairs for the trusted preflight modules in the closure."""
    paper_root = Path(paper_root)
    return [(str(paper_root / rel), f'{PAPER_TARGET}/{rel}') for rel in PREFLIGHT_MODULES]


def build_preflight_spec(case, harness, staging, closure, *, cache_dir=None, tmpfs_bytes=256 << 20):
    """Bootstrap specification for one case's boundary preflight run.

    Materializes the case's exact node files under ``staging`` (a new private
    directory) and lists them, and every file of the private cache copy, as
    hash-pinned working files under ``/work/node``. ``closure`` comes from
    ``offline_runtime_closure.build_closure`` with :func:`preflight_extra_files`.
    """
    staging = Path(staging)
    kind = node_kind(case['node'])
    staging.mkdir(mode=0o700)
    work = []
    for name, data in sorted(case_files(case, harness).items()):
        src = staging / name
        src.write_bytes(data)
        work.append({'source': str(src), 'target': f'/work/node/{name}', 'sha256': _sha(data)})
    if kind == 'openml':
        if cache_dir is None:
            raise PreflightStop(f"STOP: {case['case_id']} needs its private cache copy")
        cache_dir = Path(cache_dir)
        for p in sorted(cache_dir.rglob('*')):
            if p.is_symlink():
                raise PreflightStop('STOP: symlink in cache copy')
            if p.is_file():
                rel = p.relative_to(cache_dir).as_posix()
                work.append({'source': str(p), 'target': f'/work/node/data_cache/{rel}',
                             'sha256': _sha(p.read_bytes())})
    env = {'HOME': '/work', 'TMPDIR': '/work', 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONPATH': PAPER_TARGET, 'AR_TRAIN_SEED': str(case['train_seed']),
           'AR_SPLIT_SEED': str(case['split_seed']), **THREAD_ENV}
    argv = [closure['python'], '-B', f'{PAPER_TARGET}/r1/c3/offline_case_preflight.py',
            '--node-dir', '/work/node', '--kind', kind]
    return {'root': '/unused', 'tmpfs_bytes': tmpfs_bytes, 'closure': closure['items'],
            'work_files': work, 'argv': argv, 'env': env}


def parse_preflight_log(text):
    """Exactly one ``M3_PREFLIGHT`` record line, else STOP."""
    lines = [ln for ln in text.splitlines() if ln.startswith('M3_PREFLIGHT ')]
    if len(lines) != 1:
        raise PreflightStop('STOP: preflight record missing or repeated')
    return json.loads(lines[0][len('M3_PREFLIGHT '):])


if __name__ == '__main__':
    raise SystemExit(main())
