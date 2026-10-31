"""Synthetic temporary lease files only; never touches a real GPU lock.

Linux-only kcmp behaviour is skipped off Linux; the non-kcmp logic (flock
same-OFD via dup, independent-open rejection, witness method labels, completion
contract, FD passing) runs everywhere.
"""
import errno
import fcntl
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from r1.exam import cooperative_lease as cl
from r1.scripts import llama_server_instance as lsi


def witness(fd, pid=999, state='S', method=cl.GUARDIAN_WITNESS_METHOD):
    st = os.fstat(fd)
    return {'pid': pid, 'start_ticks': 111, 'fd': fd, 'dev': st.st_dev, 'ino': st.st_ino,
            'uid': st.st_uid, 'state': state, 'method': method}


def make_lease(tmp_path, name='synthetic.lock'):
    path = tmp_path / name
    path.touch()
    fd, identity = cl.acquire_existing(path)
    return path, fd, identity


def inheritance(server_pid=4242, start_ticks=777, runner_pid=None, fd=3, dev=10, ino=20, uid=0):
    runner_pid = os.getpid() if runner_pid is None else runner_pid
    return {'version': 'trackx_lease_inheritance/v1',
            'method': 'proc_fd_dev_ino_and_kcmp_file_ancestor_to_descendant',
            'runner_pid': runner_pid, 'runner_start_ticks': 111,
            'server_pid': server_pid, 'server_start_ticks': start_ticks, 'server_ppid': runner_pid,
            'lease_fd': fd, 'dev': dev, 'ino': ino, 'uid': uid,
            'server_fd_dev': dev, 'server_fd_ino': ino, 'server_lease_fds': [fd], 'fd_set_exact': True,
            'kcmp_pid_a': runner_pid, 'kcmp_pid_b': server_pid, 'kcmp_fd_a': fd, 'kcmp_fd_b': fd,
            'kcmp_rc': 0, 'kcmp_same_ofd': True, 'kcmp_errors_never_same': True,
            'yama_direction': 'kcmp(ancestor -> descendant); Yama ptrace_scope=1',
            'monotonic_ns': 1, 'cold_verified': False, 'scope': 'synthetic fixture'}


# -- flock / same-open-file-description semantics -------------------------------

def test_dup_shares_the_held_flock_and_passes_bound_check(tmp_path):
    path, fd, identity = make_lease(tmp_path)
    duplicate = os.dup(fd)
    try:
        record = cl.assert_held_and_bound(duplicate, path, identity, guardian_check=lambda: witness(duplicate))
        assert record['contender'] == 'blocked'
        assert record['method'] == cl.FLOCK_INHERITANCE_METHOD
        assert record['kcmp_used'] is False
        note = record['kcmp_note']
        assert 'not used' in note and 'never counts as SAME' in note
        assert 'host/kernel dependent' in note
        assert record['guardian_witness_samples'] == 4
        with pytest.raises(cl.LeaseStop):
            cl.acquire_existing(path)
        os.close(fd)
        fd = None
        # The duplicate still holds the same open file description.
        assert cl.assert_held_and_bound(duplicate, path, identity,
                                        guardian_check=lambda: witness(duplicate))['dev'] == identity[0]
    finally:
        if fd is not None:
            os.close(fd)
        os.close(duplicate)
    fresh, _ = cl.acquire_existing(path)
    os.close(fresh)


def test_independently_opened_same_inode_is_not_the_inherited_ofd(tmp_path):
    path, fd, identity = make_lease(tmp_path)
    unrelated = os.open(path, os.O_RDWR)
    try:
        with pytest.raises(cl.LeaseStop, match='does not share held flock'):
            cl.assert_held_and_bound(unrelated, path, identity,
                                     guardian_check=lambda: witness(unrelated, pid=7))
        assert cl.assert_held_and_bound(fd, path, identity, guardian_check=lambda: witness(fd))['contender'] == 'blocked'
    finally:
        os.close(unrelated)
        os.close(fd)


