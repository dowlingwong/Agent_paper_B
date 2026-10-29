#!/usr/bin/env python3
"""S1.1 interaction check: a 2 x 2 factorial at 30 seeds under the "vary" split (runbook rev. 3 §4; rev.-5).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY; reported with the result, not a gate. CPU only,
no LLM. Runs on any CPU host (digits on TASL-2, tabular on TASL-7, breast_w anywhere).

For a factor pair (A, B) with levels (a0, a1), (b0, b1) set on the node's start configuration, the
four cells are run at each seed s of the S1.1 seed block with train seed = split seed = s ("vary";
the same mechanism as the C3 audits, ``r1.c3.audit.run_config``). Per seed the interaction contrast
is I_s = y11 - y10 - y01 + y00; reported are its mean, sd, a t-interval and a seeded percentile
bootstrap interval (95 %), and the two main effects.

Default pairs (rev.-5 amendment 6; ``--pair A:B`` overrides, repeatable): HIDDEN_UNITS x BATCH_SIZE,
HIDDEN_UNITS x LEARNING_RATE_INIT and BATCH_SIZE x LEARNING_RATE_INIT on the MLP nodes; max_iter x C
on openml_breast_w. Default levels: the start value and twice it (integers rounded); ``--levels
KEY=lo,hi`` overrides.

  python -m r1.tracks.probes.s1_factorial --node digits_mlp --out s11_digits.json
"""
from __future__ import annotations

import argparse
import json
import math
import re
import tempfile
from pathlib import Path

import numpy as np
from scipy import stats

SCHEMA = "tracks_s11_factorial/v1"
S11_SEEDS = tuple(range(37001, 37031))   # Track S S1.1 seed block (30 seeds)
BOOT = 2000
BOOT_SEED = 20261029
MLP_PAIRS = [("HIDDEN_UNITS", "BATCH_SIZE"), ("HIDDEN_UNITS", "LEARNING_RATE_INIT"), ("BATCH_SIZE", "LEARNING_RATE_INIT")]
DEFAULT_PAIRS = {"digits_mlp": MLP_PAIRS, "tabular_mlp": MLP_PAIRS, "openml_breast_w": [("max_iter", "C")]}
CELLS = ("00", "10", "01", "11")


def _pattern(path: str, key: str) -> re.Pattern:
    if path.endswith((".yaml", ".yml")):
        return re.compile(r"^(" + re.escape(key) + r"\s*:\s*)(.*?)(\s*)$", re.MULTILINE)
    return re.compile(r"^(" + re.escape(key) + r"\s*=\s*)(.+?)(\s*)$", re.MULTILINE)


def current_value(files: dict[str, str], key: str) -> tuple[str, str]:
    """(path, literal value) of ``key`` in the editable files."""
    for path, text in files.items():
        m = _pattern(path, key).search(text)
        if m:
            return path, m.group(2)
    raise KeyError(f"{key} not found in the editable files")


def default_levels(literal: str, factor: float = 2.0) -> tuple[str, str]:
    """(start, start x factor); integers stay integers."""
    if re.fullmatch(r"[-+]?\d+", literal.strip()):
        return literal, str(int(round(int(literal) * factor)))
    return literal, repr(float(literal) * factor)


def parse_levels(items: list[str] | None) -> dict[str, tuple[str, str]]:
    out = {}
    for item in items or []:
        key, vals = item.split("=", 1)
        lo, hi = vals.split(",", 1)
        out[key] = (lo, hi)
    return out


def design(start_files: dict[str, str], a: str, b: str, levels: dict | None = None) -> dict[str, dict[str, str]]:
    """The four cells' editable files ("00", "10", "01", "11": first digit A high, second B high)."""
    from r1.c3.features import apply_edit
    levels = dict(levels or {})
    out = {}
    for cell in CELLS:
        files = dict(start_files)
        for key, hi in ((a, cell[0] == "1"), (b, cell[1] == "1")):
            path, lit = current_value(files, key)
            lo_v, hi_v = levels.get(key) or default_levels(lit)
            target = hi_v if hi else lo_v
            if target != lit:
                files = apply_edit(files, {"path": path, "symbol": key, "old": lit, "new": target})
        out[cell] = files
    return out


def interaction(y: dict[str, list]) -> dict:
    """Interaction contrast and main effects from per-seed metrics of the four cells (seeds aligned)."""
    rows = [(y["00"][i], y["10"][i], y["01"][i], y["11"][i]) for i in range(len(y["00"]))]
    rows = [r for r in rows if all(v is not None for v in r)]
    if len(rows) < 2:
        return {"n": len(rows), "interaction": None}
    arr = np.asarray(rows, float)
    contrast = arr[:, 3] - arr[:, 1] - arr[:, 2] + arr[:, 0]
    n = len(contrast)
    mean, sd = float(contrast.mean()), float(contrast.std(ddof=1))
    half = float(stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n))
    rng = np.random.default_rng(BOOT_SEED)
    boot = contrast[rng.integers(0, n, size=(BOOT, n))].mean(axis=1)
    return {"n": n, "interaction": mean, "sd": sd, "se": sd / math.sqrt(n),
            "ci95_t": [mean - half, mean + half], "ci95_boot": [float(np.quantile(boot, 0.025)),
                                                               float(np.quantile(boot, 0.975))],
            "main_A": float(((arr[:, 1] + arr[:, 3]) - (arr[:, 0] + arr[:, 2])).mean() / 2),
            "main_B": float(((arr[:, 2] + arr[:, 3]) - (arr[:, 0] + arr[:, 1])).mean() / 2)}


def run_pair(node: str, a: str, b: str, seeds, levels: dict | None, tmp: str) -> dict:
    from r1.c3.audit import run_config
    from r1.harness import import_harness
    harness = import_harness()
    from autoresearch.nodes.registry import load_registered_node
    spec = load_registered_node(node, repo_root=harness)
    start = {p: (harness / "nodes" / node / p).read_text() for p in spec.editable_paths}
    cells = design(start, a, b, levels)
    y = {cell: [r["metric"] for r in run_config(node, files, list(seeds), tmp)] for cell, files in cells.items()}
    return {"pair": [a, b], "levels": {k: list(current_value(cells[c], k)[1] for c in ("00", "11")) for k in (a, b)},
            "metrics": y, **interaction(y)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    ap.add_argument("--pair", action="append", default=None, help="A:B (repeatable; default: the node's pairs)")
    ap.add_argument("--levels", action="append", default=None, help="KEY=lo,hi (repeatable)")
    ap.add_argument("--seeds", type=int, default=len(S11_SEEDS))
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    pairs = [tuple(p.split(":", 1)) for p in args.pair] if args.pair else DEFAULT_PAIRS.get(args.node)
    if not pairs:
        ap.error(f"no default pairs for {args.node}; pass --pair A:B")
    seeds = S11_SEEDS[: args.seeds]
    with tempfile.TemporaryDirectory() as tmp:
        results = [run_pair(args.node, a, b, seeds, parse_levels(args.levels), tmp) for a, b in pairs]
    report = {"schema": SCHEMA, "label": "ENGINEERING_ONLY", "node": args.node, "split": "vary",
              "seeds": list(seeds), "results": results}
    Path(args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps([{k: r[k] for k in ("pair", "n", "interaction", "ci95_t")} for r in results]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
