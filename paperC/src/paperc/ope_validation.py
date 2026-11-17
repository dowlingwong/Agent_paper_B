"""Deterministic P7 benchmark on two exact E-SYN laws. ENGINEERING_ONLY.

Run python -m paperc.ope_validation, optionally with --report-only.
Each replicate has three independent train/evaluation blocks. Student intervals
across the block estimates include variation from fitting. Bias, RMSE and
coverage are measured across independent replicates against analytical values.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path
from statistics import NormalDist

import numpy as np
from scipy.stats import binomtest, t

from paperc import ope, policies, runner
from paperc.esyn import dp, sim, worlds
from paperc.esyn import policies as ep
from paperc.esyn.extra import WORLDS

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
OUT = ROOT / "esyn" / "ope_validation_v1.json"
REPORT = ROOT / "docs" / "reports" / "OPE_VALIDATION_20261117.md"
SOURCES = (Path(__file__), PKG / "ope.py", PKG / "schema.py", PKG / "policies.py", PKG / "seeds.py",
           PKG / "esyn" / "dp.py", PKG / "esyn" / "sim.py", PKG / "esyn" / "extra.py",
           PKG / "esyn" / "policies.py", PKG / "esyn" / "worlds.py", runner.OUT)
BENCHMARKS = ("budget", "strict_null")
TARGETS = ("N0", "N1", "N4")
METHODS = ("linear", "lightgbm")
EPSILON = (0.0, 0.1, 0.25)
COMPONENT_KEY, FIT_KEY = 60_004, 61_002
N_REP, N_BLOCK, N_TRAIN, N_EVAL = 12, 3, 150, 50
CONTROL_TRAIN, CONTROL_EVAL = 3072, 256
_NORMAL = NormalDist()


def code_sha256():
    h = hashlib.sha256()
    for path in SOURCES:
        h.update(path.name.encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


def exact_policy_value(world, policy) -> float:
    """Bellman evaluation on the size law, with analytical Gaussian keep gains."""
    law = dp.size_law(world)
    if world.run_cost != 1 or getattr(policy, "stochastic", False):
        raise ValueError("exact evaluation needs a deterministic policy and unit run cost")
    if not isinstance(policy, (policies.N0, ep.Static, policies.TrackSDynamic, policies.LawDP, ep.Threshold)):
        raise ValueError("no exact E2 threshold for this policy")
    b = world.base
    sigma = b.sig("filler")
    prior = (b.mu0, b.tau0 ** 2)
    sizes = [worlds.key_forecast(prior, size, 0.0, b.sigma_eta) for size in world.sizes]
    p_rule = world.regime.p_rule
    nxt = np.zeros(world.W + 1)
    for slots in range(1, world.llm_cap):
        cur = np.zeros_like(nxt)
        for w in range(1, world.W + 1):
            obs = {"epoch": "E1", "runs_left": w, "slots_left": slots, "W": world.W, "llm_cap": world.llm_cap}
            e2 = {**obs, "epoch": "E2", "runs_left": w - 1, "slots_left": slots - 1}
            expectation = 0.0
            for prob, v, (a, variance) in zip(law.probs, law.v, sizes):
                act, _, _ = policy.act({**obs, "v_star": v, "tau": math.sqrt(variance), "sigma": sigma})
                if act == "skip":
                    expectation += prob * nxt[w]
                    continue
                posterior_sd = variance / math.sqrt(variance + sigma ** 2)
                if isinstance(policy, policies.N0):
                    cut = a * sigma ** 2 / (variance + sigma ** 2)
                elif isinstance(policy, policies.TrackSDynamic):
                    cut = policy.h0 - policy.h_budget * (policies.budget_position(e2) - policy.r2_bar)
                else:
                    cut = getattr(policy, "h", 0.0)
                z = (cut - a) / posterior_sd
                immediate = a * _NORMAL.cdf(-z) + posterior_sd * _NORMAL.pdf(z)
                expectation += prob * (immediate + nxt[w - 1])
            cur[w] = p_rule * nxt[w] + (1 - p_rule) * expectation
        nxt = cur
    return float(np.dot(law.probs, law.a) + nxt[world.W - 1])


def setup(name):
    world = replace(WORLDS[name], name=f"p7_{name}")
    rungs = json.loads(runner.OUT.read_text())["worlds"][name]["rows"]
    n4 = rungs["N4"]["tuning"]
    base = {
        "N0": policies.N0(),
        "N1": ep.from_name(rungs["N1"]["policy"]),
        "N2": ep.from_name(rungs["N2"]["policy"]),
        "N3": policies.TrackSDynamic(*map(float, rungs["N3"]["policy"].split(":")[1].split(","))),
        "N4": policies.LawDP.fit(n4["probs"], n4["values"], n4["p_rule"], n4["first_gain"], world.llm_cap, world.W),
    }
    if any(policy.name != rungs[key]["policy"] for key, policy in base.items()):
        raise ValueError("reconstructed P4 policy identity differs from the accepted ladder")
    components = tuple(ope.EpsilonPolicy(p, eps, f"{k}/eps={eps:g}") for k, p in base.items() for eps in EPSILON)
    return world, base, ope.CampaignMixture(components, (1 / len(components),) * len(components))


def campaign_rows(world, mixture, instance, *, seed):
    """Sample one component for the campaign, then emit replayable P1 root rows."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, world.code, instance]))
    member = mixture.components[rng.choice(len(mixture.components), p=mixture.priors)]
    result = sim.run_campaign(world, member, instance, record=True, phase="P7")
    for row in result.rows:
        row["policy"]["behaviour_component"] = member.component
        row["policy"]["eps"] = member.eps
    return result.rows


