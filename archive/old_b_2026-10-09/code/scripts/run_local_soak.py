#!/usr/bin/env python3
"""Start one frozen llama.cpp server per worker, run the soak, stop them.

The server count is data driven: it follows `--workers`, which follows the
worker count frozen in the operative candidate registry. Round 4 runs two
workers on two L40s; the four-server Titan-X topology is historical and its
results are reported separately, never pooled with a two-worker measurement.

One single-slot server per GPU, matching the frozen serving configuration
exactly (`-c <registry context_tokens> -ctk q8_0 -ctv q8_0 -ngl 999
--parallel 1`, CUDA backend). The context ceiling is the module's `CONTEXT`
constant, currently 40960 after the 2026-08-19 amendment; the earlier 32768
figure in this docstring described the pre-amendment configuration and no longer
matched the code.

Workers are routed one-to-one onto the servers, so the throughput qualification
measures concurrency rather than N workers queueing behind a single slot.

Non-qualifying: the soak exercises harness invariants only. No scientific pool is
opened and no intervention arm is run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiment_scaffold/src"))

from causal_branch.device_mapping import (  # noqa: E402
    read_proc_identity,
    serving_attestation,
)
from causal_branch.process_fleet import ProcessFleet, run_with_fleet  # noqa: E402
# Selectable so an sm_89 build can be used without overwriting the sm_52 build
# that earlier evidence still refers to. See scripts/local_kernel_probe.py.
LLAMA_SERVER = Path(os.environ.get(
    "LLAMA_SERVER_BIN", "/path/to/llama.cpp/build/bin/llama-server"))
CONTEXT = 40960
KV_TYPE = "q8_0"
NGL = 999


def bound_server_problem(observed_sha256: str, bindings: Path) -> str | None:
    """Why the served binary is not the bound one, or None when it is."""
    try:
        import json as _json
        record = _json.loads(Path(bindings).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"the binding record {bindings} is unreadable: {exc}"
    expected = (record.get("bindings") or {}).get("llama_server_sha256")
    if not expected:
        return f"the binding record {bindings} names no llama_server_sha256"
    if expected != observed_sha256:
        return (f"the llama-server at {LLAMA_SERVER} has sha256 {observed_sha256}, not the "
                f"bound {expected} (set LLAMA_SERVER_BIN to the registered build-sm52 "
                "binary; the module default build/bin is not it)")
    return None


def server_argv(*, model: Path, port: int, device: int, alias: str,
                context: int = CONTEXT) -> list[str]:
    """The frozen single-GPU serving command.

    `--alias` matters for identity, not cosmetics. Without it llama.cpp reports
    the full GGUF path as the response model, the soak's substrate-identity
    check compares that against the bound model id, and every branch is
    correctly rejected as a mismatch. Setting the alias makes the server
    declare the identity the run binds, rather than loosening the check to
    accept whatever the server happens to say.

    `context` is the frozen context ceiling. It is a parameter, not the
    `CONTEXT` module constant, so a prospectively re-frozen contract (for
    example the 65,536 of `qwen3_8b_context_contract_successor_candidate.json`)
    runs without editing this file and without the server and the soak profile
    silently disagreeing.

    The cache flags are not optional: the transition plan freezes the serving
    configuration with cache reuse off, and the capability audit and WP1-D
    probe run with it off. `--cache-ram` defaults to 8192 MiB and
    `--cache-idle-slots` defaults to enabled, so omitting them would measure a
    configuration E0 will not execute and could make the soak's own
    `zero_prompt_cache_reuse` criterion describe a cache that was live.
    """
    return [str(LLAMA_SERVER), "--model", str(model), "--alias", alias,
            "-c", str(context),
            "-ctk", KV_TYPE, "-ctv", KV_TYPE, "-ngl", str(NGL), "--parallel", "1",
            "--host", "127.0.0.1", "--port", str(port), "--device", f"CUDA{device}",
            "--split-mode", "none",
            "--cache-ram", "0", "--cache-reuse", "0", "--no-cache-idle-slots",
            "--no-webui"]


def start_server(model: Path, *, port: int, device: int, log: Path,
                 alias: str, context: int = CONTEXT) -> subprocess.Popen:
    argv = server_argv(model=model, port=port, device=device, alias=alias,
                       context=context)
    log.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(argv, stdout=log.open("w", encoding="utf-8"),
                            stderr=subprocess.STDOUT, start_new_session=True,
                            env=server_env())


#: R6: `--device CUDA<i>` is a LOGICAL index. With PCI_BUS_ID ordering the CUDA
#: runtime enumerates exactly as `nvidia-smi --query-gpu=index` does, so the
#: attestation can name the physical card behind each index. Without it CUDA's
#: default FASTEST_FIRST order may differ from nvidia-smi's and the mapping
#: would name the wrong card.
CUDA_DEVICE_ORDER = "PCI_BUS_ID"


def server_env(environ: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if environ is None else environ)
    env["CUDA_DEVICE_ORDER"] = CUDA_DEVICE_ORDER
    env.pop("CUDA_VISIBLE_DEVICES", None)      # the index is the only selector
    return env


def physical_uuid_by_index(query=None) -> dict[int, str] | None:
    """nvidia-smi index -> physical UUID (PCI bus order), None when unavailable."""
    try:
        out = (query or (lambda: subprocess.run(
            ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=20, check=True).stdout))()
    except (OSError, subprocess.SubprocessError):
        return None
    table: dict[int, str] = {}
    for line in out.splitlines():
        if "," not in line:
            continue
        index, uuid = (part.strip() for part in line.split(",", 1))
        if index.isdigit():
            table[int(index)] = uuid
    return table


def launcher_runtime(*, server_binary: Path, server_sha256: str, model: Path, model_sha256: str | None,
                     context: int) -> dict:
    """S1: what THIS launcher hashed and executed (lands in the digested attestation)."""
    return {"llama_server_path": os.path.realpath(server_binary), "llama_server_sha256": server_sha256,
            "gguf_path": os.path.normpath(str(model)), "gguf_filename": Path(model).name,
            "gguf_sha256": model_sha256, "context": int(context)}


def build_attestation(*, run_label: str, ports: list[int], processes: list,
                      uuid_by_index: dict[int, str], identity=read_proc_identity,
                      runtime: dict | None = None) -> tuple[dict, list[str]]:
    """The attestation for the servers THIS runner started, and any problems."""
    problems: list[str] = []
    servers = []
    for index, (port, process) in enumerate(zip(ports, processes)):
        ident = identity(process.pid)
        if not ident:
            problems.append(f"server {index} (pid {process.pid}) is not running")
        uuid = uuid_by_index.get(index)
        if not uuid:
            problems.append(f"no physical GPU at index {index}")
        servers.append({"owner": f"llama-server-{index}", "base_url": f"http://127.0.0.1:{port}/v1",
                        "gpu_uuid": uuid, "cuda_device_order": CUDA_DEVICE_ORDER,
                        "logical_cuda_index": index, "identity": ident})
    return serving_attestation(run_label=run_label, servers=servers, runtime=runtime), problems


def wait_healthy(port: int, process: subprocess.Popen, timeout: float = 420.0) -> bool:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
                if json.loads(response.read().decode()).get("status") == "ok":
                    return True
        except Exception:  # noqa: BLE001 -- server not up yet
            time.sleep(2.0)
    return False


def binary_sha256(path: Path) -> str | None:
    """The digest of the server that will serve the soak, or None if absent.

    The soak artifact has to name the runtime it measured. `LLAMA_SERVER_BIN`
    selects between builds (the registered sm_52 build and the conventional
    `build/bin` beside it) and the workload runner only talks HTTP, so the
    launcher is the only process that knows which binary is behind the ports.
    It therefore computes the digest here and passes it to `realistic_soak.py`,
    where it lands in the artifact's evidence identity.
    """
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def workload_argv(*, python: str, repo_root: Path, model_id: str, ports: list[int],
                  roots: int, templates: int, plan_concurrency: int,
                  branch_deadline: float, llama_server_sha256: str,
                  context: int = CONTEXT, extra: list[str],
                  context_buckets: list[str] | None = None,
                  settling_contract: str | None = None,
                  serving_attestation_path: Path | None = None) -> list[str]:
    """The `realistic_soak.py` command line, including the runtime binding.

    Kept separate from `main` so a test can assert the digest reaches the
    workload without starting four GPU servers. `--local-context` carries the
    same frozen ceiling the servers were started with, so the soak profile and
    the served context cannot disagree.
    """
    # The soak contract is frozen per successor, so it travels as explicit
    # arguments rather than through --extra: omitted, the workload keeps the
    # historical three-bucket strict contract.
    contract: list[str] = []
    if context_buckets:
        contract += ["--context-buckets", *context_buckets]
    if settling_contract:
        contract += ["--settling-contract", settling_contract]
    if serving_attestation_path is not None:
        contract += ["--serving-attestation", str(serving_attestation_path)]
    return [python, str(repo_root / "scripts/realistic_soak.py"),
            "--substrate", "local", "--local-model-id", model_id,
            "--local-port", str(ports[0]),
            "--local-worker-ports", *[str(p) for p in ports],
            "--local-context", str(context),
            "--roots", str(roots), "--templates", str(templates),
            # --concurrency keeps the REGISTERED wave plan (4 waves of 64).
            # --max-in-flight is what the substrate can actually run at once.
            # Passing the server count as --concurrency would reshape the plan
            # into 64 waves of 4, which is a different experiment.
            "--concurrency", str(plan_concurrency),
            "--max-in-flight", str(len(ports)),
            "--branch-deadline", str(branch_deadline),
            "--llama-server-sha256", llama_server_sha256, *contract, *extra]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # No defaults. These named Qwen3-4B, a Round 2 control that is not in the
    # Round 4 candidate set at all. The runbook's soak command supplies only
    # `--workers`, so the soak would have exercised the obsolete model while the
    # surrounding report described it as qualifying the selected candidate.
    parser.add_argument("--model", type=Path, required=True,
                        help="GGUF path of the SELECTED candidate")
    parser.add_argument("--model-id", required=True,
                        help="candidate id of the SELECTED candidate; it is the "
                             "server alias, so it also labels the evidence")
    # No default. The worker count is a frozen registry field, and a default of
    # four silently produced a four-server topology on a two-GPU machine.
    parser.add_argument("--workers", type=int, required=True,
                        help="worker count frozen in the operative candidate "
                             "registry; Round 4 is 2")
    parser.add_argument("--base-port", type=int, default=8081)
    parser.add_argument("--roots", type=int, default=256)
    parser.add_argument("--templates", type=int, default=32)
    parser.add_argument("--plan-concurrency", type=int, default=64,
                        help="registered design concurrency, which sets wave sizes")
    parser.add_argument("--branch-deadline", type=float, default=360.0,
                        help="explicit per-turn wall rail; successor protocols must "
                             "supply their frozen value rather than relying on --extra")
    parser.add_argument("--context", type=int, default=CONTEXT,
                        help="frozen context ceiling, served by every worker and "
                             "carried into the soak profile; a prospectively "
                             "re-frozen contract passes its own value (e.g. 65536) "
                             "rather than editing the module constant")
    parser.add_argument("--context-buckets", nargs="+", default=None,
                        choices=("8k", "16k", "32k"),
                        help="registered bucket set; the 2026-09-19 Option B "
                             "successor passes `8k 16k`")
    parser.add_argument("--settling-contract", default=None,
                        choices=("strict", "e0_allowance"),
                        help="settling contract; the 2026-09-19 successor passes "
                             "`e0_allowance`")
    parser.add_argument("--log-dir", type=Path,
                        default=REPO_ROOT / "evidence/spikes/local-soak-servers")
    parser.add_argument("--bindings", type=Path,
                        default=REPO_ROOT / "protocols/e0_selected_model_bindings.json",
                        help="the selected-model binding record whose "
                             "`llama_server_sha256` the served binary must match")
    parser.add_argument("--allow-unbound-server", action="store_true",
                        help="DEVELOPMENT ONLY: run a binary whose digest differs from "
                             "the binding record (the artifact then cannot qualify)")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args()

    if not args.model.is_file():
        print(f"model not found: {args.model}", file=sys.stderr)
        return 2
    # S1: serve the absolute path that is hashed and attested, so the
    # attested command line names exactly the file whose digest is recorded.
    args.model = Path(os.path.abspath(args.model))
    # Refuse to start a soak whose runtime cannot be named in its own artifact.
    llama_sha256 = binary_sha256(LLAMA_SERVER)
    if llama_sha256 is None:
        print(f"llama-server not found: {LLAMA_SERVER}", file=sys.stderr)
        return 2
    # F04/F11: the binary the soak serves must be the one the binding record
    # names. The module default (`build/bin`) is the historical sm_52 tree's
    # sibling and is NOT the registered `build-sm52` binary; a qualification
    # collected on the wrong binary qualified nothing. The check is by digest,
    # so it holds whichever path LLAMA_SERVER_BIN names.
    problem = bound_server_problem(llama_sha256, args.bindings)
    if problem and not args.allow_unbound_server:
        print(f"refusing to start: {problem}", file=sys.stderr)
        return 4
    if problem:
        print(f"WARNING (development only, artifact cannot qualify): {problem}", file=sys.stderr)

    ports = [args.base_port + i for i in range(args.workers)]
    run_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record_path = (REPO_ROOT / "evidence/spikes/local-soak-servers"
                   / f"interruption-{run_token}.json")

    # Every launched server is owned by the fleet. On SIGTERM/SIGINT/SIGHUP the
    # fleet signals each child's whole process GROUP and writes an interruption
    # record, so an operator stopping a run never strands servers holding VRAM.
    with ProcessFleet(record_path=record_path) as fleet:
        for index, port in enumerate(ports):
            proc = start_server(args.model, port=port, device=index,
                                log=args.log_dir / f"server-{index}.log",
                                alias=args.model_id, context=args.context)
            fleet.adopt(f"llama-server-{index}", proc, port=port, device=index)
        for index, port in enumerate(ports):
            member = fleet.members[index]
            if not wait_healthy(port, member.process):
                print(f"server on port {port} (CUDA{index}) failed to become healthy",
                      file=sys.stderr)
                return 3
        print(f"{len(ports)} servers healthy on ports {ports}", flush=True)
        # R6: attest the servers this runner owns -- live /proc identity and the
        # physical card behind each index -- before any root runs.
        uuids = physical_uuid_by_index() or {}
        attestation, attestation_problems = build_attestation(
            run_label=run_token, ports=ports,
            processes=[m.process for m in fleet.members], uuid_by_index=uuids,
            runtime=launcher_runtime(server_binary=LLAMA_SERVER, server_sha256=llama_sha256,
                                     model=args.model, model_sha256=binary_sha256(args.model),
                                     context=args.context))
        attestation_path = args.log_dir / f"serving_attestation-{run_token}.json"
        attestation_path.parent.mkdir(parents=True, exist_ok=True)
        attestation_path.write_text(json.dumps(attestation, sort_keys=True, indent=2) + "\n",
                                    encoding="utf-8")
        if attestation_problems and not args.allow_unbound_server:
            print(f"refusing to run: serving attestation incomplete: {attestation_problems}",
                  file=sys.stderr)
            return 5

        argv = workload_argv(
            python=sys.executable, repo_root=REPO_ROOT, model_id=args.model_id,
            ports=ports, roots=args.roots, templates=args.templates,
            plan_concurrency=args.plan_concurrency,
            branch_deadline=args.branch_deadline,
            llama_server_sha256=llama_sha256,
            context=args.context, extra=args.extra,
            context_buckets=args.context_buckets,
            settling_contract=args.settling_contract,
            serving_attestation_path=attestation_path)
        print("running:", " ".join(argv), flush=True)
        # Adopted rather than `subprocess.run`: a signal to this runner must also
        # reach the soak, which would otherwise keep running orphaned.
        return run_with_fleet(fleet, argv, cwd=REPO_ROOT)


if __name__ == "__main__":
    sys.exit(main())
