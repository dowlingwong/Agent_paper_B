"""Run-level worker -> endpoint -> physical GPU -> serving-process mapping (F07).

A branch record that says only "owner: worker_a" attributes nothing: which
card, which server process, which model file and which code revision answered
it must be recoverable after the run, and must be the SAME for every branch of
the run. So the mapping is frozen once per run, digested, written to the
ledger as `run_device_mapping`, and every branch carries `{owner,
mapping_sha256}` plus whatever it observed directly (a GPU UUID reported by
the server, a base URL); the validator checks that the reference resolves and
that direct observations agree with the mapping.

Physical GPU identity is the UUID (`GPU-...`). A CUDA index is a LOGICAL
position that depends on `CUDA_VISIBLE_DEVICES` and enumeration order; it is
recorded beside the UUID and never used as identity. Serving-process identity
(pid, start time, argv digest) is recorded when the launcher supplies it and
marked `not_provided` otherwise -- it is never invented.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

MAPPING_SCHEMA = "run_device_mapping/v1"
ATTESTATION_SCHEMA = "serving_attestation/v1"
#: Environment variable through which a launcher hands its serving attestation
#: to the workload it starts (the soak producer and `causal_branch.cli e0-execute`).
ATTESTATION_ENV = "E0_SERVING_ATTESTATION"
#: A physical NVIDIA GPU identity. Sentinels such as `unobserved` never match.
GPU_UUID_RE = re.compile(r"^GPU-[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
REQUIRED_PROCESS_FIELDS = ("pid", "start_ticks", "boot_id", "cmdline")


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def mapping_digest(mapping: Mapping[str, Any]) -> str:
    """Recompute the canonical digest over every field except the digest itself."""
    body = {k: v for k, v in mapping.items() if k != "mapping_sha256"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def is_physical_gpu_uuid(value: Any) -> bool:
    return isinstance(value, str) and bool(GPU_UUID_RE.match(value))


def build_run_device_mapping(
    *,
    run_id: str,
    workers: Sequence[Mapping[str, Any]],
    runtime: Mapping[str, Any],
    code_revision: str | None,
    serving_processes: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Freeze the mapping.

    ``workers``: one entry per owner with `owner`, `base_url`, `gpu_uuid`
    (physical), optional `cuda_visible_devices`, `logical_cuda_index`,
    `endpoint_config`, `endpoint_config_sha256`.
    ``runtime``: model/runtime/config digests (gguf_sha256, llama_server_sha256,
    llama_cpp_commit, tokenizer_sha256, chat_template_sha256, sampling, ...).
    ``serving_processes``: owner -> {pid, started_at_utc, argv_sha256, ...}
    from the launcher, when it supplies them.
    """
    entries = []
    seen_owners: set[str] = set()
    for item in workers:
        owner = str(item["owner"])
        if owner in seen_owners:
            raise ValueError(f"duplicate owner in device mapping: {owner}")
        seen_owners.add(owner)
        gpu_uuid = item.get("gpu_uuid")
        if not gpu_uuid:
            raise ValueError(f"{owner}: gpu_uuid (physical) is required")
        attested = dict((serving_processes or {}).get(owner) or {})
        process = dict(attested.get("serving_process") or attested)
        process.pop("cuda_visible_devices", None)
        visible = item.get("cuda_visible_devices") or attested.get("cuda_visible_devices")
        entries.append({
            "owner": owner,
            "base_url": str(item.get("base_url") or ""),
            "endpoint_config": item.get("endpoint_config"),
            "endpoint_config_sha256": item.get("endpoint_config_sha256"),
            "gpu_uuid": str(gpu_uuid),
            "cuda_visible_devices": visible,
            "cuda_device_order": item.get("cuda_device_order") or attested.get("cuda_device_order"),
            "logical_cuda_index": item.get("logical_cuda_index"),
            "logical_index_note": "logical CUDA position; never used as identity",
            "serving_process": process or {"identity": "not_provided_by_launcher"},
        })
    entries.sort(key=lambda e: e["owner"])
    body = {
        "schema": MAPPING_SCHEMA,
        "run_id": run_id,
        "workers": entries,
        "runtime": dict(runtime),
        "code_revision": code_revision,
    }
    body["mapping_sha256"] = mapping_digest(body)
    return body


