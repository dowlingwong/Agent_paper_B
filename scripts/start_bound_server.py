#!/usr/bin/env python3
"""Serve the ONE bound E0 worker, attest it, run one command under it, stop it (R1/R6).

For stage 3 (bounded smoke and the production E0 rehearsal on the bound
deployment). The server is started with the frozen single-GPU serving command
(``run_local_soak.server_argv``), pinned to the bound physical card by
``CUDA_VISIBLE_DEVICES=<gpu_uuid>`` exactly as ``e0_launch`` pins E0 servers,
on the port of the bound endpoint file. Once healthy, its settled ``/proc``
identity is written to a serving attestation and the wrapped command runs
with ``E0_SERVING_ATTESTATION`` and ``LLAMA_SERVER_BIN`` exported, so the smoke
and the executor can bind device attribution to the process this script owns.
The server is stopped with the command (and on SIGTERM/SIGINT).

    python3 scripts/start_bound_server.py --bindings protocols/e0_selected_model_bindings.json \\
        --model /path/Qwen3-8B-Q4_K_M.gguf --log-dir <dir> -- <command ...>

Refuses (no server started) if the binary digest, GGUF digest, endpoint file
digest or physical GPU binding disagree with the record. ``--plan`` prints the
server command and the exported environment without starting anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from causal_branch.device_mapping import (  # noqa: E402
    ATTESTATION_ENV,
    is_physical_gpu_uuid,
    read_proc_identity,
    serving_attestation,
)


def _sha(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def plan(bindings_path: Path, model: Path, *, server_binary: Path, hash_model: bool = True) -> dict:
    import run_local_soak as rls  # noqa: PLC0415

    record = json.loads(Path(bindings_path).read_text(encoding="utf-8"))
    b = record.get("bindings") or {}
    problems: list[str] = []
    endpoints = b.get("worker_endpoints") or []
    if len(endpoints) != 1 or int(b.get("workers") or 0) != 1:
        problems.append(f"the record must bind exactly one worker endpoint (workers={b.get('workers')}, "
                        f"worker_endpoints={len(endpoints)})")
    entry = endpoints[0] if endpoints else {}
    uuid = entry.get("gpu_uuid")
    if not is_physical_gpu_uuid(uuid):
        problems.append(f"the bound gpu_uuid {uuid!r} is not a physical GPU UUID (stage 2 binds it)")
    endpoint_path = REPO_ROOT / str(entry.get("endpoint_config") or b.get("endpoint_config") or "_")
    if _sha(endpoint_path) != (entry.get("endpoint_config_sha256") or b.get("endpoint_config_sha256")):
        problems.append("the endpoint file does not hash to the bound digest")
    base_url = str(entry.get("base_url") or "")
    port = urlsplit(base_url).port if base_url else None
    if port is None:
        problems.append("the bound endpoint has no port")
    if _sha(server_binary) != b.get("llama_server_sha256"):
        problems.append(f"{server_binary} does not hash to the bound llama_server_sha256")
    if not model.is_file() or model.name != b.get("gguf_filename"):
        problems.append(f"{model} is not the bound GGUF file {b.get('gguf_filename')}")
    elif hash_model and _sha(model) != b.get("gguf_sha256"):
        problems.append(f"{model} does not hash to the bound gguf_sha256")
    model = Path(os.path.abspath(model))
    context = int(b.get("context_ceiling_tokens") or rls.CONTEXT)
    argv = rls.server_argv(model=model, port=port or 0, device=0, alias=str(b.get("selected_model")),
                           context=context)
    argv[0] = str(server_binary)
    runtime = rls.launcher_runtime(server_binary=server_binary, server_sha256=b.get("llama_server_sha256"),
                                   model=model, model_sha256=b.get("gguf_sha256"), context=context)
    return {"problems": problems, "argv": argv, "port": port, "base_url": base_url, "gpu_uuid": uuid,
            "owner": entry.get("owner"), "env": {"CUDA_VISIBLE_DEVICES": str(uuid)}, "runtime": runtime}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bindings", type=Path, required=True)
    ap.add_argument("--model", type=Path, required=True, help="the bound GGUF file on this host")
    ap.add_argument("--llama-server-bin", type=Path,
                    default=Path(os.environ.get("LLAMA_SERVER_BIN", "/nonexistent/llama-server")))
    ap.add_argument("--log-dir", type=Path, required=True)
    ap.add_argument("--plan", action="store_true", help="print the plan; start nothing")
    ap.add_argument("--state-json", type=Path, default=None,
                    help="S6: once the server is healthy and attested, write its recorded state "
                         "(argv, cache flags, attestation digest, pid) here BEFORE the command runs, "
                         "e.g. for determinism_rehearsal.py --server-state-json")
    ap.add_argument("command", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    p = plan(args.bindings, args.model, server_binary=args.llama_server_bin, hash_model=not args.plan)
    if args.plan or p["problems"]:
        print(json.dumps({**p, "command": command}, indent=2, sort_keys=True))
        if p["problems"]:
            print("REFUSED: the bound deployment cannot be served as recorded; nothing started", file=sys.stderr)
            return 2
        return 0
    if not command:
        print("no command to run under the server", file=sys.stderr)
        return 2
    import subprocess

    import run_local_soak as rls  # noqa: PLC0415
    from causal_branch.process_fleet import ProcessFleet, run_with_fleet  # noqa: PLC0415

    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    args.log_dir.mkdir(parents=True, exist_ok=True)
    with ProcessFleet(record_path=args.log_dir / f"interruption-{token}.json") as fleet:
        env = dict(rls.server_env(), CUDA_VISIBLE_DEVICES=p["env"]["CUDA_VISIBLE_DEVICES"])
        env.pop("CUDA_DEVICE_ORDER", None)
        server = subprocess.Popen(p["argv"], stdout=(args.log_dir / "server.log").open("w"),
                                  stderr=subprocess.STDOUT, start_new_session=True, env=env)
        fleet.adopt(f"llama-server-{p['owner']}", server, port=p["port"])
        if not rls.wait_healthy(p["port"], server):
            print("server never became healthy", file=sys.stderr)
            return 3
        identity = read_proc_identity(server.pid)
        attestation = serving_attestation(run_label=token, servers=[{
            "owner": p["owner"], "base_url": p["base_url"], "gpu_uuid": p["gpu_uuid"],
            "cuda_visible_devices": p["env"]["CUDA_VISIBLE_DEVICES"], "identity": identity}],
            runtime=p["runtime"])
        path = args.log_dir / f"serving_attestation-{token}.json"
        path.write_text(json.dumps(attestation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.state_json is not None:
            argv_ = p["argv"]
            flags = {k: (argv_[argv_.index(k) + 1] if k in argv_ and argv_.index(k) + 1 < len(argv_) else None)
                     for k in ("--cache-ram", "--cache-reuse", "--parallel", "-c", "--split-mode")}
            flags["--no-cache-idle-slots"] = "--no-cache-idle-slots" in argv_
            state = {"schema": "bound_server_state/v1", "recorded_by": "scripts/start_bound_server.py",
                     "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "base_url": p["base_url"],
                     "gpu_uuid": p["gpu_uuid"], "pid": server.pid, "health": "ok", "argv": argv_,
                     "cache_and_slot_flags": flags, "attestation": str(path),
                     "attestation_sha256": attestation.get("attestation_sha256"), "runtime": p["runtime"],
                     "note": "recorded from the launcher's own argv and attestation; no model request made"}
            args.state_json.parent.mkdir(parents=True, exist_ok=True)
            args.state_json.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.environ[ATTESTATION_ENV] = str(path)
        os.environ["LLAMA_SERVER_BIN"] = str(args.llama_server_bin)
        print(f"serving {p['base_url']} on {p['gpu_uuid']} (pid {server.pid}); attestation {path}", flush=True)
        return run_with_fleet(fleet, command, cwd=REPO_ROOT)


if __name__ == "__main__":
    sys.exit(main())
