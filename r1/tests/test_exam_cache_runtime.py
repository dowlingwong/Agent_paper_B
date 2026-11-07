"""Identity snapshots are not cold/freshness proof; only synthetic files/PIDs.

The guardian->worker edge is authorised without kcmp: a /proc
PID/start-tick/state witness plus FD dev/ino/uid plus flock re-lock and
independent-contender tests (method ``flock_relock_while_guardian_live``).  The
runner/worker->native-server edge is kcmp-proved in the legal
ancestor->descendant direction.  All /proc trees here are synthetic fixtures; no
real process, model or GPU is involved.
"""
import hashlib
import json
import os
from types import SimpleNamespace

import pytest

from r1.exam import cache_proc
from r1.exam import cache_runtime as runtime
from r1.exam import cooperative_lease as cl
from r1.exam.cooperative_lease import LeaseStop

PROC_PID = 4242
RUNNER_PID = 55555
SERVER_PID = 66666


# -- synthetic /proc and lease fixtures ---------------------------------------

def _proc_entry(proc_root, pid, ticks, *, ppid=1, state='S'):
    directory = os.path.join(proc_root, str(pid))
    os.makedirs(os.path.join(directory, 'fd'), exist_ok=True)
    fields = [state, str(ppid), '1', '1', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0',
              '20', '0', '0', str(ticks)]
    with open(os.path.join(directory, 'stat'), 'w') as handle:
        handle.write(f'{pid} (synthetic) ' + ' '.join(fields) + '\n')
    with open(os.path.join(directory, 'status'), 'w') as handle:
        handle.write(f'Name:\tsynthetic\nState:\t{state} (sleeping)\nUid:\t{os.getuid()}\t{os.getuid()}'
                     f'\t{os.getuid()}\t{os.getuid()}\n')
    return directory


def _proc_fd(proc_root, pid, fd, target):
    directory = os.path.join(proc_root, str(pid), 'fd')
    os.makedirs(directory, exist_ok=True)
    link = os.path.join(directory, str(fd))
    # Every synthetic proc table starts empty; never remove a prior fixture.
    assert not os.path.lexists(link)
    os.symlink(target, link)


def lease_fixture(tmp_path):
    path = tmp_path / 'synthetic.lock'
    path.touch()
    fd, identity = cl.acquire_existing(path)
    return path, fd, identity


def witness_env(tmp_path, fd, lease_path, *, guardian_pid=PROC_PID, ticks=111, state='S', proc_root=None):
    proc_root = str(proc_root or tmp_path / 'proc')
    _proc_entry(proc_root, guardian_pid, ticks, ppid=1, state=state)
    _proc_fd(proc_root, guardian_pid, fd, str(lease_path))
    os.environ.update({
        'TRACKX_GPU_LEASE_FD': str(fd), 'TRACKX_GPU_LEASE_DEV': str(os.fstat(fd).st_dev),
        'TRACKX_GPU_LEASE_INO': str(os.fstat(fd).st_ino), 'TRACKX_GPU_LEASE_UID': str(os.fstat(fd).st_uid),
        'TRACKX_GPU_GUARDIAN_PID': str(guardian_pid), 'TRACKX_GPU_GUARDIAN_START_TICKS': str(ticks)})
    return proc_root


@pytest.fixture
def authorized():
    token = runtime._authorized.set(True)
    yield
    runtime._authorized.reset(token)


LEASE_ENV_KEYS = ('TRACKX_GPU_LEASE_FD', 'TRACKX_GPU_LEASE_DEV', 'TRACKX_GPU_LEASE_INO',
                  'TRACKX_GPU_LEASE_UID', 'TRACKX_GPU_GUARDIAN_PID', 'TRACKX_GPU_GUARDIAN_START_TICKS',
                  'TRACKX_LEASE_EVIDENCE_DIR')


@pytest.fixture(autouse=True)
def _clear_lease_env():
    """Leave no lease environment behind for later test modules."""
    saved = {key: os.environ.get(key) for key in LEASE_ENV_KEYS}
    for key in LEASE_ENV_KEYS:
        os.environ.pop(key, None)
    yield
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def fake_ticks(proc_root):
    return lambda pid: cache_proc.process_start_ticks(pid, proc_root=proc_root)


