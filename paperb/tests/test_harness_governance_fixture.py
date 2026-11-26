"""Fixture-only checks for legacy metric sign in the pinned harness audit."""
from dataclasses import replace

import pytest

from r1.harness import import_harness

import_harness()
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.claw_worker import _extract_worker_result  # noqa: E402


@pytest.mark.parametrize('metric,expected', [('val_bpb', 0.2), ('val_auc', 0.8)])
def test_legacy_metric_sign_for_declared_bpb_and_auc(tmp_path, metric, expected):
    spec = load_registered_node('autoresearch_macos')
    spec = replace(spec, metric_name=metric)
    payload = {'history': [{'run': {'worker': {'last_result': {'changed_files': ['train.py']}},
                                     'experiment': {'success': True, 'val_bpb': 0.2, 'log_path': ''}}}]}
    result = _extract_worker_result(payload, spec, packet_ref='fixture', artifact_dir=tmp_path, node_root=tmp_path)
    assert result.success
    assert result.parsed_metrics == {metric: pytest.approx(expected)}
