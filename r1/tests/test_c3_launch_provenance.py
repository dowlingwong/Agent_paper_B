"""Launch provenance and local-work retention for the Deepthought C3 runner."""
import hashlib
import json
import tarfile
import types
from pathlib import Path

import pytest

from r1.liveness import __main__ as live
from r1.headroom import e1b_collect as collect
from r1.scripts import c3_label_sweep as sweep
from r1.scripts import dryrun_guard


def test_liveness_writes_launch_manifest_before_first_campaign(tmp_path, monkeypatch):
    pin = {'paper_commit': 'a' * 40, 'harness_commit': 'b' * 40}
    out = tmp_path / 'out'
    args = types.SimpleNamespace(runs=10, out=str(out), work=str(tmp_path / 'work'),
                                 manager='scripted', manager_model=None, proposal_schema=None,
                                 transport_max_attempts=None, nodes=['digits_mlp'], instances=1,
                                 memory_mode='none', extra_manifest=json.dumps({'launch_provenance': pin}))
    monkeypatch.setattr(dryrun_guard, 'validate_dryrun', lambda: False)
    class FirstJob(Exception): pass
    def first_job(**kwargs):
        assert json.loads((out / 'manifest.json').read_text())['launch_provenance'] == pin
        raise FirstJob()
    monkeypatch.setattr(collect, 'run_root', first_job)
    with pytest.raises(FirstJob):
        live.run_campaigns(args)
    assert json.loads((out / 'manifest.json').read_text())['launch_provenance'] == pin
    with pytest.raises(RuntimeError, match='already exists'):
        live.run_campaigns(args)


def test_local_work_archive_preserves_final_and_interrupted_references(tmp_path):
    work = tmp_path / 'local'; out = tmp_path / 'out'; out.mkdir()
    (out / 'manifest.json').write_text('{}')
    expected = {}
    for relative in ('roots/n1', 'interrupted/01/roots/n1'):
        root = work / relative; root.mkdir(parents=True)
        patch = root / 'patch.diff'; patch.write_text('change ' + relative)
        log = root / 'run.log'; log.write_text('log ' + relative)
        ledger = root / 'root_trials.jsonl'
        original = work / 'roots' / root.name
        ledger.write_text(json.dumps({'patch_ref': str(original / 'patch.diff'),
                                      'raw_log_ref': str(original / 'run.log')}) + '\n')
        for path in (patch, log, ledger): expected['work/' + str(path.relative_to(work))] = path.read_bytes()
    runner = object.__new__(sweep.SweepRunner)
    runner.archive_work_references(out, work)
    manifest = json.loads((out / 'manifest.json').read_text())['local_work_archive']
    archive = out / manifest['path']
    assert manifest['sha256'] == hashlib.sha256(archive.read_bytes()).hexdigest()
    index = json.loads((out / manifest['index']).read_text())
    assert manifest['index_sha256'] == hashlib.sha256((out / manifest['index']).read_bytes()).hexdigest()
    old_refs = [r for r in index['references'] if r['ledger'].startswith('interrupted/')]
    assert len(old_refs) == 2 and all(r['member'].startswith('work/interrupted/01/roots/n1/') for r in old_refs)
    with tarfile.open(archive) as tar:
        assert set(tar.getnames()) == set(expected)
        for name, contents in expected.items(): assert tar.extractfile(name).read() == contents


def test_local_work_archive_refuses_missing_or_external_references(tmp_path):
    work = tmp_path / 'local'; root = work / 'roots/n1'; root.mkdir(parents=True)
    out = tmp_path / 'out'; out.mkdir(); (out / 'manifest.json').write_text('{}')
    external = tmp_path / 'outside.log'; external.write_text('outside')
    (root / 'root_trials.jsonl').write_text(json.dumps({'raw_log_ref': str(external)}) + '\n')
    runner = object.__new__(sweep.SweepRunner)
    with pytest.raises(sweep.Stop, match='outside local work'):
        runner.archive_work_references(out, work)
    assert not (out / 'temporary_provenance.tar.gz').exists()