# -- guardian witness ---------------------------------------------------------

def test_guardian_witness_reports_method_and_rejects_every_ambiguity(tmp_path, monkeypatch):
    lease_path, fd, identity = lease_fixture(tmp_path)
    path = lease_path
    proc_root = witness_env(tmp_path, fd, lease_path)
    try:
        record = runtime.guardian_witness(start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        assert record['method'] == cl.GUARDIAN_WITNESS_METHOD
        assert record['fd'] == fd and (record['dev'], record['ino']) == identity
        assert record['state'] == 'S' and record['pid'] == PROC_PID

        monkeypatch.setenv('TRACKX_GPU_GUARDIAN_START_TICKS', '999')
        with pytest.raises(RuntimeError, match='start ticks changed'):
            runtime.guardian_witness(start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        monkeypatch.setenv('TRACKX_GPU_GUARDIAN_START_TICKS', '111')

        monkeypatch.setenv('TRACKX_GPU_GUARDIAN_PID', str(os.getpid()))
        with pytest.raises(RuntimeError, match='points at this process'):
            runtime.guardian_witness(start_ticks=lambda pid: 111, proc_root=proc_root)
        monkeypatch.setenv('TRACKX_GPU_GUARDIAN_PID', str(PROC_PID))

        monkeypatch.delenv('TRACKX_GPU_LEASE_FD')
        with pytest.raises(RuntimeError, match='identity missing'):
            runtime.guardian_witness(start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        monkeypatch.setenv('TRACKX_GPU_LEASE_FD', str(fd))

        _proc_entry(proc_root, PROC_PID, 111, state='Z')
        with pytest.raises(RuntimeError, match='not live'):
            runtime.guardian_witness(start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        _proc_entry(proc_root, PROC_PID, 111, state='S')

        other = tmp_path / 'other.lock'
        other.touch()
        other_proc = str(tmp_path / 'proc_wrong_fd')
        _proc_entry(other_proc, PROC_PID, 111)
        _proc_fd(other_proc, PROC_PID, fd, str(other))
        with pytest.raises(RuntimeError, match='descriptor identity changed'):
            runtime.guardian_witness(start_ticks=fake_ticks(other_proc), proc_root=other_proc)

        monkeypatch.setenv('TRACKX_GPU_LEASE_INO', str(identity[1] + 1))
        with pytest.raises(RuntimeError, match='lease not established'):
            runtime.authorize_cooperative_stagea(
                {'cache_prompt': False, 'd3_policy': runtime.COOPERATIVE_POLICY},
                lease_path=path, witness=lambda: runtime.guardian_witness(
                    start_ticks=fake_ticks(proc_root), proc_root=proc_root))
    finally:
        os.close(fd)


# -- authorization ------------------------------------------------------------

def test_authorization_requires_policy_explicit_false_and_held_ofd(tmp_path, monkeypatch):
    path, fd, identity = lease_fixture(tmp_path)
    proc_root = witness_env(tmp_path, fd, path)
    witness = lambda: runtime.guardian_witness(start_ticks=fake_ticks(proc_root), proc_root=proc_root)
    token = runtime._authorized.set(False)
    try:
        with pytest.raises(RuntimeError, match='policy'):
            runtime.authorize_cooperative_stagea({'cache_prompt': False}, lease_path=path, witness=witness)
        with pytest.raises(RuntimeError, match='policy'):
            runtime.authorize_cooperative_stagea({'cache_prompt': True, 'd3_policy': runtime.COOPERATIVE_POLICY},
                                                 lease_path=path, witness=witness)
        record = runtime.authorize_cooperative_stagea(
            {'cache_prompt': False, 'd3_policy': runtime.COOPERATIVE_POLICY}, lease_path=path, witness=witness)
        assert record['host_global_single_server'] == 'NOT_CHECKABLE'
        assert 'author assumption' in record['same_uid_external_noninterference']
        assert record['lease']['method'] == cl.FLOCK_INHERITANCE_METHOD
        assert record['lease']['kcmp_used'] is False
        assert 'Yama' in record['lease']['kcmp_note']
        assert set(record['authorization_methods']) == {cl.GUARDIAN_WITNESS_METHOD, cl.FLOCK_INHERITANCE_METHOD}
        assert record['kcmp_used_for_guardian_edge'] is False
        assert runtime.verified_lease_fd(witness=witness) == fd
        monkeypatch.setenv('TRACKX_GPU_LEASE_INO', str(identity[1] + 1))
        with pytest.raises(RuntimeError):
            runtime.verified_lease_fd(witness=witness)
        with pytest.raises(RuntimeError):
            runtime.reject_unverified_lease(witness=witness)
    finally:
        runtime._authorized.reset(token)
        os.close(fd)


@pytest.mark.parametrize('mutation,message', [
    ('fd', 'absent'),
    ('dev', 'not established'),
    ('ino', 'not established'),
    ('uid', 'not established'),
])
def test_authorization_rejects_missing_or_mismatched_lease_env(tmp_path, mutation, message):
    path, fd, identity = lease_fixture(tmp_path)
    try:
        witness_env(tmp_path, fd, path)
        if mutation == 'fd':
            os.environ.pop('TRACKX_GPU_LEASE_FD')
        elif mutation == 'dev':
            os.environ['TRACKX_GPU_LEASE_DEV'] = str(identity[0] + 1)
        elif mutation == 'ino':
            os.environ['TRACKX_GPU_LEASE_INO'] = str(identity[1] + 1)
        else:
            os.environ['TRACKX_GPU_LEASE_UID'] = str(os.getuid() + 1)
        token = runtime._authorized.set(False)
        try:
            with pytest.raises(RuntimeError, match=message):
                runtime.authorize_cooperative_stagea(
                    {'cache_prompt': False, 'd3_policy': runtime.COOPERATIVE_POLICY}, lease_path=path,
                    witness=lambda: {'pid': PROC_PID, 'start_ticks': 111, 'fd': fd,
                                     'dev': identity[0], 'ino': identity[1], 'uid': os.fstat(fd).st_uid,
                                     'state': 'S', 'method': cl.GUARDIAN_WITNESS_METHOD})
        finally:
            runtime._authorized.reset(token)
    finally:
        for key in ('TRACKX_GPU_LEASE_FD', 'TRACKX_GPU_LEASE_DEV', 'TRACKX_GPU_LEASE_INO', 'TRACKX_GPU_LEASE_UID'):
            os.environ.pop(key, None)
        os.close(fd)


def test_unverified_lease_is_always_stop_without_authorization():
    token = runtime._authorized.set(False)
    try:
        with pytest.raises(RuntimeError, match='context not authorized'):
            runtime.reject_unverified_lease()
        with pytest.raises(RuntimeError, match='context not authorized'):
            runtime.verified_lease_fd()
        with pytest.raises(RuntimeError, match='context not authorized'):
            runtime.require_worker_lease_inheritance({})
    finally:
        runtime._authorized.reset(token)


def test_boolean_or_absent_witness_is_never_accepted(tmp_path):
    path, fd, identity = lease_fixture(tmp_path)
    try:
        witness_env(tmp_path, fd, path)
        token = runtime._authorized.set(False)
        try:
            with pytest.raises(RuntimeError, match='lease not established'):
                runtime.authorize_cooperative_stagea(
                    {'cache_prompt': False, 'd3_policy': runtime.COOPERATIVE_POLICY}, lease_path=path,
                    witness=lambda: True)
        finally:
            runtime._authorized.reset(token)
    finally:
        os.close(fd)


# -- runner/worker -> native server inheritance -------------------------------

def inheritance_fixture(tmp_path, authorized, *, server_fd='valid'):
    """Real lease FD + synthetic /proc for the runner and its native server."""
    path, fd, identity = lease_fixture(tmp_path)
    proc_root = str(tmp_path / 'proc')
    _proc_entry(proc_root, RUNNER_PID, 100, ppid=1)
    _proc_entry(proc_root, SERVER_PID, 200, ppid=RUNNER_PID)
    if server_fd == 'valid':
        _proc_fd(proc_root, SERVER_PID, fd, str(path))
    elif server_fd == 'wrong':
        other = tmp_path / 'other'
        other.touch()
        _proc_fd(proc_root, SERVER_PID, fd, str(other))
    elif server_fd == 'extra':
        _proc_fd(proc_root, SERVER_PID, fd, str(path))
        extra = tmp_path / 'extra-desc'
        extra.touch()
        _proc_fd(proc_root, SERVER_PID, 99, str(extra))
        _proc_fd(proc_root, SERVER_PID, 98, str(path))
    elif server_fd != 'missing':
        raise AssertionError('invalid synthetic server fd mode')
    os.environ['TRACKX_GPU_LEASE_FD'] = str(fd)
    os.environ['TRACKX_GPU_LEASE_DEV'] = str(identity[0])
    os.environ['TRACKX_GPU_LEASE_INO'] = str(identity[1])
    os.environ['TRACKX_GPU_LEASE_UID'] = str(os.fstat(fd).st_uid)
    os.environ['TRACKX_GPU_GUARDIAN_PID'] = str(PROC_PID)
    os.environ['TRACKX_GPU_GUARDIAN_START_TICKS'] = '111'
    _proc_entry(proc_root, PROC_PID, 111)
    _proc_fd(proc_root, PROC_PID, fd, str(path))
    return path, fd, identity, proc_root


def verify_inheritance(fd, proc_root, kcmp=None, **kwargs):
    calls = []

    def default_kcmp(pid_a, pid_b, fd_a, fd_b):
        calls.append((pid_a, pid_b, fd_a, fd_b))
        return (0, 0)

    record = runtime.verify_server_lease_inheritance(
        SERVER_PID, fd, runner_pid=RUNNER_PID, started_ticks=200, proc_root=proc_root,
        start_ticks=fake_ticks(proc_root), kcmp=kcmp or default_kcmp, **kwargs)
    return record, calls


def test_server_inheritance_is_proved_ancestor_to_descendant_only(tmp_path, authorized):
    path, fd, identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        record, calls = verify_inheritance(fd, proc_root)
        assert calls == [(RUNNER_PID, SERVER_PID, fd, fd)]
        assert record['version'] == runtime.LEASE_INHERITANCE_VERSION
        assert record['method'] == runtime.LEASE_INHERITANCE_METHOD
        assert record['runner_pid'] == RUNNER_PID and record['server_pid'] == SERVER_PID
        assert record['server_ppid'] == RUNNER_PID
        assert record['kcmp_rc'] == 0 and record['kcmp_same_ofd'] is True
        assert record['server_lease_fds'] == [fd] and record['fd_set_exact'] is True
        assert (record['dev'], record['ino']) == identity
        assert record['cold_verified'] is False
        assert 'ancestor' in record['yama_direction']
        assert 'host/kernel dependent' in record['yama_direction']
        assert runtime.validate_lease_inheritance_record(record) is record
    finally:
        os.close(fd)


@pytest.mark.parametrize('kcmp_result', [(1, 0), (None, 1), (None, None)])
def test_server_inheritance_fails_closed_when_kcmp_is_not_same(tmp_path, authorized, kcmp_result):
    path, fd, identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        with pytest.raises(LeaseStop, match='kcmp'):
            verify_inheritance(fd, proc_root, kcmp=lambda *args: kcmp_result)
    finally:
        os.close(fd)


def test_server_inheritance_rejects_missing_extra_or_wrong_descriptor(tmp_path, authorized):
    # Each case starts as the exact malformed FD table; no links are removed.
    for mode, expected in [('missing', 'does not retain'), ('extra', 'FD set'),
                           ('wrong', 'identity differs')]:
        case = tmp_path / mode
        case.mkdir()
        path, fd, identity, proc_root = inheritance_fixture(case, authorized, server_fd=mode)
        try:
            with pytest.raises(LeaseStop, match=expected):
                verify_inheritance(fd, proc_root)
        finally:
            os.close(fd)


def test_server_inheritance_rejects_pid_start_and_parent_mismatch(tmp_path, authorized):
    path, fd, identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        with pytest.raises(LeaseStop, match='start ticks differ'):
            runtime.verify_server_lease_inheritance(
                SERVER_PID, fd, runner_pid=RUNNER_PID, started_ticks=999, proc_root=proc_root,
                start_ticks=fake_ticks(proc_root), kcmp=lambda *a: (0, 0))
        _proc_entry(proc_root, SERVER_PID, 200, ppid=99999)
        with pytest.raises(LeaseStop, match='parent pid'):
            verify_inheritance(fd, proc_root)
        _proc_entry(proc_root, SERVER_PID, 201, ppid=RUNNER_PID)
        with pytest.raises(LeaseStop, match='start ticks differ'):
            verify_inheritance(fd, proc_root)
        with pytest.raises(LeaseStop, match='distinct descendant'):
            runtime.verify_server_lease_inheritance(
                RUNNER_PID, fd, runner_pid=RUNNER_PID, proc_root=proc_root,
                start_ticks=fake_ticks(proc_root), kcmp=lambda *a: (0, 0))
    finally:
        os.close(fd)


def test_inheritance_record_validation_rejects_tampering(tmp_path, authorized):
    path, fd, identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        good, _ = verify_inheritance(fd, proc_root)
        broken = {key: value for key, value in good.items() if key != 'kcmp_rc'}
        with pytest.raises(LeaseStop, match='schema'):
            runtime.validate_lease_inheritance_record(broken)
        for mutation in ({'kcmp_rc': 1}, {'kcmp_same_ofd': False}, {'cold_verified': True},
                         {'kcmp_errors_never_same': False}, {'server_ppid': 1},
                         {'kcmp_pid_a': SERVER_PID}, {'fd_set_exact': False},
                         {'yama_direction': ''}, {'dev': 1}, {'server_fd_ino': 1}):
            with pytest.raises(LeaseStop):
                runtime.validate_lease_inheritance_record({**good, **mutation})
    finally:
        os.close(fd)


def test_worker_rechecks_the_record_without_upward_kcmp(tmp_path, authorized):
    path, fd, identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        record, calls = verify_inheritance(fd, proc_root)
        identity_doc = {'pid': SERVER_PID, 'process_start_ticks': 200, 'lease_inheritance': record}
        recheck = runtime.require_worker_lease_inheritance(
            identity_doc, start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        assert recheck['method'] == runtime.WORKER_RECHECK_METHOD
        assert recheck['kcmp_used_upward'] is False
        assert 'host/kernel dependent' in recheck['kcmp_not_used_reason']
        assert recheck['lease_fd'] == fd and recheck['runner_side_record']['kcmp_rc'] == 0
        assert recheck['server_ppid'] == RUNNER_PID
        with pytest.raises(LeaseStop, match='schema'):
            runtime.require_worker_lease_inheritance(
                {'pid': SERVER_PID, 'process_start_ticks': 200}, start_ticks=fake_ticks(proc_root),
                proc_root=proc_root)
        with pytest.raises(LeaseStop, match='does not bind'):
            runtime.require_worker_lease_inheritance(
                {**identity_doc, 'pid': 1}, start_ticks=fake_ticks(proc_root), proc_root=proc_root)
        os.environ['TRACKX_GPU_LEASE_FD'] = str(fd + 1)
        with pytest.raises(LeaseStop, match='FD number differs'):
            runtime.require_worker_lease_inheritance(
                identity_doc, start_ticks=fake_ticks(proc_root), proc_root=proc_root)
    finally:
        os.close(fd)


# -- worker identity binding ------------------------------------------------

def _identity_and_job(tmp_path):
    binary = tmp_path / 'fake-binary'
    binary.write_bytes(b'fake-binary')
    model = tmp_path / 'fake-model'
    model.write_bytes(b'fake-model')
    binary_sha = hashlib.sha256(binary.read_bytes()).hexdigest()
    model_sha = hashlib.sha256(model.read_bytes()).hexdigest()
    identity = {'pid': SERVER_PID, 'process_start_ticks': 200, 'port': 42, 'alias': 'fake',
                'binary': str(binary), 'binary_sha256': binary_sha,
                'model_path': str(model), 'model_sha256': model_sha}
    job = {'port': 42, 'config': {'server': {'binary': str(binary), 'binary_sha256': binary_sha}},
           'candidate': {'id': 'fake', 'runtime': {'model_path': str(model)},
                         'quant_source': {'sha256': model_sha}}}
    census = lambda i: {'count': 1, 'pid': SERVER_PID, 'process_start_ticks': 200,
                        'scope': 'synthetic', 'method': 'fixture'}
    return identity, job, census


def test_worker_binding_requires_the_inheritance_record(tmp_path, authorized):
    identity, job, census = _identity_and_job(tmp_path)
    path, fd, lease_identity, proc_root = inheritance_fixture(tmp_path, authorized)
    try:
        record, _ = verify_inheritance(fd, proc_root)
        identity['lease_inheritance'] = record
        result = runtime.validate_worker_binding(identity, job, start_ticks=fake_ticks(proc_root),
                                                 census=census, proc_root=proc_root)
        assert result['count'] == 1
        assert result['lease_inheritance_check']['method'] == runtime.WORKER_RECHECK_METHOD
        stripped = {key: value for key, value in identity.items() if key != 'lease_inheritance'}
        with pytest.raises(LeaseStop):
            runtime.validate_worker_binding(stripped, job, start_ticks=fake_ticks(proc_root),
                                            census=census, proc_root=proc_root)
        with pytest.raises(RuntimeError, match='binding changed'):
            runtime.validate_worker_binding({**identity, 'port': 43}, job,
                                            start_ticks=fake_ticks(proc_root), census=census,
                                            proc_root=proc_root)
    finally:
        os.close(fd)


def test_worker_binding_rejects_process_reuse_or_changed_port(tmp_path):
    identity, job, census = _identity_and_job(tmp_path)
    with pytest.raises(RuntimeError, match='binding changed'):
        runtime.validate_worker_binding(identity, job, start_ticks=lambda pid: 999, census=census)
    job['port'] = 43
    with pytest.raises(RuntimeError, match='binding changed'):
        runtime.validate_worker_binding(identity, job, start_ticks=lambda pid: 200, census=census)


# -- parent identity / coldness ----------------------------------------------

def _parent_fixture(tmp_path, monkeypatch, lease_record=None):
    binary = tmp_path / 'fake-binary'
    binary.write_bytes(b'fake-binary')
    model = tmp_path / 'fake-model'
    model.write_bytes(b'fake-model')
    b = hashlib.sha256(binary.read_bytes()).hexdigest()
    m = hashlib.sha256(model.read_bytes()).hexdigest()
    record = {'pid': 123, 'port': 42, 'alias': 'fake', 'model_sha256': m}
    if lease_record is not None:
        record['lease_inheritance'] = lease_record
    instance = SimpleNamespace(record=record, process=SimpleNamespace(pid=123, poll=lambda: None),
                               port=42, alias='fake', binary=str(binary), model_path=str(model))
    census = lambda i: {'count': 1, 'pid': 123, 'process_start_ticks': 456,
                        'scope': 'synthetic', 'method': 'fixture'}
    return instance, b, m, census


def test_new_process_snapshot_does_not_claim_cold_or_hostwide_exclusivity(tmp_path):
    instance, b, m, census = _parent_fixture(tmp_path, None)
    identity = runtime.capture_parent_identity(instance, binary_sha256=b, model_sha256=m,
                                               start_ticks=lambda pid: 456, census=census)
    assert identity['fresh'] is True and identity['cold_verified'] is False
    assert 'author assumption' in identity['scope']
    with pytest.raises(RuntimeError, match='context not authorized'):
        runtime.reject_unverified_cold(identity)


def test_cooperative_parent_identity_requires_verified_inheritance(tmp_path):
    record = {'version': 'trackx_lease_inheritance/v1'}
    instance, b, m, census = _parent_fixture(tmp_path, None)
    os.environ['TRACKX_GPU_LEASE_FD'] = '3'
    try:
        with pytest.raises(RuntimeError, match='lacks verified lease inheritance'):
            runtime.capture_parent_identity(instance, binary_sha256=b, model_sha256=m,
                                            start_ticks=lambda pid: 456, census=census)
    finally:
        os.environ.pop('TRACKX_GPU_LEASE_FD', None)


def test_binary_mismatch_and_second_server_stop(tmp_path):
    instance, b, m, census = _parent_fixture(tmp_path, None)
    with pytest.raises(RuntimeError, match='hash mismatch'):
        runtime.capture_parent_identity(instance, binary_sha256='0' * 64, model_sha256=m,
                                        start_ticks=lambda pid: 456, census=census)
    bad = lambda i: {'count': 2, 'pid': 123, 'process_start_ticks': 456}
    with pytest.raises(RuntimeError, match='census'):
        runtime.capture_parent_identity(instance, binary_sha256=b, model_sha256=m,
                                        start_ticks=lambda pid: 456, census=bad)
