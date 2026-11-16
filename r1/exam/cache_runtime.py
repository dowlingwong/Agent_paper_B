"""Fail-closed Stage A D3 server identity and lease inheritance scaffolding.

This module is evidence plumbing, not execution authority.  Freshness and
exclusivity cannot be derived from a PID, timestamps or a /proc snapshot;
production dispatch remains blocked until those conditions and the deployed
binary's field contract are independently established.

The child->guardian edge is *not* kcmp-proved.  It is authorised by the
guardian's /proc PID + start-tick + state witness, the exact FD dev/ino/uid
identity and a flock re-lock / independent-contender test with the explicit
method string ``flock_relock_while_guardian_live``.  The ancestor->descendant
directions are kcmp-proved: the guardian kcmp-checks the runner, and the
runner/qualification worker kcmp-checks the native server.  On the portal
(Yama ptrace_scope=1, kernel 6.8.0-136) a descendant->ancestor kcmp READ was
observed to succeed while PTRACE_ATTACH was EPERM; that permission is
host/kernel dependent, so no edge relies on it and an error is never SAME.
"""
from pathlib import Path
import os
import contextvars
import stat
import time
from r1.exam.guards import digest_file
from r1.exam.cache_proc import process_start_ticks, sample_llama_server_processes
from r1.exam.cooperative_lease import (
    LeaseStop, GUARDIAN_WITNESS_METHOD, FLOCK_INHERITANCE_METHOD, KCMP_NOT_USED_NOTE,
    kcmp_file_result, kcmp_same_ofd,
)

COOPERATIVE_POLICY = 'author_same_uid_cooperative_20261031'
GPU_LEASE_PATH = '/home/dowling/r1_locks/gpu0.lock'
LEASE_INHERITANCE_VERSION = 'trackx_lease_inheritance/v1'
LEASE_INHERITANCE_METHOD = 'proc_fd_dev_ino_and_kcmp_file_ancestor_to_descendant'
WORKER_RECHECK_METHOD = 'worker_proc_fd_recheck_no_upward_kcmp'
YAMA_NOTE = ('kcmp is used only ancestor->descendant (guardian->runner, runner->native '
             'server); an error/EPERM is never SAME. Descendant->ancestor kcmp READ '
             'permission is host/kernel dependent (observed permitted on TASL-2 while '
             'PTRACE_ATTACH was EPERM) and is not used here.')
LEASE_ENV_KEYS = ('TRACKX_GPU_LEASE_FD', 'TRACKX_GPU_LEASE_DEV', 'TRACKX_GPU_LEASE_INO', 'TRACKX_GPU_LEASE_UID')
GUARDIAN_ENV_KEYS = ('TRACKX_GPU_GUARDIAN_PID', 'TRACKX_GPU_GUARDIAN_START_TICKS')
LEASE_INHERITANCE_KEYS = frozenset({'version', 'method', 'runner_pid', 'runner_start_ticks',
                                    'server_pid', 'server_start_ticks', 'server_ppid', 'lease_fd',
                                    'dev', 'ino', 'uid', 'server_fd_dev', 'server_fd_ino',
                                    'server_lease_fds', 'fd_set_exact', 'kcmp_pid_a', 'kcmp_pid_b',
                                    'kcmp_fd_a', 'kcmp_fd_b', 'kcmp_rc', 'kcmp_same_ofd',
                                    'kcmp_errors_never_same', 'yama_direction', 'monotonic_ns',
                                    'cold_verified', 'scope'})
_authorized = contextvars.ContextVar('stagea_cooperative_authorized', default=False)
_authorized_lease_path = contextvars.ContextVar('stagea_cooperative_lease_path', default=GPU_LEASE_PATH)


