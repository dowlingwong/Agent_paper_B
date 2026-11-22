#!/usr/bin/env python3
"""Summarise the G.1b TASL-2 run captures for the result memo (read-only over the captures dir).

Reads <CAP>/_harvest/remote_harvest.txt (remote sha256sum -c results + remote sha256s) and each node's captured
attempt directory (job_record.json, SEAL_RECEIPT.json, SHA256SUMS, node.log). Prints a JSON blob and a markdown
table. Never touches the host.

Usage: python3 summarize.py <captures_dir>
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

NODES = ["mlab_ogbn_arxiv", "mlgym_fmnist", "mlab_imdb", "mlgym_houseprice"]
EXPECTED_RUNS = 460
GPU_CAP_H = 100.0


def sha256_of(p):
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts(s):
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def harvest_blocks(cap: Path) -> dict:
    hp = cap / "_harvest" / "remote_harvest.txt"
    blocks, cur = {}, None
    if not hp.is_file():
        return blocks
    for line in hp.read_text(errors="replace").splitlines():
        if line.startswith("NODE_BEGIN "):
            cur = line.split()[1]
            blocks[cur] = {}
        elif line.startswith("NODE_END "):
            cur = None
        elif cur is not None:
            for key in ("SEALED_ATTEMPT", "RUNS_ATTEMPT", "SEALED_ALL", "RUNS_ALL", "REFUSALS"):
                if line.startswith(key + "="):
                    blocks[cur][key] = line[len(key) + 1:].strip()
            for key in ("SHA_VERIFY_SEALED_RC", "SHA_VERIFY_RUNS_RC"):
                if line.startswith(key + "="):
                    blocks[cur][key] = line.split("=", 1)[1].strip()
            if line.startswith("SEALED_SHA_"):
                name, val = line[len("SEALED_SHA_"):].split("=", 1)
                blocks[cur].setdefault("sealed_sha", {})[name] = val.strip()
            if line.startswith("RUNS_SHA_"):
                name, val = line[len("RUNS_SHA_"):].split("=", 1)
                blocks[cur].setdefault("runs_sha", {})[name] = val.strip()
    return blocks


def node_attempt_dirs(cap, node):
    d = cap / node
    if not d.is_dir():
        return []
    return sorted([p for p in d.iterdir() if p.is_dir() and p.name.startswith("attempt-")])


def pick_attempt(dirs):
    if not dirs:
        return None
    sealed = [d for d in dirs if (d / "SEAL_RECEIPT.json").is_file()]
    pool = sealed or dirs
    return sorted(pool, key=lambda p: int(p.name.split("-")[1]))[-1]


def summarise(cap: Path) -> dict:
    blocks = harvest_blocks(cap)
    out = {"nodes": [], "gpu_hours_total": 0.0, "core_hours_total": 0.0}
    for node in NODES:
        rec = {"node": node}
        dirs = node_attempt_dirs(cap, node)
        rec["attempt_dirs"] = [d.name for d in dirs]
        a = pick_attempt(dirs)
        hb = blocks.get(node, {})
        rec["harvest"] = {k: hb.get(k) for k in ("SEALED_ATTEMPT", "RUNS_ATTEMPT", "SHA_VERIFY_SEALED_RC",
                                                 "SHA_VERIFY_RUNS_RC", "REFUSALS") if k in hb}
        rec["sealed"] = bool(a and (a / "SEAL_RECEIPT.json").is_file())
        rec["attempt"] = a.name if a else None
        if a is None:
            rec["state"] = "not_run"
            out["nodes"].append(rec)
            continue
        jr = json.loads((a / "job_record.json").read_text()) if (a / "job_record.json").is_file() else None
        rr = json.loads((a / "SEAL_RECEIPT.json").read_text()) if (a / "SEAL_RECEIPT.json").is_file() else None
        rec["receipt"] = rr
        rec["sha"] = {
            "job_record.json": sha256_of(a / "job_record.json"),
            "SEAL_RECEIPT.json": sha256_of(a / "SEAL_RECEIPT.json"),
            "SHA256SUMS": sha256_of(a / "SHA256SUMS"),
            "node.log": sha256_of(a / "node.log"),
        }
        if jr:
            st, fi = parse_ts(jr.get("started_utc")), parse_ts(jr.get("finished_utc"))
            wall_s = (fi - st).total_seconds() if st and fi else None
            rec.update({
                "device": jr.get("device"),
                "host": (jr.get("host") or {}).get("host"),
                "started_utc": jr.get("started_utc"),
                "finished_utc": jr.get("finished_utc"),
                "wall_s": wall_s,
                "wall_h": round(wall_s / 3600, 4) if wall_s else None,
                "runs": jr.get("runs"),
                "parts": jr.get("parts"),
                "stop": jr.get("stop"),
                "stop_class": jr.get("stop_class"),
                "timeout_basis": jr.get("timeout_basis"),
                "deadline_s": jr.get("deadline_s"),
                "determinism": jr.get("determinism"),
                "node_log": jr.get("node_log"),
                "gpu": jr.get("gpu"),
                "affinity": jr.get("affinity"),
                "projection": jr.get("projection"),
            })
            if jr.get("device") == "gpu" and wall_s:
                rec["gpu_h"] = round(wall_s / 3600, 4)
                out["gpu_hours_total"] += rec["gpu_h"]
            elif jr.get("device") == "cpu" and wall_s:
                cores = len(jr.get("affinity") or [])
                rec["cores"] = cores
                rec["core_h"] = round(wall_s / 3600 * cores, 4)
                out["core_hours_total"] += rec["core_h"]
            # cross-checks
            if rr:
                rec["cross_check"] = {
                    "receipt.job_record_sha256 == local job_record sha256":
                        rr.get("job_record_sha256") == rec["sha"]["job_record.json"],
                    "receipt.node_log_sha256 == local node.log sha256":
                        rr.get("node_log_sha256") == rec["sha"]["node.log"],
                }
        out["nodes"].append(rec)
    out["gpu_cap_h"] = GPU_CAP_H
    out["gpu_cap_ok"] = out["gpu_hours_total"] <= GPU_CAP_H
    return out


def md_table(summary: dict) -> str:
    rows = [
        "| node | device | attempt | sealed | runs exp/written/successful/divergent | started→finished (UTC) | wall | GPU-h / core-h | stop_class | sha256sum -c | SEAL_RECEIPT sha256 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in summary["nodes"]:
        if r.get("state") == "not_run":
            rows.append(f"| {r['node']} | — | — | no | — | — | — | — | NOT RUN | — | — |")
            continue
        runs = r.get("runs") or {}
        hours = r.get("gpu_h") if r.get("device") == "gpu" else r.get("core_h")
        hlabel = "GPU-h" if r.get("device") == "gpu" else f"core-h ({r.get('cores')}c)"
        verify = r.get("harvest", {}).get("SHA_VERIFY_SEALED_RC")
        if verify is None:
            verify = r.get("harvest", {}).get("SHA_VERIFY_RUNS_RC")
        verify_txt = f"rc={verify}" if verify is not None else "—"
        sealed_txt = "yes" if r.get("sealed") else "no (unsealed attempt)"
        receipt_sha = (r.get("sha") or {}).get("SEAL_RECEIPT.json") or "—"
        rows.append(
            f"| {r['node']} | {r.get('device')} | {r.get('attempt')} | {sealed_txt} | "
            f"{runs.get('expected')}/{runs.get('written')}/{runs.get('successful')}/{runs.get('divergent')} | "
            f"{r.get('started_utc')} → {r.get('finished_utc')} | "
            f"{r.get('wall_h')} h | {hours} {hlabel} | {r.get('stop_class')} | {verify_txt} | `{receipt_sha}` |"
        )
    return "\n".join(rows)


if __name__ == "__main__":
    cap = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    s = summarise(cap)
    print(json.dumps(s, indent=1, default=str))
    print("\n" + md_table(s))
