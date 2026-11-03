"""Guardian unit + synthetic subprocess tests; never a real lock, GPU, model or host.

Synthetic temporary locks only.  Child processes are the ones these tests create
(the guardian driver and its synthetic runner) and are cleaned up with SIGKILL
to their own process groups; no other process is ever signalled.
"""
import fcntl
import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

try:  # repository layout
    from r1.scripts import trackx_lease_guardian as guardian
except ImportError:  # byte-identical candidate-directory copy
    import guardian

REPO = Path(__file__).resolve().parents[2]
PYTHON = os.path.realpath(sys.executable)
TICKS = 4242

RUNNER = '''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
scenario = json.loads(Path(os.environ["SYNTH_SCENARIO"]).read_text(encoding="utf-8"))
evidence = Path(os.environ["TRACKX_LEASE_EVIDENCE_DIR"])
lease = os.environ.get("TRACKX_GPU_LEASE_FD")
observed = {"fd": int(lease) if lease and lease.isdecimal() else None,
            "env": {k: v for k, v in os.environ.items() if k.startswith("TRACKX_")}}
if observed["fd"] is not None:
    st = os.fstat(observed["fd"])
    observed.update(dev=st.st_dev, ino=st.st_ino)
(evidence / "runner_observed.json").write_text(json.dumps(observed))
action = scenario.get("action", "exit_zero")
if action == "sleep":
    time.sleep(float(scenario.get("seconds", 60)))
elif action == "exit_nonzero":
    if scenario.get("chmod_evidence_readonly"):
        evidence.chmod(0o500)
    sys.exit(int(scenario.get("exit_code", 7)))
elif action == "completion":
    completion = dict(scenario["completion"])
    completion["runner_pid"] = os.getpid()
    completion["runner_start_ticks"] = int(scenario.get("runner_start_ticks", os.environ.get("SYNTH_TICKS", "4242")))
    (evidence / "lease_completion.json").write_text(json.dumps(completion))
    if scenario.get("chmod_evidence_readonly"):
        evidence.chmod(0o500)
    sys.exit(int(scenario.get("exit_code", 0)))
sys.exit(0)
'''

HOLD_DRIVER = '''import importlib.util, json, os, sys
spec = importlib.util.spec_from_file_location("guardian_under_test", {guardian_file!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fd, expected = module.acquire_existing({lock!r})
dirfd = os.open({evidence!r}, os.O_RDONLY | os.O_DIRECTORY)
module.hold_forever({lock!r}, fd, expected, dirfd, "synthetic evidence write failure")
'''

DRIVER = '''import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("guardian_under_test", {guardian_file!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
state = json.load(open({state_path!r}, encoding="utf-8"))
def start_ticks(pid):
    if pid in state["absent"]:
        raise module.ProcessGone(pid)
    return state["ticks"].get(str(pid), state["default"])
def kcmp(pid_a, pid_b, fd_a, fd_b):
    return tuple(state["kcmp"])
try:
    result = module.run({lock!r}, {manifest!r}, {sha!r}, {evidence!r},
                        expected_runner={runner!r}, start_ticks=start_ticks,
                        proc_root={proc_root!r}, kcmp=kcmp)
except module.Stop as exc:
    sys.stderr.write("STOP: " + str(exc))
    sys.exit(2)
sys.exit(0 if result else 3)
'''


# -- helpers ------------------------------------------------------------------

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path), 'sha256': digest(path)}


def runner_script(tmp_path, name='runner.py'):
    path = tmp_path / name
    path.write_text(RUNNER)
    return path


def manifest_contract(tmp_path, runner, *, env=None, argv=None, files=None):
    manifest = {'version': guardian.MANIFEST_VERSION,
                'argv': argv or [PYTHON, str(runner), 'stage-a', '--out', str(tmp_path / 'out')],
                'files': files if files is not None else [pin(PYTHON), pin(runner)],
                'environment': env if env is not None else {'PYTHONPATH': str(REPO)}}
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    path = tmp_path / 'manifest.json'
    path.write_bytes(raw)
    return manifest, path, guardian._sha256(raw)


def validate(tmp_path, runner, **kwargs):
    expected = kwargs.pop('expected_runner', str(runner))
    manifest, path, sha = manifest_contract(tmp_path, runner, **kwargs)
    return guardian.validate_manifest(path.read_bytes(), sha, expected_runner=expected)


def blocked(path):
    fd = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return True
    else:
        return False
    finally:
        os.close(fd)


