"""All-16-case preflight under the M3 boundary on the local kernel (opt-in).

Requires AR_M3_KERNEL_TESTS=1, AR_M3_DELEGATED_CGROUP, AR_M3_PINNED_HARNESS
(6adf385) and the local Python stack. Uses the 16 actual recovered case
configurations, the actual pinned node sources, a runtime closure built from
the local interpreter, and SYNTHETIC two-class OpenML caches (see
test_m3_case_preflight.py). Each case runs in a fresh supervisor (clone3 into
a private cgroup, namespaces, private root, seccomp listener, sentinel drain).
Local synthetic evidence only: the local stack is not the pinned one (sklearn
1.9.1 here) and this is not the target-host qualification.
"""
import hashlib
import json
import os
from pathlib import Path
import platform

import pytest

from r1.c3 import offline_case_preflight as pf
from r1.c3 import offline_runtime_closure as rc
from r1.c3 import offline_supervisor as sup
from r1.c3.offline_preflight import cache_snapshot

pytestmark = pytest.mark.skipif(
    os.environ.get('AR_M3_KERNEL_TESTS') != '1' or not os.environ.get('AR_M3_DELEGATED_CGROUP')
    or not os.environ.get('AR_M3_PINNED_HARNESS')
    or platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'),
    reason='set AR_M3_KERNEL_TESTS=1, AR_M3_DELEGATED_CGROUP and AR_M3_PINNED_HARNESS')

PAPER = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def env(tmp_path_factory):
    from r1.scripts.c3_env_replay import select_cases, verify_corpus
    from test_m3_case_preflight import binary_fixture_cache
    harness = Path(os.environ['AR_M3_PINNED_HARNESS'])
    cases = select_cases(PAPER, verify_corpus(PAPER), harness)
    closure = rc.build_closure(pf.PREFLIGHT_PACKAGES, extra=pf.preflight_extra_files(PAPER))
    base = tmp_path_factory.mktemp('m3pf')
    caches = {}
    for case in cases:
        if case['node'].startswith('openml_') and case['node'] not in caches:
            data_id = json.loads(pf.case_files(case, harness)['dataset.json'])['dataset_id']
            caches[case['node']] = base / 'caches' / case['node']
            binary_fixture_cache(caches[case['node']], data_id)
    return {'harness': harness, 'cases': cases, 'closure': closure, 'base': base, 'caches': caches}


def run_case(env, case, label, cache=None):
    root = env['base'] / label
    root.mkdir()
    spec = pf.build_preflight_spec(case, env['harness'], root / 'staging', env['closure'],
                                   cache_dir=cache if cache is not None else env['caches'].get(case['node']))
    out = root / 'out'
    result = sup.supervise(spec, os.environ['AR_M3_DELEGATED_CGROUP'], str(out),
                           protected_roots=[str(env['harness'])], timeout_seconds=300)
    return result, out, spec


def test_all_16_cases_preflight_cleanly_under_the_boundary(env):
    fingerprints = {node: cache_snapshot(path)['sha256'] for node, path in env['caches'].items()}
    source_sha = hashlib.sha256((PAPER / 'r1/c3/offline_case_preflight.py').read_bytes()).hexdigest()
    binding = pf.build_case_binding(env['cases'], env['harness'], fingerprints,
                                    env['closure']['sha256'], source_sha)
    results = {}
    for i, case in enumerate(env['cases']):
        result, out, spec = run_case(env, case, f'case{i:02d}')
        record = pf.parse_preflight_log((out / 'bootstrap.log').read_text())
        results[case['case_id']] = {'supervisor': result, 'record': record, 'spec': spec}
    verdict = pf.check_preflight_results(binding, results)
    assert verdict['preflight'] == 'ALL_16_PASSED_UNQUALIFIED' and verdict['cases'] == 16


def test_damaged_cache_redownload_attempt_is_stopped_by_the_kernel_filter(env, tmp_path):
    case = next(c for c in env['cases'] if c['node'] == 'openml_ionosphere')
    damaged = tmp_path / 'damaged'
    import shutil
    shutil.copytree(env['caches']['openml_ionosphere'], damaged)
    for p in damaged.rglob('*.gz'):
        if 'features' in p.parts:
            p.write_bytes(b'not gzip')     # sklearn: "Invalid cache, redownloading"
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall'):
        run_case(env, case, 'damaged', cache=damaged)
