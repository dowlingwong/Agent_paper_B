"""Replay of the scripted proposer's law for the D25 golden regression test.

The replay is a pure function of (node, instance seed, repetition): it starts
from the node's committed start configuration, asks the scripted manager for a
proposal at budget indices 1..20, and evolves the constants by applying each
proposal (the arm-independent proposal law; keep/discard dynamics are not part
of the manager).  The same function generated the golden file before the D25
change and checks it afterwards.

AI-assisted (BUILD_BATCH3, P2); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path

from r1.harness import harness_root, import_harness

HARNESS = import_harness()

from autoresearch.manager.base import ManagerStatus  # noqa: E402
from autoresearch.manager.hyperparam_edits import parse_train_constants  # noqa: E402
from autoresearch.memory.summarizer import build_memory_context  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

from r1.headroom.scripted_manager import ScriptedRandomManager  # noqa: E402

DEFAULT_INDICES = tuple(range(1, 21))
SOURCE_RUN = "E1b_20261012T161034Z"


def start_constants(node: str) -> dict[str, str]:
    """The node's committed start configuration, filtered to its editable symbols."""
    spec = load_registered_node(node, repo_root=HARNESS)
    constants: dict[str, str] = {}
    for rel_path in spec.editable_paths:
        constants.update(parse_train_constants(HARNESS / "nodes" / node / rel_path))
    allowed = set(spec.editable_symbols or ())
    return {k: v for k, v in constants.items() if not allowed or k in allowed}


def replay(node: str, seed: int, repetition: int, indices=DEFAULT_INDICES) -> list[dict]:
    """One proposal per budget index; constants evolve by applying each proposal."""
    spec = load_registered_node(node, repo_root=HARNESS)
    manager = ScriptedRandomManager(node, seed=seed, repetition=repetition)
    constants = start_constants(node)
    sequence: list[dict] = []
    for budget_index in indices:
        status = ManagerStatus(
            campaign_id=f"{node}__s{seed}",
            budget_index=budget_index,
            current_best_metric=None,
            metric_name=spec.metric_name,
            metric_direction=spec.metric_direction,
            current_constants=dict(constants),
        )
        memory = build_memory_context([], "none", spec, budget_index)
        proposal = manager.propose_next_trial(status, memory, spec)
        edit = dict(proposal.extra["structured_edit"])
        sequence.append({
            "budget_index": budget_index,
            "symbol": edit["symbol"],
            "old": edit["old"],
            "new": edit["new"],
            "summary": proposal.proposal_summary,
        })
        constants[edit["symbol"]] = edit["new"]
    return sequence


def instances(source_run: str = SOURCE_RUN) -> list[tuple[str, int]]:
    """(node, instance seed) pairs recorded in the E1b scripted pilot run."""
    roots = Path(__file__).resolve().parents[2] / "results" / "r1" / "pilot" / source_run / "roots"
    out: list[tuple[str, int]] = []
    for path in sorted(roots.glob("*.json")):
        payload = json.loads(path.read_text())
        out.append((str(payload["node"]), int(payload["seed"])))
    return out


def golden(source_run: str = SOURCE_RUN, repetitions=(0, 1, 2)) -> dict:
    return {
        "schema": "r1.scripted_proposal_golden/1",
        "source_run": source_run,
        "replay": "apply-every-proposal; indices 1..20; start config = committed node config",
        "harness_commit": _harness_commit(),
        "instances": {
            f"{node}__s{seed}": {
                str(rep): replay(node, seed, rep) for rep in repetitions
            }
            for node, seed in instances(source_run)
        },
    }


def _harness_commit() -> str | None:
    import subprocess

    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=harness_root(),
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        return None
