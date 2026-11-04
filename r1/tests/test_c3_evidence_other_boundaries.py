"""Identifiable sweep evidence must not enter unverified training interfaces."""
import pytest

from r1.c3.evidence_boundary import is_identifiable_sweep_evidence, refuse_unverified_sweep_rows


def test_evidence_identification_and_legacy_compatibility():
    from r1.c3.train.types import DecisionPrompt
    assert is_identifiable_sweep_evidence({'_evidence_seed_split': True})
    assert is_identifiable_sweep_evidence({'meta': {'classification': {'decision_id': 'R1-SWEEP1-CLASSIFY'}}})
    assert is_identifiable_sweep_evidence({'label': 'EVIDENCE'})
    assert is_identifiable_sweep_evidence({'prompt': DecisionPrompt(state='s', proposal='p',
                                         meta={'classification': {'decision_id': 'R1-SWEEP1-CLASSIFY'}})})
    assert not is_identifiable_sweep_evidence({'label': 'PILOT', 'soft': [1.0]})
    refuse_unverified_sweep_rows([{'label': 'PILOT'}], 'legacy')
    with pytest.raises(ValueError, match='verified label-only'):
        refuse_unverified_sweep_rows([{'_evidence_seed_split': True}], 'training')


def test_env_and_prior_reject_identifiable_sweep_rows():
    from r1.c3.env import OfflineBanditEnv
    from r1.c3.prior_model import TableArmPrior

    rows = [{'_evidence_seed_split': True}]
    for split in ('label', 'eval'):
        with pytest.raises(ValueError, match='verified label-only'):
            OfflineBanditEnv(rows, split=split, plugin='onehot_moments')
    with pytest.raises(ValueError, match='verified label-only'):
        TableArmPrior.fit('A1', rows)


def test_awr_rejects_even_when_alias_is_supplied():
    from r1.c3.control import fit_awr_direct
    with pytest.raises(ValueError, match='verified label-only'):
        fit_awr_direct([{'_evidence_seed_split': True, 'renamed_eval_outcome': 1}],
                       value_key='renamed_eval_outcome')
    with pytest.raises(ValueError, match='evaluation-seed outcomes'):
        fit_awr_direct([{'delta_audit_all': 1}], value_key='delta_audit_all')


def test_trackp_guard_rejects_identifiable_sweep_training(monkeypatch):
    from r1.c3.train import run
    rows = [{'_evidence_seed_split': True, 'soft': [1.0]}]
    with pytest.raises(run.TrackPStop, match='verified label-only'):
        run.guard_rows(rows, purpose='sft')
    monkeypatch.setattr(run, 'authorization_note', lambda _: None)
    with pytest.raises(run.TrackPStop, match='P.4 final evaluation needs'):
        run.guard_rows(rows, purpose='p4_final_eval')
    assert run.guard_rows([{'label': 'PILOT', 'soft': [1.0]}], purpose='sft')


@pytest.mark.parametrize('key', ['delta_true', 'delta_audit_all', 'se_audit',
                                 'candidate_metrics', 'incumbent_metrics'])
def test_trackp_guard_rejects_eval_aliases_even_in_prompt_meta(key):
    from r1.c3.train import run
    from r1.c3.train.types import DecisionPrompt
    prompt = DecisionPrompt(state='s', proposal='p', meta={key: 1})
    with pytest.raises(run.TrackPStop, match='evaluation-seed columns'):
        run.guard_rows([{'prompt': prompt}], purpose='sft')


@pytest.mark.parametrize('nested', [
    {'nested': [{'delta_true': 1}]},
    {'nested': ({'items': [{'candidate_metrics': [1, 2]}]},)},
])
def test_trackp_guard_rejects_evaluation_fields_in_nested_sequences(nested):
    from r1.c3.train import run
    with pytest.raises(run.TrackPStop, match='evaluation-seed columns'):
        run.guard_rows([nested], purpose='sft')


def test_trackp_guard_sequence_cycles_are_bounded():
    from r1.c3.train import run
    cycle = []
    cycle.append(cycle)
    assert run.guard_rows([{'nested': cycle}], purpose='sft')


def test_trainer_rejects_p4_even_with_authorization_and_accepts_synthetic_e0(tmp_path, monkeypatch):
    import gzip
    import json
    from pathlib import Path

    torch = pytest.importorskip('torch')
    from r1.c3.train import run
    from r1.c3.train import exam_synthetic
    from r1.c3.train.trainer import Trainer, TrainConfig

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.p = torch.nn.Parameter(torch.tensor(1.0))

        def trainable_parameters(self):
            return self.parameters()

    monkeypatch.setattr(run, 'authorization_note', lambda _: tmp_path / 'trackp_p4.md')
    with pytest.raises(run.TrackPStop, match='training interface'):
        Trainer(Tiny(), [], lambda *_: None, TrainConfig(), tmp_path, purpose='p4_final_eval')
    path = Path(__file__).resolve().parents[1] / 'c3/train/data/e0_v1.jsonl.gz'
    with gzip.open(path, 'rt') as f:
        item = json.loads(next(f))
    row = {'prompt': exam_synthetic.prompt_from_dict(item['prompt']),
           'y': torch.tensor(item['y_soft']), 'item': item}
    trainer = Trainer(Tiny(), [row], lambda *_: None, TrainConfig(), tmp_path, purpose='train')
    assert trainer.rows == [row]
