"""STOP 6: render the Track X B2 report draft from the verified B2 outputs.

ENGINEERING tool; AI-assisted (Claude, Mac agent). Reads only files, recomputes every number it prints from the
B2 manifests, and refuses (``ReportError``, message starting ``STOP:``) when the inputs disagree. It never chooses
anything: X.7 stays the author's decision.

Inputs (formats of ``mac-b2-code-20261114`` @ ``a2cd540c``):

* ``analysis.json``: the stdout of ``python -m r1.exam.analyze b2 --batch <batch> --config <cfg> --rule ...``
  (``_b2_summary_v2`` plus ``execution_label`` and ``batch_verification``);
* ``b2_manifests.json``: the batch aggregate ``{'label': 'EXAM', 'manifests': [...]}`` (one manifest per finalist);
* ``invalid_trials.json``: schema ``b2_invalid_trials/v1``, written by the ``derive-invalid`` subcommand below from
  the batch's roots (per candidate, mode, node and instance; the classes of R1-EXAM-B1-TRUNCATION-INVALID and
  R1-EXAM-B1-MODEL-OUTPUT-INVALID, extended to B2 by R1-EXAM-B2-INVALID-TRIALS);
* ``b1_analysis``: the frozen B1 complete-batch analysis (``complete_batch_verifier.json``) whose sha256 the B2
  analysis binds. The scripted anchor ran only in B1, so its mu_hat comes from there.

Usage:
  python r1/scripts/b2_stop6_report.py derive-invalid --batch <b2 batch dir> --analysis analysis.json --out invalid_trials.json
  python r1/scripts/b2_stop6_report.py render --analysis analysis.json --manifests b2_manifests.json \
      --invalid-trials invalid_trials.json --b1-analysis complete_batch_verifier.json --out PROPOSER_EXAM_<date>.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from scipy import stats

SCHEMA_INVALID = 'b2_invalid_trials/v1'
B2_AUDIT_SEEDS = list(range(9201, 9211))
CLASS_ORDER = ('truncated', 'context_overflow', 'unencodable_reply')   # then model_output:<check>, then other_invalid


class ReportError(ValueError):
    pass


def _stop(msg):
    raise ReportError(f'STOP: {msg}')


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        _stop(f'cannot read {path}: {exc}')


def _rows(path):
    out = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _num(x):
    return type(x) in (int, float) and math.isfinite(x)


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


# --------------------------------------------------------------------------------------------- invalid trials

def classify_root(records, journal):
    """Invalid trials of one root, by class.

    A trial is invalid when its ledger decision is ``failed_invalid``. Its class is read from the last journal row of
    the trial (as ``validate_proposal_journal`` does): a model-output rejection gives ``model_output:<check>``;
    otherwise a truncated, context-overflow or unencodable reply gives that class; anything else (a harness parse or
    precondition failure, or a trial without a journal row) is ``other_invalid``."""
    last = {}
    for row in journal:
        last[row.get('trial_id')] = row
    classes = Counter()
    invalid = 0
    for r in records:
        if r.get('decision') != 'failed_invalid':
            continue
        invalid += 1
        row = last.get(r.get('trial_id'))
        if row is not None and row.get('check') == 'rejected':
            classes[f"model_output:{(row.get('rejection') or {}).get('check')}"] += 1
        elif row is not None and row.get('truncated'):
            classes['truncated'] += 1
        elif row is not None and row.get('context_overflow'):
            classes['context_overflow'] += 1
        elif row is not None and row.get('unencodable_reply'):
            classes['unencodable_reply'] += 1
        else:
            classes['other_invalid'] += 1
    return invalid, dict(sorted(classes.items()))


def derive_invalid(batch, analysis_path):
    """Build ``invalid_trials.json`` from the roots of a B2 batch, for exactly the verified grid of the analysis."""
    batch = Path(batch)
    analysis = _read_json(analysis_path)
    grid = (analysis.get('batch_verification') or {}).get('grid') or {}
    if grid.get('verified') is not True:
        _stop('analysis has no verified grid')
    if sha256_file(batch / 'b2_manifests.json') != analysis['batch_verification'].get('batch_manifests_sha256'):
        _stop('b2_manifests.json of the batch is not the one the analysis verified')
    rows = []
    for cid in grid['finalists']:
        for mode in grid['modes'][cid]:
            for node in grid['nodes']:
                for seed in grid['seeds']:
                    root = batch / cid / 'b2' / mode / f'{node}__s{seed}'
                    manifest = _read_json(root / 'campaign_manifest.json')
                    records = _rows(root / 'root_trials.jsonl')
                    journal = _rows(root / 'b1_proposals.jsonl')
                    invalid, classes = classify_root(records, journal)
                    diag = manifest.get('diagnostics') or {}
                    if invalid != diag.get('invalid') or len(records) != diag.get('trials'):
                        _stop(f'{cid}/{mode}/{node}__s{seed}: invalid or trial count differs from the root diagnostics')
                    rejected = {k[len('model_output:'):]: v for k, v in classes.items() if k.startswith('model_output:')}
                    if rejected != dict((manifest.get('proposal_journal') or {}).get('rejected_by_check') or {}):
                        _stop(f'{cid}/{mode}/{node}__s{seed}: model-output rejections differ from the root journal summary')
                    rows.append({'candidate': cid, 'mode': mode, 'node': node, 'instance_id': f'{node}__s{seed}',
                                 'trials': len(records), 'invalid': invalid, 'classes': classes,
                                 'llm_calls': (manifest.get('compute_budget') or {}).get('llm_calls')})
    return {'schema': SCHEMA_INVALID, 'label': 'EXAM', 'phase': 'b2',
            'batch_manifests_sha256': analysis['batch_verification']['batch_manifests_sha256'], 'rows': rows}


# ------------------------------------------------------------------------------------------- input checks

def _final_y(record):
    if record.get('seeds') != B2_AUDIT_SEEDS or len(record.get('metrics') or []) != 10 or \
            not all(_num(v) for v in record['metrics']):
        _stop('final-Y audit is not ten finite metrics on seeds 9201–9210')
    value = sum(record['metrics']) / 10
    if not _num(record.get('final_y')) or not math.isclose(value, record['final_y'], rel_tol=0.0, abs_tol=1e-12):
        _stop('final_y differs from the mean of its ten audits')
    return value


def load_and_check(analysis_path, manifests_path, invalid_path, b1_path):
    analysis = _read_json(analysis_path)
    if analysis.get('phase') != 'b2' or analysis.get('label') != 'EXAM' or analysis.get('execution_label') != 'EVIDENCE':
        _stop('analysis is not an EVIDENCE B2 analysis')
    if analysis.get('rule_version') != 'x5_rule/v2' or analysis.get('author_decision_pending') is not True:
        _stop('analysis is not an x5_rule/v2 ranking pending the author')
    proof = analysis.get('batch_verification') or {}
    grid = proof.get('grid') or {}
    if grid.get('verified') is not True:
        _stop('analysis grid is not verified')
    if sha256_file(manifests_path) != proof.get('batch_manifests_sha256'):
        _stop('b2_manifests.json is not the file the analysis verified (sha256 differs)')
    data = _read_json(manifests_path)
    manifests = data.get('manifests') if isinstance(data, dict) and data.get('label') == 'EXAM' else None
    if not isinstance(manifests, list) or [m.get('candidate') for m in manifests] != list(grid['finalists']):
        _stop('manifests differ from the verified finalists')
    if sha256_file(b1_path) != proof.get('b1_analysis_sha256'):
        _stop('B1 analysis is not the file the B2 analysis binds (sha256 differs)')
    b1 = _read_json(b1_path)
    if b1.get('phase') != 'b1' or b1.get('execution_label') != 'EVIDENCE' or b1.get('rule_sha256') != analysis.get('rule_sha256'):
        _stop('B1 analysis is not the x5_rule/v2 EVIDENCE analysis')
    if list(b1.get('finalists') or []) != list(grid['finalists']):
        _stop('B1 finalists differ from the B2 grid finalists')
    invalid = _read_json(invalid_path)
    if invalid.get('schema') != SCHEMA_INVALID or invalid.get('phase') != 'b2' or \
            invalid.get('batch_manifests_sha256') != proof.get('batch_manifests_sha256'):
        _stop('invalid_trials.json is not a b2_invalid_trials/v1 file for this batch')
    expected = [(c, mode, n, f'{n}__s{s}') for c in grid['finalists'] for mode in grid['modes'][c]
                for n in grid['nodes'] for s in grid['seeds']]
    got = [(r.get('candidate'), r.get('mode'), r.get('node'), r.get('instance_id')) for r in invalid.get('rows') or []]
    if sorted(got) != sorted(expected) or len(got) != len(set(got)):
        _stop('invalid_trials.json rows do not cover exactly the verified grid')
    for r in invalid['rows']:
        cl = r.get('classes') or {}
        if not all(type(v) is int and v >= 0 for v in cl.values()) or sum(cl.values()) != r.get('invalid'):
            _stop(f"invalid classes of {r['candidate']}/{r['mode']}/{r['instance_id']} do not add up")
    for m in manifests:
        mine = [r for r in invalid['rows'] if r['candidate'] == m['candidate']]
        diag = m.get('diagnostics') or {}
        if sum(r['invalid'] for r in mine) != diag.get('invalid') or sum(r['trials'] for r in mine) != diag.get('trials'):
            _stop(f"invalid_trials.json totals of {m['candidate']} differ from its manifest diagnostics")
    # the analysis rows must be what the manifests give
    by_c = {m['candidate']: m for m in manifests}
    rows = analysis.get('rows') or []
    if sorted(r['candidate'] for r in rows) != sorted(grid['finalists']):
        _stop('analysis rows differ from the finalists')
    cells = len(grid['nodes']) * int(grid['instances_per_node'])
    for r in rows:
        m = by_c[r['candidate']]
        ys = [_final_y(a) for a in m.get('final_audits') or []]
        if len(ys) != cells or r.get('instances') != cells:
            _stop(f"{r['candidate']}: final audits do not cover the grid")
        if not math.isclose(_mean(ys), r['final_y'], rel_tol=0.0, abs_tol=1e-12):
            _stop(f"{r['candidate']}: analysis final_y differs from its manifest")
        g = grid.get('gpu_hours', {}).get(r['candidate'])
        if not _num(g) or not math.isclose(g, r.get('gpu_hours'), rel_tol=0.0, abs_tol=1e-9) or m.get('gpu_hours') != r.get('gpu_hours'):
            _stop(f"{r['candidate']}: GPU-h differs between analysis, grid and manifest")
    ranked = sorted(rows, key=lambda r: (-r['final_y'], r['gpu_hours']))
    if [r['candidate'] for r in ranked] != [r['candidate'] for r in rows] or \
            (analysis.get('selection') or {}).get('rule_top') != (rows[0]['candidate'] if rows else None):
        _stop('analysis ranking or rule_top differs from final Y with the GPU-h tie-break')
    # descriptive thinking-on rows must be the manifests' rerun audits
    desc = {}
    for m in manifests:
        rerun = m.get('sensitivity_final_audits') or []
        if rerun:
            if len(rerun) != cells or {(a.get('node'), a.get('instance_id')) for a in rerun} != \
                    {(n, f'{n}__s{s}') for n in grid['nodes'] for s in grid['seeds']}:
                _stop(f"{m['candidate']}: thinking-on rerun audits do not cover the grid")
            desc[m['candidate']] = (_mean(_final_y(a) for a in rerun), len(rerun))
        if bool(rerun) != (len(grid['modes'][m['candidate']]) > 1):
            _stop(f"{m['candidate']}: thinking-on rerun presence differs from the grid modes")
    listed = analysis.get('thinking_on_descriptive') or []
    if any(d.get('source') != 'top3_thinking_on_rerun' or d.get('mode') != 'on' for d in listed) or \
            sorted(d.get('candidate') for d in listed) != sorted(desc) or \
            any(d.get('instances') != desc[d['candidate']][1] or not _num(d.get('final_y')) or
                not math.isclose(d['final_y'], desc[d['candidate']][0], rel_tol=0.0, abs_tol=1e-12) for d in listed):
        _stop('analysis thinking-on descriptive rows differ from the manifests')
    if analysis.get('schema_sensitivity_rows'):
        _stop('schema-free sensitivity rows present; this template does not render them')
    return analysis, manifests, invalid, b1


# ------------------------------------------------------------------------------------------- statistics

def t_interval(xs):
    n = len(xs)
    m = _mean(xs)
    if n < 2:
        return m, None, None, n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
    return m, m - h, m + h, n


def cluster_bootstrap(rows, rule, field='delta_audit'):
    """B2 mu_hat with exactly the B1 mu_hat method: ``r1.exam.analyze.bootstrap_mean`` (node-instance clusters, the
    frozen rule's bootstrap seed and resamples). Descriptive here; B2 ranks by final Y."""
    from r1.exam.analyze import bootstrap_mean
    if not rows:
        return None
    if not all(_num(r.get(field)) for r in rows):
        _stop('non-finite audited increment')
    b = bootstrap_mean(rows, field=field, rule=rule)
    return {**b, 'proposals': len(rows)}


def load_rule_for(analysis):
    """The frozen rule bytes of this checkout, checked against the analysis's rule sha256."""
    from r1.exam.analyze import load_rule
    path = Path(__file__).resolve().parents[1] / 'exam' / 'rules' / 'x5_rule_v2.yaml'
    try:
        rule, _ = load_rule(path, analysis['rule_sha256'])
    except ValueError as exc:
        _stop(f'rule file differs from the analysis rule sha256 ({exc})')
    return rule


# ------------------------------------------------------------------------------------------- rendering

def f(x, nd=6):
    return '—' if x is None else f'{x:+.{nd}f}'


def y(x, nd=6):
    return '—' if x is None else f'{x:.{nd}f}'


def _invalid_classes(rows):
    total = Counter()
    for r in rows:
        total.update(r['classes'])
    model = sorted(k for k in total if k.startswith('model_output:'))
    order = [k for k in CLASS_ORDER if k in total] + model + (['other_invalid'] if 'other_invalid' in total else [])
    return order, total


def render(analysis, manifests, invalid, b1, *, sources):
    grid = analysis['batch_verification']['grid']
    proof = analysis['batch_verification']
    nodes, finalists = grid['nodes'], grid['finalists']
    by_c = {m['candidate']: m for m in manifests}
    b1_rows = {r['candidate']: r for r in b1['rows']}
    rule = load_rule_for(analysis)
    L = []
    w = L.append
    w('# Track X B2 report draft (STOP 6)')
    w('')
    w('**AI-assisted (rendered by `r1/scripts/b2_stop6_report.py`). A draft for the review loop of STOP 6: the reviewer '
      'recomputes every table from the manifests. Not an author decision; X.7 is decided by the author.**')
    w('')
    w('## 0. Inputs')
    w('')
    w('| Input | sha256 |')
    w('|---|---|')
    for k, (p, s) in sources.items():
        w(f'| {k} (`{Path(p).name}`) | `{s}` |')
    w('')
    w(f"- Batch state sha256 `{proof.get('batch_state_sha256')}`; run HEAD `{proof.get('authorization_checkout_head')}`; "
      f"rule `{analysis['rule_version']}` sha256 `{analysis['rule_sha256']}`.")
    w(f"- Verified grid: nodes {', '.join(f'`{n}`' for n in nodes)}; instance seeds {grid['seeds'][0]}–{grid['seeds'][-1]} "
      f"({grid['instances_per_node']} per node); final-Y audit seeds {grid['audit_seeds'][0]}–{grid['audit_seeds'][-1]}.")
    w('')
    w('## 1. Finalist and rule pick')
    w('')
    top = analysis['selection']['rule_top']
    w(f"- Finalists (frozen B1, STOP 5): {', '.join(f'`{c}`' for c in finalists)}.")
    w(f"- x5_rule/v2 pick for X.7 (a), best B2 final audited Y with ties to lower GPU-h: **`{top}`**.")
    if len(finalists) == 1:
        w(f'- With a single finalist, `{top}` is the rule pick whatever its B2 score. No other finalist exists, so the B2 '
          'scores order nothing and there is no second proposer among the finalists.')
    w('')
    w('## 2. B2 final audited Y (thinking off; the ranking quantity)')
    w('')
    w('Final Y of a root = mean of the ten audit metrics of its final incumbent (seeds 9201–9210). 95 % intervals: '
      'Student t over instances; descriptive.')
    w('')
    w('| Candidate | Node | n | mean final Y | 95 % CI |')
    w('|---|---|---|---|---|')
    for c in finalists:
        fa = by_c[c]['final_audits']
        for n in nodes:
            m, lo, hi, k = t_interval([_final_y(a) for a in fa if a['node'] == n])
            w(f'| `{c}` | `{n}` | {k} | {y(m)} | [{y(lo)}, {y(hi)}] |')
        m, lo, hi, k = t_interval([_final_y(a) for a in fa])
        w(f'| `{c}` | all nodes | {k} | {y(m)} | (pooled; not used by the rule) |')
    w('')
    w('| Rank | Candidate | final Y (rule quantity) | GPU-h (verified server intervals) |')
    w('|---|---|---|---|')
    for i, r in enumerate(analysis['rows'], 1):
        w(f"| {i} | `{r['candidate']}` | {y(r['final_y'])} | {r['gpu_hours']:.3f} |")
    w('')
    w('## 3. Audited mean increment μ̂ and the scripted anchor')
    w('')
    s = b1_rows.get('scripted')
    if s is None or s.get('role') != 'anchor':
        _stop('B1 analysis has no scripted anchor row')
    w('**B1 (frozen analysis; instances 9001–9004, audit seeds 9101–9104).** The scripted anchor ran only in B1.')
    w('')
    w('| Row | Role | μ̂ (B1) | 95 % cluster interval | D28 |')
    w('|---|---|---|---|---|')
    for c in ['scripted'] + list(finalists):
        r = b1_rows.get(c)
        if r is None:
            _stop(f'B1 analysis has no row for {c}')
        ci = r.get('cluster_interval') or {}
        w(f"| `{c}` | {r.get('role')} | {f(r.get('mu_hat'))} | [{f(ci.get('lower'))}, {f(ci.get('upper'))}] | "
          f"{'pass' if r.get('d28_pass') else 'fail'} |")
    w('')
    for c in finalists:
        d = b1_rows[c]['mu_hat'] - s['mu_hat']
        w(f"- `{c}` μ̂ − scripted μ̂ (B1, point difference, descriptive; not a rule quantity): {f(d)} "
          f"({'below' if d < 0 else 'at or above'} the scripted anchor).")
    w('')
    w('**B2 (this batch; finalists only; thinking off).** Mean `delta_audit` of the audited proposals (seeds 9201–9210), '
      'with the same node-instance cluster bootstrap as B1 μ̂ (`analyze.bootstrap_mean`, the frozen rule\'s seed and '
      'resamples). Descriptive: B2 ranks by final Y. No anchor ran in B2, '
      'so these values have no B2 anchor to compare with, and B1 and B2 μ̂ come from different instances and audit seeds.')
    w('')
    w('| Candidate | Node | audited proposals | μ̂ (B2) | 95 % cluster interval |')
    w('|---|---|---|---|---|')
    for c in finalists:
        ap = [a for a in by_c[c].get('audited_proposals') or [] if a.get('mode') == 'off']
        for n in nodes + ['all nodes']:
            sub = ap if n == 'all nodes' else [a for a in ap if a['node'] == n]
            b = cluster_bootstrap(sub, rule)
            if b is None:
                w(f'| `{c}` | `{n}` | 0 | — | — |')
            else:
                w(f"| `{c}` | {'`' + n + '`' if n != 'all nodes' else n} | {b['proposals']} | {f(b['mean'])} | "
                  f"[{f(b['lower'])}, {f(b['upper'])}] |")
    w('')
    w('## 4. D28 (novelty) status')
    w('')
    w('| Candidate | B2 thinking off (decides eligibility; scope) | B2 thinking-on rerun (descriptive) | B1 D28 |')
    w('|---|---|---|---|')
    for c in finalists:
        m = by_c[c]
        on = m.get('thinking_on_d28')
        on_s = '—' if on is None else f"{'pass' if on.get('pass') else 'fail'} ({on.get('roots')} roots; {on.get('role')})"
        w(f"| `{c}` | {'pass' if m.get('d28_pass') else 'fail'} (`{m.get('d28_scope')}`) | {on_s} | "
          f"{'pass' if b1_rows[c].get('d28_pass') else 'fail'} |")
    w('')
    w('## 5. Invalid trials (charged to the LLM-call budget; the campaign continues)')
    w('')
    w('Classes: R1-EXAM-B1-TRUNCATION-INVALID (truncated reply; context overflow past trial 1), '
      'R1-EXAM-B1-MODEL-OUTPUT-INVALID (unencodable reply; model-output check `model_output:<check>`), extended to B2 by '
      'R1-EXAM-B2-INVALID-TRIALS; `other_invalid` = any other `failed_invalid` trial (harness parse or precondition failure).')
    w('')
    order, _ = _invalid_classes(invalid['rows'])
    w('| Candidate | Mode | Trials | Invalid | ' + ' | '.join(f'`{k}`' for k in order) + ' |')
    w('|---|---|---|---|' + '---|' * len(order))
    for c in finalists:
        for mode in grid['modes'][c]:
            rows = [r for r in invalid['rows'] if r['candidate'] == c and r['mode'] == mode]
            _, tot = _invalid_classes(rows)
            w(f"| `{c}` | {mode} | {sum(r['trials'] for r in rows)} | {sum(r['invalid'] for r in rows)} | "
              + ' | '.join(str(tot.get(k, 0)) for k in order) + ' |')
    w('')
    w('Per node (thinking off):')
    w('')
    w('| Candidate | Node | Trials | Invalid | LLM calls |')
    w('|---|---|---|---|---|')
    for c in finalists:
        for n in nodes:
            rows = [r for r in invalid['rows'] if r['candidate'] == c and r['mode'] == 'off' and r['node'] == n]
            calls = [r.get('llm_calls') for r in rows]
            w(f"| `{c}` | `{n}` | {sum(r['trials'] for r in rows)} | {sum(r['invalid'] for r in rows)} | "
              f"{sum(calls) if all(type(x) is int for x in calls) else '—'} |")
    w('')
    w('## 6. Thinking-on rerun (descriptive only; never enters the ranking)')
    w('')
    desc = [d for d in analysis.get('thinking_on_descriptive') or [] if d.get('source') == 'top3_thinking_on_rerun']
    if not desc:
        w('No thinking-on rerun in this batch.')
    else:
        w('| Candidate | Node | n | mean final Y (thinking on) | 95 % CI | thinking off, same node |')
        w('|---|---|---|---|---|---|')
        for d in desc:
            m = by_c[d['candidate']]
            for n in nodes:
                on = [_final_y(a) for a in m['sensitivity_final_audits'] if a['node'] == n]
                off = [_final_y(a) for a in m['final_audits'] if a['node'] == n]
                mo, lo, hi, k = t_interval(on)
                w(f"| `{d['candidate']}` | `{n}` | {k} | {y(mo)} | [{y(lo)}, {y(hi)}] | {y(_mean(off))} |")
            w(f"| `{d['candidate']}` | all nodes | {d['instances']} | {y(d['final_y'])} | (label `{d.get('label')}`) | "
              f"{y(_mean(_final_y(a) for a in m['final_audits']))} |")
    w('')
    w('## 7. Other diagnostics (all roots of the candidate, both modes)')
    w('')
    keys = ('trials', 'evaluated', 'invalid', 'duplicates', 'noops', 'parse_failed', 'forecast_queries', 'forecast_query_failed')
    w('| Candidate | ' + ' | '.join(keys) + ' |')
    w('|---|' + '---|' * len(keys))
    for c in finalists:
        dg = by_c[c].get('diagnostics') or {}
        w(f'| `{c}` | ' + ' | '.join(str(dg.get(k, '—')) for k in keys) + ' |')
    w('')
    w('## 8. For the author (X.7; not decided here)')
    w('')
    w('- (a) D22 strong proposer: the rule pick above.')
    w('- (b) B.6 second manager: chosen among the finalists by proposal distribution against `qwen2.5-coder:7b`.')
    if len(finalists) == 1:
        w('  With one finalist there is no other finalist to choose; the author decides how B.6 proceeds.')
    w('- (c) Appendix: C3 premises against proposer strength.')
    w('')
    return '\n'.join(L) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('derive-invalid')
    d.add_argument('--batch', required=True); d.add_argument('--analysis', required=True); d.add_argument('--out', required=True)
    r = sub.add_parser('render')
    for k in ('--analysis', '--manifests', '--invalid-trials', '--b1-analysis', '--out'):
        r.add_argument(k, required=True)
    a = p.parse_args(argv)
    if a.cmd == 'derive-invalid':
        out = derive_invalid(a.batch, a.analysis)
        Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
        return
    analysis, manifests, invalid, b1 = load_and_check(a.analysis, a.manifests, a.invalid_trials, a.b1_analysis)
    sources = {'analysis.json': (a.analysis, sha256_file(a.analysis)), 'b2_manifests.json': (a.manifests, sha256_file(a.manifests)),
               'invalid_trials.json': (a.invalid_trials, sha256_file(a.invalid_trials)),
               'B1 analysis': (a.b1_analysis, sha256_file(a.b1_analysis))}
    Path(a.out).write_text(render(analysis, manifests, invalid, b1, sources=sources), encoding='utf-8')


if __name__ == '__main__':
    main()
