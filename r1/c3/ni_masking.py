"""Results-masking test for the no-information condition (docs/r1/proposals/T4_PROP10_REVISION_20261028.md §3, §6).

ENGINEERING_ONLY; AI-assisted (Claude). Revised 28 Oct 2026 after the independent review
(`docs/r1/reviews/MAC_LOCAL_DELIVERABLES_REVIEW_20261028.md`, findings N1–N9, and its re-review R-N1–R-N3).

Question. Under (NF) and (NI), the Bayes per-proposal forecast given the *whole*
proposal history x_{1:n} gains nothing from executed results (T4 revision,
Proposition 10(a′).1). This script asks a weaker, operational question: do the
features derived from revealed results improve a forecaster beyond what the
remaining features carry?

Procedure. Two copies of the A3 arm (LightGBM on the C3 features, ``r1.c3.arms``)
are cross-fitted on the same folds:
- ``full``: all C3 features;
- ``masked``: the same features minus ``DIRECT_OUTCOME_FEATURES``.

On held-out audited non-inert proposals, the script compares two quantities, with
a cluster bootstrap over campaign seeds (field ``instance``):
- the RPS, as masked − full, scored against the **evaluation-half** soft label
  (audit seeds 7006–7010, ``soft_eval``) and never against the training label;
- the decision utility per 20 logged proposals at the primary run price, as
  full − masked, using ``r1.c3.offline_eval`` rules and the evaluation-half
  ``delta_true``.

Three fold schemes are run:
- ``instance``: campaign seeds, the primary scheme;
- ``pair_grouped``: campaigns that share any (node, candidate hash, incumbent hash)
  pair are kept in one fold, as a robustness check against recurring pairs. Its
  output carries ``fold_diagnostics``; when every node falls in a single fold, the
  block is ``degenerate`` (it is then a transfer test, not a leakage check);
- ``lono``: leave one node out, for transfer.

Reading (finding N1).
- An RPS interval (masked − full) above zero means that past results improve
  this forecaster beyond the retained features
  (``results_add_predictive_value``). That is evidence against the conjunction
  (NF) ∧ (NI) *only to the extent that the retained features summarise x_{1:n}*.
- An interval containing zero does not establish (NI).
- The direction of the bias is undetermined:
  - the retained features below still depend on results, which pulls the
    difference toward zero;
  - the retained features summarise the proposal history only partially, which
    can produce positives even when (NI) holds;
  - a positive can also come from increments that depend on the incumbent
    (failure of (NF-b)).
- The primary reading is the pooled ``instance`` block; per-node intervals are
  descriptive (no multiplicity control).

Width of the soft label (finding N7). The primary width is the one used by the A3
arm in the gate run (``se_audit`` at cefa389, ``offline_eval.assemble``);
``pooled_node`` (R1-SOFT-SIGMA) is a sensitivity.

Nothing here is evidence until it runs on the frozen B.2 table under the plan.
"""
from __future__ import annotations

import argparse
import functools
import json
from pathlib import Path

import numpy as np

from r1.c3 import offline_eval as OE
from r1.c3.arms import LGBMPrior, is_duplicate, is_noop, rule_skip
from r1.c3.audit import split_audit
from r1.c3.features import FEATURES
from r1.c3.labels import N_BINS, soft_label
from r1.c3.train.metrics import rps

# Features computed directly from revealed results or from decisions on them (masked).
DIRECT_OUTCOME_FEATURES = (
    "last_key_delta_z",   # standardised result of the last edit of the same key
    "last_key_kept",      # keep decision on that edit
    "keeps_so_far",       # number of keeps
    "trials_since_keep",  # depends on keeps
    "recorded_gain_z",    # recorded incumbent gain (a function of kept results)
    "invalid_so_far",     # invalid runs observed so far
)
# Retained features that still depend on results (finding N3); written to every output.
RETAINED_INCUMBENT_DEPENDENT = (  # through the incumbent, which depends on keeps
    "old_num", "log_ratio", "direction", "model_type_code", "active_key", "cfg_equals_incumbent",
    "active_equals_incumbent", "active_seen_before", "full_seen_before", "same_edit_count",
    "reverse_of_last_key_edit",
)
RETAINED_VALIDITY_DEPENDENT = (  # counted over valid trials only (features.observe returns early on invalid rows)
    "key_edit_count", "same_edit_count", "reverse_of_last_key_edit", "active_seen_before", "full_seen_before",
)
for _group in (DIRECT_OUTCOME_FEATURES, RETAINED_INCUMBENT_DEPENDENT, RETAINED_VALIDITY_DEPENDENT):
    assert set(_group) <= set(FEATURES), "feature lists must name existing C3 features"
