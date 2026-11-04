"""B.2 audit-plan dry run (M3). Reads the frozen corpus read-only; writes only to tmp_path; runs no worker."""
import json
from pathlib import Path

import pytest

from r1.c3 import dataset
from r1.c3.audit import partition_population
from r1.scripts import c3_audit_dryrun as D

REPO = Path(__file__).resolve().parents[2]


def test_design_is_k10_with_disjoint_label_and_evaluation_seeds():
    assert D.design_check() == {'k': 10, 'label_seeds': [7001, 7002, 7003, 7004, 7005],
                                'evaluation_seeds': [7006, 7007, 7008, 7009, 7010], 'disjoint': True}


def test_dryrun_on_the_frozen_corpus_partitions_the_whole_population(tmp_path):
    before = {p: D._sha(REPO / p) for p in (D.INDEX, D.SIDECAR)}
    report = D.dryrun(REPO, tmp_path / 'report', verify_git=(REPO / '.git').exists())
    counts = report['counts']
    assert sum(counts.values()) == report['table']['proposals']
    assert report['table']['replay_checks_total']['zero_delta_violations'] == 0
    assert report['table']['replay_checks_total']['repeat_metric_violations'] == 0
    assert report['blocks']['duplicates_labelled'] == 0
    assert report['blocks']['label_rows'] == counts['noops'] + counts['eligible']
    assert report['blocks']['evaluation_rows'] == counts['eligible']
    assert report['planned_seed_runs'] == 10 * report['unique_audit_configs']
    by_node = sum(sum(v.values()) for v in report['counts_by_node'].values())
    by_mode = sum(sum(v.values()) for v in report['counts_by_memory_mode'].values())
    assert by_node == by_mode == report['table']['proposals']
    assert {p: D._sha(REPO / p) for p in (D.INDEX, D.SIDECAR)} == before
    assert json.loads((tmp_path / 'report/audit_dryrun.json').read_text())['label'] == 'DRYRUN'


def _rows():
    base = {'source': 's', 'memory_mode': 'none', 'instance_seed': 100, 'sigma_node': 0.01, 'features': {}}
    return [
        {**base, 'proposal_id': 'noop', 'node': 'n', 'noop': True, 'duplicate': False,
         'candidate_hash': 'a', 'incumbent_hash': 'a', 'noop_kind': 'incumbent_repeat'},
        {**base, 'proposal_id': 'dup', 'node': 'n', 'noop': False, 'duplicate': True,
         'candidate_hash': 'b', 'incumbent_hash': 'a'},
        {**base, 'proposal_id': 'new', 'node': 'n', 'noop': False, 'duplicate': False,
         'candidate_hash': 'c', 'incumbent_hash': 'a'},
    ]


def test_noops_are_labelled_by_rule_duplicates_get_no_label(tmp_path, monkeypatch):
    rows = _rows()
    plan, counts = partition_population(rows, {'a': {}, 'b': {}, 'c': {}})
    assert counts == {'noops': 1, 'duplicates': 1, 'eligible': 1}
    assert [p['proposal_id'] for p in plan] == ['new']
    monkeypatch.setattr(dataset, 'load_table', lambda _: rows)
    blocks = D.block_checks(tmp_path, rows, plan)
    assert blocks['label_rows_rule_noop'] == 1 and blocks['label_rows_audit'] == 1
    assert blocks['evaluation_rows'] == 1 and blocks['duplicates_labelled'] == 0


def test_partition_refuses_duplicate_ids_or_missing_configs():
    rows = _rows()
    with pytest.raises(ValueError, match='duplicate proposal IDs'):
        partition_population(rows + [rows[0]], {'a': {}, 'b': {}, 'c': {}})
    with pytest.raises(ValueError, match='lacks configuration'):
        partition_population(rows, {'a': {}})


def test_report_directory_must_be_new(tmp_path):
    (tmp_path / 'report').mkdir()
    with pytest.raises(ValueError, match='must be new'):
        D.dryrun(REPO, tmp_path / 'report')


def test_frozen_source_pins_reject_self_consistent_replacement(tmp_path, monkeypatch):
    index = tmp_path / D.INDEX
    sidecar = tmp_path / D.SIDECAR
    index.parent.mkdir(parents=True)
    sidecar.parent.mkdir(parents=True)
    index.write_text('{"index":"original"}')
    sidecar.write_text(json.dumps({'index': {'sha256': D._sha(index)}, 'note': 'original'}))
    monkeypatch.setattr(D, 'INDEX_SHA256', D._sha(index))
    monkeypatch.setattr(D, 'SIDECAR_SHA256', D._sha(sidecar))
    D.verify_source_pins(tmp_path)
    sidecar.write_text(json.dumps({'index': {'sha256': D._sha(index)}, 'note': 'tampered'}))
    with pytest.raises(ValueError, match='fixed source digest'):
        D.verify_source_pins(tmp_path)
    index.write_text('{"index":"changed"}')
    sidecar.write_text(json.dumps({'index': {'sha256': D._sha(index)}}))
    with pytest.raises(ValueError, match='fixed source digest'):
        D.verify_source_pins(tmp_path)


def test_dryrun_refuses_frozen_corpus_batch_and_symlink_alias_before_writes(tmp_path, monkeypatch):
    paper = tmp_path / 'paper'
    corpus = paper / 'results/frozen'
    batch = tmp_path / 'batch'
    corpus.mkdir(parents=True)
    batch.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(corpus, target_is_directory=True)
    monkeypatch.setattr(D, 'CORPUS_TREES', {'results/frozen': 'fixture'})
    monkeypatch.setattr(D, 'BATCH', str(batch))
    for output in (corpus / 'new', alias / 'new', batch / 'new'):
        with pytest.raises(ValueError, match='inside preserved'):
            D.dryrun(paper, output, verify_git=False)
        assert not output.exists()
