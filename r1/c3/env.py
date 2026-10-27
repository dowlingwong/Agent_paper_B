"""Offline contextual-bandit environment over the labelled C3 table (RUNBOOK Track H.8). ENGINEERING_ONLY; AI-assisted (Claude).

``OfflineBanditEnv`` follows the Gymnasium API (``reset(seed, options) -> (obs,
info)``, ``step(action) -> (obs, reward, terminated, truncated, info)``) without
depending on Gymnasium: it subclasses ``gymnasium.Env`` and is registered as
``r1c3/OfflineBandit-v0`` only when Gymnasium is importable.

* **Episode** = one proposal (one step; ``terminated`` is always True).
* **Context** = the proposal's features (``FEATURES`` order; NaN -> 0); the
  full row stays available in ``info`` for bookkeeping.
* **Action** = execute (0) or skip (1); observation carries features and a 12-bin
  belief supplied by an explicit provider receiving only pre-decision fields.
  The caller must establish that the belief provider has no label/evaluation
  leakage; the API cannot certify an external closure's provenance.
  Historical bin actions are available only with ``version="bin/v0"``.
* **Legacy plug-in** (``bin/v0``, historical C3_DESIGN §5 stage 2): ``"greedy"`` uses pi = 1{b = no-op},
  mu = sigma_node mid(b), tau = sigma_node tau_node[node] (dev-estimated, in z
  units); ``"onehot_moments"`` uses ``labels.moments`` of the one-hot bin with the
  arms' tau floor, i.e. exactly the decision ``offline_eval`` takes for an arm
  whose forecast is that one-hot distribution (the acceptance check).
* **Reward** in the amended version is split-specific Track P utility u,
  computed from label columns and a training-only A1 constant prior; skip pays zero.
  In bin/v0 the legacy plug-in determines r = Delta * keep - g * execute.
  The rule layer prevents duplicate execution.
* **Seeds.** In the amended version, each row's table ``split`` selects
  ``z_train`` for train/val and ``z_eval`` for test (Track P §3.6). A1 is
  fitted once from training-split ``y_train`` only. In ``bin/v0``, the
  historical label/eval seed and weighting behavior remains selectable.

``OnlineCampaignEnv`` is not built (only if C4 finds a material DI violation).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from r1.c3 import offline_eval as OE
from r1.c3.arms import ConstantPrior, is_duplicate, is_noop
from r1.c3.audit import split_audit
from r1.c3.features import FEATURES
from r1.c3.labels import INERT, MIDPOINTS, N_BINS, action_target

try:  # Gymnasium is optional: subclass and register only when it is importable
    import gymnasium as _gym
    from gymnasium import spaces as _spaces
    _Base = _gym.Env
except Exception:  # noqa: BLE001
    _gym, _spaces, _Base = None, None, object

ENV_ID = "r1c3/OfflineBandit-v0"
SPLITS = ("label", "eval")
PLUGINS = ("greedy", "onehot_moments")


def label_rows(table_dir: Path | str, audits_path: Path | str | None = None) -> list[dict]:
    """``offline_eval.assemble`` rows plus ``delta_label`` (the label half of the audit seeds; no-ops 0)."""
    rows = OE.assemble(Path(table_dir), Path(audits_path) if audits_path else None, seed_split=True)
    audits_path = Path(audits_path) if audits_path else Path(table_dir) / "audits.jsonl"
    audits = {}
    for line in audits_path.read_text().splitlines():
        if line.strip():
            a = json.loads(line)
            audits[a["proposal_id"]] = a
    for r in rows:
        if is_noop(r):
            r["delta_label"] = 0.0
        elif is_duplicate(r):
            r["delta_label"] = None  # duplicates carry no training label
        else:
            r["delta_label"] = split_audit(audits[r["proposal_id"]])[0]["delta_audit"]
    return rows


def onehot(b: int) -> np.ndarray:
    p = np.zeros(N_BINS)
    p[int(b)] = 1.0
    return p



class OfflineBanditEnv(_Base):
    metadata = {"render_modes": []}

    def __init__(self, rows: list[dict], *, split: str | None = None, g_units: float | None = None,
                 rule_layer: bool = True, plugin: str = "greedy", tau_node: Mapping[str, float] | None = None,
                 order: str = "sequential", seed: int | None = None, version: str = "execute-skip/v1",
                 belief_provider: Callable[[Mapping[str, Any]], Any] | None = None) -> None:
        if version not in ("execute-skip/v1", "bin/v0"):
            raise ValueError("unknown environment version")
        if plugin not in PLUGINS or order not in ("sequential", "random"):
            raise ValueError(f"plugin in {PLUGINS}, order sequential|random")
        self.version, self.belief_provider = version, belief_provider
        self.tau_node = dict(tau_node or {})
        self._belief = None
        self.rule_layer, self.plugin = bool(rule_layer), plugin
        if version == "bin/v0":
            split = "label" if split is None else split
            g_units = OE.G_PRIMARY if g_units is None else g_units
            if split not in SPLITS:
                raise ValueError(f"split in {SPLITS}")
            if plugin == "greedy" and not tau_node:
                raise ValueError("the greedy plug-in needs tau_node (z units, dev-estimated) per node")
            OE._g_role(g_units)
            self.split, self.g_units = split, float(g_units)
            if split == "label":
                pop = [r for r in rows if r.get("delta_label") is not None and r.get("weight", 0) > 0]
                self._value, self._weight = "delta_label", "weight"
            else:
                pop = [r for r in rows if r.get("eval_weight", 0) > 0]
                self._value, self._weight = "delta_true", "eval_weight"
        else:
            if split is not None or g_units is not None:
                raise ValueError("split and g are determined by the table and configuration")
            self.split, self.g_units = None, float(OE.G_PRIMARY)
            self._value, self._weight = None, "weight"
            pop = []
            training = []
            for original in rows:
                r = dict(original)
                if r.get("split") not in ("train", "val", "test"):
                    raise ValueError("table split must be train, val or test")
                if "is_noop" in r and "noop" not in r:
                    r["noop"] = bool(r["is_noop"])
                r["weight"] = float(r.get("weight", 1.0))
                if not np.isfinite(r["weight"]) or r["weight"] < 0:
                    raise ValueError("invalid table weight")
                if r["weight"] == 0:
                    continue
                pop.append(r)
                if r["split"] == "train" and not is_duplicate(r):
                    y = np.asarray(r.get("y_train"), dtype=float)
                    if y.shape != (N_BINS,) or not np.all(np.isfinite(y)) or np.any(y < 0) or not np.isclose(y.sum(), 1.0, rtol=0, atol=1e-7):
                        raise ValueError("training rows require a valid y_train distribution")
                    training.append({"node": r["node"], "soft": y, "weight": r["weight"]})
            if not training:
                raise ValueError("fixed A1 requires labelled training-split rows")
            self._a1 = ConstantPrior().fit(training)
        if not pop:
            raise ValueError(f"no rows for split {split!r}")
        self.rows = pop
        self.order = order
        self._rng = np.random.default_rng(seed)
        self._i = -1
        self._current: dict | None = None
        if _spaces is not None:
            self.action_space = _spaces.Discrete(N_BINS if version == "bin/v0" else 2)
            features_space = _spaces.Box(-np.inf, np.inf, shape=(len(FEATURES),), dtype=np.float64)
            self.observation_space = features_space if version == "bin/v0" else _spaces.Dict({
                "features": features_space, "belief": _spaces.Box(0.0, 1.0, shape=(N_BINS,), dtype=np.float64)})

    def __len__(self) -> int:
        return len(self.rows)

    @staticmethod
    def observe(row: Mapping[str, Any]) -> np.ndarray:
        return np.nan_to_num(np.array([float(row["features"][c]) for c in FEATURES], float), nan=0.0)

    def reset(self, *, seed: int | None = None, options: Mapping[str, Any] | None = None):
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        if options and "index" in options:
            self._i = int(options["index"])
        elif self.order == "random":
            self._i = int(self._rng.integers(len(self.rows)))
        else:
            self._i = (self._i + 1) % len(self.rows)
        self._current = self.rows[self._i]
        r = self._current
        info = {"index": self._i, "proposal_id": r["proposal_id"], "node": r["node"], "weight": r[self._weight],
                "sigma_node": r["sigma_node"], "sigma_cmp": r["sigma_cmp"], "delta_hat": r["delta_hat"],
                "noop": is_noop(r), "duplicate": is_duplicate(r), "split": self.split if self.version == "bin/v0" else r["split"]}
        if self.version == "bin/v0":
            return self.observe(r), info
        info.pop("delta_hat")  # unavailable before execute
        self._belief = None
        try:
            public = {"proposal_id": r["proposal_id"], "node": r["node"],
                      "features": {name: r["features"][name] for name in FEATURES},
                      "sigma_node": r["sigma_node"], "sigma_cmp": r["sigma_cmp"]}
            if self.belief_provider is None:
                raise ValueError("belief_provider is required; precomputed beliefs need an explicitly controlled provider")
            p = self.belief_provider(public)
            p = np.asarray(p, dtype=float)
            if p.shape != (N_BINS,) or not np.all(np.isfinite(p)) or np.any(p < 0) or not np.isclose(p.sum(), 1.0, rtol=0, atol=1e-7):
                raise ValueError("belief must be a finite normalized 12-bin probability vector")
        except Exception:
            self._current = None
            raise
        self._belief = p.copy()
        return {"features": self.observe(r), "belief": p.copy()}, info

    def decide(self, b: int, row: Mapping[str, Any]) -> tuple[bool, bool, float]:
        """(execute, keep, g) of bin ``b`` on ``row`` under the rules."""
        if self.plugin == "onehot_moments":
            ex, kp, (_, _, _, _, g) = OE.decisions(onehot(b)[None, :], [row], self.g_units, rule_layer=self.rule_layer)
            return bool(ex[0]), bool(kp[0]), float(g[0])
        from r1.c3 import rules
        sig_n = row["sigma_node"]
        pi = 1.0 if b == INERT else 0.0
        mu = 0.0 if b == INERT else float(MIDPOINTS[b - 1]) * sig_n
        tau = float(self.tau_node[row["node"]]) * sig_n
        g = self.g_units * sig_n
        ex, kp = rules.decide(np.array([pi]), np.array([mu]), np.array([tau]), np.array([row["sigma_cmp"]]),
                              np.array([g]), np.array([row["delta_hat"]]))
        ex, kp = bool(ex[0]), bool(kp[0])
        if self.rule_layer and is_duplicate(row):
            ex = kp = False
        return ex, kp, g

    def step(self, action):
        if self._current is None:
            raise RuntimeError("call reset() first")
        row = self._current
        if self.version == "bin/v0":
            b = int(action)
            if not 0 <= b < N_BINS:
                raise ValueError(f"action must be a bin in 0..{N_BINS - 1}")
            ex, kp, g = self.decide(b, row)
            obs = self.observe(row)
        else:
            if isinstance(action, (bool, np.bool_)) or not isinstance(action, (int, np.integer)):
                raise ValueError("action must be an integer")
            b = int(action)
            if b not in (0, 1):
                raise ValueError("action must be 0 (execute) or 1 (skip)")
            ex = b == 0 and not (self.rule_layer and is_duplicate(row))
            g = self.g_units * row["sigma_node"]
            obs = {"features": self.observe(row), "belief": self._belief.copy()}
            if ex:
                # Val is drawn from training instances and uses the training-label block;
                # test uses the independent evaluation block (Track P §3.6).
                label_key = "z_train" if row["split"] in ("train", "val") else "z_eval"
                z = np.asarray(row.get(label_key), dtype=float)
                if z.ndim != 1 or z.size == 0 or not np.all(np.isfinite(z)):
                    raise ValueError(f"{label_key} must contain finite split-specific labels")
                sig = float(row["sigma_node"])
                if not np.isfinite(sig) or sig <= 0:
                    raise ValueError("sigma_node must be positive and finite")
                a1_probs = self._a1.predict([row])[0]
                reward = float(action_target(float(z.mean()) * sig, row["delta_hat"], a1_probs,
                                             sig, row["sigma_cmp"], g_units=self.g_units))
            else:
                reward = 0.0
            kp = None  # keep is already incorporated in fixed-reference utility
        if self.version == "bin/v0":
            reward = float(row[self._value] * kp - g * ex)
        info = {"execute": ex, "keep": kp, "g": g, "weight": row[self._weight], "node": row["node"],
                "proposal_id": row["proposal_id"]}
        self._current = None
        return obs, reward, True, False, info


def evaluate_policy(env: OfflineBanditEnv, policy: Callable[[np.ndarray, dict], int]) -> dict:
    """One pass over the population: weighted mean reward per node (the offline one-step value)."""
    sums: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for i in range(len(env)):
        obs, info = env.reset(options={"index": i})
        _, reward, terminated, truncated, step_info = env.step(policy(obs, info))
        assert terminated and not truncated
        s = sums[info["node"]]
        s[0] += info["weight"] * reward
        s[1] += info["weight"]
        s[2] += info["weight"] * step_info["execute"]
    return {node: {"mean_per_proposal": s[0] / s[1], "per_campaign": OE.CAMPAIGN_RUNS * s[0] / s[1],
                   "exec_rate": s[2] / s[1]} for node, s in sorted(sums.items())}


if _gym is not None:  # pragma: no cover - only when Gymnasium is installed
    try:
        if ENV_ID not in _gym.registry:
            _gym.register(id=ENV_ID, entry_point="r1.c3.env:OfflineBanditEnv")
    except Exception:  # noqa: BLE001
        pass
