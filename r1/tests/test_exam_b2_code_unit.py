"""B2 code unit (14 Nov 2026; AI-assisted, Claude): B2 authority, B2 protections and the B2 grid verifier.

Synthetic committed checkouts and fixtures only; no server, model or GPU.  Every B2 test that has a B1 twin in
``test_exam_b1_committed_authority.py`` / ``test_exam_b1_parent_binding.py`` / ``test_b1_worker_input_unittest.py``
uses the same construction, so B2 is held to the same STOPs.
"""
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.exam import runtime
from r1.exam.analyze import RULE_V2

ENV = {**os.environ, 'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
       'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
NODES = ['digits_mlp', 'openml_credit_approval', 'openml_ionosphere']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


TABLE = '| ID | Decision |\n|---|---|\n'


def plan_text(rule_sha, *, n=4, power=None, invalid=None, heading='### 14 November 2026 — author decision\n'):
    power = power if power is not None else f'| R1-EXAM-B2-POWER-PLAN | precision plan; b2_instances_per_node = {n} |\n'
    invalid = invalid if invalid is not None else \
        '| R1-EXAM-B2-INVALID-TRIALS | R1-EXAM-B1-TRUNCATION-INVALID and R1-EXAM-B1-MODEL-OUTPUT-INVALID extend to B2 |\n'
    return ('## 10. Open decisions\n### 5 November 2026 — author decision\n' + TABLE +
            f'| R1-EXAM-RULE-X5V2 | "approved {rule_sha}" |\n' + heading + TABLE + power + invalid + '## 11. Other\n')


def commit(root, message='synthetic'):
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True, env=ENV)
    subprocess.run(['git', '-C', str(root), 'commit', '-qm', message], check=True, env=ENV)


def setup_b2_repo(tmp_path, monkeypatch, *, plan=None, analysis=None, n=4):
    root = tmp_path / 'repo'; root.mkdir()
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    (root / 'docs/r1').mkdir(parents=True)
    rule = root / 'rule.yaml'; rule.write_bytes(RULE_V2.read_bytes())
    table = root / 'stage.json'; table.write_text('{"rows":[]}')
    amendment = root / 'amendment.json'; amendment.write_text('{"rows":[]}')
    acceptance = root / 'acceptance.md'; acceptance.write_text('test acceptance')
    anchor = root / 'anchor.json'; anchor.write_text('{"lower":0.2,"upper":0.8}')
    rule_sha = sha(rule)
    b1 = root / 'b1_analysis.json'
    b1.write_text(json.dumps(analysis if analysis is not None else
                             {'phase': 'b1', 'label': 'EXAM', 'rule_sha256': rule_sha, 'rows': [],
                              'finalists': ['gemma4_31b'], 'execution_label': 'EVIDENCE',
                              'batch_verification': {'synthetic': True}}))
    (root / 'docs/r1/PLAN.md').write_text(plan(rule_sha) if plan else plan_text(rule_sha, n=n))
    note = root / 'author_b2.json'
    cfg = {'rule': str(rule), 'rule_sha256': rule_sha, 'stage_a_table': str(table), 'stage_a_table_sha256': sha(table),
           'stage_a_amendment_table': str(amendment), 'stage_a_amendment_table_sha256': sha(amendment),
           'stage_a_amendment_acceptance': str(acceptance), 'stage_a_amendment_acceptance_sha256': sha(acceptance),
           'nodes': list(NODES), 'llm_call_cap': 80, 'workers': 20, 'instance_seeds': [9001, 9002, 9003, 9004],
           'audit_seeds': [9101, 9102, 9103, 9104], 'authorizations': {'b2': str(note)}, 'host': 'TASL-7',
           'gpu_uuid': 'GPU-TEST', 'b1_analysis': str(b1), 'b1_analysis_sha256': sha(b1), 'b2_instances_per_node': n,
           'anchor_duplicate_reference': {'source': str(anchor), 'sha256': sha(anchor), 'lower': 0.2, 'upper': 0.8}}
    data = {'author': 'Dowling Wong', 'phase': 'b2', 'approved': True, 'rule_sha256': rule_sha, 'nodes': cfg['nodes'],
            'llm_call_cap': 80, 'workers': 20, 'stage_a_table_sha256': sha(table),
            'stage_a_amendment_table_sha256': sha(amendment), 'stage_a_amendment_acceptance_sha256': sha(acceptance),
            'anchor_duplicate_reference_sha256': sha(anchor), 'host': 'TASL-7', 'gpu_uuid': 'GPU-TEST',
            'b1_analysis_sha256': sha(b1), 'instances_per_node': n}
    note.write_text(json.dumps(data))
    commit(root)
    monkeypatch.setattr(runtime, 'REPO', root)
    return root, cfg, rule_sha


def recommit_note(root, change):
    note = root / 'author_b2.json'; data = json.loads(note.read_text()); change(data)
    note.write_text(json.dumps(data)); commit(root, 'note change')


# ------------------------------------------------------------------------------------------- B2 authority
def test_b2_committed_authority_passes_and_returns_head(tmp_path, monkeypatch):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    assert runtime.author_gate(cfg, 'b2', rule_sha) == head


