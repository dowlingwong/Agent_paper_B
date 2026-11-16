#!/usr/bin/env python3
"""S2-C4 timing pilot (ENGINEERING): 1 node x 2 instances x both memory modes on L40S.

`make-specs` derives two S2-C2 job specs (append_only_summary and none) from the reviewed example spec, with
instances=2 and a per-mode chunk id. `collect` reads the transferred job outputs (job_record.json, llama-server.log
and the HTCondor user log) from each pilot chunk, records the timing (queue wait, wall time, GGUF fetch, GPU buffer
sizes) and writes the measured job-layout proposal for the full sweep. No labels are read.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c2_lib as lib  # noqa: E402

MODES = ("append_only_summary", "none")
PILOT_INSTANCES = 2
FULL_NODES = 8
FULL_INSTANCES = 18
FULL_MODES = 2


def make_specs(base_spec_path: Path, run_id: str, out_dir: Path) -> dict:
    base = lib.validate_spec(lib.load_spec(base_spec_path))["spec"]
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise lib.Stop(f"STOP: spec output dir {out_dir} already exists")
    out_dir.mkdir(parents=True)
    specs = {}
    for mode in MODES:
        s = copy.deepcopy(base)
        s["run_id"] = run_id
        s["chunk_id"] = f"{s['collector']['node']}-{mode}-pilot"
        s["collector"]["memory_mode"] = mode
        s["collector"]["instances"] = PILOT_INSTANCES
        s["walltime_s"] = max(3600, int(base["walltime_s"]))
        p = out_dir / f"s2_c4_{mode}.json"
        p.write_text(json.dumps(s, indent=1) + "\n")
        specs[mode] = p
    (out_dir / "pilot_specs.json").write_text(json.dumps({m: str(p) for m, p in specs.items()}, indent=1) + "\n")
    return {m: str(p) for m, p in specs.items()}


TS = re.compile(r"(\d\d/\d\d \d\d:\d\d:\d\d)")


def parse_condor_log(text: str) -> dict:
    """Queue wait and wall time from the HTCondor user log (000 submit / 001 executing / 005 terminated)."""
    submit = execute = end = None
    for line in text.splitlines():
        m = TS.search(line)
        if not m:
            continue
        t = datetime.strptime(f"2026/{m.group(1)}", "%Y/%m/%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
        if "Job submitted" in line and submit is None:
            submit = t
        elif "Job executing" in line and execute is None:
            execute = t
        elif "Job terminated" in line and end is None:
            end = t
    if submit is None or execute is None or end is None:
        raise lib.Stop("STOP: HTCondor user log lacks submit/execute/terminated lines")
    if not execute >= submit or not end >= execute:
        raise lib.Stop("STOP: HTCondor user log timestamps are inconsistent")
    return {"queue_wait_s": round(execute - submit, 1), "wall_s": round(end - execute, 1)}


BUFFER = re.compile(r"CUDA0\s+model buffer size\s*=\s*([0-9.]+)\s*MiB")
KV = re.compile(r"CUDA0\s+KV buffer size\s*=\s*([0-9.]+)\s*MiB")


def parse_llama_log(text: str) -> dict:
    out = {}
    m = BUFFER.search(text)
    if m:
        out["model_buffer_mib"] = float(m.group(1))
    m = KV.search(text)
    if m:
        out["kv_buffer_mib"] = float(m.group(1))
    return out


def collect_chunk(chunk_dir: Path) -> dict:
    chunk_dir = Path(chunk_dir)
    record = json.loads((chunk_dir / "job_record.json").read_text())
    if record.get("label") != "ENGINEERING_ONLY":
        raise lib.Stop("STOP: timing pilot must be ENGINEERING_ONLY (no labels read)")
    logs = sorted(chunk_dir.glob("*.log"))
    condor = [p for p in logs if p.name.startswith("s2_c2_job") or "condor" in p.name]
    if not condor:
        raise lib.Stop("STOP: HTCondor user log missing from the transferred chunk")
    timing = parse_condor_log(condor[0].read_text(errors="replace"))
    llama = chunk_dir / "llama-server.log"
    timing.update(parse_llama_log(llama.read_text(errors="replace")) if llama.is_file() else {})
    timing.update({"chunk_id": record["chunk_id"], "mode": record["collector_mode"] if "collector_mode" in record else
                   (json.loads((chunk_dir / "out" / "manifest.json").read_text()).get("c3_label_sweep", {})
                    .get("memory_mode") if (chunk_dir / "out" / "manifest.json").is_file() else None),
                   "gpu": record["gpu"]["name"], "host": record["host"]["fqdn"],
                   "gguf_fetch_s": record["model"]["download_seconds"],
                   "collector_s": record["collector"]["seconds"],
                   "offloaded_layers": record["server"]["offloaded_layers"],
                   "total_layers": record["server"]["total_layers"]})
    return timing


def layout(entries: list[dict]) -> dict:
    if not entries:
        raise lib.Stop("STOP: no pilot timing entries")
    wall = max(e["wall_s"] for e in entries)
    full_wall = wall * (FULL_INSTANCES / PILOT_INSTANCES)
    chunks = FULL_NODES * FULL_MODES
    total_gpu_hours = full_wall * chunks / 3600.0
    return {"pilot_wall_s": wall, "pilot_instances": PILOT_INSTANCES, "full_instances": FULL_INSTANCES,
            "estimated_full_chunk_wall_s": round(full_wall, 1), "chunks": chunks,
            "estimated_total_gpu_hours": round(total_gpu_hours, 2),
            "proposed_request_walltime_s": int(min(86400, max(3600, round(full_wall * 1.3)))),
            "proposed_request_disk_kb": 50000000, "proposed_request_memory_mb": 128000,
            "proposed_chunking": "one (node, memory mode) chunk per job"}


def report(entries: list[dict], out_json: Path, out_md: Path) -> dict:
    lay = layout(entries)
    payload = {"schema": "s2_c4_timing/1", "entries": entries, "layout": lay,
               "note": "timing only; no labels read; ENGINEERING_ONLY"}
    Path(out_json).write_text(json.dumps(payload, indent=1) + "\n")
    rows = "\n".join(f"| {e['chunk_id']} | {e.get('mode')} | {e['host']} | {e.get('gpu')} | {e['queue_wait_s']} | "
                     f"{e['wall_s']} | {e['gguf_fetch_s']} | {e['collector_s']} | "
                     f"{e.get('model_buffer_mib')}/{e.get('kv_buffer_mib')} | {e['offloaded_layers']}/{e['total_layers']} |"
                     for e in entries)
    md = f"""# S2-C4 timing pilot — 1 node x {PILOT_INSTANCES} instances x both memory modes (L40S)

