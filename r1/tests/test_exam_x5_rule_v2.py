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
    sensitivity = raw['thinking_mode']['b1_sensitivity']
    assert (sensitivity['enabled'], sensitivity['mode'], sensitivity['instances'], sensitivity['role']) == (True, 'on', 4, 'descriptive_only')
    assert raw['eligibility']['d28_scope'] == 'thinking_off_only'
    assert raw['version'] == 'x5_rule/v2' and raw['supersedes'] == 'x5_rule/v1'


@pytest.mark.parametrize('field,value', [('enabled',False),('mode','off'),('instances',3),('role','eligibility')])
def test_v2_refuses_changed_sensitivity(tmp_path,field,value):
    raw = yaml.safe_load(RULE_V2.read_text())
    raw['thinking_mode']['b1_sensitivity'][field] = value
    path=tmp_path/'rule.yaml';path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError,match='descriptive thinking-on sensitivity'):
        load_rule(path, hashlib.sha256(path.read_bytes()).hexdigest())


def test_v2_refuses_d28_scope_other_than_thinking_off(tmp_path):
    raw=yaml.safe_load(RULE_V2.read_text());raw['eligibility']['d28_scope']='all_modes'
    path=tmp_path/'rule.yaml';path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ValueError,match='D28 eligibility'):
        load_rule(path, hashlib.sha256(path.read_bytes()).hexdigest())


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
    with pytest.raises(ValueError, match='B2 node/instance grid'):
        b2_summary([_b2(sha, 'a', .5, 1., rerun=[.95]), _b2(sha, 'b', .6, 1.)], rule_path=RULE_V2)


def test_b2_refuses_a_non_off_primary_manifest():
    _, sha = v2()
    for mode in ('on', 'always_on', False, None):
        with pytest.raises(ValueError, match='refuses a primary B2 manifest'):
            b2_summary([_b2(sha, 'a', .99, 1., mode=mode), _b2(sha, 'b', .6, 1.)], rule_path=RULE_V2)
    with pytest.raises(ValueError, match='rule hash'):
        b2_summary([_b2(V1_SHA, 'b', .6, 1.)], rule_path=RULE_V2)


def test_b2_ties_go_to_lower_gpu_hours():
    _, sha = v2()
    with pytest.raises(ValueError, match='B2 node/instance grid'):
        b2_summary([_b2(sha, 'slow', .7, 3.), _b2(sha, 'fast', .7, 1.), _b2(sha, 'unknown', .7, None)], rule_path=RULE_V2)


def test_v2_b2_rejects_duplicate_primary_candidate():
    _, sha = v2()
    with pytest.raises(ValueError, match='duplicate primary B2 candidate'):
        b2_summary([_b2(sha, 'a', .9, 1.), _b2(sha, 'a', .8, 1.),
                    _b2(sha, 'b', .7, 1.)], rule_path=RULE_V2)


def test_b2_without_rule_or_under_v1_is_unchanged():
    m = _b2(V1_SHA, 'x', .7, 1., mode='on')
    old = b2_summary([m])
    assert old['rows'][0]['mode'] == 'on' and 'thinking_on_descriptive' not in old
    assert b2_summary([m], rule_path=RULE) == old
    unstamped = {k: v for k, v in m.items() if k != 'rule_sha256'}
    assert b2_summary([unstamped])['rows'][0]['candidate'] == 'x'      # historical no-rule call still works


def _v2_b2_pair(sha):
    on = {**_b2(sha, 'on_model', .9, 1., mode='on'), 'rule_version': 'x5_rule/v2'}
    off = {**_b2(sha, 'off_model', .5, 1.), 'rule_version': 'x5_rule/v2'}
    return [on, off]


def test_v2_b2_manifests_refused_without_the_v2_rule(tmp_path):
    """Review F1: v2 manifests are never ranked under v1 semantics by omitting --rule."""
    _, sha = v2()
    ms = _v2_b2_pair(sha)
    with pytest.raises(ValueError, match='requires the v2 rule'):
        b2_summary(ms)
    for m in ms:                                     # either stamp alone is enough
        only_sha = {k: v for k, v in m.items() if k != 'rule_version'}
        only_version = {**m, 'rule_sha256': None}
        for variant in (only_sha, only_version):
            with pytest.raises(ValueError, match='requires the v2 rule'):
                b2_summary([variant])
    with pytest.raises(ValueError, match='rule hash differs'):
        b2_summary(ms, rule_path=RULE)               # v1 given explicitly: sha check refuses v2 manifests
    paths = []
    for m in ms:
        path = tmp_path / f"{m['candidate']}.json"; write_json(path, m); paths.append(str(path))
    with pytest.raises(ValueError):
        analyze.main(['b2', *paths])                 # CLI default --rule (v1)
    with pytest.raises(ValueError, match='refuses a primary B2 manifest'):
        analyze.main(['b2', *paths, '--rule', str(RULE_V2), '--rule-sha256', sha])


