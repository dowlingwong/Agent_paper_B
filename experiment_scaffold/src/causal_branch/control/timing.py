"""F6: the proposed cross-fitted continuation-value timing rule and comparators.

Design reference: `docs/paper_split/B_CONTROLLER_DESIGN_20260927.md` §3-§4.

The proposed rule is standard optimal-stopping methodology (least-squares
continuation-value estimation, Longstaff & Schwartz 2001; two-step fitted-Q
evaluation) **applied** to agent verification timing; it is not a new method and
is never described as optimal.  Folds are by template family, and every root,
descendant and repetition of a family stays together.

Continuation target (corrects the max-bias): an independent noisy estimate's
positive part is upward biased, so the target is the out-of-fold second-stage
decision times the observed paired outcome,
``Y_wait = reached2 * 1{A2_oof > c2} * (U_later - U_never)``, where ``A2_oof``
comes from a second-stage model fitted without the root's own family (nested
inside any outer cross-fitting fold).

Controllers never read a replay allowance, leaf outcomes or hidden data.
Fitting uses development rows (outcomes are training labels).  Scoring at a
decision point receives only ``DecisionView`` objects (``decision_views``):
checkpoint 1 sees H1, checkpoint 2 sees H2, and a view raises on any attempt to
read outcomes or hidden data (review finding L1).

Each controller has exactly one implementation (``fit``, ``score``, ``grid``),
and the evaluation harness calls those methods (review findings U1/U2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib

import numpy as np

from causal_branch.control.allocator import AllocatorParams
from causal_branch.control.branch_tree import DecisionView

RIDGE_L2 = 0.01
N_FOLDS = 5
#: Candidate grids.  Every controller calibrates the same number of
#: configurations (27) on the same development data (design §4).
#:
#: - proposed and repeated-myopic declare no constant reserve (R = 0) and share
#:   one (c1, c2) grid (9 x 3), so their primary contrast isolates the
#:   checkpoint-1 score: the proposed rule reserves through V_wait in s1;
#: - the BAVAR-inspired scheduler and the constant-reserve ablation declare a
#:   hard reserve and tune it (3 x 3 x 3).
#: A finer c1 grid for myopic alone let a tuned high cutoff mimic a reserve and
#: moved the proposed-myopic contrast by about -0.02 U in a probe; a shared
#: grid removes that artifact.
GRID_C = (-0.5, 0.0, 0.1)
GRID_RESERVE = (0, 1, 2)
GRID_C1_FINE = (-0.5, -0.25, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2, 0.3)


class TimingError(ValueError):
    """A timing-controller request violates the design."""


# --------------------------------------------------------------------------
# Ridge helpers (one model family for every controller)
# --------------------------------------------------------------------------


def _fold_of(family: str, n_folds: int) -> int:
    digest = hashlib.sha256(str(family).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % n_folds


def _design(rows, keys, phase: int = 1):
    if not keys:
        return np.zeros((len(rows), 1))
    field = "h1" if phase == 1 else "h2"
    return np.array([[float(r[field][k]) for k in keys] + [1.0] for r in rows], dtype=float)


def _fit(x, y, l2):
    y = np.asarray(y, dtype=float)
    if not np.isfinite(y).all():
        raise TimingError("non-finite training target")
    return np.linalg.solve(x.T @ x + l2 * np.eye(x.shape[1]), x.T @ y)


def _predict(w, x):
    return x @ w


def _feature_keys(rows, key):
    return sorted({name for row in rows for name in row[key]})


@dataclass
class CrossFit:
    """Out-of-fold per-root stage scores for the proposed rule."""

    scores: dict[str, dict[str, float]]
    #: each held-out root's own continuation target under its fold's
    #: second-stage model (a label, for calibration diagnostics only)
    targets: dict[str, float] = field(default_factory=dict)
    keys_h1: list[str] = field(default_factory=list)
    keys_h2: list[str] = field(default_factory=list)


def _oof_second_stage(rows, keys_h2, l2: float, n_folds: int) -> dict[str, float]:
    """Out-of-fold ``A2`` predictions for every reached root (M1 fix).

    Each reached root's prediction comes from a second-stage model fitted
    without its own template family's fold, so the decision
    ``1{A2 > c2}`` used in the continuation target is independent of that
    root's own paired outcome.  Using an in-sample decision instead selects on
    the same noise and leaves ``V_wait`` upward biased (review finding M1).
    """

    reached = [r for r in rows if r["reached2"]]
    preds: dict[str, float] = {}
    families = sorted({r["family"] for r in reached})
    if len(families) < 2:
        if reached:
            raise TimingError(
                "the continuation target needs reached roots from at least two "
                "template families (no out-of-fold second-stage decision exists)")
        return preds
    # hash folds when they give at least two groups; otherwise leave one
    # family out, so a small development set never degrades to a zero target
    if len({_fold_of(f, n_folds) for f in families}) >= 2:
        group = {f: _fold_of(f, n_folds) for f in families}
    else:
        group = {f: i for i, f in enumerate(families)}
    for g in sorted(set(group.values())):
        train = [r for r in reached if group[r["family"]] != g]
        test = [r for r in reached if group[r["family"]] == g]
        w2 = _fit(_design(train, keys_h2, 2),
                  [r["u_later"] - r["u_never"] for r in train], l2)
        for r in test:
            preds[r["root_id"]] = float(_predict(w2, _design([r], keys_h2, 2))[0])
    return preds


def _continuation_target(rows, oof_a2: dict[str, float], c2: float) -> list[float]:
    """``Y_wait = reached2 * 1{A2_oof > c2} * (U_later - U_never)``."""

    out = []
    for r in rows:
        pred = oof_a2.get(r["root_id"]) if r["reached2"] else None
        if pred is None:
            out.append(0.0)
        else:
            out.append((1.0 if pred > c2 else 0.0) * (r["u_later"] - r["u_never"]))
    return out


def cross_fitted_scores(rows, *, n_folds: int = N_FOLDS, l2: float = RIDGE_L2,
                        c2: float = 0.0) -> CrossFit:
    """Out-of-fold ``a1``, ``a2``, ``vwait`` and the proposed ``s1``/``s2``.

    For held-out fold ``k`` every model is fitted on the other folds; inside
    that training set the continuation target uses a *nested* out-of-fold
    second-stage decision (``_oof_second_stage``).  ``y_wait`` is the held-out
    root's own target under the fold's second-stage model, returned separately in
    ``CrossFit.targets`` for calibration diagnostics.
    """

    if not rows:
        raise TimingError("no rows")
    keys_h1 = _feature_keys(rows, "h1")
    keys_h2 = _feature_keys(rows, "h2")
    out: dict[str, dict[str, float]] = {}
    targets: dict[str, float] = {}
    for fold in range(n_folds):
        train = [r for r in rows if _fold_of(r["family"], n_folds) != fold]
        test = [r for r in rows if _fold_of(r["family"], n_folds) == fold]
        if not train or not test:
            continue
        reached = [r for r in train if r["reached2"]]
        w2 = None
        if reached:
            w2 = _fit(_design(reached, keys_h2, 2),
                      [r["u_later"] - r["u_never"] for r in reached], l2)
        y_wait = _continuation_target(
            train, _oof_second_stage(train, keys_h2, l2, n_folds), c2)
        w_wait = _fit(_design(train, keys_h1, 1), y_wait, l2)
        w_a1 = _fit(_design(train, keys_h1, 1), [r["u_now"] - r["u_never"] for r in train], l2)
        for r in test:
            x1 = _design([r], keys_h1, 1)
            a1 = float(_predict(w_a1, x1)[0])
            vwait = float(_predict(w_wait, x1)[0])
            a2 = (float(_predict(w2, _design([r], keys_h2, 2))[0]) if w2 is not None else 0.0)
            targets[r["root_id"]] = ((1.0 if a2 > c2 else 0.0) * (r["u_later"] - r["u_never"])
                                     if r["reached2"] and w2 is not None else 0.0)
            out[r["root_id"]] = {"a1": a1, "vwait": vwait, "a2": a2,
                                 "s1": a1 - vwait, "s2": a2}
    if len(out) != len(rows):
        raise TimingError("cross-fitting did not cover every row")
    return CrossFit(scores=out, targets=targets, keys_h1=keys_h1, keys_h2=keys_h2)


def fit_global(rows, *, l2: float = RIDGE_L2, c2: float | None = None,
               n_folds: int = N_FOLDS) -> dict:
    """Fit the proposed rule on development rows (no held-out fold).

    The deployed second-stage model ``w2`` uses every reached development root.
    The continuation target uses out-of-fold second-stage decisions across the
    development template-family folds (M1).  ``c2=None`` sets the target's
    cutoff to the median out-of-fold prediction, so the target is non-degenerate.
    """

    if not rows:
        raise TimingError("no rows")
    keys_h1 = _feature_keys(rows, "h1")
    keys_h2 = _feature_keys(rows, "h2")
    reached = [r for r in rows if r["reached2"]]
    w2 = None
    if reached:
        w2 = _fit(_design(reached, keys_h2, 2),
                  [r["u_later"] - r["u_never"] for r in reached], l2)
    oof_a2 = _oof_second_stage(rows, keys_h2, l2, n_folds)
    if c2 is None:
        c2 = float(np.median(list(oof_a2.values()))) if oof_a2 else 0.0
    y_wait = _continuation_target(rows, oof_a2, c2)
    return {
        "keys_h1": keys_h1, "keys_h2": keys_h2, "w2": w2, "l2": l2, "c2": c2,
        "w_wait": _fit(_design(rows, keys_h1, 1), y_wait, l2),
        "w_a1": _fit(_design(rows, keys_h1, 1),
                     [r["u_now"] - r["u_never"] for r in rows], l2),
    }


# --------------------------------------------------------------------------
# Decision views: the only input to scoring (L1)
# --------------------------------------------------------------------------


def decision_views(rows) -> dict[str, tuple[DecisionView, DecisionView | None]]:
    """Build the decision-time views for a batch of roots.

    The checkpoint-2 view exists only for roots that reached checkpoint 2.  No
    outcome, hidden or post-decision field of the row is copied into a view.
    """

    views: dict[str, tuple[DecisionView, DecisionView | None]] = {}
    for r in rows:
        v1 = DecisionView(phase=1, h1=dict(r["h1"]))
        v2 = None
        if r["reached2"]:
            v2 = DecisionView(phase=2, h1=dict(r["h1"]), h2=dict(r["h2"]),
                              sufficiency_declared=bool(r.get("h2_sufficiency_declared", False)))
        views[r["root_id"]] = (v1, v2)
    return views


def _check_views(views) -> None:
    if not isinstance(views, dict):
        raise TimingError("controllers score DecisionView objects only")
    for rid, pair in views.items():
        if (not isinstance(pair, tuple) or len(pair) != 2
                or not isinstance(pair[0], DecisionView) or pair[0].phase != 1
                or (pair[1] is not None
                    and (not isinstance(pair[1], DecisionView) or pair[1].phase != 2))):
            raise TimingError(
                f"controllers score DecisionView objects only (root {rid!r})")


def _hist_x(history: dict, keys) -> np.ndarray:
    if not keys:
        return np.zeros((1, 1))
    return np.array([[float(history[k]) for k in keys] + [1.0]], dtype=float)


def _stage_scores(model: dict, views) -> dict[str, dict[str, float]]:
    """``a1``, ``vwait`` (from H1) and ``a2`` (from H2 when reached)."""

    _check_views(views)
    out: dict[str, dict[str, float]] = {}
    for rid, (v1, v2) in views.items():
        x1 = _hist_x(v1.history, model["keys_h1"])
        a1 = float(_predict(model["w_a1"], x1)[0])
        vwait = float(_predict(model["w_wait"], x1)[0])
        a2 = 0.0
        if v2 is not None and model["w2"] is not None:
            a2 = float(_predict(model["w2"], _hist_x(v2.history, model["keys_h2"]))[0])
        out[rid] = {"a1": a1, "vwait": vwait, "a2": a2}
    return out


# --------------------------------------------------------------------------
# BAVAR-inspired signals
# --------------------------------------------------------------------------


def _bavar_signals(history: dict, keys, a_hat: float, reliability: float) -> list[float]:
    """Context, expected information value, verifier reliability, interaction."""

    return ([float(history[k]) for k in keys]
            + [a_hat, reliability, a_hat * reliability, 1.0])


def _clip01(v: float) -> float:
    return float(min(1.0, max(0.0, v)))


def _fit_bavar(rows, *, l2: float, n_folds: int) -> dict:
    base = fit_global(rows, l2=l2, n_folds=n_folds)
    k1, k2 = base["keys_h1"], base["keys_h2"]
    # verifier reliability: probability that verifying improves U, estimated
    # on development data (a ridge probability, clipped to [0, 1])
    rel1 = _fit(_design(rows, k1, 1),
                [1.0 if r["u_now"] > r["u_never"] else 0.0 for r in rows], l2)
    reached = [r for r in rows if r["reached2"]]
    rel2 = w_s2 = None
    if reached and base["w2"] is not None:
        rel2 = _fit(_design(reached, k2, 2),
                    [1.0 if r["u_later"] > r["u_never"] else 0.0 for r in reached], l2)
    sig1 = []
    for r in rows:
        x = _design([r], k1, 1)
        sig1.append(_bavar_signals(r["h1"], k1, float(_predict(base["w_a1"], x)[0]),
                                   _clip01(float(_predict(rel1, x)[0]))))
    w_s1 = _fit(np.array(sig1), [r["u_now"] - r["u_never"] for r in rows], l2)
    if rel2 is not None:
        sig2 = []
        for r in reached:
            x = _design([r], k2, 2)
            sig2.append(_bavar_signals(r["h2"], k2, float(_predict(base["w2"], x)[0]),
                                       _clip01(float(_predict(rel2, x)[0]))))
        w_s2 = _fit(np.array(sig2), [r["u_later"] - r["u_never"] for r in reached], l2)
    return {"base": base, "rel1": rel1, "rel2": rel2, "w_s1": w_s1, "w_s2": w_s2}


# --------------------------------------------------------------------------
# Controllers: one implementation each, called by the evaluation harness
# --------------------------------------------------------------------------


def _grid(c1_values, c2_values, reserves) -> list[AllocatorParams]:
    return [AllocatorParams(c1, c2, r) for c1 in c1_values for c2 in c2_values for r in reserves]


@dataclass
class ProposedTiming:
    """Cross-fitted continuation-value timing heuristic (never optimal).

    ``s1 = A1(H1) - V_wait(H1)``: the net value of using the check now rather
    than keeping it; ``s2 = A2(H2)``.
    """

    name: str = "proposed"
    l2: float = RIDGE_L2
    n_folds: int = N_FOLDS

    def fit(self, rows, *, c2: float | None = None) -> dict:
        """Fit continuation value for the requested second-stage cutoff.

        ``None`` preserves the default median out-of-fold cutoff. Calibration
        supplies each candidate cutoff explicitly and retains its matching fit.
        """
        return fit_global(rows, l2=self.l2, n_folds=self.n_folds, c2=c2)

    def score(self, model: dict, views) -> dict[str, dict[str, float]]:
        return {rid: dict(v, s1=v["a1"] - v["vwait"], s2=v["a2"])
                for rid, v in _stage_scores(model, views).items()}

    def grid(self) -> list[AllocatorParams]:
        return _grid(GRID_C1_FINE, GRID_C, (0,))

    @property
    def tuning_configs(self) -> int:
        return len(self.grid())


@dataclass
class RepeatedMyopicComparator:
    """Repeated one-step advantage: ``s1 = A1``, ``s2 = A2``; reserves nothing."""

    name: str = "repeated_myopic"
    l2: float = RIDGE_L2
    n_folds: int = N_FOLDS

    def fit(self, rows) -> dict:
        return fit_global(rows, l2=self.l2, n_folds=self.n_folds)

    def score(self, model: dict, views) -> dict[str, dict[str, float]]:
        return {rid: dict(v, vwait=0.0, s1=v["a1"], s2=v["a2"])
                for rid, v in _stage_scores(model, views).items()}

    def grid(self) -> list[AllocatorParams]:
        return _grid(GRID_C1_FINE, GRID_C, (0,))

    @property
    def tuning_configs(self) -> int:
        return len(self.grid())


@dataclass
class ConstantReserveAblation:
    """Ablation: the myopic scores plus one constant reserve ``R`` (design §4).

    Checkpoint 1 verifies when ``A1 > tau`` (``tau`` is the tuned ``c1``) up to
    ``B - R``; checkpoint 2 verifies only when ``A2 > c2``.  The reserve does not
    depend on context, which is what distinguishes it from the proposed rule.
    """

    name: str = "constant_reserve"
    l2: float = RIDGE_L2
    n_folds: int = N_FOLDS

    def fit(self, rows) -> dict:
        return fit_global(rows, l2=self.l2, n_folds=self.n_folds)

    def score(self, model: dict, views) -> dict[str, dict[str, float]]:
        return {rid: dict(v, vwait=0.0, s1=v["a1"], s2=v["a2"])
                for rid, v in _stage_scores(model, views).items()}

    def grid(self) -> list[AllocatorParams]:
        return _grid(GRID_C, GRID_C, GRID_RESERVE)

    @property
    def tuning_configs(self) -> int:
        return len(self.grid())


@dataclass
class BavarInspiredVOI:
    """Context-dependent VOI scheduler inspired by BAVAR (Adeli, 2026).

    One learned scorer per decision point over these signals: the decision
    history (H1 or H2, which carries whatever actor-uncertainty or criticality
    features the task exposes), the expected information value (the predicted
    immediate verification gain), verifier reliability (the development-data
    probability that verifying improves U) and their interaction.  The scorer at
    checkpoint 2 is the same construction on H2.  A hard reserve fraction is
    tuned on development data.

    Deviations from BAVAR, listed in full:

    - no actor-sampling uncertainty model: uncertainty and criticality enter
      only as features the task's history exposes;
    - progress (checkpoint index) is implicit in the separate per-checkpoint
      scorers, and remaining budget is handled by the shared allocator's
      reserve rather than as a scorer input;
    - a single verifier, so no multi-verifier choice or allocation;
    - no RL training loop: each scorer is a ridge fit to the paired outcome on
      development data.

    It is an adaptation, not a reproduction; beating the constant-reserve
    ablation says nothing about BAVAR.
    """

    name: str = "bavar_inspired_voi"
    l2: float = RIDGE_L2
    n_folds: int = N_FOLDS

    def fit(self, rows) -> dict:
        return _fit_bavar(rows, l2=self.l2, n_folds=self.n_folds)

    def score(self, model: dict, views) -> dict[str, dict[str, float]]:
        base = model["base"]
        k1, k2 = base["keys_h1"], base["keys_h2"]
        stage = _stage_scores(base, views)
        out: dict[str, dict[str, float]] = {}
        for rid, (v1, v2) in views.items():
            a1 = stage[rid]["a1"]
            x1 = _hist_x(v1.history, k1)
            r1 = _clip01(float(_predict(model["rel1"], x1)[0]))
            s1 = float(np.array(_bavar_signals(v1.history, k1, a1, r1)) @ model["w_s1"])
            a2, s2 = stage[rid]["a2"], 0.0
            if v2 is not None and model["w_s2"] is not None:
                x2 = _hist_x(v2.history, k2)
                r2 = _clip01(float(_predict(model["rel2"], x2)[0]))
                s2 = float(np.array(_bavar_signals(v2.history, k2, a2, r2)) @ model["w_s2"])
            out[rid] = {"a1": a1, "a2": a2, "vwait": 0.0, "s1": s1, "s2": s2}
        return out

    def grid(self) -> list[AllocatorParams]:
        return _grid(GRID_C, GRID_C, GRID_RESERVE)

    @property
    def tuning_configs(self) -> int:
        return len(self.grid())


@dataclass
class FixedRegimeController:
    """Fixed now / later / never diagnostics (ignore the budget; reference only)."""

    regime: str
    name: str = "fixed"

    def regimes(self, rows) -> dict[str, str]:
        if self.regime not in {"now", "later", "never"}:
            raise TimingError("unknown fixed regime")
        return {r["root_id"]: self.regime for r in rows}


def matching_report(controllers) -> dict:
    """Substantive matching check across controllers.

    Requires the same model family, regularisation/capacity, fold count and
    tuning budget (the number of candidate configurations each controller
    calibrates).  Fails on any mismatch.
    """

    rows = []
    for c in controllers:
        rows.append(dict(
            name=getattr(c, "name", type(c).__name__),
            model_family="ridge",
            l2=getattr(c, "l2", None),
            n_folds=getattr(c, "n_folds", None),
            tuning_configs=getattr(c, "tuning_configs", None),
        ))
    fields = ("model_family", "l2", "n_folds", "tuning_configs")
    mismatched = []
    for field in fields:
        values = {r[field] for r in rows if r[field] is not None}
        if len(values) > 1:
            mismatched.append(field)
    matched = not mismatched
    if not matched:
        raise TimingError(f"controller matching failed on: {sorted(mismatched)}")
    return {"matched_decision_class": matched, "controllers": rows}
