"""B1 STOP diagnosis D0-D8 (plan docs/r1/proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md, section 3).

Two entry points, both read-only and descriptive; neither changes the recorded STOP.

1. Host mode (default, no arguments; run once on TASL-7 through the reviewed
   wrapper): reads the preserved B1 STOP root of run 6835_20261108_a for all
   three anchors (36 roots). For every root it validates the job binding
   (exact reviewed HEAD, B1, node, instance seed, audit seeds 9101-9104, rule
   hash) BEFORE opening the manifest, then checks the manifest against the
   batch-state SHA and the job SHA, then checks root_trials.jsonl against the
   manifest's evidence hash. Only after all 36 roots validate does it print
   anything. It extends the accepted descriptive reader
   (B1_STOP_ANCHOR_DESCRIPTIVE_20261108.py, SHA 46058875...) with the same
   path, O_NOATIME, owner and file-identity checks.

2. Local mode (``--descriptive-capture PATH``, on the Mac): reads the JSON
   line of the already accepted descriptive capture (24 random_valid/scripted
   rows) and computes D1 and the D3 per-node means and their sigma-standardised
   versions only. It never contacts a host.

No 7006-7010 file is opened. No raw per-seed metric vector is output; the
output carries per-proposal (budget index, delta_audit) pairs, counts and
summaries. The bootstrap is a byte-for-byte port of the frozen
r1/exam/guards.py::paired_instance_bootstrap at 68357d3d (a test compares
them). Provenance is the cooperative producer/path boundary disclosed in the
descriptive plan; it is not protection against a hostile same-UID writer.
"""
import hashlib
import json
import math
import os
import random
import re
import stat
import sys
from datetime import datetime, timezone

ROOT = '/home/dowling/exam-x/work/b1_6835_20261108_a'
HEAD = '68357d3d8cd0c9f301005e483a49ecfd05f6e5bb'
RULE = '53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad'
ANCHORS = ('random_valid', 'scripted', 'qwen25_coder_7b')
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
SEEDS = (9001, 9002, 9003, 9004)
AUDIT = [9101, 9102, 9103, 9104]
W = 20
EXPECTED_REASON = 'RuntimeError: STOP: random-valid < scripted cannot be shown; no discriminating power'
METRIC = {'digits_mlp': 'val_score', 'openml_credit_approval': 'val_auc', 'openml_ionosphere': 'val_auc'}
# D21 noise floor, docs/r1/reports/NOISE_FLOOR_COMMON_20261022.md (commit 511c3797,
# file SHA-256 9be292b773799d1591e55ea6845551a8fa121b00ec1a0dfe324b2c46de52c01d), Table 1, 30 seeds per condition.
SIGMA_JOINT = {'digits_mlp': 0.0102, 'openml_credit_approval': 0.0279, 'openml_ionosphere': 0.0410}
MEDIAN_SD_DELTA = {'digits_mlp': 0.0066, 'openml_credit_approval': 0.0030, 'openml_ionosphere': 0.0160}
DUP_REF = (0.4239, 0.5800)
PID = re.compile(r'^EXAM:(?P<inst>[a-z_]+__s\d{4}):t(?P<b>\d{3})$')


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _constant(_):
    raise ValueError('non-finite JSON number')


def _loads(raw):
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique, parse_constant=_constant)


def _read_bytes(root, parts):
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
            return raw, hashlib.sha256(raw).hexdigest()
        finally:
            os.close(f)
    finally:
        os.close(fd)


def _read(root, parts):
    raw, sha = _read_bytes(root, parts)
    return _loads(raw), sha


def _audit_seeds_match(value):
    return isinstance(value, list) and all(type(v) is int for v in value) and value == AUDIT


def _num(x):
    return type(x) in (int, float) and math.isfinite(x)