@pytest.mark.parametrize('case', ['no_power_row', 'undated', 'wrong_n', 'two_literals', 'duplicate_row',
                                  'no_invalid_row', 'invalid_row_names_one_rule', 'fenced', 'date_in_first_cell'])
def test_b2_requires_the_two_dated_author_rows(tmp_path, monkeypatch, case):
    def plan(rule_sha):
        if case == 'no_power_row': return plan_text(rule_sha, power='')
        if case == 'undated': return plan_text(rule_sha, heading='### B2 decisions (author)\n')
        if case == 'wrong_n': return plan_text(rule_sha, n=5)
        if case == 'two_literals':
            return plan_text(rule_sha, power='| R1-EXAM-B2-POWER-PLAN | b2_instances_per_node = 4; b2_instances_per_node = 4 |\n')
        if case == 'duplicate_row':
            row = '| R1-EXAM-B2-POWER-PLAN | b2_instances_per_node = 4 |\n'
            return plan_text(rule_sha, power=row + row)
        if case == 'no_invalid_row': return plan_text(rule_sha, invalid='')
        if case == 'invalid_row_names_one_rule':
            return plan_text(rule_sha, invalid='| R1-EXAM-B2-INVALID-TRIALS | R1-EXAM-B1-TRUNCATION-INVALID extends to B2 |\n')
        if case == 'fenced':
            return plan_text(rule_sha).replace('### 14 November 2026', '```\n### 14 November 2026') + '```\n'
        if case == 'date_in_first_cell':
            return plan_text(rule_sha, power='| R1-EXAM-B2-POWER-PLAN (14 Nov) | b2_instances_per_node = 4 |\n')
    _, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch, plan=plan)
    with pytest.raises(RuntimeError, match='B2 power-plan and invalid-trial author rows'):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_b2_author_rows_parser_accepts_only_the_exact_form():
    sha_ = 'a' * 64
    assert runtime._b2_author_rows(plan_text(sha_, n=4), 4)
    assert not runtime._b2_author_rows(plan_text(sha_, n=4), 3)
    assert not runtime._b2_author_rows(plan_text(sha_, n=14), 1)          # "14" never matches 1
    assert not runtime._b2_author_rows(plan_text(sha_, n=4), True)
    assert not runtime._b2_author_rows('## 10. Open decisions\n<div>\n' + plan_text(sha_)[len('## 10. Open decisions\n'):] + '</div>\n', 4)


@pytest.mark.parametrize('mutation', ['uncommitted', 'sha', 'not_evidence', 'empty_finalists', 'duplicate_finalists',
                                      'other_rule', 'no_batch_proof', 'phase'])
def test_b2_needs_the_committed_verified_b1_analysis(tmp_path, monkeypatch, mutation):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    b1 = Path(cfg['b1_analysis']); data = json.loads(b1.read_text())
    if mutation == 'uncommitted':
        b1.write_text(json.dumps({**data, 'note': 'edited'})); cfg['b1_analysis_sha256'] = sha(b1)
        with pytest.raises(RuntimeError, match='clean'):
            runtime.author_gate(cfg, 'b2', rule_sha)
        return
    if mutation == 'sha':
        cfg['b1_analysis_sha256'] = '0' * 64
        with pytest.raises(RuntimeError, match='B1 analysis is not the committed, digest-bound file'):
            runtime.author_gate(cfg, 'b2', rule_sha)
        return
    change = {'not_evidence': {'execution_label': 'DRYRUN'}, 'empty_finalists': {'finalists': []},
              'duplicate_finalists': {'finalists': ['gemma4_31b', 'gemma4_31b']}, 'other_rule': {'rule_sha256': '1' * 64},
              'no_batch_proof': {'batch_verification': None}, 'phase': {'phase': 'b2'}}[mutation]
    b1.write_text(json.dumps({**data, **change})); cfg['b1_analysis_sha256'] = sha(b1)
    recommit_note(root, lambda d: d.update(b1_analysis_sha256=cfg['b1_analysis_sha256']))
    with pytest.raises(RuntimeError, match='verified complete-batch x5_rule/v2 evidence analysis'):
        runtime.author_gate(cfg, 'b2', rule_sha)


@pytest.mark.parametrize('field,match', [('host', 'B2 host or GPU UUID'), ('gpu_uuid', 'B2 host or GPU UUID'),
                                         ('workers', 'worker count'), ('instances_per_node', 'instance count not author-bound'),
                                         ('b1_analysis_sha256', 'bind B1 analysis'), ('anchor_duplicate_reference_sha256', 'anchor reference'),
                                         ('nodes', 'nodes and accepted Stage A'), ('phase', 'bind author, phase')])