assert not set(DIRECT_OUTCOME_FEATURES) & set(RETAINED_INCUMBENT_DEPENDENT + RETAINED_VALIDITY_DEPENDENT)

ARMS = {"full": LGBMPrior, "masked": functools.partial(LGBMPrior, drop=DIRECT_OUTCOME_FEATURES)}
MODES = ("instance", "pair_grouped", "lono")
PRIMARY_SIGMA_MODE = "se_audit"


# ----------------------------------------------------------------------------- labels

def load_audits(table_dir: Path, audits_path: Path | None = None) -> dict:
    """Audit rows by proposal id (same file as ``offline_eval.assemble``)."""
    path = Path(audits_path) if audits_path else Path(table_dir) / "audits.jsonl"
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            a = json.loads(line)
            out[a["proposal_id"]] = a
    return out


def with_eval_soft(rows: list[dict], audits: dict, sigma_mode: str = PRIMARY_SIGMA_MODE) -> list[dict]:
    """Copy of ``rows`` with ``soft_eval``: the soft label of the evaluation half of the audit seeds (finding N2).

    Only audited non-inert, non-duplicate rows get one; the width rule is ``sigma_mode``, as for the training label.
    """
    out = []
    for r in rows:
        r = dict(r)
        a = audits.get(r["proposal_id"])
        if a is not None and not is_noop(r) and not is_duplicate(r) and a.get("delta_audit") is not None:
            ev = split_audit(a)[1]
            if ev["delta_audit"] is not None:
                if sigma_mode == "se_audit":
                    r["soft_eval"] = soft_label(ev["delta_audit"], ev["se"], r["sigma_node"], sigma_mode="se_audit")
                else:
                    r["soft_eval"] = soft_label(ev["delta_audit"], None, r["sigma_node"], sigma_mode=sigma_mode,
                                                k_label=ev["k"])
        out.append(r)
    return out


# ----------------------------------------------------------------------------- folds

def pair_grouped_folds(rows: list[dict], k: int = 3) -> np.ndarray:
    """Fold id per row such that campaigns sharing any (node, candidate hash, incumbent hash) share a fold.

    Campaigns (field ``instance``) are linked when they contain the same pair; connected components are assigned
    to folds greedily by size (largest first, to the currently smallest fold), so the folds stay balanced.
    """
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first_owner = {}
    for r in rows:
        inst = r["instance"]
        find(inst)
        key = (r["node"], r.get("candidate_hash"), r.get("incumbent_hash"))
        if key[1] is None or key[2] is None:
            continue
        if key in first_owner:
            parent[find(inst)] = find(first_owner[key])
        else:
            first_owner[key] = inst
    comp_rows = {}
    for i, r in enumerate(rows):
        comp_rows.setdefault(find(r["instance"]), []).append(i)
    sizes = [0] * k
    fid = np.zeros(len(rows), int)
    for comp in sorted(comp_rows, key=lambda c: (-len(comp_rows[c]), str(c))):
        f = int(np.argmin(sizes))
        fid[comp_rows[comp]] = f
        sizes[f] += len(comp_rows[comp])
    return fid


