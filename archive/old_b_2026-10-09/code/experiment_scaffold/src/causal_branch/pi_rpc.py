"""Python-to-Pi JSON-lines RPC layer (Round 8, native protocol).

Drives the vendored Pi executable as a fresh subprocess over line-delimited JSON
on stdin/stdout. Pi's RPC mode receives native commands (JSON objects with a
`type` field and optional `id`) and emits responses (`type: "response"`) and
native events (e.g. `agent_settled`, `message_end`, `tool_execution_end`) as JSON
lines on stdout. See `third_party/pi/packages/coding-agent/docs/rpc.md`.

This module owns subprocess lifecycle, request/response correlation with IDs and
timeouts, asynchronous event capture, bounded log capture, graceful abort
followed by bounded forced termination, and schema validation for every event.
Only native Pi events are accepted; `agent_settled` is the quiescence terminal
(`agent_end` is not, because retry/compaction/queued work may follow). Unknown,
duplicate, missing, out-of-order, or malformed terminal events fail closed.
User/model text is never parsed as a control event.
"""

from __future__ import annotations

import json
import subprocess
import sys
import hashlib
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

REQUEST_TIMEOUT_SECONDS = 120.0
FORCED_KILL_SECONDS = 5.0


class RpcError(RuntimeError):
    pass


class RpcTimeout(RuntimeError):
    pass


class RpcProtocolError(RuntimeError):
    pass


# Canonical (Python-internal) events and their required fields. The adapter maps
# native Pi events into these names. Message events carry a synthetic sequence id
# (native Pi does not put an `id` on message events).
CANONICAL_EVENT_REQUIRED = {
    "session_created": ("session_id", "session_dir", "agent_dir"),
    "agent_started": (),
    "message_started": (),
    "message_delta": ("delta",),
    "message_completed": ("message",),
    "tool_started": ("id", "name", "arguments"),
    "tool_completed": ("id", "name", "result", "is_error"),
    "usage_update": ("usage",),
    "settled": (),
    "run_failed": ("error",),
    "run_timed_out": ("timeout",),
    "run_aborted": ("reason",),
    "extension_error": ("error",),
}

TERMINAL_EVENTS = {"settled", "run_failed", "run_timed_out", "run_aborted"}

# Native Pi event names -> canonical names. `agent_end` is deliberately NOT a
# terminal: retry, compaction, or queued continuations may follow; the adapter
# waits for `agent_settled`. Events without a mapping are dropped (they are not
# control events).
NATIVE_TO_CANONICAL = {
    "session_start": "session_created",
    "agent_start": "agent_started",
    "message_start": "message_started",
    "message_update": "message_delta",
    "message_end": "message_completed",
    "tool_execution_start": "tool_started",
    "tool_execution_end": "tool_completed",
    "agent_settled": "settled",
    "extension_error": "extension_error",
    "agent_end": None,          # not terminal by itself
    "turn_start": None,
    "turn_end": None,
    "entry_appended": None,     # recorded via get_entries instead
    "queue_update": None,
    "compaction_start": None,
    "compaction_end": None,
    "auto_retry_start": None,
    "auto_retry_end": None,
    "summarization_retry_scheduled": None,
    "summarization_retry_attempt_start": None,
    "summarization_retry_finished": None,
    "bash_execution_update": None,
    "session_info_changed": None,
    "thinking_level_changed": None,
}

# Native event -> canonical mapping of individual fields.
_FIELD_MAP = {
    "message_started": {"id": "id"},
    "message_delta": {"id": "id", "delta": "delta"},
    "message_completed": {"id": "id", "message": "message"},
    "tool_started": {"id": "toolCallId", "name": "toolName", "arguments": "args"},
    "tool_completed": {
        "id": "toolCallId",
        "name": "toolName",
        "result": "result",
        "is_error": "isError",
    },
}

_message_sequence = 0


