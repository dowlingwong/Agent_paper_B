"""Restricted scientific tool bridge (Round 8 Stage 6).

The Python scaffold owns tool execution; Pi only requests tools. Every request
passes, in order: schema validation, tool allowlist, workspace path-containment,
hidden-path denylist, regime availability, budget authorization and debit
reservation, execution, canonical result capture, actual cost reconciliation,
and an immutable trace append. Symlink escapes, absolute-path escapes, `..`
traversal, shell interpolation outside the registered command grammar, unknown
environment variables, and access to oracle/adjudicator/sibling/evidence roots
are all rejected.
"""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .budget import BudgetGuard
from .types import CostVector

#: Imported lazily inside the helper below. `d7_adjudicator` pulls in the
#: scoring stack, and the tool bridge is imported by callers that never score.


def _validate_submitted_artifact(path: Path) -> tuple[str | None, str]:
    """Parse and validate a submission exactly as the adjudicator will.

    Returns ``(candidate_source, detail)``; ``candidate_source`` is ``None``
    when the artifact is not acceptable and ``detail`` says why, in the
    adjudicator's own words.
    """
    from .d7_adjudicator import _validate_submission  # noqa: PLC0415
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"candidate artifact is unreadable: {type(exc).__name__}"
    try:
        submission = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"submission is not valid JSON: {exc}"
    return _validate_submission(submission)

#: Re-exported so the accepted payload can echo the schema the agent must meet.
SUBMISSION_SCHEMA = "d7-submission-0.2-restricted"

REGISTERED_TOOLS = (
    "read_artifact",
    "write_artifact",
    "edit_artifact",
    "run_registered_command",
    "inspect_dataset",
    "submit_candidate",
    "request_verification",
)

# Fixed command grammar: a command name (no shell metacharacters) plus positional
# args. The caller registers the handler per command; interpolation is forbidden.
_SAFE_COMMAND = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")

# Denylisted path names (any segment) that a tool must never reach.
HIDDEN_SEGMENTS = frozenset(
    {"oracle", "assignment", "adjudicator", "sibling", "evidence", "risk", "hidden", ".pi"}
)

# Canonical tool argument schemas (JSON Schema form, matching the TypeScript
# extension's TypeBox output exactly). TOOL_SCHEMA_DIGEST is the single digest
# recorded in manifests; the extension announces its own digest on stderr and
# the smoke test proves the two match.
CANONICAL_TOOL_SCHEMAS = {
    "read_artifact": {
        "type": "object",
        "required": ["path"],
        "properties": {"path": {"type": "string", "description": "workspace-relative file path"}},
    },
    "write_artifact": {
        "type": "object",
        "required": ["path", "content"],
        "properties": {
            "path": {"type": "string", "description": "workspace-relative file path"},
            "content": {"type": "string", "description": "file content"},
        },
    },
    "edit_artifact": {
        "type": "object",
        "required": ["path", "old_string", "new_string"],
        "properties": {
            "path": {"type": "string", "description": "workspace-relative file path"},
            "old_string": {"type": "string", "description": "exact substring to replace"},
            "new_string": {"type": "string", "description": "replacement text"},
        },
    },
    "run_registered_command": {
        "type": "object",
        "required": ["command"],
        "properties": {"command": {"type": "string", "description": "registered command name"}},
    },
    "inspect_dataset": {
        "type": "object",
        "required": ["dataset_id"],
        "properties": {"dataset_id": {"type": "string", "description": "registered dataset id"}},
    },
    "submit_candidate": {
        "type": "object",
        "required": ["path"],
        "properties": {"path": {"type": "string", "description": "workspace-relative candidate path"}},
    },
    "request_verification": {
        "type": "object",
        "required": ["path"],
        "properties": {"path": {"type": "string", "description": "workspace-relative candidate path"}},
    },
}

