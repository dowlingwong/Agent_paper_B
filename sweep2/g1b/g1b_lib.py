#!/usr/bin/env python3
"""G.1b — T1 GPU-node noise floors on NEMO2 H200 (HTCondor): spec validation, chunk plan, job, summary, seal.

Authority: R1-T1-HOST-H200 and R1-TRACKG-G3-EARLY (20 Nov 2026), R1-G1B-CAP (100 GPU-h author STOP; D21 protocol
unchanged), D21 rule / uniform application (22 Oct), R1-BX-D5 (fixed step budgets, one GPU model per table),
R1-HARNESS-ISOLATION (the unisolated-run gate), R1-TRACKG-PORT-DECISIONS (4) (timeout = 3 x the census run time).
Design and decisions: ``sweep2/g1b/G1B_H200_PLAN.md``.  ENGINEERING_ONLY; no labels are read.  Stdlib only: the
job runs this file with the image's harness Python; the node runs use the job-built Track G environment.

Per node, one HTCondor job runs four parts in order: ``default`` + ``default_repeat`` (fixed-seed determinism;
a mismatch STOPs the node before any seeded run), then ``train``, ``split`` and ``joint`` (30 seeds each).  Each
part is one chunk of the harness engine ``autoresearch.trackg.noise_floor`` (pinned harness commit), which refuses
any run record that is not ``effective: true`` with empty waivers and exceptions.
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
from pathlib import Path

SCHEMA = "g1b_h200_job/v1"
RECORD_SCHEMA = "g1b_h200_job_record/1"
SUMMARY_SCHEMA = "g1b_h200_summary/1"
ENGINEERING_ONLY = "ENGINEERING_ONLY"
GPU_MODEL = "NVIDIA H200"
IMAGE_DIGEST = ("ghcr.io/dowlingwong/r1-htc-gpu@sha256:"
                "b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd")  # v2 gpu (R1-QTORCH-AMEND)
ORCHESTRATOR_PYTHON = "/opt/r1/envs/harness/bin/python"
UV = "/opt/uv/uv"
UV_PYTHONS = "/opt/r1/pythons"
PAPER_REPO = "https://github.com/dowlingwong/Agent_paper_B.git"
HARNESS_REPO = "https://github.com/dowlingwong/autoresearch_harness.git"
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/g1b_h200")

# R1-TRACKG-G3-EARLY: the six T1 nodes now; autoresearch_fixedtokens and mlgym_houseprice join after their U2.
T1_NODES_NOW = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist",
                "mlgym_breakout_minatar")
T1_NODES_LATER = ("autoresearch_fixedtokens", "mlgym_houseprice")

# D21 (22 Oct) — fixed constants, not spec values.
SEEDS_PER_CONDITION = 30
SEED_BASES = {"train": 1001, "split": 2001, "joint": 3001}
SPLIT_POLICY = "vary"
D21_MIN_MATERIAL_EDITS = 2
D21_MIN_EFFECT = 0.002
D21_MIN_MEAN_P_WRONG = 0.10
PARTS = (("default", ("default", "default_repeat"), None),
         ("train", ("train",), (1001, 1030)),
         ("split", ("split",), (2001, 2030)),
         ("joint", ("joint",), (3001, 3030)))

# Caps and layout rules (reviewed code; a spec may lower, never raise).
CAP_TOTAL_GPU_HOURS = 100.0       # R1-G1B-CAP
MAX_WALLTIME_S = 86400            # sweep-2 / S2-C2 bound for one HTCondor job
WALL_FACTOR = 1.5                 # the 20 Nov task: walltime = census per-run times x 1.5 plus startup
RUN_SECONDS_CEILING = 300.0       # R1-BX-D5
TIMEOUT_FACTOR = 3.0              # R1-TRACKG-PORT-DECISIONS (4)

SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
PLACEHOLDER = re.compile(r"^(TODO|PENDING|PLACEHOLDER|TBD|FILL)", re.IGNORECASE)
TRANSFER_OUTPUTS = "out.tar,job_record.json,SHA256SUMS,g1b_run.log"


class Stop(Exception):
    """A pre-declared STOP; outputs are preserved, nothing is retried."""


# =============================================================================================== spec
def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise Stop(f"STOP: cannot read spec {path}: {exc}") from None
    if not isinstance(spec, dict):
        raise Stop("STOP: spec must be a JSON object")
    return spec


def _placeholder(value) -> bool:
    return isinstance(value, str) and bool(PLACEHOLDER.match(value))


def _sha(value, name: str, *, allow_placeholder: bool) -> str:
    if allow_placeholder and _placeholder(value):
        return value
    if not isinstance(value, str) or not SHA.fullmatch(value):
        raise Stop(f"STOP: {name} must be a sha256 (64 hex)")
    return value


def _commit(value, name: str, *, allow_placeholder: bool) -> str:
    if allow_placeholder and _placeholder(value):
        return value
    if not isinstance(value, str) or not COMMIT.fullmatch(value):
        raise Stop(f"STOP: {name} must be a full 40-hex commit")
    return value


def runs_per_node(n_edits: int) -> int:
    return (n_edits + 1) * (len(SEED_BASES) * SEEDS_PER_CONDITION + 2)


def part_runs(n_edits: int, part: str) -> int:
    return (n_edits + 1) * (2 if part == "default" else SEEDS_PER_CONDITION)


def node_walltime(node: dict, layout: dict) -> int:
    runs = runs_per_node(node["n_edits"])
    return int(layout["startup_reserve_s"]) + int(math.ceil(runs * float(node["run_seconds"]) * WALL_FACTOR))


def projection(spec: dict) -> dict:
    """GPU-h = one GPU per job, workers = 1: sum over nodes of runs x census run time, plus a declared startup
    estimate per job; the requested walltime (x 1.5 + reserve) is reported separately as slot-hours."""
    layout = spec["layout"]
    per_node = {}
    for node in spec["nodes"]:
        runs = runs_per_node(node["n_edits"])
        run_h = runs * float(node["run_seconds"]) / 3600.0
        per_node[node["node"]] = {
            "runs": runs, "run_seconds": node["run_seconds"],
            "run_gpu_hours": round(run_h, 3),
            "gpu_hours_with_startup": round(run_h + float(layout["startup_estimate_s"]) / 3600.0, 3),
            "requested_walltime_s": node_walltime(node, layout)}
    total = sum(v["gpu_hours_with_startup"] for v in per_node.values())
    return {"per_node": per_node, "jobs": len(per_node), "total_runs": sum(v["runs"] for v in per_node.values()),
            "total_run_gpu_hours": round(sum(v["run_gpu_hours"] for v in per_node.values()), 3),
            "total_gpu_hours": round(total, 3),
            "requested_slot_hours": round(sum(v["requested_walltime_s"] for v in per_node.values()) / 3600.0, 3),
            "max_walltime_s": max(v["requested_walltime_s"] for v in per_node.values()),
            "cap_total_gpu_hours": spec["caps"]["max_total_gpu_hours"]}


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """Fail-closed validation.  ``launch=True`` (the job and the switch) refuses every placeholder."""
    allow = not launch
    if spec.get("schema") != SCHEMA:
        raise Stop(f"STOP: spec schema must be {SCHEMA}")
    if spec.get("label") != ENGINEERING_ONLY:
        raise Stop("STOP: G.1b is ENGINEERING_ONLY (a measurement, not a label table)")
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not SAFE.fullmatch(run_id) or run_id in (".", ".."):
        raise Stop("STOP: run_id must be a safe path component")
    image = spec.get("image") or {}
    if image.get("digest") != IMAGE_DIGEST:
        raise Stop("STOP: image.digest must be the v2 gpu digest (one digest per table)")
    _sha(image.get("versions_sha256"), "image.versions_sha256", allow_placeholder=allow)
    for key, repo in (("paper", PAPER_REPO), ("harness", HARNESS_REPO)):
        block = spec.get(key) or {}
        if block.get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
        _commit(block.get("commit"), f"{key}.commit", allow_placeholder=allow)
    if spec.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: gpu_model must be {GPU_MODEL} (R1-T1-HOST-H200; one GPU model per table)")
    m = spec.get("measurement") or {}
    want = {"seeds_per_condition": SEEDS_PER_CONDITION, "seed_bases": SEED_BASES, "split_policy": SPLIT_POLICY,
            "workers": 1, "timeout_factor": TIMEOUT_FACTOR, "wall_factor": WALL_FACTOR,
            "isolation_gate": "effective:true, waivers {}, exceptions []"}
    for key, value in want.items():
        if m.get(key) != value:
            raise Stop(f"STOP: measurement.{key} must be {value!r} (D21 / R1-HARNESS-ISOLATION; fixed)")
    caps = spec.get("caps") or {}
    if not isinstance(caps.get("max_total_gpu_hours"), (int, float)) or \
            not 0 < caps["max_total_gpu_hours"] <= CAP_TOTAL_GPU_HOURS:
        raise Stop(f"STOP: caps.max_total_gpu_hours must be in (0, {CAP_TOTAL_GPU_HOURS}] (R1-G1B-CAP)")
    layout = spec.get("layout") or {}
    for key, lo, hi in (("request_cpus", 4, 64), ("request_memory_mb", 8192, 262144),
                        ("request_disk_kb", 10_000_000, 200_000_000), ("startup_reserve_s", 600, 7200),
                        ("startup_estimate_s", 60, 7200)):
        if type(layout.get(key)) is not int or not lo <= layout[key] <= hi:
            raise Stop(f"STOP: layout.{key} must be an integer in [{lo}, {hi}]")
    envs = spec.get("envs") or {}
    if set(envs) - {"torch312", "jax312"} or not envs:
        raise Stop("STOP: envs must be torch312 and/or jax312 (the census environments)")
    here = Path(__file__).resolve().parent
    for name, env in envs.items():
        if env.get("python") != "3.12.16":
            raise Stop(f"STOP: envs.{name}.python must be 3.12.16 (the census and image trackp Python)")
        rel = env.get("freeze")
        if not isinstance(rel, str) or not SAFE.fullmatch(Path(rel).name) or Path(rel).parent.name != "env":
            raise Stop(f"STOP: envs.{name}.freeze must be env/<file>")
        _sha(env.get("sha256"), f"envs.{name}.sha256", allow_placeholder=False)
        path = here / rel if (here / rel).is_file() else Path(Path(rel).name)
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != env["sha256"]:
            raise Stop(f"STOP: envs.{name}.freeze sha256 differs from the pin")
    decision = spec.get("edit_count") or {}
    n_edits = decision.get("n_edits_per_node")
    if type(n_edits) is not int or not 3 <= n_edits <= 5 or decision.get("runs_per_node") != runs_per_node(n_edits):
        raise Stop("STOP: edit_count.n_edits_per_node (3-5) and runs_per_node = (n+1) x 92 must agree")
    if launch and _placeholder(decision.get("authority")):
        raise Stop("STOP: the edit count needs the author's decision (edit_count.authority) before launch")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise Stop("STOP: nodes must be a non-empty list")
    names = [n.get("node") for n in nodes]
    if len(set(names)) != len(names):
        raise Stop("STOP: a node is listed twice")
    unknown = set(names) - set(T1_NODES_NOW) - set(T1_NODES_LATER)
    if unknown:
        raise Stop(f"STOP: {sorted(unknown)} are not T1 nodes (R1-TRACKG-G3-EARLY)")
    missing = set(T1_NODES_NOW) - set(names)
    if missing:
        raise Stop(f"STOP: the six T1 nodes must all be measured (D21 uniform application); missing {sorted(missing)}")
    for node in nodes:
        name = node["node"]
        for key in ("spec_path", "node_dir"):
            value = node.get(key)
            if not isinstance(value, str) or value.startswith("/") or ".." in Path(value).parts:
                raise Stop(f"STOP: {name}.{key} must be a relative path inside the harness checkout")
        for key in ("node_spec_sha256", "committed_pin_sha256", "deployed_pin_sha256", "edits_manifest_sha256"):
            _sha(node.get(key), f"{name}.{key}", allow_placeholder=False)
        if node.get("n_edits") != n_edits:
            raise Stop(f"STOP: {name} has {node.get('n_edits')} declared edits; every node uses {n_edits} (uniform)")
        rs = node.get("run_seconds")
        if not isinstance(rs, (int, float)) or isinstance(rs, bool) or not 0 < rs <= RUN_SECONDS_CEILING:
            raise Stop(f"STOP: {name}.run_seconds (census per-run time) must be in (0, {RUN_SECONDS_CEILING}]")
        if node.get("env") not in envs:
            raise Stop(f"STOP: {name}.env must name a declared environment")
        if not isinstance(node.get("census_record"), str) or not node["census_record"]:
            raise Stop(f"STOP: {name}.census_record must name the census U2 record")
        if node_walltime(node, layout) > MAX_WALLTIME_S:
            raise Stop(f"STOP: {name} needs {node_walltime(node, layout)} s walltime > {MAX_WALLTIME_S}: split the node")
    census = spec.get("census") or {}
    _commit(census.get("commit"), "census.commit", allow_placeholder=False)
    _sha(census.get("report_sha256"), "census.report_sha256", allow_placeholder=False)
    proj = projection(spec)
    if proj["total_gpu_hours"] > caps["max_total_gpu_hours"]:
        raise Stop(f"STOP: projected {proj['total_gpu_hours']} GPU-h exceeds the R1-G1B-CAP "
                   f"{caps['max_total_gpu_hours']} GPU-h: author STOP")
    return {"spec": spec, "run_id": run_id, "projection": proj, "n_edits": n_edits}


def node_entry(spec: dict, name: str) -> dict:
    for node in spec["nodes"]:
        if node["node"] == name:
            return node
    raise Stop(f"STOP: node {name} is not in the spec")


def expected_runs(n_edits: int, conditions: tuple[str, ...], seed_range) -> list[dict]:
    """Mirror of autoresearch.trackg.noise_floor.expected_runs (the engine re-checks the expansion)."""
    configs = ["c0"] + [f"c{k}" for k in range(1, n_edits + 1)]
    runs = []
    for condition in conditions:
        if seed_range is None:
            runs += [{"config": c, "condition": condition, "train_seed": None, "split_seed": None} for c in configs]
            continue
        for seed in range(seed_range[0], seed_range[1] + 1):
            runs += [{"config": c, "condition": condition,
                      "train_seed": seed if condition in ("train", "joint") else None,
                      "split_seed": seed if condition in ("split", "joint") else None} for c in configs]
    return runs


def chunk_file(spec: dict, node: dict, part: tuple, *, interpreter: str, cgroup_parent: str, deadline: float,
               memory_limit: str) -> dict:
    part_id, conditions, seed_range = part
    return {
        "schema": "trackg_noise_chunk/v1", "label": ENGINEERING_ONLY,
        "chunk_id": f"{spec['run_id']}-{node['node']}-{part_id}", "node": node["node"],
        "spec_path": node["spec_path"], "node_dir": node["node_dir"],
        "node_spec_sha256": node["node_spec_sha256"], "frozen_pin_sha256": node["deployed_pin_sha256"],
        "edits_manifest_sha256": node["edits_manifest_sha256"], "n_edits": node["n_edits"],
        "conditions": list(conditions), "seed_range": list(seed_range) if seed_range else None,
        "runs": expected_runs(node["n_edits"], conditions, seed_range),
        "measured_run_seconds": node["run_seconds"], "timeout_factor": TIMEOUT_FACTOR,
        "deadline_epoch": deadline, "cgroup_parent": cgroup_parent, "interpreter": interpreter,
        "memory_limit": memory_limit, "isolation_waivers": {},
    }


# =============================================================================================== D21 math
def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _sd(values) -> float:
    xs = [float(v) for v in values]
    if len(xs) < 2:
        return float("nan")
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1))


def edit_stats(deltas_joint) -> dict:
    dj = [float(x) for x in deltas_joint]
    if len(dj) < 2:
        raise Stop("STOP: a D21 edit needs the paired joint deltas")
    delta = sum(dj) / len(dj)
    sd = _sd(dj)
    se = sd / math.sqrt(len(dj))
    resolved = (abs(delta) > 2 * se) if se > 0 else (delta != 0)
    p_wrong = _phi(-abs(delta) / sd) if sd > 0 else (0.0 if delta != 0 else float("nan"))
    return {"n_joint": len(dj), "delta_hat_J": delta, "sd_joint": sd, "se": se, "resolved": bool(resolved),
            "material": bool(resolved and abs(delta) >= D21_MIN_EFFECT), "p_wrong": p_wrong}


def d21_qualify(edits: list[dict], sigma_joint: float, seeds_per_condition: int) -> dict:
    material = [e for e in edits if e.get("material")]
    p_vals = [float(e["p_wrong"]) for e in material if not math.isnan(float(e["p_wrong"]))]
    mean_p = sum(p_vals) / len(p_vals) if p_vals else float("nan")
    checks = {"seeds_per_condition_is_30": int(seeds_per_condition) == SEEDS_PER_CONDITION,
              "material_edits_ge_2": len(material) >= D21_MIN_MATERIAL_EDITS,
              "mean_p_wrong_ge_0.10": bool(p_vals) and mean_p >= D21_MIN_MEAN_P_WRONG,
              "sigma_joint_gt_0": float(sigma_joint) > 0}
    return {"qualifies_D21": all(checks.values()), "checks": checks, "n_edits": len(edits),
            "n_material": len(material), "mean_p_wrong_material": mean_p, "sigma_joint": float(sigma_joint)}


def determinism_check(rows: list[dict]) -> dict:
    pairs: dict[str, dict] = {}
    for row in rows:
        if row.get("condition") in ("default", "default_repeat"):
            pairs.setdefault(row["config"], {})[row["condition"]] = row.get("metric") if row.get("success") else None
    per, ok = {}, True
    for config, got in sorted(pairs.items()):
        a, b = got.get("default"), got.get("default_repeat")
        same = a is not None and a == b
        per[config] = {"default": a, "default_repeat": b, "bit_identical": same}
        ok = ok and same
    return {"deterministic": bool(ok and per), "configs": per}


def check_row_gate(row: dict) -> None:
    """Offline re-check of the unisolated-run gate on every row (the engine checks the records)."""
    iso = row.get("isolation") or {}
    if iso.get("effective") is not True or iso.get("waivers") != {} or iso.get("exceptions") != []:
        raise Stop(f"STOP: row {row.get('run_id')} of {row.get('node')} is not effectively isolated: {iso}")


# =============================================================================================== job helpers
def _sh(argv, *, cwd=None, env=None, timeout=3600) -> subprocess.CompletedProcess:
    return subprocess.run(list(map(str, argv)), cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def image_identity(spec: dict) -> dict:
    versions = Path("/opt/r1/VERSIONS.txt")
    if not versions.is_file():
        raise Stop("STOP: /opt/r1/VERSIONS.txt missing: not the pinned image")
    got = _sha_file(versions)
    if got != spec["image"]["versions_sha256"]:
        raise Stop(f"STOP: /opt/r1/VERSIONS.txt sha256 {got} differs from the v2 pin")
    for tool in (UV, ORCHESTRATOR_PYTHON):
        if not Path(tool).exists():
            raise Stop(f"STOP: {tool} missing from the image")
    return {"digest": spec["image"]["digest"], "versions_sha256": got}


def gpu_identity() -> dict:
    res = _sh(["nvidia-smi", "--query-gpu=name,uuid,driver_version,memory.total,compute_cap",
               "--format=csv,noheader"], timeout=120)
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi failed: {res.stderr.strip()[:200]}")
    gpus = [[x.strip() for x in line.split(",")] for line in res.stdout.strip().splitlines() if line.strip()]
    if len(gpus) != 1:
        raise Stop(f"STOP: one GPU per G.1b job, nvidia-smi lists {len(gpus)}")
    name, uuid, driver, memory, cap = gpus[0]
    if name != GPU_MODEL:
        raise Stop(f"STOP: landed on {name}, not {GPU_MODEL} (one GPU model per table)")
    return {"name": name, "uuid": uuid, "driver": driver, "memory_total": memory, "compute_capability": cap}


def host_identity() -> dict:
    import socket
    return {"hostname": socket.gethostname(), "fqdn": socket.getfqdn(), "uid": os.getuid(), "euid": os.geteuid(),
            "logical_cpus": os.cpu_count(), "affinity": sorted(os.sched_getaffinity(0)),
            "kernel": os.uname().release}


def clone_at(repo: str, commit: str, dest: Path) -> dict:
    res = _sh(["git", "clone", "--quiet", "--no-checkout", repo, str(dest)], timeout=1800)
    if res.returncode != 0:
        raise Stop(f"STOP: git clone {repo} failed: {res.stderr.strip()[:300]}")
    res = _sh(["git", "-C", str(dest), "checkout", "--quiet", "--detach", commit], timeout=600)
    head = _sh(["git", "-C", str(dest), "rev-parse", "HEAD"]).stdout.strip()
    if res.returncode != 0 or head != commit:
        raise Stop(f"STOP: {repo} cannot be checked out at {commit} (got {head!r})")
    dirty = _sh(["git", "-C", str(dest), "status", "--porcelain"]).stdout
    if dirty:
        raise Stop(f"STOP: {dest} is not clean at the pin")
    return {"repo": repo, "commit": head}


def build_env(spec: dict, name: str, dest: Path, freeze: Path) -> dict:
    """Build the census environment with uv from the committed freeze; its sorted freeze must equal the pin."""
    env_spec = spec["envs"][name]
    if _sha_file(freeze) != env_spec["sha256"]:
        raise Stop(f"STOP: staged freeze {freeze} differs from the pin")
    env = dict(os.environ, UV_PYTHON_INSTALL_DIR=UV_PYTHONS, UV_PYTHON_DOWNLOADS="never", UV_NO_CACHE="1")
    res = _sh([UV, "venv", "--python", env_spec["python"], str(dest)], env=env, timeout=900)
    if res.returncode != 0:
        raise Stop(f"STOP: uv venv --python {env_spec['python']} failed: {res.stderr.strip()[:300]}")
    python = dest / "bin" / "python"
    res = _sh([UV, "pip", "install", "--python", str(python), "--no-deps", "-r", str(freeze)], env=env, timeout=3600)
    if res.returncode != 0:
        raise Stop(f"STOP: installing the {name} freeze failed: {res.stderr.strip()[-500:]}")
    got = _sh([UV, "pip", "freeze", "--python", str(python)], env=env).stdout
    want = sorted(x for x in freeze.read_text().splitlines() if x.strip())
    have = sorted(x for x in got.splitlines() if x.strip())
    if have != want:
        diff = sorted(set(have) ^ set(want))
        raise Stop(f"STOP: the built {name} environment differs from the census freeze: {diff[:20]}")
    version = _sh([str(python), "-c", "import sys; print(sys.version.split()[0])"]).stdout.strip()
    if version != env_spec["python"]:
        raise Stop(f"STOP: {name} Python is {version}, not {env_spec['python']}")
    return {"name": name, "python": str(python), "python_version": version, "freeze_sha256": env_spec["sha256"],
            "packages": len(have)}


def delegated_cgroup() -> str:
    """The job's own cgroup v2 directory, which must be delegated (writable, with cgroup.kill): the runs'
    cgroups are created below it.  No delegation is a STOP (no no_cgroup waiver in G.1b)."""
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    v2 = [line.split("::", 1)[1] for line in lines if line.startswith("0::")]
    if len(v2) != 1:
        raise Stop(f"STOP: no unique cgroup v2 entry in /proc/self/cgroup: {lines}")
    for base in (Path("/sys/fs/cgroup"), Path("/sys/fs/cgroup/unified")):
        path = base / v2[0].lstrip("/")
        if (path / "cgroup.procs").is_file():
            break
    else:
        raise Stop(f"STOP: the job cgroup {v2[0]} is not visible under /sys/fs/cgroup")
    if not (path / "cgroup.kill").is_file():
        raise Stop(f"STOP: {path} has no cgroup.kill (kernel < 5.14)")
    if not (os.access(path, os.W_OK) and os.access(path / "cgroup.procs", os.W_OK)):
        raise Stop(f"STOP: the job cgroup {path} is not delegated to the job's uid")
    return str(path)


def _write_sums(root: Path, names) -> None:
    lines = []
    for name in names:
        path = root / name
        files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file()) if path.exists() else []
        lines += [f"{_sha_file(f)}  {f.relative_to(root)}" for f in files]
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def _rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.is_file() else []


def run_node_job(spec_path: Path, node_name: str, *, started: float | None = None) -> dict:
    """The container job for one node.  Writes out/, job_record.json, out.tar, SHA256SUMS; raises Stop on a STOP."""
    started = started or time.time()
    loaded = validate_spec(load_spec(spec_path), launch=True)
    spec = loaded["spec"]
    node = node_entry(spec, node_name)
    walltime = node_walltime(node, spec["layout"])
    deadline = started + walltime - 300
    scratch = Path(os.environ.get("_CONDOR_SCRATCH_DIR", "."))
    out = scratch / "out"
    out.mkdir(exist_ok=False)
    record = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "node": node_name,
              "spec_sha256": _sha_file(spec_path), "projection": loaded["projection"]["per_node"][node_name],
              "walltime_s": walltime, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
              "output_use": "ENGINEERING_ONLY G.1b noise floor (D21); no labels read; not a label table",
              "parts": [], "stop": None}
    record_path = scratch / "job_record.json"
    try:
        record["image"] = image_identity(spec)
        record["host"] = host_identity()
        if record["host"]["euid"] == 0:
            raise Stop("STOP: the job runs as root; isolated runs need a non-root uid (no root waiver)")
        record["gpu"] = gpu_identity()
        record["paper"] = clone_at(spec["paper"]["repo"], spec["paper"]["commit"], scratch / "paper")
        if (scratch / "paper" / "sweep2" / "g1b" / "g1b_lib.py").read_bytes() != Path(__file__).read_bytes():
            raise Stop("STOP: the staged g1b_lib.py differs from the pinned paper commit")
        record["harness"] = clone_at(spec["harness"]["repo"], spec["harness"]["commit"], scratch / "harness")
        freeze = scratch / "paper" / "sweep2" / "g1b" / spec["envs"][node["env"]]["freeze"]
        record["environment"] = build_env(spec, node["env"], scratch / "env", freeze)
        harness = scratch / "harness"
        node_dir = harness / node["node_dir"]
        data_root = scratch / "data"
        data_root.mkdir()
        setup_env = dict(os.environ, AR_TRACKG_DATA_ROOT=str(data_root),
                         PATH=f"{scratch / 'env' / 'bin'}:{os.environ.get('PATH', '')}", HF_HOME=str(scratch / "hf"))
        setup = _node_setup_command(harness / node["spec_path"])
        if setup:
            res = subprocess.run(setup, shell=True, cwd=node_dir, env=setup_env, capture_output=True, text=True,
                                 timeout=7200)
            (out / "setup.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
            if res.returncode != 0:
                raise Stop(f"STOP: {node_name} setup_command failed (rc {res.returncode}); see out/setup.log")
        record["data_root"] = str(data_root)
        cgroup = delegated_cgroup()
        record["cgroup_parent"] = cgroup
        memory = f"HTCondor request_memory={spec['layout']['request_memory_mb']} MB (job cgroup {cgroup})"
        engine_env = dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1")
        for part in PARTS:
            chunk = chunk_file(spec, node, part, interpreter=str(scratch / "env" / "bin" / "python"),
                               cgroup_parent=cgroup, deadline=deadline, memory_limit=memory)
            chunk_path = out / f"chunk_{part[0]}.json"
            chunk_path.write_text(json.dumps(chunk, indent=1) + "\n")
            res = subprocess.run([str(scratch / "env" / "bin" / "python"), "-m", "autoresearch.trackg.noise_floor",
                                  "--chunk", str(chunk_path), "--harness-root", str(harness),
                                  "--out", str(out / part[0])], cwd=harness, env=engine_env,
                                 capture_output=True, text=True, timeout=max(60, int(deadline - time.time()) + 600))
            (out / f"engine_{part[0]}.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
            chunk_record = json.loads((out / part[0] / "chunk_record.json").read_text()) \
                if (out / part[0] / "chunk_record.json").is_file() else {"stop": f"engine rc {res.returncode}"}
            record["parts"].append({"part": part[0], "rc": res.returncode,
                                    **{k: chunk_record.get(k) for k in ("expected_runs", "written_rows",
                                                                        "successful_rows", "stop")}})
            if res.returncode != 0 or chunk_record.get("stop"):
                raise Stop(f"STOP: {node_name} part {part[0]}: {chunk_record.get('stop') or 'engine rc ' + str(res.returncode)}")
            if part[0] == "default":
                det = determinism_check(_rows(out / "default" / "runs.jsonl"))
                record["determinism"] = det
                if not det["deterministic"]:
                    raise Stop(f"STOP: {node_name} fixed-seed determinism failed: no seeded runs; the node does not "
                               "qualify (determinism)")
        rows = [r for p in PARTS for r in _rows(out / p[0] / "runs.jsonl")]
        for row in rows:
            check_row_gate(row)
        with (out / "runs.jsonl").open("x") as fh:
            fh.writelines(json.dumps(r, sort_keys=True) + "\n" for r in rows)
        shutil.copy2(out / "default" / "edits.json", out / "edits.json")
        record["runs"] = {"expected": runs_per_node(node["n_edits"]), "written": len(rows),
                          "successful": sum(1 for r in rows if r["success"])}
        if record["runs"]["written"] != record["runs"]["expected"]:
            raise Stop(f"STOP: {node_name} wrote {len(rows)} rows, expected {record['runs']['expected']}")
    except Stop as exc:
        record["stop"] = str(exc)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        record["stop"] = f"STOP: unexpected {type(exc).__name__}: {exc}"
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record_path.write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=scratch, check=False)
    _write_sums(scratch, ("out.tar", "job_record.json"))
    if record["stop"]:
        raise Stop(record["stop"])
    return record


def _node_setup_command(spec_yaml: Path) -> str | None:
    """The node's setup_command, read without a YAML library (one single-quoted or double-quoted line)."""
    for line in spec_yaml.read_text().splitlines():
        m = re.match(r"^setup_command:\s*(['\"])(.*)\1\s*$", line)
        if m:
            return m.group(2)
        if line.startswith("setup_command:"):
            raise Stop(f"STOP: {spec_yaml} setup_command is not a single quoted line")
    return None


