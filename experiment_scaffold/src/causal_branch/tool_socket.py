"""Per-branch Unix-domain socket bridge between the Pi tool extension and Python.

The Pi extension (`experiment_scaffold/pi_extensions/scientific_tool_bridge.ts`)
forwards each tool request over a private per-branch Unix socket to this server,
which executes the request through `registered_tools.ToolBridge`.

Protocol (length-prefixed JSON frames):

- frame  = 4-byte big-endian length + JSON payload
- request  = {"protocol_version", "run_id", "branch_id", "tool_call_id",
              "tool_name", "arguments", "token"}
- response = {"protocol_version", "tool_call_id", "ok", "result", "error"}

Fail-closed properties: bounded frame size, exactly-once tool_call_ids (duplicate
rejection), per-process capability token, request timeout, cancellation, and a
clean error response on disconnect. Every accepted request gets exactly one
response.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import struct
import tempfile
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .registered_tools import ToolRequest

PROTOCOL_VERSION = "r8-tool-bridge-1"
MAX_FRAME_BYTES = 16 * 1024 * 1024  # 16 MiB
REQUEST_TIMEOUT_SECONDS = 120.0

#: Sentinel tool name for the out-of-band rendered-system-prompt observation the
#: Pi extension sends on this socket. It is intercepted HERE, inside the server,
#: so it can never reach a `ToolBridge` from any construction site -- the
#: capability handshake, a production turn, or the real-Pi local smoke.
OBSERVED_SYSTEM_PROMPT_TOOL = "__observed_system_prompt__"
#: Sentinel for the extension's REQUEST-level observation (`before_provider_request`):
#: the system message of one provider request, one message per request.
OBSERVED_REQUEST_SYSTEM_PROMPT_TOOL = "__observed_request_system_prompt__"
OBSERVATION_TOOLS = frozenset({OBSERVED_SYSTEM_PROMPT_TOOL, OBSERVED_REQUEST_SYSTEM_PROMPT_TOOL})

FRAME_HEADER = struct.Struct(">I")


class ToolBridgeProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class BridgeRequest:
    protocol_version: str
    run_id: str
    branch_id: str
    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]
    token: str


def _read_frame(conn: socket.socket) -> dict[str, Any]:
    header = _read_exact(conn, FRAME_HEADER.size)
    length = FRAME_HEADER.unpack(header)[0]
    if length == 0 or length > MAX_FRAME_BYTES:
        raise ToolBridgeProtocolError(f"invalid frame length: {length}")
    payload = _read_exact(conn, length)
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ToolBridgeProtocolError(f"malformed frame JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ToolBridgeProtocolError("frame payload is not an object")
    return obj


def _read_exact(conn: socket.socket, size: int) -> bytes:
    data = b""
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            raise ToolBridgeProtocolError("connection closed mid-frame")
        data += chunk
    return data


def _write_frame(conn: socket.socket, obj: dict[str, Any]) -> None:
    payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_FRAME_BYTES:
        raise ToolBridgeProtocolError("response frame too large")
    conn.sendall(FRAME_HEADER.pack(len(payload)) + payload)


class ToolBridgeSocketServer:
    """One listening Unix socket per branch; the Pi extension connects per call."""

    def __init__(
        self,
        *,
        socket_dir: Path,
        run_id: str,
        branch_id: str,
        executor: Callable[[BridgeRequest], dict[str, Any]],
        token: str | None = None,
        timeout_seconds: float = REQUEST_TIMEOUT_SECONDS,
        observations: dict[str, Any] | None = None,
    ) -> None:
        socket_dir.mkdir(parents=True, exist_ok=True)
        # AF_UNIX paths are length-limited; keep the socket name short.
        socket_name = f"tb{uuid.uuid4().hex[:8]}.sock"
        candidate = socket_dir / socket_name
        self._owned_socket_dir: Path | None = None
        # macOS permits only ~104 bytes and Linux ~108. Runtime/evidence roots
        # can legitimately be much longer, so use a private short indirection
        # rather than failing after a model process has started.
        if len(os.fsencode(candidate)) >= 96:
            self._owned_socket_dir = Path(tempfile.mkdtemp(prefix="cbtb-", dir="/tmp"))
            os.chmod(self._owned_socket_dir, 0o700)
            candidate = self._owned_socket_dir / socket_name
        self.socket_path = candidate
        self.run_id = run_id
        self.branch_id = branch_id
        self.executor = executor
        #: Out-of-band observations that arrive on this socket (currently the
        #: rendered-system-prompt digest). Owned by the caller; a caller that
        #: does not care simply leaves it empty, but the sentinel is intercepted
        #: here and never forwarded to `self.executor`.
        self.observations: dict[str, Any] = observations if observations is not None else {}
        self.token = token or uuid.uuid4().hex
        self.timeout_seconds = timeout_seconds
        self._server: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._seen_ids: set[str] = set()
        self._lock = threading.Lock()
        self._stop = threading.Event()

    def start(self) -> None:
        self._server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server.bind(str(self.socket_path))
        os.chmod(self.socket_path, 0o600)
        self._server.listen(4)
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self) -> None:
        assert self._server is not None
        while not self._stop.is_set():
            try:
                conn, _ = self._server.accept()
            except OSError:
                break
            threading.Thread(target=self._handle_connection, args=(conn,), daemon=True).start()

    def _handle_connection(self, conn: socket.socket) -> None:
        try:
            conn.settimeout(self.timeout_seconds)
            request = _read_frame(conn)
            response = self._dispatch(request)
            _write_frame(conn, response)
        except (ToolBridgeProtocolError, OSError, ValueError) as exc:
            # Fail closed: a malformed request still receives exactly one response.
            try:
                _write_frame(
                    conn,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "tool_call_id": None,
                        "ok": False,
                        "result": None,
                        "error": f"bridge protocol error: {exc}",
                    },
                )
            except OSError:
                pass
        finally:
            conn.close()

    def _dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("protocol_version") != PROTOCOL_VERSION:
            raise ToolBridgeProtocolError("protocol_version mismatch")
        if request.get("token") != self.token:
            raise ToolBridgeProtocolError("capability token mismatch")
        tool_call_id = request.get("tool_call_id")
        if not isinstance(tool_call_id, str) or not tool_call_id:
            raise ToolBridgeProtocolError("missing tool_call_id")
        with self._lock:
            if tool_call_id in self._seen_ids:
                raise ToolBridgeProtocolError(f"duplicate tool_call_id: {tool_call_id}")
            self._seen_ids.add(tool_call_id)
        tool_name = request.get("tool_name")
        arguments = request.get("arguments") or {}
        if not isinstance(tool_name, str) or not isinstance(arguments, dict):
            raise ToolBridgeProtocolError("malformed tool request")
        if tool_name in OBSERVATION_TOOLS:
            # STRUCTURAL INTERCEPTION. An observation is not a tool call: it is
            # recorded here and never reaches `self.executor`, so no construction
            # site can leak it to a `ToolBridge` even if it passes the bare
            # executor. A caller with no interest in it still gets it recorded
            # and simply ignores the box.
            #
            # Observations are kept as ORDERED LISTS with a receipt sequence, so
            # a second turn-start observation in one turn, or request-level
            # observations that disagree with the turn-start one, are visible
            # to the executor instead of overwriting each other.
            import time as _time
            entry = {
                "sha256": str(arguments.get("sha256") or ""),
                "tool_call_id": tool_call_id,
                "received_seq": len(self.observations.get("rendered_system_prompt_observations", []))
                + len(self.observations.get("rendered_system_prompt_request_observations", [])),
                "received_monotonic": _time.monotonic(),
            }
            for key in ("request_index", "role", "message_count", "turn_index"):
                if key in arguments:
                    entry[key] = arguments[key]
            if tool_name == OBSERVED_SYSTEM_PROMPT_TOOL:
                turn_list = self.observations.setdefault("rendered_system_prompt_observations", [])
                turn_list.append(entry)
                # The first turn-start observation is the one the executor
                # binds; later ones are visible in the list and refused there.
                if not self.observations.get("rendered_system_prompt_sha256"):
                    self.observations["rendered_system_prompt_sha256"] = entry["sha256"]
            else:
                self.observations.setdefault(
                    "rendered_system_prompt_request_observations", []).append(entry)
            result = {"ok": True, "result": {"recorded": True}, "error": None}
        else:
            bridged = BridgeRequest(
                protocol_version=str(request.get("protocol_version")),
                run_id=str(request.get("run_id", "")),
                branch_id=str(request.get("branch_id", "")),
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                arguments=arguments,
                token=str(request.get("token", "")),
            )
            result = self.executor(bridged)
        return {
            "protocol_version": PROTOCOL_VERSION,
            "tool_call_id": tool_call_id,
            "ok": bool(result.get("ok")),
            "result": result.get("result"),
            "error": result.get("error"),
        }

    def env(self) -> dict[str, str]:
        return {
            "PI_TOOL_BRIDGE_SOCKET": str(self.socket_path),
            "PI_TOOL_BRIDGE_TOKEN": self.token,
            "PI_TOOL_BRIDGE_PROTOCOL_VERSION": PROTOCOL_VERSION,
        }

    def stop(self) -> None:
        self._stop.set()
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        if self._owned_socket_dir is not None:
            shutil.rmtree(self._owned_socket_dir, ignore_errors=True)


def default_executor(tool_bridge: Any, regime_id: str) -> Callable[[BridgeRequest], dict[str, Any]]:
    """Build the default executor from a registered_tools.ToolBridge."""

    def execute(request: BridgeRequest) -> dict[str, Any]:
        result = tool_bridge.execute(
            ToolRequest(name=request.tool_name, arguments=request.arguments, id=request.tool_call_id),
            regime_id=regime_id,
        )
        return {"ok": result.ok, "result": result.result, "error": result.error}

    return execute
