"""The live Stage-B execution path, around the production Pi+D7 harness.

This module is imported ONLY from the live branch of
``scripts/run_round5_titan_exam.py``, after readiness is green, an explicit
author authorization exists, Stage A has passed and every digest is bound. Plan
mode never imports it, which is what makes ``--plan`` structurally incapable of
starting a server, a model, a Pi process, or a root rather than merely
disinclined to.

It reuses the production adapter, tool bridge, adjudicator and evidence code
without changing their scientific semantics. What it adds is Round-5 specific
and mechanical: per-device server-lifetime accounting for GPU-hours, the frozen
topology launch line, and the two evidence rules the Round-3 diagnostic packet
paid for --

**Drain before propagating a timeout.** ``RpcTimeout`` propagated out of
``run_turn`` before the event drain, so a root that produced five completions and
eight tool calls was recorded with ``turns=0`` and ``tool_calls=[]``. Because
malformation is a rate over OBSERVED calls, that systematically flattered exactly
the candidates that time out while understating their depth. Draining first is
outcome-independent: the root still times out, still fails to settle, still has
no submission, and malformation can only go UP.

**A provider error stays a provider error.** It is recorded with the provider's
own HTTP status and message rather than a downstream symptom, is not adjudicated,
and never receives a fabricated completion id.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from causal_branch.d7_registered_commands import d7_command_handlers
from causal_branch.d7_adjudicator import TERMINAL_UNRESOLVED
from causal_branch.round5_titan_stage_a_acquisition import erase_slot
from causal_branch.round5_titan_exam import (
    MONITORING_UNKNOWN,
    exam_prompt_blockers,
    foreign_process_blockers,
    runtime_schema_blockers,
    server_environment,
    CONTEXT_TOKENS,
    MID_ARM_MIN_PROBE_INTERVAL_SECONDS,
    ENABLE_THINKING,
    OUTPUT_CEILING_TOKENS,
    ROOT_SAFETY_TIMEOUT_SECONDS,
    ROOT_WALL_RAIL_SECONDS,
    ROOT_MAX_TOOL_CALLS,
    ROOT_MAX_COMPLETION_TOKENS,
    TEMPERATURE,
    topology_profile,
)

ALLOWED_TOOLS = ("read_artifact", "write_artifact", "edit_artifact",
                 "run_registered_command", "submit_candidate")

# A tool call is MALFORMED when the bridge cannot accept it as a call at all:
# an invented tool, a tool outside the allowlist, or arguments failing schema
# validation. A well-formed call whose operation then fails is a capability
# observation, not malformation. Counting `tool_completed.is_error` conflated the
# two and reported 48% malformation for a model whose calls were all well formed.
_MALFORMATION_MARKERS = ("unknown tool:", "tool not allowlisted:",
                         "missing required argument", "invalid argument", "schema")


def classify_tool_error(message: str) -> str:
    lowered = str(message).lower()
    return ("malformed" if any(marker in lowered for marker in _MALFORMATION_MARKERS)
            else "execution_error")


@dataclass
class ExamRootResult:
    root_id: str
    template_id: str
    worker: int
    devices: list[int]
    server_port: int
    topology: str
    started_at_utc: str = ""
    finished_at_utc: str = ""
    wall_seconds: float = 0.0
    rail_bound: bool = False
    #: Deterministic, contention-invariant eligibility signal. True when the
    #: root exhausted its tool-call or completion-token budget. Unlike
    #: `rail_bound` this cannot be caused by a neighbour job or a slower card.
    budget_exhausted: bool = False
    budget_exhausted_reason: str = ""
    settled: bool = False
    turns: int = 0
    tool_calls: int = 0
    tool_call_names: list[str] = field(default_factory=list)
    malformed_tool_calls: int = 0
    tool_execution_errors: int = 0
    submission_present: bool = False
    submission_valid: bool = False
    success: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    peak_context_tokens: int = 0
    timed_out: bool = False
    partial_events_retained: bool = False
    provider_error: dict[str, Any] | None = None
    adjudication: dict[str, Any] | None = None
    invalidity_reason: str | None = None
    entry_id: str | None = None
    single_session: bool = True
    isolation_ok: bool = True
    retained_scratch: str | None = None
    error: str | None = None
    # Populated only when a hosted caller explicitly requests auditable
    # completion accounting.  The local Stage-B path leaves this empty, so its
    # execution and scoring semantics are unchanged.
    provider_completions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GpuMonitoringUnavailable(RuntimeError):
    """GPU monitoring evidence is unavailable, failed, malformed or incomplete.

    Distinct from contamination and from a clean host. The occupancy canary and
    the mid-arm probe both assert something about the cards; when the evidence
    those assertions rest on cannot be obtained, the honest answer is neither
    "contaminated" nor "clear" but MONITORING_UNKNOWN -- a shared environmental
    nonverdict that stops the run and blames no candidate.

    Deliberately NOT the same thing as an empty-but-successful process table: a
    card that genuinely has no processes on it is evidence, and reads as empty.
    """


def sample_occupancy(topology: str,
                     owned_pids: Sequence[int] = ()) -> list[dict[str, Any]]:
    """One NVML-style sample per card, for the pre-stage occupancy canary.

    Samples EVERY card on the host, including the ones the exam does not hold.
    That is deliberate on a shared machine and it is not what the canary
    verdict is computed from -- `occupancy_blockers(devices=...)` narrows the
    verdict to the leased cards. The wider sample is recorded because the
    neighbourhood is the thing that moves the leased cards' clocks: they share
    the chassis power and cooling budget, so a run whose GPU-hour denominator
    drifted needs the neighbours' load, power draw and temperature at the time
    in evidence rather than reconstructed afterwards from nothing.

    Clock, power and temperature are read here for the same reason. They cost
    one extra field in the same `nvidia-smi` call and they are the only record
    that distinguishes "this model decoded slowly" from "this card was throttled
    while this model ran".

    `owned_pids` is the recorded owned process set -- this process and the
    lease's holder. `explained_by_owned_server` was a hardcoded `False`, and it
    is the field the occupancy canary consults before excusing a card's
    baseline memory. Under `vram_holder_only`, where the exam's own holder sits
    on the leased cards by design, that made every Stage B unstartable: the
    canary reported the manager's own holder as contamination.

    The explanation is POSITIVE, never an absence. A card is explained only when
    at least one owned PID is visible on it AND every visible compute PID is
    owned. An empty pid list explains nothing, so memory or utilisation with no
    visible owner still blocks; a single foreign PID makes the subset test fail,
    so mixed cards still block. Malformed ownership evidence -- a pid list that
    is not integers -- is treated as unexplained rather than trusted.
    """
    query = ("index,uuid,memory.used,utilization.gpu,clocks.current.sm,"
             "power.draw,power.limit,temperature.gpu")
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        # This returned [] -- no samples -- which every consumer reads as "no
        # card has anything to complain about", i.e. clean. Silence is not the
        # only alternative to inventing contamination: unavailable monitoring is
        # its own state and must be said out loud. MONITORING_UNKNOWN is a
        # SHARED ENVIRONMENTAL nonverdict, never a candidate's fault and never a
        # clean sample.
        raise GpuMonitoringUnavailable(
            f"gpu inventory query failed: {exc}") from exc
    if out.returncode != 0:
        raise GpuMonitoringUnavailable(
            f"gpu inventory query exited {out.returncode}: "
            f"{(out.stderr or '').strip()[:200]}")
    # Every context type, not just COMPUTE, and fail closed. This used
    # `--query-compute-apps` and swallowed failures with `pass`, so a foreign
    # GRAPHICS context on a leased card was invisible to the pre-root canary and
    # to the mid-arm probe, and a failed query looked like an empty card.
    #
    # Both queries now raise rather than degrade to silence: the inventory query
    # above raises GpuMonitoringUnavailable, and this process query raises
    # GpuProcessQueryFailure. Neither can reach a caller as an empty sample
    # list, because "we saw nothing" and "we could not look" are different
    # claims about the machine and only one of them lets a scored root proceed.
    from causal_branch.round5_titan_stage_a_acquisition import (
        gpu_processes_by_uuid,
    )
    processes = gpu_processes_by_uuid()

    try:
        owned = {int(pid) for pid in owned_pids}
    except (TypeError, ValueError):
        # Ownership evidence we cannot parse explains nothing.
        owned = set()

    samples: list[dict[str, Any]] = []
    for line in out.stdout.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 4:
            continue
        def optional(position: int) -> float | None:
            # `nvidia-smi` prints "[N/A]" for a field a card does not expose.
            # Recording None is right; recording 0.0 would read as a card at
            # idle clocks, which is a claim about the machine.
            try:
                return float(parts[position])
            except (IndexError, ValueError):
                return None

        samples.append({
            "device": int(parts[0]),
            "compute_pids": processes.get(parts[1], []),
            "memory_used_mib": float(parts[2]),
            "utilisation_percent": float(parts[3]),
            "sm_clock_mhz": optional(4),
            "power_draw_watts": optional(5),
            "power_limit_watts": optional(6),
            "temperature_c": optional(7),
            "explained_by_owned_server": _owned_alone(
                processes.get(parts[1], []), owned),
        })
    if not samples:
        # A successful query that yields no card is incomplete evidence about a
        # host we know has cards, not a quiet host.
        raise GpuMonitoringUnavailable(
            "gpu inventory query returned no cards")
    return samples


def _owned_alone(compute_pids: Sequence[int], owned: set[int]) -> bool:
    """True only when the card carries owned processes and nothing else.

    Positively established: at least one owned PID visible, and every visible
    PID owned. Absence of evidence is never an explanation.
    """
    try:
        seen = {int(pid) for pid in compute_pids}
    except (TypeError, ValueError):
        return False
    return bool(seen) and bool(owned) and seen <= owned


def gpu_used_mib(index: int) -> float:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits", "-i", str(index)],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return -1.0


def _endpoint(port: int, model_id: str, *, timeout_seconds: float = 120.0):
    from causal_branch.model_client import AgentModelEndpoint
    return AgentModelEndpoint(
        provider="openai-compatible", base_url=f"http://127.0.0.1:{port}/v1",
        api_key="local", model_id=model_id, context_ceiling=CONTEXT_TOKENS,
        output_ceiling=OUTPUT_CEILING_TOKENS,
        sampling={"temperature": TEMPERATURE,
                  "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING}},
        timeout_seconds=float(timeout_seconds), purpose="profiling", qualifying=False,
    )


#: How long a server may take to come up. Raised from 420 s: a 35B MoE loading
#: 21 GB from a cold page cache on a card whose clocks are down because a
#: neighbour is busy can take longer than seven minutes, and a server that
#: failed to start is a SHARED failure that stops the whole panel -- so this
#: timeout being tight does not cost one row, it costs the night. A server that
#: is genuinely broken exits early and is caught by the process check, not by
#: this bound.
SERVER_START_TIMEOUT_SECONDS = 1800.0


def wait_healthy(port: int, process: subprocess.Popen,
                 timeout: float = SERVER_START_TIMEOUT_SECONDS) -> bool:
    import urllib.request
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if json.loads(response.read().decode()).get("status") == "ok":
                    return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    return False


def stop(process: subprocess.Popen) -> dict[str, Any]:
    """Signal the whole process GROUP, wait, escalate, then report.

    Servers start with `start_new_session=True` and llama-server forks, so
    terminating only the parent leaves workers holding VRAM -- the orphaned-VRAM
    failure that stranded the earlier funnels. Stage A already signalled the
    group; Stage B did not, and the two must obey one contract or the longer of
    the two runs is the one that leaks.
    """
    record: dict[str, Any] = {"pid": process.pid}
    if process.poll() is not None:
        record["state"] = "already_exited"
        record["returncode"] = process.returncode
        return record
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        record["signalled"] = "process_group"
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.terminate()
            record["signalled"] = "process_only_group_unavailable"
        except OSError:
            record["signalled"] = "none"
    try:
        process.wait(timeout=30)
        record["state"] = "terminated"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            process.kill()
        try:
            process.wait(timeout=10)
            record["state"] = "killed"
        except subprocess.TimeoutExpired:
            record["state"] = "unreaped"
    record["returncode"] = process.returncode
    return record


def verify_release(devices: Sequence[int], *, settle_seconds: float = 3.0,
                   baseline_mib: Mapping[str, float] | None = None,
                   ) -> dict[str, Any]:
    """Confirm every card came back.

    A stopped server that kept its VRAM is indistinguishable, to the next
    candidate, from one that is still running.
    """
    time.sleep(settle_seconds)
    residual = {str(device): gpu_used_mib(int(device)) for device in devices}
    baseline = dict(baseline_mib or {})
    clean = all(
        value <= float(baseline.get(device, 0.0)) + 64.0
        for device, value in residual.items() if value >= 0)
    return {"residual_memory_used_mib": residual,
            "release_baseline_memory_used_mib": baseline,
            "vram_returned_to_baseline": clean}


def execute_stage_b(
    *,
    candidate: str,
    spec: Mapping[str, Any],
    registry: Mapping[str, Any],
    plan: Mapping[str, Any],
    model_root: Path,
    out_dir: Path,
    retain_scratch: bool = True,
    wall_clock_deadline_seconds: float = ROOT_WALL_RAIL_SECONDS,
    rail_diagnostic_seconds: float | None = None,
    deterministic_root_budget: bool = False,
    lease_holder_pids: Sequence[int] = (),
) -> dict[str, Any]:
    """Run the frozen 30 roots for one candidate on the declared topology.

    Every participating device's interval runs from the moment its server is
    launched to the moment it is confirmed stopped, so GPU-hours charge held-but-
    idle time. A card holding a model is unavailable whether or not it is busy,
    and a two-card candidate that only paid for busy time would be compared at a
    price it did not pay.
    """
    from causal_branch.adapters.pi_agent import PiAgentAdapter
    from causal_branch.d7_adjudicator import (
        ADJUDICATOR_VERSION, TERMINAL_VALIDATED, adjudicate_d7, load_hidden_set,
    )
    from causal_branch.pi_fork import sole_session_file
    from causal_branch.registered_tools import ToolBridge
    from causal_branch.substrate_identity import (
        SubstrateIdentity, SubstrateIdentityMismatch,
    )

    runtime = registry.get("runtime") or {}
    # The task, verified BEFORE a single server starts or a single root record
    # exists. A binding failure here is a shared blocker that stops the launch;
    # it must never surface later as per-root harness errors that arithmetic
    # then mistakes for candidate performance.
    exam_prompt = load_frozen_exam_prompt(registry)
    llama_server = Path(str(runtime["llama_server"]))
    model = model_root / str(spec["filename"])
    dataset_root = Path(str(runtime["dataset_root"]))
    hidden_root = Path(str(runtime["hidden_table_root"]))

    scratch = Path(tempfile.mkdtemp(prefix=f"r5-titan-{candidate}-"))
    processes: list[subprocess.Popen] = []
    device_intervals: list[dict[str, Any]] = []
    peak_vram = 0.0
    results: list[ExamRootResult] = []
    bound_devices = sorted({int(device) for entry in plan["servers"]
                            for device in entry["devices"]})
    release_baseline = {
        str(device): gpu_used_mib(device) for device in bound_devices}

    try:
        for entry in plan["servers"]:
            log = out_dir / f"{candidate}-server-{entry['server']}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            handle = log.open("w", encoding="utf-8")
            started = time.monotonic()
            # Same confinement as Stage A, applied uniformly: one device
            # namespace per server. A comparison whose Stage B is not confined
            # the way its Stage A was is not a comparison.
            env = {**os.environ, **server_environment(
                entry["devices"],
                visibility_tokens=entry.get("device_uuids"))}
            # The server REFUSES to start if --slot-save-path names a directory
            # that does not exist ("not a directory"), and that path is what
            # makes the root-boundary slot erase possible at all.
            argv_list = list(entry["argv"])
            if "--slot-save-path" in argv_list:
                slot_dir = Path(argv_list[argv_list.index("--slot-save-path") + 1])
                slot_dir.mkdir(parents=True, exist_ok=True)
            process = subprocess.Popen(
                argv_list, stdout=handle,
                stderr=subprocess.STDOUT, start_new_session=True, env=env)
            processes.append(process)
            for device in entry["devices"]:
                device_intervals.append({
                    "device": int(device), "server": int(entry["server"]),
                    "start_monotonic": started, "end_monotonic": started,
                })
        healthy = [wait_healthy(entry["port"], processes[index])
                   for index, entry in enumerate(plan["servers"])]
        if not all(healthy):
            raise HarnessInfrastructureError(
                f"server_failed_to_start: healthy={healthy}")
        peak_vram = max(
            (gpu_used_mib(device) for entry in plan["servers"]
             for device in entry["devices"]), default=0.0)

        port_for_worker = {int(entry["server"]): int(entry["port"])
                           for entry in plan["servers"]}
        def run_one(assignment: Mapping[str, Any]) -> ExamRootResult:
            worker_port = port_for_worker[int(assignment["worker"])]
            # ROOT BOUNDARY. Clear the slot so this root does not begin on the
            # previous root's KV state. Same call, same slot API, same criterion
            # as the Stage-A fresh-cache probe -- one machinery, both stages.
            erase_slot(worker_port)
            return _run_exam_root(
                assignment=assignment,
                port=worker_port,
                candidate=candidate, dataset_root=dataset_root,
                hidden_root=hidden_root, scratch=scratch,
                retain_scratch=retain_scratch,
                PiAgentAdapter=PiAgentAdapter, ToolBridge=ToolBridge,
                SubstrateIdentity=SubstrateIdentity,
                SubstrateIdentityMismatch=SubstrateIdentityMismatch,
                sole_session_file=sole_session_file,
                adjudicate_d7=adjudicate_d7, load_hidden_set=load_hidden_set,
                TERMINAL_VALIDATED=TERMINAL_VALIDATED,
                endpoint_factory=(
                    lambda endpoint_port, model_id: _endpoint(
                        endpoint_port, model_id,
                        # The outer root safety stop must win this race.  If the
                        # HTTP client expires at the same instant, a wedged root
                        # can be misclassified as a provider error and trip R.
                        timeout_seconds=(
                            float(wall_clock_deadline_seconds) + 60.0))),
                registry=registry,
                exam_prompt=exam_prompt,
                # The caller owns the round-specific time policy. Completed
                # rounds retain their frozen 360 s rail; Round 7 passes its
                # 5,400 s safety stop and keeps 360 s only as a diagnostic.
                wall_clock_deadline_seconds=float(wall_clock_deadline_seconds),
                rail_diagnostic_seconds=rail_diagnostic_seconds,
                max_tool_calls=(ROOT_MAX_TOOL_CALLS
                                if deterministic_root_budget else None),
                max_completion_tokens=(ROOT_MAX_COMPLETION_TOKENS
                                       if deterministic_root_budget else None),
            )

        # Everything holding a bound card that is OURS: this process, and every
        # llama-server we started. Without them the probe would report our own
        # servers as the neighbour and void every arm on its first check.
        owned_pids = [os.getpid(), *lease_holder_pids,
                      *(process.pid for process in processes)]
        def occupancy_probe() -> list[str]:
            # Monitoring failure is reported, never swallowed. The old code
            # returned [] here -- indistinguishable from "the cards are clean" --
            # on the reasoning that inventing contamination would void a clean
            # arm. That reasoning is right about not inventing contamination and
            # wrong about the remedy: the arm must not proceed on evidence we do
            # not have. MONITORING_UNKNOWN is shared and environmental, so it
            # stops the run without blaming the candidate.
            from causal_branch.round5_titan_stage_a_acquisition import (
                GpuProcessQueryFailure,
            )
            try:
                samples = sample_occupancy(str(plan["topology"]),
                                           owned_pids=owned_pids)
            except (GpuMonitoringUnavailable, GpuProcessQueryFailure) as exc:
                return [f"{MONITORING_UNKNOWN}:{exc}"]
            return foreign_process_blockers(
                samples, owned_pids=owned_pids, devices=bound_devices)

        by_root, started_ids, cancelled_ids, failures = _run_schedule(
            plan["schedule"], run_one, occupancy_probe=occupancy_probe)
        if failures:
            primary = failures[0]
            if isinstance(primary, StageBContaminated):
                primary.started_roots = list(started_ids)
                primary.cancelled_roots = list(cancelled_ids)
                primary.completed_roots = sorted(by_root)
                raise primary
            if not isinstance(primary, HarnessInfrastructureError):
                raise primary
            # The lists ride on the exception so the runner's shared-failure
            # artifact can say exactly how far the run got: started roots,
            # cancelled (queued, never invoked), and completed-before-stop.
            primary.started_roots = list(started_ids)
            primary.cancelled_roots = list(cancelled_ids)
            primary.completed_roots = sorted(by_root)
            raise primary
        # Input order preserved so the artifact is reproducible, and no
        # candidate behaviour stops the exam early.
        results = [by_root[str(assignment["root_id"])]
                   for assignment in plan["schedule"]]
    finally:
        cleanup = [stop(process) for process in processes]
        ended = time.monotonic()
        for interval in device_intervals:
            interval["end_monotonic"] = ended
        release = verify_release(
            sorted({int(device) for entry in plan["servers"]
                    for device in entry["devices"]}),
            baseline_mib=release_baseline)
        if not retain_scratch:
            shutil.rmtree(scratch, ignore_errors=True)

    return {
        "roots": [result.to_dict() for result in results],
        "device_intervals": device_intervals,
        "peak_vram_mib": peak_vram,
        "adjudicator": ADJUDICATOR_VERSION,
        "scratch": str(scratch) if retain_scratch else None,
        "cleanup": {
            "servers": cleanup,
            "unreaped": [row["pid"] for row in cleanup
                         if row.get("state") == "unreaped"],
            "foreign_processes_touched": 0,
            **release,
        },
    }


class StageBContaminated(RuntimeError):
    """A foreign compute process appeared on a bound device DURING a timed arm.

    Distinct from `HarnessInfrastructureError` on purpose, because the two have
    opposite re-run rules. A harness error is a defect in this run and stops the
    comparison. Contamination is a defect in the MEASUREMENT CONDITIONS: the arm
    produced no verdict, so it may be re-run once the card is clear -- the one
    case where re-running is correct rather than outcome-shopping.
    """

    def __init__(self, *, blockers: Sequence[str], detected_before_root: str,
                 devices: Sequence[int]) -> None:
        super().__init__(
            f"foreign compute process on a bound device before root "
            f"{detected_before_root}: {sorted(blockers)}")
        self.blockers = sorted(blockers)
        self.detected_before_root = str(detected_before_root)
        self.devices = sorted(int(device) for device in devices)
        self.started_roots: list[str] = []
        self.cancelled_roots: list[str] = []
        self.completed_roots: list[str] = []


def _run_schedule(schedule: Sequence[Mapping[str, Any]], run_root,
                  *, occupancy_probe=None,
                  probe_interval_seconds: float = MID_ARM_MIN_PROBE_INTERVAL_SECONDS):
    """Per-worker sequential queues under one shared stop event.

    The void attempt submitted all 30 assignments to a pool at once, so a
    defect every root shared produced 120 failure records before anything
    could react. Here each worker drains its own frozen block IN ORDER, and
    the first infrastructure failure sets the stop event: no further root
    starts on any worker, every not-yet-started assignment is recorded as
    cancelled, and roots already in flight terminate safely on their own.
    Candidate outcomes never touch the event -- an NQ-shaped root result is a
    result, and stopping on one would let candidate behaviour end the exam.

    `occupancy_probe`, when supplied, is called BETWEEN roots on each worker
    and returns None when the bound devices are still ours alone, or a reason
    list when a foreign compute process has appeared. The pre-stage canary
    checks the instant before the arm starts and nothing after it, which on an
    owned host was nearly the same statement and on a SHARED host is not: an
    arm is thirty roots at up to the full rail each, so a neighbour arriving
    early enough contaminates hours of timing that would otherwise be recorded
    as a clean verdict. Probing between roots bounds the exposure at one root.

    It is checked between roots rather than during one because a root is the
    unit that carries a wall measurement; interrupting one mid-flight would
    destroy a measurement rather than protect it.

    Returns (results_by_root_id, started, cancelled, failures). `cancelled`
    is exactly the assignments never invoked; the regression test injects a
    first-root failure and asserts they stayed uninvoked.
    """
    import threading

    stop = threading.Event()
    lock = threading.Lock()
    results: dict[str, Any] = {}
    started: list[str] = []
    cancelled: list[str] = []
    failures: list[BaseException] = []

    by_worker: dict[int, list[Mapping[str, Any]]] = {}
    for assignment in schedule:
        by_worker.setdefault(int(assignment["worker"]), []).append(assignment)

    last_probe = [0.0]

    def contaminated(root_id: str, assignment: Mapping[str, Any]) -> bool:
        """True when a foreign process has appeared since the arm began."""
        if occupancy_probe is None:
            return False
        now = time.monotonic()
        with lock:
            if now - last_probe[0] < probe_interval_seconds:
                return False
            last_probe[0] = now
        blockers = occupancy_probe()
        if not blockers:
            return False
        stop.set()
        with lock:
            # One void record per arm, not one per worker: both workers see the
            # same neighbour and the arm is voided once.
            if not any(isinstance(f, StageBContaminated) for f in failures):
                failures.append(StageBContaminated(
                    blockers=blockers, detected_before_root=root_id,
                    devices=list(assignment.get("devices") or ())))
        return True

    def drain(queue: Sequence[Mapping[str, Any]]) -> None:
        for assignment in queue:
            root_id = str(assignment["root_id"])
            if stop.is_set():
                with lock:
                    cancelled.append(root_id)
                continue
            if contaminated(root_id, assignment):
                with lock:
                    cancelled.append(root_id)
                continue
            with lock:
                started.append(root_id)
            try:
                outcome = run_root(assignment)
            except BaseException as exc:  # noqa: BLE001
                # ANY exception escaping the root runner is infrastructure --
                # candidate-shaped outcomes return results, they do not raise.
                stop.set()
                with lock:
                    failures.append(exc)
                continue
            with lock:
                results[root_id] = outcome

    threads = [threading.Thread(target=drain, args=(queue,), daemon=True)
               for _, queue in sorted(by_worker.items())]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results, started, cancelled, failures


REQUIRED_TASK_FILES = ("train.csv", "dev.csv", "task.json")
OPTIONAL_TASK_FILES = ("rubric.json", "baseline.py", "pipeline.py")


def prepare_exam_root(*, assignment: Mapping[str, Any], dataset_root: Path,
                      scratch: Path, ToolBridge) -> dict[str, Any]:
    """Everything a root needs BEFORE the model exists. One function, two callers.

    `_run_exam_root` calls it in production; the model-free replay gate calls
    it with the real frozen manifest's first assignment and stops immediately
    after. The gate is only worth having if it runs THIS code -- a parallel
    miniature preparation would validate itself, not the harness.

    Required task files are VALIDATED, not copied-if-present: a template
    missing train/dev/task is dataset infrastructure failing, and silently
    running the root without them measures a crippled workspace as a model.
    """
    root_id = str(assignment["root_id"])
    template_id = root_id.rsplit("-v", 1)[0]
    workspace = scratch / root_id / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    source = dataset_root / template_id
    missing = [name for name in REQUIRED_TASK_FILES
               if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(
            f"required task files missing for {template_id}: "
            f"{', '.join(missing)} under {source}")
    for name in REQUIRED_TASK_FILES + OPTIONAL_TASK_FILES:
        if (source / name).is_file():
            shutil.copy2(source / name, workspace / name)
    bridge = ToolBridge(workspace_root=workspace,
                        allowed_tools=list(ALLOWED_TOOLS),
                        command_handlers=d7_command_handlers(workspace))
    return {"root_id": root_id, "template_id": template_id,
            "workspace": workspace, "bridge": bridge}


class HarnessInfrastructureError(RuntimeError):
    """The harness broke; the candidate was never measured.

    Raised instead of writing a scoreable root record. The attempted run
    converted 120 of these into candidate records with zero turns and zero
    tokens, the scorer read them as zero performance, and the selector
    reported no eligible model -- a confident verdict about models that were
    never asked anything. Under the replay ruling any harness_error is a
    SHARED infrastructure nonverdict: the run stops, a failure record is
    written where the selector never looks, and no candidate is scored.
    """

    def __init__(self, *, root_id: str, cause: BaseException) -> None:
        super().__init__(
            f"harness_error at root {root_id}: "
            f"{type(cause).__name__}: {str(cause)[:200]}")
        self.root_id = root_id
        self.cause_type = type(cause).__name__


class ExamPromptBindingError(RuntimeError):
    """The frozen task is absent or not the frozen task. Nothing may run."""


def load_frozen_exam_prompt(registry: Mapping[str, Any],
                            repo_root: Path | None = None) -> str:
    """Load the exam prompt and PROVE it is the frozen one.

    The prompt is the task; two wordings are two exams. The read site
    originally dereferenced runtime["exam_prompt"], which no artifact ever
    carried, so every root died on KeyError before the first model request.
    The binding is now a file plus a digest in the registry, and this loader
    refuses -- as a SHARED failure, before any server starts -- rather than
    running an exam whose task is missing, empty, or edited.
    """
    import hashlib

    runtime = registry.get("runtime") or {}
    raw = str(runtime.get("exam_prompt_path") or "").strip()
    path = Path(raw) if raw else None
    if path is not None and not path.is_absolute():
        base = repo_root or Path(__file__).resolve().parents[3]
        path = base / path
    exists = bool(path and path.is_file())
    data = path.read_bytes() if exists else b""
    blockers = exam_prompt_blockers(
        runtime=runtime, file_exists=exists,
        file_sha256=hashlib.sha256(data).hexdigest() if exists else None,
        file_text=data.decode("utf-8", errors="replace") if exists else None)
    schema = runtime_schema_blockers(runtime)
    if blockers or schema:
        raise ExamPromptBindingError("; ".join(blockers + schema))
    return data.decode("utf-8")


def _run_exam_root(
    *, assignment, port, candidate, dataset_root, hidden_root, scratch,
    retain_scratch, PiAgentAdapter, ToolBridge, SubstrateIdentity,
    SubstrateIdentityMismatch, sole_session_file, adjudicate_d7,
    load_hidden_set, TERMINAL_VALIDATED, endpoint_factory, registry,
    exam_prompt: str, identity_factory=None, user_id_factory=None,
    capture_provider_completions: bool = False,
    run_id: str = "round5-titan-compact-exam",
    wall_clock_deadline_seconds: float = ROOT_WALL_RAIL_SECONDS,
    rail_diagnostic_seconds: float | None = None,
    max_tool_calls: int | None = None,
    max_completion_tokens: int | None = None,
) -> ExamRootResult:
    from datetime import datetime, timezone

    root_id = str(assignment["root_id"])
    template_id = root_id.rsplit("-v", 1)[0]
    result = ExamRootResult(
        root_id=root_id, template_id=template_id,
        worker=int(assignment["worker"]), devices=list(assignment["devices"]),
        server_port=int(port), topology=str(assignment["topology"]),
        started_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    started = time.perf_counter()
    try:
        prepared = prepare_exam_root(assignment=assignment,
                                     dataset_root=dataset_root,
                                     scratch=scratch, ToolBridge=ToolBridge)
        workspace = prepared["workspace"]
        bridge = prepared["bridge"]
        endpoint = endpoint_factory(port, candidate)
        identity = (identity_factory(root_id, candidate, endpoint)
                    if identity_factory is not None else SubstrateIdentity(
                        base_url=f"http://127.0.0.1:{port}/v1",
                        model_id=candidate,
                        expected_system_fingerprint=None,
                        enforce_fingerprint=False))
        user_id = user_id_factory(root_id) if user_id_factory is not None else None
        adapter = PiAgentAdapter(
            pi_entry=Path(str((registry.get("runtime") or {})["pi_entry"])),
            endpoint=endpoint,
            system_prompt=Path(str((registry.get("runtime") or {})["system_prompt"])),
            extension=Path(str((registry.get("runtime") or {})["tool_extension"])),
            allowed_tools=list(ALLOWED_TOOLS), tool_bridge=bridge,
        )
        run_kwargs = dict(
            agent_dir=scratch / root_id / "agent",
            session_dir=scratch / root_id / "session",
            working_dir=workspace,
            runtime_dir=Path(tempfile.mkdtemp(prefix="r5-titan-rt-")),
            prompt=exam_prompt,
            run_id=run_id,
            branch_id=f"{root_id}-g_0", regime_id="g_0", root_id=root_id,
            identity=identity,
            wall_clock_deadline_seconds=float(wall_clock_deadline_seconds),
        )
        if max_tool_calls is not None:
            run_kwargs["max_tool_calls"] = int(max_tool_calls)
        if max_completion_tokens is not None:
            run_kwargs["max_completion_tokens"] = int(max_completion_tokens)
        # Preserve the byte-for-byte local call surface: the hosted-only user
        # identifier is added only when the portal supplies one.  This also
        # keeps the model-free scripted replay adapter compatible.
        if user_id is not None:
            run_kwargs["user_id"] = user_id
        run = adapter.run_turn(**run_kwargs)
        if capture_provider_completions:
            result.provider_completions = [row.to_dict() for row in run.completions]
        # `run.events` already carries the drained partial trace on the timeout
        # path: the production adapter drains before propagating RpcTimeout.
        result.partial_events_retained = bool(run.events)
        result.settled = run.terminal == "settled"
        result.entry_id = run.entry_id
        names = [str(event.get("name")) for event in run.events
                 if event.get("type") == "tool_started"]
        result.tool_call_names = names
        result.tool_calls = len(names)
        result.turns = sum(
            1 for event in run.events
            if event.get("type") == "message_completed"
            and isinstance(event.get("message"), dict)
            and event["message"].get("role") == "assistant")
        malformed = errors = 0
        for event in run.events:
            if event.get("type") != "tool_completed" or not event.get("is_error"):
                continue
            payload = event.get("result")
            message = (payload if isinstance(payload, str)
                       else json.dumps(payload))
            if classify_tool_error(message) == "malformed":
                malformed += 1
            else:
                errors += 1
        result.malformed_tool_calls = malformed
        result.tool_execution_errors = errors
        usage = getattr(run, "usage", None) or {}
        result.prompt_tokens = int(usage.get("prompt_tokens") or 0)
        result.completion_tokens = int(usage.get("completion_tokens") or 0)
        result.peak_context_tokens = int(usage.get("peak_context_tokens") or 0)

        try:
            sole_session_file(scratch / root_id / "session")
        except Exception:  # noqa: BLE001
            result.single_session = False
        result.isolation_ok = not any(path.name == "eval.csv"
                                      for path in workspace.rglob("*"))

        submission_path = workspace / "submission.json"
        result.submission_present = submission_path.is_file()

        if run.terminal == "run_provider_error":
            first = (run.provider_errors or [{}])[0]
            result.provider_error = {
                "http_status": first.get("http_status"),
                "error_type": first.get("error_type"),
                "provider_message": str(first.get("provider_message"))[:400],
            }
            result.error = (f"ProviderError: HTTP {first.get('http_status')} "
                            f"{first.get('error_type')}")
            result.invalidity_reason = "provider_error"
            return result

        if run.terminal == "run_timed_out":
            result.timed_out = True
            result.error = ("RpcTimeout: no terminal event observed "
                            "(partial trace retained)")
            result.invalidity_reason = "timed_out"
            result.adjudication = {
                "scored": False,
                "submission_observed_but_not_scored": result.submission_present,
            }
            return result

        if run.terminal == "run_budget_exhausted":
            result.budget_exhausted = True
            result.budget_exhausted_reason = (
                run.budget_exhausted_reason or "budget_exhausted")
            result.error = f"BudgetExhaustion: {result.budget_exhausted_reason}"
            result.invalidity_reason = "budget_exhausted"
            result.adjudication = {
                "scored": True,
                "success": False,
                "reason": result.budget_exhausted_reason,
                "submission_observed_but_not_scored": result.submission_present,
            }
            result.success = False
            return result

        submission = None
        if result.submission_present:
            try:
                submission = json.loads(submission_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result.invalidity_reason = "submission_is_not_valid_json"
        hidden = load_hidden_set(hidden_root / template_id / "eval.csv")
        verdict = adjudicate_d7(submission=submission, hidden=hidden)
        if verdict.terminal_category == TERMINAL_UNRESOLVED:
            raise RuntimeError(
                "adjudicator_unresolved: " + str(verdict.to_dict().get("reason")))
        result.adjudication = verdict.to_dict()
        result.success = verdict.terminal_category == TERMINAL_VALIDATED
        result.submission_valid = bool(
            result.submission_present and result.invalidity_reason is None
            and verdict.submission_wellformed is True)
        if not result.submission_valid and result.invalidity_reason is None:
            result.invalidity_reason = verdict.to_dict().get("reason")
    except SubstrateIdentityMismatch:
        raise
    except Exception as exc:  # noqa: BLE001
        # NOT a candidate record. This except clause used to write
        # invalidity_reason="harness_error" into a scoreable root, and 120 of
        # those became a full set of zero-performance candidate records and a
        # no-eligible-model verdict. An exception here means the HARNESS broke;
        # raising stops the whole comparison (shared scope), and the runner
        # writes a failure record where the selector never looks.
        raise HarnessInfrastructureError(root_id=root_id, cause=exc) from exc
    finally:
        # Wall time and rail status are properties of the CLOCK, not of the
        # return path. Computing them only where the function returns normally
        # recorded every exceptional termination as `rail_bound: False`, and the
        # gate requires ZERO rail-bound roots -- so the one branch that most
        # needed counting was the one branch that could not be.
        from datetime import datetime, timezone
        result.wall_seconds = time.perf_counter() - started
        # `rail_bound` answers a FIXED question -- "would this root have been cut
        # off by the 360 s rail?" -- so that a Round-7 row and a Round-6 row mean
        # the same thing by it. It is no longer the same number as the deadline:
        # Round 7 stops a root only at the safety timeout, and defining
        # rail_bound against that would silently redefine a column that appears
        # in every archived artifact. Callers that pass no diagnostic keep the
        # old identity exactly -- rail_bound still means "hit my deadline" --
        # which is what every pre-Round-7 caller relies on.
        rail = float(wall_clock_deadline_seconds if rail_diagnostic_seconds is None
                     else rail_diagnostic_seconds)
        result.rail_bound = result.wall_seconds >= rail
        # Budget exhaustion is evaluated from what the root CONSUMED, not from
        # how long it took, so a busy or slow card cannot manufacture it.
        if (max_tool_calls is not None
                and len(result.tool_call_names) >= int(max_tool_calls)):
            result.budget_exhausted = True
            result.budget_exhausted_reason = (
                f"tool_calls_{len(result.tool_call_names)}_reached_"
                f"{int(max_tool_calls)}")
        elif (max_completion_tokens is not None
              and int(result.completion_tokens or 0) >= int(max_completion_tokens)):
            result.budget_exhausted = True
            result.budget_exhausted_reason = (
                f"completion_tokens_{result.completion_tokens}_reached_"
                f"{int(max_completion_tokens)}")
        result.finished_at_utc = datetime.now(timezone.utc).isoformat()
        root_scratch = scratch / root_id
        if retain_scratch:
            # Retained read-only until the final manifest validates. It is never
            # read back by the harness: each root builds its workspace fresh, so
            # a retained tree cannot reach another root's workspace, prompt,
            # cache or scoring inputs. It exists to be inspected by a human.
            try:
                for path in sorted(root_scratch.rglob("*"), reverse=True):
                    path.chmod(0o500 if path.is_dir() else 0o400)
                root_scratch.chmod(0o500)
                result.retained_scratch = str(root_scratch)
            except OSError:
                result.retained_scratch = None
    return result
