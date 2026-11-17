"""R1-E1-OPENML-AMEND wiring into the c3_env_replay run path (fixture tests only).

No e1 run, no batch, no venv, no network: the verified mechanism and the
enforced network denial are replaced by fakes, and the real gate tests are in
``test_e1_openml_offline_mechanism.py`` / ``test_e1_offline_network.py``.
"""
import json
import sys

import pytest

from r1.c3 import e1_offline_network as NET
from r1.c3 import e1_openml_offline as M
from r1.scripts import c3_env_replay as R


@pytest.fixture(autouse=True)
def _replay_process_without_llm_modules(monkeypatch):
    """The real run happens in its own process; other tests may import LLM clients."""
    for name in [m for m in sys.modules if any(m == p or m.startswith(p + '.') for p in R.LLM_MODULES)]:
        monkeypatch.delitem(sys.modules, name)


class FakeMechanism:
    def __init__(self, *, fail_post_run=False):
        self.report = {'schema': M.SCHEMA, 'token': M.TOKEN,
                       'nodes': {node: {'dataset_id': dataset_id}
                                 for node, dataset_id in M.OPENML_IDS.items()}}
        self.calls = []
        self.fail_post_run = fail_post_run

    def verify_source_caches(self, harness):
        self.calls.append(('source_caches', str(harness)))
        if self.fail_post_run:
            raise M.MechanismStop('STOP: openml_sonar: source cache changed during the replay: x')
        return {node: 'digest' for node in M.OPENML_IDS}

    def verify_case_cache(self, node, cache_root, phase):
        self.calls.append((node, phase))
        return {'node': node, 'phase': phase}


def _cases(node='openml_sonar', n=16):
    return [{'case_id': f'{node}__s100:t001:c{i}', 'node': node, 'metric_key': 'val_auc',
             'recorded_token': '0.7', 'recorded_value': 0.7, 'files': {},
             'train_seed': 104, 'split_seed': 104, 'budget_index': 1} for i in range(n)]


class RunFixture:
    def __init__(self, tmp_path, monkeypatch, *, cases, mechanism=None, prepare_error=None):
        self.paper = tmp_path / 'paper'
        self.paper.mkdir()
        self.batch = tmp_path / 'batch'
        self.harness = self.batch / 'autoresearch_harness'
        self.harness.mkdir(parents=True)
        self.out = tmp_path / 'out'
        self.scratch = tmp_path / 'scratch'
        self.order, self.seen_mechanisms, self.plan_seen = [], [], []
        monkeypatch.setattr(R, 'BATCH', str(self.batch))
        monkeypatch.setattr(R, 'verify_corpus',
                            lambda paper: {'index_doc': {'nodes': list('abcdefgh')}, 'sweeps': {}})
        monkeypatch.setattr(R, 'verify_collector_binding', lambda paper: {})
        monkeypatch.setattr(R, 'select_cases', lambda *args: cases)
        monkeypatch.setattr(R.platform, 'node', lambda: 'deepthought.etl.kit.edu')
        monkeypatch.setattr(R, 'check_environment', lambda batch, harness: {'worker_path': '/bin'})
        monkeypatch.setattr(R, 'check_harness', lambda harness, nodes: {'data_caches_sha256': {}})
        monkeypatch.setattr(R, 'check_resources', lambda out, scratch, minimum: {})
        monkeypatch.setenv('AR_HARNESS_ROOT', str(self.harness))
        monkeypatch.setenv('PYTHONDONTWRITEBYTECODE', '1')
        monkeypatch.delenv(R.OPENML_MECHANISM_ENV, raising=False)

        def enforce():
            self.order.append('network_enforce')
            return {'enforced': True, 'schema': NET.SCHEMA}

        def reverify():
            self.order.append('network_reverify')
            return {'denied': True, 'seccomp_mode': 2}

        def prepare(paper, harness, batch, commit):
            self.order.append('identity_prepare')
            assert batch == self.batch and paper == self.paper and harness == self.harness
            if prepare_error is not None:
                raise prepare_error
            return mechanism or FakeMechanism()

        monkeypatch.setattr(NET, 'enforce', enforce)
        monkeypatch.setattr(NET, 'reverify', reverify)
        monkeypatch.setattr(M, 'prepare', prepare)

    def execute(self, calls):
        def execute(case, node_source, scratch, env, *, mechanism=None):
            self.plan_seen.append((self.out / 'replay_plan.json').is_file())
            self.seen_mechanisms.append(mechanism)
            calls.append(case['case_id'])
            return {'case_id': case['case_id'], 'success': True, 'changed_files': [], 'failure': None,
                    'replay_token': '0.7', 'recorded_token': '0.7', 'replay_value': 0.7,
                    'recorded_value': 0.7, 'wall_seconds': 0.0, 'data_cache_unchanged': True,
                    'openml_offline_cache_checks': [], 'log_text': 'val_auc: 0.7\n'}
        return execute

    def run(self, monkeypatch, *, dry_run=False, token=None, execute=None, env_token=None):
        if env_token is not None:
            monkeypatch.setenv(R.OPENML_MECHANISM_ENV, env_token)
        return R.run(self.paper, self.out, dry_run=dry_run, harness=self.harness, batch=self.batch,
                     scratch=self.scratch, min_free_bytes=1, execute=execute or execute_case_placeholder,
                     openml_mechanism=token)


def execute_case_placeholder(*_args, **_kwargs):  # replaced by RunFixture.execute in every test
    raise AssertionError('the real execute_case must not run in wiring tests')


# ---------------------------------------------------------------------------- flag behaviour

