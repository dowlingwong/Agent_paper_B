#!/usr/bin/env python3
"""Reduce the ENGINEERING smoke captures into evidence facts (no EVIDENCE rows).

Reads captures/jobs/*.json (written by driver.py inside each delegated scope),
captures/probe_scope.json, the logs, and the real harness checkouts; writes
captures/smoke_summary.json. It also runs the paper's own checks that can be
run without a label: g5_seal.reduce_rows on the fake-engine audit rows and
g5_job.check_engines on both REAL family checkouts.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path

S = Path(os.environ.get("SMOKE_ROOT", "/home/dowling/r1_engineering/tasl2_g5_smoke_20261123"))
PAPER = Path(os.environ.get("SMOKE_PAPER", "/home/dowling/r1_tracks/t1_tasl/paper_g5smoke"))
CAP = S / "captures"
LOGS = S / "logs"
SECRET = "ENGINE-SECRET-TEXT-SMOKE-20261123"
REAL_HARNESS = {  # the exact family checkouts / pins from the task
    "G5-7": (Path("/home/dowling/r1_tracks/t1_tasl/harness_g5_7"),
             "52e3c0b00df5753a96f323a8956338d88f365276"),
    "G5-AR": (Path("/home/dowling/r1_tracks/t1_tasl/harness_g5_ar"),
              "00829da116dd206a116e12ee9b108db40c2b5cbf"),
}
sys.path.insert(0, str(PAPER / "sweep2" / "t1_tasl"))
import g1b_tasl as G      # noqa: E402
import g5_job as J        # noqa: E402
import g5_seal as SE      # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_jobs() -> dict:
    out = {}
    for p in sorted((CAP / "jobs").glob("*.json")):
        try:
            out[p.stem] = json.loads(p.read_text())
        except Exception as exc:      # noqa: BLE001
            out[p.stem] = {"error": f"{type(exc).__name__}: {exc}"}
    return out


def tar_members(attempt: Path, names: tuple) -> dict:
    got = {}
    tar = attempt / "out.tar"
    if not tar.is_file():
        return got
    with tarfile.open(tar) as t:
        for m in t:
            if m.isfile() and m.name in names:
                got[m.name] = t.extractfile(m).read()
    return got


def job_view(name: str, j: dict) -> dict:
    att = j.get("attempt") or {}
    rec = att.get("record") or {}
    out = {"node": j.get("node"), "scenario": j.get("scenario"), "kind": j.get("kind"),
           "ok": j.get("ok"), "stop": j.get("stop"), "stop_class": j.get("stop_class"),
           "error": j.get("error"),
           "engine_rc": rec.get("engine_rc"),
           "cgroup_parent": (rec.get("cgroup") or {}).get("cgroup_parent"),
           "affinity": rec.get("affinity"), "gpu": rec.get("gpu"), "environment": rec.get("environment"),
           "engine_contract": (rec.get("engine") or {}).get("truncation_invalid_in"),
           "sha256sums_ok": att.get("sha256sums_ok"),
           "secret_in_clear_files": att.get("secret_in_clear_files"),
           "engine_log_has_secret": att.get("engine_log_has_secret"),
           "out_tar_members": att.get("out_tar_members"),
           "out_tar_binary_members": att.get("out_tar_binary_members"),
           "out_tar_sha256": att.get("out_tar_sha256"),
           "out_tar_bytes": att.get("out_tar_bytes"),
           "run_cgroups_kill": att.get("run_cgroups_kill"),
           "chunk_record": att.get("chunk_record"), "campaign_record": att.get("campaign_record"),
           "audit_rows": att.get("audit_rows"), "audit_row_kinds": att.get("audit_row_kinds"),
           "audit_rows_with_attribution": att.get("audit_rows_with_attribution"),
           "attempt_dir": att.get("attempt_dir"), "attempt_exists": att.get("exists"),
           "cgroup_after_ar_dirs": (j.get("cgroup_after") or {}).get("ar_dirs"),
           "cgroup_after_oom_group": (j.get("cgroup_after") or {}).get("memory_oom_group"),
           "cgroup_before_scope": (j.get("cgroup_before") or {}).get("scope_cgroup"),
           "refusals": j.get("refusals") or [],
           "engine_meta": [m.get("meta") for m in (j.get("engine_meta") or [])]}
    out["attempt"] = str(att.get("attempt_dir") or "")
    out["attempt_dir"] = out["attempt"]
    # chunk.json + rows from the tar, for the paper's own reduce_rows / diag checks
    if out["attempt_exists"]:
        attdir = Path(out["attempt"])
        members = tar_members(attdir, ("out/chunk.json", "out/audit/rows.jsonl",
                                       "out/campaign/instance_1_history/campaign_ledger.jsonl"))
        if "out/chunk.json" in members:
            out["chunk"] = json.loads(members["out/chunk.json"])
        if "out/audit/rows.jsonl" in members:
            out["rows_lines"] = members["out/audit/rows.jsonl"].decode().splitlines()
        if "out/campaign/instance_1_history/campaign_ledger.jsonl" in members:
            out["instance_ledger_lines"] = members[
                "out/campaign/instance_1_history/campaign_ledger.jsonl"].decode().splitlines()
    return out


def literal_wrapper() -> dict:
    log = LOGS / "literal_g5_wrapper.log"
    text = log.read_text(errors="replace") if log.is_file() else ""
    rc = None
    m = re.search(r"literal_wrapper_rc=(\d+)", text)
    if m:
        rc = int(m.group(1))
    scopes = re.findall(r"scope_cgroup=(/sys/fs/cgroup/\S+)", text)
    logdir = re.findall(r"(_logs/[^ \n]+\.node\.log)", text)
    node_log = None
    if logdir:
        cand = S / "runs" / "g5smoke-engineering-20261123" / logdir[-1]
        node_log = str(cand) if cand.is_file() else logdir[-1]
    return {"log": str(log), "rc": rc, "scope_cgroups": scopes,
            "user_manager_component": any(f"user@{os.getuid()}.service" in s for s in scopes),
            "node_log": node_log, "log_sha256": sha(log) if log.is_file() else None,
            "tail": text.splitlines()[-8:]}


def real_engines() -> dict:
    out = {}
    for fam, (repo, commit) in REAL_HARNESS.items():
        ent = {"repo": str(repo), "commit": commit, "clean": None, "sha256": None, "check_engines": None,
               "error": None}
        try:
            ent["clean"] = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"],
                                          capture_output=True, text=True).stdout.strip() == ""
            ent["sha256"] = sha(repo / "src/autoresearch/trackg/audit_g5.py")
            ent["check_engines"] = J.check_engines(repo, commit, G._sh)
        except Exception as exc:      # noqa: BLE001
            ent["error"] = f"{type(exc).__name__}: {exc}"
        out[fam] = ent
    return out


def reduce_rows_check(spec: dict, view: dict) -> dict:
    if not view or "chunk" not in view or "rows_lines" not in view:
        return {"ran": False, "reason": "no chunk/rows in the attempt"}
    try:
        rows = J.read_rows(view["rows_lines"], view["chunk"])
        red = SE.reduce_rows(spec, view["rows_lines"], view["chunk"], "traindev")
        return {"ran": True, "read_rows": len(rows), "traindev_rows": len(red["rows"]),
                "evaluation_rows_dropped": red["evaluation_rows_dropped"], "ok": True}
    except Exception as exc:          # noqa: BLE001
        return {"ran": True, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    spec = json.loads((S / "spec" / "smoke_spec.json").read_text())
    probe = json.loads((CAP / "probe_scope.json").read_text()) if (CAP / "probe_scope.json").is_file() else {}
    jobs = load_jobs()
    views = {k: job_view(k, j) for k, j in jobs.items()}
    lit = literal_wrapper()
    eng = real_engines()

    recs = {}
    for name, v in views.items():
        recs[name] = {k: v.get(k) for k in
                      ("node", "kind", "scenario", "ok", "stop", "stop_class", "error", "engine_rc",
                       "cgroup_parent", "affinity", "gpu", "environment", "engine_contract", "sha256sums_ok",
                       "secret_in_clear_files", "engine_log_has_secret", "out_tar_members",
                       "out_tar_binary_members", "out_tar_sha256", "out_tar_bytes", "run_cgroups_kill",
                       "chunk_record", "campaign_record", "audit_rows", "audit_row_kinds",
                       "audit_rows_with_attribution", "cgroup_after_ar_dirs", "refusals",
                       "attempt_dir")}
        recs[name]["oom_meta"] = [m.get("oom") for m in (v.get("engine_meta") or []) if m.get("oom")]
        recs[name]["worker_meta"] = [m.get("workers") for m in (v.get("engine_meta") or []) if m.get("workers")]

    hygiene = (LOGS / "final_hygiene.txt").read_text(errors="replace") if (LOGS / "final_hygiene.txt").is_file() else ""
    free = subprocess.run(["df", "-B1", "--output=avail", str(S)], capture_output=True, text=True).stdout.split()
    du = subprocess.run(["du", "-sb", str(S / "runs")], capture_output=True, text=True).stdout.split()

    ev = {
        "schema": "g5_tasl2_engineering_smoke_captures/1",
        "label": "ENGINEERING_ONLY",
        "generated_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                        capture_output=True, text=True).stdout.strip(),
        "host": os.uname().nodename, "uid": os.getuid(),
        "paper_checkout": str(PAPER), "paper_head": subprocess.run(
            ["git", "-C", str(PAPER), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "spec_sha256": sha(S / "spec/smoke_spec.json"),
        "spec_nodes": [n["node"] for n in spec["nodes"]],
        "free_disk_bytes": int(free[1]) if len(free) > 1 else None,
        "runs_tree_bytes": int(du[0]) if du else None,
        "probe": {k: probe.get(k) for k in
                  ("user_manager_component_present", "systemd_version", "siblings", "kill_probe",
                   "user_manager_oomd_props")} | {"cgroup": probe.get("cgroup")},
        "literal_g5_wrapper": lit,
        "real_engines": eng,
        "jobs": recs,
        "paper_checks": {
            "check_engines_contract": {
                "G5-7": (eng.get("G5-7") or {}).get("check_engines"),
                "G5-AR": (eng.get("G5-AR") or {}).get("check_engines")},
            "reduce_rows_smoke_ok_audit": reduce_rows_check(spec, views.get("smoke_ok_audits_normal")),
        },
        "hygiene": hygiene,
    }
    (CAP / "smoke_summary.json").write_text(json.dumps(ev, indent=1, sort_keys=True, default=str) + "\n")
    # short console table
    for name, v in sorted(recs.items()):
        print(f"{name:42s} ok={v['ok']!s:5s} stop_class={v['stop_class']!s:14s} "
              f"secret_clear={v['secret_in_clear_files']} ar_after={v['cgroup_after_ar_dirs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
