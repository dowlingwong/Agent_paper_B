"""Exclusive B1 finalization receipt; independent site review still required."""
import hashlib
import json
import os
from pathlib import Path

VERSION = 'b1_finalization/v1'
KEYS = frozenset({'version', 'phase', 'authorization_head', 'batch_state_sha256', 'status'})


def _payload(state_bytes, head):
    if not isinstance(head, str) or len(head) != 40 or any(c not in '0123456789abcdef' for c in head):
        raise ValueError('STOP: invalid B1 finalization authorization HEAD')
    state = json.loads(state_bytes)
    if not isinstance(state,dict) or state.get('status') != 'COMPLETE' or state.get('phase') != 'b1':
        raise ValueError('STOP: B1 state is not complete')
    return {'version': VERSION, 'phase': 'b1', 'authorization_head': head,
            'batch_state_sha256': hashlib.sha256(state_bytes).hexdigest(), 'status': 'FINALIZED'}


def write_finalization(batch, head):
    """Write one new receipt after guardian FINISH; never replace an entry.

    A failed or partial write is retained. Filesystem crash-durability and
    races with external same-UID writers require independent site review.
    """
    batch = Path(batch)
    if os.path.lexists(batch / 'STOP.json'):
        raise ValueError('STOP: STOP record exists')
    payload = _payload((batch / 'batch_state.json').read_bytes(), head)
    raw = (json.dumps(payload, sort_keys=True, separators=(',', ':')) + '\n').encode()
    fd = os.open(batch / 'FINALIZED.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise OSError('short finalization receipt write')
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)


def verify_finalization(batch, head):
    """Require a regular, exact receipt bound to the current batch state."""
    batch = Path(batch)
    path = batch / 'FINALIZED.json'
    if path.is_symlink() or not path.is_file():
        raise ValueError('STOP: B1 finalization receipt absent or not regular')
    try:
        raw = path.read_bytes()
        receipt = json.loads(raw)
        expected = _payload((batch / 'batch_state.json').read_bytes(), head)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError('STOP: B1 finalization receipt or state unavailable') from exc
    if not isinstance(receipt, dict) or set(receipt) != KEYS or receipt != expected:
        raise ValueError('STOP: B1 finalization receipt does not bind state and HEAD')
    if raw != (json.dumps(receipt, sort_keys=True, separators=(',', ':')) + '\n').encode():
        raise ValueError('STOP: B1 finalization receipt is noncanonical or partial')
    return receipt
