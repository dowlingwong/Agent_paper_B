"""Offline contextual-bandit environment over the labelled C3 table (RUNBOOK Track H.8). ENGINEERING_ONLY; AI-assisted (Claude).

``OfflineBanditEnv`` follows the Gymnasium API (``reset(seed, options) -> (obs,
info)``, ``step(action) -> (obs, reward, terminated, truncated, info)``) without
depending on Gymnasium: it subclasses ``gymnasium.Env`` and is registered as
``r1c3/OfflineBandit-v0`` only when Gymnasium is importable.

* **Episode** = one proposal (one step; ``terminated`` is always True).
* **Context** = the proposal's features (``FEATURES`` order; NaN -> 0); the
  full row stays available in ``info`` for bookkeeping.
* **Action** = one of the 12 bins.
* **Plug-in** (C3_DESIGN §5, stage 2): ``"greedy"`` uses pi = 1{b = no-op},
  mu = sigma_node mid(b), tau = sigma_node tau_node[node] (dev-estimated, in z
  units); ``"onehot_moments"`` uses ``labels.moments`` of the one-hot bin with the
  arms' tau floor, i.e. exactly the decision ``offline_eval`` takes for an arm
  whose forecast is that one-hot distribution (the acceptance check).
* **Reward** r = Delta * keep - g * execute with (execute, keep) from
  ``offline_eval.decisions`` (rules of T4 Propositions 6 and 8, the logged
  Delta_hat, the edit's sigma_cmp, g = g_units sigma_node; with the rule layer
  duplicates are never executed).
* **Seeds.** ``split="label"`` (training) uses the label half of the audit
  seeds (``audit.split_audit``; 7001-7005 for K = 10) and the training weights;
  duplicates have no label and are excluded.  ``split="eval"`` uses the
  evaluation half (``delta_true``) and the evaluation weights.  The label
  population never reads ``delta_true``.

``OnlineCampaignEnv`` is not built (only if C4 finds a material DI violation).
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np

from r1.c3 import offline_eval as OE
from r1.c3.arms import is_duplicate, is_noop
from r1.c3.audit import split_audit
from r1.c3.features import FEATURES
from r1.c3.labels import INERT, MIDPOINTS, N_BINS

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

    def __init__(self, rows: list[dict], *, split: str = "label", g_units: float = OE.G_PRIMARY,
                 rule_layer: bool = True, plugin: str = "greedy", tau_node: Mapping[str, float] | None = None,
                 order: str = "sequential", seed: int | None = None) -> None:
        if split not in SPLITS or plugin not in PLUGINS or order not in ("sequential", "random"):
            raise ValueError(f"split in {SPLITS}, plugin in {PLUGINS}, order sequential|random")
        if plugin == "greedy" and not tau_node:
            raise ValueError("the greedy plug-in needs tau_node (z units, dev-estimated) per node")
        OE._g_role(g_units)  # only the declared g values (PLAN §10, g (22 Oct))
        self.split, self.g_units, self.rule_layer, self.plugin = split, float(g_units), bool(rule_layer), plugin
        self.tau_node = dict(tau_node or {})
        if split == "label":
            pop = [r for r in rows if r.get("delta_label") is not None and r.get("weight", 0) > 0]
            self._value, self._weight = "delta_label", "weight"
        else:
            pop = [r for r in rows if r.get("eval_weight", 0) > 0]
            self._value, self._weight = "delta_true", "eval_weight"
        if not pop:
            raise ValueError(f"no rows for split {split!r}")
        self.rows = pop
        self.order = order
        self._rng = np.random.default_rng(seed)
        self._i = -1
        self._current: dict | None = None
        if _spaces is not None:
            self.action_space = _spaces.Discrete(N_BINS)
            self.observation_space = _spaces.Box(-np.inf, np.inf, shape=(len(FEATURES),), dtype=np.float64)

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
                "noop": is_noop(r), "duplicate": is_duplicate(r), "split": self.split}
        return self.observe(r), info

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
        b = int(action)
        if not 0 <= b < N_BINS:
            raise ValueError(f"action must be a bin in 0..{N_BINS - 1}")
        row = self._current
        ex, kp, g = self.decide(b, row)
        reward = float(row[self._value] * kp - g * ex)
        info = {"execute": ex, "keep": kp, "g": g, "weight": row[self._weight], "node": row["node"],
                "proposal_id": row["proposal_id"]}
        self._current = None
        return self.observe(row), reward, True, False, info


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