def _read_proc_state(pid, proc_root='/proc'):
    try:
        status = Path(proc_root, str(pid), 'status').read_text()
    except OSError as exc:
        raise RuntimeError('STOP: guardian state unobservable') from exc
    for line in status.splitlines():
        if line.startswith('State:'):
            fields = line.split()
            if len(fields) < 2 or not fields[1]:
                break
            return fields[1]
    raise RuntimeError('STOP: guardian state unreadable')


def _proc_stat_fields(pid, proc_root='/proc'):
    if type(pid) is not int or pid <= 0:
        raise RuntimeError('STOP: invalid pid')
    try:
        raw = (Path(proc_root) / str(pid) / 'stat').read_text()
    except OSError as exc:
        raise RuntimeError('STOP: process identity unobservable') from exc
    close = raw.rfind(')')
    if close < 0:
        raise RuntimeError('STOP: process stat unparseable')
    fields = raw[close + 2:].split()
    if len(fields) < 20:
        raise RuntimeError('STOP: process stat truncated')
    return fields


def _proc_ppid(pid, proc_root='/proc'):
    return int(_proc_stat_fields(pid, proc_root)[1])


def guardian_witness(*, start_ticks=process_start_ticks, proc_root='/proc'):
    """Observe the guardian's PID/start-tick/state and its lease FD identity.

    Returns the ``proc_pid_start_state_fd_identity`` evidence record consumed by
    ``assert_held_and_bound``.  NO kcmp is attempted on this edge: it would run
    child->parent, whose READ permission is host/kernel dependent, so it is not
    relied on and an error would never count as SAME.  Any missing or ambiguous
    observation is a RuntimeError STOP, never a False pass.
    """
    raw = os.environ.get('TRACKX_GPU_GUARDIAN_PID', '')
    start = os.environ.get('TRACKX_GPU_GUARDIAN_START_TICKS', '')
    rawfd = os.environ.get('TRACKX_GPU_LEASE_FD', '')
    if not raw.isdecimal() or not start.isdecimal() or not rawfd.isdecimal():
        raise RuntimeError('STOP: guardian identity missing')
    pid, ticks, fd = int(raw), int(start), int(rawfd)
    if pid <= 0 or ticks <= 0 or fd < 3:
        raise RuntimeError('STOP: guardian identity invalid')
    if pid == os.getpid():
        raise RuntimeError('STOP: guardian witness points at this process')
    # The /proc stat read IS the existence check; no signal is sent here.
    try:
        observed = start_ticks(pid)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError('STOP: guardian start ticks unobservable') from exc
    if observed != ticks:
        raise RuntimeError('STOP: guardian start ticks changed')
    state = _read_proc_state(pid, proc_root)
    if state in ('Z', 'X'):
        raise RuntimeError('STOP: guardian is not live')
    try:
        current = os.fstat(fd)
        link = os.stat(os.path.join(proc_root, str(pid), 'fd', str(fd)))
    except OSError as exc:
        raise RuntimeError('STOP: guardian lease descriptor unobservable') from exc
    if (link.st_dev, link.st_ino) != (current.st_dev, current.st_ino):
        raise RuntimeError('STOP: guardian lease descriptor identity changed')
    if link.st_uid != current.st_uid:
        raise RuntimeError('STOP: guardian lease descriptor owner changed')
    return {'pid': pid, 'start_ticks': ticks, 'fd': fd, 'dev': current.st_dev,
            'ino': current.st_ino, 'uid': current.st_uid, 'state': state,
            'method': GUARDIAN_WITNESS_METHOD}


def _lease_env_identity():
    fields = [os.environ.get(key, '') for key in LEASE_ENV_KEYS]
    if any(not value.isdecimal() for value in fields):
        raise RuntimeError('STOP: inherited GPU lease FD/identity absent')
    fd, dev, ino, uid = map(int, fields)
    if fd < 3:
        raise RuntimeError('STOP: invalid inherited GPU lease FD')
    return fd, dev, ino, uid


