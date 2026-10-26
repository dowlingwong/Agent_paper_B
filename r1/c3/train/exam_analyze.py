"""P.3 exam analysis under the frozen selection rule (spec §5.7; rule file r1/c3/rules/p3_rule_v1.yaml).

ENGINEERING_ONLY; AI-assisted (Claude). Self-contained: RPS skill is computed
from the per-item RPS values in the input, not from ``losses``/``metrics``.

Input (JSON, schema ``trackp_exam_results/v1``)::

    {"schema": "trackp_exam_results/v1",
     "items": {item_id: instance_id, ...},            # exam-val items and their instance (bootstrap cluster)
     "base_rate_rps": {item_id: rps, ...},            # base-rate predictor (mean y_train of exam-train)
     "models": [{
        "model": "kev-0.8b", "family": "kev",          # family keys rule.architecture_classes
        "checkpoint": "base" | "instruct",
        "author_rung": null | "trainable", "author_row": null | "PLAN row id",   # pending-author families only
        "e0": {"protocol": "trackp_e0/v1", "width_slope": float, "mean_slope": float} | null,  # null: floor
        "e2": {"val_rps_skill": float} | null,
        "e3": {"rps": {seed: {item_id: rps}}, "width_ratio": float},
        "e4": {"oom": bool, "reload_deterministic": bool, "cost_s": float} | null,
        "e6": {"A1": bool | null, ..., "A5": bool | null} | null,
        "e7": {"softmax_12": skill, "cumulative_11": skill} | null}, ...]}

Rule v1 holds the E0 thresholds of protocol v1 (width slope vs s >= 0.7, mean slope >= 0.8), withdrawn on 26 Oct
(R1-E0-PROTOCOL): ``analyze`` refuses any E0 record that does not declare ``"protocol": "trackp_e0/v1"``. P.3b on
E0 v2 results needs a rule v2 with the author's v2 thresholds (and StartLux no longer pending,
R1-STARTLUX-TRAINABLE), frozen with its sha256 before any P.3b data.

Output: ranking (E3 skill), discards with reasons, tied set and its order, finalists, control size, head forms,
floor verdict (``stop_escalate``), packing flags, the rule's sha256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

RULE_PATH = Path(__file__).resolve().parents[1] / "rules" / "p3_rule_v1.yaml"
SCHEMA = "trackp_exam_results/v1"
OUTPUT_SCHEMA = "trackp_exam_selection/v1"


class RuleHashError(RuntimeError):
    pass


class RuleSuperseded(RuntimeError):
    """The input's E0 protocol is not the one the rule's thresholds were written for."""


def load_rule(path: Path | str = RULE_PATH) -> tuple[dict, str]:
    """The rule and its sha256; refuses content that differs from the committed ``.sha256``."""
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = Path(str(path) + ".sha256").read_text().split()[0]
    if digest != expected:
        raise RuleHashError(f"{path.name}: sha256 {digest} != committed {expected}")
    return yaml.safe_load(raw), digest


class _Exam:
    def __init__(self, data: dict):
        if data.get("schema") != SCHEMA:
            raise ValueError(f"expected schema {SCHEMA}, got {data.get('schema')!r}")
        self.items = sorted(data["items"])
        inst = [data["items"][i] for i in self.items]
        self.instances = sorted(set(inst))
        idx = {s: k for k, s in enumerate(self.instances)}
        self.item_inst = np.array([idx[s] for s in inst])
        self.base = self._vec(data["base_rate_rps"])

    def _vec(self, d: dict) -> np.ndarray:
        missing = [i for i in self.items if i not in d]
        if missing:
            raise ValueError(f"missing RPS for {len(missing)} items, e.g. {missing[0]}")
        return np.array([float(d[i]) for i in self.items])

    def seeds(self, model: dict) -> np.ndarray:
        """[n_seeds, n_items] per-item RPS of a model's E3 seeds."""
        return np.stack([self._vec(v) for _, v in sorted(model["e3"]["rps"].items())])

    def skill(self, rps: np.ndarray, w: np.ndarray | None = None) -> float:
        """E3 skill: mean over seeds of 1 - mean_w(RPS) / mean_w(RPS_base); w = bootstrap item weights."""
        w = np.ones(len(self.items)) if w is None else w
        return float(np.mean(1.0 - (rps @ w) / (self.base @ w)))

    def boot_weights(self, rule: dict) -> np.ndarray:
        """[B, n_items] item multiplicities from resampling instances with replacement."""
        b = rule["bootstrap"]
        rng = np.random.default_rng(b["seed"])
        n = len(self.instances)
        draws = rng.integers(0, n, size=(b["resamples"], n))
        counts = np.stack([np.bincount(d, minlength=n) for d in draws])
        return counts[:, self.item_inst].astype(float)

    def diff_interval(self, rps_a, rps_b, W, alpha) -> tuple[float, float, float]:
        """skill(a) - skill(b): point value and percentile interval over the bootstrap weights W."""
        def sk(r):
            return np.mean(1.0 - (r @ W.T) / (self.base @ W.T)[None, :], axis=0)
        d = sk(rps_a) - sk(rps_b)
        lo, hi = np.quantile(d, [alpha / 2, 1 - alpha / 2])
        return self.skill(rps_a) - self.skill(rps_b), float(lo), float(hi)


