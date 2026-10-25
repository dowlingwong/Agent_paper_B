"""The learned-prior interface of the C3 ladder (RUNBOOK Track H.1, H.5, H.6). ENGINEERING_ONLY; AI-assisted (Claude).

Every C3 arm A1-A6 is a ``PriorModel``: it maps one proposal to a 12-bin
forecast over z = Delta / sigma_node (bin 0 = no-op), and nothing else.  The
decisions come from ``r1.c3.rules`` through ``r1.c3.control.RuleController``,
so the arms differ only in the ``PriorModel`` passed in (C3_DESIGN §1, §5).

``forecast(row) -> Forecast(probs[12], version, digest, latency_s)``.  ``row``
is a proposal row: ``{"node": ..., "features": {FEATURES...}}`` plus, for the
LLM arms, ``"edit"`` (the manager's structured edit).  Dataset rows
(``r1.c3.dataset``) qualify as they are; the online controller builds the same
row from ``r1.c3.features.features_from_view``.  (pi, mu, tau) come from
``labels.moments`` with the arms' tau floor (``Forecast.moments``).

Implementations:
- ``TableArmPrior`` wraps a fitted A1 ``ConstantPrior``, A2 ``RulesPrior`` or A3
  ``LGBMPrior`` (``r1.c3.arms``); ``offline_arm`` adapts it to
  ``offline_eval.crossfit`` (the H.1 acceptance: identical offline numbers).
  The NGBoost-Gaussian A3 variant of C3_DESIGN §5 does not exist in the code
  base and is not added here.
- ``ManagerQuestionPrior`` (A4): typed questions to the manager model through an
  injected client (one LLM call per forecast, charged to the LLM-call cap by the
  controller), mapped to bins by isotonic calibration fitted on dev.
- ``SidecarPrior`` (A5/A6): HTTP client of ``r1.c3.serve``; 1 s timeout; any
  failure falls back to the given fallback prior (A1) and is reported so the
  controller logs ``prior_unavailable``.  Sidecar calls cost compute only.
- ``FixedPrior``: a fixed distribution (tests; the A5/A6 dry-run stubs).
"""
from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol

import numpy as np

from r1.c3.arms import TAU_FLOOR_Z, ConstantPrior, LGBMPrior, RulesPrior
from r1.c3.features import FEATURES
from r1.c3.labels import BIN_NAMES, N_BINS, moments

SIDECAR_TIMEOUT_S = 1.0


@dataclass(frozen=True)
class Forecast:
    probs: tuple                 # 12 bin probabilities (bin 0 = no-op)
    version: str                 # the prior's version string
    digest: str                  # sha256 of the fitted parameters / pinned weights
    latency_s: float             # wall time of the forecast (descriptive only)
    llm_calls: int = 0           # LLM calls made for this forecast (A4)
    fallback: str | None = None  # why the fallback prior answered instead (None = the prior itself)
    info: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        p = np.asarray(self.probs, float)
        if p.shape != (N_BINS,) or not np.all(np.isfinite(p)) or np.any(p < -1e-12) or abs(p.sum() - 1.0) > 1e-6:
            raise ValueError(f"a forecast needs {N_BINS} finite non-negative probabilities summing to 1")
        object.__setattr__(self, "probs", tuple(float(x) for x in p))

    def moments(self, sigma_node: float, tau_floor_z: float = TAU_FLOOR_Z) -> tuple[float, float, float]:
        """(pi, mu, tau) in metric units (``labels.moments`` with the arms' tau floor)."""
        pi, mu, tau = moments(np.asarray(self.probs), sigma_node, tau_floor_z=tau_floor_z)
        return float(pi), float(mu), float(tau)


class PriorModel(Protocol):
    version: str
    digest: str
    rule_layer: bool             # A2 and above: rule skips (no-ops, duplicates) before any forecast
    llm_calls_per_forecast: int  # 1 for A4, 0 otherwise

    def forecast(self, row: Mapping[str, Any]) -> Forecast: ...


