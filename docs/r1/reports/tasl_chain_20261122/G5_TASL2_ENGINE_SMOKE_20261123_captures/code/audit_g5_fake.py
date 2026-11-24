"""ENGINEERING-ONLY synthetic G.5 engine for the TASL-2 smoke (20261123).

This is NOT the reviewed harness engine. It is a *fake engine* that speaks the
``g5_tasl_engine_contract/1`` output contract so that the real paper-side job
(``sweep2/t1_tasl/g5_job.py``) can be exercised on TASL-2 without a G.5
authorization, a label, or an evidence run. It writes synthetic campaign
ledgers and audit rows, creates/cleans ``ar_*`` child cgroups under the
delegated job scope exactly as the job expects a runner to, and can spawn
safe synthetic workers for the OOM / crash / deadline / orphan scenarios.

Scenario selection: environment variable ``SMOKE_SCENARIO`` (set by the smoke
driver). Evidence side-channel (not read by the job): files under
``SMOKE_META_DIR``.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ENGINE_CONTRACT = "g5_tasl_engine_contract/1"
CAMPAIGN_SCHEMA = "trackg_g5_campaign/v1"
CHUNK_SCHEMA = "trackg_g5_audit_chunk/v1"
ROW_SCHEMA = "trackg_g5_audit_row/v1"
LEDGER_SCHEMA = "trackg_v2_diff_campaign_ledger/v1"

RUN_S = 10.0                      # synthetic executed-run seconds (below the smoke node basis)
ALLOC_GIB = 9                     # > the scope's 8G MemoryMax (item 2)
SECRET = "ENGINE-SECRET-TEXT-SMOKE-20261123"

ISOLATED = {"effective": True, "waivers": {}, "exceptions": [], "log_intact": True,
            "parent_traced_by": None, "parent_dumpable_at_accept": False}


class TruncationInvalidManager(object):      # noqa: D101 - marker only; the job greps for this class
    pass


def _meta(scenario: str, obj: dict) -> None:
    d = Path(os.environ.get("SMOKE_META_DIR", "/tmp/g5smoke_meta"))
    d.mkdir(parents=True, exist_ok=True)
    name = f"engine_{scenario}_{os.getpid()}_{uuid.uuid4().hex[:8]}.json"
    (d / name).write_text(json.dumps(obj, indent=1, sort_keys=True, default=str) + "\n")


def _cgroup_parent(argv: list[str]) -> str:
    candidate = os.environ.get("AR_TEST_CGROUP_PARENT", "")
    # the input file carries the same path; prefer the file's field when present
    for i, a in enumerate(argv):
        if a in ("--campaign", "--chunk"):
            try:
                spec = json.loads(Path(argv[i + 1]).read_text())
            except Exception:      # noqa: BLE001
                continue
            return str(spec.get("cgroup_parent") or candidate)
    return candidate


def _mk_ar(parent: str, label: str) -> Path:
    p = Path(parent) / f"ar_{label}_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    p.mkdir()
    return p


def _move(pid: int, cg: Path) -> None:
    for _ in range(100):
        try:
            (cg / "cgroup.procs").write_text(f"{pid}\n")
            return
        except OSError:
            time.sleep(0.01)
    raise RuntimeError(f"could not move {pid} into {cg}")


def _populated(cg: Path) -> bool:
    try:
        text = (cg / "cgroup.events").read_text()
    except OSError:
        return False
    return any(line.startswith("populated 1") for line in text.splitlines())


def _kill_cg(cg: Path) -> None:
    try:
        (cg / "cgroup.kill").write_text("1\n")
    except OSError:
        pass
    for _ in range(100):
        if not _populated(cg):
            break
        time.sleep(0.02)
    try:
        cg.rmdir()
    except OSError:
        pass


def _mem_events(parent: str) -> dict:
    out = {}
    try:
        for line in (Path(parent) / "memory.events").read_text().splitlines():
            k, _, v = line.partition(" ")
            out[k] = int(v)
    except OSError:
        pass
    return out


def _spawn_alloc() -> subprocess.Popen:
    """A synthetic 'edit' worker: allocates past the scope's 8G MemoryMax and dies on the kernel OOM."""
    code = ("import numpy as np\n"
            f"a = np.ones({ALLOC_GIB} * 1024**3 // 8, dtype=np.uint64)\n"
            "print(int(a[0]))\n")
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _spawn_crash(how: str) -> subprocess.Popen:
    if how == "raise":
        code = "raise RuntimeError('synthetic edit worker failure')\n"
        return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    code = ("import ctypes\n"
            "ctypes.string_at(0)\n")
    return subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _spawn_sleep(seconds: int = 600) -> subprocess.Popen:
    return subprocess.Popen(["/bin/sleep", str(seconds)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# --------------------------------------------------------------------------------------------- campaign
def _step_line(step, decision, parent=None, cand=None, diff=None, run_s=RUN_S):
    e = {"schema": LEDGER_SCHEMA, "step": step, "decision": decision,
         "manager_call": {"usage": {"prompt_tokens": 1000, "completion_tokens": 300, "wall_seconds": 30.0},
                          "request": {"cache_prompt": False}}}
    if decision in ("kept", "discarded", "discarded_divergent"):
        e["proposal"] = {"diff": diff}
        e["runs"] = [{"code_state_sha256": cand, "incumbent_code_state_sha256": parent,
                      "executed": True, "elapsed_seconds_info_only": run_s}]
        e["final_outcome"] = {"kind": "divergent" if decision == "discarded_divergent" else "ok",
                              "reason": None, "value": 0.5}
    return e


def _ledger(k: int, run_s: float = RUN_S) -> list[dict]:
    """20 manager proposals per instance (W=20): a kept chain of two diffs, a discard, invalids and a
    not-run duplicate carrying a top-level code_state_sha256 (harness report item 8)."""
    lines = [{"schema": LEDGER_SCHEMA, "step": 0, "decision": "baseline",
              "runs": [{"code_state_sha256": "B"}], "final_outcome": {"kind": "ok", "value": 0.4}}]
    lines.append(_step_line(1, "kept", "B", "C1", "d1", run_s))
    lines.append(_step_line(2, "discarded", "C1", f"S{k}", f"diff-{k}", run_s))
    for s in range(3, 20):
        lines.append(_step_line(s, "invalid_proposal"))
    lines.append({"schema": LEDGER_SCHEMA, "step": 20, "decision": "not_run_duplicate",
                  "code_state_sha256": f"S{k}", "proposal": {"diff": f"dup-diff-{k}"},
                  "manager_call": {"usage": {"prompt_tokens": 1000, "completion_tokens": 300,
                                             "wall_seconds": 30.0},
                                   "request": {"cache_prompt": False}}})
    return lines


def campaign(args) -> int:
    spec = json.loads(Path(args.campaign).read_text())
    out = Path(args.out)
    scenario = os.environ.get("SMOKE_SCENARIO", "normal")
    meta = {"scenario": scenario, "argv": sys.argv, "cwd": os.getcwd(),
            "cgroup_parent": _cgroup_parent(sys.argv), "pid": os.getpid(),
            "gpu_uuid": args.gpu_uuid, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "engine_python": sys.executable, "campaign": str(args.campaign),
            "secret_in_engine_text": SECRET}
    for inst in spec["instances"]:
        d = out / f"instance_{inst['instance']}_{inst['memory_mode']}"
        d.mkdir(parents=True)
        run_s = 99.0 if scenario == "slow-run" else RUN_S
        (d / "campaign_ledger.jsonl").write_text(
            "\n".join(json.dumps(x) for x in _ledger(inst["instance"], run_s)) + "\n")
        work = d / "runs" / "s001" / "work"
        work.mkdir(parents=True)
        (work / "model.pt").write_bytes(bytes(range(256)) * 4)      # binary output, unread by the job
    (out / "campaign_record.json").write_text(json.dumps(
        {"stop": None, "stop_kind": None} if scenario != "engine-deadline"
        else {"stop": f"{SECRET}: campaign hit its deadline", "stop_kind": "deadline"}))
    print(f"fake campaign engine ok: {len(spec['instances'])} instances; {SECRET}")
    _meta(scenario, meta)
    return 0


# --------------------------------------------------------------------------------------------- audit
def _rows(chunk: dict, overrides: dict) -> list[dict]:
    state = {u["unit"]: u["code_state_sha256"] for u in chunk["units"]}
    rows = []
    for r in chunk["runs"]:
        kind, reason, extra = overrides.get((r["unit"], r["seed"]), ("ok", None, {}))
        row = {"schema": ROW_SCHEMA, "unit": r["unit"], "seed": r["seed"], "executed": True,
               "code_state_sha256": state[r["unit"]], "value": 0.123,
               "outcome": {"kind": kind, "reason": reason, "value": 0.123},
               "isolation": dict(ISOLATED)}
        row.update(extra)
        rows.append(row)
    return rows


def audit(args) -> int:
    chunk = json.loads(Path(args.chunk).read_text())
    out = Path(args.out)
    out.mkdir(parents=True)
    scenario = os.environ.get("SMOKE_SCENARIO", "normal")
    parent = _cgroup_parent(sys.argv)
    meta = {"scenario": scenario, "argv": sys.argv, "cwd": os.getcwd(), "cgroup_parent": parent,
            "pid": os.getpid(), "gpu_uuid": args.gpu_uuid,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "engine_python": sys.executable, "chunk": str(args.chunk),
            "runs": len(chunk["runs"]), "units": len(chunk["units"]),
            "secret_in_engine_text": SECRET, "ar_created": [], "ar_killed": [],
            "oom": {}, "workers": []}
    (out / "runs").mkdir()
    (out / "runs" / "weights.npy").write_bytes(b"\x93NUMPY\xff\xfe" * 64)      # binary output, unread
    overrides: dict = {}
    runs = chunk["runs"]

    if scenario in ("deadline-child", "deliberate-kill") and runs:
        cg = _mk_ar(parent, "deadline" if scenario == "deadline-child" else "kill")
        meta["ar_created"].append(str(cg))
        child = _spawn_sleep()
        _move(child.pid, cg)
        meta["workers"].append({"pid": child.pid, "kind": "sleep", "cgroup": str(cg)})
        if scenario == "deliberate-kill":
            pidfile = os.environ.get("SMOKE_PIDFILE")
            if pidfile:
                Path(pidfile).write_text(f"{os.getpid()}\n")
        _meta(scenario, meta)
        time.sleep(600)                                # the job's subprocess timeout / the external kill
        return 0                                       # unreachable in a normal smoke

    if scenario == "engine-deadline":
        (out / "chunk_record.json").write_text(json.dumps(
            {"stop": f"{SECRET}: audit hit its deadline", "stop_kind": "deadline",
             "units_rematerialised": len(chunk["units"])}))
        print(f"fake audit engine ok (deadline); {SECRET}")
        _meta(scenario, meta)
        return 0

    if scenario == "stop-unisolated":
        overrides[(runs[0]["unit"], runs[0]["seed"])] = ("divergent", None, {"gate_refusal": {
            "check": "check_effective", "detail": SECRET}})
        rows = _rows(chunk, overrides)
        (out / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (out / "chunk_record.json").write_text(json.dumps({"stop": None, "stop_kind": "unisolated"}))
        print(f"fake audit engine ok (stop-unisolated); {SECRET}")
        _meta(scenario, meta)
        return 0

    if scenario == "gate-row":
        key = (runs[0]["unit"], runs[0]["seed"])
        overrides[key] = ("divergent", "gate_refusal", {
            "isolation": dict(ISOLATED, effective=False, waivers={"smoke": 1}),
            "gate_refusal": {"check": "check_effective", "detail": SECRET}})

    if scenario == "infra":
        key = (runs[0]["unit"], runs[0]["seed"])
        overrides[key] = ("infrastructure_failure", None, {"executed": False})
        # a never-executed infrastructure row has no isolation block
        # (removed below by post-processing)

    if scenario == "oom" and runs:
        key = (runs[0]["unit"], runs[0]["seed"])
        before = _mem_events(parent)
        # (a) a worker killed by the kernel -> nonzero_exit
        cg = _mk_ar(parent, "oomworker")
        meta["ar_created"].append(str(cg))
        worker = _spawn_alloc()
        _move(worker.pid, cg)
        rc = worker.wait(timeout=180)
        after_worker = _mem_events(parent)
        _kill_cg(cg)
        meta["workers"].append({"pid": worker.pid, "kind": "alloc-worker", "rc": rc,
                                "cgroup": str(cg), "memory_events_after": after_worker})
        overrides[key] = ("divergent", "nonzero_exit", {
            "attribution": {"memory_events_cgroup": parent, "memory_events_before": before,
                            "memory_events_after": after_worker,
                            "killed": "worker", "worker_rc": rc}})
        # (b) a frozen 'parent' process killed by the kernel -> oom_kill_memory_limit
        if len(runs) > 1:
            key2 = (runs[1]["unit"], runs[1]["seed"])
            before2 = _mem_events(parent)
            cg2 = _mk_ar(parent, "oomparent")
            meta["ar_created"].append(str(cg2))
            worker2 = _spawn_alloc()
            _move(worker2.pid, cg2)
            rc2 = worker2.wait(timeout=180)
            after2 = _mem_events(parent)
            _kill_cg(cg2)
            meta["workers"].append({"pid": worker2.pid, "kind": "alloc-frozen-parent", "rc": rc2,
                                    "cgroup": str(cg2), "memory_events_after": after2})
            overrides[key2] = ("divergent", "oom_kill_memory_limit", {
                "attribution": {"memory_events_cgroup": parent, "memory_events_before": before2,
                                "memory_events_after": after2, "killed": "frozen_parent",
                                "parent_rc": rc2}})
        meta["oom"] = {"before": before, "after_worker": after_worker}

    if scenario == "crash" and len(runs) >= 2:
        for idx, how in ((0, "raise"), (1, "segfault")):
            key = (runs[idx]["unit"], runs[idx]["seed"])
            cg = _mk_ar(parent, f"crash{idx}")
            meta["ar_created"].append(str(cg))
            worker = _spawn_crash(how)
            _move(worker.pid, cg)
            rc = worker.wait(timeout=60)
            _kill_cg(cg)
            meta["workers"].append({"pid": worker.pid, "kind": f"crash-{how}", "rc": rc, "cgroup": str(cg)})
            overrides[key] = ("divergent", "nonzero_exit",
                              {"attribution": {"killed": "worker", "worker_rc": rc,
                                               "worker_kind": f"crash-{how}"}})

    rows = _rows(chunk, overrides)
    for row in rows:
        if row["outcome"]["kind"] == "infrastructure_failure":
            row.pop("isolation", None)
            row["executed"] = False
    (out / "rows.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    (out / "chunk_record.json").write_text(json.dumps(
        {"stop": None, "stop_kind": None, "units_rematerialised": len(chunk["units"])}))
    if scenario == "crash":
        (out / "worker_crash_note.txt").write_text("synthetic edit crash: raise + ctypes segfault\n")
    print(f"fake audit engine ok: {len(rows)} rows; {SECRET}")
    _meta(scenario, meta)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="synthetic G.5 engine for the ENGINEERING smoke")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("campaign")
    c.add_argument("--campaign", required=True)
    c.add_argument("--harness-root", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--gpu-uuid", default=None)
    a = sub.add_parser("audit")
    a.add_argument("--chunk", required=True)
    a.add_argument("--harness-root", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--gpu-uuid", default=None)
    args = ap.parse_args(argv)
    return campaign(args) if args.cmd == "campaign" else audit(args)


if __name__ == "__main__":
    sys.exit(main())
