"""P9 whole-pipeline power validation on E-SYN. ENGINEERING_ONLY.

Every replicate recollects mixture roots and forks and refits the P8 grid.
The independent dev block chooses settings and family members. Two fresh
test blocks support a raw experiment and a variance-matched planning law:
if D and D' are independent campaign differences for the frozen artifacts,
(D-D') / sqrt(2) has mean zero and the same conditional variance as D.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from itertools import product
import hashlib
import json
import math
from multiprocessing import Pool
from pathlib import Path
import sys

import numpy as np
from scipy.stats import binomtest

from paperc import learner_validation as p8
from paperc import learners, ope, ope_validation
from paperc import statistics as stats
from paperc.esyn import dp, sim
from paperc.esyn.extra import WORLDS

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
OUT = ROOT / "esyn" / "power_validation_v1.json"
REPORT = ROOT / "docs" / "reports" / "POWER_VALIDATION_20261117.md"
SOURCES = (Path(__file__), PKG / "statistics.py", *p8.SOURCES)

POWER_KEY = 61_004
N_REP, N_WORKERS, N_TEST = 12, 4, 512
NODES = ("budget_a", "budget_b")
FAMILIES = ("Q1", "Q3")
SCENARIOS = ("raw", "zero", "positive")
TRAIN = range(3072)
SCREEN = range(4000, 4512)
DEV = range(8_000_000, 8_000_600)
TEST = range(9_000_000, 9_000_000 + N_TEST)
TEST_CONTROL = range(TEST.stop, TEST.stop + N_TEST)
NORMAL_N, NORMAL_SD, NORMAL_DELTA, NORMAL_REPS = 128, 1.0, 0.3, 4096


def code_sha256():
    h = hashlib.sha256()
    for path in SOURCES:
        h.update(path.name.encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


def paired_scenarios(primary, control, delta):
    primary = np.asarray(primary, dtype=float)
    control = np.asarray(control, dtype=float)
    if primary.ndim != 1 or primary.shape != control.shape:
        raise ValueError("planning law needs two independent, equal-size paired samples")
    zero = (primary - control) / math.sqrt(2)
    return {"raw": primary, "zero": zero, "positive": zero + 2 * delta}


def _counts(hits, total):
    bound = binomtest(hits, total).proportion_ci()
    return {"hits": hits, "n": total, "probability": hits / total, "mc_ci": [bound.low, bound.high]}


def normal_control(*, seed: int, reps=NORMAL_REPS):
    """Exercise the same analysis stack against known-variance closed form."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, 0]))
    rows = []
    for effect in (0.0, NORMAL_DELTA / 2):
        sup, tost = 0, 0
        for draw in rng.normal(effect, NORMAL_SD, (reps, NORMAL_N)):
            test = stats.paired_test(draw, NORMAL_DELTA, known_sd=NORMAL_SD)
            d = stats.family_decisions({"normal": test})["normal"]
            sup += d["superiority"]
            tost += d["tost_rejects"]
        exact = stats.normal_power(NORMAL_N, effect, NORMAL_SD, NORMAL_DELTA)
        rows.append({"effect": effect, "exact": exact,
                     "simulation": {"superiority": _counts(sup, reps), "tost_rejects": _counts(tost, reps)}})
    return rows


def setup(node, rep):
    # Keep the same law at two synthetic nodes, with independent world streams
    # per node and replicate. World name is part of the simulator RNG key.
    world, rungs, _ = ope_validation.setup("budget")
    world = replace(world, name=f"p9_{node}_{rep:02d}", W=4, regime=replace(world.regime, llm_cap=8))
    n4 = rungs["N4"]
    rungs["N4"] = n4.fit(n4.probs, n4.values, n4.p_rule, n4.first_gain, world.llm_cap, world.W)
    components = tuple(ope.EpsilonPolicy(p, eps, f"{key}/eps={eps:g}")
                       for key, p in rungs.items() for eps in ope_validation.EPSILON)
    mixture = ope.CampaignMixture(components, (1 / len(components),) * len(components))
    return world, rungs, mixture


def reference(world):
    law = dp.size_law(world)
    thresholds = (*law.v, max(law.v) + 1)
    dp_value = dp.solve(world).value
    best_static = max(dp.static_value(world, g) for g in thresholds)
    return {"dp": dp_value, "best_myopic": best_static, "delta": stats.esyn_margin(dp_value, best_static)}


