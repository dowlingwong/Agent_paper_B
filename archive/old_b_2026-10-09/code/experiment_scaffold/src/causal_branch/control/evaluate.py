"""Paired template bootstrap for all-feasible checkpoint policy gains.

Rows are validated before aggregation. Bootstrap draws preserve template
multiplicity and all policies use the same draws. Context-only batch allocation
is recomputed in each draw. No model calls or scientific evidence are involved.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
from causal_branch.control.allocation import batch_top_q
from causal_branch.control.schema import (BranchRecord, validate_record,
    assert_no_duplicate_units, assert_projection_is_leak_free, feature_projection,
    assert_split_disjoint)

OUTCOME_CHANNELS = ("S", "U", "I")


def assert_single_outcome_channel(channels) -> None:
    """A policy contrast uses exactly one outcome channel.

    Mixing a binary success channel ``S`` and a continuous utility channel
    ``U`` in one contrast is refused: they define different estimands and must
    never be pooled into a single effect.
    """
    requested = list(channels)
    if len(requested) != 1 or requested[0] not in OUTCOME_CHANNELS:
        raise ValueError(
            "a policy contrast must use exactly one outcome channel "
            f"(one of {OUTCOME_CHANNELS}); mixing S and U is refused"
        )


@dataclass
class PolicyEvaluation:
    name: str
    capacity: float
    gain_feasible: float
    gain_selected_only: float
    gain_full_population: float
    n_templates: int
    n_roots: int
    n_eligible_checkpoints: int
    n_feasible_checkpoints: int
    n_selected: int
    achieved_capacity: float
    selected_incremental_cost: dict[str, float] = field(default_factory=dict)
    gain_ci: tuple[float, float] = (float('nan'), float('nan'))


@dataclass
class Comparison:
    outcome: str
    capacity: float
    primary_policy: str
    primary_comparator: str
    d_value: float
    d_ci: tuple[float, float]
    support_note: str
    n_bootstrap_valid: int
    n_bootstrap_undefined: int
    evaluations: dict[str, PolicyEvaluation] = field(default_factory=dict)


def checkpoint_rows(records: list[BranchRecord], channels=('S',), *, reachability=()) -> list[dict]:
    """One complete row per root/checkpoint; unavailable is defined by its mask.

    ``reachability`` optionally adds original roots that never reached an
    eligible checkpoint.  Each entry is a mapping with ``root_id``,
    ``template_family_id``, ``split`` and a ``fallback`` outcome.  Such a root is
    kept in the original-root (full-population) denominator with a zero
    contrast, so it is never silently dropped.
    """
    fields = {'S': 'outcome_success', 'U': 'outcome_utility', 'I': 'outcome_invalid'}
    if not channels or any(c not in fields for c in channels):
        raise ValueError('unknown requested outcome channel')
    assert_no_duplicate_units(records)
    assert_split_disjoint(records)
    grouped = {}
    roots = {}
    for r in records:
        validate_record(r)
        if r.integrity_status != "ok":
            # A collection or infrastructure failure is not an outcome.  The
            # evaluator refuses to analyse it as a zero, which would fabricate
            # a utility value.
            raise ValueError(
                "refusing to analyse integrity status "
                f"{r.integrity_status!r} as an outcome: {r.identity()}"
            )
        assert_projection_is_leak_free(feature_projection(r))
        if r.root_id in roots and roots[r.root_id] != r.checkpoint_id:
            raise ValueError('one-step evaluator requires one checkpoint per root')
        roots[r.root_id] = r.checkpoint_id
        key = (r.root_id, r.checkpoint_id)
        meta = (r.template_id, r.template_family_id or r.template_id, r.split,
                r.protocol_hash, r.feature_registry_version, r.runtime_manifest_hash,
                r.snapshot_hash, r.history_hash, dict(r.pre_treatment_features), dict(r.pre_treatment_mask))
        bucket = grouped.setdefault(key, {'meta': meta, 'g0': {}, 'gv': {}})
        if meta != bucket['meta']:
            raise ValueError(f'inconsistent checkpoint context/mask/lineage: {key}')
        if not r.pre_treatment_mask[r.action_id]:
            continue
        for channel in channels:
            if getattr(r, fields[channel]) is None:
                raise ValueError(f'missing requested outcome {channel} for feasible action {r.action_id}: {key}')
        bucket[r.action_id][r.repetition_id] = r
    rows = []
    for key, bucket in sorted(grouped.items()):
        template, family, split, _, _, _, _, _, features, mask = bucket['meta']
        if not bucket['g0']:
            raise ValueError(f'missing feasible g0 branch: {key}')
        if mask['gv']:
            if set(bucket['g0']) != set(bucket['gv']):
                raise ValueError(f'missing feasible gv branch or unmatched repetitions: {key}')
            for rep in bucket['g0']:
                if bucket['g0'][rep].seed_coupling_id != bucket['gv'][rep].seed_coupling_id:
                    raise ValueError(f'paired seed-coupling mismatch: {key}')
        row = dict(key=key, template=template, family=family, split=split, features=features, mask=mask)
        for action in ('g0', 'gv'):
            arm = list(bucket[action].values())
            for channel in channels:
                row[action+'_'+channel] = float(np.mean([getattr(r, fields[channel]) for r in arm])) if arm else None
            cost_names = set().union(*(set(r.cost_vector) for r in arm)) if arm else set()
            if any(set(r.cost_vector) != cost_names for r in arm):
                raise ValueError('inconsistent cost channels within an action')
            row[action+'_cost'] = {c: float(np.mean([r.cost_vector[c] for r in arm])) for c in cost_names}
        if mask['gv'] and set(row['gv_cost']) != set(row['g0_cost']):
            raise ValueError('paired actions have inconsistent cost channels')
        rows.append(row)
    by_root = {r['key'][0] for r in rows}
    for entry in reachability:
        root_id = entry.get('root_id')
        if not root_id or root_id in by_root:
            raise ValueError(f'invalid or duplicate reachability root: {root_id!r}')
        family = entry.get('template_family_id') or root_id
        split = entry.get('split')
        if split is None:
            raise ValueError('a reachability row requires its declared split')
        fallback = entry.get('fallback')
        if fallback is None:
            raise ValueError('a reachability row requires its registered fallback outcome')
        row = dict(
            key=(root_id, f'{root_id}/unreached'), template=entry.get('template_id', root_id),
            family=family, split=split, features={}, mask={'g0': True, 'gv': False},
        )
        for channel in channels:
            row['g0_'+channel] = float(fallback)
            row['gv_'+channel] = None
        row['g0_cost'] = {}
        row['gv_cost'] = {}
        rows.append(row)
    return rows


def cluster_draw_indices(template_index: np.ndarray, drawn: np.ndarray) -> np.ndarray:
    """Expand every drawn template occurrence; repeated draws repeat every row."""
    return np.concatenate([np.flatnonzero(template_index == t) for t in drawn]).astype(int)


def evaluate_policies(records: list[BranchRecord], *,
        scores_by_policy: dict[str, dict[tuple[str, str], float]],
        primary_policy: str, primary_comparator: str,
        capacities: tuple[float, ...] = (0.25,), outcome: str = 'S',
        n_bootstrap: int = 200, seed: int = 20260924, reachability=()) -> list[Comparison]:
    if primary_policy not in scores_by_policy or primary_comparator not in scores_by_policy:
        raise ValueError('explicit primary policy/comparator must name supplied policies')
    if isinstance(n_bootstrap, bool) or not isinstance(n_bootstrap, int) or n_bootstrap < 1:
        raise ValueError('n_bootstrap must be a positive integer')
    assert_single_outcome_channel((outcome,))
    rows = checkpoint_rows(records, (outcome,), reachability=reachability)
    if not rows:
        return []
    if len({r['split'] for r in rows}) != 1:
        raise ValueError('evaluation must use a single declared split')
    keys = [r['key'] for r in rows]
    feasible = np.array([r['mask']['gv'] for r in rows], dtype=bool)
    if not feasible.any():
        raise ValueError('no feasible checkpoints: conditional gain is undefined')
    contrast = np.array([r['gv_'+outcome]-r['g0_'+outcome] if r['mask']['gv'] else 0. for r in rows])
    # Family is the template resampling unit, so sibling variants stay together.
    templates = sorted({r['family'] for r in rows})
    template_index = np.array([templates.index(r['family']) for r in rows])
    aligned = {}
    for name, keyed in scores_by_policy.items():
        if set(keyed) != set(keys):
            raise ValueError(f'policy {name!r} score keys do not match checkpoints')
        aligned[name] = np.array([keyed[k] for k in keys], dtype=float)
        if not np.isfinite(aligned[name]).all():
            raise ValueError('policy scores must be finite')
    rng = np.random.default_rng(seed)
    results = []
    for q in capacities:
        evaluations = {}
        boot = {name: [] for name in aligned}
        for name, scores in aligned.items():
            selected = batch_top_q(scores, feasible, q)
            total = float(contrast[selected].sum())
            costs = {}
            for i in np.flatnonzero(selected):
                row = rows[i]
                if set(row['gv_cost']) != set(row['g0_cost']):
                    raise ValueError('paired actions have inconsistent cost channels')
                for c in row['g0_cost']:
                    costs[c] = costs.get(c, 0.)+row['gv_cost'][c]-row['g0_cost'][c]
            evaluations[name] = PolicyEvaluation(name, q, total/int(feasible.sum()),
                total/int(selected.sum()) if selected.any() else 0., total/len(rows),
                len(templates), len(rows), len(rows), int(feasible.sum()), int(selected.sum()),
                float(selected.sum()/feasible.sum()), selected_incremental_cost=costs)
        undefined = 0
        for _ in range(n_bootstrap):
            drawn = rng.choice(len(templates), size=len(templates), replace=True)
            idx = cluster_draw_indices(template_index, drawn)
            mask = feasible[idx]
            if not mask.any():
                undefined += 1  # no zero imputation for an undefined conditional mean
                continue
            for name, scores in aligned.items():
                selected = batch_top_q(scores[idx], mask, q)
                boot[name].append(float(contrast[idx][selected].sum()/mask.sum()))
        if not boot[primary_policy]:
            raise ValueError('all bootstrap draws lack feasible support')
        for name, evaluation in evaluations.items():
            evaluation.gain_ci = tuple(float(v) for v in np.percentile(boot[name], [2.5, 97.5]))
        d_boot = np.array(boot[primary_policy])-np.array(boot[primary_comparator])
        results.append(Comparison(outcome, q, primary_policy, primary_comparator,
            evaluations[primary_policy].gain_feasible-evaluations[primary_comparator].gain_feasible,
            tuple(float(v) for v in np.percentile(d_boot, [2.5,97.5])),
            f'eligible one-checkpoint roots={len(rows)}, feasible={int(feasible.sum())}; '
            f'template families={len(templates)}; unrepresented non-reaching roots are not inferred',
            len(d_boot), undefined, evaluations))
    return results
