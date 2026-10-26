"""Render selected committed pilot summaries; no experiments are executed.

Outputs are provisional and do not constitute the C3 gate or accepted C1 evidence.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOISE = ROOT / "results/r1/pilot/E1_20261022T214606Z/compare.json"
PILOT = ROOT / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
OUT = ROOT / "papers/r1/generated/pilot"


def waste_counts(rows):
    """Count source-table rows by stratum and inert kind; no deduplication."""
    counts = collections.Counter()
    for row in rows:
        key = (row["source"], row["node"], row["memory_mode"], row.get("inert_kind") or "non-inert")
        counts[key] += 1
    totals = collections.Counter()
    for (source, node, memory, _kind), count in counts.items():
        totals[(source, node, memory)] += count
    return sorted((*key, count, totals[key[:3]], count / totals[key[:3]]) for key, count in counts.items())


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    sources = [NOISE, PILOT / "proposals.jsonl", PILOT / "offline_eval.json"]
    noise = json.loads(NOISE.read_text())
    nodes = noise["summaries"]["common_30"]["nodes"]
    noise_rows = [(n, v["sigma_train"], v["sigma_split"], v["sigma_joint"]) for n, v in sorted(nodes.items())]
    write_csv(OUT / "noise_floor.csv", ["node", "sigma_train", "sigma_split", "sigma_joint"], noise_rows)
    with (PILOT / "proposals.jsonl").open() as handle:
        counts = waste_counts(json.loads(line) for line in handle if line.strip())
    write_csv(OUT / "proposal_categories.csv", ["source", "node", "memory_mode", "inert_kind", "rows", "stratum_rows", "share"], counts)
    result = json.loads((PILOT / "offline_eval.json").read_text())
    gates = result["instance"]["per_g"]["0.1"]["gate"]
    gate_rows = [(n, v["gain_A3_minus_A2_per20"], *v["ci95"], v["delta_n"]) for n, v in sorted(gates.items())]
    write_csv(OUT / "offline_pilot.csv", ["node", "gain_A3_minus_A2_per20", "ci_lower", "ci_upper", "delta_n"], gate_rows)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh([x[0] for x in noise_rows], [x[3] for x in noise_rows])
    ax.set_xlabel("Joint-seed standard deviation of baseline metric")
    ax.set_title("PILOT — pending author acceptance")
    fig.tight_layout()
    fig.savefig(OUT / "noise_floor.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    manifest = {"label": "PILOT / ENGINEERING_ONLY — not accepted evidence or gate", "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, "limitations": "Selected existing summaries, not a complete manuscript regeneration pipeline; proposal rows include partial campaigns. Offline estimates are old pilot outputs, not the current gate."}
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
