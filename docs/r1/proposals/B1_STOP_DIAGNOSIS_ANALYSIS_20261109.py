"""B1 STOP diagnosis analysis: capture JSON -> plan section 3 tables and a class verdict per hypothesis.

Input: the experiment agent's capture of B1_STOP_DIAGNOSIS_20261109.py (host mode), i.e. the
ssh.log holding one JSON line followed by ``DIAGNOSIS_CAPTURE_COMPLETE``. Output (stdout):
a Markdown report body with the D0-D8 tables and a JSON block with the verdicts.

The verdict rules below were fixed on 9 Nov 2026 BEFORE any capture existed (the analysis
was written and reviewed against synthetic data only). They are a pre-declared reading aid
for the diagnosis report, not a gate: they change no STOP, no criterion and no pin, and the
report's independent reviewer may overrule them with reasons.

Standardisation: each per-instance or per-node value is divided by the node's sigma_joint
from the D21 noise floor (constants in the diagnosis script). "z" below means such a value.

Rules (plan section 2 hypotheses; section 4 classes):

H4 engineering - SUPPORTED if any of: a D0 counter is non-zero; D1 does not reproduce the
  recorded STOP; a root has zero audited proposals; a root with termination 'worker_cap' has
  worker_runs != W. UNDETERMINED (flag) if an anchor x node has invalid / trials > 0.5.
  Otherwise NOT SUPPORTED.
H1 design (two random proposers that cannot be ordered) - SUPPORTED if the D1 point
  difference (scripted - random_valid) is <= 0, or if the mean standardised per-instance
  difference is < Z_SMALL and fewer than all three nodes have a positive node mean.
  NOT SUPPORTED otherwise.
H2 metric (mean incumbent-relative increment not monotone in quality) - SUPPORTED if, for
  either software anchor, the pooled standardised mean of the second half of each root's
  audited sequence is below the first half by more than Z_DROP, or if the audited-proposal
  counts of the two anchors differ by a factor > COUNT_RATIO on at least two nodes.
  NOT SUPPORTED otherwise.
H3 power - SUPPORTED if the D1 point difference is > 0, all three node means of the
  standardised difference are > 0 and the D1 lower bound is <= 0. NOT SUPPORTED otherwise.

Class (plan section 4): E if H4 is SUPPORTED; else D if H1 or H2 is SUPPORTED; else P if H3
is SUPPORTED; else UNCLASSIFIED (to the author). D7 is reported separately: PASS if the 7B
duplicate rate lies inside the pinned interval, FAIL otherwise. Under the author's A1 line,
R4 applies only when the class is D.
"""
import json
import math
import sys

Z_SMALL = 0.10      # sigma_joint units
Z_DROP = 0.25       # sigma_joint units
COUNT_RATIO = 1.5
W = 20
NODES = ('digits_mlp', 'openml_credit_approval', 'openml_ionosphere')
SOFTWARE = ('scripted', 'random_valid')


def load_capture(path):
    with open(path, 'rb') as f:
        lines = f.read().decode('utf-8').splitlines()
    if 'DIAGNOSIS_CAPTURE_COMPLETE' not in lines:
        raise ValueError('capture lacks DIAGNOSIS_CAPTURE_COMPLETE')
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
    if doc.get('stop_changed') is not False or 'summary' not in doc or 'rows' not in doc:
        raise ValueError('not a diagnosis capture')
    return doc


def _fmt(x, nd=4):
    if x is None: return 'n/a'
    if isinstance(x, bool): return 'yes' if x else 'no'
    if isinstance(x, int): return str(x)
    return f'{x:+.{nd}f}' if isinstance(x, float) else str(x)