def test_reviewed_flag_lifts_the_openml_stop_and_runs_all_cases(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    calls = []
    summary = fixture.run(monkeypatch, token=M.TOKEN, execute=fixture.execute(calls))
    assert summary['verdict'] == 'PASS' and summary['cases_passed'] == 16
    assert len(calls) == 16 and all(mechanism is not None for mechanism in fixture.seen_mechanisms)
    assert fixture.order[:2] == ['network_enforce', 'identity_prepare']  # (b) before (ii)
    assert all(fixture.plan_seen)  # the plan was declared before the first case
    plan = json.loads((fixture.out / 'replay_plan.json').read_text())
    assert plan['openml_offline_mechanism']['state'] == 'VERIFIED'
    assert plan['openml_offline_mechanism']['token'] == M.TOKEN
    assert plan['environment']['openml_offline_mechanism']['network']['enforced'] is True
    assert summary['openml_offline_mechanism']['network_enforced'] is True
    assert summary['openml_offline_mechanism']['post_run']['network']['denied'] is True
    assert (fixture.out / 'summary.json').is_file()


def test_environment_token_enables_the_same_mechanism(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    summary = fixture.run(monkeypatch, token=None, env_token=M.TOKEN,
                          execute=fixture.execute([]))
    assert summary['verdict'] == 'PASS' and 'identity_prepare' in fixture.order


def test_absent_flag_keeps_the_original_openml_stop(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    with pytest.raises(R.Stop, match='no replay scheduled'):
        fixture.run(monkeypatch, token=None, execute=fixture.execute([]))
    assert fixture.order == [] and not fixture.out.exists()


def test_unknown_flag_token_is_a_stop(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    with pytest.raises(R.Stop, match='unknown OpenML offline mechanism token'):
        fixture.run(monkeypatch, token='r1-e1-openml-amend-20260101', execute=fixture.execute([]))
    assert fixture.order == []


def test_dry_run_with_the_flag_defers_the_proof_to_the_host(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    result = fixture.run(monkeypatch, dry_run=True, token=M.TOKEN)
    assert result['label'] == 'DRYRUN' and result['cases'] == 16
    plan = json.loads((fixture.out / 'replay_plan.json').read_text())
    assert plan['openml_offline_mechanism']['state'] == 'DEFERRED_TO_HOST'
    assert fixture.order == []  # no network filter and no identity load in a dry run


def test_dry_run_rejects_an_unknown_flag_token(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    with pytest.raises(R.Stop, match='unknown OpenML offline mechanism token'):
        fixture.run(monkeypatch, dry_run=True, token='not-the-reviewed-token')
    assert not fixture.out.exists()


def test_non_openml_run_is_unchanged_and_needs_no_flag(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases(node='digits_mlp'))
    summary = fixture.run(monkeypatch, token=None, execute=fixture.execute([]))
    assert summary['verdict'] == 'PASS'
    assert 'openml_offline_mechanism' not in json.loads((fixture.out / 'replay_plan.json').read_text())
    assert fixture.order == []


# ---------------------------------------------------------------------------- STOP wiring

def test_network_denial_failure_is_a_stop_before_identity_or_output(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())

    def enforce():
        raise NET.NetworkDenialStop('STOP: seccomp filter installation failed: errno 1 (EPERM)')

    monkeypatch.setattr(NET, 'enforce', enforce)
    with pytest.raises(R.Stop, match='seccomp filter installation failed'):
        fixture.run(monkeypatch, token=M.TOKEN, execute=fixture.execute([]))
    assert not fixture.out.exists()


def test_identity_prepare_failure_is_a_stop_before_output(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases(),
                         prepare_error=M.MechanismStop('STOP: cache file SHA-256 differs from the audit: x'))
    with pytest.raises(R.Stop, match='cache file SHA-256 differs'):
        fixture.run(monkeypatch, token=M.TOKEN, execute=fixture.execute([]))
    assert not fixture.out.exists()


def test_wrong_preserved_batch_is_a_stop_when_the_mechanism_is_enabled(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases())
    monkeypatch.setattr(R, 'BATCH', '/ceph/not_the_preserved_batch')
    with pytest.raises(R.Stop, match='preserved sweep-1 batch'):
        fixture.run(monkeypatch, token=M.TOKEN, execute=fixture.execute([]))
    assert not fixture.out.exists()


def test_post_run_identity_failure_stops_the_run(tmp_path, monkeypatch):
    fixture = RunFixture(tmp_path, monkeypatch, cases=_cases(), mechanism=FakeMechanism(fail_post_run=True))
    summary = fixture.run(monkeypatch, token=M.TOKEN, execute=fixture.execute([]))
    assert summary['verdict'] == 'STOP' and 'source cache changed' in summary['stop']
    assert (fixture.out / 'STOP.json').is_file() and not (fixture.out / 'summary.json').exists()
    assert summary['openml_offline_mechanism']['post_run'] is None
    assert len(fixture.seen_mechanisms) == 16  # the 16 cases ran; the STOP is post-run


# ---------------------------------------------------------------------------- executor binding

def test_mechanism_executor_keeps_the_plain_executor_when_disabled():
    def execute(*_args, **_kwargs):
        return 'ran'

    assert R._mechanism_executor(execute, None) is execute


def test_mechanism_executor_injects_the_verified_object():
    seen = []

    def execute(case, node_source, scratch, env, *, mechanism=None):
        seen.append(mechanism)
        return 'ran'

    mechanism = FakeMechanism()
    bound = R._mechanism_executor(execute, mechanism)
    assert bound('case', 'harness', 'scratch', {}) == 'ran'
    assert seen == [mechanism]