def authorize_cooperative_stagea(cfg, *, lease_path=GPU_LEASE_PATH, witness=guardian_witness):
    """Authorize this process only after explicit policy and live lease checks.

    The author's same-UID cooperation is an assumption, not evidence of
    exclusive access.  The FD itself must be inherited from a reviewed guardian;
    a marker, an inode alone or an independently reopened path is insufficient.
    """
    from r1.exam.cooperative_lease import assert_held_and_bound
    if cfg.get('cache_prompt') is not False or cfg.get('d3_policy') != COOPERATIVE_POLICY:
        raise RuntimeError('STOP: cooperative D3 policy/cache setting not explicit')
    fd, dev, ino, uid = _lease_env_identity()
    try:
        st = os.fstat(fd)
        identity = (st.st_dev, st.st_ino)
        if (st.st_dev, st.st_ino, st.st_uid) != (dev, ino, uid):
            raise RuntimeError('STOP: inherited GPU lease identity mismatch')
        proof = assert_held_and_bound(fd, lease_path, identity, guardian_check=witness)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError('STOP: inherited GPU lease not established') from exc
    _authorized.set(True)
    _authorized_lease_path.set(str(lease_path))
    return {'policy': COOPERATIVE_POLICY, 'same_uid_external_noninterference': 'author assumption, not observed proof',
            'host_global_single_server': 'NOT_CHECKABLE', 'lease': proof, 'lease_fd': fd,
            'authorization_methods': [GUARDIAN_WITNESS_METHOD, FLOCK_INHERITANCE_METHOD],
            'kcmp_used_for_guardian_edge': False, 'kcmp_not_used_reason': KCMP_NOT_USED_NOTE}


def require_authorized_stagea():
    if not _authorized.get():
        raise RuntimeError('STOP: D3 cold-cache cooperative Stage A context not authorized')


def verified_lease_fd(*, witness=guardian_witness):
    """Verify local FD identity and independent contention before every child spawn."""
    require_authorized_stagea()
    reject_unverified_lease(witness=witness)
    fd, dev, ino, uid = _lease_env_identity()
    try:
        st = os.fstat(fd)
    except OSError as exc:
        raise RuntimeError('STOP: inherited GPU lease FD unobservable') from exc
    if (st.st_dev, st.st_ino, st.st_uid) != (dev, ino, uid):
        raise RuntimeError('STOP: inherited GPU lease FD identity changed')
    return fd


def reject_unverified_lease(*, witness=guardian_witness):
    """Recheck inherited FD and contention; a marker is never sufficient."""
    require_authorized_stagea()
    from r1.exam.cooperative_lease import assert_held_and_bound
    fd, dev, ino, uid = _lease_env_identity()
    try:
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino, st.st_uid) != (dev, ino, uid):
            raise RuntimeError('STOP: inherited GPU lease identity mismatch')
        return assert_held_and_bound(fd, _authorized_lease_path.get(), (st.st_dev, st.st_ino),
                                     guardian_check=witness)
    except (OSError, RuntimeError) as exc:
        raise RuntimeError('STOP: GPU lease verification failed') from exc


def _kcmp_match(kcmp, pid_a, pid_b, fd):
    result = kcmp(pid_a, pid_b, fd, fd)
    if isinstance(result, tuple) and len(result) == 2:
        rc, err = result
        return (rc if type(rc) is int else None, err if type(err) is int else None)
    if result is True:
        return 0, 0
    return None, None


def _observe_ticks(pid, *, start_ticks, proc_root):
    if start_ticks is process_start_ticks:
        return process_start_ticks(pid, proc_root=proc_root)
    return start_ticks(pid)