def test_manifest_mismatch_or_missing_is_a_stop(tmp_path):
    runner = object.__new__(sweep.SweepRunner)
    # SweepRunner.__init__ always sets ``label``; the EVIDENCE classification
    # check in check_launch_manifest (codex/b2-repair-20261031) reads it.
    runner.label = 'ENGINEERING_ONLY'
    runner.state = {'launch_provenance': {'paper_commit': 'a' * 40}}
    with pytest.raises(sweep.Stop, match='missing or invalid'):
        runner.check_launch_manifest(tmp_path)
    (tmp_path / 'manifest.json').write_text(json.dumps({'launch_provenance': {'paper_commit': 'b' * 40}}))
    with pytest.raises(sweep.Stop, match='provenance mismatch'):
        runner.check_launch_manifest(tmp_path)
    (tmp_path / 'manifest.json').write_text(json.dumps({'launch_provenance': runner.state['launch_provenance']}))
    runner.check_launch_manifest(tmp_path)


def test_earlier_collector_is_detected_by_local_scratch_path(tmp_path, monkeypatch):
    runner = object.__new__(sweep.SweepRunner)
    runner.batch = tmp_path / 'durable'; runner.scratch = tmp_path / 'local'
    monkeypatch.setattr(sweep, 'proc_table', lambda: {90001: (1, 'python -m r1.headroom.e1b_collect --work ' + str(runner.scratch))})
    assert runner.earlier_processes()[0]['pid'] == 90001


def test_resume_checks_pins_before_any_root_work(tmp_path, monkeypatch):
    runner = object.__new__(sweep.SweepRunner)
    runner.host = 'other-host'; runner.dryrun = False
    runner.config = {'noise_source': {'path': 'noise', 'sha256': 'a' * 64}}
    runner.paper = tmp_path / 'paper'; runner.harness = tmp_path / 'harness'
    runner.config_path = tmp_path / 'config.json'; runner.config_path.write_text('{"x":1}')
    runner.scratch = tmp_path / 'local'; runner.scratch.mkdir()
    runner.state = {'scratch_root': str(runner.scratch), 'launch_provenance': {
        'paper_commit': 'a' * 40, 'harness_commit': 'b' * 40,
        'config_sha256': hashlib.sha256(runner.config_path.read_bytes()).hexdigest(),
        'model_sha256': 'c' * 64, 'llamacpp_build': 'build'}}
    runner.check_tracked_clean = lambda: None
    runner.check_paper_history = lambda commit: None
    runner.git = lambda repo, *args: 'b' * 40
    runner.llamacpp_pins = lambda: {'model_sha256': 'c' * 64, 'build': {'version_line': 'build'}}
    monkeypatch.setattr(sweep.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0))
    runner.verify_resumed_provenance()
    runner.config_path.write_text('{"x":2}')
    with pytest.raises(sweep.Stop, match='configuration differs'):
        runner.verify_resumed_provenance()
    runner.config_path.write_text('{"x":1}')
    runner.llamacpp_pins = lambda: {'model_sha256': 'd' * 64, 'build': {'version_line': 'build'}}
    with pytest.raises(sweep.Stop, match='model or build'):
        runner.verify_resumed_provenance()


def test_interrupted_reference_missing_never_falls_back_to_new_root(tmp_path):
    work = tmp_path / 'work'; current = work / 'roots/n1'; current.mkdir(parents=True)
    (current / 'patch.diff').write_text('new run')
    old = work / 'interrupted/01/roots/n1'; old.mkdir(parents=True)
    (old / 'root_trials.jsonl').write_text(json.dumps({'patch_ref': str(current / 'patch.diff')}) + '\n')
    out = tmp_path / 'out'; out.mkdir(); (out / 'manifest.json').write_text('{}')
    runner = object.__new__(sweep.SweepRunner)
    with pytest.raises(sweep.Stop, match='missing or outside local work'):
        runner.archive_work_references(out, work)
    assert not (out / 'temporary_provenance.tar.gz').exists()


