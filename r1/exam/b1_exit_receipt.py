"""Cooperative B1 normal-exit receipt; not cryptographic process attestation."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from r1.exam.b1_state_preserve import ACTIVE, EXIT_RECEIPT, write_exclusive_json

MAX_BYTES = 16 * 1024 * 1024


def read_owned_regular(path):
    """Read a stable, non-symlink, user-owned regular file, bounded in size."""
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid()
                or before.st_mode & 0o022 or before.st_size > MAX_BYTES):
            raise RuntimeError('STOP: B1 receipt input is not an owned regular file')
        chunks = []
        total = 0
        while True:
            piece = os.read(fd, min(65536, MAX_BYTES + 1 - total))
            if not piece:
                break
            total += len(piece)
            if total > MAX_BYTES:
                raise RuntimeError('STOP: B1 receipt input too large')
            chunks.append(piece)
        after = os.fstat(fd)
        named = os.stat(path, follow_symlinks=False)
        key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if key(before) != key(after) or key(after) != key(named):
            raise RuntimeError('STOP: B1 receipt input changed while read')
        return b''.join(chunks)
    finally:
        os.close(fd)


def active_and_state(batch, head, pid):
    batch = Path(batch)
    if os.path.lexists(batch / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch has a STOP record')
    active_bytes = read_owned_regular(batch / ACTIVE)
    active = json.loads(active_bytes)
    if (not isinstance(active, dict) or set(active) != {'version','runner_pid','authorization_checkout_head'}
            or active.get('version') != 'b1_active/v1' or type(pid) is not int or pid <= 0
            or type(active.get('runner_pid')) is not int
            or active.get('runner_pid') != pid or active.get('authorization_checkout_head') != head):
        raise RuntimeError('STOP: B1 active sentinel does not bind the waited runner and authority')
    state_bytes = read_owned_regular(batch / 'batch_state.json')
    state = json.loads(state_bytes)
    if (not isinstance(state, dict) or state.get('status') != 'COMPLETE'
            or state.get('phase') != 'b1' or state.get('execution_label') != 'EVIDENCE'):
        raise RuntimeError('STOP: B1 waited runner did not leave a complete evidence state')
    if os.path.lexists(batch / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch gained a STOP record')
    return active_bytes, state_bytes


def _verified_finalization(batch, head):
    # The containment implementation must supply this module. Without it,
    # B1 cannot publish or verify a waited-exit receipt.
    try:
        from r1.exam.b1_finalization import verify_finalization
    except ImportError as exc:
        raise RuntimeError('STOP: B1 guardian finalization verifier is unavailable') from exc
    verify_finalization(batch, head)
    return read_owned_regular(Path(batch) / 'FINALIZED.json')


def publish_waited_success(batch, head, pid, wait_result):
    """A cooperative supervisor calls this only with its actual child's wait result."""
    if type(wait_result) is not int or wait_result != 0:
        raise RuntimeError('STOP: B1 runner did not exit successfully')
    active, state = active_and_state(batch, head, pid)
    finalized = _verified_finalization(batch, head)
    receipt = {'version':'b1_waited_exit/v1','runner_pid':pid,'exit_code':0,
               'authorization_checkout_head':head,
               'active_sha256':hashlib.sha256(active).hexdigest(),
               'batch_state_sha256':hashlib.sha256(state).hexdigest(),
               'finalization_sha256':hashlib.sha256(finalized).hexdigest()}
    write_exclusive_json(Path(batch) / EXIT_RECEIPT, receipt)
    return receipt


def publish_after_wait(child, batch, head):
    """Wait for the actual runner; no success receipt on failure or signal."""
    result = child.wait()
    return publish_waited_success(batch, head, child.pid, result)


def verify_waited_success(batch, head):
    """Fail closed without the receipt; trusts the cooperative receipt writer."""
    raw = read_owned_regular(Path(batch) / EXIT_RECEIPT)
    receipt = json.loads(raw)
    if (not isinstance(receipt,dict) or set(receipt) != {
            'version','runner_pid','exit_code','authorization_checkout_head',
            'active_sha256','batch_state_sha256','finalization_sha256'} or receipt.get('version') != 'b1_waited_exit/v1'
            or type(receipt.get('exit_code')) is not int or receipt['exit_code'] != 0
            or receipt.get('authorization_checkout_head') != head):
        raise RuntimeError('STOP: invalid B1 waited-exit receipt')
    active, state = active_and_state(batch, head, receipt.get('runner_pid'))
    finalized = _verified_finalization(batch, head)
    if (receipt.get('active_sha256') != hashlib.sha256(active).hexdigest()
            or receipt.get('batch_state_sha256') != hashlib.sha256(state).hexdigest()
            or receipt.get('finalization_sha256') != hashlib.sha256(finalized).hexdigest()):
        raise RuntimeError('STOP: B1 waited-exit receipt bytes mismatch')
    if os.path.lexists(Path(batch) / 'STOP.json'):
        raise RuntimeError('STOP: B1 batch has a STOP record')
    return receipt