def test_b2_note_binds_host_gpu_workers_count_analysis_anchor(tmp_path, monkeypatch, field, match):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    wrong = {'host': 'TASL-2', 'gpu_uuid': 'GPU-OTHER', 'workers': 19, 'instances_per_node': 5,
             'b1_analysis_sha256': '0' * 64, 'anchor_duplicate_reference_sha256': '0' * 64,
             'nodes': NODES[:2], 'phase': 'b1'}[field]
    recommit_note(root, lambda d: d.update({field: wrong}))
    with pytest.raises(RuntimeError, match=match):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_b2_config_host_and_gpu_must_match_the_note(tmp_path, monkeypatch):
    _, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    cfg['gpu_uuid'] = 'GPU-OTHER'
    with pytest.raises(RuntimeError, match='B2 host or GPU UUID'):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_b2_count_above_the_author_cap_stops(tmp_path, monkeypatch):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch, n=11)
    with pytest.raises(RuntimeError, match='author cap of 10'):
        runtime.author_gate(cfg, 'b2', rule_sha)


@pytest.mark.parametrize('n', [0, 90, True, '4'])
def test_b2_count_must_fit_the_fresh_namespace(tmp_path, monkeypatch, n):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    cfg['b2_instances_per_node'] = n
    with pytest.raises(RuntimeError):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_b2_requires_the_three_protocol_nodes(tmp_path, monkeypatch):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    cfg['nodes'] = ['digits_mlp', 'openml_credit_approval', 'track_g_node']
    recommit_note(root, lambda d: d.update(nodes=cfg['nodes']))
    with pytest.raises(RuntimeError, match='three protocol nodes'):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_dirty_checkout_refused_for_b2(tmp_path, monkeypatch):
    root, cfg, rule_sha = setup_b2_repo(tmp_path, monkeypatch)
    (root / 'dirty.txt').write_text('x')
    with pytest.raises(RuntimeError, match='clean'):
        runtime.author_gate(cfg, 'b2', rule_sha)


def test_b1_authority_is_unchanged_by_the_b2_rows():
    # The B1 parser is untouched: a plan with only the X5 row still satisfies it, and the B2 rows are ignored.
    assert runtime._x5_author_row(plan_text('a' * 64, power='', invalid=''), 'a' * 64)
    assert runtime._x5_author_row(plan_text('a' * 64), 'a' * 64)


# ------------------------------------------------------------------------------------------- seeds
def test_phase_seeds():
    cfg = {'instance_seeds': [9001, 9002, 9003, 9004], 'audit_seeds': [9101, 9102, 9103, 9104], 'b2_instances_per_node': 4}
    assert runtime.phase_seeds(cfg, 'b1') == ([9001, 9002, 9003, 9004], [9101, 9102, 9103, 9104])
    assert runtime.phase_seeds(cfg, 'b2') == ([9011, 9012, 9013, 9014], list(range(9201, 9211)))
    for bad in (0, 90, True, None):
        with pytest.raises(RuntimeError, match='9011–9099'):
            runtime.phase_seeds({**cfg, 'b2_instances_per_node': bad}, 'b2')
    with pytest.raises(RuntimeError):
        runtime.phase_seeds(cfg, 'stage-a')


# ------------------------------------------------------------------------------------------- worker / observer input
def _worker_job(phase='b2', **change):
    cfg = {'rule_sha256': 'r', 'workers': 20, 'W': 20, 'llm_call_cap': 80, 'audit_seeds': [9101, 9102, 9103, 9104],
           'instance_seeds': [9001, 9002, 9003, 9004], 'b2_instances_per_node': 4, 'value_grids': 'v.yaml',
           'host': 'TASL-7', 'nodes': list(NODES), 'proposal_schema': 'manager_proposal/v1'}
    job = {'phase': phase, 'authority_config': cfg, 'authorization_checkout_head': 'h' * 40, 'workers': 20, 'W': 20,
           'llm_call_cap': 80, 'audit_seeds': list(range(9201, 9211)) if phase == 'b2' else [9101, 9102, 9103, 9104],
           'value_grids': 'v.yaml', 'host': 'TASL-7', 'node': 'digits_mlp', 'seed': 9011 if phase == 'b2' else 9001,
           'mode': 'off', 'proposal_schema': 'manager_proposal/v1'}
    job.update(change)
    return job


@pytest.fixture
def worker_authority(monkeypatch):
    calls = []
    def committed(path, cfg, **kw):
        calls.append(('config', str(path), kw.get('rel'))); return 'h' * 40
    monkeypatch.setattr(runtime, 'require_committed_b1_config', committed)
    monkeypatch.setattr(runtime, 'require_committed_b1_registry', lambda *a, **k: None)
    monkeypatch.setattr(runtime, 'author_gate', lambda cfg, phase, sha: calls.append(('gate', phase)) or 'h' * 40)
    return calls


def test_b2_worker_input_uses_b2_config_gate_and_seeds(worker_authority):
    from r1.exam.campaign import _verify_b1_worker_input
    assert _verify_b1_worker_input(_worker_job()) == 'h' * 40
    assert ('config', str(runtime.REPO / runtime.B2_CONFIG_REL), runtime.B2_CONFIG_REL) in worker_authority
    assert ('gate', 'b2') in worker_authority


