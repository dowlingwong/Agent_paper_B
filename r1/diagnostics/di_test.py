"""AI-assisted (Codex), PILOT, not evidence. File-only E1b DI diagnostics.

No harness imports, execution, network, LLM or GPU. Inputs are Git HEAD blobs,
not mutable working-tree results. Output paths must not overwrite inputs/results.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np

SEED = 20261019
DRAWS = 9999
METRICS = ('mean_delta', 'positive_fraction', 'key_tv', 'signed_log_edit',
           'active_novelty', 'duplicate_fraction', 'metric_identical')
HORIZONS = (1, 3, 'all')


class CommittedInputs:
    def __init__(self, run):
        run = Path(run).resolve()
        self.repo = Path(subprocess.check_output(
            ['git', '-C', str(run), 'rev-parse', '--show-toplevel'], text=True).strip())
        self.run = run.relative_to(self.repo).as_posix()
        self.revision = subprocess.check_output(
            ['git', '-C', str(self.repo), 'rev-parse', 'HEAD'], text=True).strip()
        self.hashes = {}
        self.cache = {}

    def text(self, relative):
        path = f'{self.run}/{relative}'
        if path not in self.cache:
            data = subprocess.check_output(['git', '-C', str(self.repo), 'show',
                                            f'{self.revision}:{path}'])
            self.hashes[path] = hashlib.sha256(data).hexdigest()
            self.cache[path] = data.decode()
        return self.cache[path]

    def paths(self):
        if not hasattr(self, '_paths'):
            self._paths = subprocess.check_output(
                ['git', '-C', str(self.repo), 'ls-tree', '-r', '--name-only',
                 self.revision, '--', self.run], text=True).splitlines()
        return self._paths

    def ledger(self, relative):
        path = f'{self.run}/{relative}'
        if path in self.paths():
            return self.rows(relative)
        path += '.gz'
        data = subprocess.check_output(['git', '-C', str(self.repo), 'show',
                                       f'{self.revision}:{path}'])
        self.hashes[path] = hashlib.sha256(data).hexdigest()
        raw = gzip.decompress(data)
        self.hashes[path + ' (decompressed)'] = hashlib.sha256(raw).hexdigest()
        return [json.loads(line) for line in raw.splitlines() if line.strip()]

    def json(self, relative):
        return json.loads(self.text(relative))

    def rows(self, relative):
        return [json.loads(s) for s in self.text(relative).splitlines() if s.strip()]


def scalar(value):
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return None if value.lower() in ('null', 'none') else value


def configuration(files):
    result = {}
    for name, text in files.items():
        # Historical start_files serialize literal newline escapes; snapshots do not.
        if '\n' not in text and '\\n' in text:
            text = text.replace('\\n', '\n')
        if name.endswith('.py'):
            for statement in ast.parse(text).body:
                if isinstance(statement, ast.Assign):
                    for target in statement.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            result[target.id] = ast.literal_eval(statement.value)
        elif name.endswith('.yaml'):
            for line in text.splitlines():
                if ':' in line and not line.lstrip().startswith('#'):
                    key, value = line.split(':', 1)
                    result[key.strip()] = scalar(value.strip())
    if not result:
        raise ValueError('No replayable configuration')
    return result


def project(config, node):
    if node in ('digits_mlp', 'tabular_mlp'):
        keys = set(config)
    elif node in ('openml_ionosphere', 'openml_breast_w'):
        # Numeric-only dataset; imputer is inactive. Mirrors D25 projection.
        model = config['model_type']
        keys = {'model_type', 'scaler'} | {
            'logistic_regression': {'C', 'max_iter', 'class_weight'},
            'random_forest': {'n_estimators', 'max_depth', 'class_weight'},
            'gradient_boosting': {'n_estimators', 'max_depth', 'learning_rate'},
        }[model]
    else:
        raise ValueError(f'Undeclared active-key projection: {node}')
    return json.dumps({k: config[k] for k in sorted(keys)}, sort_keys=True)


def replay(rows, start, node, point, snapshot_incumbent, absolute=False):
    """Replay prefix for seen history, then anchor the branch to its E2 snapshot."""
    current = dict(start)
    seen = set()
    output = []
    for row in rows:
        index = row['budget_index']
        if index == point:
            if current != snapshot_incumbent:
                raise ValueError('Replayed prefix differs from snapshot incumbent')
            current = dict(snapshot_incumbent)
        if row['decision'] == 'skipped' or (absolute and parsed_metric(row) is None):
            continue
        edit = row['extra']['manager'].get('structured_edit')
        if not edit or edit['symbol'] not in current:
            raise ValueError('Missing/unknown structured edit')
        key = edit['symbol']
        if scalar(edit['old']) != current[key]:
            raise ValueError(f'Stale edit old value at {row["trial_id"]}: {edit}')
        candidate = dict(current)
        candidate[key] = scalar(edit['new'])
        active, incumbent = project(candidate, node), project(current, node)
        old, new = current[key], candidate[key]
        log_size = (math.log(new / old) if isinstance(old, (float, int))
                    and isinstance(new, (float, int)) and old > 0 and new > 0 else None)
        if index > point:
            delta = row['delta_vs_best']
            if delta is None:
                raise ValueError('Post-point delta missing')
            output.append({'index': index, 'key': key, 'delta': delta,
                           'positive': float(delta > 0), 'log_size': log_size,
                           'novel': float(active != incumbent and active not in seen),
                           'duplicate': float(active in seen),
                           'identical': float(delta == 0)})
            if absolute:
                output[-1]['abs_metric'] = parsed_metric(row)
        seen.add(active)
        if row['decision'] == 'kept':
            current = candidate
    return output


def mean(values):
    values = list(values)
    return float(np.mean(values)) if values else None


def summarize(rows, horizon):
    rows = rows if horizon == 'all' else rows[:horizon]
    if not rows:
        raise ValueError('Empty post-point horizon')
    return {'n': len(rows), 'mean_delta': mean(t['delta'] for t in rows),
            'positive_fraction': mean(t['positive'] for t in rows),
            'keys': {k: v / len(rows) for k, v in Counter(t['key'] for t in rows).items()},
            'signed_log_edit': mean(t['log_size'] for t in rows if t['log_size'] is not None),
            'numeric_edits': sum(t['log_size'] is not None for t in rows),
            'active_novelty': mean(t['novel'] for t in rows),
            'duplicate_fraction': mean(t['duplicate'] for t in rows),
            'metric_identical': mean(t['identical'] for t in rows)}


def distance(left, right, metric):
    if metric == 'key_tv':
        return sum(abs(left['keys'].get(k, 0) - right['keys'].get(k, 0))
                   for k in left['keys'].keys() | right['keys'].keys()) / 2
    if left[metric] is None or right[metric] is None:
        return None
    return abs(left[metric] - right[metric])


def collect(source):
    points = source.json('points.json')
    rows = []
    decisions = []
    branches = []
    for point in points:
        inst, b = point['instance'], point['budget_index']
        node = point['features']['node']
        root = source.json(f'roots/{inst}.json')
        root_rows = source.rows(f'provenance/ledgers/roots/{inst}/root_trials.jsonl')
        start = configuration(root['start_files'])
        base = f'provenance/snapshots/{inst}/E2_b{b:03d}'
        snapshot = source.json(f'{base}/manifest.json')
        incumbent = configuration({p: source.text(f'{base}/incumbent/{p}')
                                   for p in snapshot['editable_paths']})
        seqs, at = {}, {}
        for action in ('continue', 'verify'):
            for rep in (1, 2):
                leaf = f'{inst}__b{b:03d}__{action}__r{rep}'
                path = f'provenance/ledgers/branches/{leaf}'
                ledger = source.rows(f'{path}/branch_trials.jsonl')
                events = source.rows(f'{path}/branch_events.jsonl')
                if [t for t in ledger if t['budget_index'] < b] != root_rows[:b-1]:
                    raise ValueError('Branches do not share the recorded root history')
                if not any(e['event_type'] == 'branch_trial_committed' for e in events):
                    raise ValueError('Branch commitment event absent')
                trial = next(t for t in ledger if t['budget_index'] == b)
                at[action, rep] = trial
                seqs[action, rep] = replay(ledger, start, node, b, incumbent)
        directions = []
        for rep in (1, 2):
            c, v = at['continue', rep], at['verify', rep]
            verify = v['extra']['control']['verify']
            if verify['original_decision'] != c['decision']:
                raise ValueError('Verify original decision differs from continue')
            direction = ('unchanged' if c['decision'] == v['decision'] else
                         'promotion' if v['decision'] == 'kept' else 'demotion')
            directions.append(direction)
            decisions.append({'node': node, 'instance': inst, 'point': b, 'rep': rep,
                              'direction': direction, 'continue': c['decision'],
                              'verify': v['decision'], 'verify_mean_delta': verify['mean_delta']})
        # Keep repetitions together in the point-level inference unit.
        if directions[0] != directions[1]:
            raise ValueError('Mixed decision directions within point require stratified handling')
        for horizon in HORIZONS:
            summaries = {k: summarize(v, horizon) for k, v in seqs.items()}
            for (action, rep), summary in summaries.items():
                branches.append(dict(node=node, instance=inst, point=b, action=action,
                                     rep=rep, horizon=str(horizon), **summary))
            for metric in METRICS:
                cross = [distance(summaries['continue', r], summaries['verify', r], metric)
                         for r in (1, 2)]
                null = [distance(summaries[a, 1], summaries[a, 2], metric)
                        for a in ('continue', 'verify')]
                if any(x is None for x in cross + null):
                    continue
                signed = None if metric == 'key_tv' else mean(
                    summaries['verify', r][metric] - summaries['continue', r][metric]
                    for r in (1, 2))
                rows.append(dict(node=node, instance=inst, point=b, horizon=str(horizon),
                                 metric=metric, changed=directions[0] != 'unchanged',
                                 direction=directions[0], cross=mean(cross), null=mean(null),
                                 signed=signed, sigma_d=point['features']['sigma_d']))
    return decisions, rows, branches


def inference(rows, draws=DRAWS, seed=SEED):
    """Point-label permutation within node; paired instance-cluster bootstrap."""
    changed = np.array([r['changed'] for r in rows], dtype=bool)
    cross = np.array([r['cross'] for r in rows])
    null = np.array([r['null'] for r in rows])
    result = {'points': len(rows), 'changed_points': int(changed.sum()),
              'instances': len({r['instance'] for r in rows}),
              'D_changed': mean(cross[changed]), 'D_unchanged': mean(cross[~changed]),
              'D_null': mean(null), 'D_null_at_changed': mean(null[changed]),
              'signed_changed': mean(r['signed'] for r in rows
                                     if r['changed'] and r['signed'] is not None),
              'reject': False}
    if not changed.any() or changed.all():
        result['unavailable'] = 'Both changed and unchanged points required'
        return result
    effects = np.array([(cross-null)[changed].mean(),
                        cross[changed].mean()-cross[~changed].mean()])
    result['excess_null'], result['excess_unchanged'] = map(float, effects)
    result['excess_null_sigma_d'] = mean((r['cross']-r['null']) / r['sigma_d']
                                        for r in rows if r['changed'])
    result['excess_unchanged_sigma_d'] = (
        mean(r['cross']/r['sigma_d'] for r in rows if r['changed']) -
        mean(r['cross']/r['sigma_d'] for r in rows if not r['changed']))
    if rows[0].get('metric') != 'mean_delta':
        result.pop('excess_null_sigma_d')
        result.pop('excess_unchanged_sigma_d')
    rng = np.random.default_rng(seed)
    perm = np.tile(changed, (draws, 1))
    for node in sorted({r['node'] for r in rows}):
        idx = np.array([i for i, r in enumerate(rows) if r['node'] == node])
        for j in range(draws):
            perm[j, idx] = rng.permutation(changed[idx])
    pnull = (perm @ (cross-null)) / perm.sum(axis=1)
    pother = (perm @ cross) / perm.sum(axis=1) - ((~perm) @ cross) / (~perm).sum(axis=1)
    result['p_null'] = float((1 + (pnull >= effects[0]-1e-14).sum())/(draws+1))
    result['p_unchanged'] = float((1 + (pother >= effects[1]-1e-14).sum())/(draws+1))
    # Preserve all points/repetitions/horizons of a sampled instance together.
    weights = np.zeros((draws, len(rows)))
    for node in sorted({r['node'] for r in rows}):
        instances = sorted({r['instance'] for r in rows if r['node'] == node})
        counts = rng.multinomial(len(instances), np.full(len(instances), 1/len(instances)), draws)
        for i, inst in enumerate(instances):
            weights[:, [j for j, r in enumerate(rows) if r['instance'] == inst]] = counts[:, i, None]
    wc, wu = weights * changed, weights * (~changed)
    valid = (wc.sum(1) > 0) & (wu.sum(1) > 0)
    wc, wu = wc[valid], wu[valid]
    bnull = wc @ (cross-null) / wc.sum(1)
    bother = wc @ cross/wc.sum(1) - wu @ cross/wu.sum(1)
    result['bootstrap_valid'] = int(valid.sum())
    for name, sample in [('null', bnull), ('unchanged', bother)]:
        result[f'ci_{name}'] = [float(x) for x in np.quantile(sample, [.025, .975])]
    result['reject'] = bool(all(effects > 0) and result['p_null'] < .05
                            and result['p_unchanged'] < .05
                            and result['ci_null'][0] > 0 and result['ci_unchanged'][0] > 0)
    return result


def analyze(source, draws=DRAWS):
    decisions, rows, branches = collect(source)
    results = []
    for group in ('digits_mlp', 'openml_ionosphere', 'pooled_value_eligible'):
        for horizon in HORIZONS:
            for metric in METRICS:
                selected = [r for r in rows if r['horizon'] == str(horizon) and r['metric'] == metric
                            and r['node'] == ('digits_mlp' if group == 'pooled_value_eligible' else group)]
                results.append(dict(group=group, horizon=str(horizon), metric=metric,
                                    **inference(selected, draws=draws)))
    counts = {node: dict(Counter(d['direction'] for d in decisions if d['node'] == node))
              for node in sorted({d['node'] for d in decisions})}
    primary = [r for r in results if r['group'] == 'digits_mlp' and r['metric'] in METRICS[:2]]
    # Six exploratory primary tests; Holm control for their intersection-union p values.
    ordered = sorted(primary, key=lambda r: max(r.get('p_null', 1), r.get('p_unchanged', 1)))
    running = 0.
    for i, r in enumerate(ordered):
        running = max(running, min(1., (len(ordered)-i)*max(r.get('p_null', 1), r.get('p_unchanged', 1))))
        r['holm_p'] = running
    for r in results:
        if r['group'] == 'pooled_value_eligible' and r['metric'] in METRICS[:2]:
            r['holm_p'] = next(p['holm_p'] for p in primary if p['horizon'] == r['horizon'] and p['metric'] == r['metric'])
    verdict = ('violated (exploratory memory-off diagnostic)' if any(
        r['reject'] and r['holm_p'] < .05 for r in primary) else 'undetermined at this sample size')
    return dict(label='PILOT; not evidence', author='AI-assisted by Codex', seed=SEED,
                draws=draws, input_revision=source.revision, counts=counts, verdict=verdict,
                decisions=decisions, point_contrasts=rows, branch_summaries=branches,
                results=results, input_sha256=source.hashes)


def fmt(x):
    if x is None:
        return 'NA'
    if isinstance(x, list):
        return '[' + ', '.join(fmt(v) for v in x) + ']'
    return f'{x:.6g}' if isinstance(x, float) else str(x)


def markdown(report):
    lines = ['# E1b DI diagnostic tables', '', 'AI-assisted by Codex. PILOT; not evidence.', '',
             f'Input revision: `{report["input_revision"]}`. Seed {SEED}; {report["draws"]} draws.', '',
             '| Node | Promotions | Demotions | Unchanged |', '|---|---:|---:|---:|']
    for node, c in report['counts'].items():
        lines.append(f'| {node} | {c.get("promotion",0)} | {c.get("demotion",0)} | {c.get("unchanged",0)} |')
    lines += ['', 'All observed changes are promotions.', '',
              '| Group | Horizon | Metric | Changed points | D_changed | D_null (all) | D_null (changed) | D_unchanged | Signed verify − continue (changed) |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in report['results']:
        lines.append('| ' + ' | '.join(fmt(r[k]) for k in ('group','horizon','metric','changed_points','D_changed','D_null','D_null_at_changed','D_unchanged','signed_changed')) + ' |')
    lines += ['', '| Group | Horizon | Metric | Excess over null [95% CI] | Excess over unchanged [95% CI] | p(null) | p(unchanged) | Holm p (6 primary tests) | Excess null / sigma_d | Excess unchanged / sigma_d | Valid bootstrap draws |',
              '|---|---|---|---|---|---:|---:|---:|---:|---:|---:|']
    for r in report['results']:
        if 'excess_null' not in r:
            continue
        values = [r['group'],r['horizon'],r['metric'], f'{fmt(r["excess_null"])} {fmt(r["ci_null"])}',
                  f'{fmt(r["excess_unchanged"])} {fmt(r["ci_unchanged"])}',r['p_null'],r['p_unchanged'],r.get('holm_p'),
                  r['excess_null_sigma_d'] if r['metric']=='mean_delta' else None,
                  r['excess_unchanged_sigma_d'] if r['metric']=='mean_delta' else None,r['bootstrap_valid']]
        lines.append('| ' + ' | '.join(fmt(v) for v in values) + ' |')
    lines += ['', '## Decision audit', '', '| Instance | Point | Rep | Continue | Verify | Direction | Verify mean delta |', '|---|---:|---:|---|---|---|---:|']
    for r in report['decisions']:
        lines.append('| '+' | '.join(fmt(r[k]) for k in ('instance','point','rep','continue','verify','direction','verify_mean_delta'))+' |')
    lines += ['', '## Branch outcome means (equal weight per branch)', '',
              '| Node | Horizon | Action | Branches | Mean trials | Mean delta | Positive fraction | Signed log size | Active novelty | Duplicate fraction | Metric identical |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for node in report['counts']:
        for h in HORIZONS:
            for action in ('continue','verify'):
                bs=[b for b in report['branch_summaries'] if b['node']==node and b['horizon']==str(h) and b['action']==action]
                vals=[node,str(h),action,len(bs)]+[mean(b[k] for b in bs if b[k] is not None) for k in ('n','mean_delta','positive_fraction','signed_log_edit','active_novelty','duplicate_fraction','metric_identical')]
                lines.append('| '+' | '.join(fmt(v) for v in vals)+' |')
    lines += ['', f'Verdict: **{report["verdict"]}**.', '',
              'Ionosphere has no changed points, so its changed-group inference is unavailable. '
              'Pooled eligible results equal digits; ionosphere is excluded. '
              'Only mean-delta effects have meaningful sigma_d units. Numeric edit sizes exclude categorical edits. '
              'NA is unavailable, not zero. See the companion report for estimand and exchangeability limitations.']
    return '\n'.join(lines)+'\n'


def parsed_metric(row):
    metrics = row.get('parsed_metrics') or {}
    value = metrics.get('val_score', metrics.get('val_auc'))
    if value is not None and not math.isfinite(value):
        raise ValueError('Non-finite parsed metric')
    return value


def collect_absolute(source):
    """Both complete DT4 and interrupted compressed layouts; whole-point exclusion."""
    paths = source.paths()
    prefix = source.run + '/'
    manifest = source.json('manifest.json')
    leaves = [source.json(p[len(prefix):]) for p in paths
              if p.startswith(prefix + 'leaves/') and p.endswith('.json')]
    indexed = {}
    for leaf in leaves:
        indexed.setdefault((leaf['instance'], leaf['budget_index']), {})[
            leaf['action'], leaf['repetition']] = leaf
    decisions, contrasts, branches, pairs, excluded = [], [], [], [], []
    expected = {(a, r) for a in ('continue', 'verify') for r in (1, 2)}
    for (inst, b), ls in sorted(indexed.items()):
        bad = [l['leaf_id'] for l in ls.values()
               if l['integrity'] != 'ok' or l.get('error')]
        if bad or set(ls) != expected:
            excluded.append(dict(instance=inst, point=b, failed_leaves=bad,
                                 reason='failed or missing leaf; all four excluded'))
            continue
        node = ls['continue', 1]['node']
        root = source.json(f'roots/{inst}.json')
        root_rows = source.ledger(f'provenance/ledgers/roots/{inst}/root_trials.jsonl')
        start = configuration(root['start_files'])
        base = f'provenance/snapshots/{inst}/E2_b{b:03d}'
        snap = source.json(f'{base}/manifest.json')
        incumbent = configuration({p: source.text(f'{base}/incumbent/{p}')
                                   for p in snap['editable_paths']})
        seqs, at, posts = {}, {}, {}
        for action, rep in sorted(expected):
            leaf = ls[action, rep]
            ledger = source.ledger(f'provenance/ledgers/branches/{leaf["leaf_id"]}/branch_trials.jsonl')
            if [t for t in ledger if t['budget_index'] < b] != root_rows[:b-1]:
                raise ValueError(f'Branches do not share root history: {leaf["leaf_id"]}')
            at[action, rep] = next(t for t in ledger if t['budget_index'] == b)
            posts[action, rep] = [t for t in ledger if t['budget_index'] > b
                                  and t['decision'] != 'skipped' and parsed_metric(t) is not None]
            seqs[action, rep] = replay(ledger, start, node, b, incumbent, absolute=True)
            if len(seqs[action, rep]) < 3:
                raise ValueError(f'Fewer than three evaluated post-point trials: {leaf["leaf_id"]}')
        directions = []
        for rep in (1, 2):
            c, v = at['continue', rep], at['verify', rep]
            verify = v['extra']['control']['verify']
            if verify['original_decision'] != c['decision']:
                raise ValueError('Verify original decision differs from continue')
            direction = ('unchanged' if c['decision'] == v['decision'] else
                         'promotion' if v['decision'] == 'kept' else 'demotion')
            directions.append(direction)
            decisions.append(dict(node=node, instance=inst, point=b, rep=rep,
                                  direction=direction, verify_mean_delta=verify['mean_delta']))
            cp, vp = posts['continue', rep][0], posts['verify', rep][0]
            ys = [ls[a, rep]['audit_metrics'] for a in ('continue', 'verify')]
            if not ys[0] or len(ys[0]) != len(ys[1]):
                raise ValueError('Missing or unpaired audit metrics')
            changed_edit = c['extra']['manager']['structured_edit']
            mechanisms = {}
            for a, post in [('continue', cp), ('verify', vp)]:
                edit = post['extra']['manager']['structured_edit']
                same_key = edit['symbol'] == changed_edit['symbol']
                mechanisms[a + '_repeat'] = bool(same_key and scalar(edit['old']) == scalar(changed_edit['old'])
                                               and scalar(edit['new']) == scalar(changed_edit['new']))
                mechanisms[a + '_reverse'] = bool(same_key and scalar(edit['old']) == scalar(changed_edit['new'])
                                                and scalar(edit['new']) == scalar(changed_edit['old']))
            cm, vm = [p['extra']['manager'].get('worker_memory_context_text') for p in (cp, vp)]
            pairs.append(dict(node=node, instance=inst, point=b, rep=rep, direction=direction,
                              changed=direction != 'unchanged',
                              record_shift=vp['current_best_before'] - cp['current_best_before'],
                              audit_difference=mean(vv-cc for cc, vv in zip(*ys)),
                              immediate=(verify['mean_delta'] if direction == 'promotion' else
                                         -verify['mean_delta'] if direction == 'demotion' else 0.),
                              memory_differs=None if cm is None or vm is None else cm != vm,
                              **mechanisms))
        # Frozen verify response should agree across repeated decoding continuations.
        if len(set(directions)) != 1:
            raise ValueError('Mixed decision directions within point')
        for horizon in (1, 3):
            summaries = {}
            for key, seq in seqs.items():
                summary = summarize(seq, horizon)
                summary['abs_metric'] = mean(t['abs_metric'] for t in seq[:horizon])
                summaries[key] = summary
                branches.append(dict(node=node, instance=inst, point=b, action=key[0],
                                     rep=key[1], horizon=str(horizon), **summary))
            for metric in ('abs_metric',) + METRICS[2:]:
                cross = [distance(summaries['continue', r], summaries['verify', r], metric) for r in (1, 2)]
                null = [distance(summaries[a, 1], summaries[a, 2], metric) for a in ('continue', 'verify')]
                if any(x is None for x in cross + null):
                    continue
                signed = None if metric == 'key_tv' else mean(
                    summaries['verify', r][metric] - summaries['continue', r][metric] for r in (1, 2))
                contrasts.append(dict(node=node, instance=inst, point=b, horizon=str(horizon),
                                      metric=metric, changed=directions[0] != 'unchanged',
                                      direction=directions[0], cross=mean(cross), null=mean(null),
                                      signed=signed, sigma_d=manifest['noise'][node]['sigma_d']))
    return decisions, contrasts, branches, pairs, excluded


def value_estimate(points, weights=None):
    """Re-estimate budget correction inside each bootstrap draw (point weights)."""
    weights = np.ones(len(points)) if weights is None else np.asarray(weights)
    residuals, used, costs = [], [], []
    for i, p in enumerate(points):
        if not p['changed'] or weights[i] == 0:
            continue
        controls = [j for j, q in enumerate(points) if q['node'] == p['node'] and not q['changed']
                    and q['point'] == p['point'] and weights[j] > 0]
        # At least two distinct control instances, otherwise use the node pool.
        if len({points[j]['instance'] for j in controls}) < 2:
            controls = [j for j, q in enumerate(points) if q['node'] == p['node']
                        and not q['changed'] and weights[j] > 0]
        if not controls:
            return None
        cost = float(np.average([points[j]['audit_difference'] for j in controls], weights=weights[controls]))
        residuals.append(p['audit_difference'] - p['immediate'] - cost)
        used.append(weights[i]); costs.append(cost)
    if not used:
        return None
    return dict(residual=float(np.average(residuals, weights=used)),
                budget_cost=float(np.average(costs, weights=used)))


def value_inference(points, draws=DRAWS):
    estimate = value_estimate(points)
    result = dict(points=len(points), changed_points=sum(p['changed'] for p in points),
                  changed_instances=len({p['instance'] for p in points if p['changed']}))
    if estimate is None:
        return dict(result, unavailable='No changed points or no unchanged control')
    result.update(estimate)
    result['audit_difference'] = mean(p['audit_difference'] for p in points if p['changed'])
    result['immediate'] = mean(p['immediate'] for p in points if p['changed'])
    rng = np.random.default_rng(SEED)
    weights = np.zeros((draws, len(points)))
    for node in sorted({p['node'] for p in points}):
        instances = sorted({p['instance'] for p in points if p['node'] == node})
        counts = rng.multinomial(len(instances), np.full(len(instances), 1/len(instances)), draws)
        for i, inst in enumerate(instances):
            weights[:, [j for j, p in enumerate(points) if p['instance'] == inst]] = counts[:, i, None]
    samples = [value_estimate(points, w) for w in weights]
    valid = [s['residual'] for s in samples if s is not None]
    result['bootstrap_valid'] = len(valid)
    result['ci'] = list(map(float, np.quantile(valid, [.025, .975]))) if valid else None
    return result


def analyze_absolute(source, draws=DRAWS):
    decisions, rows, branches, pairs, excluded = collect_absolute(source)
    nodes = sorted({r['node'] for r in rows})
    eligible = {r['node'] for r in rows if r['changed']}
    # Average repetitions before all value inference.
    points = []
    for inst, b in sorted({(p['instance'], p['point']) for p in pairs}):
        ps = [p for p in pairs if p['instance'] == inst and p['point'] == b]
        point = {k: ps[0][k] for k in ('node', 'instance', 'point', 'changed', 'direction')}
        point.update({k: mean(p[k] for p in ps) for k in ('audit_difference', 'immediate', 'record_shift')})
        points.append(point)
    results, values, record, mechanism = [], [], [], []
    for group in nodes + ['pooled_value_eligible']:
        selected_nodes = eligible if group == 'pooled_value_eligible' else {group}
        for h in (1, 3):
            for m in ('abs_metric',) + METRICS[2:]:
                subset = [r for r in rows if r['node'] in selected_nodes and r['horizon'] == str(h) and r['metric'] == m]
                results.append(dict(group=group, horizon=str(h), metric=m, **inference(subset, draws=draws)))
        values.append(dict(group=group, **value_inference([p for p in points if p['node'] in selected_nodes], draws)))
        for changed in (True, False):
            ps = [p for p in pairs if p['node'] in selected_nodes and p['changed'] == changed]
            record.append(dict(group=group, changed=changed, point_repetitions=len(ps),
                               mean=mean(p['record_shift'] for p in ps)))
            mechanism.append(dict(group=group, changed=changed, point_repetitions=len(ps),
                                  **{k: mean(p[k] for p in ps if p[k] is not None) for k in
                                     ('memory_differs', 'continue_repeat', 'continue_reverse', 'verify_repeat', 'verify_reverse')}))
    # Holm over both horizons for every evaluable node AND pool; exclude unavailable tests.
    primary = [r for r in results if r['metric'] == 'abs_metric' and 'p_null' in r]
    ordered = sorted(primary, key=lambda r: max(r['p_null'], r['p_unchanged']))
    running = 0.
    for i, r in enumerate(ordered):
        running = max(running, min(1., (len(ordered)-i)*max(r['p_null'], r['p_unchanged'])))
        r['holm_p'] = running
    # Failure to reject is not equivalence. No equivalence margin was specified.
    violated = any(r['reject'] and r['holm_p'] < .05 and any(
        v['group'] == r['group'] and v.get('ci') and (v['ci'][0] > 0 or v['ci'][1] < 0)
        for v in values) for r in primary)
    return dict(label='PILOT, PARTIAL, not evidence', author='AI-assisted by Codex',
                input_revision=source.revision, input_sha256=source.hashes, seed=SEED, draws=draws,
                outcome='abs_metric', counts={n: dict(Counter(d['direction'] for d in decisions if d['node'] == n)) for n in nodes},
                decisions=decisions, point_contrasts=rows, branch_summaries=branches, pairs=pairs,
                value_points=points, excluded_points=excluded, results=results, values=values,
                record_shift=record, mechanism=mechanism, holm_tests=len(primary),
                verdict='violated in value terms' if violated else 'undetermined at this sample size')


def markdown_absolute(report):
    lines = ['# Absolute-metric DI diagnostic tables', '',
             'AI-assisted by Codex. PILOT, PARTIAL, not evidence.', '',
             f'Input revision: `{report["input_revision"]}`; {report["draws"]} draws; seed {SEED}.', '',
             '## Decisions changed (point-repetitions)', '',
             '| Node | Promotion | Demotion | Unchanged |', '|---|---:|---:|---:|']
    for n, c in report['counts'].items():
        lines.append(f'| {n} | {c.get("promotion",0)} | {c.get("demotion",0)} | {c.get("unchanged",0)} |')
    lines += ['', '## Distances and inference', '',
              '| Group | k | Metric | Changed points | D_changed | D_null paired | D_unchanged | Excess null [95% CI] | Excess unchanged [95% CI] | p null | p unchanged | Holm p |',
              '|---|---:|---|---:|---:|---:|---:|---|---|---:|---:|---:|']
    for r in report['results']:
        vals = [r['group'],r['horizon'],r['metric'],r['changed_points'],r['D_changed'],r['D_null_at_changed'],r['D_unchanged'],
                f'{fmt(r.get("excess_null"))} {fmt(r.get("ci_null"))}', f'{fmt(r.get("excess_unchanged"))} {fmt(r.get("ci_unchanged"))}',
                r.get('p_null'),r.get('p_unchanged'),r.get('holm_p')]
        lines.append('| '+' | '.join(map(fmt,vals))+' |')
    lines += ['', f'Holm family: {report["holm_tests"]} evaluable primary node/pool × horizon tests. NA is unavailable, not zero.', '',
              '## Value residual (point means; cluster bootstrap)', '',
              '| Group | Changed points | Changed instances | Audit difference | Immediate proxy | Budget correction | Residual | 95% CI | Valid draws |',
              '|---|---:|---:|---:|---:|---:|---:|---|---:|']
    for v in report['values']:
        lines.append('| '+' | '.join(fmt(v.get(k)) for k in ('group','changed_points','changed_instances','audit_difference','immediate','budget_cost','residual','ci','bootstrap_valid'))+' |')
    for name, keys in [('record_shift',('group','changed','point_repetitions','mean')),
                       ('mechanism',('group','changed','point_repetitions','memory_differs','continue_repeat','continue_reverse','verify_repeat','verify_reverse'))]:
        lines += ['', f'## {name}', '', '| '+' | '.join(keys)+' |', '| '+' | '.join('---' for _ in keys)+' |']
        for row in report[name]:
            lines.append('| '+' | '.join(fmt(row[k]) for k in keys)+' |')
    lines += ['', '## Metric-identical fraction (equal branch weight)', '',
              '| Node | k | Action | Fraction |', '|---|---:|---|---:|']
    for n in report['counts']:
        for h in ('1','3'):
            for a in ('continue','verify'):
                bs=[b for b in report['branch_summaries'] if b['node']==n and b['horizon']==h and b['action']==a]
                lines.append(f'| {n} | {h} | {a} | {fmt(mean(b["metric_identical"] for b in bs))} |')
    lines += ['', '## Excluded whole points', '']
    lines += [f'- `{p["instance"]} b{p["point"]:03d}`: '+', '.join(p['failed_leaves']) for p in report['excluded_points']] or ['None.']
    lines += ['', '## Decision audit', '', '| Instance | Point | Rep | Direction | Verify mean delta |', '|---|---:|---:|---|---:|']
    for d in report['decisions']:
        lines.append('| '+' | '.join(fmt(d[k]) for k in ('instance','point','rep','direction','verify_mean_delta'))+' |')
    lines += ['', f'Verdict: **{report["verdict"]}**.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    parser.add_argument('--outcome', choices=('legacy', 'abs_metric'), default='legacy')
    parser.add_argument('--md',required=True,type=Path)
    parser.add_argument('--json',required=True,type=Path)
    args=parser.parse_args()
    source=CommittedInputs(args.run_dir)
    for path in (args.md,args.json):
        absolute=path.resolve()
        if absolute.is_relative_to((source.repo/'results').resolve()) or absolute.is_relative_to(args.run_dir.resolve()):
            parser.error('Outputs must be outside existing result directories')
    report = analyze(source) if args.outcome == 'legacy' else analyze_absolute(source)
    args.md.write_text(markdown(report) if args.outcome == 'legacy' else markdown_absolute(report))
    args.json.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'counts':report['counts'],'verdict':report['verdict']}))


if __name__=='__main__':
    main()
