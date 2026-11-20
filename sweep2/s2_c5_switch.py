#!/usr/bin/env python3
"""S2-C5 — real-submission switch (EVIDENCE). DISABLED BY DEFAULT; reviewed unit, not enabled.

The switch submits a reviewed sweep-2 JDL only when ALL of the following hold:
  * the author-committed authorization note `docs/r1/authorizations/c3_sweep2_<date>.md` is present, matches the
    required format/fields (P1–P7, layout, frozen image digest, label EVIDENCE, approved: true, D8 lock, no B.2
    audits in this authorization) and is the exact note the spec pins (path + sha256);
  * the spec's run_id and image digest match the note, and the spec's accepted 32k layout matches the note;
  * the submitter passes `--enable` AND sets `S2C5_ENABLE_REAL=1` (two keys; the repository default is disabled and
    this unit does not create either).
No labels are read; no submission happens in tests/check mode.
"""
from __future__ import annotations

import argparse
from contextlib import chdir
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402
import render_jdl  # noqa: E402
from s2_c3b_lib import server_settings_sha256  # noqa: E402

FROZEN_IMAGE = lib.FROZEN_IMAGE
ACCEPTED_LAYOUT = {"layout_request_walltime_s": math.ceil(1.5 * lib.MEASURED_GPU_CHUNK_SECONDS["NVIDIA H200"]), "layout_request_disk_kb": lib.EVIDENCE_DISK_KB,
                   "layout_request_memory_mb": lib.EVIDENCE_MEMORY_MB, "layout_chunks": 16}
NOTE_DIR = ("docs", "r1", "authorizations")
NOTE_NAME = re.compile(r"^c3_sweep2_\d{8}\.md$")
REPO_ROOT = HERE.parent
REQUIRED_JDL_LINES = {
    "request_memory = 32000",
    "request_disk = 42460970",
    f"+RequestWalltime = {ACCEPTED_LAYOUT['layout_request_walltime_s']}",
    "container_image = docker://" + FROZEN_IMAGE,
    "periodic_hold = (NumJobStarts > 1)",
}
REQUIRED = ("approved", "label", "run_id", "image", "layout_request_walltime_s", "layout_request_disk_kb",
            "layout_request_memory_mb", "layout_chunks", "layout_gpu_hours", "layout_wall_hours", "b2_audits", "d8_lock")
P_FIELDS = tuple(f"P{i}" for i in range(1, 8))


class Stop(Exception):
    pass


def _authorized_note(rel: str, raw: bytes) -> bool:
    """Match the authoritative blob on the freshly fetched published main."""
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "blob", f"origin/main:{rel}"],
                          capture_output=True, check=False)
    return blob.returncode == 0 and blob.stdout == raw


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value:
        raise Stop(f"STOP: {name} must be a single-line non-empty string")
    return value.strip()


def parse_note(text: str) -> dict:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: authorization note has a duplicate field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    for key in REQUIRED:
        if key not in fields or not fields[key]:
            raise Stop(f"STOP: authorization note lacks required field {key!r}")
    for key in P_FIELDS:
        if key not in fields or not fields[key]:
            raise Stop(f"STOP: authorization note lacks required prerequisite {key!r}")
        if not fields[key].upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: authorization prerequisite {key} is not recorded as PASS")
    if not re.search(r"\bR1-S2C3-ACCEPT\b", fields["P4"]):
        raise Stop("STOP: P4 must cite R1-S2C3-ACCEPT")
    if fields["approved"] != "true":
        raise Stop("STOP: authorization note is not approved (approved: true required)")
    if fields["label"] != "EVIDENCE":
        raise Stop("STOP: authorization note label must be EVIDENCE")
    if fields["image"] != FROZEN_IMAGE:
        raise Stop("STOP: authorization note must freeze the v1 gpu digest")
    if fields["b2_audits"] != "none (this authorization carries no B.2 audits)":
        raise Stop("STOP: the sweep-2 authorization carries no B.2 audits; note must say none")
    if fields["d8_lock"].lower() != "true":
        raise Stop("STOP: R1-BX-D8 analysis lock must be recorded as true")
    for key, accepted in ACCEPTED_LAYOUT.items():
        try:
            value = int(fields[key])
        except ValueError:
            raise Stop(f"STOP: authorization {key} must be an integer") from None
        if value != accepted:
            raise Stop(f"STOP: authorization {key}={value} differs from the reviewed layout ({accepted})")
    for key, cap in (("layout_gpu_hours", 60), ("layout_wall_hours", 48)):
        try:
            projected = float(fields[key])
        except ValueError:
            raise Stop(f"STOP: authorization {key} must be numeric") from None
        if not math.isfinite(projected) or not 0 < projected <= cap:
            raise Stop(f"STOP: authorization {key} is outside (0, {cap}]")
    return fields