@pytest.mark.parametrize('change,match', [
    ({'seed': 9001}, 'seed/mode'), ({'seed': 9015}, 'seed/mode'), ({'seed': 9010}, 'seed/mode'),
    ({'audit_seeds': [9101, 9102, 9103, 9104]}, 'audit_seeds'), ({'audit_seeds': list(range(9201, 9210))}, 'audit_seeds'),
    ({'mode': 'always_on'}, 'seed/mode'), ({'host': 'TASL-2'}, 'host/node'), ({'node': 'tabular_mlp'}, 'host/node'),
    ({'workers': 4}, 'workers'), ({'llm_call_cap': 40}, 'llm_call_cap'), ({'proposal_schema': None}, 'proposal schema'),
    ({'authorization_checkout_head': 'g' * 40}, 'HEAD differs'),
])
def test_b2_worker_input_stops(worker_authority, change, match):
    from r1.exam.campaign import _verify_b1_worker_input
    with pytest.raises(RuntimeError, match=match):
        _verify_b1_worker_input(_worker_job(**change))


def test_b1_worker_input_still_calls_the_b1_config_without_rel(worker_authority):
    from r1.exam.campaign import _verify_b1_worker_input
    _verify_b1_worker_input(_worker_job('b1'))
    assert ('config', str(runtime.REPO / runtime.B1_CONFIG_REL), None) in worker_authority
    assert ('gate', 'b1') in worker_authority
    with pytest.raises(RuntimeError, match='seed/mode'):
        _verify_b1_worker_input(_worker_job('b1', seed=9011))


def test_collector_dispatch():
    from r1.exam import campaign
    with pytest.raises(RuntimeError, match='only the reviewed B1/B2 collector'):
        campaign.collect({'phase': 'stage-a'})
    seen = []
    original = campaign._collect_b1_review
    try:
        campaign._collect_b1_review = lambda job: seen.append(job['phase']) or 'ok'
        assert campaign.collect({'phase': 'b2'}) == 'ok' and campaign.collect({'phase': 'b1'}) == 'ok'
    finally:
        campaign._collect_b1_review = original
    assert seen == ['b2', 'b1']
    with pytest.raises(RuntimeError, match='refuses other phases'):
        original({'phase': 'b3'})


def test_b2_observer_context_seeds_and_rerun_nodes(monkeypatch):
    from r1.exam import observer
    from r1.exam.cache_false import D3EvidenceStop
    monkeypatch.setattr(runtime, 'author_gate', lambda cfg, phase, sha: 'h' * 40)
    monkeypatch.setattr(runtime, 'read_registry', lambda path: {})
    monkeypatch.setattr(observer, '_authorized_candidate', lambda job, cfg, registry: True)
    import r1.exam.campaign as campaign
    monkeypatch.setattr(campaign, 'require_worker_host', lambda job: job['host'])
    job = _worker_job()
    job['authority_config'].update(cache_prompt=False, registry='r.yaml', rule='rule.yaml', dryrun=False)
    with observer.authorized_b1_observer(job):
        pass
    # B2's descriptive thinking-on rerun runs on every node (no B1 sensitivity-node restriction).
    with observer.authorized_b1_observer({**job, 'mode': 'on', 'node': 'openml_ionosphere'}):
        pass
    for change in ({'seed': 9001}, {'audit_seeds': [9101, 9102, 9103, 9104]}, {'phase': 'stage-a'}):
        with pytest.raises(D3EvidenceStop):
            with observer.authorized_b1_observer({**job, **change}):
                pass


# ------------------------------------------------------------------------------------------- runner protections in b2
def _runner(tmp_path, phase='b2', dryrun=False):
    r = object.__new__(runtime.ExamRunner)
    r.cfg = {'dryrun': dryrun, 'work_dir': str(tmp_path / 'work'), 'nodes': list(NODES), 'harness_commit': 'a3fedbb',
             'workers': 20, 'host': 'TASL-7', 'W': 20, 'llm_call_cap': 80, 'audit_seeds': [9101, 9102, 9103, 9104],
             'value_grids': 'v.yaml', 'b2_instances_per_node': 4}
    r.out = tmp_path / 'work' / 'b2_batch'
    r.rule = {'version': 'x5_rule/v2'}; r.rule_sha = 's'; r.binding = 'b'
    r.b1_config_head = 'h' * 40; r.registry_path = None; r.registry = None
    r.service = None; r.child = None; r.lock = None; r.author_head = None; r.b1_lease_fd = None; r.b1_state_identity = None
    r.state = {'phase': phase, 'completed': {}, 'interruptions': [], 'execution_label': 'EVIDENCE'}
    return r


def _start_stubs(monkeypatch, calls):
    monkeypatch.setattr(runtime, 'require_committed_b1_config', lambda path, cfg, **kw: calls.append(('config', kw.get('rel'))) or 'h' * 40)
    monkeypatch.setattr(runtime, 'require_committed_b1_registry', lambda *a, **k: None)
    monkeypatch.setattr(runtime, 'author_gate', lambda cfg, phase, sha: calls.append(('gate', phase)) or 'h' * 40)
    monkeypatch.setattr(runtime, 'worker_environment', lambda *a: calls.append(('env',)) or {})
    monkeypatch.setattr(runtime, 'b1_harness_sources', lambda node, commit: calls.append(('sources', node)) or {})


