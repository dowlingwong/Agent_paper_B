"""Optional per-manifest EVIDENCE note verifier; not connected to submission.

AI-assisted (Codex). This verifies a proposed format, not an author decision,
semantic job identity, phase readiness, live host, or cryptographic authorship.
The caller must supply independently reviewed current limits. The EVIDENCE
submission path remains unconditionally STOP in hk2_submit.py.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess


class EvidenceNoteError(ValueError):
    pass


def _git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, timeout=30)
    if result.returncode:
        raise EvidenceNoteError('committed checkout verification failed')
    return result.stdout


def _head_clean(root):
    head = _git(root, 'rev-parse', '--verify', 'HEAD').strip().decode('ascii')
    if not re.fullmatch(r'[0-9a-f]{40}', head):
        raise EvidenceNoteError('invalid checkout HEAD')
    if _git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise EvidenceNoteError('checkout is not clean')
    return head


def _committed_file(root, head, relative):
    if not isinstance(relative, str) or not relative or '\x00' in relative:
        raise EvidenceNoteError('invalid relative path')
    path = Path(relative)
    if path.is_absolute() or any(part in ('..', '.', '.git') for part in path.parts):
        raise EvidenceNoteError('path must stay inside checkout')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise EvidenceNoteError('symlink path refused')
    if not current.is_file():
        raise EvidenceNoteError('committed file is missing')
    mode = _git(root, 'ls-tree', head, '--', relative).split(b'\t', 1)[0].split()
    if len(mode) < 3 or mode[0] not in (b'100644', b'100755') or mode[1] != b'blob':
        raise EvidenceNoteError('path is not a committed regular file')
    committed = _git(root, 'show', head + ':' + relative)
    if current.read_bytes() != committed:
        raise EvidenceNoteError('working file differs from committed bytes')
    return committed


def _positive_number(value, upper, name):
    try:
        finite = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise EvidenceNoteError(name + ' must be a finite number')
    if value <= 0 or value > upper:
        raise EvidenceNoteError(name + ' outside reviewed bounds')
    return value


def _strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceNoteError('duplicate JSON key')
            result[key] = value
        return result
    def invalid_constant(_):
        raise EvidenceNoteError('non-finite JSON constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)


def verify_note(root, note_path, manifest_path, expected_phase, *, max_nodes, max_budget_gpu_hours):
    """Verify exact committed note/manifest binding; never launch a job.

    max_nodes and max_budget_gpu_hours are explicit reviewed caller limits,
    not author decisions. Return an immutable checkout identity and note fields.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise EvidenceNoteError('checkout root missing')
    if type(max_nodes) is not int or max_nodes < 1:
        raise EvidenceNoteError('reviewed maximum nodes must be positive integer')
    _positive_number(max_budget_gpu_hours, float('inf'), 'reviewed maximum budget')
    if expected_phase not in ('HK6', 'HK7'):
        raise EvidenceNoteError('unsupported evidence phase')
    if Path(os.fsdecode(_git(root, 'rev-parse', '--show-toplevel').strip())).resolve() != root:
        raise EvidenceNoteError('checkout root must be the repository top level')
    head = _head_clean(root)
    try:
        note = _strict_json(_committed_file(root, head, note_path))
        manifest_raw = _committed_file(root, head, manifest_path)
        manifest = _strict_json(manifest_raw)
    except (UnicodeError, ValueError, OSError) as exc:
        if isinstance(exc, EvidenceNoteError):
            raise
        raise EvidenceNoteError('invalid note or manifest JSON') from exc
    fields = {'schema', 'author', 'approved', 'phase', 'manifest_sha256',
              'node_count', 'audit_k', 'budget_gpu_hours'}
    if not isinstance(note, dict) or set(note) != fields:
        raise EvidenceNoteError('note fields do not match the proposed schema')
    if note['schema'] != 'hk2_evidence_authorization/v1' or note['author'] != 'Dowling Wong' or note['approved'] is not True:
        raise EvidenceNoteError('note identity or approval invalid')
    if note['phase'] != expected_phase or not isinstance(manifest, dict) or manifest.get('schema') != 'hk2_job/v1' or manifest.get('kind') != 'evidence' or manifest.get('phase') != expected_phase:
        raise EvidenceNoteError('note and evidence manifest phase mismatch')
    digest = hashlib.sha256(manifest_raw).hexdigest()
    if note['manifest_sha256'] != digest:
        raise EvidenceNoteError('manifest digest mismatch')
    if type(note['node_count']) is not int or not 1 <= note['node_count'] <= max_nodes:
        raise EvidenceNoteError('node count outside reviewed bounds')
    if type(note['audit_k']) is not int or note['audit_k'] not in (6, 10):
        raise EvidenceNoteError('audit K must be 6 or 10')
    _positive_number(note['budget_gpu_hours'], max_budget_gpu_hours, 'budget')
    if _head_clean(root) != head:
        raise EvidenceNoteError('checkout HEAD changed during verification')
    return {'head': head, 'manifest_sha256': digest, 'phase': expected_phase,
            'node_count': note['node_count'], 'audit_k': note['audit_k'],
            'budget_gpu_hours': note['budget_gpu_hours']}
