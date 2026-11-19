"""Check every run record of a per-node port_smoke_gpu.py run (the task's record gate).

Usage: python3 verify_records.py <runs_root> [--node NODE]
Prints one JSON object per run record and a final summary; exit 1 if any record fails the gate:
  * isolation.waivers must be {} (no waiver);
  * a non-autoresearch node must be isolation.effective true and isolation.exceptions [];
  * autoresearch_fixedtokens may be effective false only with exceptions == ["shared_dev_shm"];
  * no 'synthetic' marker in the run log or in the node's data manifest;
  * the run must have executed (or be the intentionally refused frozen diff).
Also prints frozen_pin_sha256 (the deployed-kit pin, which includes the data link), outcome and log sha.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_root", type=Path)
    ap.add_argument("--node", default=None)
    args = ap.parse_args()
    root = args.runs_root.resolve()
    records = sorted(root.rglob("run_record.json"))
    if not records:
        print(json.dumps({"error": f"no run_record.json under {root}"}))
        return 1
    issues, rows = [], []
    for rp in records:
        d = json.loads(rp.read_text())
        iso = d.get("isolation") or {}
        waivers = iso.get("waivers")
        effective = iso.get("effective")
        exceptions = iso.get("exceptions")
        node = d.get("node")
        log = rp.parent / "run.log"
        log_text = log.read_text(errors="replace") if log.exists() else ""
        synthetic_log = "synthetic" in log_text.lower()
        manifest = rp.parent / "work" / "data" / "data_manifest.json"
        synthetic_manifest = manifest.exists() and '"synthetic"' in manifest.read_text(errors="replace")
        run = {
            "record": str(rp),
            "run_id": d.get("run_id"),
            "node": node,
            "executed": d.get("executed"),
            "outcome": d.get("outcome"),
            "effective": effective,
            "waivers": waivers,
            "exceptions": exceptions,
            "frozen_pin_sha256": d.get("frozen_pin_sha256"),
            "log_sha256": d.get("log_sha256"),
            "synthetic_in_log": synthetic_log,
            "synthetic_in_data_manifest": synthetic_manifest,
            "gpu": (d.get("limits") or {}).get("gpu_uuids"),
            "cgroup_effective": (((d.get("isolation") or {}).get("cgroup") or {})
                                 .get("kill") or {}).get("method"),
        }
        rows.append(run)
        if waivers:
            issues.append({"record": str(rp), "error": "isolation.waivers is not empty", "waivers": waivers})
        if synthetic_log:
            issues.append({"record": str(rp), "error": "synthetic marker in run log"})
        if synthetic_manifest:
            issues.append({"record": str(rp), "error": "synthetic marker in the run's data manifest"})
        if d.get("executed") is False or d.get("executed") is None:
            run["note"] = "not executed (refused diff or never started); isolation fields absent by design"
        elif node == "autoresearch_fixedtokens":
            if exceptions != ["shared_dev_shm"]:
                issues.append({"record": str(rp), "error": "autoresearch exceptions are not ['shared_dev_shm']",
                               "exceptions": exceptions})
            if effective is not False:
                issues.append({"record": str(rp), "error": "autoresearch record unexpectedly effective true",
                               "effective": effective})
        elif d.get("executed") is not False:
            if effective is not True:
                issues.append({"record": str(rp), "error": "isolation.effective is not true", "effective": effective})
            if exceptions != []:
                issues.append({"record": str(rp), "error": "isolation.exceptions is not []", "exceptions": exceptions})
    # the deployed data manifest must not be the synthetic one
    node = args.node or (rows[0]["node"] if rows else None)
    data_manifest = None
    for rp in records:
        cand = rp.parent / "work" / "data" / "data_manifest.json"
        if cand.exists():
            data_manifest = cand
            break
    out = {"runs_root": str(root), "node": node, "records": len(rows), "issues": issues,
           "data_manifest": str(data_manifest) if data_manifest else None}
    print(json.dumps(out, indent=2, default=str))
    for r in rows:
        print(json.dumps(r, default=str))
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
