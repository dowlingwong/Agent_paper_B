"""T1 proposal features for the G.5 label table (ARMS-T1FEAT A), and the T1 suite-name mapping. AI-assisted (Claude).
ENGINEERING_ONLY code; the features are computed inside the G.5 assembly (``g5_assemble``) from the sealed campaign
ledgers, so they are part of the table bytes and are re-derived byte-identically at the test stage.

Authority: the frozen preregistration's PRE-JOINT A ("each arm is one model over all nodes of both tiers (node and tier
as features)"); the T0 arms readiness report's ARMS-T1FEAT A (node codes appended for the T1 nodes, fields that do not
apply set to NaN, the tier carried by the node code, the mapping of code-level diffs decided in this unit); the G.5 code
unit part 3b-2 report §5 items 4 and 5. The report of this unit is
``docs/r1/reports/arms_t1feat_20261123/T1_FEATURES_20261123.md``; it gives the source of every field.

**The schema.** A T1 row carries exactly the featurizer-v3 fields of the T0 rows (``FEATURES_V3``, a copy of
``r1.c3.features.FEATURES``; a test checks equality), so ``arms.feature_matrix`` and ``arms_freeze.training_rows`` take
T1 rows unchanged. ``r1/c3/features.py`` is not changed: its ``NODE_INFO``, ``NODE_CODES``, ``NodeContext`` and
``FEATURIZER_VERSION`` stay as they are, so every T0 feature value and every T0 pin stays valid. The T1 node table is
``T1_NODE_INFO`` here; its codes start at ``FIRST_T1_CODE`` = 11, after the eleven T0 codes 0-10, so one
``node_code`` column serves both tiers and the tier is a function of the code (``tier_of_code``).

**What a T1 ledger holds** (harness ``trackg/campaign_v2_diff.py``, ledger
``trackg_v2_diff_campaign_ledger/v1``): step 0 is the baseline run; each step 1..W is one charged manager call (G5-W A:
W counts manager calls) with its decision, the proposal's unified diff, the run records (``manager_view``; for a diff,
``diff`` holds the pre-execution provenance of ``diff_support.apply_diff``: the normalised and raw code-state hashes of
the incumbent and of the candidate) and ``best_after``. There is no structured key/old/new edit, no model-type field
and no dataset descriptor.

**The fields, in three groups** (the report has the table):
- *Same definition as T0*: ``node_code`` (T1 codes), ``keeps_so_far``, ``trials_since_keep``, ``recorded_gain_z``
  (signed by the metric direction, as the table's Δ̂), ``budget_frac_left`` (1 − charged manager calls before the step
  / W: the budget the T1 campaign stops on), ``budget_index`` (the step), ``memory_on``, ``invalid_so_far``.
- *Code-state counterpart* (declared): ``active_equals_incumbent`` (candidate normalised code state = incumbent's,
  i.e. the harness inert rule), ``cfg_equals_incumbent`` (raw code states equal), ``active_seen_before`` (normalised
  state among the states the harness registers as evaluated before the step: the baseline and every executed
  proposal except an infrastructure-final one; the harness duplicate rule), ``full_seen_before`` (the same over raw
  states). A record without raw code states gives NaN for the two raw fields; ``featurize_ledger`` counts such rows.
- *No T1 source*: ``NO_T1_SOURCE``; numeric ones are NaN, categorical ones ``MISSING_CATEGORICAL`` (-1: LightGBM
  treats a negative categorical value as missing; T0 already uses -1 in ``new_cat_code``).

**Leakage** (C3_DESIGN §3 rule, as in ``r1.c3.features``): the features of step n read the ledger lines of steps < n
and, of step n itself, only ``proposal_side`` (its step number and the candidate's code-state hashes from the run
record, which the harness computes from the diff before anything runs). Step n's decision, outcome, metric and
``best_after`` and every later line are not read.
"""
from __future__ import annotations

import math

