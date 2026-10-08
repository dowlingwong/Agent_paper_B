"""Agent tree executor: one root's three trajectories through an agent backend.

References: ``docs/paper_split/B_INFRA_CONSTRUCTION_PLAN_20261006.md`` IP2
and ``docs/paper_split/B_EXECUTION_RUNBOOK_20261008.md`` Stage 4.1.

``execute_tree_v2`` (``branch_tree.py``) drives a Python task object; it never
runs an agent.  This module grows the same three-regime tree -- verify at
checkpoint 1 (``now``); continue to checkpoint 2, then fork ``later`` (verify)
and ``never`` (continue) from the *same* checkpoint-2 state -- by running
agent *turns* through a backend that writes Pi-shaped session JSONL.

What the executor guarantees (design v2 §1-§2):

- the session file lives inside the workspace (``<workspace>/.session/``), so
  the existing snapshot / fork path (``FileSnapshotManager``,
  ``FileBranchIsolationManager``) carries it and the checkpoint tree hash binds
  it;
- a fork writes a child session whose header names the parent and whose first
  entries are exactly the parent's prefix through the checkpoint entry
  (``pi_fork.restore_parent_to_checkpoint`` / ``read_session`` semantics);
- at most one verification per trajectory: ``ToolHandlers`` refuses a second
  ``verify_candidate`` and records the refusal as a tool result, so the record
  shows the refusal and ``records_to_tree`` sees ``verifier_calls <= 1``;
- no regime name reaches the backend: branches are ``b0``..``b3`` (plus a
  repetition suffix), prompts describe only what the agent may do, and error
  text is workspace-relative;
- the decision-time histories H1 (checkpoint 1) and H2 (checkpoint 2 on the
  continue branch) are built from the session entries up to the checkpoint
  marker and returned as ``serialiser.DecisionHistory`` with provenance.

Outcomes come from grading the executed workspace; no leaf constant is ever
supplied.  Nothing here is scientific evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Protocol

import numpy as np

from causal_branch.branching import FileBranchIsolationManager
from causal_branch.checkpoint import FileSnapshotManager
from causal_branch.control.branch_tree import TreeError, TreeRecord, records_to_tree
from causal_branch.control.configurator.serialiser import DecisionHistory, HistoryEvent
from causal_branch.pi_fork import read_session, restore_parent_to_checkpoint

SESSION_DIRNAME = ".session"
SESSION_HEADER_TYPE = "session"
#: Branch slots, in execution order.  The mapping to regimes is kept in the
#: TreeRecord (``decision_index`` + ``action``), never in a path or a prompt.
BRANCH_SLOTS = ("b0", "b1", "b2", "b3")
TOOL_NAMES = ("fit_candidate", "verify_candidate", "submit_candidate")

PROMPT_START = ("You are solving a tabular classification task. Use the tools to fit a "
                "candidate on the visible development data and submit it. Stop when the "
                "first checkpoint is announced.")
PROMPT_CONTINUE = ("Continue the task. A new development batch may have arrived. Refit if "
                   "useful and submit your final candidate.")
PROMPT_VERIFY_AVAILABLE = (" One verification of your candidate against held-out "
                           "diagnostics is available at this checkpoint; use verify_candidate at most once "
                           "before submitting.")
PROMPT_VERIFY_UNAVAILABLE = " No verification is available at this point."


class ExecutorError(ValueError):
    """The executor refused to run or the run violated the tree contract."""


# --------------------------------------------------------------------------
# Task tools and the verification guard
# --------------------------------------------------------------------------


class TaskTools(Protocol):
    """Task-side implementations behind the three agent tools."""

    def fit_candidate(self, workspace: Path) -> dict: ...
    def verify_candidate(self, workspace: Path, candidate: dict) -> dict: ...
    def submit_candidate(self, workspace: Path, candidate: dict) -> dict: ...
    def arrive_checkpoint2(self, workspace: Path) -> bool: ...
    def grade(self, workspace: Path) -> float: ...


@dataclass
class ToolHandlers:
    """One instance per branch turn.  Enforces the one-verification budget."""

    task: TaskTools
    workspace: Path
    verify_allowed: bool
    verifier_calls: int = 0
    refusals: int = 0
    log: list[dict] = field(default_factory=list)

    def call(self, name: str, arguments: Mapping[str, Any] | None = None) -> dict:
        arguments = dict(arguments or {})
        if name not in TOOL_NAMES:
            result = {"ok": False, "refused": True, "reason": f"unknown tool {name!r}"}
        elif name == "verify_candidate":
            if not self.verify_allowed or self.verifier_calls >= 1:
                self.refusals += 1
                result = {"ok": False, "refused": True,
                          "reason": "verification is not available on this branch"}
            else:
                self.verifier_calls += 1
                result = {"ok": True, "refused": False,
                          "result": self.task.verify_candidate(self.workspace, arguments.get("candidate", {}))}
        elif name == "fit_candidate":
            result = {"ok": True, "refused": False, "result": self.task.fit_candidate(self.workspace)}
        else:
            result = {"ok": True, "refused": False,
                      "result": self.task.submit_candidate(self.workspace, arguments.get("candidate", {}))}
        self.log.append({"name": name, "arguments": arguments, "ok": result["ok"],
                         "refused": result.get("refused", False)})
        return result


# --------------------------------------------------------------------------
# Session files (Pi-shaped JSONL)
# --------------------------------------------------------------------------


def _dump(record: Mapping[str, Any]) -> str:
    return json.dumps(dict(record), separators=(",", ":"), ensure_ascii=False, sort_keys=True)


def session_dir(workspace: Path) -> Path:
    return Path(workspace) / SESSION_DIRNAME


def sole_session(workspace: Path) -> Path:
    files = sorted(session_dir(workspace).glob("*.jsonl"))
    if len(files) != 1:
        raise ExecutorError(f"expected exactly one session file, found {len(files)}")
    return files[0]


def current_session(workspace: Path) -> Path:
    """The leaf of the fork chain: the one session no other session names as parent."""

    files = sorted(session_dir(workspace).glob("*.jsonl"))
    if not files:
        raise ExecutorError("workspace carries no session file")
    parents = {read_session(f).header.get("parentSession") for f in files}
    leaves = [f for f in files if f.name not in parents]
    if len(leaves) != 1:
        raise ExecutorError(f"expected one current session, found {len(leaves)}")
    return leaves[0]


def session_id_for(root_id: str, slot: str, repetition: int | None = None) -> str:
    base = f"{root_id}|{slot}|{'' if repetition is None else repetition}"
    return "s-" + hashlib.sha256(base.encode()).hexdigest()[:16]


def write_session(path: Path, header: Mapping[str, Any], entries: list[Mapping[str, Any]]) -> None:
    lines = [_dump(header)] + [_dump(e) for e in entries]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_entries(path: Path, entries: list[Mapping[str, Any]]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(_dump(entry) + "\n")


def fork_session(parent_session: Path, *, child_id: str, checkpoint_entry_id: str) -> Path:
    """Create the child session: parent prefix through the checkpoint, then nothing.

    The parent is first restored to the checkpoint entry (exact-prefix fork,
    not a whole-session copy).  The header names the parent by file name only,
    so no branch path leaks into the session text.
    """

    parent = restore_parent_to_checkpoint(parent_session, checkpoint_id=checkpoint_entry_id,
                                          entry_id=checkpoint_entry_id)
    document = read_session(parent_session)
    child_path = parent_session.with_name(f"{child_id}.jsonl")
    if child_path.exists():
        raise ExecutorError("child session already exists")
    header = {"type": SESSION_HEADER_TYPE, "id": child_id,
              "parentSession": parent_session.name,
              "parentPrefixSha256": parent.prefix_sha256}
    write_session(child_path, header, list(document.entries))
    return child_path


def checkpoint_entry(session: Path, checkpoint_id: str) -> dict:
    for entry in read_session(session).entries:
        if entry.get("type") == "checkpoint" and entry.get("checkpoint_id") == checkpoint_id:
            return dict(entry)
    raise ExecutorError(f"session carries no checkpoint entry {checkpoint_id!r}")


def prefix_digest(session: Path, entry_id: str) -> str:
    return read_session(session).prefix_digest(entry_id)


# --------------------------------------------------------------------------
# Backends
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class TurnResult:
    leaf_entry_id: str | None
    terminal: str
    usage: dict[str, int] = field(default_factory=dict)


class AgentBackend(Protocol):
    """Runs one agent turn and appends its entries to ``session``."""

    is_scripted: bool

    def run_turn(self, *, workspace: Path, session: Path, tools: ToolHandlers,
                 prompt: str, stop: str, seed: int) -> TurnResult: ...


@dataclass(frozen=True)
class PiBinding:
    """Everything the Pi backend needs; all fields must be set before a turn."""

    endpoint_path: str = ""
    pi_entry: str = ""
    system_prompt: str = ""
    extension: str = ""
    allowed_tools: tuple[str, ...] = ()
    allow_live: bool = False

    def missing(self) -> list[str]:
        out = [n for n in ("endpoint_path", "pi_entry", "system_prompt", "extension")
               if not getattr(self, n)]
        if not self.allowed_tools:
            out.append("allowed_tools")
        return out


class PiBackend:
    """The Devstral (Pi runtime) backend.  Refuses without a complete binding.

    The turn itself is delegated to ``causal_branch.adapters.pi_agent``; this
    class only guards the binding and translates the executor's call.  It is
    bound on the Ada host (runbook §6) and is never exercised on CPU.
    """

    is_scripted = False

    def __init__(self, binding: PiBinding) -> None:
        self.binding = binding

    def run_turn(self, *, workspace: Path, session: Path, tools: ToolHandlers,
                 prompt: str, stop: str, seed: int) -> TurnResult:
        missing = self.binding.missing()
        if missing:
            raise ExecutorError(f"Pi backend is not bound: missing {missing}")
        if not self.binding.allow_live:
            raise ExecutorError("Pi backend refused: allow_live is false (no authorisation)")
        raise ExecutorError("Pi backend turn delegation is bound on the Ada host; "
                            "not available in this checkout")


# --------------------------------------------------------------------------
# Histories from sessions
# --------------------------------------------------------------------------


def history_from_session(session: Path, *, phase: int, checkpoint_id: str,
                         redact: tuple[str, ...] = (), root_id: str = "",
                         template_family_id: str = "") -> DecisionHistory:
    """Decision-time history: entries up to and including the checkpoint marker."""

    document = read_session(session)
    events: list[HistoryEvent] = []
    seen_task = False
    checkpoint_step = None
    for step, entry in enumerate(document.entries):
        kind = entry.get("type")
        if kind == "message":
            role = entry.get("message", {}).get("role")
            text = str(entry.get("message", {}).get("content", ""))
            if role == "user":
                events.append(HistoryEvent(step, "observation" if seen_task else "task", text))
                seen_task = True
            elif role == "assistant":
                events.append(HistoryEvent(step, "assistant", text))
            else:
                raise ExecutorError(f"unknown message role {role!r}")
        elif kind == "tool_call":
            events.append(HistoryEvent(step, "tool_call", json.dumps(entry.get("arguments", {}),
                                                                      sort_keys=True),
                                       name=str(entry.get("name", ""))))
        elif kind == "tool_result":
            events.append(HistoryEvent(step, "tool_result", str(entry.get("content", "")),
                                       name=str(entry.get("name", ""))))
        elif kind == "checkpoint":
            events.append(HistoryEvent(step, "checkpoint", f"checkpoint {entry.get('checkpoint_id')} reached"))
            if entry.get("checkpoint_id") == checkpoint_id:
                checkpoint_step = step
                break
        else:
            raise ExecutorError(f"session entry type {kind!r} is not decision-time visible")
    if checkpoint_step is None:
        raise ExecutorError(f"session has no checkpoint {checkpoint_id!r}")
    marker = document.entries[checkpoint_step]["id"]
    return DecisionHistory(
        phase=phase, checkpoint_step=checkpoint_step, events=tuple(events), redact=redact,
        root_id=root_id, template_family_id=template_family_id,
        session_prefix_sha256=document.prefix_digest(marker),
        raw_sha256=hashlib.sha256(session.read_bytes()).hexdigest(),
    )


# --------------------------------------------------------------------------
# The executor
# --------------------------------------------------------------------------


def _relative_error(exc: Exception, workspace: Path) -> ExecutorError:
    text = str(exc).replace(str(workspace), "<workspace>")
    return ExecutorError(text)


def execute_agent_tree(task: TaskTools, backend: AgentBackend, *, root_id: str,
                       template_family_id: str, split: str, seed: int, branch_root: Path,
                       prepare, repetitions: int = 2) -> tuple[list[TreeRecord], dict, dict]:
    """Grow one root's three-regime tree through agent turns.

    ``prepare(workspace)`` lays out the task's initial workspace (no candidate
    yet; the agent fits it).  Returns ``(records, tree, histories)`` where
    ``histories = {"h1": DecisionHistory, "h2": DecisionHistory | None}``.
    """

    if repetitions < 2:
        raise ExecutorError("at least two stochastic repetitions per leaf are required")
    branch_root = Path(branch_root)
    snapshots = FileSnapshotManager()
    branches = FileBranchIsolationManager(branch_root, snapshots)
    redact = (root_id, template_family_id)

    # -- prefix: one turn to checkpoint 1 ------------------------------------
    prefix_ws = branch_root / "prefix" / "workspace"
    prefix_ws.parent.mkdir(parents=True, exist_ok=True)
    prepare(prefix_ws)
    sid0 = session_id_for(root_id, "prefix")
    s0 = session_dir(prefix_ws) / f"{sid0}.jsonl"
    write_session(s0, {"type": SESSION_HEADER_TYPE, "id": sid0}, [])
    tools0 = ToolHandlers(task=task, workspace=prefix_ws, verify_allowed=False)
    try:
        backend.run_turn(workspace=prefix_ws, session=s0, tools=tools0,
                         prompt=PROMPT_START, stop="checkpoint1", seed=seed)
    except ExecutorError:
        raise
    except Exception as exc:  # pragma: no cover - backend-specific failures
        raise _relative_error(exc, prefix_ws)
    c1 = checkpoint_entry(s0, "c1")
    snap1 = branch_root / "snap_c1"
    manifest1 = snapshots.capture(prefix_ws, snap1, checkpoint_id="c1", root_id=root_id,
                                  parent_checkpoint_id=None,
                                  budget_remaining={"verifier_calls": 1},
                                  feasible_regimes=["g0", "gv"],
                                  history_digest=prefix_digest(s0, c1["id"]))
    h1_hash = manifest1.tree_hash
    h1 = history_from_session(s0, phase=1, checkpoint_id="c1", redact=redact,
                              root_id=root_id, template_family_id=template_family_id)
    records: list[TreeRecord] = []
    usage: list[dict] = []
    refusals = 0

    def _leaf(slot: str, snap: Path, parent: str | None, checkpoint_id: str, verify: bool,
              stop: str) -> tuple[float, int]:
        nonlocal refusals
        outcomes, calls = [], []
        for rep in range(repetitions):
            branch_id = f"{slot}_r{rep}"
            ws = branches.fork(snap, branch_id=branch_id, parent_branch_id=parent)
            parent_session = current_session(ws)
            marker = checkpoint_entry(parent_session, checkpoint_id)
            child = fork_session(parent_session, child_id=session_id_for(root_id, slot, rep),
                                 checkpoint_entry_id=marker["id"])
            tools = ToolHandlers(task=task, workspace=ws, verify_allowed=verify)
            prompt = PROMPT_CONTINUE + (PROMPT_VERIFY_AVAILABLE if verify else PROMPT_VERIFY_UNAVAILABLE)
            try:
                result = backend.run_turn(workspace=ws, session=child, tools=tools, prompt=prompt,
                                          stop=stop, seed=seed * 1000 + rep)
            except ExecutorError:
                raise
            except Exception as exc:  # pragma: no cover
                raise _relative_error(exc, ws)
            usage.append(dict(result.usage))
            refusals += tools.refusals
            if verify and tools.verifier_calls != 1:
                raise ExecutorError("a verify branch must execute exactly one verification")
            if not verify and tools.verifier_calls != 0:
                raise ExecutorError("a continue branch executed a verification")
            outcomes.append(float(task.grade(ws)))
            calls.append(tools.verifier_calls)
        return float(np.mean(outcomes)), max(calls)

    # -- b0: verify now --------------------------------------------------------
    now_outcome, now_calls = _leaf(BRANCH_SLOTS[0], snap1, None, "c1", True, "finish")
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=1, branch_id=BRANCH_SLOTS[0], parent_branch_id=None, action="verify",
        history_hash_at_decision=h1_hash, history_hash_after=h1_hash, reached=True,
        verifier_calls=now_calls, outcome=now_outcome))

    # -- b1: continue to checkpoint 2 -------------------------------------------
    cont_slot = BRANCH_SLOTS[1]
    cont_ws = branches.fork(snap1, branch_id=cont_slot, parent_branch_id=None)
    parent_session = current_session(cont_ws)
    child = fork_session(parent_session, child_id=session_id_for(root_id, cont_slot),
                         checkpoint_entry_id=c1["id"])
    reached2 = bool(task.arrive_checkpoint2(cont_ws))
    if reached2:
        leaf = read_session(child).entries[-1]["id"]
        append_entries(child, [{
            "type": "message", "parentId": leaf,
            "id": "e" + hashlib.sha256(f"{child.stem}|arrival".encode()).hexdigest()[:10],
            "message": {"role": "user",
                        "content": "A new development batch (dev2.csv) has arrived in the workspace."}}])
    tools1 = ToolHandlers(task=task, workspace=cont_ws, verify_allowed=False)
    if not reached2:
        backend.run_turn(workspace=cont_ws, session=child, tools=tools1,
                         prompt=PROMPT_CONTINUE + PROMPT_VERIFY_UNAVAILABLE, stop="finish",
                         seed=seed * 1000 + 99)
        fallback = float(task.grade(cont_ws))
        records.append(TreeRecord(
            root_id=root_id, template_family_id=template_family_id, split=split,
            decision_index=1, branch_id=cont_slot, parent_branch_id=None, action="continue",
            history_hash_at_decision=h1_hash, history_hash_after=h1_hash, reached=False,
            terminated_before_decision=True, verifier_calls=0, outcome=fallback))
        tree = records_to_tree(records)
        tree["n_repetitions"] = repetitions
        return records, tree, {"h1": h1, "h2": None, "refusals": refusals, "usage": usage}
    backend.run_turn(workspace=cont_ws, session=child, tools=tools1,
                     prompt=PROMPT_CONTINUE + PROMPT_VERIFY_UNAVAILABLE, stop="checkpoint2",
                     seed=seed * 1000 + 99)
    if tools1.verifier_calls:
        raise ExecutorError("the continue branch executed a verification")
    c2 = checkpoint_entry(child, "c2")
    snap2 = branch_root / "snap_c2"
    manifest2 = snapshots.capture(cont_ws, snap2, checkpoint_id="c2", root_id=root_id,
                                  parent_checkpoint_id="c1",
                                  budget_remaining={"verifier_calls": 1},
                                  feasible_regimes=["g0", "gv"],
                                  history_digest=prefix_digest(child, c2["id"]))
    h2_hash = manifest2.tree_hash
    h2 = history_from_session(child, phase=2, checkpoint_id="c2", redact=redact,
                              root_id=root_id, template_family_id=template_family_id)
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=1, branch_id=cont_slot, parent_branch_id=None, action="continue",
        history_hash_at_decision=h1_hash, history_hash_after=h2_hash, reached=True,
        terminated_before_decision=False, verifier_calls=0, outcome=None))

    # -- b2 / b3: later and never, forked from the same checkpoint-2 state -------
    later_outcome, later_calls = _leaf(BRANCH_SLOTS[2], snap2, cont_slot, "c2", True, "finish")
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=2, branch_id=BRANCH_SLOTS[2], parent_branch_id=cont_slot, action="verify",
        history_hash_at_decision=h2_hash, history_hash_after=h2_hash, reached=True,
        verifier_calls=later_calls, outcome=later_outcome))
    never_outcome, never_calls = _leaf(BRANCH_SLOTS[3], snap2, cont_slot, "c2", False, "finish")
    records.append(TreeRecord(
        root_id=root_id, template_family_id=template_family_id, split=split,
        decision_index=2, branch_id=BRANCH_SLOTS[3], parent_branch_id=cont_slot, action="continue",
        history_hash_at_decision=h2_hash, history_hash_after=h2_hash, reached=True,
        verifier_calls=never_calls, outcome=never_outcome))
    tree = records_to_tree(records)
    tree["n_repetitions"] = repetitions
    return records, tree, {"h1": h1, "h2": h2, "refusals": refusals, "usage": usage}


def assert_no_regime_names(branch_root: Path, forbidden=("now", "later", "never")) -> None:
    """Audit: no regime name in any session text or branch path under ``branch_root``."""

    for path in sorted(Path(branch_root).rglob("*")):
        rel = str(path.relative_to(branch_root))
        for word in forbidden:
            if word in rel.split("/"):
                raise ExecutorError(f"regime name {word!r} in path {rel}")
        if path.is_file() and path.suffix == ".jsonl":
            text = path.read_text(encoding="utf-8").lower()
            for word in forbidden:
                if f'"{word}"' in text or f" {word} " in text:
                    raise ExecutorError(f"regime name {word!r} in session {rel}")
