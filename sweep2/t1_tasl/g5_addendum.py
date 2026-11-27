"""Bindings for one expansion G.5 run under R1-G5-S9.

Each addendum has its own run ID, spec and note. Its deployment is derived from
the published census and the existing G.5 spec supplies the campaign settings.
This module reads published metadata and engineering records only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import g1b_tasl as G
import g5_tasl as S

sys.path.insert(0, str(S.REPO_ROOT))
from r1.c3 import p3_split, release  # noqa: E402


SCHEMA = S.ADDENDUM_SCHEMA
FAMILY = "G5-X"
ROWS = ("R1-G5-EXPANSION-JOIN", "R1-G5-S9", "R1-STEP-ORDER", S.TASL2_CPU_ROW)
RUN_ID = re.compile(r"c3_t1_labels_\d{8}_addendum_[1-9]\d*")
G1B_SPEC = "sweep2/t1_tasl/g1b_tasl_x_spec.json"
CONFIG_KEYS = {"schema", "run_id", "node", "supply", "paper", "base_g5_note", "base_g5_spec", "g1b_note",
               "g1b_spec", "g1b_receipt", "g1b_copy", "pre_split_amendment", "instance_split", "tail", "harness"}
NODE_KEYS = ("node", "spec_path", "node_dir", "node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256",
             "run_seconds", "slowest_census_seconds", "census_record", "device", "cpus", "cpu_only", "env")


def published(citation: str, directory: str, read_main) -> tuple[str, bytes]:
    match = S.CITED.fullmatch(citation) if isinstance(citation, str) else None
    if not match:
        raise S.Stop(f"STOP: expected a path and sha256 under {directory}")
    path, sha = match.groups()
    if not S._rel_ok(path) or not path.startswith(directory + "/"):
        raise S.Stop(f"STOP: unsafe published citation {path}")
    raw = read_main(path)
    if raw is None or S._sha_bytes(raw) != sha:
        raise S.Stop(f"STOP: {path} is missing or has another sha256 on published main")
    return path, raw


def local_copy(path: str, raw: bytes, root: Path) -> Path:
    file = root / path
    if file.is_symlink() or not file.is_file() or file.read_bytes() != raw:
        raise S.Stop(f"STOP: local {path} differs from the published reference")
    return file


def deployment(g1b: dict, name: str) -> dict:
    """Reuse the CPU placement, lease and interpreter of the completed G.1b reference."""
    if name not in (*p3_split.T1_EXPANSION_MLGYM, *p3_split.T1_EXTRA_TASKS) or not G.is_x(g1b):
        raise S.Stop(f"STOP: {name} has no expansion deployment")
    node = G.node_entry(g1b, name)
    if (node.get("host"), node.get("device")) != (S.WORKER_HOST, "cpu") or \
            node.get("cpu_only") not in G.X_CPU_ONLY:
        raise S.Stop(f"STOP: {name} needs its TASL-2 CPU-only census deployment")
    cpus = G.node_cpus(g1b, node)
    S._tasl2_ok(G.cpu_list(cpus), f"{name} deployment")
    worker = g1b["hosts"][S.WORKER_HOST]
    env = node["env"]
    return {"node": {k: node[k] for k in NODE_KEYS}, "lease": G.cpu_lease_path(g1b, node),
            "environment": g1b["envs"][env], "interpreter": worker["env_python"][env],
            "harness_pin": node["harness"]["commit"], "census_base": worker["base"],
            "cpu_preflight": g1b["cpu_preflight"], "role": p3_split.role_of(name)}


def _receipt(receipt: dict, assembly: dict, name: str, run: str, spec_sha: str, canonical_spec_sha: str) -> None:
    """Require a successful receipt and the same attempt in the exact assembly."""
    if receipt.get("schema") != G.RECEIPT_SCHEMA or receipt.get("node") != name or receipt.get("host") != S.WORKER_HOST \
            or receipt.get("run_id") != run or receipt.get("stop") is not None or receipt.get("stop_class") is not None:
        raise S.Stop(f"STOP: {name} has no successful G.1b seal receipt")
    jobs = [job for job in assembly.get("jobs", ()) if job.get("node") == name]
    if (assembly.get("schema"), assembly.get("run_id"), assembly.get("spec_json_sha256")) != \
            (G.X_ASSEMBLY_SCHEMA, run, canonical_spec_sha) or len(jobs) != 1:
        raise S.Stop(f"STOP: the expansion assembly does not bind {name} to the published G.1b spec/run")
    job = jobs[0]
    keys = ("node", "attempt", "host", "job_record_sha256", "stop_class")
    if any(job.get(key) != receipt.get(key) for key in keys) or job.get("spec_sha256") != spec_sha or \
            job.get("sealed") != receipt.get("sealed_path") or job.get("device") != "cpu":
        raise S.Stop(f"STOP: {name}'s G.1b seal and assembly name different attempts")


def _g1b(config: dict, name: str, root: Path, read_main) -> tuple[dict, dict]:
    spec_path, spec_raw = published(config["g1b_spec"], "sweep2/t1_tasl", read_main)
    if spec_path != G1B_SPEC:
        raise S.Stop(f"STOP: the G.1b spec must be {G1B_SPEC}")
    g1b = json.loads(spec_raw)
    layout = deployment(g1b, name)
    note_path, note_raw = published(config["g1b_note"], S.NOTE_DIR, read_main)
    fields = G.check_note_x(local_copy(note_path, note_raw, root), local_copy(spec_path, spec_raw, root), spec=g1b,
                            on_main=lambda path, raw: read_main(path) == raw, read_main=read_main)
    G.check_gate_x(g1b, G.node_entry(g1b, name), fields, read_main)
    _, receipt_raw = published(config["g1b_receipt"], "docs/r1/reports", read_main)
    copied = S.check_g1b_copy(config["g1b_copy"], schema=G.X_SUMMARY_SCHEMA, run_id=g1b["run_id"],
                             nodes=[n["node"] for n in g1b["nodes"]], read_main=read_main)
    _, assembly_raw = published(f"{copied['assembly_copy']} sha256 {copied['assembly_sha256']}",
                                "docs/r1/reports", read_main)
    canonical_spec_sha = S._sha_bytes(json.dumps(g1b, sort_keys=True).encode())
    _receipt(json.loads(receipt_raw), json.loads(assembly_raw), name, g1b["run_id"], S._sha_bytes(spec_raw),
             canonical_spec_sha)
    S.require_deterministic(name, json.loads(copied["raw"])["verdicts"].get(name))
    copied.update(schema=G.X_SUMMARY_SCHEMA, run_id=g1b["run_id"])
    return layout, copied


def _check_split(config: dict, root: Path, read_main) -> None:
    if config.get("instance_split") != p3_split.SPLIT_FILES[2]:
        raise S.Stop("STOP: an expansion G.5 addendum must bind the exact P3 split v2")
    path, raw = published(config["pre_split_amendment"], S.NOTE_DIR, read_main)
    try:
        checked = release.split_v2_amendment(root)
    except release.ReleaseStop as exc:
        raise S.Stop(str(exc)) from exc
    if checked != {"path": path, "sha256": S._sha_bytes(raw)}:
        raise S.Stop("STOP: an expansion G.5 addendum must bind the published PRE-SPLIT amendment")


def _launch_fields(config: dict, spec_path: Path, note_path: Path | None, *, draft: bool, read_main) -> tuple[dict, bytes]:
    run_id = config.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
        raise S.Stop("STOP: an addendum needs its own canonical G.5 note and run ID")
    rel = f"{S.NOTE_DIR}/{run_id}.md"
    on_main = read_main(rel)
    if note_path is None:
        if draft or on_main is None:
            raise S.Stop(f"STOP: {rel} is not on published main")
        raw = on_main
    else:
        if not note_path.as_posix().endswith("/" + rel) and note_path.as_posix() != rel:
            raise S.Stop(f"STOP: the addendum note must be {rel}")
        raw = note_path.read_bytes()
    fields = G._note_fields(raw)
    if fields.get("approved") != ("false" if draft else "true") or (not draft and raw != on_main):
        raise S.Stop("STOP: the G.5 addendum must be approved and byte-identical on published main")
    paper = config.get("paper") or {}
    commit = paper.get("commit")
    sha = S._sha_bytes(spec_path.read_bytes())
    if not isinstance(commit, str) or not G.L.COMMIT.fullmatch(commit):
        raise S.Stop("STOP: the addendum needs its own full paper commit")
    want = {"run_id": run_id, "node": config["node"], "paper_commit": commit, "spec_sha256": sha,
            "base_g5_note": config["base_g5_note"], "base_g5_spec": config["base_g5_spec"],
            "instance_split": f"{p3_split.V2_REL} sha256 {p3_split.P3_SPLIT_V2_SHA256}",
            "pre_split_amendment": config["pre_split_amendment"], "supply": config["supply"]}
    bad = [key for key, value in want.items() if fields.get(key) != value]
    if bad:
        raise S.Stop(f"STOP: the G.5 addendum note does not bind the exact spec fields {bad}")
    review, _ = published(fields.get("review"), "docs/r1/reviews", read_main)
    S._review_names(review, [run_id, sha, commit], read_main, "the filled G.5 addendum")
    return fields, raw


def bind(spec_path: Path, note_path: Path | None = None, *, draft: bool = False, root: Path = S.REPO_ROOT,
         read_main=G._read_main) -> dict:
    """Validate a G.5 expansion note and derive its runtime spec without changing base settings."""
    config = json.loads(spec_path.read_bytes())
    if not isinstance(config, dict) or config.get("schema") != SCHEMA:
        raise S.Stop(f"STOP: the G.5 expansion spec must use {SCHEMA}")
    if set(config) != CONFIG_KEYS or any(not isinstance(config[k], dict) for k in ("paper", "g1b_copy", "harness", "tail")):
        raise S.Stop(f"STOP: the G.5 addendum spec must contain exactly {sorted(CONFIG_KEYS)}")
    name = config.get("node")
    if name not in (*p3_split.T1_EXPANSION_MLGYM, *p3_split.T1_EXTRA_TASKS) or config.get("supply") != p3_split.role_of(name):
        raise S.Stop("STOP: the G.5 addendum supply differs from the node's S9 role")
    fields, note_raw = _launch_fields(config, spec_path, note_path, draft=draft, read_main=read_main)
    _check_split(config, root, read_main)
    for row in ROWS:
        S.plan_row(row, read_main)
    base_path, base_raw = published(config["base_g5_spec"], "sweep2/t1_tasl", read_main)
    base_note, base_note_raw = published(config["base_g5_note"], S.NOTE_DIR, read_main)
    base = json.loads(base_raw)
    S.validate_spec(base, launch=True)
    base_fields = S.check_note(local_copy(base_note, base_note_raw, root), local_copy(base_path, base_raw, root),
                               spec=base, on_main=lambda path, raw: read_main(path) == raw, read_main=read_main)
    if config["paper"]["commit"] == base["paper"]["commit"] or config["paper"].get("repo") != base["paper"].get("repo"):
        raise S.Stop("STOP: the addendum must have its own paper pin in the base G.5 repository")
    layout, noise = _g1b(config, name, root, read_main)
    family = config["harness"]
    if set(family) != {"g1b_pin", "g5_commit", "harness_dir", "isolation_host_check"}:
        raise S.Stop("STOP: the G.5 harness binding needs the kit pin, G.5 commit, checkout and isolation check")
    if family.get("g1b_pin") != layout["harness_pin"] or not G.L.COMMIT.fullmatch(str(family.get("g5_commit"))):
        raise S.Stop(f"STOP: {name}'s G.5 harness must descend from its census kit pin")
    G._abs(family.get("harness_dir"), "addendum.harness.harness_dir")
    host_check = G.check_host_record({"hostname": base["worker"]["hostname"],
                                     "isolation_host_check": family.get("isolation_host_check")},
                                     family["g5_commit"], read_main)
    tail = config.get("tail")
    if not isinstance(tail, dict) or set(tail) - {"tails", S.TAILS_NU, "authority"} or tail.get("tails") not in S.TAILS:
        raise S.Stop(f"STOP: {name} needs a declared P10 tail law")
    node = dict(layout["node"], family=FAMILY, **{key: value for key, value in tail.items() if key != "authority"})
    S.check_tails_nu(node)
    tail_row = tail.get("authority", "")
    S.plan_row(tail_row, read_main, terms=(name, S.tails_text(node)))
    plan = read_main("docs/r1/PLAN.md").decode("utf-8")
    if sum(row == tail_row for row, _ in release.author_rows(plan)) != 1:
        raise S.Stop(f"STOP: {name}'s P10 declaration must be an author row on published main")
    runtime = dict(base, paper=config["paper"], run_id=config["run_id"], nodes=[node],
                   harness_families={**base["harness_families"], FAMILY: family})
    runtime["worker"] = dict(base["worker"], base=layout["census_base"],
                             env_python={**base["worker"]["env_python"], node["env"]: layout["interpreter"]})
    runtime["envs"] = dict(base["envs"], **{node["env"]: layout["environment"]})
    runtime["_addendum"] = {"note": f"{S.NOTE_DIR}/{config['run_id']}.md", "spec_sha256": fields["spec_sha256"],
                            "note_sha256": S._sha_bytes(note_raw), "role": layout["role"],
                            "cpu_lease": layout["lease"], "cpu_preflight": layout["cpu_preflight"],
                            "noise": {key: value for key, value in noise.items() if key != "raw"},
                            "base_spec_sha256": S._sha_bytes(base_raw), "base_note": base_note, "base_spec": base,
                            "base_run_id": base["run_id"],
                            "host_check": host_check, "_K": base_fields["_K"], "_K_row": base_fields["_K_row"],
                            "_freeze": base_fields["_freeze"]}
    return runtime