FEATURIZER = "g5_t1_features/1"
# A copy of r1.c3.features.FEATURES / CAT_FEATURES (featurizer v3; r1/tests/test_t1_features.py checks equality).
# Copied, not imported, so that the G.5 assembly depends only on files under the G.5 paths that the release step's
# integrity check verifies (r1/c3/release_checks.G5_PATHS).
CAT_FEATURES_V3 = ("node_code", "key_code", "model_type_code", "new_cat_code")
NUM_FEATURES_V3 = (
    "rows_log", "n_features", "n_classes", "minority",
    "old_num", "new_num", "log_ratio", "direction", "structural", "active_key",
    "cfg_equals_incumbent", "active_equals_incumbent", "active_seen_before", "full_seen_before",
    "key_edit_count", "last_key_delta_z", "last_key_kept", "keeps_so_far", "trials_since_keep",
    "recorded_gain_z", "budget_frac_left", "budget_index", "memory_on", "invalid_so_far",
    "same_edit_count", "reverse_of_last_key_edit",
)
FEATURES_V3 = CAT_FEATURES_V3 + NUM_FEATURES_V3
MISSING_CATEGORICAL = -1
# Fields with no source in a T1 ledger (the report §2 says why for each).
NO_T1_SOURCE = ("key_code", "model_type_code", "new_cat_code", "rows_log", "n_features", "n_classes", "minority",
                "old_num", "new_num", "log_ratio", "direction", "structural", "active_key", "key_edit_count",
                "last_key_delta_z", "last_key_kept", "same_edit_count", "reverse_of_last_key_edit")
RAW_STATE_FIELDS = ("cfg_equals_incumbent", "full_seen_before")

# The suite names of the T1 node specs (``suite:`` line, read at the family's G.5 commit by
# ``g5_assemble.node_metric``) -> the names of ``r1.c3.gate.SUITES`` (R1-BX-D2 as amended by R1-1GC-FALLBACK), which
# the arms-frozen record's ``Tier1.suites`` must use. The one place this mapping lives.
SUITE_NAMES = {"autoresearch": "autoresearch", "mlagentbench": "MLAgentBench", "mlgym": "MLGym"}

# The eight G.5 nodes (sweep2/t1_tasl/g5_tasl_spec.json, in its order) with the suite their node spec names. Codes are
# appended after the T0 codes 0-10 of r1.c3.features.NODE_CODES and never reused.
FIRST_T1_CODE = 11
T1_NODE_INFO = {
    "mlab_cifar10": {"suite": "mlagentbench", "code": 11},
    "mlab_imdb": {"suite": "mlagentbench", "code": 12},
    "mlab_ogbn_arxiv": {"suite": "mlagentbench", "code": 13},
    "mlgym_cifar10": {"suite": "mlgym", "code": 14},
    "mlgym_fmnist": {"suite": "mlgym", "code": 15},
    "mlgym_breakout_minatar": {"suite": "mlgym", "code": 16},
    "mlgym_houseprice": {"suite": "mlgym", "code": 17},
    "autoresearch_fixedtokens": {"suite": "autoresearch", "code": 18},
}
T1_NODE_CODES = {n: v["code"] for n, v in T1_NODE_INFO.items()}
assert len(set(T1_NODE_CODES.values())) == len(T1_NODE_CODES) and min(T1_NODE_CODES.values()) == FIRST_T1_CODE

RAN = ("kept", "discarded", "discarded_divergent")          # executed; the harness registers the code state
# Steps that leave no metric (the T0 ``invalid_so_far`` counts trials without a metric): an unparseable reply, a
# refused diff, a run that diverged or timed out, an infrastructure failure after the reruns. Inert and duplicate
# diffs are valid proposals that the harness does not run; they are not counted.
INVALID = ("invalid_proposal", "not_run_refused", "discarded_divergent", "infrastructure_failure_final")


class FeatureError(ValueError):
    """A ledger the T1 featurizer cannot read as a complete G.5 campaign ledger."""