def proposal_row(node: str, features: Mapping[str, Any], edit: Mapping | None = None) -> dict:
    """The row a ``PriorModel`` reads, from the online featurizer's output."""
    row = {"node": node, "features": dict(features)}
    if edit is not None:
        row["edit"] = dict(edit)
    return row


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _normalised(p) -> tuple:
    p = np.clip(np.asarray(p, float), 0.0, None)
    return tuple(float(x) for x in p / p.sum())


# ---------------------------------------------------------------------------
# A1-A3: the offline arms
# ---------------------------------------------------------------------------

ARM_CLASSES = {"A1": ConstantPrior, "A2": RulesPrior, "A3": LGBMPrior}


def arm_digest(arm) -> str:
    """sha256 of a fitted arm's parameters."""
    if isinstance(arm, LGBMPrior):
        return hashlib.sha256(arm.model.model_to_string().encode()).hexdigest()
    return _sha({"pooled": np.asarray(arm.pooled).tolist(),
                 "by_node": {k: np.asarray(v).tolist() for k, v in sorted(arm.by_node.items())}})


class TableArmPrior:
    """A fitted A1/A2/A3 arm as a ``PriorModel`` (one proposal per call)."""

    llm_calls_per_forecast = 0

    def __init__(self, arm, name: str | None = None) -> None:
        self.arm = arm
        self.name = name or arm.name
        self.rule_layer = self.name != "A1"  # offline_eval.decisions: rule_layer=(arm != "A1")
        self.version = f"{self.name}/{type(arm).__name__}/v1"
        self.digest = arm_digest(arm)

    @classmethod
    def fit(cls, name: str, rows) -> "TableArmPrior":
        return cls(ARM_CLASSES[name]().fit(rows), name)

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        t0 = time.perf_counter()
        p = self.arm.predict([row])[0]
        return Forecast(probs=tuple(float(x) for x in p), version=self.version, digest=self.digest,
                        latency_s=time.perf_counter() - t0)


class _OfflineArm:
    """``offline_eval.crossfit`` adapter: fit -> ``PriorModel``; predict stacks one forecast per row."""

    def __init__(self, factory: Callable[[list], Any]) -> None:
        self.factory = factory

    def fit(self, rows):
        self.prior = self.factory(rows)
        return self

    def predict(self, rows):
        return np.array([self.prior.forecast(r).probs for r in rows])


def offline_arm(name: str):
    """A zero-argument class-like factory for ``offline_eval.crossfit(arms=...)`` wrapping ``TableArmPrior``."""
    return lambda: _OfflineArm(lambda rows: TableArmPrior.fit(name, rows))


# ---------------------------------------------------------------------------
# Fixed distributions (tests; A5/A6 stubs in dry runs)
# ---------------------------------------------------------------------------

class FixedPrior:
    llm_calls_per_forecast = 0

    def __init__(self, probs, name: str = "fixed", rule_layer: bool = True) -> None:
        self.probs = _normalised(probs)
        self.name, self.rule_layer = name, rule_layer
        self.version = f"{name}/fixed/v1"
        self.digest = _sha(self.probs)

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        return Forecast(probs=self.probs, version=self.version, digest=self.digest, latency_s=0.0)


# ---------------------------------------------------------------------------
# A4: the manager's typed questions + isotonic map (C3_DESIGN §5)
# ---------------------------------------------------------------------------

SIZE_BUCKETS = ("tiny", "small", "medium", "large")
# Magnitude template per size bucket over the non-inert bins (1..11) for each sign.
# Positive side bins: 6 (central, |z| <= 0.15; counted half positive), 7 (0.15,0.5], 8 (0.5,1], 9 (1,2],
# 10 (2,3], 11 (3,inf); negative side mirrors 5,4,3,2,1.  A declared, fixed map (no tuning).
_SIZE_TEMPLATE = {"tiny": (1.0, 0.0, 0.0, 0.0, 0.0, 0.0), "small": (0.2, 0.8, 0.0, 0.0, 0.0, 0.0),
                  "medium": (0.0, 0.2, 0.5, 0.3, 0.0, 0.0), "large": (0.0, 0.0, 0.1, 0.4, 0.3, 0.2)}