@pytest.mark.parametrize('mode', ['append_only_summary', 'none'])
def test_each_sweep_passes_the_original_launch_provenance(tmp_path, mode, monkeypatch):
    config = sweep.load_config(None); config['nodes'] = ['digits_mlp']
    runner = sweep.SweepRunner(config, batch=tmp_path/'batch', paper=tmp_path/'paper',
                               harness=tmp_path/'harness', python='py')
    pin = {'paper_commit': 'a' * 40, 'harness_commit': 'b' * 40, 'config_sha256': 'c' * 64,
           'model_sha256': 'd' * 64, 'llamacpp_build': 'build'}
    runner.state.update(launch_provenance=pin, steps={'liveness': {'eligible_nodes': ['digits_mlp'],
                        'out': 'live'}, f'sweep_{mode}': {}})
    runner.state['ollama'] = {}
    runner.verify_resumed_provenance = lambda: None
    manifest_checks = []
    runner.check_launch_manifest = lambda out, *, engineering_liveness=False: manifest_checks.append(engineering_liveness)
    runner.require_liveness = lambda *a: None
    runner.save = lambda: None
    runner.manager_model_args = lambda: []
    class Captured(Exception): pass
    seen = {}
    def capture(argv, *a):
        seen.update(json.loads(argv[argv.index('--extra-manifest') + 1])); raise Captured()
    runner.collect = capture
    with pytest.raises(Captured): runner.sweep(mode)
    # The pin is the saved launch SHA even if the checkout has acquired result commits.
    assert seen['launch_provenance'] == pin
    # The resumed liveness manifest is checked as engineering liveness, never as an EVIDENCE sweep manifest.
    assert manifest_checks == [True]


def test_watchdog_refuses_manifest_mismatch_before_restart_or_move(tmp_path):
    runner = object.__new__(sweep.SweepRunner)
    runner.state = {'launch_provenance': {'paper_commit': 'a' * 40}}
    runner.restart_service = lambda *a: pytest.fail('must not restart service')
    runner.resume_interrupted = lambda *a, **k: pytest.fail('must not move or rerun roots')
    out = tmp_path / 'out'; out.mkdir()
    (out / 'manifest.json').write_text(json.dumps({'launch_provenance': {'paper_commit': 'b' * 40}}))
    with pytest.raises(sweep.Stop, match='provenance mismatch'):
        runner.runner_lost({}, out, tmp_path/'work', 'sweep_none')


def test_resume_refuses_missing_provenance_on_deepthought():
    runner = object.__new__(sweep.SweepRunner)
    runner.host = 'deepthought'; runner.dryrun = False
    runner.state = {}; runner.config = {'noise_source': None}
    with pytest.raises(sweep.Stop, match='lacks launch provenance'):
        runner.verify_resumed_provenance()


def test_preparation_record_must_match_both_tested_commits(tmp_path):
    runner = object.__new__(sweep.SweepRunner); runner.batch = tmp_path
    paper, harness = 'a' * 40, 'b' * 40
    record = {'ok': True, 'suites_skipped_dryrun': False, 'paper_head': paper, 'harness_head': harness}
    path = tmp_path/'prepare.json'; path.write_text(json.dumps(record))
    runner.check_prepared_heads(paper, harness)
    for update in ({'paper_head': 'c'*40}, {'harness_head': 'd'*40}, {'ok': False},
                   {'suites_skipped_dryrun': True}):
        path.write_text(json.dumps({**record, **update}))
        with pytest.raises(sweep.Stop, match='does not match'):
            runner.check_prepared_heads(paper, harness)


