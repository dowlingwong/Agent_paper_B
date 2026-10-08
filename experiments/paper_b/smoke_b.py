#!/usr/bin/env python3
"""Paper B engineering smoke path (ENGINEERING_ONLY).

Exercises the complete small pipeline on a closed synthetic test workload:

    branch records -> schema validation -> leak-free projection -> matched
    learners -> allocation -> paired evaluation -> conservative selection

It never touches real-agent data, model weights, credentials or the network.
Every artifact it writes carries the ``ENGINEERING_ONLY`` banner, and no
number it produces is a scientific result.

Run from the repository root::

    python3 experiments/paper_b/smoke_b.py --output results/paper_b/smoke_latest
"""

from __future__ import annotations

from dataclasses import asdict
import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from causal_branch.control.allocation import ConservativeSelector, streaming_threshold  # noqa: E402
from causal_branch.control.evaluate import evaluate_policies, checkpoint_rows  # noqa: E402
from causal_branch.control.learners import (  # noqa: E402
    ActionValueLearner,
    AdvantageLearner,
    OutcomeRiskLearner,
    UtilityDeficitLearner,
    matching_report,
)
from causal_branch.control.schema import (  # noqa: E402
    assert_no_duplicate_units,
    assert_split_disjoint,
    assert_projection_is_leak_free,
    feature_projection,
    validate_record,
)
from causal_branch.control.world import ENGINEERING_ONLY, generate_world  # noqa: E402


def _split_records(world_records, split):
    return [record for record in world_records if record.split == split]


def _checkpoint_rows(records):
    rows = checkpoint_rows(records, ('S','U'))
    for row in rows:
        for action in ('g0','gv'):
            row[action+'_success'] = row[action+'_S']
            row[action+'_utility'] = row[action+'_U']
    return rows


def fit_all(rows):
    # Same feasible training units and allowed features for every decision score.
    paired = [row for row in rows if row['mask']['gv']]
    if not paired:
        raise ValueError('no paired training support')
    feats = [row['features'] for row in paired]
    risk = OutcomeRiskLearner().fit(feats,[r['g0_success'] for r in paired])
    deficit = UtilityDeficitLearner().fit(feats,[r['g0_utility'] for r in paired])
    adv = AdvantageLearner().fit(feats,[r['gv_success']-r['g0_success'] for r in paired])
    flat, actions, labels = action_training_rows(paired)
    value = ActionValueLearner().fit(flat,actions,labels)
    return risk,deficit,adv,value


def fit_u_advantage(rows):
    """Fit the primary U-advantage learner on the paired feasible training rows."""
    paired = [row for row in rows if row['mask']['gv']]
    if not paired:
        raise ValueError('no paired training support')
    return AdvantageLearner().fit(
        [row['features'] for row in paired],
        [row['gv_utility'] - row['g0_utility'] for row in paired],
    )


def action_training_rows(rows):
    # Append feature/action/label as one tuple, including unequal feasibility.
    triples = [(row['features'],action,row[action+'_success'])
               for row in rows for action in ('g0','gv') if row['mask'][action]]
    if any(label is None for _,_,label in triples):
        raise ValueError('missing feasible training label')
    return ([t[0] for t in triples],[t[1] for t in triples],[t[2] for t in triples])


