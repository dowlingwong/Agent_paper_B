"""Round 4 (2 x L40) qualification gates that must not live inside a script.

Everything here is pure: it consumes recorded numbers and returns reasons.  It
is kept out of ``scripts/wp3_model_qualification.py`` so that each gate can be
tested directly, and so that there is exactly ONE implementation of each rule
rather than a registry-driven path and a hard-coded fallback that disagree.

Nothing in this module starts a server, downloads an artifact, generates a pool,
or issues a model request.
"""

from __future__ import annotations

import csv
from pathlib import Path

import math
from typing import Any, Mapping, Sequence

# --------------------------------------------------------------------------
# Round 4 frozen shape
# --------------------------------------------------------------------------

ROUND4_POOL = "model_selection_round4_l40"
ROUND4_WORKERS = 2
ROUND4_QUALIFICATION_ROOTS = 1000
ROUND4_TEMPLATES = 200
ROUND4_ROOTS_PER_TEMPLATE = 5
ROUND4_SMOKE_ROOTS = 4
ROUND4_MINIMUM_VISIBLE_GPUS = 2
ROUND4_OVERLAP_CONTROL = "qwen3-8b"

# Artifacts from the completed rounds. A Round 4 verdict that consumed one of
# these is not a Round 4 verdict.
SUPERSEDED_POOLS = (
    "model_selection",
    "model_selection_round2",
    "model_selection_round3",
)
SUPERSEDED_ARTIFACT_MARKERS = (
    "split_manifest_v2_candidate",
    "d7_task_registry_v2_candidate",
    "model_candidate_round2",
    "model_selection_round2_manifest_candidate",
    "model_selection_round3_manifest_candidate",
    "d7_task_registry_round2_candidate",
    "d7_task_registry_round3_candidate",
)


class Round4GuardFailure(RuntimeError):
    """A Round 4 execution guard refused to run."""


class InstrumentInfeasible(RuntimeError):
    """The pool's ideal-solver yield puts the instrument outside its window."""


# --------------------------------------------------------------------------
# B6 -- criterion 4 is relative to the pool's own ideal-solver yield
# --------------------------------------------------------------------------

IDEAL_YIELD_WINDOW = (0.35, 0.70)
CANDIDATE_YIELD_FRACTION = 0.75
YIELD_CEILING = 0.70


def criterion_4_bounds(ideal_solver_yield: float) -> dict[str, float]:
    """Derive the candidate yield window from the pool's ideal-solver yield.

    A fixed ``[0.30, 0.70]`` window silently conflates two different findings.
    A candidate scoring ``0.31`` on a pool an ideal solver clears at ``0.95``
    is a weak candidate; the same ``0.31`` on a pool an ideal solver clears at
    ``0.36`` is a hard pool.  The floor therefore tracks the instrument.

    Raises ``InstrumentInfeasible`` when the ideal yield itself falls outside
    ``[0.35, 0.70]``.  That is an instrument nonverdict: it is NOT a licence to
    regenerate the pool, because regenerating after seeing feasibility is
    exactly the outcome-driven move the protocol forbids.
    """
    ideal = float(ideal_solver_yield)
    if not math.isfinite(ideal):
        raise InstrumentInfeasible("ideal_solver_yield is not a finite number")
    low, high = IDEAL_YIELD_WINDOW
    if not low <= ideal <= high:
        raise InstrumentInfeasible(
            f"ideal_solver_yield {ideal:.4f} is outside [{low:.2f}, {high:.2f}]; "
            "D7 model-selection verdicts are withheld as instrument-infeasible "
            "and the pool is NOT regenerated"
        )
    lower = CANDIDATE_YIELD_FRACTION * ideal
    return {
        "ideal_solver_yield": ideal,
        "minimum_candidate_yield": lower,
        "maximum_candidate_yield": YIELD_CEILING,
        "candidate_yield_fraction_of_ideal": CANDIDATE_YIELD_FRACTION,
    }


