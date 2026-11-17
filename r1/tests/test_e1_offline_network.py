"""R1-E1-OPENML-AMEND requirement (b): enforced worker network denial tests.

Kernel-level installation is exercised only in a disposable child process and
only on Linux x86-64 (``test_linux_install_denies_sockets``); the decision
logic, compile-time filter shape and every STOP path run everywhere.
"""
import json
import platform
import subprocess
import sys
import types

import pytest

from r1.c3 import e1_offline_network as N

DENIED = {'seccomp_mode': 2, 'af_inet': {'errno': 101, 'error': 'ENETUNREACH'},
          'af_inet6': {'errno': 101, 'error': 'ENETUNREACH'},
          'connect': {'errno': 101, 'error': 'ENETUNREACH'}, 'denied': True}


def _report(**overrides):
    report = json.loads(json.dumps(DENIED))
    report.update(overrides)
    return report


# ---------------------------------------------------------------------------- filter shape (pure)

def test_filter_is_an_errno_deny_filter_with_arch_and_x32_guards():
    program = N.compile_filter()
    assert program[0][0] == N._LD_W_ABS and program[0][3] == 4          # arch field
    assert program[1][:3] == (N._JMP_JEQ_K, 1, 0) and program[1][3] == N.AUDIT_ARCH_X86_64
    assert program[2][0] == N._RET_K and program[2][3] == N.SECCOMP_RET_KILL_PROCESS
    assert program[4][0] == N._JMP_JGE_K and program[4][3] == N.X32_SYSCALL_BIT
    assert program[5][0] == N._RET_K and program[5][3] == N.SECCOMP_RET_KILL_PROCESS
    assert program[-1][0] == N._RET_K and program[-1][3] == N.SECCOMP_RET_ALLOW
    errno_returns = [(instruction[3]) for instruction in program
                     if instruction[0] == N._RET_K and instruction[3] & 0xFFFF0000 == N.SECCOMP_RET_ERRNO]
    assert errno_returns, 'no SECCOMP_RET_ERRNO returns in the program'
    assert all(value == (N.SECCOMP_RET_ERRNO | N.DENIED_ERRNO) for value in errno_returns)
    assert not any(instruction[3] == N.SECCOMP_RET_USER_NOTIF for instruction in program)
    guarded = {instruction[3] for instruction in program if instruction[0] == N._JMP_JEQ_K}
    assert set(N.BLOCKED_SYSCALLS.values()) <= guarded
    assert N.DENIED_ERRNO == 101 and N.DENIED_ERRNAME == 'ENETUNREACH'


def test_every_blocked_syscall_has_its_own_errno_return():
    program = N.compile_filter()
    body = program[6:-1]
    assert len(body) == 2 * len(N.BLOCKED_SYSCALLS)
    for offset in range(0, len(body), 2):
        jump, ret = body[offset], body[offset + 1]
        assert jump[0] == N._JMP_JEQ_K and jump[1] == 0 and jump[2] == 1
        assert ret[0] == N._RET_K and ret[3] == (N.SECCOMP_RET_ERRNO | N.DENIED_ERRNO)


def _run_bpf(program, nr, arch=N.AUDIT_ARCH_X86_64):
    """Minimal classic-BPF interpreter for the compiled seccomp program (any host)."""
    data = nr.to_bytes(4, 'little') + arch.to_bytes(4, 'little')
    accumulator, pc = 0, 0
    while True:
        code, jt, jf, k = program[pc]
        if code == N._LD_W_ABS:
            accumulator = int.from_bytes(data[k:k + 4], 'little')
            pc += 1
        elif code == N._JMP_JEQ_K:
            pc = pc + 1 + (jt if accumulator == k else jf)
        elif code == N._JMP_JGE_K:
            pc = pc + 1 + (jt if accumulator >= k else jf)
        elif code == N._RET_K:
            return k
        else:  # pragma: no cover - the compiler never emits another opcode
            raise AssertionError(f'unexpected BPF opcode {code}')


def test_filter_decisions_are_enforced_for_every_blocked_syscall():
    program = N.compile_filter()
    denied = N.SECCOMP_RET_ERRNO | N.DENIED_ERRNO
    for name, number in N.BLOCKED_SYSCALLS.items():
        assert _run_bpf(program, number) == denied, name
    assert _run_bpf(program, 0) == N.SECCOMP_RET_ALLOW           # read(2) is untouched
    assert _run_bpf(program, 1) == N.SECCOMP_RET_ALLOW           # write(2) is untouched
    assert _run_bpf(program, N.X32_SYSCALL_BIT | 42) == N.SECCOMP_RET_KILL_PROCESS
    assert _run_bpf(program, 42, arch=0x40000003) == N.SECCOMP_RET_KILL_PROCESS  # i386 ABI
    assert _run_bpf(program, 42, arch=0xC00000B7) == N.SECCOMP_RET_KILL_PROCESS  # aarch64 ABI


# ---------------------------------------------------------------------------- enforce() STOP paths