def mapping_from_topology(*, run_id: str, topology: Any, bindings: Mapping[str, Any],
                          code_revision: str | None,
                          serving_processes: Mapping[str, Mapping[str, Any]] | None = None
                          ) -> dict[str, Any]:
    """Build the mapping from a resolved WorkerTopology and the binding record."""
    gpu_topology = bindings.get("gpu_topology") or {}
    workers = []
    for index, endpoint in enumerate(topology.endpoints):
        workers.append({
            "owner": endpoint.owner, "base_url": endpoint.base_url,
            "endpoint_config": endpoint.endpoint_config,
            "endpoint_config_sha256": endpoint.endpoint_config_sha256,
            "gpu_uuid": endpoint.gpu_uuid,
            "cuda_visible_devices": None,
            "logical_cuda_index": None,
        })
    runtime = {key: bindings.get(key) for key in (
        "selected_model", "gguf_filename", "gguf_sha256", "quantization", "tokenizer_sha256",
        "chat_template_sha256", "llama_cpp_commit", "llama_server_sha256",
        "sampling_configuration", "context_ceiling_tokens", "cache_isolation_mode")}
    runtime["gpu_topology"] = dict(gpu_topology)
    return build_run_device_mapping(run_id=run_id, workers=workers, runtime=runtime,
                                    code_revision=code_revision,
                                    serving_processes=serving_processes)


def branch_device_reference(mapping: Mapping[str, Any], owner: str,
                            *, observed_gpu_uuid: str | None = None,
                            observed_base_url: str | None = None) -> dict[str, Any]:
    """What a branch record carries: the reference plus direct observations."""
    entry = next((w for w in mapping["workers"] if w["owner"] == owner), None)
    return {
        "owner": owner,
        "mapping_sha256": mapping["mapping_sha256"],
        "mapped_gpu_uuid": entry["gpu_uuid"] if entry else None,
        "mapped_base_url": entry["base_url"] if entry else None,
        "observed_gpu_uuid": observed_gpu_uuid,
        "observed_base_url": observed_base_url,
    }