def wait_for(path, timeout=10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.lexists(path):
            return
        time.sleep(0.02)
    raise AssertionError(f'timed out waiting for {path}')


def ticks_map(mapping=None):
    mapping = dict(mapping or {})

    def start_ticks(pid):
        if pid in mapping:
            return mapping[pid]
        raise guardian.ProcessGone(pid)
    return start_ticks


# -- manifest hardening -------------------------------------------------------

def test_manifest_accepts_the_pinned_contract(tmp_path):
    runner = runner_script(tmp_path)
    manifest = validate(tmp_path, runner)
    assert manifest['version'] == guardian.MANIFEST_VERSION
    assert manifest['argv'][0] == PYTHON


def test_manifest_rejects_tampered_pins_and_bytes(tmp_path):
    runner = runner_script(tmp_path)
    manifest, path, sha = manifest_contract(tmp_path, runner)
    tampered = dict(manifest['files'][1])
    tampered['sha256'] = '0' * 64
    bad = json.loads(path.read_text())
    bad['files'][1] = tampered
    raw = json.dumps(bad, sort_keys=True, indent=2).encode() + b'\n'
    with pytest.raises(guardian.Stop, match='pin mismatch'):
        guardian.validate_manifest(raw, guardian._sha256(raw), expected_runner=str(runner))
    with pytest.raises(guardian.Stop, match='manifest hash mismatch'):
        guardian.validate_manifest(path.read_bytes(), '0' * 64, expected_runner=str(runner))
    with pytest.raises(guardian.Stop, match='malformed manifest sha'):
        guardian.validate_manifest(path.read_bytes(), 'not-a-sha', expected_runner=str(runner))


def test_manifest_rejects_relative_non_python_or_unexpected_runner(tmp_path):
    runner = runner_script(tmp_path)
    with pytest.raises(guardian.Stop, match='absolute'):
        validate(tmp_path, runner, argv=['python3', str(runner)])
    with pytest.raises(guardian.Stop, match='absolute'):
        validate(tmp_path, runner, argv=[PYTHON, 'r1/scripts/exam_runner.py'])
    with pytest.raises(guardian.Stop, match='python interpreter'):
        validate(tmp_path, runner, argv=['/bin/sh', str(runner)])
    with pytest.raises(guardian.Stop, match='python runner script'):
        validate(tmp_path, runner, argv=[PYTHON, str(tmp_path / 'not-python.txt')])
    other = runner_script(tmp_path, 'other_runner.py')
    with pytest.raises(guardian.Stop, match='expected pinned runner'):
        validate(tmp_path, runner, expected_runner=str(other))
    extra = tmp_path / 'extra.txt'
    extra.write_text('unused')
    with pytest.raises(guardian.Stop, match='runner is not pinned'):
        validate(tmp_path, runner, files=[pin(PYTHON), pin(extra)])


@pytest.mark.parametrize('key', ['TRACKX_GPU_LEASE_FD', 'TRACKX_LEASE_EVIDENCE_DIR',
                                'TRACKX_GPU_GUARDIAN_PID'])
def test_manifest_rejects_reserved_trackx_environment(tmp_path, key):
    runner = runner_script(tmp_path)
    with pytest.raises(guardian.Stop, match='reserved TRACKX_'):
        validate(tmp_path, runner, env={'PYTHONPATH': str(REPO), key: '1'})


def test_manifest_rejects_extra_keys_wrong_version_and_duplicates(tmp_path):
    runner = runner_script(tmp_path)
    manifest, path, _ = manifest_contract(tmp_path, runner)
    for mutation, message in [
        ({'extra': 1}, 'schema'),
        ({'version': 'trackx_guardian_manifest/v2'}, 'version'),
        ({'files': [pin(PYTHON), pin(PYTHON)]}, 'duplicate'),
        ({'files': []}, 'pin list'),
        ({'environment': {'A': 1}}, 'environment'),
        ({'environment': {'A': 'b', 'C=D': 'e'}}, 'environment'),
    ]:
        raw = json.dumps({**manifest, **mutation}, sort_keys=True).encode()
        with pytest.raises(guardian.Stop, match=message):
            guardian.validate_manifest(raw, guardian._sha256(raw), expected_runner=str(runner))
    with pytest.raises(guardian.Stop, match='invalid manifest JSON'):
        guardian.validate_manifest(b'{', guardian._sha256(b'{'), expected_runner=str(runner))


def test_pinned_file_must_be_a_single_link_regular_file(tmp_path):
    runner = runner_script(tmp_path)
    link = tmp_path / 'runner-link.py'
    link.symlink_to(runner)
    with pytest.raises(guardian.Stop, match='unable to read pinned file'):
        validate(tmp_path, runner, files=[pin(PYTHON), pin(link)])
    hard = tmp_path / 'runner-hard.py'
    os.link(runner, hard)
    with pytest.raises(guardian.Stop, match='unsafe file'):
        validate(tmp_path, runner, files=[pin(PYTHON), pin(hard)])


def test_default_expected_runner_is_the_pinned_exam_runner():
    assert guardian._default_expected_runner() == str(REPO / 'r1/scripts/exam_runner.py')


# -- lock ownership -----------------------------------------------------------

def test_lock_is_never_created_and_symlink_or_hardlink_rejected(tmp_path):
    absent = tmp_path / 'absent.lock'
    with pytest.raises(guardian.Stop, match='cannot be acquired'):
        guardian.acquire_existing(str(absent))
    assert not absent.exists()
    lock = tmp_path / 'lock'
    lock.touch()
    fd, expected = guardian.acquire_existing(str(lock))
    try:
        symlink = tmp_path / 'symlink.lock'
        symlink.symlink_to(lock)
        with pytest.raises(guardian.Stop):
            guardian.acquire_existing(str(symlink))
        hard = tmp_path / 'hard.lock'
        os.link(lock, hard)
        with pytest.raises(guardian.Stop, match='link count'):
            guardian.acquire_existing(str(hard))
    finally:
        os.close(fd)


def test_assert_held_detects_replacement_and_contender(tmp_path):
    lock = tmp_path / 'lock'
    lock.touch()
    fd, expected = guardian.acquire_existing(str(lock))
    try:
        assert guardian.assert_held(str(lock), fd, expected) is True
        with pytest.raises(guardian.Stop, match='cannot be acquired'):
            guardian.acquire_existing(str(lock))
        replacement = tmp_path / 'replacement'
        replacement.touch()
        with pytest.raises(guardian.Stop, match='no longer names'):
            guardian.assert_held(str(replacement), fd, expected)
        lock.rename(tmp_path / 'old')
        lock.touch()
        with pytest.raises(guardian.Stop, match='no longer names'):
            guardian.assert_held(str(lock), fd, expected)
    finally:
        os.close(fd)


def test_evidence_persistence_is_exclusive_and_retries_short_writes(tmp_path, monkeypatch):
    module = sys.modules[guardian.__name__]
    dirfd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        guardian.persist_exclusive(dirfd, 'start.json', {'version': 1})
        assert json.loads((tmp_path / 'start.json').read_text()) == {'version': 1}
        with pytest.raises(FileExistsError):
            guardian.persist_exclusive(dirfd, 'start.json', {'version': 2})
        original = os.write
        monkeypatch.setattr(module.os, 'write', lambda fd, data: original(fd, data[:3]))
        guardian.persist_exclusive(dirfd, 'short.json', {'text': 'hello'})
        monkeypatch.undo()
        assert json.loads((tmp_path / 'short.json').read_text()) == {'text': 'hello'}
    finally:
        os.close(dirfd)


# -- completion validation ----------------------------------------------------

def completion_fixture(tmp_path, *, server_pid=999999, start_ticks=555, extra_record=False):
    out = tmp_path / 'out'
    (out / 'servers' / 'cand').mkdir(parents=True)
    batch_state = out / 'batch_state.json'
    batch_state.write_text(json.dumps({'status': 'COMPLETE'}) + '\n')
    record = {'pid': server_pid, 'stopped_utc': '2026-10-31T00:00:00Z',
              'lease_inheritance': {'version': 'trackx_lease_inheritance/v1',
                                    'method': 'proc_fd_dev_ino_and_kcmp_file_ancestor_to_descendant',
                                    'runner_pid': 123, 'runner_start_ticks': 4, 'server_pid': server_pid,
                                    'server_start_ticks': start_ticks, 'server_ppid': 123, 'lease_fd': 7,
                                    'dev': 1, 'ino': 2, 'uid': 0, 'server_fd_dev': 1, 'server_fd_ino': 2,
                                    'server_lease_fds': [7], 'fd_set_exact': True, 'kcmp_pid_a': 123,
                                    'kcmp_pid_b': server_pid, 'kcmp_fd_a': 7, 'kcmp_fd_b': 7, 'kcmp_rc': 0,
                                    'kcmp_same_ofd': True, 'kcmp_errors_never_same': True,
                                    'yama_direction': 'ancestor->descendant', 'monotonic_ns': 1,
                                    'cold_verified': False, 'scope': 'synthetic'}}
    record_path = out / 'servers' / 'cand' / 'llama_server_9000.json'
    record_path.write_text(json.dumps(record) + '\n')
    if extra_record:
        extra = json.loads(json.dumps(record))
        extra['pid'] = 1
        extra['lease_inheritance']['server_pid'] = 1
        extra['lease_inheritance']['kcmp_pid_b'] = 1
        (out / 'servers' / 'cand' / 'llama_server_9001.json').write_text(json.dumps(extra) + '\n')
    completion = {'version': guardian.COMPLETION_VERSION,
                  'batch_state': str(batch_state),
                  'batch_state_sha256': digest(batch_state),
                  'servers': [{'pid': server_pid, 'start_ticks': start_ticks,
                               'stopped_utc': '2026-10-31T00:00:00Z',
                               'record_sha256': digest(record_path),
                               'record_path': str(record_path.resolve())}],
                  'runner_pid': 1234, 'runner_start_ticks': TICKS}
    return completion, record_path, batch_state


def nested_probe_completion_fixture(tmp_path, *, server_pid=999999, start_ticks=555,
                                    probe_start_ticks=777):
    """B2 regression: Stage A always writes a qualification-probe record outside servers/."""
    out = tmp_path / 'out'
    probe_dir = out / 'cand' / 'stage-a' / '32768' / 'qualification' / 'probe_fixture'
    probe_dir.mkdir(parents=True)
    batch_state = out / 'batch_state.json'
    batch_state.write_text(json.dumps({'status': 'COMPLETE'}) + '\n')

    def record(pid, ticks):
        return {'pid': pid, 'stopped_utc': '2026-10-31T00:00:00Z',
                'lease_inheritance': {'version': 'trackx_lease_inheritance/v1',
                                      'server_pid': pid, 'server_start_ticks': ticks,
                                      'kcmp_rc': 0, 'kcmp_same_ofd': True}}

    probe_path = probe_dir / 'llama_server_9010.json'
    probe_path.write_text(json.dumps(record(555000, probe_start_ticks)) + '\n')
    servers_path = out / 'servers' / 'cand' / 'llama_server_9000.json'
    servers_path.parent.mkdir(parents=True)
    servers_path.write_text(json.dumps(record(server_pid, start_ticks)) + '\n')
    completion = {'version': guardian.COMPLETION_VERSION,
                  'batch_state': str(batch_state),
                  'batch_state_sha256': digest(batch_state),
                  'servers': [
                      {'pid': 555000, 'start_ticks': probe_start_ticks,
                       'stopped_utc': '2026-10-31T00:00:00Z',
                       'record_sha256': digest(probe_path),
                       'record_path': str(probe_path.resolve())},
                      {'pid': server_pid, 'start_ticks': start_ticks,
                       'stopped_utc': '2026-10-31T00:00:00Z',
                       'record_sha256': digest(servers_path),
                       'record_path': str(servers_path.resolve())}],
                  'runner_pid': 1234, 'runner_start_ticks': TICKS}
    return completion, batch_state, probe_path, servers_path


def completion_lock(tmp_path):
    lock = tmp_path / 'lock'
    lock.touch()
    fd, expected = guardian.acquire_existing(str(lock))
    return lock, fd, expected


def validate_completion(completion, lock, fd, expected, start_ticks):
    return guardian.validate_completion(completion, runner_pid=1234, runner_start_ticks=TICKS,
                                        lock_path=str(lock), lock_fd=fd, expected_lock=expected,
                                        start_ticks=start_ticks)


def test_valid_completion_is_accepted_only_after_full_validation(tmp_path):
    completion, record_path, batch_state = completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        summary = validate_completion(completion, lock, fd, expected, ticks_map())
        assert summary['records_verified'] == 1
        assert summary['servers'][0]['pid'] == 999999
        assert summary['batch_state'] == str(batch_state)
        assert summary['completion_sha256'] is None
        assert 'NOT_CHECKABLE' in summary['scope']
        assert (summary['servers'][0]['record_sha256']) == digest(record_path)
    finally:
        os.close(fd)


@pytest.mark.parametrize('mutation,start_ticks_factory,message', [
    ({'version': 'trackx_lease_completion/v0'}, ticks_map, 'unsupported completion version'),
    ({'extra': 1}, ticks_map, 'schema'),
    ({'runner_pid': 999}, ticks_map, 'runner pid'),
    ({'runner_start_ticks': 1}, ticks_map, 'runner start ticks'),
    ({'batch_state_sha256': '0' * 64}, ticks_map, 'batch_state digest'),
    ({'batch_state': 'relative/batch_state.json'}, ticks_map, 'absolute'),
])
def test_completion_schema_and_identity_mismatch_hold(tmp_path, mutation, start_ticks_factory, message):
    completion, _, _ = completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        with pytest.raises(guardian.Stop, match=message):
            validate_completion({**completion, **mutation}, lock, fd, expected, start_ticks_factory())
    finally:
        os.close(fd)


def test_live_server_pid_and_pid_reuse_are_distinguished(tmp_path):
    completion, _, _ = completion_fixture(tmp_path, server_pid=4242, start_ticks=555)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        with pytest.raises(guardian.Stop, match='still live'):
            validate_completion(completion, lock, fd, expected, ticks_map({4242: 555}))
        # Different start ticks mean the pid was reused: the recorded server is gone.
        summary = validate_completion(completion, lock, fd, expected, ticks_map({4242: 556}))
        assert summary['servers'][0]['pid'] == 4242
    finally:
        os.close(fd)


def test_completion_rejects_running_batch_bad_records_and_uncovered_records(tmp_path):
    completion, record_path, batch_state = completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        batch_state.write_text(json.dumps({'status': 'RUNNING'}) + '\n')
        with pytest.raises(guardian.Stop, match='not COMPLETE'):
            validate_completion({**completion, 'batch_state_sha256': digest(batch_state)},
                                lock, fd, expected, ticks_map())
    finally:
        os.close(fd)
    completion, record_path, batch_state = completion_fixture(tmp_path / 'second')
    lock, fd, expected = completion_lock(tmp_path / 'second')
    try:
        with pytest.raises(guardian.Stop, match='record digest/pid'):
            validate_completion({**completion, 'servers': [{**completion['servers'][0],
                                                            'record_sha256': '0' * 64}]},
                                lock, fd, expected, ticks_map())
        document = json.loads(record_path.read_text())
        document['lease_inheritance']['kcmp_rc'] = 1
        record_path.write_text(json.dumps(document) + '\n')
        with pytest.raises(guardian.Stop, match='SAME-OFD'):
            validate_completion({**completion, 'servers': [{**completion['servers'][0],
                                                            'record_sha256': digest(record_path)}]},
                                lock, fd, expected, ticks_map())
    finally:
        os.close(fd)
    completion, record_path, batch_state = completion_fixture(tmp_path / 'third', extra_record=True)
    lock, fd, expected = completion_lock(tmp_path / 'third')
    try:
        with pytest.raises(guardian.Stop, match='does not cover every server record'):
            validate_completion(completion, lock, fd, expected, ticks_map())
    finally:
        os.close(fd)


def test_nested_qualification_probe_record_is_covered_and_accepted(tmp_path):
    completion, batch_state, probe_path, servers_path = nested_probe_completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        summary = validate_completion(completion, lock, fd, expected, ticks_map())
        assert summary['records_verified'] == 2
        assert set(summary['record_files']) == {str(probe_path.resolve()), str(servers_path.resolve())}
    finally:
        os.close(fd)


def test_completion_rejects_record_outside_run_root_and_unlisted_nested_record(tmp_path):
    completion, batch_state, probe_path, servers_path = nested_probe_completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        outside = tmp_path / 'outside' / 'llama_server_1.json'
        outside.parent.mkdir()
        outside.write_text(probe_path.read_text())
        forged = json.loads(json.dumps(completion))
        forged['servers'][0].update({'record_path': str(outside), 'record_sha256': digest(outside)})
        with pytest.raises(guardian.Stop, match='does not cover every server record'):
            validate_completion(forged, lock, fd, expected, ticks_map())
        # An unlisted extra record under the run root (survivor blind spot) must fail.
        extra = servers_path.parent / 'llama_server_9001.json'
        extra.write_text(servers_path.read_text())
        with pytest.raises(guardian.Stop, match='does not cover every server record'):
            validate_completion(completion, lock, fd, expected, ticks_map())
    finally:
        os.close(fd)


def test_completion_rejects_record_path_mismatching_its_digest(tmp_path):
    completion, batch_state, probe_path, servers_path = nested_probe_completion_fixture(tmp_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        forged = json.loads(json.dumps(completion))
        forged['servers'][0]['record_sha256'] = digest(servers_path)
        with pytest.raises(guardian.Stop, match='digest/pid does not match its record file'):
            validate_completion(forged, lock, fd, expected, ticks_map())
    finally:
        os.close(fd)


# -- synthetic subprocess lifecycle -------------------------------------------

def launch(tmp_path, scenario, *, stdout=subprocess.DEVNULL, expected_runner=None,
           manifest_tamper=None):
    lock = tmp_path / 'gpu0.lock'
    lock.touch(mode=0o600)
    evidence = tmp_path / 'evidence'
    runner = runner_script(tmp_path)
    scenario_path = tmp_path / 'scenario.json'
    scenario_path.write_text(json.dumps(scenario))
    manifest, manifest_path, sha = manifest_contract(
        tmp_path, runner, env={'SYNTH_SCENARIO': str(scenario_path)})
    state_path = tmp_path / 'state.json'
    state_path.write_text(json.dumps({'absent': scenario.get('absent', []),
                                      'ticks': scenario.get('ticks', {}),
                                      'default': TICKS, 'kcmp': scenario.get('kcmp', [0, 0])}))
    proc_root = tmp_path / 'proc'
    proc_root.mkdir(exist_ok=True)
    if manifest_tamper is not None:
        document = json.loads(manifest_path.read_text())
        manifest_tamper(document)
        manifest_path.write_text(json.dumps(document))
    driver = tmp_path / 'driver.py'
    driver.write_text(DRIVER.format(guardian_file=str(Path(guardian.__file__).resolve()),
                                    state_path=str(state_path), lock=str(lock),
                                    manifest=str(manifest_path), sha=sha, evidence=str(evidence),
                                    runner=str(runner), proc_root=str(proc_root)))
    process = subprocess.Popen([PYTHON, str(driver)], stdout=stdout, stderr=subprocess.PIPE,
                               cwd=str(tmp_path), start_new_session=True)
    context = {'process': process, 'lock': lock, 'evidence': evidence, 'runner': runner,
               'scenario': scenario, 'tmp': tmp_path, 'stderr': process.stderr}
    return context


def wait_started(context):
    wait_for(context['evidence'] / 'start.json')
    wait_for(context['evidence'] / 'runner.json')


def wait_hold(context, reason, timeout=15.0):
    stop = context['evidence'] / 'STOP.json'
    wait_for(stop, timeout=timeout)
    document = json.loads(stop.read_text())
    assert document['status'] == 'STOP' and document['lease_retained'] is True
    assert reason in document['reason']
    assert context['process'].poll() is None
    assert blocked(context['lock'])
    return document


def cleanup(context):
    process = context['process']
    runner_record = context['evidence'] / 'runner.json'
    if runner_record.exists():
        try:
            runner_pid = json.loads(runner_record.read_text())['runner_pid']
            os.killpg(runner_pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, ValueError, OSError):
            pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    evidence = context['evidence']
    if evidence.exists():
        for entry in evidence.iterdir():
            try:
                entry.chmod(0o600)
            except OSError:
                pass
        try:
            evidence.chmod(0o700)
        except OSError:
            pass


def release_scenario(tmp_path):
    completion, record_path, batch_state = completion_fixture(tmp_path, server_pid=999999, start_ticks=555)
    return {'action': 'completion', 'completion': completion, 'absent': [999999]}


def test_valid_completion_releases_the_lock_and_keeps_the_inode(tmp_path):
    context = launch(tmp_path, release_scenario(tmp_path))
    try:
        before = os.stat(context['lock'])
        wait_started(context)
        assert context['process'].wait(timeout=20) == 0
        release = json.loads((context['evidence'] / 'lease_release.json').read_text())
        assert release['released'] is True and release['reason'] == 'validated_completion'
        assert release['lock_file_modified'] is False and release['lock_file_deleted'] is False
        assert release['completion']['records_verified'] == 1
        after = os.stat(context['lock'])
        assert (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
        assert stat.S_ISREG(after.st_mode)
        assert not blocked(context['lock'])
        assert (context['evidence'] / 'lease_inheritance.json').exists()
        inheritance = json.loads((context['evidence'] / 'lease_inheritance.json').read_text())
        assert inheritance['kcmp_rc'] == 0 and inheritance['kcmp_same_ofd'] is True
        observed = json.loads((context['evidence'] / 'runner_observed.json').read_text())
        assert observed['fd'] is not None and observed['env']['TRACKX_GPU_LEASE_FD'] == str(observed['fd'])
        assert observed['env']['TRACKX_LEASE_EVIDENCE_DIR'] == str(context['evidence'])
        for key in ('TRACKX_GPU_LEASE_DEV', 'TRACKX_GPU_LEASE_INO', 'TRACKX_GPU_LEASE_UID',
                    'TRACKX_GPU_GUARDIAN_PID', 'TRACKX_GPU_GUARDIAN_START_TICKS'):
            assert key in observed['env']
        assert not (context['evidence'] / 'STOP.json').exists()
    finally:
        cleanup(context)


def test_runner_zero_without_completion_keeps_the_lock(tmp_path):
    context = launch(tmp_path, {'action': 'exit_zero'})
    try:
        wait_started(context)
        wait_hold(context, 'without lease_completion.json')
        assert not (context['evidence'] / 'lease_release.json').exists()
    finally:
        cleanup(context)


def test_runner_nonzero_keeps_the_lock(tmp_path):
    context = launch(tmp_path, {'action': 'exit_nonzero', 'exit_code': 7})
    try:
        wait_started(context)
        wait_hold(context, 'rc=7')
    finally:
        cleanup(context)


def test_live_server_completion_keeps_the_lock(tmp_path):
    completion, _, _ = completion_fixture(tmp_path, server_pid=4242, start_ticks=TICKS)
    context = launch(tmp_path, {'action': 'completion', 'completion': completion})
    try:
        wait_started(context)
        wait_hold(context, 'still live')
        assert not (context['evidence'] / 'lease_release.json').exists()
    finally:
        cleanup(context)


def test_tampered_record_digest_keeps_the_lock(tmp_path):
    completion, record_path, _ = completion_fixture(tmp_path)
    completion['servers'][0]['record_sha256'] = '0' * 64
    context = launch(tmp_path, {'action': 'completion', 'completion': completion, 'absent': [999999]})
    try:
        wait_started(context)
        wait_hold(context, 'record digest/pid')
    finally:
        cleanup(context)


def test_tampered_batch_state_digest_keeps_the_lock(tmp_path):
    completion, _, _ = completion_fixture(tmp_path)
    completion['batch_state_sha256'] = '0' * 64
    context = launch(tmp_path, {'action': 'completion', 'completion': completion, 'absent': [999999]})
    try:
        wait_started(context)
        wait_hold(context, 'digest mismatch')
    finally:
        cleanup(context)


def test_runner_identity_mismatch_keeps_the_lock(tmp_path):
    context = launch(tmp_path, {**release_scenario(tmp_path), 'runner_start_ticks': 999})
    try:
        wait_started(context)
        wait_hold(context, 'runner start ticks')
    finally:
        cleanup(context)


def test_kcmp_failure_keeps_the_lock(tmp_path):
    context = launch(tmp_path, {'action': 'exit_zero', 'kcmp': [1, 0]})
    try:
        wait_for(context['evidence'] / 'start.json')
        wait_hold(context, 'kcmp')
    finally:
        cleanup(context)


def test_eperm_kcmp_keeps_the_lock(tmp_path):
    context = launch(tmp_path, {'action': 'exit_zero', 'kcmp': [None, 1]})
    try:
        wait_for(context['evidence'] / 'start.json')
        wait_hold(context, 'kcmp')
    finally:
        cleanup(context)


@pytest.mark.parametrize('number', ['SIGTERM', 'SIGHUP', 'SIGINT'])
def test_termination_signals_keep_the_process_and_lock(tmp_path, number):
    context = launch(tmp_path, {'action': 'sleep', 'seconds': 60})
    try:
        wait_started(context)
        context['process'].send_signal(getattr(signal, number))
        wait_hold(context, 'termination signal')
    finally:
        cleanup(context)


def test_closed_stdout_and_unwritable_evidence_still_hold(tmp_path):
    read_fd, write_fd = os.pipe()
    context = launch(tmp_path, {'action': 'exit_nonzero', 'chmod_evidence_readonly': True},
                     stdout=write_fd)
    os.close(write_fd)
    try:
        wait_started(context)
        os.close(read_fd)
        read_fd = None
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not (context['evidence'] / 'runner_observed.json').exists():
            time.sleep(0.05)
        time.sleep(2.5)
        assert context['process'].poll() is None
        assert blocked(context['lock'])
        assert not (context['evidence'] / 'STOP.json').exists()
    finally:
        if read_fd is not None:
            os.close(read_fd)
        cleanup(context)


def test_hold_forever_survives_broken_stdout_without_evidence(tmp_path):
    lock = tmp_path / 'gpu0.lock'
    lock.touch()
    evidence = tmp_path / 'evidence'
    evidence.mkdir(mode=0o700)
    evidence.chmod(0o500)
    driver = tmp_path / 'hold_driver.py'
    driver.write_text(HOLD_DRIVER.format(guardian_file=str(Path(guardian.__file__).resolve()),
                                         lock=str(lock), evidence=str(evidence)))
    read_fd, write_fd = os.pipe()
    process = subprocess.Popen([PYTHON, str(driver)], stdout=write_fd, stderr=subprocess.DEVNULL,
                               cwd=str(tmp_path), start_new_session=True)
    os.close(write_fd)
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not blocked(lock):
            time.sleep(0.05)
        os.close(read_fd)
        read_fd = None
        time.sleep(2.5)
        assert process.poll() is None
        assert blocked(lock)
        assert not (evidence / 'STOP.json').exists()
    finally:
        if read_fd is not None:
            os.close(read_fd)
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=10)
        evidence.chmod(0o700)


def test_existing_evidence_directory_or_manifest_tamper_is_refused_before_lock(tmp_path):
    context = launch(tmp_path, {'action': 'exit_zero'})
    context['evidence'].mkdir()
    try:
        assert context['process'].wait(timeout=20) == 2
        stderr = context['stderr'].read().decode()
        assert 'never resume' in stderr
        assert not blocked(context['lock'])
    finally:
        cleanup(context)
    tampered_dir = tmp_path / 'tampered'
    tampered_dir.mkdir()
    tampered = launch(tampered_dir, {'action': 'exit_zero'},
                      manifest_tamper=lambda document: document['argv'].append('--tampered'))
    try:
        assert tampered['process'].wait(timeout=20) == 2
        assert 'manifest hash mismatch' in tampered['stderr'].read().decode()
        assert not blocked(tampered['lock'])
    finally:
        cleanup(tampered)


def test_missing_lock_is_refused_without_creating_it(tmp_path):
    context = launch(tmp_path, {'action': 'exit_zero'})
    context['lock'].unlink()
    try:
        assert context['process'].wait(timeout=20) == 2
        assert 'cannot be acquired' in context['stderr'].read().decode()
        assert not context['lock'].exists()
    finally:
        cleanup(context)


def test_a_launcher_style_repo_manifest_validates(tmp_path):
    """The reviewed launcher pins every r1/*.py plus the runner: that must validate."""
    if not (REPO / 'r1/scripts/exam_runner.py').is_file():
        pytest.skip('repository tree not present next to this copy')
    rows = {}
    for path in sorted((REPO / 'r1').rglob('*.py')):
        if path.is_file():
            rows[str(path)] = digest(path)
    rows[str(REPO / 'r1/scripts/trackx_lease_guardian.py')] = digest(REPO / 'r1/scripts/trackx_lease_guardian.py')
    rows[str(REPO / 'r1/scripts/configs/exam_portal.json')] = digest(REPO / 'r1/scripts/configs/exam_portal.json')
    files = [{'path': path, 'sha256': sha} for path, sha in sorted(rows.items())]
    assert len({row['path'] for row in files}) > 50
    runner = REPO / 'r1/scripts/exam_runner.py'
    manifest = {'version': guardian.MANIFEST_VERSION,
                'argv': [PYTHON, str(runner), 'stage-a', '--config', 'config.json', '--out', 'out'],
                'files': files,
                'environment': {'PYTHONPATH': str(REPO), 'PYTHONDONTWRITEBYTECODE': '1'}}
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    validated = guardian.validate_manifest(raw, guardian._sha256(raw), expected_runner=str(runner))
    assert validated['argv'][1] == str(runner)
    assert guardian._default_expected_runner() == str(runner)


def test_completion_server_start_ticks_must_match_its_record(tmp_path):
    completion, _, _ = completion_fixture(tmp_path, server_pid=4242, start_ticks=555)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        tampered = {**completion, 'servers': [{**completion['servers'][0], 'start_ticks': 556}]}
        with pytest.raises(guardian.Stop, match='identity/time differs'):
            validate_completion(tampered, lock, fd, expected, ticks_map())
    finally:
        os.close(fd)


def test_completion_accepts_a_failed_start_record_with_lease_inheritance(tmp_path):
    """A pre-readiness failure is a legitimate stopped record if it carries the proof."""
    completion, record_path, batch_state = completion_fixture(tmp_path)
    record = json.loads(record_path.read_text())
    record.update(exited_early=1, returncode=1, stopped_before_ready=True)
    record.pop('healthy_utc', None)
    record_path.write_text(json.dumps(record) + '\n')
    completion['servers'][0]['record_sha256'] = digest(record_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        summary = validate_completion(completion, lock, fd, expected, ticks_map())
        assert summary['records_verified'] == 1
    finally:
        os.close(fd)


def test_completion_rejects_a_failed_start_record_without_inheritance(tmp_path):
    completion, record_path, batch_state = completion_fixture(tmp_path)
    record = json.loads(record_path.read_text())
    record.update(exited_early=1, returncode=1, stopped_before_ready=True)
    record.pop('lease_inheritance')
    record.pop('healthy_utc', None)
    record_path.write_text(json.dumps(record) + '\n')
    completion['servers'][0]['record_sha256'] = digest(record_path)
    lock, fd, expected = completion_lock(tmp_path)
    try:
        with pytest.raises(guardian.Stop, match='lacks lease inheritance evidence'):
            validate_completion(completion, lock, fd, expected, ticks_map())
    finally:
        os.close(fd)
