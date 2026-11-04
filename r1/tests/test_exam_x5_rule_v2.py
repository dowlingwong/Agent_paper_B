"""M2 (MAC_LOCAL_RUNBOOK_20261104): x5_rule_v2, its analyze/runner code, the B1/B2 harness binding and
the template-repair carry-through (R1-EXAM-A1-M1-REQUIREMENTS (1)).  No inference, no GPU; the
cache_prompt test uses a stand-in llama-server on 127.0.0.1.  ENGINEERING_ONLY; AI-assisted (Claude).
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest
import yaml
from r1.exam import analyze
from r1.exam.analyze import RULE, RULE_V2, b1_summary, b2_summary, choose_finalists, load_rule, thinking_off_capable
from r1.exam.campaign import write_json
from r1.exam.guards import digest_file
from r1.exam.runtime import DEFAULT_CONFIG, PreparationStop, load_config

REPO = Path(__file__).resolve().parents[2]
CONFIGS = REPO / 'r1/scripts/configs'
A3FEDBB = 'a3fedbbd44309b3fdf99d853ad841b9ec2c299e2'
V1_SHA = '0665903b276f34eca4cd4d03ac483192cd3ef3b41c24d188e2dd103d65423b6e'
REGISTRY = yaml.safe_load((REPO / 'r1/exam/registry.yaml').read_text())
REPAIRED = ('olmo31_32b', 'devstral_small2_24b', 'ministral3_14b')


def v2():
    return load_rule(RULE_V2)


# ---------------------------------------------------------------- the rule file
def test_v2_mode_fields_are_strings_and_always_on_skip():
    raw = yaml.safe_load(RULE_V2.read_text())
    for value in (raw['ranking_mode'], raw['thinking_mode']['primary'], raw['thinking_mode']['b2_mode'],
                  raw['selection']['mode']):
        assert isinstance(value, str) and value == 'off'
    assert raw['thinking_mode']['always_on_in_b1'] == 'skip'          # R1-EXAM-ALWAYS-ON-SKIP
    assert raw['thinking_mode']['b1_sensitivity']['node'] == 'openml_credit_approval'
    assert raw['version'] == 'x5_rule/v2' and raw['supersedes'] == 'x5_rule/v1'


def test_v2_loads_only_with_its_sha(tmp_path):
    sha = (Path(str(RULE_V2) + '.sha256').read_text().split()[0])
    assert sha == hashlib.sha256(RULE_V2.read_bytes()).hexdigest()
    rule, got = load_rule(RULE_V2, sha)
    assert got == sha and rule['version'] == 'x5_rule/v2'
    with pytest.raises(ValueError, match='digest mismatch'):
        load_rule(RULE_V2, V1_SHA)
    with pytest.raises(ValueError, match='digest mismatch'):
        load_rule(RULE_V2, 'not-a-sha')
    changed = tmp_path / 'x5_rule_v2.yaml'
    changed.write_bytes(RULE_V2.read_bytes() + b'# edit\n')
    with pytest.raises(ValueError, match='digest mismatch'):
        load_rule(changed, sha)


def test_v2_with_bare_off_is_refused(tmp_path):
    bad = tmp_path / 'bad.yaml'
    bad.write_text(RULE_V2.read_text().replace('ranking_mode: "off"', 'ranking_mode: off'))
    assert yaml.safe_load(bad.read_text())['ranking_mode'] is False      # the YAML trap the quotes avoid
    with pytest.raises(ValueError, match='must be the string "off"'):
        load_rule(bad, hashlib.sha256(bad.read_bytes()).hexdigest())


def test_v1_unchanged_still_loadable_and_still_default():
    assert RULE.name == 'x5_rule_v1.yaml' and load_rule.__defaults__[0] == RULE
    assert digest_file(RULE) == V1_SHA
    rule, sha = load_rule()
    assert sha == V1_SHA and rule['version'] == 'x5_rule/v1'
    portal = json.loads(DEFAULT_CONFIG.read_text())
    assert portal['rule'] == 'r1/exam/rules/x5_rule_v1.yaml' and portal['rule_sha256'] == V1_SHA


def test_registry_thinking_capability_matches_rule_comment():
    rows = [r for r in REGISTRY['candidates'] if r['role'] == 'candidate']
    capable = [r['id'] for r in rows if thinking_off_capable(r['thinking_policy'])]
    always = [r['id'] for r in rows if r['thinking_policy']['mode'] == 'always_on']
    assert len(rows) == 20 and len(capable) == 16 and len(always) == 4
    assert not thinking_off_capable({'mode': 'off', 'switchable': True, 'off_switch': False})
    assert not thinking_off_capable(None)


# ---------------------------------------------------------------- B1 analysis under v2
def _registry(tmp_path, rows):
    path = tmp_path / 'registry.yaml'
    path.write_text(json.dumps({'software_anchors': [], 'candidates': rows}))
    return path


def _obs(node, mode, value, i):
    return {'instance_id': f'{node}__s{9001 + i}', 'node': node, 'mode': mode, 'delta_audit': value,
            'candidate_metrics': [value] * 4, 'incumbent_metrics': [0] * 4, 'audit_seeds': list(range(9101, 9105))}


def _b1_manifest(registry, sha, cid, order, family, observations, primary_mode='off'):
    return {'label': 'EXAM', 'phase': 'b1', 'status': 'COMPLETE', 'candidate': cid, 'family': family, 'role': 'candidate',
            'registry_order': order, 'rule_sha256': sha, 'registry_path': str(registry),
            'registry_sha256': digest_file(registry), 'primary_mode': primary_mode, 'stage_a_pass': True,
            'd28_pass': True, 'audited_proposals': observations}


SWITCH = {'mode': 'off', 'switchable': True, 'off_switch': True}
NONTHINK = {'mode': 'off', 'switchable': False, 'off_switch': False}
ALWAYS = {'mode': 'always_on', 'switchable': False, 'off_switch': False, 'budget': 2048}


def test_thinking_on_with_higher_y_never_wins_b1(tmp_path):
    _, sha = v2()
    reg = _registry(tmp_path, [{'id': 'a', 'role': 'candidate', 'family': 'fa', 'thinking_policy': SWITCH},
                               {'id': 'b', 'role': 'candidate', 'family': 'fb', 'thinking_policy': NONTHINK}])
    node = 'openml_credit_approval'
    a = [_obs('digits_mlp', 'off', .01, i) for i in range(4)] + [_obs(node, 'on', .9, i) for i in range(4)]
    b = [_obs('digits_mlp', 'off', .02, i) for i in range(4)]
    result = b1_summary([_b1_manifest(reg, sha, 'a', 0, 'fa', a), _b1_manifest(reg, sha, 'b', 1, 'fb', b)],
                        rule_path=RULE_V2)
    rows = {r['candidate']: r for r in result['rows']}
    assert rows['a']['mu_hat'] == pytest.approx(.01) and rows['b']['mu_hat'] == pytest.approx(.02)
    assert rows['a']['b2_thinking_mode'] == 'off'                     # v1 would pick 'on' here
    assert rows['a']['thinking_on_sensitivity']['means_by_mode']['on'] == pytest.approx(.9)
    assert result['finalists'][0] == 'b'
    # under v1 the same thinking-on sensitivity would have chosen B2 mode 'on'
    _, sha1 = load_rule()
    v1 = b1_summary([_b1_manifest(reg, sha1, 'a', 0, 'fa', a)])
    assert v1['rows'][0]['b2_thinking_mode'] == 'on'


def test_always_on_model_is_never_a_finalist(tmp_path):
    rule, sha = v2()
    reg = _registry(tmp_path, [{'id': 'think', 'role': 'candidate', 'family': 'ft', 'thinking_policy': ALWAYS},
                               {'id': 'b', 'role': 'candidate', 'family': 'fb', 'thinking_policy': NONTHINK}])
    # skip: an always-on model must not even have a B1 manifest
    with pytest.raises(ValueError, match='always_on_in_b1 is skip'):
        b1_summary([_b1_manifest(reg, sha, 'think', 0, 'ft', [_obs('digits_mlp', 'always_on', 5., i) for i in range(4)],
                                 primary_mode='always_on')], rule_path=RULE_V2)
    # finalist choice: even a forged row with a huge mu_hat is not ranked
    rows = [{'candidate': 'think', 'role': 'candidate', 'family': 'ft', 'stage_a_pass': True, 'd28_pass': True,
             'mu_hat': 100., 'registry_order': 0, 'thinking_off_eligible': False, 'mu_hat_mode': 'off'}]
    rows += [{'candidate': f'c{i}', 'role': 'candidate', 'family': f'f{i}', 'stage_a_pass': True, 'd28_pass': True,
              'mu_hat': i / 10, 'registry_order': i + 1, 'thinking_off_eligible': True, 'mu_hat_mode': 'off'}
             for i in range(6)]
    finalists = choose_finalists(rows, rule)
    assert 'think' not in finalists and finalists == ['c5', 'c4', 'c3', 'c2', 'c1']
    # a row without the v2 eligibility marks (e.g. a v1 row) is not ranked under v2
    assert choose_finalists([{**rows[1], 'thinking_off_eligible': None}], rule) == []


def test_v2_b1_refuses_non_off_primary_for_capable_model(tmp_path):
    _, sha = v2()
    reg = _registry(tmp_path, [{'id': 'a', 'role': 'candidate', 'family': 'fa', 'thinking_policy': SWITCH}])
    with pytest.raises(ValueError, match='primary mode must be off'):
        b1_summary([_b1_manifest(reg, sha, 'a', 0, 'fa', [_obs('digits_mlp', 'on', .1, 0)], primary_mode='on')],
                   rule_path=RULE_V2)


# ---------------------------------------------------------------- B2 analysis under v2
def _b2(sha, cid, y, gpu, mode='off', purpose='primary', rerun=None):
    return {'label': 'EXAM', 'phase': 'b2', 'status': 'COMPLETE', 'candidate': cid, 'source_label': 'fixture',
            'rule_sha256': sha, 'final_audits': [{'final_y': y, 'metrics': [y] * 10, 'seeds': list(range(9201, 9211))}],
            'gpu_hours': gpu, 'mode': mode, 'purpose': purpose,
            'sensitivity_final_audits': [{'final_y': v, 'metrics': [v] * 10, 'seeds': list(range(9201, 9211))} for v in (rerun or [])]}


def test_b2_thinking_on_never_wins_and_is_descriptive():
    _, sha = v2()
    out = b2_summary([_b2(sha, 'a', .5, 1., rerun=[.95]), _b2(sha, 'b', .6, 1.)], rule_path=RULE_V2)
    assert [r['candidate'] for r in out['rows']] == ['b', 'a'] and out['selection']['rule_top'] == 'b'
    assert out['thinking_on_descriptive'][0]['candidate'] == 'a' and out['thinking_on_descriptive'][0]['final_y'] == .95
    assert all(r['mode'] == 'off' for r in out['rows'])


def test_b2_refuses_a_non_off_primary_manifest():
    _, sha = v2()
    for mode in ('on', 'always_on', False, None):
        with pytest.raises(ValueError, match='refuses a primary B2 manifest'):
            b2_summary([_b2(sha, 'a', .99, 1., mode=mode), _b2(sha, 'b', .6, 1.)], rule_path=RULE_V2)
    with pytest.raises(ValueError, match='rule hash'):
        b2_summary([_b2(V1_SHA, 'b', .6, 1.)], rule_path=RULE_V2)


def test_b2_ties_go_to_lower_gpu_hours():
    _, sha = v2()
    out = b2_summary([_b2(sha, 'slow', .7, 3.), _b2(sha, 'fast', .7, 1.), _b2(sha, 'unknown', .7, None)], rule_path=RULE_V2)
    assert [r['candidate'] for r in out['rows']] == ['fast', 'slow', 'unknown']


def test_b2_without_rule_or_under_v1_is_unchanged():
    m = _b2(V1_SHA, 'x', .7, 1., mode='on')
    m.pop('rule_sha256')
    old = b2_summary([m])
    assert old['rows'][0]['mode'] == 'on' and 'thinking_on_descriptive' not in old
    assert b2_summary([m], rule_path=RULE) == old


# ---------------------------------------------------------------- runner: Stage A pass set
def _stage_table(path, rows, label='ENGINEERING_ONLY'):
    write_json(path, {'label': label, 'rows': rows})
    return path


def _amend_cfg(tmp_path, stage_rows, amend_rows):
    stage = _stage_table(tmp_path / 'stage.json', stage_rows)
    amend = _stage_table(tmp_path / 'amend.json', amend_rows)
    acc = tmp_path / 'acceptance.md'
    acc.write_text('operator O1 acceptance of t7j10 (fixture)\n')
    return {'stage_a_table': str(stage), 'stage_a_table_sha256': digest_file(stage),
            'stage_a_amendment_table': str(amend), 'stage_a_amendment_table_sha256': digest_file(amend),
            'stage_a_amendment_acceptance': str(acc), 'stage_a_amendment_acceptance_sha256': digest_file(acc)}


def test_v2_pass_set_is_t7h8_union_accepted_amendment(tmp_path):
    from r1.scripts.exam_runner import stage_a_pass_set
    cfg = _amend_cfg(tmp_path,
                     [{'candidate': 'qwen38_27b', 'passed': True}, {'candidate': 'gemma4_31b', 'passed': False},
                      {'candidate': 'qwen25_coder_7b', 'passed': True}],
                     [{'candidate': 'gemma4_31b', 'passed': True}, {'candidate': 'olmo31_32b', 'passed': False},
                      {'candidate': 'qwen25_coder_7b', 'passed': True, 'm1': True}])
    got = stage_a_pass_set(cfg, {'qwen38_27b', 'gemma4_31b', 'olmo31_32b'}, v2=True)
    assert set(got) == {'qwen38_27b', 'gemma4_31b', 'qwen25_coder_7b'}
    assert got['gemma4_31b']['stage_a_pass_source'] == 'a1_amendment_measurement'
    assert got['qwen25_coder_7b']['stage_a_pass_source'] == 'stage_a_table' and 'm1' not in got['qwen25_coder_7b']
    # v1 reads only the Stage A table, unchanged
    assert set(stage_a_pass_set(cfg, {'gemma4_31b'}, v2=False)) == {'qwen38_27b', 'qwen25_coder_7b'}


@pytest.mark.parametrize('key', ['stage_a_amendment_table', 'stage_a_amendment_table_sha256',
                                 'stage_a_amendment_acceptance', 'stage_a_amendment_acceptance_sha256'])
def test_v2_pass_set_refuses_without_accepted_amendment(tmp_path, key):
    from r1.scripts.exam_runner import stage_a_pass_set
    cfg = _amend_cfg(tmp_path, [{'candidate': 'qwen38_27b', 'passed': True}], [{'candidate': 'gemma4_31b', 'passed': True}])
    cfg[key] = 'TODO_OPERATOR_O1_ACCEPTANCE' if 'sha' not in key else None
    with pytest.raises(PreparationStop, match='operator-accepted A1 amendment'):
        stage_a_pass_set(cfg, {'gemma4_31b'}, v2=True)


def test_v2_pass_set_refuses_changed_amendment_or_acceptance(tmp_path):
    from r1.scripts.exam_runner import stage_a_pass_set
    cfg = _amend_cfg(tmp_path, [{'candidate': 'qwen38_27b', 'passed': True}], [{'candidate': 'gemma4_31b', 'passed': True}])
    Path(cfg['stage_a_amendment_acceptance']).write_text('edited\n')
    with pytest.raises(PreparationStop, match='acceptance'):
        stage_a_pass_set(cfg, {'gemma4_31b'}, v2=True)
    cfg = _amend_cfg(tmp_path, [{'candidate': 'qwen38_27b', 'passed': True}], [{'candidate': 'gemma4_31b', 'passed': True}])
    _stage_table(Path(cfg['stage_a_amendment_table']), [{'candidate': 'gemma4_31b', 'passed': True}, {'candidate': 'x', 'passed': True}])
    with pytest.raises(PreparationStop, match='amendment table digest'):
        stage_a_pass_set(cfg, {'gemma4_31b'}, v2=True)


# ---------------------------------------------------------------- runner: B1/B2 mode logic under v2
def _spec(cid, policy, role='candidate', repair=None):
    s = {'id': cid, 'role': role, 'family': 'f' + cid, 'thinking_policy': dict(policy)}
    if repair: s['template_repair'] = repair
    return s


class FakeRunner:
    """Exam runner stand-in: records each (candidate, mode, nodes) the B1/B2 body asks for."""

    def __init__(self, tmp_path, specs, cfg, rule, sha):
        self.specs = specs; self.cfg = cfg; self.rule = rule; self.rule_sha = sha
        self.state = {'completed': {}, 'anchor_gate': {'fixture': True}}
        self.service = None; self.out = tmp_path; self.registry_path = tmp_path / 'registry.json'
        self.registry_path.write_text('{}')
        self.served = []; self.roots = []

    def spec_order(self, selected=None):
        return [copy.deepcopy(s) for s in self.specs if not selected or s['id'] in selected]

    def server(self, spec, mode, ctx):
        self.served.append((spec['id'], mode, (spec.get('template_repair') or {}).get('sha256')))

    def root(self, spec, phase, node, seed, mode, **kwargs):
        self.roots.append((spec['id'], mode, node))
        return {'mode': mode, 'node': node, 'instance_seed': seed, 'audited_proposals': [],
                'diagnostics': {}, 'd28': {'nodes': {node: {'pass': True}}},
                'final_audits': [{'final_y': .5, 'metrics': [.5] * 10, 'seeds': list(range(9201, 9211))}] if phase == 'b2' else [],
                'cache_prompt': {'cache_prompt': False, 'all_false': True}}

    def save(self):
        pass


def _runner_cfg(tmp_path, specs, stage_ids, amend_ids=(), extra=None):
    cfg = _amend_cfg(tmp_path, [{'candidate': c, 'passed': True} for c in stage_ids],
                     [{'candidate': c, 'passed': True} for c in amend_ids])
    cfg.update(nodes=['digits_mlp', 'openml_credit_approval', 'openml_ionosphere'], instance_seeds=[9001],
               b2_instances_per_node=1, server={'build': 'fake'}, dryrun=True, cache_prompt=False, harness_commit=A3FEDBB,
               template_repairs={s['id']: s['template_repair']['sha256'] for s in specs if s.get('template_repair')})
    cfg.update(extra or {})
    return cfg


def test_runner_v2_b1_skips_always_on_and_runs_off_primary(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('sw', SWITCH), _spec('nt', NONTHINK), _spec('think', ALWAYS)]
    runner = FakeRunner(tmp_path, specs, _runner_cfg(tmp_path, specs, ['sw', 'nt', 'think']), rule, sha)
    _evidence_unreviewed(runner, 'b1', None, False)
    assert runner.state['b1_skipped_always_on'] == ['think']
    assert 'think' not in {s[0] for s in runner.served}
    assert [(c, m) for c, m, _ in runner.served] == [('sw', 'off'), ('sw', 'on'), ('nt', 'off')]
    on_nodes = {n for c, m, n in runner.roots if m == 'on'}
    assert on_nodes == {rule['thinking_mode']['b1_sensitivity']['node']}
    m = json.loads((tmp_path / 'sw/b1_manifest.json').read_text())
    assert m['primary_mode'] == 'off' and m['thinking_on_sensitivity'] == 'descriptive'
    assert m['rule_version'] == 'x5_rule/v2' and m['cache_prompt'] is False and m['harness_commit'] == A3FEDBB


def test_runner_v2_b2_off_for_every_finalist_top3_rerun_descriptive(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec(f's{i}', SWITCH) for i in range(4)] + [_spec('nt', NONTHINK)]
    finalists = ['s0', 's1', 's2', 's3', 'nt']
    screen = tmp_path / 'b1.json'
    write_json(screen, {'rule_sha256': sha, 'finalists': finalists,
                        'rows': [{'candidate': c, 'b2_thinking_mode': 'off'} for c in finalists]})
    cfg = _runner_cfg(tmp_path, specs, finalists, extra={'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen)})
    runner = FakeRunner(tmp_path, specs, cfg, rule, sha)
    _evidence_unreviewed(runner, 'b2', None, False)
    by = {}
    for c, m, _ in runner.served: by.setdefault(c, []).append(m)
    assert by == {'s0': ['off', 'on'], 's1': ['off', 'on'], 's2': ['off', 'on'], 's3': ['off'], 'nt': ['off']}
    m0 = json.loads((tmp_path / 's0/b2_manifest.json').read_text())
    assert m0['mode'] == 'off' and m0['purpose'] == 'primary' and m0['thinking_on_rerun'] == 'descriptive'
    assert m0['final_audits'] and m0['sensitivity_final_audits']      # rerun audits stay out of the primary Y
    # an analysis that assigned a non-off B2 mode is refused under v2
    write_json(screen, {'rule_sha256': sha, 'finalists': finalists,
                        'rows': [{'candidate': c, 'b2_thinking_mode': 'on' if c == 's0' else 'off'} for c in finalists]})
    runner.cfg['b1_analysis_sha256'] = digest_file(screen)
    with pytest.raises(PreparationStop, match='B2 mode off'):
        _evidence_unreviewed(runner, 'b2', None, False)


def test_runner_v2_refuses_cache_prompt_harness_and_root_evidence(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('nt', NONTHINK)]
    for extra, msg in (({'cache_prompt': None}, 'cache_prompt must be explicitly false'),
                       ({'dryrun': False, 'harness_commit': '897d83c8efa364ec2fdd37288241cc42e01d7274'}, 'harness pin must be a3fedbb')):
        runner = FakeRunner(tmp_path, specs, _runner_cfg(tmp_path, specs, ['nt'], extra=extra), rule, sha)
        with pytest.raises(PreparationStop, match=msg):
            _evidence_unreviewed(runner, 'b1', None, False)
    runner = FakeRunner(tmp_path, specs, _runner_cfg(tmp_path, specs, ['nt']), rule, sha)
    base_root = runner.root
    runner.root = lambda *a, **k: {**base_root(*a, **k), 'cache_prompt': None}
    with pytest.raises(PreparationStop, match='cache_prompt false'):
        _evidence_unreviewed(runner, 'b1', None, False)


def test_v1_runner_path_unchanged_without_v2_rule(tmp_path):
    """The v1 B2 path still follows the B1 analysis' mode (existing behaviour) when the rule is v1."""
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = load_rule()
    specs = [_spec('sw', SWITCH)]
    screen = tmp_path / 'b1.json'
    write_json(screen, {'rule_sha256': sha, 'finalists': ['sw'], 'rows': [{'candidate': 'sw', 'b2_thinking_mode': 'on'}]})
    cfg = _runner_cfg(tmp_path, specs, ['sw'], extra={'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen)})
    runner = FakeRunner(tmp_path, specs, cfg, rule, sha)
    _evidence_unreviewed(runner, 'b2', None, False)
    assert [m for _, m, _ in runner.served] == ['on', 'off']


def test_d22_guard_unchanged_under_v2(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('nt', NONTHINK), _spec('qwen25_coder_7b', NONTHINK, role='anchor')]
    screen = tmp_path / 'b1.json'
    write_json(screen, {'rule_sha256': sha, 'finalists': ['nt'], 'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]})
    cfg = _runner_cfg(tmp_path, specs, ['nt', 'qwen25_coder_7b'],
                      extra={'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen), 'free_sensitivity': True,
                             'd22_pick': 'm2_fixture_pick_not_in_plan', 'schema_sensitivity_node': 'openml_credit_approval'})
    with pytest.raises(RuntimeError, match='D22 pick must be author-recorded'):
        _evidence_unreviewed(FakeRunner(tmp_path, specs, cfg, rule, sha), 'b2', None, False)


# ---------------------------------------------------------------- template repair carried into B1/B2
def _repaired_specs():
    return {s['id']: s for s in REGISTRY['candidates'] if s.get('template_repair')}


def test_registry_repairs_are_the_three_pinned_files():
    reps = _repaired_specs()
    assert set(reps) == set(REPAIRED)
    for cid, s in reps.items():
        path = REPO / s['template_repair']['file']
        assert digest_file(path) == s['template_repair']['sha256']


class _Captured(Exception):
    pass


def _served_args(monkeypatch, tmp_path, spec, phase, mode='off'):
    """Drive the real ExamRunner.server -> _server path up to the llama-server construction."""
    from r1.exam import runtime
    captured = {}

    class Instance:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs)
            raise _Captured()
    monkeypatch.setattr(runtime.lsi, 'LlamaServerInstance', Instance)
    monkeypatch.setattr(runtime, 'host_check', lambda cfg, out: None)
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': True, 'server': {'binary': 'x', 'start_timeout': 1}, 'gpu_uuid': 'GPU-DRYRUN'}
    runner.out = tmp_path; runner.state = {'phase': phase, 'execution_label': 'DRYRUN'}; runner.service = None
    monkeypatch.setattr(runner, 'validate_spec', lambda spec: {'version_line': 'fake'}, raising=False)
    with pytest.raises(PreparationStop):
        runner.server(copy.deepcopy(spec), mode, 32768)
    return captured


@pytest.mark.parametrize('phase', ['b1', 'b2'])
@pytest.mark.parametrize('cid', REPAIRED)
def test_b1_b2_server_serves_the_pinned_repair_template(monkeypatch, tmp_path, phase, cid):
    spec = copy.deepcopy(_repaired_specs()[cid])
    spec['runtime'] = {'model_path': str(tmp_path / 'm.gguf'), 'footprint_mib': 1}
    args = _served_args(monkeypatch, tmp_path, spec, phase)['extra_args']
    i = args.index('--chat-template-file')
    served = Path(args[i + 1])
    assert served == (REPO / spec['template_repair']['file']).resolve()
    assert digest_file(served) == spec['template_repair']['sha256']


@pytest.mark.parametrize('phase', ['b1', 'b2'])
def test_b1_b2_repair_digest_mismatch_is_a_stop(monkeypatch, tmp_path, phase):
    spec = copy.deepcopy(_repaired_specs()['olmo31_32b'])
    spec['runtime'] = {'model_path': str(tmp_path / 'm.gguf'), 'footprint_mib': 1}
    spec['template_repair']['sha256'] = '0' * 64
    from r1.exam import runtime
    monkeypatch.setattr(runtime, 'host_check', lambda cfg, out: None)
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': True, 'server': {'binary': 'x', 'start_timeout': 1}, 'gpu_uuid': 'GPU-DRYRUN'}
    runner.out = tmp_path; runner.state = {'phase': phase, 'execution_label': 'DRYRUN'}; runner.service = None
    monkeypatch.setattr(runner, 'validate_spec', lambda spec: {'version_line': 'fake'}, raising=False)
    with pytest.raises(PreparationStop, match='template repair digest mismatch'):
        runner.server(spec, 'off', 32768)


@pytest.mark.parametrize('phase', ['b1', 'b2'])
def test_b1_b2_unrepaired_model_gets_no_template_flag(monkeypatch, tmp_path, phase):
    spec = copy.deepcopy(next(s for s in REGISTRY['candidates'] if s['id'] == 'qwen38_27b'))
    spec['runtime'] = {'model_path': str(tmp_path / 'm.gguf'), 'footprint_mib': 1}
    assert '--chat-template-file' not in _served_args(monkeypatch, tmp_path, spec, phase)['extra_args']


@pytest.mark.parametrize('phase', ['b1', 'b2'])
def test_runner_passes_registry_repair_to_server_and_records_sha(tmp_path, phase):
    """The B1/B2 body hands each spec, template_repair included, to runner.server and records the sha."""
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    olmo = _repaired_specs()['olmo31_32b']
    specs = [_spec('olmo31_32b', olmo['thinking_policy'], repair=olmo['template_repair']), _spec('nt', NONTHINK)]
    extra = {}
    if phase == 'b2':
        screen = tmp_path / 'b1.json'
        write_json(screen, {'rule_sha256': sha, 'finalists': ['olmo31_32b', 'nt'],
                            'rows': [{'candidate': c, 'b2_thinking_mode': 'off'} for c in ('olmo31_32b', 'nt')]})
        extra = {'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen)}
    cfg = _runner_cfg(tmp_path, specs, ['nt'], amend_ids=['olmo31_32b'], extra=extra)
    runner = FakeRunner(tmp_path, specs, cfg, rule, sha)
    _evidence_unreviewed(runner, phase, None, False)
    assert ('olmo31_32b', 'off', olmo['template_repair']['sha256']) in runner.served
    assert ('nt', 'off', None) in runner.served
    m = json.loads((tmp_path / f'olmo31_32b/{phase}_manifest.json').read_text())
    assert m['template_repair'] == {'file': olmo['template_repair']['file'], 'sha256': olmo['template_repair']['sha256']}
    assert m['stage_a_pass_source'] == 'a1_amendment_measurement'
    assert json.loads((tmp_path / f'nt/{phase}_manifest.json').read_text())['template_repair'] is None
    # the config binds the repair shas; a differing binding is a STOP
    runner.cfg['template_repairs'] = {'olmo31_32b': '0' * 64}
    with pytest.raises(PreparationStop, match='template_repairs'):
        _evidence_unreviewed(runner, phase, None, False)


# ---------------------------------------------------------------- the v2 configs
@pytest.mark.parametrize('name', ['exam_b1_v2.json', 'exam_b2_v2.json'])
def test_v2_configs_bind_rule_harness_cache_and_repairs(name):
    path = CONFIGS / name
    cfg = load_config(path, allow_placeholders=True)
    assert cfg['rule'] == 'r1/exam/rules/x5_rule_v2.yaml'
    assert cfg['rule_sha256'] == digest_file(REPO / cfg['rule']) == Path(str(RULE_V2) + '.sha256').read_text().split()[0]
    load_rule(REPO / cfg['rule'], cfg['rule_sha256'])
    assert cfg['harness_commit'] == A3FEDBB and cfg['cache_prompt'] is False
    assert cfg['template_repairs'] == {cid: s['template_repair']['sha256'] for cid, s in _repaired_specs().items()}
    for key in ('stage_a_amendment_table', 'stage_a_amendment_table_sha256',
                'stage_a_amendment_acceptance', 'stage_a_amendment_acceptance_sha256'):
        assert key in cfg                       # explicit, sha-bound input; still a placeholder until O1 acceptance
    portal = json.loads(DEFAULT_CONFIG.read_text())
    assert {k: v for k, v in cfg.items() if k in portal and k not in (
        'comment', 'rule', 'rule_sha256', 'harness_commit', 'paper_commit', 'host', 'authorizations', 'cache_prompt',
        'd3_policy')} == {k: portal[k] for k in cfg if k in portal and k not in (
        'comment', 'rule', 'rule_sha256', 'harness_commit', 'paper_commit', 'host', 'authorizations', 'cache_prompt', 'd3_policy')}


# ---------------------------------------------------------------- harness binding: cache_prompt false on the wire
def _b1_harness_root():
    """The B1/B2 harness pin checkout: $AR_HARNESS_B1_ROOT, else the M2 worktree default; None if absent."""
    for cand in (os.environ.get('AR_HARNESS_B1_ROOT'), '/home/claude/wt/harness-a3fedbb',
                 str(REPO.parent / 'autoresearch_harness_a3fedbb')):
        if cand and (Path(cand) / 'src').is_dir():
            return Path(cand)
    return None


def _drive(tmp_path, harness):
    out = tmp_path / 'root'
    env = {k: v for k, v in os.environ.items() if k != 'LLAMACPP_CACHE_PROMPT'}
    env.update(AR_HARNESS_ROOT=str(harness), PYTHONPATH=str(REPO), PYTHONDONTWRITEBYTECODE='1')
    done = subprocess.run([sys.executable, str(REPO / 'r1/tests/exam_cache_prompt_driver.py'), str(out)],
                          cwd=REPO, env=env, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads((out / 'result.json').read_text())


def test_exam_campaign_request_manifest_and_llm_call_carry_cache_prompt_false(tmp_path):
    harness = _b1_harness_root()
    if harness is None:
        pytest.skip('harness a3fedbb checkout not found; set AR_HARNESS_B1_ROOT')
    head = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == A3FEDBB, f'B1/B2 harness pin must be {A3FEDBB}, found {head}'
    r = _drive(tmp_path, harness)
    assert r['harness']['commit'] == A3FEDBB
    assert r['requests'] and all(q['path'] == '/v1/chat/completions' for q in r['requests'])
    assert all(q['body']['cache_prompt'] is False for q in r['requests'])          # the request
    assert r['llm_call_events'] and all(e['cache_prompt'] is False for e in r['llm_call_events'])   # llm_call
    assert all(t['cache_prompt'] is False for t in r['trial_llm_calls'] if t)
    assert r['manifest_cache_prompt']['all_false'] is True and r['stop'] is None      # the manifest field
    assert r['manifest_cache_prompt']['llm_call_events'] == len(r['requests'])


def test_stage_a_harness_pin_does_not_send_cache_prompt_so_b1_evidence_stops(tmp_path):
    """Negative control: at the Stage A pin 897d83c the harness proposer sends no cache_prompt, and the
    root's manifest evidence refuses it (why B1/B2 bind a3fedbb)."""
    from r1.harness import harness_root
    harness = harness_root()
    head = subprocess.check_output(['git', '-C', str(harness), 'rev-parse', 'HEAD'], text=True).strip()
    if head != '897d83c8efa364ec2fdd37288241cc42e01d7274':
        pytest.skip(f'AR_HARNESS_ROOT is not the Stage A pin (found {head})')
    r = _drive(tmp_path, harness)
    assert r['requests'] and all('cache_prompt' not in q['body'] for q in r['requests'])
    assert r['manifest_cache_prompt'] is None and 'not explicitly false' in r['stop']
