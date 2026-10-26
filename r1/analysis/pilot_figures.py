"""Render selected committed pilot summaries; no experiments are executed.

Outputs are provisional and do not constitute the C3 gate or accepted C1 evidence.
"""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOISE = ROOT / "results/r1/pilot/E1_20261022T214606Z/compare.json"
PILOT = ROOT / "results/r1/engineering/c3_audit_pilot_20261019T001338Z"
OUT = ROOT / "papers/r1/generated/pilot"


def waste_counts(rows):
    """Count source-table rows by stratum and inert kind; no deduplication."""
    counts = collections.Counter()
    for row in rows:
        if "inert" not in row or not isinstance(row["inert"], bool) or "inert_kind" not in row:
            raise ValueError("missing or invalid inert fields")
        kind = row["inert_kind"]
        if (row["inert"] and (not isinstance(kind, str) or not kind.strip() or kind == "non-inert")) or (not row["inert"] and kind is not None):
            raise ValueError("inconsistent inert label and kind")
        key = (row["source"], row["node"], row["memory_mode"], kind if kind is not None else "non-inert")
        counts[key] += 1
    totals = collections.Counter()
    for (source, node, memory, _kind), count in counts.items():
        totals[(source, node, memory)] += count
    return sorted((*key, count, totals[key[:3]], count / totals[key[:3]]) for key, count in counts.items())


def write_csv(path, header, rows, label):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["provisional_status", *header])
        writer.writerows((label, *row) for row in rows)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    OUT.mkdir(parents=True, exist_ok=True)
    sources = [NOISE, PILOT / "proposals.jsonl", PILOT / "offline_eval.json"]
    noise = json.loads(NOISE.read_text())
    nodes = noise["summaries"]["common_30"]["nodes"]
    noise_rows = [(n, v["sigma_train"], v["sigma_split"], v["sigma_joint"]) for n, v in sorted(nodes.items())]
    write_csv(OUT / "noise_floor.csv", ["node", "sigma_train", "sigma_split", "sigma_joint"], noise_rows, "PILOT; pending author acceptance")
    with (PILOT / "proposals.jsonl").open() as handle:
        counts = waste_counts(json.loads(line) for line in handle if line.strip())
    write_csv(OUT / "proposal_categories.csv", ["source", "node", "memory_mode", "inert_kind", "rows", "stratum_rows", "share"], counts, "ENGINEERING_ONLY; partial campaigns; source-row shares")
    result = json.loads((PILOT / "offline_eval.json").read_text())
    gates = result["instance"]["per_g"]["0.1"]["gate"]
    gate_rows = [(n, v["gain_A3_minus_A2_per20"], *v["ci95"], v["delta_n"]) for n, v in sorted(gates.items())]
    write_csv(OUT / "offline_pilot.csv", ["node", "gain_A3_minus_A2_per20", "ci_lower", "ci_upper", "delta_n"], gate_rows, "ENGINEERING_ONLY; historical pilot; not current C3 gate")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh([x[0] for x in noise_rows], [x[3] for x in noise_rows])
    ax.set_xlabel("Joint-seed standard deviation of baseline metric")
    ax.set_title("PILOT — pending author acceptance")
    fig.tight_layout()
    fig.savefig(OUT / "noise_floor.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4))
    labels = [row[0] for row in gate_rows]
    gains = [row[1] for row in gate_rows]
    lower = [row[1] - row[2] for row in gate_rows]
    upper = [row[3] - row[1] for row in gate_rows]
    ax.errorbar(gains, labels, xerr=[lower, upper], fmt="o", capsize=3)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Historical A3 minus A2 per-campaign estimate")
    ax.set_title("ENGINEERING PILOT — not the C3 gate")
    fig.tight_layout()
    fig.savefig(OUT / "offline_pilot.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)
    total = sum(row[4] for row in counts)
    duplicate = sum(row[4] for row in counts if row[3] == "duplicate")
    (OUT / "pilot_numbers.tex").write_text(
        "% ENGINEERING_ONLY pilot; includes partial campaigns; not accepted evidence.\n"
        + "\\newcommand{\\PilotProposalRows}{" + str(total) + "}\n"
        + "\\newcommand{\\PilotDuplicateRows}{" + str(duplicate) + "}\n"
    )
    manifest = {"label": "PILOT / ENGINEERING_ONLY — not accepted evidence or gate", "renderer": {"python": platform.python_version(), "matplotlib": matplotlib.__version__}, "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, "limitations": "Selected existing summaries, not a complete manuscript regeneration pipeline; proposal rows include partial campaigns. Offline estimates are old pilot outputs, not the current gate."}
    (OUT / "provenance.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
