#!/usr/bin/env python3
"""G.1b real-submission switch (S2-C5 pattern). DISABLED BY DEFAULT; nothing here submits in check mode or tests.

``check`` verifies, without submitting:
  * the author-signed note ``docs/r1/authorizations/g1b_t1_h200_<YYYYMMDD>.md`` exists, is byte-identical to the
    blob on the local ``origin/main``, carries every required field (the paper commit and the staged spec's sha256
    included), ``approved: true`` and P1–P5 as PASS;
  * the staged spec validates at launch strength (no placeholder) and its run id, image digest and v2 VERSIONS
    sha256, harness commit, node list, edit count, runs per node and projected GPU-hours equal the note's, and the
    projection is within the note and within R1-G1B-CAP;
  * the staged files and every JDL are byte-identical to a fresh canonical render (``STAGE_MANIFEST.json``).
``submit`` does the same, then needs ``--enable`` AND ``G1B_ENABLE_REAL=1`` (two keys), runs the S2-C5 launch
binding (``g1b_lib.verify_launch``: ``ls-remote`` equals the local ``origin/main``, a tracked-clean checkout at the
spec's paper commit descending from main, authority files equal to main's, the PLAN rows R1-T1-HOST-H200,
R1-TRACKG-G3-EARLY, R1-G1B-CAP and R1-G1B-EDITS on main), writes a once-only marker
and runs ``condor_submit``: first ``mlab_ogbn_arxiv`` alone, then the other nodes only with ``--first-record``
(that node's sealed, STOP-free job record).  ENGINEERING_ONLY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1b_lib as lib  # noqa: E402
import g1b_render_jdl as render_jdl  # noqa: E402  (not sweep2/render_jdl.py)

REPO_ROOT = HERE.parent.parent
NOTE_NAME = re.compile(r"^g1b_t1_h200_\d{8}\.md$")
REQUIRED = ("approved", "label", "run_id", "image", "versions_sha256", "harness_commit", "paper_commit", "spec_sha256",
            "nodes", "n_edits_per_node", "runs_per_node", "gpu_hours", "d8_lock", "labels_read")
PLAN_ROWS = ("R1-T1-HOST-H200", "R1-TRACKG-G3-EARLY", "R1-G1B-CAP", "R1-G1B-EDITS")
P_FIELDS = ("P1", "P2", "P3", "P4", "P5")
P_CITES = {"P1": "R1-T1-HOST-H200", "P2": "R1-TRACKG-G3-EARLY", "P3": "R1-G1B-EDITS"}
ENABLE_ENV = "G1B_ENABLE_REAL"


class Stop(Exception):
    pass


def parse_note(text: str) -> dict:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: the note has a duplicate field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    for key in REQUIRED + P_FIELDS:
        if not fields.get(key):
            raise Stop(f"STOP: the note lacks {key!r}")
    for key in P_FIELDS:
        if not fields[key].upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: prerequisite {key} is not recorded as PASS")
    for key, cite in P_CITES.items():
        if cite not in fields[key]:
            raise Stop(f"STOP: {key} must cite {cite}")
    if fields["approved"] != "true":
        raise Stop("STOP: the note is not approved (approved: true required)")
    if fields["label"] != lib.ENGINEERING_ONLY:
        raise Stop("STOP: the note label must be ENGINEERING_ONLY")
    if fields["image"] != lib.IMAGE_DIGEST:
        raise Stop("STOP: the note must pin the v2 gpu digest")
    if fields["d8_lock"].lower() != "true" or fields["labels_read"] != "none":
        raise Stop("STOP: the note must record d8_lock: true and labels_read: none")
    try:
        gpu_h = float(fields["gpu_hours"])
    except ValueError:
        raise Stop("STOP: gpu_hours must be numeric") from None
    if not math.isfinite(gpu_h) or not 0 < gpu_h <= lib.CAP_TOTAL_GPU_HOURS:
        raise Stop(f"STOP: gpu_hours must be in (0, {lib.CAP_TOTAL_GPU_HOURS}] (R1-G1B-CAP)")
    return fields


def _note_on_main(rel: str, raw: bytes) -> bool:
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "blob", f"origin/main:{rel}"],
                          capture_output=True, check=False)
    return blob.returncode == 0 and blob.stdout == raw


def check(stage_dir: Path, note_path: Path, *, on_main=_note_on_main) -> dict:
    note = Path(note_path)
    if not note.is_file():
        raise Stop(f"STOP: note {note} missing")
    try:
        rel = note.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        raise Stop("STOP: the note must live under docs/r1/authorizations/ in this repository") from None
    if tuple(Path(rel).parts[:3]) != ("docs", "r1", "authorizations") or not NOTE_NAME.fullmatch(Path(rel).name):
        raise Stop("STOP: the note must be docs/r1/authorizations/g1b_t1_h200_<YYYYMMDD>.md")
    raw = note.read_bytes()
    if not on_main(rel, raw):
        raise Stop("STOP: the note is not committed on origin/main")
    fields = parse_note(raw.decode("utf-8"))
    stage_dir = Path(stage_dir)
    spec = lib.load_spec(stage_dir / "g1b_spec.json")
    loaded = lib.validate_spec(spec, launch=True)
    nodes = ",".join(n["node"] for n in spec["nodes"])
    pairs = {"run_id": spec["run_id"], "image": spec["image"]["digest"], "paper_commit": spec["paper"]["commit"],
             "spec_sha256": hashlib.sha256((stage_dir / "g1b_spec.json").read_bytes()).hexdigest(),
             "versions_sha256": spec["image"]["versions_sha256"], "harness_commit": spec["harness"]["commit"],
             "nodes": nodes, "n_edits_per_node": str(spec["edit_count"]["n_edits_per_node"]),
             "runs_per_node": str(spec["edit_count"]["runs_per_node"])}
    for key, value in pairs.items():
        if fields[key] != value:
            raise Stop(f"STOP: spec {key}={value!r} differs from the note ({fields[key]!r})")
    if loaded["projection"]["total_gpu_hours"] > float(fields["gpu_hours"]):
        raise Stop("STOP: the spec projects more GPU-hours than the note authorizes")
    manifest = json.loads((stage_dir / "STAGE_MANIFEST.json").read_text())
    if manifest.get("preview") is not False:
        raise Stop("STOP: a preview stage is never submittable")
    for name, sha in manifest["files"].items():
        if hashlib.sha256((stage_dir / name).read_bytes()).hexdigest() != sha:
            raise Stop(f"STOP: staged {name} changed after staging")
    for name in render_jdl.STAGED:
        if (stage_dir / name).read_bytes() != (HERE / name).read_bytes():
            raise Stop(f"STOP: staged {name} differs from the reviewed checkout")
    for node in spec["nodes"]:
        jdl = stage_dir / f"g1b_{node['node']}.jdl"
        if jdl.read_text() != render_jdl.render(spec, node):
            raise Stop(f"STOP: {jdl.name} differs from the canonical render")
    return {"run_id": spec["run_id"], "nodes": nodes, "note_sha256": hashlib.sha256(raw).hexdigest(),
            "spec_sha256": pairs["spec_sha256"],
            "projection_gpu_hours": loaded["projection"]["total_gpu_hours"]}


FIRST_NODE = "mlab_ogbn_arxiv"  # the shortest node goes first; the others wait for its clean record


def check_first_record(path: Path | None, run_id: str, spec: dict, spec_sha256: str) -> dict:
    """The first node's sealed job record must show that the infrastructure works on H200 before the other
    nodes are submitted: environment, data, cgroup, gate and engine (kit review B2/M2).  A determinism STOP of the
    node itself (``stop_class: node``) still proves that; an infrastructure STOP does not."""
    if path is None:
        raise Stop(f"STOP: submit {FIRST_NODE} alone first; the other nodes need --first-record")
    path = Path(path).resolve()
    want_dir = (lib.SEALED_ROOT / run_id / FIRST_NODE).resolve()
    if path != want_dir / "job_record.json" or not (want_dir / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: --first-record must be {want_dir / 'job_record.json'} with its SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=want_dir, capture_output=True).returncode != 0:
        raise Stop("STOP: the first node's sealed outputs do not verify against SHA256SUMS")
    record = json.loads(path.read_text())
    receipt = json.loads((want_dir / "SEAL_RECEIPT.json").read_text())
    runs = record.get("runs") or {}
    default = next((p for p in record.get("parts") or [] if p.get("part") == "default"), {})
    checks = {
        "run_id": record.get("run_id") == run_id, "node": record.get("node") == FIRST_NODE,
        "spec_sha256": record.get("spec_sha256") == spec_sha256,
        "harness": record.get("harness_commit") == spec["harness"]["commit"],
        "image": (record.get("image") or {}).get("digest") == lib.IMAGE_DIGEST,
        "gpu": (record.get("gpu") or {}).get("name") == lib.GPU_MODEL,
        "receipt": receipt.get("job_record_sha256") == hashlib.sha256(path.read_bytes()).hexdigest(),
        "environment": (record.get("environment") or {}).get("freeze_sha256")
        == (spec["envs"].get(lib.node_entry(spec, FIRST_NODE)["env"]) or {}).get("sha256"),
        "data": isinstance(record.get("data"), dict),
        "cgroup": bool(record.get("cgroup_parent")),
        "default_part": default.get("stop") is None and default.get("written_rows") == default.get("expected_runs")
        and isinstance(default.get("expected_runs"), int) and default["expected_runs"] > 0,
        "stop_class": record.get("stop_class") in (None, "node"),
        "rows": record.get("stop_class") == "node"
        or (isinstance(runs.get("expected"), int) and runs.get("written") == runs.get("expected")),
    }
    failed = sorted(k for k, ok in checks.items() if not ok)
    if failed:
        raise Stop(f"STOP: the first node's record does not show a working H200 path: {failed}")
    return {"first_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "first_record_stop_class": record.get("stop_class")}


def submit(stage_dir: Path, note_path: Path, *, enable: bool, node: str | None = None,
           first_record: Path | None = None, on_main=_note_on_main, launch_binding=None) -> dict:
    checked = check(stage_dir, note_path, on_main=on_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: G.1b real submission is disabled (needs --enable AND {ENABLE_ENV}=1)")
    spec = lib.load_spec(Path(stage_dir) / "g1b_spec.json")
    checked["launch"] = (launch_binding or lib.verify_launch)(REPO_ROOT, spec, PLAN_ROWS)
    stage_dir = Path(stage_dir).resolve()
    names = checked["nodes"].split(",")
    if node is not None:
        if node not in names:
            raise Stop(f"STOP: {node} is not in the authorized node list")
        names = [node]
    if names != [FIRST_NODE]:
        checked.update(check_first_record(first_record, checked["run_id"], spec, checked["spec_sha256"]))
        names = [n for n in names if n != FIRST_NODE]
    out = []
    for name in names:
        try:
            with (stage_dir / f"G1B_SUBMIT_STARTED_{name}.json").open("x") as marker:
                json.dump({"node": name, **checked}, marker)
        except FileExistsError:
            raise Stop(f"STOP: {name} was already submitted from this stage; check the scheduler") from None
        res = subprocess.run(["condor_submit", f"g1b_{name}.jdl"], cwd=stage_dir, capture_output=True, text=True,
                             timeout=600)
        if res.returncode != 0:
            raise Stop(f"STOP: condor_submit {name} rc={res.returncode}: {res.stderr.strip()[:300]}")
        entry = {"schema": "g1b_h200_submission/1", "node": name, "condor_submit": res.stdout[-1000:],
                 "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **checked}
        with (stage_dir / "G1B_SUBMISSIONS.jsonl").open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
        out.append(entry)
    return {"submitted": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--stage", required=True); c.add_argument("--note", required=True)
    s = sub.add_parser("submit"); s.add_argument("--stage", required=True); s.add_argument("--note", required=True)
    s.add_argument("--enable", action="store_true"); s.add_argument("--node", default=None)
    s.add_argument("--first-record", type=Path, default=None)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            print(json.dumps(check(Path(a.stage), Path(a.note)), indent=1))
        else:
            print(json.dumps(submit(Path(a.stage), Path(a.note), enable=a.enable, node=a.node,
                                    first_record=a.first_record), indent=1))
    except (Stop, lib.Stop) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