def test_deepthought_preconditions_refuse_untested_commits_before_service(tmp_path):
    runner = object.__new__(sweep.SweepRunner)
    runner.host = 'deepthought'; runner.dryrun = False; runner.paper = tmp_path/'paper'
    runner.batch = tmp_path/'batch'; runner.batch.mkdir(); runner.state = {'steps': {'preconditions': {}}}
    plan = runner.paper/'docs/r1/PLAN.md'; plan.parent.mkdir(parents=True); plan.write_text(' '.join(sweep.ROWS))
    runner.check_noise_source = lambda: None
    runner.check_heads = lambda: ('a'*40, 'b'*40)
    runner.start_service = lambda: pytest.fail('must not start model service')
    with pytest.raises(sweep.Stop, match='preparation record'):
        runner.preconditions()
    (runner.batch/'prepare.json').write_text(json.dumps({'ok': True, 'paper_head': 'c'*40,
                                                          'harness_head': 'b'*40}))
    with pytest.raises(sweep.Stop, match='tested launch commits'):
        runner.preconditions()


def test_resume_paper_history_allows_only_recorded_result_commits(tmp_path):
    import subprocess
    repo = tmp_path/'paper'; repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
    git('init', '-q'); git('config', 'user.name', 'Test'); git('config', 'user.email', 'test@example.invalid')
    (repo/'root.txt').write_text('original'); git('add', '.'); git('commit', '-qm', 'launch')
    launch = git('rev-parse', 'HEAD')
    out = repo/'results/r1/engineering/result.txt'; out.parent.mkdir(parents=True); out.write_text('result')
    git('add', '.'); git('commit', '-qm', 'runner result'); result = git('rev-parse', 'HEAD')
    runner = object.__new__(sweep.SweepRunner); runner.paper = repo
    runner.state = {'steps': {'liveness': {'commit': result}}}
    runner.check_paper_history(launch)
    runner.state['steps']['liveness']['commit'] = 'f'*40
    with pytest.raises(sweep.Stop, match='history differs'): runner.check_paper_history(launch)
    runner.state['steps']['liveness']['commit'] = result
    (repo/'root.txt').write_text('changed'); git('add', '.'); git('commit', '-qm', 'unrelated')
    with pytest.raises(sweep.Stop, match='non-result changes'): runner.check_paper_history(launch)


def test_interrupted_truncated_tail_is_archived_and_identified(tmp_path):
    work = tmp_path/'work'; old = work/'interrupted/01/roots/n1'; old.mkdir(parents=True)
    out = tmp_path/'out'; out.mkdir(); (out/'manifest.json').write_text('{}')
    ledger = old/'root_trials.jsonl'; tail = b'{"budget_index": 2, "patch_ref": '
    ledger.write_bytes(b'{"budget_index": 1}\n' + tail)
    art = old/'art/trial-002'; art.mkdir(parents=True)
    (art/'patch.diff').write_text('partial patch'); (art/'run.log').write_text('partial log')
    events = old/'root_events.jsonl'
    event_tail = b'{"event_type":"llm_call", "payload":'
    events.write_bytes(b'{"event_type":"llm_call"}\n' + event_tail)
    runner = object.__new__(sweep.SweepRunner); runner.archive_work_references(out, work)
    m = json.loads((out/'manifest.json').read_text())['local_work_archive']
    index = json.loads((out/m['index']).read_text())
    assert index['truncated_interrupted_tails'] == [{'ledger':'interrupted/01/roots/n1/root_trials.jsonl',
        'line':2, 'bytes':len(tail), 'sha256':hashlib.sha256(tail).hexdigest()}]
    assert index['truncated_interrupted_events'][0]['sha256'] == hashlib.sha256(event_tail).hexdigest()
    assert runner.interrupted_events(events)[0] == 1
    with tarfile.open(out/m['path']) as tar:
        assert tar.extractfile('work/interrupted/01/roots/n1/root_trials.jsonl').read() == ledger.read_bytes()
        assert tar.extractfile('work/interrupted/01/roots/n1/art/trial-002/patch.diff').read() == b'partial patch'
        assert tar.extractfile('work/interrupted/01/roots/n1/art/trial-002/run.log').read() == b'partial log'
        assert tar.extractfile('work/interrupted/01/roots/n1/root_events.jsonl').read() == events.read_bytes()


