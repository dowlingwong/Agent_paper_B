#!/usr/bin/env python3
"""Track P P.4 phase-1 real-submission switch (S2-C5 pattern). DISABLED BY DEFAULT; nothing here submits in check mode
or tests. ENGINEERING_ONLY; AI-assisted (Claude).

``check`` verifies, without submitting:
  * the author-signed note ``docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md`` is byte-identical to the blob on the
    local ``origin/main``, ``approved: true``, ``label: ENGINEERING_ONLY``, ``phase: 1``, P1–P8 PASS, and its key
    lines (the draft's §8) agree with the staged spec: ``run_id``, ``spec_sha256``, ``code_commit`` (the spec's paper
    commit), ``labels:`` / ``label_receipt:`` (the partition and receipt sha256), ``source_label_block:`` (the frozen
    block), ``label_freeze:``, ``table_pin:``, ``duplicate_policy:``, ``split:``, ``split_file:``, ``arms:``,
    ``lr_grid:``, ``host:``, ``host_config:``, ``micro_batch: 8``, ``image:`` (the v2.1 digest), ``versions_sha256:``,
    ``env3_freeze:`` (R1-ENV-PIN's freeze and R1-TRACKP-V21-FREEZE), ``h200_sft_probe:`` (the record the spec's
    ``estimate.source`` names), ``gpu_hours_cap: 40`` with ``slot_hours_cap: 64``, ``job_layout:``,
    ``real_label_test_read: none``, ``evaluation_seeds_read: none`` and ``harness_commit: none``; no ``<…>``
    placeholder anywhere;
  * the staged spec validates at launch strength and its projection is within the cap;
  * the staged files and every JDL are byte-identical to a fresh canonical render (``STAGE_MANIFEST.json``, whose
    sha256 is recorded with every submission), and the staged partition and receipt are the spec's.
``submit`` does the same, then needs ``--enable`` AND ``TRACKP_P4_ENABLE_REAL=1`` (two keys), runs the launch
binding (``p4_lib.verify_launch_p4``, with the PLAN rows of ``p4_lib.PLAN_ROWS``), writes a once-only marker and runs
``condor_submit``: first the spec's ``first_arm`` alone, then the other arms only with ``--first-record`` (that arm's
sealed, STOP-free job record: the H200 path works before the 4B jobs start). Before every submission the GPU-hours
charged by all sealed attempts of the run plus the projection of the arms being submitted must stay within P4-CAP
(``check_cap``; a repeat counts against the cap). A repeat is submitted from a new stage (the once-only marker).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import p4_lib as lib  # noqa: E402
import p4_render_jdl as render_jdl  # noqa: E402

REPO_ROOT = HERE.parents[3]
NOTE_NAME = re.compile(r"^trackp_p4_\d{8}\.md$")
ENABLE_ENV = "TRACKP_P4_ENABLE_REAL"
P_FIELDS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")
P_CITES = {"P1": "C3_SWEEP1_LABEL_FREEZE_", "P3": "docs/r1/reviews/", "P5": "R1-TRACKP-IMAGE-V21",
           "P6": "R1-TRACKP-P4-DECISIONS", "P7": "--check-config", "P8": "R1-T1-HOST-TASL"}
REQUIRED = ("approved", "label", "phase", "run_id", "spec_sha256", "code_commit", "labels", "label_receipt",
            "source_label_block", "label_freeze", "table_pin", "duplicate_policy", "split", "split_file", "arms",
            "lr_grid", "host", "host_config", "micro_batch", "image", "versions_sha256", "env3_freeze",
            "h200_smoke_e0", "h200_sft_probe", "gpu_hours_cap", "job_layout", "real_label_test_read",
            "evaluation_seeds_read", "harness_commit")


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
    bad = sorted(k for k, v in fields.items() if re.search(r"<[^>]*>", v))
    if bad:
        raise Stop(f"STOP: note fields still hold a <...> placeholder: {bad}")
    for key in P_FIELDS:
        if not fields[key].upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: prerequisite {key} is not recorded as PASS")
    for key, cite in P_CITES.items():
        if cite not in fields[key]:
            raise Stop(f"STOP: {key} must cite {cite}")
    want = {"approved": "true", "label": lib.ENGINEERING_ONLY, "phase": "1"}
    for key, value in want.items():
        if fields[key] != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    for key in ("real_label_test_read", "evaluation_seeds_read"):
        if not fields[key].startswith("none"):
            raise Stop(f"STOP: {key} must read none (P4-PHASE1-TEST A)")
    return fields


def _note_on_main(rel: str, raw: bytes) -> bool:
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "blob", f"origin/main:{rel}"],
                          capture_output=True, check=False)
    return blob.returncode == 0 and blob.stdout == raw


def check_binding(fields: dict, spec: dict, spec_sha256: str) -> None:
    """The note's key lines against the staged spec (module docstring)."""
    exact = {"run_id": spec["run_id"], "spec_sha256": spec_sha256, "code_commit": spec["paper"]["commit"],
             "versions_sha256": spec["image"]["versions_sha256"]}
    for key, value in exact.items():
        if fields[key] != value:
            raise Stop(f"STOP: note {key} {fields[key]!r} is not the spec's {value!r}")
    contains = {"labels": (spec["labels"]["partition_sha256"], "label_block.traindev.jsonl"),
                "label_receipt": (spec["labels"]["receipt_sha256"], "RECEIPT.json"),
                "source_label_block": (lib.SOURCE_BLOCK_SHA256,),
                "label_freeze": (spec["labels"]["freeze_record"]["path"], spec["labels"]["freeze_record"]["sha256"]),
                "split_file": (lib.SPLIT_FILE["path"], lib.SPLIT_FILE["sha256"]),
                "host_config": (lib.HOST_CONFIG, spec["host_config"]["sha256"]),
                "image": (spec["image"]["digest"],),
                "env3_freeze": (lib.ENV3_FREEZE, "R1-TRACKP-V21-FREEZE"),
                "gpu_hours_cap": ("slot_hours_cap: 64",),
                "job_layout": ("one job per base",),
                "table_pin": (lib.TABLE_PIN,),
                "duplicate_policy": (spec["protocol"]["duplicate_policy"],),
                "split": ("P3", "P4-P1SPLIT A"),
                "lr_grid": ("1e-5,3e-5,1e-4", "seeds per lr: 3", "250, 500", "20261122"),
                "host": ("NEMO2 H200", "R1-T1-HOST-TASL"),
                "harness_commit": ("none",),
                "h200_sft_probe": (str(spec["estimate"]["source"]).split(":", 1)[-1].strip(),)}
    for key, needles in contains.items():
        for needle in needles:
            if needle not in fields[key]:
                raise Stop(f"STOP: note {key} must contain {needle!r}")
    if not fields["micro_batch"].startswith("8 ") and fields["micro_batch"] != "8":
        raise Stop("STOP: note micro_batch must be 8 (P4-MB A)")
    if not re.match(r"^40(?![0-9.])", fields["gpu_hours_cap"]):
        raise Stop("STOP: note gpu_hours_cap must be 40 (P4-CAP A)")
    named = [a.strip() for a in re.split(r"[,;]", fields["arms"].split("(")[0]) if a.strip()]
    if sorted(named) != sorted(spec["arms"]):
        raise Stop(f"STOP: note arms {named} are not the spec's {spec['arms']}")