def test_b2_start_refuses_an_existing_batch_and_binds_config_gate_env_sources(tmp_path, monkeypatch):
    calls = []
    _start_stubs(monkeypatch, calls)
    r = _runner(tmp_path)
    (tmp_path / 'work').mkdir(); r.out.mkdir()
    marker = r.out / 'keep.txt'; marker.write_text('preserved')
    with pytest.raises(runtime.PreparationStop, match='B2 batch already exists; no automatic resume'):
        r.start('b2')
    assert marker.read_text() == 'preserved' and sorted(p.name for p in r.out.iterdir()) == ['keep.txt']
    assert ('config', runtime.B2_CONFIG_REL) in calls and ('gate', 'b2') in calls and ('env',) in calls
    assert {c[1] for c in calls if c[0] == 'sources'} == set(NODES)


def test_b2_start_requires_a_direct_child_of_work_dir(tmp_path, monkeypatch):
    calls = []
    _start_stubs(monkeypatch, calls)
    r = _runner(tmp_path); r.out = tmp_path / 'elsewhere' / 'b2'
    with pytest.raises(runtime.PreparationStop, match='B2 batch must be a fresh direct child of work_dir'):
        r.start('b2')
    assert not r.out.exists()


def test_b2_start_head_must_equal_config_head(tmp_path, monkeypatch):
    calls = []
    _start_stubs(monkeypatch, calls)
    monkeypatch.setattr(runtime, 'author_gate', lambda *a: 'g' * 40)
    r = _runner(tmp_path)
    with pytest.raises(runtime.PreparationStop, match='B2 authorization HEAD differs from committed config HEAD'):
        r.start('b2')
    assert not r.out.exists()


def test_b2_existing_production_root_is_preserved(tmp_path):
    r = _runner(tmp_path)
    spec = {'id': 'gemma4_31b', 'runtime': {'footprint_mib': 1}}
    path = r.out / 'gemma4_31b/b2/off/digits_mlp__s9011'; path.mkdir(parents=True)
    (path / 'partial.json').write_text('{}')
    r.space = lambda: None
    with pytest.raises(runtime.PreparationStop, match='existing B2 root is preserved; no automatic recovery'):
        r.root(spec, 'b2', 'digits_mlp', 9011, 'off')
    assert (path / 'partial.json').read_text() == '{}'


def test_b2_completed_root_must_carry_the_authorized_head(tmp_path, monkeypatch):
    r = _runner(tmp_path); r.author_head = 'c' * 40
    root = r.out / 'gemma4_31b/b2/off/digits_mlp__s9011'; root.mkdir(parents=True)
    (root / 'job.json').write_text(json.dumps({'authorization_checkout_head': 'd' * 40}))
    manifest = root / 'campaign_manifest.json'; manifest.write_text('{}')
    r.state['completed']['gemma4_31b/b2/off/digits_mlp__s9011'] = {'path': str(manifest)}
    monkeypatch.setattr(runtime, 'verify_campaign', lambda path, binding: {})
    r.space = lambda: None
    with pytest.raises(runtime.PreparationStop, match='authorization HEAD mismatch'):
        r.root({'id': 'gemma4_31b'}, 'b2', 'digits_mlp', 9011, 'off')


def test_b2_root_job_carries_authority_head_harness_and_b2_seeds(tmp_path, monkeypatch):
    r = _runner(tmp_path); r.author_head = 'c' * 40; r.space = lambda: None
    monkeypatch.setattr(runtime, 'b1_harness_sources', lambda node, commit: {'train.py': 'x'})
    seen = {}
    def run_job(job, module, interrupt=False):
        seen.update(job); raise RuntimeError('stop after job built')
    r.run_job = run_job
    with pytest.raises(RuntimeError, match='stop after job built'):
        r.root({'id': 'gemma4_31b'}, 'b2', 'digits_mlp', 9011, 'off')
    assert seen['authorization_checkout_head'] == 'c' * 40 and seen['authority_config'] == r.cfg
    assert seen['audit_seeds'] == list(range(9201, 9211)) and seen['phase'] == 'b2' and seen['seed'] == 9011
    assert seen['harness_commit'] == 'a3fedbb' and seen['node_source_sha256'] == {'train.py': 'x'}
    r.author_head = None
    with pytest.raises(runtime.PreparationStop, match='B2 worker needs the authorized checkout HEAD'):
        r.root({'id': 'gemma4_31b'}, 'b2', 'digits_mlp', 9012, 'off')


def test_b2_live_previous_server_is_preserved():
    with pytest.raises(runtime.PreparationStop, match='live previous b2 server; preserve without signalling'):
        runtime.handle_live_orphan({'pid': 1}, 'b2')


def test_b2_runner_lock_is_preserved(tmp_path):
    (tmp_path / 'runner.lock').write_text(json.dumps({'pid': 1}))
    with pytest.raises(runtime.PreparationStop, match='existing B1 runner lock'):
        runtime.claim_runner_lock(tmp_path, preserve_existing=True)


def test_b2_server_needs_the_gpu_lease(tmp_path):
    r = _runner(tmp_path)
    with pytest.raises(runtime.PreparationStop, match='GPU lease is missing before server start'):
        r._server({'id': 'gemma4_31b'}, 'off', 32768)


