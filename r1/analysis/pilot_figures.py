"""Render provisional C1 noise summaries from committed 22 October pilot data.

The 19 October C3 pilot is a test fixture only and is never an input here.
No experiments are executed; these outputs are not accepted evidence.
"""
from __future__ import annotations

import csv
import fcntl
import hashlib
import json
import platform
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "papers/r1/generated/c1_pilot"
RENDERER_REL = "r1/analysis/pilot_figures.py"
INPUT_REL = ("results/r1/pilot/E1_20261022T214606Z/compare.json",
             "results/r1/pilot/E1_20261022T214606Z/runs.jsonl",
             "results/r1/pilot/E1_20261022T214606Z/edits.json",
             "r1/noise/e1_report.py")
OUTPUT_NAMES = ("noise_floor.csv", "noise_floor.pdf")


def validate_noise_reproduction(recomputed, recorded):
    if set(recomputed) != set(recorded):
        raise ValueError("noise node set differs from recorded pilot")
    for node in recomputed:
        for key in ("sigma_train", "sigma_split", "sigma_joint"):
            if recomputed[node][key] != recorded[node][key]:
                raise ValueError(f"noise summary mismatch: {node} {key}")


def _render():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from r1.noise.e1_report import summarise

    source_bytes = {name: (ROOT / name).read_bytes() for name in INPUT_REL}
    noise = json.loads(source_bytes[INPUT_REL[0]])
    if noise.get("label") != "PILOT" or noise.get("summaries", {}).get("common_30", {}).get("label") != "PILOT":
        raise ValueError("noise summary must be explicitly PILOT")
    with tempfile.TemporaryDirectory(prefix="r1-pilot-noise-") as tmp:
        scratch = Path(tmp)
        (scratch / "runs.jsonl").write_bytes(source_bytes[INPUT_REL[1]])
        (scratch / "edits.json").write_bytes(source_bytes[INPUT_REL[2]])
        nodes = summarise(scratch)["nodes"]
    validate_noise_reproduction(nodes, noise["summaries"]["common_30"]["nodes"])
    rows = [(n, v["sigma_train"], v["sigma_split"], v["sigma_joint"]) for n, v in sorted(nodes.items())]
    with (OUT / "noise_floor.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["provisional_status", "node", "sigma_train", "sigma_split", "sigma_joint"])
        writer.writerows(("PILOT; pending author acceptance", *row) for row in rows)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh([x[0] for x in rows], [x[3] for x in rows])
    ax.set_xlabel("Joint-seed standard deviation of baseline metric")
    ax.set_title("PILOT — pending author acceptance")
    fig.tight_layout()
    fig.savefig(OUT / "noise_floor.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    manifest = {"label": "PILOT — not accepted evidence",
                "renderer": {"python": platform.python_version(), "matplotlib": matplotlib.__version__,
                             "path": RENDERER_REL,
                             "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
                "inputs": {name: hashlib.sha256(data).hexdigest() for name, data in source_bytes.items()},
                "outputs": {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest() for name in OUTPUT_NAMES},
                "limitations": "Noise sigma fields recomputed from captured pilot runs and checked against stored summary; not accepted evidence or a complete manuscript pipeline."}
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / ".render.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        status = OUT / "render_status.json"
        status.write_text(json.dumps({"status": "IN_PROGRESS"}) + "\n")
        try:
            _render()
        except BaseException:
            status.write_text(json.dumps({"status": "FAILED"}) + "\n")
            raise
        status.write_text(json.dumps({"status": "SUCCESS"}) + "\n")


def verify_outputs(directory=OUT, root=ROOT):
    """Check status and hashes, without approving outputs as evidence."""
    with (directory / ".render.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
        status = json.loads((directory / "render_status.json").read_text())
        if status.get("status") != "SUCCESS":
            raise ValueError("pilot render is not successful")
        manifest = json.loads((directory / "provenance.json").read_text())
        renderer = manifest["renderer"]
        if renderer.get("path") != RENDERER_REL or set(manifest["inputs"]) != set(INPUT_REL) or set(manifest["outputs"]) != set(OUTPUT_NAMES):
            raise ValueError("incomplete or unexpected provenance file set")
        if hashlib.sha256((root / RENDERER_REL).read_bytes()).hexdigest() != renderer["sha256"]:
            raise ValueError("renderer differs from recorded hash")
        for name, digest in manifest["inputs"].items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"input differs: {name}")
        for name, digest in manifest["outputs"].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"output differs: {name}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="check status and hashes of C1 outputs")
    if parser.parse_args().verify:
        verify_outputs()
    else:
        main()
