#!/usr/bin/env python3
"""S2-C3 L40S deployment check — replay of the 12 recorded B2 thinking-off roots (ENGINEERING, no evidence).

One job == one B2 node (3 nodes x 4 recorded instance seeds 9011-9014). The job validates a replay spec
(`s2_c3_replay/v1`, all pins fixed), verifies the pinned B2 root inputs against their SHA256SUMS, **verifies every
declared input item-by-item** (`s2_c3_declared_inputs.json`; file shas, paper git blobs, harness node trees and the
OpenML cache tree are checked), prepares the 4 `job.json` copies rewriting ONLY `out` (sandbox) and `base_url` (the
owned local server), proves the B2 configuration `binding` still recomputes exactly as the B2 code computes it,
prepares a paper checkout at the pinned B2 commit `8709dce7` (clean; the authorization checkout) plus a sandbox
worktree where the reviewed label patch **and the reviewed TASL-only preflight shim** are applied, pre-flights the B2
authorization gates twice (unshimmed: exactly the reviewed TASL refusal set; shimmed: all five gates must pass,
including the Stage A pass-set/`_authorized_candidate` gate that the B2 root campaign calls on every root), and only
then starts ONE owned llama-server (the author-accepted 32k layout: 12,203 s walltime / 42,460,977 kB disk / 32,000 MB
memory) and runs the 4 root campaigns sequentially. The campaign is executed as `r1.exam.campaign` with **all three**
patched sources (campaign, runtime, `r1.scripts.exam_runner`) shadow-executed in the module namespace, so the
authorization checkout stays byte-identical to the pinned commit the B2 authorization binds. Every refusal is a STOP:
no silent bypass, no retry. See `S2_C3_DRIVER.md` for the declared-inputs table, the shim scope and the run-time
network disclosure.

The reviewed execution-label patch (`s2_c3_label_patch.diff`) changes only the campaign `execution_label` to
ENGINEERING_ONLY and adds `replay_marker`; the reviewed shim (`s2_c3_driver_shim.diff`) only relocates the sha-bound
Stage A inputs (both the `author_gate` digest reads and the `stage_a_pass_set` read the B2 root campaign reaches) and
replaces the two TASL host checks in replay mode while keeping the production DRYRUN-env refusal and the 100 GB disk
floor. Neither changes trial/audit logic; all scopes are checked here. Raw labels are never read; no B.2 audit runs
and audit seeds 7001-7010 are refused.

Run-time network (identity pinned, no unpinned data, no TASL access): the job clones the paper repo at `8709dce7`
from GitHub, clones the harness at `a3fedbb` from GitHub, and fetches the 19.6 GB GGUF from HuggingFace, verifying the
commit / sha256 of each. The three jobs therefore need outbound GitHub/HuggingFace access and 3 x 19.6 GB model egress.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402

SCHEMA = "s2_c3_replay/v1"
RECORD_SCHEMA = "s2_c3_replay_record/v1"
SEAL_RECEIPT_SCHEMA = "s2_c3_seal_receipt/1"
KIND = "replay"

# --- fixed pins (the pre-declared protocol; nothing here is spec-selectable) -------------------------------
PAPER_COMMIT = "8709dce792d45bbb5c05d9f7d239e19454efbb15"
HARNESS_COMMIT = "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"
IMAGE_DIGEST = ("ghcr.io/dowlingwong/r1-htc-gpu@sha256:"
                "69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296")
IMAGE_LLAMA_SERVER_SHA256 = "f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0"
IMAGE_MARKERS = {"image": "r1-htc-gpu", "build_utc": "2026-11-14T23:10:24Z",
                 "llama_server_sha256": IMAGE_LLAMA_SERVER_SHA256,
                 "llama_cpp_commit": "620d2225cc436ab0b001e3200e590e3b286ef9ab"}
GGUF_SHA256 = "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75"
GGUF_SIZE = 19598489952
GGUF_URL = ("https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/"
            "619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf")
MODEL_ALIAS = "gemma4_31b"
MODEL_PROVENANCE = {"registry_doc": "docs/r1/reports/exam_phase2_20261026/gemma4_31b.json",
                    "registry_sha256": "a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61",
                    "revision": "619aca7589c72be65dd968de8602ad23d68b5c14",
                    "file": "google_gemma-4-31B-it-Q4_K_M.gguf",
                    "source_label": "bartowski imatrix Q4_K_M"}
SERVER = {"binary": "/opt/r1/llama/bin/llama-server", "ctx": 32768, "n_gpu_layers": 999, "port": 18130,
          "expected_build": "0.7.0-dev (build 11669, commit 620d2225c)",
          "extra_args": ["--jinja", "--chat-template-kwargs", "{\"enable_thinking\": false}",
                         "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--no-webui"]}
NODES = ("digits_mlp", "openml_credit_approval", "openml_ionosphere")
SEEDS = (9011, 9012, 9013, 9014)
AUDIT_SEEDS = tuple(range(9201, 9211))
RESERVED_B2_AUDIT_SEEDS = tuple(range(7001, 7011))
ROOTS = tuple(f"{node}__s{seed}" for node in NODES for seed in SEEDS)
ROOT_COUNT = 12
BINDING = "c502a9aa5e23cb190e712505b8900253fb417cdb1c143b525b3b4b1b8b45290b"
LABEL = "ENGINEERING_ONLY"
REPLAY_MARKER = "s2_c3_replay/v1"
OUTPUT_USE = ("ENGINEERING L40S deployment check; never a label table, training or selection; no B.2 audit; "
              "audit seeds 7001-7010 untouched")
CRITERIA_PATH = "docs/r1/reports/sweep2_20261116/S2_C3_CRITERIA.md"
CRITERIA_SHA256 = "63bd0a9b3c52501d93b91549f27199a9b88d7d67a0fd5498df68a0c341f4bcdc"
INPUTS_DIR = "docs/r1/reports/sweep2_20261116/c3_replay_inputs"
INPUTS_SHA256SUMS_SHA256 = "6224b75a4d4aec9ac2f289cf913e19cbb814263a9e7d0e7b381122695d0cadf6"
PATCH_PATH = "sweep2/s2_c3_label_patch.diff"
PATCH_SHA256 = "fd0234c9579b293cdb7db259303e1ef86dffdd6a7e8ed3360f04227badddf741"
PATCH_TARGET = "r1/exam/campaign.py"
# --- R1-S2C3-DRIVER: the reviewed TASL-only preflight shim and the declared-inputs audit ----------------------
SHIM_PATH = "sweep2/s2_c3_driver_shim.diff"
SHIM_SHA256 = "defac2364907d28c43aa132b08682080a4b6b52ccad4c0e058505edf1a9eaa92"
SHIM_TARGETS = ("r1/exam/runtime.py", "r1/exam/campaign.py", "r1/scripts/exam_runner.py")
PATCHED_SOURCE_SHA256 = {"r1/exam/runtime.py": "0cc6705e0414efd23a493f7f51d6e3ebd005e506b5d3bebfa8bb40b6a4cbf5d3",
                         "r1/exam/campaign.py": "d9d8b5a0709d94e578d7a7f5880f8f27aa5a66ce2f6622de952c253639710c0c",
                         "r1/scripts/exam_runner.py": "9acc121c0ff90902c1df15687b11cbe8a51d0afb2fd0d86d427fc52ad9169d85"}
DECLARED_PATH = "sweep2/s2_c3_declared_inputs.json"
DECLARED_SHA256 = "7c40fdf5ddaf435b48dffb063e85f878f1ea36d43f49a5fe094768d8ad201893"
DECLARED_SCHEMA = "s2_c3_declared_inputs/v1"
DECLARED_STAGED = "S2C3_IN_DECLARED.json"
REPLAY_DECLARED_ENV = "R1_S2C3_DECLARED_INPUTS"
REPLAY_ROOT_ENV = "R1_S2C3_DECLARED_ROOT"
REPLAY_SANDBOX_ENV = "R1_S2C3_SANDBOX_ROOT"
OPENML_CACHE_REL = "experiments/r1/pilot/L8_20261009T152916Z/nodes"
OPENML_NODES = ("openml_credit_approval", "openml_ionosphere")
# --- R1-SWEEP2-LAYOUT: the author-accepted 32k sweep-2 layout (same authority commit; measured by the S2-C2 32k
# smoke, 2026-11-16).  The C3 replay uses the accepted numbers, not a C3-specific guess; a different value is a STOP.
WALLTIME_S = 8735
REQUEST_DISK_KB = 42460970
REQUEST_MEMORY_MB = 32000
# The exact pre-declared refusal set the unshimmed TASL walk must report -- no more, no fewer (a subset is not
# accepted, so a shim that starts passing a gate that was expected to refuse is also a STOP).  The declared OpenML
# cache is installed into the harness clone before the preflight, so ``openml_data_cache`` is NOT a TASL refusal
# (the cache path/identity is checked by the declared-inputs audit instead; the first H200 run exposed this).
TASL_BLOCKER_GATES = frozenset({"verify_b1_worker_input", "host_check", "require_worker_host",
                                "authorized_candidate", "out_under_work_dir",
                                "authorization_input:stage_a_table",
                                "authorization_input:stage_a_amendment_table"})
TASL_BLOCKER_GATES_OPENML = TASL_BLOCKER_GATES | {"openml_data_cache"}
# The gate probe must exercise exactly these five campaign gates; a probe that reports a different set is a STOP
# (this is what makes the "pre-flight covers the campaign's authorization gates" statement a checked property).
PROBE_GATES = frozenset({"verify_b1_worker_input", "host_check", "require_worker_host", "harness_binding",
                         "authorized_candidate"})

B2_AUTHORIZATION_NOTE = "docs/r1/authorizations/trackx_b2_20261115.md"
B2_GPU_HOURS_OFF = 0.5049170030487908
B2_CONFIG_REL = "r1/scripts/configs/exam_b2_v2.json"

SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")

# Staged, flattened replay-input names (HTCondor transfer-input files must stay flat).
STAGED_SHA256SUMS = "S2C3_IN_SHA256SUMS"
STAGED_JOB = "S2C3_IN_{root}_job.json"
STAGED_MANIFEST = "S2C3_IN_{root}_campaign_manifest.json"


class Stop(RuntimeError):
    pass


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(Path(path).read_bytes())


def _get(d, *keys):
    cur = d
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            raise Stop(f"STOP: spec missing {'.'.join(keys)}")
        cur = cur[key]
    return cur


def _text(value, name, pattern=None):
    if not isinstance(value, str) or not value or CONTROL.search(value):
        raise Stop(f"STOP: {name} must be a nonempty single-line string")
    if pattern is not None and not pattern.fullmatch(value):
        raise Stop(f"STOP: {name} has the wrong form")
    return value


def _exact(value, expected, name):
    if value != expected:
        raise Stop(f"STOP: {name} must be {expected!r}; got {value!r}")
    return value


# ------------------------------------------------------------------ spec
def load_spec(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise Stop(f"STOP: replay spec is not readable JSON: {exc}") from None
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise Stop(f"STOP: replay spec schema must be {SCHEMA}")
    return data


def _server_thinking(server: dict) -> bool:
    """The `enable_thinking` value the pinned server argv actually sends (must be False for this exam)."""
    extra = server.get("extra_args") or []
    if "--chat-template-kwargs" not in extra or extra.index("--chat-template-kwargs") + 1 >= len(extra):
        raise Stop("STOP: --chat-template-kwargs is required")
    try:
        payload = json.loads(extra[extra.index("--chat-template-kwargs") + 1])
    except (TypeError, ValueError) as exc:
        raise Stop(f"STOP: --chat-template-kwargs is not valid JSON: {exc}") from None
    return bool((payload or {}).get("enable_thinking", True))


def _check_server(server: dict) -> None:
    _exact(_text(_get(server, "binary"), "server.binary"), SERVER["binary"], "server.binary")
    _exact(_get(server, "ctx"), SERVER["ctx"], "server.ctx (the 32k exam setting)")
    _exact(_get(server, "n_gpu_layers"), SERVER["n_gpu_layers"], "server.n_gpu_layers")
    port = _get(server, "port")
    if type(port) is not int or not 1024 <= port <= 65535:
        raise Stop("STOP: server.port must be an integer in [1024, 65535]")
    _exact(_text(_get(server, "expected_build"), "server.expected_build"),
           SERVER["expected_build"], "server.expected_build")
    extra = _get(server, "extra_args")
    if not isinstance(extra, list) or not all(isinstance(a, str) and not CONTROL.search(a) for a in extra):
        raise Stop("STOP: server.extra_args must be a list of single-line strings")
    if "$" in " ".join(extra):
        raise Stop("STOP: '$' in server.extra_args is refused")
    for flag, value in (("--jinja", None), ("--cache-type-k", "q8_0"), ("--cache-type-v", "q8_0"),
                        ("--chat-template-kwargs", None)):
        if flag not in extra:
            raise Stop(f"STOP: the exam server setting requires {flag} in server.extra_args")
        if value is not None and extra[extra.index(flag) + 1] != value:
            raise Stop(f"STOP: {flag} must be {value}")
    if _server_thinking(server) is not False:
        raise Stop("STOP: --chat-template-kwargs must disable thinking (enable_thinking: false)")
    managed = lib.MANAGED_FLAGS & set(extra)
    if managed:
        raise Stop(f"STOP: server.extra_args may not repeat managed flags {sorted(managed)}")


def _check_seed_lists(block: dict) -> None:
    seeds = block.get("seeds")
    audits = block.get("audit_seeds")
    flat = [seed for seed in (seeds if isinstance(seeds, list) else [])
            + (audits if isinstance(audits, list) else []) if isinstance(seed, int)]
    if any(seed in RESERVED_B2_AUDIT_SEEDS for seed in flat):
        raise Stop("STOP: reserved B.2 audit seeds 7001-7010 may not appear in a replay (no B.2 audit)")
    if any(seed not in AUDIT_SEEDS for seed in audits if isinstance(seed, int)):
        raise Stop("STOP: an audit seed outside 9201-9210 is refused")
    if seeds != list(SEEDS):
        raise Stop(f"STOP: replay_inputs.seeds must be exactly {list(SEEDS)} (the recorded B2 instance seeds)")
    if audits != list(AUDIT_SEEDS):
        raise Stop(f"STOP: replay_inputs.audit_seeds must be exactly {list(AUDIT_SEEDS)} "
                   "(the B2 final-audit seeds; no B.2 audit)")


def validate_spec(spec: dict) -> dict:
    if not isinstance(spec, dict) or spec.get("schema") != SCHEMA:
        raise Stop(f"STOP: replay spec schema must be {SCHEMA}")
    run_id = _text(_get(spec, "run_id"), "run_id", SAFE)
    chunk_id = _text(_get(spec, "chunk_id"), "chunk_id", SAFE)
    node = _text(_get(spec, "node"), "node", SAFE)
    if node not in NODES:
        raise Stop(f"STOP: node must be one of {list(NODES)}")
    if chunk_id != node:
        raise Stop("STOP: chunk_id must equal the node (one replay job per node)")
    kind = spec.get("kind", KIND)
    if kind != KIND:
        raise Stop(f"STOP: kind must be {KIND}")
    for key in ("dryrun", "evidence", "b2_audits", "audit_b2"):
        if key in spec:
            raise Stop(f"STOP: a replay spec may not carry {key!r}")

    image = _get(spec, "image")
    _exact(_text(_get(image, "digest"), "image.digest"), IMAGE_DIGEST,
           "image.digest (the frozen v1 gpu digest 69b06b35...)")
    _exact(_get(image, "versions_markers"), IMAGE_MARKERS, "image.versions_markers")
    _exact(_text(_get(image, "llama_server_sha256"), "image.llama_server_sha256", SHA),
           IMAGE_LLAMA_SERVER_SHA256, "image.llama_server_sha256")

    paper = _get(spec, "paper")
    _text(_get(paper, "repo"), "paper.repo")
    _exact(_text(_get(paper, "commit"), "paper.commit", COMMIT), PAPER_COMMIT,
           "paper.commit (the B2 run HEAD)")
    _exact(_text(_get(paper, "b2_authorization_note"), "paper.b2_authorization_note"),
           B2_AUTHORIZATION_NOTE, "paper.b2_authorization_note")

    harness = _get(spec, "harness")
    _text(_get(harness, "repo"), "harness.repo")
    _exact(_text(_get(harness, "commit"), "harness.commit", COMMIT), HARNESS_COMMIT,
           "harness.commit (the B2 harness pin a3fedbb...)")

    model = _get(spec, "model")
    _exact(_text(_get(model, "url"), "model.url"), GGUF_URL, "model.url (the pinned GGUF URL)")
    _exact(_text(_get(model, "sha256"), "model.sha256", SHA), GGUF_SHA256, "model.sha256 (the pick GGUF)")
    _exact(_get(model, "size"), GGUF_SIZE, "model.size")
    _exact(_text(_get(model, "alias"), "model.alias", SAFE), MODEL_ALIAS, "model.alias")
    _exact(_get(model, "provenance"), MODEL_PROVENANCE, "model.provenance")

    _check_server(_get(spec, "server"))

    replay = _get(spec, "replay_inputs")
    _exact(_text(_get(replay, "dir"), "replay_inputs.dir"), INPUTS_DIR, "replay_inputs.dir")
    _exact(_text(_get(replay, "sha256sums_sha256"), "replay_inputs.sha256sums_sha256", SHA),
           INPUTS_SHA256SUMS_SHA256, "replay_inputs.sha256sums_sha256 (the pinned inputs SHA256SUMS)")
    _exact(replay.get("nodes"), list(NODES), "replay_inputs.nodes")
    _exact(replay.get("roots"), list(ROOTS), f"replay_inputs.roots (the {ROOT_COUNT} recorded B2 off roots)")
    _exact(_text(_get(replay, "binding"), "replay_inputs.binding", SHA), BINDING,
           "replay_inputs.binding (the B2 configuration binding)")
    _check_seed_lists(replay)

    label = _get(spec, "label")
    if not isinstance(label, dict):
        raise Stop("STOP: label must be an object")
    _exact(_text(_get(label, "execution_label"), "label.execution_label"), LABEL,
           "label.execution_label (an ENGINEERING deployment check; EVIDENCE/DRYRUN refused)")
    _exact(_text(_get(label, "replay_marker"), "label.replay_marker"), REPLAY_MARKER, "label.replay_marker")
    if set(label) != {"execution_label", "replay_marker"}:
        raise Stop("STOP: label may carry only execution_label and replay_marker")

    patch = _get(spec, "label_patch")
    _exact(_text(_get(patch, "path"), "label_patch.path"), PATCH_PATH, "label_patch.path")
    _exact(_text(_get(patch, "sha256"), "label_patch.sha256", SHA), PATCH_SHA256, "label_patch.sha256")
    _exact(_text(_get(patch, "target"), "label_patch.target"), PATCH_TARGET, "label_patch.target")

    shim = _get(spec, "driver_shim")
    _exact(_text(_get(shim, "path"), "driver_shim.path"), SHIM_PATH, "driver_shim.path")
    _exact(_text(_get(shim, "sha256"), "driver_shim.sha256", SHA), SHIM_SHA256, "driver_shim.sha256")
    _exact(shim.get("targets"), list(SHIM_TARGETS), "driver_shim.targets")
    if set(shim) != {"path", "sha256", "targets"}:
        raise Stop("STOP: driver_shim may carry only path, sha256 and targets")

    declared = _get(spec, "declared_inputs")
    _exact(_text(_get(declared, "path"), "declared_inputs.path"), DECLARED_PATH, "declared_inputs.path")
    _exact(_text(_get(declared, "sha256"), "declared_inputs.sha256", SHA), DECLARED_SHA256,
           "declared_inputs.sha256")
    _exact(_text(_get(declared, "staged"), "declared_inputs.staged"), DECLARED_STAGED, "declared_inputs.staged")
    if set(declared) != {"path", "sha256", "staged"}:
        raise Stop("STOP: declared_inputs may carry only path, sha256 and staged")
    if "b2_audit" in spec or "b2_audits" in spec:
        raise Stop("STOP: no B.2 audit may be attached to a replay spec")

    criteria = _get(spec, "criteria")
    _exact(_text(_get(criteria, "path"), "criteria.path"), CRITERIA_PATH, "criteria.path")
    _exact(_text(_get(criteria, "sha256"), "criteria.sha256", SHA), CRITERIA_SHA256,
           "criteria.sha256 (the pre-declared criteria pin)")

    req = _get(spec, "requirements")
    _exact(_get(req, "gpu_min_memory_mb"), lib.GPU_MIN_MEMORY_MB, "requirements.gpu_min_memory_mb")
    _exact(float(_get(req, "gpu_min_capability")), lib.GPU_MIN_CAPABILITY, "requirements.gpu_min_capability")
    _exact(_get(req, "arch"), "X86_64", "requirements.arch")
    _exact(_get(req, "opsys"), "LINUX", "requirements.opsys")
    _exact(_get(req, "min_cpus"), lib.MIN_CPUS, "requirements.min_cpus")
    for key in ("cloud_site", "gpu_device_name", "cpu_family", "cpu_model_number", "cpu_model_contains", "machine_regex"):
        if key in req:
            raise Stop(f"STOP: requirements.{key} is no longer pinned (any GPU meeting VRAM/CC; site/CPU recorded)")
    if "requires_etp_ceph" in req:
        raise Stop("STOP: NEMO2 slots do not advertise ProvidesEtpCeph; outputs transfer to the submit host")

    # R1-SWEEP2-LAYOUT: the author-accepted 32k layout is pinned exactly (not a C3-specific guess; the S2-C2 32k
    # measurement is the basis).  A different walltime/disk/memory is a STOP, never silently rendered.
    _exact(spec.get("walltime_s"), WALLTIME_S, "walltime_s (author-accepted 32k layout)")
    _exact(spec.get("request_disk_kb"), REQUEST_DISK_KB, "request_disk_kb (author-accepted 32k layout)")
    _exact(spec.get("request_memory_mb"), REQUEST_MEMORY_MB, "request_memory_mb (author-accepted 32k layout)")
    return {"run_id": run_id, "chunk_id": chunk_id, "node": node, "spec": spec}


# ------------------------------------------------------------------ pinned inputs / job.json rewrite
def parse_sha256sums(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not SHA.fullmatch(parts[0]):
            raise Stop(f"STOP: malformed SHA256SUMS line {line!r}")
        name = parts[1].lstrip("*")
        if name in entries:
            raise Stop(f"STOP: duplicate SHA256SUMS entry {name!r}")
        entries[name] = parts[0]
    return entries


def expected_input_names() -> dict[str, str]:
    """The exact 24 pinned input files (12 roots x job.json + campaign_manifest.json)."""
    names = {}
    for root in ROOTS:
        names[f"{root}/job.json"] = f"{root}/job.json"
        names[f"{root}/campaign_manifest.json"] = f"{root}/campaign_manifest.json"
    return names


def verify_pinned_inputs(cwd: Path, spec: dict) -> dict:
    """Verify the staged, flattened replay inputs against the pinned SHA256SUMS (before any rewrite)."""
    cwd = Path(cwd)
    sums_path = cwd / STAGED_SHA256SUMS
    if not sums_path.is_file():
        raise Stop(f"STOP: staged pinned inputs SHA256SUMS missing ({STAGED_SHA256SUMS})")
    sums = parse_sha256sums(sums_path.read_text())
    pin = spec["replay_inputs"]["sha256sums_sha256"]
    got = _sha_file(sums_path)
    if got != pin:
        raise Stop(f"STOP: pinned inputs SHA256SUMS sha256 {got} != spec pin {pin}")
    expected = expected_input_names()
    if set(sums) != set(expected):
        missing = sorted(set(expected) - set(sums))
        extra = sorted(set(sums) - set(expected))
        raise Stop(f"STOP: pinned inputs are not the 12 recorded B2 roots (missing={missing[:4]} extra={extra[:4]})")
    jobs: dict[str, dict] = {}
    for root in ROOTS:
        for kind, staged in (("job.json", STAGED_JOB.format(root=root)),
                             ("campaign_manifest.json", STAGED_MANIFEST.format(root=root))):
            path = cwd / staged
            if not path.is_file():
                raise Stop(f"STOP: staged replay input {staged} missing")
            if _sha_file(path) != sums[f"{root}/{kind}"]:
                raise Stop(f"STOP: staged replay input {root}/{kind} does not match the pinned SHA256SUMS")
        job = json.loads((cwd / STAGED_JOB.format(root=root)).read_text())
        jobs[root] = job
        _check_recorded_job(root, job, spec)
    _check_job_set_consistency(jobs)
    return {"sha256sums_sha256": got, "files": len(expected), "jobs": jobs}


def _check_recorded_job(root: str, job: dict, spec: dict) -> None:
    node, seed = root.rsplit("__s", 1)
    expected = {"phase": "b2", "mode": "off", "dryrun": False, "W": 20, "workers": 20, "llm_call_cap": 80,
                "harness_commit": HARNESS_COMMIT, "authorization_checkout_head": PAPER_COMMIT,
                "audit_seeds": list(AUDIT_SEEDS), "binding": BINDING, "node": node, "seed": int(seed),
                "value_grids": "r1/exam/value_grids.yaml", "proposal_schema": "manager_proposal/v1"}
    for key, want in expected.items():
        if job.get(key) != want:
            raise Stop(f"STOP: recorded {root} job.json field {key} is {job.get(key)!r}, expected {want!r}")
    if node not in NODES or int(seed) not in SEEDS:
        raise Stop(f"STOP: replay root {root} is not one of the 12 recorded B2 off roots")
    for key in ("out", "base_url"):
        if not isinstance(job.get(key), str) or not job[key]:
            raise Stop(f"STOP: recorded {root} job.json lacks {key!r}")
    candidate = job.get("candidate") or {}
    if candidate.get("id") != MODEL_ALIAS:
        raise Stop(f"STOP: recorded {root} candidate is not the pick {MODEL_ALIAS}")
    if ((candidate.get("quant_source") or {}).get("sha256")) != GGUF_SHA256:
        raise Stop(f"STOP: recorded {root} candidate GGUF sha256 is not the pinned pick GGUF")
    if ((candidate.get("thinking_policy") or {}).get("mode")) != "off":
        raise Stop(f"STOP: recorded {root} candidate is not thinking-off")
    cfg = job.get("authority_config")
    if not isinstance(cfg, dict):
        raise Stop(f"STOP: recorded {root} lacks authority_config")
    if cfg.get("rule_sha256") != "53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad":
        raise Stop(f"STOP: recorded {root} authority rule sha256 differs from the frozen x5_rule/v2 rule")
    if cfg.get("harness_commit") != HARNESS_COMMIT or cfg.get("host") != "TASL-7":
        raise Stop(f"STOP: recorded {root} authority host/harness pins differ from the B2 evidence run")
    if list(cfg.get("nodes") or []) != list(NODES):
        raise Stop(f"STOP: recorded {root} authority nodes differ from the replay node set")


def _check_job_set_consistency(jobs: dict[str, dict]) -> None:
    bindings = {job.get("binding") for job in jobs.values()}
    if bindings != {BINDING}:
        raise Stop("STOP: the 12 recorded roots do not share the B2 configuration binding")
    configs = {json.dumps(job.get("authority_config"), sort_keys=True) for job in jobs.values()}
    if len(configs) != 1:
        raise Stop("STOP: the 12 recorded roots do not share one authority configuration")


# ------------------------------------------------------------------ declared inputs (R1-S2C3-DRIVER)
def _tree_sha(entries) -> str:
    """Digest of a tree identity: sha256 over sorted '<blob sha256>  <relative path>' lines."""
    return _sha_bytes("\n".join(f"{digest}  {rel}" for rel, digest in sorted(entries)).encode())


def load_declared_inputs(cwd: Path, spec: dict) -> dict:
    """Load the staged, sha-pinned declared-inputs manifest (R1-S2C3-DRIVER: every input itemized)."""
    cwd = Path(cwd)
    path = cwd / DECLARED_STAGED
    if not path.is_file():
        raise Stop(f"STOP: staged declared-inputs manifest {DECLARED_STAGED} missing")
    got = _sha_file(path)
    pin = spec["declared_inputs"]["sha256"]
    if got != pin:
        raise Stop(f"STOP: declared-inputs manifest sha256 {got} != spec pin {pin}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise Stop(f"STOP: declared-inputs manifest is not JSON: {exc}") from None
    if not isinstance(data, dict) or data.get("schema") != DECLARED_SCHEMA:
        raise Stop(f"STOP: declared-inputs manifest schema must be {DECLARED_SCHEMA}")
    if data.get("label") != LABEL or data.get("replay_marker") != REPLAY_MARKER:
        raise Stop("STOP: declared-inputs manifest is not the ENGINEERING_ONLY replay manifest")
    if data.get("paper_commit") != PAPER_COMMIT or data.get("harness_commit") != HARNESS_COMMIT:
        raise Stop("STOP: declared-inputs manifest pins a different paper/harness commit")
    if not isinstance(data.get("stage_a_inputs"), dict):
        raise Stop("STOP: declared-inputs stage_a_inputs must be an object")
    return data


def _declared_items(declared: dict) -> list[dict]:
    items = declared.get("items")
    if not isinstance(items, list) or not items:
        raise Stop("STOP: declared-inputs manifest has no items")
    ids = [item.get("id") if isinstance(item, dict) else None for item in items]
    if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        raise Stop("STOP: declared-inputs item ids are not unique nonempty strings")
    return items


def _declared_file_items(declared: dict) -> list[dict]:
    return [item for item in _declared_items(declared) if item.get("kind") == "file"]


def verify_declared_inputs(cwd: Path, spec: dict, declared: dict, *, cfg: dict | None = None,
                           paper_dir: Path | None = None, harness_dir: Path | None = None,
                           binding: dict | None = None, installed_cache: dict | None = None) -> dict:
    """Verify every declared input item (path + sha256/tree digest) and the declared pins.

    ``phase`` is implicit: file/value items are verified against the job sandbox, ``paper_blob`` items against the
    pinned paper checkout, ``harness_tree`` items against the pinned harness checkout, and ``staged_tree`` items
    against the installed OpenML cache report.  A missing or mismatched required input is a STOP with all failures
    persisted to ``DECLARED_INPUTS_STOP.json``; nothing is skipped or assumed.
    """
    cwd = Path(cwd)
    items = _declared_items(declared)
    failures: list[dict] = []
    verified: list[dict] = []
    for item in items:
        item_id = item["id"]
        kind = item.get("kind")
        try:
            if kind == "file":
                staged = item.get("staged")
                if not isinstance(staged, str) or not staged or "/" in staged or "\\" in staged:
                    raise Stop("declared file item needs a flat staged name")
                path = cwd / staged
                if not path.is_file():
                    raise Stop(f"staged file {staged} missing")
                got = _sha_file(path)
                if got != item.get("sha256"):
                    raise Stop(f"sha256 {got} != declared {item.get('sha256')}")
                verified.append({"id": item_id, "kind": kind, "sha256": got, "path": staged})
            elif kind == "paper_blob":
                if paper_dir is None:
                    continue
                blob = git_blob(Path(paper_dir), item["path"])
                got = _sha_bytes(blob)
                if got != item.get("sha256"):
                    raise Stop(f"committed blob {item['path']} sha256 {got} != declared {item.get('sha256')}")
                verified.append({"id": item_id, "kind": kind, "sha256": got, "commit": PAPER_COMMIT})
            elif kind == "harness_tree":
                if harness_dir is None:
                    continue
                rows = _harness_tree(Path(harness_dir), item["path"])
                tree = _tree_sha(rows)
                if tree != item.get("tree_sha256"):
                    raise Stop(f"harness tree {item['path']} digest {tree} != declared {item.get('tree_sha256')}")
                verified.append({"id": item_id, "kind": kind, "tree_sha256": tree, "commit": HARNESS_COMMIT,
                                 "files": len(rows)})
            elif kind == "staged_tree":
                declared_tree = _tree_sha([(row["path"], row["sha256"]) for row in item.get("files") or []])
                if declared_tree != item.get("tree_sha256"):
                    raise Stop(f"declared cache file list does not reproduce tree_sha256 {item.get('tree_sha256')}")
                if installed_cache is None:
                    verified.append({"id": item_id, "kind": kind, "tree_sha256": declared_tree,
                                     "files": len(item.get("files") or []),
                                     "installed_cache": "verified at job start"})
                    continue
                installed = (installed_cache.get("installed") or {}).get(item["id"])
                if installed != item.get("tree_sha256"):
                    raise Stop(f"installed cache tree {installed!r} != declared {item.get('tree_sha256')!r}")
                verified.append({"id": item_id, "kind": kind, "tree_sha256": installed, "files": len(item["files"])})
            elif kind == "value":
                want = _value_pin(item_id)
                got = {key: item.get(key) for key in want}
                if got != want:
                    raise Stop(f"declared value {got!r} != the pinned value {want!r}")
                verified.append({"id": item_id, "kind": kind, "value": got})
            else:
                raise Stop(f"unknown declared-item kind {kind!r}")
        except Stop as exc:
            failures.append({"id": item_id, "kind": kind, "reason": str(exc).replace("STOP: ", "")})
    failures.extend(_declared_pin_failures(declared, cfg, binding, paper_dir))
    report = {"schema": "s2_c3_declared_inputs_report/1", "manifest_sha256": _sha_file(cwd / DECLARED_STAGED)
              if (cwd / DECLARED_STAGED).is_file() else DECLARED_SHA256,
              "paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT, "items": len(items),
              "verified": verified, "failures": failures,
              "phases": {"files_values": True, "paper_blobs": paper_dir is not None,
                         "harness_trees": harness_dir is not None,
                         "openml_cache": installed_cache is not None}}
    if failures:
        (cwd / "DECLARED_INPUTS_STOP.json").write_text(json.dumps(report, indent=1) + "\n")
        detail = "; ".join(f"{row['id']}: {row['reason']}" for row in failures[:8])
        raise Stop(f"STOP: declared-inputs audit failed for {len(failures)} item(s): {detail}")
    return report


def _value_pin(item_id: str):
    pins = {"b2_configuration_binding": {"value": BINDING},
            "model_gguf": {"sha256": GGUF_SHA256, "value": GGUF_SIZE},
            "image_llama_server": {"sha256": IMAGE_LLAMA_SERVER_SHA256, "value": IMAGE_DIGEST}}
    if item_id not in pins:
        raise Stop(f"unknown declared value item {item_id!r}")
    return pins[item_id]


def _declared_pin_failures(declared: dict, cfg: dict | None, binding: dict | None,
                           paper_dir: Path | None) -> list[dict]:
    pins = declared.get("pins")
    if not isinstance(pins, dict):
        return [{"id": "pins", "kind": "value", "reason": "declared-inputs pins are missing"}]
    expected = {"paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT, "image_digest": IMAGE_DIGEST,
                "llama_server_sha256": IMAGE_LLAMA_SERVER_SHA256, "model_sha256": GGUF_SHA256,
                "model_size": GGUF_SIZE, "binding": BINDING,
                "replay_inputs_sha256sums_sha256": INPUTS_SHA256SUMS_SHA256, "label_patch_sha256": PATCH_SHA256,
                "driver_shim_sha256": SHIM_SHA256, "criteria_sha256": CRITERIA_SHA256}
    failures = []
    for key, want in expected.items():
        if pins.get(key) != want:
            failures.append({"id": f"pin:{key}", "kind": "value",
                             "reason": f"{pins.get(key)!r} != the pinned {want!r}"})
    if cfg is not None:
        for key in ("rule_sha256", "stage_a_table_sha256", "stage_a_amendment_table_sha256",
                    "stage_a_amendment_acceptance_sha256", "prompts_sha256", "b1_analysis_sha256"):
            if key in cfg and pins.get(key) != cfg[key]:
                failures.append({"id": f"pin:{key}", "kind": "blocker",
                                 "reason": f"{pins.get(key)!r} != authority_config {cfg[key]!r}"})
    if binding is not None:
        for key, got in (("registry_sha256", binding.get("registry_sha256")),
                         ("value_grids_sha256", binding.get("value_grids_sha256"))):
            if got is not None and pins.get(key) != got:
                failures.append({"id": f"pin:{key}", "kind": "blocker",
                                 "reason": f"{pins.get(key)!r} != recomputed {got!r}"})
    if paper_dir is not None:
        for key, rel in (("authorization_note_sha256", B2_AUTHORIZATION_NOTE),
                         ("plan_sha256", "docs/r1/PLAN.md")):
            got = _sha_bytes(git_blob(Path(paper_dir), rel))
            if pins.get(key) != got:
                failures.append({"id": f"pin:{key}", "kind": "blocker",
                                 "reason": f"{pins.get(key)!r} != committed {got!r}"})
    return failures


def _harness_tree(harness_dir: Path, rel: str) -> list[tuple[str, str]]:
    text = _git(Path(harness_dir), "ls-tree", "-r", HARNESS_COMMIT, "--", rel)
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        meta, path = line.split("\t", 1)
        mode, kind, blob = meta.split()
        if kind != "blob" or not re.fullmatch(r"[0-9a-f]{40}", blob):
            raise Stop(f"STOP: harness tree {rel} has a non-blob entry")
        rows.append((path, blob))
    if not rows:
        raise Stop(f"STOP: harness tree {rel} is empty or missing at the pinned commit")
    return rows


def _safe_extract(archive: Path, dest: Path) -> None:
    """Extract a declared input archive with no traversal, links or device entries."""
    import tarfile
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise Stop(f"STOP: declared archive member escapes the extraction root: {member.name!r}")
            if not (member.isfile() or member.isdir()):
                raise Stop(f"STOP: declared archive member is not a regular file/dir: {member.name!r}")
            if member.isfile() and (member.uid != 0 or member.gid != 0):
                raise Stop("STOP: declared archive file ownership is not normalized")
            if member.isfile() and member.mtime != 1763337600:
                raise Stop("STOP: declared archive file mtime is not the fixed replay mtime")
        try:
            tar.extractall(dest, filter="data")
        except TypeError:  # Python 3.11 has no extraction filter
            tar.extractall(dest)


def stage_openml_cache(cwd: Path, declared: dict, harness_dir: Path) -> dict:
    """Install the declared, sha-pinned OpenML caches at the exact path the B2 campaign copies from.

    The harness at ``a3fedbb`` ignores ``experiments/**``, so the installed cache is invisible to the campaign's
    clean-checkout gates.  The install is verified by per-file sha256 and per-node tree digest.
    """
    cwd, harness_dir = Path(cwd), Path(harness_dir)
    archive_items = [item for item in _declared_file_items(declared) if item["id"] == "openml_cache_archive"]
    if len(archive_items) != 1:
        raise Stop("STOP: declared inputs must carry exactly one OpenML cache archive")
    archive = cwd / archive_items[0]["staged"]
    if _sha_file(archive) != archive_items[0]["sha256"]:
        raise Stop("STOP: OpenML cache archive changed after the declared-inputs check")
    work = cwd / "work" / "openml_cache"
    if work.exists():
        raise Stop("STOP: OpenML cache staging directory already exists (fresh sandbox required)")
    _safe_extract(archive, work)
    target_root = harness_dir / OPENML_CACHE_REL
    installed, trees, files = {}, {}, 0
    for node in OPENML_NODES:
        extracted = work / node / "data_cache"
        if not extracted.is_dir():
            raise Stop(f"STOP: declared OpenML cache archive lacks {node}/data_cache")
        entries = [(path.relative_to(extracted).as_posix(), _sha_file(path))
                   for path in sorted(extracted.rglob("*")) if path.is_file()]
        tree = _tree_sha(entries)
        item = next((row for row in _declared_items(declared) if row.get("id") == f"{node}_cache"), None)
        if item is None or item.get("tree_sha256") != tree:
            raise Stop(f"STOP: extracted {node} cache tree {tree} != declared identity")
        files += len(entries)
        tree_map = {rel: digest for rel, digest in entries}
        for row in item.get("files") or []:
            if tree_map.get(row["path"]) != row["sha256"]:
                raise Stop(f"STOP: {node} cache file {row['path']} sha256 differs from the declaration")
        target = target_root / node / "data_cache"
        if target.exists():
            raise Stop(f"STOP: harness OpenML cache target already exists ({target})")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(extracted, target)
        check = subprocess.run(["git", "-C", str(harness_dir), "check-ignore", "-q", str(target)],
                               capture_output=True, text=True)
        if check.returncode != 0:
            raise Stop(f"STOP: staged OpenML cache {target} is not gitignored by the pinned harness; "
                       "it would dirty the checkout the campaign binds")
        got = _tree_sha([(path.relative_to(target).as_posix(), _sha_file(path))
                         for path in sorted(target.rglob("*")) if path.is_file()])
        if got != tree:
            raise Stop(f"STOP: installed {node} cache tree {got} != extracted {tree}")
        installed[f"{node}_cache"] = got
        trees[node] = got
    if _git(harness_dir, "status", "--porcelain", "--ignored=no"):
        raise Stop("STOP: staging the OpenML cache dirtied the pinned harness checkout")
    return {"archive_sha256": archive_items[0]["sha256"], "installed": installed, "tree_sha256": trees,
            "files": files, "target_rel": OPENML_CACHE_REL, "gitignored": True, "harness_clean": True}


# ------------------------------------------------------------------ reviewed shim scope
SHIM_ALLOWED_ANCHORS = ("def read_registry(path):", "def _committed_b1_authority(cfg, note, raw, rule_sha):",
                        "def require_worker_host(job, node=None):",
                        "def stage_a_pass_set(cfg, registry_candidates, *, v2):")
SHIM_FORBIDDEN = re.compile(r"run_config|paired\s*\(|run_real_campaign|root_trials|root_events|audit_seeds|"
                           r"instance_seeds|final_audits|diagnostics|write_json|score|metric|manager|proposal")


def check_shim_scope(diff_text: str) -> dict:
    """Refuse a shim that removes pinned lines, touches other files, or reaches trial/audit/scoring code."""
    if not isinstance(diff_text, str) or not diff_text.strip():
        raise Stop("STOP: driver shim is empty")
    files, added, removed, hunks = set(), [], [], []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) != 4 or not parts[2].startswith("a/") or not parts[3].startswith("b/"):
                raise Stop("STOP: malformed driver-shim patch header")
            files.add(parts[2][2:])
            if parts[2][2:] != parts[3][2:]:
                raise Stop("STOP: the driver shim may not rename files")
        elif line.startswith("@@"):
            hunks.append(line)
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    if files != set(SHIM_TARGETS):
        raise Stop(f"STOP: the driver shim may touch only {sorted(SHIM_TARGETS)}; got {sorted(files)}")
    if removed:
        raise Stop("STOP: the driver shim may only add lines (it must not modify or remove pinned code)")
    if not added:
        raise Stop("STOP: the driver shim adds nothing")
    anchors = []
    for hunk in hunks:
        match = re.search(r"@@ [^@]+ @@ (.*)$", hunk)
        anchor = match.group(1).strip() if match else ""
        anchors.append(anchor)
        if anchor not in SHIM_ALLOWED_ANCHORS:
            raise Stop(f"STOP: driver shim hunk anchor {anchor!r} is outside the reviewed allowlist")
    for line in added:
        code = line.strip()
        if not code or code.startswith("#") or code.startswith('"""') or code.startswith("'''"):
            continue
        if SHIM_FORBIDDEN.search(code):
            raise Stop(f"STOP: driver shim touches trial/audit/scoring code: {line[:140]!r}")
    return {"files": [rel for rel in SHIM_TARGETS if rel in files], "hunks": anchors,
            "added_lines": len(added), "removed_lines": 0,
            "additions_only": True, "touches_no_trial_audit_scoring": True}


def rewrite_job_json(text: str, new_out: str, new_base_url: str) -> str:
    """Return the job.json text with ONLY `out` and `base_url` rewritten; nothing else may change."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Stop(f"STOP: recorded job.json is not valid JSON: {exc}") from None
    for key in ("out", "base_url"):
        if key not in obj:
            raise Stop(f"STOP: recorded job.json lacks {key!r}; cannot rewrite it")
    canonical = json.dumps(obj, indent=2) + "\n"
    if canonical != text:
        # The pinned inputs were written by the B2 `write_json` (indent=2).  Refuse to guess a byte layout.
        raise Stop("STOP: recorded job.json is not in the canonical B2 write_json(indent=2) form")
    patched = dict(obj)
    patched["out"] = new_out
    patched["base_url"] = new_base_url
    rendered = json.dumps(patched, indent=2) + "\n"
    changed = [(n, old, new) for n, (old, new) in enumerate(
        zip(text.splitlines(), rendered.splitlines())) if old != new]
    if len(changed) != 2:
        raise Stop("STOP: the job.json rewrite did not change exactly two lines")
    for _, old, new in changed:
        key = re.match(r'^  "([A-Za-z0-9_]+)"\s*:', new)
        if not key or key.group(1) not in ("out", "base_url"):
            raise Stop(f"STOP: the job.json rewrite would change a forbidden line: {new[:80]!r}")
    if json.loads(rendered) != patched:
        raise Stop("STOP: rewritten job.json does not round-trip")
    return rendered


def prepare_root_jobs(cwd: Path, spec: dict, node: str, pins: dict, base_url: str, sha256sums_sha256: str) -> list[dict]:
    """Write the 4 rewritten job.json copies into their sandbox out dirs and prove byte-level scope."""
    cwd = Path(cwd)
    out_root = (cwd / "out").resolve()
    prepared = []
    for root in ordered_roots(node):
        original_path = cwd / STAGED_JOB.format(root=root)
        original_text = original_path.read_text()
        original_sha = _sha_bytes(original_text.encode())
        if original_sha != pins[root]:
            raise Stop(f"STOP: {root} job.json changed after the SHA256SUMS check")
        root_out = out_root / root
        rewritten = rewrite_job_json(original_text, str(root_out), base_url)
        root_out.mkdir(parents=True, exist_ok=True)
        job_path = root_out / "job.json"
        job_path.write_text(rewritten)
        parsed = json.loads(rewritten)
        if parsed["out"] != str(root_out) or parsed["base_url"] != base_url:
            raise Stop(f"STOP: {root} rewritten job.json does not carry the sandbox out/base_url")
        prepared.append({"root": root, "seed": parsed["seed"], "out": str(root_out),
                         "job_json": str(job_path), "original_sha256": original_sha,
                         "rewritten_sha256": _sha_file(job_path), "changed_fields": ["out", "base_url"]})
    if len(prepared) != len(SEEDS):
        raise Stop("STOP: a replay job must prepare exactly its node's 4 roots")
    after = verify_pinned_inputs(cwd, spec)  # the staged originals must be untouched
    if after["sha256sums_sha256"] != sha256sums_sha256:
        raise Stop("STOP: staged replay inputs changed while preparing job.json copies")
    return prepared


def ordered_roots(node: str) -> list[str]:
    if node not in NODES:
        raise Stop(f"STOP: unknown node {node!r}")
    return [f"{node}__s{seed}" for seed in SEEDS]


# ------------------------------------------------------------------ configuration binding (B2 method)
def recompute_binding(cfg: dict, registry_sha256: str, value_grids_sha256: str) -> str:
    """The exact B2 method (`ExamRunner.__init__`): the configuration binding, independent of out/base_url."""
    payload = {"config": cfg, "registry_sha256": registry_sha256, "rule_sha256": cfg["rule_sha256"],
               "value_grids_sha256": value_grids_sha256}
    return _sha_bytes(json.dumps(payload, sort_keys=True).encode())


def git_blob(paper_dir: Path, rel: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(paper_dir), "show", f"HEAD:{rel}"])


def verify_binding(paper_dir: Path, jobs: dict[str, dict], spec: dict) -> dict:
    """Recompute the B2 configuration binding from the pinned checkout and prove it did not change.

    B2 computes `sha256(json.dumps({'config': cfg, 'registry_sha256': digest(batch registry snapshot),
    'rule_sha256': cfg['rule_sha256'], 'value_grids_sha256': digest(value_grids)}, sort_keys=True))`
    (r1/exam/runtime.py @ 8709dce7, `ExamRunner.__init__`).  The batch registry snapshot is a byte copy of the
    committed `cfg['registry']` at the run HEAD, so the committed blobs reproduce it.  The binding covers the
    authority configuration only - `out` and `base_url` are not inputs, so a sandbox rewrite cannot change it.
    """
    cfg = jobs[ROOTS[0]]["authority_config"]
    committed_cfg = json.loads(git_blob(paper_dir, B2_CONFIG_REL))
    if committed_cfg != cfg:
        raise Stop("STOP: the recorded authority_config is not the committed B2 configuration at the pinned HEAD")
    rule = git_blob(paper_dir, cfg["rule"])
    if _sha_bytes(rule) != cfg["rule_sha256"]:
        raise Stop("STOP: the committed rule blob does not match the recorded rule_sha256")
    registry_sha = _sha_bytes(git_blob(paper_dir, cfg["registry"]))
    grids_sha = _sha_bytes(git_blob(paper_dir, cfg["value_grids"]))
    recomputed = recompute_binding(cfg, registry_sha, grids_sha)
    if recomputed != BINDING:
        raise Stop(f"STOP: recomputed B2 binding {recomputed} != recorded {BINDING}")
    if recomputed != spec["replay_inputs"]["binding"]:
        raise Stop("STOP: recomputed B2 binding differs from the replay spec pin")
    for root, job in jobs.items():
        if job.get("binding") != recomputed:
            raise Stop(f"STOP: {root} job.json binding differs from the recomputed B2 binding")
    return {"recorded": BINDING, "recomputed": recomputed, "unchanged_by_rewrite": True,
            "registry_sha256": registry_sha, "rule_sha256": cfg["rule_sha256"],
            "value_grids_sha256": grids_sha, "config_equals_committed": True,
            "method": ("sha256(json.dumps({'config': cfg, 'registry_sha256': digest(committed registry), "
                       "'rule_sha256': cfg['rule_sha256'], 'value_grids_sha256': digest(committed value grids)}, "
                       "sort_keys=True)) - the B2 ExamRunner.__init__ method")}


# ------------------------------------------------------------------ paper/harness checkouts and label patch
def _git(paper_dir: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(paper_dir), *args], text=True).strip()


def prepare_authorization_checkout(spec: dict, dest: Path) -> dict:
    if dest.exists():
        raise Stop(f"STOP: scratch checkout {dest} already exists (fresh scratch required)")
    lib.clone_at(spec["paper"]["repo"], PAPER_COMMIT, dest)
    head = _git(dest, "rev-parse", "HEAD")
    if head != PAPER_COMMIT:
        raise Stop(f"STOP: paper checkout HEAD {head} != pinned {PAPER_COMMIT}")
    dirty = _git(dest, "status", "--porcelain", "--untracked-files=all")
    if dirty:
        raise Stop("STOP: authorization checkout is not clean (a patch must never dirty it)")
    note = dest / B2_AUTHORIZATION_NOTE
    if not note.is_file():
        raise Stop(f"STOP: B2 authorization note missing from the pinned checkout ({B2_AUTHORIZATION_NOTE})")
    return {"path": str(dest), "commit": head, "clean": True,
            "b2_authorization_note_sha256": _sha_file(note)}


def check_patch_scope(diff_text: str) -> dict:
    """Refuse a label patch that touches anything except the execution label and the replay marker."""
    if not isinstance(diff_text, str) or not diff_text.strip():
        raise Stop("STOP: label patch is empty")
    files = set()
    removed, added = [], []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) != 4 or not parts[2].startswith("a/") or not parts[3].startswith("b/"):
                raise Stop("STOP: malformed label patch header")
            files.add(parts[2][2:])
            if parts[2][2:] != parts[3][2:]:
                raise Stop("STOP: label patch may not rename files")
        elif line.startswith("+++ ") or line.startswith("--- "):
            continue
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
    if files != {PATCH_TARGET}:
        raise Stop(f"STOP: label patch must touch only {PATCH_TARGET}; got {sorted(files)}")
    if not added or not removed:
        raise Stop("STOP: label patch must replace at least one line")
    allowed_removed = re.compile(r"^.*'execution_label'\s*:.*$")
    allowed_added = re.compile(
        r"^(?:.*S2-C3 replay label patch refuses a DRYRUN job.*"
        r"|.*'execution_label'\s*:\s*'ENGINEERING_ONLY'.*'replay_marker'\s*:\s*'s2_c3_replay/v1'.*)$")
    for line in removed:
        if not allowed_removed.fullmatch(line.strip()):
            raise Stop(f"STOP: label patch removes a line outside the execution label: {line[:120]!r}")
    for line in added:
        if not allowed_added.fullmatch(line.strip()):
            raise Stop(f"STOP: label patch adds a line outside the execution label/marker: {line[:120]!r}")
    for line in removed + added:
        if re.search(r"def |run_config|paired\(|audit|root_trials|root_events|diagnostics|final_audits",
                     line):
            raise Stop("STOP: label patch may not touch trial/audit logic")
    return {"files": sorted(files), "removed_lines": len(removed), "added_lines": len(added),
            "execution_label_only": True}


def apply_label_patch(paper_dir: Path, patch_path: Path, work_patch_dir: Path) -> dict:
    """Apply the reviewed patch in a sandbox worktree of the pinned commit; keep the authorization checkout clean.

    The B2 authorization gate (`require_committed_b1_config`) binds the *clean* checkout at the pinned
    authorization head.  Committing the label patch there (or leaving it dirty) would make the campaign refuse the
    replay, so the patch is applied in a separate detached worktree of the same commit and its patched source is
    shadow-executed by the driver; the authorization checkout stays byte-identical to `8709dce7`.
    """
    patch_text = patch_path.read_text()
    checked = check_patch_scope(patch_text)
    if _sha_file(patch_path) != PATCH_SHA256:
        raise Stop(f"STOP: label patch sha256 {_sha_file(patch_path)} != the spec pin {PATCH_SHA256}")
    base = work_patch_dir / "campaign.base.py"
    patched = work_patch_dir / "campaign.patched.py"
    patched_tree = Path(paper_dir).parent / "paper_patched"
    if patched_tree.exists():
        raise Stop(f"STOP: patched sandbox checkout {patched_tree} already exists")
    work_patch_dir.mkdir(parents=True, exist_ok=True)
    base.write_bytes((Path(paper_dir) / PATCH_TARGET).read_bytes())
    check = subprocess.run(["git", "-C", str(paper_dir), "apply", "--check", str(patch_path)],
                           capture_output=True, text=True)
    if check.returncode != 0:
        raise Stop(f"STOP: label patch does not apply cleanly to the pinned checkout: {check.stderr.strip()[:800]}")
    subprocess.run(["git", "-C", str(paper_dir), "worktree", "add", "--detach", str(patched_tree), PAPER_COMMIT],
                   check=True, capture_output=True, text=True)
    applied = subprocess.run(["git", "-C", str(patched_tree), "apply", str(patch_path)],
                             capture_output=True, text=True)
    if applied.returncode != 0:
        raise Stop(f"STOP: label patch application in the sandbox worktree failed: {applied.stderr.strip()[:800]}")
    patched.write_bytes((patched_tree / PATCH_TARGET).read_bytes())
    original_sha, patched_sha = _sha_file(base), _sha_file(patched)
    if original_sha == patched_sha:
        raise Stop("STOP: label patch did not change the pinned campaign source")
    if _sha_file(Path(paper_dir) / PATCH_TARGET) != original_sha:
        raise Stop("STOP: applying the label patch dirtied the authorization checkout")
    if _git(paper_dir, "status", "--porcelain", "--untracked-files=all"):
        raise Stop("STOP: authorization checkout is not clean after patch application")
    diff = _git(patched_tree, "diff") + "\n"

    def normalize(text: str) -> str:
        # The blob ids in the ``index`` line use git's abbreviation, which is environment-dependent.
        return "\n".join(line for line in text.splitlines() if not line.startswith("index ")).strip()

    if normalize(diff) != normalize(patch_text):
        raise Stop("STOP: the applied diff differs from the reviewed label patch")
    check_patch_scope(diff)
    if (work_patch_dir / "LABEL_SCOPE.json").exists():
        raise Stop("STOP: label patch evidence already exists (no overwrite)")
    (work_patch_dir / "APPLIED.diff").write_text(diff)
    (work_patch_dir / "LABEL_SCOPE.json").write_text(json.dumps(
        {"schema": "s2_c3_label_scope/1", "patch_sha256": PATCH_SHA256, "patched_tree": str(patched_tree),
         "original_source_sha256": original_sha, "patched_source_sha256": patched_sha, **checked}, indent=1) + "\n")
    return {"patch_sha256": PATCH_SHA256, "original_source_sha256": original_sha,
            "patched_source_sha256": patched_sha, "applied_cleanly": True, "patched_tree": str(patched_tree),
            "patched_campaign_source": str(patched), "scope": checked,
            "authorization_checkout_clean": True}


def apply_reviewed_patches(paper_dir: Path, staged_patches: list[dict], work_patch_dir: Path) -> dict:
    """Apply the reviewed label patch and replay shim to one detached sandbox worktree.

    Same method as ``apply_label_patch`` (the pinned authorization checkout stays byte-identical; only the patched
    sources are shadow-executed), extended to the two reviewed patches.  Both scopes, both patch shas and **all
    three** patched source byte pins are checked; a mismatch is a STOP.
    """
    paper_dir = Path(paper_dir)
    specs = {"label": {"path": PATCH_PATH, "sha256": PATCH_SHA256, "scope": check_patch_scope},
             "shim": {"path": SHIM_PATH, "sha256": SHIM_SHA256, "scope": check_shim_scope}}
    patches = []
    for entry in staged_patches:
        kind = entry["kind"]
        if kind not in specs:
            raise Stop(f"STOP: unknown reviewed patch kind {kind!r}")
        text = Path(entry["path"]).read_text()
        if _sha_file(Path(entry["path"])) != specs[kind]["sha256"]:
            raise Stop(f"STOP: {kind} patch sha256 {_sha_file(Path(entry['path']))} != the reviewed pin "
                       f"{specs[kind]['sha256']}")
        patches.append({"kind": kind, "path": Path(entry["path"]), "text": text,
                        "sha256": specs[kind]["sha256"], "scope": specs[kind]["scope"](text)})
    if [patch["kind"] for patch in patches] != ["label", "shim"]:
        raise Stop("STOP: reviewed patches must be applied in [label, shim] order")
    work_patch_dir.mkdir(parents=True, exist_ok=True)
    bases = {}
    for rel in SHIM_TARGETS:
        source = paper_dir / rel
        if not source.is_file():
            raise Stop(f"STOP: pinned paper checkout lacks {rel}")
        bases[rel] = _sha_file(source)
        (work_patch_dir / f"{Path(rel).stem}.base.py").write_bytes(source.read_bytes())
    for patch in patches:
        check = subprocess.run(["git", "-C", str(paper_dir), "apply", "--check", str(patch["path"])],
                               capture_output=True, text=True)
        if check.returncode != 0:
            raise Stop(f"STOP: {patch['kind']} patch does not apply cleanly to the pinned checkout: "
                       f"{check.stderr.strip()[:800]}")
    patched_tree = paper_dir.parent / "paper_patched"
    if patched_tree.exists():
        raise Stop(f"STOP: patched sandbox checkout {patched_tree} already exists")
    subprocess.run(["git", "-C", str(paper_dir), "worktree", "add", "--detach", str(patched_tree), PAPER_COMMIT],
                   check=True, capture_output=True, text=True)
    for patch in patches:
        applied = subprocess.run(["git", "-C", str(patched_tree), "apply", str(patch["path"])],
                                 capture_output=True, text=True)
        if applied.returncode != 0:
            raise Stop(f"STOP: {patch['kind']} patch application in the sandbox worktree failed: "
                       f"{applied.stderr.strip()[:800]}")
    patched_sources, patched_shas = {}, {}
    for rel in SHIM_TARGETS:
        target = work_patch_dir / f"{Path(rel).stem}.patched.py"
        target.write_bytes((patched_tree / rel).read_bytes())
        got = _sha_file(target)
        if got != PATCHED_SOURCE_SHA256[rel]:
            raise Stop(f"STOP: patched {rel} sha256 {got} != the reviewed patched-source pin "
                       f"{PATCHED_SOURCE_SHA256[rel]}")
        patched_sources[rel] = str(target)
        patched_shas[rel] = got
    for rel, base_sha in bases.items():
        if _sha_file(paper_dir / rel) != base_sha:
            raise Stop(f"STOP: applying the reviewed patches dirtied the authorization checkout ({rel})")
    if _git(paper_dir, "status", "--porcelain", "--untracked-files=all"):
        raise Stop("STOP: authorization checkout is not clean after patch application")
    if (work_patch_dir / "REPLAY_SCOPE.json").exists():
        raise Stop("STOP: replay-patch evidence already exists (no overwrite)")
    (work_patch_dir / "REPLAY_SCOPE.json").write_text(json.dumps(
        {"schema": "s2_c3_replay_scope/1", "patched_tree": str(patched_tree),
         "label": patches[0]["scope"], "shim": patches[1]["scope"],
         "patched_source_sha256": patched_shas, "authorization_checkout_clean": True}, indent=1) + "\n")
    (work_patch_dir / "APPLIED_LABEL.diff").write_text(patches[0]["text"])
    (work_patch_dir / "APPLIED_SHIM.diff").write_text(patches[1]["text"])
    return {"label_patch_sha256": PATCH_SHA256, "shim_patch_sha256": SHIM_SHA256,
            "patched_source_sha256": patched_shas, "patched_tree": str(patched_tree),
            "patched_campaign_source": patched_sources["r1/exam/campaign.py"],
            "patched_runtime_source": patched_sources["r1/exam/runtime.py"],
            "patched_runner_source": patched_sources["r1/scripts/exam_runner.py"],
            "label_scope": patches[0]["scope"], "shim_scope": patches[1]["scope"],
            "authorization_checkout_clean": True, "applied_cleanly": True}


# ------------------------------------------------------------------ exact B2 authorization gate pre-flight
# The probe shadow-executes BOTH B2 sources: the label-patched campaign and the shim-patched runtime.  Without the
# replay environment variables the shim is inert, so the same probe also reports the unshimmed TASL refusals.
GATE_PROBE = r"""
import json, sys, traceback
job = json.load(open(sys.argv[1]))
patched_runtime = sys.argv[2]
patched_campaign = sys.argv[3]
patched_runner = sys.argv[4]
import r1.exam.runtime as rt
exec(compile(open(patched_runtime).read(), rt.__file__, "exec"), rt.__dict__)
import r1.exam.campaign as c
exec(compile(open(patched_campaign).read(), c.__file__, "exec"), c.__dict__)
# The B2 root campaign reaches the Stage A pass set through r1.scripts.exam_runner.stage_a_pass_set via
# observer._authorized_candidate; shadow-exec the reviewed exam_runner hunk too, then exercise that exact path.
import r1.scripts.exam_runner as er
exec(compile(open(patched_runner).read(), er.__file__, "exec"), er.__dict__)
from r1.exam.runtime import host_check, b1_harness_sources, read_registry
from r1.exam.observer import _authorized_candidate
results = {}
def rec(name, fn):
    try:
        fn()
        results[name] = {"ok": True}
    except BaseException as exc:  # noqa: BLE001 - report every refusal verbatim
        results[name] = {"ok": False, "type": type(exc).__name__, "error": str(exc)[:800]}
rec("verify_b1_worker_input", lambda: c._verify_b1_worker_input(job))
rec("host_check", lambda: host_check(job["authority_config"], job["out"]))
rec("require_worker_host", lambda: c.require_worker_host(job))
def harness_binding():
    cfg = job.get("authority_config") or {}
    if job.get("harness_commit") != cfg.get("harness_commit"):
        raise RuntimeError("harness commit differs from the authority configuration")
    if job.get("node_source_sha256") != b1_harness_sources(job["node"], job["harness_commit"]):
        raise RuntimeError("node source bytes differ from the pinned harness commit")
rec("harness_binding", harness_binding)
def authorized_candidate():
    # The exact call chain of the B2 root campaign: authorized_b1_observer -> _authorized_candidate ->
    # stage_a_pass_set (taken on every root because the committed registry footprint is TODO_VERIFY_ON_HOST).
    cfg = job.get("authority_config") or {}
    registry = read_registry(cfg["registry"])
    if not _authorized_candidate(job, cfg, registry):
        raise RuntimeError("the job candidate does not resolve to the registry through the Stage A pass set")
rec("authorized_candidate", authorized_candidate)
print(json.dumps(results))
"""


def run_gate_probe(paper_dir: Path, harness_dir: Path, job_path: Path, patched_campaign: Path,
                   patched_runtime: Path, patched_runner: Path, env_extra: dict | None = None) -> dict:
    """Run the exact campaign authorization gate sequence against the prepared job (no server, no LLM)."""
    probe = paper_dir.parent / "work" / "gate_probe.py"
    probe.parent.mkdir(parents=True, exist_ok=True)
    if not probe.is_file():
        probe.write_text("#!/usr/bin/env python3\n" + GATE_PROBE)
    env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()),
               AR_HARNESS_ROOT=str(harness_dir.resolve()), PYTHONDONTWRITEBYTECODE="1",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    env.pop("LLAMACPP_CACHE_PROMPT", None)
    env.pop("LLAMACACHE_PROMPT", None)
    for key in (REPLAY_DECLARED_ENV, REPLAY_ROOT_ENV, REPLAY_SANDBOX_ENV):
        env.pop(key, None)
    if env_extra:
        env.update(env_extra)
    res = subprocess.run([sys.executable, "-B", str(probe), str(job_path), str(patched_runtime),
                          str(patched_campaign), str(patched_runner)],
                         cwd=str(paper_dir.resolve()), env=env, capture_output=True, text=True, timeout=900)
    payload = None
    for line in reversed(res.stdout.splitlines()):
        try:
            payload = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    if not isinstance(payload, dict):
        raise Stop(f"STOP: authorization gate probe produced no result (rc={res.returncode}): "
                   f"{res.stderr.strip()[-1500:]}")
    return {"probe_rc": res.returncode, "checks": payload, "stderr_tail": res.stderr[-2000:]}


def collect_preflight_blockers(spec: dict, cfg: dict, out: Path, paper_dir: Path, harness_dir: Path,
                               gate: dict) -> list[dict]:
    """All deterministic reasons the unmodified B2 campaign driver will refuse this replay environment."""
    blockers = []
    for name, result in gate["checks"].items():
        if not result.get("ok"):
            blockers.append({"gate": name, "type": result.get("type"), "reason": result.get("error")})
    # The pre-declared protocol rewrites `out` to the sandbox; B2 host_check requires out under cfg['work_dir'].
    try:
        out_under = Path(out).resolve().is_relative_to(Path(cfg["work_dir"]))
    except (KeyError, TypeError):
        out_under = False
    if not out_under:
        blockers.append({"gate": "out_under_work_dir", "type": "RuntimeError",
                         "reason": (f"rewritten out {out} is not under the B2 authorised work_dir "
                                    f"{cfg.get('work_dir')!r}; B2 host_check requires it "
                                    "(the pre-declared protocol's out rewrite cannot satisfy this)")})
    # The B2 author_gate digests Stage A inputs that live outside the repository (TASL-side files).
    for path_key, sha_key in (("rule", "rule_sha256"), ("stage_a_table", "stage_a_table_sha256"),
                              ("stage_a_amendment_table", "stage_a_amendment_table_sha256"),
                              ("stage_a_amendment_acceptance", "stage_a_amendment_acceptance_sha256")):
        rel = cfg.get(path_key)
        want = cfg.get(sha_key)
        if not isinstance(rel, str) or not isinstance(want, str):
            continue
        path = Path(rel)
        path = path if path.is_absolute() else Path(paper_dir) / path
        if not path.is_file():
            blockers.append({"gate": f"authorization_input:{path_key}", "type": "FileNotFoundError",
                             "reason": f"B2 author_gate input {path_key}={str(path)} is absent from the job sandbox"})
        elif _sha_file(path) != want:
            blockers.append({"gate": f"authorization_input:{path_key}", "type": "sha256",
                             "reason": f"B2 author_gate input {path_key} sha256 differs from the recorded pin"})
    # B2 campaign requires the verified OpenML cache for openml_* nodes; it is local TASL-side data (not in git).
    node = spec["node"]
    if node.startswith("openml_"):
        cache = Path(harness_dir) / "experiments/r1/pilot/L8_20261009T152916Z/nodes" / node / "data_cache"
        if not cache.is_dir():
            blockers.append({"gate": "openml_data_cache", "type": "RuntimeError",
                             "reason": (f"B2 campaign requires the verified OpenML cache {cache} for {node}; it is "
                                        "untracked TASL-side data and is not shipped in the harness repository")})
    return blockers


# ------------------------------------------------------------------ server + campaigns
def replay_env(cwd: Path) -> dict:
    """The replay-mode environment the reviewed shim reads (declared manifest + sandbox root; nothing else)."""
    cwd = Path(cwd).resolve()
    return {REPLAY_DECLARED_ENV: str(cwd / DECLARED_STAGED), REPLAY_ROOT_ENV: str(cwd),
            REPLAY_SANDBOX_ENV: str(cwd)}


def _worker_path() -> str:
    """The harness venv must be first on PATH: the B2 worker runs the node's `python3 train.py`; without this the
    container system Python is used and every worker run fails (32k-smoke failure mode)."""
    venv_bin = Path("/opt/r1/envs/harness/bin")
    if not (venv_bin / "python3").is_file() and not (venv_bin / "python").is_file():
        raise Stop(f"STOP: harness venv bin missing at {venv_bin} (worker python would be the system python)")
    return f"{venv_bin}:{os.environ.get('PATH', '')}"


def campaign_env(paper_dir: Path, harness_dir: Path, base_url: str, stop_fd: int | None = None,
                 cwd: Path | None = None) -> dict:
    env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()), AR_HARNESS_ROOT=str(harness_dir.resolve()),
               LLAMACPP_BASE_URL=base_url, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1", PATH=_worker_path())
    env.pop("LLAMACPP_CACHE_PROMPT", None)
    env.pop("LLAMACACHE_PROMPT", None)
    for key in (REPLAY_DECLARED_ENV, REPLAY_ROOT_ENV, REPLAY_SANDBOX_ENV):
        env.pop(key, None)
    if cwd is not None:
        env.update(replay_env(cwd))
    if stop_fd is not None:
        env["R1_B1_STOP_FD"] = str(stop_fd)
    return env


SHADOW_RUNNER = (
    "import sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import r1.exam.runtime as runtime\n"
    "exec(compile(open(sys.argv[2]).read(), runtime.__file__, 'exec'), runtime.__dict__)\n"
    "import r1.exam.campaign as campaign\n"
    "exec(compile(open(sys.argv[3]).read(), campaign.__file__, 'exec'), campaign.__dict__)\n"
    "import r1.scripts.exam_runner as exam_runner\n"
    "exec(compile(open(sys.argv[4]).read(), exam_runner.__file__, 'exec'), exam_runner.__dict__)\n"
    "campaign.main(['--job', sys.argv[5]])\n"
)


def run_one_campaign(paper_dir: Path, harness_dir: Path, job_path: Path, patched_campaign: Path,
                     patched_runtime: Path, patched_runner: Path, base_url: str, log_path: Path,
                     timeout_s: int, cwd: Path) -> dict:
    """Run one root campaign exactly as the B2 parent runs it, with all reviewed patches shadow-executed."""
    runner = Path(paper_dir).parent / "work" / "shadow_runner.py"
    runner.parent.mkdir(parents=True, exist_ok=True)
    if not runner.is_file():
        runner.write_text(SHADOW_RUNNER)
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    try:
        with log_path.open("wb") as log:
            proc = subprocess.Popen(
                [sys.executable, "-B", str(runner), str(paper_dir.resolve()),
                 str(patched_runtime), str(patched_campaign), str(patched_runner), str(job_path)],
                cwd=str(paper_dir.resolve()),
                env=campaign_env(paper_dir, harness_dir, base_url, write_fd, cwd),
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True, pass_fds=(write_fd,))
        os.close(write_fd)
        write_fd = None
        stop_seen = False
        while proc.poll() is None:
            try:
                if os.read(read_fd, 1):
                    stop_seen = True
                    lib._kill(proc)
                    break
            except BlockingIOError:
                pass
            if time.time() - started > timeout_s:
                lib._kill(proc)
                raise Stop("STOP: root campaign exceeded the job walltime budget")
            time.sleep(1.0)
        rc = proc.wait()
        wall = round(time.time() - started, 1)
    finally:
        for fd in (read_fd, write_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
    return {"returncode": rc, "wall_s": wall, "stop_signal": stop_seen, "log": str(log_path)}


def validate_campaign_manifest(out_dir: Path, job: dict, binding: dict, spec: dict) -> dict:
    manifest_path = Path(out_dir) / "campaign_manifest.json"
    if not manifest_path.is_file():
        raise Stop(f"STOP: campaign_manifest.json missing in {out_dir} (incomplete campaign; retain everything)")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("status") != "COMPLETE" or manifest.get("label") != "EXAM":
        raise Stop(f"STOP: {out_dir} manifest is not a COMPLETE EXAM campaign")
    if manifest.get("job_binding") != binding["recomputed"]:
        raise Stop(f"STOP: {out_dir} manifest job_binding differs from the recomputed B2 binding")
    if manifest.get("execution_label") != LABEL:
        raise Stop(f"STOP: label leak: {out_dir} execution_label {manifest.get('execution_label')!r} "
                   f"is not {LABEL}")
    if manifest.get("replay_marker") != REPLAY_MARKER:
        raise Stop(f"STOP: {out_dir} manifest lacks the replay marker {REPLAY_MARKER}")
    expected = {"phase": "b2", "candidate": MODEL_ALIAS, "mode": "off", "node": job["node"],
                "instance_seed": job["seed"]}
    for key, want in expected.items():
        if manifest.get(key) != want:
            raise Stop(f"STOP: {out_dir} manifest {key} {manifest.get(key)!r} != {want!r}")
    finals = manifest.get("final_audits") or []
    if len(finals) != 1 or finals[0].get("seeds") != list(AUDIT_SEEDS):
        raise Stop(f"STOP: {out_dir} must carry exactly the B2 final-audit seeds {AUDIT_SEEDS}")
    if finals[0].get("instance_id") != job["out"].rstrip("/").rsplit("/", 1)[-1]:
        raise Stop(f"STOP: {out_dir} final-audit instance id differs")
    if not isinstance(finals[0].get("final_y"), (int, float)) or isinstance(finals[0].get("final_y"), bool):
        raise Stop(f"STOP: {out_dir} final_y missing from the final audit")
    if (manifest.get("job_sha256")) != _sha_file(Path(out_dir) / "job.json"):
        raise Stop(f"STOP: {out_dir} manifest job_sha256 does not bind the rewritten job.json")
    _scan_forbidden_seeds(manifest, label=str(out_dir))
    return {"manifest": str(manifest_path), "manifest_sha256": _sha_file(manifest_path),
            "execution_label": manifest["execution_label"], "replay_marker": manifest["replay_marker"],
            "status": manifest["status"], "final_y": finals[0]["final_y"],
            "diagnostics": manifest.get("diagnostics"), "audit_seeds": finals[0]["seeds"]}


def _scan_forbidden_seeds(obj, label: str = "manifest") -> None:
    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("audit_seeds", "seeds") and isinstance(item, list):
                    if any(seed in RESERVED_B2_AUDIT_SEEDS for seed in item if isinstance(seed, int)):
                        raise Stop(f"STOP: reserved B.2 audit seed 7001-7010 found in {label}:{path}")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")
    walk(obj, "")


# ------------------------------------------------------------------ job record / packaging
def _record_base(spec: dict, binding: dict, prepared: list[dict], patch: dict) -> dict:
    return {"schema": RECORD_SCHEMA, "kind": KIND, "run_id": spec["run_id"], "chunk_id": spec["chunk_id"],
            "node": spec["node"], "label": LABEL, "replay_marker": REPLAY_MARKER,
            "label_rule": ("ENGINEERING_ONLY fixed by the replay spec and the reviewed label patch; "
                           "EVIDENCE/DRYRUN refused (a non-ENGINEERING label is a STOP)"),
            "paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT,
            "image_digest": IMAGE_DIGEST, "model_sha256": GGUF_SHA256,
            "b2_audits": "none (no B.2 audits; reserved audit seeds 7001-7010 untouched)",
            "audit_seeds": list(AUDIT_SEEDS), "output_use": OUTPUT_USE,
            "non_numeric_differences": lib.NON_NUMERIC_DIFFERENCES,
            "binding": binding, "label_patch": patch, "job_rewrites": prepared,
            "authority": _authority_pointer(), "layout": layout_record(spec),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def write_record(record: dict, path: Path) -> None:
    path.write_text(json.dumps(record, indent=1, allow_nan=False) + "\n")


def _authority_pointer() -> dict:
    """The external authority row (m6: it lives on the decisions branch, NOT in this branch's ancestry)."""
    return {"row": "R1-S2C3-DRIVER",
            "commit": "025bfc16477a3911ea461d7a6cfc85f3ea523d66",
            "ref": "origin/author-decisions-20261116b",
            "branch_ancestor": False,
            "ancestry_note": ("the decisions commit is external to this branch (merge-base 9ae6d877); the row is "
                              "not a run input, and the in-tree PLAN is the B2-bound 8709dce7 blob")}


def layout_record(spec: dict) -> dict:
    """The author-accepted 32k layout this job requests, plus the derived per-root timeout."""
    return {"walltime_s": spec["walltime_s"], "request_disk_kb": spec["request_disk_kb"],
            "request_memory_mb": spec["request_memory_mb"],
            "per_root_timeout_s": root_timeout_s(spec),
            "authority_row": "R1-SWEEP2-LAYOUT (same authority commit)",
            "basis": ("S2-C2 32k smoke measurement: 9,387 s per full 18-instance chunk, walltime 12,203 s, "
                      "disk 42,460,977 kB, memory 32,000 MB; used unchanged for the 4-root C3 replay")}


def root_timeout_s(spec: dict) -> int:
    """The per-root campaign deadline derived from the accepted job walltime (walltime - 600 s)."""
    return max(600, int(spec["walltime_s"]) - 600)


def server_record(spec: dict, server: dict) -> dict:
    """The server identity recorded in job_record.json (argv + the pinned manager settings, not just the log)."""
    extra = spec["server"]["extra_args"]
    return {"pid": server["pid"], "base_url": server["base_url"], "build": server["build"],
            "offloaded_layers": server["offloaded_layers"], "total_layers": server["total_layers"],
            "cuda_lines": server["cuda_lines"], "log": server["log"], "argv": server["argv"],
            "manager_settings": {"ctx": spec["server"]["ctx"], "n_gpu_layers": spec["server"]["n_gpu_layers"],
                                 "parallel": 1, "jinja": "--jinja" in extra,
                                 "thinking": _server_thinking(spec["server"]), "cache_prompt": False,
                                 "cache_type_k": extra[extra.index("--cache-type-k") + 1],
                                 "cache_type_v": extra[extra.index("--cache-type-v") + 1],
                                 "extra_args": list(extra), "alias": spec["model"]["alias"]}}


def package(cwd: Path) -> dict:
    """Write out.tar/work.tar + SHA256SUMS (the S2-C2 transfer/seal machinery)."""
    out, work = cwd / "out", cwd / "work"
    lib._tar_dir(out, cwd / "out.tar")
    lib._tar_dir(work, cwd / "work.tar")
    lib._write_sums(cwd)
    return {"out_tar_sha256": _sha_file(cwd / "out.tar"), "work_tar_sha256": _sha_file(cwd / "work.tar"),
            "sha256sums_sha256": _sha_file(cwd / "SHA256SUMS")}


# ------------------------------------------------------------------ prep / run
def prep(cwd: Path, spec: dict) -> dict:
    """Validate every declared input, recompute the binding, prepare both checkouts and apply the reviewed patches."""
    cwd = Path(cwd)
    staged = verify_pinned_inputs(cwd, spec)
    declared = load_declared_inputs(cwd, spec)
    local = verify_declared_inputs(cwd, spec, declared, cfg=staged["jobs"][ROOTS[0]]["authority_config"])
    paper = prepare_authorization_checkout(spec, cwd / "paper")
    harness_dest = cwd / "harness"
    if harness_dest.exists():
        raise Stop(f"STOP: scratch checkout {harness_dest} already exists (fresh scratch required)")
    lib.clone_at(spec["harness"]["repo"], HARNESS_COMMIT, harness_dest)
    if _git(harness_dest, "rev-parse", "HEAD") != HARNESS_COMMIT:
        raise Stop("STOP: harness checkout is not at the pinned B2 harness commit")
    if _git(harness_dest, "status", "--porcelain"):
        raise Stop("STOP: harness checkout is not clean")
    bind = verify_binding(cwd / "paper", staged["jobs"], spec)
    checkouts = verify_declared_inputs(cwd, spec, declared, paper_dir=cwd / "paper", harness_dir=harness_dest,
                                       cfg=staged["jobs"][ROOTS[0]]["authority_config"], binding=bind)
    cache = stage_openml_cache(cwd, declared, harness_dest)
    cache_report = verify_declared_inputs(cwd, spec, declared, paper_dir=cwd / "paper",
                                          harness_dir=harness_dest, installed_cache=cache)
    staged_patches = []
    for kind, rel, sha in (("label", PATCH_PATH, PATCH_SHA256), ("shim", SHIM_PATH, SHIM_SHA256)):
        staged_path = cwd / Path(rel).name
        if not staged_path.is_file():
            raise Stop(f"STOP: {kind} patch {rel} is not staged in the job sandbox")
        if _sha_file(staged_path) != sha:
            raise Stop(f"STOP: staged {kind} patch sha256 does not match the reviewed pin")
        staged_patches.append({"kind": kind, "path": staged_path})
    patch = apply_reviewed_patches(cwd / "paper", staged_patches, cwd / "work" / "replay_patch")
    criteria = cwd / "S2_C3_CRITERIA.md"
    if not criteria.is_file() or _sha_file(criteria) != CRITERIA_SHA256:
        raise Stop("STOP: the pre-declared criteria file is missing or its sha256 pin does not match")
    pins = {root: _sha_file(cwd / STAGED_JOB.format(root=root)) for root in ROOTS}
    after = verify_pinned_inputs(cwd, spec)  # the staged pinned roots must be untouched by preparation
    if after["sha256sums_sha256"] != staged["sha256sums_sha256"]:
        raise Stop("STOP: staged replay inputs changed during preparation")
    after_local = verify_declared_inputs(cwd, spec, declared, cfg=staged["jobs"][ROOTS[0]]["authority_config"])
    return {"staged": {"sha256sums_sha256": staged["sha256sums_sha256"], "files": staged["files"]},
            "jobs": staged["jobs"], "pins": pins, "binding": bind, "paper": paper,
            "harness": {"path": str(harness_dest), "commit": HARNESS_COMMIT},
            "patch": patch, "criteria_sha256": CRITERIA_SHA256,
            "declared_inputs": {"manifest": declared, "report": checkouts, "local": local,
                                "after_local": after_local, "openml_cache": cache,
                                "cache_report": cache_report}}


def _bypass_dispositions() -> dict[str, str]:
    """Exactly what the reviewed shim bypasses and how the B2 authorization semantics are preserved."""
    return {
        "authorization_input:stage_a_table":
            "read from the declared sha256-pinned copy S2C3_IN_stage_a_table_t7h8.json (same sha256 as "
            "authority_config.stage_a_table_sha256) instead of the TASL-absolute /home/dowling path",
        "authorization_input:stage_a_amendment_table":
            "read from the declared sha256-pinned copy S2C3_IN_stage_a_amendment_table_t7j10.json (same sha256 as "
            "authority_config.stage_a_amendment_table_sha256) instead of the TASL-absolute path",
        "authorization_input:stage_a_amendment_acceptance":
            "committed relative path docs/r1/reports/OPS_O1_20261104.md resolves in the pinned checkout; the "
            "sha256 check is unchanged",
        "authorization_input:rule":
            "committed relative path r1/exam/rules/x5_rule_v2.yaml resolves in the pinned checkout; unchanged",
        "host_check":
            "TASL-2/TASL-7 + /home/dowling{models,work} + out-under-work_dir replaced by: must NOT be an approved "
            "exam host, out must be inside the declared job sandbox, and the production DRYRUN-env refusal plus the "
            "author 100 GB disk floor are KEPT (the floor is applied to the declared job sandbox). Only the TASL "
            "host/GPU and /home/dowling work-dir pins are dropped (the L40S deployment check is off-TASL).",
        "require_worker_host":
            "the actual-node == cfg.host TASL-7 pin is replaced by the same off-TASL + sandbox + DRYRUN-env + disk-"
            "floor check; the job's host/gpu fields are still compared to the committed B2 configuration and the "
            "authorization note, and the physical L40S host/GPU is deliberately rebound from the authorization's "
            "TASL-7/GUID (disclosed in the job record's host_rebind block)",
        "verify_b1_worker_input":
            "runs unchanged apart from the Stage A relocation inside author_gate (same committed config, note bytes, "
            "PLAN rows, rule/b1-analysis digests, seed/host/gpu bindings)",
        "authorized_candidate":
            "the re-reviewed additions-only hunk in r1/scripts/exam_runner.py:stage_a_pass_set resolves BOTH "
            "TASL-absolute Stage A tables to the declared sha256-pinned copies after the same sha256 check; "
            "authorized_b1_observer -> _authorized_candidate -> stage_a_pass_set then resolves the registry footprint "
            "exactly as on TASL (no trial/manager/scoring code touched)",
        "out_under_work_dir":
            "the declared sandbox rewrite is admitted by the replay host check (out inside the job sandbox); the "
            "B2 /home/dowling/exam-x/work rule is not applicable off TASL",
        "openml_data_cache":
            "the verified cache is shipped as the declared deterministic archive S2C3_IN_openml_cache.tar.gz and "
            "installed into the pinned harness clone at the exact path the campaign reads (gitignored)",
    }


def expected_tasl_blockers(node: str) -> frozenset[str]:
    """The exact refusal set the unshimmed TASL walk must report for this node (no more, no fewer)."""
    if node not in NODES:
        raise Stop(f"STOP: unknown node {node!r}")
    return TASL_BLOCKER_GATES


def _preflight_status(expected: frozenset, got: frozenset, failed: dict) -> tuple[str, list[str], list[str]]:
    """PASS only when the unshimmed walk reports exactly the reviewed TASL set and every shimmed gate passes."""
    missing = sorted(expected - got)
    unexpected = sorted(got - expected)
    status = "PASS" if not missing and not unexpected and not failed and got else "STOP"
    return status, missing, unexpected


def preflight(cwd: Path, spec: dict, prepared: dict) -> dict:
    """Pre-flight the B2 gates twice: unshimmed (exactly the reviewed TASL refusals) and shimmed (all must pass)."""
    cwd = Path(cwd)
    node = spec["node"]
    job0 = prepared["jobs"][ordered_roots(node)[0]]
    probe_job = dict(job0)
    probe_job["out"] = str((cwd / "out" / ordered_roots(node)[0]).resolve())
    probe_job["base_url"] = "http://127.0.0.1:1/v1"  # a gate probe never serves; the gates do not use base_url
    temp_job = cwd / "work" / "preflight_job.json"
    temp_job.parent.mkdir(parents=True, exist_ok=True)
    temp_job.write_text(json.dumps(probe_job, indent=2) + "\n")
    campaign_source = Path(prepared["patch"]["patched_campaign_source"])
    runtime_source = Path(prepared["patch"]["patched_runtime_source"])
    runner_source = Path(prepared["patch"]["patched_runner_source"])
    tasl_gate = run_gate_probe(cwd / "paper", cwd / "harness", temp_job, campaign_source, runtime_source,
                               runner_source)
    blockers = collect_preflight_blockers(spec, job0["authority_config"], Path(probe_job["out"]),
                                          cwd / "paper", cwd / "harness", tasl_gate)
    shim_gate = run_gate_probe(cwd / "paper", cwd / "harness", temp_job, campaign_source, runtime_source,
                               runner_source, env_extra=replay_env(cwd))
    expected = expected_tasl_blockers(node)
    got = frozenset(entry["gate"] for entry in blockers)
    for label, result in (("unshimmed", tasl_gate), ("shimmed", shim_gate)):
        if frozenset(result["checks"]) != PROBE_GATES:
            raise Stop(f"STOP: the {label} gate probe did not exercise exactly {sorted(PROBE_GATES)}; "
                       f"got {sorted(result['checks'])}")
    failed = {name: result for name, result in shim_gate["checks"].items() if not result.get("ok")}
    status, missing, unexpected = _preflight_status(expected, got, failed)
    dispositions = _bypass_dispositions()
    bypassed = [{"gate": entry["gate"], "tasl_refusal": entry.get("reason"),
                 "disposition": dispositions.get(entry["gate"], "NOT REVIEWED")} for entry in blockers]
    return {"status": status, "tasl_blockers": blockers, "tasl_gate": tasl_gate,
            "expected_tasl_blockers": sorted(expected), "missing_tasl_blockers": missing,
            "unexpected_tasl_blockers": unexpected, "bypassed": bypassed,
            "shim_gates": shim_gate["checks"], "shim_probe_rc": shim_gate["probe_rc"],
            "shim_failed": failed,
            "shim_gate_names": sorted(shim_gate["checks"]), "probe_gates": sorted(PROBE_GATES),
            "out_under_work_dir": not any(b["gate"] == "out_under_work_dir" for b in blockers),
            "shim_scope": prepared["patch"]["shim_scope"]}


CRASH_MARKERS = ("Traceback (most recent call last)", "ModuleNotFoundError", "ImportError", "SyntaxError")
WORKER_FAILURE_MARGIN = 0.05
SWEEP1_WORKER_SUCCESS_RATE = 5287 / 5813  # frozen sweep-1 corpus, main: 5,287/5,813


def worker_audit(cwd: Path, roots: list[str]) -> dict:
    """A campaign manifest can look complete while every worker run crashed (the 32k-smoke PATH failure).
    Inspect the node run.log files: STOP if no worker ran, if every run crashed, or if the crash rate exceeds
    sweep-1's 9.05% + 5 pp."""
    logs = []
    for root in roots:
        logs.extend(sorted((Path(cwd) / "out" / root).rglob("run.log")))
    crashed = [p for p in logs if any(m in p.read_text(errors="replace") for m in CRASH_MARKERS)]
    total = len(logs); ok = total - len(crashed)
    rate = (len(crashed) / total) if total else 1.0
    audit = {"total_run_logs": total, "crashed": len(crashed), "assumed_successful": ok,
             "crash_rate": round(rate, 6), "sweep1_success_rate": round(SWEEP1_WORKER_SUCCESS_RATE, 6),
             "max_crash_rate": round(1 - SWEEP1_WORKER_SUCCESS_RATE + WORKER_FAILURE_MARGIN, 6)}
    if total == 0:
        raise Stop("STOP: no worker run.log found in any campaign output; no training evidence")
    if ok == 0:
        raise Stop(f"STOP: all {total} worker runs crashed (e.g. {crashed[0]}); no training evidence")
    if rate > audit["max_crash_rate"]:
        raise Stop(f"STOP: worker crash rate {rate:.3f} exceeds sweep-1 {1-SWEEP1_WORKER_SUCCESS_RATE:.3f} "
                   f"+ {WORKER_FAILURE_MARGIN} (max {audit['max_crash_rate']:.3f})")
    return audit


def _stop_record(cwd: Path, spec: dict, exc: Exception, status: str) -> dict:
    """A minimal STOP record so an early refusal is still a transferred, reviewable artifact."""
    declared_stop = None
    path = Path(cwd) / "DECLARED_INPUTS_STOP.json"
    if path.is_file():
        try:
            declared_stop = json.loads(path.read_text())
        except json.JSONDecodeError:
            declared_stop = {"unreadable": True}
    record = {"schema": RECORD_SCHEMA, "kind": KIND, "run_id": spec["run_id"], "chunk_id": spec["chunk_id"],
              "node": spec["node"], "label": LABEL, "replay_marker": REPLAY_MARKER,
              "paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT, "image_digest": IMAGE_DIGEST,
              "model_sha256": GGUF_SHA256,
              "b2_audits": "none (no B.2 audits; reserved audit seeds 7001-7010 untouched)",
              "audit_seeds": list(AUDIT_SEEDS), "output_use": OUTPUT_USE, "status": status,
              "driver_shim_sha256": SHIM_SHA256, "declared_inputs_sha256": DECLARED_SHA256,
              "authority": _authority_pointer(), "layout": layout_record(spec),
              "stop": f"STOP: {type(exc).__name__}: {exc}",
              "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if declared_stop is not None:
        record["declared_inputs_stop"] = declared_stop
    write_record(record, Path(cwd) / "job_record.json")
    try:
        package(Path(cwd))
    except Exception as package_error:  # noqa: BLE001 - packaging failure must not hide the STOP
        record["package_error"] = f"{type(package_error).__name__}: {package_error}"
        write_record(record, Path(cwd) / "job_record.json")
    return record


def run_replay(cwd: Path, spec: dict) -> dict:
    """Full replay job: prepare, pre-flight the B2 gates, then (only if all pass) serve and run the 4 roots."""
    cwd = Path(cwd)
    if (cwd / "job_record.json").is_file() and (cwd / "job_record.json").stat().st_size:
        raise Stop("STOP: a replay attempt already exists here; no retry (retain everything)")
    try:
        prepared = prep(cwd, spec)
    except Exception as exc:  # noqa: BLE001 - any preparation error is a STOP with retained outputs
        _stop_record(cwd, spec, exc, "STOP_PREP")
        raise Stop(f"STOP: replay preparation failed: {type(exc).__name__}: {exc}") from None
    binding = {key: prepared["binding"][key] for key in
               ("recorded", "recomputed", "unchanged_by_rewrite", "registry_sha256", "rule_sha256",
                "value_grids_sha256", "config_equals_committed", "method")}
    record = _record_base(spec, binding, [], prepared["patch"])
    record["driver_shim"] = {"path": SHIM_PATH, "patch_sha256": SHIM_SHA256, "targets": list(SHIM_TARGETS),
                             "patched_source_sha256": prepared["patch"]["patched_source_sha256"],
                             "scope": prepared["patch"]["shim_scope"],
                             "inert_without": REPLAY_DECLARED_ENV,
                             "reviewed": ("additions only to r1/exam/runtime.py + r1/exam/campaign.py + "
                                          "r1/scripts/exam_runner.py (the re-reviewed stage_a_pass_set hunk); no "
                                          "trial, manager, scoring or audit code touched")}
    declared_report = prepared["declared_inputs"]
    record["declared_inputs"] = {
        "path": DECLARED_PATH, "staged": DECLARED_STAGED, "manifest_sha256": DECLARED_SHA256,
        "items_declared": len(declared_report["manifest"].get("items") or []),
        "items_verified": len(declared_report["report"]["verified"]),
        "verified": declared_report["report"]["verified"],
        "local": declared_report["local"], "after_local": declared_report["after_local"],
        "openml_cache": declared_report["openml_cache"], "cache_report": declared_report["cache_report"],
        "independent_of_tasl": True,
        "stop_if_missing_or_mismatched": True}
    record["input_pins"] = {"replay_inputs_sha256sums_sha256": prepared["staged"]["sha256sums_sha256"],
                            "files_verified": prepared["staged"]["files"], "criteria_sha256": CRITERIA_SHA256,
                            "label_patch_sha256": PATCH_SHA256, "driver_shim_sha256": SHIM_SHA256,
                            "declared_inputs_sha256": DECLARED_SHA256, "job_json_pins": prepared["pins"]}
    record["paper_checkout"] = prepared["paper"]
    record["harness"] = prepared["harness"]
    server = None
    roots: list[dict] = []
    try:
        record["image"] = lib.image_identity(spec)
        record["host"] = lib.host_identity()
        record["gpu"] = lib.gpu_identity()
        record["cpu"] = lib.cpu_identity()
        gate = preflight(cwd, spec, prepared)
        record["preflight"] = gate
        if gate["status"] != "PASS":
            record["status"] = "STOP_B2_AUTHORIZATION_GATE"
            record["roots"] = roots
            record["stop"] = ("STOP: the reviewed shim did not make every B2 authorization gate pass, or the "
                              "unshimmed refusals were not the reviewed TASL set; no server started. Retain "
                              "everything and report to the author (see S2_C3_DRIVER.md).")
            raise Stop(record["stop"])
        record["model"] = lib.fetch_model(spec["model"], cwd / "model.gguf")
        server = lib.start_server(spec, cwd / "model.gguf", cwd / "llama-server.log")
        record["server"] = server_record(spec, server)
        # m1/O3 disclosure: the authorization binds TASL-7 + its GPU UUID; the ENGINEERING check is deliberately
        # rebound to the L40S class and the recorded job host stays TASL-7 (the config binding is unchanged).
        record["host_rebind"] = {
            "authorization_host": prepared["jobs"][ROOTS[0]]["authority_config"].get("host"),
            "authorization_gpu_uuid": prepared["jobs"][ROOTS[0]]["authority_config"].get("gpu_uuid"),
            "recorded_job_host": prepared["jobs"][ROOTS[0]].get("host"),
            "run_host": record["host"],
            "run_gpu": record["gpu"],
            "note": ("physical host/GPU rebound to the L40S class by the reviewed shim; the recorded job host/gpu "
                     "fields still equal the committed B2 configuration and the authorization note, and the B2 "
                     "binding is unchanged (out/base_url are not binding inputs)")}
        base_url = server["base_url"]
        prepared["job_rewrites"] = prepare_root_jobs(cwd, spec, spec["node"], prepared["pins"], base_url,
                                                     prepared["staged"]["sha256sums_sha256"])
        record["job_rewrites"] = prepared["job_rewrites"]
        record["roots"] = roots
        for root in ordered_roots(spec["node"]):
            job_path = cwd / "out" / root / "job.json"
            job = json.loads(job_path.read_text())
            run = run_one_campaign(cwd / "paper", cwd / "harness", job_path,
                                   Path(prepared["patch"]["patched_campaign_source"]),
                                   Path(prepared["patch"]["patched_runtime_source"]),
                                   Path(prepared["patch"]["patched_runner_source"]), base_url,
                                   cwd / "work" / "logs" / f"{root}.campaign.log",
                                   root_timeout_s(spec), cwd)
            entry = {"instance_id": root, "job_json_sha256": _sha_file(job_path), **run}
            roots.append(entry)
            if run["returncode"] != 0:
                raise Stop(f"STOP: root campaign {root} rc={run['returncode']}"
                           f"{' (audit stop signal)' if run.get('stop_signal') else ''}; outputs kept (no retry)")
            entry.update(validate_campaign_manifest(cwd / "out" / root, job, binding, spec))
            if any(seed in RESERVED_B2_AUDIT_SEEDS for seed in entry["audit_seeds"]):
                raise Stop("STOP: a reserved B.2 audit seed appeared in a replay manifest")
        record["worker_audit"] = worker_audit(cwd, ordered_roots(spec["node"]))
        record["declared_inputs"]["post_run"] = verify_declared_inputs(
            cwd, spec, declared_report["manifest"], cfg=prepared["jobs"][ROOTS[0]]["authority_config"])
        record["wall_s"] = round(sum(entry["wall_s"] for entry in roots), 1)
        record["throughput"] = {"replay_total_wall_s": record["wall_s"],
                                "b2_gpu_hours_off": B2_GPU_HOURS_OFF,
                                "limit_s": round(2 * B2_GPU_HOURS_OFF * 3600, 1)}
        record["status"] = "COMPLETE"
    except (Stop, lib.Stop) as exc:
        record["roots"] = record.get("roots") or roots
        record["status"] = record.get("status") or "STOP"
        record["stop"] = record.get("stop") or f"STOP: {exc}"
        record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_record(record, cwd / "job_record.json")
        package(cwd)
        raise Stop(str(exc)) from None
    except Exception as exc:  # noqa: BLE001 - an unexpected error is a STOP; retain everything
        record["roots"] = record.get("roots") or roots
        record["status"] = "STOP_ERROR"
        record["stop"] = f"STOP: {type(exc).__name__}: {exc}"
        record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        write_record(record, cwd / "job_record.json")
        package(cwd)
        raise Stop(record["stop"]) from None
    finally:
        if server is not None:
            lib._kill(server["proc"])
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_record(record, cwd / "job_record.json")
    record["package"] = package(cwd)
    write_record(record, cwd / "job_record.json")
    package(cwd)  # recompute SHA256SUMS over the final record (the first pass hashed the pre-final record)
    return record


# ------------------------------------------------------------------ seal (operator side; /ceph)
def seal_replay(job_output: Path, run_id: str, chunk_id: str) -> dict:
    """Seal one transferred replay job into /ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/ (no overwrite).

    A STOP output may be sealed too (retention is required by the STOP policy); the receipt records the
    record's status verbatim so a sealed STOP is never mistaken for a COMPLETE run result.
    """
    src = Path(job_output).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("schema") != RECORD_SCHEMA:
        raise Stop("STOP: job record is not an S2-C3 replay record")
    if record.get("run_id") != run_id or record.get("chunk_id") != chunk_id:
        raise Stop("STOP: job record does not match the requested run/chunk")
    if record.get("label") != LABEL or record.get("replay_marker") != REPLAY_MARKER:
        raise Stop("STOP: job record is not ENGINEERING_ONLY with the replay marker")
    if not isinstance(record.get("image_digest"), str) or not record["image_digest"].startswith("ghcr.io/"):
        raise Stop("STOP: job record has no pinned image digest")
    if not isinstance(record.get("host"), dict) or not record["host"].get("fqdn"):
        raise Stop("STOP: job record has no host identity")
    patch = record.get("label_patch") or {}
    if (patch.get("patch_sha256") or patch.get("label_patch_sha256")) != PATCH_SHA256:
        raise Stop("STOP: job record does not bind the reviewed label patch")
    shim = record.get("driver_shim") or {}
    if shim.get("patch_sha256") != SHIM_SHA256:
        raise Stop("STOP: job record does not bind the reviewed replay driver shim")
    if shim.get("patched_source_sha256") != PATCHED_SOURCE_SHA256:
        raise Stop("STOP: job record does not bind the reviewed patched-source pins")
    declared = record.get("declared_inputs") or {}
    if declared.get("manifest_sha256") != DECLARED_SHA256:
        raise Stop("STOP: job record does not bind the declared-inputs manifest")
    if declared.get("items_verified") != declared.get("items_declared"):
        raise Stop("STOP: job record's declared-inputs audit did not verify every item")
    if declared.get("independent_of_tasl") is False:
        raise Stop("STOP: job record's declared inputs are not TASL-independent")
    sums = src / "SHA256SUMS"
    if not sums.is_file():
        raise Stop("STOP: job output has no SHA256SUMS")
    check = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=str(src), capture_output=True, text=True)
    if check.returncode != 0:
        raise Stop(f"STOP: transferred SHA256SUMS verification failed: {check.stdout[-1500:]}"
                   f"{check.stderr[-1500:]}")
    try:
        target = lib._sealed_target(run_id, chunk_id)
    except lib.Stop as exc:
        raise Stop(str(exc)) from None
    if target.exists():
        raise Stop(f"STOP: sealed target exists; no overwrite ({target})")
    target.mkdir(parents=True, mode=0o700)
    for name in ("job_record.json", "SHA256SUMS", "llama-server.log"):
        path = src / name
        if path.exists():
            shutil.copy2(path, target / name)
    for name in ("out", "work"):
        tar = src / f"{name}.tar"
        if tar.exists():
            (target / name).mkdir(mode=0o700)
            subprocess.run(["tar", "-xf", str(tar), "-C", str(target / name)], check=True)
    marker = target / "ENGINEERING_ONLY.txt"
    marker.write_text(f"S2-C3 L40S deployment check - ENGINEERING_ONLY, not evidence.\n"
                      f"run_id={run_id}\nchunk_id={chunk_id}\nlabel={LABEL}\nreplay_marker={REPLAY_MARKER}\n"
                      f"label_patch_sha256={PATCH_SHA256}\n"
                      f"driver_shim_sha256={SHIM_SHA256}\n"
                      f"patched_source_sha256={json.dumps(PATCHED_SOURCE_SHA256, sort_keys=True)}\n"
                      f"declared_inputs_sha256={DECLARED_SHA256}\n"
                      f"record_status={record.get('status')}\n")
    lines = []
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{_sha_file(path)}  {path.relative_to(target)}")
    (target / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    receipt = {"schema": SEAL_RECEIPT_SCHEMA, "run_id": run_id, "chunk_id": chunk_id,
               "sealed_path": str(target), "label": LABEL, "replay_marker": REPLAY_MARKER,
               "image_digest": record["image_digest"], "model_sha256": record["model_sha256"],
               "paper_commit": record["paper_commit"], "harness_commit": record["harness_commit"],
               "label_patch_sha256": PATCH_SHA256, "driver_shim_sha256": SHIM_SHA256,
               "patched_source_sha256": PATCHED_SOURCE_SHA256,
               "declared_inputs_sha256": DECLARED_SHA256, "host": record["host"].get("fqdn"),
               "record_status": record.get("status"),
               "complete_run_result": record.get("status") == "COMPLETE",
               "engineering_only_marker": "ENGINEERING_ONLY.txt",
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


# ------------------------------------------------------------------ operator-side declared-input audit (no run)
def _pinned_blob(repo_root: Path, rel: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo_root), "show", f"{PAPER_COMMIT}:{rel}"])


def audit_declared_inputs(repo_root: Path, spec_path: Path) -> dict:
    """Operator-side declared-inputs audit from this checkout: every local file + committed paper blob + pin.

    No clone, no server, no HTCondor.  Harness-tree items and the installed OpenML cache are explicitly reported
    as *deferred to job start* (they are verified inside the pinned harness clone by the driver) rather than
    silently counted as verified.
    """
    repo_root = Path(repo_root)
    spec = validate_spec(load_spec(Path(spec_path)))["spec"]
    manifest_path = repo_root / spec["declared_inputs"]["path"]
    if not manifest_path.is_file():
        raise Stop(f"STOP: declared-inputs manifest missing ({manifest_path})")
    if _sha_file(manifest_path) != spec["declared_inputs"]["sha256"]:
        raise Stop("STOP: declared-inputs manifest sha256 != the spec pin")
    declared = json.loads(manifest_path.read_text())
    if declared.get("schema") != DECLARED_SCHEMA or declared.get("label") != LABEL \
            or declared.get("replay_marker") != REPLAY_MARKER:
        raise Stop("STOP: declared-inputs manifest is not the ENGINEERING_ONLY replay manifest")
    items = _declared_items(declared)
    failures, verified, deferred = [], [], []
    for item in items:
        item_id, kind = item["id"], item.get("kind")
        try:
            if kind == "file":
                path = repo_root / item["path"]
                if not path.is_file():
                    raise Stop(f"{path} missing")
                got = _sha_file(path)
                if got != item.get("sha256"):
                    raise Stop(f"sha256 {got} != declared {item.get('sha256')}")
                verified.append({"id": item_id, "kind": kind, "sha256": got,
                                 "path": item["path"], "staged": item.get("staged")})
            elif kind == "paper_blob":
                try:
                    blob = _pinned_blob(repo_root, item["path"])
                except (OSError, subprocess.CalledProcessError) as exc:
                    raise Stop(f"pinned paper commit {PAPER_COMMIT} not available in this clone: {exc}") from None
                got = _sha_bytes(blob)
                if got != item.get("sha256"):
                    raise Stop(f"committed blob sha256 {got} != declared {item.get('sha256')}")
                verified.append({"id": item_id, "kind": kind, "sha256": got, "commit": PAPER_COMMIT})
            elif kind == "value":
                want = _value_pin(item_id)
                got = {key: item.get(key) for key in want}
                if got != want:
                    raise Stop(f"declared value {got!r} != the pinned value {want!r}")
                verified.append({"id": item_id, "kind": kind, "value": got})
            elif kind == "staged_tree":
                declared_tree = _tree_sha([(row["path"], row["sha256"]) for row in item.get("files") or []])
                if declared_tree != item.get("tree_sha256"):
                    raise Stop("declared cache file list does not reproduce tree_sha256")
                verified.append({"id": item_id, "kind": kind, "tree_sha256": declared_tree,
                                 "files": len(item.get("files") or [])})
                deferred.append({"id": item_id, "why": "installed-cache digest is verified at job start by "
                                                      "stage_openml_cache inside the pinned harness clone"})
            elif kind == "harness_tree":
                deferred.append({"id": item_id,
                                 "why": "verified at job start against the cloned pinned harness (a3fedbb)"})
            else:
                raise Stop(f"unknown declared-item kind {kind!r}")
        except Stop as exc:
            failures.append({"id": item_id, "kind": kind, "reason": str(exc).replace("STOP: ", "")})
    cfg = json.loads((repo_root / INPUTS_DIR / ROOTS[0] / "job.json").read_text())["authority_config"]
    try:
        registry_sha = _sha_bytes(_pinned_blob(repo_root, cfg["registry"]))
        grids_sha = _sha_bytes(_pinned_blob(repo_root, cfg["value_grids"]))
        recomputed = recompute_binding(cfg, registry_sha, grids_sha)
    except (OSError, subprocess.CalledProcessError) as exc:
        failures.append({"id": "binding", "kind": "value", "reason": f"pinned commit unavailable: {exc}"})
        registry_sha = grids_sha = recomputed = None
    if recomputed != BINDING:
        failures.append({"id": "binding", "kind": "value",
                         "reason": f"recomputed {recomputed!r} != the recorded B2 binding {BINDING}"})
    binding = {"recomputed": recomputed, "registry_sha256": registry_sha, "value_grids_sha256": grids_sha}
    failures.extend(_declared_pin_failures(declared, cfg, binding, None))
    for key, rel in (("authorization_note_sha256", B2_AUTHORIZATION_NOTE), ("plan_sha256", "docs/r1/PLAN.md")):
        try:
            got = _sha_bytes(_pinned_blob(repo_root, rel))
        except (OSError, subprocess.CalledProcessError):
            continue
        if declared["pins"].get(key) != got:
            failures.append({"id": f"pin:{key}", "kind": "blocker",
                             "reason": f"{declared['pins'].get(key)!r} != committed {got!r}"})
    return {"schema": "s2_c3_declared_inputs_audit/1", "manifest_sha256": _sha_file(manifest_path),
            "manifest_path": str(manifest_path), "paper_commit": PAPER_COMMIT,
            "harness_commit": HARNESS_COMMIT, "items": len(items), "verified": verified,
            "deferred_to_job_start": deferred, "failures": failures, "binding": binding,
            "tasl_only_items_shipped": [item["id"] for item in items
                                        if str(item.get("source", "")).startswith("TASL-7")],
            "note": ("the three TASL-only inputs (Stage A tables, Stage A prompts) and the OpenML caches are copied "
                     "read-only from TASL-7 and shipped in this branch; the job verifies the same sha256 values "
                     "again, so no TASL access is needed at run time. The only run-time network fetches are the "
                     "three identity-pinned artifacts (paper clone 8709dce7, harness clone a3fedbb, 19.6 GB GGUF), "
                     "each commit/sha-verified; there is no unpinned download")}


# ------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("spec")
    p = sub.add_parser("prep")
    p.add_argument("spec")
    r = sub.add_parser("run")
    r.add_argument("spec")
    au = sub.add_parser("audit")
    au.add_argument("spec")
    pf = sub.add_parser("preflight")
    pf.add_argument("spec")
    s = sub.add_parser("seal")
    s.add_argument("job_output")
    s.add_argument("--run-id", required=True)
    s.add_argument("--chunk-id", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "audit":
        report = audit_declared_inputs(HERE.parent, Path(a.spec))
        print(json.dumps(report, indent=1))
        return 0 if not report["failures"] else 2
    if a.cmd == "preflight":
        validated = validate_spec(load_spec(Path(a.spec)))
        prepared = prep(Path.cwd(), validated["spec"])
        gate = preflight(Path.cwd(), validated["spec"], prepared)
        print(json.dumps(gate, indent=1))
        return 0 if gate["status"] == "PASS" else 2
    if a.cmd == "validate":
        validated = validate_spec(load_spec(Path(a.spec)))
        staged = verify_pinned_inputs(Path.cwd(), validated["spec"])
        declared = load_declared_inputs(Path.cwd(), validated["spec"])
        print(json.dumps({"ok": True, "run_id": validated["run_id"], "node": validated["node"],
                          "label": LABEL, "roots": len(ordered_roots(validated["node"])),
                          "inputs_verified": staged["files"],
                          "declared_inputs_items": len(_declared_items(declared)),
                          "driver_shim_sha256": SHIM_SHA256,
                          "declared_inputs_sha256": DECLARED_SHA256}))
        return 0
    if a.cmd == "prep":
        validated = validate_spec(load_spec(Path(a.spec)))
        result = prep(Path.cwd(), validated["spec"])
        print(json.dumps({"ok": True, "binding": result["binding"]["recomputed"],
                          "patched_source_sha256": result["patch"]["patched_source_sha256"],
                          "authorization_checkout_clean": True}, indent=1))
        return 0
    if a.cmd == "run":
        validated = validate_spec(load_spec(Path(a.spec)))
        record = run_replay(Path.cwd(), validated["spec"])
        print(json.dumps({"ok": True, "status": record["status"], "label": record["label"],
                          "host": record["host"]["fqdn"], "gpu": record["gpu"]["name"],
                          "wall_s": record.get("wall_s")}, indent=1))
        return 0
    print(json.dumps(seal_replay(Path(a.job_output), a.run_id, a.chunk_id), indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