def paired_instance_bootstrap(first, second, *, field='value', resamples=2000, seed=20261026):
    """Port of frozen r1/exam/guards.py::paired_instance_bootstrap (68357d3d)."""
    def clusters(rows):
        out = {}
        for r in rows:
            key = str(r['instance_id']); value = float(r[field])
            if not math.isfinite(value): raise ValueError('non-finite bootstrap input')
            out.setdefault(key, []).append(value)
        return {k: sum(v)/len(v) for k, v in out.items()}
    a, b = clusters(first), clusters(second)
    if not a or set(a) != set(b): raise ValueError('paired bootstrap requires identical nonempty instance sets')
    if resamples < 100: raise ValueError('at least 100 bootstrap resamples required')
    keys = sorted(a); diffs = [a[k]-b[k] for k in keys]; rng = random.Random(seed)
    draws = sorted(sum(rng.choice(diffs) for _ in keys)/len(keys) for _ in range(resamples))
    def pct(p):
        x = (len(draws)-1)*p; l = math.floor(x); h = math.ceil(x)
        return draws[l]*(h-x)+draws[h]*(x-l) if l != h else draws[l]
    point = sum(diffs)/len(diffs); lo, hi = pct(.025), pct(.975)
    return {'difference_point': point, 'difference_lower': lo, 'difference_upper': hi, 'median': pct(.5),
            'instances': len(keys), 'resampling_unit': 'instance_pair', 'bootstrap_resamples': resamples,
            'bootstrap_seed': seed, 'point_within_interval': lo <= point <= hi, 'bootstrap_unstable': not lo <= point <= hi,
            'descriptive_only': True}


