"""D.3 replication arms: the decision engines of FIXR3 (gap G3) and EGATE (gap G4). AI-assisted (Claude).

ENGINEERING_ONLY until a signed D.3 note cites the reviewed unit.  Source: the D.3 pre-declaration revision 4
(``docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md``, branch ``mac-d3-predecl-r4-20261127``) §5.4
(FIXR3), §5.5 (EGATE), §4.1 (replicate seeds), §5 "Run accounting" and §13 items 15, 19.

**What these engines are, and what they are not.**  A replicate arm runs one configuration several times per step,
which the pinned harness (``a3fedbbd``) cannot do from a ``Controller.decide`` (its only multi-run action is verify,
2 r runs of the KG verify response).  Each engine here is therefore a harness-free state machine that decides one
*step* (one executed proposal) from runs it requests through a ``run`` callable, and charges every run through the
campaign's single W counter (``r1.c3.accounting.ChargedRunCounter``, G8), which refuses a step it cannot fund
before the step starts.  How the G1 runner reaches it from a harness campaign (a harness action that charges like
verify, i.e. a new reviewed harness pin, §5 "Run accounting" and §12 G3/G4) is **not** part of this unit.

``run(role, config_sha256, seed, j) -> RunOutcome`` runs ``config_sha256`` once with train seed = split seed =
``seed``; ``role`` is ``"candidate"`` or ``"incumbent"``.  Metrics are oriented by ``maximize`` (all seven D.3 nodes
declare ``metric_direction: maximize``) before any difference is taken.

Rule layer: off for FIXR3 and EGATE as built (§5; §13 item 21; ``d3_controllers.D3_RULE_LAYER``); the E1 side of
both arms is ``d3_controllers.RuleLayerController(arm=..., rule_layer=False)``, which executes every proposal.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Callable, Protocol

from r1.c3 import d3_analysis as D3
from r1.c3.accounting import ChargedRunCounter, UnfundableStep

FIXR3_VERSION = "d3_fixr3/v1"
FIXR3_R = 3            # replicates per executed proposal (R1-BX-PROPOSED-CONFIRM (D7))
FIXR3_ALPHA = 0.05     # one-sided Welch t-test (R1-BX-PROPOSED-CONFIRM (D7); §13 item 5)

EGATE_VERSION = "d3_egate/v1"
EGATE_ACTION_VERSION = "verify:pace"   # the declared action version (BUILD_REVIEW_20261012 finding 16)

DECISIONS = ("kept", "discarded", "failed_invalid")


@dataclass(frozen=True)
class RunOutcome:
    success: bool
    metric: float | None = None
    seconds: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise ValueError("success must be a boolean")
        if self.success and (self.metric is None or not math.isfinite(float(self.metric))):
            raise ValueError("a successful run has a finite metric (a non-finite result is a failed run)")


class RunFn(Protocol):
    def __call__(self, *, role: str, config_sha256: str, seed: int, j: int) -> RunOutcome: ...


def replicate_seed(instance_seed: int, j: int) -> int:
    """Train seed = split seed of replicate j of an instance (§4.1): j = 0 is the instance seed itself, j = 1..9 are
    ``d3_analysis.replicate_seeds`` (6500 + 10 i + j; smoke seeds 6300 + 10 (s - 6300) + j)."""
    if not isinstance(j, int) or isinstance(j, bool) or not 0 <= j <= D3.MAX_REPLICATE_J:
        raise ValueError(f"replicate j must lie in 0..{D3.MAX_REPLICATE_J}")
    if j == 0:
        if instance_seed not in D3.INSTANCE_SEEDS and instance_seed not in D3.SMOKE_SEEDS:
            raise ValueError("not a declared D.3 instance or smoke seed")
        return int(instance_seed)
    return D3.replicate_seeds(int(instance_seed))[j - 1]


@dataclass
class StepResult:
    """One executed proposal of a replicate arm."""

    decision: str                     # "kept" | "discarded" | "failed_invalid"
    runs_charged: int
    replicates: list[dict]            # G8 entries for extra.control.replicates (the j = 0 candidate run excluded)
    display_metric: float | None      # §13 item 15: the mean of the successful candidate replicate metrics
    detail: dict = field(default_factory=dict)


def welch_one_sided(cand: list[float], inc: list[float]) -> dict:
    """One-sided Welch t-test of mean(cand) > mean(inc).  Both sample variances zero -> undefined (``p`` None)."""
    n1, n2 = len(cand), len(inc)
    if n1 < 2 or n2 < 2:
        raise ValueError("Welch needs at least two runs per side")
    # statistics.variance is exact (rational arithmetic), so identical runs give a variance of exactly 0.
    m1, m2 = statistics.fmean(cand), statistics.fmean(inc)
    v1, v2 = float(statistics.variance(cand)), float(statistics.variance(inc))
    out = {"mean_candidate": m1, "mean_incumbent": m2, "var_candidate": v1, "var_incumbent": v2,
           "n_candidate": n1, "n_incumbent": n2}
    se2 = v1 / n1 + v2 / n2
    if se2 == 0.0:
        return {**out, "t": None, "df": None, "p": None, "zero_variance": True}
    from scipy.stats import t as student_t
    t = (m1 - m2) / math.sqrt(se2)
    df = se2 ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1))
    return {**out, "t": t, "df": df, "p": float(student_t.sf(t, df)), "zero_variance": False}


def _oriented(metric: float, maximize: bool) -> float:
    return float(metric) if maximize else -float(metric)


class Fixr3Engine:
    """FIXR3 (§5.4): r = 3 replicates per executed proposal on seeds j = 0, 1, 2; keep iff a one-sided Welch test
    of mean(candidate) > mean(incumbent) rejects at alpha = 0.05 (p <= alpha); the incumbent's three runs are its own
    replicate runs as a candidate, so no incumbent run is ever made.  The first valid trial is run three times and
    kept without a test.  Any failed replicate makes the candidate ``failed_invalid`` (charged for the runs used, the
    rest not run); a first trial with a failed replicate is ``failed_invalid`` and the next proposal becomes the
    first trial.  Both variances zero -> no keep (``zero_variance``, counted).  A step needs 3 runs: with fewer left
    it is refused before it starts (``UnfundableStep``; the campaign ends ``no_fundable_candidate``)."""

    arm = "FIXR3"
    version = FIXR3_VERSION

    def __init__(self, instance_seed: int, *, maximize: bool = True, r: int = FIXR3_R, alpha: float = FIXR3_ALPHA):
        if r != FIXR3_R or alpha != FIXR3_ALPHA:
            raise ValueError("FIXR3's r = 3 and alpha = 0.05 are declared (§5.4); another value is another arm")
        self.instance_seed, self.maximize = int(instance_seed), bool(maximize)
        self.seeds = tuple(replicate_seed(self.instance_seed, j) for j in range(FIXR3_R))
        self.incumbent: str | None = None
        self.incumbent_metrics: list[float] | None = None   # oriented, j = 0, 1, 2
        self.zero_variance_cases = 0
        self.steps = 0

    def step(self, config_sha256: str, run: RunFn, counter: ChargedRunCounter) -> StepResult:
        counter.require(FIXR3_R)  # refused before it starts; nothing is charged
        self.steps += 1
        metrics: list[float] = []
        entries: list[dict] = []
        raw: list[float] = []
        for j, seed in enumerate(self.seeds):
            out = run(role="candidate", config_sha256=config_sha256, seed=seed, j=j)
            counter.charge(kind="trial" if j == 0 else "replicate", role="candidate", seed=seed,
                           config_sha256=config_sha256, success=out.success, j=j,
                           metric=out.metric if out.success else None, seconds=out.seconds)
            if j > 0:
                entries.append({"role": "candidate", "j": j, "seed": seed, "success": out.success, "charged": True,
                                "metric": out.metric if out.success else None})
            if not out.success:
                return StepResult("failed_invalid", j + 1, entries, _mean(raw),
                                  {"version": self.version, "failed_at_j": j, "first_trial": self.incumbent is None})
            raw.append(float(out.metric))
            metrics.append(_oriented(out.metric, self.maximize))
        detail = {"version": self.version, "first_trial": self.incumbent is None, "seeds": list(self.seeds)}
        if self.incumbent is None:
            self.incumbent, self.incumbent_metrics = config_sha256, metrics
            return StepResult("kept", FIXR3_R, entries, _mean(raw), {**detail, "test": None})
        test = welch_one_sided(metrics, list(self.incumbent_metrics))
        if test["zero_variance"]:
            self.zero_variance_cases += 1
            keep = False
        else:
            keep = test["p"] <= FIXR3_ALPHA
        if keep:
            self.incumbent, self.incumbent_metrics = config_sha256, metrics
        return StepResult("kept" if keep else "discarded", FIXR3_R, entries, _mean(raw),
                          {**detail, "test": test, "alpha": FIXR3_ALPHA})


class EgateEngine:
    """EGATE (§5.5): the repository's ``PaceStyleGate`` as on ``main`` (alpha = 0.1, clip = 0.05, max_pairs = 8) as a
    closed-loop E2 rule.

    One step: pair j = 0, 1, ... runs the candidate at replicate seed j and, if the incumbent has no run at seed j,
    the incumbent too (candidate first; both charged, G8); after each pair ``decide`` sees the oriented paired
    differences so far: ``commit`` -> kept; ``reject`` with fewer than max_pairs pairs -> the next pair if the budget
    can fund it, else discarded (``unfundable_pair``); ``reject`` at max_pairs -> discarded.  The first valid trial
    is kept after one run without a test.  A failed candidate run -> ``failed_invalid`` (charged for the runs used);
    a failed incumbent run -> discarded (``incumbent_failed``; the run is charged and recorded, and counts in the §10
    failure rate); a failed (incumbent, seed) run is never re-run, so a later test that reaches that pair ends there
    with discard.  If not even the first pair can be funded the step is refused before it starts
    (``UnfundableStep``; the campaign ends ``no_fundable_candidate``).  No constant is changed (§13 item 4)."""

    arm = "EGATE"
    version = EGATE_VERSION
    action_version = EGATE_ACTION_VERSION

    def __init__(self, instance_seed: int, *, maximize: bool = True, gate=None):
        from r1.baselines.responses import PaceStyleGate
        self.gate = PaceStyleGate() if gate is None else gate
        if (self.gate.alpha, self.gate.clip, self.gate.max_pairs) != (0.1, 0.05, 8):
            raise ValueError("EGATE uses PaceStyleGate as on main: alpha 0.1, clip 0.05, max_pairs 8 (§5.5)")
        self.instance_seed, self.maximize = int(instance_seed), bool(maximize)
        self.seeds = tuple(replicate_seed(self.instance_seed, j) for j in range(self.gate.max_pairs))
        self.incumbent: str | None = None
        self.steps = 0

    def _incumbent_run(self, counter: ChargedRunCounter, j: int):
        return counter.lookup(self.incumbent, self.seeds[j])

    def step(self, config_sha256: str, run: RunFn, counter: ChargedRunCounter) -> StepResult:
        first = self.incumbent is None
        need0 = 1 if first or self._incumbent_run(counter, 0) is not None else 2
        counter.require(need0)  # refused before it starts; nothing is charged
        self.steps += 1
        entries: list[dict] = []
        raw: list[float] = []
        diffs: list[float] = []
        charged = 0
        detail = {"version": self.version, "action_version": self.action_version, "first_trial": first,
                  "gate": {"alpha": self.gate.alpha, "clip": self.gate.clip, "max_pairs": self.gate.max_pairs}}
        for j in range(self.gate.max_pairs):
            seed = self.seeds[j]
            prior_inc = None if first else self._incumbent_run(counter, j)
            need = 1 if first or prior_inc is not None else 2
            if prior_inc is not None and not prior_inc.success:
                # a failed (incumbent, seed) run is never re-run: the test ends at this pair, before any run
                entries.append({"role": "incumbent", "j": j, "seed": seed, "success": False, "charged": False,
                                "metric": None})
                return self._end("discarded", charged, entries, raw, {**detail, "pairs": j, "diffs": diffs,
                                                                     "reason": "incumbent_failed_earlier"})
            if j > 0 and not counter.can_fund(need):
                return self._end("discarded", charged, entries, raw, {**detail, "pairs": j, "diffs": diffs,
                                                                     "reason": "unfundable_pair"})
            out = run(role="candidate", config_sha256=config_sha256, seed=seed, j=j)
            counter.charge(kind="trial" if j == 0 else "replicate", role="candidate", seed=seed,
                           config_sha256=config_sha256, success=out.success, j=j,
                           metric=out.metric if out.success else None, seconds=out.seconds)
            charged += 1
            if j > 0:
                entries.append({"role": "candidate", "j": j, "seed": seed, "success": out.success, "charged": True,
                                "metric": out.metric if out.success else None})
            if not out.success:
                return self._end("failed_invalid", charged, entries, raw, {**detail, "pairs": j, "diffs": diffs,
                                                                          "failed_at_j": j})
            raw.append(float(out.metric))
            if first:  # the first valid trial: kept after one run, no test
                self.incumbent = config_sha256
                return self._end("kept", charged, entries, raw, {**detail, "pairs": 0, "test": None})
            if prior_inc is None:
                inc = run(role="incumbent", config_sha256=self.incumbent, seed=seed, j=j)
                prior_inc = counter.charge(kind="replicate", role="incumbent", seed=seed,
                                           config_sha256=self.incumbent, success=inc.success, j=j,
                                           metric=inc.metric if inc.success else None, seconds=inc.seconds)
                charged += 1
                entries.append({"role": "incumbent", "j": j, "seed": seed, "success": inc.success, "charged": True,
                                "metric": inc.metric if inc.success else None})
            else:
                entries.append({"role": "incumbent", "j": j, "seed": seed, "success": prior_inc.success,
                                "charged": False, "metric": prior_inc.metric})
            if not prior_inc.success:
                return self._end("discarded", charged, entries, raw, {**detail, "pairs": j, "diffs": diffs,
                                                                     "reason": "incumbent_failed"})
            diffs.append(_oriented(out.metric, self.maximize) - _oriented(prior_inc.metric, self.maximize))
            decision, wealth, n = self.gate.decide(diffs)
            if decision == "commit":
                self.incumbent = config_sha256
                return self._end("kept", charged, entries, raw, {**detail, "pairs": n, "diffs": diffs,
                                                                "wealth": wealth, "reason": "commit"})
            detail["wealth"] = wealth
        return self._end("discarded", charged, entries, raw, {**detail, "pairs": self.gate.max_pairs, "diffs": diffs,
                                                             "reason": "max_pairs"})

    @staticmethod
    def _end(decision, charged, entries, raw, detail) -> StepResult:
        return StepResult(decision, charged, entries, _mean(raw), detail)


def _mean(xs: list[float]) -> float | None:
    return math.fsum(xs) / len(xs) if xs else None


def run_replicate_campaign(engine, proposals: list[str], run: RunFn, *, W: int = D3.W,
                           on_charge: Callable | None = None) -> dict:
    """Reference loop (ENGINEERING_ONLY; for tests and as the G1 contract): step through ``proposals`` until W runs
    are spent, a step cannot be funded (``no_fundable_candidate``) or the proposals run out (``proposals_exhausted``,
    a test-only end: in a campaign the LLM-call cap ends it).  Returns the steps, the counter and the end."""
    counter = ChargedRunCounter(W=W, on_charge=on_charge)
    steps: list[StepResult] = []
    ended = "proposals_exhausted"
    for config in proposals:
        if counter.left == 0:
            ended = "worker_runs"
            break
        try:
            steps.append(engine.step(config, run, counter))
        except UnfundableStep:
            ended = "no_fundable_candidate"
            break
    else:
        if counter.left == 0:
            ended = "worker_runs"
    return {"steps": steps, "counter": counter, "ended_on": ended, "incumbent": engine.incumbent}
