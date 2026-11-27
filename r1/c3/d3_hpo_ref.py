# AI-assisted (Claude, local worker, 27 Nov 2026). Tier E; ENGINEERING_ONLY until a signed D.3 note cites the
# reviewed unit.
"""D.3 reference rows HPO-REF (R1-D3-HPO-REF; gap G10): random search with de-duplication (RS) and SMAC3.

Source: the D.3 pre-declaration revision 4 (``docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md``, draft,
not signed) §5.8 (the methods and the configuration-space table), §4.1 (sampler seeds), §8 (schema
``r1_d3_outcome/v2``, HPO-REF rules), §13 item 26 (proposed details), §14 (the SMAC3 version is open); the pinned
analysis ``r1/c3/d3_analysis.py`` (``ENDED_ON_HPO``, ``HPO_PROPOSAL_CAP``, ``_check_ended_on``, ``validate_table``),
which this module imports and never changes.

What is here
------------
(a) ``load_node_space``: each node's configuration space from the harness node config at the D.3 pin
    ``HARNESS_PIN`` (``git show <pin>:configs/nodes/<node>.yaml``; the files are JSON), checked byte for byte by
    sha256 and key for key against the §5.8 table (``DECLARED_SPACES``) and against the edits the
    ``manager_proposal/v1`` schema admits (``editable_symbols``, ``allowed_values``, ``allowed_ranges``,
    ``active_keys``).  Any difference refuses.
(b) ``run_rs``: random search with the rule layer's de-duplication.  NumPy ``PCG64`` seeded with
    instance seed + 1,000,000 x repetition; one uniform draw per step (log-uniform on the keys marked log, integers
    uniform on their closed range), canonicalised to the node's active keys.  A draw whose canonical configuration
    equals the incumbent's (a no-op) or any configuration already executed in the campaign (a duplicate) is skipped
    and charged no run (``rule_skips``).  Every other draw is executed once and kept iff its metric beats the
    incumbent's (the default keep rule; ``maximize``).  At most ``HPO_PROPOSAL_CAP`` = 80 draws; the campaign ends
    at W charged runs (``worker_runs``) or at 80 draws (``proposal_cap``).
(c) ``run_smac3``: SMAC3 behind an import guard (``SmacUnavailable`` with a clear message when ``smac`` or
    ``ConfigSpace`` is not installed).  The facade and settings are revision 4's PROPOSED ones (§5.8, §13 item 26):
    ``HyperparameterOptimizationFacade``, ``deterministic=True``, 5 initial configurations including the default
    (the start configuration), cost = -metric.  Every ask is evaluated and charged as one worker run, so SMAC3 ends
    only at W (``proposal_cap`` never applies).  A failed run is charged and told to SMAC3 as ``WORST_COST``.
(d) Run accounting: ``HpoRunCounter``, a minimal local counter with the semantics of the G8 ``ChargedRunCounter``
    (branch ``mac-d3-g8-accounting-20261127``, not on ``main`` when this unit was written): one counter of charged
    runs, every run charged singly, a charge beyond W refused (``OverBudget``, a STOP).  Its ``charge`` signature is
    the G8 one, so the G8 class can replace it once on ``main``.  ``hpo_ended_on`` is the HPO-REF rule of
    ``d3_analysis._check_ended_on`` (the G8 ``table_ended_on`` covers the D.3a/D.3b rule only).
(e) ``campaign_summary`` (the G7 input contract ``r1_d3_campaign_summary/v1`` of branch
    ``mac-d3-g7-outcome-table-20261127``), ``audit_requests`` and ``build_row`` / ``build_table``: rows in the
    ``r1_d3_outcome/v2`` HPO-REF shape, validated by ``d3_analysis.validate_table``.

Conventions (stated, since §5.8 leaves them to the unit)
--------------------------------------------------------
* Charged run 1 of an RS campaign is the start configuration, the same first trial every D.3a arm's harness campaign
  runs; it gives the incumbent its metric.  The start configuration counts as executed (a draw equal to it is a
  skip) and, if it succeeds, as the first keep (as the harness keeps the first valid trial).  It is not a draw, so
  it does not count against the 80 draws.  SMAC3 has no separate start run: the start configuration is the default
  configuration of its initial design, and SMAC3 evaluates it as one of its asks.
* An executed configuration is the start configuration with its active keys replaced by the method's values, so
  the inactive keys keep the start values and two configurations are equal iff their active projections are.
* SMAC3 keeps: a charged run after which SMAC3's incumbent changes to another configuration.  A SMAC3 ask equal to a
  configuration already executed is still evaluated and charged (``duplicates_proposed`` and
  ``duplicates_executed`` both count it).
* The snapshot incumbent at w (``y_raw_w``) is the incumbent after the keep decision of the w-th charged run, so
  the w = 20 snapshot is the final incumbent (the analysis requires y_raw_w["20"] = y_raw).
* A worker failure of the proposal's own (``success: False``) is charged.  An infrastructure failure
  (``InfrastructureFailure`` raised by the evaluator) abandons the attempt whole: ``run_attempts`` runs the campaign
  again from the start with a fresh counter and sampler, nothing of the lost attempt is charged or kept, and the
  attempt count is recorded (§3.1; attempts are not limited; no time limit decides anything, R1-NO-TIMEOUT).
* No LLM call, no token, no proposer GPU-second, ``gpu_model`` null (§8; CPU hosts, R1-HOST-FREE (1)).
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import time
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from itertools import count
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

from r1.c3 import d3_analysis as D3

# ---------------------------------------------------------------------------------------------------------------------
# Constants (pre-declaration §5.8, §4.1, §13 item 26)
# ---------------------------------------------------------------------------------------------------------------------
HARNESS_PIN = "9bb416805175149eb87b71f28d77530572aa4bce"   # D.3 launch pin (§2, R1-D3-VERIFY-SEED)
W = D3.W
HPO_PROPOSAL_CAP = D3.HPO_PROPOSAL_CAP                      # PROPOSED (§13 item 26): 80 draws (RS) or asks (SMAC3)
RS_REPETITION_STRIDE = 1_000_000                            # §4.1: PCG64 seed = instance seed + 1,000,000 x rep
SMAC_N_INITIAL = 5                                          # PROPOSED: 5 initial configurations incl. the default
SMAC_FACADE = "HyperparameterOptimizationFacade"            # PROPOSED (§5.8)
SMAC_VERSION_REQUIRED = "2.4.0"
# Resolved SMAC3 runtime (including transitive dependencies) from the real-backend synthetic check.
SMAC_PINS = {
    "click": "8.5.1", "cloudpickle": "3.1.3", "configspace": "1.2.2", "dask": "2026.11.0",
    "dask-jobqueue": "0.9.0", "distributed": "2026.11.0", "emcee": "3.1.6", "fsspec": "2026.9.0",
    "jinja2": "3.1.6", "joblib": "1.6.0", "locket": "1.0.0", "markupsafe": "3.0.4",
    "more-itertools": "11.2.1", "msgpack": "1.2.4", "numpy": "2.4.4", "packaging": "26.4",
    "partd": "1.4.2", "psutil": "7.2.2", "pynisher": "1.0.10", "pyparsing": "3.3.3",
    "pyyaml": "6.0.4", "regex": "2026.11.25", "scikit-learn": "1.6.1", "scipy": "1.18.1",
    "smac": SMAC_VERSION_REQUIRED, "sortedcontainers": "2.4.0", "tblib": "3.2.2", "threadpoolctl": "3.8.0",
    "toolz": "1.2.0", "tornado": "6.6.1", "typing-extensions": "4.16.0", "zict": "3.0.0",
}
# PROPOSED: the metrics of the seven nodes (val_score accuracy, val_auc) lie in [0, 1]; cost = -metric lies in
# [-1, 0], so the worst cost a run can have is 0.0 and a failed run is told to SMAC3 as that cost.
WORST_COST = 0.0
NULL_TOKEN = "null"     # ConfigSpace categoricals cannot hold None; class_weight null is encoded as this string

ARMS = D3.ARMS_HPO      # ("RS", "SMAC3")
SUMMARY_SCHEMA = "r1_d3_campaign_summary/v1"   # G7's input contract (branch mac-d3-g7-outcome-table-20261127)
STAGE = "HPO-REF"

# The harness node configs at HARNESS_PIN: full sha256 of each file (§5.8 table gives the first 12 hex digits).
NODE_CONFIG_SHA256 = {
    "digits_mlp": "f830be240bd07a5dd1f49ba4cf19b8be1f0a8bdc62e34a8d813eeb1a9646cdad",
    "tabular_mlp": "971c8bda762cd1a1657c5a43cb20f2c2c94591306b80bd3cb5f5e22b9d6f9eaf",
    "openml_breast_w": "03573e6ef33aee8f98a581f18a4208c718c7374ae400dda82dd629b9dfcc34de",
    "openml_climate": "c2a9a18647cb6e35e5c97a3ea23d777ff948a4b8c4435155f6e14f46d31ee17d",
    "openml_ionosphere": "a680286e473f1de7ae463f5e07c79bd7bdbb45838766815104090d87c612c94f",
    "openml_sonar": "47e9b748b11688bc0dbd2be85d3009eb423f72c43f85d9f12cf7a7441647dc83",
    "openml_credit_approval": "3a7bef04745758aa8f4cf5a8f4428d3dcfcbac7d1a98eccd38f1e02304f1af1d",
}
# §5.8 table, first 12 hex digits as printed there (cross-checked against the full digests above in the tests).
TABLE_SHA256_PREFIX = {
    "digits_mlp": "f830be240bd0", "tabular_mlp": "971c8bda762c", "openml_breast_w": "03573e6ef33a",
    "openml_climate": "c2a9a18647cb", "openml_ionosphere": "a680286e473f", "openml_sonar": "47e9b748b116",
    "openml_credit_approval": "3a7bef047457",
}

_MLP_SPACE = {   # key: (kind, low, high, log)   -- §5.8 row 1; all five always active
    "HIDDEN_UNITS": ("int", 4, 256, False),
    "ALPHA": ("float", 1e-6, 1.0, True),
    "LEARNING_RATE_INIT": ("float", 1e-4, 0.1, True),
    "BATCH_SIZE": ("int", 8, 512, False),
    "MAX_ITER": ("int", 5, 300, False),
}
_OPENML_NUMERIC = {   # §5.8 row 2; log scales PROPOSED (§13 item 26)
    "C": ("float", 0.001, 100.0, True),
    "max_iter": ("int", 100, 3000, False),
    "n_estimators": ("int", 20, 500, False),
    "max_depth": ("int", 2, 30, False),
    "learning_rate": ("float", 0.001, 0.5, True),
}
_OPENML_CATEGORICAL = {
    "model_type": ("logistic_regression", "random_forest", "gradient_boosting"),
    "class_weight": (None, "balanced"),
    "scaler": ("none", "standard", "minmax"),
    "imputer": ("most_frequent", "constant"),
}
_OPENML_BY_MODEL_TYPE = {
    "logistic_regression": ("model_type", "C", "class_weight", "max_iter", "scaler", "imputer"),
    "random_forest": ("model_type", "n_estimators", "max_depth", "class_weight", "scaler", "imputer"),
    "gradient_boosting": ("model_type", "n_estimators", "max_depth", "learning_rate", "scaler", "imputer"),
}
_OPENML_EXCLUDED = {"openml_breast_w": ("imputer",), "openml_climate": ("imputer",),
                    "openml_ionosphere": ("imputer",), "openml_sonar": ("imputer",), "openml_credit_approval": ()}


class HpoRefError(ValueError):
    """A refusal of the HPO-REF unit (configuration space, campaign or row); nothing is written."""


class SmacUnavailable(RuntimeError):
    """The exact SMAC3 implementation or its pinned numerical stack is unavailable."""


class InfrastructureFailure(RuntimeError):
    """Raised by an evaluator for a run lost to the host or card (§3.1): the attempt is abandoned whole."""


class OverBudget(RuntimeError):
    """A charge beyond W (a campaign over W is a STOP, §10); never caught to continue."""


# ---------------------------------------------------------------------------------------------------------------------
# (a) Configuration space
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Param:
    name: str
    kind: str                      # "int" | "float" | "cat"
    low: float | None = None
    high: float | None = None
    log: bool = False
    choices: tuple = ()


@dataclass(frozen=True)
class NodeSpace:
    node: str
    config_sha256: str
    metric_direction: str
    params: tuple[Param, ...]                         # every key of the space, in declared order
    # model_type -> active keys (None: every key always active, the MLP nodes)
    active_by_model_type: Mapping[str, tuple[str, ...]] | None
    dataset_excluded: tuple[str, ...]
    editable_symbols: tuple[str, ...]

    @property
    def keys(self) -> tuple[str, ...]:
        return tuple(p.name for p in self.params)

    def param(self, name: str) -> Param:
        for p in self.params:
            if p.name == name:
                return p
        raise KeyError(name)

    def active_keys(self, config: Mapping[str, Any]) -> tuple[str, ...]:
        if self.active_by_model_type is None:
            return self.keys
        mt = config.get("model_type")
        if mt not in self.active_by_model_type:
            raise HpoRefError(f"{self.node}: model_type outside the space")
        return self.active_by_model_type[mt]

    def canonical(self, config: Mapping[str, Any]) -> tuple:
        """The active projection of a configuration (the rule layer's de-duplication key, cf.
        ``features.active_projection``): only the keys active under its model_type, sorted."""
        return tuple((k, config[k]) for k in sorted(self.active_keys(config)))


def _declared_space(node: str) -> tuple[tuple[Param, ...], dict | None, tuple[str, ...]]:
    if node in ("digits_mlp", "tabular_mlp"):
        return tuple(Param(k, kind, lo, hi, log) for k, (kind, lo, hi, log) in _MLP_SPACE.items()), None, ()
    if node not in _OPENML_EXCLUDED:
        raise HpoRefError(f"{node}: not one of the seven D.3 T0 nodes")
    excluded = _OPENML_EXCLUDED[node]
    params = [Param("model_type", "cat", choices=_OPENML_CATEGORICAL["model_type"])]
    params += [Param(k, kind, lo, hi, log) for k, (kind, lo, hi, log) in _OPENML_NUMERIC.items()]
    params += [Param(k, "cat", choices=v) for k, v in _OPENML_CATEGORICAL.items() if k != "model_type"]
    params = tuple(p for p in params if p.name not in excluded)
    active = {m: tuple(k for k in keys if k not in excluded) for m, keys in _OPENML_BY_MODEL_TYPE.items()}
    return params, active, excluded


DECLARED_SPACES = {n: _declared_space(n) for n in D3.NODES}


def read_pinned_node_config(node: str, harness_root: Path | str | None = None) -> bytes:
    """``configs/nodes/<node>.yaml`` at ``HARNESS_PIN`` from the harness checkout (``git show``; no worktree read)."""
    if harness_root is None:
        from r1.harness import harness_root as _hr
        harness_root = _hr()
    out = subprocess.run(["git", "-C", str(harness_root), "show", f"{HARNESS_PIN}:configs/nodes/{node}.yaml"],
                         capture_output=True, check=False)
    if out.returncode != 0:
        raise HpoRefError(f"{node}: node config at the harness pin is not readable")
    return out.stdout


def _num_eq(a, b) -> bool:
    return (not isinstance(a, bool) and not isinstance(b, bool) and isinstance(a, (int, float))
            and isinstance(b, (int, float)) and float(a) == float(b))


def load_node_space(node: str, config_bytes: bytes | None = None, *, harness_root=None) -> NodeSpace:
    """Node ``node``'s configuration space, from the pinned node config, checked against the §5.8 table."""
    if node not in D3.NODES:
        raise HpoRefError(f"{node}: not one of the seven D.3 T0 nodes")
    raw = config_bytes if config_bytes is not None else read_pinned_node_config(node, harness_root)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != NODE_CONFIG_SHA256[node]:
        raise HpoRefError(f"{node}: node config sha256 differs from the file at the harness pin")
    cfg = json.loads(raw)
    params, active, excluded = DECLARED_SPACES[node]
    if cfg.get("name") != node or cfg.get("metric_direction") != "maximize":
        raise HpoRefError(f"{node}: node name or metric_direction differs from §5.8 (maximize)")
    editable = tuple(cfg.get("editable_symbols") or ())
    ranges = cfg.get("allowed_ranges") or {}
    values = cfg.get("allowed_values") or {}
    names = {p.name for p in params}
    # The space is exactly what manager_proposal/v1 admits, minus the dataset-excluded (always inactive) keys.
    if set(editable) != names | set(excluded):
        raise HpoRefError(f"{node}: the space's keys differ from the proposal schema's editable_symbols")
    if set(ranges) | set(values) != set(editable) or set(ranges) & set(values):
        raise HpoRefError(f"{node}: allowed_ranges and allowed_values do not partition editable_symbols")
    for p in params:
        if p.kind == "cat":
            if p.name not in values or tuple(values[p.name]) != p.choices:
                raise HpoRefError(f"{node}: allowed_values of {p.name} differ from §5.8")
        else:
            lo_hi = ranges.get(p.name)
            if not isinstance(lo_hi, list) or len(lo_hi) != 2 or not (_num_eq(lo_hi[0], p.low)
                                                                    and _num_eq(lo_hi[1], p.high)):
                raise HpoRefError(f"{node}: allowed_ranges of {p.name} differ from §5.8")
            is_int = all(isinstance(v, int) and not isinstance(v, bool) for v in lo_hi)
            if is_int != (p.kind == "int"):
                raise HpoRefError(f"{node}: integer type of {p.name} differs from §5.8")
    for k in excluded:   # always inactive, but the schema still admits it: its values must be known
        if k not in values and k not in ranges:
            raise HpoRefError(f"{node}: dataset-excluded key {k} not admitted by the schema")
    decl = cfg.get("active_keys")
    if active is None:
        if decl:
            raise HpoRefError(f"{node}: §5.8 declares every key always active, the node config declares active_keys")
    else:
        if not isinstance(decl, dict):
            raise HpoRefError(f"{node}: active_keys missing from the node config")
        if tuple(decl.get("dataset_excluded") or ()) != excluded:
            raise HpoRefError(f"{node}: active_keys.dataset_excluded differs from §5.8")
        by = decl.get("by_model_type") or {}
        if set(by) != set(active):
            raise HpoRefError(f"{node}: active_keys.by_model_type names other model types than §5.8")
        for m, keys in by.items():
            if tuple(k for k in keys if k not in excluded) != active[m]:
                raise HpoRefError(f"{node}: active keys under {m} differ from §5.8")
    return NodeSpace(node=node, config_sha256=digest, metric_direction="maximize", params=params,
                     active_by_model_type=active, dataset_excluded=excluded, editable_symbols=editable)


