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

Policies: ``a2u`` (at g0), ``a2``, ``static:g,h``, ``dynamic:`` (5 or 8 positional values, rev. 7);
``pi_prime:`` is not supported here. World nodes (rev. 7, ``synthetic.WorldNode``) use ``simulate_world``, which
the analysis simulator reproduces exactly (``r1/tests/test_tracks_worlds.py``).

``certify`` (review M4) is the gate: Y is the exact expected value of each campaign's final configuration
(the law's ``y_true``, no audit noise); the best static is chosen on a selection seed block and the members are
evaluated against it on a disjoint evaluation block (both disjoint from every collector block); the number of
paired campaigns is sized from a pilot so that the 95 % half-width of every member's gain is at most
``tol`` x delta_Y (default 5 %), and the call fails if that is not reached within ``n_max``.

  python -m r1.tracks.oracle --node synthetic_P0 --W 10 --cap 40 --delta-Y 0.0033 \\
      --static static:0.00033,0 --static static:0.00066,0 \\
      --member dynamic:0.00033,0.0066,0,0,0 --out p0_oracle.json
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


def _e1_execute(controller: a2u.A2UController, mu: float, tau: float, sigma: float, view) -> bool:
    """The policy's E1 rule (``A2UController._decide_e1`` without the record): execute uses ">="."""
    v_star = float(rules.proposal_value(0.0, mu, tau, sigma))
    if controller.dynamic_e1:
        gap = a2u.budget_gap(view, controller.W)
        bonus = controller.b_info * (tau - controller.tau_bar)
        return v_star + bonus >= controller.g - controller.b_budget * (gap - controller.r1_bar)
    return a2u.static_execute(mu, tau, sigma, controller.g)


def _keep_prior(controller: a2u.A2UController, mu: float, tau: float, sigma: float, view) -> KeepPrior:
    """The policy's E2 keep prior (the harness keeps iff delta_hat > its threshold, i.e. m_hat > h)."""
    if controller.default_keep:
        return KeepPrior(mu=mu, tau=tau, sigma=sigma)
    thr = controller.h0 - (controller.h_budget * (a2u.budget_gap(view, controller.W) - controller.r2_bar)
                           if controller.h_budget != 0.0 else 0.0)
    return a2u.encoded_keep_prior(lambda m: m - thr, mu, tau, sigma, "oracle")


def _consts(text: str) -> dict[str, str]:
    import re
    pattern = re.compile(r"^(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*(?P<value>[^#\n]+?)(?:\s*#.*)?$")
    out = {}
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if m:
            out[m.group("name")] = m.group("value").strip()
    return out


def simulate_world(node, controller: a2u.A2UController, seed: int, *, W: int, cap: int, repetition: int = 0,
                   audit_seeds=(34001, 34002, 34003, 34004, 34005)) -> dict:
    """One campaign of a world node (``synthetic.WorldNode``) in memory, with the pipeline's semantics: rule
    proposals are rejected before any run, trial 1 is executed and kept, E1 / E2 by the policy on the keyed
    forecast (``a2u.A2UController._keyed_forecast``), the world worker's file transform."""
    from r1.tracks import worlds as WD
    from r1.tracks.synthetic import world_state
    node = node.bind(W=W, llm_cap=cap)
    manager = node.manager(seed, repetition)
    spec = SimpleNamespace(editable_paths=("train.py",))
    files = surface_start_files()
    meta = controller.prior.meta["world"]
    prior_post = (float(meta["mu0"]), float(meta["tau0"]) ** 2)
    posts: dict[int, tuple[float, float]] = {}
    runs, best, decisions, records = 0, None, [], []
    for t in range(1, cap + 1):
        if runs >= W:
            break
        prop = manager.propose_next_trial(SimpleNamespace(budget_index=t, current_constants=_consts(files["train.py"])),
                                          None, spec)
        blk = prop.extra["scripted"]["world"]
        if blk["kind"] == WD.RULE:
            decisions.append((t, "precondition_failed"))
            continue
        k, size, off = int(blk["key"]), float(blk["size"]), float(blk["off"])
        sigma = WD.sig_from_meta(meta, blk["kind"])
        post = posts.get(k, prior_post) if controller.update else prior_post
        a, A_ = WD.key_forecast(post, size, off, float(meta["sigma_eta"]))
        mu, tau = a, math.sqrt(A_)
        if t >= 2 and best is not None:
            ex = _e1_execute(controller, mu, tau, sigma, _budget(W, cap, runs, t - 1))
            records.append({"index": t, "epoch": "E1", "eligible": True, "action": "execute" if ex else "skip",
                            "index_value": float(rules.proposal_value(0.0, mu, tau, sigma)), "tau_pred": tau,
                            "r": a2u.budget_gap(_budget(W, cap, runs, t - 1), W)})
            if not ex:
                decisions.append((t, "skip"))
                continue
        runs += 1
        cand = node.candidate_files(files, prop, seed, runs)
        y, o, _ = world_state(cand["train.py"], node.world().y0)
        metric = y + o
        if best is None:
            keep, dhat = True, metric - float(meta["y0"])
        else:
            dhat = metric - best
            keep = dhat > _keep_prior(controller, mu, tau, sigma, _budget(W, cap, runs, t - 1)).threshold
            records.append({"index": t, "epoch": "E2", "eligible": True, "action": "keep" if keep else "discard",
                            "index_value": a2u.posterior_mean(dhat, mu, tau, sigma), "tau_pred": tau,
                            "r": a2u.budget_gap(_budget(W, cap, runs, t - 1), W)})
        posts[k] = WD.key_update(posts.get(k, prior_post), size, dhat, off, float(meta["sigma_eta"]), sigma)
        decisions.append((t, "keep" if keep else "discard"))
        if keep:
            files, best = cand, metric
    ys = node.audit(seed, files, audit_seeds)
    return {"y_terminal": float(np.mean(ys)), "y_per_seed": ys, "y_true_terminal": node.true_y(files),
            "runs_used": runs, "decisions": decisions, "final": files, "records": records}


def simulate(node, controller: a2u.A2UController, seed: int, *, W: int, cap: int, repetition: int = 0,
             audit_seeds=(34001, 34002, 34003, 34004, 34005)) -> dict:
    """One campaign in memory (module docstring). Returns y_terminal, runs_used, decisions."""
    if getattr(node, "synthetic_world", False):
        return simulate_world(node, controller, seed, W=W, cap=cap, repetition=repetition, audit_seeds=audit_seeds)
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
            kp = controller.prior.for_group("local", key, sign)
            obs = deltas.get(group, []) if controller.update else []
            mu, tau_n = a2u.group_posterior(kp, obs, controller.obs_inflation)
            tau = math.sqrt(tau_n ** 2 + kp.tau_w ** 2)
            sigma = kp.sigma_cmp
            if not _e1_execute(controller, mu, tau, sigma, _budget(W, cap, runs, t - 1)):
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
            keep = delta > _keep_prior(controller, mu, tau, sigma, _budget(W, cap, runs, t - 1)).threshold
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
    # y_true_terminal: the exact expected audited Y of the final configuration (no audit noise), review M4.
    return {"y_terminal": float(np.mean(ys)), "y_per_seed": ys, "y_true_terminal": law.y_true(final),
            "runs_used": runs, "decisions": decisions, "final": final}


def controller_for(node, policy: str, *, W: int, g0: float | None = None) -> a2u.A2UController:
    from r1.tracks.collect import policy_controller
    if policy.startswith("pi_prime:"):
        raise ValueError("the oracle simulator does not support pi_prime policies")
    prior = node.prior()
    ctx = NodeContext(node=SURFACE, start_files=surface_start_files(), sigma_node=prior.sigma_node, runs_total=W,
                      memory_mode="append_only_summary")
    g0 = float(0.1 * prior.sigma_node if g0 is None else g0)
    return policy_controller(policy, prior, ctx, g0=g0, W=W)


# Oracle seed blocks (review M4): disjoint from every collector block (instances < 40000, audits 33001-34999,
# selection 35001, S1.1 37001-37030). Best-static selection and member evaluation use different blocks.
ORACLE_SELECT_BASE = 1_000_000
ORACLE_EVAL_BASE = 2_000_000
ORACLE_BLOCK_SIZE = 1_000_000
Z95 = 1.959963984540054


class OracleToleranceError(RuntimeError):
    """The oracle could not certify a planted gain to the declared tolerance."""


def exact_values(node, controller, seeds, *, W: int, cap: int) -> np.ndarray:
    """E[Y | final configuration] (the law's y_true, no audit noise) of one campaign per seed."""
    return np.array([simulate(node, controller, int(s), W=W, cap=cap)["y_true_terminal"] for s in seeds])


def certify(node_name: str, statics: list[str], members: list[str], *, delta_Y: float, W: int, cap: int,
            tol: float = 0.05, n_select: int = 2000, n_pilot: int = 1000, n_max: int = 200000,
            params: dict | None = None, g0: float | None = None, strict: bool = True) -> dict:
    """Planted-gain certification (review M4).

    1. The best static is chosen on the selection block (``n_select`` seeds), never on the evaluation draws.
    2. On the evaluation block, a pilot of ``n_pilot`` paired campaigns gives the sd of D = Y_member - Y_best;
       n = max over members of ceil((z sd / (tol delta_Y))^2) (capped at ``n_max``), run on the same seeds.
    3. Each member's gain is reported with its 95 % half-width; the run fails (``OracleToleranceError`` when
       ``strict``) if any half-width exceeds tol x delta_Y.
    Y is the exact expected audited value of each campaign's final configuration (``y_true``)."""
    node = synthetic_node(node_name, params)
    ctls = {p: controller_for(node, p, W=W, g0=g0) for p in statics + members}
    sel_seeds = range(ORACLE_SELECT_BASE, ORACLE_SELECT_BASE + n_select)
    sel = {p: float(exact_values(node, ctls[p], sel_seeds, W=W, cap=cap).mean()) for p in statics}
    best = max(statics, key=lambda p: sel[p])
    target = tol * float(delta_Y)
    if n_select > ORACLE_BLOCK_SIZE or n_max > ORACLE_BLOCK_SIZE:
        raise ValueError("oracle seed blocks hold 10^6 seeds each")

    def ys(policy, n0, n1):
        return exact_values(node, ctls[policy], range(ORACLE_EVAL_BASE + n0, ORACLE_EVAL_BASE + n1), W=W, cap=cap)

    base = ys(best, 0, n_pilot)
    vals = {m: ys(m, 0, n_pilot) for m in members}
    sds = {m: float(np.std(vals[m] - base, ddof=1)) for m in members}
    n = min(max([n_pilot] + [math.ceil((Z95 * sd / target) ** 2) for sd in sds.values()]), n_max)
    if n > n_pilot:
        base = np.concatenate([base, ys(best, n_pilot, n)])
        vals = {m: np.concatenate([vals[m], ys(m, n_pilot, n)]) for m in members}
    gains = {}
    for m in members:
        d = vals[m] - base
        hw = Z95 * float(np.std(d, ddof=1)) / math.sqrt(n)
        gains[m] = {"gain": float(d.mean()), "half_width": hw, "within_tolerance": hw <= target}
    out = {"schema": ORACLE_SCHEMA, "label": "ENGINEERING_ONLY", "node": node.describe(), "W": W, "cap": cap,
           "best_static": best, "selection": {"seeds": [ORACLE_SELECT_BASE, ORACLE_SELECT_BASE + n_select],
                                              "values": sel},
           "evaluation": {"seeds": [ORACLE_EVAL_BASE, ORACLE_EVAL_BASE + n], "n": n}, "delta_Y": float(delta_Y),
           "tolerance": target, "gains": gains, "pass": all(g["within_tolerance"] for g in gains.values()),
           "best_member": max(members, key=lambda m: gains[m]["gain"]) if members else None}
    if strict and not out["pass"]:
        raise OracleToleranceError(f"CI half-width above {tol:.0%} of delta_Y for "
                                   f"{[m for m, g in gains.items() if not g['within_tolerance']]} at n = {n}")
    return out


def evaluate(node_name: str, policies: list[str], *, n: int, W: int, cap: int, seed_base: int = ORACLE_EVAL_BASE,
             params: dict | None = None, g0: float | None = None) -> dict:
    """Paired exact values of every policy on the same n oracle seeds (descriptive; ``certify`` for gates)."""
    node = synthetic_node(node_name, params)
    ys = {pol: exact_values(node, controller_for(node, pol, W=W, g0=g0), range(seed_base, seed_base + n), W=W, cap=cap)
          for pol in policies}
    base = policies[0]
    return {"schema": ORACLE_SCHEMA, "label": "ENGINEERING_ONLY", "node": node.describe(), "n": n, "W": W, "cap": cap,
            "seed_base": seed_base,
            "values": {p: {"mean": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(n))} for p, v in ys.items()},
            "gain_vs_first": {p: {"mean": float((v - ys[base]).mean()),
                                  "se": float((v - ys[base]).std(ddof=1) / math.sqrt(n))} for p, v in ys.items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    ap.add_argument("--static", action="append", required=True, help="static candidates (best chosen on selection seeds)")
    ap.add_argument("--member", action="append", default=[], help="members whose gain over the best static is certified")
    ap.add_argument("--delta-Y", type=float, required=True)
    ap.add_argument("--tol", type=float, default=0.05)
    ap.add_argument("--W", type=int, required=True)
    ap.add_argument("--cap", type=int, default=40)
    ap.add_argument("--n-select", type=int, default=2000)
    ap.add_argument("--n-pilot", type=int, default=1000)
    ap.add_argument("--n-max", type=int, default=200000)
    ap.add_argument("--g0", type=float, default=None)
    ap.add_argument("--params", default=None, help="JSON object of node parameters")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res = certify(args.node, args.static, args.member, delta_Y=args.delta_Y, tol=args.tol, W=args.W, cap=args.cap,
                  n_select=args.n_select, n_pilot=args.n_pilot, n_max=args.n_max,
                  params=json.loads(args.params) if args.params else None, g0=args.g0, strict=False)
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps({"pass": res["pass"], "best_static": res["best_static"], "gains": res["gains"]}))
    return 0 if res["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
