#!/usr/bin/env python3
"""Diagnose the degenerate ionosphere result of the DT4 LLM rerun (14 Oct 2026).

ENGINEERING_ONLY. Read-only. No LLM calls, no GPU, no worker runs.

It reads only committed artifacts:

  * ``results/r1/pilot/E1b_20261013T151857Z`` (PILOT, pinned qwen2.5-coder:7b,
    harness 9c4902d): ``provenance/ledgers/{roots,branches}/**/*.jsonl`` and
    ``points.json``.
  * ``results/r1/pilot/E1b_20261012T161034Z`` (PILOT, scripted stand-in):
    ``roots/``, ``points.json`` and ``records.jsonl``.

It prints three tables:

  Q1  what the LLM proposed on the six ionosphere roots and their branches,
      with per-key counts and repetition statistics;
  Q4  whether the two repetitions of a branch agree, and the same Q1 statistics
      for ``digits_mlp``;
  Q5  the scripted proposer's edited keys and keep rate on the same six
      ionosphere roots, reconstructed from the deterministic proposal law in
      ``r1/headroom/scripted_manager.py`` and validated against the committed
      E2 snapshot hashes.

The Q5 reconstruction replays the scripted proposer (pure arithmetic on the
node config; no worker and no LLM) and searches the keep/discard decisions so
that the incumbent hash equals the committed ``snapshot_hash`` at each E2 point.
The proposal law is reproduced from ``r1/headroom/scripted_manager.py``; the
bounded schema constants are from ``configs/nodes/openml_ionosphere.yaml``
(identical at harness c686517 and 9c4902d).

Run with a Python that has numpy (e.g. the harness venv):

    AR_HARNESS_ROOT=~/Documents/autoresearch_harness \\
        python3 r1/diagnostics/ionosphere_llm_diag.py
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]
LLM_RUN = REPO / "results" / "r1" / "pilot" / "E1b_20261013T151857Z"
SCRIPTED_RUN = REPO / "results" / "r1" / "pilot" / "E1b_20261012T161034Z"
METRIC = "val_auc"
NODE_METRIC = {"openml_ionosphere": "val_auc", "digits_mlp": "val_score"}


def node_metric(inst: str) -> str:
    return NODE_METRIC.get(inst.split("__")[0], METRIC)

IONS = [f"openml_ionosphere__s{s}" for s in (103, 113, 123, 133, 143, 153)]
DIGITS = [f"digits_mlp__s{s}" for s in (104, 114, 124, 134, 144, 154)]

# Bounded schema for openml_ionosphere (configs/nodes/openml_ionosphere.yaml at
# harness c686517 / 9c4902d).  Embedded so the script is self-contained.
ION_EDITABLE_SYMBOLS = (
    "C", "class_weight", "imputer", "learning_rate", "max_depth", "max_iter",
    "model_type", "n_estimators", "scaler",
)
ION_ALLOWED_VALUES = {
    "model_type": ["logistic_regression", "random_forest", "gradient_boosting"],
    "class_weight": [None, "balanced"],
    "scaler": ["none", "standard", "minmax"],
    "imputer": ["most_frequent", "constant"],
}
ION_ALLOWED_RANGES = {
    "C": [0.001, 100.0], "max_depth": [2, 30], "n_estimators": [20, 500],
    "learning_rate": [0.001, 0.5], "max_iter": [100, 3000],
}
# From r1/headroom/scripted_manager.py:34-39.
SCRIPTED_OPENML_ACTIVE = {
    "logistic_regression": ("C", "max_iter"),
    "random_forest": ("n_estimators", "max_depth"),
    "gradient_boosting": ("n_estimators", "max_depth", "learning_rate"),
}
SCRIPTED_CATEGORICAL = ("model_type", "class_weight", "scaler")
ION_CFG_ORDER = [
    "model_type", "C", "max_depth", "n_estimators", "learning_rate",
    "class_weight", "scaler", "imputer", "max_iter",
]


# ---------------------------------------------------------------------------
# loading helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def root_trials(run: Path, inst: str) -> list[dict[str, Any]]:
    return load_jsonl(run / "provenance" / "ledgers" / "roots" / inst / "root_trials.jsonl")


def branch_trials(run: Path, branch_id: str) -> list[dict[str, Any]]:
    p = run / "provenance" / "ledgers" / "branches" / branch_id / "branch_trials.jsonl"
    return load_jsonl(p) if p.exists() else []


def branch_ids(run: Path, inst: str) -> list[str]:
    d = run / "provenance" / "ledgers" / "branches"
    return sorted(p.name for p in d.iterdir() if p.is_dir() and p.name.startswith(inst + "__"))


def manager_extra(t: dict[str, Any]) -> dict[str, Any]:
    return ((t.get("extra") or {}).get("manager") or {})


def structured_edit(t: dict[str, Any]) -> dict[str, Any] | None:
    return manager_extra(t).get("structured_edit")


def proposal_identity(t: dict[str, Any]) -> tuple:
    """Stable identity for a proposal: the structured edit, else the summary."""
    se = structured_edit(t)
    if se:
        return (se.get("symbol"), str(se.get("old")), str(se.get("new")))
    return (None, t.get("proposal_summary"), None)


def edit_key(t: dict[str, Any]) -> str | None:
    se = structured_edit(t)
    return se.get("symbol") if se else None


def is_valid(t: dict[str, Any]) -> bool:
    return t.get("validity_status") == "valid"


def bit_identical(t: dict[str, Any]) -> bool | None:
    """candidate metric == incumbent metric, or None when there is no incumbent."""
    best = t.get("current_best_before")
    cand = (t.get("parsed_metrics") or {}).get(node_metric(str(t.get("campaign_id", ""))))
    if best is None or cand is None:
        return None
    return float(cand) == float(best)


def longest_identical_run(seq: list[tuple]) -> int:
    best = run = 0
    prev = object()
    for item in seq:
        if item == prev:
            run += 1
        else:
            run = 1
            prev = item
        best = max(best, run)
    return best


def summary_stats(trials: list[dict[str, Any]]) -> dict[str, Any]:
    keys = Counter()
    valid = 0
    with_incumbent = 0
    identical = 0
    for t in trials:
        k = edit_key(t)
        if k:
            keys[k] += 1
        if is_valid(t):
            valid += 1
        bi = bit_identical(t)
        if bi is not None:
            with_incumbent += 1
            identical += int(bi)
    ident = [proposal_identity(t) for t in trials]
    return {
        "n": len(trials),
        "keys": keys,
        "valid": valid,
        "with_incumbent": with_incumbent,
        "identical": identical,
        "distinct": len(set(ident)),
        "longest_run": longest_identical_run(ident) if ident else 0,
    }


# ---------------------------------------------------------------------------
# Q1 / Q4
# ---------------------------------------------------------------------------

def collect(run: Path, insts: list[str], include_branches: bool) -> tuple[list[dict], list[dict]]:
    """Return (root trials, branch trials after the decision point)."""
    roots: list[dict] = []
    branch_new: list[dict] = []
    for inst in insts:
        roots += root_trials(run, inst)
        if not include_branches:
            continue
        for bid in branch_ids(run, inst):
            snap_b = int(bid.split("__b")[1][:3])
            branch_new += [t for t in branch_trials(run, bid) if t.get("budget_index", 0) > snap_b]
    return roots, branch_new


def print_trial_table(trials: list[dict[str, Any]], title: str) -> None:
    print(f"\n### {title}\n")
    print("| instance | trial | summary | key | old -> new | validity | parsed | incumbent | delta | decision |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for t in sorted(trials, key=lambda r: (r.get("campaign_id", ""), r.get("budget_index", 0))):
        se = structured_edit(t) or {}
        pm = (t.get("parsed_metrics") or {}).get(node_metric(str(t.get("campaign_id", ""))))
        best = t.get("current_best_before")
        delta = t.get("delta_vs_best")
        print("| {} | {} | {} | {} | {} -> {} | {} | {} | {} | {} | {} |".format(
            t.get("campaign_id"), t.get("budget_index"), t.get("proposal_summary"),
            se.get("symbol", ""), se.get("old", ""), se.get("new", ""),
            t.get("validity_status"), "" if pm is None else f"{pm:.6f}",
            "" if best is None else f"{best:.6f}",
            "" if delta is None else f"{delta:+.4f}", t.get("decision")))


def print_summary_table(run: Path, insts: list[str], label: str) -> None:
    roots, _ = collect(run, insts, include_branches=False)
    s = summary_stats(roots)
    print(f"\n### {label}: root summary\n")
    print(f"- trials: {s['n']}; valid: {s['valid']}; with incumbent: {s['with_incumbent']}; "
          f"bit-identical to incumbent: {s['identical']} "
          f"({(100.0 * s['identical'] / s['with_incumbent']) if s['with_incumbent'] else 0:.1f} %)")
    print("- edited keys: " + ", ".join(f"{k}={v}" for k, v in sorted(s["keys"].items())))
    per_root = []
    for inst in insts:
        rs = summary_stats(root_trials(run, inst))
        per_root.append(f"{inst}: distinct={rs['distinct']}, longest-identical-run={rs['longest_run']}")
    print("- per root: " + "; ".join(per_root))


def q1() -> None:
    print("\n## Q1 — what the LLM proposed on ionosphere\n")
    roots, branch_new = collect(LLM_RUN, IONS, include_branches=True)
    print_trial_table(roots, "Q1a — the six ionosphere root ledgers")
    print_trial_table(branch_new, "Q1b — branch ledgers, new trials after each decision point")
    print_summary_table(LLM_RUN, IONS, "Q1c")
    s = summary_stats(roots)
    bs = summary_stats(branch_new)
    keeps = sum(1 for t in roots + branch_new if t.get("decision") == "kept")
    print(f"\n### Q1d — branch-new-trial summary\n")
    print(f"- trials: {bs['n']}; valid: {bs['valid']}; with incumbent: {bs['with_incumbent']}; "
          f"bit-identical to incumbent: {bs['identical']} "
          f"({(100.0 * bs['identical'] / bs['with_incumbent']) if bs['with_incumbent'] else 0:.1f} %)")
    print("- edited keys: " + ", ".join(f"{k}={v}" for k, v in sorted(bs["keys"].items())))
    print(f"- roots + branch-new trials: {len(roots) + len(branch_new)}; kept: {keeps} "
          f"(one per root, the first valid metric); invalid: "
          f"{len(roots) + len(branch_new) - s['valid'] - bs['valid']}")
    print("\n**Reading.** On the roots the LLM edits only "
          f"{', '.join(sorted(s['keys']))}; {s['identical']}/{s['with_incumbent']} candidate metrics are "
          "bit-identical to the incumbent, so the strict keep rule (delta > 0) never fires after trial 1. "
          "Across roots and branches no trial after the first is kept.")


def q4() -> None:
    print("\n## Q4 — is decoding deterministic?\n")
    print("Manager sampling settings at 9c4902d (langgraph_manager.py:293-313, "
          "langchain_client.py:141-151, configs/managers/langgraph_manager.json): "
          "temperature=0.2, no seed, no top_p/top_k (Ollama defaults). "
          "Non-zero temperature means sampling is not guaranteed deterministic.\n")
    print("### Q4a — repetition agreement per branch (LLM, ionosphere + digits)\n")
    print("| instance | point | action | new trials | identical | first divergence |")
    print("|---|---|---|---|---|---|")
    agree = total = 0
    for inst in IONS + DIGITS:
        for bid in branch_ids(LLM_RUN, inst):
            if "__r1" not in bid:
                continue
            mate = bid[:-2] + "r2"
            if not (LLM_RUN / "provenance" / "ledgers" / "branches" / mate).exists():
                continue
            snap_b = int(bid.split("__b")[1][:3])
            a = [proposal_identity(t) for t in branch_trials(LLM_RUN, bid) if t.get("budget_index", 0) > snap_b]
            b = [proposal_identity(t) for t in branch_trials(LLM_RUN, mate) if t.get("budget_index", 0) > snap_b]
            n = min(len(a), len(b))
            first = next((i + 1 for i in range(n) if a[i] != b[i]), None)
            ident = first is None and len(a) == len(b)
            agree += int(ident)
            total += 1
            parts = bid.split("__")
            point, action = parts[2], parts[3]
            print(f"| {inst} | {point} | {action} | {n} | {'yes' if ident else 'no'} | "
                  f"{'-' if first is None else first} |")
    print(f"\n- branch pairs compared: {total}; fully identical across repetitions: {agree} "
          f"({(100.0 * agree / total) if total else 0:.1f} %)")
    print_summary_table(LLM_RUN, DIGITS, "Q4b digits_mlp")
    print("\n**Reading.** Identical ledger prefixes usually give identical proposals, but not always: "
          "the two repetitions diverge at some budget index on several branches, consistent with "
          "temperature 0.2 and no seed. digits_mlp edits BATCH_SIZE/HIDDEN_UNITS/... and its metric "
          "does move, so its branch ledgers are not bit-identical like ionosphere's.")


# ---------------------------------------------------------------------------
# Q5 — scripted proposer reconstruction
# ---------------------------------------------------------------------------

def _is_int(text: str) -> bool:
    return re.fullmatch(r"[-+]?\d+", text.strip()) is not None


def _cfg_load(text: str) -> dict[str, Any]:
    cfg: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            cfg[k.strip()] = None if v in ("null", "~", "") else v
    return cfg


def _cfg_dump(cfg: dict[str, Any]) -> str:
    return "\n".join(
        f"{k}: {'null' if cfg[k] is None else cfg[k]}" for k in ION_CFG_ORDER
    ) + "\n"


def _hash_file_map(text: str) -> str:
    """Reproduce control_plane/snapshot.py::_hash_file_map for {config.yaml: text}."""
    d = hashlib.sha256()
    d.update(b"config.yaml")
    d.update(b"\0")
    d.update(hashlib.sha256(text.encode("utf-8")).hexdigest().encode("ascii"))
    d.update(b"\n")
    return d.hexdigest()


def _scripted_propose(seed: int, repetition: int, budget_index: int, text: str) -> tuple[str, str, str]:
    """Replay r1/headroom/scripted_manager.py::ScriptedRandomManager for one trial."""
    consts = {k: ("null" if v is None else str(v)) for k, v in _cfg_load(text).items()}
    rng = np.random.default_rng([seed, repetition, budget_index])
    edit: tuple[str, str, str] | None = None
    if rng.random() < 0.3:
        key = SCRIPTED_CATEGORICAL[int(rng.integers(len(SCRIPTED_CATEGORICAL)))]
        opts = ["null" if o is None else str(o) for o in ION_ALLOWED_VALUES.get(key, [])]
        opts = [o for o in opts if o != consts.get(key)]
        if key in consts and opts:
            edit = (key, consts[key], opts[int(rng.integers(len(opts)))])
    if edit is None:
        numeric = [s for s in SCRIPTED_OPENML_ACTIVE.get(consts.get("model_type", ""), ()) if s in consts]
        for _ in range(20):
            sym = numeric[int(rng.integers(len(numeric)))]
            old = consts[sym]
            factor = math.exp(rng.uniform(-math.log(3.0), math.log(3.0)))
            new_val = float(old) * factor
            lo_hi = ION_ALLOWED_RANGES.get(sym)
            if lo_hi:
                new_val = min(max(new_val, float(lo_hi[0])), float(lo_hi[1]))
            new = str(int(round(new_val))) if _is_int(old) else f"{new_val:.4g}"
            if float(new) != float(old):
                edit = (sym, old, new)
                break
    if edit is None:
        raise RuntimeError("scripted proposer found no non-trivial edit")
    return edit


def _apply(text: str, edit: tuple[str, str, str]) -> str:
    """Apply a structured config_value edit verbatim (the worker writes `new`)."""
    sym, _old, new = edit
    cfg = _cfg_load(text)
    cfg[sym] = None if new == "null" else new
    return _cfg_dump(cfg)


def reconstruct_scripted_root(inst: str) -> dict[str, Any] | None:
    """Reconstruct trials 1-12 of a scripted ionosphere root.

    Unknowns: keep/discard for trials 2..11 (trial 1 is kept as the first valid
    metric; the candidate at trial 12 is applied but its decision is pending at
    the E2_b012 snapshot).  Constraints: the editable-layer hash at each E2
    point and the recorded ``n_keeps`` in ``points.json``.
    """
    root = json.loads((SCRIPTED_RUN / "roots" / f"{inst}.json").read_text())
    seed = root["seed"]
    start = root["start_files"]["config.yaml"]
    pts = {p["budget_index"]: p for p in json.loads((SCRIPTED_RUN / "points.json").read_text())
           if p["instance"] == inst}
    n_keeps = {b: int(pts[b]["features"]["n_keeps"]) for b in pts}

    sols: list[tuple[list[int], dict[int, tuple[str, str, str]]]] = []
    for mask in itertools.product([0, 1], repeat=10):  # trials 2..11
        keeps = [1] + list(mask)
        if any(sum(keeps[:b - 1]) != n_keeps[b] for b in (4, 8, 12)):
            continue
        cur = start
        props: dict[int, tuple[str, str, str]] = {}
        for t in range(1, 12):
            e = _scripted_propose(seed, 0, t, cur)
            props[t] = e
            if keeps[t - 1]:
                cur = _apply(cur, e)
        props[12] = _scripted_propose(seed, 0, 12, cur)
        cur2, chk = start, {}
        for t in range(1, 12):
            if keeps[t - 1]:
                cur2 = _apply(cur2, props[t])
            if t in (3, 7, 11):
                chk[t + 1] = _apply(cur2, props[t + 1])
        if all(_hash_file_map(chk[b]) == pts[b]["snapshot_hash"] for b in (4, 8, 12)):
            sols.append((keeps, props))
    if not sols:
        return None
    keeps, props = sols[0]
    return {"instance": inst, "n_matches": len(sols), "keeps": keeps, "props": props}


def q5() -> None:
    print("\n## Q5 — the scripted proposer on the same six ionosphere roots\n")
    print("Scripted law (r1/headroom/scripted_manager.py): a numeric edit to a key that is "
          "*active for the current model_type* (OPENML_ACTIVE) with 30 % chance of a categorical "
          "switch among model_type/class_weight/scaler.\n")
    print("| instance | trial | key | old -> new | keep |")
    print("|---|---|---|---|---|")
    key_counts: Counter = Counter()
    keeps_total = trials_total = 0
    n_matches = {}
    for inst in IONS:
        r = reconstruct_scripted_root(inst)
        if r is None:
            print(f"| {inst} | — | reconstruction failed | | |")
            continue
        n_matches[inst] = r["n_matches"]
        for t in range(1, 13):
            sym, old, new = r["props"][t]
            keep = "?" if t == 12 else ("kept" if r["keeps"][t - 1] else "discarded")
            key_counts[sym] += 1
            trials_total += 1
            if t != 12 and r["keeps"][t - 1]:
                keeps_total += 1
            print(f"| {inst} | {t} | {sym} | {old} -> {new} | {keep} |")
    print("\n### Q5 summary (trials 1-12, six roots)\n")
    print("- edited keys: " + ", ".join(f"{k}={v}" for k, v in sorted(key_counts.items())))
    print(f"- keeps among trials 1-11: {keeps_total}/{6 * 11} "
          f"({100.0 * keeps_total / (6 * 11):.1f} %); trial 12 pending")
    print("- unique-hash matches per root: " + ", ".join(f"{k}:{v}" for k, v in n_matches.items()))
    print("\n**Reading.** By construction the scripted proposer never edits an inert key: on "
          "logistic_regression it can only touch C and max_iter (plus the categorical keys); once it "
          "switches model_type it edits that model's active keys. The LLM instead edited max_depth / "
          "n_estimators, which the logistic_regression node ignores.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--q", choices=["1", "4", "5", "all"], default="all")
    args = ap.parse_args()
    print("# Ionosphere LLM diagnosis tables (ENGINEERING_ONLY, AI-assisted)")
    print(f"\nLLM run: `{LLM_RUN.relative_to(REPO)}`  |  scripted run: `{SCRIPTED_RUN.relative_to(REPO)}`")
    if args.q in ("1", "all"):
        q1()
    if args.q in ("4", "all"):
        q4()
    if args.q in ("5", "all"):
        q5()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