# ------------------------------------------------------------------------------------------- exam_runner b2 entry
def test_b2_entry_refuses_subsets_and_the_free_sensitivity_in_production():
    from r1.scripts.exam_runner import evidence
    runner = SimpleNamespace(cfg={}, rule={'version': 'x5_rule/v2'})
    with pytest.raises(runtime.PreparationStop, match='full frozen finalist set'):
        evidence(runner, 'b2', ['gemma4_31b'], False)
    runner.cfg = {'free_sensitivity': True}
    with pytest.raises(runtime.PreparationStop, match='separately gated'):
        evidence(runner, 'b2', None, False)


def test_b2_cli_refuses_subset_and_free_sensitivity(monkeypatch, tmp_path):
    from r1.scripts import exam_runner
    monkeypatch.setattr(exam_runner, 'load_config', lambda *a, **k: {'authorizations': {'b2': 'note.md'}, 'd22_pick': 'x'})
    monkeypatch.setattr(exam_runner, 'require_committed_b1_config', lambda *a, **k: 'h' * 40)
    monkeypatch.setattr(exam_runner, 'ExamRunner', lambda *a, **k: pytest.fail('runner must not start'))
    with pytest.raises(runtime.PreparationStop, match='full frozen finalist set'):
        exam_runner.main(['b2', '--out', str(tmp_path / 'x'), '--candidate', 'gemma4_31b'])
    with pytest.raises(runtime.PreparationStop, match='separately gated'):
        exam_runner.main(['b2', '--out', str(tmp_path / 'x'), '--free-sensitivity'])
    assert not (tmp_path / 'x').exists()


# ------------------------------------------------------------------------------------------- marker tool
def test_marker_create_b2_heading_and_b1_default(tmp_path):
    from r1.scripts import b1_o2_marker as marker
    locks = tmp_path / 'locks'; locks.mkdir(mode=0o700)
    status = tmp_path / 'STATUS.md'; status.write_text('# Status\n')
    receipt = marker.create(locks, status, 'abcd_20261115_b2', 'a' * 40, 'b2')
    assert 'Track X B2 running' in status.read_text() and 'Track X B1 running' not in status.read_text()
    assert (locks / marker.NAME).exists() and receipt['run_id'] == 'abcd_20261115_b2'
    with pytest.raises(FileExistsError):
        marker.create(locks, status, 'second', 'a' * 40, 'b2')
    with pytest.raises(ValueError, match='invalid phase'):
        marker.create(locks, status, 'third', 'a' * 40, 'b3')
    locks2 = tmp_path / 'locks2'; locks2.mkdir(mode=0o700)
    marker.create(locks2, status, 'b1-run', 'a' * 40)
    assert 'Track X B1 running' in status.read_text()


# ------------------------------------------------------------------------------------------- B2 grid verifier + ranking
def _spec(cid, switchable=True, role='candidate'):
    return {'id': cid, 'role': role, 'thinking_policy': {'mode': 'off', 'switchable': switchable, 'off_switch': switchable}}


def test_expected_grid_one_finalist_with_descriptive_rerun():
    from r1.exam.b2_batch import expected_grid
    cfg = {'b2_instances_per_node': 4, 'nodes': list(NODES)}
    grid, modes, seeds = expected_grid(cfg, ['gemma4_31b'], {'gemma4_31b': _spec('gemma4_31b')}, {'gemma4_31b': {}})
    assert seeds == [9011, 9012, 9013, 9014] and modes == {'gemma4_31b': ['off', 'on']}
    assert len(grid) == 2 * 3 * 4 and len(set(grid)) == len(grid)
    assert {(m, n) for (_, m, n, _) in grid} == {(m, n) for m in ('off', 'on') for n in NODES}
    # grammar-disabled thinking-on, or rank >= 3, means no rerun
    _, modes, _ = expected_grid(cfg, ['gemma4_31b'], {'gemma4_31b': _spec('gemma4_31b')},
                                {'gemma4_31b': {'thinking_disabled_due_grammar': True}})
    assert modes == {'gemma4_31b': ['off']}
    ids = [f'c{i}' for i in range(4)]
    _, modes, _ = expected_grid(cfg, ids, {c: _spec(c) for c in ids}, {c: {} for c in ids})
    assert [len(modes[c]) for c in ids] == [2, 2, 2, 1]


