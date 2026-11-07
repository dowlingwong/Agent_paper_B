"""Offline one-step evaluation of the C3 arms and the C3 gate (C3_DESIGN §6). ENGINEERING_ONLY; AI-assisted (Claude).

Realised one-step value of an arm on a held-out proposal (C3_DESIGN §6):
  r = Delta_true * keep - g * execute,
with Delta_true = Delta_audit for audited proposals and 0 for no-ops (T4 §1,
revised 19 Oct 2026). Duplicates of an earlier evaluated configuration are not
zero-increment: arms with the rule layer (A2+) skip them (reward 0); A1/A0 may
execute them, and if such a duplicate is kept its Delta_true is its audit value
when audited, otherwise the logged Delta_hat as a proxy (counted and reported).
Duplicates carry no training label. Decisions from ``rules`` with the arm's (pi, mu, tau), the edit's
comparison noise sigma_cmp, and the *logged* campaign Delta_hat (independent of
the audit seeds).

Run price g (PLAN §10, "g (22 Oct)", option A): g is declared in units of the
node's sigma_node. The primary value is ``G_PRIMARY`` = 0.1 sigma_node; the
declared sensitivity values are ``G_SENSITIVITY`` = (0.05, 0.2) sigma_node. The
default evaluation computes exactly these three values. The superseded
per-node C3 gate is unavailable; ``gate_verdict`` reports no pass/fail until
the independently reviewed D8 aggregate gate is implemented. Sensitivity
values have no verdict. g = 0 appears only inside
the theory checks (T4 Proposition 7 threshold gain), labelled as such; it is
never a gate quantity. g is not tuned on any data.

Run accounting in the 20-run scaling (PLAN §10, 22 Oct, option A):
- primary (``skip_credited_at_g``): a skipped proposal scores r = 0, i.e. the
  skip is credited at the price g of the run it saves; freed runs are NOT
  re-spent. The per-campaign value is 20 x the weighted mean r per logged
  proposal (one logged proposal = one run in a W = 20 root campaign). This is a
  stated convention, consistent with g being declared as the value of one run,
  not a derived opportunity cost.
- sensitivity (``freed_run_call_cap``): freed runs are re-spent on further
  proposals that are exchangeable with the arm's own held-out proposals in the
  node, under a cap of c x W LLM proposals per campaign. With mean realised
  reward per executed proposal m and execution rate e, the campaign executes
  min(W, e c W) proposals and its value is m x min(W, e c W). c = 1 reproduces
  the primary accounting exactly (W x mean reward per logged proposal); the
  reported sensitivities are c = 2 (the realistic one) and c = inf (no call cap,
  value W x m; an optimistic upper bound that scales with 1/e and amplifies the
  arm with the lower execution rate). The divergence of the history after a
  skip is ignored. Deviation from the PLAN wording ("give each freed run to the
  next logged proposal of the same campaign"): the root ledgers hold exactly
  one proposal per run (W rows, budget index = cumulative budget consumed), so
  no logged proposal exists beyond the end of a campaign to receive a freed
  run; a literal replay cannot spend them. See ``RUN_ACCOUNTING``.

Population: (source, node) strata that have audited proposals. No-ops and
duplicates enter with evaluation weight 1. Randomly audited non-inert proposals carry weight
N_noninert / N_audited of their stratum (inverse sampling probability), so means
estimate the stratum's full proposal population. Proposals audited only because
they were DI-changed candidates (selected, not random) get weight 0 in
evaluation but are used for training.

Splits: ``instance`` = K-fold cross-fitting by instance seed (all nodes
trained together; every instance is held out once); ``lono`` = leave one node
out (reported, no gate verdict).

C3 gate: PLAN §10 R1-BX-D8 supersedes the older per-node D18 criterion.
The new aggregate criterion is not implemented here; this module must not
publish the old criterion as a current B.7 verdict.

Usage:
  python -m r1.c3.offline_eval --table DIR [--audits DIR/audits.jsonl] --out DIR/offline_eval.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from r1.c3 import rules
from r1.c3.audit import split_audit
from r1.c3.arms import ConstantPrior, LGBMPrior, RulesPrior, is_duplicate, is_noop, prior_moments, rule_skip
from r1.c3.dataset import load_table, noise_table
from r1.c3.labels import N_BINS, log_score, prob_positive, soft_label, soft_label_version

G_PRIMARY = 0.1  # run price g in units of sigma_node (PLAN §10, "g (22 Oct)"): the gate value
G_SENSITIVITY = (0.05, 0.2)  # declared sensitivity values; reported, never a verdict
G_EVAL = (G_PRIMARY, *G_SENSITIVITY)  # the default evaluation computes exactly these
G_THEORY = 0.0  # used only by the T4 Proposition 7 threshold-gain theory check
GATE_MIN_NODES = 2
CAMPAIGN_RUNS = 20
CALL_CAPS = (2.0, float("inf"))  # freed-run sensitivity: LLM-proposal cap per campaign in units of W (c = 1 is the primary)
RUN_ACCOUNTING = {
    "primary": {
        "name": "skip_credited_at_g",
        "rule": "r = Delta_true * keep - g * execute per logged proposal; a skip scores 0, i.e. it is credited "
                "at the price g of the run it saves; freed runs are not re-spent; per-campaign value = 20 x "
                "weighted mean r per logged proposal (one logged proposal = one run in a W = 20 root campaign).",
        "basis": "PLAN §10 'Run accounting in the 20-run scaling (22 Oct)', option A: a stated convention, "
                 "consistent with g declared as the value of one run, not a derived opportunity cost.",
    },
    "sensitivity": {
        "name": "freed_run_call_cap",
        "rule": "freed runs are re-spent on further proposals exchangeable with the arm's held-out proposals in "
                "the node, under a cap of c x W proposals per campaign: value = m x min(W, e c W), with m the "
                "weighted mean reward per executed proposal and e the execution rate. c = 1 equals the primary; "
                "reported: c = 2 (realistic) and c = inf (no cap, W x m; optimistic upper bound, scales with 1/e).",
        "call_caps_reported": ["2", "inf"],
        "assumptions": "further proposals are exchangeable with the arm's proposals in the node; history "
                       "divergence after a skip is ignored.",
        "deviation_from_plan_wording": "PLAN gives each freed run to the next logged proposal of the same "
                                       "campaign. Root ledgers hold exactly one proposal per run (W rows; budget "
                                       "index = cumulative budget consumed), so no logged proposal exists beyond "
                                       "the end of a campaign to receive a freed run; this is the closest replay "
                                       "the logs support.",
    },
}
BOOT = 2000
SEED = 20261019


def _verify_evidence_inputs(table_dir: Path, audits_path: Path, metadata: dict) -> None:
    """Bind evidence evaluation to the independently completed audit and author decision."""
    from r1.c3.audit import verify_evidence_completion
    from r1.harness import REPO

    classification = metadata.get("classification") or {}
    sweep_index = metadata.get("sweep_index") or {}
    if not classification.get("path") or not sweep_index.get("path"):
        raise ValueError("EVIDENCE requires classification and index provenance")
    verify_evidence_completion(Path(table_dir), Path(audits_path), REPO,
                               Path(sweep_index["path"]), Path(classification["path"]))


def assemble(table_dir: Path, audits_path: Path | None = None, seed_split: bool = True,
             sigma_mode: str = "se_audit") -> list[dict]:
    """Join proposals with audits.

    ``seed_split`` (default): the training soft label uses the first half of the
    audit seeds and the evaluation value Delta_true the second half
    (``audit.split_audit``: 5 + 5 for K = 10, 3 + 3 for the K = 6 pilot), so that a
    held-out proposal whose (candidate, incumbent) pair also occurs in a training
    instance (same start configuration, same audit seeds) does not share its
    audit error with the training label. ``False`` uses all K seeds for both
    (optimistic when pairs recur across instances).

    ``sigma_mode`` (R1-SOFT-SIGMA): ``"se_audit"`` (v1, default here) reproduces the
    existing tables; ``"pooled_node"`` (v2) uses s = sigma_node / sqrt(K_label) and
    records ``soft_version`` on every labelled row.
    """
    from r1.c3.analysis_guard import guard_table
    audits_path = audits_path or Path(table_dir) / "audits.jsonl"
    guard_table(table_dir, audits_path, Path(table_dir) / 'proposals.jsonl')
    meta_path = Path(table_dir) / "build.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    evidence = meta.get("label") == "EVIDENCE"
    if meta.get("classification") and not evidence:
        raise ValueError("classified table must carry an EVIDENCE label")
    if evidence and not seed_split:
        raise ValueError("EVIDENCE requires the declared label/evaluation seed split")
    if evidence:
        _verify_evidence_inputs(Path(table_dir), Path(audits_path), meta)
    rows = load_table(table_dir)
    audits = {}
    for line in Path(audits_path).read_text().splitlines():
        if line.strip():
            a = json.loads(line)
            if evidence:
                expected = list(range(7001, 7011))
                if a.get("seeds") != expected:
                    raise ValueError("EVIDENCE audits require ordered seeds 7001–7010")
                for key in ("candidate_metrics", "incumbent_metrics"):
                    values = a.get(key)
                    if not isinstance(values, list) or len(values) != 10 or any(
                            not isinstance(x, (int, float)) or isinstance(x, bool) or not np.isfinite(x)
                            for x in values):
                        raise ValueError(f"EVIDENCE audit has invalid {key}")
            audits[a["proposal_id"]] = a
    # The complete EVIDENCE population includes no-op/duplicate-only strata.
    # Pilot tables retain their original sampled-stratum behavior.
    strata = {(r["source"], r["node"]) for r in rows if evidence or r["proposal_id"] in audits}
    n_non = defaultdict(int)
    n_rand = defaultdict(int)
    for r in rows:
        k = (r["source"], r["node"])
        if k in strata and not rule_skip(r):
            n_non[k] += 1
            a = audits.get(r["proposal_id"])
            if a and (evidence or ("random" in a["reason"] and a["delta_audit"] is not None)):
                n_rand[k] += 1
    out = []
    for r in rows:
        k = (r["source"], r["node"])
        if k not in strata:
            continue
        r = dict(r)
        if evidence:
            r["_evidence_seed_split"] = True
        if is_noop(r):
            r.update(soft=soft_label(None, None, r["sigma_node"], inert=True), delta_true=0.0,
                     weight=1.0, eval_weight=1.0, audit_reason=None)
        elif is_duplicate(r):
            a = audits.get(r["proposal_id"])
            if a and (evidence or a.get("delta_audit") is not None):
                if seed_split:
                    ev = split_audit(a)[1]
                else:
                    ev = a
                dt, src = ev["delta_audit"], "audit"
            else:
                dt, src = float(r["delta_hat"]), "logged_proxy"
            r.update(soft=None, delta_true=dt, delta_true_source=src, weight=0.0, eval_weight=1.0,
                     audit_reason=a["reason"] if a else None)
        else:
            a = audits.get(r["proposal_id"])
            if not a or (not evidence and a["delta_audit"] is None):
                continue
            ratio = n_non[k] / max(n_rand[k], 1)
            if seed_split:
                lab, ev = split_audit(a)  # first half of the seeds: label; second half: evaluation
            else:
                lab = ev = a
            if lab["delta_audit"] is None or ev["delta_audit"] is None:
                continue
            if sigma_mode == "se_audit":
                soft = soft_label(lab["delta_audit"], lab["se"], r["sigma_node"], sigma_mode="se_audit")
            else:
                soft = soft_label(lab["delta_audit"], None, r["sigma_node"], sigma_mode=sigma_mode, k_label=lab["k"])
                r["soft_version"] = soft_label_version(sigma_mode)
            r.update(soft=soft, delta_true=ev["delta_audit"], weight=ratio,
                     eval_weight=ratio if evidence or "random" in a["reason"] else 0.0, audit_reason=a["reason"])
            if evidence:
                r.update(label_delta_audit=lab["delta_audit"], label_se_audit=lab["se"])
            else:
                r.update(delta_audit_all=a["delta_audit"], se_audit=a["se"])
        out.append(r)
    return out


def folds_by_instance(rows, k=3):
    """Fold id per row: rank of the instance seed within its node, modulo k."""
    fid = {}
    for node in sorted({r["node"] for r in rows}):
        seeds = sorted({r["instance_seed"] for r in rows if r["node"] == node})
        for i, s in enumerate(seeds):
            fid[(node, s)] = i % k
    return np.array([fid[(r["node"], r["instance_seed"])] for r in rows])


def crossfit(rows, mode="instance", k=3, arms=None):
    """Held-out bin distributions per arm (dict arm -> (n, 12) array)."""
    arms = arms or {"A1": ConstantPrior, "A2": RulesPrior, "A3": LGBMPrior}
    groups = folds_by_instance(rows, k) if mode == "instance" else np.array([r["node"] for r in rows])
    preds = {a: np.zeros((len(rows), N_BINS)) for a in arms}
    for gval in sorted(set(groups.tolist())):
        te = np.where(groups == gval)[0]
        tr = np.where(groups != gval)[0]
        def model_row(row, *, training):
            if not row.get("_evidence_seed_split"):
                return row
            # Evaluation-only outcomes are never passed to fit or predict.
            allowed = {"node", "features", "noop", "duplicate", "_evidence_seed_split"}
            if training:
                allowed |= {"soft", "weight"}
            return {key: value for key, value in row.items() if key in allowed}
        train = [model_row(rows[i], training=True) for i in tr]
        test = [model_row(rows[i], training=False) for i in te]
        for a, cls in arms.items():
            preds[a][te] = cls().fit(train).predict(test)
    return preds


def decisions(P, rows, g_units, rule_layer=True):
    """Plug-in decisions; with the rule layer (A2+), duplicates are never executed."""
    pi, mu, tau = prior_moments(P, rows)
    sig = np.array([r["sigma_cmp"] for r in rows])
    g = g_units * np.array([r["sigma_node"] for r in rows])
    dh = np.array([r["delta_hat"] for r in rows])
    ex, kp = rules.decide(pi, mu, tau, sig, g, dh)
    if rule_layer:
        dup = np.array([is_duplicate(r) for r in rows], bool)
        ex, kp = ex & ~dup, kp & ~dup
    return ex, kp, (pi, mu, tau, sig, g)


def rewards(rows, ex, kp, g):
    d = np.array([r["delta_true"] for r in rows])
    return d * kp - g * ex


def rho(rows, g_units):
    dh = np.array([r["delta_hat"] for r in rows])
    g = g_units * np.array([r["sigma_node"] for r in rows])
    ex = np.ones(len(rows), bool)
    return ex, ex & (dh > 0), g


def cluster_boot(diff, w, clusters, n=BOOT, seed=SEED):
    """Weighted-mean bootstrap over clusters (instances); returns draws."""
    rng = np.random.default_rng(seed)
    uc = sorted(set(clusters))
    idx = {c: np.where(np.asarray(clusters) == c)[0] for c in uc}
    sw = np.array([w[idx[c]].sum() for c in uc])
    sd = np.array([(w[idx[c]] * diff[idx[c]]).sum() for c in uc])
    draws = []
    for _ in range(n):
        pick = rng.integers(0, len(uc), len(uc))
        den = sw[pick].sum()
        draws.append(sd[pick].sum() / den if den > 0 else np.nan)
    return np.array(draws)


def capped_value(sum_wer, sum_we, sum_w, c, runs=CAMPAIGN_RUNS):
    """Per-campaign value under an LLM-proposal cap of c x W (freed-run sensitivity).

    m = sum_wer / sum_we (mean reward per executed proposal), e = sum_we / sum_w
    (execution rate); value = m x min(W, e c W). c = 1 gives W x sum_wer / sum_w,
    the primary accounting; c = inf gives W x m. An arm that executes nothing has 0.
    """
    if sum_we <= 0 or sum_w <= 0:
        return 0.0
    m, e = sum_wer / sum_we, sum_we / sum_w
    return float(m * (runs if np.isinf(c) else min(runs, e * c * runs)))


def cluster_boot_capped_diff(r_a, ex_a, r_b, ex_b, w, clusters, c, n=BOOT, seed=SEED):
    """Cluster bootstrap of capped_value(A) - capped_value(B) at call cap c; returns draws."""
    rng = np.random.default_rng(seed)
    clusters = np.asarray(clusters)
    uc = sorted(set(clusters.tolist()))
    cols = (w * ex_a * r_a, w * ex_a, w, w * ex_b * r_b, w * ex_b)
    sums = np.array([[x[clusters == k].sum() for x in cols] for k in uc])
    draws = []
    for _ in range(n):
        s = sums[rng.integers(0, len(uc), len(uc))].sum(0)
        draws.append(capped_value(s[0], s[1], s[2], c) - capped_value(s[3], s[4], s[2], c))
    return np.array(draws)


def _cap_key(c):
    return "inf" if np.isinf(c) else f"{c:g}"


def freed_run_value(r, ex, w):
    """Mean realised reward per executed proposal (weighted).

    An arm that executes nothing in the node has nothing to spend freed runs on
    (every further exchangeable proposal is skipped too), so its value is 0, the
    same as under the primary accounting.
    """
    den = float((w * ex).sum())
    return float((w * ex * r).sum() / den) if den > 0 else 0.0


def _g_role(gu):
    if np.isclose(gu, G_PRIMARY):
        return "primary"
    if any(np.isclose(gu, s) for s in G_SENSITIVITY):
        return "sensitivity"
    raise ValueError(f"g = {gu} sigma_node is not a declared value {G_EVAL} (PLAN §10, g (22 Oct)); "
                     "g = 0 is used only inside the theory checks")


def evaluate(rows, mode="instance", k=3, g_values=G_EVAL, noise=None, arms=None):
    """Held-out one-step values per arm at the declared g values. No gate verdict here (see ``gate_verdict``).

    ``arms`` (default: the A1-A3 classes of ``r1.c3.arms``) maps A1/A2/A3 to
    class-like factories, e.g. ``r1.c3.prior_model.offline_arm`` (Track H.1).
    """
    noise = noise or noise_table()
    roles = {gu: _g_role(gu) for gu in g_values}
    preds = crossfit(rows, mode, k, arms)
    w = np.array([r["eval_weight"] for r in rows])
    nodes = np.array([r["node"] for r in rows])
    inst = np.array([r["instance"] for r in rows])
    has_soft = np.array([r.get("soft") is not None for r in rows])
    soft = np.array([r["soft"] if r.get("soft") is not None else np.full(N_BINS, 1.0 / N_BINS) for r in rows])
    skip = np.array([rule_skip(r) for r in rows], bool)
    dup = np.array([is_duplicate(r) for r in rows], bool)
    res = {"mode": mode, "k": k, "n_rows": len(rows),
           "g_declaration": {"units": "sigma_node", "primary": G_PRIMARY, "sensitivity": list(G_SENSITIVITY),
                             "source": "PLAN §10, g (22 Oct), option A; fixed before any gate is computed"},
           "run_accounting": RUN_ACCOUNTING, "values": {}, "scores": {}, "theory_checks": {}}
    eval_nodes = sorted({r["node"] for r, wi, sk in zip(rows, w, skip) if wi > 0 and not sk})
    # --- scores (log score, calibration) on audited non-inert + inert rows with eval weight
    for a, P in preds.items():
        ls = log_score(soft, P)
        res["scores"][a] = {}
        for node in eval_nodes:
            m = (nodes == node) & (w > 0) & has_soft
            non = m & ~skip
            pp, yp = prob_positive(P[non]), prob_positive(soft[non])
            cal = []
            for lo, hi in ((0, .35), (.35, .5), (.5, .65), (.65, 1.01)):
                s = (pp >= lo) & (pp < hi)
                if s.any():
                    cal.append({"bin": [lo, hi], "n": int(s.sum()), "pred": float(np.average(pp[s], weights=w[non][s])),
                                "obs": float(np.average(yp[s], weights=w[non][s]))})
            res["scores"][a][node] = {
                "log_score": float(np.average(ls[m], weights=w[m])),
                "log_score_noninert": float(np.average(ls[non], weights=w[non])) if non.any() else None,
                "pi_pred_mean": float(np.average(P[m, 0], weights=w[m])),
                "inert_frac": float(np.average(soft[m, 0], weights=w[m])),
                "calibration_p_pos": cal}
    # --- realised value at each declared g (no verdicts)
    proxy = np.array([r.get("delta_true_source") == "logged_proxy" for r in rows], bool)
    for gu in g_values:
        out = {"g_sigma_units": gu, "role": roles[gu], "arms": {}, "A3_minus_A2": {},
               "freed_run_sensitivity": {"arms": {}, "A3_minus_A2": {}}}
        rr = {}
        ex0, kp0, g0 = rho(rows, gu)
        rr["A0"] = rewards(rows, ex0, kp0, g0)
        execs = {"A0": ex0}
        keeps = {"A0": kp0}
        for a, P in preds.items():
            ex, kp, (pi, mu, tau, sig, g) = decisions(P, rows, gu, rule_layer=(a != "A1"))
            rr[a] = rewards(rows, ex, kp, g)
            execs[a] = ex
            keeps[a] = kp
        out["duplicates_kept"] = {a: int((kk & dup).sum()) for a, kk in keeps.items()}
        out["duplicates_kept_with_logged_proxy"] = {a: int((kk & dup & proxy).sum()) for a, kk in keeps.items()}
        for a in rr:
            out["arms"][a] = {}
            out["freed_run_sensitivity"]["arms"][a] = {}
            for node in eval_nodes:
                m = nodes == node
                mean_r = float(np.average(rr[a][m], weights=w[m]))
                out["arms"][a][node] = {"mean_per_proposal": mean_r, "per_campaign": CAMPAIGN_RUNS * mean_r,
                                        "exec_rate": float(np.average(execs[a][m], weights=w[m]))}
                v = freed_run_value(rr[a][m], execs[a][m], w[m])
                e_w = float((w[m] * execs[a][m]).sum())
                out["freed_run_sensitivity"]["arms"][a][node] = {
                    "mean_per_executed": v,
                    "per_campaign_by_call_cap": {_cap_key(c): capped_value(float((w[m] * execs[a][m] * rr[a][m]).sum()),
                                                                           e_w, float(w[m].sum()), c)
                                                 for c in CALL_CAPS},
                    "n_executed_eval_rows": int((execs[a][m] & (w[m] > 0)).sum())}
        for node in eval_nodes:
            m = nodes == node
            diff = rr["A3"][m] - rr["A2"][m]
            gain = CAMPAIGN_RUNS * float(np.average(diff, weights=w[m]))
            draws = CAMPAIGN_RUNS * cluster_boot(diff, w[m], inst[m])
            lo, hi = np.nanpercentile(draws, [2.5, 97.5])
            out["A3_minus_A2"][node] = {"gain_per20": gain, "ci95": [float(lo), float(hi)],
                                        "delta_n": noise[node]["delta_n"], "n_instances": int(len(set(inst[m]))),
                                        "n_eval_rows": int((w[m] > 0).sum())}
            e3, e2 = execs["A3"][m].astype(float), execs["A2"][m].astype(float)
            fr = {"by_call_cap": {}, "primary_gain_per20": gain,
                  "exec_rate_A3": float(np.average(e3, weights=w[m])),
                  "exec_rate_A2": float(np.average(e2, weights=w[m]))}
            for c in CALL_CAPS:
                s3 = (float((w[m] * e3 * rr["A3"][m]).sum()), float((w[m] * e3).sum()), float(w[m].sum()))
                s2 = (float((w[m] * e2 * rr["A2"][m]).sum()), float((w[m] * e2).sum()), float(w[m].sum()))
                fd = cluster_boot_capped_diff(rr["A3"][m], e3, rr["A2"][m], e2, w[m], inst[m], c)
                fr["by_call_cap"][_cap_key(c)] = {"gain_per20": capped_value(*s3, c) - capped_value(*s2, c),
                                                  "ci95": [float(x) for x in np.percentile(fd, [2.5, 97.5])]}
            out["freed_run_sensitivity"]["A3_minus_A2"][node] = fr
        res["values"][str(gu)] = out
    # --- theory checks (Prop 7 bound vs realised threshold gain at g = G_THEORY; Prop 8 screening term
    # at the declared g values). Not gate quantities.
    res["theory_checks"]["note"] = ("Theory checks only. Proposition 7 compares the threshold gain at g = 0 "
                                    "(no screening), the only place g = 0 is used; Proposition 8 uses the "
                                    "declared g values. Not gate quantities.")
    non = ~skip & (w > 0)
    sub = [r for r, f in zip(rows, non) if f]
    if sub:
        pi3, mu3, tau3 = prior_moments(preds["A3"][non], sub)
        pi2, mu2, tau2 = prior_moments(preds["A2"][non], sub)
        sig = np.array([r["sigma_cmp"] for r in sub])
        t2 = rules.bayes_threshold(mu2, tau2, sig)
        gap = rules.gap_exact(t2, pi3, mu3, tau3, sig)
        lo_b, up_b = rules.gap_bounds(t2, pi3, mu3, tau3, sig)
        for node in sorted({r["node"] for r in sub}):
            m = np.array([r["node"] == node for r in sub])
            wn = w[non][m]
            msub = [s for s, f in zip(sub, m) if f]
            th = {"prop7_gap_under_A3_mean": float(np.average(gap[m], weights=wn)),
                  "prop7_lower_mean": float(np.average(lo_b[m], weights=wn)),
                  "prop7_upper_mean": float(np.average(up_b[m], weights=wn)),
                  "realised_threshold_gain_g0_per_noninert": None}
            # realised A3-A2 at g = G_THEORY (= 0) restricted to non-inert rows: theory check only
            ex3, kp3, _ = decisions(preds["A3"][non][m], msub, G_THEORY)
            ex2, kp2, _ = decisions(preds["A2"][non][m], msub, G_THEORY)
            d = np.array([s["delta_true"] for s in msub])
            th["realised_threshold_gain_g0_per_noninert"] = float(np.average(d * kp3 - d * kp2, weights=wn))
            for gu in G_EVAL:
                g = gu * np.array([s["sigma_node"] for s in msub])
                scr = rules.screening_term(pi3[m], mu3[m], tau3[m], sig[m], g)
                ex, kp, _ = decisions(preds["A3"][non][m], msub, gu)
                always = d * kp3 - g  # always execute, Prop 6 keep
                real = (d * kp - g * ex) - always
                th[f"prop8_screening_term_g{gu}"] = float(np.average(scr, weights=wn))
                th[f"realised_screening_gain_g{gu}"] = float(np.average(real, weights=wn))
            res["theory_checks"][node] = th
    return res


def gate_verdict(evaluation: dict) -> dict:
    """Do not apply the superseded D18 per-node gate as a B.7 verdict.

    R1-BX-D8 requires a separately reviewed and preregistered aggregate gate.
    No input is examined and no pass/fail is returned by this placeholder.
    """
    return {"verdict": "NOT_AVAILABLE",
            "reason": "STOP: R1-BX-D8 aggregate gate is not implemented and confirmed"}


def sensitivity_view(evaluation: dict) -> dict:
    """Declared-sensitivity values of A3 - A2 (no verdict) plus the freed-run accounting at every g."""
    out = {"note": "Reported for the declared sensitivity values of g and the freed-run run accounting; "
                   "no pass/fail is attached to any of these (PLAN §10, 22 Oct)."}
    for key, v in evaluation["values"].items():
        out[key] = {"role": v["role"],
                    "A3_minus_A2": ({n: {kk: x[kk] for kk in ("gain_per20", "ci95", "delta_n")}
                                     for n, x in v["A3_minus_A2"].items()} if v["role"] == "sensitivity" else
                                    "primary value: see gate"),
                    "freed_run_A3_minus_A2": v["freed_run_sensitivity"]["A3_minus_A2"]}
    return out


def table_noise(table_path: Path):
    """For pinned sweep tables, verify and load the identical noise source; preserve legacy default."""
    from r1.c3.analysis_guard import guard_table, refuse_sealed
    guard_table(table_path)
    meta_path = table_path / "build.json"
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    source = meta.get("noise_source")
    noise = None
    if source is not None:
        from r1.harness import REPO
        if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
            raise ValueError("table has malformed noise source")
        rel = Path(source["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("table noise source must be repository-relative")
        path = (REPO / rel).resolve()
        refuse_sealed(REPO / rel, path)
        if not path.is_relative_to(REPO.resolve()) or not path.is_file():
            raise ValueError("table noise source missing or outside repository")
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("table noise source sha256 mismatch")
        noise = noise_table(path)
        if noise != meta.get("noise"):
            raise ValueError("table noise constants do not match pinned source")
    return noise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--audits", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--no-seed-split", action="store_true", help="use all audit seeds for labels and values")
    args = ap.parse_args(argv)
    table_path = Path(args.table)
    noise = table_noise(table_path)
    rows = assemble(table_path, Path(args.audits) if args.audits else None, not args.no_seed_split)
    instance = evaluate(rows, "instance", args.folds, noise=noise)
    lono = evaluate(rows, "lono", noise=noise)
    result = {"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)",
              **({"noise_source": json.loads((table_path / "build.json").read_text())["noise_source"]}
                 if noise is not None else {}),
              "note": "Engineering check unless run on the frozen sweep data; tiny audited samples are not the C3 "
                      "gate decision.",
              "seed_split": not args.no_seed_split, "n_rows": len(rows),
              "g_declaration": instance["g_declaration"], "run_accounting": RUN_ACCOUNTING,
              "gate": gate_verdict(instance),
              "sensitivity": sensitivity_view(instance),
              "rows_by_stratum": {f"{s}:{n}": {"noop": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and is_noop(r)),
                                               "duplicate": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and is_duplicate(r)),
                                               "audited_other": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and not rule_skip(r))}
                                  for s, n in sorted({(r['source'], r['node']) for r in rows})},
              "instance": instance,
              "lono": lono}
    out = Path(args.out) if args.out else Path(args.table) / "offline_eval.json"
    out.write_text(json.dumps(result, indent=1))
    gate = result["gate"]
    print(json.dumps({"gate_verdict": gate["verdict"], "reason": gate["reason"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