def fold_diagnostics(rows: list[dict], fid) -> dict:
    """How the folds split the campaigns: component structure for ``pair_grouped`` (re-review R-N1).

    Every campaign of a node starts from the same configuration, so early (candidate, incumbent) pairs can link all
    of a node's campaigns into one component. The fold scheme then holds out whole nodes, which is a transfer test,
    not a leakage check; such a block is labelled ``degenerate``.
    """
    fid = np.asarray(fid)
    nodes = np.array([r["node"] for r in rows])
    inst = np.array([r["instance"] for r in rows])
    folds_per_node = {n: sorted({int(f) for f in fid[nodes == n]}) for n in sorted(set(nodes.tolist()))}
    camp_fold = {}
    for i, f in zip(inst, fid):
        camp_fold[i] = int(f)
    sizes = np.bincount(fid.astype(int)) if fid.size else np.array([0])
    whole_node = all(len(v) == 1 for v in folds_per_node.values())
    return {"n_folds": int(len(set(fid.tolist()))), "fold_row_counts": sizes.tolist(),
            "largest_fold_share": float(sizes.max() / max(sizes.sum(), 1)),
            "n_campaigns": len(camp_fold), "folds_per_node": folds_per_node,
            "n_nodes_single_fold": int(sum(len(v) == 1 for v in folds_per_node.values())),
            "degenerate": bool(whole_node)}


def _groups(rows, mode: str, k: int) -> np.ndarray:
    if mode == "instance":
        return OE.folds_by_instance(rows, k)
    if mode == "pair_grouped":
        return pair_grouped_folds(rows, k)
    if mode == "lono":
        return np.array([r["node"] for r in rows])
    raise ValueError(f"mode must be one of {MODES}")


def crossfit(rows, groups, arms=ARMS) -> dict:
    """Held-out bin distributions per arm for the given fold ids (same folds for every arm)."""
    preds = {a: np.zeros((len(rows), N_BINS)) for a in arms}
    for gval in sorted(set(groups.tolist()), key=str):
        te = np.where(groups == gval)[0]
        tr = np.where(groups != gval)[0]
        train, test = [rows[i] for i in tr], [rows[i] for i in te]
        for a, cls in arms.items():
            preds[a][te] = cls().fit(train).predict(test)
    return preds


# ----------------------------------------------------------------------------- test

def _eval_mask(rows) -> np.ndarray:
    """Audited non-inert proposals with an evaluation-half label and positive evaluation weight."""
    return np.array([(r.get("soft_eval") is not None) and (r.get("eval_weight", 0.0) > 0) and not rule_skip(r)
                     for r in rows], bool)


def _ci(draws) -> list[float]:
    d = np.asarray(draws, float)
    d = d[np.isfinite(d)]
    return [float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))] if d.size else [float("nan")] * 2


def _summary(diff, w, clusters, sel, n_boot, seed) -> dict:
    diff, w, clusters = np.asarray(diff, float)[sel], np.asarray(w, float)[sel], np.asarray(clusters)[sel]
    out = {"n": int(sel.sum()), "n_instances": len(set(clusters.tolist()))}
    if w.sum() <= 0:
        return {**out, "mean": float("nan"), "ci95": [float("nan")] * 2}
    draws = OE.cluster_boot(diff, w, clusters.tolist(), n=n_boot, seed=seed)
    return {**out, "mean": float(np.average(diff, weights=w)), "ci95": _ci(draws)}


