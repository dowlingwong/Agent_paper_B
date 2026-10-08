"""F7: the single evaluation harness for the two-checkpoint timing study.

One entrypoint: fit the controllers on development template families, freeze
them, then evaluate on held-out families.  The F4 allocator is re-run on the
held-out batch **and inside every bootstrap draw** (a template-family cluster
bootstrap with shared draws).  Policy value is the mean U over **all** original
roots, taken from the selected leaves.

N1 lives in evaluation only: the controllers never read ``p``.  The harness wires
``population_contrast_lower_bound``, ``p_grid_report`` and ``path_allowance`` with
one explicit mapping (per-checkpoint ``p``, ``p_path = min(1, p1 + p2)``, tax
``2 * m * p_path``) and reports the largest surviving ``p`` per contrast, with
the allocation-interference scope stated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dataclasses import replace as _replace

from causal_branch.control.allocator import AllocatorParams, AllocatorRoot, allocate, budget_for
from causal_branch.control.replay_validity import (
    CheckpointAllowance,
    audit_upper_confidence_bound,
    audits_needed_for_bound,
    path_allowance,
    p_grid_report,
    population_contrast_lower_bound,
    simultaneous_family_bounds,
)
from causal_branch.control.timing import (
    BavarInspiredVOI,
    ConstantReserveAblation,
    FixedRegimeController,
    ProposedTiming,
    RepeatedMyopicComparator,
    cross_fitted_scores,
    decision_views,
    matching_report,
)

P_GRID = (0.0, 0.005, 0.01, 0.02, 0.05, 0.10)
#: Working per-checkpoint replay allowance (a sensitivity assumption, never
#: called measured; RUNBOOK §12.2).
WORKING_P = 0.02
PRACTICAL_TARGET = 0.02
BONFERRONI = 2
#: Derived allocation-displacement constant for the F4 allocator (m <= 3).
DERIVED_M = 3
#: An adjusted interval narrower than this is treated as degenerate (E2).
DEGENERATE_WIDTH = 1e-9


def _controllers() -> dict:
    """The evaluated controllers; each has one implementation (U1)."""

    return {
        "proposed": ProposedTiming(),
        "myopic": RepeatedMyopicComparator(),
        "bavar": BavarInspiredVOI(),
        "constant_reserve": ConstantReserveAblation(),
    }


class EvaluationError(ValueError):
    """The evaluation harness refuses an invalid request."""


@dataclass
class EvaluationReport:
    contrasts: dict[str, dict]
    values: dict[str, float]
    readings: dict[str, str]
    precision: dict[str, float]
    diagnostics: dict
    n1: dict
    matching: dict
    n_roots: int
    n_families: int
    budget: int
    #: frozen calibrated allocator parameters per controller
    params: dict = field(default_factory=dict)
    #: realized regimes per controller on the held-out batch
    regimes: dict = field(default_factory=dict)
    #: fixed now/later/never values (reference only; they ignore the budget)
    fixed_values: dict = field(default_factory=dict)


def _value(rows, regimes) -> float:
    if not rows:
        raise EvaluationError("empty batch")
    field = {"now": "u_now", "later": "u_later", "never": "u_never"}
    return float(np.mean([r[field[regimes[r.get("draw_id", r["root_id"])]]] for r in rows]))


def _run_allocator(rows, scores, params, q):
    roots = [
        AllocatorRoot(
            root_id=r.get("draw_id", r["root_id"]),
            s1=scores[r["root_id"]]["s1"], s2=scores[r["root_id"]]["s2"],
            reached2=bool(r["reached2"]), terminated=bool(r.get("terminated", False)),
            family=r["family"], split=r.get("split", ""),
        )
        for r in rows
    ]
    return allocate(roots, budget=budget_for(len(roots), q), params=params, q=q).regimes


def _calibrate(controller, model, dev_rows, dev_views, q):
    """Pick the controller's own (c1, c2, R) from its grid on development data.

    Every controller has the same number of candidate configurations; the first
    best configuration in grid order wins, so calibration is deterministic.
    """

    scores = controller.score(model, dev_views)
    best, best_value = None, -np.inf
    for params in controller.grid():
        regimes = _run_allocator(dev_rows, scores, params, q)
        value = _value(dev_rows, regimes)
        if value > best_value:
            best, best_value = params, value
    return best


def _family_index(rows):
    families = sorted({r["family"] for r in rows})
    return families, np.array([families.index(r["family"]) for r in rows])


def _bootstrap_contrast(rows, scores, params, q, names, n_bootstrap, seed, index, n_families,
                        pairs=()):
    """Shared-draw cluster bootstrap; also counts draws where a pair coincides.

    ``pairs`` lists (a, b) controller pairs; ``identical[(a, b)]`` is the
    fraction of draws in which the two realized regimes agree on every root.
    """

    base = {}
    for name in names:
        base[name] = _run_allocator(rows, scores[name], params[name], q)
    point = {k: _value(rows, base[k]) for k in names}
    rng = np.random.default_rng(seed)
    draws = {k: [] for k in names}
    same = {pair: 0 for pair in pairs}
    for _ in range(n_bootstrap):
        drawn = rng.choice(n_families, size=n_families, replace=True)
        idx = np.concatenate([np.flatnonzero(index == t) for t in drawn]).astype(int)
        resampled = []
        for occurrence, i in enumerate(idx):
            row = dict(rows[i])
            row["draw_id"] = f"{row['root_id']}__{occurrence}"
            resampled.append(row)
        realized = {}
        for name in names:
            # re-run the allocator inside the draw (budget = floor(q * N_draw))
            realized[name] = _run_allocator(resampled, scores[name], params[name], q)
            draws[name].append(_value(resampled, realized[name]))
        for a, b in pairs:
            same[(a, b)] += int(realized[a] == realized[b])
    identical = {pair: count / max(1, n_bootstrap) for pair, count in same.items()}
    return point, {k: np.asarray(v) for k, v in draws.items()}, base, identical


def _calibration(pred, target) -> dict:
    """Out-of-fold calibration of a prediction against its paired target.

    ``slope`` and ``intercept`` come from regressing the target on the
    prediction (a calibrated predictor has slope 1, intercept 0); ``r2`` is the
    out-of-sample reliability 1 - MSE / Var(target), which can be negative.
    """

    pred, target = np.asarray(pred, dtype=float), np.asarray(target, dtype=float)
    out = {"n": int(len(pred)), "slope": None, "intercept": None, "r2": None}
    if len(pred) < 3:
        return out
    if pred.var() > 0:
        slope = float(np.cov(pred, target, bias=True)[0, 1] / pred.var())
        out["slope"] = slope
        out["intercept"] = float(target.mean() - slope * pred.mean())
    if target.var() > 0:
        out["r2"] = float(1.0 - np.mean((target - pred) ** 2) / target.var())
    return out


def _null_diagnostics(dev_rows, rows, scores):
    """Out-of-fold calibration/ranking on development and test heterogeneity."""

    fit = cross_fitted_scores(dev_rows)
    oof = fit.scores
    imm_dev = np.array([r["u_now"] - r["u_never"] for r in dev_rows])
    cont_dev = np.array([r["u_later"] - r["u_never"] for r in dev_rows])
    a1_dev = np.array([oof[r["root_id"]]["a1"] for r in dev_rows])
    a2_dev = np.array([oof[r["root_id"]]["a2"] for r in dev_rows])
    vwait_dev = np.array([oof[r["root_id"]]["vwait"] for r in dev_rows])
    imm = np.array([r["u_now"] - r["u_never"] for r in rows])
    cont = np.array([r["u_later"] - r["u_never"] for r in rows])
    a1 = np.array([scores[r["root_id"]]["a1"] for r in rows])
    a2 = np.array([scores[r["root_id"]]["a2"] for r in rows])
    vwait = np.array([scores[r["root_id"]]["vwait"] for r in rows])

    def _corr(u, v):
        return float(np.corrcoef(u, v)[0, 1]) if u.std() and v.std() else 0.0

    reached_dev = [i for i, r in enumerate(dev_rows) if r["reached2"]]
    calibration = {
        "a1": _calibration(a1_dev, imm_dev),
        "a2": _calibration(a2_dev[reached_dev], cont_dev[reached_dev]),
        "vwait": _calibration(vwait_dev, [fit.targets[r["root_id"]] for r in dev_rows]),
    }
    return {
        "oof_calibration": calibration,
        "oof_corr_a1_immediate": _corr(a1_dev, imm_dev),
        "oof_corr_a2_continuation": _corr(a2_dev, cont_dev),
        "oof_vwait_sd": float(vwait_dev.std()),
        "test_corr_a2_continuation": _corr(a2, cont),
        "test_corr_a1_immediate": _corr(a1, imm),
        "vwait_mean": float(vwait.mean()),
        "vwait_sd": float(vwait.std()),
        "vwait_heterogeneity_ci": (
            float(np.percentile(vwait, 2.5)), float(np.percentile(vwait, 97.5))),
        "a2_ranking_quality": _corr(a2, cont),
    }


def displacement_check(*, n_batches: int = 200, n_roots: int = 20, q: float = 0.25,
                       seed: int = 20260927) -> dict:
    """Measure the max number of changed roots under a single-root perturbation.

    A planted single-root perturbation must change at most ``m`` roots' realized
    regimes, where ``m <= 3`` for the F4 allocator (the root itself, one
    displaced in phase 1, one displaced in phase 2 through the capacity shift).
    """

    rng = np.random.default_rng(seed)
    budget = budget_for(n_roots, q)
    params = AllocatorParams(0.0, 0.0, 1)
    worst = 0
    for _ in range(n_batches):
        roots = [
            AllocatorRoot(root_id=f"r{i}", s1=float(rng.normal()), s2=float(rng.normal()),
                          reached2=bool(rng.uniform() < 0.8), feasible1=bool(rng.uniform() < 0.9))
            for i in range(n_roots)
        ]
        base = allocate(roots, budget=budget, params=params, q=q).regimes
        for j in range(n_roots):
            perturbed = list(roots)
            perturbed[j] = _replace(roots[j], s1=roots[j].s1 + float(rng.normal(3.0, 1.0)),
                                    s2=roots[j].s2 + float(rng.normal(3.0, 1.0)),
                                    reached2=not roots[j].reached2)
            new = allocate(perturbed, budget=budget, params=params, q=q).regimes
            changed = sum(base[k] != new[k] for k in base)
            worst = max(worst, changed)
    return {"max_changed_roots": worst, "derived_m": DERIVED_M,
            "within_bound": worst <= DERIVED_M, "n_batches": n_batches, "n_roots": n_roots}


def evaluate_tree(dev_rows, test_rows, *, q: float = 0.25, n_bootstrap: int = 200,
                  seed: int = 20260927, p_grid=P_GRID) -> EvaluationReport:
    if not dev_rows or not test_rows:
        raise EvaluationError("development and test rows are required")
    if set(r["family"] for r in dev_rows) & set(r["family"] for r in test_rows):
        raise EvaluationError("development and test template families must be disjoint")

    controllers = _controllers()
    dev_views = decision_views(dev_rows)
    test_views = decision_views(test_rows)
    models = {name: c.fit(dev_rows) for name, c in controllers.items()}
    params = {name: _calibrate(controllers[name], models[name], dev_rows, dev_views, q)
              for name in controllers}
    scores = {name: controllers[name].score(models[name], test_views) for name in controllers}
    budget = budget_for(len(test_rows), q)
    regimes = {name: _run_allocator(test_rows, scores[name], params[name], q)
               for name in models}
    values = {name: _value(test_rows, regimes[name]) for name in models}

    families, index = _family_index(test_rows)
    pairs = (("proposed", "myopic"), ("proposed", "bavar"), ("myopic", "constant_reserve"))
    point, draws, _, identical = _bootstrap_contrast(
        test_rows, scores, params, q, list(models), n_bootstrap, seed, index, len(families),
        pairs=pairs)

    contrasts = {}
    readings = {}
    precision = {}
    for comparator in ("myopic", "bavar"):
        key = f"proposed-{comparator}"
        d = draws["proposed"] - draws[comparator]
        lcb = float(np.percentile(d, 100 * (0.05 / BONFERRONI) / 2))
        ucb = float(np.percentile(d, 100 * (1 - (0.05 / BONFERRONI) / 2)))
        half = (ucb - lcb) / 2
        precision_met = half <= PRACTICAL_TARGET
        # E2: a contrast between identical policies, or a zero-width interval,
        # is an implementation artifact, not evidence about timing.
        policies_distinct = regimes["proposed"] != regimes[comparator]
        degenerate = (ucb - lcb) < DEGENERATE_WIDTH
        precondition = policies_distinct and not degenerate
        if not precondition:
            reading = "inconclusive"
        elif lcb > PRACTICAL_TARGET:
            reading = "practically_large"
        elif lcb > 0.0:
            reading = "supported"
        elif ucb < PRACTICAL_TARGET and lcb > -PRACTICAL_TARGET:
            reading = "equivalence"
        elif ucb < PRACTICAL_TARGET and precision_met:
            reading = "not_practically_useful"
        else:
            reading = "inconclusive"
        contrasts[key] = {
            "point": float(point["proposed"] - point[comparator]),
            "adjusted_lcb": lcb, "adjusted_ucb": ucb, "n_draws": len(d),
            "policies_distinct": policies_distinct,
            "degenerate_interval": degenerate,
            "identical_draw_fraction": identical[("proposed", comparator)],
            "reading_precondition_met": precondition,
        }
        readings[key] = reading
        precision[key] = half

    diagnostics = _null_diagnostics(dev_rows, test_rows, scores["proposed"])
    matching = matching_report(list(controllers.values()))
    fixed_values = {regime: _value(test_rows, FixedRegimeController(regime).regimes(test_rows))
                    for regime in ("now", "later", "never")}
    diagnostics["identical_draw_fraction"] = {f"{a}-{b}": v for (a, b), v in identical.items()}

    # N1 in evaluation: population bound and largest surviving p per contrast.
    per_family_gains = {}
    for comparator in ("myopic", "bavar"):
        by_family = {}
        for r in test_rows:
            contribution = (
                r[{"now": "u_now", "later": "u_later", "never": "u_never"}[regimes["proposed"][r["root_id"]]]]
                - r[{"now": "u_now", "later": "u_later", "never": "u_never"}[regimes[comparator][r["root_id"]]]]
            )
            by_family.setdefault(r["family"], []).append(contribution)
        per_family_gains[f"proposed-{comparator}"] = np.array(
            [np.mean(v) for _, v in sorted(by_family.items())])
    # N2/N3: one explicit p mapping, used by the grid, the tax and the bound.
    # Each grid value p is a per-checkpoint allowance (p1 = p2 = p); the path
    # allowance is the union bound min(1, p1 + p2); the batch-allocated
    # population tax is 2 * m * p_path with the derived displacement m.
    # alpha is family-wise: p_grid_report / simultaneous_family_bounds divide it
    # by the two contrasts themselves.
    p_report = p_grid_report(per_family_gains, p_grid, alpha=0.05,
                             m=DERIVED_M, checkpoints=2)
    family_bounds, _ = simultaneous_family_bounds(per_family_gains, 0.05, 0.0)
    working = CheckpointAllowance(WORKING_P, "sensitivity_assumption")
    p_path = path_allowance(working, working)
    tax = 2.0 * DERIVED_M * p_path
    n1 = {
        "p_grid_report": p_report,
        "family_bounds_at_p0": family_bounds,
        "p_semantics": (
            "grid values are per-checkpoint allowances p1 = p2 = p; "
            "p_path = min(1, p1 + p2); population tax = 2 * m * p_path"
        ),
        "working_p": WORKING_P,
        "p_path": p_path,
        "derived_m": DERIVED_M,
        "population_tax_2mp": tax,
        "population_bound_at_working_p": {
            key: population_contrast_lower_bound(row["adjusted_lcb"], p_path, m=DERIVED_M)
            for key, row in contrasts.items()
        },
        "audit_arithmetic": {
            "ucb_24_zero_miss": audit_upper_confidence_bound(24),
            "audits_for_0.02": audits_needed_for_bound(0.02),
        },
        "interference_scope": (
            "covers allocation interference under the derived m <= 3 "
            "(derivation in N1_DISPLACEMENT.md; bound reproduced by the "
            "2026-09-27 independent review, finding N5)"
        ),
    }
    return EvaluationReport(contrasts=contrasts, values=values, readings=readings,
                            precision=precision, diagnostics=diagnostics, n1=n1,
                            matching=matching, n_roots=len(test_rows),
                            n_families=len(families), budget=budget,
                            params={k: (v.c1, v.c2, v.reserve) for k, v in params.items()},
                            regimes=regimes, fixed_values=fixed_values)