def evaluate_criterion_4(
    observed_yield: float, *, ideal_solver_yield: float
) -> dict[str, Any]:
    """Criterion 4 verdict with every input it depended on recorded beside it."""
    bounds = criterion_4_bounds(ideal_solver_yield)
    observed = float(observed_yield)
    passed = bounds["minimum_candidate_yield"] <= observed <= bounds["maximum_candidate_yield"]
    return {
        "passed": passed,
        "observed_baseline_yield": observed,
        **bounds,
        "reason": None if passed else (
            f"criterion_4_baseline_yield_{observed:.4f}_outside_"
            f"[{bounds['minimum_candidate_yield']:.4f},"
            f"{bounds['maximum_candidate_yield']:.4f}]_"
            f"ideal_{bounds['ideal_solver_yield']:.4f}"
        ),
    }


# --------------------------------------------------------------------------
# B3 -- trajectory depth over every attempted root
# --------------------------------------------------------------------------

def summarize_trajectory_depth(roots: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Depth over ALL attempted roots, with the sub-populations beside it.

    Restricting the depth statistic to normally completed roots removes exactly
    the shallow roots -- errors and timeouts -- that make a candidate's median
    depth low, so a candidate that fails often looks deeper than it is.  Only
    the all-root median controls eligibility; the other two are diagnostics.
    """
    def _turns(root: Mapping[str, Any]) -> int:
        return int(root.get("turns") or 0)

    def _errored(root: Mapping[str, Any]) -> bool:
        return bool(root.get("error")) or bool(root.get("rail_bound"))

    every = [_turns(root) for root in roots]
    completed = [_turns(root) for root in roots if not _errored(root)]
    failed = [_turns(root) for root in roots if _errored(root)]
    return {
        "median_depth_all_attempted_roots": _median(every),
        "n_all_attempted_roots": len(every),
        "median_depth_normally_completed_DIAGNOSTIC_ONLY": _median(completed),
        "n_normally_completed": len(completed),
        "median_depth_errored_or_timed_out_DIAGNOSTIC_ONLY": _median(failed),
        "n_errored_or_timed_out": len(failed),
        "eligibility_statistic": "median_depth_all_attempted_roots",
    }


def _median(values: Sequence[int]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


# --------------------------------------------------------------------------
# M1 -- censoring
# --------------------------------------------------------------------------

def classify_censoring(
    roots: Sequence[Mapping[str, Any]], *, rail_seconds: float
) -> dict[str, Any]:
    """Separate censored roots from completions of the same wall time.

    A root stopped at the rail did not take ``rail_seconds``; it took at least
    ``rail_seconds``.  Treating it as an ordinary completion of that duration
    makes the schedule model treat a lower bound as a measurement, which
    understates the true makespan.  Any censored root makes the candidate's
    throughput unusable for selection, and criterion 6 already makes the
    candidate ineligible.
    """
    censored = [
        root for root in roots
        if bool(root.get("rail_bound"))
        or float(root.get("wall_seconds") or 0.0) >= float(rail_seconds)
    ]
    return {
        "rail_seconds": float(rail_seconds),
        "censored_root_count": len(censored),
        "censored_root_ids": [str(root.get("root_id")) for root in censored],
        "rail_bound_root_count": sum(1 for root in roots if root.get("rail_bound")),
        "throughput_censored": bool(censored),
        "throughput_interpretation": (
            "modelled uncensored throughput; censored roots contribute a LOWER "
            "BOUND on their duration, so this is a DIAGNOSTIC upper bound on "
            "throughput and must not enter selection"
            if censored else
            "no censored roots; throughput is a measurement"
        ),
    }


# --------------------------------------------------------------------------
# The one-shot generation record -- verified by CONTENT, not by existence
# --------------------------------------------------------------------------

ROUND4_GENERATION_RECORD_KIND = "round4_l40_pool_generation_record"
ROUND4_INDEX_START = 1200
ROUND4_INDEX_END = 1399
ROUND4_CONFIRMATORY_RESERVED_INDEX_START = 2000
ROUND4_SEED_BASE = 20260816


# The registered ideal-solver procedure, in one place.
#
# It must live in the library rather than in a command-line argument. When the
# ideal yield was passed in as `--ideal-solver-yield`, a human number decided
# criterion 4's floor for every candidate in the comparison, and nothing in the
# artifact could distinguish a measured value from a convenient one. Measuring it
# here, from the pool that was actually generated, removes that possibility
# entirely: there is no channel through which an operator-supplied yield can
# reach a verdict.
IDEAL_SOLVER_GRID = tuple(i / 20.0 for i in range(21))
IDEAL_SOLVER_BASELINE_LAMBDA = 0.5


def _read_d7_table(path: Path) -> list[tuple[tuple[float, float], int]]:
    with path.open(encoding="utf-8") as handle:
        rows = list(csv.reader(handle))[1:]
    return [((float(r[0]), float(r[1])), int(r[2])) for r in rows]


def _correct(rows: Sequence[tuple[tuple[float, float], int]], lam: float) -> int:
    """Integer count of correct predictions, exactly as the adjudicator counts.

    Deriving this from a float accuracy ratio introduces a rounding step the
    adjudicator does not have, and float equality between accuracy ratios has
    previously mis-selected the tied lambda and moved a measured yield by several
    points.
    """
    return sum(1 for (x1, x2), y in rows
               if (1 if (lam * x1 + (1 - lam) * x2) > 0.5 else 0) == y)


def measure_ideal_solver_yield(
    registry: Mapping[str, Any],
    *,
    min_additional_correct: int,
    min_absolute_improvement: float,
) -> dict[str, Any]:
    """Measure the ideal-solver yield of a generated pool. No model is called.

    Replays exactly what the registered `fit_candidate` returns: the best lambda
    on the template's own `dev.csv`, with ties going to the largest lambda
    because `fit_candidate` sorts `(accuracy, lambda)` descending and takes the
    first. The submitted rule is then scored on the hidden table under the
    registered adjudication margin.

    This is a task-instrument diagnostic. It is not a candidate result and is not
    comparable to any candidate's measured yield.
    """
    dataset_root = Path(str(registry["dataset_root"]))
    templates = sorted(
        str(row["template_id"]) for row in (registry.get("tasks") or [])
        if row.get("template_id") is not None
    )
    if not templates:
        raise InstrumentInfeasible("registry declares no templates to measure")

    beats = 0
    per_template: list[dict[str, Any]] = []
    for template in templates:
        dev = _read_d7_table(dataset_root / template / "dev.csv")
        hidden = _read_d7_table(dataset_root / "_hidden" / template / "eval.csv")
        n_eval = len(hidden)
        if not dev or not n_eval:
            raise InstrumentInfeasible(
                f"template {template} has an empty dev or hidden table")
        baseline = _correct(hidden, IDEAL_SOLVER_BASELINE_LAMBDA)
        best_dev = max(_correct(dev, lam) for lam in IDEAL_SOLVER_GRID)
        lam = max(lam for lam in IDEAL_SOLVER_GRID
                  if _correct(dev, lam) == best_dev)
        additional = _correct(hidden, lam) - baseline
        ok = (additional >= min_additional_correct
              and additional / n_eval >= min_absolute_improvement)
        beats += ok
        per_template.append({
            "template_id": template, "registered_lambda": lam,
            "additional_correct": additional, "beats_baseline": bool(ok),
            "n_eval": n_eval,
        })

    return {
        "ideal_solver_yield": beats / len(templates),
        "templates_measured": len(templates),
        "templates_beating_baseline": beats,
        "margin": {"min_additional_correct": min_additional_correct,
                   "min_absolute_improvement": min_absolute_improvement},
        "procedure": ("registered fit_candidate: 21-point lambda grid on dev.csv, "
                      "ties to the largest lambda; scored on the hidden table "
                      "under the registered adjudication margin"),
        "model_calls": 0,
        "is_candidate_result": False,
        "per_template": per_template,
    }


def validate_generation_record(
    record: Mapping[str, Any] | None,
    *,
    manifest_sha256: str | None,
    d7_registry_sha256: str | None,
) -> list[str]:
    """Every way a generation record can fail to prove what it claims.

    Checking only that the file EXISTS proves nothing: an empty file, a copy of
    the Round 3 record, or a record written after the manifest was rebuilt all
    satisfy ``is_file()``.  The record is the one-shot proof, so it has to be
    read.  In particular the recorded manifest digest must equal the digest of
    the manifest actually on disk -- otherwise the pool was regenerated or
    hand-edited after the record was written, and the one-shot guarantee is
    already broken.
    """
    if record is None:
        return ["generation_record_absent_or_unreadable"]
    if not isinstance(record, Mapping):
        return ["generation_record_is_not_an_object"]

    blockers: list[str] = []

    if record.get("artifact_kind") != ROUND4_GENERATION_RECORD_KIND:
        blockers.append(
            f"generation_record_wrong_kind:{record.get('artifact_kind')}"
        )
    if record.get("one_shot") is not True:
        blockers.append("generation_record_does_not_declare_one_shot")
    if record.get("regeneration") != "prohibited":
        blockers.append("generation_record_does_not_prohibit_regeneration")
    if not record.get("generated_at_utc"):
        blockers.append("generation_record_has_no_generation_timestamp")

    if record.get("pool") != ROUND4_POOL:
        blockers.append(f"generation_record_wrong_pool:{record.get('pool')}")

    recorded_manifest = record.get("manifest_sha256")
    if not recorded_manifest:
        blockers.append("generation_record_does_not_bind_the_manifest_hash")
    elif manifest_sha256 is None:
        blockers.append("split_manifest_unreadable_for_generation_record_check")
    elif recorded_manifest != manifest_sha256:
        # Regenerated, or edited by hand. Both break the one-shot guarantee.
        blockers.append("manifest_does_not_match_one_shot_generation_record")

    recorded_registry = record.get("d7_registry_sha256")
    if not recorded_registry:
        blockers.append("generation_record_does_not_bind_the_d7_registry_hash")
    elif d7_registry_sha256 is None:
        blockers.append("d7_registry_unreadable_for_generation_record_check")
    elif recorded_registry != d7_registry_sha256:
        blockers.append("d7_registry_does_not_match_one_shot_generation_record")

    index_range = record.get("template_index_range")
    if (not isinstance(index_range, Sequence) or isinstance(index_range, (str, bytes))
            or len(index_range) != 2):
        blockers.append("generation_record_has_no_template_index_range")
    else:
        low, high = int(index_range[0]), int(index_range[1])
        if low != ROUND4_INDEX_START or high != ROUND4_INDEX_END:
            blockers.append(
                f"generation_record_index_range_not_{ROUND4_INDEX_START}"
                f"_{ROUND4_INDEX_END}:{low}-{high}"
            )
        if high >= ROUND4_CONFIRMATORY_RESERVED_INDEX_START:
            blockers.append("generation_record_uses_confirmatory_reserved_indices")

    if int(record.get("templates") or 0) != ROUND4_TEMPLATES:
        blockers.append(
            f"generation_record_templates_not_{ROUND4_TEMPLATES}:{record.get('templates')}"
        )
    if int(record.get("roots") or 0) != ROUND4_QUALIFICATION_ROOTS:
        blockers.append(
            f"generation_record_roots_not_{ROUND4_QUALIFICATION_ROOTS}:{record.get('roots')}"
        )
    if int(record.get("roots_per_template") or 0) != ROUND4_ROOTS_PER_TEMPLATE:
        blockers.append(
            f"generation_record_roots_per_template_not_{ROUND4_ROOTS_PER_TEMPLATE}"
        )

    # The frozen ideal-solver yield lives in the record, not on a command line,
    # so a later invocation cannot quietly pass a different one.
    if "ideal_solver_yield" not in record:
        blockers.append("generation_record_does_not_record_the_frozen_ideal_yield")
    else:
        try:
            criterion_4_bounds(float(record["ideal_solver_yield"]))
        except InstrumentInfeasible as exc:
            blockers.append(f"generation_record_ideal_yield_infeasible:{exc}")
        except (TypeError, ValueError):
            blockers.append("generation_record_ideal_yield_is_not_a_number")

    return sorted(set(blockers))


def frozen_ideal_yield(record: Mapping[str, Any]) -> float:
    """The single authoritative ideal yield, read from the one-shot record."""
    return float(record["ideal_solver_yield"])


# --------------------------------------------------------------------------
# B5 -- explicit Round 4 execution guards
# --------------------------------------------------------------------------

def check_round4_execution(
    *,
    pool: str,
    mode: str,
    workers: int,
    registry_workers: int | None,
    registry_pool: str | None,
    qualification_roots: int,
    templates: int,
    roots_per_template: int,
    visible_logical_gpus: int,
    generation_record_present: bool,
    candidate_requested: Sequence[str],
    registry_candidates: Sequence[str],
    hash_checks: Mapping[str, tuple[str | None, str | None]],
    referenced_paths: Sequence[str] = (),
) -> list[str]:
    """Every reason this invocation must not produce a Round 4 verdict.

    ``hash_checks`` maps a label to ``(expected, actual)``.  A missing expected
    value is a blocker, not a pass: an unbound artifact is exactly what the
    guard exists to catch.
    """
    blockers: list[str] = []

    if str(pool) != ROUND4_POOL:
        blockers.append(f"pool_not_round4:{pool}")
    if registry_pool is not None and str(registry_pool) != str(pool):
        blockers.append(f"registry_requires_pool:{registry_pool}")
    if str(mode) not in {"smoke", "qualification"}:
        blockers.append(f"mode_not_explicit:{mode}")

    frozen_workers = ROUND4_WORKERS if registry_workers is None else int(registry_workers)
    if registry_workers is None:
        blockers.append("registry_does_not_freeze_worker_count")
    elif int(registry_workers) != ROUND4_WORKERS:
        blockers.append(f"registry_worker_count_not_two:{registry_workers}")
    if int(workers) != frozen_workers:
        blockers.append(f"workers_not_frozen_{frozen_workers}:{workers}")

    if int(visible_logical_gpus) < ROUND4_MINIMUM_VISIBLE_GPUS:
        blockers.append(f"fewer_than_two_visible_gpus:{visible_logical_gpus}")

    if str(mode) == "qualification":
        if int(qualification_roots) != ROUND4_QUALIFICATION_ROOTS:
            blockers.append(
                f"qualification_roots_not_{ROUND4_QUALIFICATION_ROOTS}:{qualification_roots}"
            )
        if int(templates) != ROUND4_TEMPLATES or int(roots_per_template) != ROUND4_ROOTS_PER_TEMPLATE:
            blockers.append(
                f"pool_shape_not_{ROUND4_TEMPLATES}x{ROUND4_ROOTS_PER_TEMPLATE}:"
                f"{templates}x{roots_per_template}"
            )
        if not generation_record_present:
            blockers.append("one_shot_generation_record_absent")

    for label, (expected, actual) in sorted(hash_checks.items()):
        if not expected:
            blockers.append(f"{label}_hash_unbound")
        elif expected != actual:
            blockers.append(f"{label}_hash_mismatch")

    requested = [str(name) for name in candidate_requested]
    if len(requested) != 1:
        blockers.append(f"exactly_one_candidate_required:{len(requested)}")
    unknown = sorted(set(requested) - set(str(n) for n in registry_candidates))
    if unknown:
        blockers.append(f"candidate_not_in_round4_registry:{','.join(unknown)}")

    for path in referenced_paths:
        text = str(path)
        for marker in SUPERSEDED_ARTIFACT_MARKERS:
            if marker in text:
                blockers.append(f"superseded_round2_or_round3_artifact:{marker}")
    if str(pool) in SUPERSEDED_POOLS:
        blockers.append(f"superseded_pool:{pool}")

    return sorted(set(blockers))


def round4_gpu_environment(workers: int = ROUND4_WORKERS) -> dict[str, str]:
    """The device binding Round 4 sets explicitly rather than inheriting.

    Leaving ``CUDA_VISIBLE_DEVICES`` unset makes worker-to-GPU binding depend on
    whatever the shell happened to export, which silently changes which physical
    device a candidate was measured on.
    """
    if int(workers) != ROUND4_WORKERS:
        raise Round4GuardFailure("Round 4 is frozen at two workers")
    return {"CUDA_VISIBLE_DEVICES": ",".join(str(i) for i in range(ROUND4_WORKERS))}


# --------------------------------------------------------------------------
# H4 -- GGUF conversion risk for the large multimodal-lineage candidates
# --------------------------------------------------------------------------

def gguf_conversion_blockers(
    *,
    candidate: str,
    filename: str,
    metadata: Mapping[str, Any],
    expected_architecture: str,
    expected_block_count: int | None,
    metadata_preserved: bool,
) -> list[str]:
    """Refuse a projector, a wrong architecture, or an unverifiable depth.

    A vision-language base such as Qwen3.5-27B is published with an ``mmproj``
    companion, and a conversion that folds or drops layers produces a file that
    loads, answers, and is not the model the registry names.  The expected block
    count comes from the IMMUTABLE base config at the pinned revision, never
    from the converted file describing itself.
    """
    blockers: list[str] = []
    lowered = str(filename).lower()
    if "mmproj" in lowered or "vision" in lowered:
        blockers.append("multimodal_projector_artifact_rejected")
    if metadata.get("vision_projector") or metadata.get("has_vision_encoder"):
        blockers.append("gguf_declares_a_vision_projector")
    if not metadata.get("text_only", False):
        blockers.append("gguf_is_not_marked_text_only")
    architecture = str(metadata.get("general.architecture") or metadata.get("architecture") or "")
    if not architecture:
        blockers.append("gguf_architecture_absent")
    elif architecture != str(expected_architecture):
        blockers.append(
            f"gguf_architecture_mismatch:{architecture}!={expected_architecture}"
        )
    if expected_block_count is None:
        blockers.append("expected_block_count_unbound_from_immutable_base_config")
    else:
        actual = metadata.get("block_count")
        if actual is None:
            blockers.append("gguf_block_count_absent")
        elif int(actual) != int(expected_block_count):
            blockers.append(
                f"gguf_block_count_mismatch:{actual}!={expected_block_count}"
            )
    if not metadata_preserved:
        blockers.append("inspected_gguf_metadata_not_preserved_before_execution")
    return [f"{candidate}:{reason}" for reason in blockers]


# --------------------------------------------------------------------------
# H5 -- fixed non-D7 reference canary
# --------------------------------------------------------------------------

CANARY_DRIFT_WARNING_FRACTION = 0.10


def assess_canary_drift(
    observations: Sequence[Mapping[str, Any]],
    *,
    warning_fraction: float = CANARY_DRIFT_WARNING_FRACTION,
) -> dict[str, Any]:
    """Compare fixed-canary decode rates against the first observation.

    The canary is the SAME Qwen3-8B artifact answering the same short non-D7
    prompts, with no adjudication and no submission, so running it costs no
    scientific root and consumes no pool.  It is a diagnostic: it can invalidate
    a throughput comparison, and it can never repair one or change a verdict.
    Replaying the first 40 verdict-bearing roots would have served the same
    purpose only by violating the no-retry rule.
    """
    rates = [float(row["decode_tokens_per_second"]) for row in observations]
    if len(rates) < 2:
        return {
            "observations": len(rates),
            "drift_warning": False,
            "insufficient_observations": True,
            "warning_fraction": float(warning_fraction),
        }
    reference = rates[0]
    if reference <= 0:
        raise ValueError("reference canary decode rate must be positive")
    deviations = [abs(rate - reference) / reference for rate in rates]
    worst = max(deviations)
    return {
        "observations": len(rates),
        "reference_decode_tokens_per_second": reference,
        "decode_tokens_per_second": rates,
        "relative_deviations": deviations,
        "maximum_relative_deviation": worst,
        "warning_fraction": float(warning_fraction),
        "drift_warning": worst > float(warning_fraction),
        "diagnostic_only": True,
        "on_warning": (
            "withhold throughput-based selection and return "
            "ROUND4_L40_INSTRUMENT_OR_INFRASTRUCTURE_BLOCKED_NONVERDICT"
        ),
    }