def run_test(rows, mode: str = "instance", k: int = 3, g_units: float = OE.G_PRIMARY,
             n_boot: int = OE.BOOT, seed: int = OE.SEED, score_against: str = "eval") -> dict:
    """Cross-fit ``full`` and ``masked`` A3 on the same folds and compare them on held-out rows.

    ``score_against="eval"`` (the only valid setting for a report) scores the RPS against ``soft_eval``;
    ``"label"`` scores against the training label and exists only so that the tests can show the label-noise
    artefact of finding N2.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if score_against not in ("eval", "label"):
        raise ValueError("score_against must be 'eval' or 'label'")
    ev = _eval_mask(rows)
    if not ev.any():
        raise ValueError("no row has an evaluation-half soft label (soft_eval); build it with with_eval_soft")
    groups_arr = _groups(rows, mode, k)
    preds = crossfit(rows, groups_arr)
    nodes = np.array([r["node"] for r in rows])
    inst = np.array([r["instance"] for r in rows])
    w = np.array([r.get("eval_weight", 0.0) for r in rows], float)
    key = "soft_eval" if score_against == "eval" else "soft"
    target = np.array([r[key] if r.get(key) is not None else np.full(N_BINS, 1.0 / N_BINS) for r in rows])

    r_full, r_mask = rps(preds["full"], target), rps(preds["masked"], target)
    util = {}
    for a, P in preds.items():
        ex, kp, (_, _, _, _, g) = OE.decisions(P, rows, g_units, rule_layer=True)
        util[a] = OE.rewards(rows, ex, kp, g) * OE.CAMPAIGN_RUNS
    has_w = w > 0

    out = {"mode": mode, "k": k if mode != "lono" else None, "g_sigma_units": g_units, "scored_against": key,
           "direct_outcome_features": list(DIRECT_OUTCOME_FEATURES),
           "retained_result_dependent": {"incumbent": list(RETAINED_INCUMBENT_DEPENDENT),
                                         "validity": list(RETAINED_VALIDITY_DEPENDENT)},
           "n_rows": len(rows), "n_eval": int(ev.sum()),
           "primary_reading": "pooled block of the instance mode; per-node blocks are descriptive",
           "pooled": {}, "nodes": {}}
    if mode == "pair_grouped":
        out["fold_diagnostics"] = fold_diagnostics(rows, groups_arr)
    groups = [("pooled", np.ones(len(rows), bool))] + [(n, nodes == n) for n in sorted(set(nodes.tolist()))]
    for name, in_group in groups:
        ev_s, w_s = ev & in_group, has_w & in_group
        wsum = w[ev_s].sum()
        block = {
            "rps_full": float(np.average(r_full[ev_s], weights=w[ev_s])) if wsum > 0 else float("nan"),
            "rps_masked": float(np.average(r_mask[ev_s], weights=w[ev_s])) if wsum > 0 else float("nan"),
            "rps_masked_minus_full": _summary(r_mask - r_full, w, inst, ev_s, n_boot, seed),
            "utility_per20_full_minus_masked": _summary(util["full"] - util["masked"], w, inst, w_s, n_boot, seed),
        }
        lo = block["rps_masked_minus_full"]["ci95"][0]
        block["results_add_predictive_value"] = bool(np.isfinite(lo) and lo > 0)
        if name == "pooled":
            out["pooled"] = block
        else:
            out["nodes"][name] = block
    return out


READING = ("An RPS interval (masked − full, scored on the evaluation-half label) above zero means that past results "
           "improve this forecaster beyond the retained features. It is evidence against the conjunction (NF) ∧ (NI) "
           "only to the extent that the retained features summarise the whole proposal history x_{1:n}. An interval containing "
           "zero does not establish (NI). The direction of the bias is undetermined: retained features still depend "
           "on results (toward zero), the history summary is incomplete (toward false positives), and increments "
           "that depend on the incumbent also give positives. Primary reading: the pooled instance-mode block; "
           "per-node blocks are descriptive.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--audits", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--sigma-mode", default=PRIMARY_SIGMA_MODE, choices=("se_audit", "pooled_node"),
                    help="soft-label width; primary = the gate's A3 width (se_audit); pooled_node is a sensitivity")
    ap.add_argument("--label", default="ENGINEERING_ONLY",
                    help="evidence label; anything but ENGINEERING_ONLY needs the plan's authorization")
    args = ap.parse_args(argv)
    table = Path(args.table)
    noise = OE.table_noise(table)  # verifies a pinned noise source exactly as offline_eval.main does (finding N6)
    audits_path = Path(args.audits) if args.audits else None
    rows = OE.assemble(table, audits_path, True, sigma_mode=args.sigma_mode)
    rows = with_eval_soft(rows, load_audits(table, audits_path), args.sigma_mode)
    result = {"label": args.label, "ai_assisted": "AI-assisted (Claude)",
              "test": "results-masking test for (NI) (T4_PROP10_REVISION_20261028 §3, §6)",
              "reading": READING, "sigma_mode": args.sigma_mode,
              "sigma_mode_role": "primary" if args.sigma_mode == PRIMARY_SIGMA_MODE else "sensitivity",
              **({"noise_source": json.loads((table / "build.json").read_text())["noise_source"]}
                 if noise is not None else {}),
              **{m: run_test(rows, m, args.folds) for m in MODES}}
    out = Path(args.out) if args.out else table / "ni_masking.json"
    out.write_text(json.dumps(result, indent=1))
    print(json.dumps({m: {"pooled_rps_masked_minus_full": result[m]["pooled"]["rps_masked_minus_full"],
                          "results_add_predictive_value": result[m]["pooled"]["results_add_predictive_value"]}
                      for m in MODES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
