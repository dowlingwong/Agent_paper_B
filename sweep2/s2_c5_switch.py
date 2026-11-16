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
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402

FROZEN_IMAGE = "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296"
ACCEPTED_LAYOUT = {"request_walltime_s": 12203, "request_disk_kb": 42460977, "request_memory_mb": 32000,
                   "chunks": 16, "gpu_hours": 41.72}
AUTHORIZATION_NOTE = r"docs/r1/authorizations/c3_sweep2_<date>\.md"
REQUIRED = ("approved", "label", "run_id", "image", "layout_request_walltime_s", "layout_request_disk_kb",
            "layout_request_memory_mb", "layout_chunks", "layout_gpu_hours", "b2_audits", "d8_lock")
P_FIELDS = tuple(f"P{i}" for i in range(1, 8))


class Stop(Exception):
    pass


def _text(value, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value:
        raise Stop(f"STOP: {name} must be a single-line non-empty string")
    return value.strip()


def parse_note(text: str) -> dict:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    for key in REQUIRED:
        if key not in fields or not fields[key]:
            raise Stop(f"STOP: authorization note lacks required field {key!r}")
    for key in P_FIELDS:
        if key not in fields or not fields[key]:
            raise Stop(f"STOP: authorization note lacks required prerequisite {key!r}")
    if fields["approved"].lower() != "true":
        raise Stop("STOP: authorization note is not approved (approved: true required)")
    if fields["label"] != "EVIDENCE":
        raise Stop("STOP: authorization note label must be EVIDENCE")
    if fields["image"] != FROZEN_IMAGE:
        raise Stop("STOP: authorization note must freeze the v1 gpu digest")
    if fields["b2_audits"].lower() not in ("none", "n/a", "not-authorized"):
        raise Stop("STOP: the sweep-2 authorization carries no B.2 audits; note must say none")
    if fields["d8_lock"].lower() != "true":
        raise Stop("STOP: R1-BX-D8 analysis lock must be recorded as true")
    for key in ("layout_request_walltime_s", "layout_request_disk_kb", "layout_request_memory_mb", "layout_chunks"):
        try:
            v = int(fields[key])
        except ValueError:
            raise Stop(f"STOP: authorization {key} must be an integer") from None
        if v != ACCEPTED_LAYOUT[{"layout_request_walltime_s": "request_walltime_s",
                                 "layout_request_disk_kb": "request_disk_kb",
                                 "layout_request_memory_mb": "request_memory_mb",
                                 "layout_chunks": "chunks"}[key]]:
            raise Stop(f"STOP: authorization {key}={v} is not the accepted 32k layout")
    try:
        if abs(float(fields["layout_gpu_hours"]) - ACCEPTED_LAYOUT["gpu_hours"]) > 0.05:
            raise Stop("STOP: authorization layout_gpu_hours is not the accepted estimate")
    except ValueError:
        raise Stop("STOP: authorization layout_gpu_hours must be numeric") from None
    return fields


def check(spec_path: Path, note_path: Path) -> dict:
    raw = Path(note_path).read_text()
    fields = parse_note(raw)
    spec = json.loads(Path(spec_path).read_text())
    src = spec.get("label_source") or {}
    if src.get("authorization") != Path(note_path).name:
        raise Stop("STOP: spec.label_source.authorization must be the authorization note basename")
    if src.get("authorization_sha256") != hashlib.sha256(raw.encode()).hexdigest():
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
    if spec.get("label") is not None and spec.get("label") != "EVIDENCE":
        raise Stop("STOP: spec label must be EVIDENCE")
    return {"run_id": fields["run_id"], "image": fields["image"], "note_sha256": src["authorization_sha256"],
            "layout": {k: fields[k] for k in ("layout_request_walltime_s", "layout_request_disk_kb",
                                              "layout_request_memory_mb", "layout_chunks")}}


def submit(spec_path: Path, note_path: Path, jdl: Path, *, enable: bool = False) -> dict:
    checked = check(spec_path, note_path)
    if not enable or os.environ.get("S2C5_ENABLE_REAL") != "1":
        raise Stop("STOP: S2-C5 real submission is disabled (needs --enable AND S2C5_ENABLE_REAL=1)")
    jdl = Path(jdl)
    if not jdl.is_file():
        raise Stop(f"STOP: reviewed JDL {jdl} missing")
    res = subprocess.run(["condor_submit", str(jdl)], capture_output=True, text=True, cwd=str(jdl.parent))
    if res.returncode != 0:
        raise Stop(f"STOP: condor_submit rc={res.returncode}: {res.stderr.strip()[:500]}")
    out = {"schema": "s2_c5_submission/v1", "run_id": checked["run_id"], "image": checked["image"],
           "note_sha256": checked["note_sha256"], "jdl": str(jdl), "condor_submit": res.stdout[-2000:],
           "submitted_utc": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime())}
    (jdl.parent / "S2C5_SUBMISSION.json").write_text(json.dumps(out, indent=1) + "\n")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--spec", required=True); c.add_argument("--note", required=True)
    s = sub.add_parser("submit")
    s.add_argument("--spec", required=True); s.add_argument("--note", required=True); s.add_argument("--jdl", required=True)
    s.add_argument("--enable", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            print(json.dumps(check(Path(a.spec), Path(a.note)), indent=1)); return 0
        print(json.dumps(submit(Path(a.spec), Path(a.note), Path(a.jdl), enable=a.enable), indent=1)); return 0
    except Stop as exc:
        print(str(exc), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