def verdicts(doc):
    s = doc['summary']; rows = doc['rows']
    gate = s.get('D1_gate_recomputed') or {}
    point, lower = gate.get('difference_point'), gate.get('difference_lower')
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
        if any(d['d0'][c] for c in d['d0']): h4_reasons.append(f'D0 counter non-zero in {k}: {d["d0"]}')
    if s.get('D1_reproduces_stop') is not True: h4_reasons.append('D1 does not reproduce the recorded STOP')
    for r in rows:
        if r['anchor'] in SOFTWARE and not r['proposals']:
            h4_reasons.append(f'no audited proposal in {r["anchor"]}/{r["instance_id"]}')
        if r.get('termination') == 'worker_cap' and r.get('worker_runs') != W:
            h4_reasons.append(f'worker_cap with worker_runs={r.get("worker_runs")} in {r["anchor"]}/{r["instance_id"]}')
    flags = [f'{k}: invalid {d["invalid"]}/{d["trials"]}' for k, d in s['D2'].items()
             if d['trials'] and d['invalid'] / d['trials'] > 0.5]
    h4 = 'SUPPORTED' if h4_reasons else ('UNDETERMINED' if flags else 'NOT SUPPORTED')

    # H1
    h1_sup = (point is not None and point <= 0) or (mean_z is not None and mean_z < Z_SMALL and positive_nodes < 3)
    h1 = 'SUPPORTED' if h1_sup else 'NOT SUPPORTED'

    # H2
    h2_reasons = []
    for a in SOFTWARE:
        f_num = f_den = s_num = s_den = 0.0
        for n in NODES:
            d4 = s['D4'][f'{a}/{n}']
            f, l = d4['first_half_of_audited'], d4['second_half_of_audited']
            if f['n'] and f['mean_over_sigma_joint'] is not None:
                f_num += f['mean_over_sigma_joint'] * f['n']; f_den += f['n']
            if l['n'] and l['mean_over_sigma_joint'] is not None:
                s_num += l['mean_over_sigma_joint'] * l['n']; s_den += l['n']
        if f_den and s_den and (f_num / f_den) - (s_num / s_den) > Z_DROP:
            h2_reasons.append(f'{a}: second-half z mean below first half by {(f_num / f_den) - (s_num / s_den):.3f}')
    ratio_nodes = []
    for n in NODES:
        a_, b_ = s['D2'][f'scripted/{n}']['audited'], s['D2'][f'random_valid/{n}']['audited']
        if min(a_, b_) == 0 or max(a_, b_) / min(a_, b_) > COUNT_RATIO: ratio_nodes.append(f'{n} ({a_} vs {b_})')
    if len(ratio_nodes) >= 2: h2_reasons.append('audited counts differ by > %.1fx on %s' % (COUNT_RATIO, ', '.join(ratio_nodes)))
    h2 = 'SUPPORTED' if h2_reasons else 'NOT SUPPORTED'

    # H3
    h3_sup = (point is not None and point > 0 and positive_nodes == 3 and lower is not None and lower <= 0)
    h3 = 'SUPPORTED' if h3_sup else 'NOT SUPPORTED'

    if h4 == 'SUPPORTED': cls = 'E'
    elif h1 == 'SUPPORTED' or h2 == 'SUPPORTED': cls = 'D'
    elif h3 == 'SUPPORTED': cls = 'P'
    else: cls = 'UNCLASSIFIED'
    d7 = s['D7']
    return {'H1': h1, 'H2': h2, 'H3': h3, 'H4': h4, 'class': cls,
            'D7': 'PASS' if d7.get('inside') is True else 'FAIL',
            'evidence': {'d1_point': point, 'd1_lower': lower, 'mean_z_difference': mean_z,
                         'node_mean_z_difference': node_z, 'positive_nodes': positive_nodes,
                         'h4_reasons': h4_reasons, 'h4_flags': flags, 'h2_reasons': h2_reasons},
            'r4_applicable_under_A1': cls == 'D',
            'thresholds': {'Z_SMALL': Z_SMALL, 'Z_DROP': Z_DROP, 'COUNT_RATIO': COUNT_RATIO},
            'rules_fixed_before_capture': True}