ENGINEERING_ONLY. Counts/timing only; no labels read. Measured on the reviewed S2-C2 job wrapper.

| chunk | mode | host | gpu | queue_wait_s | wall_s | gguf_fetch_s | collector_s | model/kv MiB | offload |
|---|---|---|---|---|---|---|---|---|---|
{rows}

## Measured layout proposal

- pilot wall (max): **{lay['pilot_wall_s']} s** for {PILOT_INSTANCES} instances; estimated full chunk
  ({FULL_INSTANCES} instances) **{lay['estimated_full_chunk_wall_s']} s**
- chunks: {lay['chunks']} (8 nodes x 2 memory modes)
- **estimated total GPU-hours: {lay['estimated_total_gpu_hours']}**
- proposed `+RequestWalltime = {lay['proposed_request_walltime_s']}` s, `request_disk = 50000000` kB,
  `request_memory = 128000` MB; one (node, memory mode) chunk per job.

These are the values to pin in the sweep-2 authorization/hand-off; S2-C3 remains a separate unit.
"""
    Path(out_md).write_text(md)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make-specs"); m.add_argument("--base"); m.add_argument("--run-id"); m.add_argument("--out-dir")
    c = sub.add_parser("collect"); c.add_argument("--chunk-dir", action="append", required=True)
    c.add_argument("--out-json", required=True); c.add_argument("--out-md", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "make-specs":
        print(json.dumps(make_specs(Path(a.base), a.run_id, Path(a.out_dir)), indent=1)); return 0
    entries = [collect_chunk(Path(p)) for p in a.chunk_dir]
    payload = report(entries, Path(a.out_json), Path(a.out_md))
    print(json.dumps(payload["layout"], indent=1)); return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lib.Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