TOOL_SCHEMA_DIGEST = hashlib.sha256(
    json.dumps(CANONICAL_TOOL_SCHEMAS, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()


@dataclass(frozen=True)
class ToolRequest:
    name: str
    arguments: Mapping[str, Any]
    id: str


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    name: str
    result: Any
    error: str | None = None
    cost: CostVector = field(default_factory=CostVector)
    digest: str = ""


def _schema_error(name: str, arguments: Mapping[str, Any], required: Sequence[str]) -> str | None:
    missing = [key for key in required if key not in arguments]
    if missing:
        return f"{name} missing arguments: {missing}"
    return None


class WorkspaceGuard:
    """Path containment + hidden-segment denylist, rejecting escapes."""

    def __init__(self, workspace_root: Path, *, read_only_roots: Sequence[Path] = ()) -> None:
        self.workspace_root = workspace_root.resolve()
        self.read_only_roots = tuple(root.resolve() for root in read_only_roots)

    def resolve_within(self, relative: str, *, for_write: bool = True) -> Path:
        if not isinstance(relative, str) or not relative:
            raise ValueError("path must be a nonempty string")
        raw = Path(relative)
        if raw.is_absolute():
            # Absolute paths are allowed only when they resolve inside the
            # workspace (some models emit the workspace's absolute path); an
            # absolute path that escapes is rejected by containment below.
            candidate = raw
        else:
            if ".." in raw.parts:
                raise ValueError("parent-traversal escape rejected")
            candidate = self.workspace_root / raw
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise ValueError("path escapes the workspace") from None
        # The hidden-segment denylist applies to reads AND writes: assignment,
        # risk, oracle, adjudicator, sibling, evidence, .pi, session, and socket
        # roots are never reachable through the tool layer.
        if any(segment in HIDDEN_SEGMENTS for segment in resolved.parts[len(self.workspace_root.parts):]):
            raise ValueError("hidden-path denylist violated")
        if resolved.is_symlink() or any(p.is_symlink() for p in resolved.parents if p != self.workspace_root):
            raise ValueError("symlink escape rejected")
        return resolved

    def allow_dataset(self, dataset_root: Path, dataset_id: str) -> Path:
        if not isinstance(dataset_id, str) or not dataset_id or any(c not in _SAFE_COMMAND for c in dataset_id):
            raise ValueError("unsafe dataset_id")
        target = (dataset_root / dataset_id).resolve()
        try:
            target.relative_to(dataset_root.resolve())
        except ValueError:
            raise ValueError("dataset path escapes the dataset root") from None
        return target


class ToolBridge:
    """Owns execution of the seven registered tools."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        dataset_root: Path | None = None,
        budget_guard: BudgetGuard | None = None,
        command_handlers: Mapping[str, Callable[..., Any]] | None = None,
        verifier: Callable[[str, Mapping[str, Any]], tuple[bool, str]] | None = None,
        trace_sink: Callable[[Mapping[str, Any]], None] | None = None,
        allowed_tools: Sequence[str] = REGISTERED_TOOLS,
    ) -> None:
        self.guard = WorkspaceGuard(workspace_root)
        self.workspace_root = workspace_root.resolve()
        self.dataset_root = dataset_root.resolve() if dataset_root else None
        self.budget = budget_guard
        self.command_handlers = dict(command_handlers or {})
        self.verifier = verifier
        self.trace_sink = trace_sink or (lambda _record: None)
        self.allowed_tools = frozenset(allowed_tools)

    def execute(self, request: ToolRequest, *, regime_id: str) -> ToolResult:
        name = request.name
        arguments = dict(request.arguments or {})
        if name not in REGISTERED_TOOLS:
            return self._fail(request, f"unknown tool: {name}")
        if name not in self.allowed_tools:
            return self._fail(request, f"tool not allowlisted: {name}")

        # 1. schema validation
        error = _schema_error(name, arguments, _REQUIRED_ARGS[name])
        if error:
            return self._fail(request, error)

        # 6. budget authorization + debit reservation (before execution)
        if self.budget is not None:
            denied = self.budget.authorize(f"tool:{name}")
            if denied is not None:
                return self._fail(request, "budget authorization failed", terminal=denied)

        try:
            result_value, cost = self._dispatch(name, arguments, regime_id)
        except (ValueError, OSError, KeyError) as exc:
            return self._fail(request, str(exc))
        except subprocess.SubprocessError as exc:
            return self._fail(request, f"command failed: {exc}")

        result = ToolResult(ok=True, name=name, result=result_value, cost=cost,
                            digest=_digest(result_value))
        self._append_trace(request, regime_id, result, None)
        return result

    # -- dispatch --------------------------------------------------------------

    def _dispatch(self, name: str, args: Mapping[str, Any], regime_id: str) -> tuple[Any, CostVector]:
        if name == "read_artifact":
            path = self.guard.resolve_within(args["path"], for_write=False)
            return path.read_text(encoding="utf-8", errors="replace"), CostVector(wall_seconds=0.01)
        if name == "write_artifact":
            path = self.guard.resolve_within(args["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(args["content"]), encoding="utf-8")
            return {"written": path.name, "sha256": _file_digest(path)}, CostVector(artifact_rewrites=1)
        if name == "edit_artifact":
            path = self.guard.resolve_within(args["path"])
            text = path.read_text(encoding="utf-8")
            old = str(args["old_string"])
            new = str(args["new_string"])
            if old not in text:
                raise ValueError("old_string not found")
            path.write_text(text.replace(old, new, 1), encoding="utf-8")
            return {"edited": path.name, "sha256": _file_digest(path)}, CostVector(artifact_rewrites=1)
        if name == "run_registered_command":
            command = args["command"]
            if not isinstance(command, str) or any(c not in _SAFE_COMMAND for c in command):
                raise ValueError("command is not in the registered grammar")
            handler = self.command_handlers.get(command)
            if handler is None:
                raise ValueError(f"unregistered command: {command}")
            output = handler(**{k: v for k, v in args.items() if k != "command"})
            return output, CostVector(tool_calls=1, wall_seconds=0.1)
        if name == "inspect_dataset":
            if self.dataset_root is None:
                raise ValueError("no dataset root configured")
            target = self.guard.allow_dataset(self.dataset_root, args["dataset_id"])
            manifest = target / ".dataset-manifest.json"
            if not manifest.is_file():
                raise ValueError("dataset not ready")
            return json.loads(manifest.read_text(encoding="utf-8")), CostVector(wall_seconds=0.01)
        if name == "submit_candidate":
            path = self.guard.resolve_within(args["path"])
            # Validate HERE, with the adjudicator's own validator.
            #
            # This used to hash the file and return `submitted` for anything at
            # all -- including a file that was not JSON, not an object, or
            # carried no `predict_py`. The agent was handed a SUCCESS while
            # holding garbage, and the failure only surfaced hours later at
            # adjudication. In Round 6 that produced 91 roots scored
            # `submission is not an object`, 8 `invalid syntax` and 2
            # `not valid JSON` -- 101 of 210 roots lost to a confound the agent
            # was given no way to see -- and, because the call always returned
            # ok and never terminated the root, one candidate called it 1,729
            # times to land 30 valid submissions.
            #
            # Sharing the validator is the point: the tool and the scorer
            # cannot disagree about what a valid submission is. The validator
            # checks the schema version, the presence of `predict_py`, and the
            # restricted-AST rules. It never touches the hidden set, so it says
            # nothing about whether the classifier is any GOOD -- task quality
            # is still entirely the model's problem. This removes format noise
            # without touching the measured construct.
            source, detail = _validate_submitted_artifact(path)
            if source is None:
                # A tool ERROR, so the agent sees the reason and may correct it
                # within its budget. Recovering from a schema error is the
                # agentic capability E0 needs; being silently wrong is not.
                raise ValueError(f"submission rejected: {detail}")
            return ({"submitted": path.name, "sha256": _file_digest(path),
                     "accepted": True, "schema_version": SUBMISSION_SCHEMA},
                    CostVector(artifact_rewrites=1))
        if name == "request_verification":
            if self.verifier is None or regime_id not in ("g_v", "g_r_f2_fehpo"):
                raise ValueError("verification unavailable in this regime")
            ok, detail = self.verifier(args.get("path", ""), dict(args))
            return {"verified": ok, "detail": detail}, CostVector(verifier_calls=1)
        raise ValueError(f"unimplemented tool: {name}")

    # -- accounting ------------------------------------------------------------

    def _fail(self, request: ToolRequest, reason: str, *, terminal: Any = None) -> ToolResult:
        result = ToolResult(ok=False, name=request.name, result=None, error=reason)
        self._append_trace(request, "", result, reason)
        return result

    def _append_trace(self, request: ToolRequest, regime_id: str, result: ToolResult, error: str | None) -> None:
        record = {
            "tool_request_id": request.id,
            "name": request.name,
            "arguments": _safe_arguments(request.arguments),
            "regime_id": regime_id,
            "ok": result.ok,
            "digest": result.digest,
            "error": error,
            "cost": result.cost.to_dict(),
        }
        self.trace_sink(record)


_REQUIRED_ARGS = {
    "read_artifact": ("path",),
    "write_artifact": ("path", "content"),
    "edit_artifact": ("path", "old_string", "new_string"),
    "run_registered_command": ("command",),
    "inspect_dataset": ("dataset_id",),
    "submit_candidate": ("path",),
    "request_verification": ("path",),
}


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_arguments(arguments: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in arguments.items():
        if key == "content" and isinstance(value, str) and len(value) > 4096:
            out[key] = f"<content {len(value)} bytes>"
        else:
            out[key] = value
    return out
