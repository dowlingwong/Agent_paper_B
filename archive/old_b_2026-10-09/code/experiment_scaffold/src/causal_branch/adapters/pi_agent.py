"""Pi production adapter (Round 8 Phase 2, native protocol).

Drives the vendored Pi executable through the native RPC layer (`pi_rpc.py`)
with a per-branch Unix-socket tool bridge: the explicit scientific extension
(`experiment_scaffold/pi_extensions/scientific_tool_bridge.ts`) forwards tool
calls to the Python `ToolBridgeSocketServer`, which owns all policy and
execution. The adapter:

- writes a native `models.json` for the exact provider/model into a fresh
  isolated agent directory;
- passes the registered system prompt via `--system-prompt`;
- disables built-in tools, extensions, skills, context files, prompt templates,
  MCP/network (offline), automatic retry, and automatic compaction;
- waits for native `agent_settled` (quiescence), then requires a real
  `get_entries` leaf ID before checkpointing;
- never reads risk, assignment, hidden evaluation, or sibling state;
- starts the subprocess from a sanitized copy of the parent environment.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, replace
import shutil
import subprocess as _subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from ..model_client import AgentModelEndpoint, endpoint_digest
from ..pi_fork import ForkError, fork_argv_digest, session_file_count, validate_session_id
from ..pi_models import PROVIDER_ID, write_native_models_json
from ..pi_rpc import PiRpcClient, RpcError, RpcProtocolError, RpcTimeout
from ..registered_tools import ToolBridge
from ..substrate_identity import (
    CompletionLedger,
    CompletionRecord,
    SubstrateIdentity,
    completion_from_message,
    provider_error_from_message,
)
from ..tool_socket import (
    OBSERVED_SYSTEM_PROMPT_TOOL,
    ToolBridgeSocketServer,
    default_executor,
)
from ..types import ModelSeedClaim

REGIMES = ("g_0", "g_v", "g_r_f2_fehpo")

#: Wire-level cache control, applied to every model record this adapter writes.
#:
#: Round 5-Titan established the shape of this fix (round10/
#: ROUND5_TITAN_SHARED_HARNESS_AMENDMENT.md section 2): the flag that disables
#: the provider's prompt cache is sent on every request and kept deliberately
#: OUT of the frozen sampling contract, so that `sampling_json_sha256` -- here,
#: the binding record's `sampling_configuration`, which `_load_bound_endpoint`
#: compares to the endpoint file for dict equality -- does not move in order to
#: change something that is not sampling.
#:
#: Why it is needed. The 2026-09-07 live rehearsal reported
#: `cache_hit_observed_while_cache_disabled` on all six branches, 90.9-93.1% of
#: each sibling's prompt served from llama.cpp's prompt cache, against a bound
#: `cache_tolerance` of 0 and a bound `cache_isolation_mode` of "disabled".
#: `--cache-reuse 0` was doing nothing about it: that flag governs reuse of a
#: partially matching prefix AFTER a mismatch, not the per-slot KV cache that a
#: sibling's shared prefix hits. So the isolation was declared, and checked, and
#: never enforced at the provider.
#:
#: Why it lives here and not in `pi_models.native_models_record`, which is the
#: single call site Pi reads. `pi_models.py` is digest-bound by
#: `protocols/hosted_ceiling_v2.yaml` (`pi_model_contract`), a record whose
#: status is `frozen_before_v2_model_requests`. Editing it to serve E0 would
#: move a frozen line of a different, unrelated protocol. This module's digest
#: is bound only by the UNSIGNED candidate
#: `protocols/substrate_selection_v6_devstral_candidate.yaml`
#: (`active_promotion.environment_hashes.adapter`), which no round has yet read
#: outcomes under -- the Round-7 exam records no `pi_agent` anywhere in
#: `evidence/round7-blackwell-grouped/`. Re-recording that digest is
#: bookkeeping; editing the frozen v2 record would not be.
#:
#: Pi merges `samplingParams` verbatim into the request body
#: (third_party/pi/packages/ai/dist/api/openai-completions.js: `Object.assign(
#: params, options.samplingParams)`), which is the same route
#: `chat_template_kwargs` already takes, so this reaches llama-server.
WIRE_CACHE_CONTROL: dict[str, Any] = {"cache_prompt": False}


def wire_endpoint(endpoint: AgentModelEndpoint) -> AgentModelEndpoint:
    """The endpoint as Pi should see it: bound sampling plus cache control.

    The returned copy is used ONLY to write `models.json`. The bound endpoint
    object is left alone, so every comparison and every evidence field that
    reports `requested_sampling` still reports the frozen sampling and nothing
    else.
    """
    return replace(
        endpoint, sampling={**dict(endpoint.sampling or {}), **WIRE_CACHE_CONTROL})


def rendered_system_prompt(system_prompt: Path, working_dir: Path) -> str:
    """The exact custom-prompt string Pi sends for this adapter's launch flags.

    Pi's custom-prompt path
    (`third_party/pi/packages/coding-agent/dist/core/system-prompt.js:13-33`)
    appends, in order: the append-system-prompt section (never set here), the
    project-context block (disabled by `--no-context-files`), the skills section
    (disabled by `--no-skills`), and finally
    ``\\nCurrent working directory: <cwd>\\n`` with the process working directory
    and backslashes normalised to ``/``. This adapter passes no
    ``--append-system-prompt``, so the rendered string is the system-prompt
    file's bytes, decoded as UTF-8, followed by that one line.

    An empty prompt file is refused rather than reconstructed: Pi treats a falsy
    ``customPrompt`` as "use the built-in prompt", so no string derived from the
    file would describe what was sent.
    """
    raw = Path(system_prompt).read_bytes()
    if not raw:
        raise ValueError(
            f"system prompt {system_prompt} is empty; Pi would send its built-in "
            "prompt, which a file-derived reconstruction does not describe")
    cwd = str(Path(working_dir).resolve()).replace("\\", "/")
    return raw.decode("utf-8") + "\nCurrent working directory: " + cwd + "\n"


def rendered_system_prompt_sha256(system_prompt: Path, working_dir: Path) -> str:
    """sha256 of the rendered system prompt as sent for the given launch cwd."""
    return hashlib.sha256(
        rendered_system_prompt(system_prompt, working_dir).encode("utf-8")
    ).hexdigest()


def assert_no_discoverable_append_system_prompt(launch_cwd: Path, agent_dir: Path) -> None:
    """Refuse if Pi could discover an append-system prompt.

    Pi runs `discoverAppendSystemPromptFile()` whenever no
    `--append-system-prompt` is passed, and `--no-context-files` does NOT disable
    it (`third_party/pi/.../core/resource-loader.js:381,819-829`). It checks
    `<cwd>/.pi/APPEND_SYSTEM.md` when the project is trusted, then
    `<agentDir>/APPEND_SYSTEM.md`. Either would make the string Pi sends differ
    from the reconstruction, so it is refused here with the path named.
    """
    for base, relative in ((Path(launch_cwd), Path(".pi") / "APPEND_SYSTEM.md"),
                           (Path(agent_dir), Path("APPEND_SYSTEM.md"))):
        candidate = base / relative
        if candidate.exists():
            raise RuntimeError(
                f"refusing to launch: Pi would discover an append-system prompt at "
                f"{candidate}; the rendered prompt would not match the recorded "
                "reconstruction")


def _tool_socket_server(*, bridge_root: Path, run_id: str, branch_id: str,
                        executor, observations: dict[str, Any],
                        timeout_seconds: float = 120.0) -> ToolBridgeSocketServer:
    """Construct the per-turn/per-handshake bridge server.

    The interception of the rendered-prompt observation lives INSIDE
    `ToolBridgeSocketServer`, so passing the bare executor here is safe by
    construction; the `observations` box is where the digest lands. Both the
    production turn and the capability handshake use this factory, so the two
    cannot drift.
    """
    return ToolBridgeSocketServer(
        socket_dir=bridge_root,
        run_id=run_id,
        branch_id=branch_id,
        executor=executor,
        observations=observations,
        timeout_seconds=timeout_seconds,
    )


# Parent-environment variables always preserved for the Pi subprocess.
_KEEP_PREFIXES = ("PATH", "HOME", "LANG", "LC_", "TMPDIR", "DYLD_", "SSL_", "TERM", "USER")
# Variables removed from the parent environment (provider keys, proxies, Pi
# homes, and experiment-hidden variables).
_REMOVE_TOKENS = (
    "API_KEY", "TOKEN", "SECRET", "PASSWORD", "PROXY", "PI_CODING_AGENT",
    "E0_", "OPENAI_", "ANTHROPIC_", "GOOGLE_", "HF_", "RISK", "ASSIGNMENT",
)


@dataclass
class PiRunResult:
    terminal: str
    entry_id: str | None
    events: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    model_seed_claim: ModelSeedClaim = ModelSeedClaim.REQUESTED_UNVERIFIED
    # The exact argv used to start Pi, so a branch record can bind the session
    # selector (resume vs fork) that produced it.
    argv: list[str] = field(default_factory=list)
    argv_sha256: str = ""
    # sha256 of the RENDERED system prompt actually sent this turn. Distinct by
    # name from the adapter's `system_prompt_sha256` (the prompt FILE digest):
    # this one moves when the rendered string moves, including when only the
    # working-directory line changes.
    rendered_system_prompt_sha256: str = ""
    # The digest Pi itself reported for the string it sent, over the tool bridge
    # (`before_agent_start`). This is an OBSERVATION, not a reconstruction; the
    # executor refuses when it is absent or differs from the reconstruction.
    rendered_system_prompt_sha256_observed: str = ""
    # The ORDERED list of turn-start observations Pi's `before_agent_start`
    # delivered on this turn (normally exactly one), each with its sequence
    # number and receipt time. `..._observed` above is the first of them.
    rendered_system_prompt_observations: list[dict[str, Any]] = field(default_factory=list)
    # Request-level observations from the extension's `before_provider_request`
    # handler (one per provider request), when the extension reports them.
    # Empty when the extension did not observe requests; NEVER inferred from
    # the turn-start observation.
    rendered_system_prompt_request_observations: list[dict[str, Any]] = field(default_factory=list)
    # Every model completion of this turn, with its own identity and usage.
    # `usage` above is the exact component-wise aggregate of these, kept for
    # callers that only need the total.
    ledger: CompletionLedger = field(default_factory=CompletionLedger)
    user_id_sha256: str = ""
    # Provider errors are recorded structurally and are NEVER completions.
    provider_errors: list[dict[str, Any]] = field(default_factory=list)
    budget_exhausted_reason: str = ""

    @property
    def completions(self) -> list[CompletionRecord]:
        return self.ledger.records

    def branch_record(self) -> dict[str, Any]:
        """The auditable branch → completions → usage chain."""
        return {
            "terminal": self.terminal,
            "entry_id": self.entry_id,
            "argv_sha256": self.argv_sha256,
            "user_id_sha256": self.user_id_sha256,
            "rendered_system_prompt_sha256": self.rendered_system_prompt_sha256,
            "rendered_system_prompt_sha256_observed": (
                self.rendered_system_prompt_sha256_observed),
            "rendered_system_prompt_observations": list(self.rendered_system_prompt_observations),
            "rendered_system_prompt_request_observations": list(
                self.rendered_system_prompt_request_observations),
            "prompt_observation_granularity": (
                "turn_start_and_per_request"
                if self.rendered_system_prompt_request_observations else "turn_start"),
            **self.ledger.to_dict(),
        }


class PiAgentAdapter:
    """Production Pi adapter. One instance is a template; each branch spawns a
    fresh Pi process, agent/session directory, and tool-bridge socket."""

    def __init__(
        self,
        *,
        pi_entry: Path,
        endpoint: AgentModelEndpoint,
        system_prompt: Path,
        extension: Path,
        allowed_tools: Sequence[str],
        tool_bridge: ToolBridge | None = None,
    ) -> None:
        self.pi_entry = pi_entry
        self.endpoint = endpoint
        self.system_prompt = system_prompt
        self.extension = extension
        self.allowed_tools = list(allowed_tools)
        self.tool_bridge = tool_bridge
        self.system_prompt_digest = _file_digest(system_prompt)
        self.extension_digest = _file_digest(extension)

    def manifest_identity(self) -> dict[str, Any]:
        return {
            "adapter": "pi_agent",
            "pi_entry": str(self.pi_entry),
            "pi_entry_sha256": _file_digest(self.pi_entry) if self.pi_entry.is_file() else None,
            "endpoint_digest": endpoint_digest(self.endpoint),
            "provider_id": PROVIDER_ID,
            "model_id": self.endpoint.model_id,
            "system_prompt_sha256": self.system_prompt_digest,
            "extension_sha256": self.extension_digest,
            "allowed_tools": self.allowed_tools,
            "model_seed_claim": ModelSeedClaim.REQUESTED_UNVERIFIED.value,
        }

    def rpc_handshake(self, *, agent_dir: Path, session_dir: Path,
                      working_dir: Path, runtime_dir: Path) -> dict:
        """Start Pi, exchange native commands, stop. NO model request.

        The same argv construction, environment sanitisation and tool socket as
        a real turn, so what this proves is that the REAL launch path works --
        not that some simplified one does.
        """
        import subprocess as _subprocess
        for path in (agent_dir, session_dir, working_dir, runtime_dir):
            Path(path).mkdir(parents=True, exist_ok=True)
        # The same construction a real turn uses, so this proves the real launch
        # path rather than a simplified one.
        write_native_models_json(agent_dir, wire_endpoint(self.endpoint))
        bridge_root = (runtime_dir or working_dir) / "bridge"
        # A handshake asks no prompt, so `before_agent_start` never fires and
        # this box is normally empty. It exists so that if a handshake ever does
        # prompt, the observation is recorded here rather than forwarded to the
        # tool bridge.
        observations: dict[str, Any] = {}
        socket_server = _tool_socket_server(
            bridge_root=bridge_root, run_id="round5-titan-handshake",
            branch_id="handshake",
            executor=default_executor(self.tool_bridge, "handshake")
            if self.tool_bridge is not None else _deny_all_executor,
            observations=observations)
        commands: list[dict] = []
        client = None
        try:
            socket_server.start()
            argv = _build_argv(
                self.pi_entry,
                endpoint=self.endpoint,
                session_dir=session_dir,
                system_prompt=self.system_prompt,
                extension=self.extension,
                allowed_tools=self.allowed_tools,
            )
            env = _sanitized_env(agent_dir=agent_dir, **socket_server.env())
            client = PiRpcClient(argv=argv, cwd=working_dir, env=env)
            client.start()
            for command in ({"type": "set_auto_compaction", "enabled": False},
                            {"type": "set_auto_retry", "enabled": False},
                            {"type": "set_thinking_level", "level": "off"}):
                client.request(command)
                commands.append({"type": command["type"], "acknowledged": True})
            node_version = None
            try:
                node_version = _subprocess.run(
                    [argv[0], "--version"], capture_output=True, text=True,
                    timeout=20).stdout.strip()
            except (OSError, _subprocess.SubprocessError):
                pass
            return {"ok": True, "commands": commands,
                    "node_version": node_version,
                    "argv_sha256": fork_argv_digest(argv),
                    "rendered_system_prompt_sha256_observed":
                        observations.get("rendered_system_prompt_sha256")}
        except Exception as exc:  # noqa: BLE001
            diagnostics = getattr(exc, "diagnostics", None)
            if diagnostics is None and client is not None:
                try:
                    diagnostics = client.launch_diagnostics()
                except Exception:  # noqa: BLE001
                    diagnostics = None
            return {"ok": False,
                    "reason": f"{type(exc).__name__}: {str(exc)[:300]}",
                    "commands": commands, "diagnostics": diagnostics}
        finally:
            if client is not None:
                try:
                    client.stop()
                except Exception:  # noqa: BLE001
                    pass
            try:
                socket_server.stop()
            except Exception:  # noqa: BLE001
                pass

    def run_turn(
        self,
        *,
        agent_dir: Path,
        session_dir: Path,
        session_id: str | None = None,
        fork_session: Path | None = None,
        fork_child_session_id: str | None = None,
        working_dir: Path,
        runtime_dir: Path | None,
        prompt: str,
        launch_cwd: Path | None = None,
        run_id: str,
        branch_id: str,
        regime_id: str,
        root_id: str | None = None,
        repetition: int = 0,
        retry_attempt: int = 0,
        turn_index: int = 0,
        user_id: str | None = None,
        identity: SubstrateIdentity | None = None,
        wall_clock_deadline_seconds: float = 300.0,
        max_tool_calls: int | None = None,
        max_completion_tokens: int | None = None,
        completion_sink: Callable[[CompletionRecord], None] | None = None,
    ) -> PiRunResult:
        """Run one prompt to quiescence through native Pi RPC.

        ``completion_sink`` (S4) is called with each completion record as soon
        as its ``message_completed`` event is observed in the live event trace
        (the reader is polled at most every 0.5 s while the turn runs), BEFORE
        identity checks, budget stops or the terminal decide the turn. A kill
        or an exception later in the turn therefore cannot discard a completion
        already produced. Each record is delivered once (by completion id); a
        sink failure propagates, failing the turn closed.

        A `ToolBridgeSocketServer` is started per branch under `runtime_dir`
        (outside the hashed workspace); the Pi extension forwards every tool
        call to it. Returns after `agent_settled` with the real `get_entries`
        leaf ID, or fails closed.

        `launch_cwd` is the directory Pi is STARTED in, which is the string Pi
        writes into the system prompt; it defaults to `working_dir` for callers
        that want the historical behaviour. E0 passes the arm-blind per-root
        directory instead, so the rendered system prompt carries no arm label.

        Exactly one session selector is valid at a time:

        - `session_id` reopens the *same* project session in a fresh process;
        - `fork_session` forks the frozen parent checkpoint into a *distinct*
          child session, which is what an E0 sibling requires.

        Supplying both, or supplying neither when `session_dir` already holds a
        session, fails closed before any model call.
        """
        _validate_session_selector(
            session_dir=session_dir, session_id=session_id, fork_session=fork_session,
            fork_child_session_id=fork_child_session_id,
        )
        # WHERE PI IS STARTED. Pi writes this directory into the system prompt of
        # every request, so it is kept separable from `working_dir` (the
        # workspace the tool bridge owns). E0 passes an arm-blind, per-root
        # `launch_cwd`, so no regime label reaches the model's context, while
        # each arm keeps its own workspace path for restoration and leakage.
        prompt_cwd = Path(launch_cwd) if launch_cwd is not None else Path(working_dir)
        prompt_cwd.mkdir(parents=True, exist_ok=True)
        # Pi would silently prepend a discovered append-system prompt; refuse
        # before any model call, naming the file.
        assert_no_discoverable_append_system_prompt(prompt_cwd, agent_dir)
        # Recorded on the result and carried into the branch record: the digest
        # of the string Pi actually sends, which the prompt-file digest cannot
        # see. It is computed before any model call so an unusable prompt (an
        # empty file) refuses up front rather than at the first completion.
        rendered_digest = rendered_system_prompt_sha256(self.system_prompt, prompt_cwd)
        write_native_models_json(agent_dir, wire_endpoint(self.endpoint))
        observations: dict[str, Any] = {}
        base_executor = (default_executor(self.tool_bridge, regime_id)
                         if self.tool_bridge is not None else _deny_all_executor)
        bridge_root = (runtime_dir or working_dir) / "bridge"
        socket_server = _tool_socket_server(
            bridge_root=bridge_root, run_id=run_id, branch_id=branch_id,
            executor=base_executor, observations=observations)
        events: list[dict[str, Any]] = []
        usage: dict[str, Any] = {}
        # The identity check runs as each completion is added, so a mismatch
        # raises out of `run_turn` and cancels the stage instead of being
        # recorded as a branch outcome.
        ledger = CompletionLedger(identity)
        user_id_sha256 = _user_id_digest(user_id) if user_id else ""

        # CLEANUP STATE AND HELPERS ARE DEFINED BEFORE ANY OPERATION THAT CAN
        # FAIL. They used to be defined partway down the try block, after the
        # first `client.request`, so a setup failure reached the `finally`,
        # called a name that did not exist yet, and the original RpcError was
        # DESTROYED and replaced by UnboundLocalError. `socket_server.start()`
        # and `client.start()` were also outside any try, so a failure between
        # them leaked the socket server.
        _closed: dict[str, Any] = {}
        _held: dict[str, Any] = {}

        def _close() -> list[str]:
            """Stop the RPC client once and return the protocol errors it saw.

            Idempotent; a no-op when the client was never constructed, so it is
            safe from `finally` however early the failure was. It NEVER raises:
            it is called both before choosing a terminal on the success path and
            from `finally` on the failure path, and in neither place may a
            cleanup fault replace the outcome that is already determined. A
            failure to stop is recorded as an event, and the protocol errors are
            still read directly from the client so the terminal decision below
            is made on the best evidence available.
            """
            client = _held.get("client")
            if client is None:
                return []
            if "report" not in _closed:
                try:
                    _closed["report"] = client.stop()
                except Exception as exc:  # noqa: BLE001 - recorded, never raised
                    events.append({"type": "cleanup_failed", "resource": "client",
                                   "error": f"{type(exc).__name__}: {exc}"})
                    try:
                        errors = list(client.protocol_errors())
                    except Exception:  # noqa: BLE001
                        errors = []
                    _closed["report"] = {"protocol_errors": errors}
                found = _closed["report"]["protocol_errors"]
                if found:
                    events.append({"type": "run_failed", "error": "; ".join(found)})
            return list(_closed["report"]["protocol_errors"])

        def _release() -> None:
            """Client and socket cleanup, INDEPENDENTLY attempted.

            Neither may mask the other, and neither may replace the exception
            that is already propagating.
            """
            for what, shutdown in (("client", _close),
                                   ("tool_bridge_socket", socket_server.stop)):
                try:
                    shutdown()
                except Exception as exc:  # noqa: BLE001 - recorded, never raised
                    events.append({"type": "cleanup_failed",
                                   "resource": what,
                                   "error": f"{type(exc).__name__}: {exc}"})

        try:
            socket_server.start()
            argv = _build_argv(
                self.pi_entry,
                endpoint=self.endpoint,
                session_dir=session_dir,
                session_id=session_id,
                fork_session=fork_session,
                fork_child_session_id=fork_child_session_id,
                system_prompt=self.system_prompt,
                extension=self.extension,
                allowed_tools=self.allowed_tools,
            )
            argv_sha256 = fork_argv_digest(argv)
            env = _sanitized_env(agent_dir=agent_dir, **socket_server.env())
            client = PiRpcClient(argv=argv, cwd=prompt_cwd, env=env)
            _held["client"] = client
            client.start()
            client.request({"type": "set_auto_compaction", "enabled": False})
            client.request({"type": "set_auto_retry", "enabled": False})
            client.request({"type": "set_thinking_level", "level": "off"})
            client.request({"type": "prompt", "message": prompt})
            # Wait for quiescence (`agent_settled`) or a failure terminal.
            #
            # A timeout must not destroy what was already observed. Before this
            # was handled, RpcTimeout propagated before the drain below, so every
            # assistant message and tool call buffered during the branch was
            # discarded: a root that had generated five completions was recorded
            # with turns=0 and tool_calls=[]. That undercounted criterion 2
            # malformation (0 malformed over 0 observed) for precisely the
            # candidates that time out, and understated criterion 5 depth.
            #
            # The recovered trace is evidence, never credit. The terminal stays
            # `run_timed_out`, which keeps the root unsettled and nonqualifying;
            # the caller must not score it. Cleanup is the same bounded path as
            # every other exit, in the `finally` below.
            # Every assistant completion is recorded, not just the last one: a
            # tool loop emits several, and keeping only the final message
            # undercounts the branch by every completion before it.
            provider_errors: list[dict[str, Any]] = []
            sunk: set[str] = set()

            def _record_of(message: Mapping[str, Any], completion_index: int) -> CompletionRecord:
                return completion_from_message(
                    message,
                    turn_index=turn_index,
                    completion_index=completion_index,
                    lineage={
                        "root_id": root_id or "",
                        "branch_id": branch_id,
                        "regime_id": regime_id,
                        "repetition": repetition,
                        "retry_attempt": retry_attempt,
                        "user_id_sha256": user_id_sha256 or "",
                        "request_contract_sha256": (
                            identity.request_contract_sha256 if identity else ""
                        ),
                    },
                )

            def _sink(record: CompletionRecord) -> None:
                if completion_sink is None or record.completion_id in sunk:
                    return
                completion_sink(record)
                sunk.add(record.completion_id)

            def _observe_completions(buffered: Sequence[dict[str, Any]]) -> None:
                """Persist completions from the live trace (index = order of distinct ids)."""
                if completion_sink is None:
                    return
                order: list[str] = []
                for event in buffered:
                    if event.get("type") != "message_completed":
                        continue
                    message = event.get("message")
                    if not isinstance(message, dict) or message.get("role") != "assistant":
                        continue
                    if provider_error_from_message(message) is not None:
                        continue
                    try:
                        record = _record_of(message, len(order))
                    except Exception:  # noqa: BLE001 -- malformed: _absorb raises it properly
                        return
                    if record.completion_id not in order:
                        order.append(record.completion_id)
                    _sink(record)

            def _absorb() -> None:
                for event in events:
                    if event.get("type") != "message_completed":
                        continue
                    message = event.get("message")
                    if not isinstance(message, dict) or message.get("role") != "assistant":
                        continue
                    # A provider error is not a completion. Recording it here --
                    # rather than letting it reach the ledger as a message with no
                    # id -- keeps the provider's own status, type and message, and
                    # invents no id, usage or fingerprint to stand in for one.
                    failure = provider_error_from_message(message)
                    if failure is not None:
                        provider_errors.append(failure)
                        continue
                    record = _record_of(message, len(ledger))
                    _sink(record)          # durable before the identity check can raise
                    ledger.add(record)

            def _result(
                terminal_name: str,
                entry_id: str | None,
                *,
                budget_reason: str = "",
            ) -> PiRunResult:
                return PiRunResult(
                    terminal=terminal_name, entry_id=entry_id, events=events,
                    usage=ledger.aggregate_usage().to_dict(),
                    model_seed_claim=ModelSeedClaim.REQUESTED_UNVERIFIED,
                    argv=list(argv), argv_sha256=argv_sha256, ledger=ledger,
                    user_id_sha256=user_id_sha256,
                    rendered_system_prompt_sha256=rendered_digest,
                    rendered_system_prompt_sha256_observed=str(
                        observations.get("rendered_system_prompt_sha256") or ""),
                    rendered_system_prompt_observations=list(
                        observations.get("rendered_system_prompt_observations") or []),
                    rendered_system_prompt_request_observations=list(
                        observations.get("rendered_system_prompt_request_observations") or []),
                    provider_errors=list(provider_errors),
                    budget_exhausted_reason=budget_reason,
                )

            def _budget_stop_reason(
                buffered: Sequence[dict[str, Any]],
            ) -> str | None:
                if max_tool_calls is not None:
                    tool_calls = sum(
                        1 for event in buffered
                        if event.get("type") == "tool_started")
                    if tool_calls >= max_tool_calls:
                        return f"tool_calls_{tool_calls}_reached_{max_tool_calls}"
                if max_completion_tokens is not None:
                    completion_tokens = 0
                    for event in buffered:
                        if event.get("type") != "message_completed":
                            continue
                        message = event.get("message")
                        if not isinstance(message, Mapping) or message.get("role") != "assistant":
                            continue
                        usage_block = message.get("providerUsage")
                        if not isinstance(usage_block, Mapping):
                            continue
                        value = usage_block.get("completion_tokens")
                        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                            completion_tokens += value
                    if completion_tokens >= max_completion_tokens:
                        return (
                            f"completion_tokens_{completion_tokens}_reached_"
                            f"{max_completion_tokens}")
                return None

            try:
                def _observe_and_budget(buffered: Sequence[dict[str, Any]]) -> str | None:
                    _observe_completions(buffered)
                    return _budget_stop_reason(buffered)

                terminal = client.wait_terminal(
                    timeout=wall_clock_deadline_seconds,
                    stop_reason=_observe_and_budget,
                )
            except RpcTimeout:
                # Drain what the branch already emitted, absorb it so token usage
                # and per-completion identity checks still apply, and return a
                # TIMED-OUT terminal. Identity remains enforced: a mismatch here
                # is still stage-fatal rather than being swallowed by the timeout.
                try:
                    events.extend(client.drain_events())
                except Exception:  # noqa: BLE001 -- a drain failure must not mask the timeout
                    events.append({"type": "run_failed",
                                   "error": "event drain failed after timeout"})
                _absorb()
                return _result("run_timed_out", None)

            events.extend(client.drain_events())
            _absorb()
            usage = ledger.aggregate_usage().to_dict()

            if terminal["type"] == "budget_exhausted":
                return _result(
                    "run_budget_exhausted", None,
                    budget_reason=str(terminal.get("reason") or "budget_exhausted"),
                )

            # A branch that hit a provider error did not settle, whatever Pi's
            # quiescence signal says: no completion was produced for that turn.
            if provider_errors:
                return _result("run_provider_error", None)
            if terminal["type"] == "extension_error":
                return _result("run_failed", None)
            if terminal["type"] != "settled":
                return _result(terminal["type"], None)
            # Quiescence reached: require a real leaf ID from native get_entries.
            entries_response = client.request({"type": "get_entries"})
            leaf_id = (entries_response.get("data") or {}).get("leafId")
            entries = (entries_response.get("data") or {}).get("entries") or []
            if not leaf_id or not any(
                str(entry.get("id")) == leaf_id for entry in entries
            ):
                raise RpcProtocolError("get_entries returned no valid leafId")
            # A protocol violation may still be in flight: a duplicate terminal
            # that arrives AFTER the first was consumed lands while nothing is
            # waiting. Stop the client here, before deciding the terminal, so
            # such an error changes the TERMINAL and not merely the event list.
            # Appending `run_failed` to `events` while returning
            # `terminal="settled"` left every consumer that reads `terminal` --
            # which is the authoritative field for the soak and for E0 -- seeing
            # a clean branch for a violated exchange.
            if _close():
                return _result("run_failed", leaf_id)
            return _result("settled", leaf_id)
        finally:
            _release()

    # -- failure translation ---------------------------------------------------

    @staticmethod
    def to_terminal_category(terminal: str) -> tuple[str, str]:
        mapping = {
            "settled": ("not_terminal", ""),
            "run_failed": ("invalid_scientific_output", "agent_run_failed"),
            "run_timed_out": ("infrastructure_timeout", "agent_timed_out"),
            "run_provider_error": ("infrastructure_provider_error", "provider_error"),
            "run_budget_exhausted": ("budget_exhaustion", "root_budget_exhausted"),
            "run_aborted": ("abstention", "agent_aborted"),
        }
        return mapping.get(terminal, ("unresolved_termination", terminal))


def _deny_all_executor(request: Any) -> dict[str, Any]:
    return {"ok": False, "result": None, "error": "no tool bridge configured"}


def _validate_session_selector(
    *,
    session_dir: Path,
    session_id: str | None,
    fork_session: Path | None,
    fork_child_session_id: str | None,
) -> None:
    """Fail closed on an ambiguous session selector, before any model call.

    `--session-dir` chooses storage, not identity. Without an explicit selector
    Pi is free to create a *new* JSONL beside the one we meant to open, which is
    exactly how a "restored" branch silently becomes a fresh agent.

    The two modes are mutually exclusive: `session_id` reopens the same session,
    `fork_session` (with its own frozen child ID) branches a distinct one.
    """
    if session_id is not None and fork_session is not None:
        raise ForkError(
            "session_id and fork_session are mutually exclusive: reopen the same session "
            "or fork a distinct child, never both"
        )
    if session_id is not None:
        validate_session_id(session_id)
        return
    if fork_session is not None:
        if fork_child_session_id is None:
            raise ForkError(
                "fork_session requires an explicit frozen fork_child_session_id; an "
                "auto-generated child ID is not reproducible across a resumed client"
            )
        validate_session_id(fork_child_session_id)
        if not fork_session.is_file():
            raise ForkError(f"fork_session does not exist: {fork_session}")
        if session_dir.is_dir() and fork_session.resolve().parent == session_dir.resolve():
            raise ForkError(
                f"fork_session {fork_session} lives inside the child session dir {session_dir}: "
                "a child must fork from the parent's own session directory"
            )
        if session_file_count(session_dir):
            raise ForkError(
                f"fork target {session_dir} already holds a session; a fork must land in a "
                "fresh child session directory"
            )
        return
    if fork_child_session_id is not None:
        raise ForkError("fork_child_session_id was supplied without fork_session")
    if session_file_count(session_dir):
        raise ForkError(
            f"{session_dir} already holds a session but no explicit selector was supplied; "
            "pass session_id to reopen it or fork_session to branch from it"
        )



# The vendored Pi entry carries a `#!/usr/bin/env node` shebang. On this host
# `node` is not on PATH at all, so exec'ing the .js file directly fails before
# Pi runs a single line -- which surfaced only as "Pi process exited before
# responding". The interpreter is therefore resolved EXPLICITLY and recorded,
# in the same spirit as the CUDA and compiler toolchain: never inherited from
# whatever the shell happens to have.
PINNED_NODE = Path.home() / ".local/node-v22.19.0/bin/node"


#: The version the registered pin names. A PATH fallback that happens to be a
#: different build is not the pinned runtime, however similar it looks.
PINNED_NODE_VERSION = "v22.19.0"


def node_provenance(path: str) -> dict[str, str]:
    """Where this interpreter came from, so a launch can record it.

    `source` is one of `explicit_env`, `pinned_path`, `path_fallback`. Only the
    first two satisfy the pin; `path_fallback` is recorded so it can never
    silently pass for one.
    """
    resolved = Path(path)
    if str(resolved) == str(PINNED_NODE):
        source = "pinned_path"
    elif any(os.environ.get(n) for n in ("R5_PI_NODE", "NODE_BIN")):
        source = "explicit_env"
    else:
        source = "path_fallback"
    version = ""
    try:
        version = _subprocess.run([str(resolved), "--version"], capture_output=True,
                                  text=True, timeout=30).stdout.strip()
    except (OSError, _subprocess.SubprocessError):
        version = ""
    return {"path": str(resolved), "source": source, "version": version,
            "satisfies_pin": str(source in ("pinned_path", "explicit_env")
                                  and version == PINNED_NODE_VERSION)}


def require_pinned_node() -> str:
    """The interpreter for a QUALIFYING launch. Refuses a PATH fallback.

    `resolve_node_executable` keeps its fallback because development and the
    non-qualifying rehearsal legitimately run on whatever Node is present. A
    qualifying run may not: a PATH fallback is whatever the shell happened to
    have, its digest enters `environment_version`, and it can change between the
    run that qualified the deployment and the run that uses it. So the pin is
    satisfied only by the registered path or by an explicit R5_PI_NODE/NODE_BIN,
    and only at the registered version.
    """
    found = resolve_node_executable()
    provenance = node_provenance(found)
    if provenance["source"] == "path_fallback":
        raise RuntimeError(
            f"refusing a PATH-resolved Node for a qualifying launch: {found} was "
            f"found on PATH, not at the pinned {PINNED_NODE} and not named by "
            "R5_PI_NODE or NODE_BIN. A pin that a PATH lookup can satisfy is not "
            "a pin. Install the registered runtime or set the variable explicitly.")
    if provenance["version"] != PINNED_NODE_VERSION:
        raise RuntimeError(
            f"Node at {found} reports {provenance['version']!r}, not the "
            f"registered {PINNED_NODE_VERSION!r}; a version change is a protocol "
            "decision, not a substitution to make at launch time")
    return found


def resolve_node_executable() -> str:
    """The Node that will run Pi. Explicit, checked, and reported if absent.

    Round-4 §2.7 (c): two variables named the same interpreter and neither read
    the other. This resolver took `R5_PI_NODE`, while the executor's environment
    digest (`e0_executor._node_digest`) took `NODE_BIN`, so a host that set one
    satisfied half the run and got an opaque refusal from the other half. Both
    are now accepted here, in that order, and `_node_digest` accepts both too.
    Setting them to different executables is refused rather than resolved.
    """
    candidates = [(name, os.environ.get(name)) for name in ("R5_PI_NODE", "NODE_BIN")]
    resolved: dict[str, str] = {}
    for name, value in candidates:
        if not value:
            continue
        path = Path(value)
        if path.is_dir():
            path = path / "node"
        if path.is_file():
            resolved[name] = str(path)
    if len(set(resolved.values())) > 1:
        raise RuntimeError(
            "R5_PI_NODE and NODE_BIN name different Node executables "
            f"({resolved}); set one, or set both to the same path")
    if resolved:
        return next(iter(resolved.values()))
    if PINNED_NODE.is_file():
        return str(PINNED_NODE)
    found = shutil.which("node")
    if found:
        return found
    raise RuntimeError(
        "no Node executable: neither R5_PI_NODE nor NODE_BIN is set to one, the pinned "
        f"{PINNED_NODE} is absent, and `node` is not on PATH")


def _build_argv(
    pi_entry: Path,
    *,
    endpoint: AgentModelEndpoint,
    session_dir: Path,
    session_id: str | None = None,
    fork_session: Path | None = None,
    fork_child_session_id: str | None = None,
    system_prompt: Path,
    extension: Path,
    allowed_tools: Sequence[str],
) -> list[str]:
    # The vendored Pi entry is JavaScript and MUST be run by the pinned Node
    # (see resolve_node_executable). A non-.js entry is only ever a test fake
    # with its own shebang -- fake_pi.py is Python -- and prefixing Node to it
    # makes the child die in the CJS module loader before it runs a line, which
    # surfaces as the same opaque "Pi process exited before responding" this
    # pin was introduced to remove.
    #
    # The real path is deliberately untouched: for a .js entry argv is
    # byte-identical to before, so every bound `argv_sha256` in existing branch
    # records still verifies.
    launcher = ([resolve_node_executable()] if pi_entry.suffix == ".js"
                else [])
    argv = [
        *launcher,
        str(pi_entry),
        "--mode", "rpc",
        "--provider", PROVIDER_ID,
        "--model", endpoint.model_id,
        "--system-prompt", str(system_prompt.resolve()),
        "--session-dir", str(session_dir),
        "--no-skills",
        "--no-extensions",
        "--no-context-files",
        "--no-prompt-templates",
        "--no-builtin-tools",
        "--offline",
        "--extension", str(extension.resolve()),
        "--tools", ",".join(allowed_tools),
    ]
    # An explicit stable ID makes a fresh Pi process open the same project
    # session instead of silently creating another JSONL in `session_dir`.
    # The first invocation creates the ID; later invocations resume it.
    if session_id is not None:
        argv.extend(["--session-id", session_id])
    # An explicit fork is a different operation: Pi's `SessionManager.forkFrom`
    # writes a NEW session whose header records `parentSession` and whose entries
    # are the parent's. `--session-id` here names the frozen child, and Pi
    # refuses if that ID already exists — so a sibling can never silently reuse
    # another sibling's session.
    if fork_session is not None:
        argv.extend(["--fork", str(fork_session.resolve())])
        argv.extend(["--session-id", str(fork_child_session_id)])
    return argv


def _sanitized_env(agent_dir: Path, **bridge_env: str) -> dict[str, str]:
    """A sanitized copy of the parent environment plus the fresh agent dir and
    the per-branch tool-bridge variables."""
    env: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(upper.startswith(prefix) for prefix in _KEEP_PREFIXES):
            env[key] = value
        elif any(token in upper for token in _REMOVE_TOKENS):
            continue
        else:
            env[key] = value
    env["PI_CODING_AGENT_DIR"] = str(agent_dir)
    # Qualification has exactly one time stop: the Python-side root safety
    # deadline. Pi's independent five-minute HTTP idle timeout would otherwise
    # turn a slow stream into a provider error and therefore an R-gate failure.
    env["PI_HTTP_IDLE_TIMEOUT_MS"] = "0"
    env.update(bridge_env)
    return env


def _user_id_digest(user_id: str) -> str:
    """Evidence records the digest, never the API `user_id` value itself."""
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