def test_unlocked_descriptor_is_rejected(tmp_path):
    path = tmp_path / 'synthetic.lock'
    path.touch()
    fd = os.open(path, os.O_RDWR)
    st = os.fstat(fd)
    try:
        with pytest.raises(cl.LeaseStop, match='contender acquired'):
            cl.assert_held_and_bound(fd, path, (st.st_dev, st.st_ino), guardian_check=lambda: witness(fd))
    finally:
        os.close(fd)


def test_missing_lease_is_never_created_and_symlink_or_hardlink_refused(tmp_path):
    absent = tmp_path / 'absent.lock'
    with pytest.raises(OSError):
        cl.acquire_existing(absent)
    assert not absent.exists()
    path, fd, identity = make_lease(tmp_path)
    symlink = tmp_path / 'symlink.lock'
    symlink.symlink_to(path)
    with pytest.raises(OSError):
        cl.acquire_existing(symlink)
    hardlink = tmp_path / 'hardlink.lock'
    os.link(path, hardlink)
    try:
        with pytest.raises(cl.LeaseStop, match='not a stable regular file'):
            cl.acquire_existing(hardlink)
    finally:
        os.close(fd)


def test_replaced_path_and_guardian_death_between_samples_fail_closed(tmp_path):
    path, fd, identity = make_lease(tmp_path)
    replacement = tmp_path / 'replacement.lock'
    replacement.touch()
    try:
        with pytest.raises(cl.LeaseStop):
            cl.assert_held_and_bound(fd, replacement, identity, guardian_check=lambda: witness(fd))
    finally:
        os.close(fd)
    path2, guardian, identity2 = make_lease(tmp_path, 'race.lock')
    unrelated = os.open(path2, os.O_RDWR)
    real_flock = fcntl.flock

    def racing_flock(target, op):
        if target == unrelated and op & fcntl.LOCK_EX and not op & fcntl.LOCK_NB:
            return real_flock(target, op)
        if target == unrelated:
            # The guardian disappears after the first contender observed the lock.
            os.close(guardian)
        return real_flock(target, op)

    import r1.exam.cooperative_lease as module
    original = module.fcntl.flock
    module.fcntl.flock = racing_flock
    try:
        with pytest.raises(cl.LeaseStop, match='guardian'):
            cl.assert_held_and_bound(unrelated, path2, identity2,
                                     guardian_check=lambda: 'guarded')
    finally:
        module.fcntl.flock = original
        os.close(unrelated)


def test_guardian_witness_is_never_a_boolean_or_relabelled(tmp_path):
    path, fd, identity = make_lease(tmp_path)
    try:
        cases = [
            (lambda: True, 'witness schema'),
            (lambda: {'pid': 999}, 'witness schema'),
            (lambda: {**witness(fd), 'method': 'kcmp_same_ofd'}, 'witness method'),
            (lambda: {**witness(fd), 'state': 'Z'}, 'not live'),
            (lambda: {**witness(fd), 'pid': os.getpid()}, 'not an owner'),
            (lambda: {**witness(fd), 'fd': fd + 1}, 'FD number changed'),
            (lambda: {**witness(fd), 'ino': identity[1] + 1}, 'identity changed'),
            (lambda: {**witness(fd), 'uid': os.fstat(fd).st_uid + 1}, 'owner differs'),
        ]
        for check, message in cases:
            with pytest.raises(cl.LeaseStop, match=message):
                cl.assert_held_and_bound(fd, path, identity, guardian_check=check)
    finally:
        os.close(fd)


def test_guardian_witness_validation_accepts_only_the_fixed_method():
    fd = os.open(os.devnull, os.O_RDONLY)
    try:
        record = witness(fd)
        assert cl.validate_guardian_witness(record) is record
    finally:
        os.close(fd)


# -- kcmp result semantics -----------------------------------------------------

def _fake_linux_syscall(monkeypatch, rc, errno_value=0):
    calls = []

    class Syscall:
        restype = None

        def __call__(self, *args):
            calls.append(args)
            import ctypes
            ctypes.set_errno(errno_value)
            return rc

    monkeypatch.setattr(cl.os, 'uname',
                        lambda: types.SimpleNamespace(sysname='Linux', machine='x86_64'))
    monkeypatch.setattr(cl.ctypes, 'CDLL',
                        lambda *a, **k: types.SimpleNamespace(syscall=Syscall()))
    return calls


