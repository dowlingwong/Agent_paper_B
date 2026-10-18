from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from ..types import (
    BranchContext,
    CostVector,
    FailureClass,
    RegimeResult,
    TerminalCategory,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MockModelProvider:
    supports_verified_deterministic_seed = True

    def complete(self, prompt: str, *, requested_seed: int | None = None) -> str:
        return f"mock:{requested_seed}:{hashlib.sha256(prompt.encode()).hexdigest()[:8]}"


class ToyBenchmark:
    expected_sum = 6

    def prepare_root(self, workspace: Path, *, template_id: str, seed: int) -> None:
        workspace.mkdir(parents=True, exist_ok=False)
        trusted = workspace / "trusted_source.json"
        trusted.write_text(json.dumps({"values": [1, 2, 3]}) + "\n", encoding="utf-8")
        shutil.copy2(trusted, workspace / "source.json")
        (workspace / "provenance.json").write_text(
            json.dumps({"source_sha256": _digest(trusted)}) + "\n",
            encoding="utf-8",
        )
        (workspace / "task.json").write_text(
            json.dumps({"template_id": template_id, "seed": seed}) + "\n",
            encoding="utf-8",
        )

    def deterministic_probe(self, workspace: Path) -> dict[str, str]:
        return {
            "source_sha256": _digest(workspace / "source.json"),
            "provenance_sha256": _digest(workspace / "provenance.json"),
        }

    def grade(self, workspace: Path) -> RegimeResult:
        result_path = workspace / "result.json"
        if not result_path.exists():
            return RegimeResult(
                terminal_category=TerminalCategory.UNRESOLVED_TERMINATION,
                failure_class=FailureClass.POSTTREATMENT_MISSINGNESS,
            )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        valid = result.get("sum") == self.expected_sum and verify_source(workspace) == "pass"
        return RegimeResult(
            terminal_category=(
                TerminalCategory.VALIDATED_COMPLETION
                if valid
                else TerminalCategory.INVALID_SCIENTIFIC_OUTPUT
            ),
            primary_outcome=float(valid),
        )


class ToyFaultInjector:
    def apply_fault(self, workspace: Path) -> None:
        (workspace / "source.json").write_text(
            json.dumps({"values": [1, 2, 30]}) + "\n", encoding="utf-8"
        )

    def apply_sham(self, workspace: Path) -> None:
        (workspace / "sham.json").write_text(
            json.dumps({"operation": "read_only_probe"}) + "\n", encoding="utf-8"
        )


def verify_source(workspace: Path) -> str:
    expected = json.loads((workspace / "provenance.json").read_text(encoding="utf-8"))[
        "source_sha256"
    ]
    return "pass" if _digest(workspace / "source.json") == expected else "fail"


def continue_toy(workspace: Path) -> None:
    values = json.loads((workspace / "source.json").read_text(encoding="utf-8"))["values"]
    (workspace / "result.json").write_text(
        json.dumps({"sum": sum(values)}) + "\n", encoding="utf-8"
    )


class ToyWorkspaceAvailabilityProbe:
    """Legacy toy workspace probe; not the registered evidence evaluator."""

    def evaluate(self, workspace: Path) -> dict[str, bool]:
        common = (workspace / "source.json").exists()
        recovery = all(
            (workspace / name).exists()
            for name in ("source.json", "trusted_source.json", "provenance.json")
        )
        return {"g_0": common, "g_v": common, "g_r_toy": recovery}


class NoInterventionRegime:
    regime_id = "g_0"

    def is_available(self, workspace: Path) -> bool:
        return (workspace / "source.json").exists()

    def execute(self, context: BranchContext) -> RegimeResult:
        continue_toy(context.workspace)
        return ToyBenchmark().grade(context.workspace)


class VerificationRegime:
    regime_id = "g_v"

    def is_available(self, workspace: Path) -> bool:
        return all((workspace / name).exists() for name in ("source.json", "provenance.json"))

    def execute(self, context: BranchContext) -> RegimeResult:
        verifier_result = verify_source(context.workspace)
        cost = CostVector(verifier_calls=1, tool_calls=1)
        if verifier_result == "pass":
            continue_toy(context.workspace)
            graded = ToyBenchmark().grade(context.workspace)
            return RegimeResult(
                terminal_category=graded.terminal_category,
                primary_outcome=graded.primary_outcome,
                verifier_result=verifier_result,
                cost=cost,
            )
        return RegimeResult(
            terminal_category=TerminalCategory.RESPONSIBLE_ESCALATION,
            primary_outcome=0.0,
            verifier_result=verifier_result,
            cost=cost,
        )


class ToyRecoveryRegime:
    regime_id = "g_r_toy"

    def is_available(self, workspace: Path) -> bool:
        return ToyWorkspaceAvailabilityProbe().evaluate(workspace)[self.regime_id]

    def execute(self, context: BranchContext) -> RegimeResult:
        if not self.is_available(context.workspace):
            return RegimeResult(
                terminal_category=TerminalCategory.NOT_TERMINAL,
                failure_class=FailureClass.REGIME_UNAVAILABLE_PRETREATMENT,
            )
        shutil.copy2(context.workspace / "trusted_source.json", context.workspace / "source.json")
        if verify_source(context.workspace) != "pass":
            return RegimeResult(
                terminal_category=TerminalCategory.RESPONSIBLE_ESCALATION,
                failure_class=FailureClass.REGIME_INDUCED_EXECUTION,
                verifier_result="postcondition_fail",
                cost=CostVector(tool_calls=2, artifact_rewrites=1),
            )
        continue_toy(context.workspace)
        graded = ToyBenchmark().grade(context.workspace)
        return RegimeResult(
            terminal_category=graded.terminal_category,
            primary_outcome=graded.primary_outcome,
            verifier_result="postcondition_pass",
            cost=CostVector(tool_calls=2, artifact_rewrites=1),
        )