def check(spec_path: Path, note_path: Path, jdl: Path | None = None) -> dict:
    note = Path(note_path)
    if not note.is_file():
        raise Stop(f"STOP: authorization note {note} missing")
    try:
        rel = note.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        raise Stop("STOP: authorization note must live under docs/r1/authorizations/ in the repository") from None
    if tuple(Path(rel).parts[:3]) != ("docs", "r1", "authorizations") or not NOTE_NAME.fullmatch(Path(rel).name):
        raise Stop("STOP: authorization note must be docs/r1/authorizations/c3_sweep2_<YYYYMMDD>.md")
    raw_bytes = note.read_bytes()
    raw = raw_bytes.decode("utf-8")
    if not _authorized_note(rel, raw_bytes):
        raise Stop("STOP: authorization note is not committed on origin/main")
    fields = parse_note(raw)
    spec = json.loads(Path(spec_path).read_text())
    if spec.get("schema") != lib.SCHEMA or spec.get("kind", "chunk") != "chunk":
        raise Stop("STOP: submission requires a sweep-2 chunk spec")
    src = spec.get("label_source") or {}
    if src.get("authorization") != Path(note_path).name:
        raise Stop("STOP: spec.label_source.authorization must be the authorization note basename")
    if src.get("authorization_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        raise Stop("STOP: spec pins a different authorization note sha256")
    if spec.get("run_id") != fields["run_id"]:
        raise Stop("STOP: spec run_id does not match the authorization")
    if (spec.get("image") or {}).get("digest") != fields["image"]:
        raise Stop("STOP: spec image digest does not match the authorization")
    if spec.get("request_walltime_s", spec.get("walltime_s")) != int(fields["layout_request_walltime_s"]):
        raise Stop("STOP: spec walltime does not match the authorization layout")
    if spec.get("request_disk_kb") != int(fields["layout_request_disk_kb"]):
        raise Stop("STOP: spec disk does not match the authorization layout")
    if spec.get("request_memory_mb") != int(fields["layout_request_memory_mb"]):
        raise Stop("STOP: spec memory does not match the authorization layout")
    if spec.get("label", "EVIDENCE") != "EVIDENCE":
        raise Stop("STOP: spec label must be EVIDENCE")
    if spec.get("walltime_s") not in (None, int(fields["layout_request_walltime_s"])):
        raise Stop("STOP: spec walltime_s differs from the authorization layout")
    jdl_sha = None
    if jdl is not None:
        jd = Path(jdl)
        if not jd.is_file():
            raise Stop(f"STOP: reviewed JDL {jd} missing")
        jdl_sha = hashlib.sha256(jd.read_bytes()).hexdigest()
        if spec.get("reviewed_jdl_sha256") != jdl_sha:
            raise Stop("STOP: spec does not pin this reviewed JDL (reviewed_jdl_sha256 mismatch)")
        jdl_lines = jd.read_text().splitlines()
        requirements = [line for line in jdl_lines if line.partition("=")[0].strip().lower() == "requirements"]
        if requirements != [f"requirements = {render_jdl.requirements(spec)}"]:
            raise Stop("STOP: reviewed JDL must require the measured H200 placement")
        lines = set(jdl_lines)
        for needle in sorted(REQUIRED_JDL_LINES):
            if needle not in lines:
                raise Stop(f"STOP: reviewed JDL lacks the accepted layout line {needle!r}")
    return {"paper_commit": (spec.get("paper") or {}).get("commit"), "run_id": fields["run_id"], "image": fields["image"], "note_sha256": src["authorization_sha256"],
            "jdl_sha256": jdl_sha,
            "layout": {k: fields[k] for k in ("layout_request_walltime_s", "layout_request_disk_kb",
                                              "layout_request_memory_mb", "layout_chunks")}}



def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True,
                          check=False, timeout=30)


# R1-S2C3B-WDBC (author, 20 Nov 2026): the only accepted C3b shortfall (see s2_c3b_lib.DECLARED_EXCEPTION).
WDBC_EXCEPTION = {"row": "R1-S2C3B-WDBC", "node": "openml_wdbc", "criterion": "invalid_rate",
                  "required": "< 0.3", "max_observed": 0.30}


