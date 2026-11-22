#!/usr/bin/env python3
"""G.4 T1 pilot on NEMO2 H200 (HTCondor): spec, job, JDL render, two-key switch, summary and the D14 date recompute.

Authority: R1-TRACKG-G3-EARLY (the pilot on mlab_cifar10, mlgym_fmnist and autoresearch_fixedtokens, or
mlgym_breakout_minatar while autoresearch is not ready), R1-T1-HOST-H200 (NEMO2 H200), R1-MAIN-PROPOSER and
R1-EXAM-X7 (main proposer gemma4_31b, thinking off), R1-BX-PROPOSED-CONFIRM D4 (manager_proposal/v2-diff; a pick
that fails diff liveness on a T1 node is a STOP), R1-BX-D14 (the dates are recomputed after G.4), and
R1-HARNESS-ISOLATION (the unisolated-run gate).  Design: ``sweep2/g4/G4_PILOT_PLAN.md``.  ENGINEERING_ONLY: the
pilot's proposals are not labels.

One job per pilot node.  It reuses the reviewed G.1b steps (``g1b_lib``: image and GPU identity, pinned clones, the
census environment, the node's data with the deployed-pin check, the delegated cgroup) and the reviewed sweep-2
server steps (``s2_c2_lib``: GGUF fetch with a streaming sha256, the owned llama-server with the exam flags, the
build and full-offload checks), then runs ``python -m autoresearch.trackg.pilot_g4 run`` (pinned harness), which
runs the campaign instances with the record gate and ``cache_prompt: false``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
# the staged copies next to this file come first; the repository locations are a fallback for the checkout only
for extra in (HERE.parent / "g1b", HERE.parent):
    if (extra / "g1b_lib.py").is_file() or (extra / "s2_c2_lib.py").is_file():
        if str(extra) not in sys.path:
            sys.path.append(str(extra))
sys.path.insert(0, str(HERE))
import g1b_lib  # noqa: E402
import s2_c2_lib  # noqa: E402

SCHEMA = "g4_h200_pilot/v1"
RECORD_SCHEMA = "g4_h200_job_record/1"
ENGINEERING_ONLY = "ENGINEERING_ONLY"
GPU_MODEL = g1b_lib.GPU_MODEL
IMAGE_DIGEST = g1b_lib.IMAGE_DIGEST
CORE_NODES = ("mlab_cifar10", "mlgym_fmnist")
THIRD_NODE = ("autoresearch_fixedtokens", "mlgym_breakout_minatar")  # autoresearch first; Breakout if not ready
CAP_PILOT_GPU_HOURS = 20.0      # declared pilot cap (proposed; the note confirms it); STOP above
W = 20                          # manager calls per campaign instance (G5-W option A)
TEMPERATURE = 0.2               # D15 (sweep 2: temperature 0.2 with the D26 seed); author item G5-TEMP
MEMORY_MODES = ("history", "none")  # the v2-diff manager: last 12 steps shown, or none; author item G5-MEM
MAX_TOKENS = 4096               # the completion cap (R1-EXAM-B1-TRUNCATION-INVALID)
TRANSFER_OUTPUTS = "out.tar,job_record.json,SHA256SUMS,llama-server.log,g4_run.log"
STAGED = ("g4_job.sh", "g4_lib.py", "g1b_lib.py", "s2_c2_lib.py")
SERVER_EXTRA_ARGS = ["--jinja", "--chat-template-kwargs", s2_c2_lib.EXAM_THINKING_KWARGS, "--cache-type-k", "q8_0",
                     "--cache-type-v", "q8_0", "--no-webui"]
MODEL = {
    "url": ("https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/"
            "619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf"),
    "sha256": "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75",
    "size": 19598489952,
    "alias": "gemma4_31b",
}
Stop = g1b_lib.Stop
NodeStop = g1b_lib.NodeStop     # a STOP about the node itself (zero diff liveness): the infrastructure worked


# =============================================================================================== spec
def walltime(node: dict, pilot: dict, layout: dict) -> int:
    calls = len(pilot["instances"]) * (pilot["budget"] + 1)  # + the baseline run of each instance
    return int(layout["startup_reserve_s"]) + int(math.ceil(
        calls * (float(node["run_seconds"]) + float(layout["llm_seconds_estimate"])) * 1.5))


def projection(spec: dict) -> dict:
    layout, pilot = spec["layout"], spec["pilot"]
    per = {}
    for node in spec["nodes"]:
        calls = len(pilot["instances"]) * (pilot["budget"] + 1)
        gpu_h = (calls * (float(node["run_seconds"]) + float(layout["llm_seconds_estimate"]))
                 + float(layout["startup_estimate_s"])) / 3600.0
        per[node["node"]] = {"campaign_steps": calls, "gpu_hours": round(gpu_h, 3),
                             "requested_walltime_s": walltime(node, pilot, layout)}
    return {"per_node": per, "total_gpu_hours": round(sum(v["gpu_hours"] for v in per.values()), 3),
            "max_walltime_s": max(v["requested_walltime_s"] for v in per.values()),
            "proposals_total": len(spec["nodes"]) * len(pilot["instances"]) * pilot["budget"]}


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    allow = not launch
    if spec.get("schema") != SCHEMA or spec.get("label") != ENGINEERING_ONLY:
        raise Stop(f"STOP: spec must be {SCHEMA}, ENGINEERING_ONLY")
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not g1b_lib.SAFE.fullmatch(run_id):
        raise Stop("STOP: run_id must be a safe path component")
    image = spec.get("image") or {}
    if image.get("digest") != IMAGE_DIGEST:
        raise Stop("STOP: image.digest must be the v2 gpu digest (the T1 table's image, as G.1b)")
    g1b_lib._sha(image.get("versions_sha256"), "image.versions_sha256", allow_placeholder=allow)
    g1b_lib._sha(image.get("llama_server_sha256"), "image.llama_server_sha256", allow_placeholder=allow)
    for key, repo in (("paper", g1b_lib.PAPER_REPO), ("harness", g1b_lib.HARNESS_REPO)):
        if (spec.get(key) or {}).get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
        g1b_lib._commit((spec.get(key) or {}).get("commit"), f"{key}.commit", allow_placeholder=allow)
    if spec.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: gpu_model must be {GPU_MODEL}")
    if spec.get("model") != MODEL:
        raise Stop("STOP: model must be the pinned gemma4_31b GGUF (R1-EXAM-X7 pick)")
    server = spec.get("server") or {}
    if server.get("extra_args") != SERVER_EXTRA_ARGS or server.get("ctx") != s2_c2_lib.CTX \
            or server.get("binary") != "/opt/r1/llama/bin/llama-server":
        raise Stop("STOP: server must use the exam flags (thinking off, q8_0 K/V, ctx 32,768)")
    if not isinstance(server.get("expected_build"), str) or not server["expected_build"]:
        raise Stop("STOP: server.expected_build must name the pinned build")
    pilot = spec.get("pilot") or {}
    if pilot.get("proposal_schema") != "manager_proposal/v2-diff" or pilot.get("cache_prompt") is not False:
        raise Stop("STOP: pilot.proposal_schema must be manager_proposal/v2-diff and cache_prompt false")
    if pilot.get("budget") != W:
        raise Stop(f"STOP: pilot.budget must be W = {W} manager calls per instance")
    if pilot.get("max_tokens") != MAX_TOKENS:
        raise Stop(f"STOP: pilot.max_tokens must be the completion cap {MAX_TOKENS}")
    if pilot.get("temperature") != TEMPERATURE:
        raise Stop(f"STOP: pilot.temperature must be {TEMPERATURE} (D15; G5-TEMP)")
    if pilot.get("memory_mode") not in MEMORY_MODES:
        raise Stop(f"STOP: pilot.memory_mode must be one of {MEMORY_MODES} (G5-MEM)")
    instances = pilot.get("instances")
    if not isinstance(instances, list) or not 1 <= len(instances) <= 5:
        raise Stop("STOP: 1-5 campaign instances per node")
    triples = set()
    for inst in instances:
        if not isinstance(inst, dict) or set(inst) != {"train_seed", "split_seed", "manager_seed"}:
            raise Stop("STOP: a pilot instance has exactly train_seed, split_seed and manager_seed")
        triple = (inst["train_seed"], inst["split_seed"], inst["manager_seed"])
        if triple in triples:
            raise Stop("STOP: pilot instances must have distinct seed triples")
        triples.add(triple)
        for key in ("train_seed", "split_seed", "manager_seed"):
            seed = inst.get(key)
            if type(seed) is not int or not 4001 <= seed <= 4099:
                raise Stop(f"STOP: pilot {key} {seed!r} must be in the pilot block 4001-4099 (disjoint from G.1b "
                           "1001-3030, audits 7001-7010, exams 9001+)")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 3:
        raise Stop("STOP: the pilot has exactly three nodes")
    names = [n.get("node") for n in nodes]
    if names[:2] != list(CORE_NODES) or names[2] not in THIRD_NODE:
        raise Stop(f"STOP: pilot nodes must be {CORE_NODES} + one of {THIRD_NODE} (R1-TRACKG-G3-EARLY)")
    if names[2] == "mlgym_breakout_minatar" and not str(spec.get("third_node_reason", "")).strip():
        raise Stop("STOP: Breakout replaces autoresearch only with third_node_reason (autoresearch not ready)")
    envs = spec.get("envs") or {}
    g1b_spec = json.loads((HERE.parent / "g1b" / "g1b_spec.json").read_text()) \
        if (HERE.parent / "g1b" / "g1b_spec.json").is_file() else None
    if g1b_spec is not None:
        if envs != g1b_spec["envs"] or (spec.get("harness") or {}).get("commit") != g1b_spec["harness"]["commit"]:
            raise Stop("STOP: envs and harness.commit must equal g1b_spec.json (one harness pin for the T1 table)")
        g1b_nodes = {n["node"]: n for n in g1b_spec["nodes"]}
    for node in nodes:
        for key in ("spec_path", "node_dir"):
            value = node.get(key)
            if not isinstance(value, str) or not value or value.startswith("/") or ".." in Path(value).parts:
                raise Stop(f"STOP: {node.get('node')}.{key} must be a relative path without '..'")
        if g1b_spec is not None and node["node"] in g1b_nodes:
            for key in ("node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256", "run_seconds", "env",
                        "spec_path", "node_dir"):
                if node.get(key) != g1b_nodes[node["node"]].get(key):
                    raise Stop(f"STOP: {node['node']}.{key} differs from g1b_spec.json")
        for key in ("node_spec_sha256", "committed_pin_sha256"):
            g1b_lib._sha(node.get(key), f"{node['node']}.{key}", allow_placeholder=False)
        if "data_manifest_sha256" not in node:
            raise Stop(f"STOP: {node['node']}.data_manifest_sha256 must be the census value (null without data)")
        if node["data_manifest_sha256"] is not None:
            g1b_lib._sha(node["data_manifest_sha256"], f"{node['node']}.data_manifest_sha256", allow_placeholder=False)
        rs = node.get("run_seconds")
        if not isinstance(rs, (int, float)) or isinstance(rs, bool) or not 0 < rs <= 300:
            raise Stop(f"STOP: {node['node']}.run_seconds must be in (0, 300]")
        if node.get("env") not in envs:
            raise Stop(f"STOP: {node['node']}.env must name a declared environment")
    layout = spec.get("layout") or {}
    for key, lo, hi in (("request_cpus", 8, 64), ("request_memory_mb", 32000, 262144),
                        ("request_disk_kb", 42_000_000, 200_000_000), ("startup_reserve_s", 600, 7200),
                        ("startup_estimate_s", 60, 7200), ("llm_seconds_estimate", 5, 600)):
        if type(layout.get(key)) is not int or not lo <= layout[key] <= hi:
            raise Stop(f"STOP: layout.{key} must be an integer in [{lo}, {hi}]")
    cap = (spec.get("caps") or {}).get("max_total_gpu_hours")
    if not isinstance(cap, (int, float)) or not 0 < cap <= CAP_PILOT_GPU_HOURS:
        raise Stop(f"STOP: caps.max_total_gpu_hours must be in (0, {CAP_PILOT_GPU_HOURS}]")
    proj = projection(spec)
    if proj["total_gpu_hours"] > cap:
        raise Stop(f"STOP: the pilot projects {proj['total_gpu_hours']} GPU-h > cap {cap}")
    slot_h = sum(v["requested_walltime_s"] for v in proj["per_node"].values()) / 3600.0
    if slot_h > cap:
        raise Stop(f"STOP: the requested walltimes ({slot_h:.2f} slot-h) exceed the cap {cap}")
    if proj["max_walltime_s"] > g1b_lib.MAX_WALLTIME_S:
        raise Stop("STOP: a pilot job exceeds the 86,400 s walltime")
    return {"spec": spec, "run_id": run_id, "projection": proj}


def pilot_file(spec: dict, node: dict, *, base_url: str, interpreter: str, cgroup_parent: str, memory: str) -> dict:
    p = spec["pilot"]
    return {"schema": "trackg_g4_pilot/v1", "label": ENGINEERING_ONLY, "node": node["node"],
            "spec_path": node["spec_path"], "node_dir": node["node_dir"],
            "node_spec_sha256": node["node_spec_sha256"], "committed_pin_sha256": node["committed_pin_sha256"],
            "data_manifest_sha256": node["data_manifest_sha256"],
            "proposal_schema": "manager_proposal/v2-diff", "extra_payload": {"cache_prompt": False},
            "budget": p["budget"],
            "instances": [{"instance": i, **inst} for i, inst in enumerate(p["instances"], start=1)],
            "measured_run_seconds": node["run_seconds"], "base_url": base_url, "model": MODEL["alias"],
            "max_tokens": p["max_tokens"], "temperature": p["temperature"], "memory_mode": p["memory_mode"],
            "cgroup_parent": cgroup_parent, "interpreter": interpreter,
            "memory_limit": memory, "isolation_waivers": {}}


# =============================================================================================== job
def llama_identity(spec: dict) -> dict:
    binary = Path(spec["server"]["binary"])
    if not binary.is_file():
        raise Stop(f"STOP: {binary} missing from the image")
    got = hashlib.sha256(binary.read_bytes()).hexdigest()
    if got != spec["image"]["llama_server_sha256"]:
        raise Stop("STOP: llama-server sha256 differs from the v2 pin")
    return {"llama_server_sha256": got}


def run_node_job(spec_path: Path, node_name: str, *, started: float | None = None) -> dict:
    """The container job for one pilot node.  Every STOP, validation included, still writes job_record.json,
    out.tar and SHA256SUMS (kit review N1)."""
    started = started or time.time()
    scratch = Path(os.environ.get("_CONDOR_SCRATCH_DIR", "."))
    out = scratch / "out"
    record = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "node": node_name, "stop": None, "stop_class": None,
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
              "output_use": "ENGINEERING_ONLY G.4 pilot measurements; proposals are not labels"}
    server = None
    try:
        out.mkdir(exist_ok=False)
        record["spec_sha256"] = g1b_lib._sha_file(spec_path)
        loaded = validate_spec(g1b_lib.load_spec(spec_path), launch=True)
        spec = loaded["spec"]
        node = next((n for n in spec["nodes"] if n["node"] == node_name), None)
        if node is None:
            raise Stop(f"STOP: {node_name} is not a pilot node")
        walltime_s = walltime(node, spec["pilot"], spec["layout"])
        deadline = started + walltime_s - 300
        record.update(run_id=spec["run_id"], projection=loaded["projection"]["per_node"][node_name],
                      harness_commit=spec["harness"]["commit"], walltime_s=walltime_s)
        record["image"] = {**g1b_lib.image_identity(spec), **llama_identity(spec)}
        record["host"] = g1b_lib.host_identity()
        if record["host"]["euid"] == 0:
            raise Stop("STOP: the job runs as root; isolated runs need a non-root uid")
        record["gpu"] = g1b_lib.gpu_identity()
        record["paper"] = g1b_lib.clone_at(spec["paper"]["repo"], spec["paper"]["commit"], scratch / "paper")
        g1b_lib.check_staged_identity(scratch / "paper", {"g4_lib.py": "sweep2/g4/g4_lib.py",
                                                          "g1b_lib.py": "sweep2/g1b/g1b_lib.py",
                                                          "s2_c2_lib.py": "sweep2/s2_c2_lib.py",
                                                          "g4_job.sh": "sweep2/g4/g4_job.sh"})
        record["harness"] = g1b_lib.clone_at(spec["harness"]["repo"], spec["harness"]["commit"], scratch / "harness")
        g1b_spec = {"envs": spec["envs"]}
        freeze = scratch / "paper" / "sweep2" / "g1b" / spec["envs"][node["env"]]["freeze"]
        record["environment"] = g1b_lib.build_env(g1b_spec, node["env"], scratch / "env", freeze)
        harness = scratch / "harness"
        record["data"] = g1b_lib.run_setup(harness, node, scratch, out)
        cgroup = g1b_lib.delegated_cgroup()
        record["cgroup_parent"] = cgroup
        record["model"] = s2_c2_lib.fetch_model(spec["model"], scratch / "model.gguf")
        server = s2_c2_lib.start_server({"server": dict(spec["server"], port=0), "model": spec["model"]},
                                        scratch / "model.gguf", scratch / "llama-server.log")
        record["server"] = {k: v for k, v in server.items() if k != "proc"}
        pilot = pilot_file(spec, node, base_url=server["base_url"], interpreter=str(scratch / "env" / "bin" / "python"),
                           cgroup_parent=cgroup,
                           memory=f"HTCondor request_memory={spec['layout']['request_memory_mb']} MB (job cgroup)")
        (out / "pilot.json").write_text(json.dumps(pilot, indent=1) + "\n")
        remaining = int(deadline - time.time())
        if remaining < 60:
            raise Stop("STOP: the job deadline was reached before the pilot engine started")
        try:
            res = subprocess.run([str(scratch / "env" / "bin" / "python"), "-m", "autoresearch.trackg.pilot_g4", "run",
                                  "--pilot", str(out / "pilot.json"), "--harness-root", str(harness),
                                  "--out", str(out / "pilot")], cwd=harness, capture_output=True, text=True,
                                 timeout=remaining,
                                 env=dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1"))
        except subprocess.TimeoutExpired as exc:
            (out / "pilot_engine.log").write_text(f"{g1b_lib._text(exc.stdout)}\n--- stderr ---\n"
                                                  f"{g1b_lib._text(exc.stderr)}")
            raise Stop("STOP: the pilot engine reached the job deadline; partial outputs kept") from None
        (out / "pilot_engine.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
        summary_path = out / "pilot" / "pilot_summary.json"
        record["summary"] = json.loads(summary_path.read_text()) if summary_path.is_file() else None
        if res.returncode != 0:
            raise Stop(f"STOP: the pilot engine exited {res.returncode}; see out/pilot/pilot_record.json")
        fit = (record["summary"] or {}).get("fit") or {}
        if fit.get("cache_prompt_false_on_every_call") is False:
            raise Stop("STOP: a recorded request lacked cache_prompt: false")
        if fit.get("all_fit_ctx") is False:
            # a prompt too long for the context is a property of the node's prompt, so the author decides (node)
            raise NodeStop("STOP: a prompt plus the completion cap exceeds the 32,768 context")
        liveness = (record["summary"] or {}).get("diff_liveness") or {}
        if not liveness.get("ran_of_valid"):
            raise NodeStop("STOP: diff liveness 0 on a T1 pilot node (R1-BX-PROPOSED-CONFIRM D4: the author decides)")
    except NodeStop as exc:
        record["stop"], record["stop_class"] = str(exc), "node"
    except Stop as exc:
        record["stop"], record["stop_class"] = str(exc), "infrastructure"
    except Exception as exc:  # noqa: BLE001 - every failure still writes the record and sums (review m5)
        record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
    finally:
        if server is not None:
            s2_c2_lib._kill(server.get("proc"))
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (scratch / "job_record.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
    if out.is_dir():
        subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=scratch, check=False)
    g1b_lib._write_sums(scratch, ("out.tar", "job_record.json", "llama-server.log"))
    if record["stop"]:
        raise Stop(record["stop"])
    return record


# =============================================================================================== render + switch
def requirements(spec: dict) -> str:
    return " && ".join(f"({c})" for c in (
        "TARGET.GPUs >= 1", f'TARGET.GPUs_DeviceName =?= "{GPU_MODEL}"', 'TARGET.Arch == "X86_64"',
        'TARGET.OpSys == "LINUX"', f"TARGET.Cpus >= {spec['layout']['request_cpus']}"))


def render(spec: dict, node: dict, *, preview: bool = False) -> str:
    name = f"g4_{node['node']}"
    lines = [
        f"# G.4 T1 pilot on {GPU_MODEL} (ENGINEERING_ONLY) — {spec['run_id']}/{node['node']}",
        "universe = container", f"container_image = docker://{spec['image']['digest']}",
        f"executable = {'PREVIEW_NOT_SUBMITTABLE_' if preview else ''}g4_job.sh",
        f"arguments = g4_spec.json {node['node']}",
        f"log = {name}.log", f"output = {name}.out", f"error = {name}.err",
        f"request_cpus = {spec['layout']['request_cpus']}", f"request_memory = {spec['layout']['request_memory_mb']}",
        f"request_disk = {spec['layout']['request_disk_kb']}", "request_GPUs = 1",
        f"+RequestWalltime = {walltime(node, spec['pilot'], spec['layout'])}", "+RemoteJob = True",
        "periodic_hold = (NumJobStarts > 1)",
        "periodic_hold_reason = \"no resume: NumJobStarts > 1 must be rerun as a fresh submission into a new dir\"",
        "periodic_hold_subcode = 42", f"requirements = {requirements(spec)}",
        "should_transfer_files = YES", "when_to_transfer_output = ON_EXIT_OR_EVICT",
        "transfer_input_files = " + ",".join((*STAGED, "g4_spec.json")),
        f"transfer_output_files = {TRANSFER_OUTPUTS}", "queue 1"]
    return "\n".join(lines) + "\n"


def _staged_source(name: str) -> Path:
    return {"g4_job.sh": HERE / "g4_job.sh", "g4_lib.py": HERE / "g4_lib.py",
            "g1b_lib.py": HERE.parent / "g1b" / "g1b_lib.py", "s2_c2_lib.py": HERE.parent / "s2_c2_lib.py"}[name]


def stage(spec_path: Path, stage_dir: Path, *, preview: bool = False) -> dict:
    spec = g1b_lib.load_spec(spec_path)
    loaded = validate_spec(spec, launch=not preview)
    stage_dir = Path(stage_dir)
    if stage_dir.exists() and any(stage_dir.iterdir()):
        raise Stop(f"STOP: stage directory {stage_dir} is not empty")
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name in STAGED:
        shutil.copy2(_staged_source(name), stage_dir / name)
    shutil.copy2(spec_path, stage_dir / "g4_spec.json")
    files = {}
    for node in spec["nodes"]:
        (stage_dir / f"g4_{node['node']}.jdl").write_text(render(spec, node, preview=preview))
    for path in sorted(stage_dir.iterdir()):
        files[path.name] = g1b_lib._sha_file(path)
    manifest = {"schema": "g4_h200_stage/1", "run_id": loaded["run_id"], "preview": preview,
                "projection": loaded["projection"], "files": files}
    (stage_dir / "STAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


NOTE_NAME = re.compile(r"^g4_t1_pilot_\d{8}\.md$")
NOTE_REQUIRED = ("approved", "label", "run_id", "image", "versions_sha256", "llama_server_sha256", "harness_commit",
                 "paper_commit", "spec_sha256", "nodes", "budget_per_instance", "instances_per_node", "gpu_hours",
                 "labels_read")
PLAN_ROWS = ("R1-T1-HOST-H200", "R1-TRACKG-G3-EARLY")
NOTE_CITES = {"P1": "R1-T1-HOST-H200", "P2": "R1-TRACKG-G3-EARLY", "P3": "G1B",
              "P4": "docs/r1/reviews/"}
G1B_FIRST_RECEIPT = re.compile(r"g1b_first_receipt=(\S+) sha256=([0-9a-f]{64})")
IMAGE_ROW = re.compile(r"^PASS\s+[—-]\s+(R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])\b")     # as G.1b P6 (G1B-IMAGE)
NOT_IMAGE_ROWS = frozenset({"R1-SWEEP2-IMAGE", "R1-QTORCH-AMEND", "R1-TRACKP-I3-H200"})
G1B_FIRST_NODE = "mlab_ogbn_arxiv"
REPO_ROOT = HERE.parent.parent


def parse_note(text: str) -> dict:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate note field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    for key in NOTE_REQUIRED + ("P1", "P2", "P3", "P4", "P5"):
        if not fields.get(key):
            raise Stop(f"STOP: the note lacks {key!r}")
    for key in ("P1", "P2", "P3", "P4", "P5"):  # P5: image v2 row for the T1 table (G1B-IMAGE)
        if not fields[key].upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: {key} is not PASS")
    for key, cite in NOTE_CITES.items():
        if cite not in fields[key]:
            raise Stop(f"STOP: {key} must cite {cite}")
    image_row = IMAGE_ROW.match(fields["P5"])
    if not image_row:
        raise Stop("STOP: P5 must start with the PLAN row id that authorizes image v2 for the T1 table: 'PASS — R1-…'")
    if image_row.group(1) in NOT_IMAGE_ROWS or image_row.group(1) in PLAN_ROWS:
        raise Stop(f"STOP: {image_row.group(1)} does not authorize image v2 for the T1 table (G1B-IMAGE)")
    fields["image_row"] = image_row.group(1)
    if fields["approved"] != "true" or fields["label"] != ENGINEERING_ONLY or fields["labels_read"] != "none":
        raise Stop("STOP: the note must be approved: true, ENGINEERING_ONLY, labels_read: none")
    if fields["image"] != IMAGE_DIGEST:
        raise Stop("STOP: the note must pin the v2 gpu digest")
    try:
        gpu_h = float(fields["gpu_hours"])
    except ValueError:
        raise Stop("STOP: gpu_hours must be numeric") from None
    if not 0 < gpu_h <= CAP_PILOT_GPU_HOURS:
        raise Stop(f"STOP: gpu_hours must be in (0, {CAP_PILOT_GPU_HOURS}]")
    return fields


def _note_on_main(rel: str, raw: bytes) -> bool:
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "blob", f"origin/main:{rel}"],
                          capture_output=True, check=False)
    return blob.returncode == 0 and blob.stdout == raw


def check(stage_dir: Path, note_path: Path, *, on_main=_note_on_main) -> dict:
    note = Path(note_path)
    try:
        rel = note.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        raise Stop("STOP: the note must live in this repository") from None
    if tuple(Path(rel).parts[:3]) != ("docs", "r1", "authorizations") or not NOTE_NAME.fullmatch(note.name):
        raise Stop("STOP: the note must be docs/r1/authorizations/g4_t1_pilot_<YYYYMMDD>.md")
    raw = note.read_bytes()
    if not on_main(rel, raw):
        raise Stop("STOP: the note is not committed on origin/main")
    fields = parse_note(raw.decode())
    spec = g1b_lib.load_spec(Path(stage_dir) / "g4_spec.json")
    loaded = validate_spec(spec, launch=True)
    pairs = {"run_id": spec["run_id"], "image": spec["image"]["digest"], "paper_commit": spec["paper"]["commit"],
             "spec_sha256": g1b_lib._sha_file(Path(stage_dir) / "g4_spec.json"),
             "versions_sha256": spec["image"]["versions_sha256"],
             "llama_server_sha256": spec["image"]["llama_server_sha256"], "harness_commit": spec["harness"]["commit"],
             "nodes": ",".join(n["node"] for n in spec["nodes"]), "budget_per_instance": str(spec["pilot"]["budget"]),
             "instances_per_node": str(len(spec["pilot"]["instances"]))}
    for key, value in pairs.items():
        if fields[key] != value:
            raise Stop(f"STOP: spec {key}={value!r} differs from the note ({fields[key]!r})")
    if loaded["projection"]["total_gpu_hours"] > float(fields["gpu_hours"]):
        raise Stop("STOP: the spec projects more GPU-hours than the note authorizes")
    m = G1B_FIRST_RECEIPT.search(fields["P3"])
    if not m:
        raise Stop("STOP: P3 must give g1b_first_receipt=<path> sha256=<hex> (the sealed G.1b first-node receipt)")
    receipt_path = Path(m.group(1))
    if not receipt_path.is_file() or g1b_lib._sha_file(receipt_path) != m.group(2):
        raise Stop("STOP: the G.1b first-node receipt named in P3 is missing or its sha256 differs")
    receipt = json.loads(receipt_path.read_text())
    sealed_dir = receipt_path.parent
    record_path = sealed_dir / "job_record.json"
    record = json.loads(record_path.read_text()) if record_path.is_file() else {}
    problems = [k for k, ok in (
        ("name", receipt_path.name == "SEAL_RECEIPT.json" and sealed_dir.name == G1B_FIRST_NODE
         and sealed_dir.parent.parent.resolve() == g1b_lib.SEALED_ROOT.resolve()),
        ("schema", receipt.get("schema") == "g1b_h200_seal_receipt/1"),
        ("stop_class", receipt.get("stop_class") in (None, "node")),
        ("node", receipt.get("node") == G1B_FIRST_NODE and record.get("node") == G1B_FIRST_NODE),
        ("record", receipt.get("job_record_sha256") == (g1b_lib._sha_file(record_path) if record else None)),
        ("sums", subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed_dir, capture_output=True).returncode == 0),
        ("image", (record.get("image") or {}).get("digest") == IMAGE_DIGEST),
        ("harness", record.get("harness_commit") == spec["harness"]["commit"])) if not ok]
    if problems:
        raise Stop(f"STOP: the G.1b first-node receipt does not show a working H200 path: {problems}")
    manifest = json.loads((Path(stage_dir) / "STAGE_MANIFEST.json").read_text())
    if manifest.get("preview") is not False:
        raise Stop("STOP: a preview stage is never submittable")
    for name, sha in manifest["files"].items():
        if g1b_lib._sha_file(Path(stage_dir) / name) != sha:
            raise Stop(f"STOP: staged {name} changed after staging")
    for name in STAGED:
        if (Path(stage_dir) / name).read_bytes() != _staged_source(name).read_bytes():
            raise Stop(f"STOP: staged {name} differs from the reviewed checkout")
    for node in spec["nodes"]:
        if (Path(stage_dir) / f"g4_{node['node']}.jdl").read_text() != render(spec, node):
            raise Stop(f"STOP: g4_{node['node']}.jdl differs from the canonical render")
    return {"run_id": spec["run_id"], "nodes": pairs["nodes"], "note_sha256": hashlib.sha256(raw).hexdigest(),
            "image_row": fields["image_row"],
            "projection_gpu_hours": loaded["projection"]["total_gpu_hours"]}


def submit(stage_dir: Path, note_path: Path, *, enable: bool, node: str | None = None, on_main=_note_on_main,
           launch_binding=None, row_check=None) -> dict:
    checked = check(stage_dir, note_path, on_main=on_main)
    if not enable or os.environ.get("G4_ENABLE_REAL") != "1":
        raise Stop("STOP: G.4 real submission is disabled (needs --enable AND G4_ENABLE_REAL=1)")
    checked["launch"] = (launch_binding or g1b_lib.verify_launch)(
        REPO_ROOT, g1b_lib.load_spec(Path(stage_dir) / "g4_spec.json"), PLAN_ROWS + (checked["image_row"],))
    (row_check or check_plan_row)(checked["image_row"], REPO_ROOT, terms=IMAGE_ROW_TERMS, what="P5 image")
    names = checked["nodes"].split(",") if node is None else [node]
    if not set(names) <= set(checked["nodes"].split(",")):
        raise Stop(f"STOP: {node} is not an authorized pilot node")
    stage_dir = Path(stage_dir).resolve()
    out = []
    for name in names:
        try:
            with (stage_dir / f"G4_SUBMIT_STARTED_{name}.json").open("x") as marker:
                json.dump({"node": name, **checked}, marker)
        except FileExistsError:
            raise Stop(f"STOP: {name} was already submitted from this stage") from None
        res = subprocess.run(["condor_submit", f"g4_{name}.jdl"], cwd=stage_dir, capture_output=True, text=True,
                             timeout=600)
        if res.returncode != 0:
            raise Stop(f"STOP: condor_submit {name} rc={res.returncode}: {res.stderr.strip()[:300]}")
        out.append({"node": name, "condor_submit": res.stdout[-1000:]})
    return {"submitted": out, **checked}


# =============================================================================================== G.5 model, D14 recompute
G5_INSTANCES, G5_W, G5_LLM_CALL_CAP = 12, 20, 80   # R1-BX-D8-V3-B; G5-W; the cap per campaign under G5-W B
PILOT_PROPOSALS = 3 * W                             # 3 instances x 20 manager calls per pilot node


def g5_node(*, run_s: float, per_call_s: float, ran_share: float, keep_share: float, k: int, w_semantics: str,
            dup_factor: float, audit_inflation: float, startup_s: float, walltime_limit_s: int,
            reuse_parent_runs: bool = True) -> dict:
    """One node of the G.5 table (draft section 8): campaigns + audits + startup, in GPU-seconds.

    ``per_call_s``: campaign GPU-seconds per manager call (LLM, runs, reruns and the instance baselines amortized);
    ``ran_share``: ran proposals per manager call; ``keep_share``: keeps per ran proposal; ``dup_factor``: the share
    of ran proposals that are not cross-instance duplicates (audited once).  W semantics "manager_calls" (G5-W A) or
    "worker_runs" (G5-W B, with an LLM-call cap of 80 per campaign).  ``reuse_parent_runs``: a kept proposal's audit
    runs at the audit seeds serve again when it is the parent of later proposals (same code state, same seeds), so only
    the 12 baselines are extra parents (G.5 draft, proposed). It relies on fixed-seed determinism of edited code
    states on H200, which G.1b checks only at the default seeds and the G.5 cluster test C2 checks for audit pairs;
    False re-runs every parent."""
    if w_semantics == "manager_calls":
        calls = G5_INSTANCES * G5_W
        ran = calls * ran_share
    elif w_semantics == "worker_runs":
        calls = min(G5_INSTANCES * G5_W / max(ran_share, 1e-9), G5_INSTANCES * G5_LLM_CALL_CAP)
        ran = min(G5_INSTANCES * G5_W, calls * ran_share)
    else:
        raise Stop(f"STOP: unknown W semantics {w_semantics!r}")
    campaign_s = calls * per_call_s
    audited = ran * dup_factor
    parents = G5_INSTANCES + (0.0 if reuse_parent_runs else keep_share * ran)
    audit_s = (audited + parents) * k * run_s * audit_inflation
    chunks = max(1, math.ceil(audit_s * 1.5 / (walltime_limit_s - 3600)))
    jobs = 2 + chunks          # two campaign waves + audit chunks
    total_s = campaign_s + audit_s + jobs * startup_s
    return {"manager_calls": round(calls, 1), "ran": round(ran, 1), "audited": round(audited, 1),
            "parents": round(parents, 1), "campaign_gpu_hours": round(campaign_s / 3600, 2),
            "audit_gpu_hours": round(audit_s / 3600, 2), "audit_chunks": chunks, "jobs": jobs,
            "gpu_hours": round(total_s / 3600, 2)}


def check_summary(summary: dict, node: str) -> dict:
    """A pilot summary is used only if it is complete and unstopped (review B1.6)."""
    problems = []
    if summary.get("node") != node:
        problems.append("node")
    if summary.get("pilot_stop") or summary.get("stops"):
        problems.append("stopped")
    if summary.get("proposals") != PILOT_PROPOSALS:
        problems.append(f"proposals {summary.get('proposals')} != {PILOT_PROPOSALS}")
    sec = summary.get("seconds") or {}
    for key in ("llm_median", "run_median", "campaign_wall_total"):
        if not isinstance(sec.get(key), (int, float)) or not sec[key] > 0:
            problems.append(f"seconds.{key}")
    rates = summary.get("rates") or {}
    for key in ("ran_of_proposals", "kept_of_ran"):
        value = rates.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            problems.append(f"rates.{key}")
    if isinstance(rates.get("ran_of_proposals"), (int, float)) and rates["ran_of_proposals"] == 0:
        problems.append("rates.ran_of_proposals is 0 (no proposal ran: zero diff liveness)")
    if problems:
        raise Stop(f"STOP: the pilot summary of {node} cannot be used: {problems}")
    return summary


def recompute_dates(summaries: dict[str, dict], params: dict, *, today: date) -> dict:
    """R1-BX-D14 recompute after G.4, from measured H200 throughput, for the G.5 table as the draft defines it.

    Pilot nodes use their own measured campaign seconds per manager call (``campaign_wall_total / proposals``), run
    median, ran share and keep share.  Nodes without a pilot summary use the census run time scaled by the median
    measured H200/census run-time ratio of the pilot nodes (stated in the output), the median LLM seconds and the
    median shares.  Both K = 10 and K = 6 are computed; K = 10 binds until the K-check row exists
    (``params["k_check_passed"]``).  D.3 and the manuscript are B.7 shifted by the R1-BX-D14 target spans."""
    pilot_nodes = set(params["pilot_nodes"])
    for node, s in summaries.items():
        if node not in pilot_nodes:
            raise Stop(f"STOP: {node} is not a pilot node")
        check_summary(s, node)
    census = {n: float(v) for n, v in params["run_seconds"].items()}
    if summaries:
        ratio = statistics_median([s["seconds"]["run_median"] / census[n] for n, s in summaries.items()])
        llm_s = statistics_median([s["seconds"]["llm_median"] for s in summaries.values()])
        ran_share = statistics_median([s["rates"]["ran_of_proposals"] for s in summaries.values()])
        keep_share = statistics_median([s["rates"]["kept_of_ran"] for s in summaries.values()])
        basis = "measured (G.4 pilot on H200)"
    else:
        ratio, llm_s = 1.0, float(params["llm_seconds_fallback"])
        ran_share, keep_share = float(params["ran_share_fallback"]), float(params["keep_share_fallback"])
        basis = "pre-pilot fallbacks (census run times, assumed shares)"
    # cross-instance duplicates (G.5 draft G5-AUDIT): a group is audited once, so the audited share of ran proposals
    # is 1 - (ran in groups - groups) / ran, measured on the pilot's 3 instances (a lower bound for 12 instances)
    dup = float(params["dup_factor"])
    dup_source = "params (no pilot summary carried cross_instance_duplicates)"
    if summaries:
        factors = []
        for s in summaries.values():
            cd = s.get("cross_instance_duplicates") or {}
            ran_n = (s["rates"]["ran_of_proposals"] or 0) * s["proposals"]
            if ran_n > 0 and isinstance(cd.get("groups"), int) and isinstance(cd.get("ran_proposals_in_groups"), int):
                factors.append(1.0 - (cd["ran_proposals_in_groups"] - cd["groups"]) / ran_n)
        if factors:
            dup = statistics_median(factors)
            dup_source = f"pilot: median over {len(factors)} node(s) of 1 - (ran in groups - groups) / ran"
    mem = int(params.get("mem_modes", 1))
    if mem not in (1, 2):
        raise Stop("STOP: mem_modes must be 1 (G5-MEM A) or 2 (G5-MEM B: both modes, 12 instances each)")
    common = {"w_semantics": params["w_semantics"], "dup_factor": dup,
              "reuse_parent_runs": bool(params.get("reuse_parent_runs", True)),
              "audit_inflation": float(params["audit_inflation"]), "startup_s": float(params["startup_s"]),
              "walltime_limit_s": g1b_lib.MAX_WALLTIME_S}
    out_k = {}
    for k in (10, 6):
        per_node = {}
        for node in params["t1_nodes"]:
            if node in summaries:
                s = summaries[node]
                inputs = {"run_s": s["seconds"]["run_median"],
                          "per_call_s": s["seconds"]["campaign_wall_total"] / s["proposals"],
                          "ran_share": s["rates"]["ran_of_proposals"], "keep_share": s["rates"]["kept_of_ran"],
                          "source": "pilot"}
            else:
                run_s = census[node] * ratio
                per_call = llm_s + ran_share * run_s * float(params["campaign_inflation"]) \
                    + G5_INSTANCES * run_s / (G5_INSTANCES * G5_W)
                inputs = {"run_s": run_s, "per_call_s": per_call, "ran_share": ran_share, "keep_share": keep_share,
                          "source": "census x ratio"}
            row = g5_node(k=k, **{x: inputs[x] for x in ("run_s", "per_call_s", "ran_share", "keep_share")}, **common)
            work_h = row["gpu_hours"] - row["jobs"] * common["startup_s"] / 3600
            row = {key: (round(v * mem, 2) if key in ("gpu_hours", "campaign_gpu_hours", "audit_gpu_hours") else v)
                   for key, v in row.items()}
            row["requested_slot_hours"] = round(mem * (row["jobs"] + 1.5 * work_h), 2)
            per_node[node] = {**row, "inputs": {x: (round(v, 4) if isinstance(v, float) else v)
                                                for x, v in inputs.items()}}
        out_k[k] = {"per_node": per_node, "total_gpu_hours": round(sum(v["gpu_hours"] for v in per_node.values()), 1),
                    "requested_slot_hours": round(sum(v["requested_slot_hours"] for v in per_node.values()), 1)}
    if not isinstance(params.get("k_check_passed"), bool):
        raise Stop("STOP: k_check_passed must be true or false")
    if params["k_check_passed"] and not re.match(r"^R1-[A-Z0-9-]+$", str(params.get("k_check_row", ""))):
        raise Stop("STOP: k_check_passed true needs k_check_row, the PLAN row recording the K-check PASS "
                   "(the CLI checks it on origin/main)")
    binding_k = 6 if params["k_check_passed"] else 10
    total = out_k[binding_k]["total_gpu_hours"]
    slots = max(1, int(params["concurrent_h200_slots"]))
    # the work of one node is serial (wave 1 campaigns, audits, checks, wave 2 campaigns, audits), so the label
    # span is at least the longest node's work
    longest_node_h = max(v["gpu_hours"] for v in out_k[binding_k]["per_node"].values())
    label_h = max(total / slots, longest_node_h)
    wall_days = math.ceil(float(params["prerequisite_days"]) + float(params.get("g1b_days", 0))
                          + float(params["queue_days"]) + label_h / 24.0)
    labels_done = today + timedelta(days=wall_days)
    b7 = labels_done + timedelta(days=int(params["analysis_days_to_b7"]))
    d3 = b7 + timedelta(days=int(params["b7_to_d3_days"]))
    manuscript = d3 + timedelta(days=int(params["d3_to_manuscript_days"]))
    targets = {"B7": date(2026, 12, 8), "D3": date(2027, 1, 3), "manuscript": date(2027, 1, 10)}
    got = {"B7": b7, "D3": d3, "manuscript": manuscript}
    cap = float(params["g5_cap_gpu_hours"])
    slot_cap = cap * float(params.get("slot_cap_factor", 1.6))
    return {"today": today.isoformat(), "basis": basis, "binding_K": binding_k,
            "h200_over_census_run_ratio": round(ratio, 4),
            "ratio_basis": "median over pilot nodes of (pilot run median, edited runs included, on H200) / (census B1 "
                           "baseline time on Ada)",
            "pilot_nodes_measured": sorted(summaries), "nodes_from_census_x_ratio":
                sorted(n for n in params["t1_nodes"] if n not in summaries), "llm_seconds_median": llm_s,
            "ran_share_median": ran_share, "keep_share_median": keep_share,
            "g5_by_K": {str(k): v for k, v in out_k.items()}, "g5_total_gpu_hours": total,
            "g5_cap_gpu_hours": cap, "g5_within_cap": total <= cap,
            "g5_requested_slot_hours": out_k[binding_k]["requested_slot_hours"], "g5_slot_cap": round(slot_cap, 1),
            "g5_slots_within_cap": out_k[binding_k]["requested_slot_hours"] <= slot_cap,
            "dup_factor_used": round(dup, 4), "dup_factor_source": dup_source, "mem_modes": mem, "longest_node_gpu_hours": longest_node_h,
            "labels_done": labels_done.isoformat(), "B7": b7.isoformat(), "D3": d3.isoformat(),
            "manuscript": manuscript.isoformat(),
            "targets_R1_BX_D14": {k: v.isoformat() for k, v in targets.items()},
            "slack_days": {k: (targets[k] - got[k]).days for k in targets},
            "note": "D3 and manuscript are B7 shifted by the R1-BX-D14 target spans (not recomputed separately)",
            "params": params}


K_CHECK_ROW_TERMS = ("K-check", "PASS")           # the K-check row must record a K-check PASS
IMAGE_ROW_TERMS = ("b1144ece", "T1")               # the image row must name the v2 gpu digest and the T1 table


def check_plan_row(row, repo: Path | None = None, *, terms: tuple[str, ...] = K_CHECK_ROW_TERMS,
                   what: str = "K-check") -> str:
    """The row must be a PLAN row on the local origin/main (fetched) whose text contains every term (case-sensitive);
    returns the row line."""
    plan = subprocess.run(["git", "-C", str(repo or REPO_ROOT), "show", "origin/main:docs/r1/PLAN.md"],
                          capture_output=True, text=True, check=False).stdout
    m = re.search(rf"^\| {re.escape(row)} \|.*$", plan, re.M) if isinstance(row, str) else None
    if not m:
        raise Stop(f"STOP: the {what} row {row!r} is not on origin/main PLAN")
    missing = [t for t in terms if t not in m.group(0)]
    if missing:
        raise Stop(f"STOP: the {what} row {row!r} does not name {missing}")
    return m.group(0)


def statistics_median(values: list[float]) -> float:
    values = sorted(values)
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2


# =============================================================================================== seal + read
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/g4_h200")


def seal(job_output: Path, run_id: str, node: str, *, sealed_root: Path | None = None) -> dict:
    """As ``g1b_lib.seal``: verify the transferred sums and record, copy to <sealed_root>/<run_id>/<node>/ (no
    overwrite), and write a receipt binding the record, ``llama-server.log`` and ``g4_run.log`` (both are written
    after SHA256SUMS)."""
    src = Path(job_output).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("label") != ENGINEERING_ONLY or record.get("run_id") != run_id or record.get("node") != node:
        raise Stop("STOP: the job record does not match the run/node or is not ENGINEERING_ONLY")
    if (record.get("image") or {}).get("digest") != IMAGE_DIGEST or (record.get("gpu") or {}).get("name") != GPU_MODEL:
        raise Stop("STOP: the job record lacks the pinned image or the H200 identity")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
        raise Stop("STOP: transferred SHA256SUMS verification failed")
    for name in (run_id, node):
        if not g1b_lib.SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    target = (sealed_root or SEALED_ROOT) / run_id / node
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "llama-server.log", "g4_run.log"):
        if (src / name).exists():
            shutil.copy2(src / name, target / name)
    receipt = {"schema": "g4_h200_seal_receipt/1", "run_id": run_id, "node": node, "sealed_path": str(target),
               "stop": record.get("stop"), "stop_class": record.get("stop_class"),
               "job_record_sha256": g1b_lib._sha_file(target / "job_record.json"),
               **{f"{n.replace('-', '_').replace('.', '_')}_sha256": (g1b_lib._sha_file(target / n)
                                                                    if (target / n).is_file() else None)
                  for n in ("llama-server.log", "g4_run.log")},
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def read_sealed_summary(sealed: Path, spec: dict, spec_file_sha256: str) -> dict:
    """The pilot summary of one sealed job, after the receipt, sums and table identity are verified."""
    import tarfile
    sealed = Path(sealed)
    if not (sealed / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: {sealed} has no SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed, capture_output=True).returncode != 0:
        raise Stop(f"STOP: {sealed} does not verify against its SHA256SUMS")
    record = json.loads((sealed / "job_record.json").read_text())
    receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    problems = [k for k, ok in (
        ("receipt", receipt.get("job_record_sha256") == g1b_lib._sha_file(sealed / "job_record.json")),
        ("run_id", record.get("run_id") == spec["run_id"]), ("spec_sha256", record.get("spec_sha256") == spec_file_sha256),
        ("harness_commit", record.get("harness_commit") == spec["harness"]["commit"]),
        ("image", (record.get("image") or {}).get("digest") == IMAGE_DIGEST),
        ("gpu", (record.get("gpu") or {}).get("name") == GPU_MODEL),
        ("stop", record.get("stop") is None)) if not ok]
    if problems:
        raise Stop(f"STOP: {sealed} cannot feed the recompute: {problems}")
    with tarfile.open(sealed / "out.tar") as tar:
        try:
            member = tar.extractfile("out/pilot/pilot_summary.json")
        except KeyError:
            member = None
        if member is None:
            raise Stop(f"STOP: {sealed}/out.tar has no out/pilot/pilot_summary.json")
        summary = json.loads(member.read())
    return check_summary(summary, record["node"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    j = sub.add_parser("job"); j.add_argument("spec"); j.add_argument("--node", required=True)
    st = sub.add_parser("stage"); st.add_argument("spec", type=Path); st.add_argument("stage_dir", type=Path)
    st.add_argument("--preview", action="store_true")
    c = sub.add_parser("check"); c.add_argument("--stage", required=True); c.add_argument("--note", required=True)
    s = sub.add_parser("submit"); s.add_argument("--stage", required=True); s.add_argument("--note", required=True)
    s.add_argument("--enable", action="store_true"); s.add_argument("--node", default=None)
    d = sub.add_parser("dates"); d.add_argument("--params", required=True, type=Path)
    d.add_argument("--spec", type=Path, default=None, help="the staged g4_spec.json the sealed jobs ran")
    d.add_argument("--sealed", nargs="*", type=Path, default=[], help="sealed node directories (g4_lib.py seal)")
    d.add_argument("--today", required=True)
    z = sub.add_parser("seal"); z.add_argument("job_output", type=Path); z.add_argument("--run-id", required=True)
    z.add_argument("--node", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            print(json.dumps(validate_spec(g1b_lib.load_spec(Path(a.spec)), launch=a.launch)["projection"], indent=1))
        elif a.cmd == "job":
            run_node_job(Path(a.spec), a.node)
        elif a.cmd == "stage":
            print(json.dumps(stage(a.spec, a.stage_dir, preview=a.preview), indent=1))
        elif a.cmd == "check":
            print(json.dumps(check(Path(a.stage), Path(a.note)), indent=1))
        elif a.cmd == "submit":
            print(json.dumps(submit(Path(a.stage), Path(a.note), enable=a.enable, node=a.node), indent=1))
        elif a.cmd == "seal":
            print(json.dumps(seal(a.job_output, a.run_id, a.node), indent=1))
        else:
            sums = {}
            if a.sealed:
                if a.spec is None:
                    raise Stop("STOP: --sealed needs --spec (the staged spec the jobs ran)")
                spec = g1b_lib.load_spec(a.spec)
                for d_ in a.sealed:
                    summary = read_sealed_summary(d_, spec, g1b_lib._sha_file(a.spec))
                    if summary["node"] in sums:
                        raise Stop(f"STOP: {summary['node']} is given twice")
                    sums[summary["node"]] = summary
            params = json.loads(a.params.read_text())
            if params.get("k_check_passed") is True:
                check_plan_row(params.get("k_check_row"))
            print(json.dumps(recompute_dates(sums, params, today=date.fromisoformat(a.today)), indent=1))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
