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

Population: (source, node) strata that have audited proposals. No-ops and
duplicates enter with evaluation weight 1. Randomly audited non-inert proposals carry weight
N_noninert / N_audited of their stratum (inverse sampling probability), so means
estimate the stratum's full proposal population. Proposals audited only because
they were DI-changed candidates (selected, not random) get weight 0 in
evaluation but are used for training.

Splits: ``instance`` = K-fold cross-fitting by instance seed (all nodes
trained together; every instance is held out once); ``lono`` = leave one node out.

C3 gate (PLAN §10, D18): per node, gain = 20 x mean per-proposal (r_A3 - r_A2)
on held-out proposals (one logged proposal = one run in a W = 20 root
campaign); pass iff gain >= delta_n on >= 2 nodes with lower 95 % cluster-
bootstrap bound (by instance) > 0.

Usage:
  python -m r1.c3.offline_eval --table DIR [--audits DIR/audits.jsonl] --out DIR/offline_eval.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from r1.c3 import rules
from r1.c3.audit import paired
from r1.c3.arms import ConstantPrior, LGBMPrior, RulesPrior, is_duplicate, is_noop, prior_moments, rule_skip
from r1.c3.dataset import load_table, noise_table
from r1.c3.labels import N_BINS, log_score, prob_positive, soft_label

G_GRID = (0.0, 0.02, 0.05, 0.1, 0.2, 0.3)  # g in units of sigma_node
CAMPAIGN_RUNS = 20
BOOT = 2000
SEED = 20261019


def assemble(table_dir: Path, audits_path: Path | None = None, seed_split: bool = True) -> list[dict]:
    """Join proposals with audits.

    ``seed_split`` (default): the training soft label uses the first half of the
    audit seeds and the evaluation value Delta_true the second half, so that a
    held-out proposal whose (candidate, incumbent) pair also occurs in a training
    instance (same start configuration, same audit seeds) does not share its
    audit error with the training label. ``False`` uses all K seeds for both
    (optimistic when pairs recur across instances).
    """
    rows = load_table(table_dir)
    audits_path = audits_path or Path(table_dir) / "audits.jsonl"
    audits = {}
    for line in Path(audits_path).read_text().splitlines():
        if line.strip():
            a = json.loads(line)
            audits[a["proposal_id"]] = a
    strata = {(r["source"], r["node"]) for r in rows if r["proposal_id"] in audits}
    n_non = defaultdict(int)
    n_rand = defaultdict(int)
    for r in rows:
        k = (r["source"], r["node"])
        if k in strata and not rule_skip(r):
            n_non[k] += 1
            a = audits.get(r["proposal_id"])
            if a and "random" in a["reason"] and a["delta_audit"] is not None:
                n_rand[k] += 1
    out = []
    for r in rows:
        k = (r["source"], r["node"])
        if k not in strata:
            continue
        r = dict(r)
        if is_noop(r):
            r.update(soft=soft_label(None, None, r["sigma_node"], inert=True), delta_true=0.0,
                     weight=1.0, eval_weight=1.0, audit_reason=None)
        elif is_duplicate(r):
            a = audits.get(r["proposal_id"])
            if a and a.get("delta_audit") is not None:
                if seed_split:
                    h = len(a["seeds"]) // 2
                    ev = paired(a["candidate_metrics"][h:], a["incumbent_metrics"][h:])
                else:
                    ev = a
                dt, src = ev["delta_audit"], "audit"
            else:
                dt, src = float(r["delta_hat"]), "logged_proxy"
            r.update(soft=None, delta_true=dt, delta_true_source=src, weight=0.0, eval_weight=1.0,
                     audit_reason=a["reason"] if a else None)
        else:
            a = audits.get(r["proposal_id"])
            if not a or a["delta_audit"] is None:
                continue
            ratio = n_non[k] / max(n_rand[k], 1)
            if seed_split:
                h = len(a["seeds"]) // 2
                lab = paired(a["candidate_metrics"][:h], a["incumbent_metrics"][:h])
                ev = paired(a["candidate_metrics"][h:], a["incumbent_metrics"][h:])
            else:
                lab = ev = a
            if lab["delta_audit"] is None or ev["delta_audit"] is None:
                continue
            r.update(soft=soft_label(lab["delta_audit"], lab["se"], r["sigma_node"]), delta_true=ev["delta_audit"],
                     delta_audit_all=a["delta_audit"], se_audit=a["se"], weight=ratio, eval_weight=ratio if "random" in a["reason"] else 0.0,
                     audit_reason=a["reason"])
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
        train = [rows[i] for i in tr]
        test = [rows[i] for i in te]
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


