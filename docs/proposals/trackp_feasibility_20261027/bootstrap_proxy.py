"""Exploratory CPU bootstrap sensitivity; fixed artificial forecasts, no model fitting.

Inputs are the committed 19 Oct engineering pilot. This is not finalist power.
AI-assisted; seed and assumptions are explicit and the output is a proposal aid.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from r1.c3.labels import soft_label, _gaussian_bins
from r1.c3.train.metrics import rps

ROOT = Path(__file__).resolve().parents[4]
PILOT = ROOT / 'results/r1/engineering/c3_audit_pilot_20261019T001338Z'

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

props = {r['proposal_id']: r for r in rows(PILOT / 'proposals.jsonl')}
audits = rows(PILOT / 'audits.jsonl')
groups = {}
for a in audits:
    p = props.get(a['proposal_id'])
    if p is None or a['reason'] != 'random' or p['inert']:
        continue
    diff = np.array(a['candidate_metrics'][3:6]) - np.array(a['incumbent_metrics'][3:6])
    y = soft_label(float(diff.mean()), float(diff.std(ddof=1) / np.sqrt(3)), p['sigma_node'], sigma_mode='se_audit')
    groups.setdefault(p['instance'], []).append(y)
labels = np.array([y for group in groups.values() for y in group])
base = labels.mean(axis=0)  # diagnostic normalizer, not an independently trained base rate
qa, qb = _gaussian_bins(-0.5, 1.0), _gaussian_bins(0.5, 1.0)  # artificial fixed forecasts
base_loss = float(np.mean(rps(np.broadcast_to(base, labels.shape), labels)))
parts = []
for key in sorted(groups):
    y = np.asarray(groups[key])
    diff = (rps(np.broadcast_to(qa, y.shape), y) - rps(np.broadcast_to(qb, y.shape), y)) / base_loss
    parts.append((len(y), float(diff.sum())))
counts, sums = np.array(parts).T
rng = np.random.default_rng(20261027)
# Illustrative upper-bound evaluation count: 2,000 total less 1,400 training, no dev allocation.
target_rows = 600
clusters = math.ceil(target_rows / counts.mean())
draws = rng.integers(0, len(parts), size=(5000, clusters))
means = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
epsilon = means - means.mean()
critical = float(np.quantile(np.abs(epsilon), .95))
grid = np.arange(0, 1.001, .005)
power = [float(np.mean(np.abs(epsilon + d) > critical)) for d in grid]
first = next((float(d) for d, p in zip(grid, power) if p >= .8), None)
output = {'label':'EXPLORATORY_PILOT_PROXY_NOT_FINALIST_POWER', 'seed':20261027, 'n_random_noninert':len(labels),
          'n_pilot_instances':len(parts), 'target_eval_rows_assumed':target_rows, 'sampled_clusters':clusters,
          'bootstrap_draws':len(draws), 'normalizer_pilot_mean_rps':base_loss,
          'paired_skill_difference_bootstrap_sd':float(epsilon.std(ddof=1)), 'null_abs_95_quantile':critical,
          'first_grid_effect_at_80pct_power':first, 'grid_step':.005,
          'power_at_effects':{str(d):float(np.mean(np.abs(epsilon+d)>critical)) for d in [0,.05,.1,.2,.3,.5,1.]},
          'assumptions':'v1 pilot labels from audit seeds 7004-7006; two fixed normal-bin forecasts z means -0.5,+0.5, sd 1; uniform instance-cluster bootstrap, no weights, duplicated pilot instances treated as independent; pilot labels estimate denominator; 600 evaluation rows and no dev allocation are assumed. Centered bootstrap shift with empirical two-sided 95% null critical value; not nested bootstrap or finalist power.'}
print(json.dumps(output,indent=2,sort_keys=True))