def validate_lease_inheritance_record(record):
    """Validate the exact ancestor->descendant lease_inheritance evidence row."""
    if not isinstance(record, dict) or set(record) != LEASE_INHERITANCE_KEYS:
        raise LeaseStop('STOP: lease inheritance evidence schema invalid')
    if record['version'] != LEASE_INHERITANCE_VERSION or record['method'] != LEASE_INHERITANCE_METHOD:
        raise LeaseStop('STOP: lease inheritance evidence version/method invalid')
    ints = ('runner_pid', 'runner_start_ticks', 'server_pid', 'server_start_ticks', 'server_ppid',
            'lease_fd', 'dev', 'ino', 'uid', 'server_fd_dev', 'server_fd_ino',
            'kcmp_pid_a', 'kcmp_pid_b', 'kcmp_fd_a', 'kcmp_fd_b', 'monotonic_ns')
    if any(type(record[key]) is not int for key in ints):
        raise LeaseStop('STOP: lease inheritance evidence types invalid')
    if record['runner_pid'] <= 0 or record['runner_start_ticks'] <= 0 or record['server_pid'] <= 0:
        raise LeaseStop('STOP: lease inheritance process identities invalid')
    if record['server_start_ticks'] <= 0 or record['server_ppid'] <= 0 or record['lease_fd'] < 3:
        raise LeaseStop('STOP: lease inheritance server identity invalid')
    if record['kcmp_rc'] != 0 or record['kcmp_same_ofd'] is not True or record['kcmp_errors_never_same'] is not True:
        raise LeaseStop('STOP: lease inheritance kcmp result is not SAME')
    if record['kcmp_pid_a'] != record['runner_pid'] or record['kcmp_pid_b'] != record['server_pid'] or \
       record['kcmp_fd_a'] != record['lease_fd'] or record['kcmp_fd_b'] != record['lease_fd']:
        raise LeaseStop('STOP: lease inheritance kcmp direction/descriptors invalid')
    if record['server_ppid'] != record['runner_pid']:
        raise LeaseStop('STOP: lease inheritance parent pid mismatch')
    if (record['server_fd_dev'], record['server_fd_ino']) != (record['dev'], record['ino']):
        raise LeaseStop('STOP: lease inheritance FD identity mismatch')
    if record['fd_set_exact'] is not True or record['server_lease_fds'] != [record['lease_fd']]:
        raise LeaseStop('STOP: lease inheritance FD set invalid')
    if record['cold_verified'] is not False:
        raise LeaseStop('STOP: lease inheritance must not claim coldness')
    if not isinstance(record['yama_direction'], str) or not record['yama_direction']:
        raise LeaseStop('STOP: lease inheritance direction note missing')
    if record['monotonic_ns'] <= 0:
        raise LeaseStop('STOP: lease inheritance timestamp invalid')
    return record