def liveness_nodes_ok(gate: dict, plan: str) -> bool:
    """8/8 live, or exactly the R1-S2C3B-WDBC 7/8 recorded by the C3b driver with the row on published main."""
    if gate.get("live_nodes") == 8:
        return True
    exc = gate.get("declared_exception")
    if not isinstance(exc, dict) or gate.get("live_nodes") != 7 or gate.get("failed_nodes") != [WDBC_EXCEPTION["node"]]:
        return False
    if any(exc.get(key) != WDBC_EXCEPTION[key] for key in ("row", "node", "criterion", "required", "max_observed")):
        return False
    observed = exc.get("observed")
    if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not 0 <= observed <= WDBC_EXCEPTION["max_observed"]:
        return False
    # m1 (review): re-check the recorded node entry itself, not only the driver's summary.
    nodes = gate.get("nodes")
    entry = nodes.get(WDBC_EXCEPTION["node"]) if isinstance(nodes, dict) else None
    if (not isinstance(entry, dict) or entry.get("pass") is not False
            or entry.get("failed_criteria") != [WDBC_EXCEPTION["criterion"]]):
        return False
    criteria = entry.get("criteria")
    target = criteria.get(WDBC_EXCEPTION["criterion"]) if isinstance(criteria, dict) else None
    if (not isinstance(target, dict) or target.get("observed") != observed
            or target.get("required") != WDBC_EXCEPTION["required"]):
        return False
    others = [node for node, verdict in nodes.items() if node != WDBC_EXCEPTION["node"]]
    if len(others) != 7 or any(not isinstance(nodes[node], dict) or nodes[node].get("pass") is not True for node in others):
        return False
    return re.search(r"^\| R1-S2C3B-WDBC \|", plan, re.M) is not None


def _verify_launch(spec_path: Path, jdl: Path, liveness_record: Path | None) -> None:
    """Bind a real submission to published authority, exact staged bytes and the C3b gate."""
    spec = json.loads(spec_path.read_bytes())
    paper = spec.get("paper") or {}
    commit = paper.get("commit")
    if not isinstance(commit, str) or not lib.COMMIT.fullmatch(commit):
        raise Stop("STOP: spec must pin the full launch commit")
    remote = _git("ls-remote", "origin", "refs/heads/main")
    local = _git("rev-parse", "origin/main")
    if remote.returncode or local.returncode or remote.stdout.split() != [local.stdout.strip(), "refs/heads/main"]:
        raise Stop("STOP: fetch published main before launch; local origin/main differs or could not be verified")
    if _git("rev-parse", "HEAD").stdout.strip() != commit or _git("status", "--porcelain", "-uno").stdout:
        raise Stop("STOP: launch checkout must be tracked-clean at the exact spec paper commit")
    if _git("merge-base", "--is-ancestor", "origin/main", commit).returncode:
        raise Stop("STOP: launch commit must descend from published main")
    authority = ("docs/r1/PLAN.md", "docs/r1/authorizations",
                 "results/r1/evidence/C3_sweep_classification_20261028.json",
                 "results/r1/pilot/C3_sweep_index_20261028T033315Z.json")
    if _git("diff", "--quiet", "origin/main", commit, "--", *authority).returncode:
        raise Stop("STOP: launch authority files differ from published main")
    plan = _git("show", "origin/main:docs/r1/PLAN.md").stdout
    for row in ("R1-SWEEP2-AUTH", "R1-S2C3-ACCEPT", "R1-SWEEP2-MEASURED-GPU", "R1-SWEEP2-MEMORY"):
        if not re.search(rf"^\| {row} \|", plan, re.M):
            raise Stop(f"STOP: missing published authority row {row}")
    if liveness_record is None:
        raise Stop("STOP: real submission requires a sealed C3b launch-commit record")
    raw = liveness_record.read_bytes()
    live = json.loads(raw)
    sealed_path = lib._sealed_target(live.get("run_id"), live.get("chunk_id")) / "job_record.json"
    sha_line = hashlib.sha256(raw).hexdigest() + "  job_record.json"
    if (liveness_record.resolve() != sealed_path
            or sha_line not in (sealed_path.parent / "SHA256SUMS").read_text().splitlines()):
        raise Stop("STOP: C3b submission guard requires the hash-verified cluster seal")
    gate = live.get("liveness_results") or {}
    binding = live.get("launch_binding") or {}
    measurement = live.get("prompt_measurement") or {}
    if (live.get("schema") != "s2_c3b_job_record/1" or live.get("label") != "ENGINEERING_ONLY"
            or live.get("stop") or not live.get("finished_utc") or gate.get("pass") is not True
            or not liveness_nodes_ok(gate, plan) or measurement.get("all_fit_ctx") is not True
            or live.get("paper_commit") != commit or live.get("image_digest") != FROZEN_IMAGE
            or binding.get("server_settings_sha256") != server_settings_sha256(spec)
            or live.get("harness_commit") != (spec.get("harness") or {}).get("commit")
            or live.get("model_sha256") != (spec.get("model") or {}).get("sha256")):
        raise Stop("STOP: sealed C3b record does not establish 8/8 (or the R1-S2C3B-WDBC 7/8) at the exact launch pins")
    staged = jdl.resolve().parent
    if spec_path.resolve() != staged / "s2_c2_spec.json":
        raise Stop("STOP: verify the exact staged s2_c2_spec.json that HTCondor will transfer")
    for name in ("s2_c2_job.sh", "s2_c2_lib.py"):
        if (staged / name).read_bytes() != (HERE / name).read_bytes():
            raise Stop(f"STOP: staged {name} differs from the reviewed launch checkout")
    with chdir(staged):
        validated = lib.validate_spec(spec)
    if validated["label"] != "EVIDENCE" or validated["kind"] != "chunk" or spec["collector"]["instances"] != 18:
        raise Stop("STOP: real submission requires one full 18-instance EVIDENCE chunk")
    collector = spec["collector"]
    key = (collector["node"], collector["memory_mode"])
    if key not in lib.SWEEP1_WORKER_BASELINE or spec["chunk_id"] != "-".join(key):
        raise Stop("STOP: chunk_id must identify one of the 16 fixed node/memory pairs")
    inputs = sorted(["s2_c2_job.sh", "s2_c2_lib.py", "s2_c2_spec.json", spec["label_source"]["authorization"]])
    jdl_text = jdl.read_text()
    names = re.findall(r"^log = ([A-Za-z0-9_.-]+)\.log$", jdl_text, re.M)
    if len(names) != 1 or jdl_text != render_jdl.render(spec, names[0], inputs):
        raise Stop("STOP: reviewed JDL differs from the canonical single-chunk render")