def _median(xs):
    s = sorted(xs); n = len(s)
    if not n: return None
    return s[n//2] if n % 2 else (s[n//2-1]+s[n//2])/2


def _mean(xs):
    return math.fsum(xs)/len(xs) if xs else None


def _summary(deltas, node):
    m = _mean(deltas)
    return {'n': len(deltas), 'mean': m, 'median': _median(deltas),
            'share_harmful': (sum(d < 0 for d in deltas)/len(deltas)) if deltas else None,
            'mean_over_sigma_joint': None if m is None else m/SIGMA_JOINT[node],
            'mean_over_median_sd_delta': None if m is None else m/MEDIAN_SD_DELTA[node]}


def _trials(raw, node):
    """In-run ledger counts. The pinned harness keeps the first valid trial
    unconditionally (decision.py: "First valid metric becomes the current best"),
    so there is no unedited start metric in the ledger: ``first_valid_metric`` is
    the in-run metric of the first valid (edited) trial, and
    ``final_kept_metric`` the in-run metric of the last kept record. Demotions,
    if any, are not followed (none are expected without a controller)."""
    rows = []
    for line in raw.decode('utf-8').splitlines():
        if line.strip(): rows.append(_loads(line.encode('utf-8')))
    metric = METRIC[node]; keeps = 0; skipped = 0; first = None; last_kept = None; decisions = {}
    for r in rows:
        if not isinstance(r, dict) or type(r.get('budget_index')) is not int: raise ValueError('bad trial row')
    for r in sorted(rows, key=lambda r: r['budget_index']):
        if r.get('node_id') not in (None, node): raise ValueError('trial node mismatch')
        value = (r.get('parsed_metrics') or {}).get(metric)
        decision = str(r.get('decision'))
        decisions[decision] = decisions.get(decision, 0) + 1
        if first is None and _num(value) and decision == 'kept': first = value
        if decision == 'kept':
            keeps += 1
            if _num(value): last_kept = value
        if decision == 'skipped': skipped += 1
    return {'records': len(rows), 'decisions': decisions, 'keeps_including_first': keeps, 'skipped': skipped,
            'first_valid_metric': first, 'final_kept_metric': last_kept,
            'gain_after_first_keep': None if first is None or last_kept is None else last_kept-first}


def inspect_root(root, completed, binding, anchor, node, seed):
    parts = (anchor, 'b1', 'off', '%s__s%d' % (node, seed)); key = '/'.join(parts)
    job, job_sha = _read(root, parts + ('job.json',))
    cfg = job.get('authority_config') if isinstance(job, dict) else None
    candidate = job.get('candidate') if isinstance(job, dict) else None
    if (not isinstance(cfg, dict) or not isinstance(candidate, dict) or candidate.get('id') != anchor or
            job.get('phase') != 'b1' or job.get('node') != node or job.get('seed') != seed or
            job.get('mode') != 'off' or job.get('dryrun') is not False or job.get('binding') != binding or
            job.get('authorization_checkout_head') != HEAD or not _audit_seeds_match(job.get('audit_seeds')) or
            not _audit_seeds_match(cfg.get('audit_seeds')) or cfg.get('instance_seeds') != list(SEEDS) or
            cfg.get('rule_sha256') != RULE or job.get('W') != W):
        raise ValueError('B1 job identity or seed mismatch; manifest not opened')
    entry = completed[key]
    if not isinstance(entry, dict) or entry.get('path') != root + '/' + key + '/campaign_manifest.json':
        raise ValueError('root state path mismatch; manifest not opened')
    manifest, manifest_sha = _read(root, parts + ('campaign_manifest.json',))
    if (manifest_sha != entry.get('sha256') or not isinstance(manifest, dict) or
            manifest.get('job_sha256') != job_sha or manifest.get('job_binding') != binding or
            manifest.get('phase') != 'b1' or manifest.get('execution_label') != 'EVIDENCE' or
            manifest.get('status') != 'COMPLETE' or manifest.get('candidate') != anchor or
            manifest.get('node') != node or manifest.get('instance_seed') != seed or manifest.get('mode') != 'off'):
        raise ValueError('manifest binding or identity mismatch')
    proposals = manifest.get('audited_proposals'); diagnostics = manifest.get('diagnostics')
    budget = manifest.get('compute_budget'); hashes = manifest.get('evidence_hashes')
    if not isinstance(proposals, list) or not isinstance(diagnostics, dict) or not isinstance(budget, dict) or not isinstance(hashes, dict):
        raise ValueError('missing manifest sections')
    inst = '%s__s%d' % (node, seed); seen = set(); props = []; d0 = {'k_not_4': 0, 'none_in_vectors': 0, 'delta_mismatch': 0}
    for p in proposals:
        if (not isinstance(p, dict) or not _audit_seeds_match(p.get('audit_seeds')) or
                p.get('instance_id') != inst or p.get('node') != node or p.get('mode') != 'off'):
            raise ValueError('proposal seed or identity mismatch')
        pid = p.get('proposal_id'); value = p.get('delta_audit'); match = PID.match(pid) if isinstance(pid, str) else None
        if not match or match.group('inst') != inst or pid in seen or not _num(value):
            raise ValueError('invalid proposal id, delta or duplicate')
        cand, inc = p.get('candidate_metrics'), p.get('incumbent_metrics')
        if not isinstance(cand, list) or not isinstance(inc, list) or len(cand) != len(AUDIT) or len(inc) != len(AUDIT):
            raise ValueError('audit vector length mismatch')
        if p.get('k') != len(AUDIT): d0['k_not_4'] += 1
        if not all(_num(v) for v in cand + inc): d0['none_in_vectors'] += 1
        else:
            recomputed = math.fsum(c-i for c, i in zip(cand, inc))/len(AUDIT)
            if abs(recomputed - value) > 1e-12: d0['delta_mismatch'] += 1
        seen.add(pid); props.append({'budget_index': int(match.group('b')), 'delta_audit': value})
    counts = {}
    for name in ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed'):
        v = diagnostics.get(name)
        if type(v) is not int or v < 0: raise ValueError('invalid diagnostic count')
        counts[name] = v
    trials_sha = hashes.get('root_trials.jsonl')
    raw, sha = _read_bytes(root, parts + ('root_trials.jsonl',))
    if not isinstance(trials_sha, str) or sha != trials_sha: raise ValueError('root_trials hash mismatch')
    return {'anchor': anchor, 'node': node, 'instance_seed': seed, 'instance_id': inst,
            'job_sha256': job_sha, 'manifest_sha256': manifest_sha, 'root_trials_sha256': sha,
            'termination': manifest.get('termination'), 'worker_runs': budget.get('worker_runs'),
            'd0': d0, 'diagnostics': counts, 'trials': _trials(raw, node),
            'proposals': sorted(props, key=lambda r: r['budget_index'])}


def summarize(rows):
    by = {(r['anchor'], r['node'], r['instance_seed']): r for r in rows}
    def vals(anchor):
        return [{'instance_id': r['instance_id'], 'value': p['delta_audit']}
                for r in rows if r['anchor'] == anchor for p in r['proposals']]
    out = {}
    # D1: the gate exactly as anchor_gate computes it (scripted first, random_valid second).
    try:
        out['D1_gate_recomputed'] = paired_instance_bootstrap(vals('scripted'), vals('random_valid'))
        out['D1_reproduces_stop'] = out['D1_gate_recomputed']['difference_lower'] <= 0
    except ValueError as exc:
        out['D1_gate_recomputed'] = None; out['D1_error'] = str(exc); out['D1_reproduces_stop'] = None
    per_inst = []
    for node in NODES:
        for seed in SEEDS:
            s = [p['delta_audit'] for p in by[('scripted', node, seed)]['proposals']]
            r = [p['delta_audit'] for p in by[('random_valid', node, seed)]['proposals']]
            ms, mr = _mean(s), _mean(r)
            per_inst.append({'instance_id': '%s__s%d' % (node, seed), 'node': node, 'scripted_mean': ms, 'random_valid_mean': mr,
                             'difference': None if ms is None or mr is None else ms-mr,
                             'difference_over_sigma_joint': None if ms is None or mr is None else (ms-mr)/SIGMA_JOINT[node]})
    out['D1_per_instance'] = per_inst
    d2, d3, d4 = {}, {}, {}
    for anchor in ANCHORS:
        for node in NODES:
            rs = [by[(anchor, node, s)] for s in SEEDS]; k = anchor + '/' + node
            d2[k] = {'roots': len(rs), 'worker_runs': [r['worker_runs'] for r in rs], 'termination': sorted({str(r['termination']) for r in rs}),
                     **{n: sum(r['diagnostics'][n] for r in rs) for n in ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed')},
                     'audited': sum(len(r['proposals']) for r in rs),
                     'keeps_including_first': sum(r['trials']['keeps_including_first'] for r in rs),
                     'mean_gain_after_first_keep': _mean([r['trials']['gain_after_first_keep'] for r in rs if r['trials']['gain_after_first_keep'] is not None]),
                     'd0': {n: sum(r['d0'][n] for r in rs) for n in ('k_not_4', 'none_in_vectors', 'delta_mismatch')}}
            deltas = [p['delta_audit'] for r in rs for p in r['proposals']]
            d3[k] = _summary(deltas, node)
            # Halves of each root's audited sequence (budget indices can exceed W when
            # duplicates/no-ops consume no worker run), plus the budget-index split.
            first, second = [], []
            for r in rs:
                ps = r['proposals']; h = (len(ps)+1)//2
                first += [p['delta_audit'] for p in ps[:h]]; second += [p['delta_audit'] for p in ps[h:]]
            early = [p['delta_audit'] for r in rs for p in r['proposals'] if p['budget_index'] <= W//2]
            late = [p['delta_audit'] for r in rs for p in r['proposals'] if p['budget_index'] > W//2]
            d4[k] = {'first_half_of_audited': _summary(first, node), 'second_half_of_audited': _summary(second, node),
                     'budget_index_le_10': _summary(early, node), 'budget_index_gt_10': _summary(late, node)}
    out['D2'] = d2; out['D3'] = {k: v for k, v in d3.items() if not k.startswith('qwen25')}; out['D4'] = d4
    q = [r for r in rows if r['anchor'] == 'qwen25_coder_7b']
    dup = sum(r['diagnostics']['duplicates'] for r in q); ev = sum(r['diagnostics']['evaluated'] for r in q)
    rate = dup/ev if ev else None
    out['D7'] = {'duplicates': dup, 'evaluated': ev, 'rate': rate, 'reference': list(DUP_REF),
                 'inside': None if rate is None else DUP_REF[0] <= rate <= DUP_REF[1]}
    out['D8_information_only'] = {k: v for k, v in d3.items() if k.startswith('qwen25')}
    out['sigma_source'] = 'NOISE_FLOOR_COMMON_20261022.md Table 1 (sha256 9be292b7...c01d), sigma_joint and median sd(delta)'
    return out


def inspect(root):
    state, state_sha = _read(root, ('batch_state.json',))
    if (not isinstance(state, dict) or state.get('phase') != 'b1' or state.get('status') != 'STOPPED' or
            state.get('stop_reason') != EXPECTED_REASON or state.get('in_progress')):
        raise ValueError('STOP state mismatch')
    completed = state.get('completed')
    expected = {'%s/b1/off/%s__s%d' % (a, n, s) for a in ANCHORS for n in NODES for s in SEEDS}
    if not isinstance(completed, dict) or set(completed) != expected:
        raise ValueError('completed root set differs from STOP capture')
    binding = state.get('binding')
    if not isinstance(binding, str) or not binding: raise ValueError('missing run binding')
    rows = [inspect_root(root, completed, binding, a, n, s) for a in ANCHORS for n in NODES for s in SEEDS]
    return {'source': 'B1-only preserved root manifests and root ledgers, run 6835_20261108_a', 'state_sha256': state_sha,
            'rows': rows, 'summary': summarize(rows), 'stop_changed': False,
            'limitations': 'Descriptive diagnosis; cooperative producer/path provenance; no 7006-7010 file opened; '
                           'no raw per-seed metric vector output. D1 recomputes the gate for diagnosis only.'}


def from_descriptive_capture(path):
    """Local mode: D1 and D3 means from the accepted 24-row descriptive capture."""
    with open(path, 'rb') as f: lines = f.read().decode('utf-8').splitlines()
    docs = [json.loads(l, object_pairs_hook=_unique, parse_constant=_constant) for l in lines if l.startswith('{')]
    if len(docs) != 1 or 'DESCRIPTIVE_CAPTURE_COMPLETE' not in lines: raise ValueError('capture is not one complete descriptive result')
    rows = docs[0]['rows']
    keys = {(r['anchor'], r['node'], r['instance_seed']) for r in rows}
    if len(rows) != 24 or keys != {(a, n, s) for a in ('random_valid', 'scripted') for n in NODES for s in SEEDS}:
        raise ValueError('capture does not hold the 24 expected rows')
    if any(not _num(r['mean_delta_audit']) for r in rows): raise ValueError('a root has no audited proposal')
    # Each root is one instance, so the root mean equals the instance cluster mean the gate uses.
    first = [{'instance_id': '%s__s%d' % (r['node'], r['instance_seed']), 'value': r['mean_delta_audit']} for r in rows if r['anchor'] == 'scripted']
    second = [{'instance_id': '%s__s%d' % (r['node'], r['instance_seed']), 'value': r['mean_delta_audit']} for r in rows if r['anchor'] == 'random_valid']
    gate = paired_instance_bootstrap(first, second)
    std_first = [dict(x, value=x['value']/SIGMA_JOINT[x['instance_id'].rsplit('__', 1)[0]]) for x in first]
    std_second = [dict(x, value=x['value']/SIGMA_JOINT[x['instance_id'].rsplit('__', 1)[0]]) for x in second]
    per_node = {}
    for anchor in ('random_valid', 'scripted'):
        for node in NODES:
            ms = [r['mean_delta_audit'] for r in rows if r['anchor'] == anchor and r['node'] == node]
            n = [r['audited_proposals'] for r in rows if r['anchor'] == anchor and r['node'] == node]
            m = _mean(ms)
            per_node[anchor + '/' + node] = {'mean_of_instance_means': m, 'audited_proposals': sum(n),
                                             'over_sigma_joint': m/SIGMA_JOINT[node]}
    return {'source': path, 'D1_gate_recomputed': gate, 'D1_reproduces_stop': gate['difference_lower'] <= 0,
            'D1_sigma_joint_standardised_for_information': paired_instance_bootstrap(std_first, std_second),
            'D3_means_by_node': per_node, 'stop_changed': False,
            'not_available_from_capture': ['D0', 'D2 keeps and incumbent gain', 'D3 median and harmful share', 'D4', 'D7', 'D8']}


def main(argv):
    try:
        if len(argv) == 3 and argv[1] == '--descriptive-capture':
            print(json.dumps(from_descriptive_capture(argv[2]), sort_keys=True, allow_nan=False, indent=1))
            return 0
        result = inspect(ROOT)
        result['observed_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        print('DIAGNOSIS_CAPTURE_COMPLETE')
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, UnicodeError) as exc:
        print('STOP: diagnosis refused: ' + type(exc).__name__ + ': ' + str(exc)[:200], file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
