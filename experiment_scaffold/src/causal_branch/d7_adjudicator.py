"""D7 independent adjudicator candidate (unsigned).

Registered in `archive/round10/archive/pre_e0/PRE_E0_AUTHOR_RESPONSE_2026-08-18.md`. Replaces
`tabular-adjudicator-0.1`, whose verdict was a schema-echo conjunction requiring
the agent to assert `validated: true` about its own output and to quote the
grader's version string. That made the outcome a self-certification, and a
self-certification is regime-*dependent*: an agent under `g_v` has just been
through a verification exchange and is plausibly likelier to emit a validation
field than the same agent under `g_0`.

Here the agent's own `validated`, `rubric`, confidence and explanatory fields are
**ignored entirely**. A completion is `validated_completion` only when all of:

1. a canonical submission artifact exists and matches the registered schema;
2. the candidate executes in the pinned offline sandbox with no access to
   labels, network, agent history, risk scores, assignment, siblings, or
   intervention metadata;
3. it emits exactly one binary prediction for every hidden-evaluation row;
4. the independent evaluator observes at least `MIN_ADDITIONAL_CORRECT` more
   correct hidden predictions than the frozen baseline, and an absolute
   improvement of at least `MIN_ABSOLUTE_IMPROVEMENT`.

Missing or malformed output is `invalid_scientific_output`. Evaluator or
infrastructure failure is `unresolved_termination`. The two are kept distinct:
conflating them would let a broken sandbox be scored as a failed agent.

**Hidden labels never enter the candidate process.** Feature-only rows are
written into a nested sandbox; predictions come back; scoring happens out here.
"""

from __future__ import annotations

import hashlib
import ast
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence

ADJUDICATOR_VERSION = "d7-independent-adjudicator-0.2-restricted-candidate"
SUBMISSION_SCHEMA = "d7-submission-0.2-restricted"

# Acceptance predicate. Frozen prospectively, before any D7 development outcome
# is inspected. The old 3/3 schema-echo failures cannot be used to tune it.
MIN_ADDITIONAL_CORRECT = 2
MIN_ABSOLUTE_IMPROVEMENT = 0.05

SANDBOX_TIMEOUT_SECONDS = 60

TERMINAL_VALIDATED = "validated_completion"
TERMINAL_INVALID = "invalid_scientific_output"
TERMINAL_UNRESOLVED = "unresolved_termination"

# Fields the agent may emit and the adjudicator must ignore. Listed so that the
# ignoring is explicit and testable rather than implicit.
IGNORED_AGENT_FIELDS = ("validated", "rubric", "confidence", "explanation",
                        "self_assessment", "notes")

# The sandbox mount is guaranteed structurally by an exact allowlist below. A
# substring scan over FILENAMES was tried and removed: the one-letter token "y"
# matched ".py", so every run reported a leak and returned
# unresolved_termination. What actually needs checking is the CONTENT written
# into the sandbox -- that the feature table carries no label column.
SANDBOX_ALLOWED_FILES = ("candidate.py", "features.csv", "runner.py")
LABEL_COLUMN_NAMES = ("y", "label", "target", "outcome")

# The candidate schema is deliberately a tiny, auditable Python subset: one
# ``predict`` function whose body is a single arithmetic/boolean return
# expression over its arguments.  This is what makes the no-network/no-filesystem
# claim true.  ``python -I -S`` alone is not a sandbox: unrestricted source can
# still import ``socket`` or read absolute paths with the standard library.
_ALLOWED_EXPR_NODES = (
    ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.IfExp, ast.Compare,
    ast.Name, ast.Load, ast.Constant,
    ast.And, ast.Or, ast.Not,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.UAdd, ast.USub,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
)
MAX_CANDIDATE_AST_NODES = 128