def test_incomplete_nonfinal_ledger_line_is_a_stop(tmp_path):
    work=tmp_path/'work'; old=work/'interrupted/01/roots/n1'; old.mkdir(parents=True)
    (old/'root_trials.jsonl').write_bytes(b'{bad}\n{"budget_index":1}\n')
    out=tmp_path/'out'; out.mkdir(); (out/'manifest.json').write_text('{}')
    runner=object.__new__(sweep.SweepRunner)
    with pytest.raises(sweep.Stop, match='malformed provenance ledger'):
        runner.archive_work_references(out, work)
    assert not (out/'temporary_provenance.tar.gz').exists()


def test_interrupted_unrecorded_artifacts_are_archived_without_truncated_ledger(tmp_path):
    work=tmp_path/'work'; old=work/'interrupted/01/roots/n1'; old.mkdir(parents=True)
    (old/'root_trials.jsonl').write_text('{"budget_index":1}\n')
    art=old/'art/trial-002'; art.mkdir(parents=True); (art/'run.log').write_text('unrecorded')
    out=tmp_path/'out'; out.mkdir(); (out/'manifest.json').write_text('{}')
    runner=object.__new__(sweep.SweepRunner); runner.archive_work_references(out, work)
    with tarfile.open(out/'temporary_provenance.tar.gz') as tar:
        assert tar.extractfile('work/interrupted/01/roots/n1/art/trial-002/run.log').read() == b'unrecorded'


def test_interrupted_symlink_root_is_rejected(tmp_path):
    work=tmp_path/'work'; roots=work/'interrupted/01/roots'; roots.mkdir(parents=True)
    outside=tmp_path/'outside'; outside.mkdir(); (roots/'unsafe').symlink_to(outside, target_is_directory=True)
    active=work/'roots/n1'; active.mkdir(parents=True); (active/'root_trials.jsonl').write_text('{}\n')
    out=tmp_path/'out'; out.mkdir(); (out/'manifest.json').write_text('{}')
    runner=object.__new__(sweep.SweepRunner)
    with pytest.raises(sweep.Stop, match='unsafe interrupted root'):
        runner.archive_work_references(out, work)


def test_interrupted_nonfinal_corrupt_event_is_a_stop(tmp_path):
    path=tmp_path/'root_events.jsonl'; path.write_bytes(b'{bad}\n{"event_type":"llm_call"}\n')
    with pytest.raises(sweep.Stop, match='malformed interrupted event ledger'):
        sweep.SweepRunner.interrupted_events(path)


def test_orphan_worker_in_scratch_is_detected_before_resume(tmp_path, monkeypatch):
    runner=object.__new__(sweep.SweepRunner); runner.batch=tmp_path/'batch'; runner.scratch=tmp_path/'scratch'
    monkeypatch.setattr(sweep, 'proc_table', lambda: {90002: (1, 'python train.py')})
    monkeypatch.setattr(sweep, 'owned_process_cwd', lambda pid: runner.scratch/'roots/n1/worker')
    assert runner.earlier_processes()[0]['pid'] == 90002
    monkeypatch.setattr(sweep, 'owned_process_cwd', lambda pid: tmp_path/'other')
    assert runner.earlier_processes() == []


def test_watchdog_refuses_orphan_before_service_restart_or_root_move(tmp_path):
    runner=object.__new__(sweep.SweepRunner); runner.state={}
    runner.earlier_processes=lambda: [{'pid': 90002, 'cmdline': 'python train.py'}]
    runner.restart_service=lambda *a: pytest.fail('must not restart service')
    runner.resume_interrupted=lambda *a, **k: pytest.fail('must not move roots')
    with pytest.raises(sweep.Stop, match='remain alive'):
        runner.runner_lost({}, tmp_path/'out', tmp_path/'work', 'sweep_none')