def verify_server_lease_inheritance(server_pid, lease_fd, *, runner_pid=None, started_ticks=None,
                                    proc_root='/proc', start_ticks=process_start_ticks,
                                    kcmp=kcmp_file_result, monotonic_ns=None):
    """Prove the native server holds the SAME lease open file description.

    Legal direction only: ``kcmp(runner_pid, server_pid, fd, fd)`` from the
    runner/worker (the ancestor).  A nonzero rc, EPERM or any unobservable
    condition is a LeaseStop.  The server must hold exactly the inherited FD
    number, and its pid/start ticks/parent pid must match the started process.
    """
    require_authorized_stagea()
    if type(lease_fd) is not int or lease_fd < 3:
        raise LeaseStop('STOP: invalid lease FD for inheritance proof')
    if runner_pid is None:
        runner_pid = os.getpid()
    if type(runner_pid) is not int or runner_pid <= 0 or type(server_pid) is not int or server_pid <= 0:
        raise LeaseStop('STOP: invalid pid for inheritance proof')
    if runner_pid == server_pid:
        raise LeaseStop('STOP: server must be a distinct descendant process')
    try:
        current = os.fstat(lease_fd)
    except OSError as exc:
        raise LeaseStop('STOP: runner lease FD unobservable') from exc
    identity = (current.st_dev, current.st_ino)
    if current.st_nlink != 1:
        raise LeaseStop('STOP: lease FD link count changed')
    try:
        runner_ticks = _observe_ticks(runner_pid, start_ticks=start_ticks, proc_root=proc_root)
        server_ticks = _observe_ticks(server_pid, start_ticks=start_ticks, proc_root=proc_root)
        ppid = _proc_ppid(server_pid, proc_root)
    except RuntimeError as exc:
        raise LeaseStop('STOP: server process identity unavailable') from exc
    if server_ticks <= 0:
        raise LeaseStop('STOP: server start ticks invalid')
    if started_ticks is not None and started_ticks != server_ticks:
        raise LeaseStop('STOP: served process start ticks differ from the started process')
    if ppid != runner_pid:
        raise LeaseStop('STOP: server parent pid differs from the ancestor process')
    try:
        observed = os.stat(os.path.join(proc_root, str(server_pid), 'fd', str(lease_fd)))
    except OSError as exc:
        raise LeaseStop('STOP: server does not retain the inherited lease descriptor') from exc
    if (observed.st_dev, observed.st_ino) != identity:
        raise LeaseStop('STOP: server lease descriptor identity differs')
    try:
        names = os.listdir(os.path.join(proc_root, str(server_pid), 'fd'))
    except OSError as exc:
        raise LeaseStop('STOP: server fd table unobservable') from exc
    matched = []
    for name in names:
        if not name.isdecimal():
            continue
        try:
            st = os.stat(os.path.join(proc_root, str(server_pid), 'fd', name))
        except OSError:
            continue  # fd closed while sampling; not evidence of the inherited FD
        if (st.st_dev, st.st_ino) == identity:
            matched.append(int(name))
    matched.sort()
    if matched != [lease_fd]:
        raise LeaseStop(f'STOP: server lease FD set differs from the inherited number: {matched}')
    rc, err = _kcmp_match(kcmp, runner_pid, server_pid, lease_fd)
    if rc != 0:
        raise LeaseStop(f'STOP: kcmp ancestor->descendant did not prove the same OFD (rc={rc} errno={err})')
    record = {'version': LEASE_INHERITANCE_VERSION, 'method': LEASE_INHERITANCE_METHOD,
              'runner_pid': runner_pid, 'runner_start_ticks': runner_ticks,
              'server_pid': server_pid, 'server_start_ticks': server_ticks, 'server_ppid': ppid,
              'lease_fd': lease_fd, 'dev': current.st_dev, 'ino': current.st_ino, 'uid': current.st_uid,
              'server_fd_dev': observed.st_dev, 'server_fd_ino': observed.st_ino,
              'server_lease_fds': [lease_fd], 'fd_set_exact': True,
              'kcmp_pid_a': runner_pid, 'kcmp_pid_b': server_pid,
              'kcmp_fd_a': lease_fd, 'kcmp_fd_b': lease_fd,
              'kcmp_rc': rc, 'kcmp_same_ofd': True, 'kcmp_errors_never_same': True,
              'yama_direction': f'kcmp(ancestor {runner_pid} -> descendant {server_pid}); {YAMA_NOTE}',
              'monotonic_ns': int(monotonic_ns if monotonic_ns is not None else time.monotonic_ns()),
              'cold_verified': False,
              'scope': ('same-UID cooperative assumption; OFD identity proved only for this '
                        'ancestor->descendant edge at this sample; cache coldness, same-UID '
                        'noninterference and host-global single-server NOT_CHECKABLE')}
    return validate_lease_inheritance_record(record)