def check_start_config(space: NodeSpace, start: Mapping[str, Any]) -> dict:
    """The start configuration must set every editable symbol, and every key of the space within its bounds."""
    start = dict(start)
    if set(start) != set(space.editable_symbols):
        raise HpoRefError(f"{space.node}: the start configuration must set exactly the editable symbols")
    for p in space.params:
        if not _in_param(p, start[p.name]):
            raise HpoRefError(f"{space.node}: start value of {p.name} outside the space")
    return start


def _in_param(p: Param, v) -> bool:
    if p.kind == "cat":
        return v in p.choices
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
        return False
    if p.kind == "int" and not (isinstance(v, int) or float(v).is_integer()):
        return False
    return p.low <= v <= p.high


def full_config(space: NodeSpace, start: Mapping[str, Any], active_values: Mapping[str, Any]) -> dict:
    """The executed configuration: the start configuration with the active keys replaced (inactive keys keep the
    start values, so equality of executed configurations is equality of active projections)."""
    out = dict(start)
    keys = space.active_keys(active_values)
    if set(active_values) != set(keys):
        raise HpoRefError(f"{space.node}: a proposed configuration must set exactly its active keys")
    for k in keys:
        if not _in_param(space.param(k), active_values[k]):
            raise HpoRefError(f"{space.node}: proposed value of {k} outside the space")
        out[k] = active_values[k]
    return out