def test_b2_with_rule_checks_every_manifest_sha():
    _, sha = v2()
    good = _b2(sha, 'a', .5, 1.)
    with pytest.raises(ValueError, match='B2 node/instance grid'):
        b2_summary([good], rule_path=RULE_V2)
    for bad in (None, V1_SHA, '0' * 64):
        with pytest.raises(ValueError, match='rule hash'):
            b2_summary([good, {**_b2(sha, 'b', .6, 1.), 'rule_sha256': bad}], rule_path=RULE_V2)
    with pytest.raises(ValueError, match='rule hash differs'):
        b2_summary([_b2(None, 'x', .7, 1.)], rule_path=RULE)


def test_v2_validator_refuses_run_descriptive(tmp_path):
    """Review F4: only the ruled 'skip' is accepted; the frozen v2 bytes are untouched."""
    assert digest_file(RULE_V2) == '53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad'
    bad = tmp_path / 'alt.yaml'
    bad.write_text(RULE_V2.read_text().replace('always_on_in_b1: skip', 'always_on_in_b1: run_descriptive'))
    with pytest.raises(ValueError, match='must be skip'):
        load_rule(bad, hashlib.sha256(bad.read_bytes()).hexdigest())


# ---------------------------------------------------------------- runner: Stage A pass set
def _stage_table(path, rows, label='ENGINEERING_ONLY'):
    write_json(path, {'label': label, 'rows': rows})
    return path


def _amend_cfg(tmp_path, stage_rows, amend_rows):
    stage = _stage_table(tmp_path / 'stage.json', stage_rows)
    amend = _stage_table(tmp_path / 'amend.json', amend_rows)
    acc = tmp_path / 'acceptance.md'
    acc.write_text(f'operator O1 acceptance of t7j10 (fixture): table SHA {digest_file(amend)}; '
                   f'Stage A table SHA {digest_file(stage)}\n')
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


@pytest.mark.parametrize('rows', [[{'passed': True}], [{'candidate': 'gemma4_31b'}], [{'candidate': 7, 'passed': True}],
                                  [{'candidate': 'gemma4_31b', 'passed': 'yes'}], ['gemma4_31b']])
def test_v2_pass_set_malformed_amendment_rows_stop(tmp_path, rows):
    """Review F8: malformed amendment rows are a STOP, not a KeyError."""
    from r1.scripts.exam_runner import stage_a_pass_set
    cfg = _amend_cfg(tmp_path, [{'candidate': 'qwen38_27b', 'passed': True}], rows)
    with pytest.raises(PreparationStop, match='row malformed'):
        stage_a_pass_set(cfg, {'gemma4_31b'}, v2=True)


def test_v2_pass_set_acceptance_must_name_both_table_shas(tmp_path):
    from r1.scripts.exam_runner import stage_a_pass_set
    cfg = _amend_cfg(tmp_path, [{'candidate': 'qwen38_27b', 'passed': True}], [{'candidate': 'gemma4_31b', 'passed': True}])
    acc = Path(cfg['stage_a_amendment_acceptance'])
    acc.write_text('accepted, without naming the tables\n')
    cfg['stage_a_amendment_acceptance_sha256'] = digest_file(acc)
    with pytest.raises(PreparationStop, match='does not name'):
        stage_a_pass_set(cfg, {'gemma4_31b'}, v2=True)