def serving_attestation(*, run_label: str, servers: Sequence[Mapping[str, Any]],
                        runtime: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The launcher's statement of what it started, taken from what it OWNS.

    ``servers``: one entry per owner with ``owner``, ``base_url``,
    ``gpu_uuid`` (physical, from the binding/topology the launcher pinned),
    ``cuda_visible_devices`` (the environment the launcher gave the server) or
    ``cuda_device_order`` + ``logical_cuda_index``, and ``identity`` -- the
    settled ``/proc`` identity of the server process the launcher spawned
    (``round8_run_supervisor.settled_process_identity``: pid, start_ticks,
    boot_id, exe, cmdline). Nothing is enumerated or guessed here.

    ``runtime`` (S1): what the launcher itself hashed and executed --
    ``llama_server_path`` (resolved) and ``llama_server_sha256``, ``gguf_path``,
    ``gguf_filename`` and ``gguf_sha256``, the served ``context``. It is part of
    the digested body, so the workload cannot restate it differently.
    """
    owners: dict[str, Any] = {}
    for server in servers:
        identity = dict(server.get("identity") or {})
        owners[str(server["owner"])] = {
            "base_url": str(server.get("base_url") or ""),
            "gpu_uuid": server.get("gpu_uuid"),
            "cuda_visible_devices": server.get("cuda_visible_devices"),
            "cuda_device_order": server.get("cuda_device_order"),
            "logical_cuda_index": server.get("logical_cuda_index"),
            "serving_process": {
                "pid": identity.get("pid"), "start_ticks": identity.get("start_ticks"),
                "boot_id": identity.get("boot_id"), "exe": identity.get("exe"),
                "cmdline": identity.get("cmdline"),
                "cmdline_sha256": hashlib.sha256(
                    "\0".join(identity.get("cmdline") or []).encode("utf-8")).hexdigest()
                if identity.get("cmdline") else None,
                "observation": identity.get("observation"),
            },
        }
    body = {"schema": ATTESTATION_SCHEMA, "run_label": run_label, "owners": owners}
    if runtime is not None:
        body["runtime"] = dict(runtime)
    body["attestation_sha256"] = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    return body


def load_serving_attestation(path: str | Path | None) -> dict[str, Any] | None:
    """Read and digest-check an attestation; None when no path is given."""
    if not path:
        return None
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    body = {k: v for k, v in document.items() if k != "attestation_sha256"}
    if document.get("schema") != ATTESTATION_SCHEMA:
        raise ValueError(f"{path}: not a {ATTESTATION_SCHEMA} document")
    if hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest() != document.get("attestation_sha256"):
        raise ValueError(f"{path}: attestation digest does not verify")
    return document


def workers_from_attestation(attestation: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [{"owner": owner, "base_url": entry.get("base_url"), "gpu_uuid": entry.get("gpu_uuid"),
             "cuda_visible_devices": entry.get("cuda_visible_devices"),
             "cuda_device_order": entry.get("cuda_device_order"),
             "logical_cuda_index": entry.get("logical_cuda_index")}
            for owner, entry in sorted((attestation.get("owners") or {}).items())]


def validate_mapping(mapping: Mapping[str, Any] | None, *, run_id: str | None = None,
                     require_serving_process: bool = True,
                     expected_owners: Sequence[str] | None = None,
                     required_runtime: Sequence[str] = ()) -> list[str]:
    """Problems with a run device mapping on its own (empty = verified).

    Recomputes the canonical digest (a mapping edited after it was frozen
    fails even if its declared digest is left alone); requires the run id,
    a physical GPU UUID per worker (``GPU-...``; sentinels fail), distinct
    GPUs and endpoints, a visible-device binding that names the physical card
    (``CUDA_VISIBLE_DEVICES`` equal to the UUID, or a PCI_BUS_ID-ordered
    logical index), and -- for qualification -- the owned serving process's
    identity (pid, start_ticks, boot_id, cmdline).
    """
    if not isinstance(mapping, Mapping) or mapping.get("mapping_present") is False:
        return ["no run device mapping"]
    problems: list[str] = []
    if mapping.get("schema") != MAPPING_SCHEMA:
        problems.append("mapping schema is not run_device_mapping/v1")
    if mapping_digest(mapping) != mapping.get("mapping_sha256"):
        problems.append("mapping digest does not recompute (edited after freezing)")
    if run_id is not None and str(mapping.get("run_id")) != str(run_id):
        problems.append(f"mapping belongs to run {mapping.get('run_id')!r}, not {run_id!r}")
    workers = list(mapping.get("workers") or [])
    if not workers:
        problems.append("mapping has no workers")
    owners = [str(w.get("owner")) for w in workers]
    if expected_owners is not None and sorted(owners) != sorted(str(o) for o in expected_owners):
        problems.append(f"mapping owners {sorted(owners)} != expected {sorted(expected_owners)}")
    uuids = [w.get("gpu_uuid") for w in workers]
    urls = [w.get("base_url") for w in workers]
    if len(set(uuids)) != len(uuids):
        problems.append("two workers are mapped to the same physical GPU")
    if len(set(urls)) != len(urls):
        problems.append("two workers are mapped to the same endpoint")
    for worker in workers:
        owner = worker.get("owner")
        if not is_physical_gpu_uuid(worker.get("gpu_uuid")):
            problems.append(f"{owner}: gpu_uuid {worker.get('gpu_uuid')!r} is not a physical GPU UUID")
        if not worker.get("base_url"):
            problems.append(f"{owner}: no endpoint base_url")
        visible = worker.get("cuda_visible_devices")
        if visible:
            if is_physical_gpu_uuid(visible) and visible != worker.get("gpu_uuid"):
                problems.append(f"{owner}: CUDA_VISIBLE_DEVICES {visible} is not the mapped GPU")
            elif not is_physical_gpu_uuid(visible) and worker.get("cuda_device_order") != "PCI_BUS_ID":
                problems.append(f"{owner}: a logical CUDA_VISIBLE_DEVICES needs PCI_BUS_ID ordering")
        elif not (worker.get("cuda_device_order") == "PCI_BUS_ID"
                  and isinstance(worker.get("logical_cuda_index"), int)):
            problems.append(f"{owner}: no visible-device binding for the physical GPU")
        if require_serving_process:
            process = worker.get("serving_process") or {}
            missing = [f for f in REQUIRED_PROCESS_FIELDS if process.get(f) in (None, "", [])]
            if missing:
                problems.append(f"{owner}: serving-process identity missing {missing}")
            elif not isinstance(process.get("pid"), int) or process["pid"] <= 0:
                problems.append(f"{owner}: serving-process pid is not a process id")
    runtime = mapping.get("runtime") or {}
    for key in required_runtime:
        if not runtime.get(key):
            problems.append(f"runtime.{key} is not bound")
    return problems


def read_proc_identity(pid: int, *, proc_root: str | Path = "/proc") -> dict[str, Any] | None:
    """pid, start_ticks, boot_id, exe, cmdline of a LIVE process (None if gone/zombie).

    The same fields ``round8_run_supervisor.process_identity`` records when the
    launcher adopts a server, so the two compare field by field.
    """
    import os

    root = Path(proc_root) / str(pid)
    try:
        stat_line = (root / "stat").read_text(encoding="utf-8")
        cmdline = (root / "cmdline").read_bytes().decode("utf-8", "replace")
    except OSError:
        return None
    tail = stat_line.rsplit(")", 1)[-1].split()
    try:
        state, start_ticks = tail[0], int(tail[19])
    except (IndexError, ValueError):
        return None
    if state in ("Z", "X", "x"):
        return None
    try:
        exe = os.readlink(root / "exe")
    except OSError:
        exe = ""
    try:
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        boot_id = ""
    return {"pid": int(pid), "start_ticks": start_ticks, "boot_id": boot_id, "exe": exe,
            "cmdline": [c for c in cmdline.split("\0") if c]}


def observed_gpu_uuids() -> list[str] | None:
    """Physical GPU UUIDs the driver enumerates now; None when it cannot be asked."""
    import subprocess

    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def check_mapping_against_host(mapping: Mapping[str, Any], *,
                               observed_gpu_uuids: Sequence[str],
                               process_identity: Any) -> list[str]:
    """Independent HOST check at freeze time (live processes, physical cards).

    ``observed_gpu_uuids``: what the driver enumerates on this host now.
    ``process_identity``: a callable pid -> /proc identity (the supervisor's
    ``process_identity``). A mapped card the host does not have, or a serving
    process that is gone or is a different process (start_ticks / boot_id /
    cmdline differ), is a problem. Run on the bound host; synthetic in tests.
    """
    problems: list[str] = []
    present = set(observed_gpu_uuids)
    for worker in mapping.get("workers") or []:
        owner = worker.get("owner")
        if worker.get("gpu_uuid") not in present:
            problems.append(f"{owner}: GPU {worker.get('gpu_uuid')} is not on this host")
        process = worker.get("serving_process") or {}
        pid = process.get("pid")
        if not isinstance(pid, int):
            problems.append(f"{owner}: no serving process to observe")
            continue
        live = process_identity(pid)
        if not live:
            problems.append(f"{owner}: serving process {pid} is not running")
            continue
        for field in ("start_ticks", "boot_id", "cmdline"):
            if live.get(field) != process.get(field):
                problems.append(f"{owner}: serving process {pid} {field} differs (not the attested process)")
    return problems


def validate_branch_device_reference(reference: Mapping[str, Any] | None,
                                     mapping: Mapping[str, Any] | None) -> list[str]:
    """Problems with one branch's device reference (empty = verified)."""
    problems: list[str] = []
    if not reference:
        return ["branch carries no device reference"]
    if not isinstance(mapping, Mapping) or mapping.get("mapping_present") is False:
        return ["no run device mapping to resolve the reference against"]
    if reference.get("mapping_sha256") != mapping.get("mapping_sha256") \
            or reference.get("mapping_sha256") != mapping_digest(mapping):
        problems.append("branch references a mapping digest that is not the run's recomputed digest "
                        f"({reference.get('mapping_sha256')})")
        return problems
    entry = next((w for w in mapping.get("workers") or [] if w.get("owner") == reference.get("owner")), None)
    if entry is None:
        problems.append(f"owner {reference.get('owner')!r} is not in the run device mapping")
        return problems
    if reference.get("mapped_gpu_uuid") != entry.get("gpu_uuid"):
        problems.append("branch's mapped GPU UUID disagrees with the mapping")
    if reference.get("mapped_base_url") != entry.get("base_url"):
        problems.append("branch's mapped endpoint disagrees with the mapping")
    observed = reference.get("observed_gpu_uuid")
    if observed and observed != entry.get("gpu_uuid"):
        problems.append(f"branch observed GPU {observed} but the mapping binds {entry.get('gpu_uuid')}")
    observed_url = reference.get("observed_base_url")
    if observed_url and observed_url != entry.get("base_url"):
        problems.append(f"branch observed base_url {observed_url} but the mapping binds {entry.get('base_url')}")
    return problems


def validate_device_attribution(mapping: Mapping[str, Any] | None,
                                references: Mapping[str, Mapping[str, Any] | None], *,
                                run_id: str | None = None,
                                require_serving_process: bool = True,
                                expected_owners: Sequence[str] | None = None,
                                required_runtime: Sequence[str] = ()) -> dict[str, Any]:
    """Mapping validity plus every REQUIRED branch reference (keyed by branch)."""
    mapping_problems = validate_mapping(mapping, run_id=run_id,
                                        require_serving_process=require_serving_process,
                                        expected_owners=expected_owners,
                                        required_runtime=required_runtime)
    problems: dict[str, list[str]] = {}
    if mapping_problems:
        problems["run"] = mapping_problems
    for key, reference in sorted(references.items()):
        found = validate_branch_device_reference(reference, mapping)
        if found:
            problems[key] = found
    present = isinstance(mapping, Mapping) and mapping.get("mapping_present") is not False
    return {"verified": present and not problems and bool(references),
            "mapping_present": present,
            "mapping_sha256": mapping.get("mapping_sha256") if present else None,
            "mapping_sha256_recomputed": mapping_digest(mapping) if present else None,
            "branches_checked": len(references), "problems": problems}


def validate_run_device_attribution(events: Sequence[Mapping[str, Any]], *,
                                    require_serving_process: bool = True,
                                    expected_owners: Sequence[str] | None = None,
                                    required_runtime: Sequence[str] = ()) -> dict[str, Any]:
    """E0: the ledger's run mapping and every exposed branch_terminal's reference."""
    mappings = [e.get("payload") for e in events if e.get("kind") == "run_device_mapping"]
    if len(mappings) > 1 and len({m.get("mapping_sha256") for m in mappings if isinstance(m, Mapping)}) > 1:
        return {"verified": False, "mapping_present": True,
                "problems": {"run": ["more than one distinct run device mapping recorded"]},
                "branches_checked": 0}
    mapping = mappings[0] if mappings else None
    run_id = next(((e.get("identity") or {}).get("run") for e in events if e.get("kind") == "run_opened"), None)
    references: dict[str, Mapping[str, Any] | None] = {}
    for event in events:
        if event.get("kind") != "branch_terminal":
            continue
        payload = event.get("payload") or {}
        if payload.get("exposed") is False:
            continue          # never launched: nothing answered it
        ident = event.get("identity") or {}
        references[f"{ident.get('root_id')}/{ident.get('regime_id')}"] = payload.get("device")
    return validate_device_attribution(mapping, references, run_id=run_id,
                                       require_serving_process=require_serving_process,
                                       expected_owners=expected_owners,
                                       required_runtime=required_runtime)