A4_QUESTION = (
    "You proposed the edit below to an ML training configuration. Answer three typed questions about its "
    "effect on the validation metric, compared with the current incumbent, before it is run.\n"
    "Node: {node}. Edit: {edit}. Features: {features}.\n"
    "1. p_no_effect: probability that the edit leaves the active configuration unchanged (no effect).\n"
    "2. p_positive: probability that the metric improves, given some effect.\n"
    "3. size: expected magnitude of the change relative to the node's noise: one of tiny, small, medium, large.\n"
    'Reply with JSON only: {{"p_no_effect": <0..1>, "p_positive": <0..1>, "size": "<tiny|small|medium|large>"}}'
)


def _call_llm(llm: Any, prompt: str) -> str:
    if callable(llm) and not hasattr(llm, "invoke"):
        return str(llm(prompt))
    reply = llm.invoke(prompt)
    return str(getattr(reply, "content", reply))


def parse_typed_answer(text: str) -> dict:
    import re
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("no JSON object in the reply")
    data = json.loads(m.group(0))
    p0, pp, size = float(data["p_no_effect"]), float(data["p_positive"]), str(data["size"]).strip().lower()
    if not (0.0 <= p0 <= 1.0 and 0.0 <= pp <= 1.0) or size not in SIZE_BUCKETS:
        raise ValueError(f"answer out of range: {data}")
    return {"p_no_effect": p0, "p_positive": pp, "size": size}


def typed_to_bins(p_no_effect: float, p_positive: float, size: str) -> tuple:
    """The 12-bin distribution implied by (calibrated) typed answers."""
    t = np.asarray(_SIZE_TEMPLATE[size], float)
    p = np.zeros(N_BINS)
    p[0] = p_no_effect
    rest = 1.0 - p_no_effect
    pos = rest * p_positive
    neg = rest * (1.0 - p_positive)
    p[6] = t[0] * (pos + neg)          # central bin carries both signs
    p[7:12] += pos * t[1:]
    p[1:6] += neg * t[1:][::-1]
    return _normalised(p)


class IsotonicMap:
    """Monotone maps raw -> calibrated for p_no_effect and p_positive (identity until fitted)."""

    def __init__(self) -> None:
        self.maps: dict[str, tuple[list, list]] = {}

    def fit(self, raw: Mapping[str, list], target: Mapping[str, list], weights: Mapping[str, list] | None = None):
        from sklearn.isotonic import IsotonicRegression
        for key in ("p_no_effect", "p_positive"):
            x, y = np.asarray(raw[key], float), np.asarray(target[key], float)
            if len(x) < 2:
                continue
            w = None if weights is None else np.asarray(weights[key], float)
            iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(x, y, sample_weight=w)
            self.maps[key] = ([float(v) for v in iso.X_thresholds_], [float(v) for v in iso.y_thresholds_])
        return self

    def __call__(self, key: str, value: float) -> float:
        if key not in self.maps:
            return float(value)
        xs, ys = self.maps[key]
        return float(np.interp(value, xs, ys))

    def digest(self) -> str:
        return _sha(self.maps)


class ManagerQuestionPrior:
    """A4: the manager answers typed questions (one LLM call per forecast); isotonic map to bins.

    ``llm`` is injected (a callable ``prompt -> text`` or an object with
    ``invoke``); tests use a fake.  Any failure answers with ``fallback`` (A1)
    and is reported in ``Forecast.fallback``; the call is still charged.
    """

    rule_layer = True
    llm_calls_per_forecast = 1

    def __init__(self, llm: Any, fallback, calibration: IsotonicMap | None = None,
                 model_id: str = "manager") -> None:
        self.llm, self.fallback = llm, fallback
        self.calibration = calibration or IsotonicMap()
        self.version = f"A4/typed_questions/v1/{model_id}"
        self.digest = _sha({"calibration": self.calibration.maps, "template": _SIZE_TEMPLATE,
                            "question": A4_QUESTION, "model": model_id})

    def prompt(self, row: Mapping[str, Any]) -> str:
        feats = {k: row["features"][k] for k in FEATURES if k in row["features"]}
        return A4_QUESTION.format(node=row["node"], edit=json.dumps(row.get("edit") or {}, sort_keys=True),
                                  features=json.dumps(feats, sort_keys=True, default=str))

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        t0 = time.perf_counter()
        try:
            answer = parse_typed_answer(_call_llm(self.llm, self.prompt(row)))
        except Exception as exc:  # noqa: BLE001 - a failed or malformed answer falls back, still charged
            fb = self.fallback.forecast(row)
            return Forecast(probs=fb.probs, version=self.version, digest=self.digest,
                            latency_s=time.perf_counter() - t0, llm_calls=1, fallback=f"a4_answer_failed: {exc!r}"[:300],
                            info={"fallback_version": fb.version, "fallback_digest": fb.digest})
        p0 = self.calibration("p_no_effect", answer["p_no_effect"])
        pp = self.calibration("p_positive", answer["p_positive"])
        return Forecast(probs=typed_to_bins(p0, pp, answer["size"]), version=self.version, digest=self.digest,
                        latency_s=time.perf_counter() - t0, llm_calls=1, info={"answer": answer})


