"""Compact per-node smoke summary for the report: every run record's gate fields + hashes.

Usage: python3 collect_smoke_summary.py <runs_root> [<runs_root> ...]
Prints/collects JSON {runs_root: {node, records: [{run_id, outcome, executed, effective, waivers,
exceptions, frozen_pin_sha256, record_sha256, log_sha256, gpu, synthetic}], gate_ok, issues}}.
"""
import hashlib
import json
import sys
from pathlib import Path


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    out = {}
    bad = 0
    for root_s in sys.argv[1:]:
        root = Path(root_s)
        rows, issues = [], []
        records = sorted(root.rglob("run_record.json"))
        node = None
        for rp in records:
            d = json.loads(rp.read_text())
            node = d.get("node", node)
            iso = d.get("isolation") or {}
            log = rp.parent / "run.log"
            manifest = rp.parent / "work" / "data" / "data_manifest.json"
            row = {
                "run_id": d.get("run_id"),
                "executed": d.get("executed"),
                "outcome": d.get("outcome"),
                "effective": iso.get("effective"),
                "waivers": iso.get("waivers"),
                "exceptions": iso.get("exceptions"),
                "frozen_pin_sha256": d.get("frozen_pin_sha256"),
                "record_sha256": sha(rp),
                "log_sha256": sha(log) if log.exists() else None,
                "gpu_uuids": (d.get("limits") or {}).get("gpu_uuids"),
                "cgroup_kill_method": (((iso.get("cgroup") or {}).get("kill") or {}).get("method")),
                "synthetic_in_log": log.exists() and "synthetic" in log.read_text(errors="replace").lower(),
                "synthetic_in_data_manifest": manifest.exists() and '"synthetic"' in manifest.read_text(errors="replace"),
            }
            rows.append(row)
            if row["waivers"]:
                issues.append(f"{row['run_id']}: waivers {row['waivers']}")
            if row["synthetic_in_log"] or row["synthetic_in_data_manifest"]:
                issues.append(f"{row['run_id']}: synthetic marker")
            if row["executed"] is not False and row["executed"] is not None:
                if node == "autoresearch_fixedtokens":
                    if row["exceptions"] != ["shared_dev_shm"]:
                        issues.append(f"{row['run_id']}: ar exceptions {row['exceptions']}")
                else:
                    if row["effective"] is not True:
                        issues.append(f"{row['run_id']}: effective {row['effective']}")
                    if row["exceptions"] != []:
                        issues.append(f"{row['run_id']}: exceptions {row['exceptions']}")
        out[str(root)] = {"node": node, "records": rows, "issues": issues,
                          "gate_ok": not issues}
        bad += bool(issues)
    print(json.dumps(out, indent=1, sort_keys=True))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