def require_worker_lease_inheritance(identity, *, start_ticks=process_start_ticks, proc_root='/proc',
                                     environ=None):
    """Worker-side recheck of the runner-recorded native-server inheritance row.

    The worker may NOT kcmp upward, so it re-derives the observable facts:
    server pid/start-tick liveness, /proc FD dev/ino, the exact FD set, and its
    own inherited FD identity.  The recorded kcmp rc must be 0 and is reported
    as the runner-side (ancestor->descendant) proof, not re-performed here.
    """
    require_authorized_stagea()
    environ = os.environ if environ is None else environ
    record = identity.get('lease_inheritance') if isinstance(identity, dict) else None
    validate_lease_inheritance_record(record)
    if type(identity.get('pid')) is not int or identity['pid'] != record['server_pid']:
        raise LeaseStop('STOP: worker identity does not bind the recorded server')
    if type(identity.get('process_start_ticks')) is not int or \
       identity['process_start_ticks'] != record['server_start_ticks']:
        raise LeaseStop('STOP: worker identity start ticks differ from the inheritance evidence')
    try:
        observed = _observe_ticks(record['server_pid'], start_ticks=start_ticks, proc_root=proc_root)
        ppid = _proc_ppid(record['server_pid'], proc_root)
        link = os.stat(os.path.join(proc_root, str(record['server_pid']), 'fd', str(record['lease_fd'])))
    except (OSError, RuntimeError) as exc:
        raise LeaseStop('STOP: worker cannot re-observe the recorded server') from exc
    if observed != record['server_start_ticks']:
        raise LeaseStop('STOP: recorded server start ticks changed')
    if ppid != record['server_ppid']:
        raise LeaseStop('STOP: recorded server parent pid changed')
    if (link.st_dev, link.st_ino) != (record['dev'], record['ino']):
        raise LeaseStop('STOP: recorded server lease descriptor identity changed')
    raw = environ.get('TRACKX_GPU_LEASE_FD', '')
    if not raw.isdecimal():
        raise LeaseStop('STOP: worker inherited GPU lease FD absent')
    fd = int(raw)
    if fd != record['lease_fd']:
        raise LeaseStop('STOP: worker inherited FD number differs from the recorded server FD')
    try:
        own = os.fstat(fd)
    except OSError as exc:
        raise LeaseStop('STOP: worker inherited lease FD unobservable') from exc
    if (own.st_dev, own.st_ino, own.st_uid) != (record['dev'], record['ino'], record['uid']):
        raise LeaseStop('STOP: worker inherited lease FD identity differs')
    return {'method': WORKER_RECHECK_METHOD, 'kcmp_used_upward': False,
            'kcmp_not_used_reason': YAMA_NOTE,
            'runner_side_record': {'version': record['version'], 'kcmp_rc': record['kcmp_rc'],
                                   'kcmp_same_ofd': record['kcmp_same_ofd'],
                                   'runner_pid': record['runner_pid'],
                                   'server_pid': record['server_pid'],
                                   'server_start_ticks': record['server_start_ticks']},
            'lease_fd': fd, 'dev': own.st_dev, 'ino': own.st_ino, 'uid': own.st_uid,
            'server_ppid': ppid, 'monotonic_ns': time.monotonic_ns(),
            'scope': ('observed /proc facts only; the ancestor->descendant kcmp was performed '
                      'by the runner, not by this worker; no upward kcmp is possible under Yama')}