# =============================================================================================== offline
def summarise(run_dir: Path, spec: dict, paper_root: Path) -> dict:
    """Exact coverage per node, the gate on every row, determinism, then the pinned e1_report rule with the
    double-entry check against d21_qualify (rule drift is a STOP)."""
    run_dir = Path(run_dir)
    rows = _rows(run_dir / "runs.jsonl")
    edits = json.loads((run_dir / "edits.json").read_text())
    nodes = [n["node"] for n in spec["nodes"]]
    n_edits = spec["edit_count"]["n_edits_per_node"]
    want = {(n, r["config"], r["condition"], r["train_seed"], r["split_seed"]) for n in nodes
            for part in PARTS for r in expected_runs(n_edits, part[1], part[2])}
    seen = {}
    for row in rows:
        check_row_gate(row)
        key = (row["node"], row["config"], row["condition"], row["train_seed"], row["split_seed"])
        if key in seen:
            raise Stop(f"STOP: duplicate run {key}")
        seen[key] = row
    missing, extra = want - set(seen), set(seen) - want
    if missing or extra:
        raise Stop(f"STOP: coverage is not exact: {len(missing)} missing, {len(extra)} extra")
    sys.path.insert(0, str(paper_root))
    from r1.noise import e1_report  # noqa: PLC0415
    for got, declared in ((e1_report.MIN_EDITS, D21_MIN_MATERIAL_EDITS), (e1_report.QUALIFY_P, D21_MIN_MEAN_P_WRONG),
                          (e1_report.MIN_EFFECT, D21_MIN_EFFECT)):
        if got != declared:
            raise Stop("STOP: r1.noise.e1_report no longer carries the D21 constants")
    pinned = e1_report.summarise(run_dir)
    verdicts = {}
    for node in nodes:
        det = determinism_check([r for r in rows if r["node"] == node])
        if not det["deterministic"]:
            verdicts[node] = {"qualifies_D21": False, "reason": "fixed-seed determinism failed", "determinism": det}
            continue
        info = pinned["nodes"].get(node, {})
        ours = d21_qualify([{"material": bool(e.get("material")), "p_wrong": e.get("p_model", float("nan"))}
                            for e in info.get("edits", [])], info.get("sigma_joint", float("nan")), SEEDS_PER_CONDITION)
        if bool(info.get("proposal", {}).get("qualifies_D21")) != ours["qualifies_D21"]:
            raise Stop(f"STOP: D21 rule drift on {node}")
        verdicts[node] = dict(ours, sigma_train=info.get("sigma_train"), sigma_split=info.get("sigma_split"),
                              median_wall_seconds=info.get("median_wall_seconds"), determinism=det)
    summary = {"schema": SUMMARY_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"], "gpu_model": GPU_MODEL,
               "split_policy": SPLIT_POLICY, "edits_per_node": n_edits, "verdicts": verdicts,
               "screening_funnel": {"measured": len(nodes),
                                    "qualified": sum(1 for v in verdicts.values() if v["qualifies_D21"]),
                                    "failed_determinism": sum(1 for v in verdicts.values()
                                                              if v.get("reason") == "fixed-seed determinism failed")}}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    return summary


