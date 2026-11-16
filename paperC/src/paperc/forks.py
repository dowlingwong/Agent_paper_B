"""Fork design and go/no-go statistics (build runbook P6; BUILD_LIST B8; plan §6 SPT-1 / SPT-3, §6.1).

AI-assisted (Claude, chat session, 16 Nov 2026; revised after review round 1). ENGINEERING_ONLY.

**Design** (Track S's ``selection_draw`` / ``select_forks``, ``r1/tracks/collect.py`` on ``trackS-ops-20261030`` @
``fab88fc``; ported, not imported). Every eligible decision of a root campaign (E1 and E2 rows that are neither
rule-forced nor forced) is a candidate fork point. Poisson sampling with three uniforms ``u`` per point from
``SeedSequence([60003, 0, world code, i, trial, epoch code, design_rep])``: uniform iff u0 < q_uniform; oversample iff
the point is near (|V* - g| <= band_e1 at E1, |m_hat - h| <= band_e2 at E2, centred on the behaviour policy's own
thresholds, as Track S's ``is_near``) and u1 < q_oversample; p_select = 1 - (1 - q_uniform)(1 - q_oversample 1{near})
(``schema.ForkDesign``; ``check_campaign`` recomputes it). Design weights are 1 / p_select. Track S's instrument
arms (ghost / ctrl-only on a third of E1 forks) do not exist in the E-SYN loop: ``channel_arms`` is always false.

**Continuations** (``esyn.sim.ForkSpec``): both arms (E1 execute / skip, E2 keep / discard) x ``reps`` replicates x
the declared continuation policies (plan: r = 2 under 2 policies, 4 continuations per arm). Replicate r of
continuation policy c shares its proposal stream across the arms (common random numbers, as Track S); measurement
noise is independent per arm, which departs from Track S's analysis simulator (see ``esyn.sim``): within-fork
variances, and so precision and power, are conditional on this convention.

**Fork differences** per fork j, continuation policy c, replicate r (Track S ``build_fork_table``):

* ``q``: the total fork Q difference Y_act - Y_not (plan §6: Q(s, execute) - Q(s, skip), keep - discard);
* ``d``: the continuation difference (Y_act - I_act) - (Y_not - I_not), where I is the forked candidate's true
  increment if kept at the fork trial (``CampaignResult.immediate``; Track S's C = y_terminal - immediate_measured,
  without audit noise). It removes the one-step value that a myopic rule already sees. In a world without a
  sequential channel (``strict_null``: fresh keys, non-binding W, independent comparisons) it is 0 in expectation for
  every state **provided the continuation policies' later decisions do not depend on the bookkeeping that differs
  between the arms** (runs left, keeps so far, incumbent measurements): true for static thresholds on the belief
  (N1, N0), false for budget-aware members (a Track S dynamic member reading runs left makes the arms decide
  differently later, so d is non-zero even in ``strict_null``). ``q`` varies with the one-step value in any world.

Which of the two carries the go/no-go floor is a pre-declaration choice for the author (plan §6 names "fork Q
differences"; the runbook's validation expects tau^2 = 0 in the null world, which holds for ``d``, not ``q``). Both are
reported.

**Statistics.**

* ``fork_means``: Hajek (sum w D / sum w), Horvitz-Thompson per eligible decision (sum w D / N, N = all eligible
  decisions of the roots; exactly design-unbiased) and the unweighted mean (biased under the oversample).
* ``tau2``: tau^2_hat = (between-fork variance of D_bar_j) - (mean within-fork s.e.^2), pooled over E1 and E2 forks
  or per epoch (``epoch=``). The pooled value includes the difference between the epochs' mean differences (a
  constant-sign effect that differs between E1 and E2, not a state-dependent sign change); the per-epoch values do
  not. D_bar_j averages the C x R
  cells; s.e.^2_j = (1 / C^2) sum_c s_jc^2 / R with s_jc^2 the replicate variance under policy c (R >= 2), so it is
  unbiased for the conditional variance of D_bar_j given the state. Between-fork variance and the mean s.e.^2 are
  design-weighted (1 / p_select); the between variance carries the small-sample factor k / (k - 1), k = Kish's
  effective number of forks. The estimate is not truncated (it can be negative); ``max(0, .)`` is shown alongside.
  Interval: percentile cluster bootstrap over root instances (forks of one root share its history).
* ``n6_value``: the cross-fitted value of the N6 improvement step (plan §7.1: multi-step supervised regression on
  fork Q differences, one approximate policy-improvement step). Root instances are split into ``folds``; on the
  other folds a ridge regression of q_bar on the state features is fitted per epoch, **unweighted** (plan §6.1: 1 / p
  only adds variance when fitting N6); pi'(s) acts (execute / keep) iff f_hat(s) > 0. On each held-out fork the gain
  of pi' over the behaviour policy's logged action is 1{pi' != b} (+1 if pi' acts, -1 otherwise) q_bar_j: the gain of
  deviating from the behaviour at that one decision and then following the continuation policies. Reported per
  eligible decision (Hajek mean) and per root (HT total of these one-decision gains / roots: **not** the value of
  running pi' for a whole campaign). An epoch with fewer than ``min_train`` training forks keeps the behaviour action
  (counted).

  **Estimand and intervals.** The point estimate targets the population value of the fitted rules, V(f_1 .. f_K) =
  sum_k W_k / W * E_s[gain_k(s)] (``rule_gain``): each fold's forks are independent of the model that predicts them.
  Two cluster-bootstrap intervals over roots:

  - ``ci_refit_*`` (**primary**, ``ci_per_decision`` / ``ci_per_campaign``): refitting bootstrap; all copies of a
    root share the root's fold (as Track S's ``refitting_bootstrap``), so no held-out root is ever in its own
    training set. A replicate holds about 63 % distinct roots, so refitted models see less information and the
    interval sits below the estimate and is wide. On E-SYN (P6 validation) it covers both the value of the
    collection's own fitted rules and the procedure's expected value in 0.90-1.00 of collections: conservative;
  - ``ci_fixed_*``: the cross-fitted decisions held fixed. Narrower, but its standard error misses that each fold's
    model was trained on the other folds' forks, so it under-covers (0.80-0.90 on E-SYN). Reported, not used for a
    decision.

Randomness of the analysis (bootstrap, fold assignment) comes from ``numpy.random.default_rng([61001, ...])``; key
61001 is claimed in the seed registry (block ``paperc_train_seeds``). E-SYN results are implementation checks, never
evidence about the real loop.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np

from paperc import schema as S
from paperc.esyn import sim
from paperc.esyn.extra import ESynWorld

ANALYSIS_KEY = 61_001
ACT = {"E1": "execute", "E2": "keep"}
NOT = {"E1": "skip", "E2": "discard"}
FEATURES = {
    "E1": ("v_star", "tau", "sigma", "runs_frac", "slots_frac", "keeps_so_far", "key_seen", "incumbent_obs"),
    "E2": ("m_hat", "candidate_delta_hat", "tau", "sigma", "runs_frac", "slots_frac", "keeps_so_far", "key_seen",
           "candidate_obs", "incumbent_obs"),
}


class ForkError(ValueError):
    pass


# ================================================================ design

@dataclass(frozen=True)
class Design:
    q_uniform: float
    q_oversample: float
    band_e1: float               # near band on V* - g (raw units)
    band_e2: float               # near band on m_hat - h (raw units)
    g: float                     # the behaviour policy's own thresholds (centre of the band)
    h: float
    belief: str = "a2u"
    design_rep: int = 0          # redraws the selection uniforms (validation only)

    def __post_init__(self) -> None:
        if not (0.0 <= self.q_uniform <= 1.0 and 0.0 <= self.q_oversample <= 1.0):
            raise ForkError("inclusion rates must lie in [0, 1]")
        if self.q_uniform == 0.0 and self.q_oversample == 0.0:
            raise ForkError("at least one inclusion rate must be positive")
        if self.band_e1 < 0 or self.band_e2 < 0:
            raise ForkError("bands must be non-negative")


@dataclass
class ForkPoint:
    fork_id: str
    instance: int
    trial: int
    epoch: str
    step: int
    behaviour_action: str
    index: float                 # V* (E1) or m_hat (E2) of the belief
    margin: float                # index - g or index - h
    design: S.ForkDesign
    features: dict


def eligible_rows(root_rows: list[dict]) -> list[dict]:
    return [r for r in root_rows if r["identity"]["epoch"] in ("E1", "E2") and not r["state"]["rule_forced"]
            and not r["action"]["forced"] and not r["identity"]["branch_path"]]


def _features(r: dict, belief: str) -> dict:
    st, env, ep = r["state"], r["env"], r["identity"]["epoch"]
    f = st["forecasts"][belief]
    base = {"v_star": f["v_star"], "m_hat": f["m_hat"], "tau": f["tau"], "sigma": f["sigma"],
            "candidate_delta_hat": st["candidate_delta_hat"], "runs_frac": st["runs_left"] / env["W"],
            "slots_frac": st["slots_left"] / env["llm_cap"], "keeps_so_far": st["keeps_so_far"],
            "key_seen": float(st["key_seen"]), "incumbent_obs": st["incumbent_obs"],
            "candidate_obs": st["candidate_obs"]}
    out = {k: base[k] for k in FEATURES[ep]}
    for k, v in out.items():
        if v is None or not math.isfinite(float(v)):
            raise ForkError(f"{r['identity']['campaign_id']}#{r['identity']['step_index']}: feature {k} is {v!r}")
    return {k: float(v) for k, v in out.items()}


def selection_uniforms(world: ESynWorld, instance: int, trial: int, epoch: str, design_rep: int = 0) -> np.ndarray:
    return np.random.default_rng(sim.fork_seed(world, instance, trial, epoch, 0, design_rep)).random(3)


def p_select(q_uniform: float, q_oversample: float, near: bool) -> float:
    return 1.0 - (1.0 - q_uniform) * (1.0 - (q_oversample if near else 0.0))


def select_forks(world: ESynWorld, instance: int, root_rows: list[dict], design: Design,
                 select_all: bool = False) -> list[ForkPoint]:
    """Poisson-sample the eligible decisions of one root (``select_all``: every eligible decision, p_select = 1,
    for oracle populations)."""
    out = []
    for r in eligible_rows(root_rows):
        ep = r["identity"]["epoch"]
        trial = int(r["state"]["proposal_hash"][1:])
        f = r["state"]["forecasts"][design.belief]
        idx = f["v_star"] if ep == "E1" else f["m_hat"]
        margin = idx - (design.g if ep == "E1" else design.h)
        near = abs(margin) <= (design.band_e1 if ep == "E1" else design.band_e2)
        if select_all:
            uni, over, ps, rule = True, False, 1.0, "uniform"
            fd = S.ForkDesign(selection_rule=rule, q_uniform=1.0, q_oversample=0.0, near_threshold=near,
                              uniform=True, oversample=False, p_select=1.0, channel_arms=False, replicate=1)
        else:
            u = selection_uniforms(world, instance, trial, ep, design.design_rep)
            uni, over = bool(u[0] < design.q_uniform), bool(near and u[1] < design.q_oversample)
            if not (uni or over):
                continue
            rule = "both" if (uni and over) else ("uniform" if uni else "oversample")
            ps = p_select(design.q_uniform, design.q_oversample, near)
            fd = S.ForkDesign(selection_rule=rule, q_uniform=design.q_uniform, q_oversample=design.q_oversample,
                              near_threshold=near, uniform=uni, oversample=over, p_select=ps, channel_arms=False,
                              replicate=1)
        out.append(ForkPoint(fork_id=f"f{trial:03d}{ep}", instance=int(instance), trial=trial, epoch=ep,
                             step=r["identity"]["step_index"], behaviour_action=r["action"]["action"],
                             index=float(idx), margin=float(margin), design=fd, features=_features(r, design.belief)))
    return out


# ================================================================ collection

@dataclass
class ForkTable:
    world: str
    behaviour: str
    continuations: list
    reps: int
    fork_id: list
    instance: np.ndarray            # root instance (cluster)
    trial: np.ndarray
    e1: np.ndarray                  # bool
    index: np.ndarray
    margin: np.ndarray
    near: np.ndarray
    p_select: np.ndarray
    b_act: np.ndarray               # bool: the behaviour policy acted (execute / keep) at the fork point
    features: list                  # dict per fork
    q: np.ndarray                   # (n, C, R): Y_act - Y_not
    d: np.ndarray                   # (n, C, R): (Y_act - I_act) - (Y_not - I_not)
    n_eligible: dict                # instance -> eligible decisions of its root
    rows: list = field(default_factory=list)
    n_eligible_epoch: dict = field(default_factory=dict)   # instance -> {"E1": n, "E2": n}

    @property
    def w(self) -> np.ndarray:
        return 1.0 / self.p_select

    @property
    def n_roots(self) -> int:
        return len(self.n_eligible)

    def __len__(self) -> int:
        return len(self.fork_id)

    def eligible(self, epoch: str | None = None) -> int:
        """Eligible decisions of all roots (of one epoch): the HT denominator."""
        if epoch is None:
            return int(sum(self.n_eligible.values()))
        return int(sum(v[epoch] for v in self.n_eligible_epoch.values()))

    def subset(self, mask) -> "ForkTable":
        """A subset of the forks over the same roots: every root's eligible counts are kept, so HT denominators
        (eligible decisions, roots) stay those of the collection."""
        m = np.asarray(mask)
        idx = np.flatnonzero(m) if m.dtype == bool else m
        return ForkTable(self.world, self.behaviour, self.continuations, self.reps,
                         [self.fork_id[i] for i in idx], self.instance[idx], self.trial[idx], self.e1[idx],
                         self.index[idx], self.margin[idx], self.near[idx], self.p_select[idx], self.b_act[idx],
                         [self.features[i] for i in idx], self.q[idx], self.d[idx], dict(self.n_eligible),
                         n_eligible_epoch=dict(self.n_eligible_epoch))

    def epoch_rows(self, epoch: str | None) -> np.ndarray:
        if epoch is None:
            return np.arange(len(self))
        if epoch not in ("E1", "E2"):
            raise ForkError(f"epoch must be 'E1', 'E2' or None, got {epoch!r}")
        return np.flatnonzero(self.e1 == (epoch == "E1"))


def fork_cells(world: ESynWorld, behaviour, instance: int, fp: ForkPoint, continuations, reps: int,
               record: bool = False):
    """q and d (C x R) of one fork point, plus the recorded fork rows when ``record``."""
    C = len(continuations)
    q, d = np.full((C, reps), np.nan), np.full((C, reps), np.nan)
    rows = []
    for c, cont in enumerate(continuations):
        for r in range(1, reps + 1):
            res = {}
            for arm in (ACT[fp.epoch], NOT[fp.epoch]):
                design = replace(fp.design, replicate=r) if record else None
                spec = sim.ForkSpec(trial=fp.trial, epoch=fp.epoch, arm=arm, continuation=cont, cont_index=c,
                                    replicate=r, fork_id=fp.fork_id, design=design)
                res[arm] = sim.run_campaign(world, behaviour, instance, record=record, fork=spec)
                if res[arm].fork_step != fp.step:
                    raise ForkError(f"{fp.fork_id} of instance {instance}: fork step {res[arm].fork_step} != "
                                    f"root step {fp.step}")
                rows += res[arm].rows
            a, b = res[ACT[fp.epoch]], res[NOT[fp.epoch]]
            q[c, r - 1] = a.Y - b.Y
            d[c, r - 1] = (a.Y - a.immediate) - (b.Y - b.immediate)
    return q, d, rows


def collect(world: ESynWorld, behaviour, instances, design: Design, continuations, *, reps: int = 2,
            record: bool = False, select_all: bool = False) -> ForkTable:
    """Roots under ``behaviour`` on ``instances``; forks selected by ``design``; both arms x ``reps`` x
    ``continuations``. ``record`` keeps the root and fork rows (``schema.check_campaign`` can check them)."""
    if reps < 1 or not continuations:
        raise ForkError("need reps >= 1 and at least one continuation policy")
    cols = {k: [] for k in ("fork_id", "instance", "trial", "e1", "index", "margin", "near", "p_select", "b_act",
                            "features", "q", "d")}
    n_elig, n_elig_ep, rows = {}, {}, []
    for i in instances:
        root = sim.run_campaign(world, behaviour, int(i), record=True)
        el = eligible_rows(root.rows)
        n_elig[int(i)] = len(el)
        n_elig_ep[int(i)] = {ep: sum(r["identity"]["epoch"] == ep for r in el) for ep in ("E1", "E2")}
        if record:
            rows += root.rows
        for fp in select_forks(world, int(i), root.rows, design, select_all=select_all):
            q, d, fr = fork_cells(world, behaviour, int(i), fp, continuations, reps, record=record)
            rows += fr
            for k, v in (("fork_id", fp.fork_id), ("instance", int(i)), ("trial", fp.trial),
                         ("e1", fp.epoch == "E1"), ("index", fp.index), ("margin", fp.margin),
                         ("near", fp.design.near_threshold), ("p_select", fp.design.p_select),
                         ("b_act", fp.behaviour_action == ACT[fp.epoch]), ("features", fp.features), ("q", q),
                         ("d", d)):
                cols[k].append(v)
    C = len(continuations)
    arr = lambda k, dt=float: np.asarray(cols[k], dtype=dt)      # noqa: E731
    return ForkTable(world=world.name, behaviour=behaviour.name, continuations=[c.name for c in continuations],
                     reps=reps, fork_id=cols["fork_id"], instance=arr("instance", int), trial=arr("trial", int),
                     e1=arr("e1", bool), index=arr("index"), margin=arr("margin"), near=arr("near", bool),
                     p_select=arr("p_select"), b_act=arr("b_act", bool), features=cols["features"],
                     q=np.asarray(cols["q"], float).reshape(-1, C, reps),
                     d=np.asarray(cols["d"], float).reshape(-1, C, reps), n_eligible=n_elig, rows=rows,
                     n_eligible_epoch=n_elig_ep)


# ================================================================ statistics

def fork_diffs(ft: ForkTable, target: str = "d", cont: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(D_bar_j, s.e.^2_j) for every fork of ``ft`` (subset by epoch with ``ft.subset(ft.epoch_rows(...))``)."""
    # mean over the C x R cells, and (1 / C^2) sum_c s_jc^2 / R
    if target not in ("q", "d"):
        raise ForkError(f"target must be 'q' or 'd', got {target!r}")
    A = ft.q if target == "q" else ft.d
    if cont is not None:
        A = A[:, [cont], :]
    C, R = A.shape[1], A.shape[2]
    if R < 2:
        raise ForkError("within-fork variance needs reps >= 2")
    if np.isnan(A).any():
        raise ForkError("missing fork cells")
    dbar = A.mean(axis=(1, 2))
    se2 = A.var(axis=2, ddof=1).sum(axis=1) / (R * C * C)
    return dbar, se2