def test_real_t7j10_shape_and_o1_acceptance_fit_the_loader(tmp_path):
    """The t7j10 rows (O1 report, ops-20261104 @ f52db28e): 3 anchors + 7 amendment candidates, all PASS,
    in the Stage A table shape.  The B1 candidate set is t7h8's 8 PASS + t7j10's 7 PASS (+ 3 anchors)."""
    from r1.scripts.exam_runner import stage_a_pass_set
    t7h8_pass = ['glm47_flash', 'ornith10_35b', 'ornith10_9b', 'qwen35_9b', 'qwen36_27b', 'qwen36_35b_a3b', 'qwen38_27b',
                 'qwen3_coder_30b_a3b']
    t7h8_fail = ['devstral_small2_24b', 'gemma4_12b', 'gemma4_26b_a4b', 'gemma4_31b', 'laguna_xs21', 'ministral3_14b',
                 'olmo31_32b', 'lfm25_24b_a2b', 'muse_glimmer_30b', 'gpt_oss_20b', 'rico03_qwen36_27b', 'nemotron35_30b_a3b']
    anchors = ['random_valid', 'scripted', 'qwen25_coder_7b']
    m1 = ['gemma4_31b', 'olmo31_32b', 'devstral_small2_24b', 'gemma4_26b_a4b', 'laguna_xs21', 'gemma4_12b', 'ministral3_14b']
    stage = [{'candidate': c, 'passed': True, 'software_anchor': c in anchors[:2]} for c in anchors] + \
            [{'candidate': c, 'passed': True} for c in t7h8_pass] + [{'candidate': c, 'passed': False} for c in t7h8_fail]
    amend = [{'candidate': c, 'passed': True, 'software_anchor': True, 'prompts': 0} for c in anchors[:2]] + \
            [{'candidate': c, 'passed': True, 'template_checks_frozen': [True] * 50} for c in ['qwen25_coder_7b'] + m1]
    cfg = _amend_cfg(tmp_path, stage, amend)
    registry = {r['id'] for r in REGISTRY['candidates'] if r['role'] == 'candidate'}
    got = stage_a_pass_set(cfg, registry, v2=True)
    cands = sorted(c for c in got if c in registry)
    assert cands == sorted(t7h8_pass + m1) and len(cands) == 15
    assert set(got) - registry == set(anchors)
    assert all(got[c]['stage_a_pass_source'] == 'stage_a_table' for c in anchors)
    for cid in REPAIRED: assert got[cid]['stage_a_pass_source'] == 'a1_amendment_measurement'


def test_v2_configs_bind_the_o1_accepted_tables():
    """The shas the v2 configs bind are the ones the accepted O1 report records."""
    for name in ('exam_b1_v2.json', 'exam_b2_v2.json'):
        cfg = json.loads((CONFIGS / name).read_text())
        assert cfg['stage_a_table_sha256'] == '00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c'
        assert cfg['stage_a_amendment_table_sha256'] == '71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103'
        assert cfg['stage_a_amendment_acceptance'] == 'docs/r1/reports/OPS_O1_20261104.md'
        assert cfg['stage_a_amendment_acceptance_sha256'] == '0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e'
        # R1-EXAM-HOST-B1B2-TASL7 (author, 4 Nov 18:10) supersedes review F9's placeholder: TASL-7 and its GPU.
        portal = json.loads(DEFAULT_CONFIG.read_text())
        assert cfg['host'] == 'TASL-7' and cfg['gpu_uuid'] == portal['gpu_uuid'] == 'GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1'


def test_author_gate_binds_amendment_shas(tmp_path, monkeypatch):
    """Review F8: runtime.author_gate's amendment clause (positive and negative)."""
    from r1.exam import runtime
    rule_sha = Path(str(RULE_V2) + '.sha256').read_text().split()[0]
    monkeypatch.setattr(runtime, 'REPO', tmp_path)
    (tmp_path / 'docs/r1').mkdir(parents=True)
    (tmp_path / 'docs/r1/PLAN.md').write_text(f'| R1-EXAM-RULE-X5V2 | `{rule_sha}` |\n')
    note = tmp_path / 'note.json'
    cfg = {'rule': str(RULE_V2), 'authorizations': {'b1': str(note)}, 'nodes': ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere'],
           'stage_a_table_sha256': 'a' * 64, 'llm_call_cap': 40, 'instance_seeds': [9001, 9002, 9003, 9004],
           'audit_seeds': [9101, 9102, 9103, 9104], 'stage_a_amendment_table_sha256': 'b' * 64,
           'stage_a_amendment_acceptance_sha256': 'c' * 64}
    base = {'author': 'Dowling Wong', 'phase': 'b1', 'approved': True, 'rule_sha256': rule_sha, 'nodes': cfg['nodes'],
            'stage_a_table_sha256': 'a' * 64, 'llm_call_cap': 40}

    def gate(data):
        note.write_text(json.dumps(data))
        monkeypatch.setattr(runtime.subprocess, 'check_output', lambda *a, **k: note.read_bytes())
        # Exercise the legacy amendment binding below the v2 STOP in isolation.
        monkeypatch.setattr(runtime, 'load_rule', lambda path, sha: ({'version': 'x5_rule/v1'}, sha))
        runtime.author_gate(cfg, 'b1', rule_sha)
    gate({**base, 'stage_a_amendment_table_sha256': 'b' * 64, 'stage_a_amendment_acceptance_sha256': 'c' * 64})
    for bad in ({}, {'stage_a_amendment_table_sha256': 'b' * 64},
                {'stage_a_amendment_table_sha256': 'b' * 64, 'stage_a_amendment_acceptance_sha256': 'd' * 64}):
        with pytest.raises(RuntimeError, match='amendment table'):
            gate({**base, **bad})