def tier_of_code(code: int) -> str:
    """The tier a ``node_code`` belongs to (PRE-JOINT A: the tier is carried by the node code)."""
    return "T1" if int(code) >= FIRST_T1_CODE else "T0"


def gate_suite(spec_suite: str) -> str:
    """The ``gate.SUITES`` name of a node spec's suite; an unknown suite is an error, never a guess."""
    if spec_suite not in SUITE_NAMES:
        raise FeatureError(f"no gate suite for node-spec suite {spec_suite!r} (SUITE_NAMES)")
    return SUITE_NAMES[spec_suite]


def check_node(node: str, spec_suite: str) -> int:
    """The node's T1 code, after checking that the node is a declared T1 node and that its node spec names the suite
    declared here."""
    info = T1_NODE_INFO.get(node)
    if info is None:
        raise FeatureError(f"{node} is not a declared T1 node (T1_NODE_INFO)")
    if spec_suite != info["suite"]:
        raise FeatureError(f"{node}'s node spec names suite {spec_suite!r}, T1_NODE_INFO declares {info['suite']!r}")
    return info["code"]


def tier1_suites(node_suites: dict) -> dict:
    """{node: gate suite} for ``gate_input_builder.Tier1.suites`` from {node: node-spec suite} (for example the
    ``suite`` of each node in the G.5 table's ``build.json``)."""
    out = {}
    for node, s in sorted(node_suites.items()):
        check_node(node, s)
        out[node] = gate_suite(s)
    return out


def describe() -> dict:
    """What the table's ``build.json`` records about the featurizer."""
    return {"version": FEATURIZER, "fields": list(FEATURES_V3), "node_codes": dict(T1_NODE_CODES),
            "missing_categorical": MISSING_CATEGORICAL, "no_t1_source": list(NO_T1_SOURCE),
            "raw_state_fields": list(RAW_STATE_FIELDS), "suite_names": dict(SUITE_NAMES)}


def _states(run: dict) -> tuple[str | None, str | None]:
    """(normalised, raw) candidate code state of a run record: the diff provenance first, then the record's own."""
    prov = run.get("diff") if isinstance(run.get("diff"), dict) else {}
    norm = prov.get("code_state_sha256") or run.get("code_state_sha256")
    raw = prov.get("code_state_raw_sha256") or run.get("code_state_raw_sha256")
    return norm, raw


def proposal_side(entry: dict) -> dict | None:
    """The only part of step n's own line the features of step n read: its step number and the candidate's code
    states (computed by the harness from the diff before the run). None when the step has no candidate state (an
    invalid reply, a refused diff)."""
    runs = entry.get("runs") or []
    if not runs:
        return None
    norm, raw = _states(runs[-1])
    if not norm:
        return None
    return {"step": entry.get("step"), "cand": norm, "cand_raw": raw}