def test_kcmp_file_result_reports_same_different_and_errors(monkeypatch):
    _fake_linux_syscall(monkeypatch, 0)
    assert cl.kcmp_file_result(101, 102, 3, 3) == (0, 0)
    assert cl.kcmp_same_ofd(101, 102, 3, 3) is True
    _fake_linux_syscall(monkeypatch, 1)
    assert cl.kcmp_file_result(101, 102, 3, 3) == (1, 0)
    assert cl.kcmp_same_ofd(101, 102, 3, 3) is False
    _fake_linux_syscall(monkeypatch, -1, errno_value=errno.EPERM)
    assert cl.kcmp_file_result(101, 102, 3, 3) == (None, errno.EPERM)
    assert cl.kcmp_same_ofd(101, 102, 3, 3) is False


def test_kcmp_rejects_invalid_arguments_and_loader_failure(monkeypatch):
    assert cl.kcmp_file_result(True, 102, 3, 3) == (None, None)
    assert cl.kcmp_file_result(2 ** 40, 102, 3, 3) == (None, None)
    assert cl.kcmp_file_result(101, 102, -1, 3) == (None, None)
    monkeypatch.setattr(cl.os, 'uname', lambda: types.SimpleNamespace(sysname='Linux', machine='x86_64'))

    def boom(*args, **kwargs):
        raise OSError('unavailable')

    monkeypatch.setattr(cl.ctypes, 'CDLL', boom)
    assert cl.kcmp_same_ofd(101, 102, 3, 3) is False


# -- completion writer contract ------------------------------------------------

def completion_fixture(tmp_path, monkeypatch, *, status='COMPLETE'):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(evidence))
    batch_state = tmp_path / 'out' / 'batch_state.json'
    batch_state.parent.mkdir()
    batch_state.write_text(json.dumps({'status': status}) + '\n')
    record = tmp_path / 'out' / 'servers' / 'cand' / 'llama_server_9000.json'
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps({'pid': 4242, 'start_ticks': 777,
                                  'stopped_utc': '2026-10-31T00:00:00Z'}) + '\n')
    servers = [{'pid': 4242, 'start_ticks': 777, 'stopped_utc': '2026-10-31T00:00:00Z',
                'record_sha256': cl.hashlib.sha256(record.read_bytes()).hexdigest(),
                'record_path': str(record.resolve())}]
    return evidence, batch_state, servers


def row(**overrides):
    base = {'pid': 4242, 'start_ticks': 777, 'stopped_utc': '2026-10-31T00:00:00Z',
            'record_sha256': 'a' * 64, 'record_path': '/nonexistent/record.json'}
    base.update(overrides)
    return base


def test_completion_writer_emits_the_pinned_contract(tmp_path, monkeypatch):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch)
    returned = cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                                   runner_pid=os.getpid(), runner_start_ticks=int(os.getpid()) + 1)
    assert returned == str(evidence / 'lease_completion.json')
    document = json.loads((evidence / 'lease_completion.json').read_text())
    assert set(document) == cl.COMPLETION_KEYS
    assert document['version'] == 'trackx_lease_completion/v1'
    assert document['batch_state'] == str(batch_state.resolve())
    assert document['batch_state_sha256'] == cl.hashlib.sha256(batch_state.read_bytes()).hexdigest()
    assert document['servers'] == servers
    assert document['runner_pid'] == os.getpid()
    assert (evidence / 'lease_completion.json').stat().st_nlink == 1
    assert not [p for p in evidence.iterdir() if p.name.startswith('.lease_completion.')]
    with pytest.raises(cl.LeaseStop, match='no overwrite'):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)


@pytest.mark.parametrize('kwargs,message', [
    ({'status': 'RUNNING'}, 'not COMPLETE'),
    ({'status': 'STOPPED'}, 'not COMPLETE'),
])
def test_completion_writer_refuses_incomplete_batch_state(tmp_path, monkeypatch, kwargs, message):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch, **kwargs)
    with pytest.raises(cl.LeaseStop, match=message):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)


