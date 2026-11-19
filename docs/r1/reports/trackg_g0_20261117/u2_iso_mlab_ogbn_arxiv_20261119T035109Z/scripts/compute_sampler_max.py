"""Compute the whole-smoke GPU upper bound from the 1 s nvidia-smi compute-app sampler.

Usage: python3 compute_sampler_max.py <gpu_uuid> <required_sampler.csv> <timestamped_sampler.csv> <out.json>

The required sampler is the unit's exact command
  nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1
It has no timestamp column, so the maximum it pins is the maximum single-row used_memory on the
used card.  A companion sampler with the same query plus `timestamp` is run concurrently so that
rows can be grouped into per-second samples (gap > 0.5 s starts a new sample) and the conservative
per-sample sum over the used card can be computed; that sum is the reported whole-smoke upper bound
(it includes any co-tenant by construction).  The CSV header is never counted.

Output JSON keys: gpu_uuid, required_sampler, required_sampler_sha256, max_single_row_mib,
used_card_rows, distinct_pids, samples_with_used_card, max_per_sample_sum_mib,
whole_smoke_upper_bound_mib, whole_smoke_upper_bound_label, sampler_duration_seconds, notes.
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_csv(path: Path, field_count: int, has_ts: bool):
    header = None
    rows = []
    if not path.exists():
        return header, rows
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("gpu_uuid"):
            header = line
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        uuid = parts[0]
        try:
            pid = int(parts[1])
        except ValueError:
            continue
        m = re.match(r"^(\d+)", parts[2])
        if not m:
            continue
        used = int(m.group(1))
        ts = None
        if has_ts and len(parts) > 3:
            ts = parts[3]
        rows.append({"gpu_uuid": uuid, "pid": pid, "used_mib": used, "ts": ts})
    return header, rows


def main() -> int:
    gpu = sys.argv[1]
    req_path = Path(sys.argv[2])
    tsf_path = Path(sys.argv[3])
    out_path = Path(sys.argv[4])

    req_header, req_rows = parse_csv(req_path, 3, False)
    used = [r for r in req_rows if r["gpu_uuid"] == gpu]
    max_row = max((r["used_mib"] for r in used), default=0)
    pids = sorted({r["pid"] for r in used})

    # Group the timestamped rows into samples: within one nvidia-smi sample the per-row timestamps
    # differ by milliseconds; consecutive samples are ~1 s apart, so a > 0.5 s gap starts a sample.
    groups: list[list[dict]] = []
    ts_rows = []
    _, tsf_rows = parse_csv(tsf_path, 4, True)
    for r in tsf_rows:
        if r["ts"] is None:
            continue
        try:
            r["dt"] = datetime.strptime(r["ts"], "%Y/%m/%d %H:%M:%S.%f")
        except ValueError:
            continue
        ts_rows.append(r)
    ts_rows.sort(key=lambda r: r["dt"])
    for r in ts_rows:
        if not groups or (r["dt"] - groups[-1][-1]["dt"]).total_seconds() > 0.5:
            groups.append([r])
        else:
            groups[-1].append(r)
    sums = []
    used_groups = 0
    for g in groups:
        s = sum(r["used_mib"] for r in g if r["gpu_uuid"] == gpu)
        if s or any(r["gpu_uuid"] == gpu for r in g):
            used_groups += 1
            sums.append(s)
    max_sum = max(sums, default=0)

    duration = 0.0
    if ts_rows:
        duration = round((ts_rows[-1]["dt"] - ts_rows[0]["dt"]).total_seconds(), 1)

    out = {
        "gpu_uuid": gpu,
        "required_sampler_command": (
            "nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1"
        ),
        "required_sampler": str(req_path),
        "required_sampler_sha256": sha(req_path) if req_path.exists() else None,
        "required_sampler_header": req_header,
        "required_sampler_total_rows": len(req_rows),
        "used_card_rows": len(used),
        "distinct_pids": pids,
        "max_single_row_mib": max_row,
        "timestamped_sampler": str(tsf_path),
        "timestamped_sampler_sha256": sha(tsf_path) if tsf_path.exists() else None,
        "timestamped_samples": len(groups),
        "samples_with_used_card": used_groups,
        "max_per_sample_sum_mib": max_sum,
        "whole_smoke_upper_bound_mib": max_sum,
        "whole_smoke_upper_bound_label": (
            "whole-smoke upper bound over the GPU(s) used, from the 1 s compute-app sampler maximum "
            "(per-sample sum over the used card's rows; includes co-tenants by construction); "
            "NOT a per-run peak and NOT attributed to the baseline process tree"
        ),
        "sampler_duration_seconds": duration,
        "notes": [
            "header lines are not counted",
            "the required sampler is the unit's exact command; the timestamped companion is used only "
            "to group rows into per-sample sums",
            "a single-row maximum equals the per-sample sum when the used card carries one compute app",
        ],
    }
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