def _fit_seed(node, rep):
    return int(np.random.SeedSequence([POWER_KEY, 1, NODES.index(node), rep]).generate_state(1)[0]) % (2 ** 31)


def _winner(candidates, scores):
    """The input order breaks dev ties, with the declared simpler method first."""
    available = [key for key in candidates if scores.get(key) is not None]
    return max(available, key=scores.__getitem__) if available else None


def train_tune_select(node, rep):
    world, rungs, mixture = setup(node, rep)
    train, records = p8.collect_roots(world, mixture, TRAIN)
    screen, _ = p8.collect_roots(world, mixture, SCREEN)
    log_support = learners.prefit_support(train, screen, ope_validation.cluster)
    data = p8.training_forks(world, train, records, rungs["N1"]) if log_support["status"] == "meets thresholds" else None

    base = sim.campaign_values(world, rungs["N1"], DEV)
    policies = {key: rungs[key] for key in ("N1", "N3", "N4")}
    scores = {"N1": 0.0, **{key: float(np.mean(sim.campaign_values(world, policies[key], DEV) - base))
                            for key in ("N3", "N4")}}
    fit_seed = _fit_seed(node, rep)
    fitted = {}
    for method, grid in p8.GRIDS.items():
        fit_policies, fit_scores, receipts = {}, {}, []
        for setting, config in enumerate(grid):
            p, support = learners.fit_supported(
                method, train, screen, config, scale=world.base.sigma_cmp, seed=fit_seed,
                cluster=ope_validation.cluster, fork_data=data, shaped=True,
            )
            gain = None if p is None else float(np.mean(sim.campaign_values(world, p, DEV) - base))
            fit_scores[setting] = gain
            if p is not None:
                fit_policies[setting] = p
            receipts.append({
                "setting": setting,
                "config": asdict(config),
                "policy": p.name if p else None,
                "dev_gain": gain,
                "prefit": support["prefit"]["status"],
                "candidate_support": support["candidate"]["status"] if support["candidate"] else None,
                "fork_support": support.get("fork_labels", {}).get("status"),
            })
        best = _winner(range(len(grid)), fit_scores)
        fitted[method] = {"selected": best, "candidates": receipts}
        if best is not None:
            policies[method], scores[method] = fit_policies[best], fit_scores[best]

    selections = {
        "Q1": (_winner(("N3", "N4", "N6"), scores), "N1"),
        "Q3": (_winner(("R0", "R1"), scores), _winner(("N4", "N6"), scores)),
    }
    receipt = {"world": world.name, "code": world.code, "fit_seed": fit_seed, "prefit": log_support,
               "training_rows": len(train.obs), "fork_points": len(data.indices) if data is not None else 0,
               "selected": selections, "fit_grid": fitted, "dev_scores": scores,
               "policies": {key: p.name for key, p in policies.items()}}
    return world, policies, scores, selections, receipt


def _test_outcomes(world, policy, instances):
    return [stats.CampaignOutcome(stats.CampaignKey(world.name, i, "c0"), float(value))
            for i, value in zip(instances, sim.campaign_values(world, policy, instances), strict=True)]


def _test_node(locked):
    world, policies, scores, selections, receipt = locked
    ref = reference(world)
    # Both selections are locked before generating either fresh test block.
    needed = {m for pair in selections.values() for m in pair if m is not None}
    observed = {m: _test_outcomes(world, policies[m], TEST) for m in sorted(needed)}
    control = {m: _test_outcomes(world, policies[m], TEST_CONTROL) for m in sorted(needed)}

    comparisons = {}
    for family, (left, right) in selections.items():
        if left is None or right is None:
            comparisons[family] = None
            continue
        main = stats.pair_campaigns(observed[left], observed[right]).differences
        other = stats.pair_campaigns(control[left], control[right]).differences
        contexts = paired_scenarios(main, other, ref["delta"])
        comparisons[family] = {"dev_difference": scores[left] - scores[right],
                               "tests": {case: stats.paired_test(d, ref["delta"]) for case, d in contexts.items()}}
    return ref, receipt, comparisons


def run_replicate(rep):
    import torch

    torch.set_num_threads(1)
    locked = {node: train_tune_select(node, rep) for node in NODES}
    tested = {node: _test_node(locked[node]) for node in NODES}
    rows = {node: {"reference": ref, **receipt, "families": {}} for node, (ref, receipt, _) in tested.items()}
    for family in FAMILIES:
        data = {node: tested[node][2][family] for node in NODES}
        for scenario in SCENARIOS:
            tests = {node: d["tests"][scenario] if d else None for node, d in data.items()}
            decision = stats.family_decisions(tests)
            for node, t in tests.items():
                entry = rows[node]["families"].setdefault(
                    family, {"dev_difference": data[node]["dev_difference"] if data[node] else None}
                )
                entry[scenario] = {"test": asdict(t) if t else None, **decision[node]}
    return {"replicate": rep, "nodes": rows}