def _class(rule, m):
    fam = m["family"]
    if fam not in rule["architecture_classes"]:
        raise ValueError(f"{m['model']}: unknown family {fam!r}")
    return rule["architecture_classes"][fam]


def _step1(rule, m) -> list[str]:
    """Disqualification reasons (spec §5.7.1): E0 failure, E4 hard limits."""
    reasons = []
    e0 = m.get("e0")
    if e0 is None:
        reasons.append("e0_missing")
    else:
        if not e0["width_slope"] >= rule["e0_pass"]["width_slope_min"]:
            reasons.append("e0_width_slope")
        if not e0["mean_slope"] >= rule["e0_pass"]["mean_slope_min"]:
            reasons.append("e0_mean_slope")
    e4 = m.get("e4")
    if e4 is None:
        reasons.append("e4_missing")
    else:
        if e4["oom"] and "oom" in rule["e4_hard_limits"]["disqualify_on"]:
            reasons.append("e4_oom")
        if not e4["reload_deterministic"] and "reload_nondeterministic" in rule["e4_hard_limits"]["disqualify_on"]:
            reasons.append("e4_reload_nondeterministic")
    return reasons


def _order_key(m):
    """Tie-break order within the tied set (rule.tie_breaks)."""
    e2 = (m.get("e2") or {}).get("val_rps_skill")
    return (-(e2 if e2 is not None else -np.inf),
            abs(m["e3"]["width_ratio"] - 1.0),
            0 if m.get("checkpoint") == "base" else 1,
            (m.get("e4") or {}).get("cost_s", np.inf))


def _head_form(rule, m):
    e7 = m.get("e7")
    if not e7:
        return None
    a, b = rule["e7"]["forms"]
    return a if e7[a] > e7[b] else b if e7[b] > e7[a] else rule["e7"]["default"]


