#!/usr/bin/env python3
"""Cross-arm comparison for the E1b rerun-2 (R1-E1B-RERUN2; PILOT).

Inputs are two or three committed E1b run directories:

- A: LLM, ``append_only_summary`` (primary);
- B: LLM, ``none`` (contrast; T2 Proposition 5 predicts memory raises g and
  lowers the value of verify);
- C: scripted stand-in (reference).

Output is a Markdown report and a JSON document with, per node and for ALL:

- per arm: rho, ``always_verify - rho``, ``kg_index - rho`` and
  ``margin_threshold - rho`` with instance-cluster bootstrap CIs, the best
  simple baseline, naive and leaf-split headroom with CIs, the share of points
  where verify changes the leaf, and the mean verify - continue;
- the memory effect ``(always_verify - rho)_B - (always_verify - rho)_A`` as a
  paired instance-cluster bootstrap with shared draws over the same instances;
- the C1 waste counters (active-key novelty fraction, inactive-key rejections,
  ``config_seen_before`` rate, LLM calls and parse failures) per arm.

The report is PILOT and carries no interpretation beyond a fixed readings
template: supported if the adjusted lower bound is above 0, inconclusive when
the interval spans 0, opposite when the adjusted upper bound is below 0, with
Bonferroni over the per-node primary contrasts (the memory effect) and the
count stated.

AI-assisted (BUILD_BATCH4, P7); ENGINEERING_ONLY/PILOT.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.baselines.evaluate import evaluate_arms
from r1.branch.schema import record_from_dict
from r1.branch.table import SiblingTable, build_table
from r1.liveness.novelty import load_segments, tally_segments

SEED = 20261012  # same default as r1.baselines.evaluate
N_BOOT = 2000
CONTRASTS = ("always_verify - rho", "kg_index - rho", "margin_threshold - rho")
PRIMARY = ("always_verify", "rho")
ALPHA = 0.05


@dataclass
class Arm:
    label: str
    path: Path
    manifest: dict = field(default_factory=dict)
    records: list = field(default_factory=list)
    table: SiblingTable | None = None

    @property
    def memory_mode(self) -> str:
        return str(self.manifest.get("memory_mode", "none"))

    @property
    def arm_role(self) -> str:
        return str(self.manifest.get("arm_role", ""))


def load_arm(label: str, path: str | Path) -> Arm:
    """Load a committed run directory (``records.jsonl`` is the analysis input)."""
    run = Path(path)
    records_path = run / "records.jsonl"
    if not records_path.exists():
        raise FileNotFoundError(
            f"run {run} has no records.jsonl; run r1.headroom.e1b_analyze on it first"
        )
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    records = [
        record_from_dict(json.loads(line))
        for line in records_path.read_text().splitlines()
        if line.strip()
    ]
    if not records:
        raise ValueError(f"run {run} has an empty records.jsonl")
    return Arm(label=label, path=run, manifest=manifest, records=records)


def _value(matrix: np.ndarray, cols: np.ndarray, rows: np.ndarray) -> float:
    vals = matrix[rows, cols[rows]]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if vals.size else float("nan")


def _contrast(table: SiblingTable, choices: dict, rows: np.ndarray,
              pair: tuple[str, str] = PRIMARY) -> float:
    a, b = pair
    return _value(table.value, choices[a], rows) - _value(table.value, choices[b], rows)


def paired_memory_effect(
    table_a: SiblingTable, choices_a: dict,
    table_b: SiblingTable, choices_b: dict,
    *, n_boot: int = N_BOOT, seed: int = SEED,
) -> dict:
    """(always_verify - rho)_B - (always_verify - rho)_A with shared instance draws.

    The two arms must cover the same instances; only shared instances are drawn
    (recorded in the result).  Draws are shared across arms: one instance
    resample is used for both, so the delta is paired.
    """
    instances_a = sorted(set(table_a.instances.tolist()))
    instances_b = sorted(set(table_b.instances.tolist()))
    shared = sorted(set(instances_a) & set(instances_b))
    if len(shared) < 2:
        raise ValueError("the paired memory effect needs at least two shared instances")
    index_a = {inst: np.flatnonzero(table_a.instances == inst) for inst in shared}
    index_b = {inst: np.flatnonzero(table_b.instances == inst) for inst in shared}
    rows_all_a = np.arange(len(table_a))
    rows_all_b = np.arange(len(table_b))
    point_a = _contrast(table_a, choices_a, rows_all_a)
    point_b = _contrast(table_b, choices_b, rows_all_b)
    rng = np.random.default_rng(seed)
    deltas: list[float] = []
    degenerate = 0
    for _ in range(n_boot):
        picked = rng.choice(len(shared), size=len(shared), replace=True)
        rows_a = np.concatenate([index_a[shared[k]] for k in picked])
        rows_b = np.concatenate([index_b[shared[k]] for k in picked])
        value_a = _contrast(table_a, choices_a, rows_a)
        value_b = _contrast(table_b, choices_b, rows_b)
        if math.isnan(value_a) or math.isnan(value_b):
            degenerate += 1
            continue
        deltas.append(value_b - value_a)
    lo, hi = np.percentile(deltas, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)]) if deltas else (math.nan, math.nan)
    return {
        "point_estimate": point_b - point_a,
        "ci": [float(lo), float(hi)],
        "level": 1 - ALPHA,
        "n_boot": n_boot,
        "n_degenerate_draws": degenerate,
        "n_instances": len(shared),
        "instances_matched": instances_a == instances_b,
    }


def _adjusted_ci(deltas: list[float], level: float) -> tuple[float, float] | None:
    if not deltas:
        return None
    lo, hi = np.percentile(deltas, [100 * (1 - level) / 2, 100 * (1 - (1 - level) / 2)])
    return float(lo), float(hi)


def _reading(lower: float, upper: float) -> str:
    """The fixed readings template; no interpretation beyond it."""
    if lower > 0:
        return "supported"
    if upper < 0:
        return "opposite"
    return "inconclusive"


def _pair_deltas(
    table_a: SiblingTable, choices_a: dict, table_b: SiblingTable, choices_b: dict,
    *, n_boot: int, seed: int,
) -> list[float]:
    """Raw shared-draw deltas, reused for the Bonferroni-adjusted interval."""
    instances = sorted(set(table_a.instances.tolist()) & set(table_b.instances.tolist()))
    index_a = {inst: np.flatnonzero(table_a.instances == inst) for inst in instances}
    index_b = {inst: np.flatnonzero(table_b.instances == inst) for inst in instances}
    rng = np.random.default_rng(seed)
    deltas = []
    for _ in range(n_boot):
        picked = rng.choice(len(instances), size=len(instances), replace=True)
        rows_a = np.concatenate([index_a[instances[k]] for k in picked])
        rows_b = np.concatenate([index_b[instances[k]] for k in picked])
        value_a = _contrast(table_a, choices_a, rows_a)
        value_b = _contrast(table_b, choices_b, rows_b)
        if math.isnan(value_a) or math.isnan(value_b):
            continue
        deltas.append(value_b - value_a)
    return deltas


def waste_for(run: Path) -> dict:
    """C1 waste counters over the root campaign ledgers (events or replay)."""
    ledgers = run / "provenance/ledgers/roots"
    target = ledgers if ledgers.exists() else None
    result: dict = {"llm_calls": 0, "parse_failures": 0, "novelty": {}, "available": target is not None}
    if target is not None:
        tallies = tally_segments(load_segments([target]))
        for node, tally in sorted(tallies.items()):
            result["novelty"][node] = {
                "source": tally.source,
                "evaluated": tally.evaluated,
                "novel": tally.novel,
                "active_novelty_fraction": tally.fraction,
                "config_seen_before": tally.seen_before,
                "config_seen_before_rate": (
                    tally.seen_before / tally.evaluated if tally.evaluated else 0.0
                ),
                "inactive_key_rejections": tally.inactive_key_rejections,
            }
    for path in sorted(run.rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get("event_type") == "llm_call":
                result["llm_calls"] += 1
                if item.get("payload", {}).get("parse_ok") is False:
                    result["parse_failures"] += 1
    return result


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "–"
    return f"{value:+.{digits}f}"


def _ci(interval) -> str:
    if interval is None or any(v is None or (isinstance(v, float) and math.isnan(v)) for v in interval):
        return "[–, –]"
    return f"[{_fmt(interval[0])}, {_fmt(interval[1])}]"


def markdown(result: dict) -> str:
    lines = [
        f"# E1b rerun-2 cross-arm comparison — {result['generated_utc']}",
        "",
        "**PILOT.** AI-assisted (BUILD_BATCH4, P7). ENGINEERING_ONLY/PILOT; no interpretation "
        "beyond the readings template at the end.",
        "",
        "## Arms",
        "",
        "| arm | directory | manager | memory mode | role |",
        "|---|---|---|---|---|",
    ]
    for label, arm in result["arms"].items():
        lines.append(
            f"| {label} | `{arm['dir']}` | {arm.get('manager', {}).get('kind', '–')} | "
            f"{arm['memory_mode']} | {arm['arm_role'] or '–'} |"
        )
    lines += ["", f"Nodes: {', '.join(result['nodes'])}.", ""]
    for node in result["nodes"] + ["ALL"]:
        lines += [f"## {node}", ""]
        present = [label for label in result["arms"] if result["per_node"][node]["arms"].get(label)]
        if not present:
            lines += ["No arm covers this node.", ""]
            continue
        lines += ["| metric | " + " | ".join(f"arm {label}" for label in present) + " |",
                  "|---" * (len(present) + 1) + "|"]
        metric_rows = [
            ("rho", lambda s: _fmt(s["rho"])),
            ("always_verify − ρ", lambda s: f"{_fmt(s['contrasts']['always_verify - rho']['point'])} {_ci(s['contrasts']['always_verify - rho']['ci'])}"),
            ("kg_index − ρ", lambda s: f"{_fmt(s['contrasts']['kg_index - rho']['point'])} {_ci(s['contrasts']['kg_index - rho']['ci'])}"),
            ("margin_threshold − ρ", lambda s: f"{_fmt(s['contrasts']['margin_threshold - rho']['point'])} {_ci(s['contrasts']['margin_threshold - rho']['ci'])}"),
            ("best simple baseline", lambda s: str(s["best_simple"])),
            ("naive headroom", lambda s: f"{_fmt(s['headroom_naive'])} {_ci(s['headroom_naive_ci'])}"),
            ("leaf-split headroom", lambda s: f"{_fmt(s['headroom_leafsplit'])} {_ci(s['headroom_leafsplit_ci'])}"),
            ("share verify changes leaf", lambda s: "–" if s["verify_changes_leaf_share"] is None else f"{s['verify_changes_leaf_share']:.2f}"),
            ("mean verify − continue", lambda s: _fmt(s["mean_verify_minus_continue"])),
            ("points / instances", lambda s: f"{s['n_points']} / {s['n_instances']}"),
        ]
        for name, getter in metric_rows:
            cells = []
            for label in present:
                section = result["per_node"][node]["arms"][label]
                cells.append(getter(section) if section else "–")
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        effect = result["per_node"][node]["memory_effect"]
        if effect:
            lines += ["", f"Memory effect (B − A) on always_verify − ρ: "
                          f"**{_fmt(effect['point_estimate'])}** {_ci(effect['ci'])} "
                          f"({effect['n_instances']} shared instances, {effect['n_boot']} shared draws)."]
        lines.append("")
    lines += ["## Waste (C1)", "",
              "| arm | availability | active-novelty | inactive-key rejections | config_seen_before | LLM calls | parse failures |",
              "|---|---|---|---|---|---|---|"]
    for label, waste in result["waste"].items():
        evaluated = sum(v["evaluated"] for v in waste["novelty"].values())
        novel = sum(v["novel"] for v in waste["novelty"].values())
        seen = sum(v["config_seen_before"] for v in waste["novelty"].values())
        rejections = sum(v["inactive_key_rejections"] for v in waste["novelty"].values())
        fraction = f"{novel / evaluated:.4f} ({novel}/{evaluated})" if evaluated else "–"
        seen_rate = f"{seen / evaluated:.4f} ({seen}/{evaluated})" if evaluated else "–"
        lines.append(
            f"| {label} | {'yes' if waste['available'] else 'no (fixture)'} | {fraction} | {rejections} | "
            f"{seen_rate} | {waste['llm_calls']} | {waste['parse_failures']} |"
        )
    readings = result["readings"]
    if readings.get("note"):
        lines += ["", "## Readings (template only)", "", readings["note"], ""]
        return "\n".join(lines).rstrip("\n")
    lines += ["", "## Readings (template only)", "",
              f"Primary contrast: `{readings['primary_contrast']}`. Bonferroni over "
              f"m = {readings['bonferroni_m']} per-node contrasts, α = {readings['alpha']}, "
              f"adjusted interval level {readings['adjusted_level']:.4f}.",
              "",
              "| node | point | adjusted CI | reading |",
              "|---|---|---|---|"]
    for node, entry in readings["per_node"].items():
        lines.append(
            f"| {node} | {_fmt(entry['point_estimate'])} | {_ci(entry['adjusted_ci'])} | "
            f"{entry['reading']} |"
        )
    lines += ["", "Readings: supported if the adjusted lower bound is > 0; inconclusive if the "
                  "interval spans 0; opposite if the adjusted upper bound is < 0.", ""]
    return "\n".join(lines).rstrip("\n")


def compare(runs: list[tuple[str, Path]], *, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Compare two or three committed runs; returns the JSON-able report."""
    arms = {label: load_arm(label, path) for label, path in runs}
    nodes = sorted({r.node for arm in arms.values() for r in arm.records})
    result = {
        "schema": "r1.e1b_compare/1",
        "label": "PILOT",
        "generated_utc": _utc(),
        "arms": {
            label: {
                "dir": str(arm.path),
                "memory_mode": arm.memory_mode,
                "arm_role": arm.arm_role,
                "manager": arm.manifest.get("manager", {}),
                "instances": sorted({r.instance_id for r in arm.records}),
            }
            for label, arm in arms.items()
        },
        "nodes": nodes,
        "per_node": {},
        "waste": {label: waste_for(arm.path) for label, arm in arms.items()},
        "readings": {"alpha": ALPHA, "primary_contrast":
                     "memory effect (always_verify − ρ)_B − (always_verify − ρ)_A, per node",
                     "per_node": {}},
    }
    if "A" not in arms or "B" not in arms:
        result["readings"]["note"] = (
            "A (or B) not provided; the paired memory effect and therefore the readings "
            "are not computed."
        )
    # Per-node sections and the paired memory effect.
    for node in nodes + ["ALL"]:
        entry = {"arms": {}, "memory_effect": None}
        for label, arm in arms.items():
            subset = [r for r in arm.records if node == "ALL" or r.node == node]
            if not subset:
                continue
            table = build_table(subset)
            report = evaluate_arms(table, n_boot=n_boot, seed=seed)
            verify, cont = table.col("verify"), table.col("continue")
            both = ~np.isnan(table.value[:, verify]) & ~np.isnan(table.value[:, cont])
            advantage = table.value[both, verify] - table.value[both, cont]
            entry["arms"][label] = {
                "n_points": len(table),
                "n_instances": report.boot.n_instances,
                "rho": report.boot.estimates.get("rho"),
                "estimates": report.boot.estimates,
                "contrasts": {
                    name: {"point": report.boot.contrasts.get(name),
                           "ci": list(report.boot.contrast_ci.get(name, (math.nan, math.nan)))}
                    for name in CONTRASTS
                },
                "best_simple": report.best_simple,
                "headroom_naive": report.headroom_naive,
                "headroom_naive_ci": list(report.boot.contrast_ci.get(
                    f"oracle_naive - {report.best_simple}", (math.nan, math.nan))),
                "headroom_leafsplit": report.headroom_leafsplit,
                "headroom_leafsplit_ci": list(report.boot.contrast_ci.get(
                    f"oracle_leafsplit - {report.best_simple}", (math.nan, math.nan))),
                "verify_changes_leaf_share": (
                    float(np.mean(advantage != 0)) if advantage.size else None
                ),
                "mean_verify_minus_continue": float(advantage.mean()) if advantage.size else None,
                "verify_rate": report.verify_rate,
                "choices": {name: [int(c) for c in cols] for name, cols in report.choices.items()},
            }
        if "A" in entry["arms"] and "B" in entry["arms"]:
            effect = paired_memory_effect(
                build_table([r for r in arms["A"].records if node == "ALL" or r.node == node]),
                {name: np.array(cols) for name, cols in entry["arms"]["A"]["choices"].items()},
                build_table([r for r in arms["B"].records if node == "ALL" or r.node == node]),
                {name: np.array(cols) for name, cols in entry["arms"]["B"]["choices"].items()},
                n_boot=n_boot, seed=seed,
            )
            entry["memory_effect"] = effect
        result["per_node"][node] = entry
    # Readings: Bonferroni over the per-node memory effects (ALL excluded).
    per_node_effects = [
        node for node in nodes if result["per_node"][node]["memory_effect"] is not None
    ]
    m = max(len(per_node_effects), 1)
    adjusted_level = 1 - ALPHA / m
    result["readings"]["bonferroni_m"] = len(per_node_effects)
    result["readings"]["adjusted_level"] = adjusted_level
    if "A" in arms and "B" in arms:
        for node in per_node_effects:
            table_a = build_table([r for r in arms["A"].records if r.node == node])
            table_b = build_table([r for r in arms["B"].records if r.node == node])
            choices_a = {name: np.array(cols) for name, cols in
                         result["per_node"][node]["arms"]["A"]["choices"].items()}
            choices_b = {name: np.array(cols) for name, cols in
                         result["per_node"][node]["arms"]["B"]["choices"].items()}
            deltas = _pair_deltas(table_a, choices_a, table_b, choices_b, n_boot=n_boot, seed=seed)
            adjusted = _adjusted_ci(deltas, adjusted_level)
            ci = adjusted or (math.nan, math.nan)
            result["readings"]["per_node"][node] = {
                "point_estimate": result["per_node"][node]["memory_effect"]["point_estimate"],
                "ci": result["per_node"][node]["memory_effect"]["ci"],
                "adjusted_ci": [float(ci[0]), float(ci[1])],
                "reading": _reading(ci[0], ci[1]) if adjusted else "inconclusive",
            }
    # JSON-safe: choices arrays are long; drop them from the output copy.
    for entry in result["per_node"].values():
        for section in entry["arms"].values():
            section.pop("choices", None)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="three run dirs (A B C) or two (B C)")
    parser.add_argument("--md", default=None, help="Markdown report path")
    parser.add_argument("--json", default=None, help="JSON output path")
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    labels = ["A", "B", "C"] if len(args.runs) == 3 else ["B", "C"]
    if len(args.runs) not in (2, 3):
        parser.error("give three run dirs (A B C) or two (B C)")
    result = compare(list(zip(labels, args.runs)), n_boot=args.n_boot, seed=args.seed)
    text = markdown(result)
    if args.md:
        Path(args.md).write_text(text + "\n", encoding="utf-8")
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
