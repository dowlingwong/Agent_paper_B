"""Tests of the STOP 6 report template (``r1/scripts/b2_stop6_report.py``) on synthetic fixtures.

The analysis fixture is produced by the real ``r1.exam.analyze._b2_summary_v2`` (format of ``a2cd540c``), so the
template is tested against the code's own output shape, not a hand-written copy of it."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

from r1.exam import analyze as A

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('b2_stop6_report', ROOT / 'r1/scripts/b2_stop6_report.py')
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

NODES = ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere']
SEEDS = [9011, 9012, 9013, 9014]
AUDIT = list(range(9201, 9211))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=True))
    return p


def final(node, seed, base):
    metrics = [base + 0.001 * ((seed + node.__len__() + i) % 7) for i in range(10)]
    return {'instance_id': f'{node}__s{seed}', 'node': node, 'seeds': AUDIT, 'metrics': metrics,
            'final_y': sum(metrics) / 10}


def proposals(node, seed, k, shift):
    out = []
    for i in range(k):
        d = shift + 0.0004 * (((seed * 3 + i * 5 + len(node)) % 9) - 4)
        out.append({'proposal_id': f'{node}__s{seed}-p{i}', 'instance_id': f'{node}__s{seed}', 'node': node, 'mode': 'off',
                    'audit_seeds': AUDIT, 'delta_audit': d, 'se': 0.001, 'k': 10, 'sd': 0.003})
    return out


def manifest(cid, *, base, rerun, shift, gpu, invalid_per_root, trials_per_root):
    fa = [final(n, s, base) for n in NODES for s in SEEDS]
    sens = [final(n, s, base - 0.002) for n in NODES for s in SEEDS] if rerun else []
    roots = len(NODES) * len(SEEDS) * (2 if rerun else 1)
    on = {'pass': False, 'roots': len(sens), 'role': 'descriptive_never_changes_eligibility'} if rerun else None
    return {'label': 'EXAM', 'phase': 'b2', 'status': 'COMPLETE', 'execution_label': 'EVIDENCE', 'candidate': cid,
            'source_label': 'bartowski imatrix Q4_K_M', 'purpose': 'primary', 'mode': 'off', 'primary_mode': 'off',
            'rule_sha256': SHA, 'rule_version': 'x5_rule/v2', 'gpu_hours': gpu, 'final_audits': fa,
            'sensitivity_final_audits': sens, 'thinking_on_rerun': 'descriptive' if rerun else None,
            'audited_proposals': [p for n in NODES for s in SEEDS for p in proposals(n, s, 3, shift)],
            'd28_pass': True, 'd28_scope': 'thinking_off_roots_only', 'thinking_on_d28': on,
            'diagnostics': {'trials': trials_per_root * roots, 'evaluated': trials_per_root * roots,
                            'invalid': invalid_per_root * roots, 'duplicates': 5, 'noops': 2, 'parse_failed': 1,
                            'forecast_queries': 40, 'forecast_query_failed': 0}}


RULE, SHA = A.load_rule(ROOT / 'r1/exam/rules/x5_rule_v2.yaml')


def build(tmp, finalists=(('gemma4_31b', True),), gpus=None):
    tmp = Path(tmp)
    ms = []
    for i, (cid, rerun) in enumerate(finalists):
        ms.append(manifest(cid, base=0.90 - 0.01 * i, rerun=rerun, shift=-0.0009 + 0.0003 * i,
                           gpu=(gpus or {}).get(cid, 3.0 + i), invalid_per_root=2, trials_per_root=80))
    mpath = write(tmp / 'b2_manifests.json', {'label': 'EXAM', 'manifests': ms})
    b1rows = [{'candidate': 'scripted', 'role': 'anchor', 'mu_hat': -0.000587, 'd28_pass': True,
               'cluster_interval': {'lower': -0.0014, 'upper': 0.0002}}] + \
             [{'candidate': cid, 'role': 'candidate', 'mu_hat': -0.000891 + 0.0001 * i, 'd28_pass': True,
               'cluster_interval': {'lower': -0.0019, 'upper': 0.0001}} for i, (cid, _) in enumerate(finalists)]
    b1path = write(tmp / 'complete_batch_verifier.json', {'phase': 'b1', 'label': 'EXAM', 'rule_sha256': SHA,
                   'execution_label': 'EVIDENCE', 'finalists': [c for c, _ in finalists], 'rows': b1rows})
    modes = {cid: (['off', 'on'] if rerun else ['off']) for cid, rerun in finalists}
    grid = {'verified': True, 'finalists': [c for c, _ in finalists], 'nodes': NODES, 'seeds': SEEDS,
            'instances_per_node': len(SEEDS), 'audit_seeds': AUDIT, 'modes': modes,
            'gpu_hours': {m['candidate']: m['gpu_hours'] for m in ms}}
    analysis = A._b2_summary_v2(ms, RULE, SHA, grid=grid)
    analysis['execution_label'] = 'EVIDENCE'
    analysis['batch_verification'] = {'batch_state_sha256': 'a' * 64, 'batch_manifests_sha256': sha(mpath),
                                      'authorization_checkout_head': 'b' * 40, 'b1_analysis_sha256': sha(b1path),
                                      'grid': grid}
    apath = write(tmp / 'analysis.json', analysis)
    rows = []
    for cid, rerun in finalists:
        for mode in modes[cid]:
            for n in NODES:
                for s in SEEDS:
                    rows.append({'candidate': cid, 'mode': mode, 'node': n, 'instance_id': f'{n}__s{s}', 'trials': 80,
                                 'invalid': 2, 'classes': {'truncated': 1, 'model_output:M7': 1}, 'llm_calls': 80})
    ipath = write(tmp / 'invalid_trials.json', {'schema': R.SCHEMA_INVALID, 'label': 'EXAM', 'phase': 'b2',
                                                'batch_manifests_sha256': sha(mpath), 'rows': rows})
    return apath, mpath, ipath, b1path


def run(paths, out):
    a, m, i, b = paths
    R.main(['render', '--analysis', str(a), '--manifests', str(m), '--invalid-trials', str(i), '--b1-analysis', str(b),
            '--out', str(out)])
    return Path(out).read_text()


def test_single_finalist_renders_all_sections(tmp_path):
    text = run(build(tmp_path), tmp_path / 'r.md')
    for h in ('## 1. Finalist and rule pick', '## 2. B2 final audited Y', '## 3. Audited mean increment',
              '## 4. D28', '## 5. Invalid trials', '## 6. Thinking-on rerun', '## 8. For the author'):
        assert h in text
    assert '**`gemma4_31b`**' in text
    assert 'is the rule pick whatever its B2 score' in text and 'no second proposer among the finalists' in text
    assert '`truncated`' in text and '`model_output:M7`' in text
    assert 'below the scripted anchor' in text     # -0.000891 vs -0.000587
    assert 'never enters the ranking' in text


def test_numbers_are_recomputed(tmp_path):
    paths = build(tmp_path)
    text = run(paths, tmp_path / 'r.md')
    ms = json.loads(paths[1].read_text())['manifests']
    ys = [a['final_y'] for a in ms[0]['final_audits'] if a['node'] == 'digits_mlp']
    assert f'| `gemma4_31b` | `digits_mlp` | 4 | {sum(ys) / len(ys):.6f} |' in text
    ap = [p for p in ms[0]['audited_proposals'] if p['node'] == 'openml_credit_approval']
    b = A.bootstrap_mean(ap, field='delta_audit', rule=RULE)
    assert f"| `gemma4_31b` | `openml_credit_approval` | {len(ap)} | {b['mean']:+.6f} | [{b['lower']:+.6f}, {b['upper']:+.6f}] |" in text
    d = -0.000891 - (-0.000587)
    assert f'{d:+.6f}' in text
    # invalid table: off mode 12 roots x 80 trials, 24 invalid
    assert '| `gemma4_31b` | off | 960 | 24 | 12 | 12 |' in text
    assert '| `gemma4_31b` | on | 960 | 24 | 12 | 12 |' in text


def test_t_interval_matches_scipy():
    m, lo, hi, n = R.t_interval([1.0, 2.0, 3.0, 4.0])
    assert n == 4 and m == 2.5
    assert math.isclose(hi - m, 3.182446305284263 * math.sqrt(5 / 3) / 2, rel_tol=1e-12)


def test_two_finalists_rank_and_no_single_finalist_sentence(tmp_path):
    paths = build(tmp_path, finalists=(('gemma4_31b', True), ('qwen36_27b', False)))
    text = run(paths, tmp_path / 'r.md')
    assert 'whatever its B2 score' not in text
    assert text.index('| 1 | `gemma4_31b`') < text.index('| 2 | `qwen36_27b`')


def _tamper(tmp_path, which, fn, match):
    paths = build(tmp_path)
    p = paths[which]
    obj = json.loads(p.read_text()); fn(obj); p.write_text(json.dumps(obj))
    if which == 1:   # keep the analysis bound to the tampered manifests so that only the content check can fire
        a = json.loads(paths[0].read_text()); a['batch_verification']['batch_manifests_sha256'] = sha(p)
        paths[0].write_text(json.dumps(a))
        i = json.loads(paths[2].read_text()); i['batch_manifests_sha256'] = sha(p); paths[2].write_text(json.dumps(i))
    with pytest.raises(R.ReportError, match=match):
        run(paths, tmp_path / 'r.md')


@pytest.mark.parametrize('which,fn,match', [
    (0, lambda a: a.update(execution_label='DRYRUN'), 'not an EVIDENCE B2 analysis'),
    (0, lambda a: a['batch_verification']['grid'].update(verified=False), 'grid is not verified'),
    (0, lambda a: a['batch_verification'].update(batch_manifests_sha256='0' * 64), 'b2_manifests.json is not the file'),
    (0, lambda a: a['batch_verification'].update(b1_analysis_sha256='0' * 64), 'B1 analysis is not the file'),
    (0, lambda a: a['rows'][0].update(final_y=a['rows'][0]['final_y'] + 1e-9), 'analysis final_y differs'),
    (0, lambda a: a['rows'][0].update(gpu_hours=9.9), 'GPU-h differs'),
    (0, lambda a: a['selection'].update(rule_top='other'), 'rule_top differs'),
    (0, lambda a: a['thinking_on_descriptive'][0].update(final_y=0.5), 'thinking-on descriptive rows differ'),
    (0, lambda a: a.update(thinking_on_descriptive=[]), 'thinking-on descriptive rows differ'),
    (1, lambda m: m['manifests'][0]['final_audits'][0]['metrics'].__setitem__(0, 9.0), 'final_y differs from the mean'),
    (1, lambda m: m['manifests'][0]['final_audits'].pop(), 'final audits do not cover the grid'),
    (1, lambda m: m['manifests'][0].update(sensitivity_final_audits=[]), 'rerun presence differs'),
    (1, lambda m: m['manifests'][0]['diagnostics'].update(invalid=1), 'totals of gemma4_31b differ'),
    (1, lambda m: m['manifests'][0].update(candidate='x'), 'manifests differ from the verified finalists'),
    (2, lambda i: i['rows'].pop(), 'do not cover exactly the verified grid'),
    (2, lambda i: i['rows'].append(dict(i['rows'][0])), 'do not cover exactly the verified grid'),
    (2, lambda i: i['rows'][0]['classes'].update(truncated=5), 'do not add up'),
    (2, lambda i: i.update(schema='other'), 'not a b2_invalid_trials/v1 file'),
    (3, lambda b: b.update(finalists=['x']), 'B1 analysis is not the file'),
])
def test_refusals(tmp_path, which, fn, match):
    _tamper(tmp_path, which, fn, match)


def test_b1_without_scripted_anchor_refused(tmp_path):
    paths = build(tmp_path)
    b = json.loads(paths[3].read_text()); b['rows'] = [r for r in b['rows'] if r['candidate'] != 'scripted']
    paths[3].write_text(json.dumps(b))
    a = json.loads(paths[0].read_text()); a['batch_verification']['b1_analysis_sha256'] = sha(paths[3])
    paths[0].write_text(json.dumps(a))
    with pytest.raises(R.ReportError, match='no scripted anchor row'):
        run(paths, tmp_path / 'r.md')


# ---------------------------------------------------------------------------------------- derive-invalid

def _root(d, trials, journal, diag_invalid=None, rejected=None):
    d.mkdir(parents=True, exist_ok=True)
    (d / 'root_trials.jsonl').write_text(''.join(json.dumps(t) + '\n' for t in trials))
    (d / 'b1_proposals.jsonl').write_text(''.join(json.dumps(j) + '\n' for j in journal))
    inv = sum(t['decision'] == 'failed_invalid' for t in trials)
    write(d / 'campaign_manifest.json', {'diagnostics': {'invalid': inv if diag_invalid is None else diag_invalid,
                                                         'trials': len(trials)},
                                         'proposal_journal': {'rejected_by_check': rejected if rejected is not None else {}},
                                         'compute_budget': {'llm_calls': len(journal)}})


def _batch(tmp, *, tamper=None):
    paths = build(tmp)
    batch = tmp
    a = json.loads(paths[0].read_text())
    for mode in ('off', 'on'):
        for n in NODES:
            for s in SEEDS:
                tid = lambda k: f'{n}__s{s}-trial-{k:03d}'
                trials = [{'trial_id': tid(1), 'decision': 'kept'}, {'trial_id': tid(2), 'decision': 'failed_invalid'},
                          {'trial_id': tid(3), 'decision': 'failed_invalid'}, {'trial_id': tid(4), 'decision': 'failed_invalid'},
                          {'trial_id': tid(5), 'decision': 'failed_invalid'}, {'trial_id': tid(6), 'decision': 'discarded'}]
                journal = [{'trial_id': tid(1), 'check': 'passed'},
                           {'trial_id': tid(2), 'check': 'not_applicable', 'truncated': True},
                           {'trial_id': tid(3), 'check': 'd25_inactive_key'},                  # revised, then rejected:
                           {'trial_id': tid(3), 'check': 'rejected', 'rejection': {'check': 'M7'}},
                           {'trial_id': tid(4), 'check': 'not_applicable', 'context_overflow': True},
                           {'trial_id': tid(6), 'check': 'passed'}]                           # trial 5: no journal row
                _root(batch / 'gemma4_31b' / 'b2' / mode / f'{n}__s{s}', trials, journal, rejected={'M7': 1})
    if tamper:
        tamper(batch)
    return batch, paths


def test_derive_invalid_classifies_and_matches_render(tmp_path):
    batch, paths = _batch(tmp_path)
    out = R.derive_invalid(batch, paths[0])
    r0 = out['rows'][0]
    assert r0['invalid'] == 4 and r0['trials'] == 6 and r0['llm_calls'] == 6
    assert r0['classes'] == {'context_overflow': 1, 'model_output:M7': 1, 'other_invalid': 1, 'truncated': 1}
    assert len(out['rows']) == 24 and out['batch_manifests_sha256'] == sha(paths[1])


def test_derive_invalid_refuses_disagreeing_root(tmp_path):
    def bad(batch):
        d = batch / 'gemma4_31b' / 'b2' / 'off' / 'digits_mlp__s9011'
        m = json.loads((d / 'campaign_manifest.json').read_text()); m['diagnostics']['invalid'] = 3
        (d / 'campaign_manifest.json').write_text(json.dumps(m))
    batch, paths = _batch(tmp_path, tamper=bad)
    with pytest.raises(R.ReportError, match='differs from the root diagnostics'):
        R.derive_invalid(batch, paths[0])


def test_derive_invalid_refuses_journal_summary_mismatch(tmp_path):
    def bad(batch):
        d = batch / 'gemma4_31b' / 'b2' / 'on' / 'openml_ionosphere__s9014'
        m = json.loads((d / 'campaign_manifest.json').read_text()); m['proposal_journal']['rejected_by_check'] = {'M8': 1}
        (d / 'campaign_manifest.json').write_text(json.dumps(m))
    batch, paths = _batch(tmp_path, tamper=bad)
    with pytest.raises(R.ReportError, match='model-output rejections differ'):
        R.derive_invalid(batch, paths[0])


def test_b1_finalists_mismatch_refused_even_when_bound(tmp_path):
    paths = build(tmp_path)
    b = json.loads(paths[3].read_text()); b['finalists'] = ['qwen36_27b']; paths[3].write_text(json.dumps(b))
    a = json.loads(paths[0].read_text()); a['batch_verification']['b1_analysis_sha256'] = sha(paths[3])
    paths[0].write_text(json.dumps(a))
    with pytest.raises(R.ReportError, match='B1 finalists differ'):
        run(paths, tmp_path / 'r.md')


def test_rule_bytes_must_match_analysis_sha(tmp_path):
    paths = build(tmp_path)
    a = json.loads(paths[0].read_text()); a['rule_sha256'] = '0' * 64; paths[0].write_text(json.dumps(a))
    b = json.loads(paths[3].read_text()); b['rule_sha256'] = '0' * 64; paths[3].write_text(json.dumps(b))
    a['batch_verification']['b1_analysis_sha256'] = sha(paths[3]); paths[0].write_text(json.dumps(a))
    with pytest.raises(R.ReportError, match='rule file differs'):
        run(paths, tmp_path / 'r.md')