def evaluate(rows, mode="instance", k=3, g_grid=G_GRID, noise=None):
    noise = noise or noise_table()
    preds = crossfit(rows, mode, k)
    w = np.array([r["eval_weight"] for r in rows])
    nodes = np.array([r["node"] for r in rows])
    inst = np.array([r["instance"] for r in rows])
    has_soft = np.array([r.get("soft") is not None for r in rows])
    soft = np.array([r["soft"] if r.get("soft") is not None else np.full(N_BINS, 1.0 / N_BINS) for r in rows])
    skip = np.array([rule_skip(r) for r in rows], bool)
    dup = np.array([is_duplicate(r) for r in rows], bool)
    res = {"mode": mode, "k": k, "n_rows": len(rows), "per_g": {}, "scores": {}, "theory": {}}
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
    # --- realised value per g
    for gu in g_grid:
        out = {"arms": {}, "gate": {}}
        rr = {}
        ex0, kp0, g0 = rho(rows, gu)
        rr["A0"] = rewards(rows, ex0, kp0, g0)
        execs = {"A0": ex0}
        proxy = np.array([r.get("delta_true_source") == "logged_proxy" for r in rows], bool)
        keeps = {"A0": kp0}
        for a, P in preds.items():
            ex, kp, (pi, mu, tau, sig, g) = decisions(P, rows, gu, rule_layer=(a != "A1"))
            rr[a] = rewards(rows, ex, kp, g)
            execs[a] = ex
            keeps[a] = kp
        out["duplicates_kept"] = {a: int((k & dup).sum()) for a, k in keeps.items()}
        out["duplicates_kept_with_logged_proxy"] = {a: int((k & dup & proxy).sum()) for a, k in keeps.items()}
        for a in rr:
            out["arms"][a] = {node: {"mean_per_proposal": float(np.average(rr[a][nodes == node], weights=w[nodes == node])),
                                     "per_campaign": CAMPAIGN_RUNS * float(np.average(rr[a][nodes == node], weights=w[nodes == node])),
                                     "exec_rate": float(np.average(execs[a][nodes == node], weights=w[nodes == node]))}
                              for node in eval_nodes}
        passes = 0
        for node in eval_nodes:
            m = nodes == node
            diff = rr["A3"][m] - rr["A2"][m]
            gain = CAMPAIGN_RUNS * float(np.average(diff, weights=w[m]))
            draws = CAMPAIGN_RUNS * cluster_boot(diff, w[m], inst[m])
            lo, hi = np.nanpercentile(draws, [2.5, 97.5])
            dn = noise[node]["delta_n"]
            ok = bool(gain >= dn and lo > 0)
            passes += ok
            out["gate"][node] = {"gain_A3_minus_A2_per20": gain, "ci95": [float(lo), float(hi)], "delta_n": dn,
                                 "pass": ok, "n_instances": int(len(set(inst[m]))),
                                 "n_eval_rows": int((w[m] > 0).sum())}
        out["gate_pass"] = bool(passes >= 2)
        out["nodes_passing"] = passes
        res["per_g"][str(gu)] = out
    # --- theory checks (Prop 7 bound vs realised threshold gain; Prop 8 screening term)
    non = ~skip & (w > 0)
    sub = [r for r, f in zip(rows, non) if f]
    if sub:
        pi3, mu3, tau3 = prior_moments(preds["A3"][non], sub)
        pi2, mu2, tau2 = prior_moments(preds["A2"][non], sub)
        sig = np.array([r["sigma_cmp"] for r in sub])
        t2 = rules.bayes_threshold(mu2, tau2, sig)
        gap = rules.gap_exact(t2, pi3, mu3, tau3, sig)
        lo_b, up_b = rules.gap_bounds(t2, pi3, mu3, tau3, sig)
        r0 = res["per_g"]["0.0"]
        for node in sorted({r["node"] for r in sub}):
            m = np.array([r["node"] == node for r in sub])
            wn = w[non][m]
            th = {"prop7_gap_under_A3_mean": float(np.average(gap[m], weights=wn)),
                  "prop7_lower_mean": float(np.average(lo_b[m], weights=wn)),
                  "prop7_upper_mean": float(np.average(up_b[m], weights=wn)),
                  "realised_threshold_gain_g0_per_noninert": None}
            # realised A3-A2 at g = 0 restricted to non-inert rows
            ex3, kp3, _ = decisions(preds["A3"][non][m], [s for s, f in zip(sub, m) if f], 0.0)
            ex2, kp2, _ = decisions(preds["A2"][non][m], [s for s, f in zip(sub, m) if f], 0.0)
            d = np.array([s["delta_true"] for s, f in zip(sub, m) if f])
            th["realised_threshold_gain_g0_per_noninert"] = float(np.average(d * kp3 - d * kp2, weights=wn))
            for gu in (0.05, 0.1, 0.2):
                g = gu * np.array([s["sigma_node"] for s, f in zip(sub, m) if f])
                scr = rules.screening_term(pi3[m], mu3[m], tau3[m], sig[m], g)
                ex, kp, _ = decisions(preds["A3"][non][m], [s for s, f in zip(sub, m) if f], gu)
                always = d * kp3 - g  # always execute, Prop 6 keep
                real = (d * kp - g * ex) - always
                th[f"prop8_screening_term_g{gu}"] = float(np.average(scr, weights=wn))
                th[f"realised_screening_gain_g{gu}"] = float(np.average(real, weights=wn))
            res["theory"][node] = th
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--audits", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--no-seed-split", action="store_true", help="use all audit seeds for labels and values")
    args = ap.parse_args(argv)
    rows = assemble(Path(args.table), Path(args.audits) if args.audits else None, not args.no_seed_split)
    result = {"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)",
              "note": "Pilot engineering check; tiny audited sample; not the C3 gate decision.",
              "seed_split": not args.no_seed_split, "n_rows": len(rows),
              "rows_by_stratum": {f"{s}:{n}": {"noop": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and is_noop(r)),
                                               "duplicate": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and is_duplicate(r)),
                                               "audited_other": sum(1 for r in rows if (r['source'], r['node']) == (s, n) and not rule_skip(r))}
                                  for s, n in sorted({(r['source'], r['node']) for r in rows})},
              "instance": evaluate(rows, "instance", args.folds),
              "lono": evaluate(rows, "lono")}
    out = Path(args.out) if args.out else Path(args.table) / "offline_eval.json"
    out.write_text(json.dumps(result, indent=1))
    g = result["instance"]["per_g"]
    print(json.dumps({gu: {"gate_pass": v["gate_pass"], **{n: round(x["gain_A3_minus_A2_per20"], 5) for n, x in v["gate"].items()}}
                      for gu, v in g.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