def test_non_linux_host_cannot_enforce_network_denial(monkeypatch):
    monkeypatch.setattr(N.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(N.platform, 'machine', lambda: 'arm64')
    with pytest.raises(N.NetworkDenialStop, match='Linux x86-64'):
        N.install()
    with pytest.raises(N.NetworkDenialStop, match='Linux x86-64'):
        N.enforce()


@pytest.mark.skipif(platform.system() == 'Linux', reason='installs an irreversible filter on Linux')
def test_install_refuses_the_current_non_linux_host():
    with pytest.raises(N.NetworkDenialStop, match='Linux x86-64'):
        N.install()


def test_install_failure_is_a_stop():
    def installer():
        raise OSError(1, 'Operation not permitted')

    with pytest.raises(N.NetworkDenialStop, match='could not be installed'):
        N.enforce(installer=installer)


def test_network_denial_stop_from_installer_is_propagated():
    def installer():
        raise N.NetworkDenialStop('STOP: no seccomp support')

    def in_process():
        return _report()

    def child():
        return _report()

    with pytest.raises(N.NetworkDenialStop, match='no seccomp support'):
        N.enforce(installer=installer, in_process=in_process, child=child)


def test_successful_enforcement_requires_proof_in_process_and_in_the_worker_child():
    calls = []

    def installer():
        calls.append('install')

    def in_process():
        calls.append('in_process')
        return _report()

    def child():
        calls.append('child')
        return _report()

    report = N.enforce(installer=installer, in_process=in_process, child=child)
    assert calls == ['install', 'in_process', 'child']
    assert report['enforced'] is True and report['schema'] == N.SCHEMA
    assert report['denied_errno'] == N.DENIED_ERRNO
    assert sorted(N.BLOCKED_SYSCALLS) == report['blocked_syscalls']


@pytest.mark.parametrize('where, report, message', [
    ('in_process', _report(denied=False), 'not proven in the replay process'),
    ('in_process', _report(seccomp_mode=0), 'not running under a seccomp filter'),
    ('in_process', _report(af_inet={'created': True}), 'for af_inet'),
    ('child', _report(connect={'connected': True}), 'for connect'),
])
def test_unproven_denial_is_a_stop(where, report, message):
    def in_process():
        return _report()

    def child():
        return _report()

    kwargs = {'in_process': in_process, 'child': child}
    kwargs[where] = lambda: report
    with pytest.raises(N.NetworkDenialStop, match=message):
        N.enforce(installer=lambda: None, **kwargs)


def test_child_probe_without_report_is_a_stop(monkeypatch):
    def fake_run(*_args, **_kwargs):
        return types.SimpleNamespace(returncode=0, stdout='no marker here\n', stderr='')

    monkeypatch.setattr(N.subprocess, 'run', fake_run)
    with pytest.raises(N.NetworkDenialStop, match='no report'):
        N.child_probe()


def test_child_probe_is_worker_representative(monkeypatch):
    seen = {}

    def fake_run(argv, **kwargs):
        seen['argv'] = argv
        seen['env'] = kwargs.get('env') or {}
        return types.SimpleNamespace(returncode=0, stdout=N.MARKER + json.dumps(DENIED) + '\n', stderr='')

    monkeypatch.setattr(N.subprocess, 'run', fake_run)
    report = N.child_probe()
    assert report['denied'] is True
    assert seen['argv'][0] == sys.executable and seen['argv'][1] == '-B' and seen['argv'][2] == '-c'
    assert seen['env']['PYTHONDONTWRITEBYTECODE'] == '1'


def test_reverify_requires_the_post_run_proof():
    with pytest.raises(N.NetworkDenialStop, match='post-run'):
        N.reverify(child=lambda: _report(denied=False))
    assert N.reverify(child=lambda: _report())['denied'] is True


# ---------------------------------------------------------------------------- real kernel check (Linux)

@pytest.mark.skipif(platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'),
                    reason='needs Linux x86-64 seccomp')
def test_linux_install_denies_sockets(tmp_path):
    script = tmp_path / 'probe.py'
    script.write_text(
        'import json, sys\n'
        'from r1.c3 import e1_offline_network as N\n'
        'N.install()\n'
        'local = N.in_process_probe()\n'
        'child = N.child_probe()\n'
        'print("RESULT " + json.dumps({"local": local, "child": child}))\n')
    completed = subprocess.run([sys.executable, '-B', str(script)], capture_output=True, text=True, timeout=120,
                               cwd=str(__import__('pathlib').Path(__file__).resolve().parents[2]))
    assert completed.returncode == 0, completed.stderr
    line = [line for line in completed.stdout.splitlines() if line.startswith('RESULT ')][-1]
    result = json.loads(line[len('RESULT '):])
    for report in (result['local'], result['child']):
        assert report['denied'] is True and report['seccomp_mode'] == 2
        for name in ('af_inet', 'af_inet6', 'connect'):
            assert report[name]['errno'] == 101