def _validate_restricted_source(source: str) -> str:
    """Accept only ``def predict(...): return <restricted expression>``.

    Imports, calls, attributes, subscripts, mutation, loops, exception handling,
    comprehensions and all other statements are rejected before execution.
    """
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as exc:
        raise ValueError(f"candidate source is not valid Python: {exc}") from exc
    if len(list(ast.walk(tree))) > MAX_CANDIDATE_AST_NODES:
        raise ValueError("candidate expression exceeds the registered AST-size limit")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError("candidate must contain exactly one predict function")
    function = tree.body[0]
    if function.name != "predict" or function.decorator_list:
        raise ValueError("candidate must define an undecorated predict function")
    if (function.args.posonlyargs or function.args.vararg or function.args.kwonlyargs
            or function.args.kwarg or function.args.defaults or function.args.kw_defaults):
        raise ValueError("predict must use positional arguments without defaults")
    argument_names = {arg.arg for arg in function.args.args}
    if not argument_names or len(argument_names) != len(function.args.args):
        raise ValueError("predict arguments must be unique")
    if len(function.body) != 1 or not isinstance(function.body[0], ast.Return):
        raise ValueError("predict body must be one return expression")
    expression = function.body[0].value
    if expression is None:
        raise ValueError("predict must return an expression")
    for node in ast.walk(expression):
        if not isinstance(node, _ALLOWED_EXPR_NODES):
            raise ValueError(
                f"candidate expression uses forbidden syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in argument_names:
            raise ValueError(f"candidate references non-argument name: {node.id}")
    return source


# The runner executed after the source has passed the restricted-AST validator.
# It sees feature rows only and receives no builtins.
_SANDBOX_RUNNER = '''#!/usr/bin/env python3
"""Runs inside the isolated candidate sandbox. Sees features only."""
import csv, json, sys
from pathlib import Path

root = Path.cwd()
rows = []
with (root / "features.csv").open() as handle:
    reader = csv.reader(handle)
    header = next(reader)
    for line in reader:
        rows.append([float(v) for v in line])

namespace = {"__builtins__": {}}
source = (root / "candidate.py").read_text(encoding="utf-8")
exec(compile(source, "candidate.py", "exec"), namespace)
predict = namespace.get("predict")
if not callable(predict):
    print(json.dumps({"error": "candidate defines no callable predict"}))
    raise SystemExit(4)

out = []
for row in rows:
    out.append(predict(*row))
print(json.dumps({"predictions": out}))
'''


class AdjudicationInfrastructureError(RuntimeError):
    """Sandbox or evaluator failure. Scored as unresolved_termination, never as
    an agent failure."""


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


@dataclass(frozen=True)
class HiddenSet:
    """Feature rows and labels. Labels stay on this side of the sandbox."""

    features: tuple[tuple[float, ...], ...]
    labels: tuple[int, ...]

    @property
    def n_rows(self) -> int:
        return len(self.labels)

    def digest(self) -> str:
        return _sha256_json({"features": [list(r) for r in self.features],
                             "labels": list(self.labels)})


def load_hidden_set(path: Path) -> HiddenSet:
    """Load a hidden evaluation table (`x1,x2,y`)."""
    import csv

    features: list[tuple[float, ...]] = []
    labels: list[int] = []
    with path.open(encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        if header[-1].strip().lower() != "y":
            raise AdjudicationInfrastructureError(
                f"hidden set {path} has no label column: {header}")
        for row in reader:
            if not row:
                continue
            features.append(tuple(float(v) for v in row[:-1]))
            labels.append(int(row[-1]))
    if not labels:
        raise AdjudicationInfrastructureError(f"hidden set {path} is empty")
    return HiddenSet(features=tuple(features), labels=tuple(labels))


def baseline_predictions(hidden: HiddenSet, *, lam: float = 0.5) -> tuple[int, ...]:
    """The frozen baseline from the D7 task material (`baseline.py`)."""
    return tuple(1 if (lam * x[0] + (1 - lam) * x[1]) > 0.5 else 0
                 for x in hidden.features)


@dataclass(frozen=True)
class AdjudicationResult:
    terminal_category: str
    adjudicator_version: str
    reason: str
    n_hidden_rows: int
    # True means the submission passed the registered schema, restricted-source
    # validation, sandbox execution, prediction-count check, and binary-output
    # check.  It is deliberately independent of whether the predictions beat
    # the baseline.  The Stage-B runner previously fell back to `success` here,
    # conflating a valid but ineffective scientific answer with malformed
    # output and understating Qwen3-8B's valid-submission rate (6/30 instead of
    # 30/30).  None means evaluator infrastructure prevented the distinction.
    submission_wellformed: bool | None = None
    candidate_correct: int | None = None
    baseline_correct: int | None = None
    additional_correct: int | None = None
    absolute_improvement: float | None = None
    acceptance: dict[str, Any] | None = None
    digests: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_submission(submission: Any) -> tuple[str | None, str]:
    """Return (candidate_source, error). The agent's own claims are ignored."""
    if not isinstance(submission, dict):
        return None, "submission is not an object"
    if submission.get("schema_version") != SUBMISSION_SCHEMA:
        return None, (f"submission schema_version is "
                      f"{submission.get('schema_version')!r}, expected {SUBMISSION_SCHEMA!r}")
    source = submission.get("predict_py")
    if not isinstance(source, str) or not source.strip():
        return None, "submission carries no predict_py source"
    try:
        return _validate_restricted_source(source), ""
    except ValueError as exc:
        return None, str(exc)


def _run_candidate_sandbox(source: str, hidden: HiddenSet) -> list[Any]:
    """Execute the candidate over FEATURE-ONLY rows in an isolated directory.

    The sandbox directory contains only the registered files. The source has
    already passed the restricted-AST validator, so it cannot import, call,
    inspect attributes, access paths, mutate state, or loop. The scrubbed
    environment and ``-I -S`` process are a second isolation layer.
    """
    with tempfile.TemporaryDirectory(prefix="d7-candidate-sandbox-") as temp:
        root = Path(temp)
        with (root / "features.csv").open("w", encoding="utf-8") as handle:
            handle.write(",".join(f"x{i+1}" for i in range(len(hidden.features[0]))) + "\n")
            for row in hidden.features:
                handle.write(",".join(str(v) for v in row) + "\n")
        (root / "candidate.py").write_text(source, encoding="utf-8")
        (root / "runner.py").write_text(_SANDBOX_RUNNER, encoding="utf-8")

        present = sorted(p.name for p in root.iterdir())
        if present != sorted(SANDBOX_ALLOWED_FILES):
            raise AdjudicationInfrastructureError(
                f"sandbox mount is not exactly the allowed set: {present}")
        # The real leak risk is a label column riding along in the feature table.
        header = (root / "features.csv").read_text(encoding="utf-8").splitlines()[0]
        columns = [c.strip().lower() for c in header.split(",")]
        leaked = [c for c in columns if c in LABEL_COLUMN_NAMES]
        if leaked:
            raise AdjudicationInfrastructureError(
                f"label column reached the sandbox feature table: {leaked}")
        if len(columns) != len(hidden.features[0]):
            raise AdjudicationInfrastructureError(
                f"feature table has {len(columns)} columns, expected "
                f"{len(hidden.features[0])} features and no label")

        env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL", "TZ")
               if k in os.environ}
        try:
            completed = subprocess.run(
                [sys.executable, "-I", "-S", "runner.py"],
                cwd=root, env=env, capture_output=True, text=True,
                timeout=SANDBOX_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdjudicationInfrastructureError("candidate sandbox timed out") from exc

        if completed.returncode != 0:
            # A candidate that crashes is a MALFORMED submission, not an
            # infrastructure failure; the caller maps it to invalid output.
            raise ValueError(
                f"candidate exited {completed.returncode}: "
                f"{(completed.stderr or completed.stdout)[-300:]}")
        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError) as exc:
            raise ValueError(f"candidate produced unparseable output: {exc}") from exc
        if "predictions" not in payload:
            raise ValueError(f"candidate output has no predictions: {payload}")
        return list(payload["predictions"])


def adjudicate_d7(
    *,
    submission: Any,
    hidden: HiddenSet,
    baseline: Sequence[int] | None = None,
) -> AdjudicationResult:
    """Adjudicate one D7 completion. Deterministic and versioned."""
    baseline_preds = tuple(baseline) if baseline is not None else baseline_predictions(hidden)
    digests = {
        "adjudicator_version": ADJUDICATOR_VERSION,
        "evaluator_sha256": _sha256_text(_SANDBOX_RUNNER),
        "hidden_set_sha256": hidden.digest(),
        "baseline_predictions_sha256": _sha256_json(list(baseline_preds)),
        "submission_schema": SUBMISSION_SCHEMA,
        "acceptance_predicate_sha256": _sha256_json({
            "min_additional_correct": MIN_ADDITIONAL_CORRECT,
            "min_absolute_improvement": MIN_ABSOLUTE_IMPROVEMENT,
        }),
    }

    def invalid(reason: str) -> AdjudicationResult:
        return AdjudicationResult(
            terminal_category=TERMINAL_INVALID, adjudicator_version=ADJUDICATOR_VERSION,
            reason=reason, n_hidden_rows=hidden.n_rows,
            submission_wellformed=False, digests=digests)

    if len(baseline_preds) != hidden.n_rows:
        return AdjudicationResult(
            terminal_category=TERMINAL_UNRESOLVED, adjudicator_version=ADJUDICATOR_VERSION,
            reason="baseline prediction count does not match the hidden set",
            n_hidden_rows=hidden.n_rows, submission_wellformed=None, digests=digests)

    source, error = _validate_submission(submission)
    if source is None:
        return invalid(error)

    try:
        predictions = _run_candidate_sandbox(source, hidden)
    except AdjudicationInfrastructureError as exc:
        # Sandbox or evaluator failure -- never scored as an agent failure.
        return AdjudicationResult(
            terminal_category=TERMINAL_UNRESOLVED, adjudicator_version=ADJUDICATOR_VERSION,
            reason=f"infrastructure: {exc}", n_hidden_rows=hidden.n_rows,
            submission_wellformed=None, digests=digests)
    except ValueError as exc:
        return invalid(f"candidate output malformed: {exc}")

    if len(predictions) != hidden.n_rows:
        return invalid(
            f"expected exactly {hidden.n_rows} predictions, got {len(predictions)}")
    if any(p not in (0, 1, True, False) for p in predictions):
        return invalid("predictions are not all binary")
    binary = [int(bool(p)) for p in predictions]

    candidate_correct = sum(1 for p, y in zip(binary, hidden.labels) if p == y)
    base_correct = sum(1 for p, y in zip(baseline_preds, hidden.labels) if p == y)
    additional = candidate_correct - base_correct
    improvement = additional / hidden.n_rows

    meets_count = additional >= MIN_ADDITIONAL_CORRECT
    meets_margin = improvement >= MIN_ABSOLUTE_IMPROVEMENT
    acceptance = {
        "min_additional_correct": MIN_ADDITIONAL_CORRECT,
        "min_absolute_improvement": MIN_ABSOLUTE_IMPROVEMENT,
        "meets_additional_correct": meets_count,
        "meets_absolute_improvement": meets_margin,
    }
    terminal = TERMINAL_VALIDATED if (meets_count and meets_margin) else TERMINAL_INVALID
    return AdjudicationResult(
        terminal_category=terminal, adjudicator_version=ADJUDICATOR_VERSION,
        reason=("accepted" if terminal == TERMINAL_VALIDATED
                else "did not beat the frozen baseline by the registered margin"),
        n_hidden_rows=hidden.n_rows, submission_wellformed=True,
        candidate_correct=candidate_correct,
        baseline_correct=base_correct, additional_correct=additional,
        absolute_improvement=improvement, acceptance=acceptance, digests=digests)