@pytest.mark.parametrize('alternate', [False, True])
def test_v2_author_gate_fails_closed_even_with_forged_plan(tmp_path, monkeypatch, alternate):
    from r1.exam import runtime
    rule_path = RULE_V2
    if alternate:
        rule_path = tmp_path / 'alternate.yaml'
        rule_path.write_bytes(RULE_V2.read_bytes() + b'\n# different bytes, same v2 version\n')
    rule_sha = digest_file(rule_path)
    monkeypatch.setattr(runtime, 'REPO', tmp_path)
    (tmp_path / 'docs/r1').mkdir(parents=True)
    (tmp_path / 'docs/r1/PLAN.md').write_text(f'<!-- R1-EXAM-RULE-X5V2 {rule_sha} -->\n')
    note = tmp_path / 'note.json'
    note.write_text(json.dumps({'author': 'Dowling Wong', 'phase': 'b1', 'approved': True, 'rule_sha256': rule_sha}))
    monkeypatch.setattr(runtime.subprocess, 'check_output', lambda *a, **k: note.read_bytes())
    with pytest.raises(RuntimeError, match='configured rule sha256 mismatch'):
        runtime.author_gate({'rule': str(rule_path), 'authorizations': {'b1': str(note)}}, 'b1', rule_sha)


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


def test_b1_stops_before_running_when_required_thinking_on_is_unavailable(tmp_path, monkeypatch):
    from r1.scripts import exam_runner
    rule,sha=v2();specs=[_spec('sw',SWITCH)]
    runner=FakeRunner(tmp_path,specs,_runner_cfg(tmp_path,specs,['sw']),rule,sha)
    monkeypatch.setattr(exam_runner,'stage_a_pass_set',lambda *a,**k:{'sw':{'thinking_disabled_due_grammar':True}})
    with pytest.raises(PreparationStop,match='required thinking-on sensitivity disabled'):
        exam_runner.evidence(runner,'b1',None,False)
    assert not runner.served and not runner.roots


def test_anchor_reference_requires_matching_source_and_finite_interval(tmp_path):
    from r1.scripts.exam_runner import verify_anchor_reference
    source=tmp_path/'reference.json';source.write_text('{"pilot":"fixture"}')
    ref={'source':str(source),'sha256':digest_file(source),'lower':0.1,'upper':0.5}
    verify_anchor_reference({'anchor_duplicate_reference':ref})
    for changed in ({'sha256':'0'*64},{'lower':float('nan')},{'lower':0.8,'upper':0.2},
                    {'lower':True},{'source':str(tmp_path/'missing')}):
        with pytest.raises(PreparationStop,match='invalid anchor duplicate reference'):
            verify_anchor_reference({'anchor_duplicate_reference':{**ref,**changed}})


def test_b1_manifest_requires_and_records_authorized_head(tmp_path):
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('nt', NONTHINK)]
    cfg = _runner_cfg(tmp_path, specs, ['nt'], extra={'dryrun': False})
    runner = FakeRunner(tmp_path, specs, cfg, rule, sha)
    with pytest.raises(PreparationStop, match='authorized checkout HEAD'):
        _evidence_unreviewed(runner, 'b1', None, False)
    runner.author_head = 'a' * 40
    _evidence_unreviewed(runner, 'b1', None, False)
    manifest = json.loads((tmp_path / 'nt/b1_manifest.json').read_text())
    assert manifest['authorization_checkout_head'] == runner.author_head


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


