"""P8 E-SYN learner benchmark. ENGINEERING_ONLY. Run with CPU thread limits.

The design constants and candidate grids define the benchmark before training.
Fit and OPE support roots are disjoint. Dev chooses the highest paired mean
over N1, with ties in grid order. The selected setting is fit with three
seeds and tested once on a common fresh campaign block.
"""
from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.stats import t

from paperc import forks, learners, ope, ope_validation, runner, schema
from paperc.esyn import dp, sim
from paperc.esyn import policies as esyn_policies

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
OUT = ROOT / "esyn" / "learner_validation_v1.json"
REPORT = ROOT / "docs" / "reports" / "LEARNER_VALIDATION_20261117.md"
SOURCES = (PKG / "learners.py", PKG / "learner_validation.py", PKG / "forks.py",
           *ope_validation.SOURCES)
COMPONENT_KEY, FIT_KEY = 60_005, 61_003
TRAIN = range(4096)
SCREEN = range(4500, 5268)
DEV = range(6_000_000, 6_001_200)
TEST = range(7_000_000, 7_006_000)
N_FIT = 3
FORK_RATE, FORK_REPS = 0.75, 4
GAIN_FLOOR = 0.10
GRIDS = {
    "N6": tuple(learners.N6Config(alpha) for alpha in (0.25, 5.0, 50.0)),
    "R0": tuple(learners.FQIConfig(leaves, rounds) for leaves, rounds in ((7, 36), (15, 48), (31, 64))),
    "R1": tuple(learners.IQLConfig(tau, beta) for tau, beta in ((0.7, 3.0), (0.8, 8.0), (0.9, 16.0))),
}