def analyze(data: dict, rule_path: Path | str = RULE_PATH) -> dict:
    rule, digest = load_rule(rule_path)
    ex = _Exam(data)
    models = data["models"]
    names = [m["model"] for m in models]
    if len(set(names)) != len(names):
        raise ValueError("duplicate model names")
    want = rule.get("e0_protocol", "trackp_e0/v1")
    stale = [m["model"] for m in models if m.get("e0") is not None and m["e0"].get("protocol") != want]
    if stale:
        raise RuleSuperseded(f"{rule['version']} has E0 thresholds for {want}; E0 records of {stale} do not declare "
                             f"it. E0 v2 needs a rule v2 with the author's thresholds (R1-E0-PROTOCOL)")
    roles = rule["roles"]
    W = ex.boot_weights(rule)
    alpha = rule["bootstrap"]["alpha"]
    rps = {m["model"]: ex.seeds(m) for m in models}
    skill = {m["model"]: ex.skill(rps[m["model"]]) for m in models}

    records, discarded, candidates, controls, floors = {}, {}, [], [], []
    for m in models:
        name, fam = m["model"], m["family"]
        cls = _class(rule, m)
        e6 = m.get("e6") or {}
        e6_failed = sorted(p for p in rule["e6"]["probes"] if e6.get(p) is False)
        rec = {"family": fam, "class": cls, "e3_skill": skill[name], "e6_failed": e6_failed,
               "packing_disabled": any(p in e6_failed for p in rule["e6"]["disable_packing_on"])}
        records[name] = rec
        if fam in roles["floor_families"]:
            floors.append(m)
            continue
        reasons = _step1(rule, m)
        rec["step1_failures"] = reasons
        if fam in roles["control_families"]:
            controls.append(m)  # always carried; failures recorded
            continue
        if fam in rule["pending_author_families"] and not (m.get("author_rung") == "trainable" and m.get("author_row")):
            reasons = reasons + ["pending_author"]
        if reasons:
            discarded[name] = reasons
        else:
            candidates.append(m)

    ranking = sorted(candidates, key=lambda m: -skill[m["model"]])
    out = {"schema": OUTPUT_SCHEMA, "rule_version": rule["version"], "rule_sha256": digest,
           "n_items": len(ex.items), "n_instances": len(ex.instances), "records": records,
           "discarded": discarded, "ranking": [m["model"] for m in ranking]}

    tied, comparisons = [], {}
    if ranking:
        top = ranking[0]
        for m in ranking:
            if m is top:
                tied.append(m)
                continue
            d, lo, hi = ex.diff_interval(rps[top["model"]], rps[m["model"]], W, alpha)
            comparisons[m["model"]] = {"diff_vs_top": d, "lo": lo, "hi": hi, "tied": bool(lo <= 0 <= hi)}
            if lo <= 0 <= hi:
                tied.append(m)
    tied_order = sorted(tied, key=_order_key)
    finalists = []
    if tied_order:
        finalists.append(tied_order[0])
        for m in tied_order[1:]:
            if len(finalists) >= rule["finalists"]["max"]:
                break
            if not rule["finalists"]["second_requires_different_class"] or _class(rule, m) != _class(rule, finalists[0]):
                finalists.append(m)
                break
    control = max(controls, key=lambda m: skill[m["model"]]) if controls else None
    out.update({"top": ranking[0]["model"] if ranking else None, "comparisons_vs_top": comparisons,
                "tied_set": [m["model"] for m in tied_order], "finalists": [m["model"] for m in finalists],
                "control": control["model"] if control else None,
                "head_forms": {m["model"]: _head_form(rule, m) for m in finalists}})

    # Step 7: does any LLM (step-1 candidates and the control) beat the best floor significantly?
    floor_check = {"floor": None, "llm_vs_floor": {}, "stop_escalate": True}
    if floors:
        best_floor = max(floors, key=lambda m: skill[m["model"]])
        floor_check["floor"] = best_floor["model"]
        for m in candidates + controls:
            d, lo, hi = ex.diff_interval(rps[m["model"]], rps[best_floor["model"]], W, alpha)
            floor_check["llm_vs_floor"][m["model"]] = {"diff": d, "lo": lo, "hi": hi, "significant": bool(lo > 0)}
        floor_check["stop_escalate"] = not any(v["significant"] for v in floor_check["llm_vs_floor"].values())
    else:
        floor_check["reason"] = "no floor result"
    out["floor_check"] = floor_check
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("results", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--rule", type=Path, default=RULE_PATH)
    a = ap.parse_args(argv)
    res = analyze(json.loads(a.results.read_text()), a.rule)
    text = json.dumps(res, indent=2, sort_keys=True)
    if a.out:
        a.out.write_text(text + "\n")
    else:
        print(text)
    return 2 if res["floor_check"]["stop_escalate"] else 0


if __name__ == "__main__":
    sys.exit(main())