@pytest.mark.parametrize('cfg_change,finalists,match', [
    ({'b2_instances_per_node': 0}, ['g'], 'instance count'), ({'b2_instances_per_node': True}, ['g'], 'instance count'),
    ({'b2_instances_per_node': 90}, ['g'], 'instance count'), ({'nodes': NODES[:2]}, ['g'], 'three protocol nodes'),
    ({'nodes': NODES[:2] + ['track_g']}, ['g'], 'three protocol nodes'),
    ({'nodes': [NODES[0]] * 3}, ['g'], 'three protocol nodes'),
    ({}, [], 'finalist list'), ({}, ['g', 'g'], 'finalist list'), ({}, ['unknown'], 'not an eligible registry candidate'),
    ({}, ['anchor'], 'not an eligible registry candidate'), ({}, ['always'], 'cannot run thinking off'),
    ({}, ['absent'], 'not an eligible registry candidate'),
])
def test_expected_grid_refusals(cfg_change, finalists, match):
    from r1.exam.b2_batch import expected_grid
    cfg = {'b2_instances_per_node': 4, 'nodes': list(NODES), **cfg_change}
    specs = {'g': _spec('g'), 'anchor': _spec('anchor', role='anchor'), 'absent': _spec('absent'),
             'always': {'id': 'always', 'role': 'candidate', 'thinking_policy': {'mode': 'always_on'}}}
    eligible = {'g': {}, 'anchor': {}, 'always': {}}
    with pytest.raises(ValueError, match=match):
        expected_grid(cfg, finalists, specs, eligible)


def _final(node='digits_mlp', seed=9011, metrics=None, **change):
    metrics = metrics if metrics is not None else [0.5 + i / 100 for i in range(10)]
    numeric = all(type(v) in (int, float) for v in metrics)
    record = {'instance_id': f'{node}__s{seed}', 'node': node, 'seeds': list(range(9201, 9211)), 'metrics': metrics,
              'final_y': sum(metrics) / 10 if numeric and metrics else 0.5}
    record.update(change)
    return {'final_audits': [record]}


@pytest.mark.parametrize('root,match', [
    ({'final_audits': []}, 'exactly one final-Y audit'),
    ({'final_audits': [_final()['final_audits'][0]] * 2}, 'exactly one final-Y audit'),
    (_final(instance_id='digits_mlp__s9012'), 'another node or instance'),
    (_final(node='openml_ionosphere'), 'another node or instance'),
    (_final(seeds=list(range(9201, 9210))), '9201–9210'),
    (_final(seeds=[True] + list(range(9202, 9211))), '9201–9210'),
    (_final(seeds=list(range(9210, 9200, -1))), '9201–9210'),
    (_final(metrics=[0.5] * 9), 'ten finite'),
    (_final(metrics=[0.5] * 9 + [float('nan')]), 'ten finite'),
    (_final(metrics=[0.5] * 9 + [True]), 'ten finite'),
    (_final(metrics=[0.5] * 9 + ['0.5']), 'ten finite'),
    (_final(final_y=0.9), 'differs from the mean'),
    (_final(extra=1), 'fields differ'),
])
def test_final_audit_checks(root, match):
    from r1.exam.b2_batch import check_final_audit
    with pytest.raises(ValueError, match=match):
        check_final_audit(root, 'digits_mlp', 9011)


def test_final_audit_accepts_a_correct_record():
    from r1.exam.b2_batch import check_final_audit
    assert check_final_audit(_final(), 'digits_mlp', 9011)['final_y'] == pytest.approx(0.545)


def _b2_manifest(sha_, cid, ys, gpu=1.0):
    finals = [{'instance_id': f'{n}__s{s}', 'node': n, 'seeds': list(range(9201, 9211)), 'metrics': [y] * 10, 'final_y': y}
              for (n, s), y in zip([(n, s) for n in NODES for s in (9011, 9012, 9013, 9014)], ys)]
    return {'label': 'EXAM', 'phase': 'b2', 'status': 'COMPLETE', 'candidate': cid, 'source_label': 'fixture',
            'rule_sha256': sha_, 'final_audits': finals, 'gpu_hours': gpu, 'mode': 'off', 'purpose': 'primary'}


def test_b2_ranking_needs_a_verified_grid_and_matches_it():
    from r1.exam.analyze import _b2_summary_v2, load_rule
    rule, sha_ = load_rule(RULE_V2, hashlib.sha256(RULE_V2.read_bytes()).hexdigest())
    one = [_b2_manifest(sha_, 'gemma4_31b', [0.7] * 12)]
    with pytest.raises(ValueError, match='grid has not been verified'):
        _b2_summary_v2(one, rule, sha_)
    with pytest.raises(ValueError, match='grid has not been verified'):
        _b2_summary_v2(one, rule, sha_, grid={'verified': False})
    grid = {'verified': True, 'finalists': ['gemma4_31b'], 'nodes': list(NODES), 'instances_per_node': 4,
            'gpu_hours': {'gemma4_31b': 1.0}}
    out = _b2_summary_v2(one, rule, sha_, grid=grid)
    assert out['selection']['rule_top'] == 'gemma4_31b' and out['rows'][0]['instances'] == 12
    with pytest.raises(ValueError, match='differ from the verified finalist grid'):
        _b2_summary_v2(one + [_b2_manifest(sha_, 'other', [0.8] * 12)], rule, sha_, grid=grid)
    with pytest.raises(ValueError, match='does not cover the verified grid'):
        _b2_summary_v2([{**one[0], 'final_audits': one[0]['final_audits'][:11]}], rule, sha_, grid=grid)
    two = {**grid, 'finalists': ['a', 'b'], 'gpu_hours': {'a': 2.0, 'b': 1.0}}
    ranked = _b2_summary_v2([_b2_manifest(sha_, 'a', [0.7] * 12, gpu=2.0), _b2_manifest(sha_, 'b', [0.7] * 12, gpu=1.0)],
                            rule, sha_, grid=two)
    assert [r['candidate'] for r in ranked['rows']] == ['b', 'a']        # tie -> lower GPU-h


