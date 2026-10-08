"""Live Stage-A acquisition: start the frozen topology and MEASURE it.

This module is the missing measurement layer. It starts the servers the frozen
topology declares, issues the Stage-A probes against them, samples NVML, and
writes an observation record bound to this module's own digest and to the raw
server logs. `run_round5_titan_stage_a.py --acquire` is its only caller, and it
is imported lazily from that branch so `--plan` cannot pull a model client into
the process at all.

Why the record is digest-bound. An observation file supplied from outside is a
hand-editable JSON document that decides whether a candidate is eligible. Bound
to the acquisition module that produced it, the llama-server binary, the runtime
commit and the SHA-256 of every raw server log, it is evidence instead.

Three measurement rules this file exists to keep.

**Capacity is not latency.** The 40,609-token request runs under a separately
recorded diagnostic timeout. It proves the ceiling fits and is never judged
against the 360-second historical rail. The realistic 32,768-token multi-turn
request records the same rail as a diagnostic; elapsed time is not a candidate
verdict in either probe.

**CPU fallback is detected by residency, not by arithmetic.** The evidence is a
loaded model, non-zero VRAM on every assigned card, ZERO model memory on every
non-assigned card, sustained utilisation during generation, and correct provider
usage metadata. Dividing a short completion by a long prefill wall time is not a
fallback detector; it is a way to fail every candidate for being large.

**`finish_reason == "length"` is inconclusive.** One prespecified retry at the
already frozen 4,096-token ceiling is permitted. No candidate-specific token
limit is ever chosen after seeing an output.

Non-scientific throughout: every prompt here is a fixed probe string. No D7
template, no exam root, and no hidden table is opened.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from causal_branch.round5_titan_runtime_evidence import (
    build_runtime_evidence,
    runtime_evidence_blockers,
)
from causal_branch.round5_titan_exam import (
    CONTEXT_TOKENS,
    STAGE_A_CANDIDATE_TIMEOUT_SECONDS,
    stage_a_candidate_timeout_seconds,
    STAGE_A_TOKEN_CALIBRATION_ATTEMPTS,
    TERMINAL_STAGE_A_TIMEOUT,
    STAGE_A_CAPACITY_MAX_PROMPT_TOKENS,
    STAGE_A_CAPACITY_MIN_PROMPT_TOKENS,
    STAGE_A_REALISTIC_MIN_PROMPT_TOKENS,
    ENABLE_THINKING,
    OUTPUT_CEILING_TOKENS,
    ROOT_WALL_RAIL_SECONDS,
    ROUND7_PANEL_VERSIONS,
    panel_version_of,
    STAGE_A_REQUEST_TIMEOUT_SECONDS,
    ROUND7_SERVER_START_TIMEOUT_SECONDS,
    STAGE_A_CAPACITY_DIAGNOSTIC_TIMEOUT_SECONDS,
    STAGE_A_CAPACITY_PROBE_TOKENS,
    STAGE_A_COHERENCE_PROBE_CONTEXTS,
    STAGE_A_MIN_FREE_VRAM_MIB,
    STAGE_A_OBSERVATION_KIND,
    STAGE_A_REALISTIC_BUCKET_TOKENS,
    STAGE_A_TERMINAL_PROMPTS,
    STAGE_A_TOOL_PROMPTS,
    TEMPERATURE,
    TITAN_CUDA_ARCHITECTURE,
    hardware_profile_of,
    host_spec,
    occupancy_blockers,
    occupancy_verdict,
    CACHE_ISOLATION_ARGV,
    server_argv,
    server_environment,
    device_mapping,
    terminal_answer_verdict,
    topology_profile,
)

HEALTH_TIMEOUT_SECONDS = 420.0
HEALTH_POLL_SECONDS = 2.0
BASE_PORT = 18500

# A fixed NON-SCIENTIFIC tool suite, deliberately unrelated to D7 so a tool
# measurement can never touch scientific material.
PROBE_TOOLS = [
    {"type": "function", "function": {
        "name": "convert_units",
        "description": "Convert a value between two units of measurement.",
        "parameters": {"type": "object", "properties": {
            "value": {"type": "number", "description": "The numeric value"},
            "from_unit": {"type": "string", "description": "Source unit"},
            "to_unit": {"type": "string", "description": "Target unit"}},
            "required": ["value", "from_unit", "to_unit"]}}},
    {"type": "function", "function": {
        "name": "lookup_timezone",
        "description": "Return the IANA timezone identifier for a city.",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string", "description": "City name"}},
            "required": ["city"]}}},
]
TOOL_PROMPTS = [
    "Convert 12 kilometres to miles. Use the convert_units tool.",
    "What timezone is Reykjavik in? Use the lookup_timezone tool.",
    "Convert 450 grams to ounces using the convert_units tool.",
    "Use lookup_timezone to find the timezone for Wellington.",
    "Convert 98.6 degrees fahrenheit to celsius with convert_units.",
]
TERMINAL_PROMPTS = [
    "What is 17 multiplied by 23? Reply with the number only.",
    "Name the capital city of Portugal. Reply with the name only.",
    "How many minutes are in three hours? Reply with the number only.",
    "Which is larger, 0.7 or 0.65? Reply with the number only.",
]
# Deterministic, checkable coherence probes for the two-card exception. Each has
# a syntactically valid and semantically checkable answer, so garbled output is
# distinguishable from a wrong answer.
COHERENCE_PROBES = {
    2048: ("Repeat exactly this token and nothing else: ALPHA-2048", "ALPHA-2048"),
    8192: ("Repeat exactly this token and nothing else: BRAVO-8192", "BRAVO-8192"),
    32768: ("Repeat exactly this token and nothing else: DELTA-32768", "DELTA-32768"),
}
FROZEN_SAMPLING: dict[str, Any] = {
    "temperature": TEMPERATURE,
    "chat_template_kwargs": {"enable_thinking": ENABLE_THINKING},
}
REPEATED_REQUEST_TRIALS = 3
# A token that must not resolve if the server is genuinely network-denied.
NETWORK_DENIAL_TARGET = "http://169.254.169.254/latest/meta-data/"


class StageAAcquisitionError(RuntimeError):
    """The acquisition could not be completed; no verdict is produced."""


class StageARequestTimeout(StageAAcquisitionError):
    """A diagnostic HTTP/startup clock expired; this is not a candidate NQ."""


def _raise_if_timeout(exc: BaseException, operation: str) -> None:
    reason = getattr(exc, "reason", None)
    if (isinstance(exc, TimeoutError) or isinstance(reason, TimeoutError)
            or "timed out" in str(exc).lower()):
        raise StageARequestTimeout(f"{operation}: {exc}") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquisition_module_sha256() -> str:
    """This file's own digest, recorded in every observation record."""
    return sha256_file(Path(__file__).resolve())


# --------------------------------------------------------------------------
# NVML
# --------------------------------------------------------------------------