def summarise(raw):
    result = {}
    for family, node in product(FAMILIES, NODES):
        rows = [r["nodes"][node]["families"][family] for r in raw]
        cases = {}
        for scenario in SCENARIOS:
            values = [r[scenario] for r in rows]
            cases[scenario] = {
                "superiority": _counts(sum(d["superiority"] for d in values), len(raw)),
                "tost_rejects": _counts(sum(d["tost_rejects"] for d in values), len(raw)),
                "tested": sum(d["test"] is not None and d["test"]["status"] == "tested" for d in values),
            }
        dev_gaps = [r["dev_difference"] - r["raw"]["test"]["mean"] for r in rows if r["raw"]["test"] is not None]
        result.setdefault(family, {})[node] = {
            "scenarios": cases,
            "mean_dev_minus_test": float(np.mean(dev_gaps)) if dev_gaps else None,
            "equivalence_power_floor_met": cases["zero"]["tost_rejects"]["probability"] >= stats.EQUIVALENCE_POWER_FLOOR,
            "selected_pairs": dict(Counter(
                "/".join(value or "unavailable" for value in r["nodes"][node]["selected"][family]) for r in raw
            )),
        }
    return result


def _formatted(rate):
    lo, hi = rate["mc_ci"]
    return f"{rate['hits']}/{rate['n']} [{lo:.2f}, {hi:.2f}]"