def test_runner_v2_d28_gate_reads_thinking_off_roots_only(tmp_path):
    """Review F2: a failing descriptive thinking-on D28 never removes a model from v2 selection."""
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('sw', SWITCH)]
    runner = FakeRunner(tmp_path, specs, _runner_cfg(tmp_path, specs, ['sw']), rule, sha)
    base_root = runner.root

    def root(spec, phase, node, seed, mode, **kw):
        r = base_root(spec, phase, node, seed, mode, **kw)
        r['d28'] = {'nodes': {node: {'pass': mode == 'off'}}}
        return r
    runner.root = root
    _evidence_unreviewed(runner, 'b1', None, False)
    m = json.loads((tmp_path / 'sw/b1_manifest.json').read_text())
    assert m['d28_pass'] is True and m['d28_scope'] == 'thinking_off_roots_only'
    assert m['thinking_on_d28'] == {'pass': False, 'roots': 1, 'role': 'descriptive_never_changes_eligibility'}
    # a failing thinking-off root still fails the gate
    (tmp_path / 'b').mkdir()
    runner2 = FakeRunner(tmp_path / 'b', specs, _runner_cfg(tmp_path, specs, ['sw']), rule, sha)
    base2 = runner2.root

    def root2(spec, phase, node, seed, mode, **kw):
        r = base2(spec, phase, node, seed, mode, **kw)
        r['d28'] = {'nodes': {node: {'pass': not (mode == 'off' and node == 'openml_ionosphere')}}}
        return r
    runner2.root = root2
    _evidence_unreviewed(runner2, 'b1', None, False)
    m2 = json.loads((tmp_path / 'b/sw/b1_manifest.json').read_text())
    assert m2['d28_pass'] is False and m2['thinking_on_d28']['pass'] is True
    # v1 keeps the historical all-roots D28
    rule1, sha1 = load_rule()
    (tmp_path / 'c').mkdir()
    runner1 = FakeRunner(tmp_path / 'c', specs, _runner_cfg(tmp_path, specs, ['sw']), rule1, sha1)
    runner1.root = root
    _evidence_unreviewed(runner1, 'b1', None, False)
    assert json.loads((tmp_path / 'c/sw/b1_manifest.json').read_text())['d28_pass'] is False