def submit(spec_path: Path, note_path: Path, jdl: Path, *, enable: bool = False,
           liveness_record: Path | None = None) -> dict:
    checked = check(spec_path, note_path, jdl)
    if not enable or os.environ.get("S2C5_ENABLE_REAL") != "1":
        raise Stop("STOP: S2-C5 real submission is disabled (needs --enable AND S2C5_ENABLE_REAL=1)")
    jdl = Path(jdl).resolve()
    try:
        _verify_launch(Path(spec_path), jdl, liveness_record)
        with (jdl.parent / "S2C5_SUBMIT_STARTED.json").open("x") as marker:
            json.dump({"paper_commit": checked["paper_commit"], "run_id": checked["run_id"],
                       "jdl_sha256": checked["jdl_sha256"]}, marker)
            marker.write("\n")
        res = subprocess.run(["condor_submit", str(jdl)], capture_output=True, text=True, cwd=str(jdl.parent),
                             timeout=600)
    except FileExistsError:
        raise Stop("STOP: this stage has already attempted submission; check the scheduler and records") from None
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
        raise Stop(f"STOP: launch verification or condor_submit could not run: {exc}") from None
    if res.returncode != 0:
        raise Stop(f"STOP: condor_submit rc={res.returncode}: {res.stderr.strip()[:500]}")
    out = {"schema": "s2_c5_submission/v1", "run_id": checked["run_id"], "image": checked["image"],
           "paper_commit": checked["paper_commit"], "note_sha256": checked["note_sha256"], "jdl_sha256": checked["jdl_sha256"], "jdl": str(jdl),
           "condor_submit": res.stdout[-2000:],
           "submitted_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())}
    with (jdl.parent / "S2C5_SUBMISSIONS.jsonl").open("a") as fh:
        fh.write(json.dumps(out) + "\n")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--spec", required=True); c.add_argument("--note", required=True)
    c.add_argument("--jdl", default=None)
    s = sub.add_parser("submit")
    s.add_argument("--spec", required=True); s.add_argument("--note", required=True); s.add_argument("--jdl", required=True)
    s.add_argument("--enable", action="store_true")
    s.add_argument("--liveness-record", type=Path)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            print(json.dumps(check(Path(a.spec), Path(a.note), Path(a.jdl) if a.jdl else None), indent=1)); return 0
        print(json.dumps(submit(Path(a.spec), Path(a.note), Path(a.jdl), enable=a.enable, liveness_record=a.liveness_record), indent=1)); return 0
    except Stop as exc:
        print(str(exc), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
