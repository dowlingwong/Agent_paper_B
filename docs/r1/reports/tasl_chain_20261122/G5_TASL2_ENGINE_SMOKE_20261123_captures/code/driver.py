#!/usr/bin/env python3
"""ENGINEERING-ONLY TASL-2 G.5 job-path smoke driver (20261123).

Runs *inside* the real delegated systemd scope created by
``bin/smoke_wrapper.sh`` with the exact argv of ``t1_tasl_node.sh``'s g5 kind
(``systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p
MemorySwapMax=0`` + ``AR_TEST_CGROUP_PARENT`` + ``taskset``).

It calls the REAL paper-side ``g5_job.run_job`` with a synthetic spec and a
*fake* ``autoresearch.trackg.audit_g5`` engine (a clean git checkout under
``fake_harness_g7`` / ``fake_harness_ar``). Nothing here is an evidence run:
no label, no sealed file, no G.5 authorization, no signed note.

usage: driver.py job <campaigns|audits> <node> <scenario>
       driver.py probe
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

S_ROOT = Path(os.environ.get("SMOKE_ROOT", "/home/dowling/r1_engineering/tasl2_g5_smoke_20261123"))
PAPER = Path(os.environ.get("SMOKE_PAPER", "/home/dowling/r1_tracks/t1_tasl/paper_g5smoke"))
SPEC_PATH = S_ROOT / "spec" / "smoke_spec.json"
SERVER_RECORD = S_ROOT / "spec" / "server_record.json"
META = S_ROOT / "work" / "meta"
CAPT = S_ROOT / "captures"
PIDFILE = S_ROOT / "work" / "engine.pid"
SECRET = "ENGINE-SECRET-TEXT-SMOKE-20261123"

sys.path.insert(0, str(PAPER / "sweep2" / "t1_tasl"))
import g1b_tasl as G        # noqa: E402
import g4_tasl as T4        # noqa: E402
import g5_tasl as S         # noqa: E402
import g5_job as J          # noqa: E402


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def fake_get(spec: dict):
    def get(url: str, timeout: float = 10.0):
        if url.endswith("/health"):
            return 200, b'{"status":"ok"}'
        props = {"default_generation_settings": {"n_ctx": 32768}, "total_slots": 1,
                 "build_info": T4.props_build(spec["proposer"]["expected_build"]),
                 "model_path": spec["proposer"]["model_path"]}
        return 200, json.dumps(props).encode()
    return get


def fake_setup(harness, node, base, out):
    data = Path(base) / "data"
    data.mkdir(parents=True, exist_ok=True)
    return {"data_root": str(data)}


def engine_factory(scenario: str):
    def engine(argv, **kw):
        env = dict(kw.get("env") or {})
        env.update({"SMOKE_SCENARIO": scenario, "SMOKE_META_DIR": str(META),
                    "SMOKE_PIDFILE": str(PIDFILE)})
        kw["env"] = env
        META.mkdir(parents=True, exist_ok=True)
        inv = {"utc": utc(), "scenario": scenario, "argv": argv, "cwd": kw.get("cwd"),
               "timeout": kw.get("timeout"),
               "env": {k: env.get(k) for k in
                       ("PYTHONPATH", "AR_TRACKG_DATA_ROOT", "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES",
                        "_CONDOR_AssignedGPUs", "SMOKE_SCENARIO", "AR_TEST_CGROUP_PARENT")}}
        _write(META / f"invocation_{scenario}_{os.getpid()}_{time.time_ns()}.json", inv)
        return subprocess.run(argv, **kw)
    return engine


def cgroup_scan(parent: str | None = None) -> dict:
    parent = parent or os.environ.get("AR_TEST_CGROUP_PARENT", "")
    out = {"scope_cgroup": parent, "ar_dirs": [], "memory_oom_group": None, "memory_max": None,
           "swap_max": None, "systemd_run_version": None, "unit": Path(parent).name if parent else None}
    p = Path(parent)
    for name in ("memory.oom.group", "memory.max", "memory.swap.max"):
        try:
            out[name.replace(".", "_")] = (p / name).read_text().strip()
        except OSError:
            pass
    for child in sorted(p.glob("ar_*")):
        out["ar_dirs"].append({"name": child.name, "populated": _populated(child),
                              "procs": _procs(child)})
    try:
        out["systemd_run_version"] = subprocess.run(
            ["systemd-run", "--version"], capture_output=True, text=True, timeout=20
        ).stdout.splitlines()[:1]
    except Exception:       # noqa: BLE001
        pass
    try:
        r = subprocess.run(["systemctl", "--user", "show", out["unit"], "-p", "ManagedOOMMemoryPressure",
                            "-p", "OOMPolicy", "-p", "MemoryMax", "-p", "Delegate"],
                           capture_output=True, text=True, timeout=20)
        out["systemctl_show"] = r.stdout.strip()
    except Exception:       # noqa: BLE001
        pass
    try:
        r = subprocess.run(["oomctl"], capture_output=True, text=True, timeout=20)
        out["oomd_monitors_scope"] = bool(out["unit"] and out["unit"] in r.stdout)
        out["oomd_lines"] = [ln.strip() for ln in r.stdout.splitlines()
                             if out["unit"] in ln or "Monitored CGroups" in ln or "Default Memory" in ln][:10]
    except Exception:       # noqa: BLE001
        pass
    return out


def _populated(cg: Path) -> bool:
    try:
        return any(ln.startswith("populated 1") for ln in (cg / "cgroup.events").read_text().splitlines())
    except OSError:
        return False


def _procs(cg: Path) -> int:
    try:
        return len([x for x in (cg / "cgroup.procs").read_text().split() if x])
    except OSError:
        return -1


def attempt_evidence(attempt: Path) -> dict:
    ev: dict = {"attempt_dir": str(attempt), "exists": attempt.is_dir()}
    if not attempt.is_dir():
        return ev
    ev["entries"] = sorted(p.name for p in attempt.iterdir())
    rec_path, diag_path = attempt / "job_record.json", attempt / "diagnostics.json"
    if rec_path.is_file():
        rec = json.loads(rec_path.read_text())
        ev["record"] = {k: rec.get(k) for k in
                        ("attempt", "stop", "stop_class", "engine_rc", "gpu_seconds", "started_utc", "finished_utc",
                         "cgroup", "affinity", "gpu", "environment", "harness", "lease", "data", "options",
                         "engine", "server_props_before", "server_props_after", "foreign_checks", "ptrace_scope",
                         "out_tar_sha256", "deadline_epoch", "node_log")}
        ev["record_sha256"] = _sha(rec_path)
    if diag_path.is_file():
        ev["diagnostics"] = json.loads(diag_path.read_text())
        ev["diagnostics_sha256"] = _sha(diag_path)
    clear_text = ""
    for name in ("job_record.json", "diagnostics.json", "SHA256SUMS"):
        p = attempt / name
        if p.is_file():
            clear_text += p.read_text(errors="replace")
    ev["secret_in_clear_files"] = SECRET in clear_text
    if (attempt / "SHA256SUMS").is_file():
        r = subprocess.run(["sha256sum", "-c", "--quiet", "SHA256SUMS"], cwd=attempt,
                           capture_output=True, text=True)
        ev["sha256sums_ok"] = r.returncode == 0
        ev["sha256sums_sha256"] = _sha(attempt / "SHA256SUMS")
    tar = attempt / "out.tar"
    if tar.is_file():
        import tarfile
        ev["out_tar_sha256"] = _sha(tar)
        ev["out_tar_bytes"] = tar.stat().st_size
        with tarfile.open(tar) as t:
            names = [m.name for m in t if m.isfile()]
            ev["out_tar_members"] = names
            ev["out_tar_binary_members"] = [n for n in names
                                            if n.endswith((".pt", ".npy", ".bin", ".blob", ".pkl"))]
            ev["engine_log_has_secret"] = False
            for member in ("out/engine.log", "out/run_cgroups_kill.json", "out/audit/chunk_record.json",
                           "out/campaign/campaign_record.json"):
                if member not in names:
                    continue
                try:
                    raw = t.extractfile(member).read().decode("utf-8", "replace")
                except Exception:       # noqa: BLE001
                    continue
                if member == "out/engine.log" and SECRET in raw:
                    ev["engine_log_has_secret"] = True
                if member == "out/run_cgroups_kill.json":
                    ev["run_cgroups_kill"] = json.loads(raw)
                if member == "out/audit/chunk_record.json":
                    ev["chunk_record"] = json.loads(raw)
                if member == "out/campaign/campaign_record.json":
                    ev["campaign_record"] = json.loads(raw)
            if "out/audit/rows.jsonl" in names:
                rows = [json.loads(x) for x in t.extractfile("out/audit/rows.jsonl").read().decode().splitlines()
                        if x.strip()]
                ev["audit_rows"] = len(rows)
                ev["audit_row_kinds"] = sorted({(r.get("outcome") or {}).get("kind") for r in rows})
                ev["audit_rows_with_attribution"] = [r for r in rows if r.get("attribution")]
    return ev


def _sha(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_attempt(spec: dict, node: str, jobname: str) -> Path | None:
    base = J.job_dir(spec, node, jobname)
    found = []
    if base.is_dir():
        for p in base.rglob("job_record.json"):
            if p.parent.name.startswith("attempt-"):
                found.append(p.parent)
    return sorted(found)[-1] if found else None


def find_refusals(spec: dict) -> list[dict]:
    root = J.run_root(spec) / "_refusals"
    out = []
    if root.is_dir():
        for p in sorted(root.glob("*.json")):
            try:
                out.append({"file": p.name, "sha256": _sha(p), "record": json.loads(p.read_text())})
            except Exception:       # noqa: BLE001
                pass
    return out


def _run_once(kind: str, node: str, scenario: str):
    spec = json.loads(SPEC_PATH.read_text())
    jobname = f"{kind}-wave1"
    if scenario == "deadline-child":
        J.STARTUP_RESERVE_S = 60          # reach the job's own subprocess timeout in ~65 s (engineering)
    ctx = {"K": 10, "K_row": None}
    META.mkdir(parents=True, exist_ok=True)
    meta_before = {p.name for p in META.glob("engine_*.json")}
    refusals_before = len(find_refusals(spec))
    result: dict = {"mode": "job", "kind": kind, "node": node, "job": jobname, "scenario": scenario,
                    "utc": utc(), "hostname": os.uname().nodename,
                    "cgroup_before": cgroup_scan()}
    try:
        rec = J.run_job(SPEC_PATH, node, jobname, ctx, engine=engine_factory(scenario),
                        setup=fake_setup, get=fake_get(spec),
                        server_record=SERVER_RECORD if kind == "campaigns" else None,
                        node_log=os.environ.get("G5_TASL_NODE_LOG"))
        result["ok"] = True
        result["stop"] = rec.get("stop")
        result["stop_class"] = rec.get("stop_class")
        rc = 0
    except J.Stop as exc:
        result["ok"] = False
        result["error"] = str(exc)
        rc = 4
    except Exception as exc:         # noqa: BLE001
        result["ok"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
        rc = 5
    refusals_after = find_refusals(spec)
    result["refusals"] = refusals_after
    result["new_refusals"] = refusals_after[refusals_before:]
    attempt = None if result["new_refusals"] else find_attempt(spec, node, jobname)
    result["attempt"] = attempt_evidence(attempt) if attempt else None
    if not result["ok"] and result.get("attempt") and result["attempt"].get("record"):
        result["stop"] = result["attempt"]["record"].get("stop")
        result["stop_class"] = result["attempt"]["record"].get("stop_class")
    result["cgroup_after"] = cgroup_scan()
    cleaned = []
    for child in Path(os.environ.get("AR_TEST_CGROUP_PARENT", "")).glob("ar_*"):
        if not _populated(child):
            try:
                child.rmdir()
                cleaned.append(child.name)
            except OSError:
                pass
    if cleaned:
        result["cleaned_empty_ar_dirs"] = cleaned
    result["engine_meta"] = []
    for p in sorted(META.glob("engine_*.json")):
        if p.name in meta_before:
            continue
        try:
            m = json.loads(p.read_text())
        except Exception:       # noqa: BLE001
            continue
        if m.get("scenario") == scenario:
            result["engine_meta"].append({"file": p.name, "meta": m})
    return result, rc


def cmd_job(kind: str, node: str, scenario: str) -> int:
    result, rc = _run_once(kind, node, scenario)
    tag = f"{node}_{kind}_{scenario}"
    _write(CAPT / "jobs" / f"{tag}.json", result)
    brief = {"tag": tag, "ok": result["ok"], "stop_class": result.get("stop_class"),
             "error": result.get("error"), "attempt": result["attempt"] and result["attempt"].get("attempt_dir")}
    print("SMOKE_RESULT " + json.dumps(brief))
    return rc


def _collect_scope_pids(cg: Path) -> list[int]:
    pids = []
    try:
        for proc in cg.rglob("cgroup.procs"):
            for x in proc.read_text().split():
                pids.append(int(x))
    except OSError:
        pass
    return pids


def cmd_orphan() -> int:
    """Old-populated-sibling scan (follow-ups review m2 / round-2 m3, smoke item 11 & (b),(d)).

    1. start a second, sibling delegated scope whose own ar_* child cgroup holds a sleep;
    2. the next job's start-of-job scan must refuse before any attempt, naming the sibling unit;
    3. inspect + clear the orphan by hand (the operator rule);
    4. the same job then runs clean.
    """
    spec = json.loads(SPEC_PATH.read_text())
    ready = S_ROOT / "work" / "sibling_ready.json"
    logp = S_ROOT / "work" / "sibling_scope.log"
    if ready.exists():
        ready.unlink()
    result: dict = {"mode": "orphan", "utc": utc(), "hostname": os.uname().nodename}
    result["cgroup_before"] = cgroup_scan()
    with logp.open("w") as fh:
        popen = subprocess.Popen(["systemd-run", "--user", "--scope", "-p", "Delegate=yes", "--",
                                  sys.executable, str(S_ROOT / "bin" / "sibling_scope.py"), str(ready)],
                                 stdout=fh, stderr=subprocess.STDOUT)
    info = None
    for _ in range(120):
        if ready.is_file():
            try:
                info = json.loads(ready.read_text())
                break
            except Exception:       # noqa: BLE001
                pass
        time.sleep(0.25)
    result["sibling"] = info
    if not info:
        result["error"] = "sibling scope did not report ready"
        _write(CAPT / "jobs" / "smoke_orphan_rule.json", result)
        return 5
    cg = Path(info["scope_cgroup"])
    result["sibling_readable"] = {"scope_cgroup": str(cg), "app_slice": str(cg.parent),
                                  "same_user_manager": f"user@{os.getuid()}.service" in cg.parts[:-1],
                                  "populated_ar": [(str(ar), (ar / "cgroup.events").read_text().splitlines())
                                                   for ar in cg.glob("ar_*")]}
    first, rc1 = _run_once("campaigns", "smoke_orphan", "normal")
    result["first_run"] = {"ok": first["ok"], "error": first.get("error"), "rc": rc1,
                           "new_refusals": first.get("new_refusals"), "attempt": first.get("attempt"),
                           "cgroup_before_ar": (first.get("cgroup_before") or {}).get("ar_dirs")}
    # operator rule: inspect and clear the scope by hand before any further job
    killed = []
    for _ in range(200):
        pids = _collect_scope_pids(cg)
        if not pids:
            break
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                killed.append(pid)
            except ProcessLookupError:
                pass
        time.sleep(0.05)
    for _ in range(100):
        if not cg.exists():
            break
        time.sleep(0.05)
    try:
        popen.terminate()
        popen.wait(timeout=10)
    except Exception:       # noqa: BLE001
        popen.kill()
    result["cleanup"] = {"killed": killed, "scope_gone": not cg.exists(),
                         "ar_left": [str(ar) for ar in cg.glob("ar_*")] if cg.exists() else []}
    second, rc2 = _run_once("campaigns", "smoke_orphan", "normal")
    result["second_run"] = {"ok": second["ok"], "error": second.get("error"), "rc": rc2,
                            "attempt": second.get("attempt"),
                            "new_refusals": second.get("new_refusals")}
    rc = 0 if (not first["ok"] and "hold processes" in str(first.get("error"))
               and second["ok"]) else 4
    result["ok"] = rc == 0
    _write(CAPT / "jobs" / "smoke_orphan_rule.json", result)
    print("SMOKE_RESULT " + json.dumps({"tag": "smoke_orphan_rule", "ok": result["ok"],
                                        "first_error": first.get("error"),
                                        "second_ok": second["ok"]}))
    return rc


def cmd_probe() -> int:
    cg = cgroup_scan()
    parent = Path(cg["scope_cgroup"])
    app_slice = parent.parent
    sib = []
    for entry in sorted(app_slice.iterdir()):
        if entry == parent or not entry.is_dir():
            continue
        try:
            events = (entry / "cgroup.events").read_text()
            procs = len([x for x in (entry / "cgroup.procs").read_text().split() if x])
            sib.append({"name": entry.name, "readable": True, "events": events.splitlines(),
                        "procs": procs})
        except OSError as exc:
            sib.append({"name": entry.name, "readable": False, "error": type(exc).__name__})
    # the job user can write cgroup.kill of a child in the delegated scope
    kill_probe = {"scope": cg["scope_cgroup"]}
    ar = parent / f"ar_killprobe_{os.getpid()}_1"
    try:
        ar.mkdir()
        child = subprocess.Popen(["/bin/sleep", "60"])
        (ar / "cgroup.procs").write_text(f"{child.pid}\n")
        kill_probe.update({"ar": str(ar), "child_pid": child.pid,
                           "populated_before": _populated(ar),
                           "kill_write_ok": bool((ar / "cgroup.kill").write_text("1\n") or True)})
        child.wait(timeout=30)
        kill_probe["populated_after"] = _populated(ar)
        ar.rmdir()
        kill_probe["rmdir_ok"] = True
    except Exception as exc:         # noqa: BLE001
        kill_probe["error"] = f"{type(exc).__name__}: {exc}"
    oomd_unit_props = {}
    try:
        r = subprocess.run(["systemctl", "--user", "show", f"user@{os.getuid()}.service",
                            "-p", "ManagedOOMMemoryPressure", "-p", "ManagedOOMMemoryPressureLimit"],
                           capture_output=True, text=True, timeout=20)
        oomd_unit_props = dict(ln.split("=", 1) for ln in r.stdout.splitlines() if "=" in ln)
    except Exception:       # noqa: BLE001
        pass
    out = {"mode": "probe", "utc": utc(), "hostname": os.uname().nodename,
           "cgroup": cg, "user_manager_component_present": f"user@{os.getuid()}.service" in parent.parts[:-1],
           "app_slice": str(app_slice), "siblings": sib, "kill_probe": kill_probe,
           "user_manager_oomd_props": oomd_unit_props,
           "systemd_version": subprocess.run(["systemctl", "--version"], capture_output=True,
                                             text=True).stdout.splitlines()[:1]}
    _write(CAPT / "probe_scope.json", out)
    print("SMOKE_PROBE " + json.dumps({k: out[k] for k in
                                       ("user_manager_component_present", "systemd_version")}))
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: driver.py job <campaigns|audits> <node> <scenario> | probe", file=sys.stderr)
        return 2
    mode = sys.argv[1]
    if mode == "probe":
        return cmd_probe()
    if mode == "job":
        return cmd_job(sys.argv[2], sys.argv[3], sys.argv[4])
    if mode == "orphan":
        return cmd_orphan()
    print(f"unknown mode {mode}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