def default_config_sha256(config: Mapping[str, Any]) -> str:
    """sha256 of the canonical JSON of a key/value configuration.  The D.3 runner must pass G1's hash of the
    rendered editable files instead (``check_pair`` compares start hashes with D.3a's)."""
    return hashlib.sha256(json.dumps(dict(config), sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


# ---------------------------------------------------------------------------------------------------------------------
# (d) Run accounting
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ChargedRun:
    w: int
    kind: str
    role: str
    seed: int
    config_sha256: str
    success: bool
    j: int | None = None
    metric: float | None = None
    seconds: float = 0.0


@dataclass
class HpoRunCounter:
    """Minimal local stand-in for the G8 ``ChargedRunCounter`` (same ``charge`` signature and semantics): every run
    is charged singly; a charge beyond W is refused with ``OverBudget``; ``on_charge`` sees every charge."""

    W: int
    on_charge: Callable[[ChargedRun], Any] | None = None
    runs: list[ChargedRun] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.W, int) or isinstance(self.W, bool) or self.W < 1:
            raise ValueError("W must be an integer >= 1")
        if self.runs:
            raise ValueError("a counter starts empty (no resume)")

    @property
    def used(self) -> int:
        return len(self.runs)

    @property
    def left(self) -> int:
        return self.W - self.used

    def charge(self, *, kind: str, role: str, seed: int, config_sha256: str, success: bool, j: int | None = None,
               metric: float | None = None, seconds: float = 0.0) -> ChargedRun:
        if kind != "trial" or role != "candidate":
            raise ValueError("HPO-REF charges trial runs of candidates only")
        if not isinstance(success, bool):
            raise ValueError("success must be a boolean")
        if metric is not None and not math.isfinite(float(metric)):
            raise ValueError("a recorded metric must be finite (a non-finite result is a failed run)")
        if success and metric is None:
            raise ValueError("a successful run records its metric")
        if self.left < 1:
            raise OverBudget(f"charge beyond W = {self.W} (a campaign over W is a STOP, §10)")
        run = ChargedRun(w=self.used + 1, kind=kind, role=role, seed=int(seed), config_sha256=str(config_sha256),
                         success=success, j=j, metric=None if metric is None else float(metric),
                         seconds=max(float(seconds), 0.0))
        self.runs.append(run)
        if self.on_charge is not None:
            self.on_charge(run)
        return run


def hpo_ended_on(*, arm: str, worker_runs: int, proposals: int) -> str:
    """``ended_on`` of a reference row by ``d3_analysis._check_ended_on``'s HPO-REF rule."""
    if arm not in ARMS:
        raise HpoRefError(f"{arm}: not a reference arm")
    if worker_runs > W or proposals > HPO_PROPOSAL_CAP:
        raise OverBudget("a reference campaign over W or over the proposal cap is a STOP")
    if worker_runs == W:
        return "worker_runs"
    if arm == "RS" and proposals == HPO_PROPOSAL_CAP:
        return "proposal_cap"
    raise HpoRefError("the reference campaign has not ended (below W and, for RS, below the proposal cap)")


# ---------------------------------------------------------------------------------------------------------------------
# Campaign record
# ---------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EvalResult:
    success: bool
    metric: float | None = None
    seconds: float = 0.0


# evaluator(node, full_config, seed) -> EvalResult; seed is train seed = split seed (the instance seed).  It may
# raise InfrastructureFailure.  No time limit is imposed here (R1-NO-TIMEOUT).
Evaluator = Callable[[str, dict, int], EvalResult]


@dataclass
class Campaign:
    arm: str
    node: str
    instance_seed: int
    repetition: int
    start_config: dict
    start_config_hash: str
    hasher: Callable[[Mapping[str, Any]], str]
    counter: HpoRunCounter
    proposals: int = 0
    duplicates_proposed: int = 0
    duplicates_executed: int = 0
    rule_skips: int = 0
    incumbent: dict | None = None        # configuration of the last keep (None: no keep yet; the start is used)
    incumbent_metric: float | None = None
    keeps: list[tuple[int, dict]] = field(default_factory=list)    # (charged run w, configuration)
    executed: list[dict] = field(default_factory=list)            # configurations of the charged runs, in order
    snapshots: dict[int, dict] = field(default_factory=dict)       # w -> incumbent after run w's keep decision
    controller_seconds: float = 0.0
    wall_seconds: float = 0.0
    infra_attempts: int = 1
    ended_on: str | None = None

    @property
    def worker_runs(self) -> int:
        return self.counter.used

    @property
    def final_config(self) -> dict:
        return dict(self.incumbent if self.incumbent is not None else self.start_config)

    def _execute(self, config: dict, evaluator: Evaluator) -> ChargedRun:
        res = evaluator(self.node, dict(config), self.instance_seed)
        if not isinstance(res, EvalResult):
            raise HpoRefError("the evaluator must return an EvalResult")
        ok = bool(res.success) and res.metric is not None and math.isfinite(float(res.metric))
        run = self.counter.charge(kind="trial", role="candidate", seed=self.instance_seed,
                                  config_sha256=self.hasher(config), success=ok,
                                  metric=float(res.metric) if ok else None, seconds=res.seconds)
        self.executed.append(dict(config))
        return run

    def _record_keep(self, run: ChargedRun, config: dict, metric: float | None) -> None:
        self.incumbent, self.incumbent_metric = dict(config), metric
        self.keeps.append((run.w, dict(config)))

    def _snapshot(self) -> None:
        if self.worker_runs in D3.BUDGET_POINTS:
            self.snapshots[self.worker_runs] = self.final_config


def _new_campaign(arm, space, start, instance_seed, repetition, hasher) -> Campaign:
    if not isinstance(instance_seed, int) or instance_seed not in D3.INSTANCE_SEEDS:
        raise HpoRefError("not a declared D.3 instance seed")
    if repetition not in range(2):
        raise HpoRefError("repetition must be 0 or 1")
    start = check_start_config(space, start)
    return Campaign(arm=arm, node=space.node, instance_seed=instance_seed, repetition=repetition,
                    start_config=start, start_config_hash=hasher(start), hasher=hasher, counter=HpoRunCounter(W))


# ---------------------------------------------------------------------------------------------------------------------
# (b) Random search with de-duplication
# ---------------------------------------------------------------------------------------------------------------------
def rs_generator(instance_seed: int, repetition: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(int(instance_seed) + RS_REPETITION_STRIDE * int(repetition)))


def _draw_param(p: Param, rng: np.random.Generator):
    if p.kind == "cat":
        return p.choices[int(rng.integers(len(p.choices)))]
    if p.kind == "int":
        return int(rng.integers(int(p.low), int(p.high) + 1))
    if p.log:
        return float(math.exp(rng.uniform(math.log(p.low), math.log(p.high))))
    return float(rng.uniform(p.low, p.high))


def draw_configuration(space: NodeSpace, rng: np.random.Generator) -> dict:
    """One uniform draw on the active keys: model_type first (if any), then each active key in declared order."""
    values: dict[str, Any] = {}
    if space.active_by_model_type is not None:
        values["model_type"] = _draw_param(space.param("model_type"), rng)
    active = space.active_keys(values)
    for p in space.params:
        if p.name not in values and p.name in active:
            values[p.name] = _draw_param(p, rng)
    return values


def _run_rs_attempt(space, start, instance_seed, repetition, evaluator, hasher, clock) -> Campaign:
    c = _new_campaign("RS", space, start, instance_seed, repetition, hasher)
    t_wall = clock()
    rng = rs_generator(instance_seed, repetition)
    # Charged run 1: the start configuration (the harness's first trial of every D.3a arm).
    run = c._execute(c.start_config, evaluator)
    if run.success:
        c._record_keep(run, c.start_config, run.metric)
    c._snapshot()
    while c.worker_runs < W and c.proposals < HPO_PROPOSAL_CAP:
        t0 = clock()
        cfg = full_config(space, start, draw_configuration(space, rng))
        c.proposals += 1
        key = space.canonical(cfg)
        noop = key == space.canonical(c.final_config)
        seen = any(space.canonical(e) == key for e in c.executed)
        c.controller_seconds += max(clock() - t0, 0.0)
        if noop or seen:
            c.rule_skips += 1                       # skipped, charged no run (§5.8)
            c.duplicates_proposed += int(not noop)  # the rule layer's duplicate flag (no-ops are not duplicates)
            continue
        run = c._execute(cfg, evaluator)
        if run.success and (c.incumbent_metric is None or run.metric - c.incumbent_metric > 0):
            c._record_keep(run, cfg, run.metric)
        c._snapshot()
    c.ended_on = hpo_ended_on(arm="RS", worker_runs=c.worker_runs, proposals=c.proposals)
    c.wall_seconds = max(clock() - t_wall, 0.0)
    return c


# ---------------------------------------------------------------------------------------------------------------------
# (c) SMAC3
# ---------------------------------------------------------------------------------------------------------------------
def require_smac():
    """Check installed distribution metadata before using the real ask/tell backend."""
    try:
        installed = {name: version(name) for name in SMAC_PINS}
    except PackageNotFoundError as exc:
        raise SmacUnavailable(f"SMAC3 is not installed with its pinned numerical environment: {exc}") from exc
    wrong = {name: (installed[name], pin) for name, pin in SMAC_PINS.items() if installed[name] != pin}
    if wrong:
        raise SmacUnavailable(f"SMAC3 distribution versions differ from the reviewed pins: {wrong}")
    try:
        import ConfigSpace  # noqa: F401
        import smac
    except ImportError as exc:
        raise SmacUnavailable(f"SMAC3 cannot import from its pinned numerical environment: {exc}") from exc
    return smac


def _encode(v):
    return NULL_TOKEN if v is None else v


def _decode(p: Param, v):
    if p.kind == "cat":
        return None if (v == NULL_TOKEN and None in p.choices) else v
    if p.kind == "int":
        return int(v)
    return float(v)


def build_configspace(space: NodeSpace, start: Mapping[str, Any], seed: int):
    """The node's space as a ConfigSpace (>= 1.0 API) with the conditions of ``active_keys`` and the start
    configuration as the default.  Needs ConfigSpace (imported here only)."""
    from ConfigSpace import Categorical, ConfigurationSpace, Float, InCondition, Integer
    cs = ConfigurationSpace(seed=seed)
    hps = {}
    for p in space.params:
        if p.kind == "cat":
            hps[p.name] = Categorical(p.name, [_encode(v) for v in p.choices], default=_encode(start[p.name]))
        elif p.kind == "int":
            hps[p.name] = Integer(p.name, (int(p.low), int(p.high)), default=int(start[p.name]), log=p.log)
        else:
            hps[p.name] = Float(p.name, (float(p.low), float(p.high)), default=float(start[p.name]), log=p.log)
    cs.add(*hps.values())
    if space.active_by_model_type is not None:
        conds = []
        for p in space.params:
            if p.name == "model_type":
                continue
            where = [m for m, keys in space.active_by_model_type.items() if p.name in keys]
            if len(where) < len(space.active_by_model_type):
                conds.append(InCondition(hps[p.name], hps["model_type"], where))
        if conds:
            cs.add(*conds)
    return cs


class Smac3Backend:
    """The pinned SMAC3 §5.8 ask/tell loop in an exclusive, per-attempt directory."""

    def __init__(self, space: NodeSpace, start: Mapping[str, Any], seed: int, *, output_directory: Path):
        require_smac()
        from smac import HyperparameterOptimizationFacade, Scenario
        from smac.runhistory.dataclasses import TrialValue
        from smac.runhistory.enumerations import StatusType
        self._space, self._TrialValue, self._Status = space, TrialValue, StatusType
        cs = build_configspace(space, start, seed)
        output_directory = Path(output_directory)
        output_directory.mkdir(exist_ok=False)
        scenario = Scenario(cs, deterministic=True, n_trials=W, seed=seed, crash_cost=WORST_COST,
                            output_directory=output_directory)
        initial = HyperparameterOptimizationFacade.get_initial_design(
            scenario, n_configs=SMAC_N_INITIAL - 1, additional_configs=[cs.get_default_configuration()])
        self._smac = HyperparameterOptimizationFacade(scenario, target_function=lambda config, seed=0: 0.0,
                                                      initial_design=initial, overwrite=False, logging_level=40)
        self._pending = None

    def _values(self, config) -> dict:
        d = dict(config)
        return {k: _decode(self._space.param(k), v) for k, v in d.items()}

    def ask(self) -> dict:
        if self._pending is not None:
            raise HpoRefError("SMAC3: ask before the previous ask was told")
        self._pending = self._smac.ask()
        return self._values(self._pending.config)

    def tell(self, cost: float, crashed: bool) -> None:
        if self._pending is None:
            raise HpoRefError("SMAC3: tell without a pending ask")
        status = self._Status.CRASHED if crashed else self._Status.SUCCESS
        self._smac.tell(self._pending, self._TrialValue(cost=float(cost), status=status))
        self._pending = None

    def incumbent(self) -> dict | None:
        inc = self._smac.intensifier.get_incumbent()
        return None if inc is None else self._values(inc)


def smac_seed(instance_seed: int, repetition: int) -> int:
    return int(instance_seed) + int(repetition)    # §4.1: Scenario(seed=<instance seed>), plus the repetition


def _run_smac_attempt(space, start, instance_seed, repetition, evaluator, hasher, clock, backend_factory) -> Campaign:
    c = _new_campaign("SMAC3", space, start, instance_seed, repetition, hasher)
    t_wall = clock()
    t0 = clock()
    backend = backend_factory(space, c.start_config, smac_seed(instance_seed, repetition))
    c.controller_seconds += max(clock() - t0, 0.0)
    while c.worker_runs < W:
        if c.proposals >= HPO_PROPOSAL_CAP:     # cannot happen: every ask is charged and W < the cap
            raise OverBudget("SMAC3 asks reached the proposal cap below W")
        t0 = clock()
        cfg = full_config(space, start, backend.ask())
        c.controller_seconds += max(clock() - t0, 0.0)
        c.proposals += 1
        dup = any(space.canonical(e) == space.canonical(cfg) for e in c.executed)
        c.duplicates_proposed += int(dup)
        c.duplicates_executed += int(dup)
        run = c._execute(cfg, evaluator)          # every ask evaluated and charged
        t0 = clock()
        backend.tell(-run.metric if run.success else WORST_COST, crashed=not run.success)
        inc = backend.incumbent()
        c.controller_seconds += max(clock() - t0, 0.0)
        if inc is not None:
            inc_cfg = full_config(space, start, inc)
            if c.incumbent is None or space.canonical(inc_cfg) != space.canonical(c.incumbent):
                if not any(space.canonical(e) == space.canonical(inc_cfg) for e in c.executed):
                    raise HpoRefError("SMAC3 named an incumbent that was never evaluated")
                c._record_keep(run, inc_cfg, None)   # SMAC3's own incumbent; no keep rule of ours
        c._snapshot()
    if inc is None:
        raise HpoRefError("SMAC3 completed W evaluations without naming an incumbent")
    c.ended_on = hpo_ended_on(arm="SMAC3", worker_runs=c.worker_runs, proposals=c.proposals)
    c.wall_seconds = max(clock() - t_wall, 0.0)
    return c


# ---------------------------------------------------------------------------------------------------------------------
# Attempts (§3.1) and the public runners
# ---------------------------------------------------------------------------------------------------------------------
def run_attempts(attempt: Callable[[], Campaign]) -> Campaign:
    """Run a campaign attempt until one completes; an ``InfrastructureFailure`` discards the attempt whole (nothing
    of it is charged or kept; a fresh counter and sampler start the next).  Attempts are not limited (§3.1 item 1)."""
    n = 0
    while True:
        n += 1
        try:
            c = attempt()
        except InfrastructureFailure:
            continue
        c.infra_attempts = n
        return c


def run_rs(space: NodeSpace, start: Mapping[str, Any], instance_seed: int, repetition: int, evaluator: Evaluator,
           *, hasher=default_config_sha256, clock=time.perf_counter) -> Campaign:
    return run_attempts(lambda: _run_rs_attempt(space, start, instance_seed, repetition, evaluator, hasher, clock))


def run_smac3(space: NodeSpace, start: Mapping[str, Any], instance_seed: int, repetition: int, evaluator: Evaluator,
              *, hasher=default_config_sha256, clock=time.perf_counter, backend_factory=None,
              output_root: Path | None = None) -> Campaign:
    if backend_factory is None:
        require_smac()
        if output_root is None:
            raise HpoRefError("SMAC3 needs a fresh output root for its attempts")
        output_root = Path(output_root)
        output_root.mkdir(parents=True, exist_ok=False)
        attempts = count(1)

        def backend_factory(space, start, seed):
            return Smac3Backend(space, start, seed, output_directory=output_root / f"attempt-{next(attempts):03d}")

    return run_attempts(lambda: _run_smac_attempt(space, start, instance_seed, repetition, evaluator, hasher, clock,
                                                  backend_factory))


# ---------------------------------------------------------------------------------------------------------------------
# (e) Summary, audit requests, rows and table
# ---------------------------------------------------------------------------------------------------------------------
def campaign_summary(c: Campaign) -> dict:
    """The campaign in G7's ``r1_d3_campaign_summary/v1`` shape (branch mac-d3-g7-outcome-table-20261127)."""
    if c.ended_on is None:
        raise HpoRefError("the campaign has not ended")
    seconds = sum(r.seconds for r in c.counter.runs)
    return {"schema": SUMMARY_SCHEMA, "stage": STAGE, "arm": c.arm, "node": c.node, "instance_seed": c.instance_seed,
            "repetition": c.repetition, "status": "complete", "gpu_model": None, "infra_attempts": c.infra_attempts,
            "worker_runs": c.worker_runs, "llm_calls": 0, "unfundable": False,
            "start_config_hash": c.start_config_hash, "final_config_hash": c.hasher(c.final_config),
            "last_keep_run": c.keeps[-1][0] if c.keeps else None, "proposals": c.proposals,
            "llm_tokens_prompt": 0, "llm_tokens_completion": 0, "worker_seconds": float(seconds),
            "proposer_gpu_seconds": 0.0, "controller_seconds": float(c.controller_seconds),
            "wall_seconds": float(c.wall_seconds), "duplicates_proposed": c.duplicates_proposed,
            "duplicates_executed": c.duplicates_executed, "rule_skips": c.rule_skips, "value_skips": 0,
            "keeps": len(c.keeps), "distinct_configs_executed": len({c.hasher(e) for e in c.executed})}


def audit_requests(c: Campaign) -> list[dict]:
    """The configurations G6 must audit as Y is (§7.1, §7.5 (a), (d)): the final incumbent, the snapshots at the
    budget points the campaign reached, and every kept incumbent.  The start configuration needs no audit (0)."""
    out = [{"point": "final", "keep_run": None, "config": c.final_config}]
    out += [{"point": str(w), "keep_run": None, "config": c.snapshots[w]} for w in sorted(c.snapshots)]
    out += [{"point": "keep", "keep_run": w, "config": cfg} for w, cfg in c.keeps]
    return out


def _last_improving_run(keep_ys: Iterable[tuple[int, float]]) -> int | None:
    prev, last = 0.0, None     # the start configuration's y_raw is 0 by rule
    for run, y in sorted(keep_ys):
        if y > prev:
            last = run
        prev = y
    return last


def build_row(c: Campaign, audit: Callable[[dict], float]) -> dict:
    """One ``r1_d3_outcome/v2`` HPO-REF row.  ``audit(config)`` is G6's y_raw of a configuration against the start
    on the instance's audit seeds; it is not called for a configuration equal to the start (y_raw = 0 by rule)."""
    s = campaign_summary(c)
    cache: dict[str, float] = {}

    def y_of(cfg: dict) -> float:
        h = c.hasher(cfg)
        if h == c.start_config_hash:
            return 0.0
        if h not in cache:
            y = audit(dict(cfg))
            if isinstance(y, bool) or not isinstance(y, (int, float)) or not math.isfinite(float(y)):
                raise HpoRefError("an audit y_raw must be finite (a non-finite audit is a STOP)")
            cache[h] = float(y)
        return cache[h]

    runs = s["worker_runs"]
    y_raw = y_of(c.final_config)
    y_w = {str(w): (y_of(c.snapshots[w]) if runs >= w else None) for w in D3.BUDGET_POINTS}
    if runs >= W and c.hasher(c.snapshots[W]) != s["final_config_hash"]:
        raise HpoRefError("the w = 20 snapshot must be the final incumbent")
    seed = c.instance_seed
    row = {"campaign_id": D3.campaign_id(STAGE, c.arm, c.node, seed, c.repetition), "stage": STAGE, "arm": c.arm,
           "node": c.node, "instance_id": D3.instance_id(c.node, seed), "instance_seed": seed,
           "repetition": c.repetition, "memory_mode": D3.HPO_MEMORY_MODE, "status": "complete", "y_raw": y_raw,
           "worker_runs": runs, "llm_calls": 0, "ended_on": c.ended_on,
           "audit_seeds": list(D3.audit_seeds(seed)), "start_config_hash": s["start_config_hash"],
           "final_config_hash": s["final_config_hash"], "gpu_model": None, "infra_attempts": s["infra_attempts"],
           "y_raw_w": y_w, "last_keep_run": s["last_keep_run"],
           "last_improving_run": _last_improving_run((w, y_of(cfg)) for w, cfg in c.keeps)}
    for key in (*D3.COMPUTE_INT_KEYS, *D3.COMPUTE_SECONDS_KEYS, *D3.MECHANISM_KEYS):
        row[key] = s[key]
    return row


def build_table(rows: Sequence[dict], *, predeclaration_sha256: str, sigma_node: Mapping[str, float],
                repetitions: int = D3.REPETITIONS) -> dict:
    """The HPO-REF table, validated by the pinned analysis (``d3_analysis.validate_table``) before it is returned."""
    table = {"schema": D3.SCHEMA, "stage": STAGE, "predeclaration_sha256": predeclaration_sha256,
             "noise_source_sha256": D3.NOISE_SOURCE_SHA256, "sigma_node": dict(sigma_node), "arms": list(ARMS),
             "a6_entered": None, "repetitions": repetitions,
             "rows": sorted(rows, key=lambda r: (ARMS.index(r["arm"]), r["node"], r["instance_seed"],
                                                 r["repetition"]))}
    return D3.validate_table(table, STAGE)
