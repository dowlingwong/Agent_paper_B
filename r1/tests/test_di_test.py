"""AI-assisted by Codex. Synthetic file-only method checks; no workers or LLMs."""
import copy
import json
import subprocess

import pytest

from r1.diagnostics.di_test import CommittedInputs, analyze, collect, replay


class Fixture:
    revision = 'synthetic'
    hashes = {}

    def __init__(self, shifted=False):
        self.data = {'points.json': []}
        for i in range(24):
            inst = f'digits_mlp__s{i}'
            changed = i < 12
            start = 'ALPHA = 0.1\nMAX_ITER = 40\n'
            first = trial(inst, 1, 'ALPHA', .1, .2, 'kept', None)
            pending = trial(inst, 2, 'ALPHA', .2, .4, 'discarded', -.1)
            self.data['points.json'].append({'instance': inst, 'budget_index': 2,
                                            'features': {'node': 'digits_mlp', 'sigma_d': .1}})
            self.data[f'roots/{inst}.json'] = {'start_files': {'train.py': start}}
            self.data[f'provenance/ledgers/roots/{inst}/root_trials.jsonl'] = [first, pending]
            snap = f'provenance/snapshots/{inst}/E2_b002'
            self.data[f'{snap}/manifest.json'] = {'editable_paths': ['train.py']}
            self.data[f'{snap}/incumbent/train.py'] = 'ALPHA = 0.2\nMAX_ITER = 40\n'
            for action in ('continue', 'verify'):
                for rep in (1, 2):
                    point = copy.deepcopy(pending)
                    if action == 'verify':
                        point['decision'] = 'kept' if changed else 'discarded'
                        point['extra']['control'] = {'verify': {
                            'original_decision': 'discarded', 'mean_delta': .1 if changed else -.1}}
                    post = []
                    for j in range(3):
                        delta = .5 if shifted and changed and action == 'verify' else .01
                        post.append(trial(inst, 3+j, 'MAX_ITER', 40*2**j, 40*2**(j+1), 'kept', delta))
                    path = f'provenance/ledgers/branches/{inst}__b002__{action}__r{rep}'
                    self.data[f'{path}/branch_trials.jsonl'] = [first, point]+post
                    self.data[f'{path}/branch_events.jsonl'] = [{'event_type':'branch_trial_committed'}]

    def json(self, path):
        return copy.deepcopy(self.data[path])

    rows = json

    def text(self, path):
        return self.data[path]


def trial(inst, index, key, old, new, decision, delta):
    return {'trial_id': f'{inst}-{index}', 'budget_index': index, 'decision': decision,
            'delta_vs_best': delta, 'extra': {'manager': {'structured_edit': {
                'symbol': key, 'old': str(old), 'new': str(new)}}}}


def test_di_holds_not_rejected():
    result = analyze(Fixture(), draws=399)
    assert result['verdict'] == 'undetermined at this sample size'
    assert not any(r['reject'] for r in result['results'])
    assert result['counts']['digits_mlp'] == {'promotion': 24, 'unchanged': 24}
    assert all(r['cross'] == 0 for r in result['point_contrasts'])


def test_shift_detected_and_deterministic():
    result = analyze(Fixture(shifted=True), draws=999)
    again = analyze(Fixture(shifted=True), draws=999)
    assert result == again
    primary = next(r for r in result['results'] if r['group']=='digits_mlp'
                   and r['horizon']=='1' and r['metric']=='mean_delta')
    assert primary['excess_null'] == pytest.approx(.49)
    assert primary['excess_unchanged'] == pytest.approx(.49)
    assert primary['reject'] and primary['holm_p'] < .05
    assert result['verdict'].startswith('violated')


def test_snapshot_and_shared_history_checks():
    source = Fixture()
    source.data['provenance/snapshots/digits_mlp__s0/E2_b002/incumbent/train.py'] = 'ALPHA = 0.3\nMAX_ITER = 40\n'
    with pytest.raises(ValueError, match='snapshot incumbent'):
        collect(source)
    source = Fixture()
    path = 'provenance/ledgers/branches/digits_mlp__s0__b002__continue__r1/branch_trials.jsonl'
    source.data[path] = copy.deepcopy(source.data[path])
    source.data[path][0]['decision'] = 'discarded'
    with pytest.raises(ValueError, match='share the recorded root history'):
        collect(source)


def test_novelty_remembers_discarded_prefix_and_uses_active_keys():
    rows = [trial('x',1,'ALPHA',.1,.2,'kept',None),
            trial('x',2,'ALPHA',.2,.4,'discarded',-.1),
            trial('x',3,'ALPHA',.2,.4,'discarded',-.1)]
    out = replay(rows, {'ALPHA':.1}, 'digits_mlp', 2, {'ALPHA':.2})
    assert out[0]['duplicate'] == 1 and out[0]['novel'] == 0
    start = dict(model_type='logistic_regression',C=.1,max_iter=1000,
                 class_weight='balanced',scaler='standard',max_depth=5)
    rows = [trial('x',1,'max_depth',5,6,'kept',None),
            trial('x',2,'max_depth',6,7,'discarded',0),
            trial('x',3,'max_depth',6,8,'discarded',0)]
    out = replay(rows,start,'openml_ionosphere',2,dict(start,max_depth=6))
    assert out[0]['novel']==0 and out[0]['duplicate']==1 and out[0]['identical']==1


def test_inputs_are_committed_blobs(tmp_path):
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    run = tmp_path/'run'
    run.mkdir()
    (run/'points.json').write_text('[1]')
    subprocess.run(['git','-C',str(tmp_path),'add','.'],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Fixture',
                    '-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
    (run/'points.json').write_text('[999]')
    source=CommittedInputs(run)
    assert source.json('points.json')==[1]
    assert len(source.hashes)==1
