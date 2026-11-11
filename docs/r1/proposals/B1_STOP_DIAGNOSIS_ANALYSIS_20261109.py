"""B1 STOP diagnosis analysis: capture JSON -> plan section 3 tables and a class verdict per hypothesis.

Input: the experiment agent's capture of B1_STOP_DIAGNOSIS_20261109.py (host mode), i.e. the
ssh.log holding one JSON line, ``DIAGNOSIS_CAPTURE_COMPLETE`` and the wrapper's ``SSH_EXIT=0``.
Output (stdout): a Markdown report body with the D0-D8 tables and a JSON block with the verdicts.
A capture with a missing, partial or internally inconsistent field is refused (exit 1, nothing
on stdout); nothing is guessed.

Provenance of the rules. They were fixed on 9 Nov 2026 before the diagnosis capture existed and
were tested against synthetic data only. The accepted descriptive capture of 8 Nov (24 per-root
mean delta_audit values for random_valid and scripted, which are sufficient for the D1 point and
the H1/H3 inputs) already existed. Its published ranges (random_valid about -0.0166..+0.0148,
scripted about -0.0028..+0.0013 per root) were known when Z_SMALL, Z_DROP and COUNT_RATIO were
chosen; its paired values were not read. The rules are a reading aid for the diagnosis report,
not a gate: they change no STOP, no criterion and no pin, and the report's independent reviewer
may overrule them with reasons.

Standardisation: each per-instance or per-node value is divided by the node's sigma_joint
from the D21 noise floor (constants in the diagnosis script). "z" below means such a value.

Rules (plan section 2 hypotheses; section 4 classes):

H4 engineering - SUPPORTED if any of: a D0 counter is non-zero; D1 does not reproduce the
  recorded STOP (or cannot be recomputed); a software-anchor root has zero audited proposals;
  a software-anchor root did not end with termination 'worker_cap' and exactly W = 20 worker
  runs (software anchors run with a proposal budget of 1,000,000, so only the worker cap can end
  them); a qwen root with termination 'worker_cap' has worker_runs != W. UNDETERMINED (flag) if
  an anchor x node has invalid / trials > 0.5. Otherwise NOT SUPPORTED.
H1 design (two random proposers that cannot be ordered) - SUPPORTED if the D1 point
  difference (scripted - random_valid) is <= 0, or if the mean standardised per-instance
  difference is < Z_SMALL and fewer than all three nodes have a positive node mean.
  NOT SUPPORTED otherwise.
H2 metric (mean incumbent-relative increment not monotone in quality) - SUPPORTED if, for
  either software anchor, the pooled standardised mean of the second half of each root's
  audited sequence is below the first half by more than Z_DROP (reason kind 'increment_drop'),
  or if the audited-proposal counts of the two anchors differ by a factor > COUNT_RATIO on at
  least two nodes (reason kind 'count_ratio'; reported separately, because count differences
  also follow from the two proposal laws alone). NOT SUPPORTED otherwise.
H3 power - SUPPORTED if the D1 point difference is > 0, all three node means of the
  standardised difference are > 0 and the D1 lower bound is <= 0. NOT SUPPORTED otherwise.

Class (plan section 4): E if H4 is SUPPORTED; else REVIEW (to the author: a possible
engineering defect is flagged but not shown) if H4 is UNDETERMINED; else D if H1 or H2 is
SUPPORTED; else P if H3 is SUPPORTED; else UNCLASSIFIED (to the author).

D7 is reported separately, exactly as the next gate computes it: PASS if the 7B duplicate rate
lies inside the pinned interval (unrounded bounds from the jobs), FAIL otherwise (including no
evaluated 7B proposal). A D7 FAIL goes to the author (plan section 4).

R4 under the author's line A1 (PLAN row R1-EXAM-B1-ANCHOR-R4, branch mac-b1-r4-20261109):
applicable only if the class is D with H1 SUPPORTED and D7 is PASS. A class D resting on H2
alone, class P, REVIEW, UNCLASSIFIED and any D7 FAIL go to the author (``needs_author``).
"""
import json
import math
import sys