def capture_parent_identity(instance, *, binary_sha256, model_sha256,
                            start_ticks=process_start_ticks, census=sample_llama_server_processes):
    """Capture only observable facts. A snapshot cannot certify a cold server."""
    record = instance.record
    process = instance.process
    pid = record.get('pid') if isinstance(record, dict) else None
    if (type(pid) is not int or pid <= 0 or process is None or process.pid != pid or
        process.poll() is not None or record.get('port') != instance.port or
        record.get('alias') != instance.alias or record.get('model_sha256') != model_sha256):
        raise RuntimeError('STOP: parent server process or pin binding missing')
    binary = Path(instance.binary).resolve(strict=True)
    model = Path(instance.model_path).resolve(strict=True)
    if digest_file(binary) != binary_sha256 or digest_file(model) != model_sha256:
        raise RuntimeError('STOP: parent binary or GGUF hash mismatch')
    identity = {'pid': pid, 'process_start_ticks': start_ticks(pid), 'port': instance.port,
                'alias': instance.alias, 'binary': str(binary), 'binary_sha256': binary_sha256,
                'model_path': str(model), 'model_sha256': model_sha256,
                'fresh': True, 'cold_verified': False,
                'scope': 'new owned process; same-UID noninterference is an author assumption; cache coldness must be checked by the first true response; host-global state NOT_CHECKABLE'}
    inheritance = record.get('lease_inheritance') if isinstance(record, dict) else None
    if os.environ.get('TRACKX_GPU_LEASE_FD'):
        # A cooperative Stage A server must have proved FD inheritance before
        # this identity can be handed to any worker.
        try:
            validate_lease_inheritance_record(inheritance)
        except LeaseStop as exc:
            raise RuntimeError(f'STOP: cooperative server lacks verified lease inheritance: {exc}') from exc
        if inheritance.get('server_pid') != pid:
            raise RuntimeError('STOP: lease inheritance server pid mismatch')
        identity['lease_inheritance'] = inheritance
    elif inheritance is not None:
        validate_lease_inheritance_record(inheritance)
        identity['lease_inheritance'] = inheritance
    sample = census(identity)
    if (not isinstance(sample, dict) or not isinstance(sample.get('method'), str) or not sample['method'] or
        not isinstance(sample.get('scope'), str) or not sample['scope'] or
        type(sample.get('count')) is not int or sample['count'] != 1 or
        type(sample.get('pid')) is not int or sample['pid'] != pid or
        type(sample.get('process_start_ticks')) is not int or sample['process_start_ticks'] != identity['process_start_ticks']):
        raise RuntimeError('STOP: parent server census/identity mismatch')
    identity['census_initial'] = sample
    return identity


def reject_unverified_cold(identity):
    """Require an owned fresh process; the first true response validates cache.

    Under the explicit author decision, another same-UID caller is assumed not
    to interfere. Neither this check nor a snapshot proves global exclusivity.
    """
    require_authorized_stagea()
    if (not isinstance(identity, dict) or identity.get('fresh') is not True or
        identity.get('cold_verified') is not False or
        'author assumption' not in str(identity.get('scope', ''))):
        raise RuntimeError('STOP: cooperative fresh server binding missing')


def validate_worker_binding(identity, job, *, start_ticks=process_start_ticks,
                            census=sample_llama_server_processes, proc_root='/proc'):
    """Check identity continuity at worker entry; this is not cold proof."""
    try:
        cfg = job['config']
        spec = job['candidate']
        if (identity['port'] != job['port'] or identity['alias'] != spec['id'] or
            identity['binary_sha256'] != cfg['server']['binary_sha256'] or
            identity['model_sha256'] != spec['quant_source']['sha256'] or
            identity['model_path'] != str(Path(spec['runtime']['model_path']).resolve(strict=True)) or
            identity['binary'] != str(Path(cfg['server']['binary']).resolve(strict=True)) or
            start_ticks(identity['pid']) != identity['process_start_ticks']):
            raise RuntimeError('STOP: worker identity binding changed')
        sample = census(identity)
        if (not isinstance(sample, dict) or not isinstance(sample.get('method'), str) or not sample['method'] or
            not isinstance(sample.get('scope'), str) or not sample['scope'] or
            type(sample.get('count')) is not int or sample['count'] != 1 or
            type(sample.get('pid')) is not int or sample['pid'] != identity['pid'] or
            type(sample.get('process_start_ticks')) is not int or sample['process_start_ticks'] != identity['process_start_ticks']):
            raise RuntimeError('STOP: worker server census changed')
    except (KeyError, TypeError, OSError) as exc:
        raise RuntimeError('STOP: worker identity binding unavailable') from exc
    recheck = require_worker_lease_inheritance(identity, start_ticks=start_ticks, proc_root=proc_root)
    result = dict(sample)
    result['lease_inheritance_check'] = recheck
    return result