def test_b2_verified_summary_uses_the_batch_verifier(monkeypatch):
    from r1.exam import analyze
    import r1.exam.b2_batch as b2b
    sha_ = hashlib.sha256(RULE_V2.read_bytes()).hexdigest()
    grid = {'verified': True, 'finalists': ['gemma4_31b'], 'nodes': list(NODES), 'instances_per_node': 4,
            'gpu_hours': {'gemma4_31b': 1.0}}
    monkeypatch.setattr(b2b, 'verify_b2_batch', lambda batch, cfg, rule_sha: ([_b2_manifest(rule_sha, 'gemma4_31b', [0.6] * 12)],
                                                                             {'grid': grid, 'synthetic': True}))
    out = analyze.b2_summary_verified('/tmp/synthetic-b2-batch', {}, rule_path=RULE_V2, expected=sha_)
    assert out['execution_label'] == 'EVIDENCE' and out['batch_verification']['grid'] == grid
    assert out['selection']['rule_top'] == 'gemma4_31b'


def test_b2_batch_verifier_refuses_dryrun_and_unauthorized(monkeypatch, tmp_path):
    from r1.exam.b2_batch import verify_b2_batch
    with pytest.raises(ValueError, match='refuses DRYRUN'):
        verify_b2_batch(tmp_path, {'dryrun': True}, 's')
    def refused(*a): raise RuntimeError('STOP: synthetic authorization refused')
    monkeypatch.setattr(runtime, 'author_gate', refused)
    with pytest.raises(RuntimeError, match='authorization refused'):
        verify_b2_batch(tmp_path, {'authorizations': {'b2': 'n.md'}}, 's')


# ------------------------------------------------------------------------------------------- runner-level B2 STOPs
def _b2_runner(tmp_path, screen_data, dryrun=False, finalists_in_registry=('nt',)):
    from r1.tests.test_exam_x5_rule_v2 import FakeRunner, _runner_cfg, _spec, NONTHINK, v2
    from r1.exam.campaign import write_json
    from r1.exam.guards import digest_file
    rule, sha = v2()
    specs = [_spec(c, NONTHINK) for c in finalists_in_registry]
    screen = tmp_path / 'b1.json'
    write_json(screen, {'rule_sha256': sha, **screen_data})
    cfg = _runner_cfg(tmp_path, specs, list(finalists_in_registry),
                      extra={'b1_analysis': str(screen), 'b1_analysis_sha256': digest_file(screen), 'dryrun': dryrun})
    runner = FakeRunner(tmp_path, specs, cfg, rule, sha); runner.author_head = 'a' * 40
    return runner


@pytest.mark.parametrize('screen,match', [
    ({'finalists': ['nt'], 'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]}, 'verified complete-batch B1 analysis'),
    ({'phase': 'b1', 'execution_label': 'DRYRUN', 'batch_verification': {}, 'finalists': ['nt'],
      'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]}, 'verified complete-batch B1 analysis'),
    ({'phase': 'b1', 'execution_label': 'EVIDENCE', 'batch_verification': {}, 'finalists': [], 'rows': []}, 'non-empty, duplicate-free'),
    ({'phase': 'b1', 'execution_label': 'EVIDENCE', 'batch_verification': {}, 'finalists': ['nt', 'nt'], 'rows': []}, 'non-empty, duplicate-free'),
    ({'phase': 'b1', 'execution_label': 'EVIDENCE', 'batch_verification': {}, 'finalists': ['nt', 'gone'],
      'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]}, 'absent from the registry or Stage A pass set'),
])
def test_b2_runner_level_stops(tmp_path, screen, match):
    from r1.scripts.exam_runner import _evidence_unreviewed
    runner = _b2_runner(tmp_path, screen)
    with pytest.raises(runtime.PreparationStop, match=match):
        _evidence_unreviewed(runner, 'b2', None, False)
    assert not runner.served and not runner.roots


def test_b2_production_manifest_records_the_authorized_head(tmp_path):
    import json as _json
    from r1.scripts.exam_runner import _evidence_unreviewed
    runner = _b2_runner(tmp_path, {'phase': 'b1', 'execution_label': 'EVIDENCE', 'batch_verification': {}, 'finalists': ['nt'],
                                   'rows': [{'candidate': 'nt', 'b2_thinking_mode': 'off'}]})
    runner.author_head = None
    with pytest.raises(runtime.PreparationStop, match='B2 manifest requires the authorized checkout HEAD'):
        _evidence_unreviewed(runner, 'b2', None, False)
    runner.author_head = 'a' * 40; runner.state = {'completed': {}}
    _evidence_unreviewed(runner, 'b2', None, False)
    m = _json.loads((tmp_path / 'nt/b2_manifest.json').read_text())
    assert m['authorization_checkout_head'] == 'a' * 40 and m['phase'] == 'b2' and m['mode'] == 'off'