def tables(doc):
    s = doc['summary']; out = []
    g = s.get('D1_gate_recomputed') or {}
    out.append('### D1 - gate recomputed (scripted - random_valid, 12 instance pairs)\n')
    out.append('| point | lower | upper | reproduces STOP |\n|---|---|---|---|')
    out.append(f"| {_fmt(g.get('difference_point'))} | {_fmt(g.get('difference_lower'))} | {_fmt(g.get('difference_upper'))} | {_fmt(s.get('D1_reproduces_stop'))} |\n")
    out.append('| instance | scripted mean | random_valid mean | difference | difference / sigma_joint |\n|---|---|---|---|---|')
    for p in s['D1_per_instance']:
        out.append(f"| {p['instance_id']} | {_fmt(p['scripted_mean'])} | {_fmt(p['random_valid_mean'])} | {_fmt(p['difference'])} | {_fmt(p['difference_over_sigma_joint'], 3)} |")
    out.append('\n### D0/D2 - counts per anchor x node (4 roots each)\n')
    out.append('| anchor/node | trials | evaluated | invalid | duplicates | no-ops | parse failed | audited | keeps (incl. first) | worker runs | termination | D0 (k!=4, None, mismatch) |\n|---|---|---|---|---|---|---|---|---|---|---|---|')
    for k, d in s['D2'].items():
        d0 = d['d0']
        out.append(f"| {k} | {d['trials']} | {d['evaluated']} | {d['invalid']} | {d['duplicates']} | {d['noops']} | {d['parse_failed']} | {d['audited']} | {d['keeps_including_first']} | {','.join(str(x) for x in d['worker_runs'])} | {','.join(d['termination'])} | {d0['k_not_4']}, {d0['none_in_vectors']}, {d0['delta_mismatch']} |")
    out.append('\n### D3 - delta_audit per anchor x node\n')
    out.append('| anchor/node | n | mean | median | share harmful | mean / sigma_joint | mean / median sd(delta) |\n|---|---|---|---|---|---|---|')
    for k, d in list(s['D3'].items()) + list(s['D8_information_only'].items()):
        tag = ' (D8, information only)' if k.startswith('qwen25') else ''
        out.append(f"| {k}{tag} | {d['n']} | {_fmt(d['mean'])} | {_fmt(d['median'])} | {_fmt(d['share_harmful'], 3)} | {_fmt(d['mean_over_sigma_joint'], 3)} | {_fmt(d['mean_over_median_sd_delta'], 3)} |")
    out.append('\n### D4 - first vs second half of each root\'s audited sequence (and budget index <= 10 / > 10)\n')
    out.append('| anchor/node | first half mean (n) | second half mean (n) | b<=10 mean (n) | b>10 mean (n) |\n|---|---|---|---|---|')
    for k, d in s['D4'].items():
        c = lambda x: f"{_fmt(x['mean'])} ({x['n']})"
        out.append(f"| {k} | {c(d['first_half_of_audited'])} | {c(d['second_half_of_audited'])} | {c(d['budget_index_le_10'])} | {c(d['budget_index_gt_10'])} |")
    d7 = s['D7']
    out.append('\n### D7 - 7B duplicate rate (the next gate)\n')
    out.append('| duplicates | evaluated | rate | pinned interval | inside |\n|---|---|---|---|---|')
    out.append(f"| {d7['duplicates']} | {d7['evaluated']} | {_fmt(d7['rate'])} | [{d7['reference'][0]}, {d7['reference'][1]}] | {_fmt(d7['inside'])} |")
    return '\n'.join(out)


def main(argv):
    if len(argv) != 2:
        print('usage: B1_STOP_DIAGNOSIS_ANALYSIS_20261109.py <capture ssh.log>', file=sys.stderr); return 2
    try:
        doc = load_capture(argv[1])
        v = verdicts(doc)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('analysis refused: ' + type(exc).__name__ + ': ' + str(exc)[:200], file=sys.stderr); return 1
    print(tables(doc))
    print('\n### Verdicts (pre-declared rules; see module docstring)\n')
    print('```json\n' + json.dumps(v, indent=1, sort_keys=True, allow_nan=False) + '\n```')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
