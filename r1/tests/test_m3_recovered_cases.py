"""Read-only recovery tests; synthetic cache contents, no numerical replay."""
import os
from pathlib import Path

import pytest

from r1.c3.offline_recovered_cases import bind_recovered_cases, RecoveryStop
from r1.scripts.c3_env_replay import verify_corpus


def _harness():
    path = os.environ.get('AR_M3_PINNED_HARNESS')
    if not path:
        if os.environ.get('R1_REQUIRE_M3_HARNESS') == '1':
            pytest.fail('AR_M3_PINNED_HARNESS required')
        pytest.skip('set AR_M3_PINNED_HARNESS')
    return Path(path)


def test_recovered_cases_are_bound_to_exact_synthetic_cache_pairs(tmp_path):
    harness = _harness()
    paper = Path(__file__).resolve().parents[2]
    corpus = verify_corpus(paper)
    nodes = [node for node in corpus['index_doc']['nodes'] if node.startswith('openml_')]
    sources, copies = {}, {}
    for node in nodes:
        sources[node] = tmp_path / 'sources' / node
        copies[node] = tmp_path / 'copies' / node
        for root in (sources[node], copies[node]):
            root.mkdir(parents=True)
            (root / 'synthetic-cache.bin').write_bytes(('fixture:' + node).encode())
    manifest = bind_recovered_cases(paper, harness, sources, copies)
    assert len(manifest['config_checks']['checks']) == 16
    assert set(manifest['cache_pairs']) == set(nodes)
    assert manifest['offline_executability'] == 'NOT_ESTABLISHED'
    assert manifest['config_checks']['offline_executability'] == 'NOT_ESTABLISHED'
    assert all(pair['cache']['files'][0]['path'] == 'synthetic-cache.bin'
               for pair in manifest['cache_pairs'].values())
    # A byte change in one copied cache aborts the entire declaration.
    (copies[nodes[0]] / 'synthetic-cache.bin').write_bytes(b'changed')
    with pytest.raises(RecoveryStop, match='source and private cache differ'):
        bind_recovered_cases(paper, harness, sources, copies)


def test_pair_maps_must_be_complete_and_disjoint(tmp_path, monkeypatch):
    # Isolate pair validation from corpus I/O; this test cannot establish any
    # provenance and does not claim the resulting cases are executable.
    import r1.c3.offline_recovered_cases as module
    nodes = [f'openml_n{i}' for i in range(6)]
    monkeypatch.setattr(module, 'verify_corpus', lambda paper: {})
    monkeypatch.setattr(module, 'verify_collector_binding', lambda paper: {})
    monkeypatch.setattr(module, 'select_cases', lambda *args: [{'node': n} for n in nodes])
    src, copies = {}, {}
    for node in nodes:
        src[node] = tmp_path / 'src' / node
        copies[node] = tmp_path / 'copy' / node
        src[node].mkdir(parents=True)
        copies[node].mkdir(parents=True)
    with pytest.raises(RecoveryStop, match='six selected'):
        bind_recovered_cases(tmp_path, tmp_path, src, {})
    copies[nodes[0]] = src[nodes[0]]
    with pytest.raises(RecoveryStop, match='distinct and non-overlapping'):
        bind_recovered_cases(tmp_path, tmp_path, src, copies)
