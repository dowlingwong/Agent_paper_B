"""Build the R1-D28-REPAIR eight-node noise summary from recorded D21 sources.

ENGINEERING_ONLY; AI-assisted (OpenAI Codex). No new measurements.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from r1.noise.e1_report import summarise

ROOT = Path(__file__).resolve().parents[2]
OLD = Path("results/r1/pilot/E1_20261022T214606Z/summary.json")
REPAIR = Path("results/r1/pilot/E1_D28_REPAIR_20261027")
CLIMATE = Path("results/r1/pilot/E1_D28_CLIMATE_20261027")
OUT = Path("results/r1/noise/D28_REPAIR_20261027/summary.json")
UNCHANGED = ("digits_mlp", "tabular_mlp", "openml_ionosphere", "openml_credit_approval")
REPAIRED = ("openml_breast_w", "openml_sonar", "openml_wdbc")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_committed_source(path, revision):
    relative=path.relative_to(ROOT)
    recorded=subprocess.run(["git", "-C", str(ROOT), "show", f"{revision}:{relative}"],
                            check=True, capture_output=True).stdout
    if path.read_bytes()!=recorded:
        raise ValueError(f"source differs from committed {revision}: {relative}")


def check_run(path, expected_nodes):
    manifest = json.loads((path/"manifest.json").read_text())
    rows = [json.loads(line) for line in (path/"runs.jsonl").read_text().splitlines() if line.strip()]
    if manifest["harness"]["commit"] != "6adf3859de66c4814fcf376eed59880fbd8eeaf7" or manifest["harness"]["dirty"]:
        raise ValueError(f"incorrect harness pin in {path}")
    if manifest["seeds_per_condition"] != 30 or set(manifest["nodes"]) != set(expected_nodes):
        raise ValueError(f"unexpected node/seed declaration in {path}")
    keys = [(r["node"], r["config"], r["condition"], r.get("train_seed"), r.get("split_seed")) for r in rows]
    if len(rows) != len(expected_nodes)*6*92 or len(keys) != len(set(keys)):
        raise ValueError(f"incomplete or duplicate rows in {path}")
    if any(not r["success"] or r["metric"] is None or not math.isfinite(r["metric"]) for r in rows):
        raise ValueError(f"failed, missing or non-finite run in {path}")
    if any(r["config"] != "c0" and r["edit_applied"] is not True for r in rows):
        raise ValueError(f"edit not applied in {path}")
    for node in expected_nodes:
        for k in range(6):
            selected = [r for r in rows if r["node"] == node and r["config"] == f"c{k}"]
            defaults = {r["condition"]:r["metric"] for r in selected if r["condition"] in ("default","default_repeat")}
            if set(defaults) != {"default","default_repeat"} or defaults["default"] != defaults["default_repeat"]:
                raise ValueError(f"default determinism failed for {node} c{k}")
            expected = {
                "train": {(i,None) for i in range(1001,1031)},
                "split": {(None,i) for i in range(2001,2031)},
                "joint": {(i,i) for i in range(3001,3031)},
            }
            for condition, seeds in expected.items():
                actual={(r["train_seed"],r["split_seed"]) for r in selected if r["condition"]==condition}
                if actual != seeds:
                    raise ValueError(f"seed coverage mismatch for {node} c{k} {condition}")
    return summarise(path)


def build():
    if sha(ROOT/OLD) != "eabc2f5c05b08cf900ab988838e41dc7f8db35a4131f4b57e72514e0e5513793":
        raise ValueError("22 October common summary hash mismatch")
    for directory, revision in ((REPAIR,"a8edeff"), (CLIMATE,"97dc445")):
        for name in ("runs.jsonl", "edits.json", "manifest.json"):
            verify_committed_source(ROOT/directory/name, revision)
    common = json.loads((ROOT/OLD).read_text())
    repair = check_run(ROOT/REPAIR, (*REPAIRED, "openml_blood_transfusion"))
    climate = check_run(ROOT/CLIMATE, ("openml_climate",))
    nodes = {n:common["nodes"][n] for n in UNCHANGED}
    nodes.update({n:repair["nodes"][n] for n in REPAIRED})
    nodes["openml_climate"] = climate["nodes"]["openml_climate"]
    sources = {
        "common_summary": {"path": str(OLD), "sha256": sha(ROOT/OLD), "nodes": list(UNCHANGED)},
        "repair": {"path": str(REPAIR), "runs_sha256": sha(ROOT/REPAIR/"runs.jsonl"),
                   "edits_sha256": sha(ROOT/REPAIR/"edits.json"), "manifest_sha256": sha(ROOT/REPAIR/"manifest.json"),
                   "nodes": list(REPAIRED)},
        "climate": {"path": str(CLIMATE), "runs_sha256": sha(ROOT/CLIMATE/"runs.jsonl"),
                    "edits_sha256": sha(ROOT/CLIMATE/"edits.json"), "manifest_sha256": sha(ROOT/CLIMATE/"manifest.json"),
                    "nodes": ["openml_climate"]},
    }
    return {"schema": "r1.d28_noise_summary/1", "label": "PILOT",
            "description": "Eight-node D21 composite under R1-D28-REPAIR; no new measurements.",
            "sources": sources, "nodes": nodes}


def main():
    out=ROOT/OUT
    data=json.dumps(build(),indent=2,sort_keys=True)+"\n"
    if out.exists() and out.read_text()!=data:
        raise SystemExit("STOP: composite exists with different bytes; preserve it")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(data)
    print(f"{out} sha256={sha(out)}")


if __name__=="__main__":
    main()
