"""Capture one sealed G.1b TASL-7 note-2 attempt (small evidence, no out.tar). ENGINEERING_ONLY."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

attempt, sealed, spec, node, wall, outdir, origin_main = sys.argv[1:8]
attempt, sealed, spec, outdir = Path(attempt), Path(sealed), Path(spec), Path(outdir)
wall = float(wall)
outdir.mkdir(parents=True, exist_ok=True)


def sha(p: Path) -> str:
    return hashlib.sha256(path_bytes(p)).hexdigest()


def path_bytes(p: Path) -> bytes:
    return Path(p).read_bytes()


rec = json.loads((attempt / "job_record.json").read_text())
rcpt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())

rows_n = eff_n = intact_n = ok_n = fail_n = 0
waivers = set()
exceptions = 0
for rj in sorted((attempt / "out").glob("*/runs.jsonl")):
    for line in rj.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows_n += 1
        iso = r.get("isolation") or {}
        eff_n += 1 if iso.get("effective") is True else 0
        intact_n += 1 if iso.get("log_intact") is True else 0
        if iso.get("waivers"):
            waivers.add(json.dumps(iso["waivers"], sort_keys=True))
        exceptions += len(iso.get("exceptions") or [])
        fail_n += 1 if r.get("failure") else 0
        ok_n += 1 if r.get("success") else 0
iso = {"rows": rows_n, "isolation_effective_rows": eff_n, "log_intact_rows": intact_n,
       "waivers": sorted(waivers), "exceptions_n": exceptions, "failed_rows": fail_n, "successful_rows": ok_n,
       "all_effective": bool(rows_n) and eff_n == rows_n and intact_n == rows_n and not waivers and exceptions == 0}
(outdir / f"{node}.isolation.json").write_text(json.dumps(iso, indent=1) + "\n")

files = {}
for name in ("out.tar", "job_record.json", "SHA256SUMS", "SEAL_RECEIPT.json", "node.log"):
    p = sealed / name
    if p.is_file():
        files[name] = sha(p)
(outdir / f"{node}.sealed.sha256").write_text("".join(f"{v}  {k}\n" for k, v in files.items()))
shutil.copy2(sealed / "SEAL_RECEIPT.json", outdir / f"{node}.SEAL_RECEIPT.json")
shutil.copy2(sealed / "SHA256SUMS", outdir / f"{node}.sealed.SHA256SUMS")
shutil.copy2(attempt / "job_record.json", outdir / f"{node}.job_record.json")
log = rec.get("node_log")
if log and Path(log).is_file():
    shutil.copy2(log, outdir / f"{node}.node.log")

summary = {
    "node": node, "host": (rec.get("host") or {}).get("host"), "attempt": rec.get("attempt"),
    "run_id": rec.get("run_id"), "spec_sha256": rec.get("spec_sha256"),
    "harness_commit": rec.get("harness_commit"), "launch_origin_main": origin_main,
    "started_utc": rec.get("started_utc"), "finished_utc": rec.get("finished_utc"),
    "wall_seconds": wall, "gpu_hours": round(wall / 3600.0, 4),
    "deadline_s": rec.get("deadline_s"), "timeout_basis": rec.get("timeout_basis"),
    "stop": rec.get("stop"), "stop_class": rec.get("stop_class"),
    "runs": rec.get("runs"), "parts": rec.get("parts"), "timing": rec.get("timing"),
    "determinism": rec.get("determinism"), "gpu": rec.get("gpu"), "environment": rec.get("environment"),
    "data": rec.get("data"), "cgroup": rec.get("cgroup"), "affinity": rec.get("affinity"),
    "lease": rec.get("lease"), "foreign_checks": rec.get("foreign_checks"),
    "isolation": iso, "sealed_path": str(sealed), "sealed_files_sha256": files, "receipt": rcpt,
}
(outdir / f"{node}.summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
print(json.dumps({"node": node, "attempt": rec.get("attempt"), "wall_seconds": wall,
                  "runs": rec.get("runs"), "isolation_all_effective": iso["all_effective"],
                  "sealed": str(sealed)}, indent=1))