def _smi(query: str, *extra: str) -> list[list[str]]:
    try:
        out = subprocess.run(
            ["nvidia-smi", f"--query-{query}", "--format=csv,noheader,nounits",
             *extra],
            capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if out.returncode != 0:
        return []
    return [[part.strip() for part in line.split(",")]
            for line in out.stdout.splitlines() if line.strip()]


def device_inventory() -> list[dict[str, Any]]:
    rows = _smi("gpu=index,name,uuid,memory.total,memory.used,utilization.gpu,"
                "driver_version,compute_cap,power.limit,power.draw,"
                "clocks.current.sm,temperature.gpu")
    devices: list[dict[str, Any]] = []
    for parts in rows:
        if len(parts) < 12:
            continue
        devices.append({
            "index": int(parts[0]), "name": parts[1], "uuid": parts[2],
            "memory_total_mib": float(parts[3]), "memory_used_mib": float(parts[4]),
            "utilisation_percent": float(parts[5]), "driver_version": parts[6],
            "compute_capability": parts[7], "power_limit_watts": parts[8],
            "power_draw_watts": parts[9], "sm_clock_mhz": parts[10],
            "temperature_c": parts[11],
        })
    return devices


class GpuProcessQueryFailure(RuntimeError):
    """The GPU process table could not be read, or could not be trusted.

    Raised rather than returning an empty map. "I could not look" and "nothing
    is there" are different claims, and every caller of this module uses the
    result to assert the ABSENCE of a foreign process on a leased card. An empty
    map on a failed query silently converts a monitoring failure into a
    clean-host verdict.
    """


def gpu_processes_by_uuid() -> dict[str, list[int]]:
    """Every process holding a context on each GPU, whatever its type.

    `nvidia-smi --query-compute-apps` lists COMPUTE contexts only. A process
    holding a GRAPHICS context is invisible to it, and on 2026-09-03 exactly
    that happened: another researcher's job attached to leased card 1 with a
    `G` context and ~1 GiB, and every gate that asks "is anything foreign here?"
    -- acquisition, lease verification, readiness, the pre-root occupancy canary
    and the mid-arm probe -- reported the card clean. `lease-verify` still said
    `held: true, blockers: []` with a neighbour resident. Only the cleanup
    baseline noticed, by memory arithmetic, after the fact.

    This driver has no `--query-graphics-apps`, so the authoritative source is
    the XML dump, whose `<process_info>` carries `<type>` (C, G, or C+G). Every
    type counts: ownership is decided by PID against the recorded owned set,
    never by context type, process name, user or executable.

    Observations are normalised to int PIDs and deduplicated per GPU UUID, so a
    process reported once as C and once as G is one PID.

    Fails closed: any query error, non-zero exit, or unparseable XML raises
    GpuProcessQueryFailure rather than returning an empty map.
    """
    import xml.etree.ElementTree as ET

    try:
        out = subprocess.run(["nvidia-smi", "-q", "-x"],
                             capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GpuProcessQueryFailure(
            f"nvidia-smi process query failed: {exc}") from exc
    if out.returncode != 0:
        raise GpuProcessQueryFailure(
            f"nvidia-smi process query exited {out.returncode}: "
            f"{(out.stderr or '').strip()[:200]}")
    try:
        root = ET.fromstring(out.stdout)
    except ET.ParseError as exc:
        raise GpuProcessQueryFailure(
            f"nvidia-smi process query returned unparseable XML: {exc}") from exc

    found: dict[str, set[int]] = {}
    for gpu in root.iter("gpu"):
        uuid_node = gpu.find("uuid")
        if uuid_node is None or not (uuid_node.text or "").strip():
            raise GpuProcessQueryFailure(
                "nvidia-smi process query reported a GPU with no UUID")
        uuid = uuid_node.text.strip()
        # A MISSING `<processes>` SECTION IS NOT AN IDLE CARD. Every GPU in
        # this driver's dump carries the element, empty when nothing is
        # resident. Its absence means the section could not be rendered, and
        # reading that as "no processes" is how an occupied card gets called
        # free -- the 2026-09-12 failure in a different shape.
        if gpu.find("processes") is None:
            raise GpuProcessQueryFailure(
                f"nvidia-smi reported no <processes> section for {uuid}; "
                "absence of the section is not evidence of an idle card")
        found.setdefault(uuid, set())
        for info in gpu.iter("process_info"):
            pid_node = info.find("pid")
            text = (pid_node.text or "").strip() if pid_node is not None else ""
            if not text.isdigit():
                # Ambiguous evidence about who is on a leased card is not
                # something to skip past.
                raise GpuProcessQueryFailure(
                    f"nvidia-smi reported a process with an unreadable pid "
                    f"{text!r} on {uuid}")
            found[uuid].add(int(text))
    return {uuid: sorted(pids) for uuid, pids in found.items()}


def compute_pids_by_uuid() -> dict[str, list[int]]:
    """Historical name, now covering every context type.

    Kept so that acquisition, lease verification, readiness, the canary and both
    Stage runners pick the wider enumeration up without a signature change. The
    name is retained rather than churned through nine call sites mid-run.
    """
    return gpu_processes_by_uuid()


def occupancy_samples(owned_pids: Sequence[int] = ()) -> list[dict[str, Any]]:
    processes = compute_pids_by_uuid()
    owned = {int(pid) for pid in owned_pids}
    samples = []
    for device in device_inventory():
        pids = processes.get(device["uuid"], [])
        samples.append({
            "device": device["index"],
            "compute_pids": pids,
            "memory_used_mib": device["memory_used_mib"],
            "utilisation_percent": device["utilisation_percent"],
            "explained_by_owned_server": bool(pids) and set(pids) <= owned,
        })
    return samples


class NvmlSampler:
    """Poll NVML CONCURRENTLY with a request, on a background thread.

    A chat completion is synchronous: by the time it returns, generation has
    ended and the GPU is idle again. Sampling utilisation after the call
    therefore reports 0% for a perfectly GPU-resident model, and
    `no_cpu_fallback` -- whose whole evidence is sustained utilisation during
    generation -- fails a model that was working. The sampler runs for the
    duration of the request and reports peak and mean, so the measurement covers
    the window it claims to.
    """

    def __init__(self, devices: Sequence[int], *, interval: float = 0.25) -> None:
        self.devices = [int(device) for device in devices]
        self.interval = float(interval)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.samples: dict[str, list[dict[str, float]]] = {
            str(device): [] for device in self.devices}

    def _poll(self) -> None:
        while not self._stop.is_set():
            rows = _smi("gpu=index,memory.used,utilization.gpu")
            stamp = time.monotonic()
            for parts in rows:
                if len(parts) < 3:
                    continue
                key = parts[0]
                if key in self.samples:
                    try:
                        self.samples[key].append({
                            "at_monotonic": stamp,
                            "memory_used_mib": float(parts[1]),
                            "utilisation_percent": float(parts[2]),
                        })
                    except ValueError:
                        continue
            self._stop.wait(self.interval)

    def __enter__(self) -> "NvmlSampler":
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)

    def summary(self) -> dict[str, Any]:
        peak_util: dict[str, float] = {}
        mean_util: dict[str, float] = {}
        peak_memory: dict[str, float] = {}
        counts: dict[str, int] = {}
        for device, rows in self.samples.items():
            counts[device] = len(rows)
            if not rows:
                continue
            utilisations = [row["utilisation_percent"] for row in rows]
            peak_util[device] = max(utilisations)
            mean_util[device] = sum(utilisations) / len(utilisations)
            peak_memory[device] = max(row["memory_used_mib"] for row in rows)
        return {
            "peak_utilisation_percent": peak_util,
            "mean_utilisation_percent": mean_util,
            "peak_memory_used_mib": peak_memory,
            "sample_counts": counts,
            "interval_seconds": self.interval,
            "sampled_concurrently_with_inference": True,
        }


def compute_apps() -> list[dict[str, Any]]:
    """Per-PROCESS, per-GPU memory. The basis of a real isolation proof."""
    rows = _smi("compute-apps=gpu_uuid,pid,used_memory")
    uuid_to_index = {row["uuid"]: row["index"] for row in device_inventory()}
    found: list[dict[str, Any]] = []
    for parts in rows:
        if len(parts) < 3 or not parts[1].isdigit():
            continue
        try:
            used = float(parts[2])
        except ValueError:
            used = -1.0
        found.append({"gpu_uuid": parts[0], "device": uuid_to_index.get(parts[0]),
                      "pid": int(parts[1]), "used_memory_mib": used})
    return found


def process_group_pids(pid: int) -> set[int]:
    """Every PID in one server's process group. llama-server forks."""
    try:
        pgid = os.getpgid(int(pid))
    except (ProcessLookupError, PermissionError, OSError):
        return {int(pid)}
    try:
        out = subprocess.run(["ps", "-o", "pid=", "-g", str(pgid)],
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return {int(pid)}
    found = {int(line) for line in out.stdout.split() if line.strip().isdigit()}
    found.add(int(pid))
    return found


def gpu_memory_used(index: int) -> float:
    rows = _smi("gpu=memory.used", "-i", str(index))
    return float(rows[0][0]) if rows else -1.0


def gpu_free_mib(index: int) -> float:
    rows = _smi("gpu=memory.free", "-i", str(index))
    return float(rows[0][0]) if rows else -1.0


# --------------------------------------------------------------------------
# server lifecycle
# --------------------------------------------------------------------------

# Every fleet that is currently holding cards. A Stage-A process that is
# TERMINATED rather than returning never reaches its own cleanup, and its
# servers are in their OWN process groups (start_new_session=True), so killing
# the stage's group does not reach them. They survive holding ~6 GiB each, and
# the NEXT candidate's occupancy canary correctly reads that as an unexplained
# baseline and refuses to run -- so one timeout silently poisons every candidate
# after it. This registry exists so a signal handler can release them.
_ACTIVE_FLEETS: list["ServerFleet"] = []


def stop_active_fleets() -> list[dict[str, Any]]:
    """Stop every fleet this process started. Safe to call twice."""
    outcomes: list[dict[str, Any]] = []
    for fleet in list(_ACTIVE_FLEETS):
        try:
            outcomes.append(fleet.stop())
        except Exception as exc:  # noqa: BLE001 -- cleanup must not raise
            outcomes.append({"error": f"{type(exc).__name__}: {exc}"})
    return outcomes


class ServerFleet:
    """Every server this acquisition started, and nothing else."""

    def __init__(self, *, candidate: str, model: Path, llama_server: Path,
                 topology: str, out_dir: Path,
                 execution_profile: Mapping[str, Any] | None = None,
                 health_timeout_seconds: float = HEALTH_TIMEOUT_SECONDS) -> None:
        self.candidate = candidate
        self.model = model
        self.llama_server = llama_server
        self.topology = topology
        self.profile = (dict(execution_profile)
                        if execution_profile is not None
                        else topology_profile(topology))
        self.out_dir = out_dir
        self.health_timeout_seconds = float(health_timeout_seconds)
        self.processes: list[subprocess.Popen] = []
        self.release_baseline_mib: dict[str, float] = {}
        self.entries: list[dict[str, Any]] = []
        self.log_paths: list[Path] = []
        self._handles: list[Any] = []

    def start(self) -> list[dict[str, Any]]:
        for index, devices in enumerate(self.profile["device_groups"]):
            uuid_groups = self.profile.get("device_group_uuids") or ()
            visibility = (list(uuid_groups[index]) if uuid_groups
                          else None)
            port = BASE_PORT + index
            slot_dir = self.out_dir / f"slots-server-{index}"
            slot_dir.mkdir(parents=True, exist_ok=True)
            argv = server_argv(llama_server=str(self.llama_server),
                               model=str(self.model), alias=self.candidate,
                               port=port, devices=devices,
                               topology=self.topology,
                               slot_save_path=str(slot_dir))
            log = self.out_dir / f"{self.candidate}-server-{index}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            handle = log.open("w", encoding="utf-8")
            self._handles.append(handle)
            # CONFINEMENT. Each server gets a device namespace containing only
            # its own physical group, and its argv names the logical devices
            # inside that namespace. Inheriting the parent's environment is what
            # let every server allocate on every card.
            mapping = device_mapping(devices, visibility_tokens=visibility)
            env = {**os.environ, **server_environment(
                devices, visibility_tokens=visibility)}
            process = subprocess.Popen(argv, stdout=handle,
                                       stderr=subprocess.STDOUT,
                                       start_new_session=True, env=env)
            self.processes.append(process)
            self.log_paths.append(log)
            if self not in _ACTIVE_FLEETS:
                _ACTIVE_FLEETS.append(self)
            self.entries.append({
                "server": index, "port": port, "devices": list(devices),
                "argv": argv, "pid": process.pid, "log": str(log),
                "started_at_utc": utc_now(),
                "device_confinement": mapping,
            })
        return self.entries

    def wait_healthy(self) -> list[bool]:
        healthy: list[bool] = []
        for index, entry in enumerate(self.entries):
            process = self.processes[index]
            deadline = time.perf_counter() + self.health_timeout_seconds
            ok = False
            while time.perf_counter() < deadline:
                if process.poll() is not None:
                    break
                try:
                    with urllib.request.urlopen(
                            f"http://127.0.0.1:{entry['port']}/health",
                            timeout=5) as response:
                        if json.loads(response.read().decode()).get("status") == "ok":
                            ok = True
                            break
                except Exception:  # noqa: BLE001
                    pass
                time.sleep(HEALTH_POLL_SECONDS)
            entry["healthy"] = ok
            entry["health_failure"] = (
                None if ok else
                "process_exited" if process.poll() is not None else
                "startup_timeout")
            healthy.append(ok)
        return healthy

    def owned_pids(self) -> list[int]:
        return [process.pid for process in self.processes]

    def stop(self) -> dict[str, Any]:
        """Signal each server's whole GROUP, wait, then verify.

        llama-server forks; signalling only the parent leaves workers holding
        VRAM. Nothing this fleet did not start is ever signalled.
        """
        if self in _ACTIVE_FLEETS:
            _ACTIVE_FLEETS.remove(self)
        outcomes = []
        for process in self.processes:
            record: dict[str, Any] = {"pid": process.pid}
            if process.poll() is not None:
                record["state"] = "already_exited"
            else:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError, OSError):
                    try:
                        process.terminate()
                    except OSError:
                        pass
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
            outcomes.append(record)
        for handle in self._handles:
            try:
                handle.close()
            except OSError:
                pass
        # Confirm the cards came back. A server that exited without releasing
        # VRAM is exactly what stranded the earlier funnels.
        time.sleep(3)
        residual = {}
        for group in self.profile["device_groups"]:
            for device in group:
                residual[str(device)] = gpu_memory_used(device)
        clean = all(
            value <= float(self.release_baseline_mib.get(device, 0.0)) + 64.0
            for device, value in residual.items() if value >= 0)
        return {
            "outcomes": outcomes,
            "residual_memory_used_mib": residual,
            "release_baseline_memory_used_mib": self.release_baseline_mib,
            "vram_returned_to_baseline": clean,
            "unreaped": [row["pid"] for row in outcomes
                         if row.get("state") == "unreaped"],
            "foreign_processes_touched": 0,
        }


# --------------------------------------------------------------------------
# HTTP probes
# --------------------------------------------------------------------------

def realistic_timeout_is_a_rail_miss(*, round7_time_policy: bool,
                                     server_alive: bool) -> bool:
    """Whether a realistic-probe request timeout is a rail miss, not a stop.

    On the legacy panels `stage_a_request_timeout_seconds` IS
    `ROOT_WALL_RAIL_SECONDS`, so a socket timeout is the same physical event as
    a probe that completes over the rail: a model too slow for the rail. That is
    a rail-bound `NQ` and the panel continues -- but only while the server is
    alive. A server that has exited or stopped answering `/health` is an
    infrastructure failure and must still stop the run, so `server_alive=False`
    keeps the raise. Round 7 removed the rail, so it also keeps the raise.
    """
    return (not round7_time_policy) and server_alive


def first_server_alive(fleet: "ServerFleet") -> bool:
    """True while the first server is still running and answering `/health`.

    Used to tell a rail miss from an infrastructure failure. On the legacy
    panels the realistic probe's request timeout IS the 360 s rail, so a request
    that times out is the same physical event as a probe that completes over the
    rail -- but only while the server is alive. A server that has exited (or
    stopped answering) is an infrastructure failure and must still stop the run,
    so this check is what keeps the timeout-as-rail-miss fix from masking one.
    """
    try:
        process = fleet.processes[0]
        port = fleet.entries[0]["port"]
    except (AttributeError, IndexError, KeyError, TypeError):
        return False
    if process.poll() is not None:
        return False
    try:
        with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5) as response:
            return json.loads(response.read().decode()).get("status") == "ok"
    except Exception:  # noqa: BLE001 -- unreachable health is not alive
        return False