# ---------------------------------------------------------------------------
# A5/A6: the sidecar client (H.5)
# ---------------------------------------------------------------------------

class SidecarPrior:
    """Client of ``r1.c3.serve``: ``POST <url>/forecast`` -> 12 probabilities.

    ``timeout_s`` (default 1 s) bounds every call.  A timeout, a connection or
    HTTP error, a malformed reply, or a reply whose ``digest`` differs from
    ``expected_digest`` (the pin) is answered by ``fallback`` (the A1 prior),
    with ``Forecast.fallback`` set; the controller logs ``prior_unavailable``.
    The campaign never crashes on the sidecar.  Calls cost compute only.
    """

    llm_calls_per_forecast = 0

    def __init__(self, url: str, fallback, *, name: str = "A5", expected_digest: str | None = None,
                 timeout_s: float = SIDECAR_TIMEOUT_S, rule_layer: bool = True) -> None:
        self.url = url.rstrip("/")
        self.fallback, self.name, self.rule_layer = fallback, name, rule_layer
        self.expected_digest, self.timeout_s = expected_digest, float(timeout_s)
        self.version = f"{name}/sidecar/v1"
        self.digest = expected_digest or "unpinned"

    def _post(self, row: Mapping[str, Any]) -> dict:
        body = json.dumps({"row": {"node": row["node"], "features": row["features"],
                                   **({"edit": row["edit"]} if row.get("edit") is not None else {})}},
                          sort_keys=True, default=str).encode()
        req = urllib.request.Request(f"{self.url}/forecast", data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310 - local sidecar only
            return json.loads(resp.read().decode())

    def forecast(self, row: Mapping[str, Any]) -> Forecast:
        t0 = time.perf_counter()
        try:
            reply = self._post(row)
            if self.expected_digest is not None and reply.get("digest") != self.expected_digest:
                raise ValueError(f"sidecar digest {reply.get('digest')!r} != pin {self.expected_digest!r}")
            probs = [float(x) for x in reply["probs"]]
            return Forecast(probs=tuple(probs), version=str(reply.get("version", self.version)),
                            digest=str(reply.get("digest", self.digest)), latency_s=time.perf_counter() - t0,
                            info={"sidecar_compute_s": float(reply.get("compute_s", 0.0))})
        except Exception as exc:  # noqa: BLE001 - never crash the campaign on the sidecar
            reason = "timeout" if isinstance(exc, TimeoutError) or "timed out" in str(exc) else type(exc).__name__
            fb = self.fallback.forecast(row)
            return Forecast(probs=fb.probs, version=self.version, digest=self.digest,
                            latency_s=time.perf_counter() - t0, fallback=f"prior_unavailable: {reason}",
                            info={"error": repr(exc)[:300], "fallback_version": fb.version,
                                  "fallback_digest": fb.digest})


__all__ = ["BIN_NAMES", "Forecast", "PriorModel", "TableArmPrior", "FixedPrior", "ManagerQuestionPrior",
           "SidecarPrior", "IsotonicMap", "offline_arm", "proposal_row", "typed_to_bins", "parse_typed_answer"]
