"""End-to-end M3 supervisor runs on the local Linux kernel (opt-in).

Requires ``AR_M3_KERNEL_TESTS=1``, ``AR_M3_DELEGATED_CGROUP`` (a writable
cgroup-v2 directory owned by the caller), Linux x86-64, user namespaces,
seccomp user notification, clone3 with CLONE_INTO_CGROUP and ``gcc -static``.
The workload is a tiny static C program compiled into the pytest temp dir; it
never touches the network (the prohibited call is ``socket(AF_UNIX)``, which
the filter suspends before the kernel runs it). This is a local synthetic run,
not the target-host qualification.
"""
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

import pytest

from r1.c3 import offline_supervisor as sup

DELEGATED = os.environ.get('AR_M3_DELEGATED_CGROUP')
pytestmark = pytest.mark.skipif(
    os.environ.get('AR_M3_KERNEL_TESTS') != '1' or not DELEGATED
    or platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64')
    or shutil.which('gcc') is None,
    reason='set AR_M3_KERNEL_TESTS=1 and AR_M3_DELEGATED_CGROUP on Linux x86-64 with gcc')

WORKLOAD_C = r'''
#include <signal.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
static void h(int s){(void)s;}
int main(int argc,char**argv){
  const char*m=argc>1?argv[1]:"clean";
  if(!strcmp(m,"exit3"))return 3;
  if(!strcmp(m,"direct")){socket(AF_UNIX,SOCK_STREAM,0);return 0;}
  if(!strcmp(m,"withdraw")){
    /* handler without SA_RESTART; every suspended socket() returns EINTR and
       the error is swallowed */
    struct sigaction sa;memset(&sa,0,sizeof sa);sa.sa_handler=h;sigaction(SIGALRM,&sa,0);
    struct itimerval t={{0,1000},{0,1000}};setitimer(ITIMER_REAL,&t,0);
    for(int i=0;i<200;i++)socket(AF_UNIX,SOCK_STREAM,0);
    struct itimerval z={{0,0},{0,0}};setitimer(ITIMER_REAL,&z,0);return 0;}
  return 0;}
'''


@pytest.fixture(scope='module')
def workload(tmp_path_factory):
    d = tmp_path_factory.mktemp('m3w')
    (d / 'w.c').write_text(WORKLOAD_C)
    subprocess.run(['gcc', '-static', '-O1', '-o', str(d / 'w'), str(d / 'w.c')], check=True)
    return d / 'w'


def run(workload, mode, tmp_path):
    sha = hashlib.sha256(workload.read_bytes()).hexdigest()
    spec = {'root': '/unused', 'tmpfs_bytes': 1 << 20,
            'closure': [{'source': str(workload), 'target': '/runtime/w', 'sha256': sha}],
            'work_files': [], 'argv': ['/runtime/w', mode],
            'env': {'HOME': '/work', 'TMPDIR': '/work', 'PYTHONDONTWRITEBYTECODE': '1'}}
    protected = tmp_path / 'protected'
    protected.mkdir(exist_ok=True)
    out = tmp_path / f'out-{mode}'
    return out, lambda: sup.supervise(spec, DELEGATED, out, protected_roots=[str(protected)],
                                      timeout_seconds=30)


def audit(out):
    return (out / 'supervisor.jsonl').read_text()


def test_clean_workload_completes_with_clean_drain_and_no_parent_atfork(workload, tmp_path):
    hooks = []
    os.register_at_fork(after_in_parent=lambda: hooks.append('after_in_parent'),
                        before=lambda: hooks.append('before'))
    out, go = run(workload, 'clean', tmp_path)
    result = go()
    assert result['status'] == 'COMPLETE_UNQUALIFIED' and result['withdrawn_drain'] == 'clean'
    text = audit(out)
    assert '"creation": "clone3_pidfd_into_cgroup"' in text
    assert '"withdrawn": 0' in text and 'process_tree_exited' in text
    # The supervisor never calls os.fork, so no parent at-fork callback ran.
    assert hooks == []


def test_received_prohibited_call_stops(workload, tmp_path):
    out, go = run(workload, 'direct', tmp_path)
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall 41'):
        go()
    assert '"event": "prohibited_syscall"' in audit(out)


def test_nonzero_workload_stops_after_clean_drain(workload, tmp_path):
    out, go = run(workload, 'exit3', tmp_path)
    with pytest.raises(sup.SupervisorStop, match='workload failed'):
        go()
    assert '"workload_status": 3' in audit(out)


def test_swallowed_interruptions_stop_whichever_route(workload, tmp_path):
    out, go = run(workload, 'withdraw', tmp_path)
    with pytest.raises(sup.SupervisorStop, match='prohibited syscall'):
        go()


def test_withdrawn_before_receipt_is_found_by_drain(workload, tmp_path, monkeypatch):
    """Descheduled supervisor: the first poll starts late, after every
    suspended call was already interrupted and withdrawn. The old monitor saw
    nothing here; the drain must find the residue and STOP."""
    real_poll = sup.select.poll
    first = []

    class SlowFirstPoll:
        # Only the monitor's poller (listener, pidfd, channel) is slowed; the
        # launcher's zero-timeout membership polls pass through unchanged.
        def __init__(self):
            self.p = real_poll()
            self.n = 0

        def register(self, *a):
            self.n += 1
            self.p.register(*a)

        def unregister(self, *a):
            self.p.unregister(*a)

        def poll(self, *a):
            if self.n == 3 and not first:
                first.append(1)
                time.sleep(2)
            return self.p.poll(*a)
    monkeypatch.setattr(sup.select, 'poll', SlowFirstPoll)
    out, go = run(workload, 'withdraw', tmp_path)
    with pytest.raises(sup.SupervisorStop, match='withdrawn before receipt'):
        go()
    text = audit(out)
    assert '"event": "withdrawn_drain"' in text
    assert '"event": "prohibited_syscall"' not in text
    assert first == [1]
