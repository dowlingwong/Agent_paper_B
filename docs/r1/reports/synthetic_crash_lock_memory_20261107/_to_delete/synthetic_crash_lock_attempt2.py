"""Test-only explicit retirement of a synthetic, unrecorded-crash lock.

This is not imported by production runner or a recovery authority. The caller
must own the synthetic parent, worker and fake server and must have observed
parent SIGKILL/wait and both children exit. Any ambiguity raises before the
caller can invoke a synthetic restart; no recorded STOP may be resumed.
"""
import json
import os
from pathlib import Path
import signal
import stat
import uuid


def _dir_identity(info, device=None):
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022
            or (device is not None and info.st_dev != device)):
        raise RuntimeError('STOP: unsafe synthetic crash directory')
    return info.st_dev, info.st_ino, info.st_uid


def _read_regular(dirfd, name, opened, device):
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(name, flags, dir_fd=dirfd); opened.append(fd)
    info = os.fstat(fd)
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o022
            or info.st_dev != device or info.st_nlink != 1):
        raise RuntimeError('STOP: unsafe synthetic crash record')
    parts = []; total = 0
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        total += len(chunk)
        if total > 4 * 1024 * 1024:
            raise RuntimeError('STOP: oversized synthetic crash record')
        parts.append(chunk)
    data = b''.join(parts)
    named = os.stat(name, dir_fd=dirfd, follow_symlinks=False)
    identity = (info.st_dev, info.st_ino, info.st_uid, info.st_nlink)
    if (named.st_dev, named.st_ino, named.st_uid, named.st_nlink) != identity or not stat.S_ISREG(named.st_mode):
        raise RuntimeError('STOP: synthetic crash record identity changed')
    return data, identity