def post_chat(port: int, *, model: str, messages: list[dict[str, Any]],
              timeout: float, tools: list[dict[str, Any]] | None = None,
              max_tokens: int = OUTPUT_CEILING_TOKENS,
              cache_prompt: bool = False) -> dict[str, Any]:
    """The ONLY way this module issues a request, so the frozen sampling
    configuration cannot be forgotten at one call site.

    `cache_prompt` defaults to False -- the safe, boundary-crossing case. It is
    set True only for a turn that CONTINUES a conversation already begun on a
    freshly-erased slot.

    The distinction is the whole point of the cache repair, and it is not a
    softening of it. Cross-boundary reuse is contamination: one root's state
    changing another root's number. WITHIN-root reuse of a conversation's own
    prefix is the workload -- every deployment does it, no other root can observe
    it, and forbidding it does not isolate anything. It only makes each turn
    reprocess the entire history, which on this hardware can put a legitimate
    33k two-turn exchange beyond the historical 360s diagnostic rail.

    Isolation between roots is enforced where it belongs: the slot is erased at
    every root boundary, and the fresh-cache probe (unique nonce, erased slot,
    cache_prompt False) must still report cached_tokens PRESENT and exactly zero.
    """
    payload: dict[str, Any] = {
        "model": model, "messages": messages, "max_tokens": max_tokens,
        # Cache lifecycle, NOT sampling: kept outside FROZEN_SAMPLING so
        # `sampling_json_sha256` is unchanged by it.
        "cache_prompt": bool(cache_prompt),
        **FROZEN_SAMPLING,
    }
    if tools:
        payload["tools"] = tools
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer local"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
        parsed["_elapsed_seconds"] = time.perf_counter() - started
        parsed["_http_status"] = 200
        return parsed
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        return {"_http_status": exc.code, "_error": detail,
                "_elapsed_seconds": time.perf_counter() - started}
    except Exception as exc:  # noqa: BLE001
        _raise_if_timeout(exc, "chat_completion_timeout")
        return {"_http_status": None, "_error": f"{type(exc).__name__}: {exc}",
                "_elapsed_seconds": time.perf_counter() - started}


def _message(response: Mapping[str, Any]) -> dict[str, Any]:
    choices = response.get("choices") or [{}]
    return (choices[0] or {}).get("message") or {}


def _finish_reason(response: Mapping[str, Any]) -> str | None:
    choices = response.get("choices") or [{}]
    return (choices[0] or {}).get("finish_reason")


def _decode_rate(response: Mapping[str, Any]) -> float | None:
    usage = response.get("usage") or {}
    completion = usage.get("completion_tokens")
    elapsed = response.get("_elapsed_seconds")
    try:
        if completion and elapsed and float(elapsed) > 0:
            return float(completion) / float(elapsed)
    except (TypeError, ValueError):
        return None
    return None


def _filler(words: int) -> str:
    """A deterministic filler of `words` words. NOT a token count."""
    return " ".join(f"w{index % 997}" for index in range(max(0, int(words))))


def count_tokens(port: int, text: str, *, timeout: float = 120.0) -> int | None:
    """Ask the SERVER how many tokens this is, using its own tokenizer.

    llama.cpp exposes `/tokenize`. Where it is available this is exact, which is
    the only way a capacity claim about a token ceiling can be honest: a word
    count is not a token count, and the ratio differs per tokenizer -- which is
    precisely what a panel of three different tokenizers guarantees.
    """
    body = json.dumps({"content": text}).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/tokenize", data=body,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        _raise_if_timeout(exc, "tokenize_timeout")
        return None
    tokens = parsed.get("tokens")
    return len(tokens) if isinstance(tokens, list) else None


