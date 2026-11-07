"""Cooperative kernel-backed parent/worker handoff for production B1.

The parent must hold the reviewed lease and enroll the child before exec.
This is not an adversarial same-UID boundary; production needs Linux /proc,
pidfd, kcmp and cgroup-v2 visibility, independently qualified on the host.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import select
import stat
import sys
from pathlib import Path
from urllib.parse import urlsplit

ENV_KEY = 'R1_B1_WORKER_CONTRACT'


class WorkerContractStop(RuntimeError):
    pass


def _stop(reason):
    raise WorkerContractStop('STOP: B1 worker contract ' + reason)


def _job_sha(job):
    return hashlib.sha256(json.dumps(job, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _pidfd_alive(fd, expected):
    try:
        lines = (Path('/proc/self/fdinfo') / str(fd)).read_text().splitlines()
        pids = [line.split(':', 1)[1].strip() for line in lines if line.startswith('Pid:')]
        poll = select.poll()
        poll.register(fd, select.POLLIN | select.POLLHUP | select.POLLERR)
        return pids == [str(expected)] and not poll.poll(0)
    except (OSError, ValueError):
        return False


def _membership(pid):
    rows = (Path('/proc') / str(pid) / 'cgroup').read_text().splitlines()
    values = [row[3:] for row in rows if row.startswith('0::')]
    if len(values) != 1 or not values[0].startswith('/') or '..' in Path(values[0]).parts:
        _stop('cgroup membership unavailable')
    return values[0]


def _same_dir(fd, path):
    a, b = os.fstat(fd), os.stat(path, follow_symlinks=False)
    return stat.S_ISDIR(a.st_mode) and stat.S_ISDIR(b.st_mode) and (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)



def _parent_runner(pid, supervisor_pid, job):
    """Bind the live parent to the reviewed runner invocation and batch path."""
    repo = Path(__file__).resolve().parents[2]
    raw = (Path('/proc') / str(pid) / 'cmdline').read_bytes().split(b'\0')
    if raw and raw[-1] == b'':
        raw.pop()
    try:
        argv = [os.fsdecode(item) for item in raw]
    except UnicodeError:
        return False
    if (len(argv) != 8 or argv[1:5] != ['-B', str(repo/'r1/scripts/exam_runner.py'), 'b1', '--config']
            or argv[6] != '--out' or Path(argv[5]).absolute() != repo/'r1/scripts/configs/exam_b1_v2.json'):
        return False
    parent_exe, ours = os.stat(f'/proc/{pid}/exe'), os.stat(sys.executable)
    if (parent_exe.st_dev,parent_exe.st_ino) != (ours.st_dev,ours.st_ino):
        return False
    if Path(os.readlink(f'/proc/{pid}/cwd')) != repo:
        return False
    raw_stat = (Path('/proc') / str(pid) / 'stat').read_text()
    after = raw_stat[raw_stat.rindex(')')+2:].split()
    if len(after) < 2 or int(after[1]) != supervisor_pid:
        return False
    batch = Path(argv[7])
    candidate, mode, node, seed = job['candidate']['id'], job['mode'], job['node'], job['seed']
    if (not batch.is_absolute() or batch.resolve() != batch or
            not isinstance(candidate,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',candidate) or
            not isinstance(node,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',node) or
            mode not in ('off','on') or type(seed) is not int):
        return False
    return Path(job['out']) == batch / candidate / 'b1' / mode / f'{node}__s{seed}'


def _fd_quiet(fd):
    poll = select.poll()
    poll.register(fd, select.POLLIN | select.POLLHUP | select.POLLERR)
    return not poll.poll(0)

def _server_listener(pid, url):
    """Verify an unambiguous IPv4 loopback listener is held by this PID."""
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError:
        return False
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not port or
            parsed.netloc != f'127.0.0.1:{port}' or parsed.path != '/v1' or
            parsed.query or parsed.fragment or parsed.username is not None):
        return False
    me, server = os.stat('/proc/self/ns/net'), os.stat(f'/proc/{pid}/ns/net')
    if (me.st_dev, me.st_ino) != (server.st_dev, server.st_ino):
        return False
    text = Path(f'/proc/{pid}/net/tcp').read_text()
    matches = []
    for line in text.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 10:
            _stop('server TCP table malformed')
        if cols[1].upper() == f'0100007F:{port:04X}' and cols[3] == '0A':
            matches.append(cols[9])
    if len(matches) != 1 or not matches[0].isdigit():
        return False
    target = f'socket:[{matches[0]}]'
    held = 0
    for entry in Path(f'/proc/{pid}/fd').iterdir():
        try:
            held += os.readlink(entry) == target
        except FileNotFoundError:
            # A changing FD set cannot establish the identity.
            return False
    return held > 0


def verify_worker_contract(job, environ=None):
    """Fail before campaign output unless the parent-bound descriptors match."""
    env = os.environ if environ is None else environ
    try:
        ctx = json.loads(env[ENV_KEY])
        required = {'version','parent_pid','parent_ticks','parent_pidfd',
                    'supervisor_pid','supervisor_ticks','supervisor_pidfd','supervisor_live_fd',
                    'guardian_pid','guardian_ticks','guardian_pidfd','lease_fd',
                    'root_fd','leaf_fd','output_fd','membership','leaf','out','job_sha256','audit_stop_fd','audit_backup_fd',
                    'server_pid','server_ticks','server_pidfd','server_leaf_fd','server_url'}
        if not isinstance(ctx, dict) or set(ctx) != required or ctx['version'] != 'b1_worker_contract/v3':
            _stop('invalid schema')
        names = ('parent_pid','parent_ticks','parent_pidfd','supervisor_pid','supervisor_ticks',
                 'supervisor_pidfd','supervisor_live_fd','guardian_pid','guardian_ticks','guardian_pidfd',
                 'lease_fd','root_fd','leaf_fd','output_fd','audit_stop_fd','audit_backup_fd')
        if any(type(ctx[k]) is not int for k in names) or ctx['parent_pid'] <= 0 or ctx['parent_ticks'] <= 0:
            _stop('invalid descriptor or parent identity')
        fds = [ctx[k] for k in ('parent_pidfd','supervisor_pidfd','supervisor_live_fd','guardian_pidfd',
                                 'lease_fd','root_fd','leaf_fd','output_fd','audit_stop_fd','audit_backup_fd')]
        if any(fd < 3 for fd in fds) or len(fds) != len(set(fds)):
            _stop('descriptor collision')
        from r1.exam.b1_audit_stop import require_notify_fds
        require_notify_fds((ctx['audit_stop_fd'],ctx['audit_backup_fd']))
        from r1.exam.cache_proc import process_start_ticks
        from r1.exam.b1_lease import adopt_inherited, verify_server_fd
        if (os.getppid() != ctx['parent_pid'] or process_start_ticks(ctx['parent_pid']) != ctx['parent_ticks']
                or not _pidfd_alive(ctx['parent_pidfd'], ctx['parent_pid'])):
            _stop('parent is absent or changed')
        if (ctx['supervisor_pid'] <= 0 or ctx['guardian_pid'] <= 0 or
                process_start_ticks(ctx['supervisor_pid']) != ctx['supervisor_ticks'] or
                process_start_ticks(ctx['guardian_pid']) != ctx['guardian_ticks'] or
                not _pidfd_alive(ctx['supervisor_pidfd'],ctx['supervisor_pid']) or
                not _pidfd_alive(ctx['guardian_pidfd'],ctx['guardian_pid']) or
                not _fd_quiet(ctx['supervisor_live_fd']) or
                not _parent_runner(ctx['parent_pid'],ctx['supervisor_pid'],job)):
            _stop('supervisor, guardian or runner identity differs')
        adopt_inherited(ctx['lease_fd'], Path.home() / 'r1_locks' / 'gpu0.lock')
        verify_server_fd(ctx['lease_fd'],ctx['guardian_pid'])
        membership, leaf = ctx['membership'], ctx['leaf']
        if (not isinstance(membership, str) or not membership.startswith('/') or
                '..' in Path(membership).parts or not isinstance(leaf, str) or
                not re.fullmatch(r'worker-[0-9a-f]{32}', leaf)):
            _stop('invalid cgroup path')
        root = Path('/sys/fs/cgroup') / membership.lstrip('/')
        if (_membership(os.getpid()) != membership.rstrip('/') + '/' + leaf or
                not _same_dir(ctx['root_fd'], root) or not _same_dir(ctx['leaf_fd'], root / leaf)):
            _stop('owned cgroup membership mismatch')
        out = Path(job['out'])
        if (not out.is_absolute() or out != out.resolve() or str(out) != ctx['out'] or
                not _same_dir(ctx['output_fd'], out)):
            _stop('output directory identity mismatch')
        info = os.fstat(ctx['output_fd'])
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            _stop('output directory ownership mismatch')
        if ctx['job_sha256'] != _job_sha(job):
            _stop('job differs from parent binding')
        server_fields = ('server_pid','server_ticks','server_pidfd','server_leaf_fd','server_url')
        software = job['candidate'].get('kind') in ('random_valid', 'scripted')
        if software:
            if any(ctx[k] is not None for k in server_fields) or job.get('base_url') is not None:
                _stop('software anchor unexpectedly references a server')
        else:
            if (any(type(ctx[k]) is not int or ctx[k] <= 0 for k in server_fields[:4])
                    or ctx['server_pidfd'] < 3 or ctx['server_leaf_fd'] < 3
                    or ctx['server_pidfd'] in fds or ctx['server_leaf_fd'] in fds
                    or ctx['server_pidfd'] == ctx['server_leaf_fd']
                    or not isinstance(ctx['server_url'], str) or job.get('base_url') != ctx['server_url']
                    or env.get('LLAMACPP_BASE_URL') != ctx['server_url']):
                _stop('server binding invalid')
            if (process_start_ticks(ctx['server_pid']) != ctx['server_ticks']
                    or not _pidfd_alive(ctx['server_pidfd'], ctx['server_pid'])):
                _stop('server process absent or changed')
            server_membership = _membership(ctx['server_pid'])
            if (not server_membership.startswith(membership.rstrip('/') + '/server-') or
                    '/' in server_membership[len(membership.rstrip('/') + '/'):]
                    or not _same_dir(ctx['server_leaf_fd'], Path('/sys/fs/cgroup') / server_membership.lstrip('/'))):
                _stop('server cgroup mismatch')
            verify_server_fd(ctx['lease_fd'], ctx['server_pid'])
            if not _server_listener(ctx['server_pid'], ctx['server_url']):
                _stop('server listener identity mismatch')
            if (process_start_ticks(ctx['server_pid']) != ctx['server_ticks'] or
                    not _pidfd_alive(ctx['server_pidfd'],ctx['server_pid'])):
                _stop('server changed during worker check')
        # Recheck process liveness and STOP channel after all filesystem reads.
        if (os.getppid() != ctx['parent_pid'] or
                process_start_ticks(ctx['parent_pid']) != ctx['parent_ticks'] or
                process_start_ticks(ctx['supervisor_pid']) != ctx['supervisor_ticks'] or
                process_start_ticks(ctx['guardian_pid']) != ctx['guardian_ticks'] or
                not _pidfd_alive(ctx['parent_pidfd'],ctx['parent_pid']) or
                not _pidfd_alive(ctx['supervisor_pidfd'],ctx['supervisor_pid']) or
                not _pidfd_alive(ctx['guardian_pidfd'],ctx['guardian_pid']) or
                not _fd_quiet(ctx['supervisor_live_fd'])):
            _stop('parent, guardian or supervisor changed during check')
        return ctx
    except WorkerContractStop:
        raise
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as exc:
        raise WorkerContractStop('STOP: B1 worker contract unavailable') from exc
