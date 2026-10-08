"""Closed synthetic world for the Paper B engineering smoke path.

This world exists to exercise the branch schema, the learners, the allocator
and the evaluator end to end.  It is a *test workload*: the outcome law is
known to the generator, the condition labels are evaluator-only, and every
artifact produced from it is marked ``ENGINEERING_ONLY``.  It is not a
scientific simulation of an agent, it is not a pilot, and no number derived
from it may be reported as a result.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

from causal_branch.control.schema import BranchRecord

ENGINEERING_ONLY = "ENGINEERING_ONLY"


@dataclass
class SyntheticWorld:
    """A generated, closed test world."""

    seed: int
    n_templates: int
    roots_per_template: int
    repetitions: int
    templates: list[str] = field(default_factory=list)
    records: list[BranchRecord] = field(default_factory=list)
    #: Evaluator-only truth, never exposed through the feature projection.
    truth: dict[str, float] = field(default_factory=dict)
    banner: str = ENGINEERING_ONLY

    def config_hash(self) -> str:
        payload = json.dumps(
            {
                "seed": self.seed,
                "n_templates": self.n_templates,
                "roots_per_template": self.roots_per_template,
                "repetitions": self.repetitions,
                "banner": self.banner,
            },
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_world(
    *,
    seed: int = 20260924,
    n_templates: int = 12,
    roots_per_template: int = 3,
    repetitions: int = 2,
    split: str = "train",
) -> SyntheticWorld:
    """Generate a tiny closed world with a known continue/verify law.

    Design (all parameters are smoke-test values, not study values):

    - one pre-treatment feature ``z`` in [0,1] plus a binary feasibility flag
      for verification;
    - baseline success probability rises with ``z``;
    - verification helps more where ``z`` is small, and *hurts* on a subset of
      checkpoints where the baseline would have succeeded (harm);
    - a latent evaluator-only condition label marks the hurt subset.
    """

    rng = np.random.default_rng(seed)
    world = SyntheticWorld(
        seed=seed,
        n_templates=n_templates,
        roots_per_template=roots_per_template,
        repetitions=repetitions,
    )
    for t in range(n_templates):
        template_id = f"{split}-tmpl-{t:03d}"
        world.templates.append(template_id)
        for r in range(roots_per_template):
            root_id = f"{template_id}/root-{r:02d}"
            checkpoint_id = f"{root_id}/ckpt-01"
            z = float(rng.uniform(0.0, 1.0))
            # Verification is available on ~70% of checkpoints.
            feasible = bool(rng.uniform() < 0.70)
            # Evaluator-only condition: 1 = the "hurt" regime (verify can harm).
            hurt = int(rng.uniform() < 0.35)
            p0 = 0.15 + 0.70 * z
            # Verification advantage: helps low-z checkpoints, hurts hurt ones.
            p_v = np.clip(p0 + 0.20 * (0.5 - z) - 0.35 * hurt, 0.02, 0.98)
            for action, p in (("g0", p0), ("gv", float(p_v))):
                if action == "gv" and not feasible:
                    world.records.append(
                        BranchRecord(
                            study="B1_pilot",
                            protocol_hash="smoke",
                            run_id=f"smoke-{seed}",
                            template_id=template_id,
                            template_family_id=template_id,
                            root_id=root_id,
                            checkpoint_id=checkpoint_id,
                            checkpoint_rule_version="smoke-rule-1",
                            split=split,
                            condition_label=f"hurt={hurt}",
                            runtime_manifest_hash="smoke-runtime",
                            snapshot_hash="smoke-snapshot",
                            history_hash="smoke-history",
                            feature_registry_version="b_features_v1",
                            pre_treatment_features={"z": z},
                            pre_treatment_mask={"g0": True, "gv": False},
                            availability_evidence_hash="smoke-availability",
                            action_id="gv",
                            action_version="gv-v1",
                            continuation_version="rho-v1",
                            repetition_id=0,
                            seed_coupling_id="smoke-seed",
                            branch_order=1,
                            execution_status="unavailable",
                            failure_reason="verifier_input_absent",
                            adjudicator_version="adj-v1",
                        )
                    )
                    continue
                for rep in range(repetitions):
                    success = int(rng.uniform() < p)
                    # Utility: success 1.0; invalid or no candidate is exactly 0;
                    # ordinary failure is 0.  Invalidity keeps its reason.
                    invalid = int((not success) and rng.uniform() < 0.25)
                    utility = 1.0 if success else 0.0
                    invalid_reason = "no_valid_candidate" if invalid else None
                    world.records.append(
                        BranchRecord(
                            study="B1_pilot",
                            protocol_hash="smoke",
                            run_id=f"smoke-{seed}",
                            template_id=template_id,
                            template_family_id=template_id,
                            root_id=root_id,
                            checkpoint_id=checkpoint_id,
                            checkpoint_rule_version="smoke-rule-1",
                            split=split,
                            condition_label=f"hurt={hurt}",
                            runtime_manifest_hash="smoke-runtime",
                            snapshot_hash="smoke-snapshot",
                            history_hash="smoke-history",
                            feature_registry_version="b_features_v1",
                            pre_treatment_features={"z": z},
                            pre_treatment_mask={"g0": True, "gv": feasible},
                            availability_evidence_hash="smoke-availability",
                            action_id=action,
                            action_version=f"{action}-v1",
                            continuation_version="rho-v1",
                            repetition_id=rep,
                            seed_coupling_id="smoke-seed",
                            branch_order=0 if action == "g0" else 1,
                            outcome_success=success,
                            outcome_utility=utility,
                            outcome_invalid=invalid,
                            invalid_reason=invalid_reason,
                            cost_vector={"verifier_calls": 1.0 if action == "gv" else 0.0},
                            execution_status="completed",
                            adjudicator_version="adj-v1",
                            artifact_hashes=(f"art-{root_id}-{action}-{rep}",),
                        )
                    )
    # Known-truth summaries (evaluator-only).
    by_action: dict[str, list[float]] = {"g0": [], "gv": []}
    for record in world.records:
        if record.outcome_success is not None:
            by_action[record.action_id].append(float(record.outcome_success))
    world.truth = {
        "mean_success_g0": float(np.mean(by_action["g0"])) if by_action["g0"] else float("nan"),
        "mean_success_gv": float(np.mean(by_action["gv"])) if by_action["gv"] else float("nan"),
    }
    return world