def check(stage_dir: Path, note_path: Path, *, on_main=_note_on_main) -> dict:
    note = Path(note_path)
    if not note.is_file():
        raise Stop(f"STOP: note {note} missing")
    try:
        rel = note.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        raise Stop("STOP: the note must live under docs/r1/authorizations/ in this repository") from None
    if tuple(Path(rel).parts[:3]) != ("docs", "r1", "authorizations") or not NOTE_NAME.fullmatch(Path(rel).name):
        raise Stop("STOP: the note must be docs/r1/authorizations/trackp_p4_<YYYYMMDD>.md")
    raw = note.read_bytes()
    if not on_main(rel, raw):
        raise Stop("STOP: the note is not committed on origin/main")
    fields = parse_note(raw.decode("utf-8"))
    stage_dir = Path(stage_dir)
    spec_path = stage_dir / "p4_spec.json"
    spec = lib.load_spec(spec_path)
    loaded = lib.validate_spec(spec, launch=True)
    spec_sha = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    check_binding(fields, spec, spec_sha)
    manifest_raw = (stage_dir / "STAGE_MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest.get("preview") is not False:
        raise Stop("STOP: a preview stage is never submittable")
    for name, sha in manifest["files"].items():
        if hashlib.sha256((stage_dir / name).read_bytes()).hexdigest() != sha:
            raise Stop(f"STOP: staged {name} changed after staging")
    for name in render_jdl.STAGED:
        if (stage_dir / name).read_bytes() != (HERE / name).read_bytes():
            raise Stop(f"STOP: staged {name} differs from the reviewed checkout")
    for arm in spec["arms"]:
        jdl = stage_dir / f"p4_{arm}.jdl"
        if jdl.read_text() != render_jdl.render(spec, arm):
            raise Stop(f"STOP: {jdl.name} differs from the canonical render")
    for name in (*render_jdl.TABLE_FILES, *render_jdl.PARTITION_FILES):
        if name not in manifest["files"]:
            raise Stop(f"STOP: the stage lacks the transferred input {name}")
    for name, sha in (("label_block.traindev.jsonl", spec["labels"]["partition_sha256"]),
                      ("RECEIPT.json", spec["labels"]["receipt_sha256"])):
        if manifest["files"].get(name) != sha:
            raise Stop(f"STOP: the staged {name} is not the spec's (and the note's) {sha}")
    return {"run_id": spec["run_id"], "arms": spec["arms"], "note_sha256": hashlib.sha256(raw).hexdigest(),
            "spec_sha256": spec_sha, "stage_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "projection_gpu_hours": loaded["projection"]["total_gpu_hours"]}


def check_first_record(path: Path | None, spec: dict, spec_sha256: str, sealed_root: Path = lib.SEALED_ROOT) -> dict:
    """The first arm's sealed record must be STOP-free on the H200 path before the other arms are submitted."""
    first = spec["first_arm"]
    if path is None:
        raise Stop(f"STOP: submit {first} alone first; the other arms need --first-record")
    path = Path(path).resolve()
    arm_root = (Path(sealed_root) / spec["run_id"] / first).resolve()
    if path.parent.parent != arm_root or path.name != "job_record.json" or \
            not (path.parent / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: --first-record must be {arm_root}/attempt-N/job_record.json with its SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=path.parent, capture_output=True).returncode != 0:
        raise Stop("STOP: the first arm's sealed outputs do not verify against SHA256SUMS")
    record = json.loads(path.read_text())
    receipt = json.loads((path.parent / "SEAL_RECEIPT.json").read_text())
    checks = {"run_id": record.get("run_id") == spec["run_id"], "arm": record.get("arm") == first,
              "spec_sha256": record.get("spec_sha256") == spec_sha256,
              "receipt": receipt.get("job_record_sha256") == hashlib.sha256(path.read_bytes()).hexdigest(),
              "image": (record.get("image") or {}).get("digest") == spec["image"]["digest"],
              "gpu": (record.get("gpu") or {}).get("name") == lib.GPU_MODEL,
              "env3_freeze": (record.get("env3_freeze") or {}).get("status") in ("identical", "causal_conv1d_only"),
              "stop": record.get("stop") is None and record.get("steps", [])[-1:] == ["test_path"]}
    failed = sorted(k for k, ok in checks.items() if not ok)
    if failed:
        raise Stop(f"STOP: the first arm's record does not show a working H200 path: {failed}")
    return {"first_record_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def check_cap(spec: dict, names: list[str], sealed_root: Path = lib.SEALED_ROOT) -> dict:
    """P4-CAP A before every submission: the GPU-hours charged by every sealed attempt of the run plus the
    projection of the arms about to be submitted must stay within the cap (a repeat counts against it)."""
    charged = lib.charged_hours(spec, sealed_root)
    proj = lib.projection(spec)["per_arm"]
    coming = round(sum(proj[n]["gpu_hours"] for n in names), 3)
    if charged["total"] + coming > spec["caps"]["gpu_hours"]:
        raise Stop(f"STOP: {charged['total']} GPU-h charged + {coming} projected for {names} exceeds P4-CAP "
                   f"{spec['caps']['gpu_hours']}: author STOP")
    return {"charged_gpu_hours": charged["total"], "projected_gpu_hours": coming}


def submit(stage_dir: Path, note_path: Path, *, enable: bool, arm: str | None = None, first_record: Path | None = None,
           on_main=_note_on_main, launch_binding=None, spec_path: Path | None = None,
           sealed_root: Path = lib.SEALED_ROOT) -> dict:
    checked = check(stage_dir, note_path, on_main=on_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: P.4 real submission is disabled (needs --enable AND {ENABLE_ENV}=1)")
    stage_dir = Path(stage_dir).resolve()
    spec = lib.load_spec(stage_dir / "p4_spec.json")
    committed = Path(spec_path) if spec_path else REPO_ROOT / "r1/scripts/htcondor/trackp_p4/p4_spec.json"
    if committed.read_bytes() != (stage_dir / "p4_spec.json").read_bytes():
        raise Stop("STOP: the staged spec is not the committed spec of the launch checkout")
    checked["launch"] = (launch_binding or (lambda repo, s, rows: lib.verify_launch_p4(repo, s, rows,
                                                                                       spec_path=committed)))(
        REPO_ROOT, spec, lib.PLAN_ROWS)
    names = list(spec["arms"])
    if arm is not None:
        if arm not in names:
            raise Stop(f"STOP: {arm} is not an authorized arm")
        names = [arm]
    if names != [spec["first_arm"]]:
        checked.update(check_first_record(first_record, spec, checked["spec_sha256"], sealed_root))
        names = [n for n in names if n != spec["first_arm"]]
    checked["cap"] = check_cap(spec, names, sealed_root)
    out = []
    for name in names:
        try:
            with (stage_dir / f"P4_SUBMIT_STARTED_{name}.json").open("x") as marker:
                json.dump({"arm": name, **checked}, marker)
        except FileExistsError:
            raise Stop(f"STOP: {name} was already submitted from this stage; check the scheduler") from None
        res = subprocess.run(["condor_submit", f"p4_{name}.jdl"], cwd=stage_dir, capture_output=True, text=True,
                             timeout=600)
        if res.returncode != 0:
            raise Stop(f"STOP: condor_submit {name} rc={res.returncode}: {res.stderr.strip()[:300]}")
        entry = {"schema": "trackp_p4_submission/1", "arm": name, "condor_submit": res.stdout[-1000:],
                 "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **checked}
        with (stage_dir / "P4_SUBMISSIONS.jsonl").open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
        out.append(entry)
    return {"submitted": out}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--stage", required=True); c.add_argument("--note", required=True)
    s = sub.add_parser("submit"); s.add_argument("--stage", required=True); s.add_argument("--note", required=True)
    s.add_argument("--enable", action="store_true"); s.add_argument("--arm", default=None)
    s.add_argument("--first-record", type=Path, default=None)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            print(json.dumps(check(Path(a.stage), Path(a.note)), indent=1))
        else:
            print(json.dumps(submit(Path(a.stage), Path(a.note), enable=a.enable, arm=a.arm,
                                    first_record=a.first_record), indent=1))
    except (Stop, lib.Stop) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