def test_completion_writer_refuses_unannounced_evidence_dir(tmp_path, monkeypatch):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch)
    monkeypatch.setenv('TRACKX_LEASE_EVIDENCE_DIR', str(tmp_path / 'other'))
    with pytest.raises(cl.LeaseStop, match='guardian-provided'):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)
    monkeypatch.delenv('TRACKX_LEASE_EVIDENCE_DIR')
    with pytest.raises(cl.LeaseStop, match='guardian-provided'):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)


@pytest.mark.parametrize('servers_factory,message', [
    (lambda: [], 'at least one'),
    (lambda: [{'pid': 1, 'start_ticks': 1, 'stopped_utc': 'x'}], 'schema'),
    (lambda: [row(pid=0, record_sha256='a' * 64)], 'pid'),
    (lambda: [row(start_ticks=0)], 'start_ticks'),
    (lambda: [row(stopped_utc=12.5)], 'ISO-8601'),
    (lambda: [row(stopped_utc='not-a-time')], 'ISO-8601'),
    (lambda: [row(record_sha256='zz')], 'record_sha256'),
    (lambda: [row(record_path='relative/record.json')], 'record_path'),
    (lambda: [row(record_path='/tmp')], 'server record'),
])
def test_completion_writer_refuses_malformed_server_rows(tmp_path, monkeypatch, servers_factory, message):
    evidence, batch_state, _ = completion_fixture(tmp_path, monkeypatch)
    with pytest.raises(cl.LeaseStop, match=message):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers_factory(),
                            runner_pid=os.getpid(), runner_start_ticks=5)


def test_completion_writer_refuses_duplicate_server_rows(tmp_path, monkeypatch):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch)
    with pytest.raises(cl.LeaseStop, match='duplicate'):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers + servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)


def test_completion_writer_is_written_by_the_runner_process_only(tmp_path, monkeypatch):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch)
    with pytest.raises(cl.LeaseStop, match='runner process'):
        cl.write_completion(str(evidence), batch_state_path=str(batch_state), servers=servers,
                            runner_pid=os.getpid() + 1, runner_start_ticks=5)


def test_completion_writer_refuses_unstable_batch_state(tmp_path, monkeypatch):
    evidence, batch_state, servers = completion_fixture(tmp_path, monkeypatch)
    link = tmp_path / 'batch_state_link.json'
    os.link(batch_state, link)
    with pytest.raises(cl.LeaseStop, match='stable regular file'):
        cl.write_completion(str(evidence), batch_state_path=str(link), servers=servers,
                            runner_pid=os.getpid(), runner_start_ticks=5)


# -- runtime wiring (r1.exam.runtime) ------------------------------------------