def _kish(w: np.ndarray) -> float:
    return float(w.sum() ** 2 / (w * w).sum())


def tau2_point(dbar: np.ndarray, se2: np.ndarray, w: np.ndarray) -> dict:
    n = len(dbar)
    if n < 2:
        return {"tau2": float("nan"), "between": float("nan"), "mean_se2": float("nan"), "n": n}
    W = w.sum()
    m = float((w * dbar).sum() / W)
    k = _kish(w)
    between = float((w * (dbar - m) ** 2).sum() / W) * (k / (k - 1) if k > 1 else float("nan"))
    mse2 = float((w * se2).sum() / W)
    return {"tau2": between - mse2, "between": between, "mean_se2": mse2, "mean": m, "n": n, "kish": k}


def _boot_index(instances: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """One cluster-bootstrap draw: row indices and a copy id per row. N6 folds use the original root id instead
    (``ft.instance[idx]``), so that every copy of a root lies in the root's fold."""
    uniq = np.unique(instances)
    pos = {u: np.flatnonzero(instances == u) for u in uniq}
    draw = rng.choice(uniq, size=len(uniq), replace=True)
    idx = np.concatenate([pos[u] for u in draw])
    cl = np.concatenate([np.full(len(pos[u]), j) for j, u in enumerate(draw)])
    return idx, cl


def tau2(ft: ForkTable, target: str = "d", cont: int | None = None, *, epoch: str | None = None, B: int = 500,
         seed: int | tuple = (0,)) -> dict:
    """tau^2_hat with a percentile cluster-bootstrap 95 % interval (clusters: root instances); ``epoch`` restricts to
    E1 or E2 forks."""
    ft = ft.subset(ft.epoch_rows(epoch)) if epoch is not None else ft
    dbar, se2 = fork_diffs(ft, target, cont)
    w = ft.w
    out = tau2_point(dbar, se2, w)
    rng = np.random.default_rng([ANALYSIS_KEY, 1, *np.atleast_1d(seed)])
    if len(np.unique(ft.instance)) >= 2 and B > 0:
        draws = []
        for _ in range(B):
            idx, _ = _boot_index(ft.instance, rng)
            draws.append(tau2_point(dbar[idx], se2[idx], w[idx])["tau2"])
        draws = np.asarray(draws)
        out["ci"] = (float(np.nanquantile(draws, 0.025)), float(np.nanquantile(draws, 0.975)))
    else:
        out["ci"] = None
    out["tau2_plus"] = max(0.0, out["tau2"]) if math.isfinite(out["tau2"]) else out["tau2"]
    out["target"], out["cont"], out["epoch"] = target, cont, epoch
    out["clusters"] = int(len(np.unique(ft.instance)))
    return out


def fork_means(ft: ForkTable, target: str = "q", cont: int | None = None, epoch: str | None = None) -> dict:
    """Hajek, HT (per eligible decision of the epoch) and unweighted means of the fork differences."""
    N = ft.eligible(epoch)
    ft = ft.subset(ft.epoch_rows(epoch)) if epoch is not None else ft
    A = ft.q if target == "q" else ft.d
    dbar = (A if cont is None else A[:, [cont], :]).mean(axis=(1, 2))
    w = ft.w
    return {"hajek": float((w * dbar).sum() / w.sum()) if len(dbar) else float("nan"),
            "ht": float((w * dbar).sum() / N) if N else float("nan"),
            "unweighted": float(dbar.mean()) if len(dbar) else float("nan"), "n_forks": len(dbar),
            "n_eligible": N}


# ---------------------------------------------------------------- N6

def _ridge_fit(X: np.ndarray, y: np.ndarray, alpha: float):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd = np.where(sd > 0, sd, 1.0)
    Z = (X - mu) / sd
    Zc = np.column_stack([np.ones(len(Z)), Z])
    P = np.eye(Zc.shape[1]) * alpha
    P[0, 0] = 0.0
    beta = np.linalg.solve(Zc.T @ Zc + P, Zc.T @ y)
    return mu, sd, beta


def _ridge_predict(model, X: np.ndarray) -> np.ndarray:
    mu, sd, beta = model
    return np.column_stack([np.ones(len(X)), (X - mu) / sd]) @ beta


def _feature_matrix(ft: ForkTable, rows: np.ndarray, epoch: str) -> np.ndarray:
    return np.array([[ft.features[i][k] for k in FEATURES[epoch]] for i in rows], dtype=float).reshape(-1, len(FEATURES[epoch]))


def _assign_folds(instances: np.ndarray, folds: int, rng: np.random.Generator) -> np.ndarray:
    uniq = np.unique(instances)
    perm = rng.permutation(len(uniq))
    fold_of = {u: int(perm[j] % folds) for j, u in enumerate(uniq)}
    return np.array([fold_of[u] for u in instances])


def n6_point(ft: ForkTable, rows: np.ndarray, clusters: np.ndarray, *, folds: int, alpha: float, min_train: int,
             rng: np.random.Generator, qbar: np.ndarray) -> dict:
    """Cross-fitted pi' on the forks ``rows``; its gain over the behaviour. ``clusters`` assigns folds: pass the
    original root instance for every row (in the bootstrap, all copies of a root then share its fold)."""
    fold_row = _assign_folds(clusters, folds, rng)
    act = np.zeros(len(rows), dtype=bool)
    fallback = 0
    models = {}
    for k in range(folds):
        te = fold_row == k
        if not te.any():
            continue
        tr = ~te
        for ep, is_e1 in (("E1", True), ("E2", False)):
            te_e = te & (ft.e1[rows] == is_e1)
            tr_e = tr & (ft.e1[rows] == is_e1)
            model = None
            if tr_e.sum() >= min_train:
                model = _ridge_fit(_feature_matrix(ft, rows[tr_e], ep), qbar[rows][tr_e], alpha)
            models[(k, ep)] = model
            if not te_e.any():
                continue
            if model is None:
                act[te_e] = ft.b_act[rows][te_e]
                fallback += int(te_e.sum())
            else:
                act[te_e] = _ridge_predict(model, _feature_matrix(ft, rows[te_e], ep)) > 0
    b = ft.b_act[rows]
    gain = (act != b) * np.where(act, 1.0, -1.0) * qbar[rows]
    w = ft.w[rows]
    fold_w = {k: float(w[fold_row == k].sum()) for k in range(folds)}
    fold_roots = {k: len(np.unique(clusters[fold_row == k])) for k in range(folds)}
    return {"per_decision": float((w * gain).sum() / w.sum()), "flip_rate": float((w * (act != b)).sum() / w.sum()),
            "gain_total": float((w * gain).sum()), "fallback": fallback, "act": act, "gain": gain,
            "fold_row": fold_row, "models": models, "fold_weight": fold_w, "fold_roots": fold_roots}


def rule_gain(fit: dict, features_by_epoch: dict, b_act_by_epoch: dict, q_by_epoch: dict) -> tuple[float, float]:
    """Population value of fitted cross-fitted rules (``fit`` from ``n6_point``) on evaluation states that none of
    them was trained on: (per eligible decision, weighting fold k by its held-out design weight W_k / W;
    per root, weighting fold k by its share of roots, divided by the evaluation roots ``q_by_epoch['roots']``).
    ``features_by_epoch[ep]``: (n_ep, len(FEATURES[ep])) matrix; ``b_act_by_epoch[ep]``: behaviour acted;
    ``q_by_epoch[ep]``: the states' (oracle) total fork differences. A fold model that is None keeps the behaviour."""
    W = sum(fit["fold_weight"].values())
    R = sum(fit["fold_roots"].values())
    n_states = sum(len(q_by_epoch[ep]) for ep in ("E1", "E2"))
    per_dec = per_root = 0.0
    for k in fit["fold_weight"]:
        tot = 0.0
        for ep in ("E1", "E2"):
            X, b, q = features_by_epoch[ep], b_act_by_epoch[ep], q_by_epoch[ep]
            if len(q) == 0:
                continue
            m = fit["models"].get((k, ep))
            act = b.copy() if m is None else _ridge_predict(m, X) > 0
            tot += float(((act != b) * np.where(act, 1.0, -1.0) * q).sum())
        per_dec += fit["fold_weight"][k] / W * tot / n_states
        per_root += fit["fold_roots"][k] / R * tot / q_by_epoch["roots"]
    return per_dec, per_root


def n6_value(ft: ForkTable, *, folds: int = 5, alpha: float = 1.0, min_train: int = 10, B: int = 300,
             seed: int | tuple = (0,), refit: bool = True) -> dict:
    """Cross-fitted value of the N6 improvement step over the behaviour policy (see the module docstring). Returns
    the point estimates, the refitting interval (``ci_refit_*``; primary, as ``ci_per_*``, when ``refit``), the
    fixed-decision interval (``ci_fixed_*``; ``ci_per_*`` only when ``refit`` is false, with ``ci_kind``) and the
    fitted rules (``fit``) for population evaluation with ``rule_gain``."""
    if len(ft) == 0:
        raise ForkError("no forks")
    qbar = ft.q.mean(axis=(1, 2))
    rng = np.random.default_rng([ANALYSIS_KEY, 2, *np.atleast_1d(seed)])
    rows = np.arange(len(ft))
    est = n6_point(ft, rows, ft.instance, folds=folds, alpha=alpha, min_train=min_train, rng=rng, qbar=qbar)
    n_roots = ft.n_roots
    out = {"per_decision": est["per_decision"], "per_campaign": est["gain_total"] / n_roots,
           "flip_rate": est["flip_rate"], "fallback_forks": est["fallback"], "n_forks": len(ft), "n_roots": n_roots,
           "folds": folds, "alpha": alpha, "fit": est}
    if B > 0 and len(np.unique(ft.instance)) >= 2:
        w, gain = ft.w, est["gain"]
        fd, fc, rd, rc = [], [], [], []
        for _ in range(B):
            idx, _ = _boot_index(ft.instance, rng)
            fd.append(float((w[idx] * gain[idx]).sum() / w[idx].sum()))
            fc.append(float((w[idx] * gain[idx]).sum() / n_roots))
            if refit:
                e = n6_point(ft, idx, ft.instance[idx], folds=folds, alpha=alpha, min_train=min_train, rng=rng,
                             qbar=qbar)
                rd.append(e["per_decision"])
                rc.append(e["gain_total"] / n_roots)
        q = lambda x: (float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975)))     # noqa: E731
        out["ci_fixed_per_decision"], out["ci_fixed_per_campaign"] = q(fd), q(fc)
        if refit:
            out["ci_refit_per_decision"], out["ci_refit_per_campaign"] = q(rd), q(rc)
            out["ci_per_decision"], out["ci_per_campaign"], out["ci_kind"] = q(rd), q(rc), "refit"
        else:
            out["ci_per_decision"], out["ci_per_campaign"], out["ci_kind"] = q(fd), q(fc), "fixed"
    return out