def test_runner_v2_b2_refuses_finalist_without_b1_row(tmp_path):
    """Review F7."""
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    specs = [_spec('nt', NONTHINK), _spec('sw', SWITCH)]
    screen = tmp_path / 'b1.json'
    write_json(screen, {'rule_sha256': sha, 'finalists': ['nt', 'sw'], 'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]})
    cfg = _runner_cfg(tmp_path, specs, ['nt', 'sw'], extra={'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen)})
    with pytest.raises(PreparationStop, match='no B1 analysis row'):
        _evidence_unreviewed(FakeRunner(tmp_path, specs, cfg, rule, sha), 'b2', None, False)


@pytest.mark.parametrize('value,ok', [(None, True), ('', True), ('false', True), ('0', True), ('true', False), ('1', False),
                                      ('yes-please', False)])
def test_runner_v2_refuses_cache_prompt_env_override(tmp_path, monkeypatch, value, ok):
    """Review F6: pre-flight refusal of LLAMACPP_CACHE_PROMPT set to anything but false/empty."""
    from r1.scripts.exam_runner import _evidence_unreviewed
    rule, sha = v2()
    if value is None: monkeypatch.delenv('LLAMACPP_CACHE_PROMPT', raising=False)
    else: monkeypatch.setenv('LLAMACPP_CACHE_PROMPT', value)
    specs = [_spec('nt', NONTHINK)]
    runner = FakeRunner(tmp_path, specs, _runner_cfg(tmp_path, specs, ['nt']), rule, sha)
    if ok:
        _evidence_unreviewed(runner, 'b1', None, False)
    else:
        with pytest.raises(PreparationStop, match='LLAMACPP_CACHE_PROMPT'):
            _evidence_unreviewed(runner, 'b1', None, False)
        assert runner.served == []


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
    """Drive the real ExamRunner.server -> _server path up to the llama-server construction.

    ``_server`` has no B1- or B2-specific branch, so the ``phase`` parameter here is nominal; the B1/B2
    proof is this test together with ``test_runner_passes_registry_repair_to_server_and_records_sha``,
    which drives the B1/B2 body itself (review F8)."""
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
@pytest.mark.parametrize('cid', REPAIRED)
def test_b1_b2_repair_digest_mismatch_is_a_stop(monkeypatch, tmp_path, phase, cid):
    spec = copy.deepcopy(_repaired_specs()[cid])
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
        assert key in cfg and not str(cfg[key]).startswith('TODO_')   # filled from the accepted O1 report
    portal = json.loads(DEFAULT_CONFIG.read_text())
    differ = ('comment', 'rule', 'rule_sha256', 'harness_commit', 'paper_commit', 'host', 'authorizations', 'cache_prompt',
              'workers', 'llm_call_cap', 'nodes',
              'd3_policy', 'gpu_uuid', 'stage_a_table', 'stage_a_table_sha256')
    assert {k: v for k, v in cfg.items() if k in portal and k not in differ} == {k: portal[k] for k in cfg if k in portal and k not in differ}


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
        if os.environ.get('R1_REQUIRE_B1_HARNESS') == '1':
            pytest.fail('R1_REQUIRE_B1_HARNESS=1 but no a3fedbb checkout found; set AR_HARNESS_B1_ROOT')
        pytest.skip('harness a3fedbb checkout not found; set AR_HARNESS_B1_ROOT (R1_REQUIRE_B1_HARNESS=1 makes this fail)')
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
        if os.environ.get('R1_REQUIRE_B1_HARNESS') == '1':
            pytest.fail(f'R1_REQUIRE_B1_HARNESS=1 but AR_HARNESS_ROOT is not the Stage A pin (found {head})')
        pytest.skip(f'AR_HARNESS_ROOT is not the Stage A pin (found {head})')
    r = _drive(tmp_path, harness)
    assert r['requests'] and all('cache_prompt' not in q['body'] for q in r['requests'])
    assert r['manifest_cache_prompt'] is None and 'not explicitly false' in r['stop']


# ---------------------------------------------------------------- B1/B2 worker host (R1-EXAM-HOST-B1B2-TASL7)
def test_b1_b2_worker_host_follows_cfg_host():
    """Author 4 Nov 18:10: B1/B2 on TASL-7; the worker must run on cfg.host, which must be an approved exam host."""
    from r1.exam.campaign import require_worker_host
    from r1.exam.runtime import APPROVED_EXAM_HOSTS
    assert APPROVED_EXAM_HOSTS == frozenset({'TASL-2', 'TASL-7'})
    assert require_worker_host({'host': 'TASL-7'}, node='TASL-7') == 'TASL-7'
    assert require_worker_host({'host': 'TASL-7'}, node='TASL-7.example.kit.edu') == 'TASL-7'
    assert require_worker_host({'host': 'TASL-2'}, node='TASL-2') == 'TASL-2'
    with pytest.raises(RuntimeError, match='configured exam host'):
        require_worker_host({'host': 'TASL-7'}, node='TASL-2')
    with pytest.raises(RuntimeError, match='configured exam host'):
        require_worker_host({'host': 'TASL-7'}, node='macbook')
    for bad in ('deepthought', 'TODO_AUTHOR', None):
        with pytest.raises(RuntimeError, match='not an approved exam host'):
            require_worker_host({'host': bad}, node=str(bad))


def test_worker_host_uses_platform_node(monkeypatch):
    from r1.exam import campaign
    import platform
    monkeypatch.setattr(platform, 'node', lambda: 'TASL-7')
    assert campaign.require_worker_host({'host': 'TASL-7'}) == 'TASL-7'
    monkeypatch.setattr(platform, 'node', lambda: 'TASL-2')
    with pytest.raises(RuntimeError, match='configured exam host'):
        campaign.require_worker_host({'host': 'TASL-7'})


def test_collect_no_longer_hardcodes_tasl2_and_root_job_carries_host():
    import inspect
    from r1.exam import campaign, runtime
    src = inspect.getsource(campaign._collect_b1_review)
    assert "'TASL-2'" not in src and 'require_worker_host(job)' in src
    assert "'host':self.cfg['host']" in inspect.getsource(runtime.ExamRunner.root)


def test_stage_a_host_rules_unchanged(tmp_path, monkeypatch):
    """Stage A keeps exam_portal.json (TASL-7) and host_check's approved-host rule."""
    import platform
    from r1.exam import runtime
    portal = json.loads(DEFAULT_CONFIG.read_text())
    assert portal['host'] == 'TASL-7' and 'workers' in portal
    monkeypatch.delenv('R1_DRYRUN', raising=False); monkeypatch.delenv('R1_FAKE_OLLAMA_ROOT', raising=False)
    monkeypatch.delenv('R1_EXAM_DRYRUN', raising=False)
    monkeypatch.setattr(platform, 'node', lambda: 'TASL-2')
    with pytest.raises(RuntimeError, match='approved portal host'):
        runtime.host_check(portal, tmp_path)          # cfg.host TASL-7 on node TASL-2: refused, as before
    monkeypatch.setattr(platform, 'node', lambda: 'macbook')
    with pytest.raises(RuntimeError, match='never infer on the Mac'):
        runtime.host_check({**portal, 'host': 'macbook'}, tmp_path)