def canonicalize_event(event: Mapping[str, Any]) -> dict[str, Any] | None:
    """Map a native Pi event to the canonical schema, or None to drop it."""
    global _message_sequence
    if not isinstance(event, dict):
        raise RpcProtocolError("event is not an object")
    raw_type = event.get("type")
    if not isinstance(raw_type, str) or not raw_type:
        raise RpcProtocolError("event lacks a string type")
    canonical_type = NATIVE_TO_CANONICAL.get(raw_type)
    if canonical_type is None:
        return None  # unknown or intentionally dropped non-terminal event
    canonical = {"type": canonical_type}
    for target, source in (_FIELD_MAP.get(canonical_type) or {}).items():
        if source in event:
            canonical[target] = event[source]
    if canonical_type in ("message_started", "message_delta", "message_completed"):
        _message_sequence += 1
        canonical.setdefault("id", f"msg-{_message_sequence}")
    if canonical_type == "message_delta" and "delta" not in canonical:
        # Native message_update carries a nested assistantMessageEvent with a
        # delta text field; extract it when present.
        assistant = event.get("assistantMessageEvent")
        if isinstance(assistant, dict) and "delta" in assistant:
            canonical["delta"] = assistant["delta"]
        elif isinstance(assistant, dict) and "text" in assistant:
            canonical["delta"] = assistant["text"]
        else:
            canonical["delta"] = ""
    if canonical_type == "message_completed" and "message" not in canonical:
        canonical["message"] = event.get("message", {})
    if canonical_type == "message_completed":
        # Surface the provider identity the locally patched Pi now records, so a
        # consumer never has to reach into the nested message to find out which
        # backend configuration served this completion.
        message = canonical.get("message")
        if isinstance(message, dict) and message.get("role") == "assistant":
            canonical["role"] = "assistant"
            for target, source in (
                ("completion_id", "responseId"),
                ("system_fingerprint", "systemFingerprint"),
                ("response_model", "providerModel"),
                ("provider_created", "providerCreated"),
                ("finish_reason", "rawStopReason"),
            ):
                if source in message:
                    canonical[target] = message[source]
    if canonical_type == "session_created":
        canonical.setdefault("session_id", str(event.get("sessionId", "")))
        canonical.setdefault("session_dir", str(event.get("sessionDir", "")))
        canonical.setdefault("agent_dir", str(event.get("agentDir", "")))
    _validate_canonical(canonical)
    return canonical


def _validate_canonical(event: Mapping[str, Any]) -> None:
    required = CANONICAL_EVENT_REQUIRED.get(event["type"])
    if required is None:
        raise RpcProtocolError(f"unregistered canonical event type: {event['type']}")
    for key in required:
        if key not in event:
            raise RpcProtocolError(f"event {event['type']} missing required field: {key}")