def load_block(world, mixture, instances):
    rows = [row for i in instances for row in campaign_rows(world, mixture, i, seed=COMPONENT_KEY)]
    return ope.load_campaigns(rows, mixture)


def cluster(obs):
    """Fixed cutoffs on the common forecast and run budget, declared for the benchmark."""
    if obs["epoch"] == "E1":
        forecast = obs["v_star"] >= 0.001
    else:
        forecast = obs["m_hat"] > 0
    return int(forecast), int(obs["runs_left"] > obs["W"] // 2)


def block_contrast(batch):
    e2 = {i for i, ob in enumerate(batch.obs) if batch.eligible[i] and ob["epoch"] == "E2"}
    first = [next((i for i in range(start, start + length) if i in e2), None)
             for start, length in zip(batch.starts, batch.lengths)]
    idx = np.array([i for i in first if i is not None], dtype=int)
    expected_gain = np.array([batch.obs[i]["m_hat"] for i in idx], dtype=float)
    a = batch.actions[idx]
    return ope.ipw_population_contrast(a * expected_gain, a, batch.behaviour[idx]), float(expected_gain.mean())


def fit_block(args):
    name, rep, block = args
    world, base, mixture = setup(name)
    start = (rep * N_BLOCK + block) * (N_TRAIN + N_EVAL)
    train = load_block(world, mixture, range(start, start + N_TRAIN))
    evaluation = load_block(world, mixture, range(start + N_TRAIN, start + N_TRAIN + N_EVAL))
    seed = int(np.random.SeedSequence([FIT_KEY, world.code, rep, block]).generate_state(1)[0]) % (2 ** 31)
    estimates = {}
    for key in TARGETS:
        estimates[key] = {}
        for method in METHODS:
            fit = ope.evaluate(train, evaluation, base[key], method=method, cluster=cluster, seed=seed)
            estimates[key][method] = fit
    ipw, contrast = block_contrast(evaluation)
    return {"estimates": estimates, "ipw": ipw, "ipw_reference": contrast}


def mean_interval(values):
    """Student interval across independent estimators, including their refits."""
    if any(v is None for v in values):
        return {"estimate": None, "ci": None}
    n = len(values)
    mu = float(np.mean(values))
    half = float(t.ppf(0.975, n - 1) * np.std(values, ddof=1) / math.sqrt(n))
    return {"estimate": mu, "ci": [mu - half, mu + half]}


def summarise(estimates, truth):
    obs = [r for r in estimates if r["estimate"] is not None]
    if not obs:
        return {"n": 0, "bias": None, "rmse": None, "covered": 0}
    error = np.array([r["estimate"] - truth for r in obs])
    return {"n": len(obs), "bias": float(error.mean()), "rmse": float(np.sqrt(np.mean(error ** 2))),
            "covered": int(sum(r["ci"][0] <= truth <= r["ci"][1] for r in obs))}


def combine(name, blocks):
    world, base, mixture = setup(name)
    truth = {key: exact_policy_value(world, base[key]) for key in TARGETS}
    estimates, summaries, support = {}, {}, {}
    for key in TARGETS:
        estimates[key], summaries[key] = {}, {}
        for kind in METHODS:
            for method in ("fqe", "wdr"):
                tag = f"{kind}-{method}"
                estimates[key][tag] = []
                for rep in range(N_REP):
                    rows = [b["estimates"][key][kind] for b in blocks[rep * N_BLOCK:(rep + 1) * N_BLOCK]]
                    values = [r["fqe"] if method == "fqe" else r["wdr"]["value"] if r["wdr"] else None for r in rows]
                    estimates[key][tag].append(mean_interval(values))
                summaries[key][tag] = summarise(estimates[key][tag], truth[key])
        rows = [b["estimates"][key]["lightgbm"] for b in blocks]
        ess = [r["support"]["ess"] for r in rows]
        wdr = [r["wdr"] for r in rows if r["wdr"] is not None]
        support[key] = {"passes": sum(r["support"]["status"] == "meets thresholds" for r in rows),
                        "n": len(rows), "ess_min": min(ess), "ess_median": float(np.median(ess)),
                        "any_count_shortfall": sum(bool(r["support"]["action_shortfalls"]) for r in rows),
                        "any_stage_action_shortfall": sum(bool(r["support"]["missing_stage_actions"]) for r in rows),
                        "ess_shortfall": sum(v < 200 for v in ess),
                        "zero_weight_blocks": sum(bool(r["zero_weight_steps"]) for r in wdr),
                        "late_live_ess_median": float(np.median([r["live_ess_by_step"][-1] for r in wdr])) if wdr else None,
                        "fitted_blocks": len(wdr)}
    ipw = []
    for rep in range(N_REP):
        rows = blocks[rep * N_BLOCK:(rep + 1) * N_BLOCK]
        ipw.append(mean_interval([b["ipw"] - b["ipw_reference"] for b in rows]))
    return {"policies": {k: p.name for k, p in base.items()}, "components": [p.component for p in mixture.components],
            "truth": truth, "summary": summaries, "replicates": estimates, "support": support,
            "ipw_summary": summarise(ipw, 0), "ipw_replicates": ipw, "blocks": blocks}


def removed_support():
    world, base, _ = setup("budget")
    only = ope.EpsilonPolicy(ep.Static(1.0, 0.0), 0.0, "always-skip")
    mix = ope.CampaignMixture((only,), (1.0,))
    start = N_REP * N_BLOCK * (N_TRAIN + N_EVAL)
    train = load_block(world, mix, range(start, start + 16))
    evaluation = load_block(world, mix, range(start + 16, start + 24))
    target = base["N0"]
    return ope.support_diagnostics(train, evaluation, evaluation.target(target), cluster,
                                   train_target_p=train.target(target))


def supported_control():
    """One larger-sample check on the budget law with an eight-slot horizon."""
    world, base, _ = setup("budget")
    world = replace(world, name="p7_budget_support", W=4, regime=replace(world.regime, llm_cap=8))
    n4 = base["N4"]
    base["N4"] = policies.LawDP.fit(n4.probs, n4.values, n4.p_rule, n4.first_gain, world.llm_cap, world.W)
    components = tuple(ope.EpsilonPolicy(p, eps, f"{k}/eps={eps:g}") for k, p in base.items() for eps in EPSILON)
    mixture = ope.CampaignMixture(components, (1 / len(components),) * len(components))
    truth = exact_policy_value(world, base["N4"])
    rows = []
    for block in range(N_BLOCK):
        begin = block * (CONTROL_TRAIN + CONTROL_EVAL)
        split = begin + CONTROL_TRAIN
        train = load_block(world, mixture, range(begin, split))
        evaluation = load_block(world, mixture, range(split, split + CONTROL_EVAL))
        seed = int(np.random.SeedSequence([FIT_KEY, world.code, 0, block]).generate_state(1)[0]) % (2 ** 31)
        rows.append({method: ope.evaluate(train, evaluation, base["N4"], method=method, cluster=cluster, seed=seed)
                     for method in METHODS})
    intervals = {}
    for method in METHODS:
        fits = [r[method] for r in rows]
        intervals[method] = {
            "fqe": mean_interval([r["fqe"] for r in fits]),
            "wdr": mean_interval([r["wdr"]["value"] if r["wdr"] else None for r in fits]),
            "supported": sum(r["screen_value"] is not None for r in fits),
        }
    return {"world": world.name, "truth": truth, "blocks": rows, "summary": intervals,
            "slots": world.llm_cap, "runs": world.W, "train": CONTROL_TRAIN, "evaluation": CONTROL_EVAL,
            "policy": base["N4"].name}


def _display(x):
    return f"{x:.6f}" if x is not None else "—"


def _coverage(summary, total):
    n, k = summary["n"], summary["covered"]
    if n == 0:
        return f"— (0/{total} intervals)"
    bound = binomtest(k, n).proportion_ci()
    return f"{k}/{n} [{bound.low:.2f}, {bound.high:.2f}]"


def markdown(result):
    lines = [
        "# P7 off-policy evaluation on E-SYN", "",
        "ENGINEERING_ONLY. Generated by `python -m paperc.ope_validation`. Data and source fingerprint in "
        "`paperC/esyn/ope_validation_v1.json`.", "",
        "## Design", "",
        "The budget and strict-null laws have fresh keys, independent Gaussian comparisons and finite budgets. "
        "The exact reference evaluates each frozen policy by backward induction over slots and runs left. It "
        "averages over rule skips and the discrete proposal-size law and integrates the Gaussian keep gain. "
        "Slot 1 is forced execute and keep. OPE uses audited terminal minus start as its sole reward.", "",
        "Each campaign draws one of the five frozen P4 rungs N0, N1, N2, N3 and N4 crossed with "
        "ε ∈ {0, 0.1, 0.25}, with equal probability. At each eligible decision the epsilon draw mixes the rung "
        "with a uniform binary action. For OPE, the mixture posterior conditions on the logged history of actions "
        "and states. Stochastic actions are replayed from the logged epsilon key. Replay and propensity "
        "reconstruction use the same belief view. Deterministic rule steps have probability one.", "",
        f"Each world has {N_REP} independent replicates of {N_BLOCK} disjoint blocks. Each block has "
        f"{N_TRAIN} training and {N_EVAL} held-out campaigns. Target policies N0, N1 and N4 were fixed in advance. "
        "The two FQE fits update backwards over slot and epoch with a linear ridge regressor or small CPU "
        "LightGBM. WDR uses those same fits, marginal mixture likelihood ratios and stepwise normalization "
        "with absorbing padding. When no weight survives, the model supplies the remaining prediction.", "",
        "The point estimate is the mean across block fits. The 95% Student interval uses variation across "
        "independent blocks, including refitting variation. Coverage counts use exact binomial limits and the "
        "denominator counts complete intervals. The observed bias and coverage are descriptive at this replication count.", "",
        "## Value errors", "",
        "| World | Target | Exact value | FQE model | Estimator | Bias | RMSE | Coverage [95% binomial CI] |",
        "|---|---|---:|---|---|---:|---:|---|",
    ]
    for world, values in result["worlds"].items():
        for key, summaries in values["summary"].items():
            for tag, stats in summaries.items():
                model, method = tag.split("-")
                lines.append(f"| {world} | {key} | {values['truth'][key]:.6f} | {model} | {method.upper()} | "
                             f"{_display(stats['bias'])} | {_display(stats['rmse'])} | {_coverage(stats, N_REP)} |")
    lines.extend([
        "", "## Support", "",
        "Clusters cross epoch, forecast region (V* ≥ 0.001 at E1, m̂ > 0 at E2) and whether "
        "more than half the run budget remains. Each action needs 30 training observations per "
        "cluster, and the target needs 200 effective held-out decisions using local action ratios. "
        "A shortfall gives insufficient data. This status also applies to a required stage-action cell with no "
        "training examples, known zero target-action propensity, or an unfitted stage. Stage-action coverage "
        "is checked for both recursive backups and held-out predictions.", "",
        "| World | Target | Supported blocks | Cluster count shortfall | Stage-action shortfall | ESS < 200 | "
        "Decision ESS min / median | WDR blocks with zero weight at any step | Median last-step live ESS |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for world, values in result["worlds"].items():
        for key, s in values["support"].items():
            last = s["late_live_ess_median"]
            lines.append(f"| {world} | {key} | {s['passes']}/{s['n']} | {s['any_count_shortfall']} | "
                         f"{s['any_stage_action_shortfall']} | {s['ess_shortfall']} | {s['ess_min']:.1f} / {s['ess_median']:.1f} | "
                         f"{s['zero_weight_blocks']}/{s['fitted_blocks']} | {last if last is not None else '—'} |")
    fail = result["removed_support"]
    lines.extend([
        "", f"The deliberate support removal returns **{fail['status']}** for N0. "
        f"Its execute actions have zero propensity in {fail['zero_propensity_target_rows']} held-out rows.",
        "", "Value errors include screens with support shortfalls to expose the effect of extrapolation. "
        "These runs have a null screen value and an insufficient-data status in the raw results. Local action ESS can be high while "
        "the sequential WDR correction has few compatible live trajectories. Late corrections in that case rely "
        "heavily on the fitted model. Behaviour-data diagnostics cannot assess states that no behaviour campaign visits.",
        "", "## Single-decision IPW population contrast", "",
        "For each holdout campaign, use its first eligible E2 state if it has one. Define a synthetic contrast "
        "with reward m̂ for keep and zero for discard. The finite observed-state reference is the mean m̂. "
        "The HT estimator uses the history-conditional action propensity. Bias and RMSE are errors against each "
        "block's own reference. Fork contrasts use the separate design weights 1/p_select in P6.", "",
        "| World | Bias | RMSE | Coverage [95% binomial CI] |", "|---|---:|---:|---|",
    ])
    for world, values in result["worlds"].items():
        s = values["ipw_summary"]
        lines.append(f"| {world} | {_display(s['bias'])} | {_display(s['rmse'])} | {_coverage(s, N_REP)} |")
    control = result["support_control"]
    lines.extend([
        "", "## Supported positive control", "",
        f"This follow-up uses the same size and measurement law with {control['slots']} slots and "
        f"{control['runs']} runs. It retains all 15 behaviour components and recomputes the N4 threshold "
        "table for the shorter horizon from the accepted N4 value law.", "",
        f"Each of {len(control['blocks'])} disjoint blocks uses {control['train']} training and "
        f"{control['evaluation']} held-out roots. The exact N4 value is {control['truth']:.6f}. This check "
        "exercises the passing screen path. Its one set of intervals does not estimate coverage.", "",
        "| Model | Supported blocks | FQE [95% interval] | WDR [95% interval] |",
        "|---|---:|---|---|",
    ])
    def show(row):
        if row["ci"] is None:
            return "—"
        lo, hi = row["ci"]
        return f"{row['estimate']:.6f} [{lo:.6f}, {hi:.6f}]"

    for method, est in control["summary"].items():
        lines.append(f"| {method} | {est['supported']}/{len(control['blocks'])} | "
                     f"{show(est['fqe'])} | {show(est['wdr'])} |")
    lines.extend([
        "", "OPE is a screening tool. This synthetic validation uses two tractable E-SYN laws and a specified "
        "behaviour mixture. It leaves the real-node state clusters, collection support, estimator calibration and "
        "test campaign performance for their own in-tier checks.",
        "", "Methods: [Le, Voloshin and Yue (2019)](https://proceedings.mlr.press/v97/le19a.html) and "
        "[Thomas and Brunskill (2016)](https://proceedings.mlr.press/v48/thomasa16.html).", "",
    ])
    return "\n".join(lines)


def main():
    print("budget support control: fitting three larger blocks", flush=True)
    control = supported_control()
    print(f"budget support control: {control['summary']['lightgbm']['supported']}/{N_BLOCK} blocks passed",
          flush=True)
    results = {}
    for name in BENCHMARKS:
        print(f"{name}: building OPE benchmark", flush=True)
        jobs = [(name, rep, block) for rep in range(N_REP) for block in range(N_BLOCK)]
        with Pool(2) as pool:
            blocks = []
            for i, row in enumerate(pool.imap(fit_block, jobs), 1):
                blocks.append(row)
                if i % N_BLOCK == 0:
                    print(f"{name}: {i // N_BLOCK}/{N_REP} replicates", flush=True)
        results[name] = combine(name, blocks)
    result = {"schema": "paperc_ope_validation/v1", "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
              "design": {"worlds": BENCHMARKS, "replicates": N_REP, "blocks": N_BLOCK, "train": N_TRAIN,
                         "evaluation": N_EVAL, "targets": TARGETS, "epsilon": EPSILON,
                         "component_key": COMPONENT_KEY, "fit_key": FIT_KEY},
              "worlds": results, "removed_support": removed_support(), "support_control": control}
    OUT.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    REPORT.write_text(markdown(result))
    return REPORT


if __name__ == "__main__":
    if "--report-only" in sys.argv[1:]:
        REPORT.write_text(markdown(json.loads(OUT.read_text())))
        print(REPORT)
    else:
        print(main())