def code_sha256():
    h = hashlib.sha256()
    for path in SOURCES:
        h.update(path.name.encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


def setup():
    world, rungs, _ = ope_validation.setup("budget")
    world = replace(world, name="p8_short_budget", W=4, regime=replace(world.regime, llm_cap=8))
    n4 = rungs["N4"]
    rungs["N4"] = n4.fit(n4.probs, n4.values, n4.p_rule, n4.first_gain, world.llm_cap, world.W)
    components = tuple(ope.EpsilonPolicy(policy, eps, f"{key}/eps={eps:g}")
                       for key, policy in rungs.items() for eps in ope_validation.EPSILON)
    mixture = ope.CampaignMixture(components, (1.0 / len(components),) * len(components))
    return world, rungs["N1"], mixture


def collect_roots(world, mixture, instances):
    """Use one replayable component per root, as in the P7 loader."""
    records = {}
    for i in instances:
        rng = np.random.default_rng(np.random.SeedSequence([COMPONENT_KEY, world.code, i]))
        member = mixture.components[rng.choice(len(mixture.components), p=mixture.priors)]
        root = sim.run_campaign(world, member, i, record=True, phase="P8")
        for row in root.rows:
            row["policy"]["behaviour_component"] = member.component
            row["policy"]["eps"] = member.eps
        cid = root.rows[0]["identity"]["campaign_id"]
        records[cid] = (i, member, root.rows)
    batch = ope.load_campaigns([r for _, _, rows in records.values() for r in rows], mixture)
    return batch, records


def training_forks(world, behaviour_batch, records, base):
    """Design interventions from mixture roots, with one fixed continuation N1."""
    design = forks.Design(q_uniform=FORK_RATE, q_oversample=0.0, band_e1=0.0, band_e2=0.0,
                          g=base.g, h=base.h)
    indices, differences = [], []
    for cid, offset in zip(behaviour_batch.ids, behaviour_batch.starts):
        instance, member, rows = records[cid]
        for point in forks.select_forks(world, instance, rows, design):
            q, _, _ = forks.fork_cells(world, member, instance, point, [base], FORK_REPS)
            idx = int(offset + point.step)
            if not behaviour_batch.eligible[idx] or behaviour_batch.obs[idx]["epoch"] != point.epoch:
                raise ValueError("fork lost alignment with its mixture root")
            indices.append(idx)
            differences.append(float(q.mean()))
    return learners.ForkTraining(np.asarray(indices, dtype=int), np.asarray(differences))


def _seed(world, rep):
    return int(np.random.SeedSequence([FIT_KEY, world.code, rep]).generate_state(1)[0]) % (2 ** 31)


def _paired(gains):
    n = len(gains)
    mean = float(np.mean(gains))
    se = float(np.std(gains, ddof=1) / math.sqrt(n))
    half = float(t.ppf(0.975, n - 1) * se)
    return {"mean": mean, "se": se, "ci": [mean - half, mean + half], "n": n}


def tune_method(world, method, train, screen, data, base_dev):
    """Return the three seeds of the dev-selected setting with support receipts."""
    scale = world.base.sigma_cmp

    def fit(config, rep):
        return learners.fit_supported(method, train, screen, config, scale=scale, seed=_seed(world, rep),
                                      cluster=ope_validation.cluster, fork_data=data, shaped=True)

    scores = []
    best = None
    for idx, cfg in enumerate(GRIDS[method]):
        policy, coverage = fit(cfg, 0)
        gain = None if policy is None else float(np.mean(sim.campaign_values(world, policy, DEV) - base_dev))
        scores.append({"candidate": idx, "config": asdict(cfg), "dev_gain": gain, "support": coverage})
        if gain is not None and (best is None or gain > best[0]):
            best = (gain, idx, policy)
    result = {"method": method, "candidates": scores, "selected": None}
    if best is None:
        return [], result

    _, idx, policy = best
    repeats = [policy]
    receipts = [scores[idx]["support"]]
    for rep in range(1, N_FIT):
        other, receipt = fit(GRIDS[method][idx], rep)
        receipts.append(receipt)
        if other is not None:
            repeats.append(other)
    result["selected"] = idx
    result["refits"] = receipts
    result["fit_seeds"] = [_seed(world, i) for i in range(N_FIT)]
    result["policy_ids"] = [p.name for p in repeats]
    return (repeats if len(repeats) == N_FIT else []), result


def removed_support(world):
    # This logger skips every eligible E1; after trial 1 it never visits E2.
    base = ope.EpsilonPolicy(esyn_policies.Static(1.0, 0.0), 0.0, "always-skip")
    mix = ope.CampaignMixture((base,), (1.0,))
    train, _ = collect_roots(world, mix, range(6000, 6128))
    screen, _ = collect_roots(world, mix, range(6200, 6328))
    result = {}
    for method, configs in GRIDS.items():
        p, support = learners.fit_supported(method, train, screen, configs[0], scale=world.base.sigma_cmp,
                                            seed=_seed(world, 0), cluster=ope_validation.cluster)
        result[method] = {"policy": p.name if p else None, "support": support}
    return result


def benchmark():
    import torch

    torch.set_num_threads(1)
    world, base, mixture = setup()
    law = dp.size_law(world)
    thresholds = (*law.v, max(law.v) + 1.0)
    best_g = max(thresholds, key=lambda g: dp.static_value(world, g))
    best_static = dp.static_value(world, best_g)
    solution = dp.solve(world)
    oracle = esyn_policies.Threshold(solution.table)
    exact_oracle = ope_validation.exact_policy_value(world, oracle)
    if not math.isclose(exact_oracle, solution.value, rel_tol=0, abs_tol=1e-14):
        raise ValueError("P8 STOP: exact DP and policy evaluation disagree")
    n1 = ope_validation.exact_policy_value(world, base)
    gap = exact_oracle - n1
    if gap <= 0:
        raise ValueError("P8 STOP: benchmark has no N1-to-DP gain")

    print("P8: collecting and independently replaying training and support roots", flush=True)
    train, records = collect_roots(world, mixture, TRAIN)
    screen, _ = collect_roots(world, mixture, SCREEN)
    prefit = learners.prefit_support(train, screen, ope_validation.cluster)
    print("P8: prefit support", prefit["status"], flush=True)
    print("P8: collecting training-only N6 forks", flush=True)
    data = training_forks(world, train, records, base) if prefit["status"] == "meets thresholds" else None
    if data is not None:
        print("P8: total fork points", len(data.indices), flush=True)

    # All choices are sealed using only train, screen and dev before TEST is generated.
    dev = sim.campaign_values(world, base, DEV)
    policies, methods = {}, {}
    for method in GRIDS:
        print("P8: fitting and selecting", method, flush=True)
        policies[method], methods[method] = tune_method(world, method, train, screen, data, dev)

    base_test = sim.campaign_values(world, base, TEST)
    static_test = sim.campaign_values(world, esyn_policies.Static(best_g, 0.0), TEST)
    dp_test = _paired(sim.campaign_values(world, oracle, TEST) - base_test)
    if abs(dp_test["mean"] - gap) > 5 * dp_test["se"] + 1e-14:
        raise ValueError("P8 STOP: on-policy DP check disagrees with exact gain beyond five paired s.e.")
    for method, fits in policies.items():
        print("P8: held-out evaluation", method, flush=True)
        if not fits:
            methods[method]["test"] = {"status": "insufficient data"}
            continue
        returns = np.asarray([sim.campaign_values(world, p, TEST) for p in fits])
        gains = returns - base_test
        test = _paired(gains.mean(axis=0))
        test.update({"status": "evaluated", "gain_share": test["mean"] / gap,
                     "share_ci": [x / gap for x in test["ci"]],
                     "fit_mean_gains": np.mean(gains, axis=1).tolist(),
                     "vs_best_static": _paired(returns.mean(axis=0) - static_test),
                     "clears_gain_floor": test["mean"] / gap >= GAIN_FLOOR})
        methods[method]["test"] = test

    return {
        "schema": "paperc_learner_validation/v1", "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
        "design": {
            "world": world.name, "slots": world.llm_cap, "runs": world.W,
            "train": [TRAIN.start, TRAIN.stop], "screen": [SCREEN.start, SCREEN.stop],
            "dev": [DEV.start, DEV.stop], "test": [TEST.start, TEST.stop],
            "component_key": COMPONENT_KEY, "fit_key": FIT_KEY, "fit_count": N_FIT,
            "n6_rate": FORK_RATE, "n6_reps_per_arm": FORK_REPS, "gain_floor": GAIN_FLOOR,
            "epsilons": ope_validation.EPSILON, "continuation": base.name, "threads": 1,
        },
        "reference": {"N1": n1, "DP": exact_oracle, "best_static_bayes_keep": best_static,
                      "best_static_threshold": best_g, "gap": gap, "dp_paired_check": dp_test},
        "training": {"rows": len(train.obs), "roots": len(train.ids), "fork_points": 0 if data is None else len(data.indices),
                     "screen_rows": len(screen.obs), "prefit": prefit},
        "methods": methods,
        "removed_support": removed_support(world),
    }


def markdown(result):
    d, ref = result["design"], result["reference"]
    lines = [
        "# P8 learner validation on E-SYN", "",
        "**ENGINEERING_ONLY.** Generated by `python -m paperc.learner_validation`.", "",
        "## Benchmark design", "",
        f"The short budget world uses the P7 control's size and comparison law with {d['slots']} slots and "
        f"{d['runs']} runs. Its baseline uses the frozen P4 N1 thresholds ({d['continuation']}). "
        "The best static Bayes-keep value, computed for this shorter horizon, is reported separately. "
        "A campaign-level mixture draws five P4 rungs crossed with ε ∈ {0, 0.1, 0.25}. "
        "N4 uses its frozen value law with a threshold table for this horizon.", "",
        f"Training roots {d['train']} and support roots {d['screen']} use disjoint half-open ranges. "
        f"Dev {d['dev']} and test {d['test']} use separate unrecorded root ranges. Each method has three "
        "fixed candidate settings and one screening fit per setting. Among supported candidates, choose the "
        "highest mean paired dev gain over N1, resolving ties in grid order. Refit the selected setting "
        f"for {d['fit_count']} declared fit seeds in total and average their paired test gains per root. "
        "The paired Student interval describes test-root variation conditional on the fitted policies. "
        "Individual seed means are retained.", "",
        "Every learner uses the same legal feature view, including runs, calls and proposal slots left. "
        f"N6 adds training-only fork labels at uniform probability {d['n6_rate']:.2f}. It averages "
        f"{d['n6_reps_per_arm']} rollouts per arm with a single frozen N1 continuation and fits unweighted "
        "per-epoch ridge regressions of total Q differences. R0 uses LightGBM for backwards fitted Q "
        "iteration with a supported-action maximum. CPU R1 uses a small double-critic IQL MLP and "
        "the mode of its advantage-weighted actor. Both RL learners use γ = 1.", "",
        "R0 and R1 redistribute the audited terminal reward using the accumulated logged posterior means of "
        "keeps as a potential, with zero potential at absorption. The final transition subtracts the "
        "accumulated potential, preserving each root's total reward. N6 uses the noise-free simulator "
        "fork outcomes as training labels. Test estimates use unshaped paired terminal gains. The root "
        "audit draws are common across policies and cancel in their paired difference.", "",
        f"The declared engineering floor is a mean gain of {100*d['gain_floor']:.0f}% of the exact "
        "N1-to-DP gap. The benchmark reports each method's test interval and records whether its "
        "point estimate clears the floor. It uses the transported P4 baseline and a short horizon.", "",
        "## Reference and supported results", "",
        f"Exact N1 {ref['N1']:.8f}, exact DP {ref['DP']:.8f}, exact gap {ref['gap']:.8f}. "
        f"The best deterministic static Bayes-keep value for this horizon is {ref['best_static_bayes_keep']:.8f}. "
        f"Paired simulation recovered a DP-minus-N1 mean of {ref['dp_paired_check']['mean']:.8f} "
        f"over {ref['dp_paired_check']['n']} test roots.", "",
        f"Logged training contained {result['training']['rows']} decisions and "
        f"{result['training']['fork_points']} selected fork points. Prefit status was "
        f"**{result['training']['prefit']['status']}**.", "",
        "| Method | Dev-selected configuration | Gain over N1 [95% CI] | DP gap recovered [95% CI] | "
        "Gain over short-horizon static [95% CI] | Clears floor |",
        "|---|---|---:|---:|---:|---|",
    ]
    for name, row in result["methods"].items():
        x = row["test"]
        if x["status"] != "evaluated":
            lines.append(f"| {name} | — | insufficient data | — | — | — |")
            continue
        cfg = row["candidates"][row["selected"]]["config"]
        settings = ", ".join(f"{key}={value:g}" for key, value in cfg.items())
        lo, hi = x["ci"]
        slo, shi = x["share_ci"]
        sv = x["vs_best_static"]
        vlo, vhi = sv["ci"]
        lines.append(f"| {name} | {settings} | {x['mean']:+.8f} [{lo:+.8f}, {hi:+.8f}] | "
                     f"{x['gain_share']:.1%} [{slo:.1%}, {shi:.1%}] | "
                     f"{sv['mean']:+.8f} [{vlo:+.8f}, {vhi:+.8f}] | {'yes' if x['clears_gain_floor'] else 'no'} |")
    lines.extend([
        "", "## Deliberately removed support", "",
        "The removal logger skips every eligible E1 and visits no eligible E2. "
        "Before fitting, the gate checks both legal arms using P7's cluster counts, stage-action coverage, "
        "local decision ESS and known zero propensity. N6 additionally checks for fork labels at each visited "
        "stage and cluster. The gate checks each candidate policy before dev evaluation. "
        "The unsupported path yields no deployable policy.", "",
        "| Method | Prefit status | Held-out zero-propensity target rows |",
        "|---|---|---:|",
    ])
    for name, entry in result["removed_support"].items():
        s = entry["support"]["prefit"]
        lines.append(f"| {name} | {s['status']} | {s['zero_propensity_target_rows']} |")
    lines.extend([
        "", "Coverage and performance here concern the specified E-SYN law and logging mixture. "
        "Real-loop training support, the logged fork loader and confirmation on fresh audited campaigns "
        "have separate gates.", "",
        "Algorithm references are [Ernst et al.](https://www.jmlr.org/papers/v6/ernst05a.html) and "
        "[Kostrikov et al.](https://arxiv.org/abs/2110.06169).", "",
    ])
    return "\n".join(lines)


def main():
    if "--report-only" in sys.argv[1:]:
        result = json.loads(OUT.read_text())
    else:
        result = benchmark()
        OUT.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    REPORT.write_text(markdown(result))
    return REPORT


if __name__ == "__main__":
    print(main())
