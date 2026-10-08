"""B-DAC3: configurator heads — encoder features into the shared ridge value heads.

Design reference: ``docs/paper_split/B_DAC_CONFIGURATOR_AMENDMENT_20261004.md`` §4.3.

The configurator's *heads* are the existing value models of controller design
v2 (``timing.py``: ``A1``, ``V_wait``, ``A2``, the BAVAR-inspired scorer and the
myopic/reserve scores), all ridge with one shared ``l2``.  This module does not
add a learner.  It adds encoder-derived features to the decision histories so
that **every** controller sees the same augmented ``H1`` / ``H2`` (design v2 §4,
matched information and capacity):

1. serialise each root's checkpoint histories (``serialiser``);
2. embed them with a frozen encoder (``encoder``), cached by fingerprint;
3. fit an outcome-blind projection (centring, top-``k`` principal directions,
   whitening) on **development roots only**, H1 and H2 texts pooled;
4. write ``e1_##`` into ``h1`` and ``e1_##`` + ``e2_##`` into ``h2`` (so H2
   contains H1), optionally dropping or keeping the telemetry features;
5. call the unchanged ``evaluate_tree``.

The projection never sees outcomes and never sees test texts.  Within the
development set it is fitted once on all development roots (outcome-blind,
transductive across development folds); this is declared in the amendment.

Feature sets (the ablation axis): ``telemetry`` (current design),
``embedding``, ``telemetry+embedding``.

Nothing here is scientific evidence until run on qualified pilot data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json

import numpy as np

from causal_branch.control.configurator.encoder import (
    EmbeddingCache,
    Encoder,
    fingerprint_digest,
)
from causal_branch.control.configurator.serialiser import (
    DecisionHistory,
    serialise_root,
    serialiser_fingerprint,
)

FEATURE_SETS = ("telemetry", "embedding", "telemetry+embedding")
DEFAULT_K = 8
CONFIGURATOR_SCHEMA = "b_dac_configurator_v1"


class ConfiguratorError(ValueError):
    """A configurator request violates the amendment."""


# --------------------------------------------------------------------------
# Outcome-blind projection
# --------------------------------------------------------------------------


PROJECTION_MODES = ("pca", "standardize")


@dataclass
class EmbeddingProjector:
    """Outcome-blind projection fitted on development texts.

    ``pca``: centre, top-``k`` principal directions, whiten (high-dimensional
    encoders such as CLM).  ``standardize``: keep every dimension, centre and
    scale (low-dimensional encoders such as Kev's typed-question features);
    ``k`` becomes the encoder dimension.
    """

    k: int = DEFAULT_K
    mode: str = "pca"
    mean: np.ndarray | None = None
    components: np.ndarray | None = None
    scale: np.ndarray | None = None
    n_fit: int = 0

    def fit(self, x: np.ndarray) -> "EmbeddingProjector":
        x = np.asarray(x, dtype=float)
        if x.ndim != 2 or len(x) < 2:
            raise ConfiguratorError("projection needs at least two development texts")
        if self.mode not in PROJECTION_MODES:
            raise ConfiguratorError(f"unknown projection mode {self.mode!r}")
        if self.mode == "standardize":
            self.k = x.shape[1]
            self.mean = x.mean(axis=0)
            self.components = np.eye(x.shape[1])
            sd = x.std(axis=0)
            self.scale = np.where(sd > 1e-12, sd, 1.0)
            self.n_fit = len(x)
            return self
        if self.k < 1 or self.k >= len(x):
            raise ConfiguratorError(
                f"k={self.k} must be in [1, n_dev_texts={len(x)}); with few roots "
                "keep k well below the number of development roots")
        self.mean = x.mean(axis=0)
        _, _, vt = np.linalg.svd(x - self.mean, full_matrices=False)
        comps = vt[: self.k]
        # sign convention: the largest-magnitude loading is positive (determinism)
        signs = np.sign(comps[np.arange(len(comps)), np.abs(comps).argmax(axis=1)])
        self.components = comps * signs[:, None]
        z = (x - self.mean) @ self.components.T
        self.scale = np.where(z.std(axis=0) > 1e-12, z.std(axis=0), 1.0)
        self.n_fit = len(x)
        return self

    def transform(self, x: np.ndarray) -> np.ndarray:
        if self.components is None:
            raise ConfiguratorError("projector is not fitted")
        return ((np.asarray(x, dtype=float) - self.mean) @ self.components.T) / self.scale

    def digest(self) -> str:
        if self.components is None:
            return "unfitted"
        h = hashlib.sha256()
        for a in (self.mean, self.components, self.scale):
            h.update(np.round(a, 12).tobytes())
        return h.hexdigest()


# --------------------------------------------------------------------------
# Feature map
# --------------------------------------------------------------------------

Histories = dict  # root_id -> (DecisionHistory, DecisionHistory | None)


def _names(prefix: str, k: int) -> list[str]:
    return [f"{prefix}_{j:02d}" for j in range(k)]


@dataclass
class FeatureMap:
    """A frozen map from (row, histories) to augmented decision histories."""

    encoder: Encoder
    feature_set: str
    projector: EmbeddingProjector
    cache: EmbeddingCache
    serialiser_kw: dict = field(default_factory=dict)
    dev_roots_digest: str = ""
    dev_families: frozenset = frozenset()

    def _texts(self, rows, histories: Histories):
        t1, t2 = {}, {}
        for r in rows:
            rid = r["root_id"]
            if rid not in histories:
                raise ConfiguratorError(f"no decision histories for root {rid!r}")
            h1, h2 = histories[rid]
            if bool(r["reached2"]) != (h2 is not None):
                raise ConfiguratorError(
                    f"root {rid!r}: a checkpoint-2 history must exist iff checkpoint 2 was reached")
            s1, s2 = serialise_root(h1, h2, **self.serialiser_kw)
            t1[rid] = s1.text
            if s2 is not None:
                t2[rid] = s2.text
        return t1, t2

    def apply(self, rows, histories: Histories) -> list[dict]:
        if self.feature_set == "telemetry":
            return [dict(r) for r in rows]
        t1, t2 = self._texts(rows, histories)
        ids1, ids2 = list(t1), list(t2)
        z1 = self.projector.transform(self.cache.embed(self.encoder, [t1[i] for i in ids1]))
        z2 = (self.projector.transform(self.cache.embed(self.encoder, [t2[i] for i in ids2]))
              if ids2 else np.zeros((0, self.projector.k)))
        e1 = dict(zip(ids1, z1))
        e2 = dict(zip(ids2, z2))
        k = self.projector.k
        n1, n2 = _names("e1", k), _names("e2", k)
        out = []
        for r in rows:
            rid = r["root_id"]
            emb1 = {n: float(v) for n, v in zip(n1, e1[rid])}
            keep = self.feature_set == "telemetry+embedding"
            h1 = ({**r["h1"]} if keep else {}) | emb1
            if r["reached2"]:
                emb2 = {n: float(v) for n, v in zip(n2, e2[rid])}
                h2 = ({**r["h2"]} if keep else {}) | emb1 | emb2
            else:
                # an unreached root is never scored at checkpoint 2; keep the
                # key set aligned so the ridge design matrix stays rectangular
                h2 = ({**r["h2"]} if keep else {}) | emb1 | {n: 0.0 for n in n2}
            out.append({**r, "h1": h1, "h2": h2})
        return out

    def provenance(self) -> dict:
        return {
            "schema": CONFIGURATOR_SCHEMA,
            "feature_set": self.feature_set,
            "encoder": self.encoder.fingerprint(),
            "encoder_digest": fingerprint_digest(self.encoder.fingerprint()),
            "serialiser": serialiser_fingerprint(**self.serialiser_kw),
            "projector_mode": self.projector.mode,
            "projector_k": self.projector.k,
            "projector_n_fit": self.projector.n_fit,
            "projector_digest": self.projector.digest(),
            "dev_roots_digest": self.dev_roots_digest,
            "projection_fitted_on": "development roots only (H1+H2 texts, outcome-blind)",
        }


def fit_feature_map(dev_rows, histories: Histories, encoder: Encoder, *,
                    feature_set: str = "telemetry+embedding", k: int = DEFAULT_K,
                    projection: str = "pca", cache: EmbeddingCache | None = None,
                    serialiser_kw: dict | None = None) -> FeatureMap:
    """Fit the outcome-blind projection on development roots only."""

    if feature_set not in FEATURE_SETS:
        raise ConfiguratorError(f"unknown feature set {feature_set!r}")
    if not dev_rows:
        raise ConfiguratorError("no development rows")
    cache = cache or EmbeddingCache()
    fmap = FeatureMap(encoder=encoder, feature_set=feature_set,
                      projector=EmbeddingProjector(k=k, mode=projection), cache=cache,
                      serialiser_kw=dict(serialiser_kw or {}))
    roots = sorted(r["root_id"] for r in dev_rows)
    fmap.dev_roots_digest = hashlib.sha256(json.dumps(roots).encode()).hexdigest()
    fmap.dev_families = frozenset(r["family"] for r in dev_rows)
    if feature_set == "telemetry":
        return fmap
    t1, t2 = fmap._texts(dev_rows, histories)
    texts = list(t1.values()) + list(t2.values())
    fmap.projector.fit(cache.embed(encoder, texts))
    return fmap


def evaluate_with_configurator(dev_rows, test_rows, histories: Histories, encoder: Encoder, *,
                               feature_set: str = "telemetry+embedding", k: int = DEFAULT_K,
                               projection: str = "pca", cache: EmbeddingCache | None = None,
                               serialiser_kw: dict | None = None, **evaluate_kw):
    """Fit the feature map on development roots, augment both sets, evaluate.

    Returns ``(EvaluationReport, provenance)``.  The evaluation harness, the
    controllers, the allocator and the bootstrap are unchanged.
    """

    from causal_branch.control.evaluate_tree import evaluate_tree

    if set(r["family"] for r in dev_rows) & set(r["family"] for r in test_rows):
        raise ConfiguratorError("development and test template families must be disjoint")
    fmap = fit_feature_map(dev_rows, histories, encoder, feature_set=feature_set, k=k,
                           projection=projection, cache=cache, serialiser_kw=serialiser_kw)
    dev_aug = fmap.apply(dev_rows, histories)
    test_aug = fmap.apply(test_rows, histories)
    report = evaluate_tree(dev_aug, test_aug, **evaluate_kw)
    prov = fmap.provenance()
    prov["h1_keys"] = sorted(dev_aug[0]["h1"])
    prov["h2_keys"] = sorted(dev_aug[0]["h2"])
    return report, prov
