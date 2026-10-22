"""Per-proposal features from root ledgers (C3_DESIGN §3). ENGINEERING_ONLY; AI-assisted (Claude).

The ledger is replayed from the start configuration with the logged structured
edits, exactly as the worker applies them (same regexes as the harness
``LocalWorker._apply_edit``), so every proposal gets the file texts of its
candidate and of the incumbent it was compared against. These texts are what
``r1.c3.audit`` runs.

Leakage rules (C3_DESIGN §3, PLAN §7): the features of proposal n use only
trials < n and the proposal's own edit. Its own Delta_hat, decision, metric and
any audit value are outcomes, kept in a separate ``outcome`` dict. Nothing from
later trials, branches or siblings enters.

Rule-detectable proposals (T4 §1 as revised 19 Oct 2026; D25/D27), two kinds:
- **no-op** (``noop``; ``inert`` is kept as its alias): the candidate's
  active-key projection equals the incumbent's. Delta = 0 exactly and, on a
  bit-exact node, the logged Delta_hat is 0.
- **duplicate** (``duplicate``): the projection equals that of an earlier
  evaluated configuration other than the incumbent. Its result is already
  known from the ledger (``known_metric``); its increment is generally NOT 0.
  Running it again buys no information.
``rule_skip`` = no-op or duplicate. Both are detectable before execution.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from r1.diagnostics.di_test import configuration, scalar

# Dataset descriptors (task group of C3_DESIGN §3). Sources: node descriptions in
# the harness configs (tabular_mlp: make_classification 2,000 x 20, 8 % label
# noise; digits_mlp: sklearn digits 1,797 x 64, 10 classes) and OpenML metadata
# (breast-w id 15: 699 x 9, 34.5 % malignant; ionosphere id 59: 351 x 34, 35.9 % bad).
NODE_INFO = {
    "digits_mlp": {"rows": 1797, "features": 64, "classes": 10, "minority": 0.10, "metric": "val_score", "family": "mlp"},
    "tabular_mlp": {"rows": 2000, "features": 20, "classes": 2, "minority": 0.50, "metric": "val_score", "family": "mlp"},
    "openml_breast_w": {"rows": 699, "features": 9, "classes": 2, "minority": 0.345, "metric": "val_auc", "family": "openml"},
    "openml_ionosphere": {"rows": 351, "features": 34, "classes": 2, "minority": 0.359, "metric": "val_auc", "family": "openml"},
    # Added 22 Oct 2026 (D21 pool; PLAN §10 node pool). OpenML metadata: wdbc id 1510, 569 x 30 numeric,
    # 37.3 % malignant; credit-approval id 29, 690 x 15 (9 categorical), 44.5 % positive.
    "openml_wdbc": {"rows": 569, "features": 30, "classes": 2, "minority": 0.373, "metric": "val_auc", "family": "openml"},
    "openml_credit_approval": {"rows": 690, "features": 15, "classes": 2, "minority": 0.445, "metric": "val_auc", "family": "openml"},
    # Added 22 Oct 2026 (PLAN §10 "D21 pool (22 Oct)"; OpenML IDs checked on openml.org on 22 Oct).
    # Rows/features are the OpenML shapes listed for the pool extension; minority shares are the
    # published UCI class counts, taken from the agent's memory. NONE of these four rows has been
    # checked against the fetched data yet (no openml.org access here): r1/noise/check_caches.py prints
    # the actual shape and class counts once the caches exist, and these values must be corrected then.
    #   credit-g id 31: 1,000 x 20 (13 categorical), 300 bad / 700 good -> 0.300;
    #   sonar id 40: 208 x 60 numeric, 97 Rock / 111 Mine -> 0.466;
    #   blood-transfusion-service-center id 1464: 748 x 4 numeric, 178 donated / 570 -> 0.238;
    #   qsar-biodeg id 1494: 1,055 x 41 numeric, 356 RB / 699 NRB -> 0.337.
    "openml_credit_g": {"rows": 1000, "features": 20, "classes": 2, "minority": 0.300, "metric": "val_auc", "family": "openml"},
    "openml_sonar": {"rows": 208, "features": 60, "classes": 2, "minority": 0.466, "metric": "val_auc", "family": "openml"},
    "openml_blood_transfusion": {"rows": 748, "features": 4, "classes": 2, "minority": 0.238, "metric": "val_auc", "family": "openml"},
    "openml_qsar_biodeg": {"rows": 1055, "features": 41, "classes": 2, "minority": 0.337, "metric": "val_auc", "family": "openml"},
}
STRUCTURAL_KEYS = {"model_type", "scaler", "class_weight", "imputer"}
# D25 active keys for the OpenML template: harness configs/nodes/openml_*.yaml
# active_keys.by_model_type minus that node's active_keys.dataset_excluded
# (imputer for numeric-only datasets). Checked against the harness configs in
# r1/tests/test_c3_features.py.
OPENML_BY_MODEL_TYPE = {
    "logistic_regression": {"model_type", "C", "class_weight", "max_iter", "scaler", "imputer"},
    "random_forest": {"model_type", "n_estimators", "max_depth", "class_weight", "scaler", "imputer"},
    "gradient_boosting": {"model_type", "n_estimators", "max_depth", "learning_rate", "scaler", "imputer"},
}
OPENML_DATASET_EXCLUDED = {
    "openml_breast_w": {"imputer"}, "openml_ionosphere": {"imputer"}, "openml_wdbc": {"imputer"},
    "openml_credit_approval": set(),  # has categorical columns: imputer is active
    "openml_credit_g": set(),  # has categorical columns: imputer is active
    "openml_sonar": {"imputer"}, "openml_blood_transfusion": {"imputer"}, "openml_qsar_biodeg": {"imputer"},
}
# Numeric-dataset projection (kept for backward compatibility).
OPENML_ACTIVE = {m: keys - {"imputer"} for m, keys in OPENML_BY_MODEL_TYPE.items()}


def openml_active_keys(node: str, model_type: str) -> set:
    """D25 active keys of an OpenML node under ``model_type``; unknown nodes are an error, never a guess."""
    if node not in OPENML_DATASET_EXCLUDED:
        raise ValueError(f"no declared D25 active-key projection for {node}; add it to OPENML_DATASET_EXCLUDED")
    return OPENML_BY_MODEL_TYPE[model_type] - OPENML_DATASET_EXCLUDED[node]
CAT_FEATURES = ("node_code", "key_code", "model_type_code", "new_cat_code")
NUM_FEATURES = (
    "rows_log", "n_features", "n_classes", "minority",
    "old_num", "new_num", "log_ratio", "direction", "structural", "active_key",
    "cfg_equals_incumbent", "active_equals_incumbent", "active_seen_before", "full_seen_before",
    "key_edit_count", "last_key_delta_z", "last_key_kept", "keeps_so_far", "trials_since_keep",
    "recorded_gain_z", "budget_frac_left", "budget_index", "memory_on", "invalid_so_far",
    "same_edit_count", "reverse_of_last_key_edit",
)
FEATURES = CAT_FEATURES + NUM_FEATURES
# Stable categorical codes: the four original nodes keep the codes they had (sorted order on 19 Oct);
# nodes added later are appended, so existing tables and models keep their encoding.
NODE_CODES = {"digits_mlp": 0, "openml_breast_w": 1, "openml_ionosphere": 2, "tabular_mlp": 3,
              "openml_credit_approval": 4, "openml_wdbc": 5,
              # appended 22 Oct 2026 (D21 pool extension)
              "openml_credit_g": 6, "openml_sonar": 7, "openml_blood_transfusion": 8, "openml_qsar_biodeg": 9}
assert set(NODE_CODES) == set(NODE_INFO), "every node in NODE_INFO needs a stable code"
MODEL_CODES = {"mlp": 0, "logistic_regression": 1, "random_forest": 2, "gradient_boosting": 3}


def stable_code(text: str, mod: int = 997) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16) % mod


def files_hash(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:20]


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def normalise_files(files: dict[str, str]) -> dict[str, str]:
    # Historical start_files may serialise literal newline escapes (di_test.configuration).
    return {k: (v.replace("\\n", "\n") if "\n" not in v and "\\n" in v else v) for k, v in files.items()}


def _pattern(path: str, key: str) -> re.Pattern[str]:
    if path.endswith((".yaml", ".yml")):
        return re.compile(r"^(" + re.escape(key) + r"\s*:\s*)(.*?)(\s*)$", re.MULTILINE)
    return re.compile(r"^(" + re.escape(key) + r"\s*=\s*)(.+?)(\s*)$", re.MULTILINE)


def _loose(value: str) -> str:
    v = str(value).strip().strip("\"'")
    return "null" if v.lower() in {"none", "null", "~"} else v


def apply_edit(files: dict[str, str], edit: dict) -> dict[str, str]:
    """Apply one structured edit to file texts the way the harness worker does."""
    path, key = edit["path"], edit["symbol"]
    if path not in files:
        raise ValueError(f"edit path {path} not editable")
    pat = _pattern(path, key)
    m = pat.search(files[path])
    if m is None:
        raise ValueError(f"assignment for {key} not found")
    if _loose(m.group(2)) != _loose(edit["old"]):
        raise ValueError(f"stale edit: {key} is {m.group(2)!r}, edit expects {edit['old']!r}")
    out = dict(files)
    out[path] = pat.sub(lambda mm: mm.group(1) + str(edit["new"]) + mm.group(3), files[path])
    return out


def active_projection(config: dict, node: str) -> str:
    if NODE_INFO.get(node, {}).get("family") == "openml":
        keys = openml_active_keys(node, config["model_type"])
    else:
        keys = set(config)
    return json.dumps({k: config[k] for k in sorted(keys)}, sort_keys=True, default=str)


def parsed_metric(row: dict):
    metrics = row.get("parsed_metrics") or {}
    v = metrics.get("val_score", metrics.get("val_auc"))
    return v if v is not None and math.isfinite(v) else None


def _num(v):
    if isinstance(v, bool) or v is None:
        return math.nan
    if isinstance(v, (int, float)):
        return float(v)
    return math.nan


@dataclass
class Proposal:
    proposal_id: str
    instance: str
    instance_seed: int
    node: str
    source: str
    memory_mode: str
    budget_index: int
    features: dict
    outcome: dict
    candidate_files: dict = field(repr=False)
    incumbent_files: dict = field(repr=False)
    edit: dict = field(default_factory=dict)

    @property
    def candidate_hash(self):
        return files_hash(self.candidate_files)

    @property
    def incumbent_hash(self):
        return files_hash(self.incumbent_files)


class ReplayError(ValueError):
    pass


def replay_campaign(rows: list[dict], start_files: dict[str, str], node: str, instance: str,
                    source: str, memory_mode: str, runs_total: int, sigma_node: float,
                    check: bool = True) -> tuple[list[Proposal], dict]:
    """Replay one root ledger; return proposals (trial >= 2 with a parsed metric) and checks.

    Checks (bit-exact CPU nodes at fixed campaign seeds): a candidate whose
    active projection equals the incumbent's must log Delta_hat == 0, and a
    re-evaluated active projection must log the same metric as before.
    """
    info = NODE_INFO[node]
    files = normalise_files(start_files)
    cur_cfg = configuration(files)
    seen_metric: dict[str, float] = {}
    seen_full: set[str] = set()
    key_hist: dict[str, list[tuple[float, int]]] = {}
    edit_counts: dict[tuple, int] = {}
    last_edit_by_key: dict[str, tuple] = {}
    keeps, last_keep_idx, invalid = 0, 0, 0
    first_metric = None
    proposals: list[Proposal] = []
    checks = {"rows": len(rows), "proposals": 0, "zero_delta_violations": 0, "repeat_metric_violations": 0,
              "skipped_invalid": 0, "no_edit_rows": 0}
    seed = int(instance.rsplit("__s", 1)[1])
    for i, row in enumerate(rows):
        b = int(row["budget_index"])
        metric = parsed_metric(row)
        edit = ((row.get("extra") or {}).get("manager") or {}).get("structured_edit")
        if row["decision"] == "skipped" or metric is None:
            invalid += 1
            checks["skipped_invalid"] += 1
            continue
        if edit:
            try:
                cand_files = apply_edit(files, edit)
            except ValueError as exc:
                raise ReplayError(f"{instance} trial {b}: {exc}") from exc
        else:
            checks["no_edit_rows"] += 1
            cand_files = dict(files)
        cand_cfg = configuration(cand_files)
        inc_act, cand_act = active_projection(cur_cfg, node), active_projection(cand_cfg, node)
        cand_full = json.dumps(cand_cfg, sort_keys=True, default=str)
        key = edit["symbol"] if edit else "__none__"
        old_v, new_v = (cur_cfg.get(key), cand_cfg.get(key)) if edit else (None, None)
        o, n = _num(old_v), _num(new_v)
        log_ratio = math.log(n / o) if o > 0 and n > 0 else math.nan
        direction = (1.0 if n > o else -1.0 if n < o else 0.0) if not (math.isnan(o) or math.isnan(n)) else math.nan
        hist = key_hist.get(key, [])
        sig = (key, str(old_v), str(new_v))
        last = last_edit_by_key.get(key)
        model = cur_cfg.get("model_type", "mlp") if info["family"] == "openml" else "mlp"
        active_keys = openml_active_keys(node, cand_cfg["model_type"]) if info["family"] == "openml" else set(cand_cfg)
        delta_hat = row.get("delta_vs_best")
        if b >= 2 and row.get("current_best_before") is not None:
            feats = {
                "node_code": NODE_CODES[node], "key_code": stable_code(key),
                "model_type_code": MODEL_CODES.get(model, 9),
                "new_cat_code": stable_code(str(new_v)) if key in STRUCTURAL_KEYS else -1,
                "rows_log": math.log(info["rows"]), "n_features": info["features"],
                "n_classes": info["classes"], "minority": info["minority"],
                "old_num": o, "new_num": n, "log_ratio": log_ratio, "direction": direction,
                "structural": float(key in STRUCTURAL_KEYS), "active_key": float(key in active_keys),
                "cfg_equals_incumbent": float(cand_cfg == cur_cfg),
                "active_equals_incumbent": float(cand_act == inc_act),
                "active_seen_before": float(cand_act in seen_metric),
                "full_seen_before": float(cand_full in seen_full),
                "key_edit_count": float(len(hist)),
                "last_key_delta_z": hist[-1][0] / sigma_node if hist else math.nan,
                "last_key_kept": float(hist[-1][1]) if hist else math.nan,
                "keeps_so_far": float(keeps), "trials_since_keep": float(b - last_keep_idx),
                "recorded_gain_z": ((row["current_best_before"] - first_metric) / sigma_node
                                    if first_metric is not None else math.nan),
                "budget_frac_left": 1.0 - (b - 1) / runs_total, "budget_index": float(b),
                "memory_on": float(memory_mode != "none"), "invalid_so_far": float(invalid),
                "same_edit_count": float(edit_counts.get(sig, 0)),
                "reverse_of_last_key_edit": float(last is not None and last[1] == str(new_v) and last[2] == str(old_v)),
            }
            noop = bool(cand_act == inc_act)
            duplicate = bool(not noop and cand_act in seen_metric)
            inert_kind = "equals_incumbent" if noop else "duplicate" if duplicate else None
            # PLAN §10 (22 Oct): a no-op is an *inactive edit* (only keys inactive for the node's
            # model change) or an *incumbent repeat* (back to the incumbent's active configuration).
            noop_kind = None if not noop else (
                "inactive_edit" if edit and key not in active_keys and cand_cfg != cur_cfg else "incumbent_repeat")
            outcome = {"delta_hat": float(delta_hat), "decision": row["decision"], "metric": metric,
                       "inert": noop, "noop": noop, "duplicate": duplicate, "rule_skip": noop or duplicate,
                       "known_metric": seen_metric[cand_act] if duplicate else None,
                       "inert_kind": inert_kind, "noop_kind": noop_kind,
                       "current_best_before": row["current_best_before"]}
            if check:
                if cand_act == inc_act and delta_hat != 0:
                    checks["zero_delta_violations"] += 1
                if cand_act in seen_metric and seen_metric[cand_act] != metric:
                    checks["repeat_metric_violations"] += 1
            proposals.append(Proposal(
                proposal_id=f"{source}:{instance}:t{b:03d}", instance=instance, instance_seed=seed,
                node=node, source=source, memory_mode=memory_mode, budget_index=b,
                features=feats, outcome=outcome, candidate_files=cand_files, incumbent_files=dict(files),
                edit=dict(edit or {})))
        # ---- update history with this trial's outcome (only after features are frozen)
        if first_metric is None:
            first_metric = metric
        seen_metric.setdefault(cand_act, metric)
        seen_full.add(cand_full)
        if row.get("current_best_before") is not None:  # the incumbent has a recorded metric
            seen_metric.setdefault(inc_act, row["current_best_before"])
            seen_full.add(json.dumps(cur_cfg, sort_keys=True, default=str))
        kept = row["decision"] == "kept"
        if edit:
            key_hist.setdefault(key, []).append((float(delta_hat) if delta_hat is not None else math.nan, int(kept)))
            edit_counts[sig] = edit_counts.get(sig, 0) + 1
            last_edit_by_key[key] = sig
        if kept:
            keeps += 1
            last_keep_idx = b
            files, cur_cfg = cand_files, cand_cfg
    checks["proposals"] = len(proposals)
    return proposals, checks