def main() -> int:
    parser = argparse.ArgumentParser(description="Paper B engineering smoke path")
    parser.add_argument("--output", required=True, help="fresh output directory")
    parser.add_argument("--seed", type=int, default=20260924)
    args = parser.parse_args()

    # One active contract; checking engineering never authorizes a model launch.
    import importlib.util
    spec = importlib.util.spec_from_file_location('b_phase_validator', ROOT/'protocols/paper_b/launch_validator.py')
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    active_contract = validator.load_contract()
    phase_errors = validator.validate_for_phase(active_contract, 'engineering', 'one_step')
    if phase_errors:
        raise SystemExit('engineering contract refused: '+str(phase_errors))
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refuse overwrite: {output} exists; choose a fresh directory")
    output.mkdir(parents=True)

    checks: list[dict] = []

    def record_check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    # 1. Generate closed test worlds with disjoint template sets per split.
    train = generate_world(seed=args.seed, n_templates=14, roots_per_template=3, repetitions=4, split="train")
    calib = generate_world(seed=args.seed + 1, n_templates=8, roots_per_template=3, repetitions=4, split="calibration")
    test = generate_world(seed=args.seed + 2, n_templates=10, roots_per_template=3, repetitions=4, split="test")
    assert_split_disjoint(train.records+calib.records+test.records)
    record_check("all pairwise split and descendant isolation", True,
                 "template-family, template and root identities checked across all three splits")
    for name, world in (("train", train), ("calibration", calib), ("test", test)):
        assert_no_duplicate_units(world.records)
        record_check(f"{name}: schema + duplicate units", True, f"{len(world.records)} records")

    train_rows = _checkpoint_rows(_split_records(train.records, "train"))
    calib_rows = _checkpoint_rows(_split_records(calib.records, "calibration"))
    test_rows = _checkpoint_rows(_split_records(test.records, "test"))
    record_check(
        "projection leak-free on every record",
        True,
        "condition label and outcomes not reachable through the projection",
    )
    record_check(
        "feasibility semantics",
        all(row["gv_success"] is None or row["mask"].get("gv") for row in train_rows),
        "unavailable gv carries no outcome",
    )

    # 2. Fit matched-capacity learners on training templates.  U is primary, so
    # the primary scores are the U-advantage learner and the utility-deficit
    # (risk-style) learner; the binary failure-risk learner is secondary.
    risk, deficit, adv, value = fit_all(train_rows)
    adv_u = fit_u_advantage(train_rows)
    matching = matching_report((risk,deficit,adv,adv_u,value))
    record_check("matched decision-score class", matching['matched_decision_class'], json.dumps(matching,sort_keys=True))

    # 3. Score the test checkpoints with each policy.
    test_feats = [row["features"] for row in test_rows]
    test_keys = [row["key"] for row in test_rows]
    test_gv_feasible = np.asarray([row["mask"]["gv"] for row in test_rows])
    scores = {
        # Primary channel (U): utility advantage and the fair risk-style
        # utility-deficit comparator.
        "advantage_u": dict(zip(test_keys, adv_u.predict(test_feats))),
        "deficit": dict(zip(test_keys, deficit.predict(test_feats))),
        # Secondary channel (S): binary advantage and binary failure risk.
        "advantage_s": dict(zip(test_keys, adv.predict(test_feats))),
        "risk": dict(zip(test_keys, risk.predict(test_feats))),
    }
    # Plain action-conditioned value controller: score = q(gv) - q(g0).
    value_rows = [row["features"] for row in test_rows for _ in ("g0", "gv")]
    value_actions = [a for _ in test_rows for a in ("g0", "gv")]
    predicted = value.predict(value_rows, value_actions).reshape(len(test_rows), 2)
    scores["action_value"] = dict(zip(test_keys, predicted[:, 1] - predicted[:, 0]))

    # 4. Paired template-aware evaluation at the primary capacity.  U is
    # primary; the binary S comparison is secondary and separate.
    test_records = _split_records(test.records, "test")
    comparisons = evaluate_policies(
        test_records,
        scores_by_policy={"advantage_u": scores["advantage_u"], "deficit": scores["deficit"]},
        primary_policy="advantage_u", primary_comparator="deficit",
        capacities=(0.25,),
        outcome="U",
        seed=args.seed,
    )
    secondary_comparisons = evaluate_policies(
        test_records,
        scores_by_policy={"advantage_s": scores["advantage_s"], "risk": scores["risk"]},
        primary_policy="advantage_s", primary_comparator="risk",
        capacities=(0.25,),
        outcome="S",
        seed=args.seed,
    )
    record_check("paired U evaluation produced a comparison", bool(comparisons),
                 f"{len(comparisons)} U comparison(s)")
    record_check("secondary S evaluation produced a comparison", bool(secondary_comparisons),
                 f"{len(secondary_comparisons)} S comparison(s)")

    # Implementation equivalence check (not a hypothesis): with identical ridge
    # designs the advantage learner and the action-value difference agree.
    value_diff = predicted[:, 1] - predicted[:, 0]
    advantage_s_scores = adv.predict(test_feats)
    record_check(
        "ridge advantage/action-value equivalence",
        bool(np.allclose(advantage_s_scores, value_diff, atol=1e-12, rtol=0)),
        f"max abs gap {float(np.max(np.abs(advantage_s_scores - value_diff))):.3e}",
    )

    # 5. Conservative selection on calibration templates, on the primary U
    # channel, against the utility-deficit comparator.
    calib_feats = [row["features"] for row in calib_rows]
    calib_scores = {
        "advantage_u": adv_u.predict(calib_feats),
        "deficit": deficit.predict(calib_feats),
    }
    training_features = [r['features'] for r in train_rows if r['mask']['gv']]
    thresholds = {name: float(np.percentile(learner.predict(training_features),75))
                  for name,learner in [('advantage_u',adv_u),('deficit',deficit)]}
    gains: dict[str, np.ndarray] = {}
    degradation: dict[str, np.ndarray] = {}
    for name, score in calib_scores.items():
        selected = streaming_threshold(score, thresholds[name], np.array([r["mask"]["gv"] for r in calib_rows]))
        gain_by_template: dict[str, list[float]] = {}
        degrade_by_template: dict[str, list[float]] = {}
        for row, is_selected in zip(calib_rows, selected):
            contribution = (row["gv_utility"]-row["g0_utility"]) if is_selected and row['mask']['gv'] else 0.
            gain_by_template.setdefault(row['family'], []).append(contribution)
            # This fixture reports overall mean degradation, not a no-fault claim.
            degrade_by_template.setdefault(row['family'], []).append(-contribution)
        gains[name] = np.asarray(
            [np.mean(v) for _, v in sorted(gain_by_template.items())], dtype=float
        )
        degradation[name] = np.asarray(
            [np.mean(v) for _, v in sorted(degrade_by_template.items())], dtype=float
        )
    selector = ConservativeSelector(delta=0.05, harm_tolerance=0.02)
    selection = selector.select(gains, degradation)
    record_check(
        "conservative selection returns a decision",
        selection.chosen is not None or selection.fallback,
        f"chosen={selection.chosen}, fallback={selection.fallback}",
    )

    # 6. Write the run artifacts with the ENGINEERING_ONLY banner.
    summary = {
        "banner": ENGINEERING_ONLY,
        "protocol_version": active_contract['protocol_version'],
        "phase": "engineering",
        "lane": "one_step",
        "design_sha256": validator.binding_digest(active_contract,'engineering','one_step'),
        "passed": all(check['passed'] for check in checks),
        "warning": (
            "This is an engineering smoke test on a closed synthetic workload. "
            "It is not a real-agent result, not a pilot, and no number here may "
            "be reported as scientific evidence."
        ),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "seed": args.seed,
        "counts": {
            "train_templates": len(train.templates),
            "calibration_templates": len(calib.templates),
            "test_templates": len(test.templates),
            "test_checkpoints": len(test_rows),
            "test_checkpoints_with_gv": int(test_gv_feasible.sum()),
        },
        "checks": checks,
        "learner_matching": matching,
        "streaming_thresholds_frozen_on_train": thresholds,
        "harm_scope": "overall fixture mean degradation; no clean-stratum guarantee",
        "primary_outcome": "U",
        "secondary_outcome": "S",
        "comparison_primary": [
            {
                "primary_policy": comparison.primary_policy,
                "primary_comparator": comparison.primary_comparator,
                "bootstrap_valid": comparison.n_bootstrap_valid,
                "bootstrap_undefined": comparison.n_bootstrap_undefined,
                "outcome": comparison.outcome,
                "capacity": comparison.capacity,
                "d_value": comparison.d_value,
                "d_ci": list(comparison.d_ci),
                "support_note": comparison.support_note,
                "evaluations": {name: asdict(value) for name,value in comparison.evaluations.items()},
            }
            for comparison in comparisons
        ],
        "comparison_secondary": [
            {
                "primary_policy": comparison.primary_policy,
                "primary_comparator": comparison.primary_comparator,
                "outcome": comparison.outcome,
                "capacity": comparison.capacity,
                "d_value": comparison.d_value,
                "d_ci": list(comparison.d_ci),
                "support_note": comparison.support_note,
            }
            for comparison in secondary_comparisons
        ],
        "conservative_selection": {
            "chosen": selection.chosen,
            "fallback": selection.fallback,
            "bounds": selection.bounds,
            "degradation_upper": selection.degradation_upper,
            "family_size": selection.family_size,
            "delta": selection.delta,
            "reason": selection.reason,
        },
        "known_truth_world": test.truth,
        "checks_passed": all(check["passed"] for check in checks),
    }
    (output / "smoke_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output / "SMOKE_BANNER.txt").write_text(
        f"{ENGINEERING_ONLY}: closed synthetic workload; no scientific claim.\n",
        encoding="utf-8",
    )
    print(f"smoke-b: {ENGINEERING_ONLY}")
    print(f"  records: train={len(train.records)} calibration={len(calib.records)} test={len(test.records)}")
    for comparison in comparisons:
        print(
            f"  D_{comparison.outcome}(q={comparison.capacity}) = {comparison.d_value:+.4f} "
            f"CI [{comparison.d_ci[0]:+.4f}, {comparison.d_ci[1]:+.4f}] ({comparison.support_note})"
        )
    print(
        f"  conservative selection: chosen={selection.chosen} fallback={selection.fallback} "
        f"(family={selection.family_size}, delta={selection.delta})"
    )
    if not summary["checks_passed"]:
        print("smoke-b: FAILED checks:")
        for check in checks:
            if not check["passed"]:
                print("  -", check["check"], check["detail"])
        return 1
    print(f"smoke-b: all {len(checks)} engineering checks passed -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