Z_SMALL = 0.10      # sigma_joint units
Z_DROP = 0.25       # sigma_joint units
COUNT_RATIO = 1.5
W = 20
ANCHORS = ('random_valid', 'scripted', 'qwen25_coder_7b')
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
SEEDS = (9001, 9002, 9003, 9004)
SOFTWARE = ('scripted', 'random_valid')
COUNTS = ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed')
D0_COUNTERS = ('k_not_4', 'none_in_vectors', 'delta_mismatch')
SUMMARY_FIELDS = ('mean', 'median', 'share_harmful', 'mean_over_sigma_joint', 'median_over_sigma_joint',
                  'mean_over_median_sd_delta')
TOL = 1e-12
# Constants of the diagnosis script (B1_STOP_DIAGNOSIS_20261109.py, SHA-256 82140eea...92f93), repeated
# here so the analysis recomputes rather than trusts the capture (review B1_DIAG_REVIEW_20261109.md
# round 2, note N1). D21 noise floor: docs/r1/reports/NOISE_FLOOR_COMMON_20261022.md (commit 511c3797,
# SHA-256 9be292b7...c01d), Table 1. 7B duplicate-rate reference: r1/scripts/configs/exam_b1_v2.json at
# 68357d3d, source docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json (SHA-256 84200770...85dd).
SIGMA_JOINT = {'digits_mlp': 0.0102, 'openml_credit_approval': 0.0279, 'openml_ionosphere': 0.0410}
MEDIAN_SD_DELTA = {'digits_mlp': 0.0066, 'openml_credit_approval': 0.0030, 'openml_ionosphere': 0.0160}
DUP_REF_PINNED = {'source': 'docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json',
                  'sha256': '84200770e9b63fdd8593085ac171d5893f214c8911f65582a030749507fc85dd',
                  'lower': 0.42386590667728663, 'upper': 0.5800007633587785}


