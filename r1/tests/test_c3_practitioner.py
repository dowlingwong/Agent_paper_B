"""Synthetic D7 tests; no experiments or real audit tables."""
import pytest
from r1.c3.practitioner import offline_welch_values, welch_replicates
from r1.c3.gate import gate_sha256


def test_welch_strong_gain_loss_and_explicit_accounting():
    gain = welch_replicates([10., 11., 9.], [0., 1., -1.], remaining_runs=6)
    assert gain['keep'] and gain['worker_runs_charged'] == 6
    assert not welch_replicates([0., 1., -1.], [10., 11., 9.], remaining_runs=6)['keep']
    assert not welch_replicates([1., 1., 1.], [1., 1., 1.], remaining_runs=6)['keep']


def test_invalid_or_underfunded_comparisons_fail_closed():
    with pytest.raises(ValueError, match='budget'):
        welch_replicates([1., 1., 1.], [0., 0., 0.], remaining_runs=5)
    with pytest.raises(ValueError, match='finite'):
        welch_replicates([1., float('nan'), 1.], [0., 0., 0.], remaining_runs=6)


def test_offline_adapter_refuses_fabricated_plan_before_iteration(tmp_path):
    class Forbidden:
        def __iter__(self):
            raise AssertionError('rows read before gate')
    fake = tmp_path / 'PLAN.md'
    fake.write_text('## 10. Open decisions\n| R1-BX-D8-CONFIRM | ' + gate_sha256() + ' |\n')
    with pytest.raises(TypeError):
        offline_welch_values(Forbidden(), plan=fake)
    with pytest.raises(RuntimeError, match='trusted committed author PLAN'):
        offline_welch_values(Forbidden())