def build_prompt_of(port: int, target_tokens: int, *, suffix: str = "",
                    timeout: float = 120.0
                    ) -> dict[str, Any]:
    """A prompt the server's own tokenizer measures at ~`target_tokens`.

    Uses `/tokenize` when available and falls back to a bounded proportional
    calibration otherwise. Either way the ACHIEVED count is returned and
    recorded; the gate then checks the provider's `usage.prompt_tokens` rather
    than trusting this estimate.
    """
    words = int(target_tokens * 0.75)
    achieved: int | None = None
    attempts: list[dict[str, Any]] = []
    for attempt in range(STAGE_A_TOKEN_CALIBRATION_ATTEMPTS):
        text = _filler(words) + suffix
        achieved = count_tokens(port, text, timeout=timeout)
        attempts.append({"attempt": attempt, "words": words,
                         "measured_tokens": achieved})
        if achieved is None:
            # No /tokenize endpoint. Fall back to a fixed ratio and let the
            # provider's own usage figure be the check.
            return {"prompt": _filler(int(target_tokens * 0.85)) + suffix,
                    "target_tokens": target_tokens,
                    "measured_tokens": None,
                    "tokenizer_endpoint_available": False,
                    "attempts": attempts}
        if abs(achieved - target_tokens) <= max(64, target_tokens // 200):
            break
        ratio = achieved / max(1, words)
        words = max(1, int(target_tokens / max(ratio, 1e-6)))
    return {"prompt": _filler(words) + suffix, "target_tokens": target_tokens,
            "measured_tokens": achieved, "tokenizer_endpoint_available": True,
            "attempts": attempts}


def erase_slot(port: int, *, slot: int = 0, timeout: float = 30.0
               ) -> dict[str, Any]:
    """Clear one server slot via the pinned server's documented slot API.

    POST /slots/:id_slot?action=erase. The server refuses the action entirely
    unless it was started with --slot-save-path, so the launch line carries it.
    Called at every root boundary and before the fresh-cache probe, so a
    measured root never begins on state left by the previous one.
    """
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/slots/{int(slot)}?action=erase",
        data=b"{}", method="POST",
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")[:400]
        return {"erased": True, "http_status": 200, "slot": int(slot),
                "body": body}
    except urllib.error.HTTPError as exc:
        return {"erased": False, "http_status": exc.code, "slot": int(slot),
                "error": exc.read().decode("utf-8", errors="replace")[:400]}
    except Exception as exc:  # noqa: BLE001
        _raise_if_timeout(exc, "slot_erase_timeout")
        return {"erased": False, "http_status": None, "slot": int(slot),
                "error": f"{type(exc).__name__}: {exc}"}


def fresh_cache_probe(port: int, *, model: str, timeout: float,
                      slot: int = 0) -> dict[str, Any]:
    """Erase the slot, then prove a UNIQUE prompt reports exactly zero reuse.

    The nonce matters: a fixed probe prompt can legitimately hit a warm cache
    from an earlier identical probe, so a zero reading would prove nothing about
    the next root. A prompt no server has seen before cannot be a cache hit, so
    a non-zero `cached_tokens` here is real reuse and nothing else.
    """
    erase = erase_slot(port, slot=slot, timeout=min(timeout, 30.0))
    nonce = uuid.uuid4().hex
    response = post_chat(
        port, model=model, timeout=timeout, max_tokens=8,
        messages=[{"role": "user",
                   "content": f"Unique probe {nonce}. Reply with the word FRESH."}])
    verdict = cache_isolation_verdict(response)
    return {"nonce": nonce, "erase": erase,
            "cached_tokens": verdict.get("cached_tokens"),
            "measured": verdict.get("measured"),
            "passed": bool(verdict.get("passed")),
            "reason": verdict.get("reason"),
            "http_status": response.get("_http_status")}


# The construction target for the realistic multi-turn probe. Prespecified here,
# not tuned to an observation. The FLOOR is unchanged at
# STAGE_A_REALISTIC_MIN_PROMPT_TOKENS (32,768); this is the narrow band the
# builder aims the templated history into so the served prompt lands at or just
# above that floor while leaving the full output ceiling of headroom under the
# 40,960 context.
STAGE_A_REALISTIC_TARGET_BAND = (32768, 33280)
STAGE_A_REALISTIC_BAND_ATTEMPTS = 12


def apply_chat_template(port: int, messages: Sequence[Mapping[str, Any]], *,
                        timeout: float = 120.0
                        ) -> str | None:
    """The history as the CANDIDATE'S OWN template renders it.

    Counting the raw user text under-counts by exactly the template's role
    markers, BOS and turn scaffolding -- which is how a two-turn history aimed
    at 32,768 arrived at 32,714 and failed a floor it was never actually built
    to clear. `/apply-template` returns the string the server will really
    tokenize, so the count is of the thing being served.
    """
    body = json.dumps({"messages": [dict(m) for m in messages]}).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/apply-template", data=body,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        _raise_if_timeout(exc, "apply_template_timeout")
        return None
    prompt = parsed.get("prompt")
    return prompt if isinstance(prompt, str) else None


def templated_token_count(port: int, messages: Sequence[Mapping[str, Any]], *,
                          timeout: float = 120.0
                          ) -> int | None:
    rendered = apply_chat_template(port, messages, timeout=timeout)
    if rendered is None:
        return None
    return count_tokens(port, rendered, timeout=timeout)


def build_history_into_band(
    port: int, *, first_turn: str, assistant_reply: str, suffix: str,
    band: tuple[int, int] = STAGE_A_REALISTIC_TARGET_BAND,
    attempts: int = STAGE_A_REALISTIC_BAND_ATTEMPTS,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Pad the SECOND user turn until the templated history lands in `band`.

    Deterministic: the padding is the same filler used everywhere, the search is
    a plain proportional step then a linear walk, and no randomness enters. Every
    attempt is preserved -- an attempt list that only kept the winner would hide
    a builder that needed ten tries on one tokenizer and one on another.

    The same algorithm runs for every candidate. It does not know which
    tokenizer it is talking to; it asks the server.
    """
    low, high = int(band[0]), int(band[1])
    history_head = [
        {"role": "user", "content": first_turn},
        {"role": "assistant", "content": assistant_reply},
    ]
    record: list[dict[str, Any]] = []
    words = max(1, low // 4)
    best: dict[str, Any] | None = None
    for attempt in range(int(attempts)):
        second = _filler(words) + suffix
        messages = history_head + [{"role": "user", "content": second}]
        measured = templated_token_count(port, messages, timeout=timeout)
        record.append({"attempt": attempt, "words": words,
                       "templated_tokens": measured})
        if measured is None:
            return {"messages": messages, "attempts": record,
                    "templated_tokens": None, "in_band": False,
                    "band": [low, high],
                    "reason": "server exposes no /apply-template or /tokenize"}
        if low <= measured <= high:
            best = {"messages": messages, "attempts": record,
                    "templated_tokens": measured, "in_band": True,
                    "band": [low, high], "words": words}
            break
        # Proportional correction on the SECOND turn only; the first turn and the
        # assistant reply stay fixed so the history remains a real conversation.
        deficit = ((low + high) // 2) - measured
        per_word = max(measured / max(1, words), 1e-6)
        words = max(1, words + int(deficit / per_word))
    if best is None:
        best = {"messages": history_head + [
                    {"role": "user", "content": _filler(words) + suffix}],
                "attempts": record,
                "templated_tokens": record[-1]["templated_tokens"],
                "in_band": False, "band": [low, high], "words": words,
                "reason": f"could not reach [{low},{high}] in {attempts} attempts"}
    return best


def prompt_tokens_of(response: Mapping[str, Any]) -> int | None:
    usage = response.get("usage") or {}
    value = usage.get("prompt_tokens")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def cache_isolation_verdict(response: Mapping[str, Any]) -> dict[str, Any]:
    """Cache isolation passes only when the metric was MEASURED and is zero.

    Extracted from `acquire()` so it can be exercised without a server. It was
    inline, and inline meant untested: the earlier version read
    `details.get("cached_tokens") or 0` and compared that to zero, so a server
    that reports no cached-token metric at all -- indistinguishable from one
    that reuses cache freely -- passed the check whose entire purpose is to
    measure cache reuse. An absent metric is an ASSERTION, not a measurement.
    """
    details = ((response.get("usage") or {}).get("prompt_tokens_details") or {})
    cached = details.get("cached_tokens")
    measured = cached is not None
    if not measured:
        return {"passed": False, "measured": False, "cached_tokens": None,
                "reason": ("the server reported no cached-token metric, so "
                           "cache isolation was ASSERTED rather than measured")}
    if int(cached) != 0:
        return {"passed": False, "measured": True, "cached_tokens": int(cached),
                "reason": ("the server reported reused cache tokens for a "
                           "fresh prompt")}
    return {"passed": True, "measured": True, "cached_tokens": 0,
            "reason": None}


def context_probe_verdict(
    response: Mapping[str, Any], *, minimum_tokens: int, maximum_tokens: int,
    label: str,
) -> dict[str, Any]:
    """A context probe passes only when the PROVIDER reports the token count.

    HTTP 200 proves a request succeeded, not that it carried the prompt the
    probe intended. The claim being made is about a token ceiling, so the
    evidence has to be a token count -- reported by the server, in the registered
    range, with a real termination.
    """
    status = response.get("_http_status")
    if status != 200:
        return {"passed": False,
                "reason": f"{label}_request_failed:{str(response.get('_error'))[:160]}",
                "http_status": status}
    tokens = prompt_tokens_of(response)
    finish = _finish_reason(response)
    if tokens is None:
        return {"passed": False,
                "reason": f"{label}_provider_reported_no_prompt_token_count",
                "http_status": status, "finish_reason": finish}
    if tokens < minimum_tokens:
        return {"passed": False,
                "reason": (f"{label}_served_only_{tokens}_prompt_tokens_"
                           f"below_{minimum_tokens}"),
                "prompt_tokens": tokens, "finish_reason": finish}
    if tokens > maximum_tokens:
        return {"passed": False,
                "reason": (f"{label}_served_{tokens}_prompt_tokens_"
                           f"above_the_{maximum_tokens}_ceiling"),
                "prompt_tokens": tokens, "finish_reason": finish}
    if finish not in {"stop", "length"}:
        return {"passed": False,
                "reason": f"{label}_did_not_terminate_normally:{finish}",
                "prompt_tokens": tokens, "finish_reason": finish}
    return {"passed": True, "prompt_tokens": tokens, "finish_reason": finish,
            "minimum_tokens": minimum_tokens, "maximum_tokens": maximum_tokens,
            "http_status": status}


# --------------------------------------------------------------------------
# individual checks
# --------------------------------------------------------------------------

def _check(passed: bool, reason: str | None = None, **evidence: Any) -> dict[str, Any]:
    record: dict[str, Any] = {"passed": bool(passed)}
    if reason:
        record["reason"] = reason
    record.update(evidence)
    return record


def static_identity_checks(spec: Mapping[str, Any], *, model: Path,
                           registry: Mapping[str, Any],
                           policy: Mapping[str, Any] | None) -> dict[str, Any]:
    """Identity, provenance and licence, resolved before a single request."""
    from causal_branch.round5_titan_exam import (
        gguf_conversion_blockers, licence_blockers, mtp_identity_blockers,
        quantization_blockers,
    )
    checks: dict[str, Any] = {}
    revision = str(spec.get("source_revision") or "")
    checks["source_revision"] = _check(
        bool(revision) and not revision.lower().startswith("pending"),
        None if revision else "source_revision_unbound", value=revision)

    expected = spec.get("expected_sha256")
    checks["lfs_digest"] = _check(
        bool(expected), None if expected else "expected_lfs_digest_unbound",
        expected_sha256=expected,
        source=spec.get("expected_sha256_source"))

    local = sha256_file(model) if model.is_file() else None
    checks["local_sha256"] = _check(
        bool(local) and local == expected,
        None if local == expected else (
            "model_file_absent" if local is None
            else "local_sha256_does_not_match_the_expected_digest"),
        local_sha256=local)

    licence = licence_blockers(candidate=str(spec.get("_candidate")), policy=policy)
    checks["licence"] = _check(not licence, "; ".join(licence) or None,
                               blockers=licence)

    metadata = spec.get("gguf_metadata") or {}
    conversion = gguf_conversion_blockers(
        candidate=str(spec.get("_candidate")),
        filename=str(spec.get("filename") or ""), metadata=metadata,
        expected_architecture=str(spec.get("expected_architecture") or ""),
        expected_block_count=spec.get("expected_block_count"),
        metadata_preserved=bool(metadata))
    architecture_reasons = [r for r in conversion if "architecture" in r]
    block_reasons = [r for r in conversion if "block_count" in r]
    checks["architecture"] = _check(
        not architecture_reasons, "; ".join(architecture_reasons) or None,
        expected=spec.get("expected_architecture"),
        observed=metadata.get("general.architecture") or metadata.get("architecture"))
    checks["block_count"] = _check(
        not block_reasons, "; ".join(block_reasons) or None,
        expected=spec.get("expected_block_count"),
        expected_source=spec.get("expected_block_count_source"),
        observed=metadata.get("block_count"))
    checks["tokenizer"] = _check(
        bool(spec.get("tokenizer_sha256")),
        None if spec.get("tokenizer_sha256") else "tokenizer_sha256_unbound",
        sha256=spec.get("tokenizer_sha256"))
    checks["chat_template"] = _check(
        bool(spec.get("chat_template_sha256")),
        None if spec.get("chat_template_sha256") else "chat_template_sha256_unbound",
        sha256=spec.get("chat_template_sha256"))

    quantization = quantization_blockers(
        candidate=str(spec.get("_candidate")),
        declared=metadata.get("quantization") or spec.get("expected_quantization"),
        expected=spec.get("expected_quantization"),
        independent_source=spec.get("expected_quantization_source"))
    checks["quantization"] = _check(not quantization,
                                    "; ".join(quantization) or None,
                                    expected=spec.get("expected_quantization"))

    mtp = mtp_identity_blockers(
        candidate=str(spec.get("_candidate")), metadata=metadata,
        filename=str(spec.get("filename") or ""),
        speculative_decoding_enabled=bool(
            (registry.get("runtime") or {}).get("speculative_decoding")))
    checks["target_versus_mtp_identity"] = _check(
        not mtp, "; ".join(mtp) or None, blockers=mtp)
    return checks


DEFAULT_CUOBJDUMP = "/usr/local/cuda-12.4/bin/cuobjdump"


def build_checks(registry: Mapping[str, Any], *, server_logs: Sequence[Path],
                 live_residency: Mapping[str, Any] | None = None,
                 cpu_fallback_observed: bool | None = None,
                 ) -> dict[str, Any]:
    """`sm_52` kernels and the binary digest, read from the live build."""
    runtime = registry.get("runtime") or {}
    binary = Path(str(runtime.get("llama_server") or ""))
    expected_digest = runtime.get("llama_server_sha256")
    actual = sha256_file(binary) if binary.is_file() else None
    checks = {
        "binary_digest": _check(
            bool(actual) and actual == expected_digest,
            None if actual == expected_digest else (
                "llama_server_absent" if actual is None
                else "llama_server_digest_does_not_match_the_registry"),
            expected=expected_digest, observed=actual, path=str(binary)),
    }
    # The pinned build must be sm_52 ON THIS MACHINE. Repository support is not
    # a live kernel probe -- and neither is a log banner. The bundle proves it
    # from the compiled cubins, the resolved libraries, the build cache, the
    # binary's own device list, the driver, and live residency.
    text = ""
    for log in server_logs:
        try:
            text += log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    cuda_error = "cuda error" in text.lower()

    # The build directory is a HOST fact and the registry binds it. The old
    # fallback hardcoded `build-sm52`, which on this host names a directory that
    # was never created, so the cache read as unreadable and the check failed on
    # a path rather than on the runtime. Prefer the explicit binding, then the
    # bound build_dir, and only then the historical default.
    toolchain = runtime.get("build_toolchain") or {}
    bound_build_dir = str(toolchain.get("build_dir") or "").strip()
    cmake_cache = (str(toolchain.get("cmake_cache_path") or "").strip()
                   or (str(Path(bound_build_dir) / "CMakeCache.txt")
                       if bound_build_dir else "")
                   or str(Path(str(runtime.get("llama_cpp_root") or ""))
                          / "build-sm52" / "CMakeCache.txt"))
    # The CMake cache is one of five independent witnesses that the bound
    # binary was built for this architecture, and it is the only one that is
    # not derived from the binary itself. If it comes from a DIFFERENT build
    # tree it witnesses a different binary: the Round-7 registry inherited
    # `build-sm120/CMakeCache.txt` from Round 6 while binding
    # `build-sm120-round7/bin/llama-server`, and nothing noticed. Require the
    # cache to live in the build tree the served binary came from.
    cache_mismatch: list[str] = []
    try:
        cache_tree = Path(cmake_cache).resolve().parent
        binary_tree = Path(binary).resolve().parent.parent
        if cmake_cache and str(binary) and cache_tree != binary_tree:
            cache_mismatch.append(
                f"cmake_cache_build_tree_{cache_tree}_is_not_the_served_binary_"
                f"build_tree_{binary_tree}")
    except (OSError, ValueError):
        cache_mismatch.append("cmake_cache_or_binary_path_unresolvable")

    hardware = hardware_profile_of(registry)
    spec = host_spec(hardware)
    bundle = build_runtime_evidence(
        llama_server=binary,
        cmake_cache=cmake_cache,
        cuobjdump=str(toolchain.get("cuobjdump") or DEFAULT_CUOBJDUMP),
        live_residency=dict(live_residency or {}),
        cpu_fallback_observed=(bool(cpu_fallback_observed)
                               if cpu_fallback_observed is not None else None),
        required_architecture=str(spec["cuda_architecture"]),
        required_compute_capability=str(spec["compute_capability"]),
    )
    reasons = runtime_evidence_blockers(
        bundle, expected_binary_sha256=expected_digest, hardware=hardware)
    if cache_mismatch:
        reasons = sorted(set(reasons) | set(cache_mismatch))
    if cuda_error:
        reasons = sorted(set(reasons) | {"server_log_reports_a_cuda_error"})
    checks["sm52_kernels"] = _check(
        not reasons, "; ".join(reasons) or None,
        expected_cuda_architecture=str(spec["cuda_architecture"]),
        evidence_bundle_sha256=bundle.get("bundle_sha256"),
        compiled_architectures=(bundle.get("cuobjdump") or {}).get("architectures"),
        target_cuda_library=(bundle.get("target_cuda_library") or {}).get("soname"),
        cmake_cuda_architectures=(bundle.get("cmake_cache") or {}).get(
            "cuda_architectures"),
        cuda_devices=(bundle.get("list_devices") or {}).get("cuda_devices"),
        live_residency=bundle.get("live_residency"),
        cpu_fallback_observed=bundle.get("cpu_fallback_observed"),
        superseded_check="server_log_grep_for_a_device_banner_this_runtime_never_emits")
    checks["_runtime_evidence_bundle"] = bundle
    return checks


def residency_checks(
    *, fleet: "ServerFleet", baseline: Mapping[str, float],
    sampled: Mapping[str, Any], per_server_memory: Mapping[str, Any],
) -> dict[str, Any]:
    """CPU fallback and device isolation, measured PER SERVER PROCESS.

    The earlier check compared the assigned devices against the "unassigned"
    ones. Under `titan_single_4x` the fleet collectively assigns all four cards,
    so that set was EMPTY and a single-card server allocating on another
    worker's GPU passed. Isolation is a property of one server, so it is proved
    per server: every PID in a server's process group must hold memory only on
    the devices that server declared.
    """
    peak_util = sampled.get("peak_utilisation_percent") or {}
    peak_memory = sampled.get("peak_memory_used_mib") or {}
    assigned = sorted({device for group in fleet.profile["device_groups"]
                       for device in group})

    loaded = {str(device): peak_memory.get(str(device), 0.0)
              - float(baseline.get(str(device), 0.0)) for device in assigned}
    resident = bool(loaded) and all(value > 256 for value in loaded.values())
    busy = max(peak_util.values(), default=0.0)

    violations: list[dict[str, Any]] = []
    per_server: dict[str, Any] = {}
    for entry in per_server_memory.values():
        declared = {int(device) for device in entry["declared_devices"]}
        observed = {int(device) for device in entry["observed_devices"]
                    if device is not None}
        stray = sorted(observed - declared)
        per_server[str(entry["server"])] = {
            "pid": entry["pid"], "process_group_pids": entry["pids"],
            "declared_devices": sorted(declared),
            "observed_devices": sorted(observed),
            "memory_by_device_mib": entry["memory_by_device_mib"],
            "stray_devices": stray,
            "isolated": not stray and bool(observed),
        }
        if stray:
            violations.append({"server": entry["server"], "pid": entry["pid"],
                               "stray_devices": stray})
        elif not observed:
            violations.append({"server": entry["server"], "pid": entry["pid"],
                               "reason": "no compute allocation observed for "
                                         "this server's process group"})

    return {
        "load_at_context_ceiling": _check(
            resident, None if resident else "no model memory resident on an "
            "assigned card at the frozen context ceiling",
            context_tokens=CONTEXT_TOKENS, loaded_mib=loaded),
        "no_cpu_fallback": _check(
            resident and busy > 0.0,
            None if resident and busy > 0.0 else
            "device residency or sustained utilisation absent during generation",
            loaded_mib=loaded,
            peak_utilisation_percent_during_generation=busy,
            mean_utilisation_percent=sampled.get("mean_utilisation_percent"),
            samples=sampled.get("sample_counts"),
            detector=("loaded model + non-zero VRAM on every assigned card + "
                      "utilisation sampled CONCURRENTLY with generation + "
                      "provider usage metadata; NOT a completion-length / "
                      "wall-time ratio, and NOT a post-hoc NVML read")),
        "device_isolation": _check(
            not violations,
            None if not violations else
            f"per-server isolation violated: {json.dumps(violations)[:300]}",
            measured="per_server_process_group",
            per_server=per_server, violations=violations,
            note=("proved per server PID rather than across the fleet: under "
                  "titan_single_4x every card is assigned to SOME worker, so a "
                  "fleet-aggregate check can never detect cross-worker "
                  "allocation")),
        "gpu_utilisation": _check(
            busy > 0.0, None if busy > 0.0 else
            "no GPU utilisation observed while inference was in flight",
            peak_percent=busy,
            peak_by_device=peak_util,
            mean_by_device=sampled.get("mean_utilisation_percent"),
            sample_counts=sampled.get("sample_counts")),
    }


def vram_margin(fleet: ServerFleet) -> dict[str, float]:
    margins: dict[str, float] = {}
    for group in fleet.profile["device_groups"]:
        for device in group:
            margins[str(device)] = gpu_free_mib(device)
    return margins


# --------------------------------------------------------------------------
# the acquisition
# --------------------------------------------------------------------------

class StageADeadline:
    """A finite bound on ONE candidate's Stage A.

    Twenty tool prompts and four terminal probes each have an HTTP diagnostic
    timeout, and with the permitted retry a stalled endpoint can multiply that
    into days. Expiry produces no candidate verdict and stops the launch; the
    manager resumes the same candidate rather than silently dropping its row.
    """

    def __init__(self, seconds: float) -> None:
        self.seconds = float(seconds)
        self.started = time.monotonic()
        self.expired_at: str | None = None

    def remaining(self) -> float:
        return max(0.0, self.seconds - (time.monotonic() - self.started))

    def expired(self) -> bool:
        if self.remaining() <= 0 and self.expired_at is None:
            from datetime import datetime, timezone
            self.expired_at = datetime.now(timezone.utc).isoformat()
        return self.remaining() <= 0

    def budget(self, request_timeout: float) -> float:
        """Never let one request outlive the candidate's whole budget."""
        return max(1.0, min(float(request_timeout), self.remaining()))

    def record(self) -> dict[str, Any]:
        return {"seconds": self.seconds,
                "elapsed_seconds": time.monotonic() - self.started,
                "remaining_seconds": self.remaining(),
                "expired": self.remaining() <= 0,
                "expired_at_utc": self.expired_at}


def stage_a_request_timeout_seconds(registry: Mapping[str, Any]) -> float:
    """Round-7 diagnostic request timeout, or the legacy frozen rail."""
    return (STAGE_A_REQUEST_TIMEOUT_SECONDS
            if panel_version_of(registry) in ROUND7_PANEL_VERSIONS
            else ROOT_WALL_RAIL_SECONDS)


def stage_a_auxiliary_timeout_seconds(registry: Mapping[str, Any]) -> float:
    """Timeout for warmup/tokenizer/template HTTP calls.

    The historical 120 s value remains part of completed-round behavior. For
    Round 7 these calls share the 1,800 s diagnostic request allowance; leaving
    the warmup at 120 s is still a first-token speed test even if every named
    long-context probe uses the longer allowance.
    """
    return (STAGE_A_REQUEST_TIMEOUT_SECONDS
            if panel_version_of(registry) in ROUND7_PANEL_VERSIONS
            else 120.0)


def stage_a_server_start_timeout_seconds(registry: Mapping[str, Any]) -> float:
    """Server-health diagnostic timeout without changing completed rounds."""
    return (ROUND7_SERVER_START_TIMEOUT_SECONDS
            if panel_version_of(registry) in ROUND7_PANEL_VERSIONS
            else HEALTH_TIMEOUT_SECONDS)


def realistic_multiturn_gate(*, capability_passed: bool, inside_rail: bool,
                             registry: Mapping[str, Any]) -> bool:
    """Only Round 7 removes elapsed time from Stage-A membership."""
    return bool(capability_passed and (
        panel_version_of(registry) in ROUND7_PANEL_VERSIONS or inside_rail))


def acquire(
    *,
    candidate: str,
    spec: Mapping[str, Any],
    registry: Mapping[str, Any],
    policy: Mapping[str, Any] | None,
    model_root: Path,
    out_dir: Path,
    topology: str,
    execution_profile: Mapping[str, Any] | None = None,
    lease_holder_pids: Sequence[int] = (),
    timeout_seconds: float = STAGE_A_CANDIDATE_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Start the frozen topology, run every Stage-A probe, and record it all.

    Every return path finalises the SAME evidence -- server log digests, cleanup
    outcome, deadline record, request count. An early return that omitted them
    (a server that failed to start, for instance) produced a record the manager
    could not classify, so a legitimate operational failure became an
    unclassified blocker and no reserve was considered.

    A contaminated host short-circuits before anything is started, because the
    rule is to WAIT rather than measure a machine somebody else is using.
    """
    profile = (dict(execution_profile)
               if execution_profile is not None else topology_profile(topology))
    runtime = registry.get("runtime") or {}
    model = model_root / str(spec.get("filename") or "")
    llama_server = Path(str(runtime.get("llama_server") or ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    # The registry's declared budget wins over the historical default, so a
    # round that needs a longer one says so in its own frozen file rather than
    # moving a constant three completed rounds also depend on.
    deadline = StageADeadline(
        timeout_seconds if timeout_seconds != STAGE_A_CANDIDATE_TIMEOUT_SECONDS
        else stage_a_candidate_timeout_seconds(registry))
    # Round 7 removes the 360 s request timeout as an eligibility path. Keep
    # completed-round acquisition semantics intact when this shared module is
    # used to replay an older registry.
    round7_time_policy = panel_version_of(registry) in ROUND7_PANEL_VERSIONS
    request_timeout_seconds = stage_a_request_timeout_seconds(registry)
    auxiliary_timeout_seconds = stage_a_auxiliary_timeout_seconds(registry)

    record: dict[str, Any] = {
        "artifact_kind": STAGE_A_OBSERVATION_KIND,
        "candidate": candidate,
        "topology": topology,
        "acquisition_module_sha256": acquisition_module_sha256(),
        "acquired_at_utc": utc_now(),
        "host": os.uname().nodename,
        "llama_server_sha256": runtime.get("llama_server_sha256"),
        "runtime_commit": runtime.get("required_commit"),
        "model_requests_issued": 0,
        "owned_pids": [int(pid) for pid in lease_holder_pids],
        "device_inventory": device_inventory(),
        "checks": {},
        "free_vram_mib_at_peak": {},
    }
    fleet = ServerFleet(candidate=candidate, model=model,
                        llama_server=llama_server, topology=topology,
                        out_dir=out_dir,
                        execution_profile=profile,
                        health_timeout_seconds=
                        stage_a_server_start_timeout_seconds(registry))
    checks: dict[str, Any] = {}
    requests_issued = 0
    cleanup: dict[str, Any] = {}
    started_servers = False

    def finalise() -> dict[str, Any]:
        """Everything every return path owes the reader."""
        record["checks"] = checks
        record["model_requests_issued"] = requests_issued
        record["stage_a_deadline"] = deadline.record()
        record["server_logs"] = [
            {"path": str(path),
             "sha256": sha256_file(path) if path.is_file() else None}
            for path in fleet.log_paths]
        record["server_log_sha256"] = hashlib.sha256(
            "".join(str(row["sha256"]) for row in record["server_logs"]
                    ).encode("utf-8")).hexdigest()
        record["cleanup"] = cleanup
        if started_servers:
            checks["process_group_cleanup"] = _check(
                bool(cleanup) and not cleanup.get("unreaped")
                and cleanup.get("vram_returned_to_baseline"),
                None if (cleanup and not cleanup.get("unreaped")
                         and cleanup.get("vram_returned_to_baseline"))
                else "a server survived cleanup or a card did not release its "
                     "memory",
                **cleanup)
        record["checks"] = checks
        return record

    # ---- occupancy BEFORE anything is started ------------------------------
    pre = occupancy_samples(owned_pids=lease_holder_pids)
    # `hardware=` is REQUIRED. occupancy_blockers defaults to the Titan
    # profile's four cards, so omitting it on any other host makes a perfectly
    # clean two-card machine report `occupancy_sampled_2_of_4_cards` and turns
    # every candidate into a TIMING_CONTAMINATED_NONVERDICT that no amount of
    # waiting can clear. Readiness always passed it; this LIVE path did not.
    held_devices = sorted({int(device) for group in profile["device_groups"]
                           for device in group})
    verdict = occupancy_verdict(occupancy_blockers(
        pre, owned_pids=lease_holder_pids,
        hardware=hardware_profile_of(registry), devices=held_devices))
    record["occupancy_samples"] = pre
    record["occupancy"] = verdict
    if not verdict["clear"]:
        record["nonverdict"] = True
        record["note"] = ("host contaminated before any server was started; "
                          "nothing was measured and nothing was killed")
        return finalise()

    baseline = {str(row["index"]): row["memory_used_mib"]
                for row in record["device_inventory"]}
    fleet.release_baseline_mib = {
        str(device): float(baseline.get(str(device), 0.0))
        for device in held_devices}

    spec = dict(spec)
    spec["_candidate"] = candidate
    checks.update(static_identity_checks(spec, model=model, registry=registry,
                                         policy=policy))

    try:
        entries = fleet.start()
        started_servers = True
        healthy = fleet.wait_healthy()
        checks["concurrent_servers"] = _check(
            all(healthy) and len(healthy) == profile["servers"],
            None if all(healthy) else "not every declared server became healthy",
            required=profile["servers"], healthy=healthy, servers=entries)
        if not all(healthy):
            if any(entry.get("health_failure") == "startup_timeout"
                   for entry in entries):
                record["stage_a_timed_out"] = True
                record["nonverdict_reasons"] = [
                    "llama_server_startup_diagnostic_timeout"]
                record["note"] = (
                    "a server stayed alive but did not become healthy before "
                    "the startup diagnostic timeout; no candidate verdict exists")
                return finalise()
            # A legitimate operational failure -- a LOAD failure, which is a
            # frozen reserve trigger. It must arrive as a complete record.
            record["note"] = ("one or more servers failed to become healthy; "
                              "this is a load failure, not an unclassified "
                              "blocker")
            return finalise()

        first_port = entries[0]["port"]

        # ---- provider metadata and response model alias --------------------
        warm = post_chat(first_port, model=candidate,
                         messages=[{"role": "user", "content": "Reply with OK."}],
                         timeout=deadline.budget(auxiliary_timeout_seconds))
        requests_issued += 1
        alias = warm.get("model")
        checks["response_model_alias"] = _check(
            alias == candidate,
            None if alias == candidate else
            f"response model {alias!r} is not the bound candidate id",
            observed=alias, expected=candidate)
        usage = warm.get("usage") or {}
        checks["provider_metadata"] = _check(
            usage.get("completion_tokens") is not None
            and usage.get("prompt_tokens") is not None,
            None if usage else "provider returned no usage metadata",
            usage=usage)

        # ---- residency, sampled CONCURRENTLY with generation ---------------
        assigned = sorted({device for group in profile["device_groups"]
                           for device in group})
        long_prompt = build_prompt_of(first_port, 4096,
                                      suffix="\nReply with the word READY.",
                                      timeout=deadline.budget(
                                          auxiliary_timeout_seconds))
        with NvmlSampler(assigned) as sampler:
            post_chat(first_port, model=candidate,
                      messages=[{"role": "user", "content": long_prompt["prompt"]}],
                      timeout=deadline.budget(request_timeout_seconds))
            requests_issued += 1
            # Per-process allocation, read while the servers are still up.
            allocations = compute_apps()
        sampled = sampler.summary()
        record["nvml_sampling"] = sampled

        per_server_memory: dict[str, Any] = {}
        for entry in entries:
            pids = process_group_pids(entry["pid"])
            mine = [row for row in allocations if row["pid"] in pids]
            memory_by_device: dict[str, float] = {}
            for row in mine:
                key = str(row["device"])
                memory_by_device[key] = memory_by_device.get(key, 0.0) + row[
                    "used_memory_mib"]
            per_server_memory[str(entry["server"])] = {
                "server": entry["server"], "pid": entry["pid"],
                "pids": sorted(pids),
                "declared_devices": list(entry["devices"]),
                "observed_devices": [row["device"] for row in mine],
                "memory_by_device_mib": memory_by_device,
            }
        record["per_server_memory"] = per_server_memory
        checks.update(residency_checks(
            fleet=fleet, baseline=baseline, sampled=sampled,
            per_server_memory=per_server_memory))

        record["free_vram_mib_at_peak"] = vram_margin(fleet)
        checks["free_vram_margin"] = _check(
            True, None,
            note="evaluated from free_vram_mib_at_peak by the gate",
            observed=record["free_vram_mib_at_peak"])

        # ---- capacity probe: token-verified, SEPARATE diagnostic timeout ---
        if deadline.expired():
            return _deadline_exceeded(record, checks, finalise)
        capacity_prompt = build_prompt_of(
            first_port, STAGE_A_CAPACITY_PROBE_TOKENS,
            suffix="\nReply with the word FITS.",
            timeout=deadline.budget(auxiliary_timeout_seconds))
        capacity = post_chat(
            first_port, model=candidate,
            messages=[{"role": "user", "content": capacity_prompt["prompt"]}],
            timeout=deadline.budget(STAGE_A_CAPACITY_DIAGNOSTIC_TIMEOUT_SECONDS),
            max_tokens=32)
        requests_issued += 1
        capacity_verdict = context_probe_verdict(
            capacity, minimum_tokens=STAGE_A_CAPACITY_MIN_PROMPT_TOKENS,
            maximum_tokens=STAGE_A_CAPACITY_MAX_PROMPT_TOKENS, label="capacity")
        checks["capacity_probe"] = _check(
            capacity_verdict["passed"], capacity_verdict.get("reason"),
            target_prompt_tokens=STAGE_A_CAPACITY_PROBE_TOKENS,
            calibration=capacity_prompt,
            diagnostic_timeout_seconds=STAGE_A_CAPACITY_DIAGNOSTIC_TIMEOUT_SECONDS,
            judged_against_root_rail=False,
            elapsed_seconds=capacity.get("_elapsed_seconds"),
            **{k: v for k, v in capacity_verdict.items()
               if k not in {"passed", "reason"}})

        # ---- realistic multi-turn; the historical rail is diagnostic -------
        if deadline.expired():
            return _deadline_exceeded(record, checks, finalise)
        started = time.perf_counter()
        realistic_timed_out = False

        def _realistic_turn(messages: list[dict[str, Any]], *, cache_prompt: bool):
            """One realistic-probe turn, with a timeout classified correctly.

            On the legacy panels `stage_a_request_timeout_seconds` IS
            `ROOT_WALL_RAIL_SECONDS`, so a socket timeout is the same physical
            event as a probe that completes over the rail: a model too slow for
            the rail. Treat it as a rail miss so the row is `NQ` and the panel
            continues -- but ONLY while the server is still alive. A server that
            has exited or stopped answering `/health` is an infrastructure
            failure and still raises, so this cannot mask one. Round 7 removed
            the rail, so it keeps the raise.
            """
            try:
                response = post_chat(
                    first_port, model=candidate, messages=messages,
                    timeout=deadline.budget(request_timeout_seconds),
                    cache_prompt=cache_prompt)
                return response, False
            except StageARequestTimeout:
                if not realistic_timeout_is_a_rail_miss(
                        round7_time_policy=round7_time_policy,
                        server_alive=first_server_alive(fleet)):
                    raise
                return ({"_http_status": None,
                         "_error": "chat_completion_timeout",
                         "_elapsed_seconds": time.perf_counter() - started},
                        True)

        first_turn = build_prompt_of(
            first_port, STAGE_A_REALISTIC_BUCKET_TOKENS // 2,
            suffix="\nSummarise in one sentence.",
            timeout=deadline.budget(auxiliary_timeout_seconds))
        history = [{"role": "user", "content": first_turn["prompt"]}]
        realistic, realistic_timed_out = _realistic_turn(history, cache_prompt=False)
        requests_issued += 1
        band_build: dict[str, Any] = {}
        if not realistic_timed_out and realistic.get("_http_status") == 200:
            reply = _message(realistic)
            # Build the SECOND turn against the fully chat-templated history,
            # measured with this candidate's own template and tokenizer, so the
            # served prompt clears the 32,768 floor rather than landing just
            # under it as an untemplated word estimate did.
            band_build = build_history_into_band(
                first_port,
                first_turn=first_turn["prompt"],
                assistant_reply=str(reply.get("content") or ""),
                suffix="\nNow reply with the word DONE.",
                timeout=deadline.budget(auxiliary_timeout_seconds))
            history = list(band_build["messages"])
            # SECOND TURN of the same conversation: it continues a history that
            # began on this slot, so its own prefix may be reused. This is the
            # multi-turn workload the rail is measuring, not cross-root reuse.
            realistic, realistic_timed_out = _realistic_turn(
                history, cache_prompt=True)
            requests_issued += 1
        elapsed = time.perf_counter() - started
        realistic_verdict = context_probe_verdict(
            realistic, minimum_tokens=STAGE_A_REALISTIC_MIN_PROMPT_TOKENS,
            maximum_tokens=CONTEXT_TOKENS, label="realistic_multiturn")
        # The elapsed time is RECORDED and does not gate. It used to: this check
        # failed a candidate whose 32,768-token multi-turn request took longer
        # than the 360 s root rail, and that is the single check that NQ'd
        # gemma-4-12b-it on TITAN -- a statement about Maxwell, not about Gemma.
        #
        # Removing the rail from Stage B and leaving it here would have moved
        # the same exclusion one stage earlier and made it worse: a candidate
        # rejected at Stage A never reaches the exam at all, so a slow model, or
        # a fast model on a card whose clocks fell because a neighbour was
        # busy, would be reported as incapable rather than as slow. On a shared
        # host the neighbours change hourly, so this gate would also have made
        # membership depend on when the probe happened to run.
        #
        # What the probe still checks is a CAPABILITY claim and still gates:
        # that the model can accept, hold and answer a genuine 32,768-token
        # multi-turn history at this exam's ceiling. Slowness costs GPU-hours,
        # and the selection rule is denominated in GPU-hours, so it is already
        # charged there -- once, in the right place, rather than twice.
        inside_rail = (not realistic_timed_out) and elapsed < ROOT_WALL_RAIL_SECONDS
        realistic_passed = realistic_multiturn_gate(
            capability_passed=bool(realistic_verdict["passed"]),
            inside_rail=inside_rail, registry=registry)
        realistic_reason = realistic_verdict.get("reason")
        if realistic_timed_out:
            # The request timed out at the rail while the server stayed alive:
            # the same outcome as a probe that completes over the rail, and the
            # same reason string, so the two paths cannot drift apart.
            realistic_passed = False
            realistic_reason = "realistic_multiturn_probe_exceeded_root_wall_rail"
        elif realistic_verdict["passed"] and not round7_time_policy and not inside_rail:
            realistic_reason = "realistic_multiturn_probe_exceeded_root_wall_rail"
        checks["realistic_multiturn_probe"] = _check(
            realistic_passed, realistic_reason if not realistic_passed else None,
            bucket_tokens=STAGE_A_REALISTIC_BUCKET_TOKENS,
            elapsed_seconds=elapsed,
            request_timed_out=realistic_timed_out,
            rail_seconds_DIAGNOSTIC_ONLY=ROOT_WALL_RAIL_SECONDS,
            slower_than_the_historical_360s_rail=not inside_rail,
            judged_against_root_rail=not round7_time_policy,
            minimum_prompt_tokens=STAGE_A_REALISTIC_MIN_PROMPT_TOKENS,
            construction_band=list(STAGE_A_REALISTIC_TARGET_BAND),
            construction_attempts=band_build.get("attempts"),
            templated_tokens=band_build.get("templated_tokens"),
            construction_in_band=band_build.get("in_band"),
            construction_method=("fully chat-templated history measured with the "
                                 "candidate's own template via /apply-template "
                                 "and its own tokenizer via /tokenize"),
            **{k: v for k, v in realistic_verdict.items()
               if k not in {"passed", "reason"}})

        # ---- 20 fixed tool prompts -----------------------------------------
        observed = malformed = 0
        tool_detail = []
        repetitions = STAGE_A_TOOL_PROMPTS // len(TOOL_PROMPTS)
        for _ in range(repetitions):
            for prompt in TOOL_PROMPTS:
                if deadline.expired():
                    break
                response = post_chat(
                    first_port, model=candidate,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=deadline.budget(request_timeout_seconds),
                    tools=PROBE_TOOLS)
                requests_issued += 1
                calls = _message(response).get("tool_calls") or []
                for call in calls:
                    observed += 1
                    function = (call or {}).get("function") or {}
                    name = function.get("name")
                    if name not in {"convert_units", "lookup_timezone"}:
                        malformed += 1
                        continue
                    try:
                        arguments = json.loads(function.get("arguments") or "{}")
                    except json.JSONDecodeError:
                        malformed += 1
                        continue
                    required = ({"value", "from_unit", "to_unit"}
                                if name == "convert_units" else {"city"})
                    if not required <= set(arguments):
                        malformed += 1
                tool_detail.append({"prompt": prompt, "calls": len(calls),
                                    "http_status": response.get("_http_status")})
        checks["tool_call_probe"] = _check(
            observed >= 1 and (malformed / observed if observed else 1.0) <= 0.02,
            None, prompts=STAGE_A_TOOL_PROMPTS,
            prompts_issued=len(tool_detail), observed_calls=observed,
            malformed_calls=malformed, detail=tool_detail)
        if deadline.expired():
            return _deadline_exceeded(record, checks, finalise)

        # ---- 4 terminal-answer probes, one permitted retry ------------------
        terminal_records = []
        terminal_passed = True
        for prompt in TERMINAL_PROMPTS[:STAGE_A_TERMINAL_PROMPTS]:
            if deadline.expired():
                terminal_passed = False
                break
            response = post_chat(first_port, model=candidate,
                                 messages=[{"role": "user", "content": prompt}],
                                 timeout=deadline.budget(request_timeout_seconds))
            requests_issued += 1
            verdict_one = terminal_answer_verdict(
                finish_reason=_finish_reason(response),
                content=_message(response).get("content"), retried=False)
            if not verdict_one["passed"] and verdict_one.get("retry_permitted"):
                # The ONE prespecified retry, at the already frozen ceiling.
                response = post_chat(
                    first_port, model=candidate,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=deadline.budget(request_timeout_seconds),
                    max_tokens=OUTPUT_CEILING_TOKENS)
                requests_issued += 1
                verdict_one = terminal_answer_verdict(
                    finish_reason=_finish_reason(response),
                    content=_message(response).get("content"), retried=True)
            terminal_records.append({"prompt": prompt, **verdict_one})
            terminal_passed = terminal_passed and verdict_one["passed"]
        checks["terminal_answer_probe"] = _check(
            terminal_passed,
            None if terminal_passed else "a terminal-answer probe did not settle",
            prompts=STAGE_A_TERMINAL_PROMPTS, records=terminal_records,
            output_ceiling_tokens=OUTPUT_CEILING_TOKENS)

        # ---- repeated-request variation ------------------------------------
        contents = []
        for _ in range(REPEATED_REQUEST_TRIALS):
            if deadline.expired():
                break
            response = post_chat(
                first_port, model=candidate,
                messages=[{"role": "user",
                           "content": "List three prime numbers, comma separated."}],
                timeout=deadline.budget(request_timeout_seconds))
            requests_issued += 1
            contents.append(_message(response).get("content"))
        checks["repeated_request_variation"] = _check(
            bool(contents), None if contents else "no repeated request completed",
            trials=len(contents),
            identical_responses=len({str(value) for value in contents}) == 1,
            responses=contents,
            note=("measured and recorded, never repaired. Variation here is a "
                  "property of the candidate that WP1-D quantifies later; it is "
                  "not a Stage-A failure"))

        # ---- network denial -------------------------------------------------
        denied = True
        denial_detail: str | None = None
        try:
            urllib.request.urlopen(NETWORK_DENIAL_TARGET, timeout=3)
            denied = False
            denial_detail = "an outbound request from the harness host succeeded"
        except Exception as exc:  # noqa: BLE001
            denial_detail = f"{type(exc).__name__}"
        checks["network_denial"] = _check(
            denied, None if denied else denial_detail,
            probe=NETWORK_DENIAL_TARGET, observed=denial_detail)

        # ---- cache isolation: erase the slot, then a UNIQUE-nonce probe -----
        # The criterion is unchanged and is not relaxed: the metric must be
        # PRESENT and exactly zero. What changed is that the slot is cleared
        # first and the prompt is unique, so a zero reading is evidence about
        # the next root rather than an accident of a warm identical probe.
        probe = fresh_cache_probe(
            first_port, model=candidate,
            timeout=deadline.budget(request_timeout_seconds))
        requests_issued += 1
        checks["cache_isolation"] = _check(
            probe["passed"], probe["reason"],
            cached_tokens=probe["cached_tokens"],
            measured=probe["measured"],
            slots_per_server=1,
            nonce=probe["nonce"],
            slot_erase=probe["erase"],
            wire_cache_prompt=False,
            server_cache_flags=list(CACHE_ISOLATION_ARGV),
            note=("passing requires the metric to be PRESENT and zero. The slot "
                  "is erased and the prompt carries a fresh nonce, so a zero "
                  "here cannot be a stale hit on an identical earlier probe"))

        # ---- Pi microtrajectory ---------------------------------------------
        if not deadline.expired():
            checks["pi_microtrajectory"] = pi_microtrajectory(
                registry=registry, candidate=candidate, port=first_port,
                out_dir=out_dir, deadline_seconds=deadline.budget(
                    request_timeout_seconds))

        # ---- two-card coherence on BOTH pairs --------------------------------
        if profile["gpus_per_worker"] > 1:
            symmetry = []
            for context in STAGE_A_COHERENCE_PROBE_CONTEXTS:
                if deadline.expired():
                    break
                prompt, expected_token = COHERENCE_PROBES[context]
                per_pair = []
                for entry in entries:
                    built = build_prompt_of(entry["port"], max(64, context - 64),
                                            suffix="\n" + prompt,
                                            timeout=deadline.budget(
                                                auxiliary_timeout_seconds))
                    response = post_chat(
                        entry["port"], model=candidate,
                        messages=[{"role": "user", "content": built["prompt"]}],
                        timeout=deadline.budget(request_timeout_seconds),
                        max_tokens=64)
                    requests_issued += 1
                    content = str(_message(response).get("content") or "")
                    per_pair.append({
                        "server": entry["server"], "devices": entry["devices"],
                        "expected": expected_token,
                        "observed": content[:120],
                        "prompt_tokens": prompt_tokens_of(response),
                        "coherent": expected_token in content,
                        "model": response.get("model"),
                    })
                coherent = all(row["coherent"] for row in per_pair)
                identities = {row["model"] for row in per_pair}
                checks[f"output_coherence_{context // 1024}k"] = _check(
                    coherent,
                    None if coherent else
                    "garbled or incorrect output on at least one GPU pair",
                    context_tokens=context, pairs=per_pair,
                    on_failure=("operational failure; NEVER a reason to change "
                                "the split mode, add CPU offload, shrink the "
                                "context"))
                symmetry.append(coherent and len(identities) <= 1)
            checks["pair_symmetry"] = _check(
                bool(symmetry) and all(symmetry),
                None if symmetry and all(symmetry) else
                "the two GPU pairs did not behave equivalently",
                per_context=list(STAGE_A_COHERENCE_PROBE_CONTEXTS))

        if deadline.expired():
            return _deadline_exceeded(record, checks, finalise)
    except StageARequestTimeout as exc:
        record["stage_a_timed_out"] = True
        record["nonverdict_reasons"] = [str(exc)[:300]]
        record["note"] = (
            "a diagnostic HTTP timeout expired; elapsed time is not a "
            "candidate-local Stage-A verdict")
    except Exception as exc:  # noqa: BLE001
        # Even an unexpected failure returns a COMPLETE record, so the manager
        # classifies it rather than meeting a half-written file.
        checks["acquisition_error"] = _check(
            False, f"{type(exc).__name__}: {str(exc)[:200]}")
    finally:
        if started_servers:
            cleanup = fleet.stop()

    # Live witnesses the bundle needs, taken from what this acquisition already
    # measured rather than probed again: peak per-device residency during the
    # kernel requests, and the CPU-fallback verdict.
    _sampled = (record.get("nvml_sampling") or {})

    def _max_over_devices(mapping: Any) -> float | None:
        """`peak_*` are dicts keyed by device index, not scalars."""
        if isinstance(mapping, Mapping):
            values = []
            for value in mapping.values():
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue
            return max(values) if values else None
        try:
            return float(mapping)
        except (TypeError, ValueError):
            return None

    _live = {
        "used_memory_mib_during": _max_over_devices(
            _sampled.get("peak_memory_used_mib")),
        "utilisation_percent": _max_over_devices(
            _sampled.get("peak_utilisation_percent")),
        "per_device_peak_memory_mib": _sampled.get("peak_memory_used_mib"),
        "source": "nvml sampling during the Stage-A kernel requests",
    }
    _fallback = checks.get("no_cpu_fallback")
    _fallback_observed = (None if not isinstance(_fallback, Mapping)
                          else (not bool(_fallback.get("passed"))))
    _build = build_checks(registry, server_logs=fleet.log_paths,
                          live_residency=_live,
                          cpu_fallback_observed=_fallback_observed)
    # The bundle is EVIDENCE, not a check. Leaving it in `checks` gives the
    # record an entry with no `passed` key, which any consumer that iterates
    # checks would have to special-case.
    record["runtime_evidence_bundle"] = _build.pop("_runtime_evidence_bundle", None)
    checks.update(_build)
    return finalise()


def _deadline_exceeded(record: dict[str, Any], checks: dict[str, Any],
                       finalise) -> dict[str, Any]:
    checks["stage_a_candidate_timeout"] = _check(
        False,
        "Stage A exceeded its registry-derived per-candidate budget",
        terminal_state=TERMINAL_STAGE_A_TIMEOUT)
    record["stage_a_timed_out"] = True
    record["nonverdict_reasons"] = ["stage_a_candidate_deadline_exceeded"]
    return finalise()


def pi_rpc_handshake(*, runtime: Mapping[str, Any], candidate: str,
                     port: int, scratch: Path) -> dict[str, Any]:
    """Start Pi and exchange ONE native command. No model request is issued.

    Separates "Pi will not start" from "the model did not answer". Both used to
    arrive as `RpcError: Pi process exited before responding`, which named
    neither. On failure the full launch diagnostics are returned -- exit code,
    stderr tail, argv digest, cwd, Node executable and version, and the entry
    digest -- so the next step is a reading rather than a re-run.
    """
    try:
        from causal_branch.adapters.pi_agent import (
            PiAgentAdapter, resolve_node_executable,
        )
        from causal_branch.registered_tools import ToolBridge
        from causal_branch.round5_titan_stage_b_execution import (
            ALLOWED_TOOLS, _endpoint,
        )
        node = resolve_node_executable()
        entry = Path(str(runtime["pi_entry"]))
        # Fail on the missing file rather than on a silent RPC stall. Spawning
        # Node against an entry that does not exist leaves the child dead and
        # the handshake waiting, which is how a 45-minute Stage-A hang looked
        # from the outside.
        if not entry.is_file():
            return {"passed": False,
                    "reason": f"pi_entry does not exist on this host: {entry}",
                    "node_executable": node, "pi_entry": str(entry),
                    "model_requests": 0}
        workspace = scratch / "handshake-workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        bridge = ToolBridge(workspace_root=workspace,
                            allowed_tools=list(ALLOWED_TOOLS))
        adapter = PiAgentAdapter(
            pi_entry=entry, endpoint=_endpoint(port, candidate),
            system_prompt=Path(str(runtime["system_prompt"])),
            extension=Path(str(runtime["tool_extension"])),
            allowed_tools=list(ALLOWED_TOOLS), tool_bridge=bridge)
        result = adapter.rpc_handshake(
            agent_dir=scratch / "handshake-agent",
            session_dir=scratch / "handshake-session",
            working_dir=workspace,
            runtime_dir=Path(tempfile.mkdtemp(prefix="r5-handshake-rt-")))
        return {"passed": bool(result.get("ok")),
                "reason": result.get("reason"),
                "node_executable": node,
                "node_version": result.get("node_version"),
                "pi_entry": str(entry),
                "commands": result.get("commands"),
                "diagnostics": result.get("diagnostics"),
                "model_requests": 0}
    except Exception as exc:  # noqa: BLE001
        diagnostics = getattr(exc, "diagnostics", None)
        return {"passed": False,
                "reason": f"{type(exc).__name__}: {str(exc)[:300]}",
                "diagnostics": diagnostics, "model_requests": 0}


def pi_microtrajectory(*, registry: Mapping[str, Any], candidate: str,
                       port: int, out_dir: Path,
                       deadline_seconds: float = STAGE_A_REQUEST_TIMEOUT_SECONDS
                       ) -> dict[str, Any]:
    """One Pi-to-llama.cpp tool microtrajectory with retained events."""
    runtime = registry.get("runtime") or {}
    required = ("pi_entry", "system_prompt", "tool_extension")
    missing = [field for field in required if not runtime.get(field)]
    if missing:
        return _check(False,
                      f"pi microtrajectory not runnable: unbound {','.join(missing)}",
                      unbound=missing)
    # BOUND IS NOT PRESENT. Every field above is a PATH, and a path that is
    # merely a non-empty string still sends `node` at a file that may not be
    # there. When `pi_entry` pointed at an unbuilt `dist/rpc-entry.js`, Node
    # resolved, the entry did not, and the RPC handshake blocked until Stage A
    # hit its 2700 s outer bound -- once per candidate, with nothing measured.
    # Readiness cannot catch this: `runtime_schema_blockers` deliberately checks
    # presence only, because host paths are a host question. This IS the host.
    absent = [field for field in required
              if not Path(str(runtime.get(field))).is_file()]
    if absent:
        detail = {field: str(runtime.get(field)) for field in absent}
        return _check(False,
                      "pi microtrajectory not runnable: bound but absent on "
                      f"this host: {','.join(absent)}",
                      absent=detail)
    scratch = Path(tempfile.mkdtemp(prefix=f"r5-stagea-{candidate}-"))
    try:
        from causal_branch.adapters.pi_agent import PiAgentAdapter
        from causal_branch.registered_tools import ToolBridge
        from causal_branch.substrate_identity import SubstrateIdentity
        from causal_branch.round5_titan_stage_b_execution import (
            ALLOWED_TOOLS, _endpoint,
        )

        # NATIVE RPC HANDSHAKE FIRST. Start Pi and exchange one command that
        # touches no model, so a launch failure is separated from a serving
        # failure. Without this, "Pi exited" and "the model never answered" are
        # the same message -- and the first of them was, in fact, a missing Node
        # interpreter rather than anything to do with the candidate.
        handshake = pi_rpc_handshake(runtime=runtime, candidate=candidate,
                                     port=port, scratch=scratch)
        if not handshake.get("passed"):
            return _check(False,
                          f"pi rpc handshake failed: {handshake.get('reason')}",
                          handshake=handshake)

        workspace = scratch / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "note.txt").write_text("probe\n", encoding="utf-8")
        bridge = ToolBridge(workspace_root=workspace,
                            allowed_tools=list(ALLOWED_TOOLS))
        adapter = PiAgentAdapter(
            pi_entry=Path(str(runtime["pi_entry"])),
            endpoint=_endpoint(port, candidate),
            system_prompt=Path(str(runtime["system_prompt"])),
            extension=Path(str(runtime["tool_extension"])),
            allowed_tools=list(ALLOWED_TOOLS), tool_bridge=bridge)
        run = adapter.run_turn(
            agent_dir=scratch / "agent", session_dir=scratch / "session",
            working_dir=workspace,
            runtime_dir=Path(tempfile.mkdtemp(prefix="r5-stagea-rt-")),
            prompt=("Read note.txt with read_artifact, then stop. "
                    "This is a non-scientific connectivity probe."),
            run_id="round5-titan-stage-a", branch_id="stage-a-probe",
            regime_id="probe", root_id="stage-a-probe",
            identity=SubstrateIdentity(
                base_url=f"http://127.0.0.1:{port}/v1", model_id=candidate,
                expected_system_fingerprint=None, enforce_fingerprint=False),
            wall_clock_deadline_seconds=deadline_seconds)
        assistant = [event for event in run.events
                     if event.get("type") == "message_completed"]
        tools = [event for event in run.events
                 if event.get("type") in {"tool_started", "tool_completed"}]
        trace = out_dir / "pi_microtrajectory_events.json"
        trace.write_text(json.dumps(run.events, indent=2, default=str),
                         encoding="utf-8")
        ok = bool(assistant) and bool(tools)
        return _check(ok,
                      None if ok else "no retained assistant or tool events",
                      terminal=run.terminal,
                      assistant_events=len(assistant), tool_events=len(tools),
                      events_retained=len(run.events), trace=str(trace))
    except Exception as exc:  # noqa: BLE001
        return _check(False, f"{type(exc).__name__}: {str(exc)[:200]}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