def load_capture(path):
    with open(path, 'rb') as f:
        lines = f.read().decode('utf-8').splitlines()
    if 'DIAGNOSIS_CAPTURE_COMPLETE' not in lines:
        raise ValueError('capture lacks DIAGNOSIS_CAPTURE_COMPLETE')
    if [l for l in lines if l.startswith('SSH_EXIT=')] != ['SSH_EXIT=0']:
        raise ValueError('capture lacks exactly one SSH_EXIT=0 line')
    docs = [l for l in lines if l.startswith('{')]
    if len(docs) != 1:
        raise ValueError('capture must hold exactly one JSON line')
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out: raise ValueError('duplicate JSON key')
            out[k] = v
        return out
    def nonfinite(_): raise ValueError('non-finite JSON number')
    doc = json.loads(docs[0], object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(doc, dict) or doc.get('stop_changed') is not False or 'summary' not in doc or 'rows' not in doc:
        raise ValueError('not a diagnosis capture')
    return doc


def _fin(x):
    return type(x) in (int, float) and math.isfinite(x)


def _count(x):
    return type(x) is int and x >= 0


def _need(cond, what):
    if not cond: raise ValueError('capture field missing or invalid: ' + what)


def _mean(xs):
    return math.fsum(xs) / len(xs) if xs else None


def _median(xs):
    s = sorted(xs); n = len(s)
    if not n: return None
    return s[n//2] if n % 2 else (s[n//2-1]+s[n//2])/2


def _summary(deltas, node):
    """As the diagnosis script's _summary."""
    m, med = _mean(deltas), _median(deltas)
    return {'n': len(deltas), 'mean': m, 'median': med,
            'share_harmful': (sum(d < 0 for d in deltas)/len(deltas)) if deltas else None,
            'mean_over_sigma_joint': None if m is None else m/SIGMA_JOINT[node],
            'median_over_sigma_joint': None if med is None else med/SIGMA_JOINT[node],
            'mean_over_median_sd_delta': None if m is None else m/MEDIAN_SD_DELTA[node]}


def _same_summary(got, exp, what):
    """N1: a D3/D4/D8 summary must equal the one recomputed from the rows (TOL)."""
    _need(got['n'] == exp['n'], f'{what}.n differs from rows')
    for f in SUMMARY_FIELDS:
        a, b = got[f], exp[f]
        _need((a is None and b is None) or (a is not None and b is not None and abs(a - b) <= TOL), f'{what}.{f} differs from rows')


def _check_summary(d, what):
    _need(isinstance(d, dict) and _count(d.get('n')) and all(f in d for f in SUMMARY_FIELDS), what)
    for f in SUMMARY_FIELDS:
        _need(d[f] is None if d['n'] == 0 else _fin(d[f]), f'{what}.{f}')


def validate(doc):
    """Refuse (ValueError) unless every field the tables and verdicts read is present, typed
    and consistent with the 36 rows; recompute D1 per-instance means, D2 audited counts and D7
    from the rows; recompute the standardised D1 values, D3/D4/D8 summaries and check the D7
    reference against the pinned constant (review note N1). Missing values are allowed only where a software root has zero audited
    proposals (then D1 cannot be recomputed; that is an H4 reason, not a guess)."""
    rows, s = doc['rows'], doc['summary']
    _need(isinstance(rows, list) and len(rows) == 36, 'rows (exactly 36)')
    by = {}
    for r in rows:
        _need(isinstance(r, dict), 'row')
        key = (r.get('anchor'), r.get('node'), r.get('instance_seed'))
        _need(key not in by, 'unique rows'); by[key] = r
        _need(r.get('instance_id') == '%s__s%s' % (key[1], key[2]), 'row instance_id')
        _need(isinstance(r.get('termination'), str) and _count(r.get('worker_runs')), 'row termination/worker_runs')
        _need(isinstance(r.get('diagnostics'), dict) and all(_count(r['diagnostics'].get(c)) for c in COUNTS), 'row diagnostics')
        _need(isinstance(r.get('d0'), dict) and all(_count(r['d0'].get(c)) for c in D0_COUNTERS), 'row d0')
        ps = r.get('proposals')
        _need(isinstance(ps, list) and all(isinstance(p, dict) and _count(p.get('budget_index')) and _fin(p.get('delta_audit'))
                                           for p in ps), 'row proposals')
        # The D4 half-split relies on each root's audited sequence being in budget order (review round 1, note 10).
        _need(all(ps[k]['budget_index'] < ps[k + 1]['budget_index'] for k in range(len(ps) - 1)),
              'row proposals in budget-index order')
    _need(set(by) == {(a, n, sd) for a in ANCHORS for n in NODES for sd in SEEDS}, 'rows (anchor, node, seed) set')
    _need(isinstance(s, dict), 'summary')
    empty = {(a, n, sd) for (a, n, sd), r in by.items() if a in SOFTWARE and not r['proposals']}
    # D1
    _need('D1_gate_recomputed' in s and 'D1_reproduces_stop' in s, 'D1')
    g = s['D1_gate_recomputed']
    if g is None:
        _need(empty and isinstance(s.get('D1_error'), str) and s['D1_reproduces_stop'] is None,
              'D1_gate_recomputed (null without an empty software root)')
    else:
        _need(isinstance(g, dict) and all(_fin(g.get(k)) for k in ('difference_point', 'difference_lower', 'difference_upper')),
              'D1_gate_recomputed point/lower/upper')
        _need(type(s['D1_reproduces_stop']) is bool and s['D1_reproduces_stop'] == (g['difference_lower'] <= 0), 'D1_reproduces_stop')
    per = s.get('D1_per_instance')
    _need(isinstance(per, list) and len(per) == 12, 'D1_per_instance (12 entries)')
    diffs = []
    for p in per:
        _need(isinstance(p, dict) and p.get('node') in NODES and isinstance(p.get('instance_id'), str), 'D1_per_instance entry')
        n, seed = p['node'], p['instance_id'].rsplit('__s', 1)[-1]
        _need(seed.isdigit() and int(seed) in SEEDS and p['instance_id'] == '%s__s%s' % (n, seed), 'D1_per_instance id')
        seed = int(seed)
        ms = _mean([q['delta_audit'] for q in by[('scripted', n, seed)]['proposals']])
        mr = _mean([q['delta_audit'] for q in by[('random_valid', n, seed)]['proposals']])
        if ms is None or mr is None:
            _need(p.get('difference') is None and p.get('difference_over_sigma_joint') is None, 'D1_per_instance empty root')
            continue
        _need(all(_fin(p.get(k)) for k in ('scripted_mean', 'random_valid_mean', 'difference', 'difference_over_sigma_joint')),
              'D1_per_instance values')
        _need(abs(p['scripted_mean'] - ms) <= TOL and abs(p['random_valid_mean'] - mr) <= TOL and
              abs(p['difference'] - (ms - mr)) <= TOL, 'D1_per_instance differs from rows')
        # N1 (1): the standardised difference is recomputed with the pinned sigma_joint.
        _need(abs(p['difference_over_sigma_joint'] - (ms - mr) / SIGMA_JOINT[n]) <= TOL,
              'D1_per_instance z differs from rows / sigma_joint')
        diffs.append(ms - mr)
    _need(len({p['instance_id'] for p in per}) == 12, 'D1_per_instance unique ids')
    if g is not None:
        _need(len(diffs) == 12 and abs(g['difference_point'] - _mean(diffs)) <= TOL, 'D1 point differs from rows')
    # D2 / D3 / D4 / D7 / D8
    d2, d3, d4, d8 = s.get('D2'), s.get('D3'), s.get('D4'), s.get('D8_information_only')
    keys = {f'{a}/{n}' for a in ANCHORS for n in NODES}
    _need(isinstance(d2, dict) and set(d2) == keys, 'D2 (9 keys)')
    _need(isinstance(d4, dict) and set(d4) == keys, 'D4 (9 keys)')
    _need(isinstance(d3, dict) and set(d3) == {f'{a}/{n}' for a in SOFTWARE for n in NODES}, 'D3 (6 keys)')
    _need(isinstance(d8, dict) and set(d8) == {f'qwen25_coder_7b/{n}' for n in NODES}, 'D8 (3 keys)')
    for k, d in d2.items():
        a, n = k.split('/')
        rs = [by[(a, n, sd)] for sd in SEEDS]
        _need(isinstance(d, dict) and all(_count(d.get(c)) for c in COUNTS + ('audited', 'keeps_including_first', 'skipped')), f'D2 {k} counts')
        _need(isinstance(d.get('d0'), dict) and all(_count(d['d0'].get(c)) for c in D0_COUNTERS), f'D2 {k} d0')
        _need(isinstance(d.get('worker_runs'), list) and isinstance(d.get('termination'), list), f'D2 {k} worker_runs/termination')
        _need(d.get('mean_gain_after_first_keep') is None or _fin(d.get('mean_gain_after_first_keep')), f'D2 {k} gain')
        _need(d['audited'] == sum(len(r['proposals']) for r in rs), f'D2 {k} audited differs from rows')
        _need(all(d[c] == sum(r['diagnostics'][c] for r in rs) for c in COUNTS), f'D2 {k} counts differ from rows')
        _need(all(d['d0'][c] == sum(r['d0'][c] for r in rs) for c in D0_COUNTERS), f'D2 {k} d0 differs from rows')
    for k, d in list(d3.items()) + list(d8.items()):
        _check_summary(d, f'D3/D8 {k}')
        a, n = k.split('/')
        # N1 (2): D3 and D8 recomputed from the rows.
        _same_summary(d, _summary([q['delta_audit'] for sd in SEEDS for q in by[(a, n, sd)]['proposals']], n), f'D3/D8 {k}')
    for k, d in d4.items():
        _need(isinstance(d, dict), f'D4 {k}')
        for h in ('first_half_of_audited', 'second_half_of_audited', 'budget_index_le_10', 'budget_index_gt_10'):
            _check_summary(d.get(h), f'D4 {k}.{h}')
        # N1 (2): D4 recomputed from the rows (halves of each root's audited sequence; budget split at W/2).
        a, n = k.split('/')
        first, second, early, late = [], [], [], []
        for sd in SEEDS:
            ps = by[(a, n, sd)]['proposals']; h = (len(ps) + 1) // 2
            first += [q['delta_audit'] for q in ps[:h]]; second += [q['delta_audit'] for q in ps[h:]]
            early += [q['delta_audit'] for q in ps if q['budget_index'] <= W // 2]
            late += [q['delta_audit'] for q in ps if q['budget_index'] > W // 2]
        for h, xs in (('first_half_of_audited', first), ('second_half_of_audited', second),
                      ('budget_index_le_10', early), ('budget_index_gt_10', late)):
            _same_summary(d[h], _summary(xs, n), f'D4 {k}.{h}')
    d7 = s.get('D7')
    _need(isinstance(d7, dict) and _count(d7.get('duplicates')) and _count(d7.get('evaluated')), 'D7 counts')
    ref = d7.get('reference')
    _need(isinstance(ref, dict) and type(ref.get('lower')) is float and type(ref.get('upper')) is float, 'D7 reference bounds')
    # N1 (3): the reference must be exactly the pinned constant (bounds, source and SHA-256).
    _need(all(ref.get(k) == v for k, v in DUP_REF_PINNED.items()), 'D7 reference differs from the pinned constant')
    q = [by[('qwen25_coder_7b', n, sd)] for n in NODES for sd in SEEDS]
    _need(d7['duplicates'] == sum(r['diagnostics']['duplicates'] for r in q) and
          d7['evaluated'] == sum(r['diagnostics']['evaluated'] for r in q), 'D7 differs from rows')
    if d7['evaluated'] == 0:
        _need(d7.get('rate') is None and d7.get('inside') is None, 'D7 rate/inside with zero evaluated')
    else:
        _need(_fin(d7.get('rate')) and abs(d7['rate'] - d7['duplicates'] / d7['evaluated']) <= TOL and
              d7.get('inside') is (ref['lower'] <= d7['rate'] <= ref['upper']), 'D7 rate/inside')
    return doc


def _fmt(x, nd=4):
    if x is None: return 'n/a'
    if isinstance(x, bool): return 'yes' if x else 'no'
    if isinstance(x, int): return str(x)
    return f'{x:+.{nd}f}' if isinstance(x, float) else str(x)


def verdicts(doc):
    validate(doc)
    s = doc['summary']; rows = doc['rows']
    gate = s['D1_gate_recomputed']
    point = None if gate is None else gate['difference_point']
    lower = None if gate is None else gate['difference_lower']
    per = s['D1_per_instance']
    zs = [p['difference_over_sigma_joint'] for p in per if p['difference_over_sigma_joint'] is not None]
    mean_z = sum(zs) / len(zs) if zs else None
    node_z = {}
    for n in NODES:
        v = [p['difference_over_sigma_joint'] for p in per if p['node'] == n and p['difference_over_sigma_joint'] is not None]
        node_z[n] = sum(v) / len(v) if v else None
    positive_nodes = sum(1 for v in node_z.values() if v is not None and v > 0)

    # H4
    h4_reasons = []
    for k, d in s['D2'].items():
        if any(d['d0'][c] for c in D0_COUNTERS): h4_reasons.append(f'D0 counter non-zero in {k}: {d["d0"]}')
    if gate is None: h4_reasons.append('D1 cannot be recomputed: ' + s['D1_error'])
    elif s['D1_reproduces_stop'] is not True: h4_reasons.append('D1 does not reproduce the recorded STOP')
    for r in rows:
        where = f'{r["anchor"]}/{r["instance_id"]}'
        if r['anchor'] in SOFTWARE:
            if not r['proposals']: h4_reasons.append(f'no audited proposal in {where}')
            if r['termination'] != 'worker_cap' or r['worker_runs'] != W:
                h4_reasons.append(f'software anchor ended {r["termination"]} with worker_runs={r["worker_runs"]} (expected worker_cap, {W}) in {where}')
        elif r['termination'] == 'worker_cap' and r['worker_runs'] != W:
            h4_reasons.append(f'worker_cap with worker_runs={r["worker_runs"]} in {where}')
    flags = [f'{k}: invalid {d["invalid"]}/{d["trials"]}' for k, d in s['D2'].items()
             if d['trials'] and d['invalid'] / d['trials'] > 0.5]
    h4 = 'SUPPORTED' if h4_reasons else ('UNDETERMINED' if flags else 'NOT SUPPORTED')

    # H1
    h1_point = point is not None and point <= 0
    h1_small = mean_z is not None and mean_z < Z_SMALL and positive_nodes < 3
    h1 = 'SUPPORTED' if (h1_point or h1_small) else 'NOT SUPPORTED'
    h1_reasons = (['D1 point <= 0'] if h1_point else []) + \
                 ([f'mean z {mean_z:.3f} < {Z_SMALL} with {positive_nodes} positive node(s)'] if h1_small else [])

    # H2
    h2_reasons = []
    for a in SOFTWARE:
        f_num = f_den = s_num = s_den = 0.0
        for n in NODES:
            d4 = s['D4'][f'{a}/{n}']
            f, l = d4['first_half_of_audited'], d4['second_half_of_audited']
            if f['n']:
                f_num += f['mean_over_sigma_joint'] * f['n']; f_den += f['n']
            if l['n']:
                s_num += l['mean_over_sigma_joint'] * l['n']; s_den += l['n']
        if f_den and s_den and (f_num / f_den) - (s_num / s_den) > Z_DROP:
            h2_reasons.append({'kind': 'increment_drop', 'text': f'{a}: second-half z mean below first half by {(f_num / f_den) - (s_num / s_den):.3f}'})
    ratio_nodes = []
    for n in NODES:
        a_, b_ = s['D2'][f'scripted/{n}']['audited'], s['D2'][f'random_valid/{n}']['audited']
        if min(a_, b_) == 0 or max(a_, b_) / min(a_, b_) > COUNT_RATIO: ratio_nodes.append(f'{n} ({a_} vs {b_})')
    if len(ratio_nodes) >= 2:
        h2_reasons.append({'kind': 'count_ratio', 'text': 'audited counts differ by > %.1fx on %s' % (COUNT_RATIO, ', '.join(ratio_nodes))})
    h2 = 'SUPPORTED' if h2_reasons else 'NOT SUPPORTED'

    # H3
    h3_sup = (point is not None and point > 0 and positive_nodes == 3 and lower is not None and lower <= 0)
    h3 = 'SUPPORTED' if h3_sup else 'NOT SUPPORTED'

    if h4 == 'SUPPORTED': cls = 'E'
    elif h4 == 'UNDETERMINED': cls = 'REVIEW'
    elif h1 == 'SUPPORTED' or h2 == 'SUPPORTED': cls = 'D'
    elif h3 == 'SUPPORTED': cls = 'P'
    else: cls = 'UNCLASSIFIED'
    d7 = s['D7']
    d7_pass = d7['inside'] is True
    needs_author = []
    if not d7_pass:
        needs_author.append('D7 FAIL: 7B duplicate rate ' + ('undefined (no evaluated 7B proposal)' if d7['rate'] is None
                            else 'outside the pinned interval') + ' (plan section 4)')
    if cls == 'REVIEW': needs_author.append('H4 UNDETERMINED: possible engineering defect flagged, not shown')
    if cls == 'D' and h1 != 'SUPPORTED': needs_author.append('class D rests on H2 alone; not covered by line A1 (PLAN R1-EXAM-B1-ANCHOR-R4)')
    if cls == 'P': needs_author.append('class P changes the criterion after seeing data (plan section 4)')
    if cls == 'UNCLASSIFIED': needs_author.append('no class rule fired (plan section 4)')
    return {'H1': h1, 'H2': h2, 'H3': h3, 'H4': h4, 'class': cls,
            'D7': 'PASS' if d7_pass else 'FAIL',
            'evidence': {'d1_point': point, 'd1_lower': lower, 'mean_z_difference': mean_z,
                         'node_mean_z_difference': node_z, 'positive_nodes': positive_nodes,
                         'h4_reasons': h4_reasons, 'h4_flags': flags, 'h1_reasons': h1_reasons, 'h2_reasons': h2_reasons},
            'r4_applicable_under_A1': cls == 'D' and h1 == 'SUPPORTED' and d7_pass,
            'needs_author': needs_author,
            'thresholds': {'Z_SMALL': Z_SMALL, 'Z_DROP': Z_DROP, 'COUNT_RATIO': COUNT_RATIO},
            'rules_fixed_before_diagnosis_capture': True,
            'descriptive_capture_known': 'ranges only (per-root mean ranges published 8 Nov; paired values not read)'}


def tables(doc):
    s = doc['summary']; out = []
    g = s['D1_gate_recomputed'] or {}
    out.append('### D1 - gate recomputed (scripted - random_valid, 12 instance pairs)\n')
    out.append('| point | lower | upper | reproduces STOP |\n|---|---|---|---|')
    out.append(f"| {_fmt(g.get('difference_point'))} | {_fmt(g.get('difference_lower'))} | {_fmt(g.get('difference_upper'))} | {_fmt(s['D1_reproduces_stop'])} |\n")
    if s['D1_gate_recomputed'] is None: out.append(f"D1 could not be recomputed: {s['D1_error']}\n")
    out.append('| instance | scripted mean | random_valid mean | difference | difference / sigma_joint |\n|---|---|---|---|---|')
    for p in s['D1_per_instance']:
        out.append(f"| {p['instance_id']} | {_fmt(p.get('scripted_mean'))} | {_fmt(p.get('random_valid_mean'))} | {_fmt(p['difference'])} | {_fmt(p['difference_over_sigma_joint'], 3)} |")
    out.append('\n### D0/D2 - counts per anchor x node (4 roots each)\n')
    out.append('"in-run gain" = mean over roots of the final kept record\'s in-run metric minus the first valid '
               'trial\'s (the harness keeps the first valid trial unconditionally; no unedited start metric exists). '
               '"skipped" = ledger rows rejected before any worker run (e.g. inactive categorical draws); they use a '
               'budget index but no worker run and are never audited.\n')
    out.append('| anchor/node | trials | evaluated | invalid | duplicates | no-ops | parse failed | skipped | audited | keeps (incl. first) | in-run gain after first keep | worker runs | termination | D0 (k!=4, None, mismatch) |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for k, d in s['D2'].items():
        d0 = d['d0']
        out.append(f"| {k} | {d['trials']} | {d['evaluated']} | {d['invalid']} | {d['duplicates']} | {d['noops']} | {d['parse_failed']} | {d['skipped']} | {d['audited']} | {d['keeps_including_first']} | {_fmt(d['mean_gain_after_first_keep'])} | {','.join(str(x) for x in d['worker_runs'])} | {','.join(str(x) for x in d['termination'])} | {d0['k_not_4']}, {d0['none_in_vectors']}, {d0['delta_mismatch']} |")
    out.append('\n### D3 - delta_audit per anchor x node\n')
    out.append('| anchor/node | n | mean | median | share harmful | mean / sigma_joint | median / sigma_joint | mean / median sd(delta) |\n|---|---|---|---|---|---|---|---|')
    for k, d in list(s['D3'].items()) + list(s['D8_information_only'].items()):
        tag = ' (D8, information only)' if k.startswith('qwen25') else ''
        out.append(f"| {k}{tag} | {d['n']} | {_fmt(d['mean'])} | {_fmt(d['median'])} | {_fmt(d['share_harmful'], 3)} | {_fmt(d['mean_over_sigma_joint'], 3)} | {_fmt(d['median_over_sigma_joint'], 3)} | {_fmt(d['mean_over_median_sd_delta'], 3)} |")
    out.append('\n### D4 - first vs second half of each root\'s audited sequence (and budget index <= 10 / > 10)\n')
    out.append('| anchor/node | first half mean (n) | second half mean (n) | b<=10 mean (n) | b>10 mean (n) |\n|---|---|---|---|---|')
    for k, d in s['D4'].items():
        c = lambda x: f"{_fmt(x['mean'])} ({x['n']})"
        out.append(f"| {k} | {c(d['first_half_of_audited'])} | {c(d['second_half_of_audited'])} | {c(d['budget_index_le_10'])} | {c(d['budget_index_gt_10'])} |")
    d7 = s['D7']; ref = d7['reference']
    out.append('\n### D7 - 7B duplicate rate (the next gate)\n')
    out.append('| duplicates | evaluated | rate | pinned interval (unrounded, from the jobs) | inside |\n|---|---|---|---|---|')
    out.append(f"| {d7['duplicates']} | {d7['evaluated']} | {'n/a' if d7['rate'] is None else repr(d7['rate'])} | [{ref['lower']!r}, {ref['upper']!r}] | {_fmt(d7['inside'])} |")
    return '\n'.join(out)


def main(argv):
    if len(argv) != 2:
        print('usage: B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <capture ssh.log>', file=sys.stderr); return 2
    try:
        doc = load_capture(argv[1])
        v = verdicts(doc)
        body = tables(doc)
        verdict = json.dumps(v, indent=1, sort_keys=True, allow_nan=False)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError) as exc:
        print('analysis refused: ' + type(exc).__name__ + ': ' + str(exc)[:200], file=sys.stderr); return 1
    print(body)
    print('\n### Verdicts (pre-declared rules; see module docstring)\n')
    print('```json\n' + verdict + '\n```')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