class _History:
    """The campaign seen through the ledger lines before the current step."""

    def __init__(self, baseline: dict) -> None:
        if baseline.get("step") != 0 or baseline.get("decision") != "baseline":
            raise FeatureError("the ledger does not start with a baseline line")
        runs = baseline.get("runs") or []
        norm, raw = _states(runs[-1]) if runs else (None, None)
        value = baseline.get("best_after")
        if not norm or not _finite(value):
            raise FeatureError("the baseline line has no code state or no finite value")
        self.inc, self.inc_raw = norm, raw
        self.evaluated, self.evaluated_raw = {norm}, ({raw} if raw else set())
        self.raw_complete = raw is not None
        self.base_value = self.best = float(value)
        self.steps_seen = 0
        self.keeps = self.last_keep = self.invalid = 0

    def observe(self, entry: dict) -> None:
        step, dec = entry.get("step"), entry.get("decision")
        if step != self.steps_seen + 1:
            raise FeatureError(f"ledger step {step} follows step {self.steps_seen} (steps must be contiguous)")
        self.steps_seen = step
        best = entry.get("best_after")
        if not _finite(best):
            raise FeatureError(f"ledger step {step} has no finite best_after")
        self.best = float(best)
        if dec in RAN:
            norm, raw = _states((entry.get("runs") or [{}])[-1])
            if not norm:
                raise FeatureError(f"ledger step {step} ran without a code state")
            self.evaluated.add(norm)
            if raw:
                self.evaluated_raw.add(raw)
            else:
                self.raw_complete = False
            if dec == "kept":
                self.keeps += 1
                self.last_keep = step
                self.inc, self.inc_raw = norm, raw
        if dec in INVALID:
            self.invalid += 1

    def features(self, side: dict, *, code: int, sign: float, sigma: float, budget_w: int, memory_on: float) -> dict:
        n = side["step"]
        if n != self.steps_seen + 1:
            raise FeatureError(f"features of step {n} asked after step {self.steps_seen}")
        nan = math.nan
        raw_ok = side["cand_raw"] is not None and self.inc_raw is not None
        vals = {f: nan for f in NUM_FEATURES_V3}
        vals.update({f: MISSING_CATEGORICAL for f in CAT_FEATURES_V3})
        vals.update({
            "node_code": code,
            "cfg_equals_incumbent": float(side["cand_raw"] == self.inc_raw) if raw_ok else nan,
            "active_equals_incumbent": float(side["cand"] == self.inc),
            "active_seen_before": float(side["cand"] in self.evaluated),
            "full_seen_before": (float(side["cand_raw"] in self.evaluated_raw)
                                 if side["cand_raw"] is not None and self.raw_complete else nan),
            "keeps_so_far": float(self.keeps), "trials_since_keep": float(n - self.last_keep),
            "recorded_gain_z": sign * (self.best - self.base_value) / sigma,
            "budget_frac_left": 1.0 - self.steps_seen / budget_w, "budget_index": float(n),
            "memory_on": memory_on, "invalid_so_far": float(self.invalid),
        })
        return {f: vals[f] for f in FEATURES_V3}


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def featurize_ledger(entries: list[dict], *, node: str, spec_suite: str, sign: float, sigma_node: float,
                     budget_w: int, w_semantics: str, memory_mode: str) -> tuple[dict, dict]:
    """Features of every step of one complete G.5 campaign ledger that has a candidate code state: ({step: features},
    info). ``sign`` is +1 for a maximised metric and -1 for a minimised one (as the table's Δ̂); ``sigma_node`` is the
    table's σ_node; ``budget_w`` the campaign's W under ``w_semantics`` ``manager_calls`` (G5-W A; B is not built in
    the engine either). ``info["raw_state_missing"]`` counts the featurised steps whose two raw-state fields are NaN
    because a record lacks raw code states."""
    code = check_node(node, spec_suite)
    if w_semantics != "manager_calls":
        raise FeatureError("budget_frac_left is defined for W counting manager calls (G5-W A) only")
    if isinstance(budget_w, bool) or not isinstance(budget_w, int) or budget_w < 1:
        raise FeatureError("W must be a positive integer")
    if sign not in (1.0, -1.0) or not _finite(sigma_node) or sigma_node <= 0:
        raise FeatureError("sign must be +1 or -1 and sigma_node positive")
    if not entries:
        raise FeatureError("an empty ledger")
    hist = _History(entries[0])
    memory_on = float(memory_mode != "none")
    out, missing = {}, 0
    for entry in entries[1:]:
        side = proposal_side(entry)
        if side is not None:
            if side["step"] != hist.steps_seen + 1:
                raise FeatureError(f"ledger step {side['step']} follows step {hist.steps_seen}")
            f = hist.features(side, code=code, sign=sign, sigma=float(sigma_node), budget_w=budget_w,
                              memory_on=memory_on)
            missing += any(math.isnan(f[k]) for k in RAW_STATE_FIELDS)
            out[side["step"]] = f
        hist.observe(entry)
    if hist.steps_seen > budget_w:
        raise FeatureError(f"the ledger has {hist.steps_seen} charged steps, more than W = {budget_w}")
    return out, {"raw_state_missing": missing}
