#!/usr/bin/env python3
"""Fast oracle evaluation of synthetic control nodes (rev. 6.1 amendment 5): 10^4 campaigns per policy member.

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Used to verify the planted gains of the synthetic
nodes (``r1.tracks.synthetic``) by large replication; never on a real node.

``simulate(node, policy, seed, W, cap)`` runs one campaign of a synthetic node in memory with the same
semantics as the harness loop + ``SyntheticWorker`` + the scripted manager + A2-U through
``run_real_campaign`` (the collector's ``tune``/``campaign`` phases): trial budget = cap (scripted managers
make no counted LLM call), the loop stops when W worker runs are used, trial 1 is executed and kept, rule
skips (no-ops, duplicates) by the C3 featurizer's definitions, the (key, sign) group update, the E1 rule of
the policy, the Bayes keep with the policy's encoded keep prior (``a2u.encoded_keep_prior``, the same
arithmetic as the harness path), the worker's offset mechanism and per-trial noise, and the terminal audit
over the K audit seeds. It reuses ``a2u.group_posterior``, ``rules.proposal_value``, ``a2u.budget_gap`` and
the node's own law and manager, so it differs from the pipeline only in skipping files, ledgers and the
featurizer's text replay. ``r1/tests/test_tracks_oracle.py`` checks that it reproduces the pipeline's
terminal Y, worker runs and decisions exactly.

Policies: ``a2u`` (at g0), ``a2``, ``static:``, ``matched_static:``, ``dynamic:`` (``pi_prime:`` is not
supported here).

  python -m r1.tracks.oracle --node synthetic_P0 --W 10 --cap 40 --n 10000 \\
      --policy static:g=0.0003,e2off=0 --policy dynamic:g0=0.0003,h0=0,b_budget=0.003 --out p0_oracle.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from r1.c3 import rules
from r1.c3.features import NodeContext
from r1.tracks import a2u
from r1.tracks.synthetic import FLOAT_KEYS, SURFACE, surface_start_files, synthetic_node

from autoresearch.control_plane.action_versions import KeepPrior  # noqa: E402  (harness on path via a2u)
from autoresearch.manager.hyperparam_edits import parse_train_constants, values_equal  # noqa: E402

ORACLE_SCHEMA = "tracks_oracle/v1"


def _start_constants() -> dict[str, str]:
    import re
    pattern = re.compile(r"^(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*(?P<value>[^#\n]+?)(?:\s*#.*)?$")
    out = {}
    for line in surface_start_files()["train.py"].splitlines():
        m = pattern.match(line.strip())
        if m:
            out[m.group("name")] = m.group("value").strip()
    return out


START = _start_constants()


def _num(v: str) -> float:
    return float(v)


def _cfg(consts: dict[str, str]) -> dict:
    """The configuration as ``di_test.configuration`` parses it (literal values)."""
    import ast
    return {k: ast.literal_eval(v) for k, v in consts.items()}


def _proj(consts: dict[str, str]) -> tuple:
    """Active projection on digits_mlp (all keys active), as the featurizer compares it."""
    return tuple(sorted(_cfg(consts).items()))


def _budget(W: int, cap: int, runs: int, consumed: int) -> SimpleNamespace:
    # The harness budget view (_budget_view) with a deterministic manager: no LLM call is counted.
    return SimpleNamespace(budget={"trials_remaining": cap - consumed, "trials_total": cap,
                                   "worker_runs_remaining": max(W - runs, 0), "worker_runs_used": runs,
                                   "llm_calls_remaining": cap, "llm_calls_used": 0})


def simulate(node, controller: a2u.A2UController, seed: int, *, W: int, cap: int, repetition: int = 0,
             audit_seeds=(34001, 34002, 34003, 34004, 34005)) -> dict:
    """One campaign in memory (module docstring). Returns y_terminal, runs_used, decisions."""
    law = node.law(seed)
    manager = node.manager(seed, repetition)
    consts = dict(START)
    offset_inc = 0.0
    current_best = None
    seen: set = set()
    deltas: dict[tuple, list[float]] = {}
    runs = 0
    decisions = []
    for t in range(1, cap + 1):
        if runs >= W:
            break
        key, step = manager.plan(SimpleNamespace(budget_index=t, current_constants=dict(consts)))
        old = consts[key]
        new = repr(float(old) * math.exp(float(step)))
        if values_equal(old, new):
            decisions.append((t, "precondition_failed"))
            continue
        cand = {**consts, key: new}
        o, n = _num(old), _num(new)
        sign = "+" if n > o else "-" if n < o else "0"
        group = (key, sign)
        cand_proj, inc_proj = _proj(cand), _proj(consts)
        features = t >= 2 and current_best is not None
        if features:
            if cand_proj == inc_proj or cand_proj in seen:
                decisions.append((t, "skip"))
                continue
            kp = controller.prior.kind("local")
            obs = deltas.get(group, []) if controller.update else []
            mu, tau_n = a2u.group_posterior(kp, obs, controller.obs_inflation)
            tau = math.sqrt(tau_n ** 2 + kp.tau_w ** 2)
            sigma = kp.sigma_cmp
            v_star = float(rules.proposal_value(0.0, mu, tau, sigma))
            if controller.dynamic_e1:
                gap = a2u.budget_gap(_budget(W, cap, runs, t - 1), controller.W)
                execute = v_star + controller.b_info * tau >= controller.g - controller.b_budget * gap
            else:
                execute = bool(rules.execute(0.0, mu, tau, sigma, controller.g))
            if not execute:
                decisions.append((t, "skip"))
                continue
        # Execute: the worker's offset mechanism and per-trial noise.
        runs += 1
        noise = law.run_sd(math.log(n / o)) * law.eps(seed, t)
        offset = noise if law.incumbent_error else offset_inc + noise
        metric = law.y_true(_cfg(cand)) + offset
        best_before = current_best
        if best_before is None:
            keep, delta = True, None
        else:
            delta = metric - best_before
            if controller.default_keep:
                prior = KeepPrior(mu=mu, tau=tau, sigma=sigma)
            else:
                view = _budget(W, cap, runs, t - 1)
                thr = controller.h0 - (controller.h_budget * a2u.budget_gap(view, controller.W)
                                       if controller.h_budget != 0.0 else 0.0)
                prior = a2u.encoded_keep_prior(lambda m: m - thr, mu, tau, sigma, "oracle")
            keep = delta > prior.threshold
        seen.add(cand_proj)
        if best_before is not None:
            seen.add(inc_proj)
            if features:
                deltas.setdefault(group, []).append(delta)
        decisions.append((t, "keep" if keep else "discard"))
        if keep:
            consts, offset_inc, current_best = cand, offset, metric
    final = _cfg(consts)
    ys = [law.audit(final, s) for s in audit_seeds]
    return {"y_terminal": float(np.mean(ys)), "y_per_seed": ys, "runs_used": runs, "decisions": decisions,
            "final": final}


def controller_for(node, policy: str, *, W: int, g0: float | None = None) -> a2u.A2UController:
    from r1.tracks.collect import policy_controller
    if policy.startswith("pi_prime:"):
        raise ValueError("the oracle simulator does not support pi_prime policies")
    prior = node.prior()
    ctx = NodeContext(node=SURFACE, start_files=surface_start_files(), sigma_node=prior.sigma_node, runs_total=W,
                      memory_mode="append_only_summary")
    g0 = float(0.1 * prior.sigma_node if g0 is None else g0)
    return policy_controller(policy, prior, ctx, g0=g0, W=W)


def evaluate(node_name: str, policies: list[str], *, n: int, W: int, cap: int, seed_base: int = 36000,
             params: dict | None = None, g0: float | None = None, k_audit: int = 5) -> dict:
    """Paired large-replication values: every policy on the same n instance seeds."""
    node = synthetic_node(node_name, params)
    seeds_audit = tuple(range(34001, 34001 + k_audit))
    ys = {}
    for pol in policies:
        ctl = controller_for(node, pol, W=W, g0=g0)
        ys[pol] = np.array([simulate(node, ctl, seed_base + i, W=W, cap=cap, audit_seeds=seeds_audit)["y_terminal"]
                            for i in range(n)])
    base = policies[0]
    out = {"schema": ORACLE_SCHEMA, "label": "ENGINEERING_ONLY", "node": node.describe(), "n": n, "W": W, "cap": cap,
           "seed_base": seed_base, "values": {p: {"mean": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(n))}
                                              for p, v in ys.items()},
           "gain_vs_first": {p: {"mean": float((v - ys[base]).mean()),
                                 "se": float((v - ys[base]).std(ddof=1) / math.sqrt(n))} for p, v in ys.items()}}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    ap.add_argument("--policy", action="append", required=True, help="the first policy is the reference")
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--W", type=int, required=True)
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--seed-base", type=int, default=36000)
    ap.add_argument("--g0", type=float, default=None)
    ap.add_argument("--params", default=None, help="JSON object of node parameters")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res = evaluate(args.node, args.policy, n=args.n, W=args.W, cap=args.cap, seed_base=args.seed_base,
                   params=json.loads(args.params) if args.params else None, g0=args.g0)
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res["gain_vs_first"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
