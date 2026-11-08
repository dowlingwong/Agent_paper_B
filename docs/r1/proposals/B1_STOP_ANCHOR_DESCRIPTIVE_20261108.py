"""Read only uniquely bound B1 anchor manifests; no gate/bootstrap execution.

Only random_valid and scripted roots for instance seeds 9001-9004 are read.
Each B1 job must bind audit seeds 9101-9104 before its manifest is opened.
Full JSON file bytes are read; their B1 producer provenance is a cooperative
process assumption, not proof against a hostile writer or prior corruption.
"""
import hashlib
import json
import math
import os
import stat
import sys
from datetime import datetime, timezone

ROOT = '/home/dowling/exam-x/work/b1_6835_20261108_a'
HEAD = '68357d3d8cd0c9f301005e483a49ecfd05f6e5bb'
RULE = '53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad'
ANCHORS = ('random_valid', 'scripted')
ALL_ANCHORS = ANCHORS + ('qwen25_coder_7b',)
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
SEEDS = (9001, 9002, 9003, 9004)
AUDIT = [9101, 9102, 9103, 9104]
EXPECTED_REASON = 'RuntimeError: STOP: random-valid < scripted cannot be shown; no discriminating power'


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _constant(_):
    raise ValueError('non-finite JSON number')


def _read(root, parts):
    if not os.path.isabs(root) or '..' in root.split('/'):
        raise ValueError('unsafe root')
    if not hasattr(os, 'O_NOATIME'):
        raise ValueError('O_NOATIME unavailable')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in tuple(p for p in root.split('/') if p) + tuple(parts[:-1]):
            if not part or part in ('.', '..') or '/' in part: raise ValueError('invalid path component')
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = new
        name = parts[-1]
        if not name or name in ('.', '..') or '/' in name: raise ValueError('invalid filename')
        f = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME, dir_fd=fd)
        try:
            before = os.fstat(f)
            if not stat.S_ISREG(before.st_mode) or before.st_uid != os.getuid():
                raise ValueError('file is not an owned regular file')
            chunks = []
            while True:
                part = os.read(f, 65536)
                if not part: break
                chunks.append(part)
            after = os.fstat(f)
            now = os.stat(name, dir_fd=fd, follow_symlinks=False)
            identity = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
            if identity(before) != identity(after) or identity(after) != identity(now):
                raise ValueError('file changed during read')
            raw = b''.join(chunks)
            return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique, parse_constant=_constant), hashlib.sha256(raw).hexdigest()
        finally:
            os.close(f)
    finally:
        os.close(fd)


def _audit_seeds_match(value):
    return isinstance(value, list) and all(type(v) is int for v in value) and value == AUDIT


def inspect(root):
    state, state_sha = _read(root, ('batch_state.json',))
    if (not isinstance(state, dict) or state.get('phase') != 'b1' or state.get('status') != 'STOPPED' or
            state.get('stop_reason') != EXPECTED_REASON or state.get('in_progress')):
        raise ValueError('STOP state mismatch')
    completed = state.get('completed')
    expected_keys = {'%s/b1/off/%s__s%d' % (a, n, seed) for a in ALL_ANCHORS for n in NODES for seed in SEEDS}
    if not isinstance(completed, dict) or set(completed) != expected_keys:
        raise ValueError('completed root set differs from STOP capture')
    binding = state.get('binding')
    if not isinstance(binding, str) or not binding:
        raise ValueError('missing run binding')
    rows = []
    for anchor in ANCHORS:
        for node in NODES:
            for seed in SEEDS:
                path_parts = (anchor, 'b1', 'off', '%s__s%d' % (node, seed))
                key = '/'.join(path_parts)
                job, job_sha = _read(root, path_parts + ('job.json',))
                cfg = job.get('authority_config') if isinstance(job, dict) else None
                candidate = job.get('candidate') if isinstance(job, dict) else None
                if (not isinstance(cfg, dict) or not isinstance(candidate, dict) or candidate.get('id') != anchor or
                        job.get('phase') != 'b1' or job.get('node') != node or job.get('seed') != seed or
                        job.get('mode') != 'off' or job.get('dryrun') is not False or job.get('binding') != binding or
                        job.get('authorization_checkout_head') != HEAD or not _audit_seeds_match(job.get('audit_seeds')) or
                        not _audit_seeds_match(cfg.get('audit_seeds')) or cfg.get('instance_seeds') != list(SEEDS) or cfg.get('rule_sha256') != RULE):
                    raise ValueError('B1 job identity or seed mismatch; manifest not opened')
                entry = completed[key]
                expected_path = root + '/' + key + '/campaign_manifest.json'
                if not isinstance(entry, dict) or entry.get('path') != expected_path:
                    raise ValueError('root state path mismatch; manifest not opened')
                manifest, manifest_sha = _read(root, path_parts + ('campaign_manifest.json',))
                if (manifest_sha != entry.get('sha256') or not isinstance(manifest, dict) or
                        manifest.get('job_sha256') != job_sha or manifest.get('job_binding') != binding or
                        manifest.get('phase') != 'b1' or manifest.get('execution_label') != 'EVIDENCE' or
                        manifest.get('status') != 'COMPLETE' or manifest.get('candidate') != anchor or
                        manifest.get('node') != node or manifest.get('instance_seed') != seed or manifest.get('mode') != 'off'):
                    raise ValueError('manifest binding or identity mismatch')
                proposals = manifest.get('audited_proposals')
                diagnostics = manifest.get('diagnostics')
                if not isinstance(proposals, list) or not isinstance(diagnostics, dict): raise ValueError('missing diagnostics')
                seen = set(); deltas = []
                for p in proposals:
                    if (not isinstance(p, dict) or not _audit_seeds_match(p.get('audit_seeds')) or
                            p.get('instance_id') != '%s__s%d' % (node, seed) or p.get('node') != node or p.get('mode') != 'off'):
                        raise ValueError('proposal seed or identity mismatch')
                    pid = p.get('proposal_id'); value = p.get('delta_audit')
                    if not isinstance(pid, str) or not pid or pid in seen or type(value) not in (int, float) or not math.isfinite(value):
                        raise ValueError('invalid proposal delta or duplicate')
                    for field in ('candidate_metrics', 'incumbent_metrics'):
                        values = p.get(field)
                        if not isinstance(values, list) or len(values) != len(AUDIT): raise ValueError('audit vector length mismatch')
                    seen.add(pid); deltas.append(value)
                counts = {}
                for name in ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed'):
                    value = diagnostics.get(name)
                    if type(value) is not int or value < 0: raise ValueError('invalid diagnostic count')
                    counts[name] = value
                rows.append({'anchor': anchor, 'node': node, 'instance_seed': seed,
                             'audited_proposals': len(deltas), 'mean_delta_audit': math.fsum(deltas)/len(deltas) if deltas else None,
                             'diagnostics': counts, 'job_sha256': job_sha, 'manifest_sha256': manifest_sha})
    return {'source': 'B1-only preserved root manifests', 'state_sha256': state_sha,
            'rows': rows, 'comparison_or_gate_recomputed': False,
            'limitations': 'Full JSON read under reviewed producer and cooperative provenance assumptions; no 7006-7010 audit is expected in these B1-only files. No bootstrap, paired difference, confidence interval, raw audit vector, or gate verdict is produced.'}


def main():
    try:
        result = inspect(ROOT)
        result['observed_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        print('DESCRIPTIVE_CAPTURE_COMPLETE')
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, UnicodeError) as exc:
        print('STOP: descriptive inspection refused: ' + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
