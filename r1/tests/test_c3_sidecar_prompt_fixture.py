"""Fixture-only controller prompt forwarding and fallback checks."""
from types import SimpleNamespace

import numpy as np
import pytest

from r1.c3 import control
from r1.c3.env import onehot
from r1.c3.features import FEATURES
from r1.c3.prior_model import FixedPrior, SidecarPrior


@pytest.fixture
def setup(monkeypatch):
    result = SimpleNamespace(features={c: 0.0 for c in FEATURES}, edit={'symbol': 'x'},
                             noop=False, duplicate=False)
    monkeypatch.setattr(control, 'featurize_view', lambda view, ctx: result)
    ctx = SimpleNamespace(node='n', sigma_node=0.01)
    fallback = FixedPrior(onehot(11), 'fixture')
    return ctx, fallback


def view(epoch='E1', summary='original'):
    return SimpleNamespace(epoch=epoch, budget_index=2, budget={}, proposal={
        'proposal_summary': summary, 'extra': {'structured_edit': {'symbol': 'x'}}},
        input_hash=lambda: 'fixture-hash')


def test_sidecar_receives_prompt_at_e1_and_changed_e2(setup, monkeypatch):
    ctx, fallback = setup
    prior = SidecarPrior('http://unused.invalid', fallback)
    received = []
    def fake_post(row):
        received.append(row.copy())
        return {'probs': list(onehot(11)), 'digest': 'fixture', 'version': 'fixture'}
    monkeypatch.setattr(prior, '_post', fake_post)
    calls = []
    def build(v, c):
        calls.append((v, c))
        return SimpleNamespace(state='state-' + v.epoch, proposal=v.proposal['proposal_summary'])
    ctl = control.RuleController(prior, ctx, prompt_builder=build, verify=False)
    e1 = view()
    ctl.decide(e1, {'skip': True})
    assert received[0]['prompt'] == {'state': 'state-E1', 'proposal': 'original'}
    assert calls == [(e1, ctx)]
    ctl.keep_prior(view('E2', 'original'))
    assert len(received) == 1
    e2 = view('E2', 'revised')
    keep = ctl.keep_prior(e2)
    assert received[1]['prompt'] == {'state': 'state-E2', 'proposal': 'revised'}
    assert calls[-1] == (e2, ctx)
    assert 'e2_forecast' in keep.source


@pytest.mark.parametrize('builder', [lambda v, c: None,
                                    lambda v, c: SimpleNamespace(state='', proposal='p'),
                                    lambda v, c: (_ for _ in ()).throw(ValueError('bad prompt'))])
def test_prompt_failure_falls_back_and_emits_event(setup, monkeypatch, builder):
    ctx, fallback = setup
    prior = SidecarPrior('http://unused.invalid', fallback)
    monkeypatch.setattr(prior, '_post', lambda row: pytest.fail('sidecar must not be called'))
    ctl = control.RuleController(prior, ctx, prompt_builder=builder, verify=False)
    decision = ctl.decide(view(), {'skip': True})
    assert decision.detail['fallback'] == 'prior_unavailable: prompt_serialization'
    assert decision.detail['fallback_version'] == fallback.version
    assert decision.events[0][0] == 'prior_unavailable'
    np.testing.assert_allclose(decision.detail['probs'], onehot(11))


def test_non_sidecar_never_serializes(setup):
    ctx, prior = setup
    def fail(*args):
        pytest.fail('non-sidecar must not serialize')
    ctl = control.RuleController(prior, ctx, prompt_builder=fail, verify=False)
    decision = ctl.decide(view(), {'skip': True})
    assert decision.detail['fallback'] is None
    np.testing.assert_allclose(decision.detail['probs'], onehot(11))


def test_real_serializer_e1_and_fresh_resume_without_download(monkeypatch):
    from r1.c3 import features
    from r1.c3.train import serialize
    from r1.tests.test_trackp_serialize import CTX, _ledger, _view

    class Tokenizer:
        def __call__(self, text, **kwargs):
            return {'input_ids': list(range(len(text.split())))}

    monkeypatch.setattr(serialize, 'pool_tokenizers', lambda: {'fixture': Tokenizer()})
    monkeypatch.setattr(features, '_is_control_plane_skip', lambda row: False)
    fallback = FixedPrior(onehot(11), 'fixture')
    prior = SidecarPrior('http://unused.invalid', fallback)
    received = []
    monkeypatch.setattr(prior, '_post', lambda row: received.append(row.copy()) or
                        {'probs': list(onehot(11)), 'digest': 'fixture', 'version': 'fixture'})
    rows = _ledger()
    rows[0]['extra']['audit'] = {'secret': 'AUDITSECRET'}
    replay = _view(rows, 3)
    v = SimpleNamespace(epoch='E1', budget_index=replay.budget_index, ledger_prefix=replay.ledger_prefix,
                        current_best=replay.current_best, proposal=replay.proposal,
                        budget={}, input_hash=lambda: 'fixture')
    ctl = control.RuleController(prior, CTX, verify=False, rule_layer=False)
    ctl.decide(v, {'skip': True})
    assert received[-1]['prompt']['state'] and received[-1]['prompt']['proposal']
    assert 'AUDITSECRET' not in str(received[-1]['prompt'])
    resumed = control.RuleController(prior, CTX, verify=False, rule_layer=False)
    v.epoch = 'E2'
    resumed.keep_prior(v)
    assert len(received) == 2 and received[-1]['prompt'] == received[-2]['prompt']
    from r1.c3.features import ReplayProposal
    v.proposal = ReplayProposal(extra={'structured_edit': {'symbol': 'ALPHA', 'old': '1e-4',
                                                             'new': '1e-2', 'path': 'train.py'}})
    ctl.keep_prior(v)
    assert len(received) == 3 and received[-1]['prompt']['proposal'] != received[0]['prompt']['proposal']
