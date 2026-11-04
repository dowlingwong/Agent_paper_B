"""Synthetic tests: no real evidence, labels, or models are read."""
import pytest
from r1.c3.gate import gate_sha256
from r1.c3.guarded_labels import load_sweep2_jsonl


def test_fake_plan_never_authorizes_or_opens_file(tmp_path, monkeypatch):
    target = tmp_path / 'labels.jsonl'
    target.write_text('{"y_eval": 1}\n')
    fake = tmp_path / 'PLAN.md'
    fake.write_text('## 10. Open decisions\n| R1-BX-D8-CONFIRM | ' + gate_sha256() + ' |\n')
    original = type(target).read_bytes
    def guarded(path):
        if path == target:
            raise AssertionError('label file must not be opened')
        return original(path)
    monkeypatch.setattr(type(target), 'read_bytes', guarded)
    with pytest.raises(TypeError):
        load_sweep2_jsonl(target, expected_sha256='a' * 64, plan=fake)
    with pytest.raises(RuntimeError, match='trusted committed author PLAN'):
        load_sweep2_jsonl(target, expected_sha256='a' * 64)