class PiRpcClient:
    """Manage one Pi subprocess and its native JSON-lines protocol."""

    def __init__(
        self,
        *,
        argv: Sequence[str],
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        request_timeout: float = REQUEST_TIMEOUT_SECONDS,
        log_limit: int = 65536,
    ) -> None:
        self.argv = list(argv)
        self.cwd = cwd
        self.env = dict(env or {})
        self.request_timeout = request_timeout
        self.log_limit = log_limit
        self.proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._pending: dict[str, list[dict[str, Any]]] = {}
        self._events: list[dict[str, Any]] = []
        self._protocol_errors: list[str] = []
        #: Whether a terminal has already been delivered for the CURRENT
        #: exchange. Reset when a `prompt` opens the next one. Without it, a
        #: duplicate terminal was only ever noticed if it happened to arrive
        #: before the waiter was scheduled -- see _handle_line.
        self._terminal_delivered = False
        #: How many further terminals are protocol-EXPECTED. Granted only when
        #: an abort is actually transmitted, and only one per abort. See
        #: `abort()` for why this is a counted allowance rather than a flag.
        self._expected_terminals = 0
        #: The abort requests whose transmission granted an allowance, kept so
        #: the artifact can show what the allowance was spent on.
        self._abort_requests: list[str] = []
        self._stderr_bytes = bytearray()
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._terminated = False

    # -- diagnostics -----------------------------------------------------------

    def launch_diagnostics(self) -> dict[str, Any]:
        """Everything needed to tell WHY Pi died, captured at the failure.

        "Pi process exited before responding" is a true statement that carries no
        information: it does not say whether the entry file was missing, Node was
        the wrong major version, an import threw, or the process was killed. Each
        of those is a different repair, and without this the only way to tell them
        apart is to reproduce by hand.
        """
        proc = self.proc
        exit_code = None
        if proc is not None:
            exit_code = proc.poll()
        with self._lock:
            stderr_tail = bytes(self._stderr_bytes[-4000:]).decode(
                "utf-8", errors="replace")
            protocol_errors = list(self._protocol_errors[-10:])
        argv = [str(part) for part in self.argv]
        node_executable = argv[0] if argv else None
        node_version = None
        if node_executable:
            try:
                node_version = subprocess.run(
                    [node_executable, "--version"], capture_output=True,
                    text=True, timeout=20).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                node_version = None

        def _digest(path: Any) -> dict[str, Any]:
            try:
                data = Path(str(path)).read_bytes()
                return {"path": str(path), "exists": True,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "bytes": len(data)}
            except OSError as exc:
                return {"path": str(path), "exists": False,
                        "error": f"{type(exc).__name__}: {exc}"}

        entry = next((part for part in argv[1:]
                      if str(part).endswith(".js")), None)
        models_json = None
        for index, part in enumerate(argv):
            if str(part).endswith("models.json"):
                models_json = part
                break
            if part in ("--models", "--models-json") and index + 1 < len(argv):
                models_json = argv[index + 1]
                break
        return {
            "exit_code": exit_code,
            "argv": argv,
            "argv_sha256": hashlib.sha256(
                json.dumps(argv, separators=(",", ":")).encode("utf-8")).hexdigest(),
            "cwd": str(self.cwd) if self.cwd else None,
            "node_executable": node_executable,
            "node_version": node_version,
            "pi_entry": _digest(entry) if entry else None,
            "models_json": _digest(models_json) if models_json else None,
            "stderr_tail": stderr_tail,
            "stderr_bytes_captured": len(stderr_tail),
            "protocol_errors": protocol_errors,
            "env_keys": sorted(self.env),
        }

    # -- lifecycle -------------------------------------------------------------

    def start(self) -> None:
        if self.proc is not None:
            raise RpcError("Pi RPC client already started")
        self.proc = subprocess.Popen(
            self.argv,
            cwd=str(self.cwd) if self.cwd else None,
            env={**self.env},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
        )
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._stderr_reader = threading.Thread(target=self._stderr_loop, daemon=True)
        self._stderr_reader.start()

    def _stderr_loop(self) -> None:
        assert self.proc is not None and self.proc.stderr is not None
        for chunk in iter(lambda: self.proc.stderr.read(4096), b""):
            if self._terminated:
                break
            with self._lock:
                if len(self._stderr_bytes) < self.log_limit:
                    self._stderr_bytes.extend(chunk[: self.log_limit - len(self._stderr_bytes)])

    def _read_loop(self) -> None:
        assert self.proc is not None
        assert self.proc.stdout is not None
        for raw in self.proc.stdout:
            if self._terminated:
                break
            self._handle_raw_line(raw)
        with self._cond:
            self._terminated = True
            self._cond.notify_all()

    def _handle_raw_line(self, raw: bytes) -> None:
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            return
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            with self._cond:
                self._protocol_errors.append(f"malformed JSON line: {exc}")
            return
        if not isinstance(obj, dict):
            with self._cond:
                self._protocol_errors.append("non-object JSON line")
            return
        if obj.get("type") == "response":
            req_id = obj.get("id")
            with self._cond:
                if req_id in self._abort_requests:
                    # The reply to an abort WE sent. `abort()` does not block
                    # for it -- the process may be dying -- so it is not in
                    # `_pending`, but it is solicited and must not be recorded
                    # as unsolicited.
                    pass
                elif req_id in self._pending:
                    self._pending[req_id].append(obj)
                    self._cond.notify_all()
                elif req_id is None:
                    # Response to an id-less command (e.g. our own abort); benign.
                    pass
                else:
                    self._protocol_errors.append(f"unsolicited response id={req_id!r}")
            return
        if obj.get("type") == "extension_ui_request":
            # Auto-cancel any extension UI request: the scientific harness never
            # delegates a decision to Pi's UI layer.
            req_id = obj.get("id")
            if isinstance(req_id, str):
                self._write_line({"type": "extension_ui_response", "id": req_id, "cancelled": True})
            return
        try:
            canonical = canonicalize_event(obj)
        except RpcProtocolError as exc:
            with self._cond:
                self._protocol_errors.append(str(exc))
            return
        if canonical is None:
            return
        with self._cond:
            if canonical.get("type") in TERMINAL_EVENTS:
                # FAIL CLOSED AT INGEST, not at inspection. `wait_terminal`
                # raises when it finds more than one terminal buffered, but it
                # REMOVES the terminal it returns -- so if the reader thread is
                # descheduled between the two events, the waiter consumes the
                # first, returns, and the duplicate lands with nobody looking.
                # Detection then depended on thread scheduling rather than on
                # the protocol violation. Recording it here makes it
                # unconditional; `PiAgentAdapter` already turns a non-empty
                # `protocol_errors` into a `run_failed` terminal, so the
                # exchange can no longer be reported as clean either way.
                already_buffered = any(event.get("type") in TERMINAL_EVENTS
                                       for event in self._events)
                if already_buffered or self._terminal_delivered:
                    if self._expected_terminals > 0:
                        # Answers a transmitted abort. Consumed, not renewed.
                        self._expected_terminals -= 1
                    else:
                        self._protocol_errors.append(
                            "duplicate terminal event: "
                            f"{canonical.get('type')!r} after a terminal had "
                            f"already been "
                            f"{'buffered' if already_buffered else 'delivered'} "
                            "for this exchange, and no transmitted abort made a "
                            "further terminal expected")
            self._events.append(canonical)
            self._cond.notify_all()

    def _write_line(self, obj: Mapping[str, Any]) -> None:
        if self.proc is None or self.proc.stdin is None or self.proc.poll() is not None:
            raise RpcError("Pi process is not running")
        self.proc.stdin.write((json.dumps(dict(obj), separators=(",", ":")) + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    # -- request/response ------------------------------------------------------

    def request(self, command: Mapping[str, Any], *, timeout: float | None = None) -> dict[str, Any]:
        req_id = uuid.uuid4().hex
        with self._cond:
            self._pending[req_id] = []
            if command.get("type") == "prompt":
                # A new exchange: the terminal it produces is its own, not a
                # duplicate of the previous exchange's.
                self._terminal_delivered = False
        self._write_line({"id": req_id, **command})
        deadline = time.monotonic() + (timeout if timeout is not None else self.request_timeout)
        process_exited = False
        with self._cond:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._pending.pop(req_id, None)
                    raise RpcTimeout(f"Pi RPC request {command.get('type')!r} timed out")
                if self._pending[req_id]:
                    responses = self._pending.pop(req_id)
                    break
                if self._terminated:
                    self._pending.pop(req_id, None)
                    process_exited = True
                    break
                self._cond.wait(timeout=min(remaining, 0.5))
        # launch_diagnostics() takes the same lock to snapshot stderr and
        # protocol errors. Calling it from inside the condition above
        # deadlocks exactly when Pi exits during a pending request.
        if process_exited:
            diagnostics = self.launch_diagnostics()
            error = RpcError(
                "Pi process exited before responding "
                f"(exit_code={diagnostics.get('exit_code')!r}, "
                f"node={diagnostics.get('node_version')!r}, "
                f"stderr_tail={diagnostics.get('stderr_tail', '')[-400:]!r})")
            error.diagnostics = diagnostics  # type: ignore[attr-defined]
            raise error
        if len(responses) > 1:
            raise RpcProtocolError(f"duplicate response for request {req_id}")
        response = responses[0]
        if response.get("success") is not True:
            raise RpcError(f"Pi command {command.get('type')!r} failed: {response.get('error')}")
        return response

    # -- events ----------------------------------------------------------------

    def drain_events(self, *, predicate: Callable[[dict[str, Any]], bool] | None = None) -> list[dict[str, Any]]:
        with self._cond:
            events = list(self._events)
            self._events.clear()
        if predicate is not None:
            events = [event for event in events if predicate(event)]
        return events

    def wait_for_event(self, event_type: str, *, timeout: float | None = None) -> dict[str, Any]:
        deadline = time.monotonic() + (timeout if timeout is not None else self.request_timeout)
        with self._cond:
            while True:
                for event in self._events:
                    if event.get("type") == event_type:
                        self._events.remove(event)
                        return event
                if self._terminated:
                    raise RpcError(f"Pi process exited before event {event_type!r}")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RpcTimeout(f"event {event_type!r} not observed")
                self._cond.wait(timeout=min(remaining, 0.5))

    def wait_terminal(
        self,
        *,
        timeout: float | None = None,
        stop_reason: Callable[[Sequence[dict[str, Any]]], str | None] | None = None,
    ) -> dict[str, Any]:
        """Wait for quiescence (`settled`) or a failure terminal. Duplicate or
        conflicting terminal events fail closed. `agent_end` alone is not
        terminal.

        ``stop_reason`` observes the complete buffered event trace while the
        process is live. It lets a caller enforce deterministic event-derived
        budgets without racing the reader thread. A returned reason is a
        synthetic terminal; the caller's normal ``stop()`` path aborts the
        process after this lock has been released.
        """
        deadline = time.monotonic() + (timeout if timeout is not None else self.request_timeout)
        with self._cond:
            while True:
                terminals = [event for event in self._events if event.get("type") in TERMINAL_EVENTS]
                if len(terminals) > 1:
                    raise RpcProtocolError(
                        "duplicate terminal events observed: "
                        + ", ".join(event.get("type", "?") for event in terminals)
                    )
                if terminals:
                    terminal = terminals[0]
                    self._events.remove(terminal)
                    self._terminal_delivered = True
                    return terminal
                if stop_reason is not None:
                    reason = stop_reason(tuple(self._events))
                    if reason:
                        return {"type": "budget_exhausted", "reason": reason}
                if self._terminated:
                    raise RpcError("Pi process exited without a terminal event")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RpcTimeout("no terminal event observed")
                self._cond.wait(timeout=min(remaining, 0.5))

    def protocol_errors(self) -> list[str]:
        with self._cond:
            return list(self._protocol_errors)

    # -- shutdown --------------------------------------------------------------

    def abort(self) -> None:
        """Ask the agent to stop, and account for the terminal that answers.

        WHAT THE PROTOCOL CAN AND CANNOT TELL US. An abort is a request and
        carries an id, so we know whether it was TRANSMITTED. The terminal that
        follows is an *event*, and the protocol does not tag an event with the
        id of the request that caused it -- so nothing on the wire positively
        identifies a given terminal as this abort's reply.

        An earlier version therefore used a blanket `_shutting_down` flag,
        suppressing every duplicate from the moment shutdown began. That is too
        broad in both directions: it was set BEFORE transmission, so a duplicate
        already in flight was excused, and it never expired, so any number of
        unsolicited terminals during shutdown were excused too.

        The rule here is the conservative one the protocol does support: a
        transmitted abort makes EXACTLY ONE further terminal expected. The
        allowance is granted only after the write succeeds, is consumed by the
        first terminal that uses it, and does not renew. A duplicate arriving
        before transmission, or a second one after the allowance is spent, is
        still a protocol violation.

        **THIS IS NOT A PROOF OF ATTRIBUTION AND IS NOT DESCRIBED AS ONE.** A
        successful write proves an abort was SENT. It does not prove that the
        next terminal was caused by it: an unsolicited duplicate arriving in the
        same window is indistinguishable from the abort's reply, and it will
        consume the allowance. Within that window the guarantee is weakened to
        "at most one terminal is excused", not "the excused terminal was the
        reply".

        The ambiguity is therefore AVOIDED rather than adjudicated wherever it
        can be: `stop()` sends no abort at all when the exchange already
        delivered its terminal, which is the common case, and then nothing is
        excused. What remains is the genuinely unsettled shutdown -- a timeout or
        a budget stop -- where an abort must be sent. That residue is a real
        protocol-policy limit and is surfaced, not closed.
        """
        if self.proc is None:
            return
        request_id = uuid.uuid4().hex
        # Registered BEFORE the write, because the reply can arrive before the
        # write call returns; the ALLOWANCE is granted only after transmission
        # succeeds. Recognising the reply and expecting a terminal are two
        # different facts and are recorded at two different moments.
        with self._cond:
            self._abort_requests.append(request_id)
        try:
            self._write_line({"id": request_id, "type": "abort"})
        except RpcError:
            pass
        else:
            # Only a TRANSMITTED abort makes a terminal expected.
            with self._cond:
                self._expected_terminals += 1
        try:
            self.proc.wait(timeout=FORCED_KILL_SECONDS)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            try:
                self.proc.wait(timeout=FORCED_KILL_SECONDS)
            except subprocess.TimeoutExpired:
                pass

    def terminate_without_abort(self) -> None:
        """Wind the child down WITHOUT sending an abort.

        Used when the exchange already delivered its terminal. Sending an abort
        then would invite a reply we would have to excuse, and an excused
        terminal is one we cannot tell from an unsolicited one -- so the
        ambiguity is avoided rather than adjudicated. No allowance is granted,
        which means any terminal arriving during this shutdown is unsolicited by
        construction and is recorded as the violation it is.
        """
        if self.proc is None:
            return
        try:
            if self.proc.stdin is not None:
                self.proc.stdin.close()          # EOF is the unambiguous signal
        except OSError:
            pass
        try:
            self.proc.wait(timeout=FORCED_KILL_SECONDS)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            try:
                self.proc.wait(timeout=FORCED_KILL_SECONDS)
            except subprocess.TimeoutExpired:
                pass

    def stop(self) -> dict[str, Any]:
        # A settled exchange does not need an abort. This is the lifecycle
        # change that REMOVES the ambiguity for the common case rather than
        # ruling on it: with no abort sent, no terminal is expected, and the
        # counted allowance never has to be trusted. The allowance survives only
        # for the genuinely unsettled case -- a timeout or a budget stop -- where
        # an abort really must be sent and the protocol really cannot say which
        # terminal answers it.
        with self._cond:
            settled_already = self._terminal_delivered
        if settled_already:
            self.terminate_without_abort()
        else:
            self.abort()
        with self._cond:
            self._terminated = True
            self._cond.notify_all()
        if self.proc is not None:
            for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        return {
            "returncode": self.proc.returncode if self.proc is not None else None,
            "stderr_tail": self._stderr_bytes[-4096:].decode("utf-8", errors="replace"),
            "protocol_errors": self.protocol_errors(),
        }
