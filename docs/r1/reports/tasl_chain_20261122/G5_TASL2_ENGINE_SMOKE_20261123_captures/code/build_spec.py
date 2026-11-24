#!/usr/bin/env python3
"""Build the ENGINEERING-ONLY synthetic G.5 smoke spec + a matching fake server_record.

Starts from the committed ``sweep2/t1_tasl/g5_tasl_spec.json`` at paper main
76a3c71f and changes only what makes the job runnable with a fake engine on
TASL-2 without an authorization: runs_root/base under the smoke dir, the two
family checkouts point at clean fake-harness git repos carrying the fake
``audit_g5`` engine, and the node list is replaced by synthetic smoke nodes
(all on cpus 16-31, per the delegation for non-GPU work; all runtimes small).

No committed file is modified.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

S_ROOT = Path(os.environ.get("SMOKE_ROOT", "/home/dowling/r1_engineering/tasl2_g5_smoke_20261123"))
PAPER = Path(os.environ.get("SMOKE_PAPER", "/home/dowling/r1_tracks/t1_tasl/paper_g5smoke"))
OUT = S_ROOT / "spec"
GPU_UUID = "GPU-4d623e76-7587-ee15-a633-46f60d220d94"

sys.path.insert(0, str(PAPER / "sweep2" / "t1_tasl"))
import g4_tasl as T4        # noqa: E402

# (name, family, device, run_seconds, slowest_census_seconds, purpose)
NODES = [
    ("smoke_ok", "G5-7", "gpu", 1.0, 65.0, "normal campaign + normal audit"),
    ("smoke_oom", "G5-7", "gpu", 1.0, 65.0, "edit-caused OOM"),
    ("smoke_crash", "G5-7", "gpu", 1.0, 65.0, "edit-caused raise/crash"),
    ("smoke_infra", "G5-7", "gpu", 1.0, 65.0, "infrastructure row -> STOP 7"),
    ("smoke_gate", "G5-7", "gpu", 1.0, 65.0, "gate refusal -> STOP 2 node"),
    ("smoke_deadline", "G5-7", "gpu", 0.1, 65.0, "job deadline kill (TimeoutExpired)"),
    ("smoke_kill", "G5-AR", "gpu", 1.0, 65.0, "deliberate engine kill"),
    ("smoke_cpu", "G5-7", "cpu", 1.0, 65.0, "CPU-only node, no --gpu-uuid"),
    ("smoke_stopdl", "G5-7", "gpu", 1.0, 65.0, "campaign engine deadline stop -> STOP 9 node"),
    ("smoke_stopdl_a", "G5-7", "gpu", 1.0, 65.0, "audit engine deadline stop -> STOP 9 node"),
    ("smoke_orphan", "G5-7", "gpu", 1.0, 65.0, "start-of-job orphan refusal then clean run"),
    ("smoke_timing", "G5-7", "gpu", 1.0, 5.0, "median run time over the synthetic basis -> timing STOP"),
]


def fake_harness_commit(repo: Path) -> str:
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    base = json.loads((PAPER / "sweep2" / "t1_tasl" / "g5_tasl_spec.json").read_text())
    spec = json.loads(json.dumps(base))
    spec["run_id"] = "g5smoke-engineering-20261123"
    spec["comment"] = "ENGINEERING-ONLY synthetic smoke spec; not evidence; not the committed spec"
    spec["label"] = "ENGINEERING_ONLY"
    spec["worker"].update({
        "hostname": "TASL-2", "gpu_uuid": GPU_UUID, "cpus": "16-31",
        "base": str(S_ROOT / "work" / "base"),
        "runs_root": str(S_ROOT / "runs"),
        "sealed_root": str(S_ROOT / "work" / "sealed_never_written"),
        "lease": "~/r1_locks/gpu0.lock",
        "extra_env": {},
    })
    g7 = S_ROOT / "fake_harness_g7"
    ga = S_ROOT / "fake_harness_ar"
    spec["harness_families"]["G5-7"].update(harness_dir=str(g7), g5_commit=fake_harness_commit(g7))
    spec["harness_families"]["G5-AR"].update(harness_dir=str(ga), g5_commit=fake_harness_commit(ga))
    spec["nodes"] = [{
        "node": name, "family": fam, "device": dev, "env": "torch312", "cpus": "16-31",
        "run_seconds": run_s, "slowest_census_seconds": slow,
        "spec_path": f"smoke/{name}.yaml", "node_dir": f"smoke/{name}",
        "node_spec_sha256": hashlib.sha256(name.encode()).hexdigest(),
        "committed_pin_sha256": hashlib.sha256((name + "pin").encode()).hexdigest(),
        "data_manifest_sha256": hashlib.sha256((name + "data").encode()).hexdigest(),
        "purpose": purpose,
    } for name, fam, dev, run_s, slow, purpose in NODES]
    spec["envs"]["torch312"]["freeze"] = base["envs"]["torch312"]["freeze"]
    spec["key_values"]["cap_gpu_hours"] = 425
    spec["proposer"]["server_url"] = "http://tasl-7.tail119748.ts.net:18095"   # fake get; no server touched
    spec["proposer"]["run_dir"] = str(S_ROOT / "work" / "proposer_never_written")
    OUT.mkdir(parents=True, exist_ok=True)
    spec_path = OUT / "smoke_spec.json"
    spec_path.write_text(json.dumps(spec, indent=1) + "\n")
    sha = hashlib.sha256(spec_path.read_bytes()).hexdigest()

    prop = spec["proposer"]
    from urllib.parse import urlparse
    port = urlparse(prop["server_url"]).port
    record = {
        "schema": T4.SERVER_RECORD_SCHEMA, "run_id": spec["run_id"], "host": "TASL-7",
        "hostname": prop["hostname"], "server_url": prop["server_url"], "spec_sha256": sha,
        "binary_sha256": prop["binary_sha256"], "bin_dir_manifest_sha256": prop["bin_dir_manifest_sha256"],
        "model_sha256": T4.MODEL["sha256"], "build": f"version: {prop['expected_build']}",
        "argv": T4.server_argv(spec, port),
        "gpu": {"uuid": prop["gpu_uuid"], "name": T4.GPU_MODEL},
        "pid": 0, "started_utc": "2026-11-23T00:00:00Z",
        "smoke_note": "SYNTHETIC server record for the ENGINEERING smoke; no server was started",
    }
    (OUT / "server_record.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({"spec": str(spec_path), "spec_sha256": sha,
                      "server_record": str(OUT / "server_record.json"),
                      "nodes": [n["node"] for n in spec["nodes"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