def test_liveness_stamped_work_references_are_archived(tmp_path):
    work=tmp_path/'work'; root=work/'liveness_20261027T000000Z/roots/n1'; root.mkdir(parents=True)
    log=root/'run.log'; log.write_text('liveness log')
    (root/'root_trials.jsonl').write_text(json.dumps({'raw_log_ref':str(log)})+'\n')
    out=tmp_path/'out'; out.mkdir(); (out/'manifest.json').write_text('{}')
    runner=object.__new__(sweep.SweepRunner); runner.archive_work_references(out,work)
    manifest=json.loads((out/'manifest.json').read_text())['local_work_archive']
    index=json.loads((out/manifest['index']).read_text())
    assert index['references'][0]['member']=='work/liveness_20261027T000000Z/roots/n1/run.log'
    with tarfile.open(out/manifest['path']) as tar:
        assert tar.extractfile(index['references'][0]['member']).read()==b'liveness log'


def test_fake_config_uses_fixture_uuid_without_mutating_real_host_config(tmp_path):
    from r1.scripts import c3_sweep_dryrun as dryrun
    config_path=Path(__file__).resolve().parents[1]/'scripts/configs/c3_sweep_deepthought.json'
    original=config_path.read_bytes(); base=json.loads(original)
    derived, changed=dryrun.dryrun_config(base, tmp_path, tmp_path/'bin')
    assert derived['gpu_uuid']=='GPU-DRYRUN' and 'gpu_uuid' in changed
    assert base['gpu_uuid']=='GPU-2516f262-6a75-eee3-26ee-b2e8d908c07d'
    assert config_path.read_bytes()==original


def test_fake_checker_rejects_schema_or_provenance_mismatch(tmp_path):
    from r1.scripts import c3_sweep_dryrun as dry
    pin={'paper_commit':'a'*40}; schema='manager_proposal/v1'; model='llamacpp/r1-manager'
    config={'llamacpp':{'model_alias':'r1-manager','model_sha256':'b'*64,'build':'build'}, 'proposal_schema':schema}
    manager={'model':model,'proposal_schema':schema}; seed={'kind':'llamacpp_seed'}
    block={'backend':'llamacpp','llama_server':{'model_sha256':'b'*64},'llamacpp_build':'build'}
    steps={}
    for name in ('sweep_append_only_summary','sweep_none','liveness'):
        out=tmp_path/name; out.mkdir(); steps[name]={'out':str(out)}
        manifest={'manager':manager,'seed_policy':seed,'launch_provenance':pin}
        if name!='liveness': manifest['c3_label_sweep']=block
        (out/'manifest.json').write_text(json.dumps(manifest))
    index=tmp_path/'index.json'; index.write_text(json.dumps({'launch_provenance':pin,'manager':{
        'backend':'llamacpp','model':model,'model_sha256':'b'*64,'llamacpp_build':'build','proposal_schema':schema}}))
    steps['index']={'path':str(index)}; result={'state':{'steps':steps,'launch_provenance':pin},'config':config}
    assert dry.check_llamacpp_manifests(result)['manager_model']==model
    for name in ('sweep_append_only_summary','sweep_none','liveness'):
        path=Path(steps[name]['out'])/'manifest.json'; data=json.loads(path.read_text())
        data['manager']['proposal_schema']='wrong'; path.write_text(json.dumps(data))
        with pytest.raises(AssertionError): dry.check_llamacpp_manifests(result)
        data['manager']['proposal_schema']=schema; data['launch_provenance']={'paper_commit':'wrong'}
        path.write_text(json.dumps(data))
        with pytest.raises(AssertionError): dry.check_llamacpp_manifests(result)
        data['launch_provenance']=pin; path.write_text(json.dumps(data))