def _no_stop_marker(batchfd):
    for name in ('STOP.json', 'B1_COMMIT_UNCERTAIN.json'):
        try:
            os.stat(name, dir_fd=batchfd, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise RuntimeError('STOP: synthetic crash batch has a STOP marker')


def _require_absent_process(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    raise RuntimeError('STOP: synthetic process still alive or ownership ambiguous')


def retire_test_owned_crash_lock(root, batch, partial, server_record, *, parent_pid,
                                 parent_returncode, worker_pid, server_pid):
    """Retain the owned runner lock after a planned synthetic crash, once only.

    The helper refuses non-DRYRUN roots, recorded STOP, live recorded processes,
    path aliases, mismatched lock/state/server records and collisions. It does
    not signal, delete, start, resume or modify any production job. Atomic
    rename and directory durability must be qualified on the test filesystem.
    Same-UID path races and external writers remain cooperative assumptions.
    """
    from r1.exam.b1_state_preserve import _NOREPLACE, _renameat_dryrun
    from r1.exam.runtime import host_check

    root, batch, partial, server_record = map(Path, (root, batch, partial, server_record))
    if (not all(p.is_absolute() and p.resolve(strict=True) == p for p in (root, batch, partial, server_record))
            or batch != root/'b1' or not partial.is_relative_to(batch)
            or server_record.parent != batch/'servers'/'qwen25_coder_7b'):
        raise RuntimeError('STOP: synthetic crash paths do not match test root')
    pids = (parent_pid, worker_pid, server_pid)
    if any(type(pid) is not int or pid <= 1 for pid in pids) or len(set(pids)) != 3:
        raise RuntimeError('STOP: invalid synthetic process identities')
    if parent_returncode != -signal.SIGKILL:
        raise RuntimeError('STOP: synthetic parent was not waited after planned SIGKILL')

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    opened = []; body_failed = False
    try:
        rootfd = os.open(root, flags); opened.append(rootfd)
        device = _dir_identity(os.fstat(rootfd))[0]
        batchfd = os.open('b1', flags, dir_fd=rootfd); opened.append(batchfd)
        _dir_identity(os.fstat(batchfd), device)
        marker, _ = _read_regular(rootfd, '.dryrun', opened, device)
        if marker != b'EXAM DRYRUN; no inference\n':
            raise RuntimeError('STOP: synthetic DRYRUN marker mismatch')
        log_raw, log_id = _read_regular(rootfd, 'SYNTHETIC_parent_first.log', opened, device)
        if b'STOP' in log_raw.upper():
            raise RuntimeError('STOP: synthetic parent log contains STOP text')
        cfg_raw, _ = _read_regular(rootfd, 'config.json', opened, device)
        cfg = json.loads(cfg_raw)
        if (cfg.get('dryrun') is not True or cfg.get('host') != 'DRYRUN'
                or Path(cfg.get('dryrun_root', '')).resolve() != root):
            raise RuntimeError('STOP: config is not the expected synthetic DRYRUN')
        host_check(cfg, batch)
        _no_stop_marker(batchfd)
        state_raw, state_id = _read_regular(batchfd, 'batch_state.json', opened, device)
        state = json.loads(state_raw)
        if (state.get('status') != 'RUNNING' or state.get('stop_reason') is not None
                or state.get('phase') != 'b1' or state.get('execution_label') != 'DRYRUN'
                or not isinstance(state.get('in_progress'), dict)
                or state['in_progress'].get('pid') != worker_pid
                or state['in_progress'].get('path') != str(partial)):
            raise RuntimeError('STOP: synthetic batch is not the expected unrecorded crash')
        lock_raw, lock_id = _read_regular(batchfd, 'runner.lock', opened, device)
        if json.loads(lock_raw).get('pid') != parent_pid:
            raise RuntimeError('STOP: synthetic parent lock mismatch')
        serversfd = os.open('servers', flags, dir_fd=batchfd); opened.append(serversfd)
        _dir_identity(os.fstat(serversfd), device)
        aliasfd = os.open('qwen25_coder_7b', flags, dir_fd=serversfd); opened.append(aliasfd)
        _dir_identity(os.fstat(aliasfd), device)
        server_raw, _ = _read_regular(aliasfd, server_record.name, opened, device)
        server = json.loads(server_raw)
        if (server.get('label') != 'DRYRUN' or server.get('pid') != server_pid
                or server.get('alias') != 'qwen25_coder_7b'
                or server.get('binary') != str(root/'fake_llama_server')
                or server.get('model_path') != str(root/'models'/'qwen25_coder_7b.gguf')):
            raise RuntimeError('STOP: synthetic server identity mismatch')
        for pid in pids:
            _require_absent_process(pid)
        try:
            os.mkdir('_to_delete', 0o700, dir_fd=batchfd)
        except FileExistsError:
            pass
        archivefd = os.open('_to_delete', flags, dir_fd=batchfd); opened.append(archivefd)
        _dir_identity(os.fstat(archivefd), device)
        # Re-read through new descriptors immediately before rename. Neither
        # state nor lock is rewritten and no recorded STOP may be bypassed.
        log_raw2, log_id2 = _read_regular(rootfd, 'SYNTHETIC_parent_first.log', opened, device)
        if (log_raw2, log_id2) != (log_raw, log_id) or b'STOP' in log_raw2.upper():
            raise RuntimeError('STOP: synthetic parent log changed before lock retirement')
        state_raw2, state_id2 = _read_regular(batchfd, 'batch_state.json', opened, device)
        lock_raw2, lock_id2 = _read_regular(batchfd, 'runner.lock', opened, device)
        if (state_raw2, state_id2) != (state_raw, state_id) or (lock_raw2, lock_id2) != (lock_raw, lock_id):
            raise RuntimeError('STOP: synthetic crash scene changed before lock retirement')
        _no_stop_marker(batchfd)
        for pid in pids:
            _require_absent_process(pid)
        target = 'crashed_runner_lock.' + uuid.uuid4().hex + '.json'
        _renameat_dryrun(batchfd, 'runner.lock', archivefd, target, _NOREPLACE)
        archived = os.stat(target, dir_fd=archivefd, follow_symlinks=False)
        if (archived.st_dev, archived.st_ino, archived.st_uid, archived.st_nlink) != lock_id or not stat.S_ISREG(archived.st_mode):
            raise RuntimeError('STOP: retired synthetic lock identity mismatch')
        os.fsync(batchfd); os.fsync(archivefd)
        return batch/'_to_delete'/target
    except BaseException:
        body_failed = True
        raise
    finally:
        close_error = None
        for fd in reversed(opened):
            try:
                os.close(fd)
            except BaseException as exc:
                if close_error is None:
                    close_error = exc
        if not body_failed and close_error is not None:
            raise close_error