def _runtime_module():
    """Import the exam runtime; stub only unrelated campaign writers if the pinned
    harness/scipy/sklearn/lightgbm stack is absent from this minimal test venv."""
    try:
        from r1.exam import runtime
        return runtime
    except (RuntimeError, ModuleNotFoundError) as exc:
        if 'harness' not in str(exc) and not isinstance(exc, ModuleNotFoundError):
            raise
    stub = types.ModuleType('r1.exam.campaign')

    def write_json(path, data):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n')

    stub.write_json = write_json
    stub.read_rows = lambda path: [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    sys.modules['r1.exam.campaign'] = stub
    from r1.exam import runtime
    return runtime


def _runner_with_service(runtime, tmp_path, monkeypatch):
    configured = {'version_line': 'synthetic-build'}
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.cfg = {'dryrun': True, 'gpu_uuid': 'GPU-FAKE', 'server': {'binary': '/synthetic/llama-server',
                                                                    'binary_sha256': 'bin', 'build': 'synthetic-build', 'start_timeout': 10},
                  'root_timeout_seconds': 30, 'watchdog': {'poll_seconds': 0.05}}
    runner.out = tmp_path / 'out'
    runner.out.mkdir()
    runner.state = {'phase': 'stage-a', 'execution_label': 'ENGINEERING_ONLY', 'server_intervals': []}
    runner.service = None
    runner.validate_spec = lambda spec: configured
    runner.space = lambda: None
    runner.save = lambda: None
    return runner


def test_stage_a_server_receives_the_verified_lease_fd_and_records_inheritance(tmp_path, monkeypatch):
    runtime = _runtime_module()
    path, fd, _ = make_lease(tmp_path)
    try:
        spec = {'id': 'cand', 'runtime': {'model_path': str(tmp_path / 'model'), 'footprint_mib': 1},
                'quant_source': {'sha256': 'model-sha'}, 'thinking_policy': {'mode': 'off'}}
        (tmp_path / 'model').write_bytes(b'GGUF')
        started = {}

        class FakeInstance:
            def __init__(self, batch, binary, **kwargs):
                self.batch = Path(batch)
                self.record = {}
                self.process = None
                self.port = 1
                self.alias = 'cand'
                self.model_path = spec['runtime']['model_path']

            def start(self, **kwargs):
                started.update(kwargs)
                self.record = {'pid': 4242, 'start_ticks': 777,
                               'lease_inheritance': inheritance(server_pid=4242, start_ticks=777, fd=kwargs['lease_fd'])}
                return self.record

            def offload(self, **kwargs):
                return {'full': True}

            def model_ids(self):
                return ['cand']

            def props(self):
                return {'model_path': spec['runtime']['model_path']}

        monkeypatch.setattr(runtime, 'host_check', lambda cfg, out: None)
        monkeypatch.setattr(runtime.lsi, 'LlamaServerInstance', FakeInstance)
        monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', lambda: fd)
        runner = _runner_with_service(runtime, tmp_path, monkeypatch)
        instance = runner._server(spec, 'off', 32768)
        assert started['lease_fd'] == fd
        evidence = json.loads((runner.out / 'servers' / 'cand' / 'lease_inheritance.json').read_text())
        assert evidence['kcmp_rc'] == 0 and evidence['server_pid'] == 4242
        assert instance.record['start_ticks'] == 777
    finally:
        os.close(fd)


def test_stage_a_server_without_inheritance_is_a_preparation_stop(tmp_path, monkeypatch):
    runtime = _runtime_module()
    path, fd, _ = make_lease(tmp_path)
    try:
        spec = {'id': 'cand', 'runtime': {'model_path': str(tmp_path / 'model'), 'footprint_mib': 1},
                'quant_source': {'sha256': 'model-sha'}, 'thinking_policy': {'mode': 'off'}}
        (tmp_path / 'model').write_bytes(b'GGUF')

        class FakeInstance:
            def __init__(self, *args, **kwargs):
                self.batch = Path(args[0])
                self.record = {}
                self.process = None
                self.port = 1
                self.alias = 'cand'
                self.model_path = spec['runtime']['model_path']

            def start(self, **kwargs):
                self.record = {'pid': 4242, 'start_ticks': 777}
                return self.record

            def offload(self, **kwargs):
                return {'full': True}

        monkeypatch.setattr(runtime, 'host_check', lambda cfg, out: None)
        monkeypatch.setattr(runtime.lsi, 'LlamaServerInstance', FakeInstance)
        monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', lambda: fd)
        runner = _runner_with_service(runtime, tmp_path, monkeypatch)
        with pytest.raises(runtime.PreparationStop, match='lease inheritance'):
            runner._server(spec, 'off', 32768)
        assert not (runner.out / 'servers' / 'cand' / 'lease_inheritance.json').exists()
    finally:
        os.close(fd)


def test_stage_a_server_lease_stop_is_a_preparation_stop(tmp_path, monkeypatch):
    runtime = _runtime_module()
    path, fd, _ = make_lease(tmp_path)
    try:
        spec = {'id': 'cand', 'runtime': {'model_path': str(tmp_path / 'model'), 'footprint_mib': 1},
                'quant_source': {'sha256': 'model-sha'}, 'thinking_policy': {'mode': 'off'}}
        (tmp_path / 'model').write_bytes(b'GGUF')

        class FakeInstance:
            def __init__(self, *args, **kwargs):
                self.batch = Path(args[0])
                self.record = {}
                self.process = None
                self.port = 1
                self.alias = 'cand'
                self.model_path = spec['runtime']['model_path']

            def start(self, **kwargs):
                raise cl.LeaseStop('synthetic inheritance failure')

        monkeypatch.setattr(runtime, 'host_check', lambda cfg, out: None)
        monkeypatch.setattr(runtime.lsi, 'LlamaServerInstance', FakeInstance)
        monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', lambda: fd)
        runner = _runner_with_service(runtime, tmp_path, monkeypatch)
        with pytest.raises(runtime.PreparationStop, match='inheritance failed'):
            runner._server(spec, 'off', 32768)
    finally:
        os.close(fd)


def test_stage_a_run_job_passes_the_verified_fd_to_the_worker(tmp_path, monkeypatch):
    runtime = _runtime_module()
    path, fd, _ = make_lease(tmp_path)
    observation = tmp_path / 'child.json'
    script = tmp_path / 'child.py'
    script.write_text(
        'import json, os, sys\n'
        'out, number = sys.argv[1], int(sys.argv[2])\n'
        'st = os.fstat(number)\n'
        'json.dump({"fd": number, "dev": st.st_dev, "ino": st.st_ino, '
        '"env_fd": os.environ.get("TRACKX_GPU_LEASE_FD")}, open(out, "w"))\n')
    real_popen = subprocess.Popen

    def fake_popen(argv, **kwargs):
        return real_popen([sys.executable, str(script), str(observation), str(fd)], **kwargs)

    try:
        monkeypatch.setattr(runtime.subprocess, 'Popen', fake_popen)
        monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', lambda: fd)
        monkeypatch.setattr('r1.exam.cache_runtime.reject_unverified_lease', lambda: None)
        runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
        runner.state = {'phase': 'stage-a', 'interruptions': []}
        runner.service = None
        runner.cfg = {'root_timeout_seconds': 30, 'watchdog': {'poll_seconds': 0.05}, 'dryrun': True}
        runner.space = lambda: None
        runner.save = lambda: None
        runner.run_job({'out': str(tmp_path / 'job')}, 'r1.exam.qualify')
        observed = json.loads(observation.read_text())
        assert observed['fd'] == fd
        assert (observed['dev'], observed['ino']) == (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
    finally:
        os.close(fd)


def test_stage_a_run_job_stops_before_spawning_without_a_verified_fd(tmp_path, monkeypatch):
    runtime = _runtime_module()

    def missing():
        raise RuntimeError('STOP: inherited GPU lease FD absent')

    monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', missing)
    called = []
    monkeypatch.setattr(runtime.subprocess, 'Popen', lambda *a, **k: called.append(a))
    runner = runtime.ExamRunner.__new__(runtime.ExamRunner)
    runner.state = {'phase': 'stage-a', 'interruptions': []}
    runner.service = None
    runner.cfg = {'root_timeout_seconds': 30, 'watchdog': {'poll_seconds': 0.05}, 'dryrun': True}
    runner.space = lambda: None
    runner.save = lambda: None
    with pytest.raises(RuntimeError, match='STOP: inherited GPU lease FD absent'):
        runner.run_job({'out': str(tmp_path / 'job')}, 'r1.exam.qualify')
    assert called == []


def test_public_start_requires_authorized_d3_context_but_is_enabled():
    runtime = _runtime_module()
    # B1 fix: the reviewed Stage A path is enabled, but start() still refuses a
    # process whose cooperative D3 context was not authorized (guardian lease +
    # explicit false).  B1/B2 evidence entries remain hard STOP.
    with pytest.raises(RuntimeError, match='D3 cold-cache cooperative Stage A context not authorized'):
        runtime.ExamRunner.start(types.SimpleNamespace(), 'stage-a')
    with pytest.raises(runtime.PreparationStop, match='reviewed harness pin'):
        runtime.ExamRunner.start(types.SimpleNamespace(), 'b1')


# -- llama_server_instance lease passing ---------------------------------------

def _wait_for(path, timeout=10.0):
    deadline = __import__('time').monotonic() + timeout
    while __import__('time').monotonic() < deadline:
        if Path(path).exists():
            return
        __import__('time').sleep(0.05)
    raise AssertionError(f'timed out waiting for {path}')


def _fake_llama_server_binary(tmp_path):
    """Tiny stand-in that records inherited descriptors then idles (no model/GPU)."""
    binary = tmp_path / 'fake-llama-server'
    observation = tmp_path / 'server-fds.json'
    binary.write_text(
        '#!/usr/bin/env python3\n'
        'import json, os, sys, time\n'
        'seen = []\n'
        'for number in range(3, 32):\n'
        '    try:\n'
        '        st = os.fstat(number)\n'
        '    except OSError:\n'
        '        continue\n'
        '    seen.append({"fd": number, "dev": st.st_dev, "ino": st.st_ino})\n'
        'json.dump({"seen": seen, "argv": sys.argv}, open(os.environ["SYNTH_OBS"], "w"))\n'
        'time.sleep(60)\n')
    binary.chmod(0o755)
    return binary, observation


def test_native_server_start_passes_the_fd_and_records_inheritance(tmp_path, monkeypatch):
    binary, observation = _fake_llama_server_binary(tmp_path)
    model = tmp_path / 'model.gguf'
    model.write_bytes(b'GGUF fixture')
    path, fd, identity = make_lease(tmp_path)
    seen = {}

    def verify(server_pid, lease_fd, *, runner_pid=None, started_ticks=None):
        seen.update(server_pid=server_pid, lease_fd=lease_fd, runner_pid=runner_pid,
                    started_ticks=started_ticks)
        return inheritance(server_pid=server_pid, start_ticks=777, runner_pid=runner_pid or os.getpid(),
                           fd=lease_fd, dev=identity[0], ino=identity[1], uid=os.fstat(fd).st_uid)

    monkeypatch.setenv('SYNTH_OBS', str(observation))
    monkeypatch.setattr(lsi, 'port_is_free', lambda port: True)
    monkeypatch.setattr(lsi, '_get_json', lambda url, timeout: (200, {'status': 'ok'}))
    monkeypatch.setattr(lsi, 'process_start_ticks', lambda pid: 777)
    monkeypatch.setattr('r1.exam.cache_runtime.verify_server_lease_inheritance', verify)
    inst = lsi.LlamaServerInstance(tmp_path / 'batch', str(binary), model_path=str(model),
                                   alias='synthetic', port=43127, start_timeout=10)
    try:
        record = inst.start(lease_fd=fd)
        inherited = record['lease_inheritance']
        assert inherited['server_pid'] == record['pid']
        assert inherited['kcmp_rc'] == 0 and inherited['kcmp_same_ofd'] is True
        assert record['start_ticks'] == 777
        assert seen['lease_fd'] == fd and seen['runner_pid'] == os.getpid()
        assert seen['started_ticks'] == 777
        _wait_for(observation)
        child = json.loads(observation.read_text())
        fds = {row['fd']: (row['dev'], row['ino']) for row in child['seen']}
        assert fds.get(fd) == (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
    finally:
        inst.stop(timeout=5)
        os.close(fd)


def test_native_server_lease_failure_stops_before_any_request(tmp_path, monkeypatch):
    binary, observation = _fake_llama_server_binary(tmp_path)
    model = tmp_path / 'model.gguf'
    model.write_bytes(b'GGUF fixture')
    path, fd, _ = make_lease(tmp_path)

    def verify(*args, **kwargs):
        raise cl.LeaseStop('STOP: kcmp ancestor->descendant did not prove the same OFD (rc=None errno=1)')

    monkeypatch.setenv('SYNTH_OBS', str(observation))
    monkeypatch.setattr(lsi, 'port_is_free', lambda port: True)
    monkeypatch.setattr(lsi, '_get_json', lambda url, timeout: (200, {'status': 'ok'}))
    monkeypatch.setattr(lsi, 'process_start_ticks', lambda pid: 777)
    monkeypatch.setattr('r1.exam.cache_runtime.verify_server_lease_inheritance', verify)
    inst = lsi.LlamaServerInstance(tmp_path / 'batch', str(binary), model_path=str(model),
                                   alias='synthetic', port=43128, start_timeout=10)
    try:
        with pytest.raises(cl.LeaseStop, match='kcmp'):
            inst.start(lease_fd=fd)
        assert 'lease_inheritance' not in inst.record
        assert 'kcmp' in inst.record['lease_inheritance_failure']['reason']
    finally:
        inst.stop(timeout=5)
        os.close(fd)


def test_native_server_uses_the_environment_contract_when_no_explicit_fd(tmp_path, monkeypatch):
    binary, observation = _fake_llama_server_binary(tmp_path)
    model = tmp_path / 'model.gguf'
    model.write_bytes(b'GGUF fixture')
    path, fd, identity = make_lease(tmp_path)
    seen = {}
    monkeypatch.setenv('SYNTH_OBS', str(observation))
    monkeypatch.setenv('TRACKX_GPU_LEASE_FD', str(fd))
    monkeypatch.setattr(lsi, 'port_is_free', lambda port: True)
    monkeypatch.setattr(lsi, '_get_json', lambda url, timeout: (200, {'status': 'ok'}))
    monkeypatch.setattr(lsi, 'process_start_ticks', lambda pid: 777)
    monkeypatch.setattr('r1.exam.cache_runtime.verified_lease_fd', lambda: fd)

    def verify(server_pid, lease_fd, *, runner_pid=None, started_ticks=None):
        seen.update(server_pid=server_pid, lease_fd=lease_fd)
        return inheritance(server_pid=server_pid, start_ticks=777, runner_pid=runner_pid or os.getpid(),
                           fd=lease_fd, dev=identity[0], ino=identity[1], uid=os.fstat(fd).st_uid)

    monkeypatch.setattr('r1.exam.cache_runtime.verify_server_lease_inheritance', verify)
    inst = lsi.LlamaServerInstance(tmp_path / 'batch', str(binary), model_path=str(model),
                                   alias='synthetic', port=43129, start_timeout=10)
    try:
        record = inst.start()
        assert record['lease_inheritance']['lease_fd'] == fd
        assert seen['lease_fd'] == fd
    finally:
        inst.stop(timeout=5)
        os.close(fd)


LINUX_KCMP = (sys.platform.startswith('linux') and os.uname().machine == 'x86_64')


@pytest.mark.skipif(not LINUX_KCMP, reason='KCMP_FILE syscall 312 requires Linux x86-64')
def test_real_kcmp_proves_shared_ofd_with_a_synthetic_child(tmp_path):
    """Linux-only: pass_fds shares the OFD, a re-opened inode does not."""
    path, fd, identity = make_lease(tmp_path)
    other = tmp_path / 'other.lock'
    other.touch()
    other_fd = os.open(other, os.O_RDWR)
    reopened = os.open(path, os.O_RDWR)
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                             pass_fds=(fd, other_fd, reopened), start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        assert cl.kcmp_file_result(os.getpid(), child.pid, fd, fd) == (0, 0)
        assert cl.kcmp_same_ofd(os.getpid(), child.pid, fd, fd) is True
        # Different inode, and the same inode separately opened: never the same OFD.
        assert cl.kcmp_same_ofd(os.getpid(), child.pid, fd, other_fd) is False
        assert cl.kcmp_same_ofd(os.getpid(), child.pid, fd, reopened) is False
        # Descendant->ancestor kcmp READ permission is host/kernel dependent (Yama
        # restricts attach mode; TASL-2 was observed to permit the READ), so this
        # chain never uses or asserts it.  Only "errors never count as SAME" is
        # guaranteed by the wrapper.
        assert cl.kcmp_same_ofd(0, 0, -1, -1) is False
    finally:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=10)
        os.close(reopened)
        os.close(other_fd)
        os.close(fd)