def markdown(data):
    config, ref = data["design"], data["reference"]
    lines = [
        "# P9 paired campaign statistics and pipeline power on E-SYN", "",
        "**ENGINEERING_ONLY.** Generated by `python -m paperc.power_validation`.", "",
        "## Statistical decision", "",
        "The paired unit is (node, instance seed, start configuration). Nested audit measurements first average "
        "within matched manager repetitions. Repetitions then average within a root. The fitted artifact is fixed "
        "within each test. Explicitly incomplete attempts are counted by arm and excluded as whole pairs. "
        "The analysis uses one-sided paired t superiority and the maximum of the two one-sided TOST p-values. "
        "Holm is applied across the declared nodes within each Q family, separately for superiority and TOST. "
        "Each uses α = 0.025. Unavailable nodes retain their Holm slots. Both statistical outcomes may hold. "
        "The stored paired intervals are unadjusted. The family decision uses Holm-adjusted p-values. "
        "An equivalence declaration additionally needs predeclared zero-effect power of at least 0.80.", "",
        "## Known-variance Normal control", "",
        f"The one-candidate limit uses `n={config['normal_n']}`, known SD {config['normal_sd']:g} "
        f"and symmetric margin {config['normal_delta']:g}. The simulation passes paired Normal draws through the "
        "same inference and family decision functions with known variance. The closed form integrates the "
        "Normal sample mean beyond the superiority bound or within the two TOST bounds.", "",
        "| True effect | Exact superiority | MC superiority [95% MC CI] | Exact TOST | MC TOST [95% MC CI] |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in data["normal_control"]:
        s, e = row["simulation"], row["exact"]
        lines.append(f"| {row['effect']:.3f} | {e['superiority']:.4f} | {_formatted(s['superiority'])} | "
                     f"{e['tost_rejects']:.4f} | {_formatted(s['tost_rejects'])} |")
    lines.extend([
        "", "## End-to-end E-SYN simulation", "",
        f"{config['repetitions']} independent repetitions each use two independently seeded synthetic nodes "
        "with the same short-budget E-SYN law. Each node recollects run-specific behaviour-mixture roots and "
        "N6 training forks, refits the P8 settings, screens support on separate roots, tunes each method on dev, "
        "selects the family members on dev, and then generates fresh paired test campaigns. "
        "The test uses the frozen selected artifact from the single prespecified fit seed of that repetition. "
        "The distributions across repetitions include variation from training and dev selection.", "",
        f"Per node there are {config['train_roots']} training, {config['screen_roots']} support and "
        f"{config['dev_roots']} dev roots. Test uses two disjoint blocks of {config['test_roots']} roots each. "
        "The 15 P4 logging components and P8 reward shaping and support rules carry over. Q1 selects among "
        "N3, N4 and N6 against N1. Q3 selects R0 or R1 against the dev-best of N4 and N6. Ties follow the declared "
        "method order. Training candidates that fail support are ineligible for dev selection.", "",
        f"The exact DP value is {ref['dp']:.9f}; the best same-horizon myopic value is {ref['best_myopic']:.9f}. "
        f"The E-SYN margin is 10% of their difference, δ = {ref['delta']:.9f}. "
        "The raw case uses fresh paired campaign contrasts, with common audit noise cancelling as in P8. "
        "For zero-effect planning, take two independent "
        "contrasts D and D′ for the selected artifacts and form (D − D′)/√2. The mean is exactly zero and the "
        "conditional variance is preserved. This also symmetrizes the distribution. The positive planning case "
        "adds 2δ to that contrast. The latter two are controlled test laws for planning rather than claims about "
        "the actual selected policies. The displayed TOST rates are statistical rejections, before the power gate.", "",
        "| Family | Node | Scenario | Valid t tests | Holm superiority [95% MC CI] | Holm TOST [95% MC CI] |",
        "|---|---|---|---:|---:|---:|",
    ])
    for family, nodes in data["summary"].items():
        for node, result in nodes.items():
            for case, s in result["scenarios"].items():
                lines.append(f"| {family} | {node} | {case} | {s['tested']}/{config['repetitions']} | "
                             f"{_formatted(s['superiority'])} | {_formatted(s['tost_rejects'])} |")
    lines.extend([
        "", "The denominator includes attempts with missing selections or unresolved variance. "
        "The MC intervals are exact binomial intervals across independent pipeline replicates. "
        "Holm is recalculated jointly over the two nodes in each replicate, family and scenario.", "",
        "| Family | Node | Mean dev contrast minus raw test contrast | Zero-effect point estimate reaches 0.80 |",
        "|---|---|---:|---|",
    ])
    for family, nodes in data["summary"].items():
        for node, result in nodes.items():
            early = result["mean_dev_minus_test"]
            effect = "—" if early is None else f"{early:+.8f}"
            lines.append(f"| {family} | {node} | {effect} | "
                         f"{'yes' if result['equivalence_power_floor_met'] else 'no'} |")
    lines.extend([
        "", "The dev–test gap is descriptive. It includes method selection and finite test sampling. "
        "The limited synthetic replication and short horizon give no real-node sizing or equivalence declaration. "
        "The JSON retains the candidate decisions, selected policies, exact references and per-repetition tests.", "",
        "Test references are [Holm (1979)](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf) and "
        "[Schuirmann (1987)](https://doi.org/10.1007/BF01068419).", "",
    ])
    return "\n".join(lines)


def benchmark():
    prototypes = [setup(node, rep)[0] for rep, node in product(range(N_REP), NODES)]
    before = [*WORLDS.values(), p8.setup()[0], *(ope_validation.setup(key)[0] for key in ope_validation.BENCHMARKS),
              replace(ope_validation.setup("budget")[0], name="p7_budget_support")]
    codes = {world.code for world in prototypes}
    if len(codes) != len(prototypes) or codes & {world.code for world in before}:
        raise ValueError("P9 STOP: synthetic world streams collide")
    ref = reference(prototypes[0])
    control = normal_control(seed=POWER_KEY)
    with Pool(N_WORKERS) as pool:
        raw = []
        for i, value in enumerate(pool.imap(run_replicate, range(N_REP)), 1):
            raw.append(value)
            print(f"P9 whole pipeline {i}/{N_REP} replicates", flush=True)
    return {
        "schema": "paperc_power_validation/v1", "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
        "design": {"seed": POWER_KEY, "repetitions": N_REP, "workers": N_WORKERS,
                   "nodes": NODES, "alpha": stats.ALPHA,
                   "train_roots": len(TRAIN), "screen_roots": len(SCREEN), "dev_roots": len(DEV), "test_roots": N_TEST,
                   "train_range": [TRAIN.start, TRAIN.stop], "screen_range": [SCREEN.start, SCREEN.stop],
                   "dev_range": [DEV.start, DEV.stop], "test_range": [TEST.start, TEST.stop],
                   "test_control_range": [TEST_CONTROL.start, TEST_CONTROL.stop],
                   "normal_n": NORMAL_N, "normal_sd": NORMAL_SD, "normal_delta": NORMAL_DELTA},
        "reference": ref, "normal_control": control, "raw": raw, "summary": summarise(raw),
    }


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
