#!/usr/bin/env python3
"""S2-C3 L40S deployment check — replay of the 12 recorded B2 thinking-off roots (ENGINEERING, no evidence).

One job == one B2 node (3 nodes x 4 recorded instance seeds 9011-9014). The job validates a replay spec
(`s2_c3_replay/v1`, all pins fixed), verifies the pinned B2 root inputs against their SHA256SUMS, prepares the 4
`job.json` copies rewriting ONLY `out` (sandbox) and `base_url` (the owned local server), proves the B2 configuration
`binding` still recomputes exactly as the B2 code computes it, prepares a paper checkout at the pinned B2 commit
`8709dce7` (clean; the authorization checkout) plus a sandbox worktree where the reviewed label patch is applied,
pre-flights the exact B2 authorization gates the campaign driver will run, and only when every gate passes starts ONE
owned llama-server (the 32k exam setting) and runs the 4 root campaigns sequentially. The campaign is executed as
`r1.exam.campaign` with the patch source shadow-executed in the module namespace, so the authorization checkout stays
byte-identical to the pinned commit the B2 authorization binds. Every refusal is a STOP: no bypass, no retry.

The reviewed execution-label patch (`s2_c3_label_patch.diff`) changes only the campaign `execution_label` to
ENGINEERING_ONLY and adds `replay_marker`; it cannot change trial/audit logic and its scope is checked here. Raw
labels are never read; no B.2 audit runs and audit seeds 7001-7010 are refused.
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
    if "enable_thinking" not in extra[extra.index("--chat-template-kwargs") + 1]:
        raise Stop("STOP: --chat-template-kwargs must disable thinking")
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

    criteria = _get(spec, "criteria")
    _exact(_text(_get(criteria, "path"), "criteria.path"), CRITERIA_PATH, "criteria.path")
    _exact(_text(_get(criteria, "sha256"), "criteria.sha256", SHA), CRITERIA_SHA256,
           "criteria.sha256 (the pre-declared criteria pin)")

    req = _get(spec, "requirements")
    _exact(_get(req, "cloud_site"), lib.CLOUD_SITE, "requirements.cloud_site")
    _exact(_get(req, "gpu_device_name"), lib.GPU_MODEL, "requirements.gpu_device_name")
    _exact(_get(req, "arch"), "X86_64", "requirements.arch")
    _exact(_get(req, "opsys"), "LINUX", "requirements.opsys")
    _exact(_get(req, "min_cpus"), lib.MIN_CPUS, "requirements.min_cpus")
    _exact(_get(req, "cpu_family"), lib.CPU_FAMILY, "requirements.cpu_family")
    _exact(_get(req, "cpu_model_number"), lib.CPU_MODEL_NUMBER, "requirements.cpu_model_number")
    _exact(_get(req, "cpu_model_contains"), lib.CPU_MODEL_CONTAINS, "requirements.cpu_model_contains")
    if "requires_etp_ceph" in req:
        raise Stop("STOP: NEMO2 slots do not advertise ProvidesEtpCeph; outputs transfer to the submit host")

    wall = spec.get("walltime_s")
    if type(wall) is not int or not 3600 <= wall <= 86400:
        raise Stop("STOP: walltime_s must be an integer in [3600, 86400]")
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


# ------------------------------------------------------------------ exact B2 authorization gate pre-flight
GATE_PROBE = r"""
import json, sys, traceback
job = json.load(open(sys.argv[1]))
patched = sys.argv[2]
import r1.exam.campaign as c
exec(compile(open(patched).read(), c.__file__, "exec"), c.__dict__)
from r1.exam.runtime import host_check, b1_harness_sources
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
print(json.dumps(results))
"""


def run_gate_probe(paper_dir: Path, harness_dir: Path, job_path: Path, patched_source: Path,
                   env_extra: dict | None = None) -> dict:
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
    if env_extra:
        env.update(env_extra)
    res = subprocess.run([sys.executable, "-B", str(probe), str(job_path), str(patched_source)],
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
def campaign_env(paper_dir: Path, harness_dir: Path, base_url: str, stop_fd: int | None = None) -> dict:
    env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()), AR_HARNESS_ROOT=str(harness_dir.resolve()),
               LLAMACPP_BASE_URL=base_url, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    env.pop("LLAMACPP_CACHE_PROMPT", None)
    env.pop("LLAMACACHE_PROMPT", None)
    if stop_fd is not None:
        env["R1_B1_STOP_FD"] = str(stop_fd)
    return env


SHADOW_RUNNER = (
    "import sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import r1.exam.campaign as campaign\n"
    "source = open(sys.argv[2]).read()\n"
    "exec(compile(source, campaign.__file__, 'exec'), campaign.__dict__)\n"
    "campaign.main(['--job', sys.argv[3]])\n"
)


def run_one_campaign(paper_dir: Path, harness_dir: Path, job_path: Path, patched_source: Path,
                     base_url: str, log_path: Path, timeout_s: int) -> dict:
    """Run one root campaign exactly as the B2 parent runs it, with the reviewed label patch shadow-executed."""
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
                 str(patched_source), str(job_path)],
                cwd=str(paper_dir.resolve()), env=campaign_env(paper_dir, harness_dir, base_url, write_fd),
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
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def write_record(record: dict, path: Path) -> None:
    path.write_text(json.dumps(record, indent=1, allow_nan=False) + "\n")


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
    """Validate the pinned inputs, recompute the binding, prepare both checkouts and apply the label patch."""
    cwd = Path(cwd)
    staged = verify_pinned_inputs(cwd, spec)
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
    staged_patch = cwd / PATCH_PATH.split("/")[-1]
    if not staged_patch.is_file():
        raise Stop(f"STOP: label patch {PATCH_PATH} is not staged in the job sandbox")
    patch = apply_label_patch(cwd / "paper", staged_patch, cwd / "work" / "label_patch")
    criteria = cwd / "S2_C3_CRITERIA.md"
    if not criteria.is_file() or _sha_file(criteria) != CRITERIA_SHA256:
        raise Stop("STOP: the pre-declared criteria file is missing or its sha256 pin does not match")
    pins = {root: _sha_file(cwd / STAGED_JOB.format(root=root)) for root in ROOTS}
    return {"staged": {"sha256sums_sha256": staged["sha256sums_sha256"], "files": staged["files"]},
            "jobs": staged["jobs"], "pins": pins, "binding": bind, "paper": paper,
            "harness": {"path": str(harness_dest), "commit": HARNESS_COMMIT},
            "patch": patch, "criteria_sha256": CRITERIA_SHA256}


def preflight(cwd: Path, spec: dict, prepared: dict) -> dict:
    """Run the exact B2 authorization gates against the prepared job, plus the deterministic environment checks."""
    cwd = Path(cwd)
    job0 = prepared["jobs"][ordered_roots(spec["node"])[0]]
    probe_job = dict(job0)
    probe_job["out"] = str((cwd / "out" / ordered_roots(spec["node"])[0]).resolve())
    probe_job["base_url"] = "http://127.0.0.1:1/v1"  # a gate probe never serves; the gates do not use base_url
    temp_job = cwd / "work" / "preflight_job.json"
    temp_job.parent.mkdir(parents=True, exist_ok=True)
    temp_job.write_text(json.dumps(probe_job, indent=2) + "\n")
    gate = run_gate_probe(cwd / "paper", cwd / "harness", temp_job,
                          Path(prepared["patch"]["patched_campaign_source"]))
    blockers = collect_preflight_blockers(spec, job0["authority_config"], Path(probe_job["out"]),
                                          cwd / "paper", cwd / "harness", gate)
    return {"gates": gate["checks"], "probe_rc": gate["probe_rc"], "blockers": blockers,
            "out_under_work_dir": not any(b["gate"] == "out_under_work_dir" for b in blockers),
            "status": "PASS" if not blockers else "STOP"}


def _stop_record(cwd: Path, spec: dict, exc: Exception, status: str) -> dict:
    """A minimal STOP record so an early refusal is still a transferred, reviewable artifact."""
    record = {"schema": RECORD_SCHEMA, "kind": KIND, "run_id": spec["run_id"], "chunk_id": spec["chunk_id"],
              "node": spec["node"], "label": LABEL, "replay_marker": REPLAY_MARKER,
              "paper_commit": PAPER_COMMIT, "harness_commit": HARNESS_COMMIT, "image_digest": IMAGE_DIGEST,
              "model_sha256": GGUF_SHA256,
              "b2_audits": "none (no B.2 audits; reserved audit seeds 7001-7010 untouched)",
              "audit_seeds": list(AUDIT_SEEDS), "output_use": OUTPUT_USE, "status": status,
              "stop": f"STOP: {type(exc).__name__}: {exc}",
              "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
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
    record["input_pins"] = {"replay_inputs_sha256sums_sha256": prepared["staged"]["sha256sums_sha256"],
                            "files_verified": prepared["staged"]["files"], "criteria_sha256": CRITERIA_SHA256,
                            "label_patch_sha256": PATCH_SHA256, "job_json_pins": prepared["pins"]}
    record["paper_checkout"] = prepared["paper"]
    record["harness"] = prepared["harness"]
    server = None
    roots: list[dict] = []
    try:
        record["image"] = lib.image_identity(spec)
        record["host"] = lib.host_identity()
        record["gpu"] = lib.gpu_identity(spec["requirements"]["gpu_device_name"])
        record["cpu"] = lib.cpu_identity()
        gate = preflight(cwd, spec, prepared)
        record["preflight"] = gate
        if gate["blockers"]:
            record["status"] = "STOP_B2_AUTHORIZATION_GATE"
            record["roots"] = roots
            record["stop"] = ("STOP: the unmodified B2 campaign driver would refuse this replay environment; "
                              "no bypass attempted and no server started. Retain everything and report to the "
                              "author; the pre-declared protocol needs an author decision (see S2_C3_UNIT.md).")
            raise Stop(record["stop"])
        record["model"] = lib.fetch_model(spec["model"], cwd / "model.gguf")
        server = lib.start_server(spec, cwd / "model.gguf", cwd / "llama-server.log")
        record["server"] = {key: server[key] for key in
                            ("pid", "base_url", "build", "offloaded_layers", "total_layers", "cuda_lines", "log")}
        base_url = server["base_url"]
        prepared["job_rewrites"] = prepare_root_jobs(cwd, spec, spec["node"], prepared["pins"], base_url,
                                                     prepared["staged"]["sha256sums_sha256"])
        record["job_rewrites"] = prepared["job_rewrites"]
        record["roots"] = roots
        for root in ordered_roots(spec["node"]):
            job_path = cwd / "out" / root / "job.json"
            job = json.loads(job_path.read_text())
            run = run_one_campaign(cwd / "paper", cwd / "harness", job_path,
                                   Path(prepared["patch"]["patched_campaign_source"]), base_url,
                                   cwd / "work" / "logs" / f"{root}.campaign.log",
                                   max(600, int(spec["walltime_s"]) - 600))
            entry = {"instance_id": root, "job_json_sha256": _sha_file(job_path), **run}
            roots.append(entry)
            if run["returncode"] != 0:
                raise Stop(f"STOP: root campaign {root} rc={run['returncode']}"
                           f"{' (audit stop signal)' if run.get('stop_signal') else ''}; outputs kept (no retry)")
            entry.update(validate_campaign_manifest(cwd / "out" / root, job, binding, spec))
            if any(seed in RESERVED_B2_AUDIT_SEEDS for seed in entry["audit_seeds"]):
                raise Stop("STOP: a reserved B.2 audit seed appeared in a replay manifest")
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
    return record


# ------------------------------------------------------------------ seal (operator side; /ceph)
def seal_replay(job_output: Path, run_id: str, chunk_id: str) -> dict:
    """Seal one transferred replay job into /ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/ (no overwrite)."""
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
    if patch.get("patch_sha256") != PATCH_SHA256:
        raise Stop("STOP: job record does not bind the reviewed label patch")
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
                      f"label_patch_sha256={PATCH_SHA256}\n")
    lines = []
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            lines.append(f"{_sha_file(path)}  {path.relative_to(target)}")
    (target / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    receipt = {"schema": SEAL_RECEIPT_SCHEMA, "run_id": run_id, "chunk_id": chunk_id,
               "sealed_path": str(target), "label": LABEL, "replay_marker": REPLAY_MARKER,
               "image_digest": record["image_digest"], "model_sha256": record["model_sha256"],
               "paper_commit": record["paper_commit"], "harness_commit": record["harness_commit"],
               "label_patch_sha256": PATCH_SHA256, "host": record["host"].get("fqdn"),
               "engineering_only_marker": "ENGINEERING_ONLY.txt",
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


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
    s = sub.add_parser("seal")
    s.add_argument("job_output")
    s.add_argument("--run-id", required=True)
    s.add_argument("--chunk-id", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        validated = validate_spec(load_spec(Path(a.spec)))
        staged = verify_pinned_inputs(Path.cwd(), validated["spec"])
        print(json.dumps({"ok": True, "run_id": validated["run_id"], "node": validated["node"],
                          "label": LABEL, "roots": len(ordered_roots(validated["node"])),
                          "inputs_verified": staged["files"]}))
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