def seal(job_output: Path, run_id: str, node: str) -> dict:
    """Verify the transferred SHA256SUMS and job record, then copy to /ceph/.../<run_id>/<node>/ (no overwrite)."""
    src = Path(job_output).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("label") != ENGINEERING_ONLY or record.get("run_id") != run_id or record.get("node") != node:
        raise Stop("STOP: the job record does not match the run/node or is not ENGINEERING_ONLY")
    if (record.get("image") or {}).get("digest") != IMAGE_DIGEST or (record.get("gpu") or {}).get("name") != GPU_MODEL:
        raise Stop("STOP: the job record lacks the pinned image or the H200 identity")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
        raise Stop("STOP: transferred SHA256SUMS verification failed")
    for name in (run_id, node):
        if not SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    target = SEALED_ROOT / run_id / node
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "g1b_run.log"):
        if (src / name).exists():
            shutil.copy2(src / name, target / name)
    receipt = {"schema": "g1b_h200_seal_receipt/1", "run_id": run_id, "node": node, "sealed_path": str(target),
               "stop": record.get("stop"), "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    j = sub.add_parser("job"); j.add_argument("spec"); j.add_argument("--node", required=True)
    s = sub.add_parser("summarise"); s.add_argument("run_dir"); s.add_argument("spec")
    s.add_argument("--paper-root", required=True)
    z = sub.add_parser("seal"); z.add_argument("job_output"); z.add_argument("--run-id", required=True)
    z.add_argument("--node", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            loaded = validate_spec(load_spec(Path(a.spec)), launch=a.launch)
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"]}, indent=1))
        elif a.cmd == "job":
            rec = run_node_job(Path(a.spec), a.node)
            print(json.dumps({"ok": True, "node": a.node, "runs": rec["runs"]}, indent=1))
        elif a.cmd == "summarise":
            print(json.dumps(summarise(Path(a.run_dir), load_spec(Path(a.spec)), Path(a.paper_root)), indent=1,
                             default=str))
        else:
            print(json.dumps(seal(Path(a.job_output), a.run_id, a.node), indent=1))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
